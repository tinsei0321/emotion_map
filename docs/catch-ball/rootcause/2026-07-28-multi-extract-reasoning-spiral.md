# EMC「裁剪西陵+伍家岗」完整诊断报告

> **分析方**：DeepSeek V4 Pro（ZCode 主线程）  
> **日期**：2026-07-28  
> **触发用例**：「帮我从中心城区范围中裁剪出西陵+伍家岗的范围」  
> **数据**：手动上传 `中心城区行政区划_1623.geojson`  
> **结果**：❌ 未执行任何工具，LLM 推理耗尽后返回 `request_upload`

---

## 一、完整失败链（基于 thinking trace 逐段还原）

```
用户上传 → 中心城区行政区划_1623.geojson（5 个面要素）
用户提问 → 「帮我从中心城区范围中裁剪出西陵+伍家岗的范围」
     │
     ├─[1] 接地上下文 ✅ 正确识别
     │     面层·boundary首选·含:西陵区/伍家岗区/点军区/夷陵区/猇亭区
     │     字段:MC=cat:boundary_name:西陵区|伍家岗区
     │     → LLM 知道有数据、有字段、有目标值
     │
     ├─[2] LLM 推理 ⚠️ 进入死循环
     │     "extract_feature 只能按属性抽单个要素"
     │     "方案1：先提取西陵区，再提取伍家岗区，然后 merge 合并"
     │     "换个思路——也可以直接用 overlay(union)"
     │     "等等，merge 的 boundary 参数需要一个 preset_id..."
     │     "让我重新思考"
     │     "其实最简单的路径：..."
     │     "等等..."
     │     "换个思路..."
     │     "或者..."
     │     （推理 token 耗尽·未产出任何 tool_call）
     │
     └─[3] 放弃 → request_upload
           "需要您补充数据才能严谨作答"
           "预选工具 extract_feature 仅支持指定图层（layer），
            无法按属性条件筛选出西陵区和伍家岗区"
```

---

## 二、根因分析（4 层递进）

### 根因 1（🔴 核心）：FC 架构只能返回 1 个 tool_call，不支持"提取多个要素"

FC 诊断的设计是「选 1 个工具 + 填参数 + plans[] 存后续」。但 LLM 的思考模式是「需要 2 次 extract_feature + merge」——这需要 3 个 tool_call，FC 装不下。

LLM 知道 plans[] 可以放后续步骤，但它纠结于"extract_feature 一次只能提一个要素" → 认为无法在 1 个 tool_call 中完成 → 放弃。

**FC 架构的单工具假设与"提取多个要素"的自然需求之间存在结构性矛盾。**

### 根因 2（🟠 关键）：推理 token 在自我怀疑中耗尽

LLM 的 reasoning chain 展示了典型的"自我怀疑螺旋"：

```
方案1 → 换个思路 → 等等不对 → 让我重新思考 → 其实 → 换个思路 → 或者 → 等等 → 让我想想 → 其实最简单的 → 等等 → 换个思路...
```

每次"等等"都消耗 reasoning token，直到预算用尽，LLM 被迫放弃。**如果 LLM 在第一次想到"extract ×2 + merge"时就果断执行 rank=1（提取西陵），问题已经解决了。**

### 根因 3（🟡）：System prompt 未覆盖"多要素提取"场景

FC system prompt 的工具×数据兼容性表说：
```
extract_feature/overlay/merge/area_stats 需面层（polygon boundary）
```

但没告诉 LLM：
- "提取多个要素时，先提取一个作为 rank=1，其余放入 plans[]"
- "where 参数支持 eq/in 操作符，可以用 in 一次匹配多个值"

LLM 不知道 `where` 可以用 `in` 操作符。如果它知道可以做 `where="MC/in/西陵区,伍家岗区"`，一次 extract_feature 就解决了。

### 根因 4（🟢）：放弃后的错误信息误导用户

LLM 放弃后说"需要您补充数据"——但数据就在 Layers 中！这不是数据缺失，是 LLM 推理失败。用户看到"上传数据"的建议会困惑："我已经上传了啊？"

---

## 三、与之前失败案例的关联

这是同一用例 24 小时内的**第 4 次**不同根因：

| # | 时间 | 失败表现 | 根因 |
|:---:|------|------|------|
| 1 | 上午 | 「剪裁西陵区」→ 报缺数据 | `select_candidates` 数据盲 → 0LLM 过滤掉正确工具 |
| 2 | 下午 | 「将中心城区中的西陵区裁剪出来」→ MC 字段不存在 | `resolve_boundary` MC→name 重命名断裂 |
| 3 | 晚上 | 「裁剪出西陵+伍家岗」→ 生成但标注"未实际生成" | finalStep LLM 编造结论（多步链失败后幻觉） |
| 4 | 现在 | 「裁剪出西陵+伍家岗」→ request_upload | FC 单工具限制 + LLM 推理螺旋耗尽 |

**这 4 次失败涉及了 EMC 管道的 4 个不同环节：0LLM 候选选择 → 字段名规范化 → 工具链执行+finalStep → FC 推理限制。这不是一个 bug 修不好，是这个高频用例经过的环节太多。**

---

## 四、系统性修复方案

### 立即（止血·不改架构）

**方案 1**：FC system prompt 增加"多要素提取"指引

```
'## 多要素提取\n'
'从一个面层中提取多个要素（如"西陵区+伍家岗区"）：\n'
'- 方式A：where="namefield/in/要素1,要素2" 一次提取多个\n'
'- 方式B：rank=1 提取第一个，rank=2+ plans[] 提取其余\n'
'优先用方式A（一次完成）。\n'
```

**方案 2**：`_norm_where` 支持 `in` 操作符的逗号分隔值

当前 `_norm_where` 解析 `field/op/value`，如果 value 含逗号应该自动拆分为 `in` 操作符的数组。

### 短期（增强工具能力）

**方案 3**：`extract_feature` 支持 `where.field IN [v1, v2]` 一次提取多个

```python
# geo_routes.py _apply_attr_filter
if op == 'in':
    values = [v.strip() for v in str(value).split(',')]
    mask = col.isin(values)
```

**方案 4**：System prompt 减少 LLM 自我怀疑

当前 prompt 的"工具×数据兼容性"表格列出了限制条件，但也触发了 LLM 的过度谨慎。增加正面示例（few-shot）：

```
'示例：用户问"裁剪出西陵区和伍家岗区" → extract_feature(where="name/in/西陵区,伍家岗区")\n'
```

### 中期（架构改进）

**方案 5**：FC 路径支持多工具链（如 extract×2+merge）

当前 FC 只能返回 1 个 tool_call。考虑支持返回多个 tool_calls（数组），由 orchestrator 顺序执行。

---

## 五、这个用例暴露的深层问题

"裁剪出西陵+伍家岗"是一个**看似简单但对 EMC 架构极其不友好**的查询：

| 特征 | 为什么对 EMC 不友好 |
|------|------|
| 涉及 2 个目标要素 | FC 单工具假设冲突 |
| 需要理解字段语义 | 依赖字段识别（0LLM+Flash） |
| 多步操作 | 需要工具链编排 |
| 空间+属性混合 | 需要区分 extract_feature vs clip |
| 中文口语表达 | "裁剪"可能指 clip 或 extract |

**每个维度都是 EMC 管道的薄弱点。4 次失败覆盖了 4 个不同环节，说明这条路径的鲁棒性要从管道的多个点同时加固，而非"堵一个漏"。**

---

## 六、相关代码位置

| 文件 | 行 | 作用 |
|------|:---:|------|
| `ai_qa/router.py` | 38-61 | FC system prompt（缺多要素提取指引） |
| `ai_qa/tool_contracts.py` | 170-185 | `extract_feature` 契约（where 参数描述） |
| `api/geo_routes.py` | 71-80 | `_apply_attr_filter`（需支持 in 操作符） |
| `api/geo_routes.py` | 106-119 | `_norm_where`（需支持逗号分隔值） |
| `frontend/js/ai_qa/tools.js` | 994-1019 | `extract_feature` 前端工具 |
| `core/geo_registry.py` | 168-178 | `resolve_boundary` — MC→name 重命名（#2 根因） |
| `frontend/js/ai_qa/harness.js` | 523 | finalStep context（缺执行结果·#3 根因） |
| `frontend/js/ai_qa/harness.js` | 276-286 | L1 产物验证 + 标注（#3 防御） |

---

> **归档信息**：`docs/catch-ball/rootcause/2026-07-28-multi-extract-reasoning-spiral.md`
