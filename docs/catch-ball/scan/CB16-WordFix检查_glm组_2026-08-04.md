# CB-16 措辞修复 + 发版遗留问题实施后检查（glm组 · ZCode + GLM 5.2）

> **验证方**：glm组（ZCode + GLM 5.2）  
> **日期**：2026-08-04 | **对象**：c53aa99（②a 措辞 + ②b-1 eval 标尺 + ②b-2 RST-L06 硬化 + ②b-3 buffer 门控）  
> **方法**：harness.js composeGapCard/gap 出口/chain pre-check/buffer 门控逐段审查 + eval_template_flash.py 标尺 diff + pytest 277 passed

---

## 核验结论：通过

**4 项实施全部正确落地。措辞分支（failedObs=0 → degraded 区分）逻辑正确·"图层"字眼不再出现在零工具场景。eval 标尺改（multi→clip/density）对齐架构现实。RST-L06 preset fallback（区名条件 + 单要素）正确。buffer/cell_size 门控改判 diagnose.template 正确。pytest 277 passed 零回归。**

---

## 一、②a 措辞修复 — **OK**

### composeGapCard `:226-234` 分支逻辑

| 条件 | 措辞 | 判定 |
|------|------|:---:|
| `_needsTool`（缺工具） | "缺现成工具" | ✅ 不变 |
| `request_upload` / gap / needed | "还差关键数据" | ✅ 不变 |
| **failedObs=0 + degraded** | **"我没能理解这个问题的分析需求"** | ✅ 新·无"图层"字眼 |
| **failedObs=0 + 非 degraded** | **"这个问题我暂时无法直接回答"** | ✅ 新·无"图层"字眼 |
| failedObs > 0（默认） | "没跑通——没能生成可用的图层" | ✅ 不变（确实试了工具） |

### gap 出口 `:1334-1343`

```javascript
const _triedTools = failedObs.length > 0;
const _honestText = _triedTools
  ? composeGapCard(...) + '---\n**诚实结论**：本轮未产出新图层。'  // 试了 → 说图层
  : composeGapCard(...);   // 没试 → 非图层叙事（composeGapCard 内分支措辞）
```

**"图层"字眼检查**：
- `_triedTools=true`（failedObs>0）：有"图层"——✅ 正确（确实试了工具·图层叙事合理）
- `_triedTools=false`（failedObs=0）：composeGapCard 内走 `:226-231` 分支——**无"图层"字眼** ✅

**failedObs 判据可靠**：只在 `:753/755/1261`（while-loop 内工具失败）push·零工具尝试 = 没进 loop = failedObs 空 ✅

---

## 二、②b-1 eval 标尺 — **OK**

### 标尺改 diff（`:88-89`）

```python
# 改前（标尺错——select_template 不返 multi）
('西陵区的商业用地', 'multi'),
('西陵区范围内密度分析', 'multi'),

# 改后（标尺对齐架构——select_template 返单工具）
('西陵区的商业用地', 'clip'),           # multi extract_overlay 链在前端覆盖
('西陵区范围内密度分析', 'density'),    # multi clip_density 链在前端覆盖
```

**glm组 预检标尺纠错采纳** ✅——注释明示"select_template 是 v1 单工具选择器·不返回 multi·multi 是前端 CHAIN_REGISTRY 概念"。

### 92% 验证

claude组 报 34/37=92%。glm组 无法独立跑 eval（需 API key·本环境 SKIP）。但标尺改逻辑正确——2 条从 multi→实际单工具·消除了 2 个系统性 MISS。MISS 3（rank/zonal·clip/overlay·hotspot/density 既有歧义）非标尺引入 ✅

---

## 三、②b-2 RST-L06 硬化 — **OK**

### chain pre-check `:1129-1142` preset fallback

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| deriveAvailable 无匹配 → fallback 条件 = 问句含区名 | ✅ | `:1131` `if (!_boundary && /(.+?)(?:区\|市\|县)/.test(...))` |
| 无区名不猜 | ✅ | 正则不匹配 → 不进 fallback → boundary 空 → chain 不出 → 走单工具/ask_user |
| preset layer 搜索（行政区） | ✅ | `:1132` `getLayers().find(x => x.name === '行政区' \|\| /行政区/.test(x.name))` |
| 取单要素（非整集合） | ✅ | `:1136-1139` `.find(f => properties.name.includes(_pname))` → 单 feature |
| boundary 赋值 | ✅ | `:1143` `diagnose.params.boundary = _boundary` |

**glm组 预检建议（"有区名才 fallback"）采纳** ✅

---

## 四、②b-3 buffer/cell_size 门控 — **OK**

### 门控改判 `:1568/1573`

```javascript
// 改前（tool 变量·G5 reroute 后旧值）
if (tool === 'density' && !p.cell_size) { ... }
if (tool === 'buffer' && !p.radius_m && !p.radius) { ... }

// 改后（加 diagnose.template·reroute 后新值）
if ((tool === 'density' || diagnose.template === 'density') && !p.cell_size) { ... }
if ((tool === 'buffer' || diagnose.template === 'buffer') && !p.radius_m && !p.radius) { ... }
```

**Codex P1 采纳** ✅——G5 reroute（`:1457` 方格→density / 周边→buffer）更新 `diagnose.template` 但局部 `tool` 变量仍是旧值。加 `diagnose.template` 条件确保 reroute 后 derive 仍触发。

**副作用检查**：`tool === 'density'` 和 `diagnose.template === 'density'` 是 OR 关系——原 case（FC 直接选 density·tool=density）仍触发 ✅。新增 case（G5 reroute 到 density·tool≠density 但 template=density）也触发 ✅。无误触发（template 只在 reroute 后变·非 reroute 不变）✅

---

## 五、承重 + 回归

| 核验点 | 结果 |
|--------|:---:|
| diagnose prompt 不动 | ✅ |
| 三态出口结构不动（exit:'gap' 不变） | ✅ |
| ChatRequest 不动 | ✅ |
| select_template 不动（标尺改非路由改） | ✅ |
| pytest 277 passed | ✅ 零回归 |

---

## 六、验证清单

| # | 验证项 | 方法 | 结果 |
|:---:|------|------|:---:|
| 1 | composeGapCard failedObs=0 分支（degraded 区分） | 代码审查 | ✅ |
| 1 | "图层"字眼不在零工具场景 | 代码审查 | ✅ |
| 2 | gap 出口 _triedTools 分支 | 代码审查 | ✅ |
| 3 | eval 标尺 multi→clip/density | diff + 注释 | ✅ |
| 4 | RST-L06 preset fallback（区名条件 + 单要素） | 代码审查 | ✅ |
| 5 | buffer/cell_size 门控改 diagnose.template | diff + OR 条件分析 | ✅ |
| 6 | pytest 277 passed | 全量运行 | ✅ |
| 7 | 承重零触碰 | diff 范围 | ✅ |
| 8 | e2e-seam 措辞断言需补？ | — | ⚠️ P2 建议（非阻塞）|

---

## 七、P2 建议

**e2e-seam 措辞断言**：当前无前端断言验证"零工具场景不含'图层'字眼"。建议加一个 e2e-seam 测试（仿 RST-L06）·触发 gap 出口（零工具）·断言答案不含"图层"——防措辞回退。但非阻塞（代码审查已确认）。

---

## 八、一句话结论

**4 项实施全部正确落地——措辞修复（failedObs=0 → degraded 区分·"图层"不在零工具场景）+ eval 标尺改（multi→clip/density·glm 标尺纠错采纳）+ RST-L06 硬化（preset fallback 区名条件 + 单要素·glm 建议采纳）+ buffer/cell_size 门控改 diagnose.template（Codex P1 采纳）。pytest 277 passed 零回归。承重零触碰。1 个 P2 建议（e2e-seam 措辞断言·非阻塞）。**

---

*glm组（ZCode + GLM 5.2）· CB-16 措辞 + 遗留检查 · 2026-08-04*  
*验证基于：harness.js :213-242 composeGapCard + :1330-1344 gap 出口 + :1108-1145 chain pre-check + :1568/1573 门控逐段审查 + eval_template_flash.py :88-89 标尺 diff + pytest 277 passed。*
