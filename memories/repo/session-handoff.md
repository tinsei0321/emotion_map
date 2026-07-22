# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月22日收工（**P0 测试铺底 + Smart Agent/Dumb Tool 内核 + P1 尺度诚实 三项落地；下一步 P2 引擎 G1-G4**）| 分支 `cpd`

---

## 当前节点：P0/内核/P1 三项落地；下一步 = P2 引擎 G1-G4

### 本会话做了什么（分支 cpd，三个 commit 已 push + 1 待 push）

1. **P0 测试铺底**（5.176，commit d4b6413 + cda7a45，已 push）：
   - `docs/emc-test-cases.md` catalog 4→11（地基行为 5-8 / 落地 ⬜ 用例 2·3 / 登记 9·10·11 + 组合场景回归元则）。
   - 6 browser 脚本全绿（复用 emc_helpers）：`test_cpd_collapsed_welcome`/`exit_badge`/`emc_height_adapt`/`history_clear`/`domain_lens_threading`/`drift_fence`。
   - `tests/browser/lib/emc_helpers.py` 补：`emc_session` 上下文管理器（**进程树 taskkill 清理**修 uvicorn 孤儿）+ `read_predicate`/`wait_predicate`（A1 谓词范式·G1）+ `ChatRequestCapture`（/chat domain_lens）；open_emc `#lp-upload` visible→**state=attached**。
   - plan §八 P0 打磨：交叉链接吸收 [GUIDANCE_E2E-k3.md](../../docs/catch-ball/GUIDANCE_E2E-k3.md) 两项增量（A1 谓词测试 + 组合场景回归），核心 6 决策不动。
2. **Smart Agent/Dumb Tool 开发内核沉淀**（5.177，commit 7b51c3c，已 push）：
   - 用户提 EMC 架构重构三点 → 评估结论：**不需推倒重来**（现状已是内核成熟实现）。
   - 用户定调凝练成内核词条「Smart Agent, Dumb Tool」（聪明只在两端·执行做最笨最稳中间件·编排器机械接线）。
   - 沉淀：[CLAUDE.md](../../CLAUDE.md) 顶层新节（三角色+四铁律+新功能判据）+ 新建 [docs/copilot-architecture.md](../../docs/copilot-architecture.md)（四层骨架+三铁律+EMC↔通用术语对照+领域驱动策略+落地模板）+ ai-qa-design 双链 + harness orchestrate 注释（逻辑零改）+ memory `smart-agent-dumb-tool`。
3. **P1 尺度诚实**（5.178，commit 45751b0，**待 push**）：
   - [ai_qa/review.py:50-54](../../ai_qa/review.py) `scale_paradigm_fit` desc 强化（**U7 三态**：微观精确问题须声明「宏观非精确」+ 替代趋势；无声明→fail / 有声明无趋势→warn / 齐全→pass；机制已就绪——客观项 fail→revise）。
   - docstring 漂移修正（review.py + `__init__.py` 六条→七条）。
   - 灰度降级：episodes.jsonl 63 条全宏观/GIS，**微观问题 0 命中** → 灰度待数据；用例 9 更新（desc 已落地 ⬜→🔄）。
   - 承重回归 pytest 207 passed（eval 未破）。

### 下一步：P2 引擎 G1–G4（v1.0 plan §八 P2，CPD 核心实施）

**G1（独立 ship，含最小可点闭环）**：
- 新建 `frontend/js/ai_qa/cpd-guide.js`（`deriveGuidance` + 特征向量真值表 + subscribe + **依赖注入 init** `initCpdGuide({getLastExit, isStreaming})`，零 import panel.js）。
- [panel.js](../../frontend/js/ai_qa/panel.js) `send()` finally dispatch `cpd:turn-ended {exit,turnId,intent}`（**H1 修复**：守卫 `settled` 非 `exit!==undefined` + 单调去重 `turnId > lastProcessed`）+ 删 `Ctrl+Shift+G` 测试代码（`_setupCpdBar`）接引擎 + 光环 click 最小 CTA。
- [cpd-state.js](../../frontend/js/ai_qa/cpd-state.js) 导出谓词（hasImport/hasRange/hasAnalysis/hasVisibleEmotionLayer，不改 deriveState 逻辑；S4 信号 `.aiq-conclusion`→`.aiq-exit-badge`）。
- 颜色全 theme var（含光环 `--emc-halo-*`，ai_qa.css:431 硬编码 hex→var）。
- **G1 三硬用例**：F5 恢复引导 / 切会话恢复 / abort 不误推；用例 10（A1 谓词真值）+ 11（H1 不冻结）启用。
- **G2** banner + CTA 调度 / **G3** 全状态 + 绿色摘要条 + timeline/compare 轻编排 / **G4** 抛光 + Playwright 回归。

### 承重（必守）
- **调用次数优先**（全局唯一权威）：默认主线程 + 会话切分 + subagent 仅大宗隔离。**不派 Explore/Plan subagent**（覆盖 plan mode 默认）。批量并行 / 合并修改 / 给推荐不穷举 / 不跑非必要验证（Playwright 仅控制流/数据流风险）。
- **diagnose prompt 永不动**（保 eval）/ 四态出口不动（小写五值 `result/gap/partial/ask/drift` + general 短路无 exit）/ harness orchestrate 主循环 / parseAgentStep 抗漂移 / review 七条骨架 / tracker 不动 / curState 纯客户端。
- **CPD plan v1.0 已定稿**（CB-CPD 专轨收尾）；实施中若发现 plan 层新问题再开 CB-CPD-04。
- **Smart Agent/Dumb Tool 内核**（新，CLAUDE.md 顶层节）：会推理→Smart / 纯执行→Dumb / 协调→编排器；Tool 越 dumb 越好（不内嵌 LLM）；编排器确定性（不调 LLM）。
- **EMC 颜色全走 theme var**（含光环渐变 `--emc-halo-*`）；**色名同步色带**（从 `--geojson-color-emotion-very-*` 派生，无"深红"）；浮层 left 随锚点自适应（勿写死）。
- 平时**只 commit 不 push**（用户手动 push）；收工/明确说 push 时才 push。

### 关键文件
- **`docs/cpd-core-plan.md`**（v1.0 定稿，权威 + §八 P2 G1-G4 roadmap + 定稿声明）
- **`docs/copilot-architecture.md`** + **CLAUDE.md「AI·Copilot 开发内核」**（Smart Agent/Dumb Tool，P2 编排器理念参照）
- `ai_qa/review.py`（P1 已改 scale_paradigm_fit U7 三态；七条骨架）
- `frontend/js/ai_qa/{panel.js,cpd-state.js,harness.js,tools.js}`（P2 G1 落点）
- `tests/browser/`（6 脚本 + emc_helpers；G1 用例 10/11 待启用）
- `docs/emc-test-cases.md`（11 例 catalog）

### 本会话 memory 沉淀（~/.claude，机本地）
- `browser-test-stability-gotchas`（进程树清理/attached 等待/exit 软断言三坑）
- `smart-agent-dumb-tool`（开发内核词条）

---

## 新会话 prompt（CPD v1.0 实施 P2 引擎 G1，复制即用）

```
接续 cpd 分支 CPD 核心 plan v1.0 的 P2 引擎 G1 实施。
读：docs/cpd-core-plan.md（v1.0 §八 P2 G1 + §4 特征向量真值表 + §4.3 turn-ended H1 修复 + §九 关键文件）+ CLAUDE.md「AI·Copilot 开发内核（Smart Agent/Dumb Tool）」（编排器确定性铁律）+ docs/copilot-architecture.md（编排器理念参照）+ frontend/js/ai_qa/{panel.js（_setupCpdBar Ctrl+Shift+G 测试代码 + send finally 段）,cpd-state.js（deriveState + 谓词待导出）,harness.js（orchestrate exit 裁定）}。
任务：P2 G1 = 新建 cpd-guide.js（deriveGuidance 特征向量真值表 + 依赖注入 init，零 import panel.js）+ panel.js send finally dispatch cpd:turn-ended（H1 修复 settled 守卫 + 单调去重）+ 删 Ctrl+Shift+G 测试接引擎 + 光环可点 CTA + cpd-state.js 导出谓词（含 M2 hasVisibleEmotionLayer 判情绪性）+ 颜色全 theme var（光环 --emc-halo-*）+ G1 三硬用例（F5/切会话/abort）+ 启用 emc-test-cases 用例 10/11。
承重：调用次数优先 / 不派 subagent / 只 commit 不 push / diagnose 与四态出口不动 / plan v1.0 已定稿不再 CB 迭代（除非实施发现 plan 层新问题）/ Smart Agent·Dumb Tool 内核（编排器确定性不调 LLM）。
```
