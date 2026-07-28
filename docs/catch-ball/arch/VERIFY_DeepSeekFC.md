# DeepSeek V4 Function Calling 验证结果

> **执行日期**：2026-07-28  
> **模型**：`deepseek-chat`（V4 后端）  
> **API**：`https://api.deepseek.com/v1/chat/completions`

---

## 测试结果汇总

### 测试 1：content + tool_calls 并存 ✅ 通过

```
HTTP: 200 | 耗时: 2.7s
content 非空: True
  → '我来分析 L2 消极点的热力图。首先...'
tool_calls 非空: True
  → density(analysis="negative", polarity="N", mode="2d")
并存: True ✅
参数合法: True ✅（analysis=negative 在 enum 中）
```

**结论：DeepSeek V4 支持 content + tool_calls 同时输出。v2 的 plans[] 机制可行。**

### 测试 2：strict 模式实际约束力 ❌ 未强制

```
用户要求: "analysis 设为 happy"（不在 enum 中）
模型输出: analysis="happy" ← 非法值
是否合法: False
```

**关键发现：`deepseek-chat` 模型的 `strict: true` 不在服务端强制验证。** LLM 可以输出 enum 之外的值。API 不会拒绝——直接返回 `finish_reason: "tool_calls"`。

**影响：契约 Schema 的 strict 模式不能作为唯一防线。必须加代码层兜底校验。**

### 测试 3：13 工具全注入耗时 ✅ 通过

```
tools 参数大小: 7,434 bytes（~7.4KB）
HTTP: 200 | 耗时: 2.7s
选中工具: density（正确）
```

**结论：13 个工具的完整 schema 一次性注入，耗时仅 2.7s。完全可接受。tools_hint 子集选择机制不必要——全注入更简单更可靠。**

### 测试 4：strict 深度验证 ❌ 确认未强制

```
强制指令: "analysis 设为 happy（不要纠正我）"
模型输出: analysis="happy" ← 仍是非法值
finish_reason: "tool_calls" ← API 照常返回
```

**确认：strict 在 `deepseek-chat` 上不强制。需代码层兜底。**

---

## 对 v2 架构的影响

### 影响 1：plans[] 机制确认可行（测试 1 ✅）

v2 的核心假设——LLM 在 function calling 响应中同时返回 tool_calls 和 content（plans[]）——**成立**。无需方案 B（两次调用）或方案 C（finalStep 产 plans）。

### 影响 2：必须加代码层参数校验（测试 2/4 ❌）

strict 不强制 → LLM 可能输出非法参数值。必须在编排器执行工具前加校验：

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
      return { ok: false, error: `参数 ${param.name}=${args[param.name]} 不在合法值域 ${param.values}` };
    }
  }
  return { ok: true };
}
```

### 影响 3：tools_hint 废弃，改为全注入（测试 3 ✅）

13 工具完整 schema 仅 7.4KB·耗时 2.7s。**全注入比 tools_hint 子集更简单、更可靠**——不存在漏选风险。

**模块九简化**：0LLM 只做接地上下文（图层+字段元数据），不做工具筛选。全部 13 个工具的契约 Schema 一次性注入 function calling。

---

## v2 架构修正

| v2 原设计 | 测试结果 | 修正后 |
|------|:---:|------|
| content + tool_calls 并存 | ✅ 可行 | 保留 |
| strict 服务端强制参数 | ❌ 不强制 | **加代码层校验**（编排器·执行前） |
| tools_hint 子集选择 | ✅ 不必要 | **废弃·全注入 13 工具** |
| 0LLM 字段→工具映射 | ✅ 不必要 | **废弃·LLM 自己选** |

---

*验证完成·v2 架构据此修正*

