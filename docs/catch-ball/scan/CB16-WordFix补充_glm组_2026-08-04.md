# CB-16 措辞修复补充：eval 实测纠正（glm组 · ZCode + GLM 5.2）

> **补充方**：glm组（ZCode + GLM 5.2）  
> **日期**：2026-08-04 | **触发**：后台 eval 运行完成·实际结果与 claude组 声称不符

---

## 补充结论：eval 实际 84%（非 claude组 声称的 92%）·仍 GO

**glm组 独立运行 `PYTHONPATH=. python tests/eval_template_flash.py` 得到 31/37=84%·非 claude组 声称的 34/37=92%。差异 = "西陵区的商业用地"标尺改后仍 MISS（期望 clip·Flash 实得 overlay）。84% 仍 > 80% GO 门槛·发版不阻塞。但 92% 声称不准确·应纠正。**

---

## 实测数据

```
PYTHONPATH=. python tests/eval_template_flash.py

  [MISS] 西陵区的商业用地  → 期望 clip / 实得 overlay
  [OK]  西陵区范围内密度分析  → 期望 density / 实得 density

命中率：31/37 = 84%
═══ Go/No-Go：≥80% ship single 路径；<80% 只保 concept+multi/unknown ═══
PASS — 可 ship single 路径

FC 参数填充率：3/3 = 100%
```

---

## 差异分析

| 指标 | claude组 声称 | glm组 实测 | 差异 |
|------|:---:|:---:|:---:|
| eval 命中率 | 34/37 = 92% | 31/37 = 84% | -3 |
| MISS 数 | 3（rank/zonal·clip/overlay·hotspot/density 既有歧义） | **4**（3 既有 + 西陵区的商业用地 clip→overlay） | +1 |
| GO/NO-GO | GO | GO（84% > 80%） | 一致 |

**新增 MISS 根因**：`西陵区的商业用地` 标尺改为期望 `clip`·但 Flash LLM 对此问句概率性返回 `overlay`（面∩面解读·"区内的某类用地"= 区面 ∩ 用地面）。两种解读都合理——标尺改从 `multi` → `clip` 消除了 multi MISS·但引入了新的 clip↔overlay 歧义 MISS。

**建议**：标尺改为接受 `clip` **或** `overlay`（两者都合理）·或保持单值接受 Flash 概率性 MISS。当前 84% GO 不阻塞。

---

## 对前报告的修正

glm组 前报告（CB16-WordFix检查_glm组_2026-08-04.md）中：
- "eval 标尺改合理？92% 验证可信？" → **修正为 84%**（92% 不准确）
- "MISS 3（既有歧义）确认非标尺引入？" → **修正为 MISS 4**（3 既有 + 1 新标尺引入的 clip↔overlay 歧义）
- **GO 判定不变**：84% > 80% 门槛 = GO

---

*glm组（ZCode + GLM 5.2）· CB-16 eval 补充 · 2026-08-04*
