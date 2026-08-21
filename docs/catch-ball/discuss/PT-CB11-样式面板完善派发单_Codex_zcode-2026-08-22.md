# PT-CB11 · 样式面板完善派发单（Codex 协同批·函数级规格）

> 主手：zcode。执行：Codex（协同模式·与 Phase 2 并行不冲突——本批纯前端+契约文档·零 Python）。依据：`PT-CB11-数据驱动图层样式面板_设计方案_zcode-2026-08-22.md`（用户已拍板：方案 A+图例双入口）。
> 分支 `EMC_harness_dsh`·commit 前缀 `PT-CB11(C3):`。**本地仓即最新·零 pull 零 push**（显式路径 commit·push 主手统一）。
> 设计铁则：**复用既有组件与 CSS 类（hm-ramp-*·GRID_PALETTE_GROUPS·HEATMAP_RAMPS）——零新设计 token·零新视觉语言**；三处（生成对话框/参数面板/图例）一套视觉。

## ① settings.js · polygon+gridField 分支替换色带编辑器（核心件）

现状（B3-5 止血版·settings.js:100-106）：`p.gridField ? 提示文案 : 拾色器`。**替换为**（gridField 层专属样式组）：

1. **色带选择器**：沿 grid-tool.js:315-360 的 `hm-ramp-item` 按钮结构（渐变条 `linear-gradient(90deg, rampDisplaySegs(...))`·`hm-ramp-group-label` 分组）——按 `paint.semantic` 分组排序：
   - `semantic='count'`：单色系→多色系→发散系；默认选中 `oranges`
   - `semantic='polarity'`：发散系置顶→多色系→单色系；默认选中 `terrain-9`
   - 无 semantic：全组平铺·默认 `grid-warm`
   - 已有 `paint.rampKey`（见②）则默认选中它（「当前所用」如实显示）
2. **反向 toggle**：语义同 grid dialog（翻转 stops 高低端）·同款交互样式；
3. **零值显隐 toggle**：就地翻转 `paint.zeroIsNoData`；
4. 保留既有：面开关/线宽/线型/填充透明度。

**应用路径（纯本地·即时）**：选中色带 k → `grid-tool.js` 的 `normStops(k)`（**须加 export**·grid-tool.js:69 现成）得归一化 stops → 反向则 reverse → `layer.paint.gridStops = stops`（`paint.rampKey = k`·`paint.reverse = r`）→ `setLayerPaint` + `renderLayer(layer)` → `refreshLegend()`（B3-3 已挂 gridStops·图例自动跟随）。

## ② render_client.js · semantic/rampKey 透传

- `_apply(spec)` 的 count 分支（:150 附近）：paint 增 `semantic: 'count'`；isPolarity 分支：`semantic: 'polarity'`；
- `spec.style.ramp_hint` 存在时透传 `paint.rampKey = ramp_hint`（受管词表内·未注册回落不设）。

## ③ sidebar.js · 图例双入口（用户采纳件）

- `refreshLegend()` 的 legend-grid 色带条（:234-246 DOM）：加可点击态（cursor:pointer·title「调整色带」）→ 点击 = 打开该层的 settings 样式面板（复用同一 popover 组件实例·锚点可挂图例条）——**同一选择器·不是另做一套**。

## ④ render-contract.md §七-7 契约升级

「换色必须重投递 spec」→「**色带/反向/零值显隐/透明度/线样式=面板本地可调**（归一化值随层内嵌）；**数据/字段/归一化变更才需重投递**」。

## ⑤ 测试（tests/test_render_channel.py·静态契约断言沿既有模式）

- settings.js 含 `hm-ramp-item` 渲染段 + `normStops` import + semantic 分支（'count'/'polarity' 字符串存在）；
- render_client.js 含 `semantic` 透传两分支 + `rampKey` 透传；
- grid-tool.js 的 `normStops` 带 export；
- render-contract.md §七-7 含「本地可调」新表述。

## DoD

- [ ] 上述五件齐 + `python -m pytest tests/ -q` 全绿（457+7 存量基线·不新增失败）
- [ ] 浏览器实测（起 8080·投一张 count choropleth 内联 spec）：面板换色带/反向/零值显隐均即时生效·图例跟随·点图例条打开同款选择器
- [ ] 执行记录落盘 `PT-CB11-C3执行记录_Codex-2026-08-22.md`（含实测截图·无新坑或已蒸馏标注）
- [ ] 铁则：零 Python 改动·零新追踪 ID·禁 emoji·A9

> zcode 主手 · 2026-08-22 上午 · C3 协同批派发
