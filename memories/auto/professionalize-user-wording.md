---
name: professionalize-user-wording
description: "When replying or advising, gently pair non-professional phrasing with the professional term"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37c73a6f-6b0f-40d8-a99f-fb15b12069c5
---

提建议/回复时，顺带把用户非专业的表述纠正为专业表达（轻量、就地在句中给出专业术语，不长篇说教）。

**Why:** 用户非程序员，希望借协作逐步建立专业化表达；与 revision-log 的"意图专业化转译"一脉相承（见 [[maintain-revision-log]]）。

**How to apply:**
- 遇到技术/设计层面的非专业表述，在回复里自然带出专业说法，例如：用户说"那个颜色不对"→ 回复用"L2 中性色板（色带）应与急/盼胶囊同色系呼应"。
- 只纠正**技术/设计术语**，不纠正寒暄/口语（如"很好/行"），避免啰嗦。
- 一次只点 1-2 个最相关的，不堆砌；用户能无感吸收即可。
- 若某术语项目已有约定（如"类型=大类/表现=小类"），优先用项目术语而非通用词。见 [[maintain-revision-log]] 术语铁律。
- **术语铁律**：核密度分析 = **核密度分析（Kernel Density Estimation, KDE）**，**禁用"热核"简称**（不规范）；英文标识符 `heatmap` 保留（MapLibre layer 类型名，正确）。
