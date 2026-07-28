# EMC finalStep 超时根因分析 — 详细结论文本生成超时

> **分析方**：DeepSeek V4 Pro（ZCode 主线程）  
> **日期**：2026-07-28  
> **触发用例**：「根据上传的情绪点数据，做一个500m方格网的空间聚合分析」  
> **结果**：✅ 图层成功生成（1738 网格单元），❌ 结论文本超时 → 降级为「详细结论文本生成超时」

---

## 一、根因摘要

> **WS1 将 LLM 单次调用超时从 45s 降到 25s，但复杂查询的 finalStep 提示词（含完整 buildContext + formatRegistry + 工具历史）达到 5-10KB，LLM 生成中文长回复需要 25-35s，触发 25s 超时 → 降级结论。这不是一个需要大幅修复的工程问题，是两个参数调节失当的叠加效应。**

---

## 二、完整时序链

```
orchestrate() 开始 ──────────────────────────────────────────────── 30s 总预算
│
├─ buildContext + layerMeta + coref ..................... <100ms
│
├─ fcDiagnoseStep (FC, Flash) .......................... 5-8s
│   └─ POST /api/v1/chat → DeepSeek V4
│      timeout: 9s (WS1 F1.5)
│
├─ runTemplatePath → TOOLS.density(params) .............. 2-4s
│   └─ 本地计算：生成 1738 网格单元
│      timeout: 无（本地同步执行）
│
├─ finalStep 提示词构建 .................................. <10ms
│   ├─ FINAL_TEMPLATE .................................... ~1.1KB
│   ├─ tool_history（工具观察文本）......................... ~200B
│   ├─ formatRegistry() .................................. ~100B
│   └─ ctx.context（buildContext 输出 + diagnose 摘要）...... ~3-8KB
│   合计 .................................................. ~5-10KB
│
├─ finalStep LLM 调用 (Flash) .......................... 需要 25-35s
│   │                                                ↑
│   │                                     ╔══════════╪══════╗
│   │                                     ║  per-call timeout  ║
│   │                                     ║  25000ms (api.js)   ║
│   │                                     ╚═════════════════════╝
│   │
│   └─ ⚡ 25s 到期 → AbortError → catch(e) → _composeDegradedConclusion()
│                                                        │
│   用户看到：                                             │
│   "详细结论文本生成超时·可点击上方图层按钮查看"            │
│                                                        │
│   但图层已成功生成！只是结论文本没出来。                    │
└──────────────────────────────────────────────────────────┘
```

---

## 三、根因分析

### 根因 1（🔴 主因）：per-call 超时 45s→25s 过于激进

| 指标 | WS1 之前 | WS1 之后 | 实际需要 | 判断 |
|------|:---:|:---:|:---:|:---:|
| FC 诊断超时 | 20s | 9s | 5-8s | ✅ 合理 |
| LLM 单次调用超时 | 45s | **25s** | 4-35s | 🔴 简单 4-10s，复杂 25-35s |
| 总预算 | 75s | 30s | — | 🟡 快路径不检查 _deadline |

25s 对 80% 的查询足够（finalStep 通常 4-10s），但对复杂查询（大接地上下文 + 多产出 + 长回复要求）finalStep 需要 25-35s。本案例的 1738 个网格单元触发了这个边界。

**证据**：`api.js:32` — `const _timeout = 25000`

### 根因 2（🟡 辅因）：finalStep 提示词含冗余上下文

`runTemplatePath` 在调用 finalStep 前重构了 `ctx.context`（`harness.js:523`）：

```javascript
ctx.context = `【单技能路径·已执行 ${def.tool}】...\n【地图实际产出图层】${formatRegistry()}...\n\n` + (ctx.context || '');
```

原始 `ctx.context` 包含完整的 `buildContext()` 输出（所有图层列表、字段详情、数据摘要），但这些信息在工具已执行完成后**对写结论不再必要**。多余的 token 增加了 LLM 的输入处理时间和输出生成时间。

**对比**：
- 需要的信息：执行了什么工具、产出了什么、当前有哪些图层
- 当前发送的信息：以上 + 全部图层字段详情 + 数据摘要 + 极性计数 + 高张力区域列表

### 根因 3（🟢 无直接影响）：`_deadline` 不检查快路径

`_deadline = 30s` 只在 while-loop 中检查（`harness.js:893`），不走 while-loop 的快路径（`runTemplatePath`）不受总预算约束。这意味着即使总时间远超 30s，只要单次 LLM 调用不超 25s，就不会触发超时。对本次案例无直接影响，但对 while-loop 场景有约束力。

---

## 四、为什么图层生成成功了但结论失败？

```
✅ 图层生成：本地计算（2-4s），不经过 LLM，不受超时影响
❌ 结论生成：LLM 调用（需 25-35s），触发 25s 超时 → 降级
```

**这不是"系统崩溃"，是"LLM 慢了 + 超时设紧了"。** 图层在 MapLibre 中正常显示，只是文本结论换成了降级模板。

---

## 五、修复方案

### 方案 A（推荐·最小改动）：per-call 超时调回 35s

| 位置 | 当前值 | 建议值 | 理由 |
|------|:---:|:---:|------|
| `api.js:32` | 25s | **35s** | 覆盖复杂 finalStep（25-35s），同时不退回 45s 的过度等待 |

**改动**：1 行。

### 方案 B（推荐·治本）：finalStep 提示词瘦身

在 `harness.js:523` 处，finalStep 调用前裁剪 `ctx.context`：

```javascript
// 当前：注入完整 ctx.context（含 buildContext 全量字段详情）
// 改进：只保留结论必需的信息
ctx.context = `【单技能路径·已执行 ${def.tool}】基于上述工具观察直接出结论。\n【地图实际产出图层】${formatRegistry()}\n` + (ctx.context || '');
```

并将 `buildContext` 的详细字段信息从 finalStep 的 context 中移除（工具已执行，字段细节不再需要）。

**改动**：~3 行。

### 方案 C（辅助）：finalStep 使用 Flash 时适当降低 max_tokens

当前 `FINAL_TEMPLATE` 要求 LLM 输出结构化中文报告 + 追问胶囊。对于简单查询这是合理的，但对于复杂查询可以设 `max_tokens` 上限避免生成过长响应。

**改动**：在 `streamChat` 调用时加 `max_tokens` 参数。

### 方案 D（长期）：分阶段超时

不同阶段的 LLM 调用应有不同的超时：
- FC 诊断（Flash，轻量）：9s ✅
- finalStep（Flash，中等）：35s（建议）
- agentStep（Pro，推理）：45s
- deliberateStep（Pro，研判）：20s

---

## 六、推荐实施

| 优先级 | 方案 | 操作 | 改动 |
|:---:|:---:|------|:---:|
| **立即** | A | per-call 超时 25s → 35s | 1 行 |
| **立即** | B | finalStep 上下文瘦身 | 3 行 |
| 短期 | C | max_tokens 上限 | 1 行 |
| 中期 | D | 分阶段超时 | ~10 行 |

---

## 七、相关代码位置

| 文件 | 行 | 作用 |
|------|:---:|------|
| `frontend/js/ai_qa/api.js` | 32 | `_timeout = 25000` — per-call 超时（根因点） |
| `frontend/js/ai_qa/harness.js` | 523 | finalStep 前 ctx.context 重构（含冗余 buildContext） |
| `frontend/js/ai_qa/harness.js` | 527 | finalStep 调用 |
| `frontend/js/ai_qa/harness.js` | 529-531 | finalStep 超时 → `_composeDegradedConclusion` 降级 |
| `frontend/js/ai_qa/harness.js` | 420-432 | `_composeDegradedConclusion` — 降级结论模板 |
| `frontend/js/ai_qa/harness.js` | 733 | `_deadline = 30000` — 总预算（不检查快路径） |
| `ai_qa/prompts.py` | 116-144 | `FINAL_TEMPLATE` — 提示词模板（~1.1KB） |
| `frontend/js/ai_qa/tools.js` | 562-641 | `buildContext()` — 接地上下文（含全量字段详情） |

---

> **归档信息**：`docs/catch-ball/emc-arch-deepdive/ROOTCAUSE_finalstep_timeout_2026-07-28.md`
