---
description: Catch-Ball 反评价编排 — 新 SCAN 报告到达后，读 RULES+KNOWLEDGE → 深读 SCAN → 逐条反评价（agree/disagree/partial）→ 行动 → 写 cb-journal+入库。主线程跑，不派 subagent。
argument-hint: "(可选) CB 轮次号如 02；省略则自动选最高未反评价轮"
---

Catch-Ball（CB）反评价编排流。第三方 DeepSeek 扫描产出 `docs/catch-ball/SCAN_DeepSeek_{NN}.md` 后，本命令编排我方反评价闭环。**双模型闭环**（RULES §1.4）：SCAN（第三方）→ 本命令（我方反评价+行动）→ 下一轮 SCAN（对比验证）。

参数 `$ARGUMENTS` 给轮次号（如 `02`）则处理该轮；省略则自动选**最高未反评价轮**（cb-journal 无已填 `## CB-{NN}` ②③ 的最大 NN）。

## 步骤

1. **定轮**：`$ARGUMENTS` 给 NN → 用之；否则 `glob docs/catch-ball/SCAN_DeepSeek_*.md` 取最大 NN，读 cb-journal 确认其 `## CB-{NN}` ②③ 未填（=未反评价）。
2. **载入 RULES + KNOWLEDGE**（注入标尺+记忆库）：
   - `docs/catch-ball/RULES.md`：六轴评分 / 反评价三分法 §3.2 / 承重红线 §3.3 / journal 四节 §4.2 / 报告模板 §4.4。
   - `docs/catch-ball/KNOWLEDGE.md`（**CB 记忆库**）：§1 承重合并 / §2 项目语境卡片 / §3 SCAN 标尺纠正模式 / §4 decline 模式库 / §5 轮次溯源。
3. **载入上下文**：`docs/catch-ball/cb-journal.md`（历史轮次，esp. 目标轮 ① 若第三方已预填）、`docs/catch-ball/retired.md`、`memories/repo/session-handoff.md`（当前承重）。
4. **深读目标 SCAN**：`SCAN_DeepSeek_{NN}.md` 全文（§0 回顾 / §1 扫描 / §2 评价 / §3 建议 / §4 讨论 / 附录）。**禁编辑此文件**（第三方专属，只读）。
5. **反评价（②，结构化表）**：逐条 SCAN 建议/讨论点 → `{agree/disagree/partial + 证据 + 行动}`。执行 **KNOWLEDGE §6 Auto-Check 清单**（4 项，数据驱动——清单在 KNOWLEDGE.md §6，不在此硬编码；CB-03 建议2）：
   - **承重红线 auto-flag**（KNOWLEDGE §1）：建议触碰 tracker 编号连续 / diagnose 永不动 / 四态 / L0 购买 / EMC 委托主 Toolbox / aggregate 别名静默零 → 自动 disagree（撞红线）。
   - **verify-before-accept**：SCAN 代码级指控（"X 用 iterrows""Y 零引用"）**先 Read/Grep 核实再 accept**（CB-01 db.py iterrows 实为 executemany 之训）。
   - **no-consumer → wontfix**：修复若无人消费（如 zonal_stats latent bug）→ wontfix 不盲修。
   - **已知 SCAN 模式套结论**（KNOWLEDGE §3）：建议匹配已知倾向（基于 AGENTS.md 理论模型判运行时 / 优化前不查活引用 / 完成度把"接口预留"计"已实现" / 把 sim 当风险 / 官方完备性质疑 4×5）→ 套已知结论，不重推。
6. **行动（③）**：agree 项落实（fix/optimize/discuss）；守承重；退役文件 → 追加 `retired.md`；`py -m pytest tests/ -q` 验零回归（RULES §6.5）。
7. **写 journal + 入库**：
   - 填 `cb-journal.md` 的 `## CB-{NN}` 四节（① SCAN 摘要——第三方已预填则保留；② 反评价；③ 行动；④ 状态/新发现；按轮追加不覆写）。
   - **若本轮有新 learning**（新承重 / 新 SCAN 模式 / 新 decline 类型）→ 同步追加 `KNOWLEDGE.md`（按主题蒸馏，标 `← CB-{NN}`）。
8. **同步**：`docs/revision-log.md` §5 加 5.NNN bullet + `docs/todo.md` 当日段（守 maintain-revision-log / todo-revision-log-sync 置顶同步）。
9. **汇报**：结论先行——X agree（已 act）/ Y disagree（附 reason 落 KNOWLEDGE §4 模式）/ Z partial / pytest 状态 / 待 push。

## 输出格式

- 反评价表：`| SCAN 建议 | 判定（agree/disagree/partial）| 证据/行动 | decline reason（若 disagree）|`
- 末尾：`CB-{NN}: X agree / Y disagree / Z partial — pytest PASS/FAIL — 待 push`
- disagree 项的 reason 必落 KNOWLEDGE §4 五类之一（用错标尺 / 事实错误 / 撞红线 / 无消费方 wontfix / 前提不成立）。

## 守则

- **不派 subagent**（主线程跑）；**只 commit 不 push**（用户手动）。
- **禁编辑 `SCAN_DeepSeek_{NN}.md`**（第三方专属，只读）；cb-journal / retired / KNOWLEDGE 我写。
- **反评价客观有据，不谄媚第三方也不为反对而反对**——agree/disagree/partial 均附论据。
- **承重红线不接受简化**（KNOWLEDGE §1）。
- 交付物中文（代码/路径英文）；专业词+通俗解释（用户是初学者）。
- 守 CLAUDE.md 全部铁律（禁 emoji / safe_print / tracker SOP 等）。

**零被动开销，手动触发**——新 SCAN 到达时 `on_session_start` hook 打印一行 `[CB] … — 运行 /cb NN 开启` 提示（不自动跑，CB 需主线程判断）。这是「上下文连贯纪律」+ 双模型闭环的一环。
