# CB 记忆库（Catch-Ball Knowledge Base）

> 跨轮沉淀的 CB 专题知识库。**cb-journal = 按轮时序流水账；本文件 = 按主题蒸馏的复用原则。** 互补不重复。
> `/cb` 命令 step 1 载入、step 4 套用已知结论、step 6 追加新 learning。每条 learning 标 `← CB-NN` 溯源。
> 版本随 CB 轮次演进（CB-03 前据 CB-01/02 经验复盘修订，同 [RULES.md](RULES.md)）。
>
> **记忆共享（通则）**：本文件登记于 [docs/context-map.md](../context-map.md) + AutoMemory `MEMORY.md`（`cb-knowledge-base` 指针），与项目 AutoMemory 双向链接（§1/§2 内嵌 `[[name]]` = AutoMemory 条目名）。不孤岛。

---

## §1 承重红线清单（合并；/cb auto-flag 用）

> 项目方声明的非协商红线。SCAN 建议触碰 → /cb 自动 disagree（撞红线），不接受"简化"。
> 合并自 RULES §3.3 + 项目散落（CLAUDE.md rule 10 + AutoMemory）。

| 红线 | 来源 | 说明 |
|------|------|------|
| 决策追踪编号连续不跳号 | CLAUDE.md rule 10 / RULES §3.3 | 新 ID 经 `register_track_id` 连续分配；"取消编号连续/简化追踪"建议→拒 |
| diagnose prompt 永不动 | RULES §3.3 / [[emc-eval-empty-context-vs-runtime]] | Flash eval 路由依赖 diagnose prompt 完整性；分层/裁剪建议→撞红线 |
| 四态出口契约（success/gap/partial/answered） | RULES §3.3 / [[emc-tri-state-exit-contract]] | harness 代码强制终态；简化/合并出口→拒 |
| L0 走购买途径·sim 充分非风险 | RULES §3.3 / [[l0-acquisition-purchase-strategy]] | 勿把 sim/自采未贯通当风险（曾被我+SCAN 误判） |
| EMC 委托主 Toolbox 不自造 geo 端点 | [[emc-delegates-to-toolbox]] | density 等分析调 generateHeatmap/Grid/TerrainForAI，不自造 |
| aggregate 别名静默零（resolve_field_alias） | [[emc-aggregate-column-alias-silent-zero]] | 中文别名列聚合须按 role 解析实际列，否则 polarity_index 静默零 |

## §2 项目语境卡片（SCAN 不知的）

> 注入这些语境，避免 SCAN 基于文档推断运行时（CB-01 之训：把 AGENTS.md 理论模型当运行时）。

- **L0 获取 = 未来走购买途径**（非自采 Scrapy）；sim 当下有意为之且充分 → 数据管道成熟度评估勿把 sim 当缺陷。[[l0-acquisition-purchase-strategy]]
- **不派 subagent**（用户全局铁律）：AGENTS.md 8/9 Agent 是**概念框架非运行时机制**，主线程直接干 → 调用次数/SOP spawn 类建议常前提不成立。
- **4×5 = 归因落点矩阵（非指标分类清单）**：跨领域×要素多归属。勿用"官方指标完备性"质疑 4×5（错标尺）。[[project-design-philosophy]]
- **eval 空 context ≠ 运行时**（C6）：Flash eval 用 `build_diagnose_prompt('')` 空 context 模拟，不反映已加载层；路由分歧验路由须带 grounding 或 browser，别只信空 context eval。[[emc-eval-empty-context-vs-runtime]]
- **唯一真短板 = 前端测试薄**（34 JS 文件零单测）；非数据、非架构（数据管道 sim 充分、架构七层稳）。

## §3 SCAN 标尺纠正模式（SCAN 倾向 → 正确标尺）

> 每条 = 跨轮验证的 SCAN 评估倾向 + 项目方正确标尺。/cb step 4 遇匹配模式 → 套结论，不重推。

| SCAN 倾向 | 正确标尺 | 溯源 |
|-----------|---------|------|
| 基于 AGENTS.md 理论模型判运行时（算 SOP spawn 次数） | SOP spawn 前提误判（项目不跑 SOP spawn）；但**调用次数确实关键**——优化靠会话切分+精准读+大宗隔离（全局「调用次数优先策略」），非 SOP 合并 | ← CB-01（4 条高优 declined），CB-02 §0.2 确认；CB-03 后策略厘清 |
| 优化前不查活引用（直接建议 perf 改进） | 先 Grep/Read verify usage；死代码→退役非优化（CB-01 db.py 实为 executemany + 零引用） | ← CB-01 建议7 |
| 未察觉 MANIFESTO ↔ diagnose prompt 耦合 | MANIFESTO 分层破坏 Flash eval 路由完整性 → 撞承重红线 | ← CB-01 建议4，CB-02 §0.2 确认 |
| 完成度把"接口预留"计为"已实现" | 偏高；真实约 8 折（L3/L4 backend ⬜ 预留 ≠ 实现） | ← CB-01（90%→真实 75-80%），CB-02 折中 80% |
| 把 sim 数据/自采未贯通当风险 | L0 走购买、sim 充分 → 非风险 | ← CB-01 澄清（用户），CB-02 §0.2 认可 |
| 用"官方指标完备性"质疑 4×5 归因 | 4×5 = 归因矩阵（多归属）非指标清单（互斥穷尽）→ 错标尺 | ← 项目设计哲学（CLAUDE.md），CB 通用 |
| 把不同用途的 sim/工具脚本误判"功能重叠"→ 建议同退役 | 先查 docstring/原职责定用途；非真冗余不并退役（generate_test_data=L0 raw 全管线测试 vs sim_performance_data=L1/L2 demo） | ← CB-02 建议4 |

## §4 Decline 模式库（reason 类型 + 例）

> decline 时附 reason，保证跨轮一致。/cb step 4 disagree 项必落其一。

| reason 类型 | 含义 | CB 例 |
|------------|------|-------|
| **用错标尺** | SCAN 用了不适合项目的评价框架 | CB-01 MCP"应与 DeepSeek 匹配"（MCP provider-neutral）/ 官方完备性质疑 4×5 |
| **事实错误** | SCAN 描述与代码不符 | CB-01 db.py"用 iterrows 逐行插"（实为 executemany）/ CB-01"数据管道 90% 全实现"（L3/L4 ⬜） |
| **撞承重红线** | 建议触碰 §1 红线 | CB-01 MANIFESTO 分层（撞 diagnose 永不动） |
| **无消费方 wontfix** | 修复改动无活消费方 | CB-01 zonal_stats latent bug（n_dom/n_elem 无人从 trimmed 响应读） |
| **前提不成立** | 建议基于对项目运行方式的误判 | CB-01 调用次数优化（不派 subagent）/ CB-01 Reviewer+Tester 合并（同） |

## §5 轮次溯源索引

> 每轮 CB 一行摘要 + 指向 cb-journal 章节。

| 轮 | 日期 | SCAN | 综合分 | 关键产出 | cb-journal |
|----|------|------|--------|---------|-----------|
| CB-01 | 2026-07-18 | [SCAN_DeepSeek_01.md](SCAN_DeepSeek_01.md) | 7.6 | 删 5 僵尸（Streamlit/pydeck/db）/ geo_routes 三处清理 / sim 注册 / e2e seam 去生产化 / §0 任务树刷新 / **5 类 declined**（调用次数前提不成立等） | `## CB-01` |
| CB-02 | 2026-07-19 | [SCAN_DeepSeek_02.md](SCAN_DeepSeek_02.md) | 7.6（持平） | CB-01 回顾核验（agree 4 通过 / disagree 3 成立）/ 新发现 requirements 僵尸依赖 + range_selector 路径大小写 + AGENTS.md 8→9 漂移 / 10 条新建议待 `/cb 02` 反评价 | `## CB-02`（②③ 待填） |

---

## §6 Auto-Check 清单（/cb step 5 加载·数据驱动，CB-03 建议2）

每次 counter-evaluation 必须执行（可追加，不删除）：

1. **承重红线检查**：建议是否触碰 §1 任何红线？→ auto-disagree。
2. **核实再接受（verify-before-accept）**：agree 前是否已 grep/读代码核验 SCAN 的事实陈述？
3. **无消费者→wontfix**：涉及的功能/代码路径是否有活消费方？
4. **已知模式匹配**：是否匹配 §3 任何标尺纠正模式？→ 应用已知结论。

## 维护策略

- **pruning 触发**（CB-03 讨论2）：§3（SCAN 标尺纠正）>15 条 → 按"近 3 轮是否再触发"归档低频；§5（轮次溯源）>10 条 → 仅留近 5 轮 + milestone（首次/评分变 >0.5）；文件 >200 行 → 评估拆分。当前 ~80 行，无需 prune。
- **CB 节奏决议**（CB-03 讨论3）：三轮高频 CB（~30 小时）后转**低频维护模式**——每 5-10 个功能 commit 触发一次 SCAN（非每轮 CB 后即 SCAN）。hook detector 保留（仍提示新 SCAN），评估节奏放缓。

---

> **下次更新时机**：CB-04 前据 CB-03 经验复盘修订（同 RULES.md）。新 learning 由 /cb step 6 入库。
