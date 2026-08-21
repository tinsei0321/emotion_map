# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月21日（**PT-CB7 主执行收工**·Qoder——审计先行+T1-T21 大半销号+用户实测五连修·明晨 office 续点）| 分支 `EMC_harness_dsh`（**main 冻结勿动**）
>
> CB 入口：`docs/catch-ball/_cb-index.md`
> 接手第一读：`_handoff/HOME.md` 收工快照 + `discuss/PT-CB7-主执行记录_Qoder-2026-08-21.md` + `discuss/PT-CB7-增补批T14-T17_入口体验与结果契约_Qoder-2026-08-21.md`
> 角色（08-21 用户令）：**Qoder = PT-CB7 主执行**（白名单内 git）·**zcode = 主手**（回收验收/裁决）·**dsh = 协助**（批派发）·**Codex+claude组 = 终审**
> 换机卡片：`_handoff/HOME.md`（家）+ `OFFICE.md`（公司）

---

## 当前节点：08-21 PT-CB7「稳定与灵魂」批主执行收工 · Qoder · 明晨 office 续点

- **08-21 完成（Qoder 主执行）**：
  1. 审计先行：T1-T9 全文审计（M1-M4 修正随执行生效）+ 任务拆解（复杂自执/简单派 dsh 三批）+ WIP 复核。
  2. EMC 仓六 commit（基线 442 passed/2 skipped）：T1 图层自清 `97fb95bd` / T6 MCP 描述紧凑 `0d752150` / T8 脚本参数化+口径对照 `9e7ca1dc` / T5+T9 身份卡扩写+RAG `c6013cf8` / T14 结果呈现契约 `1dc80123` / T10 出图范式契约 render-contract.md `a8a697e5`。
  3. 用户实测五连修：T18 render_file 第 9 插座 `3d80d2cd`（治长思维+误入 Range）/ T16 历史图层残留根治 `8608ff14` / T19 /emc-ready 真就绪 gate+快通道+杀窗守卫 `23888cb3`（治“加载一半失效”）/ T21 SSE 扇出广播+50s 豁免 `691676ab`（治“F5 才见”）/ T15 start_silent.vbs 隐藏启动+对话气泡首屏卡 `fa661192`。
  4. dsh 两批回收：批 1（T2 terminal chunk 修复/T4 计时取证/F1-F4 复核）；批 2（人设 prompt 落地生效·「你是谁」自述实测通过；T17 timeout 120s 无效——根因=MCP 冷启动 >120s 需服务端预热）。记录+截图在 `discuss/PT-CB7-dsh协助批{1,2}记录_dsh-2026-08-21.md`。
  5. 仓外插件 dsh-emc-entry 多轮改造已重建（bundle 18,977B）；当前 8080/8000 新 serve 运行中（/emc-ready 200+ACAO）。
- **office 续点（按序）**：①git pull + office dsh 环境四件套（同 08-20 卡）+ 批 2 同款补三件（人设文件复制/toolCallTimeoutMs 120000/start_silent.vbs 路径免改）②优先验证五项用户实测（快通道/冷启动气泡卡/免 F5 铺层/render_file/身份自述）③待办优先级：T17 服务端预热真修 → T7 双模预设落地+≤2min 验收（批 3）→ zcode 回收+《Qoder 执行效果评估》。
- **待裁决/观察**：T11 被 render_file 吸收待销项确认；D2 欢迎卡绑定目标会话未做；render_file 临时 dataset 累积列观察；debug-memory 撞号已清（E2 合并双 R11 + Codex 08-21 修残留双 R12·重编号 R13-R16·新增 R17-R19 与维护协议·详见 `discuss/PT-CB8-EMC-dsh避坑沉淀报告_Codex-2026-08-21.md`）。
- **注意**：dsh 文件在仓外（`D:/Github/dsh-emc-entry/` + `~/.dsh/`）不入本仓；人设改动在 `~/.dsh/.agent-presets/router-standard-subagent/`（批 2 记录 A-2 有全文与备份名）。

## 旧节点：home 凌晨收工 · PT-CB6 S6 用户复测通过 · render 通道三坑已修（office 续点=S7 回收判读）

- **08-20 凌晨 home 班完成**：
  1. 用户亲测 Q2「12345 热线诉求最密集的 10 个社区是哪些？把结果铺到地图上」→ 端到端成图，用户确认正常。
  2. 修复渲染通道三个坑：
     - `frontend/serve.py` 单线程 TCPServer 被 SSE 长连接占死 → 改 `ThreadingTCPServer` + `daemon_threads=True`（页面转圈/API 502 根因）。
     - `frontend/js/render_client.js` 缺 spec_id 去重 → SSE 重连重放 backlog 导致 8~9 个图层循环跳动；新增 `_seenSpecIds`。
     - `DATA/exports/render_inbox/` 积压 15 个旧测试 spec → 移入 `_backup/`，根目录只留内联 TOP10 spec `1787161960132-3411.json`。
  3. 最终图层：`[dsh] [真实] 12345热线诉求最密集TOP10社区(真实)`（community_choropleth_v1·value_field=诉求总量·community=174）。
- **office 到岗动作**：
  1. `git pull origin EMC_harness_dsh`（本卡随 commit 推送）。
  2. 读 `docs/catch-ball/discuss/PT-CB6-大脑实测记录_dsh-2026-08-20.md` §四 + `docs/todo.md` 2026-08-20 段。
  3. **S7 回收判读**（zcode 主手）：把本次新增三个显示面缺陷（serve 单线程 SSE 阻塞 / render_client 缺去重 / render_inbox 积压重放）并入 PT-CB6 缺陷清单，裁决是否补测/修工具描述。
  4. 若继续 PT-CB6：可安排用户复测 Q3/Q4；或按主手排期进入下一批。
- **待办/风险**：
  - `render_inbox/_backup/` 里 15 个旧 spec 未删除，只移出渲染通道；确认无用后可清。
  - `tests/_tmp_*` 临时调试文件留在工作区，未提交；确认后可删。
  - main 仍冻结；一切在 `EMC_harness_dsh`。

## 旧节点：office 收工 · B1 修复送复审 + PT-CB4 就绪（home 续点=T1 对账裁决）

- **08-19 office 班完成**：①PT 命名令编号纠正（学习线=PT-CB3/下轮=PT-CB4·CB-42 字样清零）②送审 Codex（通知+审计要点五项+prompt）③Codex 审计判 FAIL→七项修复（H1 前端守卫随层标记/H2 hotspot 补挂/M1 边界源全入口过滤/L1-L4）·门禁 389+3·实战复验过④dsh 两批六任务派发+回收全销号（A 证据 5 对/B 素材 57 层/C PII 扫描/D 服务核查工具/E 总账对账/F 指路候选；两条真发现：place_name 内嵌真实身份证→蒸馏强校验入 B4；qty 层两份物理拷贝双头→入 T1 裁决）⑤PT-CB3 意图外置线：收敛 v1→用户"零思考壳子论"质疑→dsh 实现者评价→**终收敛 v2 定稿**（EMC=契约集合体四类+两补充·结构化打回·em:mode·双写·切换判据四条）⑥AGENTS v2.4 学习必落盘规则。
- **home 到岗动作**：①`git pull origin EMC_harness_dsh` ②**开工 PT-CB4 T1 对账裁决**（zcode 判裁·输入=A 证据包 5 对+E qty 双头·产出裁决表并入 _总账.md·输家 mv _retired/+retired.md·证据冲突挂起待用户不硬拍）③T2 口径注册表（B 素材+F 候选+v2 意图卡/口径契约字段·落位 00-宜昌专项/_口径注册表.md）④T3 check_caliber 派 dsh（**F_020 取号主手先行**）⑤环境：home 自起服务（R7：先跑 tools/check_server_freshness.py 核查）；hub 盘仓 remote 仅 office 计划未配（home 无需）。
- **等用户动作**：转发 Codex 复审 prompt（送审通知§六·PT-CB2-送审通知_zcode-2026-08-19.md）——复审回后 B1 销号+学习线收敛+PT-CB3 v2 补审三重点（分流器枚举/打回率阈值/双写维护成本）。
- **Cordis 学习线（home 可续）**：通俗讲义 8 课全落盘（`discuss/PT-CB3-Cordis通俗讲义_claude-2026-08-19.md`）——第 1~5 课已讲完（含打卡：编排器类比/重装浪费/同步异步/订阅制广播），第 6~8 课（效应/生命周期/全书串讲）完整内容已写入、检查题待答；home 续学入口=讲义文件，答完检查题回 office 打卡结课。
- **纪律**：一切在分支（main 冻结）；dsh 白名单制；门禁 389+3（上浮须注明）；追踪 ID 连续不跳号；新任务一律 PT 编号；AGENTS v2.4 学习报告必讨论必落盘。

### 旧节点：EMC×dsh 可行性深挖收工 · 零实施 · 等用户确认

### 一、本轮完成（2026-08-18 下午）

1. **专题会话启动包**：汇总 R0-R9、形态3、外接大脑、材料索引、可行性问题与风险清单。
2. **dsh组专项深挖**：完成独立回应，给出 dsh 侧工程事实、限制与推荐排序。
3. **Codex 回收抽验**：
   - 强吸收三项：结果口径标签、数据说明书、知识综合；
   - 纠正 dsh 事实口径：旧仓库残留、破坏性变更计数、权限文件引用；
   - 建议外接大脑降为零维护观察。
4. **用户沟通修正**：
   - 用户反馈内部代号和抽象问题难以理解；
   - 已形成全局沟通纪律：面向用户先系统讲解、用业务名称、给例子、说明代价与推荐；
   - 已写入用户全局 AGENTS、项目 AGENTS 与 CB KNOWLEDGE。
5. **通俗报告**：
   - 五项决策说明；
   - 收工详细报告；
   - 回家继续顺序；
   - 向朋友索取实际演示的话术。

### 二、当前共识（主文口径）

- 不做“情绪地图整体搬进 dsh”。
- 主路是把情绪地图资产做成标准插座，供 Codex / Claude / ZCode / dsh 等通用助手消费。
- 第一版插座必须带：
  1. 结果口径标签；
  2. 数据说明书；
  3. 带来源的知识综合。
- 外接大脑只作为用户工作流观察项，不进产品排期。
- 以后若研究外接大脑，必须用专用干净环境和最小权限。
- 朋友每天使用 Codex+dsh 已确认；下一步先评审朋友现有链路，不从零开发。

### 三、五项决策状态

| 决策 | 建议 | 状态 |
|---|---|---|
| 三张说明标签 | 接受 | 待确认 |
| 新插座考试标准 | 接受 | 用户初步表示应该接受 |
| 外接大脑 | 不排期、不专门维护，只观察 | 待确认 |
| 朋友实践 | 先评审现有链路 | 已确认朋友每天在用 |
| 专用干净环境 | 接受，作为硬条件 | 待确认 |

### 四、回家继续动作

1. 读 `EMC-dsh可行性深挖_收工报告_通俗版_Codex-2026-08-18.md`。
2. 若同意推荐，回复：**“1、3、5 都按推荐记录。”**
3. 向朋友要：
   - 启动方式；
   - Codex 连接方式；
   - 权限确认机制；
   - 真实任务演示；
   - 日志或记录；
   - 可分享配置/代码示例。
4. 确认前：**零实施、不出正式开工计划**。
5. 确认后再讨论平台化方向与标准插座实施顺序。

### 五、关键文件

| 文件 | 用途 |
|---|---|
| `discuss/EMC-dsh可行性深挖_收工报告_通俗版_Codex-2026-08-18.md` | 回家第一读 |
| `discuss/EMC-dsh可行性深挖_用户沟通版五项决策_Codex-2026-08-18.md` | 五项决策通俗解释 |
| `discuss/EMC-dsh可行性深挖_回应_dsh组-2026-08-18.md` | dsh组 技术原文 |
| `discuss/EMC-dsh可行性深挖_回收抽验_Codex-2026-08-18.md` | Codex 抽验与修正 |
| `discuss/EMC-dsh可行性深挖_专题会话启动包_Codex-2026-08-18.md` | 专题背景包 |
| `discuss/EMC-dsh整体合体_讨论过程台账.md` | R0-R9 过程台账 |

### 六、dsh 事实修正（勿再误传）

1. 当前 dsh 仓库：`D:\Github\dsh` @ `f1e10a678e`。
2. `D:\Github\dsh_test` 目录仍存在，但不是 git 仓库，仅剩残留文件。
3. 当前历史可查 16 个 `!:` 与 13 个 BREAKING 相关提交；旧“600 commit 内 16 个”不可复现。
4. 更稳证据：8 月 11 日至 17 日六天 10 个候选版本。
5. dsh 审批没有“会话级全放行”；每次放行只对当前操作有效。

### 七、工作区与其他线

- 本轮未改生产代码。
- Excel 临时锁文件 `~$...xlsx` 不要提交。
- main 上 CB-39 / CB-41 等实施线以各自文档和 git 为准。
- 收工 commit 与本卡一起推送；回家先 `git fetch` / 对账，再读报告。

## 红线

- 面向用户沟通禁裸用内部编号。
- 未拍板前不实施、不出正式计划。
- 不写第二份工具 schema。
- 工具输出必须脱敏、带口径、可追溯。
- 外接大脑不得绕过情绪地图工具面直取数据。
- 不把产品入口绑死在 dsh。
