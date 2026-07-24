# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月24日收工（**EMC 治本 4 批 + 06/07 评估 + density 治本 plan 定稿**）| 分支 `main` | 本次 push

## 当前节点：EMC "基本不可用"根因已定位，density 治本 plan 已存待执行

今日（07-24）连做 4 批治本 + 06/07 评估。**EMC 本体核心（density 渲染 / 工具认知）仍"基本不可用"**——测量层修好了（信号/断言/报告/EMC-SUM/JSON sidecar），**本体核心未动**（K3 "相位差"诊断成立：测量进展 vs 本体未修 vs 测试基建污染）。06 工具 pass=0% / 07 意图 pass=33%（3 OK 全空心·有效≈0%）。

## 今日已 commit（4 批 · revision-log 5.200-5.203）
- **5.200 P0 安全批**：滚动复位 / srcId 导入去重 / density 执行信号。
- **5.201 B0+B1**（治超时#1）：eval 冻结 + 词表 single-source + 模型路由（final/revise→flash + gate 0.8→0.6 + while-loop 75s 预算守卫）。
- **5.202 R1**（治假 GAP·区片可分析）：D2 strategy 可派生语义 + D4 grounding 枚举 boundary 子要素 + D1 派生判定器。
- **5.203 05-llm 修复**：T1 seam 三修（pool `processed`→`performance` + `xiling_wujia`→`yichang` + dsvRows 解引号 + 五档极性·真数据 16933 行 5 档充足）+ UI 固定图钉（Range/Layers/Toolbox）+ EMC 排版/字体/答语文风。

## 下会话执行：density 治本 plan（已存）
**plan 文件**：`~/.claude/plans/emc-gis-rippling-dream.md`（第 5 批·6 步）。**先读它 + `git log --oneline -15` 对账**。
3 Explore agent + K3（`.codebuddy/reports/emc-eval-report06-07-2026-07-24.md`·C1-C9 簇）根因收敛，按优先级：
1. **C5 渲染**（用户#1 彩虹图不显示·最大见效）：`addHeatmapPaint` weightField=`emotion_intensity` 默认·数据缺该字段→weight 表达式=0→rainbow 透明（[map.js:685](frontend/js/map.js#L685)）→ **weight 兜底 1.0** + renderLayer try/catch + source 断言。
2. **C6 工具认知**（用户#4 密集→clip / #5 "不支持热力"幻觉）：`"密集"`触发词 5 处全空 + density 僵尸文案"方格面网格"（[paradigm.py:252](ai_qa/paradigm.py#L252)）+ Toolbox heatmap/grid/terrain 缺席 catalog → **Agent2 八 prompt 文案改**（paradigm.py + prompts.py·**eval-first 红线**）。"不支持热力聚合"= LLM 幻觉（非硬编码）。
3. **C 分组**（用户#2）：`categoryOf`（[state.js:867](frontend/js/state.js#L867)）**不用 parentId**·"EmotionMap Copilot"组卡永远空 → 加 parentId 短路（1 处）+ density/grid 入口传 parentId。
4. **B srcId 工具层**（用户#3 点名两次）：addResultLayer 只按名去重·异名同内容堆叠·工具层无 srcId → `_contentSig` 抽共享（[main.js:86](frontend/js/main.js#L86)）+ addResultLayer/_registerToolboxLayer 去重。
5. **T9 例间清层**（测试侧 e2e_points 堆叠·治超时加剧）。
6. **C7 夷陵资产**：行政区.geojson 9 feature **无夷陵区**·EMC 判缺**对**·[test-assets.js:8](frontend/js/test-assets.js#L8) 描述错 → 改描述 + 用例期望。
**后续（非本批）**：D3 链式模板（C3 超时）/ T4 胶囊矛盾（C4·[panel.js:816](frontend/js/ai_qa/panel.js#L816) default ready）/ T6+T3 断言（C8 空心 OK）。

## 红线 / 未决
- **DATA/processed→performance 迁移**：用户的本地数据操作（删 `DATA/processed/*` + 新增 `DATA/performance/` + `DATA/old_data_processed/`）·**未 commit·数据红线·留用户处理**（我未碰）。
- 本次 push 30 commit（29 旧 + 1 收工）。
- C6 触 diagnose prompt → **eval-first**（先冻结→改→重跑验"密集"→density）。

## 恢复指引（新会话）
1. 读 plan（`~/.claude/plans/emc-gis-rippling-dream.md`）+ `git log --oneline -15` 对账 5.200-5.203。
2. 读 K3 报告（`.codebuddy/reports/emc-eval-report06-07-2026-07-24.md`·C1-C9 簇 + 12 序路线）+ [docs/emc-fix-backlog.md](docs/emc-fix-backlog.md)（05-llm T1-T7/D3 状态表）。
3. 执行 density plan：**Step 1（C5 渲染·非红线·最大见效）→ Step 3（C 分组·最便宜）→ Step 2（C6·eval-first 红线）→ Step 4（B srcId）→ Step 5/6（T9/C7）**。
4. **承重三不动**（diagnose prompt / harness orchestrate / ChatRequest）·改前先扩 eval·每次只改一处·不派 subagent（承重走主线程）。
