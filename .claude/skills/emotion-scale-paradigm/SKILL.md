---
name: emotion-scale-paradigm
description: "情绪地图 AI 问答的尺度-方法-范式方法论：诊断问题尺度→选 GIS 工具→出匹配颗粒度的结论。用于设计/调 ai_qa prompt、扩范式、排查'答成坐标/答非所问'。单源真理在 ai_qa/paradigm.py，本 skill 是其人类可读镜像 + 决策树。"
---

# 情绪地图 · 尺度-方法-范式方法论

> 情绪地图 AI 问答的专业认知皇冠。核心命题：**分析的"尺度感"决定结论的"形态"——尺度错位 = 答非所问**。
> 单源真理 = `ai_qa/paradigm.py`（数据表）。本 skill 是其人类可读镜像 + 决策树，供开发维护演进。
> 运行时强制靠三处：① `prompts.build_diagnose_prompt`（教模型出诊断卡）② `build_agent_prompt` 拼接 GIS 目录（教模型选工具）③ `review.REVIEW_CHECKLIST.scale_paradigm_fit`（审查结论颗粒度是否匹配尺度）。

## 何时用本 skill

- 设计/调整 `ai_qa/` 任意 prompt（DIAGNOSE/AGENT/FINAL/REVIEW/REVISE）
- 扩展范式（加新尺度、新 domain 出口、新 GIS 工具）—— 改完同步 `paradigm.py` + 本 skill
- 排查"AI 答成坐标""答非所问""结论太泛/太碎"—— 多半是尺度-范式错位
- 给 demo 设计新问题样例、判断期望结论形态

---

## 表1 · 尺度-方法-范式矩阵（结论颗粒度硬约束）

| 尺度 | 地理对象 | 分析方法 | 结论范式（出口） | 禁止 | 典型问 |
|---|---|---|---|---|---|
| **宏观 macro** | 城区/片区/组团（10²–10³ km²） | 大尺度聚合（1000m 网格/行政区 zonal）+ 排序 + 类型化/结构化 | 体系化结论：哪类空间/哪些街道/哪类用地系统性落后或领先（结构判断） | **禁落单点/单网格**（用微观答宏观） | "中心城区整体如何？""哪个片区最需优先更新？" |
| **中观 meso** | 街道/社区/更新单元（1–50 km²） | 单元 zonal（边界 preset）+ 4×5 归因 + 单元间排序 | 单元级结论：哪个单元最差/最好 + 归因（domain×element）+ 单元针对性建议 | 不混到单点、不泛到整城 | "这几个街道里哪个最需更新？""某社区 4×5 偏哪格？" |
| **微观 micro** | 街/小区/公园/POI/网格（10⁻²–1 km²） | 50–100m 精细网格 + 热点聚集（Gi*）+ 落点 | 落点结论：哪个网格/聚集区/POI + 精确定位（可飞到地图） | **禁泛泛而谈**（用宏观答微观） | "这个公园里哪里最差？""这条街哪个点位被吐槽最多？" |

**判定要点**：提到"中心城区/片区/整体/哪个区/哪类"→宏观；"街道/社区/更新单元/几个对比"→中观；"这条街/这个小区/这个公园/哪个点位"→微观。"定义"类（如"什么是情绪地图"）scale 可填 macro 但 decision_type=定义，method 可空。

---

## 表2 · 4 领域 × 出口范式启发库（DIAGNOSE 选型参考，可扩）

- **城市规划**（urban_planning）：选址研判（设施缺口×情绪，中观）/ 15 分钟生活圈品质（中观单元）/ 用地类型情绪对比（宏观结构）
- **城市更新**（urban_renewal）：更新时序排序·优先级（中观，按更新单元）/ 微更新点位识别（微观，老旧小区 100m 网格）/ 片区更新系统性诊断（宏观结构）
- **城市运营**（urban_operation）：场馆商圈活动复盘（事件前后情绪对比）/ 舆情监测预警（负面聚集热点）/ 商圈业态口碑对比（中观）
- **城市治理**（urban_governance）：12345 投诉热点预警（负面聚集+关键词）/ 交通停车拥堵点排查（微观落点）/ 跨单元治理压力对比（中观排序）

> 演示 demo 对象 = 业内同行，数据略偏【规划/更新】（硬件），但保四域基本平衡。

---

## 表3 · GIS 操作目录（AI 自动选用 = Skill+Agent 层）

后端实现 `api/geo_routes.py`（复用 GeoPandas/Shapely，不造轮子）。前端暴露于 `frontend/js/ai_qa/tools.js`（POST `/api/v1/geo/*`）。复合入参范式：分析类 `layer+range+pre_filter` 一次完成，返 rows 属性表给 LLM（不灌全量 GeoJSON）。

| 工具 | 何时用 | 入参 | 产出 | 对结论范式的贡献 |
|---|---|---|---|---|
| `filter_attr` | 按属性筛选：用地/极性/domain/element/时点 | layer, field, op(eq\|in\|gt\|lt), value | 子集 | 聚焦切片，支撑类型化结论 |
| `clip` | 按几何裁剪（某区/某公园范围内） | layer, range(preset_id\|geojson) | 范围内子集 | 限定空间范围，支撑中/微观落点 |
| `merge` | 合并/dissolve（几街道→片区/同类用地合并） | layer, by(字段)\|all | 合并面域 | 上卷更大尺度，支撑宏观结构 |
| `area_stats` | 面积统计（各类用地占比/密度） | layer, group_by(字段) | 面积+占比+密度 | 从计数升级为强度/结构判断 |
| `zonal_stats` | **面域聚合**：按更新单元/街道/社区聚单元指标（宏/中观核心） | layer, boundary(preset_id\|geojson), metrics, top_n | 每单元极性/4×5 归因+排序 | 宏/中观结论主干 |
| `rank` | 排序：极性/domain/element 找 Top N | layer, by(polarity\|domain\|element), top_n, range | Top N 单元 | "最需优先…"明确排序 |
| `buffer` | 缓冲区（地铁 500m/奥体 1km） | layer, center(POI\|geojson), radius_m | 缓冲面域+范围内聚合 | 设施影响范围/选址 |
| `overlay` | 叠置（交/并/差/对称差） | layer_a, layer_b, how | 叠置结果面域 | 跨图层交叉（用地×更新） |
| `nearest` | 最近邻（离某 POI 最近的负面点） | layer, target, k | 邻近配对+距离 | 归因落点/POI 锚定 |
| `hotspot` | Gi* 热点（负面/正面聚集） | layer, value_col(score), invert | 每点 Gi* Z + hot/cold | 聚集识别，预警/排查 |

**组合范式例**：
- 宏观更新优先级 = `zonal_stats(更新单元) → rank(worst)`
- 商业用地负面集中单元 = `filter_attr(用地=商业) → area_stats(各单元) → zonal_stats(负面) → rank`
- 公园内最差点 = `clip(公园几何) → rank(50-100m 网格 worst)`

---

## DIAGNOSE 问题理解卡（6 字段，DIAGNOSE 阶段强制输出）

```json
{
  "domain_lens": ["urban_planning|urban_renewal|urban_operation|urban_governance"],
  "scale": "macro|meso|micro",
  "decision_type": "评价|选址|排查|对比|监测|定义",
  "outlet": "报告结论|指标排序|地图定位|建议清单|预警",
  "data_plan": { "needed": [], "available": [], "gap": [], "strategy": "ready|fallback_annotated|request_upload" },
  "method": ["从 GIS 工具目录选 + 组合"]
}
```

**data_plan.strategy 语义（数据自检 loop）**：
- `ready` — 数据齐全，直接作答
- `fallback_annotated` — 软缺口（有合理替代，如社区代街道、极性近似紧迫度），降级作答 + 结论显著标注口径与局限
- `request_upload` — 硬缺口（关键数据无替代，如更新紧迫度），输出"请求上传"卡，**该问不硬答**（harness 短路）

---

## 校验清单（调 prompt / 加范式后逐条过）

1. **宏观问禁落单点 / 微观问禁泛泛** — `scale_paradigm_fit` 审查项抓这个；不过 = revise。
2. **method 能从 GIS 目录选组合** — 不应让模型手算坐标；结构化/归因/排序结论必走 geo 工具。
3. **关键词能落回矩阵块** — 任何 TOPIC_TABLE 关键词须答得出"属哪个 domain×element、落哪些聚合域"。
4. **strategy 判定诚实** — 缺关键数据不假装全知；硬缺口请求上传、软缺口标注。
5. **改范式同步三处** — `paradigm.py`（数据）→ `prompts.build_diagnose_prompt`（运行时）→ 本 skill（镜像）。单源真理在 paradigm.py。
6. **承重** — REVIEW_CHECKLIST key 稳定（新增不删旧）/ revise 1 轮不递归 / diagnose 与审查失败均降级不阻塞 / MANIFESTO 花括号（参与 `.format()` 的 `*_TEMPLATE` 内 `{` `}` 转 `{{ }}`）。
