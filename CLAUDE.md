# 情绪地图 (Emotion Map) — 项目级 CLAUDE.md

> 最后更新: 2026-06-15 | Agent v2.0 | Skill 包 464

## 项目定位

基于多源社交数据（大众点评/美团/小红书/微博/12345）的城市情绪空间分析平台。让城市规划者能"看见"市民情绪的空间分布。

## 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 语言 | Python | 3.14.5 |
| 前端 | Streamlit | 1.58.0 (端口 8501) |
| 情感分析 | SnowNLP | — |
| 分词 | jieba | — |
| 地图 | Folium + 天地图瓦片 | — |
| 空间分析 | Shapely + pyproj (EPSG:4546) | — |
| 数据采集 | Scrapy | 2.16 |
| LLM 分类 | DeepSeek API (deepseek-chat) | — |
| 包管理 | pip + requirements.txt | — |

### 坐标系（宜昌专项）

本项目处理两类数据源，坐标转换模块需灵活处理：

| 数据源 | 典型 CRS | 转换路径 |
|--------|----------|----------|
| 社交媒体原文 | GCJ-02（火星坐标） | GCJ-02 → WGS84 → CGCS2000 |
| 规划矢量数据 | CGCS2000 投影（EPSG:4546, CM 111E） | CGCS2000 → WGS84（地图渲染） |
| 地图底图渲染 | **WGS84 EPSG:4326**（统一基准） | — |

- 宜昌标准投影：CGCS2000 3-degree Gauss-Kruger **CM 111E (EPSG:4546)**
- 备用投影：EPSG:4547 (CM 114E)、4548 (CM 117E) — 省内其他城市
- 模块支持自定义 EPSG 输入，不硬编码单一投影

## 目录结构

```
emotion_map/
├── apps/           # Streamlit 应用层（app_main.py + 子页面）
├── core/           # 基础设施层（config/loader/export/tracker/map/UI）
├── SCRIPT/         # 分析引擎层（L0→L1→L2→L3→L4 管道）
├── SCRAPER/        # 数据采集层（Scrapy spiders）
├── DATA/           # 数据层（raw/ + processed/ + boundaries/）
├── design/         # 设计令牌系统（tokens.json + CSS）
├── docs/           # 文档体系（prd/spec/architecture/decisions/todo/dev-notes）
├── .claude/        # Claude Code Harness（agents/skills/memory/settings/commands/hooks）
└── memories/repo/  # 跨机会话交接卡
```

## 四层数据管道

```
L0(原始采集) → L1(治理:坐标+相关+脱敏) → L2(SnowNLP情绪) → L3(LLM语义) → L4(归因)
```

- L0→L1: `SCRIPT/data_governance.py`（需 DEEPSEEK_API_KEY）
- L1→L2: `SCRIPT/emotion_analysis_v1.py` → `run_analysis_task()`
- 所有入口（CLI/Tkinter/Streamlit）共用 `run_analysis_task()`
- 导出命名: `{name}_{L1|L2|L3|L4}_result_csv.csv`

## 编码铁律（10 条，不可违反）

1. **禁用 emoji** → ASCII 标记 `[OK]` `[WARN]` `[LOAD]` `[ERR]`
2. **安全打印** → 所有 `print()` 通过 `_safe_print()` 调用
3. **禁止劫持 builtins.print**
4. **入口统一** → Streamlit 端口 8501，子页面 `?page=` 路由
5. **分析逻辑共用** → 所有入口调用同一个 `run_analysis_task()`
6. **导出命名规范** → `{name}_{L1|L2|L3|L4}_result_csv.csv`
7. **数据脱敏** → 输出禁止包含用户名/用户ID
8. **空间范围优先** → 范围 Polygon 为第一过滤条件
9. **决策追踪必埋点** → 每个公开函数 `@track()`，关键分支 `TrackContext`
10. **追踪 ID 必注册** → 所有 ID 在 `core/tracker.py` 注册表登记

## 决策追踪系统

- 基础设施: `core/tracker.py`（`@track()` / `TrackContext` / `trace_*()`）
- 模块 ID 分配: 见 `AGENTS.md` 模块 ID 分配表
- Bug 定位: [TRACE] 日志 → 决策 ID → 代码跳转（O(1)）

## Agent 协作（v2.0，8 Agent + 自动编排）

Claude Code 主线程 = PM，自动 spawn Agent 走 SOP。详见 `AGENTS.md`。

## 禁止事项

- 不要修改 `DATA/raw/` 原始数据文件
- 不要在未走 SOP 的情况下修改核心管道代码（`data_governance.py` / `emotion_analysis_v1.py`）
- 不要修改 `core/tracker.py` 的追踪 ID 注册表格式
- 不要增加新的 Python 依赖而不更新 `requirements.txt`
- 不要使用 emoji 在任何代码文件中
- 不要直接 commit 到 main（应走 feature branch，紧急修复除外）

## 详细文档索引

| 文档 | 路径 | 内容 |
|------|------|------|
| 产品需求 | `docs/prd.md` | 用户画像、功能优先级、验收标准 |
| 产品规范 | `docs/spec.md` | 字段定义、UI 规格、性能预算 |
| 架构设计 | `docs/architecture.md` | 系统架构说明 |
| 架构规范 | `docs/architecture-pattern.md` | 七层架构、路由、代码组织 |
| 决策记录 | `docs/decisions.md` | 10 个 ADR |
| 开发日志 | `docs/todo.md` | 每日任务 + 踩坑记录 |
| Agent 规范 | `AGENTS.md` | Agent 协作、SOP、DoD |
| 会话交接 | `memories/repo/session-handoff.md` | 跨机协作 |

## 模块级 CLAUDE.md

子目录的 `CLAUDE.md` 包含模块专属约定，优先级 **高于** 本文件：
- `SCRIPT/CLAUDE.md` — 数据管道编码规范
- `core/CLAUDE.md` — 基础设施层规范
- `apps/CLAUDE.md` — Streamlit 应用层规范
