# Trace 错误摘要 (Error Digest)

> 闭环补强 Wave4：SessionEnd 自动从 `.trace/trace.log` 摘取**新增** ERR/WARN 沉淀于此。
> 让 debug 史不再蒸发——可检索、可回灌。游标 `.claude/.trace-digest-cursor` 防重复（gitignored）。
>
> 说明：首个块曾含 pytest 负路径测试产生的 ERR 噪声，已清为干净种子头；
> 后续仅沉淀真实会话中产生的 ERR/WARN。

<!-- SessionEnd hook 会在下方按日期追加 ## YYYY-MM-DD HH:MM（N 条新增 ERR/WARN）块 -->
## 2026-08-10 13:53（2717 条新增 ERR/WARN）

```
            [TRACE] 20:34:20 | MOD_SPATIAL.F_008 | [ERR] | exception after 0.9ms | ValueError: aggregate_by_boundary_id 需 zone role 列（zone/area_tag/片区…）；当前点层无此列 | session=sess-43712-1786278837
              [TRACE] 20:34:23 | MOD_SPATIAL.F_009 | [ERR] | exception after 1.0ms | ValueError: DEM 分析需要至少 3 个点（极性=negative 过滤后剩 0） | session=sess-43712-1786278837
  [TRACE] 20:46:09 | MOD_TRANSFORM.F_005 | [ERR] | exception after 0.2ms | KeyError: 'lon_gcj02' | session=sess-25128-1786279569
    [TRACE] 20:46:09 | MOD_GOV.F_001 | [ERR] | exception after 0.3ms | EmptyDataError: No columns to parse from file | session=sess-25128-1786279569
      [TRACE] 20:46:09 | MOD_GOV.F_001 | [ERR] | exception after 0.0ms | FileNotFoundError: 原始数据文件不存在: /nonexistent/path.csv | session=sess-25128-1786279569
        [TRACE] 20:46:11 | MOD_ANA.F_007 | [ERR] | exception after 0.0ms | ValueError: 未知引擎: unknown_engine。可用: ['snownlp', 'deepseek-l2', 'llm', 'corpus']
        [TRACE] 20:46:20 | MOD_LLM.D_001 | [WARN] | retry provider=deepseek attempt=1/3 status=None: net | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_001 | [WARN] | retry provider=deepseek attempt=1/3 status=500: 500 | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_002 | [WARN] | fallback away provider=deepseek status=401（4xx 不可重试）: 401 | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.F_002 | [ERR] | all providers exhausted: 401 | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_001 | [WARN] | retry provider=deepseek attempt=1/3 status=None: net | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_001 | [WARN] | retry provider=deepseek attempt=2/3 status=None: net | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_002 | [WARN] | retry exhausted provider=deepseek，换下一家 | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.F_002 | [ERR] | all providers exhausted: net | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_003 | [ERR] | mid-stream failure provider=deepseek（不重试不换家）: mid | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_002 | [WARN] | fallback away provider=A status=401（4xx 不可重试）: 401 | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_001 | [WARN] | retry provider=A attempt=1/3 status=None: net | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_001 | [WARN] | retry provider=A attempt=2/3 status=None: net | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_002 | [WARN] | retry exhausted provider=A，换下一家 | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_001 | [WARN] | retry provider=B attempt=1/3 status=None: net | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_001 | [WARN] | retry provider=B attempt=2/3 status=None: net | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.D_002 | [WARN] | retry exhausted provider=B，换下一家 | session=sess-25128-1786279569
        [TRACE] 20:46:20 | MOD_LLM.F_002 | [ERR] | all providers exhausted: net | session=sess-25128-1786279569
          [TRACE] 20:46:32 | MOD_SPATIAL.F_006 | [ERR] | exception after 0.7ms | ValueError: cell_size 必须为正 | session=sess-25128-1786279569
            [TRACE] 20:46:32 | MOD_SPATIAL.F_008 | [ERR] | exception after 0.8ms | ValueError: aggregate_by_boundary_id 需 zone role 列（zone/area_tag/片区…）；当前点层无此列 | session=sess-25128-1786279569
              [TRACE] 20:46:35 | MOD_SPATIAL.F_009 | [ERR] | exception after 0.9ms | ValueError: DEM 分析需要至少 3 个点（极性=negative 过滤后剩 0） | session=sess-25128-1786279569
  [TRACE] 20:59:05 | MOD_TRANSFORM.F_005 | [ERR] | exception after 0.2ms | KeyError: 'lon_gcj02' | session=sess-41896-1786280345
    [TRACE] 20:59:05 | MOD_GOV.F_001 | [ERR] | exception after 0.3ms | EmptyDataError: No columns to parse from file | session=sess-41896-1786280345
      [TRACE] 20:59:05 | MOD_GOV.F_001 | [ERR] | exception after 0.0ms | FileNotFoundError: 原始数据文件不存在: /nonexistent/path.csv | session=sess-41896-1786280345
        [TRACE] 20:59:07 | MOD_ANA.F_007 | [ERR] | exception after 0.0ms | ValueError: 未知引擎: unknown_engine。可用: ['snownlp', 'deepseek-l2', 'llm', 'corpus']
        [TRACE] 20:59:16 | MOD_LLM.D_001 | [WARN] | retry provider=deepseek attempt=1/3 status=None: net | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_001 | [WARN] | retry provider=deepseek attempt=1/3 status=500: 500 | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_002 | [WARN] | fallback away provider=deepseek status=401（4xx 不可重试）: 401 | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.F_002 | [ERR] | all providers exhausted: 401 | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_001 | [WARN] | retry provider=deepseek attempt=1/3 status=None: net | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_001 | [WARN] | retry provider=deepseek attempt=2/3 status=None: net | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_002 | [WARN] | retry exhausted provider=deepseek，换下一家 | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.F_002 | [ERR] | all providers exhausted: net | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_003 | [ERR] | mid-stream failure provider=deepseek（不重试不换家）: mid | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_002 | [WARN] | fallback away provider=A status=401（4xx 不可重试）: 401 | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_001 | [WARN] | retry provider=A attempt=1/3 status=None: net | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_001 | [WARN] | retry provider=A attempt=2/3 status=None: net | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_002 | [WARN] | retry exhausted provider=A，换下一家 | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_001 | [WARN] | retry provider=B attempt=1/3 status=None: net | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_001 | [WARN] | retry provider=B attempt=2/3 status=None: net | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.D_002 | [WARN] | retry exhausted provider=B，换下一家 | session=sess-41896-1786280345
        [TRACE] 20:59:16 | MOD_LLM.F_002 | [ERR] | all providers exhausted: net | session=sess-41896-1786280345
          [TRACE] 20:59:28 | MOD_SPATIAL.F_006 | [ERR] | exception after 0.8ms | ValueError: cell_size 必须为正 | session=sess-41896-1786280345
            [TRACE] 20:59:29 | MOD_SPATIAL.F_008 | [ERR] | exception after 0.8ms | ValueError: aggregate_by_boundary_id 需 zone role 列（zone/area_tag/片区…）；当前点层无此列 | session=sess-41896-1786280345
              [TRACE] 20:59:31 | MOD_SPATIAL.F_009 | [ERR] | exception after 1.0ms | ValueError: DEM 分析需要至少 3 个点（极性=negative 过滤后剩 0） | session=sess-41896-1786280345
```

