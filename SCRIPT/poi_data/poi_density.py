#!/usr/bin/env python3
"""
POI 核密度曲面 + 密度引导采样（v3.1 空间生成核心）
================================================
替 v3.0 的「POI 锚点高斯聚类」（离散光斑 + 伍家空白）。纯 numpy，不引 scipy（3.14 稳）。

流程：
  POI(WGS84) -> 投影 EPSG:4546(米, 各向同性)
            -> np.histogram2d 密度网格
            -> 可分离高斯卷积平滑（sigma_m 控制光斑扩散）
            -> 归一化 P(cell)（概率分布）
  采样：np.random.default_rng.choice 按 P 采 cell -> cell 内均匀撒点
        -> zone.contains() 掩膜（米制）-> 批量最近 POI 继承 seed -> 转回 WGS84

返回 v3.0 同契约：[{'lon','lat','seed','area_tag'}, ...]。
"""
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPT = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_SCRIPT)
for _p in (_ROOT, _SCRIPT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shapely.geometry import Point
from shapely.ops import transform as shp_transform
from pyproj import Transformer

try:
    from core.tracker import track, register_track_id
    from core.utils import safe_print
except Exception:  # 独立调试兜底（无 core 环境时仍可跑）
    track = lambda *a, **k: (lambda f: f)
    register_track_id = lambda *a, **k: None
    def safe_print(s):
        print(s)

# WGS84(EPSG:4326) <-> CGCS2000 3-degree GK CM 111E(EPSG:4546)
_T = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
_T_INV = Transformer.from_crs('EPSG:4546', 'EPSG:4326', always_xy=True)


def _gaussian_kernel1d(sigma):
    """1D 高斯核（截断 +-3sigma）。sigma<阈值时退化为单位核（不平滑）。"""
    if sigma < 0.5:
        return np.array([1.0])
    r = int(max(1, round(3 * sigma)))
    k = np.arange(-r, r + 1, dtype=float)
    g = np.exp(-0.5 * (k / sigma) ** 2)
    return g / g.sum()


def _convolve_separable(H, sigma):
    """2D 密度网格的可分离高斯卷积（先 x 轴再 y 轴），'same' 模式。纯 numpy。"""
    g = _gaussian_kernel1d(sigma)
    H1 = np.apply_along_axis(lambda col: np.convolve(col, g, 'same'), 0, H)  # 沿 x(轴0)
    H2 = np.apply_along_axis(lambda row: np.convolve(row, g, 'same'), 1, H1)  # 沿 y(轴1)
    return H2


class DensityField:
    """POI 点 -> 核密度曲面 -> 密度引导采样。

    Parameters
    ----------
    seeds : list[dict]
        POI 种子，每条含 lng/lat(WGS84)，可选 name/baidu_level1/...
        （最近邻继承给采样点，供 inject_fields 的 spatial_hotspot 等标注字段）。
    zone_poly : shapely Polygon (WGS84)
        采样区域，contains() 掩膜。
    cell_m : float
        密度网格边长（米）。
    sigma_m : float
        高斯平滑 sigma（米）。越大光斑越糊开（主城 400m 糊开 158 POI 成连续带）。
    """

    def __init__(self, seeds, zone_poly, cell_m=60.0, sigma_m=250.0, bg_ratio=0.02):
        if not seeds:
            raise ValueError('[DensityField] 无 POI 种子，无法建密度曲面')
        self.seeds = seeds
        self.zone_wgs = zone_poly
        self.cell_m = float(cell_m)
        self.sigma_m = float(sigma_m)
        self._bg_ratio = float(bg_ratio)   # 背景基底占比（全域均匀）：摊薄密度带 + 提填充

        # 投影 POI + zone 到 4546（米制，各向同性）
        self._px = np.array([float(s['lng']) for s in seeds])
        self._py = np.array([float(s['lat']) for s in seeds])
        self._mx, self._my = _T.transform(self._px, self._py)
        self.zone_proj = shp_transform(_T.transform, zone_poly)
        xmin, ymin, xmax, ymax = self.zone_proj.bounds
        pad = self.sigma_m  # 边界 pad：防卷积截断 + 给 buffer 区留采样空间
        self._xmin, self._ymin = xmin - pad, ymin - pad
        self._xmax, self._ymax = xmax + pad, ymax + pad

        # 密度网格（histogram2d: H[i,j] -> x 第 i bin, y 第 j bin；shape=(nx,ny)）
        self._nx = max(8, int(np.ceil((self._xmax - self._xmin) / self.cell_m)))
        self._ny = max(8, int(np.ceil((self._ymax - self._ymin) / self.cell_m)))
        H, _, _ = np.histogram2d(
            self._mx, self._my,
            bins=[self._nx, self._ny],
            range=[[self._xmin, self._xmax], [self._ymin, self._ymax]],
        )
        sigma_cell = self.sigma_m / self.cell_m
        Hs = _convolve_separable(H, sigma_cell)
        kde = np.clip(Hs, 0.0, None)
        s = kde.sum()
        if s <= 0:
            raise ValueError('[DensityField] 密度曲面全零（POI 与区域不重叠？）')
        kde /= s
        # 背景基底（全域均匀）：纯 KDE 会把点全锁进种子密度带（稀疏种子下覆盖窄、
        # 密度带内过密成新光斑）。混入 bg_ratio 均匀基底 -> 摊薄密度带 + 提全域填充。
        # 采样时 zone.contains() 自然把背景点限制在区域内。
        bg = np.full_like(kde, 1.0 / kde.size)
        self._P = kde * (1.0 - self._bg_ratio) + bg * self._bg_ratio
        self._P /= self._P.sum()
        safe_print('[DENSITY] {} | grid {}x{} | sigma {:.0f}m ({:.1f}cell) | KDE-nonzero {:.1%} | bg {:.0%}'.format(
            zone_poly.geom_type, self._nx, self._ny, self.sigma_m, sigma_cell,
            (kde > 0).mean(), self._bg_ratio))

    @track("MOD_GEN.F_013", track_args=False)
    def sample(self, n, rng, area_tag):
        """密度引导采样 n 点。rng=Python random.Random（派生 numpy 种子保可复现）。
        返回 [{'lon','lat','seed','area_tag'}, ...]（v3.0 同契约）。"""
        nprng = np.random.default_rng(rng.randint(0, 2 ** 31 - 1))
        flatP = self._P.flatten()
        nz = self._P.shape[1]  # ny；flatten 行主序：idx = i*ny + j
        pts_mx, pts_my, pts_near = [], [], []
        collected = 0
        attempts = 0
        while collected < n and attempts < 200:
            attempts += 1
            need = int((n - collected) * 1.6) + 16  # oversample 补 contains 拒绝
            idx = nprng.choice(flatP.size, size=need, p=flatP)
            ix = idx // nz
            iy = idx % nz
            mx = self._xmin + (ix + nprng.random(need)) * self.cell_m
            my = self._ymin + (iy + nprng.random(need)) * self.cell_m
            # contains 掩膜（米制；shapely 逐点，其余向量化）
            mask = np.fromiter(
                (self.zone_proj.contains(Point(x, y)) for x, y in zip(mx, my)),
                dtype=bool, count=need)
            mx, my = mx[mask], my[mask]
            if mx.size == 0:
                continue
            # 批量最近 POI（米制欧氏）
            d2 = (mx[:, None] - self._mx[None, :]) ** 2 + (my[:, None] - self._my[None, :]) ** 2
            near = np.argmin(d2, axis=1)
            take = min(mx.size, n - collected)
            pts_mx.extend(mx[:take].tolist())
            pts_my.extend(my[:take].tolist())
            pts_near.extend(near[:take].tolist())
            collected += take
        if collected < n:
            safe_print('[DENSITY][WARN] {} 仅采到 {}/{}（区域/密度限制）'.format(
                area_tag, collected, n))
        lon, lat = _T_INV.transform(np.array(pts_mx), np.array(pts_my))
        return [{'lon': float(lon[k]), 'lat': float(lat[k]),
                 'seed': self.seeds[pts_near[k]], 'area_tag': area_tag}
                for k in range(collected)]


register_track_id("MOD_GEN.F_013", "POI 核密度曲面 + 密度引导采样（v3.1）")


if __name__ == '__main__':
    # 自检：卷积核 + shape 守恒
    k = _gaussian_kernel1d(3.0)
    assert abs(k.sum() - 1.0) < 1e-9, 'kernel != 1.0'
    safe_print('[OK] gaussian kernel sum = {:.6f} (len={})'.format(k.sum(), len(k)))
    H = np.zeros((20, 20))
    H[10, 10] = 1.0
    Hs = _convolve_separable(H, 3.0)
    safe_print('[OK] convolve peak {} -> spread sum {:.4f} (守恒={})'.format(
        H.max(), Hs.sum(), abs(Hs.sum() - 1.0) < 1e-9))
