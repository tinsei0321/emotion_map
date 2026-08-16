# EMC harness 架构借鉴 dsh（DeepSeek Harness）· 专题讨论底稿

> 整理：zcode组（ZCode + GLM 5.3）· 2026-08-16。性质：**专题讨论输入（用户已定另开会话深入讨论）·零实施**。
> 缘起：用户提出想法——「让 EMC 也用 harness+LLM+plugin 的形式运作，模仿 dsh 重构 EMC，是否能让 EMC 更智能、更灵活？」本底稿 = zcode 在线研读 dsh 核心文档后与 EMC 现状的对照梳理，供专题会话作讨论基础。
> dsh 研读范围（2026-08-16 在线）：README + `docs/architecture.md` + `docs/agent-lifecycle.md` + `docs/tool-execution-pipeline.md`。仓库：https://github.com/deepseek-ai/deepseek-harness（MIT·开发者预览·~124k stars·TypeScript+Python pnpm monorepo）。

---

## 〇 一句话结论

**EMC 已经是 harness+LLM+plugin 形式**——CLAUDE.md「Smart Agent + Dumb Tool + 确定性编排器」内核就是该模式的领域定制版（harness.js 字面同名·19 契约工具·FC+finalStep 双 LLM 端），**「重构为该形式」的前提不成立**；真正有价值的是**三点定向借鉴**（session log 可重放 / 守卫管线化 / 契约全自动派生）+ 一条条件性借鉴（CPD 复活时借 delegated turn 语义）；明确反对换框架、反对开放 agent loop 替换确定性编排、反对推翻重写。EMC「不够智能」的真实杠杆在四处痛点（知识库薄/参数填充/假结论/多步链弱），无一需要换架构。

---

## 一 dsh（DeepSeek Harness）是什么

**定位**：DeepSeek 开源的通用 agent harness（智能体运行框架），口号「Everything is a Plugin」，基于 Cordis 框架（论文《A Programming Paradigm for Spatiotemporal Composability》），开发者预览阶段、迭代快有破坏性变更。

### 四支柱（四份文档研读摘要）

1. **一切皆插件（Cordis）**：插件向共享 context 贡献 services / typed events / reversible effects；**无特权核心**——模型适配器、工具注册表、会话日志、连 agent loop 本身都是可替换插件。运行时由 Profile（命名组合）→ Bundle（Cordis config 层）→ patch 层叠组装（`dsh --profile web --dump-config` 可查看插件树）。
2. **开放式 agent loop**：**turn** = 零或多个 **step**；**step** = 一次模型请求 + 其工具调用。事件流：`turn/start` → `agent/pre-step`（可权威拒绝/改写）→ prompt 组装 + tool schemas → `llm/stream` → `assistant/message` → `tool/call` → 执行管线 → `tool/result` → `step/end` →（有新输入则下一 step）→ `agent/turn-stopping` → `turn/end`。LLM 自主决定调多少工具、何时停。
3. **Session log 单一事实源**：核心不变量「**Model-visible means logged**」——进入模型请求的任何内容都必须能从 session event log 重建（运行时有断言校验）；`deriveMessages()` 从日志投影模型历史；fork/resume/transcripts/持久化全部派生自该流。
4. **工具执行流水线**：`tools/pre-execute` waterfall（权限 allow/deny/ask + `ctx.approval` 审批·不可用即拒绝）→ Monotonic guards（不可重排守卫·只能 deny/abstain）→ `tools/execute`（超时/重试横切）→ 文件系统门（`fs/write-intent`）→ `tools/post-execute`（**accept / block / replace / add-context** 四态）→ 结果规范化 → `tool/result`（lossless JSON·唯一面向模型的产出）。

其他要点：capability seam 三元组（Service Definition / Provider / Consumer——换 provider 即可把 Bash/PTY/LSP 整体搬进远端 sandbox）；compaction（上下文压力检测→工具结果修剪→摘要）；`ctx.llm` 适配器缝隙（新模型 provider 注册即接入）；子 agent 统一 provider 接口（fresh child 到 delegated turn）。

---

## 二 对照：EMC 现状已是 harness+LLM+plugin（代码实锤）

| dsh 概念 | EMC 现状对应 | 状态 |
|---|---|---|
| harness 运行框架 | `frontend/js/ai_qa/harness.js`（确定性编排器·不调 LLM 不推理·三态出口代码裁定） | ✅ 已有·字面同名 |
| LLM 端 | diagnoseStep（FC 意图理解+工具选型）+ finalStep（LLM 综合表达）+ knowledge_qa 路径 | ✅ 已有 |
| plugin/toolbox | 19 个契约工具（`ai_qa/tool_contracts.py`）+ geo 工具箱 `generate*ForAI` 入口 | ✅ 已有 |
| 工具注册进 prompt | TOOL_CONTRACTS（单一源）→ SKILL_DEFS 镜像 → prompts 派生；P0-2 已真身解析（当场抓到 compare 漂移=机制生效实证） | ✅ 已有·派生自动化进行中 |
| 执行守卫/审批 | 四态出口契约 + CB-39 D1 结论白名单（裁定中） | 🔄 起步 |
| session log 可重放 | ❌ 无——trace.log 只记后端决策；前端 prompt 组装（ctx.context 拼接/formatRegistry() 注入）不可重放 | 缺口·借鉴点 1 |
| 子 agent / 多步委派 | CPD 引擎（plans 接口预留·CB-10 确认空骨架） | 缺口·条件性借鉴 |

**结论**：用户所说「让 EMC 用 harness+LLM+plugin 形式运作」——EMC 已经在用，这是 CLAUDE.md 内核（Smart 聪明只在两端 / Dumb 执行最笨最稳 / 编排器确定性）的设计本意。问题不在形式，在细节质量。

---

## 三 关键差异：通用 harness vs 领域 copilot（不是先进 vs 落后）

| 维度 | dsh | EMC |
|---|---|---|
| 用户 | 开发者（会改插件的人） | 规划师/住建局（非开发者） |
| 任务空间 | 开放（任意任务·文件/shell/代码） | 收敛（城市体检/更新问答+空间分析） |
| 灵活来源 | LLM 自由循环（turn/step 到无事可做） | 扩工具面+扩范式映射（内核推论：加能力=加 dumb tool+编排器登记） |
| 稳定来源 | 沙箱+守卫+审批门 | 确定性编排器+契约单一源+守卫 |
| 技术形态 | TypeScript monorepo + Cordis 依赖注入 | JS 单页 + Python 后端·零框架 |

**EMC 刻意不采用开放式自由循环的病史背书**：
- **B001 多要素推理死循环**（CB-09）——「让 LLM 边想边做」的病，修法是 M1-M3 契约+指引收敛，不是更自由的循环；
- **B003 LLM 推理螺旋耗时异常**（CB-09·PERF）——同族；
- **CB-08 实测**：FC 工具选型 100% 准确（12/12），**瓶颈在参数填充**（buffer.center / overlay.layer_a,b 缺）——「不够聪明」不是架构问题；
- **CB-22 三支柱教训**：灵活性放错地方（曾砍 LLM 支柱走确定性拼列表）被用户人工验证否定。

对 EMC 的非开发者用户，「稳定压倒灵活」是产品决策不是技术妥协。

---

## 四 借鉴清单（建议编号 G6-G8·入 CB-40 缺口清单候选）

| # | 借鉴点 | dsh 原型 | EMC 落法 | 价值 | 量级 |
|---|---|---|---|---|---|
| G6 | **Session log 可重放**（最优先） | 「Model-visible means logged」不变量 + `deriveMessages()` 投影 | 前端 turn 事件化（user/diagnose/tool/final 全记日志）→ eval 从日志重放**真实上下文** | 直接治「eval 空 context 不反映运行时」老病（CB-01 C6）·三支柱 eval 质量的地基 | 专题设计 + 1-2d |
| G7 | **守卫管线化** | `tools/post-execute` waterfall（accept/block/replace/add-context 四态） | 把 CB-39 D1 结论白名单**泛化**为系统性 post-execute 管线：降级/改写/拦截统一挂载点 | B002/B004 类修复的终态机制·未来所有诚实度守卫的插槽 | 0.5-1d（D1 落地后顺势） |
| G8 | **契约派生全自动** | capability seam 三元组（定义/实现/消费） | P0-2 走完下半程：prompt 工具描述、GEO_TOOL_CATALOG 全部从 tool_contracts 自动派生·人工同步纪律退位 | 铁律 11 的机制化终态·消灭三处同步漂移类 bug | 0.5-1d |
| G9（条件） | **CPD 复活借 delegated turn** | 子 agent 统一 provider（fresh child / delegated turn） | 若 CPD 多步引擎复活（plans 空骨架·CB-10），借 dsh 语义设计 plans 接口而非从零发明 | 多步链能力（EMC 四痛点之一） | 随 CPD 排期 |

## 五 反对项（明确不做·红线级）

1. **不换 Cordis / 不做运行时插件化**：dsh 的「一切皆插件」是为「产品被开发者改造」设计；EMC 是单一演示产品，运行时可替换性=纯过度工程（引入 monorepo+依赖注入框架+学习成本，收益≈0）。借「注册表模式」，不借「运行时可替换一切」。
2. **不用开放 agent loop 替换确定性编排**：撞内核铁律 3（编排器确定性）+ B001/B003 病史 + 可测性（Dumb 纯函数才可单测·KNOWLEDGE「唯一真短板=前端测试薄」下更不能牺牲可测性）。
3. **不推翻重写**：CLAUDE.md 明言内核「成熟实现·不需推倒重来」。

## 六 「更智能、更灵活」的真实杠杆（架构之外·按证据）

1. **知识库薄**（约 30%·体检域仅 15 条 fact）——CB-39 B/C 线正在补；
2. **参数填充 few-shot 不足**（CB-08 结论·方向已定未深做）；
3. **finalStep 假结论伤信任**（B002/B004·CB-39 D1 白名单修）；
4. **多步链弱**（CPD 空骨架·对应 G9）。

四处无一需要换架构；重构成 dsh 式一个都解决不了，反而把推理螺旋病请回来。**灵活性的正确打开方式 = 扩工具面 + 扩范式映射**（内核推论已写），不是换循环模式。

---

## 七 专题讨论议程建议（供新会话）

- **议题 1（G6）session log 设计**：事件 schema（对齐 dsh 的 user/assistant/tool/turn 事件族？）、与后端 trace.log 的关系（合并 or 双轨）、eval 重放路径（黄金集从日志重建 context）、隐私红线（session 内数据脱敏）。
- **议题 2（G7）守卫管线**：D1 白名单落地形态（CB-39 现方案）→ 管线化改造的接口设计（守卫注册表/执行顺序/四态语义）；与降级体系（三级降级）的合并关系。
- **议题 3（G8）契约派生**：P0-2 已做 SKILL_DEFS 真身解析——剩余派生面清单（prompts 工具描述/GEO_TOOL_CATALOG/前端 Tool 面板）；派生失败的 CI 红灯设计。
- **议题 4（G9）CPD 复活**：是否排期；若排期，delegated turn 语义下的 plans 接口设计（CB-10「复活须同步恢复 plans 产出指令」约束）。
- **议题 5（排期定位）**：G6-G9 与 CB-40 G1-G5（出向文件级/前端测试/持续数据流/知识库更新/时间轴）的合并排序——一张总优先级表。
- **红线重申**：diagnose prompt 永不动（KNOWLEDGE 承重红线）；编排器确定性；契约单一源；**本轮零实施**——讨论清楚出方案稿，用户拍板后走 CB 实施。

## 八 待用户拍板的决策点

| # | 决策 | 选项 |
|---|---|---|
| D1 | G6-G9 是否采纳为 CB-40 缺口清单新条目 | 全收 / 部分收 / 独立专题轮 |
| D2 | 专题讨论产物形态 | 讨论纪要+方案稿 / 直接出实施计划（CB-41 预检） |
| D3 | G6 session log 的技术选型预研 | 专题内定 / 先 spike 后定 |

---

> 附：本底稿讨论发生在 CB-39 B/C 线实施期间（并行·不阻塞）；CB-40（EMC 现状与目标差距）讨论同时进行中——G6-G8 与 CB-40 G1-G5 的排序合并在 CB-40 收敛或本专题收敛时统一裁定，勿重复开轮。
