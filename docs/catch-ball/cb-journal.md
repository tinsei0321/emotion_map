# CB Journal（Catch-Ball 轨迹）

> 我方（Claude Code）与第三方评价（`docs/catch-ball/SCAN_DeepSeek_01.md`，DeepSeek V4 Pro）的多轮 catch-ball 对话轨迹。
> 按轮追加不覆写（区别于 session-handoff 的"覆写当前节点"）。每轮四节：① SCAN 摘要 ② 我方反评价 ③ 行动 ④ 状态/新发现。
> 反评价标尺：agree=证据支持/我方漏掉；disagree=用错标尺/事实错误；partial=方向对细节偏。承重红线（tracker 编号连续/diagnose 永不动/四态）不接受简化。
>
> ---
> **归档信息**：原始路径 `docs/cb-journal.md`，于 2026-07-19 移入 `docs/catch-ball/` 归档。

---

## CB-01 · 2026-07-18（首轮）

### ① SCAN 摘要
4 个 Explore agent 扫描 ~100 文件。总评 7.6/10（架构 8.5 / 代码 7.5 / 测试 6.5 / Harness 9 / 文档 8 / 调用效率 6）。头号高优建议=调用次数优化（合并 Reviewer+Tester、批量变更、本地脚本替代 spawn、MANIFESTO 分层）。关键发现：core/ui_components+layer_registry 是 Streamlit 僵尸 / geo_routes 冗余计算 / db.py iterrows / sim agent 未注册 / Skills 落地率低 / 前端无单测。

### ② 我方反评价
**agree（采纳，已验证）**：
- Streamlit 僵尸——ui_components(835 行/29 streamlit)+layer_registry(3 st.)+**map_engine(pydeck，SCAN 未点名但同类)** 全部零活引用已核（core/__init__.py 仅 docstring 文字，活代码无 import）。删除安全。
- geo_routes 冗余——逐行核实，且发现比 SCAN 更深的问题（见 ④）。
- sim agent 未注册 settings.json——已核（仅 8 agent）。
- db.py iterrows perf、Skills 落地率、前端无单测、微服务化否决——均合理。

**disagree（用错标尺，反驳）**：
1. "数据管道 90%、L0-L4 全部实现"=**事实错误**。L1 治理从未在真实 key 实跑；SCRIPT 层 L3/L4 是 ⬜ 预留（SCAN 自身 §2.6.2 又说 9 模块⬜，自相矛盾）。归因靠 EMC 分析时 + Sim。真实 ~75%。**且 L0 未来走购买途径，sim 充分非风险**（用户澄清，memory `l0-acquisition-purchase-strategy`）。
2. "调用次数优化=头号高优"=**前提不成立**。项目跑在用户全局"不派 subagent"规则下，AGENTS.md 8 Agent 是概念框架，主线程直接干。SCAN 假设的"标准 SOP=7 spawns"是理论值非实际——解一个已基本解决的问题。
3. "MANIFESTO 分层减 token"=**撞承重红线**（diagnose 永不动保 Flash eval）。不采纳。
4. "MCP 应与 DeepSeek 匹配"=**provider-neutral 错标尺**。智谱优先因国内视觉/搜索质量，与主 LLM 厂商无关。（但 vendor SLA 单点论部分认同。）

**partial**：追踪 ROI 测量——同意做实验（30 天 trace.log 触发统计），**不同意预设简化**（编号连续是 rule 10 红线，追踪是 LLM 调试 O(1) 利器）。

**SCAN 漏掉（我补）**：§0 任务树漂移 3 周 / retired.md 缺失 / Toolbox 多维归因 ⬜ vs EMC deep_attribution ✅ 重叠 / `?e2e=1` seam 去生产化。

### ③ 行动
**已执行（本轮 commit）**：
- [x] memory `l0-acquisition-purchase-strategy` 写入（防再误判）
- [x] Tier 0.3 sim-emotion-data agent 注册 settings.json
- [x] Tier 0.2 geo_routes.py 三处清理（zonal_stats 死循环+冗余 / rank 双调用 / nearest 死三元）—— 零行为变化

**待执行（部分已做）**：
- [x] **Tier 0.1 删 3 僵尸** + .streamlit/config.toml —— commit `5e7b8c6`（用户"继续推进"授权后分类器放行；-1439 行；retired.md 留痕）
- [x] **入库** `.zcode/`（ZCode 工具状态·双环境同步）+ `docs/SCAN_DeepSeek.md`（CB 输入历史）—— commit `5e7b8c6`
- [x] Tier 1 部分：§0 树主干 refresh（七层/数据管道/Harness/底图）/ retired.md / tracking-progress 对账（改指 AGENTS.md 权威源，修 frozen-0613 漂移）
- [x] Tier 1 余（部分）：§0 分支补 topology ✅（5.134）/ `?e2e=1` 去生产化 ✅（5.134，main.js 零 test 代码→独立 e2e-seam.js + index.html 条件 dynamic-import；ESM 绿，browser 验证因环境挂延后）
- [ ] Tier 1 余：C6 补 3
- [ ] Tier 2：db.py 批量插 / 前端 JS 单测基建 / 9⬜ 埋点细化 / vendor 本地化核查
- [ ] zonal_stats latent bug 修（n_dom/n_elem 补充失效，需先确认消费方）

### ④ 新发现（SCAN 之外，清理中挖出 + 深挖定级）
- **zonal_stats latent bug → wontfix（无活消费方）**：原 discover 循环想补 `n_dom_*/n_elem_*` 到 zonal_stats 响应，遍历错源（rows.columns，而 _props_df 只返请求列）→ 补充从未生效。**深挖消费方**：`rank` 直读 gdf.columns（不经 _props_df）/ `panel.js` 矩阵 `_cellsByBucket` 读地图图层 `f.properties`（图层 GeoJSON 含完整 stats 列）—— **均不经 zonal_stats 的 trimmed 响应**，故无消费方读这两列。修复=向无人读的响应加列=死重 → **wontfix**（geo_routes 注释已标注）。
- **db.py 全闲置 → SCAN 建议7 declined**：`EmotionDB` 全仓零活引用、无 test_db（demo 走 GeoJSON 文件非 SQLite）。且 `insert_points` **早已用 executemany 批量插**（`iterrows()` 只用于构建记录列表做 col_map+NaN 过滤，非逐行 DB 插入）。SCAN 建议7 既优化死代码、又描述失准 → **declined**。db.py 去留（retire vs 留作未来购买数据 DB 预留）待用户定。

### 状态
`open` —— Tier 0 ✅（5.132-5.133）/ Tier 1 大部分 ✅（§0 refresh + ?e2e=1 去生产化 + retired.md + tracking-progress 对账，5.134）/ db.py 退役 + zonal_stats wontfix 闭环（5.135）。**待**：browser 环境恢复后复验 seam + C6 补 3；前端 JS 单测基建（头号短板）。双模型闭环：待 DeepSeek 二次扫描对比验证。

---

## CB-02 · 2026-07-19

### ① SCAN 摘要
3 个 Explore Agent + 主线程核实，覆盖 ~200 文件 / ~51,000 行。综合 7.6/10（架构 8.5 / 代码 7.5 / 测试 6.0 / Harness 9.0 / 文档 7.5 / 调用效率 7.0）。CB-01 10 条建议：✅ 2 完成 / ❌ 4 拒绝（其中 2 条因 CB-01 描述失准或撞红线）/ ⬜ 3 待处理 / 1 部分。CB-01 退役清理验证通过（5 文件已删，-1,735 行），geo_routes 修复生效，sim agent 已注册，e2e seam 正确分离。

**CB-02 新发现**：requirements.txt 残留 streamlit+pydeck 僵尸依赖；range_selector.py 路径大小写不一致（Linux 部署会 break）；AGENTS.md 声称 8 Agent 但实际 9；geo_registry.py 零 @track；prd/spec/architecture 含过时 Streamlit 内容；trace-digest.md 空；panel.js 2,098 行过大。新增 10 条建议（3 高 / 3 中 / 4 低）。

**CB-01 反评价第三方审核**：agree 4 条全部核实通过；disagree 4 条中 3 条反驳成立、1 条部分成立（数据管道完成度 90% 确实偏高但 75% 也偏保守→建议折中 80%）；partial 1 条平衡立场。

**关键讨论点**：AGENTS.md 定位（概念框架 vs 运行时契约）、topo_scanner 自文档化意义、E2E 策略困境（先 JS 单测再 browser）、双模型闭环首次验证（有价值但需改进——SCAN 应先确认运行时假设）。

### ② 我方反评价（/cb 02，2026-07-19）

**10 条建议**（verify-before-accept 已核代码级指控）：

| # | SCAN 建议 | 判定 | 证据/行动 | decline reason |
|---|-----------|------|---------|----------------|
| 1 | requirements 僵尸依赖 | **agree** | grep 零活 import 核；删 streamlit==1.58.0 + pydeck | — |
| 2 | range_selector 路径大小写 | **agree** | L21 `'data','boundaries'` 小写确认（Linux 部署 bug）；→ `'DATA'` | — |
| 3 | AGENTS.md 8→9 同步 | **agree** | settings.json 9 agent 核；AGENTS.md 标题+表+sim 行更新 | — |
| 4 | 冗余 sim 脚本退役 | **partial** | `generate_l1_mock` 退役（自标 superseded + 零活引用）；**`generate_test_data` 保留** | **事实错误**：test_data 是 L0 raw（10 万条全管线测试），与 sim_performance_data（L1/L2 demo）用途不同，非冗余 |
| 5 | geo_registry 补埋点 | **agree-defer** | 0 @track / 7 函数确认；守编号连续，独立任务（非 /cb 批次） | — |
| 6 | 文档 Streamlit 过时内容 | **agree-defer** | 多 doc 清理，非紧迫 | — |
| 7 | dev-notes 更新 | **agree-defer** | doc 工作，低优先 | — |
| 8 | trace-digest 空诊断 | **partial** | cursor `.claude/.trace-digest-cursor` **不存在**（hook 可能因此跳过追加）；诊断 defer | — |
| 9 | Bash(streamlit) 权限清理 | **agree** | settings.json allow 删 `Bash(streamlit *)` | — |
| 10 | panel.js 拆分 | **defer** | 技术债预防；前端 JS 单测（头号短板）更高优 | — |

**4 讨论点**：

| 讨论 | 判定 | 行动 |
|------|------|------|
| 1 AGENTS.md 定位（概念框架 vs 运行时） | **agree** | 加「概念框架声明」到 AGENTS.md 头部——免疫未来 SCAN 重犯 CB-01 错误（据理论 SOP 算调用次数） |
| 2 topo_scanner 自文档化扩展 | **discuss** | 远期（依赖健康度 / 追踪热力图 / 变更影响），不行动 |
| 3 E2E 策略困境 | **agree** | B 优先（JS 单测不依赖 browser）——已是项目 plan，无新行动 |
| 4 双模型闭环改进 | **agree** | RULES v2（CB-03 前）加"SCAN 先确认运行时假设"步骤 |

### ③ 行动（已执行）

**agree 快赢（已 act）**：
- [x] 建议1：requirements 删 streamlit+pydeck
- [x] 建议2：range_selector `'data'`→`'DATA'`（路径构造 + docstring）
- [x] 建议3：AGENTS.md 8→9（标题 + Agent 清单 + sim 行）
- [x] 建议9：settings.json 删 `Bash(streamlit *)` 权限
- [x] 讨论1：AGENTS.md 加「概念框架声明」
- [x] 建议4 部分：`generate_l1_mock.py` 退役（retired.md 留痕）；`generate_test_data.py` 保留（declined·事实错误）

**defer（已登记，非本轮）**：建议5（geo_registry 埋点·守编号连续）/ 建议6（文档 Streamlit 过时）/ 建议7（dev-notes）/ 建议8（trace-digest cursor 诊断）/ 建议10（panel.js 拆分）。

**验证**：`pytest tests/ -q` → **207 passed**（CB-02 行动零回归）+ 2 geocode offline tests fail（admin fresh-env：network/key 依赖，**非 CB-02 回归**；类比 h3 缺失——admin 需 `pip install -r requirements.txt` 补全；h3 已 pip install 补）。

### ④ 新发现

- CB-01 与 CB-02 之间，项目方自行发现并修复的项目（未在 CB-01 建议中）：map_engine.py pydeck 僵尸退役、zonal_stats latent bug → wontfix（深挖 3 条消费路径）、db.py 退役（已是 executemany → SCAN 描述失准）。
- **新 SCAN 标尺纠正模式（入 KNOWLEDGE §3）**：SCAN 把不同用途的 sim/工具脚本误判"功能重叠"（generate_test_data = L0 raw 全管线测试 vs sim_performance_data = L1/L2 demo）→ verify-before-accept 须查 docstring 定用途，勿轻信"重叠"。
- **跨环境 env-gap**（admin fresh-env）：h3 声明未装（pip 补）；2 geocode offline 测试 network/key 依赖失败。换环境须 `pip install -r requirements.txt` + 核 network 测试。

### 状态
`closed`（CB-02 反评价 + 行动完成）—— 5 agree 快赢已 act + generate_l1_mock 退役；5 项 defer 已登记。pytest 207 绿（2 geocode offline env-fail 非回归）。**待**：CB-03（DeepSeek 三次扫描对比验证 CB-02 改进）+ defer 项择机。本轮新 learning 已入 KNOWLEDGE §3。

---

## CB-03 · 2026-07-19

### ① SCAN 摘要
本轮特殊：项目代码（core/api/ai_qa/frontend）零变化。焦点为 CB 流程自身的成熟度评估。综合 7.7/10（首次上升 +0.1：Harness 9.0→9.2 + 文档 7.5→7.8）。CB-02 全部 5 项 agree 行动验证通过；4 项 defer 理由充分。

**核心发现——CB 自动化基础设施**：5 组件全 A 评级——`/cb` command（9 步流水线，45 行）、Hook CB detector（零 LLM 调用，27 行）、KNOWLEDGE.md（5 章节跨轮知识库，71 行）、记忆共享通则（context-map.md + CLAUDE.md）、路径归档（cb-journal/retired 移入 catch-ball/）。这是从"手动 ad-hoc"到"工程化流程"的关键跃迁。

**CB-02 反评价质量**：较 CB-01 显著提升。agree 5/5 兑现，decline/defer 理由全部充分。KNOWLEDGE.md 将 CB-02 的误判（generate_test_data ≠ 功能重叠）提炼为 §3 新模式。

**新建议（6 条）**：3 高（KNOWLEDGE vs RULES 边界 + auto-check 可配置化 + 回归功能开发）、2 中（geo_registry 埋点重申 + 文档过时重申）、1 低（trace-digest cursor 根因分析）。

**关键讨论点**：CB 自动化 ROI（当前投入合理，建议 CB-05 正式评估）/ KNOWLEDGE.md pruning 策略（预设触发条件）/ 项目阶段信号（质量巩固期应结束，CB 进入低频维护模式，每 5-10 个功能 commit 一次 SCAN）/ 双模型闭环三轮回望（4/5 目标成熟）。

### ② 我方反评价（/cb 03，2026-07-19）

**6 条建议**（verify-before-accept 已核；建议5 已核 on_session_end.py）：

| # | CB-03 建议 | 判定 | 证据/行动 |
|---|-----------|------|---------|
| 1 | KNOWLEDGE vs RULES 承重边界（重复） | **agree** | 真重复（RULES §3.3 + KNOWLEDGE §1 同 6 红线）→ 撞记忆共享通则"单一权威源"。RULES §3.3 → pointer to KNOWLEDGE §1（保留摘要 + 指针） |
| 2 | /cb auto-check 可配置清单（硬编码） | **agree** | step 5 硬编码 4 检查 → 数据驱动。KNOWLEDGE 加 §6 Auto-Check 清单 + /cb step 5 改"加载 §6" |
| 3 | geo_registry 埋点（重申） | **defer** | 守编号连续·独立任务（未变）；下个功能 sprint |
| 4 | 文档 Streamlit 过时（重申·2 轮） | **defer·提升优先级** | 下个文档维护日首项 |
| 5 | trace-digest cursor 根因（SCAN 深化） | **agree·更正 CB-02** | 已核 on_session_end.py：cursor 缺失 fallback `last_read=0`（L29-35）+ `if not errs: return`（L47）→ **空 digest = trace.log 无 ERR/WARN（健康）或 trace.log 不存在（fresh env），非 bug**。CB-02"cursor 缺失=疑似 bug"partial 被闭环深化更正 |
| 6 | panel.js 拆分（重申） | **defer** | JS 单测后（时间轴会话之后） |

**4 讨论点**：

| 讨论 | 立场 | 行动 |
|------|------|------|
| 1 CB 自动化 ROI | **agree**（当前合理） | CB-05 正式 ROI 评估（总投入 vs 实际修复/避免回归） |
| 2 KNOWLEDGE pruning | **agree** | KNOWLEDGE 加 pruning 触发（§3>15/§5>10/file>200 归档） |
| 3 CB 节奏高频→低频 | **强 agree** | KNOWLEDGE 加节奏决议；**本计划即践行**（CB 收尾后转时间轴，CB 低频，每 5-10 commit 一次 SCAN） |
| 4 "SCAN 先确认运行时假设" | **agree·PROPOSE** | 给第三方 CB-04 RULES 修订（加 SCAN 前置步骤：读 KNOWLEDGE §2 + 确认运行时）；不擅改 RULES 方法论 |

### ③ 行动（已执行）

- [x] 建议1：RULES §3.3 承重 → pointer to KNOWLEDGE §1（保留摘要 + 指针，单一权威源）。
- [x] 建议2：KNOWLEDGE 加 §6 Auto-Check 清单 + /cb step 5 改"加载 §6"。
- [x] 讨论2：KNOWLEDGE 加 pruning 触发条件。
- [x] 讨论3：KNOWLEDGE 加 CB 节奏决议（高频→低频维护）。
- [x] 建议5：本 journal 记 trace-digest 闭环更正（CB-02 partial → CB-03 确认健康；无代码改）。

**defer**：建议3（geo_registry 埋点·下个 sprint）/ 建议4（文档 Streamlit·下个文档日）/ 建议6（panel.js·JS 单测后）。
**PROPOSE 给第三方 CB-04**：讨论1（CB-05 ROI）/ 讨论4（RULES 加 SCAN 前置步骤）。

### ④ 新发现

- CB 自动化 5 组件在 ~30 小时内从 0 到完整系统——工程化能力的体现。
- 三轮 CB 累计退役 6 文件（-2,257 行）、修复 7 个问题（geo_routes 冗余×3 + 路径 case + 依赖僵尸 + AGENTS 漂移 + settings 权限）。
- **KNOWLEDGE.md 的"跨轮学习积累"是三轮 CB 最有价值的架构创新**——每轮新 learning 入库，未来 CB-N 自动避免重犯前 N-1 轮错误。
- **trace-digest 闭环深化**：CB-02 标"cursor 缺失=疑似 bug"，CB-03 核代码后确认"cursor 缺失有 fallback，空 digest=健康"——双模型闭环的"发现→深化→更正"价值兑现。

### 状态
`closed`（CB-03 反评价完成）—— 4 agree 已 act（RULES pointer / KNOWLEDGE §6·pruning·cadence / /cb step5 / trace-digest 更正）；3 defer + 2 PROPOSE 给 CB-04。CB 转低频维护模式（每 5-10 功能 commit 一次 SCAN）。**下一会话推进极性深读时间轴**（T1→T3 演进）。

---

## CB-CPD-01 · 2026-07-22（CPD 专轨 · DeepSeek + K3 双模型首评）

> 专轨定义见 `docs/cpd-core-plan-review.md`。评审对象：`docs/cpd-core-plan.md` **v0.2**（单份 plan，非全项目）。
> 评审模型：DeepSeek V4 Pro + K3（均自读项目文件 + 承重实证）。报告：[DeepSeek](SCAN_CPDPlan_01-deepseek.md) / [K3](SCAN_CPDPlan_01-k3.md)。

### ① SCAN 摘要（双模型）

**DeepSeek（综合 B-）**：六维——架构 B+ / 功能 B / 承重 B+ / **演示表现力 C+（最大短板）** / 分阶段 B / 风险 C+。核心判断：CPD v0.2 是"功能教程"非"诊断叙事"；S3"问我想看什么"反模式（应引导点地图非打字）。阻塞 G1 的 4 硬伤（ask 漏态 / 状态回退 / localStorage 脏态 / turnId 未绑）+ 演示表现力 3 关键建议（文案叙事化 / S3 空间交互优先 / S4 融入宏观诊断信号）。

**K3（更精准，附大量 file:line）**：方向与承重纪律合格，无撞红线；但 §4 引导状态机是全 plan 最弱一节——**3 个 P0 spec 错误**（plan 对"已就绪地基"的事实陈述与代码不符）：
- P0-1 `.aiq-conclusion` **死信号**（cpd-state.js:29 查询，全前端无 JS 创建者）→ curState 永不到 S4。
- P0-2 exit 词表不匹配（plan 大写 RESULT/CONCEPT；harness 实际小写 `result/gap/partial/ask/drift`；general 短路无 exit；drift 缺席）。
- P0-3 映射表 key=curState 与 deriveState 矛盾（任何可见层→S2，S0/S1 不可达）。
K3 另指：光环硬编码 hex（ai_qa.css:431）违 theme var；交互环未闭合（U6 实质）；review desc 灰度缺口。附 U1-U7 立场表。

**共识**：ask→null、exit 读 `_curTrace.exit`、turn-ended 竞态（init 恢复）、curState 承重措辞、review desc 灰度、状态回退、流式读 `_streaming`、光环 theme-var、`_followUps` 优先级。
**分歧**：G1 独立 ship（DS 否·半成品 / K3 能·agree U2）→ v0.3 调和。

### ② 我方反评价（主线程，verify-before-accept 已 grep/read 核实 4 承重证据）

**4 承重核实（全部属实）**：`.aiq-conclusion` 死信号（全前端仅 cpd-state.js:29 + ai_qa.css:523，无 JS 创建）/ exit 小写词表（harness 272/292/307/476/568/608/620/644）/ curState 进 buildContext（tools.js:455-458）/ 光环硬编码 hex（ai_qa.css:431）。

| # | 条目 | 来源 | 判定 | 证据/采纳 |
|---|---|---|---|---|
| 1 | exit 词表大写错误 | K3 P0-2+DS | **agree** | 小写五值 ∪ undefined；CONCEPT 改判 intent/skipped（同 _followUps:478）；补 drift |
| 2 | .aiq-conclusion 死信号 | K3 P0-1 | **agree** | 改 .aiq-exit-badge（panel.js:378，免疫流式误推） |
| 3 | 映射 key=curState 矛盾 | K3 P0-3 | **agree** | 改特征向量真值表（deriveState S0/S1 不可达） |
| 4 | ask 漏态 | DS+K3 | **agree** | exit='ask'→null |
| 5 | turn-ended 数据源+竞态 | DS+K3 | **agree** | 读 _curTrace.exit + {exit,turnId,intent} + finally 守卫 + 引擎 init 恢复 |
| 6 | 状态回退 | DS+K3 | **agree** | 特征向量真值表覆盖（同表重算） |
| 7 | 流式误推 | DS+K3 | **agree** | 读 _streaming 硬门 + exit-badge 天然免疫 |
| 8 | curState 承重措辞错误 | DS+K3 | **agree** | 改"推导纯客户端，注入 buildContext 仅语境提示，不参与路由" |
| 9 | 光环硬编码 hex | K3 | **agree** | 抽 --emc-halo-* theme var（G2/G4） |
| 10 | review desc 灰度 | DS+K3 | **agree** | ≥10 条历史微观问题对比 fail 率，>30% 调话术 |
| 11 | U7 三态分级 | K3+DS | **agree** | fail/warn/pass（warn 不触发 revise 防飙升） |
| 12 | 引导 vs 追问胶囊冲突 | DS+K3 | **agree** | gap/partial/ask/drift 时引擎 null；banner 内视觉分组 |
| 13 | 谓词定义缺口 | K3 M5 | **agree** | hasImport 排除 AI 组/tool 产出；hasAnalysis=_ui.tool∈{grid,zonal,heatmap} |
| 14 | localStorage 脏态 | DS+K3 | **agree** | 引擎 init 检测有图层无历史→null+warn；引导态不持久化 |
| 15 | 交互环未闭合（U6） | K3 M3+DS | **agree** | S4·result 含 ref 时加"地图定位"CTA 闭合视野端 |
| 16 | S3 空间交互优先 | DS | **agree** | 文案"点地图深红/深绿"，对话作备选 |
| 17 | P0 用例顺序矛盾 | K3 L1 | **agree** | 引擎状态转移挪 G1（P0 引擎不存在） |
| 18 | G3 绿色摘要条未定义 | K3 L2 | **agree** | §六补（banner done 变体） |
| 19 | S4→S0 重置路径 | DS | **agree** | "换范围"CTA dispatch cpd:reset |
| 20 | review.py docstring 漂移 | K3 L5 | **agree** | "六条"→"七条"顺手修（P1） |
| 21 | 文案叙事化 | DS | **partial** | 方向 agree；具体文案 G1/G2 打磨，plan 立原则+示例 |
| 22 | G1 独立 ship（分歧） | DS否/K3能 | **partial·调和** | G1 独立 ship + 含光环 click 最小 CTA（DS 方案 A） |
| 23 | 光环改胶囊整体呼吸色 | DS | **partial** | G4 抛光期（先 theme-var 化） |
| 24 | 地图层引导浮层 | DS | **partial** | 另一子系统；先用 #15 轻量闭合，浮层列 U10 |
| 25 | 用户忙检测 | DS | **partial** | 列 U8（G3 边界） |
| 26 | engage 再亮兜底 | K3 | **partial** | 列 U9（观察项） |

**disagree：0**。两份均未撞承重红线，建议皆有 file:line 证据。

### ③ 行动（plan v0.2 → v0.3，本轮 commit）

修订 cpd-core-plan.md 九点（详见 v0.3 头部变更说明）：
- §4.1 信号源重写（exit-badge / 小写 exit / 谓词 / _streaming）。
- §4.2 特征向量真值表（key 从 curState 改特征向量；ask→null / drift→retry / 回退同表重算）。
- §4.3 调度强化（turn-ended {exit,turnId,intent} + finally 守卫 + init 恢复 + cpd:reset）。
- §七 curState 措辞修正 + 光环 theme-var 列入 §九。
- §八 P0 用例改地基行为 / G1 含光环可点 / G3 绿色摘要条补 §六。
- §配套 A 灰度 + U7 三态。
- §六 6.4 演示链服务（S3 空间优先 + S4 地图定位 CTA + 文案叙事化）。
- 新增 U8-U10。

不动代码（review.py / 前端 / tests 留待 P0-P2 实施）。

### ④ 新发现

- **双模型互补**：DeepSeek 强产品/演示视角（功能教程 vs 诊断叙事），K3 强代码级精准（file:line 实证 3 P0 spec 错误）。同轮双模型比单模型覆盖更全——DS 指方向，K3 定落点。**这是 CPD 专轨首次双模型，值得固化为主轨实践**（未来 SCAN_DeepSeek_{NN} 也允许多模型 `-{model}` 后缀）。
- **4 承重证据全部属实**：plan v0.2 对"已就绪地基"的 3 处事实陈述错误（死信号/词表/映射 key）+ 1 处措辞错误（curState），均 grep/read 核实。教训：写 plan 引用"已就绪"信号须核实生产者，勿信"已订阅"=存在。
- **G1 分歧调和**：DS（半成品不可独立 ship）与 K3（可独立 ship）不悖——G1 独立 ship 指不依赖 G2 banner，但 G1 本身含光环 click 最小 CTA（DS 方案 A）。两者并取。
- **演示表现力共识**：交互环闭合（S4 地图定位 CTA）= U6 实质解法——引导从"装载自动化"升"诊断叙事"，解除"为引导而引导"风险。这是本轮最大方向收益。

### 状态
`本轮反评价完成` —— plan v0.2→**v0.3**（九点修订，吸收 26 条建议：agree 20 / partial 6 / disagree 0）。4 承重证据已核实。**待 CB-CPD-02**：v0.3 喂第三方验证修订是否落地 + 演示表现力升维是否到位（尤其 S3 空间交互 / S4 地图定位 / 文案叙事化的具体落地）。
