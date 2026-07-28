# EMC 修复工程 · 总进度汇总卡

> **一页看清** EMC 修复整体状态。**九模块实施进度矩阵（§一·监控主视图）** + 5 层分层明细（§二）+ 待修（§三）+ 时序（§四）。
> **更新**：2026-07-27（模块六 D026·**5.240**·prompt 全派生 contracts·**9/9 全落地里程碑**）
> **承继**：本卡由 `emc-fix-backlog.md`（2026-07-24 快照）更名重写，聚焦"9 模块进度 + 分层 + 时序"。
> **⚠️ 关键区分**：**设计定稿 9/9 ✅**（[deepdive 讨论](catch-ball/emc-arch-deepdive/SUMMARY.md) 全定稿·README「进度总览」✅ 指此）**≠ 实施落地 6/9 ✅**（见 §一矩阵）。看代码进度只认本卡 §一 + revision-log §5，勿认 deepdive README 的 ✅。

---

## 一、九模块实施进度矩阵（监控主视图）

> 决策 ID 源 [SUMMARY §二](catch-ball/emc-arch-deepdive/SUMMARY.md)（D001-D040）；实施状态对账 [revision-log §5](revision-log.md#L226)（5.x 倒序·最新在顶）。
> 实施 = ✅ 完成 / 🔄 部分 / ⬜ 待。优先级 P0-P4 源 [SUMMARY §六](catch-ball/emc-arch-deepdive/SUMMARY.md)。

| # | 模块 | 优先级 | 决策 | 实施 | 关键落点 / 待办 |
|:---:|------|:---:|:---:|:---:|------|
| 3 | **Execution Layer**（执行层） | P0 | D016-D018 | ✅ | **5.231**：D016 observation 参数自述（cell_size/radius·网格单元非点）+ D017 `computeStyle` 镜像（CB-04·5.226）+ D018 `focusLayer` 父组空 FC 返子层（治 Overview「0 条」） |
| 5 | **Review + Revise** | P0 | D022-D024 | ✅ | **5.232**：D022 删旧 R+R（`review.py` 215 行 + reviewStep/reviseStep + REVISE_TEMPLATE 全清）+ D023 质量防线三层（[`applyQualityDefense`](../frontend/js/ai_qa/harness.js#L233)·全代码 <20ms·取代 LLM 审查 5-15s）+ D024 episode 迁移（review→defense） |
| 4 | **FinalStep Agent**（输出层） | P1 | D019-D021 | ✅ | **5.233 + 5.234**：D019 极瘦 prompt（17KB→1.86KB·prefill 20-35s→<1s）+ D020 追问胶囊三级（L1 0 LLM 轮 <2s / L2 Pro 确认 5-8s·`runCapsule` 复用 runTemplatePath）+ D021 工具集绑定（R5 schema 硬剔 / R6 可达性软标 / R8 多样性记 episode） |
| 1 | **Diagnose Agent**（认知层） | P1 | D001-D011 | ✅ | **D006 Phase B ✅（5.236）** + **D009 Phase C ✅（5.237）**：三阶段落地—[`build_diagnose_prompt_dispatch`](../ai_qa/prompts.py) 顶调 select_candidates → 单/少候选走极瘦填卡（45.8KB→1.85KB·<5s）·复合走 Pro 计划（D009·产 chain·5-10s）·0 候选走大 prompt 兜底；卡 schema 不变 |
| 2 | **Orchestrator**（编排层） | P2 | D012-D015 | ✅ | **D012 动态 chain ✅（5.237）**：复合 → Pro 产 chain → [`runChainPath`](../frontend/js/ai_qa/harness.js#L532) 动态消费（取代固定 CHAIN_REGISTRY·主体不动）；D013 while-loop 降为兜底 ✅；D014 `_PARAM_ALIAS` 按工具 ✅（CB-04）+ D015 ensure_zone ✅ |
| 6 | **Prompt Engineering** | P4 | D025-D026+R1 | ✅ | D025 [`tool_contracts.py`](../ai_qa/tool_contracts.py) 单一源 ✅（CB-04·5.226）+ R1 rank `by` worst ✅；**D026 prompt 全派生 contracts ✅（5.240）**：FILL_CARD/PLAN（`_candidate_schema_text`）+ DIAGNOSE（GEO_TOOL_CATALOG 附录）+ FINAL（无规格）+ AGENT（手写→指针·本次）全派生 |
| 7 | **Toolbox ↔ EMC 接口** | P4 | D027-D029 | ✅ | **CB-04（5.226）**：D027 15 `generate*ForAI` 全审计 + D028 `enforceMutualExclusion` 保留 + D029 ForAI=dialog 镜像 CI；**L3 `panel_source` 全核查 ✅（5.238）**：31 处 Resolved（dialog 控件 / EMC-only / PANEL_MISSING 三态） |
| 8 | **CPD 引擎** | P3 | D030-D034 | ✅ | **D030 ✅**（cpd-guide/state 客户端纯规则·5.224）+ **D031 ✅**（[runCapsule](../frontend/js/ai_qa/harness.js#L506) 胶囊点击跳 Flash 直执·5.234·实现 CPD「选项直执」核心）+ D032 turn-over 移除 ✅ + D033 完成态 ✅ + **D034 ✅（5.239）** `capsule_clicked` episode 埋点→Pro 排序偏好·honest：不另造重复对话框 |
| 9 | **字段识别（0LLM）** | P2 | D035-D040 | ✅ | **Phase A ✅（5.235）+ Phase B 接 diagnose ✅（5.236）**：[`candidate_selector.py`](../ai_qa/candidate_selector.py) `select_candidates` 纯规则（B_TRACK keyword + field role→tool 消歧 + track 派生 + 化合物 + 三态出口）·eval 语料 **97% 命中**·Phase B 接 router dispatch 落地（单/少/复合三路分派）；Phase C compound → Pro（5.237） |

**总计**：设计定稿 **9/9 ✅** · 实施落地 **9/9 ✅（一/二/三/四/五/六/七/八/九·全落地）· 0/9 🔄 · 0/9 ⬜**

**🎯 当前推进**：CB-09 多轮次 + 9/9 完整收尾—核心 6/9（5.231→5.237）✅ + 模块七 L3（5.238）+ 模块八 CPD（5.239）+ **模块六 D026（5.240）✅**；**9 模块实施全 ✅**·待用户一次性浏览器齐验。下方 §三 仅剩 backlog（T4-T6/⑥·非 9 模块决策）。

---

## 二、分层明细（5 层 · 实施视角）

### 契约层（参数契约 · Smart↔Dumb 接口）
- ✅ density 参数契约四处分裂 → [`tool_contracts.py`](../ai_qa/tool_contracts.py) 单一真相源 + [`validate_skill_params.py`](../tests/validate_skill_params.py) 守护（CB-04·5.226）
- ✅ ForAI=dialog 镜像（`generateHeatmapForAI` 复用 `computeStyle`·CB-04）
- ✅ `normalizeParams` 按工具区分别名（治 `_PARAM_ALIAS` 误伤 density·CB-04）
- ✅ rank `by` 默认 worst + compare_regions 入 prompt（CB-04）
- ✅ density triggers 补「热力图」+ 参数名对齐 + few-shot 极性例（CB-04）
- ⬜ 13 工具 `panel_source` 全核查（L3·density 完整·其余 28 项待·非色板核心·模块七 D027 尾）

### 体验层（UX · EMC 核心价值）
- ✅ **ReAct 超时根治**（while-loop 7 策略·L0 路由补"网格/方格"+L1 缩轮+L2 完成信号+L3 prompt 条件化+P0-A 异常降级不丢图+P0-B 单轮 45s 超时+P1-C 早终止·CB-06·5.229）
- ✅ **finalStep 超时矛盾根治**（try/catch + `_composeDegradedConclusion` 零 LLM 降级·图出非"请求失败"丢图·CB-07·5.230）
- ✅ **2D/3D 跳组修复**（addLayer 补 `parentId`·配对层留 EMC 组·CB-07·5.230）
- ✅ **去 LLM 审查**（REVIEW_ENABLED 默认 false + FINAL_TEMPLATE 内嵌自查·省 7-14s·CB-05·5.227·后 5.232 整件删 review.py）
- ✅ **删除符号四层根治**（strip~~ + `getValidRefNames` 扩展治 CSS invalid 主因 + css 弱化 + REVISE 补·CB-05）
- ✅ `runTemplatePath` 加 `onObservation`（地图出图后 dock 反馈·治"出图但 dots 不停"·CB-05）
- ✅ panel 清审查 UI（占位/`_PHASE_ORDER`/审查区/文案·CB-05）
- ✅ prompt 优化工程（OPTIMIZE_TEMPLATE + chip 两行 + 中文化·5.215-5.219）
- ✅ 指代标注 `resolveCoref`（5.212）+ Bug5 折叠胶囊展开（5.224）

### 数据层（数据识别 · grounding）
- ✅ **数据识别 visible bug 修**（眼睛关的点层仍可用·`pickVisiblePointLayer`/`buildContext` 去 visible 过滤·5.228）
- ✅ Layer Manifest 字段识别（`getFieldCard` Promise 缓存 + 全字段值域·5.211/5.223）
- ✅ Flash 全字段值域识别（`buildContext` 数据摘要·categorical/数值/时间·5.223）
- ✅ EMC 组统一（`ensure_zone` `_adoptToolboxResult`·5.223）
- ✅ Layers 组卡数=0 根治（`_adoptToolboxResult` parentId·5.221）
- ✅ density 红色大面积修 + 全局中文化（5.220）

### 路由层（编排 · 计划→执行）
- ✅ **追问胶囊路由**（`runCapsule` 合成 synthDiagnose → 复用 runTemplatePath·L1 0 LLM 轮/L2 Pro 确认·跳 diagnose Flash·模块四 D020·5.234）
- ✅ `runTemplatePath` 单技能快路径（0 agent 轮·5.210）
- ✅ `runChainPath` 多步链（0 LLM 中间轮·治 C3 超时·5.210·**D012 Pro 动态 chain ✅ 5.237**）
- ✅ 模型路由（flash 默认 + 简单任务跳 diagnose·5.222）
- ✅ density 视角默认（2D/3D 读 pitch·5.222）
- ✅ E1 多步链 + E3 partial 出口（渲染失败层不计产出·5.210/5.209）

### 质量层（诚实 · 防假完成）
- ✅ **质量防线三层**（[`applyQualityDefense`](../frontend/js/ai_qa/harness.js#L233)·L1 `_verifyClaims` 谎报标注 + L2 R1/R2/R3/R4/R7 非空/补按钮/参数一致/状态矛盾/截断 + L3 `_composeDegradedConclusion`·全代码 <20ms·取代旧 R+R·5.232）
- ✅ **胶囊校验 R5/R6/R8**（R5 `validateParams` schema 硬剔无效 + R6 工具可达性软标 + R8 多样性记 episode·5.234）
- ✅ 代码诚实门保留（`_verifyClaims`/`_driftRe`/对账/F3·确定性·CB-05 去审查后仍守）
- ✅ 空答案检测（工具产出但结论过短→补引导·CB-05）
- ✅ KDE「情绪地形」去 3D 统一 2D 彩虹（5.225）

---

## 三、待修（欠什么 · 跨模块汇总）

> **🎯 CB-09 9 模块实施全 ✅（D001-D040 全落地）**·下方仅剩 backlog（非 9 模块决策·体验/运维项）。

| 项 | 模块 | 说明 | 来源 |
|----|:---:|------|------|
| ⬜ T4 胶囊矛盾 | — | 无 strategy 不显"齐全" + 值层面缺口回写 diagnose | backlog |
| ⬜ T5 对比 C 键 | — | 批4 Swipe 入口收敛 + 无焦点提示 + 双屏标题 | backlog |
| ⬜ T6 飞轮断言三件套 | — | 答案产出/落图/切题校验（非只信号） | backlog |
| ⬜ ⑥ 摘要完整 ①②③ | — | method/plan 采集（diagnose 增字段回传） | backlog |

---

## 四、时序（5.203→5.240 · 详 [revision-log §5](revision-log.md#L226)）

| 版本 | 修复 | CB |
|------|------|:--:|
| **5.240** | **模块六 D026 prompt 全派生 contracts（9/9 完整收尾·里程碑）**（AGENT 手写 GIS 规格→指针·全派生 tool_contracts·9 模块 9/9 ✅） | CB-09 |
| **5.239** | **模块八 CPD 收尾（D030-D034·9/9 第2步）**（D031 由 5.234 胶囊实现·D034 capsule_clicked episode 埋点·不另造重复对话框） | CB-09 |
| **5.238** | **模块七 L3 panel_source 全核查（D027 契约完整·9/9 第1步）**（31 处 Resolved：dialog 控件/EMC-only/PANEL_MISSING 三态·panel_missing 收紧） | CB-04 |
| **5.237** | **CB-09 轮次3c Pro 推理 + 动态 chain（D009+D012·Phase C·9 模块核心收尾）**（build_plan_prompt Pro 产 chain + normalizeCard 解析 + orchestrate Pro chain 优先·复合 5-10s） | CB-09 |
| **5.236** | **CB-09 轮次3b Flash 瘦身（D006·Phase B·SPEED WIN）**（build_diagnose_prompt_dispatch + FILL_CARD_TEMPLATE 45.8KB→1.85KB·单候选 <5s·复合兜底） | CB-09 |
| **5.235** | **CB-09 轮次3a 0LLM 候选选择器（模块九·Phase A·eval-safe）**（candidate_selector.py 纯规则 + eval 语料 97% 命中·不接路由） | CB-09 |
| **5.234** | **CB-09 轮次2b 追问胶囊三级 + 绑定工具集**（`runCapsule` L1/L2 路由 + applyQualityDefense 扩 R5/R6/R8 + 动态胶囊 chip） | CB-09 |
| **5.233** | **CB-09 轮次2a finalStep 极瘦**（FINAL_TEMPLATE 17KB→1.86KB·prefill <1s） | CB-09 |
| **5.232** | **CB-09 轮次1 删旧R+R + 质量防线三层**（删 review.py + applyQualityDefense 全代码防线） | CB-09 |
| **5.231** | **CB-09 轮次1 P0 消矛盾**（focusLayer 返子层 + observation 自述 + density 3d 清 radius + 单技能注入 formatRegistry） | CB-09 |
| 5.203-5.230 | **CB-04~07 + density 治本**（契约整改/去审查/超时根治/finalStep 矛盾/visible bug/KDE 去3D 等·11 版本）·详 [revision-log §5](revision-log.md#L226) | CB-04~07 |

---

## 五、指针
- **本卡（监控主入口）**：九模块矩阵 §一 + 时序 §四（每次 commit 后同步·[[todo-revision-log-sync]]）
- **详时序**：[revision-log §5 最新动态](revision-log.md#L226)（5.x 倒序·最新在顶）
- **设计源（9 模块 40 决策）**：[SUMMARY](catch-ball/emc-arch-deepdive/SUMMARY.md) + 各模块 `0X-*.md`（设计定稿·非实施进度）
- **评估决策**：[cb-journal](catch-ball/cb-journal.md)（CB 倒序·CB-09 在顶）+ [KNOWLEDGE](catch-ball/KNOWLEDGE.md)（跨轮蒸馏）
- **单一契约源**：[`ai_qa/tool_contracts.py`](../ai_qa/tool_contracts.py) + [`tests/validate_skill_params.py`](../tests/validate_skill_params.py)
- **最高纪律**：CLAUDE.md 第 5 条 + AGENTS.md 铁律 11（EMC 复用 Toolbox 参数面板·ForAI=dialog 镜像）
- **红线**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema（改前先扩 eval·每次一处）
