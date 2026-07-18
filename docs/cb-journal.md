# CB Journal（Catch-Ball 轨迹）

> 我方（Claude Code）与第三方评价（`docs/SCAN_DeepSeek.md`，DeepSeek V4 Pro）的多轮 catch-ball 对话轨迹。
> 按轮追加不覆写（区别于 session-handoff 的"覆写当前节点"）。每轮四节：① SCAN 摘要 ② 我方反评价 ③ 行动 ④ 状态/新发现。
> 反评价标尺：agree=证据支持/我方漏掉；disagree=用错标尺/事实错误；partial=方向对细节偏。承重红线（tracker 编号连续/diagnose 永不动/四态）不接受简化。

---

## CB-1 · 2026-07-18（首轮）

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

**待执行**：
- [ ] **Tier 0.1 删 3 僵尸**（ui_components/layer_registry/map_engine）—— 安全分类器拦了 `git rm`（Irreversible Local Destruction），**待用户显式授权**（文件 git-tracked 可恢复，零活引用已核）
- [ ] Tier 1：§0 树 refresh / retired.md / tracking-progress 对账 / `?e2e=1` 去生产化 / C6 补 3
- [ ] Tier 2：db.py 批量插 / 前端 JS 单测基建 / 9⬜ 埋点细化 / vendor 本地化核查
- [ ] zonal_stats latent bug 修（n_dom/n_elem 补充失效，需先确认消费方）

### ④ 新发现（SCAN 之外，清理中挖出）
- **zonal_stats latent bug**：原代码想补充 `n_dom_*/n_elem_*` 占比列，但 discover 循环遍历 `rows.columns`（_props_df 只返请求列 → 永不含 n_dom_）→ 补充**从未生效**。SCAN 只看到"冗余"，未发现"失效意图"。本轮清理保持原行为（移除死循环+冗余），bug 单独登记待修。

### 状态
`open` —— Tier 0.1 删除待用户授权；Tier 1/2 待用户择序。双模型闭环：本轮 Claude 执行 → 待 DeepSeek 二次扫描对比验证。
