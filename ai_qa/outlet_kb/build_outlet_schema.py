"""出口卡片确定性组装器（结果范式 agent·第三段·Wave 0）。

把分析结果（图/数/观点）按行业接口契约组装成"出口卡片"（结构化 JSON·前端渲染）。
确定性组装——不调 LLM·数字必须代码算·不编造。

核心逻辑（出口驱动开发逻辑链落地）：
  出口契约（行业要什么表）→ 反推字段（field_mapping）→ 从分析产物取字段 → 组装卡片

设计（CB-16 Codex+glm 共识）：
- 不新增 LLM 阶段（撞 D019 红线·确定性比 LLM 编造更可信）
- 字段缺失降级（填"暂无数据"·不编造·glm 建议）
- 尺度分派（contract.scales 匹配·不匹配不出卡）
- place_name 诚实标注（"格内代表地名·粗略·CB-15 后升级"）
"""
from __future__ import annotations

from . import OUTLET_CONTRACTS

# 条件触发词表（EMC 侧接口词·与 emc-patterns.js 词表一致·用户定案方案 A）
# 注意：此表是 EMC 理解逻辑（什么词触发出口）·放出向权威源；前端 emc-patterns.js 另有镜像
TRIGGER_WORDS = ('更新', '体检', '需求', '满意度', '排序', '识别', '时序', '改造')


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
        q_hit = any(w in q and (w in oid or w in contract.get('name', '')) for w in TRIGGER_WORDS)
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


def _extract_emc_value(result: dict, emc_field: str):
    """从分析结果取字段值（聚合产物 properties / 统计 dict）。缺失返回 None。"""
    if not result:
        return None
    # result 可能是统计 dict（polarity_index 等）或图层 fc（features properties）
    if isinstance(result, dict):
        if emc_field in result:
            return result[emc_field]
        # 从 features 取 Top-1 字段
        feats = result.get('features')
        if isinstance(feats, list) and feats:
            p = feats[0].get('properties', {}) if isinstance(feats[0], dict) else {}
            if emc_field in p:
                return p[emc_field]
    return None


def build_outlet_schema(diagnose: dict, result: dict, question: str = '') -> dict | None:
    """组装出口卡片（结构化 JSON·7 要素）。确定性·不调 LLM·不编造。

    返回 None = 未命中出口契约（不出卡·只出普通分析结果）。
    """
    oid = resolve_outlet_id(diagnose, question)
    if not oid:
        return None
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
    for industry_field, emc_expr in (contract.get('field_mapping') or {}).items():
        # emc_expr 可能含 "字段A + 字段B" 或 "字段A（说明）" 或 "不能测..."
        if '不能' in str(emc_expr):
            card['fields'][industry_field] = {'value': '（需客观数据·情绪地图不替代）', 'source': '边界'}
            continue
        # 取主字段（第一个标识符）
        main_field = str(emc_expr).split('+')[0].split('（')[0].split('/')[0].strip()
        if main_field and main_field not in ('图层', '评论'):
            val = _extract_emc_value(result, main_field)
            if val is not None:
                card['fields'][industry_field] = {'value': val, 'source': f'{main_field}（确定性）'}
            else:
                card['fields'][industry_field] = {'value': '暂无数据', 'source': '缺失·不编造'}
        else:
            card['fields'][industry_field] = {'value': emc_expr, 'source': '产物表达'}

    # 数据基础（点计数·若有）
    if isinstance(result, dict):
        n = result.get('point_count') or (result.get('stats', {}) or {}).get('point_count')
        if n is not None:
            card['data_base']['N'] = n
            card['data_base']['note'] = 'L2 聚合·时间窗待定'

    # 诚实标注（place_name 粗略·规则归因）
    card['limitations'].append('place_name = 格内代表地名（粗略·CB-15 后升级 POI 双源）')
    card['limitations'].append('归因 = 规则查表（DEMO·L4 深度归因待接入）')

    return card
