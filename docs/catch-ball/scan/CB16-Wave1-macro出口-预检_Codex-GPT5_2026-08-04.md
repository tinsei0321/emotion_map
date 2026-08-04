# CB-16 Wave 1（macro 出口）实施预检（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）  
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `dd4009e`  
> **方法**：五处探索依据逐行核验 + 触发链路全链追查（DOMAIN_KW→B 部→domain_lens→resolve_outlet_id→field_mapping 消费）+ 独立推演  
> **范围**：只读评估 · 不改代码 · 不 commit

---

## 结论摘要（先行）

**草案总体可行（7 处方向正确），但有一个 P1 语义问题必须在实施时处理，另有 3 个 P2 细节。**

- **【P1】checkup_dimension 四维度 × 单尺度**：现有 `build_outlet_schema` 的 field_mapping 循环**不做 scale 过滤**（`build_outlet_schema.py:120-134` 逐槽从同一 result 取值）——macro 问句会把**城区单元的值填进"住房/小区/街区维度"槽**（语义误导，比"暂无数据"更糟）。建议：槽位加 scale 限定（仅填匹配 `diagnose.scale` 的维度，其余标"需对应尺度分析"），或 Wave 1 只映射"城区维度"槽。
- **【P2】细节**：① rows 空数组守卫（`rows.length > 0` 才出卡）；② `+` 语法只取首字段（`issue_label+place_name` 实际只取 issue_label，place_name 留 Wave 2）；③ N=评论数可用 `sum(rows[].point_count)` 保持语义（zonal rows 每行带 point_count），无该列才退行数并标注"区域单元数"。
- **【简化】草案③ 的"同步 stages.js:423 B 部"实为自动**：`stages.js:7` 已 `import { DOMAIN_KW } from './emc-patterns.js'`——补词后 B 部自动生效，无需改 stages.js。
- **边界核验：无越界** ✓（不碰 diagnose/orchestrate/ChatRequest；DOMAIN_KW 非 TRIGGER_WORDS，validate 同步不受影响；place_name 精确源留 Wave 2）。

---

## 一、探索依据核验（三层断裂属实）

| 断裂点 | 实测确认 |
|---|---|
| `_maybeBuildOutletCard` 只收图层 fc | ✅ `harness.js:1572` `if (newLayerCount <= 0) return null` + 产物收集仅 `getLayer(last.id).fc.features`（`:1580-1590`）——rows 型产物（zonal/rank 表格·未成层）直接 return |
| `_extract_emc_value` 不识别 rows | ✅ `build_outlet_schema.py:78-92` 仅处理 dict 直取 / `features[0].properties`——无 `{rows:[...]}` 分支 |
| checkup_dimension field_mapping 全 prose | ✅ `urban_checkup_outlets.py:34-48` 四槽均为描述文本（非字段名）→ `_extract_emc_value` 查不到 → 必"暂无数据" |
| DOMAIN_KW 缺「体检」 | ✅ `emc-patterns.js:13-18` urban_governance = 治理/交通/停车/施工/城管/环境，无体检 |
| zonal rows 已含归因列 | ✅ `geo_routes.py:374-389` `prop_cols = [name, point_count, polarity_index, score_mean, domain_top, element_top, issue_label, attribution, suggestion]` |

**补充核验（草案未列·关键）**：
- `checkup_dimension` 契约 domain = **`urban_governance`**（`urban_checkup_outlets.py:16`）→ 补「体检」到 governance B 部**对齐正确**。
- 触发词不缺：后端 `TRIGGER_WORDS`（`build_outlet_schema.py:22`）与前端 `OUTLET_TRIGGER_KW`（`emc-patterns.js:48`）**均已含「体检」**——缺的是 domain_lens 兜底 + rows + 字段映射，与草案判断一致。
- `_EMC_FIELDS` 白名单（`tests/test_outlet_kb.py:14`）含 issue_label/place_name/domain_top/element_top/polarity_index ✓（草案 ④ 字段全部在册）。

---

## 二、七问逐答

### 1. rows 并入出口链路（前端优先 rows + 后端 rows 分支）—— 对路；长期可统一收产物

- 前端"优先取最近工具 data.rows → 无 rows 退图层 fc"与后端"`_extract_emc_value` 加 rows 分支（Top-1·与 features 同构）"是**最小一致改动**，方向正确。
- 更优解（长期）：后端 `build_outlet_schema` 入口统一归一化 `result → products`（rows/features 两类统一为"产物行"），前端只传原始产物——但 Wave 1 双分支已够，统一化留后续。
- 细节：rows 分支需 `rows[0]` 为 dict、`field in rows[0]`；与 features 分支语义一致（Top-1）✓。

### 2. newLayerCount 门放宽 —— 合理，但需空 rows 守卫

- rows 型产物（rank 表/checkup 汇总·无图层）合法出卡，放宽到「有 rows 或 newLayerCount>0」合理——macro 诊断/排序卡本就是表形态，地理定位留 Wave 2。
- **必须**：`rows.length > 0` 才触发（空 rows = 分析失败，不应出卡）；`_maybeBuildOutletCard` 的产物收集对 rows 也走同一 `data.rows` 来源（工具返回结构，需确认 zonal/rank 工具在前端 data 里的键名——`data.rows`）。

### 3. DOMAIN_KW 补「体检」—— 对齐正确；'体检' 单词足够

- 对齐核验：checkup_dimension domain=urban_governance，B 部首中 → governance ✓；后端 TRIGGER_WORDS 已含体检，补词后出卡链路闭合。
- 误触发：'体验' **不含** '体检'（体+验 vs 体+检）✓；EMC 语境下'体检'即城市体检语境，风险低。
- '城市体检' 长词更精准但会漏"体检指标对接/体检四维度"类问句（不含"城市"前缀）——**建议用 '体检'**（覆盖广）；若后续实测出现误触发再加长词限定。
- **stages.js 无需改动**（已 import DOMAIN_KW 自动生效）——草案③ 的"同步 stages.js:423 B 部"可删。

### 4. checkup_dimension 四维度映射 —— 字段合理，**但缺 scale 过滤（P1）**

- 字段映射（住房=issue_label+place_name·小区=domain_top/element_top+polarity_index·街区=issue_label+polarity_index·城区=polarity_index+domain_top）均∈白名单且 zonal rows 实有 ✓。
- **P1 语义问题**：build_outlet_schema 的 field_mapping 循环**无 scale 感知**——macro 问句会把城区单元的值填入全部四槽（住房维度显示城区 issue_label = 误导）。修法（择一）：
  a. 槽位加 scale 限定（`{'住房维度': {'scale':'micro','fields':'...'}}`）→ 组装时仅填匹配槽，其余"需对应尺度分析"；
  b. Wave 1 先只映射"城区维度"槽（其余标注待对应尺度）。
- 细节：`+` 语法经 `split('+')[0]` 只取首字段（`build_outlet_schema.py:130`）——`issue_label+place_name` 实际只出 issue_label；place_name 精确源本属 Wave 2，可接受，但需知晓。

### 5. point_count 语义 —— 用 rows 求和保持"N=评论数"

- zonal rows **每行带 point_count**（prop_cols 含）→ 前端打包时 `point_count = rows.reduce((a,r)=>a+(r.point_count||0),0)` = 聚合评论总数，维持 `data_base.N` "评论数"语义（现有 note 'L2 聚合·时间窗待定' 不误导）。
- 仅当 rows 无 point_count 列时，退 `rows.length` 并在 note 标注"区域单元数（非评论数）"。

### 6. 测试方案 —— 够；补 scale 过滤断言

- 单测 rows 用例（renewal_object_identify + checkup_dimension）+ 浏览器 E2E 覆盖主线 ✓。
- 建议补：① `rows.length === 0` 不出卡用例；② 若采纳 P1 scale 过滤——断言 macro 问句卡中"住房/小区/街区"槽为"需对应尺度分析"而非城区值；③ `sum(point_count)` 用例。

### 7. 边界 —— 无越界 ✓

- 不碰 diagnose prompt / orchestrate 主循环 / ChatRequest schema ✓；改动面 = outlet_kb 字段映射 + build_outlet_schema 取值 + harness 产物收集 + emc-patterns 词表 + 测试。
- DOMAIN_KW 非 TRIGGER_WORDS → `validate_outlet_trigger_sync`（仅查 TRIGGER_WORDS ↔ OUTLET_TRIGGER_KW）不受影响 ✓。
- place_name 精确源留 Wave 2 ✓；CB-15 范围不触碰 ✓。

---

## 三、风险与优先级

| 级别 | 项 | 处理 |
|---:|---|---|
| **P1** | checkup_dimension 四槽 × 单尺度语义错位（macro 值入 micro/meso 槽） | 槽位 scale 限定或 Wave 1 只映射城区槽 |
| **P2** | rows 空数组出卡 | 加 `rows.length>0` 守卫 |
| **P2** | `+` 只取首字段（place_name 不随 + 出现） | 知晓即可·place_name 精确源 Wave 2 |
| **P2** | N 语义 | rows 求和 point_count；无列退行数+标注 |
| **P2** | stages.js 同步步骤冗余 | 删（自动生效） |

---

## 四、判定

- **草案可行**：7 处方向正确，三层断裂的修复路径成立（rows 分支 + 门放宽 + DOMAIN_KW 体检词 + 字段映射 + 测试）。
- **必须处理 1 项（P1）**：checkup_dimension 四维度 scale 语义——不处理会出现"住房维度填城区值"的误导卡（比"暂无数据"更差）。
- **3 个 P2 细节** + 1 处草案简化（stages.js 同步步可删）。
- **边界合规**：零承重触碰，Wave 2 边界清晰。

---

*本报告为 Codex 组独立评估；核验基于当前工作树逐行追查（触发链路 DOMAIN_KW→B 部→resolve_outlet_id→field_mapping 消费），未参考其他组报告。*
