# 全局调试记忆（Debug Memory）

> **多组共享的踩坑规则库**（claude组 / zcode组 / dsh组 / Codex 通用·CB-41 首建 2026-08-18）。
> 修复中踩过的坑 → 蒸馏为可执行规则。**新会话排查前读一遍；修复提交前对照 R1/R2/R8 自查；CB 评估引用规则编号（如 debug-memory R2）。**
> 姊妹载体：按轮流水 = `catch-ball/cb-journal.md`；按 bug 台账 = `tests/buglog/`；本文件 = **按规则蒸馏**（互补不重复）。
> 维护：每次「修了 N 轮才好 / 修好又出新症状」的复盘，新规则追加于此（编号 R+ 连续）+ `docs/context-map.md` 已登记。

---

## R1 · 多入口工具必须逐入口验证

- **规则**：同一功能有多个入口（UI dialog / ForAI / 不同后端路由）时，验证必须**逐入口**跑一遍——函数直调正确 ≠ 所有路由正确。路由间的参数默认值与数据构建方式就是行为分叉点。
- **案例**：CB-41 B014——`aggregate_by_polygons` 直调与 `/geo/zonal_stats`（硬编码 `polygon_name_col='name'`）都正确，但 grid「指定单元」走的 `/spatial/aggregate`（`name_col=null` 自动推断 + `from_features` 构建）踩坑，2296 点静默只剩 600。
- **违反后果**：排查期宣告「根因已验证」，用户复测立刻翻车（本轮实际发生）。
- **检查动作**：交付修复前列出该功能的**全部入口清单**，每个入口一行验证结果；说不清入口清单 = 没验证完。

## R2 · 列值匹配必须显式处理空值——静默丢数据是重罪

- **规则**：任何「按某列的值匹配/过滤」的逻辑，必须先回答「该列为空（NaN/''）的行怎么办」：回退、报错、或显式标记丢弃，**禁止隐式丢弃**。空值 = 无信息 ≠ 负信息。
- **案例**：CB-41 B014——异构属性 GeoJSON（600/2296 要素带 `社区` 列）读入后联合成列、74% NaN，`isin` 过滤把空值行整行丢掉。`geopandas.from_features` 与 `read_file` 都会联合异构键——**GeoJSON features 属性不齐是常态不是异常**。
- **违反后果**：计数类错误无声缩小（2296→600），下游所有统计/渲染/结论全错且无报错。
- **检查动作**：写 `df[df.col.isin(...)]` / `filter(col == x)` 前后各加一行数量对账（in_n vs out_n·铁律「数据管道步骤记录 in_n/out_n」的调试版）；聚合结果总数 ≠ 输入总数时必须能解释每一行的去向。

## R3 · 地图显示错误按「数据 → 映射 → 渲染」三层排查；症状迁移 ≠ 修错方向

- **规则**：看到错误的地图表现，先判层再动手：① 数据层（计数/数值对不对——拿权威基准对账）② 映射层（数值→颜色/高度的字段与色带语义对不对）③ 渲染层（表达式/图层/进程对不对）。**上层修复会显影下层 bug**——新症状出现先问「这是同层新错，还是下层老错第一次被看见」。
- **案例**：CB-41——B013 修复（零点=不填色）让「计数为零」第一次以「中央无填充」显影，真正根因是更深的 B014（后端丢点）。若此时回头改渲染，就修反了。
- **违反后果**：在渲染层空转，反复「修复-复测-新症状」循环（用户经历的三轮）。
- **检查动作**：任何显示 bug，第一步给可疑要素做**数值对账**（真实点数 vs 显示值 vs 权威基准）；数据对了再动映射/渲染。

## R4 · 着色驱动字段必须匹配数据语义——禁静默降级

- **规则**：聚合结果的 choropleth 颜色由某个字段驱动，该字段的**语义必须与数据轨匹配**（点数轨=顺序色带·越多越深；极性轨=发散色带）。数据轨没有的字段（如无极性层的 polarity_index）**不得静默兜底**（0.5/近似值），必须显式分叉并让用户可见可选。
- **案例**：CB-41 B013——无极性体检点走情绪热度色带 grid-warm（高值=浅金）+ 零点落最深红，方向与「点越多越深」正相反；toolbox 入口更静默全员 0.5 同色。CB-23 曾加 reverse 开关但默认不反转——修了开关没修语义，反复发作。
- **违反后果**：颜色传达与事实相反的结论（密集区看着最轻），比不显示更糟。
- **检查动作**：新增数据轨（量化/体检/无极性）时，审计**所有**消费该数据的渲染路径（grid-zonal / toolbox-zonal / 3D / 时间轴 / rank），每条路径回答「无该字段时走什么语义」。

## R5 · bbox 中心 ≠ 空间归属点

- **规则**：需要「这个要素属于哪个区/社区」时，归属点禁用几何 bbox 中心——弓形/L 形/沿河要素的中心常落在邻居或水域。归属依据优先级：要素自身属性 > 用户交互位置（鼠标 lngLat）> 真质心，bbox 中心仅作展示定位用。
- **案例**：CB-41 B012——tip 社区行用要素 bbox 中心对 174 面做首命中包含测试，34/174 社区显示错名（建设→港务、朝阳路→石板、五龙↔梅子溪互串）。
- **违反后果**：悬停信息与表格/属性不一致，「张冠李戴」型信任损伤。
- **检查动作**：代码里出现 `bbox 中心`/`(min+max)/2` 参与点面判断时，自问「弓形要素会不会落外面」；全量复算错配清单（见 R9）而不是抽几组看看。

## R6 · 纸面推演穷尽后，trace + 端口是第一实证源

- **规则**：代码走查推不出结论时，先取证再猜：`py tools/trace_query.py --id MOD_* --tail N --raw`（enter/exit 时长能区分冷/热路径与真实调用次数）、`netstat -ano`（端口→PID 对照「哪个进程在服务」）。比问用户快，比盲改安全。
- **案例**：CB-41 B014 定位——trace 显示用户 5 次聚合调用（首跑 4s=冷加载·后 4 次 90ms=热路径），netstat 显示 8000 端口被用户旧后端占用（我的 serve 绑不上口）——用户操作轨迹与进程拓扑一次还原。
- **违反后果**：在错误前提上堆叠假设（本轮曾出现 5+ 个纸面假设全部落空）。
- **检查动作**：排查卡壳 >30 分钟且全是推断时，强制切换到 trace/netstat/日志取证路径。

## R7 · 旧进程载旧码——「修了还错」先问进程重启了吗

- **规则**：用户环境里长跑的前端/后端进程不包含新修复。交付修复后的验收口径**必须包含「重启服务」**，并给出核实手段（netstat 查端口 PID · 进程启动时间 vs 修复 commit 时间）。
- **案例**：CB-41 B014——修复提交后用户后端（PID 21192·8000 端口）仍是旧码；不重启复测永远「没修好」。
- **变体案例（PT-CB2 T3b·2026-08-19）**：「前端新+后端旧」假象——旧后端占 8000（新服务绑定失败 [Errno 10048] 半启动），前端 8080 静态文件读磁盘新文件（页面 build 号=新 commit）但后端跑内存旧代码 → 守卫「消失」。**页面 build 号新 ≠ 后端是新代码**（静态文件与内存代码不同源）；起验证服务前先 netstat 清端口；验证后端行为必须核对进程启动时间 vs 代码提交时间。
- **违反后果**：正确的修复被误判为无效，引发对根因的二次怀疑和多余改动。
- **检查动作**：验收指引里写明「Ctrl+C 重启 + 强刷浏览器」；远程协助时先查端口进程启动时间。

## R8 · 验证测试忌与被验实现同构

- **规则**：验证脚本若与被验代码走同一条构建/解析路径，会产生「假阳性验证」（错在一起就对在一起）。必须包含至少一条**独立基准路径**（不同 IO 层、不同库、或离线直算）。
- **案例**：CB-41 排查期——复算用 `gpd.read_file` + 函数直调（正确），而真实前端走 HTTP `from_features`（错误）——两条构建路径对同一文件的列集合都不同（异构属性联合行为一致但触发条件不同），漏验即此因。
- **违反后果**：带着「已验证」的自信交付未验证的修复。
- **检查动作**：验证计划里标注每条验证路径的「层次」（函数/路由 HTTP/浏览器 E2E），同层重复的算一条。

## R9 · 复算落到单元粒度——全量清单 > 抽样样本

- **规则**：数据归属/映射类 bug 的复算要落到**每个单元**（每社区/每格），产出全量错配清单；抽样几组既低估规模又看不出机制规律。
- **案例**：CB-41 B012——全量复算得 34/174 精确清单，且发现错配对「全部相邻或沿河」——这一规律直接指向 bbox 中心机制；此前 B012 台账只记五组样本，两轮没修透。
- **违反后果**：根因定位停在表象（「某些社区错了」），修复不彻底。
- **检查动作**：复算脚本输出逐单元对比表 + 汇总数；错配单元找共性（相邻？同形状？同数据源？）。

## R10 · 同族 bug 反复发作者的根因是「修症状层没修语义层」

- **规则**：一个 bug 修了 N 次仍复发，几乎总是因为每次修的是不同入口的症状，而错误**语义**（错的方向/错的身份假设/错的默认值）共用一根主干。修完必须反问：「还有哪些入口/模式/字段组合走同一个错误语义？」一次把语义层修对，症状层各入口自然收敛。
- **案例**：CB-41 全程——着色方向（B013·三轮）、tip 归属（B012·三次实测）、丢点（B014·自 CB-23 引入）——每个都是「入口 × 错误语义」的乘积；只有语义层修对（点数轨独立着色/mouse 归属/空值回退）才断根。
- **违反后果**：bug 打地鼠，用户信任流失（「修复过数次没能彻底解决」）。
- **检查动作**：buglog 里 `repro_count ≥ 2` 的条目，复盘时强制画「入口 × 语义」矩阵，找出那根主干。

---

## R11 · 块注释内禁止出现 `*/` 字样——前缀通配写法会提前闭合注释

- **规则**：块注释（`/** ... */`）体内不得出现 `*/` 字样——写「lyr-*/emotion-*」这类前缀列举时，`lyr-*/` 中的 `*/` 会**提前终止注释**，其后文字变成裸代码 → 整文件 SyntaxError → 模块图连坐 → 应用白屏不启动。需要列举前缀时写「lyr- 或 emotion- 前缀」或改用行注释（`//` 不受影响）。
- **案例**：CB-43 底图淡化罩层（08-18）——`/** 幂等敷罩层：锚在首个数据层（lyr-*/emotion-*）之前… */` 一行炸掉 map.js，应用无法启动；浏览器端表现为静态 HTML 在、dock/地图全无、a11y 树停滞 420 字符。
- **违反后果**：整页白屏级故障，且错误极隐蔽——`node --check file.js`（Script 解析目标）**检不出来**，看着「语法已过」实则是雷。
- **检查动作**：改完 ES module 必须 `cp x.js /tmp/x.mjs && node --check /tmp/x.mjs`（强制 ESM 解析目标）或直接起浏览器验 `window.__map`；grep 新增块注释中 `\*/` 出现两次以上的行。**「静态 HTML 在但应用没起来」= 优先怀疑模块图 SyntaxError**。

## R11 · 渲染投递通道三坑——SSE 长连接 × 单线程服务器 × 重放不去重（PT-CB6 S6·2026-08-20）

- **规则**：① SSE 长连接**不得挂在单线程 HTTP 服务器**上（一个 EventSource 占死唯一工作线程→静态页能开但 API 全 502——serve.py 必须 ThreadingTCPServer+daemon_threads）；② SSE 断线重连会**重放 backlog**，客户端必须按业务键（spec_id）会话级去重，否则"增删图层循环跳动"；③ 投递收件箱（render_inbox）是**运行时垃圾场**——测试产物会积压并在下次连 SSE 时全部重放，演示前清空/移走。
- **案例**：PT-CB6 S6 用户复测——页面转圈（单线程阻塞）→修后 8~9 图层循环跳动（无去重重放）→修后仍重放 15 个历史 spec（inbox 积压）。三坑连环，一次暴露。
- **违反后果**：演示现场"地图抽风"；且三坑症状互相掩盖（第一坑不修，二三坑根本看不到）。
- **检查动作**：演示前跑一遍无头采样（图层数恒定）；新投递通道设计时三问（服务器线程模型？重连重放去重键？inbox 清理责任方？）。
- **附带两条语义坑**（同轮记录）：zonal_stats 默认按极性指数排序**不是件数**——"最密集"类问题需显式 point_count 口径（D1 缺陷）；大图层 dataset_id 引用在浏览器连接池会排队超时，关键演示图层优先内联 GeoJSON（≤60 要素）。

## R12 · dsh web profile 是 pnpm 管——插件必须登记进 package.json，禁裸 npm install（PT-CB6 EMC 入口插件·2026-08-20）

- **规则**：
  - dsh 的 `~/.dsh/profiles/web/` 用 **pnpm**（`pnpm-workspace.yaml`·`nodeLinker: hoisted`），安装走 `dsh plugin --profile web add <tgz>`，**不是 `npm install`**。
  - 任何被 `cordis.patch.yml` 引用的插件（尤其 `@dsh-external/dsh-super-injector` 这类 `file:`/`link:` 本地插件）**必须同时登记进 package.json 的 dependencies**，否则 `npm/pnpm install` 会把它当 extraneous 修剪掉 → web 启动 `ERR_MODULE_NOT_FOUND` → 浏览器端只剩一句「Failed to load plugins」。
  - super-injector 运行时注入的插件（dsh-ds-web / dsh-git 等，源在 `D:/Github/dsh-plugins`）**不在** patch.yml/package.json，靠注入器重启自愈，勿手动登记。
  - 勿在 pnpm profile 上跑 `npm install`：会生成带 `extraneous` 标记的畸形 `package-lock.json`，npm 11 arborist 解析 `dsh-better-sidebar` 依赖树时崩 `Cannot read properties of null (reading 'children')`。
- **案例**：PT-CB6 EMC 入口插件 T1——任务书写的 `npm install` 把未登记的 super-injector junction 修剪掉，3080 起即崩；浏览器只见「Failed to load plugins」（client.js 拉取失败）。修复 = 把 super-injector 登记回 package.json（file: 源路径）+ junction 恢复 + 移除误产 npm package-lock.json。
- **违反后果**：dsh web 全站打不开（3080 崩溃），但错误藏在隐藏窗口（`dsh-web.vbs` 无日志），浏览器只给模糊的插件加载失败——极易误判成「前端缓存/插件坏」。
- **检查动作**：
  - web 起不来先 `netstat -ano | findstr :3080` 看有无 LISTENING；无则手工跑 `node --import tsx/esm apps/cli/src/bin.ts web`（cwd=`D:\Github\dsh`）抓 stderr 的 `ERR_MODULE_NOT_FOUND` 定位是哪个包缺失。
  - 对照 `cordis.patch.yml` 每个插件 id 与 package.json dependencies 是否一一登记；`npm ls --depth=0` 看 extraneous 项（未登记会被修剪的雷）。

## 附：本库首建背景（CB-41 · 2026-08-18）

用户经历三轮修复仍未根治（着色浅→着色反→无填充），zcode 接手后经「发起→dsh 排查→收敛→实施→用户复测暴露 B014→增补修复」闭环。三个台账：B012（tip 归属）/ B013（着色语义）/ B014（membership 静默丢点）·完整链条见 `docs/catch-ball/discuss/CB41-*` 三件套 + revision-log 5.257-5.260。

## R13 · dsh rc.8 三约束——仓外插件构建需登记 stub · client 模块必须导出 inject · merge 后必须 build:web（PT-CB6 home 续点·2026-08-20）

- **规则**：
  - **① 仓外插件构建需登记 stub**：rc.8 构建链（`packages/client/tsdown.client.ts` 的 `workspaceManifest`）要求插件名出现在 `packages/*/*/package.json` 清单中，否则 tsdown 报 `no packages/*/*/package.json declares the name <id>`（两层 glob，`packages/<组>/<包>/package.json`）。仓外插件（如 `D:/Github/dsh-emc-entry/`）解法：在 dsh 仓建纯登记 stub（仅 package.json 声明 name + `dsh.client`，加 `tsdown.config.ts` 内容 `export default { entry: '' }` 跳过 workspace 构建）。
  - **② client 插件模块必须导出 `inject`**：cordis 客户端插件的服务依赖声明 = 模块导出 `export const inject = ['slots','sessions','workspaces',...]`（蓝本 `packages/client/ui-task-board/src/client/index.ts:60`）。缺失时 `apply()` 内首次触碰 ctx 服务即抛"服务未声明"，**客户端启动树整体崩溃 → 整页黑屏**。node 半也必须导出 `apply`（空壳可），否则 loader 报 `invalid plugin, expect function or object with an "apply" method`。
  - **③ dsh merge 上游后必须跑 build:web**：`apps/web/dist/` 的 `/assets/index-*.js` 是前端应用本体（vite 构建产物，gitignored）。merge 后只跑 `build:lib:*` 会导致前端仍是旧版本构建，与 rc.8 新插件 bundle 版本错配 → 启动崩溃黑屏。标准动作：merge → `pnpm install` → `npm run build:lib:host` + `build:lib:client` + `build:web` → 重启 web。
- **案例**：2026-08-20 home 续点——dsh merge rc.8 后重建 dsh-emc-entry 插件，web 重启"成功"但页面黑屏：根因 A = 插件缺 `export const inject`（客户端树崩溃）；根因 B = 未跑 build:web（前端 assets 08-18 旧构建 vs rc.8 新 bundle）。修 = 补 inject + build:web，浏览器 DOM 快照确认完整渲染。
- **违反后果**：web 服务端 200、插件 bundle 200、页面 DOM 却是黑的——服务端证据全绿 ≠ 页面正常，极易误判为"前端缓存问题"。
- **检查动作**：
  - 仓外插件 tsdown 报清单错误 → 查 `packages/*/*/` 两层 glob 是否覆盖该包名；
  - dsh web 页面黑屏/白屏 → 先查插件模块有无 `export const inject`；再对照 `apps/web/dist/assets/` 文件时间戳与 merge 时间（gitignored，git 状态看不到，必须看 mtime）；
  - 服务端验证绿 ≠ 浏览器验证绿：客户端插件改动必须过浏览器 DOM 快照（IAB/headless）才算交付。

## R14 · dsh-better-sidebar 会拦截 `ctx.workspaces.openPath`——插件想开终端/外部浏览器必须直连 host RPC（PT-CB6 home 定稿修复·2026-08-20）

- **规则**：
  - **dsh-better-sidebar（≥0.12，config `interceptOpenPath: true` 默认开）在 client 侧 monkey-patch `ctx.workspaces.openPath`**：聊天文件链接改在侧边栏打开（fs.read → 文档标签），不再走系统默认应用。任何插件经 `ctx.workspaces.openPath` 打开 .bat/URL 都会被改道：
    - `.bat/.cmd` → 当文档在侧边栏打开（editor chunk 还可能加载失败），**不执行 → 独立终端永远不弹**；
    - `http(s)://` URL → 被 `resolveWorkspacePath` 当 workspace-relative 拼成 `<cwd>/http:\localhost:8080\...` → `fs.read` ENOENT 400，**外部浏览器永不打开**。
  - **解法：直连 host RPC 绕过 client patch**：`fetch('/api/host.openPath', { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ type:'client-request', rpcId: crypto.randomUUID(), method:'host.openPath', payload:{ path } }) })`——原生 `openNativePath`（Windows `Invoke-Item`，.bat 会弹 cmd 窗口执行）。URL 因 `Invoke-Item` 不认 URL，插件侧用用户手势内同步 `window.open('about:blank')` + 就绪后 `popup.location.href` 兜底（await 后再 open 会被弹窗拦截）。
  - **启动探测状态必须自愈**：探测驱动置灰（`aria-disabled`）若由 60s tick 独占，启动窗口期探测失败后按钮会滞留禁用（切会话也不恢复，模块级 store）。修 = 按钮仅"启动中"禁用（防重入）；`waitForEmc` 成功/失败都回写探测结果；`launch` 的 `finally` 里立即重探。
  - **start.bat 重启 8080 含 RAG 预热（20-30s）**：`waitForEmc` 超时不能 10s，须 ≥40s，否则"点击→开图"在冷启动时必失败。
  - **8080 未跑时按钮不应禁用点击**：任务书语义是"点击即启动 8080"，置灰只做视觉提示（`data-probe-up`），不可点状态只属于"启动中"防重入。
- **案例**：2026-08-20 定稿修复——用户报 ①点击后新会话跳标准模式（实测=host 默认 settings 的 router-standard，未复现）②点击一次后按钮禁用不恢复 ③终端不弹。根因链：better-sidebar 拦截 openPath → .bat 当文档开（不执行）+ URL 相对路径 ENOENT；探测状态无自愈 → 按钮滞留禁用；`waitForEmc` 10s < RAG 预热。修 = 插件直连 `host.openPath`（终端）+ `window.open` 手势段开图 + launching 状态机 + 40s 探测，浏览器实测冷启动全链路通过。
- **违反后果**：服务端 200、按钮在位、点击无感（console 静默 catch）——"点击了但什么都没发生"类问题，先查 console 的 `fs.read 400` 与底部侧边栏是否把 .bat/URL 当文档开了标签。
- **检查动作**：
  - 点 EMC 按钮后底部面板出现 `start.bat`/`index.html` 文档标签 → openPath 被 better-sidebar 拦截，改直连 `/api/host.openPath`；
  - 按钮点击一次后置灰不恢复 → 检查探测结果是否在 `waitForEmc`/`finally` 回写；
  - 冷启动点开链路失败 → 检查 `waitForEmc` 超时是否覆盖 RAG 预热（≥40s）。

## R15 · dsh web 必须从真实控制台窗口启动——无控制台环境会触发 node-pty AttachConsole 崩溃（PT-CB6 home 续点·2026-08-20 晚）

- **规则**：dsh web（3080）的终端功能依赖 node-pty；**在无控制台环境（后台任务/沙箱/隐藏窗口）启动 web 时，node-pty 的 `conpty_console_list_agent` 子进程执行 `AttachConsole` 会失败 → 整个 web 进程崩溃退出（exit 127，日志以 `Error: AttachConsole failed` 收尾）**。因此 dsh web 必须从真实控制台窗口启动（桌面快捷方式 / `cmd /c start` 可见窗口），勿从无控制台的后台/沙箱环境起服务。同理，插件宿主 spawn 任何外部程序必须挂 error 兜底（沿用交接卡原建议）。
- **案例**：2026-08-20 晚——zcode 后台任务起的 web 实例（`node --import tsx/esm apps/cli/src/bin.ts web --no-open`，无控制台）运行约 2 小时后崩于此错，3080 下线；用户/Codex 从常规窗口起的实例不受影响。
- **违反后果**：web 服务"无预警死亡"——崩溃前服务端一切正常，故障只在终端功能被触发时爆发，且 exit 127 极易被误读为"命令未找到"。
- **检查动作**：3080 突然无 LISTENING → 查 web 进程日志尾部是否有 `AttachConsole failed`；确认启动方式的控制台归属（后台/沙箱起的实例一律换真实窗口重启）。
