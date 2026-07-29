---
id: B003
title: 'LLM 推理螺旋 — 简单查询耗时异常（复现）'
type: PERF
severity: HIGH
status: open
module: FC诊断
source: 用户实测
cb: CB-09
rootcause: docs/catch-ball/rootcause/2026-07-28-multi-extract-reasoning-spiral.md
case_ref: TC-22
repro_count: 2
last_repro: 2026-07-29
---

# B003 · LLM 推理螺旋 — 简单查询耗时异常（复现）

## 标准化用例

**问句**：「我上传了哪些数据？」

**数据前提**：已上传 11 份地理数据文件（情绪点 3 份 + 边界 4 份 + 用地 3 份 + 水系 1 份）

**预期行为**：
① _quickIntent 识别为 general 类问句（非地理分析，是数据清单查询）
② 直接短路回答（不走 FC / diagnose），从接地上下文中提取已加载数据清单
③ 回答按类型分组（情绪评价点 / 行政边界 / 用地类型 / 水系），附数量统计
④ 响应时间 < 5s（简单数据查询，无需推理）

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:---:|------|------|------|
| 1 | 07-28 | C2：LLM 7 轮推理螺旋后答错（声称"没有上传任何数据"） | buildContext 缺数据来源标注 |
| 2 | 07-29 | 本次：结果正确但耗时很久（7 轮推理螺旋） | 同上 + intent 路由未走 general 短路 |

## 修复记录

| 日期 | 操作 | commit |
|------|------|------|
| — | 待修复 | — |

---

## 诊断摘要

**根因**：LLM 在 thinking trace 中经历了 7 轮判断→推翻→重新判断的推理螺旋：
1. 接地上下文（`buildContext`）中所有层以相同格式列出，不区分「用户上传」vs「系统预设」
2. LLM 无法直接判断哪些是用户上传的数据 → 开始用推理猜测 → 反复推翻自己的判断
3. `_quickIntent` 未将此问句路由到 general 短路路径，而是走了 FC 诊断链

**为何结果正确但耗时久**：最终 LLM 通过分析数据文件名和上下文推断出了正确答案（11 份数据），但推理过程浪费了大量 token 和时间。

**治本方向**：
- CB-09 P0-1：`buildContext` 加数据来源标注（user-uploaded / system-preset）
- CB-09 P2-1：System prompt 加「不确定时直接列出所见，不要推理」
- 新增：`_quickIntent` 增加「数据清单查询」意图识别（问句含"上传了哪些/有哪些数据/数据列表"→ general 短路）
