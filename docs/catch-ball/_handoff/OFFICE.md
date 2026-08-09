# 办公室 · 工作交接卡

> **位置**：办公室 | **最后更新**：2026-08-09（今日收工） | **操作人**：claude组（Claude Code）
> **同步**：今日全链已 commit（待 push 后 git pull 同步·含 RAG 依赖环境提醒）。

## 今日完成（08-09 · CB-21b 知识库 + CB-22 全链）

**CB-21b 城市更新专项规划知识库**：L0 资料库（`docs/urban-renewal-plan/`·875 文件提炼）+ L1 知识库（`urban_renewal.py`·305 passed）+ 三组协同。

**CB-22 系列全链闭环（用户实测通过）**：
- **RAG 建设**：本地 BGE embedding + 事实卡 35 + 索引 235 条 + `/aiqa/rag_search` + harness 短路
- **三支柱对齐**（承重发现：素材内容从未入索引·注入仅文件名·已修 meta 存 text）+ 两组复验
- **三层架构优化**（用户主导·NL 意图判断必须 LLM）：diagnose 加 `knowledge_qa` 枚举（意图判断归位·红线豁免）+ _quickIntent 降级加速器 + `_assembleKnowledgeQA` 合流 + 概念库 9 条 + 防回归
- **素材术语去硬造 + 来源标注弱化**：URP-P01/笔记:43/总览报告去「典型片区类/机制建设类」·罗列式·`〔来源：可读名称〕` + CSS 0.85em 浅灰
- **杜绝概念创造 3 层治本防线**（用户「记住」）：CLAUDE.md 铁律 13 + KNOWLEDGE + AutoMemory + 全仓黑名单断言 + 指令 3 禁推断

## 明天待做（公司电脑·RAG 遗留强调）

- [ ] **用户复测本轮全链**（无硬造分类 + 来源弱化）→ 通过后 **push 今日全链 commit**（多 commit 未推）
- [ ] **B 路径（CB-22b·query_knowledge_base 确定性查询）**——RAG_QUERY_KW 临时结构化词待迁移·`knowledge_query` 范式已预留
- [ ] **混合检索**（P1·glm/Codex 共识）：fact 加权或 Top-5 保底 ≥1 fact·降 note 占比（当前「有哪些更新项目」Top-5 全 note·fact 短文本向量信号弱）
- [ ] **全仓 `[中文]+类` 扫描 + 逐条核实源文档**（黑名单机制 + 人工审新词）
- [ ] **Recall@5 素材质量机制**（Codex V5·黄金集 Recall≥80% 持续跟踪）
- [ ] **P0-6 分通道 tier 复审**（暂缓·flash 保持·路径跑顺后**勿忘**·glm 提醒知识问答开 pro）
- [ ] L2 出向任务（outlet_kb 接入运行时·进 CB 讨论）

## ⚠️ 换环境提醒（重要）

**当前 git 分支 `fix/emc-buglog` 有较多未 push commit（今日全链）**。换环境（家/公司）前：
1. `git pull`（拉取最新·含今日全链）
2. **本地 RAG 依赖**：`pip install -r requirements-rag.txt`（sentence-transformers + torch·Py3.14）+ 首次下载 BGE 模型需 HF 镜像（`HF_ENDPOINT=https://hf-mirror.com`）
3. **数据索引**：`py tools/rag_index.py --build`（重建 235 条向量索引·本地·不入 git——**索引不入 git·换环境必须重建**）
4. **G 盘资料库**：`G:\OneDrive\2026\15_城市更新专项规划研究\` 需 OneDrive 同步（体检/GIS/政策原始资料）

## 关键文件速查

| 看什么 | 路径 |
|------|------|
| CB 入口 | `docs/catch-ball/_cb-index.md` |
| 今日全链 | `docs/catch-ball/discuss/CB22-三层架构优化_*` + `CB22-杜绝概念创造_*` + `CB22-素材术语与来源排版_*` |
| 记忆索引 | `~/.claude/projects/d--Github-emotion-map/memory/MEMORY.md` |
| 新纪律 | CLAUDE.md 铁律 13（禁非专业概念创造）·KNOWLEDGE §2 术语纪律三分 |

## 关键 learning（今日·防踩坑）

- **RAG 索引必须存 text**（承重发现：只存 source/hash·LLM 无内容可综合·三支柱①空转）
- **改素材要全仓**（fact 卡 + 笔记段落 + 总览报告都要改·曾漏 note 致 LLM 综合出硬造分类·Codex 漏改发现）
- **杜绝非专业概念创造**（用户「记住」）：分类术语须源文档可溯·禁硬造分类名/LLM 自创解释·提炼笔记同样适用
- **来源标注 = 可读名称**（完整文件名或提炼标题·非内部代号·用户能看懂）
- **e2e 测试确定性**（injectOnly 去 LLM 依赖·消冷加载竞态 flaky）
- **检索「有哪些更新项目」Top-5 全 note**（fact 短文本信号弱·混合检索 P1 待做）
