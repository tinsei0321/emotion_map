# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-08-23 16:54（**收工·壳阶段开建+RAG 双支柱**·zcode 纯编排角色） | **同步**：分支 **`EMC_Codex_Harness`**（08-24 起·EMC×dsh 已合流 main 后旧分支删除）。
> **续点第一读**：本卡 §最新收工快照 → docs/catch-ball/用户复测滚动清单.md（T1-T7·明日验收全套）。
> **最后更新**：2026-08-24 凌晨 00:27（壳工程全链闭环+SHELL2(FIX) 终裁通过）

---

## 最新收工快照（08-23 深夜·壳二期完成）

### 里程碑：EMC 一个窗口·三个引擎·可切换
- **壳 S1-S9 全完成** + **BrainAdapter dsh 适配器跑通**（?engine=dsh 首次端到端七断言全绿）
- **知识管线 SOP 落盘**（三级审批+kb_inbox+事实级查重）
- 引擎三态：`?engine=light`（默认·轻量）| `?engine=dsh`（dsh headless）| `?engine=mock`（测试）
- F_041 注册（api 层首例·格式合规）
- 门禁 557 绿·RAG 96.7% 零退化

### 明日 office 按序
1. `git fsck --no-progress | head` 体检（R25·3 秒）
2. 环境配齐（requirements 注记 office 补装清单·含 jsonschema/playwright）
3. `python -m pytest tests/ -q` 全量基线确认
4. **T1-T7 验收测试**（~45 分钟·走 3080 + 8080 双窗口三引擎）
5. 测完→体检医生专题开门
> **续点第一读**：本卡 §最新收工快照 → 台账 R66/R67 → `docs/rag-baseline.md`。

---

## 最新收工快照（08-23 凌晨 · RAG 全流程日）

### 今日完成（一条主线+三条支线）

1. **RAG 重建全流程**（PT-CB9·当日闭环）：CB 讨论（业界评估→两回应→研判→v1.2 终版判决）→ P0（黄金集/基线/门禁）→ 泳道①②③（Kimi/Codex/Kimi·Qoder 审+主手双评价收敛）——**检索质量 83.3%→96.7%**（Q-B 95% 达标·名词类 100% 全对·门禁 515+4）。A1 前注试验诚实归档（净零不全量化）。
2. **架构裁定修正**：EMC=交互壳子+Harness+RAG·大脑永远外置；C 件取消·ACP v1=壳↔Harness 协议。
3. **多组能力档案**：Kimi A-（redemption 成立）/Qoder A（审计回归）。
4. 支线：PT-CB13 进度契约收口/discuss 归档机制回应+X-01 补录/debug-memory R20-R24。

### 续点队列（按序）

1. **PT-CB9 全量验收**：office 到岗双机基线复测（`py tools/rag_eval.py --snapshot` 同 HEAD 对比）+ 全量 60 题手动档 + 用户真实问题试问（rag_query 带 followup_cues 演示）→ 收官归档（泳道过程稿按「方案 a 合流后一次性」归卷五）。
2. PT-CB11 复测 T1-T5（暂缓中·窗口用户定）。
3. 下批候选：RAG 增量运营批（F-05 消费者/F-06 巡检/知识提交工作流运营）/M2-M3 环境配方/guard 挂账小件。
4. 观察项：冷启动首轮闪烁测试（再现抓名）/codex-main.zip 留档（Harness 选型参考）。

### 注意

- 环境差异：office 机 pytest 可能 515+4 vs home 517+2（pypinyin 可选依赖·Qoder F-04 已注记）。
- 归档机制已生效：查 CB 结论先 `discuss/_INDEX.md`；卷四（EMC×dsh）/卷五（RAG）在途保护不动。

---

## 收工快照（08-22 凌晨 · PT-CB11 P1 全件合入 · 上午 CB 收口）

### 今晚完成（五线交付）

1. **zcode**：B3-1/B3-2 注入灰框治本后端（0fb5d604·render_policy 单一权威源+value_field 双层校验+manifest renderFields）。
2. **Codex**：三件工具 grid_aggregate/compare_regions/hotspot_analysis F_033-F_035（3f9e55a4）——主手审计**通过**（57e7bffe·真身独立核实+真实链路复测）。
3. **Kimi 首批双件**：K1 前端四件 B3-3~B3-6（d9685861·图例/tip/面板/全零告警+render-contract §七第8条·**playwright 四口径自测过**）；K2 area_stats F_037（99521515·9 用例）。
4. **claude 独立审计**：报告落盘 `PT-CB11-P1审计_claude-2026-08-21.md`——A(zcode)通过 / B(Codex)**有条件通过**（条件=P2-2 空集边界语义化 5-8 行补丁）；P2-1 前缀通配张力+P3×5 不阻塞；**独立审计价值实证**（空集边界 Codex mock 与主手真链双侧都漏）。
5. **用户令固化**：人工测试=阶段统一安排（`docs/catch-ball/用户复测滚动清单.md`·T1-T4 入队·阶段 1 就绪）；派发=落盘+回复内一键复制 prompt 两处齐备（入长期记忆）。

### 门禁收工态

**457 passed + 7 failed（存量环境缺依赖 matplotlib/sentence_transformers·Ops 挂账待用户定）+ 5 skipped**。

### 上午任务队列（CB 收口·按序）

1. **Kimi 件正式回收**：四口径证据核验（_tmp 截图 4 张+脚本是否移 docs 留证）+9 用例抽验+「_gdf_rows 不含面积列→逐格 _jsonable」待裁决项裁定。
2. **claude 审计终裁**：P2-2 补丁派发（建议 Codex 5 分钟件或随 P2 批）+P2-1/P3×5 处置入档。
3. **阶段 1 统一测试指引发用户**（复测清单 T1-T4·一次起三服务全测）。
4. CB 正式件：cb-journal/_cb-index 更新。
5. **P2 批排期**：nearest/overlay/trend/report_assemble 四件（F_036/F_038-F_040）+guard 迁 server 侧+A-4 版本徽章+P2-2 顺修。

### 注意

- claude 审计报告与 Kimi 记录（WorkBuddy 格式化）随收工 commit 入库。
- `_tmp/` Kimi 自测截图 4 张+脚本未入库（上午裁决）。
- dsh_test 目录仍待重启电脑后手动删（遗留）。

---


## 最新收工快照（08-23 16:54 · 壳阶段开建 + RAG 双支柱 · zcode 纯编排）

### 今日完成（白话一句话版）
- **RAG 方向定了**：您的项目适合「混合检索+受治理的活知识库」——「聪明留给外脑·知识越养越厚」；当天八范式论文讨论收敛+您三特征独立验证同向。
- **平台愿景入宪**：情绪地图=「城市规划大模型平台」第一个垂域·下一个垂域候选「城市体检医生」（首场景=12345 全年变化时间轴演示·测通后开工）。
- **驾驶舱迁移（壳）开建**：换脑插座图纸+事件管道校验器+刀路侦察全部交付·工程进入实施。
- **git 事故已恢复**（gc 死锁）·教训 R25 入册·零丢失。
- **白话纪律机制化**：以后给您看的报告开头必有白话摘要段（医院比喻示范件已立）。

### 续点队列（按序）
1. **您的验收窗口**（T1-T5·30-45 分钟）——测完即「现行链路合格」→ 体检医生专题可开；
2. 壳工程：Qoder S4（轻引擎事件发射器）→ Kimi S3 主体（前端事件化）→ S5/S7；claude 短包（E2E 骨架+git 清理清单+requirements 注记）；
3. 知识写入管线（kb_inbox 三级审批 SOP）；
4. office 到岗：git fsck 体检（R25）·双机基线复测。

### 注意
- git 后台仍有 bad-tree 噪声（已禁 gc·不影响操作）·claude 清理清单在途；
- 仓外备份 D:/Github/_emc_rescue_backup_20260823/ 保留一周后可清；
- 白话纪律 3b：用户可见文档必带白话摘要段（AGENTS.md）。

## 会话交接快照（08-21 深夜）

- **战略转向完成**：dsh 归官方+MCP 优先（R61）·宪法条款入（六禁）·A-3 stdio 修复完（4c64a121）
- **重装+全链路验证已通过**（上一会话尾段）：官方 v0.1.1-rc.2 + HTTP MCP(8600) + 用户 PowerShell 实测 Top5 社区分析落图成功；图层残留根治（7fbe6547）·layer_output 体积控制（2bebb6bc）·start.bat 一键三服务（2451b3be）
- **新会话已接续（R63）**：PT-CB11 任务书已落盘 `discuss/PT-CB11-MCP工具丰富化与注入链路补全_任务书_zcode-2026-08-21.md`（B-3 根因实锤+6 修复件+8 工具设计 F_033-F_040+执行矩阵）——**待用户拍板三项**：①批次拆分 P1/P2 ②Kimi 首件=B-3 前端 ③P1 三件执行手
- **关键文件**：`discuss/会话交接_完整计划落盘_zcode-2026-08-21.md`（必读）· `discuss/备忘录_dsh纯净官方版纪律_2026-08-21.md`（宪法）· `discuss/PT-CB10-战略转向裁定_dsh归官方与MCP优先_zcode-2026-08-21.md`

---


## 收工快照（08-21 · PT-CB7 「稳定与灵魂」批 · Qoder 主执行 · 明晨 office 续点）

### 今日完成

1. **审计先行 + 拆解**：T1-T9 全文审计（M1-M4 修正随执行生效）；任务拆解（复杂自执/简单派 dsh 三批）落盘；WIP 复核（boundary_fill_v1 保留/R15 为 T3 资产·08-21 重编号）。
2. **EMC 仓六 commit**（基线 442 passed / 2 skipped·显式路径提交·禁 add -A）：
   - T1 `97fb95bd` [dsh] 图层叠层自清理；T6 `0d752150` MCP 描述紧凑化；T8 `9e7ca1dc` 800m 脚本参数化+口径对照段+inbox 自清；T5+T9 `c6013cf8` 身份卡扩写+RAG 364 条；T14 `1dc80123` 结果呈现契约§七；T10 `a8a697e5` 出图范式契约 render-contract.md。
   - 用户实测五连修：T18 `3d80d2cd` render_file 第 9 插座（“显示到地图”一步到位·治长思维+误入 Range）；T16 `8608ff14` 历史图层残留根治（applied/ 归档）；T19 `23888cb3` /emc-ready 真就绪端点+插件快通道/杀窗守卫（治“加载一半失效”）；T21 `691676ab` SSE 扇出广播+50s 豁免（治“F5 才见”）；T15 `fa661192` start_silent.vbs 隐藏启动+对话式首屏卡。
3. **dsh 两批回收**：批 1（T2 terminal chunk=lock 失配 0.14.0→pnpm install 收敛 0.12.3；T4 计时取证 headless 110s/4 步 vs web 61s/17 步；F1-F4 复核）；批 2（人设 prompt 落地生效——「你是谁」自述 EMC 身份实测通过；T17 timeout 120s **无效**——根因=MCP 冷启动 >120s，需服务端预热）。记录+截图在 `discuss/PT-CB7-dsh协助批{1,2}记录_dsh-2026-08-21.md`。
4. **仓外插件 dsh-emc-entry** 多轮改造已重建（bundle 18,977B·服务端验证在位）：真就绪 gate（/emc-ready 读真实 status+旧 serve 降级）+快通道（已就绪不杀不重启）+杀窗守卫+对话气泡首屏卡（欢迎+加载状态同卡）+内嵌 tab 降级可选。
5. **当前运行态**：8080/8000 新 serve 已起（/emc-ready 200+ACAO 实测）；dsh web 3080 人设生效；全量 442 passed。

### office 到岗续点（按序）

1. `git pull`（gitee）；**office dsh 环境四件套**（同 08-20 卡§⚠：mcp 依赖/RAG 重建/verify_keys/profile 重建）+ **批 2 同款补三件**：①人设改动按 `PT-CB7-dsh协助批2记录` A-2 复制（`.agent-presets/router-standard-subagent/{agent.cordis.yml,router-bootstrap-v1.mjs}` 的 persona/RL_PERSONA）；②emc-test 系 profile `toolCallTimeoutMs: 120000`；③`start_silent.vbs` 内绝对路径两机盘符一致（D:），无需改。
2. **优先验证（用户实测项）**：① EMC 按钮快通道（已就绪直接开图·无终端无半载）；② 冷启动气泡卡三态；③ 出图免 F5 实时铺层（多页同收）；④ render_file“显示到地图”一步成图；⑤ 「你是谁」身份自述。
3. **待办优先级**：T17 改服务端预热（MCP 冷启动 >120s 的真修·方案=server 启动即预载 geo/RAG，设计后派 dsh）→ T7 双模预设落地+≤2min 验收（批 3）→ zcode 回收验收+《Qoder 执行效果评估》。

### 待裁决/观察

- T11 register_dataset 独立插座已被 render_file 吸收（自动登记内置）——保留或销项待主手一句话。
- D2 欢迎卡绑定目标会话（全局可见）仍未做——气泡卡形态下观感是否可接受待用户反馈。
- render_file 临时 dataset（tmp_render_* 组）在 manifest 缓慢累积——同源复用已防重，定期清理列观察。
- 工作区带入了 dsh 测试任务产物（SCRIPT/gen_12345_bottom10_layer.py + bottom10 geojson×2 + manifest/素材表改动）——随收工提交一并入库（先例同 08-20）；_tmp/gen_12345_kde.py 为他人实验残留未动。
- debug-memory 撞号已清：双 R11 已合并（E2·08-21）；残留双 R12 已由 Codex 修正（R13-R16 顺号·08-21 避坑沉淀报告）。

### 📌 家机到岗补一件（zcode · 08-21 E3 部署令 D5）

- 用户级全局 `C:\Users\<用户>\.codex\AGENTS.md` →「## Harness 工作方式」列表末尾（第 5 条后）补第 6 条「调试资产化」——**补丁文本照抄 `discuss/PT-CB8-E3回收与全局部署派发_Codex-2026-08-21.md` 附录 A**（office 已写·两机对齐·一分钟手工活）。项目级规范（AGENTS/context-map/debug-memory R1-R19+维护协议）已随 `git pull` 自动生效。若用户偏好仅项目级，可一句话撤销此件。

---

## 到岗快照（08-20 · dsh rc.8 + 会话地图删除 + EMC 入口恢复 + 黑屏修复 + 送审）

### 今日完成（ZCode 代执行）

1. **dsh 更新至上游 rc.8**：`D:/Github/dsh` merge deepseek-ai/deepseek-harness upstream/master（536 提交，rc.8 发布）→ 本地 14 提交全保留（handover/task-board/usage-monitor/web auto-session fix）；4 冲突文件手工合并（remotes package.json/client/index.ts、web-app package.json、pnpm-lock 取上游后全量重生成）；commit `8258d567c4`（merge）+ `92ae8734ee`（lockfile 刷新）+ `ec5c5e725c`（构建登记 stub）；备份分支 `backup-pre-rc8`。**已跑全量 `build:lib:host` + `build:lib:client` + `build:web`**。⚠️ 未 push（gitee origin 有 1 个新提交未拉，下次顺手 `git pull --rebase` + push）。
2. **"会话地图"插件 = dsh-synapse 已永久删除**：web profile 的 package.json（dependencies + bundles）、node_modules/dsh-synapse、`~/.dsh/synapse/` 数据目录（5.3MB workspaces.json）全删；备份 `package.json.bak-rm-synapse`。已验证页面预加载清单无 synapse。
3. **EMC 入口插件完整重建**（源码目录 `D:/Github/dsh-emc-entry/` 丢失后按任务书+复盘重建）：
   - 新实现（rc.8 机制）：`workspaces.startSession()` 新建会话 + 欢迎卡挂 `conversation.input.dock`（默认展开，可关闭，文案逐字）+ `workspaces.openPath(start.bat)` 独立终端起 8080 + 8080 就绪后 `openPath` Edge 开图；probe 保留 `no-cors` 修复（resolve=可达/reject=不可达）；零硬编码 hex（`--dsw-alias-*`）；client 模块导出 `inject = ['slots','sessions','workspaces']`。
   - rc.8 构建链适配：**登记 stub `D:/Github/dsh/packages/emc/emc-entry/`**（纯 manifest + tsdown.config.ts `entry:''` 跳过，已 commit `ec5c5e725c`）+ 插件目录 node_modules junction → dsh/node_modules + node 半导出 `apply` 空壳。
   - 接入 web profile（dependencies link: + bundles + junction；备份 `package.json.bak-emcentry`）。
   - **验证通过**：web 重启后稳定运行，`GET /plugins/dsh-emc-entry/client.js` → **200**（7639B）；浏览器 DOM 快照确认左下角按钮在位（8080 停时置灰正确）。
4. **黑屏修复（双根因）**：根因 A = 插件缺 `export const inject` 服务声明（客户端启动树崩溃）；根因 B = merge 后未跑 `build:web`（前端 assets 08-18 旧构建 vs rc.8 新 bundle 版本错配）。修后浏览器实测页面完整渲染。坑记 debug-memory **R14**（08-21 重编号）。
5. **Codex 接入修复（附带）**：`config.toml` DeepSeek provider 改回 `wire_api = "responses"`（DeepSeek V4 原生支持 Responses API，实测 200）；`models.json` 两个模型的 `supports_search_tool` → false（防 Codex 0.145.0 MCP 工具静默隐藏 bug）。重启 Codex 客户端生效。
6. **落盘**：执行记录 + 送审通知（含转发 Codex 的审计 prompt）+ 本卡 + R14（08-21 重编号）+ session-handoff 节点，随 commit 推送。

### 待办（主手回收）

- **✅ 送审已完成**：双审计（Qoder+Codex）已核毕落盘 `discuss/PT-CB6-home续点恢复_审计_Codex-2026-08-21.md`（无 CRITICAL）；用户新发现 B1/B2/B3 已由 Codex 修复并浏览器实测；本文件为收工卡，详细状态以审计报告 §D 定稿待修清单为准。
- **T4 视觉验收**：B2/B3 已有等价浏览器实测证据，四截图待主手补档；剩余排期项 = D2 欢迎卡绑定目标会话 / EMC 人设 + RAG 重建 / start.bat banner（F8 需授权）。
- node-pty `AttachConsole failed` 坑已记 debug-memory **R16**（08-21 重编号·08-20 晚实测触发：无控制台启动的 web 实例被崩掉）。
- synapse 残留 M1 已闭环：pnpm-lock 已在定稿修复中修剪干净（08-20 23:37），pnpm-workspace.yaml allowBuilds 行 08-20 晚已删。
- dsh 未 push：`git pull --rebase` + push；收工时 `git push hub --all` 补推盘仓。

### 注意

- **rc.8 之后**：仓外插件构建必须走登记 stub（packages/emc/emc-entry）+ 独立 tsdown；client 插件必须导出 `inject`；merge 上游后必须 `build:web`；web profile 禁裸 npm install（R13·08-21 重编号）。
- dsh 相关文件在仓外（`D:/Github/dsh-emc-entry/` + `~/.dsh/profiles/web/`），不入本仓 git。
- **home 机 dsh 开机自启已取消**（08-23 用户指令）：删 HKCU Run `DSH Web UI`（guardian 看门狗）+ 移走启动文件夹 `DeepSeek Harness.lnk`（Edge 弹 3080 窗口）；备份在 `C:\Users\Hi\dsh-launcher\disabled-autostart-20260820\`（lnk + hkcu-run-backup.reg，导入 .reg + lnk 移回 Startup 可恢复）。**到岗后 3080 不会自动起**，需手动：`cd D:\Github\dsh && node --import tsx/esm apps/cli/src/bin.ts web`（真实控制台窗口，勿后台/沙箱起，R16）。
- debug-memory 撞号已清（E2 合并双 R11 + Codex 08-21 修残留双 R12·重编号 R13-R16·详见避坑沉淀报告）。

---

## 收工快照（08-20 晚 · EMC 入口插件 + 重定义 + dsh web 启动修复）

### 今日完成

1. **dsh web 启动修复**：`cordis.patch.yml` 引用的 `@dsh-external/dsh-super-injector` 未登记进 package.json，被上轮 `npm install` 当 extraneous 修剪 → web 崩「Failed to load plugins」。修 = 登记依赖 + junction 恢复 + 清误产 npm 锁；坑记 `docs/debug-memory.md` R13（08-21 重编号·dsh profile 是 pnpm 管·插件须登记 package.json·禁裸 npm install）。
2. **EMC 入口插件 dsh-emc-entry**：建包 `D:/Github/dsh-emc-entry/`（左下角 `sidebar.footer.action` 按钮 + 8080 探测 + 零硬编码 token 纪律）→ 构建 client bundle → 接入 web profile → 加载验证（`/plugins/dsh-emc-entry/client.js` 200 + boot 清单在位）。
3. **入口重定义任务书**（`discuss/PT-CB6-EMC入口重定义任务书_Codex-2026-08-20.md`）：点击入口 = 开新会话（standard）+ 欢迎卡 + host 跑 start.bat + 外部 Edge 开 8080；随后 EMC 人设 + 身份卡。
4. **spawn 崩溃修复**：dsh 实现 host 时 `spawn('msedge')` 报 ENOENT 且未挂 error 监听 → 带崩 web。修 = 改 `cmd /c start "" url`（默认浏览器=Edge）+ `safeSpawn` 挂 error 兜底（源码 `src/index.ts` 与产物 `lib/index.js` 都改了）。
5. dsh 已落地：身份卡（`urban_renewal_knowledge.py` 的 IDENTITY 卡）、`start.bat --open=none`、新 preset `checkup_12345_comm174_all`（manifest.json + geojson）、新工具 `tools/grid_export.py`。

### 待修「小问题」（home 到岗续点）

1. 用户反馈入口仍有小问题（欢迎卡展开 / 新会话行为细节未完全达标）——先复现再定位，改 `D:/Github/dsh-emc-entry/src/client/index.ts` + 重建 client bundle。
2. EMC 人设 system prompt 未确认是否已配（身份卡已加，但「你是谁」仍走 dsh 默认人设；需配 system prompt + `py tools/rag_index.py --build` 重建 RAG）。
3. node-pty `AttachConsole failed` 崩溃（隐藏窗口起服务时 dsh 用终端会崩）——已记 debug-memory R16（08-21 重编号·含插件宿主 spawn 外部程序 error 兜底建议）。
4. `tools/grid_export.py` 是「非正式工具 · F_029 待立项」，勿当正式插座。

### 注意

- 工作区混有 dsh 执行任务的改动（manifest.json + 12345_诉求_社区174全量.geojson + grid_export.py + urban_renewal_knowledge.py + start.bat），本次已一并提交；**main 冻结勿动，一切在 `EMC_harness_dsh`**。
- `docs/debug-memory.md` 有两个 R11 撞号（CB-43 块注释 与 PT-CB6 SSE 三坑），已新增 R12，撞号待主手合并。
- dsh 相关文件在仓外（`D:/Github/dsh-emc-entry/` + `~/.dsh/profiles/web/`），不入本仓 git。
- 相关日志：`discuss/PT-CB6-EMC入口插件执行记录_dsh-2026-08-20.md`、`discuss/PT-CB6-EMC入口插件_问题复盘与审计交接_Codex-2026-08-20.md`、`discuss/PT-CB6-EMC入口重定义任务书_Codex-2026-08-20.md`。

---

## home 收工快照（08-20 凌晨）

- **PT-CB6 S6 用户复测通过**：Q2 端到端成图，用户确认正常。
- **渲染通道三坑修复**：serve.py 单线程 SSE 阻塞 / render_client 缺 spec_id 去重 / render_inbox 旧 spec 积压重放。
- **去 office 续点**：读 `_handoff/OFFICE.md`；S7 回收判读，将三个显示面缺陷并入 PT-CB6 缺陷清单。
- 详细进度：`docs/todo.md` 2026-08-20 段 + `memories/repo/session-handoff.md` 当前节点。



## ⚠️ 插件入仓同步提醒（08-21 office 班·PT-CB8）

- **dsh-emc-entry 插件已迁入 EMC 仓** `vendor/dsh-emc-entry/`（office 版基线·含 v2 探索痕迹 docs/v2-os-desktop-check.png 等）；office 依赖已改指 `file:D:/Github/emotion_map/vendor/dsh-emc-entry` 并重启验证（dump-config 行在位）。
- **home 到家动作**（按序）：
  1. `git pull origin EMC_harness_dsh`（vendor 目录随之到位）；
  2. **权威版本合并决策**：home 本地 `D:/Github/dsh-emc-entry` 是 08-20 晚多轮改造版（bundle 18,977B vs office 基线 lib/client.js 5,554B）——**对比两份**：以改造版为准覆盖仓内 vendor 并 commit（一次性合并·之后仓为唯一权威），或确认 office 版已含改造后删本地目录；
  3. 改 home profile 依赖行 → `file:D:/Github/emotion_map/vendor/dsh-emc-entry`，pnpm/npm 重装，重启 web；
  4. office 原目录已改名 `dsh-emc-entry.local-backup-20260821`（保留 3 天供对比·确认后可删）。
- 口径：**插件改动今后只做一次**（改仓内 vendor→commit→两端 pull+重装）；~/.dsh 配置类仍走复刻清单模式。

## ⚠️ office 侧 dsh 问答测试准备（跨机四件套·zcode 补记 08-20）

**git pull 只带回仓库侧（八工具/渲染通道/数据/配置指引文档）——dsh 的 profile 配置在家机 `~/.dsh/profiles/emc-test/`，不在 git 里。office 要复测须补四件（约 10-15 分钟）：**

1. **python 依赖**：`pip install "mcp>=1.0.0,<2.0.0"`（office 环境未装此新依赖）；
2. **RAG 索引重建**：`py tools/rag_index.py --build`（索引不入 git·每环境必建）；
3. **.env 确认**：`py tools/verify_keys.py` 验 DeepSeek/AMAP key（office 历史应已有）；
4. **dsh profile 重建**：按 `docs/catch-ball/discuss/PT-CB6-dsh侧MCP配置指引_dsh-2026-08-20.md` 照做（语法全带 file:line 实证）。**前提注意**：指引依赖用 `link:D:/Github/dsh/packages/mcp/mcp-client`——要求 office 有 dsh 本地 checkout；**没有 checkout 的变体**：依赖改 npm registry 版（去 `link:` 前缀装正式包 `@deepseek-ai/dsh-mcp-client`），其余不变（到岗让 office 的 dsh 顺手在指引文档补此变体一节）。另确认 office 已装 npm 全局 dsh + 3080 端口占用情况。

**到岗顺序**：`git pull`（gitee 可达）→ `git push hub --all` 补推盘仓 → 四件准备 → 起 `py frontend/serve.py 8080` + 浏览器开页 → `dsh --profile emc-test` → 问「12345 热线诉求最密集的 10 个社区是哪些？把结果铺到地图上」看 8080 亮 `[dsh] [真实]` 图层。
**长期解**：在家跑「一键离开」会把 `~/.dsh` 快照进 hub 盘（六平台含 dsh）——以后 dsh 配置随盘走免手配；今晚收工记得跑。

## 旧：到岗快照（08-19 office 班收工·home 续接）

- **office 班完成**：①Codex 审计 B1 判 FAIL→七项修复完毕→**送复审**（prompt 在 `PT-CB2-送审通知_zcode-2026-08-19.md` §六·**待用户转发 Codex**）·门禁 389+3 ②dsh 两批六任务全销号·两条真发现（place_name 内嵌真实身份证→蒸馏强校验入 B4；qty 层两份物理拷贝→入 T1 裁决）③PT-CB3 意图外置终收敛 v2 定稿（EMC=契约集合体·四类+两补充契约·首个实施触点=PT-CB4 T2）④PT 命名令（PT-CB3=学习线/PT-CB4=下轮实施批）⑤AGENTS v2.4 学习必落盘 ⑥`tools/check_server_freshness.py` 上线。
- **home 续点（按序）**：①`git pull` ✅ ②**开工 PT-CB4 T1 对账裁决**（zcode 判裁·输入=A 证据包 5 对+E qty 双头·裁决表并入 `_总账.md`·输家 mv `_retired/`+retired.md 登记·**证据冲突挂起待用户不硬拍**）③T2 口径注册表 ④T3 check_caliber 派 dsh（**F_020 取号主手先行**）。
- **学习线（可选并行）**：Cordis 通俗讲义 8 课全落盘（`discuss/PT-CB3-Cordis通俗讲义_claude-2026-08-19.md`）——第 6~8 课待学+检查题待答，答完回 office 打卡结课。
- **纪律**：一切在分支（main 冻结）；dsh 白名单制；门禁 389+3（上浮须注明）；追踪 ID 连续不跳号；新任务一律 PT 编号。
- **环境**：home 需自起服务时先跑 `py tools/check_server_freshness.py`（R7 预防）；hub 盘仓 remote 仅 office。

---

## 历史卡（08-18 下午·Codex 深挖收工版·HOME 断链期间的家卡底档）

> **位置**：家 | **最后更新**：2026-08-18 下午（**收工**·EMC×dsh 可行性深挖完成·Codex） | **同步**：分支 `EMC_harness_dsh` 收工报告与交接卡随 commit 推送 Gitee + GitHub。
> **回家第一读**：`discuss/EMC-dsh可行性深挖_收工报告_通俗版_Codex-2026-08-18.md`

---

## 当前节点：EMC×dsh 可行性深挖收工 · 等用户确认五项决策 · 零实施

### 一、本轮完成

1. **专题启动**：新增可行性深挖启动包，梳理 R0-R9、形态3、外接大脑与待验证问题。
2. **dsh组深挖完成**：产出 `EMC-dsh可行性深挖_回应_dsh组-2026-08-18.md`。
3. **Codex 主线程抽验**：产出 `EMC-dsh可行性深挖_回收抽验_Codex-2026-08-18.md`，确认三项强吸收修正，并纠正 dsh 的事实口径。
4. **用户沟通版**：产出五项决策通俗说明，避免内部代号造成理解障碍。
5. **收工报告**：产出 `EMC-dsh可行性深挖_收工报告_通俗版_Codex-2026-08-18.md`，供回家继续阅读。
6. **全局沟通规则**：面向用户时必须系统讲解背景/选项/代价/推荐；禁裸用内部编号；技术细节放附录。已写入用户全局 AGENTS、项目 AGENTS 与 CB KNOWLEDGE。

### 二、当前技术共识（通俗版）

- **不搬家**：不做“情绪地图整体寄生进 dsh”。
- **开标准插座**：把数据、口径、知识、地图样式和出口能力开放给通用 AI 助手。
- **插座必须带说明书**：
  1. 每个结果带口径标签；
  2. 数据清单带字段、坐标系、用途和脱敏示例；
  3. 知识检索提供带来源的综合，不只丢原文片段。
- **外接大脑暂不排期**：dsh 可当个人工作流工具；产品入口不押在 dsh 上。
- **以后若研究外接大脑**：必须使用专用干净环境，只给最小权限。

### 三、dsh 事实口径修正

- 新 dsh 仓库：`D:\Github\dsh` @ `f1e10a678e`。
- 旧 `D:\Github\dsh_test` 目录仍存在，但已不是 git 仓库，仅剩残留文件。
- 当前历史可查到 16 个 `!:` 与 13 个 BREAKING 相关提交；旧“600 commit 内 16 个”口径不可复现。
- 更稳证据：8 月 11 日至 17 日六天出现 10 个候选版本，说明 dsh 仍在快速变化。
- dsh 权限机制较严格：每次放行只对当前操作有效，没有会话级全放行。

### 四、五项决策状态

| 决策 | 建议 | 当前状态 |
|---|---|---|
| 三张说明标签 | 接受 | 待用户确认 |
| 新插座考试标准 | 接受 | 用户初步表示应该接受 |
| 外接大脑 | 不排期、不专门维护，只观察 | 待用户确认 |
| 朋友实践 | 真实存在；先评审现有链路 | 用户已确认朋友每天在用 |
| 专用干净环境 | 接受，作为硬条件 | 待用户确认 |

### 五、回家继续动作

1. 读收工报告；
2. 若同意，回复“1、3、5 都按推荐记录”；
3. 向朋友要真实演示、启动方式、连接方式、权限设置和日志；
4. 暂不实施、不出正式开工计划；
5. 确认后再决定平台化与标准插座实施顺序。

### 六、注意事项

- 本轮纯文档讨论，未改生产代码。
- 工作区可能有 Excel 临时锁文件 `~$...xlsx`，勿提交。
- main 上 CB-39 / CB-41 等实施线以各自交接和 git 为准，不要与本轮讨论混线。
