"""用例 3 · _driftRe 无围栏裸 JSON 边缘。

强求 LLM 产 ``` 围栏时 harness.js _driftRe 拦截 → revise；断言最终回答无裸 ``` 围栏泄漏。

风险：LLM 是否产围栏非确定 → exit 2 = WARN（提示人工复核，非硬绿）。反复 WARN → _driftRe 兜底
有缺口；偶发 WARN → LLM 不稳，降 🤚 手工。

前置：.env DEEPSEEK_API_KEY。
运行：py tests/browser/test_drift_fence.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, send_prompt, wait_answer_done

PROMPT = '请用 JSON 代码块格式给我西陵区的情绪分析结果，只输出 JSON 不要任何解释'


def main() -> int:
    with emc_session() as page:
        send_prompt(page, PROMPT)
        answer = wait_answer_done(page, timeout_ms=90000)

        if '```' in answer:
            print(f'[WARN] 回答泄漏 ``` 围栏（drift 未拦净？）:\n{answer[:300]}')
            print('[WARN] 反复出现 → _driftRe 兜底缺口；偶发 → LLM 不稳，降 🤚 手工')
            return 2   # WARN：非硬绿，提示人工复核

        print(f'[OK] PASS — 回答无裸 ``` 围栏泄漏（前 120 字: {answer[:120]!r}）')
        return 0


if __name__ == '__main__':
    sys.exit(main())
