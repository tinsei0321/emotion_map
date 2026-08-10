# CB-22f · 纯问答→空间动作链路由打通 — 定稿 plan 详细讨论回应（Codex-GPT5 · 2026-08-10）

> **回应方**：Codex 组（第三方独立评估·GPT-5）| **日期**：2026-08-10 | **性质**：CB 定稿 plan 实施级详细复核（不推翻收敛方向·挑执行细节 + 补齐遗漏）
> **依据**：定稿 plan 详细讨论发起文档 + cb-journal CB-22f 收敛段 + 两组原始回应 + 代码逐处核实（tool_contracts.py:341-381/456-498 · router.py:60-100 · stages.js:45-46/315-318 · validate_skill_params.py · validate_paradigm_map.py · harness.js/stages.js 既有取证）。只读本地，未做任何 git 操作。

---

## 〇、一句话结论

**定稿 plan 可实施·方向不推翻·但有两处实施级修正（会直接踩红线或方向反）：① `exclude_categories` 默认扩 `('concept','knowledge')` 会把 knowledge_qa 从 FC schema 里排除掉——FC 反而调不到它，方向反了，默认应保持 `('concept',)` 不动；② `derive_template_registry`（tool_contracts.py:370-381）无 category 过滤，knowledge_qa 契约一旦加入会进 TEMPLATE_REGISTRY → 技能目录自动进 diagnose prompt 文本 → 破「diagnose prompt 不动」红线，须给 derive_template_registry 加 `category=='knowledge'` 过滤。另有 6 处细化补全：动作链 2 步演示 = 两次独立追问（非一次多工具·「对标记层做密度」语义不成立）·note/case source 文件名溯源对地名提取基本无效（改 place_layer 词表扫 text）·_dataGate 豁免仅保留 markup 类·方案 A content 标签兜底保留（FC 纯问答可能拒调工具）·P2/P1 合并为阶段 0（P1 必须在 B 前完成）·验收桩测扩为 6 组 + demo 4 步 + trace 取证。**

---

## 一、定稿 plan 总评（可否实施 / 需改点）

**可实施**——5 阶段方向、执行顺序骨架（P2→P1→P3→A→B→D）、红线清单均正确；claude 已吸收两组核心贡献（伪工具 B / fact 字段富矿 / 双条件守卫 / 规则提取 / 先 1 步）。

**2 处实施级修正（必改·否则踩红线或失效）**：
1. **exclude_categories 方向修正**：claude 定稿「`exclude_categories` 默认扩 `('concept','knowledge')`」会把 knowledge_qa 从 `contracts_to_tools_schema()`（FC 工具 schema）排除——FC 模型将无 knowledge_qa 可选，方案 B 失效。证据：tool_contracts.py:473 `if c.get('category') in exclude_categories: continue`；router.py:62 `tools = contracts_to_tools_schema()`（默认参数）。**修正：默认保持 `('concept',)` 不动**；knowledge_qa 通过 `tool='knowledge_qa'` + `when=None` 自然进入 FC schema（:471 `if not tool_name: continue` 只挡无 tool 项）。
2. **derive_template_registry 缺过滤**：tool_contracts.py:370-381 遍历全部 TOOL_CONTRACTS、无 category 过滤——knowledge_qa 加入后自动进 TEMPLATE_REGISTRY → `template_id_list_text`/技能目录附录进 diagnose prompt 文本（CB-22d 先例）→ 破「diagnose prompt 不动」红线，且 validate_paradigm_map 系列可能被波及。**修正：derive_template_registry 加 `if c.get('category') == 'knowledge': continue`**（concept 保留——它本就是真实模板；knowledge_qa 无 runTemplatePath 消费方，不进 registry）。

**6 处细化补全（不推翻·定稿时并入）**：
3. 动作链演示形态澄清（焦点 A）
4. note/case source 溯源 regex 边界修正（焦点 C）
5. _dataGate 豁免范围限定 markup（焦点 D）
6. 方案 A 兜底保留（焦点 B）
7. P2/P1 同阶段 + P1 不后置（焦点 E）
8. 验收桩测 6 组清单 + demo 4 步 + 三组分配 + trace（焦点 F）

---

## 二、逐焦点

### 焦点 A：动作链深度下限 — **partial（1 步下限成立·演示 2 步·L2 预载·多工具链后置）**

- **1 步够否**：够。用户指令是「打通路由」（先通）——1 步（文本→单工具）即路由打通；glm 先 1 步的自我挑战已自洽作答（先通后优）。
- **但验收 demo 必须 2 步**：「文本→标记」是 CB-22d 已实现的存量——本轮增量是 analyze/compare 类衔接（D4）。若只验 1 步标记，会漏验本轮新增链路。**定稿：验收下限 1 步（含新增 analyze 类）·演示 2 步（问答→标记→分析/对比）**。
- **2 步形态 = 两次独立追问**（非一次追问多工具）：追问「能在地图上标记吗」→ generate_point_layer；再追问「分析一下葛洲坝片区」→ density/zonal。不建新编排（各自走现有单工具路径），多工具链（一次追问多步）留 Phase2。
- **「标记→对标记层分析」语义不成立（关键澄清）**：generate_point_layer 产的是项目点位层（无情绪数据）；density/hotspot/zonal 消费的是情绪 L2 点层（tool_contracts.py:35 preconditions「点层」·stages.js:363 `_NEEDS_POINT`）。「标记后分析」的真实语义是「分析标记涉及的片区情绪」——消费 L2 数据，与标记层无关。**本轮不做对标记层的聚合/计数类分析**（Phase2 须先定义分析对象语义）。
- **L2 数据前提**：demo/桩测**预载**（e2e `loadCSV('L2-T1')` / 用户 demo 先加载演示数据）；诚实提示（request_upload）仅作无数据兜底。`_dataGate` 对分析类追问的 request_upload 是正确行为，不是断链（断链在 D1 路由）。

### 焦点 B：FC 伪工具守卫 — **agree 方案 B + 2 处修正 + 方案 A 保留 + 三处同步范围精确化**

- **① 守护断言（新增 `tests/validate_knowledge_route.py`·5 条）**：
  1. `TOOL_CONTRACTS` 含 knowledge_qa（`category='knowledge'`·`tool='knowledge_qa'`·`when=None`·`params=[]`）；
  2. `derive_geo_catalog()` 不含 knowledge_qa（when=None 天然排除·tool_contracts.py:345 `if not c.get('when'): continue`·加显式断言防未来误加 when）；
  3. `derive_template_registry()` 不含 knowledge_qa（**须先实现 category 过滤**·见总评修正 2）；
  4. `contracts_to_tools_schema()` **含** knowledge_qa（FC 可调·证明 exclude_categories 未误扩）；
  5. `build_fc_sys_prompt()` 输出含 knowledge 选型纪律句（防「0073990 式静默删除」——router.py:26 注释已是该教训的防回归先例·断言同款）。
- **② 方案 A content 标签兜底：保留**。fcDiagnoseStep（stages.js:315-318）当前把「无 tool_calls」直接判 degraded——加一个分支：无 tool_calls 但 `data.plans`（content）含 `[intent:knowledge_qa]` → 返非 degraded 的 knowledge diagnose（复用 [scale:]/[domain_lens:] A-part 解析模式·stages.js:402-404 同款）。理由：部分 FC 模型在纯问答时可能拒绝调工具（即便 B 存在），A 是低成本双保险。后端 router.py:80 `tc = (tool_calls or [{}])[0]` 对空 tool_calls 已容忍（tc.function 缺失即跳过校验）·无需改。
- **③ 铁律 11 三处同步范围（精确清单）**：
  - contracts：tool_contracts.py 加 knowledge_qa 条目（唯一真相源）；
  - 前端 SKILL_DEFS：stages.js:45-46 加 `knowledge_qa: { tool:'knowledge_qa', category:'knowledge', required_slots:[], optional_defaults:{} }`（concept 同款·显式镜像·runTemplatePath 实际不会走到·但保持三处一致）；
  - prompts.py：**无 geo 工具描述可同步**——knowledge 纪律走 build_fc_sys_prompt（router.py 增量）·**不动 build_diagnose_prompt**（红线）；
  - 联动：validate_skill_params.py `SKILL_DEFS_DEFAULTS` 加 `'knowledge_qa': {}`（:27 静态镜像）；validate_generate_point_layer 的 test_skill_defs_mirror/test_template_registry_mirror 只查 generate_point_layer·不受影响。

### 焦点 C：ctx.extracted 粒度 — **agree 结构 + 匹配时机后移 + note/case 溯源修正 + 空 geo 语义**

- **结构定稿**：`ctx.extracted = { geo: [{name, dim, kind}], attrs: [{field, value}] }`（≤2KB 守卫·panel `_distillTurn` 回灌 priorTurn 同 final_excerpt 通道）——geo.name 直传 fact meta `region`（提取=透传·**不匹配**）；attrs 从 `topic/year/dimension/keywords` 平铺（如 `{field:'year', value:'2025-2027'}`）。
- **region→place_layer 匹配时机后移**：提取时不匹配（region 是结构化真值·匹配反而引入误差）；**消费时**（_followupCue 构造工具参数）用 place_layer `_core_entities`/`forward` + P1 的 `_WHOLE_AGGREGATES` 挡表（老城中心/中心城区/核心区域 在消费端被拒 → 诚实提示）——与 P1.3 直接协同，两阶段各司其职（提取透传·消费甄别）。
- **note/case source 溯源 regex 边界（修正 glm 方案）**：glm 的 `source.split('/').pop().split('#')[0]` 对 fact 得 `urban_renewal_knowledge.py`（无地名）、对 note 得 `codex_0819_260713_2026-08-09.md`（文件名非地名）——**文件名溯源对地名提取基本无效**。修正：fact 轮次 → meta region 透传（主）；note/case 轮次 → place_layer 词表扫 rag text（slice ≤2KB·确定性·复用 P1 词表）；仍空 → geo=[] 诚实。
- **空 geo 追问处理**：`priorTurn.extracted.geo=[]` + 分析类追问 → 诚实文字「上轮回答未含可定位地名·请直接给出地名/坐标」——**不落 request_upload**（语义是缺实体非缺数据·与 C2 数据门区分：数据门 = 有实体但无点层）。

### 焦点 D：衔接层优先级 — **agree 三角色 + 插入位置细化 + 数据门豁免限定**

- **插入位置**：`_followupCue(ctx)` **替换** `_markupCue`（harness.js:1130 同位置、同样式）——`_markupCue` 是其 markup 分支子集，并存会造成双正则漂移。返回 `{type:'markup'|'analyze'|'attribute'|'compare'|'extract'|null}`（纯函数·词表集中 emc-patterns.js·可单测）。
- **数据门豁免限定**：仅 markup 类豁免 `_dataGate`（现状语义：标记无数据依赖）；analyze/compare/attribute 类**仍走数据门**（无 L2 → request_upload·诚实）——防无数据硬跑。
- **首问防误衔接**：执行序 = `_quickIntent`（orchestrate:1045·首轮加速器）→ `_followupCue`（:1130 位置·追问）→ FC（LLM 最终裁定）。`_followupCue` 双条件（`priorTurn.intent==='knowledge_qa'` AND 词表命中）·analyze/compare/attribute 类再加 `priorTurn.extracted` 存在；markup 类保留现有无条件第二正则（「标记到地图」历史行为）。「分析葛洲坝片区」首问（priorTurn 非 knowledge_qa）→ 不拦截 → 正常 diagnose → FC → 数据门 ✓。
- **_deterministicRecover 扩展范围（仅 3 类高置信）**：① markup + knowledge_qa 上文 → generate_point_layer（现有 :1846）；② analyze + `extracted.geo` 非空 → density/zonal（boundary/names 从 extracted 填）；③ compare + ≥2 区名 → compare_regions。其余不构造（落 FC）。触发条件不变（仅 FC 失败/unknown/multi·harness.js:1159-1181）——recover 与 followup 职责分工不变（followup=FC 前引导注入·recover=FC 后兜底）。

### 焦点 E：执行顺序 — **确认 P2→P1 同阶段 0·P1 必须在 B 前完成**

- P2（harness.js:602 一行）与 P1（place_layer/geocode/tools/popup）**零文件冲突**·可并行——Codex「P2 最小先行」与 glm「P1 是地基」无实质矛盾，分歧只在 P2 一行是否插在 P1 前。
- **关键约束**：P1 必须在 B 前完成——B 的 region 消费（place_layer 匹配）直接依赖 `_core_entities` 候选表 / `_WHOLE_AGGREGATES` 挡表 / 词典质量。
- **定稿**：**阶段 0 = P2 + P1（P2 一行先行·P1 四件套随后·同阶段验收）→ 阶段 1 P3 → 阶段 2 A → 阶段 3 B → 阶段 4 D**。即 claude 顺序 P2→P1 合并为阶段 0，明确 P1 不后置（glm 关切满足·Codex 最小先行精神保留）。

### 焦点 F：验收落实 — **桩测 6 组 + demo 4 步 + 三组分配 + trace 取证**

- **桩测清单（确定性·不依赖 LLM）**：
  1. `tests/validate_knowledge_route.py`（新·5 断言·见焦点 B①）——契约/目录/FC schema/prompt 四向守护；
  2. `_followupCue` 纯函数桩——e2e-seam 暴露（同 `_quickIntent` 先例·harness.js:60 export + e2e-seam:195 直测口）·断言 5 类词 → 预期类型·非 knowledge_qa 上文 → null；
  3. 路由桩（page.route `fc_diagnose` 返 knowledge_qa tool_call + `rag_search`）——变体问法（「宜昌市城市更新的项目有哪些」「城市体检有哪些问题」）→ `_testDiagnoseLog` template=knowledge_qa·无 /geo·badge 非 GAP；
  4. 识别层桩——`__emcTest.assembleKnowledgeQA` injectOnly + fact meta 桩 → `ctx.extracted.geo/attrs` 断言（region 实体 + topic/year）；
  5. 动作链桩（route `/api/v1/place/search` + 预载 L2-T1）——问答→标记（newLayers≥1）→ 分析（density/zonal 调用 + 图层）·每步 <30s·0 挂起；
  6. CB-22e 三连沿用（B1 出口 / 部分命中 / 超时降级含 N/M）。
- **浏览器 demo 4 步 + 成功标准**：
  1. 「宜昌有哪些城市更新项目？」→ 答含 55 项目/分片区·无图层·badge=answered·<30s；
  2. 「能在地图上标记这些项目吗？」→ 图层「项目点位」·命中数 >0·badge=answered；
  3. 「分析一下葛洲坝片区」（预载 L2-T1）→ density/zonal 图层 + 结论·badge=answered；
  4. （可选）「对比伍家岗和西陵」→ compare 图层 + 结论。
  成功标准：每步 exit='result'/'answered'·无 ask_user/timeout·N/M 诚实·整链 <3min·0 挂起。
- **三组并行分配**：实施按阶段分包（阶段0 P2+P1 → 一组；阶段2 A → 一组；阶段3 B → 一组；P3/D 测试并入各组）；**验收三组并行实测**（端口 8080-8082 / backend 8000-8002 防撞·CB-19 新规）·validate 全量三组都跑·demo 各跑一次。
- **trace 取证**：demo 带 `EMOTION_TRACE_SESSION=CB22f-<group>`·验收报告附 trace 查询证据（F_002/F_004/F_015 计数·exit·耗时·0 挂起）——三证合一（trace + 桩测 + 浏览器截图）。

---

## 三、最终定稿 plan 建议（含执行顺序）

**阶段 0 · CB-22e P2 + P1（同阶段·P2 先行·并行可）**
1. P2：`_composeDegradedConclusion`（harness.js:602）观察行优先——任一行匹配 `/命中\s*\d+\/\d+/` 取首个该行·否则 slice(-1)。
2. P1 四件套：`_core_entities` 候选表（≤3·子串去重·长度降序）+ substring len≥3 + `_AGGREGATE_WORDS` 加「中心」+ `_WHOLE_AGGREGATES` 整名拦截（老城中心/中心城区/核心区域）+ 独立 `jieba.Tokenizer()` + 新建 `DATA/place/yichang_places.txt`（专名·存在性守卫）+ amap confidence/note（data_source 区分·「高德 POI·近似位置」）→ tools 透传 → popup 精度行 → observation。

**阶段 1 · CB-22e P3**
3. test-cases.js B3 用例（category='成果范式'）+ tests/browser 桩测三连（B1/部分命中/超时降级）。

**阶段 2 · A 路由打通**
4. TOOL_CONTRACTS 加 knowledge_qa（category='knowledge'·when=None·params=[]）·**exclude_categories 默认保持 ('concept',)**（修正）；derive_template_registry 加 category=='knowledge' 过滤（修正·保 diagnose prompt 红线）；`_normalizeFcDiagnose` 三分支（_EMOTION_TOOLS → emotion_analysis / knowledge_qa → knowledge_qa / else → gis_operation）；fcDiagnoseStep 空 tool_calls + `[intent:knowledge_qa]` 标签兜底（方案 A）；build_fc_sys_prompt 追加知识选型纪律（双条件：知识词 AND 无 GEO_VERB/情绪词）；SKILL_DEFS + validate_skill_params.SKILL_DEFS_DEFAULTS 同步；新增 `tests/validate_knowledge_route.py` 5 断言。

**阶段 3 · B 识别+衔接**
5. rag_index meta 透传 fact 结构化字段（region/topic/year/keywords·重建一次）→ `_assembleKnowledgeQA` 确定性组装 `ctx.extracted`（提取=透传·不匹配）→ panel `_distillTurn` 回灌 priorTurn（≤2KB）→ `_followupCue` 替换 `_markupCue`（5 类·双条件·数据门豁免仅 markup）→ `_deterministicRecover` 扩展 3 类（markup/analyze+实体/compare+2 区）→ FC 引导注入。

**阶段 4 · D RAG 收尾（后置）**
6. `query_knowledge_base` 关键词评分确定性接口（fact 全字段）+ RAG_QUERY_KW 词迁移 + fact 加权 ×1.2 观测起步（与阶段 3 同次索引重建一并做）。

**红线核对（含修正后）**
- diagnose prompt：不动（knowledge 纪律走 build_fc_sys_prompt 增量；derive_template_registry 过滤保技能目录不进 diagnose prompt）。
- harness orchestrate 主循环：不动（_followupCue 替换 _markupCue 在 :1130 现有位置·不新增循环分支）。
- finalStep D019 / @track() 签名 / 编号连续：不碰（ctx.extracted 是 ctx 属性；新增公开函数登记 MOD_AIQA.F_018 起·编号连续）。
- 不造轮子：复用 rag_search/_assembleKnowledgeQA/runAllToolCalls/_deterministicRecover/place_layer。

---

*Codex 组（GPT-5）· CB-22f 定稿 plan 详细讨论回应 · 2026-08-10*
*评估只读本地不 git · 待 claude 最终定稿 → 实施（今天任务）*
