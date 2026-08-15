---
name: l0-acquisition-purchase-strategy
description: "L0 原始数据未来走\"购买\"途径（非项目自采 Scrapy）；sim 当下有意为之且充分，勿当风险"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7eba1cd7-80b4-4a74-92f4-5a5c6807de5e
  modified: 2026-07-18T13:34:02.151Z
---

L0 原始数据的获取策略 = **未来走"购买"途径**（采购数据源），**非项目自采 Scrapy**。故 `DATA/processed/` 全是模拟数据（sim）**不是缺陷**——模拟数据是当下有意为之且充分的演示基底，自采 Scrapy 管线从未端到端跑通也不构成问题。

**Why:** 用户 07-18 全局复盘时明确澄清。我（Claude）初版复盘与第三方 SCAN 都曾把"真实数据=0 / 自采未跑通"误判为"最大单点风险"——这是用错标尺，与用"官方指标完备性"质疑 4×5 归因矩阵（[[project-design-philosophy]]）同类错误。

**How to apply:** 复盘/评估数据管道成熟度时，不要再把"sim 数据 / 自采未贯通"列为风险或短板。L1 DeepSeek key 验证只是常规待办（治理逻辑择机实跑一次证伪/证实），非战略风险。真正短板是前端测试薄，不是数据。归因能力由 EMC 分析时（[[emc-l4-lazy-enrichment]]）+ Sim 生成器（[[sim-research-buffer-methodology]]）覆盖，SCRIPT 层 L3/L4 ⬜ 预留是否补，视未来购买数据的处理需求而定。
