# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。

---

## 📅 2026-07-24（分支 `main` · 测试飞轮机制评估）

### ✅ 测试飞轮两批修复入库 + EMC 治本 backlog 起步（revision-log 5.199，commit a90fac1 · **用户手动 push**）

- **入库两批**（13 文件）：批1 信号链 H1(template 信号·治 C1 断链)/H3(参数断言硬化)/H5(JSON 报告)/EMC-SUM v1；批2 覆盖 A(字段识别扩容)/B(摘要中文)/C(渲染断言)。已验证 H1 生效（TOL-001 template=density 非 null）+ pytest 203 pass。
- **治本 backlog** [emc-fix-backlog.md](emc-fix-backlog.md)：6 类问题（超时/density信号/选错工具/字段manifest/渲染bug/摘要）+ 证据 + K3 P0/P1/P2 方向。
- **纠正 K3 过时认知**：diagnose 已跑 flash（stages.js:236）；超时真因 = agent 多轮 + final/revise pro 串行（非 diagnose）。
- **P0 切分（用户拍板·安全 3 项优先）**：模型路由(超时#1·harness 红线)单列独立 plan + 先扩 eval；本批先做安全 3 项——🔄 滚动复位(1a)/🔄 srcId 去重(1b)/🔄 density 执行信号(1c)。
- **承重零触**（diagnose prompt / harness orchestrate / ChatRequest 三承重不动）。

### ✅ 测试飞轮全面评估（静态审查·用户指示跳过实测）

- 产出：[test-flywheel-audit-2026-07-24.md](test-flywheel-audit-2026-07-24.md)（总评 5.1/10；机制事实清单 + 三维度不足 + 业界对照 + H/M/L 优化清单 + Prompt 预设调整专章）。
- **三处闭环断裂石锤**：① template 信号断链（ChatRequest 无 diagnose 字段，schemas.py:11-22 → 意图断言 `tmplOk` 永 false，tpl=? 根因）；② 词表三处硬编码漂移（prompts.py:190 缺 compare/filter_attr vs paradigm.py:454/470 决策树 vs 飞轮 expectTmpl）；③ 投票不落盘 + 失败不回流 prompt 池（闭环断在"报告"处）。
- **覆盖假象**：参数正确性 10 例断言恒 pass（expect* 定义未接断言，test-cases.js:276-279）；全正模式零负例（八原则反模式无一落地）；时序 T1-T3 / POI 缓冲零用例。
- **优化清单**：H 级 5 项（信号接通/词表单源/断言硬化/反馈落盘/JSON 报告）+ M 级 8 项 + L 级 5 项；Prompt 专章 P1-P5（负例池/时序变体/POI 变体/词表派生/失败回流五环）。
- 留痕：实测驱动 `tests/browser/flywheel_audit.py` 已建（三路采集，未跑）；本机 Playwright chromium 待装（cdn 慢，可配镜像）。

### ✅ EMC×飞轮 系统性改进方案（四问咨询答复）

- 产出：[emc-sys-improvement-2026-07-24.md](emc-sys-improvement-2026-07-24.md)——证据基线 11 条（E1-E11 挂行号）+ 四问方案 + P0/P1/P2 路线。
- **Q1 摘要格式**：EMC-SUM v1（3+1 行·键值定序）——单例记数/占比上浮批级；新增 tmpl 维度与耗时/调用列；judge 分误杀/漏判；同 schema 双渲染（测试报告+产品回答页脚）。
- **Q2 文件与交互**：① 去重根因=`addLayer` 零去重（state.js:667）→ srcId 指纹三态策略（复用/覆盖/并存）；② 字段识别→Layer Manifest 三级管线（嗅探→字典 core/field_dictionary.py→LLM 兜底按 srcId 缓存）+ 低置信确认向导；③ 滚动根因=`_userPinned` 发送新问题时**不复位**（panel.js:1535/1547）→ 新话轮强制跟随。
- **Q3 失败剖析**：超时=串行多 Pro 管道（report-01 14/15 超时石锤）→ 预算制+模型路由+进度透明；数据碎片化→Dataset Registry+预检喂 diagnose；推理链断裂→Tool SOP 卡+method→tool 确定性映射（QGIS Processing 描述符模式）；以图说话→10 工具成图范式+落图自检+回答图层芯片。
- **Q4 体系化**：LLM 网关/异步任务/Artifact Store/上下文编译器；episodes 重放 golden set；路由模式分流；红线=涉 diagnose/出口/harness 改动先扩 eval。
- 落地顺序：先审计报告第一批（H1/H3/H5），再接本方案 P0（共享"词表收编"项）。

### ⬜ 待用户拍板（评估优化项，按报告 §六路线）

- [ ] 第一批：H1 接通 template 信号（触 ChatRequest schema·需拍板）+ H3 参数断言硬化 + H5 JSON 报告
- [ ] 第二批：H4 反馈落盘+backlog + H2 词表单源 + M8 遥测连通
- [ ] 第三批：P1 负例池 + M2 批级 setup + M3 分层抽样 + M5 时序/POI
- [ ] 第四批：M7 catalog 登记 + M4 聚类 diff + L 级抛光
- [ ] 改进方案 P0 五项（滚动复位/srcId 去重/模型路由+预算/EMC-SUM v1/词表收编）——与第一批有依赖交叉，拍板时一并定序

---

## 📅 2026-07-23（分支 `main` · cpd 合并清理 + 测试飞轮 v3→v4 + _fill 修复 + todo 机制反思）

### ✅ 分支收敛（cpd → main）
cpd 分支（~60 commit：CPD 引擎 + EMC v1.4-1.6 + 测试飞轮 v1-3）fast-forward 合并进 main，历史线性；删 cpd 本地+远程 + `backup/pre-forcepush-9be02c3`（9be02c3 未合并，用户确认弃）。仓库收敛为单 `main`。

### ✅ 测试飞轮 v3（行内摘要+工具标注+固定位置报告+一键启动）（revision-log 5.196 · commit b63acca）
行内摘要（工具类显 tool 名·fetch 拦截 /geo /spatial 端点抓）/ 重跑 R 修复（批量中先停再重跑）/ 报告落盘 `tests/reports/`（serve `/_test/report`）/ `start.bat --open=both` 一键开主页+测试页。

### ✅ 测试飞轮 v4（方向纠偏 + 意图/工具各 100）（revision-log 5.197 · commit 89c6a31）
**意图识别 = NL→工作流转译**（断言 template+工具，非回答文本）；DATA 资产系统 `test-assets.js`（语义清单自动加载，不再让用户补范围）；意图 100 + 工具 100 生成器（270 总·≤2 工具≤4 步·针对性）；slider 默认 25；存报告覆盖确认；按钮状态机（停止↔重新开始）。用户重组 boundaries（presets/→顶层）一并修。

### ✅ _fill 中文占位符修复（revision-log 5.198 · commit 524305d）
根因：`_fill` 正则 `\w`=[A-Za-z0-9_] 不含中文 → `{区}`/`{要素}` 全未替换（200 例 prompt 失效·语法绿·仅输出扫描查出）；全局审查 4 文件正则仅此一处同类；修 `[^}]+`，270 例 0 残留；memory `js-regex-word-chinese-trap` 防复发。

### ✅ 测试报告入库（commit 81288aa）
`tests/reports/`（3 份报告）纳入 git 同步（换环境要用，勿 gitignore）。

### 📝 todo 机制反思（本日最大教训）
用户多次报"todo 不更新"，我乱找方向（TodoWrite 工具 → .workbuddy），**真 todo = 本文件 docs/todo.md**——我只更了 revision-log/handoff，**漏同步 todo.md** → 停在 07-22。
- 教训 1：同步须 **todo.md + revision-log 一起**（记忆 `todo-revision-log-sync` 早有，我没守）。
- 教训 2：诊断"不生效"先问用户"你看到什么内容"定位，别反复换工具瞎试。
- 清理：删 `.workbuddy/`（第三方工具 memo，与 claude code 无关）。

### ⬜ 下一步
- v4 实测：跑 LLM 例（slider 25 起）收转译断言失败 → 调 INTENT/TOOL prompt 池提 pass 率
- C grid 独立 skill（中期·前后端 paradigm 同步）/ D method 标准化（远期·需拍板·触 diagnose 输出）

---

## 📅 2026-07-22（分支 `cpd` · CPD 核心 plan **v1.0 定稿** + CB 专轨收敛 + EMC 浮窗交互）

### ✅ CB-CPD-03 双模型三轮 → v1.0 定稿（CB-CPD 专轨收敛）（revision-log 5.175 · commit bc5c5ee · **待用户 push**）

DeepSeek + K3 三轮验证 v0.4（报告 `SCAN_CPDPlan_03-{deepseek,k3}.md`）。

- DS 综合 A- 建议收尾；**K3 发现 v0.4 新引入 H1 链式缺陷**——general 短路 × `exit!==undefined` 守卫 × 严格 turnId+1 去重 → 引导永久冻结静默失败（已核实 panel.js:1161/1181 链）。
- 修 v1.0：① H1 dispatch 守卫→`settled` + 去重→单调递增 + `exit??null`；② M1 row 4 `hasAnalysis=true` 升级 `interpret`（dock→EMC 桥）；③ M2 hasVisibleEmotionLayer 谓词收紧 +判情绪性；④ L1 U8 改 `#param-panel.is-open` 同步谓词。
- **CB-CPD 专轨收敛**：三轮双模型闭环（v0.1→v1.0），核心 6 决策全自洽，演示 C+→B+，承重零触。
- **下一步**：P0 测试铺底 → P1 尺度诚实 → P2 引擎 G1-G4。

### ✅ CB-CPD-02 双模型二轮验证 → plan v0.4（revision-log 5.174 · commit a572ad8 · **待用户 push**）

DeepSeek + K3 二轮验证 cpd-core-plan.md v0.3（报告 `SCAN_CPDPlan_02-{deepseek,k3}.md`）。

- **首轮建议全执行**（DS 12/12、K3 15/15），v0.3 升 **B+**（两份一致，v0.2 B-→B+）。
- **两份独立收敛 2 高优**（高置信）：① init 循环 import → 依赖注入（panel.js→cpd-guide.js 单向）；② S4 动态变量无源（X×Y/N）→ 降级「{区域名}的归因已就绪」。
- **M1 色名脱节**（核实 tokens.css:28-29 色板无"深红"，very-negative #D85A30 深珊瑚橙）→ 文案"深红"改"深橙" + 色名从 theme var 派生铁律。
- M3 优先级文字矛盾（streaming 第一）；M2 range+result 兼带次 CTA。
- 反评价 14 条（agree 11 / partial 3 / disagree 0）→ plan v0.3→**v0.4** 11 点修订。
- **承重未动**（纯文档）。**v0.3/v0.4 可进 P0 测试铺底**；待 CB-CPD-03 验证定稿。

### ✅ CB-CPD-01 双模型首评反评价 → plan v0.3（revision-log 5.173 · commit c9eeed0 · **待用户 push**）

第三方 DeepSeek + K3 双模型首评 cpd-core-plan.md v0.2（均自读项目文件，报告 `SCAN_CPDPlan_01-{deepseek,k3}.md`）。

- **反评价 26 条**（agree 20 / partial 6 / disagree 0），**4 承重证据 grep/read 全部核实**：`.aiq-conclusion` 死信号 / exit 小写词表 / curState 进 buildContext / 光环硬编码 hex。
- **K3 三 P0 spec 错误**（plan 对"已就绪地基"事实陈述错）：死信号→`.aiq-exit-badge`；exit 大写→小写；映射 key=curState（S0/S1 不可达）→特征向量真值表。
- **DeepSeek 演示表现力最短板**（功能教程非诊断叙事）：S3 空间交互优先 + S4 地图定位 CTA 闭合交互环 + 文案叙事化。
- **plan v0.2→v0.3 九点修订** + cb-journal CB-CPD-01 四节 + review.md prompt 自包含（CB 协议/纪律/轮次/语境/必读文件/署名）+ SCAN 命名 `-{model}` + RULES 七轴（演示表现力）+ KNOWLEDGE 演示逻辑链北极星。
- **承重未动**（纯文档；review.py/前端/tests 留 P0-P2）。**待 CB-CPD-02** 验证修订落地 + 演示升维。

### 🔄 EMC 浮窗交互改进（前端·**已 commit 待 F5 验**·panel.js/index.html/ai_qa.css）

- F5 后默认折叠胶囊 + 展开欢迎卡（不记忆上轮态，430×640）+ 历史垃圾桶加大 + 一键全清。
- 内容驱动高度自适应（增量法，拉长+缩回；修 flex 撑满 scrollHeight 失真）。
- exit-badge 去线框改填充式 teal（避免线框设计原则）。
- **换环境后 F5 验**：折叠欢迎卡 / 高度自适应缩回 / exit-badge teal / 历史桶；有问题修后再处理。

### ⬜ 下一步：P0 测试铺底（plan §八 · v1.0 定稿后）

- 扩 `docs/emc-test-cases.md`（地基行为用例 4→N）+ 落 `tests/browser/`（复用 emc_helpers.py，断言挂真端点）。
- 详见 [cpd-core-plan.md](cpd-core-plan.md) v1.0 定稿声明 + roadmap（P0→P1 尺度诚实→P2 引擎 G1-G4）。

---

## 📅 2026-07-21（分支 `cpd` · CPD 系统级重构）

### 🔄 CPD — 情境式渐进披露（contextual progressive disclosure）

> EMC 升为系统底层主控、摈弃工程化操作体验、情境式渐进披露（软折叠）。分支 `cpd` 从 main 切出，完成后引导合并；main 遗留（批4 grid 镜像 bug）延后。plan：`~/.claude/plans/07-21-4-swipe-compressed-dawn.md`。单一真理源 `docs/design-system.md`。

- [✅] **Phase 0 · POI 入库**（revision-log 5.155 · 待 push）：`DATA/POI/` 3220 真实 POI 入 `core/place_layer.py`（无 SQL DB，库=place_layer 单 owner）。新增 `SCRIPT/poi_data/ingest_centralcity_poi.py`（字段映射 + 10 类→4×5 + 覆写 `amap_poi_centralcity_wgs84.json`，place_layer 零改动）。all_pois 4497。修 test_geocode 2 例（limit 30→200）。1623 边界 = 已有 `admin_district` preset（同 9 区），无需重复。
- [✅] **Phase 1 · 页面 UI 改造（revision-log 5.156 · 待 push）**：1a 工具簇横排（比例尺最左、按钮列其右、底对齐）；1b EMC 浮窗化（`position:absolute` 浮于 `#map` 左上 + 原生 `resize:both` 高帧率双向缩放 + localStorage 持久化 + 初始折叠条；`_setupEmcFloat` reparent 到 `#map`；`--emc-h` 三档自动调高退役为 no-op）。**左栏 `#left-panel` 暂留**（Range/Layers/Toolbox 仍在，`#lp-upper` flex:1 填满），Phase 2 加 CPD chip 行后再撤。**待用户 F5 肉眼验**。
- [⬜] **Phase 2 · CPD 软折叠状态机**：新增 `cpd-state.js` 客户端推导 curState（**不动 diagnose 保 eval**）+ 进度条/摘要 chip 行/主动作卡 + `buildContext` 增可选 hint。
- [⬜] **Phase 3 · 主题**：design-system 正冷/负暖五色带对齐 tokens + Light·yakushimabus（森绿 `#143a35` + 金黄）+ EMC 三级权重。
- [⬜] **Phase 4 · 附加**：CPD 抽象为可复用底层架构（CPD 完成后提示用户启动）。

---
