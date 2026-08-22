# PT-CB13 · 进度契约合并版派发单（Codex·与 PT-CB9 并行·零依赖）

> 主手：zcode。执行：Codex。分支 `EMC_harness_dsh`·commit 前缀 `PT-CB13:`。本地仓即最新·零 pull 零 push（显式路径 commit·主手回收统一 push）。基线 **501 passed + 4 skipped**。
> 依据：R59 裁定 K6 + 双评估交叉回收定稿（2026-08-21·合并方案已裁定）。

## 规格（R59 定稿原文吸收）

**目标**：`_board.yaml`（进度契约·文件名取 dsh 版习惯）+ `tools/gen_progress.py`（确定性生成器）——「待拍板清单是用户唯一要盯的·必须保留」。

1. **`_board.yaml` 三段结构**（结构取 Kimi 版）：
   - `stages:` 阶段进度（当前各批状态·PT-CB1~13 一行一条：批次/状态/一句话结论/文档指针）
   - `goals:` 小目标（含 PT-CB11 已完成的 42 小目标视角·可引用 Kimi 预期目标清单的映射·不重抄）
   - `awaiting_user:` 待用户项（**非空检查**·当前内容：T1-T5 复测挂账/下一批排期/Q-A Q-B 已按推荐执行可补裁）
2. **`tools/gen_progress.py` 生成器**（合并两版优点）：
   - **确定性**：同一输入同一输出——**无时间戳**（禁 datetime.now 写入产物）
   - **commit 校验**：产物头部注 `generated from <HEAD short hash>`（subprocess git rev-parse·失败降级空）
   - 数据源=`_board.yaml` → 产出 `docs/progress.md`（人读版·含 awaiting_user 置顶——用户唯一要盯的）
   - 纯只读生成（不改 _board.yaml 本身）
3. **pytest 门禁接线**：`tests/test_progress_contract.py`——①_board.yaml 可解析且三段齐 ②awaiting_user 非空断言（空则 fail·防待拍板项悄悄消失）③gen_progress.py 产物与 _board.yaml 一致性（重生成 diff=0·确定性断言）④产物无时间戳断言（grep 日期格式不中）
4. 首次填充：`_board.yaml` 按 docs/catch-ball/_cb-index.md 与 cb-journal 现状如实填（数据准确性主手回收时核）。
5. 纪律：禁 emoji·_safe_print（生成器 print 走安全打印）·零新追踪 ID（gen_progress.py 纯工具·同 grid_export 先例注明「非 MCP 正式工具」或直接不注册）。

## DoD

- [ ] 两文件+测试落盘·`python -m pytest tests/test_progress_contract.py -q` 绿·全量 501+ 不降
- [ ] 执行记录落盘 `PT-CB13-执行记录_Codex-2026-08-22.md`（含生成产物首版截图/摘录）
- [ ] 显式路径 commit

> zcode 主手 · 2026-08-22 · PT-CB13 派发（与 PT-CB9 P0 并行·零文件交集）
