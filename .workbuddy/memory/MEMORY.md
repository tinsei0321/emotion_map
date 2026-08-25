# EMC 项目长期约定（workspace memory）

## 分支与交付（2026-08-24 更新）
- 唯一工作分支：`EMC_Codex_Harness`（自 main 开出）。旧分支 `EMC_harness_dsh` 已合并入 main 并删除（里程碑标签 `emc-dsh-milestone`）。
- `main` = 稳定里程碑，仅授权合并，禁直接开发提交。
- 所有提交走 EMC_Codex_Harness，commit 前缀如 PT-CB11(K1)/PT-CB9(L1)/PT-CB9R(A2)/SHELL(S3)/PT-CB15；显式路径 add，禁 `git add -A`；禁 push（用户本地终端执行）。

## 沟通纪律
- 中文、结论先行、结构化表格、无 emoji（用 [OK]/[WARN]/[ERR]）；首次出现业务名称而非裸编号。
- 纯讨论类任务 = 零实现零 git，仅落盘 docs/catch-ball/discuss/。
- 学习报告必讨论必落盘，无回应不收敛。
- **派发 prompt 义务（2026-08-26 用户令·已改）**：凡涉及「给 xx 看/审计/讨论」等有对象的转交动作，必须同时产出一份**一键复制即用的派发 prompt**（含背景、对象、任务、材料路径、验收要求）。**交付形态：直接写在对话里（单个代码块·一键复制），禁止落盘到项目工作区**——落盘会污染仓内目录（2026-08-26 用户令，推翻 08-25「必须落盘 _prompts/」旧规）。
- **裁决点白话义务（2026-08-25 用户反馈「看不懂」）**：讨论稿/方案中需要用户拍板的裁决点，必须另配「用户可拍板的白话版」——每个决策点用生活化例子说清「选 A 会怎样、选 B 会怎样、我建议哪个」，不得只给技术条款。

## 编码铁律
- 用 _safe_print 替代裸 print；规范埋点；遵守 AGENTS.md 铁律与 debug-memory（R1/R2/R8 自查）。
- 新追踪 ID 注册 core/tracker.py；交付物必须「可双机同步」——进 git 须 commit+push 才算完成，仓外资产须有复刻清单/配方（禁硬编码绝对路径）。
- **Windows .bat 三铁律（2026-08-25 三次踩坑）**：①编码必须 GBK（非 UTF-8·cmd 按 ANSI 解析）；②行尾必须 CRLF（纯 LF 遇 goto 标签闪退）；③写完必须实跑验证（静态 lint 不算数）——Edit/Write 工具默认产出 UTF-8+LF，必踩。
- **重启服务进程必须用独立进程方式**（PowerShell Start-Process / cmd start）——在工具 shell 里后台拉起的进程会随会话结束被杀（8600 被误杀实证·2026-08-25）。
- **面向用户的交付物过「非技术视角」审一遍**：用户看不懂的输出=不合格（devcheck 技术名词堆砌被点名·改人话版）；验证脚本先核实键名/字段假设再下结论（「0% 吻合=编造」误判实证）；改注册表字段前 grep 消费方（renewal_unit nameField 实证）。

## 当前在途（2026-08-25 更新）
> ⛔ 本段已冻结（2026-08-26·PT-CB18 W1-1）：在途状态唯一落点 = 仓根 `STATE.md`，本段停止更新（观察一阶段后退役）。
- **战略定向（用户令 08-25）**：本分支聚焦 Codex Harness（cdh）；**dsh 后期大概率退役，只留一个 harness 落地（大概率 cdh）**——cdh 侧工作权重上调，dsh 专属件降优先。
- PT-CB15 双 Bug 治本已执行完（Kimi·K1-K9·门禁 600+1）：layer_output 服务端落盘+render_dataset_id、manifest 24 断链修复、193 层入消费面、口径叙事清洗、RAG 索引重建 375 chunk。
- PT-CB16 短板批：C1 E2E 骨架+C3 SSE 串台已完（607+1）；D1 交互三机制定稿（裁决⑤按 A：模型侧先行+bridge 透传单列 C2-4）；C2 实施中（C2-0→C2-3→C2-2→C2-1）；Codex 侧 S1/S2 在途。
- 待办：用户 push（PT-CB15(K1)/PT-CB16(C1C3)/D1 收敛三批）；8000 重启后复测；home 机索引重建。
