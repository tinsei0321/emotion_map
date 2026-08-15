---
name: topic-table-frontend-sync
description: 改 performance_config.TOPIC_TABLE 必须同步 frontend/js/panel.js 的 TOPIC_POLARITY/TOPIC_ORDER，否则新关键词在面板不显示
metadata: 
  node_type: memory
  type: project
  originSessionId: df323143-9af6-431f-bd47-e5904afa711d
---

`frontend/js/panel.js` 的 `TOPIC_POLARITY` + `TOPIC_ORDER` 是**硬编码白名单**，`_keywordRank` 对未登记的 topic **直接丢弃**。它与 `SCRIPT/performance_config.py::TOPIC_TABLE` 是**双源**——改后端词表（加/换/调权关键词）必须手动同步前端白名单，否则新词数据里有、面板不显示。

**Why**：2026-07-04 占道停车/大南门/长江夜游/西坝不夜岛/收费不合理 三时点全不显示，根因就是改了 TOPIC_TABLE 没同步白名单。已咬两次。

**How to apply**：改 TOPIC_TABLE → 立即同步 panel.js TOPIC_POLARITY（topic→pos/neg/neu）+ TOPIC_ORDER（每极性词序列）。已写进 [[push-not-redline]] 同级的 CLAUDE.md「数据模拟方法论」+ `.claude/agents/sim-emotion-data.agent.md`。后续应演进为后端单源（API/数据字段）驱前端，消双源。相关：[[grid-4x5-attribution]]（同为 4×5/关键词映射）。
