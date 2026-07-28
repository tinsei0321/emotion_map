# EMC 降智根因分析 — extract_feature 字段 MC 不存在

> **分析方**：DeepSeek V4 Pro（ZCode 主线程）  
> **日期**：2026-07-28  
> **触发用例**：「将中心城区中的西陵区裁剪出来」→ `extract_feature` 失败  
> **错误信息**：`过滤字段不存在: MC（可用: [('geometry', '?'), ('name', 'name')]…）`

---

## 一、根因摘要

> **`resolve_boundary` 将列名 "MC" 重命名为 "name"，但 `_apply_attr_filter` 仍引用原始列名 "MC"，导致字段名脱节。这不是孤立 bug，而是一类系统性缺陷模式：数据规范化层修改了列名，但下游消费者不知道这个修改。**

---

## 二、完整错误链（7 步·含 file:line 证据）

```
用户上传 GeoJSON: {type:"Feature", properties:{MC:"西陵区", ...}}
                          │
┌─────────────────────────┼─────────────────────────┐
│ 前端 (JS)                                  │ 后端 (Python)              │
│                                            │                            │
│ ① _fieldSamples() [tools.js:455]          │                            │
│   → getFieldCard() [tools.js:103]         │                            │
│   → profileFields(fc) 读 raw properties   │                            │
│   → resolveRole("MC") [field_dict.js:104] │                            │
│     = 'boundary_name' ✅                  │                            │
│   → 接地上下文含:                          │                            │
│   "字段:MC=s:?:西陵区|伍家岗区/name=..."   │                            │
│                                            │                            │
│ ② LLM (DeepSeek V4) 读取接地上下文          │                            │
│   → 选 extract_feature                    │                            │
│   → tool_calls[0].function.arguments:      │                            │
│     {"layer":"中心城区",                   │                            │
│      "where":{"field":"MC","op":"eq",      │                            │
│               "value":"西陵区"}}           │                            │
│                                            │                            │
│ ③ 前端校验 [tools.js:1004]                 │                            │
│   → getFieldCard(layerId, fc, 'polygon')   │                            │
│   → cards["MC"] 存在 ✅ → 校验通过         │                            │
│   (前端 GeoJSON 确有 MC 属性)              │                            │
│                                            │                            │
│ ④ ref("中心城区") [tools.js:180]           │                            │
│   → 返回 l.fc (完整 GeoJSON, 含 MC 属性)   │                            │
│   → generateExtractForAI → POST /geo/      │                            │
│     extract_feature                        │                            │
│                                            │                            │
│                                            │ ⑤ resolve_boundary()        │
│                                            │   [geo_registry.py:168-178] │
│                                            │   → GeoJSON→GeoDataFrame    │
│                                            │   → columns=[MC,geometry]   │
│                                            │   → 'name' not in columns   │
│                                            │   → find_boundary_name_     │
│                                            │     column(["MC","geo"])    │
│                                            │     [field_dict.py:248-260] │
│                                            │   → resolveRole("MC")=      │
│                                            │     'boundary_name'         │
│                                            │   → 返回 "MC"               │
│                                            │   ⚠️ polys.rename(           │
│                                            │     columns={"MC":"name"})  │
│                                            │   → columns=[name,geometry] │
│                                            │   ← MC 已消失!              │
│                                            │                            │
│                                            │ ⑥ _apply_attr_filter()      │
│                                            │   [geo_routes.py:71-80]     │
│                                            │   → field="MC"              │
│                                            │   → resolve_field_alias(    │
│                                            │     "MC",                   │
│                                            │     ["name","geometry"])    │
│                                            │   → "MC" 不在 columns 中!   │
│                                            │   → 无 alias 映射 "MC"→     │
│                                            │     "name"                  │
│                                            │   💥 ValueError:            │
│                                            │   过滤字段不存在: MC         │
│                                            │   (可用: [('geometry','?'), │
│                                            │    ('name','name')]…)       │
└────────────────────────────────────────────┴────────────────────────────┘
```

---

## 三、系统性缺陷分析

### 3.1 这不是一个孤立的 bug — 这是一类缺陷模式

核心矛盾：**管道上游做了数据规范化（列重命名），但下游消费者（字段引用方）不知道这个规范化。**

```
┌──────────────────────────────────────────────────────────┐
│              字段名规范化的断裂面                           │
│                                                          │
│  数据入口                   数据消费                      │
│  ┌──────────┐              ┌──────────────┐              │
│  │ resolve_ │  重命名      │ _apply_attr_ │              │
│  │ boundary │──MC→name──→? │   _filter    │              │
│  │          │              │              │              │
│  │ 知道改名 │              │ 不知道改名!   │              │
│  └──────────┘              └──────────────┘              │
│                                                          │
│  断裂面 = resolve_boundary 做了修改，                      │
│  但没有把修改告知下游                                      │
└──────────────────────────────────────────────────────────┘
```

### 3.2 受影响范围

`resolve_boundary` 在两处做列重命名：

| 路径 | 代码位置 | 重命名逻辑 |
|------|------|------|
| **Preset 路径** | `geo_registry.py:163-166` | `manifest.nameField` 指定的列 → `'name'` |
| **Send-in 路径** | `geo_registry.py:173-177` | `find_boundary_name_column()` 找到的列 → `'name'` |

`find_boundary_name_column` 可以匹配的列名（`field_dictionary.py:104`）：

```
MC、街道、社区、编号、区域名称、县名、市名、Layer、LAYER、
省、市、区、县、OBJECTID、FID、ID、行政区、行政区划
```

**所有**这些列名都可能触发同类 bug —— 只要 LLM 在接地上下文中看到它们并引用为 `where.field`。

当前明确受影响的端点：
| 端点 | 代码位置 | 影响 |
|------|------|:---:|
| `extract_feature` | `geo_routes.py:219-222` | 🔴 `_apply_attr_filter` after `resolve_boundary` rename |

潜在受影响端点（如果将来添加字段引用参数）：
| 端点 | 代码位置 | 风险 |
|------|------|:---:|
| `merge` | `geo_routes.py:246` | 🟡 如果按字段 dissolve |
| `area_stats` | `geo_routes.py:279,318` | 🟡 如果按字段 group_by |
| `overlay` | `geo_routes.py:362,452` | 🟡 如果按字段 join |

### 3.3 前端也在传播这个问题

前端的 `_fieldSamples()`（`tools.js:455-486`）展示原始字段名（如 "MC"）给 LLM，而 `_boundaryNames()`（`tools.js:515-539`）用 `/MC/i` 正则匹配原始列名。前端和后端各有一套列名认知，LLM 被夹在中间。

```
前端 _fieldSamples → LLM 看到 "MC" → 后端 resolve_boundary 改名 → 过滤失败
```

---

## 四、系统性修复方案

### 核心原则

> **数据规范化必须是透明的。下游消费者不应需要知道数据被如何规范化。**

### 方案 A：后端 — 过滤前规范化（防御性·最小改动·止血）

在 `_apply_attr_filter` 中增加列名规范化回退：

```python
# api/geo_routes.py _apply_attr_filter()
actual = resolve_field_alias(field, gdf.columns) if field else None
if not actual:
    # 字段可能已被 resolve_boundary 重命名（如 MC→name）——回退查找
    role = resolve_role(field) if field else None
    if role in ('boundary_name', 'land_use_class') and 'name' in gdf.columns:
        actual = 'name'
if not actual:
    avail = [(c, resolve_role(c) or '?') for c in list(gdf.columns)[:20]]
    raise ValueError(f'过滤字段不存在: {field}（可用: {avail}…）')
```

- ✅ 改动最小（3 行）
- ✅ 覆盖所有 `boundary_name` + `land_use_class` variants
- ✅ 不影响现有调用方
- ⚠️ 治标 — 只在 filter 层防御，不解决根本断裂

### 方案 B：后端 — 不改名列，加 name 副本（结构性·推荐·治本）

改变 `resolve_boundary` 的策略：**不再重命名原始列，而是添加 `name` 列作为副本**。

```python
# core/geo_registry.py resolve_boundary() send-in 路径 (line 168-178)
if isinstance(boundary, dict):
    feats = boundary.get('features') if isinstance(boundary, dict) else None
    if not feats:
        raise ValueError('boundary GeoJSON 无 features')
    polys = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
    # ⚠️ 改为 copy 而非 rename：原始列保留，name 列为副本
    if 'name' not in polys.columns:
        nf = find_boundary_name_column(polys.columns)
        if nf and nf != 'name':
            polys['name'] = polys[nf]  # 添加副本，不删原始列
    return polys
```

同样修改 preset 路径（`geo_registry.py:163-166`）：

```python
# 原代码：
# polys = polys.rename(columns={nf: 'name'})
# 改为：
if nf and nf != 'name':
    polys['name'] = polys[nf]  # 添加副本
```

- ✅ **彻底消除断裂** — 原始列 + `name` 列同时存在
- ✅ 下游消费者可用 `'name'`（便捷）或原始列名（兼容）
- ✅ 不影响现有调用方（`'name'` 列仍然可用）
- ⚠️ 微小内存开销（多一列字符串引用，GeoPandas 下几乎为零）
- ⚠️ 需同步修改 preset 路径

### 方案 C：全链路 — 字段名统一规范化层（系统级·长期）

建立前后端统一的字段名规范化协议：

1. **前端 `_fieldSamples`**：对 `boundary_name` / `land_use_class` role 字段，展示规范化名称（`name`），非原始列名
2. **后端 `_apply_attr_filter`**：同时接受原始字段名和规范化字段名
3. **后端新增工具函数** `normalize_field_ref(field, gdf_columns)` 集中处理全部字段名规范化

- ✅ 系统性根治 — 覆盖前后端全链路
- ✅ LLM 永远看到规范化名称
- ⚠️ 改动范围大 — 跨前后端
- ⚠️ 需要前后端同步部署

---

## 五、推荐实施路径

| 阶段 | 方案 | 目标 | 改动量 | 风险 |
|:---:|:---:|------|:---:|:---:|
| **立即** | A | 止血 — `_apply_attr_filter` 加回退映射 | ~5 行 | 极低 |
| **短期** | B | 治本 — `resolve_boundary` 改 rename 为 copy | ~10 行 | 低 |
| **中期** | C | 体系 — 全链路字段名统一规范化 | ~50 行 | 中 |

---

## 六、同类风险排查清单

执行以下检查可发现同类问题：

| # | 检查项 | 文件 | 状态 |
|:---:|------|------|:---:|
| 1 | `extract_feature` — `_apply_attr_filter` after `resolve_boundary` rename | `geo_routes.py:219-222` | 🔴 已确认 |
| 2 | `merge` — `by` 参数可能引用原始字段名 | `geo_routes.py:246` | ⬜ 待查 |
| 3 | `area_stats` — `group_by` 可能引用原始字段名 | `geo_routes.py:279` | ⬜ 待查 |
| 4 | 前端 `_fieldSamples` — polygon 层展示原始列名（如 MC）而非规范化名 | `tools.js:455` | ⬜ 待查 |
| 5 | 前端 `_boundaryNames` — 用 `/MC/i` 正则匹配原始列名 | `tools.js:534` | ⬜ 待查 |
| 6 | `zonal_stats` 输出 — 使用 `name` 列，但输入层可能已被重命名 | `geo_routes.py` | ⬜ 待查 |
| 7 | 其他调用 `resolve_field_alias` 引用 boundary 列名的代码 | 全局 | ⬜ 待查 |

---

## 七、相关代码位置索引

| 文件 | 行 | 作用 |
|------|:---:|------|
| `core/field_dictionary.py` | 102-105 | `boundary_name` role 注册，含 'MC' variant |
| `core/field_dictionary.py` | 248-260 | `find_boundary_name_column()` — 找名称列 |
| `core/geo_registry.py` | 163-166 | Preset 路径：`nameField` → rename |
| `core/geo_registry.py` | 168-178 | Send-in 路径：`find_boundary_name_column` → rename |
| `api/geo_routes.py` | 71-80 | `_apply_attr_filter()` — 崩溃点 |
| `api/geo_routes.py` | 198-219 | `extract_feature` 端点 — 调用链 |
| `api/geo_routes.py` | 106-119 | `_norm_where()` — where 参数解析 |
| `frontend/js/ai_qa/tools.js` | 455-486 | `_fieldSamples()` — 暴露原始字段名给 LLM |
| `frontend/js/ai_qa/tools.js` | 515-539 | `_boundaryNames()` — 用 `/MC/i` 正则匹配原始列名 |
| `frontend/js/ai_qa/tools.js` | 994-1019 | `extract_feature` 工具 — 前端校验 |
| `frontend/js/ai_qa/tools.js` | 169-191 | `ref()` — 层名→GeoJSON 解析 |
| `frontend/js/ai_qa/tools.js` | 562-641 | `buildContext()` — 接地上下文构建 |

---

> **归档信息**：`docs/catch-ball/emc-arch-deepdive/ROOTCAUSE_extract_feature_MC_2026-07-28.md`  
> **关联报告**：`AUDIT_COMPREHENSIVE_2026-07-28.md`（全局审计）、`SCAN_DeepSeek_04-glm-v3.md`（v3 修复审计）
