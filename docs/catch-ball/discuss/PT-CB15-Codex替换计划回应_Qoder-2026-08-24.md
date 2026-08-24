# PT-CB15 · Codex 替换 dsh 计划 · CB 回应（Qoder 组·工程视角·2026-08-24）

> 回应对象：`PT-CB15-Codex替换dsh计划书_zcode-2026-08-24.md`。身份：工程评审方 + 收敛后预定执行方（本文按「我怎么实施」口径细化）。
> 证据基座：codex-main.zip 源码实读（`codex-rs/config/src/mcp_types.rs`·`codex-rs/app-server/README.md`·`codex-rs/protocol/src/protocol.rs`·`sdk/typescript/src/exec.ts`·`sdk/python/pyproject.toml`+流式样例）+ EMC 侧四件参照物（`docs/brain-adapter.md`·`frontend/js/ai_qa/brain-adapter-dsh.js`·`api/aiqa_routes.py post_dsh_engine`·`tools/mcp_server_emc.py`）。零实施·零 git 写。

---

## 一 白话摘要（零术语·按 AGENTS 3b）

计划的大方向对：相当于把「每次写一封信等回信」的问诊方式，换成「视频通话」——能看见医生边想边说、边动手查资料。插座（工具集）都是现成的，不用重拉电线。

但我翻完「新设备」的出厂手册（Codex 源码）后，发现**三处要在开工前修正**：

1. **计划书选的接线方式是「实验线路」**——官方给它标了"实验性、不保证稳定"。官方真正给「自建界面」用的是一条有正式说明书的线路，我建议换到那条（详见 D2）。
2. **计划漏了第一步「装电话」**——这台新设备要先登录账号或配钥匙（认证）才能响。两台机器都还没装没登，不先做这步，第一天就卡住（建议补 C0）。
3. **工期报少了**——按「装电话 + 正式线路接线 + 通话质量对拍」实算，建议 4-5 天，不是 3-4 天。

一句话：**方向同意·可以开工·但按上面三处修正后的任务书开工。**

---

## 二 一句话结论

计划方向正确、三步走可执行、复用资产盘点准确；但 **D2 的接入通道选型须改**（`codex exec --json` 是实验性旗标路径，官方自建 UI 正路是 `codex app-server` 常驻协议）、**须补 C0 认证前置**、工期按 4-5 天重估——其余议题同意或补强。

---

## 三 源码勘察事实清单（后续条目的共同证据）

| # | 事实 | 出处（codex-main.zip 内） |
|---|---|---|
| K1 | MCP 双传输均官方支持：stdio（`command/args/env/cwd`）与 streamable_http（`url` + 可选 `bearer_token_env_var/http_headers`）；共享字段 `startup_timeout_sec`/`tool_timeout_sec`/`default_tools_approval_mode`/`enabled_tools`/`required`（=true 时该 MCP 初始化失败则 codex 直接报错退出） | `codex-rs/config/src/mcp_types.rs` |
| K2 | `codex app-server` = 官方「自建 UI」通道（VS Code 扩展就用它）：JSON-RPC 2.0 · stdio JSONL 为**默认且稳定**传输（websocket 标注 experimental/unsupported）；生命周期 `initialize → thread/start(/resume/fork) → turn/start → item/* 事件流 → turn/completed`；支持 `turn/interrupt`、审批往返（server→client request）、`mcpServer/startupStatus/updated` 启动状态通知、背压错误 `-32001`（可重试） | `codex-rs/app-server/README.md` |
| K3 | 事件粒度：`item/agentMessage/delta`（正文增量）/`item/started`/`item/completed`/`turn/plan/updated`/`thread/tokenUsage/updated`；item 生命周期恒为 started→deltas→completed；`turn/completed.status ∈ completed|interrupted|failed`，失败携 `error{message, codexErrorInfo}` | 同上 §Events |
| K4 | `codex exec --experimental-json` 是 TS SDK 走的 JSONL 路径——**旗标名自带 experimental**；exec 形态一次性、多轮须 `resume <threadId>` 重启进程、无中途打断与审批往返 | `sdk/typescript/src/exec.ts` L90 |
| K5 | `codex app-server generate-ts / generate-json-schema --out DIR`：可导出**与当前二进制版本严格匹配**的协议 schema——官方自带的版本锁机制（稳定面默认输出·实验面需 `--experimental`） | README §Message Schema/§Experimental API |
| K6 | Python SDK（`openai-codex`）：版本号 `0.0.0-dev`，但依赖硬锁 `openai-codex-cli-bin==0.147.0`（SDK 自带捆绑二进制）；classifier 标 Production/Stable；API = `AsyncCodex → thread_start → turn.stream()`（pydantic 类型化事件）；构建链 = uv（`uv_build`） | `sdk/python/pyproject.toml` + `examples/03_turn_stream_events/async.py` |
| K7 | 内部事件层（EventMsg）含 `AgentMessageContentDelta`/`ReasoningContentDelta`/`ItemStarted`/`ItemCompleted`/`McpToolCallBegin/End`/`ExecCommandOutputDelta`/`TurnComplete`——思考链与正文**原生分流** | `codex-rs/protocol/src/protocol.rs` |
| K8 | 线程持久化：`thread/resume` 可跨进程恢复；分页线程**单进程写锁**（占锁者外写入报 `-32600`）→ 支持「常驻单进程」客户端设计 | README §thread/resume |
| K9 | Codex 自带 Windows 编码兜底（shell 输出 chardet 探测 + 代码页修正）——官方对 Windows 坑有意识投入 | `codex-rs/protocol/src/exec_output.rs` |
| K10 | EMC 侧：`tools/mcp_server_emc.py` 双模式齐全——`--http` 走真 `transport='streamable-http'`（8600·start.bat 常驻·含 ~15s 启动预热），默认 stdio 模式**每次启动同样跑 ~15s 预热**；dsh 现链路已验证 8600 HTTP 消费 | `tools/mcp_server_emc.py main()`·`start.bat` |
| K11 | EMC 侧：ACP v1.1 契约 §四已预置 Codex 宿主映射表（msg.delta↔AgentMessageDelta 等）·§五-1 明文「轻循环/全量形态恒 `real`」·S6 wire schema 校验器 + `ba_wire_dump.mjs` node 桥式测法现成 | `docs/acp-contract-v1.md`·`tests/` |

> 说明：D1 的「实测双传输」我本轮以**静态勘察 + 双端实现确认**完成（两传输的配置面与 EMC 服务端实现均已核实）；运行时冒烟（同 config 两段·各起一次 tools/list）列为实施首日第一个任务（约 30 分钟），不作为评审阻塞项——证据已足够给出推荐。

---

## 四 D1-D6 逐条表态

### D1 传输方式：stdio vs HTTP —— **agree（HTTP 主选）·附强证据与兜底**

- **推荐 HTTP（streamable-http · 8600 常驻）**，与主手倾向一致，理由比计划书更硬：
  1. 8600 已是 start.bat 常驻服务、dsh 链路已验证可用（K10）——Codex 直接复用，零新增进程；
  2. stdio 的隐藏成本计划书未计入：EMC MCP stdio 模式每次冷启动含 **~15s 预热**（源码 `_warmup()`），每个会话白付一次；HTTP 常驻则预热一次全场共享；
  3. 审批/超时配置面两传输相同（K1），选型不受审批需求影响。
- **兜底与防呆两条**：
  1. config 里设 `required = true` + `startup_timeout_sec = 10`——8600 未起时**快速失败报错**，而不是像 dsh 那样静默退化成无工具纯问答（K1 的 `required` 字段就是干这个的）；
  2. 复刻清单保留 stdio 段模板（`command=py, args=[tools/mcp_server_emc.py], cwd={REPO}`），8600 不可用的机器可照抄切换（双环境差异注记·占位符不硬编码路径）。
- C4 审批配置可直接落地：`default_tools_approval_mode = "auto"`（18 件读面）+ `tools.render_spec.approval_mode = "prompt"`（写面单独收紧）+ `tool_timeout_sec ≥ 120`——字段全部源码实存（K1）。

### D2 subprocess vs SDK —— **disagree 计划写法·改为「app-server 主路」**

计划书 C5 写的「`codex exec --json` 事件流解析」是本轮**最重要的一处纠错**（源码证据见下），修正后的三档：

| 档位 | 方案 | 裁决 |
|---|---|---|
| **主路** | Python 自持 `codex app-server --stdio` 子进程：asyncio 薄 JSON-RPC 客户端（`initialize`/`thread/start`/`turn/start`/`turn/interrupt` + notification 分发，预估 ~200 行） | ✅ 官方稳定面（K2）·真流式+多轮+打断+审批往返全有·纯标准库零新依赖·契合「纯净官方版·只配置」红线 |
| **对冲** | `openai-codex` Python SDK（版本锁 `==0.147.0` 随 cli-bin 硬绑） | ⚠️ 主路 JSON-RPC 握手若撞墙（elicitation/extensions 协商细节）再切；引入须走 requirements 钉版 + uv 构建链进依赖清单（K6） |
| **冒烟用** | `codex exec --experimental-json` | ❌ 不作主路——实验旗标无稳定承诺（K4）·一次性无多轮·仅实施首日 30 分钟工具链冒烟 |

对计划书 D2 论据的两点修正：①「锁 commit 的 schema 类型作对冲」不必自造——官方就有 `codex app-server generate-json-schema`，产物与二进制版本严格匹配（K5），**把该产物存仓即版本锁**，Codex 升级时 diff 一目了然；②「SDK 0.0.0-dev 无语义化版本」属实但其 cli-bin 依赖已钉死 0.147.0，SDK 路线的版本风险比计划书描述的略低——维持「不作首选」结论的理由主要是构建链与供应链新增，而非纯版本号。

### D3 人设双层结构 —— **partial（工程面限定表态·同意拆分·指一个真坑）**

- 同意「纪律铁律 → 常驻层、身份卡 → skill 注入层」的拆法；Codex 仓内 `ext/skills` 确为官方机制，skill 路线可行。
- **工程真坑**：Codex 有**两个** AGENTS.md 层——全局（`~/.codex/AGENTS.md`）与项目（cwd 下的 `AGENTS.md`）。若壳调用时 cwd 指向本仓库，**本仓那份 9-Agent 协作规范 AGENTS.md（写给 Claude Code 的）会被注入 Codex 上下文**，内容错位且极长。C2 落地必须显式：人设写全局层（仓外·合红线 5）+ 调用侧用 `--cd`/`cwd` 指向干净目录或明确接受项目层注入并裁剪。此点列为 C2 验收项。

### D4 流式实现（JSONL 增量 → ACP msg.delta） —— **agree 框架·给完整工程案**

**事件映射表**（C6 交付物·按 K2/K3/K7 制定）：

| Codex app-server 通知 | ACP 事件 | 注记 |
|---|---|---|
| `item/agentMessage/delta`（payload.delta） | `msg.delta(kind='content', provenance='real')` | 恒 real（契约 §五-1 全量形态红线） |
| 思考/推理增量（reasoning item 流） | `msg.delta(kind='reason', provenance='real')` | 思考链正文原生分流（K7）·前端分样式渲染已支持 |
| `item/started`（工具/命令 item） | `tool.begin(name, params_summary)` | MCP 工具名直取 |
| `item/completed` | `tool.end(payload 摘要·有则带 caliber)` | 载荷结构模式按契约 §五-2·沿 `tool_contracts.py` 权威源 |
| `turn/completed(status='failed')` | `error(code, hint)` | 取 `error.message/codexErrorInfo` 语义化 |
| 命令输出增量 | `proc.delta`（可选族） | v1 先不接·留口 |
| 未知通知 | 忽略 + [TRACE] 日志 | **容错不 fail-closed**——Codex 快速发版加新事件是常态 |

**缓冲/粒度**：同意 50ms 批量转发；加两个触发器——**句末标点即冲**（首字延迟优先）与**单批字节上限**（防长段一次性喷）。前端真流式渲染路不新造：轻循环引擎（S4）已发真 `msg.delta`，`buildHooks` 渲染订阅现成，codex 适配器复用同路（dsh 版只是桩形态特例）。

**「丢包」重述**：stdio JSONL 是有序单流，无网络丢包问题；真风险三个，逐一对策——
1. **背压**：app-server 有界队列饱和回 `-32001`（README 明说可重试）→ 请求侧指数退避+抖动；
2. **管道阻塞**：慢消费者会憋爆服务端队列 → 后端异步非阻塞读、`proc.delta` 类高频事件可丢弃（先留口不接即天然规避）；
3. **SSE 代理截断**（本项目实证过的老坑）：dsh 时代已有「serve.py 对 `dsh_engine` 定向放宽 + render SSE 心跳豁免」两套先例——codex 走 SSE 长驻流，**照抄 render SSE 模式（15s 心跳 + 豁免）**，不走 dsh 的一次性 POST 模式。

**seq**：wire 层沿用 dsh 版 `_seq++` 单调模式（`wireDelta` 同款）；单流有序即天然单调，无需重排。

### D5 双引擎并存 —— **agree·附改动面清单**

同意四态常驻、dsh 保留保底。工程改动面（均为小改，但要点名防漏）：
- `getEngineMode()` 现硬编码白名单 `(m === 'dsh' || m === 'mock') ? m : 'light'`——加 `codex` 一支；
- panel `send()` 分发加 codex 分支（仿 dsh 分支结构）；
- **验收复用现成武器**：S6 wire schema 校验器 + `ba_wire_dump.mjs` 桥式测法（node 驱 JS 产 JSON → pytest jsonschema 校验）——codex 适配器 wire 直接过这道闸，即 C9「契约符合性」的可执行形态，不用新造测试框架；
- dsh/light/mock 三态回归：既有断言（含 provenance 双锁）零改动跑绿即「保底零退化」证据。

### D6 对拍标准 —— **partial agree·补三类自动量化**

claude 主导的「口径标签一致率/出图一致率/人工核 3 题」同意作骨架；工程侧补三类**零人工成本**量化：
1. **工具链一致率**：同题双引擎的工具序列+关键参数从事件日志自动提取做 diff；
2. **出图确定性比对**：`render_spec` JSON 直接 diff（确定性产物·机器判）；
3. **延迟分解**：首字时间 / 总时长 / 单工具耗时三档记录——这是「流式体验升级」的唯一硬证据，没有它验收只有主观感受。

---

## 五 C5-C8 实施细化（「我怎么实施」口径）

### 文件级拆解

| 件 | 新增/改 | 内容 |
|---|---|---|
| `core/codex_bridge.py`（新） | 新增 | app-server 进程管理（常驻单例 + 懒启动 + 看门狗重启）+ 薄 JSON-RPC 层（initialize/initialized 握手、thread/start、turn/start、turn/interrupt、notification 分发）；`@track` + `register_track_id('MOD_AIQA.F_042', ...)`（编号续 F_041 不跳号） |
| `core/codex_acp_map.py`（新） | 新增 | 第四节映射表纯函数实现 + 未知通知容错；`MOD_AIQA.F_043` |
| `api/aiqa_routes.py`（改） | 新增端点 | `POST /api/v1/aiqa/codex_engine`（**SSE**·15s 心跳·照 render SSE 豁免模式）；并发闸复用 `Semaphore(2)` 模式；`MOD_AIQA.F_044` |
| `frontend/js/ai_qa/brain-adapter-codex.js`（新） | 新增 | 仿 dsh 版骨架（bus emit + wire 造型 + seq）；差异：fetch→SSE ReadableStream 消费、`msg.delta` 真流式、**恒 `provenance:'real'`**、abort 语义沿用（用户停止=静默退出非故障） |
| `frontend/.../panel.js`（改） | 小改 | `getEngineMode()` 白名单 + send() 分发第四态 |
| `tests/`（新） | 新增 | codex wire dump 过 S6 校验器（桥式测法复刻）+ 映射表单测 |
| 仓外 `~/.codex/config.toml` | 配置 | `[mcp_servers.emc]`：`url="http://127.0.0.1:8600/mcp"`·`required=true`·`startup_timeout_sec=10`·`tool_timeout_sec=120`·`default_tools_approval_mode="auto"`·`tools.render_spec.approval_mode="prompt"`；进复刻清单（占位符·双机各配） |

### 关键设计决定（含理由）

1. **app-server 常驻单例进程**（非每请求 spawn）：thread 写锁单进程约束（K8）+ initialize 握手成本 + 多轮 resume 连续性，三条共同指向常驻；进程死 → 看门狗重启 + 当前轮发 `error` 族（不伪造）。
2. **端点形态 = SSE 而非一次性 POST**：这是与 dsh 端点的结构性差异——dsh 无流式才能一次性返回；codex 真流式必须长驻流。serve.py 代理豁免照 PT-CB7 T21 先例登记。
3. **超时预算沿慢侧设计**（PT-CB14 实证：多工具链 50-366s）：前端看门狗 630s 起步·代理定向豁免·后端不设粗暴总闸，靠心跳保活。
4. **Schema 锁**：实施当日跑 `codex app-server generate-json-schema --out`，产物存仓（建议 `tests/fixtures/codex_appserver_schema/`），Codex 升级时 diff 为第一检查项。
5. **冒烟序列（首日）**：`codex exec --experimental-json "列出可用工具"` 验证工具链 → 再进 app-server 握手——最快暴露安装/认证/PATH 问题。

---

## 六 预判坑清单（按风险降序）

| # | 坑 | 级别 | 对策 |
|---|---|---|---|
| P1 | **认证前置缺失（计划书未列）**：Codex 需 ChatGPT 登录或 API key（`CODEX_API_KEY`），双机均未装未登 | 高·阻塞 | 补 **C0**：双机安装+登录（密钥类资产按红线 5 仓外·复刻清单只记步骤不记密钥）；无 C0 则 C1 起步即死 |
| P2 | **exec --json 实验旗标**（若按原计划走） | 高 | D2 已纠：主路换 app-server 稳定面 |
| P3 | **cwd AGENTS.md 注入错位**：cwd=仓库时本仓协作规范被注入 Codex | 中 | C2 验收项：明确全局/项目两层归属 + `--cd` 定向（见 D3） |
| P4 | **版本漂移**：Codex 快速发版（现 0.147.0）·实验面字段随时变 | 中 | 只用稳定面（不开 `experimentalApi`）+ generate-json-schema 存仓版本锁 + 升级先 diff |
| P5 | **Windows 链路的已知模式复发**：GBK 控制台编码（`_safe_print` 惯例）、管道编码 | 中 | 子进程 stdout 按 UTF-8 bytes 读（JSONL 恒 UTF-8）·打印全走 `_safe_print`；Codex 本体对 Windows 编码有投入（K9），风险主要在 EMC 侧胶水 |
| P6 | **spawn 形态比 dsh 简单但别大意**：codex 是原生 exe（无 npm shim 解析问题——比 dsh 的 `.cmd`→bin.js 解析坑少一层），但 PATH 找不到时的语义化降级要照抄 dsh 版「dsh not found」样式 | 低 | fail-closed 语义化错误（不 500·不静默） |
| P7 | **8600 未起的降级语义**：dsh 是静默退化纯问答，codex 若静默同样翻车 | 中 | `required=true` 快速失败 + 前端 error 卡显式告知（对齐诚实性红线） |
| P8 | **SDK 路线的供应链面**（若对冲启用）：0.0.0-dev + uv 构建链 | 低（条件触发） | 钉版 `==0.147.0` + requirements 登记 + 复刻清单注记双机安装命令 |

---

## 七 纠错清单（对计划书·共 6 条）

1. **C5 通道表述**：「`codex exec --json` 事件流解析」→ 改为「`codex app-server` JSON-RPC（stdio JSONL）主路」——exec 的 JSON 输出在官方 SDK 实现里挂 `--experimental-json` 实验旗标（K4），无稳定承诺；app-server 才是官方自建 UI 正路（K2）。
2. **C7 表述**：「brain-adapter-codex.js……open→Codex 子进程」→ 浏览器 JS **不能** spawn 子进程；子进程在 Python 后端，前端适配器 open 的是 **SSE 连接**（dsh 版同源结构：前端 fetch→后端 spawn）。
3. **D2 论据**：「锁 commit 的 schema 类型」官方已有现成机制（`generate-json-schema`·K5），无需自造；SDK「无版本可锁」也不精确——其 cli-bin 依赖已钉 0.147.0（K6）。
4. **C1 缺口**：stdio 选项未注明**每次冷启动含 ~15s 预热成本**（K10·源码 `_warmup()`）——该成本应在选型表中显式，进一步支持 HTTP 主选。
5. **计划缺 C0**：认证/安装前置（P1）——建议列入第一步之首。
6. **工期**：3-4 天 → 建议 **4-5 天**（+C0 认证 + app-server 握手调试 + SSE 链路 + schema 锁建仓）。

---

## 八 四档裁决（对三步走 C1-C12 + 红线）

| 批次 | 裁决 | 说明 |
|---|---|---|
| 第一步 C1-C4 | **吸收+修正** | 补 C0（认证）；C1 HTTP 主选+`required=true`+stdio 复刻模板；C2 明确两层 AGENTS.md 归属；C4 审批字段按 K1 落地写法给出 |
| 第二步 C5-C8 | **吸收+重写** | C5 通道换 app-server（本文 §五文件级拆解即为重写稿）；C6 映射表+未知事件容错；C7 改 SSE 消费表述；C8 白名单改动面已点名 |
| 第三步 C9-C12 | **吸收** | C9 契约符合性用 S6 wire 校验器桥式测法（现成）；C10 并入 §四-D6 三类自动量化；C11/C12 无异议 |
| 红线 1-6 | **接受** | 补第 7 条：认证密钥类资产不入仓（复刻清单只记步骤） |

---

> Qoder 组 · 2026-08-24 · PT-CB15 工程视角回应（源码实证版）·待 zcode 收敛定稿后按本文 §五 执行
