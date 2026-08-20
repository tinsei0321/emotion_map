# PT-CB6 · home 续点恢复 · 审计报告（审计协助 · 2026-08-21）

> 审计执行：Qoder 审计组（用户调度下承接送审通知指定的 Codex 审计席位；文件名按送审通知交付要求保持）。
> 送审方：zcode（主手）。性质：home 到岗续点完工送审（dsh rc.8 更新 + synapse 删除 + EMC 入口插件重建 + 黑屏修复 + Codex 配置修复）。
> 纪律遵守：全程零实施——只读文件、只读 git 命令、对本机 3080 的只读 GET；未改任何代码/配置/进程。EMC 仓仅新增本报告一个文件。
> 环境核对：`EMC_harness_dsh` 分支已 pull（Already up to date，本地 ahead 2 = 纯文档提交，见 N2）；main 未动。

## 〇 总体结论

**无 CRITICAL。** 六项审计要点：2 项 AGREE、3 项 PARTIAL、0 项 DISAGREE（synapse 项按"彻底性"口径判 PARTIAL）。
黑屏双根因判定成立、探测纪律完整保持、构建链 stub 方案成立。主要待修集中在：**欢迎卡全局可见性（D2）、startSession 返回误用死代码（D1）、Edge 未显式指定且 URL openPath 链路未验证（D3）、synapse 在 lock/workspace 两文件残留（M1）**——均为 MEDIUM，等主手裁定后排修。浏览器点击链路（T4 四项）仍待主手实测，本报告不能替代。

## 一 逐条审计（按送审通知 §二 六项）

### 1. 重建忠实度 —— PARTIAL

对照 `PT-CB6-EMC入口重定义任务书_Codex-2026-08-20.md` 需求 1/2 逐项：

| 规格项 | 判定 | 证据 |
|---|---|---|
| 欢迎卡文案逐字（含换行） | ✅ 一致 | `D:/Github/dsh-emc-entry/src/client/components.tsx:88-90`：标题「你好，我是 EmotionMap Copilot」+ 正文「用情绪地图看懂市民心声——问区域情绪、做空间分析、追原因与建议。」，全角破折号与两段结构（=换行）均保留；实测当前构建 `lib/client.js` 亦含该文案 |
| 点击=新建会话（standard 预设），空白会话可复用 | ✅ 语义等价 | 插件 `src/client/index.ts:57` 调 `ctx.workspaces.startSession()`；rc.8 源码 `D:/Github/dsh/packages/client/runtime/src/client/workspaces/service.ts:177-202` 注释明示其为「the shared New Session action behind the shell entry points (sidebar button...)」——即与 dsh 原生「新建会话」按钮**同一函数**，精确满足任务书需求 1 语义澄清「与 dsh 原生『新建会话』按钮同语义」；预设经 `connectWorkspace` 走 host 默认（standard） |
| 不再走内嵌浏览器 | ✅ 落实 | 插件全量源码（index.ts/components.tsx）无 betterSidebar/openTab 任何引用；启动链统一 `openPath` |
| `start.bat --open=none` 依赖在位 | ✅ 在位 | EMC 仓 `start.bat:35` = `py frontend/serve.py 8080 --open=none`；`frontend/serve.py:568-571` 支持该参数 |
| 零硬编码 hex（token 纪律） | ✅ | `src/client/index.ts:72-125` STYLES 全部走 `var(--dsw-alias-*)`，svg 用 currentColor，零 hex |
| 插槽名真实存在（不得猜） | ✅ | `sidebar.footer.action`（`ui-sidebar/src/client/contract/slots.ts:46`，owner 提供 `wide: boolean` 与组件 `EmcLaunchAction({wide})` 匹配）；`conversation.input.dock`（`ui-conversation/src/client/contract/slots.ts:195`，契约注释明示「anything needing its own line above the card belongs in conversation.input.dock」=composer 上方，与执行记录口径一致） |

**偏差（3 项 MEDIUM + 3 项 LOW）：**

- **D1（MEDIUM）startSession 返回值误用（死代码）**：插件 `src/client/index.ts:57-58` 写 `const sessionId = await ctx.workspaces.startSession(); if (sessionId !== undefined) ctx.sessions.open(sessionId)`。但 rc.8 契约 `packages/client/runtime/src/client/contract/workspaces.ts:30` 与实现 `service.ts:187` 均为 `startSession(workspaceId?): void`——**无返回值**。该分支恒不执行（导航由 startSession 内部完成），功能无害但暴露 API 误读，且 `inject` 中的 `'sessions'` 服务因此仅被死代码使用。建议：删掉两行死代码，`void ctx.workspaces.startSession()` 即可。
- **D2（MEDIUM）欢迎卡全局可见，非仅新会话**：可见性由模块级全局 `welcomeShown`（`components.tsx:33-38`）驱动，而插槽是 session scope。后果：**点击按钮后欢迎卡会出现在所有会话**（含已打开的其他会话），直到用户点「知道了」；再次点击入口也会重新弹出。任务书要求是「该（新）会话内自动出现并展开」。建议：把可见性绑定到 startSession 目标 sessionId（或仅在无消息的空会话渲染）。此项已部分被 zcode 执行记录 §七「欢迎卡新会话自动出现细节若未达标…重建」预判，审计确认该细节**未达标**。
- **D3（MEDIUM）Edge 未显式指定 + URL openPath 链路未验证**：任务书需求 2 要求「外部浏览器 Microsoft Edge」且「避免开错浏览器」。实际链路 = `openPath(URL)` → host api-proxy（`api-proxy.ts:1847-1852`）→ `openNativePath` → Windows 分支 `native-path-opener.ts:101-107` = `powershell.exe Invoke-Item -LiteralPath '<URL>'`，即 **OS 默认浏览器**，不锁定 Edge（当前 home 默认浏览器恰为 Edge 时行为等价，属环境巧合而非实现保证）。另两点需 T4 实测确认：① dsh 仓全仓无 `openPath(http...)` 先例，`Invoke-Item` 对 URL 参数的 ShellExecute 行为未经验证；② Windows 分支的 `openInBrowser`（`native-path-opener.ts:75-77`）明确「names no browser without reading the UserChoice registry」直接返回 false。
- **D4（LOW·架构偏离已说明）**：未采用任务书 §二 的 host 侧 `harness.handle('emc.launch')` 设计，改为纯 client + `openPath`（node 半空壳 `src/index.ts`）。属「先查真实接口」纪律下的等价替代，R13（不直接 spawn）支撑该取舍，执行记录 §三有记载——判可接受，但任务书原设计的「host 显式开 Edge」能力恰是 D3 的解法之一，修复 D3 时可一并考虑。
- **D5（LOW）**：`src/client/index.ts:64-65` 忽略 `waitForEmc()` 返回值——8080 若 10s 未就绪仍照开浏览器，用户见连接错误页。建议 false 时改为提示。
- **D6（LOW·存量非本轮）**：`start.bat:6` 与 `:25` banner 仍写「auto-opens MAIN + TEST pages / auto-opens browser when ready」，与 `--open=none` 现状不符（上一轮 1 行改动未同步 banner 文案，终端输出会误导用户以为会自动开页）。

### 2. 探测纪律 —— AGREE

问题 C 修复口径完整保持，逐项对照复盘 §二问题 C「修复方向 1 + 注意点」：

| 口径 | 判定 | 证据 |
|---|---|---|
| `mode:'no-cors'` | ✅ | `src/client/index.ts:37` |
| resolve=可达 / reject=不可达 | ✅ | `.then(() => true).catch(() => false)`（index.ts:38-39） |
| 不读 `res.status` | ✅ | 全文件无 status 读取 |
| 2s 超时 | ✅ | `PROBE_TIMEOUT_MS = 2000`（index.ts:30）+ AbortController（35-36） |
| 60s 节流 | ✅ | `PROBE_INTERVAL_MS = 60_000`（index.ts:32）+ setInterval（144）+ effect disposer 清理（145） |

与执行记录 §三 R3 口径一致。初始 `up = true`（components.tsx:18）配合 apply 时立即首探（index.ts:143），窗口极短，且点击时 launch 链自带 start.bat 启动兜底——不构成问题。

### 3. 黑屏双根因判定 —— AGREE（未发现第三根因证据）

- **根因 A（缺 `export const inject`）成立**：蓝本核实——`D:/Github/dsh/packages/client/ui-task-board/src/client/index.ts:60` 确为 `export const inject = ['slots', 'remote', ...]` 模式；新插件已在 `src/client/index.ts:19` 补齐 `export const inject = ['slots', 'sessions', 'workspaces']`，与实际使用服务匹配。cordis 未声明服务即取用 → 启动树崩溃的机理与「黑屏」现象自洽。
- **根因 B（merge 后未跑 build:web → assets 版本错配）成立**：实测 `D:/Github/dsh/apps/web/dist/assets/index-BNmIpCDW.js` mtime = 2026-08-20 21:03:44（rc.8 新构建，与执行记录 build:web 时间点吻合），修复前为 08-18 rc.7 旧构建——时间线自洽。
- **第三根因排查（审计组主动做）**：① 两个插槽契约在 rc.8 均存在且语义匹配（见审计项 1 表）；② workspaces/sessions 契约逐项对照，唯一错配是 D1 死代码（不致黑屏）；③ 实测当前 3080 页面 200、预加载清单含 emc-entry、DOM 正常服务。**未发现第三根因证据**。
- 保留意见：根因 A 的最终闭环（点击链路下不再崩）仍依赖 T4 浏览器实测。

### 4. rc.8 构建链 stub —— AGREE（含 LOW 残留风险）

- **机制核实**：`D:/Github/dsh/packages/client/tsdown.client.ts:358-369` `workspaceManifest()` 确实 `globSync('packages/*/*/package.json')` 按 name 查找、查不到即 throw——「插件名必须在 workspace 清单注册」的约束属实，stub 是满足该约束的最小方案。
- **stub 实现核验**：`D:/Github/dsh/packages/emc/emc-entry/package.json`（name=`dsh-emc-entry`、零代码、`dsh.client` 声明）+ `tsdown.config.ts`（`export default { entry: '' }` 跳过构建）；commit `ec5c5e725c` 仅 3 文件（stub 两件 + pnpm-lock 2 行），无夹带。
- **不污染 workspace 构建/运行**：stub 未进任何 profile bundles；实测 `/plugins/dsh-emc-entry/client.js` 服务的是 profile junction 指向的真实插件（7797B，含全部特征），与 stub 无冲突。
- **vs `dsh plugin add` 正式包**：正式包需发布/仓内托管源码，对「仓外私有插件」过重；stub 方案更优，判定同意。
- **残留风险（LOW）**：① 本地 fork 占用 `packages/emc/` 域名，上游未来同名会冲突（merge 时需留意）；② stub 与仓外真包同名 `dsh-emc-entry`，pnpm 工具链（publish/why）可能混淆。建议 stub 描述字段已注明用途（✅ 已做），保持现状即可。

### 5. synapse 删除彻底性 —— PARTIAL（发现残留，彻底性宣称不成立）

已删部分全部核实通过：

| 位置 | 判定 | 证据 |
|---|---|---|
| web profile package.json（dependencies + bundles） | ✅ 干净 | 实测全文无 synapse；`dsh-emc-entry` 登记在位 |
| node_modules/dsh-synapse 目录 | ✅ 已删 | Test-Path = False |
| ~/.dsh/synapse 数据目录 | ✅ 已删 | Test-Path = False |
| emc-test / emc-test-headless profile | ✅ 无引用 | 两 package.json grep 零命中 |
| 页面预加载清单 | ✅ 无 synapse | 实测 GET 3080 首页内容 synapse 命中数 = 0 |
| 回滚能力 | ✅ | 备份 `package.json.bak-rm-synapse` 在位 |

**残留（M1·MEDIUM）**——「web profile 之外无残留引用」的宣称不成立：

- `C:/Users/Hi/.dsh/profiles/web/pnpm-lock.yaml`：L65-67（importer 的 dsh-synapse specifier/version 条目）、L344-345（packages 段 tarball 条目）、L713（snapshot 条目），共 3 处；
- `C:/Users/Hi/.dsh/profiles/web/pnpm-workspace.yaml:8`：`allowBuilds` 仍有 `dsh-synapse@…: true`。

影响评估：package.json 已无该依赖 → 运行时不安装/不加载，**当前无功能影响**；下次 `pnpm install` 会自动修剪 lock 条目。但执行记录「4 处删除」台账遗漏这两文件，彻底性口径应降级。修复建议：一次 `pnpm install`（自动清 lock）+ 手删 workspace.yaml 的 allowBuilds 行（或等主手排期，零实施组不动手）。
连带影响核查：`~/.dsh/sessions`（3 个会话目录）与 synapse 数据目录完全独立，删除无连带。

### 6. Codex 接入配置 —— PARTIAL（方向正确，两处口径不准确）

- **`wire_api = "responses"` ✅ 正确**：Codex 已于 2026-02 移除 `chat` 取值（openai/codex discussion #7782，与执行记录引用一致），`responses` 现为唯一合法值（多源交叉：OfoxAI/segmentfault/腾讯云教程同口径）。`config.toml` `[model_providers.deepseek]` 现为 responses ✓，备份 `config.toml.bak-20260820` 在位 ✓。
- **DeepSeek Responses API 文档核对 ✅**：官方文档（api-docs.deepseek.com/zh-cn/guides/responses_api/）确认 base_url = `https://api.deepseek.com`、为 Codex 需求原生提供 Responses 端点、V4-Flash 于 2026-07-31 GA 时上线（与执行记录日期口径一致）、v4-pro 于 8 月初补齐——config 默认模型 `deepseek-v4-flash` 走 responses 成立；models.json 中 v4-pro 也在 8 月后可用 responses，配置无错。
- **`supports_search_tool = false` ✅ 已落实**：models.json 两个 deepseek 模型（L65 / L132）均为 false。方向保守安全。备注：DeepSeek Responses 实际提供服务端 `web_search_call` 事件（官方事件列表），置 false = 不启用服务端搜索，属功能裁剪而非错误。
- **不准确 1（LOW）**：执行记录称「Codex 0.145.0」，实测本机为 **codex-cli 0.148.0-alpha.21**。
- **不准确 2（LOW）**：「该字段 true 会静默隐藏所有 MCP 工具（0.145.0 bug）」——公开渠道未检索到可佐证材料，属不可外部证伪的断言；配置本身无害，但建议 debug-memory 记录时标注「现场观察，未获上游确认」。
- **claude 侧同步检查（送审通知 §二.6 附问）**：`[shell_environment_policy.set]` 的 `ANTHROPIC_BASE_URL = https://api.deepseek.com/anthropic` 指向 DeepSeek Anthropic 兼容端点——与 2026-08-12「Responses 与 Anthropic 兼容同时上线」的公开报道结构一致，未见需要同步修改之处。（安全注记：config.toml 含明文 API token，属本机配置常态；本报告不复制任何 token，各组分发时注意。）

## 二 附加发现（非六项范围，顺带核验）

- **N1（LOW）执行记录数字过期**：记录 §三/§六 称 client.js **7639B**；实测当前本地构建、profile junction、3080 服务端三者一致均为 **7797B**（lib 构建 2026-08-20 21:03:11，晚于 src 最后修改 21:03:09）。推断：记录验证针对较早一次构建，其后又重建过一次。当前「磁盘=junction=服务」三者一致且特征齐全（no-cors/startSession/欢迎卡文案 grep 命中），**无实质风险**，仅台账数字未回写。
- **N2（INFO）EMC 仓纪律遵守**：ahead-2 提交（facf96f4 / f1af435e）diff 仅 5 个文档文件（HOME 交接卡/执行记录/送审通知/debug-memory R13/session-handoff），「本轮 EMC 仓零触碰生产代码」宣称属实。
- **N3（INFO）dsh 未 push 状态**：实测 master ahead 539 / behind 1，与记录一致；提醒 behind 1 需 `pull --rebase` 处理后再 push。
- **N4（INFO）debug-memory R13**：三条坑（stub 登记 / inject 导出 / build:web）与本次审计独立核验结论全部吻合，质量合格；记录中提到的两个 R11 撞号仍待合并（zcode 遗留 §七已列）。

## 三 待修清单（分级）

> 零 CRITICAL / 零 HIGH。MEDIUM 四项等主手裁定排期；LOW 可并入既有批次。

| # | 级别 | 项 | 建议修复 | 归属 |
|---|---|---|---|---|
| F1 | MEDIUM | D2 欢迎卡全局可见（所有会话均显示，非仅新会话） | `components.tsx` 可见性绑定目标 sessionId（或仅空会话渲染） | 插件仓 dsh-emc-entry |
| F2 | MEDIUM | D3 Edge 未锁定 + `openPath(URL)`→`Invoke-Item` 行为未验证 | 先由主手 T4 实测确认 URL 能否打开；若需锁定 Edge，回到 host 侧显式启动（任务书原 `emc.launch` 设计）或接受「默认浏览器」口径并在任务书侧销案 | 插件仓（+任务书口径裁定） |
| F3 | MEDIUM | D1 `startSession()` 返回误用死代码 | 删 index.ts:57-58 死代码，`void ctx.workspaces.startSession()`；`inject` 中 `'sessions'` 随之评估去留 | 插件仓 dsh-emc-entry |
| F4 | MEDIUM | M1 synapse 在 pnpm-lock.yaml（3 处）与 pnpm-workspace.yaml（allowBuilds 1 处）残留；执行记录彻底性宣称需修正 | profile 目录跑一次 `pnpm install` 修剪 lock + 手删 allowBuilds 行；执行记录/台账补记 | ~/.dsh/profiles/web |
| F5 | LOW | 记录口径：Codex 版本 0.145.0→实测 0.148.0-alpha.21；client.js 7639B→7797B | 台账回写正确数字 | 文档 |
| F6 | LOW | `supports_search_tool` bug 断言不可外部证伪 | debug-memory 标注「现场观察」 | 文档 |
| F7 | LOW | D5 waitForEmc 返回值忽略（8080 未就绪仍开浏览器） | false 分支改为置灰/提示 | 插件仓 |
| F8 | LOW | D6 start.bat banner 文案过期（仍称自动开页） | 2 行 echo 更新（需 EMC 仓授权） | EMC 仓 start.bat |
| F9 | LOW | stub 同名/上游撞名风险 | 无需动作；未来上游 merge 冲突时留意 packages/emc/ | 备忘 |
| — | 待办 | T4 浏览器点击链路四项验收 | 主手实测（新会话+欢迎卡 / 终端 start.bat / Edge 开图 / 置灰提示），同时闭环 F2 的验证需求 | 主手 |

## 四 审计方法与证据边界声明

- 证据类型：源码 file:line（EMC 仓 / dsh 仓 / 插件仓）、文件系统实测（Test-Path/mtime/尺寸）、本机 3080 只读 GET（client.js 200·7797B / 首页 synapse 0 命中）、git 历史核验、公开文档交叉检索（Codex wire_api 口径 / DeepSeek Responses 官方文档）。
- 未做（零实施边界）：未跑任何构建/测试/安装；未触发浏览器点击链路；未调用 DeepSeek API 复测（沿用执行记录 HTTP 200 证据）；`Invoke-Item` 对 URL 的行为未实测（会打开浏览器，属副作用，留 T4）。
- 审计对象版本快照：EMC 仓 HEAD=本地 ahead-2（f1af435e）；dsh 本地 master=ec5c5e725c（未 push）；插件仓=2026-08-20 21:03 构建。

> Qoder 审计组 · 2026-08-21 · 六项核毕，无 CRITICAL，MEDIUM 四项待主手裁定。

---

# 附 · Codex 综合定稿（2026-08-21 用户复核后 · 双审计 + 修复闭环）

> 用户指令：Qoder 与 Codex 两份审计综合定稿修复，并复核三个新发现。本附录由 Codex 撰写：①双审结论交叉收敛；②三个新发现（预设跳变 / 按钮禁用 / 终端不启）根因与修复（已实施 + 浏览器实测）；③欢迎卡 UI 出处；④定稿待修清单。**修复已落地且实测通过**，非纯审计。

## A 双审交叉收敛（Qoder 版 + Codex 版）

两份审计独立取证，实质结论一致：**均判无 CRITICAL**；六项中黑屏双根因（AGREE/agree）、探测纪律（AGREE/agree）、构建链 stub（AGREE/agree）三方吻合；synapse 彻底性均为 PARTIAL（残留 M1：`~/.dsh/profiles/web/pnpm-lock.yaml` 3 处 + `pnpm-workspace.yaml` allowBuilds 1 处）；重建忠实度均为 PARTIAL（欢迎卡文案逐字 ✓、新建会话语义 ✓、去内嵌 ✓、start.bat ✓，偏差集中在 D1 死代码 / D2 欢迎卡全局可见 / D3 Edge 与 URL 链路）。

仅一处口径差异并已收敛：

| 项 | Qoder | Codex | 收敛结论 |
|---|---|---|---|
| Codex 接入配置 | PARTIAL（方向对；版本实为 0.148.0-alpha.21；supports_search_tool 断言不可外部证伪） | AGREE（方向对；本机无法运行 codex.exe 确认版本） | **采纳 Qoder 版本实测**：`wire_api="responses"` + `supports_search_tool=false` 方向正确；台账版本更正为 0.148.0-alpha.21；bug 断言标注「现场观察，未获上游确认」 |
| 欢迎卡 order 20 与 QueueDock 同序 | 未单列 | P3 观察 | 保留 P3，不阻塞 |
| client.js 字节数 | N1：7639→7797 | 同（P3） | 一致，采纳 |

## B 用户三个新发现 · 根因与修复（已实施 + 实测）

### B1 新会话"自动跳转标准模式（无视默认设置）"

- **当前环境实测：未复现**。`~/.dsh/settings.yaml:13-14` 用户默认预设 = `agent-presets.default: router-standard`；host `defaultId = settings.get().default ?? config.default`（`packages/preset/agent-presets/src/index.ts:191-193`），web 组合 config.default=standard 仅作兜底；浏览器实测点击 EMC 入口后新会话 preset 显示 **router-standard**（与 dsh 原生"新建会话"同路径、同结果）。
- **可能成因（供主手复核用户现场）**：若用户点击时 8080 未运行且旧构建按钮置灰/无空白会话，行为可能与现环境不同；旧构建（修复前 lib/client.js）的 `startSession` 路径与现在一致，但欢迎卡全局可见（D2）可能让用户误判"跳到了别的会话"。**若用户现场仍复现**：请提供「无空白会话时点击」的步骤与截图，Codex 再沿 `sessions.create`（host 侧缺省 agentPreset → defaultId）深挖 settings 是否在某 profile 未挂载。
- 修复侧动作：插件注释与实现明确"preset 由 host 默认=用户 settings 默认"，不再有任何硬编码 standard 语义。

### B2 点击一次后按钮变禁用，切换会话仍禁用

- **根因（代码 + 实测）**：探测状态 store 为模块级全局，60s tick 独占更新；`waitForEmc()` 探测成功不回写 store；launch 结束不刷新。start.bat 启动窗口期（杀旧 8080 → RAG 预热 20-30s）内任意一次 tick 探测失败即置灰，随后即使 8080 恢复也要等下一次 tick（≤60s），切会话不恢复（模块级）。
- **修复（已实施，`D:/Github/dsh-emc-entry/src/client/`）**：
  - `components.tsx`：按钮仅"启动中"（launching）禁用防重入；probeUp 只驱动视觉提示（`data-probe-up` + title），**不再阻塞点击**（8080 未跑也可点击启动，符合任务书"点击即启动"）；初始 `up=false`（首探前诚实置灰）。
  - `index.ts`：`waitForEmc()` 成功/失败均 `setProbeUp()` 回写；`launch()` 的 `finally` 立即重探；新增 `setLaunching` 状态机。
- **实测**：8080 未运行时按钮可点（title=「运行 py frontend/serve.py 8080」）→ 点击 → 启动完成后按钮恢复可点；连续点击两次均正常，无滞留禁用。

### B3 EMC 对话下终端无法启动

- **根因（代码 + 浏览器实测，三层叠加）**：
  1. **dsh-better-sidebar 0.12.2 monkey-patch `ctx.workspaces.openPath`**（`~/.dsh/profiles/web/node_modules/dsh-better-sidebar/lib/client.js`："Wrap `workspaces.openPath`: intercepted calls open the file in the sidebar"；config `interceptOpenPath: true` 默认开）→ `.bat` 被当文档在侧边栏打开（editor chunk 还加载失败），**不执行 → 终端不弹**；实测底部面板出现 `start.bat` 标签 + `[dsh-better-sidebar] chunk "editor": client module system unavailable`。
  2. **URL 被 `resolveWorkspacePath` 当 workspace-relative 解析**（`packages/client/runtime/src/client/workspaces/path.ts:7-13`，`http://…` 不以 `/` 开头且非盘符 → 拼成 `<cwd>/http:\localhost:8080\…`）→ `fs.read` ENOENT 400 → **Edge 永不打开**；实测 console `GET /sidebar/api/fs.read 400` + 底部 `index.html` 标签 ENOENT。
  3. **`waitForEmc` 10s 超时 < start.bat 重启 8080 的 RAG 预热（20-30s）** → 冷启动时探测必失败。
- **修复（已实施）**：
  - `index.ts` 新增 `hostOpen(path)`：直连 `POST /api/host.openPath`（client-request RPC envelope），**绕过 better-sidebar 的 client patch**，走宿主原生 `openNativePath`（Windows `Invoke-Item` → .bat 弹独立 cmd 窗口执行）。
  - URL 开图：用户手势内同步 `window.open('about:blank')`（规避 await 后弹窗拦截），`waitForEmc`（**40s**，覆盖 RAG 预热）成功后 `popup.location.href = EMC_MAP_URL`；失败则不导航并 console 提示。
  - 删除 D1 死代码（`await startSession()` 恒 undefined + `ctx.sessions.open` 永不执行）；`inject` 精简为 `['slots','workspaces']`。
- **实测（浏览器冷启动全链路）**：8080 停止 → 按钮可点 → 点击 → cmd 窗口 start.bat 杀旧进程并重启 serve.py（原 serve.py 进程被 kill，新 serve.py 由 cmd 窗口拉起，8080 ~30s 恢复）→ 新标签页自动打开 `http://localhost:8080/frontend/index.html`（标题「宜昌市情绪地图 prototype」）→ 欢迎卡在目标会话出现 → 按钮恢复可点 → console 无 `launch failed`。
- **遗留**：`Invoke-Item` 对 `.bat` 的窗口显示依赖 Windows shell 默认动作（实测等效成立）；若个别环境终端窗口不显示，备选为 dsh 侧 `native-path-opener` 显式 `Start-Process cmd /c start`（已评估，改动面在 dsh 仓，暂不动）。

## C 欢迎卡 UI 出处（用户提问）

- **文案与形态设计**：Codex（`PT-CB6-EMC入口重定义任务书_Codex-2026-08-20.md` 需求 1.2：标题+正文两行逐字文案、图标+标题+副文案、默认展开可关闭）。
- **重建实现（当前 components.tsx）**：zcode（home 续点重建，2026-08-21 执行记录 §三）。
- **早期侧栏按钮实现**：Codex 代 dsh（`PT-CB6-EMC入口插件执行记录_dsh-2026-08-20.md`）。
- **Qoder**：无参与记录（全仓检索零命中）。

## D 定稿待修清单（合并双审 + 修复后状态）

| # | 级别 | 项 | 状态 |
|---|---|---|---|
| D1/F3 | MEDIUM | startSession 返回误用死代码 | ✅ 已修复（index.ts 重构） |
| D3/F2 | MEDIUM | Edge 未锁定 + URL openPath 链路 | ✅ 已修复（直连 host RPC + window.open 手势段开图）；Edge 由宿主浏览器决定（当前=Edge），如需强制 msedge 需 dsh 仓改动，见 B3 遗留 |
| D5/F7 | LOW | waitForEmc 返回值忽略 | ✅ 已修复（失败不导航 + 提示） |
| M1/F4 | MEDIUM | synapse 残留（pnpm-lock 3 处 + workspace allowBuilds 1 处） | ⏳ 待执行：profile 目录 `pnpm install` 修剪 + 手删 allowBuilds 行（~/.dsh 侧，非 EMC 仓） |
| D2/F1 | MEDIUM | 欢迎卡全局可见（非仅新会话） | ⏳ 待排期：需 `ctx.sessions.list` 订阅 current+blank 绑定目标会话（API 已探明，改动集中在 components.tsx/index.ts） |
| F5 | LOW | 版本台账 0.145.0→0.148.0-alpha.21；client.js 7639→7797 | ✅ 采纳（本附录）；执行记录下次回写 |
| F6 | LOW | supports_search_tool 断言标注「现场观察」 | ✅ 采纳（R14 已标注实测口径） |
| F8 | LOW | start.bat:6/25 banner 文案过期 | ⏳ 需 EMC 仓 2 行授权 |
| — | 待办 | T4 四截图（新会话+欢迎卡/终端 start.bat/Edge 开图/置灰提示） | ⏳ 主手实测（本附录 B2/B3 已提供等价浏览器实测证据，截图待主手补档） |
| — | 待办 | EMC 人设 + 身份卡 + RAG 重建；dsh 未 push（behind 1） | ⏳ 主手排期 |

## E 环境实测快照（2026-08-21 收尾）

- dsh web（3080）运行中；8080 由 cmd 窗口 start.bat 拉起（PID 23624，serve.py）。
- 插件 bundle `lib/client.js` 9.60KB（2026-08-20 21:43 后两次重建，含 hostOpen/launching/40s 探测）；`/plugins/dsh-emc-entry/client.js` 由 profile junction 提供。
- 浏览器验证：欢迎卡 ✓ / 新会话 preset=router-standard ✓ / 8080 冷启动自动开图 ✓ / 按钮可重复点击 ✓ / console 无 launch failed（唯一 400 为 better-sidebar 遗留标签的 fs.read，非 EMC 触发）。

> Codex · 2026-08-21 · 双审计综合定稿。无 CRITICAL；B1/B2/B3 已修复并实测，D2/M1 待主手排期。
