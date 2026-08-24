---
name: cb-distributed-testing
description: 测试任务三组并行分布式执行·claude组 拆解分配·持续优化 CB 机制（工作坊式）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 22c37718-5afc-4bcf-8ba0-88c388874c17
  modified: 2026-08-09T03:09:27.788Z
---

用户规则（2026-08-09 定）：测试任务越来越重、单靠人眼测已难以为继 → **测试任务由 claude组（Claude Code）合理拆解、针对性分配给三组（claude组 / Codex / glm组）同时进行**。项目推进中 claude组 须**不断提出优化 CB 机制/流程的意见**，保持工作坊式的先进性、流畅性、科学性。

**Why**：测试负载超出单人目测承受力，需分布式并行；分配权集中 claude组 保证规划一致。

**How to apply**：
- claude组 分发测试任务前，先确认各组平台 Harness 环境就绪（Python/Playwright/API Key/trace/端口隔离），针对性分配、规避各组能力盲区（如某组无浏览器/无 Key）。
- 每次 CB 轮次同步审视机制本身可优化点（测试分布、节奏、工具链、双阵营协作），主动提优化意见，不待用户说。
- 三组平台：claude组 = Claude Code + DeepSeek/GLM；codex组 = Codex + deepseek-v4-flash；glm组 = ZCode + GLM 5.2。

关联：[[cb-knowledge-base]] [[commit-only-user-pushes]]
