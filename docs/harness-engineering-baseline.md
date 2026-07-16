# Harness 工程基线（六要素评估）

> 依据 OpenAI《Harness Engineering》六要素框架，对本项目 Claude Code harness 层 + 应用内 harness（`frontend/js/ai_qa/`）的成熟度评估。
> 渐进式披露文档——按需读，不自动注入。对照 `docs/context-map.md`。最后更新：2026-07-16。

## 成熟度总表

| # | 要素 | 成熟度 | 一句话 |
|---|---|---|---|
| 1 | System Prompt | solid | 四级分层 + 三层记忆 + 北极星极强；GLM 路由未在 prompt 声明（次要） |
| 2 | Tool Definitions | basic→solid | 自建 vision-bridge MCP + skills 索引是真资产；智谱栈全局托管（非项目 .mcp.json） |
| 3 | Execution Sandbox | solid（项目最强） | `api/sandbox.py` 5 层加固 + 29 真子进程测试 + kill switch |
| 4 | Orchestration | basic | 9 agent + SOP 三级纸面清晰；纯文字承诺，无代码强制派发 |
| 5 | Hooks | basic→solid | emoji-block + trace-digest + **阶段一新增 PreCompact 快照 + 阈值提醒** |
| 6 | Middleware | none（Claude Code 层） | 真正中间件活在 `harness.js`（四态出口/对账/run_python 收口），CC 层用 hook 补丁 |

## 要素详评

**① System Prompt**：`CLAUDE.md`（项目 23.5KB）+ `AGENTS.md` + 3 模块 CLAUDE.md + 全局。优先级链「本文件 > 项目根 > 全局」每层声明。三层记忆（全量 CLAUDE.md / 按需 memory / 渐进 docs）。弱：实际推理走 GLM（bigmodel.cn 网关），prompt 假设 Claude 语义，工具用/缓存/hook 行为模型依赖。

**② Tool Definitions**：`.mcp.json` 列项目专属 server（playwright / vision-bridge / github-disabled）。**智谱栈（zai-mcp-server / web-search-prime / web-reader / zread）全局托管**（跨项目可用，非项目文件）——这是正确分层，非漂移。skills 经 `SKILLS_INDEX.md` 精选 ~50/464。弱：无 per-agent 工具收窄（reviewer 该 read-only，靠约定非强制）。

**③ Execution Sandbox**：`api/sandbox.py` 5 层——subprocess 隔离（`-I`）+ import 白名单（frame-based trust）+ open-wrapper 路径白名单 + AST 反射审计 + eval/exec/compile frame guard（memory `sandbox-eval-wrapper-context-restore`）。29 真子进程测试（攻击拒绝 + 合法突破）。诚实声明非 OS 级。弱：run_python 策略门在前端 `harness.js:466`（`ctx.allowCodeViz`），直 POST `/run` 可绕——技术后停在 sandbox，用户层门仅客户端。

**④ Orchestration**：`.claude/agents/` 9 agent + `AGENTS.md` 3 管线（纯逻辑/纯UI/逻辑+UI）+ SOP 三级（轻量/标准/严格）。DoD 6 项。弱：编排是 prompt 级散文，无代码强制 tier 路由/并行派发；`sim-emotion-data` 未在 settings 注册。

**⑤ Hooks**：`.claude/hooks/` —— SessionStart（**阶段一加阈值提醒**）/ SessionEnd（trace-digest 闭环）/ PreToolUse（emoji-block 真 enforcement）/ PostToolUse（.pyc 清理）/ **PreCompact（阶段一加 .wip.md 快照）**。`.githooks/pre-commit` pytest 门（需手动启）。弱：仍无 UserPromptSubmit / Stop；「lint」hook 只查 emoji（名过实）。

**⑥ Middleware**：Claude Code 层**无消息变换能力**（hook 只能 block/log）。真正的中间件在应用内 `harness.js`：`parseAgentStep` 归一 + 四态出口（RESULT/GAP/PARTIAL/ASK）+ `_verifyClaims` 对账 + `run_python` 收口 + `onDegraded` 不裸输。两套 harness 不共享词汇——CC 层用 hook 补丁近似，不另造框架。

## 最高 ROI 修复（阶段一已做 / 待做）

- ✅ **园丁层**（要素⑤+⑥补丁）：`/garden` + 阈值提醒 + PreCompact 快照（本阶段落地）。
- ✅ **漂移自检 ritual + 单写者纪律**（要素④补丁）：入全局 CLAUDE.md。
- ⬜ **manifest 刷新**（要素①新鲜度）：AGENTS.md/SKILLS_INDEX.md 补 ai_qa/ 等 5.x 主力；CLAUDE.md 模块数 13→18/510+（`/garden` 会列，待整）。
- ⬜ **薄 SOP 代码门**（要素④）：触 2+ 文件/控制流/I/O 时 `/sop-check` 提醒（非阻断）——可选，低优先。
- 不动：要素③ sandbox（已最强）；要素⑥ CC 层中间件（依赖官方能力，用 hook 补丁够用）。
