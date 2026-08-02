# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月03日（**CB-12 闭环：B3 88% 历史最佳 + while-loop 根治 + trace 工具 + PRM 9/10**）| 分支 `fix/emc-buglog` | **已 push**
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md` + `OFFICE.md`

## 当前节点：CB-12 闭环 — while-loop 根治（recover 扩展）→ B3 88% 历史最佳

08-02→03 大跨轮：用户体验四类依据 → G0-G6c 实施 → B3 两轮定案（glm trace 铁证推翻"API 慢"·根因 = while-loop × pro/旧模型）→ trace 工具 + pro 停用 → while-loop 根治（**glm gate 连锁被 localStorage 铁证推翻·Codex recover 缺口正确**·recover 扩展触发）→ **B3 88%（22/25）历史最佳·PRM 9/10·p95 46s·9.8min**。**用户质疑促成澄清**（key 正常·非 API 慢）。

## 今日已 commit（fix/emc-buglog · **已 push**）

| commit | 内容 |
|---|---|
| `b349fcd` | 文档：while-loop 闭环记录 + 双组验证报告 |
| `a3a4486` | B3 08 重测 80%（PRM 7/10·pro 0·F_002 8） |
| `e7cb7b9` | 词边界 slice(2) 完整块词（Codex bug） |
| `f4f78e2` | **pro 停用**（flash 足够·UI disabled + 三层守卫） |
| `3bb2f76` | **trace.log 业界级 + while-loop 修复 + CB 取证步骤 0**（session/轮转/trace_query/文档/RULES/KNOWLEDGE） |
| `a04a714` | PRM 深水 4 例（ask 收窄/zonal 强制/多 call/双字段/后端日志） |
| `2582c34` `8a33080` `cde3cf4` | PRM 攻坚 P0-P2 + 补丁 |
| `7df8d75` `8e67848` | B3 P0 搜索素材注入 + KW 收紧 + 超时 + episode 修复 |
| `1362167` `aaa8319` | G6b 搜索 + G6c 连问 + G5 derive |

## 关键架构（下会话须知道）

- **B3 根因定案**：B3 大失败 = **while-loop 退化（a04a714 stripped 阈值 3→2 退化 + zonal 无前置强制）× pro/旧模型多轮**·非 API 慢（用户 key 正常·探针 0.9s·用户质疑澄清）。修复 = 阈值回退 3→2 + 词边界（slice(2)）+ zonal 前置检查（derive 成功才强制）+ **pro 停用**（flash 足够·三层守卫）
- **trace 取证纪律**（用户要求·glm 习惯）：根因分析第一动作 = `py tools/trace_query.py --stats`（数 **F_002 agentStep/F_003 final/F_005 FC·非 F_001** 公共出口）·跑测试带 `EMOTION_TRACE_SESSION=<组>-<批>`·trace.log 轮转 200MB·CB RULES 1.2 步骤 0
- **pro 停用**：UI disabled + `_thinkMode` 强制 flash + finalStep 守卫·ctx.model 恒 flash
- **搜索/连问**：G6b 素材注入（进 ctx.context 走 finalStep+防线·非旁路）·G6c 分句 ≤2 复用 orchestrate
- **尺度出口差异化**：finalStep 尺度约束 + R10/R11 防线·general 跳过（skipScaleDefense）
- **体检套件**：`py tests/browser/test_link_checkup.py`（20 例·四件套断言·回归门）·B3 留 API 好时段

## 待续项（下会话从这继续）

- **【上午公司环境】B3 全量重测**（用户定）：`EMOTION_TRACE_SESSION=B3-verify-05 py tests/browser/flywheel_audit.py --batch B3`·跑完 `trace_query --stats --session` 附报告·预期 PRM 10/10（08 测量 + slice 200）·RST-L06 多步问（链修复验证）·pass 88%→92%
- **多步问修复待 B3 验证**：链前置 + clip_density 触发器放宽 + boundary derive（4ea8b6d+0407f78）·**代码级验证过·单例不稳定**（FC 方差）·RST-L06 断言守门·若 B3 仍 fail 查 _hasSeq 误触发/链条件
- **backlog**：MOD_PLACE 渲染风暴（~94 次/秒·Codex 观察·潜在性能）+ MOD_LLM.F_002 fallback 79 次含 3 ERR
- **CPD-L01/L02**（CPD 导游·既有 backlog）
- 时间轴 `_time_manifest.json` 404（低风险）

## 测试基建

- pytest：**225 passed**
- 飞轮：`py tests/browser/flywheel_audit.py --batch B3`（**带 `EMOTION_TRACE_SESSION=B3-<批>`**·跑完 `trace_query --stats --session` 附报告）
- 体检：`py tests/browser/test_link_checkup.py`（20 例·回归门）
- 根因分析：`py tools/trace_query.py --stats/--id/--time/--session`（第一动作）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前 CB 轮次：CB-12（体验评估 + B3 定案闭环·**B3 08 恢复 80%**）· 下一轮 CB-13（待修复后验证）
- **双阵营**：claude组（开发主）+ Codex + glm组（评估·**trace 取证功臣**）
- 反评价轨迹：`docs/catch-ball/cb-journal.md`

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / **`@track()` 签名 / `_TRACKING_REGISTRY` 格式**（改前先扩 eval·每次一处）
- **trace 取证**：根因分析先 `trace_query --stats`（F_002/F_003 非 F_001）·推断只作假设
- **EMC 产物不临时创造样式**；不动 FC prompt；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**；commit 后不 push（用户手动 push·本会话已 push 一次·后续待用户）

## 恢复指引（新会话）

1. `git log --oneline -8` 对账（最新 `b349fcd`）。
2. 读本卡「关键架构」+「待续项」。
3. 读 `docs/todo.md` 08-02 段 + `docs/revision-log.md` §5 最新。
4. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
5. 从「待续项」继续（建议先 B3 残余 F_002 或 PRM-07 后端日志）。
