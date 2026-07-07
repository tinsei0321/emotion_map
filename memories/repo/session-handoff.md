# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月07日 23:30 | 分支 `main` | HEAD=本批 commit（待 push）

---

## 当前节点：AI 问答质量优化·审查层已接通但质量仍不达标

### 承前（5.35 审查层接回 ReAct）
- 5.34 Agent Loop 重构时审查层"暂移"，5.35 把 review.py 六条 checklist 接回：草稿→Flash 审查员（✓/△/✕）→不达标带 hints 自动 revise 重写 1 轮。
- **后端**：`review.py review_answer()`（Flash+json_mode，失败降级不阻塞）+ `_parse_review_json` 容错 + `REVIEWER_MODEL` 旧 ID→`flash`；`prompts.py REVISE_TEMPLATE`；`schemas.py` phase 加 review/revise + draft/review_hints；`router.py` review（非流式单帧 SSE）/revise（流式）分支。
- **前端**：`api.js` onReview 透传；`stages.js` reviewStep/reviseStep + parseAgentStep 强化（fence/尾逗号/二次提取）；`harness.js` 接 review→revise + 降级回退 + tool_history 压缩；`panel.js` 审查状态区 + Flash reason 对齐 + Pro 分段 + [ref:] 校验 + trace 持久化。
- **验证**：import/语法/纯逻辑/pytest 通过；**E2E 未跑**（需 API Key + 聚合层）。
- **承重**：panel.js 不耦合 map/state / REVIEW_CHECKLIST key 稳定 / revise 1 轮不递归 / 审查失败降级不阻塞 / V4 模型 ID（v4-pro/flash，勿回旧 ID）。

### ⬜ 明日继续：AI 问答质量问题排查与修复（质量达标前不开 UI 重做）

**用户反馈**：5.35 后"还是有很多问题存在"，但**未细说具体问题**。明天首要任务是**定位问题根因**，而非盲目改。

**排查步骤**：
1. **先跑 E2E 观察**：`serve.py` + 生成聚合层 + 问"哪个片区最需优先更新？"，完整走 agent loop → 草稿 → 审查六条 → revise，亲眼看哪环出问题。
2. **问用户具体不满意点**：回答太长/太泛？数据数值错？归因 4×5 不准？审查没抓住真问题？revise 越改越差？工具 observation 数据不准？Pro vs Flash 差异？
3. **可疑点**：
   - 审查员 Flash 是否够严？六条 verdict 是否准？revise_hints 是否具体可执行？
   - revise 重写是否真改善，还是换种方式重复问题？
   - parseAgentStep 降级回退是否频繁触发（模型输出非 JSON）？
   - tool_history 压缩后是否丢关键信息致 final/revise 依据不足？
   - MANIFESTO/prompt 是否让模型真懂情绪地图（5.34 已强化，但可能仍不够）？
   - 工具数据（query_zone_stats/query_attribution）是否准确反映聚合层？
4. **逐项修到达标**，再开 AI 问答 UI 重做。

**暂不做**（用户明确）：AI 问答 UI 重做、其他修改——等质量达标再开。

### 承重 memory 索引
- 本轮：`ai-qa-harness-subsystem`（已更新为审查层接回）/ `verify-with-webapp-testing-skill`（E2E 验证用）/ `no-routine-playwright-verify` / `maintain-revision-log` / `todo-revision-log-sync` / `chinese-all-deliverables` / `push-not-redline` / `timestamp-no-weekday` / `no-handoff-on-routine-commit`（本卡因用户说"交接"才覆写）
- 前会话：`paint-inplace-swap-view` / `sticky-hover-priority` / `loc-anchor-by-data-not-coords` / `kde-loadbearing-logic` / `martin-ui-redesign` / `three-page-architecture` / `topic-table-frontend-sync` / `generate-grid-exclusive-vs-viewmode` / `view-data-conclusion-sync`

## 当前状态
- 分支 `main`。工作树：5.35 代码（9 文件）+ revision-log 5.35 + todo 5.35 + 本交接卡，**待 commit+push**。
- serve 已停。未做：AI 问答 E2E 验证 + 质量问题排查（明日）。

## 新会话 prompt（复制即用）
```
续 main。读 memories/repo/session-handoff.md（AI 问答质量优化·审查层已接通但质量未达标节点）。

任务：5.35 把审查层接回 ReAct 管线（review.py review_answer + router review/revise + 前端审查状态区 + revise 重写），但用户反馈"还是有很多问题存在"，未细说。明天首要**定位问题根因**：

1. 先跑 E2E 观察：serve.py + 聚合层 + 问"哪个片区最需优先更新？"，看 agent loop→草稿→审查六条→revise 哪环出问题。
2. 问用户具体不满意点（回答太长/数据错/归因不准/审查没抓问题/revise 越改越差/工具数据不准/Pro vs Flash）。
3. 可疑点：审查员 Flash 够不够严 / revise 是否真改善 / parseAgentStep 降级是否频繁 / tool_history 压缩丢信息 / MANIFESTO 是否让模型真懂 / 工具数据准确性。
4. 逐项修到达标。

质量达标前**不开** AI 问答 UI 重做（用户明确）。

承重：panel.js 不耦合 map/state / REVIEW_CHECKLIST key 稳定 / revise 1 轮不递归 / 审查失败降级不阻塞 / V4 模型 ID（v4-pro/flash 勿回旧 ID）。详 revision-log 5.35 + memory ai-qa-harness-subsystem。

计费按调动次数，工作方式见 ~/.claude/CLAUDE.md（不派 subagent、批量并行、给推荐不穷举）。前端验证用 webapp-testing skill（非 Playwright），默认交付肉眼验，控制流/数据流/bug 才上。时间戳写"MM月DD日 HH:MM"（不写星期几）。
```
