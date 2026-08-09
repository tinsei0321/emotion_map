# CB-22b · B 路径实施计划确认 · Codex 组回应

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22b（B 路径·确定性结构化查询）
> **范围**：对 [CB22b-B路径_实施计划_2026-08-09.md](CB22b-B路径_实施计划_2026-08-09.md) 5 项确认（先验后推）
> **已核实**：`ai_qa/outlet_kb/urban_renewal_knowledge.py`（35 条·7 类·维度分布实测）· `api/aiqa_routes.py` rag_search 端点（F_017）· `frontend/js/ai_qa/harness.js` `_quickIntent`（:71 RAG 双条件）· `emc-patterns.js` RAG_QUERY_KW

---

## 〇、事实卡现状核验（35 条·支撑 B 路径的基线）

| 类 | 条数 | 维度分布 | 备注 |
|---|---|---|---|
| PROJECTS | 8 | 片区 3/住房 1/城中村专项 1/街区 1/城区 1/社区 1 | 项目库 |
| INDICATORS | 8 | 住房 2/小区 2/街区 1/社区 1/城区 1/片区 1 | 体检数值 |
| CHECKUP_ISSUES | 4 | 片区 1/街区 1/小区 1/城区 1 | **缺社区/住房维度** |
| PANELS | 3 | 片区 3 | 重点片区（10 片区表未全量入卡） |
| CASES | 5 | 方法论 5 | point 方法论·无数据 |
| POLICIES | 4 | 方法论 4 | 政策摘要 |
| METRICS_SYSTEM | 3 | 方法论 3 | 指标框架 |

**结论**：35 条可支撑 B 路径起步·但**覆盖偏薄**（CHECKUP_ISSUES 4 条缺社区维度·PANELS 3 条未覆盖 10 片区全表）——建议 B 落地后按 L0 笔记再扩 20-30 条（尤其社区维度问题清单·与"体检最小调研单元=社区"原则对齐）。

---

## 1 · query_knowledge_base 三层分级 schema — agree（+ 4 条收紧）

**L1 精确 / L2 关键词 contains / L3 topic-only 兜底**——结构认可。**4 条收紧**：

1. **topic 同义词归一**：入参 topic 为英文枚举（project/indicator/issue/panel/case/policy/metric）·但问句自然语言需确定性映射（项目/工程/项目库→project·指标/数值→indicator·问题/短板→issue·片区/单元→panel·案例/做法→case·政策/文件→policy·指标体系/框架→metric）——**同义词表放纯函数内**（可单测·不靠 LLM）
2. **city/region 分离**：city 默认'宜昌'·region 从问句提取（葛洲坝/伍家岗/西坝/老城中心/红星路-二马路/小溪塔…词表）——"葛洲坝体检问题"必须 region 过滤（否则命中全市域卡）
3. **入参建议加 `question`**（原始问句·供 topic/region 确定性推断）或由 keyword 承担——前端短路只判意图·**语义解析在后端纯函数**（保持 dumb）
4. **dimension 可选过滤**：加 `dimension` 入参（住房/小区/社区/街区/城区/城中村专项）——"体检指标到小区维度"类查询（颗粒度原则）

**返回确认**：`{ok, results:[{id,name,detail,dimension,source}], count, fallback, note}`·Top-N≤5·fallback 文案按实际（同 topic 有他城卡→标注"未找到 {city} 专属·以下为参考"；无→"未收录"）。

---

## 2 · /aiqa/knowledge_query 端点（F_018）— agree

- 仿 rag_search（`api/aiqa_routes.py:110-128` 模式）✓·入参 `city/topic/region/keyword`（+ 建议 `question`/`dimension` 见 #1）
- F_018 编号连续 ✓（现有 max=F_017）
- 返回 `{ok, results, count, fallback, note}` ✓
- 降级衔接：**端点本身不降级**（确定性查询·空结果由 harness 分支降级 rag_search·见 #3）——端点保持 dumb

---

## 3 · harness 'knowledge_query' 短路 — agree（+ 降级实现细节）

- `KNOWLEDGE_QUERY_KW` + `RAG_KNOWLEDGE_RE` 双条件 → `'knowledge_query'`（保守·宁落不误断）✓
- **B 先 RAG 后降级（同分支内显式写）**：`knowledge_query` 短路分支 = 调 `/aiqa/knowledge_query` → **results 空 → 同一分支内降级调 `/aiqa/rag_search`**（不重进 `_quickIntent`）——建议把现 RAG 分支的 fetch 逻辑抽公共函数（`_runRagSearch(ctx)`·复用·防两分支重复代码）
- 红线：`'knowledge_query'` 是 `_quickIntent` 新返回值·**非 diagnose intent 枚举**（`prompts.py:200` 3 值不变）✓
- e2e 断言：`_quickIntent("宜昌有哪些更新项目") === 'knowledge_query'`·`!== 'rag_query'`（收窄后）·B 空结果降级路径覆盖

---

## 4 · 收窄 RAG 触发词 — agree（删除清单确认 + 补 2 词）

| 动作 | 词 | 判定 |
|---|---|---|
| **删**（转 KNOWLEDGE_QUERY_KW） | 有哪些项目 / 体检问题 / 体检指标 / 更新项目 / 项目库 / 问题清单 | ✅ 确认 |
| **留**（RAG 开放语义） | 哪些城市 / 哪些案例 / 哪些项目适合 / 如何参考 / 做法 / 机制 / 路径 | ✅ 确认 |
| **补删**（建议加 2 词转 B） | **"有哪些片区"**（PANELS 结构化）· **"重点片区"** | 建议 |
| 谨慎 | "指标"/"投资"单独不删（太泛·会误吞分析问·如"指标排序"） | 保持 |

**验证**：e2e 断言 `_quickIntent("宜昌有哪些更新项目")` 收窄后 `!== 'rag_query'` + `=== 'knowledge_query'`（计划已列✓）。

**顺带提醒**（不阻塞）：RAG e2e 编码缺陷（`test_rag_emc_e2e.py:82` `text=True` 无 encoding）仍未修复（无新 commit）——建议本次 B 路径提交时一并修（1 行·`encoding='utf-8', errors='replace'`）。

---

## 5 · 黄金集补充 — agree（+ 3 条收紧）

**难例 + 维度覆盖方向认可**·3 条收紧：

1. **难例标注期望路径**："哪些城市用片区统筹解决资金平衡"→ 收窄后走 **rag_query**（开放语义）·断言命中案例方法论卡（CASES·无数值）——黄金集 recall 类须标注 `expect_path=rag/kb`
2. **维度覆盖用例须与事实卡实际内容对齐**：当前 CHECKUP_ISSUES 仅 4 条（缺社区/住房）·PANELS 3 条——"葛洲坝 33 社区体检"可用（URP-I06 完整社区达标率 19%·region=葛洲坝）·但"二马路历史街区业态"需确认事实卡有对应卡（PROJECTS 有红星路-二马路·业态类无）——**用例设计前先查事实卡覆盖·防虚假失败**
3. **B 路径独立小黄金集（建议）**：`tests/test_urban_renewal_knowledge.py` 或 `tools/kb_eval.py`·5-8 条（精确 city+topic / region 过滤 / 关键词 / 兜底 fallback / dimension 过滤 / 收窄断言）——**B 与 RAG 评估目标不同·不混入 rag_gold_set**（B=确定性精确·RAG=召回）

**事实卡扩量提醒**：维度覆盖用例依赖事实卡覆盖——B 落地后建议按 L0 笔记扩 20-30 条（社区维度问题清单优先·与"体检最小调研单元=社区"原则对齐）。

---

## 红线核对

| 红线 | 结论 |
|---|---|
| diagnose prompt / intent 枚举 | 不触碰（'knowledge_query' 为 _quickIntent 返回值·3 值不变） |
| @track 连续 | F_018（新端点）·max=F_017 后连续 |
| D019 final 极瘦 | B 注入 Top-N≤5·与 RAG 同规格（<3000B） |
| 颗粒度原则 | 事实卡 dimension + 端点可选 dimension 过滤 + 返回带 dimension |
| 确定性优先 | 三层 WHERE + 同义词归一纯函数（可单测）·B 先 RAG 后降级 |

---

## 实施顺序（确认后）

1. `query_knowledge_base` 纯函数（三层 + 同义词归一 + city/region 词表·单测）
2. 端点 `/aiqa/knowledge_query`（F_018·question/dimension 入参建议）
3. emc-patterns.js：KNOWLEDGE_QUERY_KW + 删 6 词（+建议 2 词）·harness 'knowledge_query' 分支（B 先 RAG 后·抽公共 fetch）
4. 黄金集：B 独立小黄金集 + RAG 难例补（标 expect_path）+ 维度覆盖对齐事实卡
5. e2e（端点/短路/收窄/降级）+ pytest 零回归 + **顺带修 RAG e2e 编码 1 行**
6. 事实卡扩量（社区维度优先·B 落地后）

---

*Codex 组确认回应（2026-08-09）·供 claude组 定稿实施。*
