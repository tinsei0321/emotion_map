# CB-23 grid色板+tip社区 · zcode评估（2026-08-12）

> 评估方：zcode（数据侧·前端只读）｜ 方法：只读 grid-tool.js/tip-popup.js/index.html
> 结论：**4要点全通过·2个优化建议**

---

## ① gridStyle palette/reverse参数化——与极性深读交互一致性

**结论：agree ✅（生成管线参数化完整·极性深读需确认是否同步palette/reverse）**

### 生成管线（完整参数化）
grid-tool.js 三处调用全传参：
- L341-342 readParams：`palette: sel.value / reverse: dataset.reverse==='1'`
- L428 square生成：`gridStyle(level, p.polarity, p.palette, p.reverse)`
- L443 zonal生成：同上
- L284 预览：`gridStyle(level, polarity, palette, reverse)`

→ **生成时 palette/reverse 正确传入** ✅

### ⚠️ 极性深读paint切换（L510）——未传palette/reverse

```javascript
// L510: 极性深读切换极性时重新paint
const style = gridStyle(p.level, p.polarity);  // ← 未传 p.palette / p.reverse
```

**问题**：用户在生成时选了 palette='diverging-rg' + reverse=true → 生成效果正确。但切换极性（如从"综合"切到"消极"）时，paint 切换调用 `gridStyle(p.level, p.polarity)` **不传 palette/reverse** → 回退到默认色板（POLARITY_RAMP）。

**影响**：
- 如果用户**只用默认色板**（palette=空）→ 无影响 ✅
- 如果用户**手选了palette或开了reverse** → 切换极性后色板回退到默认·**用户需重新选** ⚠️

**建议**（非阻塞·P2优化）：L510 改为 `gridStyle(p.level, p.polarity, p.palette, p.reverse)`——把当前 paint 参数也传给深读切换。需确认 p 对象在深读上下文中是否保有 palette/reverse（如不在·可从 _ui 或对话框状态读取）。

---

## ② 色板集选择（8项是否够）

**结论：agree ✅（8项够用·覆盖主要场景）**

### 色板清单（grid-tool.js L278）
```javascript
const KEYS = ['grid-warm', 'terrain-9', 'green-3', 'red-3', 'blue-3', 'diverging-rg', 'rainbow', 'orange-6'];
```

| 色板 | 用途 | 场景 |
|---|---|---|
| grid-warm | L1默认（低暗红→高金黄） | 12345投诉强度 |
| terrain-9 | L2综合默认（红绿发散） | 极性综合 |
| green-3 | L2积极 | 积极占比 |
| red-3 | L2消极 | 消极占比 |
| blue-3 | L2中性 | 中性占比 |
| diverging-rg | 红绿发散（备选） | 自选 |
| rainbow | 彩虹（连续） | 自选 |
| orange-6 | 橙色梯度 | L1备选 |

**评估**：8项覆盖了默认场景（4个极性专属）+ 自选场景（4个通用）——够用。**不建议增加**（过多色板反而增加用户选择负担）。如果后续有需求可加 `viridis`（科学可视化常用）或 `gray`（灰度打印）。

---

## ③ tip社区：性能·缓存·与地址重复

**结论：agree ✅（实现合理·3个细节确认）**

### 性能评估
```javascript
// fillCommunity：每次hover触发
loadCommunities().then((fc) => {
  for (const f of fc.features) {  // 193面遍历
    // pointInPolygon 射线法·单环~20顶点
  }
});
```

- **193面×~20顶点/面 = ~3860次比较/hover**——JavaScript 射线法在毫秒级完成 ✅
- **缓存**：`_commPromise` 懒加载+缓存（首次fetch·后续用 `_commFc`） ✅
- **与reverseGeocode并行**：同质心key触发·不阻塞 ✅

### ⚠️ 细节1：tp-community 位置

HTML顺序（index.html L1194-1195）：
```html
<div class="tp-row tp-loc" id="tp-loc"></div>          <!-- 地点（地址含街办） -->
<div class="tp-row tp-community" id="tp-community" hidden></div>  <!-- 社区 -->
```

**用户要求"街办与地点信息之间"**——当前社区行在地点行**之后**（下方）。如果"街办"在地点行内（如"宜昌市西陵区云集街办二马路社区..."），则顺序为：地点(含街办) → 社区 → ...

**建议确认**：用户要的是"街办行与地点行之间插入社区行"还是"地点行下方加社区行"？当前实现是后者（地点下方）。如果用户要前者，需调整HTML顺序为：街办 → **社区** → 地点。

### ⚠️ 细节2：社区与地址中的社区重复

地址（tp-loc行）可能已含社区名（如"宜昌市西陵区云集街办**二马路社区**覆元里..."）。fillCommunity 再显示"社区：二马路社区"——**信息重复**。

**建议**（非阻塞）：
- 方案A：fillCommunity 显示时检查 tp-loc 文本是否已含社区名·若含则隐藏 tp-community
- 方案B：保持现状（重复但确保信息完整·用户可自行判断）
- 当前实现是方案B·可接受

### ⚠️ 细节3：未命中隐藏

```javascript
elC.hidden = true;  // 未命中任何社区面时隐藏
```
配置库193社区覆盖22街办范围——**配置库范围外的点**（如12345中宜都市/当阳市的投诉）hover时 tp-community 隐藏·合理 ✅

---

## ④ 两需求与既有设计语言一致性

**结论：agree ✅（设计语言一致）**

### 色板一致性
- grid色板下拉复用 `HEATMAP_RAMPS`（与heatmap-tool共享色板定义） ✅
- 反向按钮（`⇅`）是简洁的icon toggle·与buffer-tool的`buf-cap`按钮风格一致 ✅
- 预览条（`hm-style-seg`）复用heatmap的色段预览组件 ✅

### tip一致性
- tp-community 行复用 `tp-row` + `tp-vk`(key) + `tp-vv`(value) 结构·与其他tip行（tp-loc/tp-metric/tp-size）一致 ✅
- hidden 默认 + 异步填充·与 tp-loc（reverseGeocode 异步）模式一致 ✅

---

## 总结

| 要点 | 结论 | 状态 |
|---|---|---|
| ① palette/reverse参数化 | **agree** | ✅ 生成管线完整·⚠️ 极性深读L510未传palette/reverse（P2优化） |
| ② 色板8项 | **agree** | ✅ 够用·覆盖4默认+4自选 |
| ③ tip社区 | **agree** | ✅ 性能OK(193面毫秒级)·缓存OK·⚠️ 位置/重复2细节确认 |
| ④ 设计语言一致 | **agree** | ✅ 色板/tip复用既有组件 |

### 2个优化建议（P2·非阻塞）
1. **极性深读L510传palette/reverse**：`gridStyle(p.level, p.polarity, p.palette, p.reverse)`——防切换极性后色板回退
2. **tip社区与地址重复检查**：fillCommunity 显示前检查 tp-loc 是否已含同名社区·避免重复

**红线核对**：✅ 只读本地不 git ｜ ✅ 未修改代码
