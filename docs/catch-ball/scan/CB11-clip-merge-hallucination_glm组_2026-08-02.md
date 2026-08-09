# CB-11「剪裁+合并」结论撒谎讨论（glm组 · ZCode + GLM 5.2 第三方独立评估）

> **评估方**：glm组（ZCode + GLM 5.2）·第三方独立评估  
> **日期**：2026-08-02 | **分支**：`fix/emc-buglog` @ `9f84eac`+  
> **对象**：[problem_report/CB11-clip-merge-hallucination-v2_2026-08-02](../problem_report/CB11-clip-merge-hallucination-v2_2026-08-02.md)  
> **方法**：逐函数读码追踪防线漏洞链（buildLanduseCompletion → inline 扩展 → _execSummary 注入 → finalStep → applyQualityDefense L1/L2/L3）  
> **聚焦**：「只说不做」在 B002/B004/B005 多轮修复后仍复发的结构性根因

---

## 〇、一句话结论

**「只说不做」复发的根因不是单点缺陷，而是防线的系统性盲区**：现有防线（L1 图层名对账 + R4 状态矛盾 + 零图层守卫）全部针对**产物层**（图层是否生成/存在），**没有任何一条防线针对「操作描述层**」（结论声称的操作是否真被执行）。LLM 编造的不是"生成了不存在的图层"（L1 能拦），而是"执行了没调用的工具"（L1 完全看不见）。这导致只要 finalStep LLM 对 toolHistory 做了语义推演——而非直接引用——防线就全部失明。

---

## 一、4 个问题逐条评估

### 问题 1：结论与执行不符（「只说不做」复发）— **agree（最严重·确证）**

**事实核实**：agree 问题报告。代码证据链完整：

1. `buildLanduseCompletion:1350` — `_wantUnion = /合并/.test(q)` → 问句含「合并」时 `_wantUnion=true`
2. `:1358-1361` — `_wantUnion` 为 true 时直接返回 `{mergeLayers: [...]}`，**跳过 overlay intersection（裁剪）分支**
3. `runTemplatePath:537-542` — inline 路径收到 `mergeLayers` → 调 `TOOLS.merge({layers: 全量用地})`，**没有 overlay/clip 裁剪步骤**
4. `:575-576` — `_execSummary` 只描述 `def.tool`（`extract_feature`），**不提 merge 实际做了什么**
5. finalStep LLM 看到 toolHistory 有 `extract_feature`（抽西陵区）+ `merge`（合全量），问句含「裁取」→ 推演「应该裁了」→ 写「执行裁取操作·严格落在西陵区边界内」

**这是确证的「只说不做」**：结论声称了「裁取」（一个没执行的操作），系统无防线检测。

### 问题 2：buildLanduseCompletion 丢裁剪语义 — **agree（执行层根因）**

**agree 且补充根因定位**：

`:1350` 的 `_wantUnion = /合并/.test(q)` 是一个**互斥分支**——问句含「合并」就走 union/merge，不含就走 intersection/裁剪。但用户的问句**同时含「裁剪」和「合并」**（"剪裁出…合并成一个图层"），`/合并/` 先命中 → 直接 merge 全量 → **裁剪语义被吞掉**。

这不是"等价路径没走完"（问题报告 §三.问题2 的措辞）——是**裁剪步骤根本没被规划**。`buildLanduseCompletion` 的分支逻辑设计上不支持"先裁剪再合并"这个组合操作。

**代码证据**：
```javascript
// harness.js:1350-1363
const _wantUnion = mode === 'union' || (mode === 'auto' && /合并/.test(q));
const _how = _wantUnion ? 'union' : 'intersection';  // ← 互斥：合并=union·裁剪=intersection
// ...
if (_wantUnion && _tcs.length >= 2) {
  return { mergeLayers: _matches.map(l => l.id) };  // ← 直接 merge·无裁剪
}
return { tcs: _tcs };  // ← 只有 !wantUnion 才走 intersection（裁剪）
```

### 问题 3：finalStep 无步骤描述谎报检测 — **agree（防线结构性洞·核心）**

**agree·这是"只说不做"复发的直接原因**。

现有 `applyQualityDefense` 的全部防线：

| 防线 | 检测什么 | 能否检测「裁取谎报」 |
|------|---------|:---:|
| **L1 `_verifyClaims`** | 结论声称的**图层名**是否在地图上 | ❌ 图层"merged_西陵区范围"确实存在 |
| **R1 非空** | 结论是否 >10 字符 | ❌ 结论很长 |
| **R2 图层按钮** | obsOK 时是否补 `{{show:}}` | ❌ 按钮存在 |
| **R3 参数一致** | 数值是否与 observation 一致 | ❌ 66.5 km² 确实是 merge 面积 |
| **R4 状态矛盾** | obsOK 不说"失败" / obsERR 不说"成功" | ❌ obs 是成功的（merge 成功了）|
| **R7 截断** | 结论是否 >800 字符 | ❌ 未超 |

**六条防线全部失明**——因为它们检测的都是**产物状态**（图层有没有/对不对），不是**操作语义**（结论声称的操作有没有被调用）。

LLM 编造的"裁取操作"是一个**不存在的动词**——它不在 `_extractClaimedLayers` 的正则捕获范围（`生成|产出|得到|裁出|裁剪|新建|构建|输出` + 图层后缀），即使被捕获了，"裁取"对应的图层（merged_西陵区范围）确实存在——L1 对账通过。

### 问题 4：observation 语义不足 — **agree（促成因素）**

**agree**。`tools.js:1144-1145` merge observation：
```
"合并 3 个图层后得到 N 个要素，总面积 66.5 平方公里，已生成图层「merged_西陵区范围」"
```

不含：
- 被合并的图层名列表（LLM 不知道合的是"商业/居住/公园"全量 vs "西陵区内的商业/居住/公园"）
- 是否已裁剪（LLM 不知道输入图层是全量还是已裁剪子集）
- `_source_layer` 标记虽然存在于 GeoJSON 属性中，但 observation 文本不暴露

finalStep LLM 只看到"合并了 3 个图层·总面积 66.5"——它**无法判断**这些图层是否已按西陵区裁剪。加上问句含"西陵区范围"+图层名含"西陵区范围"→ LLM 合理推演"应该裁了"→ 编造。

---

## 二、5 个分歧点推荐

### 分歧 1：问题 1 根因定位——结论层 / 执行层 / 叠加？

**推荐：叠加（执行层丢语义 + 结论层编造 + 防线层盲区·三者缺一不可）**

这不是单点故障，是**三重失效**：

```
执行层（问题 2）          结论层（问题 1）           防线层（问题 3）
buildLanduseCompletion     finalStep LLM              applyQualityDefense
丢裁剪语义                 推演编造                   操作描述盲区
    ↓                          ↓                          ↓
只 merge 全量            写"执行裁取操作"           L1/R4 全部失明
（没裁剪）               （没调 clip/overlay）       （不检测动词谎报）
```

- 如果执行层不丢语义（先裁剪再合并），finalStep 就有真实裁剪步骤可引用→不会编造
- 如果 finalStep 不编造（严格基于 toolHistory 描述），即使执行层丢了语义→结论也不会谎报
- 如果防线层能检测动词谎报，即使前两层都失效→结论会被标注/降级

**三者同时失效 = 「只说不做」复发**。修任何一层都能缓解，但只有修防线层（分歧 3）才能根治——因为执行层和结论层都依赖 LLM/正则的概率性行为，只有防线层是确定性代码。

### 分歧 2：「只说不做」为何多次修复后仍复发——防线结构性洞

**推荐：防线的根本盲区是「只检测产物·不检测操作」**

B002/B004/B005 修过的防线（全部针对产物层）：

| 修复 | 防什么 | 为何本次失效 |
|------|--------|------------|
| B002 诚实观测（P0-4 `_execSummary`） | LLM 不知道工具做了什么 | `_execSummary:575` 只说 `extract_feature 成功`——merge 步骤只在 toolHistory 文本里，LLM 对它做语义推演而非直接引用 |
| B004 零图层守卫 | 工具失败但声称成功 | 本次 merge **成功了**（图出了）→ 守卫不触发 |
| B005 执行摘要注入 | LLM 基于"计划已执行"推定 | 本次 toolHistory 有 extract+merge 两步·LLM 推演"应该还裁了" |

**结构性洞**：所有防线都在回答"**图层是否真实存在**"——没有一个防线在回答"**结论声称的操作是否真实执行**"。

```
现有防线问的问题：           缺失的防线问的问题：
"你说生成的图层在地图上吗？"  "你说执行了裁取·toolHistory 里有 clip/overlay 吗？"
→ L1 _verifyClaims           → （不存在）
→ R4 状态矛盾
→ 零图层守卫
```

**这就是为什么「只说不做」会反复复发**：每次修一个产物层的洞，LLM 就在操作描述层找新的编造空间。只要防线不覆盖"操作描述 vs 实际调用"这个维度，"只说不做"会以不同变体无限复发。

### 分歧 3：是否扩展 applyQualityDefense 加「步骤描述谎报检测」？

**推荐：是·这是根治「只说不做」的唯一确定性手段**

**可行性评估**：

| 维度 | 评估 |
|------|------|
| 技术可行 | ✅ `toolHistoryText` 已有全部工具调用记录·正则提取结论中的操作动词 + 对账 toolHistory 中的工具名 |
| 成本 | ✅ <5ms（正则匹配·与 L1 同量级） |
| 误报风险 | 🟡 中——LLM 可能合理地概括"extract+merge"为"裁取合并"（语义等价概括 vs 编造） |

**实现方案（推荐 R9 规则）**：

```javascript
// applyQualityDefense 新增 R9（步骤描述对账）
// 原理：结论声称的操作动词 → 对账 toolHistory 中是否有对应工具调用
function _verifyClaimedActions(draft, toolHistoryText) {
  // 1. 提取结论中的操作动词 + 宾语
  const _actionRe = /(?:执行了?|已完成|做了?|进行了?)\s*(裁取|裁剪|裁出|剪裁|叠置|叠加|缓冲|筛选|抽取|合并)/g;
  const claimed = new Set();
  let m;
  while ((m = _actionRe.exec(draft)) !== null) claimed.add(m[1]);
  // 2. 工具→动词映射
  const _ACTION_TO_TOOL = {
    '裁取': ['clip', 'overlay'], '裁剪': ['clip', 'overlay'], '裁出': ['clip', 'overlay', 'extract_feature'],
    '剪裁': ['clip', 'overlay', 'extract_feature'],
    '叠置': ['overlay'], '叠加': ['overlay'], '缓冲': ['buffer'],
    '筛选': ['filter_attr'], '抽取': ['extract_feature'],
    // '合并' 不查——merge 本身就是合并动词·observation 会提到
  };
  // 3. 对账：声称的操作 → toolHistory 中是否有对应工具
  const _unverified = [];
  for (const action of claimed) {
    const tools = _ACTION_TO_TOOL[action] || [];
    if (tools.length && !tools.some(t => new RegExp(`动作: ${t}\\(|步骤.*${t}\\(`).test(toolHistoryText))) {
      _unverified.push(action);
    }
  }
  return _unverified;
}
```

**R9 动作**：检测到未验证的操作描述 → inline 标注「（注：实际未执行此操作·请以上方工具记录为准）」+ fixes 记录。

**误报缓解**：只检测"强措辞"（执行了/已完成/做了 + 操作动词），不检测弱引用（"包含""涉及"等）。LLM 说"合并了 3 个图层"不触发（merge observation 有），说"执行了裁取操作"但 toolHistory 无 clip/overlay → 触发。

**这是填补结构性洞的唯一确定性手段**——正则覆盖面有限（新动词需补映射），但比 LLM 审查可靠（零假阴性边界可控）。

### 分歧 4：buildLanduseCompletion 含「裁剪+合并」时——先裁剪再合并 vs 合并全量→再裁剪？

**推荐：先裁剪再合并（overlay intersection × N → merge concat）**

理由：

| 方案 | 执行 | 结论如实性 | 复杂度 |
|------|------|:---:|:---:|
| **A 先裁剪再合并** | extract(西陵区) → overlay(西陵区,商业)∩ + overlay(西陵区,居住)∩ + overlay(西陵区,公园)∩ → merge(3 个裁剪产物) | ✅ toolHistory 有 N 个 overlay intersection → LLM 能如实描述裁剪 | 高（N+1 步） |
| B 合并全量→再裁剪 | merge(全量 3 类) → overlay(merge结果, 西陵区)∩ | ✅ toolHistory 有 merge + overlay → LLM 能如实描述 | 中（2 步） |
| C 当前（只合并不裁剪） | extract(西陵区) → merge(全量 3 类) | ❌ 无裁剪步骤 → LLM 编造 | 低（2 步） |

**推荐 A 而非 B 的原因**：
- A 的每一步 overlay intersection 产出一个"西陵区内某类用地"图层——toolHistory 明确、可审计
- B 的 merge 全量先产一个大图层，再裁剪——中间产物的面积（66.5 km² 全量）会出现在 observation 中，LLM 可能仍引用它
- A 的 toolHistory 模式与"区内多类用地"overlay 链一致（已有 `intersection` 分支），改动最小

**实现**（`buildLanduseCompletion` 分支逻辑修改）：

```javascript
// 当前 :1350 互斥分支 → 改为组合
const _wantMerge = /合并/.test(q);
const _wantClip = /(裁剪|裁取|裁出|剪裁|范围内|内的)/.test(q);

if (_wantMerge && _wantClip) {
  // 先裁剪（intersection × N）再合并（merge concat）——返回两阶段 tcs
  const _clipTcs = _matches.map((l) => ({
    name: 'overlay',
    params: { layer_a: _bRef, layer_b: l.id, how: 'intersection', as: l.name + '_' + _boundaryName + '_裁剪' }
  }));
  // merge 步骤引用裁剪产物
  return { 
    twoPhase: { clipTcs: _clipTcs, mergeLayers: _clipTcs.map(t => t.params.as) },
    boundaryName: _boundaryName, mentioned: _mentioned 
  };
}
if (_wantMerge) {
  return { mergeLayers: _matches.map(l => l.id), ... };  // 纯合并（无裁剪语义）
}
return { tcs: _tcs, ... };  // 纯裁剪（intersection）
```

### 分歧 5：4 问题修复优先级

**推荐优先级**：

| 优先级 | 问题 | 修复 | 理由 |
|:---:|------|------|------|
| **P0** | 问题 3 | applyQualityDefense 加 R9（步骤描述对账） | **根治「只说不做」的确定性手段**——即使执行层/结论层都失效，R9 能拦住。用户最关注的是结论可信度。 |
| **P0** | 问题 2 | buildLanduseCompletion 支持两阶段（裁剪+合并） | 消除执行层语义丢失——让 toolHistory 有真实的裁剪步骤，finalStep 能如实引用 |
| **P1** | 问题 4 | merge observation 加图层名 + 来源标注 | 降低 finalStep 推演空间——让 LLM 知道合的是"全量"还是"已裁剪" |
| **P1** | 问题 1 | 由 P0（R9 + 两阶段）自动解决 | 问题 1 是问题 2+3 的表现——修了根因，表现自消 |

**P0 两件必须同时做**：只修 R9 不修两阶段 → R9 会频繁标注"裁取未执行"（因为执行层确实没裁）→ 用户体验差（每次都看到标注）。只修两阶段不修 R9 → 下次 LLM 换个编造变体（如"进行了空间约束"）→ R9 缺失仍复发。

---

## 三、防线的结构性洞——总结图

```
当前防线架构（全部针对产物层）：
┌─────────────────────────────────────────────────────────┐
│  L1 _verifyClaims    → 图层名对账（声称的图层在地图上吗） │
│  R1 非空             → 结论 >10 字符                      │
│  R2 图层按钮         → obsOK 时补 {{show:}}              │
│  R3 参数一致         → 数值与 observation 一致            │
│  R4 状态矛盾         → obsOK 不说"失败"                   │
│  R7 截断             → 结论 <800 字符                     │
│  零图层守卫          → newLayerCount=0 时不声称成功       │
└─────────────────────────────────────────────────────────┘
                    ↑
          全部回答："图层是否真实存在？"
          没人回答："操作是否真实执行？"  ← 结构性洞

缺失的防线：
┌─────────────────────────────────────────────────────────┐
│  R9 步骤描述对账（新）→ 结论声称的操作在 toolHistory 吗   │
└─────────────────────────────────────────────────────────┘
```

**「只说不做」复发的充分条件**：
1. 执行层有一步 LLM 能"推演"的操作（问题 2 丢语义）
2. 结论层 LLM 做了语义推演而非直接引用（问题 1 编造）
3. 防线层不检测操作描述（问题 3 盲区）

三者同时成立 = 必然复发。**只有堵住 #3（R9）才能给出确定性保证**——#1 和 #2 依赖 LLM 行为（概率性），无法根治。

---

## 四、一句话总结

**「只说不做」复发的根因是防线的系统性盲区：六条防线全部检测"图层是否存在"，没有一条检测"操作是否执行"。LLM 只要在操作描述层编造（而非图层名层），防线就全部失明。根治 = applyQualityDefense 加 R9（步骤描述对账·确定性正则·<5ms）+ buildLanduseCompletion 支持两阶段（先裁剪再合并·让 toolHistory 有真实裁剪步骤）。P0 两件必须同时做——只修其一「只说不做」会以新变体复发。**

---

*glm组（ZCode + GLM 5.2）· CB-11「剪裁+合并」结论撒谎讨论 · 2026-08-02*  
*证据基于逐函数读码（buildLanduseCompletion / runTemplatePath inline / applyQualityDefense L1-R7 / tools.js merge observation）+ 防线覆盖矩阵分析。*
