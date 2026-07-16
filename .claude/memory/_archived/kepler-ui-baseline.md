---
name: kepler-ui-baseline
description: Kepler.gl 风格 UI 基准设置 — 以后所有 UI 优化均基于此版
metadata:
  type: project
---

# Kepler UI 基准 (2026-06-15 确认)

## 核心设置（不要回退）

### 全屏地图
- pydeck_chart **不使用** `height` 参数（保持默认，由 CSS 控制）
- canvas CSS: `100vw × 100vh, position:fixed, top:0, left:0, z-index:0`
- Streamlit chrome 完全隐藏 (header/footer/sidebar)
- `inject_fullscreen_css()` 负责全屏逻辑

### HUD 工具栏（Kepler 风格）
- 位置: **右侧竖排浮动** `position:fixed, right:12px`
- 顺序 (上→下): [R] [D] [A] [M] [H] [*]
- 底部左下: [OV] [TB] [LY]
- 尺寸: 40×40px, border-radius 4px
- 色板: 背景 #29323C, hover #3A404F, 文字 #D3D8E0
- 毛玻璃: `backdrop-filter: blur(8px)`
- `hud_button_style_css()` 负责 HUD 定位和样式

### 默认主题
- **Light 模式** (carto_light 底图)
- `_map_style` 默认值: `carto_light`

### 备份
- 完整备份在 `design/backups/ui-20260615-1548/`
- 恢复命令: `bash design/backups/restore.sh`

### 关键文件
- `core/ui_components.py` — 全屏 CSS + HUD CSS + 图例
- `apps/app_main.py` — 按钮布局 + 主题默认值

**Why:** 经过 Kepler.gl 源码色板对齐 + 全视口地图 + HUD 浮动布局改造，用户确认效果满意。以后在此基准上继续。
**How to apply:** 任何 UI 修改不要回退上述设置。如果要改颜色/位置/大小，通过 Design Token 修改，不要硬编码。
