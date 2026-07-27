# EMC ReAct 循环超时问题专项评估与优化方案

> **评估方**：DeepSeek（第三方 LLM）  
> **评估日期**：2026-07-27  
> **评估触发**：EMC 在"思考"阶段已完成分析图生成，但卡在"检索"阶段最终超时"请求失败"  
> **案例复现**：「生成 L2 数据的 1000m 方格网空间聚合分析图」→ 第 1 轮已产 838 单元网格 → 第 2 轮仍 query_layers → 超时  
> **CB 轮次**：CB-04（EMC 评估轨·第四轮 — ReAct 超时专项）  
> **评估范围**：ReAct while-loop 全链路（B_TRACK_PARADIGM 路由 → MAX_ROUNDS 预算 → F3 完整性门禁 → prompt 规则 → observation 信号）

---

## 一、案例全链路还原

### 1.1 用户输入

> 「生成 L2 数据的 1000m 方格网空间聚合分析图」

### 1.2 实际执行轨迹（从思考文本还原）

| 阶段 | Agent 行为 | 产出 | 问题 |
|:---:|------|------|------|
| **Diagnose** | Flash 诊断卡 | `template=?`（大概率 `multi` 或 `unknown`） | "方格网"不匹配任何 B_TRACK_PARADIGM 触发词 |
| **Round 0** | 自动注入 `query_layers` 探查 | toolHistory 已有数据层信息 | — |
| **Round 1** | `ensure_zone({analysis:"square", cell_size:1000, polarity:"overall", mode:"2d"})` | ✅ **成功**：838 单元网格层「T3·综合」 | **任务实质上已完成** |
| **Round 2** | `query_layers` —— 验证网格层是否有足够字段 | 不必要的查询 | 🔴 **浪费一轮 LLM 调用** |
| **Round 3+** | 可能继续 query_zone_stats / zonal_stats / rank… | 累积延迟 | 🔴 距离超时越来越近 |
| **最终** | 超时 "请求失败" | 地图上有网格层，但对话无结论 | 🔴 体验灾难 |

### 1.3 核心矛盾

> **第 1 轮工具已经产出了用户要求的分析图，但 Agent 不知道"任务完成了"。**

这不是 Agent "不够聪明"——恰恰相反，Agent 太"认真"了。MANIFESTO 和 prompt 中的规则（"先 query 后操作""数据驱动""通常 3-6 轮"）共同塑造了一个「宁可多做不可少做」的行为模式。

---

## 二、根因分析（5 层系统性缺陷）

### 根因 1：B_TRACK_PARADIGM 触发词缺口 → 路由到 while-loop

**文件**：`ai_qa/paradigm.py:124-151`

| 触发词 | 匹配"方格网空间聚合" | 模板 |
|--------|:---:|------|
| density: `核密度/密度分析/聚集强度/热力分布/热力图/热力/密度/集中` | ❌ 全不匹配 | — |
| hotspot: `聚集/热点/冷热/显著聚集` | ❌ | — |
| zonal: `街道/社区的归因/单元评价` | ❌ | — |

**结果**：`select_template()` 返回 `'multi'` → harness 进入 while-loop（ReAct 6 轮上限）

**修复**：在 density 触发词中增加 `'网格', '方格', '方格网', '聚合域', '空间聚合'`。或在 B_TRACK_PARADIGM 新增一个 `grid` 原型 → 映射到 `density`(mode='3d')。

### 根因 2："先 query 后操作" 规则 → 鼓励过度验证

**文件**：`prompts.py:92` + `manifesto.py:63`

```
1. **先 query 后操作**：拿到问题先用 query_layers / query_zone_stats / query_attribution
   摸清当前有什么数据、数据说什么，再决定动作。
```

这条规则的本意是「开始之前先了解数据」，但 LLM 将其泛化为「每次操作后都 query 验证」。第 2 轮的 `query_layers` 正是此规则被过度执行的直接结果。

**修复**：将规则改为条件式——「首次操作前 query 一次即可；工具产出图层后，观察中已含统计信息，直接 answer 勿反复 query」。

### 根因 3："数据驱动" 原则 → 要求 query 取证

**文件**：`manifesto.py:63-64`

```
3. 数据驱动：每个判断都基于 query 拿到的真实数值与区域，勿臆造。
```

`ensure_zone` 的 observation（`tools.js:798`）只说「已生成聚合层（838 单元）」，不含具体数值。Agent 认为要满足「每个判断都基于 query」就必须再调 `query_layers` 或 `query_zone_stats` 获取数值。

**修复**：① 增强 `ensure_zone` observation，附带关键统计摘要（如「含 polarity/point_count 字段·可直接用于结论」）；② 在 AGENT_TEMPLATE 中澄清「工具 observation 中的统计信息即视为 query 取证」。

### 根因 4："通常 3-6 轮" 框架 → 正常化多轮行为

**文件**：`prompts.py:95`

```
4. **信息足够即 answer，简单问题提速**：通常 3-6 轮；**简单问题（单图层能答的 B 类 / 轻 C 类）≤3 轮**
```

在 prompt 中写「通常 3-6 轮」等于告诉 LLM「做 3-6 轮是正常的」。当 Agent 第 1 轮就完成了任务，它可能觉得「只做 1 轮太少了」→ 补做验证查询。

**修复**：改为「**最少轮次原则**——工具产出用户要求的图层后立即 answer，不要为"完整性"追加查询。简单操作 1 轮即答，复合操作 2-3 轮。最多 6 轮（绝对上限）」。

### 根因 5：ensure_zone observation 缺少「任务完成」信号

**文件**：`tools.js:798`

```javascript
return { observation: `已生成聚合层「${r.layerName}」（${r.featureCount} 单元）` };
```

这只是一个事实陈述。对比 `runTemplatePath` 中注入的 context（`harness.js:366`）：

```javascript
ctx.context = `【单技能路径·已执行 ${def.tool}】基于上述工具观察直接出结论，勿重选工具、勿重复执行、勿再调 geo 工具。\n\n`;
```

**修复**：在 while-loop 中，当工具产出图层后，向 toolHistory 追加一条系统级提示：「✅ 已生成用户要求的分析图层。如无进一步操作需求，请直接 answer。」

---

## 三、优化策略（四层体系）

### 总览

```
用户 NL："生成 L2 的 1000m 方格网空间聚合分析图"
       │
       ▼
[L0] 路由层修复：B_TRACK_PARADIGM 补触发词 → 单技能路径（runTemplatePath）
       │   ✅ 0 中间 LLM 轮，直接出图 + answer
       │
       ▼ （若仍落 while-loop）
[L1] 生成类快速通道：检测到 "生成/出图/热力图/网格" 关键词 → 缩 MAX_ROUNDS 到 2-3
       │   ✅ 减少可浪费的轮数
       │
       ▼
[L2] 工具完成后暗示：observation 末追加「任务完成信号」→ agent 感知
       │   ✅ 不依赖 prompt 软约束
       │
       ▼
[L3] prompt 修复：规则条件化 + 最少轮次原则 + 反过度查询
       ✅ 从源头减少 Agent 的行为偏差
```

### L0：路由层修复（最高杠杆·1 行代码）

**文件**：`ai_qa/paradigm.py:130-132`

```python
# Before:
{'archetype': '密度分布', 'stage': 'Analyze',
 'triggers': ['核密度', '密度分析', '聚集强度', '热力分布', '热力图', '热力', '密度', '集中'],
 'template': 'density'},

# After:
{'archetype': '密度分布/网格聚合', 'stage': 'Analyze',
 'triggers': ['核密度', '密度分析', '聚集强度', '热力分布', '热力图', '热力', '密度', '集中',
              '网格', '方格', '方格网', '聚合域', '空间聚合'],
 'template': 'density'},
```

**效果**：「方格网空间聚合」→ Flash 诊断为 `density` → `runTemplatePath` → 1 次工具调用 + 1 次 answer → **总耗时 ~5-8s**（而非 while-loop 的 30-75s + 超时风险）。

**联动修改**（`harness.js:302-310`）：density 单技能路径已有网格语义兜底：
```javascript
if (skill === 'density' && params.mode === '2d' && /网格|方格|标准格|grid/i.test(ctx.question || '') && !/热力|密度|heatmap/i.test(ctx.question || '')) {
    params.mode = '3d';
}
```
此兜底逻辑在单技能路径下生效——L0 修复使"方格网"能走到单技能路径，触发此兜底自动切 `mode='3d'`。

### L1：生成类请求快速通道

**文件**：`frontend/js/ai_qa/harness.js:618-619`

在 while-loop 入口处，检测问句是否为"生成类"请求，若是则将 MAX_ROUNDS 缩到 2-3：

```javascript
// 生成类请求快速通道：用户说"生成/出图/做图/热力图/网格" → 缩轮数
const _IS_GENERATE = /生成|出图|做图|热力图|网格|方格|分析图|画/.test(ctx.question || '');
const maxRounds = (!diagnose.degraded && diagnose.intent === 'gis_operation')
  ? (_IS_GENERATE ? 3 : MAX_ROUNDS_GIS)
  : (_IS_GENERATE ? 2 : MAX_ROUNDS_OTHER);
```

**效果**：即使漏网进入 while-loop，生成类请求最多 2-3 轮，Agent 没空间做无意义的验证查询。

### L2：工具完成后的「任务完成信号」

**方案 A（推荐·轻量）**：在 while-loop 工具执行后，toolHistory 追加系统提示

**文件**：`frontend/js/ai_qa/harness.js:709`（while-loop）和 `harness.js:396`（runChainPath）

```javascript
// 工具执行后，若产出图层 → 追加完成信号
if (newLayerCount > 0 || (r && r.data && r.data.layerId)) {
  const _isGenerateQ = /生成|出图|做图|分析图|画/.test(ctx.question || '');
  const _hint = _isGenerateQ
    ? '\n[系统] 已生成用户要求的分析图层。如无进一步操作需求，请直接 answer——勿再 query/verify。'
    : '\n[系统] 已产出新图层。如用户意图已满足，可直接 answer。';
  toolHistory[toolHistory.length - 1] += _hint;
}
```

**方案 B（备选）**：增强 `ensure_zone` 的 observation

```javascript
// tools.js:798
const _hint = '。图层已含 polarity/point_count/emotion 等统计字段——可直接用于结论，勿再 query 验证';
return { observation: `已生成聚合层「${r.layerName}」（${r.featureCount} 单元）${_hint}` };
```

**推荐方案 A**，因为它是系统级方案（对所有工具生效），而非逐个工具修改。

### L3：Prompt 工程修复（4 处修改）

#### L3-a："先 query 后操作" → 条件化

**文件**：`prompts.py:92`

```
Before:
1. **先 query 后操作**：拿到问题先用 query_layers / query_zone_stats / query_attribution
   摸清当前有什么数据、数据说什么，再决定动作。**勿盲目 ensure_zone**（已有聚合层就复用）。

After:
1. **首轮 query 即可**：拿到问题后在首轮执行前 query_layers 了解数据概况（系统已自动注入）。
   工具执行产出的 observation 已含关键统计——**直接据此结论，勿追加 query 验证**。
   已有聚合层就复用，勿盲目重复 ensure_zone。
```

#### L3-b："数据驱动" → 澄清取证来源

**文件**：`prompts.py:93`

```
Before:
3. **数据驱动**：thought 里引用 query 拿到的真实数值/区域，勿臆造。

After:
3. **数据驱动**：结论中引用工具 observation 中的真实数值（图层名/单元数/极性值等）或 query 结果。
   工具 observation = 已验证的数据源，无需二次 query 确认。
```

#### L3-c："通常 3-6 轮" → "最少轮次原则"

**文件**：`prompts.py:95`

```
Before:
4. **信息足够即 answer，简单问题提速**：通常 3-6 轮；**简单问题（单图层能答的 B 类 / 轻 C 类）≤3 轮**；...

After:
4. **最少轮次原则·信息足够即 answer**：
   - 生成类请求（生成图/热力图/网格/分析图）：工具产出图层 → **立即 answer**（1-2 轮）
   - 简单 GIS 操作（单工具可完成）：1-2 轮即答
   - 复合操作：2-4 轮
   - 最多 6 轮（绝对上限·超此上限可能超时）
   不要为"完整性"追加查询——工具 observation 已提供足够数据驱动结论。
```

#### L3-d：FINAL_TEMPLATE 增加「勿过度查询」规则

**文件**：`prompts.py` FINAL_TEMPLATE 中增加一条：

```
8. **勿追加查询**：工具已产出的图层/统计是最终数据——不要在结论中说"建议进一步分析XX"来暗示多做操作。
   你看到什么就说什么，诚实地基于已有数据给出结论。
```

---

## 四、系统性策略总结

### 四层防线对照

| 层 | 机制 | 解决的问题 | 改动量 | 杠杆 |
|:---:|------|------|:---:|:---:|
| **L0** | B_TRACK_PARADIGM 触发词补全 | "方格网"不进单技能路径 | 1 行 | 🔴 最高——直接消除 while-loop |
| **L1** | 生成类快速通道缩轮数 | 漏网 case 仍有多余轮次 | 5 行 | 🟡 高——兜底保护 |
| **L2** | 工具完成信号追加 | Agent 不知道"做完了" | 10 行 | 🟡 高——系统级信号 |
| **L3** | Prompt 规则条件化 | 源头减少过度查询行为 | ~20 行 | 🟢 中——行为塑造 |

### 时间改善估算

| 场景 | 当前 | L0 后 | L0+L1+L2+L3 后 |
|------|:---:|:---:|:---:|
| "生成 1000m 方格网" | 30-75s（超时） | ~8s（单技能） | ~5s（单技能+快速通道） |
| "生成热力图"（已有触发词） | ~8s（单技能） | ~8s | ~5s |
| "分析西陵区情绪"（zonal·已在单技能） | ~10s | ~10s | ~8s |

### 不改的原则

- ❌ 不改 MANIFESTO（承重红线——会影响 Flash eval）
- ❌ 不改 MAX_ROUNDS 的绝对值（仅加生成类条件缩容）
- ❌ 不改 F3 完整性门禁逻辑（`ensure_zone` 补入 `_GEO_TOOLS` 作为可选项，但不强制）
- ❌ 不改 `select_template()` 的判定逻辑（仅补 B_TRACK_PARADIGM 数据）

---

## 五、实施 Plan

### Phase 1：路由修复（立即执行·1 文件 1 行）

| Task | 文件 | 改动 | 验证 |
|------|------|------|------|
| L0 | `paradigm.py:131` | density triggers 加 `'网格', '方格', '方格网', '聚合域', '空间聚合'` | 输入"生成方格网"→ diagnose 出 `template='density'` |

### Phase 2：快速通道 + 信号（1 会话）

| Task | 文件 | 改动 | 验证 |
|------|------|------|------|
| L1 | `harness.js:618` | 生成类请求缩 MAX_ROUNDS | 生成类请求进 while-loop 时只给 2-3 轮 |
| L2 | `harness.js:709` | 工具产出图层后 toolHistory 追加完成信号 | Agent 在第 2 轮看到信号后输出 answer |

### Phase 3：Prompt 修复（1 会话）

| Task | 文件 | 改动 | 验证 |
|------|------|------|------|
| L3-a | `prompts.py:92` | "先 query 后操作" 条件化 | Flash eval 路由不受影响 |
| L3-b | `prompts.py:93` | "数据驱动" 澄清取证来源 | — |
| L3-c | `prompts.py:95` | "最少轮次原则" 替代 "通常 3-6 轮" | — |
| L3-d | `prompts.py` FINAL_TEMPLATE | 增加"勿追加查询"规则 | — |

---

*审计覆盖：`frontend/js/ai_qa/harness.js`(while-loop 全量)、`ai_qa/prompts.py`(AGENT_TEMPLATE/FINAL_TEMPLATE 全量)、`ai_qa/manifesto.py`(规则段全量)、`ai_qa/paradigm.py`(B_TRACK_PARADIGM/select_template 全量)、`frontend/js/ai_qa/tools.js`(ensure_zone 全量)、`frontend/js/ai_qa/stages.js`(SKILL_DEFS 全量)*
