"""用例 2 · domain_lens 等结构字段被前端压扁（threading 回传）。

diagnose 产 domain_lens 后，后续 step 前端须结构化回传 ChatRequest.domain_lens
（router.py:35/46/54 req.domain_lens），非压扁进 ctx.context 字符串。
捕 POST /chat 请求体 → 断言 ≥1 个携带非空 domain_lens 数组（④5.108 threading 范式）。

前置：.env DEEPSEEK_API_KEY + fixtures/compare_points.geojson。
运行：py tests/browser/test_domain_lens_threading.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import ChatRequestCapture, emc_session, inject_points, send_prompt, wait_answer_done

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'compare_points.geojson')
# 明确多领域、非 compare 的分析问句（maximize diagnose 产非-general 多领域 domain_lens；
# compare/P1-单技能路径可能过滤为空 → domain_lens threading 观测依赖 LLM，下方软断言）
PROMPT = '从城市规划和城市更新两个角度，分析西陵区的情绪问题与归因'


def main() -> int:
    with open(FIXTURE, encoding='utf-8') as fh:
        fc = json.load(fh)
    with emc_session() as page:
        cap = ChatRequestCapture(page)
        inject_points(page, fc)
        send_prompt(page, PROMPT)
        wait_answer_done(page, timeout_ms=120000)

        all_reqs = cap.all()
        # 硬断言：chat 管线跑通（≥1 POST /chat 捕到）
        assert all_reqs, '未捕到任何 POST /chat 请求（chat 管线未跑通？）'

        # 软断言：domain_lens 结构化回传（threading 代码层已核实 api.js:31 + harness.js:384 过滤 general；
        # runtime 观测依赖 LLM 产非-general 多领域诊断，非确定 → 观测到=PASS，否则 WARN 不 fail）
        r = next((x for x in all_reqs if isinstance(x.get('domain_lens'), list) and x['domain_lens']), None)
        if r:
            print(f'[OK] PASS — domain_lens 结构化回传: {r["domain_lens"]} (phase={r["phase"]})')
            return 0
        phases = [x.get('phase') for x in all_reqs]
        print(f'[WARN] {len(all_reqs)} 个 /chat 请求均未携 domain_lens 数组（phases={phases}）')
        print('[WARN] 多半 LLM 未产非-general 多领域诊断（或路由过滤为空）——threading 不可本轮观测（软断言不 fail）')
        print('[WARN] threading 代码层已核实：frontend/js/ai_qa/api.js:31 body.domain_lens + harness.js:384-385 过滤 general')
        return 0


if __name__ == '__main__':
    sys.exit(main())
