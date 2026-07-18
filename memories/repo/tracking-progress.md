# 决策追踪系统 — 全局规范

> 追踪系统规则 + 埋点进度**快照**。
> **模块表权威源 = [`AGENTS.md`](../../AGENTS.md)「模块 ID 分配」表**（12 ✅ 已埋点 + 9 ⬜ 待埋点 + retired）——本文件**不复述模块表**，避免双源漂移（2026-07-18 CB-1 修正：曾 frozen 06-13、把已删/退役模块标成已埋点）。

## 已采纳决策
- **2026-06-13**：引入决策追踪系统 (Decision Tracking System)，ADR-008（详见 [`docs/decisions.md`](../../docs/decisions.md)）
- **5.x 主力扩展**：MOD_SPATIAL / MOD_LLM / MOD_FIELD / MOD_AIQA / MOD_PERF / MOD_GEN / MOD_GEOCODE（逐条见 AGENTS.md 模块表）

## 所有 Agent 必须遵守
1. 所有公开函数必须 `@track("MOD_XXX.F_NNN")`
2. 所有关键决策分支 (>5 行) 必须 `with TrackContext("MOD_XXX.D_NNN", ...):`
3. 所有 I/O 操作必须埋点
4. 所有追踪 ID 必须经各模块 `register_track_id()` 运行时填充 `core/tracker.py` 的 `_TRACKING_REGISTRY`（非静态 dict）
5. **编号连续不跳号**（承重红线，CLAUDE.md rule 10）

## 埋点规则（摘要）
- 公开函数（非 `_` 前缀）→ `@track`
- 关键分支（>5 行 if/else/循环）→ `TrackContext`
- I/O（文件/API/DB）→ 必埋点
- 数据管道步骤 → 记 in_n / out_n
- except 块 → `trace_error()`
- 热路径小 helper（resolve_role / is_*）→ **不 track** 防日志刷爆（同 spatial/field_dictionary convention）

## 退役模块（勿再埋点，ID 保留不删）
- `MOD_APP` (apps/app_main.py) — 2026-07-18 apps/ 整层退役
- `MOD_MAP` (core/map_engine.py) — 2026-07-18 退役（pydeck 僵尸，CB-1；详见 [`docs/retired.md`](../../docs/retired.md)）
- `MOD_UI` (core/ui_components.py) — 2026-07-18 退役（Streamlit 僵尸，CB-1）

## 进度（快照；权威见 AGENTS.md + 运行时 `_TRACKING_REGISTRY`）
- **当前**：12 模块 ✅ 已埋点 / 9 模块 ⬜ 待埋点（占位，**低优先，守编号连续勿擅自加 ID**）
- 待埋点候选（热路径优先）：`core/data_loader`、`core/export`、`core/range_selector`、`api/*` 端点；纯常量模块（`config.py`/`landuse_codes_2023.py`）标"无需追踪"而非 ⬜
- 历史"完成日期 2026-06-13 / 55 ID / 13 文件"为初期快照；7 月扩展后实际更多，精确计数以 AGENTS.md + 运行时注册表为准
