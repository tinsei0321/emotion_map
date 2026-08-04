# CB-16 无法回答措辞修复 + 发版遗留问题 综合实施预检（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `ef49cc1`（③w4 综合 plan·先讨论再实施）
> **范围**：只读评估 · 不改代码 · 不 commit
> **验证手段**：代码逐行核验（措辞/链/参数派生三处关键路径）+ 历史 audit 对照 + eval 用例数核算

---

## 结论先行

**草案可行 · 无 P0。** ②a 措辞方向正确；②b 四项方向对路，但需修正 5 项事实/语义（P1）+ 2 项建议（P1）+ 3 项 P2：

- **【P1】PRM-03/04 真根因 = deriveMissingParams 的 stale `tool` 门控**：radius 正则派生**已存在**（harness.js:1546·草案"新增解析"表述不准确）——但 `const tool` 在函数开头（:1430）捕获·G5 把 lookup_place 改判 buffer 后（:1468-1477）radius 派生仍用旧 tool 判断 `tool==='buffer'` → **跳过**。修法须先修门控（reroute 后重读 tool / 改判 `diagnose.template`）+ 补字面量/尺度表 fallback。
- **【P1】②b-4 fallback 搜索撞 CB-14 红线**：行政区 preset 实测含 9 feature（含小溪塔/龙泉/生物产业园等**法定功能区**——审计 trace 实证 L001=9 面）→ 模型"硬识别"源于 preset 数据本身。修法 = **FIXED_ADMIN_DISTRICTS 白名单门控**（西陵/伍家岗/猇亭/点军·CB-14 既有常量）+ request_upload 措辞明确·**不是 lookup_place fallback**（会进一步坐实自由语义猜测）。
- **【P1】RST-L06「已定根因」缺实证**：观察签名（tools 空 + tpl=clip + 1→0 层）与「clip 尝试即抛·failedObs 记录·无 tool:executed 事件」或「零工具尝试」**两种机制都一致**；boundary fallback 是真实防御面（值得做）·但 08-04 单次 FAIL 根因需 per-test trace（audit 无 chat 日志·P2 证据采集先行）。
- **【P1】eval 修复先取证**：37 条 9 MISS（28/37=76%）·草案只列 2 个 E1 multi 例——且 eval 注释明示这两例选 single「**非退化**（single 也 0 LLM 轮）·只是 chain 路径覆盖」= 覆盖偏好非功能缺陷。先跑 eval 存全 miss 列表·区分功能缺陷 vs 覆盖偏好再修。
- **【P1】RST-L06 fallback 须 feature 级提取**：fallback 到行政区 preset 后必须按问句区名取**单要素**（仿 :1453-1460 模式）·非整集合当 boundary；preset 引用对齐顶层「行政区」（presets 已并于顶层·test-assets 一致）。

---

## 一、②a 措辞修复 —— 对路（P2 补充）

- `failedObs` 语义核实：仅在工具失败时 push（链路径 :753-755 / ReAct 路径 :1261）——gap 出口（newLayerCount=0 && !hasRows）下 `failedObs=0` ⇒ **无失败工具尝试**（非严格"零尝试"：query_layers 等成功零产出也会 successObs++ 但失败列表空）·判据**可靠**。
- 新措辞「当前无法直接回答（超出可直接分析范围）」**得体**——不包含"没试过"式断言·对"零尝试"与"尝试但零失败"两种解释均安全；exit:'gap'/quickIntent/answered/narratedAnswer 不动 ✓。
- **P2 补充**：措辞分支须覆盖**两处**——composeGapCard 默认分支（:227-229）**和** gap 出口追加行（:1313「**诚实结论**：本轮未产出新图层。」·无条件硬编码）——后者同样要说图层·必须按 failedObs 分支（草案 :1310 应明确覆盖该行）。

## 二、②b 发版遗留 —— 四项核验

### 1. eval 76% NO-GO —— 方向对·先取证
- eval 用例数核实 = 37 条 ✓（含 E1 两条 multi：`西陵区的商业用地` / `西陵区范围内密度分析`）。
- **取证缺口**：28/37=9 MISS·草案只列 2 条；且 E1 两条是覆盖偏好（选 single 时：商业用地 → overlay+landuse 自动补全可答·范围内密度 → density+range 可答）·**非用户可见缺陷**。
- **机制建议**：优先确定性修复——①链触发条件放宽（`_hasSeq` 或 template∈链首步 clip 即查链·治"范围内密度分析"无顺序词时链不触发）；②select_template_text 属 diagnose 派生附录（D026·红线段）——若需调文本必须 **eval-first** 全量验证（这正是 eval 存在意义）·勿动 diagnose 结构。
- **P2**：76% vs 80% 为边界值·LLM 方差大——eval 重跑 2-3 次取均值/记录区间再定 go/no-go。

### 2. RST-L06 硬化 —— 值得做·非"已定根因"
- chain pre-check（:1103-1125）：deriveAvailable 无匹配 → boundary 缺失 → clip(range='') 抛错 → failedObs 记录 + 无 tool:executed → 观察签名（tools 空·1→0 层）**与假设一致**；但"零工具尝试"路径（intent=general / degraded / request_upload 短路）**同样一致**。
- 测试用例核实：RST-L06 在 `frontend/js/test-cases.js:372`（非草案 :121）·显式加载 `range:'行政区', csv:'L2-T1'`——行政区层在测试内已加载·deriveAvailable 失败概率低 → 单次 FAIL 更可能是 FC 输出路径（分支到达与否）·**建议先补 per-test trace 再定根因**。
- 硬化本身仍应做（真实防御面：行政区层未加载时 clip 不再静默失败）·fallback 须 feature 级提取（见结论 P1⑤）。

### 3. PRM-03/04 buffer radius —— 真根因是 stale tool 门控
- radius 正则派生**已存在**（:1546-1548）·草案"radius 从问句解析"= 已实现项·真缺口：`const tool` 在 :1430 捕获（函数开头）·G5 reroute（:1468）把 lookup_place→buffer 后·:1546 的 `tool==='buffer'` 用**旧值** → 跳过。
- 修法：reroute 后重读 tool（或改判 `diagnose.template`）+ 补尺度表 fallback（无字面量时 250/500/1000）+ 单测（FC 选 lookup_place → reroute buffer → radius 仍填）。

### 4. PRM-07 zonal 边界 —— 白名单门控·非 lookup fallback
- 实证：行政区 preset 含 9 feature（含法定功能区）·模型"硬识别"有数据来源；CB-14 要求只认真实行政区划 → **FIXED_ADMIN_DISTRICTS 白名单门控 + request_upload 措辞明确**（"该区域不在已固化行政区划库·请上传标准范围资料"）·不采纳 fallback 搜索（撞红线）。

---

## 三、7 问速答

1. **failedObs 判据可靠**（=无失败尝试·非严格零尝试）·新措辞得体（无"没试过"断言）；两处措辞（composeGapCard 默认 + 出口追加行）都要分支。
2. **eval 方向对**：先取证全 miss 列表·E1 两例是覆盖偏好·防误伤=确定性链触发放宽优先·select_template 文本改动必须 eval-first。
3. **RST-L06 硬化**：治本面改善（真实防御）·根因需 per-test 实证·fallback 须 feature 级提取。
4. **PRM 本次应做**（小改·发版前加固）·但修法补真根因（stale tool 门控 / 白名单门控）。
5. **优先级合理**：eval（发版门禁·先取证）> 措辞（用户实测·可先行）> RST-L06（与链修复合并）> PRM（小改）。
6. **测试够**·补：eval 多次采样 · 措辞「图层」字眼断言 · 链变体（无顺序词「范围内密度」）· radius stale-tool 回归 · boundary fallback feature 级单测。
7. **承重零触碰**：exit:'gap'/quickIntent/answered/narratedAnswer/ChatRequest 不动 ✓；select_template 属 diagnose 派生附录——改动 eval-first 守红线；PRM/链改动在 harness 前端确定性层·不碰 diagnose/harness 核心结构。

---

## 四、优先级

| 级别 | 项 |
|---:|---|
| **P1 修正** | PRM radius stale-tool 门控修复（reroute 后重读）· ②b-4 改白名单门控（弃 lookup fallback）· RST-L06 根因先取证（per-test trace）· eval 全 miss 列表取证 · fallback feature 级提取 |
| **P1 建议** | 链触发条件放宽（template∈链首步即查链）· eval 多次采样判定 |
| **P2** | audit 每例 /chat fetch 证据 · gap 出口追加行措辞分支 · 措辞「图层」字眼断言 · failedObs 语义注释（零失败尝试） |

---

## 五、判定

- **草案可行 · 无 P0**。②a 直接可做（补两处分支）；②b 按 P1 修正后实施。
- **P1 修正 ×5 + P1 建议 ×2 + P2 ×3**（如上）。
- **独立判断**：基于代码逐行核验 + 历史 audit 对照 + eval 用例核算，未参考 glm组 本轮报告。

---

## 附录：关键证据

| 依据 | 结论 |
|---|---|
| harness.js:1430 vs :1468-1477 vs :1546 | `tool` 在 G5 reroute 前捕获·radius 派生用旧值 → PRM-03/04 跳过机制实证 |
| harness.js:753-755/:1261 | failedObs 仅工具失败时 push·gap 下 =0 ⇒ 无失败尝试 |
| harness.js:1313 | gap 出口追加行「本轮未产出新图层」无条件硬编码·须按 failedObs 分支 |
| audit localStorage 行政区 L001=9 面 | 含小溪塔/龙泉/生物产业园等法定功能区 → ②b-4 应白名单门控 |
| frontend/js/test-cases.js:372 | RST-L06 用例（草案引 :121 不准确）·显式加载行政区+ L2-T1 |
| eval_template_flash.py | 37 条·E1 两条注释明示 single「非退化」=覆盖偏好·28/37 需全 miss 取证 |

*登记：docs/catch-ball/scan/（RULES 4.1 命名）。本报告只读评估·未改代码·未 commit。*
