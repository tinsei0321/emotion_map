# PT-CB9 · 泳道② 检索升级派发单（Codex·第一优先·函数级）

> 主手：zcode。执行：Codex。分支 `EMC_harness_dsh`·commit 前缀 `PT-CB9(L2):`。**本地仓即最新·零 pull 零 push**（显式路径 commit·主手回收统一 push）。
> 依据：v1.2 终版判决（`PT-CB9-RAG重建计划v1.2-pre_zcode-2026-08-22.md` §六）+ 基线报告（`docs/rag-baseline.md`）。门禁基线 **508 passed + 4 skipped**（含 test_rag_gate 三断言·不许降）。
> 必读：基线报告 §二（失守模式解剖——你的处方依据）+ `docs/rag-loader-contract.md`（schema/签名/红线）。

## 铁则（沿 PT-CB11 八条+本批特则）

- **消融纪律（修-2）**：改动分 commit 逐层——`baseline→+BM25→+RRF 融合→+路由/cue`——每层跑 `py tools/rag_eval.py` 记分类增量（报告按**分类**呈现·禁只报总体）。
- 零新追踪 ID（rag_index.py 沿 grid_export 先例·纯工具不注册）；`_safe_print`·禁 emoji·A9。
- H3/D4 红线：`search()` 仍是 MCP rag_query 与 ai_qa 唯一共同真身——test_rag_gate 的 D4 断言必须全程绿。

## 件① BM25 字面匹配路（治「精确术语被身份卡顶位」·基线 10/10 miss 对症）

- `tools/rag_index.py` `search()` 增第二路：`rank_bm25.BM25Okapi`（jieba 分词·全 chunk 建一次·索引随 build 落盘 bm25 状态或运行时构建——小语料 364 段运行时构建 <1s·**选运行时构建**·零索引格式变更）。
- 查询侧同 jieba 切词；BM25 取 top `k*4` 候选。
- **RRF 融合**（rank_bm25 与稠密两路·`k=60` 常数·权重 spec 见 v1.1 补-A：起步等权·系数作观测参数记入 build meta 不拍死）。
- superseded 过滤（loader 契约：检索层滤·泳道①会填 status 字段——你按 `chunk.get('status','active')!='active'` 预置过滤即可·字段缺失=active 兼容）。

## 件② A2 路由契约（治「精确值走向量碰运气」）

- `tools/mcp_server_emc.py`：`rag_query` 与 `kb_facts` 的 docstring 增分工句——「精确名词/口径数字→优先 kb_facts（注册表直查）；叙述/方法/对比→rag_query」。
- `rag_query` 返回增结构化改道字段（窄面：命中口径类 chunk——type 适配或 source 指向口径注册表时）：
  `caliber_ref: {'kind': 'caliber_class', 'suggest': 'kb_facts', 'topic': '<命中主题>'}`；未命中口径类=省略字段（D1 定稿）。
- 返回统计可观测：`caliber_ref` 出现与否记 stderr 一行（A2 观察项·两周出现率≈0 则删）。

## 件③ H1 followup_cue（知识结构喂养宿主·D2 定稿四红线）

- 依 `docs/rag-loader-contract.md` §三：建三张小表（`ai_qa/rag_dims.json` 类·入 git）：
  ①dim→相邻 dim 映射（按业务·社区安全↔社区服务等·10-20 对起步）
  ②K 卡 topic→用户语言文案映射（「K-C1」→「社区数的统计口径」·禁裸编号）
  ③小节黑名单（修订/附录/索引）
- `rag_query` 返回增 `followup_cues`（2-3 条·价值序 维度相邻>口径关联>小节邻接·cue=疑问句方向零事实断言·目标库内真实存在才发·无 cue=**省略字段**）。

## 件④ H2 载荷四字段就位（D3）

- `rag_query` 返回确保含 `count`（已)有/`dim_counts`（已有）/`top_dim`（新增·dim_counts 最大者）/`elapsed_ms`（新增·检索耗时）——为壳阶段 ACP `tool.end` 事件备料·纯返回结构不改协议。

## DoD

- [ ] 消融各 commit 附 `py tools/rag_eval.py` 分类数字；**终态目标：总体 ≥95%（Q-B）且口径类 ≥87.5%（+10pp 下限·力争 90+）**；若 BM25+RRF 后仍 <95%·停手报主手（可能需 A1 前注启用判决）
- [ ] `python -m pytest tests/ -q` 全绿·test_rag_gate 三断言全程绿·快照零退化违例=0（改善 allowed：hit→miss 禁·miss→hit 放行——若大量改善·报主手重生成快照）
- [ ] 执行记录落盘 `PT-CB9-L2执行记录_Codex-2026-08-22.md`（含分类增量表+五判据不适用声明：本件为检索核心非 MCP 新工具）
- [ ] 显式路径 commit·零 pull 零 push

> zcode 主手 · 2026-08-22 · 泳道②派发（与泳道①并行·文件交集=零：①改 loader/数据侧·②改 search/契约侧——**rag_index.py 你只改 search 相关函数·loader 函数归泳道①**·冲突面已切分）
