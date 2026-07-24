# EMC × 测试飞轮 系统性改进方案

> 2026-07-24 ｜ 咨询答复 ｜ 依据：四问清单 + 测试报告（tests/reports/ 01~03）+ 代码证据（挂行号）
> 前置文档：[test-flywheel-audit-2026-07-24.md](test-flywheel-audit-2026-07-24.md)（飞轮机制审计）、[cpd-core-plan.md](cpd-core-plan.md)（v1.3 工作流）

---

## 〇、证据基线（先说事实，再给方案）

| # | 事实 | 证据 |
|---|------|------|
| E1 | 工具选择 15 例中 14 例 **90s 超时无回答**（s3=waitAnswer 阶段），仅 1 例通过且 badge=部分完成 | `tests/reports/report-2026-07-23-01-llm.md`；`test-cases.js:29`（s3 定义） |
| E2 | 超时例总耗时 91.3~136.6s：超出 90s 上限的部分 = setup+diagnose+agent 已吃掉 20~45s，**answer 阶段连 90s 都撑不满输出** | report-01 耗时列 |
| E3 | `addLayer` 顺序发号 `L001…`，**零去重**：同名/同文件重复导入 = 直接堆叠 | `state.js:667-707`；`main.js:108-137`（runImport 循环直调 addLayer） |
| E4 | 字段识别已有 DataEye 雏形：规则→LLM 推断 role，但**每层仅 6 字段 × 2 样本 × 24 字符**，且只覆盖**可见层** | `tools.js:466-482`、`519-523` |
| E5 | 图层语义靠**层名正则启发式**（`/行政区|片区|范围…/`），字段极性靠字符串匹配 | `tools.js:486-495`；`main.js:111`（detectColorMode） |
| E6 | 滚动跟随机制存在但**一旦上滑永久停跟**：`_userPinned` 仅靠"回到底部"按钮复位，发送新问题时**不复位** | `panel.js:1535`（置位）、`1547`（仅按钮复位）、`427-429` |
| E7 | 后端已有字段字典基础设施 `core/field_dictionary.py`（MOD_FIELD 已埋点），但前端上传链路**未接入** | AGENTS.md 模块表 |
| E8 | 时间切片体系已存在：`tagAllLayers` 给层打 `datasetId/sliceKey` | `main.js:152` |
| E9 | 词表漂移：diagnose 卡词表缺 compare/filter_attr，决策树却教选——LLM 被教唆选"不存在"的 template | `prompts.py:190` vs `paradigm.py:454/470`（审计报告 H2） |
| E10 | template 信号断链：ChatRequest 无 diagnose 字段，飞轮 tmpl 断言永 false | `schemas.py:11-22`（审计报告 H1） |
| E11 | 分析型工具（zonal/rank/area_stats）返 rows 无 layerId，成功判定已单独处理——"成图"非唯一成功态，但用户核心价值锚点是成图 | `harness.js:375` |

---

## 一、工程摘要格式优化（Q1）

### 1.1 对现行 3 行提案的评估

用户提案：`①工具：触发数/命中数/判断正确数及占比；②图层：计划/实际+摘要；③文本：完成状态`。方向正确（压缩、固定行数、面向对比），但有四个结构缺陷：

1. **粒度混叠**：单条用例的"数"与批次级"占比"混在一行——占比在单例上无意义（1/1 或 0/1），属于批级聚合。
2. **维度缺口**：意图/工具测试的核心被测物是 **template 转译**（E10），3 行里没有它的位置；也没有**耗时/调用数**（E2 证明超时是头号杀手）。
3. **判定混淆**："测试判断正确数"把「被测系统表现」与「断言本身质量」搅在一起——误杀/漏判（断言错）与系统错误必须分列，否则飞轮调 prompt 时不知道在修谁。
4. **机器不可读**：中文标点+自由文本，无法 grep/diff/进 JSON sidecar（审计 H5 的依赖）。

### 1.2 优化方案：EMC-SUM v1（3+1 行 · 键值定序）

**设计原则**：行序固定、键名固定、ASCII 分隔、单值可 grep；单例只记"数"，占比上浮批级头部；同一 schema 双渲染（测试报告 per-case 块 + EMC 产品内回答页脚卡）。

```
EMC-SUM v1 | id=<caseId> | run=<date-NN>
①链路: intent=<期望→实际 ✓|✗> tmpl=<期望→实际> tools=<期望n→实际n [name,…]> tool_hit=<n/n> judge=<✓|✗|误杀|漏判>
②产物: layers=<计划n→实产n> [<layerId>:<tool>:<摘要≤12字>; …] rows=<n> fig=<n> 落图=<ok|partial|none>
③状态: task=<done|partial|fail> exit=<result|gap|partial|ask|drift> t=<总s>(d=<诊断>/a=<agent>/w=<作答>) llm=<n次> tok=<in/out>
```

**+1 批级头部**（报告顶部，占比唯一住所）：

```
## RUN <date-NN> | mode=llm | n=<总数> | pass=<n> <pct> | timeout=<n> | gap=<n> | 误杀=<n> 漏判=<n> | t_p50=<s> t_p95=<s> | llm=<总次> | commit=<sha>
```

**关键改进点**（相对原提案）：

| 原提案 | 优化后 | 理由 |
|--------|--------|------|
| 工具"判断正确数及占比"混在单例 | 单例只记 `tool_hit=n/n`，占比上浮批级 | 粒度归位，单例可 diff |
| 无 template 维度 | ①链路首列 `intent/tmpl 期望→实际` | 对齐意图/工具测试的被测物（E10 修复后此列才有信号） |
| 无耗时/调用 | ③状态 `t=总(d/a/w 三段) llm tok` | E2：超时是头号失败，必须可聚合出 p50/p95 |
| 判定一格 | `judge=✓/✗/误杀/漏判` + 批级误杀/漏判计数 | 断言质量与系统质量分流，飞轮才知道修 prompt 还是修断言 |
| 自由文本 | 全键值 ASCII，`grep '^②产物' \| awk` 可统计 | 进 JSON sidecar（H5），支撑跨 run diff |

**落地约束**：格式版本化（`EMC-SUM v1` 字样进首行），变更升版本号；断言未接通的字段（tmpl 在 H1 修复前）统一填 `?` 而非省略键——**键永远在，值可缺失**，保证列对齐。

---

## 二、文件处理与交互缺陷（Q2）

### 2.1 重复上传堆叠 → 基于文件指纹的去重复用

**现状**：`addLayer` 顺序发号零去重（E3）；`srcName` 已存文件名但未用于判重。

**业界最佳实践**：

| 实践 | 代表 | 要点 |
|------|------|------|
| 内容寻址存储（CAS） | git / DVC / lakeFS | 以内容 hash 为唯一键，同内容天然去重 |
| 采样指纹（大文件免全量 hash） | Kepler.gl dataset id / QGIS source URI | 文件名+大小+头 N KB+元数据合成指纹 |
| 重复检测三态策略 | FME DuplicateFilter / Tableau | 完全相同→复用引用；名同内容异→提示 覆盖/并存(改名 v2)；内容同名异→提示 关联/新建 |

**落地方案（srcId 机制）**：

1. **指纹**：`srcId = sha1(文件名 + 字节数 + 前 8KB + featureCount + bbox)`，import 解析后在 `runImport`（`main.js:91` 循环内）计算，挂 `layer.srcId`。
2. **注册表**：`state.js` 增 `_srcIndex: Map<srcId, layerId[]>`（L2 拆组场景一文件多子层，故值是数组）。
3. **三态策略**：
   - 同 srcId → toast「该数据已加载，已为你选中」+ `selectLayer` 复用，**不入新层**；
   - 同 `srcName` 异 srcId → confirm 弹窗：「覆盖旧版 / 并存为 `名 (2)`」（并存时旧层标 `superseded` 降 opacity）；
   - 异名同内容（同 fc hash 异文件名）→ toast 提示关联，仍新建（尊重用户命名）。
4. **EMC 侧收益**：`_srcIndex` 同时给 grounding 一个稳定引用键（比易变的 `L001` 顺序号更适合 $n 引用与 episodes 复盘）。

### 2.2 字段/属性识别差 → 三层字段理解管线

**现状**：DataEye 雏形已存在但薄（E4）；语义靠层名正则（E5）；后端字段字典闲置（E7）。

**业界最佳实践**：

| 层 | 做法 | 代表 |
|----|------|------|
| 确定性嗅探 | CSV 经纬度列候选自动识别（lon/lng/x/y/经度/纬度…）、dtype 推断 | Kepler.gl / GDAL OGR / pandas |
| 字典匹配 | 字段名→规范角色（range/point/polarity/intensity/time）映射表 | FME SchemaMapper / Tableau Prep role |
| LLM 语义标注兜底 | 字段名+样本值→语义类型分类器（带缓存） | Sherlock/Dojo 语义类型推断；现 DataEye LLM 路 |
| 交互式列映射向导 | 识别置信度低时让用户点选确认，确认结果回写字典 | Kepler.gl / PowerBI 导入向导 |

**落地方案（Layer Manifest · 导入时一次性计算，全链路复用）**：

```
layer.meta.manifest = {
  srcId, kind, featureCount, bbox, crs,
  fields: { <name>: { dtype, role, confidence, samples[3] } },   // role 来自三级管线
  semantics: { isEmotionPoint, polarityCoverage, hasIntensity, timeTag, rangeRole },
  quality: { emptyGeoms, outOfChinaBbox, dupRows },               // 数据预检 → 喂 diagnose data_plan
}
```

- **三级管线**：嗅探（正则/dtype）→ 字典（`core/field_dictionary.py` 提升为前后端单一事实源，前端经 API 取用）→ LLM 兜底（现 getFieldCard LLM 路，结果**按 srcId 缓存**，避免每次问询重算）。
- **消费点**：`buildContext`（`tools.js:515-521`）改为读 manifest（字段数从 6 提升到全量 role 非 `?` 字段，样本 3 个）；diagnose 数据自检三态读 `quality`；SKILL_DEFS 参数校验读 `fields`。
- **低置信交互**：manifest 置信度 < 阈值时在图层右键/设置页显示「字段角色待确认」向导，用户确认即回写字典——这就是用户侧的"模糊识别→标准化转译"闭环。

### 2.3 对话窗口不跳转最新 → 新话轮强制跟随

**根因**（E6）：`_userPinned` 上滑置位后只能靠底部按钮复位，发送新问题时**不复位**——于是只要用户在上一轮长流式中上滑过一次，之后所有新回答都不再下拉到最新。

**修复（两处，共 3 行量级）**：

1. 用户发送新问题（appendMessage user 分支 / send 入口）→ `_userPinned = false; scrollBottom()`：**新话轮永远从头跟到底**（业界标准：ChatGPT/Claude/文心均如此——话轮内上滑停跟，新话轮重置）。
2. 流式期间保留现行"上滑停跟"（`panel.js:1535` nearBottom 判定不动）；回底按钮逻辑不变。

---

## 三、系统性失败剖析与解决路径（Q3）

### 3.0 失败模式总账（三份报告交叉）

| 失败模式 | 占比证据 | 根因层 |
|----------|----------|--------|
| 超时无回答（>90s） | report-01：14/15 工具例 | 串行多 Pro 调用管道（E1/E2） |
| 模板转译错误/信号缺失 | report-02：意图 7 例全 ERR（_fill bug，已修）；E9/E10 | 词表漂移 + 信号断链 |
| 工具未触发 | report-03：TOL-001 未触发 density | 推理链断裂（见 3.3） |
| 误 GAP / 假完成 | 审计报告四痛点#4 | 出口裁定宽松 + ReAct 8 轮打满 |

### 3.1 超时（>90s "卡住"感）→ 预算制 + 模型路由 + 进度透明

**根因链**（E2）：单问 = diagnose(Pro reasoner 流式) + agentStep N 轮(每轮全量上下文) + answer(Pro reasoner 流式) + review(Flash 阻塞) + revise(Pro≤1)。deepseek-reasoner 思考动辄 20-60s，**两个 Pro 调用串行即可吃光 90s**；agent 每轮重发 buildContext（字段样本+registry+wisdom）进一步放大延迟。测试 90s 上限只是产品真实体验的镜像。

**三层解法**：

**A. 预算制（deadline propagation）**：单问总预算默认 75s，分段下发 diag≤15s / agent≤25s / answer≤25s / review+revise≤10s；任一段超预算即降级（跳过 revise、review 异步化），**保证必有回答**。每段剩余预算随请求传给 LLM 网关，超时即切 fallback 模型。

**B. 模型路由（按任务复杂度选模型，而非全程 Pro）**：

| 阶段 | 现行 | 改为 | 预期收益 |
|------|------|------|----------|
| diagnose | Pro reasoner | Flash（模板覆盖场景）/ Pro（仅疑难） | -15~30s |
| agentStep | Flash | Flash 不变，但**单工具任务走 plan-once-execute 零中间轮**（扩到 10 核心工具全覆盖，见 3.4） | -20~40s |
| answer | Pro reasoner | Flash 流式默认；`deliberateStep` 判定复杂才升 Pro | -20~40s |
| review | Flash 同步阻塞 | 异步（先出答案，review 后补标记） | 感知延迟归零 |
| revise | Pro | 仅 review 判不过且预算剩余时触发 | -0~30s |

**C. 消除"卡住"感（感知层）**：SSE 阶段事件→前端阶段时间线（"诊断中→选工具→执行中→绘图→作答"逐步点亮）；工具结果**增量落图**（工具一成图立即上图，不等最终回答）；可取消按钮；骨架文本。**目标：首字节 < 5s，首图层 < 30s，全程有动静**。

### 3.2 数据理解碎片化 → 「模糊识别→标准化转译」+ 专属标准化数据库

**根因**：范围/点类型/极性/时点识别分散在层名正则（E5）、字符串匹配、薄样本（E4）里，无统一数据认知层；后端字典闲置（E7）；切片体系（E8）未接入 EMC 寻址。

**方案（与 2.2 同一 manifest 体系，此处强调"库"的建设）**：

1. **情绪地图标准化数据登记处（Dataset Registry）**：所有数据源（DATA/ 预置 + 用户上传）统一登记 `{datasetId, sliceKey(T1-T3), srcId, manifest}`——切片键复用现有 `tagAllLayers`（E8），manifest 即 2.2 产物。**文件切片化管理** = dataset/slice/revision 三级寻址（lakeFS/DVC 的轻量版），EMC 引用数据时说 `yichang_l2@T2` 而非"那个图层"。
2. **字段精准抽取**：字段字典（E7）为单一事实源；manifest 按 srcId 持久化（localStorage/后端 JSON），同文件再导入零重算。
3. **数据预检（preflight）**：导入即算 `quality`（行数/bbox 合理性/坐标系/极性覆盖率/空几何），**直接喂 diagnose data_plan 三态判定**——"缺数据"不再是 LLM 猜的，是预检报告说的。
4. **LLM 模糊识别的位置**：只负责字典与嗅探都失败的残差字段，且输出必须落到字典 role 闭集（标准化转译），禁止自由发挥。

### 3.3 GIS 工具推理链断裂 → 「方法→尺度→工具→路径」链式思维工程化

**根因**：Flash 从 SKILL_DEFS 一次性直选工具，prompt 里没有"分析方法→适用尺度→工具→执行路径"的链式结构；词表漂移让情况更糟（E9）。

**业界标准做法**：

| 做法 | 代表 | 适配到 EMC |
|------|------|-----------|
| 算法描述符（用途/前置条件/参数契约/输出契约/失败模式） | **QGIS Processing 算法描述体系**（每个算法有完整 descriptor） | 10 核心工具各建一张 **Tool SOP 卡**（下详） |
| 两阶段规划：先选方法再绑工具 | LangChain Plan-and-Execute / Semantic Kernel Planner | diagnose 段输出 `method`（密度/分区统计/排序/缓冲…），执行段 method→tool 确定性绑定 |
| JSON Schema 约束生成 + 校验修复环 | OpenAI function calling / Outlines | 工具参数按 SKILL_DEFS schema 校验，不合法→确定性修复提示重试 1 次（已有 parseAgentStep 修复环可复用） |
| 负例与 few-shot 库 | ToolLLM/API-Bank 工具文档最佳实践 | 飞轮失败例自动入 few-shot 池（审计 P5 五环闭环） |

**实现步骤（按序）**：

1. **建 Tool SOP 卡**（每工具一页，进 prompt 也进文档）：`{purpose, 适用尺度(点/区/网格), inputs(层类型+必需字段), preconditions(如 zonal 需先 ensure_zone), params 契约, outputs(图层/rows/图), 典型失败模式, 正例 2 + 负例 1}`。
2. **diagnose 增 method 字段**（不动现有 template 词表语义，词表漂移按审计 H2 先收编）：method ∈ 方法闭集，与 template 并行输出；**注意承重红线：diagnose prompt 变更前必须先固定 eval**（tests/eval_template_flash.py 扩例后冻结）。
3. **method→tool 确定性映射表**（代码而非 LLM）：density→/geo/density、分区统计→zonal_stats、排序→rank……单方法单工具任务直接 plan-once-execute，**0 中间 LLM 轮**。
4. **多工具链**（如"裁剪→密度→排序"）：Pro 出 plan（步骤数组，$n 引用已有），逐步执行+逐步落图。
5. **校验修复环**：params 过 SKILL_DEFS schema 校验 + manifest 字段存在性校验（2.2），失败给出具体修复提示重试 1 次。
6. **回流**：飞轮每轮失败的 (prompt, 期望, 实际) 三元组入 few-shot 池与 SOP 卡负例位。

### 3.4 核心价值未落地「以图说话」→ 10 工具标准化 + 成图范式

**根因**：数据识别缺失（3.2）+ 工具调用错误（3.3）叠加 → 无图层产出 → 回答退化为纯文本；而 EXIT_RESULT 对表格型工具有单独成功判定（E11），"无图也算成"进一步稀释成图率。

**方案**：

1. **成图范式表（每工具一份，确定性默认）**：默认 paint/图例/弹窗字段/命名规则/空结果处理。例：density→rainbow 色带+强度权重+legend「情绪得分密度」；rank→choropleth 降序+Top3 高亮；buffer→线框+15% 填充+名称含半径。
2. **结果契约统一**：每工具返回 `{layerId|null, rows|null, fig|null, summary}`，`addResultLayer` 强制登记 `_registry`（provenance 已有，`tools.js:345`）。
3. **落图自检**：产出后自动核（features 非空 / bbox 落在请求范围内 / 与输入层不重复 srcId）——失败即标 partial 而非 result（治"假完成"）。
4. **回答即图录**：answer 模板强制"图层引用块"（图层芯片可点击定位）+ ①②③工程摘要页脚（复用 §1 EMC-SUM 格式）——**产品内摘要与测试摘要同一 schema**，飞轮测的就是用户看到的。
5. **优先级**：10 工具按演示链使用频率排序（density/zonal/rank/buffer/clip 先行），逐个做到"单工具任务 0 中间轮 + 成图范式默认 + 自检通过"三件套齐备，再扩下一个。

---

## 四、超越清单的系统性改进（Q4）

### 4.1 架构层

| 改进 | 内容 | 价值 |
|------|------|------|
| **LLM 网关** | 统一封装 DeepSeek 调用：超时/重试/模型阶梯（Flash→Pro→fallback）/每调用延迟与 token 遥测落 jsonl | 3.1 预算制的载体；遥测直接喂飞轮批级头部 |
| **异步任务模型** | 长任务转 job（id+SSE 进度+可取消），回答区先挂"进行中"卡 | 根治"卡住"感；突破 90s 心智上限 |
| **Artifact Store** | 图层/表格/图是一等可寻址产物（srcId/registry 已有雏形），回答、测试、episodes 都以 ID 引用 | "以图说话"的架构地基 |
| **上下文编译器** | buildContext 从"每次现拼字符串"升级为编译管线：manifest 摘要+本轮相关段裁剪+token 预算 | 降延迟降成本，治 context bloat |

### 4.2 数据层

- **字段字典单一事实源**（E7 激活）+ **Dataset Registry**（3.2）+ **manifest 持久化**。
- **episodes.jsonl 复盘管线**：63+ 条真实会话按 EMC-SUM schema 重放标注，作为 golden set 种子——比人造用例更逼近真实分布。
- **勿过早建向量库**：当前规模下字典+清单+grep 足够；RAG 只在 SOP 卡/few-shot 池超过 prompt 预算时再上。

### 4.3 算法层

- **路由模式**：本地快速意图分类（规则/小模型）分流"纯问答/单工具/多步骤"，分别走 general 短路 / plan-once-execute / Pro plan——LLM 调用数与延迟双降。
- **Plan-Validate-Repair 环**（3.3 步骤 5 的 generalized）：所有 LLM 结构化输出过 schema 校验+确定性修复重试，而非裸信。
- **eval 驱动迭代**：飞轮失败→golden set→prompt/SOP 卡修改→重跑回归 gate（pass 率不得降）——这是飞轮从"测试工具"升级为"迭代引擎"的关键一跃。
- **关键参数自一致性**：cell/radius 等数值参数由 LLM 给值 + 确定性合理性钳制（尺度表：社区 250m/行政区 500m/主城 1000m），双保险。

### 4.4 产品交互层

- **进度透明**（3.1-C 阶段时间线）+ **可取消** + **回答页脚 EMC-SUM 卡**（§1 同 schema）。
- **图层即证据**：回答中每个结论挂可点击图层芯片；无图结论显式标"文本推断·未落图"——把"以图说话"变成 UI 契约。
- **去重 UX**（2.1 三态 toast/confirm）+ **字段确认向导**（2.2 低置信时）。
- **成本可见**：设置里显示本 session LLM 调用数/估算 token——与"调用次数优先"承重对齐。

### 4.5 优先级路线（P0→P2）

| 级 | 项 | 理由 | 量级 |
|----|-----|------|------|
| **P0（本周）** | ①滚动复位修复（2.3）②srcId 去重（2.1）③模型路由+预算制（3.1-A/B）④EMC-SUM v1 进飞轮报告（§1）⑤词表收编+信号接通（审计 H1/H2） | 全是"止血"：直接消除四大痛点的表层症状 | 各 0.5~2 天 |
| **P1（下周）** | ⑥Layer Manifest 管线（2.2/3.2）⑦10 工具 SOP 卡+成图范式+plan-once-execute 全覆盖（3.3/3.4）⑧异步 review+进度时间线（3.1-C） | 建立链式思维与以图说话的机制本体 | 各 2~4 天 |
| **P2（后续）** | ⑨Dataset Registry+预检喂 diagnose（3.2）⑩LLM 网关+遥测（4.1）⑪episodes 重放 golden set+回归 gate（4.3） | 数据认知与迭代引擎的长期投资 | 各 3~5 天 |

**红线提醒**：diagnose prompt / 四态出口 / harness 主循环仍是承重——P0/P1 中涉及它们的改动（H1 的 ChatRequest 加字段、method 字段、出口加 partial 权重）**必须先扩 eval 再动手**，且每次只改一处。

---

## 附：与既有文档的关系

- 本方案 §一 = 飞轮审计报告 H5/M4 的格式具象化；§二~四 = 审计 H1-H4、M1-M8 之外的**系统侧**根因治理（审计聚焦飞轮本体，本方案聚焦被测系统）。
- 落地顺序建议：先完成审计报告第一批（H1/H3/H5），再以本方案 P0 接续——两条线共享"词表收编"一项，避免重复劳动。
