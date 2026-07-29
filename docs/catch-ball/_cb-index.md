# CB Index — Catch-Ball 统一入口

> **读我**：VS Code（Claude Code）和 ZCode（DeepSeek/GLM）启动时读此文件，了解 CB 全貌。
> **维护**：每轮 CB 完成后更新。最后更新：2026-07-29。

---

## 当前状态

| 项目 | 状态 |
|------|:---:|
| **当前 CB 轮次** | **CB-09**（用户实测诊断·5 案例 + 7 根因分析） |
| **下一轮** | CB-10（待 P0 修复后触发验证） |
| **最新 SCAN** | `scan/CB09-v1.0实测诊断_ZCode-DeepSeek_2026-07-28.md` |
| **最新根因分析** | `rootcause/2026-07-28-multi-extract-reasoning-spiral.md` |
| **最新综合审计** | `audit/2026-07-28-comprehensive.md` |
| **上次操作环境** | ZCode + DeepSeek V4 Pro |
| **上次操作人** | DeepSeek（评估方） |

## 快速开始

### VS Code（Claude Code + GLM）

1. Hook 自动检测：`.claude/hooks/on_session_start.py` 启动时打印 CB 状态
2. 手动：读本文件 → 按需进入对应目录

### ZCode（DeepSeek / GLM）

1. AGENTS.md 首段引导读本文件
2. 读 `KNOWLEDGE.md` 了解红线和语境
3. 按需进入对应目录

## 文件夹地图

```
docs/catch-ball/
├── _cb-index.md          ← 你在这里
├── RULES.md              CB 规则（评估方法、七轴评分、文档规范）
├── KNOWLEDGE.md          CB 记忆库（红线、语境卡片、SCAN 标尺纠正）
├── cb-journal.md         CB 轨迹（按轮倒序·SCAN摘要+反评价+行动+状态）
├── retired.md            退役台账
│
├── scan/                 SCAN 评估报告（第三方评估产出）
│   ├── 01-deepseek.md    CB-01
│   ├── 02-deepseek.md    CB-02
│   ├── 03-deepseek.md    CB-03
│   ├── 04-glm-v3.md      CB-09（GLM v3 修复审计）
│   └── cpd/              CPD 专轨评估
│
├── rootcause/            根因分析报告
│   ├── 2026-07-28-MC-field-rename.md
│   ├── 2026-07-28-layer-hallucination.md
│   ├── 2026-07-28-nl-vs-capsule.md
│   ├── 2026-07-28-streaming-failure.md
│   └── 2026-07-28-finalstep-timeout.md
│
├── audit/                综合审计报告
│   ├── 2026-07-28-comprehensive.md  全局复盘+代码审计
│   └── 2026-07-28-deep-dive.md      全链路+识别+路由深度审查
│
├── arch/                 架构设计 + 历史评估文档
│   ├── SUMMARY.md        v2 架构全景（68 决策）
│   ├── 01~09-*.md        9 模块设计
│   ├── EVAL_*.md         历史评估报告
│   └── ...
│
└── _handoff/             换机交接卡
    ├── HOME.md            家里做了什么、待做什么
    └── OFFICE.md          办公室做了什么、待做什么
```

## CB 流程

```
SCAN 阶段（评估方：ZCode+DeepSeek 或 VS Code+GLM）
  ① 读本文件了解当前轮次
  ② 读 KNOWLEDGE.md 了解红线和语境
  ③ 产出 SCAN → docs/catch-ball/scan/NN-model.md
  ④ 更新本文件「待反评价」
  ⑤ 更新 _handoff/{HOME|OFFICE}.md

Journal 阶段（项目方：任一环境）
  ① 读本文件发现新 SCAN
  ② 逐条反评价（agree/disagree/partial）
  ③ 追加 cb-journal.md 对应轮次
  ④ 更新本文件「已反评价」
```

## 换机指南

1. **到新环境后**：`git pull` → 读本文件 → 读 `_handoff/{HOME|OFFICE}.md`
2. **离开前**：更新 `_handoff/{HOME|OFFICE}.md` → `git commit + push`
3. **跨环境一致性**：所有 CB 文件在 git 中同步，两边都能看到完整历史
