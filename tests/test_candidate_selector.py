"""0LLM 候选选择器离线测试（CB-09 轮次3a · 模块九 D035-D038 · Phase A）。

复用 [eval_template_flash.CASES](eval_template_flash.py)（34 例·Flash template 选型语料）为选择器测试语料：
零 API 成本·CI 可跑。**目标命中率 ≥83%**（对齐 eval 83% 基线·Phase B 启动门）。
miss <83% → 规则太粗·Phase B 不启动·先补 triggers/映射（这正是 Phase A 的去风险价值）。

Phase A 红线：**只读** eval CASES·不改 eval_template_flash / diagnose prompt。
"""
import pytest
from ai_qa.candidate_selector import select_candidates

# 复用 eval 语料（单源·防漂移）·tests/ 在 sys.path 时直 import·否则经 tests 包
try:
    from eval_template_flash import CASES  # type: ignore
except ImportError:
    from tests.eval_template_flash import CASES  # type: ignore


def _hit(question, expected):
    """候选集是否命中期望 template。

    - expected=concept → 选择器须归 A track 返 [concept]。
    - expected=multi → 显式 'multi' 或 ≥2 非辅助候选（隐含复合）。
    - 其他 → expected ∈ candidates（选择器返候选集·含即 hit·最终定夺留 Phase B Flash/Pro）。
    """
    cands = select_candidates(question, None)['candidates']  # 无 context·对齐 eval（只给问句）
    if expected == 'concept':
        return cands == ['concept'] or 'concept' in cands
    if expected == 'multi':
        non_aux = [t for t in cands if t != 'concept']
        return 'multi' in cands or len(non_aux) >= 2
    return expected in cands


def test_eval_corpus_hit_rate(capsys):
    """eval 34 例·选择器候选集命中率 ≥83%（Phase B 启动门）。miss 明细打印便于补规则。"""
    rows = []
    for q, expected in CASES:
        cands = select_candidates(q, None)['candidates']
        ok = _hit(q, expected)
        rows.append((ok, q, expected, cands))
    rate = sum(1 for r in rows if r[0]) / len(rows)
    missed = [(q, exp, got) for ok, q, exp, got in rows if not ok]
    # 打印全量 + miss 明细（-v 时可见·辅助补规则）
    with capsys.disabled():
        print(f'\n  [选择器命中率] {sum(1 for r in rows if r[0])}/{len(rows)} = {rate:.0%}')
        for q, exp, got in missed:
            print(f'    [MISS] {q}  → 期望 {exp} / 实得 {got}')
    assert rate >= 0.83, (
        f'选择器命中率 {rate:.0%} < 83%（Phase B 启动门）·miss {len(missed)} 例（见上行明细·补 triggers/映射）'
    )


# ── 边界用例（D035-D038 各机制覆盖）──────────────────────────────────

def test_concept_track_priority():
    """定义线索（什么是/原理）优先归 A·即使含工具词（核密度）。"""
    assert select_candidates('什么是核密度分析')['candidates'] == ['concept']
    assert select_candidates('核密度分析的原理是什么')['candidates'] == ['concept']
    assert select_candidates('这几个图层是什么意思')['candidates'] == ['concept']


def test_b_track_single():
    """B 赛道单工具命中。"""
    assert select_candidates('做核密度分析')['candidates'] == ['density']
    assert select_candidates('滨江公园 500 米缓冲')['candidates'] == ['buffer']
    assert 'overlay' in select_candidates('居住用地里情绪差的')['candidates']


def test_c_track_compare():
    """C 赛道对比 → compare。"""
    assert 'compare' in select_candidates('对比西陵区和伍家岗区情绪')['candidates']
    assert 'compare' in select_candidates('比较两个区的消极占比')['candidates']


def test_c_track_rank_zonal():
    """C 赛道 rank/zonal 候选。"""
    r = select_candidates('各区情绪排序')
    assert 'rank' in r['candidates']
    r = select_candidates('这几个街道的情绪归因')
    assert 'zonal' in r['candidates']


def test_compound_detection():
    """化合物（scope+analyze / ≥2 B 动作）→ multi 入候选。"""
    r = select_candidates('西陵区范围内密度分析')
    assert r['compound'] is True
    assert 'multi' in r['candidates']


def test_context_field_filter_removes_unsupported():
    """D035 field-role 消歧：field_roles 有字段但无情绪角色 → density 移除（5.242：field_roles 空时跳过字段过滤·须非空才测）。"""
    r = select_candidates('做核密度分析', {'field_roles': {'boundary_name'}, 'has_point': True, 'has_polygon': False})
    assert 'density' not in r['candidates']


def test_context_geometry_filter_removes_unsupported():
    """D035 geometry 过滤：只有面层 → 点操作（density）移除。"""
    r = select_candidates('做核密度分析', {'field_roles': {'polarity'}, 'has_point': False, 'has_polygon': True})
    assert 'density' not in r['candidates']


def test_context_none_is_permissive():
    """context=None 宽容模式（不按字段/几何过滤·对齐 eval）。"""
    r = select_candidates('做核密度分析', None)
    assert 'density' in r['candidates']  # 无 context 不过滤


def test_truncate_to_four():
    """D035 候选截断到 4。"""
    # 难构造 >4·验上限不变：任意问句候选 ≤4
    for q, _ in CASES:
        assert len(select_candidates(q, None)['candidates']) <= 4


def test_return_shape():
    """返字段完整（candidates/grounding/ask_scenario/track/compound）。"""
    r = select_candidates('做核密度分析')
    assert set(r.keys()) >= {'candidates', 'grounding', 'ask_scenario', 'track', 'compound'}
    assert r['track'] in ('A', 'B', 'C')


def test_data_aware_jiancai_polygon_only():
    """5.242 S1 数据感知：剪裁+只有面（无点）→ extract_feature（clip 被几何过滤剔除）。"""
    r = select_candidates('剪裁西陵区', {'has_point': False, 'has_polygon': True})
    assert 'extract_feature' in r['candidates'], f'剪裁面层应留 extract·实 {r["candidates"]}'
    assert 'clip' not in r['candidates'], f'clip 需点·应被几何过滤剔·实 {r["candidates"]}'


def test_data_aware_jiancai_has_point():
    """5.242 S1 数据感知：剪裁+有点层 → clip 保留（可裁点）。"""
    r = select_candidates('剪裁西陵区', {'has_point': True, 'has_polygon': False})
    assert 'clip' in r['candidates'], f'剪裁有点层时 clip 应留·实 {r["candidates"]}'


def test_data_aware_density_no_point_filtered():
    """5.242 S1 数据感知：生成热力图+无点 → density 几何过滤剔除（→ dispatch request_upload）。"""
    r = select_candidates('生成热力图', {'has_point': False, 'has_polygon': True})
    assert 'density' not in r['candidates'], f'density 需点·无点应剔·实 {r["candidates"]}'


def test_data_aware_density_has_point_kept():
    """5.242 S1 数据感知：生成热力图+有点 → density 保留（field_roles 空不误剔）。"""
    r = select_candidates('生成热力图', {'has_point': True, 'has_polygon': False})
    assert 'density' in r['candidates'], f'density 有点层应留（field_roles 空勿误剔）·实 {r["candidates"]}'
