---
name: trace-log-debug-discipline
description: trace.log 是调试第一证据源（用户要求）——根因分析先拉 trace.log 计数（F_002/F_003 非 F_001）·按 msgs 过滤非目标活动·保持同步更新
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 03747b20-6ef1-49b3-8c8c-c01d7496c5c0
  modified: 2026-08-02T14:27:22.354Z
---

用户 2026-08-02 明确要求：**学习 glm组 追踪 trace.log 的习惯·保持 trace.log 同步更新·这是 debug 好习惯**。

背景（B3 大失败根因定案教训）：glm组 用 `.trace/trace.log`（5M 行·在仓库）推翻了 claude组 和 Codex 的定案——claude组/Codex 都未先读 trace.log（凭 F_001 计数推断·口径错误：agentStep 也走 F_001·msgs 恒定因 history 拼入 context）。

**How to apply（根因分析纪律）**：
1. **第一动作 = 拉 trace.log 计数**——数 F_002（build_agent_prompt·while-loop 铁证）/ F_003（final）/ F_005（FC）·**非 F_001**（LLM 公共出口·不区分 agentStep/finalStep）
2. **按 msgs 过滤非目标活动**——trace.log 混有调试/并行活动（msgs=2 短调用非 B3）·按用例特征（msgs=12 长上下文）过滤才准
3. **读 [exit] 时长列**（非 enter 间隔）——单次调用时长看 exit Xms·enter 间隔含下一例耗时
4. **保持 trace.log 同步更新**——跟踪写入机制（core/tracker.py）不打断·每次会话/测试后确认 trace.log 是最新（修改时间覆盖该时段）
5. **推断只作假设不作结论**——trace.log 数据先行·推断作假设·验证后定案

**Why**: B3 大失败定案中·glm组 读 trace.log 定案（while-loop F_002 11 次）·claude组/Codex 凭推断错两次（无 while-loop / API 慢）。trace.log 在仓库·任何人可直读·是 debug 第一证据源。

相关：[[emc-tri-state-exit-contract]]（trace 决策回溯）·[[token-saving-workstyle]]（该省省·该取证取证）。
