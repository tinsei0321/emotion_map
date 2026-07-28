# EMC 降智根因分析 — 追问失败 vs 胶囊成功

> **分析方**：DeepSeek V4 Pro（ZCode 主线程）  
> **日期**：2026-07-28  
> **触发用例**：
> - Round 1：「生成 L2 情绪热力图」→ ✅ 成功（综合热力图）
> - Round 2：「进一步分析消极情绪点的分布」→ ❌ 失败（filter_attr 层引用幻觉）
> - Round 3：点击胶囊「继续完成刚才的分析」→ ✅ 成功（消极热力图）

---

## 一、核心发现

> **同一意图，两条路径，结果相反：NL 追问走 FC 诊断（LLM 选工具+参数）→ 幻觉→ 失败；胶囊点击走确定性重放（预存参数）→ 正确→ 成功。差距不在"能力"，在"路径"。**

```
同一意图: "分析消极情绪分布"
     │
     ├── NL 追问路径（fcDiagnoseStep）          ├── 胶囊点击路径（runCapsule）
     │   LLM 读接地上下文                        │   读取预存的 diagnose 卡
     │   → 看到多种层标识混在一起                 │   → template=density
     │   → 不知道用哪个                           │   → params={polarity:"negative"}
     │   → 拼凑出 "T3·综合·yichang_L2..."        │   → 直接执行
     │   → 选 filter_attr（多余步骤）             │   → 成功 ✅
     │   → 失败 ❌                                │
```

---

## 二、两条路径对比

### 路径 A：NL 追问（失败）

```
用户输入："进一步分析消极情绪点的分布"
  │
  ├─ harness.js:orchestrate()
  │   └─ fcDiagnoseStep(ctx, hooks)
  │       │
  │       ├─ POST /api/v1/chat {phase:'fc_diagnose'}
  │       │   └─ system prompt 含 数据上下文（buildContext 输出）
  │       │
  │       ├─ DeepSeek V4 FC
  │       │   ├─ 接地上下文中有:
  │       │   │   "宜昌 L2 · T3（中心城区情绪·末）(1234条,点层,...)"  ← 展示名
  │       │   │   "T3·综合(567条,热力层)"                           ← 结果层名
  │       │   │   "要消极热力图直接 density.polarity=negative"       ← 明确指令
  │       │   │
  │       │   ├─ ⚠️ 问题 1: LLM 没有直接用 density(polarity=negative)
  │       │   │   而是选了 filter_attr → 多余的中间步骤
  │       │   │
  │       │   └─ ⚠️ 问题 2: LLM 不知道有效的 layer 值
  │       │       拼凑 "T3·综合·yichang_L2_T3_L2_result_geojson.geojson"
  │       │
  │       └─ 返回: {tool_calls:[{function:{name:"filter_attr",
  │                 arguments:'{"layer":"T3·综合·yichang_L2_T3..."}'}}]}
  │
  └─ harness.js:runTemplatePath()
      └─ TOOLS.filter_attr({layer:"T3·综合·yichang..."})
          └─ ref("T3·综合·yichang...") → 解析失败 → 原样传后端
              └─ 后端 resolve_points(...) → 不是预设ID → 💥
```

### 路径 B：胶囊点击（成功）

```
用户点击胶囊："我已上传所需数据，请继续完成刚才的分析"
  │
  ├─ harness.js:runCapsule()
  │   │
  │   ├─ 读取预存的 diagnose 卡（来自 Round 1 或 Round 2 的 plans/诊断）
  │   │   template = "density"
  │   │   params = {polarity: "negative", mode: "2d", ...}
  │   │   intent = "emotion_analysis"
  │   │
  │   ├─ ⚠️ 注意: 胶囊参数来自 plans[] 或 gap recovery，
  │   │   不经过 LLM 重新选工具+填参数
  │   │
  │   └─ harness.js:runTemplatePath()
  │       └─ TOOLS.density({polarity:"negative", mode:"2d"})
  │           └─ pickVisiblePointLayer() → 自动选点层（正确）
  │               └─ generateHeatmapForAI(...) → 成功 ✅
```

---

## 三、根因分析

### 根因 1：NL 追问路径存在"层引用歧义"

接地上下文（`buildContext()` 输出）混合了三种层标识：
- **展示名**：`宜昌 L2 · T3（中心城区情绪·末）`
- **结果层名**：`T3·综合`
- **预设 ID**：`yichang_l2_t3`（LLM 看不到）

LLM 不知道用哪个作为 `layer` 参数，自行拼凑了无效引用。

> 详见 `ROOTCAUSE_filter_attr_layer_hallucination_2026-07-28.md`

### 根因 2：LLM"工具选择偏差" — 追问时倾向换工具

接地上下文已明确写：
```
要"消极/积极热力图"直接生成（density.params.polarity=...）
```

但 LLM 在追问时选了 `filter_attr`（多余步骤），而非直接用 `density(polarity="negative")`。

**推测原因**：
- 上轮已用 `density(polarity="overall")` → LLM 认为"追问应该换个方式"
- `filter_attr` 的 `when` 描述包含"极性"→ LLM 觉得匹配
- 接地上下文中 filter_attr 和 density 都有对 polarities 的描述，LLM 选了看起来"更精确"的那个

### 根因 3：胶囊路径不经过 LLM 选工具 — 这是它成功的原因，也是它的局限

胶囊使用预存的 diagnose 卡参数，完全跳过 FC 诊断步骤。这意味着：
- ✅ 不受 LLM 幻觉影响
- ✅ 参数确定性高
- ⚠️ 如果预存参数本身有误，胶囊也会失败（但本轮恰好正确）

---

## 四、为什么胶囊能成功？

胶囊参数来源可能是以下之一：

| 来源 | 何时产生 | 参数 |
|------|------|------|
| Round 1 的 `plans[]` | LLM 首次诊断时产出 | `{tool:"density", params:{polarity:"negative"}, rank:2}` |
| Round 2 的 gap recovery | `filter_attr` 失败后 `ask_user` 恢复 | 系统回退到诊断卡中的备用方案 |
| Round 2 的 fail→fallback | 编排器检测到失败后自动重试 | 降级到旧 SSE diagnose 管线 |

最可能的来源：**Round 1 的 `plans[]`**。当 LLM 在第一轮诊断"生成 L2 情绪热力图"时，它不仅选了 `density(polarity="overall")` 作为 rank=1，还产出了 plans[]：
```json
{
  "plans": [
    {"rank":1, "tool":"density", "params":{"polarity":"overall",...}, ...},
    {"rank":2, "tool":"density", "params":{"polarity":"negative",...}, 
     "label":"生成消极情绪热力图", ...}
  ]
}
```

当用户点击胶囊时，系统执行 rank=2 的计划 → `density(polarity="negative")` → 成功。

换句话说：**正确的参数在第一轮就已经被 LLM 正确地产出了（在 plans[] 里），只是在第二轮 NL 追问时 LLM 没有选择使用这些参数，而是重新推理并出错了。**

---

## 五、系统性缺陷总结

```
                    NL 追问路径              胶囊路径
                    ───────────              ────────
工具选择            LLM 重新推理             预存 plans[]
                    → 可能偏差               → 确定

参数填充            LLM 从接地上下文推导      预存 params
                    → 层引用歧义              → 确定

层选择              LLM 拼凑字符串            自动（pickVisiblePointLayer）
                    → 可能幻觉               → 确定

失败恢复            依赖 harness 降级         预存多方案
                    → 可能丢上下文            → 完整
```

**核心矛盾**：系统在第一轮已经产生了正确的 plans[]（含消极热力图参数），但第二轮 NL 追问时没有复用这些 plans，而是让 LLM 重新推理——导致本可避免的错误。

---

## 六、修复建议

### 立即

| # | 建议 | 说明 |
|:---:|------|------|
| **1** | `buildContext()` 加引用标注 | 让 LLM 明确知道有效的 layer 参数值（详见 filter_attr 报告方案 A） |
| **2** | System prompt 加追问指引 | "追问时优先用 density.polarity 切换极性而非 filter_attr" |

### 短期

| # | 建议 | 说明 |
|:---:|------|------|
| **3** | 追问时复用 plans[] | 如果 ctx.plans 中有匹配当前意图的 plan（如 rank=2 的 density(negative)），优先执行而非重新 FC 诊断 |
| **4** | `ref()` 失败时返回可用层列表 | 当前静默传递无效引用到后端；前端应提前拦截并提供有用反馈 |

### 中期

| # | 建议 | 说明 |
|:---:|------|------|
| **5** | 接地上下文简化 | 减少展示名和元数据的噪音，突出"可用引用"和"推荐操作" |
| **6** | plans[] 优先级提升 | 在多轮对话中，上轮的 plans[] 应该比重新 FC 诊断有更高的执行优先级 |

---

## 七、相关代码位置

| 文件 | 行 | 作用 |
|------|:---:|------|
| `frontend/js/ai_qa/harness.js` | 531-550 | `runCapsule()` — 胶囊执行（绕过 FC，确定性） |
| `frontend/js/ai_qa/harness.js` | 737 | `fcDiagnoseStep()` — NL 追问入口（LLM 推理） |
| `frontend/js/ai_qa/stages.js` | 293-358 | `fcDiagnoseStep()` — FC 诊断实现 |
| `frontend/js/ai_qa/tools.js` | 562-641 | `buildContext()` — 接地上下文（需加引用标注） |
| `frontend/js/ai_qa/tools.js` | 169-191 | `ref()` — 层引用解析（需错误反馈） |
| `ai_qa/router.py` | 38-61 | FC system prompt（需加追问指引） |

---

> **归档信息**：`docs/catch-ball/emc-arch-deepdive/ROOTCAUSE_nl_vs_capsule_2026-07-28.md`  
> **关联报告**：`ROOTCAUSE_filter_attr_layer_hallucination_2026-07-28.md`（层引用歧义）、`ROOTCAUSE_extract_feature_MC_2026-07-28.md`（字段名断裂）
