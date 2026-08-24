# PT-CB15 SPIKE · zcode 独立审计（主手·2026-08-24·收敛前自查）

> 性质：收敛方独立审计（R8.1 三路——执行方自报/claude+kimi 审计/主手独立验证·第三条路）。
> 方法：六文件全读（codex_bridge.py 234 行/brain-adapter-codex.js 121 行/端点/panel/serve 逐行）+ 门禁独立复跑 579+4 绿 + 协议契约逐条对。

## 一 白话摘要

把「换脑桥」自己从头到尾验了一遍：**桥是通的·接得干净·但有五处工程债要还**——最要命一处是「看门狗其实看不住门」（只有在对方完全沉默时才计时·对方持续小声说话就能无限拖下去）；另有两处「硬编码地址」会把家里能用的东西带到办公室就断；还有「工具调用的开头和结尾对不上号」「出错时的线索被丢进下水道」两处。都不是能不能用的问题·是**能不能放心用**的问题。

## 二 发现清单（主手独立·file:line 级）

| # | 级 | 发现 | 证据 | 修法 |
|---|---|---|---|---|
| Z-01 | **P1** | **看门狗名不副实**：`budget` 检查只在 `readline` 15s 超时分支——若 app-server 持续 <15s 吐行（任何通知/噪音行）·300s turn 预算**永不触发**。「有流量=无限续命」 | codex_bridge.py:149-159（`except TimeoutError: if ... > budget`） | 循环内每行处理后检查 `time.time()-t0 > budget`·与超时分支同收口 |
| Z-02 | P2 | **tool begin/end 配对断裂**：bridge 未透传 item.id·前端 end 事件 `toolcall_id:''`（begin 有 id·end 空）——壳的工具过程显示配对悬空 | codex_bridge.py:178-197（item 事件不带 id）+ brain-adapter-codex.js:82 | bridge 的 started/completed 透传 `item.id`·前端 end 复用同 id 配对 |
| Z-03 | P2 | **`_SPIKE_CWD` 硬编码绝对路径**（`D:\Github\_codex_spike_cwd`）——违反全局规则五占位符纪律·office 机可能无 D:\Github | codex_bridge.py:28 | 占位符化（`{REPO}` 邻域推导或环境变量）·复刻清单登记 |
| Z-04 | P2 | **npm vendor 路径硬编码**：`_resolve_codex_exe` 的 fallback 写死 `APPDATA\npm\node_modules\@openai\...` 链——office 机 npm/pnpm 布局差异即断 | codex_bridge.py:43-45 | 多候选探测（which/全局根遍历/npm root 命令）·失败 fail-closed 已守 |
| Z-05 | P2 | **stderr=DEVNULL**：app-server 崩溃时唯一诊断面被丢·CODEX_BRIDGE_START/CODEX_PROC_EOF 时用户只有笼统消息 | codex_bridge.py:104 | stderr 接环形缓冲（末 4KB）·error 事件携带 |
| Z-06 | P2 | **seq 缺口检测未实现**（三组回应 Kimi 建议·spike 未做）：前端 delta 带 `n` 计数可检丢帧·当前静默 | brain-adapter-codex.js:65-69（n 未消费） | n 连续性检查·跳号按 error 处理 |
| Z-07 | P3 | **`_request` 握手无超时**：initialize 挂起时 ensure 无限阻塞（前端总护栏兜底·桥内无） | codex_bridge.py:70-85 | 握手加 `wait_for(30s)` |
| Z-08 | P3 | **`_reason_sent` 跨 turn 持久**：第二轮起推理占位符不再发 | codex_bridge.py:181-184 | turn 开始时重置 |
| Z-09 | P3 | **thread 无限续用**：多轮上下文无限增长·token 成本线性涨·窗口风险 | codex_bridge.py:113-114 | 注记：长会话压缩策略列入正式化件 |
| Z-10 | P3 | done→tool.end 语义映射是 hack（「Codex 完成」伪装成工具观察行）——壳渲染可用·协议语义不纯 | brain-adapter-codex.js:86-90 | 正式化时 done 映射 turn 族·或注记豁免 |

## 三 正面确认（主手独立核实·非执行方自报）

- **契约符合**：provenance 恒 'real'（Codex 全量形态红线）·诊断卡 intent='codex' 无降级标记——诚实性✓
- **安全面**：`approvalPolicy:'never'`+`sandbox:'read-only'`（EMC 工具全只读）+argv 传递+cwd 隔离防本仓 AGENTS.md 注入——✓
- **fail-closed 语义化**：codex.exe 缺失/进程 EOF/turn 超时/turn 失败——四路 error 事件收口·不 500·不伪造✓
- **追踪号**：F_042/F_043 连续注册（F_041 后不跳号）·F_042 免 @track 豁免有实证依据（track_async 包 async generator 丢 __aiter__）且注册表描述注明——✓
- **Schema 锁**：fixtures 在仓·锚定 0.149.1·重建命令在 README——✓
- **门禁**：独立复跑 579+4 绿·rag_eval 96.7% 未复测（本件不触 RAG 面·风险零）

## 四 总裁决：**有条件通过**

- 条件=Z-01（P1 看门狗）必修+Z-02~Z-06（P2×5）限期修——**全部不阻塞「今天就能测」**（单用户·正常流下无触发）。
- Z-07~Z-10（P3×4）记账随正式化。
- Q4 的两个残留（双后端 inbox 竞争=环境因素/map.js 样式竞态=既有 bug）**非本件引入**——inbox 竞争在正式化时加运行锁或文档警示·样式竞态挂既有 bug 队列。

## 五 待与两报告交叉

claude（正确性/测试/集成）+kimi（产品/用户）两报告到达后·交叉对账合并处置表→报用户终裁。预判交叉面：Z-01 看门狗（claude 可能从测试视角同抓）/Z-02 配对（claude 协议视角）/引擎四态心智（kimi）。

> zcode 主手 · 2026-08-24 · 独立审计·第三路验证
