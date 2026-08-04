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


# ── CB-16 大南门数据专题：真实 ermawu 聚合产物出卡 ────────────
def test_build_outlet_schema_ermawu_real_aggregate():
    """真实 ermawu L3L4 聚合产物（zonal 输出结构）+ 大南门问句 → 需求分析卡（需求强度有值）。

    模拟 tools.js zonal_stats 对 ermawu 富归因层的聚合输出（issue_label/domain_top/element_top 等）。
    验证确定性组装从聚合产物取字段（非"暂无数据"）+ 命中 renewal_demand。
    """
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    # 真实 zonal 聚合产物（属性即 ermawu 富归因列聚合出的规范输出）
    result = {
        'polarity_index': -0.32,
        'point_count': 900,
        'features': [{'properties': {
            'place_name': '大南门·二马路滨江片区',
            'domain_top': 'urban_renewal',
            'element_top': '设施',
            'issue_label': '停车难',
        }}],
    }
    card = build_outlet_schema(diag, result, '大南门·二马路片区更新需求分析')
    assert card is not None
    assert card['outlet_id'] == 'renewal_demand', f'应命中 renewal_demand（实际 {card["outlet_id"]}）'
    assert card['interface'].startswith('片区策划')        # 行业接口标识
    assert card['task_link']                              # 对接建议
    assert card['can'] and card['cannot']                 # 能/不能双栏
    assert card['data_base']['N'] == 900                  # 数据基础
    # 需求强度 ← polarity_index（field_mapping）+ 问题类型 ← issue_label + 需求位置 ← place_name
    vals = {k: str(f.get('value')) for k, f in card['fields'].items()}
    assert any('-0.32' in v for v in vals.values()), f'需求强度未取到 polarity_index（{vals}）'
    assert '停车难' in vals.get('问题类型', ''), f'问题类型未取到 issue_label（{vals}）'
    assert '大南门' in vals.get('需求位置', ''), f'需求位置未取到 place_name（{vals}）'
    assert not any(v == '暂无数据' for v in vals.values()), f'真实聚合产物不应有缺失降级（{vals}）'


# ── CB-16 Wave 1（macro 出口）：rows 产物 + checkup_dimension scale 限定 ──
def test_wave1_macro_rows_result():
    """Wave 1：macro 分析（zonal/rank）rows 产物 → renewal_object_identify 出卡 + 字段取到值。

    macro 权威产物形态 = rows 数组（含 issue_label/polarity_index/domain_top）·_extract_emc_value
    统一收 rows/features 两类（claude组 ①）·不再"暂无数据"。
    """
    diag = {'scale': 'macro', 'domain_lens': ['urban_renewal'], 'outlet': '生成图层'}
    result = {'rows': [
        {'name': '西陵区', 'polarity_index': -0.42, 'domain_top': 'urban_renewal',
         'element_top': '环境', 'issue_label': '老旧破败', 'point_count': 300},
        {'name': '伍家岗区', 'polarity_index': -0.21, 'domain_top': 'urban_renewal',
         'element_top': '设施', 'issue_label': '停车难', 'point_count': 200},
    ]}
    card = build_outlet_schema(diag, result, '宜昌城区哪些区域更新优先')
    assert card is not None
    assert card['outlet_id'] == 'renewal_object_identify', f'macro 应命中更新对象识别（{card["outlet_id"]}）'
    # 更新对象 ← issue_label（rows[0] Top-1）+ 空间聚集强度 ← polarity_index
    vals = {k: str(f.get('value')) for k, f in card['fields'].items()}
    assert '老旧破败' in vals.get('更新对象（疑似）', ''), f'更新对象未取到 rows issue_label（{vals}）'
    assert any('-0.42' in v for v in vals.values()), f'空间聚集强度未取到 rows polarity_index（{vals}）'
    assert not any(v == '暂无数据' for v in vals.values()), f'rows 产物不应缺失降级（{vals}）'
    # data_base：rows 型 → N=区域单元数（非评论数）·total_points 总评论数
    assert card['data_base']['N'] == 2, f'data_base.N 应为区域单元数（{card["data_base"]}）'
    assert card['data_base']['total_points'] == 500, f'total_points 应=sum(point_count)（{card["data_base"]}）'
    assert '区域单元' in card['data_base']['note'], f'note 应标注单元数（{card["data_base"]["note"]}）'


def test_wave1_checkup_dimension_scale_limited():
    """Wave 1 + Codex P1：checkup_dimension 槽位 scale 限定——macro 问句只填城区维度·其余"需对应尺度分析"。

    防四维度×单尺度语义错位（macro 值不再误入住房/小区/街区槽·比"暂无数据"更糟）。
    """
    diag = {'scale': 'macro', 'domain_lens': ['urban_governance'], 'outlet': '报告结论'}
    result = {'rows': [{'name': '宜昌城区', 'polarity_index': 0.15, 'domain_top': 'urban_governance',
                        'element_top': '环境', 'issue_label': '绿量不足', 'point_count': 1000}]}
    card = build_outlet_schema(diag, result, '中心城区城市体检评估')
    assert card is not None
    assert card['outlet_id'] == 'checkup_dimension', f'体检应命中 checkup_dimension（{card["outlet_id"]}）'
    # 城区维度（scale=macro）→ 填真实值
    assert '0.15' in str(card['fields'].get('城区维度', {}).get('value')), \
        f'城区维度应取 polarity_index（{card["fields"]}）'
    # 住房（micro）/小区（meso）/街区（meso）→ "需对应尺度分析"（不填城区值）
    for _dim in ('住房维度', '小区维度', '街区维度'):
        assert '需对应尺度分析' in str(card['fields'].get(_dim, {}).get('value', '')), \
            f'{_dim} 应标需对应尺度分析（{card["fields"]}）'


def test_wave1_checkup_dimension_meso_scale():
    """Wave 1：checkup_dimension meso 问句 → 小区/街区维度填值·城区/住房标尺度限定。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_governance'], 'outlet': '报告结论'}
    result = {'rows': [{'name': '西陵街道', 'polarity_index': -0.3, 'domain_top': 'urban_governance',
                        'element_top': '设施', 'issue_label': '停车难', 'point_count': 500}]}
    card = build_outlet_schema(diag, result, '西陵街道小区体检评估')
    assert card is not None
    # 小区维度 field_mapping = 'domain_top/element_top + polarity_index [scale=meso]'→ 主字段取首（domain_top·+ 只取首字段）
    assert '小区维度' in card['fields'] and 'urban_governance' in str(card['fields']['小区维度']['value']), \
        f'小区维度应取 domain_top（首字段·{card["fields"]}）'
    assert '需对应尺度分析' in str(card['fields'].get('城区维度', {}).get('value', '')), \
        f'城区维度（macro）应标需对应尺度分析（{card["fields"]}）'
    assert '需对应尺度分析' in str(card['fields'].get('住房维度', {}).get('value', '')), \
        f'住房维度（micro）应标需对应尺度分析（{card["fields"]}）'


def test_wave1_empty_rows_no_card():
    """Wave 1：空 rows（分析失败）→ 不出卡（防空卡·与前端 newLayerCount 门一致）。"""
    diag = {'scale': 'macro', 'domain_lens': ['urban_renewal'], 'outlet': '生成图层'}
    # 空 rows → _extract_emc_value 无 Top-1 → 字段全降级·但卡仍组装（无 P0）
    card = build_outlet_schema(diag, {'rows': []}, '宜昌城区更新优先')
    assert card is not None
    assert all(str(f.get('value')) != '' for f in card['fields'].values()), \
        f'空 rows 字段应降级非空（{card["fields"]}）'
