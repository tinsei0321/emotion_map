# UI 重构 Plan v2 — geojson.io 风格迁移

> 2026-06-15 | 参考 geojson.io + 当前 localhost 截图

---

## 一、geojson.io 设计特征提取

从 vision-inbox 识图结果中提取的关键设计模式：

| 特征 | geojson.io 做法 | 情绪地图借鉴 |
|------|----------------|-------------|
| **工具栏** | 顶部水平，分组：Logo + 绘图工具(radio) + 操作按钮(Import/Export/Layers/About) | 顶部水平：标题 + 导入/导出 + 底图/图层/范围(下拉) + 设置 |
| **面板** | 右侧可拖拽 JSON 编辑器（JSON/Table/List三Tab） | 左侧面板：数据概要 / 工具 / 图层(三段可折叠) |
| **地图控件** | 右下角 Zoom + Geolocate + 比例尺 | 保留右下角图例，zoom 已有 |
| **弹窗** | 几乎不用弹窗，用面板内嵌 | 仅 TB 表格和设置保留弹窗 |
| **色彩** | 白色背景 + 浅灰边框，工具按钮有 active 态 | 暗底半透明（地图叠加），active 态高亮 |

## 二、目标布局（精确尺寸）

```
┌──────────────────────────────────────────────────────────────────┐
│ ←8→ [情绪地图] [导入▾] [导出▾]  │  [底图▾] [图层▾] [范围▾] [⚙]│  h=36 top=8
├──────────────┬───────────────────────────────────────────────────┤
│ ←8           │                                                   │
│ ┌ 240px ───┐ │                                                   │
│ │ ▲ 数据概要│ │                                                   │
│ │  范围  xxx│ │                  MAP (pydeck)                     │
│ │  DATA  L2│ │                   100%剩余空间                      │
│ │  文件  xxx│ │                                                   │
│ ├───────────┤ │                                                   │
│ │ ▼ 分析工具│ │                                                   │
│ │   情绪分析│ │                                                   │
│ │   单元分析│ │                                                   │
│ │   缓冲分析│ │                                                   │
│ ├───────────┤ │                                                   │
│ │ ▼ 图层   │ │                                                   │
│ │ ☑ L1 xxx │ │                                                   │
│ │ ☑ L2 xxx │ │                                                   │
│ └───────────┘ │               [图例 ▾]                  [热力 H] │
├──────────────┴───────────────────────────────────────────────────┤
│ ←8 渲染: S·标准  │  [数据表格]  [数据治理]  [数据概览]           │ h=28 bottom=4
└──────────────────────────────────────────────────────────────────┘
```

**关键尺寸**：
- 顶栏：`height: 36px; top: 8px; left: 8px; right: 8px; border-radius: 8px`
- 左面板：`width: 240px; top: 52px; left: 8px; bottom: 40px`（顶部栏下+底部栏上）
- 底栏：`height: 28px; bottom: 4px; left: 8px; right: 8px`

## 三、组件规范

### 3.1 顶部工具栏

**HTML 结构**：
```
┌──────────────────────────────────────────────────────┐
│ [情绪地图 v1.0] [导入▾] [导出▾] │ [底图▾] [图层▾] [范围▾] [⚙] │
└──────────────────────────────────────────────────────┘
  左侧组（品牌+操作）          分隔      右侧组（配置）
```

**CSS 规格**：
| 属性 | 值 |
|------|-----|
| position | fixed |
| top/left/right | 8px |
| height | 36px |
| background | rgba(20,24,32,0.55) |
| backdrop-filter | blur(12px) |
| border-radius | 8px |
| border | 1px solid rgba(255,255,255,0.06) |
| display | flex; align-items: center; justify-content: space-between |
| padding | 0 12px |
| z-index | 9500 |

**按钮规格**（toolbar button）：
| 属性 | 值 |
|------|-----|
| height | 28px |
| padding | 0 10px |
| font-size | 0.75rem |
| color | #B0B8C0 |
| background | transparent |
| border-radius | 4px |
| hover | background: rgba(255,255,255,0.08) |
| active | background: rgba(255,255,255,0.12); color: #fff |
| gap | 4px between buttons |

**下拉面板**（点击按钮弹出）：
| 属性 | 值 |
|------|-----|
| position | absolute; top: 40px（按钮下方） |
| width | 200px |
| background | rgba(20,24,32,0.85) |
| border-radius | 6px |
| border | 1px solid rgba(255,255,255,0.08) |
| backdrop-filter | blur(16px) |
| padding | 6px |
| z-index | 9600 |

**Streamlit 实现**：工具栏用 `st.markdown` 渲染纯 HTML/CSS。按钮用 `<button>` + `onclick` 设置 `session_state` 标记。下拉面板用 `st.popover` 或展开/折叠 div。

### 3.2 左侧面板

**HTML 结构**：三段折叠面板，每段有标题栏（点击折叠/展开）。

**CSS 规格**：
| 属性 | 值 |
|------|-----|
| position | fixed |
| top | 52px (8+36+8) |
| left | 8px |
| width | 240px |
| max-height | calc(100vh - 100px) |
| background | rgba(20,24,32,0.55) |
| backdrop-filter | blur(12px) |
| border-radius | 8px |
| border | 1px solid rgba(255,255,255,0.06) |
| overflow-y | auto |
| z-index | 9400 |

**段标题**（section header）：
| 属性 | 值 |
|------|-----|
| padding | 6px 10px |
| font-size | 0.7rem; font-weight: 600 |
| color | #8B929A |
| cursor | pointer |
| border-bottom | 1px solid rgba(255,255,255,0.05) |
| 折叠箭头 | ▲ 展开 / ▼ 折叠（`font-size: 0.55rem`） |

**段内容**（section body）：
| 属性 | 值 |
|------|-----|
| padding | 6px 10px |
| font-size | 0.68rem |
| color | #B0B8C0 |
| line-height | 1.5 |

**段结构**：
1. **数据概要**（默认展开）— 当前 `render_data_panel` 内容
2. **分析工具**（默认折叠）— 工具按钮列表
3. **图层**（默认展开）— 原 LY toggle 列表

**Streamlit 实现**：用 `st.markdown` 渲染面板 HTML，折叠状态存 `session_state`。图层 toggle 用 `st.checkbox` 嵌入面板中（或用 `<input type=checkbox>` + JS 同步到 session_state）。

### 3.3 底部状态栏

**CSS 规格**：
| 属性 | 值 |
|------|-----|
| position | fixed |
| bottom | 4px; left: 8px; right: 8px |
| height | 28px |
| background | rgba(20,24,32,0.50) |
| border-radius | 6px |
| font-size | 0.68rem |
| color | #6B7280 |
| display | flex; align-items: center; justify-content: space-between |
| padding | 0 10px |
| z-index | 9500 |

**内容**（从左到右）：
`[渲染: S·标准] ─────────────────── [热力图] [数据表格] [数据概览]`

### 3.4 地图控件（右下）

| 元素 | 说明 |
|------|------|
| 图例 | 紧凑版：5 个色点 + 标签，可折叠 |
| 热力图 toggle | `[H]` 按钮 |
| 后续可加 | Zoom 控件（如果 pydeck 支持） |

### 3.5 保留弹窗

| 弹窗 | 宽度 | 备注 |
|------|------|------|
| [TB] 数据表格 | large | 表格需大空间，不可替代 |
| 设置 | small | 低频操作，弹窗即可 |

## 四、数据流架构

```
session_state 单源真相:
  layers[]       ← register_layer() (D/GV/A 调用)
  selected_ranges ← R 确认范围
  file_path      ← D 加载的数据文件
  _map_style     ← M 底图切换
  _heatmap_mode  ← H 热力图

读取方:
  顶部工具栏  ← _map_style, file_path
  左侧面板    ← layers[], selected_ranges, file_path
  底部栏      ← _render_tier
  地图        ← layers[], file_path, _map_style, selected_ranges
  图例        ← _heatmap_mode

写入方:
  [导入▾]    → file_path, layers[] (via register_layer)
  [底图▾]    → _map_style
  [图层▾]    → layers[].visible
  [范围▾]    → selected_ranges
  [⚙]       → (debug toggles)
```

**关键原则**：所有 UI 组件读写同一份 `session_state`，不再各自维护独立状态。

## 五、实施 Phase

### Phase 1a：顶部工具栏（核心迁移）

**改动文件**：`ui_components.py`（新增 `render_top_toolbar`）、`app_main.py`（替换 HUD 按钮调用）

**从旧到新映射**：
| 旧按钮 | 位置 | 新位置 | 实现方式 |
|--------|------|--------|---------|
| [R] | 右侧 | [范围▾] 工具栏下拉 | st.popover |
| [D] | 右侧 | [导入▾] 工具栏下拉 | st.popover → 选文件 |
| [A] | 右侧 | 左面板"分析工具"段 | 面板内按钮 |
| [H] | 右侧 | 底部栏右侧 | toolbar button |
| [M] | 底部左下 | [底图▾] 工具栏下拉 | st.popover |
| [OV] | 底部左下 | 底部栏 [数据概览] | toolbar button → st.dialog |
| [TB] | 底部左下 | 底部栏 [数据表格] | toolbar button → st.dialog(large) |
| [LY] | 底部左下 | 左面板"图层"段 | 面板内 checkbox |
| [*] | 底部左下 | 工具栏 [⚙] | toolbar button → st.dialog(small) |

**验收标准**：
- 顶部工具栏渲染正确，所有按钮可点击
- 下拉面板展开/收起正常
- 地图不被工具栏遮挡
- 旧的右侧 HUD 和底部按钮全部移除

### Phase 1b：左侧面板（状态统一）

**改动文件**：`ui_components.py`（新增 `render_side_panel`）、`app_main.py`（替换 LY 弹窗和数据面板）

**三段的实现**：
1. 数据概要段 → 复用 `render_data_panel` 逻辑，嵌入面板
2. 分析工具段 → 新增工具列表（Phase 1b 仅放情绪分析入口）
3. 图层段 → 原 LY toggle 移入，实时同步

**折叠逻辑**：每个段的展开/折叠状态存 `session_state._panel_{section}_open`

**验收标准**：
- 三段正确渲染，折叠/展开正常
- 图层 toggle 改变 → 地图立即更新 → 数据概要段同步
- 面板内无弹窗，所有操作就地完成

### Phase 1c：底部栏 + 清理

**改动文件**：`ui_components.py`（新增 `render_bottom_bar`）、`app_main.py`

- 底部栏渲染模式 + 快捷按钮
- 移除所有旧 HUD CSS（`hud_button_style_css` 可大幅缩减）
- 移除旧数据面板（左上角独立小窗）
- 移除旧的居中标题栏

### Phase 2：弹窗瘦身

- [GV] 数据治理 → 左面板"分析工具"段内操作
- [OV] 数据概览 → 左面板"数据概要"段展开详情
- [ANA] 情绪分析 → 左面板"分析工具"段内主流程

### Phase 3：未来分析工具扩展

- 面板内新增工具按钮：单元分析、缓冲分析、热聚合
- 每个工具点击后面板内容切换为对应配置 UI
- 分析结果自动注册到 `layers[]`，图层 toggle 自动出现

## 六、待确认

1. 顶栏透明度 `0.55` 是否合适？（可调范围 0.40-0.70）
2. 左面板宽度 240px OK？还是更窄（200px）让地图更多？
3. Phase 1a 开始时，先做顶部工具栏还是先做左面板？建议先工具栏（改动最小、见效最快）
