"""
数据治理管道 v1.0 — Data Governance Pipeline (L1)
==================================================
L0(原始爬取) → L1(数据治理): 坐标转换 + 范围过滤 + 数据脱敏 → L2(SnowNLP分析)

步骤:
  1. 加载原始数据 + 坐标转换 (GCJ-02 → WGS84 → CGCS2000 EPSG:4546)
  2. 范围过滤 (加载规划范围边界 LineString → buffer 100m → Polygon → point-in-polygon)
  3. 数据脱敏 + 导出 L1
  4. 调用 L2 SnowNLP 分析

用法:
    python SCRIPT/data_governance.py
"""

import os
import sys
import builtins as _bi

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer, CRS

# 确保可导入 core 和 SCRIPT 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 安全 print — 防止 Windows GBK 控制台崩溃 ──
_real_print = _bi.print


def _safe_print(*args, **kwargs):
    try:
        _real_print(*args, **kwargs)
    except UnicodeEncodeError:
        _real_print(
            *(str(a).encode('ascii', errors='replace').decode('ascii') for a in args),
            **kwargs,
        )


# 修复 Windows GBK 控制台编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from core.coord_transform import gcj02_to_wgs84
from core.export import export_to_csv
from SCRIPT.emotion_analysis_v1 import run_analysis_task

# ═══════════════════════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'raw')
PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'processed')
BOUNDARY_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '规划范围')

# 输入文件
RAW_CSV = os.path.join(RAW_DIR, 'xiaohongshu_20260612_规划范围_raw.csv')
BOUNDARY_SHP = os.path.join(BOUNDARY_DIR, '规划范围.shp')

# 输出命名
L1_OUTPUT_NAME = 'xiaohongshu_20260612_规划范围'
L1_CSV_OUTPUT = os.path.join(PROCESSED_DIR, f'{L1_OUTPUT_NAME}_L1_result_csv.csv')
# 过滤后数据（供 L2 分析使用，不同于 L1 全量数据）
L2_INPUT_CSV = os.path.join(PROCESSED_DIR, f'{L1_OUTPUT_NAME}_L2_input_csv.csv')

# 范围 buffer 距离（米，在投影坐标系下）
BUFFER_DISTANCE_M = 100


# ═══════════════════════════════════════════════════════════
# 步骤 1: 加载原始数据 + 坐标转换
# ═══════════════════════════════════════════════════════════

def step1_load_and_transform(csv_path: str) -> pd.DataFrame:
    """
    加载原始 CSV，完成 GCJ-02 → WGS84 → CGCS2000 EPSG:4546 坐标转换。

    新增列: lon(原lon_wgs84), lat(原lat_wgs84), x_cgcs2000, y_cgcs2000
    保留原始 lon_gcj02, lat_gcj02 列不动。

    Returns:
        含转换后坐标的 DataFrame
    """
    _safe_print(f'[LOAD] 读取原始数据: {csv_path}')

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f'原始数据文件不存在: {csv_path}')

    df = pd.read_csv(csv_path, encoding='utf-8')
    _safe_print(f'[LOAD] 共加载 {len(df)} 条原始记录')

    # 兼容旧格式: 将 raw CSV 中的 lon/lat 重命名为 lon_gcj02/lat_gcj02
    df.rename(columns={'lon': 'lon_gcj02', 'lat': 'lat_gcj02'}, inplace=True)

    # 校验必需列
    required_cols = ['lon_gcj02', 'lat_gcj02']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f'原始 CSV 缺少必需列: {missing}')

    # ── 坐标转换: GCJ-02 → WGS84 ──
    _safe_print('[TRANSFORM] GCJ-02 → WGS84 (数学转换) ...')
    wgs84_lons = []
    wgs84_lats = []
    for _, row in df.iterrows():
        try:
            lon_val = float(row['lon_gcj02'])
            lat_val = float(row['lat_gcj02'])
            wlon, wlat = gcj02_to_wgs84(lon_val, lat_val)
            wgs84_lons.append(round(wlon, 6))
            wgs84_lats.append(round(wlat, 6))
        except (ValueError, TypeError) as e:
            _safe_print(f'[WARN] 坐标转换失败 (行索引={_.name}): {e}, 标记为无效')
            wgs84_lons.append(None)
            wgs84_lats.append(None)

    df['lon'] = wgs84_lons
    df['lat'] = wgs84_lats
    _safe_print(f'[OK] WGS84 转换完成, 示例: ({df["lon"].iloc[0]}, {df["lat"].iloc[0]})')

    # ── 坐标投影: WGS84 → CGCS2000 EPSG:4546 ──
    _safe_print('[TRANSFORM] WGS84 → CGCS2000 EPSG:4546 (投影转换) ...')
    try:
        transformer = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
    except Exception as e:
        _safe_print(f'[ERR] 无法创建 pyproj Transformer: {e}')
        _safe_print('[WARN] 跳过 EPSG:4546 投影，x_cgcs2000/y_cgcs2000 将为空')
        df['x_cgcs2000'] = None
        df['y_cgcs2000'] = None
        return df

    x_cgcs = []
    y_cgcs = []
    for _, row in df.iterrows():
        try:
            x, y = transformer.transform(row['lon'], row['lat'])
            x_cgcs.append(round(x, 2))
            y_cgcs.append(round(y, 2))
        except Exception as e:
            _safe_print(f'[WARN] EPSG:4546 投影失败 (索引={_.name}): {e}')
            x_cgcs.append(None)
            y_cgcs.append(None)

    df['x_cgcs2000'] = x_cgcs
    df['y_cgcs2000'] = y_cgcs
    _safe_print(f'[OK] EPSG:4546 投影完成, 示例: ({df["x_cgcs2000"].iloc[0]}, {df["y_cgcs2000"].iloc[0]})')

    # 生成稳定行标识符
    df['id_e'] = 'e' + (df.index + 1).astype(str).str.zfill(4)
    _safe_print(f'[OK] 生成行标识符 id_e: e0001 ~ e{len(df):04d}')

    # 添加范围标识
    df['scope'] = '规划范围'
    _safe_print(f'[OK] 范围标识 scope = "规划范围"')

    return df


# ═══════════════════════════════════════════════════════════
# 步骤 2: 范围过滤
# ═══════════════════════════════════════════════════════════

def step2_filter_by_boundary(df: pd.DataFrame, shp_path: str) -> pd.DataFrame:
    """
    加载规划范围边界，buffer 生成 Polygon，用 WGS84 坐标过滤。

    边界为 LineString（EPSG:4546），需 buffer 100m 转为 Polygon，
    再转为 EPSG:4326 与数据点的 WGS84 坐标做 point-in-polygon 判断。

    Returns:
        过滤后的 DataFrame（仅保留边界内的数据点）
    """
    _safe_print(f'[LOAD] 加载边界文件: {shp_path}')

    if not os.path.exists(shp_path):
        raise FileNotFoundError(f'边界文件不存在: {shp_path}')

    # 检查 .shx 伴生文件
    shx_path = shp_path[:-4] + '.shx'
    if not os.path.exists(shx_path):
        raise FileNotFoundError(
            f'Shapefile 缺少 .shx 索引文件: {shx_path}\n'
            f'请确保 .shp / .shx / .dbf 三个文件都在同一目录。'
        )

    try:
        gdf_boundary = gpd.read_file(shp_path)
    except Exception as e:
        _safe_print(f'[ERR] 边界文件读取失败: {e}')
        raise

    orig_crs = gdf_boundary.crs
    _safe_print(f'[LOAD] 边界 CRS: {orig_crs}')
    _safe_print(f'[LOAD] 边界几何类型: {[g.geom_type for g in gdf_boundary.geometry]}')
    _safe_print(f'[LOAD] 边界要素数: {len(gdf_boundary)}')

    # ── 校验边界 CRS 是否为投影坐标系（buffer 需要米制单位）──
    crs_obj = CRS.from_user_input(gdf_boundary.crs)
    if not crs_obj.is_projected:
        _safe_print(
            f'[ERR] 边界 CRS 为地理坐标系 ({gdf_boundary.crs})，'
            f'buffer 需要投影坐标系（单位为米）。'
        )
        _safe_print('[ERR] 请将边界转换为投影坐标系（如 EPSG:4546）后再使用。')
        raise ValueError(
            f'边界坐标系不是投影坐标系: {gdf_boundary.crs}。buffer 需要米制投影坐标系。'
        )

    # ── Buffer 100m 生成 Polygon（在原投影坐标系下操作，单位=米）──
    _safe_print(f'[TRANSFORM] LineString → Polygon (buffer={BUFFER_DISTANCE_M}m) ...')
    try:
        gdf_boundary['geometry'] = gdf_boundary.geometry.buffer(BUFFER_DISTANCE_M)
        _safe_print(f'[OK] Buffer 后几何类型: {[g.geom_type for g in gdf_boundary.geometry]}')
    except Exception as e:
        _safe_print(f'[ERR] Buffer 操作失败: {e}')
        raise

    # ── 转为 EPSG:4326 用于 point-in-polygon ──
    _safe_print('[TRANSFORM] 边界 Polygon → EPSG:4326 ...')
    try:
        gdf_wgs84 = gdf_boundary.to_crs('EPSG:4326')
    except Exception as e:
        _safe_print(f'[ERR] 边界坐标系转换失败: {e}')
        raise

    # ── point-in-polygon 过滤 ──
    boundary_polygon = gdf_wgs84.union_all()  # 合并所有 Polygon 为一个几何体
    _safe_print(f'[LOAD] 合并后边界几何类型: {boundary_polygon.geom_type}')

    input_count = len(df)
    keep_mask = []
    for _, row in df.iterrows():
        try:
            lon = float(row['lon'])
            lat = float(row['lat'])
            pt = Point(lon, lat)
            keep_mask.append(boundary_polygon.contains(pt))
        except (ValueError, TypeError):
            keep_mask.append(False)

    df['in_scope'] = keep_mask
    df_filtered = df[df['in_scope']].copy()
    dropped_count = input_count - len(df_filtered)

    _safe_print(f'[OK] 范围过滤完成: {input_count} → {len(df_filtered)} 条 (过滤掉 {dropped_count} 条)')

    if df_filtered.empty:
        _safe_print('[WARN] 过滤后数据为空！请检查边界范围是否与数据点坐标匹配。')

    return df_filtered


# ═══════════════════════════════════════════════════════════
# 步骤 3: 数据脱敏 + 导出 L1
# ═══════════════════════════════════════════════════════════

def anonymize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    数据脱敏处理：清空敏感列（comments）。

    脱敏规则:
      - 清空 'comments' 列（可能包含其他用户评论中的个人身份信息）
      - 保留 'title' 和 'text'（公开发布内容）
      - 保留所有其他列

    Returns:
        脱敏后的 DataFrame（原地修改）
    """
    _safe_print('[ANONYMIZE] 数据脱敏处理...')

    sensitive_cols = ['comments']
    removed = []
    for col in sensitive_cols:
        if col in df.columns:
            df[col] = ''
            removed.append(col)

    if removed:
        _safe_print(f'[OK] 已清空敏感列: {removed}')
    else:
        _safe_print('[OK] 无需脱敏的列（comments 列不存在）')

    return df


def step3_export_filtered(df: pd.DataFrame, output_path: str) -> str:
    """
    导出过滤后数据 CSV（脱敏已在步骤 1 后完成，此处仅导出）。

    Returns:
        导出的 CSV 文件路径
    """
    _safe_print(f'[EXPORT] 导出过滤后数据: {output_path}')
    export_to_csv(df, output_path)

    return output_path


# ═══════════════════════════════════════════════════════════
# 步骤 4: 调用 L2 SnowNLP 分析
# ═══════════════════════════════════════════════════════════

def step4_run_l2_analysis(l1_csv_path: str, output_name: str) -> dict:
    """
    调用 emotion_analysis_v1.run_analysis_task() 执行 L2 SnowNLP 分析。

    Args:
        l1_csv_path: L1 治理后数据 CSV 路径
        output_name: 输出文件基础名

    Returns:
        run_analysis_task 返回的结果 dict
    """
    _safe_print(f'[L2] 启动 SnowNLP 情绪分析...')
    _safe_print(f'[L2] 输入: {l1_csv_path}')
    _safe_print(f'[L2] 输出基础名: {output_name}')

    result = run_analysis_task(
        file_path=l1_csv_path,
        engine_type='snownlp',
        output_name=output_name,
        enable_keywords=True,
    )

    if result['success']:
        _safe_print(f'\n[OK] L2 分析完成!')
        _safe_print(f'  数据条数: {result["n_points"]}')
        _safe_print(f'  综合得分均值: {result["score_mean"]}')
        _safe_print(f'  五级极性分布:')
        for pol, count in result.get('polarity_stats', {}).items():
            _safe_print(f'    {pol}: {count}')
        _safe_print(f'  CSV 输出: {result["csv_path"]}')
        _safe_print(f'  GeoJSON 输出: {result["geojson_path"]}')
    else:
        _safe_print(f'[ERR] L2 分析失败: {result["message"]}')

    return result


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

def main():
    """L1 数据治理管道主入口。

    流程:
      1. 加载原始数据 + 坐标转换 → 脱敏
      2. 范围过滤（基于规划范围边界 Polygon，添加 in_scope 列）
      3. 导出 L1（含 in_scope 标记的全量数据）
      4. 导出过滤后数据 + L2 SnowNLP 分析（仅当过滤后有数据时执行）
    """
    _safe_print('=' * 60)
    _safe_print('  数据治理管道 v1.0 — L0 → L1 → L2')
    _safe_print('=' * 60)

    # ── 步骤 1: 加载原始数据 + 坐标转换 + 脱敏 ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 1/4] 加载原始数据 + 坐标转换')
    _safe_print('-' * 40)
    try:
        df = step1_load_and_transform(RAW_CSV)
    except Exception as e:
        _safe_print(f'[ERR] 步骤 1 失败: {e}')
        sys.exit(1)

    # ── 步骤 1 后立即脱敏 ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[ANONYMIZE] 数据脱敏')
    _safe_print('-' * 40)
    df = anonymize_dataframe(df)

    # ── 步骤 2: 范围过滤（先过滤以获取 in_scope 列）──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 2/4] 范围过滤')
    _safe_print('-' * 40)
    try:
        df_filtered = step2_filter_by_boundary(df, BOUNDARY_SHP)
    except Exception as e:
        _safe_print(f'[ERR] 步骤 2 失败: {e}')
        sys.exit(1)

    # ── 步骤 2 后导出 L1（含 in_scope 标记的全量数据）──
    _safe_print('\n' + '-' * 40)
    _safe_print('[EXPORT L1] 导出 L1 全量数据（含 in_scope 标记）')
    _safe_print('-' * 40)
    export_to_csv(df, L1_CSV_OUTPUT)
    _safe_print(f'[OK] L1 全量数据已保存: {L1_CSV_OUTPUT} ({len(df)} 条)')

    if df_filtered.empty:
        _safe_print('[WARN] 过滤后无数据落在规划范围内。')
        _safe_print('[WARN] 当前所有数据点坐标均为占位值 (111.295, 30.71 GCJ-02)，')
        _safe_print('[WARN] 不在规划范围 LineString 的 100m buffer 区域内，属预期行为。')
        _safe_print('[WARN] L2 分析跳过（无过滤后数据）。')
        _safe_print('\n' + '=' * 60)
        _safe_print('  数据治理管道完成 (仅 L1)!')
        _safe_print('=' * 60)
        _safe_print(f'  L1 输出: {L1_CSV_OUTPUT}')
        _safe_print('  L2 输出: (跳过 — 过滤后无数据)')
        _safe_print('')
        sys.exit(0)

    # ── 步骤 3: 导出过滤后数据（脱敏已在步骤 1 后完成）──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 3/4] 导出过滤后数据')
    _safe_print('-' * 40)
    try:
        l2_input_path = step3_export_filtered(df_filtered, L2_INPUT_CSV)
    except Exception as e:
        _safe_print(f'[ERR] 步骤 3 失败: {e}')
        sys.exit(1)

    # ── 步骤 4: 调用 L2 SnowNLP 分析（仅当过滤后有数据时执行）──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 4/4] 调用 L2 SnowNLP 分析')
    _safe_print('-' * 40)
    try:
        l2_result = step4_run_l2_analysis(l2_input_path, L1_OUTPUT_NAME)
    except Exception as e:
        _safe_print(f'[ERR] 步骤 4 失败: {e}')
        sys.exit(1)

    # ── 汇总 ──
    _safe_print('\n' + '=' * 60)
    _safe_print('  数据治理管道完成!')
    _safe_print('=' * 60)
    _safe_print(f'  L1 输出: {L1_CSV_OUTPUT}')
    if l2_result.get('success'):
        _safe_print(f'  L2 CSV:      {l2_result["csv_path"]}')
        _safe_print(f'  L2 GeoJSON:  {l2_result["geojson_path"]}')
    _safe_print('')


if __name__ == '__main__':
    main()
