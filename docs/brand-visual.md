# 品牌视觉规范 (Brand Visual Guidelines)

> 修改前端视觉、调颜色、调间距时必读本文档。
>
> **⚠ 双套 token（2026-06-17）**：`design/tokens.json` 含两套系统：
>
> - **原 Streamlit 系统**（`--em-*`）：服务于遗留 `apps/` Streamlit + `core/ui_components.py`。
> - **`geojson` 段**（`--geojson-*`）：服务于前端主界面 `frontend/`（MapLibre GL JS，geojson.io 1:1），经 `generate_css.py` 生成 `frontend/css/tokens.css`。
>
> **改前端配色** → 改 `geojson` 段；本文档下半「色彩体系/地图标记样式」同时适用于两套（情绪五级色板语义一致）。

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

## 字体系统 (Typography)

> 所有字体相关 token 在 `design/tokens.json` 的 `geojson.typography` / `geojson.color.text` 段，
> 经 `generate_css.py` 生成 `--geojson-typography-*` / `--geojson-color-text-*` 变量。
> **禁手改 `frontend/css/tokens.css`**——改 json 后重跑生成器。

### 0. 信息层级原则（总纲，贯穿一切组合式信息）

看板 / 表格 / 分析图 / 图例 / 条目罗列等**一切组合式信息显示**，必须**优先突出关键内容、弱化次要内容**。
通过以下手段实现（全部映射到本体系 token，不另起炉灶）：

| 手段 | 做法 |
|------|------|
| ① 颜色深浅 | 关键=`text-primary`(深)，正文=`secondary`(中)，次要=`tertiary`(浅) |
| ② 字号大小 | 关键数值/标题=`lg–2xl`，正文=`sm/base`，标注=`xs/2xs` |
| ③ 位置 | 关键内容居中或前置（左/顶），次要靠边/后置/折叠 |
| ④ 胶囊底色 | 关键标签/状态用胶囊 pill（`pill-bg` 淡底 + `pill-fg` 品牌字）；中性胶囊=`gray-100` 底 + `text-secondary` 字 |
| ⑤ 疏密 | 关键区块用 `line-height-relaxed` + 更大留白；列表/表格次要区用 `normal/none` 收紧 |

> 范例：右栏 info-card（键名 `xs secondary` + 关键值 `sm bold primary`）、popup（极性胶囊 + 分数 `xl bold`）、
> 统计大数字（`xl bold primary tabular-nums`）、表格（表头 `xs tertiary` 弱化、单元格 `primary`）。

### 1. 字体族 (Font Family)

系统字体栈，**零网络加载**（国内 CDN 不稳，不加 Web 字体）：

| token | 栈 | 用途 |
|-------|----|------|
| `--geojson-typography-sans` | `'Open Sans','Inter',system-ui,-apple-system,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif` | 全站默认（PingFang/Hiragino 兼顾 macOS 中文，YaHei 兜底 Windows） |
| `--geojson-typography-mono` | `'Source Code Pro',ui-monospace,'Cascadia Code',Consolas,monospace` | 数据/坐标/ID 等需对齐的数字与代码 |

### 2. 字号阶梯 (Font Size)

根字号 16px（1rem）。从 2xs→2xl 覆盖全部场景，**禁止裸 px 字号**：

| token | rem | px | 典型用途 |
|-------|-----|----|---------|
| `size-2xs` | 0.625 | 10 | 极弱标注、刻度、attribution |
| `size-xs`  | 0.75  | 12 | 元信息、表头、说明小字 |
| `size-sm`  | 0.875 | 14 | 正文、表格单元格、按钮 |
| `size-base`| 1     | 16 | 区段标题、强调正文 |
| `size-lg`  | 1.125 | 18 | 副标题、popup 正文 |
| `size-xl`  | 1.25  | 20 | 面板标题、关键数值 |
| `size-2xl` | 1.5   | 24 | 页面标题、统计大数字 |

### 3. 字重 (Font Weight)

| token | 值 | 用途 |
|-------|----|------|
| `weight-normal`   | 400 | 正文 |
| `weight-medium`  | 500 | 次级强调、按钮 |
| `weight-semibold`| 600 | 区段标题、键名 |
| `weight-bold`    | 700 | 标题、关键数值 |

### 4. 行高 / 字距 (Line Height / Letter Spacing)

**行高**：

| token | 值 | 用途 |
|-------|----|------|
| `line-height-none`    | 1     | 图标/单行控件 |
| `line-height-tight`   | 1.25  | 标题 |
| `line-height-normal`  | 1.5   | 正文 |
| `line-height-relaxed` | 1.625 | 图例/长说明 |

**字距**：

| token | 值 | 用途 |
|-------|----|------|
| `letter-spacing-tight`  | -0.01em | 大标题收紧 |
| `letter-spacing-normal` | 0       | 默认 |
| `letter-spacing-wide`   | 0.02em  | 页面标题 |
| `letter-spacing-wider`  | 0.04em  | 全大写小标题（区段头） |

### 5. 3 级字体浓度 (Text Color Ramp，浅底用)

中性灰，WCAG-aware，**浓度分 深 / 中 / 浅 3 级**（5 级过细、3 级层次更清晰）。
配合信息层级：越关键越深、越大。

> 最深一级取自工具栏 **Import** 按钮字色（`chrome-text` `#404040`），中/浅同步下调（对齐灰阶 gray-700/500/400）。

| 浓度 | token | 值 | 用途 |
|------|-------|----|------|
| 深 | `--geojson-color-text-primary`   | `#404040` | 标题、关键数值、正文强调 |
| 中 | `--geojson-color-text-secondary` | `#737373` | 正文、次要内容 |
| 浅 | `--geojson-color-text-tertiary`  | `#a3a3a3` | 说明、元信息、表头、占位提示 |

特殊用途（非浓度阶梯）：
- `--geojson-color-text-disabled` = `#cfcfcf`（禁用态，比浅更淡）
- `--geojson-color-text-inverse` = `#ffffff`（**深色底专用**，纯白）
- `--geojson-color-text-inverse-soft` = `rgba(255,255,255,0.7)`（深色底上的次要文字）

### 6. 深 / 浅底配字规则（核心）

**判定法（relative luminance）**：面亮度 L ≥ 0.5 → **浅底**（配深色 ramp）；L < 0.5 → **深底**（配 inverse 白）。
例：品牌蓝 `#007afc` L≈0.27 → 深底 → 白字；面板白 `#ffffff` L=1 → 浅底 → 深灰字。

**固定组合**：
- **浅底** → `text-primary`…`text-tertiary`（深灰 ramp，深/中/浅 3 级）
- **深底** → `text-inverse`（白）/ `text-inverse-soft`（白 70%）

**面清单（每个 surface 打标）**：
- 浅：`surface-page/panel/panelAlt/map-bg`、`section-*/table-*/import-panel-*` 各 bg
- 深：`chrome-title-bar-bg`（顶栏 navy）、`brand-primary`（品牌蓝按钮）、卫星影像底图（运行时影像，比例尺/图例叠白字）

### 7. 禁用纯黑规

**禁止使用纯黑 `#000`/`#000000` 作为字体颜色**——纯黑过于突兀、破坏整体观感。
全站最深的字体色 = `text-primary` `#404040`（柔和深灰，取自工具栏 Import 按钮字色）。深色底上的白字允许纯白 `#ffffff`。

### 8. 场景应用表

| 场景 | size | weight | color | line-height |
|------|------|--------|-------|-------------|
| 页面/面板标题 | lg–2xl | bold | primary | tight |
| 区段标题 | base/sm | semibold | primary | normal |
| 正文 | sm/base | normal | secondary | normal |
| 次要/说明 | sm | normal | tertiary | normal |
| 元信息/标注 | xs/2xs | medium | tertiary | normal |
| 数据/数值 | sm(mono) | medium | primary | none |
| 占位/禁用 | sm | normal | tertiary/disabled | normal |
| 深底文字 | sm | semibold | inverse | normal |

### 9. 符号与排版规则

- **数字/数据** → `mono` + `font-variant-numeric: tabular-nums`（等宽对齐，如统计卡大数字、表格数值列）
- **单位空格**：字母单位前空格（`12 km`、`30.7080, 111.2860`），度/百分号贴数字（`60°`、`85%`）
- **标点**：中文用全角（，。：），英文/数字用半角；中英混排视觉间距靠 letter-spacing，不手动加空格
- **标记符**：沿用 ASCII `[OK]/[WARN]/[LOAD]/[ERR]`（详见 `docs/copywriting-style.md`，禁 emoji）
- 等宽字体仅用于数据展示；间距遵循 Design Token 体系（`--geojson-spacing-*`）

## 字体与间距（旧）

> 上方「字体系统」为权威规范，本节保留作快速索引：
- 等宽字体用于数据展示
- 不使用 emoji（全部 ASCII 标记）
- 间距遵循 Design Token 体系：详见 `design/tokens.json`

## 源文件

- **唯一源**：`design/tokens.json`（手动编辑，含原系统 + `geojson` 段两套）
- **生成文件（遗留 Streamlit）**：`design/tokens.py` + `design/tokens.css`（由 `design/generate_css.py` 生成）
- **生成文件（前端 frontend/）**：`frontend/css/tokens.css`（由 `design/generate_css.py` 从 `geojson` 段生成）
