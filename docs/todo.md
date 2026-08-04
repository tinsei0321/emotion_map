# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。
> 📝 详版历史 = [revision-log §5](revision-log.md#L226)（永久审计底）·本文件只记当前 + 计划。
> 📌 **架构版本**：v1（三阶段 5.231-5.242）→ **v2（单次 LLM + FC·5.243-5.245b·第三方实施）** → **v3（v2 做对·5.246-657c2e3·GLM 修复）** → **v3.1**（reg.filter 崩溃修复 + SCAN P1）→ **v3.2**（CB-09 bug 修复·D057 修订·代码自动扩展·全自动多步执行·fix/emc-buglog 分支 7 commit）→ **v3.5**（CB-10/CB-11 系列·merge 多图层 + 只说不做根治）

---

## 📅 2026-08-04（CB-16 大南门数据专题 · 数据接入 EMC 出口链路闭环 + R7 截断修复 + Wave 1/2/3 出口 + CB-15 P0/P1 数据认知）

### 🔄 Wave 3 · 实施完成 + 检查请求已发（待两组 SCAN·先验后推）

- **范围**：出口深化最后一块（多卡 + validate_outlet_fields CI + 可感知计算器 2a·B 评论↔POI 再后置）
- **两组预检反评价**：草案可行·无 P0（glm 计算器分步 2a/2b·多卡同 domain 去重·Codex 表达式共享）
- **多卡落地**：resolve_outlet_ids（跨 domain 多卡·同 domain 最高分）+ build_outlet_schema 返 cards + build_outlet_schema_single 兼容 + /outlet_card 返 {cards, card} + 前端多卡渲染
- **validate_outlet_fields CI 落地**：tests/validate_outlet_fields.py（正则提取消费字段→死字段 fail/缺消费 warn·2 passed）
- **可感知计算器 2a 落地**：compute_perceptible_metrics（极性类·关键词命中标注·缺失诚实·B 类条件等式后置 2b）
- **验证**：pytest 269 passed（+3）·端点多卡（renewal_demand + checkup_satisfaction·card[0] 兼容·perceptible_metrics 有值）
- **检查请求已发**（0862f09·Wave 3 实施后检查·待两组 SCAN）· **可 push**（0862f09 待推）
- **后续**：Wave 3 余（2b 条件等式·可选）· Wave 0-3 出口抽象层完整

### ✅ CB-15 P1 · 实施后检查通过 + P2 补修（**可 push**·先验后推）

- **范围**：让地点进 EMC 问答管线（A buffer 中文 POI + C lookup_place + D 归因落点模板·B 评论↔POI 后置 Wave 3）
- **两组预检反评价**：四子项方向全对路·无 P0
- **A 落地**：`/geo/buffer` fallback search_place（preset 优先·top-1·无命中诚实 400·WGS84·只对 str center）
- **C 落地**：lookup_place 契约后端 + 前端执行混合（TOOL_CONTRACTS + paradigm + tools.js + SKILL_DEFS + GEO_VERB_KW + track ID F_013）
- **D 落地**：_extract_emc_value 扩 `+` 多字段合成 + 暴露 poi_names/place_name_source + 修 :179 陈旧文案
- **两组检查反评价**：通过·可推（buffer 中文名 200/400 实测·drift 既有性回测确认）+ **P2×4 补修**（触发词去"附近"·source 只列非空·docstring 修·required_slots 对齐）
- **验证**：pytest 266 passed 零回归·括号平衡×3
- **backlog**：validate_skill_params 7 工具 drift（density/buffer/clip/overlay/zonal/extract/merge·paradigm when 同步）
- **✅ 可 push**（两组已验）· **待用户 push** · Wave 3

### ✅ Wave 2 / CB-15 数据认知 P0 · 实施后检查通过 + P1/P2 补修（**可 push**·先验后推）

- **范围**：下钻链最小闭环（place_name 双源融合 + poi_names + /grid/pois + 3220 接入 + 去重）
- **两组预检反评价**：P0 实锤 place_layer 未读 3220（1270≠3220·FC 字段错配）→ _read_pois_geojson 适配层 + _load 合并 + _dedup_pois·P1 语义分层（polygon 保留边界名·grid POI 优先·最近质心）+ place_name_source
- **两组检查反评价**：主体通过 + **glm组 P1**（_dedup_pois 连锁店误删·_seen 先锁 name → name+坐标容差联合判定）+ **Codex P2**（create_square_grid 输出 cell_id 列）+ **测试边界 3 新增**
- **验证**：all_pois=4342（恢复 32 误删连锁店）·grid/pois 200（count=32 CBD）·**pytest 261 passed 零回归**（+3 新增）
- **✅ 可 push**（两组已验）· **待用户 push** · P1（lookup_place/归因落点模板）

### ✅ Wave 1（macro 出口）· 实施后检查通过 + P1/P2 补修（**可 push**·先验后推）

- **范围**：renewal_object_identify（更新对象识别·macro）+ checkup_dimension（体检四维度·含 macro）
- **两组预检**：Codex P1（checkup_dimension 四维度×单尺度语义错位→`[scale=xxx]` 槽位限定）+ claude组 P1×3（① `_extract_emc_value` 统一收 rows/features 单入口 ③ DOMAIN_KW 补「城市体检」长词 ⑤ data_base rows 分支·N=单元数）+ rows 可达性缓存（`_lastToolRows`×3）
- **两组检查反评价**：主体通过（5 环节正确·单测 23 passed）+ **glm组 P1**（runAllToolCalls rows 处理·else 误判 + 守护漏 hasRows→三独立 if + hasRows 放行）+ **Codex P1**（跨轮重置 `_lastToolRows = null`）+ P2×2（while-loop rows 捕获 / 测试改名）
- **测试**：pytest 253 passed · 括号平衡 · test_outlet_macro.py E2E 两场景全过
- **✅ 可 push**（两组已验·先验后推）· **待用户 push + 浏览器复验** · **Wave 2（CB-15 前置·后置）**

### ⏸️ CB-15 数据认知（Wave 2 前置·用户定后置·Wave 1 先行）

### ⏸️ CB-15 数据认知（Wave 2 前置·用户定后置·Wave 1 先行）

- 格↔POI sjoin + place_name 双源 + /grid/pois 端点（讨论稿共识已立·落地未做）
- **排进待办**：Wave 1 完成后推进（用户定优先级）

### ✅ R7 补修（commit a42fb1a·**待用户 push**·两组检查反评价）

R7 修复发实施后检查 → 两组 SCAN：**claude组 P0 发现** `lastIndexOf('.')` 误切 markdown 列表标题「**4.**」句点 → 结论第 N 点落 1500 边界时复现原 bug（场景 4 实测）→ **方案 A 去 `.` 切句符**。
- 采纳：Codex 断句符补 `！？` + 悬空编号行剥除（`/\n\d+\.\s*$/`）+ claude组 文案微调（"已精简"→"已截断保留要点"）+ 补边界测试
- **新增** `tests/browser/test_r7_truncation.py`（e2e-seam 直测真实 JS 逻辑·3 场景：多要素完整 / 失控截断无空标题 / {{show:}} 完整）
- **验证**：新测试全过 + 括号配对 +2/+2 + **pytest 249 passed 零回归**
- **待用户 F5 复验**

### ✅ R7 结论截断修复（commit 0aff59e·**待用户 push**·用户实测发现）

用户浏览器实测「大南门·二马路片区更新需求分析」发现结尾「**4.**\n…（结论已截断）」→ 问"未完成"。
- **根因**：R7 防线（harness.js applyQualityDefense）`>800 字 → slice(0,800)` 字符级硬切·阈值过低（用户定：多要素结论超 800 正常）+ 切点不感知 markdown（切「**4.**」标题后）+ R2 按钮被切连带 + 文案误导
- **修复**（纯 harness.js）：阈值 **800→1500**（用户定）+ 切点**结构回切**（句号/换行·治空标题）+ **R2 移 R7 后**（按钮保留）+ 文案场景化
- **验证**：括号配对完整（+7/+7）·Playwright 页面零 console 错误·**pytest 249 passed 零回归**
- **待用户 F5 复验**：重问「大南门·二马路片区更新需求分析」→ 应不再出现「**4.**」空标题

### ✅ 大南门·二马路数据接入 EMC 出口链路（commit c792c5d·**待用户 push**）

交接卡【下一步】核心待续项打穿——Wave 0 端到端演示数据场景。两组预检通过（Codex 必补项 + claude组 建议全纳入）→ 实施 → 验证 249 passed。

- **backfill**：`SCRIPT/backfill_ermawu_coords.py`（一次性·id_e 断言·保 BOM·备份·生成器修复 TODO）→ T1/T2/T3 共 2400 行补 lon/lat
- **注册点层**：`core/geo_registry.py` 追加 `ermawu_l3l4_t{1,2,3}`（level='L3L4'·富归因列原样保留）
- **边界登记**：`DATA/boundaries/presets/manifest.json` 加 `damanmen_area` + **复制 geojson 进 presets/**（Codex 必补项·name 属性改为片区名）
- **测试**：`tests/test_geo_registry.py` 新建 4 例 + `test_outlet_schema.py` +1 真实聚合出卡
- **端到端验证**：/geo/catalog 暴露 3 ermawu 层 + damanmen 边界 → /geo/zonal_stats 578 点（polarity_index 0.73·文化）→ /outlet_card 命中 **renewal_demand 需求分析卡**（需求强度 0.73·停车难·N=578）
- **pytest 249 passed（+7·零回归）**

### 待续
- **浏览器 EMC 真实问答肉眼验证**（问"大南门·二马路片区更新需求分析"→ 应出诊断卡 + 分析执行 + 出口需求分析卡·LLM 选层/路由走真实链路）
- **时间轴 manifest（_time_manifest.json）**（用户定·与需求分析是两件事·后置）
- Wave 1 macro 出口 / Wave 2 place_name 精确源 / Wave 3 可感知计算器（交接卡后续）
- CB-16 Wave 0 完成检查（两组 SCAN 待反评价·③f 发起）

---

## 📅 2026-08-03（CB-13 反评价闭环 · 多步问最终收敛 + PRM-08/CPD 根因定案）

### ✅ CB-13 反评价闭环（revision-log 5.254，commit e052fe7 · **用户手动 push**）

- **多步问最终收敛（CB-12→13 闭环）**：RST-L06 两轮连续 PASS·while-loop 根治（F_002=4）·pro 0 守住
- **PRM-08 根因定案**（两组一致）：FC 选型偏离 compare→extract_feature·非路由退化/非测量层·compare 缺确定性路由兜底 → CB-14 修（先取证）
- **CPD-L01/L02 = 测试基建文件名过期**（Codex 实锤）：`test-cases.js:8` 引用已改名的 `xiling_wujia_*`·1 行修复·产品引导逻辑正常
- **上轮 3 注意点已落地**（_hasSeq 收紧·Pro chain 前置·recover 链前置）
- **反评价**：8 agree / 2 partial / 0 disagree·learning 入库 KNOWLEDGE §3
- **backlog 修正**：MOD_LLM.F_002 79 次=调用数非 fallback 数

### ✅ CB-12 B3-verify-05 全量重测闭环（revision-log 5.253，session B3-verify-05 · **用户手动 push**）

- **B3 全量 26 例（含 RST-L06 新增）pass=23（88.5%）历史最佳**·RST-L06 多步问 PASS（tools=clip,density）→ **多步问修复收敛·CB-12 闭环**
- **PRM 9/10**（PRM-08 compare 链路 fail·tools=extract_feature 单工具·boundary[ERR]）·**F_002=4**（≤5 阈值·while-loop 早停生效）·**pro 0**·计划命中 16/20 步
- 0 timeout·误杀/漏判 0·p95 50s·11.2min
- **残余（非阻塞）**：PRM-08（compare 路由退化）+ CPD-L01/02（引导态 hint 未推）·转 backlog
- **下一步**：进入 CB-13（让 Codex/glm 组检查 PRM-08/CPD 残余 + 多步问修复确认）

### 待续

- PRM-08 compare 确定性路由兜底（CB-14·先带 session 取证 FC 选型）
- CPD-L01/L02 测试基建 1 行修复（CSV 改 resolvePoints('L1-T1')）+ CPD-L03 硬断言
- 发版候选评估（B3 88.5% 达标上沿·整体评估）
- MOD_PLACE 渲染风暴 + fallback 重试（backlog）

---

## 📅 2026-08-02（CB-12 · 链路体检 + PRM 派生 + 尺度判定 + 触发入口统一 · G0-G6a）

### ✅ CB-12 while-loop 根治 + B3 88% 历史最佳（revision-log 5.252，commit f6e415a+3abb503 · **用户手动 push**）

- **根因定案**（glm gate 连锁被 localStorage 铁证推翻·Codex recover 缺口正确）：FC 成功返 unknown/multi → recover 跳过 → while-loop
- **根治（f6e415a）**：recover 扩展触发 + 筛选守卫放宽 + gate per-template + B3 清 gate + while-loop 早停
- **B3 88%（22/25）历史最佳**·PRM 9/10·p95 46s·9.8min·演进 4%→88%（22 倍）
- **Codex 2 项已修（3abb503）**：early-stop 计划完成度 + PRM-08 测量伪影（多 boundary 收集）
- **剩余**：PRM-08 断言修复后应 10/10（B3 全量留发版前）·MOD_PLACE 风暴 + fallback 重试（backlog）

### ✅ CB-12 B3 根因定案闭环 + trace.log 业界级 + pro 停用（revision-log 5.251，commit 3bb2f76+f4f78e2+e7cb7b9 · **用户手动 push**）

- **根因定案**（glm组 trace.log 铁证·推翻"API 慢"误判）：慢 = while-loop 多轮 × pro/旧模型（F_002=18·pro 37）·**非 API**（用户 key 正常）
- **trace.log 业界级**：session 字段 + 轮转 + `tools/trace_query.py` + 文档 + CB 取证步骤 0
- **while-loop 修复**：stripped 阈值回退 3→2 + 词边界守卫（Codex slice(1) bug 修 slice(2)）+ zonal 前置检查
- **pro 停用**（flash 足够）：UI disabled + 强制 flash 三层守卫
- **B3 08 重测 80%**（PRM 7/10·pro 0·F_002 8·session trace 验证）
- **backlog**：MOD_PLACE 渲染风暴 + fallback 重试（Codex 观察）

### ✅ B3 大失败根治（revision-log 5.250，commit 7df8d75+8e67848 · **用户手动 push**）

B3 重测大失败（4%·timeout 22/25·t_p50=93s）→ 两组根因核查共识 + P0 修复：
- **搜索改素材注入**（不 bypass·走 finalStep + 防线）·SEARCH_KW 删「情绪地图/对比/介绍」+ 概念问实据门
- **超时控制**（前端 AbortController 15s + 后端 90→30s 不 retry）
- **episode 404 修复**（8e67848·1362167 误删装饰器·已提交回归）+ serve.py 脏检查（未提交改动→[WARN]·用户诉求：每次开网页都最新代码）
- **验证**：episode 200 + 脏检查 WARN + pytest 225 + 体检 20/20（T1c 搜索 27.3s 无 bypass）
- **待**：B3 重跑（API 好时段·应恢复到 ~13/25）

### ✅ G6b 联网搜索 + G6c 连问拆解 + G5 derive 增强（revision-log 5.249，commit 1362167+aaa8319 · **用户手动 push**）

- **G6b 联网搜索**：`llm.search_chat`（DeepSeek Responses API web_search·服务端执行）+ `/aiqa/search` + SEARCH_KW + general 搜索分支（失败 fallback）·T1c「宜昌城市更新政策」32s PASS
- **G6c 连问拆解**：`panel.send` 分句（≤2 句·逐句完整管线）·T8c「西陵区？伍家岗区呢」PASS
- **G5 derive 增强**（B3 重测暴露）：zonal boundary 精确区要素 + cell_size 正则放宽 + 路由修正（周边→buffer·对比→compare）
- **验证**：pytest 225 passed + 体检 20 例全 PASS（C2a 宏观无归因词·R10 生效）

### ✅ CB-12 链路体检套件 + PRM 参数派生 + 尺度判定（revision-log 5.248，commit f33ac52 · **用户手动 push**）

用户关切升级「链路通畅 + 体验达预期」→ 讨论报告 + Codex/glm组 双回应 + 用户拍板 4 项（连问最简版排 G6c·scale 前移 G1·出口差异化三层合一·性能分档软目标）。落地 G0-G6a：

- **G0 体检基建**：`test_link_checkup.py`（10 类问句四件套断言 + C2 示例①/② + R9 单测）·**18 例全 PASS**
- **G1 PRM 派生 + scale 判定**：`deriveMissingParams` 四参数确定性派生 + 去双处三字段硬编码 + `_deriveScale` 三源解析 + FC prompt 尺度段 + 内容断言·PRM 重灾区全 PASS
- **G2**：final prompt 排版段 + 契约强化
- **G3 触发入口统一**：`landuseTriggerOf` 单源 + B002 deferFinal
- **G6a 出口差异化**：finalStep 尺度约束 + R10/R11 防线
- **C3**：buglog 5 条移 resolved（OPEN 3）
- **G6b/c 设计文档**：搜索 + 连问（排期最末）

**验证**：pytest 224 passed + 体检 18 例全 PASS（R9 单测 PASS）

### 待续
- G5 性能重测 B3（PRM 修好后 p95 回落验证）
- G6b 搜索能力（设计已定·待 API 确认）
- G6c 连问拆解最简版（设计已定·待实施）

---

## 📅 2026-08-02（CB-11 · merge 多图层 + 「剪裁+合并」只说不做根治）

### ✅ merge 多图层 concat（commit 9f84eac + bea7cbd·Codex+glm组 方案 A）

**问题**：merge 工具不支持多图层（后端只有单 boundary）·LLM 猜 `layer_list` 被拒。
**修复**：后端 `layers` concat（CRS 统一 + `_source_layer`）+ 契约 layers + one-of 校验 + alias 解析 + union 链退役。
**用户实测「卡读秒」** → P1 inline `_tcs is not iterable` + P2 auto-merge 未调 `onFinalDone` 全修（bea7cbd）。

### ✅ 「剪裁+合并」只说不做根治（commit eb42d39 + fc242c2·Codex+glm组 共识）

**问题**：用户问「剪裁出西陵区…合并成一个图层」→ 实测执行只有 extract+merge（**无裁剪**）·结论却声称「执行裁取操作·严格落在西陵区边界内」——**只说不做复发**。
**根因（Codex+glm组 一致）**：防线系统性盲区——L1/R1-R7/零图层守卫全验图层存在·**无一条验操作是否执行**。
**修复**：
- **R9 步骤描述对账**（applyQualityDefense 新防线）——结论操作动词（裁取/裁剪/叠置/缓冲/筛选/抽取）→ 对账 toolHistory 工具集·未执行标注「⚠️ 未在工具执行记录中」
- **两阶段补全（A·用户拍板）**——`buildLanduseCompletion` 问句含「裁剪+合并」→ 先 3×overlay(intersection) 裁剪 → merge 裁剪产物（$n 引用）·不再互斥吞裁剪语义
- **merge observation 加来源标注**（被合并图层名·finalStep 知是否已裁剪）
- **fc242c2** hover 层存在性 guard（清理产物后轮廓层被删·旧 hover 报 lyr-Lxxx-line）

**验证**：Playwright 复现——extract→3×overlay→merge 6 步·**面积 17.3km²（西陵区内·非全量 66.5）**✓ 先裁剪再合并真执行 + pytest 32 passed + **用户自测成功** ✓

### ✅ 待续项推进（commit 679191f + 40a518b + c788114）

- **679191f**：修 clip-then-merge 偶发多 1 个 overlay——`runAllToolCalls` 结果补 `_inlineExpanded`·orchestrate 不再二次 autoExpand·Playwright 验证 5 步（extract→3×overlay→merge）
- **40a518b**：G5 命中遥测 localStorage 持久化（`emc_completion_hits_v1`·跨会话·驱动渐进退役）
- **c788114**：族 D 面层多类用地分段色——merge 产物含多类 DLMC → `landuseFillColorExpr` 数据驱动分段色（每类一色·严格按图例·不再主导色单色）

### 待续
- 触发入口统一 + PRM 参数填充瓶颈 + CPD-L01/L02
- 已知小瑕疵：「未实际生成」措辞残留（LLM 措辞·非功能 bug）

---

## 📅 2026-08-01（今日·CB-10 闭环 + 两天攻坚启动）

### 🔄 CB-10 闭环（SCAN → 反评价 → Codex 二轮审核 → plan 定稿）

- **CB-10 SCAN**（Codex+GPT-5·[CB10-EMC全面审查](docs/catch-ball/scan/CB10-EMC全面审查_Codex-GPT5_2026-08-01.md)）：综合 **6.0**·核心 = plans[] 管道未接通 / 编排器泄漏智能 / FC prompt 无守卫丢纪律 / 文档滞后 / test_final_prompt_stays_lean 回弹 / buglog 状态双源
- **反评价落盘**（[cb-journal.md](docs/catch-ball/cb-journal.md) CB-10 ②）：**9 agree / 0 disagree / 5 partial**·Auto-Check 四项合规
- **Codex 二轮审核**（[CB10-反评价二轮审核](docs/catch-ball/scan/CB10-反评价二轮审核_Codex-GPT5_2026-08-01.md)）：反评价整体公允·**7 条修正全 accept**（B005 扩 `_autoExpandOverlays` 成功路径 / B007 guard 并 P0-1 / 完成度守卫代码层追加 / 守卫四段 / P0-4 分解 / 词表集中+边界 / CPD-RESERVED 空骨架）
- **两天攻坚 plan 定稿**：`C:\Users\Hi\.claude\plans\claude-code-emotion-map-purring-ritchie.md`
- 用户拍板：① plans[] 留位给 CPD（预留接口）② 极性纪律走 prompt 恢复+守卫 ③ todo 按已提交重写 ④ 反评价稿落盘 CB 文件夹

### 🔄 Step 0 即时同步（cb-journal 已写·本次补齐三文档）

- ✅ cb-journal CB-10 ② 补 Codex 复核结论（7 修正全 accept）
- ✅ KNOWLEDGE 追加 2 条 learning（← CB-10：FC prompt 无守卫删四段·CPD-RESERVED 空骨架）
- ✅ todo.md 当日段（本节）
- ⬜ emc-fix-progress.md 头 + §三待修
- ⬜ revision-log §5 bullet

### ✅ Codex 验收「有条件通过」+ 4 项收尾修复（commit 742840d）

Codex 验收报告（[CB10-两天攻坚验收](docs/catch-ball/scan/CB10-两天攻坚验收_Codex-GPT5_2026-08-01.md)）：**7 修正全落地·无回归·不撞红线·有条件通过**。我方反评价 8 agree/1 partial 落盘 cb-journal。修复 4 项收尾 + 6 问题：

- **MED #1**：`_gen_index.py --check` 忽略「最后更新」时间戳行（逐字节比对过分钟必红·CI 恒红）→ 跨分钟验证通过
- **LOW #2/#3**：emc-fix-progress 更新/总计行 → b2949e1/v3.3/220 + _cb-index hash 同步
- **LOW #4**：test_final_prompt_stays_lean docstring <2KB → <3KB（口径统一）
- **INFO #5**：_POL_MAP overall 行并入 emc-patterns.POLARITY_KW
- **条件 3**：domain_lens A 部损失记入待修表（非静默无损失）
- **条件 4**：**B3 全量 LLM 回归跑完**（report-2026-08-01-02-llm）——**25 例 pass 13 / fail 12（52%）**·PASS 全在成果范式(RST-L01~05 产出图层)+Smart 交流(SMT)+UI 渲染(UI)；FAIL 集中在**参数正确性 PRM-01~10 全 fail**（zonal/buffer 边界没对上·PRM-06 走 extract 应 zonal）= 既有「填参路由瓶颈」（CB-08 已识别·非本次修复引入）+ CPD-L01/L02（既有 CPD 问题）·t_p50=19s t_p95=66s
- **待续**：PRM 参数填充瓶颈（zonal/buffer 边界·CB-08 F3.1 范畴）+ B008/B006-B defer

### ✅ 飞轮修复 + 族 A 主通道定型（commit 36e3084→26aa9b8）

**飞轮 5 项修复**（Codex 飞轮审查 F-1~F-13）：
- F-1 计划命中改按实际执行通道 planSteps（36e3084）
- F-2 产物语义断言（productLayers 读口 + 消极热力图色板/overlay 交集 2 例·ed60804）
- F-6 no-llm 9 失败建归属 `_deferred.md`（acdff5e）
- F-4 `--tier smoke/regression/full` 三档拆分（5f2e39c）
- F-8 `--collect` 失败→buglog 草稿（d164498）

**族 A 主通道定型**（Codex 决策评审选 A·9 agree）：
- a5eb3e1：runTemplatePath 内联扩展（治 B002 半成品 answer·全步完成→单次答案）·浏览器验证 43s 一次出 3 层
- 26aa9b8 三件收尾：① 抽 buildLanduseCompletion（intersection+union·三处共用）② N/M 完成度判定共享出口 ③ 命中遥测 + 45s 单技能预算兜底
- **主通道 A 定型**：LLM 多 call=机会通道 / 单 call+内联扩展=常态主通道 / recover=失败兜底·B 降级为模型换代后评估项

**待用户自测**：serve + 硬刷 → B002「剪裁出西陵区范围内的商业+居住+公园广场用地」→ 应一次出 3 层完整结论（不再半成品）

### ✅ CB-11 glm组 加入 + 修复（commit 2c4483c + eb9ff5e）

**glm组（ZCode + GLM 5.2）加入 CB 双阵营**（第三方评估·claude组 开发主）：RULES/_cb-index/KNOWLEDGE/cb-journal 更新。

**glm组 CB-11 主通道验证**：主通道 A 方向正确·但发现 **G1/G2 union 链无限循环致命 bug**（buildLanduseCompletion + recover 模式 A·迭代 `_tcs` 同时 push → OOM）——**用户手动测试②「合并 3 类用地」直接命中**（2/6 步失败）。

**修复（eb9ff5e）**：
- **G1/G2**：union 链改固定上界 `_n`·不再无限循环
- **关 C 键对比**（main.js 注释·保留 setCompareMode + 时间轴按钮不动）
- **G3**：inline N/M 时序——扩展失败信息 finalStep 前注入 context
- **P1-4**：N/M 提示列失败图层名
- **P1-5（用户测试③·样式契约）**：clip 裁出情绪点继承源层 colorMode + 5 级极性图例 paint
- **G4**：buildLanduseCompletion 去「西陵」硬编码·从问句提取区名

**用户手动测试 4 用例**：① 剪裁 3 类用地成功（N/M 报 3/4·已修列图层名）；② 合并失败（=G1/G2·已修）；③ 情绪点样式不对（=族 D·已修样式继承）；④ 待自测

### ✅ CB-11 merge 多图层 concat 定稿修复（commit 9f84eac）

**问题**：用户测试②「合并 3 个独立裁剪图层」持续失败——系统无「合并多个独立图层」能力（merge 只支持单 boundary）。

**Codex + glm组 独立一致裁决方案 A**（后端 `merge(layers=[...])` concat·非 overlay union 空间并集）：
- 后端 `MergeRequest.layers` + concat 分支（CRS 统一 + `_source_layer` 标记）
- 契约 merge 加 layers（alias layer_list）+ when 两模式 + **one-of 校验**（boundary|layers 至少一个）
- 前端 tools.merge/toolbox _opMerge/stages 支持 layers
- buildLanduseCompletion/recover 模式 A/C 的 merge 意图改调后端 concat·**退役 overlay union 链**（消 G1/G2 + 字段爆炸·glm组 geopandas 实测 3→9→13 列）
- 测试：concat 保留 DLMC + one-of 400 + overlay 字段爆炸负向·**pytest 223 passed**

**待用户自测**：serve + 硬刷 → 「将剪裁出西陵区范围内的商业+居住+公园广场用地 合并成一个图层」→ 一次合并成 1 个图层含 3 要素·DLMC 分类保留

### ✅ 两天攻坚（完成·commit 898998b + 7735cb8 + 392ecc1）

**Day1 真实状态确认**（Playwright test_p0_repro）：
- **B002**：`_autoExpandOverlays` 修复代码在且通常工作（触发 3 overlay）·但 overlay 执行不稳 + runTemplatePath 先渲染半成品答案再后台跑 overlay（体验割裂·记待修）
- **B005**：双区+单用地时 autoExpand 不触发 + FC 不稳定 → 诚实降级「没跑通」
- **B003**：缺数据清单短路 → FC no_tool_calls → 诚实降级

**修复（全部浏览器验证 ✓）**：
- **B003**：`_quickIntent` 加数据清单意图 → general 短路·12.7s 列「原始数据 3 类」
- **B005**：`_deterministicRecover` 模式 D（单用地+双区）+ `_autoExpandOverlays` 扩单用地 + `_LANDUSE` 去「用地」泛词 → 9.7s 双区+overlay 一次成
- **B006**：router.py 抽 `build_fc_sys_prompt` + 恢复 31e2a00 极性纪律（0073990 静默删·补回）+ 内容守卫 → B006 实测 LLM 不再缩窄极性（全三极性）
- **P0-4**：FINAL_TEMPLATE 语言风格 7 并 3 + 人民城市条件注入 → test_final_prompt_stays_lean 转绿
- **P1-1**：`_gen_index` 读 frontmatter status 优先 + B010/B011 移 resolved
- **右半段**：删 executePlans 死代码 + ctx.plans/_plansToCapsules 标 CPD-RESERVED + P0-3 完成度确定性追加
- **B007**：`_checkGeomType` 类型 guard（clip 需点/overlay+extract 需面）
- **词表集中**：emc-patterns.js 收纳 LANDUSE_KW/DOMAIN_KW/POLARITY_KW/意图词

**验证**：pytest **220 passed** 零回归 + B0 飞轮 **36/45 无回归**（fail 9 = 既有 CPD/UI 问题）+ 定向 test_p0_repro 4 用例全过。**待续**：B3 全量 LLM 回归（后台曾卡死·改定向）+ B002 半成品 answer 重构 + B008/B006-B 样式继承 defer。

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
