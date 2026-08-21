# PT-CB9 · RAG 重建实施计划（分工版 v1）

> **性质**：实施计划 v1（**待 claude组 评估回应后定稿 v1.1·未定稿前不动生产代码**）·2026-08-21
> **拟定**：zcode（glm组·主手）·应用户令「你们两个分工执行 RAG 重建」
> **上游依据**：Qoder《RAG全局审计与重构建议》（report·commit 8114d081）+ zcode 研判（`PT-CB8-RAG审计研判与裁决_zcode-2026-08-21.md`）
> **拍板基线**：用户 2026-08-21 下令转实施——研判 6 问按推荐答案视为已拍板（P0 先行/P2-P3 对调/C 线合并 PT-CB9/口径卡直入/重排序条件触发/rank_bm25+jieba 现在登记）。**任何一问与推荐不符请用户在开工前指正。**

---

## 一、目标与范围

**目标**：把知识库（RAG）从「工程素质优秀、检索 2023 基础款、内容薄且硬编码」升级为可支撑平台化（形态3「知识与范式层」承重墙）的状态——检索链路补 BM25 混合检索、内容资产大幅充实并让口径卡入库、评估进门禁可度量。

**明确不做（沿研判裁决·红线核对零冲突）**：不上框架/向量库/GraphRAG、不做 LLM 查询改写、不动冻结演示壳与 diagnose prompt、P2 重排序挂观察位（触发条件：泳道①+②落地后黄金集 Recall@5<95% 或精确名词类未全对 → 立项重启·优先 `sentence_transformers.CrossEncoder` 不新增 FlagEmbedding 包）。

## 二、阶段与泳道（总览）

```
P0 基线（zcode·先行独跑·0.5-1 天）
   ↓ 基线入档+门禁接线完成 = 泳道①②并行解锁
泳道① 内容（zcode 主·dsh 协力·2-3 天）
泳道② 检索（claude组·1-1.5 天·与①并行·白名单互斥）
   ↓ ①②各自验收全绿
泳道③ 工程（claude组·2-3 天：搬家+收编+X1/X2/X3/X5）
   ↓
收口批（zcode·0.5 天）：总验收+基线对比报告+台账/todo 收口+**接口锁验收（v1.1·核心报告 G4 条款）**：`rag_query` 工具名/核心返回字段（results/count/dim_counts/caliber）/`synthesize` 语义零破坏性变更断言；破坏性变更走版本化新工具名+旧名过渡
```

预估总量 6~8 个工作日（两组并行压缩日历时间至约 4~5 天）。

## 三、任务分解（可证伪验收）

### P0 基线（zcode）

| 任务 | 验收 |
|---|---|
| P0-1 黄金集 14→60 条（三类判据比例保持；新增精确名词类/口径类/体检域类各 ≥8；条目过术语纪律——来源可溯/禁自创分类） | `rag_gold_set.py` 60 条·每条 expect_kw/forbid_kw 有出处注记 |
| P0-2 基线实测入档 | `docs/rag-baseline.md`：Recall@5/分类型命中率/MRR（MRR 若扩 eval 则加）·含 office/家机双机数字 |
| P0-3 门禁接线：新建 `tests/test_rag_gate.py`（非 browser 目录·自动收集；断言从 GOLD_SET 动态算；`skipif` 索引/模型缺失打印重建指引） | `pytest tests/ -q` 收集到且本机过；无索引环境 skip 不红 |
| P0-4 既有 `tests/browser/test_rag_emc_e2e.py::test_rag_gold_set_regression` 断言动态化改薄壳复用同一逻辑 | 两处断言零漂移·手跑过 |
| P0-5 `requirements-rag.txt` 登记 `rank_bm25`+`jieba` 锁版（Ops 纪律·Py3.14 兼容注记） | pip 装得上·注记在档 |

### 泳道① 内容（zcode 主·dsh 协力）

| 任务 | 验收 |
|---|---|
| C-A 口径卡 12 张直入索引（含 X-01 作废卡带 `status: retired`·检索默认过滤显式问及可召回防错） | `rag_index.py` 新 loader + 黄金集新增口径类题目命中 K 卡；问答「口径引用义务」有了权威源可引 |
| C-B 图层说明书卡 57 层（manifest 投影：字段/粒度/usage/时效）+ 顺带 D 批挂账两项（K-C1 补 118/demo 点层 preset 注册·同文件免二次动） | 57 卡全部入索引；manifest 挂账项销号 |
| C-C 政策卡 11 张（01-01~01-11 已提炼件） | 入索引·来源指向 `_INDEX.md` 登记 |
| C-D 成文 md 39 份入库（**先过门禁**：geojson/csv 禁入、PII 扫描 `test_pii_guard`、X-01 作废数字加注、sim 标签禁入真实域） | +60~150 段（研判 E4 下修后口径）；入库前后黄金集刚性判据零退化 |
| C-E 体检域 fact 增量（对齐更新域量级·03-05~03-10 蒸馏笔记抽取） | 体检域 15→45+ 条；黄金集体检类新题命中 |

### 泳道② 检索（claude组·与①并行）

| 任务 | 验收 |
|---|---|
| R-1 BM25 路：jieba 分词建倒排（构建时生成·与向量同批原子写）+ `rank_bm25` Top-20 召回 | `bm25` 产物原子写；构建可增量（content_hash 跳过未变条目） |
| R-2 RRF 融合（k=60）+ fact×1.2 保留为配置常量+评估日志输出分类型命中率 | 黄金集 Recall@5 ≥ 基线+10pp；精确名词类全对；三类刚性判据零退化（含研判发现的「葛洲坝体检」题） |
| R-3 查询侧：bge 官方 instruction 前缀 + ~50 条领域同义词表（危旧房↔危房/12345↔市民诉求/葛洲坝片区↔葛洲坝…） | 前缀一行生效；同义词表有单测 |
| R-4 元数据预过滤参数 `search(query, k, domain/data_dim/city)`（可选·不传全库·向后兼容） | 三入口（前端/MCP/CLI）零改动全绿；**多入口逐入口验证（debug-memory R1）** |
| R-5 in/out 对账（静默丢数据禁令 R2）：过滤链每步可观测 | 日志含 in_n/out_n |

### 泳道③ 工程（claude组·①②完成后）

| 任务 | 验收 |
|---|---|
| E-1 `knowledge/` 目录+frontmatter 规范（域/城市/维度/年份/来源/状态/置信度）+导出器（Python 卡片→md·双轨过渡·Python 只读化） | 导出零丢失 diff 可核；`_infer_dim` 降级为兜底·声明为主 |
| E-2 `industry_kb` 收编（与 RAG 共享内容源·消灭口径分叉）——**保 `kb_facts` 插座行为兼容·触发铁律 11 契约三处同步**（tool_contracts/SKILL_DEFS/prompts） | kb_facts 回归零退化；契约三处同步检查过 |
| E-3 体验件 X1（来源+维度+年份+置信度四徽标透传·仅后端与 MCP·前端冻结不动）/X2（低置信降级走**既有**四态出口 gap 形态·禁造第五态）/X3（口径引用落地=MCP `guidance` 加一句·**不动前端 finalStep**）/X5（`--stats` 分域分状态分布） | 各件有测试；X4 不做（研判暂缓·问句侧维度推断误报风险） |

### 收口（zcode）

总验收：①门禁 `pytest tests/ -q` 零退化（442+2 基线随 PT-CB8 在途件浮动·以开工时点为准）②黄金集扩容后全绿+基线对比报告（前后 Recall@5/分类型命中率）③三入口逐入口冒烟 ④台账/todo/goal-status 知识库维度分数更新（30%→预估 65%+·按 CB-39 口径）。

## 四、白名单（互斥·防冲突）

| 批 | 文件 |
|---|---|
| P0（zcode） | `tools/rag_gold_set.py`、`tools/rag_eval.py`、新建 `tests/test_rag_gate.py`、`tests/browser/test_rag_emc_e2e.py`、`requirements-rag.txt`、新建 `docs/rag-baseline.md` |
| 泳道①（zcode/dsh） | `tools/rag_index.py`（loader 段·与②错峰）、`docs/urban-renewal-plan/`、`DATA/boundaries/presets/manifest.json` |
| 泳道②（claude组） | `tools/rag_index.py`（检索段·与①错峰协调）、`tools/mcp_server_emc.py`（可选参数透传）、`api/aiqa_routes.py` |
| 泳道③（claude组） | 新建 `knowledge/`、`ai_qa/outlet_kb/*`、`ai_qa/industry_kb/*`、`ai_qa/tool_contracts.py`（收编契约同步） |
| 冻结不动 | `frontend/`（演示壳）、`ai_qa/prompts.py` diagnose 段、`core/tracker.py`（新 track ID 按协议注册·编号连续不跳号） |

**协调点**：`tools/rag_index.py` 为①②共同战场——P0 期间由 zcode 打底（loader 接口定型），②开工时①的 loader 段已合入，claude组 只动检索函数段；冲突时 zcode 仲裁。

## 五、执行纪律（两组通用）

1. **commit 分权**：各自批次各自 commit（claude组 沿开发主惯例；zcode 沿 PT 惯例）·白名单互斥保零冲突；**每批 commit 前跑门禁零退化**。
2. **trace 纪律**：测试带 `EMOTION_TRACE_SESSION=PTCB9-<泳道>-<批号>`；报告附 trace 证据（RULES §1.2）。
3. **埋点义务**（报告漏提·研判补）：新增公开函数 `@track()` + `register_track_id` 连续占号（现至 MOD_AIQA.F_032）；关键分支 TrackContext；I/O 必埋。
4. **修复交付口径含「重启服务/重建索引」**（R7 旧进程旧码+索引 gitignore 每环境必建）。
5. **模型/依赖离线纪律**：一切模型 `local_files_only`·新依赖先 Ops 登记锁版·下载步骤写注记（25 分钟卡死坑）。
6. **验收 DoD**：Reviewer 审过+门禁过+基线对比过+文档同步（goal-status/台账）+用户验收（真实问题走一遍）。

## 六、风险与对策（沿报告 7.1+研判补充）

| 风险 | 对策 |
|---|---|
| ①②并行动同一 `rag_index.py` | 白名单分段+错峰+zcode 仲裁（§四协调点） |
| 内容入库污染召回 | 入库前门禁脚本（geojson/csv/PII/X-01/sim 五查）+入库后刚性判据回归 |
| 黄金集扩容引入争议条目 | 每条注出处·沿术语纪律；扩容后基线重测再动检索 |
| 换机索引缺失 | test_rag_gate skipif+指引；计划文档写明三步补链（pip/模型/build·KNOWLEDGE 已有） |
| PT-CB8 在途件（T7 批3/E1 挂起）插队 | P0 可在等待期插空；泳道开工以 PT-CB8 收口为前置（用户令如调整以令为准） |

## 七、定稿流程

claude组 回应（四档+补盲点）→ zcode 出 v1.1（分工定稿·吸收其修正）→ 报用户确认 → 开工。分歧项列「待用户裁决」不阻塞无争议部分（P0 无争议可先行的判断权归用户）。

---

> 维护：zcode。v1 待 claude组 回应；变更记录随 v1.1 追加。
