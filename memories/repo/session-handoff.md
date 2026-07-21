# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月22日（**CPD UI 地基全完 + 多轮精修暂时 OK；下一步 = CPD 核心引导逻辑 plan，建议新会话**）| 分支 `cpd` | HEAD `0fd3629`

---

## 当前节点：CPD UI 地基完工；下一步 = CPD 核心引导逻辑（新会话进 plan）

### 重要范围校正（用户明确）
**CPD 才刚开始**。至今所成 = **CPD 的「地基」**：EMC 浮窗 + 软折叠 chip/抽屉 + curState 反映 + 色带/主题/三级权重 + 自适应位置 + 折叠光环/chip/进度点。这些是**容器和表皮**。
**CPD 核心（未开始）= EMC 作为主控，引导情绪地图的所有功能体验**：import/range/layers/toolbox(KDE/Grid/Buffer/归因)/timeline T1-T3/compare 批4/export/search + EMC 问答，**全部经 EMC 交互引导**完成。curState 从「反映」升级为「**编排**」——EMC 每阶段主动奉上「此刻唯一动作」，调度底层。**如何引导/实现需详细 plan**。

**不合分支、不抽离模块**——都在 cpd 分支继续，CPD 真正完成才谈。

### ✅ 本会话已做（分支 cpd，全量 push 到 origin/cpd）

| Phase | 内容 |
|---|---|
| Phase 0 | 3220 真实 POI 入库 `core/place_layer.py`（commit be3f6b3） |
| Phase 1 | 工具簇横排→底部 dock 圆钮 + EMC 浮窗化 + 多轮精修 |
| Phase 2a/2b | CPD 软折叠壳：`cpd-state.js` 客户端 curState 推导（不动 diagnose）+ 进度条/chip 行 + 左栏→chip 唤出抽屉 + 自适应位置（`positionDrawer`/`positionFloatingPanels`/`relayoutFloats`）+ param-panel 浮窗卡 |
| Phase 3a/3b/3c | 情绪五级色带「正冷/负暖」对齐 design-system + 主题切换（默认 Light·yakushimabus 森绿金黄）+ EMC 三级权重 CSS（结论卡浮出/过程卡/审查胶囊）|
| 精修轮 | 折叠欢迎胶囊（Gemini 星 + 光环「淡出→再现」+ `.has-guidance` 飞快色引导钩子 + 临时测试 Ctrl+Shift+G）+ 追问胶囊/容量圈 theme 同步（铁律：EMC 颜色全走 theme var）+ chip 凸出 + 进度点 hover 提示 |

**最近 commit**：0fd3629（光环淡出/引导飞快色 + chip 凸出 + 进度点提示）。详见 revision-log §5.165-5.171。

### 🔧 引导耦合钩子已就绪（待 CPD 核心 toggle）
- 折叠胶囊 `.has-guidance` 类（CSS 定义）：加类→光环飞快颜色交替（强吸引）；CPD 核心 toggle 它（有新引导→加类 + 更新 `#chat-input` placeholder + `_fitCollapsedText` + 高度自适应）。
- 临时测试：`Ctrl+Shift+G` 模拟新引导（panel.js `_setupCpdBar`，CPD 核心上线后删）。

### 承重（必守）
- **调用次数优先**（全局 ~/.claude 唯一权威）：默认主线程 + 会话切分首选 + subagent 仅大宗隔离。**不派 Explore/Plan subagent**（直接自己读/grep/规划，覆盖 plan mode 默认）。
- **diagnose prompt 永不动**（保 eval）→ curState 纯客户端推导；四态出口(EXIT_RESULT/GAP/PARTIAL/CONCEPT)/tracker 签名/网格算法/paint-inplace 不动。
- **EMC 颜色全走 theme var**（`var(--geojson-color-*)`/`var(--emc-accent)`/`var(--emc-divider)`），**严禁硬编码** hex/rgba（反复踩坑，5.169 根治；memory `apply-design-sense-no-bounce` §5）。
- **自适应位置铁律**：浮层 left 随锚点(EMC/抽屉)右沿动态算（`getBoundingClientRect().right+gap`），勿写死固定 left（memory `adaptive-position-design-rule`）。
- **设计决策先自判别甩用户**：视觉琐问(方向/尺寸/颜色)据常识+memory 习惯直接定，别回弹（memory `apply-design-sense-no-bounce`）。
- 批4 grid 镜像 bug + diag 日志(b13eb62)→ main 遗留，CPD 期间不动。
- 只 commit 不 push（用户手动 push）；commit 后告知"待你 push"。

### 关键文件
- `docs/design-system.md`（设计 single source of truth，冲突以它为准）
- `frontend/js/ai_qa/cpd-state.js`（curState 推导 + positionDrawer/positionFloatingPanels/relayoutFloats + initCpdState）
- `frontend/js/ai_qa/panel.js`（EMC 浮窗 _setupEmcFloat + _setupCpdBar 进度/chip + _fitCollapsedText 文本自适应 + 折叠光环 `.has-guidance` 钩子 + 主题切换 + 临时 Ctrl+Shift+G）
- `frontend/js/ai_qa/harness.js`（五步 diagnose/agent/final/review/revise + 四态出口——**不动**）
- `frontend/css/ai_qa.css`（EMC 全样式：浮窗/折叠光环/欢迎胶囊/chip/进度点/三级权重/Light scope）
- `frontend/css/layout.css`（#emc-panel 浮窗几何 + #left-panel 抽屉化）
- `design/tokens.json` + `generate_css.py`（色带单一源 → tokens.css/py）
- `core/place_layer.py`（POI 库，无 DB）

---

## 新会话 prompt（CPD 核心引导逻辑 plan，复制即用）

```
接续 cpd 分支（CPD UI 地基全完 + 多轮精修暂时 OK，详见 memories/repo/session-handoff.md + docs/revision-log.md §5.165-5.171）。
本会话目标：开 CPD 核心引导逻辑的详细 plan（进 plan 模式）——EMC 作为主控，引导情绪地图所有功能体验。

【先读，不动代码】
- memories/repo/session-handoff.md（当前节点 + 承重 + 范围校正：CPD 才刚开始，核心=EMC 编排所有功能）
- docs/design-system.md §4（情境式渐进披露状态机 S0-S5 + 出现/隐身规则）
- frontend/js/ai_qa/cpd-state.js（curState 客户端推导 + positionDrawer 等自适应）
- frontend/js/ai_qa/harness.js（五步+四态出口——不动；理解 EMC 路由边界）
- frontend/js/ai_qa/panel.js（_setupCpdBar 进度/chip + _fitCollapsedText + .has-guidance 钩子）
- memory cpd-soft-collapse / apply-design-sense-no-bounce / adaptive-position-design-rule

【plan 要覆盖】
1. 功能图谱：情绪地图全部能力(import/range/layers/toolbox·KDE/Grid/Buffer/归因/timeline T1-T3/compare 批4/export/search)+EMC 问答，逐一标注「已由 EMC 引导 / 仍是裸按钮 / 待编排」。
2. 引导状态机：curState 从「反映」升「编排」——每态 EMC 主动作 + 唤出/隐身规则 + 与 harness/工具链的调度接口（不改 diagnose/四态出口）。
3. 对话→功能桥：用户自然语言意图如何经 EMC 路由到底层功能，结论如何回灌引导下一步。
4. 渐进披露细则：每功能「何时出现/如何呈现/用完如何退场」+ 折叠胶囊引导耦合（.has-guidance toggle + 文本/高度自适应 + engage 解除 + curState 联动）。
5. 承重边界：diagnose 不动 / 四态出口不动 / curState 客户端推导 / 自适应位置 / EMC 颜色 theme var。

承重：调用次数优先 / 不派 Explore·Plan subagent / 只 commit 不 push。
不合分支、不抽离模块——CPD 真正完成才谈。
```
