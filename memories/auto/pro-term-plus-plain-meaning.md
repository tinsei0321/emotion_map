---
name: pro-term-plus-plain-meaning
description: 推进具体项目时专业词必须紧跟通俗解释，用户是初学者
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 41a5ee74-402f-460b-9c2e-84071b7ce5aa
---

用户是初学者，不具备听懂专业词（LLM 韧性 / retry / fallback / streaming / generator / SSE / token / context / provider 等）的知识架构。推进具体项目时，**每个专业词后面必须紧跟一个通俗解释**，用「专业词（= 通俗解释）」或「专业词 —— 通俗话」的方式配对输出，不让人一头雾水盲目推进。

**Why:** 用户明确反馈"不要让我一头雾水、不知道在干嘛而盲目推进"；初学者需要在"被带领"中逐步建立知识架构，纯专业词会阻断理解与决策，导致用户无法判断方向对错。

**How to apply:** 沟通（聊天回复）+ **所有交付物（计划/报告/文档/代码注释）一律遵守**，不只聊天。专业词第一次出现时配解释，反复出现的可省略。技术细节（行号/函数名/代码/变量名/路径）保持英文，解释用中文大白话或类比（如"retry 重拨""fallback 换家""generator 像水龙头按需吐字"）。关联 [[chinese-all-deliverables]]（交付物用中文）。
