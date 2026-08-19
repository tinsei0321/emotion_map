"""PT-CB2 T2 · usage 白名单消费点测试（铁律7 机械化：结论层拒绝作空间操作输入）。

覆盖四类：
1. 拒绝——结论层（usage=analysis_output）出现在任何空间操作参数位 → 400 + 三段式文案（含替代建议）；
2. 放行——input 层 / 匿名 GeoJSON send-in / 非 manifest 字符串（点层 id、控制参数）不误拦；
3. 指路——拒绝文案带同组可用 input 替代（帮 AI 一步纠错）；
4. catalog 透出——/geo/catalog boundaries 每项含 usage 字段（前端守卫的单一权威投影）。

门禁：基线 375+3 → 本文件新增后上浮（执行记录注明）。
依赖：manifest.json（usage 45+12 全覆盖·PT-CB2 T1 落地）；L2 演示数据缺失时 API 级用例整组 skip。
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app
from core.config import PERFORMANCE_DIR
from core.field_dictionary import (
    UsageGuardError, clear_layer_usage_cache, get_layer_usage, validate_input_usage,
)

client = TestClient(app)

_L2 = 'yichang_l2_t1'
_L2_FILE = os.path.join(PERFORMANCE_DIR, 'yichang_L2_T1_L2_result_csv.csv')

# PT-CB2 T1 落地的结论层样本（manifest analysis_output 12 项中取代表：面/点/聚合面）
_CONCLUSION_AREA = 'base_174_aggregate_area'      # 城市体检底座·聚合范围快照
_CONCLUSION_POINT = 'page7_dual_high_point'       # page7 结论层（点版）
_CONCLUSION_MERGE = 'base_xlwj_merge_area'        # 西陵伍家合并范围
_INPUT_PRESET = 'admin_district'                  # 行政区划（input·既有用例主路径）

pytestmark = pytest.mark.skipif(
    not os.path.isfile(_L2_FILE),
    reason='演示数据 yichang_L2_T1 不存在',
)


def _boundary_available(bid: str) -> bool:
    r = client.get('/api/v1/geo/catalog')
    if r.status_code != 200:
        return False
    return any(b['id'] == bid and b['available'] for b in r.json().get('boundaries', []))


# ════════════ 单元级：守卫本体 ════════════

def test_get_layer_usage_three_states():
    """input / analysis_output / None（点层 id 与非 manifest 字符串）三态查询正确。"""
    clear_layer_usage_cache()
    assert get_layer_usage(_INPUT_PRESET) == 'input'
    assert get_layer_usage(_CONCLUSION_AREA) == 'analysis_output'
    assert get_layer_usage(_L2) is None            # geo_registry 点层 id 不在 manifest
    assert get_layer_usage('worst') is None        # 控制参数字符串不误判
    assert get_layer_usage(None) is None           # 非 str 静默放行


def test_validate_rejects_with_three_part_message():
    """拒绝文案三段式：是什么层 / 为何拒（铁律7）/ 可用替代（同组 input 优先）。"""
    with pytest.raises(UsageGuardError) as ei:
        validate_input_usage(_CONCLUSION_AREA, 'boundary')
    msg = str(ei.value)
    assert '分析结论层' in msg and 'analysis_output' in msg     # 是什么层
    assert '铁律7' in msg and '空间操作输入' in msg              # 为何拒
    assert '可改用分析原料层' in msg                            # 替代建议存在
    assert 'base_residential_point' in msg                     # 同组 input 底座在列


def test_validate_passes_input_unknown_and_none():
    """input 层 / 未注册字符串 / None → 静默放行（不抛错）。"""
    validate_input_usage(_INPUT_PRESET, 'boundary')   # input
    validate_input_usage('not_a_preset', 'boundary')  # 未注册
    validate_input_usage(None, 'boundary')            # GeoJSON send-in 位由调用方处理


def test_usage_guard_error_is_value_error():
    """UsageGuardError 是 ValueError 子类 → geo_routes 既有 except ValueError 分支自动转 400。"""
    assert issubclass(UsageGuardError, ValueError)


# ════════════ API 级：端点挂闸 ════════════

def test_api_zonal_rejects_conclusion_boundary():
    """zonal_stats(boundary=结论层) → 400 三段式（zonal 是宏观结论主干·最关键拦截位）。"""
    r = client.post('/api/v1/geo/zonal_stats',
                    json={'layer': _L2, 'boundary': _CONCLUSION_AREA, 'top_n': 5})
    assert r.status_code == 400
    d = r.json().get('detail', '')
    assert 'analysis_output' in d and '铁律7' in d and '可改用分析原料层' in d


def test_api_clip_rejects_conclusion_range():
    """clip(range=page7 结论点层) → 400（range 位拦截·先于几何类型错误）。"""
    r = client.post('/api/v1/geo/clip', json={'layer': _L2, 'range': _CONCLUSION_POINT})
    assert r.status_code == 400
    assert 'analysis_output' in r.json().get('detail', '')


def test_api_filter_attr_rejects_conclusion_layer():
    """filter_attr(layer=18村结论面) → 400（layer 位拦截·错误语义优于原 KeyError）。"""
    r = client.post('/api/v1/geo/filter_attr',
                    json={'layer': 'base_18village_area',
                          'pre_filter': {'field': 'name', 'op': 'eq', 'value': 'x'}})
    assert r.status_code == 400
    assert 'analysis_output' in r.json().get('detail', '')


def test_api_merge_rejects_conclusion_in_layers_list():
    """merge(layers=[input, 结论层]) → 400（list 内 str 逐项扫描）。"""
    r = client.post('/api/v1/geo/merge',
                    json={'layers': [_INPUT_PRESET, _CONCLUSION_MERGE]})
    assert r.status_code == 400
    assert _CONCLUSION_MERGE in r.json().get('detail', '')


def test_api_passes_input_preset():
    """zonal_stats(boundary=admin_district·input) → 不被 usage 守卫拦（既有用例零退化）。"""
    if not _boundary_available(_INPUT_PRESET):
        pytest.skip('admin_district 预设文件未上传')
    r = client.post('/api/v1/geo/zonal_stats',
                    json={'layer': _L2, 'boundary': _INPUT_PRESET, 'top_n': 3})
    assert r.status_code == 200
    assert 'analysis_output' not in str(r.json())


def test_api_dict_geojson_not_blocked():
    """匿名 GeoJSON send-in（用户上传/多步链 $n 产物）不拦——clip dict+dict 正常 200。"""
    pts = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [111.3, 30.7]},
         'properties': {'name': 'a'}},
        {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [111.31, 30.71]},
         'properties': {'name': 'b'}},
    ]}
    tri = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [
            [[111.29, 30.69], [111.33, 30.69], [111.31, 30.73], [111.29, 30.69]]]},
         'properties': {'name': '测试范围'}},
    ]}
    r = client.post('/api/v1/geo/clip', json={'layer': pts, 'range': tri})
    assert r.status_code == 200
    assert r.json()['success'] is True
    assert r.json()['count'] == 2


def test_api_control_string_not_blocked():
    """控制参数字符串（rank by='worst'）不经 usage 误拦——走正常业务错误路径。"""
    r = client.post('/api/v1/geo/rank',
                    json={'layer': _L2, 'by': 'worst', 'top_n': 3})
    assert r.status_code != 400 or 'analysis_output' not in r.json().get('detail', '')


# ════════════ catalog 透出（前端守卫的权威投影）════════════

def test_catalog_boundaries_expose_usage():
    """/geo/catalog boundaries 每项含 usage；input 与 analysis_output 均在场（45+12 投影）。"""
    r = client.get('/api/v1/geo/catalog')
    assert r.status_code == 200
    bs = r.json().get('boundaries', [])
    assert bs, 'catalog boundaries 不应为空'
    usages = {b.get('usage') for b in bs}
    assert usages <= {'input', 'analysis_output', None}
    assert 'analysis_output' in usages
    assert 'input' in usages
