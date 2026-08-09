"""出口卡片组装器测试（Wave 0·S2 打穿核心守卫）。

确定性组装验证：resolve_outlet_id 路由 + build_outlet_schema 7 要素 + 字段缺失降级 + 尺度分派。
"""
import pytest

from ai_qa.outlet_kb.build_outlet_schema import resolve_outlet_id, build_outlet_schema, build_outlet_schema_single


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
    card = build_outlet_schema_single(_diag(), _result(), '西陵区老旧小区更新需求分析')
    assert card is not None
    assert card['interface'].startswith('片区策划')     # 接口标识
    assert card['task_link']                            # 对接建议
    assert card['fields']                               # 定量/定性/地理定位
    assert card['data_base']['N'] == 1247               # 数据基础
    assert card['limitations']                          # 局限标注
    assert card['can'] and card['cannot']               # 能/不能双栏


def test_build_outlet_schema_field_mapping():
    """field_mapping 确定性取值（polarity_index → 需求强度）。"""
    card = build_outlet_schema_single(_diag(), _result(polarity=-0.3), '西陵区更新需求分析')
    # 需求强度 ← polarity_index（field_mapping 里有 polarity_index 表达）
    any_neg = any('-0.3' in str(f.get('value')) for f in card['fields'].values())
    assert any_neg, f'需求强度未取到 polarity_index（fields={card["fields"]}）'


def test_build_outlet_schema_missing_field_degrade():
    """字段缺失 → 降级"暂无数据"（不编造）。"""
    card = build_outlet_schema_single(_diag(), {'point_count': 0}, '西陵区更新需求分析')
    # 无 features/字段 → 各字段降级
    for f in card['fields'].values():
        assert f['value'] is not None, '字段缺失应降级非 None'


def test_build_outlet_schema_no_hit():
    """未命中契约（outlet 空 + 无接口词）→ None（不出卡·只出普通分析）。"""
    assert build_outlet_schema_single(_diag(outlet=''), _result(), '生成热力图') is None


# ── CB-16 Codex/glm 修复后补测（3 缺口）────────────────────
def test_qualifier_field_parsed():
    """CB-16 Codex：qualifier 后缀（降序/占比）应解析出主字段（防丢值）。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '指标排序'}
    card = build_outlet_schema_single(diag, {'polarity_index': -0.45, 'point_count': 5,
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
    card = build_outlet_schema_single(diag, result, '大南门·二马路片区更新需求分析')
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
    card = build_outlet_schema_single(diag, result, '宜昌城区哪些区域更新优先')
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
    card = build_outlet_schema_single(diag, result, '中心城区城市体检评估')
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
    card = build_outlet_schema_single(diag, result, '西陵街道小区体检评估')
    assert card is not None
    # 小区维度 field_mapping = 'domain_top/element_top + polarity_index [scale=meso]'→ 主字段取首（domain_top·+ 只取首字段）
    assert '小区维度' in card['fields'] and 'urban_governance' in str(card['fields']['小区维度']['value']), \
        f'小区维度应取 domain_top（首字段·{card["fields"]}）'
    assert '需对应尺度分析' in str(card['fields'].get('城区维度', {}).get('value', '')), \
        f'城区维度（macro）应标需对应尺度分析（{card["fields"]}）'
    assert '需对应尺度分析' in str(card['fields'].get('住房维度', {}).get('value', '')), \
        f'住房维度（micro）应标需对应尺度分析（{card["fields"]}）'


def test_wave1_empty_rows_degrades():
    """Wave 1：空 rows（分析失败）→ 后端容错组装·字段降级非空（前端门拦截不出卡·分工）。

    前端 _maybeBuildOutletCard 的 `_hasRows`（空 rows false）+ newLayerCount<=0 → return null（不出卡）。
    后端 build_outlet_schema 空 rows → _extract_emc_value 无 Top-1 → 字段全降级（诚实·不编造）。
    """
    diag = {'scale': 'macro', 'domain_lens': ['urban_renewal'], 'outlet': '生成图层'}
    # 空 rows → _extract_emc_value 无 Top-1 → 字段全降级·但卡仍组装（后端容错·前端门拦截）
    card = build_outlet_schema_single(diag, {'rows': []}, '宜昌城区更新优先')
    assert card is not None
    assert all(str(f.get('value')) != '' for f in card['fields'].values()), \
        f'空 rows 字段应降级非空（{card["fields"]}）'


# ── CB-15 P1（D）：归因落点模板（+ 组合合成 + poi_names/place_name_source 暴露）──
def test_wave_p1_composite_field_mapping():
    """CB-15 P1（D）：field_mapping 组合表达式（字段A + 字段B）→ 多字段合成取值（非首字段单取）。

    扩 _extract_emc_value 支持 + 合成：place_name + issue_label 逐字段取·非空 join·治"需求位置"落点组合。
    """
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    result = {
        'rows': [{'place_name': '大南门·二马路滨江片区', 'issue_label': '停车难',
                  'polarity_index': -0.32, 'point_count': 900}],
    }
    # 手动构造：用带 + 组合的 field_mapping（renewal_demand 需求位置 = 'place_name + 网格/POI'）
    card = build_outlet_schema_single(diag, result, '大南门·二马路片区更新需求分析')
    assert card is not None
    vals = {k: str(f.get('value')) for k, f in card['fields'].items()}
    assert '大南门' in vals.get('需求位置', ''), f'需求位置应含 place_name（组合合成·{vals}）'
    assert '停车难' in vals.get('问题类型', ''), f'问题类型应含 issue_label（{vals}）'


def test_wave_p1_poi_fields_exposed():
    """CB-15 P1（D）：聚合产物 poi_names/place_name_source 暴露给出口卡（地点清单 + 置信度来源）。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    result = {
        'rows': [{'place_name': '大南门', 'place_name_source': 'poi_sjoin',
                  'poi_names': '滨江公园、二马路老巷 等3处', 'issue_label': '停车难',
                  'polarity_index': -0.32, 'point_count': 900}],
    }
    card = build_outlet_schema_single(diag, result, '大南门更新需求分析')
    assert card is not None
    # 需求位置 ← place_name（组合内）+ 若 field_mapping 消费 poi_names 则出现
    vals = {k: str(f.get('value')) for k, f in card['fields'].items()}
    assert '大南门' in vals.get('需求位置', ''), f'需求位置应含 place_name（{vals}）'
    # limitations 不再陈旧（P0 已双源）
    lims = ' '.join(card['limitations'])
    assert 'CB-15 后升级 POI 双源' not in lims, f'陈旧文案应移除（{lims}）'
    assert '双源融合' in lims, f'应标双源融合（{lims}）'
    assert 'place_name_source' in lims, f'应标 place_name_source 置信度（{lims}）'


# ── Wave 3：多卡支持（跨 domain 多卡·同 domain 最高分·兼容单卡）──
def test_wave3_multi_card_cross_domain():
    """Wave 3（glm组）：跨 domain 多契约命中 → 多张卡（domain_lens 含 renewal + governance）。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal', 'urban_governance'], 'outlet': '建议清单'}
    result = {'rows': [{'place_name': '大南门', 'issue_label': '停车难', 'polarity_index': -0.32,
                        'domain_top': 'urban_renewal', 'element_top': '设施', 'point_count': 900}]}
    cards = build_outlet_schema(diag, result, '大南门片区更新需求与体检满意度')
    assert isinstance(cards, list) and cards, f'应出多卡（{cards}）'
    oids = [c['outlet_id'] for c in cards]
    assert 'renewal_demand' in oids, f'应含 renewal_demand（{oids}）'
    # 同 domain 最高分（renewal 只一张·不冗余）
    renewal = [c for c in cards if c['outlet_id'].startswith('renewal_')]
    assert len(renewal) == 1, f'同 domain renewal 应只一张（{oids}）'


def test_wave3_multi_card_compat_single():
    """Wave 3：build_outlet_schema_single 兼容（单 domain → 单卡·等价旧）。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    result = {'rows': [{'place_name': '大南门', 'issue_label': '停车难', 'polarity_index': -0.32,
                        'domain_top': 'urban_renewal', 'element_top': '设施', 'point_count': 900}]}
    card = build_outlet_schema_single(diag, result, '大南门片区更新需求')
    assert card is not None and card['outlet_id'] == 'renewal_demand'
    # 多卡版本首卡 = 单卡
    cards = build_outlet_schema(diag, result, '大南门片区更新需求')
    assert cards[0]['outlet_id'] == card['outlet_id']


def test_wave3_renewal_no_perceptible_gate():
    """③w2b（Codex/glm P1）：renewal 卡（urban_renewal·非体检域）不挂 perceptible_metrics（domain 门控）。

    可感知体检指标只挂体检域（urban_governance）卡·更新类卡不混挂（跨领域信息补充非预期）。
    """
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    result = {'rows': [{'place_name': '大南门', 'issue_label': '停车难', 'polarity_index': -0.32,
                        'domain_top': 'urban_renewal', 'element_top': '设施', 'point_count': 900}]}
    card = build_outlet_schema_single(diag, result, '大南门片区更新需求')
    assert card is not None and card['outlet_id'] == 'renewal_demand'
    assert 'perceptible_metrics' not in card, f'renewal 卡不应挂可感知指标（{card.get("perceptible_metrics")}）'


# ── Wave 3：可感知计算器（compute_perceptible_metrics·2a 极性类）──
def test_wave3_compute_perceptible_metrics():
    """Wave 3（glm组 2a）：可感知指标计算——极性类（含 polarity_index）出值·关键词命中标注·缺失诚实。"""
    from ai_qa.outlet_kb.build_outlet_schema import compute_perceptible_metrics
    result = {'rows': [{'polarity_index': -0.32, 'topic_top': '停车难',
                        'issue_label': '停车难', 'element_top': '设施'}]}
    metrics = compute_perceptible_metrics(result)
    assert metrics, f'应算可感知指标（{metrics}）'
    # 极性类指标都有值（含停车泊位缺口·宜居宜业等）
    vals = {m['metric']: m['value'] for m in metrics}
    assert '-0.32' in str(vals.get('停车泊位缺口（居民感知）', '')), f'停车指标应取 polarity_index（{vals}）'
    assert '-0.32' in str(vals.get('宜居宜业宜游感知', '')), f'宜居指标应取 polarity_index（{vals}）'
    # 关键词命中标注（停车泊位缺口：停车难 命中）
    kw = {m['metric']: m['source'] for m in metrics}
    assert '命中' in kw.get('停车泊位缺口（居民感知）', ''), f'停车指标应标关键词命中（{kw}）'
    # 缺失诚实
    metrics_empty = compute_perceptible_metrics({'rows': [{'issue_label': '停车难'}]})
    empty_vals = {m['metric']: m['value'] for m in metrics_empty}
    assert any(v == '暂无数据' for v in empty_vals.values()), f'缺失应降级暂无数据（{empty_vals}）'


# ── ③z2 可感知计算器 2b（B 类条件等式·Codex/glm 反评价采纳）──
def test_wave3_2b_conditional_match():
    """③z2 2b：条件匹配（element_top=环境 + 关键词命中）→ B 类指标出值 + source 标条件/命中。"""
    from ai_qa.outlet_kb.build_outlet_schema import compute_perceptible_metrics
    result = {'rows': [{'element_top': '环境', 'topic_top': '公园散步',
                        'issue_label': '绿地不足', 'polarity_index': -0.3}]}
    metrics = compute_perceptible_metrics(result)
    by_name = {m['metric']: m for m in metrics}
    # 公园绿地步行可达性感知（B 类·条件=环境 + 值=topic_top + 关键词公园/绿地/散步）
    park = by_name.get('公园绿地步行可达性感知')
    assert park is not None, f'B 类应出值（{list(by_name)}）'
    assert '公园散步' in str(park['value']), f'应取 topic_top（{park}）'
    assert '条件' in park['source'] and '命中' in park['source'], f'source 应标条件+命中（{park["source"]}）'


def test_wave3_2b_conditional_mismatch_skipped():
    """③z2 2b：条件不匹配（element_top=设施·指标条件=环境）→ 跳过（不适用·不占卡面）。"""
    from ai_qa.outlet_kb.build_outlet_schema import compute_perceptible_metrics
    result = {'rows': [{'element_top': '设施', 'topic_top': '停车难',
                        'issue_label': '停车难', 'polarity_index': -0.3}]}
    metrics = compute_perceptible_metrics(result)
    names = {m['metric'] for m in metrics}
    assert '公园绿地步行可达性感知' not in names, f'条件不匹配应跳过（{names}）'


def test_wave3_2b_conditional_missing_elem():
    """③z2 2b：element_top 缺失 → B 类暂无数据（诚实·不编造）。"""
    from ai_qa.outlet_kb.build_outlet_schema import compute_perceptible_metrics
    result = {'rows': [{'topic_top': '公园散步', 'polarity_index': -0.3}]}
    metrics = compute_perceptible_metrics(result)
    by_name = {m['metric']: m for m in metrics}
    park = by_name.get('公园绿地步行可达性感知')
    assert park is not None and park['value'] == '暂无数据', f'条件缺失应暂无数据（{park}）'


def test_wave3_2b_multi_value_condition():
    """③z2 2b（glm）：多值条件 element_top=设施/环境（老旧街区改造）→ 匹配其一即出值。"""
    from ai_qa.outlet_kb.build_outlet_schema import compute_perceptible_metrics
    # element_top=环境 命中 设施/环境 条件（老旧街区改造·关键词 老旧/破旧）
    result = {'rows': [{'element_top': '环境', 'topic_top': '老旧破旧',
                        'issue_label': '老旧破败', 'polarity_index': -0.3}]}
    metrics = compute_perceptible_metrics(result)
    by_name = {m['metric']: m for m in metrics}
    renew = by_name.get('老旧街区改造需求感知')
    assert renew is not None, f'多值条件应匹配（{list(by_name)}）'
    assert '老旧破旧' in str(renew['value']) or '老旧破败' in str(renew['value']), f'应取 issue_label/topic_top（{renew}）'


def test_wave3_2b_keyword_miss_skipped():
    """③z2 2b（Codex P1②）：条件匹配 + value_field 有值但关键词未命中 → 跳过（防跨类误标）。"""
    from ai_qa.outlet_kb.build_outlet_schema import compute_perceptible_metrics
    # element_top=环境 匹配 公园绿地·但 topic_top=停车难·issue_label=停车（关键词 公园/绿地/散步 未命中）
    result = {'rows': [{'element_top': '环境', 'topic_top': '停车难',
                        'issue_label': '停车', 'polarity_index': -0.3}]}
    metrics = compute_perceptible_metrics(result)
    names = {m['metric'] for m in metrics}
    assert '公园绿地步行可达性感知' not in names, f'关键词未命中应跳过（{names}）'


def test_wave3_2b_ekon_shifted():
    """③z2 2b（Codex P1①）：生态宜居（element_top=环境 + polarity_index·可量化）走 2a 极性类·条件不参与判定。

    明示采纳「留 2a + docstring 注明」：生态宜居含 polarity_index → 2a 出极性值（其 element_top 条件为提示·不参与判定）。
    """
    from ai_qa.outlet_kb.build_outlet_schema import compute_perceptible_metrics
    result = {'rows': [{'element_top': '环境', 'polarity_index': -0.3,
                        'topic_top': '绿地不足', 'issue_label': '绿地不足'}]}
    metrics = compute_perceptible_metrics(result)
    by_name = {m['metric']: m for m in metrics}
    ekon = by_name.get('生态宜居')
    assert ekon is not None, f'生态宜居（2a 极性类·含 polarity）应出值（{list(by_name)}）'
    assert '-0.3' in str(ekon['value']), f'生态宜居应取 polarity_index（{ekon}）'


def test_wave3_p2_satisfaction_real_fields():
    """③z2 P2：checkup_satisfaction field_mapping prose→真实字段（满意度/8领域出值·非恒暂无数据）。"""
    from ai_qa.outlet_kb.build_outlet_schema import build_outlet_schema
    diag = {'scale': 'macro', 'domain_lens': ['urban_governance'], 'outlet': '报告结论'}
    result = {'rows': [{'polarity_index': 0.15, 'element_top': '环境', 'domain_top': 'urban_governance',
                        'issue_label': '绿量不足', 'place_name': '滨江', 'point_count': 1000}]}
    cards = build_outlet_schema(diag, result, '城市体检满意度调查')
    assert cards, f'应出卡（{cards}）'
    sat = [c for c in cards if c['outlet_id'] == 'checkup_satisfaction']
    assert sat, f'应命中满意度卡（{[c["outlet_id"] for c in cards]}）'
    fields = sat[0]['fields']
    # 满意度（4 尺度）← polarity_index
    assert '0.15' in str(fields.get('满意度（4 尺度）', {}).get('value', '')), f'满意度应取 polarity_index（{fields}）'
    # 8 领域情绪值 ← element_top/domain_top（/ 取首 element_top·中文）+ polarity_index
    assert '环境' in str(fields.get('8 领域情绪值', {}).get('value', '')), f'8领域应取 element_top（首字段·{fields}）'
    # 不满意项定位 ← issue_label + place_name
    assert '绿量不足' in str(fields.get('不满意项定位', {}).get('value', '')) and '滨江' in str(fields.get('不满意项定位', {}).get('value', '')), \
        f'不满意项定位应合成 issue_label+place_name（{fields}）'


# ── ③z3 Codex P2-3：value_field 缺失 + _parse_emc_expr 纯函数边界 ──
def test_wave3_2b_value_field_missing():
    """③z3 P2-3（Codex）：条件匹配 + value_field 缺失 → 暂无数据（诚实·不编造）。"""
    from ai_qa.outlet_kb.build_outlet_schema import compute_perceptible_metrics
    # element_top=环境 匹配 公园绿地·但 value_field（topic_top）缺失 → 暂无数据
    result = {'rows': [{'element_top': '环境', 'polarity_index': -0.3}]}
    metrics = compute_perceptible_metrics(result)
    by_name = {m['metric']: m for m in metrics}
    park = by_name.get('公园绿地步行可达性感知')
    assert park is not None and park['value'] == '暂无数据', f'value_field 缺失应暂无数据（{park}）'


def test_wave3_parse_emc_expr_boundary():
    """③z3 P2-3（Codex）：_parse_emc_expr 纯函数边界（空串/无+/keywords 空/无条件无极性）。"""
    from ai_qa.outlet_kb.build_outlet_schema import _parse_emc_expr
    assert _parse_emc_expr('') is None, '空串应 None'
    assert _parse_emc_expr('（客观·情绪地图补使用感受）') is None, '无字段无极性应 None'
    assert _parse_emc_expr('polarity_index') == {'polarity': True}, '纯 polarity 应极性类'
    # 条件等式（含多值 + 关键词）
    p = _parse_emc_expr('element_top=设施/环境 + issue_label（老旧/破旧）')
    assert p is not None
    assert p['condition_field'] == 'element_top' and p['condition_values'] == ['设施', '环境'], f'多值条件拆列表（{p}）'
    assert p['value_field'] == 'issue_label' and p['keywords'] == ['老旧', '破旧'], f'值字段+关键词（{p}）'
    # 无条件有值字段（异常形态）→ None（无 condition 无法判定）
    assert _parse_emc_expr('topic_top（公园）') is None, '无条件有值字段应 None'


# ── P1（出口三段式·P1P2 评估采纳）：需求强度分级 + 复合优先级 + 口径标注 + geo_label ──
def test_p1_demand_intensity_grading():
    """P1-1（glm B1 + Codex W1）：需求强度四档——值域双轨归一 + 积极区"无显著需求"。"""
    from ai_qa.outlet_kb.build_outlet_schema import grade_demand_intensity
    # L2 路径（值域 -2~2·归一化）：-2 → 高 / -1 → 中 / -0.3 → 中 / 0 → 低 / 0.4 → 无
    assert grade_demand_intensity(-2.0, 'L2')[0] == '高', 'L2 -2 应高'
    assert grade_demand_intensity(-1.0, 'L2')[0] == '中', 'L2 -1 应中（归一后 -0.5 以下才高·保留非常消极粒度）'
    assert grade_demand_intensity(-0.3, 'L2')[0] == '中', 'L2 -0.3 应中'
    assert grade_demand_intensity(0.0, 'L2')[0] == '低', 'L2 0 应低（中性附近）'
    assert grade_demand_intensity(0.4, 'L2')[0] == '无显著需求', 'L2 0.4 应无显著需求（积极）'
    # L1 路径（-1~1 直接用）：-1 → 高 / -0.3 → 中 / 0 → 低 / 0.4 → 无
    assert grade_demand_intensity(-1.0, 'L1')[0] == '高', 'L1 -1 应高'
    assert grade_demand_intensity(-0.3, 'L1')[0] == '中', 'L1 -0.3 应中'
    assert grade_demand_intensity(0.4, 'L1')[0] == '无显著需求', 'L1 0.4 应无显著需求'
    # 缺失 → 暂无数据
    assert grade_demand_intensity(None)[0] == '暂无数据', '缺失应暂无数据'


def test_p1_priority_score():
    """P1-2（Codex W2 + glm S1）：复合优先级——p95 归一 + 缺省不参与 + 主题契合 0/0.5/1。"""
    from ai_qa.outlet_kb.build_outlet_schema import priority_score
    # 强度主导：极性越负分越高
    high = priority_score({'polarity_index': -1.0, 'point_count': 100, 'domain_top': 'x', 'element_top': 'y'}, rows_max_pc=200)
    low = priority_score({'polarity_index': -0.1, 'point_count': 100, 'domain_top': 'x', 'element_top': 'y'}, rows_max_pc=200)
    assert high > low, f'强度应主导（high={high} low={low}）'
    # 覆盖度：point_count 高加分（p95 归一）
    more = priority_score({'polarity_index': -0.5, 'point_count': 190, 'domain_top': 'x', 'element_top': 'y'}, rows_max_pc=200)
    fewer = priority_score({'polarity_index': -0.5, 'point_count': 10, 'domain_top': 'x', 'element_top': 'y'}, rows_max_pc=200)
    assert more > fewer, f'覆盖度应加分（more={more} fewer={fewer}）'
    # 缺 point_count：不参与加权（其余归一·不反超实值行）
    missing = priority_score({'polarity_index': -0.5, 'domain_top': 'x', 'element_top': 'y'}, rows_max_pc=200)
    assert 0 <= missing <= 1, f'缺失覆盖度应合法（{missing}）'
    # 主题契合：都有 > 仅一者 > 全空
    both = priority_score({'polarity_index': -0.5, 'point_count': 100, 'domain_top': 'x', 'element_top': 'y'}, rows_max_pc=200)
    one = priority_score({'polarity_index': -0.5, 'point_count': 100, 'domain_top': 'x'}, rows_max_pc=200)
    none = priority_score({'polarity_index': -0.5, 'point_count': 100}, rows_max_pc=200)
    assert both > one > none, f'主题契合应 0/0.5/1（both={both} one={one} none={none}）'
    # 无主题意图（topic_intent=False）→ 主题项不参与（权重转强度）
    no_topic = priority_score({'polarity_index': -0.5, 'point_count': 100}, rows_max_pc=200, topic_intent=False)
    assert 0 <= no_topic <= 1, f'无主题意图应合法（{no_topic}）'


def test_p1_renewal_demand_intensity_in_card():
    """P1-1 接入：renewal_demand 卡补"需求强度等级"（四档·值+阈值说明）。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    result = {'rows': [{'place_name': '大南门', 'issue_label': '停车难', 'polarity_index': -1.2,
                        'domain_top': 'urban_renewal', 'element_top': '设施', 'point_count': 900}]}
    card = build_outlet_schema_single(diag, result, '大南门更新需求分析')
    assert card is not None
    grade = card['fields'].get('需求强度等级', {}).get('value')
    assert grade == '高', f'L2 -1.2 应高（{card["fields"]}）'


def test_p1_renewal_sequence_priority_in_card():
    """P1-2 接入：renewal_sequence 卡补"优先级排序"（复合规则·Top1）。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '指标排序'}
    result = {'rows': [
        {'name': '西陵区', 'polarity_index': -1.5, 'point_count': 500, 'domain_top': 'urban_renewal', 'element_top': '设施'},
        {'name': '伍家岗区', 'polarity_index': -0.3, 'point_count': 300, 'domain_top': 'urban_renewal', 'element_top': '环境'},
    ]}
    card = build_outlet_schema_single(diag, result, '宜昌城区更新时序排序')
    assert card is not None
    assert card['outlet_id'] == 'renewal_sequence', f'应命中 renewal_sequence（{card["outlet_id"]}）'
    prio = card['fields'].get('优先级排序', {}).get('value', '')
    assert '西陵区' in prio, f'优先级应取 Top1（西陵·极性最强·{card["fields"]}）'


def test_p1_geo_label_scale():
    """P2（glm S4）：出口卡 geo_label——按尺度标注（宏观=面域/中观=单元/微观=落点）。"""
    diag = {'scale': 'macro', 'domain_lens': ['urban_renewal'], 'outlet': '生成图层'}
    result = {'rows': [{'name': '西陵区', 'polarity_index': -0.42, 'domain_top': 'urban_renewal',
                        'element_top': '环境', 'issue_label': '老旧破败', 'point_count': 300}]}
    card = build_outlet_schema_single(diag, result, '宜昌城区更新优先')
    assert card is not None
    assert card['geo_label'].startswith('宏观·面域'), f'macro geo_label 应标宏观·面域（{card["geo_label"]}）'
    # meso → 中观·单元
    diag2 = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    card2 = build_outlet_schema_single(diag2, {'rows': [{'place_name': '大南门', 'polarity_index': -0.3,
                                                         'issue_label': '停车难', 'point_count': 900}]}, '大南门更新需求')
    assert card2['geo_label'].startswith('中观·单元'), f'meso geo_label 应标中观·单元（{card2["geo_label"]}）'
    # micro → 微观·落点（CB-18 S-4 补证·else 兜底分支）
    diag3 = {'scale': 'micro', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    card3 = build_outlet_schema_single(diag3, {'rows': [{'place_name': 'CBD', 'polarity_index': -0.5,
                                                         'issue_label': '配套不足', 'point_count': 60}]}, 'CBD 落点分析')
    assert card3['geo_label'].startswith('微观·落点'), f'micro geo_label 应标微观·落点（{card3["geo_label"]}）'
    # 未知 scale → 不构建卡（诚实降级·不确定尺度不硬出行业卡）
    diag4 = {'scale': 'unknown', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    card4 = build_outlet_schema_single(diag4, {'rows': [{'place_name': 'X', 'polarity_index': -0.1,
                                                         'issue_label': 'Y', 'point_count': 10}]}, 'X')
    assert card4 is None, f'未知 scale 应不出卡（诚实降级·card4={card4}）'


def test_p1_limitations_case_benchmark_note():
    """P1-3（Codex/glm）：出口卡 limitations 统一追加"案例对标=参照非基准"卡级声明。"""
    diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    card = build_outlet_schema_single(diag, {'rows': [{'place_name': '大南门', 'polarity_index': -0.3,
                                                       'issue_label': '停车难', 'point_count': 900}]}, '大南门更新需求')
    lims = ' '.join(card['limitations'])
    assert '行业案例为对标参照' in lims, f'limitations 应含案例对标声明（{lims}）'


def test_p1_measure_note_in_cases():
    """P1-3：case_library 四案例均含 measure_note（口径标注·Codex 评估）。"""
    from ai_qa.outlet_kb.case_library import CASES
    for cid, case in CASES.items():
        assert case.get('measure_note'), f'案例 {cid} 缺 measure_note（口径标注）'
        assert case.get('source'), f'案例 {cid} 缺 source（已核实出处）'


# ═══ P3-4（CB-19）：动态 limitations + 微观落点精确化 ═══

def test_p3_4_dynamic_limitations_source():
    """P3-4 Gap A：limitations 按 place_name_source 动态标注（不硬编码"格内最近 POI"）。"""
    cases = [
        # (source, 应含子串·且不应含)
        ('poi_sjoin', '精确', '粗略'),
        ('poi_top_places', '面域代表名', '格内最近 POI'),
        ('spatial_hotspot', '粗略', '精确'),
        ('area_seed', '粗略', '精确'),
        (None, '未定位', '格内最近 POI'),
    ]
    for src, _must, _not in cases:
        diag = {'scale': 'meso', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
        row = {'place_name': '大南门', 'polarity_index': -0.3, 'issue_label': '停车难', 'point_count': 900}
        if src:
            row['place_name_source'] = src
        card = build_outlet_schema_single(diag, {'rows': [row]}, '大南门更新需求')
        lims = ' '.join(card['limitations'])
        assert _must in lims, f'source={src} limitations 应含 {_must}（{lims}）'
        assert _not not in lims, f'source={src} limitations 不应含 {_not}（{lims}）'


def test_p3_4_micro_poi_sjoin_already_precise():
    """P3-4：micro + poi_sjoin（已精确·格内最近 POI）→ 需求位置不变·source 标精确。"""
    diag = {'scale': 'micro', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    result = {'rows': [{'place_name': '万达广场', 'place_name_source': 'poi_sjoin',
                        'poi_names': '万达广场、沃尔玛 等2处', 'polarity_index': -0.5,
                        'issue_label': '配套不足', 'point_count': 60}]}
    card = build_outlet_schema_single(diag, result, '万达广场落点分析')
    loc = card['fields']['需求位置']
    assert '万达广场' in loc['value'], f'poi_sjoin 需求位置应保持 POI 名（{loc}）'
    assert '精确' in loc['source'], f'poi_sjoin source 应标精确（{loc}）'
    assert card['geo_label'].startswith('微观·落点'), f'geo_label 应微观·落点（{card["geo_label"]}）'


def test_p3_4_micro_polygon_upgrade_to_poi():
    """P3-4 Gap C：micro + poi_top_places（place_name=边界名·有 poi_names）→ 需求位置升级为首个 POI。"""
    diag = {'scale': 'micro', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    result = {'rows': [{'place_name': '大南门·二马路滨江片区', 'place_name_source': 'poi_top_places',
                        'poi_names': '滨江公园、二马路老巷 等3处', 'polarity_index': -0.32,
                        'issue_label': '停车难', 'point_count': 900}]}
    card = build_outlet_schema_single(diag, result, '大南门更新需求分析')
    loc = card['fields']['需求位置']
    assert '滨江公园' in loc['value'], f'micro+poi_top_places 需求位置应升级为首个 POI（{loc}）'
    assert 'POI 落点' in loc['source'], f'source 应标 POI 落点升级（{loc}）'
    assert card['geo_label'].startswith('微观·落点'), f'geo_label 应微观·落点（{card["geo_label"]}）'


def test_p3_4_micro_no_poi_honest():
    """P3-4：micro + 无 poi_names → 需求位置不动·source 标粗略（诚实不编造）。"""
    diag = {'scale': 'micro', 'domain_lens': ['urban_renewal'], 'outlet': '建议清单'}
    result = {'rows': [{'place_name': '西陵区', 'place_name_source': 'spatial_hotspot',
                        'polarity_index': -0.4, 'issue_label': '老旧', 'point_count': 30}]}
    card = build_outlet_schema_single(diag, result, '西陵区落点分析')
    loc = card['fields']['需求位置']
    assert '西陵区' in loc['value'], f'无 poi_names 需求位置应保持（{loc}）'
    assert '粗略' in loc['source'], f'无 poi_names source 应标粗略（{loc}）'
