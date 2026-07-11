# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月12日（收工） | 分支 `main`（与 origin/main 同步，无积压）| 本次 = 思考↔结论脱节修复(5.68) + 追问胶囊深色 UI + EMC 全面审查→Tier1 三项(DataEye/审查门重启/报告导出, 5.69)

---

## 当前节点：EMC 全面审查 + Tier1 已完+已推（待用户验 Tier1 + 推 Tier2/3）

### 背景
两段：(1) 修"思考↔结论脱节"（概念追问思考得结论、结论却被换缺数据卡）；(2) 全面系统审查 EMC 13 个端到端环节 → 用户选 Tier1 三项打包补"业界领先"差距。**承重全程未碰**（三态出口/视野-数据-结论同步/KDE cascade-exclude/4×5/对称拉伸/tip-popup/EMC 深色/网格视图配对）。

### ✅ 本会话已做（3 提交 5.68/5.69/胶囊，全部已推 origin/main 无积压）
- **5.68 思考↔结论脱节系统性修复**（`e65a3c0`）：审计整条决策管线→**只有一类病：gate 覆盖模型 deliberate 作答**。关键发现 `compressHistory` 传全 thought→finalStep 看得到思考→链本健全，脱节根因是 gate 跳 finalStep。三修：`_hardFail` 加 `answered`（deliberate answer 不当失败）+ `narratedAnswer`（**真凶**：概念问模型 prose 作答→叙述→原 degrade→GAP；改"叙述≠失败，交 finalStep"）+ diagnose 概念追问→general（即使含核密度/用地关键词）。实测"什么是核密度分析"修后出真结论（修前缺数据卡）。
- **追问胶囊深色 UI 修复**（`213b838`）：EMC 深色面板里白底+主题文字变量（翻浅）→浅字白底看不清；改半透明深底+浅字 `#ECECEC`+橙标签，对齐 welcome-chip/exit-badge。
- **5.69 EMC 全面审查→Tier1 三项**（`2363e4f`）：审计 13 环节（11 强/较全，4 差距：审查门关/自成长半残/DataEye 浅/LLM 脆弱）。用户选 Tier1：
  - **B DataEye**（[tools.js buildContext](frontend/js/ai_qa/tools.js) `_fieldSamples`）：层摘要 `字段名`→`字段=类型:2样本值`（`DLMC=str:商业`）。模型写 where 有真实值参照。
  - **A 审查门重启**（[harness.js REVIEW_ENABLED](frontend/js/ai_qa/harness.js) + [review.py](ai_qa/review.py)）：`REVIEW_ENABLED` true（`localStorage.emcReviewOff='1'` 杀开关）+ 聚焦客观项（data_driven/actionable/scale_paradigm_fit/professional fail 才强 fail；主观项 layout/concise/structure 只 warn，后端同步降级）+ C-only scope + **verdict 入 episode → 自成长闭环激活**。
  - **C 报告导出**（[panel.js _exportReport](frontend/js/ai_qa/panel.js)）：答案脚"导出报告"钮→自包含可打印 HTML（标题+时间+问题+答案[canvas→`toDataURL` PNG]+落款，CSS 藏 action 钮）→新窗 `print()` 存 PDF。实测 21.8KB HTML 含图表 PNG。
- **mapgpt-main 已删**（用户"go 删"，未入仓参考包）。

### 🔍 验证（Playwright，均已过）
parse 漂移 8/8（上轮）｜**思考↔结论**：概念问修后出真结论非缺数据卡 ｜ **DataEye**：buildContext 输出含 `DLMC=str:商业` ｜ **报告**：点钮生成 21.8KB HTML 含图表 PNG + 藏 action 钮 ｜ **追问胶囊**：computed style 深底浅字橙标 ｜ node --check/py AST 全过。审查门全 LLM 流程（Flash verdict→revise→episode）**待用户真问 C 类肉眼验**。

### ⬜ 下会话：先陪用户验 Tier1，再推 Tier2/3
1. **验 Tier1**（用户硬刷新，看右下 build 角标时间更新）：① C 类问（"哪些区域最差？为什么"）→ 看审查 verdict 区（✓/△/✕+评语）出现，pass=false 时 revise 1 轮；② 复杂筛选（"筛选 domain=治理 的负面点"）看 DataEye 提的命中率；③ 导出报告钮→PDF；④ 概念追问（"X 和 Y 区别"）不出缺数据卡。
2. **审查门是重启**（曾因"效果待优化"关）——若 Flash 审查噪/降质，console `localStorage.setItem('emcReviewOff','1')` 一键关，反馈后调 prompt/聚焦。
3. **Tier2/3 路线**（计划文件 + revision-log 5.69）：**LLM 韧性**（[llm.py](ai_qa/llm.py) 加 retry+fallback provider，DeepSeek 一挂全瘫是底线）→ **复合工具 compare/timeseries**（一次取数喂图）→ **自成长闭环接通**（[consolidate.py](ai_qa/consolidate.py) 提议→会话末 nudge/代审应用 L2，让 agent 真正越用越准）→ 主动建议 / 提速 / 多模态。

### 承重（必守，下会话续改 EMC 时留意）
- 图表/报告/用地色都是**纯增量**（新模板/后处理器/三处 addLayer 收口 paint），不动 map.js 渲染管线/极色色带。
- `panel.js` **不 import** map/state/panel 主窗口写函数（AI 子系统边界；报告 _exportReport 也只读 shell.answerEl + _history，不越界）。
- 审查聚焦**客观项**（主观项不强制 fail）；改色带离散分段；EMC 深色主题（chart/胶囊/报告按钮深色风）。
- start.bat 保持 ASCII-only；serve.py 的 no-store/?v/build-角标 勿退。

### 本轮改的关键文件（下会话续改看这些）
- 回答策略/思考↔结论：[harness.js](frontend/js/ai_qa/harness.js)（answered/narratedAnswer/REVIEW_ENABLED/C-only scope）/ [stages.js](frontend/js/ai_qa/stages.js)（parseAgentStep 抗漂移）/ [prompts.py](ai_qa/prompts.py)（概念追问→general + chart 指引）
- 审查/自成长：[review.py](ai_qa/review.py)（客观项聚焦）/ [episode.py](ai_qa/episode.py) + [consolidate.py](ai_qa/consolidate.py) + [wisdom.py](ai_qa/wisdom.py)（自成长三层，verdict 现有源）
- 渲染/UI：[panel.js](frontend/js/ai_qa/panel.js)（_renderCharts/_exportReport/_exitBadge/suggest/collapse）/ [tools.js](frontend/js/ai_qa/tools.js)（buildContext DataEye `_fieldSamples`/density/hotspot/landuseLayerPaint）/ [ai_qa.css](frontend/css/ai_qa.css)

### 承重 memory 索引
- 本轮相关：`emc-tri-state-exit-contract`（出口契约 + answered/narratedAnswer + **审查重启 C-only/客观项聚焦/自成长激活**）/ `emc-charts-and-end-to-end`（图表 + **DataEye 已完/报告已完/复合工具待做**）/ `view-data-conclusion-sync` / `design-language-consistency-iron-rule` / `verify-real-endpoint` / `maintain-revision-log`+`todo-revision-log-sync` / `no-handoff-on-routine-commit`（说"交接/收工"才覆写本卡）/ `chinese-all-deliverables`

## 新会话 prompt（复制即用）
见下方代码块。
