# apps/ — Streamlit 应用层 CLAUDE.md

> 优先级: 本文件 > 项目根 CLAUDE.md > 全局 CLAUDE.md

## 模块职责

Streamlit 前端应用。所有页面通过 `?page=` 路由统一管理。

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
- `@st.dialog` 内不要调用 `st.rerun()`（会导致对话框消失）
- CSS 统一注入: 通过 `core/ui_components.py` 管理
- Design Token: 使用 `design/tokens.py` 中的 Python Token，不硬编码颜色
- Dark/Light 主题: 通过 CSS `[data-theme]` 切换

## UI 组件规范

- 左侧面板: R(范围)/D(数据)/A(分析) 三功能按钮
- 地图标记: 双层光晕 + Material 色板
- 情绪颜色: 绿(正面)→黄(中性)→红(负面) 渐变
- 所有 UI 文本使用 ASCII 标记（无 emoji）

## 禁止事项

- 不要创建新的 Streamlit 端口（统一用 8501）
- 不要在 `@st.dialog` 内调用 `st.rerun()`
- 不要硬编码颜色值（使用 Design Token）
- 不要绕过 `core/ui_components.py` 直接写内联 CSS
- 不要修改路由表格式（保持 `if page == 'xxx':` 模式）
