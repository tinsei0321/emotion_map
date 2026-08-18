# EMC × dsh 可行性深挖 · 独立回应 —— dsh组（2026-08-18）

> 回应方：dsh组（DeepSeek Harness 母框架侧技术事实方）。依据：启动包 + 台账 + R1/R9 本组回应 + 对当前 dsh checkout 的现场复核（`D:\Github\dsh` @ `f1e10a678e`，v0.1.0-rc.7）。零实施·零 git 写（本文件为唯一落盘）。
> **口径变更声明（重要）**：此前各组引用的 dsh checkout `D:\Github\dsh_test`（master@cafd4e6132，rc.5）**已不存在**（目录已移除；用户 `~/.dsh/` 下残留 `dsh-web.vbs.bak-dsh-test` 为迁移痕迹【已实测】）。当前 checkout 为 `D:\Github\dsh`，origin 指向用户自己的 Gitee 镜像（`gitee.com/tinsei0321/dsh_0816.git`），12,411 commits，**历史已被改写**（旧 commit `cafd4e6132` 不在任何可达历史中、克隆无 tag）。**R1 的「600 commit 内 16 个 `!:` breaking」计数在当前克隆无法复现（0 个 `!:`/BREAKING 标记）**——不是结论翻案，是证据更换：本次改用**发布节奏**作定量证据（见 §0.2），结论方向不变且更强。所有 dsh 侧断言均落到当前 checkout 的 file:line。

---

## 〇 一句话结论

**形态3 方向正确、MCP 载体唯一正确、B 变体实验保留正确——但三处必须修正：① 七工具缺「开卷定参」能力（list_data 不带 schema/CRS/样例，会把 R4 证明过的病灶原样带回 MCP 面）；② rag_query 裸 chunks 输出会让 CB-22「零 LLM 综合」教训在宿主侧重演，v1 必须内置 synthesize 选项；③ 「范式编码进 description 字符串」是形态3 最脆弱的支点，caliber 必须落到 output 字段而非只留在 description。** 最小正确切口 = EMC 侧一个体外只读 Python MCP 进程（契约剥壳直出）+ dsh 侧零代码（profile 注册 mcp-client 插件行）；dsh 不做任何 plugin/ConversationNode 工程；「场景 S 地图」以 render_spec JSON 文本化替代 client plugin。

---

## 〇.1 独立立场（先亮牌：作为 dsh 维护者，我会怎么推荐）

1. **我会推荐 EMC 做 MCP 工具面，且只推荐这个**——不是因为 dsh 好，是因为 MCP 是协议不是 dsh：押协议 = 押四宿主生态 + 绝缘于 dsh preview 节奏【已实测：README.md:9-11 明示 developer preview + 破坏性变更】；押 dsh plugin/ConversationNode = 押一个 6 天 10 个 rc 的供应链（§0.2）。
2. **我不会推荐 EMC 把「产品入口」押在 dsh 上，包括场景 S**——dsh Web 是给会改插件的开发者用的（文档主轴 user/develop），不是给规划师/住建局的产品壳。EMC 自控入口（薄壳 A 单轮 FC）必须保留，dsh 只是四宿主之一。形态3 的「入口可替换」如果变成「入口 = dsh」，就是换了种方式重演方案A 的绑定。
3. **「dsh 欢迎消费者不欢迎住户」依然是本组对 dsh 内部哲学的判断**【文档证实：根 AGENTS.md "Plugins, not loop changes"；R1 已引】。MCP 消费是一阶支持（mcp-client 是官方包），领域产品住进 plugin 不是 dsh 主张的典型用法。
4. **对形态3 框架本身，本组有真分歧（不是假分歧）**：形态3 把 EMC 的 Smart 两端（意图 + 表达）全部外包，只导出 Dumb 中间件——**RAG 三支柱（CB-22）在 MCP 面只剩 1.5 根**（检索在 EMC、知识库完备度靠 description、归纳靠宿主零引导）。这是框架级风险，不是排期问题（§四.4）。

---

## 〇.2 checkout 事实更新（先于一切评审的事实底座）

| 项 | 旧口径（R1/R9） | 当前实测（2026-08-18） | 判定 |
|---|---|---|---|
| checkout 路径 | `D:\Github\dsh_test` master@cafd4e6132 rc.5 | `D:\Github\dsh` @ `f1e10a678e` rc.7（2026-08-18 01:16 +0800） | 已迁移+升级 |
| breaking 定量 | 600 commit 内 16 个 `!:` | 当前克隆 0 个 `!:`/BREAKING（历史改写，不可复现） | **证据更换** |
| 版本节奏（替代证据） | 周级 | **发布日志实测：08-11 rc.2 → 08-13 单日 8 个（0.0.1-rc.3/4/5 + 0.1.0-rc.1/2/3/5/6）→ 08-17 rc.7；6 天 10 个 rc**（`git log --grep="release(dsh)"`） | 已实测·比旧口径更硬 |
| commit 量 | 30 天 ~9,500 | 30 天 9,196（`--since=2026-07-19`） | 已实测·同量级 |
| 审批第三态 | 「always-allow（session-wide grant）本月新合入」 | 当前 approval.md:46 仅 `'ask' | 'never'`；`allowed-once` 是唯一 grant（user-approval/index.d.ts:167） | **未复现·以当前为准** |

**审批语义的当前准确定义**（直接关系 C12-⑩ 与 B 变体）：`ApprovalPolicy = 'ask' | 'never'`，按会话经 `approval/policy` 会话日志事件覆盖、重放可重建（approval.md:33）；`'never'` 下所有 ask 确定性解析为 rejected、不派发任何 answerer（approval.md:42）；`'allowed-once'` 是唯一放行形态（index.d.ts:167）。**dsh 机制上不存在「会话级永远放行」**——所谓「会话级授权」只是把策略切到 'never'（全拒）或 'ask'（逐次问）。这使 C12-⑩「禁全 allow 默认」在 dsh 侧天然成立，但也意味着：**headless/ACP 场景下审批策略只能是「ask + 客户端自动应答 allowed-once（按白名单）」**，不存在「配置一把梭放行」的中间态。本会话即为实证：用户本次把 approval 策略从 ask 改为 never，机制与文档吻合【已实测·本会话运行于 dsh Web GUI】。

---

## 一 A 议程：独立裁定形态3（EMC 领域平台 × dsh 经 MCP 消费）

### 1.1 裁定：方向成立，但「成立」的范围比拍板包窄

本组独立复核后维持三组收敛结论：**形态3 作为终局方向成立**（R4/R5 证据链完整：NL 路由被通用范式支配、平台资产可复利、深挖路由不收敛）。但作为 dsh 侧，我要指出拍板包没有充分回答的三个脆弱假设——它们决定「形态3 是产品路线还是工作流路线」：

### 1.2 脆弱假设一（最脆弱）：宿主 LLM 消费工具面时「叙事不失真」

- 机制：MCP 工具面导出的是 Dumb 中间件；意图理解与结论表达都发生在宿主。R4 已证通用 harness 强于可验证操作、弱于叙事分析（私有口径分布外）。工具 description 的 `when/limits/output`（C11）能防「参数误用」，**防不住「语义误用」**：宿主 LLM 拿到 `zonal_stats` 的数值，完全可能把宏观聚合结论说成精确诊断（「这片区域满意度 63.2 分」vs 正确口径「宏观极性偏负、主题倾向治理×设施、供假设排序」）。
- 【推断·需实验证伪】纠偏率是形态3 的生死指标：若真实任务下宿主结论需人工纠偏 >50%，形态3 只剩工作流工具价值，产品入口价值归零。
- **修改建议**：C11 的 `caliber_ref` 从「description 里的出处指针」升级为**每个工具 output 的必带字段**（`{caliber: '宏观聚合'|'确定性组装'|..., ref: paradigm/kb/口径注册 id}`）。口径可辩护是 EMC 相对裸 geopandas 的唯一差异化，不能在协议面上丢。

### 1.3 脆弱假设二：「渲染资产能契约化且无双源」

- 现状方案：JS 令牌解析权威 + 双载防双源 + `resolved_by` 标注（R8）。dsh 侧复核：**双载只能防 EMC 内部双源，防不了「宿主自制渲染器」与「JS 权威」之间的第二份实现**——dsh Web 消费端（场景 S）没有 JS 解析器，v1 渲染承诺对 dsh 消费者兑现不了。
- **修改建议**：渲染 v1 就做「render_spec 文本化」——GeoJSON + 样式令牌 JSON（色带/拉伸参数/图例），任何宿主可自行画，渲染器保持「傻瓜化」（只映射令牌到视觉，不做语义）。这比「前端 loader + MCP render 工具」两步走更早兑现场景 S，且双源风险低（渲染器无逻辑、只有映射）。ConversationNode 内嵌地图 = 完整 client plugin 工程（§四.3），**在场景 S 真实需求出现前不做**。

### 1.4 脆弱假设三：「正道好走」是可持续的运营承诺，不是架构承诺

- 机制：形态3 把「正道好走」寄托在 G10 工具体验优于 bash 裸调。但 MCP 工具面的可用性依赖 EMC 侧持续供给（B1 usage 字段、G8b 动态 enum、C 线知识、契约演进）——**消费端（dsh 等四宿主）随时会来，资产供给是排期驱动的**。供给掉队的那一天，宿主自动回落 bash 考古（现状即降级路径，成本 0）。
- **修改建议**：「正道好走」指标化：G10 spike 验收必须含摩擦差量化（bash vs MCP 同任务：轮次/耗时/参数错误率/结果一致性）；**数据不好看就降级为「用户工作流工具」定位**，不进产品承诺。

### 1.5 形态3 与 dsh 的关系修正（本组独有视角）

形态3 对 dsh 的含义不是「dsh 消费 EMC」单向，而是**「EMC 平台资产 ↔ 通用 harness」双向对偶**：dsh 侧同样在沉淀平台资产（本会话所在的环境本身：profile/bundles/插件/会话持久化）。EMC 真正应该借鉴 dsh 的不是 harness 循环（R0-R1 已否），而是**平台化的纪律形态**：契约单一源（C8）、版本化与 deprecation（C9）、eval CI 化（C10）——这些在 dsh 里是「gen-*/verify-*」脚本群 + release 门（root package.json scripts 实测：gen-tool-catalog/verify-tool-catalog/gen-config-catalog/check:ci 等），EMC 的 C8-C10 与 dsh 工程实践同构。**形态3 的「平台宪法」不是新发明，是成熟工程惯例的本地化**——这降低而非提高 E4 的拍板风险。

---

## 二 B 议程：G10 v1 七工具评审（dsh 消费者视角）

### 2.1 七工具 vs 既有实现（本组快速核查，全部有真实 backing）

| 工具 | EMC 侧 backing（本次核查） | 判定 |
|---|---|---|
| rag_query | `api/aiqa_routes.py:112` post_rag_search（检索索引） | 存在·**需修正（§2.3-①）** |
| kb_facts | `aiqa_routes.py:31` get_wisdom / `ai_qa/wisdom.py:104` retrieve_wisdom | 存在·最稳 |
| list_data | 三源（geo_registry/presets/analysis 总账）+ B1 usage 过滤 | 存在·**需修正（§2.3-②）** |
| outlet_card | `aiqa_routes.py:92` post_outlet_card + `core/export.py` F_005 | 存在·确定性组装 |
| zonal_stats | `core/spatial_analysis.py:237` aggregate_by_polygons / :403 aggregate_by_boundary_id | 存在·**有 60s 超时风险（§2.3-③）** |
| buffer | `core/buffer_analysis.py:18` create_buffer | 存在·同上 |
| rank | zonal 派生排序 | 存在（派生）·独立成工具合理（减少宿主多步） |

### 2.2 总评：v1 六只读 + 一派生是「够用的起点」，但 dsh 消费者会立刻撞到三个坑

**够用的部分**：对 dsh 而言，六只读工具的 schema 兼容性无问题——`contracts_to_tools_schema()`（tool_contracts.py:473）产 OpenAI FC 包装，剥壳直出 MCP `inputSchema`（丢 `strict`、保 `additionalProperties:false`）【文档证实 + 本组核对：mcp-client 对 outputSchema 超词汇退化 JsonValue（mcp-client/README.md:117），故 outputSchema 以最小公共词汇书写即可四宿主全兼容】。

### 2.3 三个会逼 dsh 绕回 bash 的缺口（按严重度排序）

**① rag_query 裸 chunks = 把 CB-22 教训搬进 MCP 面【推断·高置信】**
- 机制：MCP 消费端不会自动执行 EMC 的「检索 → LLM 综合」范式（三支柱之一）。若 rag_query 返回原始 chunk 列表，宿主 LLM 拿到的就是 CB-22 明令禁止的「零 LLM 综合拼列表」的输入形态。**宿主侧的归纳是无引导的**——EMC 的 select_template/paradigm prompt 资产在 MCP 面不存在。
- 修正：rag_query v1 加 `synthesize: bool`（默认 true）——server 侧调 EMC 既有 `ai_qa/llm.py` 综合后输出「已综合答案 + 来源列表 + caliber 标注」。这不是给 server 加新推理（EMC 既有资产），是**把 Smart 表达端的一小块（RAG 综合）留在平台内**。代价：server 需要 DeepSeek key 配置；只读面不变。

**② list_data 不带 schema/CRS/样例 = 「闭卷定参」原样回归【推断·高置信】**
- 机制：R4 实证通用 harness 的优势 = 先读真实数据（列名/CRS/几何）再操作。若 list_data 只返回 dataset_id 枚举，dsh agent 填 `zonal_stats` 的边界/字段参数 = 猜，猜错 → 报错 → 重试，正是 R4 描述的被支配行为。**没有「开卷定参」，MCP 面相比 bash 考古的提升只剩 schema 校验**（当然这仍然有价值，但撑不起「主路前置」）。
- 修正：list_data 每个条目返回 `{dataset_id, 行数, schema(列名+类型), crs, 样例3行, 口径链接}`。这是 v1 内改动最小的结构性修正。

**③ zonal_stats/buffer 全量跑可能撞 dsh 侧 60s 默认超时【已实测 dsh 侧约束】**
- mcp-client `toolCallTimeoutMs` 默认 60000（README.md:46）。EMC 侧全量空间统计若超 60s，dsh 会 abort 调用。修正：v1 工具参数收敛为「dataset_id + 边界 id + 可选采样/限制参数」，并在 description 的 limits 段声明量级预期（C11 正好有这层）；超大任务留给 v2 `run_analysis`。

### 2.4 schema/output/权限的坑（dsh 侧逐条）

1. **outputSchema 词汇**：只用 string/number/boolean/array/object/enum/const/oneOf；超词汇 dsh 不校验（退化 JsonValue），等于防线白写【已实测 mcp-client/README.md:117】。
2. **参数不可改写**：dsh 的 `tools/pre-execute` 不能改写参数（tools.md:402「Arguments cannot be rewritten」）——EMC 的 `validate_tool_call`（tool_contracts.py:548）必须收「已校验」输入，host 侧修正参数的唯一方式 = 拒绝重试，这增加一轮往返；所以**参数默认值要给全**（`_derive_defaults` 已存在，tool_contracts.py:373，正好用上）。
3. **权限门位置**：mcp__* 工具注册在 ctx.tools 后，走与本地工具相同的 pre-execute/guard/审批管线【已实测 tools.md:172】——**dsh 的 ask 审批对 MCP 工具生效**。但 headless/ACP 无 UI answerer：approval 策略 ask 时无人应答 → unavailable → 调用失败【已实测 approval.md:33,42】。**因此 headless/ACP 场景必须显式配置**：policy=ask + 桥客户端自动应答白名单（B 变体场景），或 policy=never（EMC 工具全只读、不触发 ask 时无影响）。这是 dsh 侧第一坑，拍板包未列。
4. **工具面泄漏面**：ACP `session/new` 拒非空 mcpServers（acp/src/index.ts:544 源码级）→ G10 只能走 **profile 全局 MCP 配置**（mcp-client 插件行，进程级生效）【已实测：CLI 把 MCP 配置编译为 cordis 插件行，apps/cli/tests/memory-mcp-configs.spec.ts:87-92】。含义：**该 profile 下所有会话（含用户自己的交互会话）共享 EMC 工具面，无法按会话隔离**——权限扩散是机制性的，唯一防线 = server 侧只读 + dataset_id 白名单 + 纪律（R1 已定，本次复核确认无替代路径）。
5. **结果回传形态**：MCP resources 在 dsh 无消费者【已实测 mcp-client/README.md:113】→ 大结果（50 单元 × 20 字段统计表）只能内联 text 进上下文，**compaction 前常驻**。v1 工具输出必须带 `top_n`/`cells` 等体积控制 + 「结果引用」设计（返回摘要 + 可再查的引用 id），否则 dsh 会话上下文被 CSV 撑爆。

---

## 三 C 议程：dsh B 卷补齐（②-⑤）

### 3.1 ② 用户日常 dsh 配置面：profile / 审批 / compaction（本次实测交付）

**Profile 面**（用户实机 `~/.dsh/profiles/web/`【已实测】）：
- `package.json` 的 `dsh.profile.bundles` = 装配清单（当前：`@deepseek-ai/dsh-base` + `@deepseek-ai/dsh-web-app` + 三个本地插件 dsh-better-sidebar/dsh-review-skills/dsh-security-scan），由 `dsh plugin add` 管理；
- `cordis.patch.yml` = 每 profile 的 loader 覆盖层（当前含 security-scan 的 config 覆盖 + `@dsh-external/dsh-super-injector` 本地注入插件）；
- **MCP server 的注册位 = profile 级 mcp-client 插件行（bundles 或 patch），进程级全局生效**——这就是「profile 全局 MCP 配置」的确切含义【已实测 memory-mcp-configs.spec.ts 机制 + 本机 profile 无 MCP 实例（当前未注册任何 MCP server，G10 落地时是首次注册）】。

**审批面**：见 §0.2——per-session 策略（ask/never）、pre-execute waterfall、allowed-once 唯一放行、ACP request_permission 一次性机器应答。

**Compaction 面**（config-catalog.md:468-510【已实测】）：`thresholdRatio`(0.8) / `retainRatio`(0.16) 或 `retainTokens` / `summarizationProvider`+`summarizationModel`（默认继承会话目标模型） / `maxTokens`(8192) / `compactionRetries`(1) / `maxOverflowRetries`(1) / `modelPolicies` 精确覆盖表 / `auto`。对本专题的实质含义：**大工具结果在 compaction 前常驻上下文，但 compaction 是自动的、按模型窗口比例触发**——EMC 工具输出体积控制（§2.4-5）直接决定会话体验，无需用户干预配置。用户实机模型 = deepseek-official / deepseek-v4-flash / reasoningEffort max（`~/.dsh/settings.yaml`【已实测】）。

### 3.2 ③ render contract 与 ConversationNode 地图承载工程量

**render contract（EMC 侧）**：现有 hot_spot/terrain/buffer 输出已含 GeoJSON 形态，样式语义集中在 JS（computeStyle/terrainRampOf）——契约化工作 = 定义字段语义（极性/拉伸/色带枚举）+ 令牌解析副本，量级 0.5-1d【推断·基于 R8 三步估算，本组认可其量级】。**v1 形态建议直接是「GeoJSON + 样式令牌 JSON」文本契约**（§1.3），无 JS 消费者也能用。

**ConversationNode 地图（dsh 侧）**：`docs/cookbook/adding-a-conversation-node.md`（233 行教程）【已实测】——机制真实存在：业务事件族（可重放设计）+ React keyed renderer + client plugin 编入 Web bundle。**地图 viewer = 完整 client plugin 工程**：事件契约设计 + 图层渲染器 + Web bundle 重建 + 与 dsh 会话事件流对拍，且**只服务 dsh Web 单宿主**，其余三宿主零收益【推断·同 R1 §2.3.4 判定，当前 checkout 复核不改变量级判断】。**本组建议：不立项**；场景 S 的替代 = 薄壳 A 内嵌 MapLibre（EMC 自有资产直接复用）+ render_spec 文本化（任何宿主可画）。

### 3.3 ④ R1 结论在形态3 语境下重审

| R1 决策 | 重审结论 | 变化 |
|---|---|---|
| D1 否决方案A | **维持且更强** | E4 把「否决运行时寄生」升格为「停止自研入口智能」；breaking 证据更换为 6 天 10 rc 后，plugin 陪跑成本论证不降反升 |
| D2 立项 B | 维持 | G10 升主路；**新增约束**：60s 超时、输出体积、profile 全局配置的泄漏面（§2.3/2.4） |
| D3 MCP 唯一解 | **维持·本次复核再确认** | mcp-client/ACP/headless 三处源码级复核全过（§附录） |
| D4 dsh组 回归 | 维持 | 本回应即回归产出；B 卷②-⑤ 本次补齐 |

### 3.4 ⑤ 对形态3 框架本身的挑战（本组与收敛结论的真实分歧点）

1. **Smart/Dumb 分界在协议面上被重新切分**：EMC 内核的「聪明只在两端」在形态3 下变成「聪明全在宿主、平台只剩 Dumb」——但 RAG 综合（§2.3-①）、口径表达（§1.2）证明**有一小块 Smart 必须留在平台内**。形态3 的准确表述应是「平台保留最小 Smart（综合+口径标注），其余外包」，不是「全外包」。这是对拍板包文案的实质修正建议。
2. **三支柱的 MCP 投影**：CB-22 三支柱（本地知识库完备度 + EMC 架构 + LLM 归纳）在 MCP 消费下只有知识库支柱完整。C11 的 when/limits/output 是「架构支柱」的替代品，但**没有任何东西替代 LLM 归纳支柱**——除非 rag_query 带 synthesize（§2.3-①）。这是框架级缺口，不是描述文案问题。
3. **「平台宪法」与 dsh 工程实践同构**（§1.5）——降低 E4 风险，同时意味着 C8-C10 可以照抄成熟惯例，不需要发明。

---

## 四 D 议程：外挂大脑 B 变体深评

### 4.1 四项机制复核（本次全部重验，结论与 R9 一致，附一处新事实）

| 机制 | 复核结果（当前 checkout） |
|---|---|
| ACP | 方法表完整（session/new\|prompt\|cancel\|update\|request_permission，README.md:24-30）；`session/new` 拒非空 mcpServers（**src/index.ts:544 源码级**）；fresh-only（README.md:78，load/resume/fork 不支持）；`demo:acp` 可跑组合存在（root package.json scripts【已实测】） |
| headless | 不挂 Host/HTTP/Web/browser、不开监听端口（bundle/headless/README.md:5,7）【已实测复核】 |
| session 复用 | ACP 面无；复用 = `sessions.create(id,{seed})` + `followup()` 插件内自组（extension-cookbook.md:127）【文档证实】 |
| request_permission | 一次性 allow/reject、客户端可自动应答（README.md:30）【文档证实】 |

**新事实（本次）**：R1 旧口径「always-allow 会话级授权」在当前 checkout 不存在（§0.2）——**B 变体的审批语义比 R9 记录的更严格**：不存在「配置一次全放行」，只有「ask + 自动应答器按白名单逐次 allowed-once」。这正好落 C12-⑩（禁全 allow 默认），但意味着**桥客户端必须实现真正的策略判断**（白名单匹配 + 拒绝回执），不是简单 allowAll。这提高了「成品评审」的审查权重：朋友成品的审批策略是评审重点之一。

### 4.2 profile 全局 MCP 的可行性（真实约束）

- 可行，但形态 = **进程级全局工具面**（§2.4-4）：EMC G10 工具对该 profile 所有会话可见。对「用户个人工作流」无害（工具全只读）；对「产品薄壳」需要接受「无法按会话隔离工具」的事实。
- 工具泄漏的实质风险：**不是 EMC 工具泄漏（只读+白名单），而是该 profile 内其他全局工具的暴露面反过来扩大**——B 变体把 dsh 大脑暴露给 Codex/薄壳时，dsh 会话里配置的所有工具（bash/shell/fs 等）都在大脑可及范围内。**B 变体的安全边界 = profile 的完整工具面，不是 EMC 工具面**。因此 B 变体若转正，必须用**专用瘦 profile**（只挂 base + EMC MCP），不挂用户日常 profile——这是 R9 未明确、本次补充的硬约束【推断·基于 profile 全局配置机制】。

### 4.3 朋友成品两条路的评估（成品未知时）

**路线甲：成品评审**（朋友成品存在时）——评审清单（对照本组机制 + C12）：
1. 是否 ACP 系还是自写 HTTP（自写 HTTP = 需要重新审查鉴权/审计，风险高一档）；
2. 审批策略实现（§4.1 新事实：是否白名单自动应答，还是简单放行）；
3. 守卫七条逐条核验；4. inject 权限声明（未声明 fs/tools 就拿不到【R9 已述·文档证实】）；5. 版本锁定方式；6. send 审计落点（session log 单一事实源）。

**路线乙：ACP 底新写**（无成品时）——**最小 demo（50 行级）设计**：
- 组件：子进程拉起 `demo:acp` 组合（dsh 自带可跑组合，无需自建 profile）→ stdio JSON-RPC 客户端（dsh 自带 `@deepseek-ai/dsh-subagent-acp` 作参考实现）→ `session/new` → `session/prompt` → 收 `session/update` 流 → `request_permission` 白名单自动应答 → `session/cancel` 兜底。
- 验收标准（四条件全过才算环路通）：① fresh 会话建起并完成一次真实任务（如「读某目录文件列表并总结」）；② 权限请求按白名单自动应答，非白名单拒绝且任务不假成功；③ 取消路径：prompt 后立即 cancel，会话无孤儿 agent（ACP README.md:38 生命周期保证）；④ 全链路日志可在 dsh session log 中溯源（Model-visible means logged）。
- 量级：1-2d【推断·R9 已估，本次复核 demo:acp 现成，量级可信】。

### 4.4 本组对 B 变体的独立判断

**「实验保留」仍偏乐观，不是过度保守**（答硬问题 3）：保留实验本身无成本，但注意转正五条件里**没有一条是 EMC 侧可控的**——A 稳定（EMC 自己）、dsh 脱 preview（外部）、自由任务需求实测（用户行为）、端口契约（EMC 自己）、真实任务验收（EMC 自己）——5 条里 2 条外部、1 条行为观察。**B 变体的真正决定变量只有「自由任务需求是否实测出现」一条**，其余都是陪跑条款。建议：观察成本降到 0——不专门维护、不专门排期；「用户工作流工具」形态（ACP 遥控 dsh 干真实任务）本身就是观察窗口，需求出现时自然转正，不出现则永远实验。

---

## 五 E 议程：生命周期与风险（dsh 侧逐项）

| 风险 | dsh 侧事实 | 对策 |
|---|---|---|
| **preview breaking** | 6 天 10 rc（§0.2）；README 明示破坏性变更 | 锁版本（profile bundles 用 tarball/junction 锁定，升级=显式动作）；**MCP 协议层完全绝缘**（dsh 侧变化只在 mcp-client 包内消化【已实测 README.md:69-71 重连/重发现机制】） |
| **版本锁定** | profile bundles 机制天然支持锁定（`dsh plugin add` 装固定 tarball） | EMC server 依赖仅 `mcp` + EMC 既有包，无 dsh 依赖——**EMC 侧零锁定负担** |
| **适配器层** | 大脑端口契约（start/send/status/stop）由 EMC 定义、dsh 作第一驱动【R9 已定】 | 维持；breaking 隔离在适配器，不进 EMC 产品面 |
| **失败恢复** | mcp-client 自动重连：指数退避 + 预算制（maxAttempts=10，崩溃循环最终卸载工具、日志可见）【已实测 README.md:48-51,69-71】 | EMC server 崩溃 → dsh 自动重启重发现；EMC 侧无需实现重连 |
| **状态同步** | 会话持久化在 dsh 侧（session-persistence-jsonl/sqlite 包存在【已实测】）；EMC 工具面设计为无状态 | 无跨侧状态同步问题；B 变体的大脑会话状态天然在 dsh |
| **审计** | session log = 单一事实源（Model-visible means logged）；MCP 工具调用入会话日志 | EMC 侧零额外工作；薄壳 trace 补载荷摘要即可【R9 已述】 |
| **PII** | dsh 无附加脱敏机制——工具输出原样进上下文 | **铁律 7 必须在 server 侧做绝**（R1 已定，本次复核无 dsh 侧替代）；rag_query 的 synthesize 路径尤其要过脱敏函数 |
| **权限扩散** | profile 全局 MCP = 进程级工具面，无法按会话隔离【已实测机制】 | 工具面只读 + dataset_id 白名单 + server 侧纪律 = 唯一防线；B 变体转正用专用瘦 profile（§4.2） |
| **最小权限** | plugin inject 声明机制（不声明 fs/tools 拿不到）【R9 已述·文档证实】 | EMC 侧不写 dsh plugin 即不适用；若未来写 client plugin，评审查 inject 列表 |
| **降级路径** | MCP 不可达 → 工具消失/调用失败 → 宿主回落 bash（现状即降级路径，成本 0）；B 断 → A 直连（R9 已定，维持） | 显式声明：**v1 全只读，最坏故障 = 工具不可用，无数据面事故面** |

**最坏故障与爆炸半径（答硬问题 5）**：v1 形态（六只读 + 派生）下最坏故障 = MCP server 崩溃循环（mcp-client 预算耗尽 → 工具卸载）或 60s 超时 abort——爆炸半径 = server 进程 + 其可读文件，**无写路径、无数据损坏、无 PII 面**。真正的红线在 v2：若未来加 `run_analysis` 写路径（生成 CSV/图件），爆炸半径扩展到 EMC 输出目录 + 未脱敏分析结果——**v2 立项前必须锁死「server 永远无权写 raw/、输出永远过脱敏」**，这是 R1「run_analysis 降 v2」决策的正确性所在，本次复核支持维持。显式降级：工具面失败 → 宿主 fallback bash（现状）；薄壳 B 断 → A 直连 + 显式错误 + 中间产物保留（R9 已定）。

---

## 六 F 议程：本组推荐路线与排序

| 序 | 路线 | 收益 | 成本 | 风险 | 可逆性 | 转正/放弃判据 |
|---|---|---|---|---|---|---|
| **1** | **G10 MCP 工具面（v1 修正版：六只读 + inspect 化 list_data + rag synthesize）** | 四宿主即插即用（dsh 零代码）；schema 校验/脱敏纪律/dataset_id 白名单落地；摩擦差可测 | <1d spike + 契约演进期维护（G8 后趋零） | 低（体外进程、只读、可随时停） | **完全可逆**（进程级，EMC 本体零改动） | 转正：摩擦差实验显著优于 bash（轮次节省 ≥30%）；放弃：数据不好看 → 降级为用户工作流工具（定位变化，不删除） |
| **2** | **ACP 外挂大脑最小实验（用户工作流形态，零 EMC 工程）** | 以零成本证伪「B 变体是否有用」；朋友成品评审的前置参照 | 0.5-1d（dsh 侧现成 demo:acp + subagent-acp） | 低 | 完全可逆 | 转正：自由任务需求实测出现 + 四条件验收（§4.3）；放弃：两周无真实使用 → 关闭观察项 |
| **3** | **渲染 API（render_spec 文本化 v1）** | 解锁地图/样式资产给任意宿主；薄壳 A 与场景 S 共同地基 | 0.5-1d（比 R8 三步方案更早兑现场景 S） | 中（双源，但渲染器傻瓜化后可控） | 可逆（纯新增资产） | 转正：薄壳 A 开工前；放弃：无外部消费者出现则与薄壳 A 绑定走 |
| **4** | **薄壳 A（单轮 FC 消费型入口）** | EMC 自控产品入口，不押任何宿主 | 2d（三前提：G10 已出、坚持单轮、Windows stdio 已证） | 低 | 可逆 | 转正：E4 拍板后即排期；放弃：若摩擦差实验证明宿主入口已足够 → 薄壳 A 可再降级为演示壳 |
| **5** | **场景 S（dsh Web 消费）** | 非开发者浏览器入口 | dsh 侧零代码（MCP）；地图呈现等 render_spec | 低 | 可逆 | 转正：合作方真实使用需求出现；放弃：无需求则永远后置 |
| **6** | **dsh client plugin（ConversationNode 地图）/ 深嵌 Web Host** | dsh 独有沉浸式地图体验 | 完整 client plugin 工程（数倍于 MCP server）+ 单宿主 + breaking 陪跑 | 高 | 不可逆倾向（工程沉没） | **不立项**；除非场景 S 需求 + dsh 脱 preview 双条件同时出现 |
| **7** | **整体寄生（方案A）/ 路由壳继续演进** | 无 | — | — | — | **维持三组否决**；本组无新事实 |

**一句话排序**：1 → 2 并行先做（都是 <1d 且互相独立），3 → 4 随 E4 排期，5 后置，6/7 不做。

---

## 七 硬问题直答

**1. 如果你是 dsh 维护者，会不会推荐 EMC 把产品入口押在这条链路上？**
不会押「dsh」，会押「MCP」。分两层：协议级（MCP 工具面）是**唯一应该押的**——它是生态不是供应商，dsh 只是生态里工具最齐全的消费者之一；入口级（产品入口 = 某个宿主）**不应该押**——EMC 自控入口（薄壳 A）必须保留，dsh 场景 S 只能作为加分项。把「入口 = dsh」就是换了包装的方案A 绑定。【立场陈述】

**2. 形态3 的哪个核心假设最容易被真实任务证伪？**
「宿主消费 EMC 工具面时叙事不失真」（§1.2）。证伪实验极便宜：选一条真实叙事任务（片区主题倾向 + 结论口径），dsh 走 G10 跑一遍，统计结论纠偏率。其次候选：「正道好走」（摩擦差量化）。【推断·实验可证】

**3. B 变体实验保留是过度保守还是仍过度乐观？**
仍偏乐观（§4.4）：转正五条件里 3 条是陪跑，真正决定变量只有「自由任务需求实测」。建议观察成本降为 0（用户工作流工具形态即观察窗口），不专门维护。【立场陈述】

**4. 最小一天内能完成的证伪实验是什么？**
**双路径摩擦差实验**（G10 写完 server 后当天做）：同一条真实 CB 空间任务（如「12345 数据某片区 zonal 统计 + 排序 + 出结论」），dsh 会话 A 走 bash 考古（现状）、会话 B 走 MCP；记录轮次/耗时/参数错误数/结果一致性/上下文占用。**判定线：B 比 A 轮次节省 <30% → G10 定位从主路降为用户工作流工具**。若 G10 还没写，等价实验 = 纸面走查（启动包 A 议程已建议），但真实双路径是唯一算数的。【实验设计】

**5. 最坏故障是什么，爆炸半径多大，如何显式降级？**
v1 最坏 = server 崩溃循环（工具卸载）或 60s 超时；爆炸半径 = server 进程内，无写路径、无 PII 面（§五）。v2 若加写路径，爆炸半径扩展至输出目录——**红线：server 永无权写 raw/、输出永过脱敏**。降级链：工具不可达 → 宿主回落 bash（现状即降级路径）→ B 断 → A 直连 + 显式错误 + 中间产物保留。【已实测机制 + 推断】

**6. EMC 现在最不应该做什么？**
① 最不该：在 E4 未拍前继续投 NL 路由/意图调优（用户 R6 已裁定死路，任何「再调一版」都是沉没）；② 不该：为 dsh 单宿主做任何 client plugin/ConversationNode 工程；③ 不该：让 MCP server 内嵌 LLM 推理做「聪明工具」（违反 dumb tool 铁律，且 C11 会挡住裸函数的同时也该挡住聪明函数）；④ 不该：写第二份 schema（C8）；⑤ 不该：把 v2 写路径（run_analysis）提前进 v1。【立场陈述】

---

## 八 最小实验设计汇总（一天级）

| 实验 | 前置 | 时长 | 判定线 |
|---|---|---|---|
| **E1 双路径摩擦差**（§七-4） | G10 server 已产出 | 0.5d | B 轮次节省 <30% → 降级定位 |
| **E2 ACP 环路 demo**（§4.3） | dsh 现成 demo:acp | 0.5-1d | 四条件验收（建会话/白名单审批/取消无孤儿/日志溯源） |
| **E3 叙事纠偏率**（§七-2） | 可用 E1 同场做 | 0.5d | 纠偏率 >50% → 形态3 入口价值存疑，caliber 落 output 字段 |
| **E4 render_spec 三图层试抽**（启动包 C 议程） | 无 | 0.5d | 热力/缓冲/分区三类能否被外部消费者理解（含无 JS 消费者） |

E1+E3 可并场：一条真实任务同时记录摩擦差与纠偏率。E2 独立零依赖。E4 纸面级。

---

## 九 待用户问题

1. **朋友成品是否存在**（一句话分流「评审」/「ACP 底新写」，R9 遗留，本组再问一次）。
2. **E4 拍板 + 排期确认**（拍板包三键；本组支持拍，但建议把 §1.2 的 caliber 落 output 字段并入 C11 条款）。
3. **dsh B 卷是否收**（本次已交付②-⑤；若收，建议连同本回应一并归档）。
4. **摩擦差判定线是否接受**（轮次节省 ≥30% 为转正线——需要用户认可这个量级，因为它是 G10 定位的裁判）。
5. **瘦 profile 策略是否接受**（B 变体若转正，用专用瘦 profile 承载大脑——涉及用户对「多 profile 管理」的接受度）。

---

## 附录：证据索引（本次复核 file:line）

**dsh 侧（`D:\Github\dsh` @ f1e10a678e，rc.7）**：
- README.md:9-11 — developer preview + 「THERE WILL BE COMPATIBILITY-BREAKING CHANGES」
- `git log --grep="release(dsh)"` — 08-11 rc.2 → 08-13 单日 7 个 → 08-17 rc.7，6 天 10 rc【实测】
- packages/mcp/mcp-client/README.md:5（命名）·:46（toolCallTimeoutMs 60s）·:48-51（重连预算）·:69-71（重连行为）·:113（tools-only）·:117（outputSchema 退化）
- packages/acp/acp/README.md:24-30（方法表）·:26（mcpServers 空才接受）·:30（request_permission）·:78（fresh-only）；packages/acp/acp/src/index.ts:544（源码级拒非空 mcpServers）
- packages/bundle/headless/README.md:5,7（无 Host/无监听端口）·:19（一次性任务）
- docs/subsystems/approval.md:33,42,46（ask/never + 会话级覆盖 + never 全拒）；packages/interaction/user-approval/index.d.ts:167（allowed-once 唯一放行）
- docs/subsystems/tools.md:172（pre-execute→guard→execute→post-execute→result）·:402（参数不可改写）
- docs/config-catalog.md:468-510（compaction 配置面）
- docs/cookbook/adding-a-conversation-node.md（ConversationNode 教程 233 行）；docs/cookbook/extension-cookbook.md:127（sessions.create+followup）
- apps/cli/tests/memory-mcp-configs.spec.ts:87-92（CLI 编译 MCP 配置为插件行）
- `~/.dsh/profiles/web/package.json` + `cordis.patch.yml`（bundles/patch 机制实机样例）；`~/.dsh/settings.yaml`（deepseek-v4-flash）
- root package.json scripts（demo:acp / subagent-acp 包 / gen-verify 工具群）

**EMC 侧（`D:\Github\emotion_map`，快速核查）**：
- ai_qa/tool_contracts.py:473（contracts_to_tools_schema·FC 包装）·:548（validate_tool_call）·:373（_derive_defaults）
- api/aiqa_routes.py:31（get_wisdom→kb_facts 底）·:92（post_outlet_card）·:112（post_rag_search→rag_query 底）
- core/spatial_analysis.py:237/:403（zonal 聚合）·:32（hot_spot）·:484/:806/:941（网格/地形）；core/buffer_analysis.py:18（create_buffer）

> dsh组 · 2026-08-18 · 零实施 · 未 git 写（本文件为唯一落盘）。所有「已实测」均于本会话内对当前 checkout 复核。
