# Toolbox 统一手册 v2.1 → v2.2 修订响应表

> 响应人：K3（手册作者）｜ 2026-07-25 ｜ 对象：主线程评审报告 `emc-toolbox-unified-review-2026-07-25.md`
> 落版：`.codebuddy/plans/toolbox-unified-toolset-execution.md` v2.2（引用行号 = v2.2 当前值）
> 方法：每条评审意见先对代码实测复核，再定 接受 / 部分接受 / 反驳；修正与反驳均附 file:line 硬证据

---

## 〇、总评回应

接受「中风险 → 修订 6 条后低风险」的评定框架。评审指出的 1 个真 bug（D-④）+ 1 个体验退化（C-②/建议 1）+ 1 处表述误导（D-②）经逐条对代码复核**全部成立**，已落版 v2.2。另发现**评审修订 2 的判据细节与代码事实冲突**（distance 不能作 cover/emotion 判据），已按实测修正为 color 判据并登记（见 §二修订 2 + §三）。

---

## 一、决策变更建议 1（focusOnlyResults 保留）— **接受**（K3 技术判断，待用户最终确认）

v2.1 §3.3③「废弃 focusOnlyResults，两路径统一向 enforceMutualExclusion 看齐」是我（K3）的错误决策，推翻。硬证据：

1. **tools.js:407-410**（focusOnlyResults 头注）：「AI 结果是 R-group（enforceMutualExclusion 不动它），故不走互斥，直关」——设计层面互斥就管不到 AI 结果组，「统一向互斥看齐」在现有机制下不成立。评审 C-② 语义区分正确。
2. **tools.js:515**：focusOnlyResults 在 addResultLayer 内对**每个** EMC 产物调用；废弃 = 全部 EMC 工具丢沉浸聚焦。评审证据 2 成立。
3. **补强证据（评审未提及）**：组 A 已委托的 density（tools.js:1284-1319）走 `_registerToolboxLayer`（:817-826），**现状即未调 focusOnlyResults**——「委托即丢聚焦」已有现存实例，证明该风险是实证的而非理论推演。（density 此行为差异系组 A 遗留；v2.2 步 7 明确不迁移 density、另案处理，手册 :317。）
4. v2.1 自相矛盾属实：§3.2 说「留 tools.js」、§3.3③ 说「废弃」。

**落版位置**：§0 一句话任务 :27（聚焦行为差异化表述）｜ §2 C4 :74（_adoptToolboxResult 组成）｜ §3.2 :106（去留协调）｜ §3.3③ :135-140（改写）｜ §6 步 7 模板 :310-311 + DoD :319。

**回退指引（若用户否决）**：§3.3③（:135-140）改回 v2.1 文案；§2 C4（:74）与步 7 模板（:310-311）删 focusOnlyResults；§0 句尾表述（:27）保留——该表述独立成立，不依赖建议 1。

---

## 二、修订清单 1-7 逐条响应

| # | 评审意见 | 响应 | 理由 / 证据 | 落版位置（v2.2） |
|---|----------|------|-------------|------------------|
| 1 | §3.3③ + §3.2 配合建议 1（focusOnlyResults 去留协调） | **接受** | 随建议 1；§3.2 行说明与 §3.3③ 已协调一致，矛盾消除 | :106, :135-140 |
| 2 | §4.3 buffer 编辑兼容推断：新产物显式 kind + 「distance 判据」 | **部分接受（事实冲突已修正）** | 主方向「新产物显式 kind」接受——D-④ 真 bug 复核成立：tools.js:1205 `_ui` 无 kind，:1206-1207 `sourceLayer` 条件性写入，v2.1「有 sourceLayer→cover」确会误判。**但「distance 判据」与代码事实冲突**：cover 路径 `_ui` 同样必含 distance（buffer-tool.js:121 `distance: p.distance`），按评审原文实现会把**全部存量 cover buffer 误判为 emotion**——与 D-④ 同型的反向事故。实测正确判据 = **`color`**：cover 必写（buffer-tool.js:121-122，readParams :90-98 默认 `#4FC3F7`），emotion 永不写（tools.js:1205 字段集无 color）。已修正落版并在手册 :197 标注冲突来源 | :197（§4.3）；协同 :267-268（§5.7 显式 kind）、:282（步 2 DoD）、:318（步 7 buffer 委托）、:323（步 8 存量回填验证） |
| 3 | §0「产出完全一致」→「图层产出一致」 | **接受** | D-② 成立：手动路径产物无 registry/$n（§3.3② 分工本如此设计），「完全一致」易误导执行者 | :27 |
| 4 | §7 补 paradigm catalog 同步·或交组 D SOP 批次 | **部分接受（解法修正为「论证无需改」）** | 张力真实（红线与实现演化的关系应写明），但「catalog 需同步」前提不成立：`kind` 是模块内部 API（§5.7 `generateBufferForAI`），EMC 委托层固定 `kind:'emotion'`，LLM 契约面（C3 参数/schema）零变化；catalog :220-226 的 emotion 描述与 LLM 实际可用行为一致——**无漂移可同步**。落版为「无需同步的论证 + 若未来向 LLM 暴露 cover 模式则届时同步并需用户拍板」 | :331 |
| 5 | §1 + §5.1 补循环依赖既有模式说明 + TDZ 禁令 | **接受** | D-① 复核成立：grid-tool.js:12 / heatmap-tool.js:12 / buffer-tool.js:7 均 import sidebar；renderLayerList（sidebar.js:343）/ refreshLegend（:163）均 `export function` 提升声明，ES module 循环下运行时调用 TDZ 安全 | :61, :223 |
| 6 | 步 8 加「12 工具 observation 快照 diff」硬 gate | **接受** | F / E-③ 成立：「逐字比对」无方法则不可执行。落版为三件套：步 7 前置基线（`tests/reports/toolbox-obs-baseline.json`·固定入参·data 剔 layerId/时间戳等易变字段）→ 逐工具 DoD diff 全等 → 步 8 硬 gate | :302, :319, :322 |
| 7（可选） | 步 5 并入步 7；步 3/4 并行批 | **部分接受** | 效率建议合理（nearest/hotspot 无 UI、步 7 顺序恰以其为首两个；四模块互不依赖），但保留 8 步编号（D5 字面「8 步」+ 避免锚点重排 churn）：落版为标题批注，DoD 不变 | :284, :288, :292 |

---

## 三、事实冲突登记（按任务纪律「不硬落版」）

| 冲突项 | 评审原文 | 实测（file:line） | 处理 |
|--------|----------|-------------------|------|
| 修订 2 判据字段 | 「有 `distance` 字段且无 `kind` → emotion」（distance 是 emotion 路径必有·cover 路径无） | cover 路径 `_ui` **必含 distance**（buffer-tool.js:121）；两路径的区别字段是 `color`（cover 必有 :121-122；emotion 必无 tools.js:1205） | 未硬落版评审原文；修正为 color 判据落版 :197，并在此登记 |

---

## 四、边界守约确认

- D1-D6 未动（§0 :29-38 原样保留）；建议 1 为唯一决策变更，手册顶部标注「待用户最终确认」（:4）。
- 后端零改动 / 不改 SKILL_DEFS（TEMPLATE_REGISTRY）/ 不改 harness orchestrate / 不改 ChatRequest schema——本次仅改手册文本（v2.1 → v2.2），未动任何代码文件。
- 修订 4 落版为「无需改 paradigm」的论证，未对 paradigm.py 提出任何改动；GEO_TOOL_CATALOG 文案同步非红线的评审判断（报告 §五）与本次落版不冲突。

## 五、遗留另案（不属本手册范围·登记）

1. **density 委托产物无沉浸聚焦**（组 A 遗留：tools.js:1284-1319 未调 focusOnlyResults）——v2.2 步 7 明确不迁移 density（:317），如需统一另案评审。
2. **main.js `_contentSig` 与 tools.js `_toolContentSig` 同语义重复**（tools.js:421-423 注释自标「待统一」）——本次不动 main.js（:107）。
