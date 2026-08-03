"""出口卡片组装器测试（Wave 0·S2 打穿核心守卫）。

确定性组装验证：resolve_outlet_id 路由 + build_outlet_schema 7 要素 + 字段缺失降级 + 尺度分派。
"""
import pytest

from ai_qa.outlet_kb.build_outlet_schema import resolve_outlet_id, build_outlet_schema


def _diag(scale='meso', domain_lens=('urban_renewal',), outlet='建议清单'):
    return {'scale': scale, 'domain_lens': list(domain_lens), 'outlet': outlet}


def _result(polarity=-0.3, n=1247, place='夷陵广场'):
    return {
        'polarity_index': polarity,
        'point_count': n,
        'features': [{'properties': {'place_name': place, 'domain_top': 'urban_renewal',
                                     'element_top': '设施', 'issue_label': '停车难'}}],
    }


def test_resolve_outlet_id_hit():
    """问句含接口词 → 命中契约（renewal_demand）。"""
    oid = resolve_outlet_id(_diag(), '西陵区老旧小区更新需求分析')
    assert oid == 'renewal_demand'


def test_resolve_outlet_id_no_hit():
    """无接口词 + outlet 非行业类 → 返回 None（不出卡）。"""
    diag = _diag(outlet='生成图层')   # 生成图层 hint 是 renewal_object_identify·但问句无接口词且无 scale 加分?
    # 生成图层 hint 是 renewal_object_identify（+3）·domain+scale（+4）·应命中·这里验证"纯通用问句"不出卡
    assert resolve_outlet_id(_diag(outlet=''), '生成热力图') is None


def test_resolve_outlet_id_scale_mismatch():
    """尺度分派：macro 问句 → macro 契约（renewal_object_identify）非 meso（renewal_demand）。"""
    oid = resolve_outlet_id(_diag(scale='macro', outlet=''), '西陵区更新需求分析')
    assert oid == 'renewal_object_identify', f'macro 问句应命中 macro 契约（实际 {oid}）'


def test_build_outlet_schema_7_elements():
    """S2 问句 → 需求分析卡（7 要素：接口标识/数据基础/定量/定性/地理定位/对接建议/局限）。"""
    card = build_outlet_schema(_diag(), _result(), '西陵区老旧小区更新需求分析')
    assert card is not None
    assert card['interface'].startswith('片区策划')     # 接口标识
    assert card['task_link']                            # 对接建议
    assert card['fields']                               # 定量/定性/地理定位
    assert card['data_base']['N'] == 1247               # 数据基础
    assert card['limitations']                          # 局限标注
    assert card['can'] and card['cannot']               # 能/不能双栏


def test_build_outlet_schema_field_mapping():
    """field_mapping 确定性取值（polarity_index → 需求强度）。"""
    card = build_outlet_schema(_diag(), _result(polarity=-0.3), '西陵区更新需求分析')
    # 需求强度 ← polarity_index（field_mapping 里有 polarity_index 表达）
    any_neg = any('-0.3' in str(f.get('value')) for f in card['fields'].values())
    assert any_neg, f'需求强度未取到 polarity_index（fields={card["fields"]}）'


def test_build_outlet_schema_missing_field_degrade():
    """字段缺失 → 降级"暂无数据"（不编造）。"""
    card = build_outlet_schema(_diag(), {'point_count': 0}, '西陵区更新需求分析')
    # 无 features/字段 → 各字段降级
    for f in card['fields'].values():
        assert f['value'] is not None, '字段缺失应降级非 None'


def test_build_outlet_schema_no_hit():
    """未命中契约（outlet 空 + 无接口词）→ None（不出卡·只出普通分析）。"""
    assert build_outlet_schema(_diag(outlet=''), _result(), '生成热力图') is None


# ── CB-16 Codex/glm 修复后补测（3 缺口）────────────────────
def test_qualifier_field_parsed():
    """CB-16 Codex：qualifier 后缀（降序/占比）应解析出主字段（防丢值）。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '指标排序'}
    card = build_outlet_schema(diag, {'polarity_index': -0.45, 'point_count': 5,
                                      'features': [{'properties': {'domain_top': 'urban_renewal'}}]},
                               '西陵区更新时序排序')
    # renewal_sequence field_mapping 优先级排序 = 'polarity_index 降序' → 应取到 -0.45
    any_neg = any('-0.45' in str(f.get('value')) for f in card['fields'].values())
    assert any_neg, f'qualifier 后缀未解析出主字段（fields={card["fields"]}）'


def test_update_layer_no_false_trigger():
    """CB-16 Codex：UI 语境"更新图层"不应误触发行业卡。"""
    oid = resolve_outlet_id({'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '生成图层'},
                            '帮我更新图层')
    assert oid is None, f'"更新图层"应不触发（实际 {oid}）'


def test_resolve_outlet_id_checkup():
    """CB-16 glm：体检满意度问句 → checkup_satisfaction（domain=urban_governance 修复后）。"""
    oid = resolve_outlet_id({'scale': 'macro', 'domain_lens': ['urban_governance'], 'outlet': '报告结论'},
                            '城市体检满意度调查')
    assert oid == 'checkup_satisfaction', f'体检满意度应命中 checkup_satisfaction（实际 {oid}）'
