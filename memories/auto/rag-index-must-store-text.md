---
name: rag-index-must-store-text
description: "RAG 索引 meta 必须持久化 text 片段全文·否则注入 LLM 的\"素材\"仅文件名·三支柱①空转"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1e26428f-d209-4215-8b05-466a170dd9b3
  modified: 2026-08-09T10:10:01.069Z
---

**RAG 索引 meta 必须存 `text` 片段全文**（CB-22 承重发现·2026-08-09）：`tools/rag_index.py` 索引曾只存 `source/type/data_dim/content_hash`·`search()` 返回无 text → harness 注入 finalStep 的"素材"仅文件名列表 → LLM 无内容可综合（靠预训练知识补·三支柱①空转·验收"关键数值必须在素材内"结构性不可过）。

**Why:** 两组评估报告都只核对了"注入素材走 finalStep"的**代码路径**·没人核对素材**内容**是否随索引持久化——路径对 ≠ 内容在。CB 复验/评估核 RAG 时须查 meta.jsonl 是否含 text（`head -1 DATA/rag_index/meta.jsonl`）。

**How to apply:** 索引构建时 meta 存 `'text': c['text'][:2000]`（防 jsonl 膨胀）·search 透传 text·前端注入片段全文（snippet ~1000B）·老索引无 text → 空串需 `--rebuild`。已机器化：`tests/validate_paradigm_map.py` + `test_rag_emc_e2e.py` 端点 text 断言。相关 [[emc-tri-state-exit-contract]] [[cb-knowledge-base]]。
