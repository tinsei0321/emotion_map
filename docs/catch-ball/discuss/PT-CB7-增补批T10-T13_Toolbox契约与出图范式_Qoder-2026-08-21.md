# PT-CB7 · 增补批 T10-T13 · 工具调用与出图契约整合计划（Qoder · 2026-08-21）

> 来源：用户等待期提交的测试问题两件（①工具调用与出图"需求契约"梳理重构；②dsh 地图渲染三问题）。本文 = 侦察结论（回答提问）+ 任务整合 + 拆解派发。
> 侦察基线：EMC_harness_dsh @ 5772047b；全部结论带 file:line 证据。

---

## 一 先回答三个问题（侦察实证）

### Q1：能不能用 Toolbox 封装工具直接出图（保留 hover tip 等 feature），而非通过 render？

**答：不需要绕路——render 通道就是 Toolbox 的渲染路径本身。** 证据链：

- Toolbox 六件（`frontend/js/toolbox/`：area-stats/hotspot/nearest/rank/vector/zonal）铺层全走 `addToolboxLayer`（shared.js:188）→ `renderLayer`（shared.js:211 调用 map.js）；
- render 通道的 `render_client.js` 铺层**同样**走 `addToolboxLayer`（render_client.js:5 import、各 scheme 分支调用）；
- hover tip 是渲染层统一基础设施：`map.js:651-652`（polygon 层）/ `map.js:1030`（point 层）对所有经 renderLayer 的层调 `bindTipPopup`（tip-popup.js:86）——**render_spec 铺的层天然带悬停 tip**，tip 内容取自 feature.properties（name/数值字段·tip-popup.js:391-446）。

**结论**：若某张 dsh 出的图缺 tip 信息，是 **properties 字段缺**（如聚合结果没带 name），不是通道选错。MCP G10 插座 = Toolbox 能力的可编程形态；render_spec 就是"出图的 Toolbox 封装"。真正的缺口是**这套范式没写成 dsh 可查的契约**（见 T10）。

### Q2：geojson 太大无法内联进 MCP 调用怎么办？

**答：用户当前的绕法（脚本直调 `mcp_server_emc.render_spec` 落收件箱·SSE 自动铺层）正确，但还差一步**——内联全量 fc 仍会把 spec 文件撑大。**正解 = dataset_id 引用范式**：geojson 落数据目录 → 注册 manifest → spec 只写 `dataset_id`（前端经 `/api/v1/render/dataset/<id>` 自取数·render_routes.py 已有端点）。这正是 174 全量已走通的路（见 Q3）。上限 60 要素是有意设计（MCP payload/上下文保护），不应放宽。

### Q3：174 全量的两个障碍（zonal_stats top_n≤20 / render_spec 内联≤60）

**答：已有现成解，且 dsh 自己已走通过一次**——证据：

- manifest 已注册 `checkup_12345_comm174_all`（`DATA/boundaries/presets/manifest.json`「12345 情绪聚合（174社区全量）」组）：`usage=analysis_output`，note 明记"dsh render 出图用·zonal_stats 同源聚合（aggregate_by_polygons）·带 point_count/score_mean/polarity_index"；
- 文件在盘：`DATA/boundaries/presets/12345_主观_社区174全量.geojson`（python 列目录实证）；
- 生成脚本已有沉淀：`SCRIPT/gen_12345_fullcoverage.py`（08-18）。

**标准范式（三档·本次固化为契约）**：

| 档 | 适用 | 路径 |
|---|---|---|
| ① inline | ≤60 要素的小结果 | render_spec(geojson=...) 直接内联 |
| ② dataset_id | 已注册数据源 | render_spec(dataset_id=...)·MCP 快查（zonal_stats top_n≤20 内） |
| ③ 脚本+注册 | 全量/超限（如 174 全量） | 脚本调 core 聚合 → geojson 落 presets → manifest 注册（usage/data_nature/K-C1 标注）→ render_spec(dataset_id=...) |

两个上限**不放宽**（LLM 上下文与 payload 保护）；③ 档把"注册 manifest"从手工 JSON 编辑变成有工具/脚本支撑的标准动作（T11）。

---

## 二 任务整合（PT-CB7 增补 T10-T13）

### T10 出图范式契约成文（复杂 · Qoder 自执）

- **内容**：① 三档出图范式写成契约文档（含 hover tip 机制说明/tip 依赖 properties 字段清单/usage 与 analysis_output 红线/K-C1 社区口径标注要求）；② `render_spec` MCP 描述追加范式指引一句（指向契约文档）；③ `list_data` 输出增「渲染能力」段（支持的 scheme 词表/三档范式速览）——让 dsh 可查。
- **白名单**：新建 `docs/render-contract.md` + `tools/mcp_server_emc.py`（仅 render_spec docstring 与 list_data 返回结构增段）+ `tests/test_mcp_server_emc.py`（+断言）。
- **红线**：caliber 零变化；不动 tool_contracts.py/prompts.py（render_spec 为 MCP 专用工具，实测不在 EMC 内部 FC 契约三处——无铁律 11 同步义务）。
- **验收**：pytest 全绿；`list_data()['render']` 段可查；契约文档覆盖三档+tip 字段清单。

### T11 register_dataset 注册工具（复杂 · Qoder 自执 · T10 之后）

- **内容**：MCP 新增第 9 插座 `register_dataset`——把"脚本产物 → 落 presets 目录 → manifest 注册（id/label/usage/data_nature/K-C1 校验）"标准动作工具化：入参（geojson 或 文件路径/id/label/usage/data_nature/community_caliber）→ 校验（FeatureCollection/字段/口径枚举）→ 写文件+写 manifest → 返回 dataset_id 供 render_spec 直接用。
- **白名单**：`tools/mcp_server_emc.py`（新函数+build_server 注册）+ `tests/test_mcp_server_emc.py`（+用例：注册/重复 id/usage 校验/K-C1 校验）+ 契约文档（T10 产出）补工具说明。
- **红线**：manifest 存量条目零改动（只增不改）；注册默认 `usage=analysis_output`（脚本产物=结论层·防误作分析输入·可显式覆盖）；A9 禁宽 except 静默。
- **验收**：注册 → `render_spec(dataset_id=新id)` 闭环可跑；重复注册幂等或显式拒绝；pytest 全绿。

### T12 渲染实证三连（简单 · 派 dsh）

- **内容**：① 浏览器铺 `render_spec(dataset_id='checkup_12345_comm174_all')` → hover tip 显示社区名+point_count（截图）；② 铺 800m 方格层 → tip 正常（截图）；③ 若 tip 缺字段，记录 properties 实际字段清单回报（供 T10 tip 字段清单校准）。
- **停止条件**：三项取证完即止，不做任何修复（发现问题回报 Qoder）。

### T13 174 全量脚本复现核验（简单 · 派 dsh）

- **内容**：`py SCRIPT/gen_12345_fullcoverage.py` 重跑 → 对账在盘文件数字（174 格/point_count 合计）一致与否；记录 wall-time；**不参数化**（参数化待本批复核后并入 T8 模板家族统一做）。

## 三 依赖与顺序

```
T12/T13（dsh·并行·可并入 dsh 批 1）──┐
T10（Qoder 自执）→ T11（Qoder 自执） ─┴→ T11 完成后派 dsh 用 register_dataset 复走 174 全量闭环（验证工具化路径）
```

优先级：T10 > T12=T13 > T11（T10 契约先行，T11 工具化随后；T12/T13 是零成本取证，即派）。

## 四 派发单（dsh 批 1 追加·与前发批 1 合并执行）

```text
【PT-CB7 · dsh 协助批 1 追加】（Qoder 主执行派发 · 2026-08-21）

纪律同批 1（dsh 环境内·EMC 仓零触碰·证据落盘同份记录文档）。

任务 D（T12 渲染实证三连·只取证不修复）：
① 8080 开 → 前端页面 → 经 render_spec(dataset_id='checkup_12345_comm174_all')
   出图 → hover 一格截图（tip 应含社区名+point_count）；
② 800m 方格层（已有 spec 或重新 dataset 出图）hover 截图；
③ 若 tip 缺信息：用 pwsh/python 列出该 geojson properties 实际字段清单回报。

任务 E（T13 复现核验·只核验不改）：
① py SCRIPT/gen_12345_fullcoverage.py 重跑；
② 对账 DATA/boundaries/presets/12345_主观_社区174全量.geojson 数字
   （格数/point_count 合计/极性字段在位）；
③ 记录 wall-time；不参数化、不改脚本。
```

## 五 与既有批次的关系

- 不动 PT-CB7 原 T1-T9 排期与验收锚（dsh 批 1 原三任务 + 本追加 D/E 合并一次跑）；
- T10/T11 为 EMC 仓新白名单（本文即授权依据·用户令"一并计入工作计划并整合进任务"）；
- 若主手认为 T11（新 MCP 插座）应独立 CB 轮立项而非 PT-CB7 内做 → 列「待主手裁决」，先只做 T10 契约成文。

---

> Qoder · 2026-08-21 · 侦察三问已答（render=Toolbox 同路径·三档范式成立·174 已有现成解）；T10-T13 待排执行。
