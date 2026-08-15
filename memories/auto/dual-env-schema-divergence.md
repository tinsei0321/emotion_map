---
name: dual-env-schema-divergence
description: ZCode+VSCode 共享工作树并行编辑同一子系统会 schema 分叉；新建带 schema 的子系统须在 skill/契约里锁死格式，跨环境遵循
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 07f5a2c9-55f8-44a7-bb1b-22d8d8873f6e
  modified: 2026-07-29T07:22:07.106Z
---

用户长期 ZCode + VSCode（Claude Code）双环境并行，共享同一 git 工作树。buglog 子系统曾因此分叉：我在 VSCode 建它（YAML frontmatter + ASCII 标签·B001），用户同时在 ZCode 做 CF-09 bug 采集（markdown 表格 + emoji·B002-B008），两套生成器互不兼容 → 我的 `_gen_index.py` 解析不了表格格式（`_parse_fm` 找 YAML `---` → 返空跳过）→ 仪表盘/回归清单对 ZCode 采的 7 个 bug **全盲**，直到我写转换脚本统一回 YAML（2026-07-29，commit abce549）。

**Why**：双环境共享工作树，若子系统没有锁死的 schema 契约，每个环境会各发明一套格式，生成器/消费方只能看到自家格式那一半。

**How to apply**：
- 新建任何带 schema 的子系统（buglog、未来追踪器、知识库），**在 skill/契约文档（SKILL.md）里写死精确格式**（字段名 + 值枚举 + frontmatter vs 表格），让生成器成为唯一解析源。
- 用户在 ZCode 也有动作后，**先 `git status` 核查有无并行改动**，发现同子系统异构格式 → 及早统一（别等积累）。
- 统一时用一次性转换脚本（verbatim 保 body，只换元数据），别手改每条。
- 关联 [[context-coherence-discipline]]（单写者）、[[cb-knowledge-base]]（CB 跨环境登记）。
