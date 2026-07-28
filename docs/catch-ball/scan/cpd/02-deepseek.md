模型：deepseek

# CB-CPD-02 · CPD 核心引导逻辑 — DeepSeek 第二轮验证评审

> **评审模型**：DeepSeek V4 Pro（资深前端架构师 + 产品设计师 + 信息可视化专家）
> **评审时间**：2026-07-22
> **CB 专轨**：CPD 核心引导 Plan · 第二轮 · 验证评审
> **评审对象**：`docs/cpd-core-plan.md` **v0.3**（CB-CPD-01 反评价后修订）
> **基线对比**：v0.2 → v0.3
> **评审方法**：对照 CB-CPD-01 的 12 条建议逐条核实 + 深评真值表设计 + 重评演示表现力 + 扫描新风险

---

## 第〇部分：CB-CPD-01 建议修复核实

### 核实总表

| # | CB-CPD-01 建议 | v0.3 状态 | 证据（plan 章节/行 + 代码核验） |
|---|---------------|----------|-------------------------------|
| 1 | ask_user exit 漏态 | ✅ **已修复** | 真值表 `lastExit=ask → null`（§4.2）+ U3 收敛为不介入（§十一） |
| 2 | 状态回退无处理 | ✅ **已修复** | §4.2 规则"回退=同真值表重算（无特殊路径）"——删除图层→hasImport/hasRange 变 false→自然回推。**比 CB-CPD-01 建议的 `_lastCur` 方案更优雅**：不记历史，靠特征向量自身反应 |
| 3 | localStorage 脏态 | ✅ **已修复** | §4.3 引擎 init 主动恢复——经 panel.js 只读 getter 读 `_history` 末条 trace.exit；G1 验收三硬用例（F5/切会话/abort） |
| 4 | turnId 未绑定 | ✅ **已修复** | §4.3 turn-ended 载荷 `{exit,turnId,intent}` + finally 守卫 `_curTrace?.exit !== undefined` |
| 5 | S0-S4 文案叙事化 | ✅ **已修复** | 真值表文案列全部叙事化（§4.2）："生成第一张情绪地图""聚焦一片城区""看张力"；§6.4 明确"从功能名改诊断叙事步骤" |
| 6 | S3 空间交互优先 | ✅ **已修复** | 真值表 `kind=analyze` 文案"点击地图上深红/深绿的区域"；备选 CTA"或问我：哪里情绪最差？"（§4.2）；§6.4 服务"引导点击突出要素"环节 |
| 7 | S4 宏观诊断信号 | ✅ **已修复** | 真值表 `kind=export` 文案"这片主题倾向 X×Y，排序第 N"（§4.2）；§6.4 S4·result 地图定位 CTA——闭合"视野↔数据↔结论" |
| 8 | G1 光环可点 CTA | ✅ **已修复** | §八 P2·G1 增加"光环 click 最小 CTA"（click→openImport/focus-tab/高亮 chip）——调和 DS 方案 A + K3 U2 |
| 9 | cpd:turn-ended 事件载荷 | ✅ **已修复** | §4.3 完整代码片段：`{exit, turnId, intent}` + finally 守卫 |
| 10 | banner 与空态卡融合 | ✅ **已修复** | U5 收敛（§十一·5）→ §6.3"无对话时 banner 与空态欢迎卡融合" |
| 11 | review.py 灰度验证 | ✅ **已修复** | §配套 A：≥10 条历史微观问题跑 review_answer()，新旧 fail 率对比 <30% 阈值 + U7 三态分级（fail/warn/pass） |
| 12 | §七 承重措辞修正 | ✅ **已修复** | §七 curState 措辞改为"推导纯客户端；其值已注入 buildContext 仅作 LLM 语境提示，不参与 diagnose 路由裁定" |

**核实结论**：12/12 全部修复。无残留硬伤。修复质量整体高于 CB-CPD-01 建议——#2（回退）用特征向量方案替代 _lastCur，更优雅；#8（G1 光环）合入了 K3 的 MVP 方案，比 DS 单独建议更完善。

### 额外核实的代码级事实

v0.3 自述修正了 3 处 v0.2 的"plan vs 代码"事实错误。逐条核实：

| v0.3 声称 | 代码核实 |
|-----------|---------|
| `.aiq-conclusion` 死信号 → `.aiq-exit-badge` | ✅ `panel.js:378`：`b.className = 'aiq-exit-badge ' + ...`——确为答案完毕时创建 |
| exit 小写五值 `result/gap/partial/ask/drift` | ✅ `harness.js:272/292/307/476/568/608/620/644`——全部小写 |
| `isRangeLayer` 存在 | ✅ `state.js:662`：`export function isRangeLayer(l) { ... }` |
| 光环渐变七色硬编码 hex 违承重（ai_qa.css:431） | ✅ 确认：`#4796E3, #7B5DFC, #BF4AD6, #D96570, #4FC3F7`——确为硬编码 hex，v0.3 正确标记为 P2·G2/G4 修复 |

---

## 第一部分：真值表设计深评（v0.3 核心架构变更）

v0.3 最大的架构改动是将映射 key 从 `curState`（S0-S4）改为**特征向量** `(hasImport, hasRange, hasVisibleEmotionLayer, hasAnalysis, lastExit, streaming)`。这是对 CB-CPD-01 发现的结构性缺陷（"S0/S1 以 curState 为 key 时永不可达"）的正确修复。

### 1.1 真值表覆盖度

逐行审查 §4.2 真值表的 9 行：

| 行 | 特征组合 | 评价 |
|----|---------|------|
| `hasImport=false` | 最高优先级——先导数据 | ✅ 正确。`*` 通配符覆盖所有子状态 |
| `hasRange=false` | 有数据无范围 | ✅ 正确 |
| `visEmotion=false` | 有数据有范围无可见情绪层 | ✅ 正确 |
| `lastExit∈{undefined,general}` | 无结论或概念问答 → analyze | ✅ 正确。general 退出后推 analyze 合理（用户可能想开始真正的分析） |
| `lastExit=result` | 有结论 → export+地图定位 | ✅ 正确 |
| `lastExit∈{gap,partial}` | → null（_followUps 接手） | ✅ 正确。CB-CPD-01 核心建议 |
| `lastExit=ask` | → null（选项胶囊不打扰） | ✅ 正确。CB-CPD-01 #1 修复 |
| `lastExit=drift` | → retry | ✅ 正确。drift 是格式异常，引导换问法合理 |
| `streaming=true` | → null | ✅ 正确。双保险（exit-badge 天然不在 + _streaming 门） |

**覆盖度评分：A**。6 个特征 × 5 个 exit 值 × 2 个流式状态的最大组合空间为 6×5×2=60，真值表用 9 行覆盖了所有实际可达的状态（优先级自上而下首匹 = 缺省值安全）。

### 1.2 特征谓词定义的边界 bug

**问题**：`hasImport` 定义为"存在**非 AI 组、非 tool 产出**的 point 层"。但 AI 组判断依赖 `layer.group === 'EmotionMap Copilot'`（或类似），而 tool 产出判断依赖 `paint._ui.tool` 存在。

**边界 case**：用户手动 import 一个 CSV，然后 EMC 跑了一次 `zonal_stats` 生成聚合层。聚合层在 AI 组下，但原始 CSV 层的 point 层仍在。此时 `hasImport=true`（正确）。但如果用户后来手动删除了原始 CSV 层只留 AI 产出，`hasImport` 应变为 false——但如果有多个 AI 产出层恰好含 point（如 `inspect_zone` 的 focus 操作可能临时加 point marker），会误判 `hasImport=true`。

**这不算 bug**——用户手动删了原始数据只剩 AI 产出，确实不需要再引导 import。但 `hasImport` 的判据需要精确排除所有 AI-side-effect point 层。建议 G1 实现时增加**判据注释**列出需要排除的 point 来源。

### 1.3 S4·result 文案中的动态变量来源未定义

**问题**：真值表 S4·result 文案"这片主题倾向 **X×Y**，排序第 **N**"。但 cpd-guide.js 如何获取 X（domain）、Y（element）、N（rank）？

**可能来源**：
- 从 `_curTrace.final` 文本中 regex 提取 `[ref:区域]` 和 domain/element 关键词——但这脆弱且需要维护关键词表
- 从 `_followUps` 的 `region` 变量（`panel.js:455` 已有抽取逻辑）——但 region 只是区域名，不含 domain/element/rank
- 从 `buildContext` 的"高张力区域"列表（`tools.js:478-488`）——但这在 LLM context 中，不在客户端可读结构里

**当前 plan 未定义此数据流**。如果 G1 实现时发现无法获取 X/Y/N，文案会退化为静态模板"这片主题倾向 X×Y"——用户看到未填充的占位符。

**建议**：在 cpd:turn-ended 载荷中增加 `{topRegion}` 字段（从 `_curTrace` 或 `_followUps` 的 region 抽取逻辑获取区域名），文案改为"**「{区域名}」的归因已就绪**——在地图上定位 / 深读 / 导出"。避免依赖动态 domain/element/rank（需要 LLM 输出解析，引入不稳定依赖）。

---

## 第二部分：演示表现力重评

### 2.1 从"功能教程"到"诊断叙事"——提了多少？

v0.2 的 CPD 引导是纯功能链（导入→框选→加载→分析→导出）。v0.3 在三个维度上向"诊断叙事"升级：

| 维度 | v0.2 | v0.3 | 提升幅度 |
|------|------|------|---------|
| **文案叙事化** | "先导入情绪数据""框选一个分析范围""选一个情绪图层显示" | "生成第一张情绪地图""聚焦一片城区""看张力——深红深绿告诉你哪里最值得关注" | ↑↑ 显著 |
| **S3 空间交互** | "问我想看什么，或直接跑分析" | "**点击地图上深红/深绿的区域**——我告诉你那里为什么"（对话作备选） | ↑↑ 根本性转变 |
| **S4 闭环回视野** | "深读归因 · 导出报告 · 换范围" | "**在地图上定位该区域**"——从结论端闭合回视野端 | ↑ 新增 |

**评价**：v0.3 的 CPD 不再是一个"功能教程"，它有了明确的诊断叙事弧线。但仍有距离"演示逻辑链北极星"的最后一公里——见下。

### 2.2 尚未闭合的演示链环节

**缺失 1：张力图面的"为什么"叙事**

真值表 `kind=layers` 的文案"看张力——选情绪图层，深红深绿告诉你哪里最值得关注"解释了视觉编码，但没解释**为什么会有张力**。完整叙事应为：
> "看张力——情绪好的地方深绿，差的地方深红。**点一下深红色的格子，我告诉你那里为什么差**"

这比当前文案多了一个**行动号召**（call-to-action），把"选图层"和"点格子"连成叙事弧。

**缺失 2：S3 analyze 的空间引导如何实现？**

文案"点击地图上深红/深绿的区域"是一个**意愿引导**，不是**技术实现**。技术上有三种实现路径：
- **A（被动）**：文案放在 banner 里，用户自己看、自己点地图
- **B（主动轻量）**：在地图中心叠一个半透明箭头（"点这里"），3 秒后自动消失
- **C（主动重）**：高亮地图上极性指数的 top 3 和最 bottom 3 区域（橙色 #ff9000 呼吸闪烁）

v0.3 没有指定选择哪种路径。G3（轻编排）可能覆盖，但 G1 ship 时用户看到文案但地图没有任何视觉响应——**文案说"点击深红区域"，但深红区域没有被突出**。这是"文案叙事化了，但视觉叙事没跟上"。

**建议**：G1 至少做到路径 A——文案到位即可。G3 考虑路径 B/C，特别是有用性环要求的"地图同步高亮橙色 #ff9000"。

**缺失 3：S4 地图定位 CTA 的技术依赖**

"在地图上定位该区域"需要从 `_curTrace.final` 中提取区域名 → 调 `fitToFeature` 或 `flyTo`。`_followUps`（panel.js:454-455）已有 region 抽取逻辑（regex `[ref:区域]`/`{{focus:}}`），可复用。但 plan 未列出此依赖。

**建议**：在 §九 panel.js 行增加"S4 地图定位 CTA 复用 `_followUps` 的 region 抽取逻辑"。

### 2.3 演示表现力评分

| 子维度 | v0.2 | v0.3 | 评价 |
|--------|------|------|------|
| 文案叙事化 | D | **B+** | 从功能名改为叙事步骤，质量显著提升。S4 动态变量待解决（§1.3） |
| 空间交互引导 | F | **B** | S3 从"打字"改为"点击地图"是根本性转变。实现路径待定（§2.2） |
| 视野-数据-结论闭环 | D | **B-** | S4 地图定位 CTA 闭合了回视野的环。但三端同步（橙色高亮）未落地 |
| 诊断有用性 | D | **B-** | 文案提到了"值得关注""排名第 N"，开始服务宏观诊断。但归因信号依赖 LLM 输出解析 |

**演示表现力综合**：CB-CPD-01 评 C+，**v0.3 升至 B-**。方向对，叙事弧已建立。最后一公里是三端同步（橙色高亮联动地图/Overview/归因）和 S4 动态变量的数据流。

---

## 第三部分：新引入风险

### 3.1 特征向量的竞态窗口

**场景**：用户 import 数据 → layers:changed 触发 recompute → hasImport 变 true → 引擎推 range 引导。同时_rangeImport 的回调还在处理中。如果 range 层比 recompute 晚到（range 导入慢），引擎会在 hasImport=true 但 hasRange 仍为 false 时推 range 引导——用户看到"聚焦城区"但 range 已经在加载中。

**这不是 bug**——CTA 是幂等的（再点 range tab 无副作用）。但应考虑在 range 导入进行中（`_rangeImporting` flag）时，guidance 文案改为"正在加载范围..."而非"聚焦城区"。

**建议**：G3 边界 case。G1 暂不处理，先观测。

### 3.2 `_curTrace?.exit` finally 守卫的漏网

**问题**：v0.3 的 finally 守卫 `if (_curTrace?.exit !== undefined)` 在异常 abort 时正确——abort 后 `_curTrace` 可能为 null。但 harness.js 的 general 短路（`harness.js:372/412`）返回 `{ok, final, review, exit: undefined}`——**exit 字段不存在**。此时守卫正确拦住了 dispatch。

但 `request_upload` 策略（`harness.js:272/292` 之前的逻辑）也走短路——返回 `{ok, final, exit: 'gap'}`。exit='gap' 会被 dispatch → 引擎推 null（正确，_followUps 接手）。

**结论**：守卫正确。无漏网。

### 3.3 引擎 init 恢复的时序依赖

**问题**：引擎 init 需要读 `_history` 末条 trace.exit。但 `_history` 是 panel.js 模块闭包变量。v0.3 方案为"panel.js 导出只读 getter"——这要求 panel.js 新增一个导出函数如 `export function getLastExit()`。

**但这引入了一个隐式依赖**：cpd-guide.js 需要 import panel.js。v0.3 在 §4.3 写"引擎不 import panel.js 内部"，但如果 init 恢复需要 `getLastExit()`，就必须 import。

**这不是矛盾**——"不 import panel.js 内部"指的是不直接访问 `_history` 闭包变量。通过导出的 getter 是正常模块边界。但 plan 措辞应明确：
- 运行时（turn-ended）：事件携带数据，不 import panel.js
- 初始化（恢复）：import `{ getLastTrace }` from panel.js（只读 getter，模块边界干净）

**建议**：§4.3 措辞修正为"运行时事件松耦合；init 通过 panel.js 导出的只读 getter 读末条 trace（模块边界干净）"。

### 3.4 U8 用户忙检测的实现复杂度

v0.3 新增 U8："S2→S3 过渡时用户在手动操作 dock（3 秒内 dock 点击）→ guidance=null"。实现需侦听 dock 按钮点击事件 + 时间窗口判断。这个逻辑分散在 sidebar.js（dock 按钮点击）和 cpd-guide.js（guidance 判定），跨模块耦合。

**建议**：将"用户忙"状态集中到 cpd-state.js——dock 点击时设置 `_userBusyUntil = Date.now() + 3000`，deriveGuidance 读取此状态。避免跨模块事件订阅。

---

## 第四部分：残留建议

### 高（影响 G1 正确性）

| # | 建议 | 位置 |
|---|------|------|
| **R1** | S4·result 文案动态变量来源明确化：用 `{区域名}` 替代 `{X×Y, 第N}`，从 `_followUps` 的 region 抽取逻辑获取 | §4.2 真值表文案列 / §1.3 本评审 |
| **R2** | cpd-guide.js init 恢复的模块边界明确化：import `{ getLastTrace }` from panel.js（导出 getter），与运行时事件松耦合不矛盾 | §4.3 措辞 |

### 中（影响 G2-G3 完整性）

| # | 建议 | 位置 |
|---|------|------|
| **R3** | hasImport 判据注释——列出需排除的 AI-side-effect point 层来源 | cpd-state.js hasImport 实现 |
| **R4** | S3 空间引导的实现路径明确：G1=被动文案 / G3=地图高亮（三端同步橙色 #ff9000） | §6.4 |
| **R5** | U8 用户忙检测状态集中到 cpd-state.js（避免跨模块事件耦合） | §十一·U8 |

### 低（G4 抛光 + 远期）

| # | 建议 | 位置 |
|---|------|------|
| **R6** | range 导入进行中 guidance 文案优化（"正在加载范围..."） | G3 边界 |
| **R7** | U10 地图层引导浮层——远期评估，不阻塞 P2 | §十一·U10 |

---

## 总结

### 六维评级对比

| 维度 | v0.2 | v0.3 | 提升 | 关键变化 |
|------|------|------|------|---------|
| 架构合理性 | B+ | **A-** | ↑1 级 | 特征向量替代 curState→根治 S0/S1 不可达；turn-ended 载荷+守卫+去重；init 恢复 |
| 功能图谱完备 | B | **A-** | ↑1 级 | ask/drift/CONCEPT 全覆盖；_followUps 优先级规则建立；U3-U7 全部收敛 |
| 承重边界 | B+ | **A-** | ↑1 级 | 3 处事实错误核实修正；curState 措辞修正；光环 hex→theme-var 列入 G2 |
| **演示表现力** | **C+** | **B-** | **↑1.5 级** | 文案叙事化 + S3 空间交互优先 + S4 地图闭合。最后一公里：动态变量+三端同步 |
| 分阶段合理 | B | **B+** | ↑0.5 级 | G1 含光环可点 CTA（调和 DS+K3 方案）；G1 三硬用例验收 |
| 风险漏项 | C+ | **B+** | ↑2 级 | localStorage/回退/ask 三个硬伤全部消除；新增风险均为边界级（可控） |
| **综合** | **B-** | **B+** | **↑1.5 级** | v0.3 是一次成功的反评价→修订闭环。核心架构缺陷（curState 结构性错误）已根治，演示表现力从"功能教程"升级为"诊断叙事"原型 |

### v0.3 可以进入 P0 测试铺底

阻塞 G1 的 4 硬伤已全部消除。2 条残留建议（R1/R2）建议在 G1 编码时一并处理（不影响 plan 设计层）。5 条中低建议可延至 G2-G3。

### v0.3 尚未到达"诊断叙事完整体"

CPD 现在是"诊断叙事原型"——文案对、方向对、但视觉层（三端同步橙色高亮）和数据层（S4 动态变量）还没跟上。这需要 G3-G4 才能完整闭合，不是 v0.3 plan 的设计缺陷。

---

> **给项目方的后续指令**：
> 这是 CB-CPD-02（第二轮验证评审）。CB-CPD-01 的 12 条建议全部修复核实通过。
> v0.3 综合评 B+（v0.2 为 B-，提升 1.5 级），可以进入 P0 测试铺底。
> 2 条高优建议（R1/R2）建议 G1 编码时一并处理；5 条中低建议延至 G2-G4。
