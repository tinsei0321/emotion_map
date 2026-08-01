---
id: B005
title: '多步操作链 — 只做一半停下（部分新）'
type: BUG
severity: CRIT
priority: P0
status: resolved
module: 工具调用
source: 用户实测
cb: CB-09
rootcause: docs/catch-ball/rootcause/2026-07-28-multi-extract-reasoning-spiral.md
case_ref: TC-24
repro_count: 1
last_repro: 2026-07-29
---

# B005 · 多步操作链 — 只做一半停下（部分新）

## 标准化用例

**问句**：「将西陵区+伍家岗区范围内商业用地筛选出来。」

**数据前提**：
- 行政区面层（含西陵区、伍家岗区）
- 西陵伍家岗核心主城面层（已有）
- 用地_商业面层

**预期行为**：
① Step 1：获取/确认西陵区+伍家岗区合并范围（merge 或 extract_feature 双区）
② Step 2：用合并范围 clip 商业用地面层
③ Step 3：生成「西陵伍家岗商业用地」面图层（含 2 个面）
④ 所有步骤执行完毕后再出结论

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:---:|------|------|------|
| 1 | 07-29 | Step 1（抽取西陵伍家岗范围）成功 → Step 2（clip 商业用地）未执行 → finalStep 仍出完整结论 | 多步链执行断裂 + finalStep 假结论（B002 同根因） |

## 修复记录

| 日期 | 操作 | commit |
|------|------|------|
| 2026-08-01 | CB-10 P0-1/分歧1：_deterministicRecover 模式 D（单用地+双区→extract where in 双区 + overlay）+ _autoExpandOverlays 扩单用地 + _LANDUSE 去「用地」泛词（防「商业用地」误匹配 3 overlay）→ 浏览器验证「西陵区+伍家岗区商业用地」一次双区+overlay 9.7s | 898998b |
| 2026-07-29 | P0-4: harness.js runChainPath + while-loop exit 注入多步链执行结果摘要（全完成+产出数） | 31e2a00 |
|------|------|------|
| — | 待修复 | — |

---

## 诊断摘要

**根因有两层**：

**层 1 — 多步链执行断裂**：当前 FC 架构为单工具模式（每次返回 1 个 tool_call）。多步操作依赖 `plans[]` 机制（LLM 规划多步，系统顺序执行）。但在本例中，Step 1（extract_feature 抽取西陵伍家岗范围）执行后，Step 2（clip 商业用地）未被触发。可能原因：
- plans[] 中 rank=2 的步骤未正确传递到下一轮执行
- 或者 Step 1 返回后系统认为"已完成"而未继续

**层 2 — finalStep 假结论**（与 B002/B004 同根因）：即使 Step 2 未执行，finalStep 仍然基于 plans[] 写出了完整的结论文本，声称"已裁剪，生成 2 个面"。

**治本方向**：
- CB-09 D1：FC 架构是否应支持多工具返回（tool_calls[] 数组），或强化 plans[] 的顺序执行保证
- CB-09 P1-1：finalStep context 注入执行结果摘要（已执行/未执行/失败）
- 新增：harness 增加「all planned steps executed?」校验——plans[] 中所有步骤都执行完毕才进入 finalStep
