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

## 三 三档出图范式（按结果体量选档）

| 档 | 适用 | 调用形态 | 上限/理由 |
|---|---|---|---|
| ① inline | ≤60 要素小结果（Top-N 层等） | `render_spec(kind, name, geojson={...})` | 60 要素硬顶（MCP payload/上下文保护·不放宽） |
| ② dataset_id | 已注册数据源（preset/点层） | `render_spec(kind, name, dataset_id='<id>')` | 前端经 `/api/v1/render/dataset/<id>` 自取数·无体量限制 |
| ③ 脚本+注册 | 全量/超限（如 174 社区全量、800m 方格全量） | 脚本调 core 聚合 → geojson 落 `DATA/boundaries/presets/`（或 analysis 目录）→ manifest 注册 → 回到②档 | zonal_stats top_n≤20 / inline≤60 均不放宽——超限走本档 |

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

## 五 caliber_lite 义务（每 spec 必带）

- `usage`：input / analysis_output（dataset 由注册表判定·inline 由调用方声明）；
- `data_nature`：real / demo；
- `community`：社区口径（dataset 按注册表自动·inline 按 community_caliber 入参·K-C1 校验不符给 community_warning）；
- `note`：修正/口径说明。

## 六 常见坑（已踩·勿复踩）

1. **geojson 太大内联进 MCP**：调用即爆 payload——一律转③档（脚本落盘 + dataset_id 引用）。
2. **zonal_stats 要全量 174 行**：top_n 硬顶 20 是有意设计——全量走③档脚本聚合（与 zonal_stats 同源函数 `core.spatial_analysis.aggregate_by_polygons`）。
3. **tip 空白/缺名**：properties 没带 `name`（聚合时 polygon_name_col 未指定或源数据无名）。
4. **同会话重复出图叠层**：PT-CB7 T1 后 render_client 铺新层前自清全部 `[dsh]` 层——同会话仅存最新一张（多图并存需求回主手裁定）。
5. **结论层回灌**：usage=analysis_output 的 dataset 再作 zonal/buffer 输入会被 `_reject_analysis_output` 拒绝——这是红线不是 bug。

---

> Qoder · 2026-08-21 · PT-CB7 T10。修订须同步 `list_data()['render']` 段与 render_spec docstring 指引。
