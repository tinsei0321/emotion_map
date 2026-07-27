# EMC 架构深度拆解讨论 — 会议记录

> **会议日期**：2026-07-27  
> **参与方**：用户（产品 owner）+ DeepSeek（第三方 LLM·架构评估）  
> **背景**：经 CB-04 六轮 SCAN + CB-08 互评，共识为「LLM 简化链路」方向。现逐个模块拆解 EMC 架构与运行机制，产出可执行改造方案。  
> **既定方向**：保 LLM·不分简单/复杂边界·瘦 prompt 提速度  
> **产出目录**：`docs/catch-ball/emc-arch-deepdive/`

---

## 进度总览

| # | 模块 | 状态 | 决议数 | 关键结论 |
|:---:|------|:---:|:---:|------|
| 1 | **Diagnose Agent**（认知层） | ✅ 已完成 | 11 | 三阶段低耦合·进入编排器 |
| 2 | **Orchestrator**（编排层） | ✅ 已完成 | 4 | 动态 chain·while-loop降级·别名分区·门禁修 |
| 3 | **Execution Layer**（执行层） | ✅ 已完成 | 3 | 统一observation·computeStyle路由·EMC组修 |
| 4 | **FinalStep Agent**（输出层） | ✅ 已完成 | 3 | 轻prompt·追问胶囊三级·3-5s |
| 5 | **Review + Revise** | ✅ 已完成 | 5 | 删除旧R+R·新质量防线8条·<20ms |
| 6 | **Prompt Engineering** | ✅ 已完成 | 2 | contracts单一源·prompt全派生 |
| 7 | **Toolbox ↔ EMC 接口** | ✅ 已完成 | 3 | 参数审计全过·互斥保留·镜像落地 |
| 8 | **CPD 引擎** | ✅ 已完成 | 5 | 不调LLM·Pro plans消费·选项直执 |
| 9 | **字段识别** | ✅ 已完成 | 6 | 纯规则·6场景追问·候选≤4 |

---

## 决策记录

| ID | 模块 | 决策 | 日期 |
|----|------|------|------|
| — | — | 暂无 | — |

---

## 开放问题 [OPEN]

| ID | 问题 | 提出模块 |
|----|------|:---:|
| — | 暂无 | — |

---

## 模块一：Diagnose Agent（认知层）— Stage 1+2 决议完成·Stage 3 讨论中

> **架构决议**：三阶段低耦合——0LLM（字段识别+候选工具集）→ Flash（填信息卡·匹配不推理）→ Pro（推理+计划）

### Stage 1: 0LLM ✅ 已决议

| 决策 | 内容 |
|------|------|
| **字段→工具映射** | 纯规则——`field_dictionary.js` 扩展 `FIELD_TO_TOOLS` + `GEOMETRY_TO_TOOLS` |
| **候选工具集** | 字段角色 ∩ 几何类型 ∩ NL关键词 → 控制在 2-4 个 |
| **接地上下文** | `buildContext` 精简——Flash 只需字段名+角色+1-2样本值，不需全量值域分布 |
| **触发词补全** | `B_TRACK_PARADIGM` density 触发词已补「热力图」「网格」「方格网」「聚合域」「空间聚合」 |

### Stage 2: Flash LLM ✅ 已决议

| 决策 | 内容 |
|------|------|
| **职能** | 只做匹配+填卡——不推理、不计划、不选工具 |
| **输入** | 0LLM 产出的候选工具集（1-4个）+ 精简接地上下文 |
| **输出** | 每个候选工具一张「信息卡」——参数槽位绑定工具 schema |
| **信息卡字段** | 工具参数（按 schema 填值）+ `confidence` + `rationale` + `data_status` |
| **路由** | 单卡→直传编排器；2-4卡→交 Pro 推理；0卡→降级 |
| **Prompt 瘦身** | 从当前 30-54KB 缩至 **1-3.5KB**——只保留工具schema、三态判据、卡格式、精简grounding |
| **耗时** | 从当前 25-45s 缩至 **<5s** |

**Flash prompt 精简清单**：

| 保留 | 大小 | 移除 | 大小 | 去哪 |
|------|:---:|------|:---:|------|
| 工具参数 schema | ~200/工具 | MANIFESTO §1-6 | ~7KB | Pro（如需） |
| 数据三态判据 | ~200 | 尺度-范式矩阵 | ~1.8KB | Pro |
| 信息卡输出格式 | ~200 | 领域出口启发库 | ~1.5KB | Pro |
| 精简接地上下文 | ~500-2000 | industry_kb | 8-20KB | Pro（C类才用） |
| （可选）1 few-shot | ~300 | 触发词确认表 | ~300 | 0LLM已做 |
| | | intent分类规则 | ~200 | 代码判断 |
| | | 回答公约 | ~300 | finalStep的事 |
| | | GEO_TOOL_CATALOG描述 | ~2KB | Pro |
| **合计** | **~1-3.5KB** | **合计移除** | **~25-50KB** | |

### Stage 3: Pro LLM ✅ 已决议

| 决策 | 内容 |
|------|------|
| **触发条件** | Flash 产出 2-4 张信息卡 → 交 Pro；单卡 → 跳过 Pro 直传编排器 |
| **职能** | 推理（多卡选最优）+ 计划（排单步参数或多步 chain） |
| **Prompt** | 统一轻量 ~6-10KB——工具能力字典 + 编排规则 + MANIFESTO §7 + 信息卡 + 接地 |
| **不分 intent** | gis_operation / emotion_analysis 同一套轻 prompt——不深入归因/领域出口（复杂问题由 CPD 多轮引导拆解） |
| **输出** | 执行计划：`{ template, params, chain }`——编排器直接消费 |
| **chain** | 先线性后 DAG——当前线性，后续改造并行 |

### 工具能力字典（Pro 知识底座）

| 决策 | 内容 |
|------|------|
| **覆盖** | 13 工具 × 4 category（Load/Transform/Analyze/Export） |
| **条目结构** | name / category / triggers / params(类型+枚举+默认) / exclusive_with / composes_with / recipes |
| **编排规则** | 互斥检测 / 依赖顺序 / 出口唯一 / Load→Transform→Analyze不可逆 / 并行判断 |
| **维护** | ⬜ 列入「EMC 自我成长」范畴——未来重点开发·优化 recipes + 自动同步 contracts |

### 模块一数据流总图

```
用户 NL
  → 0LLM（字段识别+候选工具集·<100ms）
  → Flash（填信息卡·匹配不推理·<5s）
  → Pro（多卡时推理计划·5-10s；单卡时跳过）
  → 编排器
```

---

## 决策记录

| ID | 模块 | 决策 | 日期 |
|----|------|------|------|
| D001 | Diagnose | 架构改为三阶段低耦合：0LLM → Flash → Pro | 07-27 |
| D002 | Diagnose | Flash 只做匹配+填卡，不推理不计划不选工具 | 07-27 |
| D003 | Diagnose | 信息卡绑定工具 schema，每候选工具填一张 | 07-27 |
| D004 | Diagnose | 单卡→编排器；多卡→Pro；零卡→降级 | 07-27 |
| D005 | Diagnose | 单卡 confidence=low 也直接执行 | 07-27 |
| D006 | Diagnose | Flash prompt 从 30-54KB 缩至 1-3.5KB·耗时 <5s | 07-27 |
| D007 | Diagnose | 0LLM 字段识别纯规则，不引入 LLM | 07-27 |
| D008 | Diagnose | 数据三态判断归 Flash（匹配型·非推理） | 07-27 |
| D009 | Diagnose | Pro prompt 统一轻量 ~6-10KB·不分 intent | 07-27 |
| D010 | Diagnose | 单问深度控制在 gis_operation 级别·复杂问题由 CPD 多轮拆解 | 07-27 |
| D011 | Diagnose | 工具能力字典 13 工具·维护列入 EMC 自我成长 | 07-27 |
| D012 | Orchestrator | runChainPath 从固定链 → Pro 动态 chain | 07-27 |
| D013 | Orchestrator | while-loop 降级为异常兜底·MAX_ROUNDS 缩至 2-3 | 07-27 |
| D014 | Orchestrator | _PARAM_ALIAS 改为按工具注册别名 | 07-27 |
| D015 | Orchestrator | _GEO_TOOLS 补 ensure_zone | 07-27 |
| D016 | Execution | 统一 observation 格式 [OK]/[ERR]/[WARN] | 07-27 |
| D017 | Execution | generateHeatmapForAI 接入 computeStyle | 07-27 |
| D018 | Execution | focusLayer 父组空 FC 返子层 | 07-27 |
| D019 | FinalStep | 保 LLM·轻 prompt ~1-2KB·3-5s | 07-27 |
| D020 | FinalStep | 追问胶囊三级·L1直达 L2轻判 L3走CPD | 07-27 |
| D021 | FinalStep | 胶囊绑定工具集·参数从 observation 派生 | 07-27 |
| D022 | Review | 删除旧 R+R 全部代码 | 07-27 |
| D023 | Review | 新质量防线三层·全部代码 <20ms | 07-27 |
| D024 | Review | 旧 R+R episode 日志迁至新防线 | 07-27 |
| D025 | Prompt | tool_contracts.py 单一真相源 | 07-27 |
| D026 | Prompt | Flash/Pro/finalStep prompt 从 contracts 派生 | 07-27 |
| D027 | Toolbox | generate*ForAI 15 个全审计·契约完整 | 07-27 |
| D028 | Toolbox | 保留互斥·增隐藏提示+空组不显示 | 07-27 |
| D029 | Toolbox | ForAI=dialog镜像通过 contracts+CI 校验 | 07-27 |
| D030 | CPD | CPD 不调 LLM·内容来自 Pro plans | 07-27 |
| D031 | CPD | CPD 选项点击后直接执行·跳过 Flash | 07-27 |
| D032 | CPD | 已执行选项自动移除·剩余继续 | 07-27 |
| D033 | CPD | 全部执行后展示完成·不进一步建议 | 07-27 |
| D034 | CPD | 用户偏好记入自我成长·优化 Pro 排序 | 07-27 |
| D035 | Field | 字段→候选工具·分析型优先·截断到 4 | 07-27 |
| D036 | Field | 关键词累积匹配合并·取并集 | 07-27 |
| D037 | Field | 候选为空→短路·提示导入数据 | 07-27 |
| D038 | Field | 候选≥5→追问·6场景预写模板 | 07-27 |
| D039 | Field | 追问文案纯中文+专业术语·不调LLM | 07-27 |
| D040 | Field | density analysis 维度分歧单独追问 | 07-27 |

---

## EMC 自我成长（未来开发·当前计划）

| 项目 | 内容 | 状态 |
|------|------|:---:|
| 工具能力字典自动同步 | `tool_contracts.py` 单一源 → 字典自动派生 | ⬜ 计划中 |
| recipes 优化 | 基于运行时日志挖掘常见 NL→参数模式，自动补全 recipes | ⬜ 计划中 |
| Pro chain 质量反馈 | 执行结果反哺 Pro 推理——chain 执行成功率回写字典 | ⬜ 计划中 |

---

## 开放问题 [OPEN]

| ID | 问题 | 提出模块 |
|----|------|:---:|
| — | 暂无 | — |

---

## 模块二：Orchestrator（编排层）✅ 已完成

> 决议见 [02-orchestrator.md](02-orchestrator.md)。4 个改造：动态 chain·while-loop 降级·_PARAM_ALIAS 按工具分区·_GEO_TOOLS 补 ensure_zone。

| ID | 决策 |
|----|------|
| D012 | runChainPath 从 CHAIN_REGISTRY 固定链 → Pro 动态 chain |
| D013 | while-loop 降级为异常兜底·MAX_ROUNDS 缩至 2-3 |
| D014 | _PARAM_ALIAS 改为按工具注册别名·修 density radius 丢失 |
| D015 | _GEO_TOOLS 补 ensure_zone·修 F3 门禁误判 |
| DAG | 暂不做·先线性链·记入自我成长 |

---

## 模块三：Execution Layer（执行层）✅ 已完成

> 决议见 [03-execution-layer.md](03-execution-layer.md)。3 个改造：统一 observation·computeStyle 路由·EMC 组修。

| ID | 决策 |
|----|------|
| D016 | 统一 observation 格式 [OK]/[ERR]/[WARN] + 实际参数 + 明确单位 |
| D017 | generateHeatmapForAI 接入 computeStyle·density 补 analysis 映射 |
| D018 | focusLayer 父组空 FC 时返子层·修 Overview「0 条」 |

---

## 模块四：FinalStep Agent（输出层）✅ 已完成

> 决议见 [04-finalstep-agent.md](04-finalstep-agent.md)。3 个决策：轻 prompt·追问胶囊三级·参数派生。

| ID | 决策 |
|----|------|
| D019 | 保 LLM·轻 prompt ~1-2KB·耗时 3-5s |
| D020 | 追问胶囊三级——L1 直达（同工具）·L2 轻判（跨工具单步）·L3 走 CPD |
| D021 | 胶囊绑定工具集·参数从 observation 派生·不跨越可用数据边界 |

---

## 模块五：Review + Revise 🔴 讨论中

### 当前状态

```
REVIEW_ENABLED = false（默认关闭）
single-template → 显式跳过
gis_operation → 显式跳过
while-loop + emotion_analysis → 唯一可能触发审查的路径
```

**审查机制三重关闭——大部分请求根本没在跑。** 但代码还在（review.py + reviewStep + reviseStep）。

### 讨论要点

1. 审查机制在新架构中还有价值吗？
2. `_verifyClaims`（代码级图层验证）是否够用？
3. 是彻底删掉审查代码，还是保留但不跑？

---

## 模块六：Prompt Engineering ⬜ 待讨论

### 已决议的 prompt 瘦身

| 阶段 | 当前 | 瘦身后 | 决议模块 |
|------|:---:|:---:|:---:|
| Flash diagnose | 30-54KB | 1-3.5KB | 模块一 |
| Pro 推理 | — | 6-10KB | 模块一 |
| finalStep | 20-44KB | 1-2KB | 模块四 |

### 待讨论

- MANIFESTO 分层——哪些节给哪些阶段
- paradigm 数据收口——tool_contracts.py 作为单一源

---

## 进度总览（更新）
