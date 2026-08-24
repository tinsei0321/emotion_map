# PT-CB15 · Codex 替换 dsh 计划 · claude 回应（正确性/测试视角·2026-08-24）

> 回应对象：`PT-CB15-Codex替换dsh计划书_zcode-2026-08-24.md`。必读已完成：计划书全文 + SHELL2-FIX 复审（BA dsh 适配器验收口径）+ tests/acp_schema/（五族 schema 校验器·S4/BA wire dump 范式）+ D:/Github/codex-main.zip 源码（codex-rs/app-server-protocol/ schema 与 Rust 源·sdk/python 客户端源·codex-rs/exec 事件源）。零实施零 git 写（本文件除外）。

---

## 〇 一句话结论

**有条件通过**——三步走 C1-C12 骨架成立，但有一处**必改**：C5 的「codex exec --json」规格不成立（该面无 token 增量·「逐字打字」验收①必须走 app-server 协议），另有 D2 选项失真、C4 缺审批接线两处修正——三处修正后即可收敛开工。

## 一 白话摘要段

我拿着 Codex 的官方源码（您指定的 zip）把计划书里"接线怎么接、验收怎么验"两头都核了一遍。**大方向对**：Codex 确实有官方的事件流（相当于"直播"），dsh 只有"录播"，换脑的价值成立。但我发现**三处需要改的地方**：①计划书说用 `codex exec --json` 拿"消息增量"——我查了源码，这个命令只给"整条消息"，没有逐字增量，"直播"必须用另一条官方通道（app-server 协议）才能实现——这是验收第一条"逐字打字"的硬前提，不改必翻车；②"自己写客户端 vs 官方 SDK"这个选择题本身问错了——官方 SDK 本质就是"自己写客户端"的封装版，而且咱们的适配器是浏览器里的 JS，官方的 Python SDK 根本用不上，真正的选择是"用官方 TS 版还是自己写 JS 版"；③审批配置只说了"收紧"，没说机制——Codex 有自己的审批事件族，需要明确映射。验收标准我给了一套能落地的"考卷"：10 道题双引擎对答，机算两个率（路由决策一致率、出图一致率），人工核 3 题的事实点，加上三条回归红线（dsh/轻量/RAG 零退化）。**结论：改完这三点，这活能干。**

---

## 二 源码勘察事实（证据基础·正确性视角立足点）

| # | 事实 | 证据（codex-main.zip） |
|---|---|---|
| F1 | **`codex exec --json` 无 token 增量**——事件是 item 级 JSONL（thread.started/turn.started/item.started/item.updated/item.completed/turn.completed/turn.failed/error）·AgentMessage 是整条 `{text}`·Reasoning 同 | `codex-rs/exec/src/exec_events.rs:30-133`（ThreadEvent 枚举 + `AgentMessageItem{text}`） |
| F2 | **token 增量只有 app-server 协议 v2 有**——`AgentMessageDeltaNotification {delta,itemId,threadId,turnId}` + `ReasoningTextDeltaNotification`·另 18 变体 ThreadItem（userMessage/agentMessage/plan/mcpToolCall/dynamicToolCall…）+ `McpToolCallProgressNotification` | `codex-rs/app-server-protocol/schema/json/v2/AgentMessageDeltaNotification.json`·`ItemStartedNotification.json`（ThreadItem oneOf 18） |
| F3 | **官方 Python SDK 本质 = subprocess 包装**——`Popen([codex_bin,"app-server","--listen","stdio://"])` + stdin/stdout JSON-RPC + 通知路由（`next_turn_notification`）·传输面即 stdio | `sdk/python/src/openai_codex/client.py:238-298`（start/close/request/notify） |
| F4 | 工具调用事件结构：mcpToolCall 变体带 `server+tool+arguments+status(enum: inProgress/completed/failed)+result`·ItemCompleted 带 `completedAtMs`·ErrorNotification 带 `{message,codexErrorInfo}+willRetry:bool` | `ItemStartedNotification.json` variant[7]·`ErrorNotification.json`·`TurnError` |
| F5 | 官方组合 schema 现成：`codex_app_server_protocol.v2.schemas.json`（545KB·draft-07·全 v2 类型）——可直接作测试侧「Codex 输入合法面」校验器 | `codex-rs/app-server-protocol/schema/json/` |
| F6 | dsh BA 验收范式已有：`ba_wire_dump.mjs` + `test_brain_adapter_wire.py`（wire 过真 jsonschema·provenance 诚实性·lane 分层）·S4 主路同范式（s4_wire_dump.mjs）·brain-adapter 契约三形态已注记「Codex 全量形态·恒 real」 | `tests/acp_schema/`·`docs/brain-adapter.md:33-34` |

---

## 三 D1-D6 逐条表态

### D1 接入传输方式（stdio vs streamable-http）—— **partial**

- 议题所指应是 **C1 的 MCP 服务器传输**（Codex 如何调用 EMC 18 件工具）——此面选 HTTP 8600 常驻合理（免冷启动·工具面有缓存·计划书 2.2 已列「MCP 18 件工具全通」）。
- **但 C5 的 app-server 传输是另一个决策面**，勿混：app-server 默认/官方面是 `--listen stdio://`（F3 证据：SDK 即 stdio）。若 D2 走官方 SDK 或自写 JSON-RPC，传输即 stdio 内定，无需再议。
- 证据缺口：app-server 是否支持 `http://` 传输未确认（`app-server/src/main.rs:29-36` 注释只列 `stdio://` 为默认）。**建议**：D1 收敛为「MCP 面 HTTP 8600 常驻 + app-server 面 stdio」双轨，勿把两个面压成一个选择。

### D2 app-server 客户端（subprocess exec --json vs 官方 SDK）—— **disagree（选项本身失真·重组）**

- **exec --json 一票否决**：F1 证明它无 token 增量——不满足 C9 验收①「逐字打字」；它是 **item 级**流（tool call 是整条 arguments+result 一次性到），连「工具调用过程可见」都是降级粒度（无进度）。C5 若按此实现，第一步就偏离验收。
- **SDK=subprocess 的封装修饰**（F3）：「自写 vs SDK」不是二元对立——官方 Python SDK 就是 Popen+JSON-RPC+类型生成。真正的约束是 **brain-adapter-codex.js 是前端 JS**：官方 Python SDK 在本架构用不上（除非起 Node 代理进程——过度设计·否决）。
- **重组后的真选项**：①官方 TS SDK（`sdk/typescript/`·检查其通知流 API 成熟度）②JS 自写 JSON-RPC 客户端（request/notify/next_notification 三函数 + v2 通知路由·类型可从 F5 组合 schema 生成）。**claude 倾向②**——JS 侧自写面很小（协议面就是 4-5 个要消费的通知族），且零第三方依赖、版本锁定即 schema 文件本身（比锁 SDK commit 更稳）；TS SDK 若通知流 API 已够用则选①。**最终裁决留给 Qoder 工程实测**——但 exec --json 面必须从选项表删除。

### D3 人设双层结构（AGENTS.md 常驻段 + 身份卡 skill）—— **agree**

- Codex 原生机制支持（`docs/agents_md.md` 存在·AGENTS.md 常驻 + skill 注入是官方两条路径），拆法（纪律/铁律常驻 + EMC 身份触发注入）与 dsh profile 内容分层天然吻合。
- **补验收**：迁移完整性不能只看文件到位——对拍题库（见 C10）必须含 1 题**身份一致性题**（「你是谁·回答范式」），两引擎答案比对 EMC 身份口径（4×5 矩阵/尺度-方法-范式/工具委托纪律的体现），防「人设拆过去但丢了」。

### D4 流式体验（50ms 批量 + seq 单调）—— **partial**

- 50ms 批量合理（防事件洪泛·同 dsh 的 ping 节流思路）。补三点正确性语义：
  1. **seq 单调 + 全序**：缓冲不得乱序（FIFO 队列·flush 按入队序）；ACP msg_delta 的 wire.seq 从 Codex delta 流序号映射（F2 每 delta 有 itemId——用 itemId 对齐 agentMessage 条目·seq 用转换层自增单调即可）。
  2. **丢包 = 断流 ≠ 静默**：Codex 进程退出/管道断裂 → 必须走 error 族降级（仿 dsh fail-closed 断言「不得静默成功」·SHELL2-FIX 复审 FIX-03 范式），且**转换层要判别「正常 turn.completed 后停止」vs「中途断流」**——前者是收束、后者是错误。
  3. **seal 前 flush 积压**：turn.completed 到达时缓冲内残留 delta 必须先全部发出再 seal——防最后一段滞留（dsh 是全量一次发无此问题·Codex 流式有此坑）。

### D5 双引擎并存（dsh 保留保底）—— **agree**

- 与红线 2（dsh 路径零退化）一致·`?engine=codex` 第四态与 `?engine=dsh` 并列·退役另议。补充：**四态分发有回归面**（getEngineMode 白名单 `light|dsh|mock` 现只认三态——新增 codex 态时 ba 单测同步扩`brain-adapter` 的 getEngineMode 测试·防旧三态行为回归）。

### D6 对拍标准（claude 主交付·「同等质量」量化设计）—— **见下专节**

「同等质量」必须分维量化、不能一个数。五维设计：

| 维度 | 测什么 | 怎么算 | 阈值（通过） |
|---|---|---|---|
| ①口径标签一致率（机算） | 诊断卡路由决策（engine/template/intent）·**分两档**：强一致=template 完全同·弱一致=不同但人工判「都合理」（如 dsh 选 zonal vs Codex 选 overlay 且理由成立） | 强一致数/10 + 弱一致数/10 | **强 ≥ 6/10 且弱 ≥ 9/10**·其余漂移登记表（逐条人工批注合理/不合理） |
| ②出图一致率（机算） | 「出图 vs 不出图」二元决策（render 族事件 + newLayerCount≥1）——出图与否是确定性决策面（同路由应同出图）·**内容不做逐字段 diff**（两 LLM 参数天然不同·严格 diff 必误报） | 同决策题数/10 | **≥ 9/10** |
| ③答案事实核查（人工·抽 3 题） | 每题抽事实点（数字准确/来源正确/结论与数据一致）·**盲跑**（不标引擎名防预期偏差） | 关键事实错误数 | **0**（≤1 非关键错误→有条件通过） |
| ④体验差异（记录·非判据） | 首 token 延迟/总耗时（C10③速度）/流式逐字 vs 一次性（C10④） | 台账记录 | —（不上线判据·供用户体感） |
| ⑤回归判定（门禁） | dsh 零退化（C11）+ 轻量默认零退化 + RAG 96.7% 零退化（红线 2/3/4） | 既有测试全绿 | **三绿必须**（任一红→不通过） |

> 设计依据：口径标签是 LLM 路由决策（两引擎都是 diagnoseStep LLM·本质有随机性）——所以①不能要求 100%，用「强+弱两档+漂移登记」给人工仲裁留位（呼应 CB 既有「LLM 归纳不追 100% 一致·只追可信」口径）；出图决策是工具面确定性的（同路由→同出图）——所以②可严格到 9/10；事实核查是质量底线——③必须 0 关键错。

---

## 四 C9-C12 验收口径（每条从「可见」到「可断言」）

**C9 单引擎验收五条——逐条给断言**（建议写进验收报告达标矩阵：断言/通过/证据三列）：

| # | 验收 | 可测断言 |
|---|---|---|
| ① | 流式输出可见（逐字打字） | msg.delta(content) 条数 ≥ 20 且单条 delta ≤ 64 字符（token 级粒度·非一次性全文）·wire.seq 单调且唯一·首 delta 出现 ≤ 30s（首 token 延迟记录） |
| ② | 工具调用过程可见 | tool.begin/tool.end 成对·verb ∈ 18 件工具名集合·toolcall_id 唯一且 begin/end 配对相等（仿 S4 配对断言） |
| ③ | 落图正常 | 工具型题 render 族事件出现 + newLayerCount ≥ 1·前端图层 selectLayer 到位 |
| ④ | 多轮对话（上下文延续） | 第二轮 turn_id 变·thread_id 不变（Codex thread 贯穿）·第二轮答案人工核含第一轮信息（抽 1 题） |
| ⑤ | 错误语义化降级 | 杀 Codex 进程/MCP 超时场景 → error 族事件·code 语义化（非裸 Error message）·前端降级卡·不裸输（守 EMC 三态出口契约） |

**C10 对拍十题题库构成**（固定题库·同题同参数跑双引擎·盲跑）：

| 类别 | 题数 | 覆盖 |
|---|---|---|
| 分析型（zonal/compare/rank/area_stats 各 1） | 4 | 四路由 + 口径标签一致率主面 |
| 工具链 + 落图（多工具串联题） | 2 | 出图一致率主面 |
| 知识问答（RAG 检索+LLM 综合） | 2 | 答案事实核查主面 |
| 概念题（EMC 身份/范式） | 1 | D3 身份一致性验证 |
| 边界题（超长/空题） | 1 | 错误降级 + 超时路径 |

**红线**：题库与 rag_eval 96.7% 评估集**隔离**（防对拍用例污染 eval 集）；人工核的 3 题输出匿名化（去掉引擎标识）。

**C11 dsh 保底验证**：断言 = `tests/test_dsh_engine.py + test_brain_adapter_wire.py` 全绿（已有 20 passed 基线）+ 对拍期间 dsh 路径随机抽查 2 题不回归。

**C12 验收报告**：达标矩阵（C9 五断言 × 通过/不通过/证据）+ 对拍五维数据表（D6）+ 切换操作指引（?engine=codex 用法 + 回退 dsh 方法）。

---

## 五 测试覆盖设计（Codex 事件转换层 → ACP schema·仿 S4 wire dump）

三层递进（沿用 tests/acp_schema/ 现有范式·不新造轮子）：

**L1 转换层纯函数单测（新 `tests/codex_conv/`）**——Codex v2 通知样例 → 转换函数 → ACP 事件断言：
- 映射正确性：`ItemStarted(mcpToolCall,inProgress)`→tool.begin（verb=工具名·params_summary=arguments 摘要·不携完整参数）·`AgentMessageDeltaNotification`→msg.delta(content)·`ReasoningTextDeltaNotification`→msg.delta(reason)·`ItemCompleted(mcpToolCall,completed)`→tool.end（result 摘要化）·`ItemCompleted(mcpToolCall,failed)`→error 族（toolcall_id 附）·`ErrorNotification`→error 族（code 语义化·hint 提取 codexErrorInfo）·`turn.completed`→turn seal。
- **反向契约**：转换产物 wire 逐个过 tests/acp_schema/schemas 真 jsonschema（复用现有 validator·不复制）。
- **输入合法面**：手搓样例先过 F5 官方 `codex_app_server_protocol.v2.schemas.json`（draft-07）再喂转换层——防「测试测了不存在的格式」（双机无该 schema 文件时 skip·与 node 缺席 skip 同纪律）。
- **边界**：willRetry=true 的 error（Codex 自动重试通知→不立即降级·等终局）·status=failed 工具·大结果转文件机制·未知事件类型（登记 trace + 忽略不崩·`onDegraded` 永不裸输）。

**L2 wire dump 集成测试（仿 s4_wire_dump.mjs 新 `codex_wire_dump.mjs` + pytest）**——fake 事件泵驱动 brain-adapter-codex.js 全路径 → bus 事件流 dump → 断言：四族 wire 过 schema·**provenance 恒 real**（全量形态·与 dsh 的 synthesized 恰反·诚实性契约双向验证）·toolcall 配对·seq 单调·turn diagnose/seal 齐全·lane 分层（process/render 按族）。

**L3 真端点 smoke（C3 四步链）**——list_data→rag_query→zonal_stats→render_spec + 落图·打真 POST 端点（守「验证测实际业务端点」纪律·假 fetch 测不出路由缺失）·**Codex 未装则 skip 不红**（SHELL2-FIX 复审 N3 教训：Part C 曾无缺席守卫必红）。

**L4 错误路径**：进程崩溃/超时/管道断 → fail-closed 断言「不得静默成功」（仿 test_dsh_engine.py:67-75 的 FIX-03 范式）·错误事件 → error 族降级卡语义化。

---

## 六 纠错清单（义务·三处）

1. **C5 规格错误（必改）**：「codex exec --json 事件流解析（JSONL：agent 轮次/工具调用/消息增量）」——exec --json **无消息增量**（F1）·「逐字打字」验收①只有 app-server v2 的 AgentMessageDeltaNotification 能提供（F2）。C5 必改走 `codex app-server --listen stdio://`（JSON-RPC + v2 通知），或随 D2 裁决走 SDK/自写客户端——但面必须是 app-server。
2. **D2 选项失真（必改）**：「subprocess exec --json vs 官方 SDK」二元对立不成立——exec 面不合格（同①）·SDK=subprocess 封装（F3）·且 brain-adapter 是前端 JS——官方 Python SDK 用不上。重组为「TS SDK vs JS 自写 JSON-RPC」。
3. **C4 审批接线缺口（必补）**：C4 只说 render_spec 写面「单独收紧」没说机制——app-server 有独立审批通知族（PermissionsRequestApproval 等·v2 schema 现成）·需明确「Codex approval 流 → ACP approval_req 族」映射（ACP v1.1 已有 approval_req schema·README 接线注记说首个真实消费者=RAG kb_inbox——此处出现第二消费者·需在契约登记·防双头）。

另附 4 条 P3 级注记（不阻塞）：①getEngineMode 三态白名单扩四态需带回归（D5 补）②对拍题库与 rag_eval 集隔离（C10 红线）③大结果转文件在 L1 边界测（计划书 2.1 已提 Codex 有该机制）④Codex 侧 token 用量（turn.completed 带 usage）可记录作成本对比（计划书未提·对拍台账顺手记）。

---

## 七 四档裁决（C1-C12）

| 项 | 裁决 | 条件/修正 |
|---|---|---|
| C1 Codex MCP 注册 | ✅ 通过 | 传输定 HTTP 8600 常驻·startup_timeout≥60 保留 |
| C2 人设迁移 | ✅ 通过 | 补 D3 身份一致性验收题 |
| C3 工具验证 | ✅ 通过 | 补 L3 真端点 smoke（Codex 未装 skip） |
| C4 审批配置 | ⚠️ 有条件通过 | **补 approval_req 接线映射**（纠错③） |
| C5 app-server 客户端 | ❌ **改** | exec --json 面删除·改走 app-server 协议（纠错①） |
| C6 事件转换层 | ✅ 通过 | 按五族映射表（§五 L1）·补 willRetry 语义 |
| C7 brain-adapter-codex.js | ✅ 通过 | 仿 brain-adapter-dsh.js 模式·provenance 恒 real |
| C8 引擎第四态 | ✅ 通过 | getEngineMode 四态 + 回归（D5 补） |
| C9 单引擎验收 | ✅ 通过 | 五条断言化（§四） |
| C10 双引擎对拍 | ✅ 通过 | 按 D6 五维量化 + 十题题库（§三/§四） |
| C11 dsh 保底验证 | ✅ 通过 | 断言=既有 20 用例全绿 |
| C12 验收报告 | ✅ 通过 | 达标矩阵 + 五维数据表 + 切换指引 |

**总裁决：有条件通过**——C5 必改（app-server 面）+ D2 选项重组 + C4 补审批接线，三处修正后即可收敛定稿、交 Qoder 执行。修正后本组验收口径（D6 五维 + C9 五断言 + L1-L4 测试面）即作为 C10-C12 的验收依据。

—— claude · 2026-08-24 · 家机 · 零实施零 git 写
