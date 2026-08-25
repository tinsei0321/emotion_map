# 决策追踪编号全表（自根 AGENTS.md 移出 · PT-CB18 W1-2）

> 根手册只留铁律 9/10 一句口径与排查纪律；编号全表、埋点细则查本文。
> 编号 → 业务名速查另见仓根 `GLOSSARY.md`（`py tools/gen_glossary.py` 生成）。

## 决策追踪系统说明

**目的**：让 bug 定位从 O(n) 全量代码搜索降为 O(1) 决策 ID 精准跳转。

**基础设施**：`core/tracker.py` — 提供 `@track()` 装饰器 / `TrackContext` 上下文管理器 / `trace_*()` 快捷函数。

## 模块 ID 分配

| 状态 | 模块 ID | 文件 |
|------|---------|------|
| ✅ | `MOD_GOV` | `SCRIPT/data_governance.py` |
| ✅ | `MOD_ANA` | `SCRIPT/emotion_analysis_v1.py` |
| ✅ | `MOD_REL` | `SCRIPT/relevance_filter.py` |
| ✅ | `MOD_RUN` | `SCRIPT/run_analysis.py` |
| ✅ | `MOD_GEN` | `SCRIPT/generate_l1_mock.py` |
| ✅ | `MOD_PERF` | `SCRIPT/sim_performance_data.py` |
| ✅ | `MOD_SCRAPER` | `SCRAPER/spiders/` |
| ✅ | `MOD_GEOCODE` | `core/geocode.py` |
| ✅ | `MOD_LLM` | `ai_qa/llm.py` |
| ✅ | `MOD_AIQA` | `ai_qa/paradigm.py` + `ai_qa/prompts.py`（select_template 路由 + 5 build_*_prompt；manifesto.py 纯常量） |
| 🔧 | `MOD_CHECKUP` | `SCRIPT/checkup_ingest.py`（体检数据直通适配器·阶段 1' 规划·2026-08-11 定稿 D5 决策·F_001 起） |
| ✅ | `MOD_SPATIAL` | `core/spatial_analysis.py` + `core/buffer_analysis.py` |
| ✅ | `MOD_FIELD` | `core/field_dictionary.py` |
| ❌ retired | `MOD_APP` | ~~`apps/`~~ 2026-07-18 整层退役（`frontend/` 接管） |
| ⬜ | `MOD_LOADER` | `core/data_loader.py` |
| ⬜ | `MOD_MAP` | `core/map_engine.py` |
| ⬜ | `MOD_TRANSFORM` | `core/coord_transform.py` |
| ⬜ | `MOD_RANGE` | `core/range_selector.py` |
| ⬜ | `MOD_EXPORT` | `core/export.py` |
| ⬜ | `MOD_MM` | `SCRIPT/multimodal_analysis.py` |
| ⬜ | `MOD_UTILS` | `core/utils.py` |
| ⬜ | `MOD_PLACE` | `core/place_layer.py` |
| ⬜ | `MOD_UI` | `core/ui_components.py`（仅 `design/backups/` 残留引用） |
| 🔧 | `MOD_TRACKER` | `core/tracker.py`（infra 本体，非业务模块） |

> **状态图例**：✅ 已埋点+`register_track_id` 注册 / ⬜ 占位待埋点（保留规划意图，不删） / 🔧 追踪 infra 本体。**注册机制** = 各模块 `register_track_id()` 在 import 时调用，运行时填充 `core/tracker.py` 的 `_TRACKING_REGISTRY`（**非** tracker.py 内静态 dict）。
>
> **5.x 主力**：`MOD_SPATIAL` / `MOD_LLM` / `MOD_FIELD` / `MOD_AIQA` 均已正式分配 ✅（ai_qa broader paradigm+prompts 已埋点；manifesto.py 纯常量无函数）。仍待埋点：上表 9 个 ⬜ 模块。**低优先，勿擅自加 ID**（守 `_TRACKING_REGISTRY` 编号连续不跳号红线——待正式分配时整体规划）。

## 埋点规则

- 公开函数（非 `_` 前缀）→ `@track("MOD_XXX.F_NNN")`；
- 关键分支（>5 行 if/else/循环体）→ `with TrackContext("MOD_XXX.D_NNN", ...):`；
- I/O 操作（文件读写/API/DB）→ 必须埋点；
- 数据管道步骤 → 记录 in_n / out_n；
- except 块 → `trace_error()`；
- **高频循环扫描类豁免（PT-CB10 C2-8·D9 纪律固化）**：周期 ≥1s 的常驻扫描/轮询函数（如 watcher 循环）免 `@track`（防 [TRACE] 刷屏淹没有效信号）；但**必须**在其功能 ID 的 `register_track_id` 注册表描述中注明「高频扫描·免埋点」，使豁免可审计可追溯（先例：MOD_AIQA.F_029 render 收件箱 watcher）。

## Debug 工作流

```
报错 → 看 [TRACE] 日志 → 定位出错决策 ID → 跳转代码 → 精准修复
```
