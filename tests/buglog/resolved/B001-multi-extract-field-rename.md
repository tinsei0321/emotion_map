---
id: B001
title: 多要素裁剪失败螺旋（extract_feature 字段重命名断裂 + 单工具限制 + FC 推理死循环）
type: BUG
severity: HIGH
status: resolved
module: 数据识别
source: 用户实测
cb: CB-09
rootcause: docs/catch-ball/rootcause/2026-07-28-multi-extract-reasoning-spiral.md
case_ref: TC-06
repro_count: 4
last_repro: 2026-07-28
---

# B001 · 多要素裁剪失败螺旋

## 标准化用例

**问句**：「帮我从中心城区范围中裁剪出西陵 + 伍家岗的范围」

**数据前提**：面层（中心城区行政区划·字段 `MC`·含西陵区/伍家岗区/…）

**预期行为**：
① `extract_feature` 被选中且 `where` 正确引用字段名（`MC` 或重命名后的 `name`）
② 西陵区 + 伍家岗区面图层已生成
③ 结论诚实描述（不编造未生成的图层）

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:-:|------|------|------|
| 1 | 07-28 | select_candidates 数据盲 → 误路由 clip | 0-LLM context=None |
| 2 | 07-28 | extract_feature 报 `MC` 字段不存在 | resolve_boundary 将 `MC`→`name` 重命名后 filter 找不到 |
| 3 | 07-28 | 多步链失败 → finalStep 编造结论 | finalStep 无执行结果感知（详见 rootcause/2026-07-28-hallucination-finalstep.md） |
| 4 | 07-28 深夜 | FC 推理螺旋 → request_upload | FC 单工具限制 + 契约 `when`「单要素」误导 + 缺 `in` 操作符指引 |

## 修复记录

| 日期 | 操作 | commit |
|------|------|--------|
| 07-28 | M1 `_norm_where` 拆逗号（支持 `in` 多值列表） | 1320e7c |
| 07-28 | M2 FC sys prompt 多要素指引 | 1320e7c |
| 07-28 | M3 契约 `extract_feature` 去「单要素」误导（`when`=FC description·上游根因） | f68f61c |
