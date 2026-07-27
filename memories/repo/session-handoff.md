# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月27日收工（**CB-09 EMC 架构重构 9 模块 9/9 全落地** 5.231-5.240）| 分支 `main` | **本次 commit+push**

## 当前节点：CB-09 9 模块全落地·明日测试飞轮（开 plan·用户主导）

今日（07-27）整日推进 **CB-09 EMC 架构彻底重构**——9 大模块实施 **9/9 全 ✅**（D001-D040 全落地）。**明日用户主导**：根据新架构**更新测试飞轮机制 + 模拟测试内容**（开 plan）·9 模块测试围绕新飞轮展开（用户约定「9 模块做完一起验」·今日全做完·明日飞轮齐验）。

## 新 EMC 架构全景（明日飞轮须覆盖的路径）

| 路径 | 改造后 | 测试要点 |
|------|------|------|
| **三阶段 diagnose** | 0LLM 规则选型（select_candidates 97%）→ Flash 极瘦填卡（1.85KB·<5s）→ Pro 复合计划（chain） | 单候选问走 Flash·复合问走 Pro chain·概念问走 general 短路 |
| **追问胶囊** | 动态 {label,level,skill,params}·L1 跳 Flash <2s / L2 Pro 确认 5-8s | 答案后追问区出胶囊·点击 L1/L2 路由·R5 剔无效 |
| **质量防线** | applyQualityDefense 全代码 <20ms（L1 谎报标注 + R1-R8 + L3 降级） | 谎报图层→标注·矛盾→降级·空答→兜底 |
| **Pro 动态 chain** | 复合→build_plan_prompt 产 chain→runChainPath 动态消费 | 复合问（如「西陵区范围内密度分析」）→ clip→density |
| **契约单一源** | tool_contracts.py → 派生 prompt/SKILL_DEFS/validate | 加工具只改一处·CI 守护 |

详：[emc-fix-progress §一 9 模块矩阵](../docs/emc-fix-progress.md) + [revision-log §5](../docs/revision-log.md#L226)（5.231-5.240 逐条）。

## 今日已 commit（5.231-5.240 + 收尾·branch main·**本次 push**）

- **fd34191** 5.240 模块六 D026 prompt 全派生 contracts（9/9 收尾·AGENT 手写规格→指针）
- **a436f91** 5.238 模块七 L3 panel_source 全核查（D027·31 处 Resolved）
- **0dc9a4b** 5.239 模块八 CPD 收尾（D031 胶囊实现 + D034 偏好埋点）
- **c1fc977** 5.237 轮次3c Pro 推理 + 动态 chain（D009+D012·Phase C）
- **885bde1** 5.236 轮次3b Flash 瘦身（D006·Phase B·45.8KB→1.85KB）
- **5b16f49** 5.235 轮次3a 0LLM 候选选择器（模块九·Phase A·97% 命中）
- **d801cd7** 5.234 轮次2b 追问胶囊三级 + R5/R6/R8
- **4a31631** 5.233 轮次2a finalStep 极瘦（17KB→1.86KB）
- **a3cdeca** 5.232 轮次1 删旧R+R + 质量防线三层 + **4c2d783** 5.231 P0 消矛盾
- **893bda3** docs emc-fix-progress 九模块矩阵（监控卡）
- **收尾** todo/revision-log/emc-fix-progress 按新架构清理 + 上周归档 `docs/todo-archive/2026-07-20_2026-07-26.md`

## 下会话：明日测试飞轮（用户主导·开 plan）

- **用户将开 plan**：根据新 EMC 架构更新测试飞轮机制 + 模拟测试内容。AI 进 plan mode 配合设计。
- **飞轮是 9 模块齐验载体**：覆盖三阶段路径（单候选/复合/胶囊/防线/概念问）+ 信号链 + 断言 + 报告 + 闭环。
- **参考旧评估**：[test-flywheel-audit-2026-07-24](../.codebuddy/reports/test-flywheel-audit-2026-07-24.md)（5.1/10·三处闭环断裂·H/M/L 清单·新架构下需重审）。
- **pytest 基线**：214 passed + 5 skipped（零回归·CI 可跑）·eval_template_flash 保留测兜底路径（大 prompt 不变）。

## 留用户验证 / 未决

- **9 模块浏览器齐验**（明日飞轮就绪后）：① 单候选「做核密度分析」<5s 出图 ② 复合「西陵区范围内密度分析」Pro plan 5-10s 出图 ③ 胶囊 L1 <2s/L2 5-8s ④ 诚实防线（谎报/矛盾/R5）⑤ 概念问 general 短路。
- **明早办公室大讨论**（用户主持·议题未告知）。
- **KDE 去 3D 连带**（备查·非大讨论主题）：「情绪地形」命名 / 总体情况栏 1 卡 / EMC generateTerrainForAI 仍 3D / Grid 3D 收口 / 按钮文案空格。

## 红线 / 纪律（下会话守）

- **承重三不动**（改前先扩 eval·每次一处·不派 subagent）：diagnose prompt（`build_diagnose_prompt`/DIAGNOSE_TEMPLATE·eval-anchored）/ harness orchestrate 主循环 / ChatRequest schema。
- **新架构红线**：Phase B/C 极瘦 prompt（FILL_CARD/PLAN）+ select_candidates 是新 gate·改前守 eval；卡 schema 8 字段不变（parseDiagnoseCard 归一）。
- **最高纪律**：EMC 复用 Toolbox 参数面板（ForAI=dialog 镜像）·tool_contracts.py 单一源·禁 emoji（[OK]/[ERR]）。

## 恢复指引（新会话·办公机）

1. `git log --oneline -12` 对账（fd34191 5.240 → a3cdeca 5.232·9 CB-09 commit + docs + 收尾）。
2. 读 [emc-fix-progress.md](../docs/emc-fix-progress.md) §一 矩阵（9/9 · 验什么）+ §四 时序。
3. 读本卡「新 EMC 架构全景」+ [todo.md](../docs/todo.md) 2026-07-28 段（明日飞轮计划）。
4. 明日用户开题「测试飞轮」→ 进 plan mode 设计新飞轮 + 模拟测试内容（围绕三阶段 + 胶囊 + 防线 + chain）。
5. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
