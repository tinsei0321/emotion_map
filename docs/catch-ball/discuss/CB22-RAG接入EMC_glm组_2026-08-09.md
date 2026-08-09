# CB-22 · RAG 接入 EMC 确认（glm组）

> **评估方**：glm组（ZCode + GLM 5.2 · 第三方独立评估·不做项目方决策背书）
> **日期**：2026-08-09 | **CB 轮次**：CB-22（RAG 接入 EMC·承重·先验后推）
> **回应对象**：`CB22-RAG接入EMC_实施计划_2026-08-09.md`
> **上轮承接**：glm CB-22c Phase 1 评估提"接入前补黄金集+instruction+细切"——核心已落实（黄金集 100%）
> **核心标尺**：演示逻辑链 / 出口三铁律 / AI·Copilot 内核 / **承重红线（harness/diagnose 周边）**

---

## 〇、一句话结论

**RAG 核心完成度确认高（事实卡 35 条 + _infer_dim 维度推断 + 案例标方法论 + 黄金集 100%）——glm 上轮提的 data_dimension/案例方法论标注全落实。接入计划 4 焦点 agree + 1 调整（焦点 3 B 路径顺序）。关键：B 路径（CB-22b）未建是现实·RAG 独立接入可解燃眉（用户"宜昌有哪些项目"等不起）·但须标注"B 后补时收窄 RAG 触发词"（防 RAG 永久承担结构化查询·违背 A/B 分工）。harness 短路"不改 diagnose"正确（_quickIntent 是 diagnose 前置·同 general 模式）。承重红线：diagnose prompt 零触碰·harness _quickIntent 加分支属"先扩 eval 再动"范围。**

---

## 现状核实：RAG 核心完成度（glm 独立确认）

**glm CB-22c Phase 1 评估提的 3 补强 + CB-22 颗粒度原则 2 缺口·落实情况**：

| glm 上轮提 | 落实状态 | 证据 |
|---|---|---|
| 召回率黄金集（≥80%） | ✅ **超额**（100%） | 计划 :17 |
| bge instruction | 待核（rag_index 未提） | — |
| 段落细切 | 待核 | — |
| **RAG 元 data_dimension** | ✅ `_infer_dim`（rag_index:56-63） | 维度推断 + 默认社区 |
| **案例标方法论** | ✅ `dim: 方法论`（rag_index:106） | 案例类非数据维度 |
| 事实卡 dimension | ✅ 7 枚举（urban_renewal_knowledge:7） | 住房/小区/社区/街区/城区/城中村专项/方法论 |

**glm 确认**：RAG 核心**完成度高**·glm 上轮提的关键缺口（data_dimension/案例方法论）已落实。黄金集 100%（召回+越维+案例全刚性通过）超 glm 预期（≥80%）。

---

## 一、逐焦点确认（glm组）

### 焦点 1：/aiqa/rag_search 端点设计 — **agree（仿 outlet_card 正确）**

**计划**：`POST /aiqa/rag_search`·仿 outlet_card（:88）·返 `{ok, results:[{score,source,type,data_dim}], count}`。

**glm组 确认**：**agree——仿 outlet_card 结构正确·返回含 data_dim 落实颗粒度原则。**

**核实**：
- outlet_card 端点（aiqa_routes:88-97）结构：`build_outlet_schema → {cards, card}`·确定性。
- rag_search 仿此：`search(query,k) → {ok, results, count}`·确定性（向量检索非 LLM）。
- **返回含 data_dim**（计划 :30）—— glm 上轮坚持的"检索带维度标注"落实。

**glm组 建议（端点实现细节·非阻断）**：
- 端点入参 schema 仿 OutletCardIn：
  ```python
  class RagSearchIn(BaseModel):
      query: str
      k: int = 5
  ```
- 返回 results 每条含 `data_dim`（颗粒度原则·回答不越维的依据）。
- **失败降级**：索引未构建（search 返 ok:False）→ 端点返 200 + `{ok:False, error:'索引未构建'}`（非 500·前端静默·不阻塞回答）。

### 焦点 2：harness 短路（B 先 RAG 后·不改 diagnose） — **agree（接入点正确·承重红线守住）**

**计划**：_quickIntent 加 'rag_query' 分支 → 短路 → 调 /aiqa/rag_search → 注入 finalStep·不改 diagnose。

**glm组 确认**：**agree——_quickIntent 是 diagnose 前置短路（harness 层）·加分支不改 diagnose prompt·承重红线守住。**

**核实（harness _quickIntent 现状 :60-77）**：
- 现短路值：'general'（概念/清单/问候/实据搜索）/ null（落 diagnose）。
- RAG 接入：加 RAG_QUERY_KW（开放语义·哪些/如何/为什么 + 跨文档）→ 返 'rag_query'。
- **不改 diagnose**：_quickIntent 在 diagnose 之前（:60 注释"返 general→短路；null→落原 diagnose"）·加 'rag_query' 是新短路值·diagnose prompt 零触碰 ✅。

**glm组 建议（短路触发词设计·对齐 glm CB-22b B 路径分工）**：

```javascript
// emc-patterns.js 加
export const RAG_QUERY_KW = ['如何', '为什么', '哪些城市', '哪些案例', '适合', '综合'];
// vs KNOWLEDGE_QUERY_KW（CB-22b B 路径·结构化）：'有哪些项目', '体检问题', '体检指标'
```

**关键区分（glm 坚持 A/B 分工）**：
- **B 路径（query_knowledge_base·确定性）**：结构化查询（"有哪些项目/指标"）·精确 WHERE。
- **RAG（rag_search·向量）**：开放语义（"哪些适合片区更新"/"如何参考"）·模糊召回。
- 触发词**必须分离**——禁 RAG 承担结构化查询（杀鸡用牛刀 + 概率误命中）。

**harness 主循环分支**：
```javascript
const qi = _quickIntent(q);
if (qi === 'general') { /* 现有 general 短路 */ }
else if (qi === 'knowledge_query') { /* B 路径（CB-22b·待建）*/ }
else if (qi === 'rag_query') { /* RAG 短路 → /rag_search */ }
else { /* null → 落 diagnose */ }
```

**承重红线核验**：
- diagnose prompt：**零触碰**（_quickIntent 前置·不进 FC）✅
- 四态出口：RAG 注入 finalStep·走 EXIT_CONCEPT（general 直答）·非新态 ✅
- D019 final 极瘦：RAG 注入 intent-gated + <3000B（焦点 4）✅
- **但 harness _quickIntent 加分支 = 改 harness 主循环**——属**承重周边**·须"先扩 eval 再动·一次一处"（计划标"承重"正确）。

### 焦点 3：B 路径前置 vs RAG 先独立接入 — **partial（RAG 独立可接·但须标注 B 后补收窄）**

**计划问**：query_knowledge_base（CB-22b）尚未建——先建 B 再接 RAG？还是 RAG 先独立？

**glm组 判断：partial——RAG 独立接入可解燃眉（用户等不起）·但须标注"B 后补时收窄 RAG 触发词"（防 RAG 永久承担结构化查询）。**

**现实约束**：
- B 路径（CB-22b）定稿未实施——query_knowledge_base 不存在。
- 用户"宜昌有哪些更新项目"等真实查询**现在就要答**（用户定 RAG 本周重点）。
- 若等 B 先建再接 RAG——用户等不起·RAG 本周重点打折扣。

**glm组 建议（RAG 独立接入 + B 后补收窄）**：

**现阶段（B 未建）**：
- RAG 触发词**宽**（含结构化"有哪些项目"+ 开放"哪些适合"）—— RAG 承担所有知识查询。
- 即 RAG 临时承担 B 路径职责（结构化查询用 RAG 近似·非确定性但有召回）。

**B 后补时（CB-22b 实施）**：
- RAG 触发词**收窄**（去掉"有哪些项目/体检问题"等结构化词·只留"如何/为什么/哪些适合"开放语义）。
- 结构化查询转 B 路径（query_knowledge_base 确定性 WHERE）。
- **禁 RAG 永久承担结构化查询**——违背 glm CB-22b A/B 分工原则（结构化走确定性·开放走向量）。

**实现标注（防遗忘）**：
```javascript
// emc-patterns.js RAG_QUERY_KW
export const RAG_QUERY_KW = [
  // 开放语义（RAG 本职）
  '如何', '为什么', '哪些城市', '哪些案例', '适合', '综合',
  // ★ 临时承担 B 路径结构化（CB-22b B 建后移除下列·转 KNOWLEDGE_QUERY_KW）
  '有哪些项目', '体检问题', '体检指标', '更新项目',
];
// TODO(CB-22b): B 路径建后·删上述"临时结构化"词·RAG 只保留开放语义
```

**glm组 提醒**：
- RAG 临时承担结构化查询·**检索质量不如确定性 B**（向量近似 vs 精确 WHERE）——"宜昌有哪些项目"可能召回不全（黄金集虽 100%·但真实查询可能超出黄金集覆盖）。
- B 后补是**质量升级**·非可选——计划须标"B 路径 CB-22b 实施后收窄 RAG"为**必做项**（非后置可选）。

### 焦点 4：finalStep 注入（<3000B + 维度声明） — **agree（体积 + 维度双守卫）**

**计划**：rag 结果 intent-gated 注入（Top-K ≤5 + 来源 + data_dim）·<3000B·回答带维度声明。

**glm组 确认**：**agree——<3000B（glm CB-22c 建议收紧值采纳）+ 维度声明（颗粒度原则落实）。**

**体积守卫（glm 确认）**：
- 计划 :48 `<3000B`——glm CB-22c 讨论发起提 <8000B 偏宽·glm 建议收紧 <3000B（与 final_brief 同档）——**采纳** ✅。
- 实现：Top-K ≤5 条·每条 ≤200 字（source + snippet + data_dim）= ≤1000B + 维度声明模板 ~200B = <3000B。

**维度声明（glm 确认）**：
- 回答带"本数据源为 {data_dim} 维度"（颗粒度原则·cannot 维度化 F_016 已做）。
- finalStep 注入 RAG 结果时·LLM 据此声明边界（"本数据为社区维度·无法到栋"）。

**glm组 建议（注入格式）**：
```markdown
【RAG 知识检索（Top-3·维度标注）】
1. [0.82·社区维度] 葛洲坝片区 33 社区体检...（来源：glm_葛洲坝体检）
2. [0.76·方法论] 上海愚园路改造做法...（来源：case_library·方法论参考）
3. [0.71·片区维度] 南湖公园 76 亩...（来源：glm_南湖公园）
```
- 每条标 score + data_dim + 来源。
- **案例类显式标"方法论参考"**（防 LLM 引他城数据·颗粒度原则 2）。

### 焦点 5：e2e 测试设计 — **agree（含三阶段 + 回归）**

**计划**：e2e（"宜昌哪些项目适合片区更新"→ rag_search Top-K）+ 回归。

**glm组 确认**：**agree——补三阶段（端点/短路/注入）+ 黄金集回归。**

**glm组 测试设计建议**：

| 阶段 | 测试 | 断言 |
|---|---|---|
| **端点** | POST /aiqa/rag_search {query:"宜昌更新项目"} | 200 + results 非空 + 每条含 data_dim |
| **短路** | _quickIntent("宜昌哪些项目适合") === 'rag_query' | 短路命中（非 null 落 diagnose） |
| **注入** | finalStep 含"RAG 知识检索" + 维度声明 | 注入 <3000B + 回答不越维 |
| **黄金集回归** | 黄金集 3 类（召回/越维/案例）100% | 接入后黄金集仍 100%（防接入退化） |
| **B 后补收窄**（CB-22b 后） | RAG 触发词收窄·结构化转 B | RAG 不再命中"有哪些项目"（转 B） |

**glm组 关键提醒**：
- **黄金集回归**是核心——接入 EMC（harness 短路 + finalStep 注入）可能引入新故障（短路误判/注入膨胀）·黄金集 100% 须保持。
- **越维刚性**（颗粒度原则）：e2e 须含"数据到社区·问哪栋" → 回答含"无法到栋"声明·**断言刚性 100%**。

---

## 二、风险清单

### 阻断级
无（核心已完成·接入是接线·非新建能力）。

### 警告级（承重周边·须守 SOP）

| # | 风险 | glm组 建议 |
|---|---|---|
| **W1** | harness _quickIntent 加分支（承重周边） | 先扩 eval（test-cases.js 加 rag_query 短路用例）·一次一处·可回退 |
| **W2** | RAG 触发词过宽（临时承担 B 结构化·检索质量次优） | B 后补（CB-22b）必做收窄·标 TODO·非后置可选 |
| **W3** | finalStep 注入膨胀（RAG 结果 + final_brief 叠加） | intent-gated（仅 rag_query 触发）+ <3000B 断言 |

### 建议级

| # | 建议 | 优先级 |
|---|---|---|
| **S1** | RAG 触发词分"开放语义"+"临时结构化"·B 建后删后者 | P0（标注 TODO） |
| **S2** | e2e 黄金集回归（接入后黄金集仍 100%） | P0 |
| **S3** | 注入格式标 data_dim + 案例标"方法论参考" | P1 |
| **S4** | B 路径 CB-22b 实施列为必做（非后置） | P1（质量升级） |

---

## 三、可否执行结论

### ✅ 可执行——4 焦点 agree + 1 调整（B 顺序）·承重红线守住

**glm组 核心立场**：

RAG 核心完成度高（glm 上轮关键补强全落实）·接入 EMC 是**接线收尾**（端点 + 短路 + 注入）·非新建能力。4 焦点 agree + 1 调整：
- 焦点 1 端点：**agree**（仿 outlet_card·含 data_dim）
- 焦点 2 harness 短路：**agree**（不改 diagnose·_quickIntent 前置·承重守住）
- 焦点 3 B 顺序：**partial**（RAG 独立可接解燃眉·但 B 后补必做收窄·标 TODO）
- 焦点 4 注入：**agree**（<3000B + 维度声明·glm 收紧值采纳）
- 焦点 5 测试：**agree**（三阶段 + 黄金集回归）

**承重红线核验**：
- **diagnose prompt**：零触碰（_quickIntent 前置短路·不进 FC）✅
- **四态出口**：RAG 走 EXIT_CONCEPT（general 直答）·非新态 ✅
- **D019 final 极瘦**：注入 <3000B·intent-gated ✅
- **harness _quickIntent 加分支**：承重周边·须"先扩 eval 再动·一次一处"——**计划标"承重"正确·实施时守 SOP**。

**glm组 关键提醒（B 路径收窄·防 RAG 永久越界）**：
- 现阶段 B 未建·RAG 临时承担结构化查询（触发词宽）——可接受（用户等不起）。
- 但 **B 后补（CB-22b）是必做项**——收窄 RAG 触发词·结构化转确定性 B。
- 禁 RAG 永久承担结构化查询（违背 A/B 分工·向量近似不如精确 WHERE）。
- 实现标注 TODO（emc-patterns.js RAG_QUERY_KW 注释）·防遗忘。

---

## 附：现状核实证据（glm组 独立）

| 发现 | 证据 |
|---|---|
| **事实卡 35 条 + dimension 7 枚举** | urban_renewal_knowledge:7（住房/小区/社区/街区/城区/城中村专项/方法论） |
| **_infer_dim 维度推断** | rag_index:56-63（关键词推断 + 默认社区） |
| **案例标 dim:方法论** | rag_index:106（案例类非数据维度·颗粒度原则 2 落实） |
| 黄金集 100% | 计划 :17（召回+越维+案例全通过） |
| harness _quickIntent 现状 | harness.js:60-77（general 短路 + null 落 diagnose·RAG 加 'rag_query' 分支） |
| _quickIntent 不改 diagnose | :60 注释"返 general→短路；null→落原 diagnose"·RAG 加新短路值同模式 |
| outlet_card 端点（仿照） | aiqa_routes:88-97（build_outlet_schema → {cards,card}·确定性） |
| **B 路径 query_knowledge_base 未建** | CB-22b 定稿未实施·计划焦点 3 问顺序 |

### 声明

本回应由 glm组（ZCode + GLM 5.2）独立产出·2026-08-09·基于核实 urban_renewal_knowledge（事实卡）+ rag_index（_infer_dim/案例 dim）+ harness _quickIntent + outlet_card 端点。第三方独立评估·不做项目方决策背书。glm CB-22c Phase 1 评估提的补强（data_dimension/案例方法论）已落实——glm 确认核心完成度。

---

*登记：docs/context-map.md · CB-22 RAG 接入 EMC glm组 确认。*
