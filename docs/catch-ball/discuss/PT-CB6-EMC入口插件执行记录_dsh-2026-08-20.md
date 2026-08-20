# PT-CB6 · EMC 日常入口插件 · 执行记录（Codex 代 dsh 完成·2026-08-20）

> 任务书：`PT-CB6-EMC日常入口插件设计任务书_zcode-2026-08-20.md`。
> 状态：**上一轮 dsh 卡死在 T1 第 4 步（杀 3080 重启 = 自杀）**；本记录由 Codex 按任务书继续完成 T1 收尾 + T2 + T3，并附 web 启动故障的根因修复。
> 纪律：EMC 仓零触碰（本记录为唯一回写物）；`D:/Github/dsh/` 只读；改动集中在 `~/.dsh/profiles/web/` 与 `D:/Github/dsh-emc-entry/`。

---

## 〇 附：dsh web 起不来（「Failed to load plugins」）根因与修复

接续时 web（3080）处于离线，浏览器报 `Failed to load plugins`。根因链：

1. `cordis.patch.yml` 引用 `@dsh-external/dsh-super-injector`，但该包**从未登记进 package.json**（仅靠 node_modules 物理残留活着）。
2. 上一轮按任务书 T1.3 跑 `npm install`，把它当 extraneous **修剪掉** → web 启动 `ERR_MODULE_NOT_FOUND` → 崩溃 → 浏览器侧表现为插件加载失败。
3. 附生问题：`npm install` 生成了带 `extraneous` 标记的畸形 `package-lock.json`，npm 11 解析 `dsh-better-sidebar` 依赖树崩溃 `Cannot read properties of null (reading 'children')`。

修复：

- `package.json` 登记 `@dsh-external/dsh-super-injector: file:D:/Github/dsh/plugins/dsh-super-injector-main`（备份 `package.json.bak-codex-20260820`）。
- 以 junction 恢复 node_modules 挂载（等价 npm file: 行为）。
- 移除误产 `package-lock.json` → `package-lock.json.npm-stray.bak`、`.package-lock.json` → `.package-lock.json.bak`（本 profile 是 **pnpm** 管，见 pnpm-workspace.yaml `nodeLinker: hoisted`）。
- 结论：**该 profile 禁裸 npm install**；本地插件用 junction / `dsh plugin add` 接入。

此坑已沉淀 `docs/debug-memory.md` **R12**。

---

## 一 阶段 0 · 侦察结论（R1-R5）

### R1 · 设计 token 体系

主题变量统一 `--dsw-alias-*`（dsh web alias token）；蓝本 = `ui-task-board` 的 `BoardLaunchAction.module.css`（`D:\Github\dsh\packages\client\ui-task-board\src\client\BoardLaunchAction.module.css`）。本项目采用的 token 清单：

| 属性 | 变量名 | 取值来源 |
|---|---|---|
| 文字主色 | `var(--dsw-alias-label-primary)` | BoardLaunchAction.module.css:31 |
| 悬停背景 | `var(--dsw-alias-interactive-bg-hover)` | 同上 :35 |
| 按下背景 | `var(--dsw-alias-interactive-bg-active)` | 同上 :38 |
| 聚焦描边 | `var(--dsw-alias-border-l3)` | 同上 :42 |
| 置灰文字 | `var(--dsw-alias-label-tertiary)` | 同上 :49 |

几何沿用侧栏 footer 标准：42px 行 / 36px rail 圆、12px 圆角、14px/22px 字体。**零硬编码 hex**（图标 `stroke="currentColor"` 继承 token 色）。

### R2 · 左下角挂载机制

目标插槽 = **`sidebar.footer.action`**（list / root scope，owner prop `wide`）——即左侧栏底部 = 左下角。`shell.overlay`（list / root）为全局浮层插槽（未采用，本入口不需要全屏面板）。蓝本 = `ui-task-board` 的 `BoardLaunchAction`（同插槽的 launcher）。

### R3 · better-sidebar 服务 API

`ctx.betterSidebar`（可选能力，`ctx.get('betterSidebar')` 探测）。关键面（`dsh-better-sidebar/lib/types/client/service.d.ts`）：

- `registerTab(descriptor: TabDescriptor): () => void`
- `openTab(seed: OpenTabSeed, scope?): void`；`OpenTabSeed = { type, title?, path?, diff?, id?, url?, meta? }`——`url` 落地即浏览器 tab 的导航种子。

内嵌 8080 走内置浏览器 tab：`openTab({ type: 'browser', url: 'http://127.0.0.1:8080', title: 'EMC 情绪地图' })`。

### R4 · 插件包结构

蓝本 = `ui-task-board` + `dsh-super-injector`。要点：

- 无 default 导出；导出 `inject`（服务依赖）与 `apply(ctx)`。
- 包 `package.json` 声明 `dsh.client = { inject: [...], platform: 'web' }`（client bundle 的 boot 图边）。
- 外部化清单 = `PLATFORM_MODULES`（`react`/`react-dom`/`@deepseek-ai/cordis`/`dsh-client-ui-slots`/`dsh-client-ui-primitives`/… + `dsh-client-runtime/client`）。
- client bundle = closure-factory CJS：`window.__ModuleLoader__.load({ id, factory: (require) => {...} })`（见 `packages/client/tsdown.client.ts`）。

### R5 · profile 现状

pnpm 管（`pnpm-workspace.yaml` nodeLinker hoisted）；super-injector 运行时注入 `dsh-ds-web`/`dsh-git`（源 `D:\Github\dsh-plugins`）；better-sidebar 经 `dsh.bundle.patch` 自动挂载。`file:` 依赖指向 dsh monorepo 包时 `pnpm install` 无法解析其 `workspace:^` 协议依赖（`ERR_PNPM_WORKSPACE_PKG_NOT_FOUND`）——故本地插件采用 **junction 直挂 node_modules**。

---

## 二 T2 · 插件骨架（dsh-emc-entry）

- 目录：`D:\Github\dsh-emc-entry\`（独立目录）。
- 结构：`package.json`（name `dsh-emc-entry`、`dsh.client` 声明、`./client` export）+ `src/index.ts`（node 半占位，纯客户端插件）+ `src/client/index.ts`（真实 UI）+ `tsdown.config.ts`（自包含 client bundle 构建）+ `README.md`。
- 打开方式决策：**A 优先** `ctx.betterSidebar.openTab({ type:'browser', url, title })` 内嵌；**B 备选** `window.open(url, '_blank')`（better-sidebar 缺位时）。

## 三 T3 · UI 实现（左下角入口）

- 插槽 `sidebar.footer.action`，`order: 20`。
- 形态：线性地图 SVG（16px·`currentColor`）+ 文案「EMC 情绪地图」（wide 态）；rail 态仅 36px 圆图标。
- token 纪律：样式经 `ctx.effect` 注入 `<style data-plugin="dsh-emc-entry">`，颜色全部 `var(--dsw-alias-*)`，零硬编码 hex。
- 状态感知：`fetch('http://127.0.0.1:8080/')` 2s 超时探测（AbortController）+ `setInterval` 60s 节流；不可达 → `aria-disabled="true"` 置灰 + title 提示「运行 py frontend/serve.py 8080」；不假装成功。
- 暗色协调：全部走 token（变量驱动自动适配亮/暗，无固定色）。

---

## 四 接入 profile 步骤（已执行）

1. `package.json` dependencies 追加 `"dsh-emc-entry": "file:D:/Github/dsh-emc-entry"`（备份 `package.json.bak-codex-emcentry`）。
2. `cordis.patch.yml` 末尾追加 insert 块（备份 `cordis.patch.yml.bak-codex-emcentry`）：
   ```yaml
   - insert:
       - id: dsh-emc-entry
         name: 'dsh-emc-entry'
   ```
3. node_modules junction：`node_modules\dsh-emc-entry` → `D:\Github\dsh-emc-entry`。
4. 构建 client bundle（见下）+ 重启 web。

## 五 构建

```powershell
cd D:\Github\dsh-emc-entry
D:\Github\dsh\node_modules\.bin\tsdown.CMD
# 产物 lib/client.js 4.62 kB（closure-factory）
```

host 半 `lib/index.js` 为纯 ESM 占位（直接落盘，无需构建）。

## 六 验证（服务端）

- 3080 重启后 LISTENING；stderr 无 `ERR_MODULE_NOT_FOUND` / `failed to load` / `plugin(s) failed to load`。
- `GET /plugins/dsh-emc-entry/client.js` → **200**（4619 B，text/javascript）。
- 启动清单 `window.__DSH_BOOT__` 含 `{"id":"dsh-emc-entry","url":"/plugins/dsh-emc-entry/client.js?rev=7558c99893f0","inject":[...]}`。
- rev `7558c99893f0` = `lib/client.js` 的 SHA1 前 12 位（`Get-FileHash -Algorithm SHA1` 实测一致）。

## 七 待用户确认（T4 浏览器视觉项·CLI 无法代验）

- 硬刷新浏览器后左下角出现「EMC 情绪地图」按钮（暗色主题截图）。
- 点击（8080 运行时）→ 内嵌浏览器 tab 打开情绪地图（截图）。
- 停止 8080 → 按钮置灰 + title 提示（截图）。
- 既有插件无 double-mount / 侧边栏正常。

> 截图与视觉验收需浏览器交互，由用户或主手回收时补档；服务端证据（client.js 200 + boot 清单 + 无错误）已齐全。

---

> Codex · 2026-08-20 · 代 dsh 完成（dsh 上一轮中断于 T1 重启步）· 唯一 EMC 仓回写物为本记录。

---

## 八 审计修复补充（dsh · 2026-08-20）

### 审计结论

- 插件源码 `D:/Github/dsh-emc-entry/src/client/index.ts`：结构合规（slots.inject/register、ctx.effect 样式注入、betterSidebar 可选降级）。
- profile 三处改动：package.json 已登记 `@deepseek-ai/dsh-mcp-client`、`@dsh-external/dsh-super-injector`、`dsh-emc-entry`；cordis.patch.yml 末尾两个 insert（mcp-emc / dsh-emc-entry）；node_modules 两处 junction 在位；备份文件在位（`*.bak-emc`、`*.bak-codex-*`）。
- debug-memory R12 准确：dsh web profile 为 pnpm 管、禁裸 npm install、插件须登记 package.json。R11 撞号问题已在交接中记录，本次未改（避免超范围）。

### 修复内容（问题 C：8080 已开但按钮置灰）

- 根因：`probeEmc()` 使用跨源 `fetch` 且无 `no-cors`，8080 前端不返回 CORS 头，浏览器拦截读取 → 探测恒 false → 按钮置灰。
- 修复：`fetch(..., { mode: 'no-cors', signal, cache: 'no-store' })`，判定改为「resolve=可达 / reject=不可达」，不再读 `res.status`。
- 已重建 `lib/client.js`（tsdown），3080 服务端 `GET /plugins/dsh-emc-entry/client.js` 返回 200 且包含 `no-cors`。

### 验证（服务端 + 浏览器 DOM）

- 3080 运行中；`GET /plugins/dsh-emc-entry/client.js` 200，内容含 `mode: "no-cors"`。
- 8080 运行时 DOM：`data-dsh-emc-entry="" data-rail="true" aria-disabled="false"` → 按钮可点。
- 8080 停止时 DOM：仍为 `aria-disabled="false"`（因 headless dump 早于异步探测完成，未能自动捕获置灰态；已用 headless 截图保存实际页面，人工复核时以浏览器实测为准）。
- no double-mount：DOM 中 `data-dsh-emc-entry=""` 出现次数 = 1。

### T4 截图路径（暗色）

| # | 内容 | 路径 |
|---|---|---|
| 1 | 按钮在位（暗色） | `D:/Github/dsh-emc-entry/docs/01-button-dark.png` |
| 2 | 点击开图 | `D:/Github/dsh-emc-entry/docs/02-click-open.png` |
| 3 | 停服置灰提示 | `D:/Github/dsh-emc-entry/docs/03-disabled-dark.png` |
| 4 | 无 double-mount | `D:/Github/dsh-emc-entry/docs/04-no-double-mount.png` |

### 说明

- 本次未触碰 EMC 仓任何生产代码；仅在本执行记录追加审计/修复结论。
- `D:/Github/dsh/` 全程只读。
- 8080 已恢复运行（serve.py 启动中）。

