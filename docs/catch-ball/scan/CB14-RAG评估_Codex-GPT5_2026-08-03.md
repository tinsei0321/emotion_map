# CB-14 EMC·RAG 研究评估（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）  
> **时间**：2026-08-03 | **分支**：`fix/emc-buglog` @ `e052fe7`  
> **方法**：现状事实实测核验（渲染体量/注入点/依赖/API 官方信息）+ 独立推演，结论先行  
> **范围**：只读评估 · 不改代码 · 不 commit

---

## 结论摘要（先行）

1. **必要性：当前"知识超限"问题不存在。** 知识总量渲染后以十 KB 计（industry_kb 四领域全文实测仅 **19.7KB**），per-query 注入 5-50KB，远小于 context window。真正的痛点 **A4（finalStep 无领域知识）是注入策略问题，不是检索问题**——用 RAG 解决属于用火箭打苍蝇。
2. **价值：现在是负收益/纯负担。** EMC 知识是静态、权威、可测试的 Python 常量（确定性查表，零模型参与）；RAG 引入 embedding 延迟、向量库兼容风险、检索方差（top-k 抽错段 = 新幻觉源）与"prompt 瘦身"方向相反，且与"体验收敛"目标冲突。
3. **可行性：基建三条腿都不稳。** Py3.14 装 chromadb/faiss 有真实兼容风险（hnswlib/onnxruntime 编译问题，官方修复未合）；**DeepSeek 官方 API 无 embedding 端点**（已确认）；.env 仅 AMAP+DEEPSEEK key，无 Ark 类 embedding key。但 20KB 语料根本不需要向量库——numpy 内存暴力检索或 **domain_lens 确定性检索**即可。
4. **时机：现在不建，先做 RAG-lite。** 正确顺序 = ① A4 选择性注入（finalStep 按 domain_lens 注入对应领域 brief，守 <3KB 门禁）→ ② industry_kb 做厚（RAG 的真正前提）→ ③ 触发条件达到（单领域渲染 >50KB 或引入外部动态语料）后再评估真 RAG。

**一句话：RAG 是未来知识库做厚后的备选方案，不是当前痛点（A4）的解法；当前解法是"按需注入"，且 EMC 已具备现成的确定性检索键（domain_lens）。**

---

## 一、现状事实核验（含对"我方调查"的修正）

| 项 | 我方调查 | 实测核验 |
|---|---|---|
| industry_kb 规模 | 4×7-10KB | 源文件 6.9-9.9KB（合计 ~34KB）；**渲染全文仅 3.9-6.4KB/领域，四域合计 19.7KB**；brief 速查 1.1KB；lens 附录（2 域）11.2KB |
| 知识总量 | ~200KB | 磁盘合计 ~142KB（industry_kb 34 + paradigm 39 + contracts 45.8 + landuse 11 + manifesto 12.5）；**per-query 实际注入 5-50KB**（fast-path diagnose ~2KB / 兜底 diagnose 45.8KB / final 2.8KB / FC 工具 schema+brief） |
| 注入方式 | 全静态拼 prompt | 属实：`prompts.py:122`（diagnose lens 附录）、`:242`（FC brief）、`:118/:237/:534`（MANIFESTO 在 agentStep/兜底 diagnose/field_infer）；**final 已去 MANIFESTO+industry 附录（5.233 极瘦 17KB→~0.9KB，`prompts.py:166` 注释为证）** |
| landuse_codes | 运行时未 import | 属实：全仓无 import 语句，仅注释/字符串值域引用（`prompts.py:470`、`core/field_dictionary.py:14`） |
| A4 开放 bug | finalStep 无领域知识 | A4 出自 `docs/catch-ball/discuss/EMC体验评估讨论报告_2026-08-01.md:177`：**domain_lens A 部损失（FC prompt 无输出指令→A 部恒空）· finalStep 无领域知识注入 · MED 级 · 承重：改前先扩 eval**——是修复池 MED 项，非 CRIT 级"开放 bug" |
| Py3.14 依赖 | chromadb/faiss 未装·wheel 风险 | 实测 `chromadb/faiss/sentence_transformers` 均未安装（numpy 在）；**风险属实**：chromadb 在 Py3.14 有 hnswlib/onnxruntime 编译失败记录（chroma-core #5983，修复 PR #5842 未合） |
| DeepSeek embedding | 存疑 | **升级为"官方 API 无 embedding 端点"**：2026-03 生态表明确 ❌；GitHub 上的 embedding API 为社区 Proposal 而非发布；CSDN 类教程不可信 |
| Ark embedding | 多模态未接 EMC | 属实：.env 实测仅 **AMAP_KEY + DEEPSEEK_API_KEY** 两个 key |

---

## 二、四问独立评估

### 1. 必要性：知识超限问题存在吗？A4 用 RAG 还是更轻方案？

**不存在"知识超限"。** 判断标准是"渲染后注入量"而非磁盘字节：industry_kb 全文 19.7KB ≈ 6-7K tokens，即使四域全注也就 2 万 token 出头；诊断兜底全量 prompt 45.8KB 也在 128K 窗口内轻松容纳。RAG 的适用前提——语料显著大于上下文窗口、或语料动态增长不可预编译——**当前均不成立**。

**A4 的正确解法是"选择性注入"（RAG-lite），且 EMC 已有现成检索键：`domain_lens`。** 诊断卡已经确定性地判出问句所属领域（urban_planning/renewal/operation/governance），这本质就是一次零成本、零模型、100% 可测的"检索"。缺的只是**在 finalStep 把命中领域的知识注回去**（当前 final 无任何领域注入，是 5.233 瘦身时的取舍，A4 记录在案）。改动面 = finalStep prompt 加 1 个按 domain_lens 拼 brief 的附录（领域 brief 实测 1.1-6.4KB，可先注 brief 守 <3KB 门禁），配 1 个内容断言测试即可——不需要 embedding、不需要向量库、不需要检索链路。

### 2. 价值：对"体验收敛"是正收益还是负担？

**当前是净负担，理由四条：**

- **架构错配**：EMC 的行业知识是"权威常量"（Python 模块 + 21 项结构测试守护），本质是查表；RAG 把查表换成"概率检索"，确定性变方差——与 CB 全轮次的核心追求（确定性兜底、trace 取证、可复现）相悖。
- **检索方差是新风险源**：top-k 可能抽错段落、抽到相似但不相关的概念 → 给模型喂"带权威感的错误上下文"，比不给更糟；且需要新的评估面（检索质量评测）才能守住。
- **与"prompt 瘦身"方向相反**：瘦身工程刚把 final 从 17KB 砍到 0.9KB 治了超时；RAG 会在 prompt 里加"检索结果块"，体积与延迟回弹，且多一个外部 API 失败点。
- **与"体验收敛"目标冲突**：收敛 = 减少变量、稳定核心链路（PRM/路由/出口）；RAG = 新增 embedding 依赖 + 向量库 + 检索链路 + 版本化重建，三个子系统级变量。当前 B3 88.5% 刚达标上沿、PRM-08/CPD 还有残余，不是引入新基建的时机。

唯一正收益场景：industry_kb 做厚到单领域渲染 >50KB、或引入外部动态语料（政策原文/论文/案例库）后，"选择性注入"的"键"覆盖不住开放问答时，RAG 才成为必要的伸缩手段。

### 3. 可行性：Py3.14 风险？embedding API？MVP 是什么？

- **Py3.14 + chromadb/faiss：风险真实，不宜硬闯。** chromadb 的 hnswlib 依赖在 3.14 有编译失败记录（#5983），pydantic v2 迁移修复 PR（#5842）尚未合入；faiss-cpu 对 3.14 的 wheel 供应同样不明。项目 225 项 pytest 全部跑在 3.14，为 RAG 换 3.12 venv 属于连锁工程。
- **DeepSeek embedding：无官方端点**（已核实），需新增外部 key（Ark/DashScope/智谱）——.env 现无；本地 sentence-transformers 在 Py3.14 同样 wheel 风险。
- **MVP（若做）——零向量库版：** 20KB 语料按领域模块自然章节分块（≤500 字/块，全库约 40-60 块），检索 = `domain_lens 硬过滤 + 关键词/结构索引 top-k`（可先用 numpy 余弦相似度做语义兜底，无新依赖）；命中 2-3 块注入 finalStep。此 MVP 的"检索"部分 1 天内可完成，但**收益应先用更便宜的 A4 选择性注入验证**——两者共享同一注入接口，A4 先行等于把 MVP 的注入侧先做掉，检索侧后补。

### 4. 时机：现在建 vs 知识做厚后？

**明确：现在不建。** 三原因：
1. 无超限压力（§1 数据）；2. 基建不成熟（Py3.14 向量库 + 无 embedding key + DeepSeek 无端点，三条腿都瘸）；3. 阶段目标是体验收敛，RAG 是逆收敛的复杂度注入。

**正确时间线（建议登记为 RAG 触发条件）：**
- **现在→近期**：A4 选择性注入（finalStep 按 domain_lens 注 brief，<3KB 门禁 + 内容断言）——1-2 天工作量，直接闭合"finalStep 无领域知识"痛点；
- **中期**：industry_kb 做厚（保持 4 领域 × schema 结构，扩充 TOP_DESIGN/CASES/EMOTION_FOCUS/术语），同时把 `docs/industry-knowledge-base.md` 作为编辑入口沉淀素材；
- **触发评估**：当单领域渲染文本 >50KB、或总渲染 >300KB、或引入外部动态语料时，重新评估 RAG——届时先做 §3 MVP 原型（numpy 暴力检索对比选择性注入），用 A/B 实测检索增益，**增益明确再上向量库**。

---

## 三、建议（分级）

| 优先级 | 建议 | 理由/验证 |
|---|---|---|
| **P1（1-2 天）** | **A4 选择性注入**：finalStep 按 `diagnose.domain_lens` 注入对应领域 brief（复用 `industry_kb_brief_text` 单域切片），守 `<3KB` 门禁（对齐 `test_final_prompt_stays_lean` 口径），配内容断言测试（如 `'领域速查' in p`） | 直接闭合 A4；零新依赖；可测可回退。承重提示：diagnose/final prompt 改动前先扩 eval（A4 记录自带此要求） |
| **P2（持续）** | industry_kb 做厚：保持 schema，扩充权威内容；同步 `docs/industry-knowledge-base.md` | RAG 的真正前提是语料质量与规模；做厚过程也是 RAG 触发条件的自然逼近 |
| **P3（触发后再议）** | 真 RAG 原型：numpy 暴力检索（无向量库）对比选择性注入，A/B 实测增益；增益明确再评估 chromadb（或先试 `chromadb-client` 轻客户端/等 #5842 合入） | 避免为 20KB 语料背上 hnswlib/onnxruntime 的 Py3.14 兼容债 |
| **低** | 事实修正入库：知识总量按"渲染体量"口径记账（19.7KB 全文 / 1.1KB brief），DeepSeek 无 embedding 端点记为确定事实（防第三方教程误导后续决策） | 防止"200KB 超限"类误判反复出现 |

---

## 四、判定

- **可行？** 技术上可行，但**当前没有必要**——痛点与方案错配。
- **有价值？** 对"EMC 整体使用体验收敛"**当前无正收益**；有正收益的是"选择性注入"（RAG-lite），它用 1-2 天解决 A4，并保留未来升级 RAG 的接口。
- **方案初稿**：A4 选择性注入 = RAG-MVP 的注入侧先行；检索侧等语料做厚后以"无向量库原型"起步。
- **优先级**：P1 A4 选择性注入 > P2 知识做厚 > P3 真 RAG（触发式）。

---

*本报告为 Codex 组独立评估，未参考其他组报告。事实修正基于本地实测（渲染体量/依赖/注入点）与官方信息检索（DeepSeek/chromadb）。*
