# CB-13 B3-verify-05 验证与残余根因（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）  
> **时间**：2026-08-03 | **分支**：`fix/emc-buglog` @ `e052fe7` | **环境**：办公室  
> **方法**：trace 取证先行（`trace_query --stats --session B3-verify-05`）→ 报告/audit JSON 三方核对 → 代码逐路径核验（select_template C 路由 / compare 工具链 / CPD 引导状态机 / 链前置与 recover）

---

## 第〇部分 · CB-12 注意点落地核验（上轮执行情况回顾）

上轮（CB-12 多步问修复评估）Codex/glm 共 3 个注意点，**在 6d2e609 已全部落地**，本轮实测验证生效：

| 上轮注意点 | 落地证据（当前工作树） | 本轮实测 |
|---|---|---|
| ① Codex：`_hasSeq` 过宽（"先看看热力图…"概念问误触发链） | 已收紧为完整「先<动作>再<目标>」结构：`/先\|然后\|接着\|随后\|再\s*.{0,10}(?:裁剪\|…\|排序).{0,20}(?:再\|然后\|接着\|随后).{0,10}(?:热力\|…\|筛选)/`（`frontend/js/ai_qa/harness.js:1087`） | RST-L06 PASS；B3 无概念问误触发迹象 |
| ② Codex：链前置抢在 Pro chain（FC 自产链）之前 | `diagnose.chain` 检查已移到顺序词链前置**之前**（`harness.js:1083`） | Pro 停用后该顺序无害且仍正确 |
| ③ glm：recover 触发后 `_hasSeq` 改走链前置 | FC 失败/unknown/multi + 顺序词 → 合成最小 diagnose 走链前置（`harness.js:984-992` + `[seq-chain]` 日志） | F_002 仅 2 次 agentStep 调用，链前置兜底生效 |

**结论：上轮 3 个注意点均已落地，无需再动。**

---

## 第一部分 · B3-verify-05 实测核对

三方证据交叉核对一致：

| 证据源 | 内容 | 核对结果 |
|---|---|---|
| `tests/reports/report-2026-08-03-03-llm.md` | n=26 · pass=23（88.5%）· 0 timeout · 0 误杀/漏判 | ✅ |
| `tests/browser/out/audit-B3-090102.json` | rows=26 · stats{total:26, pass:23, fail:3} | ✅ |
| `py tools/trace_query.py --stats --session B3-verify-05` | 336 行 · F_003=40 · F_005=20 · **F_002(agentStep)=4 行（=2 次调用）** · MOD_LLM.F_002=25 全 `attempt=0` · 0 ERR | ✅ |

**pro 独立核（第四项）**：25 条 `MOD_LLM.F_001` 原始行**全部 `model=deepseek-v4-flash`**（含 FC json 调用 5 条与流式 20 条）；25 条 `MOD_LLM.F_002` 全部 `provider=deepseek tier=flash attempt=0`；本会话 **0 条 D_001/D_002/D_004（无重试/无换家）、0 ERR**。→ **pro 停用与 flash 三层守卫独立确认，无复发迹象。**

**while-loop 独立核**：`--id MOD_AIQA.F_002 --session B3-verify-05` 仅 2 次 enter/exit（08:53:24、08:59:11，均紧随 F_005 FC 之后），即整轮 26 例仅 2 个用例各发生 1 次 agentStep（ReAct 单轮兜底），远低于 B3-08 的 8 次与 while-loop 阈值 5。→ **while-loop 根治状态独立确认。**

---

## 第二部分 · 4 项检查结论

### 1. PRM-08 为何仍 fail —— **非路由退化，是 FC 选型方差 + 上轮误把"测量修复"当"执行修复"**

**实测现象**（`report-2026-08-03-03-llm.json`）：
- PRM-08：`template=compare` · `method=compare_regions()` · `tools=["extract_feature"]` · `params={}` · `newLayers=2` · 36.7s —— **fail**
- RST-L02（**同一问句**「对比西陵区与伍家岗区范围内情绪极性差异」）：`tools=["zonal_stats","compare"]` · `params.boundary=西陵区, boundaries=西陵区|伍家岗区` · `newLayers=1` —— **pass**

**逐项排查**：
1. **select_template C 路由未退化**：两 case 的 `diagnose.template` 均为 `compare`——问句含"对比"→ `paradigm.py:516-521`（`decision_type=对比` 或问句含 对比/比较/VS → `compare`）命中正常。
2. **3abb503 为何未生效**：`git show 3abb503` 显示它改的是 **`frontend/js/test-cases.js`（测试测量端）**——`_extractParams` 由 first-capture-wins 改为**收集全部 zonal boundary 调用**（`test-cases.js:86-96` → `p.boundaries` 多区拼接）。它只在 compare 链路**真正执行**（走 `/geo/zonal_stats` 逐区调用）时才能让断言看到两区（RST-L02 受益于此）；PRM-08 根本未走 compare 执行路径 → `params={}` → 断言 `boundary[ERR]`。**上轮预期 PRM 10/10 的前提（把测量修复当作执行修复）不成立。**
3. **真实机制（推断·trace 支撑）**：同一问句同轮两结果不同 → FC 随机性。PRM-08 的 FC 直接产出 `extract_feature`（单工具、未带 boundaries），而非 `compare_regions` 链。执行侧对 compare 缺参的确定性兜底是 ask_user（`harness.js` runTemplatePath → `_missingSlotAsk('compare', ['boundaries'])`），但本 case 实际执行了 extract_feature（+2 层，两区各自抽取），未走 compare/未 ask → 判定为 **FC 选型单例偏离**（与 KNOWLEDGE §2「工具选型 100%·填参才是路由瓶颈」同类，本次连选型都未命中 compare）。F_002 于 08:53:24 紧随 FC 出现，属该 case 内 ReAct 兜底路径（归属按时间窗推断）。
4. **判据**：这不是 compare 链路"退化"（RST-L02 同轮证明链路可用），而是 **compare 缺少确定性路由兜底**（CHAIN_REGISTRY 仅 extract_overlay/clip_density，无 compare 链；recover 也不覆盖"对比+双区名"模式）。

### 2. CPD-L01/L02 —— **产品引导逻辑无 bug，测试用例引用了已改名消失的 CSV（测试基建缺陷）**

**实测现象**：CPD-L01/L02 均 `stage s1` · `hint 未推 range/analyze`；CPD-L03"通过"但断言恒真（两分支均 pass，`test-cases.js:121`）。

**根因（证据链完整）**：
- `test-cases.js:8`：`const CSV = 'xiling_wujia_L1_T1_result_csv.csv'`——CPD-L01/L02 直接 `t.loadCSV(CSV)`（不经 llmRun 的 `resolvePoints` 语义解析）。
- 该文件名**已不存在**：`DATA/performance/` 实测仅 `yichang_*` / `ermawu_*`（`Test-Path xiling_wujia_* → False`）；`test-assets.js:2-4` 明确记录 **2026-07-24 xiling_wujia→yichang 改名**，`POINTS` 语义映射已指向 `yichang_*`（`test-assets.js:20-23`）。
- `loadCSV` 对 404 的处理：`fetch('/DATA/performance/xiling_wujia…') → r.text()`（404 正文）→ `dsvRows` 解析失败 → **静默返回 `{ok:false}`（不抛错）**（`e2e-seam.js:129-141`）→ 无点层导入 → `hasImport()=false` → `deriveGuidance` row 2 `!hasImport → null`（`cpd-guide.js:56`）→ 无任何 hint。
- 其他 PRM/RST/SMT 用例不受影响：走 `resolvePoints('L2-T1') → yichang_L2_T1_L2_result_csv.csv`（存在）。
- 产品侧 CPD 引导逻辑经 `tests/browser/test_cpd_predicates.py` 验证正常（注入点层 → `hasImport=true` → 引导可达），**非产品 bug**。

这也解释了为何 CPD-L01/02 自改名后一直是"既有 backlog"：失败是**文件名引用过期**，不是引导状态机问题。

### 3. RST-L06 收敛确认 + 上轮注意点复核

- **收敛成立**：RST-L06 PASS（`tools=clip,density` · `newLayers=2` · 22.1s），链前置确定性执行（clip→density 两步，0 中间 LLM 轮）；整轮 F_002 仅 2 次调用证明 while-loop 未回潮。
- **Codex 注意点 1（_hasSeq 过宽）**：已落地（`harness.js:1087` 收紧正则），本轮无概念问误触发链的新证据 → **无需再落地**。
- **Codex 注意点 2（Pro chain 前置）**：已落地（`harness.js:1083`），且 Pro 已停用 → 顺序无害、保留正确 → **无需再动**。
- **glm 建议（recover 链前置）**：已落地（`harness.js:984-992`），F_002 低位证明有效 → **无需再动**。

### 4. while-loop / pro 独立核 —— **均无复发迹象**（详见第一部分 trace 证据）

---

## 第三部分 · 建议（分级）

| 优先级 | 建议 | 证据/验证方法 |
|---|---|---|
| **高** | PRM-08：给 compare 加确定性兜底——仿 clip_density recover 模式：FC 未产出 compare 但问句含 对比/比较/VS 且可派生 ≥2 区名时，合成 `template=compare` 并确定性填 `boundaries`（或进 CHAIN_REGISTRY）。治 FC 单例偏离，不依赖模型稳定性 | 修复后 PRM-08 单例连跑 5 次应稳定 `zonal_stats+compare` + `boundaries=两区`；trace F_002 不再出现在 compare 用例 |
| **高** | CPD-L01/L02 修复：`test-cases.js:8` 的 `CSV` 改走语义解析（`resolvePoints('L1-T1')` → `yichang_L1_T1_result_csv.csv`），或直接改为存在的文件名——1 行修复，属测试基建 | 修复后 CPD-L01/L02 应 pass；同时建议把 CPD-L03 的恒真断言改为硬断言（新对话后 hint 应含 '范围'） |
| **中** | 3abb503 类"测量修复"须与"执行修复"区分标注（建议入 KNOWLEDGE §3 标尺纠正：修复测量端 ≠ 修复执行端），防下轮再按 10/10 预期 | 评审 diff 时核对文件归属（test-cases.js=测量 / harness.js=执行） |
| **低** | backlog「MOD_LLM.F_002 fallback 79 次含 3 ERR」**建议重新核实**：`MOD_LLM.F_002` 是 `chat_with_fallback` 每次调用入口的日志（`llm.py:349`，attempt=0 即首试），非仅 fallback 事件；本会话 25 条全 `attempt=0`、0 换家/0 ERR | `--id MOD_LLM.F_002 --level ERR` 复查历史日志区分"调用数"与"真实 fallback 数" |

---

## 第四部分 · 判定

- **多步问修复最终收敛（CB-12→13 闭环）✅**：RST-L06 PASS + 链前置确定性执行 + F_002 2 次调用（while-loop 根治维持）+ 上轮 3 个注意点全部落地生效。
- **PRM-08 需下一轮修**：非路由退化；根因 = compare 缺确定性路由兜底（FC 选型方差单例偏离）。建议按高优实施。
- **CPD-L01/L02 需修（1 行，测试基建）**：产品 CPD 引导逻辑正常；修复测试数据引用过期文件名即可。不属于产品引导态缺陷。

---

## 附录 · trace 证据

```
py tools/trace_query.py --stats --session B3-verify-05
== 各 ID 计数（336 行）==
  MOD_FIELD.F_001: 158     MOD_AIQA.F_003: 40      MOD_LLM.F_002: 25
  MOD_LLM.F_001: 25        MOD_FIELD.F_002: 22     MOD_LLM.F_005: 20
  MOD_SPATIAL.F_003: 16    MOD_SPATIAL.F_006: 6    MOD_AIQA.F_006: 6
  MOD_FIELD.F_003: 6       MOD_RANGE.F_013: 4      MOD_RANGE.F_014: 4
  MOD_AIQA.F_002: 4        ← agentStep 2 次调用（enter+exit）· while-loop 低
```

`--id MOD_LLM.F_001 --session B3-verify-05`：25/25 `model=deepseek-v4-flash`（pro 0）  
`--id MOD_LLM.F_002 --session B3-verify-05`：25/25 `provider=deepseek tier=flash attempt=0`（0 重试/0 换家）  
会话内 ERR/D_001/D_002/D_004：**0 条**

---

*本报告为 Codex 组独立评估；trace 数据先行、推断已标注假设（PRM-08 的 F_002 归属按时间窗推断，计数级结论不受影响）。*
