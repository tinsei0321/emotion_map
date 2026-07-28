# EMC 结果范式超时 + 2D/3D 图层跳转 Bug 专项评估

> **评估方**：DeepSeek（第三方 LLM）  
> **评估日期**：2026-07-27  
> **评估触发**：L0 路由修复后两个遗留问题  
> &nbsp;&nbsp;&nbsp;&nbsp;① 快速出图但结论为「[请求失败] LLM 单轮超时(45s)」——图已出、文失败，彼此矛盾  
> &nbsp;&nbsp;&nbsp;&nbsp;② 点击 Layers 中 EMC 图层组的 2D/3D 按钮 → 图层跳转至网格聚合组 → EMC 组变空(0)  
> **CB 轮次**：CB-04（EMC 评估轨·第五轮 — 超时+Bug 专项）

---

## 问题一：出图成功但结论超时「[请求失败] LLM 单轮超时(45s)」

### 1.1 现象

```
用户发送 → diagnose → density 工具执行 → 地图出图(2-3s) → finalStep 等 45s → 超时 → [请求失败]
                                                            ↑
                                                    图已出，文失败——矛盾
```

### 1.2 根因链

#### 根因 1：finalStep 的 system prompt 过大致 prefill 超时

finalStep LLM 调用时的 system prompt 由 5 大块拼接而成：

| 组件 | 来源 | 大小估算 | 说明 |
|------|------|:---:|------|
| **MANIFESTO** | `manifesto.py:12-87` | ~12 KB (~3000-4000 tokens) | 11 节领域宪法·全文注入所有 LLM 调用 |
| **FINAL_TEMPLATE** | `prompts.py:125-161` | ~3 KB | 文风规则 + 出口元素 + 自查清单 |
| **industry_kb appendix** | `industry_kb/__init__.py:88` | 5-20 KB | 每命中一个 domain 追加 ~5-7 KB，两个 domain = 翻倍 |
| **ctx.context 接地** | `tools.js:563` buildContext | 2-8 KB | 图层列表 + 字段样本 + 统计摘要 |
| **toolHistory** | `harness.js:367` | 0.5-1 KB | 已执行工具 + observation |
| **合计** | | **20-44 KB**（**5000-12000+ tokens**） | |

**LLM 必须先 prefill（处理）整个 system prompt 再生成第一个 token。** 即使使用 Flash 模型，prefill 20-44 KB 本身就需 20-35 秒。生成结论文本还需 10-25 秒。**总计 30-60 秒，超过 45 秒 per-call timeout。**

#### 根因 2：45s timeout 在 api.js 中统一设定

**文件**：`frontend/js/ai_qa/api.js:32-34`

```javascript
const _timer = setTimeout(() => _ac.abort(new Error('LLM 单轮超时(45s)')), 45000);
```

所有 LLM 调用（diagnose/agentStep/finalStep/review/revise）共享同一个 45s 超时。finalStep 的 prompt 最大、生成量最多，却享受和 diagnose 相同的超时窗口——不成比例。

#### 根因 3：runTemplatePath 无 try/catch 保护 finalStep

**文件**：`frontend/js/ai_qa/harness.js:366-367`

```javascript
// runTemplatePath finalStep — NO try/catch
let draft = await stages.finalStep(ctx, hooks, toolHistoryText);
```

对比 while-loop 路径（`harness.js:762-767`）**有** try/catch：

```javascript
try {
    draft = await stages.finalStep(ctx, hooks, toolHistoryText);
} catch (e) {
    if (hooks.onDegraded) hooks.onDegraded('');
    return { ok: false, degraded: true, rounds: round };
}
```

`runTemplatePath` 和 `runChainPath` 两个快速路径都缺少此保护。超时异常一路冒泡到 `panel.js:1476` → 渲染 `[请求失败] LLM 单轮超时(45s)`。

#### 根因 4：超时后无降级结论生成

当 finalStep 超时时，**地图上已有正确的分析图层**（如 838 单元网格层），但对话区只显示错误信息。系统没有任何机制「基于已成功的工具产出生成简单的降级结论」——如：

```
已生成 1000m 方格网空间聚合图（838 单元），覆盖中心城区范围。
点击下方按钮查看图层详情或进行下一步分析。
{{show:T3·综合}}
```

这种降级结论可以零 LLM 调用生成——直接从 toolHistory 和 formatRegistry() 提取图层信息拼接而成。

### 1.3 解决方案（三层优化）

#### Layer 1：瘦身 finalStep 的 system prompt（治本·省 prefill 时间）

**策略**：answer 阶段不需要完整 MANIFESTO + industry_kb。

| 组件 | 当前 | 优化后 | 节省 |
|------|------|------|:---:|
| MANIFESTO | 全文 11 节 | **仅保留 §8 回答策略 + §9 回答约定**（2 节） | ~8 KB |
| industry_kb | 全文追加 | **移除**（answer 阶段不需要城市规划政策框架） | 5-20 KB |
| ctx.context | buildContext 全量 | 不变（接地必要） | — |
| FINAL_TEMPLATE | 全文 | 不变 | — |

**实现**：在 `prompts.py` 中新增 `build_final_prompt_light()` 函数，或在 `build_final_prompt()` 中增加 `light=True` 参数。改动如下：

```python
# prompts.py:164
def build_final_prompt(context, tool_history, context_tokens, domain_lens, light=False):
    ctx = context or '（未提供数据上下文）'
    hist = tool_history or '（无探索历史）'
    if light:
        # answer 阶段用轻量 prompt：核心规则 + 文风 + 自查
        manifesto_light = MANIFESTO_LIGHT  # 仅 §8+§9
        prompt = _today_line() + manifesto_light + FINAL_TEMPLATE.format(...)
        # 不加 industry_kb appendix
    else:
        prompt = _today_line() + MANIFESTO + FINAL_TEMPLATE.format(...)
        prompt += industry_kb_lens_appendix(domain_lens)
    return _inject_tokens(prompt, context_tokens)
```

**效果估算**：system prompt 从 20-44 KB 降到 8-15 KB，prefill 时间从 20-35s 降到 8-15s。总耗时从 30-60s 降到 15-30s——在 45s 超时窗口内。

#### Layer 2：延长 finalStep 超时 / 分级超时（防御）

**文件**：`frontend/js/ai_qa/api.js:32-34`

方案 A：finalStep 专用更长的超时（60s）：
```javascript
const _timeout = phase === 'answer' ? 60000 : 45000;
const _timer = setTimeout(() => _ac.abort(new Error('LLM 单轮超时')), _timeout);
```

方案 B：保持 45s 但结合 Layer 1 的 prompt 瘦身，双重保险。

**推荐方案 A+B**——瘦身减少正常需时，长超时兜底异常波动。

#### Layer 3：超时降级结论生成（容错·关键体验改善）

**文件**：`frontend/js/ai_qa/harness.js:366-367`

为 `runTemplatePath` 添加 try/catch + 降级结论生成：

```javascript
let draft;
try {
    draft = await stages.finalStep(ctx, hooks, toolHistoryText);
} catch (e) {
    // 超时降级：基于已成功的工具产出生成简单结论
    const _layers = formatRegistry();
    const _toolSummary = toolHistoryText.slice(-300);  // 最后一条 observation
    draft = _composeDegradedConclusion(diagnose, _layers, _toolSummary);
    if (hooks.onDegraded) hooks.onDegraded(draft);
}
```

`_composeDegradedConclusion()` 生成零 LLM 调用的降级文本：

```javascript
function _composeDegradedConclusion(diagnose, registry, toolObs) {
  const _layers = registry.length
    ? registry.map(l => `{{show:${l.name}}}`).join('\n')
    : '';
  return [
    `## 分析图已生成`,
    ``,
    `地图上已生成分析图层，但由于生成结论文本超时，未能自动撰写详细结论。`,
    ``,
    `**已产出图层**：`,
    _layers,
    ``,
    `可点击上方图层按钮查看详情，或尝试简化问题后重试（如指定更具体区域/时点）。`,
  ].join('\n');
}
```

**效果**：即使 finalStep 超时，用户看到的不再是冷冰冰的「[请求失败]」，而是「分析图已生成 + 图层按钮」。图与文不再矛盾。

#### Layer 4（可选）：流式渲染 toolHistory 中的 observation

当 finalStep 还在等待 LLM 响应时，toolHistory 中的 observation（如「已生成聚合层（838 单元）」）可先行渲染到对话区，作为「临时结论」。finalStep 文本到达后再替换。

这需要在 `panel.js` 中修改 `onFinal` hook 的逻辑——在第一次 token 到达前先展示 observation 摘要。

---

## 问题二：2D/3D 按钮导致图层跳转至网格聚合组

### 2.1 现象

```
EMC 图层组: [网格聚合层] [2D|3D 按钮]
     │
     ├── 点击 2D/3D 按钮
     │
     ▼
EMC 图层组: (空·0 个图层)          ← 图层"消失"
网格聚合组: [网格聚合层·2D]         ← 图层"跳转"到这里
     │
     ├── 再次点击
     │
     ▼
EMC 图层组: [网格聚合层]            ← 图层"回来"了
网格聚合组: (隐藏)
```

### 2.2 根因

**文件**：`frontend/js/map.js:395-397`（`toggleGridViewMode`）和 `map.js:362-365`（`setViewMode`）

两处代码创建新配对图层时，**遗漏了 `parentId`**：

```javascript
// map.js:393-398 — toggleGridViewMode
pair = addLayer({ name: ..., kind: 'polygon', fc: l.fc,
                  paint: { ...l.paint, _ui: { ...l.paint._ui, mode: target } } });
// ❌ parentId: l.parentId 未传递
```

```javascript
// map.js:362-365 — setViewMode
pair = addLayer({ name: ..., kind: 'polygon', fc: l.fc,
                  paint: { ...l.paint, _ui: { ...l.paint._ui, mode: target } } });
// ❌ parentId: l.parentId 未传递
```

**完整链路**：

| 步骤 | 事件 | 位置 |
|:---:|------|------|
| 1 | EMC 生成网格层 → `_adoptToolboxResult` 设置 `parentId = _aiGroup().id` | `tools.js:698-702` |
| 2 | Sidebar 渲染 2D/3D 按钮 | `sidebar.js:292-298` |
| 3 | 用户点击 → `toggleGridViewMode(layerId)` | `sidebar.js:441-446` |
| 4 | 创建新配对图层 `addLayer({...})` **无 `parentId`** | `map.js:393-398` 🔴 |
| 5 | 新图层 `parentId=null` → `categoryOf()` 返回 `'grid'` | `state.js:876` |
| 6 | `applyGroupOrder()` 将新图层归入网格聚合组 | `state.js:934-977` |
| 7 | Sidebar `skipIds` 去重：原图层(隐藏·在 EMC 组)与新图层(可见·在网格组)同签名 → 原图层被 skip | `sidebar.js:360-376` |
| 8 | EMC 组 `children` 过滤 skipIds 后为空 → 显示 count=0 | `sidebar.js:402` |
| 9 | 再次点击 → 找已有配对 → 原图层恢复可见 → EMC 组恢复 | `map.js:383-388` |

### 2.3 修复

**两处各加 1 行**：

```javascript
// map.js:362 — setViewMode
pair = addLayer({ name: ..., kind: 'polygon', fc: l.fc,
                  parentId: l.parentId,           // ← 加这行
                  paint: { ... } });

// map.js:395 — toggleGridViewMode
pair = addLayer({ name: ..., kind: 'polygon', fc: l.fc,
                  parentId: l.parentId,           // ← 加这行
                  paint: { ... } });
```

`addLayer()`（`state.js:702-704`）已自动处理 `parentId`——将新图层 ID 推入父组的 `children` 数组。无需额外改动。

---

## 三、实施计划

### 立即执行（P0）

| # | 问题 | 文件 | 改动 | 验证 |
|---|------|------|------|------|
| 1 | finalStep 超时 | `prompts.py:164` | `build_final_prompt` 增加 `light=True` 参数（answer 阶段用轻量 prompt） | 同一问题 finalStep 耗时从 30-60s 降到 <25s |
| 2 | finalStep 超时 | `harness.js:366` | `runTemplatePath` finalStep 加 try/catch + 降级结论生成 | 超时时显示"分析图已生成"而非"[请求失败]" |
| 3 | 2D/3D 跳转 | `map.js:362,395` | 两处 `addLayer` 补 `parentId: l.parentId` | 点击 2D/3D 图层留在 EMC 组 |

### 后续（P1）

| # | 问题 | 文件 | 改动 |
|---|------|------|------|
| 4 | finalStep 超时 | `api.js:32` | answer phase 超时延至 60s |
| 5 | finalStep 超时 | `harness.js:414` | `runChainPath` finalStep 同样加 try/catch |
| 6 | 流式渲染 | `panel.js` onFinal hook | 在第一个 token 前先渲染 observation 摘要 |

---

*审计覆盖：`frontend/js/ai_qa/api.js`(Supervisor 全量)、`frontend/js/ai_qa/harness.js`(runTemplatePath/runChainPath/while-loop 全量)、`ai_qa/prompts.py`(build_final_prompt/FINAL_TEMPLATE 全量)、`ai_qa/manifesto.py`(全量)、`ai_qa/industry_kb/`(4 领域全量)、`frontend/js/map.js`(setViewMode/toggleGridViewMode 全量)、`frontend/js/sidebar.js`(renderLayerList/skipIds 全量)、`frontend/js/state.js`(addLayer/categoryOf/applyGroupOrder 全量)*
