# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月17日（**EMC 整体优化三阶段 B→A1→Sim + A1+Sim 展示闭环 全 done + pushed**）| 分支 `main`（**本地 = origin 同步**，用户手动 push 完成）| 本次会话 = 5.115–5.121

---

## 当前节点：EMC 整体优化三阶段 + 展示闭环 全 done；用户开新会话做**新任务**（待给定）

### 背景
07-17 一整天连续推进：先 browser 终验 07-16 的 compare/_driftRe/④⑤（5.115 全 PASS）→ tracker 文档对账 + MOD_FIELD/MOD_AIQA 埋点（5.116/5.117）→ 用户定 **EMC 整体优化三阶段 plan（B 基建 → A1 L4 多维归因 → Sim 大南门·二马路 L3+L4 数据）**，经多轮 co-design（含 Sim 详细 sub-plan + Sim-0 资讯收集通用模式 + buffer 科学化）→ 三阶段 + A1+Sim 展示闭环全落地 commit + 用户手动 push 完成。**用户现开新会话做新任务（与 EMC 无关，内容待给定）**——本卡 EMC 工作归档。

### ✅ 本会话已做（5.115–5.121，每 commit 同步 todo.md + revision-log §5，用户手动 push）

- **5.115 browser 终验 Tier1 全 PASS + SKILLS_INDEX 刷新（`79e1967`）**：compare 机制走通（路由+逐区 zonal_stats+优雅降级，网络验证）/ _driftRe 代码确认 / ④权威术语 / ⑤④gate footer / ⑤②aggregate 别名双端点。新发现·延后：compare 中文地点名↔preset_id 语义错配（happy path 未通，开新 plan 低优）。
- **5.116 tracker 文档对账 + MOD_FIELD 埋点（`e7d7618`）**：AGENTS.md 模块表 + CLAUDE.md manifest 双重漂移修正（MOD_SPATIAL/MOD_LLM/MOD_PERF 早有埋点补入，8 幽灵模块标 ⬜）；field_dictionary 补 MOD_FIELD（F_001-F_003+D_001，热路径 helper 不 track）；MOD_SPATIAL.F_005 非跳号（属 buffer_analysis.py）。
- **5.117 ⑤③ membership 原语 + ⑤④ execSkips + MOD_AIQA 埋点（`5213bc1`）**：zone role（membership）+ aggregate_by_boundary_id（MOD_SPATIAL.F_008，非 sjoin）+ harness execSkips 分桶 + MOD_AIQA（select_template + 5 build_*_prompt）。
- **5.118 EMC 基建做厚 + Sim-0 资讯收集（`60fc191`）**：B1 wisdom +3 条（culture/planning-meso/operation-event）+ consolidate utf-8 修 + B2 多轮记忆（formatTurnHistory）；Sim-0 web-search 实采 ermawu 真实资讯 → `DATA/sim/research/ermawu.md`（**通用模式，以后 sim 沿用**）。
- **5.119 A1 L4 多维归因做厚（`01f52c4`）**：**lazy enrichment**（规则底不动 + LLM 按需）— `/aiqa/deep_attribution` 端点 + `build_deep_attribution_prompt`（MOD_AIQA.F_007）+ `deep_read_attribution` 工具；政策→情绪→项目闭环 + 官方补盲区（真端点 probe：policy_link=防止大拆大建+十五五，project_link=历史街区保护更新/业态多元化/回迁）。
- **5.120 Phase Sim 大南门·二马路 L3+L4 生成器（`7a9d8cf`）**：standalone `SCRIPT/sim_ermawu_l3l4.py`（MOD_PERF.F_013）+ `ermawu_l3l4_config.py`（10 ABSA aspect + policy/project 种子 + T1→T3 归因深化弧）+ buffer 科学化（200m tapered）；产 `DATA/processed/ermawu_l3l4_{T1-T3}`；内置 validate：pos率 0.06→0.56→0.70，文化/事件占比 ~0.75，policy→project 闭合 100%。
- **5.121 A1+Sim 展示闭环（`424f9f4`）**：`deep_read_attribution` 消费 Sim L4 种子 hints（policy_seed/project_seed/aspect_primary）→ prompt「优先采用」权威锚 → deep_attribution 落到具体政策/项目。

### 🎯 下一步（新会话 = 新任务，待用户给定）
- **本次起用户指示**：不验证（手动）+ push 用户手动。
- EMC 工作已归档，剩余可选项（低优，待用户决定是否回接）：① browser 验证全链路（Import ermawu_l3l4 → 聚合 → deep_read_attribution，用户手动）；② compare 中文地点名↔preset_id 语义适配（开新 plan，低优）。
- **新任务由用户在新会话给定**——读本卡知 EMC 已 done 不重复。

### Push 状态
**origin/main 已同步**（本地 = origin）。07-17 七个 commit（79e1967/5.115 → e7d7618/5.116 → 5213bc1/5.117 → a3aa60b todo sync → 60fc191/5.118 → 01f52c4/5.119 → 7a9d8cf/5.120 → 424f9f4/5.121）均已在 origin（用户手动 push 完成）。

### 承重（必守，下会话续改时留意）
- **EMC L4 lazy enrichment（5.119 新）**：L4 = 规则底 `_attach_4x5_attrs` 不动 + lazy LLM 按需（否决 eager 每 aggregate 跑）；`/aiqa/deep_attribution` + `build_deep_attribution_prompt`(MOD_AIQA.F_007) + `deep_read_attribution` 工具；低置信<0.5/LLM 断→回退规则底；diagnose prompt 不动保 Flash eval（改的是 agent 工具目录）。memory `emc-l4-lazy-enrichment`。
- **Sim 资讯收集+buffer 方法论（5.118/5.120 新）**：新片区 sim 走 Sim-0（web-search→`DATA/sim/research/<area>.md`，通用 Phase 0，从想象→实测）+ buffer 100-400m tapered（人发帖溢出 boundary 线）；范例 ermawu standalone（`ermawu_l3l4_config`+`sim_ermawu_l3l4` MOD_PERF.F_013，ABSA aspect + 政策→项目种子）。memory `sim-research-buffer-methodology`。
- **上下文连贯四纪律（5.113）**：除草/压缩前快照/漂移自检/单写者。memory `context-coherence-discipline`。
- **EMC compare 技能契约（5.114）**：compare 复用 zonal_stats 不造端点；C 路由 decision_type=对比→compare；boundaries≤4；eval 测不出靠 browser(C6)。memory `emc-compare-skill`。
- **项目顶层设计哲学**：4×5=归因矩阵(非指标清单)+多归属+政策→情绪→项目闭环+补盲区；勿用官方完备性质疑 4×5。memory `project-design-philosophy`。
- **EMC 委托主 Toolbox 不自造** / aggregate 别名静默零（加 stat 须 resolve_field_alias）/ score≠confidence / FIELD_INFER 0.3 choke point / Flash 80% gate / diagnose prompt 永不动保 eval / 四态出口+frame-based trust 不破 / C6(eval空context≠运行时) / node --check 假绿须 .mjs。
- **只 commit 不 push**（用户手动；memory `commit-only-user-pushes`）/ **不验证**（07-17 用户指示，本次起手动验）/ 专业词+通俗解释 / todo+revision-log 最新置顶同步。

### 本轮改的关键文件（EMC 三阶段 + 闭环）
- **A1 L4 归因**：[ai_qa/prompts.py](ai_qa/prompts.py)（DEEP_ATTRIBUTION_TEMPLATE + build_deep_attribution_prompt MOD_AIQA.F_007）/ [api/aiqa_routes.py](api/aiqa_routes.py)（POST /aiqa/deep_attribution）/ [frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js)（deep_read_attribution，含 L4 hint 收集）。
- **Sim 数据**：[SCRIPT/ermawu_l3l4_config.py](SCRIPT/ermawu_l3l4_config.py) + [SCRIPT/sim_ermawu_l3l4.py](SCRIPT/sim_ermawu_l3l4.py)（MOD_PERF.F_013）/ [DATA/sim/research/ermawu.md](DATA/sim/research/ermawu.md) / 产 [DATA/processed/ermawu_l3l4_{T1-T3}](DATA/processed/)。
- **基建**：[ai_qa/wisdom.py](ai_qa/wisdom.py)（+3 条）/ [ai_qa/consolidate.py](ai_qa/consolidate.py)（utf-8 修）/ [frontend/js/ai_qa/harness.js](frontend/js/ai_qa/harness.js) + [panel.js](frontend/js/ai_qa/panel.js)（formatTurnHistory 多轮记忆）。
- **tracker**：[core/field_dictionary.py](core/field_dictionary.py)（zone role + MOD_FIELD）/ [core/spatial_analysis.py](core/spatial_analysis.py)（aggregate_by_boundary_id F_008）/ [ai_qa/paradigm.py](ai_qa/paradigm.py) + [prompts.py](ai_qa/prompts.py)（MOD_AIQA）/ [AGENTS.md](AGENTS.md) + [CLAUDE.md](CLAUDE.md)（模块表+manifest 对账）。
- **纲领**：[docs/revision-log.md](docs/revision-log.md) §5（5.115–5.121）/ [docs/todo.md](docs/todo.md) 07-17 日段。

### 承重 memory 索引
- 本会话新增：`emc-l4-lazy-enrichment`（L4 lazy + 规则底不动 + 端点/工具 + 低置信回退）/ `sim-research-buffer-methodology`（Sim-0 资讯收集通用 + buffer 科学化 + ermawu 范例）。
- 复用：`emc-compare-skill` / `emc-delegates-to-toolbox` / `emc-aggregate-column-alias-silent-zero` / `emc-eval-empty-context-vs-runtime` / `emc-domain-lens-threading` / `project-design-philosophy` / `context-coherence-discipline` / `token-saving-workstyle` / `no-handoff-on-routine-commit` / `maintain-revision-log` / `todo-revision-log-sync` / `commit-only-user-pushes` / `node-check-esm-unreliable` / `pro-term-plus-plain-meaning` / `chinese-all-deliverables` / `grid-4x5-attribution`。

---

## 新会话 prompt（新任务，复制即用 — 用户填具体内容）

```
接续 07-17 会话（EMC 整体优化三阶段 B→A1→Sim + 展示闭环 全 done + pushed 到 origin）。
我要开始一个新任务：<具体任务描述>。

承重：上下文连贯四纪律（/garden+阈值提醒 / PreCompact→.wip.md / 读交接卡前 git 对账 / 单写者）/
EMC L4 lazy enrichment（规则底不动+lazy LLM，勿 eager）/ Sim 资讯收集+buffer 方法论（新片区 sim 走 Sim-0+buffer）/
compare 技能契约 / 项目设计哲学6原则（4×5=归因矩阵非指标清单）/
EMC 委托 Toolbox 不自造 / aggregate 别名静默零（resolve_field_alias）/ score≠confidence /
FIELD_INFER 0.3 choke point / Flash 80% gate / diagnose prompt 永不动保eval /
四态出口+frame-based trust 不破 / C6(eval空context≠运行时) / node --check 假绿须.mjs /
只 commit 不 push（用户手动）/ 专业词+通俗解释 / todo+revision-log 最新置顶同步。
先读交接卡 memories/repo/session-handoff.md + docs/revision-log.md §5（5.115–5.121）确认 EMC 已归档，再动手新任务。
```
