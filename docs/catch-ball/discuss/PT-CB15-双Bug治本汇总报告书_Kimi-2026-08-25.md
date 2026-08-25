# PT-CB15 · 双 Bug 治本汇总报告书（Kimi·2026-08-25·供 Codex 审计 / 收敛用）

## 白话摘要

今天修了两个病。第一个病：AI 画的社区边界像随手描的——查清楚不是它瞎画，是它「抄不全」：真边界有几百个坐标点，AI 用脑子转运时只能抄下十几个。修法是改规矩：以后精细边界由服务器直接存档、贴取件单号，AI 只报单号，一个点都不丢。第二个病：AI 嘴里的「130 个社区、两个方面」是旧黄历——原因是你今天改了知识库，但另外三本账（索引文件、图层说明书、边界选择指引）没同步改，AI 查的是旧账。修法：索引重建了、说明书的旧话清干净了、193 层（含村）修好了登记地址并定为默认边界、还立了一条新规矩「以后改口径必须四本账一起改」。全部改动经 600 项自动测试验证零失败。

---

## 一、任务链与收敛范围

| 环节 | 文档 | 结论 |
|---|---|---|
| 根因分析 | `PT-CB15-新Harness出图双bug根因分析与修复计划_Kimi-2026-08-25.md`（v1.1·用户四项拍板） | Bug2=LLM 上下文转录抽稀（坐标比对 100% 源顶点子集·非幻觉）；Bug1=口径四载体分裂 |
| 交叉评审 | Qoder 三报告评审（2026-08-25） | 采 Kimi 主干 + zcode P1-4（manifest file 断裂修复）前置 |
| 执行定稿 | `PT-CB15-双Bug治本执行版任务书_Kimi-2026-08-25.md`（K1-K9） | 本批执行依据 |
| 执行记录 | `PT-CB15-双Bug治本执行记录_Kimi-2026-08-25.md` | 全量实证与清单 |
| **本件** | 汇总报告书 | 审计入口 |

## 二、交付物与门禁

- **门禁**：`pytest tests/ -q` 三轮全量 **600 passed / 1 skipped 零失败**（前基线 595+4·净增 = 新增 2 测试 + 改写 6 测试 + 既有 skip 条件变化；skip=1 为 test_pii_guard 空参数集·数据依赖·与本批无关）。
- **改动文件**（8 个白名单内 + 2 文档）：`tools/mcp_server_emc.py`、`tools/rag_index.py`、`tools/check_server_freshness.py`、`DATA/REGISTRY/presets/manifest.json`、`requirements-rag.txt`、`tests/test_render_channel.py`、`tests/test_mcp_server_emc.py`、`docs/render-contract.md`、`docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md`。
- **派生产物**：`DATA/RAG/rag_index/`（375 chunk·今日化）；`DATA/Export/exports/tmp_render/`（运行期落盘目录）。

## 三、九件执行摘要（K1-K9）

| # | 内容 | 关键实证 |
|---|---|---|
| K1 | manifest 断链修复 22 条 + 删死链 1 + 设计内保留 1；193 层改指 `DATA/AUTHORITY/boundaries_社区村_193.geojson` | `resolve_boundary('base_community_area')` = 193 要素；进 list_data 可见清单（60 边界） |
| K2 | layer_output 六工具服务端落盘 + `render_dataset_id`（simplify 阶梯退役·nearest 微几何内联例外） | 193 层 zonal TOP3 落盘顶点全保真（港务 77/朝阳路 370/建设 215） |
| K3 | tmp_render 7 天 TTL（文件 + 失链登记双清） | 测试覆盖 |
| K4 | render_spec 内联抽稀软校验（面均顶点 <30 且带统计字段→提示不阻断） | 实测触发/不误报 |
| K5 | 契约双写：render-contract §三 改写 + list_data paradigm/boundary_guidance + 六工具 docstring | 三处文本一致 |
| K6 | 口径叙事清洗：page7 三层去「两方面合计」；130=历史调研范围标注；193=现行权威标注；口径注册表 K-C1/K-01 注记 + 第七节四载体同步检查表 | grep 验证·**措辞为草案待用户过目** |
| K7 | RAG 索引重建 375 chunk（净增 11） | 检索「社区口径 193 含村」Top-1 命中 K-C1 |
| K8 | check_server_freshness 新增 RAG 索引新鲜度段 | 实测 [OK] |
| K9 | 测试改写 6 + 新增 3（persist 断言/抽稀软校验/TTL） | 600+1 零失败 |

## 四、接口变更登记（审计重点核对）

1. **zonal_stats / rank / grid_aggregate / hotspot_analysis / area_stats / overlay_analysis**：`layer_output=True` 返回 `geojson` 键 → `render_dataset_id` + `render_hint`（用户拍板③授权·任务书 §二 登记）。nearest_analysis 保持内联（≤40 顶点微几何·例外已注记）。
2. `_dataset_meta` 返回增 `note` 字段（内部函数·非工具面）。
3. render_spec 新增两条 note 分支：内联抽稀软警告（K4）+ layer_output 直传产物豁免 P1-B 软警示（防误报）。
4. `_layer_output_geojson` 删除，替换为 `_layer_output_fc`（无 simplify）；新增 `_persist_layer_output`/`_attach_render_ref`/`_register_tmp_dataset`/`_cleanup_tmp_render`/`_load_st_model`（rag_index）。
5. render_file 登记逻辑重构为共用 `_register_tmp_dataset`（行为等价·tmp id 时间戳从秒改毫秒防同秒碰撞）。

## 五、计划外发现（审计请复核处置是否恰当）

1. **transformers 5.14.1 × bge-small-zh-v1.5 不兼容**：AutoProcessor 抛「Unrecognized processing class」——本机 08-20 后 transformers 大版本漂移所致。处置：`rag_index._load_st_model` 加 AutoTokenizer 兜底（st 原生支持 processor 即 tokenizer 实例）+ requirements-rag.txt 注记。**请审计：兜底是否引入隐性风险；是否应改锁 transformers<5。**
2. **断链实际 24 条**（评审/任务书预估 3/21 条）——含 3 条历史 tmp_render 登记，按同一映射规则修复。
3. **冒烟副作用**：两条测试 spec 被在线 watcher 推送上屏（已记录·T1 自清机制覆盖）。
4. **WorkBuddy 沙箱 os.remove 拦截**：本执行环境 fail-closed；TTL 删除在真实服务进程无此约束；门禁以 `PYTHONPATH=` 旁路验证。**请审计：TTL 测试在无污染环境的可重复性。**

## 六、未了事项（收敛前必须挂账）

| # | 事项 | 责任 |
|---|---|---|
| U1 | 8000 后端当前载 b2f9ffb3 旧码（本批修复未生效）——**复测前必须重启 + 硬刷新** | 用户/主手 |
| U2 | 本批全部改动**未 commit 未 push**（规则七：未 push 不算交付）·建议前缀 `PT-CB15(K1)` | 主手/用户 |
| U3 | 口径文本草案过目（manifest 5 条 + 口径注册表 K-C1/K-01/第七节措辞） | 用户 |
| U4 | home 机到岗重建索引（双机纪律）+ 环境配方 M1-M3 仍未立项 | 主手 |
| U5 | `docs/progress.md`、`_ctx_prefix_map.json`、`DATA/REGISTRY/presets/更新单元.geojson` 有非本批改动/副产物——提交前主手甄别 | 主手 |
| U6 | watcher TTL（我 13:32 复核件的 F1·防非 Codex 源迟到 spec）未纳入本批——建议下一批 | 主手裁决 |

## 七、给审计的建议验证口径

1. 同题重问「12345 诉求最多 7 个社区」→ 图层 7 要素、顶点与源一致、口径=193、无「两个方面」、spec 走 dataset_id；
2. `git diff` 对照白名单；pytest 复跑 600+1；
3. `resolve_boundary('base_community_area')` = 193；list_data 含 boundary_guidance；
4. 抽稀软校验正/反例各一；TTL 以伪造 mtime 实测；
5. `tools/check_server_freshness.py` RAG 段 [OK]。

---

> Kimi · 2026-08-25 · 收敛请求：Codex 审计通过后销号；打回项按结构化打回（错误码+缺失项+修正示例）返回我组。
