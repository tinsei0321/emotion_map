# DeepSeek 深度扫描评估报告 — GLM v3 修复专项

> **扫描模型**：DeepSeek V4 Pro（ZCode 主线程） | **扫描时间**：2026-07-28 | **CB 轮次**：CB-09
> **评估对象**：commit `7858d5a` — GLM v3 修复（3 CRITICAL + 4 HIGH）
> **变更范围**：5 文件，+114 / -67 行

---

## 第〇部分：背景与评估范围

### 0.1 评估背景

GLM（v1 实施者）基于第三方 v2 评估报告的发现，提交了 v3 修复 commit `7858d5a`，声称修复如下：

| 等级 | 编号 | 修复项 | 涉及文件 |
|:---:|:---:|------|------|
| 🔴 CRITICAL | C1 | provider fallback — FC 路径缺 fallback，单点故障 | `llm.py`, `router.py` |
| 🔴 CRITICAL | C2 | data gate — 工具×数据兼容性检测缺失 | `router.py`, `stages.js` |
| 🔴 CRITICAL | C3 | domain_lens — FC 路径 domain_lens 恒空 | `router.py`, `stages.js` |
| 🟠 HIGH | H2 | range — 数值参数缺 min/max 约束 | `tool_contracts.py` |
| 🟠 HIGH | H5 | timeout — FC 超时 45s→20s | `stages.js` |
| 🟠 HIGH | H6 | 校验统一 — 前后端双重校验→后端单源 | `router.py`, `harness.js` |
| 🟠 HIGH | (H?) | 未在 diff 中明确标注的第 4 个 HIGH | — |

> **注**：commit 声称 "4 HIGH"，diff 中明确可见 C1/C2/C3 + H2/H5/H6 = 6 项变更。剩余 1 项 HIGH 可能为原有问题已在变更中间接修复，或标注遗漏。以下评估逐项核实。

### 0.2 评估方法

- **读取范围**：全部 5 个变更文件的完整内容 + 变更前后版本对比（`git diff HEAD~1..HEAD` + `git show 143f3da`）
- **逐行核实**：每个修复点的代码正确性、边界条件、跨模块一致性
- **语法验证**：Python `ast.parse` 验证通过；JS 无 node 可用但通过人工逐对括号计数
- **引用格式**：`` `file:line` ``（绝对行号·当前 HEAD）

---

## 第一部分：逐项核实

### C1：provider fallback（`ai_qa/llm.py:305-322` + `ai_qa/router.py:64-65`）

**旧代码**（`router.py`）：
```python
client = LLMClient(model='flash')   # FC 用 Flash
result = client.chat_with_tools(messages, tools)
```
→ 单 `LLMClient` 直连，无 fallback。DeepSeek 不可用时直接抛异常。

**新代码**：
```python
# llm.py:305-322 — 新增函数
def chat_with_tools_fallback(messages, tools, tier: str = 'flash', **kwargs) -> dict:
    providers = _resolve_providers(tier)
    ...
    for prov in providers:
        model = prov.model_flash if tier == 'flash' else prov.model_pro
        cli = LLMClient(base_url=prov.base_url, model=model, api_key=prov.api_key)
        try:
            return cli.chat_with_tools(messages, tools, **kwargs)
        except LLMError as e:
            last_err = e
            trace_warn('MOD_LLM.D_002', f'FC fallback ...')
    raise last_err or LLMError('FC 所有 provider 均失败')

# router.py:64-65 — 调用替换
result = chat_with_tools_fallback(messages, tools, tier='flash')
```

**判定**：✅ **修复正确**。

- 复用 `_resolve_providers(tier)`（与 `chat_with_fallback` 同链）→ DeepSeek→Ark→讯飞
- 非流式场景无需 retry（FC 无 mid-stream 概念），每家 1 次 → 正确
- `trace_log` / `trace_warn` / `trace_error` 埋点完整（`MOD_LLM.F_002` + `MOD_LLM.D_002`）
- `register_track_id` 已有对应注册（`llm.py:325-328`）

**边界检查**：
- `_resolve_providers` 返回空列表 → `raise LLMError(...)` ✅
- 最后一家也失败 → `raise last_err or LLMError(...)` ✅
- `tier='pro'` 时用 `prov.model_pro` ✅

**风险**：无。

---

### C2：data gate（`ai_qa/router.py:53-59` + `frontend/js/ai_qa/stages.js:367-370`）

**修复维度一：System prompt 工具×数据兼容性指导**（`router.py:53-59`）

新增 prompt 片段告知 LLM：
```
## 工具×数据兼容性
- density/hotspot/rank/zonal_stats/compare_regions 需**情绪点层**（含 polarity/score 字段）
- clip 需**点层 + 范围**（range）
- extract_feature/overlay/merge/area_stats 需**面层**（polygon boundary）
- buffer/nearest 需**点层 + 目标**（center/target）
若数据不支撑所选工具，换一个合适的工具或说明缺什么数据。
```

**判定**：✅ **正确**。给 LLM 数据感知能力，让其在选工具时自检数据兼容性。

**修复维度二：代码层 data gate**（`stages.js:367-370`）

```javascript
const _NEEDS_POINT = /^(density|hotspot|rank|clip|buffer|nearest)$/.test(toolName);
const _noPoint = layerMeta && layerMeta.has_point === false;
const _strategy = (_NEEDS_POINT && _noPoint) ? 'request_upload' : 'ready';
```

**判定**：✅ **正确但覆盖面有限**。

**已验证**：
- `ctx.layerMeta` 在 `harness.js:721-724` 被正确填充（从 `getLayers()` 派生）
- `fcDiagnoseStep` 在 `harness.js:737` 被调用，此时 `ctx.layerMeta` 已填充 ✅
- `has_point` / `has_polygon` 字段存在 ✅

**⚠️ 边界缺口**：
1. **zonal_stats 不在 `_NEEDS_POINT` 中**：`zonal_stats` 需要情绪点层做分区统计，但在 `_NEEDS_POINT` regex 中缺失。如果用户传了 polygon 但没有 point 数据，zonal_stats 会以 `strategy='ready'` 通过 gate，执行时可能失败或产出空结果。对比：`zonal_stats` 在 `_EMOTION_TOOLS`（intent 推导）中存在，在 `_NEEDS_POINT`（data gate）中缺席 → 不一致。
2. **只检查 `has_point`，未检查 `has_polygon`**：`extract_feature` / `overlay` / `merge` / `area_stats` 需要 polygon，但 data gate 未覆盖。System prompt 给了 LLM 提示，但代码层无兜底。
3. **System prompt 与代码 gate 不完全对应**：prompt 说 `zonal_stats` 需情绪点层，但代码 gate 不拦。

**严重度**：中。比旧代码（`strategy='ready'` 恒真）有本质改善，但不是全量防护。

---

### C3：domain_lens A+B 混合（`ai_qa/router.py:48-51` + `frontend/js/ai_qa/stages.js:394-416`）

**修复维度一：System prompt 指令 LLM 产出 domain_lens**（`router.py:48-51`）

```
## domain_lens
在回复文本开头输出领域标签（选 0-2 个最匹配的）：
[domain_lens:urban_planning] 或 [domain_lens:urban_renewal] 或 [domain_lens:urban_operation] 或 [domain_lens:urban_governance]
判断依据：规划/用地→planning·更新/老旧/改造→renewal·运营/商圈/场馆→operation·治理/交通/停车→governance
情绪分析类（极性/归因/排序）默认 urban_renewal。无明确领域则不输出。
```

**修复维度二：代码层 A+B 混合推导**（`stages.js:394-416`）

```javascript
function _deriveDomainLens(question, fcContent) {
  // A：parse FC content [domain_lens:xxx]
  if (fcContent) {
    const m = String(fcContent).match(/\[domain_lens:(urban_planning|urban_renewal|urban_operation|urban_governance)\]/);
    if (m) return [m[1]];
  }
  // B：关键词推导兜底
  const _DK = {
    urban_planning: ['规划', '用地', '商业用地', '居住用地', '功能区', '土地'],
    urban_renewal: ['更新', '老旧', '改造', '棚改', '小区', '归因', '情绪'],
    urban_operation: ['运营', '商圈', '场馆', '奥体', '商业街', '演唱会'],
    urban_governance: ['治理', '交通', '停车', '施工', '城管', '环境'],
  };
  for (const [domain, kws] of Object.entries(_DK)) {
    if (kws.some((kw) => question.includes(kw))) { hits.push(domain); break; }
  }
  return hits.length ? hits : ['urban_renewal'];
}
```

**判定**：✅ **核心逻辑正确**，⚠️ **有三处细节偏差**。

**已验证**：
- A 路径：正则 `\[domain_lens:(urban_planning|...)\]` 正确匹配 system prompt 指定格式 ✅
- B 路径：关键词覆盖 4 个领域，`break` 取首个命中（最多 1 个）✅
- `_normalizeFcDiagnose` 调用 `_deriveDomainLens(question, fcContent)` 正确传参 ✅

**⚠️ 细节偏差**：

1. **数量不匹配**：System prompt 说 "选 0-2 个最匹配的"，但 `_deriveDomainLens` 永远只返回 1 个或默认 1 个（`['urban_renewal']`）。函数不产 0 也不产 2。如果 LLM 产出 2 个 domain_lens 标签，正则只匹配第一个。这不是 bug（下游可能只消费第一个），但与 prompt 声明不一致 → 文档级偏差。

2. **关键词顺序敏感**：`_DK` 中 `urban_renewal` 的 `break` 策略 + 关键词 "情绪"/"归因" 泛化度高。`for...of` 遍历顺序为 `planning → renewal → operation → governance`。问题：用户问 "**交通**拥堵对居民**情绪**的影响" → `planning` 不命中（"交通"不在其关键词），`renewal` 命中 "情绪" → 返回 `urban_renewal`。但实际更合适的可能是 `urban_governance`（交通治理）。**关键词匹配的贪心策略（首个命中即返回）对跨领域组合问题敏感度不足**。

3. **默认值争议**：`['urban_renewal']` 作为"情绪分析主场景"默认值。但空问题（`question=''` 且无 `fcContent`）也会返回此值 → 下游可能看到无意义的默认 `domain_lens`。原始的恒空 `[]` 更诚实（表示"不确定"），硬填默认值可能误导。

**严重度**：低。A+B 混合设计方向正确，偏差为边界 case，不影响主链路。

---

### H2：range 约束（`ai_qa/tool_contracts.py:387-408`）

```python
_PARAM_RANGES = {
    'radius': (50, 3000), 'cell_size': (50, 5000), 'radius_m': (50, 3000),
    'top_n': (1, 20), 'k': (1, 10), 'bandwidth_m': (50, 3000),
}

def _param_to_json_schema(p):
    ...
    if p['name'] in _PARAM_RANGES:
        lo, hi = _PARAM_RANGES[p['name']]
        prop['minimum'] = lo
        prop['maximum'] = hi
    return prop
```

**判定**：✅ **修复正确**。

- JSON Schema `minimum`/`maximum` 约束 LLM 产出合理数值范围 ✅
- 覆盖 6 个数值参数（radius / cell_size / radius_m / top_n / k / bandwidth_m）✅
- `_param_to_json_schema` 被 `contracts_to_tools_schema()` 调用 → 全 13 工具的 schema 都受益 ✅

**⚠️ 潜在局限**：
- `radius` 上限 3000m 对城市级分析够用，但对区域级（如"宜昌市全域"）可能偏小
- `cell_size` 上限 5000 同理
- 硬编码范围无法按工具语义调整（如 `density.radius` vs `buffer.radius_m` 可能需要不同范围）。不过与 commit 意图一致（治 LLM 填 `radius=1` 或 `99999`）→ 当前值合理。

**严重度**：无。

---

### H5：timeout 45s→20s（`frontend/js/ai_qa/stages.js:298`）

```javascript
const _timer = setTimeout(() => _ac.abort(new Error('FC 单轮超时(20s)')), 20000);
// v3 H5：20s（FC 正常 2.7s·45s 太长致降级 70s+）
```

**判定**：✅ **修复正确**。

- FC 正常耗时 2.7s（实测数据见 `VERIFY_DeepSeekFC.md:14`）✅
- 20s = ~7x 正常耗时 + provider fallback 余量（3 家 × ~3s + 网络抖动）→ 合理 ✅
- 旧 45s 在 fallback 场景下累计可达 135s（3 家 × 45s），严重拉长降级链 → 确实过长

**⚠️ 残留**：
- 行 296 注释仍写 "45s timeout"：`// 5a/5b：AbortController + 45s timeout（同 streamChat·治用户取消 + 挂起）` → 应更新为 20s
- 注释引用 "同 streamChat"：FC 走非流式 JSON，与 streamChat 的 45s 语义不同 → 注释有误导性

**严重度**：无（注释问题为 COSMETIC）。

---

### H6：校验统一（`ai_qa/router.py:67-75` + `frontend/js/ai_qa/harness.js:13-14`）

**后端（`router.py:67-75`）**：
```python
from ai_qa.tool_contracts import validate_tool_call
tc = (result.get('tool_calls') or [{}])[0]
if tc and tc.get('function'):
    _args = _json.loads(tc['function'].get('arguments', '{}'))
    _v = validate_tool_call(tc['function']['name'], _args)
    if _v['fixes']:
        tc['function']['arguments'] = _json.dumps(_v['params'], ensure_ascii=False)
        result.setdefault('_fc_fixes', _v['fixes'])   # 供前端日志
```

**前端（`harness.js:13-14`）**：
```javascript
// v3 H6：前端 _validateFcParams 已删除——信赖后端 validate_tool_call
```

**判定**：✅ **方向正确**，⚠️ **`_fc_fixes` 未传回前端**。

**已验证**：
- `validate_tool_call`（`tool_contracts.py:487-526`）逻辑正确：enum 外→默认替代、required 缺→补默认 ✅
- 前端不再重复校验 → 单一职责 ✅
- 后端校验在返回 `JSONResponse` 之前完成 → 前端收到的 params 已修正 ✅

**⚠️ 问题**：
`result.setdefault('_fc_fixes', _v['fixes'])` 设置后，JSONResponse 只返回 `tool_calls` / `plans` / `usage`，**`_fc_fixes` 字段未被包含**（`router.py:76-79`）：

```python
return JSONResponse({
    'tool_calls': result.get('tool_calls'),
    'plans': result.get('content'),
    'usage': result.get('usage'),
})
```

虽然修正后的 params 已通过 `tool_calls[0].function.arguments` 返回前端（通过对象引用），但 `_fc_fixes` 本身（描述改了什么）从未离开后端。注释 "供前端日志" 在当前实现中不成立 → **注释与实现不一致**。

**严重度**：低。功能不受影响（param 已修正），仅日志/可观测性缺失。

---

## 第二部分：回归问题发现

### 🔴 BR1（CRITICAL）：`stages.js` 语法错误 — 多余括号

**位置**：`frontend/js/ai_qa/stages.js:417-418`

```javascript
416: }                          // ← _deriveDomainLens 闭合（正确）
417:   };                        // ← 🔴 孤儿括号！不闭合任何语句
418: }                           // ← 🔴 孤儿括号！不闭合任何语句
419:
420: /** v2 plans[] 容错解析... */
421: function _parsePlans(content) {
```

**根因**：v3 编辑在旧 `_normalizeFcDiagnose` 函数闭合（`  };` + `}`）之后插入了新 `_deriveDomainLens` 函数。原 `  };` + `}` 在新位置（行 391-392）正确闭合了 `_normalizeFcDiagnose`，但旧位置的行 417-418 保留了重复的闭合括号未被删除。

**证据**：
- `git show 143f3da:frontend/js/ai_qa/stages.js` 第 390 行附近：`_normalizeFcDiagnose` 闭合后直接接 `_parsePlans` → 语法正确
- v3 commit diff 中行 417-418 的 `  };` 和 `}` 为**无前缀上下文行**（非 `+` 非 `-`）→ 它们是旧代码在新文件中的残留
- commit `143f3da`（紧接在 v3 之前）专门修复了同类型错误：`fix(emc): 5.245b stages.js 语法错误修复（多余 }·致地图加载失败）`，根因描述为 "_normalizeFcDiagnose 函数闭合后多了一个 }"

**影响**：🔴 **阻断级 (BLOCKING)**。ES module 顶层出现孤立 `};` 和 `}` 会导致 JavaScript 解析失败 → `stages.js` 无法被 import → 整个模块图断裂 → `main.js` 无法执行 → MapLibre 不初始化 → **地图白屏**。

**验证**：`node --check frontend/js/ai_qa/stages.js` 不可用（环境无 node），但人工逐对计数确认：
- 开 `{`：`_deriveDomainLens` 函数体 1 个 + `_DK` 对象字面量 1 个 + `for` 块 1 个 + `if` 块 2 个 = 5
- 闭 `}`：行 402 `}` + 行 403 `}` + 行 413 `}`（for 块内 if 闭）+ 行 414 `}`（for 块闭）+ 行 416 `}`（函数闭）= 5
- 行 417 `  };` 不闭合任何 `{` → 语法错误
- 行 418 `}` 不闭合任何 `{` → 语法错误

**这与 commit `143f3da` 修复的错误完全同类**——函数闭合后多余括号。上次是 `_normalizeFcDiagnose` 后多一个 `}`，这次是 `_deriveDomainLens` 后多 `  };` + `}`。

---

### 🟡 BR2（MEDIUM）：`_fc_fixes` 未包含在 JSONResponse 中

**位置**：`ai_qa/router.py:75-79`

`result.setdefault('_fc_fixes', _v['fixes'])` 设值但 JSONResponse 不传。详见 H6 分析。

---

### 🟡 BR3（MEDIUM）：System prompt domain_lens 指令与 plans JSON 冲突

**位置**：`ai_qa/router.py:42-43,48-50`

System prompt 同时要求：
1. "在回复文本中输出 plans JSON"
2. "在回复文本开头输出领域标签 `[domain_lens:xxx]`"

如果 LLM 严格遵循"开头输出"，content 会是：
```
[domain_lens:urban_renewal]
{"plans":[...]}
```

但前端 `_parsePlans()`（`stages.js:421`）直接 `JSON.parse(content)`，前置 `[domain_lens:xxx]` 标签会导致 JSON 解析失败 → plans 为空 → CPD 胶囊缺失。

**缓解**：A 路径（`_deriveDomainLens` 的 regex match）会成功提取 domain_lens，且 B 路径（关键词兜底）在 A 失败时接管。所以 plans 解析失败时 domain_lens 仍可工作。但 **plans 丢失是真实损失**。

**严重度**：中。影响 CPD 追问胶囊产出。

---

## 第三部分：综合评估

### 3.1 修复质量矩阵

| 编号 | 修复项 | 方向 | 实现 | 边界 | 回归风险 | 综合 |
|:---:|------|:---:|:---:|:---:|:---:|:---:|
| C1 | provider fallback | ✅ | ✅ | ✅ | 无 | ✅ **通过** |
| C2 | data gate | ✅ | ✅ | ⚠️ 部分缺口 | 无 | ⚠️ **有条件通过** |
| C3 | domain_lens | ✅ | ✅ | ⚠️ 细节偏差 | 低 | ⚠️ **有条件通过** |
| H2 | range 约束 | ✅ | ✅ | ✅ | 无 | ✅ **通过** |
| H5 | timeout 20s | ✅ | ✅ | ✅ | 无 | ✅ **通过** |
| H6 | 校验统一 | ✅ | ✅ | ⚠️ 日志缺失 | 无 | ⚠️ **有条件通过** |
| — | **BR1 语法错误** | — | 🔴 | — | 🔴 BLOCKING | 🔴 **阻断** |

### 3.2 一句话总结

> **6 个修复项的方向和核心逻辑全部正确，但引入 1 个 CRITICAL 回归（stages.js 多余括号致 JS 语法错误·阻断前端加载）和 3 个 MEDIUM 边界问题。BR1 必须立即修复（删 2 行），其余可在后续迭代中处理。**

### 3.3 与 commit `143f3da` 的对照

`143f3da`（v3 前一个 commit）修复了同类型 stages.js 语法错误：
- 根因：`_normalizeFcDiagnose` 闭合后多一个 `}`
- 影响：地图白屏（module graph 断裂）

v3 修复本质上**重演了同一模式**：修改 `_normalizeFcDiagnose` + 插入新函数后，未清理旧闭合括号。**同一文件的同类错误在连续两个 commit 中发生**，说明编辑流程缺乏语法校验环节（如 `node --check` 或 linter pre-commit hook）。

---

## 第四部分：优化建议

### P0（立即修复·BLOCKING）

| # | 建议 | 文件 | 操作 |
|:---:|------|------|------|
| **P0-1** | 删除孤括号 | `stages.js:417-418` | 删除行 417 `  };` 和行 418 `}` |
| **P0-2** | JS 语法校验门禁 | `.husky/pre-commit` 或 CI | 加 `node --check` 对 `frontend/js/**/*.js`（避免同类回归） |

### P1（高优先·建议在下一轮修复）

| # | 建议 | 位置 | 说明 |
|:---:|------|------|------|
| **P1-1** | `_NEEDS_POINT` 补 `zonal_stats` | `stages.js:368` | `zonal_stats` 需情绪点层（与 System prompt 一致），当前不在 data gate regex 中 |
| **P1-2** | 解耦 plans JSON 与 domain_lens 标签 | `router.py:42-50` | 方案 A：domain_lens 用独立字段（如 `tool_calls` 并列）而非 content 前缀；方案 B：`_parsePlans` 容错 strip `[domain_lens:xxx]` 前缀 |
| **P1-3** | `_fc_fixes` 传入 JSONResponse | `router.py:76-79` | 加 `'fixes': result.get('_fc_fixes')` 供前端可观测 |

### P2（中优先·后续迭代）

| # | 建议 | 位置 | 说明 |
|:---:|------|------|------|
| **P2-1** | `_deriveDomainLens` 支持多 domain_lens | `stages.js:398-416` | 对齐 System prompt "选 0-2 个"；或改 prompt 为 "选 1 个" |
| **P2-2** | data gate 扩展 polygon 检查 | `stages.js:367-370` | 面层工具（extract_feature/overlay/merge/area_stats）无 polygon 时设 `strategy='request_upload'` |
| **P2-3** | 更新 H5 注释 | `stages.js:296` | "45s timeout" → "20s timeout"；"同 streamChat" → 独立说明 |
| **P2-4** | `_deriveDomainLens` 无匹配时返 `[]` 而非默认 `['urban_renewal']` | `stages.js:415` | 空值更诚实；下游应能处理空 domain_lens |

---

## 第五部分：讨论点

### D1：FC path 的 data gate 应该是 LLM 职责还是代码职责？

当前设计：System prompt 做软约束（告知 LLM 数据兼容性规则） + `_NEEDS_POINT` regex 做硬门禁（代码层拦截）。两者互补，但 **职责边界模糊**：
- 代码层只检查 `has_point` → 对 polygon-only 场景不完整
- System prompt 告知了所有规则但无强制性（LLM 可能不遵守）

**建议方向**：代码层做全部硬门禁（point + polygon 全覆盖），System prompt 只做解释性提示（"为什么这个工具不可用"）。但当前 C2 是改善（从无→有），不应因"不完整"否定其价值。

### D2：`_fc_fixes` 的可观测性

`validate_tool_call` 的参数修正（enum→默认替代、required 补默认值）是"静默修正"——用户不知道参数被改了。这在功能上正确（修正后工具能跑），但在调试/信任建立上有损失。如果 LLM 频繁输出非法参数（strict 不强制），累积的 silent fixes 可能掩盖 prompt 质量问题。

**建议**：将 `_fc_fixes` 传回前端，在 diagnostics 面板展示（如 "[参数修正] polarity=happy → overall"），让用户和开发者可见修正行为。

---

## 附录

### A. 变更文件清单

| 文件 | +行 | -行 | 变更内容 |
|------|:---:|:---:|------|
| `ai_qa/llm.py` | 20 | 0 | 新增 `chat_with_tools_fallback` |
| `ai_qa/router.py` | 39 | 6 | FC fallback + system prompt + backend validate |
| `ai_qa/tool_contracts.py` | 14 | 1 | `_PARAM_RANGES` + min/max schema |
| `frontend/js/ai_qa/harness.js` | 2 | 41 | 删除 `_validateFcParams` |
| `frontend/js/ai_qa/stages.js` | 65 | 12 | timeout + data gate + domain_lens |

### B. Python 语法验证

```
llm.py — ast.parse ✅
router.py — ast.parse ✅
tool_contracts.py — ast.parse ✅
```

### C. JS 语法验证

Node.js 不可用（环境限制）。人工逐对括号计数确认 stages.js:417-418 为孤括号（详见 BR1）。

### D. 评分（针对 v3 修复，非全项目）

| 轴 | 得分 | 说明 |
|------|:---:|------|
| 架构设计 | 7/10 | C1/C2/C3 方向正确；C3 A+B 混合设计优雅 |
| 代码质量 | 5/10 | 主逻辑 OK；BR1 语法错误 -3；BR3 冲突 -1；注释不一致 -1 |
| 测试覆盖 | N/A | 本次未涉及测试变更 |
| Harness 工程 | N/A | 本次未涉及 Harness 变更 |
| 文档完整度 | N/A | 本次未涉及文档变更 |
| 调用效率 | N/A | 本次未涉及 |
| 演示表现力 | N/A | 本次未涉及 |

> **综合（仅针对 6 修复项）**：⚠️ **6.0/10** — 修复方向全对，但 BR1（阻断）拉低整体评分。修复 BR1 后预计 **8.0/10**。

---

> **归档信息**：`docs/catch-ball/report/SCAN_DeepSeek_04-glm-v3.md`
> **下一轮建议**：修复 BR1 → 浏览器 E2E 验证 FC 路径 + domain_lens + data gate → 触发 CB-10 验证。
