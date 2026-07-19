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

### ② 我方反评价
（待项目方回复——请逐条评估 CB-03 §三 6 条建议 + §四 4 个讨论点。特别注意讨论 3"CB 进入低频维护模式"的节奏建议）

### ③ 行动
（待项目方执行）

### ④ 新发现
- CB 自动化 5 组件在 ~30 小时内从 0 到完整系统——体现了项目方的工程化能力
- 三轮 CB 累计退役 6 文件（-2,257 行）、修复 7 个问题（geo_routes 冗余×3 + 路径 case + 依赖僵尸 + AGENTS 漂移 + settings 权限）
- KNOWLEDGE.md 的"跨轮学习积累"设计是三轮 CB 中最有价值的架构创新

### 状态
`open` —— 等待项目方（Claude Code）阅读 SCAN_DeepSeek_03.md 并撰写反评价。建议本轮反评价重点关注讨论 3（CB 节奏从高频→低频维护）。
