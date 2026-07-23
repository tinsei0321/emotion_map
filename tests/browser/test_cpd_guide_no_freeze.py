"""用例 11（G1 配套）· H1 引擎不冻结（CB-CPD-03 H1 回归）。

H1 根因（v0.4）：finally 守卫 `exit!==undefined` × 严格 turnId+1 去重 × general 无 exit =
general 轮 settled=true 照常 push 致 _history 跳号但不 dispatch → 引擎丢事件 → 永久冻结（静默失败）。
v1.0 修：守卫改 `settled`（覆盖 general exit=null）+ 单调去重 `turnId > lastProcessed`（免疫跳号）。

本测确定性验证引擎侧契约（免 LLM，与用例 5 同级稳定）：
  dispatch cpd:turn-ended 序列（result → general exit=null → 跳号 result → 低 turnId），
  断言引擎对 general/跳号仍响应（不冻结）、对低 turnId 去重（不重复）。
panel.js finally `settled` dispatch 侧由代码审查 + 用例 6（exit-badge 走 answer 路径）覆盖。

组合场景（GUIDANCE §4.4）：事件×状态×去重咬合——H1 静默冻结教训制度化。

运行：py tests/browser/test_cpd_guide_no_freeze.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session


def _dispatch(page, detail):
    page.evaluate(
        "(d) => document.dispatchEvent(new CustomEvent('cpd:turn-ended', { detail: d }))",
        detail)


def _count(page):
    return page.evaluate("() => window.__gCount")


def _wait_gt(page, threshold, timeout_ms=3000):
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if _count(page) > threshold:
            return True
        page.wait_for_timeout(100)
    return False


def main() -> int:
    with emc_session() as page:
        page.wait_for_function("() => !!window.__cpdPredicates", timeout=30000)
        # 计数 cpd:guidance 派发 = 引擎响应证据（_compute 每次派发一次）
        page.evaluate("window.__gCount = 0; document.addEventListener('cpd:guidance', () => { window.__gCount++; });")
        page.wait_for_timeout(500)   # 等 initCpdGuide 首 _compute 稳定
        base = _count(page)

        # 1. result 轮（turnId=1）：引擎响应
        _dispatch(page, {'exit': 'result', 'turnId': 1, 'intent': 'emotion_analysis'})
        assert _wait_gt(page, base), 'turnId=1 未响应——引擎冻结'
        last = _count(page)

        # 2. general 短路轮（exit=null·turnId=2）：H1 核心——settled 守卫下 general 也响应（不冻结）
        _dispatch(page, {'exit': None, 'turnId': 2, 'intent': 'general'})
        assert _wait_gt(page, last), 'general 轮（exit=null）后引擎未响应——H1 冻结回归'
        last = _count(page)

        # 3. 跳号 result 轮（turnId=4，跳过 3）：单调去重 4 > 2 仍处理（免疫 general 跳号）
        _dispatch(page, {'exit': 'result', 'turnId': 4, 'intent': 'emotion_analysis'})
        assert _wait_gt(page, last), '跳号 turnId=4 未响应——单调去重失效（H1 未修）'
        last = _count(page)

        # 4. 低 turnId（turnId=2 ≤ lastProcessed=4）：单调去重忽略，不重复处理
        _dispatch(page, {'exit': 'result', 'turnId': 2, 'intent': 'emotion_analysis'})
        page.wait_for_timeout(400)
        after = _count(page)
        assert after == last, f'低 turnId 应被去重忽略，却重复处理了（{last} → {after}）'

        print(f'[OK] PASS — H1 不冻结：result→general(exit=null)→跳号 result 均响应（gCount {base}→{last}）+ 低 turnId 去重')
        return 0


if __name__ == '__main__':
    sys.exit(main())
