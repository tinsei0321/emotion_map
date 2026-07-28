# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月28日收工（**5.242 EMC 链路系统性修复·选型数据感知 + 9 bug·融合 DeepSeek 评估**）| 分支 `main` | **本次 commit+push**

## 当前节点：9 模块验证暴露链路缺陷 → 系统性修复 → 待飞轮齐验

今日（07-28）：用户验证 9 模块后报「剪裁西陵区」失败 + 「无变化」+ 「基本功能丧失」。经诊断 + DeepSeek 6-agent 代码评估（[EVAL_REPORT_unified_2026-07-28](../docs/catch-ball/emc-arch-deepdive/EVAL_REPORT_unified_2026-07-28.md)），定位**系统性根因**并修复。

## 今日已 commit（5.241 + 5.242 · branch main · **已 push**）

- **0de8cbf** 5.242 **EMC 链路系统性修复（选型数据感知 + 9 bug·融合 DeepSeek 评估）**
  - **根因**：`select_candidates(question, None)` context 硬 None → 0LLM 选型**数据盲**（不知用户加载点还是面）→ 剪裁面层误路由 clip（要点·硬失败）。`TOOL_GEOMETRY_REQUIRE['clip']` 误设 None（Phase A 漏设·应 'point'）。
  - **修复 11 项**：S1 数据感知（layer_meta {has_point,has_polygon} 端到端接线）+ clip 几何表修正（None→'point'）+ stale multi 移除 + 剪裁歧义词（clip+extract→数据裁决）+ 空候选→request_upload + S3 clip 失败智能建议 extract + S4 ensure_zone + S5 F_008 碰撞 + S6 capsule intent 动态 + S7 正则统一 + S9 chain hasRows + S8 FILL_CARD 兜底。
  - **实测**：剪裁+polygon→[extract_feature] / 剪裁+point→[clip,extract] / density+无点→[]→request_upload。
- **7356d7a** 5.241 selector trigger 补「剪裁/裁剪」+ 诊断「无变化」根因（uvicorn 需重启）

## 新 EMC 架构全景（明日飞轮须覆盖的路径）

| 路径 | 改造后 | 测试要点（飞轮·覆盖「数据×问句」组合） |
|------|------|------|
| **三阶段 diagnose** | 0LLM 规则选型（select_candidates·**数据感知**·has_point/has_polygon）→ Flash 极瘦填卡（1.85KB·<5s）→ Pro 复合计划 | 单候选问 + 有点→Flash / 无点→request_upload / 复合→Pro chain |
| **追问胶囊** | 动态 L1 <2s / L2 Pro 确认 5-8s | 答案后追问区出胶囊·点击路由 |
| **质量防线** | applyQualityDefense 全代码 <20ms | 谎报标注 / 矛盾降级 / R5 剔无效 |
| **Pro 动态 chain** | 复合→Pro 产 chain→runChainPath（hasRows·分析型不误判） | 复合问→Pro plan→chain 执行 |
| **数据感知路由** | 剪裁+polygon→extract / 剪裁+point→clip / density+无点→request_upload | **核心·飞轮必测**：同问句 + 不同数据 → 不同路由 |

详：[emc-fix-progress §一 9 模块矩阵](../docs/emc-fix-progress.md) + [revision-log §5](../docs/revision-log.md#L226)（5.242）+ [DeepSeek EVAL_REPORT](../docs/catch-ball/emc-arch-deepdive/EVAL_REPORT_unified_2026-07-28.md)（8 bug + 10 风险 + 15 优化建议·P0 已修·P1 部分修·P2 待续）。

## 下会话：测试飞轮更新（用户主导·**开 plan**）

- **用户将开 plan**：根据新架构更新飞轮机制 + 模拟测试内容。AI 进 plan mode 配合设计。
- **飞轮核心**：覆盖「数据×问句」组合测（不只关键词）·DeepSeek 评估报告 §十一（缺失测试 7 项）可参考。
- **DeepSeek P2 建议**（S10-S15·可选）：工具几何能力矩阵自动路由 / contracts 自动派生 / Flash hit-rate gate 阈值评估 / `_quickIntent` 质量防线 / while-loop finalStep 降级 / density 维度分歧追问。
- **pytest 基线**：219 passed + 5 skipped（零回归·CI 可跑）。

## 留用户验证 / 未决

- **重启 serve + 硬刷**（5.242 新代码须重启 serve 才生效）→ 重测「剪裁西陵区」（只有面）→ 应走 extract_feature·不报"无点层"。
- **明早办公室大讨论**（用户主持·议题未告知）。
- **KDE 去 3D 连带**（备查）：命名 / 栏卡 / EMC generateTerrainForAI 仍 3D / Grid 3D 收口。

## 红线 / 纪律（下会话守）

- **承重三不动**（改前先扩 eval·每次一处·不派 subagent）：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema。
- **新纪律**：选型须感知数据（`select_candidates(question, layer_meta)`·layer_meta 从 getLayers 推导 has_point/has_polygon）·**question-only 选型是架构债·已修**。
- **承重 Python 改动后须重启 serve.py**（uvicorn 无 --reload）·commit 后显式提醒用户重启。
- **最高纪律**：EMC 复用 Toolbox 参数面板·tool_contracts.py 单一源·禁 emoji。

## 恢复指引（新会话）

1. `git log --oneline -5` 对账（0de8cbf 5.242 / 7356d7a 5.241 / 66f7b12 收工·docs）。
2. 读 [DeepSeek EVAL_REPORT](../docs/catch-ball/emc-arch-deepdive/EVAL_REPORT_unified_2026-07-28.md)（8 bug + 10 风险·P0 已修·P1 部分修·P2 待续）。
3. 读本卡「数据感知路由」+ todo 2026-07-28 段。
4. 明日用户开题「测试飞轮」→ 进 plan mode 设计新飞轮（围绕三阶段 + 数据感知 + 胶囊 + 防线 + chain）。
5. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。**改 Python 后重启 serve**。
