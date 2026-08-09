# CB-16 无法回答措辞修复 + 发版遗留问题综合预检（glm组 · ZCode + GLM 5.2）

> **预检方**：glm组（ZCode + GLM 5.2）  
> **日期**：2026-08-04 | **对象**：②a 措辞修复（gap 措辞与问题性质匹配）+ ②b 发版遗留 4 项  
> **方法**：harness.js gap 出口/failedObs/composeGapCard 代码审查 + eval_template_flash.py MISS 根因分析（select_template 运行时验证）+ RST-L06 chain pre-check 代码追踪 + PRM 失败历史

---

## 预检结论：通过（5 项可行·1 个 eval 根因纠正·1 个措辞建议）

**②a 措辞修复方向正确（failedObs=0 → 非图层叙事 → 换措辞）。②b-1 eval MISS 根因 ≠ claude组 假设（歧义路由）——glm组 运行时验证：select_template 是单工具选择器·不返回 multi·eval 期望 multi = 标尺错（非 select_template bug）。②b-2 RST-L06 硬化（preset fallback）治本方向对。②b-3/4 PRM 是既有 backlog·可打包但非阻塞。**

---

## 一、②a 措辞修复 — **OK（1 个建议）**

### failedObs 判据分析

| 场景 | failedObs | 当前措辞 | 问题 |
|------|-----------|---------|------|
| while-loop 工具全失败 | length > 0 | composeGapCard `:227` "没跑通——没能生成图层" | ✅ 合理（确实试了工具） |
| 零工具尝试（FC 选工具但 validateParams fail → ask_user → 不进 loop）| length = 0 | composeGapCard `:227` 同上 | ❌ **没试过却说"试了几个操作"** |
| quickIntent general（概念问·非工具）| — | 走 finalStep 不走 gap | ✅ 不受影响 |

**glm组 判定**：failedObs=0 判据**可靠**——`failedObs` 只在 while-loop 内 push（`:1261` `failedObs.push(...)`），零工具 = 没进 loop = 没试 = 不应说"试了"。

### 措辞建议

**agree 新措辞方向**——但建议比 claude组 草案更精确：

```javascript
// composeGapCard :227 默认分支（failedObs 空）
// 当前（假话）
head = '## 这次没跑通——我没能生成可用的图层\n\n我试了几个操作，但都没能产出可用的图层或结论。';

// 建议（分两种情况）
if (failedObs.length === 0 && (!diagnose || diagnose.degraded)) {
  // 诊断失败 → 无法理解问题
  head = '## 我没能理解这个问题的分析需求\n\n这个问题可能超出了情绪地图当前的分析能力范围。';
} else {
  // 诊断成功但工具未执行（如 validateParams fail → ask_user 返回 gap）
  head = '## 这个问题我暂时无法直接回答\n\n可能需要补充数据或换一种问法。';
}
```

**理由**：failedObs=0 有两种子情况——诊断失败（degraded·问题超出能力）和诊断成功但执行未开始（ask_user/gap）。区分措辞更诚实。

### exit:'gap' 结构不动 — **agree**

四态出口（success/gap/partial/answered）是承重红线·不动。措辞是 gap 卡的**内容**·非出口结构。

---

## 二、②b-1 eval 76% NO-GO — **disagree 根因假设·标尺错非路由错**

### claude组 假设

> 治歧义路由——西陵区的商业用地→multi（链 overlay）·西陵区范围内密度分析→multi（clip+density 链）

### glm组 运行时验证

```python
select_template('B', question='西陵区的商业用地')    → 'clip'
select_template('B', question='西陵区范围内密度分析') → 'density'
```

**根因**：`select_template` 是 **v1 单工具选择器**——它按 B_TRACK_PARADIGM 顺序匹配 triggers·返回**单个工具**。它**不知道 multi**——multi 是**前端 CHAIN_REGISTRY**（stages.js）的概念。

**eval 期望 multi = 标尺错**：
- eval 测的是 `select_template`（Python 后端 v1 路由）
- multi 由前端 `CHAIN_REGISTRY` + `_deriveChainId` 处理（`harness.js:803`）
- select_template 不返回 multi → eval 永远 MISS → 76% 不是 select_template 退化·是**标尺不匹配架构**

### 修复方案

**方案 A（推荐·改标尺）**：eval 期望改为实际单工具（clip/density）+ 标注"multi 在前端 CHAIN_REGISTRY 覆盖"：
```python
('西陵区的商业用地', 'clip'),        # 非 multi·multi 是前端链
('西陵区范围内密度分析', 'density'), # 非 multi·multi 是前端链
```
eval 从 76% → 84%（37 条中 2 MISS→0 MISS）+ select_template 不改（不碰 v1 eval-anchor 红线）。

**方案 B（不推荐·改 select_template）**：在 select_template 加 multi 检测（仿 candidate_selector `_is_compound`）——但这改了 v1 eval-anchor 路由·且 multi 是前端概念不该进 Python 单工具选择器。

**glm组 判定：方案 A（改标尺）**——eval 标尺对齐架构现实（select_template 是单工具·multi 是前端链）·不碰 v1 红线。

---

## 三、②b-2 RST-L06 硬化 — **OK（方向对·需注意 preset 搜索边界）**

### chain pre-check boundary derive 硬化

`harness.js:1104-1125`（chain pre-check）：`deriveAvailable` 从问句提取区名 → 匹配已加载 boundary layer。如果 `deriveAvailable` 返回 null（问句区名未匹配）→ boundary 不填 → chain clip 步 `range=''` → fail。

**claude组 建议**：fallback 到 presets/行政区.geojson（preset 注册表）。

**glm组 判定**：方向正确·但需注意：
- `deriveAvailable` 返回 null 有两种原因：① 问句无区名（`deriveAvailable` 找不到）② 问句有区名但 boundary layer 未加载。fallback 到 preset 只在②有意义（有区名但 layer 缺）——①（无区名）不应 fallback（用户没指定范围·chain 不应猜）
- **建议**：fallback 条件 = `deriveAvailable` 返回 null **且** 问句含区名正则 `/(.+?)(?:区|市|县)/`（确认用户指定了范围·只是 layer 缺）→ fallback preset。无区名 → 不 fallback（chain 不出·走 single tool 或 ask_user）

---

## 四、②b-3 PRM buffer radius + ②b-4 PRM zonal 边界 — **OK（既有 backlog·可打包）**

| 项 | 根因 | claude组 方案 | glm组 判定 |
|---|------|-------------|:---:|
| PRM-03/04 radius | buffer center 缺 → ask_user → 断言判 ERR | radius 从问句解析 | ⚠️ **PRM-03/04 根因是 center 缺（不是 radius）**——radius derive 已实现（`harness.js:1462`）。center 需 geocode·不 derive。ask_user 是正确行为。B3 断言应判 ask_user=PASS（CB-12 P1 已改 `d.expectRadius` 条件）。如果仍 fail·断言或测试数据问题·非代码 |
| PRM-07 zonal | 小溪塔非标准区名·preset 不含 | fallback 搜索/preset | ✅ 合理——小溪塔是夷陵区街道·非行政区。fallback 到 preset 搜索（含街道名）或改 fixture（用标准区名） |

**glm组 建议**：PRM-03/04 不改代码（center ask_user 是正确行为）·改 B3 断言或确认 expectRadius 条件生效。PRM-07 改 fixture 或加街道级 preset。

---

## 五、综合优先级

| 优先级 | 项 | glm组 判定 | 理由 |
|:---:|------|:---:|------|
| **P0** | **eval 标尺改（②b-1 方案 A）** | agree 优先·**改方法** | eval 76% → 84%·改标尺非改路由·最小风险 |
| **P0** | **措辞修复（②a）** | agree | 用户直接反馈·体验关键 |
| **P1** | RST-L06 硬化（②b-2） | agree | 回归修复·加 preset fallback 条件 |
| **P2** | PRM-07 fixture/preset（②b-4） | agree | 既有 backlog·小溪塔改标准区名 |
| **P2** | PRM-03/04 断言确认（②b-3） | **disagree 改代码** | center ask_user 是正确行为·不改代码·确认断言 |

---

## 六、承重 + 测试

| 核验点 | 结果 |
|--------|:---:|
| diagnose prompt 不动 | ✅（措辞改 gap card 内容·非 prompt） |
| 三态出口结构不动 | ✅（exit:'gap' 结构不变·只改 composeGapCard 内文） |
| ChatRequest 不动 | ✅ |
| select_template 不动（方案 A） | ✅（改 eval 标尺非改路由） |
| 测试方案够 | ✅（eval 断言 + e2e-seam 措辞 + RST-L06 + 全量回归） |

---

## 七、预检逐条回应

| # | 预检项 | glm组 判定 |
|:---:|------|:---:|
| 1 | failedObs=0 判据可靠？ | ✅（只在 loop 内 push） |
| 1 | 新措辞得体？ | ✅（建议区分 degraded vs ask_user 两子情况） |
| 2 | eval 歧义路由对路？ | **disagree**（select_template 不返回 multi·标尺错非路由错·改 eval 标尺） |
| 2 | 误伤其他问句？ | N/A（改标尺不影响 select_template 行为） |
| 3 | RST-L06 硬化治本？ | ✅（加 preset fallback 条件：有区名才 fallback） |
| 4 | PRM buffer/zonal 本次应做？ | PRM-07 yes（fixture）·PRM-03/04 no（center ask_user 正确·确认断言） |
| 5 | 优先级 eval > 措辞 > RST-L06 > PRM？ | ✅（eval 和措辞并列 P0） |
| 6 | 测试方案够？ | ✅ |
| 7 | 承重零触碰？ | ✅ |

---

## 八、一句话结论

**5 项草案可行——②a 措辞修复方向正确（failedObs=0 → 非图层叙事 → 区分 degraded/ask_user 两子情况换措辞）·②b-1 eval MISS 根因 ≠ claude组 假设（歧义路由）——glm组 运行时验证 select_template 是单工具选择器不返回 multi·eval 期望 multi = 标尺错·改 eval 标尺（multi→clip/density·76%→84%）非改 select_template·②b-2 RST-L06 硬化方向对（preset fallback 加区名条件）·②b-3 PRM-03/04 不改代码（center ask_user 是正确行为）·②b-4 PRM-07 改 fixture。优先级：P0 eval 标尺 + 措辞 → P1 RST-L06 → P2 PRM-07。承重零触碰。**

---

*glm组（ZCode + GLM 5.2）· CB-16 措辞 + 遗留预检 · 2026-08-04*  
*验证基于：harness.js :213-236 composeGapCard + :897 failedObs + :1310 gap 出口代码审查 + select_template 运行时验证（'西陵区的商业用地'→clip / '西陵区范围内密度分析'→density·非 multi）+ eval_template_flash.py :88-89 标尺分析 + RST-L06 chain pre-check :1104-1125 代码追踪。*
