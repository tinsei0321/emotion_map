"""③w5 措辞断言（Codex/glm P2）：gap 卡措辞与问题性质匹配——零工具尝试不含「图层」字眼。

经 e2e-seam 暴露的 window.__emcTest.composeGapCard 直测真实 JS 逻辑（非 Python 复刻）：
- 场景 1：failedObs=0 + diagnose.degraded → 「我没能理解这个问题的分析需求」·无「图层」字眼
- 场景 2：failedObs=0 + 非 degraded → 「这个问题我暂时无法直接回答」·无「图层」字眼
- 场景 3：failedObs>0（试过工具）→ 「没能生成可用的图层」（保留·确实试了）

无需 LLM（纯调防线函数），与 test_r7_truncation 同级稳定。

运行：py tests/browser/test_gap_wording.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session


def _gap(page, diagnose, failedObs):
    return page.evaluate("""([d, f]) => {
      const cg = window.__emcTest.composeGapCard;
      return cg(d, f);
    }""", [diagnose, failedObs])


def main() -> int:
    with emc_session() as page:
        page.wait_for_function("() => !!(window.__emcTest && window.__emcTest.composeGapCard)", timeout=45000)

        # ── 场景 1：failedObs=0 + degraded（诊断失败→无法理解）→ 无「图层」字眼 ──
        r1 = _gap(page, {'degraded': True, 'data_plan': {}}, [])
        assert '图层' not in r1, f'场景1（degraded·零工具）不应含「图层」字眼（{r1}）'
        assert '没能理解' in r1, f'场景1 应含「没能理解」（{r1}）'

        # ── 场景 2：failedObs=0 + 非 degraded（诊断成功但执行未开始→暂无法回答）→ 无「图层」字眼 ──
        r2 = _gap(page, {'degraded': False, 'data_plan': {}}, [])
        assert '图层' not in r2, f'场景2（非 degraded·零工具）不应含「图层」字眼（{r2}）'
        assert '无法直接回答' in r2, f'场景2 应含「无法直接回答」（{r2}）'

        # ── 场景 3：failedObs>0（试过工具失败→图层叙事保留）→ 含「图层」──
        r3 = _gap(page, {'degraded': False, 'data_plan': {}}, ['zonal_stats: 执行失败'])
        assert '图层' in r3, f'场景3（试过工具）应含「图层」字眼（{r3}）'
        assert '没能生成' in r3, f'场景3 应含「没能生成」（{r3}）'

        print('[OK] 措辞三场景断言全过（零工具无图层·试过工具有图层）')
        return 0


if __name__ == '__main__':
    sys.exit(main())
