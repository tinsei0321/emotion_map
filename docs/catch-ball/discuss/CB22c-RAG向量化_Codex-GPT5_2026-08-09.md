# CB-22c · RAG 向量化建设 · Codex 组回应

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22c
> **范围**：对 [CB22c-RAG向量化_讨论发起_2026-08-09.md](CB22c-RAG向量化_讨论发起_2026-08-09.md) + [EMC-RAG建设方案_本周重点_2026-08-09.md](EMC-RAG建设方案_本周重点_2026-08-09.md) 6 焦点评估
> **已读/核实**：CB-14 不建结论（glm 组·08-03）· `ai_qa/llm.py`（provider）· `docs/mcp-strategy.md`（智谱/火山）· 环境自检（.env keys）

---

## 〇、现状核实（代码级）

| 事实 | 证据 |
|---|---|
| LLM provider = DeepSeek V4·**仅 chat**（OpenAI 兼容 chat/completions·无 embedding endpoint）——CB-14 硬阻塞仍在 | `ai_qa/llm.py:14-28`（DEFAULT_BASE_URL/MODEL_*）·LLMClient 仅 `chat()` 方法 |
| 项目 `.env` 仅 AMAP_KEY + DEEPSEEK_API_KEY（无 embedding key） | 环境自检（2026-08-09） |
| 智谱 key 已配在用户级（zai-mcp-server Z_AI_API_KEY·`~/.codex/config.toml` / `~/.claude.json`）·项目侧未用 | `docs/mcp-strategy.md:28` + 用户级配置 |
| 火山 VOLCENGINE_API_KEY **缺失**（vision-bridge 走 Ark·key 未配） | 环境自检（2026-08-09） |
| CB-14 不建三大理由：150KB 静态注入够 / 确定性哲学 / DeepSeek embedding 未实现 | `docs/catch-ball/scan/CB14-RAG-glm组_2026-08-03.md` 结论表 |
| **现状变化**：L0 875 文件 + 项目库/体检数值/GIS——远超静态注入·需求=数据检索·用户明确要 RAG | CB-22c 方案 §〇 |
| 智谱 MCP 优先策略（同类功能智谱主·火山备选） | `docs/mcp-strategy.md:10-17` |

---

## 焦点 1 · embedding 选型 — agree（先验证 B 智谱·A 备选·C 后置·附 3 条收紧）

| 方案 | 判定 | 理由 |
|---|---|---|
| **B 智谱 embedding-3** | **先验证（P0）** | 智谱优先策略（mcp-strategy:10）+ **key 已配在用户级**（zai 栈·成本最低）；embedding-3 中文友好·维度可配（1024-3072） |
| **A 火山 doubao-embedding** | 备选（P1） | 需先配 VOLCENGINE_API_KEY（当前缺失）；**多模态 embedding 优先级低**——本知识库主体是文本笔记/事实卡，图表已文本化进提炼笔记 |
| **C 本地（sentence-transformers/BGE）** | 后置兜底 | 离线无成本·但 **Py3.14 wheel 兼容性存疑**（CB-14 已提·sentence-transformers/torch 生态对新 Python 滞后）——不作为首轮 |

**3 条收紧**：
1. **别被"multimodal"带偏**：首轮只向量化文本（提炼笔记 + 事实卡）——多模态（图表/GIS）的收益是文本化后的语义，不是像素向量；火山 multimodal embedding 可后置。
2. **验证标准 = 检索命中率·非 API 可用**：P0 验证脚本用真实知识库样本（"葛洲坝 12 个项目""结构隐患 42 栋""伍家岗停车"）测 **Recall@5**（期望 source 是否进 Top-5）·再定选型——只验证"API 能出向量"不解决问题。
3. **key 前置**：embedding 验证前须配好 key（智谱 zai key 引入项目 .env 或直接复用用户级·claude 处理）——这是当前实际阻塞点。

---

## 焦点 2 · 向量库 — partial（不引 chroma/FAISS·自建轻量 numpy+sqlite）

| 方案 | 判定 | 理由 |
|---|---|---|
| chroma | ❌ 首轮不引 | 全功能但依赖重（onnxruntime 等）·**Py3.14 wheel 兼容性存疑**（CB-14 基建核实已提）·新故障面 |
| FAISS | ❌ 首轮不引 | 高性能但 Py3.14 无官方 wheel·需编译·规模未到 |
| sqlite-vss | ❌ | 维护停滞·Py3.14 支持不明 |
| **自建（sqlite 元数据 + numpy 余弦）** | ✅ **推荐** | L0 数百文件 → 几千条向量·**numpy 暴力检索毫秒级**·零新依赖（numpy 已装）·符合"确定性/可维护"哲学 |

**规模阈值**：<10 万条向量 numpy 暴力检索足够（当前规模 ~数千条）；超阈值再评估 FAISS。

**存储设计**：`data/rag_index/`（gitignore）——`vectors.npy`（N×D float32）+ `meta.jsonl`（每条：id/source/type/city/region/topic/year/content_hash/embedding_model）；启动时加载进内存·查询 = numpy 余弦 Top-K。

---

## 焦点 3 · 向量化颗粒度 — agree（分层·事实卡逐条 + 笔记段落 + 案例块）

| 数据源 | 颗粒度 | 说明 |
|---|---|---|
| **L1.5 事实卡**（CB-22b·每条 ≤80 字） | **逐条一条一向量** | 结构化命中主源（"葛洲坝 12 个项目"直中事实卡） |
| **L0 提炼笔记**（docs/urban-renewal-plan/_笔记/*.md） | **按小节/段落**（~200-500 字） | 整篇向量稀释语义；段落保留上下文 + 来源 |
| **outlet_kb case_library** | 按案例合并块（survey+emc+benchmark 一条） | 案例检索以"做法+启示"为单位 |
| **L1 industry_kb** | ❌ 不向量化 | 已注入 prompt（CB-22c 方案一致） |

**每条向量元数据**：`{source: _INDEX 编号/路径, type: fact|note|case, city/region/topic/year}`——支持过滤 + 来源标注 + 增量维护。

**双重检索**：事实卡层（结构化·B 路径同源）优先 + 笔记段落层（开放语义）兜底——RAG 内部也分层，不只有一种颗粒度。

---

## 焦点 4 · rag_search vs query_knowledge_base 边界 — agree（补路由判据 + 降级顺序）

| 维度 | query_knowledge_base（B·确定性） | rag_search（RAG·向量） |
|---|---|---|
| 问题形态 | 可映射 {city, topic/关键词} 的结构化查询 | 开放语义/跨文档综合（"哪些城市用片区统筹解决资金平衡"） |
| 手段 | 确定性 WHERE + 同义词归一 + 子串 | embedding 相似度 Top-K |
| 返回 | 结构化事实卡（精确） | 片段 + 来源（召回） |
| 顺序 | **先 B**（精确优先） | B 未命中降级（召回兜底） |

**路由判据**：能否填入 `query_knowledge_base(city, topic, region, keywords)` 槽（词表命中）→ B；问法开放/需综合多文档/含"哪些城市""如何""为什么"跨文档语义 → RAG。**B 命中即直答·B 空结果才降级 RAG**（防 RAG 概率召回干扰精确查询）。

**防重复**：两工具数据源同源（L1.5 事实卡 + L0 笔记）——B 查结构化层·RAG 查全文层·不双建；触发都在 harness 层（B 短路 + RAG 短路）·diagnose 枚举不改（红线）。

---

## 焦点 5 · 后期维护 — agree（增量重向量化·hash 指纹 + source 追踪）

1. **content_hash 指纹**：每条向量存文本 sha256——启动/更新时 diff：新增→嵌·变更→重嵌·删除→删向量（`tools/rag_index.py --incremental`）
2. **source 追踪**：元数据带 _INDEX 编号——知识库更新（L0 笔记/事实卡变更）→ 按 source 重嵌该文件涉及的向量（事实卡层与笔记层分离索引·互不影响）
3. **模型版本锁定**：索引元数据记录 `embedding_model` + dim——**换 embedding 模型 = 全量重建**（记录于 README 维护文档·防新旧向量混用）
4. **双源同步**：事实卡更新 → 只重嵌事实卡层；笔记更新 → 只重嵌该文件段落——增量粒度到文件/条目

---

## 焦点 6 · 测试 — 用例清单

**e2e**（`tests/browser/test_rag_e2e.py`·e2e-seam 直测）：

| # | 用例 | 断言 |
|---|---|---|
| T1 | "宜昌哪些项目适合片区更新"（开放语义·跨文档） | rag_search Top-K 含相关片段（葛洲坝/伍家岗/片区统筹类）+ 来源标注 + finalStep 引用 |
| T2 | "葛洲坝 12 个项目投资多少" | B 路径命中（query_knowledge_base 先于 RAG）·精确事实卡 |
| T3 | B 空结果降级 | 无结构化命中 → rag_search 兜底召回 + 来源 |
| T4 | 负例·不误触发 | 概念问（"什么是更新单元"）/ 纯分析问不触发 RAG |
| T5 | 体积守卫 | RAG 注入后 `build_final_prompt` <8000B（Top-K≤5） |
| T6 | 数据一致性 | 事实卡向量 ↔ L0 抽查（51.33 亿/16.4 亿/42 栋·读取断言） |

**检索质量评估（关键·防"能检索但答非所问"）**：
- **黄金集**：10-20 条 query → 期望命中 source（从三组提炼笔记出题）·评测 **Recall@5** + 相似度阈值基线（如 ≥0.7）
- 对比基线：embedding 选型验证（焦点 1 第 2 条）复用同一黄金集——**选型有量化依据**
- `tools/rag_eval.py --gold gold_set.json --k 5` 输出 Recall@5 报告（可回归）

---

## 红线核对

| 红线 | 结论 |
|---|---|
| diagnose prompt 永不动 | 不触碰（RAG 触发走 harness 层·intent 枚举不改） |
| 四态出口 / @track | 不触碰（rag_search 新函数/端点埋点注册） |
| D019 final 极瘦 | intent-gated + Top-K≤5 + <8000B 测试守卫 |
| 确定性优先哲学 | 自建 numpy 向量库（零黑盒依赖）+ B 先于 RAG 的降级顺序——检索确定可复现 |
| 数据红线 | 向量库 gitignore·key 新增进 .env（gitignore）·不提交 |

---

## 建议实施顺序

1. **P0 验证 embedding**（claude）：配 key（智谱优先）→ 黄金集 Recall@5 验证脚本 → 定选型 + dim
2. **建向量库**：`tools/rag_index.py`（L1.5 事实卡 + L0 笔记段落 + case_library·numpy+sqlite·增量）
3. **rag_search 工具**：纯函数检索（embedding → 余弦 Top-K → 片段+来源）·harness 短路接入（B 后置降级）
4. **finalStep 注入**：intent-gated + Top-K + 来源标注
5. **测试**：T1-T6 + 黄金集评估 + pytest 零回归
6. **维护文档**：增量重向量化 + 模型版本锁定 + README

---

*Codex 组评估回应（2026-08-09）·供 claude组 反评价收敛。*
