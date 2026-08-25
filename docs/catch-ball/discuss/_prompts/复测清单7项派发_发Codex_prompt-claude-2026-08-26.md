# 复测清单 7 项派发 · 发 Codex 执行（2026-08-26 home）

> 执行者：Codex 桌面工具。任务对象：`d:\Github\emotion_map`（分支 `EMC_Codex_Harness`）。
> 本任务为浏览器级 E2E 复测，非代码开发。发现 bug 只记录不擅改，修不修由主手/用户裁决。

## 背景（已就绪·勿重复验证）

- codex 配置隔离修复已完成并推送（ef93247）：EMC Harness 自备 CODEX_HOME（`_codex_cwd/.codex`），
  与你的桌面配置分离；**你的配置里没有 emc MCP 工具**——本任务走浏览器 E2E，不需要直调 EMC API。
- RAG 索引已重建（385 chunk）。git HEAD 已与 origin 同步。门禁基线：618 passed + 1 skipped。

## 步骤 1：启动服务

执行 `start.bat`（命令行 `cmd /c start.bat` 或双击）。

通过标准：
- 8600（MCP）LISTENING：`netstat -ano | findstr ":8600.*LISTENING"`
- 8000（后端）+ 8080（前端）LISTENING
- 3080（dsh web）起不来为**已知非致命**（home 可能无 EMCxDSH 目录），忽略即可

## 步骤 2：自检

执行 `py tools\devcheck.py`（或双击 devcheck.bat）。
通过标准：全绿（人话版：能测/不能测 + 点哪里）。有红项先记录再继续。

## 步骤 3：进入 EMC 面板

浏览器打开 `http://localhost:8080/frontend/index.html?engine=codex` → 展开 EMC 面板 →
确认绿色「引擎·codex」徽标。

注意：**首次提问时桥会自愈生成 `_codex_cwd/.codex` 配置（预期行为，非异常）**；若面板报
「Codex 桥启动失败」或「harness CODEX_HOME 自愈失败」，记录完整错误 + stderr_tail。

## 步骤 4：复测清单 7 项（逐项记录 PASS/FAIL + 证据）

| # | 操作 | 通过标准 |
|---|---|---|
| 1 | 问「你是谁/能做什么」 | 应答 EMC 产品身份，**无「读代码/改文件/跑命令」** |
| 2 | 问「数据分哪几类」 | 应答 权威 AUTHORITY / 注册 REGISTRY / 专题 THEME / 产物 Export 四层 |
| 3 | 问「投诉 TOP12 社区紫色渲染」 | 图层为**真边界**（万达≈66 顶点量级·非手绘 5-20 点）；再试全量 20+ 走 aggregate_export 不报沙箱错 |
| 4 | 任一数据类回答 | 三段式（**加粗结论+表格+口径段**）·表格有网格线/斑马纹 |
| 5 | 第 4 项后追问「那第 8 个呢」 | 直接答不重述背景（followup_actions 生效） |
| 6 | 用 130 层口径提问（如「按 130 个片区的口径统计…」） | AI **先请示口径**（130 历史 vs 193 现行）再作答 |
| 7 | 连开两个地图页（新标签页开相同 URL） | render_spec 带 target 仅目标页上屏，不带则两页同上 |

## 步骤 5：汇报

按项输出表格：`| 项 | 操作 | 结果 | 证据 |`。失败项给：现象 + 控制台/网络错误 +
截图 + 初步判断。

## 纪律

- 全程中文，`[OK]`/`[WARN]`/`[ERR]` 标记。
- **不 push 任何代码改动**。
- 每项复测留证据（截图/日志）。
- 服务起不来：记录 start.bat + devcheck 输出，逐条列失败原因，**不要反复重启超 2 次**。
