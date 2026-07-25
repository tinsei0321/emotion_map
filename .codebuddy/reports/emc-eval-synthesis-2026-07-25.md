# EMC "基本不可用" 根因合成报告（review + plan 合一）

> 评估人：K3 ｜ 2026-07-25 ｜ 方法：**静态评审**（代码事实 + 历史报告 + commit 链），不重跑测试（T7 干净基线待用户）
> 前置（本文在其上合成，非重做）：[emc-eval-report06-07-2026-07-24.md](emc-eval-report06-07-2026-07-24.md)（C1-C9 簇·相位差）、[emc-sys-improvement-2026-07-24.md](emc-sys-improvement-2026-07-24.md)（P0/P1/P2）、[test-flywheel-audit-2026-07-24.md](test-flywheel-audit-2026-07-24.md)（H1-H5）
> 行号以 2026-07-25 `main`（de660df）为准。测试原文：`tests/reports/report-2026-07-24-{04,05,06,07}-llm.md`。

---

## 一、总裁定（根因一段话）

**"相位差"只对了一半，须升级为"错位"：本体动了，但动的不是演示链承重墙。**

5.200-5.203 四批治本真实落地、代码可验（模型路由 `stages.js:251/296`、75s 预算 `harness.js:433`、gate 0.6 `harness.js:43`、假 GAP 三件套 `prompts.py:214` + `tools.js:560` + `harness.js:462-468`），06/07 两轮实测恰恰跑在含全部四批修复的系统上（07 sidecar commit=d706c2f）——但用户可见的两个 demo 断点 **C5（density 渲染）与 C6（工具认知）在该时点一行未改**（`map.js:685`、`paradigm.py:250/252` 原样，"密集"触发词在后端 prompt 层 0 命中）。**"基本不可用"的共性根因不是测量与本体的相位差，而是修复队列与演示链的错位**：队列按"失败模式分类学"（C1-C9 / P0-P2）排序，先修系统内部健康（信号/超时/假 GAP/数据洗涤）；demo 链按"用户 5 分钟看到什么"排序——渲染可见性 > 工具认知 > 分组/堆叠 > 超时。两个序列在四批里的交集恰好为空。两个放大器叠加：**基建噪声双向扭曲读数**（06 失败中 27% 纯错期望；07 表观 33% pass 全空心、有效 ≈0%）；**验证债务**（T7 干净基线从未执行，B1/R1 成效是 eval 代理指标上的断言，不是端到端事实）。

结论：**不修 C5+C6，EMC 不能 demo**——这两条是 demo 最高频路径的出口（热力图不可见）与入口（"密集"无路由）。修完 density plan 前 4 步（C5/C 分组/C6/B srcId）+ T9/T7 重跑，demo 链即通且首次可验证。真就是"执行 queue 里的 density plan 即可"；之前没执行到位的原因不是红线拦路（6 步中 5 步非红线），而是 plan 5.204 才定稿、且既有优先级框架（K3 P0 止血优先）天然把用户可见断点排在系统内部健康之后。

---

## 二、三层状态（量化 + 证据）

### 2.1 测量层（飞轮）：主干已接通，末梢四处半盲

| 信号/断言 | 状态 | 证据 |
|---|---|---|
| template 信号（H1） | **已通** | `panel.js` onDiagnose dispatch `diagnose:done` → `e2e-seam.js:62-65` chatPhases 读 `_testDiagnoseLog`；07 报告 tpl 列 7/9 非 `?`（04 时 6/17 为 `?`） |
| 参数断言（H3） | **已通** | test-cases.js PARAMS 断言接 sig.params 容差匹配（backlog 已修表） |
| JSON sidecar + run 元数据（H5） | **已通** | 07 含 commit=d706c2f |
| renderedNew 渲染断言 | **已通但语义失真** | `test-cases.js:28/48` source 差值计数，06 首战立功捕到 TOL-001/002/010；但 heatmap source 按 sourceKey **互斥替换**（`heatmap-tool.js:919-920` 先 remove 再 add），例间堆叠时差值可为 0 ≠ "未渲染" |
| polarity 五档（T1 后） | **已通** | `e2e-seam.js:104/117` 真数据 16933 行 5 档（Very Neg 6610 / Very Pos 4716 / Neutral 3810 / Neg 1203 / Pos 594） |
| s1 快败分支可见性 | **半盲** | s1 靠 badge 文本正则 `缺数据\|未产出\|需上传`（`test-cases.js:170`）二分，无 exit 字段直采——07 残余 4 例 s1 的真实分支（degraded diagnose / request_upload / ask_user）不可见 |
| 任务完成校验（T6） | **未做** | 07·INT-005 **零工具执行**仍判 OK（`tpl=multi tools=无`）——信号 pass ≠ 有效能力 pass 的活标本 |
| 参数序列化（T3） | **未做** | 05·INT-005/006 `区=[object Object]` |

### 2.2 测试基建：T1 已修，T8/T9/C7 残留；污染占比可估

**T1（5.203·6f880a7）已修**：pool `processed`→`performance`（`e2e-seam.js:104`）+ 文件名 `xiling_wujia`→`yichang` + dsvRows 解引号 + 五档极性。**T8（路径同源）症状已除、机制未建**：seam 仍硬编码 `'/DATA/performance/'`（:104），无单一事实源。**T9（例间清层）未做**：`test-cases.js:17-24` 每例 loadCSV 无清理 → `e2e_points` 每例 +3~4 层堆叠（`e2e-seam.js:36-56`），堆叠反向膨胀上下文加剧超时。**C7（夷陵资产）未修**：`test-assets.js:8` 仍描述"含西陵/伍家岗/**夷陵**等区"，而 `DATA/boundaries/行政区.geojson` 实测 9 feature = 龙泉/猇亭区/点军区/小溪塔/白洋/西陵区/龙泉绿心/伍家岗区/生物产业园，**无夷陵区**（本报告 PowerShell 解析复核）。

**06 工具（11 例 0%）噪声/能力分解**：

| 子集 | 例 | 性质 | 归因 |
|---|---|---|---|
| TOL-003/006/009 | 3 | **纯噪声**（27%） | C7 夷陵错期望——EMC 判缺**正确**，用例错 |
| TOL-004/005/011 | 3 | 真实缺口 + 堆叠放大 | C2/C6（"密集"无触发词）/C3 链式；T9 未做加剧 |
| TOL-001/002/010 | 3 | **真实缺口** | C5 渲染（见 2.3 机制二分） |
| TOL-007/008 | 2 | **真实缺口** | C2 语义桥缺失（错选 clip/extract_feature） |

→ **06 的 0% 中：~27% 纯基建噪声，~73% 真实能力缺口。噪声放大表观失败，但不构成主体。**

**07 意图（9 例 33%）分解**：3 个 OK 全空心（INT-005 零工具；INT-008/009 "哪里最差"只 clip 未 rank，`EXIT_RESULT newLayerCount>0` 放行，`harness.js:327/342`）→ **表观 33% 与有效 ≈0% 之差全部来自测量层（C8 空心断言）**；4 例 s1 快败（INT-001/003/004/006）+ 2 超时（INT-002/007）为真实失败（超时受堆叠放大）。

**新发现（本报告首报）**：stale 路径不止 seam——`time-source.js:20` `MANIFEST_URL = '/DATA/processed/_time_manifest.json'` 仍指向**已被用户本地迁移删除**的 `DATA/processed/`（本报告复核：目录不存在；`DATA/performance/` 下亦无 `_time_manifest.json`）。`loadManifest()` :32-35 fetch 404 → throw → **产品侧全局时间轴（时光叙事 F5）当前即坏**。T8"路径同源"的适用范围应从 seam 扩大到产品侧；manifest 再生成属数据红线，留用户拍板。

### 2.3 系统本体：两处动了（可验证），两处没动（demo 断点）

**动了①：5.201 模型路由/预算**——diagnose flash（`stages.js:236`）、final/revise 默认 flash（`:251` `ctx.answerModel || 'flash'` / `:296`）、复杂升 pro（`harness.js:459-460`）、gate 0.8→0.6（`harness.js:43`）、75s while-loop 预算守卫（`harness.js:433`）。
**动了②：5.202 假 GAP 三件套**——D2 可派生语义（`prompts.py:214`）+ D4 grounding 枚举 boundary 子要素（`tools.js:553/587`）+ D1 派生判定器（`tools.js:560` → `harness.js:462-468`，仅覆盖 `strategy==='request_upload'` 分支）。

**没动①：C5 渲染——机制二分（本报告修正 5.204 收敛）**。5.204 把"renderedNew=0"与"彩虹图不显示"当作同一机制（weight=0→透明），静态证据显示二者须分开：

- **weight 链（视觉不可见机制）**：`map.js:685` weightField 默认 `emotion_intensity` → `map.js:789-791` `buildWeightExpression` 缺字段走 `coalesce(..., 0.3)` → 有效权重 ~0.24 均匀低压暗（rainbow 色带低端近透明）。**但"数据缺该字段"只在手工构造 props 的路径必然成立**——`e2e-seam.js:116-122` 只写 polarity/score/text/domain/element 五字段（飞轮路径）；产品导入路径 `import.js:116/129/146` `properties: { ...r }` **保留全部 CSV 列**（L2 CSV 表头实测含 `emotion_intensity`），to-number 可转字符串 → weight 在产品导入路径**本应工作**。→ 用户#1"彩虹图不显示"的真因**未坐实**，候选：底图 key/Referer、z-order/互斥（`heatmap-tool.js:919-920,931`）、或用户数据走的正是丢字段路径。**5.204 plan Step1 的前提只对 seam 路径必然成立；weight 兜底修复方向仍正确（防御性），但 T12 二分应先于或与兜底同行。**
- **renderedNew=0（source 未注册机制）**：weight 不影响 source 计数；差值 0 的三候选——底图 style 未加载（飞轮环境天地图 404，`e2e-seam.js:31` 注释自承"底图 404 时永 false"）→ addSource 抛错被吞（`:37-39` safe() 仅护 loadPoints，工具路径 renderLayer 无 safe 包装但 `tools.js:1120` try/catch 吞成 _ERR）；同源替换（互斥 remove+add 净差 0）；测量基线取点。T12 二分待做。

**没动②：C6 工具认知——实锤三断**。①"密集"触发词在后端 prompt 层 **0 命中**（本报告 grep `paradigm.py`+`prompts.py` 复核；`:250` 触发词仅 核密度/密度分析/聚集强度/热力分布）→ TOL-004/005"哪里最密集"超时、TOL-007 错选 clip；②僵尸文案 `:252` yields 仍写"规则方格面网格"，而实际 `tools.js:1112-1136` 已委托 Toolbox 彩虹热力/网格/地形（`heatmap-tool.js:898` generateHeatmapForAI）→ 文档漂移喂给 LLM 错误产物预期；③Toolbox heatmap/grid/terrain 三能力未入 GEO_TOOL_CATALOG（`:170-255` 无条目）→ "不支持热力聚合"幻觉（06 用户亲见）。附带：EMC density 硬编码 `weightField: ... || 'emotion_intensity'`（`tools.js:1133`）——与 C5 同一扳机。

---

## 三、5.200-5.203 成效审计（逐批：打磨测量 vs 动本体）

| 批次 | commits | 治哪个簇 | 性质 | 对**有效 pass** 的贡献 | 副作用 |
|---|---|---|---|---|---|
| 5.200 P0 安全 | 89d7d70 / ed1d97f / 4a01052 | E6 滚动 / E3 堆叠 / density 信号 | **打磨测量 + 外围 UX**（零承重） | **0**（能力未动）；1c 让 06 首次可观 density 触发（测量增益） | srcId 只修导入半链（`main.js:79-139`）；工具产物层未修（`tools.js:320-322` 按名去重、`:654` 无去重）——用户#3 点名两次只闭合一半 |
| 5.201 B0+B1 | a93ce67 / a96bfea / d2cd5be / 78395c6 / 1e49182 | C9 超时 / E9 词表漂移 | **动本体**（harness 承重，eval-first 合规：83%→91%） | **方向存疑的正贡献**：超时率 report-01 14/15(93%) → 04 10/17(59%) → 07 2/9(22%)；t_p50 91→70s。但部分改善来自**"快完成（空心）替代长超时"**——gate 放松 + templatePath 短路使"哪里最差"类任务单 clip 即 EXIT_RESULT（07·INT-008/009 vs 04 同题超时） | **空心完成被制度化**：C4 假完成从 bug 变成默认路径；回答变浅 |
| 5.202 R1 | f1ee84a / 83b073b / f77129b / 37568f8 | C4 假 GAP | **动本体**（diagnose prompt 红线，eval-first 合规：25/27=93% 不退化） | **未证实**：04→05 s1 构成变化（6 例纯 GAP → 5 例中 2 例带工具执行）是弱证据；07 仍 4/9 s1——D1 只盖 `request_upload` 分支（`harness.js:462`），degraded diagnose（tpl=?）与 ask/空结果分支不在覆盖内 | 无回归（eval PASS）；但**T7 未跑，R1 成效是断言不是事实** |
| 5.203 T1+UX | 6f880a7 / 9fe6521 / bc62e72 / 284ae94 | Q1 seam / UI / 文风 | **打磨测量 + 外围 UX**（3c 触 final prompt 但保守） | **0**（能力未动）；T1 解锁极性评估真实性——后续一切涉极性结论的前提 | 04/05 涉极性例结论作废（自我声明）；测试 CSV 默认常量 `test-cases.js:8-10` 仍写 `xiling_wujia_*`（向后兼容路径，未随 T1 更新，低危漂移） |

**逐批诚实区分小结**：四批中两批（5.200/5.203）纯打磨测量与外围，两批（5.201/5.202）真动了本体且红线纪律全程合规（eval 先冻结后改、每子步独立 commit、pytest 203 pass 基线稳）。用户"基本不可用、测试全失败"的观感与"四批治本"并存的原因：**不是改动无效，也不是全被噪声掩盖，而是改动落点与用户痛点的交集为空**——用户 5 条投诉（#1 彩虹图 / #2 分组 / #3 堆叠 / #4 密集→clip / #5 "不支持热力"）无一在 5.200-5.203 的射程内，全部落在 5.204 才定稿的 density plan 里。改对了"病"，没改"疼"。

---

## 四、根因研判（压力测试"相位差" + 假设 a-e 裁定）

**"相位差"不是托辞，但不充分。** 它正确描述了 06-07 报告时点之前的状态（测量层进展 vs 本体未动），但 5.201/5.202 已触本体后，"本体未动"不再成立；真正没过时的部分是"基建污染"。本次修正为三层判词：**本体已动两处（路由/假GAP），但有效能力在 demo 链上未见提升——因为动的不是 demo 链断点，且已动部分的成效从未被端到端验证。**

| 假设 | 裁定 | 证据与理由 |
|---|---|---|
| (a) 基建噪声掩盖真实能力 | **次要（~25-30%）** | 06 的 27%（3/11 夷陵）纯噪声 + 超时受 T9 堆叠放大；07 表观 33% 全为空心失真。但清完全部噪声后 06 仍 8/11 真实失败——噪声扭曲读数，不制造失败主体 |
| (b) 核心能力真实缺口（C5+C6 未修 = 演示链断裂） | **主因** | demo 最高频两动作（"看密度/哪里密集"→热力图）入口出口双断：入口"密集"0 触发词（`paradigm.py:250`），出口 weight 压暗（`map.js:685/791` + `tools.js:1133`）。用户 5 投诉中 #1/#4/#5 三条落此 |
| (c) 架构/内核不匹配（Smart-Agent-Dumb-Tool + eval-first + 承重三不动 → 修复速度 < 退化速度） | **非根因（但有一处真实代价 + 一处排序失灵）** | 红线纪律 4 批零回归（eval 93%、pytest 203 pass）；C5/C 分组/B srcId/T9/C7 **全非红线却未被执行**——不是红线挡路。真实代价 = B1"保必有回答"以变浅为代价（空心完成制度化）。排序失灵 = P0/P1/P2 按系统内部健康度排（超时>信号>渲染），demo 链按用户可见排（渲染>认知>超时），**缺一个演示链视角的优先级裁定者**——这是流程的产物，但根子不是承重结构 |
| (d) 数据/资产问题 | **次要** | 夷陵缺 = 用例错非系统错（EMC 判缺正确）；L2 CSV `score` 与 `emotion_intensity` 双列并存 + 前端归一只消费 score（`import.js:642`）= C5 扳机的半个成因；**新增**：数据迁移删 `DATA/processed/` 致 `time-source.js:20` manifest 404——时间轴产品侧即坏（d 的最新成员） |
| (e) 其他（本报告提出） | **验证债务 + 演示链视角缺席（与 b 并列的机制性根因）** | 每批结尾"待用户跑飞轮验证"，T7 干净基线从未执行 → B1/R1 成效停留在 eval 代理指标；飞轮的闭环最后一公里（重跑）挂在用户身上。**这解释了"为什么改了 4 批用户仍觉得没起色"——连"起色是否发生"都没有被测量确认过** |

**共性根因一句话**：EMC"基本不可用" = **演示链断点从未进入已执行批次**（排序错位，b+e）+ **已执行批次的成效从未被端到端确认**（验证债务，e）+ **表观读数被基建噪声双向扭曲**（失败放大 27%、成功注水 33%→0%，a）。架构与红线无罪（c 不成立）；数据是帮凶不是主谋（d）。

---

## 五、关键路径计划（基本不可用 → 业内同行可 demo）

### 5.1 最小修复集（不修就 demo 不了 vs 噪声/可延后）

**关键路径（最小 demo 集）**——目标：5 分钟 demo 跑通「问密度→出可见彩虹图→问哪里最差→出排序→图层归组不堆叠」：

| 序 | 项 | 簇 | 内容 | 红线 | 量级 |
|---|---|---|---|---|---|
| 1 | **C5 渲染二分+兜底** | C5 | T12 二分（产品路径复现"彩虹图不显示"：底图/z-order/weight 三选一）+ `map.js:791` weight 缺字段兜底（回退 `score` 或 uniform 1.0）+ renderLayer 容错+落图核验 | 否 | 0.5-1 天 |
| 2 | **C6 工具认知** | C6/C2 | `paradigm.py:250` 触发词加"密集/集聚"+`:252` 僵尸文案改委托实况 + Toolbox heatmap/grid/terrain 收编 catalog + `tools.js:1133` weightField 默认对齐数据实况 | **是**（diagnose prompt→eval-first；eval 已冻结 25/27=93%，成本=一次重跑） | 0.5-1 天 |
| 3 | **C 分组** | C 分组 | `state.js:867` categoryOf 加 parentId 短路 + density/grid 入口传 parentId（`heatmap-tool.js:921-926` 现无） | 否 | 2 小时 |
| 4 | **B srcId 工具层** | B | `_contentSig` 抽共享（`main.js:86`）+ `tools.js:320` addResultLayer / `:654` _registerToolboxLayer 按 srcId 去重 | 否 | 0.5 天 |
| 5 | **T9 + 时间轴路径 + T7 重跑** | C1 | test-cases.js 例间清层；`time-source.js:20` manifest 路径同源（用户拍板 manifest 再生成）；全量重跑 04-07 → 干净基线 | 否（manifest 再生成=数据红线，留用户） | 0.5 天 |
| 6 | C7 夷陵资产 | C7 | `test-assets.js:8` 描述改正 + 用例期望改"真缺口精确说明" | 否 | 1 小时 |

**噪声/可延后（第二环及以后）**：D3 链式模板（治 TOL-004/005/011、INT-002/007 残余超时——demo 加分项，"哪里最差"真出 rank）→ T4 胶囊矛盾（`panel.js:816` default ready 消灭）→ T6+T3（空心 OK 灭绝 + 参数序列化）→ T5 对比 C 键 → P1 manifest/SOP 卡/异步 review → P2 全部。

### 5.2 与既有计划对账

- **density 6 步 plan**（`~/.claude/plans/emc-gis-rippling-dream.md`）：与本最小集**完全重合**（C5/C 分组/C6/B/T9/C7），顺序维持原 plan（Step1 C5 → Step3 C 分组 → Step2 C6 eval-first → Step4 B → Step5/6）。本报告唯一修正：**Step1 前提"数据缺该字段"只对 seam 路径必然成立，T12 二分须并入 Step1**（避免兜底修完产品路径仍不显）。
- **P0**（emc-sys-improvement §4.5）：5 项全部已做或在做（滚动复位/srcId/模型路由/EMC-SUM/词表收编）——P0 关闭。
- **P1**：仅"SOP 卡"与 C6 相邻可随行；manifest 管线、异步 review 延后（不挡 demo）。
- **05-llm 遗留** T4/T5/T6/T3/D3：全部第二环，无一在 demo 关键路径。
- **验证债务清偿**：T7 重跑并入第 5 项——这是四批治本首次接受端到端裁决。

### 5.3 本周（5.204 起）3-5 件事（依赖序）

1. **C5 二分+兜底**（非红线，用户#1，最大见效）——上午能开工，当天出结果。
2. **C 分组 + C7 资产**（非红线，最便宜，用户#2 + 用例真相）。
3. **C6 工具认知**（eval-first：冻结→改 prompt→重跑 eval→飞轮验"密集"→density 端到端肉眼验；用户#4/#5）。
4. **B srcId 工具层**（非红线，用户#3 后半链）。
5. **T9 + time-source 路径 + T7 全量重跑**（偿验证债务，出干净基线报告——此后所有 pass 率以新基线为准）。

### 5.4 红线 × 速度建议

**不建议解锁任何承重点**（diagnose prompt / harness orchestrate / ChatRequest 三不动维持）。承重三不动的成本被高估：C6 是唯一红线项，eval-first 的实际成本 = 一次 `eval_template_flash.py` 重跑（分钟级），且 5.201/5.202 已两次走通该流程无退化。真正建议放宽的是**"每次只改一处"的串行粒度**：从"会话级串行"放宽为"**红线串行 + 非红线并行批**"——最小集 6 项中 5 项非红线（C5/C 分组/C7/B/T9）可同一批做完一次 commit 串，C6 单独走 eval gate。**速度瓶颈从来不是红线，是 plan 定稿后空转一个会话未动工。**

---

## 六、风险/未决

1. **R1 残余 s1 分支未定性**（07 4/9：INT-001/003/004/006）——D1 只盖 `request_upload`（`harness.js:462`），degraded diagnose（tpl=? ×2）与 ask/空结果分支未覆盖；T7 重跑后若 s1 仍在，扩 D1 覆盖面（5.205 候选）。
2. **C5 产品路径真因未坐实**——weight 机制仅 seam 路径必然成立（产品导入 `import.js:116` 保留 emotion_intensity）；用户#1 的复现环境与数据路径未知，T12 二分是 Step1 前置。
3. **时间轴断裂（本报告首报）**——`DATA/processed/` 已删（用户本地迁移，未 commit）→ `time-source.js:20` manifest 404 → 时光叙事产品侧即坏；`DATA/performance/` 无 `_time_manifest.json`，再生成属数据红线，**留用户拍板**；代码侧路径同源随行第 5 项。
4. **renderedNew 断言语义**——同源替换场景差值失真（`heatmap-tool.js:919-920`），T9 清层后复核；必要时改存在性断言。
5. **空心完成制度化**——B1 用变浅换超时（07·INT-008/009 clip 即过）；解药 P1-4 落图自检 + T6 完成校验在第二环，未治前"信号 pass 率"不可作为能力指标引用。
6. **test-cases.js:8-10 默认 CSV 常量**仍 `xiling_wujia_*`（向后兼容文件名，T1 后低危漂移，随行清理）。
7. **夷陵区数据是否补**——产品决策，非代码问题；不补则 C7 用例期望须永久改"真缺口精确说明"。
8. **DATA 迁移未 commit**（`DATA/processed/` 删除 + `DATA/performance/` 新增 + `DATA/old_data_processed/`）——用户本地操作，数据红线，本报告不碰。

---

## 附：证据锚点速查

- 本体（已动）：`stages.js:236/251/296`、`harness.js:43/331-333/432-433/459-468/513-515`、`prompts.py:192/214/229`、`tools.js:553/560/587`
- 本体（未动）：`map.js:685/789-791`、`paradigm.py:250/252`、`tools.js:320-322/654/1133`、`state.js:867-870`、`panel.js:816`、`heatmap-tool.js:899/919-926`
- 基建：`e2e-seam.js:31/36-56/62-65/104/116-122`、`test-cases.js:8-10/17-24/28/48/170/196`、`test-assets.js:8`、`time-source.js:20`
- 数据：`DATA/boundaries/行政区.geojson`（9 feature 无夷陵区）、`DATA/performance/yichang_L2_T1_L2_result_csv.csv`（表头含 score+emotion_intensity 双列，16933 行 5 档）、`DATA/processed/`（已删）
- 报告：`tests/reports/report-2026-07-24-04-llm.md`（6%·commit 58716bb·B1 后）、`-05`（18%·pre-T1）、`-06`（0%·工具）、`-07`（33% 空心·commit d706c2f）
- commit：5.200=89d7d70/ed1d97f/4a01052；5.201=a93ce67/a96bfea/d2cd5be/78395c6/1e49182；5.202=f1ee84a/83b073b/f77129b/37568f8；5.203=6f880a7/9fe6521/bc62e72/284ae94；HEAD=de660df
