# CB 记忆库（Catch-Ball Knowledge Base）

> 跨轮沉淀的 CB 专题知识库。**cb-journal = 按轮时序流水账；本文件 = 按主题蒸馏的复用原则。** 互补不重复。
> `/cb` 命令 step 1 载入、step 4 套用已知结论、step 6 追加新 learning。每条 learning 标 `← CB-NN` 溯源。
> 版本随 CB 轮次演进（CB-03 前据 CB-01/02 经验复盘修订，同 [RULES.md](RULES.md)）。
>
> **记忆共享（通则）**：本文件登记于 [docs/context-map.md](../context-map.md) + AutoMemory `MEMORY.md`（`cb-knowledge-base` 指针），与项目 AutoMemory 双向链接（§1/§2 内嵌 `[[name]]` = AutoMemory 条目名）。不孤岛。
>
> **双阵营（2026-08-01）**：claude组（Claude Code + DeepSeek/GLM 5.2·开发主）+ Codex + glm组（ZCode + GLM 5.2·第三方评估）。本记忆库供三方面共享——红线 §1 对评估方同样生效。

---

## §1 承重红线清单（合并；/cb auto-flag 用）

> 项目方声明的非协商红线。SCAN 建议触碰 → /cb 自动 disagree（撞红线），不接受"简化"。
> 合并自 RULES §3.3 + 项目散落（CLAUDE.md rule 10 + AutoMemory）。

| 红线 | 来源 | 说明 |
|------|------|------|
| 决策追踪编号连续不跳号 | CLAUDE.md rule 10 / RULES §3.3 | 新 ID 经 `register_track_id` 连续分配；"取消编号连续/简化追踪"建议→拒 |
| diagnose prompt 永不动 | RULES §3.3 / [[emc-eval-empty-context-vs-runtime]] | Flash eval 路由依赖 diagnose prompt 完整性；分层/裁剪建议→撞红线 |
| 四态出口契约（success/gap/partial/answered） | RULES §3.3 / [[emc-tri-state-exit-contract]] | harness 代码强制终态；简化/合并出口→拒 |
| L0 走购买途径·sim 充分非风险 | RULES §3.3 / [[l0-acquisition-purchase-strategy]] | 勿把 sim/自采未贯通当风险（曾被我+SCAN 误判） |
| EMC 委托主 Toolbox 不自造 geo 端点 | [[emc-delegates-to-toolbox]] | density 等分析调 generateHeatmap/Grid/TerrainForAI，不自造 |
| aggregate 别名静默零（resolve_field_alias） | [[emc-aggregate-column-alias-silent-zero]] | 中文别名列聚合须按 role 解析实际列，否则 polarity_index 静默零 |

## §2 项目语境卡片（SCAN 不知的）

> 注入这些语境，避免 SCAN 基于文档推断运行时（CB-01 之训：把 AGENTS.md 理论模型当运行时）。

- **L0 获取 = 未来走购买途径**（非自采 Scrapy）；sim 当下有意为之且充分 → 数据管道成熟度评估勿把 sim 当缺陷。[[l0-acquisition-purchase-strategy]]
- **不派 subagent**（用户全局铁律）：AGENTS.md 8/9 Agent 是**概念框架非运行时机制**，主线程直接干 → 调用次数/SOP spawn 类建议常前提不成立。
- **4×5 = 归因落点矩阵（非指标分类清单）**：跨领域×要素多归属。勿用"官方指标完备性"质疑 4×5（错标尺）。[[project-design-philosophy]]
- **eval 空 context ≠ 运行时**（C6）：Flash eval 用 `build_diagnose_prompt('')` 空 context 模拟，不反映已加载层；路由分歧验路由须带 grounding 或 browser，别只信空 context eval。[[emc-eval-empty-context-vs-runtime]]
- **唯一真短板 = 前端测试薄**（34 JS 文件零单测）；非数据、非架构（数据管道 sim 充分、架构七层稳）。
- **演示逻辑链是项目北极星**（CLAUDE.md 最高优先级，[[emotion-map-logic-chain]]）：张力图面→引导点击→交互分析→定位关注区+主题倾向+排序优先级（宏观诊断信号，非精确识别）。**UI/UX 与视觉表现力 = 与架构/代码同等的承重维度**（RULES §2.1 第七轴「演示表现力」10%）——勿用纯工程标尺（架构/代码/测试）低估 UI 债、勿把表现力当"装饰"。SCAN 评估须覆盖演示逻辑链落地度。

- **EMC-Toolbox 参数契约单一源** = `ai_qa/tool_contracts.py`（CB-04 立）：density 参数契约曾四处分裂（[prompts:85](../../ai_qa/prompts.py#L85)/[paradigm:289](../../ai_qa/paradigm.py#L289)/TEMPLATE_REGISTRY/SKILL_DEFS+Tool 各一份不一致·致"消极热力图出综合彩虹图"）→ 单一权威源 + prompt/SKILL_DEFS 派生 + `tests/validate_skill_params.py` 校验治本。**ForAI 入口须 = dialog 入口镜像**（复用 `computeStyle`/`terrainRampOf`，不自带默认另搞一套）；参数面板缺的能力（`PANEL_MISSING`）→ 提醒开发者补，EMC 不自行造。同类坑 [[emc-aggregate-column-alias-silent-zero]]。← CB-04
- **pickVisiblePointLayer 飞轮盲区**（CB-08 F2.0）：[`pickVisiblePointLayer`](../../frontend/js/ai_qa/tools.js#L664) 曾只认 l2-/confidence 点层·漏 colorMode='polarity'（上传点层默认·[state.js:696](../../frontend/js/state.js#L696)）→ resolvePointLayer null → 全点工具报"缺数据"。**飞轮用 L2-group 结构（走 group 分支）测不出**·只有用户独立上传 polarity 点层才中——评估数据布局须覆盖独立 polarity 上传·勿只靠 group 结构飞轮。修法=any-point 兜底。
- **SSE 流式 HTTP/1.0 陷阱**（CB-08 F1.4）：serve.py 代理流式转发须 `protocol_version='HTTP/1.1'`（`SimpleHTTPRequestHandler` 默认 1.0·浏览器缓冲到连接关闭·`wfile.flush()` 无效）·前开发卡此。渐进 token 全链已就绪（后端 `httpx stream+yield` / 前端 `onFinal(tok)`）·唯一断点=代理 `resp.read()` 全缓冲；修法=SSE 分支分块 read+flush+`Connection: close`。
- **工具选型 100%·填参才是路由瓶颈**（CB-08 F3.1）：v2 FC 下工具选择准确率 100%（DeepSeek 实测 12/12）·路由问题在**参数填充**（buffer.center / overlay.layer_a,b / compare.boundaries 缺）非选型。优化投参数提取 few-shot（FC sys prompt）·非选型逻辑；eval 须测参数（`run_fc_param_eval`）·不只 template 字段。
- **范围三来源准则（用户定·CB-14）**：「范围」参数必须锚定**明确来源**（可增补注册机制·非固定枚举）：① 用户绘制 ② 临时上传范围（含需剪裁）③ 固化库范围（预设面域·行政区划等·可剪裁）④ 未来可增补。**EMC 不做自由语义猜测**——范围名锚定失败（不在任何来源）→ 诚实 request_upload（让用户上传标准资料）。**固化库行政区划只识别真实行政区划**（`FIXED_ADMIN_DISTRICTS`·tools.js·当前西陵区/伍家岗区/猇亭区/点军区）；**法定功能区（小溪塔/龙泉/东部产业新区/生物产业园等）不预置**→ 锚定失败→request_upload。灵活性放对地方 = 专注情绪地图专属语义（极性/4×5/归因）·不在非行政区划边界识别上死磕。实现：tools.js `FIXED_ADMIN_DISTRICTS` + deriveAvailable 白名单过滤（固化库 preset 层）+ harness.js derive 错 boundary 校验修复。← CB-14
- **字段字典前后端人工同步易漂移**（CB-08 F2.6）：`core/field_dictionary.py`（权威）↔ `frontend/js/field_dictionary.js`（镜像）原人工同步无 CI·曾 `.py` 有 `zone`/`.js` 缺。新 `tests/validate_field_dict_sync.py` CI 守护（role 集 + variant 集一致）·改字典须两侧同步。
- **FC prompt 无内容守卫 → 静默删已验证段**（CB-10）：0073990「简化 FC prompt」一次删掉**四段**已验证内容（极性范围纪律 / plans 产出指令 / domain_lens 输出指令 / CB-09 M2 多要素提取段），全仓库无内容断言捕获。修法：① 抽 `build_fc_sys_prompt(context)` 小函数（router.py 内联 sys_content 抽出）② 内容断言 `'极性范围纪律' in p and '严禁自行缩窄' in p`（仿 `test_final_prompt_stays_lean` 模式）③ **prompt 改了就测行为**（浏览器复测 B006/TC-25·L01 本质）。「不要动 FC prompt」教训针对**重写**，revert 式还原（恢复已验证原文）风险等级不同。← CB-10
- **CPD-RESERVED 是空骨架**（CB-10）：0073990 删除 plans 产出指令后，`ctx.plans` 只有后端自建 rank=1 单元素（router.py:96-105），rank=2+ 恒空。`_plansToCapsules` 纯函数 + `ctx.plans` 赋值保留 = **接口预留**，非活数据路径。CPD 复活时须**同步恢复 plans 产出指令**（FC prompt 段）否则仍是空骨架。避免下轮把「预留接口」报成「死代码」也避免把「空骨架」当「已实现」。← CB-10
- **生成器 --check 逐字节比对遇时间戳脆弱**（CB-10）：`_gen_index.py render_summary` 头部「最后更新」时间戳每次重渲染变化 → `--check` 全文逐字节比对 → 过分钟必红·CI 守护实质失效。修法：--check 比对时**忽略时间戳行**（或时间戳仅生成不参与比对）。同类「生成器含当前时间」的 --check 都要留意。← CB-10 ③
- **结论颗粒度 = 数据来源维度（跨轮蒸馏·CB-22 确立·用户多轮澄清）**：城市体检/更新 = **四维度（城区⊃街区⊃社区⊃小区+零散住房/城中村·层级包含关系）**。**概念关键：社区≠小区**——社区=行政区划（设党群中心·官方管理·调研最小单元·机制决定）·小区=居住形态单元（社区子集）·社区⊃n 个小区+零散住房+城中村（城中村/指定片区另有专项调研）。**数据来自哪个维度+颗粒度 → 只能得到哪个维度+颗粒度的答案**。最小调研单元是社区但**数据到栋即可答到栋**（GIS 危旧房 380 栋/结构隐患 42 栋到栋·停车 140 小区到小区）·不臆造越维。**历史权威源 = `paradigm.py` SCALE_PARADIGM 三尺度范式**（macro=城区/meso=街区·小区/micro=住房·小区·已硬编码 city_checkup_level·含 forbidden 铁律：宏观禁落单点·微观禁泛泛）。08-03 出口抽象层讨论定稿（`EMC-出口抽象层架构讨论_2026-08-03.md`）·**讨论过即沉淀·跨轮充分消费不重起炉灶**。→ 检索/回答标注数据维度·回答不越维·黄金集含越维问题验证。[[emc-compare-skill]] ← CB-22
- **纯回答稳定性 = 三支柱缺一不可（跨轮蒸馏·CB-22 用户定·零 LLM 教训）**：① **本地知识库完备度**（素材·事实卡/笔记/政策/案例·决定信息基础）② **EMC 架构**（分类→范式映射·决定问题正确路由到对应回答范式）③ **LLM 归纳总结能力**（综合素材 + 引用来源·决定回答质量与表达）。**RAG 检索出相关文件后必须走 LLM 综合总结**——零 LLM（确定性拼列表）= 把检索结果当答案·违背三支柱·用户人工验证否定（CB-22 教训：claude 采纳 glm「确定性组装」方向·砍掉 LLM 支柱·根本错误）。→ 知识问答路径 = RAG 检索素材（知识库）→ 架构路由知识问答范式（EMC 架构）→ LLM 综合 + 引用来源（LLM 能力）。**任何方案不得砍三支柱之一**。← CB-22
- **EMC+RAG 产品定位 = 本地化聚焦专业知识蒸馏（跨轮蒸馏·CB-22 用户定·项目最根本定位）**：EMC 通过 RAG 实现的效果 = **纯问答 → 得到稳定、准确、全面的相关信息**（当前基于宜昌城市更新/城市体检专题）。**核心价值 = 区别于通用网络搜索/其他 AI**——EMC 蒸馏出的是**① 本地化**（宜昌专属·非通用）**② 聚焦**（城市更新/体检·非泛泛）**③ 专业**（权威源·政策/指标/项目）**④ 可追溯**（来源引用·防张冠李戴）的专业知识。三支柱的最终目的即服务此定位：知识库=本地化聚焦专业素材·架构=正确路由·LLM=蒸馏成稳定准确全面回答。← CB-22
- **契约 `when` = FC 工具 description**（CB-09·承重）：[`contracts_to_tools_schema`](../../ai_qa/tool_contracts.py#L438) `description = c.get('when') or voice`——即 `TOOL_CONTRACTS` 每工具的 `when` 字段**直接成为 FC LLM 看到的工具说明**。故误导性契约文本（如 extract_feature 曾写"抽**单要素**"）会**直接误导 LLM**（比 sys prompt 更上游·LLM 先看工具描述）。判据：FC 推理死循环/错报"缺能力"时，**先查契约 `when`/`voice`/`failure_modes` 是否误导**，改契约描述优先于补 sys prompt。← CB-09（multi-extract 死循环首例）

## §3 SCAN 标尺纠正模式（SCAN 倾向 → 正确标尺）

> 每条 = 跨轮验证的 SCAN 评估倾向 + 项目方正确标尺。/cb step 4 遇匹配模式 → 套结论，不重推。

| SCAN 倾向 | 正确标尺 | 溯源 |
|-----------|---------|------|
| 基于 AGENTS.md 理论模型判运行时（算 SOP spawn 次数） | SOP spawn 前提误判（项目不跑 SOP spawn）；但**调用次数确实关键**——优化靠会话切分+精准读+大宗隔离（全局「调用次数优先策略」），非 SOP 合并 | ← CB-01（4 条高优 declined），CB-02 §0.2 确认；CB-03 后策略厘清 |
| 优化前不查活引用（直接建议 perf 改进） | 先 Grep/Read verify usage；死代码→退役非优化（CB-01 db.py 实为 executemany + 零引用） | ← CB-01 建议7 |
| 未察觉 MANIFESTO ↔ diagnose prompt 耦合 | MANIFESTO 分层破坏 Flash eval 路由完整性 → 撞承重红线 | ← CB-01 建议4，CB-02 §0.2 确认 |
| 完成度把"接口预留"计为"已实现" | 偏高；真实约 8 折（L3/L4 backend ⬜ 预留 ≠ 实现） | ← CB-01（90%→真实 75-80%），CB-02 折中 80% |
| 把 sim 数据/自采未贯通当风险 | L0 走购买、sim 充分 → 非风险 | ← CB-01 澄清（用户），CB-02 §0.2 认可 |
| 用"官方指标完备性"质疑 4×5 归因 | 4×5 = 归因矩阵（多归属）非指标清单（互斥穷尽）→ 错标尺 | ← 项目设计哲学（CLAUDE.md），CB 通用 |
| 把不同用途的 sim/工具脚本误判"功能重叠"→ 建议同退役 | 先查 docstring/原职责定用途；非真冗余不并退役（generate_test_data=L0 raw 全管线测试 vs sim_performance_data=L1/L2 demo） | ← CB-02 建议4 |
| 根因分析凭代码推断/转述·不拉原始 trace.log（数 F_001 猜 while-loop / 猜 API 慢） | **trace 取证第一动作**：`trace_query --stats` 数 F_002（agentStep·while-loop 铁证）/F_003/F_005·勿用 F_001（公共出口）；trace.log 在仓库各组件直读·不依赖转述；推断只作假设 | ← CB-12 B3 大失败（claude/Codex 凭 F_001 推断错两次·glm组 读 trace 定案 while-loop） |
| 把「测量层修复」当「执行层修复」（断言端修复未生效 → 疑执行 bug） | **先分文件归属**：`test-cases.js`=测量端（断言参数收集）·`harness.js`/`prompts.py`=执行端（路由/工具选型）·测量修复只在其守的前提（执行正确）成立时有效·执行错则测量"失效"是表象 | ← CB-13（3abb503 多 boundary 收集仅测量端·PRM-08 实为 FC 选型偏离） |
| template 路由对但工具错 → 归因 select_template | **先查 FC 阶段工具选型**：FC 独立做工具选择（看 sys prompt「工具选择决策」规则排序 + 各工具 when/examples 诱导性），**不消费 template 信号**——template 对但工具错时查 prompts.py 决策规则 + tool_contracts 各工具 when/examples | ← CB-13（PRM-08 compare→extract_feature·RST-L02 同句 PASS 对照） |
| 预防性兜底结果好 → 建议拆除 | **看它防的风险是否仍在**（如 FC 方差），非看当前结果好坏；F_002 低位正是兜底生效的结果 | ← CB-13（recover 链前置 / seq-chain 合成 diagnose 勿拆） |

## §4 Decline 模式库（reason 类型 + 例）

> decline 时附 reason，保证跨轮一致。/cb step 4 disagree 项必落其一。

| reason 类型 | 含义 | CB 例 |
|------------|------|-------|
| **用错标尺** | SCAN 用了不适合项目的评价框架 | CB-01 MCP"应与 DeepSeek 匹配"（MCP provider-neutral）/ 官方完备性质疑 4×5 |
| **事实错误** | SCAN 描述与代码不符 | CB-01 db.py"用 iterrows 逐行插"（实为 executemany）/ CB-01"数据管道 90% 全实现"（L3/L4 ⬜） |
| **撞承重红线** | 建议触碰 §1 红线 | CB-01 MANIFESTO 分层（撞 diagnose 永不动） |
| **无消费方 wontfix** | 修复改动无活消费方 | CB-01 zonal_stats latent bug（n_dom/n_elem 无人从 trimmed 响应读） |
| **前提不成立** | 建议基于对项目运行方式的误判 | CB-01 调用次数优化（不派 subagent）/ CB-01 Reviewer+Tester 合并（同） |

## §5 轮次溯源索引

> 每轮 CB 一行摘要 + 指向 cb-journal 章节。

| 轮 | 日期 | SCAN | 综合分 | 关键产出 | cb-journal |
|----|------|------|--------|---------|-----------|
| CB-01 | 2026-07-18 | [SCAN_DeepSeek_01.md](SCAN_DeepSeek_01.md) | 7.6 | 删 5 僵尸（Streamlit/pydeck/db）/ geo_routes 三处清理 / sim 注册 / e2e seam 去生产化 / §0 任务树刷新 / **5 类 declined**（调用次数前提不成立等） | `## CB-01` |
| CB-02 | 2026-07-19 | [SCAN_DeepSeek_02.md](SCAN_DeepSeek_02.md) | 7.6（持平） | CB-01 回顾核验（agree 4 通过 / disagree 3 成立）/ 新发现 requirements 僵尸依赖 + range_selector 路径大小写 + AGENTS.md 8→9 漂移 / 10 条新建议待 `/cb 02` 反评价 | `## CB-02`（②③ 待填） |
| CB-04 | 2026-07-27 | [SCAN_EMCArch](report/SCAN_EMCArch_deepseek_2026-07-27.md) | 6.5（执行层 4↓） | EMC density/polarity 流水线契约整改：14 入口全审·13 agree/0 disagree/1 partial·plan 融合定稿（L1 双维度+R1+P1b+P1c / L2 tool_contracts 单一源 / L3 全扫）·契约分裂模式入 §2·最高纪律（复用参数面板） | `## CB-04` |
| CB-08 | 2026-07-28 | [DEEP_DIVE](emc-arch-deepdive/DEEP_DIVE_2026-07-28.md) | —（修复轮·非评分） | EMC v1.0 聚焦修复 3 WS（耗时 Flash 默认+SSE 流式 / 识别 F2.0 polarity 元凶+字段 dict fuzzy+同步 CI / 路由 FC 参数 few-shot+eval 参数覆盖）·9 agree/1 disagree/5 partial·**据实 drop** F1.3（single 类别非 while-loop）+F2.1-3（C2 门已对·field-role 门重造假缺数据）+F3.2-3（前端已捕获·alias 撞名）·4 新 learning 入 §2 | `## CB-08` |
| CB-09 | 2026-07-28 | [rootcause multi-extract](rootcause/2026-07-28-multi-extract-reasoning-spiral.md) | —（修复轮） | multi-extract 死循环（裁剪西陵+伍家岗）：M1 `_norm_where` 拆逗号(in list) + M2 FC sys prompt 多要素指引 + **M3 契约 extract_feature 去"单要素"误导**（我补 DeepSeek 漏报：契约 `when`=FC description·上游根因）·4 agree/1 partial/1 已存在/1 defer | `## CB-09` |

---

## §7 评估协作规则（CB-16 ③z 确立·2026-08-04）

> 评估方（Codex / glm组）与开发主（claude组）**同一本地工作区**协作。跨轮共识，勿再违反。

1. **评估方不 git pull / 不 git push**——只读本地文件即可（工作区与 claude组 同步，claude组 负责 git 操作）。请求文档第一步统一写「读本地文件·无需 git pull/push」。
2. **claude组 先验后推**：发起/预检文档（草案）可 push（供评估方读 + 跨环境同步）；**实施代码须两组检查通过后才 push**（先验后推·`先讨论再实施`）。
3. 请求文档模板：`docs/catch-ball/_handoff/CB{NN}-{topic}预检*.md`（第一步读本地文件·第二步草案·第三步预检 N 问·第四步产 SCAN）。
4. **测试任务三组并行（2026-08-09 新规）**：测试负载重、单靠人眼测难以为继 → **claude组 拆解测试任务、针对性分配三组（claude组/Codex/glm组）同时进行**；claude组 分发前先确认各组平台 Harness 环境就绪（Python/Playwright/API Key/trace/端口隔离·三组并发 B3 需 `--port/--backend-port` 隔离 + sys.executable）；claude组 持续提出 CB 机制优化意见（工作坊式先进性/流畅性/科学性）。[[cb-distributed-testing]]
   - **三组环境就绪（08-09 自检）**：glm组 7/7 OK 全能力；Codex 5 OK + 2 WARN（SessionStart hook 已补 `.codex/hooks.json`·多模态 Key 缺失 → 多模态/OCR 类用例 Codex 不承接·claude组/glm 承接）。报告：`discuss/CB环境自检_回应_Codex-GPT5_2026-08-09.md` + `_handoff/CB环境自检_glm组_2026-08-09.md`
   - **session 标签纪律（glm 实测·08-09 采）**：`EMOTION_TRACE_SESSION` **仅 B3/e2e 浏览器用例需要带**（走真实问答链路 FC→工具→finalStep·产 trace）；**pytest 单测/静态核验不产 trace·无需带**（glm 实测带 session 跑单测·trace 查询返 0 行）——分配任务时标注测试类型决定是否带标签。

## §6 Auto-Check 清单（/cb step 5 加载·数据驱动，CB-03 建议2）

每次 counter-evaluation 必须执行（可追加，不删除）：

1. **承重红线检查**：建议是否触碰 §1 任何红线？→ auto-disagree。
2. **核实再接受（verify-before-accept）**：agree 前是否已 grep/读代码核验 SCAN 的事实陈述？
3. **无消费者→wontfix**：涉及的功能/代码路径是否有活消费方？
4. **已知模式匹配**：是否匹配 §3 任何标尺纠正模式？→ 应用已知结论。

## 维护策略

- **pruning 触发**（CB-03 讨论2）：§3（SCAN 标尺纠正）>15 条 → 按"近 3 轮是否再触发"归档低频；§5（轮次溯源）>10 条 → 仅留近 5 轮 + milestone（首次/评分变 >0.5）；文件 >200 行 → 评估拆分。当前 ~80 行，无需 prune。
- **CB 节奏决议**（CB-03 讨论3）：三轮高频 CB（~30 小时）后转**低频维护模式**——每 5-10 个功能 commit 触发一次 SCAN（非每轮 CB 后即 SCAN）。hook detector 保留（仍提示新 SCAN），评估节奏放缓。

---

> **下次更新时机**：CB-04 前据 CB-03 经验复盘修订（同 RULES.md）。新 learning 由 /cb step 6 入库。
