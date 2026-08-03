# CB-16 EMC"出口"深化 · SCAN（Codex 第三方独立评估）

> **评估方**：Codex（GPT-5，第三方独立评估小组）  
> **评估时间**：2026-08-03 | **分支**：`fix/emc-buglog` @ `c7c7f4b`  
> **对象**：[EMC-出口抽象层架构讨论_2026-08-03](../../discuss/EMC-出口抽象层架构讨论_2026-08-03.md)（专业版）+ 通俗版 + `ai_qa/outlet_kb/`（7 契约 + 指标映射 + 5 案例）  
> **方法**：只读核验（outlet_kb 代码 + 聚合产物字段 + 承重红线）+ 独立判断（不引用对方报告结论）  
> **一句话结论**：**出口方向正确、outlet_kb 数据底座扎实；核心缺口不是"字段不存在"而是"装配函数 + 触发 + 渲染"三段未接线**（聚合产物已含 place_name/topic_top 等 7 要素输入——比报告暗示的前置缺口更小）；方案 = 后端确定性组装 + 前端模板渲染 + 条件触发；MVP = S2 单场景打穿；"出口驱动开发"应固化为 CI 守卫（新产物字段必须在出口契约有映射）

---

## 〇、结论先行（通俗 + 专业）

**通俗版**：情绪地图现在是"会分析但不会交作业"——分析完只给图层/卡片，给不了行业要的"表"。出口层 = 一个"填表专员"：把分析结果（图/数/观点）按行业表格格式装好交出去。这个专员**必须用代码算数字**（不能靠 AI 编），**不加新 AI 阶段**（省时间、守红线）。

**专业版**：出口 = 出向链路（分析结果 → 行业格式化产物 → 编制/体检流程），目前为 0；outlet_kb 已定义 7 契约 + 指标映射 + 案例库（数据底座✓），但**缺三件接线**：① `build_outlet_schema` 装配函数（不存在）② 触发判定（哪些问句出卡）③ 前端卡片渲染。三者是 MVP 的全部新增面。

---

## 一、报告核验（事实层）

| 声称 | 核验 | 结果 |
|---|---|:---:|
| outlet_kb：7 契约 + 21 指标映射 + 5 案例 | `ai_qa/outlet_kb/`（urban_renewal/checkup CONTRACTS + METRIC_MAPPINGS + case_library CASES·确定性查询函数齐全） | ✓ |
| `build_outlet_schema` 为提案非实现 | 全仓库 grep 零命中——**不存在** | ✓ |
| 诊断卡 `outlet` 是引导词非契约 | `paradigm.py:462` / `prompts.py:202`——7 值枚举·prompt 引导 | ✓ |
| 聚合产物字段可支撑 7 要素 | **补充核验**：`core/spatial_analysis.py:585-600` 聚合已含 `place_name`（格内代表地名）+ `topic_top`；polarity_index/n_*/domain_top/element_top/issue_label/attribution 全在 | **✓（关键）** |
| 出向链路 = 0 | `DOMAIN_OUTLETS`（`paradigm.py:70-107`）纯启发词·export.py 通用格式 | ✓ |

**独立发现（修正报告口径）**：

1. **"结构化字段池缺失"不是前置缺口**——聚合产物（grid/zonal 的 feature properties）已含 7 要素输入字段（含 place_name·点侧众数·粗略）。真正缺口是**三层接线**：装配（build_outlet_schema）+ 触发（条件判定）+ 渲染（前端卡片）。比报告"出向=0"的缺口定义更聚焦。
2. **定案归属问题**：通俗版"焦点 1-6 定案"标注"Codex + claude组 一致"——**Codex 本轮才首次回应出口议题**，此前未参与该讨论。该表述需修正（不能把未发生的立场记为一致）。本 SCAN 的立场独立给出，与定案部分重合属独立判断趋同，非引用。

---

## 二、结果范式 agent 方案初稿

### A1 架构：后端确定性组装 + 前端模板渲染 + 条件触发（agree 定案方向）

```text
finalStep 完成 → 触发判定（问句含 更新/体检/需求/满意度/时序 等接口词 + intent≠general）
  → build_outlet_schema(diagnose, 产物图层 fc, outlet_kb)
       ├─ resolve_outlet_id(diagnose) → OUTLET_CONTRACTS[oid]
       ├─ 从产物 fc.features 取 Top-N（按 polarity_index 排序）→ 填 7 要素
       └─ 返回结构化 schema（JSON）→ 前端卡片组件渲染
```

- **实现位置**：`ai_qa/outlet_kb/` 内新增 `build_outlet_schema.py`（出向权威源内聚·非 core/ 新目录——outlet_kb 已是出向单一权威源，同处放装配器避免双源漂移）；
- **不新增 LLM 阶段**：agree（撞 D019 final 极瘦红线 + 数字必须代码算）；
- **条件触发**：不是每问出卡（"生成热力图"不出卡·"西陵区更新需求分析"才出卡）——触发判定放 finalStep 之后（不打扰主链路·纯增量）。

### A2 outlet_id 映射：诊断卡 outlet + domain + scale 三联合 → OUTLET_CONTRACTS

- 诊断卡 outlet（生成图层/指标排序/报告结论…）是**出口形态**，OUTLET_CONTRACTS 是**行业接口**——两维度不同，需解析器桥接；
- `resolve_outlet_id(diagnose)`：遍历 OUTLET_CONTRACTS，匹配 `domain ∈ diagnose.domain_lens` + `scale ∈ contract.scales` + 问句关键词（需求/满意度/排序/识别→对应契约）；纯代码确定性，未命中返回 null（不出卡）；
- 注意：一个 diagnose 可命中多契约（如 renewal_demand + checkup_satisfaction）——MVP 取优先级最高一个（问句关键词最强命中），后续支持多卡。

### A3 尺度校验：模板按尺度分派 + **字段白名单**（agree 不加独立校验层）

- 现有 SCALE_PARADIGM + _outletLine + R10/R11 已两层约束；
- 补充"源头防越界"：**macro 模板 schema 不含 place_name/网格 ID 字段**（白名单字段集按尺度裁剪）——组装函数根本不读 micro 字段，混入在源头不可能；
- 比"组装后校验"更早更便宜（agree claude组 定案方向·补充机制）。

### B1 字段一一对应：字段池已存在·缺口 = 装配 + 渲染

- 7 要素输入的字段（polarity_index/n_*/domain_top/element_top/place_name/issue_label/attribution）**全部已在聚合产物 properties**（`core/spatial_analysis.py:244-600`）；
- `build_outlet_schema` 的输入 = **产物图层的 fc.features**——需要在 finalStep 后把"本次分析产物图层"（layerId → getLayer(id).fc）传给装配器（harness 轻量接线，不触碰承重路径）；
- 渲染：前端新增卡片组件（仿 `cpd-guide-card` 模式）——7 要素结构化表格 + 图层引用（{{show:}}）。

### B2 可感知 10 项全量罗列：outlet_kb 补全 + 每项标注"分析工具 + 4×5 落点 + 尺度"

| 10 项 | 4×5 落点（示例） | 分析工具 | 尺度 |
|---|---|---|---|
| 公园绿地可达 | element_top=环境 | grid/zonal | meso |
| 养老托育 | element_top=设施 | grid/zonal | meso |
| 内涝积水 | topic_top=积水 | grid（实时窗） | macro |
| 15 分钟生活圈 | domain=规划 + 设施 | zonal（社区单元） | meso |
| 小区环境 | element_top=环境 | zonal | meso |
| 停车 | element_top=服务/设施 | grid/hotspot | meso |
| 物业 | element_top=服务 | zonal | meso |
| 老旧街区 | issue_label + place_name | grid | meso |
| 活力烟火气 | domain=运营 + 文化 | hotspot | meso |
| 宜居感知 | 综合（跨 domain） | grid（综合极性） | macro |

- outlet_kb 已覆盖公园/养老/内涝等（`urban_checkup_outlets.METRIC_MAPPINGS`）——补全剩余项 + 每项附工具列（与 F 出口驱动联动）；
- 验证原则：每项 emc_field 必须在聚合产物可取值（报告焦点 7 ✓）。

### B3 案例库：演示依据 + 出口卡"对接建议"佐证·诚实区分

- case_library 三段式（survey 真实 / emc_angle 对应 / benchmark 对标）质量高（来源标注 ✓）；
- 用途：① 立项演示场景依据（宜昌望洲岗）② 出口卡"对接建议"要素附案例佐证（"宜昌望洲岗：改造前后情绪对比佐证"）；
- **诚实边界**：emc_angle 是"假设情绪地图做了会怎样"的**对应推演**，非已发生事实——出口卡引用时须区分"行业真实做法（已发生）"与"情绪地图对应（假设）"，防演示越界。

### C 与 CB-15 协同：macro 零依赖 ✓·meso/micro **可先行**（软化定案）

- **macro 零依赖**：agree（面域 + 极性面即可·可立即做）；
- **独立修正**：place_name **已存在于聚合产物**（点侧众数·`spatial_analysis.py:585`）——S2 的"需求位置"要素**现在就能填**（诚实标注"格内代表地名·粗略"）；CB-15 是**精度升级**（POI sjoin 优先 + 置信度），非**解锁前置**；
- 故建议：Wave 1 的 S2 不阻塞等 CB-15——先带"粗略 place_name + 诚实标注"打穿演示，CB-15 完成后换精确源（schema 接口不变·只换字段来源）。

### D MVP：S2 单场景打穿 ✓·最小闭环 = 表是唯一新增件

- **agree 单场景**（S2 更新需求分析·meso 覆盖核心板块）；
- 最小闭环四要素：**图**=极性面（已有）·**数**=polarity_index/占比（已有）·**观点**=4×5 归因（已有）·**表**=需求分析卡（**唯一新增**·build_outlet_schema + 前端渲染）——验证"出口层不推倒已有分析·只加最后一公里"。

### E 承重与风险

- **不触碰 diagnose/harness/ChatRequest**：agree——build_outlet_schema 是 finalStep 后的纯新增层；诊断卡 outlet 字段（承重）不改，OUTLET_CONTRACTS 独立新增；
- **D019 红线**：不新增 LLM 阶段 ✓（后端组装 + 前端渲染）；
- **S2 规则归因诚实标注**：当前归因 = 规则查表（`lookup_attribution`·`spatial_analysis.py:551`）——出口卡"定性归因"要素必须标注"来源=规则归因·置信度低/高"，防演示被误读为 LLM 深度归因。

---

## 三、出口驱动开发逻辑链落地（焦点 F · 核心）

### 机制：出口契约的 field_mapping = 开发决策验收标准

**逻辑链落地为一条纪律 + 一个 CI**：

1. **纪律**：每个 EMC 开发决策（新工具/新图层/图例/文本范式）先问一句——"这服务哪个出口的哪张表？"答不上 = 不立项（或先补出口契约）；
2. **CI 守卫**：新增 `tests/validate_outlet_fields.py`——扫描新增/修改的分析产物字段（聚合函数输出列 + 工具观察字段），校验：每个字段要么在 outlet_kb 某契约 field_mapping 有映射，要么显式标记"未映射（待定）"——防"分析了很多、行业用不上"的无序扩张；
3. **五步反推示例（S2 需求分析卡）**：

```text
出口表（renewal_demand·片区策划需求分析）：问题类型/需求强度/需求位置/需求类型/数据基础
  → ① 分析方法：zonal/grid 聚合 + 4×5 归因（已有）
  → ② 计划：范围筛点 → 聚合 → 归因 → 排序（已有链能力）
  → ③ 执行工具：zonal_stats/grid 服务"需求位置+强度"列·rank 服务"时序"列
  → ④ 图例样式：极性面红绿（消极=需求热点）服务卡的"图"·单元名标注服务"位置"
  → ⑤ 文本范式：卡片的"对接建议"要素按 task_link 渲染（②老旧小区整治…）
```

4. **从"结果对接层"升级为"开发方法论"**：出口契约字段清单成为 EMC 开发路线图的事实来源——CB-15 的 place_name 双源、POI sjoin 因"需求位置"列而立项；grid 图例设计因"图"要素而立项。**这是本讨论最有长期价值的产出**——不只是一层代码，是一套"以行业表为北极星的开发约束"。

---

## 四、优先级与实施序列

| 波次 | 内容 | 依赖 | 交付物 |
|---:|---|---|---|
| **Wave 0** | `resolve_outlet_id` + `build_outlet_schema`（S2 契约装配）+ 条件触发 + 前端卡片渲染 | 无（聚合产物字段已就绪） | 问"西陵区更新需求分析"→ 出需求分析卡（7 要素） |
| **Wave 1** | macro 出口（renewal_object_identify/checkup_dimension）+ 案例佐证 + 诚实标注 | 无 | 更新对象识别卡 + 体检维度卡 |
| **Wave 2** | CB-15 完成后 place_name 换精确源（schema 接口不变） | CB-15 | 需求位置精度升级 |
| **Wave 3** | 可感知 10 项补全 + `validate_outlet_fields.py` CI + 多卡支持 | Wave 0/1 | 出口字段守卫 + 指标全覆盖 |

**MVP 验收**（立项演示最小集）：一条 S2 问句端到端出"需求分析卡"——图（极性面）· 数（polarity_index）· 表（7 要素卡）· 观点（规则归因·标注）四要素齐，演示"情绪地图找市场"成立。

---

## 五、风险与边界

| 风险 | 级别 | 对策 |
|---|:---:|---|
| 出口层过度设计（想填的表太多） | 中 | 先落城市更新/体检两板块（outlet_kb 已限定）·其他领域不立项 |
| 4×5 ↔ 8 领域弱映射（一归因对多指标） | 中 | 显式映射 + 置信度·多映射时选主指标 |
| S2 规则归因被误读为深度分析 | 高 | 出口卡"定性归因"要素显式标注"规则归因·置信度" |
| place_name 粗略（点侧众数） | 中 | 诚实标注"格内代表地名·CB-15 后升级 POI 双源" |
| 报告定案归属表述（Codex 立场被预记） | 低 | 修正通俗版"Codex+claude组 一致"表述·本 SCAN 为 Codex 首轮独立立场 |

---

## 六、给 claude组 的待确认

1. **S2 演示数据**：是否有"带 place_name 的评论点层 + 行政区边界"现成演示集（供 Wave 0 端到端验证）；
2. **条件触发词表**：接口词（更新/体检/需求/满意度/时序/识别）是否由 EMC 侧定（进 emc-patterns）还是进 outlet 契约（出向权威源）；
3. **卡片渲染形态**：前端表格组件样式（仿 cpd-guide-card）是否有既有设计 token 约束。

---

*本报告为 Codex 组独立 SCAN；outlet_kb/聚合产物/承重红线经代码核验（`ai_qa/outlet_kb/*`·`core/spatial_analysis.py:244-600`·`paradigm.py:462`），未引用对方报告结论。*
