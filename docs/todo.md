# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

---

## 📅 2026-06-28（周日）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 空间分析 P0 后端地基 | `core/spatial_analysis.py` `core/buffer_analysis.py` `api/routes.py` `api/schemas.py` `tests/test_spatial_analysis.py` `requirements.txt` | create_square_grid(F_006, snap-to-grid 4546→4326)；/spatial/aggregate + /spatial/grid(hex\|square)；h3+httpx 补装；F_005 补登；10 测试全过；hotspot/moran+PySAL 延后 P4 |
| 2 | ✅ | Grid工具5项修复+vibe策略 | `frontend/js/{map,grid-tool,sidebar,state}.js` `frontend/index.html` `~/.claude/CLAUDE.md`(新) | ①3D图层自动pitch55+暗色底图(dark-matter),2D复原原底图(setView3D+_pre3dBasemap记忆) ②图例linear-gradient→分段span(复用.legend-heat-seg) ③green-3/red-3/blue-3拉大对比(浅淡深深) ④2D透明度统一控件(fill-opacity读_ui.extrusionOpacity,2D/3D同滑块) ⑤要素按钮原地更新(editLayerId分支;按钮生成→调整) ⑥录入全局CLAUDE.md:调动次数优先(不派subagent/批量并行/合并修改) |
| 3 | ✅ | Grid视角/图例/透明度/2D-3D视图按钮(4项) | `frontend/js/{map,map-controls,grid-tool,sidebar}.js` | ①3D生成不跳视角:fitBounds后设pitch=60+style.load防setStyle吞+与map-controls统一 ②L2综合图例labels=消极/中性/积极(单色/热度=低/高) ③2D首次透明根治:grid paint显式fillOpacity=extrusionOpacity绕开addLayer默认0.3 ④2D/3D视图按钮(btnView)一键切换:setViewMode按数据签名配对独立层(无配对则同fc生成,渲染独立)+pitch+Light/Dark底图+generateGrid不再独占关grid层 |
| 4 | ✅ | Grid视图切换两下+独占修复(2项) | `frontend/js/{map,grid-tool}.js` | ①2D/3D切换要点两下:setView3D的once(style.load)race→第一下pitch回调没挂上(底图已切),第二下底图已dark跳过setBasemap才easeTo;改:移除_easePitch/style.load等待(maplibre setStyle不重置camera)→直接easeTo pitch(650ms顺滑,一次到位) ②生成新网格没关其他图层:上轮误改generateGrid跳过grid层(为视图按钮多层)破坏独占→改回独占关所有其他可见层(记memory:generateGrid独占与setViewMode配对两场景独立勿耦合) |

### 📝 开发日志

**关键字**：空间聚合分析, Spatial Analysis, 标准网格(方格 fishnet), 指定单元(zonal), H3, polarity_index, EPSG:4546, create_square_grid, snap-to-grid

#### 做了什么
- **P0 后端地基**：用户把核密度（连续密度场：KDE 地形+H3 密度分箱）与空间聚合（离散面域统计：方格/指定单元+Gi\*/Moran's I）拆为两个 Toolbox 功能。本期只做后端，为 P1-P3 铺地基。
  - `create_square_grid`(F_006)：snap-to-grid 只建有点的格（避免稀疏点生成巨量空格），EPSG:4546 量米制保证 50/200/400/1000m 精确，聚合 point_count/score_mean/五级极性/polarity_index，回 4326。
  - `/spatial/aggregate`(指定单元) + `/spatial/grid`(hex|square 统一入口) 端点，schemas 照搬 BufferRequest。
  - 补装 h3(P1 用) + httpx(端点测试)；补登 F_005(buffer，原 @track 未注册，rule 10)。
- **复用**：聚合统计复制 aggregate_by_polygons（不动既有函数，零回归）；CRS 范式照搬 create_buffer；端点结构照搬 /spatial/buffer。

#### 踩坑 & 收获
- **PySAL 重栈延后**：libpysal+esda 在 requirements.txt 声明但本 env 未装，且仅 P4 的 Gi\*/Moran's I 需要 → P0 不装、不接 hotspot/moran 端点（免留调用即 500 的死端点）。h3 轻量，为 P1 装上。
- **TestClient 需 httpx**：fastapi.testclient 在本 env 缺 httpx → 端点测试初失败；装 httpx 后全过（starlette 弃用警告指向 httpx2，httpx 仍可用）。
- **snap-to-grid vs 全 fishnet**：稀疏点下全 fishnet 会生成巨量空格；改为按点 snap 到格原点、去重后只建有点的格（与 create_hex_grid 行为一致）。
- **track 注册是运行时的**：MOD_SPATIAL 的 ID 不在 tracker.py 静态 `_REGISTRY`，而是各模块 import 时 `register_track_id()` 动态填。F_005(buffer) 之前只 @track 未 register → rule 10 漏洞，本次补登。

#### 🔜 下一步（新会话）
- **P1 核密度重组**：拆 综合/极性地形(去 L1/L2 命名)、移走情绪网格、加 H3 六边形(2D/3D, 橙黄-暗红)。/spatial/grid(hex) 已就绪。
- **P2 空间聚合骨架 + 标准网格**：新 Toolbox 项 + 步骤导航 + 标准网格(2D/3D, 3 极性)。/spatial/grid(square) 已就绪。
- **衔接**：plan `~/.claude/plans/majestic-marinating-cerf.md`（P0 已完成）。

---

## 📅 2026-06-27（周五）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | A1 三页架构文档整合 | `architecture.md` `decisions.md`(ADR-015) `prd.md` `dev-notes.md` `memory/three-page-architecture.md` | 三页=数据库→控制台→实时地图；当前聚焦控制台 α v0.1；L0-L4 双视角 |
| 2 | ✅ | B0 全局色彩 | `design/tokens.json` `css/tokens.css` `css/panel.css` | 8 处 #007afc→#4285F4；新增 card-fill #384555；Overview/Table 卡片深灰+浅字 |
| 3 | ✅ | B1 上端栏单层化 | `index.html` `css/layout.css` `css/toolbar.css` | 双层→单条深蓝 48px；面包屑递进；Import/Export/i 靠右白字 |
| 4 | ✅ | B2 左下 3 按钮集 | `js/map-controls.js` `css/map-controls.css` | 指针/测量/图层纵列于 5 按钮簇上方；initToolbar 选择器自动绑；measure 占位 |
| 5 | ✅ | B3 左端栏三区 + B6 随动复核 | `index.html` `js/sidebar.js` `css/sidebar.css` `css/layout.css` `css/tokens.css` | 手风琴→tab 互斥（Range/Layers/Toolbox）；删 Analysis/+Upload Range；区2 工具栏（初版深灰，row 6 修订为白底）；默认宽 240px；B6 Playwright 验左簇跟随零改动 |
| 6 | ✅ | B3·区2 工具栏修订（按参考截图） | `index.html` `js/sidebar.js` `css/sidebar.css` | 配色翻转：深灰底→白底+#384555图标+hover；顺序 [+][文件夹][方片叠加][眼睛][垃圾桶]…[漏斗 计数]；新增 #lp-add/#lp-group 占位；补漏斗 SVG；计数 textContent→querySelector 避免冲掉 svg |
| 7 | ✅ | B4 左端参数弹出栏 | `index.html` `js/param-panel.js` `js/settings.js` `js/heatmap-tool.js` `js/buffer-tool.js` `js/main.js` `css/param-panel.css` | 三参数入口（样式/核密度/Buffer）独立浮窗→统一 `#param-panel`（紧贴左栏右缘 + 随动 + 不可拖宽 + 默认隐藏）；1:2 分栏（左=样式 / 右=分析 子页签）+ 中灰 2px 竖线 + 右上 X；`<dialog>`→`<div>`、id 全保留，仅 showModal→面板显隐，**apply 链零改**；决策①核密度拍平单滚动 ②底图保留 top-right；Playwright 全链路验证（含核密度真生成） |
| 8 | ✅ | B5 色板圆角 + 品牌蓝查漏 | `css/settings.css` `css/sidebar.css` `css/panel.css` `css/toolbar.css` `css/dialog.css` `css/toast.css` `css/param-panel.css` `css/search-bar.css` `js/map.js` | `.swatch` 50%→圆角矩形(--geojson-radius-md 6px)；残留旧蓝 #007afc/rgba(0,122,252) 清零——半透明→color-mix 派生、回退值→#4285F4、toast --geojson-brand 幽灵 token 修复、map.js 回退；保留 PRESET_COLORS/arch-diagram 内容色 |
| 9 | ✅ | A2 UI 层文档（Martin 收尾） | `docs/decisions.md` `docs/spec.md` `docs/ui-redesign-plan.md` `memory/martin-ui-redesign.md` | ADR-016（Martin 导航范式决策：三区左栏+悬浮参数栏+胶囊选项集+品牌蓝单源，落地 B0-B5）；spec §3.4 前端导航架构规格（§3 定位注改指 §3.4）；ui-redesign-plan Phase 4（B0-B5 落地，标注 Phase1-3 已被 ADR-012 超越）；memory martin-ui-redesign 承重约定 |

> 💡 Martin 导航重塑全部完成（B0-B5 + B6 + A2 文档，ADR-016）→ 控制台 α v0.1 UI 主线收口。下一步可推进 L3 语义/L4 归因接口、或空间分析引擎 MVP（缓冲区+行政聚合）。

### 📝 开发日志

**关键字**：三页架构 ADR-015, L0-L4 双视角, #4285F4/#384555, 单层顶栏, 面包屑, 3 按钮集, Martin 导航重塑, 色板圆角, color-mix 派生

#### 做了什么
- **A1 三页架构文档**：产品升级三页架构（数据库→控制台→实时地图），当前=控制台 α v0.1。ADR-015 + architecture(§2 三页图 / §4 L0-L4 双视角 / §8 演进) + prd(§1.5 / §3.1 三页树) + dev-notes(06-27) + memory(three-page-architecture)。
- **B0 色彩**：token 单源（tokens.json→generate_css.py→tokens.css），品牌蓝 #007afc→#4285F4（8 处 + pill.bg RGB）；新增 --geojson-color-card-fill #384555；Overview/Table 卡片(ov-t1/ov-stat/stat-cell/ov-placeholder)深灰填充 + inverse 文字。数据表格保持白底。
- **B1 单层顶栏**：双层 88px→单条深蓝 48px；面包屑「宜昌市情绪地图 › 控制台（Console） prototype alpha v0.1」（title-zh ×2/3）；Import/Export/i 靠右白字（.draw-tool/.tb-text 改深蓝底白字）；select/basemap 移出（迁 B2）。
- **B2 3 按钮集**：map-controls 在 5 按钮簇上方加 toolsGroup（指针/测量/图层），8px 间距、悬停灰选中蓝。select/basemap 带 data-tool/data-action → initToolbar 自动绑（不改调用链）；measure toast 占位；#map .emotion-tools-ctrl 覆盖 .draw-tool 深蓝底白字污染。
- **B3 左端栏三区**：`.lp-sections` 从 4 段加法手风琴改为三区——区1 选择栏 tab 互斥（Range/Layers/Toolbox，`setActiveTab` 同步 pane 显隐 + 文件夹 title）、区2 深灰 `#384555` 工具栏（文件夹按当前页触发 range/import-input + 漏斗「可见/总数」+ 眼睛/垃圾桶从 Layers 段头迁入 id 不变）、区3 操作栏仅此滚动。删 Analysis 段（整合数据库）+ 删 `+Upload Range` 卡（上载统一文件夹）。默认宽 ×0.8 = 240px（`--left-w` + `--geojson-layout-left-panel-width` 同步）。
- **B6 随动复核**：左簇 `.emotion-controls-root` 锚 `#map`（absolute left:10px），`#map` flex-shrinks 天然跟随左端栏。Playwright 实测：遍历 --left-w ∈ [240,320,400,500]，Δcluster === Δlp（gap 恒 18 = gutter8 + offset10），B3 未动 flex → **零代码改动**，仅验证。

#### 踩坑 & 收获
- **token 单源**：tokens.css "DO NOT EDIT" → 改 tokens.json + 跑 generate_css.py；pill.bg 是 rgba 非 #007afc 字面量，replace_all 漏，单独更 RGB→(66,133,244)。
- **.draw-tool 双语境**：header（深蓝底）与 #map（白底）共用 .draw-tool → 用 `#map .emotion-tools-ctrl .draw-tool` 覆盖回白底深字。
- **initToolbar 选择器复用**：按钮迁址带 data-tool/data-action 即自动绑，不必改 map.js/main.js（initMap 先于 initToolbar，按钮已 in DOM）。
- **B3 迁移不破坏绑定**：`#layers-toggle-all`/`#layers-clear` 从 `.section-head` 迁到 `.lp-zone-tools`，id 不变 → sidebar.js 的 getElementById 绑定与 renderLayerList 的 innerHTML 刷新全保留；旧 `.section-head .layers-*` CSS 选择器变 dead 但无害。
- **B6 同步读取陷阱**：`#left-panel` 有 `transition: width`，遍历 `--left-w` 后同步 `getBoundingClientRect()` 读到动画初值（lpRight 卡 240）。解法：测试时 `lp.style.transition='none'` + `void lp.offsetWidth` 强制回流，再验 Δcluster===Δlp。另：cluster 与左端栏间隔是 gutter(8)+offset(10)=18，非 10。
- **showLayerManager 适配**：原依赖 `.lp-section[data-section="layers"]` 加 `.open`，三区重构后改调 `setActiveTab('layers')`——重构结构性改动必须 grep 旧选择器的所有消费方。
- **B5 幽灵 token + 半透明 token 化**：`--geojson-brand`（toast.css 引用）全仓无定义 → 回退 `#007afc` 永驻旧蓝（**真 bug**，非纯回退值不一致），改用真 token `--geojson-color-brand-primary`。半透明蓝（选中态填充等）无法直接引 token → `color-mix(in srgb, var(--geojson-color-brand-primary) N%, transparent)` 派生（单源真值，brand 变更自动跟随）；`rgba(66,133,244,N)` 虽匹配 `--geojson-color-pill-bg` 风格但仍是硬编码 RGB，不满足"替换为 token"。**判别**：`PRESET_COLORS` 调色板色 / arch-diagram 七色 `--lc` 是**内容色**（用户选色/装饰分层），非 chrome token 消费方，保留不动；`.ov-swatch`/`.stat-cell .swatch` 为图例小圆点，保留圆形。

#### 🔜 下一步（新会话）
- **B4 左端弹出栏**（✅ 已完成）：紧贴 `#left-panel` 右缘的 `#param-panel`（absolute `left:var(--left-w)` 随动 B6 机制、不可拖宽、默认隐藏），1:2 分栏（左=点/线/面样式 `#settings-popover` / 右=核密度·Buffer 子页签）+ 中灰 2px 竖线 + 右上 X。三模块 `<dialog>`→`<div>`、id 全保留，open/close 由 `showModal()`→`openParamPanel()/closeParamPanel()`（新 `param-panel.js` 编排显隐+页签+outside-click/Escape），**apply 链零改**（`applyPaint`/`generateHeatmap`/`generateBuffer` + 读值选择器一字未动）。**决策已锁**：①核密度 3 段拍平单滚动（不引入步骤导航）②`#basemap-popover` 保留 top-right。Playwright 全链路验证通过：paint 实时生效、核密度真生成（图层 4→5 + 热力图例）、buffer 填充、tab 切换、X/Escape 关闭；零 JS 错误。
- **B5 色板圆角 + 品牌蓝查漏**（✅ 已完成）：`.swatch` 圆形(50%)→圆角矩形(`--geojson-radius-md` 6px，与同弹窗 `.linestyle-cap` 一致)；全局 `#4285F4` 品牌蓝查漏——残留旧蓝 `#007afc`/`rgba(0,122,252)` 清零：(a)半透明填充改 `color-mix(in srgb, var(--geojson-color-brand-primary) N%, transparent)` 派生（`.layer-row.is-selected` 12/18%、`.is-bar-sel`/`.hm-style-btn.is-bar-sel` 12/18%、`.sc-hit`/`.arch-desc code` 6%、linestyle-cap 选中阴影 30%）；(b)`var(--token,#007afc)` 回退值统一→`#4285F4`（panel/sidebar/toolbar/settings/param-panel/search-bar）；(c)**toast `--geojson-brand` 幽灵 token**（全仓无定义、回退永驻旧蓝）→真 token `--geojson-color-brand-primary`；(d)`map.js` hover-ring 回退 `#007afc`→`#4285F4`。**保留不动**（内容色非 chrome）：`PRESET_COLORS` 调色板蓝、arch-diagram 七色彩虹 `--lc`。
- **A2 UI 层文档**（✅ 已完成）：①`decisions.md` **ADR-016**「Martin 编辑器范式（三区左栏+悬浮参数栏）」——背景/三选项表/决策(B0-B5)/后果 + 索引行 ②`spec.md` **§3.4** 前端主界面导航架构规格（布局区域表 + 左栏三区表 + 色彩控件单源），§3 定位注改指 §3.4 ③`ui-redesign-plan.md` **Phase 4**（B0-B5 落地表，Phase 1-3 标注已被 ADR-012 超越）④memory **`martin-ui-redesign`**（承重约定：三区 tab 互斥/参数栏随动 B6/apply 链零改/品牌蓝单源 `#4285F4`/胶囊设计语言）+ MEMORY.md 索引。revision-log §5.12 已同步。
- **衔接**：plan 文件 `C:\Users\Hi\.claude\plans\feature-kde-l2-3d-martin-delegated-milner.md`（B3-B6+A2 执行计划，**Phase 1 = B3+B6 已完成**）。

---

## 📅 2026-06-25（周三）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | Phase 2 地点搜索 — 后端 | `core/geocode.py` `api/routes.py` `api/schemas.py` `requirements.txt` | MOD_GEOCODE：本地 rapidfuzz + 高德兜底，`_amap_request` 双向 GCJ-02↔WGS84；3 GET 路由 |
| 2 | ✅ | Phase 2 地点搜索 — 前端搜索栏 | `frontend/js/search-bar.js` `css/search-bar.css` `js/api.js` `index.html` `main.js` `popup.js` `design/tokens.json` | 6 态状态机（不用 maplibre-gl-geocoder），胶囊折叠 32px→200px；空白点击反查 chip |
| 3 | ✅ | Search v2 — 拼音匹配 + 高亮 | `core/place_layer.py` `frontend/js/search-bar.js` | pypinyin 模糊匹配（wd/wanda→万达）；结果高亮子串 |
| 4 | ✅ | Search v2 — 红大头针 + Point 卡 + 交互 | `frontend/js/search-bar.js` `popup.js` | 自定义红色 pushpin，hover tooltip，click popup，激活放大，点外收起，x 关闭 |
| 5 | ✅ | Search v2.1 — 排名分层 | `core/place_layer.py` `tests/test_geocode.py` | exact(300) > prefix(250) > pinyin-exact(220) > substring(180+) > fuzzy；修"金缔华城→苏宁易购"bug |
| 6 | ✅ | Search v2.1 — 落水 POI 过滤 + 导出标记 | `core/place_layer.py` `export_poi_geojson.py` `DATA/place/pois_wgs84.geojson` | 28/1428 落现状水系，`__init__` 预标 `_in_water`，`forward()` 跳过，导出标 in_water |
| 7 | ✅ | Search v2.1 — Point 卡审计字段 | `frontend/js/popup.js` `core/place_layer.py` `api/schemas.py` | 数据源(高德POI库/种子手标) + baidu_level1/2 + area + 坐标 6 位精度 |
| 8 | ✅ | Search v2.1 — L0 数据点 popup 增强 | `frontend/js/popup.js` | showPopup 坐标 6 位不灰 + async 反查"区域 / 最近 POI" |
| 9 | ✅ | Zone v2.2 — POI/zone 审计 | `docs/poi-zone-audit.md` `audit_poi_zones.py` `audit_zones_local.py` | seed 121 条无 amap 对照（部分伪造）+ 坐标偏 1–9km；万达≠国贸 2731m；太古里伪造。根因报告 |
| 10 | ✅ | Zone v2.2 — 数据根基重建（Stage 1） | `DATA/place/zone_typology.json` `core/place_layer.py` | amap 重建 12 zone（7 商圈 + 4 非商业 + general）+ center+radius 商圈圆 + 删 wanda_cbd + all_pois=amap |
| 11 | ✅ | Zone v2.2 — 情绪叙事级联（Stage 2） | `emotion_corpus.json` `snapshot_config.py` `generate_l1_mock.py` `check_spatial.py` `place_keywords.json` | corpus 桶扩 12 zone × 3 极性；zone_caps 重算；mock 打标；check_spatial 适配 |
| 12 | ✅ | 合并 + 清理 + L0 popup 对齐 | git `main` / `frontend/js/popup.js` | merge feat→main(14 commits)；删 2 分支；main-only 工作流；L0 badge "原始"对齐 L1/L2 节奏 |
| 13 | ✅ | P2 geocode 离线退化 | `core/place_layer.py` `core/geocode.py` `tests/test_geocode.py` | `forward()` 加 `min_fuzzy_score` 参数；离线时 55→35 返回更多近似命中；pytest 35/37 全过 |
| 14 | ✅ | P3 下拉结果丰富化 | `core/place_layer.py` `api/schemas.py` `frontend/js/search-bar.js` `frontend/css/search-bar.css` `tests/test_geocode.py` | zone 色点 + 双副信息（zone+地址/类别同时显示）+ 匹配类型标签（精确/前缀/拼音/子串）|
| 15 | ✅ | P5 UX loading 态 + 无结果引导 | `frontend/js/search-bar.js` `frontend/css/search-bar.css` | 输入即显 spinner "搜索中..."；空态显示标题+引导文案 |

> 💡 开发工作流（solo）: 以后在 main 上直接工作 → `git commit` → `git push`。不做分支/PR。

### 📝 开发日志

**关键字**：地点搜索, 高德地理编码, CRS 红线, rapidfuzz 模糊匹配, 6 态搜索栏状态机, 拼音匹配, 分层排名, 落水过滤, zone 重建, amap 数据校准, 商圈本地知识

#### 做了什么
- **Phase 2 全栈地点搜索**（后端 `core/geocode.py` MOD_GEOCODE + 3 GET 路由 → 前端 6 态搜索栏 + 反查 chip）。两大红线：AMAP_KEY 仅服务端 .env（`_load_env()` 自加载——api/main.py 不加载 .env）；高德 GCJ-02 一律 `_gcj_loc_to_wgs`（正向）+ regeo 入参 `wgs84_to_gcj02`（反向），1m 往返单测守住。
- **Search v2**：pypinyin 拼音模糊（wd/wanda→万达）+ 结果高亮；红色大头针标记（hover tooltip + click Point 卡 + 激活态放大 + 点外收起 + x 关闭）。
- **Search v2.1 数据质量**：① 排名分层（exact>prefix>substring）修"金缔华城→苏宁易购"bug——原 partial_ratio 同分按数据顺序误排；② 28/1428 落现状水系→forward 跳过+导出标 in_water；③ Point 卡加审计字段（数据源/baidu_level/area/坐标 6 位）④ L0 数据点 popup async 反查区域+最近 POI。
- **Zone v2.2 根基重建**：审计发现 seed 158 条中 121 条 amap 无对照、坐标偏 1–9km（宜昌东站 9334m/国贸大厦 1019m/水悦城 671m）、太古里（西陵）伪造。用户本地知识校准——宜昌 9 商圈（夷陵CBD≠万达；CBD 专指夷陵广场；万达=万达广场唯一；水悦城/中南路/五一广场/吾悦/夷陵万达 各自独立）。重写 zone_typology 为 12 zone（7 商圈 center+radius 圆 + 4 非商圈子区 amap 锚点 buffer + general）；all_pois=amap only（seed 退命名不参与坐标/边界）。Stage 2 级联情绪叙事 12 zone（corpus/zone_caps/generate_l1_mock/check_spatial）。模拟数据暂不动。华翔CAZ/江南URD 数据 0 命中→归 general。
- **工作流切换**：合并全部到 main，删分支，以后 solo main-only 开发（commit→push 即完成）。

#### 踩坑 & 收获
- **数据信源不可信**：seed 158 条是手标/模板生成的，坐标大面积错+含伪造条目。amap 1270 条准。zone 边界原由 seed buffer 构建→种子错边界全错。教训：生成数据不能当初信源（边界/坐标），只能用真实 API 数据做锚。
- **排名同分陷阱**：`partial_ratio` 对"金缔华城"和"苏宁易购(金缔华城店)"都给 100 分——排序本质是 tiebreaker，不在数据层而在排层。分层打分才是正解。
- **zone 命名需本地人校准**：AI 从数据推断"万达簇""万达-国贸商圈"，但本地知识是万达=万达广场（唯一）、CBD=夷陵广场（≠万达）、万达和国贸 2731m 两个商圈。不加本地校验的 zone 分类不可靠。

#### 验证
- `py -m pytest tests/ -q`：geocode 25 全过（CRS 1m 往返 + 排名分层 + 落水过滤）。全量 80+/81（1 既有 L2 test_capabilities 与本批无关）。
- Playwright：搜索→flyTo CRS 自洽（center==hit 坐标）；Point 卡字段全显；L0 popup async 反查挂载；落水点不在结果中。
- curl `/place/search?q=金缔华城` → 金缔华城(300) 首条；`/reverse-geocode` → zone 正确。

#### 🔜 下一步
- 情绪真实数据 pipeline（L0→L1→L2 完整跑通，待 DeepSeek API Key 验证）。
- KDE 批2 时间轴。
- 华翔CAZ/江南URD 数据补齐后升 zone。

---

## 📅 2026-06-22（周一）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 批1·1b 小类配色按大类派生 | `frontend/js/state.js` | `EMOTION_TYPE_COLORS` 7 色派生自 `EMOTION_MACRO`；愁类 2 小类紫色系明度梯度 |
| 2 | ✅ | 类型细分色板方向翻转对齐胶囊顺序 | `frontend/js/state.js` | `positive/negative/neutral` 三 ramp 端点反转，对齐 `EMOTION_MACRO_ORDER`；放弃"高密度=最强情绪"旧语义 |
| 3 | ✅ | 补 todo.md 06-19~06-21 断档 | `docs/todo.md` | 核密度弹窗重构 7 项 + 开发日志（交接卡遗留） |
| 4 | ✅ | H 按钮重生成消失 bug | `heatmap-tool.js` `map.js` `serve.py` | opacity 反推百分比/比例混用（0.01 几乎透明）→ `*100`；附带 `to-number` + `serve.py` import ?v（破 Chrome module 缓存）+ 编辑分支原地更新（`editLayerId`） |
| 5 | ✅ | 色带随大类胶囊动态变化 | `state.js` `heatmap-tool.js` `map.js` `heatmap-legend.js` `panel.js` | `buildMacroRamp` inline rampStops（选中大类→只含选中类色）；消费方优先 inline；rampKey 保持 polarity（reverse 显示对齐胶囊序） |
| 6 | ✅ | 色带 HSL 色相插值 + 每类 3 段 | `state.js` | 取消 macroShades 明度变体；类色 HSL 插值（`gradientStopsHsl`），每类占 3 段色相；段数 积极 6/消极 9/中性 6/单类 3；HSL 替 RGB（中间黄绿明亮非土黄） |
| 7 | ✅ | #hm-macros click→change 事件 | `heatmap-tool.js` | label-click 时序 is-on 滞后 input.checked，单选色带不更新 → change 同步 |

> 💡 标准启动指令：`py frontend/serve.py 8080` → `http://127.0.0.1:8080/frontend/index.html`

### 📝 开发日志

**关键字**：小类配色派生, 色板方向翻转, EMOTION_MACRO_ORDER 对齐, density 语义放弃

#### 做了什么
- **批1·1b 小类配色按大类派生**：小类独立色板（`EMOTION_TYPE_COLORS`）与大类色板（`MACRO_COLORS`/`EMOTION_MACRO`）冲突——"不满抱怨"=橙却属大类"愁"=紫。改为派生：单小类=大类色，愁类 2 小类（焦虑担忧/不满抱怨）用紫色系明度梯度（中紫 `#A569BD` / 深紫 `#7D3C98`）。调用点不动（`heatmap-tool.js:274` `EMOTION_TYPE_COLORS[t]` 值变即生效）。
- **类型细分色板方向翻转**：`positive/negative/neutral` 三 ramp 端点顺序与胶囊 `EMOTION_MACRO_ORDER` 反向（积极胶囊 喜→乐，色板却 乐→喜）。反转三 ramp 端点对齐胶囊顺序（积极 喜→乐、消极 怒→哀→愁、中性 急→盼）。放弃"高密度=最强情绪"旧语义——色板是单维 density 渐变，颜色仅借大类色做视觉编码，无真实"密度段=情绪"含义。消费方（图例 / Overview / 设置 / 地图 paint）单源自动跟。
- **补 todo.md 06-19~06-21 断档**：核密度弹窗重构 7 项 + 开发日志（交接卡遗留项）。
- **H 按钮重生成消失 bug**（5bab6d4）：H 按钮重生成（原样再点生成）→ 热力图消失、眼睛救不回。Playwright + paint 查证：`openHeatmapDialog` 反推 opacity 百分比/比例混用（`sp.opacity` 0~1 直接赋百分比控件 0~100 → type=range clamp 1 → `generateHeatmap` 读 `1/100=0.01` 几乎透明）。修复：反推 `Math.round(sp.opacity*100)`。附带：`buildWeightExpression` `to-number`（MapLibre worker string 健壮）；`serve.py` 拦截 .js 注入 `import ?v=<mtime>`（破 Chrome module graph 缓存——旧 serve 只 main.js 带 ?v，子 module 缓存旧版致 F5 失效）；编辑分支原地更新（激活 `editLayerId`，4.6「继续编辑」语义）。
- **色带演进**（62724d1）：
  - **随胶囊动态**：`buildMacroRamp`（state.js）按选中大类生成 inline rampStops（选中大类 → 只含选中类色；全选 = 等同固定 ramp）；消费方优先 inline、fallback rampKey；rampKey 保持 polarity（rampDisplaySegs 据 polarity reverse，色带与胶囊同向）。
  - **每类 3 段 + HSL 色相插值**：取消 macroShades 明度变体（跨类明度跳变割裂），类色直接 HSL 插值（`gradientStopsHsl`，hue 最短路径），每类占 3 段色相，整体连续不割裂。段数 积极 6/消极 9/中性 6/单类 3。HSL 替 RGB（RGB 绿↔黄中间土黄 `rgb(152,148,65)`，HSL 中间黄绿明亮 `rgb(123,218,87)`）。
  - **#hm-macros click→change**：label-click 时序下 is-on class 滞后 input.checked（rAF 读旧值），单选时 renderStylePreview 取旧选中态、色带不更新 → 改 `change` 事件（input toggle 后同步触发）。

#### 踩坑 & 收获
- **色板方向 vs 胶囊顺序**：色板设计遵循 density 语义（左低右高），胶囊遵循情绪分类顺序（`EMOTION_MACRO_ORDER`），两者语义轴不同向导致全局反向。统一为胶囊顺序（视觉一致优先于牵强的 density-情绪绑定语义）。
- **小类派生 vs 直接读大类色**：愁类 2 小类若直接读大类色会撞色（焦虑担忧=不满抱怨=愁紫），保留小科级 + 值派生自大类色系，兼顾统一与区分。

#### 验证
- `node --check frontend/js/state.js` 语法通过。
- 起页肉眼验（`py frontend/serve.py 8080`）：核密度弹窗 ①选「类型细分」→ ②小类胶囊色对齐大类色系 → ③色板分段条方向对齐胶囊顺序。未上 Playwright（配色/方向小改）。

#### 🔜 次日计划
- 批1·1a 预览图换 terrain/factor Kepler 截图（等素材补齐，⏸ 搁置）。
- 任务树下一模块（Range 范围分析 / Analysis 接入 / Table 表格）。

---

## 📅 2026-06-19~06-21（周五~周日）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 核密度弹窗三阶引导重构 | `frontend/js/heatmap-tool.js` `frontend/css/dialog.css` | ①分析类型(总体/类型细分/多维归因) ②数据源 ③显示样式；①三组纵向排版 |
| 2 | ✅ | kepler 离散分段色板 + 栏/选项/胶囊三组件 token | `frontend/js/state.js` `design/tokens.json` `frontend/css/dialog.css` | 全站色带统一 `.segmented`，取代无极渐变 |
| 3 | ✅ | L1 热度值 | `frontend/js/heatmap-tool.js` | 强度×置信度，3 段动态分位 |
| 4 | ✅ | 7 大类配色 + 类型细分色板方向修复 | `frontend/js/state.js` | `MACRO_COLORS` 单一调色源(UberPool 6+1)；端点顺序低→高 |
| 5 | ✅ | 联动（Overview/popup/图例） | `frontend/js/sidebar.js` `frontend/js/popup.js` `legend` | `layers:changed` 事件三处同步 |
| 6 | ✅ | serve.py 自动 ?v 注入 + 启动清端口 | `frontend/serve.py` | `?v=<mtime>` 改文件即拉新，零手动 bump |
| 7 | ✅ | revision-log 任务树 + 工作机制 memory | `docs/revision-log.md` `~/.claude/` | 模块化任务树；session-handoff/token-saving/revision-log/kde-loadbearing |

> 💡 标准启动指令：`py frontend/serve.py 8080` → `http://127.0.0.1:8080/frontend/index.html`

### 📝 开发日志

**关键字**：核密度弹窗(KDE), 三阶引导, kepler 离散分段色板, L1 热度值, 7 大类配色, 类型细分色板方向修复, layers:changed 联动, serve ?v 注入, revision-log 任务树

#### 做了什么
- **核密度弹窗三阶引导重构**：①分析类型(总体情况/类型细分/多维归因) → ②数据源 → ③显示样式。①三组纵向排版（kepler 风），取代旧版杂糅表单。
- **kepler 离散分段色板**：全站色带统一 `.segmented`（色块拼接，非无极 linear-gradient）。色板采样自 kepler 源码——网格暖色谱≈Global Warming；7 色分类≈UberPool 6 色+补 1 色；L1 默认单色改橙红(ColorBrewer Reds)。栏/选项/胶囊三组件设计 token。
- **L1 热度值**：L1 综合舆情热度 = 强度×置信度，3 段动态分位（取代静态阈值）。
- **7 大类配色**：喜怒哀乐愁急盼 = 绿/橙/红/紫红/紫/深蓝/天蓝（`MACRO_COLORS` 单一调色源；胶囊/classify-7/积极·消极·中性格色板均派生自此，保证全局一致）。
- **类型细分色板方向修复**：端点顺序 = [低值色 … 高值色]（gradientStops 从低 density 到高 density）。积极=喜(绿)高/乐(橙)低；消极=怒(红)高/哀(紫红)中/愁(紫)低；中性=急(深蓝)高/盼(天蓝)低。
- **三处联动**：Overview / popup / 图例 通过 `layers:changed` 事件同步。
- **serve.py `?v=<mtime>` 自动注入**：返回 index.html 时给本地 css/js 引用自动注入 `?v=<mtime>`，文件一改浏览器即拉新，开发者零手动 bump；启动时清占用端口。
- **revision-log 任务树 + 工作机制 memory**：revision-log 顶部建模块化任务树（根→模块→批→叶，AI 全程维护）；建 4 条工作机制 memory（session-handoff / token-saving / revision-log / kde-loadbearing）。

#### 踩坑 & 收获
- **kde-loadbearing 两条底层逻辑（勿破坏）**：①**联动排除**——无字段层级自动排除（类型细分锁 L2、L1 无情绪字段时胶囊禁用）；②**独占显示**——生成新热力图隐藏其他层 + `dispatch layers:changed` 保侧栏眼睛同步。
- **类型细分色板端点顺序**：gradientStops 从低 density 到高 density，端点顺序 = [低值色 … 高值色]；方向搞反会让"高密度=低值色"，视觉语义倒置。

#### 验证
- 起页肉眼验（`py frontend/serve.py 8080`），未上 Playwright（配色/布局小改，遵循 no-routine-playwright-verify）。
- 核密度弹窗三阶引导、L1 热度值分位、7 大类胶囊色、类型细分色板方向、三处联动均肉眼确认。

#### 🔜 次日计划
- 批1·1b：小类配色按大类派生（小类色继承所属大类色相基调；愁类 2 小类用紫色系明度梯度）。
- 批1·1a：预览图换 terrain/factor Kepler 截图（等素材补齐，⏸ 搁置）。

---

## 📅 2026-06-18（周四）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | Import v1：1:1 geojson.io 导入管道 | `frontend/js/{import,dialog,toast,state,map,sidebar,main,popup}.js` `frontend/css/{toast,dialog,sidebar,popup,legend,layout}.css` `frontend/index.html` | groupFiles/detectType/parse(GeoJSON/CSV/KML/Shapefile)/proj4 CRS/几何分流/polarity探测/merge/fitBounds；导入确认弹窗（单/组合文件）；全局胶囊 toast；左栏图层管理器（眼睛/删除/清空） |
| 2 | ✅ | Import v2 批1：bug 修复 + 核心显示 | 同上 + `tokens.css` | 7 bug（polygon 线层泄漏/Import 误切模式/删 seed/左栏默认展开/Layers 自动展开/shapefile 5件包/眼睛放大）+ L1 橙色置信度着色 + 图例按层显隐 + polygon 海军轮廓 + 范围第二 popup |
| 3 | ✅ | Import 细化轮 | 同上 | 闭合线归为 polygon（GIS 常识）；范围 popup 重构（名称下沉第二层、收起显 Range）；点大小改密度自适应（稀疏14-18/高8-12/超高4-6，随zoom插值）；选中=灰白加粗描边不填充；收起胶囊定宽64px；L2 配色提浅（最深不变） |
| 4 | 🔄 | Import 批2：要素按钮 + Kepler 设置弹窗 + 预设色板 | `frontend/js/settings.js` `frontend/css/settings.css` `frontend/js/{sidebar,map}.js` `frontend/index.html` | 点/面 marker 变可点「要素按钮」（激活=深灰粗圆角框）；Kepler 设置弹窗（预设色板横条/色块 + 透明度/线宽滑块 + 面填充开关）；线暂不开放。实现完成待肉眼验 |

> 💡 标准启动指令：`@pm 开始处理 2026-06-18 的任务 N：任务名称`

### 📝 开发日志

**关键字**：Import, geojson.io 1:1, shapefile, proj4 CRS, L1 置信度, 密度自适应, 图层管理器, 范围 popup

#### 做了什么
- **Import v1**：geojson.io 1:1 导入。两处 Import（工具栏+左栏）+ 页面拖放 → 原生文件窗 → **每次导入都弹确认弹窗**（单文件=文件名+格式下拉可改写；组合包="Import {name} (n/N)"+文件名列表；Cancel/Import）。管道：`groupFiles`(shapefile 多文件成组) → `detectType`(扩展名/JSON内容sniff) → `parseGroup`(GeoJSON/CSV/KML/Shapefile) → `reprojectFC`(proj4 读 .prj → WGS84) → `splitByGeometry`(Point/Line/Polygon 分流) → `detectColorMode`(polarity/confidence/needsAnalysis) → **merge 追加** + fitBounds。全局胶囊 toast。左栏图层管理器（眼睛显隐/×删除/区段头清空）。
- **Import v2 批1**（用户实测后 7 bug + 显示）：①polygon 开关失效=fill(`lyr-{id}`)+line(`lyr-{id}-line`)两图层泄漏，改同步增删 ②顶端 Import 误切 sections，改仅加载成功后切 ③删 seed 模拟数据，首屏空 ④左栏默认展开凸显 Import ⑤加载后自动展开 Layers ⑥**shapefile 5件包失效**=shpjs `combine` 参数顺序写反(应[几何,属性])，改走 parseShp/parseDbf/combine 直读 ⑦眼睛放大。+ L1 橙色置信度着色（Kepler 风、小点无描边、置信度越高越深）+ 图例按层显隐（polarity/confidence/range 三块）+ polygon 默认 fillOff 海军轮廓 + 范围第二 popup（海军主题、面积/周长/类型/顶点/bbox）。
- **细化轮**：①闭合 LineString 归为 polygon（首尾点重合=面边界，GIS 常识）→ marker 显「面」②范围 popup 重构：名称下沉第二层(.popup-text，类评论)、「范围」badge 去强调、收起显粗体"Range"、与情绪胶囊同宽 ③点大小**密度自适应**(densityStops：≤1000→14-18/≤20000→8-12/>20000→4-6，随zoom插值，取代固定3x) ④选中=灰白(#E8E8E8)加粗(3.5)描边、不填充 ⑤收起胶囊定宽64px+大写+省略 ⑥L2 配色提浅（very-negative #B92D2D 不变，其余按明度比例提浅）⑦范围透明 hit 层(宽12)易悬停/点击。
- **Import 批2**：要素按钮 + Kepler 设置弹窗。图层行「点/面」marker 由 span 改可点 button（激活=gray-700 `#404040` 粗圆角框、放大到 ~22px 与眼睛齐；线为禁用 chip）；点开 `#settings-popover`（`position:fixed`，靠左栏右边+8px、240px、圆角 8px=radius-lg 同左簇/图例）：点·L1 confidence=**序列色板横条点选**(→`paint.ramp`)+透明度滑块；点·L2/needsAnalysis=仅透明度（颜色由极性/灰决定）；面=**填充开关**(→`paint.fillOn`)+**单色色块**(→`paint.color`)+线宽滑块+填充透明度滑块。控件 change → `setLayerPaint`+`renderLayer` 实时重渲（renderLayer 的 remove+readd 已支持 live）。预设 6 序列色板（橙默认/蓝/绿/紫/红/灰）+ 10 单色块。一次一弹窗；外部点/ESC/删图层关闭。`map.js addPointPaint` 改读 per-layer `paint.ramp`/`paint.opacity`。
- **点密度策略再修订**（用户定）：`densityStops` 阈值收紧——`<500→[14,18]` / `500-2000→[8,11]` / `≥2000→[3,5]`（原 ≤1000/≤20000/>20000）。用户 2000 点数据 ~10.7px→~4px。L0-L4 统一（radius 本就 colorMode 无关）。
- **配置**：index.html 加 CDN 解析库（csv2geojson/shpjs/proj4/fflate；@tmcw/togeojson 走 esm.sh 动态导入，CN 不可达则降级）。tokens.json/tokens.css 情绪五色单源同步。

#### 踩坑 & 收获
- **shpjs combine 参数顺序**：`combine([geometries, properties])` shp 在前 dbf 在后；写反 → geometry/properties 颠倒，splitByGeometry 无可识别几何→静默无操作（不抛异常）。用 getStyle() 取原始 paint 表达式才看出。
- **map.project 坐标系**：返回**地图容器内坐标**，Playwright `page.mouse.click` 用**视口坐标**，差左栏+头栏偏移 → 测试点击老偏。修正：+ getContainer().getBoundingClientRect() 偏移。
- **CGCS2000 .prj**：规划范围.shp 的 .prj = CGCS2000 3-degree GK CM_111E，**False_Easting=500000**(EPSG:4538)，非 4546 的 37500000。proj4 能直接解析 WKT，实测 [525439,3398933]→[111.266,30.711] 宜昌正确。
- **paint.get() 返回求值态**：MapLibre `layer.paint.get('circle-radius')` 返回当前 zoom 求值后的值，看不到原始表达式；改用 `map.getStyle().layers[].paint` 取原始表达式验证。
- **闭合线=面**：CAD 导出的 LWPolyline shapefile 几何类型是 LineString 但首尾闭合，本质是面边界。splitByGeometry 据此归为 polygon。

#### 验证
- Playwright file-upload 喂真实文件端到端：L2 GeoJSON（polarity 5色）/ L1 CSV（橙色置信度）/ shapefile 5件包（CRS重投影到宜昌）/ 测试 polygon（B1开关+范围popup）。控制台全程仅 favicon 404。
- 密度半径表达式 `interpolate(zoom,8→8px,14→12px)` 实测；选中 halo `stroke #E8E8E8 width 3.5 opacity 0` 实测；收起胶囊 `width 64px uppercase` 实测。

#### 🔜 次日计划
- Import 批2：要素按钮 + Kepler 设置弹窗 + 预设色板
- 用户视觉复验反馈微调（点密度档阈值 / L2 配色深浅 / 范围 popup 字段）
- MCP 收尾（github PAT / web_reader 重复）—— 06-17 遗留

---

## 📅 2026-06-17（周三）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 交接恢复：补 4 个天地图底图 JSON | `apps/static/tianditu_*.json` | gitignore 不同步，办公机手动补（img/vec × 有/无注记），否则默认底图 404 灰屏 |
| 2 | ✅ | 文档去陈：9 份权威文档对齐前端迁移 | 根`CLAUDE.md`/`apps/CLAUDE.md`/`AGENTS.md`/`docs/{architecture,architecture-pattern,spec,prd,brand-visual,ui-redesign-plan}.md` | Streamlit→MapLibre，全部标「迁移期遗留」，+130/−49 |
| 3 | ✅ | 新增 ADR-012 前端迁移决策 | `docs/decisions.md` | 历史审计连续，旧 ADR-001~011 不动 |
| 4 | ✅ | 补录 06-16 晚~06-17 凌晨工作 + 换机清单 | 本文件 + `session-handoff.md` | 昨晚工作原只记于交接卡，todo.md 漏更（见日志） |
| 5 | ✅ | MCP 能力层纳入 vibe coding + 智谱优先策略 | 根`CLAUDE.md`/`AGENTS.md`/`docs/mcp-strategy.md`(新)/`docs/decisions.md`(ADR-013)/本文件 | 9 服务实测 7 通；github PAT 失效、web_reader 重复待修 |
| 6 | ✅ | 闭环补强 9 波：开环→闭环 | `core/tracker.py`/`.claude/{settings,agents/*,hooks/*,commands/verify}`/`.githooks/`/`tests/test_pii_guard.py`/`docs/{trace-digest,decisions}.md`/memory/ | pytest 59 passed；trace 落盘+回灌、提交门禁、emoji 拦截、记忆索引全到位；ADR-014 |

> 💡 标准启动指令：`@pm 开始处理 2026-06-17 的任务 N：任务名称`

### 📝 开发日志

**关键字**：交接恢复, 文档去陈, ADR-012, 同步诊断, todo.md 漏更, 换机清单, MCP策略, 智谱优先, ADR-013

#### 做了什么
- **交接恢复**：办公机 `git pull` 到 cee9da9（与家用机同步健康，HEAD=origin），补 4 个被 gitignore 的天地图底图 JSON（img/vec × 有/无注记）
- **文档去陈**（+130/−49，10 文件）：根 CLAUDE.md / apps/CLAUDE.md / AGENTS.md / docs 6 份全部对齐「frontend/ MapLibre 为主、Streamlit 迁移期遗留」；ASCII 架构图内部不动（破坏对齐），改用 callout 兜底
- **新增 ADR-012**：记录前端迁移决策（背景/选项 A-C/决策/后果），保持 ADR 审计连续
- **同步诊断**：查明 todo.md 漏更真相——git 同步正常，但昨晚工作（前端 v2 / P0 债 / 启动说明）只写进 session-handoff + frontend/README，未同步进 todo.md
- **启动说明定位**：= `frontend/README.md`（cee9da9，86 行），未丢失
- **换机清单**：写入 session-handoff.md「换机前必做」，防止 todo.md 再漏更
- **MCP 能力层**：实测全部 9 个 MCP（7 通 / github 认证失败 / web-reader 重复）；新建 `docs/mcp-strategy.md` 路由手册；CLAUDE.md 规则 11 视觉改智谱为主、新增规则 12、补 MCP 状态行 + 文档登记；AGENTS.md 升 v2.1 加「MCP 能力外挂」子节；ADR-013 落档
- **闭环补强（9 波，ADR-014）**：诊断=协作半成品/闭环开环；补反馈链——①tracker 落盘 `.trace/trace.log`+`recent_errors()` ②`/verify`+`.githooks/pre-commit`(core.hooksPath) ③emoji PreToolUse hook(精确拦 U+1F000-1FAFF)+PII guard 测试 ④SessionEnd trace 摘要回灌 `docs/trace-digest.md`(游标防重) ⑤8 agent v2.1+MCP 能力段+铁律 1-12 ⑥建 MEMORY.md 索引(原缺失！)+修 3 陈旧记忆+3 种子 ⑦GitHub Actions CI(best-effort) ⑧skill 索引已精选(物理移除暂缓)。pytest 56→59 passed 零回归

#### 踩坑 & 收获
- **todo.md vs session-handoff 职责分裂**：两者都承载工作状态，昨晚只更交接卡、漏正式日志 → 新会话/Agent 读 todo.md 误判「06-16 后没干活」。根因：无「换机前必更两文件」强制清单
- **git 同步本身健康**：HEAD=origin/main=cee9da9，无未推送/未拉取，.claude/ 配置全在 git。问题在内容写入策略，不在 git
- **lint 区分**：MD028（我引入的 callout 紧跟 blockquote）修了；MD060/MD032/MD040（原文既有表格/标题接列表风格）不逐处改，保全文一致性
- **github MCP `disabled:true` 被忽略**：`.mcp.json` 标了禁用仍被加载，且 PAT 失效致 `Bad credentials`——禁用标记未必生效，需移除条目或重启确认
- **web-reader 重复服务**：`web-reader`（连字符）与 `web_reader`（下划线）指向同一智谱端点，保留连字符一份即可
- **Auto Memory 暗写不召回**：memory 目录有 6 条记忆但 MEMORY.md 索引从不存在——召回靠读索引，等于 6 条全废。已补建索引。根因：写记忆的流程没同步写索引
- **emoji hook UTF-8 陷阱**：初版用 `sys.stdin.read()` 在 Windows cp936 下把 emoji 读坏→JSON 解析失败→被 except 吞掉静默放行。改 `sys.stdin.buffer.read().decode('utf-8')` 才真拦住。教训：Windows 下读 stdin 必显式 UTF-8

#### 🔜 次日计划 (2026-06-18)
- 办公机补验证：pytest 56 回归 + FastAPI governance 冒烟（交接卡 P0 待办）
- Phase 2：前端接真实数据 `/api/v1/points` + A 分析接 `/analyze`
- MCP 收尾：github MCP 设 `GITHUB_PAT` 或移除条目；清理 `web_reader` 重复服务；核实 `4_5v_mcp` 来源

---

## 📅 2026-06-16（周二）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ⏸️ | L0→L1→L2 端到端管线验证 | `SCRIPT/data_governance.py`, `SCRIPT/emotion_analysis_v1.py`, `DATA/raw/simulated_20260613_100k_raw.csv` | **用户搁置至下周**：DeepSeek Key 已配好，届时跑完整三阶段 |
| 2 | ⬜ | 文档一致性修正 | `docs/spec.md`, `docs/architecture.md`, `AGENTS.md` | Python 3.14.5 / L1 列数 26 / pm.agent.md 角色说明 |
| 3 | ⬜ | Git 提交 + push | — | commit session-handoff 更新 + todo 更新 |

> 💡 标准启动指令：`@pm 开始处理 2026-06-16 的任务 N：任务名称`

### 📝 开发日志

**关键字**：文档修正, 交接更新

> ⚠️ L0→L2 端到端管线验证已由用户明确搁置至下周，本周不再排入计划。

#### 做了什么
- **P0 阻断债清理（5 项，家用机）**：①h3 v3→v4 API ②CorpusAnalyzer 双 `analyze_single` 合并 ③ADR 编号消解（ADR-008→011，避与 Scrapy 冲突）④PostToolUse hook 对齐（仅清 .pyc，不重启/不测试）⑤`run_governance_pipeline()` 抽取（API/CLI 共用、不含 sys.exit）——函数级已验证，pytest/FastAPI 冒烟待办公机补跑
- **前端 Phase 1 落地（家用机）**：`frontend/` MapLibre GL JS geojson.io 外壳，Token 单源（tokens.json `geojson` 段 → frontend/css/tokens.css），Playwright 验证通过
- **文档一致性修正**：d02dd36 提交（Python 版本/L1 列数/pm.agent 角色）

#### 踩坑 & 收获
- 家用机 Python 实为 3.13.2（非文档 3.14.5），pypi 直连被墙致 pytest/FastAPI 未跑成
- 前端 v2 配色纠正：误做全深色 chrome → 改「浅色为主 + 深蓝标题带」
- 切底图后情绪点消失：MapLibre 5.x re-apply 三套机制不稳 → 改 `setStyle(transformStyle)` 声明式 carry-over emotion-* 源/图层

#### 🔜 次日计划 (2026-06-17)
- （已完成，见上方 06-17 条目：交接恢复 + 文档去陈 + ADR-012）

---

## 📅 2026-06-15（周一）

### 🌙 凌晨完成（06-14 残余，commit `f044ca1`）

| # | 状态 | 任务 | 备注 |
|---|------|------|------|
| M1 | ✅ | Agent 架构 v2.0 升级 | 11→8 精简 + 自动编排 |
| M2 | ✅ | PRD + Spec 文档 | 27 功能 MoSCoW + 全规范 |
| M3 | ✅ | .claude 配置初始化 | 权限 + 记忆体系 + 中文偏好 |

### ☑ TODO List（今日，08:00+）

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ⏸️ | L0→L1→L2 端到端管线验证 | `SCRIPT/data_governance.py`, `SCRIPT/emotion_analysis_v1.py`, `DATA/` | **暂缓至下周**：准备测试数据 → 跑 L0→L1 治理 → 跑 L1→L2 情感分析 → 验证各层输出 |
| 2 | ⬜ | 用户验收周末改动 | 全项目 | Agent v2.0 架构 + PRD/Spec 文档 + 启动应用验证 + L1_COLUMNS 重排 + confidence 重命名 |
| 3 | ⬜ | Git 清理 + commit + push | — | 处理未提交 geojson + 提交今日变更 |
| 4 | ✅ | 安装 .claude Skill 包 | `.claude/skills/` | 4 源合入 455 技能：daymade(64) + python-skills(12) + laurigates(362) + **anthropics(17)** |

> 💡 标准启动指令：`@pm 开始处理 2026-06-15 的任务 N：任务名称`

### 📝 开发日志

**关键字**：端到端管线, 验收, Skill包, L1→L2验证, SnowNLP

#### 做了什么
- **Task 1**: L1→L2 管线验证通过（因缺 DeepSeek API Key，仅验证 L1→L2 段）
  - 用现有 L1 2000行数据跑 SnowNLP L2 分析：2000行全量通过
  - 极性分布：Very Positive 672 / Positive 275 / Neutral 232 / Negative 269 / Very Negative 552（U型分布，模拟数据预期正常）
  - CSV + GeoJSON 正确导出
  - 全部追踪点触发 (MOD_ANA.F_008/F_009/F_010, MOD_EXPORT.F_001/F_002)
  - check_data_quality.py 硬编码路径已修复，但 L1 段因列不匹配无法运行（旧脚本，技术债务）
- **Task 2**: 用户验收周末改动全部通过
  - 8 Agent 注册正确（pm.agent.md 未注册，作为行为指南保留）
  - PRD (294行) + Spec (436行) 完整
  - .claude 配置：权限/Memory/编排均正确
  - Streamlit 8501 正常启动，所有模块导入正常
- **Task 4**: 安装 .claude Skill 包
  - 4 源合入：anthropics(17) + daymade(64) + python-skills(12) + laurigates(362) = **455 技能**
  - 官方 anthropics/skills 从 Gitea 镜像拉取（GitHub 直连失败）
  - 以 anthropic- 前缀命名空间存放

#### 踩坑 & 收获
- GitHub 直连被重置（网络限制），通过 cncfstack Gitea 镜像成功拉取 anthropics/skills
- check_data_quality.py 是旧版脚本，L1 段期望 `in_scope`/`_kw_pass` 列，与当前 L1 CSV 26列格式不兼容——需后续全面重构
- L2 SnowNLP 2000行 ~6秒，比预期的 10 秒更快
- 455 个 Skill 文件总量 ~11MB，对 Git 仓库体积影响可接受

#### 发现的文档不一致（待修正）
- Python 版本：文档 3.10+/3.13.2，实际 3.14.5
- L1 列数：spec.md 写 20 列，实际 CSV 26 列
- pm.agent.md 未注册但仍在 agents/ 目录（行为指南角色）

#### 🔜 次日计划 (2026-06-16)
- 配置 DEEPSEEK_API_KEY，跑完整 L0→L1→L2 端到端管线
- 修复 check_data_quality.py 适配当前 L1 数据格式
- 修正文档中的 Python 版本和 L1 列数不一致

---

## 📋 每日模板

```markdown
## 📅 YYYY-MM-DD（周X）

### ☑ TODO List
<!-- 当日计划完成的任务，每天 ≤ 3 个大任务 -->

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ⬜ | 做什么 | `xxx.py` | |
| 2 | ⬜ | 做什么 | `xxx.py` | |
| 3 | ⬜ | 做什么 | `xxx.py` | |

> 💡 标准启动指令：`@pm 开始处理 YYYY-MM-DD 的任务 N：任务名称`
> ⚠️ 编号规则：每日任务从 1 开始连续编号，不跳号、不重复。跨日引用使用 `MMDD-NN` 格式（如 `0613-07`）。

### 📝 开发日志
<!-- 记录实际做了什么、踩了什么坑、收获了什么 -->

**关键字**：tag1, tag2

#### 做了什么
- 

#### 踩坑 & 收获
- 

#### 碎片想法
- 

#### 🔜 次日计划 (YYYY-MM-DD)
- 
```

---

## 📅 2026-06-13（周六）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 规划范围真实数据落图（L1治理+坐标转换+范围过滤管道） | `SCRIPT/data_governance.py`（新建）, `core/coord_transform.py`, `core/range_selector.py` | 边界=规划范围(LineString→buffer Polygon)；管道已就绪，24条占位坐标全部被过滤（预期行为），待真实坐标数据后完整验证 |
| 2 | ✅ | Data Agent 创建 + L0→L1 相关性筛选模块 | `SCRIPT/relevance_filter.py`（新建）, `data_governance.py`（重构 v1.1）, `.claude/agents/data.agent.md`, `AGENTS.md` | 两层漏斗：关键词粗筛 + DeepSeek LLM 精分类；Agent 整合入全局调度 |
| 3 | ➡ | L1 治理 + L2 分析 端到端验证 | `data_governance.py`, `emotion_analysis_v1.py`, `DATA/` | 数据爬取暂时放弃，MVP 专注 L0→L2 管线跑通，确保各层数据有价值 |
| 4 | ✅ | 情绪点显示样式优化（颜色/光晕/描边） | `core/config.py`, `core/map_engine.py`, `core/ui_components.py` | Designer 重设计：双层光晕 + Material色板 + Neutral改琥珀色 |
| 5 | ✅ | Design Token 体系搭建（设计令牌系统） | `design/tokens.json`, `design/generate_css.py`, `design/tokens.css`, `design/tokens.py` | Designer 创建完整设计体系：7大类150+token + 自动生成器 + ui_components.py 全部 Token 化 |
| 6 | ✅ | Token 双模式 (Light/Dark) + 设计系统展示页 | `design/tokens.json`(重构), `design/generate_css.py`(重写), `design/tokens.css`, `design/tokens.py`, `core/ui_components.py`, `apps/app_design_system.py`(新建) | Dark/Light 镜像双主题 + prefers-color-scheme 自动跟随 + [data-theme] 手动切换 + 独立 Kitchen Sink 展示页 |
| 7 | ✅ | 主应用集成新 Design Token（低饱和色卡+CSS变量） | `apps/app_main.py`, `design/tokens.css`, `design/tokens.py` | 添加 inject_theme_css() 调用 + 重新生成 Token CSS/Python |
| 8 | ✅ | 修复注记开关 [LB] 导致底图偏移/复位 | `apps/app_main.py` | st_folium() 返回值保存 last_center/last_zoom 到 session_state，rerun 后视图保持 |
| 9 | ✅ | 边界线粗细+颜色可调节（[R]窗口内） | `apps/app_main.py`, `core/map_engine.py` | show_range_dialog 新增 slider(1-20) + 7色 selectbox；add_boundary_layer 动态 hex→RGB + weight 参数 |
| 10 | ✅ | 决策追踪系统 (Decision Tracking System) | `core/tracker.py`(新建), `.claude/agents/debugger.agent.md`, `developer.agent.md`, `reviewer.agent.md`, `AGENTS.md`, `docs/architecture-pattern.md`, `docs/decisions.md` | 决策 ID + 行为 + Log + Tracking 体系；bug 定位 O(n)→O(1)；全局配套更新 |
| 11 | ✅ | 分析控制台柱状图颜色统一 + 按钮状态逻辑重构 | `design/tokens.json`, `design/tokens.py`, `design/tokens.css`, `core/ui_components.py`, `apps/app_main.py` | 图表颜色与地图 POLARITY_RGBA 对齐；按钮"开始分析"→"在地图上显示"双态切换 |
| 12 | ✅ | [LB] 按钮：注记死开关 → 地图底图 Dark/Light 切换 | `apps/app_main.py`, `core/map_engine.py` | 移除 _theme JS 注入；_map_style 控制 CartoDB dark-matter/positron 底图切换；[LM]/[LB] 图标自动切换 |
| 13 | ✅ | R 默认颜色→活力橙 + 新增 [Map] 底图切换 | `apps/app_main.py`, `core/map_engine.py` | 边界色默认 #d97d5c；5种底图(CartoDB深/浅/标准 + 天地图无/有注记)；Designer 优化为 radio+色条预览 |


> 💡 标准启动指令：`@pm 开始处理 YYYY-MM-DD 的任务 N：任务名称`

> ⚠️ 策略调整 (2026-06-13)：数据爬取暂时放弃（后期购买稳定数据），MVP 焦点转为 **L1 数据治理 + L2 数据分析 端到端跑通**，确保每一层产出的数据都有实际价值。

### 📝 开发日志

**关键字**：Data Agent, 相关性筛选, DeepSeek LLM, 两层漏斗, L0→L1 治理重构, 人民城市, 情绪点样式重设计, Design Token 体系, **决策追踪系统, Decision Tracking, Trace ID**

#### 做了什么
- 创建新 Agent：📡 数据管家（Data Agent），定义在 `.claude/agents/data.agent.md`
  - 职责：L0 多源数据采集 + L1 数据治理（坐标转换/范围过滤/相关性筛选/脱敏/字段规范化）
  - 可调用：developer, gis-developer
  - 已整合入 AGENTS.md 全局调度体系（Agent 从 10 → 11）
- 新建 `SCRIPT/relevance_filter.py` L0→L1 相关性筛选模块（~330 行）
  - 第一层：关键词粗筛（30 个广告/灌水关键词），旅游/美食/探店全部放行
  - 第二层：DeepSeek LLM 精分类，判断市民城市感受 → 映射五要素（设施/环境/服务/文化/事件）
  - 批量并发（ThreadPoolExecutor，每批 5 条），3 次指数退避重试
  - 新增 L1 字段：relevance, relevance_dimensions, relevance_emotion, relevance_urban_value, relevance_summary, filter_layer
- 重构 `SCRIPT/data_governance.py` v1.0 → v1.1
  - 管线从 4 步扩展为 5 步：坐标转换 → 范围过滤 → **相关性筛选（新）** → 脱敏+导出 → L2 分析
  - 脱敏时机后移（LLM 需要原始文本做分类）
  - 无 API Key 时优雅降级跳过
- 全部走完整 SOP：Developer → Reviewer（发现 1 个 bug + 1 个优化）→ Developer 修复 → Reviewer 复审 → Tester 测试（17/17 用例通过）
- Designer 重设计情绪点显示样式：双层光晕（外层 radius=13 opacity=0.12 + 内层 radius=7 opacity=0.92 stroke=#fff）+ Neutral 从灰色改为亮琥珀色 #ffd740 → 卫星底图上可见性大幅提升
- Designer 创建完整 Design Token 体系：7 大类 150+ token（color/typography/spacing/radius/shadow/effect/component），含 JSON 单源 + CSS/Python 自动生成器 + ui_components.py 全部 Token 化
- Designer 扩展 Token 体系为 Light/Dark 双模式：tokens.json 增加 theme 层级，Dark/Light 镜像对称（深色半透明底↔浅色半透明底），CSS 支持 prefers-color-scheme 自动跟随 + [data-theme] 手动切换
- Designer 创建设计系统展示页 `apps/app_design_system.py`：独立 Streamlit Kitchen Sink，含主题切换/色板/字体/间距/圆角/阴影/组件全展示
- **PM 搭建决策追踪系统 (Decision Tracking System)**：
  - 新建 `core/tracker.py`（~280 行）：装饰器 `@track()` / 上下文管理器 `TrackContext` / 快捷函数 `trace_*()` / 全局注册表
  - 更新 debugger.agent.md：新诊断流程基于 [TRACE] 日志 + 决策 ID 精准定位
  - 更新 developer.agent.md：新增决策追踪编码标准 + 模块 ID 分配表 + 埋点规则
  - 更新 reviewer.agent.md：新增追踪点完整性审查清单
  - 更新 AGENTS.md：铁律 9/10 + 决策追踪系统说明 + 共享知识库
  - 更新 docs/architecture-pattern.md：增加决策追踪系统章节
  - 更新 docs/decisions.md：ADR-008 决策追踪系统
  - **渐进式埋点完成（13文件55追踪ID）**：全部 core/ + SCRIPT/ + apps/ + SCRAPER/ 模块已添加 @track() 装饰器和 register_track_id() 注册

#### 关键设计决策
- **相关性筛选理念**：从"是否属于城市规划领域"转变为"感知市民对城市的感受与需求"，践行"人民城市"理念
- **宽容原则**：旅游打卡、美食探店、街区体验全部保留（城市活力信号），不确定时倾向于保留
- **LLM 选型**：DeepSeek-V3（已有 API Key + 推理能力强 + 中文理解好）
- **两层漏斗**：先关键词快筛（免费），再 LLM 精分类（API），减少 API 调用量
- **决策追踪系统**：自研 `core/tracker.py`（~280 行），用决策 ID（MOD_XXX.F_NNN / D_NNN）装饰器 + 上下文管理器实现 O(1) 精准 bug 定位；全员遵守铁律 9/10 埋点规范

#### 踩坑 & 收获
- Reviewer 发现 relevance_summary 在 error 分支被覆盖 → 详细字段填充移入 else 互斥分支
- 并发累加计数器是代码异味 → 改为批次完成后从 DataFrame 列值统计
- 情绪点 Neutral 用灰色在天地图卫星底图上完全不可见 → Designer 改用亮琥珀色 #ffd740（绿→黄→红灯语义），双层光晕（外层 radius=13 opacity=0.12 + 内层 radius=7 opacity=0.92 stroke=#fff）大幅提升可见性

#### 🔜 次日计划 (2026-06-14)
- L0→L1→L2 端到端管线验证（准备有意义的测试数据 + 跑通全流程）
- L2 SnowNLP 分析结果质量评估（极性分布合理性、关键词有效性）
- 优化 L2 输出：情绪关键词提取质量 + 可视化落图

---

## 📅 2026-06-14（周日）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | LY 图层 checkbox 修复 + [确定] 按钮 | `apps/app_main.py` | 修复 _all_layers_hidden 不联动 + 新增红色确定按钮（未走 SOP，用户确认跳过） |
| 2 | ✅ | 数据层架构优化：L1_COLUMNS 重排 + v1.0 代码清理 | `SCRIPT/data_governance.py`, `apps/app_main.py` | 走完整 SOP Developer→Reviewer(2轮)→Tester；9组分组重排 + 3个DEPRECATED函数删除 + 残留导入/常量清理 |
| 3 | ✅ | L2 字段规范：confidence→l2_confidence + 新增 L2_COLUMNS | `SCRIPT/emotion_analysis_v1.py` | L2 CSV 列名改为 l2_confidence 避免与 L1 ai_confidence 冲突；新增 L2_COLUMNS 常量(9字段) |
| 4 | ⬜ | 端到端管线验证 L0→L1→L2 | `data_governance.py`, `emotion_analysis_v1.py` | 06-13 延续 |
| 5 | ✅ | L1~L4 confidence 列全局重命名：l1_confidence / l2_confidence / l3_confidence / l4_confidence | `SCRIPT/emotion_analysis_v1.py`, `docs/architecture.md`, `check_data_quality.py`, `SCRIPT/test_scripts_2.py` | 走完整 SOP；L2_COLUMNS 新增 l2/l3/l4_confidence；run_pipeline 按 phase 写入；run_full_pipeline L3/L4 写入对应置信度；架构文档字段表拆分；4 个 TrackContext 埋点 + 4 个追踪 ID 注册；Reviewer 两轮审查 + Tester 9/9 通过 |

> 💡 标准启动指令：`@pm 开始处理 2026-06-14 的任务 N：任务名称`

### 📝 开发日志

**关键字**：LY图层, 数据层架构审查, L1_COLUMNS, v1.0清退, **confidence列重命名, l1/l2/l3/l4_confidence**

#### 做了什么
- 修复 LY 图层控制 checkbox 不生效（_all_layers_hidden 与 checkbox 不联动）
- 新增红色 [确定] 按钮 + 批量操作分区优化交互
- PM 审查 L0→L2 数据管线架构，发现 5 个问题（同前）
- 数据层架构优化走完整 SOP 管线（同前）
- **L1~L4 confidence 列全局重命名走完整 SOP**：
  - PM 全局搜索 → 定位 4 文件 13 处引用
  - Developer 执行：`L2_COLUMNS` 新增 `l2_confidence`/`l3_confidence`/`l4_confidence`；`run_pipeline` 按 phase 条件写入对应置信度列；`run_full_pipeline` L3/L4 步骤分别写入 `l3_confidence`/`l4_confidence`；`docs/architecture.md` 字段表拆分 `confidence` → `l2/l3/l4_confidence`（列数 24→25/28→30/30→32）；`check_data_quality.py` / `test_scripts_2.py` 更新列名
  - Reviewer 首轮发现 3 个问题：① `run_pipeline` 硬编码 `l2_confidence` 未按 phase 区分 ② 4 个 >5 行块缺少 `TrackContext` ③ `TrackContext` 导入未使用
  - Developer 修复：if/elif/else 按 phase 写入 + 4 个 `TrackContext` 包裹（D_003~D_006）+ 追踪 ID 注册
  - Reviewer 复审通过 ✅
  - Tester 9/9 测试用例全部通过 ✅

#### 踩坑 & 收获
- Streamlit `st.dialog` 关闭时不自动触发 rerun → 需要显式"确定"按钮
- 数据层字段顺序对 CSV 可读性影响极大（人工检查时需反复滚动）
- `from pyproj import Transformer, CRS` 中 `CRS` 在函数删除后变为未使用导入，reviewer 静态分析是必要的

#### 🔜 次日计划 (2026-06-15)
- L0→L1→L2 端到端管线验证
- 用户验收本次所有改动

---

## 📅 2026-06-12（周五）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 情绪数据爬取方案调研+小范围测试（西陵区） | `SCRAPER/data_scraper.py`（新建） | Scrapy 框架搭建完成 + 小红书 Spider 测试通过（HTTP 200） |
| 2 | ✅ | ~~西陵区真实数据落图~~ → 移至 06-13 任务1，范围改为规划范围 | — | 边界从西陵区改为用户上传的规划范围 Shapefile |
| 3 | ✅ | Agent 协作体系搭建：程序开发/调试/进度管理/审查/测试/文档 Agent | `.claude/agents/*.agent.md`, `AGENTS.md` | 6 Agent + AGENTS.md + 架构记忆 + 使用场景，基础搭建完成 |
| 4 | ✅ | 系统架构优化：七层架构 + 空间分析引擎重定义 + 溯佰科定位修正 | `docs/architecture.md`, `docs/decisions.md`, `docs/dev-notes.md`, `memories/repo/architecture-pattern.md`, `SCRIPT/emotion_analysis_v1.py`, `core/map_engine.py` | PM 研判 → Developer 改代码 → PM 同步文档，SOP 首次实战 |
| 5 | ✅ | 环境同步：requirements.txt 补全 + 新增环境管家 Agent | `requirements.txt`, `.claude/agents/ops.agent.md`, `AGENTS.md` | Scrapy 未装、streamlit-folium/shapely/pyproj 漏登记 |
| 6 | ✅ | 跨机协作体系：会话交接卡 + ops 自检 + PM 交接流程 | `memories/repo/session-handoff.md`, `ops.agent.md`, `pm.agent.md`, `AGENTS.md` | 换机 `@pm 同步上下文`，下班 `@pm 下班交接` |
| 7 | ✅ | Agent 扩展：UI设计师/设计审查员/GIS开发员（10 Agent） | `.claude/agents/designer.agent.md`, `design-reviewer.agent.md`, `gis-developer.agent.md`, `AGENTS.md` | 设计→审查→迭代闭环，GIS 专项能力 |
| 8 | ✅ | 初始页面重构：左侧三功能按钮 R/D/A + 全屏地图 | `app_main.py`, `core/ui_components.py` | 极简风格，CSS 统一到 ui_components，emoji 全清 |
| 9 | ✅ | 范围选择引擎：矢量文件上传/CRS检测/缓存/边界叠加 | `core/range_selector.py`, `app_main.py`, `data/boundaries/` | 支持 .shp/.geojson/.gpkg，自动投影转换 |
| 10 | ✅ | 坐标转换工具（WGS84/GCJ02/BD09）+ 宜昌标准 CGCS2000 | `core/coord_transform.py` | 社交媒体→WGS84→CGCS2000 投影完整链路 |
| 11 | ✅ | 爬虫验证：Scrapy 2.16 兼容修复 + 24条小红书数据采集 | `SCRAPER/spiders/xiaohongshu_spider.py` | start_urls 兼容 + explore 页 SSR 提取 |
| 12 | ✅ | 全局代码审查 + UI审查 + 交互审查（三 Agent 并行） | `app_main.py`, `ui_components.py`, `export.py` | 16 项问题全部修复，通过 Tester 验证 |

### 📝 开发日志

**关键字**：Agent扩展, UI重构, 范围引擎, 坐标转换, 跨机协作, 审查闭环, Scrapy兼容

#### 做了什么
- Agent 阵容从 6 → 10 个（新增 Ops/Designer/Design Reviewer/GIS Developer）
- 初始页面重构：左侧 R/D/A 三按钮 + 全屏地图，极简 ASCII 统一风格
- 范围选择引擎：支持 .shp/.geojson/.gpkg 上传，CRS 自动检测转换，边界叠加
- 坐标转换工具：GCJ02/BD09→WGS84，宜昌标准 CGCS2000_3_Degree_GK_CM_111E
- Scrapy 2.16 兼容修复：start_urls 空列表 bug + explore 页 SSR 数据提取
- 全局代码/UI/交互三 Agent 并行审查，16 项问题全部修复
- 跨机环境同步 + 会话交接卡体系
- CSS 统一收归 ui_components.py，空状态引导，emoji 全清

#### 踩坑 & 收获
- Streamlit @st.dialog 内 st.rerun() 导致对话框消失 → 去掉 rerun，利用自动重跑
- file_uploader 残留问题 → 最终去掉对话框内上传，改为读取 data/boundaries/ 目录
- 旧建成区文件 11280 区域导致卡顿 → 清理残留，0.1s 秒开
- Shapefile 单文件无法读取 → 多文件上传 + 子文件夹组织
- Scrapy 2.16 要求 start_urls 非空 → 加占位 start_urls 兼容
- geom.crs 不存在 → 改为 gdf.crs
- 边界只在数据加载后显示 → 空状态也叠加（selected_ranges 判定）

#### 碎片想法
- Tester Agent 必须每次都用，不通过不提交
- GIS 开发员和 Tester 交叉核实 CRS 很有价值
- SHP→GeoJSON 当前方案已足够，暂不需要独立转换工具

#### 🔜 06-13(周六)
- 西陵区真实数据落图（L1 数据治理 + 坐标转换 + 范围过滤）
- 数据爬取方案最终确定（登录 API vs 购买数据）
- 空间分析引擎 MVP（缓冲区分析 + 行政单元聚合）开始编码


## 📅 2026-06-11（周四）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | L2/L3/L4 三级分析架构重构 | `emotion_analysis_v1.py`, `config.py`, `map_engine.py`, `ui_components.py`, `export.py` | 五级极性、引擎模板、导出命名统一 |
| 2 | ✅ | 入口统一：CLI + Tkinter + Streamlit 共用 run_analysis_task() | `run_analysis.py`, `app_main.py`, `launch.py` | 控制台合并进 main 为子页面，删 analysis_console.py |
| 3 | ✅ | GBK 编码修复 + docs/ 文档体系 | 全项目 `.py`, `docs/*.md` | emoji→ASCII，\_safe_print，架构规范入记忆 |

### 📝 开发日志

**关键字**：重构, 架构, 编码, GUI, 路由

#### 做了什么
- 重构 EmotionResult 为 L2→L3→L4 三级叠加结构，五级极性全链路更新
- 新增 run_analysis_task() 统一分析入口，CLI/Tkinter/Streamlit 全部调用它
- analysis_console 合并进 app_main，用 `?page=console` 路由，只启一个端口 8501
- 建立 docs/ 五文件（dev-notes/architecture/decisions/todo/scenarios）
- Tkinter GUI 美化，状态栏清晰
- 全项目 emoji 换 ASCII([OK]/[WARN]/[LOAD])，\_safe_print 防崩溃

#### 踩坑 & 收获
- Windows GBK 编码是最大坑——emoji 在 print/Streamlit 中反复崩溃，最终全量替换 + \_safe_print 解决
- builtins.print 劫持导致递归无限循环，改用显式 \_safe_print() 调用
- `?page=console&file=xxx` 路由模式是未来子页面的标准做法

#### 碎片想法
- 三入口统一到 run_analysis_task() 是正确的架构决策
- 导出含 L2/L3/L4 阶段标识，溯源清晰

#### 🔜 明日
- 西陵区数据爬取启动 + Agent 协作体系搭建


## 📅 2026-06-10（周三）及之前

| 日期 | 关键进展 |
|------|----------|
| 06-09 | SnowNLP pipeline 初版、点状地图、CSV/GeoJSON 导出、模块化重构 |
| 05-28~31 | 课题启动：20 轮对话确定三段式框架、技术栈、七大应用场景 |


## 🗂 长期备忘

| # | 想法 | 状态 |
|---|------|------|
| L1 | LLM 大模型接入（溯佰科平台 Agent 嵌入） | ⬜ |
| L2 | 时序分析（多时间切片对比） | ⬜ |
| L3 | 行政区划聚合视图 | ⬜ |
| L4 | 自动报告生成（PDF） | ⬜ |
| L5 | 空间自相关分析（Moran's I） | ⬜ |
| L6 | 问题-对策映射引擎 | ⬜ |
| L7 | Docker 部署 | ⬜ |
| L8 | 配置外部化（.env） | ⬜ |
| L9 | 移动端适配 | ⬜ |
| L10 | 语料库本地化词典 | ⬜ |
| L11 | 空间分析引擎 MVP（缓冲区分析 + 行政单元聚合） | ⬜ |
