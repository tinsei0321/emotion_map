"""出向知识库 · 全项目行业接口契约（v1）· 出口卡片组装的数据基础。

与入向知识库（ai_qa/industry_kb/）的职责区分：
- industry_kb（入向）= 给 LLM 注入政策/术语（prompt 语境·让 AI 用专业话语作答）。
- outlet_kb（出向）= 定义行业接口契约 + 案例库 + 指标库（结果范式 agent 确定性组装
  出口卡片的数据源·让分析结果"填进行业已有的表"）。

**设计哲学**（对齐 CLAUDE.md 出口抽象层）：
- EMC 找市场接口，非市场找 EMC——每个出口卡片对应行业具体表单项（问题清单/更新项目
  统计表/满意度问卷等）。
- 一一对应：行业要求字段 → 情绪地图产出字段（图/数/表/观点）。
- 边界诚实：能/不能双栏——情绪=市民感知（主观），不替代客观检测（结构/数量）。
- 可成长：政策/案例更新 → 模块更新。

本包是出向单一权威源；改各领域 = 改权威源。结果范式 agent（build_outlet_schema）
查询契约 → 组装出口卡片 → 前端渲染。确定性组装，不靠 LLM 编造数字。
"""
from . import urban_renewal_outlets, urban_checkup_outlets, case_library

# 出口契约注册表（outlet_id → 契约定义·补 domain 字段=来源模块 DOMAIN）
OUTLET_CONTRACTS = {}
for _mod, _domain in ((urban_renewal_outlets, urban_renewal_outlets.DOMAIN),
                      (urban_checkup_outlets, urban_checkup_outlets.DOMAIN)):
    for _oid, _c in _mod.CONTRACTS.items():
        _c.setdefault('domain', _domain)
        OUTLET_CONTRACTS[_oid] = _c

# 指标库（行业官方指标 → 情绪地图字段映射）
METRIC_MAPPINGS = {}
METRIC_MAPPINGS.update(urban_renewal_outlets.METRIC_MAPPINGS)
METRIC_MAPPINGS.update(urban_checkup_outlets.METRIC_MAPPINGS)

# 案例库（城市真实做法 → 情绪地图对接）
CASE_LIBRARY = case_library.CASES


def get_outlet_contract(outlet_id):
    """按 outlet_id 查出口契约（含接口标识/适用尺度/字段映射/所需产物字段）。"""
    return OUTLET_CONTRACTS.get(outlet_id)


def get_metric_mapping(metric_id):
    """按行业指标查情绪地图字段映射（能/不能双栏）。"""
    return METRIC_MAPPINGS.get(metric_id)


def get_case(city_key):
    """按城市查案例（真实数据 + 情绪地图对接）。"""
    return CASE_LIBRARY.get(city_key)


def outlet_kb_brief_text(domain_lens):
    """渲染命中领域的出口契约速查（供结果范式 agent / prompt 参考·轻量）。"""
    seen = []
    for dk in domain_lens or []:
        if dk and dk not in seen:
            seen.append(dk)
    if not seen:
        return ''
    lines = ['出向接口速查（行业表单项 → 情绪地图产出）：']
    for oid, c in OUTLET_CONTRACTS.items():
        if c.get('domain') in seen:
            lines.append(
                f"- {c.get('name','')}（{oid}）· 对接 {c.get('industry_interface','')}"
                f"· 尺度 {c.get('scales','')} · 字段映射 {list(c.get('field_mapping',{}).keys())}"
            )
    return '\n'.join(lines)


__all__ = [
    'OUTLET_CONTRACTS', 'METRIC_MAPPINGS', 'CASE_LIBRARY',
    'get_outlet_contract', 'get_metric_mapping', 'get_case', 'outlet_kb_brief_text',
    'urban_renewal_outlets', 'urban_checkup_outlets', 'case_library',
]
