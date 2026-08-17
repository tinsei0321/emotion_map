# CB Index — Catch-Ball 统一入口

> **读我**：claude组（Claude Code 开发主）+ Codex + zcode组（ZCode + GLM 5.2·2026-08-11 由 glm组 正式更名）启动时读此文件，了解 CB 全貌。
> **维护**：每轮 CB 完成后更新。最后更新：2026-08-18 凌晨（**EMC×dsh 专题 R0-R9 全线收敛预备·收工归档**：形态3 拍板包+外挂大脑轮收敛+通俗报告在盘待用户拍板；CB-39 B/C 于 main 在途）。

---

## 当前状态

| 项目 | 状态 |
|------|:---:|
| **当前 CB 轮次** | **CB-39 · 双线实施**（数据线：P0 工程线✅验证通过 + A 线 A1-A5✅ → **待 B 线治理**；基线 366+3；唯一现行计划 `discuss/CB39-实施计划_Codex-2026-08-16.md` v3.1）‖ **CB-40 · EMC 现状与目标差距·已收敛**（`discuss/CB40-EMC现状与目标差距_收敛定稿_2026-08-16.md`·CB-39 后排期依据：G1>G5>G2·`docs/goal-status.md` 每轮必更） |
| **上一轮** | CB-38 主线回归与数据沉淀（收敛定稿 + EMC 全局审计 D1-D9 裁定·双输入线并入 CB-39）；CB-24~37 简记见 cb-journal 顶部补账 |
| **当前环境** | **Codex（主开发·唯一 git 写者·08-13 起）** + **claude组（第三方独立评估+收敛）** + **zcode组（评估）**（**dsh组 已退出·08-16**） |
| **当前分支** | `EMC_harness_dsh`（**dsh 专题讨论分支·2026-08-16 开**·承载整体合体三组讨论；main 上 CB-39 B/C 线继续） |
| **最新讨论** | **EMC×dsh 专题·R0-R9 全线收敛预备（08-18 凌晨收工）**——① **形态3（平台化）三组评审零对抗**：拍板包 `discuss/EMC-形态3平台化_拍板包_Codex-2026-08-18.md` **待用户三键**（拍 E4/拍排期/答 B 卷去留）；② **外挂大脑轮（R9·朋友思路）已收敛**：`discuss/EMC-dsh外挂大脑链路_回应与收敛_Codex-2026-08-18.md` 待两键（拍收敛/答朋友成品是否存在）；③ 通俗版收敛报告 `discuss/EMC-dsh合体讨论_通俗收敛报告_2026-08-18.md`（用户已读懂方向）。台账 R0-R9·**换机先读** |
| **最新进展** | CB-39 已开工：P0-2 守卫通电（9 validate_*·15 ID 补注册·SKILL_DEFS 真身解析）+ P0-1 诚实度（phase 真实标签·key 空显式报错·L0 隔离）+ A 线回收归集（E16 六件迁出演示池·数据池三分·page7 归档·**总账 100 行**）；performance 只剩 sim=时间轴专题轮分轴前提；下一批 B 线治理 |
| **接手文档** | `memories/repo/session-handoff.md` + `docs/catch-ball/cb-journal.md`（CB-38 + CB-29~37 补账）+ `_handoff/HOME.md` + `OFFICE.md` |
| **上次操作人** | tinsei0321 + Codex（专题 R8 回收/R9 发起与收敛/拍板包/通俗报告/收工归档·commit push 经授权）+ 三组（形态3 评审×2 + 外挂大脑×3） |

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
