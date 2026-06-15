# SCRIPT/ — 数据分析引擎层 CLAUDE.md

> 优先级: 本文件 > 项目根 CLAUDE.md > 全局 CLAUDE.md

## 模块职责

L0→L1→L2→L3→L4 四级数据管道。这是项目核心分析逻辑所在，修改需走完整 SOP。

## 生产文件 vs 辅助文件

| 生产代码（修改需 SOP） | 辅助代码（可跳过 SOP） |
|------------------------|------------------------|
| `data_governance.py` — L0→L1 主编排器 | `generate_test_data.py` — 测试数据生成 |
| `emotion_analysis_v1.py` — L1→L2 SnowNLP 引擎 | `generate_l1_mock.py` — L1 模拟数据 |
| `relevance_filter.py` — 两层相关性漏斗 | `test_scripts.py` / `test_scripts_2.py` — 早期测试 |
| `run_analysis.py` — CLI + Tkinter 入口 | `test_scripts_heatmap.py` — 热力图测试 |
| | `label_training_data.py` — 标注工具 |

## 管道调用链

```
data_governance.py (L0→L1)
  ├── step1_load_and_transform()  → core/coord_transform.py
  ├── llm_classify_batch()        → relevance_filter.py → DeepSeek API
  ├── 过滤 (relevant + has_location)
  ├── 脱敏 (清空 comments)
  └── step4_run_l2_analysis()
        └── run_analysis_task()   → emotion_analysis_v1.py
              └── run_pipeline()  → SnowNLP + jieba
                    └── export_results() → core/export.py
```

## 编码规范

- 每个公开函数必须 `@track("MOD_XXX.F_NNN")`
- 关键 if/else/for 分支（>5 行）必须 `with TrackContext(...)`
- 数据管道步骤记录 in_n / out_n
- 所有 print 使用 `_safe_print()`（Windows GBK 兼容）
- L0 原始 CSV 列名: lon_gcj02 / lat_gcj02（不是 lon/lat）
- L1 输出 26 列（不含 in_scope / _kw_pass）
- L2 输出 29 列（keywords 已上移至 L1）

## 坐标系转换

详见 `core/CLAUDE.md` 坐标转换规范。

简记：`GCJ-02 → WGS84 (EPSG:4326) → CGCS2000 (EPSG:4546, 宜昌 CM 111E)`

## API 依赖

| API | 用途 | 环境变量 |
|-----|------|----------|
| DeepSeek | L1 相关性 LLM 分类 | `DEEPSEEK_API_KEY` |
| 批次大小 | 50 条/次（`llm_classify_batch`） | — |
| 重试策略 | 3 次指数退避 | — |

## 禁止事项

- 不要在 `data_governance.py` 中硬编码 API Key
- 不要修改管道步骤顺序而不更新 `docs/spec.md`
- 不要在无 API Key 时静默跳过 L1 LLM 步骤（应明确报错或降级提示）
- 不要删除旧的 test_scripts.py（作为历史参考保留）
