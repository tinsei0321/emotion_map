---
name: sim-research-buffer-methodology
description: 模拟数据两方法论——Sim-0 资讯收集(web-search→research/<area>.md 通用 Phase 0)+buffer 科学化(100-400m tapered，人发帖溢出 boundary)
metadata: 
  node_type: memory
  type: project
  originSessionId: 7df3929a-b2fc-4538-b199-255debff9d54
---

模拟数据生成（任何新片区）走两方法论（07-17 确立，用户 co-design）：

**① Sim-0 资讯收集（通用 Phase 0，以后所有 sim 沿用）**：模拟前先 `web-search-prime`（智谱优先）采目标片区真实新闻/口碑 → 落 `DATA/sim/research/<area>.md` 资讯素材库 → 喂养 aspect 分类法 + 评论文本池 + policy_seed/project_seed 映射。落地 CLAUDE.md 数据模拟方法论「新闻报道」素材源——**从想象升级为实测采集**。每 aspect/种子须可回链真实资讯。

**② buffer 科学化（人发帖坐标必溢出 boundary 线）**：sim 范围**不限定在 boundary polygon 内**——人发帖带 GPS 抖动(~10-100m)+邻近性（对街/邻 block/停车/交通站）。boundary polygon 外扩 **100-400m（默认 200m）**，EPSG:4546 米制精确 buffer + **tapered 密度**（核心密→buffer 衰减，如 buffer 区密度=核心×0.4）+ **尊重相邻叙事区**（buffer ∩ 邻区做归属判定，避免双计/串味）。

**Why:** 纯想象数据失真（用户：让评论更真实）；不 buffer 则点呆板贴 boundary 线（街道是线状、人发帖必溢出）。资讯收集 + buffer 让模拟数据"像真的"。

**How to apply:**
- 新片区 sim 第一步：web-search 采真实资讯 → `DATA/sim/research/<area>.md`（事实+政策+口碑+来源链接），再设计 aspect/文本/种子。
- 空间生成必 buffer（100-400m，米制）+ tapered + 邻区归属判定。
- 范例：ermawu（大南门·二马路）sim——`SCRIPT/ermawu_l3l4_config.py`（10 ABSA aspect + policy/project 种子 + T 弧）+ `SCRIPT/sim_ermawu_l3l4.py`（**MOD_PERF.F_013**，standalone 不动城市 sim 引擎）→ 产 `DATA/processed/ermawu_l3l4_{T1-T3}`（独立集，ABSA aspect 级 + 政策→项目种子，策略异于 L1/L2 通用城市整体 polarity 弧）。ermawu 资讯库见 `DATA/sim/research/ermawu.md`（1877/2025-01-25 开街/修旧如旧最小干预不大规模拆除→直扣防止大拆大建 63 号/20 小区 44 栋/日均1.5万·五一10万+）。
- 资讯库是数据（非逻辑）；不替代 L1/L2 百度热力点底座（空间密度源）；仅采公开资讯无 PII。
- ermawu L4 种子供 [[emc-l4-lazy-enrichment]] deep_read_attribution 消费。
