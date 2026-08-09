# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-08-10 | **操作人**：claude组（Claude Code）
> **同步**：git push 后办公室可见。到办公室后读 `OFFICE.md`（公司 08-09 收工卡·最新）。

## 当前状态（08-10 · CB-22d 收敛定稿）

- **分支**：`fix/emc-buglog` @ `200f928`（与 origin 同步·工作区干净）
- **CB-22d 知识问答→地图标记**（反评价收敛定稿·待用户确认后实施）：
  - 场景：问项目→文字回答 OK；追问「能在地图上标记吗」→ EMC 无法完成
  - 根因（用户判断深化）：Smart/Dumb 接口断裂（计划→执行脱节）·非地点精度
  - 两组详细评估 → **7 项缺陷全核实**（resume 恒 false / FC 走契约 when / priorTurn 无 final / runTemplatePath ask_user / _dataGate 误拦 / 面化白名单 / SLOT_HINT）
  - 修正版 plan：[反评价收敛定稿](docs/catch-ball/discuss/CB22d-知识问答到地图标记_反评价收敛定稿_2026-08-10.md)（P0-0 前置接线 + P0-1 工具 + P0-2 FC 路由 + P0-3 豁免 + P0-4 测试 + P1 数据增强）
  - **glm 最高价值判断**：不修则「工具实现了却从不被触发」= 修复层面重演用户说的「计划与执行脱节」
- **待**：用户确认 ① 验收口径（tier-2 行政区级面+标注可接受？）② 实施时机 → 实施（claude 开发 + 两组复验）
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
