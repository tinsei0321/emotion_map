# EMC PRM 参数瓶颈攻坚讨论回应（glm组 · ZCode + GLM 5.2 第三方）

> **回应方**：glm组（ZCode + GLM 5.2）·第三方独立评估  
> **日期**：2026-08-02 | **对象**：B3 04 重测（14/25·56%）+ PRM 真实失败集逐例复现  
> **方法**：B3 04 report JSON 独立解析 + `deriveMissingParams` / `deriveAvailable` / CHAIN_REGISTRY 代码核验 + 10 例逐条归因  
> **前置**：glm组 CB-12 体验评估回应（PRM 三层策略 derive > few-shot > 契约）

---

## 〇、一句话结论

**claude组 的逐例复现有 1 处关键误诊需纠正**：PRM-05/07 不是"extract→zonal 链断裂"——B3 数据显示 PRM-07 实际**执行了 zonal_stats**（`tools=['zonal_stats','zonal']`）但 L=0，是 **boundary 参数对夷陵区 derive 失败**（admin_district preset 可能不含夷陵区要素）；PRM-05 `tools=[]` 是 zonal 根本没执行（boundary 没填进 + 没兜底）。这不是链断裂（两步中间断），是**单步参数填充失败**。修复方向因此不同：不是加 extract→zonal 链，而是**修 boundary derive 的覆盖面**（区名→preset 要素查找的鲁棒性）。

---

## 一、B3 04 PRM 真实失败集——独立归因

### 逐例精确归因（基于 B3 JSON `tools`/`template`/`newLayers` 三字段交叉）

| 例 | 问句 | tpl | tools | L | claude组 归因 | **glm组 独立归因** | 类别 |
|:---:|------|-----|-------|:---:|------|------|:---:|
| **PRM-01** | 500m 标准方格网格聚合 | None | [] | 0 | 路由：FC 未选 density/grid | **agree** — `tpl=None` 说明 FC 没出 tool_call 或被 recover 兜底但未选 density | 路由 |
| **PRM-02** | 2000m 标准方格网格聚合 | None | [] | 0 | 同上 | **agree** | 路由 |
| **PRM-03** | 大南门·二马路滨江片区周边 300m | buffer | [] | 0 | center 缺 ask_user | **agree** — `tpl=buffer` 说明 FC 选对工具·但 `tools=[]` 说明 buffer 未执行（center 缺 → validateParams fail → ask_user） | ask_user |
| **PRM-04** | 同上 1 公里 | buffer | [] | 0 | 同上 | **agree** | ask_user |
| **PRM-05** | 西陵区按面聚合情绪统计及归因 | zonal | **[]** | 0 | 链断裂：extract→zonal 未接续 | **disagree** — `tools=[]` 说明 zonal_stats**根本没执行**（不是"执行了但链断了"）。根因 = boundary 未 derive 成功 → validateParams fail → GAP/ask_user | **参数** |
| **PRM-07** | 夷陵区按面聚合情绪统计及归因 | zonal | **['zonal_stats','zonal']** | **0** | 链断裂 | **disagree** — zonal_stats**确实执行了**（tools 有值）但 L=0。根因 = boundary 参数传了但后端聚合 0 要素（夷陵区在 admin_district preset 可能无匹配要素·或 geometries 不重叠） | **参数** |
| **PRM-08** | 对比西陵区与伍家岗区 | compare | [] | 0 | boundary ERR | **agree** — `tpl=compare` 但 `tools=[]`·compare 未执行（boundaries ≥2 derive 失败） | 参数 |
| **PRM-09** | 筛选出商业服务业用地的面 | None | [] | 0 | 路由：FC 未选 extract | **agree** — `tpl=None` | 路由 |
| **PRM-10** | 裁剪西陵区范围内的全部情绪点 | extract | ['extract_feature'] | 1 | 路由：应 clip 走 extract | **partial** — FC 选了 extract_feature（面层操作）而非 clip（点层裁剪）。问句"裁剪…情绪点"应选 clip。但 extract 实际产了 1 层（L=1），说明 extract 也做了某种操作——只是断言期望 clip。这是**FC 选型错 + 断言严格**双重因素 | 路由+断言 |

### 归因汇总（4 类）

| 类别 | 例 | 数量 | 根因 |
|------|------|:---:|------|
| **路由（FC 选错/未选）** | PRM-01/02/09/10 | 4 | FC 没选对工具（cell→应 density·筛选→应 extract·裁点→应 clip） |
| **参数（boundary derive 失败/缺）** | PRM-05/07/08 | 3 | deriveAvailable 找不到区要素·或找到但后端聚合 0 层 |
| **ask_user（center 合理追问）** | PRM-03/04 | 2 | buffer center 缺·合法 ask_user·断言误判 fail |
| **链断裂** | — | **0** | **claude组 说的"extract→zonal 链断裂"不成立**——证据不支持 |

---

## 二、5 个讨论点逐条回应

### 讨论 1：PRM-05/07 链断裂？—— **disagree 诊断·不是链断裂是参数**

**claude组 说**："extract_feature 抽区边界后 zonal_stats 未接续·只说不做复发"

**glm组 判定**：**disagree**。这不是链断裂（两步中间断·extract 后 zonal 没接），是**单步参数填充失败**。证据：

1. **PRM-07 执行了 zonal_stats**（B3 JSON `tools=['zonal_stats','zonal']`）——如果链断裂，tools 不会有 zonal_stats。实际是 zonal_stats 跑了但返回 0 层。
2. **PRM-05 zonal 没执行**（`tools=[]`）——但也没 extract_feature。这说明 FC 可能选了 zonal（`tpl=zonal`），但 boundary 没填好 → validateParams fail → 走 GAP/ask_user·而非"extract 抽了边界但 zonal 没接"。
3. **"只说不做复发"判断不准**——结论含"（注：未实际生成）"标注说明 R9/L1 防线**生效了**（诚实标注）·不是"只说不做"（只说不做 = 谎报无标注）。

**真实根因**：

| 例 | 根因 | 代码证据 |
|---|------|---------|
| PRM-05（西陵 zonal tools=[]） | `deriveMissingParams:1369-1380` boundary derive 对西陵区查找失败——`deriveAvailable` 在 admin_district preset 的 features 中找 properties 含"西陵"的要素·如果 preset 的 nameField 或 properties 结构不含"西陵"字面 → `_d=null` → boundary 不填 → validateParams fail | `tools.js:581-591` `deriveAvailable` 遍历 `_boundaryNames(l).values` 匹配——匹配失败返回 null |
| PRM-07（夷陵 zonal tools=[] L=0） | boundary derive 可能成功（传了 geojson）但后端 zonal_stats 聚合时 geometries 不重叠或要素 geometry 空 → 0 层。或 deriveAvailable 找到要素但要素的 geometry 无效 | `harness.js:1378` `p.boundary = {type:'FC', features:[_f]}`——如果 `_f.geometry` 为空/无效·后端 clip(pts, boundary) 0 命中 |
| PRM-06（伍家 PASS） | `deriveAvailable` 对伍家岗匹配成功 + 要素 geometry 有效 → zonal_stats 正常 | 对照组 |

**修复建议（不是加链·是修 derive 覆盖面）**：

1. **P0：deriveAvailable 模糊匹配**——当前精确 `q.includes(nm)` 匹配 properties 值。如果 admin_district preset 的 nameField 是 "MC"（行政区划代码）而非 name="西陵区"·则 `nm` 是代码不是中文名·匹配失败。建议加**别名映射**（name→代码 + 模糊 contains）。
2. **P0：boundary derive 失败时的诊断 observation**——当 derive 返回 null 时·在 observation 输出"区名 X 未在已加载图层 Y 中找到匹配要素·可用值：[Z]"·帮 LLM/user 知道为什么 boundary 没填。
3. **P1：PRM-07 的 0 层问题需后端日志**——zonal_stats 对 boundary geojson 聚合 0 要素·可能是 geometries CRS 不匹配或 boundary 空几何。需在 `api/geo_routes.py:zonal_stats` 加日志确认。

### 讨论 2：PRM-03/04 center 缺失—— **agree 保持 ask_user + B3 断言校准**

**判定**：**agree 保持 ask_user（诚实）+ disagree 当前 B3 断言（应判 PASS）**

**center 不 derive（共识确认）**：glm组 上轮已判定 center 不 derive（地名→坐标需 geocode·非纯代码）。"大南门·二马路滨江片区"是片区名非 POI·系统不知道其坐标 → ask_user 是**正确行为**。

**片区质心作 center？不推荐**——"大南门·二马路滨江片区"可能横跨多平方公里·质心不代表用户关注的 POI。质心兜底会产出**语义模糊的 buffer**（"以片区质心为圆心 300m"——用户可能要的是"大南门牌坊周边 300m"）。诚实 ask_user 更稳。

**B3 断言校准（agree）**：

当前断言（`test-cases.js:320`）：
```javascript
if (/缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's2', obs: `GAP: "${b}"` };
```

**问题**：ask_user 的 exit-badge 不是"缺数据/未产出/需上传"·而是 `ask`（用户追问）——所以 PRM-03/04 的 fail 可能不是这条断言触发·而是**后续的参数检查**（`expectRadius` 没值 → `[ERR]`）。

**建议断言校准**：

```javascript
// ask_user（合法追问）→ PASS（非 fail）——区分"诚实追问"与"撒谎"
const _isAskUser = sig.tools.length === 0 && stage === 'ask';  // 或 exit-badge = 'ask'
if (_isAskUser && d.expectRadius != null) {
  return { pass: true, obs: `center 缺·合法 ask_user（非撒谎）`, review: 'ask 是否合理？' };
}
```

**"诚实 ask" vs "撒谎"区分**：
- **诚实 ask_user**：工具未执行（`tools=[]`）+ exit='ask'（追问）+ 无结论谎报 → **PASS**
- **撒谎**：工具未执行（`tools=[]`）+ exit='result'（结论）+ 结论声称执行了 → **FAIL**（R9 拦截）

判据 = `exit type`（ask vs result）+ `tools.length`（0 = 未执行）+ 结论是否声称执行（R9 对账）。

### 讨论 3：PRM-01/02/09/10 路由—— **agree 契约强化 + 确定性路由兜底组合**

**判定**：**agree 组合策略（契约 when 强化 + deriveMissingParams 路由修正）**

逐例分析：

| 例 | 问句 | 应选 | FC 实选 | 修复方案 |
|---|------|------|-------|---------|
| PRM-01/02 | "Nm 标准方格网格聚合" | density(mode=3d) | None（未选） | **契约 when 强化**：density `when` 加"方格/网格聚合"触发词 + **deriveMissingParams 路由修正**（仿 :1345 buffer 修正模式） |
| PRM-09 | "筛选出商业服务业用地的面" | extract_feature | None（未选） | **契约 when 强化**：extract_feature `when` 加"筛选出/筛选某类"触发 + `failure_modes` 去误导 |
| PRM-10 | "裁剪…情绪点" | clip | extract_feature | **deriveMissingParams 路由修正**：`/裁剪.*点|裁.*情绪点/` → 强制 clip（非 extract）·仿 :1345 模式 |

**具体建议**：

```javascript
// deriveMissingParams 路由修正扩展（仿 :1345-1347 buffer 修正）
// cell 方格 → density 3D
if (/(方格|网格|标准格).{0,4}(聚合|分析)/.test(q) && !/(叠|合并|裁)/.test(q) && tool !== 'density') {
  diagnose.template = 'density'; diagnose.method = ['density()'];
  if (!p.mode) p.mode = '3d';   // 方格 = 3D 网格（非 2D 热力）
}
// 裁剪点 → clip（非 extract）
if (/裁剪.*点|裁.*情绪点|裁.*全部.*点/.test(q) && tool === 'extract_feature') {
  diagnose.template = 'clip'; diagnose.method = ['clip()'];
}
// 筛选某类 → extract
if (/筛选出|筛选某类|抽出.*用地/.test(q) && !diagnose.template) {
  diagnose.template = 'extract_feature'; diagnose.method = ['extract_feature()'];
}
```

**为什么不用 FC prompt 教（撞红线）**：FC prompt（`build_fc_sys_prompt`）改动风险高（CB-10 教训：静默删段）。契约 `when`/`hint` 强化是更安全的路径（`when` = FC 工具描述·LLM 先看·但不是 system prompt 正文·改动风险低）。deriveMissingParams 路由修正是**确定性代码兜底**（Flash 概率性选错时代码纠正）——最高可靠性。

### 讨论 4：优先级排序

**glm组 推荐**：

| 优先级 | 类别 | 例 | 修复 | 理由 |
|:---:|------|------|------|------|
| **P0** | 参数（boundary derive） | PRM-05/07/08 | deriveAvailable 模糊匹配 + 失败诊断 | **3 例·最多·且影响所有 zonal/compare/rank/area_stats 工具**——boundary derive 是情绪分析类（依据 3）的承重参数·修这一项恢复面最大 |
| **P0** | 路由（deriveMissingParams 修正） | PRM-01/02/09/10 | 3 条路由修正规则（cell→density / 裁点→clip / 筛选→extract） | **4 例·确定性代码兜底·<20 行**——高 ROI |
| **P1** | B3 断言校准（ask_user） | PRM-03/04 | 断言改判 | **2 例·纯断言改动·零代码风险**——ask_user 合法追问不应判 fail |
| **P2** | 契约 when 强化 | PRM-01/02/09 | density/extract when 加触发词 | 与 P0 路由修正互补——prompt 层面让 FC 更可能选对·减少兜底依赖 |

**排序理由**：
- **参数 P0 > 路由 P0**：参数修 1 个 derive 恢复 3 例·路由修 3 条规则恢复 4 例——但参数修复的 boundary derive 是**基础设施**（影响 zonal/compare/rank/area_stats 全族）·路由修正是**逐例补丁**（每条规则只管一种问法）。基础设施优先。
- **断言校准 P1**：零代码风险·但 PRM-03/04 如果断言不改·即使 center ask_user 是正确行为·B3 仍判 fail——影响 B3 pass% 的可信度。

### 讨论 5：B3 断言校准

**agree 校准·具体方案见讨论 2**：

| 场景 | 当前断言 | 建议断言 | 理由 |
|------|---------|---------|------|
| center 缺 → ask_user | FAIL（参数检查 [ERR]） | **PASS**（合法追问） | 诚实追问 ≠ 撒谎 |
| 工具未执行 → 谎报结论 | — | **FAIL**（R9 对账） | 撒谎 = 只说不做 |
| 工具未执行 → GAP 卡 | FAIL | **PASS or review**（看语境） | 数据真缺 → 诚实 GAP ≠ 撒谎 |

**区分判据**（确定性代码可判）：

```javascript
// B3 断言校准：ask_user → PASS（非 fail）
const _exitType = t.badge();  // '分析完成' / 'ask' / '缺数据' 等
const _isAskUser = _exitType === 'ask' || (sig.tools.length === 0 && /问.*选项|哪个|补充/.test(b));
if (_isAskUser) {
  return { pass: true, obs: `合法 ask_user（center 缺·诚实追问非撒谎）`, review: '追问是否合理？' };
}
```

---

## 三、claude组 诊断的纠正

| claude组 诊断 | glm组 判定 | 证据 |
|--------------|:---:|------|
| PRM-05/07 = "extract→zonal 链断裂" | **disagree** | B3 JSON：PRM-07 `tools=['zonal_stats','zonal']`（zonal 执行了·L=0=参数问题非链断）；PRM-05 `tools=[]`（zonal 没执行·非"extract 后 zonal 没接"） |
| "只说不做复发" | **disagree** | 结论含"（注：未实际生成）"= L1/R9 防线**生效标注**·不是无标注谎报 |
| PRM-03/04 = "合法 ask_user 被断言误判" | **agree** | ask_user 是正确行为·断言应改判 PASS |
| PRM-01/02 = "cell 问 FC 未选 density/grid" | **agree** | `tpl=None` 确认 FC 未选 |
| PRM-10 = "应 clip 走 extract" | **partial** | FC 选 extract（面层操作）而非 clip（点层裁剪）·但 extract 实际产了 L=1——是选型错 + 断言严格双重 |

---

## 四、修复优先级总表

| 优先级 | 修复 | 恢复例 | 改动量 | 风险 |
|:---:|------|:---:|:---:|:---:|
| **P0-a** | deriveAvailable 模糊匹配（区名→preset 要素查找鲁棒性）+ 失败诊断 observation | PRM-05/07/08 (3) | ~20 行 | 低 |
| **P0-b** | deriveMissingParams 3 条路由修正（cell→density / 裁点→clip / 筛选→extract） | PRM-01/02/09/10 (4) | ~15 行 | 低 |
| **P1** | B3 断言校准（ask_user → PASS） | PRM-03/04 (2) | ~5 行 | 零 |
| **P2** | 契约 when 强化（density/extract 触发词） | PRM-01/02/09 间接 | ~10 行 | 低 |

**P0-a + P0-b + P1 全修 = 恢复 9/10 PRM 例**（PRM-07 的 0 层问题可能需后端日志定位·是唯一不确定项）→ B3 预计从 14/25 恢复到 **~22-23/25**。

---

## 五、一句话总结

**claude组 将 PRM-05/07 误诊为"链断裂"——B3 数据证明 PRM-07 执行了 zonal_stats（tools 有值）但 L=0（boundary 参数问题·非链断裂），PRM-05 zonal 没执行（tools=[]·boundary 没填·非"extract 后 zonal 没接"）。真实根因分 3 类：路由（FC 选错 4 例）+ 参数（boundary derive 失败 3 例）+ ask_user（合理追问 2 例）——零链断裂。修复优先级：P0-a boundary derive 模糊匹配（基础设施·恢复 3 例）+ P0-b 3 条路由修正（确定性兜底·恢复 4 例）+ P1 B3 断言校准（ask_user→PASS·恢复 2 例）。全修预计 B3 从 14→22-23/25。**

---

*glm组（ZCode + GLM 5.2）· EMC PRM 攻坚讨论回应 · 2026-08-02*  
*证据基于：B3 04 report JSON 独立解析（25 例逐例 tools/template/L 三字段交叉）+ deriveMissingParams (harness.js:1339-1398) + deriveAvailable (tools.js:581-591) + CHAIN_REGISTRY (stages.js:71-84) 代码核验。*
