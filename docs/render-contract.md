# EMC 出图契约（render contract · PT-CB7 T10 · 2026-08-21）

> 权威：本文是 dsh/任何外部 Agent 经 MCP 出图到 EMC 前端的**唯一范式依据**。
> 关联真身：`tools/mcp_server_emc.py`（render_spec/list_data）· `api/render_routes.py`（SSE+dataset 端点）· `frontend/js/render_client.js`（铺层客户端）· `frontend/js/toolbox/shared.js`（addToolboxLayer）· `frontend/js/tip-popup.js`（hover tip）。
> 红线：caliber/caliber_lite 结构零变化；usage=analysis_output 层禁作分析输入（身份卡同律）。

---

## 一 通道真相：render = Toolbox 同一渲染路径

外部 Agent 无需（也无法）"绕过 render 直调 Toolbox"——两条链在 `addToolboxLayer`（shared.js:188）汇合：

```
Toolbox 手动工具（六件）──► addToolboxLayer ──► map.js renderLayer ──► bindTipPopup（hover tip）
dsh render_spec ──SSE──► render_client.js ──► addToolboxLayer ──►（同上）
```

因此 **render_spec 铺出的层天然具备 hover tip、图例、图层管理等全部 Toolbox 交互**。
tip 内容取自 feature.properties——**tip 缺信息 = properties 缺字段，不是通道问题**。

## 二 hover tip 依赖的 properties 字段（契约）

| 字段 | 必需性 | tip 呈现 | 出处 |
|---|---|---|---|
| `name` | **必选** | 标题行（社区/单元/地点名） | tip-popup.js:441-446 |
| `point_count` | 推荐 | 量级（诉求量） | tip-popup.js:509 |
| `polarity_index` | 推荐 | 情绪判断行（正/负倾向+色） | tip-popup.js:422-423 |
| `domain_top` / `element_top` | 可选 | 领域/要素行（4×5 归因） | tip-popup.js:405 |

聚合产物（zonal_stats/grid 类）至少带 `name` + `point_count`；有极性数据时带 `polarity_index`。

## 三 出图档位（PT-CB15 K2 修订：分析结果走服务端直传·内联档收窄）

**分析结果出图正道（PT-CB15 起）**：分析工具（zonal_stats/rank/grid_aggregate/hotspot/area_stats/overlay）`layer_output=True` → 返回 `render_dataset_id`（几何服务端落盘 tmp_render + 自动登记临时 dataset·7 天 TTL）→ `render_spec(dataset_id=..., value_field=...)` 引用。
**几何不过模型上下文**——内联转录必抽稀（实测 2297 顶点手抄成 80·边界如随手画）。nearest_analysis 连线（≤40 顶点微几何）为内联例外。

| 档 | 适用 | 调用形态 | 上限/理由 |
|---|---|---|---|
| ⓪ 分析直传（首选） | 分析工具的出图（Top-N/聚合/叠置等） | `render_spec(dataset_id=<layer_output 返回的 render_dataset_id>)` | 几何零转录·边界 100% 保真 |
| ① inline | 模型自造小几何示意（非分析工具产物） | `render_spec(kind, name, geojson={...})` | 60 要素硬顶；带统计字段的面要素均顶点 <30 触发抽稀软警告（K4） |
| ② dataset_id | 已注册数据源（preset/点层） | `render_spec(kind, name, dataset_id='<id>')` | 前端经 `/api/v1/render/dataset/<id>` 自取数·无体量限制 |
| ③ 脚本+注册 | 全量/超限（如 193 社区全量、800m 方格全量） | 脚本调 core 聚合 → geojson 落 `DATA/Export/analysis/`（或 REGISTRY）→ manifest 注册 → 回到②档 | zonal_stats top_n≤20 / inline≤60 均不放宽——超限走本档 |

**边界默认指引（PT-CB15 K6·用户拍板）**：12345 社区级分析默认边界 = `base_community_area`（**193 含村·SQMC·现行权威**）；`checkup_cfg_community_xlwj`（130）= 西陵+伍家岗**历史调研范围**，显式点名才用；`checkup_cfg_community174`（174）= 去村统计口径。

**直入口（PT-CB7 T18）：「把某文件显示到地图上」= `render_file(file='<仓内路径>')` 一步到位**——服务端读取、自动判 kind、≤60 内联/>60 自动登记临时 dataset 并引用（同源复用·usage=analysis_output）。**零思考、零手工注册、不进 Range**。

**③档注册要求**（manifest.json 条目字段）：
- `id`：`checkup_`/`subj_` 前缀按轨道；`usage`：脚本聚合产物**默认 `analysis_output`**（结论层·防误作分析输入），确为原料才 `input`；
- `nameField`：tip 与列表用的名称字段；`note`：注明来源/口径/生成脚本；
- 社区口径数据必标 K-C1 枚举（174/154/118/130 等·注册表 `_口径注册表.md`）。
- 范例：`checkup_12345_comm174_all`（174 社区全量·gen_12345_fullcoverage.py 生成）。

## 四 scheme 受管词表（style.scheme）

| scheme | kind | 用途 | 数据要求 |
|---|---|---|---|
| `point_default_v1` | point | 点层（单色橙） | 点要素 |
| `community_choropleth_v1` | choropleth | 分级着色（计数 sequential / 极性 diverging） | 面要素 + `style.value_field`（默认 polarity_index；计数用 point_count） |
| `boundary_fill_v1` | choropleth | 范围/边界浅填充描边（非数据编码） | 面要素 |

未知 scheme 拒渲染（render_client.js 词表校验）。

**色带透传（PT-CB8 色板通道）**：计数分支支持 `style.ramp_hint` 指定色带——命中 `HEATMAP_RAMPS` 词表（如 `red-3`/`ylorrd`/`terrain-9`/`classify-7` 等，含多色系 viridis/magma/plasma/ylorrd/ylgnbu/bugn/rainbow）则用该色带（countStops 默认反转·低浅高深），无效或缺失回落默认 `grid-warm`。调用形态：`render_spec(..., value_field='point_count', ramp_hint='red-3')`。极性分支仍走 `polarityStops`（不受 ramp_hint 影响）。

## 五 caliber_lite 义务（每 spec 必带）

- `usage`：input / analysis_output（dataset 由注册表判定·inline 由调用方声明）；
- `data_nature`：real / demo / test（PT-CB14 C3：test = 测试 spec·前端徽标 [测试]·**清理纪律：测试投递用毕即删**——测试 spec 不得留在地图/渲染流中占位，验证完清除或覆写正式 spec）；
- `community`：社区口径（dataset 按注册表自动·inline 按 community_caliber 入参·K-C1 校验不符给 community_warning）；
- `note`：修正/口径说明。

## 六 常见坑（已踩·勿复踩）

1. **geojson 太大内联进 MCP**：调用即爆 payload——一律转③档（脚本落盘 + dataset_id 引用）。
2. **zonal_stats 要全量 174 行**：top_n 硬顶 20 是有意设计——全量走③档脚本聚合（与 zonal_stats 同源函数 `core.spatial_analysis.aggregate_by_polygons`）。
3. **tip 空白/缺名**：properties 没带 `name`（聚合时 polygon_name_col 未指定或源数据无名）。
4. **同会话重复出图叠层**：PT-CB7 T1 后 render_client 铺新层前自清全部 `[dsh]` 层——同会话仅存最新一张（多图并存需求回主手裁定）。
5. **结论层回灌**：usage=analysis_output 的 dataset 再作 zonal/buffer 输入会被 `_reject_analysis_output` 拒绝——这是红线不是 bug。
6. **「显示到地图」误入 Range**（PT-CB7 T18 实录）：用户说「显示/展示/放到地图上」= 立即 render_file 直接渲染（zoom_to 默认开·地图跟随）；**不是**注册成 preset/Range 条目等用户自己点——交互地图的跟随显示是 EMC 体验核心，把动作留给用户 = 理解错误。

## 七 结果呈现契约（行为义务·PT-CB7 T14）

> 面向对象：EMC 人设下的 agent（dsh/Codex 等外部宿主同适用）。与 §一~六（机制契约）配套：机制说「怎么出图」，本节说「何时必须出图」。

1. **凡工具可成图必出图**：分析类问题（聚合/排序/缓冲/分布）的答案凡有空间载体，必须经 render_spec/render_file 出图（按 §三 选档），不得只给文字/表格；纯知识问答（口径/背景）除外。**地图是答案的画布：问答通过地图的跟随显示才是交互体验的核心（EMC 初衷）。**
2. **图文并茂双交付**：图（render_spec）+ 文字结论同轮交付；文字结论必带口径对照段（口径卡 ID + 子集声明「本结果≠全量」+ 覆盖说明），与身份卡 T9 纪律同源。
3. **出图前提自查**：properties 必带 `name`（§二）；聚合时指定名称字段；无图可出时明说原因（无空间载体/数据缺口），不静默降级为纯文本。
4. **结论层只展示**：本轮产出的 analysis_output 图仅用于呈现，禁作后续分析输入（§六-5 同律）。
5. **交付闭环声明**：答案末尾注明已出的图层名（[dsh] 前缀）与打开方式，便于用户在地图核对。
7. **样式本地可调·数据变更才重投递**（PT-CB11 C3 升级·替代 PT-CB8 F4 的 v1 简化口径）：`[dsh]` 投递图层（render_spec/render_file）的配色是**受管语义色带**（HEATMAP_RAMPS 词表·normStops 归一化），且**归一化值随层内嵌**（`_count_norm`/`_grid_norm`）。因此**色带/反向/零值显隐/透明度/线样式=前端样式面板本地可调**（ms 级即时生效·图例自动跟随·图例色带条同为入口）；**换语义/数据/字段/归一化方式**才需改 render_spec 的 scheme/value_field 参数重新投递。设计原则：渲染契约权威样式（EMC×dsh 路线第 4 条「图层同源」·本地调整仅在受管词表内选色·不另造色值）。
8. **注入层图例/悬停/面板判定 = gridField 语义·非 _ui.tool 白名单**（PT-CB11 B3-3~B3-5）：注入层刻意不带 `_ui.tool` 标记（PT-CB8 F4 修复——防要素按钮误入 zonal 分析对话框），因此前端三处对「数据驱动 choropleth」的识别一律以 `paint.gridField` 存在为准（与 map.js 着色/线色 F4 判据同源）：①左侧色带图例（legend-grid）按 gridField 显示·标题取层名·标签订低/高；②悬停 tip-popup 按 gridField 绑定·指标行显 value_field 原始值·次行显要素 name（勿走 L2 极性兜底）；③参数面板对 gridField 层隐藏拾色器并提示「数据驱动着色·换色请重投递 spec」（本条 §七-7 的 UI 落地）。**禁回退到 _ui.tool 白名单判定**——那会让注入层全部漏判（灰框期症状：无图例/无 tip/误导性线框图例）。

## 八 待开发工具登记机制（PT-CB10 C2-9）

> 用途：消费方（dsh/外部宿主/脚本）遇到**无权威工具可承接的渲染/分析需求**时，不自造工具、不静默降级，而是登记待主手裁决。

**触发条件**：需要的能力既不在 MCP 插座面（list_data/rag_query/kb_facts/outlet_card/zonal_stats/buffer/rank/render_spec/render_file/emc_status）也不在 Toolbox 参数面板，且非一次性临时件。

**登记四要素**（落盘位置：本文件 §八 登记表·追加不删）：

| 要素 | 内容 |
|---|---|
| 工具名（候选） | 建议名称与语义（如 grid_aggregate） |
| 场景 | 触发该需求的真实任务描述（可追溯·防凭空立项） |
| 成本 | 预估实现/维护代价（接口面/测试面/契约同步三处义务） |
| 优先级 | P1（阻塞主线）/P2（体验改善）/P3（观察） |

**流程**：登记 → 主手定期裁决（立项/暂缓/否决+理由回填本表）→ 立项走正常 PT 批次（含铁律 11 契约三处同步义务）。

**登记表**：

| 工具名 | 场景 | 成本 | 优先级 | 裁决 |
|---|---|---|---|---|
| （暂无登记项） | — | — | — | — |

## 九 色板缺口登记机制（PT-CB10 C2-10）

> 用途：受管色带词表（HEATMAP_RAMPS/scheme 词表）不足以表达某场景语义时，登记缺口由主手裁决入词表——**禁调用方自带色值另搞一套**（§七-7 图层同源同源纪律）。

**触发条件**：`ramp_hint`/scheme 词表均无法表达所需语义（如新增双变量编码、特殊行业色规）。

**登记三要素**（落盘位置：本文件 §九 登记表·追加不删）：

| 要素 | 内容 |
|---|---|
| 场景 | 需要新色带的真实出图需求（数据语义/读者预期） |
| 期望 | 期望的色系/语义（sequential/diverging·低浅高深等）与参考 |
| 理由 | 现有词表为何不足（避免重复登记） |

**流程**：登记 → 主手裁决入受管词表（HEATMAP_RAMPS 单一权威源·state.js）或否决+理由回填 → 入词表后方可经 ramp_hint/scheme 消费。

**登记表**：

| 场景 | 期望 | 理由 | 裁决 |
|---|---|---|---|
| （暂无登记项） | — | — | — |



---

> Qoder · 2026-08-21 · PT-CB7 T10。修订须同步 `list_data()['render']` 段与 render_spec docstring 指引。
