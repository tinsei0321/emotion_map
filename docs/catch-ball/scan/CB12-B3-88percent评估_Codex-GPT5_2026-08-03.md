# CB-12 f6e415a + B3 88% 评估（Codex 第三方）

> **评估方**：Codex（GPT-5，第三方独立评估小组）  
> **评估时间**：2026-08-03 | **分支**：`fix/emc-buglog` @ `f6e415a`  
> **方法**：读 f6e415a/b5477dd diff + trace 独立核验（B3-verify-04）+ compare 请求路径追踪  
> **结论**：**5 项修复 4 项正确落地，1 项有误停风险（early-stop 会截断多步 while-loop）**；**B3 88% 可信（22/25·3 fail = PRM-08 测量伪影 + CPD backlog 2）**；**PRM-08 根因 = 测量伪影**（compare 复用 zonal_stats 逐区单 boundary 调用·请求体无 `boundaries` 数组·断言捕获不到第二区）——执行正确，非代码缺陷

---

## 一、f6e415a 修复评估

| 修复 | 判定 | 证据/问题 |
|---|:---:|---|
| P0 recover 触发扩展（degraded OR unknown/multi） | **OK** | `harness.js:975-992`：条件扩展正确；`_hitRecover` 遥测+持久化 ✓。**轻微误伤风险**：multi 带有效链时 recover 命中会整体替换（如"裁剪+合并"多步问被 recover 的 intersection 模式降级为不合并）——建议 recover 命中前检查原 diagnose 是否有有效 `chain`（有则保留） |
| P0 筛选路由守卫放宽（unknown/multi 也强制 extract） | **OK** | `harness.js:1382`：`(!template \|\| 'unknown' \|\| 'multi')` ✓（PRM-09 转 PASS 实证） |
| P1 gate per-template（unknown 才受 gate） | **OK（gate 已近退化）** | `harness.js:1072`：其他 single 模板恒 fast path——**全局连锁消除 ✓**。注意：'unknown' 的 category 本非 single，gate 检查对 unknown 是死代码（反正走 while-loop/recover）——gate 已实质退化，可保留为日志或移除 |
| P1 B3 飞轮清 gate（?test=1 冷启动） | **OK** | `harness.js:860-864`：?test=1 清 localStorage gate stats ✓（verify-04 F_005=25 全量跑·verify-03 的"F_005=9"数据不完整问题确认由全量解决） |
| **P2 while-loop 早停**（产图层→强制 answer） | **⚠️ 误停风险** | `harness.js:1213-1219`：`newLayerCount > 0 && !diagnose.chain && !keep` → 强制结束。**缺陷**：while-loop 内**合法的多步任务**（如"先裁剪西陵区情绪点，再生成热力图"）第 1 步产层即被截断 → **只做一半回潮**！`!diagnose.chain` 只排除 Pro 链，不排除 while-loop 自身规划的后续步骤；F3 完整度 gate（`_plannedGeoSteps`/`_executedGeoSteps`）在 answer 分支有、此处没有。**修复**：早停条件加 `_plannedGeoSteps(diagnose.method) <= _executedGeoSteps(toolHistory)`（计划已执行完才停） |

## 二、B3 88% 确认

### 数据（`report-2026-08-03-01-llm` + trace B3-verify-04）

```
pass=22/25（88%）· timeout=0 · t_p95=46s · 9.8min
trace: F_005=25（全量 FC）· F_002=10（5 例 × 1 轮·早停压到 1 轮）· F_001=33
```

### 可信度评估

- **3 fail = PRM-08（测量伪影·见三）+ CPD-L01/02（backlog·未触碰子系统）**——无新假阳性 ✓；
- **PRM 9/10**：07 小溪塔、09 筛选转 PASS ✓（recover 扩展 + 守卫放宽实证）；08 是唯一真实"未通过"但**执行正确**（见三）；
- **5 例 while-loop 但通过**：早停压到 1 轮（验证了早停效果·但也暴露误停风险）；F_002 比例 40%（10/25）vs verify-03 的 67%（6/9 部分 run）——绝对数相近、相对下降，**"大幅下降"表述略过强**（绝对值 10 vs 8·仍偏高）；
- **弱断言残留**：PRM-10 显示"3→0 层"却 PASS（断言只看 `tools.includes('clip')` 不看产物）；RST-L02/L03 类 badge-only 断言仍在——88% 略高于真实"链路通畅"数，但方向正确。

## 三、PRM-08 攻坚（唯一 fail·根因 = 测量伪影）

### 根因（代码级确认）

- `compare_regions` 前端（`tools.js:1002-1013`）把 boundaries 逐区转 `{label, geo}` → `generateCompareForAI` → **`_execute` mode='compare' 复用 `geoPost('zonal_stats', body)` 逐区调用**（`zonal-tool.js:100-130`：`body = { layer, boundary: geo }`·每区一次）；
- **请求体永远没有 `boundaries` 数组**（每次调用只有单 `boundary`）→ `_extractParams`（first-capture-wins·`test-cases.js:72-73`）只捕获第一个 zonal 调用的 `boundary`（西陵区）→ `p.boundaries` 恒空 → PRM-08 断言 `/西陵.*伍家/` 找不到第二区 → boundary[ERR]；
- **执行正确**：PRM-08 显示 +1 层（`_ok>=2` 才产层·`zonal-tool.js:118-123`）→ 两个区都聚合了；RST-L02 同路径 +1 层（断言不查 boundaries 所以 PASS）。

### 修复方向（测试侧）

1. `_extractParams` 对 compare 类：**收集多次 zonal 调用的所有 `boundary` 值**（append 而非 first-capture-wins）→ `p.boundaries` = 多区数组；或
2. PRM-08 断言改为：`sig.tools.includes('compare')` + observation 含"2 区并排"/两个区名（回答层断言）；或
3. 断言 `p.boundary` 含 西陵 + `p.boundaries` 为空时允许（说明 compare 走逐区路径）——用"执行工具 + 层产出 + 结论含两区名"组合替代单 key 检查。

**建议**：方案 1（`_extractParams` 收集多 boundary）最通用，一次修好所有 compare 类断言。

---

## 四、验证结论：**有条件通过**

- **B3 88% 可信**：22/25 · PRM 9/10 · 3 fail 归因清楚（08 测量伪影 + CPD backlog）· 无新假阳性；
- **f6e415a 4/5 正确**（recover 扩展 / 筛选守卫 / gate per-template / 飞轮清 gate）——recover 扩展是本次 88% 的关键；
- **需修 2 项后转"通过"**：
  1. **early-stop 加计划完成度判断**（`_plannedGeoSteps <= _executedGeoSteps`·`harness.js:1213`）——防多步 while-loop 被截断（只做一半回潮）；
  2. **PRM-08 测量修复**（`_extractParams` 收集多 boundary·`test-cases.js`）——让 88% 反映真实执行（PRM 应 10/10）。

---

*本报告为 Codex 组独立评估；trace 数据经 `trace_query --session B3-verify-04` 实测，compare 请求路径经 `zonal-tool.js:100-130` 逐行确认。*
