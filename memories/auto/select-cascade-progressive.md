---
name: select-cascade-progressive
description: 数据选择必须联动递进 — 选层级后下游只显示该层级数据，不混层
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 22e972fb-64fe-47c3-bbb5-efd0c7d69068
---

数据选择控件之间是**联动+递进**关系：选了上游（如数据层级 L1/L2）后，下游控件（如点层下拉）必须**只显示该层级的数据**，不能混入其他层级。

**Why:** 用户多次强调这是基本逻辑——选 L1 就不该出现 L2 极性相关内容；选择应层层过滤，避免用户选到无效组合。我在 grid-tool 第一版让点层下拉列了所有层级点层被纠正。

**How to apply:** 任何"上游选择 → 下游选项"的控件对（level→点层、类型→子类、面域→名称列），下游 populate 时按上游值过滤；上游 change 时重新 populate 下游 + 重置选中。参考 grid-tool.js `populateSources(srcs, level)` + `#grid-level` change → 重填点层。

**实现陷阱**：隐藏 `.hm-section` 必须加 `.hm-section[hidden]{display:none}` CSS——`.hm-section{display:flex}` 会覆盖 `[hidden]` 属性，导致设了 hidden 的 section 仍可见可点（grid 选 L1 时极性胶囊没灰掉就是这个根因）。关联 [[ramp-discrete-segments]]（同属 UI 一致性规则）。
