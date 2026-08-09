# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-08-10 | **操作人**：claude组（Claude Code）
> **同步**：git push 后办公室可见。到办公室后读 `OFFICE.md`（公司 08-09 收工卡·最新）。

## 当前状态（08-10 · CB-22d 讨论中）

- **分支**：`fix/emc-buglog` @ `f94d3cd`（与 origin 同步·工作区干净）
- **CB-22d 知识问答→地图标记**（进行中·等两组详细评估）：
  - 场景：问项目→文字回答 OK；追问「能在地图上标记吗」→ EMC 无法完成
  - 根因（用户判断深化）：Smart/Dumb 接口断裂（计划→执行脱节）·非地点精度
  - 两组回应已回收（glm + Codex）→ 反评价裁决（采纳 Codex 归 gis_operation + glm 内核）
  - 定稿 plan：`generate_point_layer` 工具 + 三级面化回退 + 路由使能 + 契约豁免
  - 落 [综合plan反评价](docs/catch-ball/discuss/CB22d-知识问答到地图标记_综合plan反评价_2026-08-10.md)（6 焦点请两组详细评估）·cb-journal CB-22d 段已记
- **待**：两组 `综合plan评估_{组}_2026-08-10.md` → claude组 收敛 → 实施
- **接手文档**：`OFFICE.md`（公司 08-09 权威卡）+ `DEEPSEEK_ONBOARDING_2026-07-30.md`（历史）

## ✅ 家环境 RAG 补链完成（08-09 晚·用户要求补齐环境）

- ✅ **依赖已装**：torch `2.13.0+cpu`（**PyPI 默认源无 `+cpu` 标签·改用阿里云 `mirrors.aliyun.com/pytorch-wheels/cpu` 直装 wheel**）+ sentence-transformers 5.7.0
- ✅ **BGE 模型已缓存**：`BAAI/bge-small-zh-v1.5`（HF 镜像自动下载·`~/.cache/huggingface`）
- ✅ **索引已重建**：`data/rag_index/` 235 条（事实 36 + 笔记 185 + case 5 + 概念卡 9·维度 512）
- ✅ **检索冒烟通过**：`--query "葛洲坝有哪些更新项目"` → Top-5 含 fact（URP-P02/P01）+ note
- ⚠️ 仍缺 `AMAP_KEY`（B3 高德类用例需补 .env）
- 家无 G 盘（L0 原始资料以 git 内 `docs/urban-renewal-plan/` 为准·不阻塞）

## 待做（优先级排序）

- [ ] 补 .env `AMAP_KEY`（高德 POI/逆地理用例必需）
- [ ] 等待两组回应 `进度同步与环境检查_回应_{组}_2026-08-09.md` + `三组进入状态通知` 就绪确认 → /cb 反评价收敛 → 发 RAG 遗留任务分配
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
