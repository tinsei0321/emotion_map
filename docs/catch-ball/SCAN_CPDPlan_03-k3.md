# SCAN_CPDPlan_03 · k3 独立评测（第三轮验证评审）

模型：k3
轮次：CB-CPD-03（v0.4 验证）
日期：2026-07-22
评测人立场：中立第三方 · 证据驱动 · 全部结论经代码复核（引文件:行号）

---

## 〇、总体判断

**综合评级：A-（上轮 B+）——agree v0.4 架构方案收敛，P0 测试铺底可立即启动；但发现 1 个 v0.4 新引入的高优链式缺陷（H1），G1 动手前必修，否则任何一次 general 问答后引导引擎永久冻结。**

v0.4 声称的 9 项修订（H1 DI / H2 变量降级 / M1 色名 / M3 流式优先 / M2 兼带 CTA / R3 / R4 / U8 / L1 / L5）经逐条代码复核**全部属实**（§一）。但本轮对 v0.4 新增机制（turn-ended 事件 + turnId 去重 + finally 守卫）做组合推演时，发现三者在 general 短路场景下相互咬合成断链（§三 H1）——这是前两轮未暴露、由 v0.3/v0.4 修复动作自身引入的新缺陷，性质同前两轮"修订引入新高优"的模式一致。

---

## 一、上轮（CB-CPD-02）闭环核验：9/9 属实

| 上轮问题 | v0.4 处置 | k3 代码复核 | 结论 |
|---|---|---|---|
| H1 循环 import | §4.3 改依赖注入 `initCpdGuide({getLastExit, isStreaming})`，cpd-guide.js 零 import panel.js | 注入 getter `() => _history.at(-1)?.trace?.exit ?? null` 与 panel.js:1182 push 结构吻合（trace 挂在 assistant 条目，`.at(-1)` 取到） | ✅ 成立 |
| H2 S4 动态变量无源 | §4.2 降级为 `{区域名}`（复用 _followUps:455） | panel.js:455 `ans.match(/\[ref:([^\]]+)\]/)…` 抽取逻辑实证存在 | ✅ 成立 |
| M1 文案"深红"脱节 | §4.2 改"深绿/深橙"+ §4.2 色名铁律（从 `--geojson-color-emotion-very-*` 派生） | tokens.css:25-29 端点 `#0F6E56`/`#D85A30`（CB-CPD-02 已核），"深红"在渲染端确实不存在 | ✅ 成立 |
| M3 优先级文字矛盾 | §4.2 规则行改 streaming 第一 | 与真值表末行（streaming=true→null）语义对齐 | ✅ 成立 |
| M2 hasRange=false+result 断档 | §4.2 row 2 注：兼带深读/导出次 CTA | 表述无歧义 | ✅ 成立 |
| R3 hasImport 误判 | §4.1 排除来源注释（inspect_zone marker/zonal grid/AI 组） | 谓词定义完整 | ✅ 成立 |
| R4 S3 实现路径 | §6.4：G1 被动文案 / G3 地图高亮三端同步 | 阶段切分干净 | ✅ 成立 |
| U8 3 秒魔数 | 弃时间窗，改 is-open 确定性信号 | 方向正确，但事实描述有偏差 → 本轮 L1 | ✅（附修正） |
| L1/L5 init 重置 + 不持久化 | §4.3 重置 expectedTurnId + §6.5 明文 | 与 switchSession:227/clearChat:1270 场景匹配 | ✅ 成立 |

前两轮承重事实复核（维持有效）：harness 小写五值 exit（harness.js:272/292/307/476/568/580/608/620/644 逐一 grep 核实）；general 短路无 exit 字段（harness.js:372/412 返回对象无 `exit` key）；`.aiq-exit-badge` 由 panel.js:378 真实创建；`_streaming` 置位于 panel.js:1135；review.py:50-53 现状 desc 与 §配套 A 引述逐字吻合；emc_helpers.py / eval_template_flash.py 均存在。**闭环成立。**

---

## 二、六维评价

### 1. 架构合理性 —— ✅ 优良（一个组合缺陷见 H1）

依赖注入方案干净：`panel.js → initCpdGuide({getters}) → cpd-guide.js` 单向，引擎对 panel.js 零 import，与决策 2"引擎不 import panel.js 内部"完全自洽。运行时事件（turn-ended）+ init 恢复（getter）双通道分工明确：事件管增量、getter 管全量恢复。finally 守卫防 abort 误推的意图正确（panel.js:1171-1176 catch 段 settled=false）。**但事件覆盖范围与 turnId 去重语义组合出断链——见 H1，这是本轮唯一结构性问题。**

### 2. 功能图谱完备 —— ⚠️ 一个死信号 + 一个谓词盲区（M1/M2）

§三图谱 12 行逐一核对无遗漏（search 独立、toolbox·归因标记未实现均合理）。但：
- **M1**：特征向量定义含 `hasAnalysis`（§4.1），§4.2 真值表六列**无此列、零行引用**——定义了不用的死信号。
- **M2**：`hasVisibleEmotionLayer` 谓词（§4.1："visible 非 group 非 range"）不判情绪性，任意可见层都算 → 详见 §三。

### 3. 承重边界 —— ✅ 清白（一处提示见 L2）

逐条核对禁改清单：diagnose prompt 不动（引导纯客户端 + 尺度诚实落 review 层）；四态出口不动（§七措辞已是"五值 + general 短路"准确描述）；harness/stages/tools TOOLS/tracker 不动；curState 纯客户端（tools.js:455-458 注入仅作语境提示的修正表述准确）；自适应位置（cpd-state.js:71-97 实证已是锚点动态算）；软折叠（决策 3）。`#ff9000` 出现在 §6.4 G3 文案——地图侧高亮不在"EMC 颜色"承重字面范围，但见 L2 提示。

### 4. 演示表现力 —— ✅ 方向到位（一个演示链断点风险见 M2）

U6 实质解法成立：S3 空间交互优先（"点击深绿/深橙区域"为首选、对话降备选）+ S4 地图定位 CTA（复用 :455 region 抽取）把引导从"装载链"闭合进"点击要素→分析→归因"交互环——这是三轮以来演示表现力首次从"文案叙事"落到"交互闭环"。色名铁律（§4.2，从 theme var 派生显示名）保证视野端色带与引导文案永远同词，是"视野↔数据↔结论同步"在文案层的正确落地。G3 呼吸闪烁（极性 top/bottom 橙色脉冲高亮）是三端同步铁律的首个视觉落地，方向对。**风险：M2 谓词盲区会让"点击深绿/深橙区域"指向一张根本没有情绪渲染的图面 = 演示链第一环（张力图面）断点。**

### 5. 分阶段合理 —— ✅ 成立（H1 必须划入 G1 范围）

P0 测试 → P1 尺度 → P2 引擎依赖正序；G1 含光环可点最小闭环可独立 ship；引擎状态转移用例挪 G1（v0.3 已修）消除自测悖论。**注意：H1 不是追加功能，它是 §4.3 事件规范自身的缺陷，修复必须作为 G1 实现的一部分（改 dispatch 条件 + 去重语义两行代码级），不能推给 G3/G4。**

### 6. 风险漏项 —— ⚠️ H1 即本轮核心漏项

v0.4 已覆盖：流式双保险、init 三硬用例、引导态不持久化、engage 解除、回退同表重算。本轮新增：H1（general 断链，§三）；其余见 L1/L2。

---

## 三、本轮发现（按优先级）

### H1（高优 · G1 必修）：general 短路与 turn-ended 机制三处咬合断链

**事实链（全部代码实证）：**
1. general 短路返回对象**无 exit 字段**（harness.js:372 quick-general / :412 general）。
2. panel.js:1162 `_curTrace.exit = _result.exit || _curTrace.exit` → general 轮 `_curTrace.exit` 保持 `undefined`。
3. v0.4 §4.3 dispatch 守卫 `if (_curTrace?.exit !== undefined)` → **general 轮不 dispatch**。
4. 但 general 轮**照常 push 历史**（panel.js:1181-1184，settled=true）→ `_history.length` 每轮 +2（user :1126 + assistant :1182）。
5. v0.4 §4.3 去重语义"只处理 expectedTurnId+1"（严格递增 1）。

**三个咬合后果：**
- **断链冻结**：general 轮 turnId 跳过 +2，下一轮 result  dispatch 的 turnId 与引擎 expectedTurnId+1 不符 → 引擎丢事件 → **此后引导永久冻结**，且无任何报错迹象（静默失败）。
- **lastExit 陈旧**：result 之后用户问 general 问题（如"什么是 4×5 矩阵？"）→ 无事件 → 引擎仍认为 lastExit=result → 继续推 export/定位 banner，与当前对话语境脱节。
- **intent 载荷成死重**：§4.3 声明 intent"供 general 判定"，但 general 轮恰恰不 dispatch——intent 在它唯一服务的场景永远缺席；§4.2 真值表 row 4 的 `general` 值同理永不出现（它既不是 exit 值，也无事件更新）。

**改法（两行代码级，G1 范围内）：**
1. dispatch 条件从 exit 守卫改为完成守卫：`if (settled) dispatch({ exit: _curTrace?.exit ?? null, turnId: _history.length, intent: _curTrace?.diagnose?.intent ?? null })`。settled 仅在 orchestrate 正常返回时置 true（panel.js:1161），abort/异常天然不 dispatch——原守卫意图完整保留，且 general/drift/ask 全部覆盖。
2. 去重语义从"严格 expectedTurnId+1"改**单调递增**（`turnId > lastProcessedTurnId` 即处理）。turnId 本就按 +2 步进，严格 +1 在数学上必断；单调判断同时免疫快速连续 send 与 general 跳号。
3. §4.2 row 4 标注改：`lastExit ∈ {null（含 general 短路）}`，并注明引擎可用 `intent==='general'` 区分 null-exit 的来源（与 _followUps:478 同源同判）。

### M1（中优 · G3 前定夺）：hasAnalysis 死信号——dock 产图场景无桥

§4.1 特征向量含 hasAnalysis，§4.2 真值表无列无行引用。具体场景：用户从 toolbox 直接跑 Grid/Heatmap（openHeatmapDialog 等 → openParamPanel，实证 heatmap-tool.js:610/buffer-tool.js:86/grid-tool.js 均挂 #param-panel），全程无 EMC 对话 → hasAnalysis=true、lastExit=null → 落到 row 4 analyze 文案"点击深绿/深橙区域"。语义勉强通，但浪费了 CPD 的核心价值场景：**dock 路径产出的图恰是最需要 EMC 解读的图**。
**改法（二选一）**：(a) 增行——`hasAnalysis=true ∧ lastExit=null` → kind=`interpret`：「这张图已就绪——问我：这张热力图说明了什么？」把 dock 产出桥回 EMC 对话（闭合"dock 操作→EMC 解读"编排环，服务有用性环）；(b) 从特征向量删 hasAnalysis，承认 G1-G2 不用。建议 (a)，且实现成本仅一行真值表。

### M2（中优 · G1 实现注释）：hasVisibleEmotionLayer 谓词不判情绪性

§4.1 定义"visible 非 group 非 range"——**任意可见层**（含无情绪字段的普通导入 GeoJSON、纯边界层）都判 true。场景：用户导入一份无情绪字段的 POI 文件 → hasImport=true、hasVisibleEmotionLayer=true → 真值表跳过 layers 行直推 analyze"点击深绿/深橙区域"——但图面上没有任何情绪渲染，**演示链第一环（张力图面）是空的，引导文案在撒谎**。
**改法**：谓词收紧为 `visible ∧ 非group ∧ 非range ∧（paint 引用情绪色板 ∨ feature 含情绪/score 字段）`，G1 实现注释列出判据来源（emotionColors() 引用或 L2 字段词典）。若实现期发现判据不可靠，降级方案：layers 行与 analyze 行之间加"图层已载但未染情绪 → 提示选情绪图层/字段"中间态。

### L1（低优 · 文案修正）：U8 "dock" 不存在 + observer 复用表述失真

- 全前端无 `#dock` 元素（index.html 只有 `.tool-row` 按钮 + `#param-panel`:366）；heatmap/grid/buffer 三工具统一 openParamPanel（param-panel.js），**"dock/param-panel is-open"实为 param-panel 一家**。
- "复用 cpd-state.js:60-63 observer"表述失真：该 observer（实为 :58-63）监听 param-panel class 是为**自适应定位**（positionFloatingPanels），不向外部暴露 busy 态；且确定性引擎在 deriveGuidance 时**同步查** `document.getElementById('param-panel').classList.contains('is-open')` 即可，根本不需要 observer。
- **改法**：§十一 U8 措辞改"#param-panel.is-open 同步谓词（无需 observer）"；顺带决策左抽屉 `is-drawer-open` 是否也算 busy（用户正在抽屉里手动配图层时推 banner 同样是打扰）。

### L2（低优 · 实现期提示）：§6.4 `#ff9000` 硬编码出现在 plan 文本

G3"极性 top/bottom 区域橙色 #ff9000 呼吸闪烁"——地图侧高亮不在"EMC 颜色走 theme var"承重的字面范围，但与全站 token 化方向（及"同步高亮是否入 token"的既有问题）一致。**改法**：G3 实现时确认是否已有同步高亮 token；无则一并 token 化（如 `--geojson-color-sync-highlight`），plan 此处加注"色值以 token 为准"。

---

## 四、开放问题立场（§十一）

| # | k3 立场 |
|---|---|
| U1-U7 | 已收敛，维持（不再重开） |
| U8 | agree 确定性信号方向；按 L1 修正事实描述（param-panel 同步谓词，非"dock"+observer） |
| U9 | 维持观察——H1 修复后引导不再冻结，"再亮兜底"的紧迫性进一步下降，同意留观察 |
| U10 | agree 轻量闭合优先；S4 地图定位 CTA 已覆盖核心价值，地图浮层抛光期再评估 |

---

## 五、结论

- **agree v0.4 整体收敛**：架构方案（DI + 事件 + 真值表）正确，承重清白，演示表现力从文案层升维到交互闭环层。P0 测试铺底可立即启动，不阻塞。
- **G1 动手前必修 H1**（dispatch 改 settled 守卫 + 去重改单调递增 + 真值表标注）——两行代码级修复，但必须写进 §4.3 规范，否则引导引擎存在静默冻结路径。
- **M2 谓词收紧随 G1 实现注释落地**；**M1 建议采纳 (a) 方案（interpret 行）**，一行真值表换 dock→EMC 编排闭环，性价比高。
- 本轮 1 高 2 中 2 低，无 disagree。若 v0.5 修掉 H1/M2 并吸收 M1/L1，k3 预期可出末轮 A 级收敛意见。

---

## 附录 · 本轮新增证据索引

| 发现 | 关键证据 |
|---|---|
| H1 | harness.js:372/412（general 无 exit）；panel.js:1162（exit 保持 undefined）；panel.js:1177-1184（finally 段 settled/push 结构）；panel.js:1126/1182（_history 每轮 +2）；plan §4.3 守卫与"expectedTurnId+1"原文 |
| M1 | plan §4.1 特征向量定义 vs §4.2 真值表六列；heatmap-tool.js:610 / buffer-tool.js:86 / grid-tool.js（均 openParamPanel） |
| M2 | plan §4.1 hasVisibleEmotionLayer 定义原文 |
| L1 | index.html:366（#param-panel）；grep 全前端无 #dock；cpd-state.js:58-63（observer 用途=positionFloatingPanels） |
| L2 | plan §6.4 `#ff9000` 原文；tokens.css 无 sync-highlight token（前轮 CB 第七轴既有问题） |
