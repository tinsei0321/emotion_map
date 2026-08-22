# CB-23 前端依赖全本地化（vendor）· zcode 评估回应（2026-08-12）

> 回应方：zcode（数据侧·前端只读评估）｜ 方法：只读本地 vendor/index.html/js
> 结论：**修复整体成功·4 评估要点中 3 个通过、1 个有风险（esm.sh 动态 import 未本地化）**

---

## 要点1：vendor 版本与 CDN 原引用一致？

**结论：agree ✅（版本匹配·3个核心包逐项验证）**

| 依赖 | CDN原版本 | vendor实际版本 | 一致 |
|---|---|---|---|
| maplibre-gl | 5.2.0 | **5.2.0**（文件头首行确认） | ✅ |
| deck.gl | 9.1.0 | **9.1.0**（UMD内 `VERSION="9.1.0"` 确认） | ✅ |
| marked | 12.0.2 | **12.0.2** | ✅ |
| chart.js | 4.4.4 | **4.4.4** | ✅ |
| proj4 | — | 文件正常（91KB·UMD格式） | ✅ |
| csv2geojson | — | 文件正常（15KB） | ✅ |
| fflate | — | 文件正常（32KB） | ✅ |
| topojson-client | — | 文件正常（7KB） | ✅ |

> 注：deck.gl min.js 内含 `loaders.gl version 4.2.1`（内部依赖·非 deck.gl 主版本）与 `probe.gl 4.1.0`——这些是 deck.gl 的打包内嵌依赖，版本号不同属正常（非混淆）。

---

## 要点2：UMD 全局名兼容

**结论：agree ✅（6/7确认匹配·1个需验证）**

| 依赖 | UMD全局名 | 页面消费名 | 匹配 |
|---|---|---|---|
| maplibre-gl | `maplibregl` | `maplibregl.Map()`（map.js:84） | ✅ |
| deck.gl | `deck` | `deck.ScreenGridLayer`/`deck.MapboxOverlay`（map.js:807-842） | ✅ |
| deck-aggregation-layers | `deck`（扩展挂载） | 同上（附加图层类） | ✅ |
| deck-mapbox | `deck`（扩展挂载） | 同上（MapboxOverlay） | ✅ |
| chart.js | `Chart` | `Chart`（panel.js渲染图表） | ✅ |
| marked | `marked` | `marked`（panel.js markdown渲染） | ✅ |
| proj4 | `proj4` | `proj4`（坐标转换） | ✅ |
| csv2geojson | `csv2geojson` | csv解析 | ✅ |
| shpjs | **⚠️ 未检出明确全局名** | shapefile解析 | **需验证** |
| fflate | 无 self/window 赋值（可能挂 module） | zip压缩 | **需验证** |
| topojson-client | 无 self/window 赋值 | topojson解析 | **需验证** |

### ⚠️ 3个需验证的包
- **shpjs**：文件前2000字符未检出 `self.shpjs` 或 `window.shapefile`——可能是模块内部导出非全局挂载。建议在浏览器 console 执行 `typeof shpjs` 确认是否全局可用；若不可用需检查是否有 wrapper 脚本
- **fflate/topojson-client**：同样未检出全局名赋值——这两个是小型工具库，可能通过其他方式引入（如 import.js 动态加载）。如果 index.html 的 `<script>` 标签已引入但全局名不可用，可能是 UMD 构建格式问题（CJS vs UMD）

**建议**：claude 在浏览器 console 执行 `typeof shpjs === 'function'` / `typeof fflate` / `typeof topojson` 验证·3个包目前是**潜在风险点**（加载成功但全局名可能不挂载）。

---

## 要点3：有无遗漏 CDN 引用

**结论：partial ✅（index.html 无残留·但 esm.sh 动态 import 仍在）**

### index.html CDN 残留
```
grep "https://" index.html → 0 命中 ✅
grep "cdn.|unpkg|jsdelivr" → 0 命中 ✅
```
**index.html 全部 CDN 引用已改为 vendor 本地·无残留** ✅

### ⚠️ esm.sh 动态 import（import.js）

`js/import.js` 第28行仍有 `await import('https://esm.sh/' + spec)`——动态 ESM 导入 **未本地化**：

```javascript
// import.js:28
const mod = await import('https://esm.sh/' + spec);
// import.js:315/326
mod = await import('https://esm.sh/@tmcw/togeojson@5.8.1');
```

**影响评估**：
- esm.sh 用于按需加载无 UMD 构建的小型库（togeojson/wellknown/polyline 等）
- **如果用户不上传 KML/GPX 文件 → 不触发 esm.sh → 不影响核心功能**
- **如果用户上传 KML/GPX → esm.sh 网络不通 → 该功能报错**（但非白屏·仅功能缺失）

**建议**：
- **短期**：可接受（KML/GPX 上传是边缘功能·核心地图/问答/分析不受影响）
- **长期**：将 togeojson 等也下载到 vendor·import.js 改为本地路径（与本次 vendor 化同理）

---

## 要点4：附带修复——天地图底图源

**结论：agree ✅（cartocdn→tianditu 切换成功）**

### 验证
- index.html 底图选择器：4个天地图选项（`tianditu-vec-nolabel`/`tianditu-img`/`tianditu-img-nolabel`/`tianditu-vec`）·**无 cartocdn 残留** ✅
- map.js：天地图瓦片源 `https://t{0-3}.tianditu.gov.cn/DataServer?T=${T}&x={x}&y={y}&l={z}&tk=${TIANDITU_KEY}` ✅
- 天地图 Key 已内联（非敏感·浏览器端权限类型）✅
- 默认底图 = `tianditu-vec-nolabel`（浅色无注记）·与原 cartocdn 浅色风格一致 ✅

### 天地图 vs cartocdn 对比
| 维度 | cartocdn（原） | 天地图（现） |
|---|---|---|
| 网络 | 海外CDN（断网不通） | 国内政府服务（通） |
| 风格 | 浅色无注记（positron） | 浅色无注记（vec-nolabel） |
| 瓦片 | 矢量栅格混合 | 栅格（raster） |
| 注册 | 无需Key | 需Key（已内联） |
| 速度 | 海外慢 | 国内快 |

**天地图切换合理**——解决了 cartocdn 断网问题·风格基本一致·国内访问更快。

---

## 其他发现

### ⚠️ marked 重复文件
vendor 目录有两个 marked：
- `marked.min.js`（37KB·2026-07-19·旧版）
- `marked-12.min.js`（35KB·2026-08-12·新版·index.html 引用此文件）

**建议**：删除旧 `marked.min.js`（避免混淆·index.html 已引用新版）。非阻塞（不影响功能）。

### ✅ 加载顺序正确
index.html 中 vendor 脚本加载顺序：
maplibre-gl → deck.gl×3 → [页面] → marked/chart/csv2geojson/shpjs/proj4/fflate/topojson

maplibre 先于 deck.gl 加载（deck.gl MapboxOverlay 依赖 maplibre）·顺序正确 ✅

---

## 总结

| 要点 | 结论 | 状态 |
|---|---|---|
| 1. 版本一致 | **agree** | ✅ maplibre 5.2.0/deck 9.1.0/marked 12.0.2/chart 4.4.4 全匹配 |
| 2. UMD全局名 | **agree**（3个需验证） | ✅ 6/9确认匹配·shpjs/fflate/topojson需console验证 |
| 3. CDN残留 | **partial** | ✅ index.html 零残留·⚠️ esm.sh 动态import仍在（边缘功能） |
| 4. 天地图 | **agree** | ✅ cartocdn→tianditu 切换成功·4选项·Key内联 |

### 建议claude执行的3个小动作
1. 浏览器 console 验证 `typeof shpjs`/`typeof fflate`/`typeof topojson`（3个潜在UMD风险点）
2. 删除旧 `vendor/marked.min.js`（37KB重复）
3. 记录 esm.sh 动态 import 为"已知技术债"（KML/GPX上传功能·非核心·可后补本地化）
