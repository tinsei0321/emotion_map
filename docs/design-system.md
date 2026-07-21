# EmotionMap 设计系统规范

> v1.0 | 2026-07-21 | 配色 + UI + 交互 + Token 全栈设计规范
>
> 本文档是 EmotionMap 前端设计的 single source of truth。涵盖：情绪五级色带（Dark/Light 双模式）、EMC 面板三级权重系统、情境式渐进披露交互逻辑、设计 Token 制作与生成管线。后续所有 UI 改动以此为准。

---

## 一、情绪五级色带（核心）

### 1.1 设计语义

情绪色带是一条**连续发散带**，语义 = 情绪温度：

```
正（冷青绿）= 积极 → 清新、健康、有活力
  #0F6E56 深青绿 ── veryPositive（极正）
  #5DCAA5 青绿   ── positive（正）
  #C0C0C0 浅灰   ── neutral（中性）
  #F0997B 浅珊瑚  ── negative（负）
  #D85A30 深珊瑚橙 ── veryNegative（极负）
负（暖珊瑚橙）= 消极 → 紧张、低沉、需关注
```

**方向说明**：本方案采用"正冷/负暖"（与中国股市"涨红跌绿"同向），与早期"正暖/负冷"方案相反。选择"正冷/负暖"的理由：
- 青绿 = 清新/健康/平静 → 契合"情绪好"的心理联想
- 珊瑚橙 = 温暖/警觉/需关注 → 契合"情绪差"的警示语义
- CVD（色盲）友好：青绿 vs 珊瑚橙在色相和明度上均有足够区分度

### 1.2 贯穿场景

同一条色带贯穿全站所有情绪相关渲染：

| 场景 | 用法 | 文件 |
|------|------|------|
| 地图渲染 | 情绪散点/热力/网格填充色 | `state.js emotionColors()` |
| EMC 结论卡 | 顶部 8px 极性色带 | `ai_qa.css .aiq-conclusion-band.*` |
| 图例 | 五级色阶条 | `legend.css` |
| 时间轴 | 情绪轨迹线/区域填充 | `time-bar.css` |
| 4x5 矩阵 | 归因热力单元格底色 | `district-stats.js` |
| 答案内联 | 区域名后 8x8px 色方块 | `ai_qa.css .emotion-swatch.*` |

### 1.3 Dark / Light 双模式色值

| 极性 | Dark 模式（默认） | Light 模式 | 说明 |
|------|-------------------|------------|------|
| veryPositive | `#5DCAA5` | `#0F6E56` | Dark 用亮青绿（在深底上可见），Light 用深青绿 |
| positive | `#9FE1CB` | `#5DCAA5` | Dark 用浅青绿，Light 用中青绿 |
| neutral | `#E6E6E6` | `#C0C0C0` | Dark 用亮灰（在深底上可读），Light 用中灰 |
| negative | `#F5C4B3` | `#F0997B` | Dark 用浅珊瑚，Light 用中珊瑚 |
| veryNegative | `#F0997B` | `#D85A30` | Dark 用中珊瑚（避免深底上暗色不可见），Light 用深珊瑚橙 |

**配色铁律**：
- Dark 模式：深底 + 浅字，emotion 色值取 **浅端**（保证在深底上可读）
- Light 模式：浅底 + 深字，emotion 色值取 **深端**（保证在浅底上可读）
- 两模式色值**不同**，但语义一致——由 token 系统自动切换

### 1.4 CVD 安全验证

| 组合 | 正常视觉 | 红绿色盲 | 蓝黄色盲 | 全色盲 |
|------|---------|---------|---------|--------|
| veryPositive vs veryNegative | 青绿 vs 珊瑚橙 | 明度差异足够 | 色相差异足够 | 明度差异足够 |
| positive vs negative | 浅青绿 vs 浅珊瑚 | 可区分 | 可区分 | 可区分 |

---

## 二、EMC 面板三级权重系统

### 2.1 问题定义

当前 EMC 面板（`ai_qa.css`）存在三宗罪：
1. **视觉黑洞**：整块炭黑 `#1f1f1f` 嵌在浅色左栏中，会议室投影更糟
2. **层级平铺**：过程卡/结论卡/审查卡同宽左侧 2px 竖条，用户找不到结论
3. **工程师自嗨**：token 容量圈（`ctx-cap`）是技术指标，用户不关心

### 2.2 三级权重设计

```
一级（浮出）── 结论卡：白底 + 阴影 lg + 顶部 8px 极性色带
                用户视线第一落点，"答案是什么"

二级（折叠）── 过程卡：浅灰底 + 无线框 + 默认折叠
                思考链/工具调用，点击才展开

三级（胶囊）── 审查：收成一行"质量 N/7 ✓"胶囊
                hover 才展开 7 条 checklist
```

### 2.3 结论卡结构

```
┌─────────────────────────────┐
│ ████████ 8px 极性色带 ████████ │  ← 按答案整体极性染色
│─────────────────────────────│
│ 诊断结论                      │  ← 标题
│ 西陵区居住情绪整体偏暖...      │  ← 正文（GIS 术语翻译成大白话）
│ [情绪最低 2.1] [偏冷 2.6]     │  ← 极性 chip（色带取色）
│ 冷区 2 个 · 样本 3,420 条     │  ← 统计行（monospace）
└─────────────────────────────┘
  box-shadow: lg（浮出感）
  border-radius: 12px
```

### 2.4 过程卡结构

```
┌─────────────────────────────┐
│ > 展开 ReAct 思考链（3 轮）    │  ← 默认折叠，点击展开
└─────────────────────────────┘
  background: gray-100
  border: none
  border-radius: 6px
```

### 2.5 审查胶囊结构

```
┌─────────────────────────────┐
│ ● 质量 7/7 通过 (hover 展开)  │  ← 默认只显示一行
└─────────────────────────────┘
  hover 后展开：
┌─────────────────────────────┐
│ ✓ data_driven  ✓ actionable  │
│ ✓ scale_fit    ✓ professional│
│ △ layout      △ concise     │
│ ✓ structure                  │
└─────────────────────────────┘
```

### 2.6 答案内联微可视化

在 EMC 的文字答案中，提到区域极性时自动插入 8x8px 情绪色方块：

```
"二马路片区 ████████ 情绪得分 2.1/5"
            ^^^^^^^^ emotion-swatch.very-negative（8x8px 珊瑚橙方块）
```

提到对比时插入 40px 迷你双向条形：

```
"居住 ██████░░░░ 商业 ░░░░██████"
       ^^^^^^^^^^^^ 40px 双向条形（正/负）
```

### 2.7 token 容量圈替代

将工程师向的 token 容量圈（`ctx-cap`）替换为用户语言：

```
┌─────────────────────────────┐
│ ○ 已掌握 3 层数据 (hover 详情) │  ← 图标 + 数据层数
└─────────────────────────────┘
  hover 展开：
  - 居住情绪（12,847 条）
  - 商业情绪（5,231 条）
  - 西陵区边界（69 km2）
```

---

## 三、Dark / Light 双模式切换

### 3.1 切换机制

```html
<!-- 默认 Dark 模式 -->
<html data-theme="dark">

<!-- 用户切换 Light 模式 -->
<html data-theme="light">
```

CSS 通过 `[data-theme]` 属性选择器切换变量：

```css
/* Dark 模式（默认） */
:root, [data-theme="dark"] {
  --geojson-color-surface-panel: #1f1f1f;
  --geojson-color-text-primary: #ECECEC;
  --geojson-color-emotion-very-positive: #5DCAA5;
  --geojson-color-emotion-positive: #9FE1CB;
  --geojson-color-emotion-neutral: #E6E6E6;
  --geojson-color-emotion-negative: #F5C4B3;
  --geojson-color-emotion-very-negative: #F0997B;
}

/* Light 模式 */
[data-theme="light"] {
  --geojson-color-surface-panel: #ffffff;
  --geojson-color-text-primary: #404040;
  --geojson-color-emotion-very-positive: #0F6E56;
  --geojson-color-emotion-positive: #5DCAA5;
  --geojson-color-emotion-neutral: #C0C0C0;
  --geojson-color-emotion-negative: #F0997B;
  --geojson-color-emotion-very-negative: #D85A30;
}
```

### 3.2 切换入口

在 EMC 面板顶栏（`chat-head`）右侧放置模式切换按钮：

```
┌─────────────────────────────┐
│ EmotionMap Copilot    [🌙/☀] │  ← 点击切换 Dark/Light
└─────────────────────────────┘
```

### 3.3 切换时的过渡

```css
#emc-panel {
  transition: background-color 0.3s ease, color 0.3s ease;
}
#emc-panel * {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
```

### 3.4 持久化

用户选择存入 `localStorage`，下次打开自动恢复：

```javascript
// 读取
const theme = localStorage.getItem('emc-theme') || 'dark';
document.documentElement.setAttribute('data-theme', theme);

// 切换
function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('emc-theme', next);
}
```

---

## 四、情境式渐进披露交互逻辑

### 4.1 核心理念

> "此时此刻需要什么 = 出现对应提示"

不一股脑摆出所有功能按钮，而是由 EMC 按当前任务进度，在"恰好需要的那一刻"奉上"恰好那一个"动作。其余一律隐身。

### 4.2 六步引导状态机

```
S0 开场 → S1 选范围 → S2 载图层 → S3 跑分析 → S4 读结论 → S5 收尾
                                                              ↓
                                                    导出 / 深挖 / 换范围
```

### 4.3 每步的出现/隐身规则

| 状态 | 触发条件 | 出现什么 | 隐身什么 | 同屏主动作 |
|------|----------|----------|----------|-----------|
| S0 开场 | 页面加载完成 | EMC 问候 + 两个入口按钮 | Range/Layers/Toolbox/Import/Export 全部 | 1 |
| S1 选范围 | 用户点击入口 | 范围选择器（下拉或绘制工具） | 开场按钮消失 | 1 |
| S2 载图层 | 范围已确定 | EMC 图层推荐卡（仅列有数据覆盖的） | 范围选择器折叠为绿色摘要条 | 1 |
| S3 跑分析 | 图层已载入 | EMC 对话区 + 输入框激活 | 图层选择卡折叠为绿色摘要条 | 1 |
| S4 读结论 | 分析完成 | 诊断卡片 + 内联可视化 + 建议动作 | 思考链折叠（可展开回看） | 1 |
| S5 收尾 | 用户点建议动作 | 导出按钮（此时才出现） | 诊断卡片折叠为摘要 | 1 |

### 4.4 进度指示器

左栏顶部常驻 5 步进度条（被动信息，不受"同屏 1 个主动作"限制）：

```
●───○───○───○───○   步骤 1/5 · 选择起点
```

- 当前步骤：蓝色圆点
- 已完成：绿色圆点 + 绿色连线
- 未到达：灰色圆点 + 灰色连线

### 4.5 绿色摘要条（已完成步骤折叠）

每当一步完成，该步骤的控件折叠为一条绿色摘要条：

```
┌─────────────────────────────┐
│ ● 已完成：框选西陵区      修改 │  ← 绿色底 + 可点击"修改"回退
└─────────────────────────────┘
```

### 4.6 状态转移

```
S0 --点击"看全局"--> S1a（下拉选择）
S0 --点击"聚焦片区"--> S1b（地图绘制）
S0 --直接输入问题--> S3（跳过范围，用默认全市）
S1 --范围确定--> S2
S2 --图层载入--> S3
S3 --EXIT_RESULT--> S4
S3 --EXIT_GAP--> S2（提示补数据）
S3 --EXIT_CONCEPT--> S4（概念解答，无 GIS 操作）
S4 --点建议动作--> S5a（深挖）
S4 --说"导出"--> S5b（导出）
S4 --说"换范围"--> S5c --> S0/S1
```

### 4.7 与现有 harness.js 的衔接

1. **DIAGNOSE 阶段**不变——仍理解用户问题、路由工具选型
2. **新增**：DIAGNOSE 输出追加 `curState` 字段，标记当前引导阶段
3. **tools.js `buildContext()`** 增加：当前状态 + 已完成步骤摘要，注入 LLM context
4. **panel.js UI 渲染**：根据 `curState` 决定哪些控件可见

---

## 五、设计 Token 制作

### 5.1 Token 管线

```
design/tokens.json  →  python design/generate_css.py  →  frontend/css/tokens.css
     (single source)         (编译器)                      (CSS 变量)
                            ↓
                      design/tokens.py
                      (Python 常量)
```

**铁律**：`tokens.css` 和 `tokens.py` 是自动生成物，**禁止手动编辑**。改动只改 `tokens.json`，然后重跑 `generate_css.py`。

### 5.2 tokens.json 结构

```json
{
  "theme": {
    "dark": { "color": { "emotion": {...}, "brand": {...}, ... }, "component": {...} },
    "light": { "color": { "emotion": {...}, "brand": {...}, ... }, "component": {...} }
  },
  "typography": { "fontFamily": {...}, "fontSize": {...}, ... },
  "spacing": { "1": "4px", "2": "8px", ... },
  "radius": { "sm": "4px", "md": "8px", ... },
  "shadow": { "sm": "...", "md": "...", "lg": "..." },
  "geojson": {
    "color": {
      "brand": {...},
      "emotion": {          ← 前端唯一 emotion 色源
        "veryPositive": "#0F6E56",
        "positive": "#5DCAA5",
        "neutral": "#C0C0C0",
        "negative": "#F0997B",
        "veryNegative": "#D85A30"
      },
      ...
    },
    ...
  }
}
```

### 5.3 emotion 色值（Light 模式 · geojson 段）

| Token | 值 | 语义 |
|-------|-----|------|
| `geojson.color.emotion.veryPositive` | `#0F6E56` | 深青绿 — 极正 |
| `geojson.color.emotion.positive` | `#5DCAA5` | 青绿 — 正 |
| `geojson.color.emotion.neutral` | `#C0C0C0` | 浅灰 — 中性 |
| `geojson.color.emotion.negative` | `#F0997B` | 浅珊瑚 — 负 |
| `geojson.color.emotion.veryNegative` | `#D85A30` | 深珊瑚橙 — 极负 |

### 5.4 emotion 色值（Dark 模式 · theme.dark 段）

| Token | 值 | 语义 |
|-------|-----|------|
| `theme.dark.color.emotion.veryPositive` | `#5DCAA5` | 亮青绿（深底可读） |
| `theme.dark.color.emotion.positive` | `#9FE1CB` | 浅青绿 |
| `theme.dark.color.emotion.neutral` | `#E6E6E6` | 亮灰（深底可读） |
| `theme.dark.color.emotion.negative` | `#F5C4B3` | 浅珊瑚 |
| `theme.dark.color.emotion.veryNegative` | `#F0997B` | 中珊瑚（深底可读） |

### 5.5 theme.light 段 emotion 色值

| Token | 值 | 语义 |
|-------|-----|------|
| `theme.light.color.emotion.veryPositive` | `#0F6E56` | 深青绿 |
| `theme.light.color.emotion.positive` | `#5DCAA5` | 青绿 |
| `theme.light.color.emotion.neutral` | `#888888` | 中灰 |
| `theme.light.color.emotion.negative` | `#F0997B` | 浅珊瑚 |
| `theme.light.color.emotion.veryNegative` | `#D85A30` | 深珊瑚橙 |

### 5.6 chart.polarity 同步

`theme.dark.color.chart` 和 `theme.light.color.chart` 中的 polarity 五色必须与 emotion 保持一致：

```json
// theme.light.color.chart
{
  "polarityVeryNegative": "#D85A30",
  "polarityNegative": "#F0997B",
  "polarityNeutral": "#C0C0C0",
  "polarityPositive": "#5DCAA5",
  "polarityVeryPositive": "#0F6E56"
}
```

### 5.7 gradient.hotcold 同步

```json
// theme.light.color.gradient
{
  "hotcold0": "#0F6E56",
  "hotcold1": "#5DCAA5",
  "hotcold2": "#909090",
  "hotcold3": "#F0997B",
  "hotcold4": "#D85A30"
}
```

### 5.8 重新生成

修改 `tokens.json` 后，必须重跑生成器：

```bash
python design/generate_css.py
```

验证：

```bash
grep "emotion" frontend/css/tokens.css
# 应输出 5 个 --geojson-color-emotion-* 变量，值与 tokens.json geojson 段一致
```

---

## 六、前端色源同步

### 6.1 `frontend/js/state.js`

```javascript
// emotionColors() — 从 CSS 变量读取，fallback 值与 token 一致
export function emotionColors() {
  return {
    'Very Positive': token('--geojson-color-emotion-very-positive') || '#0F6E56',
    'Positive':      token('--geojson-color-emotion-positive')      || '#5DCAA5',
    'Neutral':       token('--geojson-color-emotion-neutral')       || '#C0C0C0',
    'Negative':      token('--geojson-color-emotion-negative')      || '#F0997B',
    'Very Negative': token('--geojson-color-emotion-very-negative') || '#D85A30',
  };
}

// L2 常量 — 与 token 一致
export const L2_POSITIVE = { 'Very Positive': '#0F6E56', 'Positive': '#5DCAA5' };
export const L2_NEGATIVE = { 'Very Negative': '#D85A30', 'Negative': '#F0997B' };
export const L2_NEUTRAL_COLOR = '#C0C0C0';
```

### 6.2 `core/config.py`

```python
# COLOR_MAP — 与 tokens.json geojson 段一致
COLOR_MAP = {
    'Very Positive': '#0F6E56',   # 深青绿 — 极正
    'Positive':      '#5DCAA5',   # 青绿 — 正
    'Neutral':       '#C0C0C0',   # 浅灰 — 中性
    'Negative':      '#F0997B',   # 浅珊瑚 — 负
    'Very Negative': '#D85A30',   # 深珊瑚橙 — 极负
}

# FOLIUM_COLOR_MAP — 与 COLOR_MAP 一致
FOLIUM_COLOR_MAP = {
    'Very Positive': '#0F6E56',
    'Positive':      '#5DCAA5',
    'Neutral':       '#C0C0C0',
    'Negative':      '#F0997B',
    'Very Negative': '#D85A30',
}

# POLARITY_RGBA — 与 COLOR_MAP 一致（RGBA 格式）
POLARITY_RGBA = {
    'Very Positive': [15, 110, 86, 230],    # #0F6E56 深青绿
    'Positive':      [93, 202, 165, 230],   # #5DCAA5 青绿
    'Neutral':       [192, 192, 192, 230],  # #C0C0C0 浅灰
    'Negative':      [240, 153, 123, 230],  # #F0997B 浅珊瑚
    'Very Negative': [216, 90, 48, 230],    # #D85A30 深珊瑚橙
}
```

---

## 七、EMC 面板 CSS 规范

### 7.1 Dark 模式（默认）· `#emc-panel` scope

```css
#emc-panel {
  --geojson-color-surface-panel: #1f1f1f;
  --geojson-color-surface-panel-alt: #262626;
  --geojson-color-text-primary: #ECECEC;
  --geojson-color-text-secondary: #A0A0A0;
  --geojson-color-text-tertiary: #707070;
  --geojson-color-border-default: #3a3a3a;
  --geojson-color-gray-100: #2a2a2a;
  --geojson-color-gray-200: #3a3a3a;
  --geojson-color-brand-primary: #F0997B;      /* 珊瑚橙（动作态） */
  --geojson-color-danger: #E06C5C;
  --emc-accent: #F0997B;
  --emc-accent-soft: rgba(240, 153, 123, 0.12);
  --emc-divider: rgba(255, 255, 255, 0.08);
  --emc-user-bubble: #303030;
  color-scheme: dark;
}
```

### 7.2 Light 模式 · `#emc-panel` scope

```css
[data-theme="light"] #emc-panel {
  --geojson-color-surface-panel: #ffffff;
  --geojson-color-surface-panel-alt: #f8f8f8;
  --geojson-color-text-primary: #404040;
  --geojson-color-text-secondary: #737373;
  --geojson-color-text-tertiary: #a3a3a3;
  --geojson-color-border-default: #e5e5e5;
  --geojson-color-gray-100: #f5f5f5;
  --geojson-color-gray-200: #e5e5e5;
  --geojson-color-brand-primary: #D85A30;      /* 深珊瑚橙（动作态） */
  --geojson-color-danger: #dc2626;
  --emc-accent: #D85A30;
  --emc-accent-soft: rgba(216, 90, 48, 0.12);
  --emc-divider: rgba(0, 0, 0, 0.08);
  --emc-user-bubble: #f0f4f8;
  color-scheme: light;
}
```

### 7.3 三级权重 CSS

```css
/* 一级：结论卡 */
.aiq-conclusion {
  background: var(--geojson-color-surface-panel);
  border-radius: var(--geojson-radius-lg, 8px);
  box-shadow: var(--geojson-shadow-lg);
  overflow: hidden;
  margin: 8px 0 4px;
}
.aiq-conclusion-band { height: 8px; }
.aiq-conclusion-band.very-positive { background: var(--geojson-color-emotion-very-positive); }
.aiq-conclusion-band.positive { background: var(--geojson-color-emotion-positive); }
.aiq-conclusion-band.neutral { background: var(--geojson-color-emotion-neutral); }
.aiq-conclusion-band.negative { background: var(--geojson-color-emotion-negative); }
.aiq-conclusion-band.very-negative { background: var(--geojson-color-emotion-very-negative); }
.aiq-conclusion-body { padding: 12px 14px; }

/* 二级：过程卡 */
.aiq-reason {
  border-left: none;
  background: var(--geojson-color-gray-100);
  border-radius: var(--geojson-radius-md, 6px);
}

/* 三级：审查胶囊 */
.aiq-review-collapsed {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 10px; font-size: var(--geojson-typography-size-2xs);
  border-radius: 999px; cursor: pointer;
}
.aiq-review-collapsed.pass { color: #16A085; background: rgba(22,160,133,0.08); border: 1px solid rgba(22,160,133,0.2); }
.aiq-review-collapsed.fail { color: var(--geojson-color-danger); background: rgba(220,38,38,0.08); border: 1px solid rgba(220,38,38,0.2); }
.aiq-review-collapsed.warn { color: #d9a400; background: rgba(217,164,0,0.08); border: 1px solid rgba(217,164,0,0.2); }
.aiq-review:hover .aiq-review-collapsed { display: none; }
.aiq-review:hover .aiq-review-items { display: flex; }
.aiq-review-items { display: none; }

/* 答案内联微可视化 */
.emotion-swatch {
  display: inline-block; width: 8px; height: 8px;
  border-radius: 2px; vertical-align: middle; margin: 0 2px;
}
.emotion-swatch.very-positive { background: var(--geojson-color-emotion-very-positive); }
.emotion-swatch.positive { background: var(--geojson-color-emotion-positive); }
.emotion-swatch.neutral { background: var(--geojson-color-emotion-neutral); }
.emotion-swatch.negative { background: var(--geojson-color-emotion-negative); }
.emotion-swatch.very-negative { background: var(--geojson-color-emotion-very-negative); }
```

---

## 八、配色铁律（Dark/Light 通用）

| # | 规则 | 说明 |
|---|------|------|
| 1 | 深底 + 浅字 | Dark 模式：背景深、文字浅、emotion 色取浅端 |
| 2 | 浅底 + 深字 | Light 模式：背景浅、文字深、emotion 色取深端 |
| 3 | 珊瑚橙 = 动作态 | 仅用于发送按钮、聚焦边框、强调文字，不做大面积铺色 |
| 4 | 情绪色 = 数据态 | 仅用于情绪散点、结论卡色带、图例、swatch，不做 UI 装饰 |
| 5 | 品牌蓝 = 交互态 | `#4285F4` 仅用于链接、选中态、focus ring，退为纯交互色 |
| 6 | 一条带贯穿 | 情绪五级色带是全站唯一主角色，贯穿地图/结论卡/图例/时间轴/矩阵 |

---

## 九、文件清单与改动范围

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `design/tokens.json` | 修改 | emotion 五色 + chart.polarity + gradient.hotcold（共 6 段 × 2 主题） |
| `design/generate_css.py` | 不改 | 生成器逻辑不变，重跑即可 |
| `frontend/css/tokens.css` | 自动生成 | 重跑 `generate_css.py` 后自动更新 |
| `frontend/css/ai_qa.css` | 修改 | Dark/Light 双模式 scope + 三级权重 + emotion-swatch |
| `frontend/js/state.js` | 修改 | emotionColors() fallback + L2_POSITIVE/L2_NEGATIVE |
| `core/config.py` | 修改 | COLOR_MAP + FOLIUM_COLOR_MAP + POLARITY_RGBA |
| `frontend/js/ai_qa/panel.js` | 修改 | 主题切换按钮 + localStorage 持久化 |
| `frontend/js/ai_qa/harness.js` | 修改 | curState 注入 + 渐进披露状态机 |

---

## 十、验证清单

修改完成后，逐项验证：

- [ ] `python design/generate_css.py` 无报错
- [ ] `grep "emotion" frontend/css/tokens.css` 输出 5 个新色值
- [ ] `python frontend/serve.py 8080` 启动无报错
- [ ] 地图渲染：情绪散点颜色为新色带
- [ ] EMC 面板：Dark 模式默认，Light 模式可切换
- [ ] EMC 结论卡：顶部色带颜色与答案极性一致
- [ ] EMC 审查：默认收胶囊，hover 展开
- [ ] 答案内联：区域名后有 emotion-swatch 色方块
- [ ] 进度条：5 步指示器正确反映当前步骤
- [ ] 绿色摘要条：已完成步骤正确折叠
- [ ] 导出按钮：仅在 S5（收尾）时出现
