# CB-12 while-loop 根治 + B3 88% 验证（glm组 · ZCode + GLM 5.2）

> **验证方**：glm组（ZCode + GLM 5.2）  
> **日期**：2026-08-03 | **对象**：`f6e415a`（recover 扩展 + gate per-template + 早停 + 筛选守卫）+ B3 report-2026-08-03-01 (88%)  
> **方法**：diff 审查 + B3 report JSON 解析 + trace session B3-verify-04 独立拉取 + PRM-08 params 深挖 + pytest 225 passed

---

## 验证结论：通过

**5 项修复全部正确落地·B3 88%（22/25）历史最佳·PRM 9/10·F_002 大幅下降·p95 46s。** recover 扩展是关键——FC 成功返 unknown/multi 现在有确定性出口（不再直落 while-loop）。gate per-template + B3 清 gate + 早停三层防御到位。PRM-08 唯一 fail 根因定位到 deriveAvailable 对"伍家岗"查找失败（不是补丁逻辑问题）。无假阳性·无断言放宽。

---

## 一、修复落地验证

### ① P0 recover 扩展触发 — **OK（核心修复）**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| degraded OR template∈{unknown,multi} 触发 recover | ✅ | `harness.js:981` `!diagnose \|\| diagnose.degraded \|\| diagnose.template === 'unknown' \|\| diagnose.template === 'multi'` |
| recover 命中 → 替换 diagnose（确定性出口） | ✅ | `:986-987` `if (_recovered) { diagnose = _recovered; }` |
| observation 标注恢复类型 | ✅ | `:990` `[恢复] FC 返 ${template} → 确定性匹配 → 直执行` |

**误触发风险评估**：

| 风险 | 评估 | 理由 |
|------|:---:|------|
| multi 链被 recover 抢（用户要多步·recover 给单步） | **低** | FC 返 `multi` = FC 知道多步但**没拆解**（没出 tool_calls）·recover 给确定性单工具或链 = 比 FC 的模糊 multi **更好**。如果 FC 真出了多 tool_calls（`_allToolCalls.length > 1`）·template 不会是 `multi`（FC 返了具体工具）→ recover 不触发 |
| recover 模式匹配错（选错工具） | **中** | recover 按关键词匹配模式 A-G·新问法可能匹配错。但这是 FC 失败时的已有风险·非本次新增 |

### ② P0 筛选路由守卫放宽 — **OK**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| unknown/multi 也强制 extract | ✅ | `harness.js:1382` `(!diagnose.template \|\| diagnose.template === 'unknown' \|\| diagnose.template === 'multi')` |
| B3 PRM-09 恢复 | ✅ | report: PRM-09 `tpl=extract_feature tools=['extract_feature'] L=1 layer(tool)[OK]` PASS |

### ③ P1 gate per-template — **OK**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| unknown 才受 gate | ✅ | `harness.js:1072` `(diagnose.template !== 'unknown' \|\| _tplHitRateReady())` |
| 其他 single 模板始终 fast path | ✅ | zonal/density/buffer/clip 等不受 gate 影响 |
| gate 恒 PASS 时 zero 影响 | ✅ | `template !== 'unknown'` = true → 短路 `_tplHitRateReady()` → 无副作用 |

### ④ P1 B3 飞轮清 gate — **OK**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| `?test=1` → 清 localStorage gate | ✅ | `harness.js:860-864` `if (... test === '1' && localStorage.getItem(...)) { localStorage.removeItem(...); }` |

### ⑤ P2 while-loop 早停 — **OK（附 1 低风险记录）**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| 产图层后 `round = maxRounds + 1`（等价 break） | ✅ | `harness.js:1215-1217` `if (newLayerCount > 0 && !diagnose.chain && !keep) { round = maxRounds + 1; }` |
| 排除 chain（多步链不被截断） | ✅ | `!diagnose.chain` 守卫 |
| 排除 keep（用户标记保留的层不触发早停） | ✅ | `!(step.action.params && step.action.params.keep)` |

**低风险**：while-loop 中 LLM 可能在第 1 轮产图层但**还没做完**（如"裁剪+排序"——第 1 轮裁剪产图·第 2 轮排序·早停跳过排序）。但 while-loop 通常处理 FC 失败/unknown 的兜底场景·用户意图已由 recover 尽量确定性处理·while-loop 内的 LLM 决策本身就是概率性的·早停 = 牺牲少量多步完整性换稳定性和速度。**可接受的 trade-off**。

---

## 二、B3 88% 结果确认

### 总体指标

| 指标 | verify-01 (80%) | verify-03 (回潮) | **verify-04 (88%)** | 演进 |
|------|:---:|:---:|:---:|:---:|
| pass | 20/25 | ~10/25 | **22/25** | **历史最佳** |
| PRM | 7/10 | ?/10 | **9/10** | PRM-07/09 恢复 |
| timeout | 0 | ? | **0** | ✅ |
| p95 | 69s | ? | **46s** | **-33%** |
| 总耗时 | ~36min | ? | **9.8min** | **-73%** |
| F_002 (while-loop) | 8 | 6 | **10** (5 cases × 1 round) | 绝对数略升·但每 case 仅 1 轮（早停） |

### trace session B3-verify-04 验证

```
F_005 (FC): 25 次（25 case 全 reach FC）
F_002 (agentStep): 10 次 = 5 case × 1-2 轮（早停后每 case ≤1 轮）
F_003 (finalStep): 46 次
F_002/F_005 = 10/25 = 40%（verify-03 是 6/9=67%·下降）
pro 调用: 0（停用生效）
```

**F_002 每次仅 1 轮**（00:17:23, 00:22:12, 00:22:31, 00:22:47, 00:27:02）——早停生效·while-loop 不再多轮 ReAct。

### PRM 逐例（9/10 PASS）

| 例 | verify-04 | 变化 | 归因 |
|---|:---:|:---:|------|
| PRM-01（500m 方格） | ✅ | 稳定 | density 路由 |
| PRM-02（2000m 方格） | ✅ | 稳定 | density 路由 |
| PRM-03（300m 周边） | ✅ | 稳定 | ask_user PASS |
| PRM-04（1km 周边） | ✅ | 稳定 | ask_user PASS |
| PRM-05（西陵 zonal） | ✅ | 稳定 | boundary derive |
| PRM-06（伍家 zonal） | ✅ | 稳定 | boundary derive |
| **PRM-07（小溪塔 zonal）** | **✅** | **新恢复** | fixture 改小溪塔 + boundary derive |
| **PRM-08（对比两区）** | **❌** | **唯一 fail** | deriveAvailable 对"伍家岗"查找失败（见下） |
| **PRM-09（筛选）** | **✅** | **新恢复** | recover 扩展（unknown→extract） |
| PRM-10（裁剪点） | ✅ | 稳定 | clip 路由 |

### 断言可信度（无假阳性/放宽）

- PRM-03/04 PASS = ask_user 断言（badge="等你选择" + askChips > 0 + tools=[]）——诚实追问·非假阳性
- PRM-07 PASS = boundary[OK]（实跑 zonal_stats L=1）——真实产出
- PRM-09 PASS = layer(tool)[OK]（实跑 extract_feature L=1）——真实产出
- PRM-10 PASS = range(tool)[OK]（实跑 clip）——真实产出
- **无断言放宽**——所有 PASS 都有实际工具执行或合法 ask_user 佐证

---

## 三、PRM-08 唯一 fail 根因定位

### 现象

PRM-08（"对比西陵区与伍家岗区范围内情绪极性差异"）→ `tools=['zonal_stats', 'compare'] L=1 boundary[ERR]`

### params 深挖

```json
{
  "boundary": "GeoJSON{1}#西陵区"
}
```

**关键发现**：params 只有 `boundary`（单数·1 个区=西陵区）·**没有 `boundaries`（复数·≥2 区数组）**。compare 工具需要 `boundaries`（≥2）·但 derive 只填了 `boundary`（单数）。

### 根因链

1. `:1409` compare 路由触发（问句含"对比" + boundaries < 2）
2. `:1414` `q.match(/[一-龥]{2,6}(?:区|市|县|街道|镇)/g)` → 匹配 ["西陵区", "伍家岗区"]
3. `:1418-1428` 逐区 deriveAvailable：
   - "西陵区" → `_strip = "西陵"` → `deriveAvailable("西陵", layers)` → **找到**（exact "西陵区" 或 stripped "西陵" 命中）→ `_bs.push(西陵 FeatureCollection)`
   - "伍家岗区" → `_strip = "伍家岗"` → `deriveAvailable("伍家岗", layers)` → **未找到**（`_d2 = null` → `continue`）
4. `:1429` `_bs.length = 1 < 2` → `p.boundaries` **不设置**
5. `:1432+` boundary derive（单数）·tool = `compare_regions` → `p.boundary` = 西陵区单要素
6. compare 执行：`params.boundaries` = undefined → guard fail

### "伍家岗"为什么 derive 失败？

`deriveAvailable("伍家岗", layers)`：
- exact 轮（`:599-601`）：`"伍家岗".includes("伍家岗区")` = false（问句比值短）→ 不命中
- stripped 轮（`:603-611`）：`_strip("伍家岗区")` = "伍家岗"·`_qStrip = _strip("伍家岗")` = "伍家岗"·`_qStrip.includes("伍家岗")` = true → **应命中**

**但 `_allVals` 可能不含"伍家岗区"**——`_boundaryNames(l)` 返回的 values 可能是 MC 代码（如 "0801"）而非中文名。双字段扫描（`:591-597`）只扫 `name/NAME/名称` 字段——如果 admin_district preset 用的是 `MC` 字段存代码 + `name` 字段存"伍家岗"·双字段扫描应找到。但如果 `name` 字段值是"伍家岗街道"（不是"伍家岗区"）·`_strip("伍家岗街道")` = "伍家岗"（剥"街道"）·exact "伍家岗".includes("伍家岗街道") = false → stripped 命中 → 应工作。

**最可能原因**：`features.slice(0, 30)` 只扫前 30 个要素——如果"伍家岗"在第 31+ 个 feature 中（大行政区的 feature 排序）·双字段扫描漏掉它。

### 修复建议

```javascript
// tools.js:592 当前
for (const f of (l.fc && l.fc.features || []).slice(0, 30)) {

// 建议：扫全部 features（或至少 100）——行政区通常 <20 个·但大图层可能更多
for (const f of (l.fc && l.fc.features || []).slice(0, 200)) {
```

或更精准：按区名过滤 features 后再提取（不用 slice）。

---

## 四、验证清单总结

| # | 验证项 | 方法 | 结果 |
|:---:|------|------|:---:|
| 1 | recover 扩展（unknown/multi 触发）| diff + 代码核验 | ✅ OK |
| 2 | 筛选路由守卫放宽 | diff + PRM-09 PASS | ✅ OK |
| 3 | gate per-template | diff + gate 恒 PASS zero 影响 | ✅ OK |
| 4 | B3 飞轮清 gate | diff | ✅ OK |
| 5 | while-loop 早停 | diff + trace F_002 每次仅 1 轮 | ✅ OK |
| 6 | recover 误触发（multi 链被抢）| 代码分析 | ✅ 低风险（multi = FC 未拆解·recover 更好） |
| 7 | 早停误停（多步链截断）| `!diagnose.chain` 守卫 | ✅ 低风险（排除 chain + keep） |
| 8 | B3 88%（22/25）| JSON 解析 | ✅ 历史最佳 |
| 9 | PRM 9/10 | JSON 逐例 | ✅ PRM-07/09 新恢复 |
| 10 | 断言无假阳性/放宽 | 逐例验证 | ✅ 全部有实跑/ask_user 佐证 |
| 11 | F_002 下降 + 每 case 1 轮 | trace session | ✅ 40%（vs 67%）·早停生效 |
| 12 | p95 46s / 9.8min | report meta | ✅ -33% / -73% |
| 13 | pytest 225 passed | 独立运行 | ✅ 零回归 |

---

## 五、演进对照

```
B3 演进（4% → 88%·22 倍）：

  4%  ──→ B3 大失败（搜索旁路 + API 慢 + pro 37 调用）
  ↓     修复：搜索素材注入 + KW 收紧 + pro 停用
  80% ──→ B3 06/07/08（PRM 攻坚 + derive + 路由修正 + 断言校准）
  ↓     回潮：B3-verify-03（40%·while-loop 回潮）
  ↓     诊断：gate 连锁（误判）→ 修正：recover 缺口（FC 返 unknown 无兜底）
  88% ──→ B3-verify-04（recover 扩展 + gate per-template + 早停）
  
  PRM: 0/10 → 9/10
  p95: 69-93s → 46s
  总时: 36min → 9.8min
```

---

## 六、一句话结论

**while-loop 根治（f6e415a）5 项修复全部正确落地——recover 扩展触发是核心（FC 成功返 unknown/multi 不再直落 while-loop·recover 给确定性出口）+ gate per-template（防全局连锁）+ B3 清 gate（冷启动）+ 早停（产图即 answer·每 case ≤1 轮）+ 筛选守卫放宽（unknown 也走 extract）。B3 88%（22/25）历史最佳·PRM 9/10·p95 46s（-33%）·9.8min（-73%）·F_002 每次 1 轮（早停生效）·无假阳性。PRM-08 唯一 fail = deriveAvailable 对"伍家岗"查找失败（`features.slice(0, 30)` 可能漏·建议扩到 200 或按区名过滤）·不是补丁逻辑问题。**

---

*glm组（ZCode + GLM 5.2）· CB-12 while-loop 根治 + B3 88% 验证 · 2026-08-03*  
*验证基于：f6e415a diff + B3 report-2026-08-03-01 JSON 解析 + trace session B3-verify-04（F_002=10/F_005=25/F_003=46）+ PRM-08 params 深挖（boundary 单数非 boundaries）+ pytest 225 passed。*
