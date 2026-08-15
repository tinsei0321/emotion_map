---
name: cpd-soft-collapse
description: CPD 系统级重构决策——EMC 升底层主控、软折叠（非严格隐身）、curState 客户端推导不碰 diagnose、浮窗 resize:both
metadata: 
  node_type: memory
  type: project
  originSessionId: ab9ecdfe-67aa-400a-9932-8d2c86b24a90
  modified: 2026-07-21T12:18:23.825Z
---

**CPD（情境式渐进披露）系统级重构**（2026-07-21 启动，分支 `cpd` from main，plan `~/.claude/plans/07-21-4-swipe-compressed-dawn.md`）。EMC 升为系统底层主控，摈弃工程化操作体验（左栏常驻 Range/Layers/Toolbox），「此时此刻需要什么=出现对应提示」。

**三项拍板决策**（用户 AskUserQuestion）：
1. **1623 行政边界** → 注册为 boundary preset（实际=已有 `admin_district` preset 同 9 区，无需重复），**不替换 6 叙事区**（classify_point 不动，零回归）。
2. **CPD 强度 = 软折叠**（非 design-system §4 严格隐身）：工程控件折叠为摘要 chip、**保留一键展开**（业内同行 demo 不迷路）。chip 行始终可达，EMC 引导为主但不锁死路径。
3. **右栏 Overview/Table** → **保留独立右栏**（承重不破；EMC 专注引导/归因）。

**承重红线**：`diagnose` prompt **永不动**（保 eval，[[emc-eval-empty-context-vs-runtime]]）→ CPD 的 `curState`（S0-S5）**客户端从会话状态推导**（新增 `frontend/js/ai_qa/cpd-state.js`，信号=getSelectedLayer/visible layers/range/结论卡），**不进 diagnose 输出、不进 LLM context 必需项**（可作 buildContext 可选 hint，不影响路由）。四态出口（EXIT_RESULT/GAP/PARTIAL/CONCEPT）/tracker 签名/网格算法/paint-inplace 不动。

**Phase 1 已落**（commit 07ed76d）：工具簇横排（比例尺左+按钮列右）+ EMC 浮窗（`position:absolute` 浮 `#map` 左上 + 原生 `resize:both` 高帧率双向缩放 + localStorage 持久化 + 初始折叠条）。`--emc-h` 三档自动调高（setEmcMode/comfort/compact/expand）**退役为无害 no-op**（CPD 摒弃工程化自动调高 → 用户自持尺寸）。左栏 `#left-panel` 暂留，Phase 2 加 CPD chip 后再撤。

**Phase 2 待做**：`cpd-state.js` + EMC 顶部进度条+摘要 chip 行+主动作卡 + `sidebar.js renderLayerList` 等 pane 渲染换宿主（EMC 抽屉）+ 撤 `#left-panel` + `buildContext` 增 curState 可选 hint。
**Phase 3 待做**：design-system 正冷/负暖五色带对齐 tokens + Light·yakushimabus（森绿 `#143a35`+金黄，参考 yakushimabus.com）+ EMC 三级权重。
**Phase 4 附加**（CPD 完成后提示用户）：CPD 抽象为可复用底层架构（skill/模块模板）。

main 遗留（批4 grid 镜像 bug + b13eb62 `[compare]` diag 日志）延后到 cpd 合并后。关联 [[poi-library-is-place-layer]]、[[view-data-conclusion-sync]]、[[design-language-consistency-iron-rule]]。
