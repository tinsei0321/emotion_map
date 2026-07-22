# CPD 核心引导逻辑（EMC 主控编排）实施计划

> 状态：**v0.3**（2026-07-22）· CB-CPD-01 反评价后修订（DeepSeek + K3 首轮）→ 待 CB-CPD-02 验证，见 [cpd-core-plan-review.md](cpd-core-plan-review.md) + [cb-journal.md `## CB-CPD-01`](catch-ball/cb-journal.md)
> 分支 `cpd` | 承重：调用次数优先 / 不派 subagent / 只 commit 不 push / 不合分支不抽离
>
> **v0.2 → v0.3 变更**（CB-CPD-01 反评价，26 条建议 agree 20 / partial 6 / disagree 0）：
> - **修 3 处事实错误**（K3 P0，已 grep 核实）：① `.aiq-conclusion` 死信号→改 `.aiq-exit-badge`；② exit 词表大写→小写五值 ∪ undefined（CONCEPT 改判 intent/skipped，补 drift）；③ §4.2 映射 key=curState（deriveState 使 S0/S1 不可达）→ 特征向量真值表。
> - **强化承重实证**：curState 措辞修正（已进 buildContext 语境，非"不进 LLM"）；光环硬编码 hex（ai_qa.css:431）→ theme-var 化。
> - **演示表现力升维**（DeepSeek 最短板）：引导从"功能教程"→"诊断叙事"——S3 空间交互优先、S4 地图定位 CTA 闭合交互环、文案叙事化。
> - turn-ended 载荷 `{exit,turnId,intent}` + finally 守卫 + 引擎 init 恢复；U7 三态分级 + 灰度；新增 U8-U10。
>
> 原引导引擎主体（§二决策 / §三图谱 / §五桥 / §六披露 / §七承重）保留并修正。

CPD 至今所成 = 地基（浮窗 + 软折叠壳 + curState 反映 + 色带/主题/三级权重 + 自适应位置 + 内容驱动高度自适应 + 默认折叠欢迎卡）。**本计划 = CPD 核心 + 两条 EMC 质量配套**：curState 从「反映」升「编排」的同时，补齐「尺度诚实话术」与「运行时测试」两块最薄处。

---

## 一、Context（为什么做）

CPD 地基完工，但 EMC 仍**被动**：curState 只"反映"状态（染进度点），用户得自己找 import/range/toolbox 按钮。这与 design-system §4「此时此刻需要什么 = 出现对应提示」「EMC 按任务进度奉上恰好那一个动作」的核心理念差距大——所有功能仍是"裸按钮"，EMC 没有真正"调度底层"。

**引导引擎**新增确定性编排：每个特征状态算出"此刻唯一动作"，通过已就绪的 `.has-guidance` 光环钩子 + 折叠态文案自适应 + 展开态 CTA banner + 底层控件聚焦，主动引导用户完成 import→range→layers→analyze→结论→导出 全链路。对话/分析路径（harness）原样不动，只加一个客户端事件作为"结论回灌"接缝。

**两条 EMC 质量配套**（v0.2 吸收）：
- **尺度诚实**：产品定位"宏观是护城河，不声称微观精度"（CLAUDE.md「产品本质」），但 EMC ReAct loop 会调到 `nearest`/`buffer`/`inspect_zone`（[tools.js:656/880/923](frontend/js/ai_qa/tools.js#L656)）微观工具——存在"做到微观却不说宏观局限"的诚实落差。落 review checklist（非引导层、非 diagnose）。
- **测试加固**：EMC 是产品最大差异化，运行时测试却最薄（[emc-test-cases.md](emc-test-cases.md) 仅 4 例、前端 JS 零单测 = KNOWLEDGE §2 唯一真短板）= 质量风险最高角落，优先级高于代码重构。

**v0.3 动因**（CB-CPD-01 反评价）：两份第三方首评（DeepSeek + K3）核实 plan v0.2 对"已就绪地基"有 3 处事实陈述错误（死信号/exit 词表/映射 key），且演示表现力是最大短板（功能教程非诊断叙事）。本轮修订吸收 26 条建议，修正事实错误 + 升维演示表现力。

---

## 二、核心设计决策（先定调，再展开）

### 决策 1：引导 = 纯客户端确定性引擎，不进 LLM
"编排"**不**靠 EMC 发对话消息、**不**改 diagnose/harness。新增 `cpd-guide.js`，用纯函数 `deriveGuidance()` 从客户端**特征信号向量**确定性算出引导对象。承重铁律「diagnose prompt 永不动（保 eval）」「四态出口不动」「curState 推导纯客户端」。

### 决策 2：两条路径 cleanly 分工，事件松耦合
- **主动引导路径（新）**：用户"还没说话"时，引导引擎推唯一动作（UI nudge，非对话消息）。
- **对话分析路径（不动）**：用户"已说话"时，走 harness（diagnose→SKILL_DEFS→TOOLS→四态出口）。
- **唯一接缝 = 事件**（v0.3 强化）：panel.js `send()` finally 段 dispatch `cpd:turn-ended {exit,turnId,intent}` → 引擎读载荷算下一步。**引擎不 import panel.js 内部**（`_history` 是模块闭包变量，不导出）；对 harness/stages/tools/diagnose/四态出口**零侵入**，对 panel.js 单行事件注入。

### 决策 3：软折叠基调不变（非严格隐身）
chip/控件始终可达，引导 = 高亮 + 文案 + 光环 + CTA，不强制隐身其他控件。engage 解除（光环停而非控件锁死）。

### 决策 4：尺度诚实 = review 层自觉话术，非引导层
尺度诚实靠 review checklist（[review.py](ai_qa/review.py) `scale_paradigm_fit`）。当问题尺度细于数据支撑，Flash 审查员 fail 不含宏观声明的话术 → revise 重写。承重：review 是审查层 Flash prompt，**非 diagnose**（永不动），改 `desc` 不破 `tests/eval_template_flash.py`（eval 只测 diagnose 模板路由）。

---

## 三、功能图谱（逐一标注编排定位）

| 功能 | 入口（文件） | 现状 | CPD 编排定位 |
|---|---|---|---|
| **import 数据** | dropzone + `openImport`(sidebar.js) + import-input | 裸按钮 | **待编排**：hasImport=false 主动作「生成第一张情绪地图」→ 光环/CTA 触发 import |
| **range 范围** | range tab + range-input + `runRangeImport` | 裸按钮 | **待编排**：hasRange=false 主动作「聚焦一片城区」→ CTA 开 range tab |
| **layers 图层** | drawer 3 tabs + `renderLayerList` + chip | 已软折叠 | **待编排**：无可见情绪层主动作「看张力」→ 高亮 layers chip |
| **toolbox·KDE** | `tool-heatmap`/`openHeatmapDialog`(dock) | 裸按钮 | **半引导**：dock 待编排；EMC `density` skill 已可对话 |
| **toolbox·Grid** | `tool-grid`/`openGridDialog`(dock) | 裸按钮 | **半引导**：dock 待编排；EMC `zonal` skill 已可对话 |
| **toolbox·Buffer** | `tool-buffer`/`openBufferDialog`(dock) | 裸按钮 | **半引导**：dock 待编排；EMC `buffer` skill 已可对话 |
| **toolbox·归因** | `tool-attribution` | **待开发**(toast「开发中」) | 标记未实现；EMC `query_attribution` 部分覆盖 |
| **timeline T1-T3** | `time-bar.js`/`timeline.js` | 裸控件 | **轻编排**：S3/S4 nudge 时点切换（可选，G3） |
| **compare 批4** | `'c'` 键 POC + EMC `compare` skill | 半裸+EMC 可对话 | EMC `compare` skill **已引导**；正式 UI 入口待补（G3） |
| **export 报告** | `_exportReport`(panel.js footer icon) | 已在 EMC 页脚 | **已引导**：S4·result 主动作「导出」+ 地图定位 |
| **search 地名** | `search-bar.js` `initSearchBar` | 裸控件 | **独立**：非情绪分析，暂不编排 |
| **EMC 问答** | `orchestrate`(harness.js) | 主控 | **已是主控**，不改内部 |

---

## 四、引导映射（curState 反映 → 编排 · v0.3 重写）

### 4.1 信号源（全客户端 · v0.3 修正 3 处事实错误）

- 复用 `cpd-state.js` 已订阅：`getLayers()`（visible 非 group）、`#chat-messages .chat-msg-user`、`layers:changed`/`layer:selected`/MutationObserver。
- **S4 结论信号（v0.3 修正）**：~~`.aiq-conclusion`~~（cpd-state.js:29 查询，但**全前端无 JS 创建者 = 死信号**，curState 永不到 S4——CB-CPD-01 K3 P0-1 核实）→ 改用 **`.aiq-exit-badge`**（[panel.js:378](frontend/js/ai_qa/panel.js#L378) 回答完毕时创建，流式中不存在，顺带免疫流式误推）。deriveState 的 `concl` 判据同步改。
- **特征谓词（v0.3 定义，CB-CPD-01 K3 M5）**：
  - `hasImport` = 存在**非 AI 组、非 tool 产出**的 point 层（排除 EMC grid/AI 组含 point 的误判）。
  - `hasRange` = 有 isRange 层（复用 [state.js:662](frontend/js/state.js#L662) `isRangeLayer`，无歧义）。
  - `hasAnalysis` = 存在 `paint._ui.tool∈{grid,zonal,heatmap}` 或归属 'EmotionMap Copilot' 组的层。
  - `hasVisibleEmotionLayer` = 有可见情绪层（visible 非 group 非 range）。
- **上轮 exit（v0.3 修正词表，CB-CPD-01 K3 P0-2）**：读 **`_curTrace.exit`**（非 `_history` 末条——push 时序竞态）。harness 实际返回**小写五值** `result`/`gap`/`partial`/`ask`/`drift`（[harness.js:272/292/307/476/568/608/620/644](frontend/js/ai_qa/harness.js#L272)）∪ `undefined`（general 短路 [harness.js:372/412](frontend/js/ai_qa/harness.js#L372) 无 exit 字段）。~~plan v0.2 大写 RESULT/CONCEPT~~ 是事实错误。CONCEPT 不是 exit 值，改判 `trace.diagnose.intent==='general' || trace.review.skipped∈{'general','quick-general'}`（同 `_followUps` [panel.js:478](frontend/js/ai_qa/panel.js#L478) 同源同判）。
- **流式硬门（v0.3）**：引擎读 `_streaming`（[panel.js:1135](frontend/js/ai_qa/panel.js#L1135)），流式中 `guidance=null`（双保险：exit-badge 天然不在 + _streaming 门）。

### 4.2 引导映射（v0.3 重写：key 从 curState → 特征向量真值表）

> **v0.3 修正（CB-CPD-01 K3 P0-3）**：deriveState（cpd-state.js:27-35）任何可见层→S2，故以 curState 为 key 时 S0/S1 永不可达（结构性错误）。映射改用**特征信号向量**，curState 仅作进度点显示输入。

**特征向量** `(hasImport, hasRange, hasVisibleEmotionLayer, hasAnalysis, lastExit, streaming)` → guidance（按优先级自上而下首匹）：

| hasImport | hasRange | visEmotion | lastExit | streaming | kind | 文案（叙事化·服务演示链） | target |
|---|---|---|---|---|---|---|---|
| **false** | * | * | * | false | `import` | 「生成第一张情绪地图——导入数据，我帮你定位最值得关注的区域」 | `openImport` |
| true | **false** | * | * | false | `range` | 「聚焦一片城区——框选范围，看情绪的高低起伏」 | `cpd:focus-tab range` |
| true | true | **false** | * | false | `layers` | 「看张力——选情绪图层，深红深绿告诉你哪里最值得关注」 | 高亮 layers chip |
| true | true | true | ∈{undefined, general} | false | `analyze`（空间优先） | 「点击地图上深红/深绿的区域——我告诉你那里为什么」（备选 CTA：「或问我：哪里情绪最差？」） | 地图 hover/click 引导 / input |
| true | true | true | `result` | false | `export`(+地图定位) | 「这片主题倾向 X×Y，排序第 N——深读 / 在地图定位 / 导出」 | export + 地图 focus + range |
| true | true | true | `gap`/`partial` | false | `null` | —（`_followUps` 已覆盖追问胶囊，引擎不重复推） | — |
| true | true | true | `ask` | false | `null` | —（选项胶囊已在答案区，U3 收敛为不介入） | — |
| true | true | true | `drift` | false | `retry` | 「生成异常·已拦截——换个问法或缩小范围」 | input（同 `_followUps`:465） |
| * | * | * | * | **true** | `null` | —（流式硬门） | — |

**规则**：
- **回退 = 同真值表重算**（无特殊路径，CB-CPD-01 共识）：用户删图层/range → hasImport/hasRange 变 false → 自然回推 import/range。
- **优先级**：`hasImport=false` 优先一切（先导数据）→ `streaming=true`（不打扰）→ `lastExit∈{gap,partial,ask}` → null（让 `_followUps` 接手）→ `drift` → retry → 其余按表。
- **文案叙事化**（v0.3·CB-CPD-01 演示表现力）：从"功能名"（导入/框选/加载）改"诊断叙事步骤"（生成张力地图/聚焦城区/看张力分布），服务演示逻辑链的诊断叙事，非功能教程。具体文案 G1/G2 实现时打磨。

### 4.3 调度接口（v0.3 强化：事件载荷 + init 恢复 + reset）

- **不改** harness.js / stages.js / diagnose / 四态出口 / tracker。引擎只读（trace/curState），不写 harness；**不 import panel.js 内部**。
- **turn-ended 事件载荷（v0.3）**——panel.js `send()` finally 段 dispatch：
  ```js
  if (_curTrace?.exit !== undefined) document.dispatchEvent(new CustomEvent('cpd:turn-ended', {
    detail: { exit: _curTrace.exit, turnId: _history.length, intent: _curTrace?.diagnose?.intent }
  }));
  ```
  - 携带 `{exit, turnId, intent}`：`turnId` 供引擎去重（快速连续 send 只处理 expectedTurnId+1，CB-CPD-01 DS 竞态解）；`intent` 供 general 判定。
  - **finally 守卫** `_curTrace?.exit !== undefined`（abort/异常 orchestrate 抛错时不误 dispatch）。
- **引擎 init 主动恢复（v0.3，CB-CPD-01 K3 竞态）**：F5/switchSession/clearChat 不 dispatch turn-ended → 引擎初始化时经 panel.js 导出的**只读 getter** 读 `_history` 末条 trace.exit 一次，算初始引导（非 import 闭包）。G1 验收三硬用例：F5 恢复 / 切会话 / abort 不误推。
- **"换范围"重置（v0.3，CB-CPD-01 DS）**：S4·result 的"换范围"CTA dispatch `cpd:reset` → 引擎重置 lastExit + recompute（不依赖手动删图层）。
- CTA 复用既有入口：`openImport`/`cpd:focus-tab`/`openHeatmap/Buffer/GridDialog`/`_exportReport` + 地图 focus/popup（S4 地图定位，复用 `_followUps`:455 region 抽取）。

---

## 五、对话 → 功能桥

### 5.1 正向（用户自然语言 → 底层功能）：**不改**
已由 harness 路由（`_quickIntent` → `diagnoseStep` → SKILL_DEFS → TOOLS → 落地图）。CPD 不介入。

### 5.2 反向（结论 → 引导下一步）：**事件接缝 + _followUps 优先级**
- `_followUps`（[panel.js:450-497](frontend/js/ai_qa/panel.js#L450)）已有 exit→追问胶囊映射（gap/partial/ask/drift 均覆盖）。
- **职责划分（v0.3·CB-CPD-01 共识）**：`lastExit∈{gap,partial,ask,drift}` → 引擎 guidance=null（`_followUps` 已覆盖，不双 CTA 打架）；引擎只负责 **curState 驱动的主动引导 + result 出口**。G2 banner 内主 CTA（UI 动作，按钮）与追问胶囊（对话动作，`aiq-suggest-chip`）**视觉分组**不混排。

---

## 六、渐进披露细则

### 6.1 每功能：何时出现 / 如何呈现 / 用完如何退场
| 功能 | 何时出现 | 如何呈现 | 用完退场 |
|---|---|---|---|
| import | hasImport=false | 折叠态光环 + 文案；展开态 banner CTA | 导入成功（layers:changed）→ 转 range |
| range | hasRange=false | banner CTA「聚焦城区」→ 开 range tab | range 层加入 → 转 layers |
| layers | 无可见情绪层 | 高亮 layers chip + banner | 可见情绪层出现 → 转 analyze |
| KDE/Grid/Buffer | analyze 阶段 | 高亮 toolbox chip + banner | 聚合层生成 / 对话开始 → null |
| export | result 出口 | banner 主 CTA + 地图定位次 CTA | 导出后停 result（可 cpd:reset 换范围） |

### 6.2 折叠胶囊引导耦合（`.has-guidance`，钩子已就绪）
1. `guidance != null` 且 `_emcCollapsed == true` → `classList.add('has-guidance')` + `placeholder = guidance.text` + `_fitCollapsedText()`。
2. `guidance == null`（流式/ask/gap/partial）或展开态 → `remove('has-guidance')`。
3. **engage 解除**：CTA 点击 / input 聚焦 / input 输入 / 动作完成 → `remove('has-guidance')`（光环停，避免闪烁；下一状态变化再定重亮）。
4. 删除 `Ctrl+Shift+G` 测试代码（panel.js `_setupCpdBar`）。

### 6.3 展开态呈现
- `.emc-guide-banner`（`.emc-cpd-bar` 下、`#emc-view` 上）：`guidance.text` + 主 CTA +（result 时）次追问胶囊（合并 `_followUps`，视觉分组）。
- 无对话时 banner 与空态欢迎卡（`renderEmptyState`）融合（U5 收敛）；有对话时置顶。
- banner left 走自适应（复用 `relayoutFloats`/`positionFloatingPanels`）。

### 6.4 演示链服务 + 绿色摘要条（v0.3·CB-CPD-01 演示表现力共识）
- **引导服务演示链交互环**（U6 实质解法）：引导不止于"装载链"（import→range→layers），须闭合"点击要素→分析→归因"交互环——
  - **S3 analyze 空间交互优先**：文案"点击地图深红/深绿区域"（引导 hover/click 要素），对话作备选 CTA（非首选）——服务演示逻辑链"引导点击突出要素"环节。
  - **S4·result 地图定位 CTA**：结论含 `[ref:区域]`/`{{focus:}}` 时，banner 次 CTA「在地图上定位该区域」（复用 `_followUps`:455 region 抽取 + 现有 focus/popup），把引导环从"结论"闭合回"视野端"——落实"视野↔数据↔结论"同步铁律。
- **文案叙事化**：S0-S4 从"功能名"改"诊断叙事步骤"（生成张力地图/聚焦城区/看张力分布/点击深红格子/宏观诊断信号），服务"定位关注区+主题倾向+排序优先级"有用性环。具体文案 G1/G2 打磨（见 §4.2 文案列）。
- **绿色摘要条定义**（§八 G3 提及但 v0.2 未定义，CB-CPD-01 K3 L2）：已完成步骤（import/range）折叠成的「● 已导入 · 修改」条 = **banner 的 done 变体**（同组件不同态，非新视觉方言）；点「修改」回退引导（同真值表重算）。

---

## 七、承重边界（不动清单 · v0.3 措辞修正）

- ✅ **diagnose prompt 永不动**（保 eval）——引导纯客户端，尺度诚实落 review 层，均不进 diagnose context。
- ✅ **四态出口不动**（`result`/`gap`/`partial`/`ask`/`drift` + general 短路）——引擎只读 exit。
- ✅ **harness.js / stages.js / tools.js TOOLS / tracker 签名 / 网格算法 / paint-inplace 不动**。
- ✅ **curState 推导纯客户端**（cpd-state.js `deriveState` 只读 DOM，不改逻辑）；其值已注入 `buildContext`（[tools.js:455-458](frontend/js/ai_qa/tools.js#L455)）仅作 LLM 语境提示（标注"仅供参考，不改变工具选型"），**不参与 diagnose 路由裁定**——v0.2 "不进 LLM context" 措辞错误（CB-CPD-01 核实），此修正。
- ✅ **自适应位置铁律**：banner/浮层 left 随锚点动态算，不写死。
- ✅ **EMC 颜色全走 theme var**（`var(--emc-accent)` 等），禁硬编码 hex/rgba——**含光环渐变**（现 ai_qa.css:431 七色硬编码 hex 违承重，CB-CPD-01 K3 核实 → 抽 `--emc-halo-*` theme var，Light 另校准，落 G2/G4）。
- ✅ **软折叠基调**（非严格隐身，chip 始终可达）。
- ✅ **review checklist 骨架稳定**（七条 key/name 不改——前端 [panel.js:721](frontend/js/ai_qa/panel.js#L721) 按 key 渲染）；尺度诚实只改 `scale_paradigm_fit` 的 `desc`，review 非 diagnose、改 desc 不破 eval。
- ⚠️ 批4 grid 镜像 bug / diag 日志（main 遗留）CPD 期间不动。

---

## 八、分阶段交付（v0.3 · P0 测试 → P1 尺度 → P2 引擎）

### P0 · EMC 测试加固铺底（§配套 B · 最高优）
- 扩充 [emc-test-cases.md](emc-test-cases.md)（4 → N）：
  - 落地 ⬜ 用例 2（domain_lens threading）/ 用例 3（`_driftRe` 裸 JSON）。
  - 新增 **CPD 地基行为用例**（已实现）：默认折叠欢迎卡 / 内容驱动高度自适应（拉长+缩回）/ exit-badge 填充渲染 / 历史垃圾桶加大+全清。
  - 新增 **尺度诚实用例**（P1 配套）：问"某条街精确情绪分"→ 断言回答含"宏观方向/非精确测量"声明。
  - **引擎状态转移用例挪 G1**（CB-CPD-01 K3 L1：P0 引擎不存在，测不了——v0.2 自相矛盾，此修正）。
- 落地 `tests/browser/` 复用 [lib/emc_helpers.py](tests/browser/lib/emc_helpers.py)；断言硬挂真端点。
- 前端 vitest 单测基建：本次不搭（后续可选）。

### P1 · 尺度诚实（§配套 A · 小工作 + 灰度）
- 改 [review.py:50-53](ai_qa/review.py#L50) `scale_paradigm_fit` desc（详见 §配套 A）。
- **灰度验证 + U7 三态分级**（v0.3，详见 §配套 A）。
- 顺手修 review.py:1 / ai_qa/__init__.py:11 docstring "六条"→"七条"漂移（CB-CPD-01 K3 L5）。
- 承重回归：跑 `tests/eval_template_flash.py` 确认 eval 不破。

### P2 · CPD 引导引擎 G1–G4（测试网就绪后推进 · v0.3 强化）
- **G1 引擎 MVP + 折叠态耦合 + 光环可点**：`cpd-guide.js`（`deriveGuidance` + 特征向量真值表 + subscribe）；panel.js `send()` finally dispatch `cpd:turn-ended {exit,turnId,intent}`（finally 守卫）；**引擎 init 主动读末条 trace**（F5/切会话恢复）；`_setupCpdBar` 删测试接引擎驱动 `.has-guidance` + placeholder + `_fitCollapsedText` + engage 解除；**光环 click 最小 CTA**（click→`openImport`/`cpd:focus-tab range`/高亮 chip）——G1 独立 ship 且含最小可点闭环（CB-CPD-01 调和 DS 方案 A + K3 U2）。颜色全 theme var（含光环 `--emc-halo-*`）。
- **G2 展开态 banner + CTA 调度**：`.emc-guide-banner` + 主 CTA + result 次追问胶囊（视觉分组）；CTA→`cpd:guide-cta`→sidebar.js / 触发 import/工具/导出/地图定位；banner 自适应位置。
- **G3 全状态 + 细则 + 轻编排**：绿色摘要条（§6.4 banner done 变体）；timeline/compare 正式 UI 轻编排；边界（用户忙检测 U8 / 空边界）。
- **G4 抛光 + 回归**：主题同步（Light/Dark，含光环渐变校准）、动画节奏、光环/CTA 一致性；Playwright 回归（状态转移/CTA 调度/exit 回灌/init 恢复）。
- 每完成一 G 立即补行为用例（TDD-lite）；每 Phase commit（不 push）+ sync revision-log。

---

## 九、关键文件

| 文件 | 改动 | 时机 |
|---|---|---|
| `frontend/js/ai_qa/cpd-guide.js` | **新建**：确定性引擎（deriveGuidance + 特征向量 + 映射 + subscribe + init 恢复） | P2·G1 |
| `frontend/js/ai_qa/panel.js` | `send()` finally 加 `cpd:turn-ended {exit,turnId,intent}`（守卫）；`_setupCpdBar` 删测试接引擎 + 光环 click CTA；导出末条 trace 只读 getter；banner 渲染 | P2·G1/G2 |
| `frontend/js/ai_qa/cpd-state.js` | S4 信号 `.aiq-conclusion`→`.aiq-exit-badge`；导出 hasImport/hasRange/hasAnalysis/hasVisibleEmotionLayer 谓词（不改 deriveState 逻辑） | P2·G1 |
| `frontend/js/sidebar.js` | 监听 `cpd:guide-cta`/`cpd:reset`（复用 `cpd:focus-tab`） | P2·G2 |
| `frontend/css/ai_qa.css` | `.emc-guide-banner` + `.has-guidance` 微调；**光环渐变抽 `--emc-halo-*` theme var**（ai_qa.css:431 硬编码 hex→var，Light 另校准） | P2·G2/G4 |
| `ai_qa/review.py` | `scale_paradigm_fit` desc 强化；:1 docstring "六条"→"七条" | P1 |
| `docs/emc-test-cases.md` | 扩充用例（4→N，地基行为 + 尺度诚实） | P0 |
| `tests/browser/test_*.py` | 落地 ⬜ 用例 + G1 引擎行为用例（复用 emc_helpers） | P0/P2 |
| `docs/design-system.md` §4 | 补「引导引擎 = 确定性编排层」说明 | P2·G4 |

**复用（不重造）**：`deriveState/recompute/subscribe/initCpdState`(cpd-state.js)、`_fitCollapsedText/setEmcCollapsed/_fitEmcToContent`(panel.js)、`_followUps`(+其 exit/intent/skipped 判据)、`cpd:focus-tab`/`openImport`、`openHeatmap/Buffer/GridDialog`、`relayoutFloats`、`isRangeLayer`(state.js:662)、`.has-guidance` CSS、`tests/browser/lib/emc_helpers.py`、REVIEW_CHECKLIST 七条骨架。

---

## 十、验证

1. **启动**：`py frontend/serve.py 8080`，浏览器开。
2. **P0 测试**：`py tests/browser/test_compare_regions.py` 等跑通；emc-test-cases.md ⬜→✅；断言挂真端点。
3. **P1 尺度诚实**：browser 问"某条街精确情绪分"→ 回答含宏观声明；改 review.py 后 `tests/eval_template_flash.py` 不破 + 灰度（≥10 条历史微观问题 fail 率对比 <30%）。
4. **P2 G1 肉眼**：清 localStorage → 折叠 → 亮光环 + placeholder；**光环可点**→触发 import/focus-tab；导入→文案变；出结论→文案变 export。**G1 三硬用例**：F5 恢复引导 / 切会话恢复 / abort 不误推。
5. **P2 G2 肉眼**：展开→banner 显 CTA；点 CTA→开 drawer/import/工具/导出/**地图定位**（S4 含 ref 时）。
6. **承重回归**：diagnose/四态出口未变→跑 emotion_analysis + GAP 问，出口徽章一致；光环渐变 Light/Dark 都走 theme var（无硬编码 hex）。
7. **G4 Playwright**：状态转移链 + CTA 调度 + exit 回灌 + init 恢复 + 回退引导。
8. 常规前端改动由用户肉眼验（memory `no-routine-playwright-verify`）。

---

## §配套 A · 尺度诚实（决策 4 展开 · v0.3 加灰度 + U7 三态）

> 把"宏观护城河"从产品文档落成 AI 自觉话术。落点 = review 审查层（非引导层、非 diagnose）。

- **现状落差**：`scale_paradigm_fit`（[review.py:50-53](ai_qa/review.py#L50)）desc 仅"宏观禁落单点、微观禁泛泛"——查颗粒度，未要求微观精确问题声明宏观局限。
- **强化**：desc 追加——问题尺度细于数据支撑（精确到单点/单街/单建筑）时，回答须含"情绪地图是宏观方向、非精确测量"诚实声明 + 给能给的宏观趋势，禁假装精确值。
- **U7 三态分级（v0.3·CB-CPD-01 共识）**：desc 强化后 Flash 对微观问题 fail 率必升 → revise 触发率/时延/token 涨（revise 仅 1 轮，仍无声明则按 fail 交付）。收敛三态防飙升：
  - 无声明 = **fail**（触发 revise）
  - 有声明无替代趋势 = **warn**（轻提醒，不触发 revise）
  - 声明 + 替代趋势齐全 = **pass**
  （review verdict 三态天然支持。）
- **灰度验证（v0.3·CB-CPD-01 共识）**：P1 改 desc 后取 **≥10 条历史微观问题**（episodes.jsonl）跑 `review_answer()` 对比新旧 fail/revise 率；突增 >30% 先调话术再上。
- **分寸**：声明诚恳不推诿——"情绪地图看的是宏观分布与演变，这条街级别精确分数数据不足，但周边区域宏观趋势是 X"。给替代价值，不空手。
- **承重**：review 非 diagnose，改 desc 不破 eval；前端按 key 渲染，改 desc 零影响。

---

## §配套 B · EMC 测试加固（P0）

> EMC = 差异化核心，运行时测试却最薄。先铺底，给 P2 引擎重构兜底。

- **catalog 扩充**（emc-test-cases.md 4→N）：落地 ⬜ 用例 2/3 + **CPD 地基行为**（默认折叠欢迎卡/高度自适应/exit-badge/历史桶）+ 尺度诚实（P1 配套）+ **G1 引擎行为**（状态转移/init 恢复/光环可点，随 G1 实现 TDD-lite 补）。
- **落地原则**：复用 `tests/browser/lib/emc_helpers.py`；断言硬挂网络/数据层（真 POST+数据）；软挂回答散文。
- **vitest 单测基建**：本次不搭；运行时行为 Playwright 覆盖。后续若纯函数（`deriveGuidance`/`_exitBadge`）增多再评估。

---

## 十一、开放问题（待 CB-CPD-02 收敛）

1. **U1 引导 = UI nudge（非对话消息）**——CB-CPD-01 两份均 agree。
2. **U2 MVP 分阶段**——CB-CPD-01 K3 agree G1 独立 ship；DS 要求含光环可点（v0.3 调和：G1 独立 ship + 光环 click 最小 CTA）。
3. **U3 S4·ask 出口引导**——CB-CPD-01 两份收敛为 **null 不介入**（选项胶囊已在答案区），写入真值表。
4. **U4 timeline/compare/search 编排深度**——CB-CPD-01 agree 当前深度（search 独立 / timeline·compare 轻编排入 G3）。
5. **U5 banner 与空态欢迎卡融合**——CB-CPD-01 agree 融合（§6.3）。
6. **U6 引导是否真服务演示链**——CB-CPD-01 partial：当前只服务前链路（装载），**交互环未闭合**；v0.3 解法 = S3 空间交互优先 + S4 地图定位 CTA（§6.4），闭合后才解除"为引导而引导"风险。
7. **U7 尺度诚实话术分寸**——CB-CPD-01 收敛**三态分级**（fail/warn/pass）+ 灰度（§配套 A）。
8. **U8（v0.3）用户忙检测**：S2→S3 过渡时用户在手动操作 dock（3 秒内 dock 点击）→ guidance=null。G3 边界。
9. **U9（v0.3）engage 解除后再亮兜底**：长期无动作引导消失，是否加"N 分钟→轻量再亮"或保持不打扰优先。留观察。
10. **U10（v0.3）地图层引导浮层**：S0/S1 地图中心叠加引导浮层（DS 建议），属另一子系统；先用 S4 地图定位 CTA 轻量闭合，地图浮层抛光期评估。
