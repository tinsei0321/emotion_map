# CB-12 trace.log 工具 + while-loop 修复 + pro 停用验证（Codex 第三方）

> **验证方**：Codex（GPT-5，第三方独立评估小组）  
> **验证时间**：2026-08-02 | **分支**：`fix/emc-buglog` @ `3bb2f76`+`f4f78e2`  
> **方法**：跑 trace 工具实测（session 隔离 + 轮转备份查询）+ 独立核验 B3 窗口 trace 计数 + 读两个 commit diff  
> **结论**：**trace 工具可用（session 隔离 ✓·轮转备份查询 ✓）**；**B3 窗口证据独立确认**（F_001=104=66 flash+37 pro+1 reasoner · F_002=18 · F_003=56——**推翻上一轮"F_001 每例 1 次→无 while-loop"定案**，while-loop × pro 是真根因）；**while-loop 修复 partial**（阈值回退 ✓·zonal 前置 ✓·词边界守卫有 1 个 bug）；**pro 停用完整**（三层 + 无活残留路径）

---

## 一、trace 工具验证（实测）

| 项 | 结果 | 证据 |
|---|---|---|
| session 隔离 | **OK** | `EMOTION_TRACE_SESSION=Codex-verify-001` 跑 `test_geo_routes.py` → `trace_query --stats --session Codex-verify-001` 返 **78 行**（MOD_FIELD.F_001:40 / RANGE.F_013:14 / F_014:14 / SPATIAL.F_003:6 / FIELD.F_002:4）；无 session 全量 = **1274 行**——过滤精确 |
| 轮转备份查询 | **OK** | B3 窗口在 `trace.log.1`（277MB 轮转档）——`--file .trace/trace.log.1 --time 21:14-21:50` 正常返回 |
| --id/--time/--stats 组合 | **OK** | `--id MOD_AIQA.F_002 --time 21:14-21:50 --stats` 返 18 行 |
| 指南 ID 映射 | **OK** | F_001=chat 公共出口（勿作 while-loop 判据）、F_002=agentStep（while-loop 铁证）、F_003=finalStep——与 `llm.py:93/208`、`stages.js` 对应 |

## 二、B3 窗口证据独立核验（推翻上一轮定案）

| 指标 | claude组 声称 | Codex 独立查询 | 判定 |
|---|---:|---:|---|
| F_002（agentStep·while-loop） | 18 | **18** | ✓ 一致 |
| F_003（finalStep） | 56 | **56** | ✓ 一致 |
| F_001 总数 | 104 | **104**（66 flash + 37 pro + 1 reasoner） | ✓ 一致（pro/reasoner = 38 ✓） |
| F_001 每例次数 | — | **~4/例**（104/25） | **推翻上一轮"每例 1 次·共 21 次"定案**——实际多轮（while-loop）+ 多 finalStep |
| 根因 | while-loop × pro/旧模型（非 API 慢） | 支持（F_002=18 + 38 次 pro/旧模型 + 探针 0.9s） | ✓ 新证据成立 |

**重要**：上一轮定案（"F_001 每例 1 次 → 无 while-loop · 根因=API 慢"）**被 trace 数据推翻**——F_001 实为 104（≈4/例）。这正是 trace 纪律（步骤 0 先取证）的价值：定案前没跑 stats，两次推断都错。**while-loop + pro/旧模型 才是 B3-08 大失败根因**，本次修复方向（while-loop 修复 + pro 停用）直接对症。

## 三、while-loop 修复验证（3bb2f76）

| 项 | 判定 | 证据/问题 |
|---|---|---|
| stripped 阈值 3→2 | **OK** | `tools.js:606-611`——"西陵/伍家"2 字区名恢复 stripped 匹配 |
| 词边界守卫 | **partial（1 个 bug）** | `tools.js:611` `q.slice(idx+len, idx+len+1)` 只取 **1 字符**，但块词表含 2 字词（公园/广场/大道）——`/(公园)$/.test("公")` 恒 false → **"西陵公园/广场/大道"仍会误匹配**（仅 路/山/街 1 字后缀被挡）。修复：`slice(2)` 或对后续 1-2 字符做完整块词匹配。另：`q.indexOf` 取**首次出现**——"西陵路和西陵区"首遇"路"被挡后整值跳过（后续 西陵区 不匹配）——残余边界 |
| zonal 前置检查 | **OK** | `harness.js:1369-1382`——`deriveAvailable` 成功才强制 zonal + 填 boundary；失败保留 FC 选择（防强制 zonal 无 boundary → 退化）✓ |
| 对 F_002 下降的预期 | 合理 | 阈值回退恢复 recover 模式 F 的 derive（2 字区名）→ 减少 FC 失败后落 while-loop；zonal 前置防强制路由破坏单工具路径——但 **F_002 不一定归零**（FC degraded / unknown 模板等其它 while-loop 入口仍在） |

## 四、pro 停用验证（f4f78e2）

| 层 | 判定 | 证据 |
|---|---|:---:|
| UI disabled | **OK** | `index.html` pro 按钮 `disabled` + title "已停用" |
| panel 强制 flash | **OK** | `panel.js` 载入时 localStorage pro 残留 → 强制 flash + 写入；点击守卫 `if (!b \|\| b.disabled) return` |
| finalStep 守卫 | **OK** | `stages.js:466` `answerModel === 'pro' ? 'flash' : ...` |
| 残留路径 | **无** | ① `deliberateStep` 由 `ctx.model === 'pro'` 守卫（`harness.js:524`）——ctx.model 已强制 flash → 永不触发；② router.py `req.model = _diag_model`（pro 覆盖）位于**旧 SSE diagnose 分支**——`diagnoseStep` 在 harness.js **已无调用**（FC 失败直入 while-loop·ef4bcdc）→ 死路径；③ 前端 `send` model 来自 `_thinkMode`（强制 flash） |
| 预期 | pro 调用归零 | B3 窗口 37 pro + 1 reasoner 全部来自前端可选的 pro 模式（测试 `opts.mode` 可设 pro）——禁用后无入口 ✓ |

## 五、额外观察（非阻塞）

- **MOD_PLACE.F_002 = 203,996 / MOD_PLACE.F_003 = 186,908**（B3 窗口 36 分钟）——地图渲染风暴级计数（~94 次/秒），疑似 place-layer 连续渲染或地图空闲重绘；虽非本次失败根因，但值得单独查（潜在性能项）；
- **MOD_LLM.F_002（fallback）= 79 次（含 3 ERR）**——provider 级调用远超用例数，可能有重试/降级链在跑——建议单独看 fallback 触发原因。

## 六、验证结论：**有条件通过**

- trace 工具：**通过**（session/轮转/查询全可用，B3 证据可独立复现）；
- while-loop 修复：**有条件通过**——阈值回退 + zonal 前置正确；**词边界守卫需修**（`slice(1)` → `slice(2)` 或块词完整匹配），否则"西陵公园/广场/大道"误匹配残留；
- pro 停用：**通过**（三层 + 无活残留路径）；
- **B3 可重测**：预期 F_002 显著下降（非归零）+ pro 调用归零；重测时带 `EMOTION_TRACE_SESSION=B3-<批次>` + `trace_query --stats --session` 附报告（新纪律已可用）。

---

*本报告为 Codex 组独立验证；trace 计数经 `trace_query --file .trace/trace.log.1 --time 21:14-21:50` 实测（session 隔离经 `Codex-verify-001` 批次实测）。*
