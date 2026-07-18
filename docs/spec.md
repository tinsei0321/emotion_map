# 产品规范文档 (Specification)

> 情绪地图 (Emotion Map) v1.0 — 技术实现规范
> 本文档定义"怎么做才对"，是 Developer / Reviewer / Tester 的共同参考基准。
>
> **⚠ 2026-07-18 退役声明**：`apps/` Streamlit 层 + `launch.py` 已整层退役（前端 `frontend/` 完全接管，启动 `py frontend/serve.py 8080`）。下文 1.1~1.3「遗留 Streamlit」规格及涉及 `apps/` / `:8501` 的描述仅作历史记录，不再有效。

---

## 一、入口与路由规范

> **⚠ 前端迁移（2026-06-17）**：前端主 UI 面 = [`frontend/`](../frontend/)（MapLibre GL JS，geojson.io 1:1），启动 `py -m http.server 8080`，浏览器开 `http://127.0.0.1:8080/frontend/index.html`，详见 [`frontend/README.md`](../frontend/README.md)。
>
> 1.1~1.3 以下为**遗留 Streamlit**（:8501）规格，仅维护不扩展，不再新增页面。

### 1.1 遗留 Streamlit 主应用（迁移期遗留）

| 项目 | 规范 |
|------|------|
| 端口 | **8501**（唯一端口，不允许新增端口） |
| 启动命令 | `py launch.py` 或 `python -m streamlit run apps/app_main.py`（遗留） |
| 页面路由 | `st.query_params['page']` 分发 |
| 路由注册位置 | `app_main.py` → `main()` 函数顶部路由表 |
| 返回机制 | 每个子页面函数末尾 `return`（不依赖后续逻辑） |

### 1.2 路由表

| 路由 | 函数 | 说明 |
|------|------|------|
| 默认 (`/`) | `show_map_browser()` | 全屏地图浏览器 |
| `?page=console` | `show_analysis_console()` | 分析控制台 |
| `?page=console&file=xxx` | `show_analysis_console()` | 分析控制台（自动加载结果） |
| `?page=design-system` | `show_design_system()` | 设计系统展示页 |

### 1.3 新增子页面流程

1. 在 `app_main.py` 新建 `show_xxx_page()` 函数
2. 在 `main()` 路由表注册：`if page == 'xxx': show_xxx_page(); return`
3. 侧边栏放 `[返回地图浏览器](/)` 链接
4. 页面间跳转用 `st.link_button` 或 `st.markdown` 链接

### 1.4 分析入口统一

- CLI / Tkinter / 遗留 Streamlit / 前端 API **所有入口调用同一个** `run_analysis_task()`
- 入口函数签名：`run_analysis_task(input_file: str, output_dir: str, l2_only: bool = False) -> Optional[str]`
- 返回值：输出 CSV 路径（成功）或 None（失败）
- 禁止任何入口绕过统一函数直接调用 `SnowNLPAnalyzer` 或 `run_pipeline()`

---

## 二、数据管道规范

### 2.1 数据层级定义

```
L0 (原始爬取) → L1 (数据治理) → L2 (情绪分析) → L3 (语义增强) → L4 (多维归因)
```

每一级：
- 独立输出 CSV 文件
- 不破坏前级字段（叠加添加，不修改）
- 文件名包含层级标识

### 2.2 文件命名规范

| 层级 | 目录 | 命名模板 | 格式 |
|------|------|----------|------|
| L0 | `DATA/raw/` | `{source}_{YYYYMMDD}_{scope}_raw.csv` | CSV |
| L1 | `DATA/processed/` | `{name}_L1_result_csv.csv` | CSV |
| L2 | `DATA/processed/` | `{name}_L2_result_csv.csv` | CSV |
| L2 GeoJSON | `DATA/processed/` | `{name}_L2_result_geojson.geojson` | GeoJSON |
| L3 | `DATA/processed/` | `{name}_L3_result_csv.csv` | CSV |
| L4 | `DATA/processed/` | `{name}_L4_result_csv.csv` | CSV |

### 2.3 字段规范（逐级对照）

#### L0 字段 (13 列)

| 序号 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 1 | `source` | str | 数据来源平台 |
| 2 | `url` | str | 原文链接 |
| 3 | `crawl_time` | datetime | 爬取时间 ISO 8601 |
| 4 | `title` | str | 标题 |
| 5 | `text` | str | 正文（情绪分析主文本源） |
| 6 | `comments` | str | 评论 |
| 7 | `area` | str | 爬取时的区域标签 |
| 8 | `tags` | str | 原始标签 |
| 9 | `like_count` | int | 点赞数 |
| 10 | `comment_count` | int | 评论数 |
| 11 | `publish_time` | str | 发布时间 |
| 12 | `lon_gcj02` | float | 原始 GCJ-02 经度 |
| 13 | `lat_gcj02` | float | 原始 GCJ-02 纬度 |

#### L1 新增字段 (13 列, 共 26 列)

| 序号 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 14 | `lon` | float | **WGS84 经度 (EPSG:4326)** — GeoJSON 导出/地图渲染基准 |
| 15 | `lat` | float | **WGS84 纬度 (EPSG:4326)** |
| 16 | `x_cgcs2000` | float | CGCS2000 EPSG:4546 投影 X（米），宜昌规划基准 |
| 17 | `y_cgcs2000` | float | CGCS2000 EPSG:4546 投影 Y（米） |
| 18 | `id_e` | str | 稳定行标识符（格式：`e0001`~`eNNNN`） |
| 19 | `scope` | str | 空间过滤使用的边界名称 |
| 20 | `location_mentioned` | str | LLM 识别的地点提及 |
| 21 | `keywords` | str | jieba 提取的关键词（逗号分隔） |
| 22 | `text_length` | int | 文本长度（字符数） |
| 23 | `relevance` | str | 城市相关性判定（relevant / irrelevant） |
| 24 | `relevance_category` | str | 相关性分类（设施/环境/服务/文化/事件） |
| 25 | `primary_emotion` | str | LLM 判定的一级情绪标签 |
| 26 | `emotion_intensity` | int | 情绪强度 1~5 |
| 27 | `urban_value` | str | 城市治理价值（high / medium / low） |
| 28 | `l1_confidence` | float | L1 LLM 分类置信度 0~1 |
| 29 | `has_location` | bool | 文本是否包含地点信息 |
| 30 | `spatial_hotspot` | str | 空间热点类型（生成器注入） |
| 31 | `spatial_type` | str | 空间分布类型（生成器注入） |

> **变更记录 (2026-06-15)**：L1 从 spec 原定 20 列修正为 26 列。新增 6 个 LLM 分类字段（location_mentioned, relevance, relevance_category, primary_emotion, emotion_intensity, urban_value, l1_confidence, has_location）+ 2 个空间字段（spatial_hotspot, spatial_type）；移除 `in_scope` 和 `_kw_pass`（已不再使用）。

#### L2 新增字段 (3 列, 共 29 列)

| 序号 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 32 | `score` | float | SnowNLP 综合情绪得分 0~1 |
| 33 | `polarity` | str | 五级极性 |
| 34 | `l2_confidence` | float | L2 置信度 0~1（文本长度归一化） |

> 注：`keywords` 字段已上移至 L1（jieba 关键词在数据治理阶段预提取）。

#### L3 多模态增强字段 (7 列, 共 36 列)

| 序号 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 35 | `vision_score` | float | 视觉情绪得分 0~1（火山引擎 Ark Vision） |
| 36 | `vision_scene` | str | 场景分类（公园/街道/商店/餐厅/交通/…） |
| 37 | `vision_objects` | str | 检测到的城市相关物体（JSON 数组） |
| 38 | `vision_summary` | str | 图像内容摘要 |
| 39 | `vision_confidence` | float | 视觉分析置信度 0~1 |
| 40 | `ocr_text` | str | OCR 提取的文字（讯飞 iFlytek） |
| 41 | `ocr_confidence` | float | OCR 置信度 0~1 |

### 2.4 坐标规范

| 列名 | 坐标系 | EPSG | 用途 |
|------|--------|------|------|
| `lon_gcj02` / `lat_gcj02` | GCJ-02（火星坐标） | — | 原始留存，不可溯源时置 None |
| `lon` / `lat` | **WGS84** | 4326 | 所有地图渲染/GeoJSON 导出/空间分析基准 |
| `x_cgcs2000` / `y_cgcs2000` | CGCS2000 | 4546 | 宜昌城市规划标准投影（米制运算） |

**转换链**：`GCJ-02 → WGS84（数学转换，~100-700m 偏移）→ CGCS2000 EPSG:4546（投影，<1m 偏差）`

### 2.5 情绪极性规范

#### 五级极性（标准）

| 极性 | 分数区间 | 颜色 | 含义 |
|------|----------|------|------|
| Very Negative | [0.00, 0.20) | `#E06050` 珊瑚红 | 严重不满 → 紧急干预 |
| Negative | [0.20, 0.40) | `#F0A050` 琥珀橙 | 一般负面 → 关注改善 |
| Neutral | [0.40, 0.60) | `#C0C0C0` 浅灰 | 中性/无明显情绪 |
| Positive | [0.60, 0.80) | `#5DADE2` 蓝 | 一般正面 → 维持 |
| Very Positive | [0.80, 1.00] | `#48C9B0` 蓝绿 | 非常满意 → 标杆 |

#### 颜色系统规格

- **配色原则**：低饱和、适中明度，在卫星深色底图上清晰可辨
- **点状标记**：双层光晕（外层 radius=13 opacity=0.12 + 内层 radius=7 opacity=0.92 stroke=#fff）
- **热力图梯度**：冷热模式用白→黄→橙→红；极性模式用绿渐变(正面)/灰渐变(负面)

### 2.6 L1 相关性筛选规范

**两层漏斗**：
1. **第一层** — 关键词粗筛（免费）
   - 30 个广告/灌水关键词黑名单
   - 旅游/美食/探店全部放行
   - 判断：可疑保留 + 明确无关过滤
2. **第二层** — DeepSeek LLM 精分类（API）
   - 输入：经过第一层筛选的文本
   - 输出：relevance (bool) + dimensions + emotion + urban_value + summary
   - 批量并发：ThreadPoolExecutor，每批 5 条
   - 重试策略：3 次指数退避
   - 无 API Key 时优雅降级跳过

**新增 L1 字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `relevance` | bool | 是否与城市感受相关 |
| `relevance_dimensions` | str | 相关维度（设施/环境/服务/文化/事件） |
| `relevance_emotion` | str | 情绪倾向（正面/负面/中性） |
| `relevance_urban_value` | bool | 是否有城市感知价值 |
| `relevance_summary` | str | LLM 分类理由简述 |
| `filter_layer` | str | 过滤层级标识（keyword/llm/pass） |

### 2.7 脱敏规范

- **时机**：L1 管道最后一步（LLM 分类之后，导出之前）
- **处理列**：`comments` 全覆盖写空字符串
- **禁止出现在输出**：用户名、用户ID、手机号、邮箱、IP 地址
- **保留**：文本正文（分析需要）、坐标（可视化需要）、发布时间

---

## 三、UI 组件规范

> **⚠ 定位（2026-06-17，更新 2026-06-27）**：3.1~3.3 为**遗留 Streamlit** UI 规格（Folium iframe / HUD 按钮 / st.dialog）。
>
> 前端主界面 `frontend/` 的导航架构规格见下文 **§3.4**（Martin 范式，ADR-016）；启动手册见 [`frontend/README.md`](../frontend/README.md)。

### 3.1 布局规范

| 区域 | 位置 | 实现 |
|------|------|------|
| 地图 | 全屏 100%×100% | Folium iframe `position:fixed; top:0; left:0; width:100vw; height:100vh` |
| 标题栏 | 顶部居中 | `position:fixed; top:10px; left:50%; transform:translateX(-50%); z-index:10000` |
| HUD 按钮组 | 左侧垂直排列 | `position:fixed; left:10px; top:50%; transform:translateY(-50%); z-index:9999` |
| 图例面板 | 右下角 | `position:fixed; right:10px; bottom:10px; z-index:9998` |
| 统计面板 | 左下方 | HUD 按钮右侧 |
| 弹窗 | 居中 | `st.dialog` |

### 3.2 HUD 按钮面板规格

| 按钮 | 标签 | 功能 | 触发方式 |
|------|------|------|----------|
| [R] | Range | 范围选择弹窗 | `st.dialog` |
| [D] | Data | 数据源选择 + 概览弹窗 | `st.dialog` |
| [A] | Analyze | 分析控制台子页面 | `?page=console` 跳转 |
| [Map] | Map Style | 底图切换 radio | 内嵌 radio 控件 |
| [LM]/[LB] | Light Mode/Brightness | Dark/Light 底图切换 | 按钮 toggle |
| [?] | Legend | 图例显示/隐藏 | 按钮 toggle |

### 3.3 Design Token 规范

**Token 源**：`design/tokens.json`（单一数据源）

**7 大类**：
| 类别 | 前缀 | 示例 |
|------|------|------|
| Color | `--em-` | `--em-primary`, `--em-bg`, `--em-text` |
| Typography | `--em-font-` | `--em-font-size-sm` |
| Spacing | `--em-space-` | `--em-space-md` |
| Radius | `--em-radius-` | `--em-radius-md` |
| Shadow | `--em-shadow-` | `--em-shadow-sm` |
| Effect | `--em-effect-` | `--em-blur` |
| Component | `--em-comp-` | `--em-comp-hud-btn-size` |

**双主题**：每个 Token 有 Light / Dark 两套值
- CSS 自动跟随：`prefers-color-scheme` 媒体查询
- 手动切换：`[data-theme="dark"]` / `[data-theme="light"]` 属性选择器

**生成管道**：
```
tokens.json (源) → generate_css.py → tokens.css
                 → tokens.py      → Python 常量
```

### 3.4 前端主界面导航架构（frontend/ MapLibre，Martin 范式）

> ADR-016 落地规格。3.1~3.3 为遗留 Streamlit。控制台 α v0.1 = 三页架构之一（ADR-015）。

**布局区域**（geojson.io 1:1 外壳）：

| 区域 | 位置 | 规格 | 实现 |
|------|------|------|------|
| 顶栏 | 顶部全宽 | 单层 48px 深蓝底白字；面包屑「宜昌市情绪地图 › 控制台 α v0.1」+ Import/Export/i 靠右 | `#header` `.draw-tool` |
| 左栏 | 左侧 | 默认 240px（`--left-w`），三区结构；可拖宽 ≥220px | `#left-panel` `.lp-zone-{select,tools,operate}` |
| 地图 | 中央 | 全屏 MapLibre + 天地图 WMTS；左下 5 按钮簇 + 上方 3 按钮集 | `#map` `.emotion-tools-ctrl` |
| 右面板 | 右侧 | Overview / Table 双 tab（active = `#384555` 深灰实心） | `#right-panel` `.ptab` |
| 参数栏 | 左栏右缘 | 紧贴 `#left-panel` 右缘悬浮（`left:var(--left-w)` 随动 B6），默认隐藏，1:2 分栏 | `#param-panel` |

**左栏三区**（tab 互斥，`setActiveTab`）：

| 区 | 内容 | 说明 |
|----|------|------|
| 区1 选择 | Range / Layers / Toolbox tab | 互斥显隐 pane；文件夹按当前 tab 触发 range/import-input |
| 区2 工具栏 | `[+][文件夹][方片叠加][眼睛][垃圾桶]…[漏斗 计数]` | 白底 + `#384555` 图标 + hover 浅灰；`+`/方片叠占位 toast |
| 区3 操作 | 滚动操作区 | 仅滚动 |

**色彩与控件单源**：

- 品牌蓝 `--geojson-color-brand-primary: #4285F4`（同 `chrome-active-fill`/`brand-selected`）；深灰文字/图标 `--geojson-color-card-fill: #384555`（**非底色**）。
- 半透明蓝（选中态填充等）走 `color-mix(in srgb, var(--geojson-color-brand-primary) N%, transparent)`，**勿**写死 `rgba(0,122,252)`/`#007afc`（旧蓝，已清退；`--geojson-brand` 为幽灵 token 已修）。
- 胶囊选项集（线型/色板/分析类型）：无线框 + 阴影 + 选中蓝底白字 + 悬停灰（`--geojson-radius-md` 6px）。
- `.swatch` 调色板 = 圆角矩形（`--geojson-radius-md`）；`.ov-swatch`/`.stat-cell .swatch` = 图例小圆点，保留圆形。
- Token 源同 §3.3：`design/tokens.json` → `generate_css.py` → `frontend/css/tokens.css`。

---

## 四、导出规范

### 4.1 CSV 导出

- **编码**：UTF-8 BOM（Excel 兼容中文）
- **分隔符**：逗号
- **索引**：不输出 DataFrame 默认索引
- **空值处理**：保留为空字符串（不填 "N/A"）

### 4.2 GeoJSON 导出

- **坐标系**：WGS84 (EPSG:4326)
- **坐标列**：使用 `lon` / `lat`（不是 `lon_gcj02` / `lat_gcj02`）
- **属性**：包含除 L0 原始坐标外的所有字段
- **空坐标**：跳过（不写入 FeatureCollection）

### 4.3 导出文件清单

每次 L2 分析完成后自动生成：
1. `{name}_L1_result_csv.csv`
2. `{name}_L2_result_csv.csv`
3. `{name}_L2_result_geojson.geojson`

---

## 五、追踪系统规范

### 5.1 模块 ID 分配

| 模块 ID | 文件 | 编号范围 |
|---------|------|----------|
| `MOD_GOV` | `SCRIPT/data_governance.py` | F_001~ / D_001~ |
| `MOD_ANA` | `SCRIPT/emotion_analysis_v1.py` | F_001~ / D_001~ |
| `MOD_REL` | `SCRIPT/relevance_filter.py` | F_001~ / D_001~ |
| `MOD_RUN` | `SCRIPT/run_analysis.py` | F_001~ / D_001~ |
| `MOD_LOADER` | `core/data_loader.py` | F_001~ / D_001~ |
| `MOD_MAP` | `core/map_engine.py` | F_001~ / D_001~ |
| `MOD_TRANSFORM` | `core/coord_transform.py` | F_001~ / D_001~ |
| `MOD_RANGE` | `core/range_selector.py` | F_001~ / D_001~ |
| `MOD_EXPORT` | `core/export.py` | F_001~ / D_001~ |
| `MOD_UI` | `core/ui_components.py` | F_001~ / D_001~ |
| `MOD_APP` | `apps/app_main.py` | F_001~ / D_001~ |
| `MOD_SCRAPER` | `SCRAPER/spiders/` | F_001~ / D_001~ |
| `MOD_TRACKER` | `core/tracker.py` | F_001~ / D_001~ |

### 5.2 埋点规则

| 场景 | 方式 | 要求 |
|------|------|------|
| 公开函数（非 `_` 前缀） | `@track("MOD_XXX.F_NNN")` | 必须 |
| 关键分支（> 5 行 if/else/循环体） | `with TrackContext("MOD_XXX.D_NNN", ...)` | 必须 |
| I/O 操作（文件读写/API/DB） | `TrackContext` 包裹 | 必须 |
| 数据管道步骤 | 记录 `in_n` / `out_n` | 建议 |
| except 块 | `trace_error()` | 必须 |

### 5.3 ID 注册要求

- 所有追踪 ID 必须在 `core/tracker.py` 末尾注册表登记
- 编号连续不跳号
- 废弃 ID 标记为 `DEPRECATED`，不回收编号

---

## 六、性能预算

| 指标 | 预算 | 测量点 |
|------|------|--------|
| 地图首次渲染（遗留 Streamlit） | ≤ 3s | `create_base_map()` + `streamlit_folium` |
| 地图首次渲染（前端 frontend/） | ≤ 3s | MapLibre GL JS + 天地图瓦片（待实测标定） |
| 1000 点 marker 添加 | ≤ 2s | `add_point_layer()` 执行时间 |
| 5000 点热力图生成 | ≤ 3s | `add_heatmap_layer()` 执行时间 |
| 1000 条 SnowNLP 分析 | ≤ 10s | `SnowNLPAnalyzer.analyze_batch()` |
| LLM 50 条分类 | ≤ 30s | `relevance_filter.py` 批量分类 |
| Shapefile 加载 | ≤ 2s | `geopandas.read_file()` |
| CSV 导出 10000 行 | ≤ 1s | `pandas.to_csv()` |
| 边界坐标转换 | ≤ 1s | `coord_transform.py` |

---

## 七、配置规范

### 7.1 配置项管理

- **全局常量**：`core/config.py`
- **可调参数**（暂在 config.py，未来 .env）：
  - `TIANDITU_KEY` — 天地图 API Key
  - `DEEPSEEK_API_KEY` — DeepSeek API Key（暂不在 config.py）
  - `POLARITY_THRESHOLDS` — 情绪极性阈值
  - `COLOR_MAP` — 情绪颜色映射
  - `DEFAULT_CENTER` — 默认地图中心
  - `DEFAULT_ZOOM` — 默认缩放级别

### 7.2 路径规范

```
_PROJECT_ROOT/
  DATA/
    raw/              # L0 原始爬取
    processed/        # L1~L4 分析结果
    boundaries/       # 矢量边界文件 (.shp/.geojson/.gpkg)
  core/               # 基础设施层
  SCRIPT/             # 分析引擎层
  SCRAPER/            # 数据采集层
  apps/               # 应用层
  design/             # Design Token 系统
  docs/               # 文档
  .claude/agents/     # Agent 定义
  .claude/            # Claude Code 配置
```

---

## 八、编码规范

### 8.1 铁律（必须遵守）

1. **禁用 emoji**：只允许 ASCII 标记 `[OK]` `[WARN]` `[LOAD]` `[ERR]`
2. **安全打印**：所有 `print()` 必须通过 `_safe_print()` 调用
3. **禁止劫持 builtins.print**：不得重新绑定 `builtins.print`
4. **入口统一**：前端主界面 = `frontend/`（MapLibre）；遗留 Streamlit 仅 :8501，不再新增页面
5. **分析逻辑共用**：所有入口调用同一个 `run_analysis_task()`
6. **导出命名**：`{name}_{L1|L2|L3|L4}_result_csv.csv`
7. **数据脱敏**：输出禁止包含用户名/用户ID
8. **空间范围优先**：采集以 Polygon 为第一过滤条件
9. **决策追踪必埋点**：公开函数 `@track()`，关键分支 `TrackContext`
10. **追踪 ID 必注册**：所有 ID 在 `core/tracker.py` 注册表登记

### 8.2 代码风格

- **Python**：PEP 8（4 空格缩进，120 字符行宽）
- **导入顺序**：标准库 → 第三方库 → 本地模块
- **文档字符串**：Google style（`Args:` / `Returns:` / `Raises:`）
- **类型注解**：公开函数建议添加（Python 3.14+ 语法）
- **私有函数**：`_` 前缀（如 `_build_text_for_classification`）

### 8.3 文件组织

- 每个 `.py` 文件开头顶部有模块文档字符串（`"""..."""`）
- 模块文档字符串描述本文件职责和核心类/函数
- 核心模块 ≤ 500 行（超过需拆分）

---

## 九、测试规范

### 9.1 测试文件

| 文件 | 用途 |
|------|------|
| `SCRIPT/test_scripts.py` | 逐条分析测试（小规模） |
| `SCRIPT/test_scripts_2.py` | 向量化分析测试（大规模） |
| `SCRIPT/test_scripts_heatmap.py` | 热点图独立调试 |
| `SCRIPT/generate_test_data.py` | 测试数据生成 |
| `SCRIPT/generate_l1_mock.py` | L1 Mock 数据生成 |
| `check_data_quality.py` | 数据质量检测 |

### 9.2 测试用例要求

- Tester Agent 每次验证至少覆盖：正常输入、边界输入、空输入
- 输出检查项：文件存在性、列名正确性、行数一致性、字段值有效性
- 测试报告结论：通过 / 失败 + 失败用例清单

---

## 十、依赖规范

### 10.1 核心依赖（requirements.txt）

| 包 | 版本要求 | 用途 |
|----|----------|------|
| streamlit | >=1.35 | 遗留前端应用框架（迁移期） |
| streamlit-folium | >=0.20 | 遗留 Streamlit Folium 集成 |
| folium | >=0.17 | 遗留地图可视化（core/map_engine.py） |
| pandas | >=2.0 | 数据处理 |
| geopandas | >=0.14 | 地理数据处理 |
| shapely | >=2.0 | 空间运算 |
| pyproj | >=3.6 | 坐标系转换 |
| snownlp | >=0.12 | 情绪分析 |
| jieba | >=0.42 | 中文分词 |
| altair | >=5.0 | 统计图表 |
| pydeck | >=0.8 | 遗留高级地图可视化 |
| openai | >=1.0 | LLM API 调用（DeepSeek 兼容） |

### 10.2 环境要求

- Python 3.14+
- pip 最新版
- 虚拟环境推荐（venv）
- Windows 需注意 GBK 编码兼容

---

## 十一、附录

### A. Agent SOP 流程速查

```
用户需求
  → PM（拆解 + 路由）
    → 纯逻辑：Developer → Reviewer → Tester → 用户验收
    → 纯 UI：Designer → Design Reviewer → 用户验收
    → 逻辑+UI：Designer（设计稿）→ Developer（按稿编码）→ Reviewer → Tester → 用户验收
```

### B. 文档索引

| 文档 | 用途 |
|------|------|
| `docs/prd.md` | 产品需求（做什么） |
| `docs/spec.md` | 产品规范（怎么做才对） — 本文档 |
| `docs/architecture.md` | 系统架构（怎么做） |
| `docs/architecture-pattern.md` | 架构规范（编码约束） |
| `docs/decisions.md` | 技术决策 (ADR) |
| `docs/todo.md` | 任务追踪 |
| `docs/scenarios.md` | 应用场景灵感 |
| `docs/dev-notes.md` | 开发笔记 |
