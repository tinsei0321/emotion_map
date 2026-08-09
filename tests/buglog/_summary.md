# EMC Bug 修复工程日志

> 自动生成（`py tests/buglog/_gen_index.py`）·勿手改 · 最后更新：2026-08-01 23:22
> 条目 **11** · OPEN **3** · RESOLVED **8** · P0 阻塞 **2** · 修复已提交 **2**
> 飞轮：27 用例 · 最近报告：report-2026-08-01-02-llm (52%·13/25)

---

## 工程概览

| 指标 | 值 |
|------|-----|
| 总条目 | 11 |
| OPEN（未解决） | 3 |
| RESOLVED（已解决） | 8 |
| P0 阻塞 | 2（B002/B004）|
| P1 高优先 | 0（无）|
| P2 中优先 | 1（B008）|
| 修复已提交 | 2 |
| 飞轮用例 | 27 |
| 最近飞轮报告 | report-2026-08-01-02-llm (52%·13/25) |

---
## P0 · 阻塞项（必须立即修复）

### B002 · finalStep 假结论 — "只说不做/只做一半"（复现）

- **严重度**：CRIT | **模块**：finalStep | **复现**：3×
- **修复进度**：P0-4 v3 根治：① _autoExpandOverlays 代码自动扩展多步骤 ② D057 修订允许多 tool_calls ③ FC prompt 简化去旧诊断卡触发 ④ clip 描述加 ❌面层禁止 ⑤ extract_feature/overlay when 修正 (3a97e19)
- **问句**：「剪裁出西陵区范围内的商业+居住+公园广场用地」
- **同根因**：B004
- **关联**：[entry](open/B002-finalstep-fake-conclusion-recurrence.md) · [rootcause](../../docs/catch-ball/rootcause/2026-07-28-hallucination-finalstep.md) · TC-21 · CB-09

### B004 · finalStep 假结论 — 筛选点图层"只说不做"（复现）

- **严重度**：CRIT | **模块**：finalStep | **复现**：2×
- **修复进度**：P0-4: 同 B002——harness.js finalStep context 注入执行结果（成功/失败/产出数） (31e2a00)
- **问句**：「将西陵区范围内的积极情绪点筛选出来单独显示。」
- **同根因**：B002
- **关联**：[entry](open/B004-finalstep-fake-conclusion-point-filter.md) · [rootcause](../../docs/catch-ball/rootcause/2026-07-28-hallucination-finalstep.md) · TC-23 · CB-09

## P1 · 高优先

*暂无*

## P2 · 中优先

### B008 · 网格聚合 2D/3D 视角未解耦（新发现）

- **严重度**：MED | **模块**：UI | **复现**：3×
- **修复进度**：待修复
- **问句**：「对当前区域做 500m 方格网聚合」（任意网格聚合问句）」
- **关联**：[entry](open/B008-grid-aggregation-view-decoupling.md) · TC-27 · CB-09

## 已解决

| ID | 标题 | 模块 | 修复 commit |
|:-:|------|:-:|------|
| B001 | 多要素裁剪失败螺旋（extract_feature 字段重命名断裂 + 单工具限制 + FC 推理死循环） | 数据识别 | f68f61c |
| B003 | LLM 推理螺旋 — 简单查询耗时异常（复现） | FC诊断 | 898998b |
| B005 | 多步操作链 — 只做一半停下（部分新） | 工具调用 | 31e2a00 |
| B006 | 意图理解偏差 + 图层样式不匹配（部分新） | FC诊断 | 31e2a00 |
| B007 | 图层类型混乱 — 声称面层实际产出点层（部分新） | 工具调用 | 7735cb8 |
| B009 | 回到底部按钮位置+样式不当（太显眼·右下→右上） | UI | adef900 |
| B010 | 飞轮测试数据层命名混乱 — L2·e2e 不知所云 | UI | adef900 |
| B011 | 飞轮测试每例重复加载行政区 — 图层堆叠 | 工具调用 | adef900 |

---

## 修复时间线（倒序）

| 日期 | commit | 修复内容 | 关联 Bug |
|------|--------|----------|:---:|
| 2026-08-01 | 898998b | CB-10 P1-2：_quickIntent 加「数据清单」意图（上传了哪些/有哪些数据/数据列表）→ general... | B003/B005/B006 |
| 2026-08-01 | 7735cb8 | CB-10 P1-3：_checkGeomType 几何类型门——clip 需点层/overlay+extract 需面... | B007 |
| 2026-07-29 | 31e2a00 | P0-4: harness.js 3 处 finalStep context 注入 newLayerCount 执行摘要... | B002/B004/B005/B006 |
| 2026-07-29 | 8e5e76f | P0-4 v2 治本：① tools.js 五工具观测诚实化（count=0 不说"已生成"）② harness.js ... | B002 |
| 2026-07-29 | 3a97e19 | P0-4 v3 根治：① _autoExpandOverlays 代码自动扩展多步骤 ② D057 修订允许多 tool... | B002 |
| 2026-07-29 | adef900 | ① 按钮迁至右上角 sticky（原右下）② 透明磨砂背景+细绿边框（原深色填充）③ 文本 '↓'（原'回到底部 ↓'） | B009/B010/B011 |
| 07-28 | 1320e7c | M1 `_norm_where` 拆逗号（支持 `in` 多值列表） | B001/B001 |
| 07-28 | f68f61c | M3 契约 `extract_feature` 去「单要素」误导（`when`=FC description·上游根因） | B001 |

## 复发趋势（repro ≥ 2）

- **B001** · 多要素裁剪失败螺旋（extract_feature 字段重命名断裂 + 单工具限制 + FC 推理死循环） — 4× 复现（resolved）
- **B002** · finalStep 假结论 — "只说不做/只做一半"（复现） — 3× 复现（open）
- **B008** · 网格聚合 2D/3D 视角未解耦（新发现） — 3× 复现（open）
- **B003** · LLM 推理螺旋 — 简单查询耗时异常（复现） — 2× 复现（resolved）
- **B004** · finalStep 假结论 — 筛选点图层"只说不做"（复现） — 2× 复现（open）

---

## 飞轮对接

- **飞轮用例**：27 个（`tests/emc_test_cases.md`）
- **最近报告**：report-2026-08-01-02-llm (52%·13/25)（`tests/reports/`）
- **仪表盘**：`?test=1` → 仪表盘 tab（KPI + 未解决清单 + 复发趋势 + 回归关注）
- **索引文件**：[`_index.md`](_index.md) · [`_trend.md`](_trend.md) · [`_regression.md`](_regression.md)
- **条目目录**：[`open/`](open/) · [`resolved/`](resolved/)
