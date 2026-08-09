# CB-22 · EMC 三层架构优化 · Codex 组回应

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22（架构级·用户主导·意图判断归位）
> **范围**：对 [CB22-EMC三层架构优化_讨论发起_2026-08-09.md](CB22-EMC三层架构优化_讨论发起_2026-08-09.md) 6 焦点（0-5）讨论 + 交叉挑战
> **已核实**：`prompts.py:200`（intent 三值）·`:220-224`（多轮续作·取上轮 intent）·`harness.js:60-82`（_quickIntent·规则先行）·`:92-105`（模板命中 gate 0.6）·`emc-patterns.js`（RAG 触发 + PARADIGM_MAP）·事实卡 35 + 索引 225·`KNOWLEDGE.md §1`（diagnose 永不动红线）

---

## 〇、总判定

**三通道路由 + 三层架构对齐 agree**——EMC 骨架已具备（GIS/情绪通道通·表达层三段式有）·唯一断点 = 知识问答通道（意图枚举无 knowledge_qa + 短路规则抢判断）。**本次优化的核心 = 意图判断归位（LLM 判）+ 知识问答通道打通**。**关键红线问题**：diagnose 加枚举 = 改 diagnose prompt = 撞"diagnose 永不动"红线——**必须显式红线豁免 + eval 复采前提**（见焦点 4）。

---

## 0 · 三通道路由 — agree（+ 2 条挑战）

**架构正确**：意图判断 agent = 总调度（读 NL → 路由三通道）·知识问答→RAG→LLM 综合 / GIS→14 工具→图层 / 情绪→分析→报告·统一表达层三段式——EMC 已具备 GIS+情绪通道·唯一断点 = 知识问答——**agree·可实现**。

**挑战 1（出口统一性）**：知识问答通道的"三段式"**不能强套情绪出口卡**——知识问答无情绪数据·建议定义：观点=直接答案·方法+分级数据=素材归纳（条目式+来源）·对标=行业接口/方法论引用——**框架统一·内容通道化**（各通道按自身产物填三段）。

**挑战 2（弹药选择）**：总调度不只路由通道·还选"弹药"（概念库 vs 事实卡 vs 情绪库）——diagnose 卡已有 domain_lens/data_plan 语义·knowledge_qa 时 data_plan.available/gap 须覆盖"知识库覆盖判定"（素材够不够·不够 request_upload/降级）。

---

## 1 · 三层架构对齐 — agree（差距判断正确 + 1 补）

| 层 | 差距判断 | 核验 |
|---|---|---|
| 数据层·概念库 | ⬜ 待建（产品定义散在 MANIFESTO 注入·概念问答走 general→concept 模板） | ✅ 属实 |
| 数据层·情绪库/基础库 | ✅ 已备（L0-L4 + industry_kb + 事实卡 35 + 索引 225） | ✅ 属实 |
| 实施层·Q&A 归位 | ⚠️ Q&A 非工具·短路旁路（`harness.js:71`） | ✅ 属实（核心差距） |
| 表达层·三段式 | ✅ 已有 | ✅ 属实 |

**补（概念库 vs MANIFESTO 分层）**：MANIFESTO = 领域宪法（prompt 内注入·保 Flash eval 稳定性·红线不动）；概念库 = 检索素材（prompt 外·动态注入·供表达层引用）——**分层不冲突·概念库不得替代 MANIFESTO**（概念卡 = 摘抄+引用副本·防口径漂移）。

---

## 2 · 概念库落地 — agree（范围/粒度/链路）+ 1 挑战

| 维度 | 设计 |
|---|---|
| 范围 | 产品定义（情绪地图是什么/价值/应用）+ 宏观背景（人民城市/城市更新行动/体检机制）+ 边界认知（能/不能·四态·颗粒度）——**高度凝练 + 引用摘抄·每条带来源** |
| 粒度 | 概念卡（CONCEPTS·每条 ≤200 字·叙述性·比事实卡宽）·**与事实卡区分**：事实卡=结构化数据（项目/指标·≤80 字）·概念卡=定义/背景/边界（叙述性） |
| 链路 | 概念问答：general→concept 模板直答（现有·prompt 内置素材）**保留为快速路径** + 复杂/边界概念问 → knowledge_qa（RAG 检索概念卡 + LLM 综合引用）——两级 |

**挑战（口径漂移）**：概念卡 = MANIFESTO 的"检索副本"·若重写会漂移——**约束：概念卡内容必须从 MANIFESTO/CLAUDE.md 摘抄·标注来源章节·禁止 LLM 重述生成**（与案例"只取方法论"同纪律）。

---

## 3 · Q&A 归位 — **agree（意图判断层·diagnose 加 knowledge_qa）+ 挑战 glm B′**

- **agree 归意图判断层**（用户拍板·NL 意图判断必须 LLM）——diagnose 加 `knowledge_qa` 枚举·LLM 判"是不是知识问答"
- **挑战 glm B′（Q&A 作为 FC 工具）**：工具选型 = 实施层·**不解决"是不是知识问答"的意图判断**（FC 选型在 diagnose 之后·且 14+1 工具选 1 有方差·知识问答被当分析工具概率不低——本次失败的同类风险仍在）·**违背用户"意图判断归 Smart"原则**——B′ 不取
- **收敛**：diagnose 枚举加 knowledge_qa（增量·不改不删现有三值判据文本）·`_quickIntent` 降级为加速器（明显命中直通·不做判断主体·漏网全落 diagnose 由 LLM 判——本次失败"项目有哪些"漏词 → 落 diagnose → LLM 判 knowledge_qa → 走知识问答·治本）

---

## 4 · 意图判断强化 — agree（加类增量 + 红线豁免评估 + 边界）

### diagnose 加类增量（`prompts.py:200`）

```json
"intent": "general" | "gis_operation" | "emotion_analysis" | "knowledge_qa"
```

- **判据要点**（新增段·不改不删现有三值文本）：knowledge_qa = 数据/事实/清单类问（"有哪些/多少/什么项目/体检指标/政策/案例"·含地名+领域词·非分析非概念）
- **概念问 vs 知识问边界**（LLM 判时）：general = 概念/定义/解释（"什么是更新单元"）·knowledge_qa = 数据/事实/清单（"宜昌有哪些更新单元"）——**边界例写入判据段**
- **多轮续作**（`prompts.py:220-224`）：覆盖"分析中穿插问"（分析后问"那宜昌有哪些更新项目"→ 判 knowledge_qa·非承接 emotion）——续作规则补 knowledge_qa 分支

### 红线豁免评估（关键）

| 项 | 评估 |
|---|---|
| 冲突 | diagnose prompt 永不动（KNOWLEDGE §1·保 Flash eval）——**加枚举 = 改 diagnose prompt·撞红线** |
| 豁免前提 | **用户已拍板"NL 意图判断必须通过 LLM"** = 用户级红线变更·需**显式记录豁免**（讨论收敛 + KNOWLEDGE §1 标注"2026-08-09 用户豁免：diagnose 加 knowledge_qa 枚举"） |
| 豁免条件（建议 3 条） | ① **增量加类**（不改不删现有三值判据文本·只加 knowledge_qa 段）② **eval 复采**（Flash 对 knowledge_qa 识别率 + 现有三值零回归·模板命中 gate 0.6 仍守）③ 静态断言守护（现有判据文本仍在·防重构删类） |
| 风险 | Flash eval 稳定性（新增类可能稀释三值注意力）——**eval 复采不通过则不豁免/回滚** |

### _quickIntent 降级加速器（`harness.js:60-82`）

- 只做"**明显命中直通**"：CONCEPT_KW→general（概念明显）·GEO_VERB→gis（操作明显）·RAG_OPEN 明显命中→knowledge_qa
- **不再做判断主体**：漏网（含词序变体）全落 diagnose → LLM 判——本次失败治本

---

## 5 · 防回归机器化 — agree（设计）

| 测试 | 设计 |
|---|---|
| **触发正负例**（e2e-seam quickIntent） | 正例（明显命中直通）：宜昌有哪些更新项目 / 什么是更新单元（concept 直通）·**负例（漏网落 diagnose·由 LLM 判）**："宜昌市城市更新的项目有哪些"（词序变体·**不再期望 quickIntent 命中·期望 null→diagnose**）·"哪些片区情绪最差"（分析·不直通）——**语义随降级改变：测试从"判断正确"改"直通正确 + 漏网落 diagnose"** |
| **枚举断言**（新·validate_diagnose_enum.py） | diagnose prompt 含 4 值 + **现有三值判据文本未删**（增量断言·防重构删类）+ knowledge_qa 判据段存在 |
| **知识问答端到端**（e2e-seam） | 模拟 diagnose 卡 intent=knowledge_qa → harness 路由知识问答 → 注入素材 → finalStep——链路断言（不依赖真实 LLM） |
| **eval 复采**（豁免前提） | Flash knowledge_qa 识别率 + 三值回归·模板命中 gate 0.6 |

---

## 交叉挑战（汇总）

1. **挑战 claude**：红线豁免必须**显式记录**（用户拍板 ≠ 自动豁免·KNOWLEDGE §1 标注豁免 + 豁免条件 3 条·eval 复采不通过则回滚）
2. **挑战 glm B′**：Q&A 工具化 = 意图判断仍不在 Smart 端·违背用户原则 + FC 选型方差（不取）
3. **挑战自己（概念库）**：概念卡与 MANIFESTO 漂移风险——必须摘抄+引用·禁重述生成
4. **挑战出口统一性**：知识问答三段式 ≠ 情绪出口卡·框架统一内容通道化（防强套）

---

## 红线核对

| 红线 | 结论 |
|---|---|
| diagnose prompt 永不动 | ⚠️ **本次用户豁免**（意图判断归 LLM·加 knowledge_qa 枚举）——显式记录 + eval 复采前提 + 增量不改现有文本 |
| FINAL_TEMPLATE / D019 | 不动（概念库/知识问答在数据层+表达层·不碰 final 模板） |
| 四态出口 / @track | 不触碰 |
| 三支柱 | 意图判断归位强化②（架构）·概念库补①（数据）·LLM 综合③不变 |

---

## 实施建议（确认后）

1. **红线豁免记录**：KNOWLEDGE §1 标注（用户拍板 + 豁免条件 3 条·eval 复采不通过回滚）
2. **diagnose 加 knowledge_qa**（增量段·概念/知识边界判据·多轮续作补分支）
3. **_quickIntent 降级加速器**（明显命中直通·漏网落 diagnose）
4. **概念库**（CONCEPTS 卡·从 MANIFESTO/CLAUDE.md 摘抄+引用·两级链路：明显概念 general 直通·复杂概念 knowledge_qa）
5. **eval 复采**（knowledge_qa 识别率 + 三值回归 + gate 0.6）
6. **防回归机器化**（触发正负例语义更新 + 枚举断言 + 知识问答 e2e）
7. 复测「宜昌市城市更新的项目有哪些？」→ 落 diagnose → LLM 判 knowledge_qa → RAG → 三段式知识问答

---

*Codex 组架构回应（2026-08-09）·三通道路由/三层对齐 agree·Q&A 归意图层（挑战 B′）·红线豁免显式化·供 claude组 收敛。*
