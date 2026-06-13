# 决策追踪系统 — 全局规范

## 已采纳决策
- **2026-06-13**：引入决策追踪系统 (Decision Tracking System)，ADR-008
- 详见 `docs/decisions.md` ADR-008

## 所有 Agent 必须遵守
1. 所有公开函数必须 `@track("MOD_XXX.F_NNN")`
2. 所有关键决策分支 (>5行) 必须 `with TrackContext("MOD_XXX.D_NNN", ...):`
3. 所有 I/O 操作必须埋点
4. 所有追踪 ID 必须在 `core/tracker.py` 注册表登记
5. 编号连续不跳号

## 模块 ID 速查
| 模块 ID | 文件 |
|---------|------|
| MOD_GOV | SCRIPT/data_governance.py |
| MOD_ANA | SCRIPT/emotion_analysis_v1.py |
| MOD_REL | SCRIPT/relevance_filter.py |
| MOD_RUN | SCRIPT/run_analysis.py |
| MOD_LOADER | core/data_loader.py |
| MOD_MAP | core/map_engine.py |
| MOD_TRANSFORM | core/coord_transform.py |
| MOD_RANGE | core/range_selector.py |
| MOD_EXPORT | core/export.py |
| MOD_UI | core/ui_components.py |
| MOD_APP | apps/app_main.py |
| MOD_SCRAPER | SCRAPER/spiders/ |
| MOD_TRACKER | core/tracker.py |

## 渐进式埋点进度
- [x] core/tracker.py (基础设施自身)
- [x] core/coord_transform.py (6个函数)
- [x] core/data_loader.py (1个函数 + 2个决策点)
- [x] core/export.py (2个函数)
- [x] core/map_engine.py (5个函数)
- [x] core/range_selector.py (9个函数)
- [x] core/ui_components.py (10个函数)
- [x] SCRIPT/data_governance.py (6个函数)
- [x] SCRIPT/emotion_analysis_v1.py (5个函数)
- [x] SCRIPT/relevance_filter.py (4个函数)
- [x] SCRIPT/run_analysis.py (2个函数)
- [x] apps/app_main.py (2个函数)
- [x] SCRAPER/spiders/xiaohongshu_spider.py (2个函数 + 1个决策点)

### 统计
- 总计埋点: **55** 个追踪 ID
- 覆盖文件: **13** 个 Python 文件
- 完成日期: 2026-06-13
