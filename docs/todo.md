# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。
> 📝 详版历史 = [revision-log §5](revision-log.md#L226)（永久审计底）·本文件只记当前 + 计划。
> 📌 **架构版本**：v1（三阶段 5.231-5.242）→ **v2（单次 LLM + FC·5.243-5.245b·第三方实施）** → **v3（v2 做对·5.246-657c2e3·GLM 修复）** → **v3.2**（CB-09 bug 修复·D057 修订·代码自动扩展·全自动多步执行）

---

## 📅 2026-07-29（今日·CB-09 "只说不做" 根治）

### ✅ 「只说不做」根治（commit 3a97e19+ · **fix/emc-buglog 分支**）

经过 ~20 轮迭代，最终方案：代码自动扩展 + 工具描述修正 + FC prompt 简化。

**根因链**：
1. LLM 词映射 "裁剪"→clip（错选工具）
2. clip 裁面层返回空→假结论
3. FC prompt 含旧诊断卡格式触发"预选工具"幻觉
4. 单 tool_call 设计无法完成多步骤

**修复（5 个维度）**：
- 工具观测诚实化：5 工具 count=0 时报"未生成"（`tools.js`）
- 零图层守卫：newLayerCount=0 跳过 LLM finalStep（`harness.js`）
- _autoExpandOverlays：代码检测"X区Y1+Y2"模式自动生成 overlay（`harness.js`）
- extract_feature/overlay/clip 契约修正：function description 明确区分点/面（`tool_contracts.py`）
- FC prompt 简化：去旧诊断卡触发词 + 直接词映射"裁剪面层→overlay"（`router.py`）

**架构变更**：D057 修订——LLM 可输出多个 tool_calls，orchestrator 顺序执行全部。新增 `runAllToolCalls` + `_autoExpandOverlays`。

详见 [revision-log §5](revision-log.md#L226)。

---

## 📅 2026-07-29（今日·CB 飞轮 buglog 扩建）

### ✅ buglog schema 统一 + CF-09 采集入库（commit abce549 · **用户手动 push**）

双环境并行致 buglog schema 分叉（我 YAML/ASCII vs ZCode 表格/emoji）→ 仪表盘对 B002-B008 全盲。按用户定「统一 YAML」修。详见 [revision-log §5](revision-log.md#L226)。

- **转换**：B002-B008 表格元数据 → YAML frontmatter（ASCII 枚举·emoji+诊断留 body·rootcause 规范·case_ref 映射 TC-21~27）。
- **重生索引**：`_index`/`_trend` 现 8 条 ASCII（覆盖 ZCode emoji 版）；`_gen_index --check` 过。
- **入库 ZCode**：emc_test_cases TC-21~27 + CB09-supplement 采集记录。
- **验证**：`/_test/buglog` 返 8 条（open 7 + resolved 1 + recList 5）。
- **教训**：双环境并行同子系统易 schema 分叉；skill 须锁死 frontmatter 契约。

### ✅ 飞轮扩建 P3 回归清单 + P2 hotfix（commit ed8fabf + 7354fb5/8c09e31 · **用户手动 push**）

落地 DeepSeek 方案 P3「回归用例自动生成」+ 修 P2 两个 bug。**飞轮扩建 P0-P3 全完成**。详见 [revision-log §5](revision-log.md#L226)。

- **P2 hotfix**：7354fb5 修 serve.py `/_test/*` 路由 `norm` 未赋值先引用致全站崩（我 P2 引入）；8c09e31 配置弹窗加「仪表盘」按钮（不必跑测试即可看仪表盘）。
- **P3**：`_gen_index.py render_regression` 从 resolved buglog 自动提取问句+预期 → `_regression.md`；serve 加 `regressionList`；仪表盘加「回归关注」节；skill 补说明。
- **诚实边界**：自动生成回归清单 ✅；**不**自动执行（数据前提逐案 + 语义预期无法可靠转断言·虚假绿风险）；关联 case_ref 在常规跑已覆盖。
- **验证**：`/_test/buglog` 返 regressionList（B001）+ `_regression.md` 解析正常。**待浏览器验证**：仪表盘「回归关注」节渲染。

### ✅ CB 飞轮 buglog 扩建 P2 仪表盘（commit 5f92a05 · **用户手动 push**）

接 P0/P1，落地 DeepSeek 方案的「仪表盘 UI」（按 CB 反评价修正）。详见 [revision-log §5](revision-log.md#L226)。

- **数据源**：serve.py 加 `GET /_test/reports`（report-*.json 现算 pass%/p50/p95）+ `GET /_test/buglog`（复用 _gen_index.load_entries·单一解析源）。
- **UI**：test-board.js 抽屉加「运行/仪表盘」tab（保运行 UI·治 §5.4 矛盾）+ 4 KPI + 最新报告 + 未解决清单 + 历史复发；css 复用既有色（#0F6E56/#D85A30/--emc-accent）非森绿·全 ASCII。
- **验证**：serve.py 解析 + 数据函数实测 + JS 核查 + 优雅降级。**待浏览器验证**：`?test=1` → 仪表盘 tab。
- **defer**：P3 回归自动生成（需改 test-cases.js 数据流）。

### ✅ CB 飞轮 buglog 扩建 P0/P1（commit c4f3cd6 · **用户手动 push**）

用户让 DeepSeek 出 EMC 飞轮扩建方案（bug 采集 skill + 用例 log + 仪表盘 UI）→ 要求我按 CB 标准（agree/disagree/partial + 证据）反评价 6 方面 → 落地修正版 P0+P1。详见 [revision-log §5](revision-log.md#L226)。

- **CB 反评价**（verify-before-accept）：扩建路径 **agree**；映射表/buglog/UI/skill **partial**——emoji 撞编码规范 1 / palette 把品牌橙 `#D97757` 当失败色撞设计语言 / 漏 `flywheel_audit.py` + EMC-SUM 结构化数据 / skill「自动触发」前提不成立 / §5.4「替换抽屉」与「不删」矛盾；客观评价=方向对·瘦身后合理。
- **P0 落地**：`tests/buglog/` open/resolved + `_template.md`（ASCII 标签）+ B001 种子（CB-09 multi-extract·resolved·复现 4）+ `.claude/skills/bug-collector` 采集 skill（去自动触发·委托脚本刷索引）+ `tests/_index.md` 飞轮总入口。
- **P1 落地**：`_gen_index.py` 确定性索引生成器（generate + `--check` CI·对标 validate_field_dict_sync·非 LLM 维护）→ 自动产 `_index.md`/`_trend.md`（recurring=派生属性非独立目录）。
- **验证**：pytest 220 passed（1 既有 fail `test_final_prompt_stays_lean`·非本次范围）+ buglog `--check` 通过。
- **defer**：P2 仪表盘（复用 `#0F6E56/#D85A30/#4285F4`·tab 非替换·下一检查点）/ P3 回归自动生成（需改 test-cases.js 数据流）。

---

## 📅 2026-07-28（**v2→v3 架构转型 + 修复**·commit+push）

### ✅ EMC Hotfix R3（multi-extract 死循环·commit 982a454·**待浏览器验证**）

用户上传面层 + 问「裁剪出西陵+伍家岗」→ FC 死循环→错报"需要数据"。DeepSeek rootcause + CB。

- **CB 反评价**：DeepSeek 诊断准；方案2（_norm_where 拆逗号）agree；方案3（后端 in）**已存在**（核实）；方案5 defer；**我补漏报**——契约 `when`（=FC 工具 description）写"抽单要素"误导 LLM。
- **M1** [`_norm_where`](api/geo_routes.py#L127)：op=in+逗号→拆 list（实测 `MC/in/西陵区,伍家岗区`→两区 list）。
- **M2** [router FC sys prompt](ai_qa/router.py#L60)：加多要素提取段 + `where=in/A,B` few-shot。
- **M3** [契约 extract_feature](ai_qa/tool_contracts.py#L171)：voice/when/failure_modes/where-hint 去"单要素"+加 `in/A,B`（改 LLM 可见描述）。
- **验证**：`_norm_where` 实测 + pytest 221 passed。**待浏览器验证**：重启后端→上传面层→「裁剪出西陵+伍家岗」→一次出两区·不死循环。

### ✅ EMC 渐进 token 显示三连修 S6/S7/S8（commit 07b3736/8228fc9/3aaaaeb·**待浏览器验证**）

用户验证：结论渐进 token 通了，但诊断思考仍"卡住"。要求 DeepSeek 式思考可见。

- **S6 Flash reason 渲染**：[`panel.js onReason`](frontend/js/ai_qa/panel.js#L1273) 去 `if(isFlash)return`——Flash 默认下 reason 也逐 token 渲染（之前被丢·致"卡住"）。
- **S7 FC 流式**：实测 V4 flash FC stream 吐 reasoning_content → [`llm.py`](ai_qa/llm.py) `chat_with_tools_stream`（实测 87 reason chunk+正确 tool_call）+ router FC→SSE + api.js `streamFcDiagnose` + stages fcDiagnoseStep 改用。**诊断思考渐进可见**。
- **S8（用户猜中）去 is-flash 折叠**：[`panel.js:1087`](frontend/js/ai_qa/panel.js#L1087) 去 `is-flash` class——[`ai_qa.css:268`](frontend/css/ai_qa.css#L268) `.is-flash .reason-body{display:none}` 把 Flash 思考藏了。去后流式展开·完成收起 DeepSeek 同款。
- **验证**：:8000+:8080 FC 实测 408 reason line 流式 + pytest 221 passed 零回归。**待浏览器验证**：硬刷 → 诊断思考逐字蹦 + 结论渐进 + 完成收起「Thought for Ns」。

### ✅ EMC Hotfix R2（commit 4322504·重启后实测两问题·**待浏览器验证**）

重启验证 3 WS 后报：①渐进 token 仍无 ②复杂问 finalStep 超时→降级结论泄 `density({...})`"代码块"。双源核实 DeepSeek 两 ROOTCAUSE 报告 + 我方实测。

- **S1 SSE 真·渐进流式**：DeepSeek 诊断 urllib BufferedReader 缓冲——**实测复现**（`read(4096)` 攒包 vs `fp.read1(4096)` 逐 chunk）。[`serve.py _send_streamed`](frontend/serve.py) 改 `read1` + `TCP_NODELAY`。不采纳 DeepSeek A（绕代理+COR）/ C（httpx 重写）。
- **S2 finalStep per-phase 超时**：[`api.js`](frontend/js/ai_qa/api.js#L32) `answer`=45s（用户定）/ `agent_step`=30s / 其余 25s。修正 WS1 F1.5 的 25s 一刀切（复杂 finalStep 需 25-35s）。**关键洞察**：「无渐进 token」是 finalStep 超时的副作用（降级走静态串非流式）。
- **S4 降级结论清洗**：[`_composeDegradedConclusion`](frontend/js/ai_qa/harness.js#L424) 去「第N轮·动作: tool(params)→」前缀·治"代码块"泄漏。
- **defer**：S3（context 瘦身·S2 已治超时）/ S5（2D/3D 视角——density mode 语义 2d=热力图/3d=网格柱·需 mode API 重构非 hotfix）。
- **验证**：pytest 221 passed+3 skipped 零回归 + serve 编译/死锁无回归。**待浏览器验证**：重启 serve → ①简单问 token 逐个蹦（S1）②复杂问不超时+干净结论（S2+S4）。

### ✅ EMC v1.0 聚焦修复工程·3 WS（commit b2a24ab+943ced4+afa5db4·CB-08·**待浏览器验证**）

双源核实（3 Explore agent + DeepSeek `DEEP_DIVE_2026-07-28` CB 反评价）·架构骨架 Smart/Dumb/Orchestrator 完好·**3 个实现层缺口·不推倒重来**。plan：`emc-v1-0-report-2026-07-28-01-llm-1-emc-inherited-swing.md`。

- **WS1 耗时**（b2a24ab）：Flash 默认（去 deliberate 串行）+ 收紧 `_needsDeliberate`（去 method>=3 过触发）+ **SSE 流式**（[serve.py](frontend/serve.py) HTTP/1.1+分块 flush·前开发卡 HTTP/1.0 默认·致 flush 无效）+ 超时 75→30s/FC 20→9s + profile_fields localStorage 缓存 + per-phase 计时。→ 简单 ~12-18s（设计 6-11s 需 1-LLM 模式·长期 F10）。
- **WS2 识别**（943ced4）：**F2.0 元凶**——[`pickVisiblePointLayer`](frontend/js/ai_qa/tools.js#L664) 漏 colorMode='polarity' 上传点层（默认·[state.js:696](frontend/js/state.js#L696)）→ 全点工具报"缺数据"·**飞轮 L2-group 测不出·用户独立上传必中**·加 any-point 兜底；+ hidden 纪律一致（query_layers/预热）+ e2e-seam 例间清点层（治 FC-12）+ 字段字典中文 fuzzy+补规划/人口域 + **新 CI [`validate_field_dict_sync.py`](tests/validate_field_dict_sync.py)**（即抓 zone 漂移）。
- **WS3 路由**（afa5db4）：**reframe「工具选型 100%·填参才是瓶颈」**·[router.py](ai_qa/router.py) FC sys prompt 加参数提取 few-shot（buffer.center/compare.boundaries≥2/overlay.layer_a,b）+ eval 加 `run_fc_param_eval`（测参数·治 eval 测不到"模板对参数空"）。
- **据实 drop**：F1.3（zonal/compare 是 single 类别走 runTemplatePath·非 while-loop）/ F2.1-3（C2 门已对·元凶在 F2.0 下游·field-role 门会重造假缺数据）/ F3.2-3（前端 validateParams 已捕获缺槽·compare alias 撞 zonal boundary）。
- **验证**：pytest **221 passed**+3 skipped 零回归·serve/boot 干净。**待浏览器验证**：重启 serve + 硬刷 → 上传 **polarity 点层**（非 L2-group）→ density 出图（F2.0 核心）→ 渐进 token 蹦出（F1.4）→ ~12-18s。

### 🎯 架构转型：v1 三阶段 → v2 单次 LLM + Function Calling → v3 做对

用户 + DeepSeek 产出 v2 改良混合架构（[SUMMARY](docs/catch-ball/emc-arch-deepdive/SUMMARY.md)·61 决策 D041-D068）·废弃 v1 三阶段 + 信息卡·改用 DeepSeek V4 原生 function calling + 契约 Schema。第三方实施（5.243-5.245b）→ GLM 审查发现 3 CRITICAL + 6 HIGH → v3 修复（7858d5a）→ 用户实测发现 `reg.filter` 崩溃 → v3.1 修复（657c2e3）。

### ✅ v3.1 reg.filter 崩溃修复 + SCAN P1 边界（revision-log 5.246·commit 657c2e3）

- **根因（治用户全部 4 问题）**：`formatRegistry()` 返**字符串**·`applyQualityDefense` + `_composeDegradedConclusion` 对其调 `.filter()` → 类型错误崩溃 → `[请求失败]` + 胶囊消失 + dock 永转（感知 70s+）。
- **修复**：`getArtifacts()` 替代（返数组）。+ SCAN P1：zonal_stats 补 _NEEDS_POINT / _parsePlans strip domain_lens 前缀 / _fc_fixes 传回 / domain_lens 默认返 []。
- **验证**：pytest **221 passed**+3 skipped 零回归 + serve/boot 干净。**待浏览器验证**：重启 serve + 硬刷 → 「分析情绪热度」→ FC → 出图 → applyQualityDefense **不崩** → 胶囊显示 → ~10s。

### ✅ v3 修复第三方 v2 的 3 CRITICAL + 4 HIGH（commit 7858d5a）

- **C1**：`chat_with_tools_fallback`（DeepSeek→Ark→讯飞 provider 链·治 FC 单点故障）。
- **C2**：执行前 data gate（`_normalizeFcDiagnose` 检查 layer_meta.has_point + _NEEDS_POINT→request_upload·治 5.242 数据感知回归）。
- **C3**：domain_lens A+B 混合（`_deriveDomainLens`：先 parse FC content `[domain_lens:xxx]`→空则关键词推导）。
- **H2**：`_PARAM_RANGES`（radius/cell_size/top_n 等 minimum/maximum）。**H5**：timeout 45s→20s。**H6**：删前端 `_validateFcParams`·后端 router 调 `validate_tool_call`。

### ✅ 第三方 v2 实施（5.243-5.245b·commit 810139c→143f3da）

- **5.243** v2 FC 后端+前端（contracts_to_tools_schema + chat_with_tools + fcDiagnoseStep + D062 校验 + D065 数据变化检测）。
- **5.244** v2 CPD plans→胶囊（D068 _plansToCapsules）。
- **5.245** FC diagnose 兼容性修复（7 项：tool→skill 映射 / normalizeCard 补全 / intent 推导 / signal+timeout / usage 统计）。

### ✅ v1 三阶段实施（5.231-5.242·已被 v2 取代·代码保留过渡期）

- 5.231-5.240：9 模块 v1 三阶段（select_candidates + FILL_CARD + PLAN + dispatch）。
- 5.241-5.242：selector trigger + 数据感知修复。
- **v2 取代**：v1 diagnose 管线（select_candidates / FILL_CARD / PLAN / dispatch）被 FC 取代·但代码保留（Phase 4 清理待 v3 稳定后）。

### 🔄 遗留（待处理）

- **浏览器验证**：重启 serve + 硬刷 → 测「分析情绪热度」+「剪裁西陵区」→ 确认 reg.filter 不崩 + 胶囊显示 + ~10s 速度。
- **Phase 4 清理**：v3 稳定后删 v1 diagnose 管线（select_candidates / FILL_CARD / PLAN / dispatch / triggers·~500 行）。
- **测试飞轮**：围绕 v2/v3 FC 架构更新飞轮机制 + 模拟测试内容（开 plan）。
- **FC 稳定性**：DeepSeek V4 FC 复杂场景（R1 社区报告空响应/循环）·fallback 降级。
- **plans[] 常空**（R2）：LLM FC 模式倾向不产 content → CPD plans 设计名存实亡·finalStep 胶囊兜底。
