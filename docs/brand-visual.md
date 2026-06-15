# 品牌视觉规范 (Brand Visual Guidelines)

> 修改前端视觉、调颜色、调间距时必读本文档。

## 色彩体系

### 情绪五级色板（地图标记 + 图表）

| 极性 | 颜色 | 色值 | 用途 |
|------|------|------|------|
| Very Positive | 蓝绿 | `#1ABC9C` | 极度满意 |
| Positive | 蓝 | `#5DADE2` | 一般正面 |
| Neutral | 浅灰 | `#C0C0C0` | 中性 |
| Negative | 琥珀橙 | `#F0A050` | 一般负面 |
| Very Negative | 珊瑚红 | `#E06050` | 严重不满 |

### 地图标记样式

- **双层光晕**：外层 radius=13 opacity=0.12 + 内层 radius=7 opacity=0.92
- **描边**：白色 `#fff` stroke=1
- **Neutral 色**：亮琥珀色 `#ffd740`（避免在卫星底图上不可见）

## 主题

- 支持 **Light / Dark** 双模式
- CSS 自动跟随系统 `prefers-color-scheme`
- 手动切换通过 `[data-theme="dark"]` / `[data-theme="light"]`

## 按钮颜色

| 功能 | 颜色 | 说明 |
|------|------|------|
| R（范围） | `#d97d5c` 活力橙 | 范围选择 |
| D（数据） | — | 数据管理 |
| A（分析） | — | 分析控制台 |

## 字体与间距

- 等宽字体用于数据展示
- 不使用 emoji（全部 ASCII 标记）
- 间距遵循 Design Token 体系：详见 `design/tokens.json`

## 源文件

- **唯一源**：`design/tokens.json`（手动编辑）
- **生成文件**：`design/tokens.py` + `design/tokens.css`（由 `design/generate_css.py` 生成）
