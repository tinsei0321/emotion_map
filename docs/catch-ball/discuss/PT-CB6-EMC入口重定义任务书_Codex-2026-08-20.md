# PT-CB6 · EMC 入口重定义任务书（Codex 设计 · dsh 执行 · 2026-08-20）

> 设计：Codex。执行：dsh。依据：用户对 EMC 入口按钮的新定义。
> 范围：把入口从「内嵌浏览器开 8080」改为「开新会话 + 欢迎卡 + 外部 Edge 启动 8080」，随后补 EMC 人设 + 身份卡。

---

## 〇 现状（执行前快速核对，无需改动）

- 插件源码：`D:/Github/dsh-emc-entry/`，client 入口 `src/client/index.ts`（当前挂 `sidebar.footer.action`，点击经 better-sidebar `openTab({type:'browser',url})` 内嵌开 8080——**本次要移除该内嵌行为**）。
- 启动脚本已存在：`D:\Github\emotion_map\start.bat`（杀旧 8080/8000 → `py frontend/serve.py 8080 --open=both`，用系统默认浏览器开 main+test 两页）。
- 现有执行记录：`docs/catch-ball/discuss/PT-CB6-EMC入口插件执行记录_dsh-2026-08-20.md`；复盘：`PT-CB6-EMC入口插件_问题复盘与审计交接_Codex-2026-08-20.md`。

---

## 一 需求规格（精确·按此验收）

### 需求 1 · 点击 = 开新会话 + 自动展开欢迎卡

点击左下角「EMC 情绪地图」按钮后（client 侧）：

1. **新建一个会话**（不是打开已有会话），agent 预设 = `standard`（默认预设）。
2. 该会话内**自动出现并展开**一张「欢迎卡」，文案（精确，含换行，中文）：

   > 你好，我是 EmotionMap Copilot
   > 用情绪地图看懂市民心声——问区域情绪、做空间分析、追原因与建议。

- 语义澄清：是「新建」，若系统已有空白会话可复用空白（与 dsh 原生「新建会话」按钮同语义）；欢迎卡默认展开、非折叠。

### 需求 2 · 启动 8080 + 外部 Edge 打开（不在 dsh 内嵌）

同一点击（host 侧，与需求 1 并发或紧接）：

1. 在**独立终端窗口**运行 `.\start.bat`（cwd=`D:\Github\emotion_map`）→ 杀旧进程并起 `py frontend/serve.py 8080`。
2. 8080 用**外部浏览器 Microsoft Edge**打开 `http://localhost:8080/frontend/index.html`；**绝不再走 dsh 内嵌浏览器**。
3. 去重：把 `start.bat` 的 `py frontend/serve.py 8080 --open=both` 改为 `--open=none`（EMC 仓 1 行改动，本需求授权），由插件宿主显式开 Edge——避免「默认浏览器再开两页」或「开错浏览器」。

---

## 二 实现接口（dsh 直接可用；仍须按「先查真实接口」纪律逐条核实）

### 客户端（client 半）

- **建会话**：`ctx.get('workspaces')?.connectWorkspace(workspaceId)`（内部走 `sessions.create`，预设由 host 默认赋 `standard`）。`workspaceId` 取「当前活动工作区」或首个工作区——先查 `workspaces` 服务真实方法（`packages/client/runtime/src/client/workspaces/service.ts` 已有 `connectWorkspace` 先例）。
- **欢迎卡**：先查会话空态/首屏的插槽再写代码。已知线索：
  - `conversation.view`（list / session scope）、`conversation.session.header`、`conversation.session.header.actions/utilities`（`packages/client/ui-conversation/src/client/contract/slots.ts`）。
  - 空会话首屏 hero 在 `EmptyHero.tsx`（当前是硬编码 chrome，未必有现成插槽）。
  - 若空态无合适插槽：优先找会话体内可加性插槽；仍无，用 `shell.overlay`（list / root）挂一张默认展开的欢迎卡，或用任务书 R2 备选「DOM 注入」。**最终插槽名以 `Slots.listSubTree` 查询结果为准，不得猜。**
- 欢迎卡形态：一张卡片（图标 + 标题「你好，我是 EmotionMap Copilot」+ 副文案），默认展开；token 纪律同前（颜色 `var(--dsw-alias-*)`，零硬编码 hex）。
- **不再使用** `betterSidebar`；移除现有 `openTab` 内嵌逻辑。

### 宿主（host 半，需从「纯占位」改为真实逻辑）

- 用 `harness.handle('emc.launch', handler)` 注册包私有方法；client 经 `host.call('emc.launch')` 触发（返回 `{ok:true}` 或错误）。
- handler 内两步：
  1. 独立终端跑 start.bat：`Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','start.bat' -WorkingDirectory 'D:\Github\emotion_map'`（不阻塞宿主，起完即返）。
  2. 外部 Edge 开地图：`Start-Process -FilePath 'msedge' -ArgumentList 'http://localhost:8080/frontend/index.html'`。
- 路径/URL 常量集中在 host 文件头（`EMC_ROOT`、`EMC_MAP_URL`），不用魔法字符串。
- host 半需补 `package.json` 的 `dsh.host` 能力声明（若有）与必要的 `node:child_process` 导入；以 cordis 宿主插件规范为准。

---

## 三 阶段二 · EMC 人设 + 身份卡

（欢迎卡文案已含「我是 EmotionMap Copilot」；人设=让 dsh 以此身份回答问题）

1. **身份卡**：在 `ai_qa/outlet_kb/urban_renewal_knowledge.py` 的 FACTS 数组加一张卡：`topic='identity'`（或复用 `project` 但 `name`/`detail` 写明身份），`detail`=欢迎卡同款介绍 + 能力（区域情绪/空间分析/原因建议），补 `source`/`year`/`keywords`。
2. **重建 RAG**：`py tools/rag_index.py --build`（索引当前 08-18 旧，需重建让 rag_query 能召回身份卡）。
3. **人设（system prompt）**：给 web profile 配一条系统提示，语义：「你是 EmotionMap Copilot（EMC 情绪地图助手）。自我介绍与知识类问题优先调 `kb_facts` / `rag_query` 检索 EMC 知识库，回答注明来源；数据/分析类问题优先用 `zonal_stats`/`rank` 等 EMC 工具，并遵守口径（174/154 等）」。落点先查 dsh 的 system prompt / agent preset 机制（profile `cordis.yml` 或 preset 文件），不在 patch.yml 里硬塞。

---

## 四 拆解步骤 + 逐项验收

| 步 | 内容 | 验收 |
|---|---|---|
| S1 | 只读侦察：查 `Slots.listSubTree`（欢迎卡插槽）、`Service.listService`（workspaces/sessions/harness 真实签名）、`Builtin.listBuiltins`（harness.handle 真身） | 记录插槽名/方法签名进执行记录 |
| S2 | host 半实现 `emc.launch`（跑 start.bat + 开 Edge），补 package.json 能力声明 | `host.call('emc.launch')` 能起 8080 并 Edge 开图 |
| S3 | client 半：点按钮 = 新建会话（standard）+ 展开欢迎卡 + 触发 `host.call('emc.launch')`；移除内嵌 openTab | 点击后：新会话出现、欢迎卡展开、终端弹 start.bat、Edge 开地图页 |
| S4 | 改 `start.bat`：`--open=both` → `--open=none`（1 行） | 起 8080 不再自动开系统默认浏览器，仅 Edge 开主页面 |
| S5 | 重建 client bundle：`D:\Github\dsh\node_modules\.bin\tsdown.CMD`（cwd=`D:/Github/dsh-emc-entry`） | `lib/client.js` 更新、`/plugins/dsh-emc-entry/client.js` 200 且 rev 变化 |
| S6 | 阶段二：加身份卡 + 重建 RAG + 配人设 | 问 dsh「你是谁」→ 以 EmotionMap Copilot 身份答并引知识库 |
| S7 | 截图留档 + 执行记录（复用现有执行记录或新开一条） | 四截图（新会话+欢迎卡 / 终端 start.bat / Edge 开图 / 人设问答） |

---

## 五 纪律与边界

- EMC 仓可写：`start.bat`（1 行）、`ai_qa/outlet_kb/urban_renewal_knowledge.py`（身份卡 1 条）、执行记录；**其余零触碰**。
- `D:/Github/dsh/` 只读（侦察）。
- 插件源码/构建只在 `D:/Github/dsh-emc-entry/`；profile 改动只在 `~/.dsh/profiles/web/`。
- 先查真实接口再写代码；零硬编码 hex（欢迎卡颜色走 `--dsw-alias-*`）；ASCII 标记；副作用带 disposer（`ctx.effect`）。
- 完成即停，等主手回收（附截图路径与审计结论）。

---

> Codex · 2026-08-20 · 设计签发。
