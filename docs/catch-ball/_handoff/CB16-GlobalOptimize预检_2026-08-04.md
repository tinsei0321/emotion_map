# CB-16 全局优化 + 发版快照 + 时间轴重规划 实施预检（Codex / glm组 · 2026-08-04）

> **用途**：用户定「①更新过时文件 + 归档陈旧内容 + 全局优化 ②发版候选评估 + 收尾技术债」→ 出 plan 进 CB。落地前请两组预检下方实施草案。
> **登记**：docs/context-map.md · cb-journal CB-16 ③w2。

---

【CB-16 全局优化 + 发版快照 + 时间轴重规划 实施预检（Codex / glm组）】

背景：claude组 三路探索（过时文档 / 发版评估入口 / 时间轴 manifest 根因）完成。用户定：发版评估**先做全局优化+快照**（非冲达标）；时间轴 **重新规划·更优解**。请预检下方 4 子项草案。

第一步 · 读本地文件（同一工作区·**无需 git pull/push**·直接读）
- 探索依据：CLAUDE.md「当前开发状态」:223-227 · `docs/emc-fix-progress.md`（头部 v3.5/220 vs 实际 CB-16/276）· `docs/todo.md`（周归档缺 07-27~08-02·:55 重复节）· `docs/spec.md`/`docs/architecture.md`（Streamlit 死段）· `docs/decisions.md`（停 ADR-016）· `frontend/js/time-source.js:22,31-39` + `core/geo_registry.py:29-41` + `core/config.py:13-14`（时间轴 manifest 404 根因）· `tests/browser/flywheel_audit.py`（B3 飞轮）

第二步 · 实施草案（4 子项·请预检）

**1. 全局优化 · 过时文件更新 + 陈旧归档**
- **CLAUDE.md「当前开发状态」5 行**：L3（LLM 语义）✅·L4（多维归因）✅·空间分析引擎 ✅·UI 优化 ✅·L0→L1 补「L0 走购买·sim 当下充分」（revision-log 5.119/5.120 证据）
- **todo 周归档**：新建 `docs/todo-archive/2026-07-27_2026-08-02.md` 归档 5 个日段（07-28/29/08-01/08-02×2）·删 :55 重复「CB-15 数据认知」节
- **emc-fix-progress.md**：头部更新到 CB-16/276（或标注由 revision-log 承接）·修 :27/29 自相矛盾（220 vs 32）
- **spec.md / architecture.md 清 Streamlit 死段**（12+18 处引用·header 已声明退役）
- **decisions.md**：补 ADR-017~019（Streamlit 退役 / EMC v2/v3 FC 转型 / 出口抽象层）或声明冻结由 revision-log 承接
- **记忆 GC**（`~/.claude/projects/d--Github-emotion-map/memory/`）：合并 extrusion-height 重复索引行·裁决 push-not-redline vs commit-only-user-pushes 冲突（需用户/两组定权威源）·global-time-axis/batch4 记忆标注「设计稿·待落地」

**2. 发版候选评估 · 先做快照（非冲达标）**
- 跑 `EMOTION_TRACE_SESSION=B3-<批> py tests/browser/flywheel_audit.py --batch B3`（当前基线 23/26·88.5%）→ 出**现状快照**（pass 数 + trace 取证 F_002/pro/timeout）
- link_checkup 体检（20 例回归门）+ pytest 全量零回归（当前 276）
- **不修 PRM/CPD-L03**（发版前留·非本次）
- 产出快照报告 → 用户判断发版就绪度

**3. 时间轴重规划 · 同源派生 manifest（更优解·治本）**
- 根因：数据 R100 迁移到 `DATA/performance` 但手写 `_time_manifest.json` 从未落到新位置（仍留 `old_data_processed`）·代码已改指 `/DATA/performance/_time_manifest.json` → 404。**数据一片没丢·只缺描述符**。
- **候选 1（推荐·治本）**：新增 `/api/v1/geo/time-datasets` 端点，从 `geo_registry._POINT_LAYERS`（单一权威）+ 扫 `PERFORMANCE_DIR` **现场组装 manifest**（sourceTemplate 拼 `/DATA/performance/{name}_{slice}_result_geojson.geojson`·L1 双扩展名特判）；`time-source.js:22` 改为「先试 manifest 文件·404 fallback API」→ 时间轴与问答**共享同一注册表**·消除第二份手写清单·未来加数据自动发现
- **候选 2（快速解封）**：把 `old_data_processed/_time_manifest.json` 落到 `DATA/performance/` + 修 3 条 sourceTemplate（ermawu→performance·xiling→old_data_processed）——**写描述符是否算数据红线需用户/两组拍板**
- 建议：候选 2 立即解封演示 + 候选 1 长期同源收编

**4. backlog 收尾（本次快速项）**
- **validate_skill_params 7 工具 drift**：density/buffer/clip/overlay/zonal/extract/merge·paradigm when 同步（契约源 tool_contracts.py 单一源 + 镜像 paradigm.py）
- **renewal 卡 perceptible_metrics domain 门控**（③z3 已知·`_build_card:230` 无条件调用→ 按 domain 门控）
- **CPD-L03 硬断言**（根因已修·test-cases.js CSV 改名 yichang·补断言）
- 其余 backlog（MOD_PLACE 风暴 / F_002 已澄清 / 时间轴 manifest 由子项 3 承接）不进本次

请预检：
1. **全局优化范围**：CLAUDE.md 5 行 + 周归档 + emc-fix-progress + Streamlit 死段 + decisions 补档 + 记忆 GC——范围合理？有无遗漏/过度？（记忆 GC 里 push 冲突裁决需用户/两组定）
2. **发版快照**：先做 B3 快照（不修 PRM/CPD-L03）对吗？还是应连带修 PRM 缺口？
3. **时间轴同源派生**：候选 1（geo_registry 同源 + fallback API）思路对路？L1 双扩展名特判可靠？候选 2（落手写 manifest）是否算数据红线？
4. **backlog 收尾**：7 工具 drift + renewal 门控 + CPD-L03 是否都是本次应做？优先级？
5. **测试方案**：全局优化（文档无测试）·时间轴（time-source fallback 单测 + 端点直测）·backlog（validate_skill_params 回归）——够？
6. **承重零触碰**：不碰 diagnose/harness/ChatRequest·时间轴同源派生不破坏 geo 问答·CLAUDE.md 更新只改当前开发状态段？
7. **范围边界**：4 子项是否都要？优先级？（全局优化 + 时间轴是主体·发版快照 + backlog 是配套）

第四步 · 产出简短 SCAN 落 docs/catch-ball/scan/CB16-GlobalOptimize预检-*_2026-08-04.md
- 判定：草案是否可行·有无需改项（优先级 P0/P1/P2）
- 独立判断·不要互相参考对方报告

规则：只读评估·禁改代码/禁 commit·结论先行。

---

*本请求由 claude组 发起（2026-08-04）·CB-16 全局优化 + 发版快照 + 时间轴重规划 实施预检。*
