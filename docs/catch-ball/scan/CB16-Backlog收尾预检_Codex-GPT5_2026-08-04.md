# CB-16 发版 backlog 收尾 实施预检（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `c53aa99`（③w5 后·发版 backlog 打包·先讨论再实施）
> **范围**：只读评估 · 不改代码 · 不 commit
> **验证手段**：代码/数据逐项核验（行政区 fixture 字段·district-stats 依赖·fallback 字段匹配·boundary 来源识别）

---

## 结论先行

**草案总体可行 · 无 P0**，但需修正 3 项 P1（含 1 项上一轮硬化实际失效的发现）+ 2 项 P2：

- **【P1】RST-L06 fallback（③w5 已实施）对真实 preset 无效**：`行政区.geojson` 要素 properties **仅有 `MC` 字段**（manifest `nameField:"MC"`）·而 harness.js:1135 fallback 硬编码匹配 `name || NAME || name_field`——三者均缺 → **永不命中**·硬化是死代码。修法：fallback 复用 manifest nameField（MC）或 deriveAvailable 同款字段解析（`b.field`/双字段扫描）。
- **【P1】item 3（fixture 9→4）有破坏性依赖**：`district-stats.js` 的 `_TUAN_MAP` 按 **9 个 MC** 组 8 组团（含小溪塔/龙泉/白洋/生物产业园/龙泉绿心）做 L1 数据总览 PIP 分类——清成 4 要素后 4 个组团恒空·该功能损坏。建议：**不动 fixture**（PRM-07 根因是 FC 直供绕过白名单·由 item 2 兜底）·或确需清理则同步改 district-stats.js（范围扩大·需用户确认）。
- **【P1】item 2 需先定义 boundary 来源识别机制**：FC 直供 boundary 是裸 geojson·**无 source 标记**——无法从对象本身判断「preset 行政区」vs「用户上传层」。建议判据：boundary 要素名（按 manifest nameField 解析）与已加载「行政区」preset（registry source=preset）内要素名**精确匹配** → 判定来自 preset → 白名单校验；无匹配 → 视为用户提供·不动（避免误伤）。拒绝后走 request_upload 措辞需同时设置 `diagnose.data_plan.strategy='request_upload'`（否则清 boundary 后 zonal 无 boundary 失败→gap 措辞·非 request_upload 措辞）。

---

## 一、逐项核验

### 1. footer「未生成图层」条件化 —— 对（P2）
- 现 footer（:231-232）恒含「未生成图层」·failedObs=0 分支也出现——草案改「未完成分析」正确·与 request_upload 分支**不冲突**（footer 全分支统一·条件化仅换措辞·request_upload+零尝试时「未完成分析」更贴切）。
- 补充：degraded（无法理解）分支同样 failedObs=0·footer 同步走「未完成分析」·无需单列。

### 2. FC 直供 boundary 白名单校验 —— 方向对·机制需定（P1）
- 08-04 PRM-07 `GeoJSON{1}#小溪塔` = FC 直供单要素绕过 derive 白名单——校验点应加在 deriveMissingParams 的 boundary 分支（:1490-1530 boundary-suspect 旁）。
- **来源识别**：裸 geojson 无 source → 用「要素名 ∈ 已加载行政区 preset（source=preset）要素名集合」判定预设来源（见结论 P1③）；用户上传层不匹配 → 不校验（防误伤·Q2）。
- **拒绝后路由**：需设 `data_plan.strategy='request_upload'` + gap 文案（"该区域不在已固化行政区划库·请上传标准范围资料"）·否则落 gap 而非 request_upload 措辞。

### 3. preset fixture 清理 —— 需重新定标（P1）
- 实证：行政区.geojson 9 要素·仅 MC 属性·MC=龙泉/猇亭区/点军区/小溪塔/白洋/西陵区/龙泉绿心/伍家岗区/生物产业园。
- **district-stats.js 依赖 9 MC → 8 组团**（loadDistricts/classifyPointsByDistrict）——清 4 要素即坏 4 组团（小溪塔/龙泉/白洋/高新区·生物产业园 恒空）。
- 建议：**保留 fixture·白名单已在 derive 层生效·PRM-07 由 item 2 兜底**（fixture 并非根因）；若用户坚持数据只含真实区划 → 同步改 district-stats.js（_TUAN_MAP 收敛）·范围扩大·需用户拍板。

### 4. RST-L06 复跑 —— 前提是先修 fallback（P1）
- 方法建议：B3「成果范式」子集（含 RST-L06）1 次 + 单例 ×3（LLM 方差）·并先补 per-test fetch 证据（audit 无 chat 日志·否则 FAIL 仍无法定位分支）。
- **先修 fallback 字段 bug（MC）再复跑**——否则复跑只是验证"没修过的硬化"·结论不可信。

### 5. eval 注释精确化 + 复采 —— 对（P2）
- 注释改：「select_template 对复合问（「…并排序」）仍可返 multi·这两条问句的 canonical 单工具为 clip/density（multi 由前端 CHAIN_REGISTRY 覆盖）」。
- 复采时机：发版前与 B3 快照/link_checkup 同批·记录日期/模型/温度·≥2 次取均值（76%↔92% 跨运行差 = 方差实证）。

---

## 二、7 问速答

1. **footer 条件化对**：failedObs=0 →「未完成分析」·与 request_upload 分支不冲突；degraded 分支同享。
2. **白名单校验逻辑对**·但需来源识别机制（preset 要素名匹配判定）·避免误伤上传层；拒绝后须设 data_plan.strategy='request_upload' 才走到对应措辞。
3. **fixture 清理属数据改动**（非 raw 红线·但已入库且被 district-stats 依赖）·9→4 破坏 8 组团 → 建议不动·由 item 2 兜底。
4. **复跑方法**：B3 成果范式子集 + 单例 ×3 + per-test 证据·且先修 fallback MC 字段 bug。
5. **eval 注释/复采**：发版前与快照同批·记录元数据·≥2 次。
6. **5 项均必要但需调序**：1（footer·独立小改）→ 2（白名单·P1）→ 4（修 fallback 后复跑·P1）→ 5（复采·P1）→ 3（重新定标·可能 drop·P1 决策）。
7. **承重零触碰**：全在前端 harness/数据/文案·不碰 diagnose prompt/三态出口/ChatRequest ✓。

---

## 三、优先级

| 级别 | 项 |
|---:|---|
| **P1 修正** | RST-L06 fallback 字段改 MC（manifest nameField）· item 3 重新定标（不动 fixture 或联动 district-stats）· item 2 来源识别 + request_upload 路由机制 |
| **P2** | footer 条件化（可直接做）· eval 注释精确化 + 发版前复采 |

---

## 四、判定

- **草案可行 · 无 P0**。5 项方向均正确·但 item 2/3 需按 P1 修正实施·item 4 需先修上一轮 fallback 字段 bug。
- **P1 修正 ×3 + P2 ×2**（如上）。
- **独立判断**：基于代码/数据逐项核验（fixture 字段·district-stats 依赖·fallback 匹配·boundary 来源），未参考 glm组 本轮报告。

---

## 附录：关键证据

| 依据 | 结论 |
|---|---|
| 行政区.geojson 要素 props = 仅 `MC` | manifest nameField=MC·fallback 硬编码 name/NAME/name_field 永不命中 |
| DATA/boundaries/presets/manifest.json | admin_district nameField="MC" |
| frontend/js/district-stats.js `_TUAN_MAP` | 9 MC → 8 组团·fixture 清 4 即坏 4 组团 |
| harness.js:1135-1140 | fallback 匹配字段缺 MC → 死代码 |
| harness.js:1490-1530 | FC boundary 校验点（boundary-suspect 旁）·裸 geojson 无 source |
| harness.js:231-232 | footer 恒含「未生成图层」·条件化无冲突 |

*登记：docs/catch-ball/scan/（RULES 4.1 命名）。本报告只读评估·未改代码·未 commit。*
