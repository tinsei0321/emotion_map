# PT-CB15 · cdh 不可用根因报告（Codex·2026-08-25）

## 白话摘要

不是代码或数据本身坏了，而是“旧服务进程”还占着端口、用着改之前的旧路径。就像家里换了新钥匙，但门口还站着一个拿旧钥匙的人——新指令到了，他打不开门，就回一句“数据状况待确认”。把三个旧进程杀掉、用最新代码重启后，问“你是谁”“你能做什么分析”，以及一个完整的“查清单→分区统计→出图”链路都通了。

## 结论

**根因：数据目录重构后，8600 MCP / 8000 后端 / 8080 前端三个常驻进程未重启，继续加载重构前的路径常量。**

## 证据链

1. 用户手动测试时，`tools/mcp_server_emc.py` 已把 `MANIFEST` 从 `DATA/boundaries/presets/manifest.json` 改为 `DATA/REGISTRY/presets/manifest.json`，但 8600 进程仍是重构前启动的旧进程，仍按旧路径读 manifest → `list_data` 拿不到清单 → 模型只能回答“数据状况待确认”。
2. 同样，8000 后端与 8080 前端白名单也未加载 `DATA/REGISTRY/`、`DATA/AUTHORITY/`、`DATA/THEME/`。
3. 本地静态检查 `list_data` 与 pytest 均正常（2 passed），说明代码/数据正确，问题只在运行态。

## 修复动作

- 杀掉旧进程：8000 PID 33364、8600 PID 21500、8080 PID 33292。
- 以最新代码重启：
  - `py tools/mcp_server_emc.py --http --port 8600`
  - `py -m uvicorn api.main:app --port 8000`
  - `py frontend/serve.py 8080 --open=none`

## 回归验证

- “你是谁？”：正常返回 EMC 分析师身份，不再提前结束。
- “你能做什么分析？”：调用 `list_data` 成功，并给出能力说明。
- 完整链路题：`list_data → zonal_stats → render_spec` 全部 `ok=true`，`done completed`，耗时 66.9s。

## 待讨论（发 kimi / qoder）

1. 是否需要在启动流程加入“路径/版本自检”，避免今后数据目录重构后再次踩“旧进程持旧路径”？
2. 是否需要在 `serve.py` / `start.bat` 启动时强制清理 8600/8000/8080 旧进程（现有 `_free_port` 只清前端与后端，8600 未纳入统一清理）。
3. 用户两个问题暴露的诊断口径：当前“数据状况待确认”文案是否过于笼统，应把“MCP 工具面不可用/旧进程”直接显式化。
