# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月18日（**复盘修复日 done：Phase 5 browser e2e + compare 中文地名 + 底图 + 清测试债**）| 分支 `main` | 本次会话 = 5.129–5.131

---

## 当前节点：复盘修复日 done；用户开新会话做**项目全局开发复盘**（比上轮更全面）

### 背景
07-18 是"复盘 + 修复优化"日，连落三件，git 干净：
- **5.129 EMC 稳定性 Phase 5**：建 browser e2e 测试框架（`tests/browser/`，Playwright + 自管 serve.py）+ 治 compare 5.115 中文地名↔preset_id 错配（新增 `boundary-resolve.js`，中文地名→GeoJSON dict）+ `main.js` 加 `?e2e=1` test seam 注入 fixture 点层。硬断言 TDD 红→绿确证。
- **5.130 修底图不显示**：`map.js` 天地图三项引退役的 `../apps/static/tianditu_*.json`（从未入 git）→ 改内联 raster style 对象（`_tiandituStyle` + TIANDITU_KEY，浏览器端验 Referer）。
- **5.131 清测试债**：pytest 5 红→全绿（207 passed/3 skipped/0 failed）——装 matplotlib（requirements 已声明未装）+ capabilities 断言 stale（L2 已支持 supports_category）+ renewal skip-if-absent。

用户上一轮做了一次复盘（聚焦"测试债 + 本轮工作"），现要**更全面复盘项目全局开发情况**（架构/各模块/管道/测试/债/文档/方向），故开新会话。

### ✅ 本会话已做（5.129–5.131，每 commit 同步 todo.md + revision-log §5）

| commit | 5.NNN | 内容 | push |
|---|---|---|---|
| `1a4b72e` | 5.129 | browser e2e 框架 + compare 中文地名解析（boundary-resolve.js）+ main.js ?e2e=1 seam + docs/emc-test-cases.md C6 清单 + test_emc_template 白名单补 | ✅ 已 push |
| `e340d14` | 5.130 | map.js 天地图 style 内联（治底图 404） | ✅ 已 push |
| `0efd5c2` | 5.131 | 清 5 个既有测试失败 → pytest 全绿 | ⬜ **待 push** |

### 🎯 下一步（新会话 = 项目全局开发复盘，用户明确要求）
用户要"更全面的复盘项目全局开发情况"。复盘应覆盖（不限于 EMC）：
1. **架构健康度**：七层骨架 / 依赖关系 / 承重红线是否守得住 / 有无循环依赖残留。
2. **各功能模块成熟度**：revision-log §0 任务树 ✅/🔄/⬜ 分布——哪些该收尾、哪些该砍、哪些该推进。
3. **数据管道 L0→L4 实际贯通**：L0→L1→L2 通否（L1 LLM 分类需 key 验证）、L3 语义/L4 归因接口预留状态、Sim 数据生成器（ermawu 范例）。
4. **测试覆盖**：单元 207 绿 + browser e2e 框架（用例 1 done，C6 余 3 待补）+ eval（Flash 模板路由）。
5. **技术债清单**：已知待办——compare answer 散文保守 / `?e2e=1` seam 去生产化 / C6 用例补 3（domain_lens/_driftRe/路由分歧）/ 路线图 🔄 项（KDE 批2-4、Analysis 接入、Table、导航 B4/B5、多维归因）。
6. **文档/记忆体系**：revision-log 治理（→5.131）/ design token / memory 三层（CLAUDE.md + AutoMemory + 专项文档）/ retired.md 台账。
7. **下阶段方向建议**：基于复盘给"该收/该推进/该砍"判断。

**复盘优先，先不动代码**；复盘报告交付后再与用户定方向。

### Push 状态
`1a4b72e`（5.129）+ `e340d14`（5.130）**已在 origin**（用户手动 push）。`0efd5c2`（5.131）**待 push**——新会话开始前用户应先 `git push`。

### 承重（必守，下会话续改时留意）
- **只 commit 不 push**（用户手动；memory `commit-only-user-pushes`）。`0efd5c2` 待 push。
- **调动次数优先**（用户全局规则，覆盖 plan mode 派 Explore/Plan 默认）：不派 subagent 探索/规划，自己读文件/grep/规划；批量并行只读；合并多文件修改；给推荐不穷举。
- **底图 5.130 新**：`map.js` BASEMAPS 天地图 = 内联 raster style 对象（不再依赖外部 JSON，根除路径脆弱）；TIANDITU_KEY 浏览器端权限验 Referer；CARTO 三项 CDN URL；默认 tianditu-img-nolabel。
- **compare 中文地名 5.129 新**：`frontend/js/ai_qa/boundary-resolve.js` 解析中文地名→单 feature GeoJSON dict（接入 compare_regions + zonal_stats）；admin_district feature 的 MC 属性 = 地名，非 preset_id。memory `emc-compare-skill`（已更新）。
- **browser e2e 5.129 新**：`tests/browser/`（Playwright sync + 自管 serve.py，**不用 with_server.py**——后者下 main.js seam 长时间不可用）；硬断言挂网络层；`main.js` ?e2e=1 test seam（注入 fixture 点层，零生产影响但仍是 prod test hook——**待去生产化**）。
- **pytest 全绿 5.131**：207 passed/3 skipped/0 failed；matplotlib 已装（KDE 地形依赖）；renewal 测试 skip-if-absent（更新单元.geojson 未随仓分发）。
- **EMC 承重（07-17 沿用）**：L4 lazy enrichment（规则底不动+lazy LLM）/ Sim 资讯收集+buffer 方法论 / compare 技能契约 / 委托主 Toolbox 不自造 / aggregate 别名静默零（resolve_field_alias）/ score≠confidence / diagnose prompt 永不动保 Flash eval / 四态出口+frame-based trust / C6（eval 空 context≠运行时）/ node --check 假绿须 .mjs。
- **项目顶层设计哲学**：4×5=归因矩阵（非指标清单）+多归属+政策→情绪→项目闭环+补盲区+知识库可成长；勿用官方指标完备性质疑 4×5（错标尺）。memory `project-design-philosophy`。
- **上下文连贯四纪律**：除草/压缩前快照/漂移自检/单写者。memory `context-coherence-discipline`。
- 专业词+通俗解释（用户是初学者）/ todo+revision-log 最新置顶同步 / 交付物中文（代码/路径英文）。

### 本轮改的关键文件
- **Phase 5 e2e**：[tests/browser/](tests/browser/)（lib/emc_helpers.py + test_compare_regions.py + fixtures/compare_points.geojson + README）/ [frontend/js/ai_qa/boundary-resolve.js](frontend/js/ai_qa/boundary-resolve.js)（新）/ [frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js)（compare_regions + zonal_stats 接入 resolver）/ [frontend/js/main.js](frontend/js/main.js)（?e2e=1 seam）/ [docs/emc-test-cases.md](docs/emc-test-cases.md)（C6 四例清单）/ [tests/test_emc_template.py](tests/test_emc_template.py)（白名单补）/ pytest.ini（norecursedirs）。
- **底图**：[frontend/js/map.js](frontend/js/map.js)（_tiandituStyle + TIANDITU_KEY 内联）。
- **清债**：[tests/test_emotion_analysis.py](tests/test_emotion_analysis.py)（capabilities 断言）/ [tests/test_range_selector_presets.py](tests/test_range_selector_presets.py)（renewal skip-if-absent）+ matplotlib 本地安装（requirements 已声明）。
- **纲领**：[docs/revision-log.md](docs/revision-log.md) §5（5.129–5.131）/ [docs/todo.md](docs/todo.md) 07-18 日段。

### 承重 memory 索引
- 本会话更新：`emc-compare-skill`（+5.129 中文地名解析 boundary-resolve + E2E 测试范式：?e2e=1 seam + 自管 serve.py 不用 with_server.py）。
- 复用（全局复盘需参照）：`project-design-philosophy` / `emotion-map-logic-chain`（演示逻辑链=全局纲领）/ `context-coherence-discipline` / `token-saving-workstyle` / `maintain-revision-log` / `todo-revision-log-sync` / `no-handoff-on-routine-commit` / `commit-only-user-pushes` / `chinese-all-deliverables` / `pro-term-plus-plain-meaning` / `node-check-esm-unreliable` / EMC 系（emc-delegates-to-toolbox / emc-l4-lazy-enrichment / emc-eval-empty-context-vs-runtime / emc-domain-lens-threading / emc-aggregate-column-alias-silent-zero / emc-tri-state-exit-contract）/ `sim-research-buffer-methodology` / `verify-real-endpoint`。

---

## 新会话 prompt（项目全局开发复盘，复制即用）

```
接续 07-18 会话（复盘修复日 done：Phase 5 browser e2e 框架 + compare 中文地名修复 + 底图修复 + 清测试债 → pytest 全绿，详见 memories/repo/session-handoff.md）。
本会话目标：对【项目全局开发情况】做一次更全面的复盘——不只 EMC、不只最近几轮，覆盖整个项目。

复盘产出要覆盖（结论先行、结构化、分类打分）：
1. 架构健康度（七层骨架 / 依赖 / 承重红线守得住否 / 循环依赖残留）
2. 各功能模块成熟度（revision-log §0 任务树 ✅/🔄/⬜ 分布 → 该收/该推进/该砍）
3. 数据管道 L0→L4 实际贯通（L1 待 key 验证 / L3·L4 预留 / Sim 生成器）
4. 测试覆盖（单元 207 绿 + browser e2e 框架 + eval Flash 路由）
5. 技术债清单（compare answer 散文 / ?e2e=1 seam 去生产化 / C6 用例补 3 / 路线图 🔄 项）
6. 文档/记忆体系健康（revision-log 治理 / memory 三层 / design token / retired.md）
7. 下阶段方向建议

先读（不动代码）：
- memories/repo/session-handoff.md（当前节点 + 承重）
- docs/revision-log.md（全文：§0 路线图任务树 + §3 板块总览 + §4 设计脉络 + §5 最新动态 5.129–5.131）
- CLAUDE.md（演示逻辑链=全局纲领 + 项目设计哲学 + 当前开发状态）+ AGENTS.md（模块表）
- git log --oneline -30 看脉络；Glob 看各层目录结构

承重：调动次数优先（不派 subagent，自己读）/ 只 commit 不 push（0efd5c2 待 push）/ 项目设计哲学（4×5=归因矩阵非指标清单，勿用官方完备性质疑）/ EMC 承重红线见交接卡。
复盘优先先不动代码；报告交付后再与我定方向。
```
