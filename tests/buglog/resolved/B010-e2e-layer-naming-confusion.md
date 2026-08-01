---
id: B010
title: '飞轮测试数据层命名混乱 — L2·e2e 不知所云'
type: UI
severity: LOW
priority: P2
status: resolved
module: UI
source: 飞轮发现
cb: CB-09
rootcause: ''
case_ref: ''
repro_count: 1
last_repro: 2026-07-29
---

## 标准化用例

**问句**：（飞轮测试运行时查看 Layers 面板）

**数据前提**：飞轮 `?test=1` 运行 llm 测试用例

**预期行为**：
① Layers 面板中测试注入的图层名清晰可辨（如「测试数据 · 情绪点」）
② 不使用 `e2e` 等内部代号命名面向用户的图层

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:---:|------|------|------|
| 1 | 07-29 | Layers 出现「L2 · e2e」组名，用户困惑来源 | e2e-seam.js loadPoints 硬编码组名 'L2 · e2e' |

## 修复记录

| 日期 | 操作 | commit |
|------|------|------|
| 2026-07-29 | e2e-seam.js loadPoints 组名 'L2 · e2e' → '测试数据 · 情绪点' | adef900 |
