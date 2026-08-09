# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-08-09 | **操作人**：claude组（Claude Code）
> **同步**：git push 后办公室可见。到办公室后读 `OFFICE.md`（公司 08-09 收工卡·最新）。

## 当前状态（08-09 · pull 公司全链后）

- **分支**：`fix/emc-buglog` @ `56cd67b`（与 origin 同步·工作区干净·`434a604..56cd67b` fast-forward）
- **公司 08-09 全链已同步**（OFFICE 卡）：CB-21b 城市更新知识库 + CB-22 RAG/三支柱/三层架构/术语去硬造/杜绝概念创造·pytest 307 + validate 9 + e2e 7
- **进度同步 + 环境检查已发两组**：`docs/catch-ball/discuss/进度同步与环境检查_讨论发起_2026-08-09.md`
- **接手文档**：`OFFICE.md`（公司 08-09 权威卡）+ `DEEPSEEK_ONBOARDING_2026-07-30.md`（历史）

## ⚠️ 家环境检查结果（08-09 pull 后自检）

- ✅ 核心就绪：Python 3.14.6 / pytest 冒烟 41 passed / Playwright 1.61 / trace 工具
- ❌ **RAG 链未就绪**：依赖未装（`pip install -r requirements-rag.txt`）· 索引未建（`py tools/rag_index.py --build`）· BGE 模型未缓存（需 `HF_ENDPOINT=https://hf-mirror.com`）· 家无 G 盘
- ⚠️ .env 缺 `AMAP_KEY`（仅 DEEPSEEK_API_KEY）

## 待做（优先级排序）

- [ ] **RAG 补链**（若家做 RAG 任务）：装 requirements-rag.txt → BGE 模型（HF 镜像）→ `rag_index.py --build` 重建索引
- [ ] 补 .env `AMAP_KEY`（高德 POI/逆地理用例必需）
- [ ] 等待两组回应 `进度同步与环境检查_回应_{组}_2026-08-09.md` → /cb 反评价收敛
- [ ] 公司待做（OFFICE 卡）：B 路径 query_knowledge_base · 混合检索 · 全仓 [中文]+类 扫描 · Recall@5 · P0-6 复审 · L2 出向任务

## 关键文件速查

| 看什么 | 路径 |
|------|------|
| CB 入口 | `docs/catch-ball/_cb-index.md` |
| CB 轨迹 | `docs/catch-ball/cb-journal.md`（CB-19 最新） |
| 发版回归结果 | `docs/catch-ball/discuss/发版回归全面测试_结果_*2026-08-08.md` |
| todo 日志 | `docs/todo.md` |
| revision-log | `docs/revision-log.md` |
| 记忆索引 | `~/.claude/projects/d--Github-emotion-map/memory/MEMORY.md` |
