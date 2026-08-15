---
name: browser-test-stability-gotchas
description: tests/browser Playwright 脚本三坑——进程树清理/attached 等待/exit 值软断言；写新 browser 用例前先 recall
metadata: 
  node_type: memory
  type: feedback
  originSessionId: de71ce91-41e0-4b33-ae62-ab9868fc457e
  modified: 2026-07-22T12:43:46.473Z
---

tests/browser/ Playwright 脚本（emc_session 自管 serve.py）有三个稳定性坑，写新用例前务必 recall，否则逐个踩：

1. **serve.terminate() 留 uvicorn 孤儿**——serve.py 自起 uvicorn :8000 子进程；只 terminate 父进程 → uvicorn 子进程成孤儿占 :8000 → 下一测试的 serve 绑不上 → goto ERR_CONNECTION_REFUSED（_wait_health 却命中残留返 200，矛盾假象）。**杀全树**：emc_session finally 用 Windows `taskkill /F /T /PID`（非 serve.terminate()）。
2. **wait_for_selector(visible) 偶发超时**——折叠态 / 慢 mount 下 `#lp-upload`（左栏 import 钮，抽屉关时 hidden）/ `#chat-input` 偶发 hidden → 默认 visible 等待超时。**改 `state='attached'`**：change 监听绑在 attach（非可见），attached 早于 visible 且严格不破既有用例。历史列表 `#emc-history-list` 同理（抽屉默认关，需先点 `#chat-history` 切历史视图才 populate）。
3. **exit-badge / domain_lens 值 LLM 非确定**——exit-badge 的 exit（result/gap/...）和 domain_lens（多领域诊断）都依赖 LLM 路由：compare 实测常落 gap 非 result；"什么是4×5矩阵"被当实质问题（4×5 是项目归因矩阵概念）非 general；domain_lens threading（api.js:31 + harness.js:384 过滤 'general'）非空要求 LLM 产非-general 多领域诊断。**硬断言挂结构（badge 渲染 / ≥1 /chat 捕到 / 无围栏），LLM 依赖部分软断言（WARN exit 2 不 fail）**。

**Why**：坑 1 致跨测试级联（最难定位），坑 2 致首跑即挂，坑 3 致假 fail（LLM 方差被误判回归）。
**How to apply**：新 browser 用例 = `with emc_session() as page:` + 硬断言 DOM/网络结构 + LLM 依赖项软断言兜底；G1 谓词测试（read_predicate）同理。关联 [[verify-real-endpoint]]（测真业务端点）+ [[no-routine-playwright-verify]]（常规改动不跑）。
