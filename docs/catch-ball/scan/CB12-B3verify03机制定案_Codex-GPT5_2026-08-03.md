# CB-12 B3-verify-03 while-loop 回潮机制定案（Codex 第三方·结合新机制分析）

> **定案方**：Codex（GPT-5，第三方独立评估小组）  
> **定案时间**：2026-08-03 | **分支**：`fix/emc-buglog` @ `1ddac28`  
> **方法**：读 gate/while-loop/recover 入口代码 + trace 时间分布 + 机制推演  
> **结论**：**verify-03 根因 = FC 成功但 template='unknown'/'multi' → recover 只在 FC 失败时触发（缺口）→ 直落 while-loop**；**gate 连锁假说：机制缺陷成立（全局开关属实）但非 verify-03 触发**（F_002=6 太少·gate 关闭会连锁大量 while-loop）；**3 个机制缺陷全部确认**，修复优先级 = recover 缺口(P0) > force-route 守卫(P1) > gate 自适应(P1) > while-loop 确定性出口(P2)

---

## 一、trace 时间分布核验（gate 连锁假说验证）

`trace_query --session B3-verify-03 --time 23:45-23:56` 全量分布：

- **多数用例走快路径**（FC → spatial → F_003 无 F_002，如 23:45:23→23:46:02→23:46:38 三连快路径）；
- F_002 只有 **2 例**（23:53:00+23:53:12 例 A 2 轮、23:54:35 例 B 1 轮），且分散在 run 尾部；
- F_005（FC）= 9 次 / F_003（finalStep）= 14 次 / F_001 = 12 次。

**gate 连锁假说判定**：

- `_tplHitRateReady`（`harness.js:112-116`）确实是**全局开关**（`hits/n >= 0.6` 一个布尔值管所有问）——**缺陷属实（潜在）**；
- 但若 gate 在 verify-03 关闭 → **后续所有单模板用例全部 while-loop**（F_002 应 ≫ 6）——实际 F_002=6（2 例）→ **gate 未关闭**；
- **结论**：gate 连锁**不是 verify-03 触发**（trace 反证），但**是真实潜在连锁风险**（某批 unknown 打低命中率 → 全站退化）——P1 修。

## 二、根因定案（修正版）：recover 触发条件缺口

**核心缺口（代码级）**：

- `orchestrate` 中 `_deterministicRecover` 只在 **FC 失败**时调用（`harness.js:973`：`if (!diagnose || diagnose.degraded)`）；
- **FC 成功但 template='unknown'/'multi'**（如 PRM-09 新问句"筛选出西陵区"→ FC 返 'multi'，或 FC 返非规范工具名 → `stages.js:210` 归一 'unknown'）→ **跳过 recover → 单工具路径条件不满足（`SKILL_DEFS['unknown'].category='unknown'` 非 single）→ 链未命中 → 直落 while-loop**；
- 与上一轮结论一致（`harness.js:1368` 筛选守卫 `!diagnose.template` 放行 'multi'/'unknown'）——**这是 verify-03 的真触发**。

**1ddac28 两处再次排除**：zonal 多 call 重写（重写后单工具 → 快/gap 非 while-loop）·recover 模式 G（仅 FC 失败触发·本次 FC 正常）。

## 三、while-loop 机制 3 缺陷评估

| claude组 缺陷 | Codex 判定 | 证据 |
|---|:---:|---|
| 1. gate 全局开关（某批 unknown → 全站连锁） | **成立（潜在）** | `harness.js:112-116` 单布尔值全局生效；`_recordTplResult` 只计 'unknown' 为 miss（'multi' 计 hit·注意）——连锁条件是 ≥40% unknown 累积 |
| 2. while-loop = ReAct 多轮慢 + 可能只做一半 | **成立** | 每轮 agentStep 一次 LLM（F_001 msgs=12）；MAX_ROUNDS=4/10（`harness.js` 顶）；中间 break 只做一半风险真实 |
| 3. recover 兜底不完整（FC 失败未覆盖问句） | **成立 + 补充** | 更关键的是 **recover 根本不处理"FC 成功但 unknown/multi"**——这是 verify-03 直接触发（比"覆盖不全"更基础） |

## 四、修复方案与优先级

| # | 方案 | 判定 | 优先级 |
|---:|---|---|:---:|
| 1 | **recover 扩展触发**：`_deterministicRecover` 也处理"FC 成功但 template='unknown'/'multi'"（进 while-loop 前先确定性路由） | agree——直接治 verify-03 模式 | **P0** |
| 2 | **force-route 守卫放宽**：筛选路由 `!diagnose.template` → `(!template \|\| 'unknown' \|\| 'multi')`（`harness.js:1368`） | agree——治 PRM-09 类 | **P0** |
| 3 | **gate 每问自适应/滑窗**：全局布尔 → 最近 N 样本滑窗 或 仅对"本问 FC unknown"降级（不再因历史批全站退化） | agree——防潜在连锁 | **P1** |
| 4 | **while-loop 确定性出口优先**：进 ReAct 前先跑确定性路由（recover 全覆盖 + 链注册表扩展）·ReAct 仅作最终兜底 | agree——减少"只做一半" | **P1** |
| 5 | **回退 1ddac28** | **不回退**——zonal 重写正确（PRM-07 多 call 必需）·问句改更是 fixture 修正（数据前提） | — |
| 6 | **确认 verify-03 run 完整性**：F_005=9 / 25 例·"10/25"仅 ~10 例判定——run 是否中断/跳例？ | 需 claude组 确认（数据完整性） | **P1'** |

## 五、验证方法（修复后）

1. 单例复现 PRM-09（筛选出西陵区）：修复前 FC 成功 → while-loop（F_002≥1）·修复后 → 快路径（F_002=0）；
2. `trace_query --session <批>` 断言：F_002/F_005 比例回落到 <20%·pro=0·全 flash；
3. gate 修复验证：构造 localStorage 低命中率（人为塞 6 miss）→ 修复后仍走快路径（gate 不再全局关）或仅日志提示。

---

*本报告为 Codex 组独立定案；trace 分布经 `trace_query --session B3-verify-03 --time 23:45-23:56` 实测，recover/gate/force-route 代码经逐路径核验。*
