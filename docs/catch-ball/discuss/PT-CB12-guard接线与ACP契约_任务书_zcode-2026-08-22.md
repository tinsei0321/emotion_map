# PT-CB12 · guard 统一接线 + ACP 契约 v1 · 任务书（zcode 主手·2026-08-22）

> 依据：claude 全批终审 N1（guard 统一接线·下批第一顺位·已随收官裁定）+ 用户 Harness 选型裁定（暂 dsh·**契约成熟后再测 Codex**——ACP 批是「契约成熟」的直接落点）。
> 分支 `EMC_harness_dsh`·commit 前缀 `PT-CB12(T1/T2):`。本地仓即最新·零 pull 零 push（显式路径 commit·主手回收统一 push）。基线 **500 passed + 4 skipped**（首次全绿）。

## 件① guard 统一接线（执行=Codex 协同·~0.5d）

**问题**（claude 终审 N1）：`_GUARD_SPECS` 声明 7 件工具但 `_guard_check` 仅 trend 1 处接线——其余工具守卫在各自函数体内。「挂表」≠「有守卫」·新工具漏接线风险。

**规格**：
1. 9 件带面输入工具（zonal/buffer/rank/grid_aggregate/compare_regions/area_stats/nearest_analysis/overlay_analysis/trend_analysis）入口统一改调 `_guard_check(tool, {'boundary'|'layer_a'...: 值}, caliber)`；
2. `_GUARD_SPECS` 补齐 9 件声明（参数名与真实签名对齐·`_audit_input_surfaces` 启动核对兜底）；
3. **行为零变化**：既有 G-2 拒绝测试（散在 test_mcp_server_emc 各工具用例）必须原样全绿——本件是接线重构非守卫改语义；
4. 体内原有 `_reject_analysis_output` 直调可移除（由 _guard_check 包）或保留双保险——**推荐移除**（单一通路·防双份维护漂移）；
5. 表头注释（N1 已加）更新为「全量接线完成」；
6. 测试：新增 1 例「未声明工具调 _guard_check 的行为」文档化断言（防未来漏声明）。

## 件② ACP 契约 v1 起草（执行=zcode 自做·20 行级·**只定义不实现**）

**依据**：Harness 选型讨论收口 §三.D + 用户裁定（契约成熟=测 Codex 的前置）。

**产出**：`docs/contracts/acp-v1.md`（或 render-contract 同级目录）——内容框架：
1. **四动词**（create/read/update/dispose 或同等·最小集）；
2. **五族事件**（宿主无关语义层）：消息增量 / 工具条目起止 / 命令输出增量 / 错误 / 审批请求——词表第一候选=EMC 自持四阶段（diagnose/agent_step/answer/optimize）映射；
3. **状态对象**：会话/轮次/工具调用的最小状态字段；
4. **附录**：Codex v2 Notification ↔ ACP 语义映射表（从选型讨论沉淀）+ dsh 现状（无官方面）注记；
5. 红线：不抄 Codex 字段名（threadId 等）·不绑传输格式·EMC 为契约权威。

## DoD

- [ ] 件①：G-2 拒绝用例全绿原样·+1 新断言·_GUARD_SPECS 9 件齐·全量门禁 500+ 不降
- [ ] 件②：acp-v1.md 落盘·四动词+五族+状态对象+映射附录·零实现代码
- [ ] 执行记录/契约评审注记落盘·显式路径 commit

> zcode 主手 · 2026-08-22 · PT-CB12 开批
