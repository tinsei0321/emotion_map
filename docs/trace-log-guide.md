# trace.log 使用指南（CB-12 · 业界级追踪日志）

> **目的**：让所有组（claude / Codex / glm）都能利用 trace.log 做根因分析——先取证·后推断。
> **背景**：B3 大失败根因定案教训——glm组 读 trace.log 定案（while-loop F_002）·claude/Codex 凭推断错两次。本指南 = 取证纪律固化。

## 一、trace.log 是什么

- **路径**：`.trace/trace.log`（本地·gitignore 不进 git·各组读自己环境）
- **写入**：`core/tracker.py` 的 `@track` / `TrackContext` / `trace_log` 自动写·每次调用一条
- **格式**（CB-12 起含 session 关联）：
  ```
  [TRACE] 21:17:36 | MOD_AIQA.F_002 | [enter] | 0.1ms | session=sess-1234-5678
  [TRACE] 21:17:36 | MOD_LLM.F_001 | chat stream=True model=deepseek-v4-flash msgs=12 | session=...
  ```
- **轮转**：>200MB 自动轮转（trace.log.1/2/3·env `EMOTION_TRACE_MAX_BYTES`/`EMOTION_TRACE_BACKUP` 可调）

## 二、核心 ID 速查（根因分析用）

| ID | 含义 | 用途 |
|----|------|------|
| `MOD_AIQA.F_002` | build_agent_prompt（agentStep） | **while-loop 铁证**（出现 = ReAct 多轮） |
| `MOD_AIQA.F_003` | build_final_prompt（finalStep） | 结论出口 |
| `MOD_LLM.F_005` | FC diagnose | 选型 |
| `MOD_LLM.F_001` | LLM chat（**公共出口**·agentStep+finalStep 共用） | **勿作 while-loop 判据**（msgs 恒定≠非多轮） |
| `MOD_LLM.F_002` | chat fallback | provider 切换 |
| `MOD_AIQA.F_007` | search_chat | 联网搜索 |

## 三、用法（tools/trace_query.py）

```bash
# 根因分析第一动作：各 ID 计数（一眼看 while-loop/finalStep/FC 分布）
py tools/trace_query.py --stats

# 按 ID / 时间窗 / 级别 / session / 关键词
py tools/trace_query.py --id MOD_AIQA.F_002 --time 21:14-21:50
py tools/trace_query.py --level ERR
py tools/trace_query.py --session B3-final8
py tools/trace_query.py --case B3 --tail 100
```

## 四、各组协作规范（CB 流程步骤 0 · 取证）

1. **跑测试带 session**（隔离批次·防混入调试活动）：
   ```bash
   EMOTION_TRACE_SESSION=B3-<批次> py tests/browser/flywheel_audit.py --batch B3
   ```
2. **反评价/验证报告附 trace 证据**：`trace_query --stats --session <批号>` 结果（stats 表）随报告
3. **根因分析第一动作**：`--stats` → `--id <疑点> --time <窗>` → 逐条
4. **推断只作假设·trace 数据先行**（数据定案·推断验证）

## 五、红线（core/CLAUDE.md）

- `@track()` 签名 / `_TRACKING_REGISTRY` 格式 **禁止改**
- 本机制 = 增量加（结构化字段追加 + 轮转 + 查询工具）·兼容旧行
