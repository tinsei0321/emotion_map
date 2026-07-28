# EMC 9 大模块系统性评估报告

> **评估方**：DeepSeek（第三方 LLM）  
> **评估日期**：2026-07-28  
> **评估触发**：用户反馈"降智"、数据无法识别、超时等问题远未达预期  
> **评估方法**：代码审计（逐模块对照设计文档）+ 业界对标（kepler.gl/Mapbox/Power BI）  
> **诚实声明**：本报告不附和设计文档的"✅ 已完成"标记，以代码实际状态为准

---

## 一、核心发现：设计与实现的巨大鸿沟

### 1.1 触目惊心的现状

用户被告知"9 大模块已完成代码工程"。实际代码审计结果表明：

| 模块 | 设计状态 | **代码实际** | 差距 |
|:---:|:---:|:---:|------|
| 1. Diagnose 三阶段 | ✅ 已决议 | **❌ 0% 实现** | 核心 refactor 完全没做 |
| 2. Orchestrator | ✅ 已决议 | ⚠️ 30% | chain 仍固定、while-loop 部分降级 |
| 3. Execution | ✅ 已决议 | ✅ 80% | computeStyle✅ focusLayer✅ observation 半完成 |
| 4. FinalStep | ✅ 已决议 | ✅ 90% | prompt 瘦身✅ 胶囊✅ |
| 5. Review+Revise | ✅ 已决议 | ✅ 90% | 删旧 R+R✅ 代码防线✅ |
| 6. Prompt Engineering | ✅ 已决议 | ⚠️ 40% | contracts 存在但未派生 |
| 7. Toolbox 接口 | ✅ 已决议 | ✅ 85% | 委托✅ |
| 8. CPD | ✅ 已决议 | ⚠️ 30% | 引擎存在但不消费 Pro plans |
| 9. 字段识别 | ✅ 已决议 | **❌ 0% 实现** | 无字段→工具映射 |

**模块一和模块九——架构重构的核心——代码实现率 0%。** 这就是"降智"和"超时"依然存在的根本原因。

### 1.2 用户当前体验问题的根因映射

| 用户反馈 | 设计文档的方案 | 实际代码 | 为什么没修好 |
|------|------|------|------|
| "降智"——简单 GIS 操作跑不通 | 模块一：Flash 填信息卡 + Pro 推理 | Flash 仍是 25KB 旧 prompt + 8 字段旧卡 | **模块一未实现** |
| 数据无法识别 | 模块九：0LLM 字段→工具映射 | field_dictionary 只有角色识别，无工具映射 | **模块九未实现** |
| 思考阶段已出答案但卡检索 | 模块一：Flash <5s + 单卡直传 | Flash prefill 仍 20-35s | **模块一未实现** |
| 超时 | 模块一+四：prompt 瘦身 | finalStep 已瘦✅，diagnose 未瘦❌ | **半完成** |

---

## 二、逐模块详细评估

### 模块一：Diagnose Agent ❌ 0% 实现（最严重）

#### 设计目标

```
0LLM 字段识别(<100ms) → Flash 填信息卡(<5s·1-3.5KB) → Pro 推理(5-10s)
```

#### 代码实际

```
_quickIntent(关键词预判) → diagnoseStep(Flash·单次·25KB+ prompt·8字段旧卡) → 编排器
```

**关键差距**：

| 设计 | 代码实际 | 文件:行 |
|------|------|------|
| 0LLM 字段→工具映射 | **不存在**。field_dictionary.js 只有 FIELD_ROLES（角色识别），无 FIELD_TOOLS | `field_dictionary.js:9-53` |
| Flash 填信息卡 | **不存在**。Flash 仍产出旧 8 字段诊断卡 `{intent, domain_lens, scale, decision_type, outlet, data_plan, template, params}` | `stages.js:169-202` normalizeCard |
| Flash prompt 1-3.5KB | **仍是 25KB+**。`build_diagnose_prompt` 仍拼 MANIFESTO 全文 + 8 附录 + 6 few-shot | `prompts.py:220-253` |
| Pro 推理阶段 | **不存在**。deliberateStep 只在 Pro 模式 + 复杂任务时触发，且做的是"验证"非"推理-计划" | `stages.js:302-313` |
| 单卡直传编排器 | **不存在**。所有请求都走同一条 diagnose → orchestrate 路径 | `harness.js:567` |

#### 评估

**模块一是整个重构的核心——它定义了新的认知架构。它完全没有落地。** 所有下游模块（Pro 动态 chain、CPD 消费 plans、字段识别追问）都依赖它，所以全部阻塞。

### 模块二：Orchestrator ⚠️ 30% 实现

| 设计 | 代码实际 | 状态 |
|------|------|:---:|
| Pro 动态 chain | 仍用 CHAIN_REGISTRY 固定链（2 条） | ❌ |
| while-loop 降级 2-3 轮 | 部分实现——生成类请求缩到 2-3，其他仍 4-6 | ⚠️ |
| _PARAM_ALIAS 按工具分区 | **已实现**——全局 + 按工具两层别名 | ✅ |
| _GEO_TOOLS 补 ensure_zone | 需核实 | ⚠️ |

### 模块三：Execution Layer ✅ 80% 实现

| 设计 | 代码实际 | 状态 |
|------|------|:---:|
| generateHeatmapForAI 接入 computeStyle | **已实现**——接受 analysis 参数，调 computeStyle | ✅ |
| 统一 observation [OK]/[ERR]/[WARN] | **半完成**——只有 [ERR] 前缀，无 [OK]/[WARN] | ⚠️ |
| focusLayer 父组空 FC 返子层 | **已实现** | ✅ |

### 模块四：FinalStep ✅ 90% 实现

| 设计 | 代码实际 | 状态 |
|------|------|:---:|
| 轻 prompt 0.6-1.3KB | **已实现**——去 MANIFESTO，~0.9KB | ✅ |
| 三句骨架 | **已实现** | ✅ |
| 追问胶囊 L1/L2/L3 | **部分**——L1/L2 有了，L3 禁止 | ✅ |

### 模块五：Review+Revise ✅ 90% 实现

| 设计 | 代码实际 | 状态 |
|------|------|:---:|
| 删除旧 R+R | **已删除** review.py/reviewStep/reviseStep | ✅ |
| 8 条代码质量规则 | **已实现** applyQualityDefense（实际 ~10 条） | ✅ |

### 模块六：Prompt Engineering ⚠️ 40% 实现

| 设计 | 代码实际 | 状态 |
|------|------|:---:|
| tool_contracts.py 单一源 | **文件存在**（33KB），定义完整 | ✅ |
| prompt 从 contracts 派生 | **未派生**——仍用手写镜像 + 校验脚本 | ❌ |

### 模块七：Toolbox 接口 ✅ 85% 实现

| 设计 | 代码实际 | 状态 |
|------|------|:---:|
| generate*ForAI 契约完整 | density 委托 Toolbox ✅ | ✅ |
| ForAI = dialog 镜像 | computeStyle 接入 ✅ | ✅ |

### 模块八：CPD ⚠️ 30% 实现

| 设计 | 代码实际 | 状态 |
|------|------|:---:|
| 不调 LLM | **已实现**——纯客户端确定性 | ✅ |
| 消费 Pro plans | **无法实现**——Pro 不存在，无 plans 可消费 | ❌ |

### 模块九：字段识别 ❌ 0% 实现

| 设计 | 代码实际 | 状态 |
|------|------|:---:|
| FIELD_TO_TOOLS 映射 | **不存在** | ❌ |
| 候选工具选择器 | **不存在** | ❌ |
| 候选≥5 追问 6 场景 | **不存在** | ❌ |

---

## 三、业界对标：方向性反思

### 3.1 业界标准架构

| 平台 | 架构 | 核心 |
|------|------|------|
| **kepler.gl** | 单 LLM + function calling | LLM 选工具 → 用户确认参数 → 浏览器执行。原始数据不发 LLM |
| **Mapbox** | MCP 工具服务器 | GIS 能力做成工具，任何 LLM 调 |
| **Power BI Copilot** | LLM + RAG over 语义层 | 语义层是质量关键 |
| **Tableau Pulse** | LLM + 语义模型 | 同上 |

**业界共识：单 LLM + function calling + 语义层。不是多阶段 LLM 管线。**

### 3.2 我们 9 大模块的方向性问题

| 设计决策 | 业界做法 | 评估 |
|------|------|:---:|
| 0LLM→Flash→Pro 三阶段 | 单 LLM + function calling | ⚠️ 过度设计 |
| Flash 填信息卡 → Pro 推理 | LLM 直接用 function calling 选工具+填参 | ⚠️ 拆成两次 LLM 反而慢 |
| contracts 语义层 | ✅ 业界共识 | ✅ 方向正确 |
| 删除旧 R+R | ✅ 业界不做 LLM 审 LLM | ✅ 方向正确 |
| finalStep 轻 prompt | ✅ 业界用小模型 + 领域缩窄 | ✅ 方向正确 |

### 3.3 关键启示

**模块一的「三阶段 LLM 管线」与业界主流相悖。** kepler.gl 用单次 LLM + function calling 就实现了同样的效果——LLM 直接选工具、填参数、出结果。不需要拆成 Flash 填卡 + Pro 推理两次 LLM 调用。

**但我们的 contracts（模块六语义层）方向完全正确**——这就是业界说的「语义层」，是 AI+专业平台的核心资产。

---

## 四、架构建议：从三阶段回归单 LLM + Function Calling

### 4.1 为什么改方向

| 维度 | 三阶段（当前设计） | 单 LLM + function calling（建议） |
|------|:---:|:---:|
| LLM 调用次数 | 2-3 次（Flash + Pro + finalStep） | **1-2 次**（function calling + finalStep） |
| 总延迟 | 13-20s（理论） | **5-10s** |
| 实现复杂度 | 高——三阶段 + 信息卡 + plans + CPD 消费 | **低**——标准 function calling 模式 |
| 业界验证 | ❌ 无先例 | ✅ kepler.gl/Mapbox/Power BI |
| 已有代码复用 | 模块四/五/六/七可复用 | 同左 |

### 4.2 建议的新架构

```
用户 NL
  │
  ▼
0LLM 预处理（保留·纯代码）
  ├─ 字段识别 → 语义角色
  ├─ 构建接地上下文（元数据·不发原始数据）
  └─ 构建工具目录子集（基于字段+关键词动态选择）
  │
  ▼
LLM + Function Calling（单次调用）
  ├─ 模型：DeepSeek V4（支持 function calling）
  ├─ Prompt：语义层摘要 + 工具子集 + 接地上下文 + 用户 NL
  ├─ LLM 直接选工具 + 填参数（类似 kepler.gl）
  └─ 输出：tool_calls = [{ name, params }]
  │
  ▼
编排器（确定性派发·0 LLM）
  ├─ 单工具 → 直接执行
  ├─ 多工具 → 按依赖顺序执行
  └─ 异常 → 降级
  │
  ▼
工具执行 → observation（统一格式）
  │
  ▼
finalStep（保留·轻 LLM）
  ├─ 翻译 observation → 三句结论
  └─ 生成追问胶囊
  │
  ▼
质量防线（保留·纯代码）
```

### 4.3 和当前 9 大模块的关系

| 模块 | 在新架构中的角色 |
|:---:|------|
| 模块一 | **重构**——从三阶段改为单 LLM + function calling |
| 模块二 | **保留**——编排器逻辑不变 |
| 模块三 | **保留**——observation 统一格式继续 |
| 模块四 | **保留**——finalStep 轻 prompt 已实现 |
| 模块五 | **保留**——代码质量防线已实现 |
| 模块六 | **提升为核心**——contracts 就是语义层，是 function calling 的工具定义 |
| 模块七 | **保留**——Toolbox 委托已实现 |
| 模块八 | **保留**——CPD 消费 plans[]（来源改为 function call content） |
| 模块九 | **简化**——0LLM 做 tools_hint 软建议 + tools_fallback 兜底 |

---

## 四之二、v2 改良混合架构定稿（2026-07-28 更新）

经用户 + DeepSeek 深入讨论，v2 架构已定稿。核心变化：

| v1 三阶段（已废弃） | v2 改良混合（当前） |
|------|------|
| 0LLM → Flash 填信息卡 → Pro 推理 | **0LLM → 单次 LLM + function calling + 契约 Schema** |
| 信息卡约束参数 | **契约 Schema（contracts → JSON Schema → strict）** |
| 0LLM 硬筛选候选集 | **tools_hint 软建议 + tools_fallback 兜底** |
| Pro 产出 plans[] | **function call content 附带 plans[]** |
| 2-3 次 LLM 调用 | **1-2 次** |

**61 条决策（D001-D061）·v2 新增 D041-D061 为当前有效架构。**

详见：
- `01-diagnose-agent.md`（v2 完整重写）
- `02-orchestrator.md` / `06-prompt-engineering.md` / `08-cpd-engine.md` / `09-field-recognition.md`（v2 适配）
- `SUMMARY.md`（v2 全景 + 61 条决策 + 实施优先级）

---

## 五、修复 Plan（v2 更新）

### Phase 0：止血（立即·1-2 天）

修当前最影响体验的 bug，不改架构：

| # | 问题 | 修复 | 文件 |
|---|------|------|------|
| 1 | diagnose prompt 25KB → prefill 慢 | 移除 MANIFESTO 全文 + industry_kb + 冗余附录 | `prompts.py:220` |
| 2 | observation 无 [OK] 前缀 | 补全统一格式 | `tools.js` |
| 3 | "Layers 已上传数据无法识别" | 核实 buildContext 是否正确读取图层字段 | `tools.js:563` |

### Phase 1：语义层落地（1 周）

把 contracts 从「文件存在但不派生」变成「function calling 的工具定义」：

| # | 任务 | 文件 |
|---|------|------|
| 4 | contracts 转为 function calling 的 tools schema 格式 | `tool_contracts.py` |
| 5 | diagnose 改为 function calling 模式（单次 LLM） | `harness.js` + `stages.js` |
| 6 | 删除旧 diagnose prompt（MANIFESTO + 8 附录） | `prompts.py` |

### Phase 2：0LLM 简化（3 天）

| # | 任务 | 文件 |
|---|------|------|
| 7 | 字段识别只做接地上下文（不做候选工具选择） | `field_dictionary.js` |
| 8 | 工具目录动态子集注入（基于字段+关键词） | `tools.js` buildContext |

### Phase 3：验证（3 天）

| # | 任务 |
|---|------|
| 9 | 对标 kepler.gl：单次 LLM → 选工具 → 出图 → 写结论 |
| 10 | 耗时验证：目标 <10s 端到端 |
| 11 | 准确性验证：简单 GIS 操作 100% 跑通 |

---

## 六、总结

### 6.1 当前状态

9 大模块中，**只有 4 个真正完成**（模块四/五/七 + 模块三大部分）。核心的模块一（三阶段架构）和模块九（字段识别）完全没实现。用户看到的"降智""超时"问题，根因正是这两个核心模块的缺失。

### 6.2 方向性建议

模块一的「0LLM→Flash→Pro 三阶段」设计与业界主流（单 LLM + function calling）相悖。建议回归业界验证过的模式：

- **单次 LLM + function calling**（kepler.gl 模式）
- **contracts 语义层作为核心**（Power BI 模式）
- **0LLM 只做接地上下文**（不做候选工具选择——LLM 自己选）

### 6.3 已完成模块的价值

模块四（finalStep 瘦身）、模块五（删 R+R）、模块六（contracts）、模块七（Toolbox 委托）——这些在新架构中**全部保留**，是有价值的已完成资产。

### 6.4 一句话

> **停止追逐三阶段架构的幻影。回归单 LLM + function calling + 语义层的业界标准。把 contracts 做成 function calling 的工具定义，一次 LLM 调用完成选工具+填参数。**

---

*评估依据：全量代码审计（frontend/js/ai_qa/ + ai_qa/ + frontend/js/toolbox/）+ 业界研究（kepler.gl/Mapbox/Power BI/Tableau/ThoughtSpot）+ 9 大模块设计文档对照*
