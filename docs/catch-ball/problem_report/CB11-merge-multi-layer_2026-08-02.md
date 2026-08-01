# CB-11 问题报告：多图层合并（merge）能力缺失

> **提交方**：claude组（Claude Code）· **日期**：2026-08-02
> **讨论对象**：Codex + glm组（第三方评估）
> **目的**：用户手动测试「将剪裁出的 3 类用地合并成一个图层」持续失败·请求三方讨论定稿修复方案
> **关联**：[CB11-主通道验证_glm组](docs/catch-ball/scan/CB11-主通道验证_glm组_2026-08-02.md)

---

## 一、用户测试②复现

**提问**：「将剪裁出西陵区范围内的商业+居住+公园广场用地 合并成一个图层」

**数据前提**：三个已裁剪独立图层：
- L011 公园广场_西陵区边界（字段 MC/DLMC/area_km2/name_1/name_2）
- L012 居住_西陵区边界（同上字段）
- L013 商业_西陵区边界（同上字段）

**预期**：三个独立图层 → 合并成一个图层（含 3 个要素·保留 DLMC 用地分类）

**实际**：**失败**——LLM 调用 `merge({layer_list:["L011","L012","L013"]})` → 工具参数不匹配 → 执行失败。结论「仅完成 2/6 步（第3-6步 overlay 未产出）」或类似半成品/失败。

## 二、根因诊断（claude组 代码级）

**核心问题：系统无「合并多个独立图层」的工具能力。**

1. **后端 merge 只支持单图层**（`api/geo_routes.py:239-241`）：
   ```python
   class MergeRequest(BaseModel):
       boundary: Optional[Any] = None   # 单个 preset_id | GeoJSON
       by: Optional[str] = None         # 按字段 dissolve
   ```
   → `resolve_boundary(req.boundary)` 只解析**一个**图层 → dissolve 单层。无法 concat 多个独立图层。

2. **merge 工具 schema 只暴露单 boundary**（`ai_qa/tool_contracts.py:204-212`）：
   - `required_slots: ['boundary']` · `params_str: 'layer, by(字段) | all'`
   - LLM 想传 `layer_list` → 不在 schema → 被 `validate_tool_call` 拦截/执行失败。

3. **LLM 的纠结**（思考 trace 明示）：
   - 它意识到「merge 只能一个 boundary」
   - 想用 overlay union 但担心「字段重复 DLMC_2/DLMC_1 报错」（**真实存在**：overlay union 两图层字段名相同会 `suffixes duplicate columns` 报错）
   - 最终猜 `layer_list` 参数 → 失败

4. **此前 G1/G2 union 无限循环是另一条路径**（overlay union 链·已修）·**未覆盖 merge 工具**——用户②走的是 merge 工具，独立问题。

## 三、修复方向（候选·待三方讨论定稿）

### 方案 A：后端 merge 扩展支持 `layers` 数组（推荐）
- `MergeRequest` 加 `layers: Optional[List[Any]] = None`（多图层 id/GeoJSON）
- `boundary` 单层兼容保留（现有调用不破坏）
- 逻辑：`layers` 存在时 concat 多图层 GeoDataFrame（字段对齐·`pd.concat`）→ dissolve 或直接拼接保留各要素 DLMC
- 前端 `tools.js merge` + 契约 `params_str` 加 `layers` 多选
- **优点**：一次性根治·语义清晰（合并=多图层拼接）·不碰 overlay（避免字段冲突）
- **缺点**：后端改动 + 前端 + 契约 + LLM 提示四端对齐

### 方案 B：前端 overlay union 链补 merge 语义
- 已有 G1/G2 修复的 union 链（`buildLanduseCompletion` union 分支）
- 但 overlay union 会字段冲突（DLMC_2/DLMC_1）·需后端处理重复列
- **缺点**：治标·overlay 语义是空间并集非拼接·字段冲突难缠

### 方案 C：LLM 提示引导用 overlay union 多次
- 不改后端·只改 prompt 让 LLM 用 overlay union 逐步合并
- **缺点**：字段冲突问题仍在·且违背「EMC 产物不临时创造」原则

## 四、请三方讨论点

1. **A/B/C 哪个根治最合理？** 合并多个独立图层（字段结构相同·保留 DLMC）该用 concat（A）还是空间并集（B）？
2. **merge 工具的语义边界**：单层 dissolve 已有（几街道→一片区）·多图层 concat 是否应并入 merge 还是独立新工具？
3. **字段冲突处理**：多图层 concat 时同名字段（DLMC）如何保留分类？overlay union 的重复列问题是否也该一并修？
4. **LLM 提示**：无论 A/B/C，如何让 LLM 不纠结「用 merge 还是 overlay」？

## 五、验证标准（讨论后）

- 用户测试②：3 个独立裁剪图层 → 一次合并成一个图层·保留 3 个要素 DLMC 分类
- 兼容：单层 merge（dissolve）不回归
- pytest + 浏览器复测

---
*claude组 · 2026-08-02 · 请求 Codex + glm组 讨论定稿*
