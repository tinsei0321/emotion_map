# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月16日（④+⑤ 全收口：industry_kb 动态注入 + A3 字段角色系统完整化，2 commits 待 push）| 分支 `main`（本地领先 origin 2 commits，**待用户 push**）| 本次会话 = 5.108–5.112

---

## 当前节点：EMC ④+⑤ 全收口，下会话先插「工作策略优化」（用户指定）

### 背景
07-16 跨数轮一气做完 **④ industry_kb 按 domain_lens 动态注入 + ⑤ A3 字段角色系统完整化**（②alias 解析 / ④-confidence 阈值 / ③popularity 消费 / ④-_missStats+80% gate / ②遗留 score 别名化+confidence role 拆分）。④ 把 ②③ 厚化的权威细则接进回答层；⑤ 把 aggregate 系列的承重缺口（中文别名静默零、低置信 role 误导、热度维度未消费、Flash template 命中率无遥测/gate、score/l1_confidence role 混淆）全部修掉。**用户下会话要先插入一个「工作策略优化」（process/method，非 EMC 代码），完事后回 EMC browser 终验 + 低优先项**。2 commits 待 push。

### ✅ 本会话已做（5.108–5.112，每 commit 同步 todo/revision-log）

- **5.108 ④ industry_kb 按 domain_lens 动态注入（`3d0afe4`）**：②③ 厚化却运行时 0 消费的知识接进回答层。domain_lens 前端回传（ChatRequest 加字段 + harness/stages/api 透传）→ 后端按命中域渲染完整权威语境注入 agent/answer/revise/review 四 step；`industry_kb_text` 全量厚化（+KEY_TERMS 全表/METRICS_BASELINE/ELEMENT_HINTS/CASES），新公共 `industry_kb_lens_appendix`。**diagnose 一字不改保 eval 95%**。memory `emc-domain-lens-threading`。
- **5.109 ⑤②+⑤④-confidence 字段 role 承重加固（`71ecd70`）**：① aggregate 4 孤岛（aggregate_by_polygons/_attach_4x5_attrs/create_hex_grid/create_square_grid）接 `resolve_field_alias`——polarity/domain/element/topic 中文别名（情绪/领域/要素）走得通，**polarity_index 不再静默零**。② `validate_llm_roles`（所有 LLM role choke point）加 `LLM_ROLE_CONFIDENCE_FLOOR=0.3`，conf<0.3「纯猜」档 role=null 不承重。memory `emc-aggregate-column-alias-silent-zero`。
- **5.110 ⑤③ popularity 热度消费（`0262889`）**：新 `_attach_popularity_attrs` 共享 helper，aggregate/square_grid 消费 category（category_top 众数+category_count 多样性）+ timestamp（ts_count+ts_peak_hour 最热小时 datetime 解析），复用 ⑤② alias（类别/时间）。boundary_id 分组键暂不做（另一聚合模式）。
- **5.111 ⑤④-_missStats 遥测 + Flash 80% gate（`0754e93`）**：Flash template 命中率（'unknown'=miss）localStorage `ai_qa_template_stats_v1` 跨会话累积（clearChat 不重置）+ footer 显示；80% gate（self-protection：冷启动 samples<10 放行保零回归，成熟≥10 && <80% 退 while-loop）接入 runTemplatePath 激活。比原注释「冷启动→while-loop」更安全（不改冷启动行为）；要原语义翻 `_tplHitRateReady` 冷启动子句即可。
- **5.112 ⑤② 遗留 拆 confidence role + score 别名化（`5f91ed7`）**：修 design smell——`l1_confidence` 原归 `score` role（情绪得分混数据置信度）→ 拆独立 `confidence` role（36 roles）。import.js:631 `findKeyByRole('score')` 找 confidence（冲突源）→ 拆 scoreKey+confKey（demo 零回归，score-only 边界层改正 needsAnalysis）。aggregate/hex/square_grid 数值 mean 全 role 解析（得分/评分/置信度/情绪强度 别名），输出规范名；square_grid confidence→`l1_confidence_mean`（保 popup/state hotness 契约）。**⑤② 真收口**。

### 🎯 下一步任务计划

**Tier 0 · 下会话第一件（用户指定）**
1. **工作策略优化（process/method）**：用户要插入一个工作策略（how I work）的优化，**非 EMC 代码**。具体内容用户下会话给。优化确定后可能写成 feedback memory + 更新全局/项目 CLAUDE.md 工作方式。

**Tier 1 · 待用户（push + 验证）**
2. **push 2 commits**（`0754e93` 5.111 + `5f91ed7` 5.112）→ 本地与 origin 同步。
3. **browser 终验 ④⑤ 数据流**（eval 测不出这类，须实跑）：⑤④ gate/命中率（localStorage 累积 + footer 显示 + 冷启动零回归）；⑤② 中文别名 aggregate（得分/置信度/情绪强度→score_mean/l1_confidence_mean/emotion_intensity_mean）；④ 城市更新问答回答用权威术语（留改拆/完整社区/体检四层级）。
4. **Flash eval 复核②③**（`py tests/eval_template_flash.py`，需 DEEPSEEK_API_KEY，~19 调用）：验 ②③ brief 改动**未伤 95%**。④⑤ 不动 diagnose prompt → eval 不受其影响（C6：eval 空 context 测不出 ④⑤ 数据流改进）。
5. **A4/A6 browser 补验**（C1 遗留两项视觉交互，不阻塞）：A4=只载 L1·T1 点 terrain 验「不跑 L2」纪律；A6=buffer 产物层点 B 钮看面板回填 distance=500。

**Tier 2 · 低优先 EMC 收尾（可选）**
6. **⑤③ boundary_id 分组键**：点按 boundary_id 列直接分组（免 sjoin 上传面几何），需重构 polarity 3-level 路径的硬编码 `groupby('index_right')` 为通用 group key。substantive feature。
7. **⑤④ execSkips/lowConfField 分桶遥测**：runTemplatePath 执行 skip（missing-slot/tool-failed）+ 低置信 field role（validate_llm_roles low-conf null）计数，补全 _missStats 全貌。轻、frontend-only，但 80% gate 不用这些。

### Push 状态
**2 commits 待用户手动 push**：`0754e93`（5.111 ⑤④ _missStats/gate）+ `5f91ed7`（5.112 ⑤② score 别名化/confidence 拆 role）。（5.105–5.110 + handoff 已 push 至 `7f69a18`。）

### 承重（必守，下会话续改时留意）
- **项目顶层设计哲学**（CLAUDE.md「项目设计哲学」节，6 原则）：4×5=归因落点矩阵（非指标分类清单）+ 多归属 + 政策→情绪→项目闭环 + 补官方盲区 + 知识库可成长 + 城市规划=设计全谱。**勿用官方指标完备性质疑 4×5**（错标尺）。memory `project-design-philosophy`。
- **EMC 委托主 Toolbox 不自造**：density→generateHeatmap/Grid/TerrainForAI；归因复用 rank/hotspot/buffer/overlay。
- **数据可见纪律铁律**：EMC 只用 `getLayers().filter(visible)` 层（pickVisiblePointLayer/query_layers/buildContext 三处同源）；registry 未显示层一律禁用。
- **run_python 收口**：harness gate 拦截，`ctx.allowCodeViz=true` 才放行。
- **aggregate 列名 aliasing 静默零（⑤② 承重）**：加 aggregate stat 须 `resolve_field_alias` 读实际列 + 输出规范名，别硬编码字面列名。memory `emc-aggregate-column-alias-silent-zero`。
- **score ≠ confidence（5.112 新）**：两 role 已分离；square_grid confidence role 输出映射 `l1_confidence_mean`（popup/state 契约勿重命名）；import.js 用 scoreKey+confKey 分找。
- **FIELD_INFER confidence 阈值 0.3（⑤④）**：`validate_llm_roles` choke point，<0.3 role=null；前端 getFieldCard 信任后端输出。
- **Flash 80% gate（5.111 新）**：`_tplHitRateReady` cold-start 放行零回归 / 成熟<80% 退 while-loop；命中率 localStorage `ai_qa_template_stats_v1` 跨会话。
- **diagnose prompt 永不动**（保 Flash eval 95%）：④ 权威语境注入只在 post-diagnose step，diagnose 用 brief。memory `emc-domain-lens-threading`。
- **三大件出图 / 5.74 对账 / 四态出口 / frame-based trust**——全不破。
- **C6 洞见**：eval 空 context ≠ 运行时有层/有 domain_lens 路由；数据流改动（④⑤）eval 测不出，须 browser/probe 实跑验。memory `emc-eval-empty-context-vs-runtime`。
- **前端 ESM 验证**：`node --check x.js` 对 ESM 假绿，改前端 JS 须 `.mjs` 副本或 `--input-type=module`。
- **F_005**：唯一→buffer；kde_raster/density 端点已删。
- **todo/revision-log 最新置顶铁律**：todo 按日段倒序、revision-log §5 顶「📍 最新动态」指针；禁止底部追加。
- **commit 只不 push**（用户手动）；专业词+通俗解释（用户初学者）；交付物中文。

### 本轮改的关键文件（下会话续改看这些）
- **知识层（④）**：[ai_qa/industry_kb/__init__.py](ai_qa/industry_kb/__init__.py)（`industry_kb_text` 全量厚化 + `industry_kb_lens_appendix`）/ [ai_qa/prompts.py](ai_qa/prompts.py)（agent/final/revise 加 domain_lens 拼附录 + user_roles 加 'confidence'）/ [ai_qa/review.py](ai_qa/review.py) / [ai_qa/router.py](ai_qa/router.py) + [ai_qa/schemas.py](ai_qa/schemas.py)（ChatRequest.domain_lens）/ [frontend/js/ai_qa/](frontend/js/ai_qa/) harness.js（domain_lens 回传 + ⑤④ template 遥测/gate + getTemplateStats）+ stages.js + api.js + panel.js（footer 显命中率）。
- **字段层（⑤）**：[core/spatial_analysis.py](core/spatial_analysis.py)（4 孤岛 alias + `_attach_popularity_attrs` + score/ei/confidence 别名化）/ [core/field_dictionary.py](core/field_dictionary.py)（拆 confidence role + `validate_llm_roles` 0.3 阈值）+ [frontend/js/field_dictionary.js](frontend/js/field_dictionary.js) 镜像 / [frontend/js/import.js](frontend/js/import.js)（scoreKey/confKey 分离）。
- **测试**：[tests/test_industry_kb.py](tests/test_industry_kb.py)（20 测，④ 后全过）。
- **纲领**：[docs/revision-log.md](docs/revision-log.md) §5（5.108–5.112）/ [docs/todo.md](docs/todo.md) 07-16 日段。

### 承重 memory 索引
- ⑤ 会话新增：`emc-domain-lens-threading`（diagnose 卡字段结构化复用范式）/ `emc-aggregate-column-alias-silent-zero`（aggregate 别名静默零·加 stat 须 resolve_field_alias）。
- 复用：`project-design-philosophy` / `emc-eval-empty-context-vs-runtime` / `emc-delegates-to-toolbox` / `verify-real-endpoint` / `spatial-aggregation-numeric-coerce` / `node-check-esm-unreliable` / `commit-only-user-pushes` / `pro-term-plus-plain-meaning` / `maintain-revision-log` / `chinese-all-deliverables` / `no-handoff-on-routine-commit` / `landuse-codes-2023`。

---

## 新会话 prompt（复制即用）

```
先做一件工作策略优化（process/method，非 EMC 代码），再回 EMC。

【第一件·工作策略优化】（用户指定）
<把你要优化的工作策略写在这——比如：调度/沟通/验证节奏/commit 粒度/何时问 vs 直接做/某类改动的 SOP 等>
确定后写成 feedback memory（+ 更新 ~/.claude/CLAUDE.md 或项目 CLAUDE.md「工作方式」节）固化。

【然后·回 EMC】基线：07-16 已完成 ④industry_kb 动态注入(3d0afe4) + ⑤A3 字段角色系统全收口
（⑤②aggregate alias 71ecd70/5f91ed7 · ⑤④-confidence 0.3 阈值 71ecd70 · ⑤③popularity 0262889 ·
⑤④-_missStats+80%gate 0754e93 · ⑤②遗留 confidence 拆 role+score 别名化 5f91ed7）。2 commits 待 push
（0754e93/5f91ed7）。④ 把 ②③ 厚化权威细则接进回答层（diagnose 不动保 eval）；⑤ 修 aggregate 承重缺口
（中文别名静默零→resolve_field_alias；低置信 role→0.3 阈值；category/timestamp 热度消费；
Flash template 命中率遥测+80% self-protection gate；score≠confidence 拆 role 后全 alias 化）。
EMC 回归 32 pass（test_industry_kb 20 + test_a3_paradigm 12）。
回 EMC 后按优先级：① 用户 push 2 commits + Flash eval 复核②③（验未伤95%）+ browser 终验 ④⑤ 数据流
（eval测不出：⑤④ gate/命中率 + ⑤② 中文别名 aggregate 得分/置信度/情绪强度 + ④ 权威术语）；② A4/A6 browser 补验；
③ 低优先 ⑤③ boundary_id 分组键 / ⑤④ execSkips 分桶。
承重：项目设计哲学6原则（4×5=归因矩阵非指标清单，勿用官方指标完备性质疑）/ EMC 委托 Toolbox 不自造 /
数据可见纪律铁律 / run_python 收口 / aggregate 别名静默零（加 stat 须 resolve_field_alias 读实际列+输出规范名）/
score≠confidence（5.112 拆 role，square_grid confidence→l1_confidence_mean 保契约）/ FIELD_INFER confidence 0.3 choke point /
Flash 80% gate（cold-start 放行零回归/成熟<80% 退while-loop）/ diagnose prompt 永不动保eval /
三大件+5.74+四态+frame-based trust 不破 / C6(eval空context≠运行时，数据流改动靠browser/probe) /
node --check 假绿须.mjs / commit 只不 push / 专业词+通俗解释 / todo+revision-log 最新置顶同步。
先读交接卡 memories/repo/session-handoff.md + docs/revision-log.md §5（5.108–5.112），再动手。
```
