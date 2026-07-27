# EMC 架构重构 — 汇总 & 优化

> **日期**：2026-07-27  
> **参与**：用户 + DeepSeek  
> **产出**：9 模块·40 条决策·全链路改造方案

---

## 一、架构全景

```
用户 NL
  │
  ▼
┌─ 0LLM 字段识别 ─────────────────────────── <100ms
│  候选工具集 1-4 个                           
│  候选=0→短路·候选≥5→追问                     
├───────────────────────────────────────────
│  Flash LLM 填信息卡 ──────────────────── <5s
│  每候选工具填一张·不推理·不选工具            
│  Prompt: 1-3.5KB                             
├───────────────────────────────────────────
│  单卡→直传                                   
│  多卡→Pro LLM 推理计划 ──────────────── 5-10s
│         Prompt: 2.5-5KB                      
│         产出: plans[]（编排器+CPD 通用消费）    
├───────────────────────────────────────────
│  编排器 确定性派发 ───────────────────── <10ms
│  单工具→runTemplatePath                       
│  多步→runChainPath (Pro 动态 chain)           
│  while-loop 降级为异常兜底                     
├───────────────────────────────────────────
│  工具执行 ───────────────────────── 100ms-2s
│  统一 observation [OK]/[ERR]/[WARN]           
│  每个 generate*ForAI = dialog 镜像            
├───────────────────────────────────────────
│  finalStep LLM 结论 ────────────────── 3-5s
│  Prompt: 0.6-1.3KB                            
│  三句骨架 + 追问胶囊 (L1/L2/L3)                
│  L3 胶囊→CPD 介入                             
├───────────────────────────────────────────
│  质量防线 代码规则 ──────────────────── <20ms
│  _verifyClaims + 8 条质量规则                 
│  旧 R+R 全部删除                               
└───────────────────────────────────────────

CPD（消费 Pro plans·不调LLM）
  展示 rank=2+ 选项 → 用户点击 → 直执 → 自动移除
```

---

## 二、决策清单（40 条）

### 模块一：Diagnose Agent

| ID | 决策 |
|----|------|
| D001 | 架构改为三阶段低耦合：0LLM → Flash → Pro |
| D002 | Flash 只做匹配+填卡，不推理不计划不选工具 |
| D003 | 信息卡绑定工具 schema，每候选工具填一张 |
| D004 | 单卡→编排器；多卡→Pro；零卡→降级 |
| D005 | 单卡 confidence=low 也直接执行 |
| D006 | Flash prompt 从 30-54KB 缩至 1-3.5KB·耗时 <5s |
| D007 | 0LLM 字段识别纯规则，不引入 LLM |
| D008 | 数据三态判断归 Flash（匹配型·非推理） |
| D009 | Pro prompt 统一轻量 ~2.5-5KB·不分 intent |
| D010 | 单问深度控制在 gis_operation 级别·复杂问题由 CPD 多轮拆解 |
| D011 | 工具能力字典 13 工具·维护列入自我成长 |

### 模块二：Orchestrator

| ID | 决策 |
|----|------|
| D012 | runChainPath 从 CHAIN_REGISTRY 固定链 → Pro 动态 chain |
| D013 | while-loop 降级为异常兜底·MAX_ROUNDS 缩至 2-3 |
| D014 | _PARAM_ALIAS 改为按工具注册别名·修 density radius 丢失 |
| D015 | _GEO_TOOLS 补 ensure_zone·修 F3 门禁误判 |

### 模块三：Execution Layer

| ID | 决策 |
|----|------|
| D016 | 统一 observation 格式 [OK]/[ERR]/[WARN] + 实际参数 + 明确单位 |
| D017 | generateHeatmapForAI 接入 computeStyle·density 补 analysis 映射 |
| D018 | focusLayer 父组空 FC 时返子层·修 Overview「0 条」 |

### 模块四：FinalStep Agent

| ID | 决策 |
|----|------|
| D019 | 保 LLM·轻 prompt ~0.6-1.3KB·耗时 3-5s |
| D020 | 追问胶囊三级——L1 直达·L2 轻判·L3 走 CPD |
| D021 | 胶囊绑定工具集·参数从 observation 派生 |

### 模块五：Review + Revise

| ID | 决策 |
|----|------|
| D022 | 删除旧 R+R 全部代码 |
| D023 | 新质量防线三层·全部代码 <20ms |
| D024 | 旧 R+R episode 日志迁至新防线 |

### 模块六：Prompt Engineering

| ID | 决策 |
|----|------|
| D025 | tool_contracts.py 单一真相源 |
| D026 | Flash/Pro/finalStep prompt 从 contracts 派生 |
| R1 | rank `by` 默认值 `'polarity'` → `'worst'` |

### 模块七：Toolbox ↔ EMC

| ID | 决策 |
|----|------|
| D027 | generate*ForAI 15 个全审计·契约完整 |
| D028 | 保留 enforceMutualExclusion·增隐藏提示+空组隐藏 |
| D029 | ForAI=dialog 镜像通过 contracts+CI 校验落地 |

### 模块八：CPD 引擎

| ID | 决策 |
|----|------|
| D030 | CPD 不调 LLM·内容来自 Pro plans |
| D031 | CPD 选项点击后直接执行·跳过 Flash |
| D032 | 已执行选项自动移除·剩余继续 |
| D033 | 全部执行后展示完成·不进一步建议 |
| D034 | 用户偏好记入自我成长·优化 Pro 排序 |

### 模块九：字段识别

| ID | 决策 |
|----|------|
| D035 | 字段→候选工具·分析型优先排序·截断到 4 |
| D036 | 关键词累积匹配·取并集 |
| D037 | 候选为空→短路·提示导入数据 |
| D038 | 候选≥5→追问·6 场景预写模板 |
| D039 | 追问文案纯中文+专业术语·不调 LLM |
| D040 | density analysis 维度分歧单独追问 |

---

## 三、耗时对比

| 场景 | 改造前 | 改造后 | 改善 |
|------|:---:|:---:|:---:|
| 简单请求（单卡·如"生成热力图"） | 50-95s | **8-10s** | 87% |
| 复杂请求（多卡+Pro·如"分析西陵区"） | 50-95s + 超时风险 | **13-20s** | 75% |
| CPD 多轮（连续分析） | 不可用 | **每轮 5-8s** | — |

---

## 四、删除清单

| 组件 | 理由 |
|------|------|
| `review.py` + `reviewStep` + `reviseStep` + `REVISE_TEMPLATE` | D022·旧 R+R 全部删除 |
| `CHAIN_REGISTRY` 固定链 | D012·Pro 动态 chain 替代 |
| `_tplHitRateReady` Flash 命中率 gate | D006·新架构不需要 |
| MANIFESTO §1-11 | D006/D009·领域知识由 contracts 替代 |
| `_DIAGNOSE_FEW_SHOT` 6 个示例 | D006·缩至 1 个 |
| industry_kb 在 Flash/finalStep 中注入 | D006/D019·移除 |

---

## 五、自我成长（未来开发）

| 项目 | 当前状态 |
|------|:---:|
| tool_contracts 自动同步（contracts → SKILL_DEFS → prompt） | ⬜ |
| recipes 基于运行时日志优化 | ⬜ |
| Pro chain 质量反馈闭环 | ⬜ |
| CPD 用户偏好 → Pro 排序优化 | ⬜ |
| DAG 并行链执行 | ⬜ |
| PANEL_MISSING 监控 | ⬜ |

---

## 六、实施建议

| 优先级 | 模块 | 理由 |
|:---:|------|------|
| **P0** | 模块三（执行层） | 消除结论矛盾·最小改动最大收益 |
| **P0** | 模块五（删除旧 R+R） | 删除死代码·零风险 |
| **P1** | 模块四（finalStep 轻 prompt） | 削减最大瓶颈·25-50s→3-5s |
| **P1** | 模块一（Flash 瘦身） | 25-45s→<5s |
| **P2** | 模块二（编排器改造） | 动态 chain + 降级 |
| **P2** | 模块九（字段识别追问） | 候选≥5 的体验改善 |
| **P3** | 模块一（Pro 推理） | 多卡路径·需要 Flash+编排器先就位 |
| **P3** | 模块八（CPD 改造） | 依赖 Pro plans 产出 |
| **P4** | 模块六（contracts 单一源） | 基础设施·无运行时收益·但消除维护债 |
| **P4** | 模块七（ForAI 镜像 CI） | 同上 |

---

## 七、跨模块补充设计

### 7.1 多轮对话上下文传递

```
轮1: 字段识别 → Flash → Pro → plans[5项]
     → 执行rank=1 → finalStep
     → plans存入turnHistory (rank=1标记executed)

轮2: 用户点CPD选项 → 跳过Flash+Pro → 直接执行
     → 该plan标记executed → CPD移除

数据变化判断: 图层数变 / 字段角色变 / 用户主动要求"重新分析" → 清空plans[]·重新走完整管线
```

### 7.2 异常恢复（统一降级链路·永不出现「请求失败」）

| 失败层 | 降级策略 |
|------|------|
| 0LLM | 候选集=全部工具 → Flash 从 13 个中填卡 |
| Flash | 取第一个候选工具 + 默认参数 → 跳过 Pro 直接执行 |
| Pro | 取 Flash 信息卡中 confidence 最高 → 直接执行 |
| 工具执行 | observation=`[ERR]` + 原因 → finalStep 诚实报告 |
| finalStep | 纯 observation 展示（不经 LLM 翻译）·保留追问胶囊 |
| 质量防线 | R1/R4 硬拦截触发 → 纯 observation 展示 |

### 7.3 前后端 contracts 同步

```
tool_contracts.py (Python 单一源)
  → build_js_contracts.py (构建脚本)
  → stages_contracts.js (自动生成 JSON)
  → stages.js import 使用
```

CI 校验：`validate_contracts_sync.py` 对比 Python ↔ JS 两端——不一致即报错。

---

*全 9 模块·43 条决策·跨模块 3 项补充·定稿*
