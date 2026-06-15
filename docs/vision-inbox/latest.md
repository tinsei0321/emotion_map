# 识图结果 — 2026-06-15

## 概述

一张 Claude Code 终端截图，标题 "Bash Test vision chat with explicit env var"。正在测试火山引擎 Ark 视觉 API，通过环境变量 `ARK_API_KEY` 传入密钥后运行 `.claude/skills/volceng` 脚本。右侧 OUT 面板出现大段乱码。

## 详细描述

### IN 面板（输入命令）

```bash
ARK_API_KEY="ark-441a78e6-125f-4a40-89dd-fe690ef09cde-b9449" python .claude/skills/volceng
```

- 将火山引擎 API Key 作为临时环境变量传入（只对当前命令生效）
- 执行 `.claude/skills/volceng` 脚本，该 skill 用于调用火山引擎的视觉/多模态模型

### OUT 面板（输出）

- 显示大量 `��`（U+FFFD 替换字符）和重复的乱码序列
- 乱码中可辨识出部分 Markdown 片段如 `### j...`（推测原始输出为标题 `### 某某内容`）
- 整体呈现典型的编码错乱特征

## 乱码原因

1. **Windows 终端 GBK ↔ UTF-8 编码冲突（主因）** — PowerShell/CMD 默认使用 GBK (cp936) 编码，而 Python 脚本输出 UTF-8，字节被 GBK 解释器误读后产生 U+FFFD 替换字符。项目编码铁律第 2 条 `_safe_print()` 正是为此而生。

2. **API 返回二进制数据（次因）** — 如果火山引擎视觉 API 返回了二进制内容（图片等）而脚本直接 `print()`，也会产生乱码。

## 安全提醒

截图中 API Key 完整可见（`ark-441a78e6-...-b9449`）。公开分享前应遮挡或到火山引擎控制台重置此 Key。
