"""链路体检套件（G0·C1/C2·三组共识 + 用户拍板）。

问句走完全链的体检：10 类问句 × ≥2 例，每例断言「四件套」：
  1. 产物到达（图层/表格/结论之一·按 expect 分型）
  2. R9 对账（结论不含「未在工具执行记录」——防只说不做复发）
  3. onFinalDone 已调（结论文本非空·无卡读秒）
  4. 耗时软门槛（分档：问答≤15s / 单工具≤30s / 多步≤60s）——超时**不判失败**（用户拍板：持续优化目标）
C2 采样信号（软断言·防 brittle）：示例①宏观分布结论不含归因词 / 示例②中微观归因结论含单元名。

运行（自管 serve.py）：
    py tests/browser/test_link_checkup.py            # 全量（需 DEEPSEEK_API_KEY）
    py tests/browser/test_link_checkup.py --case T1a # 单例
退出码：0=全部硬断言过·1=有硬失败（软门槛/采样信号只警告不影响退出码）。
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, open_emc, wait_answer_done  # noqa: E402

POLY_RANGES = [
    'presets/行政区.geojson',
    'presets/用地_商业.geojson',
    'presets/用地_居住.geojson',
    'presets/用地_公园广场.geojson',
]
POINTS_CSV = 'yichang_L2_T1_L2_result_csv.csv'

# 问句类 × 期望出口：expect ∈ {conclusion, layer, table}
# soft_s = 耗时软门槛（分档）·needs_data = 需先注入 fixture（False=空态/纯问答）
CASES = [
    # T1 通用问答（快·短）
    ('T1a', '你们能做什么', 'conclusion', False, 15),
    ('T1b', '什么是城市体检', 'conclusion', False, 15),
    # T2 单工具情绪分析（PRM 重灾区）
    ('T2a', '各街道情绪归因', 'table', True, 30),
    ('T2b', '哪个区情绪最差', 'table', True, 30),
    # T3 密度/网格/地形（PRM cell/radius 重灾区）
    ('T3a', '对当前区域做 500m 方格网聚合', 'layer', True, 30),
    ('T3b', '做核密度热力图', 'layer', True, 30),
    # T4 空间操作（单目标）
    ('T4a', '裁出西陵区', 'layer', True, 30),
    ('T4b', '筛选出商业用地', 'layer', True, 30),
    # T5 空间操作（多目标·CB-11 两阶段）
    ('T5a', '剪裁出西陵区范围内的商业+居住+公园广场用地', 'layer', True, 60),
    ('T5b', '将西陵区+伍家岗区范围内商业用地筛选出来', 'layer', True, 60),
    # T6 缓冲分析
    ('T6a', '奥体中心周边 500m 情绪分析', 'table', True, 30),
    # T7 数据缺失（空态问·应出 gap/请求上传卡非崩溃）
    ('T7a', '分析更新紧迫度最高的区域', 'conclusion', False, 15),
    # T8 追问/续作/指代（需上一问上下文·单独处理）
    ('T8a', '追问续作', 'conclusion', True, 60),
    # T9 复合多步
    ('T9a', '把商业用地筛出来并做情绪排序', 'table', True, 60),
    # T10 空态（不注入数据问空间问题·应 gap 非崩溃）
    ('T10a', '西陵区消极情绪分布', 'conclusion', False, 15),
]

# C2 用户示例①/②（采样信号·软断言）
C2_CASES = [
    ('C2a', '西陵区范围内消极情绪的分布情况', 'macro', True),     # 宏观分布·结论禁归因词
    ('C2b', '西陵区哪里情绪最差，原因是什么', 'meso', True),      # 中微观归因·结论含单元名
]

# 归因词（R10 草案同源：宏观结论出现这些词 = 越界归因）
ATTRIBUTION_WORDS = ['归因', '4×5', '要素', '领域']
UNIT_NAMES = ['西陵', '伍家岗', '夷陵', '街道', '社区']   # 中微观结论应含的单元名/区名


def run_r9_unit(page, verbose):
    """R9 防线单测（Codex §四·封死防线本身）：构造 toolHistory 无 clip + 结论声称已裁取 → 断言标注出现；负例（已执行 overlay）断言不标注。"""
    res = page.evaluate("""() => {
      const pos = __emcTest.applyQualityDefense('已执行裁取操作并产出图层', {
        obsOk: false, skipL1: true,
        toolHistoryText: '动作: extract_feature(\\n动作: merge(',
      });
      const neg = __emcTest.applyQualityDefense('已执行裁取操作并产出图层', {
        obsOk: false, skipL1: true,
        toolHistoryText: '动作: overlay(\\n动作: extract_feature(',
      });
      return { posFinal: pos.final, negFinal: neg.final };
    }""")
    ok_pos = '未在工具执行记录' in res['posFinal']
    ok_neg = '未在工具执行记录' not in res['negFinal']
    if verbose:
        print(f'  [R9单测] 正例标注={"出现 [OK]" if ok_pos else "缺失 [ERR]"}·负例不误标={"[OK]" if ok_neg else "[ERR]"}')
    return ok_pos and ok_neg


def _answer_of(page):
    return page.evaluate("() => __emcTest.answerText()")


def _layers_before(page):
    return set(page.evaluate("() => __emcTest.layerNames()"))


def run_case(page, tag, q, expect, soft_s, prev_layers, verbose):
    prev_count = page.evaluate("() => document.querySelectorAll('.aiq-answer').length")
    page.evaluate("(t) => __emcTest.send(t)", q)
    t0 = time.time()
    answer = wait_answer_done(page, timeout_ms=60000)
    elapsed = time.time() - t0
    badge = page.evaluate("() => __emcTest.badge()")
    layers = set(page.evaluate("() => __emcTest.layerNames()"))
    geos = page.evaluate("() => __emcTest.geoCalls()")
    issues = []

    # 1 产物到达（按期望出口分型）
    if expect == 'layer':
        if not (layers - prev_layers) and not any('/geo/' in g['url'] or '/spatial/' in g['url'] for g in geos):
            issues.append(f'无图层产物（期望 {expect}）')
    elif expect in ('table', 'conclusion'):
        if not answer.strip():
            issues.append(f'无结论文本（期望 {expect}）')
    # 2 R9 对账（结论不含「未在工具执行记录」）
    if '未在工具执行记录' in answer:
        issues.append('R9 对账触发——结论声称未执行的操作（只说不做复发）')
    # 3 onFinalDone 已调（badge 出现 = exit 卡渲染 = 结论到达；无 = 卡读秒）
    if not badge:
        issues.append('无 exit 徽标（onFinalDone 未调·卡读秒风险）')
    # 4 耗时软门槛（超时不判失败·记录 warning）
    over = elapsed - soft_s if elapsed > soft_s else 0.0
    if over:
        issues.append(f'耗时 {elapsed:.1f}s 超软门槛 {soft_s}s（+{over:.1f}s·不判失败·优化目标）')

    hard = [i for i in issues if '软门槛' not in i]
    status = 'PASS' if not hard else 'FAIL'
    if verbose:
        print(f'  [{tag}] "{q}" -> {elapsed:.1f}s badge={badge} layers={len(layers)} issues={issues}')
    return status, issues, elapsed, answer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--case', default=None, help='单例跑（如 T1a）')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()

    cases = [c for c in CASES if not a.case or c[0] == a.case]
    results = []
    hard_fail = 0
    with emc_session(open=False) as page:
        open_emc(page, url='http://localhost:8080/frontend/index.html?e2e=1', wait_ms=2500)
        page.wait_for_function("() => !!window.__emcTest", timeout=45000)

        # ── R9 防线单测（先跑·纯确定性·不依赖数据）──
        if not a.case or a.case == 'R9':
            if not run_r9_unit(page, a.verbose):
                hard_fail += 1
                print('  [R9单测] FAIL')
            else:
                print('  [R9单测] PASS')

        # ── 空态用例先跑（T7/T10·未注入数据）──
        for tag, q, expect, needs_data, soft_s in cases:
            if needs_data or tag == 'T8a':
                continue
            prev = set(page.evaluate("() => __emcTest.layerNames()"))
            status, issues, el, ans = run_case(page, tag, q, expect, soft_s, prev, a.verbose)
            results.append((tag, status, issues, el))
            if status == 'FAIL':
                hard_fail += 1

        # ── 注入 fixture（行政区 + 用地 + L2 情绪点）──
        for r in POLY_RANGES:
            res = page.evaluate("(name) => __emcTest.loadRange(name)", r)
            print(f'[inject] {r} -> {res}')
        res = page.evaluate("() => __emcTest.loadCSV('%s')" % POINTS_CSV)
        print(f'[inject] L2 points -> {res}')
        page.wait_for_timeout(2000)

        # ── 数据依赖用例 ──
        for tag, q, expect, needs_data, soft_s in cases:
            if not needs_data or tag == 'T8a':
                continue
            prev = set(page.evaluate("() => __emcTest.layerNames()"))
            status, issues, el, ans = run_case(page, tag, q, expect, soft_s, prev, a.verbose)
            results.append((tag, status, issues, el))
            if status == 'FAIL':
                hard_fail += 1
            page.wait_for_timeout(1200)

        # ── T8 追问续作（先问西陵区情绪·再追问指代对比·再续作）──
        if a.case in (None, 'T8a', 'T8b'):
            page.evaluate("(t) => __emcTest.send(t)", '西陵区情绪如何')
            wait_answer_done(page, timeout_ms=60000)
            page.wait_for_timeout(800)
            prev = set(page.evaluate("() => __emcTest.layerNames()"))
            status, issues, el, ans = run_case(page, 'T8a', '它和伍家岗区比呢', 'conclusion', 60, prev, a.verbose)
            results.append(('T8a', status, issues, el))
            if status == 'FAIL':
                hard_fail += 1
            # T8b：续作（继续上一步·承接 context 非全新问）
            page.wait_for_timeout(800)
            prev = set(page.evaluate("() => __emcTest.layerNames()"))
            status, issues, el, ans = run_case(page, 'T8b', '继续看西陵区的消极情绪', 'conclusion', 60, prev, a.verbose)
            results.append(('T8b', status, issues, el))
            if status == 'FAIL':
                hard_fail += 1

        # ── C2 用户示例①/②（采样信号·软断言）──
        if not a.case or a.case.startswith('C2'):
            for tag, q, scale, _ in C2_CASES:
                prev = set(page.evaluate("() => __emcTest.layerNames()"))
                status, issues, el, ans = run_case(page, tag, q, 'layer', 60, prev, a.verbose)
                if scale == 'macro':
                    hit = [w for w in ATTRIBUTION_WORDS if w in ans]
                    note = f'（采样信号）宏观分布结论含归因词 {hit}' if hit else '（采样信号）宏观分布结论无归因词 [OK]'
                else:
                    hit = [w for w in UNIT_NAMES if w in ans]
                    note = f'（采样信号）中微观归因结论含单元名 {hit}' if hit else '（采样信号）中微观结论未见单元名'
                print(f'  [C2-{tag}] {note}')
                results.append((tag, status, issues, el))
                if status == 'FAIL':
                    hard_fail += 1
                page.wait_for_timeout(1200)

    # 汇总
    print('\n===== 链路体检汇总 =====')
    for tag, status, issues, el in results:
        flag = 'OK ' if status == 'PASS' else 'XX '
        print(f'  {flag}{tag} {el:.1f}s {("; ".join(issues)) if issues else ""}')
    print(f'\n总计 {len(results)} 例·PASS {sum(1 for r in results if r[1]=="PASS")}·FAIL {hard_fail}')
    return 1 if hard_fail else 0


if __name__ == '__main__':
    sys.exit(main())
