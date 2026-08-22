# EMC · Harness 选型讨论发起：现阶段外置大脑用 dsh 还是 Codex Harness？（zcode·2026-08-22）

> 发起：zcode 主手（用户令）。讨论方：Codex + Kimi（用户转发）。性质：**选型讨论·零实施**——回应落盘各自文档，立场四档（支持/反对/有条件/替代方案），主手收口后交用户拍板。
> 关联：`PT-CB10-战略转向裁定`（R61·dsh 归官方+MCP 优先）·`备忘录_dsh纯净官方版纪律`（宪法六禁）·`EMC-dsh工程预期与双环境同步核心思想`（两阶段路线）·ACP 契约定义批（P2 后批清单）。

---

## 一 讨论起源与过程实录（08-22 上午·本会话）

1. **用户问题①**：未来想把 EMC 的「大脑」从 dsh 换成 Codex Harness，能热拔插吗？（小工程量·简单配置）
2. **zcode 初判**：能——架构设计目标如此（宪法原理原文「拔掉 dsh 换 claude/codex/zcode 当大脑，EMC 不改一行代码」）·接触面唯一=MCP·换脑=配置级（注册+人设+启动三步）。诚实差异三点：驾驶舱体验/体积参数按 dsh 调/宿主小脾气。
3. **用户给料**：提供 Codex Harness 源码（D:\Github\codex-main.zip·7342 文件·codex-rs 为主）要求复判·并提出设想「**EMC 未来兼容多种 Harness 当大脑**」。
4. **zcode 源码勘察**（证据见 §二）——结论升级：源码级确认可行且更顺。
5. **用户问题②**：壳阶段（dsh 融入 EMC 底层后），3080 流式输出能搬进 EMC 对话框吗？Codex 呢？
6. **zcode 判断**：dsh=私有协议禁依赖+headless 无流式→**不该搬也不用搬**（壳阶段 EMC 自己长循环）；Codex=app-server 协议官方支持「自建 UI」→**可以且是正路**。
7. **用户反问③**：可我 EMC 现在就能流式输出 DeepSeek，背后是什么？
8. **zcode 核实**：EMC 自持流式管道（证据见 §三）——修正前判：EMC 已是带分阶段事件的迷你 agent 循环，与 3080 差距比想象小。
9. **用户令**：落盘全过程·发起「现阶段用 dsh 还是 codexh」讨论·发 Codex+Kimi。

## 二 证据清单（源码级·codex-main.zip 勘察）

### A · Codex Harness 的 MCP 客户端能力（工具面=与 dsh 对等）

| 证据 | 位置 | 对 EMC 的意义 |
|---|---|---|
| 双传输：`Stdio{command,args,env}` + `StreamableHttp{url,bearer,headers}` | `codex-rs/config/src/mcp_types.rs` McpServerTransportConfig | EMC 插座两种模式（stdio / --http 8600）**零适配** |
| per-server `startup_timeout_sec` / `tool_timeout_sec` | 同上 | dsh 侧踩过的冷启动 15-20s 超时坑在 Codex=配置项直接解 |
| MCP 大结果转文件机制 | `codex-rs/core/src/mcp_openai_file.rs` | 大 geojson 结果优雅转附件（dsh spill 崩溃同族问题在 Codex 侧有官方处理） |
| per-server 审批模式/并行声明/enabled/required | mcp_types.rs | 精细化宿主管控 |

接入配置预估（全部改动）：
```toml
[mcp_servers.emc]
url = "http://127.0.0.1:8600/mcp"   # 或 stdio: command="py", args=["tools/mcp_server_emc.py"]
startup_timeout_sec = 60
tool_timeout_sec = 120
```

### B · Codex Harness 的会话事件面（dsh 没有的分水岭）

| 证据 | 位置 | 意义 |
|---|---|---|
| 逐字流 `AgentMessageDeltaNotification` | codex-rs/app-server-protocol/schema/ | AI 回复打字机事件（=3080 体验的事件源） |
| 过程流 `CommandExecOutputDeltaNotification` / `ItemCompletedNotification` | 同上 | 命令输出流/条目完成 |
| 会话控制 Thread/Turn 全生命周期+Notification 体系 | 同上（164 个 MCP 相关 schema 文件） | 「自建 UI 驱动 Codex」官方路径（其 IDE 插件即此实现） |
| 官方 SDK：Python + TypeScript | sdk/python·sdk/typescript | 协议有包装层支持 |

### C · EMC 自持流式能力（关键修正性发现）

| 层 | 现状 | 实现 |
|---|---|---|
| 模型正文流 | ✅ | `ai_qa/llm.py`（MOD_LLM.F_001）直连 DeepSeek 官方 API（OpenAI 兼容 SSE）·stream=true 逐 token yield |
| 思考链流 | ✅ | 同上·`delta.reasoning_content` → kind='reason'\|'content'（V4 Pro 思考链） |
| 分阶段过程事件 | ✅ | `api/aiqa_routes.py /api/v1/chat` SSE 端点·前端 `ai_qa/api.js streamChat`：**diagnose / agent_step / answer / optimize** 四阶段 |
| 逐工具调用事件（名/参/果） | ◐ 通道在·粒度待细化 | agent_step 阶段已有 |
| 多步自主编排 | ◐ 单轮范式为主 | 范式体系（尺度→工具→出口卡）在 |

**要点**：EMC 的流式管道从头到尾零 harness 参与——模型供应商原生流式能力被 EMC 自持消费。harness 只是「编排层」的可替换选项；壳阶段补齐编排可视化=扩展现有循环（非从零造）。

### D · dsh 现状（对比基准）

- ✅ 纯净官方版 v0.1.1-rc.2·MCP 唯一接触面·18 工具消费实测通过（含真实分析+落图）
- ✅ 网页驾驶舱 3080（流式·用户明确喜欢「看着它干活」）
- ⚠️ 已知宿主坑：streamable-http 不自动重连（重启 MCP 须刷新页面）/冷启动超时（服务端预热补丁绕过）/工具结果缓冲小（200KB 硬顶为其定制·spill 曾崩）
- ⚠️ 无公开会话事件接口（web=私有协议·headless=无流式）——壳阶段对话接管无官方路径
- ✅ M1 配方已磨合成型（双 profile 四行 insert）

## 三 核心议题（请两组逐条表态）

**议题 0（总）**：现阶段（测试期·外置驾驶舱阶段）EMC 的外置大脑主选 **dsh** 还是 **Codex Harness**？还是双脑并行？各自给出推荐+理由+代价。

**议题 1 · 选型判据排序**：以下判据您如何排序/补充——①工具面成熟度（MCP 客户端稳定性）②驾驶舱体验（用户看 AI 干活）③与壳阶段路线的衔接（会话事件面）④双环境同步成本（M 配方）⑤宿主坑风险 ⑥与开发组工具链协同（Codex 已是执行手）。

**议题 2 · dsh 独有价值**：网页驾驶舱对演示/复测的价值是否无可替代？若转 Codex 为主，用户「看着 AI 干活+出图」的体验路径是什么（终端围观？IDE？还是提前做 EMC 对话框接管——那是否本就该是壳阶段的事）？

**议题 3 · Codex 接入风险**：从实现者视角评估——app-server 协议/SDK 的版本稳定性？MCP 客户端在 Windows 双环境的坑？skill 机制与 EMC 人设（身份卡）兼容？审批模式对只读 EMC 工具的打扰？

**议题 4 · 双脑并行 vs 单脑聚焦**：dsh=演示驾驶舱 + Codex=工程脑的并行方案，心智/维护成本是否值得？还是违反「接触面最小」精神？

**议题 5 · 对 ACP 契约批的影响**：若确认多脑路线，ACP 契约（四动词+事件流+状态对象·P2 后批）的事件流部分应以 Codex Notification 体系为参照定义——两组对 ACP 契约的 scope 建议。

**议题 6 · 迁移与回退**：M-codex 配方页（注册+人设+体检三题）预估半天 spike 是否成立？回退到 dsh 的成本？

## 四 主手初步意见（供挑战·非结论）

**倾向：现阶段 dsh 继续当主驾驶舱（体验最优·已磨合·M1 成型），Codex 启动「第二脑并行试点」（半天 spike：config 注册+人设搬迁+插座考试三题），用实测数据说话；壳阶段主力待试点结果+ACP 契约批后再定。**

理由：①现阶段的用户价值重心=复测演示（3080 体验不可替代）②Codex 的 app-server 优势要壳阶段才兑现·现阶段不增益 ③并行试点成本低（半天）且符合「先试点后迁移」纪律 ④避免未经验证就切主脑的回退成本。

反方观点（自录·供讨论方引用）：并行双脑=双份宿主坑跟踪+用户心智负担；若壳阶段终点本来就是 EMC 自持编排，第二脑试点可能提前回答「还需不需要外置脑」。

## 五 回应要求

- 各组落盘：`EMC-Harness选型回应_Codex-2026-08-22.md` / `EMC-Harness选型回应_Kimi-2026-08-22.md`（discuss/ 目录）
- 逐议题表态（支持/反对/有条件/替代方案）+ 理由 + 证据（可实读 codex-main.zip 或 EMC 仓代码）
- 零实施零 git 写（回应文档除外）·本地仓即最新零 pull
- 主手收口后出裁决表交用户拍板

> zcode 主手 · 2026-08-22 08:4x · 讨论发起·待 Codex/Kimi 回应
