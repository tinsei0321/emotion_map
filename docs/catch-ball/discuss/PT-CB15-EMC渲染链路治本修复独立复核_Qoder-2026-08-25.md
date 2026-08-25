# PT-CB15 · EMC 渲染链路治本修复独立复核（Qoder·2026-08-25）

> 复核对象：`PT-CB15-EMC渲染残留与后台幽灵图层根因报告_Codex-2026-08-25.md`
> 方法：不采信报告结论，对四条链路（SSE 通道 / MCP 写入端 / codex_bridge / 前端消费端）逐一读码取证，全部结论附文件行号。

## 白话摘要

把地图出图想象成「餐厅上菜」：Codex 是厨师，地图页面是餐桌，中间有个传菜员（后台监视线程）。这次查出一个 Codex 没发现的更深层问题——**客人喊停之后，厨师其实还在后厨继续炒**。现在的代码里，「停止」只停了传菜，没停厨师：点了停止或超时后，厨师会把炒了一半的旧菜悄悄端上来，顶掉你面前正在吃的新菜。这就是「文字都结束了，旧图突然冒回来」的真正源头。修法分两步：①喊停时同时叫停厨师（协议本身支持，改一个文件就够）；②给每道菜贴上「这是哪一单点的」标签，传菜员和餐桌都只认当前那一单，贴错标签的菜直接拒收。另外三件小事：模型拿「历史成品菜」（TOP10 那份）冒充「本单现炒的 TOP7」——不硬禁（有时客人就是要成品），改为菜单上写清楚 + 上错菜时服务员提醒一句；控制台那条红色报错（时间清单文件不存在）改为一次性灰色提示，不补假文件（补了会掩盖「清单从未生成」这个事实）；最后给三个服务（网页/接口/工具箱）加一张启动对账单，防止各跑各的版本或目录对不上。

## 一、独立复核结论（逐问）

### 问 1：render_spec 应否绑定 turn_id？——**应绑定，但它是第二道防线；第一道防线 Codex 没发现**

**复核发现的更上游根因**：`core/codex_bridge.py` 的 `ask()` 在超时（L227-231、L247-251）、进程 EOF（L238-244）、客户端断开（generator 被 cancel）等所有收口路径，**只 return，从不调 app-server 协议的 `turn/interrupt`**——该协议方法真实存在（`tests/fixtures/codex_appserver_schema/ClientRequest.json` L6843 `turn/interrupt`，参数 threadId+turnId）。后果链：

1. 前端 abort/超时 → SSE 断 → 后端 `ask()` 收口 → `async with self._lock`（L207）释放；
2. 但 app-server 的 turn **继续在后台跑**，继续调 MCP render_spec 写收件箱；
3. 若用户已发下一问，新 `turn/start` 排队（app-server 单进程串行·模块头 L24 注释自证）——旧 turn 的完成事件与新 turn 交错；
4. 旧 turn 延迟写 spec → watcher 1 秒内扫描（`api/render_routes.py` L211-235）→ SSE 广播（`_publish` L198）→ 前端 `_clearDshLayers()` 清掉当前正确图层、铺上旧图（`frontend/js/render_client.js` L82-95、L117）＝「EMC 文本已结束，旧图层突然推回」。

**通道层证实 Codex 判断**：spec 结构（`tools/mcp_server_emc.py` L1568-1577）无任何轮次字段；watcher 全局广播；前端 `_seenSpecIds` 仅防同 spec 重复（L13、L181），无轮次概念——跨轮 spec 全数接受。

**治本方案（两层）**：
- **第一层（源头·P0）：`ask()` 全部非正常收口路径发 `turn/interrupt`**（fire-and-forget，best-effort，失败仅 log）。正常 `turn/completed`（L286）无需。这是治本——不做这层，旧 turn 依旧在后台烧 token 写盘，turn_id 过滤只是把幽灵挡在门外，源头还在生产幽灵。
- **第二层（通道·P1）：spec 加 `turn_ref` 软标记 + 前端过滤**。链路：前端复用**已有的** `acp-channel.js` turn_id（L29 `turn-<ts>-<seq>`，零新增标识体系）→ 随 question POST `/aiqa/codex_engine` → 后端作为指令行前缀注入（`[render_ctx] turn_ref=…·调 render_spec 时原样传入`）→ `render_spec` 增 `turn_ref` 参数写入 spec → render_client 与「当前 turn_id」比对。**过滤规则必须宽松**：spec 带 turn_ref 且≠当前 → 拒；不带 turn_ref → 照常渲染（兼容 dsh 桌面/脚本等合法生产者）。abort 语义：panel 已有 settled 概念（L1822），abort 时广播「当前 turn 失效」，后续同 turn_ref 的 spec 也拒——用户喊停就一停到底。
- 模块解耦：render_client 经 document CustomEvent（如 `turn:current`）订阅 panel 的轮次状态，不改 panel 既有 API。

### 问 2：出图数据源收敛——**引导+清单治理+软警示；不做硬禁**

取证：`page7_12345_top10` 实测 `usage=analysis_output`（manifest 61 条中 19 条 analysis_output·含 5 条 `tmp_render_*` 历史残留，个别 note 源指向已退休的 `DATA\boundaries`）。正路已存在：`rank/zonal_stats` 的 `layer_output=True` 返回 geojson（`mcp_server_emc.py` L598、L693）→ render_spec inline（契约 §三-①，TOP7 ≤60 完全够）。

我的意见（四件套，见分歧点 4）：
1. **render_spec docstring** 加硬指引：分析结论类出图（Top-N/排名/聚合）必须传本轮工具返回的 geojson；dataset_id 仅限「展示该数据集本身」的直陈诉求——名字相近的历史 preset ≠ 本轮答案（TOP7≠TOP10≠174 全量）。
2. **list_data 的 render.paradigm 段**（L436-446）同步同一句——list_data 是模型出图前必查入口。
3. **docs/render-contract.md §三** 加「档位选择须与问题一致」条款（文档权威面）。
4. **清单治理**：`tmp_render_*` 组不进 list_data 输出（过滤菜单可见性，不动 render_file 的 `_find_tmp_dataset` 复用逻辑）；**render_spec 返回值软警示**：dataset 引用且 usage=analysis_output 时附 hint「静态历史产物·请核对与本轮问题的 Top-N/口径一致·建议改传本轮 geojson」——不拒绝，一次往返给模型自纠机会。

### 问 3：_time_manifest.json——**前端分级降级；不补空 manifest**

`frontend/js/time-source.js` L20-22 注释自证缺口成因与「再生成属数据红线（留用户）」的既定决策；main.js L330 `.catch(()=>{})` 已静默功能降级，唯一害处是 console.error 红字（L37）+ E2E 归因负担（`tests/browser/s3_acp_event_e2e.py` L51-58 专门归类）。

修法：catch 区分 **404（未配置 → 一次性 console.info「时间轴清单未配置·时间过滤休眠」）** 与真实错误（网络/5xx → 保留 error）。同时把「manifest 待生成·责任=性能数据导出管道」登记进 `DATA/README.md`——缺口要**可追溯**，不是**被掩盖**。补空 manifest 会让 404 变 200，将来时间轴启用时没人知道 manifest 从未真实生成，且与「数据红线」注释冲突。

### 问 4：统一自检——**应做，轻量三件，不建监控工程**

已有：/api/v1/version + 前端徽章 30s 复检（render_client L199-260）、watcher pidfile 竞争锁、emc_status 探活、start.bat 的 8600 轮询。缺口三项：
1. **SSE 首帧 hello（最值得做）**：`_sse_stream` 连接时先发 `event: hello`（data 含 server_startup/applied_count）再进循环。前端记录 hello 时戳——**任何先于 hello 到达的 spec 帧 = backlog 重放回归**（hello 必是第一帧），拒染 + console.error。这把「连接不重放」从代码约定升级为运行时可验证的协议不变量，改动约 8 行。
2. **三服务对账**：/version 扩展（或 /selfcheck）：inbox 可写 + watcher 锁状态 + 探 8600 可达 + **repo_root 比对**（emc_status 小扩展返回 repo_root——MCP 与 API 若从不同 checkout 跑，render_inbox 写错目录，图永远不出现的静默失败即被点亮）。mismatch → stderr WARN 一行 + 端点返回标记，前端并入徽章 title，不新开 UI。
3. **顺带清死代码**：`render_routes.py` 的 `_BACKLOG` 已只写不读（L45-48、L147-148；`_sse_stream` L243 已不消费），模块头 L7 与 `render_stream` docstring L259 仍写「先补 backlog」——注释与实现相反，会误导下一位维护者以为有重放。删 `_BACKLOG` + 改两处注释。

## 二、与 Codex 的分歧点

| # | Codex 方案 | Qoder 意见 | 理由 |
|---|---|---|---|
| 1 | 问 1 提议「在 AGENTS.md / tool_contracts 中约束 render_spec」 | **AGENTS.md 路径无效；tool_contracts.py 非其契约面** | codex_bridge P2-2（L44-47）特意把 cwd 隔离到仓外 `_codex_cwd` 防本仓 AGENTS.md 注入——**Codex 根本读不到 AGENTS.md**；render_spec 不在 ai_qa/tool_contracts.py（实测 0 命中），其契约三处 = render_spec docstring / list_data.render 段 / docs/render-contract.md |
| 2 | 幽灵图层归因「watcher 延迟推送的竞态」（通道层） | **更上游根因 = bridge 从不 turn/interrupt**（生命周期层） | 只做 turn_id 过滤是治标：旧 turn 仍后台跑完写盘烧 token；interrupt 才断源头。两层都要，优先级 interrupt > turn_ref |
| 3 | 问 3 倾向「补最小 manifest **或**优雅降级」二选一 | **明确选降级，不补空 manifest** | 空 manifest 掩盖「从未生成」事实、与 time-source.js 数据红线注释冲突（口径归用户/数据管道定，代码不代编） |
| 4 | 问 1 倾向「禁止随手挑 page7_*/tmp_render_*」（约束更死） | **不硬禁，引导+清单治理+软警示** | 硬禁误伤合法场景（用户直陈「把 TOP10 那层显示出来」）；「图与问题一致」是语义判断，只能在模型可见的契约文本层引导，工具层无法判定 |

## 三、最终建议（按优先级）

| 级 | 项 | 改动面 | 效果 |
|---|---|---|---|
| **P0-A** | codex_bridge 全收口路径发 `turn/interrupt` | `core/codex_bridge.py` 单文件（需在 turn/start 时记录返回的 turnId 供 interrupt 用） | 幽灵源头根治：turn 收口后 app-server 停跑，不再延迟写盘 |
| **P0-B** | SSE 首帧 hello + 前端拒染 hello 前 spec | `api/render_routes.py` + `frontend/js/render_client.js` 约 8 行 | 「不重放」变协议不变量，回归即告警；顺带删 `_BACKLOG` 死代码与过时注释 |
| **P1-A** | turn_ref 全链（前端 turn_id→端点注入→render_spec 参数→前端过滤·宽松规则） | 4 文件小改 | 软防线双保险；abort 语义一致（停就全停） |
| **P1-B** | 出图数据源四件套 + analysis_output 引用软警示 + tmp_render_* 不进 list_data | `tools/mcp_server_emc.py` + `docs/render-contract.md` | TOP7 答对图；清单不再诱导随手挑 |
| **P2-A** | time-source 404 分级降级 + DATA/README.md 登记缺口 | `frontend/js/time-source.js` 一处 | 控制台干净，缺口可追溯 |
| **P2-B** | /version 扩展自检（inbox/锁/8600/repo 比对·emc_status 增 repo_root） | `api/render_routes.py` + `tools/mcp_server_emc.py` | 跨服务错位静默失败被点亮 |

**登记项（本轮不修·留 CB 追踪）**：① dsh 引擎 Q4v3 超时重试的旧尝试副作用（`api/aiqa_routes.py` L150-158「出图副作用与响应解耦」注释自证——首试超时已写盘的 spec 与重试结果并存；EMC 默认 Codex 后低优先）；② 旧 turn 的 delta/tool 事件与新 ask 的 readline 串流风险（共享 stdout 单管道·bridge L225——未实证，建议 interrupt 落地后回归验证）。

## 四、验证口径（实施后必测）

1. 问 A 出图中途中止 → 立即问 B → B 文本结束后 60s 内不出现 A 的图层（P0-A 验证）。
2. 硬刷新 ×3 → 无任何历史 [dsh] 图层复活；人为恢复 backlog 重放代码 → 前端拒染告警（P0-B 验证）。
3. 「最差的 7 个社区」→ 图层要素数 = 7（非 10/非 174），且 origin.source_tool 为本轮 rank/zonal（P1-B 验证）。
4. 控制台零 `_time_manifest` 红字，仅一条 info（P2-A 验证）。
5. kill 8600 后 selfcheck → 徽章 title 可见 mismatch/不可达标记（P2-B 验证）。
