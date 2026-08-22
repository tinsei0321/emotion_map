# PT-CB9 · 泳道③ 工程收尾派发单（Kimi·zcode+Codex 双审计模式）

> 主手：zcode（主审）+ Codex（复审）。执行：Kimi（能力评估 A- 后首件独立担纲·R24 redemption 场景）。分支 `EMC_harness_dsh`·commit 前缀 `PT-CB9(L3):`。**本地仓即最新·零 pull 零 push**（显式路径 commit·主手回收统一 push）。
> 依据：v1.2 终版+泳道①②回收记录（96.7% 达标后工程收尾）。门禁基线 **514 passed + 4 skipped**。
> 必读：`docs/rag-loader-contract.md`（护栏权威源）+ `docs/rag-baseline.md` + **debug-memory R24（治理标注必引原文句子——本件的语义标注红线）**。

## 铁则

- **R24 红线**：X-01 作废登记每条必附原文引句（禁主题/时间推断）——你的 3prime 误读已规则化·本件即用新规则做同类工作。
- 只改工程侧：`tools/rag_index.py`（build/命令链）+ `tools/rag_ctx_prefix.py` + 注册表登记；**禁碰 search 检索逻辑与黄金集期望**（96.7% 成果冻结·快照零退化）。
- 零新追踪 ID·`_safe_print`·禁 emoji·A9；不确定的语义判断→待裁清单（不硬拍）。

## 件① 重建命令一体化（护栏 4）

- `rag_index.py --build` 内部串「（增量）前注生成 → 入库 → 索引构建」：检测 `_ctx_prefix_map.json` 缺失/正文 hash 不符的限定域 chunk → 自动调 `rag_ctx_prefix.generate()`（增量·跳过未变更）→ 再走 build。**禁拆两个手工步骤**（双机重建一条命令）。
- `--build` 输出摘要含：chunk 总数/前注覆盖数/跳过数/superseded 数。

## 件② loader 护栏齐全化（护栏 3+5）

- **护栏 3**：build 的 `content_hash` 改为覆盖「正文+前注」整体（前注变而正文未变→hash 变→快照可检测）；`ctx_prefix_hash` 分离保留（loader 契约三字段不变）。
- **护栏 5**：新增测试 `tests/test_rag_loader.py` +1 用例——黄金集抽 6 条限定域 chunk 断言前注含出处要素（文档名/小节/口径状态任二·`rag-baseline` 抽样法）。

## 件③ X-01 作废 chunk 逐条显式登记（R24 应用）

- 按 `口径注册表 X-01` 作废数字清单（87.9%/5,615/港务 1,153/双高各代含合并 26/page7 密度版/公服 1,068/194 行/675 行）——**逐值 grep 语料**定位含该值的 chunk：
  - 每条登记必附**原文引句**（R24）+ 替代口径指针（X-01 替代列）；
  - 属「历史叙述上下文提及」（如口径注册表 X-01 卡自身/变更链记录）→ **不标 superseded**（登记但 active·理由注明）；
  - 属「以作废数字为现行结论」→ 标 `status:'superseded'`；
  - 不确定 → 待裁清单。
- 登记产物：`tools/rag_index.py` 的 `_SUPERSEDED_SOURCES` 显式清单（chunk source 级·替代 `_SUPERSEDED_FILE_PREFIX` 文件级机制）+ 执行记录附逐条引句表。
- **改后必跑**：`py tools/rag_index.py --build` + `python -m pytest tests/ -q` + `python tools/rag_eval.py`——**96.7% 零退化红线**（若某 golden 期望答案本身含作废数字→待裁报主手·不自改期望）。

## DoD

- [ ] 三件齐·全量 514+4 不降·rag_eval 96.7% 零退化·test_rag_gate 全绿
- [ ] 执行记录落盘 `PT-CB9-L3执行记录_Kimi-2026-08-22.md`（含：X-01 逐条引句表/待裁清单/无新坑或已蒸馏声明）
- [ ] 显式路径 commit·零 pull 零 push

## 审计安排（用户令·双审模式）

1. Kimi 交付 → **zcode 主审**（真实链复测+R8.1 边界+引句抽验）；
2. **Codex 复审**（代码对抗审查：命令链原子性/护栏完备性/登记与检索行为一致性）；
3. 双审通过 → 泳道③收口·PT-CB9 进入全量验收。

> zcode 主手 · 2026-08-22 · 泳道③派发（Kimi 担纲·双审计）
