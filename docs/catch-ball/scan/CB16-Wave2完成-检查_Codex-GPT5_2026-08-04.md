# CB-16 Wave 2 / CB-15 数据认知 P0 实施后检查（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）  
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `49e0e71`（Wave 2 commit `623e293`）  
> **方法**：commit diff 逐行核验 + 实跑单测 + 去重逻辑定向实测 + 端点契约与聚合产物追查  
> **范围**：只读评估 · 不改代码 · 不 commit

---

## 结论摘要（先行）

**Wave 2 / CB-15 P0 通过。** 4 环节全部落地且核心正确：3220 接入实锤（all_pois=4310·实测）、双模式 place_name（polygon 保边界名 / grid POI 最近质心）、place_name_source 兜底链、/geo/grid_pois 双参数确定性；单测实测 **53 passed（16+37）**。  
**1 项 P1 需修 + 2 项 P2：**
- **【P1】`_dedup_pois` 逻辑缺陷（实测确认）**：`_dup = _nm in _seen` 名字快检短路——**同名异址（连锁店）第二条被误删**（定向实测：同名异址 → 1 条·注释意图"名同址异是两条"未达成）；coord 容差 30m 是**死代码**（coord 检查只在首现名时执行·永远为空操作）。修复：改为"同名 **且** 坐标<30m 才去重"联合判定（去掉 `_seen` 快检或改为 name+coord 双键）。
- **【P2】cell_id 半实现**：`/geo/grid_pois` 端点收 `cell_id`（`grid_{size}_{row}_{col}`），但 `create_square_grid` **未输出 cell_id 列**——前端需自算或走质心路径。建议补聚合输出列（CB-15 P0 定项）。
- **【P2】测试补 3 边界**：空 POI 格（place_name_source fallback）、grid place_name 覆盖断言、**去重连锁店用例**（正是缺陷处·当前测试未覆盖）。

---

## 一、4 环节核验

| 环节 | 落地核验 | 判定 |
|---|---|---|
| ① `_read_pois_geojson` + _load 合并 + `_dedup_pois` | ✅ FC 适配（geometry→lng/lat·category→baidu_level1·keyword→baidu_level2·district→area·domain/element 空已 docstring 标注）·_load 合并 3220·**all_pois=4310 实测** | 正确（**去重逻辑有缺陷**·P1） |
| ② `_attach_poi_attrs` 双模式 | ✅ polygon 保留边界名 + poi_names/poi_count 增强（source=poi_top_places）·grid place_name=最近质心 POI（source=poi_sjoin）·sjoin 列名冲突修复（poly_ 前缀·防 name_left/right 冲突） | 正确 |
| ③ `_attach_4x5_attrs` place_name_source 兜底 | ✅ hotspot/area_seed/empty 三态标注·POI 覆盖后改写——可追溯链完整 | 正确 |
| ④ `/geo/grid_pois` | ✅ cell_id/质心双收·row/col floor 与 create_square_grid 同源（确定性）·返回 {cell_id,pois,count} rows 风格·缺参 400 | 正确（cell_id 聚合侧未输出·P2） |
| ⑤ 测试 | ✅ 5 新增（3220 接入/centroid/cell_id/缺参/polygon 属性）+ geocode limit 200→1000 | 覆盖主线（缺 3 边界·P2） |

---

## 二、七问逐答

### 1. `_read_pois_geojson` 适配正确 ✓（1 个标注建议）

- geometry→lng/lat ✓（实测 lng>100）；category→baidu_level1、keyword→baidu_level2、district→area ✓；domain/element 空且 docstring 已标注 ✓。
- **建议**：输出侧（grid_pois 响应/聚合 poi_names）对 3220 POI 的 domain/element 空值也标"待 L4/规则补"（防下游把空当"无归因"误判）。

### 2. `_dedup_pois` **有缺陷（P1·实测确认）**

- 保先序 ✓（1270 在前·重复去后序）；name 归一化（空格/全角括号）✓。
- **缺陷**：`_dup = _nm in _seen` 先短路——同名第二条直接丢弃，coord 检查只对"名首现"执行（永远空操作）→ **coord 容差 30m 是死代码**；同名异址（连锁店分支）被误删。定向实测：`[同名A@(111.29,30.70), 同名A@(111.42,30.78)]` → 去重后 1 条（注释意图应 2）。
- **修复**：`_dup = (name 归一相等) and (坐标<30m)` 联合判定（或按 poi_id 精确去重——3220/1270 同源 poi_id·比 name+coord 更稳）。影响：连锁店分支丢失 → place_name/poi_names 精度略降（非崩溃）。

### 3. `_attach_poi_attrs` 双模式正确 ✓

- polygon 保留边界名（place_name 不动）+ POI top_places ✓——与预检 P1 语义分层一致；grid POI 最近质心（几何确定性·`min(_recs, key=distance)`）✓。
- sjoin 列名冲突修复完整（poly 非 geometry 列统一 `poly_` 前缀·poi 侧 name 无冲突）✓。
- stats 位置对齐（reset_index + index_right + iloc 同序）✓。

### 4. place_name_source 兜底链正确 ✓

- 链：`poi_sjoin`（grid POI 覆盖）→ `poi_top_places`（polygon 增强）→ `spatial_hotspot`/`area_seed`（4x5 标注·`_place_src` 精确到字段）→ `empty`（`.where` 兜底）✓；空格无 POI → 标注兜底保留 ✓。

### 5. `/geo/grid_pois` 契约合理 ✓（cell_id 聚合侧待补·P2）

- cell_id 确定性（row/col floor 与 create_square_grid 同源·TestClient 验证 centroid→cell_id→cell_id 复用同 count）✓；质心兜底 ✓；返回 rows 兼容（name/category/domain/element/lng/lat）✓；缺参 400 ✓。
- **P2**：create_square_grid 未输出 cell_id 列——前端点击格子需自算 `grid_{size}_{row}_{col}` 或传质心；建议补列（CB-15 P0 定项·顺带本轮）。
- LLM 用法：P1 lookup_place 之前，前端点击先用（悬停/点击范式）；可选轻量工具后置。

### 6. 测试覆盖基本够；补 3 边界（P2）

- 已覆盖：3220 接入（count≥3000/字段映射/reverse 命中）·端点双路径（centroid/cell_id 同 count）·缺参 400 · polygon poi 属性列。实测 53 passed。
- **缺**：① 空 POI 格（fallback 链）② grid place_name 覆盖断言（最近质心·source=poi_sjoin）③ **去重连锁店**（正是 P1 缺陷处·当前测试无同名异址用例）。

### 7. 承重零触碰 ✓

- place_layer/geocode 只增不改（新增适配/合并/去重·既有 forward/reverse 语义不变）；聚合层 fallback 保旧 sim 数据兼容（hotspot/area_seed 路径保留）；53 passed 零回归佐证。不碰 diagnose/harness/ChatRequest。

---

## 三、端到端验证

| 项 | 结果 |
|---|---|
| `pytest test_spatial_analysis + test_geocode` | ✅ **实测 53 passed（16+37）** |
| 3220 接入 count | ✅ **实测 all_pois=4310**（yichang_pois=3220·去重 187） |
| grid_pois 端点 | ✅ TestClient 实测：centroid 200 出格 + cell_id 复用同 count（"count=32 CBD" 为 claude组 具体值·测试断言结构与一致性） |
| 去重连锁店 | ❌ 实测误删（同名异址→1 应 2）·P1 |
| 浏览器「大南门有哪些地点」 | 待 claude组/用户环境（本机 py 占位符环境限制·同前） |

---

## 四、判定

- **Wave 2 / CB-15 P0 通过**：4 环节核心正确、3220 接入实锤（4310）、双模式 place_name 与 source 链完整、端点确定性、单测全绿。
- **P1（1 项）**：`_dedup_pois` 连锁店误删（coord 容差死代码）——改 name+coord 联合判定（或 poi_id 去重）。
- **P2（2 项）**：create_square_grid 补 cell_id 输出列；测试补 3 边界（空格 fallback / grid place_name 覆盖 / 去重连锁店）。
- **边界合规**：零承重触碰；P1（lookup_place/归因落点）P2（节流/拓扑）后置清晰。

---

*本报告为 Codex 组独立评估；单测实跑 + commit diff 逐行核验 + 去重逻辑定向实测（连锁店误删已复现），E2E 浏览器受本机 py 占位符限制未重跑，未参考其他组报告。*
