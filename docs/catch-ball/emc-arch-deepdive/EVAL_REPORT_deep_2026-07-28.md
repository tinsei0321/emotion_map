# EMC 架构重构 · 深度评估报告（v2 · 含实测定性分析）

> **评估方**：DeepSeek（ZCode 主线程）  
> **日期**：2026-07-28  
> **触发**：用户实测 "剪裁西陵区范围" 失败 → 逐行代码 tracing 定位根因  
> **方法**：6 并行 Agent 代码审查 + 手动逐函数 tracing + git history 对账  
> **上一版**：`EVAL_REPORT_comprehensive_2026-07-27.md`（被本报告取代）

---

## 零、实测故障 Tracing

### 0.1 用户操作

1. 上传了一个面图层（"中心城区范围"→ polygon boundary）
2. 输入指令：「剪裁西陵区范围」
3. 系统返回失败：「multi→clip 没跑通」并要求上传情绪点数据

### 0.2 完整代码路径逐行 Trace

#### Step 0：意图预判 `_quickIntent`（`harness.js:16-28`）

```
输入: "剪裁西陵区范围"
→ 概念词检测: 什么是/含义/区别... → 无命中
→ geo 动词检测: 核密度/热力/裁剪/缓冲... → "裁剪" 在列表中 → 返回 null（非 general）
→ 结论: 不短路，进入完整管线
```

#### Step 1：0LLM 候选选择 `select_candidates`（`candidate_selector.py`）

```
select_candidates('剪裁西陵区范围', None)   ← context=None!
                                            ↑ 关键：无数据上下文！

1. _b_hits('剪裁西陵区范围'):
   遍历 B_TRACK_PARADIGM 9 个模板 → 逐一检查 triggers:
   
   buffer:   周边/附近/半径/缓冲/米内/公里内           → ✗
   nearest:  最近/邻近/最近邻                          → ✗
   density:  核密度/密度分析/热力/网格/方格网/聚合域    → ✗
   hotspot:  聚集/热点/冷热/显著聚集                    → ✗
   overlay:  交集/叠置/叠加/里的/用地中/两图            → ✗
   merge:    合并/合成/dissolve/并成                    → ✗
   clip:     范围内/区的/区内的/片区                    → ✗
             + ext: 里面的/当中的/某区/这个区/那个区/
                    剪裁/裁剪/裁剪出                    → ✓ '剪裁' 命中！
   extract:  抽某/裁出某/单独裁出/提取某                → ✗
             + ext: 只要/单独/抽出/抠出/裁出/提取/剪裁出
                    → '裁出' 检查: "剪裁西陵区范围"
                      s[1]='裁' s[2]='西' ≠ '出'     → ✗
   filter:   按字段/用地类/属性筛选/筛选某类             → ✗
   
   → b_hits = ['clip']

2. _derive_track('剪裁西陵区范围', ['clip']):
   A-keywords: 什么/原理/定义... → ✗
   compare-keywords: 对比/比较/差异... → ✗
   b_hits 非空 → track = 'B'

3. _is_compound(...):
   len(b_hits)>=2? → No (only 1)
   scope cues (区内/范围内/里的/...) ∩ analyze cues (密度/热力/归因/...)? → No
   → compound = False

4. candidates = ['clip']

5. context=None → _filter_by_context 跳过

6. 排序+截断: ['clip'] → ['clip'], pre_truncate=1

返回: {candidates:['clip'], track:'B', compound:False, ask_scenario:None}
```

**此刻的问题**：`select_candidates` 传入了 `None` 作为 context。即使前端已经检测到只有 polygon 数据（无 point 数据），这个信息**完全无法到达选择器**。`'剪裁' → 'clip'` 的映射是无条件执行的。

#### Step 2：Prompt 分派 `build_diagnose_prompt_dispatch`（`prompts.py:314`）

```python
cands = ['clip']
'multi' not in cands → True
→ return build_fill_card_prompt(question, ['clip'], context)
   path = 'fill_card', model = None (Flash)
```

FILL_CARD_TEMPLATE 向 Flash LLM 注入：
```
【预选工具】（template 只能取其一·method=[template]）：
- clip（范围裁取）：必填:range；可选：（无）
```

**规则 1：「template/method = 预选工具（1 个→直接填；多个→选最匹配问句的·禁选预选外的）」**

Flash **被禁止**选择 `extract_feature`——候选列表中只有 `clip`。

#### Step 3：Flash 填卡（LLM 调用）

Flash 看到：
- 问题：「剪裁西陵区范围」
- 唯一候选工具：clip（范围裁取）
- grounding 上下文：包含「中心城区范围（N条,面,...）」等已加载图层

Flash 输出 diagnose 卡：
```json
{
  "template": "clip",
  "params": {"range": "中心城区范围"},
  "method": ["clip"],
  "data_plan": {"strategy": "ready"}
}
```

#### Step 4：编排路由 `orchestrate`（`harness.js:765-767`）

```javascript
const _tdef = stages.SKILL_DEFS['clip'];
// _tdef = {tool:'clip', category:'single', required_slots:['range'], optional_defaults:{}}
// _tdef.category === 'single' → true
// _tplHitRateReady() → true
→ return await runTemplatePath(ctx, hooks, diagnose);
```

#### Step 5：单技能执行 `runTemplatePath`（`harness.js:406`）

```javascript
// 1. validateParams('clip', {range:'中心城区范围'})
//    required_slots=['range'], range 已填 → ok=true
// 2. TOOLS['clip']({range:'中心城区范围'})
```

#### Step 6：`TOOLS.clip()` 执行（`tools.js:979`） ← **💥 爆炸点**

```javascript
async clip(params = {}) {
    // params = {range: '中心城区范围'}  ← 没有 layer 字段！
    if (!params.range) return ...;       // range 有值 → 通过
    
    const _layer = resolvePointLayer(params);  // 找点层
    //   → params.layer 为 undefined
    //   → pickVisiblePointLayer()        // 扫描所有图层
    //       → 过滤 group 层 → 无 L2 group
    //       → 过滤 kind==='point' 的层 → **无点层！**
    //       → return null
    if (!_layer) return _ERR_NO_VISIBLE_PT();
    //  ↑ 返回: "[ERR] 无已加载的情绪点层——请先在 Layers 上传/加载情绪点数据"
}
```

**clip 的硬性约束**：`resolvePointLayer()` 必须找到至少一个 `kind==='point'` 且 `colorMode` 匹配 L2/L1 的图层。用户上传的是 polygon 面层，不满足此条件。

#### Step 7：错误恢复 `runTemplatePath`（`harness.js:459-477`）

```javascript
const failed = /\[ERR\]|失败|错误/.test(obs);     // → true
const recoverable = /无可见点|无可见情绪点/.test(obs); // → true

// recoverable → ask_user（而非 GAP 放弃）
const ask = {
    type: 'ask_user',
    question: `clip 没成功：无已加载的情绪点层...请按可用字段/数据重试`,
    options: ['我来指定正确的字段/值重试', '换一个分析方向', ...]
};
```

用户看到：「上传情绪点数据」的提示——**但用户的真实需求是从面层中抽取西陵区，跟情绪点数据毫无关系。**

---

## 一、根因分析（三层递进）

### 根因 1：0LLM 选择器数据盲（架构级缺陷）

```
用户数据：只有 polygon 面层，无 point 点层
                   ↓
         select_candidates(question, context=None)
                   ↓
          无法感知数据类型 → '剪裁' 无条件映射为 'clip'
                   ↓
          clip 需要 point 数据 → 硬失败
```

**问题本质**：0LLM 候选选择器设计上就是 context-unaware 的。`build_diagnose_prompt_dispatch`（`prompts.py:318`）调用 `select_candidates(question or '', None)`——第二个参数硬编码为 `None`。

即使前端 `buildContext()` 已经完整列出了所有已加载图层（包括面层、字段值域等），这些信息**完全不进入候选选择器**。

**影响范围**：所有涉及数据类型约束的工具选择（density/hotspot/rank/buffer/nearest 需要 point；clip 需要 point；extract_feature/overlay/merge 需要 polygon）都无法在 Stage 0 做出正确判断。

### 根因 2：'剪裁'语义映射错误（词→工具映射缺陷）

| 中文词 | 用户意图 | 0LLM 映射 | 正确映射 |
|--------|---------|:---:|:---:|
| 剪裁/裁剪 | 从面层中提取要素 | `clip`（点层空间裁剪） | `extract_feature`（面层属性抽取） |
| 裁出 | 从面层裁出某区域 | `extract_feature` ✅ | ✅ |

`_B_TRACK_TRIGGER_EXT`（`candidate_selector.py:54`）将 `'剪裁'` 注册为 clip 的触发词，注释写「补用户原话（"剪裁西陵区"曾误路由 zonal·5.241）」。

5.241 的修复方向错误：它把 "剪裁西陵区" 从 zonal 修正为 clip，但**正确的目标应该是 extract_feature**。在中文 GIS 口语中，「剪裁一个面层」通常指 extract（从面层中提取子集），而非 clip（用面裁剪点层）。

### 根因 3：恢复路径不智能（工具失败后无替代建议）

```
clip 失败 → ask_user "上传情绪点数据"
                         ↓
           extract_feature 就在旁边，却不被建议
```

`runTemplatePath` 的恢复逻辑（`harness.js:459-477`）检测到 `recoverable` 错误后，生成泛化的 ask_user 提示，**完全不知道 extract_feature 是可替代工具**。`TOOL_GEOMETRY_REQUIRE` 表已经记录了 clip 需要 point 数据，但这个信息在错误恢复时未被消费。

### 根因 4：FILL_CARD 候选集锁定过死（Flash 无法自适应）

FILL_CARD_TEMPLATE 规则：「禁选预选外的」——Flash LLM 即使识别出 extract_feature 更合适，也被规则禁止选择。这是**正确的设计意图**（候选选择由 0LLM 负责，Flash 只填卡），但当前 0LLM 选错了候选，Flash 没有纠错机制。

---

## 二、全链路数据流图（实测定性）

```
用户: "剪裁西陵区范围"
数据: 仅加载了 polygon 面层（中心城区范围），无 point 层

┌─ QuickIntent ───────────────────────────────────────────
│  "裁剪" 在 geo 动词列表 → null（不短路·进入完整管线）
├─ 0LLM select_candidates(question, context=None) ─────────
│  B-track triggers: '剪裁'∈clip_ext → candidates=['clip']
│  ⚠️ context=None → 不知数据只有 polygon
│  ⚠️ '剪裁'→clip 映射在 polygon-only 场景下语义错误
├─ Flash fill_card(candidates=['clip']) ───────────────────
│  规则: "禁选预选外的" → 只能选 clip
│  输出: template='clip', range='中心城区范围'
├─ runTemplatePath('clip', {range:'中心城区范围'}) ──────────
│  validateParams → ok (range 已填)
│  TOOLS.clip() → resolvePointLayer() → NULL（无 point 层！）
│  💥 return _ERR_NO_VISIBLE_PT()
├─ 错误恢复 ─────────────────────────────────────────────
│  recoverable=true → ask_user "上传情绪点数据"
│  ⚠️ extract_feature 是正确替代·系统不提
└─ 用户体验 ─────────────────────────────────────────────
   看到: "请上传情绪点数据"
   预期: "从中心城区范围中提取西陵区"
```

---

## 三、9 模块深度重评（含实测根因）

### 模块一：Diagnose Agent — 降级：A → B

| 决策 | 原评 | 实测后 | 说明 |
|------|:---:|:---:|------|
| D001 三阶段低耦合 | ✅ | ✅ | 架构正确，但 Stage 0→Stage 1 的 context 传递链断裂 |
| D002 Flash 只填充不推理 | ✅ | ⚠️ | 候选锁定过死——Flash 无法纠错 0LLM 的映射错误 |
| D003 信息卡绑定 schema | ✅ | ✅ | ok |
| D004 单卡→编排器 | ✅ | ✅ | ok |
| D005 单卡 confidence=low 也执行 | ✅ | ✅ | ok |
| D006 Flash prompt 1-3.5KB | ✅ | ✅ | 1.85KB，pass |
| D007 0LLM 纯规则 | ✅ | 🔴 | **纯规则但数据盲**——context=None 导致无法感知可用数据类型 |
| D008 数据三态归 Flash | ✅ | ✅ | ok |
| D009 Pro prompt 统一轻量 | ✅ | ✅ | ok |
| D010 复杂 CPD 拆解 | ✅ | ✅ | ok |
| D011 工具能力字典 | ✅ | ✅ | ok |

**新发现**：D007 设计为"纯规则不引入 LLM"，但实现中 `select_candidates(question, None)` 将 context 硬编码为 `None`，导致整个选择器对可用数据完全无感知。这是一个架构层面的设计遗漏：纯规则可以且应该消费结构化 context（field_roles / has_point / has_polygon），但调用方 `build_diagnose_prompt_dispatch` 没有传递。

### 模块九：字段识别（0LLM）— 降级：B+ → C

| 决策 | 原评 | 实测后 | 说明 |
|------|:---:|:---:|------|
| D035 字段→候选工具·截断 4 | ✅ | ✅ | 排序逻辑正确 |
| D036 关键词累积匹配 | ✅ | 🔴 | **'剪裁'→clip 映射在 polygon-only 场景语义错误** |
| D037 候选为空→短路 | ✅ | ⚠️ | 当前 clip 不为空但实际不可执行（缺 point）→ 不触发短路 |
| D038 候选≥5→追问 | ✅ | ✅ | ok |
| D039 追问文案纯中文 | ✅ | ✅ | ok |
| D040 density 维度分歧 | ⚠️ | ⚠️ | 仍未实现独立追问 |

**新发现**：D036 的 trigger 扩展方向有误。5.241 commit 将 `'剪裁'` 补入 clip 的 trigger 列表，但这治标不治本——当用户有 polygon 数据而无 point 数据时，正确的工具是 `extract_feature`，不是 `clip`。**修复方向应该是让选择器感知数据类型，而非穷举所有可能的 trigger 词映射。**

### 模块二：Orchestrator — 维持 B+

原评估中发现的 `_GEO_TOOLS` 缺 `ensure_zone`（Bug #1）仍然存在。其他无变化。

### 模块三：Execution Layer — 新增发现

| 项目 | 发现 |
|------|------|
| `TOOLS.clip()` | 硬依赖 point 数据——`resolvePointLayer()` 强制要求。用户有 polygon 无 point 时直接失败 |
| `TOOLS.extract_feature()` | 正确支持 polygon→polygon 操作——`_opExtract` 发送 `{layer, where}` 到 `/geo/extract_feature` |
| 错误恢复 | `_ERR_NO_VISIBLE_PT()` 消息误导——提示"上传情绪点数据"，而非"试试 extract_feature" |
| 工具间关系 | `TOOL_GEOMETRY_REQUIRE` 表已记录工具几何约束，但错误恢复时未消费 |

### 模块四~八：维持原评估

模块四（finalStep）、模块五（R+R）、模块六（prompt）、模块七（toolbox）、模块八（CPD）在本次实测中未暴露新问题，维持上一版评估。

---

## 四、Bug 清单（更新·共 8 项）

| # | 严重度 | 模块 | 描述 | 本次新发现 |
|:---:|:---:|:---:|------|:---:|
| **B1** | 🔴 高 | 模块一 D007 | `select_candidates` 被调用时传入 `context=None`，0LLM 选择器完全无法感知可用数据类型（point vs polygon）——导致所有数据类型敏感的候选过滤失效 | 🆕 |
| **B2** | 🔴 高 | 模块九 D036 | `'剪裁'/'裁剪'` 映射为 `clip`（点层空间裁剪），但在 polygon-only 场景下正确映射应为 `extract_feature`（面层属性抽取）。5.241 fix 方向有误 | 🆕 |
| **B3** | 🟡 中 | 模块三 | `TOOLS.clip()` 失败后错误恢复路径不智能——系统知道 extract_feature 是可替代工具（同一 `vector-tool.js` 文件），但不向用户建议 | 🆕 |
| **B4** | 🟡 中 | 模块二 D015 | `_GEO_TOOLS` 不含 `ensure_zone`（`harness.js:608`） | 延续 |
| **B5** | 🟡 中 | 追踪设施 | `MOD_AIQA.F_008` 被两个函数同时注册（碰撞） | 延续 |
| **B6** | 🟡 中 | 模块四 | `runCapsule` 硬编码 `intent:'emotion_analysis'` | 延续 |
| **B7** | 🟢 低 | 模块五 | `_verifyClaims` 与 `_extractClaimedLayers` 正则不一致 | 延续 |
| **B8** | 🟢 低 | 模块四 | FINAL_TEMPLATE 中 `B/C 类` 引用已移除的 MANIFESTO 术语 | 延续 |

---

## 五、风险清单（更新·共 10 项）

| # | 风险等级 | 描述 | 本次新发现 |
|:---:|:---:|------|:---:|
| **R1** | 🔴 高 | **0LLM 选择器数据盲**——`select_candidates(question, None)` 不消费 context。所有需要感知数据类型的选择（point 工具 vs polygon 工具）都可能出错。影响约 50% 的工具调用场景 | 🆕 |
| **R2** | 🔴 高 | **候选锁定无纠错机制**——FILL_CARD "禁选预选外" + Flash 必须填给定候选 = 0LLM 选错→全链路错。无 stage 间纠错回路 | 🆕 |
| **R3** | 🟡 中 | **trigger 词映射靠穷举**——`_B_TRACK_TRIGGER_EXT` 每发现一个映射错误就加一个词，无法从根本上解决语义歧义 | 🆕 |
| **R4** | 🟡 中 | `runChainPath` 缺乏分析型工具意识——仅检查 `newLayerCount`，不检查 `hasRows` | 延续 |
| **R5** | 🟡 中 | Flash hit-rate gate 60% 阈值可能导致平均延迟远超设计目标 | 延续 |
| **R6** | 🟡 中 | `paradigm.py` 与 `tool_contracts.py` 镜像同步依赖 CI 而非自动派生 | 延续 |
| **R7** | 🟢 低 | F_009/F_010/F_011 未注册追踪 ID | 延续 |
| **R8** | 🟢 低 | `_quickIntent` 路径绕过质量防线 | 延续 |
| **R9** | 🟢 低 | `runTemplatePath` 与 while-loop 的 finalStep 降级路径不对称 | 延续 |
| **R10** | 🟢 低 | D040 density 维度追问未独立实现 | 延续 |

---

## 六、优化建议（更新·共 15 条）

### P0（阻塞用户正常使用·立即修复）

| # | 建议 | 关联 |
|:---:|------|:---:|
| **S1** | **向 `select_candidates` 传入 context**：修改 `build_diagnose_prompt_dispatch`（`prompts.py:318`），从 `req.context` 中提取 `field_roles`/`has_point`/`has_polygon` 并传入，让 `_filter_by_context` 过滤掉不可执行工具。对"剪裁西陵区范围"场景：has_point=False → 过滤掉 clip（需要 point）→ 保留 extract_feature（无几何要求） | B1, R1 |
| **S2** | **修正 '剪裁/裁剪' 的映射**：将 `_B_TRACK_TRIGGER_EXT` 中的 `'剪裁'/'裁剪'` 从 `clip` 移至 `extract_feature`（或两个都加，让 context filtering 按数据类型裁决）。用户口语中"剪裁"更常指 polygon→polygon 提取 | B2 |
| **S3** | **clip 失败时智能建议 extract_feature**：在 `runTemplatePath` 的恢复逻辑中（`harness.js:459`），当 `def.tool === 'clip'` 且错误为 `_ERR_NO_VISIBLE_PT` 时，检查是否有 polygon 数据可用→如有，ask_user 中增加「尝试用 extract_feature 从面层抽取」选项 | B3 |

### P1（架构修复·尽快）

| # | 建议 | 关联 |
|:---:|------|:---:|
| **S4** | 在 `_GEO_TOOLS` 中补 `'ensure_zone'` | B4 |
| **S5** | 修复 F_008 碰撞 + 注册 F_009-F_011 | B5 |
| **S6** | `runCapsule` synthDiagnose 继承原始 intent | B6 |
| **S7** | 统一 `_verifyClaims` 和 `_extractClaimedLayers` 正则 | B7 |
| **S8** | FILL_CARD_TEMPLATE 增加兜底规则：「如果预选工具明显不适用（如数据不支撑），在 rationale 中说明并建议替代工具」——给 Flash 有限的纠错表达空间 | R2 |
| **S9** | `runChainPath` 引入 `_ANALYTICAL_TOOLS` 的 `hasRows` 检查 | R4 |

### P2（架构优化·持续）

| # | 建议 | 关联 |
|:---:|------|:---:|
| **S10** | 建立「工具几何能力矩阵」自动路由：point-only 工具在有 poly 无 point 时自动排除，并推荐替代工具。将 `TOOL_GEOMETRY_REQUIRE` 表前移到 0LLM 选择器，作为 context filtering 的一部分 | R1, R3 |
| **S11** | 实现 `tool_contracts.py` → `paradigm.py` 自动派生 | R6 |
| **S12** | 评估 Flash hit-rate gate 阈值（当前 60% → 建议 75%） | R5 |
| **S13** | `_quickIntent` 路径增加质量防线 | R8 |
| **S14** | 统一 `runTemplatePath` 和 while-loop 的 finalStep 降级路径 | R9 |
| **S15** | 为 `select_candidates` 实现 D040 density 维度分歧独立追问 | R10 |

---

## 七、架构设计反思

### 7.1 三阶段管线的 context 断裂

```
                    context 在此断裂
                         ↓
0LLM(select_candidates) ──→ Flash(fill_card) ──→ Pro(plan)
   ↑ context=None              ↑ context=文本       ↑ context=文本
   无数据感知                  有数据感知           有数据感知
```

0LLM 是整个管线的**唯一门控点**（决定哪些工具进入候选），但它是**唯一不感知数据的阶段**。这导致：

- 数据不支持的工具（如 polygon-only 场景下的 clip）通过了门控
- 数据支持的工具（如 extract_feature）被错误排除
- Flash 即使看到了完整的 grounding 文本，也无法纠正 0LLM 的选择

**架构原则**：门控点必须具备与下游同等或更强的信息获取能力。如果 0LLM 要做候选过滤，它必须能消费 context。

### 7.2 trigger 词穷举的不可持续性

`_B_TRACK_TRIGGER_EXT` 目前有 ~25 个扩展 trigger 词，每发现一个映射错误就加一个词。但中文 GIS 口语用词极其灵活：

| 用户可能说的 | 含义 |
|-------------|------|
| 剪裁西陵区 | extract from polygon |
| 裁出西陵区 | extract from polygon |
| 裁剪西陵区 | could be clip or extract |
| 切出西陵区 | extract |
| 抠出西陵区 | extract |
| 把西陵区裁出来 | extract |
| 只要西陵区 | extract / filter |
| 西陵区范围里的点 | clip (points in polygon) |

穷举无法覆盖所有变体。**正确的方案是 context-aware filtering**：让选择器先按关键词生成宽候选集（clip + extract_feature），再按可用数据类型过滤（有 point→保留 clip；有 polygon→保留 extract_feature）。

### 7.3 工具失败后的智能恢复

当前错误恢复路径：

```
工具失败 → obs 包含 [ERR] → recoverable 检测 → ask_user
```

理想路径：

```
工具失败 → 查 TOOL_GEOMETRY_REQUIRE 判断失败原因
         → 查可用数据中是否有替代工具的输入
         → 如有 → ask_user 明确建议替代工具
         → 如无 → ask_user 诚实地说明缺什么数据
```

---

## 八、总结

本次实测暴露了 EMC 架构中最核心的缺陷：**0LLM 候选选择器是数据盲的**。这导致所有涉及数据类型判断的工具路由都可能出错——"剪裁西陵区范围"只是冰山一角。同样的问题会发生在：

- 用户只有 polygon 数据但关键词触发了 density（需要 point）
- 用户只有 point 数据但关键词触发了 extract_feature（需要 polygon）  
- 用户混合数据但选择器无 context 无法按优先级排序

**5.241 修复方向有误**：把 '剪裁' 从「无映射→zonal」改为「剪裁→clip」，但正确方向应该是「剪裁→extract_feature」（或基于 context 动态裁决）。

**P0 三项修复（S1+S2+S3）可以在 <50 行代码内解决这个具体问题**，但更根本的架构改进（S10: context-aware 工具路由矩阵）需要更系统的设计。

---

*报告由 DeepSeek（ZCode 主线程）基于 6 并行 Agent 代码审查 + 手动逐函数 tracing 生成。*  
*Tracing 覆盖 7 个关键函数、3 层调用链、2 次 LLM 调用。*
