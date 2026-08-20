# PT-CB6 · EMC 日常入口插件 · 设计任务书（zcode 主手签发·2026-08-20）

> 签发：zcode（主手·只负责路径设计与要求）。执行：**dsh（UI 设计 + 代码实现 + 配置接入全部执行）**。
> 目标：①EMC 八工具接入用户日常 web 配置组 ②web UI 左下角新增「EMC 情绪地图」独立入口（插件形态·dsh 设计 token 把控）。
> 纪律总纲：**先查真实接口再写代码**（Cordis 插件开发纪律）；一切改动可回滚；EMC 仓库零触碰（8080 显示屏现成·本任务不需要 EMC 侧任何改动）。

---

## 一、背景与管线总览

```
[阶段0 侦察] → [T1 配置接入] → [T2 插件骨架] → [T3 UI 设计实现] → [T4 验收走查]
   (只读)        (可回滚增量)     (新目录零污染)    (token 纪律)      (行为级+视觉级)
```

**管线逻辑**：侦察先行（接口/token/挂载点三查）→ 配置接入先行（工具可用是入口存在的前提）→ 插件骨架（注册链路通）→ UI 精修（token 对齐）→ 双维验收。**每个 T 是一个决策门：过不了不进下一个，发现的偏差回任务书注释并落执行记录。**

## 二、阶段 0 · 侦察清单（只读·写代码前必做·结论落执行记录）

| # | 侦察项 | 位置/方法 | 要回答的问题 |
|---|---|---|---|
| R1 | dsh 设计 token 体系 | `D:/Github/dsh/apps/web/node_modules/@deepseek-ai/dsh-client-ui-primitives/`（src/README）+ web app 样式表 grep `:root`/`--` 变量 | **实际可用的 CSS 变量名清单**（颜色/圆角/间距/字号）——UI 实现的唯一样式来源 |
| R2 | 左下角挂载机制 | `@deepseek-ai/dsh-client-ui-slots/`（插槽系统 README+src） | 是否有现成左下角/状态栏插槽？有→用插槽（优先）；无→DOM 注入（参考 better-sidebar 的 client 注入方式） |
| R3 | better-sidebar 服务 API | `~/.dsh/profiles/web/node_modules/dsh-better-sidebar/docs/external-plugin-guide.md` + `ctx.betterSidebar.registerTab` | 能否注册「EMC 地图」tab 并内嵌 `http://127.0.0.1:8080`（README 明示 HTTP 默认侧边栏打开） |
| R4 | 插件开发规范 | `D:/Github/dsh/apps/cli/config/agent-presets/cordis/skills/cordis-plugin-development/SKILL.md` | 插件包结构/注册即 effect/撤销纪律 |
| R5 | 用户日常 profile 现状 | `~/.dsh/profiles/web/`（package.json/cordis.patch.yml 已通读） | patch.yml 有 double-mount 警告注记——insert 块追加到文件**末尾新段落**，不动既有条目 |

## 三、任务拆解

### T1 · 配置接入（EMC 工具进日常 web）

1. `~/.dsh/profiles/web/package.json` dependencies 追加：
   `"@deepseek-ai/dsh-mcp-client": "file:D:/Github/dsh/packages/mcp/mcp-client"`（**office 用 npm，禁 `link:` 协议**——EUNSUPPORTEDPROTOCOL 实证）；
2. `~/.dsh/profiles/web/cordis.patch.yml` **末尾**追加 insert 块（office 实证片段·emc-test 同款）：

```yaml
- insert:
    - id: mcp-emc
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: emc
        transport: stdio
        command: py
        args: ['D:/Github/emotion_map/tools/mcp_server_emc.py']
        cwd: 'D:/Github/emotion_map'
        toolCallTimeoutMs: 60000
        failOnStartupError: true
```

3. profile 目录 `npm install`；`node --import tsx/esm apps/cli/src/bin.ts --profile web --dump-config` 验证 `mcp-emc` 行在位（在 `D:/Github/dsh` 目录跑）；
4. 重启 web 服务：`netstat -ano | findstr :3080` 取 PID → `taskkill /PID <pid> /F` → 照 `~/.dsh/dsh-web.vbs` 的等价命令行重启（`node --import tsx/esm apps/cli/src/bin.ts web`·cwd=`D:\Github\dsh`·env 带 `DSH_CHECKOUT=D:\Github\dsh`）；
5. 验证：3080 重新监听 + 会话内问「列出 mcp__emc 开头工具」→ 8 工具。

**回滚**：删两处增量 + 重启。**风险预案**：`failOnStartupError: true` 若 EMC server 起不来会拖垮 web——首次重启后立即检查 3080，失败则临时改 `false` 并回执行记录登记。

### T2 · 插件骨架（新目录·零污染）

1. 插件名建议 `dsh-emc-entry`；开发目录建议 `D:/Github/dsh-emc-entry/`（独立目录，避免占用 profile 内空间；最终经 `file:` 依赖装入 web profile——与用户现有 vendor tgz 插件同模式）；
2. 包结构按 R4 规范（apply 声明/注册即 effect/可撤销）；MVP 功能链：**插件加载 → 服务注册 → 入口按钮渲染 → 点击 → 打开 EMC 地图**；
3. 打开方式优先级（依 R3 侦察定案，执行记录写明选择理由）：
   - **A 优先**：`ctx.betterSidebar.registerTab` 注册「EMC 地图」tab 内嵌 `http://127.0.0.1:8080`（better-sidebar 内嵌浏览器机制现成·用户已装）；
   - B 备选：无 better-sidebar 时 `window.open` 新窗口；
4. 装入 web profile：package.json 加 `file:D:/Github/dsh-emc-entry` 依赖 + patch.yml 末尾 insert 行（或 bundles 通道·依 R4 规范定）。

### T3 · UI 设计与实现（左下角入口·dsh 设计 token 纪律）

**位置**：web UI **左下角**（依 R2：有左下角/状态栏插槽用插槽；无则 DOM 注入到左下角既有容器，z-index 与现有浮层协调）。

**形态**：图标 + 文字「EMC 情绪地图」的小型入口按钮（悬停微反馈；不做大面板）。

**设计 token 纪律（硬要求）**：
1. **禁硬编码样式值**——颜色/圆角/边框/间距/字号全部引用 R1 侦察到的 dsh 既有 CSS 变量（执行记录附**所用 token 清单表**：`属性 → 变量名 → 取值来源文件`）；
2. 图标与现有 web UI 图标同风格（线性描边/尺寸档位对齐·可用内联 SVG）；
3. **暗色主题必须协调**（用户当前即暗色——按钮在暗色下截图走查）；变量驱动应自动适配亮色；
4. 文案中文为主（「EMC 情绪地图」/未启动提示文案）；有余力接 dsh 多语言机制（zh/en）。

**状态感知（做进 MVP）**：
- 8080 可达 → 按钮常态，点击开图；
- 8080 不可达 → 按钮**置灰**（或角标），点击弹提示「EMC 地图服务未启动——在 emotion_map 目录运行 `py frontend/serve.py 8080`」；探测用轻量请求（如 fetch 8080 根路径超时 2s·**不得阻塞主线程 UI**，后台节流探测 ≥60s 一次）。

### T4 · 验收（双维·全部留档入执行记录）

| # | 验收项 | 通过标准 |
|---|---|---|
| 1 | 工具接入 | 日常 web 会话列出 8 个 mcp__emc__ 工具 |
| 2 | 入口在位 | web 重启后左下角按钮存在（**截图**：暗色主题） |
| 3 | 点击行为 | 8080 运行时点击→EMC 地图可见（侧边栏 tab 或新窗口·**截图**） |
| 4 | 诚实降级 | 8080 停止时按钮置灰+提示（**截图**）；不假装成功 |
| 5 | token 走查 | 所用 token 清单表齐·零硬编码 hex（主手抽检） |
| 6 | 回滚演练 | 删增量后 web 恢复原状（说明即可·不必真删） |
| 7 | 既有功能 | 修改版插件（侧边栏等）全部正常·无 double-mount 报错 |

## 四、白名单与纪律

- **dsh 可写**：`~/.dsh/profiles/web/`（package.json/cordis.patch.yml/node_modules）、新插件目录 `D:/Github/dsh-emc-entry/`；
- **只读**：`D:/Github/dsh/`（侦察）、`D:/Github/emotion_map/`（零触碰零 commit）；
- 执行记录落盘 EMC 仓：`docs/catch-ball/discuss/PT-CB6-EMC入口插件执行记录_dsh-2026-08-20.md`（**唯一 EMC 仓写入物**·含 R1-R5 侦察结论/token 清单/决策理由/验收截图路径）；截图存插件目录 `docs/` 下并在记录中引用路径；
- EMC 仓 commit 由主手回收时做（dsh 不动 EMC 仓 git）；插件目录自建 git 可选；
- 改日常 profile 前先备份两个文件（`package.json.bak-emc` / `cordis.patch.yml.bak-emc`）。

## 五、给主手的回收钩子

回收时 zcode 将抽检：①dump-config 双插件行（mcp-emc + dsh-emc-entry）②token 清单零硬编码③四截图④回滚备份在位⑤8 工具+入口双通。产物并入 PT-CB6 收口件。
