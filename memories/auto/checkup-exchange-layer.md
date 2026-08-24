---
name: checkup-exchange-layer
description: "城市体检对接层（阶段 0'·2026-08-11）— DATA/exchange 三分法 + PII 例外 + MOD_CHECKUP + 口径 18 项"
metadata: 
  node_type: memory
  type: project
  originSessionId: 45ee6ad8-5b1f-41d0-abc4-a6aee44d9056
  modified: 2026-08-11T04:45:55.863Z
---

城市体检·两板块分析（双项目交叉·紧急任务定稿）阶段 0' 对接层已落地（2026-08-11）。

**落点**：
- 对接层 = `DATA/exchange/`（README 三分法 + manifest.json 引用清单 + schema_inventory.md + PII_EXCEPTIONS.md + 口径对齐.md），登记 `docs/context-map.md`。
- 上游 = zcode 中转站 `{URENEWAL_ROOT}/1 宜昌市城市体检/EMC数据中转站/`（manifest v1.1.0·已预治理·不建五层）。
- `{URENEWAL_ROOT}` 占位新增本机开发环境 `D:\OneDrive\2026\15_城市更新专项规划研究`（`docs/urban-renewal-plan/_PATHS.md`）。
- 追踪模块 = **MOD_CHECKUP**（`SCRIPT/checkup_ingest.py`·阶段 1' 规划·F_001 起·AGENTS.md 已登记）。

**Why**：Codex 评估 7 修正 + 6 决策全采纳——①治理管线不能直跑 data_governance.py（WGS84 会被当 GCJ-02 二次转换·数百米偏移）②不重建 DATA/exchange 五层（zcode 已建）③PII：building_50year_1.geojson 380 要素含 yslxr/yslxrdh（验收联系人+电话·值空格但字段存在）·只引用不复制。

**How to apply**：
- 引用数值前必读 `口径不一致清单_18项.csv`（建议口径：学位 6603 非 7482 / 结构 42 非 43 / 菜市场 57.84% / 250栋≠54栋结构隐患）。
- 阶段 1' checkup 直通适配器：WGS84 透传（无 GCJ 二次转换）·无 LLM 漏斗·L2 旁路·L1 导出剥离 `存在问1`（照片URL）·面层质心化点层。
- 阶段 2' RAG 消费 04_互通优化（15 fact 卡 + RAG 安全版摘要）·勿重做；outlet_kb 增客观轨契约。
- PII 验收扫描：`grep -rE "yslxr|yslxrdh|存在问1" DATA/performance/ DATA/boundaries/ docs/urban-renewal-plan/00-宜昌专项/` 零残留。

关联：[[emc-tri-state-exit-contract]]（EMC 出口契约）· [[emc-l4-lazy-enrichment]]（归因 lazy）· [[rag-index-must-store-text]]（RAG 三支柱）
