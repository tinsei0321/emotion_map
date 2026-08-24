# PT-CB15 SPIKE 审计 · claude（正确性/测试/集成视角·2026-08-24）

> 审计对象：Qoder spike 交付 `5925118`（四问全通·条件 PASS）·依据派发单 `PT-CB15-SPIKE审计派发_zcode-2026-08-24.md`。已读：core/codex_bridge.py（233 行）·api/aiqa_routes.py codex_engine 段·frontend/js/ai_qa/brain-adapter-codex.js（121 行）·panel.js/brain-adapter-dsh.js/serve.py 改动·tests/fixtures/codex_appserver_schema/（README+两锚点文件）·执行记录（K-1~K-7 全卡点）。零实施零 git 写（本报告除外）。

---

## 〇 总裁决（先行）

**有条件通过**——spike 四问验证扎实（证据链完整·K-1~K-7 诚实失败记录·红线全部守住），但「spike」与「转正」之间有明确缺口：**①本件零测试新增**（581+2 是 PT-CB14 基线·5925118 无任何 test 文件）②P2 级正确性四件（并发竞态/时长边界/配对语义/锁面错位）③Q4 两残留（K-4/K-5）无防回归测试。条件 = 收敛转正式任务书时，按 C9-C12 口径补测试 + P2 修复入任务书。

## 一 白话摘要段

Qoder 把「新医生（Codex）」的试用期体检做完了，四关全过，我复核了它的体检报告和手术记录。**结论：手术本身成功、红线没碰、记录诚实**——18 件工具全会用、逐字说话实测有录屏级证据、多轮指代和出图管道各环验证通过、老引擎（dsh/轻量/RAG）全部零退化。但我查出**四个需要记入病历的隐患**和一个**大缺口**：①桥的「启动检查」没上锁——两问同时发时可能自摆乌龙（两个进程抢方向盘）；②总时限 300 秒比老引擎的 480 秒预算紧，而咱们实测过复杂分析题最长要 366 秒——**长题会被 300 秒闸门硬砍**；③工具调用「开始」和「结束」事件对不上号（结束事件的关联 ID 是空的，老引擎版是配对的）——以后做事件校验必挂；④协议版本锁只锁了「请求面」，而桥主要消费的「通知面」没锁——Codex 升级改通知格式时没有任何预警。**大缺口：这批交付一个测试用例都没加**——新桥/新端点/新适配器全靠「真实机器实测」，没有自动回归网。这些都不推翻 spike 结论，但转正前必须补齐。

---

## 二 逐文件发现（P1-P3 + file:line）

### S1 `core/codex_bridge.py`

| # | 级 | 发现 | 证据（file:line） |
|---|---|---|---|
| B-1 | **P2** | **ensure() 在锁外·并发双请求竞态自毁**——`ask` 先 `await self.ensure()`（锁外）再 `async with self._lock`。两请求并发：A 进 ensure 完成 spawn（`_proc=procA`·`_thread_id` 仍 None）→ B 的 ensure 条件（`_proc 且 _thread_id`）不满足 → **B 也 spawn procB 覆盖 `_proc`** → A 返回后 turn/start 发到 `self._proc`（procB·未握手）→ 协议错乱；procA 泄漏无引用。实测单用户低频未触发·但并发两问必踩 | [codex_bridge.py:87-118](core/codex_bridge.py#L87-L118)（ensure）vs [codex_bridge.py:126-134](core/codex_bridge.py#L126-L134)（ask 的锁位置） |
| B-2 | **P2** | **300s 看门狗 < PT-CB14 实证 366s 上限**——`_TURN_TIMEOUT_S=300` + 前端硬编码 `timeout_s:300` → 复杂多工具链题（dsh 实证 50-366s·执行记录 §四自认「同量级·50-366s 区间内」）在 300s 被硬砍（CODEX_TURN_TIMEOUT·用户拿 error 非答案）。对比：dsh 端点预算 240s×2 重试=480s·Codex 单预算 300s 偏紧。端点 clamp 上限已允许 600·但前端固定 300 卡死 | [codex_bridge.py:31](core/codex_bridge.py#L31)·[brain-adapter-codex.js:45](frontend/js/ai_qa/brain-adapter-codex.js#L45) |
| B-3 | P3 | `_SPIKE_CWD` 硬编码盘符（`D:\Github\...`）——执行记录 §八自己标注「office 机盘符不同需改」·建议按 {REPO} 同级推导（认同执行记录建议·转正时改） | [codex_bridge.py:28](core/codex_bridge.py#L28) |
| B-4 | P3 | `-c model_provider="deepseek"` 硬编码——有用户令依据（08-24）·切回 glm 需改代码·建议将来入仓外 config | [codex_bridge.py:101-102](core/codex_bridge.py#L101-L102) |
| B-5 | P3 | `stderr=DEVNULL`——app-server fatal/panic 诊断全弃流·仅 stdout JSON-RPC 可见·排障面缺口（spike 有 K-2 PowerShell 取证坑先例·stderr 弃流后此类问题更难查） | [codex_bridge.py:104](core/codex_bridge.py#L104) |
| B-6 | P3 | `_request` 握手期只认本 rid 响应·其余通知静默丢弃——thread/start 期间的 MCP startup 通知丢失（spike 实测无碍·emc ready 0.4s·风险低） | [codex_bridge.py:74-85](core/codex_bridge.py#L74-L85) |
| B-7 | P3 | **F_042 免 @track 豁免——核实通过**：K-3 实证（track_async 包 async generator→`__aiter__` 丢·`'async for' requires...`）+ 端点 F_043 track_async 链路覆盖 + 注册表描述注明——豁免理由成立。R3（track_gen 变体）为后续改进·不阻塞 | [codex_bridge.py:123-125](core/codex_bridge.py#L123-L125)·[执行记录 §七-R3](docs/catch-ball/discuss/PT-CB15-SPIKE执行记录_Qoder-2026-08-24.md) |

**看门狗/心跳交互核验（派发点①·专项）**：15s `wait_for(readline)` 超时发 ping 继续·总预算到发 error 收口——asyncio StreamReader 取消后 `_read_line` 缓冲保留·**心跳不丢已读行**（安全）；但「有数据但 turn 不结束」场景（工具调用挂起）不触发心跳——依赖 MCP 侧 tool_timeout_sec=120 兜底（配置面）——链条无洞。**线程生命周期核验**：EOF→error 帧+`_proc=None`+`_thread_id=None`→下轮重建 ✓（诚实标注）；`close()` 无调用方（单例=服务生命周期·合理）。**多轮续用核验**：同 thread 连续 turn/start ✓（Q4 指代实证）·EOF 后上下文丢弃为降级路径·合理。

### S2 `api/aiqa_routes.py` codex_engine 段

| # | 级 | 发现 | 证据 |
|---|---|---|---|
| R-1 | **P2** | **空 question 前端静默成功**——端点空 question 返回 JSON `{ok:false}`（HTTP 200·非 SSE）→ 前端 `r.ok=true` + SSE 解析器找不到帧 → 流读完 → `full=''`·`fail=null` → **seal 空答案·exit='final'·看似成功**（不落 error 族）。dsh 版无此坑（一次性 JSON·ok:false 走 fail 分支）——SSE 解析器遇非 SSE 响应的行为未防御 | [aiqa_routes.py:224](api/aiqa_routes.py#L224)·[brain-adapter-codex.js:47-119](frontend/js/ai_qa/brain-adapter-codex.js#L47-L119) |
| R-2 | P3 | SSE 帧分隔依赖 `\n\n` 两端约定（非规范 CRLF 兼容·`\r\n\r\n` 会断）——当前两端同源可控·若未来换 SSE 库/代理改写换行则断·建议注释标注约定 | [aiqa_routes.py:228](api/aiqa_routes.py#L228)·[brain-adapter-codex.js:58](frontend/js/ai_qa/brain-adapter-codex.js#L58) |
| R-3 | ✓ | **复用度评估：无复制粘贴面**——post_codex_engine（36 行·SSE 流式 async gen）vs post_dsh_engine（一次性 JSON·subprocess）形态差异天然分离·除 tracker 外零共享·双维护风险不成立 | [aiqa_routes.py:197-231](api/aiqa_routes.py#L197-L231) |
| R-4 | ✓ | **错误路径全语义化**：桥启动失败/EOF/超时/协议错→error 帧（fail-closed·不 500）·SSE 开流后异常→error 帧兜底（CODEX_ENDPOINT）·与 dsh 端点同一纪律 | [aiqa_routes.py:220-228](api/aiqa_routes.py#L220-L228) |

### S3 `frontend/js/ai_qa/brain-adapter-codex.js`

| # | 级 | 发现 | 证据 |
|---|---|---|---|
| A-1 | **P2** | **tool.end 的 wire.toolcall_id 恒空串·begin/end 不配对**——tool.begin 用 `toolcallId(name)`（含 `_seq`）·tool.end 发 `toolcall_id:''`（done 事件同）——与 dsh 版配对语义不对称（dsh 版 begin/end 同 id）·且违反 S4 配对断言标准（test_s4_wire.py:86-89 同款断言——本适配器一旦纳入 wire 校验必挂）。**更深一层**：begin 的 toolcallId 含 `_seq`·而 delta 也吃 `_seq`——begin 与 end 之间 `_seq` 已漂移·即使想回填也对不上——需 begin 时存 map、end 时取 | [brain-adapter-codex.js:21](frontend/js/ai_qa/brain-adapter-codex.js#L21)·[brain-adapter-codex.js:82,89](frontend/js/ai_qa/brain-adapter-codex.js#L82-L89) |
| A-2 | P3 | **双轨并存未验证**：SSE error 帧已发 error 族 + 流中已有部分 delta → ④ 有 full 时不再补发 error 且直接 seal——bus 上「降级卡 + 答案」并存·渲染端行为未验证（低概率·但 K-5 已证明渲染路径有竞态先例·值得在 E2E 里点一次） | [brain-adapter-codex.js:110-118](frontend/js/ai_qa/brain-adapter-codex.js#L110-L118) |
| A-3 | ✓ | **provenance 恒 'real'·诚实性红线符合**——全量形态契约（brain-adapter.md §二）·错误事件标 real 亦合理（错误是真的·非合成桩）·与 dsh 的 synthesized 恰成双向对照 | [brain-adapter-codex.js:31,68,75,93](frontend/js/ai_qa/brain-adapter-codex.js#L31-L93) |
| A-4 | ✓ | **丢弃防护=帧级容错非静默**：坏 JSON 帧 continue（丢帧不崩）·流中断按 fail/full 收口（有内容则 seal 已收·诚实不丢弃）——delta 帧丢字不可恢复但低频可接受 | [brain-adapter-codex.js:63,99-118](frontend/js/ai_qa/brain-adapter-codex.js#L63-L118) |
| A-5 | ✓ | **与 dsh 版对称性**：诊断卡/630s 总护栏（对齐 FIX-04）/abort 静默/失败 error 族/成功 seal——结构对称·差异均为形态所需（SSE 消费 vs 一次性 POST·真 delta vs 桩） | 全文件 |

### S4 第四引擎白名单 + S5 serve.py

| # | 级 | 发现 | 证据 |
|---|---|---|---|
| W-1 | ✓ | **白名单回归风险 = 零**——`getEngineMode` 条件短路加 `'codex'`（一行）·light/dsh/mock 三态行为不变·mock 的 `?acp-mock=1` 兼容映射未动；panel 分发 `else if` 链新增分支·徽标 MODES 加 codex（#10a37f）——回归证据=581+2 全量绿（同 PT-CB14 基线·见 §六） | [brain-adapter-dsh.js:23](frontend/js/ai_qa/brain-adapter-dsh.js#L23)·[panel.js:1776-1779](frontend/js/ai_qa/panel.js#L1776-L1779) |
| W-2 | ✓ | **serve.py 分层合理**：600s 定向读超时 + SSE 50s Timer 豁免·沿 dsh/render 双先例·无新风险。**链条审视**：后端 300s（最紧·B-2）< 代理 600s < 前端 630s——后端先砍·一致但偏紧（B-2 同根） | [serve.py:263-266](frontend/serve.py#L263-L266)·[serve.py:286-289](frontend/serve.py#L286-L289) |

### S6 schema 锁

| # | 级 | 发现 | 证据 |
|---|---|---|---|
| L-1 | **P2** | **锁面错位：锁了请求面·漏了通知面（bridge 主消费面）**——bridge 消费的 item/agentMessage/delta·item/started·item/completed·turn/completed 全是 **Server→Client 通知**·其 schema 在 v2/ 全量产物（291 文件·不入仓）；仓内 ClientRequest.json（182KB）是请求面·ClientNotification.json（0.4KB）只是 Client→Server 的 initialized（近空）。README 升级检查流程只 diff ClientRequest.json——**通知面漂移不可检测**（通知字段改名/删字段时 bridge 断链零预警）。修复：通知面聚合锚点入仓（或重建脚本+通知面 diff 命令） | [tests/fixtures/codex_appserver_schema/README.md:17-29](tests/fixtures/codex_appserver_schema/README.md#L17-L29) |
| L-2 | ✓ | **重建命令可复现**：`codex app-server generate-json-schema --out ...` 明确·锚 0.149.1·稳定面（未加 --experimental）·「派生资产只记命令」纪律符合 | [README.md:10](tests/fixtures/codex_appserver_schema/README.md#L10) |

### S6 测试覆盖（派发点⑥·核心缺口）

| # | 级 | 发现 | 证据 |
|---|---|---|---|
| T-1 | **P2** | **spike 交付零新增测试**——`git show 5925118 --name-only tests/` 仅 fixture 数据文件（ClientRequest/ClientNotification/README）·无任何 test_*.py；581+2 = **PT-CB14 修复批基线**（6d08939 明示「新基线581+2」·非本件新增）。bridge/端点/适配器三层**全部无测试**（连 node dump 都没有）——回归只能靠真 Codex 机器·可移植性差（双机差异） | `git show 5925118 --stat`·[6d08939](docs/decisions.md) |
| T-2 | **P2** | **Q4 两问题无防回归测试**——K-4（双后端 inbox 竞争）无测试（架构级 R1·环境因素·短期纪律=同机单实例）·K-5（map.js 样式竞态·既有 bug）无测试（R2 建议·未修）——两问题均「记录在案」但无自动网·K-5 尤其会在任何 SSE 早于样式到达的场景复发 | [执行记录 §五 K-4/K-5](docs/catch-ball/discuss/PT-CB15-SPIKE执行记录_Qoder-2026-08-24.md) |
| T-3 | ✓ | **track_id 合规面**：F_042/F_043 注册连续不跳号·validate_track_ids.py（ast 扫描 @track 去重）不报——F_042 免装饰器豁免下注册面仍合规（描述性注册） | [tests/validate_track_ids.py](tests/validate_track_ids.py) |

---

## 三 横切发现

| # | 发现 | 性质 |
|---|---|---|
| X-1 | **spike 验证面宽但边界薄**——Q1-Q4 覆盖功能面（工具/流式/壳/多轮/出图·证据链完整）·但并发（B-1）、时长边界（B-2）、配对语义（A-1）、非 SSE 响应（R-1）四个正确性死角未碰——「条件 PASS」的条件正在于此 | 承接总裁决 |
| X-2 | **测试可移植性倒挂**——codex 链路唯一验证手段是真机器实测（spike 日志/截图·仓外）·而 office 机未装 Codex 时（复刻清单差异注记）——双机差异下 office 侧零验证手段。转正后建议：bridge 纯逻辑抽函数（解析/映射与 spawn 解耦）→ 无机器可单测；真机 E2E 走 skip 纪律（node 缺席 skip 同款） | 测试架构建议 |
| X-3 | **纠错③（C4 审批接线）被 spike 实测化解**——K-1 实证：app-server 下工具直接放行（config `default_tools_approval_mode="approve"` + turn 参数 approvalPolicy='never'·read-only 沙箱）·approval 流根本不出现 → approval_req 族映射无需实现。**但注意配置耦合**：approvalPolicy='never' 写死 + 依赖 config approve——config 一旦改 strict 语义·链路断（P3 记录） | 收敛登记 |
| X-4 | **DeepSeek 定向覆盖验证充分**——假 key 证伪（401 响应含 api.deepseek.com/responses 目标 URL）确证请求真实发往 DeepSeek·桌面顶层 glm 配置不受影响·可审计 | ✓ |

**红线核查（全部守住）**：MCP 18 件零改动 ✓·dsh 路径零改动（白名单一行）✓·light 零触碰 ✓·RAG 零触碰 ✓·Codex 配置仓外 ✓·cwd 隔离 ✓·581+2 全量绿 ✓——**这是「有条件通过」而非退回的根基**。

---

## 四 四档总裁决

**有条件通过**。

- **通过依据**：四问实测证据链完整（18 工具全通·74 delta 逐 token·浏览器 MutationObserver 31 次 DOM 增量·望洲社区 -1.061 与服务端交叉校验）·K-1~K-7 诚实失败记录（含 K-2 取证坑自曝）·红线全守·回归基线全绿。
- **条件（转正式任务书必带·三件）**：
  1. **补测试**——按 C9-C12 口径：bridge 解析/映射纯函数单测（spawn 解耦·无机器可跑）+ 端点 SSE 帧测试 + brain-adapter-codex.js node dump（仿 s4_wire_dump 范式·**toolcall 配对断言**将直接暴露 A-1）·真机 E2E 走 skip 纪律；
  2. **修 P2 四件**——B-1 ensure 加锁（双检锁）·B-2 前端 timeout_s 提 600（对齐 dsh 630s 护栏·端点 clamp 已允许）·A-1 tool.end 回填 begin 的 toolcall_id（begin 存 map）·L-1 通知面锚点入仓（或重建脚本补通知面 diff）；
  3. **Q4 残留处置**——K-5（map.js 样式竞态）建议随本里程碑修（R2·SSE 早于样式到达是常态）·K-4 短期纪律登记（同机单实例）。
- **P3 挂账（不阻塞）**：B-3 盘符硬编码（转正改 {REPO} 推导）·B-4 模型商硬编码（入仓外 config）·B-5 stderr 弃流·B-6 握手期通知丢弃·R-1 空 question 前端静默（端点 422 化或前端非 SSE 检测）·R-2 SSE 分隔约定注释·A-2 双轨并存 E2E 点检·X-3 config 耦合注记·R4 计量（token 用量恒零·下批补）。
- **回看**：本审计与派发单的「条件 PASS」预判一致——spike 的价值在验证不在交付·缺口集中在「转正」的工程化层（测试+边界）·非 spike 本身失职。

—— claude · 2026-08-24 · 家机 · 零实施零 git 写
