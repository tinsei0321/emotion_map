# CB-10 SCAN 深度扫描评估报告（EMC 全面审查）

> **扫描模型**：Codex（GPT-5，第三方独立评估，独立于 Claude Code 主开发工具）  
> **扫描时间**：2026-08-01 | **CB 轮次**：CB-10  
> **扫描分支**：`fix/emc-buglog` @ `a274362`（HEAD；main 为稳定主线）  
> **评估范围**：EMC（前端 LLM Agent 对话系统）——架构理念、9 模块设计对账、计划-执行链路、B001-B011 慢性 bug、文档一致性  
> **约束**：只读审查 + 改进 plan，未修改任何代码；未启动服务  
> **关联文档**：`docs/catch-ball/arch/SUMMARY.md`（61 决策）、`tests/buglog/`、`docs/emc-fix-progress.md`、`docs/revision-log.md`、`docs/todo.md`

---

## 第〇部分：上一轮（CB-09）建议执行回顾

| CB-09 项 | 目标 | 现状核验 | 判定 |
|---|---|---|---|
| P0-1 | `buildContext` 加数据来源标注（user-uploaded / system-preset） | 已在代码：`frontend/js/ai_qa/tools.js:596-613`（上传/预设/工具产物/绘制 中文 tag） | [OK] 已落地 |
| P0-2 | `buildContext` 加图层类型标注（point/polygon/heatmap） | grounding 含 kind 信息，但无"被裁剪层类型=源层类型"强校验 | [WARN] 部分落地 |
| P0-3 | FC prompt 极性范围纪律（未限定极性→默认全极性·禁缩窄） | `31e2a00` 曾添加，被后续 prompt 重写（`0073990`/`500d4b9`）静默删除；当前 `ai_qa/router.py:52-59` 无此段 | [ERR] 修复丢失 |
| P0-4 | finalStep context 注入执行结果摘要 | 已落地（`harness.js:525-540`、`1068-1076`、`runAllToolCalls`/`runChainPath` 均有注入） | [OK] 已落地 |
| P2-1 | System prompt 加「不确定时直接列出所见，不要推理」 | 未发现对应恒定指令；数据清单问句仍走 FC | [ERR] 未落地 |
| 新增 | `_quickIntent` 数据清单查询短路（上传了哪些/有哪些数据） | `frontend/js/ai_qa/harness.js:74-100` 无该类关键词 | [ERR] 未落地 |

**CB-09 遗留结论**：多步链断裂（B005）的根因（plans[] 无消费方）未在本轮之前修复，本次审查确认仍是架构级缺口（详见第三部分）。

---

## 第一部分：扫描内容

### 1.1 扫描范围

| 维度 | 覆盖文件 | 扫描深度 |
|---|---|---|
| 架构与编排 | `frontend/js/ai_qa/harness.js`（101KB）、`stages.js`（28KB）、`api.js` | L2（关键函数逐段） |
| 工具执行 | `frontend/js/ai_qa/tools.js`（84KB）、`frontend/js/heatmap-tool.js`、`frontend/js/toolbox/vector-tool.js` | L2 |
| 后端 FC | `ai_qa/router.py`、`ai_qa/llm.py`、`ai_qa/tool_contracts.py`、`ai_qa/prompts.py` | L2 |
| CPD/UI | `frontend/js/ai_qa/cpd-guide.js`、`cpd-state.js`、`panel.js`（相关段） | L2 |
| 设计文档 | `docs/catch-ball/arch/SUMMARY.md` + `01~09-*.md`（9 模块） | L1 |
| 慢性 bug | `tests/buglog/`（open 10 + resolved 1 + 生成器） | L1 |
| 文档对账 | `docs/emc-fix-progress.md`、`docs/todo.md`、`docs/revision-log.md`、`docs/catch-ball/_cb-index.md` | L1 |
| 测试 | 全量 `pytest tests/`（本环境实测） | L1 |

### 1.2 测试环境说明

- Python 3.14.6 / pytest 9.1.1（本机 `py` 启动器不可用，使用 `C:\Users\Hi\AppData\Local\Python\bin\python3.14.exe`）。
- 全量结果：`196 passed / 20 failed / 5 skipped / 3 errors`。
- 20 个 `tests/test_sandbox.py` 失败在**单独运行该文件时全部通过（28/28）**——判定为测试间隔离/本环境缓存问题，非 EMC 代码回归。
- `tests/test_range_selector_presets.py` 2 个 error 为本沙箱临时目录权限问题（`PermissionError: C:\Users\...\Temp\pytest-of-Hi`）。
- **真实未修复回归**：`test_final_prompt_stays_lean`——final prompt 实测 3616 字节 > 3KB 限制（07-28 起已知，文档标注"非本次范围"，至今未修）。

---

## 第二部分：扫描结果 / 评价

### 2.1 维度一：EMC 整体架构（Smart Agent, Dumb Tool）

**结论：骨架成立，但"智能"正向编排器渗漏，"计划"半成品无消费方。**

| 子项 | 判定 | 证据 |
|---|---|---|
| Smart 两端（意图理解 + 结果表达） | [OK] | FC 诊断 `stages.js:293` + finalStep `stages.js:440` |
| 编排器机械接线 | [ERR] 已泄漏推理 | `_autoExpandOverlays`（`harness.js:1248` 用地关键词正则）、`_deterministicRecover`（`harness.js:1161` 模式 A/B/C）、`_matchPlanToQuestion`（`harness.js:22`）、`_deriveDomainLens`（`stages.js:393`）——领域规则正在堆积 |
| Dumb 工具纯参数化 | [WARN] | `extract_feature` 内置字段自纠正（`tools.js:1044-1068`，getFieldCard 猜字段名） |
| 计划-执行分离 | [ERR] 断裂 | plans[] 只存不消费（详见 2.3） |

**边界泄漏根因**：多步计划能力（LLM 产 plans[]）未闭环，改用 3 个确定性正则补丁在编排层"机械补智能"；每出现新问法就加正则，不可收敛，且三个补丁互不覆盖。

### 2.2 维度二：9 模块设计 vs 实际代码

| 模块 | 关键决策 | 落地状态 | 证据 |
|---|---|---|---|
| 1 Diagnose | D041 单次 FC + 契约 Schema | [OK] | `router.py:47` / `tool_contracts.py:412` |
| | D045/D047 plans[] 附带产出 | [WARN] 半成品 | FC prompt 无 plans 产出指令（`router.py:52-59`）；无 content 时后端自建 rank=1 单元素 plan（`router.py:96-105`），rank=2+ 恒空 |
| | D063 全注入 13 工具 | [OK] | `contracts_to_tools_schema()` 排除 concept/multi/unknown |
| 2 Orchestrator | D050 不查 SKILL_DEFS | [WARN] 漂移 | 仍查 `stages.SKILL_DEFS`（`harness.js:894-901`、`1329`），保留 `_TOOL_TO_SKILL` 反映射 |
| | D057 单 tool_call | [ERR] 文档滞后 | 代码已修订为多 tool_calls 批量执行（`b2bdca9`；`stages.js:331-340`、`harness.js:890-901`），但 `SUMMARY.md`/`02-orchestrator.md` 未更新 |
| | D062 代码层参数校验 | [OK] | 后端 `validate_tool_call`（`router.py:88-95`） |
| 3 Execution | D016 统一 observation | [OK] 主体 | `tools.js:1023-1159`；但 `runAllToolCalls` 用另一套 `第N步: tool(params) → obs` 格式（`harness.js:1282-1290`） |
| | D017 computeStyle 镜像 | [OK] | `heatmap-tool.js:839-846` |
| 4 FinalStep | D019 极瘦 prompt 1.86KB | [ERR] 回弹 | 实测 3616B；`test_final_prompt_stays_lean` 失败 |
| | D020 追问胶囊三级 | [WARN] 换实现 | 胶囊来自 finalStep 草稿 `{{capsule:...}}` 标记（`harness.js:318-356`），非设计所述"从 observation 派生 + 绑定工具集" |
| 5 Review+Revise | D022 删旧 R+R | [OK] | `reviewStep/reviseStep` 已无 |
| | D023 质量防线三层 | [OK] | `applyQualityDefense`（`harness.js:262-317`）纯代码 |
| 6 Prompt Eng | D052 契约派生 schema | [OK] | `tool_contracts.py:412` |
| | D059 删旧 diagnose prompt | [WARN] 保留兜底 | 旧 SSE `build_diagnose_prompt_dispatch` 仍接 `router.py:62-66`（设计允许 fallback） |
| 7 Toolbox↔EMC | D027/D029 契约 + 镜像 | [WARN] | 13 工具契约 + `validate_skill_params.py`；但 rank 契约 `params_str` 仍写旧枚举 `by(polarity|domain|element)`（`tool_contracts.py:58`），实际 enum 为 `worst/best/domain:X/element:X` |
| 8 CPD | D054 plans[] → CPD | [ERR] 未落地 | `cpd-guide.js:41-73` 只看特征信号，不读 plans；plans→胶囊被禁用（`07d57c1`） |
| 9 字段识别 | D063/D064 全注入 + 简化 0LLM | [OK] | `buildContext`（`tools.js:595`）只做接地 + 来源标注 |

**未落地/漂移清单**：D054 从未实现；D057 代码改而文档未改；D019 瘦身回弹；D020 实现机制偏离；D045 缺 prompt 指令支撑。

### 2.3 维度三：计划-执行流水线链路

**链路**：用户 NL → `_quickIntent`（`harness.js:74`）→ `_dataGate`（`harness.js:797`）→ `fcDiagnoseStep`（`stages.js:293`）→ `orchestrate` 分流（`harness.js:724`）→ `runTemplatePath` / `runAllToolCalls` / `runChainPath` / while-loop → `finalStep`（`stages.js:440`）→ `applyQualityDefense`（`harness.js:262`）。

**核心发现：plans[] 无任何常规消费方。**

- plans[] 存入 `ctx.plans`（`harness.js:822-824`），但：
  - plans→胶囊转换被禁用（`harness.js:542-545`；commit `07d57c1` 明确写"keep plans[] for future auto-execution"）；
  - `executePlans` 完整存在（`harness.js:1320-1360`），但**全仓库零调用**（git 历史显示调用点在 `176ff65/f4845b3/f3e30aa` 引入后又被移除，留下死函数）；
  - CPD 引擎（`cpd-guide.js`）只消费状态信号，不读 plans；
  - 唯一 plans 复用是 `_matchPlanToQuestion`（`harness.js:779-786`），且只匹配 density/rank + 极性词。

**三个用户症状的根因**：

| 症状 | 根因定位 | 严重度 |
|---|---|---|
| "只做一半"（B005） | LLM 产 1 tool_call + plans[2+] 无消费者。缓解均为补丁：`_autoExpandOverlays` 需 ≥2 用地关键词或通配（`harness.js:1252-1255`，"商业用地"单关键词不触发）；`CHAIN_REGISTRY` 仅 2 条硬编码链（`stages.js:70-84`）；`_deterministicRecover` 只在 FC 失败时触发（`harness.js:810-819`） | CRITICAL（架构级） |
| "只说不做"（B002/B004） | 已加固未根治：诚实观测（`tools.js:1028-1032` 等 count=0 不说"已生成"）、零图层守卫跳过 LLM finalStep（`harness.js:1056-1066`）、执行摘要注入（`harness.js:1068-1076`）、L1 谎报标注。但多步计划不执行时，"诚实"只保证不编造，不保证完成 | CRITICAL（架构级） |
| "答非所问"（B006） | ① 极性纪律被丢：`31e2a00` 添加的"极性范围纪律"段在 prompt 重写（`0073990`/`500d4b9`）中被删，当前 `router.py:52-59` 无此段；② `_deriveDomainLens` 的 A 部（parse FC content `[domain_lens:xxx]`，`stages.js:390`）因 prompt 无输出指令而恒空，只剩 B 部关键词兜底 | HIGH |

### 2.4 维度四：慢性 bug 状态（B001-B011）

| ID | 严重度 | 状态 | 修复是否在代码 | 根因 / 复发原因 |
|---|---|---|---|---|
| B001 | HIGH | resolved | [OK] 在 | `_norm_where` 拆逗号（`api/geo_routes.py:127`）+ 契约去"单要素"误导（`tool_contracts.py:182`）；复现 4 次已收口 |
| B002 | CRIT P0 | open | [WARN] 部分 | 三层加固在（`31e2a00`/`8e5e76f`/`3a97e19`）；plans 无消费者→"做一半"根因未除 |
| B003 | HIGH P1 | open | [WARN] 部分 | `buildContext` 来源标注已在（`tools.js:596-613`）能答对但慢；`_quickIntent` 无数据清单短路（`harness.js:74-100`）仍走 FC |
| B004 | CRIT P0 | open | [OK] 在 | 零图层守卫 + 诚实观测已拦截假结论；"不做"依旧可能（同 B005） |
| B005 | CRIT P0 | open | [WARN] 部分 | 架构根因 = plans 无消费方 + CHAIN_REGISTRY 仅 2 条 + `_autoExpandOverlays` 需 ≥2 关键词；"商业用地"单关键词用例仍会只做一半 |
| B006 | HIGH P1 | open | [ERR] A 修复丢失 | 极性纪律从 `router.py:52-59` 消失；B 样式继承无实现（clip/extract/overlay 产物无源图层样式传播） |
| B007 | HIGH P1 | open | [WARN] 契约缓解 | clip 用 `resolvePointLayer` 硬解析点层（`tools.js:1025-1028`），无类型一致性校验；overlay 无校验；契约描述已区分点/面（缓解） |
| B008 | MED P2 | open | [WARN] 部分 | density 按 pitch 默认 mode（`tools.js:1212-1215`）；2D/3D 样式未解耦、视角切换不刷新 |
| B009 | LOW P2 | open（已提交） | [OK] 在 | `ai_qa.css:430-432` sticky 右上 + `panel.js:1794` "↓"；待浏览器验证 |
| B010 | LOW | frontmatter=resolved 但文件在 open/ | [OK] 在 | `e2e-seam.js:55` 组名已改"测试数据 · 情绪点" |
| B011 | MED P1 | frontmatter=resolved 但文件在 open/ | [OK] 在 | `e2e-seam.js:136-144` loadRange 去重已加 |

**工具链自身缺陷**：`tests/buglog/_gen_index.py:59` 的 `_status` 从**目录**派生、忽略 frontmatter → B010/B011 frontmatter 写 `resolved` 却被计为 OPEN（`_summary.md` 显示 OPEN 10）。状态存在双源不一致。

### 2.5 维度五：文档一致性

| 文档 | 滞后程度 | 证据 |
|---|---|---|
| `docs/catch-ball/_cb-index.md` | 滞后 14+ commits | 写"当前分支 @ `7126f6d`"，实际 HEAD `a274362` |
| `docs/todo.md` | 工作树被回退且未提交 | `git diff` 删除 2026-07-30 Codex 会话整段 + 版本号 v3.2→v3.1（48 行）；与已提交版本和 buglog 修复记录矛盾 |
| `docs/emc-fix-progress.md` | 停在 07-28 | 声称"9/9 模块全 ✅ + pytest 221 passed + finalStep 1.86KB"，与当前不符（final prompt 3.6KB；本环境全量 196/20/5/3）；未反映 07-29~07-31 bug 修复工程 |
| `docs/revision-log.md` | 停在 07-29 abce549 | 未记录 07-30 全量 revert（`5ae053a`）+ 07-31 重建（`a274362` 等）；文档内部矛盾——多处"221 passed 零回归"与"1 既有 fail `test_final_prompt_stays_lean`"并存 |
| `SUMMARY.md` | D057 未更新 | 代码已改多 tool_calls，设计文档仍写"LLM 只输出 1 个 tool_call" |
| buglog `_summary/_index` | 状态双源 | B010/B011 frontmatter=resolved vs 目录=open |

---

## 第三部分：七轴评分（本环境证据版）

| 轴 | 权重 | 得分 | 依据 |
|---|:---:|:---:|---|
| 架构设计 | 18% | 6.5 | 骨架好；plans 管道断裂、编排器泄漏智能 |
| 代码质量 | 22% | 6.5 | 诚实防线/契约单一源强；死代码 executePlans、正则堆叠、观测格式两套 |
| 测试覆盖 | 13% | 5.5 | pytest 较全 + 飞轮 27 用例 + 回归清单；前端 JS 零单测（KNOWLEDGE 已承认）、prompt 内容无守卫、沙箱套件隔离问题 |
| Harness 工程 | 18% | 6.0 | CB 闭环 + buglog + 生成器 CI 设计好；状态双源 bug、文档滞后 |
| 文档完整度 | 9% | 4.5 | 体系庞大但多处滞后/自相矛盾/工作树回退 |
| 调用效率 | 10% | 6.0 | FC 单次 + finalStep 设计 6-11s；B003 数据清单仍走 FC、final prompt 回弹 |
| 演示表现力 | 10% | 5.5 | EMC 有 CPD 导游/胶囊 UI；但多步执行与样式继承 bug 拖累体验 |
| **综合** | 100% | **6.0** | 权重加权（四舍五入一位） |

---

## 第四部分：独立判断

### 4.1 做得好（值得保留）

- 契约单一源 + 派生 schema + 后端 `validate_tool_call`——CB-04 "四处分裂"问题治得干净。
- `computeStyle` / `_normalizePolarity` 镜像（`heatmap-tool.js:100,839`）——"消极热力图出综合彩虹图"根因修复仍在。
- 诚实观测 + 零图层守卫 + `applyQualityDefense` 纯代码防线——本仓库最强工程质量，方向正确。
- buglog + 飞轮 + `_gen_index --check` 闭环机制本身设计不错（虽有状态双源小 bug）。
- 工具委托 Toolbox（`tools.js:1023-1159`）——"Dumb 执行"落地路径清晰。

### 4.2 架构级缺陷（非修 bug 能解决）

1. **plans[] 是一条从未接通的管道**。设计、数据结构、函数（`executePlans`）、存储（`ctx.plans`）都在，唯独没有消费者，还被 `07d57c1` 显式禁用。"多步计划→顺序执行"是 EMC 核心承诺，目前靠正则补丁支撑——B002/B005 反复出现的唯一根因。
2. **编排器正在变成"领域推理器"**。`_LANDUSE` 关键词表、`_DK` 领域词表、`_POL_MAP` 极性词表散落 harness/stages，违反"编排器机械接线"铁律，且不可收敛。
3. **FC prompt 无版本化守卫**。两次 prompt 重写静默丢掉极性纪律；没有 prompt 内容回归测试，修好的东西随时被"简化"掉。
4. **文档-代码双轨不同步是常态**。D057、finalStep 极瘦、221 passed、分支 hash 多处与现实脱节；`docs/todo.md` 工作树被回退。

---

## 第五部分：改进 plan（按优先级）

### P0 · 打通"计划→执行"（否则 B002/B004/B005 无法翻篇）

**P0-1 接通 `executePlans` 为 plans[] 唯一消费方（推荐方案 A）**
- 改动文件：`frontend/js/ai_qa/harness.js`（`runTemplatePath` 成功后、`finalStep` 前，若 `ctx.plans` 有 rank≥2 且通过 `stages.validateParams`，调 `executePlans` 顺序执行；任一步失败→诚实汇报"完成 N/M 步"）；`frontend/js/ai_qa/stages.js`（plan 校验）
- 风险：中——LLM 填的 plan 参数可能错（validate 兜底）；需防重复执行（rank=1 已执行）
- 验证：TC-21 / TC-23 / TC-24 + B005 用例，断言"计划步数=执行步数"
- 备选方案 B：删除 plans[] 概念，FC 强制多 tool_calls 为唯一多步通道（与 D057 修订一致），并把 `_autoExpandOverlays` / `_deterministicRecover` 正则收敛到一处

**P0-2 恢复 FC prompt 极性纪律 + 加 prompt 内容回归测试**
- 改动文件：`ai_qa/router.py:52-59`（补回"极性范围纪律"段）；`tests/test_emc_template.py`（新增断言）
- 风险：低；验证：TC-25 + B006 用例

**P0-3 补"计划完成度守卫"**：finalStep 前检查 `planned >= 2 && executed < planned` → 自动续做或显式 partial 出口
- 改动文件：`frontend/js/ai_qa/harness.js`（复用 F3 完整度逻辑 `harness.js:978-990` 至 FC 单工具路径）
- 风险：中；验证：B005 / 飞轮 TC-24

**P0-4 修 `test_final_prompt_stays_lean`**（final prompt 3616B > 3KB）
- 改动文件：`ai_qa/prompts.py`（FINAL_TEMPLATE 瘦身）或如实放宽守卫并记 ADR
- 风险：低；验证：pytest 该用例转绿

### P1 · 收口慢性 bug

**P1-1 buglog 状态单源化**
- 改动：`tests/buglog/_gen_index.py`（frontmatter status 与目录不一致→`--check` 失败）；B010/B011 移入 `resolved/`；B009 保持 open（注明"已提交未验证"）
- 风险：低；验证：`py tests/buglog/_gen_index.py --check`

**P1-2 B003 数据清单短路**
- 改动：`harness.js:74-100`（`_quickIntent` 加"上传了哪些/有哪些数据/数据列表"→ general 直答，复用 `buildContext` 分组摘要）+ 测试
- 风险：低；验证：TC-22（<5s）

**P1-3 B007 几何类型门**
- 改动：`tools.js`（clip/extract_feature/overlay 拒绝"面层输入走点层路径"，observation 报"图层类型不匹配"）+ `tool_contracts.py` 描述
- 风险：低；验证：TC-26

**P1-4 B008 2D/3D 解耦**
- 改动：`frontend/js/heatmap-tool.js`/grid 生成 + `tools.js`（按 `viewMode` 选 `fill` vs `fill-extrusion`，加视角切换刷新监听）
- 风险：中（前端渲染）；验证：2D/3D 各跑一次网格聚合

**P1-5 B006-B 样式继承**
- 改动：`frontend/js/toolbox/vector-tool.js` + `tools.js _adoptToolboxResult`（生成图层继承源图层 paint/图例）
- 风险：中；验证：B006 用例肉眼比对图例

### P2 · 文档与守卫

- **P2-1 文档同步**：恢复/更新 `docs/todo.md`（提交工作树或重写为 a274362 状态）；`docs/emc-fix-progress.md` 改为"架构 ✅ / bug 工程 10 open"口径；`_cb-index.md` 分支 hash 更新；`SUMMARY.md` + `02-orchestrator.md` 同步 D057 修订
- **P2-2 修复内容守卫清单**：把 31e2a00（极性纪律）、8e5e76f（诚实观测）、3a97e19（多步扩展）等关键修复做成可 grep / 可测试断言，防 prompt 重写再次静默丢弃

---

## 附：关键证据索引

- plans 无消费方：`harness.js:542-545`、`harness.js:822-824`、`harness.js:1320`（executePlans 零调用）、`cpd-guide.js:41-73`
- 编排器泄漏智能：`harness.js:1248`、`harness.js:1161`、`harness.js:22`、`stages.js:393`
- 极性纪律丢失：`router.py:52-59` vs `31e2a00` diff
- finalStep 加固：`harness.js:525-540`、`harness.js:1056-1066`、`tools.js:1028-1032`
- prompt 回弹：`test_final_prompt_stays_lean`（3616B）
- 文档滞后：`_cb-index.md`（7126f6d vs a274362）、`docs/todo.md`（git diff 未提交回退）

---

*本报告为第三方独立评估，未参考主开发工具（Claude Code）既有结论；待项目方反评价（agree / disagree / partial）。*
