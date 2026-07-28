# 模块六：Prompt Engineering — v2 改良混合架构

> **状态**：✅ 已决议（v2）  
> **日期**：2026-07-28  
> **关联决策**：D052-D053（v2）·D025-D026（v1·修订）

---

## 一、v1 → v2 变更

| 维度 | v1 | v2 |
|------|------|------|
| contracts 派生目标 | paradigm / prompts / SKILL_DEFS | **契约 Schema（核心）** + 旧目标过渡期保留 |
| diagnose prompt | 30-54KB（MANIFESTO + 8 附录 + 6 few-shot） | **删除**·保留极简 fallback |
| SKILL_DEFS | 编排器查工具+默认值 | **废弃**（D050） |
| function calling | 不使用 | **核心机制** |

## 二、契约 Schema 派生

### 2.1 派生函数

```python
# tool_contracts.py 新增
def contracts_to_tools_schema(tool_names: list = None) -> list:
    """从 contracts 派生 function calling 的 tools 参数格式。
    
    tool_names: 0LLM 的 tools_hint（优先注入完整 schema 的工具子集）
    返回: [{ type:"function", function:{ name, description, strict, parameters } }]
    """
```

### 2.2 参数名规则

**契约 Schema 中的参数名以工具实际读取的参数名为准**——从源头消灭别名：

| 工具 | 契约 Schema 参数名 | 工具内部读取 | 一致性 |
|------|------|------|:---:|
| density | `radius` | params.radius | ✅ |
| buffer | `radius_m` | params.radius_m | ✅ |
| density | `cell_size` | params.cell_size | ✅ |

**不再需要 _PARAM_ALIAS 桥接**（D051）。

### 2.3 strict 模式保障

```json
{
  "strict": true,
  "parameters": {
    "additionalProperties": false,
    "required": ["analysis", "polarity", "mode"]
  }
}
```

- `strict: true` → 服务端验证 JSON Schema
- `additionalProperties: false` → 禁止 LLM 填 schema 外的参数名
- `required` → 必填参数 LLM 不能漏

## 三、旧 diagnose prompt 处理

### 3.1 删除清单

| 组件 | 大小 | 处理 |
|------|:---:|:---:|
| MANIFESTO 全文注入 diagnose | ~12KB | 删除 |
| DIAGNOSE_TEMPLATE 8 字段 | ~6KB | 删除 |
| 8 个附录（范式/出口/工具目录...） | ~10KB | 删除 |
| industry_kb 注入 diagnose | 5-20KB | 删除 |
| 6 个 few-shot | ~3KB | 删除 |
| **合计删除** | **~36-51KB** | |

### 3.2 极简 fallback 保留

**当 function calling 失败时（DeepSeek V4 偶有空响应/循环调用），退回 prompt 模拟模式。**

```
fallback prompt（~1KB·仅在 function calling 失败时使用）:

"你是情绪地图分析助手。根据用户问题选择一个工具并填写参数。

可用工具:
{tools_hint 的精简 schema}

用户问题: {question}
数据上下文: {grounding}

输出 JSON:
{ "tool": "工具名", "arguments": {...}, "plans": [...] }
"
```

**触发条件**：
- function calling API 返回空 tool_calls
- function calling API 超时
- function calling 返回非法 JSON（strict 应该不会·但兜底）

**fallback 不走 function calling**——纯 prompt + JSON 输出 + 代码解析。质量略低但保证可用。

## 四、新旧派生目标对照

| 派生目标 | v1 角色 | v2 角色 | 状态 |
|------|------|------|:---:|
| **契约 Schema（tools 参数）** | ❌ 不存在 | function calling 核心 | ✅ 新增 |
| paradigm.py TEMPLATE_REGISTRY | Flash 选型 | 无用 | ⚠️ 过渡保留 |
| prompts.py diagnose 段 | Flash prompt | 删除（保留 fallback） | ⚠️ 精简 |
| SKILL_DEFS | 编排器查工具 | 废弃 | ❌ 删除 |
| prompts.py FINAL_TEMPLATE | finalStep | 不变 | ✅ 保留 |
| prompts.py fallback prompt | ❌ 不存在 | function calling 失败兜底 | ✅ 新增 |

## 五、决策

| ID | 决策 |
|----|------|
| D052 | contracts 新增 contracts_to_tools_schema() 派生契约 Schema |
| D053 | paradigm.py / SKILL_DEFS 过渡期保留·逐步废弃 |
| D059 | 旧 diagnose prompt（MANIFESTO + 8 附录 + 6 few-shot）删除 |
| D060 | 保留极简 fallback prompt（~1KB）·function calling 失败时退回 |
| D061 | 契约 Schema 参数名以工具实际读取为准·消灭别名 |

---

*关联文档：README.md·01-diagnose-agent.md（v2）·02-orchestrator.md（v2）*
