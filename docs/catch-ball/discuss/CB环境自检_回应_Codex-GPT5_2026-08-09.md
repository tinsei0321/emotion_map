# CB 环境自检报告（Codex 组 · 三组并行测试前）

> **报告方**：Codex 组（Codex + deepseek-v4-flash · 第三方评估）
> **日期**：2026-08-09 | **环境**：办公室桌面（Codex 桌面版）
> **用途**：三组并行测试分发前环境就绪核验（claude组 拆解分配）
> **依据**：本地文件已读——`docs/catch-ball/_cb-index.md` / `RULES.md` / `KNOWLEDGE.md`（含 §7.4 三组并行新规）/ `_handoff/HOME.md` + `OFFICE.md` / cb-journal CB-18/18b/19/20 / `docs/trace-log-guide.md`；未做任何 git 操作。

---

## 结论

`{1. Python: OK}|{2. Playwright: OK}|{3. API Key: OK(WARN 可选)}|{4. trace: OK}|{5. 端口隔离: OK}|{6. 平台 Harness: WARN(1)}|{7. CB 机制: OK}`

→ **可以接手测试任务**（2 项 WARN 均不阻塞）

---

## 逐项证据

### 1. Python 环境 — OK

- `py --version` / `python --version` = Python 3.14.5（`C:\Users\admin\AppData\Local\Python\pythoncore-3.14-64\python.exe`）
- 冒烟：`py -m pytest tests/test_coord_transform.py tests/test_export.py -q` → **19 passed**（0.2s）
- requirements.txt 全量满足（此前补齐 altair 6.2.1 / tqdm 4.68.2 / ijson 3.5.1 / watchfiles 1.2.0）

### 2. Playwright 浏览器 — OK

- `py -m playwright --version` = 1.60.0
- 浏览器缓存：chromium-1223 + chromium_headless_shell-1223（`%LOCALAPPDATA%\ms-playwright`）
- chromium headless 实际 launch 验证通过；`tests/browser/lib/emc_helpers` import OK——B3 飞轮等浏览器用例前提齐备

### 3. API Key — OK（WARN：可选多模态 Key 缺失）

- `.env` DEEPSEEK_API_KEY 已配（len=35）；`api.main` 启动注入 os.environ 验证通过（serve 起的后端可读到，跑测试必需项满足）
- **WARN**：IFLYTEK_API_KEY / VOLCENGINE_API_KEY / ARK_API_KEY 未配 → 多模态/OCR 类用例不可承接（B3 不需要）

### 4. trace 工具 — OK

- `py tools/trace_query.py --stats` 可跑：当前 `.trace/trace.log` 共 616,826 行，MOD_AIQA.F_002 / F_003 / F_005 计数可查（F_001 按纪律不作 while-loop 判据）
- 控制台中文乱码仅为 codepage 显示问题，功能不受影响
- B3 等跑测试可带 `EMOTION_TRACE_SESSION=<组>-<批>`，报告可附 `trace_query --stats --session <批号>` 证据

### 5. 端口隔离 — OK

- serve.py 支持 `--backend-port`（默认 8000·`frontend/serve.py:127-128` 注释 + `:526-529` 参数解析）；start.bat 存在
- 当前 8080/8000 已被 claude组 serve 占用（netstat 实测）→ 三组并发跑 B3 必用 `--port/--backend-port` 隔离 + `sys.executable`（= pythoncore-3.14-64）

### 6. 平台 Harness（Codex 侧）— WARN（1 项）

- `.codex/hooks.json`：仅注册 PreToolUse（on_pre_edit_lint.py）+ PostToolUse（on_post_edit.py）；**SessionStart `[HOOK]` 未接 Codex 侧**（on_session_start.py 存在，但仅 `.claude/settings.json` 注册了 Claude 侧）→ 影响仅会话启动自动环境检查，不影响测试执行
- MCP：repo `.codex/config.toml` 已配 playwright（npx @playwright/mcp）+ vision-bridge（`.claude/mcp_servers/vision_bridge_server.py` 存在）；用户级 zai / web-reader / web-search-prime / zread 已配；npx 11.17.0 可用；playwright MCP 首次拉起需下载包，未实测启动

### 7. CB 机制 — OK（无歧义）

- 身份：第三方评估（Codex）——只读本地、不 git pull/push、git 由 claude组 负责；SCAN/响应落 `docs/catch-ball/discuss/` + `scan/`，由 claude组 push
- 已掌握：先验后推 · 并集采纳（任何发现如实上报）· trace 取证纪律 · 承重红线（追踪编号连续 / diagnose prompt 永不动 / 四态出口契约 / L0 购买·sim 非风险 / EMC 委托 Toolbox / aggregate 别名静默零）· 七轴评分
- 已读 KNOWLEDGE §7.4 新规：claude组 拆解测试任务、三组并行、分发前确认各组环境

---

## WARN 汇总（不阻塞）

| # | 项 | 影响 |
|---|----|------|
| 1 | SessionStart hook 未接 Codex 侧 | 仅影响会话启动自动环境检查（[HOOK] 打印），测试执行不受影响 |
| 2 | IFLYTEK / VOLCENGINE / ARK Key 未配 | 多模态/OCR 类用例盲区，B3 不受影响 |

---

## 可承接 / 不可承接

- **可承接**：B3 飞轮（浏览器 + LLM）· pytest 全量 · trace 取证（trace_query --stats / --session）· 静态核验 · e2e-seam 直测
- **不可承接**：需讯飞/火山密钥的多模态/OCR 类用例；MCP 视觉（vision-bridge）配置就绪但未实测

---

## 待命

自检完成，等 claude组 发测试任务分配（任务拆解 + 我组负责部分 + session 标签）；收到后按 `EMOTION_TRACE_SESSION=<组>-<批>` 执行并附 trace 证据。
