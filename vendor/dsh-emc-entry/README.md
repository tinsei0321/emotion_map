# dsh-emc-entry（v2 · 模型当向导）

EMC 情绪地图的 dsh web 入口插件（PT-CB8 · 临时测试件 · 最小实现）。

> 定位声明：入口按钮 = 临时测试件（为高效推进 EMC×dsh 测试）；终态 dsh 以
> 底层 MCP 消费 EMC、不显化前端。能用就好，不引入新依赖。

## 行为（v2）

点击 web 左下角（`sidebar.footer.action`）「EMC 情绪地图」按钮后：

1. **新建对话 + 固定文本注入**：以用户身份经 `IConversation.send()` 发送固定
   流程文本（对话服务唯一正规接口——无伪造 assistant 消息的 API，模型回应即
   真实助手消息）。模型轮询 `emc_status` 工具当向导：工具活动 = 实时进度，
   预热中提示含预计时长，就绪后简短欢迎（可引 kb_facts 身份卡）。
2. **并行探测 8080**：`/emc-ready` 三态（ready/starting/down，fetch 2s 超时，
   不阻塞 UI）。down → `host.openPath('D:/Github/emotion_map/start_silent.vbs')`
   静默拉起；starting → 勿重复启动，直接进入轮询。
3. **就绪弹浏览器**：自身并行轮询 `/emc-ready`（2s 间隔），就绪 →
   `host.openPath(emc-open.html)` 弹**系统默认浏览器**并 0s 跳转 8080。
   禁内嵌 tab 自动开（预热期乱码教训）。（office 机实测 `Invoke-Item` 对 URL
   静默无效，故经本地 .html 文件关联跳转；home 机 T15 直开 URL 实证过。）
4. **进行中态**：点击至就绪按钮置灰/转圈（防重复开多对话）；就绪或 90s 超时
   恢复。超时不另弹错——对话流自然呈现模型侧的未就绪说明（失败诚实态）。

### v1 → v2 移除项

- 点击直接开内嵌 tab（better-sidebar）；
- `/emc/launch` host 路由与 cmd spawn（全部改走 `host.openPath` 正规通道）；
- 60s 节流探测、置灰态（改为进行中态）；
- 空白会话静态欢迎卡（模型真实回应取代伪造欢迎）。

## 设计 token（验收 5：视觉与 v1 一致，零硬编码）

颜色零硬编码 hex，全部引用 dsh 主题变量（`--dsw-alias-*`）：

| 属性 | 变量 |
|---|---|
| 文字色 | `var(--dsw-alias-label-primary)` |
| 悬停背景 | `var(--dsw-alias-interactive-bg-hover)` |
| 按下背景 | `var(--dsw-alias-interactive-bg-active)` |
| 聚焦描边 | `var(--dsw-alias-border-l3)` |
| 进行中置灰 | `var(--dsw-alias-label-tertiary)` |

图标为内联线性 SVG（`stroke="currentColor"`），转圈动画只用 transform。

## 安装到 profile（本地 link）

1. `~/.dsh/profiles/web/package.json` dependencies 含：
   `"dsh-emc-entry": "file:D:/Github/dsh-emc-entry"`
2. `~/.dsh/profiles/web/cordis.patch.yml` 含：
   ```yaml
   - insert:
       - id: dsh-emc-entry
         name: 'dsh-emc-entry'
   ```
3. `cd ~/.dsh/profiles/web && pnpm install`
4. 构建后同步 node_modules 副本（pnpm file: 非 symlink）并硬刷新浏览器。

## 构建

node 半（`lib/index.js`）为最小空插件，直接落盘。client 半用 dsh checkout 的
tsdown 打包成 closure-factory CJS：

```powershell
cd D:\Github\dsh-emc-entry
node D:\Github\dsh\node_modules\tsdown\dist\cli.mjs
```

产物 `lib/client.js`（`window.__ModuleLoader__.load({ id: 'dsh-emc-entry', factory })`）。
构建后需把 `lib/*.js` 同步到 `~/.dsh/profiles/web/node_modules/dsh-emc-entry/lib/`
（或重跑 pnpm install），再硬刷新浏览器。

## 侦察依据

- 插槽：`sidebar.footer.action`（list/root，owner prop `wide`），蓝本=ui-task-board。
- 对话：`sessions.scope(id).get('conversation').send(text)`（ui-conversation
  apply.ts 的 scopedConversation 同款模式；scope-addressed 经 cordis tracker）。
- 新建对话：`workspaces.connectWorkspace(wid)`（复用/新建 blank 会话）→
  `sessions.open(sid)`。
- 打开路径/URL：`workspaces.openPath(path)` → `host.openPath`（Windows 走
  `Invoke-Item`，URL 弹默认浏览器——home T15 实证）。
- 就绪探针：EMC `frontend/serve.py` 的 `/emc-ready`（带 CORS `*`，真就绪才 200）。
- 向导工具：EMC `tools/mcp_server_emc.py` 的 `emc_status`（第 10 工具·F_032）。
