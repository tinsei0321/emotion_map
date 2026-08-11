# CB-22d · 综合 plan 详细评估 — 回应（Codex-GPT5 · 2026-08-10）

> **评估方**：Codex 组（第三方评估·GPT-5）| **日期**：2026-08-10 | **性质**：CB 讨论轮·综合 plan 可行性详细评估
> **依据**：综合 plan 反评价文档 + 讨论发起 + 两组上轮回应 + 代码逐点复算（panel/harness/stages/tools/tool_contracts/paradigm/prompts/shared/map/geocode）+ FC 工具清单实测 + preset/附件5 盘点。未做任何 git 操作。

---

## 〇、一句话结论

**方案骨架成立、方向正确（B 工具为本 + 归 gis_operation 不新增 intent + 三级回退 + P1 数据增强），判定为「需修正后可行」——但有 4 个必修接线点：① P0-2 路由条件不覆盖主复现句（且 quick-rag 轮 priorTurn.intent 为空）② `_dataGate` 的「点位/地块」词会误拦变体句 ③ `runTemplatePath` 零图层分支是 ask_user 而非诚实文字（与 P0-1「全未命中→诚实文字」直接冲突）④ 面化回退不能复用 `FIXED_ADMIN_DISTRICTS` 白名单（葛洲坝会被拒）。另有 5 项强化建议。**

---

## 一、逐焦点详细评估

### 焦点 A：方案可行性（P0-1 工具层）— **partial（骨架可行·漏 4 个接线点）**

**归 gis_operation + 新技能·不新增 intent——技术完整可行**，实测确认关键前提：

| 接线点 | 证据 | 结论 |
|---|---|---|
| FC 工具暴露 | `contracts_to_tools_schema()` 实测 **14 工具**（density/rank/buffer/clip/overlay/zonal_stats/compare_regions/extract_feature/area_stats/merge/nearest/lookup_place/hotspot/filter_attr）·run_python 不在列 | ✅ 新增契约后 FC 自动 14→15·glm 补充成立 |
| C2 天然豁免 | `stages.js:362` `_NEEDS_POINT` 不含新工具名 | ✅ 无 request_upload |
| SKILL_DEFS/契约/镜像 | `stages.js:45` + `tool_contracts.py:20` + `paradigm.py:367` + `validate_skill_params.py` 四镜像·plan P0-3 已覆盖 | ✅ |
| 落图基建 | `toolbox/shared.js` addToolboxLayer + `map.js:516/635` point circle 渲染 | ✅ 需显式 circle paint（plan 已采纳挑战 2） |
| search_place 路由 | `api/routes.py:440` `GET /place/search` + `core/geocode.py:188` | ✅ 复用成立 |

**漏掉的 4 个接线点（必修）**：

1. **`runTemplatePath` 零图层 → ask_user 陷阱（最重要）**：`harness.js` runTemplatePath 尾部——`failed = /\[ERR\]|失败|错误/`；`if (failed || (newLayerCount === 0 && !hasRows)) { if (!failed || recoverable) { → ask_user } else { → gap } }`。新工具「全未命中」返回诚实 observation（不含 [ERR]/失败/错误）→ `failed=false`、`newLayerCount=0`、`hasRows=false`（新工具不在 `_ANALYTICAL_TOOLS`）→ **必然进 ask_user 分支**，问「该范围未聚合到足够情绪点数据」这类无关问题——**P0-1「全未命中→零图层+诚实文字（不 request_upload）」在现有编排器下不成立**。修法：runTemplatePath 对 `generate_point_layer` 特判——`data.layerId===null && Array.isArray(data.unmatched)` → 跳过 ask_user，带 toolHistory 走 finalStep 诚实文字出口（exit='result'/answered·零图层）。此改动在 harness 编排器层（非 diagnose prompt·红线安全）。
2. **`_dataGate` 词误拦**：`harness.js:1572-1573` `_dataGate` = `/用地|地块|土地/` + `/情绪点|点位/`。用户变体句「把这些项目的**点位**标到地图」→ 命中点位正则 + 无点层 → **前置 request_upload，新工具根本没机会执行**；「**地块**」变体同理。修法：`_dataGate` 加豁免——`priorTurn.intent==='knowledge_qa' && /标记|标到地图/` 时跳过数据门（或窄化正则：点位须含情绪/极性语义）。plan 未提此点。
3. **面化回退不能复用 `deriveAvailable` 白名单**：`tools.js:600` 区域 `FIXED_ADMIN_DISTRICTS` 白名单只认 西陵/伍家岗/猇亭/点军——**葛洲坝不在白名单**，复用该匹配会被拒。tier-2 须在工具内自建 name→面 containment 匹配（扫已加载 preset 要素 name/name_field：行政区 MC、社区、大南门·二马路滨江片区 preset `name`），匹配不到再退行政区面+名称标注。
4. **names 缺失的 ask 文案**：`runTemplatePath` 缺必填槽走 `_missingSlotAsk` → `_SLOT_HINT` 无 `names` 条目 → 泛问「要做 generate_point_layer 分析，还缺 names」。须补 `_SLOT_HINT.names`（「请提供要标到地图的项目/地点名，或让我从上一轮回答中提取」）。

**三级面化回退（点→面→文字）符合演示逻辑链**：文字知识（认知）→ 点位/面图层（图面张力）→ `{{show:图层}}` + 交互（引导点击）→ 定位关注区 ✓。**面化数据缺口不阻塞 Phase 1**：街办/更新单元 geojson 缺失只影响 tier-2 精度（葛洲坝退西陵区面+名称标注），tier-3 文字兜底完整——但 tier-2 名称标注本身就是「大致区域」承诺的一部分，验收须允许「行政区级面+标注」为合格（勿按街办级标准验收）。

### 焦点 B：方案有效性（P0-2 路由 + P0-4 验收）— **partial（主场景覆盖不足 + 验收有漏）**

**P0-2 条件 `ctx.resume && priorTurn.intent==='knowledge_qa' && 标记词` 的实况**：

- 主复现句「能在地图上标记出这些项目的位置吗？」`ctx.resume=false`（无续作词·已复算）→ **条件不触发**，plan 自己也承认「本句天然落 diagnose 由 LLM 判」。可靠性风险：句中「这些项目」命中 `RAG_KNOWLEDGE_RE` 知识词 → **diagnose LLM 可能判回 knowledge_qa（纯文字出口·bug 原样复现）**——新技能救不了 intent 误判。
- `priorTurn.intent` 可信度漏洞：`_curTrace.diagnose` **仅由 `onDiagnose` hook 赋值**（`panel.js:1455`）。diagnose 路径的知识问答 ✓（`hooks.onDiagnose` 先于 knowledge_qa 分支调用）；但 **quick-rag 路径（如「宜昌有哪些更新项目」）不调 diagnose → `_curTrace.diagnose=null` → `priorTurn.intent=''`** → P0-2 条件死代码。修法：`_assembleKnowledgeQA` 或 panel 侧补独立于 diagnose 的知识问答标记（如 `_curTrace.rag=true`），路由条件改读该标记。
- **必修建议**：路由条件扩为「priorTurn/turnHistory 含知识问答 && /标记|标到地图|在地图上|点位|位置/」**无条件注入上下文提示**（不翻转 resume·不改 diagnose 文本），把主复现句从「LLM 自由选型」变成「编排器确定性引导 + LLM 只做 names 提取」——更贴 Copilot 内核（Smart 两端·Dumb 中间·编排器确定性）。

**验收标准覆盖评估**：工具三态 stub / 路由负例 / 静态断言 / B3 / 黄金集 / eval 复采 / 用户验收——主体覆盖好，但漏 4 个场景：

1. **零图层诚实出口的确定性用例**（会撞 ask_user 陷阱·见焦点 A-1）——必须加「全未命中 → 断言 finalStep 诚实文字而非 ask_user/gap」。
2. **`_dataGate` 变体负例**：「标记…点位/地块」不得 request_upload。
3. **knowledge_qa 误判回归样本**：diagnose eval 加「标记句」样本，断言 intent 非 knowledge_qa（否则纯文字 bug 复现）。
4. **面化回退 stub 用例**：search_place 未命中 + preset 命中（大南门/西陵区）→ 断言面要素 + 名称标注；葛洲坝不被白名单拒。

### 焦点 C：承重红线（P0-3 契约豁免）— **agree 骨架 + 条件性挑战**

- **3 条件充分**：与 2026-08-09 knowledge_qa 先例一致（增量不改不删 / eval 复采含 gate 0.6 / 静态断言守现有文本 + KNOWLEDGE §1 登记）。补充：豁免登记应附「**3 处 prompt 文本变更清单**」（TEMPLATE_REGISTRY 派生目录 / `prompts.py` 选择要点行 / `paradigm.py` DIAGNOSE_CARD_FIELDS）便于审计与回滚对照。
- **「选择要点·铁律」追加影响**：追加不改删 → 现有 10 个 gis 技能触发词不变，现有选型不回归 ✓；风险在**新技能与旧技能边界**——LLM 可能把「标记」问仍选 density/clip（旧行为）。缓解：`when`/`voice` 写清「**仅当问句要求把名称/项目/地点标到地图时选此技能**；其余 GIS 操作仍选原技能」。
- **不新增 intent 是否真规避注意力稀释——partial**：intent 枚举 4 值、PARADIGM_MAP、`validate_paradigm_map._REQUIRED_KEYS`、静态断言确实零改动 ✓；但**风险转移而非消除**：① gis_operation 内可选技能 10→11（选型表变大）② 更关键——标记句含知识词可能判 knowledge_qa（4 值内部误判·新技能救不了）。**glm 独立新意图在意图判定可靠性上确实更强**（显式判据「上轮 knowledge_qa + 标记/地图 → layer_from_knowledge」上移边界）；**但更优解不是回到第 5 值，而是「确定性编排器规则」**：priorTurn=知识问答 + 标记词 → harness 注入提示/强制路由（焦点 B 建议），把主场景的 LLM 方差压到 names 提取单点。**claude组 裁决方向正确（改动面最小·贴架构），须补确定性路由层才能兑现「规避」收益**。

### 焦点 D：用户核心诉求达成度 — **agree 结构成立 + 2 处修正**

- **三级回退满足「模糊给区域而非拒答」** ✓：点→面/标注→文字，tier-3 是「基于知识库信息给出已覆盖内容的回答 + 坐标缺口诚实声明」，与 request_upload（把数据缺口当出口·拒答）有本质区别。四态语义：≥1 命中 = success/result；部分命中 = 诚实 partial（命中 n/N + 未命中列表）；全未命中 = answered（知识已答·坐标未收录声明）——**均不 request_upload** ✓。
- **修正 1（关键）**：全未命中要真正落到「诚实文字」必须绕开 `runTemplatePath` ask_user（焦点 A-1），否则用户看到「未聚合到情绪点数据」式无关追问——四态被破坏。
- **修正 2**：tier-2 面化产物图层名须防与用户已有层冲突（`addToolboxLayer` 按 name/srcId 去重会替换同层）——建议命名「项目点位（西陵区·葛洲坝片区）」式带标注名，且 `keep:true`（用户要在地图上看到的结论层·守图层生命周期显式意图优先）。
- 预期体验与演示逻辑链一致 ✓：文字答案 → 点位/面图层（张力）→ `{{show:图层}}` 引导点击 → 定位关注区。finalStep 在 gis_operation 路径自动支持 `{{show}}`（FINAL_TEMPLATE 图层主出口）✓。

### 焦点 E：数据增强（P1）— **agree 值得做·叠加合理**

- **可行性实测**：`附件5-城市更新项目库.docx` 存在于家环境 OneDrive 路径（34,987 B）✓。抽取（项目名/地址/片区）→ geocode（AMAP_KEY 已配·status=1 有效）→ **repo 内 L1.5 数据源**（守 RAG 纪律：原文不进 repo·只存提炼数据）→ generate_point_layer 解析顺序「项目源 → 通用 POI」✓ 合理。
- **成本/收益**：中成本（docx 解析 + 地址清洗 + 批量 geocode + 去重/口径标注）·高收益（项目级精确点位·演示逻辑链从「片区级」升「项目级」·命中率可测仿黄金集）。
- **风险提醒（CB-22 教训机器化）**：项目库**版本口径严格标注**（55 项目 vs 43 完整社区混算教训）；未抽到地址的项目仍走 tier-2/3 回退；抽取产物术语/分类禁硬造（来源可溯）。

### 焦点 F：两组补充与异议 — **异议 4 条（必修）+ 更好做法 5 项**

**异议（对综合 plan 的 4 处遗漏/不成立）**：

1. **P0-2 主场景覆盖不足**（resume 条件不触发主复现句 + quick-rag 轮 priorTurn.intent 空值）——见焦点 B。
2. **`_dataGate` 误拦「点位/地块」变体**——见焦点 A-2，plan 未提。
3. **零图层诚实出口与 runTemplatePath ask_user 冲突**——见焦点 A-1，plan 的 P0-1 验收在此场景不成立。
4. **面化白名单陷阱**（葛洲坝被 FIXED_ADMIN_DISTRICTS 拒）——见焦点 A-3。

**更好做法（强化）**：

1. 主场景加**确定性 e2e-seam 用例**（injectOnly 同模式）：stub `priorTurn={intent:'knowledge_qa'}` + 标记句 → 断言提示注入/路由/落图/诚实出口·B3 只做真实 LLM 冒烟（消方差 flaky）。
2. names 并发/上限具体化：**上限 50 名 · 并发 ≤10 · 单请求 5s 超时 · 总预算兜底**（防 55 名顺序挂死·plan 只写「Promise.all + 限流」未给参数）。
3. 匹配结果属性携带**来源与匹配类型**：`{name, source: local|amap|preset, match_type: point|area|none}`——finalStep 据此可读标注（溯源铁律·防 LLM 自创地址）。
4. 黄金集加「知识→图层」意图类 1-2 条（glm 建议已采纳·落地为 B3/e2e-seam 断言清单而非 RAG 黄金集——RAG 黄金集是检索级，意图级应独立成列）。
5. 实施顺序微调：**先 harness 三处接线（路由提示 + _dataGate 豁免 + runTemplatePath 特判）→ 再工具/契约/镜像 → 后豁免登记与测试**——接线点先行可避免工具上线即踩 ask_user。

---

## 二、可行性判定

**判定：需修正后可行（非「直接可行」）**

- 骨架成立度约 **80%**：B 工具 + 归 gis_operation + 三级回退 + P1 增强的方向、契约/镜像/豁免流程、验收主体均正确，与架构（Smart/Dumb/编排器确定性）和红线（四态/D019/diagnose 增量豁免/追踪连续）兼容。
- **4 处必修**（均为 harness/编排器层·非 prompt 层·红线安全）：① P0-2 条件扩展 + priorTurn 知识问答标记 ② `_dataGate` 豁免 ③ `runTemplatePath` 零图层特判 ④ 面化匹配去白名单化。
- **不阻塞因素**：面化数据缺口（街办/更新单元缺失）不阻塞 Phase 1；P1 可并行筹备但不应阻塞 P0 验收。

---

## 三、补充建议（按实施顺序）

1. **P0-0（前置接线·半天级）**：harness 三处——`_dataGate` 加「priorTurn=知识问答 + 标记词」豁免；`runTemplatePath` 对 generate_point_layer 加零图层诚实出口特判（不进 ask_user）；`_assembleKnowledgeQA`/panel 补知识问答轮标记（`_curTrace.rag=true`·独立于 diagnose）。
2. **P0-1（工具层）**：按 plan 实现 + 焦点 A 修正（点样式显式 circle、并发/上限/超时参数、来源与匹配类型属性、面化自建 containment 匹配、`_SLOT_HINT.names`）。
3. **P0-2（路由）**：条件改为「priorTurn/turnHistory 含知识问答 && /标记|标到地图|在地图上|点位|位置/」**无条件注入提示**（不翻转 resume）；主复现句 + 「把刚才…标到地图」双场景都覆盖。
4. **P0-3（契约/镜像/豁免）**：按 plan + 豁免登记附 3 处变更清单。
5. **P0-4（测试）**：焦点 B 补 4 个场景（零图层诚实出口 / _dataGate 变体负例 / knowledge_qa 误判样本 / 面化回退 stub）+ 确定性主场景 e2e-seam + B3 冒烟 + 黄金集回归 + 用户验收（验收按「行政区级面+标注」为 tier-2 合格口径）。
6. **P1**：附件5 抽取（版本口径标注·未抽地址走回退）→ 项目点位源 → 解析顺序升级。

---

*Codex 组 · CB-22d 综合 plan 详细评估 · 2026-08-10*
*评估方只读本地不 git · 评估落 discuss/ · claude组 收到后 /cb 收敛 → 实施*
