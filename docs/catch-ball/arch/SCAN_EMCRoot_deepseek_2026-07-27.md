# EMC 架构根因深度评估：「生成 1000m 方格网」案例全链路审计

> **评估方**：DeepSeek（第三方 LLM）  
> **评估日期**：2026-07-27  
> **评估触发**：用户在多轮修复后仍遇到三重矛盾——结论与成图矛盾、成图但 Overview 显示 0 条、耗时反而更长  
> **用户核心质疑**：「这是很简单、很直接的提问，只需要推理+计划好，直接调用固定工具+填入参数，很快出图，为什么要经过那么久？」  
> **CB 轮次**：CB-04（EMC 评估轨·第六轮 — 架构根因审计）  

---

## 〇、先直接回答用户的核心质疑

> 「这是很简单、很直接的提问，只需要推理+计划好后，直接调用固定工具+填入相应参数，能够很快的出图，为什么要经过那么久的审查等机制？」

**审查不是瓶颈——审查对这个请求本就是关闭的。**

`REVIEW_ENABLED` 默认 `false`（`harness.js:34`），单技能路径显式跳过审查（`harness.js:395`），gis_operation 路径也跳过审查（`harness.js:859`）。三重关闭。

**真正的瓶颈是两个本可省略的 LLM 调用**：

| 步骤 | 当前 | 最小可行 |
|------|:---:|:---:|
| diagnose（Flash LLM） | ✅ 必须 | ❌ 可省略——代码已能检测"网格"+"1000m" |
| 工具执行 | ✅ 0 LLM | ✅ 0 LLM（已是最优） |
| finalStep（Flash LLM） | ✅ 必须 | ❌ 可省略——模板结论即可 |
| review | ✅ 已跳过 | ✅ 已跳过 |
| **总 LLM 调用** | **2 次** | **0 次** |
| **总耗时** | **30-60s** | **2-3s** |

**「为什么审查很难通过？」——审查根本没在跑。出问题的是 finalStep 这个 LLM 调用本身：prompt 太大（MANIFESTO 全文 ~12KB + FINAL_TEMPLATE + industry_kb + grounding），LLM prefill 就需要 20-35s，然后生成的结论还可能与实际工具产出矛盾。**

---

## 一、三重矛盾的根因

### 1.1 结论说「无法生成 1000m 方格网…仅含 300m 热力图」——但地图上确实是 1000m 网格

**根因链（5 个因素共同导致）**：

#### ① observation 从未说明实际 cell_size

`tools.js:1153-1157` 中 density 工具的 observation：
```javascript
// mode='3d' 时产出：
"网格聚合(3D·固定色段)：{N} 点 → 已生成图层「{name}」（套用 Toolbox 固定色段，可切 2D/3D）"
```

**从未提及 `cell_size=1000`。** LLM 无法从 observation 中获知实际使用的网格分辨率。

#### ② observation 把网格单元称为「点」

`tools.js:1155`：`${_mode === 'terrain' ? '层等值面' : '点'}`

`mode='3d'` ≠ `'terrain'`，所以 observation 写「838 点」。但 838 是网格单元数，不是点数。LLM 看到「点」→ 理解为点密度分析 → 联想到默认 300m 半径的热力图。

#### ③ `radius: 300` 永远在 params 中

`stages.js:45` SKILL_DEFS.density 的 `optional_defaults`：`{ mode: '2d', radius: 300, weightField: 'emotion_intensity', cell_size: 600, polarity: 'overall' }`

`validateParams`（`stages.js:86-91`）合并默认值时，**无论 mode 是什么，`radius: 300` 都会被注入 params**。LLM 在 toolHistory 中看到 `params: {..., radius: 300, cell_size: 1000, ...}`，同时 observation 未确认用哪个，就默认了熟悉的「300m 半径」。

#### ④ prompt 四处灌输「radius 默认 300」

| 位置 | 内容 |
|------|------|
| `paradigm.py:303` | `radius?(2D热力带宽·默认300), cell_size?(3D网格边长·默认600)` |
| `prompts.py:86` | `"radius": 300(2D热力带宽), "cell_size": 600(3D网格边长)` |
| `stages.js:45` | `optional_defaults: { radius: 300, ... }` |
| `grid-tool.js:20` | `DEFAULTS = { cellSize: 400 }` |

**四处都说 radius=300。LLM 被过度锚定在这个数字上。**

#### ⑤ 单技能路径缺少「实际产出图层」注入

`harness.js:380`（单技能路径）：
```javascript
ctx.context = `【单技能路径·已执行 ${def.tool}】基于上述工具观察直接出结论...`;
```

对比 `harness.js:787`（ReAct 路径）：
```javascript
ctx.context = '【地图实际产出图层】' + formatRegistry() + '（严禁声称生成不在此列表的图层...）';
```

**单技能路径没有注入实际图层列表，也没有「严禁编造」的强约束。** LLM 更容易在缺少 grounding 的情况下产生与事实矛盾的结论。

### 1.2 Overview/Table 显示「L2·情绪·0 条」

**根因**：`focusLayer()` 把 EMC 图层解析为其父组（EmotionMap Copilot），而父组的 `fc` 是空的。

**链路**：

| 步骤 | 位置 | 行为 |
|:---:|------|------|
| 1 | `tools.js:270` | `_aiGroup()` 创建 EMC 组，`fc: { type: 'FeatureCollection', features: [] }` — **空 FC** |
| 2 | `tools.js:699` | `_adoptToolboxResult` 设置 `L.parentId = _aiGroup().id` |
| 3 | `state.js:797-801` | `focusLayer(layer)` → layer 有 parentId → 返回父组对象（空 FC） |
| 4 | `panel.js:612` | `tier1` 读 `layer.fc.features.length` → **0** |

设计注释（`tools.js:269`）承认了这个问题：「必传空 fc：组会被 focusLayer() 当作 Overview 焦点（tier1 读 group.fc.features），无 fc 则崩溃」。但只防止了崩溃，没解决「0 条」显示。

### 1.3 手动 Toolbox 生成顶掉 EMC 图层 + 眼睛开关跳转

**根因**：`enforceMutualExclusion`（`state.js:1036-1059`）把所有 `isToolAnalysisLayer` 的图层视为互斥——EMC 网格和手动网格都是 B 类分析图层，只有一个能可见。

| 操作 | 结果 |
|------|------|
| 手动生成网格 | EMC 网格被 `enforceMutualExclusion` 隐藏 |
| 点击 EMC 眼睛开关 | `_applyExclusiveOn` → 开 EMC 网格 → 关手动网格 → 地图跳到 EMC 网格 |
| 再点击 | 切换回来 |

**这不是 bug，这是设计**——分析图层互斥。但对用户而言体感是「图层跳来跳去」。

---

## 二、为什么"越修越慢"

### 2.1 答案超时从 45s → 60s 反直觉变慢

`api.js:33`：answer phase 超时从 45s 延长到 60s。**意图是减少超时，实际效果是让慢 LLM 响应多跑 15 秒才中断。**

### 2.2 finalStep prompt 从未瘦身

之前建议的「light prompt」（MANIFESTO 只留 §8+§9、移除 industry_kb）**未落地**。`build_final_prompt`（`prompts.py:164-172`）仍然是全文 MANIFESTO + FINAL_TEMPLATE + industry_kb appendix。

**当前 finalStep 的 system prompt 仍然是 20-44 KB，prefill 20-35 秒。**

### 2.3 工具的 observation 描述不准确引发假 revise

当 finalStep LLM 因 observation 误导产生矛盾结论后，`_verifyClaims`（`harness.js:218`）可能检测到声称图层与实际不符 → 触发 `_reviseOnce`（`harness.js:245`）→ 再多一次 LLM 调用。虽不常见但存在。

---

## 三、架构层面评估：EMC 对简单请求是否「过度设计」

### 3.1 对照用户的核心诉求

用户说：
> 「只需要推理+计划好，直接调用固定工具+填入参数，快速出图」

当前架构对这个请求做的事：

```
用户: "生成1000m方格网"
  → _quickIntent: 0 LLM ✅
  → diagnose LLM: 1 次 Flash ← ❌ 不必要（代码已能检测"网格"+"1000m"）
  → params fill + mode fix: 0 LLM ✅
  → 工具执行: 0 LLM ✅
  → finalStep LLM: 1 次 Flash ← ❌ 不必要（模板结论即可）
  → review: 已跳过 ✅
```

**2 次不必要的 LLM 调用，每次带 20-40 KB prompt。** 对于「直接调用固定工具+填入参数」这个需求来说，**确实过度设计了**。

### 3.2 「Smart Agent, Dumb Tool」在这里变形了

对照 `docs/copilot-architecture.md` 四铁律：

| 铁律 | 对「生成 1000m 方格网」的适用性 |
|------|------|
| 1. Tool 越 dumb 越好 | ✅ 工具执行足够 dumb——纯 JS，0 LLM |
| 2. Agent 聪明只在两端 | ⚠️ Smart 在 diagnose + finalStep，但**对这个请求，两端都不需要聪明**——参数可正则提取，结论可模板生成 |
| 3. 编排器确定性 | ✅ 编排正确 |
| 4. 计划-执行分离 | ⚠️ 分离了，但 plan 环节（diagnose LLM）对此请求是**杀鸡用牛刀** |

**问题不是铁律错了，而是铁律的应用缺少一个「简单请求快速通道」**——当 NL 中的参数和工具选择可以**确定性提取**时，应该跳过 LLM 直接执行。

### 3.3 用户建议评估：去掉 EMC 组

| 维度 | 评估 |
|------|------|
| **解决「0 条」** | ✅ 直接解决——focusLayer 不再解析到空 FC 的组 |
| **解决图层跳转** | ❌ 不解决——enforceMutualExclusion 仍然互斥 |
| **副作用** | 失去侧栏 EMC 分组、失去批量眼睛开关、EMC 和手动图层混在一起不可区分 |

**去掉 EMC 组是治标不治本。** 真正的修复应该是：

1. 修 `focusLayer`（`state.js:797`）：当父组 FC 为空时返回子图层自身
2. 修 `tier1` 或 EMC 组创建：让 EMC 组聚合子图层的 FC

**但用户的核心 frustration 不是 EMC 组，而是整个管线的延迟和矛盾结论。**

---

## 四、系统性问题总结

### 当前「生成 1000m 方格网」的完整问题清单

| # | 症状 | 根因 | 严重度 |
|---|------|------|:---:|
| 1 | 等 30-60s 才出结论 | 2 次不必要的 LLM 调用（diagnose + finalStep），每次带巨型 prompt | 🔴 |
| 2 | 结论说「无法生成」但图已生成 | observation 未确认 cell_size + 标注为"点" + radius:300 注入 params | 🔴 |
| 3 | Overview 显示「0 条」 | focusLayer 解析到空 FC 的 EMC 组 | 🟡 |
| 4 | 手动生成顶掉 EMC 图层 | enforceMutualExclusion 互斥设计 | 🟡 |
| 5 | 眼睛开关导致图层跳转 | 互斥 + selectLayer 联动 | 🟡 |
| 6 | 越修越慢 | 超时从 45s→60s，prompt 未瘦身 | 🟡 |

### 架构决策回顾

| 决策 | 对简单请求的影响 |
|------|------|
| 所有请求必走 diagnose LLM | 对参数可确定性提取的请求是浪费时间 |
| 所有结论必走 finalStep LLM | 对工具产出明确且简单的请求是浪费 |
| MANIFESTO 全文注入所有 LLM 调用 | 12KB 文本对「生成网格」结论毫无帮助 |
| EMC 组用空 FC 创建 | 直接导致 Overview 显示 0 条 |

---

## 五、优化方案

### 核心思路：「简单请求快速通道」——gis_operation 请求跳过 LLM

对参数可确定性提取的 B 类（gis_operation）请求，**用代码完成 diagnose + finalStep，零 LLM 调用**。

#### 设计

```
用户: "生成1000m方格网"
  → _quickIntent 扩展: 检测到 gis_operation 信号词 + 可提取参数
    → 直接构造 diagnose card（无 LLM）:
      { intent: 'gis_operation', template: 'density',
        params: { mode: '3d', cell_size: 1000, polarity: 'overall' } }
  → runTemplatePath（无 LLM）
    → TOOLS.density(params) — 出图（0 LLM）
  → 模板结论（无 LLM）:
      "## 1000m 方格网已生成\n{{show:T3·综合}}\n1000m 网格聚合，838 个单元。"
  → DONE. 总耗时: 2-3s.
```

**这不是去掉 Smart Agent——Smart Agent 的灵活性保留给真正的复杂请求（C 类情绪分析、multi 多步组合）。** 只是为「参数确定性可提取」的 B 类请求提供快速通道。

### 具体实施

#### Phase 1：消除矛盾结论（P0）

| # | 文件 | 改动 |
|---|------|------|
| 1 | `tools.js:1155` | observation 改「{N} 点」→「{N} 单元」，追加 `(cell_size={cell_size}m)` |
| 2 | `stages.js:45` | density SKILL_DEFS 移除 `radius` 默认值（mode='3d' 时无意义），或按 mode 条件化 |
| 3 | `harness.js:380` | 单技能路径注入 `formatRegistry()`（与 ReAct 路径对齐） |
| 4 | `tools.js:1153` | observation 从 `{featureCount} 点` 改为 `{featureCount} 网格单元（{cellSize}m）` |

#### Phase 2：简单请求快速通道（P0·架构优化）

| # | 文件 | 改动 |
|---|------|------|
| 5 | `harness.js:16` | `_quickIntent` 扩展：对 gis_operation 信号词 + 参数可提取的请求，直接构造 diagnose card |
| 6 | `harness.js:383` | 对 gis_operation + 简单工具产出 → 模板结论（跳过 finalStep LLM） |
| 7 | `harness.js` 新增 | `_templateConclusion(diagnose, toolResult)` 函数——基于工具产出生成模板结论 |

#### Phase 3：修复「0 条」+ 图层跳转（P1）

| # | 文件 | 改动 |
|---|------|------|
| 8 | `state.js:797` | `focusLayer`：当父组 fc 为空时返回子图层自身 |
| 9 | `map.js:362,395` | `parentId` 传递（上一轮已识别） |

#### Phase 4：finalStep prompt 瘦身（P1·兜底）

| # | 文件 | 改动 |
|---|------|------|
| 10 | `prompts.py:164` | `build_final_prompt` 对 `light=True` 时只用 MANIFESTO §8+§9，不加 industry_kb |
| 11 | `api.js:33` | answer 超时回退到 45s（在 prompt 瘦身后不再需要 60s） |

---

## 六、关于 EMC 组的建议

用户建议「去掉 EMC 组，让图层回归通用组」。我的评估：

**我不建议完全去掉 EMC 组**——它在侧栏提供了有价值的分组（用户一眼看出哪些图层是 EMC 生成的），且不影响核心功能。

**但我建议在以下场景中弱化 EMC 组的存在**：
- `focusLayer` 不再把 EMC 子图层解析为其父组（用 Phase 3 修复）
- 考虑给 EMC 组一个**实时聚合的 FC**（`groupFC` 函数已存在，`state.js:721`），这样 Overview 就能显示正确的条数

如果用户坚持去掉 EMC 组，改动也很小：删除 `tools.js:698-702` 的 `parentId` 赋值即可。但我认为先试 Phase 3 的修复更稳妥。

---

## 七、总结

**用户的直觉是对的。**「生成 1000m 方格网」这类请求——参数可确定性提取、工具选择唯一、产出明确——完全不需要 2 次 LLM 调用。当前架构对这类请求是**过度设计**。

**核心矛盾**：Smart Agent / Dumb Tool 架构本身没问题，但它目前**对简单请求和复杂请求一视同仁**——都走完整的 diagnose LLM → tool → finalStep LLM 管线。需要一个「简单请求快速通道」来区分。

**最直接的改善**（Phase 1+2，1-2 个会话）：
1. 修 observation 准确描述工具产出 → 消除矛盾结论
2. 对 gis_operation 简单请求 → 跳过 diagnose LLM + 模板结论 → **耗时从 30-60s 降到 2-3s**

这才是用户真正要的：「直接调用固定工具+填入参数，快速出图」。

---

*审计覆盖：`frontend/js/ai_qa/harness.js`(全量)、`frontend/js/ai_qa/tools.js`(density 全量)、`frontend/js/ai_qa/stages.js`(SKILL_DEFS/normalizeParams 全量)、`ai_qa/prompts.py`(build_final_prompt/DIAGNOSE_TEMPLATE/FINAL_TEMPLATE 全量)、`ai_qa/paradigm.py`(B_TRACK_PARADIGM/select_template 全量)、`frontend/js/state.js`(focusLayer/enforceMutualExclusion/categoryOf 全量)、`frontend/js/panel.js`(tier1/setOverview 全量)、`frontend/js/grid-tool.js`(generateGridForAI 全量)*
