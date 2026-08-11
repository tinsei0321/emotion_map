# CB Index — Catch-Ball 统一入口

> **读我**：claude组（Claude Code 开发主）+ Codex + zcode组（ZCode + GLM 5.2·2026-08-11 由 glm组 正式更名）启动时读此文件，了解 CB 全貌。
> **维护**：每轮 CB 完成后更新。最后更新：2026-08-11（CB-23 两板块风险前置验证发起·阶段 1' 前·紧急任务）。

---

## 当前状态

| 项目 | 状态 |
|------|:---:|
| **当前 CB 轮次** | **CB-23 · 阶段 1' 风险前置验证 → 反评价收敛定稿**（Codex 回收 8 项全采纳·待实施 A1-A8·zcode 街道查源待发） |
| **上一轮** | CB-22i 追问标记崩溃根因修复（.slice bug·完整链路实测通过·commit a27c0e2e） |
| **当前环境** | **claude组（Claude Code + DeepSeek/GLM 5.2·开发主）** + **Codex** + **zcode组（ZCode + GLM 5.2·评估·2026-08-11 由 glm组 更名·本次任务分工）** |
| **当前分支** | `main`（阶段 0' b4cb7a9d + CB-23 4fd10ccd + 更名 031a869b·待 push） |
| **最新讨论** | `discuss/CB23-两板块风险前置验证_反评价收敛定稿_2026-08-11.md`（8 项采纳清单定稿阶段 1' 设计） |
| **最新进展** | 风险前置三验证（zonal ✅ / hotspot ⚠️ 两坑 / 街道缺失 ⚠️）→ **Codex 回收核验成立**（F1 partial/F2 partial/F3 agree/F4 agree+补·8 项全采纳）→ **反评价收敛定稿**：D1 加权密度主图（grid weight_field F_010）/ D1c Gi* 降辅助 / D2 街道 P0 zcode 查源 / D3 权重规范+常数守卫 F_011 / D4 补 `{col}_sum`+sort_by F_012 / D5 manifest 漂移修 → **阶段 1' 落地清单 A1-A8** → 下一步：发 zcode 查源 prompt + 后端小扩展 |
| **接手文档** | `memories/repo/session-handoff.md` + `docs/catch-ball/cb-journal.md`（CB-23 轨迹）+ `_handoff/HOME.md` + `OFFICE.md` |
| **上次操作人** | tinsei0321 + claude组（+ Codex/glm 评估中） |

## 快速开始

### claude组（Claude Code·开发主）

1. Hook 自动检测：`.claude/hooks/on_session_start.py` 启动时打印 CB 状态
2. 手动：读本文件 → 按需进入对应目录
3. 新接手：读 `_handoff/DEEPSEEK_ONBOARDING_2026-07-30.md`

### Codex / glm组（CB 辅助评估）

1. 读本文件了解当前轮次 + 最新 SCAN
2. 读 `KNOWLEDGE.md` 了解红线和语境
3. 产出 SCAN → `scan/CB{NN}-{topic}_{env}-{model}_{YYYY-MM-DD}.md`（glm组 用 `CB{NN}-{topic}_glm组_{YYYY-MM-DD}.md`）
4. 按需进入对应目录
5. **glm组（ZCode + GLM 5.2）**：以第三方评估者身份加入·独立 SCAN/讨论·与 Codex 互补视角·非开发主

## 文件夹地图

```
docs/catch-ball/
├── _cb-index.md          ← 你在这里
├── RULES.md              CB 规则（评估方法、七轴评分、文档规范）
├── KNOWLEDGE.md          CB 记忆库（红线、语境卡片、SCAN 标尺纠正）
├── cb-journal.md         CB 轨迹（按轮倒序·SCAN摘要+反评价+行动+状态）
├── retired.md            退役台账
│
├── scan/                 SCAN 评估报告
│   ├── CB01~CB03         历史评估（DeepSeek）
│   ├── CB09-*.md         CB-09 实测诊断 + GLMv3 修复审计
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
└── _handoff/             换机交接卡 + 接手文档
    ├── HOME.md            家里做了什么、待做什么
    ├── OFFICE.md          办公室做了什么、待做什么
    ├── SESSION_2026-07-30.md     今日 Session 完整记录
    └── DEEPSEEK_ONBOARDING_2026-07-30.md  Claude Code + DeepSeek 接手文档
```

## CB 流程

```
SCAN 阶段（评估方：Codex 或 glm组·CB 辅助·独立于开发主 claude组）
  ① 读本文件了解当前轮次
  ② 读 KNOWLEDGE.md 了解红线和语境
  ③ 产出 SCAN → docs/catch-ball/scan/{NN}-{model}.md（glm组 用 {NN}-glm组.md）
  ④ 更新本文件「待反评价」
  ⑤ 更新 _handoff/{HOME|OFFICE}.md

Journal 阶段（项目方：claude组）
  ① 读本文件发现新 SCAN
  ② 逐条反评价（agree/disagree/partial）
  ③ 追加 cb-journal.md 对应轮次
  ④ 更新本文件「已反评价」
```

## 换机指南

1. **到新环境后**：`git pull` → 读本文件 → 读 `_handoff/{HOME|OFFICE}.md`
2. **离开前**：更新 `_handoff/{HOME|OFFICE}.md` → `git commit + push`
3. **跨环境一致性**：所有 CB 文件在 git 中同步，两边都能看到完整历史
