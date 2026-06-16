#

**Ready for review**Select text to add comments on the plan

# 情绪地图 — Streamlit → MapLibre GL JS 完整迁移计划

> 2026-06-16 | 全功能复刻 + UI 优化

## 上下文

当前 Streamlit 前端交互体验已达框架天花板——dialog 嵌套 bug、tooltip 弱、按钮状态不可靠、布局靠 CSS hack。MapLibre GL JS 是 WebGIS 工业标准，迁移后获得：完整的 Web 地图交互、MVT 矢量瓦片百万级流畅、完全的 UI 控制、溯佰科对接时前端可直接复用。

**核心原则**：后端（`core/`、`SCRIPT/`、`api/`）完全不动，只重写前端。

***

## 一、新项目结构

```
emotion_map/
├── frontend/              ← 新增：MapLibre GL JS 前端
│   ├── index.html         # 入口 HTML
│   ├── css/
│   │   ├── tokens.css     # 扁平化 CSS 变量（从 design/tokens.json 迁移，只保留 Light 主题）
│   │   ├── layout.css     # 全屏地图 + 工具栏 + 面板布局
│   │   ├── buttons.css    # 按钮三级体系
│   │   ├── dialogs.css    # 弹窗样式
│   │   ├── legend.css     # 图例
│   │   └── toast.css      # Toast 动画
│   ├── js/
│   │   ├── main.js        # 入口：初始化地图 + 绑定事件
│   │   ├── map.js          # MapLibre 地图实例 + 底图切换 + 天地图
│   │   ├── layers.js       # 点图层 + 热力图 + 边界图层 + 选中标记
│   │   ├── toolbar.js      # 工具栏按钮渲染 + 事件绑定
│   │   ├── panel.js        # 左侧面板：数据概览 + 图层列表
│   │   ├── dialogs.js      # 弹窗管理器：打开/关闭/动画
│   │   ├── import-dialog.js    # DATA 数据源弹窗
│   │   ├── analysis-dialog.js  # ANA 情绪分析弹窗
│   │   ├── range-dialog.js     # RNG 分析范围弹窗
│   │   ├── overview-dialog.js  # OV 数据概览弹窗
│   │   ├── table-dialog.js     # TB 数据表格弹窗
│   │   ├── export-dialog.js    # Export 导出弹窗
│   │   ├── basemap-dialog.js   # Map 底图切换弹窗
│   │   ├── layer-dialog.js     # LY 图层控制弹窗
│   │   ├── governance-dialog.js# GV 数据治理弹窗
│   │   ├── api.js         # FastAPI 后端通信（fetch 封装）
│   │   └── state.js        # 前端状态管理（替代 session_state）
│   └── assets/
│       └── favicon.svg
├── api/                   # 已有，扩展端点
├── core/                  # 不动
├── SCRIPT/                # 不动
├── DATA/                  # 不动
├── apps/                  # Streamlit 前端 — 保留但不再开发
└── design/                # tokens.json 保留作为设计源
```

## 二、技术选型

| **层**    | **选型**                        | **理由**                    |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 地图       | MapLibre GL JS 5.x            | WebGIS 标准，MIT 协议，MVT 瓦片   |
| 底图       | 天地图 WMTS + CartoDB GL Styles  | 国内加载快，与现有一致               |
| 构建       | 纯 HTML/CSS/JS（无框架）            | 零学习成本，文件少，直接打开即用          |
| 样式       | CSS 变量                        | 从 tokens.json 直接映射        |
| 弹窗       | 原生 `<dialog>` + CSS animation | 现代浏览器全支持                  |
| 图表       | Chart.js（CDN）                 | 替代 Altair，轻量 60KB         |
| 后端通信     | Fetch API                     | 调用 FastAPI `/api/v1/*` 端点 |
| HTTP 服务器 | FastAPI 托管静态文件                | 一个端口同时提供 API + 前端         |

## 三、Design Token 扁平化

当前 `tokens.json` 有 525 行，Light + Dark 双主题。迁移策略：

1. 只保留 `--color-*`、`--space-*`、`--radius-*`、`--font-*`、`--shadow-*` 变量
2. 去掉 Dark 主题（MapLibre 前端先用 Light）
3. 去掉 component 级 Token（按钮/弹窗在图例中的 Token 在新前端直接写在对应 CSS 文件）
4. 保留 geojson.io 设计语言：
   * Brand: `#007afc`
   * 情绪五色: Very Positive `#78DC32`, Positive `#5DADE2`, Neutral `#C0C0C0`, Negative `#C4956A`, Very Negative `#B92D2D`
   * 间距: 4px 基准，8px 按钮间距
   * 圆角: 4px 默认，6px 弹窗
   * 字体: system-ui, 0.875rem 正文, 0.75rem 辅助
   * 过渡: 150ms cubic-bezier(.4,0,.2,1)

## 四、布局结构

```
┌─ 标题栏 48px (#1a2940) ───────────────────────────────────┐
│  宜昌市情绪地图 v1.0                                        │
├─ 工具栏 44px (#fff, border-bottom #e5e5e5) ────────────────┤
│  [R] [LY] [A] [OV] [TB]      [H]      [Import] [Export]   │
├────────────────────────────────────────────────────────────┤
│ ┌─ 左侧面板 260px ──┐                                      │
│ │ ▶ 数据一览         │        MapLibre 地图 (flex:1)        │
│ │   范围: 规划范围    │                                      │
│ │   文件: xxx.csv    │                                      │
│ │                    │                                      │
│ │ ▶ 图层一览         │                                      │
│ │ ● L1 xxx          │         [图例] 右下角                  │
│ │ ○ L2 xxx          │                                      │
│ └────────────────────┘                                      │
│                                          [M] 左下角         │
└────────────────────────────────────────────────────────────┘
```

## 五、弹窗迁移对照

| **当前 Streamlit**          | **MapLibre `<dialog>`** | **宽度** | **内容**                               |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `show_data_source_dialog` | `import-dialog.js`      | 400px  | select → fetch `/api/v1/data` → 文件列表 |
| `show_analysis_dialog`    | `analysis-dialog.js`    | 600px  | radio 引擎选择 → fetch `/api/v1/analyze` |
| `show_range_dialog`       | `range-dialog.js`       | 550px  | FileReader + 图层行渲染                   |
| `show_overview_dialog`    | `overview-dialog.js`    | 650px  | Chart.js 柱状图 + 统计卡                   |
| `show_table_dialog`       | `table-dialog.js`       | 750px  | 搜索框 + 可滚动表格                          |
| `show_export_dialog`      | `export-dialog.js`      | 400px  | radio + download                     |
| `show_basemap_dialog`     | `basemap-dialog.js`     | 400px  | 颜色色块 + radio                         |
| `show_layer_dialog`       | `layer-dialog.js`       | 400px  | toggle 列表                            |
| `show_governance_dialog`  | `governance-dialog.js`  | 600px  | 文件选择 + 进度条 + 结果                      |
| `show_settings_dialog`    | —                       | —      | 迁移中省略，开发工具                           |

## 六、图层迁移对照

| **pydeck**                                 | **MapLibre GL JS**                                             |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `pdk.Layer('ScatterplotLayer')`            | `map.addLayer({type:'circle', paint:{'circle-color': [...]}})` |
| `pdk.Layer('HeatmapLayer')`                | `map.addLayer({type:'heatmap'})`                               |
| `pdk.Layer('GeoJsonLayer')` ×2 (glow+line) | 两个 `line` layer，不同 width + opacity                             |
| `pdk.Layer('ScatterplotLayer')` 选中标记       | `map.addLayer({type:'circle'})` ×2                             |
| `create_base_map()`                        | `new maplibregl.Map({style: {...}})`                           |

**点图层数据驱动样式**（用 MapLibre expressions 替代 RENDER\_TIERS）：

```js
'circle-color': ['match', ['get', 'polarity'],
    'Very Positive', '#78DC32',
    'Positive', '#5DADE2',
    'Neutral', '#C0C0C0',
    'Negative', '#C4956A',
    'Very Negative', '#B92D2D',
    '#888']
```

**tooltip → MapLibre popup**：

```js
map.on('click', 'emotion-points', (e) => {
    const props = e.features[0].properties;
    new maplibregl.Popup()
        .setHTML(`<div>...${props.tt_polarity}...</div>`)
        .setLngLat(e.lngLat)
        .addTo(map);
});
```

## 七、实施步骤

### Phase 1 — 骨架 + 地图（\~6h）

| **#** | **任务**              | **产出**                                              |
| -------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 1.1   | 创建 `frontend/` 目录结构 | index.html + css/ + js/                             |
| 1.2   | 迁移 Design Token     | `css/tokens.css`（扁平化 CSS 变量）                        |
| 1.3   | 布局 CSS              | `css/layout.css`：全屏地图 + 固定工具栏 + 左侧面板                |
| 1.4   | MapLibre 地图实例       | `js/map.js`：初始化 + 天地图 WMTS + CartoDB 样式切换           |
| 1.5   | 点图层                 | `js/layers.js`：GeoJSON source + circle layer + 五级色板 |
| 1.6   | Tooltip/Popup       | 点击显示详情卡片                                            |
| 1.7   | FastAPI 静态文件托管      | `api/main.py` 增加静态文件路由                              |

**Phase 1 验证**：浏览器打开 → 看到地图 → 加载情绪点 → 点击出 popup。

### Phase 2 — 工具栏 + 面板（\~4h）

| **#** | **任务** | **产出**                                            |
| -------------------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 2.1   | 工具栏按钮  | `js/toolbar.js`：R/LY/A/OV/TB/Import/Export/M/H 按钮 |
| 2.2   | 左侧面板   | `js/panel.js`：数据一览 + 图层一览，折叠展开                    |
| 2.3   | 图例     | 右下角浮动五级色板                                         |
| 2.4   | Toast  | CSS animation toast                               |

### Phase 3 — 弹窗（\~10h）

| **#** | **弹窗**     | **产出**                                     |
| -------------------------------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| 3.1   | 弹窗框架       | `js/dialogs.js`：`<dialog>` 管理器，打开/关闭/动画    |
| 3.2   | Import 数据源 | 文件列表（fetch `/api/v1/data`）→ 加载数据到地图        |
| 3.3   | ANA 情绪分析   | 引擎选择 → fetch `/api/v1/analyze` → 进度 → 结果加载 |
| 3.4   | RNG 分析范围   | 文件上传 + 图层列表 + 样式编辑                         |
| 3.5   | OV 数据概览    | Chart.js 柱状图 + 统计卡                         |
| 3.6   | TB 数据表格    | 搜索 + 表格 + 下载                               |
| 3.7   | Export 导出  | 格式选择 + 下载                                  |
| 3.8   | Map 底图     | 色块 + radio 切换                              |
| 3.9   | LY 图层      | toggle 列表                                  |
| 3.10  | GV 数据治理    | fetch `/api/v1/governance` + 进度条           |

### Phase 4 — 图层 + 交互完善（\~4h）

| **#** | **任务**             |
| -------------------------------------------------------- | --------------------------------------------------------------------- |
| 4.1   | 热力图切换（H 按钮）        |
| 4.2   | 边界图层（多图层管理）        |
| 4.3   | 选中点高亮（金色圆环）        |
| 4.4   | 点图层分级渲染（按数据量自适应半径） |
| 4.5   | 键盘快捷键（Esc 关闭弹窗等）   |

### Phase 5 — 后端对接 + 联调（\~4h）

| **#** | **任务**                               |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 5.1   | FastAPI 新增 GeoJSON 返回端点              |
| 5.2   | CSV 文件上传端点                           |
| 5.3   | 前后端联调，全流程跑通                          |
| 5.4   | 旧的 Streamlit `apps/` 目录标记 deprecated |

**总工时**：\~28h（4-5 天 AI 辅助开发）

## 八、API 端点扩展

| **端点**                 | **方法** | **用途**                   | **新增/已有** |
| ------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `/api/v1/health`       | GET    | 健康检查                     | 已有        |
| `/api/v1/data`         | GET    | 列出可用数据文件                 | 已有        |
| `/api/v1/analyze`      | POST   | 运行情绪分析                   | 已有        |
| `/api/v1/governance`   | POST   | 运行数据治理                   | 已有        |
| `/api/v1/points`       | GET    | 返回情绪点 GeoJSON（支持 ?bbox=） | 新增        |
| `/api/v1/points/stats` | GET    | 极性统计                     | 新增        |
| `/api/v1/boundaries`   | GET    | 边界 GeoJSON 列表            | 新增        |
| `/api/v1/upload`       | POST   | CSV/GeoJSON 文件上传         | 新增        |
| `/api/v1/export`       | POST   | 导出 CSV/GeoJSON           | 新增        |

## 九、UI 优化（相对于当前 Streamlit）

| **优化点** | **当前**             | **MapLibre**                            |
| ---------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 地图交互    | hover 仅 tooltip    | click 打开详情卡片 + popup                    |
| 弹窗动画    | Streamlit 原生       | 400ms ease-out + 遮罩淡入                   |
| 按钮状态    | disabled 灰显，无过渡    | 150ms transition + hover 色变             |
| 图层切换    | 弹窗内 toggle → rerun | 面板内 toggle → map.setLayoutProperty 即时生效 |
| 底图切换    | 弹窗 → rerun         | 弹窗 → map.setStyle 即时切换                  |
| 范围上传    | 弹窗内 file\_uploader | 弹窗内 FileReader + 拖拽上传                   |
| 数据表格    | st.dataframe       | HTML table + 虚拟滚动                       |
| Toast   | st.toast           | CSS animation toast + 3s 自动消失           |
| 空状态     | 禁用按钮               | 引导提示覆盖层                                 |

## 十、验证方法

1. `python -m pytest tests/ -q` — 后端 56 tests 通过
2. 浏览器打开 `http://localhost:8000` — 地图 + 工具栏 + 面板显示正常
3. Import → 加载数据 → 点渲染 → 点击出 popup
4. A → 选引擎 → 分析 → 结果加载到地图
5. 所有弹窗打开/关闭动画正常，无 JS 错误
