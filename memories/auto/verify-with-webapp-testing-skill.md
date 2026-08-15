---
name: verify-with-webapp-testing-skill
description: 前端验证用 webapp-testing skill（非 Playwright MCP）；默认不验证，交付肉眼验
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fed1d60a-02fb-4599-aa2e-975832ec5441
---

前端改动验证：**默认不跑自动验证**（效率低），交付后由用户肉眼验。确需验证（控制流/数据流风险、bug 复现）时，用 **webapp-testing skill**（已安装），不用 Playwright MCP。

**Why**：用户明确说过多次——Playwright MCP 太慢/重，已装 webapp-testing skill 替代。每次默认上 Playwright = 浪费调动 + 违背"调动次数优先"。

**How to apply**：
- 常规前端/CSS/HTML/JS 改动：实现完交付，**不自动验证**（用户 F5 肉眼验）。
- 仅以下上 webapp-testing：(a) 用户明确要求；(b) 控制流/异步/数据流隐患（paint 切换、filter、坐标转换、生成管线）；(c) bug 复现/回归。
- 命中 (b)(c) 时调用 webapp-testing skill 而非 Playwright MCP。

关联 [[no-routine-playwright-verify]]（原"不跑非必要 Playwright"——现扩展为用 webapp-testing 替代）。
