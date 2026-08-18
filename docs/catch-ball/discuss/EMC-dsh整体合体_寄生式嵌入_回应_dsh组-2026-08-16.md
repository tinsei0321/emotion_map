# EMC × dsh 整体合体（寄生式嵌入）· 三组联合讨论回应 —— dsh组

> **勘误注记（2026-08-18·PT-CB1/T3a 归档批）**：① 本地 dsh 仓已迁至 `D:\Github\dsh`；本文件时点的旧仓 `D:\Github\dsh_test` 已不可用（目录仅残留清理文件）。② 本文件「600 commit 内 16 个 `!:`」口径在当前历史不可复现；现行口径 = 全史可检出 16 个 `!:`（均 2026-08-10 及以前），供应链主证据改用 **08-11~08-17 六天 10 个 rc** 的发布节奏。③ 审批语义以 2026-08-18 新仓实测为准：`ask|never` 两态、`allowed-once` 为唯一 grant、无 session 宽授权；与本文「always-allow 第三态（session-wide grant）」表述冲突处以实测为准。出处：`EMC-dsh可行性深挖_回收抽验_Codex-2026-08-18.md`。

> 回应方：dsh组（DeepSeek Harness 母框架侧）· 2026-08-16 · 分支 `EMC_harness_dsh` · 零实施纯讨论。
> 依据：zcode 评估发起稿 + 前置底稿（均 2026-08-16），并对 dsh checkout（`D:\Github\dsh_test`，master@cafd4e6132，v0.1.0-rc.5）做了现场核查——所有 dsh 侧结论均落到文件路径/行号/提交哈希级证据，不用二手转述。
> 分组侧重：议题4 主答 + 议题1/2 质证；议题3/5/6 只供给 dsh 侧技术事实，裁决留给主答组。

---

## 〇 一句话结论

**认同 zcode 的方向性裁决（否决 A、立项 B），但对其中三条 dsh 相关事实表述做了修正，修正后反对 A 的论证更硬而非更软**：① dsh **原生支持 MCP**（一阶客户端 `@deepseek-ai/dsh-mcp-client`），zcode「若 dsh 不支持 MCP」的分支前提不成立——这使 D3 载体选型退化为「MCP server 唯一解」，dsh 零代码即可消费 EMC 工具面；② dsh 的破坏性变更从定性担忧升级为**定量实锤**（近 600 commit 内 16 个 breaking `!:` 提交、最近一批就在上一周、30 天约 9,500 commits）——这使「整体寄生」的维护成本论证更强；③ 「dsh 没有地图 UI」字面成立但需修正为「Web Client 有可扩展会话节点机制、地图 viewer 技术上可行、但代价数倍于 MCP server 且只服务 dsh 单宿主」。**方案A 未发现任何成立场景；方案B 立项 + MCP 载体 + 1-2d spike 为最优解。**

---

## 一 四决策点建议（D1-D4 先答）

| # | 决策 | dsh组建议 | 理由（证据见后文各节） |
|---|---|---|---|
| **D1** | 方案A（整体寄生）裁定 | **否决**（与 zcode 一致） | 六维反对无结构性漏洞；dsh 侧补三刀：确定性编排器在 dsh 里不是「失守」而是「用 turn-stopping/concludeTurn/guard 重焊」，焊接点是 0.x 每周变动的 API；未发现任何 A 成立的合理场景（含 dsh 独有场景，见 §3.2） |
| **D2** | 方案B（工具级寄生）是否立项 | **立项 + spike**（1-2d，体外） | EMC 本体零改动、四条承重红线原样；四份 harness 全部消费 MCP 协议，「一次实现处处可用」的边际成本≈0；与 CB-39 B/C 线、CB-40 G1-G5 零交叉 |
| **D3** | 方案B 载体预选 | **MCP server 唯一首选**（dsh plugin 缓议、bash 侧门过渡保留） | dsh 原生 MCP 客户端使 MCP server「写完当天 dsh 零代码接入」；EMC 仓内已有 FastMCP 先例（vision_bridge_server.py）；「双轨」反对——同一能力两份 schema 双源漂移，撞红线「契约单一源」 |
| **D4** | dsh组 回归参与本轮 | **回归**（本回应即回归产出） | 议题4 是 dsh 母框架技术事实题，本组已给出源码级证据；后续 dsh 侧质证（D3 落地细节、dsh 兼容面）继续由本组供给，避免其余两组转述 dsh 事实出错。范围=讨论/质证，实施仍由 Codex 主线程执行 |

---

## 二 议题4 主答：dsh 母框架技术事实（四组实锤）

### 2.1 dsh 消费 MCP：一阶客户端，非假设、非第三方

**结论：dsh 原生支持 MCP 客户端，且工具命名与 Claude Code/Codex 同形。** 证据：

- `packages/mcp/mcp-client`（`@deepseek-ai/dsh-mcp-client`）：「MCP client bridge that registers external server tools on `ctx.tools`」（`packages/mcp/README.md:7`）。
- 双 transport：`stdio`（spawn 子进程）+ `streamable-http`（URL+headers，可带鉴权 token），另含自动重连策略（指数退避 + 预算制：`reconnect.maxAttempts` 默认 10，连续失败后卸载工具，见 `mcp-client/README.md:34-51`）。
- 工具命名：`mcp__<serverName>__<rawName>`（`README.md:5,32`）——与 Claude Code/Codex 的 `mcp__server__tool` 形态一致，命名是 `(serverName, rawName)` 的纯函数，重连/再同步不换名。
- 运行时行为：激活时 `listTools()` → 逐个 `ctx.tools.register()`；监听 `notifications/tools/list_changed` 再同步；崩溃自动重启+重发现，旧代工具保持注册不泄漏（`README.md:64-71`）。
- 配置面已文档化进官方 config-catalog（stdio/streamable-http/reconnect 完整配置节，`docs/config-catalog.md:1214-1267`）；CLI 把用户 MCP 配置编译为 cordis 插件行（`apps/cli/tests/memory-mcp-configs.spec.ts`）。

**对 EMC 工具面的实际限制**（`mcp-client/README.md:109-115` Known Limitations）：只桥接 **tools**（resources/prompts 无消费者、延期）；非文本渲染 lossy（image/audio 成占位符）；`outputSchema` 超出 harness JSON Schema 词汇子集时退化为不校验的 `JsonValue`。→ 三点都不影响 EMC 六工具面（全是 text/CSV 输出；见 §5.1 schema 兼容判定）。

### 2.2 破坏性变更节奏：定量实锤（zcode 定性判断的升级）

- README 原文（`README.md:9-11`）：「DeepSeek Harness is currently in **developer preview** and is iterating rapidly. **THERE WILL BE COMPATIBILITY-BREAKING CHANGES.**」
- 当前版本 **0.1.0-rc.5**（根 `package.json`）。
- 提交历史量化（`git log` 实测，截至 2026-08-16）：
  - 最近 **600 commit 内 16 个 `!:` 破坏性提交**（conventional commits breaking 标记）；
  - 最近一批 breaking 日期 **2026-07-29 ~ 2026-08-09**——即上一周；其中 **2026-08-06 单日 3 个**（`37cbd155f5 refactor(cli)!` / `62d0f26fd6 refactor(cli)!` / `cd6b4ee3c9 feat(cli)!`），集中在 cli/config/profile 层——**正是第三方 plugin 分发生态所依赖的层**；
  - 30 天 commit 量约 **9,500**（`--since=2026-07-16`）。
- 另：审批机制仍在演进（`31dcb00260 feat(approval): always-allow third state (session-wide grant)` 为本月新合入）。

**定性**：zcode「preview 有破坏性变更」成立且被低估——真实节奏是**周级 breaking、单日可达 3 个**。任何「plugin 级寄生」= 每周陪跑 API 迁移；「MCP 级寄生」完全绝缘于该节奏（MCP 协议是外部标准，dsh 侧变化只在 mcp-client 内部消化）。

### 2.3 dsh plugin 开发的真实成本（骨架便宜，长期贵）

**骨架成本（低）**：plugin = 一个 TypeScript 模块导出 `apply(ctx)`（`docs/user/develop/basic/index.md:17-27`）；最小工具 plugin 约 20 行（`docs/user/develop/basic/tool.md:11-33`）；本地 `--patch ./cordis.yml` 加载，**无需 fork monorepo**；分发走 `dsh plugin add`（npm 发布或 `pnpm pack` tarball，`docs/user/develop/basic/publish.md:177-178`）。zcode §2.4「必须整体迁入 monorepo」的隐含恐惧不成立。

**真实成本（高），全在骨架外：**

1. **语言栈**：TS strict 全栈 + pnpm/tsdown 构建链（根 `AGENTS.md:137`「strict: true、noImplicitAny、导出级 JSDoc 校验」）。EMC 前端是纯 JS 零构建（CLAUDE.md 技术栈），零 TS 基建——这是新增的**永久性**工具链负担，不是一次性。
2. **API 陪跑**：§2.2 的 16 breaking/600 commit 节奏，plugin 是扩展点 API 的 consumer，必须逐周跟。EMC「稳定压倒灵活」的产品决策与「每周适配」直接冲突。
3. **行为保障重做**：EMC 的确定性编排器在 dsh 内**技术上可以重焊**（`agent/pre-step` 权威改写 + `agent/turn-stopping` + Monotonic `concludeTurn()` + `ctx.tools.guard()`，见 `docs/cookbook/extension-cookbook.md:33,101-129`）——但这等于把 CB-22 系列 10+ 轮硬化行为搬到焊接点上再验证一遍，且焊点在动（§2.2）。
4. **地图 UI（若想要）**：dsh Web Client 支持自定义会话节点（`ConversationNodeDefinition` + React keyed renderer，`docs/cookbook/adding-a-conversation-node.md`，233 行教程 + 事件族可重放设计）——地图 viewer 技术上可行，但这是 **React client plugin + 事件族设计**的完整工程，量级数倍于 MCP server，且**只服务 dsh 单宿主**（zcode/claude/codex 拿不到任何收益）。

**成本结论**：plugin 是「省在开头、贵在长期」的载体；MCP 是「省在协议、贵在开头一次性写 server」的载体。对 EMC 的维护人月结构（用户一人 + agent 组合），长期成本是决定性变量。

### 2.4 「领域产品作为 plugin 寄生」在 Everything-is-a-Plugin 哲学下的内部视角

- **哲学层面欢迎**：根 `AGENTS.md:3`「everything is a plugin」；`AGENTS.md:108`「**Plugins, not loop changes**: new behavior goes on documented extension points」。`extension-cookbook.md` 的 feature→mechanism map（L101-129）逐行列出「每个产品特性=某个文档化扩展点上的监听器，没有任何一行修改 loop」——领域产品以「工具 plugin + 会话节点 + 事件消费」形态入驻，机制上完全开放、无特权核心排斥。
- **但内部视角的诚实判断（本组不说客气话）**：
  1. dsh 的预设用户是**会改插件的开发者**（README 自述 developer preview；文档主轴 = user/develop 插件教程群）。EMC 的目标客户是规划师/住建局非开发者——两套预设不重合，zcode §2.2 用户错位判断成立。
  2. 「扩展点 API 文档化」≠「扩展点 API 稳定」。0.x 下文档化只是可发现性保证；16 breaking/600 大半砸在 cli/config/profile 层（§2.2），那正是 `dsh plugin add` 生态的承重层。把「稳定压倒灵活」的领域产品放进来 = **用最不稳定的层承载最需要稳定的层**，方向反了。
  3. dsh 欢迎的是「**消费者**」不是「**住户**」：MCP 消费是一阶支持、零代码、绝缘于 breaking（§2.1/2.2）；把产品逻辑住进 plugin 是另一回事。dsh 自身也不主张「领域产品寄生」是 plugin 的典型用法——它的示例全是 harness 能力（工具/钩子/协议驱动/UI 行）。
  4. **一条对 EMC 反而有利的 dsh 独有事实**：dsh 是四份 harness 里唯一**浏览器原生 Web GUI**（`apps/web`，即本讨论所在的 GUI 形态）+ MIT 全开源 + 可自托管 + DeepSeek 官方模型适配器（`dsh-llm-deepseek`）。若用户想要「浏览器里的开放 agent 对话」体验，dsh Web 是现成的。但这条同样由 **MCP 路径**获得（§2.1）——它是「MCP 首选」的加分项，不是「plugin 寄生」的理由。

### 2.5 对 zcode 稿 dsh 相关描述的修正清单

| zcode 表述 | dsh 事实（证据） | 修正后结论 |
|---|---|---|
| 「dsh 无『FC 单次意图理解』概念，诊断逻辑必须翻译进 system prompt/agent loop——等于重写」 | 有 `agent/pre-step`（可权威拒绝/改写）、`agent/turn-stopping`、Monotonic `concludeTurn()`、`ctx.tools.guard()` | 不是「重写」，是「重焊」：技术上可近似实现单轮单意图+终态工具，但焊接点=0.x 周级变动的扩展点 API。反对结论不变、论证更硬 |
| 「dsh 是开发者终端/CLI 形态，没有地图 UI」 | 字面成立；但 Web Client 有 `ConversationNodeDefinition` 自定义会话节点机制（React） | 地图 viewer 可行但代价=完整 client plugin 工程且单宿主专属；不改变裁决，但不能再以「无地图 UI」作论据 |
| 「dsh plugin（若 dsh 不支持 MCP 或用户指定 dsh 为宿主）」 | dsh 原生 MCP 客户端（§2.1） | 分支前提「若 dsh 不支持 MCP」不成立，议题2 前提需修正 |
| 「开发预览、有破坏性变更」 | 16 breaking/600 commit、周级节奏、单日 3 个、30 天 9.5k commit（§2.2） | 定性判断升级为定量实锤 |
| （隐含）「必须迁进 monorepo/被供应链绑架」 | `dsh plugin add` 支持 npm/tarball 外部分发（§2.3） | 修正为「API 陪跑风险」，比仓绑架更隐蔽 |

---

## 三 议题1 质证：方案A 六维反对是否有漏洞

### 3.1 六维框架检查：无结构性漏洞，两处表述可硬化

逐维检查（dsh 事实面）：

1. **红线维（2.1）**：结论正确，论证可硬化——见 §2.5 第 1 行「重写→重焊」。补充一点：dsh 的 open loop 是 `turn = 0..n step、LLM 自主决定何时停`（底稿 §一.2 引用无误），EMC 的 B001/B003 病史（推理螺旋/死循环）正是这个 loop 模式的同族病——zcode 说「把病请回来当特性」不是修辞，是机制同源。
2. **形态维（2.2）**：成立，附 §2.5 第 2 行修正（地图 UI 的准确表述）。
3. **再硬化维（2.3）**：完全成立。颗粒度/诚实度防线在 dsh 里可重焊（pre-step/guards/post-execute），但「重焊」本身要消耗 CB 轮次再验证，且焊点在动——zcode「重付历史学费」成立。
4. **供应链维（2.4）**：修正「仓绑架」表述（外部可分发），但 breaking 定量数据（§2.2）使风险不减反增：绑定的不是仓库而是 **API 迁移节奏**。
5. **工具链维（2.4）**：成立（TS/pnpm 全套 vs EMC 零构建）。
6. **收益维（2.5）**：成立，「等价物」论证因 G6-G9 存在而闭合（session log→G6、守卫→G7、受控多步→G9）。

**漏洞结论：无。六维之间无重复计数、无循环论证；任何一维单独都足以否决 A。**

### 3.2 方案A 合理场景检索：dsh 独有场景已识别，仍指向 B 不指向 A

zcode §2.6 steelman（竞赛后转向「用户+agent 出 PPT/报告」生产线）本组认同。补充一个 zcode **未识别**的 dsh 独有场景：

> **场景 S**：用户想把「EMC 能力 + 开放对话」交给**非开发者合作方**（规划局同事/评审）在**浏览器**里直接使用。四份 harness 中 dsh 是唯一浏览器原生 Web GUI + 可自托管 + MIT 的（§2.4.4）；zcode/claude code/codex 都是终端/IDE 形态，合作方无法直接上手。

该场景是真实的、且是 dsh 相对其余三份 harness 的唯一不可替代点。**但结论仍是 B 而非 A**：场景 S 的全部需求（浏览器里对话 + 调 EMC 工具）由「MCP server + dsh 原生 MCP 客户端」全量覆盖（§2.1），EMC 本体、四条承重红线、CB-22 硬化行为全部原地不动。**场景 S 是 D3 选 MCP 的加分项，不是 A 的豁免理由。**

**结论：未发现任何方案A 成立的合理场景。steelman 的最大力气只推出「dsh 值得被接入」，推不出「EMC 值得搬进 dsh」。**

### 3.3 「用户已拥有三份通用 harness」反证检查：成立，且被协议生态加固

本组特意做了反证尝试：该论断是否低估了 dsh 的独有价值（MIT/自托管/浏览器 GUI/DeepSeek 原生适配）？→ **不构成反证**：

- 用户确实已拥有 zcode/claude code/codex 三份通用 harness，且 CB 工作流已深度嵌入其中（CB 索引为证）；dsh 是第四份、价值在场景 S（§3.2），而不是「用户缺的第四份」。
- 更强的事实：**四份 harness 全部消费 MCP 协议**，且命名形态同形（`mcp__server__tool`，dsh 与 Claude Code/Codex 一致，§2.1）。这意味着 zcode 论断被协议生态本身加固：harness 越多，「工具级寄生」的边际成本越趋零、「整体寄生」的锁定成本越高。
- 反向推论同样成立：正因为四份都吃 MCP，**方案B 不是「给 dsh 开侧门」，而是「给整个 harness 生态开侧门，dsh 自动在内」**——zcode「协议级寄生」的定性在 dsh 侧得到一阶支持。

---

## 四 议题2 质证：载体选型

### 4.1 前提修正

zcode 议题2 的三选项预设「dsh plugin（若 dsh 不支持 MCP 或用户指定 dsh 为宿主）」——**前半句前提已被 §2.1 推翻**：dsh 支持 MCP，且是一阶客户端。选型空间退化为：

| 选项 | 状态 | 判定 |
|---|---|---|
| MCP server | 真选项 | **唯一首选** |
| bash 野生侧门 | 真选项 | 现状过渡，不作长期载体 |
| dsh plugin | **伪选项**（对「让 EMC 进 dsh」这个目标） | 仅当需要 dsh 独有 UI 能力时才成真 |

### 4.2 建议：MCP server 唯一首选（与 zcode 一致，理由新增 dsh 侧一条）

- **新增理由（dsh 侧实锤）**：MCP server 写完当天，dsh 经原生 mcp-client 零代码接入（stdio spawn Python 或 streamable-http 均可，§2.1）；EMC 只需交付一份 server，四份 harness 全通。
- 工程基础：仓内已有 FastMCP 先例（`.claude/mcp_servers/vision_bridge_server.py`，模式可复制）；`run_analysis_task()`（`SCRIPT/emotion_analysis_v1.py:1038`）与 `export_outlet_card_csv()`（`core/export.py:200`）都是现成稳定入口。
- 一个落地注意点：`mcp` 包当前**未列入 requirements.txt**（vision_bridge 是文档手动 `pip install mcp requests`）——spike 时需由 Ops 补依赖登记，这是 spike 的少数几个实质改动之一。

### 4.3 dsh plugin 分支的真实成立条件

仅当以下两者**同时**成立才立项（本组建议排在任何 G 项之后）：

1. 用户点名 dsh 为宿主（而非「任意 harness」）；
2. 想要 dsh 独有 UI 能力：Web Client 内嵌地图/图层会话节点（ConversationNode，§2.3.4）。

**明确反对「双轨」（MCP + dsh plugin 并行维护）**：同一能力两份 schema 定义必然双源漂移，直接撞红线「契约单一源」。若未来确有 dsh UI 需求，正确做法是 dsh plugin 作为 **MCP 之上的薄 UI 壳**（plugin 只做会话节点渲染，工具调用仍走 MCP），schema 仍以 MCP server 为单一源——但这是后话，不进本轮 spike。

### 4.4 bash 野生侧门的定位

现状即事实（CB 出图主线各组 agent 天天经 bash 调脚本）。定位：**MCP 落地前的过渡保留**（成本 0、已验证），落地后降级为调试通道；不作为长期载体——它没有 schema（无参数校验）、没有审批（无 allow/deny）、没有脱敏纪律（铁律 7 全凭 agent 自觉），正是方案B 要消灭的形态。

---

## 五 边界议题的 dsh 侧事实供给（非主答，供对应主答组裁决）

### 5.1 议题3：schema 复用可行性（dsh 兼容面技术判定）

- `contracts_to_tools_schema()`（`ai_qa/tool_contracts.py:473`）产出的是 **OpenAI function-calling 包装**（`{type:'function', function:{name, description, strict, parameters}}`）；MCP 工具定义需要裸 JSON Schema 的 `inputSchema` → 适配是**剥壳级**（`function.parameters` → `inputSchema`；`strict` 字段 MCP 不认识、丢弃；`additionalProperties:false` 保留），约 10 行，不是重写。zcode「schema 直出」论断成立，精确表述为「**剥壳直出**」。
- dsh 侧词汇兼容：`docs/subsystems/tools.md:100` 确认 dsh JSON Schema 词汇显式支持 `additionalProperties: true|false`、object/array/enum/const/oneOf 等；`mcp-client` 对超词汇 `outputSchema` 退化为不校验的 `JsonValue`（§2.1 限制）。→ **建议**：MCP server 的 outputSchema 以最小公共词汇书写（string/number/boolean/array/object/enum），四宿主全兼容；EMC 六工具面（§3.3 清单）全部满足，无冲突。

### 5.2 议题5：脱敏/审批/中转站纪律映射到 dsh 的事实面

- dsh 审批机制：`tools/pre-execute` waterfall（allow/deny/**ask**）+ `ctx.approval`（ask 未答即拒绝）+ monotonic guards 不可重排（底稿 §一.4 引用无误；`extension-cookbook.md:118`）；本月新增 always-allow 第三态（`31dcb00260`）。→ 四宿主各有审批门，但**纪律的单一权威源必须放在 MCP server 侧**：sim 数据目录在 server 侧拒绝访问、只读工具无任何写路径、输出统一过脱敏函数——宿主审批只是第二道，不能作为纪律的承载层（否则「四宿主 × 各自审批配置」= 纪律漂移）。
- dsh 侧风险提示：open loop 下宿主可能把只读工具的结果反复喂回模型重组——这更支持「脱敏在 server 侧做绝」（进模型的都是脱敏后的），与 zcode 议题5 方向一致。

### 5.3 议题6：排期（一句）

方案B spike（1-2d）**建议入 CB-40 缺口清单**（编号随 G6-G9 族续编，如 G10）：体外零耦合、可与 CB-39 B/C 线并行、不阻塞 G1-G5；具体排序交 Codex 排期统一表，本组不再单开轮。

---

## 六 结论汇总

1. **D1 否决方案A**：六维反对无漏洞；dsh 侧补三刀后论证更硬——确定性编排器是「重焊」不是「重写」、breaking 是周级实锤、地图 UI 是可行但单宿主专属的贵工程；方案A 无任何成立场景（含 dsh 独有的场景 S）。
2. **D2 立项方案B**：工具级（协议级）寄生是用户设想的正确落法；1-2d spike 体外实施，EMC 本体零改动、四红线原样、CB-39/CB-40 零交叉。
3. **D3 载体 MCP server 唯一**：dsh 原生 MCP 客户端使「一次实现、四宿主全通（含 dsh）」，dsh plugin 仅在需要 dsh 独有 UI 时以「MCP 之上的薄 UI 壳」形态另行立项；bash 侧门过渡保留；反对双轨。
4. **D4 dsh组 回归**：本回应即回归产出；后续 dsh 侧质证与兼容面事实由本组持续供给，实施不参与。

> 红线重申（dsh 侧视角）：diagnose prompt 永不动 / 编排器确定性 / 契约单一源 / 三支柱缺一不可——四条在方案B（MCP 载体）下是**服务器外的边界条件**（MCP server 只暴露既有稳定入口、不承载任何编排/范式/知识库逻辑）；在方案A 下是**重焊清单**。载体的选择本身就是红线的一部分。
