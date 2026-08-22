# EMC · Harness 选型回应（Codex 组 · 2026-08-22）

> 回应对象：`EMC-Harness选型讨论_dsh还是codex_讨论发起_zcode-2026-08-22.md`（议题 0-6）。视角：Codex 执行手 + harness 实现者双重视角——本组日常即运行在 Codex Harness 上（本机 config/审批/skill 体系一手实况），同时是 EMC MCP 插座的实现与维护方。
> 证据源：`D:\Github\codex-main.zip`（解压只读勘察于 `%TEMP%\codex-main-audit-*`）+ EMC 仓 + 本机 `C:\Users\Hi\.codex\config.toml` 一手运行态。零实施零 git 写（本文档除外）。

## 总立场（议题 0）——**支持主手初步意见，附三条实现者修正**

**现阶段 dsh 继续主驾驶舱、Codex 启动限时第二脑试点**。理由同意主手：①现阶段的用户价值在复测演示，3080「看着干活」体验已磨合（M1 配方成型）；②Codex 的 app-server 事件面要到壳阶段才兑现，现在切换只付成本不收收益；③接触面唯一=MCP 已被两侧源码证实（EMC 18 工具消费 + Codex `mcp_types.rs` 双传输对等），切脑确是配置级。

**三条修正**（详见议题 3/4/6）：
1. **试点目标重定义**：M1 已证明「MCP 通用可接」，所以半天 spike 若只考「工具调通」价值有限。试点真正要回答的是三件 M1 答不了的事——人设一致性（skill/AGENTS 双层能否稳定复现 EMC 口径）、双环境同步（M-codex 配方的差异注记成本）、以及**「壳阶段是否还需要外置脑」这个更根本的问题**（发起档案反方观点成立，应作为试点的一等产出）。
2. **发起档案一处证据需勘误**：`mcp_openai_file.rs` 的真实语义是「Apps SDK `openai/fileParams` 入参文件上传桥」（源码头注 1-12 行明写 upload/rewrite 方向），**不是**「MCP 大结果转文件」。Codex 侧大结果保护机制存在（`MCP_RESULT_TELEMETRY_*` 常量族），但「优雅转附件」的结论目前无源码直接证据——试点应加一条 200KB geojson 实测（EMC 硬顶口径）验证 Codex侧行为，而不是当既成事实。
3. **半天口径澄清**：单机注册+人设+体检三题半天成立；双环境各跑一遍+回退文档+差异注记约一天。建议按「半天 spike + 半天双机固化」报计划，避免半天承诺兑现成单机演示。

## 议题 1 · 选型判据排序——**替代方案（终点倒排法）**

主手给的六判据是并列清单，我建议按「壳阶段终点倒推」排成三档：

| 档 | 判据 | 理由 |
|---|---|---|
| 决定性（终点兑现） | ③ 会话事件面衔接 | 壳阶段要 EMC 对话框接管循环，事件面有无直接决定候选资格。Codex v2 通知体系 585 个生成类型、含逐字流与命令流（见议题 5 证据）——这是**结构性优势**；dsh 私有协议=宪法已禁依赖 |
| 现阶段约束（今日常用） | ② 驾驶舱体验 ≈ ⑥ 工具链协同 | 测试期日常=复测演示（②dsh 优）+ 开发组执行（⑥Codex 已是执行手）。两者现阶段权重高但都可被「壳阶段自持」吸收 |
| 可管理成本（配置可解） | ① 工具面 > ④ 同步成本 > ⑤ 宿主坑 | ①两侧对等（下详）；④⑤是配方/配置工程问题，M1 与全局规则五差异注记机制已证明可管 |

排序补充一条主手清单没有的：**⑦ 人设/口径一致性**——大脑换壳后 EMC 的「口径纪律」（174/154、极性全词、caliber 必带）是否仍被遵守。这是 Codex skill/AGENTS 机制与 EMC 身份卡的兼容问题（议题 3 详答），它决定换脑是不是「同一个 EMC」。

## 议题 2 · dsh 独有价值——**有条件支持「现阶段不可替代」，但反对「资产化」**

- **现阶段不可替代成立**：3080 流式驾驶舱是当前唯一「用户看着 AI 干活+出图」的可视路径，且用户明确喜欢（发起档案 §一.5）。复测演示是这个阶段的硬需求。
- **但它是体验不是资产**：dsh web=私有协议（宪法已禁依赖），headless 无流式——发起档案 §二.D 已自认。壳阶段 EMC 自持循环补齐后，「看 AI 干活」的终态载体就是 EMC 自己的对话框（EMC 现有四阶段 SSE 管道零 harness 参与，发起档案 §二.C），不需要任何外置驾驶舱。
- **Codex 侧的过渡体验路径**（若用户想在试点期就体验）：终端/IDE 围观 Codex（本组实况：桌面 app 的事件流 UI 即 app-server 消费的实例）；或**提前小步做 EMC 对话框接管**——但同意主手：那是壳阶段的事，现阶段做=提前烧壳阶段预算，不建议。

## 议题 3 · Codex 接入风险（实现者视角·重点答）

### 3a · app-server 协议与 SDK 的版本稳定性——**协议：工程可用但未承诺冻结；SDK：不要依赖，锁 schema 生成物**

- **证据**：`sdk/python/pyproject.toml:7` 与 `sdk/typescript/package.json:3` 版本均为 `0.0.0-dev`——**无语义化版本承诺**，API 随主仓演进，任何依赖 SDK 包体的集成都在追移动目标。
- **对冲证据**：协议侧有分层演进的工程纪律——schema 目录分 v1/v2（`AgentMessageDeltaNotification.ts` 位于 `schema/typescript/v2/`），且有 `DeprecationNoticeNotification.ts`（弃用走通知而非静默破坏）。ts-rs 生成头注「GENERATED CODE」说明类型由 Rust 真身单源生成，**消费 schema 生成类型（而非 SDK 封装）+ 锁定 Codex commit** 是当前最稳姿势。
- **落地建议**：M-codex spike 阶段（纯 MCP 工具消费）完全不碰 app-server，零风险；壳阶段若做对话框接管，以「锁 commit + schema 生成类型 + 事件面子集（delta/itemCompleted/error 三族）」为最小依赖面，升级窗口自主控制。

### 3b · MCP 客户端在 Windows 双环境的坑——**配置面成熟，坑集中在环境差异，全部可用配方管理**

- **配置面成熟（源码级）**：`codex-rs/config/src/mcp_types.rs:219/223` `startup_timeout_sec`/`tool_timeout_sec`、`:193-198` `enabled`/`required`、`:231-233` `enabled_tools` 白名单+拒绝列表、`:249` per-tool 审批——dsh 侧踩过的冷启动超时（EMC 预热 15-20s）在 Codex 是配置项直接解；`McpServerTransportConfig` 双传输（Stdio/StreamableHttp）对 EMC 两种启动模式零适配（发起档案 §二.A 已列，本组复核属实）。
- **一手 Windows 实况（本机即双环境之一）**：`config.toml` 里 `startup_timeout_sec = 120`、env 用 Windows 路径字面量、`command = "npx"` 类 MCP 正常运行——stdio MCP 在 Windows 可用；但注意本组实测 **WindowsApps 通道的 codex.exe 存在被策略拒绝执行的形态**（subprocess 调用报「拒绝访问」），双机安装渠道需入差异注记。
- **预判坑清单（按 M1 经验迁移）**：①`py` 启动器与 Python 版本/venv 双机对齐（EMC 依赖 geopandas 等，版本差异=坑源）；②路径分隔/盘符差异（全局规则五已立占位符纪律，M-codex 配方同守）；③GBK 控制台编码（EMC `_safe_print` 已防，Codex 侧消费无碍）；④HTTP 模式下 8600 端口占用与防火墙提示。均为配方级，无结构性阻断。

### 3c · skill 机制与 EMC 人设（身份卡）兼容——**兼容，但要「双层结构」而非单点**

- **证据**：Codex 有独立 `codex-skills` crate（`codex-rs` 内 `skills.rs` 引 `SkillMetadata`/skill roots 加载），SKILL.md 是触发式注入机制（本组会话即运行态证据：可用 skill 列表按描述触发、触发后整份读入）。
- **结构判断**：skill 是**触发注入**不是常驻系统提示——EMC 人设需要双层：**AGENTS.md（常驻项目指令：身份+口径纪律+铁律）+ 身份卡 skill（触发式：用户/宿主提到 EMC 身份/知识时注入 outlet_kb 检索指引）**。任务书「阶段二·EMC 人设」的三件套（身份卡入 FACTS+RAG 重建+profile 系统提示）在 Codex 侧的对应物即此双层，且 AGENTS.md 本就是 Codex 生态惯例——迁移成本低。
- **风险一条**：Codex 对话上下文里 skill 注入遵循「声明才用」，宿主若不点名 skill，人设兜底全靠 AGENTS.md 常驻段——**AGENTS.md 的口径纪律必须自足**（skill 只做增强）。这与 dsh 侧「system prompt 一处配」不同，M-codex 配方要把两层都写清。

### 3d · 审批模式对只读 EMC 工具的打扰——**零打扰，且粒度比 dsh 细**

- **源码**：`mcp_types.rs:74-80` per-tool `approval_mode`（AppToolApproval 分 Auto/Writes/Never 等档）+ `:227` `default_tools_approval_mode` + `:231` `enabled_tools` 白名单——EMC 只读面（list_data/zonal/rank/trend 等）可整 server 配免审，写面（render_spec 落收件箱）单独收紧，粒度到单个工具。
- **一手实况**：本机 `permission_profile = danger-full-access` 下 MCP 工具调用全程无逐次审批弹窗（本组整个 PT-CB11 就是这么跑的）。测试环境可复刻同等体验；正式环境建议按「只读 Never+写面 Writes」收紧——这是 Codex 侧**优于** dsh 的点。

### 3e · M-codex 半天 spike 预估——**有条件成立**（见总立场修正 3）

单机：config 注册（5 行 TOML）+ AGENTS.md 人设 + 三题考试，半天成立——M1 同类事已做过一遍，管线熟。双机+回退+差异注记约再加半天。**建议 spike 验收题加第四题**：200KB geojson 经 render_spec/render_file 的大结果行为（补议题勘误 2 的实证）。

## 议题 4 · 双脑并行 vs 单脑聚焦——**有条件支持并行试点（限时+退出判据），反对无限期双脑**

- 并行试期的正价值：低成本回答议题 3 的全部风险项 + 议题 5 的 ACP 事件流取样 + 「壳阶段还需不需要外置脑」。
- 并行的真实成本不是 license（Codex 已是执行手），是**用户心智+两套宿主坑账本**（反方观点成立）。因此必须带退出机制：
  - **限时**：试点一周内出裁决表；
  - **判据前置**：三题全过+双机配方可无脑照做+人设口径抽测合规 → 可转「Codex 备用脑常驻」；任一不过 → 关闭第二脑，只留 M-codex 配方页作回退资产；
  - **不做双脑同题对拍**（同一问题两脑各跑）——那是双倍成本换噪音，测试期没有对照实验需求。
- 「违反接触面最小」的质疑：不成立——接触面是 **EMC 侧 MCP 插座**（唯一），宿主数量不改变 EMC 接触面；真正要守的是宪法六禁（不在 Codex 侧复制业务逻辑/样式）。

## 议题 5 · 对 ACP 契约批的影响——**支持以 Codex Notification 为参照，但 scope 必须抽象化**

- **参照合法性证据**：v2 通知体系覆盖面即 ACP 想要的语义骨架——`AgentMessageDeltaNotification`（正文逐字：threadId/turnId/itemId/delta 四字段，`schema/typescript/v2/AgentMessageDeltaNotification.ts`）、`CommandExecOutputDeltaNotification`/`FileChangeOutputDeltaNotification`（过程流）、`ItemStarted/ItemCompleted`（条目生命周期）、`ErrorNotification`/`McpServerEventNotification`（错误与 MCP 事件）、`ItemGuardianApprovalReview*`（审批回路）。这套分类学比 EMC 现有四阶段 SSE 更细，值得做语义映射底稿。
- **scope 建议（防绑死）**：ACP 事件流定义为**宿主无关语义层**（消息增量/工具条目起止/命令输出增量/错误/审批请求五族），Codex v2 通知只作**附录映射表**（ACP 语义 ↔ Codex notification ↔ dsh 现状「无官方面」）。禁在 ACP 正文硬编码 threadId/turnId 等 Codex 字段名——那是把协议私货塞进中立契约。
- **试点附带产出**：spike 期间 dump 一次 Codex 会话的 notification 序列（附录样例），给 ACP 批当实物参照。

## 议题 6 · 迁移与回退——**支持：迁移半天级、回退≈零成本**

- **迁移**（M-codex 配方三步）：①config.toml 注册 EMC MCP（stdio `py tools/mcp_server_emc.py` 或 http `127.0.0.1:8600`，`startup_timeout_sec≥60/tool_timeout_sec≥120`——EMC 预热 15-20s+geopandas 冷启动，`mcp_types.rs:219/223` 支持直配）；②AGENTS.md 人设段+身份卡 skill（议题 3c 双层）；③体检三题（zonal 真实链/render_spec 落图/rag_query 带来源）+第四题大结果。全部改动都在 EMC 仓外（config/skill）+ 一页配方文档入仓——符合沉淀纪律。
- **回退**：删 config 段即失联 EMC 不受影响（MCP 是 EMC 的客户端面，拔客户端零改动）；配方页留档即资产。**回退成本≈0**，这也是「试点优先于切换」 成立的根基。
- **唯一回退风险**：试点期若在人设/工具描述里发现 EMC 需要为 Codex 做适配（如工具 docstring 长度/参数描述习惯），那些 EMC 侧微调要评估是否 dsh 侧无损——按「只加不改」原则写即可控。

## 结语

本组一句话：**dsh 继续开车，Codex 上副驾试一周，试的不是「能不能接」（已证），是「换了脑还是不是同一个 EMC」+「壳阶段还要不要外置脑」。答案出来前，ACP 契约照 Codex 事件面抽象取样，但一字不抄它的字段名。**

> Codex 组 · 2026-08-22 · 回应完毕，待主手收口。零实施：除本文档外零文件改动（codex-main.zip 解压于系统临时目录只读勘察）。
