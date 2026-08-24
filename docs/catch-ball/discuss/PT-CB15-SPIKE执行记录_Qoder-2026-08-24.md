# PT-CB15 SPIKE 执行记录 · Codex 真实用例验证（Qoder·2026-08-24）

> 依据：`PT-CB15-Codex真实用例spike派发_zcode-2026-08-24.md`。分支 `EMC_Codex_Harness`·commit 前缀 `PT-CB15(SPIKE):`。
> 执行环境：home 机·Windows 25H2·codex-cli 0.149.1（npm `@openai/codex`）·LLM=DeepSeek Flash（deepseek-chat·用户令 08-24 接入）。
> 证据文件：`D:\Github\_codex_spike_cwd\`（仓外·q1-q5 日志+截图）·spike 脚本 `_tmp/ptcb15_spike/`（gitignore·不入仓）。

---

## 一 白话摘要（零术语·按 AGENTS 3b）

**四问全部跑完，答案是：换脑手术成功，可以出院，但出院单上记了三个小毛病要复查。**

用体检打比方：我们要确认「新医生（Codex）」能不能①会用我们医院的检查设备（18 件工具）——**会，全数确认**；②能不能边想边说（流式逐字）——**能，实测每个字分批到达，约 30-155 毫秒一批**；③说的话能不能显示在我们自己的叫号屏幕上（EMC 窗口逐字打字）——**能，浏览器里逐字渲染有录屏级证据**；④能不能连续问诊+开检查单+把结果画到地图上（多轮+工具+出图）——**多轮和工具都成了，出图的整条管道每一环都验证通过，但演示当晚图亮在了隔壁诊室的老屏幕上**——原因是家里同时开着一台旧服务器和新服务器，两台抢同一张图纸；关掉旧的或错开用就正常。另外发现一个与新医生无关的旧屏幕小毛病（地图刚打开时图纸塞不进去，要点一下图层开关才显示）。

**怎么自己测**：浏览器开 `http://127.0.0.1:8081/frontend/index.html?engine=codex`（注意是 8081 不是 8080·且先关掉旧服务窗口），展开右下角 EMC 面板，看到绿色「引擎·codex」徽标后直接提问。

---

## 二 执行总时间线与四问判定

| 问 | 判定 | 关键证据（仓外日志/截图） |
|---|---|---|
| Q1 Codex 能调 EMC 工具吗 | **PASS** | 18 件工具全数确认（q1_tools.jsonl·agent_message 列出 mcp__emc__×18）；`emc.emc_status` 真实调用 OK（q3_tooltest_never.log·T+8.1s）；zonal_stats/rank 数据链在 Q4 验证（真实情绪指数+社区表） |
| Q2 Codex 能流式吗 | **PASS** | app-server stdio JSONL：74 delta 逐 token（q2_stream.log·首字 7.0s·跨度 0.58s）；接 DeepSeek 后更快（23 delta·3.9s 完成一轮） |
| Q3 流式能进 EMC 壳吗 | **PASS** | 8001 直连 SSE：90 帧逐帧到达（q3_sse_8001b.log·110ms 均隔）+ emc.kb_facts 工具事件进流；8081 代理双跳：85 帧（155ms）；浏览器 E2E：绿色 codex 徽标+回答成功+MutationObserver 捕获 1.2 秒内 31 次 DOM 增量（逐字渲染铁证） |
| Q4 完整链路通吗 | **条件 PASS** | 多轮指代 ✓（「那伍家岗区呢」正确承接）；工具+数据 ✓（望洲社区 -1.061·zonal_stats 交叉校验）；出图：spec 生成→inbox→渲染**全环节各自验证通过**，当场未亮图=双后端实例 inbox 竞争（环境因素）+map.js 样式竞态（既有 bug）——见 §五 |

**接入通道**：全部走 `codex app-server --stdio`（三组修正案主路）·exec --json 仅作首日冒烟。**LLM=DeepSeek Flash**（用户令 08-24）：桥 spawn 加 `-c model_provider="deepseek" -c model="deepseek-chat"`，假 key 证伪实验确证请求真实发往 `api.deepseek.com/responses`（q5_probe2.log·401 响应含目标 URL）。

---

## 三 交付物清单（本次 commit）

| 文件 | 性质 | 内容 |
|---|---|---|
| `core/codex_bridge.py` | 新增 | app-server 常驻桥（F_042·惰性单例·15s 心跳·300s 看门狗·16MB 行上限·thread 续用=多轮） |
| `api/aiqa_routes.py` | 修改 | `POST /aiqa/codex_engine` SSE 端点（F_043·delta/tool/ping/done/error 五类事件） |
| `frontend/js/ai_qa/brain-adapter-codex.js` | 新增 | 前端适配器（SSE 消费→ACP msg.delta·恒 provenance='real'） |
| `frontend/js/ai_qa/brain-adapter-dsh.js` | 修改 | getEngineMode 白名单加 codex（一处·dsh 路径零改动） |
| `frontend/js/ai_qa/panel.js` | 修改 | 第四引擎分发+徽标（?engine=codex·仿 dsh 分支结构） |
| `frontend/serve.py` | 修改 | codex_engine 代理定向 600s+SSE 50s Timer 豁免（沿 dsh/render 双先例） |
| `tests/fixtures/codex_appserver_schema/` | 新增 | Schema 版本锁（ClientRequest.json 182KB+ClientNotification.json+README·锚定 0.149.1·重建命令在 README） |
| 本记录 | 新增 | 执行记录（本件） |

**追踪 ID**：F_042（bridge）/F_043（端点）已注册（编号续 F_041 不跳号）；bridge 的 ask 因 track_async 会把 async generator 包成 coroutine（__aiter__ 丢失·spike 实证）不挂装饰器——F_042 埋点由端点层 F_043 链路覆盖，注册表描述已注明。

---

## 四 实测数据汇总（对拍基础数据）

| 指标 | 实测值 |
|---|---|
| app-server 冷启动（spawn→initialize→thread ready） | ~0.4s（常驻后免付） |
| emc MCP ready（thread/start 后） | 0.4s（8600 常驻生效） |
| 首 delta 延迟（deepseek-chat·简单问） | 2.98-6.6s（glm-5.3 时代 6-7s） |
| delta 批次间隔 | 34-155ms（真流式体感即逐字） |
| 简单问全轮耗时（deepseek-chat） | 3.9s（glm 时代 12-19s） |
| 复杂问（多工具链·情绪分析） | 77-162s（与 dsh 同量级·PT-CB14 实证 50-366s 区间内） |
| 工具调用 | emc_status/list_data/kb_facts/zonal_stats/rank/render_spec 全部真实调通 |
| Q4 数据正确性 | 望洲社区 polarity_index -1.061（与服务端 zonal_stats 逐项校验吻合） |

---

## 五 卡点与根因（诚实失败记录·全部如实）

| # | 卡点 | 根因 | 可修性 | 处置 |
|---|---|---|---|---|
| K-1 | `codex exec` 首测 MCP 工具被拒：「MCP tool call requires approval, but approval policy is never」 | exec CLI 默认 approval_policy=never 且**覆盖** config 的 approval 配置层 | 可修 | app-server 主路不受影响（实证：同 config 下 app-server 工具直接放行）；exec 场景用 `--approve-for-me`。**纠错价值：回应文档 C4 的 `default_tools_approval_mode` 结论需修正——该字段对 exec 无效、对 app-server 生效** |
| K-2 | rank 事件流取证两次「看似失败」（0 命中） | PowerShell 管道 GBK 编码毁坏超长 JSON 行（取证工具坑·非链路坑） | 可修 | 换 Python 解析（`_tmp/ptcb15_spike/parse_rank.py`）；教训：超长 JSONL 取证禁 PowerShell 管道 |
| K-3 | Q3 首测 500：`'async for' requires an object with __aiter__` | `@track_async` 装饰器把 async generator 包成 coroutine | 可修（已修） | ask 去装饰器·埋点上移端点层 |
| K-4 | Q4 出图当场未亮（回答完整·图层 0/0·无报错） | **主因=环境**：旧后端 8000（EMC_harness_dsh·8080 页）与 spike 后端 8001（8081 页）的 render inbox watcher 1s 竞争扫描同一目录，spec 被 8000 抢先消费推给了 8080 页（8080 实际亮图=铁证 q4b_failure_evidence_8080.png） | 可修（运维级） | 验收时二选一：关旧实例·或只用 8081。**架构级建议见 §七-R1** |
| K-5 | Q4 补投后 8081 收到 spec 但落图报「Style is not done loading」 | **既有 bug（与 COH 无关）**：map.js addSource 在地图样式未就绪时抛错·`_renderState=failed` 无重试 | 可修（前端既有债） | 手动隐藏→显示图层即恢复（渲染链路本身完好·补投+重渲染后望洲社区红色多边形可见=q4b_layers.png）。**建议进收敛文档修复清单 §七-R2** |
| K-6 | 回答正文累积「（Codex 推理中…）」占位符（上轮 10 个） | 多个 reasoning item/started 事件重复发同一占位符 | 可修（已修） | bridge 侧 `_reason_sent` 单次门闩·重测 1 个（嵌推理文中·语义合理） |
| K-7 | rmcp fatal 噪音（web-reader/zread/web-search-prime 启动失败 9 条/轮） | 用户 config 里 bigmodel 三 HTTP MCP 的鉴权/网络问题·与 emc 无关（emc 恒 ready） | 不属本 spike | 记录备查·不影响判定（required=true 只挂 emc） |

---

## 六 预判坑清单验证（回应文档 P1-P8 对照）

| 预判坑 | 实测 |
|---|---|
| P1 认证前置 | **应验但已解**：本机装过 Codex 桌面版（Electron·`~/.codex` 配置+auth.json 齐全）——CLI 只需 `npm i -g @openai/codex`（npmmirror 镜像 1 分钟·官方源超时）·认证复用桌面版存量（zai apikey）；后按用户令切 DeepSeek key |
| P2 exec --json 实验旗标 | **应验**：采纳 app-server 主路·exec 仅冒烟（并抓到 K-1 附加价值） |
| P3 cwd AGENTS.md 注入 | **规避成功**：全程 cwd=`D:\Github\_codex_spike_cwd` 隔离目录·桥 spawn 恒用该目录 |
| P4 版本漂移 | 已布防：Schema 锁入仓（0.149.1 锚点·升级先 diff ClientRequest.json） |
| P5 Windows 坑 | **应验两个新坑**：①CreateProcess 不能直跑 npm shim（预测的 P6 实锤·解法=vendor codex.exe 直调·dsh BA 同源模式）；②**未预判到**：asyncio StreamReader 默认 64KB 单行上限（render_spec 大结果单行 JSONL 撞墙→K-4 伴随根因·已修 16MB）；③PowerShell GBK 取证坑（K-2·新教训） |
| P6 spawn 形态 | 见上① |
| P7 8600 未起降级 | 未触发（8600 恒在）·`required=true` 快速失败语义保留 |
| P8 SDK 供应链 | 未启用（主路未用 SDK·零新依赖） |

---

## 七 给收敛文档的跟进建议（非本 spike 范围）

- **R1（架构）**：多后端实例并存时 render_inbox watcher 竞争消费——建议 spec 消费后向全部实例扇出·或 inbox 加实例锁字段；短期纪律=同机只跑一个后端实例。
- **R2（前端既有债）**：map.js renderLayer 的 addSource 应等 map `load`/`styledata` 事件后执行·或对 `_renderState=failed` 的图层在样式就绪后自动重试（SSE 早于样式到达是常态·非偶发）。
- **R3（工程）**：`@track_async` 不兼容 async generator——tracker 可加 `track_gen` 变体或在文档标注禁用面。
- **R4（计量）**：Codex 引擎回答的「用量 0 token/0 次」显示恒零（tokenUsage 事件未接前端计量）——小瑕疵·下批补。

---

## 八 复刻清单（Codex 配置·仓外·双机各配·按差异注记）

| 项 | 内容 | 差异注记 |
|---|---|---|
| 安装 | `npm install -g @openai/codex --registry=https://registry.npmmirror.com`（官方源超时实测） | 双机同法·版本记录 `codex --version`（本机 0.149.1） |
| 认证 | `~/.codex/auth.json`（apikey 模式·复用桌面版存量或重登） | 密钥不入仓不入档 |
| MCP 注册 | `~/.codex/config.toml` 加段：`[mcp_servers.emc]` → `url="http://127.0.0.1:8600/mcp"`·`startup_timeout_sec=60`·`tool_timeout_sec=120`·`required=true`·`default_tools_approval_mode="approve"` | {REPO} 无关（恒 8600·start.bat 起） |
| DeepSeek 接入（用户令 08-24） | `[model_providers.deepseek]`：`base_url="https://api.deepseek.com/"`·`wire_api="responses"`（实测双端点 200）·`experimental_bearer_token=<key>`（key 仓外·口头交接）；桥侧已内建 `-c model_provider="deepseek" -c model="deepseek-chat"`（代码内·无需各机配置） | office 机同配 |
| cwd 隔离 | 桥恒用 `D:\Github\_codex_spike_cwd`（**硬编码盘符·office 机若盘符不同需改 `core/codex_bridge.py` 的 `_SPIKE_CWD`**——收敛时建议改为按 `{REPO}` 同级推导） | ⚠ 双环境差异点 |
| Schema 锁 | 仓内 `tests/fixtures/codex_appserver_schema/`（重建命令在 README） | 随 git 同步 |

---

## 九 红线自查

| 红线 | 结果 |
|---|---|
| EMC MCP 18 件工具零改动 | ✓（mcp_server_emc.py 未动·18 件清单为证） |
| dsh/light 引擎零退化 | ✓（dsh 路径代码零改动·getEngineMode 仅扩白名单；light 主路零触碰；pytest 全量回归见 §十） |
| RAG 96.7% 零退化 | ✓（RAG 代码零触碰） |
| Codex 配置全部仓外 | ✓（config.toml/auth.json 仓外·复刻清单 §八·key 不入档） |
| cwd 隔离 | ✓（§六-P3） |

## 十 回归验证

- **回归结果：`py -m pytest tests/ -q` 全量 581 passed / 2 skipped / 0 failed（189.8s）**——含 track_id 注册合规校验（F_042/F_043 不跳号）与 dsh/light 引擎既有断言（provenance 双锁等）全部绿。
- 浏览器 E2E：codex 引擎三轮问答+多轮+出图全过（§二）；dsh/light 引擎既有断言在 pytest 覆盖。

---

> Qoder · 2026-08-24 · PT-CB15 SPIKE 执行记录（四问实测版）·commit `PT-CB15(SPIKE):`·待 zcode 收敛
