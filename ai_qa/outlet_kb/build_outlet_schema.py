"""出口卡片确定性组装器（结果范式 agent·第三段·Wave 0）。

把分析结果（图/数/观点）按行业接口契约组装成"出口卡片"（结构化 JSON·前端渲染）。
确定性组装——不调 LLM·数字必须代码算·不编造。

核心逻辑（出口驱动开发逻辑链落地）：
  出口契约（行业要什么表）→ 反推字段（field_mapping）→ 从分析产物取字段 → 组装卡片

设计（CB-16 Codex+glm 共识）：
- 不新增 LLM 阶段（撞 D019 红线·确定性比 LLM 编造更可信）
- 字段缺失降级（填"暂无数据"·不编造·glm 建议）
- 尺度分派（contract.scales 匹配·不匹配不出卡）
- place_name 诚实标注（CB-15 P0 双源融合·place_name_source 标置信度）
"""
from __future__ import annotations

from . import OUTLET_CONTRACTS

# 条件触发词表（EMC 侧接口词·与 emc-patterns.js 词表一致·用户定案方案 A）
# 注意：此表是 EMC 理解逻辑（什么词触发出口）·放出向权威源；前端 emc-patterns.js 另有镜像
# CB-16 Codex："更新"过宽（"帮我更新图层"误触发）——排除 UI 语境（更新图层/更新时间/刷新）
TRIGGER_WORDS = ('更新', '体检', '需求', '满意度', '排序', '识别', '时序', '改造')
# UI 语境词（命中则不算"更新"接口触发·防"更新图层/更新时间"误出卡）
_UI_CONTEXT_WORDS = ('更新图层', '更新时间', '更新样式', '刷新', '重新加载')

# ── P1（出口三段式）：需求强度分级 + 复合优先级（确定性·不调 LLM）─────────
# polarity_index 值域双轨（glm P1P2 评估 B1）：L1 路径 -1~1（core/spatial_analysis.py:267）/
#   L2 路径 -2~2（:277-282）——分级前须归一化（L2 的 -2~2 → -1~1）·阈值统一用归一化后值
#   阈值与 frontend/js/state.js:329-338 valenceOf（±0.15/±1）对齐·防两处再漂移
_DEMAND_LEVELS = ('高', '中', '低', '无显著需求')


def grade_demand_intensity(polarity_index, level: str = 'L2'):
    """需求强度分级（P1-1·确定性）。四档：高/中/低/无显著需求。

    polarity_index 值域双轨归一（glm P1P2 B1）：
      L2 路径 -2~2 → 归一化 -1~1（/2）再分级·L1 路径 -1~1 直接用。
    阈值（归一化后·对齐 valenceOf）：
      高：pi<=-0.5（非常消极·需求强烈）｜中：-0.5<pi<=-0.15（消极·有需求）
      低：-0.15<pi<=0.15（中性附近）｜无显著需求：pi>0.15（积极·无负面需求）
    """
    if polarity_index is None:
        return ('暂无数据', 'polarity_index 缺失')
    pi = float(polarity_index)
    if level == 'L2':
        pi = max(-1.0, min(1.0, pi / 2.0))   # -2~2 → -1~1 归一化（保留"非常消极/消极"粒度）
    if pi < -0.5:
        return ('高', '极性 <-0.5（非常消极）·需求强烈')
    if pi <= -0.15:
        return ('中', '极性 -0.5~-0.15（消极）·有需求')
    if pi <= 0.15:
        return ('低', '极性 -0.15~0.15（中性附近）·无明显需求')
    return ('无显著需求', '极性 >0.15（积极）·无负面需求')


# 复合优先级权重（P1-2·启发式初值·待真实数据回归校准——glm P1P2 S1 诚实标注）
PRIORITY_WEIGHTS = {'intensity': 0.5, 'coverage': 0.3, 'topic': 0.2}


def priority_score(row: dict, rows_max_pc=None, topic_intent: bool = True) -> float:
    """更新时序复合优先级（P1-2·确定性·升级"polarity 降序"单一规则）。

    priority = 强度项×0.5 + 覆盖度项×0.3 + 主题契合项×0.2
      - 强度项：负向极性映射（归一化后 -1~1 → 0~1·越负越高）
      - 覆盖度项：point_count / rows_max_pc（**p95 替代全域 max**·Codex P1P2 修正·防离群格支配）
        ·缺省（无 point_count 或 rows_max_pc）→ 不参与加权（其余权重归一·Codex 修正·防缺失反超实值）
      - 主题契合项：domain_top+element_top 都有=1 / 仅一者=0.5 / 全空=0（Codex 修正·空不加分）
        ·问句无主题意图（topic_intent=False）→ 该项不参与（权重转强度·glm P1P2 S2）
    """
    import math
    # 强度项（负向极性映射·-1~1 → 0~1）
    pi = row.get('polarity_index') or row.get('score_mean') or 0
    try:
        pi = float(pi)
    except (TypeError, ValueError):
        pi = 0.0
    intensity = max(0.0, min(1.0, -pi))   # 越负 → 越接近 1（需求越强）

    # 覆盖度项（p95 归一·缺省不参与加权）
    coverage = None
    pc = row.get('point_count')
    if pc is not None and rows_max_pc:
        try:
            pc = float(pc)
            if pc > 0 and rows_max_pc > 0:
                coverage = min(1.0, pc / rows_max_pc)
        except (TypeError, ValueError):
            coverage = None

    # 主题契合项（0/0.5/1·问句无主题意图不参与）
    topic = None
    if topic_intent:
        has_d = bool(row.get('domain_top') or row.get('domain'))
        has_e = bool(row.get('element_top') or row.get('element'))
        topic = 1.0 if (has_d and has_e) else (0.5 if (has_d or has_e) else 0.0)

    # 加权求和（缺失项不参与·权重归一化）
    items = [('intensity', intensity)]
    if coverage is not None:
        items.append(('coverage', coverage))
    if topic is not None:
        items.append(('topic', topic))
    w_sum = sum(PRIORITY_WEIGHTS[k] for k, _ in items) or 1.0
    return sum(PRIORITY_WEIGHTS[k] * v for k, v in items) / w_sum


def resolve_outlet_id(diagnose: dict, question: str = '') -> str | None:
    """诊断卡（outlet+domain_lens+scale）+ 问句接口词 → OUTLET_CONTRACTS key。

    遍历契约，匹配 domain ∈ domain_lens + scale ∈ contract.scales + 问句接口词。
    返回最高优先级一个（问句关键词最强命中）；未命中返回 None（不出卡）。
    """
    if not diagnose:
        return None
    q = question or ''
    domain_lens = diagnose.get('domain_lens') or []
    scale = diagnose.get('scale') or ''
    outlet = diagnose.get('outlet') or ''

    # outlet 7 值（前端交互类型）→ 行业接口的粗略映射（A2 glm 方案）
    OUTLET_HINT = {
        '指标排序': ('renewal_sequence', 'checkup_satisfaction'),
        '报告结论': ('checkup_satisfaction', 'renewal_demand'),
        '建议清单': ('renewal_demand', 'renewal_content'),
        '生成图层': ('renewal_object_identify', 'checkup_dimension'),
    }
    hinted = OUTLET_HINT.get(outlet, ())

    best = None
    best_score = 0
    for oid, contract in OUTLET_CONTRACTS.items():
        # 必要条件：domain 匹配 + scale 匹配（契约只服务其领域/尺度）
        if contract.get('domain') not in domain_lens:
            continue
        if scale and scale not in contract.get('scales', []):
            continue
        score = 0
        # 触发条件（至少一个）：
        #   ① 问句接口词命中（契约名/标识含词·如"需求"→renewal_demand）
        #   ② outlet 提示命中（诊断卡判"建议清单/报告结论/指标排序"→ 对应行业接口）
        # CB-16 Codex：排除 UI 语境（"更新图层/更新时间"非行业接口词·不触发）
        q_clean = q
        for _ui in _UI_CONTEXT_WORDS:
            q_clean = q_clean.replace(_ui, '')
        q_hit = any(w in q_clean and (w in oid or w in contract.get('name', '')) for w in TRIGGER_WORDS)
        if q_hit:
            score += 3
        if oid in hinted:
            score += 2
        if score <= 0:
            continue  # 无触发（问句无接口词 + 诊断卡非行业类）→ 不出卡
        if score > best_score:
            best_score = score
            best = oid
    return best


def resolve_outlet_ids(diagnose: dict, question: str = '') -> list[str]:
    """多卡（Wave 3·glm组 P1）：多契约命中 → 按 score 降序的 oid 列表（跨 domain 多卡）。

    同 domain 只取最高分一张（防同 domain 多卡信息冗余·glm 预检 P1）。保留 resolve_outlet_id
    （返首个·兼容旧调用）。问句无接口词 + 诊断卡非行业类 → []（不出卡）。
    """
    if not diagnose:
        return []
    q = question or ''
    domain_lens = diagnose.get('domain_lens') or []
    scale = diagnose.get('scale') or ''
    outlet = diagnose.get('outlet') or ''
    OUTLET_HINT = {
        '指标排序': ('renewal_sequence', 'checkup_satisfaction'),
        '报告结论': ('checkup_satisfaction', 'renewal_demand'),
        '建议清单': ('renewal_demand', 'renewal_content'),
        '生成图层': ('renewal_object_identify', 'checkup_dimension'),
    }
    hinted = OUTLET_HINT.get(outlet, ())
    scored = []
    for oid, contract in OUTLET_CONTRACTS.items():
        if contract.get('domain') not in domain_lens:
            continue
        if scale and scale not in contract.get('scales', []):
            continue
        q_clean = q
        for _ui in _UI_CONTEXT_WORDS:
            q_clean = q_clean.replace(_ui, '')
        q_hit = any(w in q_clean and (w in oid or w in contract.get('name', '')) for w in TRIGGER_WORDS)
        score = 0
        if q_hit:
            score += 3
        if oid in hinted:
            score += 2
        if score > 0:
            scored.append((oid, contract.get('domain'), score))
    # 按 score 降序·同 domain 只取最高分（防冗余）
    scored.sort(key=lambda x: -x[2])
    seen_domains = set()
    out = []
    for oid, dom, sc in scored:
        if dom in seen_domains:
            continue
        seen_domains.add(dom)
        out.append(oid)
    return out


def _extract_emc_value(result: dict, emc_field: str):
    """从分析结果取字段值（统一收 rows/features/统计 dict 三类·Top-1）。

    CB-16 Wave 1（两组预检·claude组 ①）：单一入口规整 rows/features → 单一 features 视图——
    避免前端/后端各判一次产物形态（防漂移·单一真相源）。macro 分析（zonal/rank）权威产物
    是 rows 数组（已含 issue_label/polarity_index/domain_top/element_top）→ 每行当 feature.properties。
    """
    if not result or not isinstance(result, dict):
        return None
    # 顶层 dict 兜底（统计型 result：polarity_index 等直接键）
    if emc_field in result:
        return result[emc_field]
    # 统一规整为 features 列表（rows / features 两类 → 单一 features 视图）
    rows = result.get('rows')
    if isinstance(rows, list) and rows:
        feats = [{'properties': r} for r in rows if isinstance(r, dict)]   # rows 型：每行当 feature.properties（已同构）
    else:
        feats = result.get('features') or []
        if isinstance(feats, list):
            feats = [f if isinstance(f, dict) and 'properties' in f else {'properties': f} for f in feats]
    if not feats:
        return None
    # Top-1 取值（与 features 语义一致·macro 卡反映排名第一区域）
    p = feats[0].get('properties', {}) if isinstance(feats[0], dict) else {}
    if isinstance(p, dict) and emc_field in p:
        return p[emc_field]
    return None


def _parse_emc_expr(expr: str) -> dict | None:
    """解析 METRIC_MAPPINGS emc_field 表达式（确定性·纯函数·不调 LLM）。

    支持三类：
    - 极性类（含 polarity_index）：`polarity_index` / `topic_top（…）+ polarity_index` → {'polarity': True}
    - 条件等式（B 类）：`element_top=环境 + topic_top（公园/绿地/散步）` → {
        'condition_field': 'element_top', 'condition_values': ['环境'],
        'value_field': 'topic_top', 'keywords': ['公园', '绿地', '散步']}
    - 无条件无极性（（客观…）/满意度情绪值）→ None（不适用）

    `/` 语义两处（与 _build_card 的取首不同）：
    - 条件值 `element_top=设施/环境` → 拆多值列表 ['设施', '环境']（或 语义·匹配其一即算）
    - 关键词 `（公园/绿地/散步）` → 拆多关键词列表（任一命中即标注）
    """
    import re
    if not expr:
        return None
    if 'polarity_index' in expr:
        return {'polarity': True}
    # 条件等式：形如 'element_top=X[/Y] + 值字段（kw1/kw2）'
    _cm = re.search(r'([a-z_][a-z0-9_]*)=([^+]+)', expr)
    if not _cm:
        return None   # 无条件无极性（（客观…）/满意度情绪值）→ 不适用
    condition_field = _cm.group(1)
    condition_values = [v.strip() for v in _cm.group(2).split('/') if v.strip()]
    # 值部分：' + ' 之后的 '字段（关键词）'·取第一个 ASCII 字段
    _val_part = expr.split('+', 1)[1] if '+' in expr else ''
    _fm = re.search(r'([a-z_][a-z0-9_]*)', _val_part)
    value_field = _fm.group(1) if _fm else None
    _km = re.search(r'（([^）]+)）', _val_part)
    keywords = _km.group(1).split('/') if _km else []
    if not value_field:
        return None
    return {'condition_field': condition_field, 'condition_values': condition_values,
            'value_field': value_field, 'keywords': keywords}


def _build_card(oid: str, diagnose: dict, result: dict, question: str = '') -> dict | None:
    """组装单张出口卡片（7 要素·确定性）。返回 None = 尺度分派不匹配。"""
    contract = OUTLET_CONTRACTS.get(oid)
    if not contract:
        return None
    scale = diagnose.get('scale') or ''
    if scale and scale not in contract.get('scales', []):
        return None  # 尺度分派（不匹配不出卡）

    card = {
        'outlet_id': oid,
        'name': contract.get('name', ''),
        'interface': contract.get('industry_interface', ''),   # 接口标识
        'scale': scale,
        'task_link': contract.get('task_link', []),            # 对接建议
        'can': contract.get('can', ''),                        # 能（边界诚实）
        'cannot': contract.get('cannot', ''),                  # 不能（边界诚实）
        'fields': {},                                          # 定量/定性/地理定位
        'data_base': {},                                       # 数据基础
        'limitations': [contract.get('boundary', '')],         # 局限标注
        'source': '确定性组装（build_outlet_schema·非 LLM）',
    }

    # field_mapping：行业表单项 ← 情绪地图字段（确定性取值·缺失降级）
    # CB-16 Wave 1（Codex P1）：槽位 scale 限定——emc_expr 含 [scale=xxx] 时仅填匹配 diagnose.scale 的维度·其余"需对应尺度分析"
    #   （治 checkup_dimension 四维度×单尺度语义错位：macro 问句不再把城区值填进住房/小区/街区槽）
    import re as _re
    for industry_field, emc_expr in (contract.get('field_mapping') or {}).items():
        # emc_expr 可能含 "字段A + 字段B" 或 "字段A（说明）" 或 "不能测..." 或 "[scale=xxx]"
        _sm = _re.search(r'\[scale=([a-z]+)\]', str(emc_expr))
        if _sm and _sm.group(1) != scale:
            card['fields'][industry_field] = {'value': '（需对应尺度分析·当前 ' + (scale or '未知') + '）', 'source': 'scale 限定'}
            continue
        if '不能' in str(emc_expr):
            card['fields'][industry_field] = {'value': '（需客观数据·情绪地图不替代）', 'source': '边界'}
            continue
        # 取字段（支持 "字段A + 字段B" 组合·CB-15 P1 glm组/Codex：扩 + 号合成——逐字段取值·非空 join·治落点组合）
        #   去尾部限定词（降序/占比/排序/负数/正数/TOPn）+ scale 标记；每个 + 分隔的字段独立取·空值跳过
        _expr_clean = _re.sub(r'\[scale=[a-z]+\]', '', str(emc_expr))
        _field_parts = [_re.split(r'\s*(?:降序|占比|排序|负数|正数|TOP\d+)', p)[0].split('（')[0].split('/')[0].strip()
                        for p in _expr_clean.split('+')]
        _field_parts = [p for p in _field_parts if p and p not in ('图层', '评论')]
        if _field_parts:
            # 逐字段取·非空 join（P2·Codex/glm）：source 只列实际提取字段（非空 parts）·value 同
            _extracted = [(p, _extract_emc_value(result, p)) for p in _field_parts]
            _nonempty = [(p, v) for p, v in _extracted if v is not None]
            if _nonempty:
                card['fields'][industry_field] = {'value': '、'.join(str(v) for _, v in _nonempty),
                                                  'source': '、'.join(f'{p}（确定性）' for p, _ in _nonempty)}
            else:
                card['fields'][industry_field] = {'value': '暂无数据', 'source': '缺失·不编造'}
        else:
            card['fields'][industry_field] = {'value': emc_expr, 'source': '产物表达'}

    # ── P3-4（CB-19）：微观落点精确化——micro 尺度时需求位置按 place_name_source + poi_names 升级 ──
    #   治 Gap C（polygon/rank-on-boundary 下 place_name 仍是边界名/粗略众数·非 POI 落点）。
    #   复用 _extract_emc_value（Top-1 row）·不新建字段·诚实标注 source。确定性·不调 LLM。
    if scale == 'micro' and '需求位置' in card['fields']:
        _src = _extract_emc_value(result, 'place_name_source')
        _pois = _extract_emc_value(result, 'poi_names')
        _loc = card['fields']['需求位置']
        if _src == 'poi_sjoin':
            # 已精确（place_name=格内最近 POI）·仅 source 补注
            _loc['source'] = 'place_name（精确·poi_sjoin·格内最近 POI）'
        elif _pois:
            # polygon/rank-on-boundary：place_name=边界名·升级为首个 POI（精确落点）
            _first_poi = str(_pois).split('、')[0].strip()
            _loc['value'] = _first_poi if _first_poi else _loc.get('value', '')
            _loc['source'] = 'place_name（POI 落点·poi_names 首个·精确）' + (f'｜面域代表名兜底 {_loc.get("value", "")}' if _loc.get('value') else '')
        else:
            # 无 POI 落点·诚实标粗略
            _loc['source'] = 'place_name（粗略·无 POI 落点·' + (str(_src or 'source 缺失') + '）')

    # ── P1（出口三段式）：需求强度分级 + 复合优先级（确定性·Codex/glm P1P2 评估采纳）─────────
    if oid == 'renewal_demand' or oid in OUTLET_CONTRACTS and OUTLET_CONTRACTS[oid].get('name', '') == '更新需求摸排':
        # P1-1 需求强度等级（值域双轨归一·四档·glm B1 + Codex W1 修正）
        _pi_raw = _extract_emc_value(result, 'polarity_index')
        if _pi_raw is not None:
            _grade, _grade_note = grade_demand_intensity(_pi_raw, level=scale and 'L2' or 'L1')
            card['fields']['需求强度等级'] = {'value': _grade, 'source': f'极性 {_pi_raw}（{_grade_note}·确定性分级）'}
    if oid == 'renewal_sequence' or oid in OUTLET_CONTRACTS and OUTLET_CONTRACTS[oid].get('name', '') == '更新时序排序':
        # P1-2 复合优先级（p95 归一·缺省不参与·主题契合 0/0.5/1·Codex P1P2 修正）
        _rows = (result or {}).get('rows') or []
        if isinstance(_rows, list) and _rows:
            import math as _m
            _pcs = [float(r.get('point_count') or 0) for r in _rows if isinstance(r, dict) and r.get('point_count') is not None]
            if _pcs:
                _sorted_pc = sorted(_pcs)
                _p95 = _sorted_pc[int(_m.ceil(0.95 * len(_sorted_pc))) - 1] or 1.0
            else:
                _p95 = None
            _scored = [(r, priority_score(r, rows_max_pc=_p95)) for r in _rows if isinstance(r, dict)]
            _scored.sort(key=lambda x: -x[1])
            if _scored:
                _top_r, _top_s = _scored[0]
                _top_name = _top_r.get('place_name') or _top_r.get('name') or '关注区域'
                _top_pi = _top_r.get('polarity_index')
                card['fields']['优先级排序'] = {'value': f'{_top_name}（优先级 {_top_s:.2f}）',
                                                'source': f'复合规则（强度×{PRIORITY_WEIGHTS["intensity"]}·覆盖×{PRIORITY_WEIGHTS["coverage"]}·主题×{PRIORITY_WEIGHTS["topic"]}·确定性）'}

    # 数据基础（点计数·若有）
    # CB-16 Wave 1（claude组 ⑤）：rows 型（macro 分析）——N=区域单元数·note 区分·total_points 标总评论数（禁混用）
    if isinstance(result, dict) and isinstance(result.get('rows'), list) and result['rows']:
        _r = [x for x in result['rows'] if isinstance(x, dict)]
        if _r:
            card['data_base']['N'] = len(_r)   # 单元数（非评论数）
            _tp = sum(int(x.get('point_count') or 0) for x in _r)
            card['data_base']['note'] = f'{len(_r)} 个区域单元（单元评论数见 point_count 列）'
            if _tp:
                card['data_base']['total_points'] = _tp   # 总评论数
    elif isinstance(result, dict):
        n = result.get('point_count') or (result.get('stats', {}) or {}).get('point_count')
        if n is not None:
            card['data_base']['N'] = n
            card['data_base']['note'] = 'L2 聚合·时间窗待定'

    # 诚实标注（place_name 双源融合·CB-15 P1 修陈旧文案·P3-4 动态按 source·治 Gap A 硬编码误标）
    #   poi_sjoin → 精确（格内最近 POI）·poi_top_places → 面域代表名 + POI 增强·spatial_hotspot/area_seed → 粗略兜底·缺失 → 未定位
    _loc_src = _extract_emc_value(result, 'place_name_source')
    if _loc_src == 'poi_sjoin':
        card['limitations'].append('地点 = 格内最近 POI（精确·place_name_source=poi_sjoin·CB-15 双源融合）')
    elif _loc_src == 'poi_top_places':
        card['limitations'].append('地点 = 面域代表名（POI 增强·place_name_source=poi_top_places·双源融合）')
    elif _loc_src in ('spatial_hotspot', 'area_seed'):
        card['limitations'].append(f'地点 = 标注兜底（粗略·place_name_source={_loc_src}·无 POI 落点）')
    else:
        card['limitations'].append('地点 = 未定位（place_name_source 缺失·不编造）')
    card['limitations'].append('归因 = 规则查表（DEMO·L4 深度归因待接入）')
    # P1（Codex/glm P1P2 评估）：出口卡卡级声明——行业案例为对标参照非评分基准（防"对标上海 93.60 分"误当情绪地图产出）
    card['limitations'].append('行业案例为对标参照·非评分基准·数值口径以当地官方发布为准')
    # P2（glm P1P2 S4）：地理定位尺度标注（宏观=面域/中观=单元/微观=POI·让用户一眼看懂地点尺度）
    _scale_cn = {'macro': '宏观·面域', 'meso': '中观·单元', 'micro': '微观·落点'}.get(scale, '')
    card['geo_label'] = (_scale_cn + ('：' + (card['fields'].get('需求位置', {}).get('value') or '') if card['fields'].get('需求位置') else '')) if _scale_cn else ''

    # Wave 3（glm组）：可感知体检指标（2a 极性类·B 类条件等式后置）
    # ③w2b（Codex/glm P1）：仅体检域（urban_governance）挂可感知指标——更新类卡不混挂体检指标（跨领域信息补充非预期）
    if (contract.get('domain') or '') == 'urban_governance':
        card['perceptible_metrics'] = compute_perceptible_metrics(result)

    return card


def compute_perceptible_metrics(result: dict) -> list[dict]:
    """可感知体检指标计算（Wave 3·glm组 2a + 2b·确定性·不调 LLM）。

    对 METRIC_MAPPINGS 可感知指标分两类：
    - 2a 极性类（emc_field 含 polarity_index）：A 类极性直取 + C 类关键词+极性 → polarity_index 值 + 关键词命中标注
      （**含生态宜居**：其 expr = `element_top=环境 + polarity_index`·条件为提示·2a 不参与判定——Codex P1① 明示采纳）
    - 2b 条件等式（emc_field 形如 `element_top=环境 + topic_top（公园/绿地/散步）`·**可感知**）：条件匹配才出值
      （生态宜居等可量化组条件等式**不参与 2b**——仅可感知 industry 进 2b·Codex P1①）
    缺失 → '暂无数据'·条件不匹配/关键词未命中 → 跳过（不适用·不占卡面·Codex P1②）。
    """
    try:
        from .urban_checkup_outlets import METRIC_MAPPINGS
    except Exception:
        METRIC_MAPPINGS = {}
    out = []
    for metric_name, m in METRIC_MAPPINGS.items():
        expr = str(m.get('emc_field') or '')
        _parsed = _parse_emc_expr(expr)
        if _parsed is None:
            continue   # 无条件无极性（（客观…）/满意度情绪值）→ 不适用
        _industry = m.get('industry', '')
        if _parsed.get('polarity'):
            # ── 2a 极性类（含 polarity_index）──
            val = _extract_emc_value(result, 'polarity_index')
            if val is None:
                out.append({'metric': metric_name, 'value': '暂无数据',
                            'source': '缺失·不编造', 'industry': _industry})
                continue
            kw_hit = _kw_hit(expr, result)
            out.append({'metric': metric_name, 'value': val,
                        'source': 'polarity_index（确定性）' + (f'·{kw_hit}' if kw_hit else ''),
                        'industry': _industry})
            continue
        # ── 2b 条件等式（可感知·如公园绿地可达性）──
        if '可感知' not in _industry:
            continue   # 生态宜居等可量化组条件等式不参与 2b（Codex P1①）
        _elem = _extract_emc_value(result, _parsed['condition_field'])
        if _elem is None:
            out.append({'metric': metric_name, 'value': '暂无数据',
                        'source': '缺失·不编造', 'industry': _industry})
            continue
        _matched = [v for v in _parsed['condition_values'] if v in str(_elem)]
        if not _matched:
            continue   # 条件不匹配（该指标对当前要素不适用·不占卡面）
        _val = _extract_emc_value(result, _parsed['value_field'])
        if _val is None:
            out.append({'metric': metric_name, 'value': '暂无数据',
                        'source': '缺失·不编造', 'industry': _industry})
            continue
        # 关键词命中标注（未命中 → 跳过·防"停车"被标到"养老托育"名下·Codex P1②）
        kw_hit = ''
        _topic = _extract_emc_value(result, 'topic_top')
        _issue = _extract_emc_value(result, 'issue_label')
        for _kw in _parsed['keywords']:
            if (_topic and _kw in str(_topic)) or (_issue and _kw in str(_issue)):
                kw_hit = f'命中：{_kw}'
                break
        if not kw_hit:
            continue
        out.append({'metric': metric_name, 'value': _val,
                    'source': f"{_parsed['value_field']}（确定性）·条件：{_parsed['condition_field']}={_matched[0]}·{kw_hit}",
                    'industry': _industry})
    return out


def _kw_hit(expr: str, result: dict) -> str:
    """关键词命中标注（2a 共用）：emc_field 的（关键词）提示 → topic_top/issue_label 匹配。"""
    _topic = _extract_emc_value(result, 'topic_top')
    _issue = _extract_emc_value(result, 'issue_label')
    for _part in expr.split('+'):
        import re
        _pm = re.search(r'（([^）]+)）', _part)
        if _pm:
            for _kw in _pm.group(1).split('/'):
                if (_topic and _kw in str(_topic)) or (_issue and _kw in str(_issue)):
                    return f'命中：{_kw}'
    return ''


def build_outlet_schema(diagnose: dict, result: dict, question: str = '') -> list[dict]:
    """组装出口卡片（Wave 3·glm组 多卡）：多契约命中 → cards 列表（跨 domain 多卡·同 domain 最高分）。

    确定性·不调 LLM·不编造。返回 [] = 未命中出口契约（不出卡）。
    """
    oids = resolve_outlet_ids(diagnose, question)
    cards = []
    for oid in oids:
        c = _build_card(oid, diagnose, result, question)
        if c is not None:
            cards.append(c)
    return cards


def build_outlet_schema_single(diagnose: dict, result: dict, question: str = '') -> dict | None:
    """兼容旧调用（Wave 0/1/2）：返首卡或 None（多卡时取第一张·等价旧单卡）。"""
    cards = build_outlet_schema(diagnose, result, question)
    return cards[0] if cards else None
