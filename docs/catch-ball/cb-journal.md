# CB Journal（Catch-Ball 轨迹）

> 我方（claude组：Claude Code + DeepSeek/GLM 5.2）与第三方评价（Codex + glm组：ZCode + GLM 5.2）的多轮 catch-ball 对话轨迹。
> 按轮**倒序**（最新在顶·CB-NN 大→小·便于看最新进展；不覆写）。新轮次写在文件顶部。
> 每轮四节：① SCAN 摘要 ② 我方反评价 ③ 行动 ④ 状态/新发现。

---

## CB-16 · 2026-08-03（出口深化讨论 · 发起）

### ① SCAN 摘要

**本轮由 claude组 发起**（非第三方 SCAN）：基于最新版出口抽象层报告（含官方三类指标·软指标可信性缺口·出口卡片·案例深挖 v3·outlet_kb），发 Codex/glm 两组深读报告、聚焦 EMC"出口"、参与讨论。请求：[CB16-出口深化讨论](_handoff/CB16-出口深化讨论_2026-08-03.md)。

**核心内容**：
- 三大指标体系：国家十五五（10 项·统领）/ 住建部（4 维度 61 项·规建营·重点）/ 自然资源部（110 项·了解）
- 官方三类指标（建科〔2023〕75号）：可量化 ~55-65% / 可感知 ~15-20% / 可评价 ~15-25%·合计 30-45% 涉及市民感受
- 软指标可信性缺口 = 情绪地图要填的（全量评论流）
- 出口卡片体系（4×5 ↔ 体检指标 ↔ 更新任务·能/不能双栏）
- outlet_kb（7 契约 + 21 指标映射 + 5 案例·确定性组装）

**6 焦点**：A 结果范式 agent 架构（后端确定性组装 vs LLM）· B outlet_kb 接入（可感知 10 项逐项对应）· C 与 CB-15 数据认知协同（CB-15 先行）· D MVP 范围（S2 打穿）· E 承重与风险（D019 红线）· **F 出口驱动开发逻辑链（用户定·重点）**：基于出口反推定制分析方法/计划/执行工具/图例样式/出图文本范式——出口抽象层从"结果对接层"升级为"开发方法论"。

### ② 我方反评价（对 CB-16 两组 SCAN）

**两组独立一致·全部 agree**（verify-before-accept 通过）：

| 讨论点 | 判定 | 证据 |
|---|:---:|---|
| 出口方向正确（铁律 A·EMC 找市场）| **agree** | 立项成败关键·Codex+glm 独立一致 |
| outlet_kb 扎实（7 契约+21 指标+5 案例）| **agree** | field_mapping 引用真实 EMC 字段（`core/spatial_analysis.py` 聚合产物·非纸上谈兵）|
| MVP 只打穿 S2（更新需求分析）| **agree** | 一个场景全链路验证 > 三场景半成品·S2 meso 路径 zonal_stats 已稳定 |
| 不新增 LLM 阶段 | **agree** | 后端确定性组装 + 前端 markdown 渲染·不撞 D019·确定性比 LLM 编造更可信 |
| 出口驱动开发需验证闭环 | **agree** | 不能只是理念·要 6 步可执行流程（定义→反推→验证可产出→可组装→可渲染→可对接）·作为新功能评审清单非全量门禁 |

**关键独立洞察（两组互补）**：
- **Codex**：缺口 = 三层接线（装配 build_outlet_schema + 触发条件判定 + 前端渲染）非字段缺失——聚合产物已含 place_name/topic_top 等 7 要素输入·比报告"出向=0"更聚焦；**place_name 已存在·S2 可先行**（点侧众数·诚实标注·CB-15 是精度升级非解锁前置）；**出口驱动 CI 守卫**（validate_outlet_fields.py 防"分析了很多行业用不上"）；**修正"Codex 立场被预记"**（通俗版表述需改）
- **glm**：**出口驱动验证闭环 6 步**（可执行流程）+ **新功能评审清单非全量门禁**（基础设施不被阻塞）+ outlet_card 字段缺失降级（填"暂无数据"不编造）

### ③ 行动
- 深读两组 SCAN + verify-before-accept（聚合产物字段/outlet_kb 代码核验）
- 反评价落 plan（共识 + 独立洞察 + 收敛方案 Wave 0-3）
- **收敛方案**：Wave 0 = S2 打穿（build_outlet_schema + resolve_outlet_id + 条件触发 + 前端卡片）·Wave 1 = macro 出口（零 CB-15）·Wave 2 = CB-15 后 place_name 精确源·Wave 3 = 可感知计算器 + validate_outlet_fields CI
- 待用户确认 Codex 3 问（S2 演示数据/条件触发词表/卡片渲染形态）

### ③b 行动（Wave 0 实施 + 续）
- **Wave 0 核心已实施**（commit 9a98785·已 push）：`build_outlet_schema.py`（resolve_outlet_id + build_outlet_schema·确定性组装·不调 LLM·字段降级·尺度分派·诚实标注）+ 测试 13 passed + 端到端 S2 卡验证（接口标识/问题类型/需求强度/需求位置/需求类型/数据基础/对接任务/局限）
- **数据模拟开专题**（用户定·暂缓）：后续专门模拟大南门·二马路片区范围及周边数据展示 EMC 出口
- **Wave 0 剩余发起 CB**：条件触发词表（emc-patterns.js 镜像·方案 A）+ 前端卡片渲染（用既有 token）·请求落 `_handoff/CB16-Wave0剩余_2026-08-03.md`

### ③c 行动（Wave 0 三 bug 修复·CB 反评价）
- **两组 SCAN 发现 3 bug·全部核实 + 修复**（commit f84b3ae）：
  - ① qualifier 后缀解析（Codex）：`polarity_index 降序` 丢值 → 解析去尾部限定词
  - ② "更新"词过宽（Codex）："更新图层"误触发 → 排除 UI 语境
  - ③ 体检契约 domain（glm P0）：`urban_checkup` 不在 domain_lens 枚举 → 改 `urban_governance`（S6 可触发）
- 补 3 回归测试（qualifier/更新图层负测/体检契约命中）·10 passed·全量 pytest 242 passed
- 测试口径修正：13 → 实际 7（Codex 核实·已补至 10）

### ③d 行动（Wave 0 剩余实施预告·CB 机制）
- Wave 0 剩余两项实施方案已起草·发 CB 预告（`_handoff/CB16-Wave0剩余实施_2026-08-03.md`）：
  - ① 条件触发词表镜像 emc-patterns.js（OUTLET_TRIGGER_KW·单一权威源在后端·同步守卫 validate_outlet_trigger_sync.py·仅 UI 提示不改控制流）
  - ② 前端 outlet-card 渲染（仿 .cpd-guide-card·既有 token·纯模板函数·{{show:}} 复用 renderAnswer）
- 按机制：等两组预检 SCAN 后实施

### ③e 行动（Wave 0 完整链路实施·按两组预检）
- **两组预检通过**（Codex agree + 关键缺口"无前端接线"·glm agree + 排除表镜像建议）·反评价采纳全部
- **Wave 0 完整链路实施**（commit 38d3a0c·已 push）：
  - `/aiqa/outlet_card` 端点（接收 diagnose+result+question→build_outlet_schema）
  - harness result 态后条件调（_maybeBuildOutletCard·触发词+UI 语境排除·产物收集·失败静默）
  - panel renderOutletCard 纯模板渲染（仿 cpd-guide-card·既有 token·7 要素·缺失灰·引用块·{{show:}} 复用）
  - emc-patterns.js OUTLET_TRIGGER_KW + OUTLET_UI_EXCLUDE_KW（镜像含排除表·Codex/glm 建议）
  - validate_outlet_trigger_sync.py 同步守卫（双份校验·2 passed）
- **端到端验证**：/outlet_card → 需求分析卡（停车难/-0.32/夷陵广场·诚实标注）·JS import OK·pytest 242

### ③f 行动（Wave 0 实施后检查发起）
- Wave 0 完整链路已实施（38d3a0c+bd3ccce）·发实施后检查 CB 请求（`_handoff/CB16-Wave0完成检查_2026-08-04.md`）：5 环节核验（端点/接线/渲染/词表/守卫）+ 端到端验证（复现命令 + 浏览器出卡）
- 待两组检查 SCAN → 反评价

### ③g 行动（大南门数据专题实施预告发起）
- **交接卡【下一步】核心待续项推进**：大南门·二马路数据接入 EMC 出口链路（数据接入·非新契约/非新 LLM 阶段）
- 探索发现 3 缺口：① ermawu CSV 无 lon/lat（坐标只在 geojson）② ermawu 三层未注册 `geo_registry._POINT_LAYERS`（问答无法加载）③ 大南门边界不在 range presets manifest（/geo/catalog 不可见）
- 发实施前预告（`_handoff/CB16-大南门数据专题实施_2026-08-04.md`）：CSV 补坐标列（一次性 backfill·不动生成器）+ 注册点层（level='L3L4'）+ 边界登记 + 回归测试 + 端到端出卡
- **用户定**：时间轴 manifest（_time_manifest.json）与需求分析是两件事·后置（本次不做）
- 待两组预检 SCAN → 反评价 → 实施

### ③h 行动（大南门数据专题实施 · 两组预检通过后落地）
- **两组预检通过**（Codex「通过 + 1 必补项」· claude组「全过 + 4 追加建议」）·反评价采纳全部：
  - **Codex 必补项**：边界登记只改 manifest 不够——`list_presets` 用 `os.path.join(_PRESETS_DIR, file)` 判 available·须**复制文件进 `DATA/boundaries/presets/`**（已落实·复制不移动）
  - **claude组 建议**：backfill 按 id_e 匹配 + 断言（实测 T1/T2/T3 序完全一致·700/800/900）+ 保 utf-8-sig BOM + 坐标列加末尾 + 生成器修复 TODO 注释（已全落实）
- **实施完成**（本 commit·验证全过）：
  - `SCRIPT/backfill_ermawu_coords.py`：一次性补丁·T1/T2/T3 共 2400 行补 lon/lat（id_e 断言·幂等·备份·保 BOM·生成器 TODO 注释）
  - `core/geo_registry.py`：`_POINT_LAYERS` 末尾追加 `ermawu_l3l4_t{1,2,3}`（level='L3L4'·富归因列原样保留）
  - `DATA/boundaries/presets/manifest.json`：「城市更新单元」组加 `damanmen_area` + **复制 geojson 进 presets/**（name 属性"绘制多边形"→片区名·P1 优化顺手做）
  - `tests/test_geo_registry.py` 新建（4 例：注册/900 行/坐标域/富归因列/load_preset available）+ `tests/test_outlet_schema.py` +1（真实 ermawu 聚合产物出卡）
- **端到端验证**（真实端点·memory「verify-real-endpoint」）：/geo/catalog 暴露 3 ermawu 层 + damanmen 边界可用 → /geo/zonal_stats(ermawu_l3l4_t3 × damanmen_area) 返回 578 点·polarity_index 0.73·domain_top=urban_operation·文化 → /aiqa/outlet_card 命中 **renewal_demand 需求分析卡**（接口=片区策划·需求强度 0.73·问题类型=停车难·数据基础 N=578·诚实标注 place_name 粗略）
- **pytest 249 passed（+7 新测·零回归）**
- **观察**：真实 zonal 行无 place_name 字段（需求位置缺失降级·诚实不编造·符合设计·CB-15 后 place_name 精确源升级）；level='L3L4' 对 density 工具枚举/R5 胶囊防线影响为知晓点（本轮不走 density·非阻塞·SCAN 记一笔）

### ③i 行动（R7 结论截断修复 · 用户实测发现 + 用户定阈值策略）
- **用户浏览器实测**「大南门·二马路片区更新需求分析」：结论基本可用·但结尾出现「**4.**\n…（结论已截断·详见上方图层）」——问"未完成是什么原因"
- **根因定案**：R7 截断防线（harness.js applyQualityDefense）`final.length > 800 → slice(0,800)` 字符级硬切——① 阈值 800 过低（用户定：多要素结论超 800 正常·实测 audit 结论 p95≈1000）② 切点不感知 markdown 结构·恰切在「**4.**」标题后 → 空标题 ③ 连带 bug：R2 `{{show:}}` 图层按钮在 R7 前追加·长结论时被切掉（图层主出口失效）④ 文案固定「详见上方图层」·无图层时误导
- **修复**（纯 harness.js·不碰承重）：
  - R7 阈值 **800 → 1500**（用户定·只拦真失控长文·p95≈1000 留余量）
  - **切点结构回切**：`lastIndexOf('。'/'；'/'\n'/'.', 1500)` 切到自然断句边界·下限 750 兜底·不再出现「**4.**」空标题
  - **R2 移 R7 后**：长结论时图层按钮不被切（图层主出口防失效）
  - **文案场景化**：有图层「详见上方图层与数据」/ 无图层「结论较长已精简·详见上方分析」
- **验证**：括号配对完整（+7/+7 成对·注释差异为既有）+ Playwright 页面加载零 console 错误（harness.js import 链语法 OK）+ **pytest 249 passed 零回归**
- **待用户 F5 复验**：重问「大南门·二马路片区更新需求分析」→ 应不再出现「**4.**」空标题

### ③j 行动（R7 截断修复实施后检查发起）
- R7 修复已完成（0aff59e + 49e4122）·发实施后检查 CB 请求（`_handoff/CB16-R7截断修复检查_2026-08-04.md`）：4 环节核验（阈值 1500 / 结构回切 / R2 移后 / 文案场景化）+ 端到端验证（用户场景 1100 字完整通过 + >1500 字截断在句末 + 产图层按钮保留）
- **预检 5 问**（给两组）：阈值合理性（含按结论类型动态调之问）·断句符覆盖（！？遗漏？）·R2 移后副作用·文案准确性·**截断后 {{show:}} 按钮是否真保留 + 残句边界**
- 待两组检查 SCAN → 反评价

### ③k 行动（R7 检查反评价 + 补修 · 两组 SCAN 处理）
- **两组检查 SCAN 到**（`CB16-R7截断修复-检查_Codex-GPT5` + `CB16-R7截断修复-claude组`）·反评价：
  - **agree（两组一致）**：阈值 1500 合理（用户实测 ~1100 字完整通过·不建议动态化）·R2 后移无副作用（realLayers 顶部算·R10/R11/R5/R6/R8 不依赖 {{show:}}）·文案场景化对路
  - **claude组 P0 发现（采纳）**：`lastIndexOf('.')` 会把 markdown 列表标题「**4.**」句点当切点·结论第 N 点落 1500 边界时**精确复现原 bug**（场景 4 实测·根因 = `.` 误切·我初版修复没堵住）→ 方案 A 去 `.` 切句符
  - **Codex 低优（采纳）**：断句符补 `！？` + 悬空列表编号行剥除（`/\n\d+\.\s*$/` 硬化）
  - **claude组 文案微调（采纳）**：「结论较长已精简」→「结论较长·已截断保留要点」（精简暗示主动提炼·实为硬切）
  - **claude组 补测试（采纳）**：新增 `tests/browser/test_r7_truncation.py`（e2e-seam 暴露的 applyQualityDefense 直测真实 JS 逻辑·非 Python 复刻）
- **补修完成**（harness.js R7 段）：去 `.` 切句符·加 `！？`·悬空编号行剥除·文案微调
- **验证**：新测试 3 场景全过（多要素完整 / 失控截断无空标题 / {{show:}} 完整）+ 括号配对 +2/+2 + pytest 249 passed 零回归
- **待用户 F5 复验**（补修后重问大南门需求分析）

### ③l 行动（Wave 1 macro 出口实施 · 两组预检反评价 + 落地）
- **两组预检 SCAN 到**（`CB16-Wave1-macro出口-预检_Codex-GPT5` + `CB16-Wave1-macro出口-claude组`）·反评价：
  - **两组一致**：草案可行·三层断裂修复路径成立·无 P0
  - **Codex P1（采纳）**：checkup_dimension 四维度×单尺度语义错位（macro 值入 micro/meso 槽）→ 槽位 `[scale=xxx]` 限定（仅填匹配 diagnose.scale·其余"需对应尺度分析"）
  - **claude组 P1×3（采纳）**：① `_extract_emc_value` 升级为**后端统一收 rows/features**（单入口规整·防前后端漂移）③ DOMAIN_KW 补「**城市体检**」长词（防健康体检/体检中心误触）⑤ `data_base` 加 rows 分支（N=单元数·note 区分·total_points 总评论数）
  - **P2（采纳）**：`rows.length>0` 守卫·`+` 只取首字段（place_name 留 Wave 2）·stages.js 无需改（已 import DOMAIN_KW 自动生效）
  - **rows 可达性（claude组 风险·确认属实）**：`_maybeBuildOutletCard` 在 finalStep 后调用·工具局部 r 已出作用域 → 模块级 `_lastToolRows` 缓存（3 处工具调用点捕获）
- **落地 7 处**：`build_outlet_schema.py`（rows 分支 + scale 限定 + data_base rows）·`harness.js`（_lastToolRows 缓存×3 + 产物收集优先 rows + 门放宽 + 测试钩子）·`emc-patterns.js`（DOMAIN_KW 补城市体检）·`urban_checkup_outlets.py`（四维度真实字段 + [scale]）·`e2e-seam.js`（setOutletRows/buildOutletCardForTest）·单测 4 新增 + `test_outlet_macro.py` E2E
- **验证**：pytest 253 passed（+4 新增·零回归）·括号配对平衡×3 · E2E 两场景全过（rows 门放宽出卡 + 字段非空 + scale 限定·outlet_card 端点 200）
- **待用户浏览器复验**（macro 问句真出卡）

### ③m 行动（Wave 1 实施后检查发起·先验后推）
- 用户定「进 cb·先验后推」→ 发起 Wave 1 实施后检查（`_handoff/CB16-Wave1完成检查_2026-08-04.md`）：5 环节核验（① _extract_emc_value 统一收 ② _lastToolRows 缓存×3 + 门放宽 ③ DOMAIN_KW 城市体检 ④ checkup_dimension scale 限定 ⑤ data_base rows + 测试）+ 端到端验证（单测 15+6+2 + E2E 两场景 + 浏览器）
- **预检 7 问**（给两组）：统一收正确性（有无破坏 features 用例）·缓存×3 覆盖全部工具路径？·门放宽副作用？·scale 限定正确性？·data_base 语义？·城市体检长词触发正确性？·测试覆盖够？
- **未推**（97cf232 + 9ea1290·先验后推：两组通过后用户 push）
- 待两组检查 SCAN → 反评价

### ③n 行动（Wave 1 检查反评价 + 补修 · 两组 SCAN 处理）
- **两组检查 SCAN 到**（`CB16-Wave1完成-检查_Codex-GPT5` + `CB16-Wave1完成-glm组`）·反评价：
  - **两组一致**：Wave 1 主体通过（5 环节正确·单测 23 passed·单步 macro 端到端通路确认）
  - **glm组 P1（采纳）**：`runAllToolCalls` rows 处理缺陷——:1868-1869 `else` 挂在 rows 缓存 if 上（rows 型无 layerId → 成功误判失败）+ :1875 守护漏 hasRows → 多步 macro 链降级 → 改三独立 if + 守护加 hasRows + failedSteps 排除 rows 成功步
  - **Codex P1（采纳）**：`_lastToolRows` 跨轮不重置 → orchestrate 入口重置 `_lastToolRows = null`（防 turn1 zonal rows 附 turn2 出口卡）
  - **Codex P2（采纳）**：while-loop 兜底路径（:1249）补 rows 捕获（对齐其他 3 路径）
  - **Codex P2（采纳）**：`test_wave1_empty_rows_no_card` 名实不符 → 改名 `test_wave1_empty_rows_degrades` + docstring 说明前后端分工
- **验证**：括号平衡·pytest 253 passed 零回归·E2E 两场景全过
- **待用户 push**（先验后推·两组通过后推）

### ③o 行动（Wave 2 / CB-15 实施预检发起）
- 用户定「进入 Wave 2 / CB-15·保持 CB 机制」→ 读 CB-15 讨论稿（五点共识 + glm 致命发现已核实）+ 现状探索（place_name 只读标注·place_layer 已读 3220 POI·reverse_geocode 已接）→ 发起 Wave 2 预检（`_handoff/CB16-Wave2-CB15预检_2026-08-04.md`）
- **草案 5 处**：① place_name 双源融合（sjoin POI 优先·fallback 标注·保旧 sim 兼容）② 聚合输出 poi_names（top-N 清单）③ `/grid/pois` 端点（选中格按需）④ 3220 接入（复用 place_layer）⑤ 承重零触碰（place_layer/geocode 只增不改·新工具契约三处同步）
- **预检 7 问**（给两组）：双源融合方案 + sjoin 性能 / poi_names 输出 top-N 防配额爆 / grid/pois 端点结构 + LLM 用法 / 3220 接入够不够 / place_name 改动回归风险 + 旧 sim 兼容 / 测试方案 / 边界（只做 P0·P1/P2 后置）
- **待两组 SCAN** → 反评价 → 实施

### ③p 行动（Wave 2 / CB-15 P0 实施 · 两组预检反评价）
- **两组预检 SCAN 到**（`CB16-Wave2-CB15-预检_Codex-GPT5` + `CB16-Wave2-CB15-glm组`）·反评价：
  - **两组一致 P0（采纳·实锤）**：place_layer **未读 3220**（读的是 SCRIPT/poi_data/amap_poi_wgs84.json 1270·非 DATA/POI/3220）+ 3220 字段错配（坐标在 geometry·无 lng/lat/baidu/domain）→ 加 `_read_pois_geojson` 适配层 + _load 合并
  - **P1（采纳）**：place_name 语义分层（polygon 保留边界名·grid POI 优先·取最近质心 POI）+ place_name_source 字段（可追溯）+ 改前跑现有测试 + sjoin 列名冲突修复（poi/poly 双 name → poly_ 前缀）
  - **P2（采纳）**：poi_names 逗号 top-5 + 等N处·poi_count·3220 vs 1270 去重（name+coord 容差·保先序）
- **落地**：`place_layer.py`（_read_pois_geojson + _load 合并 + _dedup_pois）·`spatial_analysis.py`（_attach_poi_attrs + place_name_source + 两处接入）·`api/geo_routes.py`（/grid/pois 端点·cell_id/质心双收）·测试 5 新增 + test_geocode limit 适配（3220 扩容 1277→4310·200 上限触顶）
- **验证**：3220 接入 all_pois=4310（去重 187）·reverse 覆盖扩大 · /grid/pois 端点 200（centroid count=32 CBD·cell_id 确定性一致）· pytest 258 passed 零回归
- **待两组实施后检查**（用户定 CB 机制·先验后推）

### ③q 行动（Wave 2 实施后检查发起·先验后推）
- 用户定「实施后检查（两组核验）」→ 发起 Wave 2 实施后检查（`_handoff/CB16-Wave2完成检查_2026-08-04.md`）：4 环节核验（① _read_pois_geojson 适配层 + _dedup_pois ② _attach_poi_attrs 双模式 + sjoin 列名冲突修复 + place_name_source ③ /grid/pois 端点契约 ④ 测试）+ 端到端验证（3220 count=4310 + grid_pois 200 count=32 + 聚合 poi_names）
- **预检 7 问**（给两组）：适配层字段映射遗漏？·去重连锁店不误删？·双模式/sjoin 冲突修复完整？·place_name_source 兜底链？·端点契约 + LLM 用法？·测试边界（空 POI 格/grid 覆盖/去重极端）？·承重零触碰？
- **未推**（623e293·先验后推：两组通过后 push）
- 待两组检查 SCAN → 反评价

### ③r 行动（Wave 2 检查反评价 + 补修 · 两组 SCAN 处理）
- **两组检查 SCAN 到**（`CB16-Wave2完成-检查_Codex-GPT5` + `CB16-Wave2完成-glm组`）·反评价：
  - **两组一致**：Wave 2 P0 主体通过（4 环节核心正确·3220 接入 4310·双模式 place_name·source 链完整·端点确定性·53 单测全过）
  - **glm组 P1（采纳·两组实锤）**：`_dedup_pois` 同名异址连锁店误删——`_seen` 先锁 name·第二条同名直接判重·坐标容差成死代码 → 去 `_seen`·改 name+坐标容差联合判定（O(n²)·n=4310·_load 一次）
  - **Codex P2（采纳）**：create_square_grid 未输出 cell_id 列 → 补确定性 cell_id（grid_{size}_{row}_{col}·4546）
  - **glm组 P2（采纳）**：补测试边界（去重连锁店 / grid place_name_source=poi_sjoin / cell_id 列）
- **验证**：all_pois=4342（修复后恢复 32 条误删连锁店·预期）·pytest 261 passed 零回归（+3 新增）
- **待用户 push**（先验后推·两组已验·通过）

### ③s 行动（CB-15 P1 预检发起）
- 用户定「出 P1 计划·走 CB 流程·执行」→ 探索确认四子项现状与缺口（buffer 中文 POI 根因 resolve_boundary 只认 preset/GeoJSON·评论↔POI 逐点 O(n·4310) 需 sjoin_nearest·search/reverse 端点已有但无 AI 工具·field_mapping 只读 place_name + 陈旧文案）→ 定稿 P1 计划 + 发起预检（`_handoff/CB16-CB15-P1预检_2026-08-04.md`）
- **草案 4 子项**：A buffer 中文 POI（后端 fallback search_place）·B 评论↔POI 批量 sjoin_nearest · C lookup_place AI 工具（契约三处同步 + track ID）·D 归因落点模板（place_name+poi_names+issue_label 合成 + 修陈旧文案）
- **预检 7 问**（给两组）：A 后端 fallback vs 前端 search 方案 + 边界·B sjoin_nearest 性能 + 落列污染·C 纯前端 vs 契约条目 + 触发词·D 落点模板破坏既有用例？·范围边界 P1 必要性·测试方案·承重零触碰
- **待两组 SCAN** → 反评价 → 实施

### ③t 行动（CB-15 P1 实施 · 两组预检反评价）
- **两组预检 SCAN 到**（`CB16-CB15-P1-预检_Codex-GPT5` + `CB16-CB15-P1-glm组`）·反评价：
  - **两组一致**：P1 四子项方向全部对路·无 P0 阻塞
  - **A 采纳（两组）**：buffer 后端 fallback search_place（AI/前端共用一处）·边界（preset 优先·top-1·无命中诚实 400·WGS84·只对 str center）
  - **B 后置（glm组 P2 建议·采纳）**：评论↔POI 批量 sjoin_nearest 后置 Wave 3（非问答阻塞·grid_pois + poi_names 已够）
  - **C 采纳（两组）**：lookup_place 契约后端 + 前端执行混合·触发词**避开"周边"**（与 buffer 冲突·用"在哪/叫什么/附近/坐标"）·契约三处同步 + track ID
  - **D 采纳（两组）**：落点组合模板（扩 `+` 多字段合成）+ 暴露 poi_names/place_name_source + 修 :179 陈旧文案
- **落地**：`geo_routes.py`（buffer fallback）·`build_outlet_schema.py`（+ 合成 + 文案修）·`tool_contracts.py` + `paradigm.py` + `tools.js` + `stages.js` + `emc-patterns.js` + `candidate_selector.py`（lookup_place 契约三处同步 + track ID F_013）
- **验证**：pytest 266 passed（+8 新增·buffer 中文名 200 / 无命中 400 mock / lookup_place 契约 / 落点合成 / poi 字段）·括号平衡×3
- **已知**：test_validate_skill_params density.when drift 为**既有**（HEAD 版同 fail·非本次引入·backlog）
- **待两组实施后检查**（用户定 CB 机制·先验后推）

### ③u 行动（CB-15 P1 实施后检查发起·先验后推）
- 用户定「发起 P1 实施后检查」→ 发起检查请求（`_handoff/CB16-CB15-P1完成检查_2026-08-04.md`）：4 环节核验（① buffer fallback ② + 合成 + 文案 ③ lookup_place 契约三处同步 ④ 测试）+ 端到端验证（buffer 中文名 200 / lookup_place 契约 / 浏览器奥体中心 + 滨江公园）
- **预检 7 问**（给两组）：buffer fallback 边界/preset 优先·+ 合成破坏既有用例？·lookup_place 契约同步完整 + 触发词避周边有效？·:179 文案正确？·测试边界（多命中 top-1/坐标直查）？·承重零触碰？·density.when drift 既有不阻塞？
- **未推**（61567d6·先验后推：两组通过后 push）
- 待两组检查 SCAN → 反评价

### ③v 行动（CB-15 P1 检查反评价 + P2 补修 · 两组 SCAN 处理）
- **两组检查 SCAN 到**（`CB16-CB15-P1完成-检查_Codex-GPT5` + `CB16-CB15-P1完成-glm组`）·反评价：
  - **两组一致**：CB-15 P1 通过·可推（A buffer 中文 fallback + C lookup_place 契约 + D 组合合成/:179 文案全正确·单测 34 passed·buffer 中文名 200/400 实测·density.when drift 既有性独立回测确认非本次引入）
  - **P2 全采纳**（低成本·随 P1 修顺手清理）：① lookup_place triggers 去「附近」（与 buffer 重叠·"附近/周边"留 buffer）② 组合合成 source 只列非空 parts ③ docstring :13 旧文案修 ④ required_slots=['q']→[] 对齐 SKILL_DEFS（lng/lat 直查合法）
  - **backlog（Codex 扩）**：validate_skill_params drift 是 7 工具（density/buffer/clip/overlay/zonal_stats/extract_feature/merge）paradigm when 同步·非仅 density
- **验证**：pytest 266 passed 零回归·测试补断言（lookup 触发词不含附近）
- **待用户 push**（先验后推·两组已验·通过）

### ③w 行动（Wave 3 预检发起）
- 用户定「继续 Wave 3·进 cb」→ 探索确认现状（可感知 10 项指标库完整·build_outlet_schema 只返单契约·validate_outlet_trigger_sync AST 解析模式可参考·B 评论↔POI 后置待做）→ 定稿 Wave 3 计划 + 发起预检（`_handoff/CB16-Wave3预检_2026-08-04.md`）
- **草案 4 子项**：① B 评论↔POI 批量（attach_nearest_poi sjoin_nearest·新列禁覆盖 area_seed）② 可感知 10 项计算器（compute_perceptible_metrics·emc_field 表达式→指标值）③ validate_outlet_fields CI（AST 解析消费字段→死字段/缺消费）④ 多卡支持（多契约命中→cards 列表）
- **预检 7 问**（给两组）：B sjoin 方案/性能/新列策略·可感知计算器表达式解析/计算语义/落点·validate CI 判定合理/放 tests 还是运行时·多卡兼容既有？·范围边界·测试方案·承重零触碰
- **待两组 SCAN** → 反评价 → 实施

### ③x 行动（Wave 3 实施 · 两组预检反评价）
- **两组预检 SCAN 到**（`CB16-Wave3-预检_Codex-GPT5` + `CB16-Wave3-glm组`）·反评价：
  - **两组一致**：草案方向可行·无 P0
  - **glm组 P1（采纳）**：可感知计算器分两步——2a 极性类（A 类 2 + C 类简单 2·P1 立即做）+ 2b 条件等式（B 类 6 项·需表达式解析器·P2）·多卡同 domain 只出最高分一张（防冗余）
  - **Codex P1（采纳）**：emc_field 表达式解析器 compute + validate 共享（validate_outlet_fields 用正则收 ASCII 字段·跳过中文说明段）·多卡兼容迁移（cards + card=cards[0]）
  - **两组一致（采纳）**：B 评论↔POI 继续后置（非出口深化核心·grid_pois + poi_names 已够）
- **落地**：`build_outlet_schema.py`（resolve_outlet_ids 多契约·同 domain 去重 + build_outlet_schema 返 cards + build_outlet_schema_single 兼容 + compute_perceptible_metrics 2a）·`api/aiqa_routes.py`（/outlet_card 返 {cards, card}）·`harness.js` + `panel.js`（多卡渲染·兼容单卡）·`tests/validate_outlet_fields.py`（死字段 fail/缺消费 warn）
- **验证**：pytest 269 passed（+3 新增）·端点多卡（renewal_demand + checkup_satisfaction 2 卡·card[0] 兼容·perceptible_metrics 有值）
- **待两组实施后检查**（用户定 CB 机制·先验后推）

### ③y 行动（Wave 3 实施后检查发起·先验后推）
- 用户定「实施后检查（两组核验）」→ 发起检查请求（`_handoff/CB16-Wave3完成检查_2026-08-04.md`）：5 环节核验（① resolve_outlet_ids 多契约 + 计算器 ② /outlet_card {cards,card} ③ 前端多卡渲染 ④ validate_outlet_fields CI ⑤ 测试）+ 端到端验证（单测 + 端点多卡）
- **预检 7 问**（给两组）：resolve_outlet_ids 多契约/同 domain 去重/兼容·多卡破坏既有单卡？·计算器 2a 正确 + 2b 边界·validate CI 误报？·测试边界（同 domain 多契约/关键词未命中/空 result）·承重零触碰·density.when drift 既有不阻塞？
- **未推**（1daffc6·先验后推：两组通过后 push）
- 待两组检查 SCAN → 反评价

### ③z 行动（Wave 3 余留 2b + P2 预检发起·先讨论再实施）
- 家庭环境续作·用户定「plan 也进 CB」→ 对齐 ③w 模板发起两组预检（`_handoff/CB16-Wave3预检2b-P2_2026-08-04.md`）
- **草案 2 子项**：① 可感知计算器 **2b**（B 类条件等式 6 项·`_parse_emc_expr` 拆 `+` + 条件/值识别·element_top 缺失→暂无数据/不匹配→跳过/匹配→取值+关键词标注·复用 `_extract_emc_value`·2a 不动）② checkup_satisfaction **P2**（field_mapping prose→真实字段·`'满意度（4 尺度）':'polarity_index'`·`'8 领域情绪值':'domain_top/element_top + polarity_index'`·均 ∈ _EMC_FIELDS 白名单·对齐 checkup_dimension）
- **预检 7 问**（给两组）：2b 表达式解析/计算语义·P2 契约语义与 checkup_dimension 信息重复？·CI 提取兼容·范围边界·测试方案·承重零触碰
- **待两组补充预检 SCAN → 反评价 → 实施**

### ③z2 反评价（glm + Codex 补充预检 SCAN·两组均通过·无 P0）
- **glm组**（`scan/CB16-Wave3补充预检_glm组_2026-08-04.md`）：B 类**恰好 7 项**（claude组 写 6-7）·`_parse_emc_expr` 需处理**多值条件 `/`**（`element_top=设施/环境` 拆列表·非取首·与 `_build_card` 取首语义不同·两处注释明确）·2b source 对齐 2a 格式
- **Codex**（`scan/CB16-Wave3补充预检_Codex-GPT5_2026-08-04.md`）·**P1×3 全 agree（verify 通过）**：
  ① **生态宜居 2a/2b 边界**：2a `if 'polarity_index' in expr` 把生态宜居（`element_top=环境 + polarity_index`）当极性类·忽略条件 → 采纳「移 2b 做条件评估」（条件型按条件判定·更合语义）
  ② **关键词未命中→跳过**：草案只定义命中+标注·未定义未命中 → 采纳「条件匹配 + value_field 有值但关键词未命中→跳过」（防 `停车` 标到 `养老托育` 名下）
  ③ **`8 领域情绪值` `/` 字段序**：`_build_card` `split('/')[0]` 取首确认（实测 `urban_governance、0.15` 英文枚举）→ 采纳「`element_top/domain_top` 中文要素优先」+ 注释两处 `/` 语义差异
- **Codex P2 采纳**：panel.js 不渲染 perceptible_metrics（2a 已交付 UI 不可见·并入本批补渲染）·source 标注统一（并入）
- **Codex P2 暂缓**：renewal 卡体检指标 domain 门控（既有行为非本次引入·2b 放大但非阻塞·backlog）
- **登记**：`_handoff/CB16-Wave3预检2b-P2_2026-08-04.md` 第一步改「读本地文件·无需 git pull/push」·KNOWLEDGE §7（评估方不 git）
- 待实施（2b + P2 + panel 渲染）→ 实施后检查 → 通过后 push

### ③z3 行动（Wave 3 余留 2b + P2 实施 + 实施后检查发起·先验后推）
- **实施**（据 ③z2 反评价·Codex P1×3 + glm 注意项×2 全采纳）：
  - `build_outlet_schema.py`：`_parse_emc_expr`（拆 `+` + 条件/值识别·**多值 `/` 拆列表**·含 polarity→2a）+ `compute_perceptible_metrics` 分 2a/2b（生态宜居**明示留 2a**·2b 仅可感知·条件不匹配→跳过·关键词未命中→跳过·source 对齐）+ `_kw_hit` 抽共用
  - `urban_checkup_outlets.py`：checkup_satisfaction field_mapping prose→真实字段（`'满意度（4 尺度）':'polarity_index'`·`'8 领域情绪值':'element_top/domain_top + polarity_index'` element_top 优先·`'不满意项定位'` 不动）
  - `panel.js` renderOutletCard：新增 perceptible_metrics 渲染（可感知体检指标小节）
  - `tests/test_outlet_schema.py` +7（2b 命中/不匹配/缺失/多值/关键词未命中→跳过/生态宜居 2a·P2 满意度字段）
- **验证**：pytest 29 + **274 passed 零回归**·panel.js ESM 语法 OK·**真端点**（POST /aiqa/outlet_card）：cards 2 张 + checkup_satisfaction 字段出真实值（满意度←polarity_index·8领域←element_top·不满意定位←issue_label+place_name）+ 2b B 类「公园绿地步行可达性感知」条件命中出值（source 标条件+命中）
- **检查发起**：`_handoff/CB16-Wave3完成检查2b-P2_2026-08-04.md`（7 问·含已知 renewal 卡无条件调用·暂缓 backlog）
- **未推**（先验后推：两组检查通过后 push）·待两组检查 SCAN → 反评价

### ③z3b 反评价（glm + Codex 实施后检查 SCAN·两组均通过·可推）
- **Codex**（`scan/CB16-Wave3完成2b-P2_Codex-GPT5_2026-08-04.md`）：**通过·无 P0/P1·可推**·2a 实为 5 项（A2+C2+生态宜居·renewal 模块不在 METRIC_MAPPINGS·修正声明）
- **glm组**（`scan/CB16-Wave3完成2b-P2_glm组_2026-08-04.md`）：**通过·全部正确落地**·_parse_emc_expr 多值 `/` 拆列表✅·2a/2b 分支✅·P2 防空卡✅·端到端 2 场景✅·274 passed✅
- **两组一致观察**：`.outlet-metrics` CSS 缺失（Codex P2-1 / glm P3）→ **采纳补 CSS**（本次引入·真实视觉缺口）
- **Codex P2-3 采纳**：补 value_field 缺失→暂无数据 + `_parse_emc_expr` 纯函数边界测试（空串/无+/keywords 空/无条件）
- **Codex P2-2 不采纳**：条件匹配 substring→`==`（可选优化·受控词表低风险·保持现状）
- **已知 backlog 确认**：renewal 卡带 perceptible_metrics（`_build_card:230` 无条件·domain 门控暂缓）
- **验证**：pytest 31 + **276 passed 零回归**（+2 边界测试）·两组通过 → **可 push**

### ④ 状态
`CB-16 全闭环（Wave 0-3 + ③z 余留 2b/P2）· 已推 0a0d103 + 7d8a258` —— Wave 0-3 出口抽象层 + ③z 余留全部闭环。进入新阶段：**全局优化 + 发版快照 + 时间轴重规划（③w2 预检发起）**。

### ③w2 行动（全局优化 + 发版快照 + 时间轴重规划 预检发起·先讨论再实施）
- 用户定「①更新过时文件 + 归档陈旧 + 全局优化 ②发版候选评估 + 收尾技术债」→ 出 plan 进 CB（`_handoff/CB16-GlobalOptimize预检_2026-08-04.md`）
- **三路探索完成**：过时文档（CLAUDE.md 5 行过时·emc-fix-progress 自相矛盾·todo 周归档缺 07-27~08-02·spec/arch Streamlit 死段·decisions 停 ADR-016·记忆 GC）· 发版评估（B3 23/26·PRM 硬门槛·无成文检查清单）· 时间轴 manifest 404（根因=数据 R100 迁移到 performance·手写 manifest 未落新位置·**数据没丢只缺描述符**）
- **用户决策**：发版评估**先做全局优化+快照**（非冲达标）·时间轴**重新规划·更优解**（同源派生 manifest 治本·候选 1 geo_registry 同源 + fallback API·候选 2 落手写 manifest 快速解封）
- **草案 4 子项**：①全局优化（CLAUDE.md 5 行 + 周归档 + emc-fix-progress + Streamlit 死段 + decisions 补档 + 记忆 GC）②发版快照（B3 现状 23/26 + link_checkup + pytest·不修 PRM）③时间轴同源派生 manifest（治本·时间轴与问答共享注册表）④backlog 收尾（7 工具 drift + renewal domain 门控 + CPD-L03 断言）
- **预检 7 问**（给两组）：全局优化范围合理？发版快照对？时间轴同源派生思路/数据红线？backlog 优先级？测试方案？承重零触碰？范围边界？
- 待两组 SCAN → 反评价 → 实施

### ③w2b 反评价（glm + Codex 预检 SCAN·两组通过·用户拍板）
- **Codex**（`scan/CB16-GlobalOptimize预检_Codex-GPT5_2026-08-04.md`）：草案可行·无 P0。**P1 修正×3**：① L4 标 🔄 非 ✅（出口卡 limitation「L4 深度归因待接入」同步·守「预留当已实现→偏高 8 折」标尺）② global-time-axis/batch4 **已实现**（time-bar/time-source/timeline 三件套 + mapB 在仓）·标「已实现+待修/待polish」非「设计稿」③ CPD-L03 断言落点定位实际执行处（test-board/test_cpd_predicates·非 test-cases.js·'changyi' 已零引用）。**P1 建议×2**：validate 同步含 extract_feature/merge 全字段（params/yields/contributes）·时间轴候选 1 直接做（含 L1/L2 模板差异特判）。**P2**：Streamlit 死段保留退役声明+MOD_APP 引用·ADR 轻量补录·快照产物存档。
- **glm组**（`scan/CB16-GlobalOptimize预检_glm组_2026-08-04.md`）：通过·**validate_skill_params 当前 FAIL**（1 failed·7 工具 when/params/yields/contributes contracts vs paradigm drift·P1 优先·CB-12/16 改 contracts 未同步 paradigm）。时间轴候选 1 建议 **glob 扫文件非模板拼接**（L1 T1 双扩展名 `_csv.csv.geojson`·L2 `_L2_` infix·无法统一模板）。候选 2 不碰数据红线（描述符 JSON·非数据文件）。push 冲突需用户拍板。发版快照含 `trace_query --stats`。
- **用户拍板**：① 时间轴**后置专题**（不成熟·开专题再议）→ 子项 3 从本次**剥离**·不实施同源派生/解封·但 global-time-axis/batch4 记忆标注修正照做 ② push 冲突权威源 = **commit+push 组合**（push-not-redline）③ 发版 = 先全局优化+快照（非冲达标）
- **plan 重写**（时间轴剥离·3 子项）：①全局优化 ②发版快照 ③backlog 收尾（validate 全字段 + renewal 门控 + CPD-L03 落点定位）
- 待实施 → ③w3 检查 → 通过后 push

### ③w3 行动（全局优化 + backlog 收尾 实施 + B3 快照 + 检查发起·先验后推）
- **实施**（据 ③w2b 反评价·Codex P1×3 + glm 注意项·时间轴剥离用户拍板）：
  - `paradigm.py` `_sync_geo_catalog_guard_fields`：导入时对齐 GEO_TOOL_CATALOG 4 guard 字段 ← contracts（validate drift 修复·**4 passed**）
  - `build_outlet_schema.py`：renewal 卡 perceptible_metrics domain 门控（仅 urban_governance）·+测试
  - CLAUDE.md 当前开发状态 5 行（L3✅·L4🔄·空间✅·UI✅·L0→L1 补 sim）
  - todo 周归档（07-27~08-02·302 行）+ 删重复节 + decisions ADR-017~019 + 记忆 GC（删 push 记忆·标 time-axis/batch4）
  - **pytest 277 passed**（+renewal 门控）零回归
- **B3 快照**（`EMOTION_TRACE_SESSION=B3-snapshot-0804`·9.6min）：**26 例 pass=22 fail=4（84.6%·低于基线 88.5%）**·**RST-L06 回归**（多步「先裁剪再热力图」·tools= 空·旧 PASS）·PRM-03/04 buffer radius[ERR]·PRM-07 zonal 边界（已知 backlog）
- **RST-L06 根因假设**：paradigm density.when 同步成 contracts（加「方格/网格聚合→mode=3d」）为唯一 LLM 可见差异·疑影响「热力图」路由·**待两组 SCAN 独立判断 + 实证**
- **检查发起**：`_handoff/CB16-GlobalOptimize检查_2026-08-04.md`（7 问·含 RST-L06 回归根因）
- **未推**（先验后推）·**tracklog 待补**（trace_query B3-snapshot-0804·分类器不可用阻塞）
- 待两组检查 SCAN → 反评价 → 通过后 push

### ③w3b 反评价（glm + Codex 实施后检查 SCAN·两组通过·可推）
- **Codex**（`scan/CB16-GlobalOptimize检查_Codex-GPT5_2026-08-04.md`）：实施通过·无 P0/P1·可推。**RST-L06 根因修正**：claude组 的 paradigm 假设不成立——实时 FC 路径（router.py fc_diagnose）只用 build_fc_sys_prompt + contracts_to_tools_schema·**不消费 paradigm**·geo_tool_catalog_text 仅进 build_diagnose_prompt（eval/fallback）。回归 = LLM 方差（16 份历史 audit：RST-L06 08-03×3 PASS/本次 FAIL·PRM 同型翻转·spread 13→25）。**建议保留 paradigm 同步** + P1 验证（eval 回归 + RST-L06 复跑 ×3）。修正声明：CPD-L03 落点 frontend/js/test-cases.js:17（非无此文件）。
- **glm组**（`scan/CB16-GlobalOptimize检查_glm组_2026-08-04.md`）：通过·**disagree claude组 假设**——RST-L06 根因 = **clip range 未 derive**（chain pre-check boundary derive 缺陷）→ validateParams fail → ask_user → tools=[] 无执行。证据：FC 正确选 clip（template=clip）·density.when 不影响 FC 选 clip·CB-12 P2 后缀（方格/网格）对问句无关。density.when 同步应保留（消除漂移·CI 红线）。**验证方向**：`deriveAvailable('先裁剪西陵区情绪点，再生成热力图', getLayers())` 是否 null。
- **反评价**：两组通过·可推。**保留 paradigm 同步**（消除漂移·正确方向）·实施 3 项正确（validate 4 passed + renewal 门控 + 全局优化）·PRM-03/04/07 = 既有 backlog·**RST-L06 = 独立 backlog**（clip range derive·非本次引入·修法 = 排查 chain boundary derive·Codex 建议复跑 ×3 实证）
- **待**：eval 回归（P1 验证·同步改附录文本）+ RST-L06 复跑 ×3 → 通过后 push

### ③w4 行动（措辞修复 + 发版遗留问题 综合预检发起·用户定一并打包）
- 用户实测「EMC 无法回答时结论统一'无法生成图层'·但问题可能与图层无关」→ 出 plan 进 CB·用户再定**把发版遗留问题一并打包定 plan**（`_handoff/CB16-WordFix预检_2026-08-04.md`）
- **① 措辞修复**（根因：harness.js:1310 gap 只看产出不看问题性质·composeGapCard :227 默认「没能生成可用的图层」·无「无法回答」措辞）：草案 = failedObs.length>0（在试图层）→ 现有图层措辞；=0（零工具尝试）→ 新「当前无法直接回答」措辞·exit:'gap' 结构不动
- **② 发版遗留问题打包**（用户定）：eval 76% NO-GO（歧义路由 multi 治·MISS 2 = 商业用地/范围内密度）+ RST-L06（chain boundary derive fallback 到 presets/行政区）+ PRM-03/04（buffer radius 解析）+ PRM-07（zonal 非 preset fallback）
- **预检 12 问**（给两组）：措辞 failedObs 判据 + eval 歧义路由 + RST-L06 硬化 + PRM 范围 + 测试方案 + 综合优先级
- 待两组 SCAN → 反评价 → 实施

### ③w4b 反评价（glm + Codex 综合预检 SCAN·两组通过·无 P0）
- **glm组**（`scan/CB16-WordFix预检_glm组_2026-08-04.md`）：
  - 措辞 failedObs=0 判据可靠（仅 loop 内 push）·建议区分 degraded（无法理解）vs ask_user（暂无法回答）两子情况
  - **eval 根因纠正**：select_template 单工具选择器不返回 multi·eval 期望 multi = 标尺错 → 改标尺（multi→clip/density·76%→84%）非改路由·不碰 v1 eval-anchor
  - RST-L06 硬化方向对·fallback 加区名条件（有区名才 fallback·无区名不猜）
  - PRM-03/04 center ask_user 正确行为·改断言非代码 · PRM-07 改 fixture
- **Codex**（`scan/CB16-WordFix预检_Codex-GPT5_2026-08-04.md`）·P1 修正×5：
  - **PRM-03/04 真根因 = stale tool 门控**：`const tool` :1430 早捕获·G5 reroute lookup_place→buffer 后 :1546 `tool==='buffer'` 用旧值跳过·radius 正则派生已存在 → 修 reroute 后重读 tool
  - **PRM-07 = FIXED_ADMIN_DISTRICTS 白名单门控**（preset 实测含 9 法定功能区·模型硬识别有数据来源·CB-14 红线）·**弃 lookup fallback**
  - RST-L06 根因未实证（两种机制一致·需 per-test trace）·fallback 须 feature 级提取（仿 :1453-1460）
  - eval 先取证全 miss 列表（37 条 9 MISS·草案只列 2·E1 两例是覆盖偏好非缺陷）
  - 措辞须两处分支（composeGapCard 默认 :227 + gap 出口追加行 :1313 无条件硬编码）
- **反评价采纳**：措辞两处分支 + failedObs 判据·eval 改标尺（先取证）·RST-L06 硬化（feature 级 + 区名条件·根因待取证）·PRM-03/04 stale-tool 门控·PRM-07 白名单门控（弃 fallback）
- 待实施（②a 措辞 + ②b eval/RST-L06/PRM）→ ③w5 检查 → 通过后 push

---

### ① SCAN 摘要

**本轮由 claude组 发起**（非第三方 SCAN）：用户今日确立两个核心定性，重新定义 EMC 数据认知边界与标准出口——① 范围=矢量表达不关键·地点认知（拓扑）是关键·范围锚定三来源+诚实 request_upload ② 归因↔地点联动=中微观标准出口·标准分析结论（格子/热点）与地点信息联动·归因指向具体地点。需求报告：[EMC-数据认知体系重构需求](discuss/EMC-数据认知体系重构需求_2026-08-03.md)（含四阶段讨论演进脉络 + 现状调研 + 6 讨论焦点）。请求：[CB15-数据认知-评估请求](_handoff/CB15-数据认知-评估请求_2026-08-03.md)。

**现状调研关键**：
- 已有：范围三来源部分落地·网格级归因（domain_top/element_top/place_name）·POI 引擎（1270+157+7·rapidfuzz 分档）·逆地理编码（高德 regeo 已接·地址/区/街道）·L1/L2 点带地点标注
- 缺失：POI 进问答管线（LLM 不可见）·格↔POI 空间查询·评论↔POI 运行时关联·地点级归因聚合·批量逆地理·范围↔位置拓扑枚举
- 孤岛：DATA/POI/yichang_pois.geojson（3220 条）无消费方·amap_poi_centralcity 缺失·buffer 中文 POI 名失败

### ② 我方反评价（对 CB-15 两组 SCAN · 讨论稿·非定稿）

**五点共识两组独立一致，全部 agree**（verify-before-accept 通过）：

| 讨论点 | 判定 | 证据 |
|---|:---:|---|
| 架构分层（后端空间查询 + 前端联动工具） | **agree** | 空间计算（sjoin/逆地理）在后端（geopandas/4546）·联动呈现在前端·同构 zonal/compare 模式 |
| 触发双层（默认轻量 place_name + 按需重查） | **agree** | 全量清单 token/配额爆·对齐悬停试探/点击锁定·place_name 已有 |
| 3220 接入 + 最近 POI 反查 | **agree** | 复用 reverse·text 抽取确定性差弃用·模拟标注 schema 复用 |
| 配额节流（本地优先 + 上限 + 持久缓存） | **agree** | glm 补 lru_cache 坐标级去重·跨会话无效→持久化缓存 |
| 承重零触碰（只增不改 + 契约三处同步） | **agree** | 不触 diagnose/harness/ChatRequest·place_layer 数据扩展非接口变更 |

**关键发现（glm 独有·已核实）**：
- **place_name 依赖 sim 期标注**（`spatial_analysis.py:585-597` 只读 spatial_hotspot/area_seed·不碰 POI）→ 真实数据恒空→下钻链第一步断。**verify 属实·Codex 遗漏**。修正：P0 双源融合（sjoin POI 优先·fallback 标注）。

**分歧待收敛**：centralcity 缺失（Codex: 本地重生成 vs glm: regeo 兜底）·AI 工具 lookup_place 是否 P0（glm 倾向 P1）。

### ②b 出口抽象层并入（glm 课题·立项关键）

**用户提交 [EMC-出口抽象层架构讨论](discuss/EMC-出口抽象层架构讨论_2026-08-03.md)**（glm 课题·立项成败关键）——承接 CB-15，定义「分析完成后」的出口范式。

**核心命题**：EMC 的"出口" = 分析结果 → **行业接口格式化对接**（成果范式 agent·第三段）。底层逻辑三铁律：**EMC 找市场接口（非市场找 EMC）** / **三段式线性（意图→结果→成果范式·禁一竿子插到底）** / **定性+定量+地理信息按尺度分类**。

**关键缺口（已核实）**：出向链路 = 0（全仓库无 IndustryAdapter/OutletAdapter）·`DOMAIN_OUTLETS`（paradigm.py:70）纯 dict 无序列化/导出·诊断卡 `outlet`（:462）7 值枚举引导词非契约。**立项风险点**。

**已完整**：行业接口清单（八项任务/体检四维度/8大领域/三级体系·政策底座附 C 全文）+ 4×5 归因↔体检指标↔更新任务映射 + 六大演示场景（S2 更新需求分析最有力）+ 六大讨论焦点。

**与 CB-15 协同**：CB-15（分析过程中·格↔POI 联动）**先行** → 出口抽象层（分析完成后·成果范式）依赖其产出（micro 落点清单需 CB-15 的归因↔地点联动填"地理定位"要素）。两者前后承接构成完整链路。

### ③ 行动
- 深读两组 SCAN + verify-before-accept（place_name 依赖核实）
- 评估落库：需求报告追加 CB-15 评估节（五点共识 + 致命发现 + 优先级 + 6 讨论焦点）
- 研读出口抽象层报告 + 核实 DOMAIN_OUTLETS/outlet 缺实现 + 出向链路=0
- **发起三方讨论**（出口抽象层 × CB-15 数据认知·协同收敛）
- **出口卡片对标对表**（用户要求·搜索国内案例）：宁夏 3表6图 / 片区 13表13图 / 满意度问卷 4 尺度 / 完整社区 6 目标 20 项 → 梳理「行业要求 × EMC 产出一一对应」→ 更新专业版 5.4/5.5/5.6 + 焦点7 + 通俗版四补充（双主线·能/不能双栏·三典型场景）

### ④ 状态
`讨论中 → 三方讨论收敛` —— CB-15 五点共识已立 + 出口抽象层并入（立项关键）+ 出口卡片对标对表落地（结构化为"顶层→板块→指标→核心指标"·能/不能双栏·聚焦不夸大）+ 报告 EMC→情绪地图·EMC（首用全称·后简称·案例深挖湖北/上海/广州/南京真实数据）+ **outlet_kb 出向知识库已建**（7 契约 + 8 指标 + 5 案例 + 测试 6 passed·pytest 234）+ **出口修正工程讨论发起**（结果范式 agent 架构/outlet_id 映射/outlet_kb 接入/CB-15 协同/MVP）·两者协同：CB-15 先行 → 出口抽象层依赖其产出·待三方收敛。

---

## CB-14 · 2026-08-03（RAG 定稿 + 修复检查 · 发起）

### ① SCAN 摘要

**双线**：① RAG 研究定稿（用户新设想·多方讨论）：两组 SCAN（[glm](scan/CB14-RAG-glm组_2026-08-03.md) + [Codex](scan/CB14-RAG评估_Codex-GPT5_2026-08-03.md)）一致——**现在不建 RAG·改做 RAG-lite（A4 选择性注入）**。关键：A4 是 D019 主动裁剪（非容量约束）·industry_kb 渲染仅 19.7KB·DeepSeek 无 embedding 端点·Py3.14 向量库风险。
② 收敛 CB-13 残余 + 推进 P1（A4）：claude组 完成 3 处修复（CPD 测试基建 / PRM-08 compare 兜底 / A4 选择性注入）→ 发两组检查。请求：[CB14-检查请求](_handoff/CB14-检查请求_2026-08-03.md)。

### ② 我方反评价（对 RAG 定稿）

| SCAN 结论 | 判定 | 证据 |
|---|:---:|---|
| 现在不建 RAG（glm+Codex 独立一致） | **agree** | 知识超限不存在·A4=工程裁剪·embedding 硬阻塞 |
| A4 选择性注入 = 正确解法 | **agree** | EMC 已有 domain_lens 检索键·轻 10 倍·零依赖 |
| 分阶段（P1 注入→P2 做厚→P3 真 RAG 触发式） | **agree** | ROI 不成立·知识成长后再评估 |

### ③ 行动
- 收敛① CPD 测试基建（test-cases.js CSV→yichang + L03 硬断言）
- 收敛② PRM-08 compare 兜底（harness.js `_allToolCalls` 重写对齐 clip/zonal）
- P1 A4 选择性注入 finalStep（industry_kb_final_brief + build_final_prompt + 守卫测试）
- 发 CB-14 检查请求给两组（3 项改动检查）

### ②b 我方反评价（对 CB-14 修复检查 SCAN · Codex + glm 两组）

**3 处修复两组一致判定"正确可提交"**。verify-before-accept 全部成立：

| 改动 | 判定 | 我方核实/证据 |
|---|:---:|---|
| CPD 测试基建（CSV→yichang + L03 硬断言） | **agree** | 文件实存·loadCSV await 无竞态·L03 硬断言是新对话引导态的诚实探针 |
| PRM-08 compare `_allToolCalls` 重写 | **agree** | `:1033` deriveMissingParams 先于 `:1077` runAllToolCalls·重写必然生效·区名<2 与误改边界安全·三分支 if/else if 互斥 |
| A4 选择性注入方向 | **agree** | 链路闭环（harness→stages→api→router→prompts）·静态门禁不破·正治 A4 痛点 |
| **A4 体积口径**（Codex：每域 1.6KB 非宣称 0.6KB）| **agree（修正）** | 我宣称"每域 ~0.6KB"不实·实测 1.6KB·须修注释/文档口径 |
| **A4 注入条件过宽**（glm 改进点①）| **partial** | Codex 判断"自然门控已存在·保留观察"更稳——硬加 decision_type 门有漏注风险·采纳「观察哨」方案·但同意纯 GIS 操作无谓回弹是真实场景 |
| **静态门禁盲区**（glm 改进点②）| **agree** | `test_final_prompt_stays_lean` 传 `('','')` domain_lens=None 不触发注入·条件注入路径无体积守卫·须补 |
| 复合问句次级 call 丢弃 | **agree（已知限制）** | 与 clip/zonal 既有模式一致·不单列修复 |

**CB-14 ②b 反评价：5 agree / 1 partial / 0 disagree** · 两组代码级判定 + 我方 verify 全成立。

### ③b 行动（修复检查后的收尾）
- **采纳 glm 改进点②**：补条件注入体积守卫测试（四域全注 <5KB·防 final_brief 加厚回弹）
- **采纳 Codex 口径修正**：A4 注释/文档"每域 ~0.6KB"→"~1.6KB"
- **注入条件**：保留现门控（domain_lens 非空）+ 观察哨（B3-verify-06 延迟/答案风格）·不硬加 decision_type（防漏注）
- 等 B3-verify-06 落盘补 CPD/PRM-08 实测复核

### ④ 状态
`修复检查闭环 → 待 B3-verify-06 实测复核` —— RAG 定稿已达成；3 处修复两组判定正确可提交；A4 体积口径修正 + 补体积守卫测试；B3-verify-06 运行中。

---

## CB-13 · 2026-08-03（B3-verify-05 实测 88.5% + 代码修复检查 · 发起）

### ① SCAN 摘要

**本轮由 claude组 发起**（非第三方 SCAN）：B3-verify-05 全量重测结果已出（**23/26 88.5% 历史最佳·RST-L06 多步问收敛**），发 Codex/glm 两组检查代码修复情况。评估请求：[CB13-评估请求](_handoff/CB13-评估请求_2026-08-03.md)。

**B3-verify-05 实测**（`report-2026-08-03-03-llm` + `audit-B3-090102` + trace `--session B3-verify-05`）：
- 总 pass **23/26 (88.5%)**·0 timeout·误杀/漏判 0·计划命中 16/20 步
- **RST-L06 PASS**（tools=clip,density·1→2层）→ **多步问修复收敛·CB-12 闭环**
- PRM 9/10（PRM-08 fail·tools=extract_feature 单工具·boundary[ERR]·疑 compare 路由退化）
- F_002=4（≤5 阈值·while-loop 早停生效）·pro 0·F_005=20

### ② 我方反评价（对 CB-13 SCAN · Codex + glm 两组）

**两组结论高度一致，且均已独立核验通过**。verify-before-accept：

| SCAN 结论 | 判定 | 我方核实/证据 |
|---|:---:|---|
| **多步问最终收敛（CB-12→13 闭环）** | **agree** | RST-L06 两轮连续 PASS（tools=clip,density·1→2层）·F_002=4（≤5）·pro 0·三方证据（report+audit+trace）一致 |
| **PRM-08 非路由退化·非测量层失效** | **agree** | `test-cases.js:317`（PRM-08 严查 expectBoundary）vs `:361`（RST-L02 只查产层）同句不同判·3abb503 只修测量端（`test-cases.js`）不修执行端·FC 选型偏离 compare→extract_feature 是根因 |
| **CPD-L01/L02 = 测试基建文件名过期**（Codex）| **agree（实锤）** | `DATA/performance/` 仅 `yichang_*`·`xiling_wujia_*` 不存在·`test-cases.js:8` 引用过期文件名·loadCSV 404 静默返 `{ok:false}`·CPD 引导逻辑正常（`cpd-guide.js:59/66` 文案在）|
| **glm CPD 时序/元数据待证** | **partial** | Codex 文件名实锤解释「导入失败」→ 时序假设可能 moot；但「loadCSV 后元数据是否与运行时一致」仍未证·留取证 |
| **上轮 3 注意点已落地** | **agree** | Codex 核 `_hasSeq` 收紧（`harness.js:1087`）+ Pro chain 前置 + glm recover 链前置（`harness.js:984-992`）·F_002 低位证明生效 |
| **F_002=4 是兜底生效结果·勿拆** | **agree** | glm 对（预防性兜底看防的风险是否仍在·FC 方差仍在）·保留 recover 链前置 |
| **顺序词正则抽常量**（`_hasSeq` vs `_seqRe`）| **agree** | `harness.js:1087` 与 `:986` 字面相同分两处·改一处须同步·抽常量防分裂 |
| **Pro chain 死路径** | **partial** | Pro 停用后 `:1072` 附近成死代码·清理低优先·防未来 Pro 复活误判 |
| **MOD_LLM.F_002 backlog 建议重核** | **agree** | Codex 对（`chat_with_fallback` 入口日志·25 条全 attempt=0·非真实 fallback 数）·backlog 数字需修正 |

**CB-13 反评价：8 agree / 2 partial / 0 disagree** · 两组独立结论 + 我方 verify-before-accept 全部成立。

### ③ 行动

- **PRM-08（高）**：compare 缺确定性路由兜底（CHAIN_REGISTRY 无 compare 链·FC 选型偏离时无兜底）→ 下轮 CB-14 修：仿 clip_density recover 模式，问句含 对比/比较/VS 且可派生 ≥2 区名时合成 compare + 确定性填 boundaries。**先取证**（glm 建议）：带 session 单跑 PRM-08 问句 5 次 + console/网络面板抓 FC tool_calls，确认「范围内」是否抢答触发点（假设 A/B 待证）。
- **CPD-L01/L02（高·1 行）**：`test-cases.js:8` CSV 改走 `resolvePoints('L1-T1')` 或改存在文件名——**测试基建修复，非产品 bug**。建议 CPD-L03 恒真断言改硬断言。
- **学习入库（KNOWLEDGE §3）**：① 修复测量端 ≠ 修复执行端（3abb503 教训）；② template 对但工具错 → 查 FC sys prompt 工具决策规则排序 + when/examples 诱导性，非查 select_template；③ 预防性兜底必要性看防的风险是否仍在。← CB-13
- **backlog 修正**：MOD_LLM.F_002 fallback 79 次含 3 ERR → 重核为「调用数」非「fallback 数」（Codex）。

### ④ 状态
`闭环达成 → CB-12→13 多步问收敛 · 残余 PRM-08/CPD 转 CB-14` —— 多步问修复最终收敛·CB-12 三项主成果守住·PRM-08（FC 选型兜底）+ CPD-L01/L02（测试基建）进下一轮。

---

## CB-11 · 2026-08-02（主通道验证·glm组 第三方）

### ① SCAN 摘要
[CB11-主通道验证_glm组_2026-08-02](scan/CB11-主通道验证_glm组_2026-08-02.md)（glm组·ZCode + GLM 5.2 首次加入·独立第三方）：主通道 A 方向正确·但 **G1/G2 union 链无限循环致命 bug**（`buildLanduseCompletion:1351` + `_deterministicRecover:1235`·迭代 `_tcs` 同时 push → JS heap OOM·Node.js 复现）——**用户测试②「合并 3 类用地」直接命中**（2/6 步失败）。G3 inline N/M 时序缺陷（finalStep 看不到扩展失败·LLM 写乐观结论）·G4 boundaryName 硬编码「西陵」·G5 遥测不持久化·触发入口不一致·多步形态覆盖窄。

### ② 我方反评价（结合用户手动测试 4 用例·verify-before-accept）

| glm组 | 判定 | 证据 |
|---|:---:|---|
| G1/G2 union 无限循环 | **agree** | 读码确认 `:1351 for(i=1;i<_tcs.length;i++) push`·**用户测试②命中**（合并→2/6 步失败）·必修 |
| G3 inline N/M 时序缺陷 | **agree** | inline 路径 finalStep 前未注入扩展失败·LLM 可能写乐观结论（对比 runAllToolCalls 有 `_failNote`） |
| G4 boundaryName 硬编码西陵 | **agree** | `_polyLayers.find(l=>l.name.includes('西陵'))`·非西陵区失效 |
| G5 遥测不持久化 | **agree** | console 仅本会话·跨会话丢失·应仿 `_TPL_STATS_KEY` 写 localStorage |
| 触发入口不一致 | **agree** | inline/autoExpand/recover 三套触发条件·同一问句成功/失败走不同扩展 |
| 后端补全建议 | **partial** | 中期演进·记待修（contracts 元数据支撑） |
| 多步形态覆盖窄 | **partial** | merge→clip/filter→density 记待修 |

**用户手动测试（claude组 侧证据）**：① 剪裁 3 类用地成功但报「3/4 扩展」（N/M 口径把第 1 步 extract 算进分母 + 未列失败图层名）；② 合并 3 类用地失败（=G1/G2 union 循环）；③ 筛选情绪点样式不对（clip 产物无图例继承 = 族 D）。**新要求**：关 C 键对比（保留时间轴按钮）+ **EMC 产物不临时创造样式**（用固化图例）。

**CB-11 反评价：7 agree / 2 partial / 0 disagree**

### ③ 行动
- P0：修 G1/G2 union 链无限循环 + 关 C 键
- P1：G3 inline N/M 时序 + N/M 提示列图层名 + 点层样式继承（clip 用固化极性图例）+ G4 去西陵硬编码
- P2：G5 遥测持久化 + 触发入口统一 + 多步形态扩展 + 后端补全
- 验证：pytest + 复测 B002/合并/B006 + C 键无效

### ④ 状态
`open → 修复执行中` —— 用户手动测试已确认 G1/G2 根因·计划已批准（`claude-code-emotion-map-purring-ritchie.md`）。

### ③·merge 多图层修复定稿反评价（Codex + glm组 方案 A · 9f84eac）

> 问题报告 [CB11-merge-multi-layer](problem_report/CB11-merge-multi-layer_2026-08-02.md) → Codex + glm组 独立一致裁决方案 A（后端 `merge(layers=[...])` concat·非 overlay union 空间并集）。

| 项 | 判定 | 落地 |
|---|:---:|---|
| 选 A（后端 layers concat）·双组独立一致 | **agree** | 9f84eac 落地 |
| B（overlay union）字段冲突（glm组 geopandas 实测 3→9→13 列）| **agree** | 拒绝·保留 overlay 空间并集能力 |
| 并入 merge 不建新工具 | **agree** | merge 加 layers 模式 |
| one-of 校验最容易漏 | **agree** | validate_tool_call 特判 + stages required_slots=[] + tools guard |
| `_source_layer` 标记列（glm组）| **agree** | 后端 concat 加 |
| overlay 字段爆炸负向测试（glm组）| **agree** | test_overlay_union_field_explosion_negative |
| union 链对 merge 语义退役 | **agree** | buildLanduseCompletion/recover 模式 A/C 改调 concat |

**CB-11 ③：merge 多图层修复——7 agree / 0 disagree · pytest 223 passed · 待用户自测**

### ③·「剪裁+合并」只说不做反评价（Codex + glm组 · 防线结构性洞）

> 用户问句「剪裁出西陵区范围…合并成一个图层」→ Playwright 实测：**执行只有 extract_feature→merge（无裁剪），结论却声称「执行裁取操作·严格落在西陵区边界内」**——只说不做复发。两组报告 [Codex](scan/CB11-剪裁合并结论撒谎_Codex-GPT5_2026-08-02.md) + [glm组](scan/CB11-clip-merge-hallucination_glm组_2026-08-02.md) 一致：**4 问题全成立·根因=防线系统性盲区（只验图层存在·不验操作是否执行）**。

| 项 | 判定 |
|---|:---:|
| 问题 1 结论与执行不符（只说不做）| **agree**·最严重 |
| 问题 2 buildLanduseCompletion 丢裁剪语义（`_wantUnion=/合并/` 互斥吞「裁剪」）| **agree**·执行层根因 |
| 问题 3 防线无操作描述检测（结构性洞·L1/R1-R7/零图层守卫全失明）| **agree**·根治关键 |
| 问题 4 observation 语义不足（merge 不含来源/是否裁剪）| **agree** |
| 分歧 2 多次修复仍复发（防线只验存在性）| **agree** |
| 分歧 3 R9 步骤描述对账（<5ms·确定性）| **agree** |
| 分歧 4 执行路径 A vs B' | **用户拍板 A**（先裁剪再合并·架构契合：toolHistory 可审计·复用既有 intersection 链·B' 全量中间产物混淆）|
| 分歧 5 优先级 | **用户拍板 R9+两阶段同时**（glm组·只修其一「只说不做」换变体复发）|

**CB-11 ④：只说不做定稿——8 agree / 0 disagree · 修复 = R9 + 两阶段（A）+ merge observation 来源标注 · 待实施**

---

## CB-10 · 2026-08-01（EMC 全面审查·Codex+GPT-5 第三方）

### ① SCAN 摘要
[CB10-EMC全面审查_Codex-GPT5_2026-08-01](scan/CB10-EMC全面审查_Codex-GPT5_2026-08-01.md)（Codex+GPT-5·只读审查·分支 fix/emc-buglog @ a274362）：
- 综合分 **6.0**（架构 6.5/代码 6.5/测试 5.5/Harness 6.0/文档 4.5/调用 6.0/演示 5.5）
- **架构级缺陷 4 条**：① plans[] 从未接通管道（executePlans 零调用·07d57c1 禁用·CPD 不读）② 编排器正变"领域推理器"（_LANDUSE/_DK/_POL_MAP 词表散落）③ FC prompt 无版本化守卫（两次重写静默丢极性纪律）④ 文档-代码双轨不同步（D057/finalStep/221 passed/分支 hash）
- **P0 4 条**：接通 executePlans(方案A)/删 plans(方案B)、恢复极性纪律+守卫、计划完成度守卫、修 test_final_prompt_stays_lean
- **P1 5 条**：buglog 状态单源、B003 短路、B007 几何类型门、B008 2D/3D 解耦、B006-B 样式继承
- **P2 2 条**：文档同步、修复内容守卫清单
- 实测：pytest 196 passed/20 failed/5 skipped/3 errors（20 failed = test_sandbox 隔离问题·非回归；真实未修回归 = test_final_prompt_stays_lean 3616B>3KB）

### ② 我方反评价（verify-before-accept·读真码核实·待 Codex 对反评价二轮评估）

| SCAN 建议 | 判定 | 证据/行动 | decline reason（若 disagree） |
|---|:---:|---|---|
| P0-1 接通 executePlans(方案A) / 删 plans[](方案B) | **partial** | 方向「计划→执行闭环」agree。方案A 不采：executePlans（harness.js:1320）是被 D057 修订 `_allToolCalls`→`runAllToolCalls` 取代的死代码，非 CPD 接口；方案B 不采：plans[] 是给 CPD 的预留接口（CPD 搁置≠删），删概念撞用户立场。B005 真缺口 = `_autoExpandOverlays` 需≥2 关键词（单用地不触发）+ FC 单 tool_call 无补全 → 走 `_allToolCalls` 覆盖缺口 + Day1 浏览器验证定位 | — |
| P0-2 恢复 FC prompt 极性纪律 + 内容回归测试 | **agree** | 证据链强：31e2a00 有纪律段 → 0073990/500d4b9 静默删 → 当前 router.py:52-59 无。恢复已验证段（非重写）+ tests/test_emc_template.py 断言守卫防再删 | — |
| P0-3 计划完成度守卫 | **partial** | 方向 agree。当前「计划」=`_allToolCalls` 数组非 plans[]（D057 修订后）；runAllToolCalls 已有 failedSteps 注入+零图层守卫，缺 finalStep 前显式「完成 N/M 步」判定 → 补 | — |
| P0-4 修 test_final_prompt_stays_lean | **agree** | 真实未修回归（SCAN 实测 3616B>3KB·非沙箱误报）。先看 FINAL_TEMPLATE：无损瘦身则瘦身，否则放宽守卫+记 ADR | — |
| P1-1 buglog 状态单源 | **agree** | `_gen_index.py:59` 从目录派生、忽略 frontmatter → B010/B011 frontmatter=resolved 却计 OPEN·真 bug → 读 frontmatter 优先 + B010/B011 移 resolved/ | — |
| P1-2 B003 数据清单短路 | **agree** | 与既有方案一致：`_quickIntent` 加清单意图 → general 短路（buildContext 来源标注已就绪 tools.js:596） | — |
| P1-3 B007 几何类型门 | **agree**（后置） | clip/extract/overlay 加类型一致性校验 + 契约强化（两天空隙·非 P0） | — |
| P1-4 B008 2D/3D 解耦 | **partial** | MED·前端渲染·不在两天重点·记待修 | — |
| P1-5 B006-B 样式继承 | **partial** | 方向 agree（symbology propagation·clip/extract/overlay 产物继承源层图例）·超两天范围·记待修 | — |
| P2-1 文档同步 | **agree** | todo.md 按已提交重写 07-30 Codex 段 + 补 08-01；emc-fix-progress/_cb-index/SUMMARY/02-orchestrator D057 同步；CB 环境 ZCode→Claude Code+Codex/DeepSeek | — |
| P2-2 修复内容守卫清单 | **agree** | 关键修复（诚实观测/多步扩展/极性纪律）做成可 grep/可断言·防 prompt 重写静默丢弃 | — |
| 发现2 编排器泄漏智能 | **partial** | 泄漏真实（_LANDUSE/_DK 词表散落 harness/stages）→ **集中到一个模块 agree**；**完全消除确定性兜底 disagree**——07-30 P03 教训：依赖 LLM 单次行为不可靠（no_tool_calls 必现），确定性恢复是务实妥协，非"泄漏" | — |

**Auto-Check 清单**：① 承重红线——无触碰（P0-2 恢复的是 FC sys prompt 纪律段，非 diagnose eval prompt·不撞「diagnose 永不动」）✅ ② verify-before-accept——P0-1/P0-2/P1-1 均读真码核实 ✅ ③ 无消费者→wontfix——P0-1 方案A(executePlans) 无活消费方·不盲修 ✅ ④ 已知模式——「eval≠runtime」SCAN 正确认识未套错 ✅

**CB-10: 9 agree / 0 disagree / 5 partial**

**第三方复核结论（Codex 二轮审核 · [CB10-反评价二轮审核](scan/CB10-反评价二轮审核_Codex-GPT5_2026-08-01.md)）**：反评价整体公允（事实核查到位）·7 条修正全 accept——

| Codex 修正 | 判定 | 整合 |
|---|:---:|---|
| B005 修复通道：扩成功路径 `_autoExpandOverlays` 非 `_deterministicRecover` 模式 D（触发位置错）| accept | Day1 改 `_autoExpandOverlays` 放宽单用地+双区 |
| B007 类型校验随 P0-1 同包（自动多步静默放大错配）| accept | B007 guard 并入 P0-1 同包·契约强化留 P1 |
| 完成度守卫：结论层确定性追加「已完成 X/Y 步」代码行，非仅 context 注入 | accept | Day2 P0-3 代码层确定性追加 |
| FC prompt 守卫覆盖四段（极性纪律/plans/domain_lens/多要素提取）+ `build_fc_sys_prompt` 抽函数 | accept | Day2 P2-2 四段断言 |
| P0-4 先分解静态/动态，静态瘦身 ≤2KB，docstring/断言口径统一 | accept | Day2 P0-4 |
| 分歧2：失败路径兜底保留 agree；成功路径泄漏 → 集中词表+边界（多 tool_call 优先 runAllToolCalls·auto-expand 注册表+命中遥测）| accept | Day2 词表集中+边界 |
| CPD-RESERVED 是空骨架（plans 生产链已随 0073990 停供）→ 记 KNOWLEDGE | accept | Step 0 KNOWLEDGE 记录 |

**CB-10 最终：9 agree / 0 disagree / 5 partial + Codex 二轮 7 修正全 accept**

### ③ 行动
- **两天攻坚 plan 定稿**：`C:\Users\Hi\.claude\plans\claude-code-emotion-map-purring-ritchie.md`（CB-10 反评价整合版）
- **两天攻坚完成**（commit 898998b+7735cb8+392ecc1+b2949e1）：B003 数据清单短路 / B005 单用地+双区+_LANDUSE 泛词 / B006 极性纪律恢复+守卫 / P0-4 prompt 瘦身 / P1-1 buglog 状态单源 / 右半段（删 executePlans·CPD-RESERVED·P0-3 完成度守卫）/ B007 _checkGeomType 类型 guard / 词表集中 emc-patterns.js
- **验证**：pytest 220 passed + B0 飞轮 36/45 无回归 + 定向 test_p0_repro 4 用例全过（B002/B005/B003/B006）

### ④ 状态
`done → 两天攻坚完成·Codex 验收：有条件通过` —— Codex 验收报告（[CB10-两天攻坚验收](scan/CB10-两天攻坚验收_Codex-GPT5_2026-08-01.md)）7 修正全落地·4 项收尾条件（_gen_index --check 时间戳脆弱 / 文档口径 / domain_lens A 部损失入待修 / B3 全量回归）·我方反评价见下。

### ③·验收反评价（Codex 两天攻坚验收 · 逐条 agree/partial）

| Codex 验收项 | 判定 | 我方处理 |
|---|:---:|---|
| 7 修正全落地（B005/B007/完成度守卫/FC prompt/P0-4/词表集中/CPD-RESERVED）| **agree** | 属实·已核实 |
| MED #1 `_gen_index --check` 时间戳脆弱（逐字节比对→过分钟必红·CI 失效）| **agree** | 修：--check 忽略时间戳行 |
| LOW #2 emc-fix-progress 新旧混杂（更新行 a274362 / 总计行 v3.1·221）| **agree** | 统一 b2949e1/v3.3/220 |
| LOW #3 _cb-index hash 仍 a274362 | **agree** | 同步 b2949e1 |
| LOW #4 test docstring <2KB vs 断言 <3000 vs 实际 2641B | **agree** | docstring 改 <3KB |
| INFO #5 _POL_MAP overall 行残留内联 | **agree** | 并入 POLARITY_KW |
| INFO #6 部分失败 exit 仍 'result' | **partial** | 非红线·机制未破坏·与 EXIT_PARTIAL 对齐可选（本验收周期不强制）|
| 分歧（只恢复极性纪律·不恢复 plans/domain_lens/多要素提取）判定成立 | **agree** | 判定成立·domain_lens A 部损失记待修（非静默无损失）|
| 收尾条件 4 B3 全量 LLM 回归 | **agree** | 补跑 B3 更新报告（后台曾卡死·重试）|

**CB-10 ③：验收反评价——8 agree / 1 partial / 0 disagree**

---

### ③·飞轮机制审查反评价（Codex · F-1~F-13 + 7 问题族 · 逐条）

> SCAN：[CB10-飞轮机制审查与EMC问题梳理](scan/CB10-飞轮机制审查与EMC问题梳理_Codex-GPT5_2026-08-01.md)。飞轮三层互补设计优秀；4 系统性弱点 + 7 问题族归并（A 多步管道唯一架构根因·B 意图/参数概率性·C 正则覆盖·D 样式契约·E 字段已收敛·F 测试基建·G 治理）。

| Codex 意见 | 判定 | 处理 |
|---|:---:|---|
| F-1 计划命中指标语义漂移（method 派生 ≠ 计划） | **agree** | 记待修：按 `_allToolCalls.length` 实际执行通道统计 |
| F-2 断言不覆盖产物正确性（B006-B/B008 测不出） | **agree** | 记待修：density/overlay/clip/merge 产物语义断言 |
| F-3 llm 数据形态单一（无单层全量/无 polarity） | **agree** | 记待修：补 2 个数据形态用例 |
| F-4 llm 全量回归不可日常跑 → 拆 smoke/regression/full 三档 | **agree** | 记待修：三档拆分 + B3 卡死根因修 |
| F-5 llm 单次失败非回归 → 自动重测 1 次标 flaky | **agree** | 记待修 |
| F-6 no-llm 9 个 CPD/UI 失败长期红无主 → 进 buglog 或 defer 清单 | **agree** | 记待修：9 例建归属 |
| F-7 误杀/漏判投票无消费方 | **partial** | 方向对·低优先级·记待修（每月校准） |
| F-8 失败→buglog 断链（无"记录"入口）→ --collect | **agree** | 记待修：`flywheel_audit.py --collect` + 按钮 |
| F-9 仪表盘缺跨次趋势 | **partial** | 低优先级·记待修 |
| F-10 UI 交互合格 | **agree** | 维持 |
| **F-11 `--check` 时间戳脆弱** | **已修** | 742840d（`_strip_timestamp`）✓ 跨分钟验证 |
| **F-12 `_regression.md` 只覆盖 B001** | **已核实自动解决** | B010/B011 移 resolved/ 后自动收录（render_regression 按 resolved 全量）✓ |
| F-13 修复记录 commit 无祖先校验 | **partial** | 记待修：`--check` 加 commit 祖先校验 |
| 族 A 多步主通道未定型 + B002 半成品 answer | **agree** | 已记待修（B002 半成品）+ 主通道定型待架构决策 |
| 族 D 样式契约缺失 | **agree** | 已 defer（B006-B/B008）·记 P2 |

**反评价：11 agree / 2 partial / 2 已修·已核实 / 0 disagree**

### ③·飞轮机制审查深入反评价（verify-before-accept · 逐条核实代码）

> 方法：每条先 grep/read 核实 Codex 的代码级陈述（verify-before-accept），再判 agree/partial；agree 项给**具体行动方案**（非笼统"待修"）。已核实：F-1 属实（test-board.js:390-391 `_pl=method.length`）、F-2 属实（llmRun sig 只抓 tools/template/method/params/newLayers/renderedNew·不覆盖色板/几何/样式）、F-6 属实（no-llm 9 失败长期无主）、F-11 已修（742840d）、F-12 已核实自动收录。

| Codex 意见 | 判定 | 具体行动 |
|---|:---:|---|
| F-1 计划命中指标漂移（method 派生≠计划） | **agree** | `test-board.js:390-391` 改按实际执行通道统计：`_allToolCalls.length`（LLM 多 call）或 autoExpand 链长·且「实产≥计划且无失败步」才命中·保留字段名 `计划命中` 防断下游 grep |
| F-2 断言不覆盖产物正确性 | **agree** | 选 4 高频工具加语义断言：density 色板钩子（analysis=negative → 用消极色板非彩虹·CB-04 已修勿回退）/ overlay feature 数+字段 / clip 产物 point_count / merge 几何合并·断言写成 test-board 可判定的信号（暴露 `_ui`/paint）·非浏览器人工 |
| F-3 llm 数据形态单一 | **agree** | e2e-seam 补 2 用例：单层全量点（无 polarity 拆分）+ 无 polarity 字段点（走 any-point 兜底·CB-08 F2.0 回归） |
| F-4 三档拆分 smoke/regression/full | **agree（最高实操价值）** | `flywheel_audit.py` 加 `--tier`：smoke（no-llm 45 + llm 精选 10）/ regression（llm 意图+工具 30-40）/ full（B1-B3 发版）·**先修 B3 卡死根因**（`emc_helpers` 起 serve + 批处理超时——曾因 `\| tail` 缓冲误判卡死·实为输出缓冲非进程挂）·B3 用无缓冲重定向已跑通（25 例 11.1min·本日实证） |
| F-5 llm 单次失败≠回归 → flaky 重测 | **agree** | test-board `[R]` 重跑加自动重试 1 次·仍失败计 fail·报告标 `flaky`（首过/二过）·防 Flash 概率性误报回归 |
| F-6 no-llm 9 失败长期红无主 | **agree** | 9 例（CPD-03~08/10 + UI-09 + PRED-09）二选一：建 buglog 条目（标 rootcause）或进显式 defer 清单（原因+负责）·**已确认 CPD 类 = backlog T4/T5 范畴·UI-09/PRED-09 需定位** |
| F-7 投票数据无消费方 | **partial** | 方向对·但「每月校准」无机制支撑（无定时器/无触发点）·先记待修·待 F-2 断言落地后一并看投票口径 |
| F-8 失败→buglog 断链 → --collect | **agree** | `flywheel_audit.py --collect`（失败例自动产 buglog 草稿·人工确认入库·复用 bug-collector skill 标准化）·test-board 失败行加「记录」按钮走同流程 |
| F-9 仪表盘缺跨次趋势 | **partial** | 方向对·但低优先（f_4 三档拆分更急·仪表盘趋势依赖多报告积累）·记待修 |
| F-10 UI 交互合格 | **agree** | 维持 |
| F-11 --check 时间戳脆弱 | **已修** | 742840d `_strip_timestamp`·跨分钟验证 ✓ |
| F-12 _regression.md 只覆盖 B001 | **已核实自动解决** | B010/B011 移 resolved/ 后 render_regression 自动收录（实测 _regression.md 现 3 条）✓ |
| F-13 修复记录 commit 无祖先校验 | **partial** | 可做但低价值（文档防漂移够用·--check 已守生成物）·记待修·非阻塞 |
| 族 A 多步主通道未定型 | **agree** | **本轮最核心**：B002 半成品 answer 时序（全步骤完成→单次答案）记待修·主通道二选一定型（推荐 `_allToolCalls` 主通道 + FC prompt 促多 call·行为回归）·架构决策需用户拍板 |
| 族 B 意图/参数概率性 | **agree** | 守卫已收敛（build_fc_sys_prompt+断言+guard）·长期 grounding 结构化·记 P2 |
| 族 C 正则覆盖盲区 | **agree** | 已集中 emc-patterns.js + 命中遥测待加·随族 A 收敛 |
| 族 D 样式契约 | **agree** | 已 defer（B006-B/B008）·computeStyle 扩展至全部产物·P2 |
| 族 E 字段猜测 | **agree** | 已收敛（B001+CI）·低风险残留 |
| 族 G 治理 | **agree** | 文档口径已修（742840d）·流程+CI 收敛 |

**Auto-Check**：① 承重红线——无触碰（F 意见均改 test-board/audit/断言·不触 diagnose prompt/tracker/四态）✅ ② verify-before-accept——F-1/F-2/F-6/F-12 读码核实 ✅ ③ 无消费者→wontfix——F-7/F-9/F-13 低价值·partial 不盲修 ✅ ④ 已知模式——「评估偏工程标尺」未触发（本 SCAN 合理聚焦飞轮基建）✅

**反评价（深入版）：15 agree / 3 partial / 2 已修·已核实 / 0 disagree**

### ③·主通道决策评审反评价（Codex · 选 A 定型 + 3 收尾）

> SCAN：[CB10-主通道决策评审](scan/CB10-主通道决策评审_Codex-GPT5_2026-08-01.md)。**选 A 定型**（Flash 单 tool_call 是模型现实·B 低概率高成本）+ 三层定位（LLM 多 call=机会通道 / 单 call+补全=常态主通道 / recover=失败兜底）+ 3 件收尾 + 演进路径。

| Codex 意见 | 判定 | 行动 |
|---|:---:|---|
| 选 A 定型（B 降级为模型换代后评估项）| **agree** | 与项目方建议一致·B 不做当前投入 |
| 三层定位（确定性补全=常态主通道·LLM 多 call=机会·recover=失败兜底）| **agree** | 架构定位采纳·文档记录 |
| 正则补全必须保留（两层次·遥测驱动退役）| **agree** | 保留·加命中遥测 |
| a5eb3e1 部分满足族 A·「统一」未达成（3 缺口：覆盖窄/无 union 分支/无 N/M 判定）| **agree** | **三件收尾做**（见下）|
| 收尾 #1 抽共享补全函数 buildLanduseCompletion（intersection+union）·inline/autoExpand/recover 改调 | **agree** | 做：新 completion.js 或 harness 共享函数 |
| 收尾 #2 N/M 完成度判定提升为共享出口（inline 路径也追加）| **agree** | 做 |
| 收尾 #3 命中遥测（inline/autoExpand/recover 各自计数）| **agree** | 做：console 可查 |
| 风险：单技能路径无总预算（B002 43s）→ 加 45-50s 兜底 | **agree** | 做：单技能路径加总预算 |
| 风险：内联触发正则又一条内联正则 → 收尾 #1 一并移入共享 | **agree** | 做：并入共享函数 |

**反评价：9 agree / 0 disagree** · 行动 = 三件收尾 + 45s 预算 + 遥测 · 完成后用户自测一次 · 立即做 = F-1/F-2/F-6 · 本周 = F-4 三档 + F-8 · 族 A 主通道 = 架构决策待用户拍板


### ① SCAN 摘要
[SCAN_DeepSeek_05](scan/05-deepseek.md)（DeepSeek V4 Pro·ZCode 主线程）：基于用户 5 个实测案例的深度诊断——裁剪西陵+伍家岗（request_upload·推理螺旋）、上传了哪些数据（答错·信息缺失）、裁剪西陵+伍家岗再测（假结论·无执行感知）、消极情绪追问（层引用幻觉）、500m 网格聚合（图层OK/结论超时）。**核心发现**：接地上下文缺两类语义标注（数据来源+可用引用），LLM 面对信息缺口进入推理螺旋。综合分 7.3/10（↓0.6 vs CB-08）。7 条 P0-P1 建议。

### ② 我方反评价
（待项目方填写）

### ③ 行动
（待项目方填写）

### ④ 状态
`open → 待反评价` —— SCAN 已产出，待项目方逐条 agree/disagree/partial。

---

## CB-08 · 2026-07-28（EMC v1.0 聚焦修复工程·双源核实）
>
> ---
> **归档信息**：原始路径 `docs/cb-journal.md`，于 2026-07-19 移入 `docs/catch-ball/` 归档。

---

## CB-09 · 2026-07-28（multi-extract 推理死循环·where=in/A,B）

### ① SCAN 摘要
DeepSeek [rootcause/2026-07-28-multi-extract-reasoning-spiral](rootcause/2026-07-28-multi-extract-reasoning-spiral.md)：用户上传面层 + 问「裁剪出西陵+伍家岗」→ FC 死循环（extract 单要素→merge/overlay 转圈）→ 错误结论"需要数据"。4 层根因 + 5 方案。

### ② 反评价（verify-before-accept·读真码）
| DeepSeek | 判定 | 核实 |
|---|:---:|---|
| 根因1 FC 单工具冲突 | partial | 真·但 in 多值单 call 可解 |
| 根因2 推理螺旋 | agree | 症状 |
| 根因3 sys prompt 缺指引 | **agree+extend** | **且契约 `when`（=FC description）写"抽单要素"误导**（DeepSeek 漏报）|
| 方案2 _norm_where 拆逗号 | agree | 核实成立（value 不拆→isin 空）|
| 方案3 后端 in 支持 | **已存在** | 核实 `_apply_attr_filter` op='in'→isin+自纠正·DeepSeek 没核实 |
| 方案5 FC 多工具链 | defer | in 单 call 已解 |
**CB-09: 4 agree / 1 partial / 1 已存在 / 1 defer + 1 我补漏（契约描述误导）**。

### ③ 行动（commit 982a454）
- **M1** [`_norm_where`](../../api/geo_routes.py#L127)：op=in+逗号→拆 list。
- **M2** [router FC sys prompt](../../ai_qa/router.py#L60)：加多要素提取段 + few-shot。
- **M3** [契约 extract_feature](../../ai_qa/tool_contracts.py#L171)：voice/when/failure_modes/where-hint 去"单要素"+加 `in/A,B`（改 LLM 可见 description）。

### ④ 状态
`done`（commit）—— `_norm_where` 实测通过 + pytest 221 passed。**待浏览器验证**：重启后端 → 上传面层 → 「裁剪出西陵+伍家岗」→ 一次 extract(where=in/...) 出两区。
**新 learning 入 KNOWLEDGE**：契约 `when` = FC 工具 description（`contracts_to_tools_schema` desc=when）·误导性描述（"单要素"）是推理死循环的上游根因·**修契约描述优先于 sys prompt**（更上游·LLM 直接看到的工具说明）。

---

## CB-08 · 2026-07-28（EMC v1.0 聚焦修复工程·双源核实）

### ① SCAN 摘要
DeepSeek [DEEP_DIVE_2026-07-28](emc-arch-deepdive/DEEP_DIVE_2026-07-28.md)（V4 Pro·全链路+识别+路由）+ 我方 3 Explore agent 并行（链路耗时 / 数据识别 / 工具路由）。基准飞轮 `report-2026-07-28-01-llm`：75% pass、t_p50=27s、t_p95=93s。DeepSeek 结论：架构方向正确、**工具选型 100%**、瓶颈在 LLM 延迟（结构非代码）+ 数据识别盲区（pickVisiblePointLayer polarity）+ 参数填充。给 4 CRITICAL（S1-S4）+ 4 HIGH + 3 MEDIUM + 17 条 F1-F17 建议。

### ② 反评价（agree 9 / disagree 1 / partial 5·详见会话反评价表·主线程已 verify-before-accept 读真码）
**agree（采纳）**：S1 pickVisiblePointLayer 漏 polarity（**真码核实 [tools.js:664](../../frontend/js/ai_qa/tools.js#L664)·飞轮测不出·用户上传必中·入 WS2 元凶）/ S3 multi-tool while-loop 假设（部分·单工具成立）/ S4 参数填充 #1 失败 / S6 SSE 缓冲破坏流式 / S7 超时全景 / S9 字段词典缺域 / F13 per-phase 计时 / F6 FC few-shot / 工具选型 100% reframe。
**disagree**：F8 _normalizeFcDiagnose 加必填检查——**已存在** [harness.js:444](../../frontend/js/ai_qa/harness.js#L444) validateParams→exit='ask'（事实错误·DeepSeek 漏看）。
**partial**：S2 has_point 不递归 group（事实部分错·标准 L2-split 子层是顶层条目·has_point 已 true·飞轮 density 过即证·但递归加固便宜无害→采纳防御）/ S5 LLM 延迟结构性的（部分·单次调用 API 层不可解·但仍有代码级赢面）/ S8 compare boundaries 改名（partial·改 canonical 撞 schema·采 alias 更稳·但 alias 撞 zonal → 最终 drop 改 few-shot）/ S10 confidence floor 0.3（先观测·不贸然调）/ F7 rename（同 S8）。
**Auto-Check**：承重红线无触碰（F6 改 FC sys prompt 非 diagnose eval prompt·不撞红线）✅ / verify-before-accept S1/S2/S3 读真码 ✅ / 已知模式（eval≠runtime）DeepSeek 正确认识未套错 ✅。

### ③ 行动（3 WS·commit b2a24ab+943ced4+afa5db4·plan `emc-v1-0-report-...-swing.md`）
- **WS1 耗时**（b2a24ab）：Flash 默认 + 收紧 `_needsDeliberate` + SSE 流式（HTTP/1.1+分块 flush）+ 超时收紧 + profile_fields 缓存 + per-phase 计时。
- **WS2 识别**（943ced4）：**F2.0 pickVisiblePointLayer 加 any-point 兜底**（元凶）+ hidden 纪律一致 + e2e-seam 例间清点层 + 字段字典中文 fuzzy + 补规划/人口域 + **新 CI validate_field_dict_sync.py**（即抓 zone 漂移）。
- **WS3 路由**（afa5db4）：FC sys prompt 加参数提取 few-shot + eval 加 `run_fc_param_eval`。
- **据实 drop**：F1.3（zonal/compare single 类别非 while-loop·S3 归因此 moot）/ F2.1-3（C2 门已对·元凶 F2.0 下游·field-role 门重造假缺数据）/ F3.2-3（前端 validateParams 已捕获·compare alias 撞 zonal）。

### ④ 状态
`done`（commit）—— pytest **221 passed**+3 skipped 零回归·serve/boot 干净。**待浏览器验证**：重启 serve + 硬刷 → 上传 polarity 点层 → density 出图（F2.0）→ 渐进 token（F1.4）→ ~12-18s。
**新 learning 入 KNOWLEDGE**：① S1 polarity 点层飞轮盲区（飞轮 L2-group 结构测不出独立 polarity 上传）② SSE 流式 HTTP/1.0 陷阱（前开发卡此）③ 工具选型 100%·填参才是路由瓶颈（非选型）④ 字段字典前后端人工同步漂移（zone 例·新 CI 守护）。

---

## CB-07 · 2026-07-27（EMC finalStep 超时矛盾 + 2D/3D 跳组）

### ① SCAN 摘要
[SCAN_EMCTimeout](report/SCAN_EMCTimeout_deepseek_2026-07-27.md)（DeepSeek）：CB-06 后两遗留——①finalStep 超时"[请求失败]"·图已出但结论失败·矛盾（CB-06 P0-A 漏 finalStep·runTemplatePath/runChainPath 无 try/catch）②2D/3D 按钮跳组（map.js 漏 parentId）。

### ② 反评价（全 agree·已核实）
| 条目 | 判定 | 核实 |
|---|---|---|
| finalStep prompt 过大（MANIFESTO+industry_kb 20-44KB）致 prefill 超 45s | agree | build_final_prompt |
| runTemplatePath/runChainPath finalStep 无 try/catch | agree | :367/:414 核实·CB-06 漏 |
| Layer 3 降级结论 _composeDegradedConclusion（零 LLM） | agree | 治矛盾核心 |
| Layer 2 answer phase 60s | agree | 分级 timeout |
| Layer 1 轻量 prompt | agree（P1·评估后不做） | answer 质量风险·Layer 2+3 已治矛盾 |
| bug2 map.js parentId 漏 | agree | :362/:395 核实 |

**CB-07: 全 agree/0 disagree**。Layer 1 评估后留 P1（manifesto 11 节·answer 必需七/八/九/十/十一·瘦身风险 answer 质量·Layer 2+3 已治矛盾）。

### ③ 行动
- Layer 3 [harness:367/414](../../frontend/js/ai_qa/harness.js#L367) runTemplatePath/runChainPath finalStep try/catch + `_composeDegradedConclusion`（零 LLM·formatRegistry+toolHistory 拼"分析图已生成+{{show}}"·非"请求失败"丢图）。
- Layer 2 [api.js](../../frontend/js/ai_qa/api.js) phase answer → 60s timeout。
- bug2 [map.js:362/395](../../frontend/js/map.js#L362) addLayer 补 `parentId: l.parentId`（配对层留 EMC 组·不跳网格聚合组）。
- Layer 1 评估：不做（Layer 2+3 治矛盾·Layer 1 answer 质量风险·P1 留）。

### ④ 状态
`done` —— pytest 191 passed 零回归 + 浏览器加载 PAGEERRORS=0。

---

## CB-06 · 2026-07-27（EMC ReAct 超时根治·while-loop 体验）

### ① SCAN 摘要
[SCAN_EMCReAct](report/SCAN_EMCReAct_deepseek_2026-07-27.md)（DeepSeek）：用户报"思考阶段已出图（838 单元）但卡检索·超时请求失败·丢图"。全审 ReAct while-loop。根因：①B_TRACK density triggers 缺"网格/方格"→落 while-loop ②"先 query 后操作"致过度验证 ③"通常 3-6 轮"正常化多轮 ④ensure_zone observation 缺完成信号 ⑤agent_step throw 不降级丢图（我补）⑥无单轮超时（我补）。

### ② 反评价（全 agree·verify-before-accept 核实）
| 条目 | 来源 | 判定 | 核实 |
|---|---|---|---|
| L0 路由 triggers 补"网格/方格" | DeepSeek | agree | [paradigm:131](../../ai_qa/paradigm.py#L131) 核实无·CB-04 漏补 |
| L1 生成类缩轮 | DeepSeek | agree | [harness:618](../../frontend/js/ai_qa/harness.js#L618) |
| L2 工具完成信号 | DeepSeek | agree | [harness:709](../../frontend/js/ai_qa/harness.js#L709)·系统级 |
| L3 prompt 条件化 4 处 | DeepSeek | agree | prompts :92/93/95 + FINAL（AGENT_TEMPLATE·非 diagnose·不破 eval） |
| P0-A 异常降级·不丢图 | 我补 | — | DeepSeek 未提·治"万一超时/网络·不丢图·不请求失败" |
| P0-B 单轮超时 | 我补 | — | DeepSeek 未提·确定性（最坏 45s） |

**CB-06: DeepSeek 4 agree/0 disagree + 我补 2 兜底**。防（L0-L3）+ 兜（P0-A/B）互补。时间："生成方格网" 30-75s→~5s。

### ③ 行动（7 策略）
- L0 [paradigm:131](../../ai_qa/paradigm.py#L131) density triggers 补"网格/方格/方格网/聚合域/空间聚合" → "方格网"路由 density → runTemplatePath（避 while-loop）。
- L1 [harness:618](../../frontend/js/ai_qa/harness.js#L618) `_IS_GEN` 生成类缩轮 2-3。
- L2 [harness:712](../../frontend/js/ai_qa/harness.js#L712) 工具产出后 toolHistory 追加完成信号。
- P1-C [harness:686](../../frontend/js/ai_qa/harness.js#L686) 生成类+已产出+`query_*` 验证→早终止 break。
- L3 prompts :92/93/95 + FINAL 条件化（首 query 即可/数据驱动/最少轮次/勿追加查询）。
- P0-A [harness:641](../../frontend/js/ai_qa/harness.js#L641) agentStep try/catch·throw 降级 finalStep（区分 AbortError）。
- P0-B [api.js](../../frontend/js/ai_qa/api.js) streamChat per-call timeout（45s·AbortController）。

### ④ 状态
`done` —— pytest 191 passed 零回归（含 eval·diagnose 路由不破）+ 浏览器加载 PAGEERRORS=0。

---

## CB-05 · 2026-07-27（EMC UX·去审查 + 删除符号根治）

### ① SCAN 摘要
[SCAN_EMCUX](report/SCAN_EMCUX_deepseek_2026-07-27.md)（DeepSeek·UX 专项）：用户报两体验问题——①工具出图后 EMC 对话仍"思考"+ 审查未通过循环等待；②地名胶囊被删除线。DeepSeek 全审审查链路 + 删除符号双根因。

### ② 反评价（全 agree·verify-before-accept 核实）
| 条目 | 判定 | 核实 |
|---|---|---|
| 方案 B 去审查（覆盖窄/假阳性/_verifyClaims 替代） | agree | 印证·论证更细 |
| runTemplatePath 无 onObservation（UX 根因·我漏） | agree | [harness:325-366](../../frontend/js/ai_qa/harness.js#L325) 核实 |
| 内嵌自查清单（FINAL_TEMPLATE 5 条） | agree | 零额外 LLM |
| 空答案检测（代码门防只说不做） | agree | 补 _verifyClaims 漏 |
| 删除符号根因 A（REVISE_TEMPLATE 缺禁~~·我漏） | agree | [:292-312](../../ai_qa/prompts.py#L292) 核实 |
| 删除符号根因 B（CSS cite-chip-invalid line-through·**主因**·我漏） | agree | [:847](../../frontend/js/ai_qa/panel.js#L847)+[css:284](../../frontend/css/ai_qa.css#L284) 核实·**关键修正** |
| 四层根治 | agree | 全采纳 |

**CB-05: 全 agree/0 disagree/0 partial**。DeepSeek 补我漏的 3 根因（runTemplatePath 无信号/CSS invalid 主因/REVISE 缺规则）。**关键修正**：删除符号主因是 CSS cite-chip-invalid（非 markdown ~~），原"仅 strip ~~"治不了，需扩展 getValidRefNames 治本。

### ③ 行动（去审查 + 删除符号四层）
- **A 去审查**：REVIEW_ENABLED 默认 false + FINAL_TEMPLATE 内嵌自查 5 条 + 空答案检测（newLayerCount>0 但结论<20 字符→补引导）+ runTemplatePath 加 onObservation + panel 清审查 UI（占位/_PHASE_ORDER/审查区/文案）。review.py 保留开关（emcReviewOn 调试）。
- **B 删除符号四层**：renderAnswer strip ~~ + REVISE 补禁~~ + getValidRefNames 扩展所有 polygon（治 CSS invalid 主因）+ cite-chip-invalid line-through→opacity。

### ④ 状态
`done` —— pytest 191 passed 零回归 + 浏览器加载/console 无 JS 错。体验：工具出图→finalStep 流式结论→完成（省审查 7-14s）。地名胶囊无删除线（CSS invalid 治本）。

---

## CB-04 · 2026-07-27（EMC 架构 · density/polarity 流水线契约整改）

### ① SCAN 摘要

[SCAN_EMCArch_deepseek_2026-07-27](report/SCAN_EMCArch_deepseek_2026-07-27.md)（DeepSeek，L1 全量审计）：触发用例"生成 L2 消极点的热力图"→ 实出综合彩虹图。**全量审计 14 个 `generate*ForAI` 入口**，定性为**系统性参数契约不完整**（非孤立 bug）。总评 6.5/10（认知 6 / 编排 9 / **执行 4↓** / 输出 8）。

分级发现：🔴 P0 = H1 [generateHeatmapForAI:819](../../frontend/js/heatmap-tool.js#L819) 硬编码 `rampKey:'rainbow'` 绕过 [computeStyle:93](../../frontend/js/heatmap-tool.js#L93)；H2 [tools.js density](../../frontend/js/ai_qa/tools.js#L1121) 未传 analysis/rampKey；R1 [SKILL_DEFS.rank:40](../../frontend/js/ai_qa/stages.js#L40) 默认 `by:'polarity'` 非有效值。⚠️ P1 = P1a density prompt 参数名漂移（bandwidth_m/cell_size_m/value_col vs radius/cell_size/weightField）；P1b [_PARAM_ALIAS:12](../../frontend/js/ai_qa/stages.js#L12) 全局 radius→radius_m 误伤 density；P1c compare_regions 不在 prompt；P1d/e/f 多工具缺 agg_cols/layer/as·keep。⚠️ P2 = 触发词缺「热力图」+ 高级参数无 AI 通道。

一句话：**Smart Agent 想得对，Dumb Tool 做不到——不是 Tool 不够 Dumb，是参数契约不够完整**（非架构问题，是接口完整性问题）。

### ② 我方反评价（verify-before-accept · 逐条核实）

| # | SCAN 条目 | 判定 | 核实/行动 |
|---|---|---|---|
| H1 | ForAI 硬编码 rainbow | **agree** | 核实；ForAI 加 analysis 复用 computeStyle |
| H2 | density 未传 analysis | **agree** | density 补 polarity→analysis 映射 |
| R1 | rank by:'polarity' 无效 | **agree** | 核实 [rank-tool.js:16](../../frontend/js/toolbox/rank-tool.js#L16)+[geo_routes.py:376](../../api/geo_routes.py#L376)；默认改 worst |
| P1a | density prompt 参数名漂移 | **agree** | contracts 对齐 |
| P1b | _PARAM_ALIAS 误伤 density | **agree** | 核实 [harness.js:292](../../frontend/js/ai_qa/harness.js#L292) 确调 normalizeParams；改按工具区分别名 |
| P1c | compare_regions 缺 prompt | **agree** | 核实；补 |
| P1d/e/f | 多工具参数缺口 | **agree** | 并入 L3 四步法 |
| P2a | 触发词缺热力图 | **agree** | L3 补 |
| P2d | 高级参数无 AI 通道 | **partial** | 按最高纪律先核查参数面板；PANEL_MISSING→提醒开发者补 |
| Phase 0 density 止血 | **agree** | 采纳并修正：analysis（色板）+ polarity（筛选）双维度 |
| Phase 1 手动补三处 | **agree（路径调）** | 走 `tool_contracts.py` 单一源（用户定） |
| Phase 3 validate 脚本 | **agree** | 并入 L2 guard |
| Phase 3 AGENTS 铁律 11 | **agree** | 落为最高纪律第 2 条 |

**CB-04: 13 agree / 0 disagree / 1 partial — pytest 待 L1 后跑 — 待 push**

**disagree: 0**。本轮 SCAN 质量极高（14 入口全审 + 行号对比表 + 根因链），KNOWLEDGE §3 老毛病（文档当运行时/完成度偏高/sim 当风险）一个没犯，反补我漏掉的 R1/P1b 两真 bug。

### ③ 行动（plan 融合定稿 → L1 实现）

plan 据 SCAN 融合（用户批准）：**L1 止血** density 双维度（analysis 色板 + polarity 筛选，修正原"纯 polarity"）+ R1 by worst + P1b alias 按工具区分 + P1c compare 入 prompt；**L2 治本** 新建 `ai_qa/tool_contracts.py` 单一权威源 + prompt/SKILL_DEFS 派生 + 并入 SCAN `tests/validate_skill_params.py`；**L3 全扫** 13 工具四步法（独立轮次）；**最高纪律**（用户指示 + SCAN 铁律）EMC 分析图严格复用 Toolbox 参数面板、ForAI=dialog 镜像、PANEL_MISSING 提醒开发者补 → 入 memory/CLAUDE.md/AGENTS.md。

### ④ 新发现 + 状态

- **契约分裂模式**（新 learning → KNOWLEDGE §2）：density 参数契约在 [prompts.py:85](../../ai_qa/prompts.py#L85) / [paradigm GEO_TOOL_CATALOG:289](../../ai_qa/paradigm.py#L289) / [TEMPLATE_REGISTRY:329](../../ai_qa/paradigm.py#L329) / SKILL_DEFS+TOOLS **四处各写一份且不一致**——"参数加在哪、加几次"失控的系统性坑（同类 [[emc-aggregate-column-alias-silent-zero]]）。治本 = 单一源 `tool_contracts.py` + 派生 + 校验。
- **SCAN 高质量范式**（正例，不入 §3）：本轮零 decline——扎实代码级审计，不犯老毛病。双模型闭环再现：我诊断覆盖 H1/H2/P1a，SCAN 全审补 R1/P1b/P1c + 14 入口系统化。**多模型 = 视角正交覆盖盲区**（同 CB-CPD-03 H1 之训）。

### 状态
`open → L1 实现中` —— plan 融合定稿（13 agree/0 disagree/1 partial）。L1 density 止血 + R1/P1b/P1c 紧急修进行中；L2 contracts + L3 全扫待续。双模型闭环：L1 落地后可触发下一轮 SCAN 对比验证（density 极性图 + rank by 回归）。

---

## CB-CPD-03 · 2026-07-22（DeepSeek + K3 双模型第三轮 · 稳定化验证 → 收敛定稿）

> 评审对象：`docs/cpd-core-plan.md` **v0.4**。基线 v0.3→v0.4。报告：[DeepSeek](SCAN_CPDPlan_03-deepseek.md) / [K3](SCAN_CPDPlan_03-k3.md)。**本轮 = CB-CPD 专轨收尾轮**（用户授权此轮收敛）。

### ① SCAN 摘要（双模型）

**DS 综合 A-**（v0.3 B+→A-）：CB-CPD-02 5/7 修复（R2/R5 超越）。v0.4 核心贡献：消除循环 import（依赖注入）+ 流式优先级修正 + 色名同步 + S4 动态变量降级。**v0.4 是第一个所有架构决策自洽的版本**（映射 key/信号源/exit 词表/载荷/init/优先级全收敛）。**建议 CB-CPD 专轨在此轮收尾**，进 P0。残留 1 条（streaming 行物理位置歧义，G1 实现按文字优先级即可）。

**K3 综合 A-**（上轮 B+）：CB-CPD-02 9/9 属实。**但本轮组合推演发现 1 个 v0.4 新引入的高优链式缺陷 H1**（general 断链）+ M1（hasAnalysis 死信号）+ M2（hasVisibleEmotionLayer 不判情绪性）。agree v0.4 整体收敛，**H1 G1 动手前必修**（两行代码级）；M1 建议 interpret 行；M2 谓词收紧。K3："修 H1/M2/M1 后预期末轮 A 级收敛"。

**分歧**：DS 说收尾（v0.4 稳定无阻塞）；K3 发现 H1（真 bug 静默冻结）→ 须先修 H1 再收敛。**项目方立场：修 K3 H1/M1/M2/L1 后此轮收敛**（用户授权），不再开 CB-CPD-04。

### ② 我方反评价（主线程，H1 已核实 [panel.js:1161/1162/1181](frontend/js/ai_qa/panel.js#L1161) 链）

| # | 条目 | 来源 | 判定 | 证据/采纳 |
|---|---|---|---|---|
| 1 | H1 general 断链（v0.4 新引入） | K3 H1 | **agree** | 已核实：general 短路（[harness.js:372/412](frontend/js/ai_qa/harness.js#L372)）无 exit → v0.4 守卫 `exit!==undefined` 不 dispatch，但 general 轮 `settled=true` 照常 push（panel.js:1181）致 `_history` 跳号 → 严格 turnId+1 去重丢事件 → 引擎**永久冻结（静默）**。改：守卫 `settled` + 去重单调递增 + `exit??null` + 真值表 lastExit∈{null} |
| 2 | M1 hasAnalysis 死信号 → interpret 分支 | K3 M1 | **agree** | §4.1 定义但真值表零引用 → row 4 `hasAnalysis=true` 升级 interpret（dock 产图桥回 EMC） |
| 3 | M2 hasVisibleEmotionLayer 不判情绪性 | K3 M2 | **agree** | v0.4 "非 group 非 range" 对无情绪层撒谎"点击深绿/深橙"（演示链第一环断点）→ 谓词收紧 +判情绪性 |
| 4 | L1 U8 措辞（#dock 不存在） | K3 L1 | **agree** | 全前端无 #dock（统一 openParamPanel）→ U8 改 `#param-panel.is-open` 同步谓词（无需 observer） |
| 5 | DS streaming 行物理位置歧义 | DS | **partial** | G1 实现按文字优先级（streaming 第一），无需改 plan |
| 6 | L2 #ff9000 token | K3 L2 | **partial** | G3 实现期确认是否 token 化 |
| 7 | R6 range 文案 / S4 远期扩展 | DS | **partial** | G3 实施细节 |

**disagree：0**。两份均未撞红线。本轮关键 = K3 H1（DS 未发现的静默冻结路径），已核实必修。

### ③ 行动（plan v0.4 → **v1.0 定稿**，本轮 commit，CB-CPD 专轨收尾）

修订 cpd-core-plan.md → **v1.0 定稿**：
- §4.3 H1 修复：dispatch 守卫 `exit!==undefined`→**`settled`** + 去重"严格+1"→**单调递增** + `exit??null` + intent 供 general 判定。
- §4.2 row 4：lastExit∈{null,undefined,general}（null 含 general 短路）+ `hasAnalysis=true` 升级 interpret 分支（M1）。
- §4.1：hasVisibleEmotionLayer 谓词收紧 +判情绪性（M2）；hasAnalysis 标注 interpret 用。
- §十一 U8 措辞改 `#param-panel.is-open` 同步谓词（L1）。
- **新增定稿声明**（§十一后）：核心 6 决策自洽 + 三轮链式缺陷全修 + CB-CPD 收尾 + 下一步 roadmap。

不动代码（review.py/前端/tests 留 P0-P2）。

### ④ 新发现 + 收敛声明

- **双模型互补的极限案例**：CB-CPD-03 DS（产品视角，说稳定收尾）vs K3（代码推演，发现 H1 静默冻结）——DS 漏 H1 因其偏架构/演示视角；K3 靠组合推演（general×守卫×去重×push）挖出。**多模型价值 = 视角正交覆盖盲区**。H1 是"修订动作引入新缺陷"模式的第 3 次（CB-CPD-01 spec 错误 / CB-CPD-02 循环 import / CB-CPD-03 general 断链）——启示：每次修 plan 要自检组合场景（尤其事件+状态机+去重咬合）。
- **H1 静默失败的危险性**：引导引擎永久冻结但零报错——若非 K3 推演发现，G1 实施后会以"引导偶尔不工作"的玄学 bug 出现。`settled` 守卫 + 单调去重是正确解（覆盖所有正常完成轮 + 免疫跳号）。
- **收敛达成**：核心 6 架构决策全自洽（DS §2.1 表），三轮链式缺陷全修，演示表现力 C+→B+，承重零触。剩余 U8-U10/R6/streaming 行/L2 = G1-G3 实施细节。**CB-CPD 专轨收尾**（DS 建议 + K3"修后末轮 A 级" + 用户授权）。v1.0 进 P0/G1。

### 状态
`CB-CPD 专轨收尾 · v1.0 定稿` —— plan v0.4→**v1.0**（修 K3 H1 断链 + M1 interpret + M2 谓词 + L1 措辞）。反评价 7 条（agree 4 / partial 3 / disagree 0）。H1 已核实。**CB-CPD-01/02/03 三轮闭环**（v0.1→v1.0，核心决策全收敛）。**进 P0 测试铺底 → P1 尺度诚实 → P2 引擎 G1-G4**。若实施中发现 plan 层新问题，再开 CB-CPD-04。

---

## CB-CPD-02 · 2026-07-22（DeepSeek + K3 双模型第二轮验证评审）

> 评审对象：`docs/cpd-core-plan.md` **v0.3**。基线 v0.2→v0.3。报告：[DeepSeek](SCAN_CPDPlan_02-deepseek.md) / [K3](SCAN_CPDPlan_02-k3.md)。两份独立评审（K3 未读 DS 全文，重合发现 = 收敛信号）。

### ① SCAN 摘要（双模型）

**DS 综合 B+**（v0.2 B-，↑1.5 级）：六维 架构 A- / 功能 A- / 承重 A- / 演示表现力 B-（C+→B-）/ 分阶段 B+ / 风险 B+。**CB-CPD-01 12/12 全部核实通过**；特征向量真值表根治 S0/S1 不可达；回退"同表重算"比 `_lastCur` 更优雅。演示升至 B-（文案叙事化 + S3 空间交互 + S4 地图闭合），尚未到"诊断叙事完整体"（S4 动态变量 + 三端同步未落地）。v0.3 可进 P0。

**K3 综合 B+**（与 DS 独立收敛）：**CB-CPD-01 15/15 执行或合理处置**，2 处修法超建议（exit-badge 免疫流式 / 同表重算无状态腐烂）。**v0.3 新增内容自身引入 2 高优**（均不在 v0.2，修订动作产生）：H1 init 循环 import / H2 S4 动态变量无源；3 中优（M1 色名脱节 / M2 真值表组合 / M3 优先级文字矛盾）。agree v0.3 可进 P0，H1/H2 G1 动手前必修。

**两份独立收敛（高置信）**：① init 模块边界（v0.3 "只读 getter" 致循环 import → 依赖注入）；② S4 文案动态变量客户端无源（X×Y/N → 降级 {区域名}）。

### ② 我方反评价（主线程，M1 色板已 grep 核实 tokens.css:28-29）

| # | 条目 | 来源 | 判定 | 证据/采纳 |
|---|---|---|---|---|
| 1 | init 循环 import → 依赖注入 | DS R2+K3 H1 | **agree** | v0.3 "导出 getter" 致 panel.js↔cpd-guide.js 循环 → 改 panel.js→cpd-guide.js 单向（init 注入 getter），cpd-guide.js 零 import panel.js |
| 2 | S4 动态变量无源 → 降级 | DS R1+K3 H2 | **agree** | X×Y/N 非确定性（正则抠违背用例 2 反模式）→ 「{区域名}的归因已就绪」（复用 _followUps:455） |
| 3 | M1 色名脱节 | K3 M1 | **agree** | 已核实 tokens.css:28-29（very-negative #D85A30 深珊瑚橙、very-positive #0F6E56 深青绿，**无"深红"**）→ 文案"深红"改"深橙"；色名从 theme var 派生（铁律） |
| 4 | M3 优先级文字矛盾 | K3 M3 | **agree** | v0.3 文字"hasImport 优先→streaming"致无数据+流式首匹 import → 改 streaming 第一优先 |
| 5 | M2 hasRange=false+result 组合 | K3 M2 | **agree** | range 引导兼带深读/导出次 CTA（避免演示高潮断档） |
| 6 | L1 init 重置 expectedTurnId | K3 L1 | **agree** | 切会话/clearChat 致 _history.length 回退断链 |
| 7 | R3 hasImport 谓词注释 | DS R3 | **agree** | G1 实现注释列出排除来源（inspect_zone focus marker 等） |
| 8 | R4 S3 实现路径明确 | DS R4 | **agree** | G1=被动文案 / G3=地图高亮三端同步 #ff9000 |
| 9 | U8 改确定性信号 | DS R5+K3 L4 | **agree** | 弃"3 秒"魔数 → dock/param-panel is-open（复用 cpd-state.js:60-63） |
| 10 | L5 引导态不持久化明文 | K3 L5 | **agree** | §6.5 补一句（init 重算） |
| 11 | L3 纯 AI 层文案降级 | K3 L3 | **agree** | §4.2 import 行注释（visEmotion=true 降级） |
| 12 | DS 2.2 layers 文案加 CTA | DS | **partial** | 方向 agree（"点深橙格子我告诉你为什么"）；G1/G2 打磨 |
| 13 | R6/L2 range 导入中文案 | DS R6/K3 L2 | **partial** | G3 边界低优 |
| 14 | turnId 去重价值有限 | K3 L1 | **partial** | 保留（无害），补 #6 expectedTurnId 重置 |

**disagree：0**。两份均未撞红线；新增建议皆有 file:line 证据，且两份独立收敛（init/S4）= 高置信。

### ③ 行动（plan v0.3 → v0.4，本轮 commit）

修订 cpd-core-plan.md 11 点（详见 v0.4 头部变更）：
- §4.2 真值表：色名深红→深橙（M1）+ S4 文案降级 {区域名}（H2）+ 优先级 streaming 第一（M3）+ range+result 兼带次 CTA（M2）+ import 纯 AI 层注释（L3）+ 色名铁律 + S4 动态变量来源说明。
- §4.3 init 改依赖注入（H1）+ 重置 expectedTurnId（L1）。
- §4.1 hasImport 谓词注释（R3）。
- §6.4 S3 路径（R4）+ 色名；§6.5 引导态不持久化（L5）。
- §九 panel.js/cpd-guide.js 行（getter→注入）。
- U8 改 is-open。

不动代码（review.py/前端/tests 留 P0-P2）。

### ④ 新发现

- **双模型独立收敛 = 高置信信号**：CB-CPD-01（init 数据源/exit 词表）+ CB-CPD-02（init 循环 import/S4 动态变量）两轮均有"两份独立得出相同结论"——收敛点应优先处理。双模型比单模型更可靠（DS 指产品方向，K3 定代码落点）。
- **修订动作产生新问题（v0.3→v0.4 教训）**：v0.3 修 v0.2 的 3 spec 错误时引入 2 新高优（init getter 致循环 import / S4 文案用了无源变量）——修订本身的回归。本轮修掉。启示：修 plan 时新方案要自检"是否引入新依赖/无源变量"。
- **色名同步色带（M1）是"视野↔结论同步"在文案层的体现**：文案属结论端，色名须与视野端渲染（theme var 端点）同色——演示逻辑链同步铁律的细化。
- **v0.3/v0.4 可进 P0（两份共识）**：H1/H2 不阻塞 P0 测试铺底，只阻塞 G1 编码。P0（地基行为测试）可与 CB 并行启动。

### 状态
`本轮反评价完成` —— plan v0.3→**v0.4**（11 点修订，吸收两份收敛 + 11 agree + 3 partial，disagree 0）。M1 色板已核实。**待 CB-CPD-03**：验证 v0.4 修订落地（H1 依赖注入 / H2 S4 降级 / M1 色名 / M3 优先级）+ 是否达"连续 2 轮无新实质分歧"定稿条件。**v0.3/v0.4 可进 P0 测试铺底**（与 CB 并行）。

---

## CB-CPD-01 · 2026-07-22（CPD 专轨 · DeepSeek + K3 双模型首评）

> 专轨定义见 `docs/cpd-core-plan-review.md`。评审对象：`docs/cpd-core-plan.md` **v0.2**（单份 plan，非全项目）。
> 评审模型：DeepSeek V4 Pro + K3（均自读项目文件 + 承重实证）。报告：[DeepSeek](SCAN_CPDPlan_01-deepseek.md) / [K3](SCAN_CPDPlan_01-k3.md)。

### ① SCAN 摘要（双模型）

**DeepSeek（综合 B-）**：六维——架构 B+ / 功能 B / 承重 B+ / **演示表现力 C+（最大短板）** / 分阶段 B / 风险 C+。核心判断：CPD v0.2 是"功能教程"非"诊断叙事"；S3"问我想看什么"反模式（应引导点地图非打字）。阻塞 G1 的 4 硬伤（ask 漏态 / 状态回退 / localStorage 脏态 / turnId 未绑）+ 演示表现力 3 关键建议（文案叙事化 / S3 空间交互优先 / S4 融入宏观诊断信号）。

**K3（更精准，附大量 file:line）**：方向与承重纪律合格，无撞红线；但 §4 引导状态机是全 plan 最弱一节——**3 个 P0 spec 错误**（plan 对"已就绪地基"的事实陈述与代码不符）：
- P0-1 `.aiq-conclusion` **死信号**（cpd-state.js:29 查询，全前端无 JS 创建者）→ curState 永不到 S4。
- P0-2 exit 词表不匹配（plan 大写 RESULT/CONCEPT；harness 实际小写 `result/gap/partial/ask/drift`；general 短路无 exit；drift 缺席）。
- P0-3 映射表 key=curState 与 deriveState 矛盾（任何可见层→S2，S0/S1 不可达）。
K3 另指：光环硬编码 hex（ai_qa.css:431）违 theme var；交互环未闭合（U6 实质）；review desc 灰度缺口。附 U1-U7 立场表。

**共识**：ask→null、exit 读 `_curTrace.exit`、turn-ended 竞态（init 恢复）、curState 承重措辞、review desc 灰度、状态回退、流式读 `_streaming`、光环 theme-var、`_followUps` 优先级。
**分歧**：G1 独立 ship（DS 否·半成品 / K3 能·agree U2）→ v0.3 调和。

### ② 我方反评价（主线程，verify-before-accept 已 grep/read 核实 4 承重证据）

**4 承重核实（全部属实）**：`.aiq-conclusion` 死信号（全前端仅 cpd-state.js:29 + ai_qa.css:523，无 JS 创建）/ exit 小写词表（harness 272/292/307/476/568/608/620/644）/ curState 进 buildContext（tools.js:455-458）/ 光环硬编码 hex（ai_qa.css:431）。

| # | 条目 | 来源 | 判定 | 证据/采纳 |
|---|---|---|---|---|
| 1 | exit 词表大写错误 | K3 P0-2+DS | **agree** | 小写五值 ∪ undefined；CONCEPT 改判 intent/skipped（同 _followUps:478）；补 drift |
| 2 | .aiq-conclusion 死信号 | K3 P0-1 | **agree** | 改 .aiq-exit-badge（panel.js:378，免疫流式误推） |
| 3 | 映射 key=curState 矛盾 | K3 P0-3 | **agree** | 改特征向量真值表（deriveState S0/S1 不可达） |
| 4 | ask 漏态 | DS+K3 | **agree** | exit='ask'→null |
| 5 | turn-ended 数据源+竞态 | DS+K3 | **agree** | 读 _curTrace.exit + {exit,turnId,intent} + finally 守卫 + 引擎 init 恢复 |
| 6 | 状态回退 | DS+K3 | **agree** | 特征向量真值表覆盖（同表重算） |
| 7 | 流式误推 | DS+K3 | **agree** | 读 _streaming 硬门 + exit-badge 天然免疫 |
| 8 | curState 承重措辞错误 | DS+K3 | **agree** | 改"推导纯客户端，注入 buildContext 仅语境提示，不参与路由" |
| 9 | 光环硬编码 hex | K3 | **agree** | 抽 --emc-halo-* theme var（G2/G4） |
| 10 | review desc 灰度 | DS+K3 | **agree** | ≥10 条历史微观问题对比 fail 率，>30% 调话术 |
| 11 | U7 三态分级 | K3+DS | **agree** | fail/warn/pass（warn 不触发 revise 防飙升） |
| 12 | 引导 vs 追问胶囊冲突 | DS+K3 | **agree** | gap/partial/ask/drift 时引擎 null；banner 内视觉分组 |
| 13 | 谓词定义缺口 | K3 M5 | **agree** | hasImport 排除 AI 组/tool 产出；hasAnalysis=_ui.tool∈{grid,zonal,heatmap} |
| 14 | localStorage 脏态 | DS+K3 | **agree** | 引擎 init 检测有图层无历史→null+warn；引导态不持久化 |
| 15 | 交互环未闭合（U6） | K3 M3+DS | **agree** | S4·result 含 ref 时加"地图定位"CTA 闭合视野端 |
| 16 | S3 空间交互优先 | DS | **agree** | 文案"点地图深红/深绿"，对话作备选 |
| 17 | P0 用例顺序矛盾 | K3 L1 | **agree** | 引擎状态转移挪 G1（P0 引擎不存在） |
| 18 | G3 绿色摘要条未定义 | K3 L2 | **agree** | §六补（banner done 变体） |
| 19 | S4→S0 重置路径 | DS | **agree** | "换范围"CTA dispatch cpd:reset |
| 20 | review.py docstring 漂移 | K3 L5 | **agree** | "六条"→"七条"顺手修（P1） |
| 21 | 文案叙事化 | DS | **partial** | 方向 agree；具体文案 G1/G2 打磨，plan 立原则+示例 |
| 22 | G1 独立 ship（分歧） | DS否/K3能 | **partial·调和** | G1 独立 ship + 含光环 click 最小 CTA（DS 方案 A） |
| 23 | 光环改胶囊整体呼吸色 | DS | **partial** | G4 抛光期（先 theme-var 化） |
| 24 | 地图层引导浮层 | DS | **partial** | 另一子系统；先用 #15 轻量闭合，浮层列 U10 |
| 25 | 用户忙检测 | DS | **partial** | 列 U8（G3 边界） |
| 26 | engage 再亮兜底 | K3 | **partial** | 列 U9（观察项） |

**disagree：0**。两份均未撞承重红线，建议皆有 file:line 证据。

### ③ 行动（plan v0.2 → v0.3，本轮 commit）

修订 cpd-core-plan.md 九点（详见 v0.3 头部变更说明）：
- §4.1 信号源重写（exit-badge / 小写 exit / 谓词 / _streaming）。
- §4.2 特征向量真值表（key 从 curState 改特征向量；ask→null / drift→retry / 回退同表重算）。
- §4.3 调度强化（turn-ended {exit,turnId,intent} + finally 守卫 + init 恢复 + cpd:reset）。
- §七 curState 措辞修正 + 光环 theme-var 列入 §九。
- §八 P0 用例改地基行为 / G1 含光环可点 / G3 绿色摘要条补 §六。
- §配套 A 灰度 + U7 三态。
- §六 6.4 演示链服务（S3 空间优先 + S4 地图定位 CTA + 文案叙事化）。
- 新增 U8-U10。

不动代码（review.py / 前端 / tests 留待 P0-P2 实施）。

### ④ 新发现

- **双模型互补**：DeepSeek 强产品/演示视角（功能教程 vs 诊断叙事），K3 强代码级精准（file:line 实证 3 P0 spec 错误）。同轮双模型比单模型覆盖更全——DS 指方向，K3 定落点。**这是 CPD 专轨首次双模型，值得固化为主轨实践**（未来 SCAN_DeepSeek_{NN} 也允许多模型 `-{model}` 后缀）。
- **4 承重证据全部属实**：plan v0.2 对"已就绪地基"的 3 处事实陈述错误（死信号/词表/映射 key）+ 1 处措辞错误（curState），均 grep/read 核实。教训：写 plan 引用"已就绪"信号须核实生产者，勿信"已订阅"=存在。
- **G1 分歧调和**：DS（半成品不可独立 ship）与 K3（可独立 ship）不悖——G1 独立 ship 指不依赖 G2 banner，但 G1 本身含光环 click 最小 CTA（DS 方案 A）。两者并取。
- **演示表现力共识**：交互环闭合（S4 地图定位 CTA）= U6 实质解法——引导从"装载自动化"升"诊断叙事"，解除"为引导而引导"风险。这是本轮最大方向收益。

### 状态
`本轮反评价完成` —— plan v0.2→**v0.3**（九点修订，吸收 26 条建议：agree 20 / partial 6 / disagree 0）。4 承重证据已核实。**待 CB-CPD-02**：v0.3 喂第三方验证修订是否落地 + 演示表现力升维是否到位（尤其 S3 空间交互 / S4 地图定位 / 文案叙事化的具体落地）。

---

## CB-03 · 2026-07-19

### ① SCAN 摘要
本轮特殊：项目代码（core/api/ai_qa/frontend）零变化。焦点为 CB 流程自身的成熟度评估。综合 7.7/10（首次上升 +0.1：Harness 9.0→9.2 + 文档 7.5→7.8）。CB-02 全部 5 项 agree 行动验证通过；4 项 defer 理由充分。

**核心发现——CB 自动化基础设施**：5 组件全 A 评级——`/cb` command（9 步流水线，45 行）、Hook CB detector（零 LLM 调用，27 行）、KNOWLEDGE.md（5 章节跨轮知识库，71 行）、记忆共享通则（context-map.md + CLAUDE.md）、路径归档（cb-journal/retired 移入 catch-ball/）。这是从"手动 ad-hoc"到"工程化流程"的关键跃迁。

**CB-02 反评价质量**：较 CB-01 显著提升。agree 5/5 兑现，decline/defer 理由全部充分。KNOWLEDGE.md 将 CB-02 的误判（generate_test_data ≠ 功能重叠）提炼为 §3 新模式。

**新建议（6 条）**：3 高（KNOWLEDGE vs RULES 边界 + auto-check 可配置化 + 回归功能开发）、2 中（geo_registry 埋点重申 + 文档过时重申）、1 低（trace-digest cursor 根因分析）。

**关键讨论点**：CB 自动化 ROI（当前投入合理，建议 CB-05 正式评估）/ KNOWLEDGE.md pruning 策略（预设触发条件）/ 项目阶段信号（质量巩固期应结束，CB 进入低频维护模式，每 5-10 个功能 commit 一次 SCAN）/ 双模型闭环三轮回望（4/5 目标成熟）。

### ② 我方反评价（/cb 03，2026-07-19）

**6 条建议**（verify-before-accept 已核；建议5 已核 on_session_end.py）：

| # | CB-03 建议 | 判定 | 证据/行动 |
|---|-----------|------|---------|
| 1 | KNOWLEDGE vs RULES 承重边界（重复） | **agree** | 真重复（RULES §3.3 + KNOWLEDGE §1 同 6 红线）→ 撞记忆共享通则"单一权威源"。RULES §3.3 → pointer to KNOWLEDGE §1（保留摘要 + 指针） |
| 2 | /cb auto-check 可配置清单（硬编码） | **agree** | step 5 硬编码 4 检查 → 数据驱动。KNOWLEDGE 加 §6 Auto-Check 清单 + /cb step 5 改"加载 §6" |
| 3 | geo_registry 埋点（重申） | **defer** | 守编号连续·独立任务（未变）；下个功能 sprint |
| 4 | 文档 Streamlit 过时（重申·2 轮） | **defer·提升优先级** | 下个文档维护日首项 |
| 5 | trace-digest cursor 根因（SCAN 深化） | **agree·更正 CB-02** | 已核 on_session_end.py：cursor 缺失 fallback `last_read=0`（L29-35）+ `if not errs: return`（L47）→ **空 digest = trace.log 无 ERR/WARN（健康）或 trace.log 不存在（fresh env），非 bug**。CB-02"cursor 缺失=疑似 bug"partial 被闭环深化更正 |
| 6 | panel.js 拆分（重申） | **defer** | JS 单测后（时间轴会话之后） |

**4 讨论点**：

| 讨论 | 立场 | 行动 |
|------|------|------|
| 1 CB 自动化 ROI | **agree**（当前合理） | CB-05 正式 ROI 评估（总投入 vs 实际修复/避免回归） |
| 2 KNOWLEDGE pruning | **agree** | KNOWLEDGE 加 pruning 触发（§3>15/§5>10/file>200 归档） |
| 3 CB 节奏高频→低频 | **强 agree** | KNOWLEDGE 加节奏决议；**本计划即践行**（CB 收尾后转时间轴，CB 低频，每 5-10 commit 一次 SCAN） |
| 4 "SCAN 先确认运行时假设" | **agree·PROPOSE** | 给第三方 CB-04 RULES 修订（加 SCAN 前置步骤：读 KNOWLEDGE §2 + 确认运行时）；不擅改 RULES 方法论 |

### ③ 行动（已执行）

- [x] 建议1：RULES §3.3 承重 → pointer to KNOWLEDGE §1（保留摘要 + 指针，单一权威源）。
- [x] 建议2：KNOWLEDGE 加 §6 Auto-Check 清单 + /cb step 5 改"加载 §6"。
- [x] 讨论2：KNOWLEDGE 加 pruning 触发条件。
- [x] 讨论3：KNOWLEDGE 加 CB 节奏决议（高频→低频维护）。
- [x] 建议5：本 journal 记 trace-digest 闭环更正（CB-02 partial → CB-03 确认健康；无代码改）。

**defer**：建议3（geo_registry 埋点·下个 sprint）/ 建议4（文档 Streamlit·下个文档日）/ 建议6（panel.js·JS 单测后）。
**PROPOSE 给第三方 CB-04**：讨论1（CB-05 ROI）/ 讨论4（RULES 加 SCAN 前置步骤）。

### ④ 新发现

- CB 自动化 5 组件在 ~30 小时内从 0 到完整系统——工程化能力的体现。
- 三轮 CB 累计退役 6 文件（-2,257 行）、修复 7 个问题（geo_routes 冗余×3 + 路径 case + 依赖僵尸 + AGENTS 漂移 + settings 权限）。
- **KNOWLEDGE.md 的"跨轮学习积累"是三轮 CB 最有价值的架构创新**——每轮新 learning 入库，未来 CB-N 自动避免重犯前 N-1 轮错误。
- **trace-digest 闭环深化**：CB-02 标"cursor 缺失=疑似 bug"，CB-03 核代码后确认"cursor 缺失有 fallback，空 digest=健康"——双模型闭环的"发现→深化→更正"价值兑现。

### 状态
`closed`（CB-03 反评价完成）—— 4 agree 已 act（RULES pointer / KNOWLEDGE §6·pruning·cadence / /cb step5 / trace-digest 更正）；3 defer + 2 PROPOSE 给 CB-04。CB 转低频维护模式（每 5-10 功能 commit 一次 SCAN）。**下一会话推进极性深读时间轴**（T1→T3 演进）。

---

## CB-02 · 2026-07-19

### ① SCAN 摘要
3 个 Explore Agent + 主线程核实，覆盖 ~200 文件 / ~51,000 行。综合 7.6/10（架构 8.5 / 代码 7.5 / 测试 6.0 / Harness 9.0 / 文档 7.5 / 调用效率 7.0）。CB-01 10 条建议：✅ 2 完成 / ❌ 4 拒绝（其中 2 条因 CB-01 描述失准或撞红线）/ ⬜ 3 待处理 / 1 部分。CB-01 退役清理验证通过（5 文件已删，-1,735 行），geo_routes 修复生效，sim agent 已注册，e2e seam 正确分离。

**CB-02 新发现**：requirements.txt 残留 streamlit+pydeck 僵尸依赖；range_selector.py 路径大小写不一致（Linux 部署会 break）；AGENTS.md 声称 8 Agent 但实际 9；geo_registry.py 零 @track；prd/spec/architecture 含过时 Streamlit 内容；trace-digest.md 空；panel.js 2,098 行过大。新增 10 条建议（3 高 / 3 中 / 4 低）。

**CB-01 反评价第三方审核**：agree 4 条全部核实通过；disagree 4 条中 3 条反驳成立、1 条部分成立（数据管道完成度 90% 确实偏高但 75% 也偏保守→建议折中 80%）；partial 1 条平衡立场。

**关键讨论点**：AGENTS.md 定位（概念框架 vs 运行时契约）、topo_scanner 自文档化意义、E2E 策略困境（先 JS 单测再 browser）、双模型闭环首次验证（有价值但需改进——SCAN 应先确认运行时假设）。

### ② 我方反评价（/cb 02，2026-07-19）

**10 条建议**（verify-before-accept 已核代码级指控）：

| # | SCAN 建议 | 判定 | 证据/行动 | decline reason |
|---|-----------|------|---------|----------------|
| 1 | requirements 僵尸依赖 | **agree** | grep 零活 import 核；删 streamlit==1.58.0 + pydeck | — |
| 2 | range_selector 路径大小写 | **agree** | L21 `'data','boundaries'` 小写确认（Linux 部署 bug）；→ `'DATA'` | — |
| 3 | AGENTS.md 8→9 同步 | **agree** | settings.json 9 agent 核；AGENTS.md 标题+表+sim 行更新 | — |
| 4 | 冗余 sim 脚本退役 | **partial** | `generate_l1_mock` 退役（自标 superseded + 零活引用）；**`generate_test_data` 保留** | **事实错误**：test_data 是 L0 raw（10 万条全管线测试），与 sim_performance_data（L1/L2 demo）用途不同，非冗余 |
| 5 | geo_registry 补埋点 | **agree-defer** | 0 @track / 7 函数确认；守编号连续，独立任务（非 /cb 批次） | — |
| 6 | 文档 Streamlit 过时内容 | **agree-defer** | 多 doc 清理，非紧迫 | — |
| 7 | dev-notes 更新 | **agree-defer** | doc 工作，低优先 | — |
| 8 | trace-digest 空诊断 | **partial** | cursor `.claude/.trace-digest-cursor` **不存在**（hook 可能因此跳过追加）；诊断 defer | — |
| 9 | Bash(streamlit) 权限清理 | **agree** | settings.json allow 删 `Bash(streamlit *)` | — |
| 10 | panel.js 拆分 | **defer** | 技术债预防；前端 JS 单测（头号短板）更高优 | — |

**4 讨论点**：

| 讨论 | 判定 | 行动 |
|------|------|------|
| 1 AGENTS.md 定位（概念框架 vs 运行时） | **agree** | 加「概念框架声明」到 AGENTS.md 头部——免疫未来 SCAN 重犯 CB-01 错误（据理论 SOP 算调用次数） |
| 2 topo_scanner 自文档化扩展 | **discuss** | 远期（依赖健康度 / 追踪热力图 / 变更影响），不行动 |
| 3 E2E 策略困境 | **agree** | B 优先（JS 单测不依赖 browser）——已是项目 plan，无新行动 |
| 4 双模型闭环改进 | **agree** | RULES v2（CB-03 前）加"SCAN 先确认运行时假设"步骤 |

### ③ 行动（已执行）

**agree 快赢（已 act）**：
- [x] 建议1：requirements 删 streamlit+pydeck
- [x] 建议2：range_selector `'data'`→`'DATA'`（路径构造 + docstring）
- [x] 建议3：AGENTS.md 8→9（标题 + Agent 清单 + sim 行）
- [x] 建议9：settings.json 删 `Bash(streamlit *)` 权限
- [x] 讨论1：AGENTS.md 加「概念框架声明」
- [x] 建议4 部分：`generate_l1_mock.py` 退役（retired.md 留痕）；`generate_test_data.py` 保留（declined·事实错误）

**defer（已登记，非本轮）**：建议5（geo_registry 埋点·守编号连续）/ 建议6（文档 Streamlit 过时）/ 建议7（dev-notes）/ 建议8（trace-digest cursor 诊断）/ 建议10（panel.js 拆分）。

**验证**：`pytest tests/ -q` → **207 passed**（CB-02 行动零回归）+ 2 geocode offline tests fail（admin fresh-env：network/key 依赖，**非 CB-02 回归**；类比 h3 缺失——admin 需 `pip install -r requirements.txt` 补全；h3 已 pip install 补）。

### ④ 新发现

- CB-01 与 CB-02 之间，项目方自行发现并修复的项目（未在 CB-01 建议中）：map_engine.py pydeck 僵尸退役、zonal_stats latent bug → wontfix（深挖 3 条消费路径）、db.py 退役（已是 executemany → SCAN 描述失准）。
- **新 SCAN 标尺纠正模式（入 KNOWLEDGE §3）**：SCAN 把不同用途的 sim/工具脚本误判"功能重叠"（generate_test_data = L0 raw 全管线测试 vs sim_performance_data = L1/L2 demo）→ verify-before-accept 须查 docstring 定用途，勿轻信"重叠"。
- **跨环境 env-gap**（admin fresh-env）：h3 声明未装（pip 补）；2 geocode offline 测试 network/key 依赖失败。换环境须 `pip install -r requirements.txt` + 核 network 测试。

### 状态
`closed`（CB-02 反评价 + 行动完成）—— 5 agree 快赢已 act + generate_l1_mock 退役；5 项 defer 已登记。pytest 207 绿（2 geocode offline env-fail 非回归）。**待**：CB-03（DeepSeek 三次扫描对比验证 CB-02 改进）+ defer 项择机。本轮新 learning 已入 KNOWLEDGE §3。

---

## CB-01 · 2026-07-18（首轮）

### ① SCAN 摘要
4 个 Explore agent 扫描 ~100 文件。总评 7.6/10（架构 8.5 / 代码 7.5 / 测试 6.5 / Harness 9 / 文档 8 / 调用效率 6）。头号高优建议=调用次数优化（合并 Reviewer+Tester、批量变更、本地脚本替代 spawn、MANIFESTO 分层）。关键发现：core/ui_components+layer_registry 是 Streamlit 僵尸 / geo_routes 冗余计算 / db.py iterrows / sim agent 未注册 / Skills 落地率低 / 前端无单测。

### ② 我方反评价
**agree（采纳，已验证）**：
- Streamlit 僵尸——ui_components(835 行/29 streamlit)+layer_registry(3 st.)+**map_engine(pydeck，SCAN 未点名但同类)** 全部零活引用已核（core/__init__.py 仅 docstring 文字，活代码无 import）。删除安全。
- geo_routes 冗余——逐行核实，且发现比 SCAN 更深的问题（见 ④）。
- sim agent 未注册 settings.json——已核（仅 8 agent）。
- db.py iterrows perf、Skills 落地率、前端无单测、微服务化否决——均合理。

**disagree（用错标尺，反驳）**：
1. "数据管道 90%、L0-L4 全部实现"=**事实错误**。L1 治理从未在真实 key 实跑；SCRIPT 层 L3/L4 是 ⬜ 预留（SCAN 自身 §2.6.2 又说 9 模块⬜，自相矛盾）。归因靠 EMC 分析时 + Sim。真实 ~75%。**且 L0 未来走购买途径，sim 充分非风险**（用户澄清，memory `l0-acquisition-purchase-strategy`）。
2. "调用次数优化=头号高优"=**前提不成立**。项目跑在用户全局"不派 subagent"规则下，AGENTS.md 8 Agent 是概念框架，主线程直接干。SCAN 假设的"标准 SOP=7 spawns"是理论值非实际——解一个已基本解决的问题。
3. "MANIFESTO 分层减 token"=**撞承重红线**（diagnose 永不动保 Flash eval）。不采纳。
4. "MCP 应与 DeepSeek 匹配"=**provider-neutral 错标尺**。智谱优先因国内视觉/搜索质量，与主 LLM 厂商无关。（但 vendor SLA 单点论部分认同。）

**partial**：追踪 ROI 测量——同意做实验（30 天 trace.log 触发统计），**不同意预设简化**（编号连续是 rule 10 红线，追踪是 LLM 调试 O(1) 利器）。

**SCAN 漏掉（我补）**：§0 任务树漂移 3 周 / retired.md 缺失 / Toolbox 多维归因 ⬜ vs EMC deep_attribution ✅ 重叠 / `?e2e=1` seam 去生产化。

### ③ 行动
**已执行（本轮 commit）**：
- [x] memory `l0-acquisition-purchase-strategy` 写入（防再误判）
- [x] Tier 0.3 sim-emotion-data agent 注册 settings.json
- [x] Tier 0.2 geo_routes.py 三处清理（zonal_stats 死循环+冗余 / rank 双调用 / nearest 死三元）—— 零行为变化

**待执行（部分已做）**：
- [x] **Tier 0.1 删 3 僵尸** + .streamlit/config.toml —— commit `5e7b8c6`（用户"继续推进"授权后分类器放行；-1439 行；retired.md 留痕）
- [x] **入库** `.zcode/`（ZCode 工具状态·双环境同步）+ `docs/SCAN_DeepSeek.md`（CB 输入历史）—— commit `5e7b8c6`
- [x] Tier 1 部分：§0 树主干 refresh（七层/数据管道/Harness/底图）/ retired.md / tracking-progress 对账（改指 AGENTS.md 权威源，修 frozen-0613 漂移）
- [x] Tier 1 余（部分）：§0 分支补 topology ✅（5.134）/ `?e2e=1` 去生产化 ✅（5.134，main.js 零 test 代码→独立 e2e-seam.js + index.html 条件 dynamic-import；ESM 绿，browser 验证因环境挂延后）
- [ ] Tier 1 余：C6 补 3
- [ ] Tier 2：db.py 批量插 / 前端 JS 单测基建 / 9⬜ 埋点细化 / vendor 本地化核查
- [ ] zonal_stats latent bug 修（n_dom/n_elem 补充失效，需先确认消费方）

### ④ 新发现（SCAN 之外，清理中挖出 + 深挖定级）
- **zonal_stats latent bug → wontfix（无活消费方）**：原 discover 循环想补 `n_dom_*/n_elem_*` 到 zonal_stats 响应，遍历错源（rows.columns，而 _props_df 只返请求列）→ 补充从未生效。**深挖消费方**：`rank` 直读 gdf.columns（不经 _props_df）/ `panel.js` 矩阵 `_cellsByBucket` 读地图图层 `f.properties`（图层 GeoJSON 含完整 stats 列）—— **均不经 zonal_stats 的 trimmed 响应**，故无消费方读这两列。修复=向无人读的响应加列=死重 → **wontfix**（geo_routes 注释已标注）。
- **db.py 全闲置 → SCAN 建议7 declined**：`EmotionDB` 全仓零活引用、无 test_db（demo 走 GeoJSON 文件非 SQLite）。且 `insert_points` **早已用 executemany 批量插**（`iterrows()` 只用于构建记录列表做 col_map+NaN 过滤，非逐行 DB 插入）。SCAN 建议7 既优化死代码、又描述失准 → **declined**。db.py 去留（retire vs 留作未来购买数据 DB 预留）待用户定。

### 状态
`open` —— Tier 0 ✅（5.132-5.133）/ Tier 1 大部分 ✅（§0 refresh + ?e2e=1 去生产化 + retired.md + tracking-progress 对账，5.134）/ db.py 退役 + zonal_stats wontfix 闭环（5.135）。**待**：browser 环境恢复后复验 seam + C6 补 3；前端 JS 单测基建（头号短板）。双模型闭环：待 DeepSeek 二次扫描对比验证。

---


## CB-05（2026-07-28）· AUDIT_COMPREHENSIVE 全局审计反评价

### ① SCAN 摘要
- **SCAN**：[AUDIT_COMPREHENSIVE_2026-07-28](emc-arch-deepdive/AUDIT_COMPREHENSIVE_2026-07-28.md)（DeepSeek V4 Pro·35 文件 ~16,200 行 L1 逐行·七轴 7.9/10·↑+0.9 from v2 初始 7.0）
- 5 CRITICAL + 12 HIGH + 15 MEDIUM + 12 LOW·历史 Bug 修复率 87.5%（7/8）·v2→v3→v3.1 演进正面评价

### ② 反评价（逐条·grep/read 核实后判定）

| # | 等级 | SCAN 建议 | 判定 | 证据/行动 |
|:---:|:---:|------|:---:|------|
| CR1 | 🔴 | F_002 重复注册 | **agree** | llm.py:198+325 同 ID·**已修**→F_003/F_004 |
| CR2 | 🔴 | 裸 except 吞 CancelledError | **partial** | sync handler 不产 asyncio.CancelledError·**已修**（加 KeyboardInterrupt/SystemExit 前置） |
| CR3 | 🔴 | geocode 坐标转换静默失效 | **agree** | geocode.py:38 bare except 哑函数·**已修**（加 stderr 日志） |
| CR4 | 🔴 | SSE 代理断裂 | **decline** | serve.py 是开发服务器·非生产路径·FC 非流式可接受（**前提不成立**） |
| CR5 | 🔴 | buffer geometry/area 错位 | **agree** | buffer_analysis.py:56-59 长度不匹配·**已修**（buffered.notna() 过滤） |
| H1 | 🟠 | DEEPSEEK_MODEL env 覆盖 | **agree** | llm.py:279 全局 env 覆盖 provider model·**已修**（显式 model 不读 env） |
| H2 | 🟠 | MANIFESTO .format() 脆弱 | **agree** | 已知·**已修**（加 `# ⚠️ 禁止 .format()` 注释） |
| H3 | 🟠 | '热点' 触发词歧义 | **partial** | '热点'只在 hotspot·真正歧义是 **'聚集'**（density '聚集强度' substring）·**已修**（hotspot '聚集'→'聚集区'） |
| H4 | 🟠 | validate_tool_call 不校验 range | **agree** | _PARAM_RANGES 只在 Schema·validate 不查·**已修**（加 range clamp） |
| H5 | 🟠 | tracker ismethod 缺陷 | **agree** | inspect.ismethod 对非绑定返 False·**已修**（补 'self' 字面检测） |
| H6 | 🟠 | tracker 裸 @track 不检测 | **agree** | _has_track_decorator 只检 @track(...) ·**已修**（补裸 @track ast.Name 检测） |
| H7 | 🟠 | _free_port 暴力杀进程 | **partial** | 已有 netstat PID 过滤·非误杀（**已知设计取舍**） |
| H8 | 🟠 | .env 加载时序 | **partial** | geocode.py 有自己的 .env loader·但这是红线 #1（AMAP_KEY 兜底）·**不改** |
| H9 | 🟠 | aggregate DRY-debt | **decline** | 无消费方紧急性·backlog（**无消费方 wontfix**） |
| H10 | 🟠 | moran_i KNN 异常过宽 | **decline** | 预存·backlog（**无消费方 wontfix**） |
| H11 | 🟠 | stages.js 注释 45s→20s | **agree** | trivial·**已修** |
| H12 | 🟠 | extract_feature cards.fields bug | **agree** | getFieldCard 返平铺非 {fields:{}} ·**已修**（cards[_field]） |
| M7 | 🟡 | episode 静默失败 | **agree** | **已修**（加 stderr 日志） |

**汇总**：13 agree（已 act）/ 3 partial（部分修 or 不改·附理由）/ 3 decline（附 reason）/ 0 disagree

### ③ 行动
- **修复 13 项**（CR1/CR3/CR5 + H1/H2/H3/H4/H5/H6/H11/H12 + M7 + CR2）·涉及 8 文件。
- **decline 3 项**：CR4（serve.py 开发服务器·非生产）/ H7（已有 PID 过滤）/ H9+H10（backlog）。
- pytest **221 passed**+3 skipped 零回归。

### ④ 状态/新发现
- **SCAN 质量高**：35 文件逐行审计·证据充分（file:line 精确）·反评价核实无事实错误（H3 细节修正：'聚集' 非 '热点'）。
- **H8 .env 时序**：geocode.py 有独立 .env loader·这是**红线 #1 设计**（AMAP_KEY 必须兜底）·不改。
- **CR4 SSE 代理**：记录 backlog·生产部署用 nginx/uvicorn 直接·非 serve.py。
- **七轴 7.9/10**：从 v2 初始 7.0 提升 +0.9·主要来自 v3 C1/C2/C3 + v3.1 reg.filter 修复。

