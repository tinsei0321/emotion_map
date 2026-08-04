# CB-16 发版 backlog 收尾 实施后检查（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `23efe74`（③w7·先验后推未推）
> **范围**：只读评估 · 不改代码 · 不 commit
> **验证手段**：代码/数据逐项核验（footer/MC/白名单/fixture/district-stats/eval tuple 比较）

---

## 结论先行

**实施通过 · 可推 · 无 P0/P1 需修项。** ③w6 预检 P1×3 全落地且实现正确：footer 条件化、fixture 清 4 + district-stats 收敛、RST-L06 fallback MC 修复、eval 注释精确化（含 tuple 双接受）。4 项 P2 建议（非阻塞）：

- **【P2】陈旧注释三处**：district-stats.js 头部「9 preset MC → 8 组团」、panel.js「8 组团」×4 处、test-assets.js desc「9 要素（…法定功能区）」——功能已数据驱动自适应（4 组团）·注释未同步。
- **【P2】补 fixture 静态守卫**：建议加 validate 式断言「行政区 preset 的 MC 全集 == FIXED_ADMIN_DISTRICTS」·防未来再塞法定功能区回潮（仿 validate_outlet_fields 模式·低成本高价值）。
- **【P2】残余风险记录**：FC 凭空编造非白名单 boundary 的场景未被守卫（fixture 治本后概率低·工具侧校验兜底）——可入 backlog·非本次必做。
- **【P2】eval 复采未执行**：发版前复采（记录日期/模型/温度·≥2 次）为运行项·留发版门禁时做。

---

## 一、逐项核验

### 项 1 footer 条件化 —— 正确
- `_footerLayer = (failedObs && failedObs.length > 0) ? '或未生成图层' : ''` → footer 变「在没有可靠数据前…」（零尝试）/「…或未生成图层前…」（试过）✓。
- 与 request_upload 分支**不冲突**：footer 全分支统一渲染·failedObs=0 时 request_upload 分支同样显示「未完成分析」——语义兼容（数据缺失叙事）✓。

### 项 3 fixture 清理 + district-stats 同步 —— 正确
- 行政区.geojson 现 4 要素（西陵区/伍家岗区/猇亭区/点军区）·与 FIXED_ADMIN_DISTRICTS 完全一致 ✓；`.bak9` 完整备份原 9 要素（1.92MB）✓；新文件保留 UTF-8 BOM（EF BB BF）✓。
- district-stats.js `_TUAN_MAP` 8→4 组团·`loadDistricts`/`classifyPointsByDistrict` 数据驱动·panel.js 渲染自动 4 组团 ✓。
- **PRM-07 根治实证**：test-cases.js PRM-07 用例 `expectRequestUpload: true`——fixture 无小溪塔后 derive 自然失败→request_upload·期望行为达成 ✓（此前 FAIL 源于 9 要素 preset 供 FC 锚定）。

### 项 4 RST-L06 fallback MC 修复 —— 正确（死代码消除）
- fallback 匹配字段补 `f.properties.MC`（manifest nameField=MC）·pre-set 要素仅 MC 时不再永不命中 ✓。
- 复跑留待前台 serve（serve 后台不稳）——**不阻塞**：硬化本身已正确·复跑是根因实证项（P2·建议带 per-test fetch 证据）。

### 项 5 eval 注释精确化 —— 正确
- 注释改为「select_template 对多数单工具问返单工具·复合问（…并排序）可能返 multi」——与实现一致 ✓。
- **tuple 双接受已适配**：`ok = got == expected if isinstance(expected, str) else got in (expected or ())`（eval :138）——「西陵区的商业用地」期望 `('clip','overlay')` 不再恒 MISS ✓。

---

## 二、7 问速答

1. **footer 条件化正确**：零尝试无「图层」·与 request_upload 分支不冲突（全分支统一·措辞条件化）。
2. **fixture 清理正确**：9→4 与白名单一致·district-stats 8→4 同步·.bak9 完整备份·BOM 保留·L1 总览数据驱动渲染 4 组团。
3. **fallback MC 修复对**：死代码消除·复跑留待前台 serve·不阻塞。
4. **eval 注释精确化合理**：+ tuple 双接受治「商业用地」clip/overlay 概率性歧义。
5. **影响面核查通过**：功能引用方仅 district-stats（已同步）·panel.js 渲染自适应·PRM-07 测试期望与清理后行为一致；残余为注释陈旧（P2）。
6. **承重零触碰**：diagnose prompt/三态出口/ChatRequest 未动·改动在 harness 前端 + 数据 fixture（用户拍板）✓。
7. **测试**：pytest 277/ESM-OK 以记录为准（本地无 pytest）；**建议补 fixture 静态守卫**（preset MC 全集 == FIXED_ADMIN_DISTRICTS·防回潮·P2）。

---

## 三、优先级

| 级别 | 项 |
|---:|---|
| **P2** | 陈旧注释同步（district-stats/panel/test-assets）· fixture 静态守卫（MC ⊆ 白名单）· FC 编造 boundary 残余风险入 backlog · eval 发版前复采 |

---

## 四、判定

- **判定：实施通过 · 可推**。P1×3 全落地·实现与预检一致·无 P0/P1 需修项。
- **P2 ×4**（注释/守卫/backlog/复采）——均非阻塞。
- **独立判断**：基于代码/数据逐项核验，未参考 glm组 本轮报告。

---

## 附录：关键证据

| 依据 | 结论 |
|---|---|
| harness.js:240 `_footerLayer` | failedObs>0 才「未生成图层」·零尝试「未完成分析」 |
| 行政区.geojson | 4 要素（西陵/伍家岗/猇亭/点军）·BOM 保留（EF BB BF） |
| 行政区.geojson.bak9 | 完整 9 要素备份（1.92MB） |
| district-stats.js `_TUAN_MAP` | 4 组团·与 fixture 一致（头部注释仍写 8 组团·P2） |
| harness.js:1136-1137 | fallback 补 `f.properties.MC`·死代码消除 |
| eval :138 | tuple 期望比较适配（`got in (expected or ())`）·注释精确化 |
| test-cases.js PRM-07 | `expectRequestUpload: true`·fixture 清 4 后自然达成（根治） |
| panel.js :973-1042 | 「8 组团」注释陈旧×4（渲染数据驱动·P2） |

*登记：docs/catch-ball/scan/（RULES 4.1 命名）。本报告只读评估·未改代码·未 commit。*
