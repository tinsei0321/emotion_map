# CB-16 Wave 3 实施预检（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）  
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `0c9ba95`  
> **方法**：探索依据逐行核验（METRIC_MAPPINGS 表达式语义/单契约 resolve/CI 守卫范本/sjoin 范本）+ 消费链追查  
> **范围**：只读评估 · 不改代码 · 不 commit

---

## 结论摘要（先行）

**Wave 3 四子项草案可行。** 1 项 P1 设计要点（emc_field 表达式解析器）+ 2 项 P1 兼容/诚实要点 + 2 项 P2。  

- **【P1】可感知计算器需要专用表达式解析器（非复用 field_mapping 解析）**：METRIC_MAPPINGS 的 `emc_field` 含**条件语义**——`element_top=环境`（命中判定）、`topic_top（公园/绿地/散步）`（主题词提示）、`+` 组合、`综合` qualifier——比 build_outlet_schema 的纯取值解析复杂。**compute 与 validate_outlet_fields 必须共享同一 parser**（单一真相源·防漂移）。
- **【P1】多卡支持需兼容迁移**：`/outlet_card` 现返回单 `{card}`（`aiqa_routes.py:97-98`）——建议 `{cards:[...]}` 为主 + 保留 `card=cards[0]`（向后兼容 Wave 0/1/2 既有测试与前端），或全量同步更新消费方（一次性迁移）。
- **【P1】B 超距双态诚实**：`max_dist_m=1000` 超阈值时 `nearest_poi_name` 置空（不误导"2km 外也叫关联"）+ dist 保留或标注。
- **【P2】多卡上限/去重**（多 domain 命中 ≤3 卡防刷屏）；METRIC_MAPPINGS 消费字段入 `_EMC_FIELDS` 白名单同步。

---

## 一、探索依据核验

| 依据 | 核验 |
|---|---|
| 可感知 10 项 METRIC_MAPPINGS | ✅ `urban_checkup_outlets.py:58-117`·`emc_field` 表达式含 `field=value` 条件 / `field（hint）` 提示 / `+` 组合 / qualifier——**非纯取值** |
| **METRIC_MAPPINGS 消费方** | ✅ 全仓 rg 无消费（outlet_kb_brief_text 只渲染 OUTLET_CONTRACTS）——10 项当前是**纯数据孤儿**·compute 是让它活化的新增 |
| resolve_outlet_id 单契约 | ✅ `build_outlet_schema.py:27-75` 最高分单 oid·`build_outlet_schema` 单卡·`/outlet_card` 返回 `{card}` |
| validate_outlet_trigger_sync AST 范本 | ✅ `tests/validate_outlet_trigger_sync.py` AST 解析 py/js 词表比对——validate_outlet_fields 同模式（tests/ 静态守卫） |
| sjoin_nearest 范本 | ✅ `geo_routes.py:613` + `_attach_poi_attrs`（4546 米制·rtree） |

---

## 二、四子项预检

### 1. B 评论↔POI（attach_nearest_poi）—— 对路（P1）

- `sjoin_nearest(points, pois, distance_col)` 4546 米制 ✓（/geo/nearest + _attach_poi_attrs 既有模式）；rtree·4310×N 毫秒级 ✓。
- 落新列 `nearest_poi_name`/`nearest_poi_dist_m` ✓（禁覆盖 area_seed/spatial_hotspot·与 P1 预检一致）；运行时附加不改 CSV ✓。
- **P1 诚实**：`max_dist_m=1000` 超阈值 → `nearest_poi_name` 置空 + dist 保留（或标注"超 1km"）——防"2km 外最近 POI 也叫关联"误导。

### 2. 可感知计算器（compute_perceptible_metrics）—— 需专用解析器（P1）

- **表达式语义**：`element_top=环境`（条件：命中判定 + 值=该字段）·`topic_top（公园/绿地/散步）`（值 + 命中关键词标注）·`+` 组合（值 join·命中=任一元）·`综合` qualifier。**build_outlet_schema 的 main_field 解析只取值·不处理 `=`/`（）`——不能直接复用**。
- **P1 设计**：新增 `outlet_kb/metric_expr.py`（或并入 build_outlet_schema）小解析器：`field` | `field=value` | `field（hint）` | `+` join·输出 `{fields, conditions, hints, qualifiers}`——**compute 与 validate_outlet_fields 共享**（单一真相源·防两处解析漂移）。
- 计算输出 `[{metric, value, source, industry}]`：值=字段值（条件命中才报）/ 主题关键词标注 / 缺失 → '暂无数据' + source='缺失·不编造' ✓；落点 `card.perceptible_metrics`（扩展字段·不破既有）✓。
- METRIC_MAPPINGS 是既有资产（10 项表达式已写）——只增 parser 不改数据 ✓。

### 3. validate_outlet_fields CI —— 对路（P1·随 parser 落地）

- 仿 validate_outlet_trigger_sync：tests/ 静态守卫·AST/解析提取 field_mapping + emc_field 消费字段集 → 对比聚合产物实际字段集。
- "死字段"（产物有·无消费）/ "缺消费"（消费引用·产物无）判定合理——**产物字段白名单需定义**：静态字段（place_name/poi_names/polarity_index/...）+ 动态前缀（`n_dom_*`/`n_elem_*`）·或对齐扩展后的 `_EMC_FIELDS` 白名单（P2：METRIC_MAPPINGS 消费字段同步入白名单）。
- **P1**：消费字段提取用 metric_expr parser（共享）·防 validate 与 compute 解析不一致。

### 4. 多卡支持 —— 对路（P1 兼容迁移）

- `resolve_outlet_id` → `resolve_outlet_ids`（按 score 降序·多契约命中）·`build_outlet_schema` → 多卡·`/outlet_card` → `{cards}`。
- **P1 兼容**：保留 `card=cards[0]`（首卡·既有测试/前端零破坏）或全量同步更新消费方；前端 `renderOutletCard` 循环（单卡路径不变）。
- **P2**：多卡上限/去重（多 domain_lens 问句如"更新+体检"复合→≤3 卡·防刷屏）。

---

## 三、七问速答

1. **B 对路**：sjoin_nearest 性能无虞·新列不覆盖·超距双态诚实（P1）。
2. **计算器需专用解析器**（=条件/（）hint/+ 组合·P1）·输出确定性·缺失诚实；落点 perceptible_metrics 合理。
3. **validate CI 对路**（tests/ 静态·AST 同模式）；死字段/缺消费判定需产物白名单（静态+动态前缀）·与 compute 共享 parser（P1）。
4. **多卡对路**但需兼容迁移（{cards}+{card} 或全量同步·P1）；既有单卡用例需同步或兼容。
5. **范围**：B + compute = Wave 3 核心（下钻链收尾 + 满意度指标演示）；validate CI 随 parser 落地低成本高价值；**多卡可 P1b 后置**（单卡已演示·多卡是增强）。P2/P3（lookup 集成地理定位/节流/拓扑）后置清晰 ✓。
6. **测试**：attach_nearest_poi（命中/超距/空点）·compute（条件命中/缺失/组合）·validate（死/缺）·多卡（双 domain 双卡/单卡兼容）——够；补 parser 边界（`=` 不匹配·`（）` 空 hint）。
7. **承重零触碰**：diagnose/harness/ChatRequest 不动·确定性组装不变·build_outlet_schema 扩展兼容单卡·新 track ID（compute F_* 连续）✓。

---

## 四、优先级

| 级别 | 项 |
|---:|---|
| **P1** | emc_field 表达式解析器（compute + validate 共享·=条件/（）hint/+ 组合）·B 超距双态诚实·多卡兼容迁移（{cards}+{card}） |
| **P2** | 多卡上限/去重·METRIC_MAPPINGS 消费字段入 _EMC_FIELDS 白名单·产物字段白名单（静态+动态前缀）定义 |
| **范围建议** | B + compute + validate CI 先行（Wave 3 核心）·多卡可 P1b 后置 |

---

## 五、判定

- **Wave 3 草案可行**：四子项方向正确·消费链清晰（METRIC_MAPPINGS 活化/单卡→多卡/CI 守卫/评论关联收尾）。
- **P1 三项**：表达式解析器（共享）·B 超距诚实·多卡兼容迁移。
- **P2 三项**：多卡上限·白名单同步·产物字段集定义。
- **边界合规**：零承重触碰·确定性组装不变·范围清晰（多卡可后置）。

---

*本报告为 Codex 组独立评估；探索依据逐行核验（emc_field 条件语义/METRIC_MAPPINGS 无消费方/单卡端点/AST 守卫范本/sjoin 模式），未参考其他组报告。*
