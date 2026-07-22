# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月22日（**CB-CPD 专轨收敛 · CPD 核心 plan v1.0 定稿；EMC 浮窗交互改进已 commit 待验；换环境推进 P0 测试铺底**）| 分支 `cpd`

---

## 当前节点：CPD 核心 plan v1.0 定稿（三轮 CB-CPD 收敛）；下一步 = 前端 F5 验 + P0 测试铺底

### 本会话做了什么（分支 cpd）
1. **CB-CPD 专轨三轮闭环 → plan v1.0 定稿**（DeepSeek + K3 双模型，47 条建议 agree 35 / partial 12 / disagree 0，承重零触）：
   - v0.1→v0.3（CB-CPD-01）：修 3 spec 错误（`.aiq-conclusion` 死信号→`.aiq-exit-badge` / exit 大写词表→小写五值 / 映射 key=curState→特征向量真值表）+ 演示表现力升维（S3 空间交互 / S4 地图闭合 / 文案叙事化）。
   - v0.3→v0.4（CB-CPD-02）：两份收敛（init 循环 import→依赖注入 / S4 动态变量无源→降级 {区域名}）+ 色名同步色带（深红→深橙）。
   - v0.4→**v1.0**（CB-CPD-03）：修 K3 发现的 H1 链式缺陷（general 断链静默冻结→`settled` 守卫 + 单调去重）+ M1 interpret 分支（dock→EMC）+ M2 谓词收紧（判情绪性）。
   - 核心 6 决策全自洽，演示 C+→B+。
2. **CB 机制强化**：RULES 六轴→七轴（加演示表现力 10%）/ KNOWLEDGE §2 演示逻辑链北极星 / review.md prompt 自包含 + SCAN 命名 `-{model}` + 模型署名。
3. **EMC 浮窗交互改进**（前端，已 commit 待 F5 验）：F5 默认折叠欢迎卡（不记忆上轮态，430×640）+ 内容驱动高度自适应（增量法，修 flex 撑满 scrollHeight 失真）+ exit-badge 去线框改填充 teal（避免线框设计原则）+ 历史垃圾桶加大 / 一键全清。

### v1.0 核心 6 架构决策（已自洽）
特征向量真值表 / `.aiq-exit-badge` 信号 / 小写 exit ∪ null / `settled` 守卫 + 单调去重 / 依赖注入 init（panel.js→cpd-guide.js 单向）/ streaming 第一优先。详见 [docs/cpd-core-plan.md](../../docs/cpd-core-plan.md) 定稿声明。

### 下一步（换环境）
1. **前端 F5 验**（panel.js / index.html / ai_qa.css 已 commit，未验）：折叠欢迎卡 + 高度自适应缩回（拉长+缩回）+ exit-badge teal 填充 + 历史桶加大/全清。验 OK 进 P0；有问题修后再处理。
2. **P0 测试铺底**（plan §八）：扩 `docs/emc-test-cases.md`（地基行为用例 4→N）+ 落地 `tests/browser/`（复用 emc_helpers.py，断言挂真端点）。
3. **P1 尺度诚实**：`ai_qa/review.py:50` `scale_paradigm_fit` desc 强化 + 灰度（≥10 条历史微观问题对比 fail 率）+ U7 三态分级 + docstring 六条→七条。
4. **P2 引擎 G1-G4**：`cpd-guide.js`（依赖注入 init + 特征向量 + turn-ended `settled` + 单调去重 + 光环可点）。
5. 新会话 prompt 见下方。

### 承重（必守）
- **调用次数优先**（全局唯一权威）：默认主线程 + 会话切分 + subagent 仅大宗隔离。**不派 Explore/Plan subagent**（覆盖 plan mode 默认）。
- **diagnose prompt 永不动**（保 eval）/ 四态出口不动（小写五值 `result/gap/partial/ask/drift` + general 短路无 exit）/ harness/stages/tools/tracker 不动 / curState 纯客户端。
- **CPD plan v1.0 已定稿**（CB-CPD 专轨收尾）；实施中若发现 plan 层新问题再开 CB-CPD-04。
- **EMC 颜色全走 theme var**（含光环渐变 `--emc-halo-*`，G2/G4 落）；**避免线框**（填充式胶囊，memory `avoid-frames-fill-style`）；**色名同步色带**（从 `--geojson-color-emotion-very-*` 派生，无"深红"）。
- 只 commit 不 push（用户手动 push）；**本次收工用户明确 push**。

### 关键文件
- **`docs/cpd-core-plan.md`**（v1.0 定稿，权威 + 定稿声明 + roadmap）
- `docs/cpd-core-plan-review.md`（CB 专轨 + prompt 自包含 + §七 定稿声明）
- `docs/catch-ball/`（cb-journal CB-CPD-01/02/03 + SCAN_01-03 + RULES/KNOWLEDGE）
- `ai_qa/review.py:50`（scale_paradigm_fit，P1 改）
- `frontend/js/ai_qa/{panel.js,cpd-state.js,harness.js,tools.js}`（P2 G1 落点）
- `docs/emc-test-cases.md` + `tests/browser/lib/emc_helpers.py`（P0）

---

## 新会话 prompt（CPD v1.0 实施 P0 测试铺底，复制即用）

```
接续 cpd 分支 CPD 核心 plan v1.0 定稿（CB-CPD 三轮收敛）的实施。
读：docs/cpd-core-plan.md（v1.0 §八 P0 + 定稿声明）+ docs/cpd-core-plan-review.md §七（收敛）+ docs/emc-test-cases.md（4 例现状）+ tests/browser/lib/emc_helpers.py。
任务：① 先 F5 验前端 3 文件（panel.js/index.html/ai_qa.css：F5 折叠欢迎卡 + 高度自适应缩回 + exit-badge teal，已 commit 未验）→ 验 OK 进 P0；② P0 扩 emc-test-cases（地基行为用例）+ 落 tests/browser（复用 emc_helpers，断言挂真端点）。
承重：调用次数优先 / 不派 subagent / 只 commit 不 push / diagnose 与四态出口不动 / plan v1.0 已定稿不再 CB 迭代（除非实施发现 plan 层新问题）。
```
