---
name: model-strategy-2026-08
description: 2026-08-02 模型使用策略变更——不再「调动次数节省优先」·不禁 subagent·DeepSeek key 随便用·但仍尽量节省
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 03747b20-6ef1-49b3-8c8c-c01d7496c5c0
  modified: 2026-08-01T15:57:20.896Z
---

用户 2026-08-02 明确模型使用策略变更（覆盖此前「调动次数优先」全局规则）：

1. **不再「调用次数节省优先」**——开发不再单一 GLM 模型调用，会用到 DeepSeek（如当前会话的 Claude 就由 DeepSeek 驱动）；计费不再按调动次数，不必抠调用。
2. **不再需要禁 subagent**——Explore / Plan / Agent 可用，需要时放心派。
3. **但开发依然要尽量节省的方式**——不铺张、克制使用（批量并行/合并修改等习惯保留）。

**Why**: 用户称「搜索用 key 就用 deepseek 的，随便用不用担心 token」——资源约束从「调动次数」变为「token 不担心但别浪费」。
**How to apply**: 复杂任务可派 subagent 并行探索/规划；常规工作仍主线程 + 批量并行（好习惯保留）；LLM/搜索调用不抠门。与本会话记忆 [[token-saving-workstyle]] 部分冲突——本条覆盖「禁 subagent / 调用优先」部分，「省 token 好习惯」部分保留。
