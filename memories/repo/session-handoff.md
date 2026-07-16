# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月16日（④industry_kb 动态注入 + ⑤A3 字段角色系统收口 全做完，6 commits 待 push）| 分支 `main`（本地领先 origin 6 commits，**待用户 push**）| 本次会话 = 5.108–5.110

---

## 当前节点：EMC ④ 知识层深交付 + ⑤ A3 字段角色系统收工，⑤④-_missStats 承接下会话

### 背景
07-16 续会一气做完 **④ industry_kb 按 domain_lens 动态注入（harness 承重·深交付）+ ⑤ A3 字段角色系统（②alias 解析 / ④-confidence 阈值 / ③popularity 消费）**。④ 把 ②③ 厚化却运行时 0 消费的知识接进回答层；⑤ 修了 aggregate 系列的承重缺口（中文别名静默零/空 + 低置信 role 误导 + 热度维度未消费）。**⑤④-`_missStats` 遥测暂缓**——其消费方（Flash 80% gate）未实现，建空计数器=推测性基建，下会话配套做。6 commits 待用户 push。

### ✅ 本会话已做（5.108–5.110，每 commit 同步 todo/revision-log，**待 push**）

- **5.108 ④ industry_kb 按 domain_lens 动态注入（`3d0afe4`）**：②③ 厚化的权威细则原本运行时 0 消费（`industry_kb_text` 0 调用、ELEMENT_HINTS 无渲染路径），且 diagnose 的 `domain_lens` 前端被压扁成中文标签不回传后端。修：domain_lens 前端回传（ChatRequest 加字段 + harness/stages/api 透传）→ 后端按命中域渲染完整权威语境注入 agent/answer/revise/review 四 step；`industry_kb_text` 全量厚化（+KEY_TERMS 全表/METRICS_BASELINE/ELEMENT_HINTS/CASES），新公共 `industry_kb_lens_appendix`。**diagnose prompt 一字不改保 eval 95%**。test_industry_kb 20 pass。memory `emc-domain-lens-threading`。
- **5.109 ⑤②+⑤④-confidence 字段 role 承重加固（`71ecd70`）**：① **⑤② alias 解析**——[spatial_analysis.py](core/spatial_analysis.py) 4 孤岛（aggregate_by_polygons / _attach_4x5_attrs / create_hex_grid / create_square_grid）硬编码 polarity/domain/element/topic 英文列名 gate，中文别名（情绪/领域/要素）走不进 → polarity_index 静默零、domain_top 静默空（历史同类 bug 注释 :243）。接 `resolve_field_alias`（已存在·P1 已接 filter_attr 等 3 处，唯独 aggregate 系列漏），按 role 解析实际列去读、输出保规范名（polarity_index/domain_top）。② **⑤④-confidence 0.3 阈值**——[field_dictionary.py](core/field_dictionary.py) `validate_llm_roles`（所有 LLM role choke point）加 `LLM_ROLE_CONFIDENCE_FLOOR=0.3`，conf<0.3「纯猜」档 role=null 不承重。承重 smoke：中文别名 pi=0.8 非静默零 + 规范名零回归；confidence ≥0.3 保留/<0.3 null。memory `emc-aggregate-column-alias-silent-zero`。
- **5.110 ⑤③ popularity 热度消费（`0262889`）**：timestamp/boundary_id/category 三 role 早登记但 aggregate 未消费。用户择「消费现有 role·category 优先」（不加新 popularity role）。新 `_attach_popularity_attrs` 共享 helper：category→category_top(众数)+category_count(多样性)，timestamp→ts_count+ts_peak_hour(最热小时 datetime 解析)，复用 ⑤② alias（类别/时间 别名友好）。boundary_id 分组键暂不做（另一聚合模式）。承重 smoke：类别/时间别名 → category_top=购物/count=3 + ts_peak_hour=8；无列 graceful 跳过零回归。

### 🎯 下一步任务计划（按优先级）

**Tier 0 · 待用户（push + 验证）**
1. **push 6 commits**（5.105–5.110：82cbc8b/51a35ac/0407fae/3d0afe4/71ecd70/0262889）→ 本地与 origin 同步。
2. **Flash eval 复核②③**（`py tests/eval_template_flash.py`，需 DEEPSEEK_API_KEY，~19 调用）：验 ②③ brief/KEY_TERMS 改动**未伤 95%**。④⑤ 不动 diagnose prompt → eval 不受其影响（C6：eval 空 context 测不出 ④⑤ 的数据流改进，靠 browser/probe）。
3. **browser 实测（可选·验数据流）**：上传/构造中文别名列（情绪/领域/要素/类别/时间）的点层，zonal/grid 聚合验 polarity_index/domain_top/category_top/ts_peak_hour 真产出（eval 测不出这类）；④ 验城市更新问答回答用权威术语。
4. **A4/A6 browser 补验**（C1 遗留两项视觉交互，不阻塞）：A4=只载 L1·T1 点 terrain 验「不跑 L2」纪律；A6=buffer 产物层点 B 钮看面板回填 distance=500。

**Tier 1 · 承重（下会话正经做）**
5. **⑤④-`_missStats` 遥测 + Flash 80% gate（配套做）**：`_missStats` 全仓现不存在；语义挂点现成（stages.js:176 Flash gate template→unknown + harness.js:201/220/235 runTemplatePath skipped reasons + trace 骨架通 panel.js）。**消费方 = harness.js:354 注释提的 Flash 80% gate**（决定 runTemplatePath single 路径何时从渐进激活转主导）。本轮刻意不建空计数器——待 80% gate 设计时一并做（计数器→阈值判断→路由切换 + panel 显示）。另可顺带记 `validate_llm_roles` 的 low-confidence null 到 `_missStats.field_low_confidence`。

**Tier 2 · 后续**
6. ⑤② 遗留：score/emotion_intensity/l1_confidence 的 mean 仍硬编码（缺失=graceful degradation 非静默错值）；若要别名化须解「输出名契约」问题（得分_mean vs score_mean）。
7. ⑤③ 遗留：boundary_id 作面域分组键（非 sjoin 的另一聚合模式）；timestamp 更细时间分桶（现只 peak_hour）。

### Push 状态
**6 commits 待用户手动 push**：`82cbc8b`（5.105 C1+merge）/ `51a35ac`（5.106 ②事件）/ `0407fae`（5.107 ③做厚）/ `3d0afe4`（5.108 ④动态注入）/ `71ecd70`（5.109 ⑤②+⑤④-conf）/ `0262889`（5.110 ⑤③popularity）。本地领先 origin 6 commits。

### 承重（必守，下会话续改时留意）
- **项目顶层设计哲学**（CLAUDE.md「项目设计哲学」节，6 原则）：4×5=归因落点矩阵（非指标分类清单）+ 多归属 + 政策→情绪→项目闭环 + 补官方盲区 + 知识库可成长 + 城市规划=设计全谱。**勿用官方指标完备性质疑 4×5**（错标尺）。memory `project-design-philosophy`。
- **EMC 委托主 Toolbox 不自造**：density→generateHeatmap/Grid/TerrainForAI；归因复用 rank/hotspot/buffer/overlay。
- **数据可见纪律铁律**：EMC 只用 `getLayers().filter(visible)` 层（pickVisiblePointLayer/query_layers/buildContext 三处同源）；registry 未显示层一律禁用。
- **run_python 收口**：harness gate 拦截，`ctx.allowCodeViz=true` 才放行。
- **aggregate 列名 aliasing 静默零（⑤② 新承重）**：aggregate 系列硬编码列名 gate 遇中文别名静默跳过→polarity_index 静默零/domain_top 空。**加 aggregate stat 须 `resolve_field_alias` 读实际列 + 输出规范名**，别再硬编码字面列名。memory `emc-aggregate-column-alias-silent-zero`。
- **FIELD_INFER confidence 阈值 0.3（⑤④ 新）**：`validate_llm_roles` choke point，<0.3 role=null 不承重；前端 getFieldCard 信任后端输出。
- **diagnose prompt 永不动**（保 Flash eval 95%）：④ 的权威语境注入只在 post-diagnose step（agent/answer/revise/review），diagnose 用 brief 全 4 域速查。memory `emc-domain-lens-threading`。
- **三大件出图 / 5.74 对账 / 四态出口 / frame-based trust**——全不破。
- **C6 洞见**：eval 空 context ≠ 运行时有层/有 domain_lens 路由；数据流改动（④⑤）eval 测不出，须 browser/probe 实跑验。memory `emc-eval-empty-context-vs-runtime`。
- **前端 ESM 验证**：`node --check x.js` 对 ESM 假绿，改前端 JS 须 `.mjs` 副本或 `--input-type=module`。
- **F_005**：唯一→buffer；kde_raster/density 端点已删。
- **todo/revision-log 最新置顶铁律**：todo 按日段倒序、revision-log §5 顶「📍 最新动态」指针；禁止底部追加。
- **commit 只不 push**（用户手动）；专业词+通俗解释（用户初学者）；交付物中文。

### 本轮改的关键文件（下会话续改看这些）
- **知识层（④）**：[ai_qa/industry_kb/__init__.py](ai_qa/industry_kb/__init__.py)（`industry_kb_text` 全量厚化 + `industry_kb_lens_appendix`）/ [ai_qa/prompts.py](ai_qa/prompts.py)（agent/final/revise 加 domain_lens 拼附录）/ [ai_qa/review.py](ai_qa/review.py)（审查员注入）/ [ai_qa/router.py](ai_qa/router.py) + [ai_qa/schemas.py](ai_qa/schemas.py)（ChatRequest.domain_lens + 四 phase 透传）/ [frontend/js/ai_qa/](frontend/js/ai_qa/) harness.js+stages.js+api.js（domain_lens 回传）。
- **字段层（⑤）**：[core/spatial_analysis.py](core/spatial_analysis.py)（4 孤岛 alias + `_attach_popularity_attrs`）/ [core/field_dictionary.py](core/field_dictionary.py)（`validate_llm_roles` confidence 阈值）。
- **测试**：[tests/test_industry_kb.py](tests/test_industry_kb.py)（20 测，④ 后全过）。
- **纲领**：[docs/revision-log.md](docs/revision-log.md) §5（5.108–5.110）/ [docs/todo.md](docs/todo.md) 07-16 日段。

### 承重 memory 索引
- 本会话新增：`emc-domain-lens-threading`（diagnose 卡字段结构化复用范式·threading 别正则抠）/ `emc-aggregate-column-alias-silent-zero`（aggregate 别名静默零·加 stat 须 resolve_field_alias）。
- 复用：`project-design-philosophy`（4×5 矩阵非指标清单·勿错标尺）/ `emc-eval-empty-context-vs-runtime`（eval 空 context 不模拟层/卡字段）/ `emc-delegates-to-toolbox` / `verify-real-endpoint`（验真端点真数据流非模拟）/ `spatial-aggregation-numeric-coerce`（groupby mean 前 to_numeric）/ `node-check-esm-unreliable` / `commit-only-user-pushes` / `pro-term-plus-plain-meaning` / `maintain-revision-log` / `chinese-all-deliverables` / `no-handoff-on-routine-commit` / `landuse-codes-2023`。

---

## 新会话 prompt（复制即用）

```
继续 EMC。基线：07-16 已完成 ④industry_kb 按 domain_lens 动态注入(3d0afe4) → ⑤A3 字段角色系统
收口（⑤②aggregate alias 71ecd70 / ⑤④-confidence 0.3 阈值 71ecd70 / ⑤③popularity 消费 0262889），
6 commits 待 push。④ 把 ②③ 厚化的权威细则接进回答层（domain_lens 回传后端→注入 agent/answer/
revise/review，diagnose 不动保 eval）；⑤ 修 aggregate 承重缺口（中文别名静默零→resolve_field_alias；
低置信 role→0.3 阈值 null；category/timestamp 热度消费）。
下一步按优先级：① 用户 push 6 commits + Flash eval 复核②③（验未伤95%）+ browser 实测中文别名
数据流（eval测不出）；② ⑤④-_missStats 遥测 + Flash 80% gate 配套做（消费方=harness.js:354
runTemplatePath 激活，本轮刻意不建空计数器）；③ A4/A6 browser 补验。
承重：项目设计哲学6原则（4×5=归因矩阵非指标清单，勿用官方指标完备性质疑）/ EMC 委托 Toolbox 不自造 /
数据可见纪律铁律 / run_python 收口 / aggregate 别名静默零（加 stat 须 resolve_field_alias 读实际列+
输出规范名）/ FIELD_INFER confidence 0.3 choke point / diagnose prompt 永不动保eval /
三大件+5.74+四态+frame-based trust 不破 / C6(eval空context≠运行时，数据流改动靠browser/probe) /
node --check 假绿须.mjs / commit 只不 push / 专业词+通俗解释 / todo+revision-log 最新置顶同步。
先读交接卡 memories/repo/session-handoff.md + docs/revision-log.md §5（5.108–5.110），再动手。
⑤④-_missStats 是承重，动手前先探 80% gate 现状（runTemplatePath 渐进激活 harness.js:354）、出计划。
```
