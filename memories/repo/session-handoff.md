# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月15日（5.99–5.104 全收工 + push）| 分支 `main`（**已 push 至 da4a687，与 origin 同步**）| 本次会话 = 5.99–5.104

---

## 当前节点：EMC 三层架构齐备 + 行业知识库 v1 落地，今日推进全部收工

### 背景
07-15 一日完成 6 步推进：**A1（Flash 解锁 single-path）→ A2（density 退场）→ A3①（范式树+select_template）→ 行业知识库 v1 + 项目顶层设计哲学 → B1（加 5 技能）→ 收尾（filter_attr + 知识库接入 diagnose）**。EMC **认知层 + 执行层 + 知识层**三层齐备且互通，Flash 模板命中率 **69%→95%（历史最高）**。所有改动已 commit + push。

### ✅ 本会话已做（5.99–5.104，每 commit 同步 todo/revision-log，已 push）
- **5.99 A1（`4e38ca2`）Flash 命中率 69%→85% PASS**：diagnose 加「必吐 JSON 不散文」铁律 + concept 映射 + 6 条 few-shot + DIAGNOSE_CARD_FIELDS 对齐契约。解锁 single-path 主导。
- **5.100 A2（`6a4e9b8`）后端 density 全退场**：删 `/geo/density` + `kde_raster`(F_005) + `_KDE_PROJECT_CRS` + kde 的 F_005/D_004 注册；**顺带修 F_005 重复注册 bug**（kde→恢复 buffer 唯一）。
- **5.101 A3①（`75e8910`）专业范式树**：B_TRACK_PARADIGM 9 原型（Load→Transform→Analyze）+ SCALE_PARADIGM method_templates 对齐住建部城市体检四层级 + select_template 单一真相源。Flash 85%→92%。
- **5.102 行业知识库 v1 + 项目设计哲学（`e8d1c93`）**：6 原则入 CLAUDE.md 顶层（4×5=归因矩阵非指标清单 + 政策→情绪→项目闭环 + 补盲区 + 知识库可成长 + 城市规划=设计全谱）；四领域权威源 `ai_qa/industry_kb/`（规划·设计/更新/运营/治理，宏观政策+项目聚焦+案例+情绪归因+4×5 多归属映射）。**业界调研汲取 GeoLLM-Engine**，CityGPT/MapLibre-demo 不采纳。
- **5.103 B1（`505dfc7`）加技能 9→14**：nearest/hotspot/area_stats/merge/extract_feature 登记 single → A3① B_TRACK 4 原型自动点亮。零白名单改。Flash 5 新技能 5/5 全命中。
- **5.104 收尾（`da4a687`）filter_attr + 知识库接入 diagnose**：filter_attr(B1.5) → B_TRACK 9 原型**全点亮**（B 赛道 single-path 100%）；industry_kb_brief_text() 注入 diagnose（Flash 用官方术语+项目类型）。Flash **18/19=95% 历史最高**。

### 🎯 下一步任务计划（详细，按优先级）

**Tier 0 · 验证（最优先，待用户）**
1. **C1 运行时验证（用户开 serve）**——今日积累（single-path 15 技能 / 范式树 / 知识库接入 / 官方术语 / Flash 95%）**真实效果一直没在 serve 验过**（全是静态 + Flash eval API 模拟）。开 serve（`start.bat` 或 `py frontend/serve.py 8080`）验各 track：
   - density 三模式（走 Toolbox）/ 只传 L1·T1 不跑 L2 / buffer 点 B 回填真半径 / 缺工具卡。
   - single-path 各技能直走（density/rank/buffer/clip/overlay/zonal + nearest/hotspot/area_stats/merge/extract_feature/filter_attr）。
   - 5.97 三修复（侧栏刷新/可见层/图例）+ diagnose 用官方术语（留改拆/接诉即办/一网统管/三区三线）。

**Tier 1 · 战略做厚（差异化·用户反复强调）**
2. **事件领域成体系化**（补官方盲区·EMC 差异化核心）——运营/治理 × 事件「瞬时活动→不同场所空间的要求与优化」专题。官方标准缺位、未来活动更频繁灵活（硬件定型、空间复合利用）。需先调研事件运营标准/案例 + 设计知识模块（industry_kb 事件专题或扩展）+ 归因框架（活动前后情绪对比/聚集/交通关联）。复用 density/hotspot/buffer 工具。
3. **知识库做厚**：四领域 PROJECT_TYPES/CASES 细化——完整社区设施清单 / 城市体检 76 指标 / 生命线 7 类设施（燃气/桥梁/隧道/供水/排水/热力/管廊）/ 接诉即办三率细则 / 街道设计导则细则。追加进各 `ai_qa/industry_kb/<domain>.py`。

**Tier 2 · 接入深化（承重 SOP）**
4. **industry_kb_text 按 domain_lens 动态注入**（harness 改·承重 SOP）：现 v1 注入全四领域 brief（静态）；动态版 = diagnose 出 domain_lens 后，后续 agent/final step 注入该领域**完整**权威语境（industry_kb_text，非 brief 全量）。涉 harness ctx.context 注入（承重），走完整 SOP。
5. **A3②③④**：② field_dictionary 接承重（上传层字段别名「情绪/得分/领域」列走聚合——现 aggregate 硬编码 polarity/domain/element 列名，改 resolve_field_alias，承重 SOP）；③ popularity role（timestamp/boundary_id/category→时间/边界/品类热度分析）；④ _missStats 遥测 + confidence 阈值 0.3。

### Push 状态
**已 push 至 `da4a687`（5.99–5.104 全部），本地与 origin/main 同步**。下会话从干净状态起。

### 承重（必守，下会话续改时留意）
- **项目顶层设计哲学**（CLAUDE.md「项目设计哲学」节，6 原则，全项目生效）：4×5=归因落点矩阵（非指标分类清单）+ 多归属 + 政策→情绪→项目闭环 + 补官方盲区 + 知识库可成长 + 城市规划=设计全谱。**勿用官方指标完备性质疑 4×5**（错标尺）。memory `project-design-philosophy`。
- **EMC 委托主 Toolbox 不自造**：density→generateHeatmap/Grid/TerrainForAI；新增分析能力优先扩 Toolbox 工具+程序化入口，勿自造并行 geo 端点。
- **数据可见纪律铁律**：EMC 只用 `getLayers().filter(visible)` 层（pickVisiblePointLayer/query_layers/buildContext 三处同源）；single 技能不硬默认 layer（5.95 已修）；registry 未显示层一律禁用。
- **run_python 收口**：harness gate 拦截，`ctx.allowCodeViz=true` 才放行。
- **主 Toolbox dialog 流不破**：generateHeatmap/Terrain/Grid 不动，仅 *ForAI 入口；generateGridForAI 签名不改；buffer 产物 _ui 透传。
- **三大件出图**（addResultLayer+paint固化+侧栏刷新）/ **5.74 对账**（_verifyClaims/_extractClaimedLayers/_registerToolboxLayer）/ **四态出口**（RESULT/GAP/CONCEPT/PARTIAL）/ **frame-based trust**——全不破。
- **前端 ESM 验证**：`node --check x.js` 对 ESM 假绿，改前端 JS 须 `.mjs` 副本（`cp x.js /tmp/x.mjs && node --check`）。
- **F_005**：现已唯一→buffer（5.100 修了 kde 重复注册）；kde_raster/density 端点已删。
- **字段语义层**：物理列名不改 / L2_* 五极色对齐 tokens(#78DC32 套)。
- **todo/revision-log 最新置顶铁律**：todo 按日段倒序、revision-log §5 顶「📍 最新动态」指针；**禁止底部追加**；每事同步。
- commit 只不 push（用户手动；本次用户明确 push 已执行）；专业词+通俗解释（用户初学者）；交付物中文。

### 本轮改的关键文件（下会话续改看这些）
- **认知层**：[ai_qa/paradigm.py](ai_qa/paradigm.py)（TEMPLATE_REGISTRY 15 技能 / B_TRACK_PARADIGM 9 原型 / SCALE_PARADIGM method_templates / select_template 真相源 / DOMAIN_OUTLETS framework）／ [ai_qa/prompts.py](ai_qa/prompts.py)（DIAGNOSE_TEMPLATE 铁律+few-shot / build_diagnose_prompt 注入 brief+范式树+决策树）。
- **知识层**：[ai_qa/industry_kb/](ai_qa/industry_kb/)（四领域模块 + __init__ brief/text/mapping）／ [docs/industry-knowledge-base.md](docs/industry-knowledge-base.md)。
- **执行层**：[frontend/js/ai_qa/stages.js](frontend/js/ai_qa/stages.js)（SKILL_DEFS 15 / validateParams / normalizeCard）／ [frontend/js/ai_qa/harness.js](frontend/js/ai_qa/harness.js)（runTemplatePath/路由/run_python gate）／ [frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js)（TOOLS 实装）。
- **测试**：[tests/eval_template_flash.py](tests/eval_template_flash.py)（19 case 手动评测）/ [tests/test_emc_template.py](tests/test_emc_template.py)（结构测）/ [tests/test_a3_paradigm.py](tests/test_a3_paradigm.py) / [tests/test_industry_kb.py](tests/test_industry_kb.py)。
- **纲领**：[CLAUDE.md](CLAUDE.md)（项目设计哲学节 + 4×5 标注）／ [docs/revision-log.md](docs/revision-log.md) §5（5.99–5.104）。

### 承重 memory 索引
- 本会话新增：`project-design-philosophy`（顶层 6 原则·最高优先·勿错标尺质疑 4×5）。
- 复用：`emc-delegates-to-toolbox` / `emc-tri-state-exit-contract` / `stand-on-giants-shoulders`（业界优先）/ `node-check-esm-unreliable`（.mjs 验）/ `commit-only-user-pushes`（用户 push；本次明确 push 已执行）/ `pro-term-plus-plain-meaning` / `maintain-revision-log` / `chinese-all-deliverables` / `no-handoff-on-routine-commit`（说"交接/收工"才覆写本卡）/ `landuse-codes-2023` / `verify-real-endpoint`（验真 POST 端点）。

---

## 新会话 prompt（复制即用）

```
继续 EMC。基线：07-15 已完成 A1→A2→A3①→行业知识库 v1+设计哲学→B1→收尾（filter_attr+知识库接入），
全部 commit+push（da4a687）。三层齐备（执行 15 技能 single-path / 认知 范式树+select_template /
知识 industry_kb 接入 diagnose），Flash 18/19=95% 历史最高。
下一步按优先级：① C1 运行时验证（用户开 serve，今日积累一直没验过）；② 事件领域成体系化（补官方盲区差异化）；
③ 知识库做厚；④ industry_kb_text 按 domain_lens 动态注入（harness 改·承重）；⑤ A3②③④。
承重：项目设计哲学 6 原则（4×5=归因矩阵非指标清单 + 政策→情绪→项目 + 补盲区 + 知识库可成长 +
城市规划=设计全谱，勿用官方指标完备性质疑 4×5）/ EMC 委托 Toolbox 不自造 / 数据可见纪律铁律 /
run_python 收口 / 三大件+5.74+四态+frame-based trust 不破 / node --check 假绿须 .mjs /
commit 只不 push / 专业词+通俗解释 / todo+revision-log 最新置顶同步。
先读交接卡 memories/repo/session-handoff.md + docs/revision-log.md §5（5.99–5.104），再动手。
```
