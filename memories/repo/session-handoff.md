# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月09日 | 分支 `main` | 本次 = EMC UI 重设计（详见 revision-log 5.48，本次 commit）

---

## 当前节点：EMC（EmotionMap Copilot）UI 重设计 · 左端栏融合 · 已实现+自检过（待肉眼验）

### 背景
AI 问答功能基座已稳（意图路由 + 工具链 $n + 产物验证 gate + 多轮上下文 + 多会话 + 操作按钮 + 诚实铁律）。本轮把它从**底部独立抽屉**重设计为**融入左端栏的 EMC**（VS Code Claude Code 插件式），并对齐 Claude Code 对话交互语言。**承重逻辑全程未碰**（视野-数据-结论同步 / KDE cascade-exclude / 4×5 归因 / 对称拉伸 / tip-popup）。

### ✅ 本会话已做（7 块 + token + 2 bug 修，详见 revision-log 5.48）
1. **结构重组** [index.html](frontend/index.html) + [layout.css](frontend/css/layout.css)：`#left-panel` 上下分区——上半 `#lp-upper`（Range/Layers/Toolbox）+ 横向拖拽条 `.gutter-emc` + 下半 `#emc-panel`（EMC）；默认宽 240→**380**。
2. **EMC 迁入 + 重命名 + 去控件**：删 `#chat-trigger` FAB + `#chat-close` ×；标题 "AI 规划问答"→**"EmotionMap Copilot"**；容器 `#chat-panel`→`#emc-panel`（dock 流内，退 fixed 抽屉）。
3. **历史 1:1 Claude Code** [panel.js](frontend/js/ai_qa/panel.js)：就地视图切换（chat↔history）+ 搜索框 + 列表（标题+时间+垃圾桶）；数据层 `_archive`/`_history`/`switchSession`/`deleteSession` **零改**，仅视图层重写。
4. **Pro/Flash 移至发送左侧**：输入底部条 = `[ctx 圈][+ 附加][Pro|Flash] … [↑发送]`。
5. **textarea 加高 2×**：min 76px / 封顶 160px 自适应。
6. **智能高度三档**（compact 160 / comfort 窗口½ / expand 窗口⅔）：图层堆积→让位、对话/流式→撑开、选层→重算；**手动拖设 `--emc-h-user` 基线、自动围绕基线回退**。`setEmcMode()` + layer-list `MutationObserver` + EMC 生命周期/地图焦点钩子。
7. **Claude Code 交互语言对齐**：Thinking 头 `Thought for Ns · Nk token`（可折叠）+ 工具调用卡（renderToolCard：名+目标+✓/✕+结果可展开）+ Esc 中断 + 助手 hover 复制 + 代码块语言标签+复制。
- **token** [tokens.json](design/tokens.json)：左栏 `leftPanelMin` 220→300、`leftPanelWidth` 240→380，重跑 `generate_css.py` 同步 [tokens.css](frontend/css/tokens.css)（顺带修其与 json 既有 240 不同步）。
- **2 bug 修**（Playwright 自检发现）：① `.gutter-emc` 被 layout.css 后定义的 `.gutter` 同优先级反覆盖（col-resize）→ 提优先级 `.gutter.gutter-emc`；② `_checkCrowded` 读到隐藏但渲染的 `.lp-zone-operate` 误判拥挤→加「无图层→comfort」前置守卫。

### 🔍 自检（Playwright，已过）
console 无 JS 报错（仅 favicon 404）｜初始 EMC=comfort(425px=窗口½)｜gutter `row-resize`/379×8｜历史视图切换+搜索+列表渲染 ✓｜title="EmotionMap Copilot"｜trigger/close 已删｜input rows=3/minH=76｜panel.js/sidebar.js ESM 语法 ✓。

### ⬜ 下会话：用户肉眼验 + 后续

**肉眼验清单**（需真环境/数据）：
1. 拖 `.gutter-emc` 上下调高；上半缩到窗口 1/3 卡住、EMC 缩到一对话框(160)卡住；拖后设基线、自动调度回落基线。
2. 真实 AI 查询（需 API key + 已导入数据）：看工具卡/Thinking 头/复制/Esc 中断的实际效果。
3. 历史搜索过滤 + 多会话点选进入 + 垃圾桶删除。
4. 图层堆积（连生成 grid/KDE/buffer）→ EMC 自动让位 compact；删层→回 comfort。
5. **遗留清理**：`frontend/js/ai_qa/panel.js.tmp.7336.8a8a4e4363a8`（上轮崩溃残留临时文件，未被引用；删属红线，留给用户 `rm`）。

**后续可选**（EMC 留 UI 后做的，原计划）：
- 多模态截图（用户贴图 → EMC 识图入上下文）。
- 主动建议（基于当前地图状态主动提示问题）。
- 报告生成（依赖新 UI 范式 + L4 归因）。

### 承重（必守，本轮未碰但下会话续改 EMC 时留意）
- panel.js **不 import** map/state/panel 主窗口写函数（AI 子系统边界；本轮仅加了 `getSelectedLayer` 只读引用作 +affix 上下文）。
- 视野-数据-结论同步性 / KDE cascade-exclude / 4×5 归因聚合 / 对称拉伸 / tip-popup 统一悬停 / 设计语言一致性——均未受影响（纯容器迁移 + 新增 EMC 内部交互）。
- EMC 主题 = **浅色**（与主界面一致，用户已定；勿改深色）。
- 智能高度：拖拽中(`body.dragging`)/流式中(`_streaming`)不自动调档，防打架。

### 本轮改的文件（下会话续改 EMC 看这些）
- [frontend/index.html](frontend/index.html)（结构：#lp-upper/.gutter-emc/#emc-panel + 输入区 + 历史视图 markup）
- [frontend/css/layout.css](frontend/css/layout.css)（#lp-upper/.gutter.gutter-emc/#emc-panel + --left-w/--emc-h）
- [frontend/css/ai_qa.css](frontend/css/ai_qa.css)（退 fixed / 历史视图 / 输入区 / textarea 加高 / toolcard / Thinking 头 / 复制 / code-block）
- [frontend/js/sidebar.js](frontend/js/sidebar.js)（initVDrag 纵向拖拽 + 基线 + resize）
- [frontend/js/ai_qa/panel.js](frontend/js/ai_qa/panel.js)（容器重命名 / 历史就地视图 / 智能高度 setEmcMode+observer / renderToolCard / Thinking 头 / 复制 / Esc / code-block / +affix）
- [design/tokens.json](design/tokens.json) + 重跑生成器（左栏宽 token）

### 承重 memory 索引
- 本轮相关：`emotion-map-logic-chain`（演示逻辑链）/ `view-data-conclusion-sync` / `design-language-consistency-iron-rule`（改一处先 grep 同类）/ `stand-on-giants-shoulders`（Claude Code 交互语言复刻，非造轮子）/ `maintain-revision-log` + `todo-revision-log-sync` / `no-routine-playwright-verify`（本轮控制流风险大，例外跑了 Playwright 自检）/ `chinese-all-deliverables` / `frontend-default-light-theme`（EMC 走浅色）/ `session-handoff`（本卡协议）/ `no-handoff-on-routine-commit`（平时只更 revision-log，说"交接"才覆写本卡）
- AI 问答既有基座：意图路由 + 工具链 $n + 产物 gate + 多会话 + 操作按钮 + 诚实铁律（见 revision-log 5.42–5.47）

## 新会话 prompt（复制即用）
见下方代码块。
