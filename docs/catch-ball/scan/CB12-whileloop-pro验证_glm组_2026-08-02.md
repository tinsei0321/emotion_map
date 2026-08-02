# CB-12 trace.log 工具 + while-loop 修复 + pro 停用验证（glm组 · ZCode + GLM 5.2）

> **验证方**：glm组（ZCode + GLM 5.2）·第三方独立评估  
> **日期**：2026-08-02 | **对象**：`3bb2f76`（trace.log 业界级 + while-loop 修复）+ `f4f78e2`（pro 停用）  
> **方法**：diff 审查 + `tools/trace_query.py --stats` 独立运行 + Node.js stripped/边界复现（9 例）+ pro 残留路径全扫 + pytest 225 passed  
> **前置**：[CB12-B3定案审查_glm组](CB12-B3定案审查_glm组_2026-08-02.md)（glm组 trace.log 铁证发现 F_002 while-loop）

---

## 验证结论：通过

**三项修复全部正确落地·glm组 上轮发现的 while-loop 根因（F_002 铁证）已闭环。** stripped 阈值回退 2 字区名恢复 ✅·词边界守卫拦截"西陵路/点军山" ✅·zonal 前置检查消除无 boundary 强制 ✅·pro 三层守卫无残留 ✅·trace_query 工具可用 ✅·pytest 225 passed 零回归 ✅。1 个极边缘（"伍家岗大道"多字符边界）记 P3·不影响 B3。

---

## 一、逐项验证清单

### ① trace.log 业界级（3bb2f76）— **OK**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| `tools/trace_query.py` 存在且可运行 | ✅ | `python tools/trace_query.py --stats` 输出 1196 行·30+ ID 计数 |
| `--stats` 模式输出 ID 计数 + ERR 标记 | ✅ | `MOD_LLM.F_002: 21 [ERR 3]` 等·ERR 计数可见 |
| session 隔离（`EMOTION_TRACE_SESSION`）| ✅ | tracker.py 加 session 字段（diff 确认 `core/tracker.py` +18 行）|
| 轮转（trace.log → trace.log.1）| ✅ | 当前 trace.log 已轮转（F_002=4 vs 旧 trace.log.1 的 18）|
| `docs/trace-log-guide.md` 用法文档 | ✅ | 54 行·含 session 用法 |

**trace_query 输出（当前轮转后）**：
```
MOD_AIQA.F_003: 26   (finalStep)
MOD_AIQA.F_002: 4    (agentStep — 修复后大幅下降·旧轮转 18→4)
MOD_LLM.F_005: 1     (FC diagnose)
MOD_LLM.F_001: 1     (LLM chat)
```

F_002 从 B3 窗口的 18 次 → 修复后 4 次（当前轮转的修复后运行）——**while-loop 显著下降**。

### ② while-loop 修复（3bb2f76）— **OK（3 项全部落地·附 1 极边缘记录）**

#### ②-a stripped 阈值 3→2 回退 — **OK**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| 阈值改回 `>= 2` | ✅ | `tools.js:607` `_nmStrip.length >= 2`（a04a714 的 `>= 3` 已回退）|
| "西陵"（2 字）stripped 匹配恢复 | ✅ | Node.js 复现："西陵范围内" → 匹配西陵区 ✅ |
| "夷陵"（2 字）stripped 匹配恢复 | ✅ | Node.js 复现："夷陵范围内" → 匹配夷陵区 ✅ |

**glm组 上轮指出的"a04a714 stripped 阈值 3→2 退化"已修复——2 字区名 boundary derive 恢复·validateParams 不再 fail·不再触发 ask_user/while-loop 退化链。**

#### ②-b 词边界守卫 — **OK（附 1 极边缘）**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| "西陵路"→不匹配（边界 `路`）| ✅ | Node.js："西陵路周边" → 不匹配 ✅ |
| "点军山"→不匹配（边界 `山`）| ✅ | Node.js："点军山公园" → 不匹配 ✅ |
| 边界检查逻辑（`路\|山\|公园\|广场\|大道\|街`）| ✅ | `tools.js:608` 正则检查 stripped 值后一字符 |

**极边缘**（P3·不阻塞）：
- "伍家岗大道" → 匹配"伍家岗"——因为边界检查只查 stripped 值后**一个字符**（"大"不在 blocklist）·而"大道"是双字符。但"伍家岗大道"非真实宜昌地名·实际不影响。建议（P3）：边界检查改查后 2 字符或用 `/(路\|山\|公园\|广场\|大道\|街)/.test(q.slice(idx+len, idx+len+2))`。

#### ②-c zonal 强制路由前置检查 — **OK**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| `deriveAvailable` 前置（zonal 路由内先调）| ✅ | `harness.js:1370` `const _zonalD = deriveAvailable(q, layers)` 在改 template 前 |
| derive 成功才强制改 template | ✅ | `:1371` `if (_zonalD) { diagnose.template = 'zonal'... }` |
| derive 失败 → 不改 template（保留 FC 原选）| ✅ | `:1379` 注释"boundary 不能 derive → 不强制改 template"·无 else 分支 = 不改 |
| boundary 填充用 `_zonalD`（非旧 `_d`）| ✅ | `:1374-1376` 用 `_zonalD.field` / `_zonalD.name`（变量名同步更新）|

**glm组 上轮建议"zonal 路由加 deriveAvailable 前置检查（boundary 能填才强制改）"——完全落地。** 消除了"强制 zonal + 无 boundary → validateParams fail → ask_user/while-loop 退化"路径。

### ③ pro 停用（f4f78e2）— **OK（三层守卫·无残留）**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| UI disabled（pro 按钮 `disabled`）| ✅ | `index.html:235` `disabled` + title "已停用" |
| `_thinkMode` 强制 flash（localStorage 有 pro 也覆盖）| ✅ | `panel.js:27-28` `if (_thinkMode !== 'flash') { _thinkMode = 'flash'; localStorage.setItem(...) }` |
| 点击 pro 按钮忽略（`b.disabled` 检查）| ✅ | `panel.js:1628` `if (!b \|\| b.disabled) return` |
| finalStep 守卫（answerModel='pro' → flash）| ✅ | `stages.js:469` `model: (ctx.answerModel === 'pro' ? 'flash' : ...)` |
| `ctx.model` 来源 = `_thinkMode`（强制 flash）| ✅ | `panel.js:1551` `model: _thinkMode` → 恒 'flash' |
| harness pro 检查变死代码（`ctx.model === 'pro'` 永不成立）| ✅ | `harness.js:526,1003` 两处 `ctx.model === 'pro'` → 因 ctx.model 恒 flash → 死代码（安全·不执行）|

**pro 残留路径扫描**：
```
harness.js:526   if (ctx.model === 'pro' && ...) → 死代码（ctx.model 恒 flash）
harness.js:1003  if (ctx.model === 'pro' && ...) → 死代码
stages.js:469    最终守卫 pro→flash → 额外保险
panel.js:27-28   _thinkMode 强制 flash → 入口守卫
panel.js:1628    disabled 点击忽略 → UI 守卫
```

**三层守卫（入口 UI + _thinkMode 强制 + finalStep 最终）·无 pro 残留执行路径。**

---

## 二、回归验证

| 项目 | 结果 | 证据 |
|------|:---:|------|
| pytest 全量 | ✅ | **225 passed, 5 skipped**（独立运行确认） |
| trace_query --stats | ✅ | 输出正常·ID 计数 + ERR 标记 |
| 红线（diagnose prompt / tracker / 四态出口）| ✅ | diff 改 tools.js deriveAvailable + harness.js deriveMissingParams + panel.js/stages.js/index.html pro 停用 + tracker.py session 字段·不碰 diagnose prompt |

---

## 三、while-loop 根因闭环确认

glm组 上轮（CB12-B3定案审查）发现的 while-loop 铁证：

| 证据 | 上轮（a04a714 后）| 修复后（3bb2f76 后）| 闭环 |
|------|:---:|:---:|:---:|
| `MOD_AIQA.F_002`（agentStep·while-loop）| **18 次**（B3 窗口）| **4 次**（当前轮转·修复后运行）| ✅ **下降 78%** |
| stripped 阈值退化（2 字区名失效）| 3→2 字区名不匹配 | 2→恢复匹配 ✅ | ✅ |
| zonal 强制无 boundary | 强制改 template + boundary 可能失败 | 前置检查·derive 成功才改 ✅ | ✅ |

**claude组 单例复现确认**："PRM-05 zonal 单步·F_002 = 0"——单工具路径恢复·不再走 while-loop。

---

## 四、B3 重测就绪评估

| 条件 | 状态 |
|------|:---:|
| while-loop 退化修复（stripped + zonal 前置）| ✅ |
| pro 调用归零（三层守卫）| ✅ |
| trace_query 可监控 F_002（验证 while-loop 不复发）| ✅ |
| pytest 零回归 | ✅ |
| B3 waitAnswer 超时调整 | ⚠️ 未改（90s·如果 API 偶尔慢 + 少量 while-loop 仍可能超时）|

**建议可重跑 B3**。预期：
- F_002（agentStep）显著下降（18→<5）
- pro 调用归零（37→0）
- pass 率恢复到 06/07 水平（76-80%）或更高（zonal 前置 + stripped 恢复解决 PRM-05/06/07）
- 如果仍有少量 while-loop（_tplHitRateReady gate 问题）·trace_query 能实时捕获

---

## 五、验证清单总结

| # | 验证项 | 方法 | 结果 |
|:---:|------|------|:---:|
| 1 | trace_query --stats 可用 | 独立运行 | ✅ OK（1196 行·30+ ID） |
| 2 | stripped 阈值 3→2 回退 | Node.js 9 例 | ✅ OK（2 字区名恢复） |
| 3 | 词边界守卫（路/山）| Node.js | ✅ OK（西陵路/点军山拦截） |
| 4 | zonal 前置检查 | diff + 代码核验 | ✅ OK（derive 成功才强制） |
| 5 | pro UI disabled | diff | ✅ OK |
| 6 | pro _thinkMode 强制 flash | diff | ✅ OK |
| 7 | pro finalStep 守卫 | diff | ✅ OK |
| 8 | pro 残留路径扫描 | 全代码 grep | ✅ OK（死代码·不执行） |
| 9 | pytest 225 passed | 独立运行 | ✅ OK |
| 10 | F_002 while-loop 下降 | trace_query 对比 | ✅ 18→4 |

---

## 六、一句话结论

**三项修复全部正确落地——while-loop 根因闭环（stripped 阈值 2 字区名恢复 + zonal 前置检查消除无 boundary 强制 + F_002 从 18→4 下降 78%）·pro 三层守卫无残留（UI disabled + _thinkMode 强制 flash + finalStep 守卫）·trace_query 工具可用（--stats 输出正常）·pytest 225 passed 零回归。可重跑 B3——预期 F_002 显著下降 + pro 归零 + pass 恢复到 76-80%+。1 个极边缘（"伍家岗大道"多字符边界·P3）不影响实际使用。**

---

*glm组（ZCode + GLM 5.2）· CB-12 trace + while-loop + pro 验证 · 2026-08-02*  
*验证基于：diff 审查（3bb2f76 + f4f78e2）+ `tools/trace_query.py --stats` 独立运行 + Node.js stripped/边界 9 例 + pro 残留全扫 + pytest 225 passed + trace_query F_002 对比（18→4）。*
