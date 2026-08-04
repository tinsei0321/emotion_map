# CB-16 Wave 3 完成 2b+P2 实施后检查（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `401371b`（③z3·先验后推未推）
> **范围**：只读评估 · 不改代码 · 不 commit
> **验证手段**：代码逐行核验 + 内联断言（沙箱无 pytest、:8000 不可达，未装依赖保只读；用同一后端函数直调做等价端点验证；pytest 29/274 以 claude组 环境为准）

---

## 结论先行

**2b + P2 实施通过 · 无 P0/P1 · 可推。** 反评价 P1×3 全采纳且实现正确：生态宜居留 2a 明示、关键词未命中→跳过、element_top 优先；P2 契约字段全合规（CI 不红）；panel 渲染并入。3 项 P2 小修（不阻塞）。

---

## 一、核验结果

**① 2b 可感知计算器 —— 正确**
- `_parse_emc_expr` 全量矩阵（checkup 模块 17 项）：极性 5 / 条件 11 / 不适用 2。多值 `/` 拆列表正确（老旧街区 `['设施','环境']`·商圈 `['服务','文化']`）·关键词 `/` 拆多词正确·含 polarity → 2a ✓
- 2a 极性类 5 项（A2+C2+生态宜居）·生态宜居 docstring 明示「条件为提示不参与判定」✓；`_kw_hit` 抽取等价（内联实测停车泊位命中标注·宜居无标注·无回归）
- 2b 仅可感知 industry 进（7 项）·生态宜居可量化不参与 ✓；缺失→暂无数据 / 不匹配→跳过 / 匹配→取值 / 关键词未命中→跳过 ✓
- source 实测与预期一致：`topic_top（确定性）·条件：element_top=环境·命中：公园` ✓

**② checkup_satisfaction P2 —— 正确**
- 满意度 `polarity_index` ✓ · 8 领域 `element_top/domain_top + polarity_index` 实测 `设施、-0.32`（element_top 中文优先·Codex P1③）✓ · 不满意项不动 ✓
- CI：`_extract_contract_fields` 7 字段 / `_extract_metric_fields` 5 字段 · dead 均空 · 无误报 ✓

**③ panel.js 渲染 —— 不破坏布局**
- metricsBlock 插于 fields 与 task 之间·复用 `.outlet-field/.outlet-muted` 样式·暂无数据灰·source 放 title ✓；`flex column + gap` 布局不受影响 ✓
- **P2**：`.outlet-metrics/.outlet-metrics-title` 未定义 CSS（全仓 rg 无）→ 小节标题无样式（不破版·视觉差）

**④ 测试 +7 —— 覆盖到位**
- 2b 命中/不匹配/缺失/多值条件/关键词未命中/生态宜居 2a + P2 字段非空·与实现语义一一对应 ✓

---

## 二、7 问速答

1. **解析正确**：多值 `/` 拆列表·含 polarity→2a·生态宜居留 2a 合理（docstring + 测试双明示）。
2. **语义正确**：不匹配→跳过 + 关键词未命中→跳过·不占卡面·防跨类误标；不会漏真适用指标（条件+关键词双重约束与指标定义一致）。条件匹配用 substring·受控词表下低风险（P2 可改 `==`）。
3. **P2 对路**：element_top 优先 + `/` 取首 = 中文要素 + 极性·符合「8 领域情绪值」语义（对齐反评价 P1③）。
4. **渲染不破坏布局**：复用既有样式·插在字段后；仅小节标题缺 CSS（P2）。
5. **测试够**：+7 覆盖核心路径；补 value_field 缺失→暂无数据、`_parse_emc_expr` 纯函数单测（P2）。
6. **承重零触碰**：commit 仅 6 文件（build_outlet_schema / urban_checkup_outlets / panel.js / test_outlet_schema + 2 docs）·diagnose/harness/ChatRequest 不动·2a 行为不回归·确定性组装不变。
7. **已知 backlog 确认**：renewal_demand 卡也带 perceptible_metrics（`_build_card:230` 无条件调用·场景 A 实测 5 项）——非本次引入·不阻塞 ✓。

---

## 三、优先级

| 级别 | 项 |
|---:|---|
| **P2-1** | 补 `.outlet-metrics / .outlet-metrics-title` CSS（小节标题视觉） |
| **P2-2** | 2b 条件匹配 substring → 可选 `==`（受控词表·低风险·非必须） |
| **P2-3** | 测试补：value_field 缺失但条件匹配→暂无数据 · `_parse_emc_expr` 纯函数边界单测（空串/无 `+`/keywords 空） |

---

## 四、判定 + 修正声明

- **判定：通过 · 可推**（claude组 push）。无 P0/P1 需修项。
- **预检计数修正**：补充预检时我写「2a 处理 6 项（含 renewal 需求强度）」——实测 `compute_perceptible_metrics` 只 import `urban_checkup_outlets.METRIC_MAPPINGS`，renewal 模块指标不在计算范围，**2a 实为 5 项**（A2 + C2 + 生态宜居）。实现与反评价一致，此修正不影响结论。
- **独立判断**：基于代码逐行核验 + 内联断言，未参考 glm组 本轮报告。

---

## 附录：内联验证证据（等价端点核心逻辑）

| 场景 | 结果 |
|---|---|
| `_parse_emc_expr` 17 项矩阵 | 极性 5 / 条件 11 / 不适用 2 · 多值条件拆列表正确 |
| 2a 极性类（含生态宜居） | 5 项出值 · 生态宜居 `-0.3` 单条（不重复进 2b） |
| 2b 环境 + 公园散步 | `公园绿地步行可达性感知` = 公园散步 · source 含 条件+命中 |
| 2b 设施 + 停车难 | 养老托育 / 公园绿地 等 B 类全部跳过（关键词未命中） |
| 多卡场景 A | `[renewal_demand, checkup_satisfaction]` · 满意度=`-0.32` · 8领域=`设施、-0.32` · 不满意项=`停车难、大南门` |
| CI 提取 | contracts 7 字段 / metrics 5 字段 · dead 均 `[]` |

*登记：docs/catch-ball/scan/（RULES 4.1 命名）。本报告只读评估·未改代码·未 commit。*
