---
name: acceptance-through-cb
description: 每次功能完成后，验收工作交给另两组（Codex/glm组）走 CB 流程做，不默认用户浏览器肉眼验证为主验收
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0e80bf22-14e5-4417-ac10-dd091eb78bca
  modified: 2026-08-08T06:57:42.075Z
---

用户 2026-08-08 明确：「每次完成后验收工作让另两组完成，进入 CB」。

**Why**：用户不想每次完成都自己浏览器肉眼验收（耗时、且让 claude组 与两组之间缺一次独立校验）；验收权威从「用户肉眼」移到「CB 双阵营评估」。这也让「整体验收清单」这类功能正确性验收从用户侧转由两组以证据驱动方式（代码核验 + 可跑测试 + e2e-seam 直测）完成。

**How to apply**：每完成一个功能/专题 → 发起 CB「实施后检查/验收」（claude组 出改动清单 + 验收焦点 + 附 A prompt）→ 两组独立验收出 SCAN/回应 → claude组 反评价收敛 → 定「可验收/需修复」。观感类（观点卡干货感/setTerrain 地势感等纯 UI 表现力）两组只能代码核验，可标注「可选用户观感复核」，不作主验收。与 [[no-routine-playwright-verify]] 互补：claude组 实现后仍不跑 Playwright 自验，但验收环节进 CB 由两组做。
