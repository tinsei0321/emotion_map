# Skills 精选索引 — emotion_map 项目

> 2026-07-17 | 从 464 个精简到 ~50 个高频 Skill
> 按项目实际需求精选，无关 Skill 不再列出
> 本文件 = marketplace/plugin Skill 精选；**项目自有能力（EMC ai_qa 技能谱 + 命令）见下方🟣节**

## 🟣 项目自有能力（非 marketplace — 优先用这些，勿重复造轮子）

> 这些是项目内置的，不在上方 marketplace 索引里。改 EMC/归因/除草优先查这里。

| 能力 | 路径 / 入口 | 说明 |
|------|-------------|------|
| **EMC ai_qa 技能谱** | [ai_qa/paradigm.py](ai_qa/paradigm.py) `TEMPLATE_REGISTRY` | 16 技能：concept/density/rank/buffer/clip/overlay/zonal/**compare**/extract_feature/filter_attr/merge/nearest/hotspot/area_stats/multi/unknown。select_template 按决策树路由（C 赛道 decision_type=对比→compare）。改技能目录/决策树须重跑 Flash eval |
| **行业知识库** | [ai_qa/industry_kb/](ai_qa/industry_kb/) | 四领域权威源：urban_planning(规划设计) / urban_renewal(更新) / urban_operation(运营) / urban_governance(治理)。全项目可成长基础设施（顶层政策+核心概念+官方术语+底线指标+项目类型+案例+情绪归因焦点+4×5 多归属映射）|
| **用地分类国标** | [ai_qa/landuse_codes_2023.py](ai_qa/landuse_codes_2023.py) | 2023.11 国标 24 一级/111 二级/40 三级。**读 .py 勿再读 PDF** |
| `/garden` | [.claude/commands/garden.md](.claude/commands/garden.md) | 上下文除草（按需扫过期 memory/巨型文件/漂移 manifest/僵尸注释，**产清单不自动改**）|
| `/verify` | [.claude/commands/verify.md](.claude/commands/verify.md) | 验证流程 |

## 🔴 每日工作流（高频使用 — 14 个）

| Skill | 触发场景 |
|-------|----------|
| `python-code-quality` | Python 代码质量检查 |
| `python-testing-strategy` | 测试策略与 pytest 配置 |
| `python-api-design` | API 设计（FastAPI 等） |
| `python-cli-development` | CLI 工具开发 |
| `code-quality-plugin-code-review` | 代码审查 |
| `code-quality-plugin-code-refactor` | 代码重构 |
| `code-quality-plugin-code-lint` | 代码检查 |
| `code-quality-plugin-debugging-methodology` | 调试方法论 |
| `testing-plugin-test-setup` | 测试环境搭建 |
| `testing-plugin-test-run` | 运行测试 |
| `testing-plugin-test-quick` | 快速测试 |
| `git-plugin-git-commit` | Git 提交 |
| `git-plugin-git-push` | Git 推送 |
| `git-plugin-git-pr` | PR 管理 |

## 🟡 文档/配置/会话（中频使用 — 14 个）

| Skill | 触发场景 |
|-------|----------|
| `anthropic-docx` | 生成 Word 报告 |
| `anthropic-pdf` | PDF 处理 |
| `anthropic-xlsx` | Excel/CSV 数据分析 |
| `anthropic-pptx` | 制作 PPT |
| `daymade-docs-mermaid-tools` | Mermaid 图表 |
| `daymade-docs-pdf-creator` | PDF 创建 |
| `documentation-plugin-docs-generate` | 文档生成 |
| `documentation-plugin-docs-sync` | 文档同步 |
| `project-plugin-project-continue` | 项目继续 |
| `project-plugin-project-discovery` | 项目发现 |
| `session-plugin-session-start` | 会话启动 |
| `session-plugin-session-end` | 会话结束 |
| `configure-plugin-configure-linting` | 配置代码检查 |
| `configure-plugin-configure-formatting` | 配置格式化 |

## 🟢 中文专项（按需使用 — 7 个）

| Skill | 触发场景 |
|-------|----------|
| `ifly-translate` | 中英互译 |
| `ifly-text-proofread` | 中文校对 |
| `ifly-pdf-image-ocr` | OCR 识别 |
| `byted-web-search` | 联网搜索（时效性信息） |
| `byted-text-to-speech` | 文字转语音 |
| `byted-voice-to-text` | 语音转文字 |
| `byted-deepsearch` | 深度搜索 |

## 🔵 Agent/工作流/辅助（12 个）

| Skill | 触发场景 |
|-------|----------|
| `agent-patterns-plugin-agent-teams` | Agent 编排 |
| `agent-patterns-plugin-wave-based-dispatch` | 分波调度 |
| `agent-patterns-plugin-verify-before-plan` | 规划前验证 |
| `workflow-orchestration-plugin-workflow-preflight` | 工作流预检 |
| `anthropic-skill-creator` | 创建新的专属 Skill |
| `anthropic-claude-api` | Claude API 参考 |
| `anthropic-frontend-design` | 前端设计 |
| `deep-research` | 深度研究 |
| `prompt-optimizer` | 优化 Prompt |
| `tools-plugin-mermaid-diagrams` | Mermaid 图表 |
| `tools-plugin-shell-expert` | Shell 专家 |
| `auto-repo-setup` | 自动环境配置 |

## ⚫ 完全无关 — 建议禁用/卸载

以下类别对应 Rust/TypeScript/游戏引擎/智能家居/苹果生态/K8s 等，
本项目永不会触发，占用索引空间，建议清理：

`bevy-*`, `comfyui-*`, `rust-*`, `typescript-*`, `bun-*`, `home-assistant-*`,
`obsidian-*`, `macos-*`, `ios-*`, `taskwarrior-*`, `kubernetes-*`, `terraform-*`,
`finops-*`, `langchain-*`, `css-*` (项目用纯 CSS 变量), `networking-*`,
`container-*`, `cloudflare-*`, `youtube-*`, `twitter-*`, `bilibili-*`, `douban-*`,
`gangtise-*`, `ima-*`, `feishu-*`, `capture-screen`, `competitors-analysis`,
`product-analysis`, `tunnel-doctor`, `video-comparer`, `slides-creator`,
`repomix-*`, `scrapling-*`, `excel-automation`, `financial-data-collector`
