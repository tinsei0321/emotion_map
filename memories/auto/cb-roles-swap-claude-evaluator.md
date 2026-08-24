---
name: cb-roles-swap-claude-evaluator
description: 角色变更（2026-08-13）——claude组由主开发转为第三方独立评估（接替原 Codex 评估岗）·Codex 为主开发（唯一 git 写者）·zcode组评估不变
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 191f11bd-159d-4b99-89a3-912fe75d498b
  modified: 2026-08-13T08:52:31.364Z
---

**角色变更（2026-08-13 生效）**：claude组 = 第三方独立评估（接替原 Codex 评估岗）；Codex = 主开发（唯一 git 写者·commit 由 Codex 执行）；zcode组 = 评估方不变。

**claude组新职责**：
1. 只读本地文件，**不 git pull/push/commit**（commit 由 Codex 主开发统一执行）
2. **不写生产代码、不改数据、不改正式 Excel**
3. Codex 每轮完成工作后发审计/讨论邀请 → 我逐焦点评估
4. 意见落盘：`docs/catch-ball/discuss/CB*-*_评估_Claude-YYYY-MM-DD.md`（固定格式：〇一句话结论 / 一总评 / 二逐焦点 agree/disagree/partial+一句话证据+定稿建议 / 三定稿建议清单 P0-P3 / 四红线核对；文件注明「评估方：Claude · 只读不 git」）

**评估基准（承重红线不变）**：77 项原始指标名逐字不动 / 数据源只允许中转站真实数据（sim 禁入）/ 分析过程不消费 board（方面=框架·结论=数据验证）/ 宏观诊断非精确识别 / 口径可溯 / 术语「街办」≠道路 / diagnose prompt 永不改动。

**Why**：用户拍板角色互换（三组轮岗机制）。交接卡已同步角色变更注；沿用原 Codex 评估立场与方法·保持三方评估口径连续。

**How to apply**：后续会话按"评估方"身份工作——等 Codex 发邀请才评估；不主动写 DATA/analysis/ md、不做 xlsx；自己之前的开发产物（page1-6 md 等）转交 Codex 主开发接手维护。更新交接卡/记忆等 CB 域文档仍由我维护（非生产数据）。

关联：[[cb-third-party-no-git]]（权限口径反转·claude 现为"只读方"）· [[cb-roles-rename-zcode]]· [[page-rebuild-with-data-audit]]（工作流转交 Codex 参考）
