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
| diagnose prompt 永不动 | RULES §3.3 / [[emc-eval-empty-context-vs-runtime]] | Flash eval 路由依赖 diagnose prompt 完整性；分层/裁剪建议→撞红线。**2026-08-09 用户豁免**：diagnose intent 枚举加 `knowledge_qa`（增量不改不删现有三值·CB-22 三层架构·NL 意图判断归 LLM）——豁免 3 条件：① 增量加类 ② eval 复采通过（含模板命中 gate 0.6）③ 静态断言守现有判据文本·**不通过回滚**。**2026-08-10 第二次豁免（CB-22d）**：选择要点铁律 + TEMPLATE_REGISTRY + GEO_TOOL_CATALOG 增量加 `generate_point_layer` 技能条目（批量地名标点·知识问答→地图标记·增量不加值不改现有·FC 主路径走契约 when 不依赖铁律）——豁免 3 条件：① 增量加技能条目 ② eval 复采通过 ③ 静态断言守现有技能 id（`test_emc_template.py` 全在 + 新增 `validate_generate_point_layer.py`）·**不通过回滚** |
| 四态出口契约（success/gap/partial/answered） | RULES §3.3 / [[emc-tri-state-exit-contract]] | harness 代码强制终态；简化/合并出口→拒 |
| L0 走购买途径·sim 充分非风险 | RULES §3.3 / [[l0-acquisition-purchase-strategy]] | 勿把 sim/自采未贯通当风险（曾被我+SCAN 误判） |
| EMC 委托主 Toolbox 不自造 geo 端点 | [[emc-delegates-to-toolbox]] | density 等分析调 generateHeatmap/Grid/TerrainForAI，不自造 |
| aggregate 别名静默零（resolve_field_alias） | [[emc-aggregate-column-alias-silent-zero]] | 中文别名列聚合须按 role 解析实际列，否则 polarity_index 静默零 |
| 密钥只输出 key 名（禁贴值） | CB-39 D9 | CB/审计/交接文档禁出现 key 值（子代理会话明文+归档扩散风险）；验证走 `tools/verify_keys.py`（不回显值·退出码可接 CI）；疑似泄露即轮换（SOP：`tools/KEY_ROTATION.md`）并只述名 |
| 静默丢数据禁令（聚合/过滤链） | CB-41 B014 / debug-memory R2 | 点按列值匹配/过滤时空值行（NaN/''）**不得隐式整行丢弃**——空值=无信息≠负信息；异构属性 GeoJSON（features 属性不齐）联合读入后空值是常态。丢数据必须可观测（in_n/out_n 对账） |
| 多入口工具逐入口验证 | CB-41 B014 / debug-memory R1 | 同功能多入口（dialog UI / ForAI / 不同后端路由）验证须逐入口跑——路由间参数默认值+数据构建方式即行为分叉点；函数直调正确≠路由正确 |

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
  - **零 LLM 边界（CB-22 两组对齐·Codex 挑战 2·防以"R3 先例"回潮）**：零 LLM **只允许出现在失败兜底**（R3 EXIT_CONCEPT·RAG 检索不可用/无素材时·禁 LLM 凭空编）；**成功路径必须 LLM 综合**——不得以"R3 已有零 LLM 先例"为由把成功路径也砍成零 LLM。
- **全局调试记忆库已建（CB-41·2026-08-18）**：[`docs/debug-memory.md`](../debug-memory.md)（R1-R10·多组共享·AGENTS.md 知识源表已登记）——多入口逐入口验证 / 列值匹配禁静默丢空值 / 显示 bug 按数据→映射→渲染三层排查 / bbox 中心禁做空间归属 / trace+netstat 第一实证 / 旧进程载旧码必问重启 / 验证忌同构 / 复算落单元粒度 / 同族复发=修症状没修语义。**SCAN/评估发现同类坑引用规则编号（debug-memory R#）·修复复盘新规则追加于此**。← CB-41
  - **LLM 综合边界（CB-22 两组对齐·Codex §2 建议·产品定位"准确"的依赖）**：LLM 综合 = **归纳 + 组织 + 表述素材·不新增事实**——素材未覆盖的信息标注"知识库未收录"·禁止以预训练知识补细节/补素材外数值（黄金集③"案例不引数据"即此边界的机器化）。注：素材**内容**须随索引持久化注入（`tools/rag_index.py` meta `text` 字段·CB-22 承重发现——此前仅文件名无内容·三支柱①空转）。← CB-22 对齐轮
  - **概念归纳纪律（CB-22 用户实测·2026-08-09）**：素材卡的**分类术语/归纳标题必须来源可溯**（从源文档/笔记摘录·禁 LLM 自创分类术语——用户会质疑"这是 LLM 自己定义的吗？"·业内不专业）。**版本口径严格标注**（如 00-03 最新版 260713 的 55 项目 vs 00-02 老版 0610 的 43 完整社区·勿混算·曾把老版口径安到最新版构成·张冠李戴）。
  - **素材卡术语纪律三分（CB-22 用户实测·2026-08-09 深化）**：① 源文档有**正式分类术语**→沿用（如住建部"四维度/八大领域"）；② 源文档**无分类**→直接罗列事实（数字+片区名）·不造分类名；③ 源文档有但属**非正式工作稿用语**（如"典型片区类/机制建设类"提炼者归纳标签）→罗列事实·用户判定不要即改。「典型片区类/机制建设类」曾入素材卡·用户判定非专业·已去（URP-P01 改"前 4 组合计 43 个/其他项目 12 个"·排除描述非分类名）。**覆盖全部向量化素材**（fact 卡 + note 段落 + concept 卡）——L0 提炼笔记段落也是素材·提炼时同样禁硬造分类（曾漏改 note:43 致 LLM 综合出硬造分类·用户"记住"·CLAUDE.md 铁律 13）。**LLM 综合禁从数字推断分类/解释**（指令 3 扩展·"侧重制度与保障机制搭建"是 LLM 顺着标签自创解释·素材无此表述）。
  - **来源标注可读性（CB-22 用户实测·2026-08-09）**：来源标注的使用逻辑 = **让用户确认数据有确切来源（非编造）→ 须可读可查**——用**可读完整名称**（笔记「完整名称」字段·如《宜昌市中心城区城市更新专项规划260713（阶段性成果 PDF 版）》）或 **LLM 提炼简短标题**（从内容归纳·用户能懂）·**禁内部代号**（如 00-03/260713 版·用户看不懂）。LLM 介入判定：原文有完整名称→直接用；无→提炼标题。素材卡 `source` 可读 + `source_path` 内部路径双字段。
- **EMC+RAG 产品定位 = 本地化聚焦专业知识蒸馏（跨轮蒸馏·CB-22 用户定·项目最根本定位）**：EMC 通过 RAG 实现的效果 = **纯问答 → 得到稳定、准确、全面的相关信息**（当前基于宜昌城市更新/城市体检专题）。**核心价值 = 区别于通用网络搜索/其他 AI**——EMC 蒸馏出的是**① 本地化**（宜昌专属·非通用）**② 聚焦**（城市更新/体检·非泛泛）**③ 专业**（权威源·政策/指标/项目）**④ 可追溯**（来源引用·防张冠李戴）的专业知识。三支柱的最终目的即服务此定位：知识库=本地化聚焦专业素材·架构=正确路由·LLM=蒸馏成稳定准确全面回答。← CB-22
- **契约 `when` = FC 工具 description**（CB-09·承重）：[`contracts_to_tools_schema`](../../ai_qa/tool_contracts.py#L438) `description = c.get('when') or voice`——即 `TOOL_CONTRACTS` 每工具的 `when` 字段**直接成为 FC LLM 看到的工具说明**。故误导性契约文本（如 extract_feature 曾写"抽**单要素**"）会**直接误导 LLM**（比 sys prompt 更上游·LLM 先看工具描述）。判据：FC 推理死循环/错报"缺能力"时，**先查契约 `when`/`voice`/`failure_modes` 是否误导**，改契约描述优先于补 sys prompt。← CB-09（multi-extract 死循环首例）
- **RAG 链 = 纯 git 内数据源·不依赖 OneDrive/G 盘（CB-22 家环境补链确认·2026-08-09）**：`tools/rag_index.py` 的 4 个来源**全部在 repo 内**（`docs/urban-renewal-plan/` 提炼笔记 + `ai_qa/outlet_kb/` 三 py 文件），**原始资料（OneDrive/G 盘 875+ 文件 docx/pptx/GIS）从不进索引**（CB-21b 共识：原文不复制进 repo·只存提炼笔记 + `{URENEWAL_ROOT}` 占位引用）。故**换环境 RAG 索引可独立重建·与 OneDrive 路径无关**；`{URENEWAL_ROOT}` 只影响 L0 原文溯源（`_PATHS.md` 双环境配置表：办公室 `G:\` / 家庭 `C:\Users\Hi\`·均已填）。**RAG 补链三步**：① `pip install -r requirements-rag.txt`（**torch `2.13.0+cpu` PyPI 默认源无 `+cpu` 标签·须从国内 PyTorch 镜像拉**——阿里云 `mirrors.aliyun.com/pytorch-wheels/cpu/torch-2.13.0+cpu-cp314-cp314-win_amd64.whl` 实测可用·官方 download.pytorch.org 国内慢）；② BGE 模型 `BAAI/bge-small-zh-v1.5`（脚本内置 `HF_ENDPOINT=https://hf-mirror.com`·首次 build 自动下载）；③ `py tools/rag_index.py --build` 重建（索引不入 git·**每环境必建**）。**家环境已建**：235 条（fact 36 + note 185 + case 5 + concept 9·维度 512）。← CB-22
- **AMAP_KEY 在历史会话可找回（2026-08-09 恢复）**：高德 key `7294b86...16` 曾写入 `.env:3`（历史会话上下文记载）·家环境 .env 重建时丢→ 从 `~/.claude/projects/<proj>/*.jsonl` 会话历史 grep `AMAP_KEY=` 找回·已补回 `.env` 并实测高德 API `status=1` 有效。**换环境补 .env 时先查历史会话找回既有 key**（避免重复申请）。
- **降级结论「选观察行」坑（CB-22e 两组实锤·2026-08-10）**：`_composeDegradedConclusion`（harness.js:602）用 `/已生成|产出|单元|点|层/` 筛选 toolHistory 后 **`slice(-1)` 取末行**——generate_point_layer 的 observation 三行里 tip 行（含「点」「图层」）**必然**是最后匹配行，而「命中 N/M」行永远被丢弃 → 部分命中（N<M）与全命中的降级结论**不表述 N/M**。修法：优先规则「任一行为 `/命中\s*\d+\/\d+/` → 取首个该行·否则维持 slice(-1)」。**通用降级是为分析类 finalStep 超时设计·对产物 observation 多行格式的准确表述须验证/特化**（glm 补充：先手测·不准再改）。← CB-22e
- **FC 契约「伪工具」承载无工具意图（CB-22f Codex·2026-08-10）**：FC 前端把「无 tool_calls」直接判 `degraded`（stages.js:316-318）——纯问答意图（无 GIS 工具）不能用「FC 返空」承载。二选一：**方案 B 伪工具**（TOOL_CONTRACTS 加 `{skill:'knowledge_qa', tool:'knowledge_qa', category:'knowledge', when:None, params:[]}`·when=None 不进 GEO_TOOL_CATALOG·contracts_to_tools_schema/text 的 exclude_categories 默认扩 ('concept','knowledge')·_normalizeFcDiagnose 加映射）·方案 A content 标签（`[intent:knowledge_qa]`·stages.js:402-404 同款解析）。**铁律 11 同步**：走方案 B 须同步前端 SKILL_DEFS 镜像/validate_skill_params/validate_paradigm_map 断言（契约三处同步）或显式豁免。← CB-22f
- **`_normalizeFcDiagnose` 二元硬编码 intent（CB-22f 两组核实·2026-08-10）**：stages.js:361 `intent = _EMOTION_TOOLS.has(toolName) ? 'emotion_analysis' : 'gis_operation'`——只产两值·**永不产 knowledge_qa** → harness.js:1234 `if (intent === 'knowledge_qa')` 合流分支不可达（变体纯问答「宜昌市城市更新的项目有哪些」落 GIS 路径→GAP/ask）。改三分支：`_EMOTION_TOOLS → emotion_analysis / 知识类 toolName → knowledge_qa / else → gis_operation`。**纯问答只靠 6 词加速器**（emc-patterns.js RAG_QUERY_KW·设计意图「最小化宁漏不误」——不扩词表·根治走 D1/D2 契约+映射）。← CB-22f
- **`exclude_categories` 误扩会把伪工具从 FC schema 排除（CB-22f Codex 实施级修正·2026-08-10）**：`contracts_to_tools_schema`/`contracts_to_text` 默认 `exclude_categories=('concept',)`（tool_contracts.py:456/501·`:471 if not c.get('tool'): continue` 只挡无 tool 项）——加 knowledge 伪工具（category='knowledge'）后**默认保持 ('concept',) 不动**；若扩 ('concept','knowledge') 会把 knowledge_qa 从 FC schema 排除·FC 反而调不到它·方案 B 失效（方向反）。同时 `derive_template_registry`（:366-381）**无 category 过滤**——knowledge_qa 会进 TEMPLATE_REGISTRY → 技能目录进 diagnose prompt 文本 → 撞「diagnose prompt 永不动」红线·须加 `category=='knowledge'` 过滤。**新增契约类须查三处派生函数消费面**（schema/registry/catalog·各自过滤语义不同）。← CB-22f 详细讨论
- **track ID 编号须核对现有最大再分配（CB-22f glm 修正·2026-08-10）**：讨论发起文档写 query_knowledge_base → MOD_AIQA.F_018 起·但核实现有最大编号 = **F_015**（rag_search·F_016/F_017 未占用）——跳号违反「追踪编号连续」红线。**分配前先 grep `MOD_XXX.F_0[0-9]+` 取现有最大 +1**，勿凭文档。← CB-22f 详细讨论
- **FC 空 tool_calls 路径（CB-22f glm 实施级·2026-08-10）**：`fcDiagnoseStep`（stages.js:316-318）`if (!tc || !tc.function) return { degraded: true, _fcError: 'no_tool_calls' }`——FC 空 tool_calls 直接判 degraded。加 knowledge 伪工具后·方案 B（FC 返 knowledge_qa tool_calls）走 :332 _normalizeFcDiagnose OK·但**方案 A content 标签兜底**（FC 空 tool_calls + content 含 `[intent:knowledge_qa]`）仍走 :316-318 degraded——须显式改此处（content 含标签 → 返非 degraded knowledge diagnose）。**plan 实施点须列全改动文件/行·防只改归一层漏兜底层**。← CB-22f 详细讨论
- **LLM 流式挂起 → 无降级兜底 = 读秒卡死（CB-22h glm 承重根因·2026-08-10）**：`_assembleKnowledgeQA` 的 finalStep（harness.js:214）**裸 await 无 try/catch**——对比 runTemplatePath:850 有 catch→`_composeDegradedConclusion`·知识问答路径漏降级兜底（CB-22f 回归）。DeepSeek 流式挂起→前端 45s abort→finalStep throw→无 catch→裸抛→onFinalDone 不触发→UI 读秒不停（真实会话 sess-34620 挂 5.5 分钟铁证）。**新增 finalStep 调用路径必须带降级兜底**（catch→诚实文案·保 onFinalDone 收尾）·对照已有 catch 的 runTemplatePath/runChainPath。← CB-22h
- **httpx read timeout 是「每两 chunk 间」非总时长（CB-22h Codex/glm·2026-08-10）**：`httpx.Client(timeout=60.0)` 标量 → connect/read/write/pool 各 60s·**read=每两次 chunk 之间最多等 60s**——DeepSeek 间歇心跳/空 chunk 会重置计时·流式挂起无异常绕过 retry/fallback（trace 挂 5.5 分钟 >60s 铁证）。修：① **墙钟总 deadline**（`time.monotonic() + TTL` 每 chunk 检查·超时抛 LLMError→SSE error 帧→前端降级·释放 zombie 线程）② httpx timeout 显式分段（connect=15/read=60/write=30/pool=15·防 connect 无限等）。**流式调用的超时 = 总预算 deadline 而非单 chunk 读超时**。← CB-22h
- **BGE 预热 daemon 线程竞态（CB-22h glm·2026-08-10）**：`api/main.py` startup 用 `threading.Thread(daemon=True)` 异步预热 RAG 模型——用户首问在预热完成前到达→rag_search 内**同步加载 15.9s 阻塞 uvicorn 事件循环**（sess-34620 铁证）+ finalStep LLM 排队。修：**预热改同步阻塞启动**（startup `await warmup()`·uvicorn 等加载完再接请求·启动慢 ~15s 换首问稳定）·或端点检测未加载返友好提示。**后台预热须可观测（完成标志/日志）·不能静默竞态**。← CB-22h
- **trace 取证须核会话身份 + track ID 语义（CB-22h 上轮教训·2026-08-10）**：CB-22g 曾把 pytest 会话（sess-22008·25s·含测试 fixture 指纹）误当用户会话·F_005 误判为 FC（实为 build_diagnose_prompt·FC 端点无埋点）→ 整条根因链不成立（Codex 戳穿）。**修**：① 先核会话身份（PID 对照 wmic：sess-34620 的 34620=uvicorn PID→真实用户）② 核 track ID 语义（register_track_id 查注册）③ FC 端点补埋点（F_019）·否则 FC 失败在 trace 不可观测。**trace 取证不能凭计数推断·须核身份+语义**。← CB-22h
- **deadline 被动检查在生成器阻塞时不可达（CB-22i glm 承重根因·2026-08-10）**：`for chunk in cli.chat()` 循环体内放 deadline 检查·**生成器阻塞在 `__next__()`（首 chunk 前挂死·DeepSeek 连接建立但无 SSE data）时·循环体永远不执行·deadline 永不触发**（Python 实测铁证 + trace 17:29 有 D_004 vs 18:09 无 D_004 对比）。httpx read timeout 同理——「每两 chunk 间」·首 chunk 前不计时/被 TCP keepalive 重置。**修 = 主动中断**：`threading.Timer(ttl, resp.close)` 强制 close·iter_lines() 抛 StreamClosed→LLMError→SSE error→前端降级（实测 1.2s 中断）。**流式调用超时须主动中断（Timer/异步 cancel）·非被动检查循环体内**。← CB-22i
- **Playwright page.route 桩测盲区（CB-22i glm·2026-08-10）**：`page.route` 前端层拦截·**绕过 serve 反代 + uvicorn 真实阻塞链路**——模拟「fetch 已 resolve 后 reader 阻塞」（abort 能 reject reader→降级 ✅）·但真实场景是「fetch 未 resolve（serve 反代挂在 urlopen·200 未返）·await fetch 等响应头被卡」——**桩测"通过"测的不是真实场景**。且 serve（SimpleHTTPRequestHandler 单线程）后端挂死会拖死后续请求排队。**验证真实挂起须后端层模拟（monkeypatch LLMClient.chat 永不返回 / 本地挂死 SSE server）·非前端 route 桩**。← CB-22i
- **serve 反代 + 前端 fetch 双重挂死兜底（CB-22i·2026-08-10）**：后端 uvicorn 挂死→serve 反代 `urlopen(timeout=60)` 同款心跳陷阱也挂→前端 `await fetch` 等响应头被卡·abort 的 TCP FIN 因 serve 单线程阻塞延迟处理→读秒 5 分半。**修 = 三层兜底**：① 后端 LLM Timer 主动中断（根治阻塞源）② serve 反代 `_send_streamed` Timer 强制 close（50s·防 serve 拖死）③ 前端 `Promise.race` fetch 总超时（45s+5s·防 abort 延迟）。**流式链路任一层挂死都须有独立总超时兜底**。← CB-22i
- **用户 tab 常驻旧 JS（CB-22i Codex·2026-08-10）**：ES module 页面加载时一次性拉取·**常驻页面内存·serve 重启/文件更新不刷新已打开页面**——三次修复若用户 tab 未刷新·全部落空（"没有任何变化"最简解释）。serve `?v=mtime` + no-store 都正常·**刷新即新 JS**。**排查"修复无效"先让用户强刷（Ctrl+Shift+R）/重开标签页**。← CB-22i
- **`JSON.parse(...).slice` 对对象报错（CB-22i 追问标记崩溃根因·2026-08-10）**：panel.js `_distillTurn` extracted 回灌写 `JSON.parse(JSON.stringify(_ext)).slice(0, 5)`——但 `_ext` 是 **`{geo,attrs}` 对象·无 `.slice` 方法** → `PAGEERROR: JSON.parse(...).slice is not a function` → 追问消费 `priorTurn.extracted` 时链路崩（用户「追问标记没反应」直接根因·Playwright 抓 console 定位）。修 = 对象属性限制（`geo` 数组 slice ≤5·`attrs` slice ≤8·深拷贝）。**截断须作用于数组字段·非对象本身**·排查前端崩溃先抓 console PAGEERROR。← CB-22i

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

1. **评估方不 git pull / 不 git push**——只读项目数据与代码即可（工作区与 claude组 同步，claude组 负责 git 操作）；**评估意见必须落盘 `docs/catch-ball/discuss/`（讨论类）或 `scan/`（SCAN 类）·禁只回聊天文字**（RULES §5.1.1·2026-08-13 起强制）。请求文档第一步统一写「只读项目数据与代码·禁 git·评估意见落盘 docs/catch-ball/discuss/ 或 scan/」。
2. **claude组 先验后推**：发起/预检文档（草案）可 push（供评估方读 + 跨环境同步）；**实施代码须两组检查通过后才 push**（先验后推·`先讨论再实施`）。
3. 请求文档模板：`docs/catch-ball/_handoff/CB{NN}-{topic}预检*.md`（第一步读本地文件·第二步草案·第三步预检 N 问·第四步产 SCAN）。
4. **测试任务三组并行（2026-08-09 新规）**：测试负载重、单靠人眼测难以为继 → **claude组 拆解测试任务、针对性分配三组（claude组/Codex/glm组）同时进行**；claude组 分发前先确认各组平台 Harness 环境就绪（Python/Playwright/API Key/trace/端口隔离·三组并发 B3 需 `--port/--backend-port` 隔离 + sys.executable）；claude组 持续提出 CB 机制优化意见（工作坊式先进性/流畅性/科学性）。[[cb-distributed-testing]]
5. **组间交叉挑战（CB-22 教训·2026-08-09 采）**：方案收敛时**各组须对其他组方案至少提 1 条挑战或确认**（写入收敛模板）——本次零 LLM 失误的机制根因 = 收敛无交叉挑战（Codex 未质疑 glm 零 LLM·glm 未自问"全面性"·claude 独立收敛到错方案）。**三支柱检查入收敛清单**：每个方案收敛前过三支柱·标"动了哪支柱·哪支柱质量下限是否达标"·砍支柱 = 一票否决（Codex §4 机制 3 条）。
   - **三组环境就绪（08-09 自检）**：glm组 7/7 OK 全能力；Codex 5 OK + 2 WARN（SessionStart hook 已补 `.codex/hooks.json`·多模态 Key 缺失 → 多模态/OCR 类用例 Codex 不承接·claude组/glm 承接）。报告：`discuss/CB环境自检_回应_Codex-GPT5_2026-08-09.md` + `_handoff/CB环境自检_glm组_2026-08-09.md`
   - **session 标签纪律（glm 实测·08-09 采）**：`EMOTION_TRACE_SESSION` **仅 B3/e2e 浏览器用例需要带**（走真实问答链路 FC→工具→finalStep·产 trace）；**pytest 单测/静态核验不产 trace·无需带**（glm 实测带 session 跑单测·trace 查询返 0 行）——分配任务时标注测试类型决定是否带标签。

6. **用户沟通纪律（2026-08-18 用户反馈·全局生效）**：面向用户的决策说明必须按「非程序开发者」沟通——① 专业人员先系统讲解背景/选项/代价/推荐，不只抛结论；② 禁裸用内部编号（G10、B1、P3、B 变体、C11 等），首次必须用业务名称或「业务名称（内部编号：XXX）」；③ 决策问题要说明接受/不接受意味着什么、现在是否执行、时间与演示影响，并给推荐答案。技术细节放附录或链接。

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
