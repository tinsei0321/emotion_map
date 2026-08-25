# PT-CB15 · 双 Bug 治本执行版任务书（定稿·Kimi 执行·2026-08-25）

> **上游链**：Kimi 根因报告 v1.1（用户四项拍板）→ Qoder 三报告交叉评审（定谳：Kimi 主干 + zcode P1-4 前置 + 共有守卫项）→ 用户令「Kimi 定稿并执行」→ **本件=执行定稿**。
> **执行**：Kimi。**白名单**：`tools/mcp_server_emc.py`、`api/render_routes.py`（如需）、`DATA/REGISTRY/presets/manifest.json`、`docs/render-contract.md`、`docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md`、`tools/check_server_freshness.py`、`tests/test_render_channel.py`、`tests/test_mcp_server_emc.py`、本任务书与执行记录（discuss/）。RAG 索引重建（`DATA/RAG/`）为派生资产重建动作。
> **纪律**：门禁零退化；追踪 ID 不新增则不复核注册表；git 提交由主手/用户代执行（建议前缀 `PT-CB15(K1)`）；口径文本（manifest label/note）为草案，**用户过目后生效**。

## 白话摘要

这次修两件事。第一件：以后分析工具算出「哪几个社区」后，边界数据不再让 AI 用脑子抄一遍——改成工具直接把精细边界存进文件、贴个取件单号，AI 只把单号递给出图口，边界一个点都不会丢。第二件：把数据说明书里的旧话清理干净——「130 社区」标注为历史调研范围、默认改用 193（含村）；「两个方面合计」这种上一任务的结论从图层名字里退役；再重建一次知识索引，让今天的 DATA 整理真正被 AI 读到。另外顺手把登记表里 21 个搬家后没改地址的条目修好——包括 193 那层，它之前登记的是旧地址，AI 根本调不出来。

## 一、执行清单（顺序即依赖序）

| # | 动作 | 要点 | 验收 |
|---|---|---|---|
| K1 | **manifest 断链修复（P0 前置·采 zcode P1-4）** | 21 条可解析断链改指真实新位置（analysis→Export/analysis；12345主观→THEME/...；exchange→Export/exchange）；`base_community_area` 改指 `DATA/AUTHORITY/boundaries_社区村_193.geojson`（用户拍板权威源）；死链 `tmp_render_1787246545`（KDE 文件库内不存在）删除；`admin_community`（reference_only·94MB 不入 git）保持原样 | 修复后断链=1（仅 admin_community 设计内断链）；`resolve_boundary('base_community_area')` 实测 193 要素 |
| K2 | **R1-1 几何零转录** | `_layer_output_geojson` 六调用点（zonal_stats/rank/grid_aggregate/hotspot/area_stats/overlay）改服务端落盘 `DATA/Export/exports/tmp_render/<tool>-<ms>.geojson` + 复用 TMP_RENDER_GROUP 自动登记 → 返回 `render_dataset_id`+`render_hint`，不再回传 geojson；nearest_analysis 保持内联（≤40 顶点微几何·契约注明例外） | 六工具 layer_output=True 返回 dataset_id 且文件落盘、manifest 登记可 resolve |
| K3 | **R1-4 tmp_render TTL** | 落盘时顺带清理：tmp_render/ 超 7 天文件删除 + manifest 中 file 已失的 tmp_render_ 条目摘除 | 老文件/死条目实测被清 |
| K4 | **R1-2 内联抽稀软校验** | render_spec 内联面要素：平均外环顶点 <30 且 properties 含统计字段（point_count/polarity_index/value/score_mean）→ note 警告不阻断 | 投递 5 顶点面要素实测触发 note |
| K5 | **R1-3 契约双写** | render-contract §三改写（内联档收窄为模型自造小几何示意；分析结果出图=dataset_id 引用·nearest 微几何例外）+ list_data render.paradigm 段 + 六工具 docstring 同步 | 三处文本一致 |
| K6 | **R2-2/3/4 口径叙事清洗** | manifest：page7 三层 label/note 去「两方面合计」；130 层 note 标注「历史调研范围·12345 社区级分析默认边界=193 层」；list_data 增边界指引一句；_口径注册表补三口径标注（193=现行权威含村/130=历史调研范围/174=去村统计口径）+「两方面=上一任务结论·非数据特征」退役注记 + 四载体同步检查表（R2-5） | 文本落实·用户过目 |
| K7 | **R2-1 RAG 索引重建** | `py tools/rag_index.py --rebuild` | vectors.npy/meta.jsonl mtime 今日化；`--stats` 正常 |
| K8 | **R2-6 索引新鲜度进体检** | check_server_freshness.py 增 RAG 段：索引 mtime vs 知识源最新 mtime 比对告警 | 实测新旧两态输出正确 |
| K9 | **测试更新 + 门禁** | layer_output 断言 geojson→render_dataset_id（6 处测试改写·nearest 保持原断言）；新增三测：持久化落盘+登记、抽稀软校验触发、TTL 清理 | pytest 全量零退化（基线开工实测） |

## 二、接口变更声明（接口锁纪律）

- zonal_stats / rank / grid_aggregate / hotspot_analysis / area_stats / overlay_analysis 的 `layer_output=True` 返回结构：`geojson` 键 → `render_dataset_id` + `render_hint` 键。**非 rag_query 锁范围**；变更已随用户拍板（v1.1 拍板③）授权；本任务书即变更登记。
- render_spec / render_file / rag_query / 其余工具签名零变更。

## 三、完成定义（DoD）

- [ ] K1-K9 全做；门禁零退化；193 层 resolve 实测通过
- [ ] 执行记录落盘（含口径文本草案待用户过目标注 + 未 push 声明）
- [ ] R7 三态提醒写入执行记录（后端重启 + 页面硬刷新后复测）

> 定稿：Kimi · 2026-08-25 · 依据 Qoder 交叉评审 §四 最终建议全量吸收。
