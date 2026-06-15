# Skills 索引 — emotion_map 项目精选

> 464 个已安装 Skill 中，本索引列出**与本项目直接相关**的核心技能。
> Claude 在接收到任务时会自动匹配 description 最相关的 skill，本索引用于帮助快速定位。

## 🔴 每日工作流（高频使用）

| Skill | 触发场景 |
|-------|----------|
| `python-*` (12个) | 任何 Python 代码编写/审查/打包 |
| `python-plugin-*` (16个) | ruff 格式化、pytest 测试、uv 包管理 |
| `code-quality-plugin-code-review` | 代码审查 |
| `code-quality-plugin-code-lint` | 代码检查 |
| `code-quality-plugin-code-refactor` | 代码重构 |
| `testing-plugin-test-*` (10个) | 测试运行/分析/报告 |
| `git-plugin-git-commit` | Git 提交 |
| `git-plugin-git-pr` | PR 管理 |

## 🟡 文档输出（中频使用）

| Skill | 触发场景 |
|-------|----------|
| `anthropic-docx` | 生成 Word 报告 |
| `anthropic-pdf` | PDF 处理 |
| `anthropic-xlsx` | Excel/CSV 数据分析 |
| `anthropic-pptx` | 制作 PPT |
| `daymade-docs-*` (6个) | Markdown/PDF/PPT 转换 |

## 🟢 中文专项（按需使用）

| Skill | 触发场景 |
|-------|----------|
| `ifly-translate` | 中英互译 |
| `ifly-text-proofread` | 中文校对 |
| `ifly-pdf-image-ocr` | OCR 识别 |
| `byted-web-search` | 联网搜索（时效性信息） |
| `byted-text-to-speech` | 文字转语音 |
| `byted-voice-to-text` | 语音转文字 |

## 🔵 项目管理（辅助使用）

| Skill | 触发场景 |
|-------|----------|
| `anthropic-skill-creator` | 创建新的专属 Skill |
| `deep-research` | 深度研究 |
| `prompt-optimizer` | 优化 Prompt |
| `blueprint-plugin-blueprint-*` (30个) | 项目蓝图管理 |

## ⚫ 完全无关（本项目不需要关注）

以下技能对应 Rust/TypeScript/游戏引擎/智能家居/苹果生态，本项目永不会触发：
`bevy-*`, `comfyui-*`, `rust-*`, `typescript-*`, `bun-*`, `home-assistant-*`, `obsidian-*`, `macos-*`, `ios-*`, `taskwarrior-*`, `kubernetes-*`, `terraform-*`, `finops-*`, `langchain-*`, `css-*`, `networking-*`, `container-*`

> 注：无关技能虽然不会被触发，但保留在 `.claude/skills/` 中不影响性能（按需加载）。
