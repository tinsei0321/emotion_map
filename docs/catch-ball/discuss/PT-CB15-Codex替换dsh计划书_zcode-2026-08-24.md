# PT-CB15 · Codex Harness 替换 dsh 计划书 · CB 讨论发起（zcode·2026-08-24·待三组回应后收敛）

> **用户令**：写一份替换成 Codex 的计划书·Kimi/claude/Qoder 三组进 CB 联合讨论·zcode 收敛定稿·Qoder 执行。
> 性质：**实施计划书+CB 讨论发起**——非纯讨论·收敛后即开工（Qoder 已预定为执行方）。

---

## 一 白话摘要（零术语·按 AGENTS 3b）

**目标**：把 EMC 的「外聘主治医生」从 dsh 换成 Codex——因为 Codex 有官方的「视频通话」能力（流式输出+多轮对话），而 dsh 只有「写信问诊」（一问一答·无流式）。换完后您在 EMC 自己的窗口里就能看到完整的 Harness 体验。

**为什么现在做**：①您裁定「契约成熟后再测 Codex」——现在契约（换脑插座+事件协议）刚建成·时机到了 ②您明确说「要测完整的 Harness 在 EMC 里」——Codex 是唯一能提供完整体验的路径 ③dsh headless 版（T7 已可用）作为保底不删除。

**怎么做**：分三步——第一步「接入」（让 Codex 当 EMC 背后的大脑·跑通分析+出图）·第二步「流式」（在 EMC 窗口看到逐字输出）·第三步「验收」（对照 dsh 版·同等质量+体验升级）。

---

## 二 背景

### 2.1 为什么替换

| | dsh | Codex Harness |
|---|---|---|
| 流式输出 | ❌ headless 无流式（一次性全文） | ✅ app-server 协议有逐字流 |
| 多轮对话 | ❌ headless 单问 | ✅ Thread/Turn 全生命周期 |
| 自建 UI 接口 | ❌ 私有协议（宪法禁依赖） | ✅ 官方 SDK（Python+TS） |
| 工具调用（MCP） | ✅ streamable-http | ✅ stdio + streamable-http |
| 超时配置 | ⚠️ 需服务端预热绕过 | ✅ per-server `startup_timeout_sec`/`tool_timeout_sec` |
| 大结果处理 | ⚠️ 曾 spill 崩溃（已修） | ✅ 大结果转文件机制 |
| 现状 | headless BA 已通（T7） | 未接入·源码勘察+契约已备 |

**结论**：Codex 在「流式+多轮+官方接口」三个关键面全面优于 dsh——正是「EMC 壳里完整 Harness 体验」的解锁钥匙。

### 2.2 已有资产（不推倒重来）

| 资产 | 状态 | 复用度 |
|---|---|---|
| BrainAdapter 契约（S1） | ✅ 已定义降级/全量双形态 | 全量形态=本次实施对象 |
| ACP v1.1 事件协议 | ✅ 五族+schema 校验器 | Codex 事件→ACP 转换层 |
| 壳对话框架（S3） | ✅ 前端事件化完成 | 直接消费 Codex 流式事件 |
| MCP 18 件工具 | ✅ 全通（F_021-F_041） | Codex 经 MCP 消费·零改动 |
| dsh headless BA | ✅ 已通（T7） | 保留为保底引擎·不删除 |
| 三引擎切换 | ✅ ?engine=light\|dsh\|mock | 新增 ?engine=codex 第四态 |

---

## 三 实施计划（三步走·预估 3-4 天）

### 第一步：接入（~1 天）

| # | 任务 | 规格 |
|---|---|---|
| C1 | Codex MCP 注册 | config.toml 加 `[mcp_servers.emc]` 段——stdio（`py tools/mcp_server_emc.py`）或 HTTP（`http://127.0.0.1:8600/mcp`）·`startup_timeout_sec≥60`·`tool_timeout_sec≥120` |
| C2 | EMC 人设迁移 | dsh profile 的 EMC 身份提示词 → Codex AGENTS.md 常驻段+身份卡 skill（双层结构·Codex 特有） |
| C3 | 工具验证 | 18 件 MCP 工具全过——`list_data`→`rag_query`→`zonal_stats`→`render_spec` 四步链+落图 |
| C4 | 审批配置 | EMC 只读面（工具全只读）→ per-server 免审批·写面（render_spec）单独收紧 |

### 第二步：流式+壳接入（~1.5 天）

| # | 任务 | 规格 |
|---|---|---|
| C5 | Codex app-server 客户端 | Python subprocess 或 SDK 连接——`codex exec --json` 事件流解析（JSONL：agent 轮次/工具调用/消息增量） |
| C6 | 事件转换层 | Codex JSONL 事件 → ACP 五族事件映射（msg.delta←token流 / tool.begin←工具调用 / tool.end←工具结果 / error←异常） |
| C7 | brain-adapter-codex.js | 仿 brain-adapter-dsh.js——open→Codex 子进程/连接·流式事件→ACP 通道·close→清理 |
| C8 | 引擎第四态 | panel.js `?engine=codex` 分发——与 light/dsh/mock 并列 |

### 第三步：验收+对拍（~1 天）

| # | 任务 | 规格 |
|---|---|---|
| C9 | 单引擎验收 | ①流式输出可见（逐字打字）②工具调用过程可见③落图正常④多轮对话（上下文延续）⑤错误语义化降级 |
| C10 | 双引擎对拍 | 同题 10 问·dsh vs Codex——①答案质量同等级（口径/来源/正确性）②出图一致 ③速度对比 ④流式体验差异记录 |
| C11 | dsh 保底验证 | ?engine=dsh 路径零退化（dsh 不删·可随时切回） |
| C12 | 验收报告 | 用户故事达成度+对拍数据+切换操作指引 |

### 红线（全程）

1. EMC MCP 工具面零改动（18 件不动）；
2. dsh 引擎路径零退化（保留保底）；
3. 轻量引擎默认路径零退化；
4. RAG 96.7% 零退化；
5. Codex 配置全部仓外（~/.codex/·不入 git·配复刻清单）；
6. 纯净官方版纪律不破（Codex 不改源码·只配置）。

---

## 四 讨论议题（三组逐条表态·D1-D6）

| # | 议题 | 主手倾向 |
|---|---|---|
| D1 | 接入传输方式：stdio vs streamable-http？ | **HTTP**（MCP 8600 常驻已就绪·stdio 每次冷启动慢）·但 stdio 免端口依赖——两组评估 |
| D2 | app-server 客户端：subprocess `codex exec --json` vs 官方 SDK（Python/TS）？ | **subprocess 优先**（SDK 0.0.0-dev 无语义化版本·锁 commit 的 schema 类型作对冲）·Codex 源码已勘察确认可行 |
| D3 | 人设双层结构：AGENTS.md 常驻段+身份卡 skill——内容从 dsh profile 怎么拆？ | dsh 的 system prompt → AGENTS.md（纪律+铁律常驻）+ 身份卡 skill（EMC 身份触发注入）·Kimi 产品视角评估 |
| D4 | 流式体验：Codex JSONL 的 token 增量 → ACP msg.delta——延迟/粒度/丢包怎么处理？ | 批量转发（50ms 缓冲）+ seq 单调保证——Qoder 工程视角评估 |
| D5 | 双引擎并存策略：dsh 保留为保底 vs 用 Codex 后逐步退役 dsh？ | **并存**（?engine 四态常驻·用户随时切）——退役另议 |
| D6 | 对拍标准：C10 的「同等质量」怎么量化？ | 口径标签一致率/出图一致率/答案事实核查（抽 3 题人工核）——claude 正确性视角设计 |

---

## 五 CB 讨论流程

| 步骤 | 内容 | 产出 |
|---|---|---|
| 1 | zcode 出计划书（本件） | ✅ |
| 2 | 三组各自回应（Kimi 产品/claude 正确性/Qoder 工程） | 回应文档×3 |
| 3 | zcode 收敛（冲突消解+裁决表） | 收敛文档 |
| 4 | 用户终裁 | 终裁 |
| 5 | **Qoder 执行**（收敛定稿即为任务书） | 实施+验收 |

**分组重点**：
- **Kimi**（产品/用户视角）：D3（人设拆分·用户体验影响）+D5（并存策略·用户操作复杂度）+流式体验的用户期待
- **claude**（正确性/测试视角）：D6（对拍标准量化）+C9-C12 验收口径+测试覆盖设计
- **Qoder**（工程视角）：D1/D2/D4（技术选型+流式实现）+C5-C8 实施细节+风险预判

**回应要求**：一句话结论+D1-D6 逐条（agree/disagree/partial+证据）+实施建议补充+纠错义务+四档裁决（对三步走 C1-C12）。产出含白话摘要段。

**回应文件**：`docs/catch-ball/discuss/PT-CB15-Codex替换计划回应_{组名}-2026-08-24.md`

---

> zcode 主手 · 2026-08-24 · PT-CB15 计划书+CB 发起·待三组回应后收敛定稿·Qoder 执行
