# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月02日（**CB-11 只说不做根治 + merge 多图层 + 待续项推进**）| 分支 `fix/emc-buglog` | **已 push**
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md` + `OFFICE.md`

## 当前节点：CB-11 闭环 + merge 多图层 + 「剪裁+合并」只说不做根治 → 待续项

今日（08-02）：用户实测「剪裁+合并」类问题 → Codex + glm组 双评估 → 根治「只说不做」复发（R9 防线 + 两阶段补全）+ merge 多图层 concat + 待续项推进。**用户自测成功 ✓**。

## 今日已 commit（fix/emc-buglog · **已 push**）

| commit | 内容 |
|---|---|
| `9f84eac` | **merge 多图层 concat**（Codex+glm 方案 A）：后端 `MergeRequest.layers` + concat（CRS 统一 + `_source_layer`）+ 契约 layers + one-of 校验 + union 链退役 |
| `bea7cbd` | 验收修复 P1-P6（inline `_tcs is not iterable` / auto-merge 未调 `onFinalDone`「卡读秒」/ alias 解析 / `_source_layer` 语义 / layers 字符串防御） |
| `eb42d39` | **「剪裁+合并」只说不做根治**（Codex+glm 共识）：R9 步骤描述对账（防线结构性洞）+ 两阶段补全（先裁剪再合并）+ merge observation 来源标注 |
| `fc242c2` | hover 层存在性 guard（`lyr-Lxxx-line` 报错） |
| `679191f` | clip-then-merge 偶发多 1 个 overlay（`runAllToolCalls` 补 `_inlineExpanded`·防双执行） |
| `40a518b` | G5 命中遥测 localStorage 持久化（`emc_completion_hits_v1`·驱动渐进退役） |
| `c788114` | 族 D 面层多类用地分段色（merge 产物按 DLMC 数据驱动·严格按图例） |
| `c973576` | 文档同步（todo/revision-log） |

## 关键架构（下会话须知道）

- **主通道 A 定型**：LLM 多 call=机会通道 / 单 call+内联扩展=常态主通道 / `_deterministicRecover`=失败兜底；B（prompt 促多 call）降级为模型换代后评估项
- **「剪裁+合并」两阶段**：`buildLanduseCompletion` 问句含「裁剪+合并」→ 先 overlay(intersection)×N 裁剪 → merge 裁剪产物（`$n` 引用）·走 `runAllToolCalls`（处理 `$n`）
- **R9 防线**：applyQualityDefense 结论操作动词 → 对账 toolHistory 工具集·未执行标注（防「只说不做」复发·结构性洞）
- **merge 多图层**：`merge(layers=[...])` 后端 concat（保留 DLMC·无字段后缀）·overlay union 是空间并集勿代替
- **词表集中**：`emc-patterns.js`（LANDUSE_KW/DOMAIN_KW/POLARITY_KW/意图词）
- **样式契约**：点层 clip 继承源 colorMode（5 级极性图例）·面层用地 `landuseLayerPaint` 国标色 + 多类 `landuseFillColorExpr` 分段色

## 待续项（下会话从这继续）

- **触发入口统一**（glm组 P1）：`buildLanduseCompletion` 内置触发判断·调用方不再各自写正则（inline/autoExpand/recover 三套触发条件）
- **PRM 参数填充瓶颈**（CB-08 F3.1）：zonal/buffer 边界参数·B3 飞轮 10 例 fail
- **CPD-L01/L02**（既有 CPD 问题·defer 表 `_deferred.md`）
- 已知小瑕疵：合并结论「未实际生成」措辞残留（LLM 措辞·非功能 bug）
- 时间轴 `_time_manifest.json` 404（低风险·待时间轴开发补）

## 测试基建

- pytest：**223 passed**
- 飞轮：`py tests/browser/flywheel_audit.py --tier smoke`（每次 commit）/ `--tier full`（发版）
- 浏览器复现脚本：`py tests/browser/test_p0_repro.py --case B002|B005|B003|B006` + 合并用例（手动 Playwright 内联）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前 CB 轮次：CB-11（merge + 只说不做根治·已闭环）· 下一轮 CB-12（待修复后验证）
- **双阵营**：claude组（Claude Code + DeepSeek/GLM 5.2·开发主）+ Codex + glm组（ZCode + GLM 5.2·评估）
- 反评价轨迹：`docs/catch-ball/cb-journal.md`（CB-10/CB-11）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema（改前先扩 eval·每次一处）
- **EMC 产物不临时创造样式**——有固化图例用图例·无则 defaultPaint（族 D 红线）
- **不动 FC prompt**；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**（uvicorn 无 --reload）
- commit 后不 push（用户手动 push·CLAUDE.md 例外时用户说 push）

## 恢复指引（新会话）

1. `git log --oneline -8` 对账（最新 `c973576`）。
2. 读本卡「关键架构」+「待续项」。
3. 读 `docs/todo.md` 08-02 段 + `docs/revision-log.md` §5 最新。
4. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
5. 从「待续项」继续（建议先做触发入口统一·低风险）。
