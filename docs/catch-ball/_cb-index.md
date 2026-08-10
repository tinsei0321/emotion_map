# CB Index — Catch-Ball 统一入口

> **读我**：claude组（Claude Code 开发主）+ Codex + glm组（ZCode + GLM 5.2）启动时读此文件，了解 CB 全貌。
> **维护**：每轮 CB 完成后更新。最后更新：2026-08-10（CB-22g 反评价收敛完成·Codex 戳穿 trace 取证误判·采 Codex 主线·P0 执行中·连带体检整合进 RAG）。

---

## 当前状态

| 项目 | 状态 |
|------|:---:|
| **当前 CB 轮次** | **CB-22g · 反评价收敛完成**（Codex 戳穿 trace 取证误判：sess-22008 是 pytest·F_005≠FC·FC 缺埋点；采 Codex 主线·连带体检整合进 RAG）·P0 执行中 |
| **上一轮** | CB-22f 纯问答→空间动作链路由打通（5 阶段实施完成·315 passed·**用户实测追问失败→CB-22g**） |
| **当前环境** | **claude组（Claude Code + DeepSeek/GLM 5.2·开发主）** + **Codex** + **glm组（ZCode + GLM 5.2·评估）** |
| **当前分支** | `main`（CB-22d 已并入·fix/emc-buglog 已删） |
| **最新讨论** | `discuss/CB22g-追问无法完成_反评价收敛定稿_2026-08-10.md`（glm+Codex 回应→claude 主线程核实收敛·采 Codex 主线）+ 两组回应稿 |
| **最新进展** | CB-22g 收敛：claude 上轮 trace 取证误判（sess=pytest·F_005≠FC·FC 无埋点）→ 坐实 F_016 冲突→F_018 + FC 缺埋点 + knowledge_qa 零参 schema 嫌疑 + 旧 SSE 死路径（不做 glm 补 knowledge）→ P0 代码修复（F_018 / validate_track_ids 守卫 / FC 埋点 F_019 / stages.js:322 bug）+ 连带体检整合（md+16fact+重建）·P1 待用户 live 冒烟 + 重采真会话定位 FC 根因 |
| **接手文档** | `memories/repo/session-handoff.md`（08-05 卡·已过时·历史背景）+ `_handoff/HOME.md` + `OFFICE.md`（08-08 权威快照）+ `_handoff/CB恢复记忆prompt_2026-08-09.md` |
| **上次操作人** | tinsei0321 + claude组 + Codex + glm组 |

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
