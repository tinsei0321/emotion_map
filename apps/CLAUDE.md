# apps/ — Streamlit 迁移期遗留层 CLAUDE.md

> 优先级: 本文件 > 项目根 CLAUDE.md > 全局 CLAUDE.md
>
> **⚠ 定位（2026-06-17）**：`apps/`（Streamlit :8501）= **迁移期遗留层，仅维护不扩展**。
> 前端主 UI 面 = [`frontend/`](../frontend/)（MapLibre GL JS，geojson.io 1:1），**新功能一律进 `frontend/`**，权威前端规范见 [`frontend/README.md`](../frontend/README.md)。
> 本文件：前半（模块职责/文件清单/路由/约定）= 遗留 Streamlit 维护规范；末尾「UI 组件规范」段 = `frontend/` 设计规格备查。

## 模块职责

遗留 Streamlit 前端应用。所有页面通过 `?page=` 路由统一管理（遗留，不再新增页面）。

## 文件清单

| 文件 | 职责 |
|------|------|
| `app_main.py` | 主应用入口 + 路由分发 + 地图/对话框/图例 (~1470行) |
| `app_console.py` | 分析控制台页面（?page=console） — 独立拆分 |
| `app_design_system.py` | 设计系统展示页（Kitchen Sink） |

> `register_layer()` 函数已提取至 `core/layer_registry.py`，被 `app_main.py` 和 `app_console.py` 共享。

## 路由规范

- 端口: **8501**（唯一）
- 路由方式: `st.query_params['page']`
- 路由表在 `app_main.py` 的 `main()` 中

```
/                          → 地图浏览器（默认）
/?page=console             → 分析控制台
/?page=design-system       → 设计系统
```

## 新增页面流程

1. 在 `app_main.py` 创建 `show_xxx_page()` 函数
2. 在 `main()` 路由表中注册: `if page == 'xxx': show_xxx_page(); return`
3. 侧边栏放返回链接: `[返回地图浏览器](/)`
4. 页面间跳转: `st.link_button` 或 `st.markdown`，URL 格式 `/?page=xxx`

## Streamlit 特殊约定

- 使用 `st.session_state` 保持地图中心/缩放（避免 rerun 后复位）
- **`@st.dialog` 内 `st.rerun()` 规则**（详见 `.claude/memory/_archived/streamlit-dialog-patterns.md`，Streamlit 遗留快照）：
  - ❌ toggle/checkbox/radio 等控件的值变更回调中**禁止** `st.rerun()` — Streamlit 自动重绘 dialog
  - ✅ "确定"/"确认"/"关闭"按钮 + 批量操作按钮中**需要** `st.rerun()` — 用户明确表示操作完成
  - ✅ Toast 通知使用 `st.session_state['_toast']` 模式，不在 dialog 内直接 `st.markdown`
- CSS 统一注入: 通过 `core/ui_components.py` 管理
- Design Token: 使用 `design/tokens.py` 中的 Python Token，不硬编码颜色
- Dark/Light 主题: 通过 CSS `[data-theme]` 切换

## UI 组件规范

> **主 UI 面 = `frontend/`（MapLibre GL JS，geojson.io 1:1）**。Streamlit(`app_main.py` :8501) 为迁移期遗留，新功能一律进 `frontend/`。
> geojson.io 设计语言权威规格见 [docs/vision-inbox/latest.md](../docs/vision-inbox/latest.md) 与计划 Part F；颜色一律走 `design/tokens.json` 的 `geojson` 段（单源，经 `generate_css.py` 生成 `frontend/css/tokens.css`）。

- **两层深色头栏**（`#1a1a1a` chrome）：上层标题「宜昌市情绪地图 v1.0」加粗；下层工具栏 = 左对齐绘制工具 `Select/Point/Line/Polygon/Rectangle/Circle/(more)`（占位，加粗英文首字母 S/P/L/Po/R/C，圆角方形 32px，hover 浅亮、选中常亮蓝 `#007afc`）+ 右对齐 `Import / Export`（圆角矩形文字按钮）+ `M`(切换底图)。
- **左侧栏**（默认折叠，可拖拽宽）：`Import` 面板（拖放 + 支持类型列表）→ 导入后切换为 `Range / Layers / Analysis` 三个可折叠区段（深石板蓝 `#2c3e50` 头、白字 UPPERCASE、chevron）。
- **右侧栏**（可拖拽宽）：`Overview`（文件/图层/L1·L2 信息卡 + 五级统计 + 迷你柱状图）+ `Table`（geojson.io 表格：深列头 `#343a40`、悬停 `#f1f3f5`）。
- **点击交互**：点情绪点 / 范围线 → 右下角浮动浮窗（`#feature-popup`，280px，非居中、非贴点），`×` 关闭。
- **折叠/拖拽**：左右侧栏各有显眼折叠钮（面板边缘竖向中点，40×40 半透明深底 + 白边）与 8px `col-resize` 拖拽条。
- **底图**：仅 4 张天地图（影像 img 有/无注记 + 常规 vec 有/无注记），默认影像无注记，WMTS 瓦片加载；CartoDB 已移除（CN 被墙）。
- **情绪点**：保留五级语义色（`geojson.emotion`，唯一非 chrome-蓝处）；选中态 `#007afc` 光环。
- 所有 UI 文本使用 ASCII 标记（无 emoji）。

## 禁止事项

- 不要创建新的 Streamlit 端口（统一用 8501）
- 不要在 `@st.dialog` 的控件回调中调用 `st.rerun()`（明确按钮除外，见上方约定）
- 不要硬编码颜色值（使用 Design Token）
- 不要绕过 `core/ui_components.py` 直接写内联 CSS
- 不要修改路由表格式（保持 `if page == 'xxx':` 模式）
