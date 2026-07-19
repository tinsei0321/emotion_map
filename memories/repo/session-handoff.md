# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月19日（**CB 三轮收尾完成 + 工作策略厘清**）| 分支 `main` | 本次会话 = 5.136–5.139

---

## 当前节点：CB 三轮收尾完成；下一会话推进**极性深读时间轴**（T1→T3 演进）

### 背景
三轮 catch-ball（CB-01/02/03）完成项目质量巩固 + CB 自动化建设 + 工作策略厘清。CB-03 后 CB 转**低频维护模式**（每 5-10 功能 commit 一次 SCAN）。用户定：**先 CB 收尾（done），再开新会话推进时间轴**（守调用次数优先策略——任务边界切会话）。

### 三轮 CB 战果（详见 [docs/catch-ball/cb-journal.md](docs/catch-ball/cb-journal.md)）
- **CB-01**（7.6）：删 5 僵尸（Streamlit/pydeck/db，-2257 行）/ geo_routes 清理 / sim 注册 / e2e seam 去生产化 / §0 刷新。
- **CB-02**（7.6）：requirements 僵尸依赖清 / range_selector 路径大小写 / AGENTS.md 8→9+概念框架声明 / generate_l1_mock 退役 / generate_test_data declined（事实错误：L0 raw 非冗余）。
- **CB-03**（7.7 首升·META 轮）：CB 自动化 5 组件全 A；RULES §3.3 pointer KNOWLEDGE §1 / KNOWLEDGE §6 Auto-Check + pruning + cadence / /cb step5 数据驱动 / trace-digest 闭环更正 / 拓扑同步（cb-flow 边 11 条入图）。
- **工作策略厘清**（5.138）：全局 `~/.claude/CLAUDE.md` 加「调用次数优先策略」（三层防御：会话切分首选 / 主线程精准读默认 / subagent 仅大宗隔离）；统一矛盾 memo（`token-saving-workstyle` 重写）。

### ✅ 本会话已做（5.136–5.139）

| commit | 5.NNN | 内容 |
|---|---|---|
| `87979cc` | 5.136 | CB 自动化（/cb 命令 + hook 检测 + KNOWLEDGE 记忆库 + 记忆共享通则 + 路径迁移） |
| `6bdc9ac` | 5.137 | CB-02 反评价 dogfood（5 agree + 1 declined + 5 defer） |
| `fa5073e` | 5.138 | 工作策略厘清（调用次数优先 + 三层防御，统一矛盾 memo）+ CB-03 输入 |
| （本次） | 5.139 | CB 收尾（CB-03 反评价 + 拓扑同步 cb-flow + core/CLAUDE.md 清） |

前 3 个已 push（origin/main）。5.139 待 push。

### 🎯 下一会话：极性深读时间轴（T1→T3 演进动画）

来自 revision-log §0 临时分支「待决策」：
- **任务**：极性深读·时间轴——T1→T3 极性成效动画（演示张力随时间演化，服务北极星"张力图面"）。
- **路线**（待择）：A JS rAF + setData（推荐，轻量）/ B deck.gl 重引入（重）/ C 阶梯淡入。
- **前置**：Overview 原地更新重构（时间轴焦点切换时 Overview 即时追随，不全量重渲）。
- **范围**：仅 L2·综合·标准网格 焦点层时显时间轴（scaffold cell 承载 T1→T3）。

### 承重（必守）
- **调用次数优先策略**（全局 `~/.claude/CLAUDE.md` 唯一权威）：默认主线程 + 会话切分首选 + subagent 仅大宗隔离；批量并行/合并修改/给推荐不穷举/不跑非必要验证沿用。
- **CB 低频维护**：CB-03 后每 5-10 功能 commit 一次 SCAN（非每轮即 SCAN）；hook detector 保留提示。
- **CB 反评价标尺**：agree/disagree/partial 有论据；承重红线（tracker 编号连续 / diagnose 永不动 / 四态 / L0 购买）不接受简化；不编辑 `docs/catch-ball/SCAN_DeepSeek_{NN}.md`（第三方只读）。
- **记忆共享通则**：任何记忆/子系统须登记 context-map + 双链 + 不孤岛（CB KNOWLEDGE 为首例）。
- **拓扑同步纪律**：新子系统 → 加 §0 分支 + topo_scanner 语义边（防拓扑漂移）。
- 专业词+通俗解释；todo+revision-log 置顶同步；只 commit 不 push（用户手动）。

### 本轮改的关键文件
- **CB-03 反评价**：[cb-journal.md](docs/catch-ball/cb-journal.md) CB-03 ②③④ / [RULES.md](docs/catch-ball/RULES.md) §3.3 pointer / [KNOWLEDGE.md](docs/catch-ball/KNOWLEDGE.md) §6+维护 / [cb.md](.claude/commands/cb.md) step5。
- **拓扑同步**：[revision-log.md](docs/revision-log.md) §0 + Catch-Ball 分支 / [topo_scanner.py](core/topo_scanner.py) cb-flow 边 / [core/CLAUDE.md](core/CLAUDE.md) 去退役。
- **memory（机本地）**：`topo-sync-discipline`（新）+ MEMORY.md 索引。

### 跨环境待办（Hi 机补写，机本地 ~/.claude）
全局 CLAUDE.md「调用次数优先策略」节 + memory（token-saving-workstyle 重写 / communication-style / cb-knowledge-base / topo-sync-discipline）+ MEMORY.md 索引——admin 独有，Hi 机需复制。

---

## 新会话 prompt（极性深读时间轴，复制即用）

```
接续 07-19 会话（CB 三轮收尾 done + 工作策略厘清，5.136-5.139，详见 memories/repo/session-handoff.md）。
本会话目标：推进极性深读时间轴（T1→T3 演进动画）—— revision-log §0 临时分支「待决策」项。

先读（不动代码）：
- memories/repo/session-handoff.md（当前节点 + 承重）
- docs/revision-log.md §0 临时分支（时间轴路线 A/B/C + 前置 Overview 重构）
- frontend/js/panel.js refreshOverview（时间轴显隐逻辑）+ timeline.js（现有 scaffold）

承重：调用次数优先策略（全局；默认主线程+会话切分+大宗隔离）/ CB 低频维护 / 承重红线（时间轴改动勿碰四态/diagnose）/ 拓扑同步（若加新组件）。
建议先 plan 路线选择（A JS rAF 推荐 vs B deck.gl）+ Overview 原地更新前置。
```
