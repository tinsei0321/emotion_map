# EMC 架构重构 — 汇总 & 优化（v2 改良混合架构）

> **日期**：2026-07-27（v1）→ 2026-07-28（v2）  
> **参与**：用户 + DeepSeek  
> **版本**：v2——单次 LLM + function calling + 契约 Schema（废弃 v1 三阶段+信息卡）  
> **产出**：9 模块·61 条决策·全链路改造方案

---

## 一、v2 架构全景（实测后定稿）

```
用户 NL
  │
  ▼
┌─ 0LLM 字段识别 ─────────────────────────── <100ms
│  纯代码·不调 LLM                                
│  ├─ 字段识别 → 语义角色                          
│  ├─ 构建接地上下文（元数据·不发原始数据）         
│  └─ 数据缺失检测（无数据→短路提示导入）           
│  ⚠️ 不做工具筛选——全注入                        
├─────────────────────────────────────────────
│  LLM + Function Calling ────────────────── 2-3s
│  单次调用·DeepSeek V4·原生 function calling       
│                                                  
│  输入:                                            
│    tools 参数: 全部 13 工具完整契约 Schema（7.4KB） 
│    system prompt: 接地上下文 + NL                   
│                                                  
│  LLM 内部:                                        
│    理解意图 + 从 13 工具中选 + 填参数 + 产 plans[]  
│                                                  
│  输出:                                            
│    tool_calls: [1 个·rank=1]   ← 编排器执行        
│    content: plans[] JSON       ← CPD 素材           
│                                                  
│  fallback: function calling 失败 → 极简 prompt 模式 
├─────────────────────────────────────────────
│  编排器 确定性派发 ────────────────────── <10ms
│  JSON.parse(arguments)                            
│  ⚠️ 代码层参数校验（strict 实测不强制·必须兜底）     
│  TOOLS[name](params)                              
│  while-loop 降级为异常兜底                          
├─────────────────────────────────────────────
│  工具执行 ─────────────────────────── 100ms-2s
│  统一 observation [OK]/[ERR]/[WARN]                
│  每个 generate*ForAI = dialog 镜像                 
├─────────────────────────────────────────────
│  finalStep LLM 结论 ──────────────────── 3-5s
│  Prompt: 0.6-1.3KB                                
│  三句骨架 + 追问胶囊 (L1/L2)                        
├─────────────────────────────────────────────
│  质量防线 代码规则 ───────────────────── <20ms
│  _verifyClaims + 8 条质量规则                      
│  旧 R+R 全部删除                                    
└─────────────────────────────────────────────

CPD（消费 plans[]·不调LLM）
  展示 rank=2+ 选项 → 用户点击 → 直执 → 自动移除

总耗时: 6-11s（实测 function calling 2.7s + finalStep 3-5s）
```

---

## 二、决策清单（61 条）

> v1 决策（D001-D040）保留作为历史记录·标注「v1·已修订」的表示被 v2 取代。  
> v2 决策（D041-D061）为当前有效架构。

### 模块一：Diagnose Agent

#### v2（当前有效）

| ID | 决策 |
|----|------|
| D041 | 单次 LLM + function calling + 契约 Schema（修订 D001） |
| D042 | 废弃信息卡·参数约束由契约 Schema 承担（修订 D002/D003） |
| D043 | 契约 Schema 从 contracts 派生·strict 服务端强制 |
| D044 | 0LLM 软建议（tools_hint + fallback）·不做硬筛选（修订 D007） |
| D045 | plans[] 在 function call content 字段附带产出 |
| D046 | LLM prompt 30-54KB → 1-3KB·prefill <2s（修订 D006） |
| D047 | 数据三态在 function calling 内完成（修订 D008） |
| D048 | 单工具直执·多工具 plans 交 CPD·取消 Pro 阶段（修订 D004/D009） |
| D049 | 数据缺失→0LLM 短路提示导入 |

#### v1（历史·已修订）

| ID | 决策 | 状态 |
|----|------|:---:|
| D001-D011 | 三阶段 0LLM→Flash→Pro | 已修订 |

### 模块二：Orchestrator

#### v2（当前有效）

| ID | 决策 |
|----|------|
| D050 | 编排器消费 tool_calls[0]·不再查 SKILL_DEFS |
| D051 | _PARAM_ALIAS 废弃·契约 Schema additionalProperties:false（修订 D014） |
| D057 | LLM 只输出 1 个 tool_call·其余进 plans[] |
| D058 | arguments JSON.parse·strict 保证合法性 |
| D062 | 编排器加代码层参数校验（strict 实测不强制） |

#### v1（保留）

| ID | 决策 |
|----|------|
| D013 | while-loop 降级·MAX_ROUNDS 缩至 2-3 |
| D015 | _GEO_TOOLS 补 ensure_zone |

### 模块三：Execution Layer（v1 保留·无需适配）

| ID | 决策 |
|----|------|
| D016 | 统一 observation 格式 [OK]/[ERR]/[WARN] + 实际参数 + 明确单位 |
| D017 | generateHeatmapForAI 接入 computeStyle·density 补 analysis 映射 |
| D018 | focusLayer 父组空 FC 时返子层·修 Overview「0 条」 |

### 模块四：FinalStep Agent（v1 保留·无需适配）

| ID | 决策 |
|----|------|
| D019 | 保 LLM·轻 prompt ~0.6-1.3KB·耗时 3-5s |
| D020 | 追问胶囊三级——L1 直达·L2 轻判·L3 走 CPD |
| D021 | 胶囊绑定工具集·参数从 observation 派生 |

### 模块五：Review + Revise（v1 保留·无需适配）

| ID | 决策 |
|----|------|
| D022 | 删除旧 R+R 全部代码 |
| D023 | 新质量防线三层·全部代码 <20ms |
| D024 | 旧 R+R episode 日志迁至新防线 |

### 模块六：Prompt Engineering

#### v2（当前有效）

| ID | 决策 |
|----|------|
| D052 | contracts 新增 contracts_to_tools_schema() 派生契约 Schema |
| D053 | paradigm.py / SKILL_DEFS 过渡期保留·逐步废弃 |
| D059 | 旧 diagnose prompt 删除（MANIFESTO+8附录+6few-shot） |
| D060 | 保留极简 fallback prompt·function calling 失败兜底 |
| D061 | 契约 Schema 参数名以工具实际读取为准·消灭别名 |

#### v1（保留）

| ID | 决策 |
|----|------|
| D025 | tool_contracts.py 单一真相源 |
| R1 | rank `by` 默认值 `'polarity'` → `'worst'` |

### 模块七：Toolbox ↔ EMC（v1 保留·无需适配）

| ID | 决策 |
|----|------|
| D027 | generate*ForAI 15 个全审计·契约完整 |
| D028 | 保留 enforceMutualExclusion·增隐藏提示+空组隐藏 |
| D029 | ForAI=dialog 镜像通过 contracts+CI 校验落地 |

### 模块八：CPD 引擎

#### v2（当前有效）

| ID | 决策 |
|----|------|
| D054 | plans[] 数据源改为 function call content·格式不变 |

#### v1（保留）

| ID | 决策 |
|----|------|
| D030 | CPD 不调 LLM·内容来自 plans |
| D031 | CPD 选项点击后直接执行·跳过 LLM |
| D032 | 已执行选项自动移除·剩余继续 |
| D033 | 全部执行后展示完成·不进一步建议 |
| D034 | 用户偏好记入自我成长 |

### 模块九：字段识别

#### v2 简化（当前有效·实测后定稿）

| ID | 决策 |
|----|------|
| D063 | 废弃 tools_hint·全注入 13 工具（测试: 7.4KB/2.7s） |
| D064 | 0LLM 简化·只做接地上下文 + 数据缺失检测 |
| D037 | 候选为空→短路·提示导入数据（保留） |

#### 废弃

| 原 ID | 废弃理由 |
|------|------|
| D035/D036 | 全注入不需要字段→工具映射 |
| D038-D040 | 不做候选筛选·无需追问 |
| D055/D056 | 全注入替代 tools_hint/fallback |

| ID | 决策 |
|----|------|
| D035 | 字段→候选工具·分析型优先排序·截断到 4 |
| D036 | 关键词累积匹配·取并集 |
| D037 | 候选为空→短路·提示导入数据 |
| D038 | 候选≥5→追问·6 场景预写模板 |
| D039 | 追问文案纯中文+专业术语·不调 LLM |
| D040 | density analysis 维度分歧单独追问 |

---

## 三、耗时对比（实测后）

| 场景 | 改造前 | v2 实测 |
|------|:---:|:---:|
| 简单请求（"生成热力图"） | 50-95s | **6-11s**（FC 2.7s + finalStep 3-5s + 工具 0.2-2s） |
| 复杂请求（"分析西陵区"） | 50-95s + 超时 | **6-11s**（同——单次 FC） |
| CPD 多轮（连续分析） | 不可用 | **每轮 3-5s**（点击直执·无 LLM） |
| 13 工具全注入 prefill | — | **2.7s**（实测） |

**v2 核心优势**：简单和复杂请求耗时相同——都是单次 function calling。不再因复杂度增加 LLM 调用。

---

## 四、删除清单

| 组件 | 理由 | 决策 |
|------|------|:---:|
| `review.py` + `reviewStep` + `reviseStep` + `REVISE_TEMPLATE` | 旧 R+R 全部删除 | D022 |
| MANIFESTO 全文注入 diagnose | function calling 替代 | D059 |
| DIAGNOSE_TEMPLATE 8 字段 | function calling 替代 | D059 |
| 8 个 diagnose 附录 | function calling 替代 | D059 |
| `_DIAGNOSE_FEW_SHOT` 6 个示例 | function calling 替代 | D059 |
| industry_kb 注入 diagnose | 移除 | D059 |
| SKILL_DEFS | 编排器不再查·契约 Schema 替代 | D050/D053 |
| `_PARAM_ALIAS` | 契约 Schema additionalProperties:false 替代 | D051 |
| `_tplHitRateReady` Flash gate | 新架构不需要 | D046 |
| 信息卡（v1 概念） | 契约 Schema 覆盖 | D042 |
| Pro 独立阶段（v1） | function calling 内部完成 | D048 |

---

## 五、自我成长（未来开发）

| 项目 | 当前状态 |
|------|:---:|
| 契约 Schema 自动同步（contracts → tools schema） | ⬜ |
| recipes 基于运行时日志优化 | ⬜ |
| function calling 质量反馈闭环 | ⬜ |
| CPD 用户偏好 → LLM 排序优化 | ⬜ |
| DAG 并行链执行 | ⬜ |
| PANEL_MISSING 监控 | ⬜ |

---

## 六、实施建议（v2）

| 优先级 | 模块 | 理由 |
|:---:|------|------|
| **P0** | 模块六（契约 Schema 派生） | v2 核心——contracts_to_tools_schema() 落地·一切的前提 |
| **P0** | 模块一（function calling 模式） | 替换旧 diagnose·prompt 30-54KB→1-3KB·治超时根因 |
| **P0** | 模块二（编排器适配） | 消费 tool_calls·废弃 SKILL_DEFS + _PARAM_ALIAS |
| **P1** | 模块九（0LLM tools_hint） | tools_hint + fallback 软建议·配合 function calling |
| **P1** | 模块三（observation 补全 [OK]） | 统一格式半完成·补全前缀 |
| **P2** | 模块八（CPD plans 消费） | 数据源改 function call content·逻辑不变 |
| **P2** | 模块六（旧 diagnose prompt 删除） | function calling 稳定后删除·保留 fallback |
| **P3** | 模块七（ForAI 镜像 CI） | 防护性·无运行时收益 |

### 已完成（v1 遗产·保留）

| 模块 | 状态 |
|------|:---:|
| 模块三（computeStyle + focusLayer） | ✅ 已实现 |
| 模块四（finalStep 轻 prompt + 胶囊） | ✅ 已实现 |
| 模块五（删除旧 R+R + 质量防线） | ✅ 已实现 |
| 模块七（Toolbox 委托） | ✅ 已实现 |

---

## 七、跨模块补充设计（v2 实测后定稿）

### 7.1 多轮对话上下文传递（D065 + D068）

```
轮1: 0LLM → function calling → ctx.plans[5项]
     → 执行 rank=1 → finalStep（读 ctx.plans 生成胶囊）
     → 轮结束: ctx.plans 存入 turnHistory.lastPlans
                _dataSignature() 存入 turnHistory.lastDataSig

轮2: harness 入口:
     → 对比 currentSig vs turnHistory.lastDataSig
     → 相同 → 复用 lastPlans（用户点 CPD 选项 → 直执）
     → 不同 → 清空 lastPlans → 重新走完整管线
     → 提示用户「数据已变化·已重新分析」

ctx.plans 生命周期:
  function calling 产出 → parsePlans 校验（D067）→ ctx.plans
  → finalStep 读（追问胶囊）
  → CPD 读（rank=2+ 选项）+ 写（executed 标记）
  → turnHistory 跨轮持久化
```

### 7.2 异常恢复（v2 统一降级链路·永不「请求失败」）

| 失败层 | 降级策略 |
|------|------|
| 0LLM | 接地为空 → 短路提示导入数据 |
| function calling | API 失败/空 tool_calls → fallback prompt（D066·contracts 派生） |
| 参数校验（D062） | 非法值且有默认值 → 替换默认值；无默认值 → observation=[ERR] |
| plans[] 解析（D067） | JSON 格式错误 → 空 plans（CPD 无选项·不崩溃） |
| 工具执行 | observation=`[ERR]` + 原因 → finalStep 诚实报告 |
| finalStep | 纯 observation 展示（不经 LLM 翻译）·保留追问胶囊 |
| 质量防线 | R1/R4 硬拦截 → 纯 observation 展示 |

### 7.3 前后端 contracts 同步

```
tool_contracts.py (Python 单一源)
  ├─→ contracts_to_tools_schema()  → 契约 Schema（function calling）
  ├─→ contracts_to_text()          → fallback prompt 工具描述（D066）
  ├─→ build_js_contracts.py        → stages_contracts.js（前端）
  └─→ validate_contracts_sync.py   → CI 校验
```

### 7.4 新增决策（D062-D068）

| ID | 模块 | 决策 | 来源 |
|----|------|------|:---:|
| D062 | Orchestrator | 编排器加代码层参数校验（strict 不强制） | 实测 |
| D063 | Field | 废弃 tools_hint·全注入 13 工具 | 实测 |
| D064 | Field | 0LLM 简化·只做接地 + 缺失检测 | D063 |
| D065 | Harness | 数据变化检测放 harness·_dataSignature | P1-1 |
| D066 | Prompt | fallback prompt 从 contracts 派生 | P1-2 |
| D067 | Orchestrator | plans[] 解析后代码校验·容错 | P1-3 |
| D068 | Orchestrator | plans[] 存 ctx.plans·三方共享 | P1-4 |

---

*全 9 模块·68 条决策（D001-D068）·v2 改良混合架构·实测后定稿*
