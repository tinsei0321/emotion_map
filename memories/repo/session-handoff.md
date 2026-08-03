# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月03日（**CB-12 闭环：B3-verify-05 23/26 88.5% 历史最佳 + 多步问 RST-L06 收敛 + while-loop 根治 + pro 0**）| 分支 `fix/emc-buglog` | **已 push**
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md` + `OFFICE.md`

## 当前节点：CB-12 闭环 — B3-verify-05 全量重测 88.5% + 多步问 RST-L06 收敛

08-02→03 大跨轮：用户体验四类依据 → G0-G6c 实施 → B3 两轮定案（glm trace 铁证推翻"API 慢"·根因 = while-loop × pro/旧模型）→ trace 工具 + pro 停用 → while-loop 根治（**glm gate 连锁被 localStorage 铁证推翻·Codex recover 缺口正确**·recover 扩展触发）→ 多步问修复（4ea8b6d+0407f78+6d2e609）→ **B3-verify-05 全量 23/26（88.5%）历史最佳·RST-L06 多步问 PASS·CB-12 闭环**。

## 今日已 commit（fix/emc-buglog · **已 push**）

| commit | 内容 |
|---|---|
| `8e24294` | 文档：CB-12 多步问修复评估报告入库（Codex/glm·微调依据） |
| `bb96028` | 文档：CB 恢复记忆卡（Codex/glm 换环境）+ 交接卡上午详细计划 + context-map 登记 |
| `6d2e609` | 多步问微调（Codex+glm）：`_hasSeq` 收紧 + Pro chain 前置 + recover 链前置 |
| `13084cc` | 文档：Codex/glm 2 项确认 + 多步热力图评估报告入库 + 交接卡更新 |
| `0407f78` | 多步问链前置补丁：seq-chain pre-check before single-tool + boundary derive |
| `4ea8b6d` | 多步问修复 + Codex/glm 边界：clip_density trigger widen + chain trigger + `_planned>0` + `_GEO_TOOLS` density + slice 200 |

> 注：交接卡旧版「今日已 commit」列表（`b349fcd`/`a3a4486` 等）与实际 git log 不符，漂移对账后以 git 为准覆写。

## 关键架构（下会话须知道）

- **B3 根因定案**：B3 大失败 = **while-loop 退化（a04a714 stripped 阈值 3→2 退化 + zonal 无前置强制）× pro/旧模型多轮**·非 API 慢（用户 key 正常·探针 0.9s·用户质疑澄清）。修复 = 阈值回退 3→2 + 词边界（slice(2)）+ zonal 前置检查（derive 成功才强制）+ **pro 停用**（flash 足够·三层守卫）
- **trace 取证纪律**（用户要求·glm 习惯）：根因分析第一动作 = `py tools/trace_query.py --stats`（数 **F_002 agentStep/F_003 final/F_005 FC·非 F_001** 公共出口）·跑测试带 `EMOTION_TRACE_SESSION=<组>-<批>`·trace.log 轮转 200MB·CB RULES 1.2 步骤 0
- **pro 停用**：UI disabled + `_thinkMode` 强制 flash + finalStep 守卫·ctx.model 恒 flash
- **多步问修复（B3 收敛）**：链前置 + clip_density 触发器放宽 + boundary derive + recover 链前置（4ea8b6d+0407f78+6d2e609）·RST-L06 断言（tools 含 clip+density）·**CB-12 闭环**
- **搜索/连问**：G6b 素材注入（进 ctx.context 走 finalStep+防线·非旁路）·G6c 分句 ≤2 复用 orchestrate
- **尺度出口差异化**：finalStep 尺度约束 + R10/R11 防线·general 跳过（skipScaleDefense）
- **体检套件**：`py tests/browser/test_link_checkup.py`（20 例·四件套断言·回归门）·B3 留 API 好时段

## 待续项（下会话从这继续）

- **【今日】CB-13 评估**：发 B3-verify-05 结果给 Codex/glm 组（已发恢复卡·让他们检查 PRM-08/CPD 残余 + 多步问修复确认）→ 反评价 → 行动
- **PRM-08 compare 链路**：B3-verify-05 fail·tools=extract_feature 单工具·boundary[ERR]·疑 compare 路由退化（应 zonal×2 两区·实际只 extract_feature）·backlog
- **CPD-L01/L02**（CPD 导游·既有 backlog·引导态 hint 未推 range/analyze）
- **backlog**：MOD_PLACE 渲染风暴（~94 次/秒·Codex 观察·潜在性能）+ MOD_LLM.F_002 fallback 79 次含 3 ERR
- 时间轴 `_time_manifest.json` 404（低风险）
- 发版候选评估（B3 88.5% 达标上沿·整体评估）

## 测试基建

- pytest：**225 passed**
- 飞轮：`py tests/browser/flywheel_audit.py --batch B3`（**带 `EMOTION_TRACE_SESSION=B3-<批>`**·跑完 `trace_query --stats --session` 附报告）
- 体检：`py tests/browser/test_link_checkup.py`（20 例·回归门）
- 根因分析：`py tools/trace_query.py --stats/--id/--time/--session`（第一动作）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前 CB 轮次：CB-12 **闭环**（B3-verify-05 23/26 88.5% 历史最佳·多步问 RST-L06 收敛·while-loop 根治·pro 0）· 下一轮 CB-13（让两组检查残余 + 确认多步问修复）
- **双阵营**：claude组（开发主）+ Codex + glm组（评估·**trace 取证功臣**）
- 反评价轨迹：`docs/catch-ball/cb-journal.md`
- 恢复卡：`docs/catch-ball/_handoff/CB恢复记忆卡_2026-08-03.md`（两组换环境用）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / **`@track()` 签名 / `_TRACKING_REGISTRY` 格式**（改前先扩 eval·每次一处）
- **trace 取证**：根因分析先 `trace_query --stats`（F_002/F_003 非 F_001）·推断只作假设
- **EMC 产物不临时创造样式**；不动 FC prompt；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**；commit 后不 push（用户手动 push）

## 恢复指引（新会话）

1. `git log --oneline -8` 对账（最新 `8e24294` + 收尾 commit）。
2. 读本卡「关键架构」+「待续项」。
3. 读 `docs/todo.md` 08-03 段 + `docs/revision-log.md` §5 最新。
4. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
5. 从「待续项」继续（建议先 CB-13 评估反馈或 PRM-08 compare 链路）。
