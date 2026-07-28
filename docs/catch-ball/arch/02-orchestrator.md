# 模块二：Orchestrator（编排层）— v2 改良混合架构

> **状态**：✅ 已决议（v2）  
> **日期**：2026-07-28  
> **关联决策**：D050-D051（v2）·D012-D015（v1·部分保留）

---

## 一、v1 → v2 变更

| 维度 | v1 | v2 |
|------|------|------|
| 输入来源 | diagnose card 的 template + params | **function call 的 tool_calls** |
| 工具查找 | SKILL_DEFS[template] → tool name | **直接用 tool_calls[0].function.name** |
| 参数来源 | diagnose card params + SKILL_DEFS 默认值 | **tool_calls[0].function.arguments** |
| 参数别名 | _PARAM_ALIAS 全局+按工具 | **废弃**——契约 Schema additionalProperties:false |
| 多工具 | Pro plans chain | **rank=1 单 tool_call 执行·plans[] 交 CPD** |

## 二、v2 架构

```
LLM 响应:
  tool_calls: [{ name, arguments }]    ← 1 个（rank=1）
  content: plans[] JSON                ← CPD 素材

编排器入口:
  parse tool_calls[0].function.arguments → params
  runTemplatePath(tool_name, params)     ← 单工具直执

多工具场景:
  LLM 只输出 1 个 tool_call（最优先）
  其余放 plans[] content → CPD 展示 rank=2+
  用户点 CPD 选项 → 编排器再执行（同一路径）
```

## 三、三个关键决策

### Q1：tool_calls 数量

**决策：LLM 只输出 1 个 tool_call（rank=1）**

- prompt 指令明确要求：「输出 1 个 tool_call（最优先执行的工具）」
- 其余候选放 content 的 plans[] JSON
- 语义清晰：tool_calls = 现在执行·plans[] = 后续引导
- 回答结束时追问 rank=2~3 相关内容（消费 plans → 接入 CPD）

### Q2：arguments 解析

**决策：JSON.parse(tool_calls[0].function.arguments)**

- DeepSeek V4 标准：arguments 是 JSON 字符串
- 编排器解析为对象后传给 TOOLS[name](params)
- 契约 Schema strict 模式保证字符串是合法 JSON

### Q3：_PARAM_ALIAS 废弃

**决策：废弃 _PARAM_ALIAS**

- 契约 Schema 参数名以**工具实际读取的参数名为准**
  - buffer 用 `radius_m`（工具内部读 params.radius_m）
  - density 用 `radius`（工具内部读 params.radius）
- strict + additionalProperties:false 禁止 LLM 填别名
- 从源头消灭参数名漂移——不靠 alias 桥接

## 四、保留不变（v1）

| 组件 | 状态 | 理由 |
|------|:---:|------|
| while-loop 降级（D013） | ✅ | 异常兜底·罕见触发 |
| _GEO_TOOLS 补 ensure_zone（D015） | ✅ | F3 门禁修复 |
| runChainPath 逻辑 | ⚠️ | 保留但少用——v2 中多步通过 CPD 逐轮执行·非一次 chain |

## 五、决策

| ID | 决策 |
|----|------|
| D050 | 编排器入口改为消费 tool_calls[0]·不再查 SKILL_DEFS |
| D051 | _PARAM_ALIAS 废弃·契约 Schema additionalProperties:false·参数名以工具实际读取为准 |
| D057 | LLM 只输出 1 个 tool_call（rank=1）·其余进 plans[] |
| D058 | arguments JSON.parse 解析·契约 Schema strict 保证合法性 |
| D062 | **新增**：编排器加代码层参数校验（strict 实测不强制·必须兜底） |

### D062 详解：代码层参数校验

```javascript
// 编排器：tool_calls 解析后、执行前
function validateToolCall(toolName, args) {
  const contract = TOOL_CONTRACTS[toolName];
  if (!contract) return { ok: false, error: `未知工具: ${toolName}` };
  for (const param of contract.params) {
    if (param.required && args[param.name] == null) {
      return { ok: false, error: `缺少必填参数: ${param.name}` };
    }
    if (param.values && args[param.name] && !param.values.includes(args[param.name])) {
      // 参数值不在枚举中 → 用默认值替代（而非报错）
      if (param.default) {
        args[param.name] = param.default;
      } else {
        return { ok: false, error: `参数 ${param.name}=${args[param.name]} 不在合法值域` };
      }
    }
  }
  return { ok: true };
}
```

**触发时**：tool_calls 解析后、`TOOLS[name](params)` 前。  
**失败时**：参数非法且无默认值 → observation=`[ERR]` → finalStep 诚实报告 → 追问胶囊建议调整。

---

*关联文档：README.md·01-diagnose-agent.md（v2）·SCAN_PostImpl_deepseek_2026-07-28.md*
