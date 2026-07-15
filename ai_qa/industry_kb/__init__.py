"""行业知识库 · 全项目行业知识基础设施（v1）。

四领域权威源（规划·设计 / 更新 / 运营 / 治理），每领域含：顶层政策 + 核心概念体系 + 官方术语 +
可量化底线 + 项目类型（中微观聚焦）+ 其他城市案例 + 情绪归因焦点 + 4×5 矩阵多归属映射。

**设计哲学**（项目顶层纲领，见 CLAUDE.md）：
- 4×5 是归因落点矩阵（非指标分类清单），跨领域×跨要素多归属；矩阵骨架稳定。
- 归因底层逻辑 = 政策→情绪→项目：政策指引方向 → 情绪地图定位实际痛点 → 指向具体项目。
- 差异化 = 补官方话语盲区（如事件的瞬时空间影响）。
- 可成长：政策更新→模块更新→矩阵映射丰富；做厚路径见 docs/industry-knowledge-base.md。

本包是**单一权威源**（仿 ai_qa/landuse_codes_2023.py 模式）；改各领域 = 改权威源。
EMC 按 domain_lens 命中时，可调 industry_kb_text(domain_key) 渲染该领域权威语境（v1 预留）。
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
    """渲染某领域权威语境为可读文本（供 diagnose prompt 按需注入 / 人读）。
    v1 不自动注 prompt（避免 prompt 过长、保 Flash eval 不回归）；future 按 domain_lens 注入。"""
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
    lines.append(f'项目类型（指向具体项目）：{" / ".join(mod.PROJECT_TYPES)}')
    lines.append(f'情绪归因焦点：{mod.EMOTION_FOCUS}')
    mp = get_matrix_mapping(domain_key)
    lines.append('4×5 矩阵多归属映射：' + ' / '.join(f"{e}({r})@{dom.split('_')[-1]}" for dom, e, r in mp))
    return '\n'.join(lines)


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
    'get_matrix_mapping', 'industry_kb_text', 'industry_kb_brief_text', 'all_matrix_mappings',
    'urban_planning', 'urban_renewal', 'urban_operation', 'urban_governance',
]
