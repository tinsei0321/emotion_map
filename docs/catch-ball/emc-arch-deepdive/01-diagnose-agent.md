# 模块一：Diagnose Agent（认知层）— v2 改良混合架构

> **状态**：✅ 已决议（v2）  
> **日期**：2026-07-28  
> **参与**：用户 + DeepSeek  
> **版本说明**：v1（2026-07-27）三阶段设计经业界对标（kepler.gl/Mapbox/Power BI）后修订为 v2 改良混合架构。废弃「信息卡」概念，引入「契约 Schema」。  
> **关联决策**：D001-D011（v1·已废弃）→ D041-D049（v2）

---

## 一、v1 → v2 变更说明

| 维度 | v1（三阶段） | v2（改良混合） | 变更理由 |
|------|------|------|------|
| 认知架构 | 0LLM → Flash 填信息卡 → Pro 推理 | **0LLM → 单次 LLM + function calling** | 业界主流（kepler.gl/Mapbox）是单 LLM + function calling·非多阶段管线 |
| LLM 调用次数 | 2-3 次（Flash + Pro + finalStep） | **1-2 次**（function call + finalStep） | 减少串行延迟 |
| 信息卡 | Flash 产出·Pro 消费 | **废弃**——职能被契约 Schema + function calling strict 覆盖 | strict schema 服务端强制·比 Flash 自由 JSON 更可靠 |
| 参数约束 | Flash prompt 中描述 schema | **契约 Schema**（contracts → JSON Schema → tools 参数） | DeepSeek V4 原生支持 function calling + strict 验证 |
| 工具选择 | 0LLM 硬筛选候选集 | 0LLM **软建议**（tools_hint）+ LLM 自主选 | 硬筛选有漏选风险·不可恢复 |
| plans[] | Pro 产出 | **function call 响应中附带**（content 字段 JSON） | 单次调用同时获得执行指令 + CPD 引导素材 |
| Pro 阶段 | 独立第二次 LLM 调用 | **取消**——function calling 内部完成推理 | 简化架构·减少延迟 |

---

## 二、v2 架构

```
用户 NL
  │
  ▼
┌─ Stage 1: 0LLM ───────────────────────────── <100ms
│  纯代码·不调 LLM                                
│  ├─ 字段识别 → 语义角色（field_dictionary）     
│  ├─ 构建接地上下文（图层名+字段+值域样本）       
│  │  ⚠️ 只发元数据·不发原始数据（kepler.gl 模式） 
│  ├─ tools_hint：基于字段+关键词动态选择优先注入 
│  │  完整 schema 的工具子集（2-4 个）             
│  └─ tools_fallback：其他工具的精简列表           
│     （name + 一句话描述·在 system prompt 提及）  
│  产出：{ grounding, tools_hint, tools_fallback } 
└─────────────────────────────────────────────────┘
  │
  ▼
┌─ Stage 2: LLM + Function Calling ───────── 3-8s
│  单次调用·DeepSeek V4·原生 function calling      
│                                                  
│  输入:                                            
│    tools 参数: tools_hint 对应的完整契约 Schema    
│    system prompt: 接地上下文 + tools_fallback 提及 
│                    + 用户 NL                       
│                                                  
│  LLM 内部完成（黑盒·由 strict schema 约束）:      
│    - 理解意图                                     
│    - 评估候选工具                                 
│    - 选工具 + 填参数（enum/范围服务端强制）         
│    - 排优先级 + 产出 plans[]                       
│                                                  
│  输出:                                            
│    tool_calls: [{ name, arguments }]  ← 执行指令  
│    content: plans[] JSON              ← CPD 素材  
│      [{ rank, label, tool, params,                   
│         confidence, rationale }]                     
└─────────────────────────────────────────────────┘
  │
  ├─ tool_calls → 编排器（模块二）执行 rank=1
  └─ plans[] → CPD（模块八）展示 rank=2+
  │
  ▼
finalStep（模块四）→ 质量防线（模块五）
```

**总耗时**：0LLM(<100ms) + LLM(3-8s) + finalStep(3-5s) = **6-13s**

---

## 三、契约 Schema（核心机制）

### 3.1 定义

> **契约 Schema = tool_contracts.py 派生的 JSON Schema，注入 function calling 的 tools 参数，通过 strict 模式强制 LLM 只能填情绪地图专用工具的合法参数值。**

### 3.2 参数约束链路

```
tool_contracts.py（开发者维护·单一真相源）
  │
  │  contracts_to_tools_schema()（派生函数）
  ▼
契约 Schema（JSON Schema 格式）
  │
  │  注入 function calling 的 tools 参数（strict: true）
  ▼
DeepSeek V4（服务端验证 JSON Schema）
  │
  │  LLM 只能填合法值·非法值被 API 拒绝
  ▼
tool_calls: [{ name:"density", arguments:{ analysis:"negative", polarity:"N" } }]
  │
  │  编排器取 arguments
  ▼
generateHeatmapForAI(analysis="negative", polarity="N")
  │
  │  computeStyle(analysis, polarity) → rampKey
  ▼
出图（消极热力图·red-3 色板·符合情绪地图规范）
```

### 3.3 契约 Schema 示例（density 工具）

```json
{
  "type": "function",
  "function": {
    "name": "density",
    "description": "情绪地图·核密度/热力图/网格聚合。综合/总体→analysis=terrain；积极→positive；消极→negative；中性→neutral",
    "strict": true,
    "parameters": {
      "type": "object",
      "properties": {
        "analysis": {
          "type": "string",
          "enum": ["terrain", "positive", "negative", "neutral"],
          "description": "terrain=综合彩虹·positive/negative/neutral=极性细分"
        },
        "polarity": {
          "type": "string",
          "enum": ["ALL", "P", "N", "O"],
          "description": "ALL=综合·P=积极·N=消极·O=中性。须与 analysis 联动"
        },
        "mode": {
          "type": "string",
          "enum": ["2d", "3d", "terrain"],
          "description": "2d=彩虹热力图·3d=网格聚合·terrain=3D KDE"
        },
        "level": {
          "type": "string",
          "enum": ["L1", "L2", "L3", "L4"]
        },
        "cell_size": {
          "type": "number",
          "minimum": 50,
          "maximum": 5000,
          "description": "网格边长(米)·仅 mode=3d 时生效"
        },
        "radius": {
          "type": "number",
          "minimum": 50,
          "maximum": 3000,
          "description": "热力半径(米)·仅 mode=2d 时生效"
        }
      },
      "required": ["analysis", "polarity", "mode"],
      "additionalProperties": false
    }
  }
}
```

### 3.4 契约 Schema 保证的制式化要素

| 你的要求 | 契约 Schema 的保障 |
|------|------|
| 参数输入稳定（在设定范围内） | ✅ JSON Schema enum + range + strict 服务端强制 |
| 情绪地图专属字段（analysis/polarity） | ✅ contracts 中定义·enum 约束合法值 |
| 参数联动（analysis=negative → polarity=N） | ✅ description 引导 + computeStyle 兜底 |
| 图例样式稳定 | ✅ computeStyle(analysis, polarity) 锁定 rampKey |
| 出图规则稳定 | ✅ generateHeatmapForAI 复用 Toolbox dialog 同一套逻辑 |
| 色板制式化 | ✅ 契约 Schema 不暴露 rampKey·由 computeStyle 内部决定 |

---

## 四、Stage 1: 0LLM 详细设计

### 4.1 职责边界

| 0LLM 应该做 | 0LLM 不应该做 |
|------|------|
| ✅ 字段识别 → 语义角色 | ❌ 候选工具硬筛选（漏选风险） |
| ✅ 构建接地上下文（元数据·不发原始数据） | ❌ 决定 LLM 能看到哪些工具 |
| ✅ tools_hint（基于字段+关键词·优先注入完整 schema） | ❌ 替 LLM 做任何决策 |
| ✅ tools_fallback（其他工具精简列表） | ❌ 任何 LLM 推理 |
| ✅ 数据缺失检测（无数据→短路提示导入） | |

### 4.2 tools_hint vs tools_fallback

```
0LLM 产出:
  tools_hint: [density, hotspot, zonal_stats]  ← 完整 schema 注入 function calling
  tools_fallback: [clip, buffer, rank, ...]    ← 精简列表在 system prompt 提及

LLM 收到:
  tools 参数: [density 完整schema, hotspot 完整schema, zonal_stats 完整schema]
  
  system prompt 末尾:
    "其他可用工具（如需可要求）: clip(裁切), buffer(缓冲), rank(排序),
     merge(合并), overlay(叠置), area_stats(面积统计), nearest(最近邻),
     extract_feature(抽取), filter_attr(筛选), compare_regions(区域对比)"
```

**效果**：
- 常用工具完整 schema 在 tools 参数中（function calling 原生支持 + strict 约束）
- 非常用工具在 prompt 中提及（LLM 知道存在·可主动要求·但需多一轮交互）
- 0LLM 不阻断 LLM 的选择能力——只是让常用工具更快被选

### 4.3 tools_hint 选择规则

```javascript
// 基于字段角色
FIELD_TO_TOOLS = {
  polarity:         ['density', 'zonal_stats', 'rank', 'hotspot'],
  score:            ['density', 'zonal_stats', 'rank', 'hotspot', 'buffer'],
  emotion_type:     ['density'],
  boundary_name:    ['zonal_stats', 'area_stats', 'clip', 'merge'],
};

// 基于关键词（累积匹配·取并集）
KEYWORD_TO_TOOLS = {
  '热力图': ['density'], '密度': ['density'], '网格': ['density'],
  '排序': ['rank'], '最差': ['rank'],
  '归因': ['zonal_stats'], '裁出': ['clip'],
  '对比': ['compare_regions'], '热点': ['hotspot'],
  '缓冲': ['buffer'], '周边': ['buffer'],
};

// 候选 = 字段角色工具 ∪ 关键词工具·取前 4 个（分析型优先）
```

---

## 五、Stage 2: LLM + Function Calling 详细设计

### 5.1 输入

```
POST /chat/completions
{
  "model": "deepseek-v4-flash",
  "messages": [
    { "role": "system", "content": "{接地上下文} + {tools_fallback 提及} + {指令}" },
    { "role": "user", "content": "生成 L2 消极点的热力图" }
  ],
  "tools": [ 契约 Schema × 2-4 个 ],
  "tool_choice": "auto",
  "strict": true
}
```

### 5.2 输出（两种信息并存）

```json
{
  "content": "{\"plans\":[{\"rank\":1,\"label\":\"消极热力图\",\"tool\":\"density\",\"params\":{\"analysis\":\"negative\",\"polarity\":\"N\"},\"confidence\":\"high\",\"rationale\":\"用户明确说消极\"},{\"rank\":2,\"label\":\"消极区排序\",\"tool\":\"rank\",\"params\":{\"by\":\"worst\"},\"confidence\":\"medium\"}]}",
  "tool_calls": [
    {
      "id": "call_xxx",
      "type": "function",
      "function": {
        "name": "density",
        "arguments": "{\"analysis\":\"negative\",\"polarity\":\"N\",\"mode\":\"2d\",\"level\":\"L2\"}"
      }
    }
  ]
}
```

| 字段 | 消费方 | 用途 |
|------|------|------|
| `tool_calls` | 编排器 | 取 rank=1 执行 |
| `content.plans[]` | CPD | 展示 rank=2+ 为引导选项 |
| `content.plans[].confidence` | 调试/日志 | 排查 LLM 选择质量 |

### 5.3 LLM prompt 精简（关键改进）

| 组件 | 当前（v1 diagnose） | v2 |
|------|:---:|:---:|
| MANIFESTO 全文 11 节 | ~12KB | **0**（移除） |
| DIAGNOSE_TEMPLATE 8 字段 | ~6KB | **0**（function calling 替代） |
| 6 个附录（范式/出口/工具目录...） | ~10KB | **0**（契约 Schema 替代） |
| industry_kb | 5-20KB | **0**（移除） |
| 6 个 few-shot | ~3KB | **0**（function calling 不需要示例） |
| 接地上下文 | 2-8KB | **精简到 0.5-2KB**（只元数据） |
| tools_fallback 提及 | — | **~0.3KB** |
| **合计** | **30-54KB** | **~1-3KB** |

**prefill 从 20-35s 降到 <2s。**

---

## 六、plans[] 结构

```typescript
interface Plan {
  rank: number;           // 优先级（1=执行·2+=CPD选项）
  label: string;          // 中文标签（CPD 展示用）
  tool: string;           // 工具名
  params: object;         // 参数（符合契约 Schema）
  confidence: "high" | "medium" | "low";
  rationale: string;      // LLM 选择理由（调试用）
}
```

### 消费规则

| 消费方 | 取什么 | 做什么 |
|------|------|------|
| 编排器 | rank=1 的 tool + params | 直接执行·不经第二次 LLM |
| CPD | rank=2+ 的全部 | 展示为可点击引导选项 |
| finalStep | rank=1 的 label | 生成追问胶囊提示 |
| 调试日志 | 全部 confidence + rationale | 排查 LLM 选择质量 |

### 跨轮复用（模块八 CPD）

```
轮1: LLM 产出 plans[5项] → 执行 rank=1 → plans 存入 turnHistory
轮2: 用户点 CPD 选项(rank=3) → 直接执行·不走 LLM → rank=3 标记 executed
数据变化: 图层/字段变了 → 清 plans[] → 重新走 LLM
```

---

## 七、异常处理

| 失败层 | 降级策略 |
|------|------|
| 0LLM 字段识别失败 | tools_hint = 全部 13 个工具（LLM 从全量选） |
| LLM function call 超时 | 降级——取 tools_hint[0] + 默认参数 → 直接执行 |
| LLM 返回非法参数 | strict schema 已拦截·API 层报错 → 重试一次 |
| LLM 未返回 plans[] | CPD 无选项可展示·finalStep 仍正常出结论 |
| LLM 选错工具 | 质量防线（模块五）检测 observation 矛盾 → 降级展示 |

**统一原则**：永不出现「请求失败」——地图有图层 + 对话区有 observation。

---

## 八、决策记录

| ID | 决策 | v1 对照 | 验证依据 |
|----|------|------|------|
| D041 | 架构改为单次 LLM + function calling + 契约 Schema | 修订 D001 | 测试1 ✅ |
| D042 | 废弃信息卡·参数约束由契约 Schema 承担 | 修订 D002/D003 | — |
| D043 | 契约 Schema 从 tool_contracts.py 派生·strict 标记保留 | 新增 | 测试2/4: strict 不强制 |
| D044 | 0LLM 不做工具筛选·全注入 13 工具 schema | 修订 D007 | 测试3: 7.4KB/2.7s |
| D045 | plans[] 在 function call content 字段附带产出 | 修订 D003 | 测试1: 并存 ✅ |
| D046 | LLM prompt 从 30-54KB 缩至 1-3KB·prefill <2s | 修订 D006 | 测试3: 2.7s |
| D047 | 数据三态判断在 LLM function calling 内完成 | 修订 D008 | — |
| D048 | 单工具直执·多工具 plans 交 CPD·取消 Pro 阶段 | 修订 D004/D009 | — |
| D049 | 数据缺失→0LLM 短路提示导入 | 保留 | — |
| D062 | **新增**：编排器加代码层参数校验（strict 不强制） | — | 测试2/4 ❌ |
| D063 | **新增**：废弃 tools_hint·全注入 13 工具 | 修订 D044 | 测试3: 全注入 2.7s |

---

## 九、和业界对标

| 平台 | 我们的对应 |
|------|------|
| kepler.gl：单 LLM + function calling + 元数据接地 | ✅ 完全一致 |
| kepler.gl：原始数据不发 LLM | ✅ 接地上下文只元数据 |
| Power BI：语义层是核心 | ✅ contracts（契约 Schema 源）= 语义层 |
| Mapbox：MCP 工具服务器 | ⚠️ 我们是内嵌 tools·非 MCP·但模式相同 |
| kepler.gl：用户确认参数后执行 | ⚠️ 我们自动执行·未来可加确认步骤 |

---

*关联文档：README.md·CB-04 全量 SCAN·kepler.gl AI 文档·DeepSeek function calling 文档*
