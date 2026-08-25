<!-- generated 2026-08-26 07:02 from a87ae50 -->

# EMC 当前状态（单一交接文档）

> 数据源 `_board.yaml` + git·`py tools/gen_state.py` 生成·HEAD `a87ae50`。在途状态以本文为唯一落点；历史进度看 `docs/progress.md`。

## 当前分支

`EMC_Codex_Harness`

## 在途批次（每批一行）

- PT-CB3（部分完成）：学习线（Cordis/dsh 精髓）持续输出·意图外置与需求契约讨论进行中（docs/catch-ball/_cb-index.md）
- PT-CB8（待回收）：EMC×dsh 避坑沉淀报告（R1-R19+六元模式）已落盘·全组当轮回应待收（docs/catch-ball/discuss/PT-CB8-EMC-dsh避坑沉淀报告_Codex-2026-08-21.md）
- PT-CB9（泳道中）：RAG 重构 v1.2 候选讨论中（业界适配+Harness 接轨·六增补待拍板）（docs/catch-ball/discuss/PT-CB9-RAG重构CB讨论发起_zcode-2026-08-22.md）
- PT-CB12（进行中）：guard 统一接线（T1 完成待回收）+ ACP 契约 v1（T2 已落盘）·收口中（docs/catch-ball/discuss/PT-CB12-T1执行记录_Codex-2026-08-22.md）
- PT-CB18（进行中）：工作方式优化批（单一交接文档/手册瘦身/术语表/规范模板·Qoder 执行 W1/W2 中）（docs/catch-ball/discuss/PT-CB18-工作方式优化任务书_v1.0定稿-2026-08-26.md）

## 待拍板项（消费 _board.yaml decisions 区）

- D-001 RAG 重构 v1.2 讨论（PT-CB9）六增补采纳与否（业界适配+Harness 接轨）｜候选：全采纳 / 甄别后修订采纳 / 暂缓待 RAG 框架另定
- D-002 工作方式优化批（PT-CB18）后续四件（档案喂检索等）启动时点｜候选：W1/W2 验证复核通过即启动 / 待用户 push 完成后启动

## 门禁基线

- pytest：618 通过 + 1 跳过（零失败）（2026-08-26·commit `ef93247`）
- 全量跑法：`py -m pytest tests/ -q`（判新旧以本文首行生成时间 + HEAD 为准）

## 最近 5 提交

- `a87ae50 docs(cb): EMC Harness 机制分析报告——vs codex 原生对照(三层定制无编排层·226s 思维链拆解·出图不符=工具契约缺口) + 改进建议`
- `9590b1e docs(todo): 周归档补账——08-03~08-23 三周 27 段入归档 + 08-25 收工 7 批成果同步 + 本周 3 段倒序收拢`
- `3121d83 docs(cb): 复测清单 7 项派发 prompt 落盘（发 Codex 执行·2026-08-26 home）`
- `722d212 docs: sync-log 5.128 Codex 配置隔离 + todo 08-26 段（冲突二次复发根治记录）`
- `ef93247 fix(codex): 配置隔离——harness 自备 CODEX_HOME 自愈生成(_codex_cwd/.codex·锁定 deepseek-v4-flash 不可切换·P2-4 环境变量切换退役) + emc required 迁出桌面 ~/.codex(备份 bak-20260826·二次复发根治) + models.json Deferred 补丁自动化 + ops 纪律3/§三改写 + 2 条单测(618+1 门禁绿)`
## 手写区（里程碑级阶段结束时按 docs/state-handoff-template.md 八字段手写·小批只跑生成器刷机器骨架·禁写密码密钥）
