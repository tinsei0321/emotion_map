---
name: dev-workflow-auto-reload
description: 每次改完代码后，清理缓存 + 重启 Streamlit，用户刷新浏览器即可
metadata:
  type: reference
---

# 开发工作流：改代码 → 重启 → 刷新

## 每次改完代码后必做

```bash
# 1. 清 pycache（否则旧 .pyc 可能导致 import 失败）
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# 2. 杀旧进程 + 重启
taskkill //F //IM python.exe 2>/dev/null; sleep 2
py -m streamlit run apps/app_main.py --server.port 8501
```

然后告诉用户：**刷新浏览器 `F5`**。

## 为什么热重载不够可靠

Streamlit 的 `--server.runOnSave` 在以下情况会失效：
- `__pycache__` 残留旧 `.pyc`（最常见的 import 失败原因）
- 新增/重命名函数后模块缓存未刷新
- 文件结构变更
- 多文件联动改动

因此**清缓存 + 硬重启是最可靠的方案**。

**Why:** 用户多次遇到改完代码后刷新页面仍然报 ImportError，最后发现是 pycache 缓存问题。
**How to apply:** 每次代码改动完成后，执行上述命令，然后让用户 F5。
