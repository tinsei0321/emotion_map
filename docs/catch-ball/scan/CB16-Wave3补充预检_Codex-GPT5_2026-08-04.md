# CB-16 Wave 3 补充预检（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `10c4ae3`（本地已同步·按 KNOWLEDGE §7 评估方不 pull/push）
> **范围**：只读评估 · 不改代码 · 不 commit
> **验证手段**：代码逐行核验 + 内联模拟（沙箱 Python 3.13 无 pytest，不装依赖保只读；pytest 全量请 claude组 实施后跑，基线 269 passed）

---

## 结论先行

**草案可行 · 无 P0。** 两子项方向正确：2b 解析方案对路（B 类 7/7 全覆盖）、P2 契约字段全合规（CI 不红）。需改 **3 项 P1 + 4 项 P2**：

- **【P1】2a 现状计数与「生态宜居」边界**：2a 门控是 `'polarity_index' in expr`（`build_outlet_schema.py:244`）——实际处理 **6 项**（A 类 2 + C 类 2 + `生态宜居` + `需求强度`），非草案所述「A 类 2 + C 类 2」。其中 `生态宜居`（`element_top=环境 + polarity_index`）是 B 形态条件等式：2a 现**忽略条件直接取极性**，草案「2a 不动 + 2b 按 industry 门控」会使该条件永远不参与判定。需二选一并明示（留 2a + docstring 注明「条件为提示·不参与判定」／移 2b 做条件评估），勿静默。
- **【P1】B 类「关键词未命中」语义缺口**：草案只定义「命中则值 + 关键词标注」，未定义「条件匹配、value_field 有值但关键词未命中」怎么办。建议**未命中 → 跳过**（同「不适用·不占卡面」语义，防 `停车` 被标到 `养老托育覆盖满意度` 名下）；value_field 缺失 → `暂无数据`。
- **【P1】`8 领域情绪值` 的 `/` 语义**：`_build_card` 对 `domain_top/element_top` 取 `split('/')[0]`（`build_outlet_schema.py:198`）——是**取首字段**（domain_top），非双字段 OR 回退。实测输出 `urban_governance、0.15`（英文枚举·与「8 领域」中文语义有落差）。建议改 `element_top/domain_top + polarity_index`（中文要素优先）或明确接受「对齐 Wave 1 checkup_dimension 模式」。

---

## 一、2b 可感知计算器（B 类条件等式）

**解析方案对路**：`+` 拆分 → 条件（`field=X/Y`）与值（`field（kw1/kw2）`）识别 → `{condition_field, condition_values, value_field, keywords}`。内联 parser 实测 **7/7 全覆盖**（公园绿地/养老托育/15分钟生活圈/小区环境品质/物业管理/老旧街区改造/商圈活力·含 `设施/环境`、`服务/文化` 双值条件）。B 类实为 **7 项**（草案写「~6-7」没问题，正文「6 项」是计数误差）。

**industry 门控正确**：可量化/可评价组另有 6 个条件等式条目（健康舒适/交通便捷/风貌特色/多元包容/15分钟社区生活圈综合评估/生态宜居）按「非可感知」保持跳过 ✓——建议 parser 文档注明「仅 可感知 industry 参与 2b」，防未来复用到全量 METRIC_MAPPINGS 时误算。

**计算语义**：缺失→暂无数据 / 不匹配→跳过 / 匹配→值+命中标注——区分「无数据」与「不适用」·诚实，对路。Top-1 取值继承 2a（`_extract_emc_value` 取首单元·`build_outlet_schema.py:126-152`），一致性 OK，docstring 注明即可。source 统一为 2a 同款：`'{field}（确定性）·命中：{kw}'` / `'缺失·不编造'`（2b 照抄该模式，不动 2a 代码）。

## 二、checkup_satisfaction P2（prose→真实字段）

- 字段全部 ∈ `_EMC_FIELDS`：`polarity_index / domain_top / element_top / issue_label / place_name` ✓
- **CI 实测**（模拟 P2 改动后跑 `_extract_contract_fields`）：消费集 = `{domain_top, element_top, issue_label, n_elem_, place_name, point_count, polarity_index}`，**无死字段、无误报**（prose 中文段正则本就不收·`tests/validate_outlet_fields.py:29-41`）✓
- **无跨卡重复**：checkup_satisfaction 与 checkup_dimension 同 domain（urban_governance）→ `resolve_outlet_ids` 同 domain 只出一张（`build_outlet_schema.py:96-115`）✓；卡内「满意度/8领域」两行均含 polarity → 轻微重复，可接受（P2 可选：满意度行换 `n_positive/n_negative` 满意率——范围外，不阻塞）
- 「满意度（4 尺度）」显示原始极性（-1..1），建议 source 注明「情绪代理·非问卷率」（与 can 栏「自动满意率」措辞对齐）

---

## 三、7 问速答

1. **解析对路**：B 类 7/7 覆盖·「不匹配→跳过」语义正确；补「关键词未命中→跳过」（P1）。
2. **计算语义合理**：缺失/不匹配/匹配三态区分诚实；source 统一为 2a 同款格式。
3. **P2 契约对路**：无跨卡重复；`/` 是取首字段非 OR 回退，需修正字段序或明确接受（P1）。
4. **CI 兼容**：P2 改后提取无死字段、无误报（内联模拟实测）。
5. **范围**：两项均为余留必要项（2b=计算器闭环·B 类 7 项当前全静默；P2=满意度卡 2/3 槽恒「暂无数据」·防空卡）。**P2 改动最小可先做，2b 是主体**。关联项：前端 `panel.js renderOutletCard` 未渲染 `perceptible_metrics`（2a 已交付但 UI 不可见·建议 P2 一并或明确后置）；renewal 卡也带体检指标（`_build_card:230` 无条件调用·2b 会放大·可 domain 门控·非阻塞）。
6. **测试基本够**：补 parser 边界（无条件/无关键词/空串/非 element_top 条件）+ 关键词未命中→跳过 + value_field 缺失→暂无数据 + `生态宜居` 2a 不回归 + 满意度 source 断言。
7. **承重零触碰**：不碰 diagnose/harness/ChatRequest·确定性组装不变·2a 循环不动（输出集随 2b 增加是预期）；`_parse_emc_expr` 私有函数无需 track ID（outlet_kb 未分配 MOD·守「勿擅自加 ID」红线）；新增分支→严格 SOP（pytest 全绿 + L0→L1→L2 不退化验证）。

---

## 四、优先级

| 级别 | 项 |
|---:|---|
| **P1** | 生态宜居 2a/2b 边界明示 · B 类关键词未命中→跳过 · `8 领域情绪值` `/` 字段序（domain_top→element_top 优先或明确接受） |
| **P2** | source 标注统一 · 前端渲染 perceptible_metrics（关联项） · renewal 卡体检指标 domain 门控（可选） · 测试补边界 |

---

## 五、判定

- **草案可行**：两子项无 P0 阻塞，方向与落地路径清晰。
- **P1×3**（语义明示与修正）· **P2×4**（一致性/测试/关联项）。
- **独立判断**：结论基于代码逐行核验 + 内联模拟（2a 门控 6 项枚举 / P2 后 CI 提取 / checkup_satisfaction 卡面模拟 / 2b parser 7/7），未参考其他组本轮报告。

---

*登记：docs/catch-ball/scan/（RULES 4.1 命名）。本报告只读评估·未改代码·未 commit。*
