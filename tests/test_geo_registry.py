"""GIS 数据注册表测试（CB-16 大南门数据专题接入守卫）。

覆盖：ermawu_l3l4 三层注册后可 resolve_points 加载（含坐标/富归因列/坐标域）+ 大南门边界 preset 可用。
"""
import pytest

from core.geo_registry import resolve_points, list_point_layers, clear_cache, resolve_boundary
from core.range_selector import load_preset


@pytest.fixture(autouse=True)
def _fresh_cache():
    """清模块缓存（防测试间缓存污染·数据文件更新后必清）。"""
    clear_cache()
    yield


# ── ermawu 点层注册（CB-16 数据专题接入）────────────────────

def test_ermawu_layers_registered():
    """list_point_layers 含 3 个 ermawu 条目（level='L3L4'）。"""
    layers = list_point_layers()
    ermawu = [l for l in layers if l['id'].startswith('ermawu_l3l4')]
    assert len(ermawu) == 3, f'应注册 3 个 ermawu 层（实际 {len(ermawu)}）'
    ids = {l['id'] for l in ermawu}
    assert {'ermawu_l3l4_t1', 'ermawu_l3l4_t2', 'ermawu_l3l4_t3'} == ids
    assert all(l['available'] for l in ermawu), 'ermawu 层应全部 available（坐标已 backfill）'
    assert all(l['level'] == 'L3L4' for l in ermawu)


def test_ermawu_t3_resolvable():
    """resolve_points('ermawu_l3l4_t3') 返回 900 行·含坐标·富归因列·坐标域合理。"""
    gdf = resolve_points('ermawu_l3l4_t3')
    assert len(gdf) == 900, f'应 900 行（实际 {len(gdf)}）'
    assert 'geometry' in gdf.columns
    assert gdf.geometry.geom_type.iloc[0] == 'Point'
    # 富归因列存在（出口卡片依赖）
    for col in ('aspect_primary', 'policy_seed', 'project_seed', 'matrix_multi', 'blind_spot'):
        assert col in gdf.columns, f'缺富归因列 {col}'
    # 坐标域合理（大南门·二马路·宜昌西陵区约 111.28E, 30.69N）
    assert 111.0 < gdf.geometry.x.mean() < 112.0
    assert 30.0 < gdf.geometry.y.mean() < 31.0


def test_ermawu_all_times_resolvable():
    """T1/T2/T3 三层均加载成功（坐标 backfill 全覆盖）。"""
    for t, n in (('t1', 700), ('t2', 800), ('t3', 900)):
        gdf = resolve_points(f'ermawu_l3l4_{t}')
        assert len(gdf) == n, f'{t}: 应 {n} 行（实际 {len(gdf)}）'
        assert 'lon' in gdf.columns or 'geometry' in gdf.columns


# ── 大南门边界 preset（Codex 必补项验证）────────────────────

def test_damanmen_preset_available():
    """大南门边界已登记 preset 且文件已复制进 presets/（available=True）。"""
    p = load_preset('damanmen_area')
    assert p is not None, 'damanmen_area 未登记 manifest'
    assert p['available'], 'damanmen_area 应 available（文件须在 DATA/boundaries/presets/）'
    assert p.get('nameField') == 'name'


# ── PRM-07（08-08 深读·glm A）：resolve_boundary dict 法定功能区黑名单兜底 ──

def _blocked_boundary(name):
    """构造单要素 GeoJSON boundary（属性名 MC=name·仿 LLM 直传）。"""
    return {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'properties': {'MC': name},
            'geometry': {'type': 'Polygon', 'coordinates': [[[111.28, 30.68], [111.29, 30.68], [111.29, 30.69], [111.28, 30.69], [111.28, 30.68]]]},
        }],
    }


def test_resolve_boundary_dict_blocked_functional_zone():
    """dict 直供法定功能区（小溪塔）→ 拒绝（诚实 request_upload·CB-14 不硬猜）。"""
    with pytest.raises(ValueError, match='法定功能区'):
        resolve_boundary(_blocked_boundary('小溪塔'))


def test_resolve_boundary_dict_allows_user_upload():
    """dict 直供用户上传合法地名（非黑名单）→ 放行（用户上传层不受限）。"""
    gj = _blocked_boundary('用户自定义片区A')
    gdf = resolve_boundary(gj)
    assert gdf is not None and len(gdf) == 1
    assert 'name' in gdf.columns or 'MC' in gdf.columns
