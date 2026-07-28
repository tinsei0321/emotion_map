"""0LLM 候选工具选择器（CB-09 轮次3a · 模块九 D035-D038 · Phase A）。

三阶段 diagnose 重构的 Stage 0（[01-diagnose-agent.md](../docs/catch-ball/emc-arch-deepdive/01-diagnose-agent.md)）：
纯规则·确定性·不调 LLM·<100ms。问句(+可选 context) → candidate_tools(1-4) + grounding + ask_scenario。

**Phase A（本文件）= eval-safe 基础**：
  - 不动 diagnose prompt / DIAGNOSE_TEMPLATE / eval_template_flash（守 83% 基线）。
  - 不接 harness 路由（影子或落地延到 Phase B）。
  - 仅提供纯函数 + 离线测试（tests/test_candidate_selector.py 复用 eval 语料）。
**Phase B**（后续）才把 Flash 选型前移到这里、prompt 45.8KB→1-3.5KB、重写 eval。

复用（勿重造）：
  - paradigm.B_TRACK_PARADIGM（B 赛道 keyword→template·[:122]）— base trigger 源。
  - paradigm._SINGLE_SKILL_IDS（候选合法性校验）。
  - core.field_dictionary.resolve_role / FIELD_ROLE_DICT（field→role·role→tool 消歧）。

设计偏离 [09-field-recognition.md](../docs/catch-ball/emc-arch-deepdive/09-field-recognition.md)「本地 JS」：选 Python 权威源
（eval 是 Python 红线须可测 + B_TRACK 已在 Python 收敛单一源 + 后端纯规则 <100ms 不增 round-trip·满足"快+不调 LLM"本意）。
"""
from core.field_dictionary import resolve_role  # noqa: F401  （re-export 供 Phase B grounding 用）
from ai_qa.paradigm import B_TRACK_PARADIGM, _SINGLE_SKILL_IDS
from core.tracker import register_track_id


# ════════════ role → tool 映射（D035 field-role 消歧）═══════════
# 工具所需字段角色：缺则数据不支撑 → 移除候选。set()=无硬字段依赖（preset/任意字段可）。
EMOTION_ROLES = frozenset({'polarity', 'score', 'emotion_type', 'emotion_intensity'})
BOUNDARY_ROLES = frozenset({'boundary_name', 'boundary_id', 'zone'})
LANDUSE_ROLES = frozenset({'land_use_class'})

TOOL_FIELD_REQUIRE = {
    'density': EMOTION_ROLES, 'hotspot': EMOTION_ROLES, 'rank': EMOTION_ROLES,
    'zonal': EMOTION_ROLES, 'compare': EMOTION_ROLES,
    'filter_attr': set(), 'clip': set(), 'buffer': set(), 'overlay': set(),
    'merge': set(), 'extract_feature': set(), 'area_stats': set(), 'nearest': set(),
}

# 工具所需几何（'point'/'polygon'/None=不限）。context 提供时收紧。
TOOL_GEOMETRY_REQUIRE = {
    'density': 'point', 'hotspot': 'point', 'rank': 'point', 'nearest': 'point',
    'buffer': 'point', 'clip': 'point',   # 5.242：clip 需点层（resolvePointLayer）·Phase A 误设 None·治剪裁面层误路由
    'zonal': None, 'compare': None, 'filter_attr': None,
    'overlay': None, 'merge': None, 'extract_feature': None, 'area_stats': None,
}

# 分析型优先排序（D035）：候选排序时分析型排前。
ANALYSIS_TOOLS = frozenset({'density', 'hotspot', 'zonal', 'rank', 'compare'})

# ════════════ B_TRACK trigger 扩展（本地·不动 diagnose prompt·eval-safe）═══════════
# paradigm.B_TRACK_PARADIGM 的 triggers 注入 diagnose prompt（改它=动 prompt=伤 eval）。
# 本选择器在 base 之上补 trigger（仅本地用·不回灌 prompt）。补的词是规则选择器需显式、而 Flash 靠语感能命的。
_B_TRACK_TRIGGER_EXT = {
    'overlay': ['重叠', '重合', '相交', '同一块'],
    'clip': ['里面的', '当中的', '某区', '这个区', '那个区', '剪裁', '裁剪', '裁剪出'],  # 剪裁/裁剪 = 裁点（has_point 时）·歧义词·与 extract 都入候选由 _filter_by_context 按数据裁决
    'extract_feature': ['只要', '单独', '抽出', '抠出', '裁出', '提取', '剪裁', '裁剪', '裁剪出', '剪裁出'],  # 剪裁/裁剪 = 抽面（has_polygon 时）·5.242 与 clip 歧义·数据过滤定夺
    'density': ['密集'],  # 补"密集"（B_TRACK 有"集中"无"密集"）
    'rank': [],  # rank 非 B 赛道（C 赛道·下方规则）
}


def _b_triggers():
    """B_TRACK base triggers + 本地扩展 → {template: [triggers]}（取并集）."""
    out = {}
    for arch in B_TRACK_PARADIGM:
        out[arch['template']] = list(arch['triggers'])
    for tpl, extra in _B_TRACK_TRIGGER_EXT.items():
        out.setdefault(tpl, [])
        for t in extra:
            if t not in out[tpl]:
                out[tpl].append(t)
    return out


# ════════════ track 派生（去 Flash 依赖）═══════════
_TRACK_A_KEYWORDS = ('什么', '原理', '意思是', '定义', '解释', '区别', '含义')
_TRACK_C_KEYWORDS = ('情绪', '极性', '消极', '积极', '归因', '负面', '正面', '状况', '感受', '满意度')
# rank（C 赛道·落点排序）vs zonal（C 赛道·宏观归因）消歧
_RANK_KEYWORDS = ('排序', '最差', '最好', '最需', '哪个点', '点位', '落点', 'top', 'Top', 'TOP', '排名')
_ZONAL_KEYWORDS = ('归因', '状况', '整体', '街道', '单元', '区域情绪', '区情绪', '概况')
_COMPARE_KEYWORDS = ('对比', '比较', 'VS', 'vs', 'versus', '哪个区更', '差异')
_AREA_STATS_KEYWORDS = ('面积', '占比', '用地结构', '各类用地')  # area_stats（C 赛道·面层结构统计）
# 化合物（≥2 动作 → multi）
_COMPOUND_CUES = ('并', '然后', '再', '接着', '之后', '同时')

_B_TRIGGERS = _b_triggers()


def _has_b_trigger(q):
    """问句是否命中任何 B 赛道 trigger."""
    for tpl, trigs in _B_TRIGGERS.items():
        if any(t in q for t in trigs):
            return True
    return False


def _b_hits(q):
    """问句命中的 B 赛道 template 列表（保序·B_TRACK_PARADIGM 顺序即优先级）."""
    hits = []
    for arch in B_TRACK_PARADIGM:
        tpl = arch['template']
        trigs = _B_TRIGGERS.get(tpl, arch['triggers'])
        if any(t in q for t in trigs) and tpl in _SINGLE_SKILL_IDS and tpl not in hits:
            hits.append(tpl)
    return hits


def _derive_track(question, b_hits):
    """问句 + B 命中 → track ∈ {A, B, C}.

    A 优先：强定义线索（什么是/原理/定义/意思）即使含工具词也归概念问
    （"什么是核密度分析"=问概念·非做密度分析）。
    compare 次优先：对比/比较 强信号 → C track（压过 B incidental trigger·如"比较两个区的消极占比"
    被 clip "区的" 误抢）。"""
    q = question or ''
    if any(k in q for k in _TRACK_A_KEYWORDS):
        return 'A'
    if any(k in q for k in _COMPARE_KEYWORDS):
        return 'C'
    if b_hits:
        return 'B'
    if any(k in q for k in _TRACK_C_KEYWORDS) or any(k in q for k in _RANK_KEYWORDS) \
       or any(k in q for k in _ZONAL_KEYWORDS) or any(k in q for k in _AREA_STATS_KEYWORDS):
        return 'C'
    return 'C'  # 默认情绪分析（EMC 主场景）


def _is_compound(question, b_hits):
    """化合物检测（→ multi）：≥2 不同 B 动作 / B动作+第二动作线索 / scope+analyze 模式."""
    q = question or ''
    if len(b_hits) >= 2:
        return True
    _scope = any(t in q for t in ('区内', '范围内', '里的', '里面', '当中的', '这个区', '那个区'))
    _analyze = any(k in q for k in ('密度', '热力', '归因', '排序', '情绪分析', '热点'))
    # B 动作 + "并/然后/再" + 分析动作 → 复合
    if b_hits and any(c in q for c in _COMPOUND_CUES) and _analyze:
        return True
    # scope（区内/范围内）+ analyze（密度/归因/排序）→ extract/clip + 分析 = 复合
    if _scope and _analyze:
        return True
    return False


def select_candidates(question, context=None):
    """0LLM 候选工具选择（纯规则·D035-D038）。

    Args:
        question: 用户问句。
        context: dict | None。{field_roles: set[str], has_point: bool, has_polygon: bool}。
                 None/空 = 宽容模式（不按字段/几何过滤·对齐 eval：eval 只给问句无 context）。
    Returns:
        {candidates: [skill_id], grounding: str, ask_scenario: int|None, track: str, compound: bool}
        - candidates: 1-4 个 single 技能 id（+ 可能含 'multi'/'concept'）。
        - ask_scenario: None=正常/短路；1-6=≥5 候选追问场景（09-field-recognition §三）。
        - compound: 是否检出化合物（multi）。
    """
    ctx = context or {}
    field_roles = frozenset(ctx.get('field_roles') or [])
    has_point = ctx.get('has_point')
    has_polygon = ctx.get('has_polygon')
    q = question or ''

    b_hits = _b_hits(q)
    track = _derive_track(q, b_hits)
    compound = _is_compound(q, b_hits)

    # 1. track → 初始候选
    if track == 'A':
        return {'candidates': ['concept'], 'grounding': _grounding(field_roles, has_point, has_polygon),
                'ask_scenario': None, 'track': 'A', 'compound': False}

    candidates = []
    if track == 'B':
        candidates = list(b_hits)
        if not candidates:
            candidates = ['multi']  # B 识别不到具体原型 → 多步兜底（同 select_template）
    else:  # track == C
        if any(k in q for k in _COMPARE_KEYWORDS):
            candidates = ['compare']
        else:
            # area_stats/rank/zonal 都入候选（让 Phase B Flash/Pro 按 scale 定夺）·优先排序后
            cands = []
            if any(k in q for k in _AREA_STATS_KEYWORDS):
                cands.append('area_stats')
            if any(k in q for k in _RANK_KEYWORDS):
                cands.append('rank')
            if any(k in q for k in _ZONAL_KEYWORDS):
                cands.append('zonal')
            candidates = cands or ['zonal']  # 默认宏观归因（EMC 主场景）

    # 2. 化合物 → 加 multi（候选头部）
    if compound and 'multi' not in candidates:
        candidates = ['multi'] + candidates

    # 3. field-role + geometry 收紧（仅 context 提供时·eval 无 context 跳过保可比性）
    if field_roles or has_point is not None or has_polygon is not None:
        candidates = _filter_by_context(candidates, field_roles, has_point, has_polygon)
        # 5.242：过滤后若 real tools（非 multi/concept）< 2 → 移除 stale multi（compound 在过滤前判·过滤后可能只剩 1 工具·不再是复合）
        _real_after = [t for t in candidates if t not in ('multi', 'concept')]
        if 'multi' in candidates and len(_real_after) < 2:
            candidates = [t for t in candidates if t != 'multi']

    # 4. 分析型优先排序（multi/concept 保头）+ 截断到 4
    def _sort_key(t):
        if t in ('multi', 'concept'):
            return (0, t)
        return (1, 0 if t in ANALYSIS_TOOLS else 2, t)
    candidates = sorted(candidates, key=_sort_key)
    pre_truncate = len(candidates)
    candidates = candidates[:4]

    # 5. 三态出口（D037/D038）
    ask_scenario = None
    if not candidates:
        ask_scenario = None  # =0 短路（caller 据 candidates==0 判提示导入）
    elif pre_truncate > 4:
        ask_scenario = _pick_ask_scenario(candidates)

    return {'candidates': candidates, 'grounding': _grounding(field_roles, has_point, has_polygon),
            'ask_scenario': ask_scenario, 'track': track, 'compound': compound}


def _filter_by_context(candidates, field_roles, has_point, has_polygon):
    """按可见字段角色 + 几何收紧候选（D035 field 消歧·5.242 数据感知）。

    field_roles 空时只按几何（has_point/has_polygon）过滤·不按字段（前端 layer_meta 只送几何·字段未送时勿误剔）。"""
    out = []
    for t in candidates:
        if t in ('multi', 'concept', 'unknown'):
            out.append(t)
            continue
        require = TOOL_FIELD_REQUIRE.get(t)
        if require and field_roles and not (field_roles & require):
            continue  # field_roles 提供时才按字段过滤（空=未知=跳过·5.242 防 density 被误剔）
        geo = TOOL_GEOMETRY_REQUIRE.get(t)
        if geo == 'point' and has_point is False:
            continue
        if geo == 'polygon' and has_polygon is False:
            continue
        out.append(t)
    return out


def _pick_ask_scenario(candidates):
    """≥5 候选 → 追问场景（09-field-recognition.md §三）。"""
    analysis = [t for t in candidates if t in ANALYSIS_TOOLS]
    spatial = [t for t in candidates if t not in ANALYSIS_TOOLS and t not in ('multi', 'concept')]
    if analysis and not spatial:
        return 1
    if spatial and not analysis:
        return 2
    if analysis and spatial:
        return 3
    return 6  # 兜底


def _grounding(field_roles, has_point, has_polygon):
    """精简 grounding（Phase B 注入 Flash 用·Phase A 仅返回字符串）。"""
    parts = []
    if field_roles:
        parts.append('字段角色：' + '/'.join(sorted(field_roles)[:8]))
    if has_point:
        parts.append('有点层')
    if has_polygon:
        parts.append('有面层')
    return '；'.join(parts) if parts else ''


# ════════════ 追踪 ID 注册（MOD_AIQA 扩展）═══════════
register_track_id("MOD_AIQA.F_012", "select_candidates（0LLM 候选工具选择·模块九 D035-D038·Phase A 纯规则·5.242 context 接回）")


if __name__ == '__main__':
    # 自检：几条代表问
    for q in ('做核密度分析', '哪里情绪最集中', '各区情绪排序', '什么是核密度分析',
              '对比西陵区和伍家岗区情绪', '西陵区的商业用地', '滨江公园 500 米缓冲'):
        r = select_candidates(q)
        print(f"  [{r['track']}] {q} → {r['candidates']}" + (f" (compound)" if r['compound'] else ''))
