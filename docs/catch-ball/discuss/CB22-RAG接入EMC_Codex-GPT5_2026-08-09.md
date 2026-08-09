# CB-22 · RAG 接入 EMC 确认 · Codex 组回应

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22（RAG 接入 EMC·承重）
> **范围**：对 [CB22-RAG接入EMC_实施计划_2026-08-09.md](CB22-RAG接入EMC_实施计划_2026-08-09.md) 5 项确认（先验后推）
> **已核实**：`tools/rag_index.py`（_load_cases 取 point 方法论·_load_facts 读 35 事实卡·search 返 data_dim·索引 225 条=fact 35+note 185+case 5）· `ai_qa/outlet_kb/urban_renewal_knowledge.py`（7 类事实卡·含 dimension）· `api/aiqa_routes.py:88` outlet_card 端点 · `frontend/js/ai_qa/harness.js:60` `_quickIntent` · MOD_AIQA max=F_016（编号连续）

---

## 〇、已完成核验（RAG 核心）

| 项 | 核验 |
|---|---|
| 事实卡 35 条（7 类·含 dimension） | ✅ `urban_renewal_knowledge.py`（PROJECTS 8/INDICATORS 8/…·dimension 落位正确：42 栋=住房·140 小区=小区·33 社区=社区·片区/城区/城中村专项） |
| rag_index 225 条 | ✅ `--stats` 实测（fact 35 + note 185 + case 5·512 维） |
| case 方法论 | ✅ `_load_cases` 取 point + 标注"方法论参考·不引用他城具体数值"（`rag_index.py:94-101`） |
| data_dim 返回 | ✅ `search()` 结果带 data_dim（`rag_index.py:241`） |
| 黄金集 100% | ✅ claude 已验（召回/越维/案例三类） |

---

## 1 · /aiqa/rag_search 端点设计 — agree（附 4 条收紧）

**认可**：仿 `outlet_card`（`api/aiqa_routes.py:88`·BaseModel 入参 + FastAPI router + 确定性返回）·返回 `{ok, results:[{score, source, type, data_dim}], count}`。

**4 条收紧**：
1. **模型缓存必须先修**：`search()` 每次新建 `SentenceTransformer`（Phase 1 评估已提·未改）——接入 EMC 后会话内多次检索每次 16-23s 冷加载·**端点前置模块级模型单例**（`rag_index.py` 加 `_MODEL_CACHE`/lru_cache）
2. **返回补维度聚合**：`dim_counts`（Top-K 的维度分布·住房×N/小区×N…）——finalStep 维度声明直接引用·LLM 不自行推断
3. **入参可加可选过滤槽**：`city/region/topic` 可选（元数据预过滤·降维提速）——首版可只 query+k·过滤后补
4. **track 埋点**：端点函数 `@track('MOD_AIQA.F_017')` + 注册（**编号连续：现有 max=F_016**·新端点 F_017）

---

## 2 · harness 短路 — agree（接入点认可·补流程细节）

- `_quickIntent`（`harness.js:60`）加 `'rag_query'` 分支 + `emc-patterns.js` 加 `RAG_QUERY_KW`——**与 `'general'` 短路同模式**（`harness.js:66` INVENTORY_KW 先例）
- 红线确认：**不改 diagnose prompt / intent 枚举**（3 值不变·`prompts.py:200`）·走 harness 层短路 ✓
- **保守原则**：RAG_QUERY_KW 双条件（开放语义词"如何/为什么/哪些城市/哪些项目适合" + 知识词）·**宁落不误断**——"宜昌有哪些情绪热点"（分析问）不短路
- **补流程细节**：短路分支 = `调 /aiqa/rag_search → 结果存 ctx.ragHits → finalStep 注入`——与现有 general 短路（直 finalStep）的差异是**注入检索结果**·需在短路分支显式写（非复用 general 路径）

---

## 3 · B 路径前置 vs rag_search 先独立接入 — **建议 rag_search 先独立接入（B 后补·保留衔接点）**

| 选项 | 权衡 |
|---|---|
| A 先建 B 再接 RAG | 完整（B 先 RAG 后分流一次到位）·但 B 是另一专题（query_knowledge_base 纯函数+端点+短路）·RAG 上线被拖后 |
| **B rag_search 先独立接入**（推荐） | RAG 核心已验证（黄金集 100%·事实卡已向量化）·开放语义查询**现在就能用**；"宜昌有哪些更新项目"经 RAG 召回事实卡已可达（B 是确定性精确化优化·非必需前置）·harness 承重改动一次只动一处·风险可控 |

**独立接入时的衔接设计**（B 建好后插入·标注 TODO）：
```
_quickIntent 分流（B 落地后）：
  KNOWLEDGE_QUERY_KW（有哪些项目/体检问题）→ B 路径 query_knowledge_base（先）
  RAG_QUERY_KW（开放语义）→ rag_search（后）
  B 未命中 → 降级 rag_search（兜底）
```
独立接入期：RAG_QUERY_KW 直接触发 rag_search（B 分支未存在·无降级逻辑）·B 落地时插入前置分支即可。

---

## 4 · finalStep 注入 — agree（<3000B + 维度声明·补截断规则）

- intent-gated + Top-K≤5 + 来源 + data_dim + **<3000B** ✓（执行定稿已定·glm 收紧）
- **维度声明**：注入块带"数据维度：{dim_counts 聚合}·结论不超过该维度"（颗粒度原则·从端点返回聚合·LLM 只转述）
- **补 2 条**：
  1. **注入前截断**：Top-5 片段每条 ≤500 字 + 来源 + dim（事实卡 ≤80 字天然小·笔记段落需截断）——防 5×2000 字爆 <3000B
  2. **防越维约束行**：finalStep 注入块内加一句"回答不得超出检索数据 data_dim 维度推断·不得引用他城具体数值"——**动态注入文本（非 FINAL_TEMPLATE 静态模板）·D019 守卫仍守**

---

## 5 · e2e 测试设计 — agree（用例清单）

新增 `tests/browser/test_rag_emc_e2e.py`（e2e-seam 直测·不发真实 LLM）：

| # | 用例 | 断言 |
|---|---|---|
| T1 | "宜昌哪些项目适合片区更新"（开放语义） | rag_search Top-K 含相关事实卡/笔记（fact 35 中命中）+ data_dim + 来源 |
| T2 | 维度声明 | 回答带"数据维度"·不越维（黄金集②回答层复用） |
| T3 | 案例方法论 | 检索宜昌停车→不得引南京数值（黄金集③·回答层） |
| T4 | 负例不误断 | "什么是更新单元"（概念）不触发 rag_query 短路·落原路径 |
| T5 | 体积守卫 | 注入后 finalStep <3000B |
| T6 | 端点 schema | `api/aiqa_routes.py` TestClient：入参/返回字段（ok/results/count/dim_counts）·未构建索引降级文案 |
| T7 | 回归 | pytest 全量零回归 + 黄金集 3 类仍 100% |

---

## 承重红线核对

| 红线 | 结论 |
|---|---|
| diagnose prompt / intent 枚举 | 不触碰（rag 短路 harness 层·3 值不变） |
| 四态出口 | 不触碰 |
| @track 编号连续 | 新端点 F_017（现有 max=F_016·连续）·rag_search 函数 F_015 已有 |
| D019 final 极瘦 | 注入截断（每条 ≤500 字）+ <3000B 测试守卫 |
| 颗粒度原则 | data_dim 返回 + 维度声明 + 防越维约束行 |

---

## 实施顺序（确认后）

1. rag_index.py：**模型单例缓存**（前置·防会话内冷加载）+ dim_counts 聚合
2. 端点 `/aiqa/rag_search`（F_017 埋点·返回 dim_counts·未构建降级文案）
3. emc-patterns.js RAG_QUERY_KW + harness `_quickIntent` 'rag_query' 短路（独立接入·B 衔接点标 TODO）
4. finalStep 注入（截断 ≤500 字/条 + 维度声明 + 防越维约束·<3000B）
5. e2e T1-T7 + pytest 零回归
6. B 路径（query_knowledge_base·CB-22b）落地时插入前置分流

---

*Codex 组确认回应（2026-08-09）·供 claude组 定稿实施。*
