---
name: claude-code-model-default-flash
description: "Claude Code 默认模型 2026-08-26 起全档改 deepseek-v4-flash[1m]（settings.json 三项 pro→flash）；要 pro 需 /model 手动切"
metadata: 
  node_type: memory
  type: project
  originSessionId: 960e706a-817c-40ff-9ba3-f70a150cde4a
  modified: 2026-08-25T22:45:38.880Z
---

用户 2026-08-26 发现扣费异常（选 flash 却按 pro 扣）后拍板：**Claude Code 默认模型全档改 flash**。

- **背景**：`~/.claude/settings.json` 原配置是 DeepSeek 官方文档推荐值（ANTHROPIC_MODEL/OPUS/SONNET=deepseek-v4-pro[1m]·HAIKU=flash）——照抄没错，但会话默认主模型=pro，且显式设 DEFAULT_SONNET=pro 会覆盖官方网关「sonnet→flash」映射 → 大量消耗按 pro 计费。
- **改动**（备份 settings.json.bak-20260826）：ANTHROPIC_MODEL / DEFAULT_OPUS / DEFAULT_SONNET 三项 → `deepseek-v4-flash[1m]`；SMALL_FAST/HAIKU/SUBAGENT 原本已是 flash；EFFORT=max 不动。
- **效果**：新会话默认 flash（1m 上下文）；要 pro 时 `/model` 手动切 `deepseek-v4-pro[1m]`（模型列表仍可选手动）。

**How to apply:** 评估 token 成本/会话模型预期时默认按 flash 想；勿再假设 pro 默认。关联 [[codex-harness-config-isolation]]（codex 桌面工具 zai 配置是另一条线·互不影响）。
