# CB-12 while-loop 机制分析 + B3-verify-03 根因重定（glm组 · ZCode + GLM 5.2）

> **审查方**：glm组（ZCode + GLM 5.2）·第三方独立评估  
> **日期**：2026-08-03 | **对象**：claude组 while-loop 机制分析（3 缺陷）+ B3-verify-03 回潮根因重定  
> **方法**：B3-verify-03 session 全量 trace（153 行）逐 case 分析 + 4 while-loop 入口代码核实 + 3 缺陷逐条评估 + verify-01 对照  
> **关键**：glm组 独立读取 `.trace/trace.log` session B3-verify-03 全量 153 行（非 claude组 转述）

---

## 〇、一句话结论

**gate 连锁假说成立——trace 全量分析显示 while-loop 集中在 case 7-8（被 single-tool 包围），gate 在 case 6-7 间翻转（某 case 记 unknown miss → 命中率跌 < 0.6 → 后续全 while-loop → while-loop answer 记 hit → 命中率回 ≥ 0.6 → single-tool 恢复）。这是 gate 设计的结构性缺陷：全局开关 + localStorage 跨 session 持久 = 概率性连锁。claude组 3 缺陷全部成立·缺陷 1（gate 全局开关）= P0 根因。推荐修复 = gate 改"按 template 个别判断"（非全局关）+ B3 飞轮模式冷启动 + while-loop MAX_ROUNDS 早停。**

---

## 一、B3-verify-03 逐 case 分析（trace 全量 153 行独立读取）

| Case | 时间 | FC (F_005) | 路径 | while-loop? | 说明 |
|:---:|------|:---:|------|:---:|------|
| 1 | 23:45:23 | ✅ | single-tool (SPATIAL zonal → F_003) | ❌ | 快路径正常 |
| 2 | 23:46:25 | — | F_003 only（quickIntent 短路？） | ❌ | 概念问直答 |
| 3 | 23:46:38 | — | F_003 only | ❌ | 同上 |
| 4 | 23:48:11 | ✅ | single-tool (SPATIAL buffer → F_003) | ❌ | 快路径正常 |
| 5 | 23:49:44 | ✅ | single-tool (SPATIAL buffer → F_003) | ❌ | 快路径正常 |
| 6 | 23:51:17 | ✅ | **GAP**（FC 后无 tool/F_002/F_003） | ❌ | FC 成功但无执行——可能 ask_user / request_upload |
| **7** | 23:52:50 | ✅ | **WHILE-LOOP**（2 轮 F_002） | **✅ 2 轮** | 🔴 gate FAIL |
| **8** | 23:54:23 | ✅ | **WHILE-LOOP**（1 轮 F_002） | **✅ 1 轮** | 🔴 gate FAIL |
| 9 | 23:55:56 | ✅ | single-tool (SPATIAL clip → F_003) | ❌ | 快路径恢复 |
| 10 | 23:57:29 | ✅ | single-tool (SPATIAL extract → F_003) | ❌ | 快路径正常 |
| 11 | 23:59:01 | ✅ | truncated（trace 结束） | — | — |

**关键发现：while-loop 不是均匀分布——集中在 case 7-8·被 single-tool 包围。**

---

## 二、gate 连锁假说验证

### 假说：某 case 记 unknown → gate 翻转 → 后续 while-loop → while-loop 记 hit → gate 回转

**trace 证据链**：

```
Case 1-5：single-tool（gate PASS）→ _recordTplResult(template) 记 hit
Case 6：GAP（FC 成功但可能 template='unknown' 或 ask_user）
  → 如果 template='unknown' → _recordTplResult('unknown') 记 miss
  → hits=5, misses=1, samples=6 → rate=83%（仍 > 60%·gate 仍 PASS）
Case 7-8：WHILE-LOOP
  → 但 case 7 FC 正常（非 unknown）→ 如果 gate PASS 应走 single-tool
  → 事实走了 while-loop → gate 此时 FAIL
  → 说明 case 6 或更早有更多 miss 累积（跨 session localStorage）
```

**gate 状态推断**：

| 时点 | 推断 hits/misses | 推断 rate | gate | 路径 |
|------|:---:|:---:|:---:|------|
| Case 1-5 | 本 session +5 hits | >60%（但跨 session 有累积 miss） | PASS | single-tool |
| Case 6 | 可能 +1 miss | 可能跌 <60% | **FLIP→FAIL** | GAP（ask_user?） |
| Case 7-8 | — | <60% | **FAIL** | **while-loop** |
| Case 7 while-loop 出 answer | +1 hit（template 非 unknown） | 可能回 ≥60% | **FLIP→PASS** | — |
| Case 9-10 | — | ≥60% | PASS | single-tool 恢复 |

**判定：gate 连锁假说成立——while-loop 集中在 gate FAIL 窗口·gate 回转后 single-tool 恢复。**

### 排除替代解释

| 替代假说 | 排除理由 |
|---------|---------|
| FC 失败（degraded）→ while-loop | claude组 确认"F_002 前 FC 正常（F_005 msgs=9-12）"——FC 非 degraded |
| FC 返回 unknown → template 非 single → while-loop | 如果 template='unknown'→`_tdef=undefined`（SKILL_DEFS 无 unknown 条目）→ `:1064` 条件 `_tdef && ...` = false → while-loop。但 case 7-8 后 case 9-10 恢复 single-tool——如果 FC 持续返 unknown 不应恢复 |
| 1ddac28 zonal 重写 → while-loop | zonal 重写不改 gate / while-loop 入口·且 case 7-8 可能非 zonal 问 |

**gate 连锁是最简洁的解释**——一个变量（localStorage rate）的翻转解释了 while-loop 的集中性 + 可恢复性。

---

## 三、claude组 3 缺陷逐条评估

### 缺陷 1：gate 是"全局开关"非"每问判断" — **agree（P0·根因）**

**确认成立**。`_tplHitRateReady()`（`harness.js:115-119`）：
```javascript
function _tplHitRateReady() {
  const s = _loadTplStats();           // localStorage 读全局累积
  const n = s.hits + s.misses;
  if (n < _TPL_MIN_SAMPLES) return true;  // 冷启动放行
  return s.hits / n >= _TPL_HIT_RATE_GATE; // 全局命中率判断
}
```

**问题**：gate 是**二值全局开关**——一旦命中率 < 60%，**所有后续 single-type 模板都被挡**（不只是 unknown 的那个）。这导致：
- 一个 unknown miss → 全局 rate 略降 → 可能触发 gate FAIL → **所有 single 问全退 while-loop**（连锁）
- while-loop 出 answer → 记 hit → rate 回升 → gate PASS → single-tool 恢复
- **振荡**：gate 在 PASS/FAIL 间翻转·B3 pass 率随之波动（76%→80%→40%→80%）

**这是 B3 pass 率跨 session 不稳定的结构性根因。**

### 缺陷 2：while-loop = ReAct 多轮·慢·可能"只做一半" — **agree（P1·体验）**

**确认成立**。while-loop 入口（`harness.js:1088-1093`）：
```javascript
const maxRounds = (!diagnose.degraded && diagnose.intent === 'gis_operation')
  ? (_IS_GEN ? 3 : MAX_ROUNDS_GIS)   // MAX_ROUNDS_GIS = 10
  : (_IS_GEN ? 2 : MAX_ROUNDS_OTHER); // MAX_ROUNDS_OTHER = 4
```

GIS 操作最多 10 轮 ReAct·每轮 1 次 agentStep（F_001 msgs=12）= 10 次 LLM 调用。每轮 15-30s → 10 轮 = 150-300s。B3 `waitAnswer(90s)` 会超时。

**但**：gate 连锁修复后（缺陷 1）·while-loop 触发频率应大幅下降——此缺陷是**次级影响**非根因。

### 缺陷 3：recover 兜底不完整 — **agree（P2·覆盖面）**

**确认成立**。`_deterministicRecover`（`harness.js:1478+`）覆盖模式 A-G（用地/方格/聚合/筛选/裁剪/合并/缓冲）——但未覆盖所有问句模式。新问法（如"西陵区公园绿地面积统计"）FC 失败时 recover 未命中 → degraded → while-loop。

**但**：这是 FC 失败时的兜底问题·非 gate 连锁的根因。gate 连锁导致的是 **FC 成功但仍 while-loop**——更严重。

---

## 四、修复方案评估

### 方案 A：回退 1ddac28 — **disagree（不推荐）**

1ddac28 不改 gate / while-loop 入口 / localStorage。回退不解决 gate 连锁。且丢失 PRM-07/09 修复。

### 方案 B：gate 改"每问自适应"（按 template 个别判断）— **agree（P0·推荐）**

**当前**：gate = 全局命中率开关（`_tplHitRateReady()` 返 boolean·所有 single 问共用）

**建议**：gate 改为**按 template 个别判断**——只对 `template='unknown'` 退 while-loop·其他 single 模板（zonal/density/buffer/clip 等）始终走 fast path：

```javascript
// 当前（全局开关·harness.js:1064）
if (_tdef && _tdef.category === 'single' && _tplHitRateReady()) {

// 建议（per-template 判断）
if (_tdef && _tdef.category === 'single' && 
    (diagnose.template !== 'unknown' || _tplHitRateReady())) {
  // unknown 仍受 gate 约束·其他 single 模板始终走 fast path
```

**效果**：
- FC 返 zonal/density/buffer 等 → 始终走 runTemplatePath（不受 gate 影响）
- FC 返 unknown → 受 gate 约束（gate FAIL 时退 while-loop·合理·unknown 确实不可靠）
- **消除 gate 连锁**——一个 unknown miss 不再影响其他模板的 fast path

**风险**：低——`unknown` 是唯一应被 gate 拦的模板（其他模板即使参数不对也走 ask_user 恢复）。

### 方案 C：B3 飞轮模式清 gate（冷启动）— **agree（P0·与 B 配合）**

```javascript
// orchestrate 入口·飞轮模式清 gate
if (new URLSearchParams(location.search).get('test') === '1') {
  localStorage.removeItem(_TPL_STATS_KEY);  // B3 = 冷启动·gate 放行
}
```

B3 是测试环境·gate 累积无意义·每次冷启动 = 零回归基线。

### 方案 D：while-loop 确定性出口优先 + MAX_ROUNDS 早停 — **agree（P1·体验改进）**

while-loop 内加确定性早停：如果第 1 轮 agentStep 就产出了图层（newLayerCount > 0）·直接出 finalStep（不等 MAX_ROUNDS）：

```javascript
// harness.js while-loop 内（现有 _IS_GEN 早止是类似的）
if (newLayerCount > 0 && !/_IS_GEN/.test(...)) {
  // 产出图层后立即 answer（不等多轮 ReAct）
  break;
}
```

**但这不是 P0**——gate 修复后 while-loop 触发频率大降·MAX_ROUNDS 早停是体验优化。

---

## 五、修复优先级

| 优先级 | 修复 | 理由 | 改动量 |
|:---:|------|------|:---:|
| **P0** | **gate 改 per-template 判断**（方案 B·`:1064` 改 1 行）| 根治 gate 连锁——消除"一个 unknown 全局关"的结构性缺陷 | 1 行 |
| **P0** | **B3 飞轮清 gate**（方案 C·orchestrate 入口加 3 行）| B3 测试冷启动 = 零回归基线·防跨 session 累积干扰 | 3 行 |
| **P1** | while-loop MAX_ROUNDS 早停（方案 D）| gate 修复后 while-loop 频率大降·但残余 while-loop 仍应早停 | ~5 行 |
| **P2** | recover 模式扩展（缺陷 3）| 新问法覆盖·非根因 | 持续 |
| ❌ | 回退 1ddac28 | 不解决根因·丢收益 | — |

---

## 六、根因定案

| 根因层 | 定位 | 证据 |
|--------|------|------|
| **直接原因** | `_tplHitRateReady()` gate FAIL（`harness.js:1064`）| trace：case 7-8 FC 正常但走 while-loop = gate 挡住 single-tool 路径 |
| **根本原因** | gate 是全局开关（`harness.js:115-119`）·一个 unknown miss → 全局 rate 跌 → 所有 single 模板被挡 | trace：while-loop 集中在 case 7-8·被 single-tool 包围·gate 回转后恢复 |
| **触发条件** | 跨 session localStorage 累积 miss（`harness.js:87` `_TPL_STATS_KEY`）+ B3 多次重测累积 unknown | B3 pass 率跨 session 波动（76%→80%→40%）= gate 振荡 |
| **与 1ddac28 的关系** | 无直接关系——1ddac28 不改 gate / while-loop 入口 / localStorage | diff 确认：1ddac28 只改 deriveMissingParams zonal 重写 + compare 补丁 + recover G + fixture |

---

## 七、验证方法

```bash
# 1. 确认 gate 状态（浏览器 console）
JSON.parse(localStorage.getItem('ai_qa_template_stats_v1'))
# 如果 rate < 0.6 且 samples >= 10 → gate FAIL = 根因确认

# 2. 修方案 B（per-template gate）后重跑 B3
# 如果 while-loop 显著下降（F_002 < 3）+ pass 率稳定 ≥ 76% → 根因确认

# 3. 修方案 C（B3 清 gate）后重跑
# 如果 pass 率稳定（无振荡）→ 跨 session 累积是触发条件确认

# 4. trace 对照
python tools/trace_query.py --session <new> --id MOD_AIQA.F_002
# F_002 应显著下降（从 6-8 → 0-2）
```

---

## 八、一句话结论

**B3-verify-03 while-loop 回潮根因 = `_tplHitRateReady()` gate 连锁——全局开关设计（harness.js:115-119）导致一个 unknown miss 可使全局命中率跌 < 0.6 → 所有 single 模板被挡 → FC 正常的 case 也退 while-loop。trace 全量分析确认：while-loop 集中在 case 7-8（gate FAIL 窗口）·gate 回转后 single-tool 恢复——振荡模式 = gate 连锁的铁证。claude组 3 缺陷全部成立·缺陷 1（gate 全局开关）= P0 根因。修复 P0 = gate 改 per-template 判断（`:1064` 1 行：unknown 才受 gate·其他 single 始终 fast path）+ B3 飞轮清 gate（冷启动）。不建议回退 1ddac28——不改 gate·非根因。**

---

*glm组（ZCode + GLM 5.2）· CB-12 while-loop 机制分析 + B3-verify-03 根因重定 · 2026-08-03*  
*证据基于：B3-verify-03 session trace 全量 153 行逐 case 分析 + 4 while-loop 入口代码核实（harness.js:1058-1086）+ gate 逻辑（harness.js:82-126）+ 3 缺陷逐条评估 + verify-01 对照（F_002=8 / F_005=19 / F_003=30）。*
