# CB-11 merge 多图层 concat 实现验收（Codex 第三方）

> **验收方**：Codex（GPT-5，第三方独立评估小组）  
> **验收时间**：2026-08-02 | **分支**：`fix/emc-buglog` @ `fa429f9`（`9f84eac` 实现 + `fa429f9` 文档）  
> **对象**：方案 A（后端 `merge(layers=[...])` concat）定稿实现，9 文件改动  
> **方法**：逐条读码核验 6 个关键点 + pytest 实测 + 红线核查 + 渲染路径追踪  
> **结论**：**有条件通过**——后端 concat / one-of / 契约 / 退役 union 链主体真实落地、pytest 零回归；**1 个"落地但对用户不生效"的渲染 bug**（auto-merge 分支未调 `onFinalDone`）+ 2 个收尾项（`_source_layer` 追溯语义、防御性归一）

---

## 一、逐条核验（方案 A 关键点）

### 1. 后端 concat（非 overlay union）—— **agree（落地属实）**

- `api/geo_routes.py:239-243`：`MergeRequest.layers: Optional[list]`（Pydantic 2.13.4 下裸 `list` 合法，实测通过）；
- `api/geo_routes.py:247-263`：`req.layers` 分支——逐项 `resolve_boundary` → CRS 防御（`if not g.crs: set_crs('EPSG:4326')` + `to_crs('EPSG:4326')`）→ `pd.concat(gdfs, ignore_index=True)` → 可选 `by` dissolve；
- DLMC 分类保留 + 无字段后缀：`test_merge_layers_concat` 实测通过（`pytest tests/test_geo_routes.py` 11 passed）；
- `boundary` 单层路径完全保留（`api/geo_routes.py:264-268`），零回归。

### 2. one-of 校验（最容易漏的点）—— **agree（落地属实）**

- `ai_qa/tool_contracts.py:509-511`：`validate_tool_call` merge 特判——`boundary` 与 `layers` 都空 → `{ok:False, fixes:['缺必填参数: boundary 或 layers...']}` ✓；
- `frontend/js/ai_qa/stages.js:58`：merge `required_slots: []`（one-of 无法在 required_slots 表达）✓；
- `frontend/js/ai_qa/tools.js:1130`：guard `if (!params.boundary && !params.layers)` ✓；
- LLM 只传 `layers` → 前端校验过 → `tools.js:1132-1134` 走 layers 分支（`(params.layers||[]).map(ref)`）→ 后端 concat ✓；空 merge → 400（`test_merge_requires_boundary_or_layers` 实测通过）✓。

### 3. 契约 when 两模式 + alias—— **agree（落地属实）**

- `ai_qa/tool_contracts.py:206-219`：`when` 明写两模式（多图层 concat vs 单层 dissolve）+ "`overlay(how="union")` 是空间并集·非图层拼接·同名字段会后缀冲突·**勿用 overlay 代替 merge**" ✓；
- `layers` 参数 alias 收 `layer_list` + `layers_list`（LLM 已猜过的形态）✓；
- `params_str`/`failure_modes`/`planning_common` 同步更新 ✓。

### 4. 退役 union 链 —— **partial（主体 agree + 1 个渲染 bug + 1 个覆盖缺口）**

**退役主体属实**：
- recover 模式 A/C 的 merge 意图改调 `template:'merge' + params.layers`（`harness.js:1234-1241`、`1304-1311`），G1/G2 union 链代码已删 ✓；
- `buildLanduseCompletion` union 分支返回 `mergeLayers`（`harness.js:1348-1352`）→ `_autoExpandOverlays` 调 `TOOLS.merge(layers)`（`harness.js:1364-1372`）✓；
- overlay union **空间并集能力保留**：`api/geo_routes.py:460` `gpd.overlay` 未动 ✓；
- `_hitInline/_hitRecover/_hitAutoExpand` 遥测变量均有定义（`harness.js:15-17`），auto-merge 日志无 ReferenceError ✓。

**BUG（落地但对用户不生效）**：`harness.js:1364-1372` auto-merge 分支**未调用 `hooks.onFinalDone(_obs)`**，直接 `return {final:_obs,...}`。而 panel 唯一渲染路径是 `onFinalDone`（`panel.js:1430-1443`：`shell.answerEl.innerHTML = renderAnswer(text,...)`），`orchestrate` 返回值只用于 exit/newLayerCount/defense（`panel.js:1545-1550`），**不渲染 `_result.final`**。后果：用户问"合并 X+Y+Z 用地"且命中此分支时——答案区不显示、`_curTrace.final` 不设、history 不持久化（`panel.js:1566` 依赖 final）。另 `harness.js:1367` `_diag` 为死变量。

**覆盖缺口（非本 commit 阻塞）**：inline 扩展路径（a5eb3e1）无 merge 分支——"剪裁出 X 区 3 类用地 **并合并**"复合问句 inline 只做 intersection，最终 merge 不执行。已记录，待族 A 多步形态扩展。

### 5. `_source_layer` 标记 —— **partial（存在但追溯语义弱）**

- 实现存在：`api/geo_routes.py:255` `g['_source_layer'] = str(i)` ✓；
- 但值为 **layers 数组序号**（0/1/2），非图层 id/name——换顺序即变、无法回指具体图层，"追溯来源"只达成一半。建议改为携带原始引用（`str(i)+':'+层名/id` 或 layers 传入值）。

### 6. overlay 字段爆炸负向测试 —— **agree（落地属实）**

- `test_overlay_union_field_explosion_negative`（`tests/test_geo_routes.py`）：断言 overlay union 有后缀列（≥4 列）+ concat 不膨胀 + 保留要素——锁定"merge 用 concat 不用 overlay"决策 ✓ 实测通过。

---

## 二、验收标准核查

### 红线

| 红线 | 结果 | 证据 |
|---|---|---|
| diagnose prompt（build_diagnose_prompt） | [OK] 未触碰 | 9f84eac+fa429f9 未改 `ai_qa/prompts.py` |
| 决策追踪编号 | [OK] 未触碰 | 未改 `core/tracker.py` |
| 四态出口 | [WARN] 未被修改但新增路径需复核 | auto-merge 是新增 result 路径（`harness.js:1372` exit:'result'）；失败时 newLayerCount=0 仍返回 result，无 N/M/零图层出口——随 #1 修复一并复核 |

### 回归

- `tests/test_geo_routes.py`：**11 passed**（含 3 个新 merge 测试）✓ 与声称一致；
- 全量：本环境 `201 passed / 19 failed / 5 skipped / 3 errors`——19 failed 为沙箱隔离问题（单跑全过）、3 errors 为沙箱权限（`tmp_path`），与基线一致；**无新增回归**。健康环境口径 223 passed = 201 + 19 + 3，与声称吻合 ✓；
- `boundary` 单层 dissolve 路径：代码未改分支（`geo_routes.py:264-268`）+ 既有 `test_merge_dissolves_all` 通过 ✓。

### 诚实性

- commit message 与代码一一对应（backend/contract/one-of/stages/tools/toolbox/recover/autoExpand/tests 全部找到落点）✓；
- **一处"落地但对用户不生效"**：auto-merge 分支不渲染（见 4）——这是本次唯一需要修的实质问题；
- fa429f9 明示"待用户自测"——未虚报浏览器验证 ✓。

### 边界

- Pydantic 2.13.4 `Optional[list]`：合法（实测 11 passed 证明 schema 工作）✓；
- **防御性缺口**：`layers` 若被 LLM 传成字符串（strict 不强制）→ Pydantic 422。建议后端 `if isinstance(req.layers, str): req.layers=[req.layers]`；
- 空数组 `layers:[]` → 走 boundary 分支 → 400（文案"需 boundary 或 layers"），可接受；
- concat 字段不一致 NaN 填充：可接受（裁剪产物同源同字段）；`_source_layer` 序号列随输出进入前端图层 properties，非 PII，不撞脱敏红线。

---

## 三、验收结论：**有条件通过**

方案 A 主体真实落地：后端 concat（保留 DLMC、无后缀、CRS 防御）、one-of 校验闭环（LLM 只传 layers 不再被拒、空 merge 400）、契约两模式 + `layer_list` alias、G1/G2 union 链退役且 overlay 空间并集能力保留、负向测试锁定决策、pytest 零回归。满足以下条件后转"通过"：

1. **修 auto-merge 渲染 bug**：`harness.js:1364-1372` 补 `if (hooks.onFinalDone) hooks.onFinalDone(_obs)`（建议过 `applyQualityDefense` 或至少 R2 补 `{{show:}}` 按钮），删 `_diag` 死变量；失败时按诚实出口处理（newLayerCount=0 → 明确"未生成"而非 result）；
2. **`_source_layer` 追溯语义**：序号改为携带层名/id（否则"追溯"名不副实）；
3. **防御性归一**（可选）：后端 `layers` 字符串→数组，防 LLM 单字符串 422；
4. **用户自测**：合并用例跑通后更新 buglog/回归清单。

---

*本报告为第三方独立验收；pytest 实测通过，浏览器渲染 bug 经代码路径追踪确认（`onFinalDone` 为唯一渲染入口）。*
