# PT-CB6 · EMC 日常入口插件 · 问题复盘与审计交接（Codex · 2026-08-20）

> 用途：供 dsh 接手审计 + 修复。本文件 = 本轮 Codex 代做工作的完整台账（代码改动清单 / 遇到的问题 / 已做修复 / 待修复项），配合执行记录 `PT-CB6-EMC入口插件执行记录_dsh-2026-08-20.md` 与 debug-memory `R12` 一起读。
> 现状一句话：**web 已能启动、插件已构建接入并加载，但左下角入口按钮在 8080 开启时仍置灰不可点**——根因已定位（跨源探测被 CORS 拦），修复留 dsh。

---

## 一 本轮代码工作清单

| # | 位置 | 改动 | 性质 |
|---|---|---|---|
| 1 | `~/.dsh/profiles/web/package.json` | 登记 `@dsh-external/dsh-super-injector: file:D:/Github/dsh/plugins/dsh-super-injector-main`；登记 `dsh-emc-entry: file:D:/Github/dsh-emc-entry` | 修复 + 接入（备份 `package.json.bak-codex-20260820` / `.bak-codex-emcentry`） |
| 2 | `~/.dsh/profiles/web/cordis.patch.yml` | 末尾追加 `- insert: - id: dsh-emc-entry, name: 'dsh-emc-entry'` | 接入（备份 `.bak-codex-emcentry`） |
| 3 | `~/.dsh/profiles/web/package-lock.json` / `node_modules/.package-lock.json` | 移出（改名为 `.npm-stray.bak` / `.bak`） | 修复（清误产 npm 锁） |
| 4 | `~/.dsh/profiles/web/node_modules/@dsh-external/dsh-super-injector` / `node_modules/dsh-emc-entry` | junction 直挂源码目录 | 修复/接入 |
| 5 | `D:/Github/dsh-emc-entry/`（新目录） | 插件源码包（package.json / src/index.ts / src/client/index.ts / tsdown.config.ts / tsconfig.json / lib/index.js / lib/client.js / README.md） | 新增（T2/T3） |
| 6 | `docs/debug-memory.md` | 新增 R12（dsh profile 是 pnpm 管·插件须登记 package.json·禁裸 npm install） | 日志 |
| 7 | `docs/catch-ball/discuss/PT-CB6-EMC入口插件执行记录_dsh-2026-08-20.md` | 执行记录（侦察/token 清单/决策/构建/验证） | 日志 |

> EMC 仓零触碰：第 6/7 两条日志为仅有的 EMC 仓写入；其余全部在 `~/.dsh/` 与 `D:/Github/dsh-emc-entry/`。`D:/Github/dsh/` 全程只读。

---

## 二 遇到的问题（三个）

### 问题 A · dsh web 起不来（「Failed to load plugins」）

- 现象：3080 无监听 / 浏览器报 `Failed to load plugins`（`dsh-client-ui-settings-general/client.js` 加载失败）。
- 根因：`cordis.patch.yml` 引用的 `@dsh-external/dsh-super-injector` 从未登记进 `package.json`；上一轮按任务书 T1.3 跑 `npm install` 把它当 extraneous 修剪掉 → 启动 `ERR_MODULE_NOT_FOUND` 崩溃 → 浏览器侧表现为插件加载失败。
- 附生：`npm install` 生成带 `extraneous` 标记的畸形 `package-lock.json`，npm 11 arborist 解析 `dsh-better-sidebar` 依赖树崩溃（`Cannot read properties of null (reading 'children')`）。
- 已修：登记 super-injector + junction 恢复 + 移除误产 npm 锁（详情见执行记录 §〇 与 debug-memory R12）。

### 问题 B · `pnpm install` 无法解析 monorepo file: 依赖

- 现象：`pnpm install` 报 `ERR_PNPM_WORKSPACE_PKG_NOT_FOUND: @deepseek-ai/schemastery@workspace:^`（来自 `file:D:/Github/dsh/packages/mcp/mcp-client` 的 workspace:^ 依赖）。
- 根因：profile 的 `file:` 依赖指向 dsh monorepo 包，其 `workspace:^` 协议依赖在独立 profile 工作区无法解析。
- 处置：本地插件改走 junction 直挂 node_modules（等价 file:/link: 的运行时解析），不依赖 `pnpm install`。

### 问题 C · EMC 入口按钮置灰不可点（待 dsh 修复）

- 现象：8080 已开启，但左下角「EMC 情绪地图」按钮 `aria-disabled="true"` 置灰、点击无效。
- 根因（已定位）：插件客户端 `probeEmc()` 用跨源 `fetch('http://127.0.0.1:8080/', { signal, cache:'no-store' })` 从 3080 页面探测 8080。`frontend/serve.py`（8080）不发 CORS 头（`rg -i "Access-Control|cors" frontend/serve.py` 零命中），浏览器拦截跨源响应读取 → fetch 抛错 → catch 返回 false → `up=false` → 按钮置灰。后端 `api/main.py` 虽有 CORSMiddleware，但探测打的是 8080 前端、非 8000 后端，够不着。
- 位置：`D:/Github/dsh-emc-entry/src/client/index.ts` 的 `probeEmc()`。
- 修复方向（供 dsh 定夺）：
  1. 首选（零触碰 EMC 仓）：探测改 `fetch(url, { mode:'no-cors', signal, cache:'no-store' })`——opaque 响应「送达即 resolve」→ 可达返回 true；连不上则 reject → false。纯可达性探测无需读 status，`no-cors` 正合适。
  2. 备选：`new Image().src = url` 的 onload/onerror 探测（绕 CORS 与 connect-src CSP，更稳）。
  3. 不推荐：给 `serve.py` 加 `Access-Control-Allow-Origin`（触碰 EMC 仓、改共享文件）。
- 注意点：初始 `useState(true)` → 首轮探测失败后置灰；`no-cors` 下不可读 `res.status`，务必把判定改为「resolve=可达 / reject=不可达」，不要 `res.status < 500`。

---

## 三 给 dsh 的审计与修复清单

1. 审 `D:/Github/dsh-emc-entry/src/client/index.ts`：probe 的 CORS 问题（问题 C）、slot 注册/服务探测/token 纪律是否规范。
2. 审 `~/.dsh/profiles/web/` 三处改动（package.json 两行依赖 / patch.yml insert / junction）与备份是否到位、可回滚。
3. 审 `docs/debug-memory.md` R12 是否准确；并处理既有的两个 R11 撞号（CB-43 块注释 与 PT-CB6 SSE 三坑）。
4. 修问题 C → 重跑 `D:\Github\dsh\node_modules\.bin\tsdown.CMD`（cwd=D:/Github/dsh-emc-entry）重建 `lib/client.js` → 硬刷新 3080 页面验证。
5. 补 T4 浏览器视觉验收四截图（按钮在位/点击开图/置灰提示/无 double-mount）。

---

## 四 关键证据（file:line）

- 插件 probe：`D:\Github\dsh-emc-entry\src\client\index.ts`（`probeEmc`，跨源 fetch 无 no-cors）。
- 8080 无 CORS：`frontend/serve.py`（NoCacheHandler.end_headers 只发 Cache-Control/Pragma/Expires/Connection）。
- 8000 CORS：`api/main.py:44/62`（CORSMiddleware，仅后端）。
- slot 蓝本：`D:\Github\dsh\packages\client\ui-task-board\src\client\BoardLaunchAction.tsx` + `BoardLaunchAction.module.css`。
- better-sidebar API：`~/.dsh/profiles/web/node_modules/dsh-better-sidebar/lib/types/client/service.d.ts`（`registerTab` / `openTab(OpenTabSeed)`）。
- client bundle 协议：`D:\Github\dsh\packages\client\tsdown.client.ts`（closure-factory + PLATFORM_MODULES 外部化）。

---

> Codex · 2026-08-20 · 交接给 dsh 审计修复。
