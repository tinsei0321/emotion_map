# EMC 项目长期约定（workspace memory）

## 分支与交付（2026-08-24 更新）
- 唯一工作分支：`EMC_Codex_Harness`（自 main 开出）。旧分支 `EMC_harness_dsh` 已合并入 main 并删除（里程碑标签 `emc-dsh-milestone`）。
- `main` = 稳定里程碑，仅授权合并，禁直接开发提交。
- 所有提交走 EMC_Codex_Harness，commit 前缀如 PT-CB11(K1)/PT-CB9(L1)/PT-CB9R(A2)/SHELL(S3)/PT-CB15；显式路径 add，禁 `git add -A`；禁 push（用户本地终端执行）。

## 沟通纪律
- 中文、结论先行、结构化表格、无 emoji（用 [OK]/[WARN]/[ERR]）；首次出现业务名称而非裸编号。
- 纯讨论类任务 = 零实现零 git，仅落盘 docs/catch-ball/discuss/。
- 学习报告必讨论必落盘，无回应不收敛。

## 编码铁律
- 用 _safe_print 替代裸 print；规范埋点；遵守 AGENTS.md 铁律与 debug-memory（R1/R2/R8 自查）。
- 新追踪 ID 注册 core/tracker.py；交付物必须「可双机同步」——进 git 须 commit+push 才算完成，仓外资产须有复刻清单/配方（禁硬编码绝对路径）。

## 当前在途（2026-08-24）
- PT-CB15 Codex 替换 dsh：三组回应齐，Qoder 执行真实用例验证 spike（33eddf9，~5h）。
- Kimi 待收 Qoder spike 结果后跟进：C4 render_spec 免审批、C7 断流看门狗、D1 嵌入模型进程内单例、D5 引擎角标。
