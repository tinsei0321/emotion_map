# CB-16 措辞修复 + 发版遗留问题 实施后检查（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `c53aa99`（③w5·先验后推未推）
> **范围**：只读评估 · 不改代码 · 不 commit
> **验证手段**：代码逐行核验 + 历史审计对照（eval 92% 无法本地复跑·需 API Key·以 claude组 重跑记录为准）

---

## 结论先行

**实施通过 · 可推 · 无 P0/P1 需修项。** ③w4b 预检 P1×5 全采纳且实现正确：措辞两处分支、eval 标尺纠错、RST-L06 preset fallback、radius/cell_size 门控修复均核实。5 项 P2 建议（非阻塞）：

- **【P2】「图层」字眼仍有泄漏**：composeGapCard 的 guide footer 恒含「在没有可靠数据或**未生成图层**前…」（:231-232）——零工具尝试分支也会出现·与「非图层叙事」目标不完全一致。建议条件化或改「未完成分析」。
- **【P2】eval 注释表述不严谨**：注释称「select_template 不返回 multi」——实际 select_template 对复合问（「…并排序」·eval 第 13 条仍为 multi）返回 multi·更准确应为「这两条问句的 canonical 单工具是 clip/density·multi 由前端链覆盖」。
- **【P2】eval 单次采样**：92% 为单次重跑·含 LLM 方差（改标尺仅贡献 +2 期望·34 命中仍需 Flash 实际返回 clip/density）·建议发版前再采一次并记录日期/模型。
- **【P2】FC 直供 boundary 绕过白名单**：08-04 PRM-07 的 `GeoJSON{1}#小溪塔` 即 FC 直供单要素（boundary-suspect 只查 >1 特征/字符串·白名单在 derive 层）——backlog 应同时记「FC boundary 白名单校验」与「preset fixture」。
- **【P2】补 e2e-seam 措辞断言**：本轮未新增任何测试（commit 无 tests/ 改动）·预检 P2 项未落地——建议补 composeGapCard 两分支 + gap 出口零尝试「不含图层字眼」断言。

---

## 一、核验结果

### ②a 措辞 —— 正确（P2 一处）

- gap 出口：`_triedTools = failedObs.length > 0` → tried 时 composeGapCard + 追加「**诚实结论**：本轮未产出新图层。」；零尝试 → **仅 composeGapCard**（不追加图层行）——预检 P2「两处分支」要求已覆盖 ✓。
- composeGapCard：零 failedObs 分支置于默认前——`diagnose.degraded` →「我没能理解这个问题的分析需求」（无法理解）/ 非 degraded →「这个问题我暂时无法直接回答」（暂无法回答）·head 均无「图层」✓；failedObs>0 → 保留「没能生成可用的图层」✓。
- failedObs 判据可靠（仅在工具失败时 push·:753/755/1261 核实）·degraded 区分合理（诊断失败 vs 执行未开始）。
- **P2**：guide footer「未生成图层」字眼泄漏（见结论）。

### ②b-1 eval 标尺 —— 合理（P2 两处）

- 两条 multi 期望改 clip/density（eval :88-89）·注释明示「multi 是前端 CHAIN_REGISTRY 概念·eval 测 v1 single-tool select_template·76% 是标尺不匹配架构」——**改标尺非改路由**·符合 ③w4 预检「覆盖偏好非功能缺陷」判定路径 ✓。
- 92%（34/37）与 MISS 3（rank/zonal·clip/overlay·hotspot/density）为既有歧义清单内·与冻结基线已知歧义一致 ✓（无法本地复跑·以记录为准）。
- **P2**：注释「select_template 不返回 multi」不严谨（复合问返回 multi·第 13 条仍是）；单次采样需复采。

### ②b-2 RST-L06 fallback —— 正确

- chain pre-check（:1129-1144）：deriveAvailable 无匹配 + 问句含 `(.+?)(?:区|市|县)` → 已加载「行政区」层取**单要素**（name/NAME/name_field 匹配）·无区名不猜 ✓——feature 级提取 ✓·条件收敛 ✓。
- **注**：fallback 依赖行政区层已加载（未做 preset 注册表异步加载）——RST-L06 测试显式加载·演示场景通常已加载·可接受。
- 根因实证仍缺（同 ③w3b）：硬化是防御面·08-04 FAIL 是否由此修复需**复跑 RST-L06 验证**（P2）。

### ②b-3 buffer/cell_size 门控 —— 正确

- radius（:1572）/cell_size（:1568）改判 `tool === 'X' || diagnose.template === 'X'`——G5 reroute（lookup_place→buffer / 方格→density）后 template 已更新·旧 tool 变量不再阻塞 ✓；OR 放宽仅多填无害参数·无副作用 ✓。

### ②b-4 PRM-07 —— 留 backlog 合理

- 白名单 gate 确认在 `tools.js deriveAvailable`（:622 `_inAdminWhitelist`·preset+行政区层名 → FIXED_ADMIN_DISTRICTS 过滤）——「已在 derive 层实现」属实（CB-14 既有）✓。
- 数据 fixture（preset geojson 含法定功能区）留 backlog（改数据需用户确认）合理 ✓；**补**「FC 直供 boundary 白名单校验」条目（P2·见结论）。

---

## 二、7 问速答

1. **两处分支正确**：gap 出口追加行已按 failedObs 分支·composeGapCard 零尝试分支无「图层」head；但 footer「未生成图层」字眼仍泄漏（P2）。
2. **eval 标尺合理**：multi 是前端链概念·改期望单工具符合架构；92% 可信（无法本地复跑）·MISS 3 为既有歧义非标尺引入；注释表述需精确化（P2）。
3. **RST-L06 fallback 对**：feature 级 + 区名条件 + 无区名不猜 ✓；依赖行政区层已加载（可接受）；建议复跑验证根因（P2）。
4. **门控改判正确**：template 更新后不再被旧 tool 阻塞·OR 放宽无有害副作用 ✓。
5. **PRM-07 留 backlog 合理**：白名单已在 derive 层·fixture 改动需用户确认；补 FC boundary 校验条目（P2）。
6. **承重零触碰**：diagnose prompt 未动（eval 改的是测试期望非 prompt）·exit:'gap'/quickIntent/answered/narratedAnswer/ChatRequest 未动 · commit 仅 harness.js + eval + docs ✓。
7. **测试基本够**：pytest 277/ESM-OK 以记录为准（commit 无 tests/ 改动·+1 无法本地核实）；**建议补 e2e-seam 措辞分支断言**（P2·预检项未落地）。

---

## 三、优先级

| 级别 | 项 |
|---:|---|
| **P2** | composeGapCard footer「未生成图层」措辞条件化 · eval 注释精确化 + 发版前复采 · RST-L06 复跑验证 · FC boundary 白名单校验入 backlog · e2e-seam 措辞分支断言 |

---

## 四、判定

- **判定：实施通过 · 可推**。P1×5 全采纳·实现与预检一致·无 P0/P1 需修项。
- **P2 ×5**（措辞残留/注释/采样/backlog 条目/测试补强）——均非阻塞。
- **独立判断**：基于代码逐行核验 + 历史对照，未参考 glm组 本轮报告。

---

## 附录：关键证据

| 依据 | 结论 |
|---|---|
| harness.js:1335-1341 | gap 出口 `_triedTools` 分支·零尝试不追加「未产出新图层」行 |
| harness.js:226-233 | composeGapCard 零 failedObs 分支（degraded/非 degraded）·head 无「图层」 |
| harness.js:231-232 | guide footer 恒含「未生成图层」→ P2 残留 |
| harness.js:1129-1144 | RST-L06 fallback（feature 级·区名条件·无区名不猜） |
| harness.js:1568/1572 | radius/cell_size 门控 `|| diagnose.template === 'X'` |
| tools.js:588/:622 + :8 | deriveAvailable 内白名单（FIXED_ADMIN_DISTRICTS·CB-14 既有） |
| tests/eval_template_flash.py:88-89 | multi→clip/density 标尺纠错 + 注释 |
| commit c53aa99 stat | 仅 harness.js + eval + docs·无 tests/ 新增（e2e-seam 措辞断言未补） |

*登记：docs/catch-ball/scan/（RULES 4.1 命名）。本报告只读评估·未改代码·未 commit。*
