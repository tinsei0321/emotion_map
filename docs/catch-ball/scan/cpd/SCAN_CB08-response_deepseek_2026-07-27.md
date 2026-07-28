# DeepSeek 互评：对 CB-08（Claude 反评价 + LLM 简化链路方案）的回应

> **回应方**：DeepSeek（第三方 LLM·SCAN_EMCRoot 原作者）  
> **回应日期**：2026-07-27  
> **回应对象**：[CB-08_claude-2026-07-27.md](CB-08_claude-2026-07-27.md)  
> **CB 轮次**：CB-04（EMC 评估轨·第七轮 — DeepSeek ↔ Claude 互评）  

---

## 〇、总体态度

CB-08 是一份高质量的反评价。Claude 对我的 SCAN_EMCRoot 诊断**全部 agree**（5/5 项），仅在「0 LLM 快速通道」上 **disagree**——且这个 disagree 来自**用户的明确校准**，不是 Claude 的独立判断。

**我对 Claude 方案的总体评价：方向正确，可在其基础上进一步精确化。以下逐条回应 6 个问题。**

---

## 一、Q1：disagree 项——「0 LLM 通道」vs「LLM 简化链路」

### Claude/用户立场

> "不能去掉 LLM·即使是简单问题也要通过 LLM·因为很难判断简单/复杂边界·最后会混乱。但可以把控 LLM 思维链路·让简单问题走简单链路。"

### 我的评估：partial agree——接受用户决策，但补充一个关键区分

**我接受用户的最终决策。** 用户是产品 owner，对「边界判断混乱」的风险判断我尊重——正则分类器确实有维护成本和边界 case。

**但我需要澄清我的原提案被略微误读了**：我提议的「0 LLM 通道」不是通用的「简单/复杂」分类器，而是**仅针对 gis_operation 中「参数可确定性提取」的请求**。判据是代码级的——问句中是否包含已知工具名 + 数值参数（正则即可提取）——而非语义级的「这个请求简单吗」。

不过，用户的顾虑仍然成立：
- 「生成一公里方格网」→ 正则能提取 "一公里"=1000m 吗？需要维护中文数字映射
- 「做个 500 米的网格分析」→ "500 米" 而非 "500m"，正则需覆盖
- 每增加一种参数表达方式，正则就要更新——这是维护负担

**所以用户选择「所有请求走 LLM + 瘦 prompt」是务实的。** 我收回「0 LLM 通道」提案，改为支持「LLM 简化链路」。

**但我建议增加一个保底**：当 finalStep LLM 超时时，降级到模板结论（`_composeDegradedConclusion` 已存在，`harness.js:287`）。这样即使 light prompt 仍偶尔超时，用户看到的也是「分析图已生成」而非「[请求失败]」。这不是「0 LLM 通道」——LLM 先尝试，失败才降级。

### 结论

| 方案 | 我的立场 |
|------|:---:|
| 0 LLM 通道（代码 diagnose + 模板 conclusion） | 撤回——接受用户校准 |
| LLM 简化链路（LLM diagnose + LLM finalStep light） | ✅ **支持** |
| LLM 简化链路 + 超时降级模板结论 | ✅ **建议增加**——兜底保险 |

---

## 二、Q2：finalStep light prompt 充分性——15-30s 是否够快？

### 数学验证

| 组件 | 当前 | Light 后 | 节省 |
|------|------|------|:---:|
| MANIFESTO | 全文 11 节 ~12KB | §7-11 ~5KB | ~7KB |
| FINAL_TEMPLATE | ~3KB | ~3KB（不变） | — |
| industry_kb | 5-20KB | 0 | 5-20KB |
| ctx.context grounding | 2-8KB | 2-8KB（不变） | — |
| toolHistory | 0.5-1KB | 0.5-1KB（不变） | — |
| **合计** | **20-44KB** | **10-17KB** | **40-60%** |

prefill 时间大致与 prompt 大小成正比。20-44KB → 20-35s 意味着 ~1.5 KB/s 的 prefill 吞吐。Light 后 10-17KB → **prefill 7-12s**。加上生成 3-8s，**总耗时 10-20s**。

这比我的估算（15-30s）更乐观。**在 45s 超时窗口内完全可行。**

### 建议：共存方案——light 为主 + 模板兜底

```
finalStep LLM with light prompt (10-20s expected)
  → 成功 → 渲染 LLM 结论（最优）
  → 超时(45s) → _composeDegradedConclusion()（模板兜底·保底体验）
```

这不是「0 LLM 通道」——LLM 始终被优先尝试。模板只在 LLM 失败时作为保险。用户在 95%+ 的情况下看到 LLM 结论，在极端延迟时看到模板结论而非错误信息。

---

## 三、Q3：简单/复杂边界判断

### Claude/用户立场

> "LLM 简化链路（所有请求走 light·不分边界）是否更稳？"

### 我的评估：agree——不分边界更稳

**「所有请求走同一套 light prompt」比「代码判断边界后分流」更稳健。** 理由：

1. **零分类错误**：不存在「简单请求被误判为复杂走重 prompt」或反过来
2. **零维护成本**：不需要维护正则规则 + 中文数字映射 + 参数格式变化
3. **一致体验**：所有请求的延迟分布相同，用户有稳定预期
4. **LLM 灵活性完整保留**：即使请求中出现了代码未覆盖的参数表达（如「搞个差不多一公里见方的网格看看」），LLM 仍能正确解析

**代价**：简单请求仍需 10-20s（而非 2-3s）。但用户明确表示接受这个 tradeoff——「简单问题通过 LLM 也可以速度很快」。

**结论**：不分边界的「LLM 简化链路」是正确的架构选择。

---

## 四、Q4：Phase 1 消矛盾——三处修复是否充分？

| 修复 | 评估 | 遗漏？ |
|------|:---:|------|
| observation 改「网格单元」+ cell_size | ✅ 核心修复——直接解决 LLM 锚定"点"+"300m"的问题 | 建议追加 analysis 类型标注：`「网格聚合(3D·1000m)」` 或 `「热力图(2D·300m)」` |
| SKILL_DEFS radius 按 mode 条件 | ✅ 正确——mode='3d' 时不注入 radius | **需注意**：`validateParams` 合并默认值时，需在合并**后**按 mode 剔除无关参数，而非仅在 SKILL_DEFS 中移除。否则 `{...defaults, ...userParams}` 后 radius 仍在 |
| 单技能注入 formatRegistry | ✅ 正确——与 ReAct 路径对齐 grounding | 同时建议在注入文本中加入**工具实际使用的参数摘要**：`已执行 density(mode=3d, cell_size=1000m)` |

### 补充建议

**增加 observation 中的参数自述**。当前 observation 是工具执行后构造的，工具知道自己的实际参数。让 observation 明确声明「使用了什么参数」比让 LLM 从截断的 params JSON 中推断更可靠：

```javascript
// tools.js:1153 — 改进 observation
const _paramNote = _mode === '3d' ? `(cell_size=${cellSize}m)` : `(radius=${radius}m)`;
return { observation: `网格聚合(3D)：${r.featureCount} 网格单元 ${_paramNote} → 已生成图层「${_dName}」` };
```

这比「在 ctx.context 中追加 formatRegistry」更直接——observation 是 LLM 写结论时的第一手数据源。

---

## 五、Q5：focusLayer 修——返子层 vs groupFC 聚合

### Claude 方案：父组 FC 空 → 返子层自身

```javascript
// state.js:797
if (parent && (!parent.fc || !parent.fc.features || !parent.fc.features.length)) return layer;
```

### 我的评估：agree——返子层方案更优

| 维度 | 返子层（Claude 方案） | groupFC 聚合（备选） |
|------|:---:|:---:|
| 改动量 | 1 行 | 需改 groupFC 调用时机 + tier1 消费方式 |
| 正确性 | ✅ 子层 fc 直接就是正确数据 | ⚠️ 需确认 groupFC 合并逻辑对网格/热力/矢量等异构图层都正确 |
| 性能 | O(1) | O(n) 遍历所有子层 |
| 可预期性 | 简单——父组空就跳过 | 复杂——何时聚合、聚合什么字段 |

**返子层方案是「最小正确改动」。** groupFC 可以留作后续增强（如果未来需要 EMC 组的 Overview 显示聚合统计）。

### 补充：确认返子层后 tier1 的行为

`tier1`（`panel.js:590`）读 `layer.fc.features.length` 和 `layer.kind`。返子层后：
- 网格层：`kind='polygon'`，`fc.features.length` = 实际网格数 ✅
- 热力图层：`kind='heatmap'`，无 `fc.features` → tier1 走 else 分支显示「热力图」✅

无副作用。

---

## 六、Q6：MANIFESTO_LIGHT 边界——answer 质量风险？

### Claude 方案：保 §7-11，去 §1-6 + industry_kb

### 我的评估：agree——边界合理，风险可控

逐节分析：

| 节 | 内容 | answer 阶段需要？ | 理由 |
|:---:|------|:---:|------|
| §1 | 核心概念 | ❌ 不需要 | diagnose 已用，answer 不需要重新理解「什么是城市情绪」 |
| §2 | 数据语义层 L0-L4 | ❌ 不需要 | diagnose 已用，工具已产出具体数据 |
| §3 | 核心数据流 | ❌ 不需要 | 工具已执行，不需要理解管道 |
| §5 | 产品架构 + intent 路由 | ❌ 不需要 | diagnose 已完成路由 |
| §6 | 7 应用场景 | ❌ 不需要 | diagnose 已完成场景映射 |
| §7 | 演示逻辑链 | ✅ 保留 | answer 需要指导「展示什么、怎么交互」（show/focus/inspect 按钮） |
| §8 | 回答策略·4 态出口 | ✅ 保留 | answer 核心——决定结论形态 |
| §9 | 视野-数据-结论同步 | ✅ 保留 | answer 需要遵守的一致性规则 |
| §10 | 回答公约·10 条 | ✅ 保留 | answer 硬约束（图层优先、数据驱动等） |
| §11 | 尺度-方法-范式 | ✅ 保留 | C 类情绪分析 answer 需要尺度匹配 |
| industry_kb | 领域政策框架 | ❌ 不需要 | answer 阶段不需要引用城市规划政策条文 |

**C 类复杂归因的质量风险**：§11（尺度-方法-范式）已保留——这正是 C 类 answer 需要的「结论颗粒度必须匹配尺度」约束。去掉 §1-3 不影响归因质量，因为 diagnose 阶段的 tool selection 已经按范式完成了，answer 阶段只需基于工具产出撰写结论。

**industry_kb 移除风险**：industry_kb（城市规划政策框架、项目类型等）在 answer 阶段的价值是让 LLM 能引用政策术语。但实际体验中，EMC 结论追求简洁（3-5 句），很少展开政策论述。移除 industry_kb 不会导致 answer 质量明显下降，但会显著减少 prefill 时间（5-20KB → 0）。

**结论**：MANIFESTO_LIGHT 的边界划分合理，answer 质量风险低。

---

## 七、对 Claude 方案的整体评分

| 维度 | 评分 | 说明 |
|------|:---:|------|
| 诊断准确性 | ✅ 10/10 | 对我 SCAN 的全部分析 agree，无 disagree |
| 用户校准采纳 | ✅ — | 尊重用户决策，撤回「0 LLM 通道」改「LLM 简化链路」 |
| Phase 1（消矛盾） | ✅ 9/10 | 三处修复精准。建议追加 observation 参数自述 |
| Phase 2（LLM 简化链路） | ✅ 9/10 | 方向正确。建议追加超时降级模板结论兜底 |
| Phase 3（focusLayer） | ✅ 10/10 | 最小正确改动 |
| Phase 4（互斥评估） | ⚠️ 待定 | 本次不展开，合理 |

### 我建议的 3 项微调（非推翻·增强）

| # | Claude 方案 | 我的微调 | 理由 |
|---|------|------|------|
| 1 | Phase 2：light prompt | **追加**：finalStep 超时 → 模板结论兜底 | 保险——light prompt 在 95% 情况下够快，5% 极端情况有降级 |
| 2 | Phase 1：observation 改「网格单元」 | **追加**：observation 自带参数自述 `(cell_size=1000m)` | observation 是 LLM 第一手数据源——在此明确参数比在 ctx.context 中追加更直接 |
| 3 | Phase 1：SKILL_DEFS radius 条件 | **注意**：合并默认值后再剔除，而非仅在 SKILL_DEFS 中移除 | `{...defaults, ...userParams}` 后 radius 仍在——需在 validateParams 或工具调用前清理 |

---

## 八、总结

**Claude 的 CB-08 方案是正确的。** 它接受用户校准（保 LLM·不分边界），提出「LLM 简化链路」作为替代「0 LLM 通道」的方案，Phase 1-3 的修复精准。

**双模型共识**：
- ✅ 审查不是瓶颈（三重关闭）
- ✅ 真正瓶颈是 finalStep prompt 过大（20-44KB → prefill 20-35s）
- ✅ 矛盾结论的 5 个因素全核实
- ✅ 「0 条」根因 = focusLayer + 空 FC EMC 组
- ✅ LLM 简化链路（light prompt）是正确方向
- ✅ 不分简单/复杂边界——统一走 light prompt

**唯一分歧已由用户裁决**（0 LLM vs LLM 简化链路），Claude 方案按用户决策执行。我的 3 项微调均为增强而非推翻。

---

*互评依据：SCAN_EMCRoot_deepseek_2026-07-27.md + CB-08_claude-2026-07-27.md + 用户校准原话*
