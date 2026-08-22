# RAG 语料地图（PT-CB9 L1 · v1.2-pre §5.1 白名单制）

> 单一登记处：RAG 索引的**全部语料来源**在此建档——新增来源必须先入本图再入库（原则 1：语料白名单制·登记即入口）。
> 条数为 2026-08-22 实跑（`py tools/rag_index.py --build` 同源 loader）：**notes 282 + facts 68 + concepts 9 + cases 5 = 364 chunk**。
> 索引产物（向量/meta）= 派生资产·重建命令 `py tools/rag_index.py --build`（本图变→必重建+门禁）。

## 一 四源登记

| # | 来源路径 | chunk type | dim 取值 | 条数 | 知识提交入口（加内容改哪里） | 维护纪律一句话 |
|---|---|---|---|---|---|---|
| 1 | `docs/urban-renewal-plan/**/*.md`（跳过 `_` 前缀/README/模板） | `note` | `_infer_dim` 关键词推断：住房/小区/社区/街区/城区/城中村 | 282 | 该目录下新增/编辑 md（按 `\n## ` 小节切分·<20 字段丢弃） | 小节即 chunk——写笔记时按「一节一义」组织，作废口径小节等泳道①标 status 不删档 |
| 2 | `ai_qa/outlet_kb/urban_renewal_knowledge.py`（`all_facts()`） | `fact` | 卡内 `dimension` 字段直读（住房/小区/社区/街区/城区/片区/方法论等） | 68 | 该文件内 PROJECTS/INDICATORS 等列表追加事实卡 dict（id 连续） | 事实卡须带 source/keywords·从笔记蒸馏的卡补 lineage（泳道①规则表） |
| 3 | `ai_qa/outlet_kb/concept_knowledge.py`（`all_concepts()`） | `concept` | 恒 `方法论` | 9 | 该文件内追加概念卡 dict | 概念卡=定义/边界认知·不收数据值（数据值走事实卡） |
| 4 | `ai_qa/outlet_kb/case_library.py`（`CASES`） | `case` | 恒 `方法论` | 5 | 该文件 CASES dict 追加案例（key 语义化） | 案例只取方法论 point·**禁引他城具体数值**（防张冠李戴·刚性门禁） |

> 维度分布实跑（参考）：notes=城区103/住房66/小区53/社区43/城中村12/街区5；facts=方法论15/片区12/住房9/小区10/城区8/街区6/项目库3/社区2/城中村专项1/成效1/平台身份1。

## 二 新增来源流程（五步·v1.2-pre §5.1 原则 1 落地）

1. **入图**：在本文件 §一 追加一行（路径/type/dim/条数预估/提交入口/纪律）——先入图后入库，未登记来源不进索引；
2. **入库**：按该行「知识提交入口」落内容（md 笔记或知识库 dict·遵守该源纪律列）；
3. **重建**：`py tools/rag_index.py --build`（向量与 meta 整体重建·原子写）；
4. **门禁**：`py -m pytest tests/test_rag_gate.py tests/test_rag_loader.py -q` 全绿（Recall 不降·全文/枚举断言过）；
5. **commit**：来源文件 + 本图变更同批显式路径提交（索引产物 `data/rag_index/` 派生资产按仓规随构建纪律处理）。

## 三 治理字段现状（泳道① 2026-08-22）

- `status`：3prime/ 系列 15 个数据文件（2026-08-12 旧口径批次·占比表/落位）全节标 `superseded`（依据 03-10 §一声明）；`分析计划与内容_总纲` 待裁未标；其余全 `active`。
- `lineage`：事实卡 67/68 标注（格式 `src:<文件>#<节>`·EMC-IDENTITY-01 无语料内同源未标）；notes/cases/concepts 暂无可确证同源对。
- 过滤与去重的检索侧消费归泳道②（superseded 默认滤除·字段缺失=active 兼容）。
