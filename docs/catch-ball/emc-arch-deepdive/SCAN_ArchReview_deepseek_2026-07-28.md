# v2 改良混合架构 — 架构评审报告

> **评审方**：DeepSeek（第三方 LLM·v2 设计参与者）  
> **评审日期**：2026-07-28  
> **评审视角**：「Smart Agent, Dumb Tool」+「高内聚、低耦合」  
> **评审性质**：自我评审——包括对我自己设计的批判  
> **诚实声明**：本报告不附和 v2 设计，逐一指出设计缺陷和耦合风险

---

## 一、总体评分

| 维度 | 评分 | 说明 |
|------|:---:|------|
| Smart Agent / Dumb Tool 合规 | ⚠️ 7/10 | 大方向正确，但有 2 处违反铁律 |
| 高内聚 | ⚠️ 6/10 | 模块一内聚不足，模块六边界模糊 |
| 低耦合 | ⚠️ 6/10 | 3 处隐藏耦合点 |
| 链路连通性 | ✅ 8/10 | 数据流清晰，但有 1 处断裂风险 |
| 代码可落地性 | ⚠️ 7/10 | 多数可行，2 处实现风险高 |
| **整体** | **⚠️ 7/10** | 方向对，细节有坑 |

---

## 二、Smart Agent / Dumb Tool 合规审查

### 铁律 1：Tool 越 dumb 越好——单一职责 + 参数契约 + 纯执行 + 不内嵌 LLM

| 审查项 | 状态 | 说明 |
|------|:---:|------|
| 工具不内嵌 LLM | ✅ | generate*ForAI 全部纯执行 |
| 参数契约完整 | ✅ | 契约 Schema + strict 强制 |
| 单一职责 | ✅ | 每个工具一个分析出口 |

**合规。**

### 铁律 2：Agent 聪明只在两端——意图理解（入口）+ 结果输出（出口）

| 审查项 | 状态 | 说明 |
|------|:---:|------|
| 入口端 LLM 做意图理解 | ✅ | function calling = 意图理解 |
| 出口端 LLM 做结果呈现 | ✅ | finalStep = 结果输出 |
| **中间执行无 LLM** | ⚠️ | **CPD 点击执行时不经 LLM——正确。但 finalStep 仍是一次 LLM 调用** |

**问题**：finalStep 是第二次 LLM 调用。按铁律 2，中间不应有 LLM。但 finalStep 做的是「observation → 用户可读文本」的翻译，属于出口端——**勉强合规**，但增加了延迟。

**严重度**：低——finalStep prompt 已瘦到 0.6-1.3KB，耗时 3-5s 可接受。

### 铁律 3：编排器确定性——协调是机械的，不调 LLM

| 审查项 | 状态 | 说明 |
|------|:---:|------|
| 编排器不调 LLM | ✅ | JSON.parse + TOOLS[name](params) |
| 编排器不做推理 | ✅ | 直接派发 tool_calls |

**合规。**

### 铁律 4：计划-执行分离

| 审查项 | 状态 | 说明 |
|------|:---:|------|
| 计划阶段产意图 | ✅ | function calling 产出 tool_calls + plans[] |
| 执行阶段按计划跑 | ✅ | 编排器机械派发 |
| **同类型任务不重复推理** | ⚠️ | **CPD 点击执行 rank=2 时不重新推理——正确。但 plans[] 跨轮复用的「数据变化检测」机制未明确定义** |

**问题**：文档说「图层数变/字段角色变/用户主动要求重新分析 → 清空 plans[]」，但**谁检测数据变化？** 0LLM？编排器？CPD？这是一个**未分配的职责**。

**严重度**：中——影响多轮对话的正确性。

### 铁律审查结论

| 铁律 | 合规 | 问题 |
|:---:|:---:|------|
| 1 | ✅ | — |
| 2 | ⚠️ | finalStep 第二次 LLM（勉强合规） |
| 3 | ✅ | — |
| 4 | ⚠️ | 数据变化检测职责未分配 |

---

## 三、高内聚审查

### 模块一：Diagnose Agent

**内聚度**：⚠️ 中等

| 组件 | 职责 | 内聚问题 |
|------|------|------|
| 0LLM 字段识别 | 字段→角色 + tools_hint | ✅ 内聚 |
| 0LLM 接地上下文 | 图层元数据 | ✅ 内聚 |
| LLM function calling | 选工具 + 填参数 + 产 plans[] | ⚠️ **一个 LLM 调用做了 3 件事** |

**问题**：function calling 的 LLM 同时产出 `tool_calls`（执行指令）和 `content: plans[]`（CPD 素材）。这两个输出的**消费者不同**（编排器 vs CPD），但**生产者相同**（同一次 LLM 调用）。

这不违反低耦合（消费者隔离），但违反**接口隔离原则**——编排器只需要 tool_calls，却被强制接收整个响应（含 plans[]）。CPD 只需要 plans[]，却被强制等待 tool_calls 执行完。

**严重度**：低——实践中不是问题（JSON 解析很快），但架构上不干净。

### 模块六：Prompt Engineering

**内聚度**：⚠️ 低

| 组件 | 职责 | 内聚问题 |
|------|------|------|
| tool_contracts.py | 工具参数定义 | ✅ |
| contracts_to_tools_schema() | 派生契约 Schema | ✅ |
| 旧 diagnose prompt 删除 | 清理 | ⚠️ 过渡期保留 paradigm.py / SKILL_DEFS |
| fallback prompt | function calling 失败兜底 | ⚠️ **和契约 Schema 是两套不同的工具描述** |

**问题**：fallback prompt 中的工具描述和契约 Schema 中的工具描述**可能漂移**——开发者改了 contracts 但忘了同步 fallback prompt 的手写描述。这又回到了 v1 的「多处手写」问题。

**严重度**：中——fallback 是低频路径，但漂移时会导致 fallback 模式选错工具。

### 模块五：Review + Revise → 质量防线

**内聚度**：✅ 高

8 条规则 + _verifyClaims + 降级渲染，全部纯代码，职责单一。

**无问题。**

---

## 四、低耦合审查

### 耦合点 1：契约 Schema 是「硬依赖中心」

```
tool_contracts.py
  ├─→ 契约 Schema → function calling（模块一）
  ├─→ 旧 paradigm.py（模块六·过渡保留）
  ├─→ 旧 SKILL_DEFS（模块六·过渡保留）
  └─→ validate_skill_params.py（CI 校验）
```

**问题**：contracts 是全系统的硬依赖。如果 contracts 定义有误（如 enum 漏了一个值），**所有下游都出错**。

**缓解**：CI 校验脚本（validate_skill_params.py）可以检测。但当前是「镜像+校验」模式，不是「派生」模式——仍有漂移风险。

**严重度**：中——单点故障，但有校验兜底。

### 耦合点 2：plans[] 格式跨模块契约

```
LLM 产出 plans[] → CPD 消费 → 编排器执行（点击 CPD 选项时）
```

**问题**：plans[] 的格式 `{rank, label, tool, params, confidence, rationale}` 是一个**跨 3 个模块的隐式接口契约**。没有 TypeScript 接口定义或 JSON Schema 约束——如果 LLM 产出格式漂移（如 rank 从数字变成字符串），CPD 和编排器都会出错。

**严重度**：中——function calling 的 content 字段不受 strict 约束（strict 只管 tool_calls），plans[] 是自由 JSON。

**建议**：给 plans[] 也加一层代码校验——解析 content JSON 后验证字段类型。

### 耦合点 3：0LLM tools_hint 和 LLM 的隐式协议

```
0LLM 产出 tools_hint → 注入 function calling 的 tools 参数
```

**问题**：0LLM 必须保证 tools_hint 中的工具名和 contracts 中的工具名完全一致。如果 0LLM 输出 `density` 但 contracts 中是 `density_analysis`，function calling 找不到匹配的 schema。

**严重度**：低——0LLM 的 FIELD_TO_TOOLS / KEYWORD_TO_TOOLS 映射表是硬编码，和 contracts 同源维护。

---

## 五、链路连通性审查

### 主链路（正常路径）

```
用户 NL → 0LLM → LLM function calling → 编排器 → 工具执行 → finalStep → 质量防线 → 渲染
```

| 环节 | 连通性 | 风险 |
|:---:|:---:|------|
| 0LLM → LLM | ✅ | — |
| LLM → 编排器 | ✅ | tool_calls 解析 |
| 编排器 → 工具 | ✅ | TOOLS[name] 查找 |
| 工具 → finalStep | ✅ | observation 传递 |
| finalStep → 质量防线 | ✅ | 规则检查 |
| **质量防线 → 渲染** | ✅ | — |

**主链路完整。**

### CPD 链路（多轮引导）

```
finalStep → CPD 展示 plans[] → 用户点击 → 编排器执行 → finalStep → CPD 更新
```

| 环节 | 连通性 | 风险 |
|:---:|:---:|------|
| finalStep → CPD | ⚠️ | **plans[] 从 LLM content 传到 finalStep 再传到 CPD——传递路径长** |
| CPD → 编排器 | ✅ | 点击触发执行 |
| 编排器 → finalStep | ✅ | 同主链路 |
| **CPD 更新** | ⚠️ | **已执行选项移除逻辑——谁来维护 plans[] 的 executed 状态？** |

**问题 1**：plans[] 从 LLM 响应的 content 字段解析出来后，需要传给 finalStep（生成追问胶囊）和 CPD（展示选项）。**传递机制未明确定义**——是存在全局变量？还是通过事件传递？还是通过 turnHistory？

**问题 2**：用户点击 CPD 选项后，该 plan 标记为 executed。**谁维护这个状态？** CPD 自己？还是 turnHistory？如果是 CPD 自己，页面刷新后状态丢失。

**严重度**：中——影响多轮引导的可靠性。

### fallback 链路（function calling 失败）

```
LLM function calling 失败 → fallback prompt → LLM 输出 JSON → 代码解析 → 编排器
```

| 环节 | 连通性 | 风险 |
|:---:|:---:|------|
| 失败检测 | ⚠️ | **如何判断 function calling「失败」？空 tool_calls？API 报错？超时？** |
| fallback prompt → LLM | ✅ | — |
| **LLM JSON → 代码解析** | ⚠️ | **自由 JSON 不受 strict 约束——解析失败风险** |

**问题**：fallback 路径的质量明显低于主路径。LLM 在 prompt 模式下可能产出格式错误的 JSON，或选错工具（无 strict schema 约束）。但这是兜底——可接受质量降级。

**严重度**：低——罕见路径。

---

## 六、代码可落地性审查

### 可直接落地的

| 组件 | 可行性 | 说明 |
|------|:---:|------|
| contracts_to_tools_schema() | ✅ | 标准 Python → JSON 转换 |
| 编排器消费 tool_calls | ✅ | JSON.parse + TOOLS[name] |
| 质量防线 8 条规则 | ✅ | 已实现 |
| finalStep 轻 prompt | ✅ | 已实现 |
| 0LLM tools_hint | ✅ | 硬编码映射表 |

### 实现风险高的

| 组件 | 风险 | 说明 |
|------|:---:|------|
| **DeepSeek V4 function calling 稳定性** | ⚠️ 高 | V3 时代有空响应/循环调用报告。V4 需实测。如果不稳定，整个 v2 架构的基础就不稳 |
| **LLM content 字段产出 plans[]** | ⚠️ 中 | LLM 需要在 function calling 响应中同时输出 tool_calls 和 content JSON。非标准用法——需验证 DeepSeek V4 是否支持 content + tool_calls 并存 |
| **plans[] 跨模块传递** | ⚠️ 中 | 传递机制未定义 |
| **数据变化检测** | ⚠️ 中 | 职责未分配 |

---

## 七、发现的设计缺陷（4 个）

### 缺陷 1：content + tool_calls 并存的假设未验证

**问题**：v2 假设 DeepSeek V4 function calling 响应中同时包含 `content`（plans[] JSON）和 `tool_calls`（执行指令）。这是**非标准用法**——标准 function calling 响应中，LLM 要么输出 tool_calls，要么输出 content，通常不同时。

**如果 DeepSeek V4 不支持并存**，v2 的 plans[] 产出机制就失效——CPD 无素材。

**缓解**：实测 DeepSeek V4。如果不支持，改用「两次 function call」——第一个 tool_call 是 `submit_plans`（返回 plans[]），第二个是实际工具。但这增加了一次调用。

### 缺陷 2：数据变化检测职责真空

**问题**：文档说「图层数变/字段角色变 → 清空 plans[]」，但没说**谁检测**。

| 候选 | 适合？ | 理由 |
|------|:---:|------|
| 0LLM | ⚠️ | 0LLM 每次都跑——但它不知道上一轮的 plans[] |
| 编排器 | ❌ | 编排器不跨轮 |
| CPD | ✅ | CPD 持有 plans[]·最适合检测变化 |
| turnHistory | ⚠️ | 存储介质·非检测者 |

**建议**：CPD 在每次用户操作前对比当前图层状态和上一轮的图层状态——变化则清空 plans[] 并通知用户「数据已变化·建议重新分析」。

### 缺陷 3：fallback prompt 与契约 Schema 的双重维护

**问题**：fallback prompt 中的工具描述是手写的，和 contracts 中的定义可能漂移。

**建议**：fallback prompt 也从 contracts 派生——用 `contracts_to_text()` 生成纯文本工具列表，注入 fallback prompt。

### 缺陷 4：0LLM tools_hint 可能误导 LLM

**问题**：tools_hint 注入完整 schema 的工具子集（2-4 个），tools_fallback 在 system prompt 提及其他工具。但如果 LLM 想用 fallback 中的工具，它**无法通过 function calling 调用**（因为该工具的 schema 不在 tools 参数中）。

**现状**：LLM 只能在 content 中说「我想用 clip」，然后代码解析后重新走一轮 function calling（把 clip 加入 tools_hint）。这是**额外的一轮交互**——增加延迟。

**严重度**：中——罕见场景（0LLM 的 tools_hint 覆盖率应该 >90%），但发生时用户体验差。

---

## 八、和业界对标的差距

| 业界做法（kepler.gl） | v2 | 差距 |
|------|------|:---:|
| 用户确认参数后执行 | 自动执行 | ⚠️ 无确认步骤 |
| 全部工具 schema 注入 | tools_hint 子集 + fallback | ⚠️ 13 个工具不多·可全注入 |
| LLM 只做工具选择 | LLM 选工具+填参数+产 plans[] | ⚠️ 多了 plans[] 产出 |

### 关键反思：tools_hint 是否必要？

kepler.gl 把**全部工具 schema** 注入 function calling——不做子集选择。我们的工具只有 13 个，完整 schema 大约 10-15KB。

**如果全注入**：
- 0LLM 不需要做 tools_hint（简化模块九）
- LLM 自己从 13 个中选（无漏选风险）
- prompt 增大 ~10KB（prefill 多 3-5s）
- 但省了 0LLM 的复杂度和 tools_hint/fallback 双重机制

**tradeoff**：13 个工具的完整 schema（~15KB·prefill ~5s）vs tools_hint 子集（~5KB·prefill ~2s）+ fallback 复杂度。

**我的修正建议**：如果 13 个工具完整 schema 的 prefill 在可接受范围（<5s），**全注入比 tools_hint 子集更简单、更可靠**。0LLM 只做接地上下文，不做工具筛选。

---

## 九、改进建议汇总

| # | 缺陷 | 改进 | 优先级 | 状态 |
|:---:|------|------|:---:|:---:|
| 1 | content + tool_calls 并存未验证 | **实测 DeepSeek V4** | P0 | ✅ 已验证·支持并存 |
| 2 | 数据变化检测职责真空 | **分配给 harness**（D065） | P1 | ✅ 已决议 |
| 3 | fallback prompt 双重维护 | **fallback 也从 contracts 派生**（D066） | P1 | ✅ 已决议 |
| 4 | 0LLM tools_hint 误导风险 | **全注入 13 工具**（实测 7.4KB/2.7s） | P2 | ✅ 已采纳·废弃 tools_hint |
| 5 | plans[] 格式无 schema 约束 | **加代码校验**（D067） | P1 | ✅ 已决议 |
| 6 | plans[] 传递机制未定义 | **ctx.plans 共享**（D068） | P1 | ✅ 已决议 |
| **新** | **strict 实测不强制** | **编排器加代码层参数校验**（D062） | P0 | ✅ 已决议 |

### 实测后新增发现

| 发现 | 影响 | 决策 |
|------|------|:---:|
| content + tool_calls 并存 ✅ | v2 plans[] 机制可行 | D045 确认 |
| strict 不强制 ❌ | 不能依赖服务端验证 | D062 加代码校验 |
| 13 工具全注入 2.7s ✅ | tools_hint 多余 | D063 废弃·全注入 |

---

## 十、总结

### v2 的正确决策

| 决策 | 评价 |
|------|------|
| 单次 LLM + function calling | ✅ 业界主流·正确 |
| 契约 Schema + strict | ✅ 参数约束可靠·正确 |
| 废弃信息卡 | ✅ 简化·正确 |
| 删除旧 R+R | ✅ 正确 |
| finalStep 轻 prompt | ✅ 正确 |
| 0LLM 不做硬筛选 | ✅ 正确 |

### v2 的问题

| 问题 | 严重度 |
|------|:---:|
| content + tool_calls 并存假设未验证 | 🔴 P0 |
| 数据变化检测职责真空 | 🟡 P1 |
| fallback prompt 双重维护 | 🟡 P1 |
| plans[] 无 schema 约束 | 🟡 P1 |
| plans[] 传递机制未定义 | 🟡 P1 |
| tools_hint 可能多余（13 工具可全注入） | 🟢 P2 |

### 一句话评审

> **v2 方向正确（单 LLM + function calling + 契约 Schema），但有 1 个 P0 验证缺口（content+tool_calls 并存）和 4 个 P1 设计漏洞（数据变化检测/双重维护/格式约束/传递机制）。这些不是架构级问题，是落地前必须补的细节。建议先做 P0 实测，再推进实现。**

---

*评审依据：v2 全部模块文档 + Smart Agent/Dumb Tool 四铁律 + kepler.gl/Mapbox/Power BI 业界对标*
