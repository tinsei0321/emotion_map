# CB-16 全局优化 + 发版快照 + 时间轴重规划预检（glm组 · ZCode + GLM 5.2）

> **预检方**：glm组（ZCode + GLM 5.2）  
> **日期**：2026-08-04 | **对象**：4 子项实施草案（全局优化 / 发版快照 / 时间轴重规划 / backlog 收尾）  
> **方法**：CLAUDE.md/emc-fix-progress.md/todo.md/spec.md 现状核实 + time-source.js/geo_registry.py/config.py 代码审查 + DATA/ 目录文件系统验证 + manifest 模板解析运行时验证 + validate_skill_params 运行

---

## 预检结论：通过（4 子项可行·1 个 P0 + 2 个 P1 + 3 个 P2 建议）

**4 子项草案全部可行。时间轴候选 1（geo_registry 同源 + fallback API）思路正确但有一个文件名 pattern 陷阱（L1 T1 双扩展名 `_csv.csv.geojson`·需特判）。候选 2（落手写 manifest）不碰数据红线（只是移动描述符 JSON·非数据文件）。validate_skill_params 当前 FAIL（7 工具 when/params/yields/contributes contracts≠paradigm drift）——backlog 收尾应修。记忆 GC 的 push 冲突需用户拍板。**

---

## 一、全局优化（子项 1）— **OK（范围合理·1 个需用户拍板）**

| 预检点 | 判定 | 证据/建议 |
|--------|:---:|---------|
| CLAUDE.md「当前开发状态」5 行更新 | ✅ | L3/L4/空间分析/UI 均已完成·L0→L1 补"购买"合理 |
| todo 周归档（07-27~08-02） | ✅ | 5 日段归档 + 删 :55 重复节·标准文档卫生 |
| emc-fix-progress.md 头部更新（220→276） | ✅ | 当前头部写 pytest 220·实际 274+·版本 v3.5 未含 CB-12/16 |
| spec.md / architecture.md Streamlit 死段 | ✅ | header 已声明退役·清引用是标准清理 |
| decisions.md ADR-017~019 | ✅ | 建议声明冻结由 revision-log 承接（非新增完整 ADR·减少文档债） |
| 记忆 GC：push 冲突裁决 | ⚠️ **需用户拍板** | `push-not-redline` vs `commit-only-user-pushes`——glm组 无法代用户定规则·建议列出两条冲突原文 + 影响·交用户选 |

**遗漏检查**：无遗漏——AGENTS.md 也应同步（当前仍写 "Streamlit 已于 2026-07-18 退役" 但可能有其他过时段落）。

---

## 二、发版快照（子项 2）— **OK（先快照不修 PRM 对路）**

| 预检点 | 判定 | 理由 |
|--------|:---:|------|
| 先做 B3 快照（不修 PRM） | ✅ | 发版快照 = 现状记录·非冲达标。PRM 缺口是已知 backlog（G1）·发版前修 = 范围蔓延 |
| link_checkup 体检（20 例） | ✅ | 发版前确认出口卡片链路不回归 |
| pytest 全量零回归（276） | ✅ | 标准发版门 |

**glm组 建议**：快照应包含 `trace_query --stats`（验证 F_002/pro 调用状态）——这是 CB-12 建立的 trace 纪律·发版快照应含。

---

## 三、时间轴重规划（子项 3）— **OK（候选 1 思路对·1 个文件名陷阱）**

### 根因确认

glm组 独立验证：
- `time-source.js:22` `MANIFEST_URL = '/DATA/performance/_time_manifest.json'` → **404**（文件不在）
- `DATA/old_data_processed/_time_manifest.json` → **存在**（旧位置·R100 迁移时漏移）
- `DATA/performance/*.geojson` → **存在**（数据没丢·只缺描述符）
- `DATA/processed/` → **不存在**（旧 manifest 引用此路径·已迁移到 performance）

### 候选 1（geo_registry 同源 + fallback API）— **思路正确·1 个陷阱**

| 预检点 | 判定 | 证据 |
|--------|:---:|------|
| 从 `_POINT_LAYERS` 单一权威派生 manifest | ✅ | geo_registry.py:29-41 已有 9 条点层定义（含文件名/标签/层级） |
| 扫 PERFORMANCE_DIR 现场组装 | ✅ | config.py:14 `PERFORMANCE_DIR = DATA/performance` |
| sourceTemplate 拼 geojson 路径 | ⚠️ **陷阱** | **L1 T1 文件名 = `yichang_L1_T1_result_csv.csv.geojson`（双扩展名）**·L1 T2/T3 = `yichang_L1_T2_result_geojson.geojson`（标准）·L2 = `yichang_L2_T1_L2_result_geojson.geojson`（有 _L2_ infix）。同一层不同时间片文件名 pattern 不同 → sourceTemplate 模板无法统一填——**需特判或逐文件扫** |
| time-source.js fallback（manifest 404 → API） | ✅ | 合理·两层容错 |
| 消除第二份手写清单 | ✅ | geo_registry 单一源派生 = 消除时间轴/问答两份清单 |

**L1 双扩展名陷阱**（P0 实施注意）：

```
实际文件名（DATA/performance/）：
  yichang_L1_T1_result_csv.csv.geojson    ← 双扩展名（_csv.csv.geojson）
  yichang_L1_T2_result_geojson.geojson    ← 标准
  yichang_L1_T3_result_geojson.geojson    ← 标准
  yichang_L2_T1_L2_result_geojson.geojson ← _L2_ infix
  yichang_L2_T2_L2_result_geojson.geojson
  yichang_L2_T3_L2_result_geojson.geojson
  ermawu_l3l4_T1_result_geojson.geojson
  ermawu_l3l4_T2_result_geojson.geojson
  ermawu_l3l4_T3_result_geojson.geojson
```

候选 1 实施时：**不能假设 sourceTemplate 能统一填**——应改为扫 PERFORMANCE_DIR 匹配 `{layer_id}_*` glob → 动态发现文件名（而非模板拼接）。这是比 claude组 草案更稳健的方案。

### 候选 2（落手写 manifest）— **不算数据红线**

| 预检点 | 判定 | 理由 |
|--------|:---:|------|
| 落 `_time_manifest.json` 到 `DATA/performance/` | ✅ | manifest 是**描述符 JSON**（元数据·非数据文件）——定义数据集/时间片/模板·不含任何情绪数据。移动它 ≠ 动数据红线 |
| 修 3 条 sourceTemplate | ⚠️ | 旧 manifest 引用 `DATA/processed/`（已不存在）→ 需改为 `DATA/performance/`。但 L1 T1 双扩展名仍需特判 |

**glm组 建议**：候选 2 立即解封（移动 JSON + 修路径 + L1 T1 特判）→ 候选 1 长期收编（API 同源）。

---

## 四、backlog 收尾（子项 4）— **OK（3 项都该做·validate_skill_params 当前 FAIL）**

| 预检点 | 判定 | 证据 |
|--------|:---:|------|
| validate_skill_params 7 工具 drift | **❌ 当前 FAIL** | glm组 运行 `pytest validate_skill_params.py` → **1 failed**：density/buffer/clip/overlay/zonal_stats/extract_feature/merge 的 `when`/`params`/`yields`/`contributes` 在 contracts vs paradigm 间 drift（CB-12/CB-16 改了 contracts 但 paradigm 未同步） |
| renewal 卡 perceptible_metrics domain 门控 | ✅ 应做 | glm组 Wave 3 报告标注的 P3 已知项·_build_card:267 无条件调用 |
| CPD-L03 硬断言 | ✅ 应做 | 根因已修·test-cases.js CSV 改名即可 |

**validate_skill_params FAIL 细节**（P1·应本次修）：
```
FAIL: 7 工具 when/params/yields/contracts ≠ paradigm
  density.when: contracts 加了 CB-12 P2 方格网格说明·paradigm 未同步
  buffer.when: contracts 加了 G2 radius 换算·paradigm 未同步
  clip.when: contracts 加了 CB-12 P2 裁剪点说明·paradigm 未同步
  overlay.when: contracts 重写了·paradigm 未同步
  zonal_stats.when: contracts 加了 G2 boundary 说明·paradigm 未同步
  extract_feature.when/params/contributes: contracts 加了 CB-12 P2 筛选说明·paradigm 未同步
  merge.when/params/yields/contributes: contracts 加了 CB-11 多图层说明·paradigm 未同步
```

**修复方向**：paradigm.py 的 GEO_TOOL_CATALOG 对应字段同步 tool_contracts.py 的 when/params_str/yields/contributes——或放宽 validate_skill_params 断言（允许 contracts 有增量补充·只校验 paradigm⊆contracts 子集关系）。

---

## 五、预检逐条回应

| # | 预检项 | glm组 判定 |
|:---:|------|:---:|
| 1 | 全局优化范围合理？ | ✅（记忆 GC push 冲突需用户拍板） |
| 2 | 发版快照先做 B3（不修 PRM）？ | ✅ agree |
| 3 | 时间轴候选 1 思路对路？ | ✅（L1 T1 双扩展名需 glob 扫文件·非模板拼接） |
| 3 | L1 双扩展名特判可靠？ | ⚠️ 改为 glob 扫更可靠 |
| 3 | 候选 2 算数据红线？ | ❌ 不算（描述符 JSON·非数据文件） |
| 4 | backlog 3 项都该做？ | ✅（validate_skill_params **当前 FAIL**·P1 优先） |
| 5 | 测试方案够？ | ✅（时间轴 fallback 单测 + 端点直测 + skill_params 回归） |
| 6 | 承重零触碰？ | ✅（时间轴不碰 geo 问答·全局优化只改文档） |
| 7 | 4 子项都要？优先级？ | ✅ 全要·P1: skill_params + 时间轴候选 2 · P2: 文档/记忆 GC |

---

## 六、优先级建议

| 优先级 | 子项 | 理由 |
|:---:|------|------|
| **P0** | 时间轴候选 2（立即解封） | 演示阻塞——时间轴 404 = 演示不可用 |
| **P1** | validate_skill_params 修 drift | 当前 FAIL·CI 红线 |
| **P1** | 发版快照（B3 + link_checkup + pytest） | 发版前必需 |
| **P2** | 全局优化（文档更新 + 记忆 GC） | 工程卫生·不阻塞功能 |
| **P2** | backlog 收尾（perceptible 门控 + CPD-L03） | 已知 backlog·不阻塞 |
| **P3** | 时间轴候选 1（API 同源收编） | 长期优化·候选 2 解封后不阻塞 |

---

## 七、一句话结论

**4 子项草案可行——全局优化范围合理（记忆 GC push 冲突需用户拍板）·发版快照先做不修 PRM 对路·时间轴候选 1 思路正确但有 L1 T1 双扩展名陷阱（应改 glob 扫文件非模板拼接）·候选 2 不碰数据红线（描述符 JSON 移动）·validate_skill_params 当前 FAIL（7 工具 contracts vs paradigm drift·P1 需修）。优先级：P0 时间轴候选 2 解封 → P1 skill_params + 发版快照 → P2 文档/记忆 GC + backlog。**

---

*glm组（ZCode + GLM 5.2）· CB-16 全局优化预检 · 2026-08-04*  
*验证基于：CLAUDE.md/emc-fix-progress.md/todo.md 现状核实 + time-source.js:22/geo_registry.py:29-41/config.py:13-14 代码审查 + DATA/ 文件系统验证（manifest 404 + L1 T1 双扩展名 + old_data_processed 残留）+ validate_skill_params 运行（1 failed）+ pytest 274 passed。*
