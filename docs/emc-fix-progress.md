# EMC 修复工程 · 总进度汇总卡

> **一页看清** EMC 修复整体状态。**九模块实施进度矩阵（§一·监控主视图）** + 5 层分层明细（§二）+ 待修（§三）+ 时序（§四）。
> **更新**：2026-08-05（**出口三段式 P0-P2 + 热点图 P0/P1/P1.5 全流程**·CB 计划→执行→审计→修正全闭环；分支 fix/emc-buglog @ 0916e8c·pytest 293 passed + validate 28 passed）
> **承继**：本卡由 `emc-fix-backlog.md`（2026-07-24 快照）更名重写，聚焦"9 模块进度 + 分层 + 时序"。
> **⚠️ 关键区分**：**v1（三阶段 5.231-5.242）已被 v2（单次 LLM + FC·5.243-5.245b 第三方）取代** → v3（GLM 修复 3C+4H·7858d5a）→ **v3.1（reg.filter 崩溃修复·657c2e3）** → **v3.2（CB-09 bug 修复·D057 修订·代码自动扩展·全自动多步执行）** → **v3.3（CB-10 两天攻坚·B003/B005/B006/B007/P0-4/P1-1/右半段/词表集中）** → **v3.4（飞轮修复 5 项 + 族 A 主通道 A 定型）** → **v3.5（CB-11·glm组 加入 + G1/G2 union 无限循环修复 + 关 C 键 + 点层样式继承）** → **v3.6（出口三段式 + 热点图重做·2026-08-05·当前）**。v1 diagnose 管线（select_candidates/FILL_CARD/PLAN/dispatch）代码保留过渡期·Phase 4 清理待 v3 稳定后。架构设计源 [SUMMARY v2](catch-ball/emc-arch-deepdive/SUMMARY.md)（61 决策 D041-D068）。**CB-10 全面审查发现**：B002/B005 根因=plans[] 管道未接通·B006 极性纪律被 prompt 重写静默删·test_final_prompt_stays_lean 回弹 3616B·buglog 状态双源——已覆盖（剩余见 §三待修）。

---

## 一、九模块实施进度矩阵（监控主视图）

> 决策 ID 源 [SUMMARY §二](catch-ball/emc-arch-deepdive/SUMMARY.md)（D001-D040）；实施状态对账 [revision-log §5](revision-log.md#L226)（5.x 倒序·最新在顶）。
> 实施 = ✅ 完成 / 🔄 部分 / ⬜ 待。优先级 P0-P4 源 [SUMMARY §六](catch-ball/emc-arch-deepdive/SUMMARY.md)。

| # | 模块 | 优先级 | 决策 | 实施 | 关键落点 / 待办 |
|:---:|------|:---:|:---:|:---:|------|
| 3 | **Execution Layer**（执行层） | P0 | D016-D018 | ✅ | **5.231**：D016 observation 参数自述（cell_size/radius·网格单元非点）+ D017 `computeStyle` 镜像（CB-04·5.226）+ D018 `focusLayer` 父组空 FC 返子层（治 Overview「0 条」） |
| 5 | **Review + Revise** | P0 | D022-D024 | ✅ | **5.232**：D022 删旧 R+R（`review.py` 215 行 + reviewStep/reviseStep + REVISE_TEMPLATE 全清）+ D023 质量防线三层（[`applyQualityDefense`](../frontend/js/ai_qa/harness.js#L233)·全代码 <20ms·取代 LLM 审查 5-15s）+ D024 episode 迁移（review→defense） |
| 4 | **FinalStep Agent**（输出层） | P1 | D019-D021 | ✅ | **5.233 + 5.234**：D019 极瘦 prompt（17KB→1.86KB·prefill 20-35s→<1s）+ D020 追问胶囊三级（L1 0 LLM 轮 <2s / L2 Pro 确认 5-8s·`runCapsule` 复用 runTemplatePath）+ D021 工具集绑定（R5 schema 硬剔 / R6 可达性软标 / R8 多样性记 episode） |
| 1 | **Diagnose Agent**（认知层） | P1 | D041-D049 (v2) | ✅ v3 | **v2 FC ✅（5.243）+ v3 修复（7858d5a）**：单次 LLM + function calling + 契约 Schema（废弃 v1 三阶段）·[`fcDiagnoseStep`](../frontend/js/ai_qa/stages.js) + [`contracts_to_tools_schema`](../ai_qa/tool_contracts.py) ·v3 加 C1 provider fallback / C2 data gate / C3 domain_lens A+B |
| 2 | **Orchestrator**（编排层） | P2 | D050-D051 (v2) | ✅ v3 | **v2 消费 tool_calls[0] ✅（5.243）**：直接用 `tool_calls[0].function.name`·不查 SKILL_DEFS·`_TOOL_TO_SKILL` 反映射 ·v3 H6 删前端校验·后端 `validate_tool_call` 单源 ·D013 while-loop 降为兜底 ✅·D015 ensure_zone ✅ |
| 6 | **Prompt Engineering** | P4 | D025-D026+R1 | ✅ | D025 [`tool_contracts.py`](../ai_qa/tool_contracts.py) 单一源 ✅（CB-04·5.226）+ R1 rank `by` worst ✅；**D026 prompt 全派生 contracts ✅（5.240）**：FILL_CARD/PLAN（`_candidate_schema_text`）+ DIAGNOSE（GEO_TOOL_CATALOG 附录）+ FINAL（无规格）+ AGENT（手写→指针·本次）全派生 |
| 7 | **Toolbox ↔ EMC 接口** | P4 | D027-D029 | ✅ | **CB-04（5.226）**：D027 15 `generate*ForAI` 全审计 + D028 `enforceMutualExclusion` 保留 + D029 ForAI=dialog 镜像 CI；**L3 `panel_source` 全核查 ✅（5.238）**：31 处 Resolved（dialog 控件 / EMC-only / PANEL_MISSING 三态） |
| 8 | **CPD 引擎** | P3 | D030-D034 | ✅ | **D030 ✅**（cpd-guide/state 客户端纯规则·5.224）+ **D031 ✅**（[runCapsule](../frontend/js/ai_qa/harness.js#L506) 胶囊点击跳 Flash 直执·5.234·实现 CPD「选项直执」核心）+ D032 turn-over 移除 ✅ + D033 完成态 ✅ + **D034 ✅（5.239）** `capsule_clicked` episode 埋点→Pro 排序偏好·honest：不另造重复对话框 |
| 9 | **字段识别（0LLM）** | P2 | D063-D064 (v2) | ✅ v3 | **v2 简化 ✅（5.243）**：废弃 tools_hint/筛选·全注入 13 工具（7.4KB/2.7s）·0LLM 只做 grounding + 数据缺失检测 ·v1 `candidate_selector.py` 保留过渡期（Phase 4 清理待 v3 稳定后） |

**总计**：v1 设计定稿 9/9 ✅ · **v2 架构转型 ✅**（D041-D068·单次 LLM + FC）· v3 修复 ✅（3C+4H+reg.filter）· **当前 v3.6**（出口三段式 + 热点图重做）· pytest **293 passed** · validate **28 passed** · 定向浏览器验证 FC 全链 ✓。

**🎯 当前状态**：**v3.6**（出口三段式 + 热点图重做·2026-08-05）——**出口三段式 P0-P2**（观点先行干货→4 要点→行业接口参数：FINAL_TEMPLATE 软扩 `> **观点：**` + result-struct.js 结论段独立聚合 + 观点卡/4 要点卡 + 需求强度四档 + 复合优先级 + CSV 导出 + geo_label·pytest 293 passed）+ **热点图 P0/P1/P1.5**（命名定标 8 处·Gi\*→显著聚集点 + A/B 全 ns 实锤（score U 形离散·Gi\* 连续假设不匹配）+ 软分级五档（threshold 参数化·诚实标 84% 倾向）+ setTerrain 连续曲面（create_terrain_dem F_009·draping 隔离·替代千层饼））。**两组评估/审计全闭环**（P0/P1/P1.5 计划+实施各过两轮 CB·B1/W1-W3/W6 修复采纳）。**剩余**：整体验收（todo「整体验收清单」·用户浏览器验收）+ PRM 参数填充瓶颈 + CPD-L01/L02 + 长期 KDE/DBSCAN 替代 Gi\* 评估（热点图 P2/P3）+ P3 工具管线并行（后置·`$n` 索引重构前置）。Phase 4 清理待 v3 稳定后。

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
| ✅ **B002/B005 多步执行缺口** | 编排 | `_autoExpandOverlays` 扩单用地 + `_deterministicRecover` 模式 D + `_LANDUSE` 去泛词·浏览器验证 ✓（898998b） | CB-10 |
| ✅ **B006 极性纪律丢失** | Prompt | build_fc_sys_prompt 恢复 31e2a00 纪律段 + 内容守卫（898998b）·浏览器验证 B006 全极性 ✓ | CB-10 |
| ✅ **test_final_prompt_stays_lean 回弹** | Prompt | 语言风格 7 并 3 + 人民城市条件注入 → 转绿（898998b） | CB-10 |
| ✅ **buglog 状态双源** | 测试 | `_gen_index` 读 frontmatter status 优先 + B010/B011 移 resolved（898998b） | CB-10 |
| ✅ **B007 几何类型门** | 工具 | `_checkGeomType` clip 需点/overlay+extract 需面·类型不匹配报错（7735cb8） | CB-10 |
| ✅ **B003 数据清单短路** | 路由 | `_quickIntent` 清单意图 → general 短路·浏览器验证 ✓（898998b） | CB-10 |
| ✅ **executePlans 死代码** | 编排 | 删·保 ctx.plans/_plansToCapsules 作 CPD-RESERVED（898998b） | CB-10 |
| ✅ **词表集中** | 编排 | emc-patterns.js 收纳 LANDUSE_KW/DOMAIN_KW/POLARITY_KW/意图词（7735cb8） | CB-10 |
| ⬜ **domain_lens A 部损失** | 路由 | FC prompt 无 domain_lens 输出指令 → `_deriveDomainLens` A 部（parse [domain_lens:xxx]）恒空·只剩 B 部关键词兜底·非关键词措辞返 [] → finalStep 无领域知识注入·恢复需 +~600B + L01 回归风险·记待修非静默无损失（Codex 验收条件 3） | CB-10 ③ |
| ⬜ **B002 半成品 answer** | 体验 | runTemplatePath 先渲染半成品答案再后台跑 autoExpand·结论诚实但割裂·待重构 | CB-10 |
| ⬜ T4 胶囊矛盾 | — | 无 strategy 不显"齐全" + 值层面缺口回写 diagnose | backlog |
| ⬜ T5 对比 C 键 | — | 批4 Swipe 入口收敛 + 无焦点提示 + 双屏标题 | backlog |
| ⬜ T6 飞轮断言三件套 | — | 答案产出/落图/切题校验（非只信号） | backlog |
| ⬜ ⑥ 摘要完整 ①②③ | — | method/plan 采集（diagnose 增字段回传） | backlog |

---

## 四、时序（5.203→v3.6 · 详 [revision-log §5](revision-log.md#L226)）

| 版本 | 修复 | CB |
|------|------|:--:|
| **v3.6** | **出口三段式 + 热点图重做**（出口三段式 P0-P2：观点先行软扩/result-struct 结论段独立聚合/观点卡 4 要点卡/需求强度四档/复合优先级/CSV 导出/geo_label + 热点图 P0-P1.5：命名定标 8 处/A/B 全 ns 实锤/软分级五档/setTerrain 连续曲面·0916e8c·pytest 293 passed·两组评估审计全闭环） | CB 专题 |
| **v3.5** | **CB-10/CB-11 系列·merge 多图层 + 只说不做根治**（G1/G2 union 无限循环 + 关 C 键 + 点层样式继承 + merge 多图层 concat + 「剪裁+合并」根治） | CB-11 |
| **v3.3** | **CB-10 Day2 右半段 + B007 + 词表集中**（删 executePlans 死代码·CPD-RESERVED 标注·P0-3 完成度确定性追加·B007 _checkGeomType 类型 guard·emc-patterns.js 词表集中·7735cb8/392ecc1） | CB-10 |
| **v3.2** | **CB-10 Day1 P0-P4 修复**（B003 数据清单短路·B005 单用地+双区+_LANDUSE 泛词·B006 极性纪律恢复+守卫·P0-4 final prompt 瘦身·P1-1 buglog 状态单源·898998b·pytest 220 passed·B0 36/45 无回归） | CB-10 |
| **v3.1** | **reg.filter 崩溃修复 + SCAN P1 边界**（formatRegistry()→getArtifacts()·治 [请求失败]+胶囊消失+速度·SCAN P1: zonal_stats/parsePlans/fc_fixes/domain_lens） | v3 |
| **v3** | **修复第三方 v2 的 3 CRITICAL + 4 HIGH**（C1 provider fallback / C2 data gate / C3 domain_lens / H2 range / H5 timeout / H6 校验统一） | v3 |
| **5.245b** | stages.js 语法错误修复（多余 }·第三方） | v2 |
| **5.245** | FC diagnose 兼容性修复 7 项（tool→skill / normalizeCard 补全 / intent 推导·第三方） | v2 |
| **5.244** | v2 CPD plans→胶囊（D068 _plansToCapsules·第三方） | v2 |
| **5.243** | **v2 FC 后端+前端**（contracts_to_tools_schema + chat_with_tools + fcDiagnoseStep + D062 + D065·第三方） | v2 |
| **5.242** | v1 选型数据感知系统性修复（11 项·GLM） | CB-09 |
| **5.240** | 模块六 D026 prompt 全派生 contracts（v1·已被 v2 FC 取代） | CB-09 |
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
