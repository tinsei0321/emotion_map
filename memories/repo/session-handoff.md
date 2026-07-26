# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月26日收工（**toolbox 验收 + EMC 大收敛 5.206**）| 分支 `toolbox-unified-toolset` | 本次 push

## 当前节点：toolbox 验收通过待合并 + EMC 大收敛 5.206 落地，下会话推进专题 D/E（红线 eval-first）

今日（07-26）做 toolbox 工程验收 + EMC 大收敛批次。**toolbox 工程验收通过（建议合并·暂缓）**——三件套本机复现全绿（obs diff 0/12 + unified ALL-PASS + pipeline ALL-PASS）+ 静态 A-E 全过 + 4 裁决（§7-4 互斥扩集接受 / M6 color 判据接受 K3 修正·评审 distance 失误自认 / §6-7 area_stats 接受 / §7-3·§7-5 遗留）。EMC 大收敛 5.206 落 4 代码 commit + 文档 sync + 全盘点 18 项（不遗漏）。

## 今日已 commit（5.206 · revision-log §5 · branch toolbox-unified-toolset）
- **547a334** 验收报告（`.codebuddy/reports/toolbox-unified-acceptance-2026-07-26.md`·建议合并）+ 步 1 `_contentSig` 统一（main.js import shared.toolContentSig·消重复）
- **3d1e12b** 步 2 T3 参数序列化（治 `[object Object]`）+ T6 hasAction 门控（灭绝空心 OK·C8）
- **1fb9dfb** 批次 A T4 胶囊矛盾（panel.js:816 strat 缺省 unknown·治 05-llm Q2）+ T5 对比入口收敛（time-bar 无焦点提示 + main.js 'c' 键注释）
- **62f25e7** 批次 C D1 扩覆盖（harness.js:462·deriveAvailable 扩 request_upload + strategy 缺失·治 s1 残余 INT-003/004/006·eval 25/28=89% 不退化）
- **aa61ca0** docs sync（revision-log §5 5.206 + todo 2026-07-26 当日段）

## 下会话执行：专题 D/E（红线 eval-first · 后续会话各个击破）

**plan 文件**：`~/.claude/plans/plan-claude-plans-emc-gis-rippling-drea-whimsical-lobster.md`（全盘点 18 项 + 专题 D/E 计划·不遗漏）。**先读它 + `git log --oneline -8` 对账 5.206**。

- **专题 D diagnose 认知深化**（eval-first）：D1 SOP 卡扩字段（GEO_TOOL_CATALOG paradigm.py:170-255 加 scale/preconditions/failure_modes/examples·降 eval 3 MISS 路由歧义）+ D2 method→tool 确定性映射 + D3 EMC-SUM 摘要 method/plan 采集（domain_lens threading 5.108 范式·不改 ChatRequest schema）。
- **专题 E harness 承重**（eval-first）：E1 D3 多步链（CHAIN_REGISTRY + runChainPath + orchestrate :513 分流·0 中间 LLM 轮·治 C3 残余超时）+ E2 P0-4 进度透明（SSE 阶段时间线 + 增量落图 + 可取消·治 C9）+ E3 P1-4 partial 出口裁定（EXIT_RESULT :327/:600 + addToolboxLayer _renderState 联动·治假完成制度化）。
- **建议序**：D 先（SOP 卡改善路由·eval gate 已稳 89%）→ E（harness 大专题·每子步独立 commit）。

## 留用户验证 / 未决
- **T7 飞轮全量重跑**（`?test=1`·04-07 干净基线·首次端到端裁决·验 D1 s1 收敛 + T4/T5 效果 + T6 灭绝空心 + 干净 pass 率）。
- **toolbox 合并**（验收通过·暂缓·用户定时机 merge `toolbox-unified-toolset` → main·20 commits）。
- **manifest 再生成**（time-source·DATA/performance/_time_manifest.json·数据红线·时光叙事 F5 产品侧恢复）。
- **DATA 迁移 commit**（processed→performance·用户本地未 commit·数据红线）。
- **CPD predicates failing 另案查**（test_cpd_predicates inject_points 后 wait_predicate 超时·pre-existing 嫌疑·K3 §7-7 称未跑·与 toolbox 改动面正交）。

## 红线 / 纪律（下会话守）
- **承重三不动**：diagnose prompt（prompts.py build_diagnose_prompt）/ harness orchestrate（harness.js orchestrate 主循环）/ ChatRequest schema（schemas.py）—— 改前先扩 eval，每次只改一处，不派 subagent（承重走主线程）。
- chain_id/method 走 domain_lens threading 不改 schema；后端零改动；不改 SKILL_DEFS/TEMPLATE_REGISTRY；禁 emoji（[OK]/[ERR]）；不动归因占位；依赖单向不破。

## 恢复指引（新会话）
1. 读 plan（`~/.claude/plans/plan-claude-plans-emc-gis-rippling-drea-whimsical-lobster.md`）+ `git log --oneline -8` 对账 5.206（547a334/3d1e12b/1fb9dfb/62f25e7/aa61ca0）。
2. 读验收报告（`.codebuddy/reports/toolbox-unified-acceptance-2026-07-26.md`）+ K3 完成报告（`toolbox-unified-completion-2026-07-26.md`）+ 手册 v2.2。
3. 选专题 D 或 E 起（用户定优先级·建议 D 先）。
4. eval-first：先扩 eval → 冻结基线 → 改 → 重跑验不退化（≥89%）。
5. 承重三不动 / 每次只改一处 / 不派 subagent。
