# CB-11 多图层合并（merge）修复方案评审（Codex 第三方）

> **评审方**：Codex（GPT-5，第三方独立评估小组）  
> **评审时间**：2026-08-02 | **分支**：`fix/emc-buglog` @ `5c3a787`  
> **对象**：[problem_report/CB11-merge-multi-layer_2026-08-02](../problem_report/CB11-merge-multi-layer_2026-08-02.md)  
> **结论**：**选方案 A（后端 `layers` 数组 concat）为根治方案**；B（overlay union 链）与 C（prompt 引导）对"合并多个独立图层"这一意图是错误路径。A 落地后，`buildLanduseCompletion`/`_deterministicRecover` 的 union 链（G1/G2 高危路径）可对 merge 语义退役——一箭双雕。

---

## 一、问题核实（agree 项目方根因）

用户测试②的失败链核实无误：

1. **系统确无"合并多个独立图层"能力**：`MergeRequest` 只有单 `boundary`（`api/geo_routes.py:239-244`），`merge()` 只做单层 `dissolve`/`unary_union`（`api/geo_routes.py:245-262`）；前端 `tools.js:1129-1142` merge guard 只认 `boundary`。
2. **LLM 的直觉是对的**：`merge({layer_list:["L011","L012","L013"]})` 正是"多图层合并"的正确 API 形态——是系统能力缺失，不是 LLM 选错。
3. **拒绝路径确认**：`validate_tool_call`（`tool_contracts.py:496+`）对 merge 无 `layer_list` 参数定义（静默忽略），`boundary` required 无默认 → 返 `缺必填参数: boundary`；前端 `tools.js` guard 再拦 → 用户看到失败。
4. **LLM 的纠结有事实依据**：overlay union 同名字段确实会出后缀（见第二节字段分析），它不敢走 overlay 是对的。

---

## 二、A vs B 核心评估：字段冲突 + 语义错配

### 方案 B（overlay union 链）——**不推荐**，三个硬伤

| 硬伤 | 分析 | 证据 |
|---|---|---|
| **语义错配** | overlay union 是**空间并集**（求两块面的并集几何，重叠区切碎），不是"把 3 个要素放进一个图层"。三个裁剪产物（商业/居住/公园广场）空间上不相交，union 会产出碎片 + 属性污染，与用户"保留 3 个要素·DLMC 分类"的预期完全不符 | `api/geo_routes.py:460` `gpd.overlay(a, b, how='union')` |
| **字段冲突** | overlay 内部 merge 会对同名字段加 `_1/_2` 后缀（`DLMC_1/DLMC_2`）——DLMC 分类字段被破坏；N 层链式 union 每次字段翻倍膨胀 | 问题报告 §二.3 已证实 + G1/G2 链式路径 |
| **复杂度与风险** | N 层 = N-1 次二元操作 + 每次字段膨胀；且该路径刚踩过 G1/G2 无限循环（`eb9ff5e` 修复），是已知高危区 | `26aa9b8` 引入 → `eb9ff5e` 修 |

### 方案 A（后端 `layers` 数组 concat）——**根治**

- **语义正确**：`pd.concat` 多图层 GeoDataFrame = 要素拼接（concat），同名字段（DLMC）自然合并、无后缀，分类语义保留；
- **字段干净**：同名字段直接对齐，不同字段补 NaN（各裁剪产物字段一致，问题不大）；
- **复杂度 O(1)**：一次后端操作完成 N 层合并，无链式、无循环风险；
- **与 LLM 直觉对齐**：LLM 已经猜对了 `layer_list`，A 只需把它做成正式参数（建议参数名 `layers`，alias 收 `layer_list`）。

### 方案 C（prompt 引导走 overlay）——**不推荐**

字段冲突与空间语义问题仍在，且违背"EMC 产物不临时创造"原则；是让 LLM 绕路，不是补能力。

**裁决**：**A**。B 只保留给真正的空间并集意图（如"把西陵区与伍家岗区合成一个连续片区"——相邻面求并），且该意图也可由 `merge(layers=[...], by)` 的 dissolve 表达，overlay union 在 merge 语义下可整体退役。

---

## 三、四个讨论点的独立意见

### 讨论点 1：concat（A）vs 空间并集（B）—— **concat 是唯一正确语义**

"合并 3 个独立图层（字段结构相同·保留 DLMC）"= 图层拼接（concat），不是空间求并。空间并集适用于"相邻面合成连续片区"（这正是 merge 单层 `unary_union` 已覆盖的场景）。二者是不同操作，concat 归属 merge、空间并集归属 overlay（或 merge 的 dissolve 模式），**不混用**。

### 讨论点 2：merge 语义边界 —— **并入 merge，不建新工具**

- 单层 dissolve（`boundary + by`，几街道→一片区）保留；
- 多图层 concat（`layers` 数组，可选 `by` dissolve）并入 merge——一个工具两个模式，语义都是"合并"；
- **不建新工具**：新工具会增加 LLM 选型歧义（本次失败正是 LLM 在 merge/overlay 间纠结所致），并入 merge 让直觉命中即成功。

### 讨论点 3：字段冲突处理 —— **concat 无冲突；overlay 重复列问题作为独立改进**

- **concat**：`pd.concat(gdfs, ignore_index=True)`——同名字段（MC/DLMC/area_km2/name_1/name_2）直接对齐，无后缀；`by` 存在时再 `dissolve` 归组。CRS 不一致时先统一 `to_crs`。
- **overlay 重复列**：作为独立改进修（overlay 是空间分析工具，字段后缀在"两图层属性并集"场景是合理语义），**不要用修 overlay 代替 merge**——两个工具两种语义。

### 讨论点 4：LLM 提示 —— 契约 when/params_str 显式两模式 + 禁替

契约 merge（`tool_contracts.py:203-219`）更新：

- `params_str` 加 `layers` 多选；
- `when` 明写："合并**多个独立图层** → `merge(layers=[id1,id2,...])`（concat·保留各要素分类字段）；合并**同一图层内**要素 → `merge(boundary, by)`（dissolve）。`overlay(how='union')` 是空间并集（求两块面的并集几何）·非图层拼接·同名字段会后缀冲突·**勿用 overlay 代替 merge**"；
- 参数 alias 收 `layer_list`（LLM 已用过的形态）。

---

## 四、实施方案（A · 完整改动面）

| # | 层 | 改动 | 文件 |
|---:|---|---|---|
| 1 | 后端 | `MergeRequest` 加 `layers: Optional[List[Any]] = None`；`merge()` 加 concat 分支：逐项 `resolve_boundary` → CRS 统一 → `pd.concat(ignore_index=True)` → 可选 `by` dissolve → 面积 + `_to_geojson`；`boundary` 单层路径保留 | `api/geo_routes.py:239-262` |
| 2 | 契约 | merge 加 `layers`（type list，alias `layer_list`）；`boundary` required 改 False；`required_slots`/`params_str`/`when` 更新（见讨论点 4） | `ai_qa/tool_contracts.py:203-219` |
| 3 | 校验 | `validate_tool_call` 对 merge 加 **one-of 特判**：`boundary` 与 `layers` 至少一个，否则 `缺必填参数: boundary|layers`（否则 LLM 只传 layers 仍被拒） | `ai_qa/tool_contracts.py:496+` |
| 4 | 前端编排 | `stages.js` SKILL_DEFS merge `required_slots: ['boundary'] → []`（one-of 无法在 required_slots 表达，以 tools.js guard 为准） | `frontend/js/ai_qa/stages.js:57` |
| 5 | 前端工具 | `tools.js` merge：guard 改 `!params.boundary && !params.layers`；传 `layers: (params.layers \|\| []).map(ref)`；observation 按模式措辞 | `frontend/js/ai_qa/tools.js:1129-1142` |
| 6 | Toolbox 委托 | `_opMerge` body 加 `layers` 透传；layers 模式命名 `as` 或「合并图层」 | `frontend/js/toolbox/vector-tool.js:86-99` |
| 7 | 补全路径 | `buildLanduseCompletion`/`_deterministicRecover` 的 **merge 意图改调后端 concat**（`tools.merge` with layers），union 链对 merge 语义退役（G1/G2 高危路径消失） | `frontend/js/ai_qa/harness.js` |
| 8 | 测试 | 后端：merge layers concat 保留 DLMC / CRS 不一致 / by dissolve 单测；契约：one-of 校验单测；前端：`validateParams` merge layers 通过；飞轮：`TOOL_TARGETS` merge 组加「合并X+Y+Z用地」多图层变体 | `tests/` + `frontend/js/test-cases.js` |

**兼容性**：`boundary` 路径完全不变（现有调用零回归）；新增 `layers` 为纯增量。

**验证**：
1. `pytest` 后端 merge layers 用例 + 全量零回归；
2. 浏览器用户测试②：「将剪裁出西陵区范围内的商业+居住+公园广场用地合并成一个图层」→ 一次合并、1 个图层含 3 要素、DLMC 分类保留；
3. 单层 merge 回归（`merge(boundary, by)` dissolve 不破）；
4. 飞轮 merge 组多图层变体绿。

---

## 五、风险与注意

- **CRS 不一致**：concat 前必须统一 CRS（裁剪产物同源通常一致，防御性 `to_crs` 便宜）。
- **字段差异**：不同图层字段集不一致时 concat 补 NaN——可接受；如需严格字段对齐，先 `gdf[common_cols]` 过滤。
- **one-of 校验是本次最容易漏的点**：只在契约加 `layers` 而漏改 `validate_tool_call`/`required_slots`，LLM 传 layers 仍会被"缺 boundary"拒——问题会原样复现。
- **`_to_geojson` 数量上限**（`_MAX_RETURN_FEATS`）：concat 结果超限时截断——3 要素场景无碍，但要在 observation 里诚实标注截断。
- **G1/G2 退役需确认**：确认无"真空间并集"场景依赖 union 链后再删，避免误删 overlay union 的空间并集能力（叠置分析本身保留）。

---

## 六、一句话结论

**选 A**：`merge(layers=[...])` 后端 concat 是"合并多个独立图层"的唯一正确语义（保留 DLMC、无字段后缀、单次操作）；B/C 治标且保留字段冲突与 G1/G2 高危链；A 落地同时让 merge 语义下的 union 链退役。实施时最容易漏的是 one-of 校验（`validate_tool_call` + `required_slots`）——漏了问题会原样复现。

---

*本报告为第三方独立评审；用户测试②失败链经代码核实（`validate_tool_call` 拒绝路径 + `tools.js` guard），浏览器复验需 API key。*
