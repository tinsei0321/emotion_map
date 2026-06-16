---
name: ui-design-system
description: 情绪地图 UI 设计系统 — 颜色/按钮/布局/交互 全部铁律
metadata:
  type: reference
---

# 情绪地图 UI 设计系统

> 基于 geojson.io 设计语言 | 2026-06-15

## 一、色彩

| Token | 值 | 用途 |
|-------|-----|------|
| 品牌蓝 | `#007afc` | Primary 按钮、toggle 激活、焦点环 |
| Hover 蓝 | `#0060c7` | Primary 按钮 hover |
| 标题栏底 | `#1a2940` | 顶部标题栏 48px |
| 工具栏底 | `#ffffff` | 顶部工具栏 44px |
| 工具栏边框 | `#e5e5e5` (gray-200) | 工具栏底部分隔线 |
| 面板底 | `#ffffff` | 左侧面板 |
| 面板边框 | `#e5e5e5` | 1px solid |
| 主文字 | `#171717` (gray-900) | 标题、重要文字 |
| 次要文字 | `#525252` (gray-600) | 辅助说明 |
| 禁用文字 | `#d4d4d4` (gray-300) | 禁用按钮 |
| 按钮 default | `#ffffff` 底 + `#525252` 字 | 工具栏按钮 |
| 按钮 hover | `#d4d4d4` 底 + `#171717` 字 | 工具栏按钮 hover |
| 弹窗遮罩 | `rgba(0,0,0,0.2)` | 模态弹窗背景 |
| Toast 底 | `rgba(36,39,48,0.94)` | 居中提示条 |

## 二、按钮

| 层级 | 样式 | 场景 |
|------|------|------|
| **工具栏按钮** | 36×36 方形, 4px 圆角, 白底无边框, 粗体, hover 灰底 `#d4d4d4` | R/LY/A/OV/TB/H/M |
| **工具栏长条** | 72×36 矩形, 4px 圆角, 同上 | Import/Export |
| **Primary** | `#007afc` 蓝底白字, hover `#0060c7` | 确认/上传/显示/开始分析 |
| **Secondary** | `#fff` 白底 + `#d4d4d4` 1px 边框 + `#525252` 字 | 取消/清空 |
| **禁用** | `opacity:0.5; cursor:not-allowed` | 无数据时禁用 |

## 三、间距规则

- 标准方形按钮：`S=36px`, 间距：`G=8px`, 圆角：`R=4px`
- 定位公式：`left/right = 12 + Σ(prev_width + G)`
- **改按钮宽度 → 必须更新后续所有按钮位置**

## 四、双层顶栏

```
标题栏 48px  #1a2940 深蓝底  白字 "宜昌市情绪地图 v1.0"
工具栏 44px  #ffffff 白底    bottom-border: 1px #e5e5e5
按钮 top: 52px (48 + 4 padding)
```

## 五、左侧面板

- 260px 宽, 白底, 4px 圆角, 微弱阴影
- `<details>` 原生折叠（数据一览/图层一览）
- 图层开关用 LY 弹窗控制（面板仅展示）

## 六、Toast 通知

- 全屏正中央 `top:50%;left:50%;transform:translate(-50%,-50%)`
- 胶囊形 `border-radius:100px`
- 暗底白字, 2s 自动淡出
- **地图上任何变化都必须触发**（见 [[toast-notification-rule]]）

## 七、Dialog 规则

- 控件 toggle/checkbox 回调 **禁止** `st.rerun()`
- 确认/批量按钮 **需要** `st.rerun()`
- `register_layer()` 更新已有图层时 **必须** 重置 `visible=True`
- 详见 [[streamlit-dialog-patterns]]

## 八、Streamlit 主题

`.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#007afc"
```

## 九、字体

- 工具栏按钮：粗体 700, 0.75rem
- 标题：1rem, 粗体 600, 白色

## 十、教训

- **Streamlit `st.radio` 不可深度自定义 CSS**：它不是原生 `<input type="radio">`，而是 BaseWeb 组件。`appearance:none`、`::before` 等技巧对它无效。需要用按钮列表模拟单选。
- **Toast 动画重播**：CSS animation 在 Streamlit DOM patch 下不会自动重播。用 `st.empty()` 强制每次新建 DOM 元素。

**Why:** 积累了一晚上的 UI 调试经验，必须文档化避免重复犯错。
**How to apply:** 修改任何 UI 相关代码前，先读本文件和相关 memory。
