# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。

---

## 📅 2026-07-27（分支 `main`（合并 toolbox 后）· toolbox 验收 + EMC 大收敛 + 专题 D + E2 + E3 + E1 + Layer Manifest + 指代标注 + 优化工程+全字段值域识别 + KDE 去3D）

### 🔄 遗留：明早办公室大讨论 + KDE 去 3D 连带设计问题（用户主持·议题本会话未告知）

- **明早办公室大讨论**：用户主持·议题本会话未告知（用户已澄清 ≠ 下方 KDE 连带问题）·等用户开题再 brainstorming。
- **KDE 去 3D 连带设计问题**（本次改动撬动·备查·非大讨论主题）：
  - 「情绪地形」命名：去 3D 后"地形"语义失真·是否改名（综合热度/情绪密度）？
  - 「总体情况」栏仅剩 1 卡（情绪地形）·是否补总体分析或并入类型细分？
  - EMC `generateTerrainForAI` 仍 3D（density mode='terrain'）·与 Toolbox 去 3D 口径分裂·是否同步去？
  - 3D 能力收口：Grid 仍有 3D 地形（[index.html:723](frontend/index.html#L723)）·是否统一 3D 收口到 Grid？
- **按钮文案**：现「生成 2D 热力图」（带空格·与兄弟按钮排版一致）·用户原话「生成2D热力图」·待定。
- **浏览器验证 5.225**：KDE 情绪地形 → 单按钮「生成 2D 热力图」→ 2D 综合彩虹热力图（L1/L2 一致）。
- **浏览器验证 5.224**：EMC 折叠胶囊点击正常展开。

### ✅ CB-07 finalStep 超时矛盾 + 2D/3D 跳组修复（revision-log 5.230）

- bug1：finalStep 超时"[请求失败]"矛盾→Layer 3 try/catch + `_composeDegradedConclusion`（零 LLM 降级结论·图+{{show}} 按钮·非"请求失败"）+ Layer 2 answer phase 60s。
- bug2：2D/3D 跳组→[map.js:362/395](frontend/js/map.js#L362) addLayer 补 `parentId: l.parentId`（配对层留 EMC 组）。
- Layer 1 评估后不做（answer 质量风险·Layer 2+3 已治矛盾·P1 留）。详见 [cb-journal CB-07](docs/catch-ball/cb-journal.md)。

### ✅ CB-06 EMC ReAct 超时根治·while-loop 7 策略（revision-log 5.229）

- 用户报"思考阶段已出图但卡检索·超时请求失败·丢图"。第三方 DeepSeek 评估（[SCAN_EMCReAct](docs/catch-ball/report/SCAN_EMCReAct_deepseek_2026-07-27.md)），反评价全 agree。
- **防（DeepSeek）**：L0 density triggers 补"网格/方格"→"方格网"走 runTemplatePath（避 while-loop）+ L1 生成类缩轮 + L2 工具完成信号 + L3 prompt 条件化（首 query/数据驱动/最少轮次/勿追加查询）。
- **兜（我补）**：P0-A agentStep try/catch·throw 降级 finalStep（不"请求失败"丢图）+ P0-B streamChat 45s timeout。P1-C 早终止。
- 详见 [cb-journal CB-06](docs/catch-ball/cb-journal.md)。

### ✅ 数据识别 visible bug 修 + emc-fix-progress 汇总卡（revision-log 5.228）

- **bug**：上传 L2 点层眼睛关·EMC 判缺数据（pickVisiblePointLayer/buildContext 三处 visible 过滤·眼睛关=显示控制非数据可用性）。
- **修**：三处去 visible（已加载即用·含 hidden·buildContext 标"隐藏"·pool 优先 visible fallback all）+ _ERR/纪律文案改。
- **emc-fix-progress.md**：总进度汇总卡（五层·一页看清·详 [emc-fix-progress.md](docs/emc-fix-progress.md)）·backlog 更名归档 `.archived`。

### ✅ CB-05 EMC UX 优化·去审查 + 删除符号根治（revision-log 5.227）

- 用户报两体验问题：审查等待 + 删除符号。第三方 DeepSeek UX 评估（[SCAN_EMCUX](docs/catch-ball/report/SCAN_EMCUX_deepseek_2026-07-27.md)），反评价全 agree。
- **去审查**：REVIEW_ENABLED 默认 false + FINAL_TEMPLATE 自查清单 + 空答案检测 + runTemplatePath onObservation + panel 清审查 UI。
- **删除符号四层**：strip ~~ + REVISE 补禁~~ + getValidRefNames 扩展（治 CSS invalid 主因·DeepSeek 发现）+ invalid 视觉弱化。
- 详见 [cb-journal CB-05](docs/catch-ball/cb-journal.md)。

### ✅ L1+L2+L3 density/polarity 契约整改全完成（CB-04 · pytest 191 passed 零回归）

- **根因**（CB-04 全审 14 `generate*ForAI`）：density 参数契约四处分裂（[prompts:85](ai_qa/prompts.py#L85)/[paradigm:289](ai_qa/paradigm.py#L289)/TEMPLATE_REGISTRY/SKILL_DEFS）+ [generateHeatmapForAI:819](frontend/js/heatmap-tool.js#L819) 硬编码 rainbow + [_PARAM_ALIAS:12](frontend/js/ai_qa/stages.js#L12) 误伤 density + rank by 无效。
- **L1-a** density 双维度（analysis 色板 + polarity 筛选）：generateHeatmapForAI 复用 computeStyle + tools.js 补 polarity→analysis + `_normalizePolarity`。
- **L1-b** normalizeParams 按工具区分别名（治 _PARAM_ALIAS 误伤）+ density 别名收编。
- **L1-c** paradigm+prompts density 补 analysis/polarity + few-shot + buildContext hint。
- **L1-d** rank by 默认 worst。**L1-e** compare_regions 入 prompt。
- **L2 ✅** 新建 [tool_contracts.py](ai_qa/tool_contracts.py)（16 工具单一真相源·density 首例完整 panel_source）+ [validate_skill_params.py](tests/validate_skill_params.py)（守护 contracts<->paradigm<->SKILL_DEFS·4 PASS）。**L3 ✅** panel_missing 清单 28 项（density 完整·其余待开发者核查·务实版避 eval 红线·不派生）。
- **最高纪律**（用户指示）：EMC 分析图严格复用 Toolbox 参数面板已有色板/参数·ForAI=dialog 镜像·缺失提醒开发者补。

### ✅ CB-04 第三方 SCAN 全审 EMC 架构 + density/polarity 契约整改 plan 定稿（revision-log 5.226）

- 第三方 DeepSeek 全审 14 `generate*ForAI` 入口（[SCAN_EMCArch](docs/catch-ball/report/SCAN_EMCArch_deepseek_2026-07-27.md)）：系统性参数契约不完整（H1/H2/R1 P0 + P1a-f）。
- 反评价 **13 agree / 0 disagree / 1 partial**（R1/P1b verify-before-accept 核实·补漏 2 真 bug·无 decline）。详见 [cb-journal CB-04](docs/catch-ball/cb-journal.md)。

### ✅ KDE「情绪地形」去 3D · 统一 2D 综合彩虹热力图（revision-log 5.225，commit d6b7d2c · **已 push**）

- 用户要「总体情况·情绪地形」去 3D·确认键改名「生成 2D 热力图」·结果 2D 综合彩虹。
- 单文件 [heatmap-tool.js](frontend/js/heatmap-tool.js)：terrain 恒出 rainbow 2D + 删 3D 分支 + 删死码 generateTerrain() + 极性锁综合 + 标签/描述去 3D。
- **未动**：Grid 3D（[index.html:723](frontend/index.html#L723)）+ EMC `generateTerrainForAI`（见遗留）。
- node --check .mjs 语法过·浏览器视觉验留用户。

### ✅ EMC Bug5 折叠胶囊无法展开（revision-log 5.224，commit 0f8761b/38b64ed · **已 push**）

- 上轮代码 commit 未 sync·本次补记。Bug5：EMC 折叠胶囊点不展开。
- 5.224（0f8761b）`_runGuidanceCta` 先展开；5.224b（38b64ed）真根因——移除 `cpd:focus-tab` 切走（点 EMC 胶囊留 EMC）。
- 浏览器验留用户。

### ✅ EMC Flash 全字段值域识别 + EMC 组 + L2 消极（revision-log 5.223，commit b5b3981 · **待用户 push**）

- 全字段值域摘要（buildContext·categorical/数值/时间·Flash 知有什么/缺什么）—— Layer Manifest 完整版。
- 能力 hint（极性筛选·勿判缺）。EMC 组（ensure_zone _adoptToolboxResult）。filterFc polarity 筛（消极≠综合）。
- 不动 diagnose/schema/orchestrate。
- **留用户**：浏览器验 grounding 全字段值域 + EMC 组 + L2 消极热力图。

### ✅ EMC Bug3 删除符号 + Bug1 density 视角（revision-log 5.222，commit 44df49f/dd559cc · **待用户 push**）

- Bug3 删除符号：streamChat 过滤控制符（DEL 等）+ FINAL_TEMPLATE 禁 markdown ~~。需用户确认具体。
- Bug1 density 视角默认：_mode 读地图 pitch（2D→2d/3D→3d·非硬 2d）。
- Bug1 其余（消失/2D-3D 切换）：5 机制交织·标 Playwright 实测 + 多轮。
- Bug2（review 慢）已有降级·异步后续。Bug4（交互胶囊）列后续·讨论。
- **留用户**：结论删除符号确认 + density 视角验 + Bug1 其余实测。

### ✅ EMC Layers 数=0根治 + 能力 hint（revision-log 5.221，commit 8348624 · **待用户 push**）

- Bug 1 根治：_adoptToolboxResult 补 parentId 后 push group.children（getChildren 用此·addLayer 无 parentId 未 push 致数=0）。
- 能力 hint（系统覆盖）：buildContext 加全 EMC geo 工具能力（15+）→ Flash 知能生成不判缺。
- 系统 check（非报一个修一个）：一次性排查所有工具认知缺口。
- 不动 diagnose/schema/orchestrate。
- **留用户**：浏览器验 density/grid → 组卡数正确 + 「400m 方格网」不判缺。

### ✅ EMC density 红色修 + 中文化（revision-log 5.220，commit 689abf6 · **待用户 push**）

- Bug 2 density 红色大面积：intensity 1→0.6 + radius 300→200 + rainbow stops 红段 0.85→0.92（红只最高·低密度可见）。
- 中文化：_liveRecTip 英文→中文（密度热力图/分区统计...）+ FINAL_TEMPLATE 加⑤禁英文 GIS 术语。
- Bug 1（Layers）：根因误判（addLayer push group.children）·待 Playwright 实测（visible/gfold/css）。
- **留用户**：浏览器验 density 红色 + 中文化 + Bug 1（实测给场景）。

### ✅ EMC chip tip 标签对齐 + 衔接确认 + 自成长 P2（revision-log 5.219，commit b5e0675 · **待用户 push**）

- chip tip bug：_liveRecTip 标签（'密度'）≠ _liveRecognize（'热力图'）→ tip 空。修 tags.includes 实际标签（8 类）·实时生效。
- 衔接确认：路径 1（优化键→diagnose）+ 路径 2（diagnose 内部 prompt 工程）都通·已实现。
- 自成长 P2：运行时不自动学·开发层手动·自动学（golden/RAG/反馈）需用户量·P2 后续。
- **留用户**：浏览器验 chip 两行 tip 实时 + 优化→diagnose 衔接。

### ✅ EMC prompt 优化方向修正 + chip 两行 tip + 减 token（revision-log 5.218，commit bdf4d3a · **待用户 push**）

- 用户校准（推翻前几轮）：prompt 优化=精准化扩充+逻辑梳理（非改写/条目化/启发）·用户提问语气·启发是 chip/CPD 职能。
- OPTIMIZE_TEMPLATE 重写（精准化+用户语气+few-shot 理想例·~150 token）+ buildOptimizeContext 极简（层名·~200 token）→ Flash <2s。
- chip 两行（[_renderRecognize](frontend/js/ai_qa/panel.js)+[_liveRecTip](frontend/js/ai_qa/panel.js)）：第一行短语 + 第二行方法 tip（density/zonal/rank...）。
- 不动 diagnose/schema/orchestrate。
- **留用户**：浏览器验精准化（层名+极性）+ 用户语气 + <2s + chip 两行 tip。

### ✅ EMC prompt 优化工程系统化（revision-log 5.217，commit 2bcc08c/65add16/b491c23 · **待用户 push**）

- bug JSON 根治：OPTIMIZE_TEMPLATE 弱约束 → Flash 出 JSON。修 meta-prompt 强化（禁 JSON + few-shot 用户理想例）+ _parseOptimize 拦 JSON + onOptimize 流式拦截。
- 简洁条目化风格：分号短句 + 去修饰 + 关键词（用户精确 spec + few-shot）。
- 超时 <3s：buildOptimizeContext（精简·层名+kind+字段role·~500 token）替换 buildContext。
- feature：Layers 数据消费（关联层名）+ 智能场景（守不增维度）。
- 客观评估：大工程·meta-prompt 多轮迭代（3-5 轮·反馈驱动）。
- **留用户**：浏览器验 bug 不复现 + 简洁条目化 + <3s + 不增维度。

### ✅ EMC 优化键四修（revision-log 5.216，commit fd077e0 · **待用户 push**）

- bug 缺数据代码块：_esc 加反引号转义（composeGapCard 动态值含 ` 致 marked 代码块）。
- 优化键位置：margin-left:auto + margin-right:2px（发送键左 2px 间隔）。
- 撤销 icon：Lucide undo（左上箭头+弧·换旧丑回箭头）。
- chip 发散：_liveRecognize 升级（区名→子地点/密度→热力图名词/多地点→对比·最多 6 chip·启发）。
- chip 发散 vs 优化不增维度（语境不同·并存）。

### ✅ EMC LLM prompt 优化键（revision-log 5.215，commit 30237cb · **待用户 push**）

- 用户校准：prompt 工程=梳理已有要素（非改写/非增维度）·业界 LLM（5.214 代码差）·启发=需求更清晰。
- [build_optimize_prompt](ai_qa/prompts.py) meta-prompt（Flash 流式·不增维度·只梳理已有·自然语言）+ router phase optimize + stages optimizeStep。
- _toggleOptimize LLM 三态（sparkle⇄loading[spinner+placeholder"prompt优化中..."]⇄undo 撤销）。
- 恢复 5.213 输入提示 chip（对话框下·代码预览·与优化键并存）。删 5.214 代码版。
- 不动 diagnose/schema/orchestrate。<3s（Flash+精简+流式）。
- **留用户**：浏览器验输入模糊→优化→梳理已有（不增维度）→启发→撤销。

### ✅ EMC 一键优化 prompt 键（revision-log 5.214，commit d6e9add · **已升级为 5.215 LLM**）

- 反转 5.213（删 chip 显示）+ 加真功能键（用户澄清"要功能键非显示"）。
- #aiq-optimize 发送键左 32×32（sparkle icon）·[_optimizePrompt](frontend/js/ai_qa/panel.js#L984) 代码改写（指代展开+口语规范+意图模板）·撤销（.is-optimized ⇄ undo icon）。
- 纯代码（毫秒级无 LLM）·非深度优化（接受改写有限）。纯前端·不动 diagnose/schema/orchestrate。
- **留用户**：浏览器肉眼验输入"这边怎么样"+选中西陵区→点优化→改写→撤销恢复。

### ✅ EMC UI 显化已识别标签（revision-log 5.213，commit 0a02412 · **已反转于 5.214**）

- 用户想法"发送键左侧加 LLM 优化键"·校准否决（重复 diagnose + 多 2-5s + 改写风险）·选 A UI 显化。
- [_liveRecognize](frontend/js/ai_qa/panel.js#L947)（代码关键词·几 ms·非 LLM）→ 区名/意图/尺度 chip·输入时实时显。
- sparkle 圆角正方图标 32×32（同 chat-send·Light token + Dark EMC 覆盖）+ chip（填充胶囊·设计语言统一）。
- 定位：预览（代码大概）·diagnose 精确卡不重复。纯前端·不动 diagnose/schema/orchestrate。
- **留用户**：浏览器肉眼验输入"西陵区情绪归因"→显 chip。

### ✅ EMC grounding 指代标注（revision-log 5.212，commit e3c4266 · **待用户 push**）

- 用户认知校准：EMC NL→计划 = diagnose Flash 一步（2-5s·计划阶段唯一 LLM）；prompt 工程已重度内嵌 build_diagnose_prompt（MANIFESTO+8 附录+few-shot+grounding）；加独立 NL→prompt 层价值边际（LLM 已理解 NL）。
- resolveCoref（[tools.js:233](frontend/js/ai_qa/tools.js#L233)·几 ms·非 LLM）：检测指代词（这边/这个区/这里/刚才/上次）→ activeAnalysis/selectedLayer（这边）+ priorTurn.done（刚才）→ grounding 显式标注。
- orchestrate diagnose 前注入 ctx.context（[:449](frontend/js/ai_qa/harness.js#L449)）。保守（不标误·不改写 NL）。不动 diagnose prompt/schema/主循环。
- **留用户**：飞轮验选中西陵区+问"这边情绪"→diagnose 知指代。

### ✅ EMC Layer Manifest 最小版（revision-log 5.211，commit 80d09c4 · **待用户 push**）

- backlog ④「字段识别分散」已被 getFieldCard 缓存（5.200-5.205）解决·本轮补两小缺口。
- ① getFieldCard Promise 缓存（[:99](frontend/js/ai_qa/tools.js#L99)·并发首次不重复 LLM）② layers:changed 监听预计算（fire-and-forget·新层导入即算·首次 diagnose 命中缓存·治首字延迟）。
- tools.js 单文件·不动 import.js/diagnose/schema/orchestrate。结构化 manifest + 消费统一（backlog ④ 完整版）标 YAGNI。
- **留用户**：飞轮验首次 diagnose 首字更快 + 并发不重复 LLM。

### ✅ EMC 专题 E1 · 多步链 runChainPath（revision-log 5.210，commit f5b4078/3f31c15/3dbfcdf · **待用户 push**）

- 治 C3 多步超时：template=multi 标准链走 runChainPath（0 中间 LLM 轮·确定性）非 while-loop ReAct。
- 3 step：① CHAIN_REGISTRY（[stages.js](frontend/js/ai_qa/stages.js) 纯前端·extract_overlay/clip_density·chain_id harness 派生非 Flash）② runChainPath（[harness.js](frontend/js/ai_qa/harness.js) 类比 runTemplatePath·复用 $n/_stepResults）③ orchestrate :537 multi 分流（最小 if + _deriveChainId）。
- 红线：前端为主·不改后端 paradigm/prompts/schema；orchestrate 最小 if 不动 single/while-loop/出口裁定。
- 验证：eval 31/37=84%（multi 命中）+ 三步 .mjs 语法过；chain 执行留用户飞轮。
- 风险：覆盖面窄（仅标准链）+ triggers 误匹配（保守起步）。

### ✅ EMC 专题 E3 · partial 出口消费 _renderState（revision-log 5.209，commit 32924b9 · **待用户 push**）

- 治假完成制度化：[_verifyClaims:225](frontend/js/ai_qa/harness.js#L225) + orchestrate [:690](frontend/js/ai_qa/harness.js#L690) 两处 actual 过滤加 `_renderState`（渲染失败层不计"实际产出"→声称的若渲染失败=missing→EXIT_PARTIAL）。
- 信号源：[map.js:461](frontend/js/map.js#L461) _renderState=failed/ok + [shared.js:176](frontend/js/toolbox/shared.js#L176) addToolboxLayer 检测。
- 纯对账真值源增强·不动主循环/分流/出口裁定条件/prompt/schema。composePartialCard"未生成"语境涵盖渲染失败。
- **留用户**：飞轮渲染失败用例（如 density bbox 越界）→ 验 partial 标注。

### ✅ EMC 专题 E2 · 进度透明（revision-log 5.208，commit 4e15134 · **待用户 push**）

- 治 C9 延迟感知：[setPhase](frontend/js/ai_qa/panel.js#L903) 加时间戳+done（已完成段填充）+ 阶段计时（"检索 8s·共 12s"·0.5s 刷新）+ onAction "正在执行·[工具CN]"（[_TOOL_CN](frontend/js/ai_qa/panel.js#L925) 映射）+ onObservation "已生成 N 层"（layer delta）+ 可见取消按钮（复用 _abortCtl·Esc/Ctrl-C 保留）。
- 纯前端（panel.js + ai_qa.css）**零承重**·复用 hooks 时序不加 onProgress·不动 orchestrate/router/schema/prompt/SKILL_DEFS。
- 设计语言：填充式无线框 + 胶囊紧凑 + 离散分段（memory avoid-frames/capsule/ramp）。
- **留用户**：start.bat 肉眼验进度条/计时/增量落图/取消。

### ✅ EMC 专题 D · diagnose 认知深化（revision-log 5.207，commit ded4696/c074b75/02ec4ba/64244c8 · **待用户 push**）

- **D1 SOP 卡扩字段**（[paradigm.py](ai_qa/paradigm.py)·eval-first）：GEO_TOOL_CATALOG 12 工具 +scale/preconditions/failure_modes（歧义工具 +examples 正负例）。failure_modes 给 Flash 反向判据（clip 只切点/单一关系勿 multi/hotspot vs density/area_stats 非情绪）。eval 3 跑：基线 91% → 扩字段 89% → 微调 **91% 不退化**（公园点位/各区排序/离地铁 deterministic 改善）。残余 MISS = LLM 方差 + 商业用地 select_template triggers 张力（B_TRACK"区内的"→clip 过宽·另案）。
- **D2 method 确定性派生**（[harness.js](frontend/js/ai_qa/harness.js)）：`deriveDiagnoseMethod` Flash 未输出时按 template 派生（single→[tool()]），解锁 F3 gate/formatDiagnoseSummary/_needsDeliberate 悬挂读取。不动 diagnose prompt/schema/orchestrate。
- **D3 EMC-SUM 计划→实产**（e2e-seam/test-cases/test-board）：chatPhases +method → ②`计划N→实产M层` + EMC-SUM 头`计划命中` + 报表 method 字段。闭合 test-board:26 TODO。method 留前端 trace 不改 schema。
- **红线守约**：D1 不动 DIAGNOSE_TEMPLATE 本体（附录数据）；D2/D3 不动 ChatRequest schema + orchestrate 主循环。test_a3+emc_template 19 pass + 三前端 .mjs 语法过。
- **留用户**：?test=1 飞轮验 计划→实产 + method 渲染。

### ✅ toolbox 验收 + EMC 大收敛批次（revision-log 5.206，commit 547a334/3d1e12b/1fb9dfb/62f25e7 · **用户手动 push**）

- **toolbox 验收**（[报告](.codebuddy/reports/toolbox-unified-acceptance-2026-07-26.md)）：建议合并·三件套本机复现全绿（obs 0/12 + unified + pipeline ALL-PASS）+ 4 裁决（M6 接受 K3 color 修正·评审 distance 失误自认）。
- **全盘点 18 项**（不遗漏·emc-fix-backlog + K3 §9 + 验收 §四 + plan 步 1-6 交叉去重）。
- **步1** _contentSig 统一（547a334）/ **步2** T3 参数序列化 + T6 hasAction 灭绝空心 OK（3d1e12b）。
- **批次A** T4 胶囊矛盾（strat 缺省 unknown）+ T5 对比入口收敛（无焦点提示）（1fb9dfb）。
- **批次C** D1 扩覆盖（harness :462·治 s1 残余·eval 89% 不退化）（62f25e7）。
- **批次B** CPD predicates failing（pre-existing 嫌疑·K3 §7-7 称未跑·登记另案）。
- **推迟**：A3 $n 链 diff / ensure_zone registry / Layer Manifest / P2。
- **专题 D/E 计划就绪**（diagnose SOP / harness D3+P0-4+P1-4·红线 eval-first·后续会话）。
- **留用户**：T7 飞轮 + manifest 再生成 + DATA 迁移 commit。分支 19 commits 待合并（暂不合并）。

## 📅 2026-07-25（分支 `main` · EMC density 治本 3 包执行）

### ✅ EMC density 治本 3 包执行（revision-log 5.205，commit d8dbcb2 · **用户手动 push**）

- **K3 合成报告根因**（[emc-eval-synthesis-2026-07-25](.codebuddy/reports/emc-eval-synthesis-2026-07-25.md)）："相位差→**错位**"——修复队列（系统健康序）vs 演示链（用户可见序）5.200-5.203 交集空·改对病没改疼。主因 C5+C6 缺口 + 验证债务；架构/红线无罪。
- **主线程核验 K3**：三承重判断属实（time-source manifest 404 首报 / C5 机制二分 / C6"密集"0 触发词）+ 补两漏（addHotpointLayer 同病 / buildWeight 0.3 非 0.24）。
- **包A C5 渲染**（map.js·非红线）：resolveWeightField（emotion_intensity→score→uniform 兜底）+ 同步 addHotpointLayer + renderLayer addSource 容错 + _renderState。
- **包C 低耦合小项**：C 分组（density 委托补 parentId·组卡非空·用户#2）/ C7（夷陵描述改正）/ B srcId（_toolContentSig + 按 srcId 去重·闭合用户#3）/ T9（例间清层）/ time-source（路径同源）。
- **包B C6 认知**（paradigm.py·**eval-first 红线**）：density 触发词加密集/集聚/热力图 + yields 改委托实况；eval 扩 2 例双命中，**25/28=89% PASS** 不退化。
- **承重纪律**：C6 触 diagnose prompt → eval-first；harness/ChatRequest 未触。
- **留用户验证**：T7 飞轮全量重跑 04-07（?test=1·偿验证债务）+ C5 density 彩虹图肉眼验。**红线未决**：DATA 迁移未 commit（数据红线）/ manifest 再生成留用户 / R1 残余 s1 4/9（T7 后定夺扩 D1）。

## 📅 2026-07-24（分支 `main` · 测试飞轮机制评估）

### 🔄 收工·06/07 评估 + density 治本 plan 定稿（待下会话执行）（revision-log 5.204，本次 push）

- **06/07 评估**：06 工具 pass=0% / 07 意图 pass=33%（3 OK 全空心·有效≈0%）·**EMC 本体核心未动**（K3 "相位差"：测量 4 批真进展·本体 C2/C3/C5/C6/C8 未修）。
- **3 Explore agent + K3**（`.codebuddy/reports/emc-eval-report06-07-2026-07-24.md`·C1-C9 簇）根因收敛：C5 渲染（weight 透明）/ C6 工具认知（"密集"缺触发词 + density 僵尸文案 + Toolbox 缺席 catalog）/ C 分组（categoryOf 不用 parentId）/ B srcId 工具层 / T9 清层 / C7 夷陵资产（无夷陵·EMC 判缺对）。
- **density 治本 plan 已存** `~/.claude/plans/emc-gis-rippling-dream.md`（6 步·下会话执行·C5 最大见效→C6 eval-first→C 分组→B srcId→T9/C7）。
- 交接卡 [session-handoff.md](../memories/repo/session-handoff.md) 已更。**DATA 迁移留用户处理（数据红线·未 commit）**。本次 push 30 commit。

### ✅ EMC 05-llm 修复 T1 + UI 固定图钉 + EMC 排版/文风（revision-log 5.203，commit 6f880a7/9fe6521/bc62e72/284ae94 · **用户手动 push**）

- **自评+K3 对账**：05-llm Q1-Q4 全命中（Q1 seam 洗坏+错池 / Q2 胶囊矛盾 / Q3 对比 POC 退化 / Q4 信号-only 断言）。**补 K3**：T1 不只 washing，pool（processed→performance）+ 文件名（xiling_wujia→yichang）也错。
- **T1 修 seam**（6f880a7·关键·解锁极性评估）：三修（pool+文件名+dsvRows/五档）→ 真数据 16933 行·5 档充足（Very Neg 6610/Very Pos 4716/Neutral 3810/Neg 1203/Pos 594·非 ~89% Neutral）。**05/04 涉极性例结论作废·待 T7 重跑**。
- **UI 固定图钉**（9fe6521）：Range/Layers/Toolbox 抽屉右上角图钉（品牌蓝亮起）·固定后点空白不隐（+param-panel 联动）·Esc/X 仍关。
- **EMC 排版**（bc62e72）：问题理解卡字体 2xs→xs/sm + 标签通俗化（软缺口·降级标注→部分数据替代）。
- **答语文风**（284ae94·红线·飞轮验）：FINAL_TEMPLATE 加「文风」指令（简短/生动具体/通俗优先/结论先）·不碰承重规则。
- **路线**（[emc-fix-backlog](emc-fix-backlog.md)）：T4/T5/T6/T3/D3 pending·T7 待用户重跑。**下一步**：D3 链式方法库治 R2 真超时，或 T4/T5（你报的可见 bug）。

### ✅ EMC R1 数据认知治假 GAP（D2+D4+D1）（revision-log 5.202，commit f1ee84a/83b073b/f77129b/37568f8 · **用户手动 push**）

- **根因（K3 深化）**：R1 双缺口——strategy 语义缺口（prompts.py:210-211 缺"超集可派生"类）+ 可见性缺口（grounding 不枚举 boundary 子要素名）。工具层已能解析中文区名，**认知层没告诉模型"西陵区可用"**。
- **Step1** eval 扩区片例冻结（D2 gate·f1ee84a）；**D2** prompt 补"可派生→ready"（83b073b）；**D4** grounding 枚举 boundary 全量名（f77129b）；**D1** `deriveAvailable` post-diagnose 强制 ready 挡假 GAP（37568f8）。
- **承重纪律**：D2 触 diagnose prompt → eval-first；D4/D1 非红线。
- **验证**：eval PASS 25/27=93%；**待用户跑飞轮** INT-002~007 验不再假 GAP。**下一步**：D3 链式方法库治 R2 多步超时（INT-008~017）。

### ✅ EMC 治本 B0 护承重 + B1 模型路由（治超时#1）（revision-log 5.201，commit 9fd8dc4/a93ce67/a96bfea/d2cd5be/78395c6/1e49182 · **用户手动 push**）

- **K3 深度消化**：智能倒挂 + 五脱节；本批攻 ③延迟架构错位（深度研究串行管道 vs 交互工具秒级期望）。
- **B0 护承重**：eval 加 compare+负例 → **冻结基线 83%**（a93ce67）；词表 single-source（`template_id_list_text` 从 TEMPLATE_REGISTRY 派生）→ 重跑 **91% 无退化**（a96bfea）。
- **B1 路由+预算**（治超时#1·三刀合击）：**2a** final/revise→flash（复杂升 pro·d2cd5be）/ **2b** 松 gate 0.8→0.6（fast path 默认·78395c6）/ **2c** while-loop 75s 预算守卫（保必有回答·1e49182）。
- **承重纪律**：B0 先冻结 eval 再改 prompt（红线 eval-first）；B1 三子步按风险升序独立 commit。
- **验证**：eval PASS；**待用户跑飞轮** density/zonal/rank 验 p95<60s + 无 90s 超时无答 + 无质量崩。
- **下一步**：P0-4 进度+取消 / B2 飞轮v5 / B3 P1 本体（GIS 工具 SOP 卡·治 4 MISS 路由歧义）。

### ✅ EMC P0 安全批·滚动复位 + srcId 去重 + density 执行信号（revision-log 5.200，commit 89d7d70/ed1d97f/4a01052 · **用户手动 push**）

- **1a 滚动复位**（[panel.js:1260](frontend/js/ai_qa/panel.js#L1260) send）：`_userPinned` 发新问即复位（治 E6 上滑后所有新回答不跟）。
- **1b srcId 去重**（[main.js:79-98](frontend/js/main.js#L79-L98) + runImport）：内容签名 srcSig（collision-free 串键·优于 hash）→ 同文件复用 / 异名同内容关联 toast / 快照打 `layer.srcId`（L001 编号零动，srcId 供 EMC grounding 稳定引用）。
- **1c density 执行信号**（harness:332 + e2e-seam + test-cases）：runTemplatePath 派发 `tool:executed` 事件 → e2e-seam 监听 → test-cases 并集 `sig.tools`（治 density 委托前端无 fetch·TOL-001 永远 tool_hit=0）。
- **承重零触**（diagnose prompt / harness orchestrate / ChatRequest 三承重不动）。
- **验证**：语法肉眼复核（node 不在环境）；待用户肉眼验 1a + 跑飞轮 TOL-001 验 density 入 sig.tools。
- **下一步**：模型路由(超时#1·harness 红线)独立 plan + 先扩 eval。

### ✅ 测试飞轮两批修复入库 + EMC 治本 backlog 起步（revision-log 5.199，commit a90fac1 · **用户手动 push**）

- **入库两批**（13 文件）：批1 信号链 H1(template 信号·治 C1 断链)/H3(参数断言硬化)/H5(JSON 报告)/EMC-SUM v1；批2 覆盖 A(字段识别扩容)/B(摘要中文)/C(渲染断言)。已验证 H1 生效（TOL-001 template=density 非 null）+ pytest 203 pass。
- **治本 backlog** [emc-fix-backlog.md](emc-fix-backlog.md)：6 类问题（超时/density信号/选错工具/字段manifest/渲染bug/摘要）+ 证据 + K3 P0/P1/P2 方向。
- **纠正 K3 过时认知**：diagnose 已跑 flash（stages.js:236）；超时真因 = agent 多轮 + final/revise pro 串行（非 diagnose）。
- **P0 切分（用户拍板·安全 3 项优先）**：模型路由(超时#1·harness 红线)单列独立 plan + 先扩 eval；本批先做安全 3 项——🔄 滚动复位(1a)/🔄 srcId 去重(1b)/🔄 density 执行信号(1c)。
- **承重零触**（diagnose prompt / harness orchestrate / ChatRequest 三承重不动）。

### ✅ 测试飞轮全面评估（静态审查·用户指示跳过实测）

- 产出：[test-flywheel-audit-2026-07-24.md](../.codebuddy/reports/test-flywheel-audit-2026-07-24.md)（总评 5.1/10；机制事实清单 + 三维度不足 + 业界对照 + H/M/L 优化清单 + Prompt 预设调整专章）。
- **三处闭环断裂石锤**：① template 信号断链（ChatRequest 无 diagnose 字段，schemas.py:11-22 → 意图断言 `tmplOk` 永 false，tpl=? 根因）；② 词表三处硬编码漂移（prompts.py:190 缺 compare/filter_attr vs paradigm.py:454/470 决策树 vs 飞轮 expectTmpl）；③ 投票不落盘 + 失败不回流 prompt 池（闭环断在"报告"处）。
- **覆盖假象**：参数正确性 10 例断言恒 pass（expect* 定义未接断言，test-cases.js:276-279）；全正模式零负例（八原则反模式无一落地）；时序 T1-T3 / POI 缓冲零用例。
- **优化清单**：H 级 5 项（信号接通/词表单源/断言硬化/反馈落盘/JSON 报告）+ M 级 8 项 + L 级 5 项；Prompt 专章 P1-P5（负例池/时序变体/POI 变体/词表派生/失败回流五环）。
- 留痕：实测驱动 `tests/browser/flywheel_audit.py` 已建（三路采集，未跑）；本机 Playwright chromium 待装（cdn 慢，可配镜像）。

### ✅ EMC×飞轮 系统性改进方案（四问咨询答复）

- 产出：[emc-sys-improvement-2026-07-24.md](../.codebuddy/reports/emc-sys-improvement-2026-07-24.md)——证据基线 11 条（E1-E11 挂行号）+ 四问方案 + P0/P1/P2 路线。
- **Q1 摘要格式**：EMC-SUM v1（3+1 行·键值定序）——单例记数/占比上浮批级；新增 tmpl 维度与耗时/调用列；judge 分误杀/漏判；同 schema 双渲染（测试报告+产品回答页脚）。
- **Q2 文件与交互**：① 去重根因=`addLayer` 零去重（state.js:667）→ srcId 指纹三态策略（复用/覆盖/并存）；② 字段识别→Layer Manifest 三级管线（嗅探→字典 core/field_dictionary.py→LLM 兜底按 srcId 缓存）+ 低置信确认向导；③ 滚动根因=`_userPinned` 发送新问题时**不复位**（panel.js:1535/1547）→ 新话轮强制跟随。
- **Q3 失败剖析**：超时=串行多 Pro 管道（report-01 14/15 超时石锤）→ 预算制+模型路由+进度透明；数据碎片化→Dataset Registry+预检喂 diagnose；推理链断裂→Tool SOP 卡+method→tool 确定性映射（QGIS Processing 描述符模式）；以图说话→10 工具成图范式+落图自检+回答图层芯片。
- **Q4 体系化**：LLM 网关/异步任务/Artifact Store/上下文编译器；episodes 重放 golden set；路由模式分流；红线=涉 diagnose/出口/harness 改动先扩 eval。
- 落地顺序：先审计报告第一批（H1/H3/H5），再接本方案 P0（共享"词表收编"项）。

### ⬜ 待用户拍板（评估优化项，按报告 §六路线）

- [ ] 第一批：H1 接通 template 信号（触 ChatRequest schema·需拍板）+ H3 参数断言硬化 + H5 JSON 报告
- [ ] 第二批：H4 反馈落盘+backlog + H2 词表单源 + M8 遥测连通
- [ ] 第三批：P1 负例池 + M2 批级 setup + M3 分层抽样 + M5 时序/POI
- [ ] 第四批：M7 catalog 登记 + M4 聚类 diff + L 级抛光
- [ ] 改进方案 P0 五项（滚动复位/srcId 去重/模型路由+预算/EMC-SUM v1/词表收编）——与第一批有依赖交叉，拍板时一并定序

---

## 📅 2026-07-23（分支 `main` · cpd 合并清理 + 测试飞轮 v3→v4 + _fill 修复 + todo 机制反思）

### ✅ 分支收敛（cpd → main）
cpd 分支（~60 commit：CPD 引擎 + EMC v1.4-1.6 + 测试飞轮 v1-3）fast-forward 合并进 main，历史线性；删 cpd 本地+远程 + `backup/pre-forcepush-9be02c3`（9be02c3 未合并，用户确认弃）。仓库收敛为单 `main`。

### ✅ 测试飞轮 v3（行内摘要+工具标注+固定位置报告+一键启动）（revision-log 5.196 · commit b63acca）
行内摘要（工具类显 tool 名·fetch 拦截 /geo /spatial 端点抓）/ 重跑 R 修复（批量中先停再重跑）/ 报告落盘 `tests/reports/`（serve `/_test/report`）/ `start.bat --open=both` 一键开主页+测试页。

### ✅ 测试飞轮 v4（方向纠偏 + 意图/工具各 100）（revision-log 5.197 · commit 89c6a31）
**意图识别 = NL→工作流转译**（断言 template+工具，非回答文本）；DATA 资产系统 `test-assets.js`（语义清单自动加载，不再让用户补范围）；意图 100 + 工具 100 生成器（270 总·≤2 工具≤4 步·针对性）；slider 默认 25；存报告覆盖确认；按钮状态机（停止↔重新开始）。用户重组 boundaries（presets/→顶层）一并修。

### ✅ _fill 中文占位符修复（revision-log 5.198 · commit 524305d）
根因：`_fill` 正则 `\w`=[A-Za-z0-9_] 不含中文 → `{区}`/`{要素}` 全未替换（200 例 prompt 失效·语法绿·仅输出扫描查出）；全局审查 4 文件正则仅此一处同类；修 `[^}]+`，270 例 0 残留；memory `js-regex-word-chinese-trap` 防复发。

### ✅ 测试报告入库（commit 81288aa）
`tests/reports/`（3 份报告）纳入 git 同步（换环境要用，勿 gitignore）。

### 📝 todo 机制反思（本日最大教训）
用户多次报"todo 不更新"，我乱找方向（TodoWrite 工具 → .workbuddy），**真 todo = 本文件 docs/todo.md**——我只更了 revision-log/handoff，**漏同步 todo.md** → 停在 07-22。
- 教训 1：同步须 **todo.md + revision-log 一起**（记忆 `todo-revision-log-sync` 早有，我没守）。
- 教训 2：诊断"不生效"先问用户"你看到什么内容"定位，别反复换工具瞎试。
- 清理：删 `.workbuddy/`（第三方工具 memo，与 claude code 无关）。

### ⬜ 下一步
- v4 实测：跑 LLM 例（slider 25 起）收转译断言失败 → 调 INTENT/TOOL prompt 池提 pass 率
- C grid 独立 skill（中期·前后端 paradigm 同步）/ D method 标准化（远期·需拍板·触 diagnose 输出）

---

## 📅 2026-07-22（分支 `cpd` · CPD 核心 plan **v1.0 定稿** + CB 专轨收敛 + EMC 浮窗交互）

### ✅ CB-CPD-03 双模型三轮 → v1.0 定稿（CB-CPD 专轨收敛）（revision-log 5.175 · commit bc5c5ee · **待用户 push**）

DeepSeek + K3 三轮验证 v0.4（报告 `SCAN_CPDPlan_03-{deepseek,k3}.md`）。

- DS 综合 A- 建议收尾；**K3 发现 v0.4 新引入 H1 链式缺陷**——general 短路 × `exit!==undefined` 守卫 × 严格 turnId+1 去重 → 引导永久冻结静默失败（已核实 panel.js:1161/1181 链）。
- 修 v1.0：① H1 dispatch 守卫→`settled` + 去重→单调递增 + `exit??null`；② M1 row 4 `hasAnalysis=true` 升级 `interpret`（dock→EMC 桥）；③ M2 hasVisibleEmotionLayer 谓词收紧 +判情绪性；④ L1 U8 改 `#param-panel.is-open` 同步谓词。
- **CB-CPD 专轨收敛**：三轮双模型闭环（v0.1→v1.0），核心 6 决策全自洽，演示 C+→B+，承重零触。
- **下一步**：P0 测试铺底 → P1 尺度诚实 → P2 引擎 G1-G4。

### ✅ CB-CPD-02 双模型二轮验证 → plan v0.4（revision-log 5.174 · commit a572ad8 · **待用户 push**）

DeepSeek + K3 二轮验证 cpd-core-plan.md v0.3（报告 `SCAN_CPDPlan_02-{deepseek,k3}.md`）。

- **首轮建议全执行**（DS 12/12、K3 15/15），v0.3 升 **B+**（两份一致，v0.2 B-→B+）。
- **两份独立收敛 2 高优**（高置信）：① init 循环 import → 依赖注入（panel.js→cpd-guide.js 单向）；② S4 动态变量无源（X×Y/N）→ 降级「{区域名}的归因已就绪」。
- **M1 色名脱节**（核实 tokens.css:28-29 色板无"深红"，very-negative #D85A30 深珊瑚橙）→ 文案"深红"改"深橙" + 色名从 theme var 派生铁律。
- M3 优先级文字矛盾（streaming 第一）；M2 range+result 兼带次 CTA。
- 反评价 14 条（agree 11 / partial 3 / disagree 0）→ plan v0.3→**v0.4** 11 点修订。
- **承重未动**（纯文档）。**v0.3/v0.4 可进 P0 测试铺底**；待 CB-CPD-03 验证定稿。

### ✅ CB-CPD-01 双模型首评反评价 → plan v0.3（revision-log 5.173 · commit c9eeed0 · **待用户 push**）

第三方 DeepSeek + K3 双模型首评 cpd-core-plan.md v0.2（均自读项目文件，报告 `SCAN_CPDPlan_01-{deepseek,k3}.md`）。

- **反评价 26 条**（agree 20 / partial 6 / disagree 0），**4 承重证据 grep/read 全部核实**：`.aiq-conclusion` 死信号 / exit 小写词表 / curState 进 buildContext / 光环硬编码 hex。
- **K3 三 P0 spec 错误**（plan 对"已就绪地基"事实陈述错）：死信号→`.aiq-exit-badge`；exit 大写→小写；映射 key=curState（S0/S1 不可达）→特征向量真值表。
- **DeepSeek 演示表现力最短板**（功能教程非诊断叙事）：S3 空间交互优先 + S4 地图定位 CTA 闭合交互环 + 文案叙事化。
- **plan v0.2→v0.3 九点修订** + cb-journal CB-CPD-01 四节 + review.md prompt 自包含（CB 协议/纪律/轮次/语境/必读文件/署名）+ SCAN 命名 `-{model}` + RULES 七轴（演示表现力）+ KNOWLEDGE 演示逻辑链北极星。
- **承重未动**（纯文档；review.py/前端/tests 留 P0-P2）。**待 CB-CPD-02** 验证修订落地 + 演示升维。

### 🔄 EMC 浮窗交互改进（前端·**已 commit 待 F5 验**·panel.js/index.html/ai_qa.css）

- F5 后默认折叠胶囊 + 展开欢迎卡（不记忆上轮态，430×640）+ 历史垃圾桶加大 + 一键全清。
- 内容驱动高度自适应（增量法，拉长+缩回；修 flex 撑满 scrollHeight 失真）。
- exit-badge 去线框改填充式 teal（避免线框设计原则）。
- **换环境后 F5 验**：折叠欢迎卡 / 高度自适应缩回 / exit-badge teal / 历史桶；有问题修后再处理。

### ⬜ 下一步：P0 测试铺底（plan §八 · v1.0 定稿后）

- 扩 `docs/emc-test-cases.md`（地基行为用例 4→N）+ 落 `tests/browser/`（复用 emc_helpers.py，断言挂真端点）。
- 详见 [cpd-core-plan.md](cpd-core-plan.md) v1.0 定稿声明 + roadmap（P0→P1 尺度诚实→P2 引擎 G1-G4）。

---

## 📅 2026-07-21（分支 `cpd` · CPD 系统级重构）

### 🔄 CPD — 情境式渐进披露（contextual progressive disclosure）

> EMC 升为系统底层主控、摈弃工程化操作体验、情境式渐进披露（软折叠）。分支 `cpd` 从 main 切出，完成后引导合并；main 遗留（批4 grid 镜像 bug）延后。plan：`~/.claude/plans/07-21-4-swipe-compressed-dawn.md`。单一真理源 `docs/design-system.md`。

- [✅] **Phase 0 · POI 入库**（revision-log 5.155 · 待 push）：`DATA/POI/` 3220 真实 POI 入 `core/place_layer.py`（无 SQL DB，库=place_layer 单 owner）。新增 `SCRIPT/poi_data/ingest_centralcity_poi.py`（字段映射 + 10 类→4×5 + 覆写 `amap_poi_centralcity_wgs84.json`，place_layer 零改动）。all_pois 4497。修 test_geocode 2 例（limit 30→200）。1623 边界 = 已有 `admin_district` preset（同 9 区），无需重复。
- [✅] **Phase 1 · 页面 UI 改造（revision-log 5.156 · 待 push）**：1a 工具簇横排（比例尺最左、按钮列其右、底对齐）；1b EMC 浮窗化（`position:absolute` 浮于 `#map` 左上 + 原生 `resize:both` 高帧率双向缩放 + localStorage 持久化 + 初始折叠条；`_setupEmcFloat` reparent 到 `#map`；`--emc-h` 三档自动调高退役为 no-op）。**左栏 `#left-panel` 暂留**（Range/Layers/Toolbox 仍在，`#lp-upper` flex:1 填满），Phase 2 加 CPD chip 行后再撤。**待用户 F5 肉眼验**。
- [⬜] **Phase 2 · CPD 软折叠状态机**：新增 `cpd-state.js` 客户端推导 curState（**不动 diagnose 保 eval**）+ 进度条/摘要 chip 行/主动作卡 + `buildContext` 增可选 hint。
- [⬜] **Phase 3 · 主题**：design-system 正冷/负暖五色带对齐 tokens + Light·yakushimabus（森绿 `#143a35` + 金黄）+ EMC 三级权重。
- [⬜] **Phase 4 · 附加**：CPD 抽象为可复用底层架构（CPD 完成后提示用户启动）。

---


## 📅 2026-07-25（分支 	oolbox-unified-toolset · Toolbox 统一工具集层）

### ✅ Toolbox 统一工具集层（8 步全完成·执行手册 v2.2）

- [✅] **步 1 基建**：	oolbox/shared.js（7 函数自 tools.js 逐字迁移 + addToolboxLayer 通用落图 + placeToolLayer）+ api.js geoPost；tools.js 抽取 re-export + addResultLayer 拆分（行为零回归）。
- [✅] **步 2 Buffer 合一**：kind:'cover'|'emotion' 双模式单一 _execute；emotion 中心四路（地点搜索/地图取点/图层要素/手输坐标）；generateBufferForAI；编辑回填显式 kind + 存量 color 判据（§4.3 v2.2）。
- [✅] **步 3/4 新模块**：zonal（聚合/对比）+ area-stats + rank + vector（叠置/裁剪/抽取/合并/筛选五合一）+ UI 三步向导 dialog。
- [✅] **步 5 内嵌**：nearest/hotspot 纯 ForAI（无 UI）。
- [✅] **步 6 接线**：Toolbox +4 入口（tool-row/pp-tab/sidebar 分派/main init/param-panel 白名单泛化）。
- [✅] **步 7 委托（最敏感）**：tools.js 12 工具改薄委托（observation 逐字保留）；_adoptToolboxResult（C4 全项·focusOnlyResults 沉浸聚焦保留·v2.2 建议 1）；删 geoFetch + 5 合成器；**快照 diff 0/12 全过**。
- [✅] **步 8 验证**：E2E 	est_toolbox_unified ALL-PASS（7 入口/两路径同核/Buffer 双模式+回填/color 判据/console 红线）；流水线回归 	est_toolbox_pipeline ALL-PASS（geo 200×2·机制断言）；obs diff 终跑 0/12；既存用例 compare_regions/exit_badge/domain_lens_threading 全 PASS。
- **环境注记**：DATA/boundaries/presets/ 本机激活 5 预设 + manifest（测试前置·非代码）；既存用例对 LLM 路由/超时有固有方差（exit_badge 首跑失败复跑过·实证非回归）。
- **遗留另案**：① density 委托产物无沉浸聚焦（组 A 遗留·不迁移防未评审行为变更）；② isToolAnalysisLayer 未扩新工具类别（扩会破 EMC R-group 互斥免疫·需评审）；③ MC 系面域模糊匹配首行（现状 fuzzy fallback·zonal-tool 已加 _featName/_normalizeGeoNames 缓解 UI 路径）。
