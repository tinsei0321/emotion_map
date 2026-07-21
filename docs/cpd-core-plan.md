# CPD 核心引导逻辑（EMC 主控编排）实施计划

> 状态：**初稿 v0.1**（2026-07-22 凌晨）· 多轮第三方大模型评价中 → 见 [cpd-core-plan-review.md](cpd-core-plan-review.md)
> 分支 `cpd` | 承重：调用次数优先 / 不派 subagent / 只 commit 不 push（本次收工例外 push）/ 不合分支不抽离
> 范围校正：CPD 至今所成 = 地基（浮窗 + 软折叠壳 + curState 反映 + 色带/主题/三级权重 + 自适应位置）。**本计划 = CPD 核心**：curState 从「反映」升「编排」，EMC 每阶段主动奉上「此刻唯一动作」。

---

## 一、Context（为什么做）

当前 CPD 地基完工，但 EMC 仍是**被动**的：curState 只"反映"状态（染进度点），用户得自己在左栏抽屉/dock 找 import/range/toolbox 按钮。这与 design-system §4「此时此刻需要什么 = 出现对应提示」「EMC 按任务进度奉上恰好那一个动作」的核心理念差距大——所有功能仍是"裸按钮"，EMC 没有真正"调度底层"。

本计划新增一个**确定性的引导引擎**，把 curState 升级为编排信号：每个状态算出"此刻唯一动作"，通过已就绪的 `.has-guidance` 光环钩子 + 折叠态文案自适应 + 展开态 CTA banner + 底层控件聚焦，主动引导用户完成 import→range→layers→analyze→结论→导出 全链路。**对话/分析路径（harness）原样不动**，只加一个客户端事件作为"结论回灌"接缝。

---

## 二、核心设计决策（先定调，再展开）

### 决策 1：引导 = 纯客户端确定性引擎，不进 LLM
"编排"**不**靠 EMC 发对话消息、**不**改 diagnose/harness。新增 `cpd-guide.js`，用纯函数 `deriveGuidance()` 从客户端信号（curState + 特征存在性 + 上轮 exit）确定性算出引导对象。理由：
- 承重铁律「diagnose prompt 永不动（保 eval）」「四态出口不动」「curState 纯客户端推导」。
- design-system §4.3 的"出现什么"（问候/图层推荐卡/诊断卡）本质是**确定性 UI 内容**（列可见层、静态问候），无需 LLM。

### 决策 2：两条路径 cleanly 分工，零耦合
- **主动引导路径（新）**：用户"还没说话"时，引导引擎推唯一动作（UI nudge，非对话消息）。
- **对话分析路径（不动）**：用户"已说话"时，走 harness（diagnose→SKILL_DEFS→TOOLS→四态出口）。
- **唯一接缝**：对话结束（结论落地）→ panel.js `send()` 末尾 dispatch `cpd:turn-ended {exit}` → 引导引擎读 exit 算下一步引导（RESULT→导出/换范围；GAP→上传；PARTIAL→补传）。复用现有 `_followUps` 的 exit→动作映射，**不另造一套**。

### 决策 3：软折叠基调不变（非严格隐身）
沿用 memory `cpd-soft-collapse`：chip/控件始终可达，引导 = **高亮 + 文案 + 光环 + CTA**，不强制隐身其他控件、不自动开抽屉（CTA 点击才开）。"奉上唯一动作"= 视觉聚焦那一个，而非锁死其余。

---

## 三、功能图谱（逐一标注编排定位）

| 功能 | 入口（文件） | 现状 | CPD 编排定位 |
|---|---|---|---|
| **import 数据** | dropzone + `openImport`(sidebar.js) + import-input | 裸按钮 | **待编排**：S0 主动作「先导入情绪数据」→ CTA 触发 import |
| **range 范围** | range tab + range-input + `runRangeImport` | 裸按钮 | **待编排**：S0/S1 主动作「框选/上载范围」→ CTA 开 range tab |
| **layers 图层** | drawer 3 tabs + `renderLayerList` + chip | 已软折叠(chip 可达) | **待编排**：S2 主动作「选一个情绪图层」→ 高亮 layers chip |
| **toolbox·KDE** | `tool-heatmap`/`openHeatmapDialog`(dock) | 裸按钮 | **半引导**：dock 裸按钮待编排；EMC `density` skill 已可对话跑 |
| **toolbox·Grid** | `tool-grid`/`openGridDialog`(dock) | 裸按钮 | **半引导**：dock 待编排；EMC `ensure_zone`/`zonal` skill 已可对话 |
| **toolbox·Buffer** | `tool-buffer`/`openBufferDialog`(dock) | 裸按钮 | **半引导**：dock 待编排；EMC `buffer` skill 已可对话 |
| **toolbox·归因** | `tool-attribution` | **待开发**(toast「开发中」) | 标记未实现；EMC `query_attribution`/`open_attribution` 部分覆盖 |
| **timeline T1-T3** | `time-bar.js`/`timeline.js`（L2·综合·标准网格焦点显） | 裸控件 | **轻编排**：S3/S4 nudge 时点切换（可选，G3） |
| **compare 批4** | `'c'` 键 POC（无正式 UI）+ EMC `compare` skill | 半裸(POC)+EMC 可对话 | EMC `compare` skill **已引导**；正式 UI 入口待补（G3，挂 time-bar） |
| **export 报告** | `_exportReport`(panel.js footer icon) | 已在 EMC 页脚 | **已引导**：S5 主动作「导出报告」→ CTA 触发 footer 导出 |
| **search 地名** | `search-bar.js` `initSearchBar`(geocode) | 裸控件 | **独立**：地名搜索非情绪分析，暂不编排（保持轻量） |
| **EMC 问答** | `orchestrate`(harness.js) | 主控 | **已是主控**，本计划不改其内部 |

**小结**：EMC 已对话引导 = KDE/Grid/Buffer/compare/归因查询/各种 geo 工具（SKILL_DEFS 全覆盖）。裸按钮 = import/range/dock 工具/timeline。本计划核心 = 给裸按钮接上确定性引导 + 用 exit 回灌闭环。

---

## 四、引导状态机（curState 反映 → 编排）

### 4.1 信号源（全客户端，复用 + 扩展）
- 复用 `cpd-state.js` 已订阅：`getLayers()`（visible 非 group）、`#chat-messages .chat-msg-user`/`.aiq-conclusion`、`layers:changed`/`layer:selected`/MutationObserver。
- **新增信号**：
  - 特征存在性：`hasImport = 有 point 层`、`hasRange = 有 isRange 层`（复用 sidebar `isRange` 判定：polygon/line 且无 `_ui.tool`）、`hasAnalysis = 有 grid/zonal 聚合层`。
  - 上轮 exit：读 `_history` 末条 assistant trace 的 `exit`（RESULT/GAP/PARTIAL/CONCEPT/ask）；`send()` 末尾 dispatch `cpd:turn-ended {exit}` 作为刷新触发。

### 4.2 状态 → 唯一动作映射（确定性）

| curState | 细分信号 | 引导 kind | 主动作文案（示例） | target（CTA 指向） |
|---|---|---|---|---|
| **S0 空** | 无 import | `import` | 「先导入情绪数据，我帮你读懂它」 | 触发 `openImport` |
| S0 | 有 import、无 range | `range` | 「框选一个分析范围（如西陵区）」 | 开 range tab（`cpd:focus-tab range`） |
| **S1 选范围** | 有 range、无可见情绪层 | `layers` | 「选一个情绪图层显示」 | 高亮 layers chip |
| **S2 载图层** | 有可见层、无对话 | `analyze` | 「问我想看什么，或直接跑分析」 | input 聚焦 / 高亮 toolbox chip |
| **S3 分析** | 对话中、无结论、非流式 | `null`（不打扰） | —（流式/思考中不推引导） | — |
| **S4 结论** | exit=`RESULT` | `export` | 「深读归因 · 导出报告 · 换范围」 | export + range |
| S4 | exit=`GAP` | `import` | 「补传所需数据，我接着分析」 | import |
| S4 | exit=`PARTIAL` | `import` | 「补传数据，补完刚才的分析」 | import |
| S4 | exit=`CONCEPT`(general) | `analyze` | 「想看真实情绪分析？试试这些」 | 转回 S2 analyze 引导 |

> S1 range-only / S5 导出为瞬态/用户触发，不自动判（与 `cpd-state.js` 现有注释一致）；S5 导出作为 S4·RESULT 的 CTA 之一呈现，不单列状态点。

### 4.3 调度接口（与 harness/工具链，零侵入）
- **不改** harness.js / stages.js / diagnose / 四态出口 / tracker。
- 引擎只**读** exit（trace），不**写** harness。
- 唯一新增事件：`cpd:turn-ended {exit}`（panel.js `send()` finally 段 dispatch）→ 引擎 `recompute()`。
- CTA 执行复用既有入口：`openImport`(sidebar.js)、`cpd:focus-tab`(sidebar.js 已监听)、`openHeatmapDialog/openBufferDialog/openGridDialog`、`_exportReport`（经 footer button click 或导出函数提取）。

---

## 五、对话 → 功能桥

### 5.1 正向（用户自然语言 → 底层功能）：**不改**
已由 harness 路由：`_quickIntent` 预判 → `diagnoseStep` 选 SKILL_DEFS 技能 → `runTemplatePath`/while-loop 调 `TOOLS[*]` → 结果自动落地图。CPD 不介入这条。CPD 只补"用户还没说话时"的主动引导（决策 2）。

### 5.2 反向（结论 → 引导下一步）：**事件接缝**
- 现有 `panel.js _followUps(t)` 已有 exit→追问胶囊映射（GAP→上传/换问法；RESULT→深读/对比/热点；PARTIAL→补完）。
- 引擎的 S4 引导与 `_followUps` **同源同表**：引擎读 exit 算"主动作"，`_followUps` 读 exit 算"追问胶囊"，二者不冲突——主动作 = 视觉聚焦的那一个，追问胶囊 = 展开态补充选项。G2 把两者合并到同一 guidance 渲染（banner 主 CTA + 次追问胶囊），避免两套并行。

---

## 六、渐进披露细则

### 6.1 每功能：何时出现 / 如何呈现 / 用完如何退场
| 功能 | 何时出现 | 如何呈现 | 用完退场 |
|---|---|---|---|
| import | S0·无 import | 折叠态光环 + 文案；展开态 banner CTA「导入数据」 | 导入成功（`showLayerManager` → layers:changed）→ 引擎重算转 range |
| range | S0·有 import 无 range | banner CTA「框选范围」→ 开 range tab | range 层加入（layers:changed）→ 转 layers |
| layers | S1·有 range 无可见层 | 高亮 layers chip + banner「选图层」 | 可见情绪层出现 → 转 analyze |
| KDE/Grid/Buffer | S2·analyze | 高亮 toolbox chip + banner「直接跑 / 问我」；点 chip 开 dock 工具弹窗 | 聚合层生成 / 对话开始 → 转 S3 |
| export | S4·RESULT | banner 主 CTA「导出报告」 | 导出后不强制转态（停在 S4，可换范围重来） |

### 6.2 折叠胶囊引导耦合（`.has-guidance`，钩子已就绪）
现状：`.has-guidance` CSS 已定义（光环飞快色交替），`_fitCollapsedText` 已实现文案自适应，`Ctrl+Shift+G` 测试 toggle（panel.js `_setupCpdBar`）。

**CPD 核心接线**（替换测试 toggle）：
1. 引擎算出 `guidance != null` **且** `_emcCollapsed == true` → `#emc-panel.classList.add('has-guidance')` + `chat-input.placeholder = guidance.text` + `_fitCollapsedText()`。
2. `guidance == null`（S3 流式中）或展开态 → `remove('has-guidance')`。
3. **engage 解除**：CTA 点击 / input 聚焦 / input 输入 / 动作完成事件 → `remove('has-guidance')`（即使引导仍在，光环停，避免持续闪烁扰眼；下一状态变化再决定是否重亮）。
4. 删除 `Ctrl+Shift+G` 测试代码（panel.js `_setupCpdBar` 内 keydown 块）。

### 6.3 展开态呈现
- 新增轻量 `.emc-guide-banner`（插在 `.emc-cpd-bar` 下、`#emc-view` 上）：一行 `guidance.text` + 主 CTA 按钮 +（S4 时）次追问胶囊（合并 `_followUps`）。
- 无对话时 banner 可与空态欢迎卡（`renderEmptyState`）融合，避免上下两块重复；有对话时 banner 置顶不挤压对话流。
- banner left 走自适应（复用 `relayoutFloats`/`positionFloatingPanels` 思路），不挡抽屉/param-panel（memory `adaptive-position-design-rule`）。

---

## 七、承重边界（不动清单）

- ✅ **diagnose prompt 永不动**（保 eval）——引导纯客户端，不进 LLM context。
- ✅ **四态出口不动**（EXIT_RESULT/GAP/PARTIAL/CONCEPT + ask）——引擎只读 exit。
- ✅ **harness.js / stages.js / tools.js TOOLS / tracker 签名 / 网格算法 / paint-inplace 不动**。
- ✅ **curState 客户端推导**（cpd-state.js `deriveState` 不改逻辑，引擎是其上层消费者）。
- ✅ **自适应位置铁律**：banner/浮层 left 随锚点动态算，不写死。
- ✅ **EMC 颜色全走 theme var**（`var(--emc-accent)` 等），严禁硬编码 hex/rgba（memory `apply-design-sense-no-bounce` §5）。
- ✅ **软折叠基调**（非严格隐身，chip 始终可达）。
- ⚠️ 批4 grid 镜像 bug / diag 日志（main 遗留）CPD 期间不动。

---

## 八、分阶段交付（MVP 先行，可独立 ship）

### Phase G1 — 引擎 MVP + 折叠态耦合（核心闭环）
- 新建 `frontend/js/ai_qa/cpd-guide.js`：`deriveGuidance()` + 信号采集（hasImport/hasRange/hasAnalysis/lastExit）+ S0/S1/S2/S4 基础映射 + `subscribe` 联动。
- panel.js `send()` finally 段 dispatch `cpd:turn-ended {exit}`；`_setupCpdBar` 删 `Ctrl+Shift+G` 测试，接真实引擎驱动 `.has-guidance` + placeholder + `_fitCollapsedText` + engage 解除。
- **交付即用户可验**：折叠态随状态亮光环 + 文案指引。
- 颜色全 theme var。

### Phase G2 — 展开态 banner + CTA 调度
- `ai_qa.css` 加 `.emc-guide-banner`；panel.js 渲染 banner（主 CTA + S4 次追问胶囊，合并 `_followUps`）。
- CTA 点击 → `cpd:guide-cta {target}` → sidebar.js 监听（复用 `cpd:focus-tab`）/ 触发 `openImport`/工具弹窗/`_exportReport`。
- banner 自适应位置（接 `relayoutFloats`）。

### Phase G3 — 全状态 + 细则 + 轻编排
- 绿色摘要条（已完成步骤折叠，design-system §4.5）：import/range 完成后折成「● 已导入 · 修改」条。
- S5 导出 gating（导出主 CTA 仅 S4·RESULT 显）。
- timeline T1-T3 / compare 正式 UI 入口的轻编排（compare 挂 time-bar 替 `'c'` 键 POC）。
- 边界 case：流式中不推引导、ask 出口处理、空 import 但有 range 等。

### Phase G4 — 抛光 + 回归
- 主题同步（Light/Dark banner 配色）、动画节奏、光环/CTA 一致性。
- Playwright 回归（控制流/数据流风险：状态转移、CTA 调度、exit 回灌）——仅此阶段上 Playwright（承重：常规改动肉眼验）。
- 每完成一 Phase：commit（不 push）+ 更 `docs/revision-log.md` §5 顶部 + 同步 `todo.md`。

---

## 九、关键文件

| 文件 | 改动 |
|---|---|
| `frontend/js/ai_qa/cpd-guide.js` | **新建**：确定性引导引擎（deriveGuidance + 信号 + 映射 + 联动） |
| `frontend/js/ai_qa/panel.js` | `send()` 加 `cpd:turn-ended`；`_setupCpdBar` 删测试接引擎；banner 渲染；CTA 绑定 |
| `frontend/js/ai_qa/cpd-state.js` | 导出 hasImport/hasRange/hasAnalysis 辅助（或引擎自采，不改 deriveState） |
| `frontend/js/sidebar.js` | 监听 `cpd:guide-cta`（复用 `cpd:focus-tab` 范式）→ 开 drawer/触发 import |
| `frontend/css/ai_qa.css` | `.emc-guide-banner` + `.has-guidance` 微调（颜色 theme var） |
| `docs/design-system.md` §4 | 补「引导引擎 = 确定性编排层」说明（与 curState 反映层区分） |

**复用（不重造）**：`deriveState/recompute/subscribe/initCpdState`(cpd-state.js)、`_fitCollapsedText/setEmcCollapsed`(panel.js)、`_followUps`(panel.js)、`cpd:focus-tab`/`openImport`(sidebar.js)、`openHeatmap/Buffer/GridDialog`、`relayoutFloats`(cpd-state.js)、`.has-guidance` CSS。

---

## 十、验证

1. **启动**：`py frontend/serve.py 8080`（serve 自起后端 + no-cache 注入），浏览器开。
2. **G1 肉眼**：清空 localStorage → 折叠 EMC → 应亮光环 + placeholder = 「先导入情绪数据」；导入点层 → 文案变「框选范围」；上载 range → 「选图层」；问一个问题出结论 → 文案变「导出报告/换范围」。
3. **G2 肉眼**：展开 EMC → banner 显对应 CTA；点 CTA → 正确开 drawer tab / import / 工具弹窗 / 导出。
4. **承重回归**：diagnose/四态出口未变 → 跑一条 emotion_analysis + 一条 GAP 问，确认出口徽章/卡与改前一致。
5. **G4 Playwright**：状态转移链 + CTA 调度 + exit 回灌（控制流风险）。
6. 常规前端改动交付后由用户肉眼验（memory `no-routine-playwright-verify`）。

---

## 十一、开放问题（待多轮评价收敛 · 见 review 日志）

1. **引导呈现 = UI nudge（非对话消息）**：据 design-system §4.3 定 UI banner/光环/CTA，不发 chat 消息。→ 待第三方评价是否认同"不发对话消息"这一克制。
2. **MVP 先行 vs 全量**：G1→G4 分阶段，G1 可独立 ship。→ 待第三方评价分阶段合理性。
3. **S4·ask 出口的引导**：用户点选项胶囊续作时，引导引擎应否介入（当前 S3 不打扰，ask 归 S3？）。
4. **timeline/compare/search 编排深度**：当前轻编排/不编排。→ 待第三方评价是否漏。
5. **banner 与空态欢迎卡融合 vs 并存**的视觉处理。
