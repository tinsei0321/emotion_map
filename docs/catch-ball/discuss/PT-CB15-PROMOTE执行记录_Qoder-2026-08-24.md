# PT-CB15 转正批执行记录 · 修复批（Qoder·2026-08-24）

> 依据：`PT-CB15转正批派发_zcode-2026-08-24.md`（三方收敛处置表）。分支 `EMC_Codex_Harness`·commit 前缀 `PT-CB15(PROMOTE):`·零 pull 零 push。
> 门禁实基线对齐说明：派发写 579+4（略滞后），本分支实基线 **581 passed / 2 skipped**（spike 后复测·两者均满足 DoD「585+ 绿」）——记录在案。

---

## 一 白话摘要（零术语·按 AGENTS 3b）

**给新引擎做了一次全面「出厂复检 + 加固」，14 个毛病（1 个必治的 + 11 个限期治的 + 2 个顺手治的）全部处理完，体检从 581 项全过升到 597 项全过，原有本领（知识检索 96.7%、两个旧引擎）一样没退。**

挑三件说：①原来有个「闹钟只在安静时才响」的问题——新引擎如果一直小声说话，超时的闹钟永远不响，现在改成**每听一句就检查一次表**（配了专门的模拟测试）；②原来「家里只能开一台服务器」只是口头约定，现在**代码会自动上锁**——第二台想抢图纸直接让位并每分钟提醒；③原来屏幕刚打开时图纸偶尔塞不进去要手动点一下，现在**塞不进会自动等屏幕就绪再塞一次**。

---

## 二 逐件验证（P1×1 + P2×11 + P3×2）

### P1 必修

| 件 | 修法落地 | 验证 |
|---|---|---|
| P1-1 看门狗「有流量即续命」（Z-01） | `ask()` 主循环每行到达即查预算（静默分支语义保留）·超时消息区分「有流量仍超预算」 | 单测 `test_bridge_highfreq_budget_still_triggers`：每 50ms 吐行·短预算注入·断言部分事件产出后仍 `CODEX_TURN_TIMEOUT` 收口 ✓；静默路径 `test_bridge_silence_budget` 回归 ping+收口语义不变 ✓ |

### P2 限期修（11 件全修）

| # | 修法落地 | 验证 |
|---|---|---|
| P2-1 配对断裂（Z-02） | 桥 tool begin/end 透传 `item.id`→前端 `toolcallByItemId` 映射·end 复用同 toolcall_id | 单测 `test_bridge_parse_events`（begin/end 同 item_id）✓；**线上冒烟实证**：promote_smoke.log 里 `call_00_NYxgq2…` begin/end 同 id ✓ |
| P2-2 cwd 硬编码 | `{REPO}.parent/_codex_cwd` 推导（`Path(__file__).parents[1].parent`·仍仓外隔离）；派发单示例 `parents[1]/...` 落在仓内会破隔离红线——**按红线修正为同级目录**，复刻清单/运维文档同步 | 冒烟实证：桥自动建 `d:\Github\_codex_cwd` 并 spawn 成功 ✓ |
| P2-3 npm vendor 硬编码（Z-04） | 三候选探测：PATH（排除 .cmd shim）→ APPDATA npm vendor（glob 全平台 triplet）→ `npm root -g`（nvm/自定义 prefix）·全败 fail-closed | 冒烟实证（本机走候选 2 命中）✓；启动失败路径单测 `test_bridge_start_fail` ✓ |
| P2-4 model 配置硬编码（B-4） | `CODEX_MODEL_PROVIDER`/`CODEX_MODEL` 环境变量（默认 deepseek+deepseek-chat·用户令 08-24）·`-c` 覆盖只作用桥进程 | 冒烟实证（默认值跑通 DeepSeek 回答）✓；运维文档 §三登记 |
| P2-5 stderr DEVNULL（Z-05/B-5） | stderr=PIPE + 后台抽取环形缓冲末 4KB·五处 error 事件随带 `stderr_tail` | 代码落地（诊断面·故障时可见 rmcp/模型层报错）；单测覆盖 error 事件结构 |
| P2-6 seq 缺口检测（Z-06） | 前端 `lastN` 连续性检查·跳号发 `CODEX_SEQ_GAP` error 事件（不中断渲染·诚实可观测） | 单测 `test_bridge_parse_events` 断言 wire n 单调 1,2 ✓；前端逻辑随 CRLF 测覆盖 |
| P2-7 零测试补测 | 桥解析单测 7 件（坏行/超长行/EOF/配对/高频预算/静默预算/启动失败）+ SSE 帧解析离线 5 件（node 桥式·抽 `sse-parse.mjs` 纯函数）+ 端点错误路径 2 件 + 竞争锁 2 件 = **16 件新增** | 16/16 绿·1.28s ✓ |
| P2-8 map.js 样式竞态（C-1） | addSource 捕「not done loading」→ `map.once('styledata')` 自动重试一次（`_styleRetry` 门闸防环）+ 告警日志 | 白名单内既有 bug·代码落地（重试幂等·日志可观测） |
| P2-9 inbox 竞争（C-4） | **最轻量方案=pidfile 锁**：`_try_claim_watch()` 锁文件记持有者 pid·活实例持锁则让出（每轮重查·死者 1s 内接管）；消费源全局唯一→错向根治 | 单测 2 件（抢占/接管/自持 + 活实例持锁让出·真子进程验证）✓。**评审注记**：跨进程扇出需 IPC·重方案不采；pid 复用误判窗口极小（死者 1s 重抢）可接受 |
| P2-10 运维纪律（C-2） | 新增 `docs/codex-harness-ops.md`（纪律 5 条·第一条=同机单后端 + 自测指引 + 故障速查 + 环境变量表）；竞争锁让出时每分钟 WARN 提醒 | 文档落盘 ✓ |
| P2-11 SSE 帧分隔（R-2） | 两端注释互指（端点 `_gen` + adapter 头部）；解析抽 `parseSseFrames` 纯函数·**CRLF 归一化内含** | 离线测 `test_crlf_frames`/`test_mixed_noise_frame` ✓ |

### P3 顺手（2 件）

| 件 | 落地 | 验证 |
|---|---|---|
| Z-07 握手超时 | `_request` readline 挂 `wait_for 30s`·超时语义化 `握手超时` 异常 | 代码落地（单行） |
| Z-08 `_reason_sent` 每 turn 重置 | **在案验证·无需代码改动**——该变量是 `ask()` 局部（每 turn 天然重置）；冒烟实证推理占位符 1 个 | promote_smoke.log 单占位符 ✓ |

---

## 三 DoD 核验

| DoD | 结果 |
|---|---|
| P1-1 修+测试（高频行流用例） | ✓（§二·含静默路径回归） |
| P2 十一件全修 | ✓（逐件验证表） |
| 全量 pytest 585+ 绿 | **✓ 597 passed / 2 skipped / 0 failed**（65.7s·581 基线 + 16 新增） |
| rag_eval 96.7% 零退化 | **✓ Recall@5 = 96.7%**（caliber 93.8/checkup 93.8/narrative 100/noun 100·越维度 2 件通） |
| light/dsh 引擎零退化 | ✓（dsh/light 代码零触碰·全量绿含 provenance 双锁断言；getEngineMode 白名单仅增不改） |
| 执行记录落盘 | ✓（本件） |
| 显式路径 commit·零 pull 零 push | ✓（收尾执行） |

## 四 转正版端到端冒烟（代码层之外）

重启 8081/8001 组合跑 `sse_client.py`：HTTP 200 → reason 占位 1 个 → `kb_facts` begin/end 同 item_id（**P2-1 线上实证**）→ 44 delta 帧（91ms 均隔）→ done completed（7.1s）。新 cwd 推导目录自动创建·DeepSeek Flash 默认接线正常。

## 五 交付物清单（本次 commit）

| 文件 | 性质 | 要点 |
|---|---|---|
| `core/codex_bridge.py` | 重写 | P1-1 + P2-1/2/3/4/5 + P3-Z07 + readline ValueError 纵深防御（CODEX_LINE_LIMIT） |
| `api/render_routes.py` | 修改 | P2-9 竞争锁（`_try_claim_watch` + watcher 让出逻辑·每分钟提醒） |
| `api/aiqa_routes.py` | 修改 | P2-11 SSE 帧约定注释 |
| `frontend/js/ai_qa/sse-parse.mjs` | 新增 | P2-7/P2-11：帧解析纯函数（CRLF 归一化·离线可测） |
| `frontend/js/ai_qa/brain-adapter-codex.js` | 修改 | P2-1 配对/P2-6 seq 缺口/P2-7 解析引用共享函数 |
| `frontend/js/map.js` | 修改 | P2-8 styledata 重试（既有 bug·白名单内） |
| `tests/test_codex_bridge.py` | 新增 | 桥解析单测 7 件 |
| `tests/test_codex_engine_endpoint.py` | 新增 | 端点错误路径 2 件 + 竞争锁 2 件 |
| `tests/acp_schema/codex_sse_parse_dump.mjs` + `test_codex_sse_parse.py` | 新增 | SSE 帧解析离线测 5 件（node 桥式） |
| `docs/codex-harness-ops.md` | 新增 | P2-10 运维纪律 + 自测指引 |
| `docs/brain-adapter.md` | 修改 | Codex 全量形态状态 → 已验证转正 |

---

> Qoder · 2026-08-24 · PT-CB15 转正批执行记录（14 件全修·597 绿·96.7% 零退化）·待回收
