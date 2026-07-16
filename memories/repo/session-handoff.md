# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月16日（**阶段一 工作策略园丁层 + 阶段二 EMC compare 技能** 全 done，2 commits 本次会话末 push）| 分支 `main`（本地领先 origin 2 commits）| 本次会话 = 5.113 + 5.114

---

## 当前节点：阶段一（process/method 园丁层）+ 阶段二（EMC compare 技能）全 done，待 browser 终验

### 背景
用户先要「工作策略优化（process/method，非 EMC 代码）」——参考 OpenAI《Harness Engineering》强化 vibe coding 工作架构 + 系统全局 Plan + 六要素评估。诊断：**项目已有 7 套连贯机制=上下文树（高度对齐「地图非说明书 + 渐进式披露」），缺的是「园丁层」（只长不烂）+ 3 裂缝（两套记忆树/巨型文件/manifest 过期）**。做完阶段一后用户实测发现 EMC 欢迎胶囊"对比西陵伍家岗"仍犯三老毛病（代码块/回答一半/方法不做），选「彻底：加 compare 技能」做阶段二。两阶段全 commit 待 push。

### ✅ 本会话已做（5.113 + 5.114，每 commit 同步 todo/revision-log）

- **5.113 工作策略·上下文连贯园丁层（`400c4a3`）**：
  - `/garden` 命令（按需除草：过期 memory/巨型文件/漂移 manifest/僵尸注释，**产清单不自动改**）+ `on_session_start.py` 阈值提醒（memory>50 或 revision-log>500KB 打印一行，零 LLM 开销）。
  - PreCompact hook（`on_precompact.py` → `memories/repo/.wip.md`，git/trace 锚点，gitignore）+ settings.json 注册。
  - 僵尸记忆树归档：`.claude/memory/` 10 文件 → `_archived/`（git mv）；项目根 `MEMORY.md` + `apps/CLAUDE.md` 重定向到用户全局树（单一权威源）。
  - 全局 `~/.claude/CLAUDE.md` 加「Harness 工作方式·上下文连贯四纪律」+ feedback memory `context-coherence-discipline`。
  - manifest 刷新：CLAUDE.md「13 模块 55+」→「18 模块 510+」+ rule 12 智谱栈全局托管说明；AGENTS.md 模块表加 5.x 主力备注（ai_qa/field_dictionary/spatial_analysis 待正式 MOD_）。
  - 新 `docs/context-map.md`（一页可见上下文树）+ `docs/harness-engineering-baseline.md`（六要素详表，防 memory 膨胀）。
- **5.114 EMC·区域对比 compare 技能 + _driftRe 拓宽（`8f82ebb`）**：治欢迎胶囊"对比"三老毛病（代码块/回答一半/方法不做）。
  - 根因：`_driftRe`（harness.js:516）只拦 action-JSON 代码块→非 action 代码块泄漏；F3 完整性门仅 gis_operation→emotion_analysis 半截；TEMPLATE_REGISTRY 无 compare 技能→叙述拒绝。
  - compare 三件套（复用 zonal_stats 不造 geo 端点，守红线）：`paradigm.py`（TEMPLATE_REGISTRY 加 compare + select_template C 路由 decision_type=对比→compare 优先于 rank/zonal + 决策树文本）+ `tools.js`（`compare_regions`：boundaries≤4 区逐区 geoFetch('zonal_stats')，并排 observation）+ `stages.js`（SKILL_DEFS 镜像 + normalizeParams regions/areas→boundaries）。
  - `_driftRe` 拓宽：草稿任意 ``` 围栏→`_reviseOnce` 重写 prose（EMC 结论设计上无代码块，图表走内联 {chart}/{fig}）；复用既有 revise-失败→固定卡 通道。
  - 验证：pytest 34 pass（+2 compare 路由测试）；三 JS ESM .mjs 绿；**Flash eval 16/19=84% PASS**（3 MISS 全是 C6「里-class」边界老案例，与 compare 无关——compare 问句不在 19 例、走 B-track/scale 不经 compare 路由）。memory `emc-compare-skill`。

### 🎯 下一步任务计划

**Tier 1 · 待用户（push + 验证）**
1. **push**：本次会话末 commit+push（400c4a3 + 8f82ebb + 交接卡 commit）→ 本地与 origin 同步。
2. **browser 终验 compare（C6，eval 测不出）**：点欢迎「区域对比」胶囊（对比西陵/伍家岗）→ 验 ① 不出代码块 ② 两区都覆盖不半截 ③ 不说"方法不做"，输出并排对比+差异。顺带验 `_driftRe`（Flash 若吐代码块会被自动重写为 prose）。
3. **④⑤ 数据流 browser 终验**（上一会话遗留，仍未做）：⑤④ gate/命中率 + ⑤② 中文别名 aggregate 得分/置信度/情绪强度 + ④ 城市更新问答回答用权威术语。

**Tier 2 · 低优先 / 可选**
4. **SKILLS_INDEX.md 刷新**：补 ai_qa 等 5.x 主力（留 `/garden` 自动列；阶段一未做）。
5. **EMC ⑤③ boundary_id 分组键 / ⑤④ execSkips 分桶**（低优先收尾，5.x 遗留）。
6. **PreCompact hook 实测**：等下次 85% 压缩触发时验证 `.wip.md` 写入（阶段一建好未自然触发）。

### Push 状态
本次会话末 **commit+push**：`400c4a3`（5.113 园丁层）+ `8f82ebb`（5.114 compare）+ 交接卡 commit。push 后本地与 origin 同步。

### 承重（必守，下会话续改时留意）
- **上下文连贯四纪律（5.113 新，入全局 CLAUDE.md）**：除草（/garden 按需 + 阈值提醒）/ 压缩前快照（PreCompact→.wip.md）/ 漂移自检（读交接卡前 git log+status 对账）/ 单写者（并行 subagent 只回结论给 PM）。memory `context-coherence-discipline`。
- **EMC compare 技能契约（5.114 新）**：compare 复用 zonal_stats 不造端点；select_template C 路由 decision_type=对比→compare（优先 rank/zonal）；boundaries≤4 区；compare 路由 **eval 测不出靠 browser**（C6）；diagnose 因技能目录变→改完必重跑 eval。memory `emc-compare-skill`。
- **_driftRe 拓宽（5.114）**：任意 ``` 围栏→`_reviseOnce` 重写 prose，不静默 strip。
- **项目顶层设计哲学**（CLAUDE.md 6 原则）：4×5=归因落点矩阵（非指标分类清单）+ 多归属 + 政策→情绪→项目闭环。**勿用官方指标完备性质疑 4×5**（错标尺）。memory `project-design-philosophy`。
- **EMC 委托主 Toolbox 不自造**：density/compare→generateHeatmap/Grid/TerrainForAI 或 zonal_stats；只用 Layers 可见层（registry 禁用）；run_python 收口（ctx.allowCodeViz 才放行）。
- **aggregate 列名 aliasing 静默零（⑤② 承重）**：加 stat 须 `resolve_field_alias` 读实际列 + 输出规范名；compare 继承 zonal_stats 的 alias 解析，自身不重复。
- **score ≠ confidence**：5.112 拆 role；square_grid confidence→`l1_confidence_mean`（popup/state 契约勿重命名）。
- **FIELD_INFER confidence 0.3 choke point**：`validate_llm_roles` <0.3 role=null。
- **Flash 80% gate**：`_tplHitRateReady` cold-start 放行零回归 / 成熟<80% 退 while-loop。
- **diagnose prompt 永不动**（保 Flash eval）：技能目录/决策树可长（加 compare 已重跑 eval 84%），但 TEMPLATE/few-shot 结构不动。
- **三大件出图 / 5.74 对账 / 四态出口 / frame-based trust**——全不破。
- **C6**：eval 空 context ≠ 运行时有层路由；数据流改动（compare/_driftRe/④⑤）eval 测不出，须 browser/probe 实跑验。
- **前端 ESM 验证**：`node --check x.js` 假绿，须 `.mjs` 副本或 `--input-type=module`。
- **commit 只不 push**（用户手动；本次例外因用户明说 push）。
- **专业词+通俗解释**（用户初学者）；交付物中文；todo+revision-log 最新置顶同步。

### 本轮改的关键文件（下会话续改看这些）
- **阶段一（5.113 园丁层）**：[.claude/commands/garden.md](.claude/commands/garden.md) / [.claude/hooks/on_precompact.py](.claude/hooks/on_precompact.py) + [on_session_start.py](.claude/hooks/on_session_start.py) / [.claude/settings.json](.claude/settings.json) / [.gitignore](.gitignore) / [MEMORY.md](MEMORY.md) + [apps/CLAUDE.md](apps/CLAUDE.md)（重定向全局树）/ [CLAUDE.md](CLAUDE.md) + [AGENTS.md](AGENTS.md)（manifest 刷新）/ [docs/context-map.md](docs/context-map.md) + [docs/harness-engineering-baseline.md](docs/harness-engineering-baseline.md) / 全局 `~/.claude/CLAUDE.md`（机器本地，不入 git）。
- **阶段二（5.114 compare）**：[ai_qa/paradigm.py](ai_qa/paradigm.py)（TEMPLATE_REGISTRY + select_template + 决策树）/ [frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js)（compare_regions）/ [frontend/js/ai_qa/stages.js](frontend/js/ai_qa/stages.js)（SKILL_DEFS + normalizeParams）/ [frontend/js/ai_qa/harness.js](frontend/js/ai_qa/harness.js)（_driftRe 拓宽）/ [tests/test_a3_paradigm.py](tests/test_a3_paradigm.py)（+2 测试）。
- **纲领**：[docs/revision-log.md](docs/revision-log.md) §5（5.113–5.114）/ [docs/todo.md](docs/todo.md) 07-16 日段。

### 承重 memory 索引
- 本会话新增：`context-coherence-discipline`（上下文连贯四纪律 + 7机制=上下文树）/ `emc-compare-skill`（compare 复用 zonal_stats + 路由 + _driftRe 拓宽 + C6 eval 盲区）。
- 复用：`project-design-philosophy` / `emc-delegates-to-toolbox` / `emc-aggregate-column-alias-silent-zero` / `emc-eval-empty-context-vs-runtime` / `emc-domain-lens-threading` / `token-saving-workstyle` / `no-handoff-on-routine-commit` / `maintain-revision-log` / `todo-revision-log-sync` / `commit-only-user-pushes`（本次用户明说 push 例外）/ `node-check-esm-unreliable` / `pro-term-plus-plain-meaning` / `chinese-all-deliverables`。

---

## 新会话 prompt（复制即用）

```
接续 07-16 会话（阶段一 工作策略园丁层 + 阶段二 EMC compare 技能 已 done + commit + push）。
先 browser 终验，再按 Tier 推进。

【Tier 1·browser 终验（C6，eval 测不出）】基线：07-16 阶段二加 compare 技能（commit 8f82ebb）+
拓宽 _driftRe。browser 实跑验：
① 欢迎胶囊「区域对比·对比西陵区和伍家岗区的情绪与归因」→ 应路由 compare_regions，输出两区并排对比+差异
（不代码块 / 不半截 / 不说"方法不做"）；
② _driftRe：若 Flash 终答吐代码块（```围栏），应被 _reviseOnce 自动重写为 prose。
承重：compare 复用 zonal_stats 不造端点 / select_template C 路由 decision_type=对比→compare（优先 rank/zonal）/
boundaries≤4 区 / compare 路由 eval 测不出靠 browser / _driftRe 任意围栏→revise。

【Tier 1·④⑤ 数据流 browser 终验（上会话遗留）】⑤④ gate/命中率 + ⑤② 中文别名 aggregate
（得分/置信度/情绪强度→score_mean/l1_confidence_mean/emotion_intensity_mean）+ ④ 城市更新问答回答用权威术语。

【Tier 2·低优先】SKILLS_INDEX.md 刷新（补 ai_qa，留 /garden）/ ⑤③ boundary_id 分组键 / ⑤④ execSkips 分桶 /
PreCompact hook 等下次压缩自然触发时实测 .wip.md。

承重：上下文连贯四纪律（/garden+阈值提醒 / PreCompact→.wip.md / 读交接卡前 git 对账 / 单写者，已入全局 CLAUDE.md）/
compare 技能契约（emc-compare-skill）/ _driftRe 拓宽 / 项目设计哲学6原则（4×5=归因矩阵非指标清单，勿用官方完备性质疑）/
EMC 委托 Toolbox 不自造 / aggregate 别名静默零（加 stat 须 resolve_field_alias）/ score≠confidence /
FIELD_INFER confidence 0.3 choke point / Flash 80% gate / diagnose prompt 永不动保eval /
三大件+5.74+四态+frame-based trust 不破 / C6(eval空context≠运行时，数据流改动靠browser) /
node --check 假绿须.mjs / commit 只不 push（用户明说才 push）/ 专业词+通俗解释 / todo+revision-log 最新置顶同步。
先读交接卡 memories/repo/session-handoff.md + docs/revision-log.md §5（5.113–5.114），再动手。
```
