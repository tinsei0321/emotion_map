模型：deepseek

# CB-CPD-01 · CPD 核心引导逻辑 — DeepSeek 六维评审

> **评审模型**：DeepSeek V4 Pro（资深前端架构师 + 产品设计师 + 信息可视化专家）
> **评审时间**：2026-07-22
> **CB 专轨**：CPD 核心引导 Plan · 第一轮 · 首评
> **评审对象**：`docs/cpd-core-plan.md` v0.2（单份 plan，非全项目）
> **必读文件已自读**：cpd-core-plan-review.md / RULES.md / KNOWLEDGE.md / CLAUDE.md / cpd-core-plan.md / review.py / panel.js / cpd-state.js / harness.js / tools.js / emc-test-cases.md / design-system.md §4
> **承重红线已知**：diagnose 永不动 / 四态出口不动 / harness-stages-tools 不动 / curState 纯客户端 / theme var 禁 hex / 自适应位置 / 软折叠

---

## 一、架构合理性（权重 20%）

### 1.1 两路径分工是否干净？

**结论**：方向对，但"零耦合"宣言有两处不实。

**理由**：
- 计划 §二·决策 2 声称"两条路径 cleanly 分工，零耦合"。但 cpd-guide.js 需读 `_history` 末条的 exit——`_history` 是 panel.js 模块闭包变量（`let _history = []`，panel.js:34），**不导出**。cpd-guide.js 若 import panel.js 内部状态 = 强耦合，若通过事件携带 = 松耦合。计划未明确选择哪种，留下了架构模糊。
- 计划 §九 列出 panel.js 改动："`send()` 加 `cpd:turn-ended`"。但 `send()` finally 段（panel.js:1170-1196）当前**无此 dispatch**——这不是"加一行"，而是在 finally 尾部插入新逻辑。且 finally 段已有 `saveHistory()` + `applyLongConvCollapse()` + episode POST + 状态重置——新增 dispatch 需确认不干扰这些操作的时序。

**改法**：明确数据流为事件驱动（松耦合）：
```js
// panel.js send() finally 尾部追加：
document.dispatchEvent(new CustomEvent('cpd:turn-ended', {
  detail: { exit: _curTrace?.exit, turnId: _history.length, intent: _curTrace?.diagnose?.intent }
}));
// cpd-guide.js 仅监听此事件，不 import panel.js 内部任何变量
```
在计划 §九 panel.js 行加注："事件携带数据，引擎不 import panel.js 内部"。

### 1.2 cpd:turn-ended 接缝是否真零侵入？

**结论**：措辞修正——对 harness/stages/tools 零侵入，对 panel.js 单行事件注入。

**理由**：
- 不改 harness.js / stages.js / tools.js / diagnose / 四态出口 → **真正的零侵入**
- 需要改 panel.js（加事件 dispatch + 删 _setupCpdBar 测试代码 + 引擎驱动 .has-guidance）→ 不算零侵入
- 计划还提到"`_setupCpdBar` 删测试接引擎"——当前 `_setupCpdBar`（panel.js:1505-1564）末尾有 14 行 `Ctrl+Shift+G` 测试代码（lines 1550-1563），这删除是清理而非侵入

**改法**：措辞改为："对对话/分析路径零侵入；对 UI 层（panel.js）单行事件注入"。计划 §二·决策 2 更新此措辞。

### 1.3 deriveGuidance 有无漏态/竞态？

**结论**：存在 **2 个硬伤漏态 + 1 个竞态风险 + 1 个数据结构缺陷**。

#### 漏态 1（硬伤）：ask_user 挂起态

**证据**：harness.js `orchestrate()` 有 `exit: 'ask'` 出口（harness.js:446-456），触发 `onAskUser(action)` hook，panel.js `_renderAskOptions()` 渲染选项胶囊。计划 §四·4.2 状态映射表只列了 RESULT/GAP/PARTIAL/CONCEPT 四种 exit，**无 ask**。

**场景**：用户问"帮我分析这个区域"→EMC 反问"你指的是哪个区域？[选项A] [选项B]"→此时 curState=S3（有消息），exit=ask，无结论。deriveGuidance 读到未知 exit → 走 default（大概率推 analyze 引导）→ 光环在选项胶囊上方闪"问我想看什么"→**与当前交互冲突**。

**改法**：映射表加一行：
```
| S3 | exit=`ask` | `null` | —（用户正在选选项，不打扰；_followUps 已处理追问胶囊）| — |
```

#### 漏态 2（硬伤）：状态回退无处理

**证据**：cpd-state.js `deriveState()` 是纯 forward 瞬态快照——只看当前 DOM，不记历史。如果用户从 S3 删图层退到 S2（layers:changed→recompute），引擎读到 vis.length>0 && msgs>0 && !concl → curState=S2 → 推"选图层"引导。但用户**已有图层只是删了一个**——推 layers 引导是错误引导。

**改法**：cpd-state.js 增加 `let _lastCur = 'S0'` 记录上一状态。deriveGuidance 检测后退（`curIdx < _lastIdx`）→ 返回 `null`（不打扰，等用户进入下一个 forward 状态）。
```js
// cpd-state.js recompute() 修改：
export function recompute() {
  const next = deriveState();
  const prev = _cur;
  if (next !== prev) {
    _lastCur = prev;  // ← 新增：记录上一状态
    _cur = next;
    _subs.forEach(fn => { try { fn(_cur, prev); } catch (_) {} });  // 回调增加 prev 参数
  }
  return _cur;
}
```

#### 竞态：快速连续 send 的 exit 错配

**证据**：用户快速连续发两条消息——第一条 abort、第二条开始。第一条 send() finally dispatch cpd:turn-ended(GAP)，第二条 send() 正在执行。`_history[_history.length-1]` 此时是第一条的 trace（第二条还没 push）。引擎读到 exit=GAP → 推 import 引导——但用户正在输入第二条消息。

**改法**：cpd:turn-ended 携带 `turnId`（= `_history.length`），引擎只处理 `turnId === expectedTurnId + 1` 的事件，忽略过时的 dispatch。

#### 数据结构缺陷：_history 末条 ≠ 当前 turn 的 exit

当 send() finally 段执行 `_history.push({..., trace})` **之前**，`_curTrace.exit` 已经确定。计划说"读 _history 末条 assistant trace 的 exit"——但 cpd:turn-ended 如果在 push 之前 dispatch，`_history` 末条还是上一条。正确的数据源是 `_curTrace.exit`（当前 trace 对象），非 `_history` 末条。

**改法**：cpd:turn-ended 直接从 `_curTrace.exit` 取值，不读 _history。

---

## 二、功能图谱完备（权重 15%）

### 2.1 漏了某项能力？

**结论**：漏了 **3 个状态 + 1 个退出路径 + 1 个关键衔接**。

| 缺失项 | 问题 | 严重度 | 改法 |
|--------|------|--------|------|
| **ask 出口** | 上文漏态 1。映射表无 ask→guidance | 硬伤 | 加 `exit=ask → null` |
| **CONCEPT exit 误推** | 映射表有 `exit=CONCEPT → analyze`。但 CONCEPT 是纯概念问答（"情绪地图能做什么"），答完后推"问我想看什么"不合逻辑 | 中 | `exit=CONCEPT → null`（或退回到当前 curState 的默认引导，而非强推 analyze） |
| **空 import 有 range** | 用户先框范围再导数据：`hasRange=true` 但 `hasImport=false`。curState=S0 → 推 import。文案"先导入情绪数据"没问题，但引导未利用已有范围——应暗示"导入数据到已选范围" | 低 | deriveGuidance 读取 `hasRange` 信号，import 引导文案动态调整 |
| **S4→S0 重置路径** | S4 RESULT CTA 含"换范围"。点击后需清图层+重置状态回 S0。但当前无 CTA→状态重置的映射——依赖用户手动删图层触发的 layers:changed 自然降级 | 中 | CTA handler 主动重置：`document.dispatchEvent(new CustomEvent('cpd:reset'))` → 引擎重置 `_lastCur=null` + recompute |
| **S2→S3 过渡** | 用户选图层后，可能在手动操作 toolbox dock（不想对话）。如果引擎此时聚焦 input（"问我想看什么"），干扰手动操作 | 中 | 增加"用户忙"检测：最近 3 秒内 dock 按钮被点击 → guidance=null |

### 2.2 状态→动作漏信号？

**结论**：_followUps 与 deriveGuidance 存在 **2 个重复/冲突点**，计划未协调。

**冲突 1**：S4 RESULT → 引擎推 export 引导（光环 CTA），同时 `_followUps`（panel.js:450-497）渲染追问胶囊（深读归因 / 区域对比 / 热点分析）。两者的职责边界模糊——引擎管"下一步动作"，_followUps 也管"下一步追问"。G2 计划"合并到同一 guidance 渲染"方向正确，但缺乏合并规则——哪个优先？冲突时谁让步？

**冲突 2**：exit=GAP → 引擎推 import 引导（"补传所需数据"），`_followUps` 也推（"上传数据 / 换问法 / 现有能力"）。两条引导语义重叠。引擎应该知道 `_followUps` 已覆盖此 exit，不重复推。

**改法**：为 deriveGuidance 和 _followUps 建立优先级规则——exit=GAP/PARTIAL/ask/drift 时，引擎 guidance=null（_followUps 已覆盖），引擎只负责 RESULT/CONCEPT 出口 + curState 驱动的主动引导。

---

## 三、承重边界（权重 25%）

### 3.1 有无暗触不可改部分？

**结论**：无硬伤。但存在 **1 个承重宣誓与既有代码的矛盾 + 1 个验证缺口**。

#### 矛盾：curState 已进 LLM context

**证据**：`tools.js buildContext()`（tools.js:464）早已注入 curState：
```js
parts.push(`引导阶段：${_cs}${_csl ? '·' + _csl.label : ''}（用户所处进度，仅供参考，不改变工具选型）`);
```
计划 §七 承重边界写"curState 纯客户端推导（不进 LLM context）"——但既有代码已注入为**语境提示**（非路由裁定）。

**这不是承重违背**——curState 的**推导逻辑**确实是纯客户端的（cpd-state.js deriveState 只看 DOM），inject 进 LLM 的只是**结果值**（作为语境 hint，明确标注"仅供参考，不改变工具选型"）。但计划不应写"不进 LLM context"——这是事实错误。

**改法**：计划 §七 承重边界措辞修正为："curState 推导纯客户端（deriveState 只读 DOM），注入 buildContext 仅作语境提示（标注'仅供参考，不改变工具选型'），不参与 diagnose 路由裁定"。

#### 验证缺口：review.py scale_paradigm_fit desc 改后无灰度

**计划声称**："review 非 diagnose，改 desc 不破 eval"（§配套 A）。技术上正确——`tests/eval_template_flash.py` 测的是 diagnose 模板路由（`select_template`），不涉及 review prompt。

**但缺少灰度**：scale_paradigm_fit desc 从"宏观禁落单点、微观禁泛泛"强化为"微观精确问题必须含宏观局限声明"。Flash 审查员如果因此对每个回答 fail→revise 过度触发→回答质量下降。

**改法**：P1 实施步骤加——改 desc 前跑 `tests/eval_template_flash.py`（confirm 不破）；改 desc 后拿 3-5 条历史问答跑 `review_answer()`，对比旧 desc vs 新 desc 的 pass/fail 率变化。若 fail 率突增 >30%，调整话术。

#### 承重宣誓矛盾：buildContext 中的 curState

上文已覆盖。补充——cpd-core-plan.md §一 已正确描述 curState 在 buildContext 的注入，但 §七 承重宣誓措辞不一致。计划内部自相矛盾。

---

## 四、演示表现力（权重 25%·重点）

> 评价标准：引导是否服务演示逻辑链（张力→点击→分析→宏观诊断）；nudge 增强"突出要素可见性"与"视野-数据-结论同步"，还是打断节奏/沦为装饰；curState 从"反映"升"编排"是否真提升演示张力与宏观诊断有用性。

### 4.1 引导是否服务演示逻辑链？

**结论**：**S0-S2 服务演示链，S3-S4 脱节——引导从"让张力可见"变成"让工具可用"。存在"功能教程化"风险。**

#### S0-S2：✅ 正确服务了演示链的前半段

```
演示链：张力图面 → 引导点击突出要素 → 交互分析张力原因 → 定位关注区+主题倾向+排序优先级
CPD 映射：
  S0 import → 数据是张力图面的前提（服务"张力图面"）
  S1 range  → 框选范围让张力可见（服务"张力图面"的聚焦）
  S2 layers → 选情绪图层→渲染对称拉伸/色带（服务"张力图面"的呈现）
```

这个映射是对的。但**文案是纯功能性的**（"先导入情绪数据""框选一个分析范围""选一个情绪图层显示"），没有暗示**为什么要做这些**——用户感觉在被教程引导，而非被张力图面吸引。

**改法**：S0-S2 文案增加"为什么"的暗示：
- S0：~~"先导入情绪数据，我帮你读懂它"~~ → "**下一张张力地图，从这里开始**——导入情绪数据，我帮你定位最值得关注的区域"
- S1：~~"框选一个分析范围（如西陵区）"~~ → "**聚焦一片城区**——框选范围，看情绪的高低起伏"
- S2：~~"选一个情绪图层显示"~~ → "**看张力**——选情绪图层，深红深绿会告诉你哪里最值得关注"

#### S3-S4：❌ 从"表现力服务"变成"工具教程"

```
S3 analyze → "问我想看什么，或直接跑分析" ← 这是功能引导，不是演示引导
S4 RESULT → "深读归因 · 导出报告 · 换范围" ← 这是出口引导，没有强化"宏观诊断信号"
```

**问题**：S3 引导文案把用户推向"用对话做分析"——但演示逻辑链的核心是"引导点击突出要素→交互分析张力原因"。让用户打字问问题是反模式的——用户应该**点击地图上的深红深绿区域**，而非在对话框问"哪里情绪最差"。

**改法**：S3 引导改为**空间交互优先**：
- S3 analyze → "**点击地图上深红/深绿的区域**——我会告诉你那里为什么这样"（引导 hover/click 地图要素，非打字）
- S3 analyze 备选 CTA → "或直接问我：'哪里情绪最差？' '对比这两个区域'"
- S4 RESULT → "**这片区域的主题倾向是 X×Y，排序第 N**——深读归因 / 对比周边 / 导出报告"（在文案中融入宏观诊断信号，而非纯功能列表）

### 4.2 nudge 增强"突出要素可见性"还是沦为装饰？

**结论**：当前设计偏装饰——光环亮了但跟"突出要素"没有直接关系。

**问题**：
- `.has-guidance` 光环（panel.js 已有的 CSS hook）是一个**输入框光晕**——它引导用户"发消息"，而非"看地图"。演示逻辑链第一阶段是"张力图面"——用户应该被深红深绿吸引，而非被输入框光晕吸引
- 折叠态的 placeholder 文案变化（"先导入情绪数据"）出现在**折叠胶囊的 input**——这个 input 在折叠态下极小（胶囊形态），用户几乎不会读
- 展 开态 banner 在对话流顶部——用户视线在**地图**和**EMC 面板**之间切换时，引导出现在面板顶部而非地图上

**改法**：
1. **地图层引导（G3 轻编排）**：在 S0/S1 时，地图中心叠加半透明引导浮层（"从这里开始"箭头 + "导入数据"），不与 EMC 面板耦合。点浮层触发 import。用户看到地图而非面板时，引导更直观
2. **图层高亮与双同步**：S2 引导时，不仅高亮 layers chip（面板内），还应在地图上显示示意性边界框（"你的数据会出现在这里"），让"视野"和"数据"同步可感
3. **CTA 与视野联动**：S4 RESULT→"导出报告"CTA 点下时，地图应 flyTo 到分析结果最显著的单元 + 短暂橙色 #ff9000 高亮（体现"视野-数据-结论"同步铁律）

### 4.3 折叠/展开一套设计语言？

**结论**：折叠态与展开态是两个独立系统，缺乏统一设计语言。

**证据**：
- 折叠态：光环 + placeholder 文案。光环是输入框光晕，文案在胶囊 input 里
- 展开态：banner（计划 G2 新增）在 EMC 顶部。banner 与空态欢迎卡（panel.js renderEmptyState:1230-1255）可能同时出现（U5 未决）
- 追问胶囊（_followUps）在对话流底部
- **三个引导元素分布在三个位置**：顶部 banner / 底部胶囊 / 折叠态光环——没有形成递进或统一的视觉语言

**改法**：
1. 折叠态光环 → 改为**折叠胶囊整体呼吸色**（`var(--emc-accent)` 的 15% opacity 呼吸动画），而非仅 input 光晕。让整个胶囊"在呼唤"，而非 input 在闪
2. 展开态 banner 与空态欢迎卡 → **融合**（U5 收敛）：无对话时 banner 替换空态欢迎卡内容（复用空态容器）；有对话时 banner 置顶但不重复空态
3. 追问胶囊 → **在 S4 时移入 banner 内部**（作为次 CTA 行），而非留在对话流底部。Banner 成为"下一步行动面板"——主 CTA + 次追问，全部在视野同一区域

### 4.4 curState 从"反映"升"编排"是否真提升宏观诊断有用性？

**结论**：**潜力大，但当前映射偏"功能编排"而非"诊断编排"。**

当前映射：
```
S0→import / S1→range / S2→layers / S3→analyze / S4→export
```
这是**功能链**（导入→框选→加载→分析→导出），不是**诊断链**。从"反映"升"编排"的真正价值应该是：
```
"当前无数据" → "帮你生成第一张张力地图" → "看，这里是情绪最差的区域" → "点击它，看归因" → "这片区域的主题倾向是治理×设施，建议优先关注"
```

**"反映"→"编排"的升维应该是从"告诉用户有什么功能可用"变成"带用户走一遍诊断叙事"**。

**改法**：文案和 CTA 从"功能名"改为"叙事步骤"：
- S0："**生成第一张情绪地图**"（= import + 自动渲染张力）
- S1："**聚焦到西陵区**"（= range + 自动切视图）
- S2："**看张力分布**——深红=情绪差，深绿=情绪好"（= layers + 解释视觉编码）
- S3："**点一下深红色的格子**——我告诉你那里为什么差"（= 引导点击 + 触发归因分析）
- S4："**这里主题倾向是 治理×设施，排名第 3/48**——深读 / 对比 / 导出"（= 归因结果 + 宏观诊断信号 + 下一步）

这样的编排才真正服务"定位关注区 + 主题倾向 + 排序优先级"的有用性环。

---

## 五、分阶段合理（权重 10%）

### 5.1 G1 真能独立 ship？

**结论**：**不能。G1 是半成品——光环亮但无 CTA，用户看到引导却无法行动。**

**证据**：
- G1 交付物：光环亮 + placeholder 文案 + `_fitCollapsedText`。CTA 在 G2 才实现
- 折叠态下唯一可达的控件是 chip（展开按钮）。点 chip→展开→光环灭（engage 解除规则：input 聚焦→remove has-guidance）→展开后看到空面板——引导链断裂
- 计划 §十·验证 G1 说"亮光环 + placeholder；导入点层→文案变"——这验证的是"光环能不能亮"，不是"用户能不能从光环完成操作"
- G1 ship 后的用户体验：光环说"先导入情绪数据"→用户不知道怎么导入→点击展开→光环灭了→困惑

**改法**（二选一）：
- **方案 A（推荐）**：G1 合入 G2 的 CTA 最小集。至少光环能触发 `openImport()`（复用现有 sidebar.js 函数）。光环的 click handler 在 G1 就实现——click→openImport（S0）/ click→cpd:focus-tab range（S1）/ click→高亮 layers chip（S2）。"光环可点"是 G1 MVP 的底线
- **方案 B**：G1 降级为"纯文案提示 + 光环动画"，明确声明"不可交互，CTA 在 G2"。验证标准改为"文案正确切换"而非"用户可操作"

### 5.2 阶段依赖倒置？

**结论**：P0→P1→P2 依赖链合理。但 P2 内部 G1→G2 存在 soft-block。

- G2 CTA 需要 sidebar.js 监听 `cpd:guide-cta`。如果 G1 提前 ship，guidance 对象有 target 字段但无消费方
- **不是严格依赖倒置**（G1 不 import G2），但降低了 G1 独立 ship 的价值
- P0 测试铺底在引擎之前→正确。P1 尺度诚实是小改动→先做合理

---

## 六、风险漏项（权重 5%）

### 硬伤级

| 风险 | 场景 | 当前状态 | 改法 |
|------|------|---------|------|
| **localStorage 脏态** | 用户清 localStorage → 地图图层仍在（来自渲染状态）→ _history=[] → deriveState 判 S2 → 引擎读不到 exit → 行为未定义 | 计划未提及 | 引擎初始化检测：`if (!_history.length && hasVisibleLayers())` → guidance=null + console.warn |
| **状态回退** | 上文 §1.3 漏态 2。S3→S2 后退时推错误引导 | 计划未处理 | cpd-state.js 记录 _lastCur，后退→null |
| **ask_user 漏态** | 上文 §1.3 漏态 1。ask 挂起时误推引导 | 映射表无 ask | 加 `exit=ask → null` |

### 中等风险

| 风险 | 说明 | 改法 |
|------|------|------|
| **引导 vs 追问胶囊打架** | S4 RESULT→引擎推 export 光环；用户点追问胶囊续作→流式结束→引擎又推 export。忽略"用户选了继续分析"的信号 | deriveGuidance S4 逻辑加判断：上轮是追问胶囊触发 → 不推 export，推"继续深读" |
| **流式误推** | 流式结束→finalStep 完成→exit badge 渲染。MutationObserver 在两者间触发可能拿到旧 DOM | 加 300ms debounce |
| **异常路径 dispatch** | send() catch 块后 finally 是否仍 dispatch？如果 orchestrate 抛异常，_curTrace.exit 可能为 undefined | finally 段 dispatch 前检查 `_curTrace?.exit` 存在 |

### 低风险

| 风险 | 说明 |
|------|------|
| **banner 与空态卡同时出现** | U5 未决。G2 前需收敛 |
| **Ctrl+Shift+G 测试代码残留** | 计划已计划删除，无风险 |

---

## 总结

### 六维评级

| 维度 | 权重 | 评级 | 关键问题数 |
|------|------|------|-----------|
| 架构合理性 | 20% | **B+** | 4（ask 漏态·硬伤 / 回退无处理·硬伤 / 数据流模糊 / turnId 竞态） |
| 功能图谱完备 | 15% | **B** | 5（ask 出口 / CONCEPT 误推 / 空 import·range / S4 重置 / S2-S3 过渡） |
| 承重边界 | 25% | **B+** | 2（curState 不进 LLM 宣誓与既有代码矛盾 / review desc 灰度缺） |
| **演示表现力** | **25%** | **C+** | **5（S3-S4 脱节演示链·硬伤 / 偏装饰非诊断编排 / nudge 不看地图 / 三元素三位置 / 功能链非诊断链）** |
| 分阶段合理 | 10% | **B** | 2（G1 不可独立 ship / G1-G2 soft-block） |
| 风险漏项 | 5% | **C+** | 6（localStorage 脏态·硬伤 / 追问打架 / 流式误推 / 异常 dispatch / banner 冲突 / 测试残留） |

**综合**: **B-**（方向对但演示表现力是最大短板。CPD 当前是"功能教程"而非"诊断叙事"——它能帮用户学会用工具，但不能帮用户感受张力图面的价值。需要从"告诉用户有什么功能"升级为"带用户走一遍诊断叙事"）

### 阻塞 G1 的 4 硬伤（修复后才能进入开发）

| # | 问题 | 位置 | 修复 |
|---|------|------|------|
| 1 | ask_user exit 漏态 | §四·4.2 映射表 | 加 `exit=ask → null` |
| 2 | 状态回退无处理 | cpd-state.js | 记录 `_lastCur`，后退→null |
| 3 | localStorage 脏态 | cpd-guide.js init | 有图层无历史→降级 |
| 4 | turnId 未绑定 | cpd:turn-ended 事件 | 携带 turnId，引擎去重 |

### 提升演示表现力的 3 条关键建议（决定 CPD 是"功能教程"还是"诊断叙事"）

| # | 建议 | 影响 |
|---|------|------|
| 5 | **S0-S4 文案从"功能名"改为"叙事步骤"**（见 §4.1 改法） | 将 CPD 从"导入→框选→加载→分析→导出"升级为"生成张力地图→聚焦城区→看张力分布→点击深红格子→宏观诊断信号" |
| 6 | **S3 引导改为空间交互优先**（"点击地图上深红/深绿区域"而非"问我想看什么"） | 让引导服务演示逻辑链的"引导点击突出要素"环节 |
| 7 | **S4 RESULT 文案融入宏观诊断信号**（"这片区域主题倾向 X×Y，排名第 N"） | 让引导服务"定位关注区+主题倾向+排序优先级"的有用性环 |

### 其他强烈建议

| # | 建议 |
|---|------|
| 8 | G1 合入 CTA 最小集（光环可点），否则 G1 不可独立 ship |
| 9 | 明确 cpd:turn-ended 事件携带 exit+turnId+intent，引擎不 import panel.js |
| 10 | banner 与空态卡融合（U5 收敛），追问胶囊 S4 移入 banner |
| 11 | review.py desc 改后灰度验证（3-5 条历史问答 pass/fail 对比） |
| 12 | 计划 §七 承重措辞修正：curState "不进 LLM context"→"推导纯客户端，注入 buildContext 仅作语境提示" |

---

> **给项目方的后续指令**：
> 这是 CB-CPD-01（CPD 核心引导逻辑首轮第三方评审）。12 条建议按严重度排序。
> **阻塞 G1 的 4 硬伤**（#1-#4）必须在设计层先收敛——更新 `docs/cpd-core-plan.md` → v0.3。
> **演示表现力 3 条**（#5-#7）是决定 CPD 价值上限的关键——当前 plan 的 CPD 是"功能教程"，
> 按这三条改后才是"诊断叙事"（项目北极星要求的"一切为了演示表现力"）。
>
> 评审完成后请在 `docs/catch-ball/cb-journal.md` 追加 `## CB-CPD-01` 反评价。
