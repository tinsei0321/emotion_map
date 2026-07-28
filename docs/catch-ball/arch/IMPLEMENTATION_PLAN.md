# v2 实施计划（基于 GLM 评估 + 代码验证）

> **日期**：2026-07-28  
> **依据**：GLM 评估报告（EVAL_GLM_v2_implementation.md）+ 代码验证（本地 vs 远程分叉确认）  
> **状态**：✅ 可执行——GLM 评估通过·代码状态已核实  
> **核心判断**：GLM 的 4 阶段计划准确·需补 1 个关键前提 + 修正 1 个 enum 细节

---

## 〇、GLM 评估审核结论

### 同意 GLM 的判断

| GLM 结论 | 我的审核 |
|------|:---:|
| v2 方向正确·同意实施 | ✅ agree |
| ~70% v1 代码保留 | ✅ agree——执行层/防线/胶囊/contracts 保留 |
| 4 阶段实施（后端 FC → 前端 → CPD/fallback → 清理） | ✅ agree——顺序合理 |
| validateToolCall 非法值用默认值替代（非报错） | ✅ agree——更宽容 |
| polarity enum 以 contracts 为准（overall/...） | ✅ agree——**我 v2 文档的 ALL/P/N/O 写错了** |
| 6-8s 端到端目标 | ✅ agree——实测支撑 |

### 需补充的关键前提

**GLM 的 Phase 0（git pull）是硬性前提·不是可选步骤。**

经验证：本地分支停在 5.234 之前，远程已到 5.242（bb6fd99）。v1 的 diagnose 管线（candidate_selector / FILL_CARD / PLAN / dispatch）**全部在远程**——本地没有。**不 pull 就无法替换 v1→v2。**

### 需修正的 1 个细节

**polarity enum**：v2 设计文档（01-diagnose-agent.md §3.3）写的是 `ALL/P/N/O`。实际 tool_contracts.py 和 computeStyle 都用 `overall/positive/negative/neutral`。**实施时以 contracts 为准——GLM 正确指出了这个不一致。**

---

## 一、实施前提（必须先做）

### Step 0：分支同步

```bash
# 1. 本地 v2 文档先 commit（已完成）
# 2. 拉取远程 5.235-5.242
git pull origin main
# 3. 解决冲突（deepdive 文档可能冲突·保留 v2 版）
# 4. 验证：ai_qa/candidate_selector.py 应存在
ls ai_qa/candidate_selector.py
grep "FILL_CARD_TEMPLATE" ai_qa/prompts.py
```

**验证标准**：
- `candidate_selector.py` 存在且有 `select_candidates` 函数
- `prompts.py` 含 `FILL_CARD_TEMPLATE` / `PLAN_TEMPLATE` / `build_diagnose_prompt_dispatch`
- `harness.js:708` 含 `5.242` 注释

**如果 pull 失败或文件不存在 → 停止·不继续后续步骤。**

---

## 二、4 阶段实施计划

### Phase 1：后端 FC 基础设施（1 天）

#### 1.1 `contracts_to_tools_schema()` + `contracts_to_text()`

**文件**：`ai_qa/tool_contracts.py`（新增两个函数）

| 函数 | 输入 | 输出 | 消费方 |
|------|------|------|------|
| `contracts_to_tools_schema()` | TOOL_CONTRACTS | `[{type:function, function:{name,description,strict,parameters}}]` | function calling tools 参数 |
| `contracts_to_text()` | TOOL_CONTRACTS | 纯文本工具列表 | fallback prompt |

**关键细节**（GLM §1.1 + 我的修正）：
- **polarity enum 用 contracts 原值**（`overall/positive/negative/neutral`）——不是 ALL/P/N/O
- **参数名对齐工具实际读取**（buffer `radius_m` / density `radius`）
- `additionalProperties: false` + `strict: true`
- 全 13 个 GIS 工具（不含 concept/multi/unknown）

**验证**：pytest 结构测试——13 工具·格式正确·enum 对齐 contracts。

#### 1.2 `chat_with_tools()`

**文件**：`ai_qa/llm.py`（LLMClient 类新增方法）

```python
def chat_with_tools(self, messages, tools, tool_choice='auto'):
    """DeepSeek V4 function calling·非流式。
    返 { tool_calls: [{name, arguments}], content: str }
    arguments 是 JSON 字符串（调用方 JSON.parse）。"""
```

**关键**：不改现有 `chat()` 签名——新方法独立。非流式（FC 2.7s 一次返完整结果）。

#### 1.3 `validate_tool_call()`

**文件**：`ai_qa/tool_contracts.py` 或编排器层

```python
def validate_tool_call(tool_name, args):
    """strict 不强制→代码兜底。
    required 缺→补默认值；enum 外→用默认值替代（非报错）。
    返 { ok, params, fixes }"""
```

**关键**（GLM §1.3 + D062）：非法值→默认值替代·不 reject。复用现有 `validateParams` 范式。

#### 1.4 Router FC phase

**文件**：`ai_qa/router.py`

```python
elif req.phase == 'fc_diagnose':
    tools = contracts_to_tools_schema()
    result = client.chat_with_tools(messages, tools)
    return JSONResponse({ 'tool_calls': result['tool_calls'], 'plans': result['content'] })
```

**验证**：`POST /api/v1/chat {phase:'fc_diagnose', messages:[...]}` → 返回 tool_calls + plans。

**Phase 1 commit**：`feat(emc): 5.243 v2 FC 后端`

---

### Phase 2：前端适配（1 天）

#### 2.1 `fcDiagnoseStep()`（替代 diagnoseStep）

**文件**：`frontend/js/ai_qa/stages.js`（新增）

```javascript
export async function fcDiagnoseStep(ctx, hooks) {
  const resp = await fetch('/api/v1/chat', { ... phase: 'fc_diagnose' ... });
  const { tool_calls, plans } = await resp.json();
  const tc = tool_calls && tool_calls[0];
  return {
    template: tc ? tc.function.name : 'unknown',
    params: tc ? JSON.parse(tc.function.arguments) : {},
    plans: plans,
    degraded: !tc,
    intent: tc ? 'gis_operation' : 'unknown',
    _fc: true,
  };
}
```

#### 2.2 orchestrate 改用 fcDiagnoseStep

**文件**：`frontend/js/ai_qa/harness.js`

```javascript
// 替代 diagnoseStep 调用
diagnose = await stages.fcDiagnoseStep(ctx, hooks);
// 后续不变：runTemplatePath(diagnose.template, diagnose.params)
```

**关键**：runTemplatePath 几乎不变——读 template + params 执行。废弃 select_candidates / FILL_CARD / PLAN / dispatch 路径。

#### 2.3 数据变化检测（D065）

**文件**：`frontend/js/ai_qa/harness.js`（orchestrate 顶部）

```javascript
const _sig = getLayers().map(l => `${l.srcId}:${(l.fc?.features||[]).length}:${l.kind}`).join('|');
if (ctx.priorTurn?._dataSig && ctx.priorTurn._dataSig !== _sig) {
  ctx.plans = null;
}
ctx._dataSig = _sig;
```

**Phase 2 commit**：`feat(emc): 5.244 v2 FC 前端`

**验证**：浏览器「剪裁西陵区」→ FC → extract_feature → 出图·6-8s。

---

### Phase 3：CPD plans[] + fallback（半天）

#### 3.1 plans[] 解析 + 消费

**文件**：`frontend/js/ai_qa/harness.js`

```javascript
// FC 响应解析后
ctx.plans = parsePlans(diagnose.plans);  // D067 容错校验
// finalStep 读 ctx.plans → 追问胶囊
// CPD 读 ctx.plans → rank=2+ 选项
```

**parsePlans**（D067）：JSON.parse + 字段校验 + 容错（解析失败=空 plans·不崩溃）。

#### 3.2 极简 fallback

**文件**：`ai_qa/prompts.py` + `ai_qa/router.py`

FC 失败时退回极简 prompt（~1KB·从 `contracts_to_text()` 派生·非手写）：
```
"你是情绪地图分析助手。选择一个工具并填写参数。
可用工具: {contracts_to_text()}
用户问题: {question}
数据上下文: {grounding}
输出 JSON: { tool, arguments, plans }"
```

**Phase 3 commit**：`feat(emc): 5.245 v2 CPD plans + fallback`

**验证**：手动触发 FC 失败（断网/DNS）→ fallback 出图。

---

### Phase 4：清理废弃 v1 代码（半天·渐进）

| 废弃 | 文件 | 理由 |
|------|------|------|
| `candidate_selector.py` | `ai_qa/` | FC 自主选·无需规则预选 |
| `FILL_CARD_TEMPLATE` + `build_fill_card_prompt` | `prompts.py` | FC tools schema 取代 |
| `PLAN_TEMPLATE` + `build_plan_prompt` | `prompts.py` | 取消 Pro 阶段 |
| `build_diagnose_prompt_dispatch` | `prompts.py` | FC 端点取代 |
| trigger 规则（`_B_TRACK_TRIGGER_EXT` 等） | `candidate_selector.py` | 无需关键词触发 |

**过渡期保留**（D053）：
- `paradigm.py` GEO_TOOL_CATALOG / TEMPLATE_REGISTRY（编排器 validateParams 暂用）
- `SKILL_DEFS`（同上·逐步迁移到 contracts 直接校验）
- `field_dictionary`（0LLM grounding 用）
- `buildContext`（前端 grounding 用）

**Phase 4 commit**：`refactor(emc): 5.246 v2 清理废弃 v1 diagnose 管线`

**验证**：pytest 零回归（保留件未改）。

---

## 三、修正 v2 设计文档

实施前需修正 1 处文档错误：

| 文件 | 错误 | 修正 |
|------|------|------|
| `01-diagnose-agent.md` §3.3 | polarity enum `ALL/P/N/O` | 改为 `overall/positive/negative/neutral`（对齐 contracts + computeStyle） |

---

## 四、验证标准（GLM §五 + 补充）

| # | 验证项 | 方法 | 标准 |
|:---:|------|------|------|
| 1 | contracts_to_tools_schema | pytest 结构测试 | 13 工具·格式正确·enum 对齐 |
| 2 | FC 实测 | 「剪裁西陵区」+ polygon 数据 | tool_calls[0].name = extract_feature |
| 3 | validateToolCall | 非法 enum 测试 | 默认值替代·非报错 |
| 4 | 端到端 | 浏览器测试 | 6-8s 出图 |
| 5 | plans[] 解析 | 畸形 JSON 测试 | 容错·不崩溃 |
| 6 | fallback | 断网测试 | 极简 prompt 出图 |
| 7 | pytest 回归 | 全量测试 | 零回归 |

---

## 五、风险 + 缓解

| 风险 | 等级 | 缓解 |
|------|:---:|------|
| 分支同步冲突 | 🔴 | Phase 0 必须 git pull·冲突优先保留 v2 文档 |
| DeepSeek V4 FC 复杂场景稳定性 | 🟡 | fallback prompt 兜底 + 真实场景测试 |
| strict 不强制 | 🟡 | D062 validateToolCall 代码兜底 |
| polarity enum 漂移 | 🟢 | 以 contracts 为准·不改 computeStyle |
| v1→v2 替换遗漏 | 🟡 | Phase 4 渐进清理·保留过渡期 |

---

## 六、总评

**GLM 的评估和实施计划质量高·可直接执行。** 补充了 2 点：

1. **Phase 0（git pull）是硬性前提**——本地分支落后远程 10 个实现 commit·不 pull 无法替换 v1
2. **polarity enum 修正**——v2 文档的 ALL/P/N/O 写错·以 contracts（overall/...）为准

**建议立即执行 Phase 0·然后按 Phase 1→4 顺序推进。预计 3 天完成主链路（Phase 1-3）·半天清理（Phase 4）。**

---

*实施计划基于 GLM 评估（EVAL_GLM_v2_implementation.md）+ 代码验证（本地 vs 远程 bb6fd99）+ v2 全部设计文档*
