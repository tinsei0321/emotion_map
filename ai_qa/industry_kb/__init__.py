"""行业知识库 · 全项目行业知识基础设施（v1）。

四领域权威源（规划·设计 / 更新 / 运营 / 治理），每领域含：顶层政策 + 核心概念体系 + 官方术语 +
可量化底线 + 项目类型（中微观聚焦）+ 其他城市案例 + 情绪归因焦点 + 4×5 矩阵多归属映射。

**设计哲学**（项目顶层纲领，见 CLAUDE.md）：
- 4×5 是归因落点矩阵（非指标分类清单），跨领域×跨要素多归属；矩阵骨架稳定。
- 归因底层逻辑 = 政策→情绪→项目：政策指引方向 → 情绪地图定位实际痛点 → 指向具体项目。
- 差异化 = 补官方话语盲区（如事件的瞬时空间影响）。
- 可成长：政策更新→模块更新→矩阵映射丰富；做厚路径见 docs/industry-knowledge-base.md。

本包是**单一权威源**（仿 ai_qa/landuse_codes_2023.py 模式）；改各领域 = 改权威源。
EMC 按 diagnose 产出的 domain_lens 命中时，post-diagnose 各 step（answer/revise/agent_step/review）
调 industry_kb_text(domain_key) 渲染该领域完整权威语境注入 prompt（diagnose 用 brief 速查）。
"""
from . import urban_planning, urban_renewal, urban_operation, urban_governance

# 四领域模块索引（顺序 = EMC domain_lens 常见顺序：规划/更新/运营/治理）
INDUSTRY_DOMAINS = {
    'urban_planning': urban_planning,
    'urban_renewal': urban_renewal,
    'urban_operation': urban_operation,
    'urban_governance': urban_governance,
}

# EMC 4×5 合法集（domain_key × element，对齐 CLAUDE.md 4×5 治理要素定义）
DOMAIN_KEYS = tuple(INDUSTRY_DOMAINS.keys())
ELEMENTS = ('设施', '环境', '服务', '文化', '事件')
ROLES = ('主', '次')


def get_matrix_mapping(domain_key):
    """某领域的 4×5 矩阵多归属映射 → list of (domain_key, element, role)。
    多归属是 feature（一领域知识可落多格）；role∈{主,次} 供归因计数的主/次约定。"""
    mod = INDUSTRY_DOMAINS.get(domain_key)
    return list(getattr(mod, 'MATRIX_MAPPING', [])) if mod else []


def industry_kb_text(domain_key):
    """渲染某领域权威语境为可读文本（全量字段，供 post-diagnose 各 step 按 domain_lens 注入 / 人读）。

    diagnose 出 domain_lens 后，answer/revise/agent_step/review 的 prompt 据此注入命中领域
    的完整权威语境——政策方向 / 核心概念 / 官方术语 / 底线指标 / 项目落点 / 要素归因细化 /
    他城案例 / 情绪归因焦点 / 4×5 矩阵多归属映射，使回答用权威话语 + 归因落到具体项目
    （政策→情绪→项目闭环）。diagnose 阶段用 brief 速查（全 4 域），不注本完整版（保 Flash eval）。
    v1→v2：补齐 ELEMENT_HINTS/KEY_TERMS 全表/METRICS_BASELINE/CASES（原仅 8 字段）。"""
    mod = INDUSTRY_DOMAINS.get(domain_key)
    if not mod:
        return ''
    lines = [f'【{mod.NAME}（{mod.DOMAIN_KEY}）· 权威语境】主管：{mod.AUTHORITY}']
    lines.append('顶层政策（方向）：')
    for d in mod.TOP_DESIGN:
        lines.append(f"  - {d['policy']}（{d['doc']}，{d['year']}）：{d['gist']}")
    lines.append('核心概念：')
    for k, v in mod.CORE_FRAMEWORK.items():
        lines.append(f'  - {k}：{v}')
    # 官方术语全表（brief 只取前 4，此处全量供回答用权威话语）
    kt = getattr(mod, 'KEY_TERMS', {})
    if kt:
        lines.append('官方术语：')
        for k, v in kt.items():
            lines.append(f'  - {k}：{v}')
    # 可量化底线（防止大拆大建拆≤20%、拆建比≤2 等硬约束）
    mb = getattr(mod, 'METRICS_BASELINE', [])
    if mb:
        lines.append('底线指标：')
        for m in mb:
            lines.append(f'  - {m}')
    lines.append(f'项目类型（指向具体项目）：{" / ".join(mod.PROJECT_TYPES)}')
    # 要素归因细化（③ 厚化：设施/环境/服务/文化/事件在该域具体指什么，回答层归因落点）
    eh = getattr(mod, 'ELEMENT_HINTS', {})
    if eh:
        lines.append('要素归因细化：')
        for e, h in eh.items():
            lines.append(f'  - {e}：{h}')
    # 他城案例（佐证，回答可引）
    cs = getattr(mod, 'CASES', [])
    if cs:
        lines.append('他城案例：')
        for c in cs:
            lines.append(f"  - {c.get('city', '?')}·{c.get('project', '?')}：{c.get('point', '')}")
    lines.append(f'情绪归因焦点：{mod.EMOTION_FOCUS}')
    mp = get_matrix_mapping(domain_key)
    lines.append('4×5 矩阵多归属映射：' + ' / '.join(f"{e}({r})@{dom.split('_')[-1]}" for dom, e, r in mp))
    return '\n'.join(lines)


def industry_kb_lens_appendix(domain_lens):
    """按 diagnose 的 domain_lens 渲染命中领域完整权威语境附录（post-diagnose step 注入用）。

    过滤 'general'/falsy/非法 domain，去重保序；对每个有效域调 industry_kb_text 全量渲染，
    空行分隔。空（无命中域）返回 ''（调用方据此跳过拼接）。
    diagnose 不注此（它产 lens + 已有 brief 全 4 域速查，保 Flash eval 95%）；
    answer/revise/agent_step/review 注此——回答用权威话语 + 归因落到具体项目（政策→情绪→项目闭环）。
    """
    if not domain_lens:
        return ''
    seen = []
    for dk in domain_lens:
        if dk and dk in INDUSTRY_DOMAINS and dk not in seen:
            seen.append(dk)
    if not seen:
        return ''
    body = '\n\n'.join(industry_kb_text(dk) for dk in seen)
    return ('\n\n═══════════ 附录 · 聚焦领域权威语境（按 diagnose domain_lens 注入·政策→情绪→项目）═══════════\n'
            + body)


def industry_kb_brief_text():
    """四领域官方术语 + 项目类型速查（精简，注入 diagnose prompt 让 Flash 用官方话语 + 指向具体项目）。
    增量（vs DOMAIN_OUTLETS framework）：KEY_TERMS 精确术语表 + PROJECT_TYPES 项目落点（呼应"政策→情绪→项目"闭环）。
    完整权威语境见 industry_kb_text(domain_key)；本 brief 是全四领域精简速查。"""
    lines = ['四领域官方术语与项目类型速查（回答用权威术语；归因指向具体项目类型，呼应"政策→情绪→项目"）：']
    for dk, mod in INDUSTRY_DOMAINS.items():
        terms = '、'.join(list(mod.KEY_TERMS.keys())[:4])
        proj = '、'.join(mod.PROJECT_TYPES[:4])
        lines.append(f"- {mod.NAME}：术语[{terms}]；项目类型[{proj}]")
    return '\n'.join(lines)


def all_matrix_mappings():
    """全领域矩阵映射汇总 → list of (domain_key, element, role, source_domain)。
    供"某矩阵格被哪些领域知识覆盖"的反查（数据模拟逆推/归因展示用）。"""
    out = []
    for dk, mod in INDUSTRY_DOMAINS.items():
        for dom, elem, role in getattr(mod, 'MATRIX_MAPPING', []):
            out.append((dom, elem, role, dk))
    return out


__all__ = [
    'INDUSTRY_DOMAINS', 'DOMAIN_KEYS', 'ELEMENTS', 'ROLES',
    'get_matrix_mapping', 'industry_kb_text', 'industry_kb_brief_text', 'industry_kb_lens_appendix',
    'all_matrix_mappings',
    'urban_planning', 'urban_renewal', 'urban_operation', 'urban_governance',
]
