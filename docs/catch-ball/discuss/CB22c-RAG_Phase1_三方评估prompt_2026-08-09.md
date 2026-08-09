# CB-22c · RAG Phase 1 实现评估 — 三方共同（claude + codex + glm）

> **发起方**：claude组 | **日期**：2026-08-09 | **CB 轮次**：CB-22c（Phase 1 实现）
> **用途**：rag_index.py 核心实现已落（claude 组）+ 索引已构建（190 条）+ 检索已验证 → **三组共同评估**（claude 自查 + codex/glm 独立审）
> **登记**：docs/context-map.md

---

```
【CB-22c RAG Phase 1 实现评估 · 三方共同】

背景：RAG 向量化 Phase 1 核心已实现——tools/rag_index.py（本地 BGE 向量化 + numpy 检索）·索引已构建
（190 条·512 维）·检索已验证（"宜昌有哪些更新项目"命中 0.819·"葛洲坝体检问题"0.745·"停车"类 0.595 偏低）。
三组共同评估实现质量，确认后可接入 EMC。

第一步 · 读本地文件（无需 git）
- 读 tools/rag_index.py（实现·主）
- 读 docs/catch-ball/discuss/CB22c-RAG_Phase1_执行定稿_2026-08-09.md（执行定稿·采纳基线）
- 读 docs/catch-ball/discuss/CB22c-RAG_Phase0评估_{你的组}_2026-08-09.md（你之前的评估·自查是否被落实）
- 可实测：export HF_ENDPOINT=https://hf-mirror.com && py tools/rag_index.py --stats（索引状态）

第二步 · 评估焦点（agree/disagree/partial + 证据·按你组视角）
1. 【claude 自查 + 两组审】编码规范：query/passage 统一封装（bge instruction）是否正确落实？相似度是否可能失真？
2. 【两组审】原子写 + embed_hash：临时文件+os.replace 是否充分？增量重向量化缺口？
3. 【两组审】元数据 schema（source/type/content_hash/embedding_model/dim）够吗？防漂移？
4. 【两组审】索引质量：190 条（笔记段落 185 + 案例 5）覆盖够吗？缺 L1.5 事实卡？（CB-22b 尚未建·应否先建）
5. 【三组】检索质量：验证结果（0.819/0.745 高·0.595 停车偏低）→ 是否需黄金集 Recall 量化？bge-small vs large？
6. 【claude 自查】承重红线：@track（MOD_AIQA.F_014/015）注册了吗？diagnose/四态出口未碰？

第三步 · 产出回应
- claude 组：自查结论（已实测·补充证据）
- codex/glm 组：独立评估
- 落盘 docs/catch-ball/discuss/CB22c-RAG_Phase1评估_{组名}_{YYYY-MM-DD}.md
- 中文为主·引用 path:line·不 git
```

---

*claude组（2026-08-09）·RAG Phase 1 实现三方评估 prompt·待三组产出。*
