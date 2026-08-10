# CB Index — Catch-Ball 统一入口

> **读我**：claude组（Claude Code 开发主）+ Codex + glm组（ZCode + GLM 5.2）启动时读此文件，了解 CB 全貌。
> **维护**：每轮 CB 完成后更新。最后更新：2026-08-10（CB-22g 反评价收敛完成·Codex 戳穿 trace 取证误判·采 Codex 主线·P0 执行中·连带体检整合进 RAG）。

---

## 当前状态

| 项目 | 状态 |
|------|:---:|
| **当前 CB 轮次** | **CB-22h · 追问读秒卡住·三组根因讨论**（CB-22g 修复后用户实测仍卡·真实会话 sess-34620 取证：finalStep LLM 挂起 5 分半·office 网络不稳 + 后端无服务端超时·6 焦点待三组验证） |
| **上一轮** | CB-22g 追问无法完成（反评价收敛定稿·采 Codex 主线·F_018/F_019/stages.js:322/体检 RAG 整合·**用户实测仍卡→CB-22h**） |
| **当前环境** | **claude组（Claude Code + DeepSeek/GLM 5.2·开发主）** + **Codex** + **glm组（ZCode + GLM 5.2·评估）** |
| **当前分支** | `main`（CB-22d 已并入·fix/emc-buglog 已删·ahead 11 未 push） |
| **最新讨论** | `discuss/CB22h-追问读秒卡住_三组根因讨论发起_2026-08-10.md`（真实会话 sess-34620 证据 + 6 焦点·含三组各自 curl 实测网络） |
| **最新进展** | CB-22g 修复（d1d50e6b·F_018/F_019/体检 RAG 36→52）→ 用户实测仍「读秒卡住」→ **真实会话取证**（sess-34620=uvicorn PID·17:13:45 flash LLM 无 exit 挂 5 分半 + 全 trace 401/net/mid-stream 交替 + API 直测 200·间歇性 + office 网络不稳历史）→ **CB-22h 发起·待三组验证** |
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
