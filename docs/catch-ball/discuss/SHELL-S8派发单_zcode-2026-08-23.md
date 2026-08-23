# SHELL(S8) · 壳架构知识卡派发单（claude·2026-08-23 晚）

> 主手：zcode（纯编排）。执行：**claude**（简单内容件）。commit 前缀 `SHELL(S8):`。本地仓即最新·零 pull 零 push。
> 依据：壳阶段联合任务书 v1.0 §二 S8——「壳架构知识卡（裁定不入 RAG·工程契约类）·D 内容·0.2d」。

## 规格

1. **产出**：`docs/shell-architecture.md`（壳架构一页知识卡）——内容五段：
   - **白话摘要段**（AGENTS 3b 硬条款·开篇）：壳是什么/三保障（换脑/同等质量/流式）/当前状态——医院比喻·零专业术语。
   - 架构图（ASCII 四层：用户→壳对话→引擎/适配器→EMC 服务/工具/RAG）。
   - 三保障对应实现（BrainAdapter 契约/acp-channel.js 事件流/ACP v1.1）——各附 file 指针。
   - 红线清单（五条·从 v1.0 §三照抄+现状注记）。
   - 垂直域切换位说明（六件套+共享不变量清单指针 → docs/vertical-profile.md）。

2. **裁定注记**（卡内显式声明）：本卡为工程契约类知识·按 PT-CB9 方向 CB 收敛裁定**不入 RAG 语料**（下划线排除规则同族·语料地图白名单制不扩）。

3. **零代码改动**——纯 docs 件。产出含白话摘要段。

## DoD

- [ ] 落盘 `docs/shell-architecture.md` + 执行记录（`SHELL-S8执行记录_claude-2026-08-23.md`·简短即可）
- [ ] 全量 pytest 不降（552+4 基线·纯 docs 件应零影响）
- [ ] 显式路径 commit·零 pull 零 push

> zcode 主手 · 2026-08-23 · S8 派发（壳阶段收官件）
