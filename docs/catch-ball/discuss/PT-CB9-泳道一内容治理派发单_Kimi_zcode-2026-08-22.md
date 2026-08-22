# PT-CB9 · 泳道① 内容治理派发单（Kimi·与泳道②并行·文件零交集）

> 主手：zcode。执行：Kimi。分支 `EMC_harness_dsh`·commit 前缀 `PT-CB9(L1):`。**本地仓即最新·零 pull 零 push**（显式路径 commit·主手回收统一 push）。
> 依据：v1.2 终版 + `docs/rag-loader-contract.md`（**你的编码权威源**——schema/签名/红线全在内）+ 基线报告 §二.2（同源现象 11/60 实证）。
> 门禁基线 508+4 不许降。你首批双件考核优——本件是内容治理细活，质量优先于速度。

## 铁则

- **只改 loader/数据侧**：`rag_index.py` 的 `_load_notes/_load_facts/_load_concepts/_load_cases` 四函数与数据文件；**禁碰 `search()`/`build_index()` 的检索逻辑**（归泳道② Codex·文件内冲突面已切分）。
- 零新追踪 ID·`_safe_print`·禁 emoji·A9；改数据文件前先读原文（治理是精细手术不是重写）。

## 件① 语料地图建档（v1.2-pre §5.1·白名单制）

- 新建 `docs/rag-corpus-map.md`：四源逐一登记——来源路径→chunk type/dim→条数→知识提交入口（哪个文件加内容）→维护纪律一句话。
- 盘点以 `tools/rag_index.py` 实际索引面为准（notes=282/facts=68/concepts=9/cases=5·总 364——数字以你实跑为准入图）。
- 附「新增来源流程」一节：入图→入库→`py tools/rag_index.py --build`→门禁→commit（五步模板·v1.2-pre §5.1 原则 1 的落地版）。

## 件② 治理字段填充（loader 契约 schema 落地·status/lineage）

1. **status 字段**：四 loader 按 chunk 语义填 `status`：
   - 与 X-01 作废口径关联的 chunk（作废值 87.9%/5,615/港务 1,153/双高各代/page7 密度版——见口径注册表 §三）→ `status: 'superseded'`（**先 grep 定位**哪些 md 小节/事实卡含这些值·逐条标注·不确定的单列「待裁」清单不改）；
   - 其余默认 `'active'`。
2. **lineage 字段（C-D 同源标注·不删除）**：
   - 起步集=黄金集 11 条实证同源对（`tests/rag_golden.yaml` 带 lineage 标注的条目）+ 你 grep 能确认的「事实卡 ↔ 原笔记」对（格式沿契约：`'src:<上游文件>#<节>'`）；
   - **只标注不删档**（去重的检索侧处理归泳道②消融验证）；目标：事实库 68 张卡中可确证同源的全部标注。
3. **全文纪律断言（CB-22）**：`tests/test_rag_loader.py` 新增——抽 20 chunk 断言 `text` 为全文非截断（len>20 的段 text 与源 md 小节文本一致性抽查）。
4. **检索兼容红线**：字段缺失=`active` 兼容（泳道②按此预置过滤）——加一条断言：全部 chunk 经 loader 后 status ∈ {'active','superseded'}。

## DoD

- [ ] corpus-map 落盘（数字实跑入图）+ 治理字段填充（superseded 标注清单+待裁清单入执行记录）+ lineage 标注数报告
- [ ] `python -m pytest tests/ -q` 全绿（508+4 基线·新测试上浮注明）·test_rag_gate 全绿（你的改动不允许造成任何 hit→miss 翻转——**superseded 过滤在泳道②侧·你只填字段**）
- [ ] 执行记录落盘 `PT-CB9-L1执行记录_Kimi-2026-08-22.md`（含：标注统计/待裁清单/无新坑或已蒸馏声明）
- [ ] 显式路径 commit·零 pull 零 push

> zcode 主手 · 2026-08-22 · 泳道①派发（①=数据侧·②=检索侧·零文件交集·并行安全）
