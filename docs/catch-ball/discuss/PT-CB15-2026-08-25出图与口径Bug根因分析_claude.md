# PT-CB15 · 2026-08-25 出图与口径 Bug 根因分析（claude·仅分析不修复）

> 审计方式：只读探查（代码/索引 mtime/产物 spec 逐条核验）。未改任何文件。
> 用户实测场景：cdh（codex Harness·v4-flash）问「生成 7 个社区的范围」——回答口径异常（Bug1）+ 出图边界粗糙不重合（Bug2）。

---

## 一 Bug1：RAG 未吸收今天的 DATA 整理（口径错误）

### 现象
回答口径写「统计范围是西陵+伍家岗的 130 个社区边界」「数据为你上传的两类社区层 12345 点（安全韧性、民生基础）合计」——但用户上传的是 **193 社区**范围；且「两个方面」是上一任务的结论性内容，用户已明确数据分析时不再提。

### 根因链（三层·全部有证据）

**R1-1 · RAG 检索索引未重建（直接根因）**
- 检索用向量库 `DATA/RAG/rag_index/`（meta.jsonl + vectors.npy）mtime = **08-20 17:16**；`tools/rag_index.py` RAG_DIR = `DATA/RAG/rag_index`（索引 364 条·今天 0 条新增）。
- 今天（08-25）全部 DATA 整理（12345 迁 `DATA/THEME/theme_城市体检/`、geo_registry 路径更新、口径说明）**没有触发 `py tools/rag_index.py --rebuild`**——cdh 的 rag_query 检索到的仍是 08-20 素材（含旧口径）。

**R1-2 · 「完善」落点与检索链路脱节**
- 用户今天的「RAG 完善」落点 = `DATA/RAG/ai_qa/episodes.jsonl`（14:17 更新·L3 学习库·`api/aiqa_routes.py` L3=episode.py 写入路径）——**episodes 不在 rag_query 检索链路**（rag_index 数据源 = `docs/urban-renewal-plan/*.md`·见 `tools/rag_index.py:37` NOTES_DIR）。完善对象与检索对象是两个系统——完善了检索端读不到。

**R1-3 · 旧口径素材仍在检索源 + 未区分「知识 vs 用户输入」**
- 「130」在 `docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md:55`（西陵+伍家岗=130·历史口径锚点）；「两个方面」注册表 15 行仍在（08-13 定稿·今天 docs 素材零更新·`find -newermt 08-25` 无结果）。
- 实测 `rag_query('统计范围 130 社区 两个方面...')` 命中 `ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-*`（08-20 索引内旧知识卡）。
- **cdh 把 RAG 知识口径直接当成本次任务口径**——未声明「130=西陵+伍家岗历史口径·与你上传的 193 非同一对象」，用户上传数据未被当作权威输入。这是「口径混用」的模型行为面。

### 关联放大项（环境）
- **迁移半程**：`DATA/boundaries/presets/manifest.json` 已不在原路径（今天整理迁往 `DATA/_Retired/boundaries/` 等），但 `tools/mcp_server_emc.py` MANIFEST 常量等路径引用未同步——MCP 的 list_data presets 段与预设加载可能已处于「迁移中断」状态（部分口径/清单错乱的环境放大器）。此点属并行方迁移收尾范畴，报告仅记录。

---

## 二 Bug2：出图 7 个社区边界粗糙不重合

### 现象
结论图层生成 7 个社区面，但边界线粗糙（多边形顶点明显少于原社区面）·像「随手画」·与真实社区边界不重合。

### 前提修正（用户质疑·实测确认）
「工具面缺 GIS 提取能力」**不成立**——能力一直在：`zonal_stats/rank/grid_aggregate` 的 **`layer_output=True` 参数**（dsh 时代就有）返回「boundary 解析的源面精确几何 + 统计值」（`_layer_output_geojson`·仅体积 >200KB 才简化·小数据集原样输出）；dsh 时代「轻松做到」的实证（PT-CB14 停车 140 区投递）走的是**③档脚本路径**（预生成文件 `checkup_qty_停车泊位缺口_140点.geojson` → render_file 投递）。**断点不在工具，在通道与引导。**

### 根因链（三通道断点·产物 spec 逐条核验）

**R2-1 · cdh 手绘内联 GeoJSON 出图（直接表现·产物证据）**
- 最新 applied spec（`DATA/Export/exports/render_inbox/applied/1787638661446-8079.json`·用户实测产物）：
  - `kind: choropleth`·**`dataset_id: None`**·**inline feats: 7**·geometry: Polygon·**坐标点集仅 18 个**/面
- 对比真实社区面（体检对象_社区_面·193 含村）——真实边界数十至数百顶点，18 点远低于真实 → **LLM 凭位置记忆手绘的简化形**。历史同模式：`1787634299060-2226.json`（20 feats·10 点）——非偶发。

**R2-2 · 主断点：cdh 引导/契约未传「精确几何提取方法论」**
- PT-CB15 C2（EMC 人设迁移：dsh persona → AGENTS.md 常驻段）**转正批未落地**；现 `_codex_cwd/AGENTS.md` 为应急简化版——只规定「唯一工具面=emc MCP·必出图」·**未写「出图 = zonal_stats/rank(layer_output=True) 取精确面 → render_spec」的方法论**。
- dsh persona（emc-test profile 提示词）含完整工具用法指引（含 layer_output 通道）；**迁移到 cdh 时细节丢失**——v4-flash 拿到工具 schema（layer_output 参数有 JSON 描述）但未与「精确边界」关联 → 退化手画。

**R2-3 · 通道断：沙箱封死脚本③档（dsh 时代「轻松做到」的主通道）**
- cdh 的 app-server：`sandbox=read-only` + AGENTS.md 第 4 条「禁 commandExecution/bash/python」→ **「脚本全量生成 geojson 文件 → render_file 投递」通道断**（render-contract §三 ③档）。
- dsh 时代该通道通畅（dsh headless 自带执行环境·140 区面即脚本/规则产物）。

**R2-4 · 真实子缺口：按名称任意子集无 MCP 入口**
- 用户点名「这 7 个社区」的场景：MCP 工具无按名称过滤参数（zonal_stats/rank 全量聚合后 top_n 截断·无 pre_filter）——dsh 时代靠脚本③档实现；cdh 时代该入口断（R2-3）→ 唯剩手画。
- （top7 最差/最好场景可由 rank(layer_output=True) 覆盖·通道在·引导缺。）

---

## 三 修复计划书（按优先级·本次不执行）

### Bug1 修复（RAG 吸收 + 口径纪律）

| # | 动作 | 落点 | 说明 |
|---|---|---|---|
| P1-1 | **重建 RAG 索引**：`py tools/rag_index.py --rebuild`（先确认今天口径素材已落 `docs/urban-renewal-plan/`） | tools/rag_index.py | 让检索端吸收今天整理（新口径/新数据说明） |
| P1-2 | **权威口径文档落 docs**：新增/更新口径说明（数据分析不提「两个方面」·130=西陵+伍家岗历史口径·193=用户上传含村社区·各口径适用场景） | docs/urban-renewal-plan/（_口径注册表 或新文档） | 重建索引的素材前提；且从源头消除「两个方面」被检索 |
| P2-1 | **cdh 口径纪律**：AGENTS.md 引导补「回答口径须声明知识来源 + 用户上传数据优先于知识库口径；RAG 知识口径≠本次任务输入」 | `D:\Github\_codex_cwd\AGENTS.md`（仓外·模板化后入 `docs/emc-codex-persona.md`） | 治模型行为面（R1-3） |
| P2-2 | **catalog 标签与数据源对齐**：subj_12345 点层 label/说明随 theme 迁移更新（安全韧性/民生基础 = 12345 政务热线数据·非「用户上传」模糊表述） | core/geo_registry.py | 防 catalog 误导口径 |
| P2-3 | **迁移收尾对齐**：MANIFEST 等路径常量同步迁移后新路径（与并行方迁移对齐后执行·避免冲突） | tools/mcp_server_emc.py 等 | 环境放大项 |

### Bug2 修复（精确出图·修正版）

| # | 动作 | 落点 | 说明 |
|---|---|---|---|
| P1-1 | **AGENTS.md 出图方法论补全（治 R2-2 主断点·最高优先）**：补「出图两条精确通道」——①topN/最差最好场景：`zonal_stats/rank(layer_output=True)` 取精确面 → render_spec；②已生成文件：`render_file` 投递（③档）。明示「禁止手绘多边形」。模板入 `docs/emc-codex-persona.md`（收敛稿条件 2 同源） | `_codex_cwd/AGENTS.md`（模板同步 docs） | 治 R2-1/R2-2 模型行为（零代码·立刻可验） |
| P1-2 | **评估恢复脚本③档通道（治 R2-3）**：cdh sandbox 由 read-only 放宽（如 workspace-write 限定 `_codex_cwd` 或白名单命令）——恢复「脚本生成精确 geojson → render_file」；**需安全评估 + 用户裁决**（改沙箱=改攻击面·与「cwd 仓外隔离」防线联动权衡） | codex_bridge.py spawn 参数 + 引导 | 恢复 dsh 时代主通道 |
| P1-3 | **新增 MCP 工具 `select_boundary_subset`（治 R2-4 真子缺口）**：入参 boundary preset id + 名称列表 → 精确子集面 geojson（EPSG:4326·原几何）——用户点名社区场景的正道 | tools/mcp_server_emc.py + 登记 SKILL 面 | 补按名子集入口（dsh 时代靠脚本·cdh 时代缺） |
| P2-1 | **render_spec 内联几何质量守卫**：choropleth 内联 Polygon 顶点数下限（如 ≥20/面）或面积合理性校验——超低顶点告警/语义化拒绝（防手画静默上线） | tools/mcp_server_emc.py render_spec | 兜底防线 |
| P2-2 | **spec 来源可追溯**：render_spec 产出带「几何来源」（tool-extracted / script-file / LLM-inline）注记 | render spec schema + render_client 徽标 | 展示层可见·验收口径可判 |

### 验收建议
- Bug1：rebuild 后 `rag_query('两个方面')` 不再命中旧口径文档；实测问题重问口径正确（193 社区·不提前任结论）。
- Bug2：同问题重问 → spec 要素几何来自 `select_boundary_subset`（dataset_id 或精确内联·顶点数与源面一致·边界重合）。

---

## 四 证据清单（本次探查实测）

| 证据 | 值 |
|---|---|
| rag_index mtime | `DATA/RAG/rag_index/` 08-20 17:16（meta 364 条·今天 0 新增） |
| rag_index 数据源 | `docs/urban-renewal-plan/*.md`（tools/rag_index.py:37）·今天该目录 0 更新 |
| 完善落点 | `DATA/RAG/ai_qa/episodes.jsonl` 08-25 14:17（L3 学习库·非检索链路） |
| 旧口径锚点 | `_口径注册表.md:55`（130=西陵+伍家岗）·`:15`（两个方面·08-13 定稿） |
| rag_query 实测 | 命中 `outlet_kb/urban_renewal_knowledge.py#URP-*`（旧知识卡） |
| Bug2 产物 | `applied/1787638661446-8079.json`·dataset_id=None·inline 7 feats·18 顶点/面 |
| 同模式历史 | `1787634299060-2226.json`·inline 20 feats·10 顶点/面 |
| 迁移半程 | `DATA/boundaries/presets/manifest.json` 原路径不存在（迁 `DATA/_Retired/boundaries/`） |
