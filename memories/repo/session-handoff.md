# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-06-29 晚（续）| 分支 `feature/kde-l2-3d` @ ce13da2（本批 push 后 = HEAD/origin 同步）

## 上一节点（06-29 晚续）—— 数据语义化重模拟 + 对称拉伸 + 4×5 归因（演示逻辑链纲领首落地）

**核心交付：把"演示逻辑链"提为项目全局纲领，并首次落地张力 + 可识别问题的数据底座**

1. **演示逻辑链 = 全局纲领**（最高优先级，写入根 `CLAUDE.md`「## 演示逻辑链」）：`张力图面 → 引导点击突出要素 → 交互分析 → 识别具体城建/更新问题`。两句哲学：**一切数据为演示表现力（数据可用性）；一切演示为应用场景有用性**。优先级高于编码规范；凡削弱表现力/脱离应用场景的"纯技术正确但无用"实现让位于此链。
2. **表现力环（张力）**：
   - `_grid_norm`(前端 grid-tool) / `_norm`(后端 terrain) **对称拉伸** `0.5+sign(pi)·min(1,|pi|/p95)·0.5`（p95=|polarity_index|95 分位）——替线性 `(pi+2)/4`（只到 terrain-9 中段=无张力根因）；**grid 前端与 terrain 后端必须同步同公式**，否则综合配色不一致。
   - `l1_confidence` **局部点密度自相关**（`generate_l1_mock._spatial_confidence`，dens_norm 分位）——amap POI `weight` 恒 1.0 无梯度（首版踩坑 conf 全 0.74+），改 dens_norm 后 0.42–0.97、heat(count×conf) 对比 ~50×。
3. **有用性环（识别问题）**：
   - **POI-anchored 4×5**：amap POI 已预映射 `domain`/`element`（0 缺失，4×5 多样铺开），`_seed_domain_element` 直接读 seed 字段做空间聚类。
   - **三层极性**（保叙事弧 `_check`）：arc 采样 + `POI_POLARITY_LEAN`(13 类高德类别→倾向) 18% 翻转叠纹理 + 对称拉伸放大。
   - **聚合层 4×5 归因（DEMO，L3/L4 接管后删表）**：`create_square_grid`/`create_terrain_mesh` 每格/环加 `domain_top`/`element_top`(众数)+`n_dom_*/n_elem_*`；`core/spatial_analysis.py` 的 `_ATTRIBUTION_RULES`+`lookup_attribution(dom,elm,sign(pi))` 查表生成 `issue_label`/`attribution`/`suggestion`（如 governance×facility×neg→"交通拥堵/设施陈旧"）。**归因字段在聚合产出层（非 L1/L2 per-point），清洗=后端不再生成**。
4. **旧数据备份**：`DATA/processed/` 旧模拟数据移入 `old-data/`（16 文件），新数据仍落 processed/。

## 当前状态
- 分支 `feature/kde-l2-3d` @ `ce13da2`，origin 同步（本批 push 完成）
- 后端 :8000（旧进程，**未加载本批新聚合/归因/拉伸代码**）+ 前端 :8080 在线
- 验证已过（业务函数层）：T1 pi=-0.13 / T3=0.47（叙事弧✓）、|pi|>1.2 约半数格（张力✓）、terrain `_norm` overall[0..1] 铺满、归因连贯（renewal×service neg→"老旧小区/物业"）；pytest 8 passed（2 h3 缺包 pre-existing 无关）

## 待验证（用户 F5 + 重启，未完成）
1. **后端重启**：双击 `start.bat`（serve.py 无 --reload，运行中进程是旧代码）→ 加载新聚合(domain_top/element_top)+归因+terrain `_norm` 拉伸
2. **真 HTTP POST 复核**（memory `verify-real-endpoint`）：重启后 `POST /api/v1/spatial/grid` 喂 T1 L2 → 格含 `polarity_index` 跨度 + `domain_top`/`issue_label` 非空 + `_grid_norm` 极值；`/spatial/terrain` 同测 `_norm` 跨度
3. **F5 肉眼**（CLAUDE.md：UI 配色不依赖识图）：导入 L2 T1/T3 → ①网格「综合」深红/深绿分明（不再中段蓝）；②L1 热度金黄高柱/暗红贴地对比；③地形红绿高地+平地落差；④grid 与 terrain 综合配色一致（同拉伸）

## 承重注意事项（踩坑，勿重复）
1. **演示逻辑链是北极星**（CLAUDE.md 最高优先级）：每个数据/功能决策对应链一环——张力=表现力、4×5 归因=有用性。memory `emotion-map-logic-chain`
2. **`_norm`/`_grid_norm` 对称拉伸须 grid+terrain 同步**（同公式 `0.5+sign(pi)·min(1,|pi|/p95)·0.5`），否则综合配色不一致。memory `symmetric-norm-stretch`
3. **l1_confidence 用局部密度 dens_norm**，不能用 POI weight（amap 恒 1.0）。memory `confidence-local-density`
4. **POI 已预映射 domain/element 直接读 seed**；勿用 `poi_4x5_map._L1_FALLBACK`（其 key 是百度类名，高德类名"餐饮服务"等不匹配会全 fallback）。`_L1_FALLBACK` 缺口待修。memory `grid-4x5-attribution`
5. **4×5 归因在聚合层**（DEMO 规则表 `_ATTRIBUTION_RULES`），L3/L4 LLM 归因上线后删表；字段 `issue_label`/`attribution`/`suggestion` 在格 properties 供 Task 2.7 popup
6. **三层极性保叙事弧**：arc 采样（保 `_check`）+ POI lean 18% 翻转（纹理）+ 拉伸（放大），勿硬继承 POI lean（会破弧）
7. terrain 渲染走 fill-extrusion，勿回退 deck.gl（GridLayer extruded 不渲染）。memory `terrain-mesh-rendering`
8. 高度控件 = `maxHeight` 绝对米（读 `_ui.maxHeight`）。memory `extrusion-height-maxheight`
9. 工具生成不弹 Overview（不 dispatch `layer:selected`）。memory `tool-no-auto-overview`
10. `generateGrid` 独占 vs `setViewMode` 配对 = 两独立场景，勿耦合。memory `generate-grid-exclusive-vs-viewmode`
11. 后端聚合数值列必须 `pd.to_numeric(coerce)`；验证须打真 POST 不只 health。memory `spatial-aggregation-numeric-coerce`
12. 后端无 `--reload`，改 `core/` 后须 start.bat 重启才生效

## 下一步（待用户在新会话定；候选，按优先级）
- **【建议优先】Task 2.7 网格/地形 popup + Overview**（演示链"交互→识别"桥，本周重点）：点网格/柱体/地形环 → popup+Overview 显示 `domain_top×element_top` + 极性 + 归因（`issue_label`/`attribution`/`suggestion`）+ 点数/分数/置信度。复用 `popup.js`/`panel.js` + 地形 hover 段落式样式。**数据底座已就位（本批），直接接字段**
- **修 `_L1_FALLBACK` 高德类名缺口**：补"餐饮服务/购物服务/风景名胜"等高德 13 类 key（小修，提升 map_baidu_to_4x5 健壮性）
- **Task 2.2 时间轴架构**：layer 增 `timeTag` + import.js 透传 time_label + 同 L 合并单卡 + timeline 组件
- **Task 3 热点图**：map.js `addHotpointLayer`(deck.gl ScreenGrid) 半成品 → 接入 heatmap-tool「总体情况」组第二卡

## 新会话 prompt（复制即用）
```
续 feature/kde-l2-3d @ ce13da2（昨晚数据语义化重模拟 + 对称拉伸 + 4×5 归因已 push，演示逻辑链已入 CLAUDE.md 全局纲领）。读 memories/repo/session-handoff.md（最新快照：3 项待 F5+重启 + 承重 12 条）。

本会话任务：<在此填，建议「Task 2.7 网格/地形 popup + Overview 接 4×5 归因」——演示链"交互→识别"桥，数据底座已就位>
要点：①点网格/柱体/地形环 → popup+Overview 显示 domain_top×element_top + 极性 + 归因(issue_label/attribution/suggestion) + 点数/分数/置信度；②复用 popup.js/panel.js + 地形 hover 段落式样式；③归因字段已在聚合 GeoJSON properties（create_square_grid/create_terrain_mesh 产出），前端直接读。

先确认后端已 start.bat 重启（加载新聚合/归因代码）。计费按调动次数，工作方式见 ~/.claude/CLAUDE.md（不派 subagent）。
```

## 承重 memory 索引（本会话新增 4 条）
- `emotion-map-logic-chain` — 演示逻辑链=全局纲领（张力→点击→分析→识别），已入 CLAUDE.md 最高优先级
- `symmetric-norm-stretch` — `_norm`/`_grid_norm` 对称拉伸是张力根因；grid+terrain 须同步
- `confidence-local-density` — l1_confidence 用局部密度 dens_norm（amap weight 恒1.0）
- `grid-4x5-attribution` — POI 已预映射 domain/element 直接读；4×5 归因在聚合层(DEMO,L3/L4 删)；三层极性保弧
