# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月18日 上午（**page7 数据图层线 TOP10/TOP20 交付 · zcode 接续**·claude·4 commit 待用户 push）| 分支 `EMC_harness_dsh`（含全部 page7 数据谱系·main 为其祖先·merge-and-delete 待行）
>
> CB 入口：`docs/catch-ball/_cb-index.md`
> 角色：Codex = 主开发（唯一 git 写者）·claude组 = 评估+收敛·zcode组 = 本线接续（用户指派·page7 数据图层线）
> 换机卡片：`_handoff/HOME.md`（家）+ `OFFICE.md`（公司）

---

## 当前节点：page7 数据图层线交付完毕 · zcode 接续 · 4 commit 待用户 push

### 一、本会话完成（2026-08-18·claude）

1. **TOP10/TOP20 社区图层**（用户指令：12345 两方面诉求总量排名前 10/前 20 社区·一个图层·社区分开不合成一面）：
   - 图层：`DATA/boundaries/presets/12345_top{10,20}_社区.geojson`（**单社区面不合并**·属性 排名/诉求总量/民生基础件/安全韧性件/每周约件数 + 街办/来源）
   - presets 注册：`page7_12345_top10` / `page7_12345_top20`（体检控件对象组末尾·manifest 单点）
   - 生成脚本：`SCRIPT/gen_12345_top10_layer.py`（幂等复跑·`TOP_NS=[10,20]`·**对账断言全量锁定**：1-10 锁 md 主观表头部·11-20 锁 08-18 基线·漂移即报错）
2. **口径**（与 page7 两表口径 2026-08-17 扩域版零漂移）：源 = `DATA/analysis/12345主观/12345_社区x9类_全覆盖.csv`（174 范围内 ok 精确点·154 社区·区级点不进表）；总量 = 类9 九列求和；方面拆分 民生基础={住宅,停车,出行,噪声,物业} / 安全韧性={出行安全,消防安全,环境安全,管网安全}（点级「方面」字段交叉核验）
3. **数字锚点**：TOP10 = 主观表头部（朝阳路 594→宝联 156·含新区东城）；TOP20 续位 体育场路 136→柏临河路 88（第 20 名边界无并列·88 vs 83）；**11-17 名含 5 个两表重叠社区**（宝联/体育场路/营盘路/胜利四路/汕头路·与客观表叠加成片叙事）
4. 文档同步：按页 md（`体检2026补充_按页数据更新_2026-08-17.md` page7 节 + 数据文件对照表）+ revision-log **5.255/5.256** + todo 08-18 段
5. commits：`f672f0a8`（TOP10）·`94e8e2f3`（docs）·`7ce68fbe`（TOP20）·`f84af447`（docs）——**全部待用户手动 push**
6. 验证：`py -m pytest tests/test_range_selector_presets.py -q` 3 passed；RAG 索引本地重建 363 条（`HF_HUB_OFFLINE=1` 24s·索引 gitignore 不入库）

### 二、zcode 接续要点（扩展模式与口径权威）

- **扩展模式**：如需 TOP50/按方面单独 TOP/按街办聚合 → 改 `TOP_NS` 或仿该脚本（读矩阵 csv → 排序 → 从 `DATA/analysis/体检对象_社区_面.geojson`（193 面·筛 类型=城市社区）抽面 → presets 幂等注册）
- **口径权威源**：page7 = `DATA/analysis/page7小结/page7_绝对值口径_全域_2026-08-17.csv` + 按页 md page7 节；**改阈值/口径必须四同步**：md + csv + Excel（4 sheet）+ 图层对账断言（断言会拦漂移·勿绕过）
- **红线**：presets 注册走 manifest 单点勿散放；geojson/csv/xlsx 禁入 RAG；DATA/raw 不动；只 commit 不 push（用户手动 push）
- **RAG build 必带** `HF_HUB_OFFLINE=1`（裸跑联网卡死·5.253 踩坑）

### 三、并行线（本会话未动·以 git/文件为准）

- **EMC×dsh 专题**：R0-R9 全收敛·**卡在等用户三组拍板**（E4 形态3 / 并轨排期 / 外挂大脑两键）→ 台账+拍板包+通俗报告在 `docs/catch-ball/discuss/`（详见 git 历史 15468f62 前后的交接卡·git log 可溯）
- **main**：CB-39 B 线 B1-B4 → C 线 C1-C5 在途（Codex 另会话推进）；基线 366 passed + 3 skipped
- Codex 今晨新增未跟踪：`docs/catch-ball/discuss/EMC-dsh可行性深挖_专题会谈启动包_Codex-2026-08-18.md`（**勿动·待其自 commit**）

### 四、工作区注意（非 claude 产生·待用户裁定）

- `DATA/analysis/page7小结/page7_分组汇总_2026-08-17_绝对值.xlsx` 显示已修改（用户 Excel 开着·或为用户自编）+ `~$` 锁文件在
- `DATA/analysis/12345_top10_社区.geojson`（analysis 根·用户手动副本·presets 正主在 `DATA/boundaries/presets/`·留删待用户定）

## 关键架构（下会话须知道·承重）

- **数据池三分**（DATA/README 单源）·铁律7（片区=结论·4 维度控件第一落位）·「两板块=结论」（分析过程不按 board 过滤）
- **page7 两表口径**（用户 08-17 定）：客观线 ≥15 问题点（48 社区）/ 主观线 ≥50 件≈每周 1 件（47 社区）/ 重叠恰 10（叠加目标·非独立类别）；**双高概念已废**
- 守卫已通电：9 validate_* 进 pytest·SKILL_DEFS 真身解析·diagnose prompt 冻结

## 红线 / 纪律

- 只 commit 不 push·修订日志每提交一行（§5 顶）·todo 最新置顶·交接卡只在说"交接"时覆写
- sim 禁入·gdb 只读·密钥只输出 key 名·术语「街办」·交付物全中文·专业词+通俗解释
- CB 工作流：评估方只读+禁 git+落盘 discuss/；每轮收敛必更 _cb-index+cb-journal+goal-status

## 恢复指引（zcode 新会话）

1. `git log --oneline -6` 对账（4 commit 待 push）+ `git status`（注意 §四 两处用户文件·勿误提交 `~$` 锁文件与 Codex 未跟踪文档）
2. 读本卡 + `DATA/analysis/汇总/体检2026补充_按页数据更新_2026-08-17.md` page7 节 + `SCRIPT/gen_12345_top10_layer.py`
3. 复跑自检：`py -X utf8 SCRIPT/gen_12345_top10_layer.py`（应全 [OK]/[skip]·零变化）+ `py -m pytest tests/test_range_selector_presets.py -q`
4. 等用户下一指令（数据图层延伸候选：TOP50 / 按方面分层 / 两表重叠 10 社区专层 / 客观线 TOP 社区同构图层）
