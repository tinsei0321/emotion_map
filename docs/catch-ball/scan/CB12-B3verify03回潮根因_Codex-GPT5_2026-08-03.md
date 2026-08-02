# CB-12 B3-verify-03 while-loop 回潮根因定案（Codex 第三方）

> **定案方**：Codex（GPT-5，第三方独立评估小组）  
> **定案时间**：2026-08-03 | **分支**：`fix/emc-buglog` @ `1ddac28`  
> **方法**：读 1ddac28 diff + trace 取证（`--session B3-verify-03` 上下文）+ orchestrate 路由逻辑逐路径推演  
> **结论**：**1ddac28 的 zonal 多 call 重写与 recover 模式 G 都不是 while-loop 触发点**（机制上不可能）；根因 = **PRM-07/09 两个新问句经 FC 返回 'multi'/'unknown' 模板 → 筛选强制路由的 `!diagnose.template` 守卫放行 → 落 while-loop**——是**测试问句变更暴露的路由缺口**，不是 harness 回归；**不回退 1ddac28**，修 force-route 守卫

---

## 一、trace 取证（B3-verify-03 · 独立核验）

```
--stats: F_002=6 · F_001=12 · F_003=14 · F_005=9
F_002 上下文：
  23:52:50 F_005（FC·成功） → 23:53:00 F_002+F_001（agentStep 轮1）
                             → 23:53:12 F_002+F_001（agentStep 轮2·同一例）
  23:54:23 F_005（FC·成功） → 23:54:35 F_002+F_001（agentStep 轮1）
```

- **3 个 F_002 轮 = 2 例 while-loop**（例 A 2 轮 + 例 B 1 轮），**FC 全程正常**（F_005 无 degraded 迹象）——与用户声称一致 ✓；
- **关键**：F_005=9（25 例仅 9 次 FC）——**"10/25"疑似只有 ~10 例完成判定（OK 3 + ERR 7）**，其余 15 例未产出判定（或 run 中断）——**需 claude组 确认该 run 的完整 n**（报告文件未随附）。

## 二、orchestrate 路径推演（哪些机制能让"FC 正常"落 while-loop）

FC 成功（非 degraded）后落 while-loop，**只有三个入口**：

1. `_tplHitRateReady()` gate 关闭 → 单模板路径全跳过 → **全例 while-loop**——但 F_002=6（仅 2 例）→ **gate 未全局关闭**，排除；
2. `diagnose.template` 为 'unknown'/'concept'/'multi' 且链未命中 → 落 while-loop；
3. FC 返回的工具名不在 SKILL_DEFS（非规范名）→ template 'unknown'。

**结论**：FC 正常 + 仅 2 例 while-loop ⇒ 这 2 例的 template = **'multi' 或 'unknown'**（链注册表只有 extract_overlay/clip_density 两条，未命中）。

## 三、1ddac28 两处嫌疑逐一排除

| 嫌疑 | 机制推演 | 判定 |
|---|---|---|
| zonal 多 call 重写（`harness.js:1384`） | 重写后 `_allToolCalls.length=1` → orchestrate 走单工具路径（非 runAllToolCalls）→ `runTemplatePath(zonal)` → **快路径或 gap**（validateParams 失败 → EXIT_GAP/ask_user，非 while-loop）——**机制上不可能产生 while-loop**；且重写在 `if (_zonalD)` 内（derive 成功才执行） | **排除** |
| recover 模式 G（筛选→extract·`harness.js:1548`） | recover 只对 **FC 失败**（degraded）触发——本次 FC 全程正常 → **从未进入 recover** | **排除** |

## 四、真根因：新问句 → FC 'multi'/'unknown' → 筛选 force-route 守卫漏放行

1ddac28 同时改了 **PRM-07/09 的问句**（test-cases.js）：

- PRM-09 改为「从已载行政区中筛选出**西陵区**」——**筛选强制路由**（`harness.js:1368`）条件为 `(/筛选出\|筛选某类\|抽出.*用地/.test(q) && !diagnose.template)`——**`!diagnose.template` 只放行"无模板"**；若 FC 返回 **'multi'（多步计划）或 'unknown'**（非规范工具名）→ template 为真值 → **不强制** → 链未命中 → **while-loop**；
- PRM-07 改为「**小溪塔**范围内按面聚合…」——zonal 强制路由（`tool !== 'zonal_stats'`）对 'multi'/'unknown' 仍会强制（tool 从 method 派生）→ PRM-07 大概率被 zonal 路由救回；**最可能 while-loop 的是 PRM-09**（+ 另一例未知）；
- **这是测试问句变更暴露的路由缺口**（筛选路由对 'multi'/'unknown' 模板不覆盖），非 1ddac28 harness 回归。

**file:line 证据**：`harness.js:1368`（`!diagnose.template` 守卫）+ `stages.js:210`（非 SKILL 工具名归一 'unknown'）+ `stages.js:70-84`（链注册表仅 2 条）。

## 五、修复建议（不回退 1ddac28）

| # | 建议 | 判定 |
|---:|---|---|
| 1 | **筛选 force-route 守卫放宽**：`!diagnose.template` → `(!diagnose.template \|\| diagnose.template === 'unknown' \|\| diagnose.template === 'multi')`——高置信问法（筛选出+行政区/用地）对 'multi'/'unknown' 也强制 extract | agree（根治缺口） |
| 2 | **同批检查其余 force-route**：方格/裁剪/zonal 路由的守卫是否也需兼容 'unknown'（当前 zonal/裁剪按 tool 判·已兼容；方格按 tool 判·已兼容）——只需改筛选一处 | agree |
| 3 | **trace 加 template 字段**：FC 返回的 `diagnose.template` 记入 trace（现有 F_005 detail 无模板）——下次"FC 正常但 while-loop"可 trace 级定案（不需要推演） | agree（需 register_track_id 或复用现有 ID detail·守编号红线） |
| 4 | **确认 verify-03 的 n**：10/25 的 15 例为何无判定（F_005=9 暗示大部分未达 FC）——若 run 被中断/跳例，结果归因需重跑确认 | agree（数据完整性） |

## 六、优先级

- **P1**：修复建议 1（筛选守卫放宽）——直接治"新问句 → while-loop"，预计 PRM-09 类转快路径；
- **P1'**：修复建议 4（确认 run 完整性）——数据前提；
- **P2**：修复建议 3（trace 加 template）——防下次推演。

---

*本报告为 Codex 组独立定案；trace 上下文经 `trace_query --session B3-verify-03 --time 23:52:30-23:55:30` 实测，机制推演基于 orchestrate 路由代码逐路径核验。*
