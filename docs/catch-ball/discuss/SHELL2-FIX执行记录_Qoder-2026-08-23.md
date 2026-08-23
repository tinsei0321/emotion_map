# SHELL2(FIX) 深度审计修复批执行记录（Qoder · 2026-08-23）

> 依据：SHELL2-FIX派发单_zcode-2026-08-23（P1×3 阻断级 + P2×9 限期修）+ 壳工程深度审计收敛。
> commit 前缀 SHELL2(FIX): · 本地仓即最新·零 pull 零 push · 复审=claude。

## 白话摘要

上一轮体检（深度审计）给新装的「换脑系统」开了一张 12 项的整改单；这一批照单全修完了。打比方说：

**三件大事（P1）**：①给发电机房装了「双工位闸门」——以前谁都能同时开工，几台机器一起转会把整栋楼的电线烧掉；现在最多两台同时转，多的排队，而且把「长时间占工位」的活挪到了专用工棚，不再霸占全楼共享的工位。②给投递窗口装了「重量秤」——超过 4000 字的问题直接礼貌拒收（以前会吓出服务器 500 错误），就算漏网的超长件在路上卡住也会被接住、给一句人话而不是崩溃。③把一条早就走不通的备用小路彻底封死了——以前它平时没人走、真走上去还会把服务器吓一跳，现在直接立牌「此路不通，请走正门」。

**九件小事（P2）**：前端装了「330 秒总保险丝」（后端哑死时主动放弃并道歉，不再无限转圈）；回答最长限 200 公斤（200KB）防仓库爆仓；大货物称重改成先看个头再上秤（快 100 倍的廉价判长）；启动脚本写明了「换脑功能依赖 8600 号仓库在营业」；给主路信号补了三道质检关（过官方格式检验器）；追问建议的挑选逻辑抽成了独立零件并配了 13 项单测；道歉卡前面加了一行「原因：×××（自动诊断）」的白名单提示（不泄露原始错误）；dsh 引擎回答完后的追问改成了知识类口吻（不再串台成情绪分析问法）；契约里「必须带口径摘要」改成「有则带」（没有口径源时不硬造）。

**验收数字**：全仓测试 557→**574 绿**（新增 17 项·DoD 570+ 达标）；RAG 召回 **96.7% 零退化**；node 单测 65 项全过；浏览器四路复验全绿——轻量引擎回归（light 默认路径）/ S7 冒烟（含追问 chips 链路·被 FIX-09 重构后复验）/ dsh 引擎端到端 / 追问三态（含真 dsh 轮兜底追问实证）。轻量引擎默认路径零改动实证：无参 URL 走的路径与修复前逐字同路。

## 一 逐件修法与落点

| # | 级 | 修法落点 |
|---|---|---|
| FIX-01 | P1 | `api/aiqa_routes.py`：`post_dsh_engine` 改 `async def` + `asyncio.to_thread`（同步执行体 `_run_dsh_sync` 进专用线程·不占 uvicorn 共享池）+ 模块级 `_dsh_semaphore = asyncio.Semaphore(2)` 排队（不快速失败）；配套 `core/tracker.py` **加法新增** `track_async()`（既有 `track()` 零改动·同步面不受影响——端点转 async 后同步装饰器会吞协程·此为必要基建） |
| FIX-02 | P1 | `DshEngineIn.question` 加 `Field(max_length=4000)`（pydantic 422 语义拒绝）+ `_run_dsh_sync` 补 `except OSError`→`{ok:False, error:'问句过长或系统限制：…'}` |
| FIX-03 | P1 | 删 fallback 字符串 cmdline 分支——bin.js 缺失直接 `{ok:False, error:'dsh 安装布局未识别'}`（fail-closed）；主路径（node 直调 argv·shell=False）保留 |
| FIX-04 | P2 | `brain-adapter-dsh.js`：fetch 外 `Promise.race` 看门狗（330s > 代理 300s > 后端 240s）·超时→降级卡；成功/失败均 `clearTimeout`（防定时器泄漏）；`deps.timeoutMs` 测试注入口 |
| FIX-05 | P2 | `_run_dsh_sync`：stdout 截 `_DSH_MAX_OUTPUT=200KB` + `truncated` 标记 |
| FIX-06 | P2 | `acp-channel.js _summary`：string 直 slice / Array→`[N 行结果]` / object→键名列表（≤6）——万行观察值不再全量 stringify |
| FIX-07 | P2 | `start.bat` 顶部 REM 注记：?engine=dsh 依赖 8600 MCP（emc-test profile 走 http://127.0.0.1:8600/mcp）·本启动器先起 8600 再起 web·含探活命令 |
| FIX-08 | P2 | `tests/acp_schema/s4_wire_dump.mjs`（fake hooks 驱动 `createEngineEmitter` 全 14 方法·16 调用含两轮配对）+ `test_s4_wire.py` 三断言：四族 wire 过真实 jsonschema / 过程族信封恒 real / 分层+六族齐+toolcall 配对+seq 单调 |
| FIX-09 | P2 | 追问逻辑抽纯模块 `frontend/js/ai_qa/followup.js`（`normalizeFollowupCues`+`pickFollowupSource`·语义与原内联逐字一致）；`tests/browser/followup_chips_dump.mjs`（13 断言）+ `test_followup_chips.py`（node 逻辑 + mock 引擎实证：追问建议条/优先级/回填不直发） |
| FIX-10 | P2 | ①`acp-channel.js` error wire 补 `hint`（schema 可选位·截 200）；②panel ERROR 订阅器：白名单原因行（`DEGRADED_PARSE`/`DSH_ENGINE_FAIL` 映射固定文案·未知码归通用行）+ 原始 hint 只存 `_curTrace.degradeHint/degradeReason`（不显 UI·红线不破） |
| FIX-11 | P2 | panel `_followUps` 增 `intent==='dsh'` 分支（深问/求据/本地分析三问·不与情绪分析问法混调）——E2E Part C 真 dsh 轮实证 |
| FIX-12 | P2 | `docs/acp-contract-v1.md` §5-2：caliber「必带」→「有则带」（发射侧无口径源不硬造·带则统一结构）；`tool_end.schema.json` caliber 本就可选项·无需改 |

## 二 验证数字（DoD 逐项）

| 验 | 结果 |
|---|---|
| 全量 pytest | **574 passed / 2 skipped**（基线 557+2→+17 新增·DoD 570+ 达标·171s） |
| 新增测试明细 | test_dsh_engine.py 14 测（解析三分支/fail-closed/空问句/超长 422/OSError/夹取×3/超时语义/截断×2/信号量并发峰值 ≤2）+ test_s4_wire.py 3 测 |
| rag_eval 96.7% | **Recall@5 = 96.7% 零退化**（caliber 93.8 / checkup 93.8 / narrative 100 / noun 100·越维×2+注入×2 通过） |
| node 单测 | acp_channel.test.mjs 65 断言 ALL PASS（FIX-06 后 _summary 断言兼容·`{rows}` 摘要仍含 'rows'）+ followup_chips_dump 13 断言 |
| 浏览器回归四路 | S3 E2E 三场景 PASS（light 默认路径零退化·含 C3）/ S7 冒烟 PASS（S5 chips 链路被 FIX-09 重构后复验）/ SHELL2 BA E2E PASS（?engine=dsh 真问题）/ FOLLOWUP_CHIPS PASS（node+mock 实证+真 dsh 兜底追问） |
| 红线 | MCP 零改动（tools/ 未触）·轻量引擎默认路径（无参 URL）与修复前逐字同路·契约文档改动仅 §5-2 两处措辞 |

## 三 边界与注记

- **track_async 基建**：core/tracker.py 属追踪基础设施——本批为 FIX-01 必要配套·**纯加法**（新函数·既有同步面零改动）；注册表无新 ID（F_041 已注册）。
- **信号量跨 loop**：模块级 Semaphore 惰性绑当前 loop——uvicorn 单 loop 安全；测试中多次 `asyncio.run` 复用同闸已实证无绑定异常。
- **dsh 并发耐受**：Semaphore(2) 为防御性上限（审计盲区 1 未实测 dsh 自身并发）——实测观察后可收紧为 1。
- **前端 330s vs 代理 300s**：代理先断时前端收到 502→降级卡（语义化）；330s 只兜代理哑死极端态。
- **截图**：`tests/browser/out/fix09_mock_cues.png` / `fix11_dsh_static.png`（gitignore 内·归档证据在位）。
- **遗留**：审计 P3 十件未动（按派发单口径记账·随相关批次顺手治理）；test_followup_chips Part C 依赖外网+本机 dsh——无外网机器跑 Part A/B 即可（脚本自带栈探活降级）。

## 四 流转

Qoder 交付完毕 → **claude 复审**（对照派发单 12 件 + 两组原审计逐项核验）→ zcode 收敛终裁。

> Qoder · 2026-08-23 · SHELL2(FIX) 12 件全修·574 绿·96.7% 零退化·待复审
