---
name: env-restore-2026-08
description: 2026-08-10 系统重装后环境恢复事实：Python 3.14.5 用户级安装路径、智谱栈从 backups 恢复、gh 未装、ARK key 待补
metadata: 
  node_type: memory
  type: project
  originSessionId: f704569a-df11-4a01-9845-7faaf0efc5b7
  modified: 2026-08-10T06:03:19.188Z
---

2026-08-10 用户重装系统 + VSCode + Claude Code，环境全面恢复完成：

- **Python 3.14.5**：官方安装包静默安装，用户级路径 `%LOCALAPPDATA%\Programs\Python\Python314\`（`python`/`py`/`pip` 均可用，注册表 HKCU\Environment\Path 已含 Python314/Scripts/Launcher 三段）。Git Bash 里跑 `python` 需自行 export POSIX 路径（Windows 子进程 CreateProcess 不认 POSIX PATH——曾致 serve.py 报 [WinError 2] 找不到 py，真实终端无此问题）。
- **Python 依赖**：pip install -r requirements.txt 全量成功，版本精确一致（pandas 3.0.3 / geopandas 1.1.3 / scrapy 2.16.0 / snownlp / jieba 现场编译）。
- **智谱 MCP 栈**（zai-mcp-server/web-search-prime/web-reader/zread）：从 `~/.claude/backups/.claude.json.backup.*`（老备份，顶层 mcpServers 字段）恢复合并进 `~/.claude.json`，含密钥。以后重装可从 backups 恢复。
- **未装/待办**：gh CLI（GitHub release 下载域网络受限，winget v1.2 太老也装不了）；`.env` 缺 `ARK_API_KEY`/`IFLYTEK_API_KEY`/`VOLCENGINE_API_KEY`（vision_bridge 备选视觉 + 多模态分析要用，SessionStart hook 会提醒）；GITHUB_PAT 不存在（github MCP 既有失效状态）。
- **验证**：pytest 307 passed；hooks 全链路正常；serve.py 前端 8080 + uvicorn 8000 + API 反代全 200。
