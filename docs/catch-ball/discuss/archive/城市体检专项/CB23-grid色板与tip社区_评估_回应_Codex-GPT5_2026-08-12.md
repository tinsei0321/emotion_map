# CB-23 两需求实现评估 · grid 色板增强 + tip 社区字段（Codex + GPT-5）

> **评估方**：Codex（GPT-5）| **日期**：2026-08-12 | **性质**：需求 1（grid 色板 palette/reverse 参数化）+ 需求 2（tip 社区字段·配置库 193 社区射线法）实现评估（只读本地·不 git）
> **实读**：grid-tool.js gridStyle/readParams/生成传参/深读调用（510/528）·renderRampPreview·tip-popup.js loadCommunities/pointInPolygon/fillCommunity/reverseGeocode·index.html tip 模板（tp-loc → tp-community 顺序）

---

## 〇、一句话结论

**两需求实现方向正确（gridStyle 参数化 ✓·tip 社区 fetch 193 面缓存 ✓）·4 项评估 2 agree + 2 partial——2 项 P1/P2 修正 + 2 项建议：① gridStyle palette/reverse 与极性深读交互不一致——**生成传参 ✓（square/zonal 两处 428/443）·但深读调用（510/528）`gridStyle(p.level, p.polarity)` 未传 palette/reverse·点图后极性深读 paint 切换回默认色板（用户选的新色板不保持）**——建议深读传参一致；② 色板 8 项 agree（覆盖 L1 强度/L2 极性/发散/彩虹·HEATMAP_RAMPS 同源）·P2 可加单色连续 + rainbow 防误用标注；③ tip 社区 partial——`loadCommunities` 缓存 193 面 ✓ 但 **`fillCommunity` 无「质心→社区」结果缓存（每 hover 遍历 193 面·建议 Map 缓存含未命中）**·`_locLine` 高德地址社区 vs 配置库社区可能不一致（配置库权威·标注）·**模板顺序 community 在 tp-loc 后·需求「街办与地点之间」应移到 loc 前**；④ 设计语言 agree（HEATMAP_RAMPS 同源·tp-row 统一悬停卡）。**

---

## 二、逐项评估

### ① gridStyle palette/reverse 参数化 · 与极性深读交互

**结论：partial（生成一致·深读未传参·交互不一致）**

**一句话证据**：gridStyle(level, polarity, palette, reverse)（72-88）·readParams 加 palette/reverse（341-342）·生成传参 square/zonal（428/443）·renderRampPreview 同步（272-287）✓；**但极性深读调用（510/528）`gridStyle(p.level, p.polarity)` 未传 palette/reverse**——用户选「terrain-9 + 反向」生成图层后·点图极性深读（paint 就地切换）回默认色板（不保持用户选择）。

**定稿建议**：
1. **深读传参**：510/528 改为 `gridStyle(p.level, p.polarity, p.palette, p.reverse)`（与生成一致·深读保持用户色板/反向）；
2. 或深读明确「默认色板」并在 UI 标注（若设计意图是深读复位）——建议前者（一致性优先）。

### ② 色板集（8 项）

**结论：agree（覆盖充分·HEATMAP_RAMPS 同源）+ P2 观察**

**一句话证据**：8 项 = 自动/grid-warm（L1 默认）/terrain-9（L2 综合）/green-3/red-3/blue-3（极性）/diverging-rg（红绿发散）/rainbow——覆盖强度/极性/发散/彩虹·与 heatmap 共用 HEATMAP_RAMPS ✓。

**P2 建议**：
1. 可加单色连续（Blues/Purples/Greys 3 项·Chroma 风格）——用户要「灵活调节」·单色连续补足（可选）；
2. **rainbow 标注「非极性语义」**（CB-04 教训：rainbow 曾致「消极热力图出综合彩虹图」）——下拉加注释防误用。

### ③ tip 社区（fetch 193 面 + 射线法）

**结论：partial（fetch 缓存 ✓·3 处补强）**

**一句话证据**：loadCommunities 缓存 193 面（_commFc/_commPromise 一次性 fetch）✓·pointInPolygon 射线法正确（外环 contains）·fillCommunity 未命中隐藏 ✓；但 **fillCommunity 无「质心→社区」结果缓存**——每 hover 触发后遍历 193 面（防抖内·但高频 hover + 大面层）·建议 `Map<key, name>` 缓存（含未命中 null·与 reverseGeocode cache 同模式）；**_locLine 高德地址社区 vs 配置库社区可能不一致**（高德行政社区 vs 体检 193 口径）——配置库权威·显示冲突时社区行优先 + 标注来源；**模板顺序**：index.html 1194-1195 tp-loc 在 tp-community 前——用户需求「街办与地点信息之间」应 community 在 loc 前（街办在 loc 地址文本内·社区行插 loc 前=街办与地点之间）。

**定稿建议**：
1. fillCommunity 加结果缓存（质心 key → 社区名·含未命中）·避免每 hover 193 面遍历；
2. 模板顺序 tp-community 移到 tp-loc 前（符合「街办与地点之间」）；
3. 社区行标注「配置库体检口径」·与高德地址社区冲突时社区行优先。

### ④ 设计语言一致性

**结论：agree（一致）**

**一句话证据**：grid 色板下拉/反向按钮复用弹窗控件风格·色板与 heatmap 共用 HEATMAP_RAMPS（同源）·tip 社区行复用 tp-row/tp-vk/tp-vv 样式（统一悬停卡）✓。

---

## 三、结论

**两需求实现达标（gridStyle 参数化 + tip 社区 fetch 缓存方向正确）·4 项评估 2 agree + 2 partial——修正清单：① 深读传参 palette/reverse（P1 交互一致）② fillCommunity 结果缓存（P2 性能）③ 模板顺序 community 移 loc 前（P2 需求语义）④ 社区行权威标注（P2）·色板加单色连续 + rainbow 标注（P2 可选）**。

---

## 四、红线核对

| 红线 | 核对 | 状态 |
|---|---|---|
| 生成/深读一致 | 生成 ✓·深读未传参 | ⚠️ P1 |
| 色板与 heatmap 一致 | HEATMAP_RAMPS 同源 | ✅ |
| tip 性能 | fetch 缓存 ✓·结果缓存待加 | ⚠️ P2 |
| 社区口径 | 配置库 193 权威·标注 | ✅ |

---

*Codex（GPT-5）· 两需求实现评估 · 2026-08-12 · 只读本地不 git · 回应落 discuss/ · P1（深读传参）+ P2（结果缓存/顺序/标注）修正后收口*
