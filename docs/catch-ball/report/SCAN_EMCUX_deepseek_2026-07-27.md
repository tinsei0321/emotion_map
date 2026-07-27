# EMC 用户体验问题专项评估（审查等待 + 删除符号）

> **评估方**：DeepSeek（第三方 LLM）  
> **评估日期**：2026-07-27  
> **评估触发**：L1 整改落地后的两个 UX 问题  
> **CB 轮次**：CB-04（EMC 评估轨·第三轮 — UX 专项）  
> **评估范围**：审查机制全链路（reviewStep → reviseStep → UI 渲染）+ 删除符号双根因追踪

---

## 问题一：审查等待时间不合理

### 1.1 现象复现

**用户描述**：
> 在"思考"阶段，地图上已经生成了分析图（EMC 组也正常显示出），但是 EMC 的对话状态仍在"思考"阶段，并且经常会出现"审查未通过"情况，然后又继续等待。

**技术还原**（以 density 单技能路径为例）：

| 时间 | 事件 | UI 显示 | 关键位置 |
|------|------|---------|---------|
| t=0 | 用户发送消息 | dock 出现，dots 动画，"诊断" | `panel.js:1447` |
| t=0-3s | Flash diagnose LLM | dots 继续，"思考" | `harness.js:540` |
| t=3s | runTemplatePath 开始 | dots 继续，"思考" | `harness.js:610` |
| **t=4s** | **TOOLS.density() → renderLayer() → 地图已更新** | **dots 继续，"思考"** | `heatmap-tool.js:865` |
| t=4-15s | finalStep LLM（生成结论文本） | dots 继续，"思考"→"生成" | `harness.js:366` |
| t=15s | 结论文本流式出现 | dots 停止，"审查中…" | `panel.js:1335` |
| t=15-18s | reviewStep LLM | "审查中…" | `harness.js:821` |
| t=18s | 审查结果 | "审查未过·重写中" 或 "审查通过" | `panel.js:870` |
| t=18-25s | reviseStep LLM（若未过） | "审查未过，重写中…"→ 重写文本 | `harness.js:835` |

**核心矛盾**：地图在 t=4s 已就绪，但文本在 t=15-25s 才出现，中间 10-20 秒用户看到地图变了但对话状态仍在"思考"。

### 1.2 根因链

#### 根因 1：post-tool LLM 调用串行阻塞

工具执行（t=4s）之后，以下 LLM 调用**串行执行**，每个都阻塞后续：

```
finalStep LLM (5-15s) → reviewStep LLM (2-4s) → [reviseStep LLM (5-10s)]
```

三轮 LLM 调用累计 12-30 秒，全部在文本出现前完成。**没有并行化、没有流式穿插、没有提前展示部分结果。**

文件位置：
- `harness.js:366` — finalStep LLM（runTemplatePath）
- `harness.js:821` — reviewStep LLM（while-loop 路径）
- `harness.js:835` — reviseStep LLM（若审查失败）

#### 根因 2：runTemplatePath 无工具完成信号

`runTemplatePath`（单技能路径，最常用的 fast path）**从不调用 `hooks.onObservation`**。对比：

| 路径 | 工具执行后的 UI 信号 | 文件位置 |
|------|---------------------|---------|
| runTemplatePath | ❌ 无信号 | `harness.js:325-366` — 跳过了 onObservation |
| runChainPath | ✅ `hooks.onObservation(obs, i+1)` | `harness.js:396` |
| while-loop ReAct | ✅ `hooks.onObservation(obs, round)` | `harness.js:709` |

这意味着最常见的 density/zonal/rank 单技能请求，地图更新后**完全没有 UI 状态切换**。

#### 根因 3：审查假阳性（正确结果被判"未通过"）

审查机制设计：

| 维度 | 详情 | 文件位置 |
|------|------|---------|
| **审查模型** | Flash（小模型，快但不精确） | `review.py:60` |
| **硬失败项** | `data_driven` / `actionable` / `scale_paradigm_fit` / `professional` | `review.py:175` |
| **失败判定** | 任一硬失败项 `verdict=fail` → `pass=false` | `review.py:179-180` |
| **假阳性场景** | Flash 误判「简洁正确」的答案为「不够数据驱动」 | — |

**假阳性的典型路径**：
1. EMC 生成了一条正确且简洁的结论（如"西陵区情绪偏消极，极性指数 -0.45"）
2. Flash 审查员检查 `data_driven` 项（要求"每个判断都有具体数值与区域支撑"）
3. Flash 因上下文截断或理解偏差，判定 `verdict=fail`
4. 触发 reviseStep → 又多等 5-10 秒 → 重写后的文本可能更差（Flash 模型生成能力有限）

**更讽刺的是**：对于 density 单技能路径（runTemplatePath），审查**本就被跳过了**（`harness.js:374`：`review: { pass: true, degraded: true, skipped: 'single-template' }`）。用户看到的"审查未通过"更可能发生在 **while-loop ReAct 路径**（多轮推理后走审查），此时用户已经等了很久。

#### 根因 4：审查范围窄但体感差

审查**仅对 `emotion_analysis`（intent C）答案生效**。统计跳过条件：

| 跳过条件 | 文件位置 |
|----------|---------|
| intent=general | `harness.js:589` |
| intent=gis_operation | `harness.js:814` |
| single-template | `harness.js:374` |
| chain-path | `harness.js:417` |
| request_upload | `harness.js:599` |
| drift/hallucination | `harness.js:761/773` |
| partial | `harness.js:801` |

**实际上大部分路径都跳过了审查**。审查主要落在 ReAct while-loop 路径（multi/unknown 模板），而这恰恰是用户**等得最久**的路径（多轮 agent_step LLM + finalStep + review + revise）。

### 1.3 用户提出的两个方案评估

#### 方案 A：重新制作审查环节

| 维度 | 评估 |
|------|------|
| **优点** | 保留质量门禁，治假阳性 |
| **可行改进** | ① 提审模型（Flash→Pro）减少假阳性；② 缩硬失败项范围（只保留 `data_driven` + 新增 `no_action` 防"只说不做"）；③ 主观项（layout/concise/structure）改为仅记录不进阻塞 |
| **耗时改善** | 有限——仍多 1 次 LLM 调用（2-4s）。假阳性减少但无法根除（小模型固有局限） |
| **工程代价** | 中等——改 `review.py` 清单 + prompt + 前端 UI |

**结论**：可改善但无法根治等待问题。审查的本质矛盾是「用小模型快速检查大模型输出」——快则不精，精则不快。

#### 方案 B：去掉审查机制，整合入结果输出范式

| 维度 | 评估 |
|------|------|
| **优点** | 完全消除审查等待（省 2-12s），架构简化 |
| **风险** | 失去质量门禁——"只说不做"、"数据臆造"等违规没有代码级拦截 |
| **现有替代** | `_verifyClaims`（`harness.js:218`）已提供代码级防臆造——比对声称图层 vs 实际图层。这是**确定性**的，比 LLM 审查更可靠 |
| **需补强** | ① 增加「空答案检测」（finalStep 产出纯叙述无工具调用 → 触发 GAP）；② 在 finalStep prompt 中内嵌自查清单（让主 LLM 自己检查数据驱动/可操作/不臆造）；③ 保留 `_verifyClaims` 作为最后防线 |

**结论**：**推荐方案 B**，理由如下。

### 1.4 推荐方案：去掉独立审查，改为「内嵌自查 + 代码门禁」双层机制

#### 架构原理

对照「Smart Agent, Dumb Tool」内核：

| 现有设计 | 问题 | 改进后 |
|----------|------|--------|
| Smart（finalStep）→ Flash Review（独立 LLM）→ Smart（reviseStep） | 两个 LLM 串行，小模型审大模型 = 假阳性 + 慢 | Smart（finalStep + 内嵌自查规则）→ 代码门禁（`_verifyClaims` + 空答案检测） |
| 审查 LLM 是独立调用 | 多一次网络往返 + token 消耗 | 自查规则注入 finalStep prompt，零额外调用 |

#### 具体设计

**第一层：finalStep prompt 内嵌自查规则**（`prompts.py` FINAL_TEMPLATE）

在 FINAL_TEMPLATE 末尾增加自查清单，让主 LLM 在生成结论时自我检查：

```
【自查清单·生成结论前必过】
1. 数据驱动：结论中每个判断是否附了具体数值/区域名？（禁止"情绪偏负面"无数据支撑）
2. 有工具产出：是否引用了实际工具产出的图层/结果？（禁止纯叙述无工具）
3. 不臆造：所有地名/数值是否来自工具观察？（禁止编造不存在的地名/数字）
4. 可操作：结论是否给出了具体方向/建议？（至少 1 条可行动建议）
5. 不自 contradict：结论与工具观察是否一致？（若工具显示负面，不能说正面）
有不满足的，在结论中诚实标注局限，不要强行满足。
```

这比外部 Flash 审查更有效，因为：
- 主 LLM（Pro/DeepSeek V4）比 Flash 更聪明，更理解自己写的内容
- 零额外 LLM 调用，不增加等待时间
- 自查在生成时执行，不是事后修补

**第二层：代码门禁（确定性，无 LLM）**

保留并增强现有门禁：

| 门禁 | 位置 | 功能 | 改进 |
|------|------|------|------|
| `_verifyClaims` | `harness.js:218` | 比对声称图层 vs 实际图层 | ✅ 保留 |
| **新增：空答案检测** | `harness.js` finalStep 后 | 若工具产出 > 0 但结论 < 20 字符 → 标记 degrade | 🔑 防"只说不做" |
| **新增：反删除符号过滤** | `api.js` 或 `panel.js` | 硬过滤 `~~...~~` 模式 | 解决问题二 |

**第三层：审查降级为可选诊断工具**

原审查机制不删除，改为：
- 默认关闭（`REVIEW_ENABLED = false`）
- 用户可在 console 开启（`localStorage.setItem('emcReviewOn', '1')`）
- 用于调试/诊断——当怀疑结论质量时手动开启

#### 等待时间改善估算

| 路径 | 当前耗时 | 改进后耗时 | 节省 |
|------|---------|-----------|------|
| runTemplatePath（单技能） | finalStep(5-15s) | finalStep(5-15s) | **无变化**（本就没审查） |
| runChainPath（多步链） | finalStep(5-15s) | finalStep(5-15s) | **无变化**（本就没审查） |
| while-loop ReAct（多轮） | finalStep(5-15s) + review(2-4s) + [revise(5-10s)] | finalStep + 内嵌自查(5-15s) | **省 7-14s** |

#### 改善 runTemplatePath 的 UX（补充）

审查去掉后，runTemplatePath 仍需解决「地图已出但文字没出」的 UX 问题。建议：

```javascript
// harness.js:325 — runTemplatePath 工具执行后
// 当前：直接跳 finalStep
// 改进：加 onObservation 信号 + dock 状态切换
if (hooks.onObservation) {
  hooks.onObservation(`工具执行完成，正在生成结论…`, 1);
}
```

并在 `panel.js` 中让 `onObservation` 在 dock 上显示「地图已更新·生成结论中…」替代原来的 dots 动画。

---

## 问题二：结论中出现删除符号（地名胶囊被划掉）

### 2.1 现象

地名胶囊（如 `[ref:西陵区]`、`[ref:伍家岗区]`）被渲染为带删除线的样式，意义不明。

### 2.2 双根因

#### 根因 A：LLM 输出 `~~text~~` → marked GFM 解析为 `<del>` 标签

**全链路**：

1. DeepSeek LLM 生成结论时，可能输出 `~~西陵区~~` 或 `~~[ref:西陵区]~~`（GFM 删除线语法）
2. 前端 `renderAnswer()` 调用 `marked.parse(text)`（`panel.js:442`）
3. `marked` 配置 `gfm: true`（`vendor/marked.min.js:12`），GFM tokenizer 含 `del` 规则
4. `~~text~~` 被转为 `<del>text</del>` → 浏览器默认渲染删除线

**为什么 LLM 会输出 `~~`**：

| 原因 | 说明 | 文件位置 |
|------|------|---------|
| **REVISE_TEMPLATE 缺失规则** | FINAL_TEMPLATE 有规则 6「禁 markdown 删除线」（`prompts.py:130`），但 **REVISE_TEMPLATE 没有**（`prompts.py:292-312`） | `prompts.py:292` |
| 审查未过 → 走 reviseStep | revise 时 LLM 不受「禁~~」约束，可自由输出 `~~` | `harness.js:835` |
| DeepSeek 天然倾向 | DeepSeek 模型在"修正/废弃/不确定"语境下会使用 `~~` 标记 | — |
| 无硬过滤 | `api.js:64` 的控制字符过滤不覆盖 `~~`（0x7E 是 tilde，非 DEL 控制字符） | `api.js:64` |

**关键发现**：当前修复（`prompts.py:130` 规则 6）只在 FINAL_TEMPLATE 中生效。但审查失败 → revise 路径使用的是 REVISE_TEMPLATE，**完全没有「禁~~」规则**。这解释了为什么修复后仍然出现——所有经过 revise 的答案都可能重新引入 `~~`。

#### 根因 B：`[ref:地名]` 芯片被标记为 `cite-chip-invalid` → CSS 删除线

**全链路**：

1. EMC 结论中包含 `[ref:西陵区]`（按照 `manifesto.py:68` 规范："引用区域一律标 [ref:区域名]"）
2. 前端 `renderAnswer()` 将 `[ref:地名]` 正则替换为 `<button>` 芯片（`panel.js:443-447`）
3. 替换时调用 `getValidRefNames()` 检查地名是否有效（`panel.js:842-855`）
4. **`getValidRefNames()` 范围极度狭窄**——只检查：
   - `kind === 'polygon'` 的图层
   - 且 `paint._ui.tool === 'grid'` 或 `'terrain'`
   - 且 feature 有 `properties.name` 或 `properties.issue_label`
5. 如果地名来源不是 grid/terrain 层（如来自 `zonal_stats`、`area_stats`、`extract_feature` 等其他工具），验证失败
6. CSS 类 `cite-chip-invalid` 应用 → `text-decoration: line-through`（`ai_qa.css:284`）

**为什么大量地名胶囊被划掉**：

| 场景 | 为什么 invalid |
|------|---------------|
| 地名来自 zonal_stats 图层 | `getValidRefNames()` 只看 grid/terrain |
| 地名来自 area_stats 图层 | 同上 |
| 地名来自 extract_feature 图层 | 同上 |
| 图层是中间产物已被清理 | 渲染时图层已不存在 |

### 2.3 为什么没彻底解决

| 尝试 | 为什么不够 |
|------|-----------|
| prompt 规则 6「禁 markdown 删除线」 | 只覆盖 FINAL_TEMPLATE，REVISE_TEMPLATE 缺失；且是软约束 |
| 控制字符过滤（`api.js:64`） | `~~` 不是控制字符，不匹配 |
| `cite-chip-invalid` 设计意图 | 原是「未验证=标记」的设计，但范围过窄产生大量假阳性 |

### 2.4 根治方案

#### 方案：硬过滤 + prompt 补全 + ref 验证范围扩展（三层防御）

**Layer 1：硬过滤 `~~`（治根因 A·不可绕过）**

在 `panel.js` 的 `renderAnswer()` 中，`marked.parse()` 之前或之后，用正则硬删除所有 `~~...~~` 包裹：

```javascript
// panel.js:441 — renderAnswer()
// 硬过滤：删除所有 ~~...~~（防止 marked 渲染为 <del>）
text = text.replace(/~~(.+?)~~/g, '$1');
// 然后再走 marked.parse()
let html = window.marked.parse(text);
```

**为什么放在 marked 之前**：如果在 marked 之后，`<del>` 标签已生成，需要用 DOM 操作去除——更复杂。正则预处理简单可靠。

**注意**：需处理跨行 `~~`（`/~~([\s\S]+?)~~/g`，非贪婪）。

**Layer 2：REVISE_TEMPLATE 补全规则（治根因 A·源头减少）**

在 `prompts.py:292` REVISE_TEMPLATE 中加入与 FINAL_TEMPLATE 相同的规则 6：

```
6. **禁 markdown 删除线**——勿输出 ~~ 包裹的文本（会渲染成删除符号·用户困惑）
```

**Layer 3：扩展 `getValidRefNames()` 范围（治根因 B）**

将 `panel.js:842-855` 的验证范围从仅 grid/terrain 扩展到所有 polygon 图层（不限制 `_ui.tool`）：

```javascript
// Before (panel.js:842-855):
for (const l of getLayers()) {
  if (l.kind === 'polygon' && l.paint && l.paint._ui &&
      (l.paint._ui.tool === 'grid' || l.paint._ui.tool === 'terrain')) {
    // ...
  }
}

// After: 检查所有 polygon 图层（zonal_stats/area_stats/extract 等工具产出均覆盖）
for (const l of getLayers()) {
  if (l.kind === 'polygon' && l.fc && l.fc.features) {
    for (const f of l.fc.features) {
      const name = (f.properties || {}).name;
      if (name) names.add(name);
    }
  }
}
```

**为何安全**：`cite-chip-invalid` 的原始设计意图是标记「LLM 编造的不存在地名」。扩展范围后，只要地图上存在同名 polygon feature 即视为有效——这比原设计更合理（zonal_stats 产出的西陵区 polygon 同样是"存在的地名"）。

**Layer 4（可选·保险）**：`cite-chip-invalid` 的视觉降级

即使地名真的 invalid（LLM 确实编造了不存在的地名），改用**弱化而非删除线**的视觉：

```css
/* ai_qa.css:284 — 改 cite-chip-invalid */
.cite-chip-invalid {
  opacity: 0.5;                    /* 弱化，非删除线 */
  /* text-decoration: line-through; */  /* 移除 */
  cursor: not-allowed;
  pointer-events: none;
}
```

删除线在中文语境中暗示"这个信息是错的/废弃的"，对用户困惑度远高于 opacity 弱化。

---

## 三、综合建议与优先级

| 优先级 | 问题 | 方案 | 改动文件 | 效果 |
|:---:|------|------|------|------|
| **P0** | 删除符号 | Layer 1：硬过滤 `~~` | `panel.js:441` | **彻底消灭**——正则预处理，不依赖 prompt 软约束 |
| **P0** | 审查等待 | 去掉独立审查 + 内嵌自查 | `harness.js:34` + `prompts.py` FINAL_TEMPLATE | ReAct 路径 **省 7-14s**，消除假阳性 |
| **P1** | 地图已出但 dock dots 不停 | runTemplatePath 加 onObservation | `harness.js:325` + `panel.js:1320` | 最常见路径的 UX 改善 |
| **P1** | 删除符号 | Layer 2：REVISE_TEMPLATE 补规则 | `prompts.py:292` | 源头减少 `~~` 产生 |
| **P2** | 地名芯片划掉 | Layer 3：扩展 `getValidRefNames()` | `panel.js:842` | 消除假阳性 invalid |
| **P2** | 地名芯片划掉 | Layer 4：改 invalid 视觉为弱化 | `ai_qa.css:284` | 即使真的 invalid 也不困惑用户 |

---

## 四、关于"去掉审查"的补充论证

### 为什么审查机制在当前架构下是低杠杆的

1. **覆盖范围窄**：大部分路径（single-template/chain/general/gis_operation）本就跳过审查。审查主要落在 while-loop ReAct 路径——而这恰恰是用户等得最久的路径。
2. **假阳性率高**：Flash 小模型审 DeepSeek V4 大模型的输出，语义理解能力不对称。4 个硬失败项中任何一个被 Flash 误判，都触发 5-10s 的 revise 惩罚。
3. **已有更可靠的替代**：`_verifyClaims`（`harness.js:218`）是**确定性代码门禁**，比 LLM 审查更可靠——图层存在性是可验证的事实，不需要 LLM 判断。
4. **用户核心价值是体验**：EMC 的价值在于"快速得到可视化分析 + 简洁结论"。审查增加的 2-14s 等待 + 可能的重写，与"快速"矛盾。

### 去掉审查后的防护

| 风险 | 防护机制 | 可靠性 |
|------|---------|:---:|
| LLM 只说不做（无工具调用出结论） | 空答案检测（代码级） + `_verifyClaims` | ✅ 确定性 |
| LLM 编造数据/地名 | `_verifyClaims` + 扩展 `getValidRefNames()` | ✅ 确定性 |
| 结论质量低（不专业/不简洁） | finalStep 内嵌自查清单（prompt 级） | ⚠️ 软约束 |
| 结论与工具结果矛盾 | 内嵌自查清单 + `_verifyClaims` 交叉验证 | ✅ 半确定性 |

**核心判断**：代码级门禁（`_verifyClaims` + 空答案检测）覆盖了最关键的硬性错误（臆造数据、只说不做）。结论质量的软性问题（是否足够简洁/专业）交由 finalStep prompt 优化——这本身就是 Smart Agent 的职责（铁律 2：Agent 聪明只在两端）。不需要再插入一个小模型来做大模型的质量评判。

---

## 五、实施建议

### 立即执行（1 个会话）

1. **panel.js:441** — 加 `text.replace(/~~([\s\S]+?)~~/g, '$1')` 硬过滤
2. **harness.js:34** — `REVIEW_ENABLED` 默认 `false`
3. **prompts.py** FINAL_TEMPLATE — 增加内嵌自查清单（5 条）
4. **harness.js** finalStep 后 — 增加空答案检测

### 后续（下一轮次）

5. **harness.js:325** — runTemplatePath 加 onObservation
6. **prompts.py:292** — REVISE_TEMPLATE 补规则 6
7. **panel.js:842** — 扩展 `getValidRefNames()` 范围
8. **ai_qa.css:284** — 改 invalid 视觉为 opacity 弱化

---

*审计覆盖：`frontend/js/ai_qa/harness.js`(全量)、`frontend/js/ai_qa/stages.js`(review/revise 段)、`frontend/js/ai_qa/panel.js`(渲染+状态段)、`ai_qa/review.py`(全量)、`ai_qa/prompts.py`(FINAL_TEMPLATE/REVISE_TEMPLATE)、`frontend/vendor/marked.min.js`(GFM del tokenizer)、`frontend/css/ai_qa.css`(cite-chip 样式)*
