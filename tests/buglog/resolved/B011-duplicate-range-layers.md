---
id: B011
title: '飞轮测试每例重复加载行政区 — 图层堆叠'
type: BUG
severity: MED
priority: P1
status: resolved
module: 工具调用
source: 飞轮发现
cb: CB-09
rootcause: ''
case_ref: ''
repro_count: 1
last_repro: 2026-07-29
---

## 标准化用例

**问句**：（飞轮运行 25 例 llm 测试·每例调 loadRange('行政区')）

**数据前提**：飞轮 `?test=1` + llm 模式 + FC全链路

**预期行为**：
① 同一 GeoJSON 文件（行政区.geojson）只加载一次
② Layers 面板不出现多个同名「行政区」面层

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:---:|------|------|------|
| 1 | 07-29 | Layers 堆叠多个「行政区」面层·点开均为同一数据（中心城区范围） | e2e-seam.js loadRange 无去重检查·每例 addLayer 一次 |

## 修复记录

| 日期 | 操作 | commit |
|------|------|------|
| 2026-07-29 | loadRange 加同名+同 srcName 去重检查·已加载则跳过 | adef900 |
