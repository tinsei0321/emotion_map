# EMC 数据识别体系 — 现状分析与重构讨论

> **讨论发起**：用户 | **日期**：2026-07-29 | **主题**：EMC 数据识别架构重构
> **关联**：CB-09 发现（接地上下文缺语义标注 / 层引用歧义）

---

## 一、现状剖析：当前架构到底长什么样

### 1.1 数据在 EMC 中的全生命周期

```
┌─ 数据进入 ─────────────────────────────────────────────────────┐
│                                                                 │
│  预设数据                      用户上传                         │
│  geo_registry.py               import.js                        │
│  resolve_points(id)            parseCSV / parseGeoJSON          │
│  resolve_boundary(id)          → normalizeFC()                  │
│       │                             │                          │
│       └──────────┬──────────────────┘                          │
│                  ↓                                             │
│   addLayer({id, name, kind, fc, colorMode, ...})               │
│   state.js — 全局 _layers Map                                  │
│                                                                 │
├─ 数据识别 ──────────────────────────────────────────────────────┤
│                                                                 │
│   getFieldCard(layerId, fc)                                     │
│   tools.js:103                                                  │
│   ├─ resolveRole(field) ── 0LLM 规则（field_dictionary.js）     │
│   │   33 角色 × ~190 variants，精确+大小写匹配                   │
│   └─ fetchProfileFields() ── Flash LLM 推断（规则 miss 时）     │
│       → 返 {field: {role, dtype, samples, source, confidence}} │
│                                                                 │
├─ 数据感知 ──────────────────────────────────────────────────────┤
│                                                                 │
│   buildContext()                  harness.js: layerMeta         │
│   tools.js:562                    {has_point, has_polygon}      │
│   ├─ _fieldSamples() ── 字段摘要                                │
│   ├─ _boundaryEnum() ── 面层子要素枚举                          │
│   ├─ 数据内容摘要 ── 字段值域                                    │
│   └─ 分析能力清单                                                │
│                                                                 │
│   ↓ 注入 FC system prompt 的「数据上下文」                       │
│                                                                 │
├─ 数据引用 ──────────────────────────────────────────────────────┤
│                                                                 │
│   LLM 选 tool + 填 layer 参数                                    │
│   → ref(layerName) ── tools.js:169                              │
│       ├─ $n 引用（第 n 个工具产物）                              │
│       ├─ 精确名称匹配                                            │
│       ├─ 唯一包含匹配                                            │
│       └─ 原样返回（作 preset_id 送后端）                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 当前的数据分类现状 — 混乱点

**问题 1：预设 vs 上传在代码中无显式边界**

| 数据来源 | 如何进入 | 如何标识 | LLM 能看到区别吗？ |
|------|------|------|:---:|
| 系统预设（L2 情绪点） | `geo_registry.py` preset → `resolve_points(id)` | 无标记 | ❌ 无法区分 |
| 系统预设（行政区划） | Range 面板加载 → `addLayer()` | 无标记 | ❌ 无法区分 |
| 用户上传（GeoJSON） | `import.js` → `parseGeoJSON()` → `addLayer()` | 无标记 | ❌ 无法区分 |
| 用户上传（CSV） | `import.js` → `parseCSV()` → `addLayer()` | 无标记 | ❌ 无法区分 |
| EMC 工具产物 | `addResultLayer()` / `_adoptToolboxResult()` | 无标记 | ❌ 无法区分 |
| 手动绘制 | `addLayer()` | 无标记 | ❌ 无法区分 |

所有数据进入 `_layers` Map 后，**没有任何字段区分来源**。`buildContext()` 把它们全部等價列出。这就是 CB-09 C2（"我上传了哪些数据"）答错的根因。

**问题 2："指定范围"面板是目前唯一的预设概念**

Range 面板（`core/geo_registry.py` + `frontend/js/range-presets.js`）有 `list_boundaries()` → 返预设列表（id + name + available）。但：
- 这个"预设"概念仅用于面板 UI，**未接入 EMC 数据管线**
- `buildContext()` 不知道某个层来自 Range 预设
- `resolve_boundary(id)` 加载的层与用户上传的层在 `_layers` 中无法区分

**问题 3：数据识别分散在 4 个环节、缺乏统一入口**

| 环节 | 做什么 | 谁在做 | 是否有统一抽象 |
|------|------|------|:---:|
| 导入时 | 解析格式、推断 kind/colorMode | `import.js` | ❌ |
| 字段识别 | 推断字段 role | `getFieldCard()` → `field_dictionary.js` | ❌ |
| 接地上下文 | 描述数据给 LLM | `buildContext()` | ❌ |
| 层引用 | 解析 LLM 的层引用 | `ref()` | ❌ |

这四个环节各自独立，没有共享的"数据身份"概念。

---

## 二、逐一回应你的三点理想/预期

### 2.1 预设 vs 临时 — 需要显式的数据来源标记

> "预设通常是标准数据，如行政区划、用地权属、用地性质等偏官方的一定周期内的固化数据。临时数据为用户手动上载。区分预设或上传，是开发者/工程人员/后台决定的，不是靠LLM或数据内容等方式"

**当前状态**：❌ 未实现。所有层在 `_layers` 中无来源标记。

**推荐方案**：在 `addLayer()` 时增加 `source` 字段

```javascript
// state.js addLayer()
const SOURCE = {
  preset_boundary: '系统预设·边界',     // Range 面板加载的行政区划
  preset_point: '系统预设·点数据',      // L1/L2 情绪点
  user_upload: '用户上传',              // import.js 导入
  emc_tool: 'EMC 分析产物',             // density/extract_feature 等产出
  manual_draw: '手动绘制',              // draw-tool
};
```

每个层携带 `source` 字段。`buildContext()` 展示给 LLM：

```
中心城区行政区划(5条,面层·boundary首选·来源:用户上传,含:西陵区/...)
宜昌 L2 · T3(1234条,点层·来源:系统预设·点数据,字段:polarity=...)
T3·综合(567条,热力层·来源:EMC分析产物)
```

**LLM 就能准确回答"你上传了中心城区行政区划"而非"你没有上传任何数据"。**

### 2.2 统一数据注册表 — 强烈建议建立

> "建立一个显化的'数据库'，对每个上传（包括预设+临时）、EMC处理生成（包括中间产物）以及手动绘制的所有数据建立'唯一身份id串'"

**当前状态**：⚠️ 部分存在但不完整

EMC 内部已有两个接近"注册表"的概念：

| 现有机制 | 覆盖范围 | 缺失 |
|------|:---:|------|
| `_layers` Map（state.js） | 所有地图图层 | 无"数据来源"字段 |
| `_registry` 数组（tools.js:154） | EMC 工具产物 | 不含用户上传层、预设层 |
| `_fieldCardCache` Map（tools.js:104） | 字段识别缓存 | 仅字段信息，不含元数据 |
| `_stepResults` 数组（tools.js:148） | 工具产物 fc | 仅 GeoJSON，不含元数据 |

**没有一个统一的地方可以查到"当前有哪些数据、来源是什么、有什么字段"。**

**建立统一注册表的必要性**：✅ **非常必要**

理由：

1. **去重**：同一数据不会重复加载。当前 `addLayer()` 不做去重，同一文件拖两次 → 两个层。

2. **避免缓存污染**：当前 `_fieldCardCache` 用 `layerId` 作 key，layerId 是自增序号。层移除后 cache 不清理，新层可能命中旧缓存。

3. **LLM 接地质量**：统一注册表 → `buildContext()` 从单一来源读取 → 信息一致、不遗漏。

4. **调试可观测**：当前排查"为什么 LLM 说没数据"需要追 4 个环节。统一注册表 → 一个 `console.table(registry)` 看清全部。

5. **预设管理**：预设数据注册表可以标记"可用/不可用"（文件是否已上传），Range 面板直接读注册表而非手维护列表。

**推荐的注册表结构**：

```javascript
// DataRegistry（模块级单例）
{
  "L001": {
    id: "L001",                    // 唯一 ID（自增或 UUID）
    name: "中心城区行政区划",
    source: "user_upload",         // preset_boundary | preset_point | user_upload | emc_tool | manual_draw
    kind: "polygon",
    fc: {...},                     // GeoJSON FeatureCollection（或 lazy ref）
    fields: {                      // 从 getFieldCard 缓存
      "MC": { role: "boundary_name", dtype: "str", samples: [...] },
      ...
    },
    createdAt: 1722230400000,
    parentId: null,                // EMC 工具链：来源层 ID
    toolChain: [],                 // 产生此层的工具链
    hash: "a1b2c3...",             // fc 内容哈希（去重用）
  },
  ...
}
```

### 2.3 字段识别+提取+生成新数据 — 部分必要

> "能够识别+提取。识别数据id、数据类型、数据内的字段，提取数据内的字段，并生成新的数据文件+id"

**逐项分析**：

| 能力 | 当前实现 | 是否必要 | 说明 |
|------|:---:|:---:|------|
| **识别数据 ID** | ❌ 无统一 ID | ✅ **必要** | 见 §2.2 |
| **识别数据类型** | ⚠️ `kind` 字段（point/polygon/heatmap） | ✅ 已有但不完整 | 缺 group/line/raster 等细分 |
| **识别数据内字段** | ✅ `getFieldCard()` | ✅ 已有 | 0LLM 规则 + Flash LLM 推断 |
| **提取字段值** | ✅ `_fieldSamples()` / `_boundaryEnum()` | ✅ 已有 | 用于接地上下文 |
| **生成新数据文件+ID** | ⚠️ EMC 工具产物有 `_adoptToolboxResult()` | 🟡 **部分必要** | 见下方详析 |

**关于"生成新数据文件+ID"的分析**：

当前 EMC 工具（density、extract_feature 等）产出的结果图层已经落地到 `_layers` 和 `_registry`，有 `layerId`。但是：

- ✅ **生成 ID**：已实现（`addResultLayer` 分配 layerId）
- ❌ **持久化**：图层存在于内存（`_layers` Map），刷新页面后消失。用户无法"保存提取结果"
- ❌ **导出**：没有"将 EMC 提取的西陵区面导出为 GeoJSON 文件"的功能

**建议**：生成 ID（已有）是必要的；持久化+导出是 P2 功能（当前阶段不紧急，但注册表设计时预留接口）。

---

## 三、当前架构的问题根源

### 不是"混乱"，是"演进式生长"导致的自然碎片化

EMC 的数据管线经历了 v1→v2→v3 迭代，每个阶段加了新机制但未统一抽象：

```
v1 时期：addLayer() → _layers → 基础渲染
v2 时期：+ getFieldCard() → _fieldCardCache → buildContext()
v3 时期：+ _registry → _stepResults → _adoptToolboxResult
当前：   四套机制并存，无统一入口
```

**核心矛盾**：`_layers`（state.js）管渲染，`_registry`（tools.js）管工具链，`_fieldCardCache`（tools.js）管字段识别，`geo_registry.py`（后端）管预设——**四种数据视角，没有一种能完整回答"现在有哪些数据、从哪来的、有什么字段"。**

---

## 四、重构建议：三步走

### Phase 1：统一注册表 + 数据来源标记（~100 行·最大影响）

1. 新建 `frontend/js/data_registry.js` — 统一数据注册表
2. 所有 `addLayer()` 调用前先在注册表登记
3. 注册表携带 `source` 字段
4. `buildContext()` 从注册表读取（而非从 `_layers` 遍历）
5. `getFieldCard()` 结果缓存到注册表（替代 `_fieldCardCache`）

### Phase 2：预设数据接入注册表（~50 行）

1. `geo_registry.py` 的预设列表同步到前端注册表
2. 预设数据标注 `source: 'preset_boundary'` / `source: 'preset_point'`
3. Range 面板从注册表读取可用预设列表

### Phase 3：字段提取+导出能力（~80 行）

1. 注册表支持字段查询 API（`getFields(layerId)`）
2. "提取数据"功能：从层中选择字段→生成新的数据层（带新 ID）
3. 导出 GeoJSON/CSV（利用现有 import.js 的反向能力）

---

## 五、讨论点

### D1：注册表应该放前端还是后端？

- **前端**：即时响应、LLM 接地上下文即时可用。但刷新丢失。
- **后端**：持久化、跨会话存在。但每次 `buildContext()` 需要 HTTP 往返。
- **混合**：前端为主（热数据），后端持久化为辅（冷数据）。推荐此方案。

### D2：唯一 ID 用什么？

- 自增序号（当前 `layerId`）：简单但不跨会话唯一。
- UUID：跨会话唯一但不可读。
- 语义 ID（如 `user_upload/中心城区行政区划/2026-07-28`）：可读但可能冲突。
- **推荐**：`{source}/{short_hash}/{timestamp}` — 可读+去重+跨会话唯一。

### D3：注册表是否应该替代 `_layers`？

不。`_layers` 是 MapLibre 的渲染层管理，注册表是数据元信息管理。两者共存：注册表管"有什么数据"，`_layers` 管"怎么渲染"。注册表中的一个数据条目可能对应 0 个或 1 个 `_layers` 条目（用户可能关闭眼睛）。

---

## 六、与 CB-09 发现的对齐

CB-09 的两个 CRITICAL 发现（接地上下文缺语义标注 / LLM 推理螺旋）都与数据识别架构直接相关：

| CB-09 发现 | 根因 | 本讨论的解决方案 |
|------|------|------|
| LLM 不知道哪些是用户上传的 | buildContext 不区分来源 | 注册表 `source` 字段 |
| LLM 拼凑无效层引用 | buildContext 不标注可用引用 | 注册表统一 ID → buildContext 展示 |
| LLM 推理螺旋 | 信息缺失触发 | 完整注册表 → 完整接地 → LLM 无需猜 |
| "我上传了哪些数据"答错 | 同上 | 同上 |
| 无法去重 | addLayer 无去重 | 注册表 hash 去重 |

---

> **归档信息**：`docs/catch-ball/arch/DATA_RECOGNITION_ANALYSIS_2026-07-29.md`
> **下一步**：用户确认方案 → 进入实施阶段