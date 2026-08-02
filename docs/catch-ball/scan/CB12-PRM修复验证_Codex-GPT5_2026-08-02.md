# CB-12 PRM 攻坚修复验证（Codex 第三方）

> **验证方**：Codex（GPT-5，第三方独立评估小组）  
> **验证时间**：2026-08-02 | **分支**：`fix/emc-buglog` @ `cde3cf4`+`8a33080`+`2582c34`（HEAD `ca40c05`）  
> **对象**：PRM 攻坚 P0-a/P0-b/P1/P2 + PRM-08/10 补丁 + B3-06/07 重测  
> **结论**：**修复主体落地属实（有条件通过）**——B3 76-80% 稳定、PRM 路由/模糊匹配/ask 断言四类修复有效；但发现 **2 个断言/通道问题**（PRM-09 假阳性 PASS、PRM-10 路由对多 tool_calls 通道失效）+ **1 个未落地项**（聚合/归因→zonal 强制路由，PRM-06 方差根因）

---

## 一、修复落地验证清单

| 修复 | 判定 | 证据 |
|---|:---:|---|
| P0-a deriveAvailable 模糊匹配 | **OK** | `tools.js:584-594`：剥单后缀（`[区市县街道镇]$`）+ 双向包含 + 最短 2 字。**边界评估**：剥后缀只去尾 1 字符，"西陵区街道"→"西陵区街"再双向包含仍能命中 ✓；"夷陵↔夷陵区"是目标匹配 ✓；误匹配风险（如值"西陵小学"含"西陵"会命中）存在但 deriveAvailable 本就是兜底、且 `_boundaryNames` 只枚举边界层名/字段值——可接受 |
| P0-b 3 条路由修正 | **OK（含 1 个残留误触发 + 1 个通道缺口）** | `harness.js:1344-1353`：方格→density(3d)、裁剪点→clip（2582c34 放宽为 tool!=='clip'）、筛选用地→extract。**残留 1**：`/筛选出/` 裸词（无"用地"上下文）在 FC unknown 时会强制 extract——"筛选出西陵区的情绪点"（应 clip/filter_attr）会被误路由；建议收紧为 `/筛选出?.*(用地|地块|面)/`。**通道缺口（见 PRM-10）**：路由只改 `diagnose.template`，对 `_allToolCalls` 多 call 通道不生效 |
| recover 模式 E | **OK** | `harness.js:1496-1508`：FC 失败兜底 density(3d)+cell derive，与路由 1 同正则，一致 |
| P1 ask_user 断言 | **OK（含 1 个假阳性）** | `test-cases.js:321-325`：badge"等你选择" 或 askChips>0 + 无工具 → PASS；`e2e-seam.js:119` askChips 计数。判定充分区分诚实 ask vs 撒谎（要求无工具执行 + 真实 ask 信号）✓——但 **PRM-09 被误判 PASS（见二）**，ask 类 PASS 需限定场景 |
| P1 `_sum` 数组递归 | **OK** | `test-cases.js:75`：数组元素递归（boundaries 多区序列化可见区名）；浅数组无栈风险 |
| P2 契约 when | **OK** | `tool_contracts.py` density/clip/extract_feature when 补触发句，纯增量无歧义 |
| PRM-08 补丁（compare boundaries） | **partial** | `harness.js:1355-1372`：FC 已选 compare 且无 boundaries 时也补 derive——条件正确；但 B3-07 仍只填 1 区（见二） |
| PRM-10 补丁（clip 路由放宽） | **partial** | 条件放宽正确，但**对多 call 通道无效**（见二） |

---

## 二、B3-07 PRM 行逐例分析（`report-2026-08-02-07-llm.md`）

| 例 | 07 结果 | Codex 分析 |
|---|---|---|
| PRM-01/02 | PASS（cell=500/2000 ✓） | density 路由 + cell derive 生效 ✓ |
| PRM-03/04 | PASS（ask_user 诚实追问） | ask 断言生效 ✓（badge=分析完成 但 askChips>0 命中——断言第二分支工作） |
| PRM-05 | PASS（zonal·区=GeoJSON{1}#西陵区） | 模糊匹配生效 ✓ |
| **PRM-06** | **FAIL**（tpl=extract_feature·boundary[ERR]） | **方差实锤**：04/06 跑 zonal 过、07 跑 extract——**"聚合/归因→zonal 强制路由"未实现**（讨论方案 P0 主推项未落地），这是 06 的根因 |
| PRM-07 | FAIL（zonal·1→0 层·boundary[ERR]） | 需查：夷陵区是否在测试点数据内（fixture 覆盖西陵/伍家岗·夷陵可能无点）→ 若数据缺即预期无效，非代码缺陷 |
| PRM-08 | FAIL（compare·1 区） | boundaries derive 间歇只填 1 区（伍家岗区在 04 的 PRM-06 能 derive、07 的 08 不能——**方差/数据态差异**）·需逐例复现 geos |
| **PRM-09** | **PASS（ask_user 假阳性）** | "筛选出商业服务业用地的面"本应 extract_feature 执行，07 却判"合法 ask_user"PASS（badge=分析完成 + askChips>0 + 无工具）——**这是断言过宽的假阳性**：任何"ask chips + 无工具"都 PASS，未验证 ask 是否合理（本问不需要澄清）。真实 PRM 应为 **5/10**（01-05） |
| PRM-10 | FAIL（tpl=clip 但 tools=extract+merge） | **路由对多 call 通道失效**：FC 输出 [extract_feature, merge] 多 call → orchestrate 走 `runAllToolCalls`（先于/绕过 derive 路由）→ derive 的 template=clip 不影响多 call 执行。且 clip 路由未 derive range（区名→范围）→ 即使走单工具也会 clip guard 报"需 range" |

---

## 三、B3 结果确认与归因修正

- **76-80% 稳定、0 timeout、p95 69-70s**：与 glm组 预计（22-23 深水 4 例外）大体一致——但 **glm组 预计口径偏高**：真实"链路通畅"数应扣掉 PRM-09 假阳性 → 有效约 18-19/25（72-76%）；
- **PRM 实际稳定数为 5/10 非 6/10**（09 是假阳性 PASS）；06 是方差、07 待数据核、08 待复现、10 是通道缺口——均为已知深水项；
- **修复有效性确认**：4% → 76-80% 的修复贡献（API 恢复之外）真实存在——路由（01/02/10）、模糊匹配（05）、ask 断言（03/04）都有代码落地与运行级证据。

---

## 四、剩余 4 例攻坚建议

1. **PRM-06（方差）**：实现讨论方案 P0 主推项——**"聚合/归因/统计 + 区名 → 强制 zonal_stats + boundary derive"**（`deriveMissingParams` 加第 4 条路由，与 方格/裁剪/筛选 同款）；根治 LLM 时对时错的 extract-first 行为。
2. **PRM-07（夷陵 0 层）**：先核对测试点数据是否含夷陵区（fixture 以 西陵/伍家岗 为主）——若缺，改用例数据/预期；若有，查后端 zonal 为何 0 层（边界要素与点层无重叠？）。
3. **PRM-08（compare 1 区）**：逐例复现拿 geos 序列（FC 参数 vs derive 的 `p.boundaries` vs 实际执行 body）——定位是 deriveAvailable 间歇 null 还是执行丢参。
4. **PRM-10（clip 通道）**：① derive 路由修正**同时重写 `_allToolCalls`**（高置信时把多 call 替换为 clip 单 call）；② clip 路由补 **range derive**（区名→行政区层/GeoJSON，仿 boundary derive）——否则单工具路径也卡"需 range"。
5. **PRM-09 断言**：ask_user PASS 收窄——仅在**需要澄清参数的用例**（center 类）放行，且校验 ask 文案含对应参数线索（"哪个/设施/地点"）；或用 `review` 标记代替 PASS（保留人工确认）。

---

## 五、验证结论：**有条件通过**

修复主体真实落地（模糊匹配/3 路由/模式 E/ask 断言/契约/08/10 补丁条件均正确），B3 76-80% 稳定。转"通过"需完成：

1. **PRM-09 假阳性**：ask_user PASS 收窄到 center 类用例（或 review 标记）——否则"链路通畅"数虚高；
2. **PRM-10 通道缺口**：路由修正对 `_allToolCalls` 生效 + clip range derive；
3. **PRM-06 方差**：补"聚合/归因→zonal"强制路由；
4. **PRM-07**：核对夷陵测试数据前提；
5. **PRM-08**：逐例复现定位 boundaries 单区根因。

---

*本报告为 Codex 组独立验证；修复经 diff 读码核验，PRM 逐例经 B3-07 报告行级分析，假阳性/通道缺口为本次新发现。*
