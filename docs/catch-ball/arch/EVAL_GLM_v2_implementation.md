# GLM 评估 · v2 实施计划与关键细节（供第三方实施参考）

> **评估方**：GLM（Claude Code·EMC v1 实施者）  
> **日期**：2026-07-28  
> **评估对象**：v2 改良混合架构（单次 LLM + function calling + 契约 Schema）  
> **阅读范围**：emc-arch-deepdive 全部 v2 文档（01/02/06/08/09 + SUMMARY 61 决策 + VERIFY + SCAN×2 + GLM_FINAL_PROMPT）  
> **用途**：第三方实施者参考——v2 架构判断 + 精确实施步骤 + 关键技术细节 + 验证标准

---

## 一、架构判断：✅ v2 方向正确·同意实施

### 1.1 v2 核心优势（实测支撑）

| 优势 | 证据 |
|------|------|
| **消灭选型类问题** | LLM 直接看全 13 工具 + grounding·原生选型（不再 v1 的 select_candidates 关键词猜 + 数据盲 + trigger 脆弱 + 候选锁定） |
| **更简** | 1 次 FC 调用取代 v1 三阶段（0LLM→Flash 填卡→Pro）+ 其所有接线（dispatch / FILL_CARD / PLAN / filter / stale multi） |
| **更可靠** | DeepSeek V4 原生 function calling（结构化 tool_calls）> v1 解析自由 JSON 卡 |
| **业界对标一致** | kepler.gl / Mapbox / Power BI = 单 LLM + FC + 语义层（[SCAN_PostImpl §三](SCAN_PostImpl_deepseek_2026-07-28.md)） |

### 1.2 v1 实现状态（⚠️ 第三方须知）

[SCAN_PostImpl](SCAN_PostImpl_deepseek_2026-07-28.md) 说模块一/九 "0% 实现"——这是**办公机**（git 停在 5.234）的审计。实际 v1 已落地（5.235-5.242·家用机已 push bb6fd99）：
- candidate_selector.py（select_candidates + 数据感知 5.242）
- FILL_CARD / PLAN prompt + dispatch（5.236/5.237）
- 完整 diagnose 管线 + 5.242 数据感知修复（layer_meta / clip 几何表 / stale multi）

**v2 不是修 broken 代码·是替换已实现但复杂的 v1**。第三方实施前**必须 git pull** 拿到最新代码（5.235-5.242）。

### 1.3 保留 vs 替换（~70% v1 代码保留）

| v1 件 | v2 处置 | 理由 |
|------|:---:|------|
| applyQualityDefense（质量防线） | **保留** | 全代码 <20ms·与选型无关 |
| 追问胶囊（runCapsule + renderSuggest） | **保留** | finalStep 产胶囊·与 FC 正交 |
| tool_contracts.py（单一源） | **保留 + 升级** | 派生 JSON Schema → FC tools（D052） |
| TOOLS 工具执行 + runTemplatePath | **保留** | FC 选工具 → 仍走 TOOLS 执行 |
| finalStep（极瘦 prompt 1.86KB） | **保留** | 不变 |
| episode/consolidate（自成长） | **保留** | 不变 |
| field_dictionary（字段识别） | **保留** | 0LLM grounding 用 |
| buildContext（前端 grounding） | **保留** | 不变 |
| **select_candidates** | **废弃** | FC LLM 自主选·无需规则预选 |
| **FILL_CARD / PLAN prompt** | **废弃** | FC tools schema 取代 |
| **dispatch（build_diagnose_prompt_dispatch）** | **废弃** | FC 端点取代 |
| **trigger 规则（_B_TRACK_TRIGGER_EXT 等）** | **废弃** | 无需关键词触发 |
| **SKILL_DEFS / paradigm GEO_TOOL_CATALOG** | **过渡期保留**（D053） | 逐步废弃·编排器 validateParams 暂用 |

---

## 二、v2 全决策速查（D041-D068·影响实施的）

| ID | 决策 | 实施影响 |
|----|------|------|
| D041 | 单次 LLM + FC + 契约 Schema | 新 FC 端点 |
| D042 | 废弃信息卡 | 删 FILL_CARD/PLAN/dispatch |
| D043 | Schema from contracts + strict 标记 | contracts_to_tools_schema |
| D044 | （已被 D063 取代）0LLM 不做硬筛选 | — |
| D045/D054 | plans[] in FC content 字段 | FC 响应解析 |
| D046/D059 | diagnose prompt 删除（36-51KB） | 删旧 prompt |
| D047 | 数据三态在 FC 内完成 | LLM system prompt 指令 |
| D048 | 单工具直执·取消 Pro 阶段 | 删 build_plan_prompt |
| D049 | 数据缺失→0LLM 短路提示导入 | 保留现有短路 |
| D050/D058 | 编排器消费 tool_calls[0]·JSON.parse·不查 SKILL_DEFS | orchestrate 改 |
| D051/D061 | _PARAM_ALIAS 废弃·Schema 参数名=工具实际读名·additionalProperties:false | contracts Schema 对齐 |
| D052 | contracts_to_tools_schema() 派生函数 | 新函数 |
| D053 | paradigm/SKILL_DEFS 过渡期保留·逐步废弃 | 不立即删 |
| D055/D056 | 全注入替代 tools_hint/fallback | 13 工具全注入 |
| D057 | LLM 只输出 1 个 tool_call·其余进 plans[] | FC prompt 指令 |
| D060/D066 | 极简 fallback ~1KB·从 contracts 派生（非手写） | fallback prompt |
| D062 | 编排器代码层参数校验（strict 实测不强制·**非法值用默认值替代·非报错**） | validateToolCall |
| D063/D064 | 全注入 13 工具·废弃 tools_hint·0LLM 只做 grounding + 缺失检测 | 简化 0LLM |
| D065 | 数据变化检测·harness·_dataSignature | 跨轮 plans 清空 |
| D067 | plans[] 解析后代码校验·容错 | plans validate |
| D068 | ctx.plans 共享（编排器/CPD/finalStep） | plans 流转 |

---

## 三、精确实施步骤

### Phase 0 · 机器同步（前置·必须）

```bash
git add -A && git commit -m "docs(emc): v2 架构文档"   # 本地 v2 文档先 commit
git pull origin main                                      # 拉 5.235-5.242（v1 实现 + 5.242 数据感知修复）
# resolve conflict if any（deepdive 文档可能冲突·保留 v2 版）
```

**第三方须知**：此机器（办公机）可能停在 5.234。v2 必须在最新代码（5.235-5.242）上构建——否则 v1 diagnose 管线不存在·无法替换。

### Phase 1 · 后端 FC 基础设施

#### 1.1 `contracts_to_tools_schema()`（[tool_contracts.py](ai_qa/tool_contracts.py)·新·D052）

从 TOOL_CONTRACTS → JSON Schema（[01 §3.3](01-diagnose-agent.md) 格式）：

```python
def contracts_to_tools_schema() -> list:
    """TOOL_CONTRACTS → DeepSeek V4 function calling tools 参数。
    返 [{ type:'function', function:{ name, description, strict:true,
    parameters:{ type:'object', properties:{...}, required:[...], additionalProperties:false } } }]"""
```

**关键细节**：
- **参数名对齐**（D051/D061）：Schema 用工具实际读名（buffer `radius_m` / density `radius`）·与 tool_contracts.py params `name` 一致。
- **polarity enum 对齐**（⚠️）：01 §3.3 示例用 `ALL/P/N/O`·当前 contracts 用 `overall/positive/negative/neutral`·**须统一**。建议保持 contracts 原值（`overall/positive/negative/neutral`）·因为 computeStyle 已适配。Schema enum 从 contracts params 的 `enum` 字段派生。
- **enum/range/required 从 contracts params 派生**：`type`（string/number/bool/source/list）→ JSON Schema type；`enum` → JSON Schema enum；`required:True` → required 数组。
- **additionalProperties:false**（D051）：每个工具 parameters 加此字段·禁别名。
- **description**：从 contracts 的 `when` 或 `voice` 字段派生（给 LLM 的工具说明）。
- **strict:true**（D043）：虽然实测不强制·但标记保留（无害·可能未来 provider 支持）。
- 全 13 GIS 工具（不含 concept/multi/unknown）。

**contracts_to_text()（D066·fallback 用）**：从 contracts 派生纯文本工具列表·注入 fallback prompt·避免双重维护。

#### 1.2 `chat_with_tools()`（[llm.py](ai_qa/llm.py)·新方法·LLMClient 类）

```python
def chat_with_tools(self, messages, tools, tool_choice='auto', stream=False):
    """DeepSeek V4 function calling·非流式·返 { tool_calls, content }。
    body 加 tools/tool_choice·解析 response.choices[0].message.tool_calls + content。"""
    body = {'model': self.model, 'messages': messages, 'tools': tools,
            'tool_choice': tool_choice, 'stream': False}
    # ... POST → parse response.choices[0].message.tool_calls + .content
    return {'tool_calls': tool_calls, 'content': content}
```

**关键细节**：
- 现有 `chat()` body 无 tools·新方法独立（不改 chat 签名）。
- **非流式**（FC 2.7s 一次返完整 tool_calls·不需 SSE）。
- response 格式（[01 §5.2](01-diagnose-agent.md)）：`choices[0].message.tool_calls[0].function.{name, arguments}` + `choices[0].message.content`（plans[] JSON 字符串）。
- arguments 是 **JSON 字符串**（需 JSON.parse·D058）。

#### 1.3 `validateToolCall()`（D062·编排器层）

```python
def validate_tool_call(tool_name, args):
    """strict 不强制→代码兜底。查 TOOL_CONTRACTS：
    - required 缺→补默认值（optional_defaults）
    - enum 外→用默认值替代（非报错·02 §D062 详解）
    - 返 { ok, params, fixes }"""
```

**关键细节**（[02 §D062](02-orchestrator.md)）：
- **非法值→默认值替代**（非 reject·非 error）。更宽容·不因 LLM 输出 ALL/P/N/O vs overall/... 而失败。
- 复用现有 `validateParams`（[stages.js](frontend/js/ai_qa/stages.js#L87)）范式·加默认值替代逻辑。

#### 1.4 Router FC phase（[router.py](ai_qa/router.py)）

```python
elif req.phase == 'fc_diagnose':
    from ai_qa.tool_contracts import contracts_to_tools_schema
    tools = contracts_to_tools_schema()
    client = get_llm_client(tier='flash')   # DeepSeek V4
    result = client.chat_with_tools(messages, tools)
    # 返 JSON: { tool_calls:[{name, arguments}], content_plans:'...' }
    return JSONResponse({ 'tool_calls': result['tool_calls'], 'plans': result['content'] })
```

- **非流式返 JSON**（FC 不需 SSE·前端 fetch await）。
- 现有 `/api/v1/chat` 端点加 phase='fc_diagnose' 分支·或新独立端点。

### Phase 2 · 前端适配

#### 2.1 `fcDiagnoseStep()`（[stages.js](frontend/js/ai_qa/stages.js)·新·替代 diagnoseStep）

```javascript
export async function fcDiagnoseStep(ctx, hooks) {
  const resp = await fetch('/api/v1/chat', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      phase: 'fc_diagnose',
      messages: [...(ctx.history||[]), {role:'user', content: ctx.question}],
      context: ctx.context,   // grounding（buildContext 产出）
    })
  });
  const { tool_calls, plans } = await resp.json();
  if (hooks.onReason) hooks.onReason('Function Calling…', 0);
  // 兼容 orchestrate 的 diagnose 对象
  const tc = tool_calls && tool_calls[0];
  return {
    template: tc ? tc.function.name : 'unknown',   // 工具名（density/clip/...）
    params: tc ? JSON.parse(tc.function.arguments) : {},
    plans: plans,                                    // rank=2+ → CPD/胶囊
    degraded: !tc,
    intent: tc ? 'gis_operation' : 'unknown',
    _fc: true,
  };
}
```

#### 2.2 orchestrate（[harness.js](frontend/js/ai_qa/harness.js)）

```javascript
// 替代 diagnoseStep 调用（:697 附近）
diagnose = await stages.fcDiagnoseStep(ctx, hooks);
// orchestrate 不变：diagnose.template → runTemplatePath（已有逻辑）
// FC 的 template = 工具名（density/clip/...）·params = FC arguments
// runTemplatePath(validateParams → TOOLS[name](params) → finalStep → defense)
```

- **runTemplatePath 几乎不变**：读 diagnose.template + diagnose.params → 执行。
- **废弃路径**：select_candidates / FILL_CARD / PLAN / dispatch / parseDiagnoseCard（FC 取代）。
- **_quickIntent 短路保留**（概念问跳 diagnose·不走 FC）。

#### 2.3 数据变化检测（D065·harness）

```javascript
// harness orchestrate 顶（diagnose 前）
const _sig = getLayers().map(l => `${l.srcId}:${(l.fc?.features||[]).length}:${l.kind}`).join('|');
if (ctx.priorTurn?._dataSig && ctx.priorTurn._dataSig !== _sig) {
  ctx.plans = null;   // 数据变化→清 plans（D065）
}
ctx._dataSig = _sig;  // 存入 trace→turnHistory
```

### Phase 3 · CPD plans[] + FC fallback

#### 3.1 plans[] → 胶囊/CPD（D045/D054/D067/D068）

FC content plans[] → JSON.parse → validate（D067 容错·非法 skip）→ `trace.plans`（ctx.plans 共享 D068）→ renderSuggest 展示 rank=2+（复用胶囊渲染管线·`trace.defense.capsules` 格式兼容）。

**plans[] 消费规则**（[01 §6](01-diagnose-agent.md)）：

| 消费方 | 取什么 | 做什么 |
|------|------|------|
| 编排器 | rank=1 的 tool + params | 直接执行（tool_calls 已含） |
| CPD/renderSuggest | rank=2+ 全部 | 展示为可点击引导选项 |
| finalStep | rank=1 的 label | 生成追问胶囊提示 |
| 调试日志 | 全部 confidence + rationale | 排查 LLM 选择质量 |

#### 3.2 极简 fallback（D060/D066）

FC 失败（网络/超时/无 tool_calls/解析失败）→ 极简 prompt 模式：

```
fallback prompt（~1KB·从 contracts 派生 contracts_to_text()·非手写）:

"你是情绪地图分析助手。根据用户问题选择一个工具并填写参数。
可用工具: {contracts_to_text() 产出}
用户问题: {question}
数据上下文: {grounding}
输出 JSON: { "tool": "工具名", "arguments": {...}, "plans": [...] }"
```

- Flash 跑此 prompt → 输出 JSON → 同 FC 路径解析执行。
- **不退回 v1 大 prompt**（45.8KB 太慢）。

### Phase 4 · 清理（渐进·D053 过渡期保留）

- **废弃**：candidate_selector.py（select_candidates + 全部 trigger/filter 逻辑）/ FILL_CARD_TEMPLATE / PLAN_TEMPLATE / build_diagnose_prompt_dispatch / build_fill_card_prompt / build_plan_prompt。
- **过渡期保留**（D053）：paradigm GEO_TOOL_CATALOG / TEMPLATE_REGISTRY / SKILL_DEFS（编排器 validateParams 暂用·逐步迁移到 contracts 直接校验）。
- **保留**：field_dictionary（0LLM grounding）/ buildContext（前端 grounding）/ DIAGNOSE_TEMPLATE（极简 fallback 用其结构·或独立 fallback prompt）。

---

## 四、关键技术细节（实施者必读）

### 4.1 契约 Schema 示例（density·[01 §3.3](01-diagnose-agent.md)）

```json
{
  "type": "function",
  "function": {
    "name": "density",
    "description": "情绪地图·核密度/热力图。综合→analysis=terrain；消极→negative",
    "strict": true,
    "parameters": {
      "type": "object",
      "properties": {
        "analysis": { "type": "string", "enum": ["terrain","positive","negative","neutral"] },
        "polarity": { "type": "string", "enum": ["overall","positive","negative","neutral"] },
        "mode": { "type": "string", "enum": ["2d","3d","terrain"] },
        "radius": { "type": "number", "minimum": 50, "maximum": 3000 },
        "cell_size": { "type": "number", "minimum": 50, "maximum": 5000 }
      },
      "required": ["analysis", "polarity", "mode"],
      "additionalProperties": false
    }
  }
}
```

### 4.2 FC 响应格式（[01 §5.2](01-diagnose-agent.md)）

```json
{
  "content": "{\"plans\":[{\"rank\":1,\"label\":\"消极热力图\",\"tool\":\"density\",\"params\":{...},\"confidence\":\"high\"},{\"rank\":2,...}]}",
  "tool_calls": [
    { "id": "call_xxx", "type": "function",
      "function": { "name": "density", "arguments": "{\"analysis\":\"negative\",\"polarity\":\"N\"}" } }
  ]
}
```

### 4.3 polarity enum 对齐（⚠️ 实施者注意）

| 来源 | polarity 值 |
|------|------|
| 01 §3.3 Schema 示例 | ALL/P/N/O |
| tool_contracts.py | overall/positive/negative/neutral |
| computeStyle（实际消费） | overall/positive/negative/neutral |

**建议**：Schema enum 从 tool_contracts.py 派生（overall/positive/negative/neutral）·不改 computeStyle。01 §3.3 的 ALL/P/N/O 是设计文档的示意·实施时以 contracts 为准。

### 4.4 异常处理（[01 §7](01-diagnose-agent.md)）

| 失败层 | 降级策略 |
|------|------|
| 0LLM 字段识别失败 | 全注入 13 工具（D063·已废弃 tools_hint·恒全注入） |
| LLM FC 超时 | 极简 fallback prompt（D060·从 contracts 派生） |
| LLM 返回非法参数 | validateToolCall → 默认值替代（D062·非报错） |
| LLM 未返回 plans[] | CPD 无选项·finalStep 仍出结论 |
| LLM 选错工具 | 质量防线（applyQualityDefense）检测 observation 矛盾 → 降级 |

**统一原则**：永不出现「请求失败」——地图有图层 + 对话区有 observation。

---

## 五、验证标准

1. **contracts_to_tools_schema**：13 工具·格式对齐 §4.1·additionalProperties:false·pytest 结构测。
2. **FC 实测**：`chat_with_tools(messages, tools)` → 「剪裁西陵区」+ polygon grounding → tool_calls[0].name = extract_feature（LLM 自主选对·v1 的数据盲问题根治）。
3. **validateToolCall**：非法 enum→默认值替代（非报错）·pytest。
4. **端到端**：浏览器「剪裁西陵区」（只有面）→ FC → extract → 出图·**6-8s**（FC 2.7s + finalStep 3-5s）。
5. **速度对比**：v1 diagnose 25-45s → v2 FC 2.7s + finalStep 3-5s = **6-8s**（省 70%+）。
6. **pytest** 零回归（v1 的 219 passed 测不受影响——保留件未改）。

---

## 六、commit 节奏

| Phase | commit |
|-------|--------|
| 0 | `docs(emc): v2 架构文档 + sync` |
| 1 | `feat(emc): 5.243 v2 FC 后端（contracts_to_tools_schema + chat_with_tools + validateToolCall + router）` |
| 2 | `feat(emc): 5.244 v2 FC 前端（fcDiagnoseStep + orchestrate + _dataSignature）` |
| 3 | `feat(emc): 5.245 v2 CPD plans[] + 极简 fallback` |
| 4 | `refactor(emc): 5.246 v2 清理废弃 v1 diagnose 管线` |

---

## 七、风险 + 缓解

| 风险 | 等级 | 缓解 |
|------|:---:|------|
| DeepSeek V4 FC 供应商锁定 | 🟡 | 项目已定 DeepSeek 唯一（约束条件） |
| strict 不强制 | 🟡 | D062 validateToolCall 代码兜底（默认值替代） |
| v1→v2 大改 | 🟡 | diagnose 管线替换（~30%）·执行/防线/胶囊保留 |
| FC 失败 fallback | 🟡 | D060 极简 prompt（~1KB·从 contracts 派生·非 v1 大 prompt） |
| polarity enum 漂移 | 🟢 | 以 tool_contracts.py 为准（overall/...）·不改 computeStyle |
| 机器未 sync | 🔴 | Phase 0 必须 git pull 拿 5.235-5.242 |

---

*评估方：GLM（Claude Code·EMC v1 实施者）·2026-07-28·基于 emc-arch-deepdive 全部 v2 文档深度阅读。*
