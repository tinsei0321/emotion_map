---
name: button-design-language
description: 工具栏按钮间距设计规则：改按钮宽度必须同步调整相邻按钮位置
metadata:
  type: feedback
---

# 按钮间距设计语言

## 规则

工具栏按钮定位必须遵循统一公式：

```
从左到右: left = 12 + Σ(prev_button_width + G)   // G = 8px gap
从右到左: right = 12 + Σ(prev_button_width + G)
```

## 变量

- `S = 36px` — 标准方形按钮宽/高
- `G = 8px` — 按钮间距
- `R = 4px` — 圆角
- 长条按钮宽度 = `2*S = 72px`（如 Import/Export），高度仍为 `S`

## 铁律

**改按钮宽度 → 必须同步更新该按钮之后所有按钮的位置**。

例如：Import 从 36px 改为 72px，Export 位置不受影响（Import 在 Export 左边），但如果有第三个按钮在 Import 右边，它的 right 值需要 +36。

## 历史犯过的错误

- Import/Export 宽度从 36→72 时，位置公式正确（`right: 12+S+G` 基于 Export 的 36px 宽度计算），但当时没有明确文档记录规则。

**Why:** 用户发现改按钮宽度后不检查间距，这是基本的设计逻辑遗漏。
**How to apply:** 每次修改按钮尺寸，检查 CSS 中该按钮及所有相邻按钮的 left/right 定位值。
