# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。
> 📝 详版历史 = [revision-log §5](revision-log.md#L226)（永久审计底）·本文件只记当前 + 计划。
> 📌 **架构版本**：v1（三阶段 5.231-5.242）→ **v2（单次 LLM + FC·5.243-5.245b·第三方实施）** → **v3（v2 做对·5.246-657c2e3·GLM 修复）** → **v3.1**（reg.filter 崩溃修复 + SCAN P1）→ **v3.2**（CB-09 bug 修复·D057 修订·代码自动扩展·全自动多步执行·fix/emc-buglog 分支 7 commit）→ **v3.5**（CB-10/CB-11 系列·merge 多图层 + 只说不做根治）

---

## 📅 2026-08-26（Kimi · PT-CB19 cdh 综合修复计划收敛 · office 推进清单）

### ✅ 已收敛（home 机）

- 三报告合一（Kimi 思维链评估 / claude 机制对照 / codex 复测 7 项）→ 五问题域：P-A 思维链慢 / P-B 出图契约缺口 / P-C 色带归一缺失 / P-D 知识权威分级未落调用面 / P-E 验收方法学；
- 计划书落盘 `docs/catch-ball/discuss/PT-CB19-cdh综合修复计划书_Kimi收敛-2026-08-26.md`：W1-W11 三批次 · Kimi 7 件 / Codex 4 件 · 验收标准按 codex 修正口径（项 3 三要件同验·项 6 移出验收改验 130 拒绝纠偏）；
- Codex 组派发 prompt 已在对话交用户（不落盘·08-26 令）。

### ⬜ 待用户拍板（四裁决 · 计划书 §五白话版）

1. 推理档 high→medium：建议先 W9 对拍拿数据再定；
2. 130 口径：建议硬拒绝+纠偏 193；
3. 快路径共存（W11）：建议看 W10 三引擎对拍数据再拍；
4. 批次一 W1-W4：建议立即开工（两组可并行）。

### ⬜ office 环境待执行（拍板后按序）

1. Kimi 组批次一：W2 行政区过滤参数（zonal_stats/rank/aggregate_export 加 region）→ W3 render_spec 意图锁（scope 声明+要素数守卫）→ W4 cdh AGENTS.md 任务方法论段（标准路径/Top-N 纪律/色带速查/130 纪律改写）；
2. Codex 组：W1 色带归一表+未命中告警（可与 Kimi 并行）→ W5 批次一验收复测（三要件同验）；
3. 批次二（Kimi）：W6 数据四层短答入 RAG / W7 130 硬约束 / W8 口径段权威分级——rag_eval 96.7% 门禁零退化；
4. 批次三：W9 推理档对拍（Codex）→ W10 三引擎同题对拍（Codex 执行·Kimi 收敛）→ W11 快路径方案进 CB。

## 📅 2026-08-26（Kimi · PT-CB18 工作方式优化批收口 · office 待执行清单）

### ✅ 已收口（home 机）

- PT-CB18 W1/W2 执行+验收通过：手册 309→91 行（双阈值 150/200）、STATE.md 单一状态源（首行时间+HEAD 哈希）、GLOSSARY.md 编号翻译表、一事一档（RULES §4.8）、评审三档、派发/白话模板；门禁 621+3 零失败，5 commit 在本地。
- 工作方式新基线六条已入 workspace `MEMORY.md` 全局段；全组通知 prompt 已在对话交用户。

### ⬜ office 环境待执行（到岗后按序）

1. **git pull 后先跑生成器**重建 STATE.md / GLOSSARY.md（用首行哈希判新旧），再开工——别拿 home 机旧状态当真；
2. ~~**用户 push** 五批 PT-CB18 commit~~ ✅ 已在远程（08-26 核实 origin 已含至 90b3250）；**新增待推**：PT-CB19 三批（49a39e0/3f3b9dd/07c512a·home 机沙箱无 gitee 凭证）——用户终端执行 `git push origin EMC_Codex_Harness`；
3. **全组通知下发**（08-26 对话内 prompt，复制发各组）；
4. **用户拍板**：W3-2（自家档案喂 RAG）是否派发 Qoder——验收已裁定具备启动条件；
5. W3 队列按序：W3-2 → W3-5（RTK 评估）→ W3-1 / W3-3 / W3-4（W1/W2 验证复核后另起）；
6. 观察项执行件：`_board.yaml` awaiting_user 标 deprecated 迁移（decisions 唯一来源）；`gate_baseline` 改「零失败」口径（并入 W3-1）；debug-memory 双 R25 改号（规则库维护顺手件）；CLAUDE.md 353 行瘦身（入 W3-3 候选，同判据 A-D 自证）。

### ⬜ 待诊断（用户 08-26 反馈）

- **todo.md 机制「老是卡住」**——具体症状待用户补充再立项。候选方向：周归档靠手工易忘 / 倒序维护成本 / 多会话同写覆盖（实证：今日 .workbuddy 日志已被并行会话覆盖一次，写前必读回）。

## 📅 2026-08-26（claude·Codex Harness 配置隔离修复）

### ✅ Codex 配置隔离——冲突二次复发根治（revision-log 5.128，commit ef93247 · 已推 origin）

- **根因**：EMC harness 与桌面 Codex 工具共用 `~/.codex/config.toml`——emc `required=true` 在共享配置里，家机 8600 未起时桌面工具全部工具调用快速失败；桌面应用升级/model 切换持续改写该文件 → 手工补丁必被冲掉（复发机制）。
- **隔离**：桥自备 CODEX_HOME（`_codex_cwd/.codex`·`_ensure_harness_home` F_045 自愈生成：锁定 deepseek-v4-flash 不可切换 + emc required 迁入 + models.json Deferred 补丁自动化 + 密钥运行时复制不进仓）；桌面配置摘除 emc 段（备份 bak-20260826·flash/pro 可切换保留）。
- **验证**：initialize 响应 codexHome 指向注入目录（CODEX_HOME 100% 生效）；618 passed + 1 skipped 门禁绿。
- 附带：git fetch 报 geometric repack 失败（reflog 无效条目）→ 已设 `maintenance.auto=false` 仓库级绕行；根治（reflog expire + gc）待用户裁决。

## 📅 2026-08-24（office 到岗 · HOME 五步+T1-T7 验收+体检医生专题 · zcode）

### ✅ 到岗五步（1-3 完成）

- fsck 体检过（dangling 无害）· 环境配齐（补装 rank_bm25+jieba=RAG 泳道新依赖）· **基线 574+2 与 home 一致**。
- 主手预检三绿：MCP 8600 streamable-http 握手（需 Accept 双头）/ 8080 health 三引擎 / dsh_engine 端到端（hi→8.3s ok:true）。
- 同步报告（H:\DEV-SYNC-HUB
eports6-08-24-office-EMC-dsh对接同步报告.md）读毕：office 对齐 home 六维一致·dsh 0.1.1-rc.2 官方纯净·18 工具·三引擎·遗留六项（hub 黄灯口径/交接仓 2commit/备份/render_inbox 坏件/思维链补丁/profile 复刻）。

### 🎯 T1-T7 用户验收进行中（指引已交·3080+8080 双窗口三引擎）

### 🔄 本周重点：城市体检医生专题（方向框架已出·待用户四方向排序+Agent形态裁定）

- 四方向：①77项指标落图分析 ②体检×12345四象限比对（推荐先锋）③情绪对问题分析价值（归因佐证）④诉求动态时间轴（time-bar 动画+突变检测）
- 待裁定：优先排序 / 数据缺口盘点 / Agent 形态（MCP 工具组合 vs 分析脚本先行）→ 专题任务书进 CB

## 📅 2026-08-24~25（Codex Harness 融合启动·spike 验证+三方审计+转正批）

### ✅ 分支更替（用户令）
- EMC×dsh 完整链路合流 main（282 提交快进·标签 emc-dsh-milestone）→ 旧分支三处删除 → 新分支 **EMC_Codex_Harness**。

### ✅ PT-CB15 Codex 替换 dsh（CB 讨论→spike→审计→转正）
- 三组 CB 讨论（Kimi/claude/Qoder·六议题）→ Qoder spike 四问全通（工具/流式/壳/全链路·真流式 34-155ms/批）→ **三方审计**（zcode 独立+claude+kimi·零重叠互补：P1 看门狗靠 zcode/零测试靠 claude/用户面靠 kimi）→ **转正批 14 件全修**（看门狗/配对/硬编码×3/诊断面/seq/补测 16 件/竞态重试/竞争锁/SSE CRLF）。
- 四引擎就位：light|dsh|codex|mock（?engine 切换·codex=真流式全量形态）。
- 门禁 **595+4 绿·RAG 96.7% 零退化**。
- 避坑蒸馏：R26（看门狗有流量即续命）+R27（跨进程桥六坑）实时入册。

### ✅ 08-25 收工 7 批（交接卡成果表同步·门禁 616+1）

- **PT-CB15(K1)** 出图双 Bug 治本：几何零转录（layer_output 服务端落盘→render_dataset_id）、manifest 24 断链修复、193 层（含村）入消费面成默认边界、「两个方面」叙事退役、RAG 索引重建 375 chunk、watcher 迟到 TTL、tmp_render 7 天 TTL、transformers 5.x 兼容兜底
- **PT-CB16(C1C3)** E2E 测试骨架（tests/e2e·真实数据顶点保真）+ SSE 多页面订阅身份/定向投递（render_spec target）
- **PT-CB16(S1)** Codex 侧：环境配方 M1-M3（docs/dsh-environment/）+ 索引半自动重建
- **PT-CB16(D1→C2)** 交互三机制定稿+实施：会接话（followup_actions 两级 resolved_params）/会请示（身份卡分支请示纪律）/会看大小（scale 确定性倒推·outlet_card scale_check）；契约 docs/interaction-contract.md
- **PT-CB17(B1B4)** cdh 产品层四问题治本：AGENTS.md 身份纪律+回答范式+只读沙箱纪律（仓内权威副本 docs/cdh/AGENTS.md·start.bat 同步）、aggregate_export 全量导出工具（F_044·③档脚本路径退役）、表格 CSS 规范化、RAG 语料扩 DATA 分层（385 chunk·96.7% 门禁零退化）
- **R7+ 防旧码体系** start.bat 三进程全重置（8000/8080/8600 先杀旧再起新）、devcheck.bat 人话版自检（tools/devcheck.py）、serve.py 启动自检、emc_status 进程自证戳、bat 三铁律（GBK+CRLF+实跑）

### 在途
- office 到岗：T1-T7 用户实测（含新增 T8=?engine=codex 体验——EMC 壳里完整 Harness 首测）+ 转正批复验。
- 挂账：Q4 残留已修入转正批（竞态重试/竞争锁）·五件 P3 随正式化。

