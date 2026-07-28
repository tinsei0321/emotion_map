# EMC 降智根因分析 — filter_attr 层引用幻觉

> **分析方**：DeepSeek V4 Pro（ZCode 主线程）  
> **日期**：2026-07-28  
> **触发用例**：先「生成 L2 情绪热力图」→ 再「进一步分析消极情绪点的分布」→ 第二次失败  
> **错误信息**：`[ERR] filter_attr 失败："未知点层 id: T3·综合·yichang_L2_T3_L2_result_geojson.geojson（可用：['yichang_l2_t1', 'yichang_l2_t2', 'yichang_l2_t3', ...]）"`

---

## 一、根因摘要

> **LLM 在接地上下文中看到多种层标识（展示名、预设 ID、文件名片段），但系统没有明确告知"哪个是有效的层引用"。LLM 自行拼凑了 `T3·综合·yichang_L2_T3_L2_result_geojson.geojson`（热力图展示名 + 源文件名片段），导致 `ref()` 无法解析、`resolve_points()` 将其当预设 ID 查询失败。**

这是**层引用歧义**的系统性问题：接地上下文混合了展示名、预设ID、文件名三类标识，LLM 无法区分哪个是有效的 `layer` 参数值。

---

## 二、完整错误链（6 步）

```
第一轮：用户「生成 L2 情绪热力图」
  │
  ├─ FC → density(polarity="overall") → 生成热力图
  │   结果层名: "T3·综合"（T3=数据时点·综合=overall 极性）
  │
  ▼
第二轮：用户「进一步分析消极情绪点的分布」
  │
  │  接地上下文（buildContext 输出）包含:
  │  ┌─────────────────────────────────────────────┐
  │  │ 宜昌 L2 · T3（中心城区情绪·末）(1234条,点层,  │  ← 展示名（来自 manifest）
  │  │   字段:polarity=s:polarity:overall|.../      │
  │  │        score=n:score:-2.0~2.0/...)          │
  │  │ T3·综合(567条,热力层)                        │  ← 热力图结果层展示名
  │  │                                             │
  │  │ EMC 分析能力（可生成·勿判缺数据需上传）：      │
  │  │ 密度热力图（2D 彩虹/3D·可按极性筛：综合/     │
  │  │ 积极/消极/中性）...                          │
  │  │ L2 已含 polarity... 要"消极/积极热力图"      │
  │  │ 直接生成（density.params.polarity=...）      │
  │  └─────────────────────────────────────────────┘
  │
  ├─[1] LLM 应选 density(polarity="negative") 直接出消极热力图
  │      （接地上下文明确写了"要消极热力图直接生成 density.polarity=negative"）
  │      ⚠️ 但 LLM 选了 filter_attr —— 多余的中间步骤
  │
  ├─[2] LLM 需要给 filter_attr 填 layer 参数
  │      看到上下文中有:
  │        - "T3·综合"（热力图名称·不是点层）
  │        - "宜昌 L2 · T3（中心城区情绪·末）"（展示名·不是预设ID）
  │      ⚠️ 不知道有效的 layer 值是预设 ID（如 yichang_l2_t3）
  │
  ├─[3] LLM 自行拼凑: "T3·综合" + "yichang_L2_T3_L2_result_geojson.geojson"
  │      → "T3·综合·yichang_L2_T3_L2_result_geojson.geojson"
  │      （LLM 看到的数据摘要或上下文某处含文件名片段，拼接到一起）
  │
  ├─[4] 前端 tools.js:filter_attr → resolvePointLayer({layer: "T3·综合·..."})
  │      → ref("T3·综合·yichang_L2_T3_L2_result_geojson.geojson")
  │      → 精确匹配失败 / 包含匹配失败 → 返回原始字符串
  │
  ├─[5] generateFilterForAI({layer: "T3·综合·yichang_L2_T3_L2_result_geojson.geojson", ...})
  │      → POST /geo/filter_attr
  │
  └─[6] 后端 resolve_points("T3·综合·yichang_L2_T3_L2_result_geojson.geojson")
         → 不是预设 ID → 💥 "未知点层 id"
         → 可用预设: ['yichang_l2_t1', 'yichang_l2_t2', 'yichang_l2_t3', ...]
```

---

## 三、系统性缺陷分析

### 3.1 三个层标识混在同一个上下文里，LLM 无法区分

| 标识类型 | 示例 | 来源 | LLM 能否用作 layer 参数？ |
|------|------|------|:---:|
| **预设 ID** | `yichang_l2_t3` | `geo_registry.py` manifest key | ✅ 可以 |
| **展示名** | `宜昌 L2 · T3（中心城区情绪·末）` | manifest `name` 字段 | ❌ `ref()` 可能找不到 |
| **结果层名** | `T3·综合` | 热力图工具自动生成 | ❌ 不是点层 |
| **文件名片段** | `yichang_L2_T3_L2_result_geojson.geojson` | 某处上下文泄漏 | ❌ 不是有效引用 |

**核心矛盾**：`buildContext()` 展示的是展示名（人类可读），但 `layer` 参数需要的是预设 ID 或可解析的层名。LLM 看到了展示名却不知道预设 ID，于是自行拼凑。

### 3.2 接地上下文没有"如何引用层"的指引

FC system prompt（`router.py:38-61`）只说：
```
f'## 数据上下文\n{req.context or "（无数据上下文）"}\n'
```

没有任何关于以下内容的说明：
- 层应该用预设 ID 引用（如 `yichang_l2_t3`）
- 层的展示名和预设 ID 的对应关系
- `layer` 参数为空时系统会自动选择默认层

### 3.3 LLM 选错了工具路径

接地上下文明确写了：
```
要"消极/积极热力图"直接生成（density.params.polarity=overall|positive|negative|neutral）
```

LLM 应该直接选 `density(polarity="negative")` 一步出图。但它选了 `filter_attr`（先筛选再出图），多了一步且引入了层引用问题。

这是一个**工具选择偏差**：当上轮已经用过 `density` 出综合热力图后，LLM 倾向于"换一个工具"来回答追问，而非"同一个工具换参数"。

### 3.4 `ref()` 无错误反馈

当前 `ref()` 对无法解析的引用：
```javascript
function ref(v) {
  ...
  return v;  // 原样返回，不报错
}
```

这导致无效的层引用静默传递到后端，后端才报错。前端失去了提前拦截和给出有用错误信息的机会。

---

## 四、受影响范围

这是一个**系统性缺陷**，影响所有需要 LLM 指定 `layer` 参数的工具：

| 工具 | layer 参数 | 受影响 |
|------|:---:|:---:|
| `density` | 隐式（`pickVisiblePointLayer`） | 🟢 不受影响（自动选层） |
| `hotspot` | 隐式 | 🟢 不受影响 |
| `rank` | 隐式 | 🟢 不受影响 |
| `zonal_stats` | 隐式 | 🟢 不受影响 |
| `filter_attr` | **LLM 可指定** | 🔴 **受影响** |
| `clip` | LLM 可指定 range | 🟡 类似风险 |
| `extract_feature` | LLM 可指定 layer | 🔴 **受影响** |
| `buffer` | LLM 可指定 | 🟡 类似风险 |
| `nearest` | LLM 可指定 | 🟡 类似风险 |

---

## 五、系统性修复方案

### 核心原则

> **接地上下文必须明确区分"展示名"和"可用引用"。工具描述必须告诉 LLM 如何正确引用数据层。**

### 方案 A：接地上下文增强（前端·推荐·治本）

在 `buildContext()` 中为每个层增加**可用引用**信息：

```javascript
// tools.js buildContext() 中 (line 576)
// 当前:
return `${l.name}(${cnt}条,${_kindTag(l)}...)`;

// 改进:
const refs = [];
if (l.presetId) refs.push(`id=${l.presetId}`);  // 预设 ID 可直接用于 layer 参数
if (l.name) refs.push(`name="${l.name}"`);        // 名称也可用于 ref()
return `${l.name}(${cnt}条,${_kindTag(l)}${refs.length ? ',引用:' + refs.join('|') : ''}...)`;
```

输出示例：
```
宜昌 L2 · T3（中心城区情绪·末）(1234条,点层,引用:id=yichang_l2_t3|name="宜昌 L2 · T3（中心城区情绪·末）",字段:polarity=...)
T3·综合(567条,热力层,引用:name="T3·综合")
```

- ✅ LLM 明确知道用 `id=yichang_l2_t3` 或 `name="T3·综合"` 作为 layer 参数
- ✅ 消除展示名和引用的歧义
- ✅ 改动集中在前端 `buildContext()` 一处

### 方案 B：System prompt 增加引用指引（后端·辅助）

在 FC system prompt 中增加层引用说明：

```python
# router.py fc_diagnose system prompt (line 38 后)
'## 层引用\n'
'数据上下文中的每个图层都有"引用"标注：\n'
'- id=xxx → 直接用作 layer 参数（如 id=yichang_l2_t3）\n'
'- name="xxx" → 直接用作 layer 参数（如 name="宜昌 L2"）\n'
'若不确定 layer 参数，留空使用默认层。\n'
'热力层不可用作 filter_attr/clip 的 layer——这些工具需要点层。\n\n'
```

- ✅ 给 LLM 明确的行为指引
- ✅ 防止 LLM 用热力层做 filter_attr

### 方案 C：`ref()` 增强错误反馈（前端·防御）

```javascript
function ref(v) {
  // ...现有解析逻辑...
  
  // 新增：无法解析时的结构化错误
  if (typeof v === 'string' && v && !v.startsWith('{')) {
    const all = getLayers().filter(...);
    const names = all.map(l => l.name).filter(Boolean);
    console.warn('[ref] 无法解析层引用:', v, '可用:', names.slice(0, 10));
    // 返回特殊标记，让调用方知道解析失败
    return { _unresolved: true, _raw: v, _available: names };
  }
  return v;
}
```

- ✅ 前端提前发现无效引用
- ✅ 提供可用的层名列表
- ⚠️ 需要调用方处理 `_unresolved` 标记

### 方案 D：工具选择偏差修正（System prompt）

在 system prompt 或工具描述中增加提示：

```
'## 追问处理\n'
'用户追问时优先考虑已有工具换参数（如 density.polarity=negative），'
'而非引入新工具（如 filter_attr + density）。减少中间步骤。\n'
```

- ✅ 减少不必要的工具链
- ✅ 降低层引用出错概率

---

## 六、推荐实施路径

| 阶段 | 方案 | 目标 | 改动量 |
|:---:|:---:|------|:---:|
| **立即** | A | 接地上下文加引用标注 | ~15 行 |
| **立即** | B | System prompt 加引用指引 | ~10 行 |
| **短期** | C | `ref()` 增强错误反馈 | ~10 行 |
| **短期** | D | 追问处理优化提示 | ~5 行 |

---

## 七、相关代码位置索引

| 文件 | 行 | 作用 |
|------|:---:|------|
| `frontend/js/ai_qa/tools.js` | 562-641 | `buildContext()` — 接地上下文构建（需加引用标注） |
| `frontend/js/ai_qa/tools.js` | 169-191 | `ref()` — 层引用解析（需增强错误反馈） |
| `frontend/js/ai_qa/tools.js` | 960-975 | `filter_attr` 工具 — 调用 `resolvePointLayer` + `ref` |
| `frontend/js/ai_qa/tools.js` | 666-670 | `resolvePointLayer()` — 从 params 取 layer 或自动选 |
| `ai_qa/router.py` | 38-61 | FC system prompt（需加引用指引） |
| `ai_qa/tool_contracts.py` | 259-275 | `filter_attr` 契约 — `layer` 参数 hint='默认 L2' |
| `core/geo_registry.py` | 32 | L2 数据预设：`yichang_l2_t3 → '宜昌 L2 · T3'` |
| `api/geo_routes.py` | 161-177 | `filter_attr` 端点 — `resolve_points(req.layer)` 崩溃点 |

---

> **归档信息**：`docs/catch-ball/emc-arch-deepdive/ROOTCAUSE_filter_attr_layer_hallucination_2026-07-28.md`  
> **关联报告**：`ROOTCAUSE_extract_feature_MC_2026-07-28.md`（同类根因·字段名规范化断裂）、`AUDIT_COMPREHENSIVE_2026-07-28.md`（全局审计）
