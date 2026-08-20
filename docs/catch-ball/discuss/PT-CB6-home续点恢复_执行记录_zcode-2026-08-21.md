# PT-CB6 · home 续点恢复 · 执行记录（zcode · 2026-08-21）

> 性质：home 到岗续点执行记录——dsh 更新 rc.8 + "会话地图"删除 + EMC 入口插件重建恢复 + 黑屏修复 + Codex 配置修复。
> 送审件：本记录 + `PT-CB6-home续点恢复_送审通知_zcode-2026-08-21.md`（含转发 Codex 的审计 prompt）。
> 纪律：EMC 仓只写文档（本记录/送审/交接卡/debug-memory）；`D:/Github/dsh/` 改动 = merge rc.8 + 构建登记 stub（详见 §一）；插件源码在仓外 `D:/Github/dsh-emc-entry/`。

---

## 〇 任务来源

用户三条指令：① 把本地 dsh 更新至 deepseek-harness 最新版；② 永久删除"会话地图"插件；③ Home 环境到岗续点——恢复"EMC 入口功能"。执行中发现并修复 Codex config.toml 接入问题（上一轮遗留）与 web 黑屏问题（本轮引入）。

## 一 dsh 更新至上游 rc.8

- **基线**：`D:/Github/dsh` @ `99f6f02f`（上游 rc.7），本地 +14 提交（handover 机制/task-board/usage-monitor/web auto-session 修复），gitee origin（`tinsei0321/dsh_0816`）为唯一 remote。
- **动作**：`git remote add upstream https://github.com/deepseek-ai/deepseek-harness.git` → fetch → 测 `git merge --no-commit upstream/master`（536 提交 / 1604 文件）→ **仅 4 文件冲突**：
  1. `packages/api/remotes/package.json`——本地包（handover-board/task-board/usage-monitor）与上游包（file-reference/session-reference/credentials/goal 等）在 dependencies/peerDependencies/devDependencies **并列插入**，取并集；
  2. `packages/api/remotes/src/client/index.ts`——同型：imports / export type / `$mount` 装配列表三处并列合并；
  3. `packages/bundle/web-app/package.json`——dependencies 并列合并（含上游 `dsh-subprocess`/`open`）；
  4. `pnpm-lock.yaml`——取上游后全量重新生成（本地 workspace 包条目由 pnpm 补回）。
- **构建**：`pnpm install` 后 `npm run build:lib:host`（23s）与 `build:lib:client` 通过，上游新包 typert 产物补齐（`packages/context/session-reference/lib/typert.host.js` 等）。
- **提交**：`8258d567c4`（merge）+ `92ae8734ee`（lockfile 刷新）+ `ec5c5e725c`（登记 stub，见 §三）。备份分支 `backup-pre-rc8`。
- **未 push**：gitee origin ahead 539 / behind 1（远端有一个未拉提交，需 `git pull --rebase` 后 push）。

## 二 "会话地图"插件删除 = dsh-synapse

- **身份**：全盘搜索（.codex 插件缓存/AppData/dsh 生态）无"会话地图"命名的插件；用户指认后确认 = `dsh-synapse`（`github:liangmianya/dsh-synapse` 0.3.0，"A visual, non-linear conversation workspace plugin for DeepSeek Harness"）。
- **删除位置**（共 4 处，web profile 唯一引用）：
  1. `~/.dsh/profiles/web/package.json` dependencies 行 + `dsh.profile.bundles` 数组项（备份 `package.json.bak-rm-synapse`）；
  2. `~/.dsh/profiles/web/node_modules/dsh-synapse/`（目录删除）；
  3. `~/.dsh/synapse/`（数据目录 5.3MB workspaces.json，永久删除）；
  4. 验证：web 重启后页面预加载清单无 synapse、其他 profile 无引用。

## 三 EMC 入口插件重建（源码目录丢失后按任务书+复盘重建）

- **现场**：`D:/Github/dsh-emc-entry/` 不存在；web profile 的 package.json 登记、node_modules junction、cordis.patch.yml insert 全部消失（仅 super-injector 登记在）。任务书 `PT-CB6-EMC入口重定义任务书_Codex-2026-08-20.md` + 复盘 `PT-CB6-EMC入口插件_问题复盘与审计交接_Codex-2026-08-20.md` 为唯一依据。
- **重建实现**（rc.8 机制，`D:/Github/dsh-emc-entry/src/client/index.ts` + `components.tsx`）：
  - 左下角按钮挂 `sidebar.footer.action`（order 20，宽/窄双态，零硬编码 hex 走 `--dsw-alias-*`）；
  - 8080 探测保留复盘问题 C 的 `no-cors` 修复（resolve=可达/reject=不可达，不读 status，2s 超时 + 60s 节流）；
  - 点击 launch 链：`ctx.workspaces.startSession()` 新建/复用空白会话（preset 由 host 默认 standard）→ `ctx.sessions.open(sessionId)` → 欢迎卡 `setWelcomeShown(true)`（挂 `conversation.input.dock`，composer 上方，默认展开可关闭，文案与任务书逐字一致）→ `ctx.workspaces.openPath(D:/Github/emotion_map/start.bat)` 独立终端起 8080 → 轮询就绪后 `openPath(http://localhost:8080/frontend/index.html)` 外部浏览器（Edge）开图；
  - 不再走内嵌浏览器（任务书需求 2）；不直接 spawn 进程（R13 前车）。
- **rc.8 构建链两处硬约束**（新增经验，见 debug-memory R13）：
  1. 仓外插件名必须在 `packages/*/*/package.json` 清单注册——建纯登记 stub `D:/Github/dsh/packages/emc/emc-entry/package.json`（零代码 + `tsdown.config.ts` `entry:''` 跳过 workspace 构建，commit `ec5c5e725c`）；
  2. 插件 node 半必须导出 `apply`（空壳可），否则 loader 报 `invalid plugin, expect function or object with an "apply" method`。
- **接入**：web profile package.json 登记 `dsh-emc-entry: link:D:/Github/dsh-emc-entry` + bundles 数组（备份 `package.json.bak-emcentry`）；node_modules junction；插件包自建 `cordis.patch.yml` insert。
- **验证**：web 重启稳定，`GET /plugins/dsh-emc-entry/client.js` → HTTP 200（7639B，含 no-cors/startSession/欢迎卡文案）；页面 DOM 快照确认左下角按钮在位（8080 未开时 aria-disabled 置灰——探测逻辑正确）。

## 四 黑屏事件（根因双叠 + 修复）

用户复测报"页面黑屏"。排查：

1. **根因 A（我的插件）**：client 插件模块未导出 `export const inject = [...]` 服务依赖声明，`apply()` 内 `ctx.slots.inject` 触发 cordis 服务未声明异常 → 客户端启动树崩溃。对照蓝本 `packages/client/ui-task-board/src/client/index.ts:60`（`export const inject = ['slots', 'remote', ...]`）。修 = 补 `export const inject = ['slots', 'sessions', 'workspaces']`。
2. **根因 B（rc.8 合并后）**：前端 `/assets/index-*.js`（`apps/web/dist/`）为 08-18 旧构建（rc.7 时代），插件 bundle 全部为 rc.8 新构建 → 版本错配。修 = `npm run build:web`（3.3s，新 hash 落地）。
- **修复后验证**：重启 web → 浏览器实测页面完整渲染（DOM 快照：侧边栏/新建会话/任务看板/「EMC 情绪地图」按钮/选择模型全在位，非黑屏）。

## 五 Codex config.toml 修复（附带）

- 上一轮把 DeepSeek provider 误改为 `wire_api = "chat"`，新版 Codex 已移除 chat 支持（讨论 openai/codex#7782）。经查证 DeepSeek V4 官方 API 已原生提供 Responses 端点（2026-07-31 起），改回 `wire_api = "responses"`，实测 `POST https://api.deepseek.com/responses` HTTP 200。
- 修 `models.json`：两个 deepseek 模型的 `supports_search_tool` true → false（Codex 0.145.0 bug：该字段 true 会静默隐藏所有 MCP 工具）。
- 文件：`C:\Users\Hi\.codex\config.toml`（备份 `config.toml.bak-20260820`）、`models.json`。

## 六 验证清单

| # | 项 | 结果 |
|---|---|---|
| 1 | dsh merge 后 `build:lib:host` + `build:lib:client` + `build:web` | 全过 |
| 2 | web（3080）重启后稳定运行 | LISTENING 持续 |
| 3 | `GET /plugins/dsh-emc-entry/client.js` | 200 / 7639B / 含 no-cors+startSession |
| 4 | 页面渲染（浏览器 DOM 快照） | 完整 UI 非黑屏；EMC 按钮在位（8080 停时置灰） |
| 5 | 页面预加载清单 | 无 synapse；含 dsh-emc-entry |
| 6 | DeepSeek `/responses` 端点 | HTTP 200 |
| 7 | EMC 仓 pytest | 未跑（本轮零触碰生产代码，仅文档） |

## 七 遗留（浏览器验收待主手）

- 点击入口的完整链路（新会话+欢迎卡+终端 start.bat+Edge 开图）需 8080 运行时浏览器实测（T4 截图四项）。
- 欢迎卡"新会话自动出现"细节若未达标，改 `D:/Github/dsh-emc-entry/src/client/components.tsx` 重建。
- EMC 人设 system prompt 未配；身份卡后需 `py tools/rag_index.py --build`。
- debug-memory 两个 R11 撞号待合并；node-pty AttachConsole 坑待记。
- dsh 未 push（gitee behind 1）。

> zcode · 2026-08-21 · home 到岗续点完成，送审。
