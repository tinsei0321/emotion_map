# EMC "简单裁剪反复失败" 根因分析

> **分析方**：DeepSeek V4 Pro（ZCode 主线程）  
> **日期**：2026-07-28  
> **触发用例**：「根据中心城区范围裁剪出西陵+伍家岗范围」  
> **现象**：结论文字声称成功提取，但图层标注「（注：未实际生成）」—— **finalStep LLM 编造了结论，图层实际未产出**

---

## 一、根因摘要

> **finalStep 的 LLM 在写结论时不知道工具链执行的真实结果。工具可能部分失败或被跳过，但 LLM 从 `ctx.context` 中看到 diagnose 卡说"用 extract_feature 抽取西陵+伍家岗"，就假定执行成功并写出完整结论。`applyQualityDefense` 发现骗局后诚实标注了「未实际生成」，但无法补救——图层已经没了。**

---

## 二、失败链路追踪

```
用户：「根据中心城区范围裁剪出西陵+伍家岗范围」
  │
  ├─[1] FC 诊断 → 选 extract_feature（正确）
  │     plan: ①extract 西陵 ②extract 伍家岗 ③merge
  │
  ├─[2] runTemplatePath / runChainPath / while-loop
  │     │
  │     ├─ 尝试 extract_feature(where="name/eq/西陵区") 
  │     │   → ❌ 失败（字段不存在 / 数据不匹配 / MC→name 重命名问题）
  │     │
  │     ├─ 降级/重试/跳过…
  │     │
  │     └─ 最终未产出有效图层
  │
  ├─[3] finalStep LLM 被调用
  │     ctx.context 中有：
  │       - diagnose 卡：template=extract_feature, method=[extract_feature()]
  │       - "已执行 extract_feature" 的描述（不管成功与否）
  │       - formatRegistry() 输出
  │     │
  │     ⚠️ LLM 不知道执行结果，从 context 推断"应该成功了"
  │     → 产出：{{show:西陵区+伍家岗区}} + 长篇地理描述
  │     → 描述里提到夷陵广场、CBD、运河公园、宜昌东站…
  │       （这些地名是 LLM 对宜昌的地理知识，不是从数据中读到的！）
  │
  └─[4] applyQualityDefense L1
        _verifyClaims: "西陵区+伍家岗区" 不在 getLayers() 中
        → inline 标注：「（注：未实际生成）」
        → 诚实，但用户看到的是"说了做了但没做"
```

---

## 三、三个叠加根因

### 根因 1（🔴 主因）：finalStep LLM 无执行结果感知

`finalStep` 收到的 `ctx.context` 只包含"计划做什么"，不包含"实际做了什么、哪些失败了"。

```javascript
// harness.js:523 — finalStep 前的 context 重构
ctx.context = `【单技能路径·已执行 ${def.tool}】基于上述工具观察直接出结论…
【地图实际产出图层】${formatRegistry()}…\n\n` + (ctx.context || '');
```

- `【单技能路径·已执行 extract_feature】` — 告诉 LLM "执行了"，但不说是成功还是失败
- `formatRegistry()` — 列出已注册的图层，但如果工具失败则列表为空
- 原始 `ctx.context` — 包含 diagnose 卡（计划），不含执行结果

**LLM 的默认行为是"相信系统已经做了该做的事"**。当它看到"已执行 extract_feature"但没有明确的失败信号时，它假定成功。

### 根因 2（🟠 辅因）：多步工具链无原子性保证

"裁剪出西陵+伍家岗"需要至少 2 步（extract × 2），可能需要 merge。如果任何一步失败：
- 后续步骤可能跳过
- 已成功的步骤产物可能残留
- 没有统一的回滚机制

当前代码的降级路径是：
```javascript
// harness.js:493 — 失败检测
if (failed || (newLayerCount === 0 && !hasRows)) {
    // → ask_user（可恢复）或 EXIT_GAP（不可恢复）
}
```

但 `ask_user` 路径可能不触发 finalStep（它直接返回），而 EXIT_GAP 只在特定条件下触发。中间状态可能导致 finalStep 在"部分成功"的情况下被调用。

### 根因 3（🟡 辅因）：LLM 用世界知识填补数据空白

finalStep 产出的结论中提到了"夷陵广场、CBD、运河公园、宜昌东站、中南路"——这些地理细节**不可能**来自上传的"中心城区"多边形数据（这种数据通常只有名称+几何，不会有商业地标描述）。

LLM 用自己的训练数据（对宜昌的地理知识）填补了信息空白，让结论看起来非常专业可信，但完全是编造的。

---

## 四、为什么"（注：未实际生成）"不够

`applyQualityDefense` 的 L1 检测是诚实的，但它发生在**用户已经看到完整结论之后**：

| 时间点 | 用户看到 | 问题 |
|------|------|------|
| finalStep 产出 | 「已从中心城区行政区划中筛选出西陵区和伍家岗区…西陵为老城中心（夷陵广场、CBD…）」 | 看起来完全可信 |
| applyQualityDefense | 「（注：未实际生成）」追加到末尾 | 用户先被说服，后被否定——信任崩塌 |

**修复方向不是在 defense 层面加强检测，而是在 finalStep 之前阻止 LLM 写出不实结论。**

---

## 五、修复方案

### 方案 A（推荐·最小改动）：finalStep 前注入执行结果摘要

在 `harness.js:523` 处，将工具执行的真实结果注入 context：

```javascript
// 当前
ctx.context = `【单技能路径·已执行 ${def.tool}】...\n\n` + (ctx.context || '');

// 改进：注入执行结果
const execResult = newLayerCount > 0 
  ? `【执行结果】成功生成 ${newLayerCount} 个图层：${formatRegistry()}`
  : `【执行结果】⚠️ 工具执行未产出图层。地图上当前无新增图层。请诚实说明，不要编造已生成的图层。`;
ctx.context = execResult + '\n\n' + (ctx.context || '');
```

### 方案 B（短期）：`{{show:}}` 模板在 defense 前就做存在性检查

在 finalStep 的 `onToken` 回调中，当检测到 `{{show:X}}` 模板时，立即检查 X 是否在 registry 中。如果不在，替换为 `（图层 X 未生成）` 而非留到 defense 阶段。

### 方案 C（中期）：finalStep 分离"结论生成"和"图层引用"

让 finalStep 只生成文字结论，图层引用由代码层（`formatRegistry()`）自动追加，不由 LLM 控制。

---

## 六、为什么"简单裁剪"反复失败——汇总

这个用例在过去 24 小时内被报告了多次：

| 时间 | 用例 | 失败原因 |
|------|------|------|
| CB-08 前 | 「剪裁西陵区」 | `select_candidates` 数据盲 → 误路由 clip |
| CB-08 后 | 「将中心城区中的西陵区裁剪出来」 | `extract_feature` 字段 MC 不存在（MC→name 重命名） |
| 现在 | 「裁剪出西陵+伍家岗范围」 | 多步工具链失败 + finalStep LLM 编造结论 |

**每次修好一个 bug，就暴露下一个。这不是"修不好"，是这条链路经过的代码太多（FC 诊断→工具选择→参数填充→字段解析→多步执行→finalStep→防御），每个环节都可能出错。**

**根治方向**：为"裁剪/抽取"这条高频路径建立专用快速通道，减少经过的环节数。

---

## 七、相关代码位置

| 文件 | 行 | 作用 |
|------|:---:|------|
| `harness.js` | 523 | finalStep 前 context 重构（缺执行结果） |
| `harness.js` | 276-286 | L1 产物验证 + inline 标注 |
| `harness.js` | 354-363 | `_extractClaimedLayers` — 提取 {{show:}} 引用 |
| `harness.js` | 247-255 | `_verifyClaims` — 对账地图实际图层 |
| `harness.js` | 420-432 | `_composeDegradedConclusion` — 降级结论模板 |
| `harness.js` | 489-518 | 工具失败 → ask_user / GAP 路由 |
| `tools.js` | 994-1019 | `extract_feature` 工具实现 |
| `geo_routes.py` | 198-219 | `extract_feature` 后端端点 |
| `geo_registry.py` | 168-178 | `resolve_boundary` — MC→name 重命名 |

---

> **归档信息**：`docs/catch-ball/rootcause/2026-07-28-hallucination-finalstep.md`
