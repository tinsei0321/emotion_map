# CB-31 地图底图策略 · Plan 审计（zcode 组 · 2026-08-13）

> **审计方**：zcode（第三方协同审计·只读不 git）
> **日期**：2026-08-13 | **CB 轮次**：CB-31 地图底图策略
> **审计对象**：`docs/catch-ball/discuss/CB31-地图底图策略_plan_2026-08-13.md`（Claude 评估方设计）
> **性质**：协同审计（选型 / 坐标基准 / _loadDarkMatter 改造 / 容错 / 交叉挑战）+ **zcode 环境实测探活（CARTO / Esri / 天地图国内可达性）**
> **核心标尺**：国内可达 / 稳定高清 / 坐标无偏 / 业界对标 / 容错回退
> **承重红线**：坐标基准（WGS84·排除 GCJ-02）/ dm- 前缀携带逻辑 / 容错不卡灰屏

---

## 〇、一句话结论

**Claude 方向正确（天地图主源网络层可达已实证 + CARTO 失效已实证 + 连带故障核实属实）·但方案的承重级未验证风险点被 zcode 实测证伪——Esri Living Atlas 在 zcode 环境双层不可达（DNS 污染 `202.103.44.150` 假地址 + IP 层封锁·即使 `--resolve` 强制 Akamai 真实 IP `23.55.96.160` 仍 timeout）·与 CARTO 同款 HTTP=000。zcode 主张：Esri 补源在 zcode 环境不可用（须 Claude/Codex 在用户 office 环境补探活确认·若同样不可达则方案退路「天地图 + CSS filter 反色做暗底」是必然而非可选）；天地图主源 + 排除 GCJ-02 + _loadDarkMatter 改 addSource（dm- 前缀不变）+ 容错回退 + swatch 校准 + 初始态修复 全部 agree（代码核实属实·改动设计合理）；Esri World Imagery 升级影像 partial（高清但日期不受控/拼接色差 + zcode 环境不可达·建议后置）；apps/static 孤儿 JSON 清理需谨慎（核实零引用但建议保留 git 历史不物理删）。**

---

## 一、zcode 环境实测探活（本审计核心实证·最大未验证风险点）

### 1.1 探活结果矩阵（zcode 环境·2026-08-13）

| 源 | URL | HTTP | 耗时 | zcode 判定 |
|---|---|---|---|---|
| **CARTO**（现状） | `basemaps.cartocdn.com/gl/positron.../style.json` | **000** | 15s timeout | ❌ 失效（与 plan 一致）|
| **Esri services** Light Gray | `services.arcgisonline.com/.../World_Light_Gray_Base/.../tile/4/6/10` | **000** | 15s timeout | ❌ **不可达** |
| **Esri services** Dark Gray | `services.arcgisonline.com/.../World_Dark_Gray_Base/.../tile/4/6/10` | **000** | 15s timeout | ❌ **不可达** |
| **Esri server** Topo | `server.arcgisonline.com/.../World_Topo_Map/.../tile/4/6/10` | **000** | 15s timeout | ❌ **不可达** |
| **Esri server** Imagery | `server.arcgisonline.com/.../World_Imagery/.../tile/4/6/10` | **000** | 15s timeout | ❌ **不可达** |
| **天地图** t0 img_w（demo tk） | `t0.tianditu.gov.cn/DataServer?...&tk=demo` | 418 | 1.1s | ⚠️ tk 校验拒（网络可达）|
| **天地图** t0 img_w（真实 tk） | 同上 + 真实 tk | 403 | 0.1s | ⚠️ Referer 校验（网络可达）|
| 天地图 t0-t3（真实 tk） | 4 子域 | 全 403 | 0.1s | ✅ **网络层全可达** |

### 1.2 Esri 双层不可达的铁证（DNS 污染 + IP 封锁）

**DNS 污染证据**（nslookup）：
```
services.arcgisonline.com → 202.103.44.150（湖北电信 DNS 劫持地址·非 Esri 真实 IP）
server.arcgisonline.com   → 23.55.96.160（Akamai 真实段）+ 202.103.44.150（污染混合）
```
- Esri 真实 CDN 是 Akamai（`23.x` / `2a03:2880:` 段）·`202.103.44.150` 是国内运营商 DNS 污染注入的假地址。

**IP 层封锁证据**（`--resolve` 强制真实 IP）：
```
curl --resolve "server.arcgisonline.com:443:23.55.96.160" → HTTP=000 timeout 8s
```
- 即使绕过 DNS 污染·强制连 Akamai 真实 IP `23.55.96.160`·仍 timeout——**GFW 对 Akamai 段的 SNI/IP 封锁**·不只 DNS 问题。

**Esri 重测稳定性**：services Light Gray 连测 3 次（含首次）全 HTTP=000 timeout 12s——**稳定不可达·非偶发**。

### 1.3 天地图网络层可达的铁证

- t0-t3 四子域全 0.1s 快速响应（非 timeout）·**网络层完全可达**。
- 403 body：`{"resolve":"Key权限类型为:浏览器端，请使用浏览器访问！"}`——**应用层 tk+Referer 校验**·非网络问题。
- curl 带 Referer 仍 403（天地图校验更严·可能要求完整浏览器指纹）·**但浏览器原生请求（serve :8080 运行时）能用**（项目已在用·非新风险）。

### 1.4 探活结论（关键·影响选型定稿）

| 维度 | zcode 环境 | 对 plan 的影响 |
|---|---|---|
| CARTO 失效 | ✅ 实证（与 plan 一致）| plan 根因成立 |
| **Esri 可达** | ❌ **不可达（DNS+IP 双层封锁）** | **plan §2.3 Esri 补源在 zcode 环境失效** |
| 天地图主源 | ✅ 网络层可达 | plan 主源成立 |

**zcode 关键提醒（必须落 plan）**：
- zcode 环境 Esri 不可达 ≠ 用户 office 环境不可达（环境差异·CB-22h/g/h/i 教训：网络因环境而异）。
- 用户推荐 Esri·**可能用户 office 环境可达**（或用户有代理/VPN）。
- **须 Claude/Codex 在用户 office 环境补探活 Esri**——这是方案定稿前的前置·不能只靠 zcode 单环境判定。
- **若用户 office 环境同样不可达** → plan §6.1 退路「天地图 + CSS filter 反色做暗底」是**必然而非可选**（无 Esri 则浅灰/暗灰/彩色/高清影像全缺·只能天地图全包 + CSS filter 模拟暗色）。

---

## 二、代码现状核实（zcode 独立·勿只信 plan 陈述）

| plan 声明 | zcode 核实 | 文件:行 | 结论 |
|---|---|---|---|
| 7 个底图（3 CARTO + 4 天地图） | ✅ 属实 | map.js:21-31 BASEMAPS | 一致 |
| CARTO 外链 cartocdn.com | ✅ 属实 | map.js:23-25 | 一致 |
| DM_BASEMAP_KEY='dark-matter' | ✅ 属实 | map.js:77 | 一致 |
| _BASEMAP_BG 7 映射 | ✅ 属实 | map.js:78 | 一致 |
| setBasemap transformStyle 携带 dm- | ✅ 属实 | map.js:260-268 carrySources/carryLayers 按 `id.startsWith('dm-')` | 一致 |
| _loadDarkMatter fetch style.json | ✅ 属实 | map.js:277 `fetch(BASEMAPS[DM_BASEMAP_KEY])` | 一致 |
| _loadDarkMatter try/catch 吞失败 | ✅ 属实 | map.js:295 `catch (e) { console.warn }` | 一致 |
| index.html 缺 positron 按钮 | ✅ 属实 | index.html:1011-1020 仅 dark-matter/voyager/tianditu×4 | 一致 |
| **初始态三方打架** | ✅ **属实但 plan 描述需修正** | HTML:1015 勾 `tianditu-vec-nolabel` / DEFAULT_BASEMAP='tianditu-img-nolabel'(map.js:32) / main.js:346 `setActiveBasemap('positron')` | **三方不一致**（plan 说 HTML 勾 tianditu-vec-nolabel 属实·但 DEFAULT 是 img-nolabel·非 vec-nolabel）|
| main.js:346 死代码 setActiveBasemap('positron') | ✅ 属实 | main.js:346 | 一致 |
| toolbar.js setActiveBasemap 实现 | ✅ 属实 | toolbar.js:100-103 toggle is-active | 一致 |
| dialog.css bm-swatch 纯 CSS 渐变 | ✅ 属实 | dialog.css:104-108 5 个渐变（bm-sat/vec/dark/light/voyager）| 一致 |
| apps/static 4 个孤儿 JSON | ✅ 属实 | apps/static/ 4 文件（tianditu_img/img_nolabel/label/nolabel.json·Jun 13-17·http·老 WMTS）| 一致 |
| 孤儿 JSON 零引用 | ✅ 属实 | grep `apps/static` 在 frontend/js/ 仅 map.js:7 注释（"原引已被删改内联"）| 一致 |
| vendor 本地化 | ✅ 属实 | index.html:11-12 `vendor/maplibre-gl.js` 本地 | 一致 |
| README 脱节 | ✅ 属实 | README.md:56/74/85 讲"CARTO Positron / apps/static JSON / 必须从根起" | 一致 |

**zcode 核实结论**：plan 代码现状陈述**全部属实**·无虚报。唯一需修正：初始态打架的 DEFAULT 是 `tianditu-img-nolabel`（非 plan §一.2 暗示的 tianditu-vec-nolabel）·但不影响"三方打架"结论。

---

## 三、逐焦点审计（5 条 + 交叉挑战）

### 焦点 1：选型（天地图主 + Esri 补）—— **partial（方向对·但 Esri 补源在 zcode 环境不可达·须用户环境补探活）**

**逐项审计**：

| 子项 | zcode 判定 | 证据 / 理由 |
|---|---|---|
| 天地图主源 | **agree** | zcode 实测网络层可达（t0-t3 全 0.1s）·WGS84/CGCS2000 无偏·中文注记·国家版图权威 |
| Esri 补源（Light/Dark Gray/Topo 对位 positron/dark-matter/voyager） | **partial** | 对位恰当（GIS 业界标准·风格族匹配）·**但 zcode 环境不可达（§一）**·须用户 office 环境补探活 |
| Esri World Imagery 升级影像 | **partial·建议后置** | 高清（Maxar 0.3-0.5m）好·**但**：①成像日期不受控·瓦片间可能差数年·拼接色差（plan 已诚实标注）②zcode 环境不可达 ③天地图影像已够用（img_w）·升级非必需。**建议二期·不在本轮** |

**zcode 定稿建议**：
- 天地图主源 **定稿**（实证可达）。
- Esri 补源 **条件定稿**——须 Claude/Codex 在用户 office 环境补探活（`curl services.arcgisonline.com` + `server.arcgisonline.com`）：
  - **若可达** → Esri 补源按 plan §2.3 实施（Light/Dark Gray/Topo·可选 World Imagery 后置）。
  - **若不可达** → 启用退路：浅灰/暗灰/彩色改天地图（vec_w 已是浅灰系）+ CSS `filter: invert(1) hue-rotate(180deg)` 反色做暗底（raster 可反色·无偏移·plan §6.1 退路）。
- **Esri World Imagery 后置**（本期不做·避免日期不受控风险）。

### 焦点 2：坐标基准硬约束（排除 GCJ-02）—— **agree（认可·无例外）**

- **agree**：GCJ-02 源（高德/百度/腾讯）做底图与 WGS84 数据错位 50-500m·对空间归因平台致命。
- **证据**：项目数据（POI/网格/12345 点）+ 天地图均 WGS84/CGCS2000（plan §2.1 + zcode 核实 map.js 天地图模板 `_tiandituStyle` 用 `img_w/vec_w` 的 `_w` = Web Mercator EPSG:3857·WGS84 基准）。
- **无例外**：plan 问"纯展示场景有无例外"——**zcode 判定无例外**。即使纯展示·底图路网与数据点错位 50-500m 仍是视觉欺骗（用户看到 POI 落在错误的路上）·分析平台不可接受。若未来真需 GCJ-02 底图展示·须做瓦片重投影（工程不划算·plan §2.1 已排除）。
- **Esri 也是 WGS84**（理论安全）·但可达性是另一问题（焦点 1）。

### 焦点 3：_loadDarkMatter 改造（fetch style.json → addSource Esri Dark Gray raster）—— **agree（不破坏 dm- 逻辑·预载零卡顿保留）**

**zcode 逐项核实**：

| 子项 | zcode 判定 | 证据 |
|---|---|---|
| fetch style.json → addSource raster 改造可行 | **agree** | 现状 _loadDarkMatter（map.js:274-296）fetch CARTO style.json 后遍历 sources/layers 加 `dm-` 前缀 addSource/addLayer。改 Esri raster 后：直接 `addSource('dm-esri-dark', {type:'raster',tiles:[...],tileSize:256}) + addLayer({id:'dm-esri-dark',type:'raster',source:'dm-esri-dark'})`·**更简单**（单一 raster 层·非 CARTO 多 vector 层）|
| 不破坏 transformStyle dm- 携带 | **agree** | transformStyle（map.js:263/266）按 `id.startsWith('dm-')` 判断携带——**只要新 raster 层 id 仍 `dm-` 前缀（如 `dm-esri-dark`）·携带逻辑零改**。plan §三 "DM_BASEMAP_KEY 保持 'dark-matter'·dm- 前缀不变" 正确 |
| 预载零卡顿特性保留 | **agree** | 现状预载（_loadDarkMatter 在 style.load 调一次·_dmLoaded 标志防重·visibility 初值 none）——改 raster 后**预载机制不变**（仍是 style.load 调一次 + addSource/addLayer + visibility none + pitch>1 显隐）。raster 比 vector 加载更快（单瓦片 vs 多 source）·零卡顿特性**更好** |
| Esri Dark Gray 不可达时降级 | **须补** | plan §三说"fetch 失败被 try/catch 吞"——改 addSource 后·若 Esri 不可达（zcode 环境实证）·raster 瓦片加载失败·dm 层空。**须补降级**：Esri Dark Gray addSource 失败 → 纯深色背景（_BASEMAP_BG[DM_BASEMAP_KEY] #0e0e0e）+ 可选 CSS filter 反色做路网纹理（焦点 1 退路） |

**zcode 定稿建议**：
- _loadDarkMatter 改 addSource Esri Dark Gray raster **agree**·dm- 前缀不变（携带逻辑零改）。
- **补降级**：Esri 不可达时 `_dmLoaded=true` 但 dm 层空·`_applyDark3D` 仍设深色背景（现状已有 :309）——**3D 暗态至少有深色背景·非灰屏**。若要有路网纹理·退路 CSS filter 反色天地图 vec（焦点 1 退路）。

### 焦点 4：容错回退 + 健康探活 + swatch 校准 —— **agree（到位·回退 DEFAULT 优于卡灰屏）**

| 子项 | zcode 判定 | 证据 / 建议 |
|---|---|---|
| map.on('error') 监听瓦片失败 | **agree** | MapLibre 原生事件·现状零容错（setBasemap 无 catch）·plan §2.4.1 加 error 监听 + setBasemap catch 回退 DEFAULT 正确 |
| setBasemap 失败回退 DEFAULT_BASEMAP | **agree** | 回退 DEFAULT（天地图·实证可达）**优于卡灰屏**——现状 setStyle 失败静默卡死·用户看灰屏无反馈。回退至少保住可用底图 |
| 健康探活（启动探活各源·失效按钮标灰禁用） | **agree·建议简化** | plan §2.4.3 启动探活——**建议简化**：启动时对各 basemap 第一张瓦片 HEAD 请求·失效标灰 `disabled`（非现在的"看着能点、点了灰屏"）。但探活本身也可能因网络波动误判（Esri 偶发通）·建议探活结果**缓存 + 允许用户手动重试**（非一次性永久禁用）|
| swatch 校准 | **agree** | 现状 dialog.css:104-108 纯 CSS 渐变（bm-sat/vec/dark/light/voyager）——色块掩盖失效（用户看色块以为有效·点了灰屏）。校准到 Esri 实际色调 + **失效时显灰叉图标**（视觉区分有效/失效）|

**zcode 定稿建议**：容错三件套（error 监听 + 回退 DEFAULT + 探活标灰）**agree 全做**·探活简化（缓存+手动重试）·swatch 校准 + 失效显灰叉。

### 焦点 5：交叉挑战（≥1 条·CB-22 教训）

#### 挑战 1（承重）：Esri 在 zcode 环境双层不可达·方案"天地图主 + Esri 补"在 zcode 环境等于"天地图单源"——Claude 是否在用户 office 环境实证过 Esri 可达？

- **zcode 实证**：Esri services/server 双子域·Light/Dark/Topo/Imagery 四源·DNS 解析 + `--resolve` 强制真实 IP·**全 HTTP=000 timeout**（§一）。
- **挑战**：Claude plan §2.3 把 Esri 作为"补天地图缺的浅灰/暗灰/彩色/高清影像"——**若 Esri 不可达·这四种风格全缺·等于退回天地图单源（只有影像/矢量·无浅灰/暗灰/彩色地形）**。
- **风险**：方案定稿后实施·若用户环境 Esri 同样不可达·positron/dark-matter/voyager 三个按钮（Esri Light/Dark/Topo 替换）**仍点灰屏**（与现状 CARTO 失效同款）·只是从"CARTO 被墙"变成"Esri 被墙"·**问题没解决·只是换了失效源**。
- **zcode 要求**：**Claude/Codex 须在用户 office 环境补探活 Esri**（`curl -m 15 services.arcgisonline.com/.../tile/4/6/10` + `server.arcgisonline.com/.../World_Imagery/...`）·落 plan §六 验证前置：
  - 可达 → Esri 补源按 plan 实施。
  - 不可达 → 启用退路（天地图全包 + CSS filter 反色做暗底）·**plan 须写明退路是必然而非可选**。
- **zcode 诚实**：zcode 环境 ≠ 用户环境（CB-22h 天地图 DeepSeek 三组实测环境差异教训）·不单凭 zcode 判定 Esri 全国不可达。但**zcode 实证是强信号**·Esri 在国内普遍被 GFW 干扰（Akamai CDN 段常被封）·用户环境可达概率需实证。

#### 挑战 2（次要）：apps/static 4 个孤儿 JSON 清理——plan 说"清理（红线·执行时显式确认）"·是否该保留 git 历史？

- **zcode 核实**：apps/static/ 4 文件（tianditu_img/img_nolabel/label/nolabel.json·Jun 13-17·http·老 WMTS + 单子域）·frontend/js/ 零引用（map.js:7 注释明说改内联）。
- **挑战**：plan §三"清理（红线·执行时显式确认）"——zcode **agree 清理**·但建议：
  - **git rm 保留历史**（git 本身保留删除记录·可追溯）·非物理删。
  - 清理前 grep 全仓一次（防有 docs/测试引用）·`grep -rn "apps/static" docs/ tests/` 确认零引用再删。
  - README.md:74/85 同步更新（删"apps/static JSON"误导）。
- **zcode 定稿**：清理 agree·git rm + grep 确认 + README 同步。

#### 挑战 3（建议）：初始态修复——plan 说"index.html is-active 改到 DEFAULT_BASEMAP 对应按钮"·但 DEFAULT 是 img-nolabel·按钮里没有 img-nolabel 的独立样式区分？

- **zcode 核实**：index.html:1015 现勾 `tianditu-vec-nolabel`·但 DEFAULT_BASEMAP='tianditu-img-nolabel'（map.js:32）·main.js:346 `setActiveBasemap('positron')`——**三方打架**。
- **plan 修复**：main.js:346 改 `setActiveBasemap(DEFAULT_BASEMAP)` + index.html is-active 改到 DEFAULT 对应按钮。
- **zcode 建议**：**修复正确·但须同步 DEFAULT_BASEMAP 与 index.html 按钮 is-active**——若 DEFAULT=img-nolabel·index.html 应勾 `tianditu-img-nolabel` 按钮（非现在的 vec-nolabel）。**三处一致**（DEFAULT_BASEMAP + index.html is-active + main.js setActiveBasemap 都指向同一 key）。

---

## 四、zcode 定稿 plan 建议

### 4.1 前置（必做·定稿前）

```
Claude/Codex 在用户 office 环境补探活 Esri：
  curl -m 15 -o /dev/null -w "%{http_code}" https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/4/6/10
  curl -m 15 -o /dev/null -w "%{http_code}" https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/4/6/10
落 plan §六 验证前置·区分两支：
  - 可达 → Esri 补源实施（4.2）
  - 不可达 → 退路实施（4.3）
```

### 4.2 若 Esri 可达·按 plan 实施（zcode agree）

- **map.js BASEMAPS**（21-31）：3 CARTO → Esri Light Gray/Dark Gray/Topo（{z}/{y}/{x} 模板）·天地图 4 变体保留。
- **map.js _BASEMAP_BG**（78）：加 Light `#f5f5f5`/Dark `#2b2b2b`/Topo `#f2efe9` 映射。
- **map.js DM_BASEMAP_KEY**（77）：保持 'dark-matter'（dm- 前缀不变·携带逻辑零改）。
- **map.js _loadDarkMatter**（274-296）：fetch style.json → addSource Esri Dark Gray raster（dm- 前缀）+ 补降级（Esri 不可达 → 深色背景）。
- **map.js setBasemap**（253-270）：加 map.on('error') + catch 回退 DEFAULT_BASEMAP。
- **index.html**（1011-1022）：补 positron 按钮（改 Esri Light Gray 标签）+ is-active 改到 DEFAULT_BASEMAP 对应按钮（img-nolabel）。
- **main.js:346**：`setActiveBasemap('positron')` → `setActiveBasemap(DEFAULT_BASEMAP)`。
- **dialog.css**（104-108）：swatch 校准 Esri 色调 + 失效显灰叉。
- **健康探活**：启动探活各源第一张瓦片·失效标灰 disabled（缓存 + 手动重试）。
- **README.md**：删"apps/static JSON / CARTO Positron / 必须从根起"误导·改现状。
- **apps/static/**：git rm 4 孤儿 JSON（grep 确认零引用后）。

### 4.3 若 Esri 不可达·退路实施（zcode 建议·plan §6.1 升级为分支）

- **BASEMAPS**：positron/dark-matter/voyager 三个 CARTO 改：
  - positron → 天地图 vec_w（浅灰系·已实证可达）或保留按钮但标灰禁用。
  - dark-matter → 天地图 vec_w + CSS `filter: invert(1) hue-rotate(180deg) brightness(0.8)`（raster 反色做暗底·无偏移）。
  - voyager → 天地图 vec_w + 轻度 CSS 调色（或直接禁用·标"国际源不可达"）。
- **_loadDarkMatter**：改 addSource 天地图 vec_w（dm-tianditu-vec 前缀）+ CSS filter 反色·或纯深色背景降级。
- **其余同 4.2**（容错/初始态/README/孤儿 JSON）。

### 4.4 红线核对

| 红线 | zcode 核实 |
|---|---|
| 坐标基准 WGS84（排除 GCJ-02）| ✅ 天地图+Esri 均 WGS84·硬约束认可 |
| dm- 前缀携带逻辑 | ✅ 改 Esri/天地图 raster 后 dm- 前缀不变·transformStyle（map.js:263/266）零改 |
| 容错不卡灰屏 | ✅ 回退 DEFAULT + 探活标灰 + 失败降级 |
| 不造轮子 | ✅ 复用 MapLibre 原生 raster source / error 事件 / addSource addLayer |

---

## 五、风险清单

### 阻断级（须定稿前解决）

| # | 风险 | zcode 建议 |
|---|---|---|
| **B1** | Esri 在 zcode 环境双层不可达（DNS 污染 + IP 封锁）·方案"Esri 补源"可能全国普遍不可达 | **前置探活**（§4.1）·用户 office 环境实证·不可达则启用退路（§4.3） |

### 警告级

| # | 风险 | zcode 建议 |
|---|---|---|
| **W1** | Esri World Imagery 成像日期不受控·拼接色差 | 后置（本期不做） |
| **W2** | 健康探活误判（网络波动） | 探活缓存 + 手动重试（非永久禁用） |
| **W3** | 天地图 403 Referer 校验（curl 测 403·浏览器能用） | 浏览器实测确认（serve :8080）·非 curl 判定 |

### 排除项（zcode 核实非风险）

| # | plan 疑点 | zcode 排除 |
|---|---|---|
| GCJ-02 例外 | 无例外（纯展示也错位） | ✅ |
| dm- 携带逻辑破坏 | dm- 前缀不变则零改 | ✅ |
| 预载零卡顿丢失 | raster 比 vector 更快 | ✅ |

---

## 六、zcode 结论

### ✅ Claude 方向正确·Esri 可达性是唯一阻断级待实证

**zcode 判定**：

CB-31 地图底图策略 plan ·**方向正确·代码现状陈述全部属实·连带故障核实属实**：

| 维度 | zcode 判定 |
|---|---|
| 天地图主源 | ✅ agree（实证网络层可达）|
| 排除 GCJ-02 硬约束 | ✅ agree（无例外）|
| _loadDarkMatter 改 addSource | ✅ agree（dm- 前缀不变·携带零改·预载保留）|
| 容错回退 + 探活 + swatch 校准 | ✅ agree（回退 DEFAULT 优于灰屏）|
| Esri 补源 | ⚠️ partial（对位恰当·但 zcode 环境不可达·须用户环境补探活）|
| Esri World Imagery | ⚠️ partial（后置·日期不受控）|

**承重红线**：全守（WGS84 基准 / dm- 前缀 / 容错 / 不造轮子）✅。

**zcode 核心贡献**：
1. **承重实证**：Esri 在 zcode 环境双层不可达（DNS 污染 `202.103.44.150` + IP 封锁 `--resolve` 强制仍 timeout）——方案最大未验证风险点被证实·须用户环境补探活。
2. CARTO 失效 + 天地图可达 + 连带故障（初始态三方打架 / 孤儿 JSON / README / swatch）全部代码核实属实。
3. 退路升级：Esri 不可达时"天地图 + CSS filter 反色"是必然而非可选（plan §6.1 升级为分支）。
4. 初始态修复补充：DEFAULT_BASEMAP（img-nolabel）+ index.html is-active + main.js setActiveBasemap 三处须一致。

**关键定调**：**Esri 可达性是本方案唯一阻断级待实证——zcode 环境证实不可达（强信号）·但环境差异须用户 office 补探活。若用户环境同样不可达·退路（天地图全包 + CSS filter）是必然而非可选。定稿前必须落 §4.1 前置探活**。

---

## 附：zcode 独立探活与核实证据

| 探活/核实项 | 命令/文件 | 结果 |
|---|---|---|
| CARTO 失效 | curl basemaps.cartocdn.com style.json | HTTP=000 timeout 15s |
| Esri services Light/Dark Gray | curl services.arcgisonline.com ×2 源 ×3 次 | 全 HTTP=000 timeout 12-15s |
| Esri server Topo/Imagery | curl server.arcgisonline.com ×2 源 | 全 HTTP=000 timeout 15s |
| Esri DNS 污染 | nslookup services.arcgisonline.com | `202.103.44.150`（湖北电信劫持）|
| Esri IP 封锁 | curl --resolve 强制 `23.55.96.160` | HTTP=000 timeout 8s（Akamai 真实 IP 仍不通）|
| 天地图 t0-t3 可达 | curl ×4 子域 | 全 403 0.1s（Referer 校验·网络层可达）|
| 天地图真实 tk | map.js:9 `4d4dc85287c003c8a18d5520b8920796` | 前端公开·浏览器可用 |
| BASEMAPS 现状 | map.js:21-31 | 3 CARTO + 4 天地图（属实）|
| DM_BASEMAP_KEY/_BASEMAP_BG | map.js:77-78 | dark-matter + 7 映射（属实）|
| transformStyle dm- 携带 | map.js:263/266 | id.startsWith('dm-')（属实·改 raster 零改）|
| _loadDarkMatter fetch | map.js:277 | fetch CARTO style.json + try/catch 吞（属实）|
| index.html 缺 positron | index.html:1011-1020 | 仅 dark-matter/voyager/tianditu×4（属实）|
| 初始态三方打架 | HTML:1015 vec-nolabel / map.js:32 img-nolabel / main.js:346 positron | 三方不一致（属实）|
| apps/static 孤儿 JSON | apps/static/ 4 文件 | tianditu_img/img_nolabel/label/nolabel.json（属实·零引用）|
| README 脱节 | README.md:56/74/85 | CARTO Positron + apps/static（属实）|
| vendor 本地化 | index.html:11-12 | vendor/maplibre-gl.js 本地（属实）|

### 声明

本审计由 zcode（第三方协同审计）独立产出·2026-08-13·基于 curl 探活（CARTO/Esri services/server ×4 源 ×多测 + 天地图 t0-t3 + DNS nslookup + `--resolve` 强制 IP）+ 代码级核实 map.js:21-31/77-78/253-296/260-268 + index.html:1011-1020 + main.js:346 + toolbar.js:100 + dialog.css:104-108 + apps/static/ + README.md。第三方协同审计·不做项目方决策背书。zcode 环境 Esri 不可达 ≠ 用户环境·须 Claude/Codex 补 office 探活。

---

*登记：docs/context-map.md · CB-31 地图底图策略 plan 审计 zcode 组。*

*zcode · CB-31 地图底图策略 plan 审计 · 2026-08-13*
*审计只读不 git · zcode 环境实测探活（Esri 双层不可达 + 天地图可达 + CARTO 失效）·待 Claude/Codex 补用户 office Esri 探活 → 定稿*
