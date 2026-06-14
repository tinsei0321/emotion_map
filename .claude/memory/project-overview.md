---
name: project-overview
description: 情绪地图项目总览 — 架构、技术栈、工作流、关键规范
metadata:
  type: project
---

# 情绪地图 (Emotion Map) 项目总览

**目标**：基于多源社交数据（大众点评/美团/小红书/微博/12345）的城市情绪空间分析平台。

## 技术栈
- **前端/UI**：Streamlit (端口 8501)，`?page=` 路由
- **后端分析**：Python 3.10+，SnowNLP 情感分析，四级数据管道 (L0~L4)
- **空间引擎**：Folium 底图 + Shapely 空间分析 + 天地图瓦片
- **数据采集**：Scrapy 多源爬虫
- **跨机协作**：Git 同步代码 + memories/repo/session-handoff.md 交接

## 架构（七层）
1. **数据层** `data/` — L0 原始 → L4 分析结果 (csv/geojson)
2. **采集层** `SCRAPER/` — Scrapy 多源爬取
3. **基础设施层** `core/` — config / data_loader / export / tracker
4. **分析引擎层** `SCRIPT/` — L1 治理 → L2 SnowNLP → L3 LLM → L4 归因
5. **空间引擎层** `core/` — 底图/热力图/空间分析
6. **UI 组件层** `core/` — Streamlit 可复用组件
7. **应用层** `apps/` — Streamlit 主应用

## 核心文件
- `apps/app_main.py` — Streamlit 主应用 + 所有子页面路由
- `SCRIPT/emotion_analysis_v1.py` — 核心分析引擎
- `SCRIPT/run_analysis.py` — CLI + Tkinter 桌面入口
- `core/config.py` — 全局配置（天地图Key、阈值、颜色映射）
- `core/tracker.py` — 决策追踪系统
- `launch.py` — 一键启动

## 编码铁律
1. 禁用 emoji → ASCII 标记 `[OK]` `[WARN]` `[LOAD]` `[ERR]`
2. 所有 `print()` 必须通过 `_safe_print()` 调用（Windows GBK 兼容）
3. 禁止劫持 `builtins.print`
4. Streamlit 统一端口 8501，子页面 `?page=` 路由
5. 所有入口调用同一个 `run_analysis_task()`
6. 导出命名：`{name}_{L1|L2|L3|L4}_result_csv.csv`
7. 分析结果禁止包含用户名/用户ID
8. 空间范围优先于关键词过滤
9. 每个公开函数必须 `@track()`，关键分支必须 `TrackContext`
10. 所有追踪 ID 必须在 `core/tracker.py` 注册表登记

## 多 Agent 协作
- 11 个专业 Agent 定义在 `.github/agents/`
- PM 驱动 SOP 流程：PM → Developer/Designer → Reviewer/Design Reviewer → Tester → Docs → 验收
- 跨机协作：`@pm 同步上下文` 恢复 → `@pm 下班交接` 保存

**Why:** 初始化项目 Claude Code 配置时需要了解完整项目上下文。
**How to apply:** 每次在此项目工作时，参考本文件理解架构和约束。与 [[agent-workflow]] [[coding-rules]] 配合使用。
