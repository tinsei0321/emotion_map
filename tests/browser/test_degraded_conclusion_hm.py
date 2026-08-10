"""CB-22e P2/P3 桩测：_composeDegradedConclusion 观察行优先规则（N/M 命中表述）。

经 e2e-seam 暴露的 window.__emcTest.composeDegraded 直测真实 JS 逻辑（非 Python 复刻）：
- 场景 1（部分命中·核心）：observation 含「命中 2/5」+ tip 行 → 取「命中 N/M」行（修 Codex 实锤断链）
- 场景 2（全命中）：含「命中 5/5」→ 取该行
- 场景 3（无命中行）：维持 slice(-1)（末匹配行）·零行为变化
- 场景 4（空 toolHistory）：fallback 通用文案

无需 LLM（纯调防线函数），与 test_gap_wording 同级稳定。

运行：py tests/browser/test_degraded_conclusion_hm.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session


def _concl(page, tool_history_text):
    return page.evaluate("""(txt) => {
      const c = window.__emcTest.composeDegraded;
      return c(txt);
    }""", tool_history_text)


def main() -> int:
    with emc_session() as page:
        page.wait_for_function("() => !!(window.__emcTest && window.__emcTest.composeDegraded)", timeout=45000)

        # ── 场景 1：部分命中 2/5（核心·Codex 实锤断链修复）──
        th = (
            '第1轮·动作: generate_point_layer({"names":["A","B","C","D","E"]}) → '
            '地点标记：命中 2/5 → 已生成图层「项目点位」(2 点)（来源：amap2）\n'
            '未匹配到坐标（诚实列出·不编造）：C、D、E\n'
            '已命中项目 → 点位图层（橙色点·可点击查看名称/来源）。未命中项目 → 已文字列出'
        )
        r1 = _concl(page, th)
        assert '2/5' in r1, f'部分命中降级结论应含「2/5」（Codex 断链修复·{r1}）'
        assert '命中' in r1, f'应含「命中」（{r1}）'
        print(f'  [OK] 场景1 部分命中 2/5 → {r1[:60]}...')

        # ── 场景 2：全命中 5/5 ──
        th2 = (
            '第1轮·动作: generate_point_layer({"names":["A","B","C","D","E"]}) → '
            '地点标记：命中 5/5 → 已生成图层「项目点位」(5 点)（来源：local5）\n'
            '已命中项目 → 点位图层'
        )
        r2 = _concl(page, th2)
        assert '5/5' in r2, f'全命中降级结论应含「5/5」（{r2}）'
        print(f'  [OK] 场景2 全命中 5/5 → {r2[:60]}...')

        # ── 场景 3：无命中行（分析类·零行为变化·维持末匹配行）──
        th3 = '第1轮·动作: density({}) → 热力图已生成·共 120 点'
        r3 = _concl(page, th3)
        assert '热力图已生成' in r3, f'无命中行应维持 slice(-1)（{r3}）'
        print(f'  [OK] 场景3 无命中行维持末行 → {r3[:60]}...')

        # ── 场景 4：空 toolHistory → fallback ──
        r4 = _concl(page, '')
        assert '分析图已生成' in r4, f'空输入应 fallback 通用文案（{r4}）'
        print(f'  [OK] 场景4 空输入 fallback → {r4[:60]}...')

        print('[OK] _composeDegradedConclusion 选行规则四场景断言全过（N/M 表述修复）')
        return 0


if __name__ == '__main__':
    sys.exit(main())
