# 壳二期件① 执行记录：BrainAdapter · dsh headless 适配器（Qoder · 2026-08-23）

> **依据**：docs/catch-ball/discuss/壳二期派发_zcode-2026-08-23.md 件① + docs/brain-adapter.md v0.1 契约。
> **commit 前缀**：SHELL2(BA): · 本地仓即最新·零 pull 零 push。
> **前置**：壳一期 S1-S9 全完成（S3 事件化 / S4 引擎发射层在位——本批直接复用其 bus 与 wire 纪律）。

## 白话摘要

上次装修给家里装好了「标准插座」（事件广播系统）；这次干的事是：**第一次把别人家的真发电机（dsh，一个独立 AI 助手）接进来发电**——EMC 地图窗口里问问题，问题被转给 dsh 处理，dsh 的回答再回到地图窗口里显示。以前窗口只能用自己的内置引擎答题，现在**换脑**成了现实：网址后面加 `?engine=dsh` 就用 dsh，加 `?engine=mock` 用模拟引擎，什么都不加就用原来的轻量引擎（默认路径一个字没动）。

诚实是这个活的关键规矩：dsh 的无界面模式**没有逐字直播**能力（回答是一口气出来的），所以我们不装——等待期间屏幕上显示「dsh 引擎思考中·已 3 秒/6 秒/9 秒…」的进度条式提示（全部盖「模拟」章），回答到了就整段一次性显示。这就是契约里的「降级形态如实告知」。

实测：真问「什么是留改拆？」，dsh 约 12-51 秒返回 300 字回答（含宜昌本地政策细节），窗口正常显示、历史正常存档、诊断卡明确标注「dsh 引擎」。三层验收全过：①JS 单测 65 项（含桩事件/失败降级/用户中止三分支）；②格式校验——发出的每条事件都过了官方 JSON Schema 检验器（Python 侧 3 项真校验）；③浏览器端到端实测截图为证。原有轻量引擎复验零退化，全仓 557 项测试通过，MCP 工具接口一个字没动。

两个工程小插曲：①Windows 上调 dsh 必须绕开命令行解释器以防问句里的特殊字符被误当命令（改为直接调底层 node 脚本）；②开发服务器的转发超时 60 秒不够 dsh 慢的时候用（实测一次跑了 51 秒），为 dsh 专用通道定向放宽到 300 秒，其他通道语义不变。

## 一 交付清单

| 件 | 路径 | 说明 |
|---|---|---|
| 后端引擎端点 | `api/aiqa_routes.py`（+80·F_041） | `POST /api/v1/aiqa/dsh_engine`：spawn `dsh --profile emc-test "<q>"` 一次性问答·stdout 全量返回 {ok, output, elapsed, stderr_tail}；超时 30-600s 夹取（默认 240）·**npm shim 解析直调 node+bin.js（argv 传参零注入面）**·解析失败回退全引号命令行 |
| 前端适配器 | `frontend/js/ai_qa/brain-adapter-dsh.js`（新·103 行） | `runDshEngine(acp, ctx, deps)`：诊断卡（engine=dsh 显式）→ tool.begin 桩（dsh_brain·wire 造型）→ 周期 ping（msg.delta reason「已 Ns」步进）→ 返回后 tool.end 配对 + msg.delta content 一次性全文 + seal；失败=error.degraded（DSH_ENGINE_FAIL）不伪造答案；中止=静默退出；`getEngineMode()` 三引擎判别（?engine= / ?acp-mock 回兼容 / window 旗标） |
| 壳分发 | `frontend/js/ai_qa/panel.js`（±10） | send() 三引擎分发：light（默认·orchestrate 传 ACP 通道·S4 路径不变）/ dsh（runDshEngine）/ mock（runAcpMockPeer）——三路同走 buildHooks 接渲染订阅·send 尾部零改动 |
| 代理超时定向放宽 | `frontend/serve.py`（+3） | `/aiqa/dsh_engine` 路径代理读超时 60s→300s（对齐后端 240s 预算·实测 dsh 慢跑 51s 会被 60s 切断）；其余路由含 SSE 维持 60s 语义不变 |
| node 单测⑤ | `tests/acp_channel.test.mjs`（56→65 断言） | BA 成功（桩/配对/ping≥3/全文批量/seal）/ 失败（error.degraded+无 seal）/ 中止（无降级卡）三分支 + synthesized 红线 + wire 严格造型（wireStrict 提为模块级与 ④ 共用） |
| S6 校验器对接 | `tests/acp_schema/ba_wire_dump.mjs` + `test_brain_adapter_wire.py`（3 测） | node 驱动 BA 事件流（fake fetch·无网络）dump wire → pytest 用**真实 jsonschema 校验器**逐个验四族 wire + provenance 诚实性 + process lane 断言——契约 §三验收 1/3 落地 |
| E2E | `tests/browser/she2_ba_dsh_e2e.py` | `?e2e=1&engine=dsh` 真问题端到端（七断言·DoD 证据） |

## 二 验收证据（派发单 DoD 逐项）

| 验 | 结果 | 明细 |
|---|---|---|
| E2E `?engine=dsh` 真问题 | **PASS** | 问「什么是留改拆？」→ 定稿徽章 + 300 字答案（dsh 真回答·含宜昌「十五五」本地政策）+ dsh_brain 工具卡 + ping 桩（已 3s/6s/9s）+ diagnose 卡 engine=dsh + trace 持久化 + 零真 console error（截图 `tests/browser/out/she2_ba_dsh_e2e.png` / `she2_ba_dsh_waiting.png` / `she2_ba_dsh_answer.png`——对话框展开态） |
| node 单测 | PASS | 65 断言 ALL PASS（①-⑤） |
| S6 schema 校验器 | PASS | 3 passed——四族 wire 逐个过 tests/acp_schema/schemas 真校验 + synthesized 诚实性 + process lane |
| 轻量引擎零退化 | PASS | S3 E2E 三场景（A=light 默认路径 SSE mock 全链 / B=mock / C=C3 样式面板）复验全绿 |
| pytest 全量 | PASS | 557 passed / 2 skipped（554+3 BA 新测·本日基线不降反升） |
| MCP 零改动 | PASS | `git diff --stat tools/mcp_server_emc.py` 空 |

**dsh headless 实测形态**（本机·dsh 0.1.1-rc.2）：`dsh --profile emc-test "<q>"` → stdout 纯文本答案·实测 9-51s（波动大·代理放宽依据）·外网可达（api.deepseek.com 通·与壳一期「离线机」判断不冲突——彼时为 CDN 瓦片超时误判全离线）。

## 三 红线与契约对齐

| 项 | 对齐 |
|---|---|
| 降级形态诚实性（契约 §三-3） | BA 发出的全部 msg.delta/tool.*/error 信封 provenance 恒 `synthesized`（node 断言 + S6 pytest 双锁）；ping=「已 Ns」步进非思考流；content=一次性全文不伪装逐字流 |
| wire 兼容（过 S6 校验器） | 四族 wire 与 S4 引擎发射层同构（session 占位 emc-shell·toolcall 配对·seq 单调）——S6 pytest 直接消费 |
| 轻量引擎零退化 | 默认路径（无参 URL）走 orchestrate+ACP 通道·与 S4 交付逐字同路；分发仅加 mode 判别 |
| MCP 工具面零改动 | 未触 tools/；BA 是翻译层非编排层（契约红线——壳不经 BA 调 MCP·dsh 自主决定是否经其 profile 挂载的 G10 工具） |
| 编排权 | 引擎层（dsh agent loop 自主）——壳只消费事件流 |
| 降级不伪造 | dsh 不可用/超时 → error.degraded 固定降级卡（不编答案）；用户中止 → 静默（主动停止非故障） |

## 四 边界与遗留

- **地图联动未含**：派发单 E2E 提「答案+地图联动」——知识型问题（什么是留改拆）无图层产物；dsh 侧 GIS 落图需其经 G10 工具回流 EMC 渲染契约（B 变体五条件线），本批 BA 范围=对话问答链路，落图留 dsh→EMC 数据面联调批次。
- **每次 send 冷启 dsh**：headless 一次性进程（冷启含在 9-51s 内）——常驻会话（ACP session 复用）属 Codex 全量形态/控制面常驻线，非本批范围。
- **turn/render 族 wire 未定稿**：BA 事件 bus 直发不带 wire（与 S4 同口径·S2 增补后统一补）。
- **并行批注记**：件②（知识管线 SOP·claude）已随 93869ba 入库——本批 commit 仅含件① 自有文件（docs/progress.md 他人改动未碰）。

> Qoder · 2026-08-23 · 壳二期件① 完毕——「EMC 窗口用 dsh 当引擎」首次端到端跑通
