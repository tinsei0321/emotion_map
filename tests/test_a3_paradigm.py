"""EMC A3① 专业范式树·结构测（CI 可跑）。

校验：
1) select_template 单一真相源纯函数——track + card + question → template 的判定正确（含 B 赛道关键词
   优先级裁断、B1 待建技能降级 multi、C 赛道 scale 映射）。
2) B_TRACK_PARADIGM 9 原型结构健全（archetype/stage/triggers/template/voice）。
3) SCALE_PARADIGM 3 尺度都含 method_templates + city_checkup_level（对齐住建部城市体检四层级）。
4) diagnose prompt 注入了 B 赛道范式树 + 选型决策树 + 城市体检层级。
"""
from ai_qa.paradigm import (
    B_TRACK_PARADIGM, SCALE_PARADIGM, TEMPLATE_REGISTRY, select_template,
    b_track_paradigm_text, select_template_text, scale_paradigm_text,
)
from ai_qa.prompts import build_diagnose_prompt


# ── select_template 真相源 ──────────────────────────────────────────
def test_select_A_concept():
    assert select_template('A', {}) == 'concept'
    assert select_template('A', {'scale': 'macro'}) == 'concept'   # A 无视 card


def test_select_B_keyword_priority():
    """B 赛道：问句关键词按 B_TRACK_PARADIGM 顺序匹配，先具体后泛。"""
    assert select_template('B', {}, '地铁站周边情绪') == 'buffer'          # 周边→buffer
    assert select_template('B', {}, '滨江公园500米缓冲') == 'buffer'        # 缓冲→buffer
    assert select_template('B', {}, '做核密度分析') == 'density'            # 核密度→density
    assert select_template('B', {}, '哪里情绪最集中') == 'density'          # 集中→density
    assert select_template('B', {}, '居住用地里情绪差的') == 'overlay'      # 用地里→overlay（先于 clip）
    assert select_template('B', {}, '某区的商业用地') == 'clip'             # 区的→clip（无 用地里）
    assert select_template('B', {}, '西陵区的情绪点') == 'clip'             # 区的→clip


def test_select_B_b1_skills_resolve_directly():
    """B1 已登记的 single 技能（nearest/hotspot/merge）→ 直接解析（不再降级 multi）。"""
    assert select_template('B', {}, '离地铁最近的负面点') == 'nearest'      # 最近→nearest（B1 已登记）
    assert select_template('B', {}, '负面聚集热点') == 'hotspot'            # 聚集/热点→hotspot（B1 已登记）
    assert select_template('B', {}, '合并几个街道成片区') == 'merge'        # 合并→merge（B1 已登记）


def test_select_B_filter_attr_resolves():
    """filter_attr（B1.5 已登记）→ 直接解析（B_TRACK 9 原型全 single，无 unregistered）。"""
    assert select_template('B', {}, '按用地类筛选') == 'filter_attr'        # 用地类→filter_attr（B1.5 已登记）


def test_select_B_no_match_multi():
    """识别不到具体原型 → multi（B 操作多步兜底）。"""
    assert select_template('B', {}, '某个无关的模糊问') == 'multi'


def test_select_C_scale_mapping():
    """C 赛道：scale → zonal/rank。"""
    assert select_template('C', {'scale': 'macro'}) == 'zonal'
    assert select_template('C', {'scale': 'meso'}) == 'zonal'
    assert select_template('C', {'scale': 'micro'}) == 'rank'
    assert select_template('C', {}) == 'zonal'   # scale 缺省→zonal


def test_select_unknown_track():
    assert select_template('X', {}) == 'unknown'


# ── B_TRACK_PARADIGM 结构 ───────────────────────────────────────────
def test_b_track_paradigm_structure():
    assert len(B_TRACK_PARADIGM) == 9, 'B 赛道 9 原型'
    valid_stages = {'Load', 'Transform', 'Analyze'}
    for a in B_TRACK_PARADIGM:
        for k in ('archetype', 'stage', 'triggers', 'template', 'voice'):
            assert k in a, f'B 原型缺字段 {k}: {a}'
        assert a['stage'] in valid_stages, f"非法 stage: {a['stage']}"
        assert isinstance(a['triggers'], list) and a['triggers'], f'triggers 应为非空 list: {a["archetype"]}'


def test_b_track_pending_marked():
    """未登记技能的原型（B1 待建）应能在 b_track_paradigm_text 标注 pending。"""
    _single = {s['skill'] for s in TEMPLATE_REGISTRY if s.get('category') == 'single'}
    txt = b_track_paradigm_text()
    for a in B_TRACK_PARADIGM:
        if a['template'] not in _single:
            assert 'multi' in txt, f"待建技能 {a['template']} 未标注 multi 降级"


# ── SCALE_PARADIGM 城市体检对齐 ─────────────────────────────────────
def test_scale_has_city_checkup_fields():
    for s in SCALE_PARADIGM:
        assert 'city_checkup_level' in s, f"缺 city_checkup_level: {s['scale']}"
        assert 'method_templates' in s and s['method_templates'], f"缺 method_templates: {s['scale']}"
    levels = [s['city_checkup_level'] for s in SCALE_PARADIGM]
    # 四层级（住房→小区→街区→城区）应有体现
    joined = ''.join(levels)
    assert '城区' in joined and ('小区' in joined or '住房' in joined) and '街区' in joined


def test_scale_text_renders_new_fields():
    txt = scale_paradigm_text()
    assert '城市体检层级' in txt and '默认方法模板' in txt
    for s in SCALE_PARADIGM:
        assert s['city_checkup_level'] in txt


# ── diagnose prompt 注入 ────────────────────────────────────────────
def test_diagnose_prompt_includes_paradigm_tree():
    p = build_diagnose_prompt('')
    assert 'B 赛道操作范式树' in p, 'diagnose prompt 未注入 B 赛道范式树'
    assert '选型决策树' in p and '单一真相源' in p, '未注入 select_template 决策树'
    for a in B_TRACK_PARADIGM:
        assert a['archetype'] in p, f"diagnose prompt 缺 B 原型: {a['archetype']}"
