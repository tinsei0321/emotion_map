# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

---

## 📅 2026-07-16

### ✅ EMC·区域对比 compare 技能 + _driftRe 拓宽（revision-log 5.114，commit 待 push）

实测欢迎胶囊"对比西陵伍家岗"犯三老毛病（代码块/回答一半/方法不做），选「彻底：加 compare 技能」。
- **compare 三件套**（复用 zonal_stats 不造端点，守红线）：
  - [paradigm.py](ai_qa/paradigm.py)：TEMPLATE_REGISTRY 加 compare（single/compare_regions/boundaries）；select_template C 分支 decision_type=对比→compare（优先于 rank/zonal）；决策树文本+_SINGLE_SKILL_IDS 同步。
  - [tools.js](frontend/js/ai_qa/tools.js)：`compare_regions`——boundaries（数组/分隔串，≤4 区）逐区 geoFetch('zonal_stats')，并排 observation+data.comparison；<2 区→引导 preset_id。
  - [stages.js](frontend/js/ai_qa/stages.js)：SKILL_DEFS 加 compare 镜像；normalizeParams 加 regions/areas→boundaries。
- **_driftRe 拓宽**（[harness.js:516](frontend/js/ai_qa/harness.js)）：草稿任意 ``` 围栏→_reviseOnce 重写 prose（治代码块泄漏，图表走内联 {chart}/{fig}）。
- **胶囊**：compare 就位后"区域对比"合法，不改文案。
- **验证**：pytest 34 pass（+2 compare 路由测试）；三 JS ESM .mjs 绿；**Flash eval 16/19=84% PASS**（3 MISS 全是 C6"里-class"边界老案例，与 compare 无关）。承重：diagnose 因技能目录变已重跑 eval≥80%；未碰 alias 站点/canonical 名/四态/visible-only。commit 只不 push。
- **待 browser 终验（C6，你肉眼）**：compare 胶囊→并排对比（不代码块/不半截/不拒）；_driftRe→非 action 代码块重写。

### ✅ 工作策略·上下文连贯园丁层（revision-log 5.113，commit 待 push）

用户要"先做工作策略优化（process/method）"，参考 OpenAI《Harness Engineering》。诊断：已有 7 机制=上下文树（对齐"地图非说明书"），缺园丁层。
- **除草**：`/garden` 命令（[garden.md](.claude/commands/garden.md)，按需扫过期 memory/巨型文件/漂移 manifest/僵尸注释，产清单不自动改）+ 阈值提醒（[on_session_start.py](.claude/hooks/on_session_start.py)：memory>50 或 revision-log>500KB 打印一行，零 LLM 开销）。
- **压缩前快照**：PreCompact hook（[on_precompact.py](.claude/hooks/on_precompact.py) → `memories/repo/.wip.md`，git/trace 锚点，gitignore）+ [settings.json](.claude/settings.json) 注册。
- **记忆树归档**：僵尸 `.claude/memory/` 10 文件 → `_archived/`（git mv）；[MEMORY.md](MEMORY.md) + [apps/CLAUDE.md](apps/CLAUDE.md) 重定向用户全局树（单一权威源）。
- **纪律固化**：全局 `~/.claude/CLAUDE.md` 加「Harness 工作方式·四纪律」+ memory `context-coherence-discipline`。
- **manifest 刷新**：[CLAUDE.md](CLAUDE.md)「13 模块 55+」→「18 模块 510+」+ rule 12 智谱栈全局托管说明；[AGENTS.md](AGENTS.md) 模块表加 5.x 主力备注。
- **可见地图**：新 [context-map.md](docs/context-map.md) + [harness-engineering-baseline.md](docs/harness-engineering-baseline.md)（六要素详表）。
- **验证**：settings.json JSON 合法；两 hook py_compile 过 + 实跑（session_start 阈值未触发零噪声 / precompact 写 .wip.md 成功）；全仓无残留 `.claude/memory/` 引用。承重：未动 EMC 承重代码。commit 只不 push。
- **下一步**：阶段二 EMC compare 技能根治（欢迎胶囊"对比"老毛病：代码块/回答一半/方法不做）。

### ✅ EMC ⑤② 遗留：拆 confidence role + score 别名化（revision-log 5.112，commit 待 push）

⑤② 遗留 + 修 design smell（l1_confidence 原归 score role）。
- **拆 role**（[field_dictionary.py](core/field_dictionary.py)+[.js](frontend/js/field_dictionary.js)）：score 只留情绪得分变体；新 `confidence` role（l1_confidence/置信度/...）。36 roles。
- **候选**（[prompts.py](ai_qa/prompts.py)）：user_roles 加 'confidence'。
- **import.js**（[:631](frontend/js/import.js#L631)）：scoreKey/confKey 分离（原 findKeyByRole('score') 找 confidence 是冲突源）；demo 零回归，score-only 层改正 needsAnalysis。
- **score 别名化**（[spatial_analysis.py](core/spatial_analysis.py)）：aggregate/hex/square_grid 数值 mean 按 role 解析（得分/评分/置信度/情绪强度），输出规范名；square_grid confidence→`l1_confidence_mean`（保 popup/state 契约）。hex 顺带修无 score KeyError。
- **验证**：承重 smoke——square_grid 去冲突（得分+置信度+情绪强度→三独立 mean）；规范名零回归；字典 36 roles 自检；EMC 32 pass；ESM 绿。承重：未碰 demo 数据/popup 契约名/colorMode UI。commit 只不 push。
- **⑤② 真收口**（polarity/domain/element/topic + score/ei/confidence 全 alias 化）。⑤ 剩 ⑤③ boundary_id 分组键 + ⑤④ execSkips 分桶（低优先）。

### ✅ EMC ⑤④ _missStats 遥测 + Flash 80% gate（revision-log 5.111，commit 待 push）

harness.js:354 注释提的「Flash 80% gate」原只有注释无逻辑（greenfield），补齐。
- **遥测**（[harness.js](frontend/js/ai_qa/harness.js)）：localStorage key `ai_qa_template_stats_v1={hits,misses}`（clearChat 不重置，跨会话累积）；diagnose 成功后 `_recordTplResult`（'unknown'→miss）；`getTemplateStats()` export。范式照 api.js getCallStats。
- **80% gate（self-protection）**：`_tplHitRateReady()` = 冷启动(samples<10)放行**保零回归**；成熟后 ≥80% 放行、<80%（Flash 经验证不可靠）退 while-loop。激活条件加 `&& _tplHitRateReady()`。比原注释「冷启动→while-loop」更安全（不改冷启动行为）；要原语义翻冷启动子句即可。
- **显示**（[panel.js](frontend/js/ai_qa/panel.js)）：footer 追加「Flash 模板 X/Y(Z%)」累积命中率。
- **验证**：ESM .mjs 过 node --check（harness+panel）；gate 阈值数学 7 case 全对。承重：未碰 trace 结构/持久化 schema/既有 runTemplatePath 出口；冷启动零回归。commit 只不 push。
- **⑤ 全收口**（②alias+④-conf+③popularity+④-_missStats/gate）。**待 browser 终验**：localStorage 累积 / footer 显示 / 冷启动零回归 / gate 退 while-loop。次要遥测（execSkips/lowConfField）未纳入（gate 仅需命中率）。

### ✅ EMC ⑤③ popularity 热度消费（revision-log 5.110，commit 待 push）

用户择「消费现有 role·category 优先」（不加新 popularity role）。
- [spatial_analysis.py](core/spatial_analysis.py) 新 `_attach_popularity_attrs` 共享 helper（与 `_attach_4x5_attrs` 并列），aggregate_by_polygons + create_square_grid 调用。
- **category** → `category_top`(众数) + `category_count`(去重多样性)；**timestamp** → `ts_count` + `ts_peak_hour`(最热小时，datetime 解析)。复用 ⑤② alias（类别/时间 别名友好）。boundary_id 分组键暂不做（另一聚合模式）。产物自动进 zone 属性+grounding，前端无需改。
- **验证**：承重 smoke——类别/时间别名列 aggregate 得 category_top=购物/count=3 + ts_count=5/peak_hour=8；无列 graceful 跳过零回归。承重：纯 additive，规范数据零回归。commit 只不 push。
- **⑤ 收口**：⑤②+⑤④-conf+⑤③ 全交付。**⑤④-`_missStats` 暂缓**（消费方 Flash 80% gate 未实现，建空计数器=推测性基建，待 gate 设计时一并做）。

### ✅ EMC ⑤②+⑤④ 字段 role 承重加固（revision-log 5.109，commit 待 push）

⑤ A3 字段角色系统的两个承重缺口。
- **⑤② 别名解析**：[spatial_analysis.py](core/spatial_analysis.py) 4 孤岛（aggregate_by_polygons/_attach_4x5_attrs/create_hex_grid/create_square_grid）接 `resolve_field_alias`——polarity/domain/element/topic gate 字面列名改按 role 解析实际列去读，输出保规范名（polarity_index/domain_top）。中文别名（情绪/领域/要素）走得通，**polarity_index 不再静默零**。
- **⑤④ confidence 0.3 阈值**：[field_dictionary.py](core/field_dictionary.py) `validate_llm_roles`（所有 LLM role choke point）加 `LLM_ROLE_CONFIDENCE_FLOOR=0.3`，conf<0.3（纯猜档）→ role=null 不承重。
- **验证**：承重 smoke——中文别名列 aggregate 得 polarity_index=0.8 + domain_top/归因链通；规范列名零回归；confidence 阈值 ≥0.3 保留/<0.3 null；字典自检 35 roles 全过。承重：仅字段解析层，规范数据零回归。commit 只不 push。
- **未做（待决策）**：⑤③ popularity（timestamp/boundary_id/category 热度，设计 A/B 待择）；⑤④-_missStats（遥测，待 80% gate 消费方定，不建空计数器）。

### ✅ EMC ④ industry_kb 按 domain_lens 动态注入（revision-log 5.108，commit 待 push）

②③ 厚化的权威细则运行时 0 消费（`industry_kb_text` 0 调用、ELEMENT_HINTS 无渲染路径）+ diagnose 的 `domain_lens` 前端压扁成标签不回传后端。④ 闭环断链：domain_lens 回传 → 后端按命中域渲染完整权威语境 → 注入 post-diagnose step。
- **用户决策**：不在乎 token/调用成本 → 注全 4 个 post-diagnose step（agent/answer/revise/review）；渲染全量字段。
- **前端回传**：[harness.js](frontend/js/ai_qa/harness.js) 设 `ctx.domainLens`（过滤 general）→ [stages.js](frontend/js/ai_qa/stages.js) 四 step opts 透传 → [api.js](frontend/js/ai_qa/api.js) body 加 `domain_lens`。
- **后端注入**：[schemas.py](ai_qa/schemas.py) ChatRequest 加字段 → [router.py](ai_qa/router.py) 四 phase 透传 → [prompts.py](ai_qa/prompts.py) agent/final/revise + [review.py](ai_qa/review.py) 审查员拼附录（范式照 build_diagnose_prompt 拼 brief）。**diagnose 不动保 eval**。
- **厚化渲染**：[industry_kb 包](ai_qa/industry_kb/__init__.py) `industry_kb_text` 补 4 段（官方术语全表/底线指标/ELEMENT_HINTS 要素归因/他城案例），单域 1.2KB→~1.8KB；新增公共 `industry_kb_lens_appendix`。
- **验证**：pytest test_industry_kb **20 pass**（+新 6 测）+ test_a3_paradigm 12 pass；前端 3 文件 .mjs 过 node --check；后端 import 无环 + 签名自检；probe 验单/双域附录形态。**eval 刻意不跑**（diagnose 字节不变→必然不受影响；C6：eval 空 context 验不了回答层改进）。承重：全 additive。commit 只不 push。

### ✅ EMC ③知识库做厚（revision-log 5.107，commit 待 push）

四领域权威细则补全（中等深度，不扰 brief top-4）。
- [urban_renewal](ai_qa/industry_kb/urban_renewal.py)：完整社区（[106 试点](http://zw.china.com.cn/2023-07/24/content_94525225.shtml)设施清单）+ 体检指标维度（**标注与 4×5 归因矩阵层次不同防错标尺**）。
- [urban_planning](ai_qa/industry_kb/urban_planning.py)：街道设计导则（[上海](https://up.caup.net/pdf/shanghai-jiedao-daoze.pdf)/深圳/株洲，车本位→人本位/慢行优先）+ 完整街道。
- [urban_governance](ai_qa/industry_kb/urban_governance.py)：三率口径（响应/解决/满意）。
- [urban_operation](ai_qa/industry_kb/urban_operation.py)：生命线 7 类（燃气/桥梁/隧道/供水/排水/热力/管廊）。
- **验证**：4 模块自检 + EMC 全回归 **31 pass 0 回归**。承重：仅知识层 additive。commit 只不 push。

### ✅ EMC ②事件领域成体系化（revision-log 5.106，commit 待 push）

事件（瞬时活动）是 EMC 补官方盲区的差异化核心，v1 仅一句带过、未成体系。
- **调研实证**：官方有《大型群众性活动安全管理条例》（国务院令505号，公安口安全许可/应急）管**安全底线**；[城市体检 61/76 指标](http://tj.sina.cn/news/2023-07-24/detail_20230724.html)全是常态空间指标，**事件瞬时影响缺失**→ EMC 补「散场拥堵/体验/情绪聚集」维度。
- **落地**：[urban_operation.py](ai_qa/industry_kb/urban_operation.py) 8 字段增厚（条例+瞬时空间影响+活动情绪复盘四步法，KEY_TERMS 重排使**事件词进 brief 前 4** 立即影响 Flash）；[urban_governance.py](ai_qa/industry_kb/urban_governance.py) 镜像次归属。
- **归因四步法**（复用现有工具·不造新）：① 前后情绪对比(rank/zonal) ② 负面聚集(hotspot) ③ 影响圈(buffer) ④ 交通关联(overlay/nearest)。
- **验证**：两模块 __main__ 自检 + pytest test_industry_kb **14 pass 0 回归** + brief 打印确认事件词进运营 brief 前 4。承重：仅知识层 additive（14 字段 schema 不破、矩阵骨架不动）。commit 只不 push。

### ✅ EMC C1 运行时验证 + merge grounding 修复（revision-log 5.105，commit 待 push）

首次开 serve 端到端验 07-15 积累（之前全是静态测 + Flash eval 空 context 模拟）。
- **发现 + 修**：merge/clip/overlay 等 boundary 类首轮不识已加载面层（出缺槽 GAP 追问）→ buildContext grounding 加**层类型标签**（_kindTag：点/面/线/热力）+ **boundary 优先级启发式**（_polyRole：行政片区=首选 / 用地类 / 分析网格）+ 软化 ensure_zone 误导线；query_layers 同步（设计语言一致）。
- **验证（直连 API 省 LLM）**：① merge 修复——手搓新 grounding 跑 Flash，问「合并行政区」→ template=merge + boundary 填对 ✅ 不再追问；② 执行层 6 端点（merge/area_stats/hotspot/filter_attr/nearest/extract_feature）POST 真 geojson 全 HTTP200 ✅；③ A1-A3 user browser 验 ✅；A5/A7/run_python/四态 代码证。
- **C6 探针发现（接受）**：eval（空context）vs 运行时（有层）对「里」类歧义路由分歧（zonal vs overlay），zonal 合理非错。
- **承重**：仅 grounding 文本层，未碰 harness/三大件/数据可见纪律三处同源。ESM .mjs 过。commit 只不 push。
- **待验**：A4（L1 纪律）/A6（buffer B 钮回填）需 browser 视觉，用户方便补。

## 📅 2026-07-15

### ✅ EMC 收尾变现：filter_attr(B1.5) + 行业知识库接入 diagnose（revision-log 5.104，commit 待 push）

让已建基础设施变现，两件收尾：
- **filter_attr 登记 single 技能（B1.5）**：paradigm TEMPLATE_REGISTRY +1 + stages.js SKILL_DEFS 镜像（零白名单改，pre_filter/filter_attr 已在白名单、TOOLS 已实装）→ **B_TRACK 9 原型全点亮**（B 赛道 single-path 100% 覆盖）。
- **行业知识库接入 diagnose**：industry_kb_brief_text()（四领域官方术语+项目类型速查，精简）注入 build_diagnose_prompt → 让 Flash 用官方话语、归因指向具体项目（呼应"政策→情绪→项目"闭环）。增量 vs DOMAIN_OUTLETS framework：KEY_TERMS 精确术语表 + PROJECT_TYPES 项目落点。
- **验证**：py_compile + .mjs + pytest **192 pass / 6 预存 0 新回归**；**Flash eval 18/19 = 95%（历史最高）**——filter_attr 命中 + brief 注入未伤路由反达峰值。承重未碰（纯 prompt 层 + 追加，不碰 harness/normalizeCard/前端）。commit 只不 push。

### ✅ 行业知识库 v1 + 项目顶层设计哲学（revision-log 5.102，commit 待 push）

用户要求对标住建部等权威源建可做厚的行业知识库（四领域），经三次澄清确立**项目顶层设计哲学**（全项目，不只 EMC）：
- **6 原则入 CLAUDE.md 顶层纲领**：① 4×5=归因落点矩阵（非指标分类清单）+ 多归属 + 骨架稳定不动；② 归因=**政策→情绪→项目**闭环（情绪地图核心价值）；③ 官方话语对齐 + 补盲区（事件瞬时空间影响=差异化）；④ 知识库全项目可成长；⑤ 城市规划=**城市规划设计全谱**；⑥ 多归属主/次约定。
- **纠正错标尺**：我曾用"官方指标分类完整性"质疑 4×5（交通缺位/事件定位/安全），用户指出这是错标尺——体检"指标维度"（互斥穷尽）≠ EMC"归因矩阵"（多归属）；交通是矩阵交叉 feature、事件是补盲区差异化、安全民生部分已落硬件格。
- **落地**：新增 [ai_qa/industry_kb/](ai_qa/industry_kb/)（四领域权威源，宏观政策+项目聚焦+案例+情绪归因+4×5 多归属映射）+ [docs/industry-knowledge-base.md](docs/industry-knowledge-base.md) 概览 + paradigm DOMAIN_OUTLETS 注入官方框架 + [tests/test_industry_kb.py](tests/test_industry_kb.py)（13 测）+ memory `project-design-philosophy`。
- **验证**：py_compile + 每模块自检 + pytest **190 pass / 6 预存 0 新回归**；diagnose prompt 注入官方框架（+247 字 Flash-safe）。承重：4×5 矩阵骨架不动，新增节/模块全 additive。commit 只不 push。
- **下一步（做厚路径）**：各领域 PROJECT_TYPES/CASES 细化 + **事件领域成体系化**（补盲区差异化核心）+ industry_kb_text 注 diagnose。

### ✅ EMC 承重双修 + 静态清理 + Flash gate + lingbot 评估（revision-log 5.95–5.97）

**EMC 承重双修（revision-log 5.95，commit `32a86ac` 待 push）**：开 serve 运行时验证前，静态深读（Explore 全链追踪 + 直读）揪出 2 个承重必破缺陷，先修再做 Flash 80% gate 实测。
- **visible 纪律被默认 layer 绕过**（数据可见纪律铁律，5.92 Track 1 核心保证漏）：rank/buffer/clip/zonal 的 SKILL_DEFS（stages.js）+ TEMPLATE_REGISTRY（paradigm.py）optional_defaults 去硬默认 `layer='yichang_l2_t1'`。该默认经 validateParams 合并后使 `resolvePointLayer`（tools.js:494）走 `if (params.layer) return params.layer` 直接返字符串、跳过 `pickVisiblePointLayer` 的 visible 过滤 → 后端拿 'yichang_l2_t1' 当 preset_id 解析可能成功 → **"只传 L1·T1 却跑 L2"**。去默认后 single 技能与 density 同源走可见层；buffer 额外把缺省 layer 改用可见点层名交后端聚合。
- **buffer 编辑面板元数据丢失**（主 Toolbox dialog 流不破）：TOOLS.buffer（tools.js）产物注入 `_ui`（distance 关键 + dissolve/lineWidth/fillOpacity/lineStyle + sourceLayer 尽力解析）。addResultLayer（tools.js:280）既有 _ui.tool 注入对已有 _ui 仅补 tool，元数据完整透传。修 openBufferDialog（buffer-tool.js:72）seed 残缺致 applyParams 回填 DEFAULTS(1000m) 重做全然不同 buffer 的缺陷。
- **验证**：py_compile + .mjs ESM（stages/tools）+ pytest test_emc_template 5/5 全过。**Flash 80% gate 实测 = 9/13 = 69% → NO-GO**（真 DeepSeek-v4-flash）：2 概念问 Flash 散文直答不吐 diagnose 卡（走 general 短路、非真回归）+ 2 真歧义（clip↔zonal / overlay↔multi，所选皆有效操作）。**结论：single 路径暂不主导，保渐进激活兜底**（不命中→unknown→while-loop 零回归，符合 5.91 设计）。运行时待用户开 serve 验。
- **承重**：未碰主 Toolbox dialog 流（仅补 _ui 透传）/ generateGridForAI 签名 / 三大件出图 / 5.74 / 四态 / frame-based trust / F_005；commit 只不 push。
- **静态另揪中/低风险点（留 ①运行时验证一并修）**：density 2D heatmap 产物侧栏列表可能不刷新 / query_layers 列不可见层 / buffer 层被 isRange 当 range 显假图例 / legend-grid `_ui.tool==='density'` 死码。
- **下一步**：① Flash 80% gate 实测（py tests/eval_template_flash.py）→ 定 single 路径是否主导 ship；② 运行时验证各 track（用户开 serve）；③ upload 胶囊；④ 后端 density 全退场（SOP）；⑤ P2 专业框架；⑥ 加技能 #8-11。本地领先 origin（5.89-5.95）待用户手动 push。

**借鉴评估 · lingbot-map（revision-log 5.96，零代码改动，待 push）**：用户拟借鉴 docs/lingbot-map-main 的「AI+地图」实现，双 Explore agent 全仓深读证伪——实为 **3D 重建/SLAM** 项目（GCT=几何上下文变换器，图像帧序列→3D 点云+相机位姿，基于 VGGT/DINOv2），**非 AI+地理地图**。与情绪地图（LLM+2D 地理地图）数据模态/AI 角色/「map」含义/技术栈全零重叠，零 LLM/零文本/零 GIS，**可复用代码≈0**。
- **决策（不采纳）**：仅提炼 3 条架构思想启发（未来设计参考，非现成代码）落 [docs/reference-lingbot-map-eval.md](reference-lingbot-map-eval.md)：① 流式增量更新（paged KV cache）——未来实时情绪管线可借鉴「只处理增量」；② keyframe 降级+滑窗——未来大规模聚合；③ YAML 配置驱动摄段化渲染——emotion_map 已有 design tokens，largely 冗余。
- **删除**：原项目 324M（含示例图/PDF/权重引用，未跟踪）已 `rm -rf` 删除防重复下载。
- **承重**：零代码改动（仅新增评估笔记 + 删未跟踪参考目录），未碰任何承重模块；commit 只不 push。
- **正确参考方向**：找 AI+地理地图参考应转向 GeoLLM/MapGPT/CityGPT/UrbanGPT、LLM 地理实体抽取、MapLibre/Leaflet+LLM demo；agent loop 看 Anthropic SDK + .claude/skills。

**EMC 承重静态清理（revision-log 5.97，commit `ff5bec2` 待 push）**：5.95 双修时静态另揪的 3 个中/低风险兄弟 bug，前置收掉（让 ① 运行时验证少失败点）：
- **density 2D/terrain 侧栏不刷新**（heatmap-tool.js）：generateHeatmapForAI + generateTerrainForAI 补 renderLayerList/refreshLegend/reorderAllZ/showLayerManager（+ import，与 grid-tool 同模式，环已存在安全）。
- **query_layers 列不可见层**（tools.js）：加 `l.visible` 过滤 + 标签改「已加载可见图层（未显示层一律禁用）」，与 pickVisiblePointLayer/buildContext 一致。
- **isRange 分析产物显假图例**（sidebar.js）：改为排除任何 `_ui.tool` 标记层（buffer/overlay/area_stats/merge 不再显 NAVY range 假图例），仅纯面/线显 range；一并收掉 isRange 里的 density 死码。
- **验证**：.mjs ESM（heatmap-tool/tools/sidebar）全过。legend-grid 侧 density 死分支（polLabel）无害留。运行时待用户开 serve 验。承重未碰三大件出图逻辑/5.74/四态/frame-based trust/F_005；commit 只不 push。
- **下一步**：① 用户开 serve 运行时验证各 track（density 三模式 / 只传 L1 不跑 L2 / buffer 面板回填真半径 / 缺工具卡 + 本次 3 修复）；③ upload 胶囊；④ 后端 density 全退场（SOP）；⑤ P2 框架；⑥ 加技能（Flash 69% 下尚早）。本地领先 origin（5.89-5.97）待手动 push。

### ⏸️ 暂缓：upload 胶囊（用户 07-15 指定搁置）

Phase 2 跳过项 `{{upload:preset}}` 胶囊（panel.js renderAnswer+onMsgClick / harness compose* / tools.js buildContext / range-presets triggerUpload 导出）——用户 07-15 明确「暂时跳过胶囊开发，搁置」。遇缺 Range/商业/居住用地暂以纯文本 composeGapCard 引导，不做点击上传胶囊。后续需要时再启动。

### 📊 状态（07-15 收工）

- **EMC 三层齐备 + Flash 18/19=95%（历史最高）**——07-15 一日完成 A1→A2→A3①→行业知识库 v1+设计哲学→B1→收尾（filter_attr+知识库接入），全部 commit + **push 至 `da4a687`**。
  - **执行层**：15 技能 single-path（B 赛道 B_TRACK 9 原型 100% 覆盖）。
  - **认知层**：范式树 + select_template 真相源 + Flash 95%。
  - **知识层**：行业知识库 v1 接入 diagnose（官方术语+项目类型）+ 项目设计哲学 6 原则入 CLAUDE.md。

- **已 push 至 `da4a687`（5.99–5.104 全部），本地与 origin/main 同步**。

- **下一步（按优先级，详见交接卡）**：① **C1 运行时验证**（用户开 serve——今日积累一直没验过）；② **事件领域成体系化**（补官方盲区差异化·战略）；③ 知识库做厚（指标细化）；④ industry_kb_text 按 domain_lens 动态注入（harness 改·承重）；⑤ A3②③④（field_dict 接承重/popularity/_missStats）。

### 🗺️ 任务计划 · EMC 架构优化 + 功能升级（07-15 拟定，详细）

> 基线：5.89–5.97 工作机制重构 + 承重双修 + 静态清理全收；Flash 80% gate = 69% NO-GO → single 路径保渐进激活（不主导）。推进序 **A1 → A2（并行）→ A3 → B1**。每步：实现→静态验证（.mjs/py_compile/pytest）→（改承重走 SOP）→commit（只不 push）→同步 todo 顶部当天段 + revision-log + 刷新 §5「最新动态」指针。

**Tier 1 · 解锁 + 清债**

- ✅ **A1. Flash 命中率提升 → 解锁 single-path 主导** ★★★（解锁器，**5.99 已完成**）
  - **结果：69% → 11/13 = 85% PASS**（single-path 可主导 ship）。改 [ai_qa/prompts.py](ai_qa/prompts.py) DIAGNOSE_TEMPLATE「必吐 JSON 不散文」铁律 + concept 映射 + 字段数 7→8 订正 + 6 条 few-shot（concept/density/buffer/clip/overlay）+ 选择要点 anti-multi 铁律；[ai_qa/paradigm.py](ai_qa/paradigm.py) `DIAGNOSE_CARD_FIELDS` 对齐契约（method→template/params）+ clip/multi triggers 细化；[tests/eval_template_flash.py](tests/eval_template_flash.py) 加 .env loader。
  - **主杠杆命中**：2 concept MISS 修掉（diagnose 必吐卡 + concept 映射）；另修地铁站周边→buffer、某区商业用地→clip、并排序→multi（balanced few-shot + anti-multi 规则）。剩 2 MISS 为真歧义「所选皆有效」（各区情绪排序→zonal、居住用地里→clip）。
  - 验证：pytest `test_emc_template` 5/5 + py_compile + Flash gate 11/13=85%。承重未碰（normalizeCard/runTemplatePath/路由/四态/渐进激活兜底全在）；commit 只不 push。

- ✅ **A2. 后端 density 全退场（删 F_005 kde_raster）** ★★（承重清债，**5.100 已完成**）
  - **结果**：删 `/api/v1/geo/density` 端点（`DensityRequest` + `density()`）+ `kde_raster`(F_005) + `_KDE_PROJECT_CRS` 常量 + kde 的 F_005/D_004 注册（2 文件 -150 行）。**顺带修 F_005 重复注册 bug**——[buffer_analysis.py](core/buffer_analysis.py)(原主) 与 spatial_analysis.py(kde) 双重注册，kde 退场后 F_005 唯一→buffer（符合 core/CLAUDE.md「不删已有 ID」，删的是冲突重复，F_005 仍在）。
  - 验证：py_compile + grep 零 dangling 代码引用（`kde_raster`/`DensityRequest`/`geo/density`/`_KDE_PROJECT_CRS` 全无）+ F_005 唯一→buffer + pytest 166 pass / 6 预存 0 新回归。承重未碰（buffer 聚合 / aggregate_by_polygons(331-372) / hot_spot / moran / F_007 terrain / geo_routes helper / 三大件 / 5.74 / 四态 / frame-based trust 全在）；commit 只不 push。

**Tier 2 · 专业层做厚**

- **A3. P2 专业框架** ★★（有用性环，较大，A1 后）— **① 已完成 5.101（②③④ 待续）**
  - 目标：认知层从「P1 技能编排」做厚到「专业范式 + 字段语义 + 热度维度 + 遥测」。
  - ✅ **① 专业范式树（5.101 完成）**：B_TRACK_PARADIGM 9 原型（Load→Transform→Analyze，顺序=关键词优先级）+ SCALE_PARADIGM.method_templates 对齐住建部城市体检四层级（住房→小区→街区→城区）+ select_template(track,card,question) 单一真相源。**业界调研汲取 GeoLLM-Engine**（single-path 验证 + Load-Filter-Plot + intent→工具序列），CityGPT/MapLibre-demo 不采纳。Flash 命中率 85%→92%（A1 协同提升）；pytest 177 pass 0 新回归；承重未碰（Python+prompt 层）。
  - ⬜ ② field_dictionary 接承重函数（上传层 alias + spatial_analysis polarity 门控/五级/domain-element 硬编码列名→resolve_field_alias）。
  - ⬜ ③ popularity role（timestamp/boundary_id/category 已存 → 时间/边界/品类热度分析）。
  - ⬜ ④ _missStats 遥测 + confidence 阈值 0.3。
  - 演示价值：识别更具体城建/更新问题（有用性环），对规划师/住建局更有说服力。

**Tier 3 · 扩能（gated on A1）**

- ✅ **B1. 加技能 9→14** ★（nearest/hotspot/area_stats/merge/extract_feature，**5.103 已完成**）
  - **结果**：TEMPLATE_REGISTRY 9→14，5 工具登记为 single 技能（paradigm TEMPLATE_REGISTRY +5 / stages.js SKILL_DEFS 镜像 / prompts 枚举+选择要点 / eval CASES +5）。**零白名单改**（optional_defaults 避开 invert/where/group_by）。A3① B_TRACK 4 原型自动点亮、normalizeCard 路由新技能。
  - 验证：py_compile + .mjs ESM + pytest **191 pass / 6 预存 0 新回归**；**Flash eval 5 新技能 5/5 全命中**（single-path B 赛道打通）。总体 14/18=78% 系旧歧义 case flaky-low（rank↔zonal/clip↔overlay，"所选皆有效"；此前 85-92%），非 B1 问题。承重未碰（8 字段契约/SKILL_DEFS 同步/白名单/通用路由/数据可见纪律全在）；commit 只不 push。
  - 注：filter_attr（B_TRACK 第 5 pending 原型）未入 B1，留 B1.5。

**持续 / 搁置**：C1 运行时验证（用户开 serve 验各 track + 5.97 三修复，持续）；C2 upload 胶囊（⏸️ 07-15 搁置）。

## 📅 2026-07-14

### ✅ EMC 工作机制重构三阶段·站在巨人肩膀上落地（revision-log 5.89–5.94）

**EMC 图面本地化 Track 0（revision-log 5.89）**：density 无图例/无情绪语义 + 五极色三套打架 → 半成品图面直接解药（用户原怀疑"工具适配不了数据"经实测证伪，真因=图面最后一公里本地化缺位）。
- **改**：①density 图例分支（sidebar.js：isRange 排除 density + legend-grid 加 density + 标题"情绪密度"）②density 默认 value_col='score'（geo_routes/tools，按得分加权带情绪语义）③五极色归一 tokens 单源（state.js L2_* #86E61C→#78DC32 套对齐 tokens.css/emotionColors；DENSITY_RAMP→gradient.neg；brand-visual.md 同步）④density 3D + 去噪（tools _ui mode:'3d' + map cell 线归零消莫尔）⑤粗化透明化（kde_raster 回传 actual_cell_m + observation 标实际分辨率）。
- **撤销（agent 误判纠正）**：0.6 polygon NAVY 隐形——撤销（addLayer 给非分析 polygon 配 PRESET_COLORS，本就可见）；hotspot 无图例——撤销（addLayer 默认 point→colorMode:'polarity'，图例本就触发）。
- **验证**：.mjs ESM（state/map/sidebar/tools）+ py_compile 全过；pytest 161 过/6 失败全预先存在且无关（h3 未装 + 未碰模块）。运行时待用户开 serve 肉眼验。
- **承重**：未碰三大件出图/5.74 对账/四态出口/frame-based trust；F_005 仅增 attrs 不改签名；commit 只不 push。
- **后续**：Track 1（L1 兜底 + query-first 代码门控）/ Track 2 P1 编排（TEMPLATE_REGISTRY 技能化 + runTemplatePath + buffer 聚合 + Flash 80% gate）/ Track 3 P2 专业框架，降级后续会话。

**EMC Track 1 + Track 2 完成（revision-log 5.90 / 5.91，commit b8de781 / 待 push）**：
- **Track 1（5.90, b8de781）**：① L1 极性静默全0兜底（aggregate_by_polygons 探测小写3级→3级路径，空值剔分母，治"撒谎中性"）+ score 自适应默认 ② query-first 代码门控（round0 注入 TOOLS.query_layers observation 到 toolHistory，零 LLM，治"盲目调错工具"）。
- **Track 2（5.91）**：① TEMPLATE_REGISTRY 9 技能（拟人化·可生长）+ template_registry_text ② diagnose method→template+params + 技能目录附录 ③ stages.js SKILL_DEFS 镜像 + validateParams + _PARAM_ALIAS 25 项 + normalizeCard（非 SKILL 归一 unknown）④ harness runTemplatePath（single 路径 0-agentStep，p^N→p²，缺槽/失败→EXIT_GAP）+ 路由 ⑤ buffer 聚合闭环（BufferRequest 继承 _GeoBase + 焊圈内 4×5 归因，省略逐字节同原）⑥ Flash 80% gate（test_emc_template.py 结构测 + eval_template_flash.py 手动评测）。**两真 bug 修**：normalizeParams 加 export + parseDiagnoseCard 收 template 卡。
- **验证**：py_compile + .mjs ESM 全过；node 内联测 parse+validate 6/6；pytest 166 过（+5）/6 预存无关失败；buffer TestClient no-layer 逐字节同原 / with-layer 焊 point_count=396·polarity=-0.596。
- **承重**：未碰三大件出图/5.74 对账/四态出口/frame-based trust；F_003 不改签名；commit 只不 push。
- **渐进激活**：Flash 首次见 template，未可靠输出前落 unknown→while-loop（零回归）；达标后 single 主导。运行时 E2E + Flash 实测待用户开 serve + 跑 eval。下续 P2（加技能 #8-11 + B/C 范式树 + field_dictionary 接承重函数）。

**EMC 工作机制重构（revision-log 5.92/5.93）**：三 agent 证实用户 4 猜测全中（EMC 自造并行 GIS 没套 Toolbox + 数据用 registry 缓存非 Layers 可见 + run_python 软约束 + 无上传胶囊）。分 2 commit 矫正。
- **Commit A（5.92）**：① 数据可见纪律——pickVisiblePointLayer 只扫 visible 层，6 点层工具默认 layer 从 registry `'yichang_l2_t1'` 改为 visible fc + 无可见守卫（绝不臆造跑 registry）；buildContext 过滤 visible + 移除 formatGeoCatalog（registry 全量泄漏源）。② addResultLayer 注入 _ui.tool（EMC 产物获 Toolbox 编辑面板身份，buffer 受益）。③ run_python 收口——harness gate 拦截（ctx.allowCodeViz 才放行）+ composeGapCard 缺工具分支（引导后续开发不临场写代码）。
- **承重**：未碰三大件出图/5.74/四态/frame-based trust；commit 只不 push。
- **Commit B（5.93）**：generateHeatmapForAI（heatmap-tool.js 新增 2D 彩虹程序化入口，仿 generateGridForAI）+ EMC TOOLS.density 委托——2D→generateHeatmapForAI(rainbow) / 3D→generateGridForAI(terrain-9 可切 2D)，弃用自造 /api/v1/geo/density + DENSITY_RAMP；TEMPLATE_REGISTRY/SKILL_DEFS density 同步（optional_defaults 改 Toolbox 入参 mode/radius/weightField/cell_size/polarity，移除 layer 硬默认走可见层）。参数化设计落地：tool=成熟gis+本地化（委托 Toolbox 固定 HEATMAP_RAMPS），design=标准分析图层。
- **验证**：.mjs ESM（heatmap-tool/tools/stages）+ py_compile + pytest 166 过/6 预存无关；test_emc_template 5/5。运行时（density 出 2D 彩虹/3D 网格、套 HEATMAP_RAMPS、可切 2D/3D）待用户开 serve 验。
- **承重**：未碰主 Toolbox dialog 流/generateGridForAI 签名/三大件出图/5.74/四态/frame-based trust；commit 只不 push。
- **Phase 2 下续**：{{upload:preset}} 胶囊（遇缺 Range/商业/居住用地引导点击上传）+ generateTerrainForAI（3D KDE 等值面备选）+ DENSITY_RAMP/`/api/v1/geo/density` 全退场 + catalog 转 upload 引导源。

**EMC 工作机制重构·Phase 2 完成（revision-log 5.94）**：用户指定跳过 upload 胶囊（留后续），收尾其余：
- **generateTerrainForAI**（heatmap-tool.js 新增 export）：3D KDE 等值面·情绪地形程序化入口（仅 L2，仿 generateHeatmapForAI/generateGridForAI）。**Toolbox 可视化三件套（heatmap 2D / grid 3D / terrain 3D）程序化入口齐备**，EMC 全量套用。
- **density 三模式路由**（TOOLS.density）：mode='2d'→heatmap / '3d'→grid / **'terrain'→terrain**。
- **provenance 补注册**（_registerToolboxLayer）：density 委托 Toolbox 的图层补入 _registry/_stepResults/_curResultIds——修 $n 引用 + formatRegistry provenance + 5.74 对账缺口（5.93 标注的取舍）。
- **DENSITY_RAMP 退场**（tools.js 删死码 const）+ `/api/v1/geo/density` 后端标 DEPRECATED（保留代码，F_005 承重全删须 SOP）。
- **验证**：.mjs ESM + py_compile + pytest 166 过/6 预存无关。运行时待用户开 serve 验。
- **承重**：未碰主 Toolbox dialog 流/generateGridForAI 签名/三大件出图/5.74(强化)/四态/frame-based trust/F_005(保留)；commit 只不 push。
- **后续（用户指定）**：{{upload:preset}} 胶囊 + catalog 转 upload 引导源。


## 📅 2026-07-13

### ✅ EMC 倾向性重定向：图层优先 + 交互体验（revision-log 5.88）

用户批 EMC 跑向学术报告（过长/分析多/偏离核心/不产图层），三条硬要求：①每回答必产图层（文字辅助）②简单直接+解题逻辑透明 ③结论结合地图互动。Explore 证实能力全有、缺口 100% 在 prompt 倾向。两决策：4×5/尺度**降权保留**、长度**软引导+审查卡**。修 5 处 prompt 层：①manifesto 第十节回答公约重写（删"专业不口语化"、加"图层优先/解题透明/简单直接/互动/简短"、4×5降权）+ 演示链改"先产图层"+EXIT"或"改"且"+身份/数据流；②FINAL 出口要素图层升首+解题一句话+文字注脚；③AGENT 规则4 简单问题≤3轮提速；④paradigm outlet"生成图层"升默认+三尺度加图层；⑤review concise 升 OBJECTIVE(超长fail)+structure/professional/scale 降权重定向。py_compile+.format 无 KeyError+11 契约落位全过。承重未碰（四态框架/5.70/5.74/P1-P3/5.87 不动，key 稳定）。第6处 harness 图层门延后（run_python 出图不入 newLayerCount 恐误杀，需 figCount 追踪）。端到端真跑待用户验。

### ✅ run_python 端到端失败治理：沙箱诊断+字段契约+出图路由（revision-log 5.87）

用户验证 run_python（问"用 Python 画各区极性柱图"）反复试错 9 轮才硬编码跑通、审查失败结论无价值。两份并行调研定位三层根因（沙箱静默吞错 / prompt 契约断层 / 路由+兜底缺失），**非策略不可行，是「问题-字段-答案」闭环在 run_python 路径上断了**（字段语义层 P1-P3 已就位、但 run_python prompt 没接上）。修 A 沙箱 data_refs 加载成功/失败都 print 诊断（sandbox.py PRELUDE §1，成功列可用变量治瞎猜、失败明确诊断治裸 NameError）；B 补字段契约（prompts L83 字段名迁移铁律+示例配套+geopandas+白名单 / paradigm CODE_EXEC_CATALOG，顺手修 catalog 双括号 bug）；C 出图路由（prompts 规则 9 柱折饼→zonal_stats+{{chart}} 勿用 run_python，chart 捷径上提 agent 可见）。py_compile + .format 无 KeyError（len 14815）+ 9 项契约落位 + 沙箱诊断 print 实测可见，全过。承重未碰。端到端真跑待用户验。D/E（失败兜底+revise 保图）可选未做。

### ✅ focus/show/inspect 按钮正则兼容单括号（revision-log 5.86）

沙箱收尾梳理遗留（todo 旧记"下次顺手改"）。`{{focus|show|inspect:target}}` 操作按钮占位符正则只认双括号，但 `TEMPLATE.format()` 吞一层括号（`{{`→`{`）致 LLM 收到/输出单括号，前端双括号正则匹配不到 → 按钮不渲染（裸文字）。panel.js 两处正则（L294 按钮渲染 / L414 `_followUps` 抽首个 focus 区域）对齐 chart(5.67)/fig(5.83) 改 `\{{1,2}...\}{1,2}` 1~2 花括号兼容，capture group 不变回调签名不动。四类答案占位符（chart/fig/focus·show·inspect）正则统一收口。`.mjs` ESM 语法过 + exec 双/单/混合括号逻辑验证 PASS 8/8。承重未碰。

### ✅ 字段语义层 P1：统一字段字典 + alias 解析（revision-log 5.80）

实施字段语义层 plan P1。新建 core/field_dictionary.py（35 roles 权威源 + resolve_role/alias/find_boundary_name_column）+ frontend/js/field_dictionary.js（镜像 + findKeyByRole）。收敛 9 处零散映射：state.js FIELD_SYNONYMS re-export / geo_routes _apply_attr_filter 注入 alias 解析 + extract_feature 删硬编码 / geo_registry resolve_boundary GeoJSON nameField 推断 + _point_layer_overview 删 _KEY_FIELDS / range_selector name_candidates 改字典 / landuse_colors dominantDMLC 改 resolveRole / import.js detectColorMode pickKey→findKeyByRole。修 pandas Index 真值歧义 bug。物理列名不改（alias 只读）。验证：py_compile + node check + 自检 + pytest 152 passed（6 预存 fail，0 新回归）。承重：registry 未碰（P3）/ 自产层只声明 / 5.74 对账不动。P2（profile+LLM 推断端点）/ P3（catalog/registry 带字段）待续。

## 📅 2026-07-12

### ✅ 国标用地分类固化进规则（revision-log 5.79）

用户上传 2023.11 正式版用地用海分类指南 PDF，要求梳理一/二/三级类+代码写进规则、以后不读 PDF。新建 ai_qa/landuse_codes_2023.py（24 一级/111 二级/40 三级 + 代码 + landuse_name/level/parent/children/search + EMC_PRESET_TO_GB 对照）+ docs 概览 + CLAUDE.md 索引 + memory。三法交叉核对，自检过。诚实差异：指南述 113/140 但 PDF 实际 111/40（三级类仅 06-12 城镇建设类），以 PDF 为准。承重未碰（纯新增）。字段语义层 land_use_class role 以此为值域。

### ✅ 顶栏 .title-version 加 build 号（换环境识别）（revision-log 5.78）

用户"换环境"诉求——顶栏 logo 旁 `prototype alpha v0.1` 只显静态版本，换机器/分支后难识别 build。serve.py 新 `_inject_header_version`（注入 `（build：git 短哈希）` 到 .title-version span，与 5.75 `_inject_title` 同源 `_git_short`，幂等）。顺手删 out.png 测试产物。py_compile + 功能测过。承重未碰（仅 serve +1 注入器 +1 调用行）。

### ✅ EMC 月级改造（一）：P0d 第四态 + P1 ask_user + P3 沙箱骨架（revision-log 5.77）

月级全计划开跑第一段。**P0d EXIT_PARTIAL 第四态**：三态出口扩四态（做成一部分+标注局限+引导下一步，非替换），composePartialCard 引导式卡（断言句→引导句），对账 missing 1-2 升级走 partial 出口。**P1 ask_user 主动澄清**：prompts action schema 加第三态 + rule8 何时问，stages parseAgentStep 加 isAsk，harness ask 分支挂起（exit='ask'），panel onAskUser 渲染问+选项胶囊（复用 aiq-suggest-chip），对话引导语气。**P3 沙箱骨架**：api/sandbox.py（SAFE_READY=False 红线·不挂 /run）+ tests/test_sandbox.py 19 测试全过；frame-based trust 设计解 matplotlib lazy-import vs 拦 socket 矛盾。**两组 Workflow 对抗验证**：初验 3 路 serious（揪 CRITICAL fallback_annotated 误判 + 注入面 + ask 博弈漏洞 + 8 项）→ 修 11 处 → 复验 3 路 mostly-fixed → 再修 5 处（drift 卡转义/fails 转义/JSDoc/ask 跨会话重置/口径通俗）。node --check + prompts format + pytest 152 passed（6 failed 全预存环境 h3/SnowNLP，无关）全绿，0 新回归。承重未碰（四态扩非替换/composePartialCard 模板化/诚实门不被跳/沙箱红线/思考透明 5.70）。待用户带 key 复现 P0d/P1 + 待 push。下会话：P3 挂 /run + run_python → P2 减 GAP。

### ✅ EMC P0 止血（一）：宽容三零容忍（revision-log 5.76）

用户"稍出错没答案"——5.72/5.74 三零容忍违反体验>正确性。P0a drift 命中先 _reviseOnce markdown 重写（失败才退卡）；P0b 对账 missing≤2 保 draft+自动标注"未实际生成"（≥3 大面积才退 gap）；P0c narration narrations≥3 认文字答交 finalStep（不逼 MAX 落 gap）。范式：做不成也体面答。node --check 过，待复现验证。后续月级全计划已批：P0d（第四态+引导式卡）→P1（ask_user+语气）→P3（code-exec）→P2（减GAP）。承重未碰。

### ✅ 页面 title 加 build 号 + commit/push 分离（revision-log 5.75）

title 加 git 短哈希（prototype alpha v0.1（短哈希），无日期，方便识别版本）；右下角标同步去日期。serve.py _inject_title + do_GET 用 _git_short（每请求读 HEAD，commit 后 F5 即更新）。memory commit-only-user-pushes：以后 Claude 只 commit，用户手动 push（覆盖 CLAUDE.md commit+push 组合）。py_compile + curl 验证过。

### ✅ EMC 系统性防谎报 tool-as-truth（revision-log 5.74）

诊断"报告说生成 6 图层但 Layers 无图"——trace 铁证 B 路径（0 工具，finalStep 编）。范式转变：工具产出即真值（LLM 文字只解释已注册产物）。① artifact registry（tools.js _registry+setToolContext，5 数组保留不破）+ ② getArtifacts/formatRegistry + ④ harness finalStep 前注入 registry 真值（finalStep/review/revise 共用 ctx）+ ⑤ finalStep 后结构化对账（_extractClaimedLayers 抽声称 vs getLayers 实际，missing→退 gap+实际清单，intent 无关=根治单点失败=⑦核心）。正则验证过（编图层全拦、真图层不误拦）。增益后续：③ expected_outputs 计划字段 + ⑥ 自动补做。承重未碰（5 数组/getLayers 只读/composeGapCard 模板/审查客观项）。与阶段2 code-exec 同轨前置（①②⑤ 复用）。node --check 过，待带 key 复现。

### ✅ serve.py build 角标扫描修复（revision-log 5.73）

改 ai_qa/ 代码 build 角标不更新——查 [serve.py _build_stamp](frontend/serve.py) 用 os.listdir 只扫顶层不递归子目录，frontend/js/ai_qa/ 改动不进 stamp。改 os.walk 递归。澄清：代码生效靠 _inject_import_versions 给 ES module 注入 ?v=<mtime>，与 stamp 独立（stamp 旧 ≠ 代码没生效）。验证 curl /frontend/index.html → build `2023d15 · 07-12 15:19:06`。serve.py HTTP 根=repo root，入口=/frontend/index.html。

### ✅ EMC 阶段1 稳定性修复（revision-log 5.72）

诊断 EMC 对略复杂多步任务失败（第一次 EXIT_GAP 零工具 / 第二次裸 JSON）——后台 trace（episodes.jsonl + .trace/trace.log）确认老病两条漏边复发。修：narration 逃避堵漏（diagnose 正常的任务逼工具至 MAX_ROUNDS 落 gap 卡模板，不让 LLM 自编"做不成"；仅概念问降级诊断认叙述作答）+ finalStep JSON 漂移拦截（整段 agent JSON→落固定卡，永不裸输）+ MAX_ROUNDS 8→16 + FINAL_TEMPLATE 格式铁律软引导。后台可访问性：episodes+trace 够判大类根因，逐步 thought/action 仍在浏览器内存。能力边界（客观）：≤4步稳/5-6看运气/多分支×N超16轮/Overview联动缺工具。desktop 工作台评估：用户判断 20%对/80%错（Skills 是开发工具的、EMC 运行时无；核心差距工具范式 40% 非模型 5%），路径 阶段1→2(code-exec)→3。node --check/py_compile 过，待用户带 key 重问复现。承重未碰。

### ✅ LLM 韧性 retry + fallback（revision-log 5.71）

Explore 核实 llm.py 单点单次零兜底，DeepSeek 一挂全瘫。新增 `chat_with_fallback`（调度员，LLMClient 电话机不改）：流式边界（首 chunk 前失败可重试/换家，首 chunk 后失败直接抛防错位）；retry MAX_RETRIES=3 退避 1/2/4s（5xx/429/网络可重试，4xx 换家）；provider 链 DeepSeek→Ark→讯飞空 key 跳过（仅配 DeepSeek 兼容）；router/review 各改几行共用、yield 形状不变。trade-off：备用家可能不支持思考链字段，切换时思考过程或少一段（≫全哑火）。新建 test_llm_resilience.py 10 用例全过；api-conventions 补流式边界节；.env.example 补 provider 链配置。承重未碰（LLMClient 签名/三态/审查/自成长不动）。

### ✅ EMC 思考过程主题折叠 + 容量圆圈富 tooltip（revision-log 5.70）

用户两件前端可读性诉求。**思考主题折叠**：流式照常累加，流末 `finalizeReason`（onFinalDone/onDegraded）按 \n\n/转折词切主题→默认收起目录+点开看展开体（加粗转折词，先 escapeHtml 防注入）；复用 toolcard 折叠样板；单主题不折叠直接显。事件委托改：topic-head 不冒泡整块。**容量圆圈富 tooltip**：去原生 title，JS 单例挂 body（position:fixed），hover 现填（百分比+Claude 橙进度条+5 类明细：输入/输出/思考链/缓存命中/会话规模）；顺手 warn 色 amber→Claude 橙。诚实约束：DeepSeek 不拆输入内部，明细按 token 类型+会话规模重定义。承重未碰（只改渲染/纯前端增量）。node --check 过，视觉待 F5 验。

### ✅ EMC 全面审查 → Tier1 三项（DataEye + 审查门 + 报告导出）（revision-log 5.69）

用户要"全面系统回顾 EMC，核心=业界领先端到端"。审计 13 个端到端环节（11 强/较全，4 差距：审查门关/自成长半残/DataEye 浅/LLM 脆弱）。用户选 Tier1 三项打包：
- **B DataEye**：`buildContext` 层摘要 `字段名`→`字段=类型:2样本值`（borrow GIS Copilot）。实测含 `DLMC=str:商业`。
- **A 审查门重启**：`REVIEW_ENABLED` true（`localStorage.emcReviewOff` 杀开关）+ 聚焦客观项（data_driven/actionable/scale_fit/professional；主观项只 warn）+ C-only scope + **verdict 入 episode→自成长闭环激活**。
- **C 报告导出**：答案脚"导出报告"钮→自包含可打印 HTML（标题+问题+答案+图表 PNG+落款）→新窗 print 存 PDF。实测 21.8KB HTML 含图表 PNG。
- 承重全未碰。push 2363e4f。

### ✅ 追问胶囊深色 UI 修复（白底浅字看不清）

EMC 深色面板里追问胶囊用白底+主题文字变量（深色 EMC 翻浅）→浅字白底看不清。改成 EMC 深色风（半透明深底 `rgba(255,255,255,.06)`+浅字 `#ECECEC`+橙标签+hover 橙边），对齐 welcome-chip/exit-badge。push 213b838。

### ✅ 思考↔结论脱节系统性修复（revision-log 5.68，07-11）

用户报概念追问思考已得结论、结论却被换缺数据卡。系统性审计整条决策管线→**只有一类病：gate 覆盖模型 deliberate 作答**。关键发现 `compressHistory` 传全 thought→finalStep 看得到思考→链本健全，脱节根因是 gate 跳 finalStep。三修：`_hardFail` 加 `answered`（deliberate answer 不当失败）+ `narratedAnswer`（**真凶**：概念问模型 prose 作答→叙述→原 degrade→GAP；改交 finalStep）+ diagnose 概念追问→general。实测"什么是核密度分析"修后出真结论（KDE vs Gi* 对比）。教训：验证别清 localStorage 历史（清了用户聊天史）。push e65a3c0。

### ⬜ 下会话：验 Tier1 + 推 Tier2/3
1. **用户验 Tier1**（硬刷新看 build 角标）：C 类问→审查 verdict 区；复杂筛选命中率（DataEye）；导出报告钮→PDF。
2. **审查门是重启**（曾关）——若 Flash 审查噪/降质，`localStorage.setItem('emcReviewOff','1')` 一键关。
3. **Tier2/3 路线**（计划文件）：LLM 韧性(retry+fallback) / 复合工具 compare·timeseries / 自成长闭环接通(consolidate→L2) / 主动建议 / 提速 / 多模态。

---

## 📅 2026-07-10

### ✅ EMC 图表生成·Phase 1（revision-log 5.67）

用户要 EMC「略复杂任务端到端、超越同行」。检索+zread 实读开源 AI+GIS agent（GIS Copilot DataEye/tool-doc RAG/SmartDebugger、LLM-Geo/GISclaw、GeoGPT、ChartGPT、CARTO）+ 用户上传 mapgpt-main（**纯营销页无代码可 copy**）。结论：EMC agent 骨架已对齐 SOTA，**最大差距=没图表**。
- **改**：答案里 `{{chart:TYPE|title=..|x=标签|y=数值}}` → Chart.js 柱/折/饼（bar=排序/line=时序/pie=占比）。panel.js `_renderCharts`（挂 enhanceCodeBlocks）+ Chart.js@4 CDN + FINAL_TEMPLATE 教模型出图 + .aiq-chart-wrap CSS。
- **两个陷阱**：`.format()` 吞一层括号→正则兼容 1~2 花括号；畸形规格用 HTML 实体防二次嵌套。
- **验证**（Playwright 真实管线）：注入伪答案走 restoreHistory→renderAnswer→_renderCharts → 3 图全渲染+3 实例绑定+畸形留 1 个不嵌套+零崩。承重全未碰（图表纯增量）。
- **push**：4535303（含上轮积压 410ae0c/a8517ac/4bf9ca5 一起推上）。

### ✅ EMC 回答策略重构 + 阶段3 三项 + 用地色全路径 + 防缓存（revision-log 5.61–5.66）

- **5.61 三态出口契约**（闸门，根治"只说不做"+代码块泄漏）：harness 代码强制终态(做成/缺数据/纯问答)+parseAgentStep 抗漂移(8/8)+onDegraded 永不裸输+密度出口做真(kde_raster/geo/density)+hotspot 修落图+装齐 scipy/libpysal/esda。
- **5.62 阶段3 三项**：推荐追问胶囊（上下文相关）+ 长对话折叠（>2 自动折叠）+ 用地色（PDF 附录B 39 类 → landuse_colors.js matcher 10/10）。
- **5.63–5.65 用地色三连修**：DLMC 权威落色→fillOpacity 0.6（原 0.15 看不见）→**全路径覆盖**（预设/手动上传 main.js/EMC tools.js addResultLayer 三处收口 `landuseLayerPaint`）+ serve.py **build 角标**（改代码后硬刷新看角标时间=新代码）。
- **5.66 start.bat 单实例**：netstat+taskkill 清 8080/8000 旧进程再起单实例；ASCII-only（cmd 按 GBK 解析 .bat，UTF-8 中文会破坏 `^|` 转义）。
- **验证**：parse 漂移 8/8 / landuse matcher 10/10+landuseLayerPaint 9/9 / KDE 真数据冒烟 / 预设+EMC 真实管线落色确认 / start.bat 实测。

### ⬜ 下会话：EMC 端到端 Phase 2/3 + 收尾

1. **先验 Phase 1**：硬刷新（看 build 角标）→ 问"各区情绪排序"/"T1→T3 演进"→ 看答案出图。
2. **Phase 2 DataEye 深化**：tools.js buildContext 加字段 dtype+2-3 样本值（borrow GIS Copilot），复杂 where 命中率升。低工作量。
3. **Phase 3 复合工具+报告导出**：compare/timeseries 一次性取数喂图（geo_routes+spatial_analysis）+ 答案脚"导出报告"钮（Chart.js toBase64Image→markdown/PDF，事企业"城市体检报告"出口）。
4. **Phase 4（远期）**：tool-doc RAG（工具数翻倍再做）+ code-gen kernel。
5. **mapgpt-main 待删**：`docs/mapgpt-main/`（未入仓、读完即删）——红线，需用户确认后 `rm -rf`。
6. **遗留**：`{{focus}}` 单括号隐患（.format 吞括号，模型可能输单括号、前端双括号正则匹配不到）——下次顺手把 focus/show/inspect 正则也改成兼容 1~2 花括号。

### ✅ 网格 2D/3D 底图切换卡顿·不换底图（revision-log 5.60）

用户报 2D/3D 切换底图卡顿（Dark→天地图影像慢）。
- **根因**：setView3D 每次切都 setBasemap→setStyle 换底图 = 重载瓦片（卫星瓦片慢）+ 旧拆新未到空白卡顿。vector 底图无法常驻显隐，平滑=不换底图。
- **修**：setView3D 加 AUTO_3D_BASEMAP=false，3D 不再自动切暗底图，只保 pitch 动画；逻辑 flag 包起可恢复。
- **权衡**：失 3D 自动暗底图观感，换流畅（用户可手动选暗底图）。
- **验证**：node --check + 200 ✓。真环境待复验。
- **后续**：Phase 2 余（推荐追问/长对话折叠）+ 阶段 3（用地色）+ 审查 agent 重构，建议开新会话。

### ✅ EMC 折叠收窄/复制 + 关审查 + 右栏缝隙 + 网格 2D/3D 闪烁（revision-log 5.59）

用户一揽子 3 功能 + 2 bug。
- **F1 折叠键收窄+橙框+文案**：根因=layout.css `min-height:320px` 钳死折叠态（非 --emc-h）。修：is-collapsed 连 min-height:0 覆盖 + --emc-h:40px；折叠输入框橙线框（展开 focus 同改橙）；placeholder 切换（折叠=新文案）。
- **F2 暂关审查**：harness `REVIEW_ENABLED=false` 跳过 Flash 审查员（诚实门保留）；审查 agent 下轮重构。
- **F3 复制回答 icon**：_renderFooter 页脚=meta + 复制 icon（复制 markdown，剥 {{action}}）；onFinalDone/onReviseDone 存 _finalMd。
- **B1 右栏缝隙**：根因=panel-body padding:16px + ov-subtabs sticky top:0 → 顶 16px 未覆盖带（漏出+浪费）。修：panel-body 去 top padding → sticky 贴顶无缝。
- **B2 网格 2D/3D 卡顿+闪烁+柱高跳**（承重）：根因=renderLayer 每次 removeSource+addSource+addLayer 全重建，切视角每调一次 → 首帧表达式回退（色/高闪）+ setStyle 换底图卡。修：_gridMapSetVis 布局显隐快速路径——已在地图的配对层免重建，仅首次走 renderLayer（带兜底）。
- **验证**：node --check + CSS/JS 200 ✓。B2 承重带兜底，真环境待复验。
- **后续**：审查 agent 重构；Phase 2 余（推荐追问/长对话折叠）；阶段 3（用地色）。

### ✅ EMC 交互·阶段 2（上）：折叠键 + 空态欢迎卡（revision-log 5.58）

进入原 3 阶段计划 Phase 2（EMC 交互）。本条做结构性两项，推荐追问/长对话折叠后续。
- **折叠键**：`.chat-head` 加 `#chat-collapse`（历史/新建/折叠 三键同 class 对齐）；折叠态 `is-collapsed` 局部覆盖 `--emc-h=48px`（绕开 EMC_MIN）+ 藏 head/view/foot，只留一行输入触发条，**点输入框展开**。`_emcCollapsed` localStorage 持久化；4 处自动高度函数加守卫防打架。
- **空态欢迎卡**：`renderEmptyState()`——问候+能力清单+4 示例追问胶囊（点击即发 send）。空→显/非空→移除；restoreHistory 调、appendMessage 清。
- **验证**：node --check ✓ + index.html 200 ✓ + 逐处追码。视觉（折叠高度/欢迎排版/三键对齐）待用户肉眼验。
- **后续**：Phase 2 余两项——推荐追问（答案后追问胶囊）+ 长对话折叠（旧轮折叠）。阶段 3（用地标准色）待续。

### ✅ EMC 图层清理·显式意图覆盖默认（keep:true）（revision-log 5.57）

用户点出 5.56 消费式清理太"死板"：用户 prompt 明说要保留某层，仍因被引用过而被清。
- **矛盾**：默认启发式（链式中间产物该清）vs 用户显式意图（保留某层）谁赢。死板=启发式赢；智能=显式意图覆盖默认。
- **解法**：6 个产出工具加 `keep` 参数 → addResultLayer 登 _keepIds → 消费式移除（增量+兜底）跳过 _keepIds。机械规则降级为可覆盖的默认。
- **何时 keep（AI 判断）**：用户明说保留 / 该层是要给用户看的结论（非跳板）。判据"用户最终要在地图看到吗"。prompts 加生命周期说明 + 6 工具 keep 文档 + 规则第 7 条。
- **时序安全**：keep 产出时登记，先于后续引用消费。
- **验证**：node --check + prompts parse + keep 3 场景追码全过（链式+keep 留两层/链式无 keep 留最终/keep 经 cleanup 仍留）。
- **后续**：阶段 2（EMC 交互）+ 阶段 3（用地标准色）待续。

### ✅ EMC 组中间图层泄漏·消费式补全（命名引用）（revision-log 5.56）

用户第二次报 EMC 组留"过程中"图层（应只留最终答案图层）。
- **根因（复发）**：B2 消费式只检测 `$1`/`$2` 显式变量引用，不检测**图层名**引用；agent 常用名字（overlay(layer_a="西陵区·伍家岗区")）→ 名字解析分支不标消费 → 中间产物漏网。
- **修**（tools.js ref）：名字解析命中本轮 EMC 结果（id∈_resultIdByStep）→ 同 $n 标 _consumedIds。命名/$n 一视同仁。
- **修**（tools.js cleanupConsumedResults + panel.js finally）：轮末兜底清"被消费但未增移"的残留（后续工具失败场景）。
- **并列最终仍保留**：居住+商业互不引用→都留；链式中间→被引用即清。
- **验证**：node --check + 消费式 4 场景追码全过（链式命名/链式$n/并列/失败兜底）。
- **后续**：阶段 2（EMC 交互）+ 阶段 3（用地标准色）待续。

### ✅ EMC「回答一半停住」系统性根因修复（revision-log 5.55）

用户重报老问题（问 GIS 操作，EMC 自相矛盾诊断卡 intent=general+操作字段，无工具半截叙述+"审查中…"卡死）。排查定位单一根因 + 三个连带漏洞。
- **根因**：flash 诊断把 GIS 操作标 `intent=general`（normalizeCard 只补空 intent、不纠错标）→ harness general 短路（空 toolHistory 不跑工具 + 不走 review）→ Pro 被逼文字叙述操作半截停住 + "审查中…"永卡。74.6k/137s/10 次是空转代价。
- **F1**（stages.js normalizeCard）：intent 改强信号仲裁——outlet=生成图层/decision_type=操作 → gis_operation 压倒 general 误标；通用问答/定义/全 general domain → general；否则采信 stated。四例验证全过。
- **F2**（harness.js）：矛盾守卫——仍判 general 却带纯几何 geo method → 改 gis_operation 不短路。
- **F3**（harness.js）：完整性 gate——agent 发 answer 前，gis_operation 且计划 geo 步数 > 已执行步数 = 半截，强制续做(max1)。步数比对（不按工具名，clip↔overlay 不误判）；仅 gis_operation 触发。新增 `_plannedGeoSteps`/`_executedGeoSteps`（不按 ASCII 逗号切，防实参误切）。
- **F4**（harness.js）：general/request_upload 短路补 onReview(degraded) → 显"审查跳过"，清"审查中…"永卡。
- **验证**：node --check + intent 仲裁四例 + F3 步数追码全过。真环境复验待重放。
- **后续**：阶段 2（EMC 交互）+ 阶段 3（用地标准色）待续。

### ✅ EMC 多轮连续性·阶段 B+C：场景真跑通 + 鲁棒收尾（revision-log 5.54）

续 5.53 阶段 A。B 让 Q1「筛选西陵+伍家岗居住商业用地」真出完整结果；C 鲁棒收尾。
- **B1·extract 多值 `in`**（Q1"只伍家岗"主因）：where 原直传不归一、`in` 被后端压成单值。修 tools.js：where 走 `normPreFilter` → `{field,op,value:[...]}` → 后端 `_apply_attr_filter` `in` 做 `col.isin([list])` 命中两区，一调用拿全。
- **B2·结果层消费式保留**（修 5.52 bug2 过激）：加 `_resultIdByStep`+`_consumedIds`；`ref('$n')` 标消费；`addResultLayer` 只删被消费的中间产物、保并列最终结果（居住+商业都在）。轮界清空不泄漏。
- **B3·上传层字段透传**：buildContext 已加载图层补属性字段名（剔除 `_xxx`，≤6），AI 能写对 where。
- **C1·多目标完整性提示**（prompts.py AGENT 规则铁律）：全部目标须落地、method 多步全做完再 answer。不做 `_verifyClaims` 计数检查（B1 多值使合法更少调用→必误报）。
- **C2·目录缓存失效**：tools.js 导出 `invalidateGeoCatalog()`；range-presets.js 上传成功后调 → 当轮 AI 即可见新预设，不刷新。
- **C3·用地数据模型提示**：明示用地预设按类 dissolve、无"类×区"联合 → "某区某类用地"须 overlay(区, land_xxx)。
- **验证**：node --check + ast.parse ✓｜B1 端到端追码 ✓｜B2 消费式追码 ✓｜无循环依赖。真环境复验待用户重放 Q1→Q2。
- **后续**：阶段 2（空态欢迎/推荐追问/折叠旧轮/EMC 折叠键）+ 阶段 3（用地标准色）待续。

## 📅 2026-07-09

### ✅ EMC 多轮连续性·阶段 A：续作承接上轮 trace（revision-log 5.53）

用户两问失败 → 三路深挖三簇根因（上下文丢失/无续作意图/工具缺口）。
- **根因**：ctx.history 只回灌 trace.final，丢弃上轮 diagnose/steps/caliber；"继续"判 general 短路 rounds:0；prompts 零续作指令。
- **A1** panel.js `_buildPriorTurn`（蒸馏上轮 intent/method/done/gap/strategy）+ `_isResumeCue` → ctx.priorTurn/resume。
- **A2** harness.js `formatPriorTurn` 注入 ctx.context 顶部；ctx.resume 跳过 general/request_upload 短路，强跑 agent loop 续上轮 method。
- **A3** prompts.py DIAGNOSE 最高优先级续作判定（取上轮 intent、承接 method、勿判 general）。
- **验证**：mock 上轮 request_upload → "继续" → agent loop 跑+调 overlay（pre-A 零工具），LLM 明引"上一轮上下文…已执行第一步"。overlay 400 系 mock 无数据。
- **后续**：阶段 B（extract 多值 in / 结果层消费式保留 / 上传层字段透传）+ C（完整性/目录失效/组合提示）。

### ✅ EMC 紧急修：对话空白(再) + 只留最终结果层（revision-log 5.52）

- **bug1 对话空白（第二次）**：根因 = 5.51 focusOnlyResults 对 AI 结果 selectLayer+dispatch layer:selected → refreshOverview→focusLayer(结果)返父组→tier1 读 group.fc.features，而 _aiGroup 建组未传 fc→每次产图层工具崩→查询脱轨对话不完整→"点历史才显示"。修：_aiGroup 传空 fc / focusOnlyResults 去 selectLayer / tier1 加守卫。
- **bug2 过程层进 Layers**：extract→overlay 链显两层。修：addResultLayer 加新结果前移除本轮前序结果（中间产物），只留最终。$n 走 _stepResults fc 不受影响。
- **验证**：reload 0 错（原 4 错/查询清零）｜真查询跑通对话全程渲染｜mock 链后仅留最终层。
- **后续**：阶段 2（EMC 交互）+ 阶段 3（用地色）待续。

### ✅ EMC 增强·阶段 1：AI 结果呈现（revision-log 5.51）

- **①组重命名**：「AI 工作区」→「EmotionMap Copilot」（tools.js + state.js，仍 'ai' 类钉底）。
- **②直白命名**：六工具 `as` 兜底去「动词·」用内容（overlay「叠置·intersection」→「交·A与B」等）+ prompts.py 加命名规则+补 `as` 参。
- **③沉浸聚焦**：addResultLayer 每结果→focusOnlyResults 关其余（含 Range/点/旧结果）+ 缩放本轮并集(maxZoom16)+Overview 追随；_curResultIds 每轮 send 清空。
- **验证**：node/py ✓｜reload 0 错｜mock 测：结果入新组/ai 类、既有层被关/结果显示。命名/真查询待用户。
- **后续**：阶段 2（空态欢迎/推荐追问/折叠旧轮/EMC 折叠键）→ 阶段 3（用地标准色）。

### ✅ EMC 模块 Dark 模式（Claude Code 深灰 + 橙）· 纯换肤（revision-log 5.50）

5.49 紫白标题嫌丑 → 整个 EMC 做 Claude Code 风 Dark（深炭灰 + Claude 橙 #D97757）；**仅 EMC 深色，主界面保浅色**。
- **手法**：`#emc-panel` scope 覆写 `--geojson-color-*` 一键暗化 + `brand-primary:#D97757` 一键蓝→橙；≈15 处硬编码色逐改（紫→暗/橙、蓝 tint→橙、黑分割线→白、focus 白底→暗、用户气泡橙→灰、状态绿提亮）。
- **细节**：暗滚动条、gutter-emc 无缝、橙色 caret、代码块压深、color-scheme:dark。
- **未碰**：JS/承重逻辑/5.49 几何与图层钉底。
- **验证**：reload 0 错｜DOM 测色全中 + EMC 内 white_bgs=[]｜vision 复核可读/无泄漏｜compact(320) chat-messages=146px 回归过。

### ✅ EMC 肉眼验修复：对话空白严重 bug + 标题栏配色 + 图层钉底（revision-log 5.49）

用户肉眼验 5.48 后报三类问题，定位根因并修（承重逻辑未碰）。
- **严重 bug·对话空白**：根因 = `compact` 档 160px < 固定 chrome 高（chat-head 48 + input-area 133 = 181），`#chat-messages` 被挤到 24px→空白；载图层触发 `_checkCrowded`→compact→触发。"暂无匹配会话"是历史空态副现象。**修**：`EMC_MIN=320`，5 处下限同步（panel.js 档位+clamp / sidebar.js 拖拽+resize / layout.css min-height）。验 compact(320) 下 chat-messages=146px（原 24）。
- **标题栏配色+压缩**：`.chat-head` padding 10→6（48→40px）+ bg `#58427c` + 白字白 icon；`.aiq-mode.is-active`/`.chat-send` bg→`#58427c`（`.is-stop` 保红）。验 bg=`rgb(88,66,124)`。
- **图层钉底**：`categoryOf` 把 AI 工作区 group 独立成 `'ai'` 类；`_groupOrder=[...,range,ai]`；`applyGroupOrder`+`renderLayerList` 双钉底 + `reorderGroupSegment` 守卫。验渲染序 …→范围边界→AI 工作区（末）。
- **清理**：`git rm` 孤儿临时文件 `panel.js.tmp.7336.8a8a4e4363a8`。
- **验证**：node --check ✓｜reload 0 报错｜DOM 数值达标｜vision 复核无溢出。

### ✅ AI 问答 · EMC UI 重设计：左端栏融合 + 智能高度 + Claude Code 交互（revision-log 5.48）

AI 问答基座稳后，从底部独立抽屉重设计为融入左端栏的 **EmotionMap Copilot（EMC）**（VS Code Claude Code 插件式），1:1 对齐 Claude Code 对话交互。**承重逻辑未碰**。
- **结构** [index.html](frontend/index.html)+[layout.css](frontend/css/layout.css)：`#left-panel` 上下分区（`#lp-upper` + `.gutter-emc` 纵向拖拽 + `#emc-panel`），默认宽 240→380。
- **EMC 迁入**：删 `#chat-trigger` FAB + `#chat-close` ×；标题→"EmotionMap Copilot"；`#chat-panel`→`#emc-panel`（dock 流内）。
- **历史 1:1 Claude Code** [panel.js](frontend/js/ai_qa/panel.js)：就地视图(chat↔history)+搜索+列表+垃圾桶；数据层零改。
- **Pro/Flash 移发送左侧** + **textarea 加高 2×**（76→160 自适应）。
- **智能高度三档**(compact/comfort/expand)：图层堆积→让位、对话→撑开、选层→重算；手动拖设基线、自动围绕基线回退。
- **Claude Code 交互**：Thinking 头(Thought for Ns·Nk)+工具卡(renderToolCard)+Esc 中断+hover 复制+代码块复制。
- **token** [tokens.json](design/tokens.json)：左栏 min/width 上调 + 重跑生成器。
- **2 bug**：`.gutter` 同优先级反覆盖→`.gutter.gutter-emc`；`_checkCrowded` 误判隐藏 operate 拥挤→无图层守卫。
- **验证**：Playwright 自检过（console 无错/comfort 425/gutter row-resize/历史切换 ✓/语法 ✓）。深度（工具卡/真实查询/拖拽手感）待用户肉眼验。

### ✅ AI 问答 · catalog 数据 overview + 错误 detail 可操作化（吸收 GIS Copilot，revision-log 5.47）

一次性通读 docs/SpatialAnalysisAgent-master（Penn State GIS Copilot）。架构不同（code-exec vs tool-schema），吸收两点：
- **数据 overview**：geo_registry `_point_layer_overview` 返 fields+samples+dtypes+crs；catalog 经 formatGeoCatalog 拼「polarity:Very Positive/score:1.0」入 grounding（LLM 知取值不只字段名）。
- **错误 detail**：resolve_boundary preset 不可用加「可用 preset 列表」。
- 不吸收：code-exec/DAG/QGIS TOML/Qt UI（架构不同/不可移植）。差异化：4×5/尺度范式/情绪数据/产物 gate 是壁垒。
- 验证：catalog samples/dtypes ✓；preset 不可用 detail 含可用列表 ✓。

## 📅 2026-07-08

### ✅ Import · 解析配置弹窗 1:1 + 源 CRS 手选 + GPX/TopoJSON（revision-log 5.46，07月08日 23:50）

1:1 复刻 geojson.io 导入弹窗（截图=CSV 解析配置）+ 用户追加的坐标系选择/转换。纯前端轮（GDB/CAD 延后服务端）。
- **弹窗重构** [dialog.js](frontend/js/dialog.js)：按格式自适应——CSV 全套(Kind 坐标列/WKT列/GeoJSON列/编码折线·分隔符·经纬列·Infer types)，其余格式下拉；onConfirm 回 `{type,config}[]`；中文化。[dialog.css](frontend/css/dialog.css) 加配置区样式。
- **源 CRS 手选** ★：弹窗 CRS 区（自动检测+预设下拉+目标WGS84）；[import.js](frontend/js/import.js) `reprojectFC(fc,{prjWkt,crs})` 改签名（显式>.prj>启发式，向后兼容）+ `gcj02ToWgs84` + EPSG 速查表。取代写死 EPSG:4546 静默启发式。
- **新格式**：GPX(togeojson)、TopoJSON(topojson-client)；CSV WKT/polyline 走 esm.sh 动态 import。
- **调用点同步**：[main.js](frontend/js/main.js) runImport 透传 config；runRangeImport / [range-presets.js](frontend/js/range-presets.js) 签名兼容。
- **验证**：node --check 全过 + serve 200 + served 字节含新符号。CRS/Kind 正确性交用户真文件验。
- **延后**：GDB / CAD(dxf/dwg) → 服务端轮。

### ✅ AI 问答 · 可靠性硬 gate + 显式链变量 + 多会话 + 答案操作按钮（revision-log 5.45，07月08日 23:00）

业界对比后聚焦差异化（情绪+规划认知+问题闭环是壁垒）。本轮治两痛点+会话：
- **A1 产物验证 gate**：_verifyClaims 抽取声称图层 对照 getLayers 不一致→revise（B 操作也启用，治只说不做）。
- **A2 显式链变量 $n**：_stepResults + ref('$n')，LLM 用 $1/$2 引用前序产物（比图层名稳）。
- **A3 失败重试**：上轮 [ERR]→下轮换法提示。
- **D1 多会话存档**：_archive + chat-new 存档开新 + chat-history 列会话切换/删除。
- **D2 答案操作按钮**：{{focus/show/inspect}} → 可点按钮触发 TOOLS。
- **验证**：node check + Playwright 冒烟（加载/console 无错）。深度功能待用户。
- **留 UI 后**：多模态/主动建议/报告生成。

### ✅ AI 问答 · UI 改造 + AI 工作区组 + 回答诚实铁律（revision-log 5.44，07月08日 22:10）

- **①容量圆圈 SVG**：移输入栏左端，4px 环，深灰/>60%橙，悬停百分比（反映当前 context 占用）。
- **④用时用量**：footer"用时 Xs · 用量 Yk token / Z 次"（api call stats）。
- **⑤图标**：发送↑/停止▢ SVG。
- **②历史/新对话**：去清空，加图标按钮；历史下拉（单轮垃圾桶删除），新对话清空。（多会话存档留后续）
- **③AI 工作区组**：addResultLayer 归组（addGroup+parentId，sidebar 一致渲染）。
- **⑥诚实铁律**：FINAL_TEMPLATE 禁"只说不做"（声称必有对应工具产物，失败如实报）+ 出口要素（办法+图层+结论+建议）。
- **验证**：DOM 就位 + footer"131s/22.5k/4" + 圆圈 0.35%。组/铁律效果待用户真环境。

### ✅ AI 问答 · 修复流式中开关对话框回答停住（revision-log 5.43，07月08日 21:30）

- **bug**：对话进行中收起/展开 chat-panel，回答停住。根因：chat-trigger 展开无脑 restoreHistory() 清空重建，进行中 shell（未入 _history）被清，hooks 写脱离 DOM 旧元素。
- **修**：展开时 `!_streaming` 才 restoreHistory（流式中保留 shell；is-collapsed 是 transform/opacity 不破坏 DOM）。
- **验证**：Playwright 流式中收起→展开，textLen 4987→10510、isStreaming=true、shell 保留 = 流继续。

### ✅ AI 问答 · 多轮上下文 + 容量圆圈 + 几何端点修复（revision-log 5.42，07月08日 21:00）

- **诉求1 多轮上下文**：根因 stages messages 只传当前问题（无历史→失忆）。修 panel ctx.history（前 N 轮）+ stages 4 阶段拼历史。
- **诉求1 容量圆圈**（V4 Pro 1M）：llm stream_options → router {usage} → api.getLastUsage → panel 圆圈（绿<50%/黄<80%/红）。chat-head UI。
- **诉求2 几何修复**（后端非造轮子，版本兼容+bug）：① nearest 去靶标 Point 强制（支持面）+ 修 sjoin_nearest 旧参数；② hotspot 装 PySAL + 修 DistanceBand(threshold=0) 岛屿 bug→KNN；③ prompt 加工具选择决策（A内的B=extract→overlay，面∩面用 overlay 勿 clip）。
- **验证**：TestClient 全几何端点 200 ✓；Playwright 第3问 messages=5条（含历史）✓ + 圆圈 0.4% 绿 ✓。
- **未决**：组合操作 LLM 选工具质量待用户真环境（本环境 LLM 弱）。

### ✅ AI 问答 · GIS 工具链 chain + diagnose 提速（Phase 0 补丁，revision-log 5.41，07月08日 18:00）

- **诉求**：组合操作"西陵区内的商业用地"无法完成 + 思考缓慢。根因：**工具链无法 chain**（extract 产物喂不回 overlay）+ diagnose 用 Pro 偏重。
- **chain**：geoFetch 统一出口加 `ref()`——图层名引用参数（layer/range/layer_a/layer_b/boundary/center/target）匹配前端图层名→转 geojson send-in 后端。一处改动全工具通。prompt 加 chain 示例。
- **提速**：diagnose 改 flash（分类不需 Pro）。
- **验证**：TestClient extract 西陵区(1面) → overlay∩land_commercial(1面 3.23km²) ✓；node --check ✓。浏览器实测待用户。

### ✅ AI 问答 · 意图路由认知重构 + GIS 结果回写闭环（Phase 0 地基，revision-log 5.40，07月08日 17:35）

- **诉求→判断**：两致命 bug（拒答"今天星期几" + "裁出西陵区"8 次失败答非所问）。根因 = **4 层缺陷叠加**（① 认知层 MANIFESTO 收窄 + DIAGNOSE 封闭分类无超域出口；② 工具语义 clip 只切点 + catalog 不暴露字段；③ 前端不回写 geojson 用完即弃；④ 无反馈回路→盲目重试）。后续 GIS 能力全经 agent 暴露 → **先修 agent 地基再做 Phase 1**。详见 plan `main-maplibre-deck-gl-gis-geopandas-temporal-marshmallow.md`。
- **0a 意图路由**：MANIFESTO 三类意图（A 通用/B 纯 GIS 操作/C 情绪）+ DIAGNOSE `intent` 字段 + harness 分流（A 短路直接答 / B 进 loop 跳情绪审查 / C 原路径）。
- **0b schema 暴露**：catalog 带 fields（43）/name_field（admin_district=MC）→ LLM 不瞎猜字段。
- **0c extract_feature**：新端点抽面（裁出西陵区=1 面）；clip 仍切点，语义分明。
- **0d 回写**：addResultLayer 封装 + clip/filter_attr/extract/overlay/buffer/merge 落图 + clip 补 pre_filter + 支持 `as` 命名。
- **0e 反馈**：compressHistory 每轮附「地图:N层」断重试死循环。
- **承重**：不改 resolve_boundary name 规范化（extract 内兜底）/ intent 兜底推断防老模型 / B 跳 review / addResultLayer 同名替换防堆叠。
- **验证**：TestClient catalog(43字段/MC) + extract(西陵区 1 面) + clip(17925 点) ✓；Playwright **bug A 端到端通**（今天星期几→general→直接答日期，不拒答不引导情绪）；bug B 浏览器实测 + 情绪场景不退化待用户；pytest 124 passed（5 既有失败 h3/SnowNLP/geocode 无关）。
- **下一步**：Phase 1（手绘范围/时序 diff/叠置补完/DBSCAN/上传矢量闭环）。可达性/等时圈/缓冲暂不做。

### ✅ AI 问答 · 自成长知识闭环（三层"灵魂"· L2 wisdom + L3 episode + consolidate，revision-log 5.39，07月08日 16:00）

- **诉求→判断**：用户要"单一自我增长的灵魂 md"。判断：内核对（**缺反馈闭环**——用过不会更好），形态错（冗余/腐烂/抢 token）。已有 MANIFESTO/paradigm/auto-memory/design 四层灵魂；真缺口 = 真实问答的答问智慧捕获反哺。改建**三层知识闭环**（按生命周期分列）。
- **三层**：L1=MANIFESTO（不动）/ L2=`ai_qa/wisdom.py`（**人审策展**，6 条种子从 5.36-5.38 提炼）/ L3=`DATA/ai_qa/episodes.jsonl`（自动 append，gitignore，不进 prompt）。
- **闭环 3 动作**：① 捕获——每次问答 panel.js send 末尾 fire-and-forget POST `/aiqa/episode`；② 沉淀——`py -m ai_qa.consolidate` 读 L3 聚簇打印 L2 编辑**提议**（人审，不自动写）；③ 注入——buildContext fetch `/aiqa/wisdom` 拼 ctx.context（v1 wholesale，>12 条切检索）。
- **用户拍板**：全闭环+种子 / 人审策展 / 仅隐式反馈（不加 👍👎 UI）。
- **承重**：人审是 L2 不腐烂前提 → L2 恒小可 wholesale；L1 不动；episode 含用户问题→gitignore。
- **验证**：单测 ✓（修 consolidate `(x or {} and ..)` 优先级致 nfail 双计 + unicode 标记 GBK 崩溃→全 ASCII）；pytest 8 passed；Playwright 实测 `/aiqa/wisdom` 返 1463 字 + `/chat diagnose` 请求体 context 含完整 wisdom = 闭环通；send 触发 episode POST 落 jsonl。真实 LLM 质量对比待用户（带 key 同类问两次）。
- **演进**：L2 > ~12 条 → harness 按 diagnose 卡 fetch `/aiqa/wisdom?scale=&domain=` 切检索；未来可加显式 👍👎（richer 信号）。

### ✅ AI 问答 · 专业认知层知识基座 + GIS 工具骨干（revision-log 5.36，07月08日 12:20）

- **问题重定义**：5.35 后"回答几乎不能用"根因**不在审查/revise**，在 ai_qa 缺「专业认知层」——agent loop 在前端 harness.js，工具 tools.js 只读单一聚合层，不能下钻/上卷/按几何过滤，故宏观/微观问都答成坐标（范式错位）。详见 plan `main-memories-repo-session-handoff-md-a-smooth-hamster.md`。
- **Phase A2/B3 知识基座**：`ai_qa/paradigm.py`（尺度-方法-范式矩阵 + 4 域出口启发 + GIS 操作目录 10 工具 + DIAGNOSE 卡 6 字段）；`manifesto.py` 第十一节「尺度-方法-范式」硬约束。
- **Phase B1/B2 GIS 骨干**：`core/geo_registry.py`（lazy 缓存 L1/L2×T1-T3 + 边界 preset）；`api/geo_routes.py`（10 个 `/geo/*` 原子操作：filter_attr/clip/merge/area_stats/zonal_stats/rank/buffer/overlay/nearest/hotspot + catalog；复合入参 layer+range+pre_filter 免中间中转；复用 aggregate_by_polygons/hot_spot_analysis）。
- **验证**：12 路由注册 ✓；E2E `zonal_stats`(L2×行政区) →「白洋/伍家岗区/猇亭区 pi+归因」**宏观结构化结论（非坐标）= 验收核心路径打通**；clip/area_stats/filter_attr ✓；`test_geo_routes.py` 8 passed，全量 124 passed（5 既有失败与本轮无关）。

### ✅ AI 问答 · 前端接线 + 流式三件套（认知层/GIS 骨干收尾，revision-log 5.38，07月08日 13:20）

- **两个阻塞后端缺口（5.37 遗留，先补）**：① [router.py:15](ai_qa/router.py#L15) 漏 import `build_revise_prompt`（revise 路径 NameError）→ 补；② `AGENT_TEMPLATE`【可用工具】只列 8 旧工具、10 geo 工具未列入 → 补 10 geo 工具 + `build_agent_prompt` 拼接 `geo_tool_catalog_text()`。
- **Phase B4 geo 端到端** ✅：`tools.js` 10 geo 工具（geoFetch + 紧凑 observation）+ `buildContext` async 增列边界/时点/工具清单。
- **Phase A1 diagnose 前端** ✅：`stages.js` parseDiagnoseCard + diagnoseStep；`harness.js` 前插 diagnose（降级不阻塞 + 卡摘要注入 ctx.context + request_upload 短路）；`panel.js` 问题理解卡。
- **Phase A3 前端** ✅：审查区泛化遍历 `review.scores`，第 7 条 `scale_paradigm_fit` 自动渲染（无需改）。
- **Phase C 数据自检** ✅：request_upload → 「请求上传」结论卡（不硬答）；fallback_annotated → 口径标注卡。
- **Phase D 流式三件套** ✅：D1 逐字 RAF drain（治 O(n²)，流末 marked.parse）+ userPinned 停跟/回底浮钮；D2 思考移 `#chat-suggest` sticky dock + 阶段 chip；D3 `回答完毕·测试版 v1.0·时间戳`（无星期）+ trace.doneAt 持久化。
- **Phase A4** ✅：`.claude/skills/emotion-scale-paradigm/SKILL.md`（方法论镜像）；`docs/ai-qa-design.md` 第 3/4/5 章同步。
- **承重**：panel.js 不新增 map/state 耦合 / REVIEW_CHECKLIST key 稳定 / revise 1 轮不递归 / diagnose 与审查失败均降级不阻塞 / MANIFESTO 花括号 AGENT_TEMPLATE 全转义。
- **验证**：5 ai_qa JS `node --check` ✓；`test_geo_routes.py` 8 passed；Playwright 实测面板/dock/back-btn/chip/css/catalog 全挂载，**`zonal_stats(renewal_unit)` 返 3 行结构化归因（无坐标）= 验收核心路径打通**；修 back-btn 被 restoreHistory 清空 bug。**真实 LLM 硬测待用户**（本 shell 无 DEEPSEEK_API_KEY；既存降级链路 OK）。

### ✅ AI 问答 · 审查层接通 + agent loop 稳健性 + 思考体验对齐（revision-log 5.35，07月07日 23:25）

- **审查层接通（后端）**：`review.py` 新增 `review_answer()`（Flash + json_mode，六条 checklist 打分 ✓/△/✕，失败降级 {pass:True,degraded:True} 不阻塞交付）+ `_parse_review_json` 容错（fence/尾逗号/缺 key 补全 6 条/verdict 归一/fail 强制 pass=False）+ `REVIEWER_MODEL` 旧 ID 修正为 'flash'；`prompts.py` REVISE_TEMPLATE + build_revise_prompt；`schemas.py` phase 加 review/revise + draft/review_hints；`router.py` review（非流式单帧 SSE）/revise（流式）分支。
- **前端**：`api.js` onReview/draft/reviewHints 透传；`stages.js` reviewStep/reviseStep + parseAgentStep 强化（strip fence/去尾逗号/正则二次提取 action）+ onReason 透传 round；`harness.js` 接 finalStep→reviewStep→!pass→reviseStep + 降级回退（解析失败不再裸显 raw，break loop 走 finalStep）+ tool_history 压缩（params≤80/obs≤200）+ onRoundStart；`panel.js` 审查状态区 + Flash reason 对齐（"Flash·直接作答"）+ Pro 按轮分段折叠 + [ref:] 存在性校验（臆造名标 .cite-chip-invalid 灰显）+ trace 持久化（reasonSegments/review/revised）；`ai_qa.css` .aiq-review 系列 + .aiq-reason-segment + .cite-chip-invalid。
- **承重**：审查失败降级不阻塞 + revise 最多 1 轮不递归 + panel.js 不耦合 map/state（ref 校验只读 getLayers）+ REVIEW_CHECKLIST key 稳定。
- **待用户验**：完整 agent loop + 审查六条 + revise 重写 E2E（需 API Key + 聚合层数据）；Flash 模式 reason 区；降级回退；引用校验；历史持久化。

### ✅ AI 问答 Agent Loop 重构（Claude Code 式 ReAct）+ 还原底部面板 + 历史持久化（revision-log 5.34）

- **5.33 四层 Harness 实测三问题**：①看不到历史（开关丢失）②思考是"结果"非"动态"③回答不可用。根因=线性管线。
- **Agent Loop（ReAct）**：每轮 reasoner 输出 {thought, action}（reasoning 实时流 + thought 可见 + action tool/answer）。模型自主调工具循环（query→操作→answer），多轮上限8。真"边想边做边说"。
- **工具集**：query_layers/query_zone_stats/query_attribution/query_keywords/ensure_zone/focus_zones/open_attribution/inspect_zone/answer。
- **MANIFESTO 强化**（重读 architecture.md）：+三页焦点 +7场景 +演示链 +回答SOP +工具指导。
- **还原底部滑出**（独立窗不便，UI 后续重做）+ **localStorage 历史**。Review 暂移。
- **验证**：后端 import + agent_prompt 轮次 ✓；主页零 console error + panel 打开 ✓；agent_step E2E（reasoning 155字 + {thought,action}，定义问题第1轮 answer）✓。
- **待删确认**：protocol.js/ai_qa_host.js/chat.html（跨窗口协议弃用）。
- **待用户验**：完整 agent loop（带数据多轮工具循环 + 动态思考流 + 历史 + [ref:] 定位）。

---

## 📅 2026-07-07

### ✅ 任务2 时间轴 MVP 落地（revision-log 5.29）

- **两决策点确认**：① 柱体动画走 **A JS rAF+setData**；② Overview 重构 **限定到可动画 KPI**（count line + 饼图 + 极性矩阵；tier1/2 不动）。
- **数据架构**：L2 点自带 polarity/domain/element → 前端 **snap-to-grid O(1) 聚合**进活跃 grid scaffold（免后端改、免 sim 重生）；共享 max 跨 T 归一化 `_grid_h`。
- **落地**：`timeline.js`（新，scrub+T1/T2/T3 停点+play/pause/prev/next+错峰+#3A5368/#8B658B）+ `map.js updateGridSourceData`（每帧 setData，承重 paint 就地切换）+ `panel.js` KPI compute/paint 导出 + `grid-tool.js` 导出 `piToNorm` + `index.html/main.js` 挂载显隐。
- **验证**（MCP Playwright + 真实数据）：零 JS 错；timeline 初始化 OK；T1 16933 点 100% 聚合、消极>积极符合叙事弧。
- **承重全保**：paint 就地 / 双 sub-Tab / `_resolveLocAnchors` / enforceMutualExclusion / gridSig / sticky 最高级 不动。

### ✅ 本轮第二段：bug 修复 + 5 处小修改 + 时间轴矩阵/关键词/极性（revision-log 5.30）

- **聚合崩溃 bug**：scaffold 重投影致 2 格 min-corner 取整碰撞 → `arr` 洞 → `null.point_count` 崩 → `_snaps=null` → 播放静默。修：桶存数组 + 点取最近质心格 + arr 全填 blank。
- **综合矩阵/关键词不随 T**：`paintOverallKpi` 只动 count+饼图。修：加 `paintOverallMatrix`（pi lerp→色变）+ `paintOverallKeywords`（按最近 T 停点离散换词）。
- **极性深读地图错乱**：lerp `_grid_n_*` 致 filter `_grid_n_*>0` 穿越 0 闪烁。修：lerp 字段去 `_grid_n_*`（filter 稳定，高度/色用 `_grid_h_*`）。
- **极性矩阵显示浮点**：`_lerpPolKpi` n 取整。
- **5 小修改**：极性深读切 2D/3D 保持极性层（setOverview 同 fc 迁移 _polarityState）/ 初始底图天地图影像无注记 / 行政区 #d8d8d8 / 可见层眼睛加深。
- **未验**：动画行为 + 极性保持 + 小改视觉 待用户 F5；debug 钩子（window.__tl + [timeline] 日志）暂留待验后清。

### ✅ AI 问答 Harness 四层重做 + 独立子架构 + 独立窗口化（revision-log 5.33，07月07日 23:30）

- **B1 不可用根因**：萌芽 Harness 无灵魂（知识层/思考层缺失 + 执行开环）+ 面板折叠地图。
- **Harness 四层**：知识（MANIFESTO 领域宪法）/ 思考（think framing,mapping,steps + Pro reasoning 流式）/ 执行（tool 语义化 + 协议 RPC）/ 审查（6 条 checklist + Flash 审 + Revise 1 轮）。
- **独立子架构**：后端 `ai_qa/`（manifesto/prompts/review/schemas/router/llm）+ 前端 `js/ai_qa/`（protocol/harness/stages/tools/panel/api）+ `chat.html` + `ai_qa_host.js`。散落文件迁入，零外部依赖。
- **独立窗口化**：BroadcastChannel 协议化（CHANNEL='emotion-map-ai'）+ 真独立窗（window.open chat.html，不挡地图）+ 浮窗降级。panel.js 不调 map/state（形态可插拔）。
- **验证**：后端 import 链 + /api/v1/chat 挂载（OpenAPI 17 路由）✓；前端回归 webapp-testing（主页 #chat-trigger + chat.html #chat-send、零 console error）✓；think 端到端（Pro reasoning 117字 + JSON framing/mapping/steps，"什么是情绪地图"正确只 conclude 不建层）✓。
- **待删确认**：core/chat_context.py、core/llm_client.py、frontend chat-panel.js/chat-orchestrator.js/chat-panel.css（已迁入 ai_qa/，红线待用户确认）。
- **待用户验**：完整端到端（带数据问答：解题面板5格 + 审查6条 + [ref:] 定位 + 独立窗/浮窗切换）。

---

### ⬜ 明日（07-08）任务详细

**P0 · F5 验证本轮修复（确认后再推进）**
1. 综合 Overview 时间轴 Play：矩阵**色** + 关键词随 T1→T2→T3 变。
2. 极性深读时间轴 Play：地图柱体平滑、cell 不闪烁；面板矩阵数字正常（无小数）。
3. 极性深读点 2D/3D 视角按钮：**保持极性层**（不跳回综合 Tab）。
4. 初始底图 = 天地图影像（无注记）；行政区层 #d8d8d8；可见层眼睛加深。
5. 异常 → F12 贴 `[timeline]` 日志 + `window.__tl()` 输出。

**P1 · debug 钩子清理 + commit（P0 通过后）**
- 删 `timeline.js` 的 `window.__tl` + 诊断 console.log/warn。
- commit「feat: timeline MVP + 5 小修改 + bug 修复」。

**P2 · 时间轴剩余设计要点**
- **播放起步切 3D**（MVP 未接）：`play()` 起步若 2D → 切 3D。**决策点**：3D 下底图用 dark-matter（setView3D 现自动切，柱体对比强）还是保留天地图影像（演示语境）？需与用户对齐。
- **T2 关键词副本**：`polarity_deepread_keywords.json` 仅 T1/T3（无 T2）；T2 停点 block 词处理（crossfade T1↔T3 或补 T2 副本）。
- **极性深读 block 关键词随 T 切**：当前 hover-driven（`#ov-block-kw`），时间轴下是否按 T 换副本待定。

**P3 · 地点 tip 全面核对修正（延后两次，必做）**
- 审计脚本：遍历副本 v3 所有 loc name → area_seed/spatial_hotspot 匹配 → 输出 cell 坐标。
- 逐项核对 vs 真实宜昌地理（奥体/南湖/体育场/中南路/二马路/桃花岭/长江之心）。
- 副本 name 具体化（"东山"→"东山大道港城路口"）；数据缺 POI 的换或标无定位。
- webapp-testing 逐词 hover 截图核对。memory `loc-anchor-by-data-not-coords`。

**P4 · 承重回归 + 打磨**
- 回归：paint 就地切换还原 / 双 sub-Tab / enforceMutualExclusion / sticky 最高级 / 换层 timeline 显隐 + source 还原。
- scrub 连续拖动（当前 click 跳 + 停点；drag 暂未实现，可选）。


---

## 📅 2026-07-06（周一）

### ⬜ 明日任务：地点 tip 全面核对修正（用户报"仍有大量错误"，先放一放，严格对照真实情况检查）

> 用户反馈 5.27 的地名→cell 匹配仍有多处错位。根因可能：① 副本地名太泛（如"东山""点军""政务中心"是大片区，匹配到的 area_seed 不代表具体地标）；② 多义匹配（一个地名命中多个 area_seed，取最近 cell 不一定对）；③ 副本地名与 area_seed 实际用词不一致；④ 数据无该 POI 但内容仍写（长江之心/夷陵广场 T1 缺）。

**执行方法（审计 + 逐项修正）**：
1. **审计脚本**：遍历副本 v3 所有 loc name → 跑 area_seed/spatial_hotspot 匹配 → 输出每个 name 命中的 area_seed 列表 + 解析到的 cell._center 坐标（`py` 一次性 grep `DATA/performance/yichang_L2_T1_*.geojson`）。
2. **逐项核对**：每个解析到的 cell 坐标 vs 真实宜昌地理（奥体/南湖/体育场/中南路/二马路/桃花岭/长江之心 等）——cell 是否真在该地标附近。
3. **修正原则**：副本 name 必须具体到能唯一命中一个 area_seed（如"东山"→"东山大道港城路口"或换更具体 POI）；数据无该 POI 的（长江之心）要么换数据里存在的沿江楼盘、要么标"无定位"不显 tip；多义时取最近 + 人工确认。
4. **验证**：webapp-testing skill 逐词 hover → 截图核对 tip 落点（用户明确要求过 tip 准确性，此处值得验证）。

**关联 memory**：[loc-anchor-by-data-not-coords](C:\Users\Hi\.claude\projects\d--Github-emotion-map\memory\loc-anchor-by-data-not-coords.md)（数据为准禁猜坐标）、[verify-with-webapp-testing-skill](C:\Users\Hi\.claude\projects\d--Github-emotion-map\memory\verify-with-webapp-testing-skill.md)。

### ✅ 地点锚定系统修 + sticky 最高级 + 词点击柱体橙 + 消极 3x（revision-log 5.27，承 efb0908，未自动验证交付肉眼验）

- **致命错修复（地点锚定）**：v2 副本硬编码 lngLat 是猜的（奥体误标→错 cell）。系统修：副本只留地名（locs=[name]），`_resolveLocAnchors` 去 grid 源点层按 area_seed/spatial_hotspot 含地名找真实 POI → 最近 cell。数据无该 POI→跳过 tip（不错指）。新 memory `loc-anchor-by-data-not-coords`。
- **sticky 最高级 bug（全局）**：hover 不覆盖 sticky 长显（词/块/tip）；`if(_polWordTipSticky) return` + `if(!_polBlockSticky) render`。新 memory `sticky-hover-priority`。
- **牵引线**：line 200+i×25（cap 300）stagger 避叠（v2 固定 300 太高且重叠）。
- **词点击→柱体橙**：词 click→`toggleStickyHighlight(locCells,'polkw:word')`（⊆ 块聚合域）；矩阵 click→块橙 `polmx`；释放 resetHighlightCellSet。
- **副本 v3 内容修正**（用户逐项）：二马路消极→历史感不强/没特点/业态不行（非拆没了）；噪音→体育场（修路）；内涝→南湖（逢雨必淹）；加装电梯→桃花岭扩量；烂尾→长江之心；堵车→中南路十字口；停车难+中南；没意思→打卡同质化。消极 3x（4-7 词含短句吐槽：商圈停车靠抢/中南路堵死/围挡挡路/老人爬楼难）。
- **process**：新 memory `verify-with-webapp-testing-skill`——前端验证用 webapp-testing skill 非 Playwright，默认不验交付肉眼验。本轮按此未自动验证。

### ✅ 极性深读 review 修正 + 地点 tip feature（revision-log 5.26，承 ea8e66f，Playwright 验证全通过）

- **review 修正**（用户两问）：① 矩阵 `_matrix4x5ByPolarity` 误用 Σ 点数 → 改"该极性点数>0 的单元数"（每格计1，与地图 filter 同口径）；② `_polarityBodyHtml` 漏抄占比 → 加回 `_cityTotalOf` 占比 + cellSize 话语。
- **关键词卡片照搬**：`_renderBlockKw` 复用 `.ov-kw-sp`（fill+词+地点淡灰+数字降序）+ 板块头单位 `（单位：个情绪点）`；综合 `_keywordsHtml` 也加单位。
- **副本 v2**：`{word,n,locs:[{name,lng,lat}]}`，含短句话题（开街烟火气足/楚超火爆），T1/T3×3×20，停车难→5 商圈、二马路/奥体→唯一。
- **联动+空态**：矩阵↔词互高亮；hover 块→瞬时词组（leave→清空回 hint 不残留）；click 块→sticky 长显。
- **地点 tip**（新 feature）：hover/click 词 → 对应聚合域·3D 柱体上方白线 300px + 胶囊（地点名，`.ov-unit` 字号浅灰）。`maplibregl.Marker` anchor bottom 锚最近 cell._center；cap ≤8。click 词→`.is-sticky` 橙填充+浮起+深字（综合/极性一致，改 `.is-sticky` 橙框→填充）。
- **UI 紧凑**：`.ov-pol-tabs` gap 2px + `.ov-pol-body` padding-top 10px（Tab↔内容隔离）。
- **时间规范**：新 memory `timestamp-no-weekday`——时间戳不写星期几（07-06=周一，反复误写周日）。
- **已知交互**：toggleGridViewMode 切 2D/3D pair 重选层致极性 tab 重置（既有行为，非 bug；3D 下生成+深读+tip 可用）。

### ✅ 任务1 完成：单元深读→极性深读重构 + Layers 子卡 + Toolbox 去极性 + Tab 条 sticky（plan `main-head-46250a6-...sequential-swing.md`，Playwright 验证全通过）

- **pivot**：用户否决上会话「Q2 推荐深读清单 + cluster①分级（单格大头针思路延续）」方向，改为**整体重构**——单元深读（单格级）→ 极性深读（极性·聚合域级），深读价值聚焦「支撑 4×5 什么行动」。
- **1-A Layers 子卡**：`sidebar.js` grid 类目按 `_ui.analysis` 拆「标准网格/指定单元」虚拟子卡（`subGroupRowHtml`，2px gap，双击折叠 `_groupFold` 合成 id）；`grid-tool.js` 层名瘦身去 `analysisLabel·sizeTag` → `T1·综合·file`。
- **1-B Toolbox 去极性**：`index.html` 删 `#grid-polarity-section`；`grid-tool.js` `selectedPolarity` 恒 overall；`collectPolygonLayers` 改 `isRangeLayer` 过滤（排除 grid/buffer 产物）+ label `（N 面）`。
- **1-C 极性深读 paint 就地切换**（替原设想 3 隐藏图层）：综合 grid fc 已带 `_grid_h_pos/neg/neu`+`_grid_n_pos/neg/neu`，切极性 = 改 `paint.gridField/gridStops/heightField`+`_polarityFilter`+`renderLayer`。生成时备份 `_overallPaint`。`map.js` addPolygonPaint/addHitLayer 透传 filter（条件展开，修 MapLibre `filter:undefined` 坑）。`panel.js` 删 `setCellOverview`/`cellEmptyHint`；`activateOvTab` cell→polarity；`main.js` `cell:selected` 不再切深读。
- **1-D 动态关键词 + 副本**：`_matrix4x5ByPolarity`（按极性重计 4×5）；hover/选中矩阵块 → `_renderBlockKeywordsFor` 查 `DATA/performance/polarity_deepread_keywords.json`（T1+T3 × 3 极性 × 20 块，规划/更新×设施/环境/文化块 4-6 词强项目味，`info-i` 标演示副本）填 `#ov-block-kw`。
- **1-E Tab 条 sticky**：`panel.css` `.ov-subtabs`（top:0）+ `.ov-pol-tabs`（top:30px）position:sticky + bg 遮罩。
- **验证**：Playwright 0 错误；子卡/层名/paint 切换（filter `_grid_n_pos>0`⇄`_grid_n_neg>0` 实测）/hover 关键词/回切还原全通过。承重全保（TOPIC_MATRIX_MAP/双 sub-Tab/enforceMutualExclusion/gridSig 等）。

### ⬜ 任务2 待启动（新会话）：极性深读·时间轴（T1→T3 成效动画）

- **关键决策点（新会话首问）**：地图柱体动画路线 A（JS rAF + setData，推荐）/ B（deck.gl 重引入）/ C（阶梯淡入）。
- **前置**：Overview 原地更新重构（panel.js 从 innerHTML 重建改 DOM 原地 tween——任务2 动画 + 本任务 hover 动态关键词都受益）。
- **副本已预置**：T1/T3 双副本本会话已建（`polarity_deepread_keywords.json`），任务2 直接复用。
- 详见 revision-log 5.25 + 交接卡 `memories/repo/session-handoff.md`。



### ✅ 已完成（plan `revision-log-5-19-misty-map.md`，Phase 1-3；待 F5 验）
- **P1 图层 L 优先排序 + L 徽章 + 手动拖拽保留**：
  - **排序键**（[`state.js`](frontend/js/state.js)）：`_layerTypeRank` 拆 `_layerLevelRank`（L1=0<L2=1，主键）+ `_layerPolarityRank`（overall<积极<中性<消极，末键）；`applyGroupOrder` 组内排序改 `(levelRank, timeRank, polarityRank)`——**L 数据优先于 T**（原 timeRank 压过 L 的 bug 修）。terrain 同理。
  - **手动拖拽保留**：新增 `_frozenCats` Set + `freezeCategoryOrder(cat)`；within-category 拖拽落定（[`sidebar.js`](frontend/js/sidebar.js) layer-row + 同 cat 多 group 两路径）→ 标 frozen；`applyGroupOrder` 跳过 frozen category 的组内排序（保用户手动序）；`addLayer` 解冻新层 category（让其按规则归位）。`renderLayerList` 仍无条件 `restackZ`（z-sync 与顺序解耦）。
  - **L 徽章**（sidebar.js `hintChip`）：grid/terrain 升 `"L1·G"`/`"L2·G"`/`"L1·E"`/`"L2·E"`（L=level，字母=工具类型）；L 前缀色 = 新增 [`levelPointColor`](frontend/js/state.js)（L1=`#FF9800` CONFIDENCE 橙、L2=`#3DBA9D` Positive teal = 情绪点层标签色）。
- **P2A L2 综合 Overview**（[`panel.js`](frontend/js/panel.js) tier3 综合分支 + [`panel.css`](frontend/css/panel.css)）：题头加 `（单位：个点）`（新 `.ov-unit` 细体同题头色）；countLine「共 N **条**」→「共 N **个**」（量词统一=情绪点）；**删 4 领域柱**（并入矩阵行标签）；饼图 1.8×（`.ov-pie svg` 104→187px）+ 图例字号 11→13px/dot 9→10px；归因矩阵题头加 `（单位：个单元）`；矩阵块圆角正方形（`border-radius` 3→8px 宽度不变）；行标签下加 domain 单元计数 `(N)`（新 `.mx-rowcount` 11px 粗体、`.mx-rowlabel` 改 column 居中）。新增 `_domainTotals`/`_unit` 辅助。
- **P2B L2 极性 Overview**（panel.js `_singlePolBody` + `_singlePolMatrixHtml`）：**极性总览只留 countLine 一句**（删 `ov-ov-bars-row` 4 领域+5 要素横条，已并入矩阵）；归因矩阵题头加 `（单位：个单元）`；块圆角；行标签加 domain `(N)` + **列头加 element `(N)`**（`.mx-head` 改 column 居中）。新增 `_elementTotals`。
- **P3 悬停橙黄**（panel.css）：`.mx-cell:hover` 加 `background:#ff9000 !important; color:#fff`（覆写内联 `_piColor`，浮起 scale 保留，sticky 选中态橙轮廓不变）；`.ov-dbar:hover` 加 `translateY(-1px)` 浮起 + `.ov-dbar-fill` `background:#ff9000 !important`。
- 验证：3 JS `node --check` 全过；**待 F5 验**（图层默认序 L1 在前/L2 在后、行标签 L1·G/L2·E 配色、手动拖后不被覆盖；L2 综合/极性 题头单位/量词/饼图 1.8×/矩阵圆角+行标(N)；hover 橙黄）。

### ✅ Round 2 + 小修（F5 反馈 5 项 + commit 前小修；待 F5 验）
- **P2C L1 网格/点层 Overview 分家 + 卡顿修复**：根因 `_fillL1Pies` PIP 每次 setOverview 重跑（数万点×9多边形阻塞主线程，2D/3D 卡）→ L1 网格删数据总览（仅矩阵 + 引言 + 4 维柱带占比 + 灰线 + 阴影，**零 PIP**）；L1 点层（热度分布）接管数据总览（双段总结 + 紫饼图 187px + 8 组团横条）；per-组团 PIP 缓存 `layer._tuanCls` + bbox 预筛。
- **中心城区计数改 area_tag**（[`panel.js`](frontend/js/panel.js) `_l1AreaTagCount`）：core+central_outer=15997 ✓（验 T2 全域 32524 / 中心城区 15997 / 占比 49%）、零 PIP、随数据公式化；产出率按 T ∈ 10/11/12%、L0=round(L1/rate) 倒推。
- **8 组团**（[`district-stats.js`](frontend/js/district-stats.js) `_TUAN_MAP`）：西陵/伍家岗/点军/小溪塔/高新区·生物产业园(生物产业园+龙泉绿心 合并)/龙泉/猇亭/白洋·顾家店。
- **P4 联动打磨**：`_applySync` >5 删最浅档（drop 底 1/3，仅中+高 alpha 0.5~1.0）；字色统一深字 #333（删白字混色）；地图聚合域高亮不变。
- **小修**：L1 网格无单元深读 → 隐藏 sub-Tab + cell:selected 守卫（[`main.js`](frontend/js/main.js) `isL1Grid`）；归因矩阵三处标题下加一句话引言（`_matrixIntro`）；L2 综合矩阵补 5 要素列头 `(N)`；矩阵块加阴影。
- 验证：JS `node --check` 全过；**待 F5 验**（L1 点层数据总览 + 网格不卡 + 联动深字 + 矩阵引言）。

### ⬜ 下一步（新会话推进）

**任务 A：已完成**（Feature 4 语义表 TOPIC_MATRIX_MAP + sim 锚点修正，见 revision-log 5.22）。

**任务 B-2：单元深读 12 词 cell ID 定稿**（任务 A + sim 锚点修正已完成，见 revision-log 5.22）
- 12 词锚点已验落点修正：楚超火爆→奥体(181) / 卷桥河露营→卷桥河湿地(82) / 江南绿肺→江南URD(22) / 大南门→ermawu(116) / 占道→二马路+居住(180) / 口袋公园→park_plaza(370) / 业态→商圈(463) / 社区服务配套→居住(276) / 网红→商圈+二马路(828) / 夜经济→场馆+滨江(644) / 停车难→核心商圈+中南路(1547) / 堵车→交通走廊(14)。
- ✅ 已完成（见 revision-log 5.23）：12 词典型格 cell ID 定稿（cellSize=400m 三时点合并，cell ID=格中心坐标）。后续前端实现机制（配置坐标列表 + 聚合后按坐标匹配格 feature）待新任务。
- 残余可调：停车难 1547 偏多+seed 落口袋 POI（缩 `_CORE_RADIUS` 或加概率门控）；江南绿肺 22 点军低密度（可扩 radius）。

**⏸ 搁置（不做）**：2D/3D 切换地图聚合域高亮保持（未决，根因+尝试见 revision-log 5.21）。

---

## 📅 2026-07-03（周五）

### ✅ 已完成
- **Task4 Overview 双层 sub-Tab + 单元深读增强 + 联动 zoom**（plan `main-head-commit-inherited-tide.md`）：
  - **双层 sub-Tab**：[`panel.js`](frontend/js/panel.js) setOverview/setCellOverview 改写进独立 `#ov-layer-pane`/`#ov-cell-pane`（不再互相覆盖，切换内容互不丢）；新增 `activateOvTab`（silent 避抖）；[`index.html`](frontend/index.html) `#overview-pane` 内嵌 `.ov-subtabs`（图层总览|单元深读，仅分析层显，28px/xs/品牌蓝下划线，轻于顶层 `.ptab`）。
  - **联动 zoom**：[`map.js`](frontend/js/map.js) `easeToCell`（质心 + zoom clamp[13,15.5]，替 `fitBounds` 避占满）+ `easeBackFromCell`（恢复进入单元前视野）；[`main.js`](frontend/js/main.js) cell:selected→切单元深读 + zoom in；cell:cleared/换层→回图层总览 + zoom out。issue/Table 行点击改纯 dispatch cell:selected（统一 zoom）。
  - **内容分层级不重复**：图层总览（总结向）= 极性 donut（conic-gradient）+ 4×5 宏矩阵 + Top5 排行（点击深读）+ 治理柱；单元深读（微观，指向 4×5）= 该单元 domain×element 桶定位 + 桶均值 + 极性分位条 + 归因链 + 建议。
  - 验证：6 JS node --check 全过；待 F5 验双 Tab 切换 + 单元 zoom（不占满）+ donut/分位。
- **Task3 指定区域演示（更新单元 + 用地筛选）+ 上传限制 + 搜索历史**：
  - **更新单元**：核验 preset 150 面/119 碎面（与用户"20~40"矛盾，bbox 跨整城）→ 用户重导干净矢量；[`range_selector.load_preset`](core/range_selector.py) nameField='编号' 时加载期注入「更新单元-NN」（不改原文件）；manifest nameField 修（更新单元→编号、行政区→MC）。
  - **用地筛选 400MB 服务端 ingest**：浏览器上传必 OOM/超时，新增 [`ingest_landuse_preset.py`](SCRIPT/ingest_landuse_preset.py)（`--inspect` 列 DLMC + 建议映射；`--split --map` 按 DLMC 拆类 → dissolve → 简化 → WGS84 落盘 + 更新 manifest）。用户数据=单 GeoJSON 全用地，按 DLMC 拆商业/公园广场/居住。**待用户放数据到 `DATA/raw/` + 跑 inspect 确认映射**。
  - **上传限制**：[`dialog.js`](frontend/js/dialog.js) `SIZE_BLOCK` 80→200MB；[`range-presets.js`](frontend/js/range-presets.js) '+' 加 >200MB 守卫。
  - **搜索历史**：[`search-bar.js`](frontend/js/search-bar.js) 单条「×」+「清除全部」+ css。
  - 验证：3 新单测过（编号注入 + ingest inspect/split）；pytest 116 passed，5 fail 均预存在/环境（h3 未装→hex、geocode 离线、test_capabilities），零回归。
- **performance 文件夹同步**：`.gitignore` 删 `DATA/performance/`（197MB/12 文件入库）；AMAP_KEY 核验一致不动。

- **Overview 大改（视野-数据-结论同步）+ zoom 修 + toolbox 保 Range + 用地 ingest**（plan 同文件，P0-P6）：
  - **P0 zoom stacking 修**：`easeToCell` 进入单元层固定 `_cellModeZoom` 一次，同层切格只 pan 不抬（修"越点越低"）；`isRangeLayer` 抽 state.js，grid/heatmap 独占关他保 Range 层。
  - **P1 Overview 4 板块**：层级切换（sub-tab→深灰 #384555）/ 标题（单行 `L2·综合·T3·标准网格·400m`）/ 数据属性（3 行：文件名·样式计数尺寸·坐标系格式，`layer.crsInfo`）/ 数据分析；间隔 4px。
  - **P2 数据总览**：SVG 5 极性饼图（slice pop-out + click sticky）+ 4 领域柱（数字入条）；`highlightCellSet` 基础设施（tip-popup，橙 #ff9000/opacity 1.0 多 feature 叠加）。
  - **P3 归因矩阵美化** + hover/click→地图同步（domain×element 桶格）。
  - **P4 关键词**：`KEYWORD_TABLE`（4×5×2 网感词）→ Top5 正/负两列 + 次数条，点击→top-N 最强聚集 fitBounds。
  - **P5 用地 ingest**：修 `_detect_geographic` Polygon 嵌套 bug；跑 390MB 三调→拆 商业/公园广场/居住 3 preset（0.1-0.6MB）。
  - **P6 视野-数据-结论同步性** 写入 CLAUDE.md 演示逻辑链（铁律）+ memory。
  - 验证：7 JS node --check 全过；pytest 116 passed/5 预存在零回归；待 F5 验饼图/矩阵/关键词交互 + zoom + 4 板块。
- **Overview 视觉/交互精修（9 项反馈）**：
  - **Range 图例**：矩形线框+面域填充（同步线/填充态），名称=层实际名。
  - **全局"i"**：`.info-i`（灰填圆+CSS tooltip）+ Overview 三题头行内提示迁入。
  - **板块样式**：去线框+阴影加深+灰填充；属性行1 小浅灰、行2/3 粗；三部分灰色横线分隔；题头深灰；sticky 白色外轮廓。
  - **数据总览**：饼图 +20%、图例纵向小字去粗（色同地图极性图例）；count 行"共 N 条·积极/消极/中性"替均分。
  - **归因矩阵**：色板活泼（中性蓝非灰、Material 600）；去首行缩进（行标列 64→42 + 去"城市"前缀）。
  - **关键词**：3 列（正/中/负）+ KEYWORD_TABLE 网感重写（地铁通了/盼BRT/红灯长/网红打卡点/夜经济/噪音大/老旧小区/断头路…）+ 点击高亮 ~10 格。
  - **饼图选中逻辑**：点数>阈值(积极/消极>10、中性>1) 且 占比>40%。
  - **3D 高亮**：选中柱体升高 2× + 橙 #ff9000 + 100%（修与 2D 同效）。
  - 验证：4 JS node --check 全过；pytest 116 passed/5 预存在零回归；待 F5 验。

- **Overview batch-2 精修（11 项反馈 + skill 扩充，plan `main-head-9bff353-overview-elegant-fountain.md`）**：
  - **图层互斥/Overview 追随**（任务6/7）：[`state.js`](frontend/js/state.js) `enforceMutualExclusion`/`isToolAnalysisLayer`/`isEmotionPointLayer`（B 组分析层互斥、A↔B 不共存、同源极性保留、保 Range）接入眼睛/工具生成/视角切换；[`main.js`](frontend/js/main.js) `refreshOverview` 追随可见层——**修换层 Overview 不匹配 / 2D·3D 提示串台**。
  - **橙柱易选+深读**（任务9）：[`tip-popup.js`](frontend/js/tip-popup.js) `pickHLCell`（橙柱命中优先，修点橙柱选中背后格）+ `focusCell`（单格橙原高、其余取消）；click/hover 优先橙柱；cell:selected 同步清 sticky。
  - **选中橙框**（任务8）：饼图/矩阵/关键词 sticky → 橙黄 #ff9000 4px；修**关键词框被 track overflow 裁切** → 改挂 track。
  - **"i" 浮窗**（任务1）：`position:absolute` 被右栏裁切 → `position:fixed` 单例 `#info-i-tip`（浅灰底深灰字 10px）。
  - **3D 重叠/穿模**（任务4）：悬停升起柱 overlay 0.9→**1.0 不透明**（修两色重叠/共面穿模闪烁）。
  - **视觉小改**：去"数据分析"标题；count 行单行无省略；横条数字深灰；矩阵全称"城市规划"+新序(规划/更新/运营/治理)+左齐；饼图+图例整体居中。
  - **关键词 Top10**（任务11）：标题+slice 5→10+点击高亮 5→10；`KEYWORD_TABLE` 用用户勾选 30 词按 4×5 桶重填；表头细体。
  - **skill 扩充**：装 web-design-guidelines + code-review-and-quality（npx）；写 `~/.claude/CLAUDE.md` 全局规则；**4 个 claude-plugin 待回家开 VPN 装**。
  - 验证：24 JS node --check 全过；待 F5 验。

- **演示数据 narrative_zone + 单极性 Overview + 排版/3D/排序/z-order 七项**（plan `main-head-docs-elegant-sparkle.md`）：
  - **item1 数据叙事片区**：[`performance_config`](SCRIPT/performance_config.py) `NARRATIVE_ZONES/POLARITY/BIAS/POI_NARRATIVE_ZONE` + `pick_*` 加 `narrative_zone` 参；[`sim_performance_data`](SCRIPT/sim_performance_data.py) `classify_narrative_zone`（ermawu>riverside 几何优先→residential/traffic/commercial POI 类别→general）+ 滨江带几何(长江水体∩cc buffer 400m) + `validate_45` 打印片区 breakdown；**停用 `apply_anchors`**（与 narrative 弧冲突）。宜昌新闻调研锚定（滨江25km绿廊/加装电梯一拖二/东山大道拥堵/二马路修旧如旧）。
  - **item2 综合排版**：`_barsHtml` 通用横条（全称+加粗，领域 #4876FF / 要素 #836FFF），数据总览拆**双行**（饼图+图例横排一行 / 4领域一行）；`.ov-dbar-*` 加高(15→18)白字加粗。
  - **item5 单极性 Overview**：`_isSinglePol(polarity!=='overall')` 分流→`_singlePolBody` = 极性点数 + 4领域+4要素横条 + 归因矩阵(count 三级紫 #6A5ACD/#7B68EE/#8470FF) + 关键词 Top10(词 1/3 + 地点 Top5 2/3)；新色源 `DOMAIN_BAR_COLOR/ELEMENT_BAR_COLOR/POL_MATRIX_TIERS`。
  - **item3 选中 3D 穿模彻底修**：[`tip-popup`](frontend/js/tip-popup.js) `focusCell`/`_applyHL` 高度 → **定高 `mh+EPS_HL`**（不随 hf 缩放，恒全图最高 → 不被邻柱遮挡、易点中、不穿透背后；严格高于原柱 → 无共面 z-fight/闪烁）；`_hlKeys` 跟踪 + `maybeCellHover` 跳过 sticky/focus 格防两 overlay 竞争。
  - **item4 隐藏 cell-popup**：[`popup.js`](frontend/js/popup.js) `CELL_POPUP_ENABLED=false` 开关（保留 cell:selected dispatch + 函数/DOM）。
  - **item6 图层排序规则**：[`state.js`](frontend/js/state.js) `_groupOrder` 改 L数据→KDE→空间聚合→Buffer→Range；`applyGroupOrder` 多键稳定排序（groupRank + timeRank T1<T2<T3 + typeRank 热度<综合<极性）。
  - **item7 z-order 漂移修**：[`sidebar`](frontend/js/sidebar.js) `renderLayerList` 无条件 `restackZ`（安全网）+ [`map`](frontend/js/map.js) `setViewMode` 末尾补 `restackZ`（修 pair render 先于 reorder 致 stale）。
  - **item1.4 地名烘焙**：[`spatial_analysis`](core/spatial_analysis.py) `_attach_4x5_attrs` 加 `place_name`（spatial_hotspot 多数）供单极性地点 Top5。
  - **item1.3 文本池**：[`emotion_corpus.json`](SCRIPT/poi_data/emotion_corpus.json) 加 narrative_zone 键 ~50 条 + 重建池（202/286，71%）。
  - **item1.5 sim agent 文档** 更新 narrative_zone 方法论 + 本机约束。
  - 验证：9 文件 node --check + py_compile 全过；**全量数据重生顺延办公机**（家机缺 baidu-heatpoints）；待 F5 验。

- **单极性 Overview + 3D 橙柱选中 F5 反馈精修（6 项，07-04）**：
  - **item1 橙柱强制不可穿透 + 选中拉长**：[`tip-popup`](frontend/js/tip-popup.js) `_hlFeatures`+`pickHLByLngLat`（地理 contains 兜底）+ `_applyHL` 高度改**原柱高×factor**（hover 1.2/click 1.5）；[`popup`](frontend/js/popup.js) cell 点击 `pickHLCell||pickHLByLngLat`（鼠标在橙柱格子内强制选中、不穿透背后）。
  - **item2 外扩嵌套消闪烁**：`_bufferFeature(1.02)` 橙柱 footprint 绕质心扩 2% → 嵌套原柱 → 消侧面共面 z-fight。
  - **item3 数据条加宽白字**：[`.ov-dbar-fill`](frontend/css/panel.css) min-width 34 + 右齐白字（短条色块托底）+ 4领域/5要素两栏顶齐；全局规则：fill=白字/track 浅底=深灰字。
  - **item4 矩阵三色拉开**：`POL_MATRIX_TIERS` → #A020F0/#9370DB/#D8BFD8（深/中/浅，替旧三紫太近）。
  - **item5 countLine 修正**：total 含主级+非常级（修"消极 899/非常级 7551" vn>total bug）+ `_cityTotalOf` 反查 group 占比 → "偏X情绪点 X 个，占城市 Y%"。
  - **item6 关键词地点横杠**：记下待办公机重生数据（旧 L2 无 spatial_hotspot；后端 place_name 逻辑已就绪）。
  - 验证：4 JS node --check 全过；待 F5 验橙柱选中/不穿透/不闪烁 + 单极性总览字色/矩阵色/计数。

### ⬜ 下一步
- **【回家装 skill · 已完成 ✅】** 家机已装：4 个 claude-plugin（superpowers v6.0.3 / ui-ux-pro-max v2.6.2 / planning-with-files v3.1.3 / claude-mem v13.9.3，全 enabled）+ 2 个 npx skill（code-review-and-quality 正常装 / web-design-guidelines 手动装 CLI 发现不到）+ 家机全局 `~/.claude/CLAUDE.md` 补 2 条 skill 规则。
- **【待 F5 验 batch-2 + 本批】** 图层互斥切换 / 橙柱选中 / 三处橙框 / i 浮窗 / **3D 选中不穿模（item3）** / 关键词 Top10 / **cell-popup 隐藏（item4）** / **综合双行排版（item2）** / **单极性 Overview（item5：4领域+4要素+三级紫矩阵+地点Top5）** / **图层新排序序（item6）** / **新生成极性网格 z-order 不漂移（item7）**。
- **【待办公机跑全量 sim】** `DATA/baidu-heatpoints/` 家机缺（gitignore）→ 办公机 `git pull` + `py SCRIPT/sim_performance_data.py` 重生 6 数据集（narrative_zone 弧落地）+ 看 `[CHECK]` 各片区极性占比核验。文本池已本机重建（随 commit 同步）。
- **【待 F5 验】** Task4 双层 Tab + zoom：导入 L1/L2→生成网格→点单元→ donut/分位/4×5 递进。
- **【待用户数据】** 更新单元干净矢量替换 `presets/更新单元.geojson`；400MB 用地放 `DATA/raw/` → 跑 `ingest_landuse_preset.py --inspect` → 确认映射 → `--split`。
- Task5 AI 问答重做；POI/地名纠错（后期）；F5 验后微调。

---

## 📅 2026-07-02（周四）

### ✅ 已完成
- **本周重点四件套（底图 / 图层交互 / 色段条取色器 / Range 线宽）**——用户初始实现 + 补 buffer 一致性 + fitToLayer bbox 修正：
  - **①天地图·影像无注记底图**：新增 `tianditu-img-nolabel`（影像无注记，`apps/static/tianditu_img_nolabel.json`，仅 img 无 cia）+ 底图 popover 与 `tianditu-img` 影像组并列 + `setBasemap` 容器背景色；与 CARTO 三素图同属"干净底图"（数据叠加首选）。（初版误加矢量无注记，按用户指正改影像无注记。）
  - **②图层行单击 / 双击交互**：`selectLayerRow` 单击加 `openRightPanel()`（弹右栏 Overview/Table；仅约束 `layer:selected` 事件不自动弹栏——行点击是显式入口，承重④不变）；`.layer-row` dblclick → `fitToLayer`（递归 walk **全坐标**算 bbox，Point/Line/Polygon 通用，非仅首点）→ fitBounds 飞至。
  - **③要素色板重做色段取色器**：`RANGE_GRADIENTS` 11 条色板（综合彩虹[饱和度优化降彩] / 综合极性[红→灰→绿发散] / 积极·消极·中性 + Viridis/Magma/Cividis/Turbo/Spectral + 日落暖金）；抽导出 `renderColorPicker` 共享 settings+buffer——**每条=一行离散色段**（复用参数面板 ③ 的 `hm-style-bar`/`hm-style-seg`，等宽实色块非渐变），**点色段取该段预设色**（离散不让自由调色），**去圆角方形色块 + 去色段前文字标签**，仅留色段；buffer 复用同源取色器（点/线/面/缓冲要素按钮色板统一）。（初版用渐变条+连续插值，用户多次强调要"色段"非"色带"、不让自由调色，改离散色段。）
  - **④Range 线宽调优**：默认 2→**1px**（addLayer polygon/line + addPolygonPaint/addLinePaint 兜底 + settings 滑块默认）；hover 加粗 `baseW+3`→**`baseW+1`**（默认 1→2px）；`baseW` 改 live 读 `layer.paint.lineWidth`（settings 调线宽后 hover 同步）。
  - 验证：5 JS node --check 全过；待 F5 验 6 底图格 / 行单击弹栏·双击飞至 / 色段条取色 / 范围线宽 1px+hover 2px。

- **演示数据最终版（百度热力点锚定 L1/L2）+ 地点层扩中心城区 + 模拟 agent**（plan `3-curious-bachman.md`，Task2+1 做透；3/4/5 后续）：
  - **Task2 地点层扩中心城区（AMAP_KEY 缺→fallback）**：核验 POI 仅覆西陵伍家 + AMAP_KEY 未配。`sim_centralcity_poi.py` 百度位置+真实类别分布+水域屏蔽 → 2499 sim POI；`place_layer` 双源合并 3769。
  - **Task1 引擎** `sim_performance_data.py` + `performance_config.py`：百度去聚合（`Poisson(value×0.639)`+jitter，全域~34k/快照）；area_type 2 级（core/central_outer）驱 4×5 倾斜（POI 继承 80% + 区域 bias×时间，0 空格）；极性弧 core T1 neg55%→T3 pos62% + 7 锚点迁移；外环纯热度点；L2=cc 子集→SnowNLP。产出 `DATA/performance/yichang_L1/L2_T1-T3`（schema 兼容）。
  - **Task1c/1d**：`api/routes` + `config.PERFORMANCE_DIR` 合并下拉；`sim-emotion-data.agent.md` 操作手册。
  - 验证：3 轮迭代；L1 34k/L2 17k、4×5 0 空格、score 弧 0.44→0.54→0.62、pytest 115 passed/1 预先存在**零回归**；AMAP_KEY 到位一键切真实高德。待 F5 端到端验（导入 L1 全域点阵 + L2 中心城区核密度 + 切 T1→T3 看递进 + grid 指定单元 4×5 归因）。
- **Range popup 收起交互反转**：原"点面域不收起、点轮廓 toggle"→ 改"非轮廓线即收起（含面域）"。`classifyMapClick` 重分 `range-outline`(line/hit) / `range-fill`(面域)；handler outline→开/保持、fill+blank→收起；删死码 `isRangePopupExpanded`。待 F5 验。
- **放大镜外环统一加载指示器**：`geocode-loader.js` 泛化（`track(kind,p)`+`trackGeneration`，分色 geocode 蓝/generation 青，完成统一橙 #F5A623 替原绿，stroke-width 不变）；search-bar 按 snapshot.color inline 设环色 + 去 is-collapsed 限制；生成 4 处接入（grid runGrid/runAggregate、buffer runBuffer、heatmap runTerrain）。以后新读取加 `KIND_COLORS` 一行即可。待 F5 验生成青→完成橙、反查蓝→橙。

---

## 📅 2026-07-01（周三）

### ✅ 已完成
- **Task 2.8 popup/3D 七项实测反馈修复**（续 feature/kde-l2-3d，Task 2.7 后用户实测 7 个问题）：
  - **①胶囊颜色对齐柱体**：`popup.js` 胶囊原用 `rampColor(gridStops拍平)`（等距 5 段插值，丢 stop 位置）≠ 柱体 `_gridColorExpr`（按真实 stop 位 interpolate）→ 同值不同色（Task 2.7 漏网第三处旧公式）。`state.js` 新增 `rampColorAt(stops,val)`（按 `[pos,hex]` 真实位置 lerpHex，镜像 MapLibre）+ `export lerpHex`，胶囊改用→= 柱体同色。
  - **②近邻 POI 列表·去距离**：「·41m」=最近POI→格中心距离（易混淆），后端只返 1 个。改 `place_layer.reverse` 返 `nearest_pois`(top-5)+`poi_count`(500m 计数)；前端 `_locLine`(tip)去距离加「等N处」+ 新 `_locBlock`(cell)详列近邻 top-3（纯文本+CSS pre-line 换行）。
  - **③默认格 200→400m**：DEFAULTS + HTML 输入框/滑块 3 处同步。
  - **④tip 地点自动换行**：`tp-loc` 去 nowrap 加 word-break，卡 height:auto 跟随撑高。
  - **⑤地点加载进度环**：新 `geocode-loader.js`（inflight 计数+模拟进度 10→90→100/绿/停1s/淡出）；`search-bar` 收起态放大镜外圈 2px SVG 环（灰→绿）；popup/tip reverseGeocode 包 trackGeocode。仅地点反查。
  - **⑥悬停升高基准过时**：`showCellHover` 读闭包 ui.maxHeight（要素按钮调拉伸后过时）→ 改读 live `layer.paint._ui`。
  - **⑦3D 透视**：默认 FOV 36.87°（长焦压缩、疑似轴测）→ `setVerticalFieldOfView(55)` 加宽 + `setLight`（viewport/[1.5,210,45]/.6）方向光明暗立体；FOV 设一次（camera 抗 setStyle）、light style.load 重敷。
  - 验证：7 JS node --check + 2 py compile 全过；视觉/异步交用户 start.bat（后端改 place_layer）+F5 肉眼验。
- **Task 2.9 popup/3D 第二轮实测反馈（6 项）**：
  - **①3D 上沿白条**：FOV55+pitch60 视口上沿露 #map 白底（暗底图下刺眼）→ `setBasemap` 按 basemap 设容器背景（dark-matter→深灰等），露空区融入。
  - **②进度环 2→4px**：circle r=14→13（避 stroke4 裁剪）+ RING_C 同步。
  - **③方向光改东北+降曝**：position 语义=[r,方位°(0=上/北,顺时针),极角°(0=正上,90=水平)]；原[1.5,210,45]光从左下→改[1.5,45,60]东北来光（亮面朝 NE）+ 极角 60 侧光强对比 + intensity .6→.5 降曝。
  - **④cell-popup 排版对齐 tip-popup**（字号不改）：4 行=极性判断(词+色)/积极·中性·消极(计数)/聚类程度(高/中/低（点数）)/置信度；cp- CSS 镜像 tp-。
  - **⑤悬停升高 1.5→2×**。
  - **⑥悬停高亮**：4px 白外轮廓不可行（fill-extrusion 无 outline，sleeve 厚度随缩放失效）；白色顶冠方案评估后弃用 → 仅保留 2× 升起 + 同款 color（不变色）。
  - 验证：4 JS node --check 全过；光照观感激用户 F5 肉眼验（均可一行调参）。
- **Task 2.10 3D 柱体高度算法 + 默认透明度**：
  - **①高度扁平根因 = `_grid_h` 分位归一化**（preprocessGrid 按 q25/q50/q75/qMax 排名均布 0~1，抹平点数差）→ 改**点数幂次保持量级** `_grid_h=clamp((pc/p95)^1.3,0,1)`（p95 抗离群、γ=1.3 放大高值；counts 由 pc×conf 改纯 pc）。L1 颜色同读 _grid_h（矮柱暗红高柱金黄）。用户选 γ=1.3。
  - **②默认透明度 100%→90%**：DEFAULTS + HTML 滑块 + terrain(0.92→0.9) + hover overlay(写死1→读 liveUi.extrusionOpacity) 四处同步。
  - 数据侧不动（KDE 采样本就长尾，算法是扁平唯一根因）。
  - 验证：4 JS node --check 全过；激 F5 **重生成网格**肉眼验高度差/透明度。
- **Task 2.11 L1 柱高 clamp 修复 + grid-warm 色板重调**：
  - **①34/44 等高根因=clamp**：诊断 L1 数据(400m 格) point_count 分布 p95=17-19/max=42-80；Task 2.10 `_grid_h=min(1,(pc/p95)^1.3)` 中 p95 ref 太小→≥19 点全 clamp 到满高。改 ref `p95→max`（零 clamp），γ 保 1.3（用户选）。L1 T1(max=73)：34→372m/44→522m（差 150m，不再等高）。
  - **②grid-warm 色板重调**（红黄各半+自然过渡）：改 6 段 `#8B0000/#C92A20/#EE5A28/#FF9900/#FFC63C/#FFDF00`（暗红低端不变、#FF9900 中、#FFDF00 顶）；normStops 后 FF9900@0.500 红黄正中分界（node 验证）。
  - 验证：2 JS node --check + 色板归一化数学；激 F5 重生成 L1 网格肉眼验。
- **Task 2.12 柱高 γ→sqrt + 默认柱高 2000m + L1 色板红段收窄**：
  - **①趴地根因=γ>1 不适合长尾**（max=73/q50=3，γ=1.3→1→4m 趴地）。改 γ 1.3→**0.5（sqrt）**（ref=max 不变）：1→234/3→405/6→573/12→811/34→1365/44→1553/73→2000m。
  - **②默认柱高 1000→2000m、上限 3000→4000m**（DEFAULTS+HTML 滑块；terrain 不动）。
  - **③L1 大面积红根因=红段占 0-0.40 而数据主体 _grid_h 落此区**：改 grid-warm stops 红段收窄到 renorm 0-0.15、过渡段 0.15-0.50 对齐数据主体；renorm `[0/0.15/0.30/0.50/0.78/1.0]=[#8B0000/#C92A20/#F06428/#FF9900/#FFC63C/#FFDF00]`。q50-q90 落红橙→橙黄中间过渡段，不再大面积红（node 验证）。
  - 验证：2 JS node --check + 色板数学 + γ 柱高；激 F5 重生成 L1 网格肉眼验。
- **Task 2.13 高度 offset 阈值 + L2 极性网格语义重做**：
  - **①高度 offset**：用户要"1-2 点趴地、3 点起跳~234m、3-5 点 200-500m"。幂次做不到（需阈值跳）。改 `_grid_h=((pc-2)/(max-2))^0.5`：pc≤2→0 趴地、3→237m、73→满高（node 验证）。
  - **②L2 极性网格语义重做**（原用占比错，应=该极性聚合程度=数量+程度）：(a)新增 `_grid_n_pos/neg/neu` 点数 + `_grid_h_pos/neg/neu` 高度；(b)gridStyle field 占比→分极性高度（颜色+高度同源）；(c)heightField 按 polarity 选；(d)green/red/blue-3 ramp 3→6 段；(e)popup _cellKvRows L2 极性分支（程度判断+该极性点数+聚类+置信度）；(f)tip metricText L2 极性分支（显该极性点数）。例：11/4/6 格积极网格→高度/颜色∝11 + "积极点数 11/非常或偏积极"。
  - 验证：4 JS node --check + offset 数学；激 F5 重生成 L1/L2 网格肉眼验。
- **Task 2.14 极性网格去数量为 0 的格（hotfix）**：Task 2.13 后极性网格仍渲染该极性点数=0 的空格。新增 `filterPolarityZero` 在 preprocessGrid 后过滤（L2 积极/消极/中性剔 `_grid_n_*=0` 格，综合/L1 不动），square+zonal 两处调。验证：node --check；F5 重生成 L2 极性网格验无空格。
- **Task 2.15 区分 pc=1/2 高度（hotfix）**：Task 2.13 offset=2 让 pc=1,2 都=0 无区分；用户要 1→50m, 2→100m。改 `heightOf`：pc≤2 线性 val×0.025，pc≥3 保持 offset+sqrt。全局（含分极性）。node 验证 1→50/2→100/3→237/73→2000。
- **Task 2.16 极性 popup 4×5 + 视角按钮 + 图层栏紧凑**：
  - **①极性 popup 聚焦该极性+4×5**：去"极性程度判断"行（图层已明示极性），加"治理要素 domain×element"+"问题识别 issue_label"；tip tp-valence 极性网格显治理要素（替综合判断）。
  - **②视角按钮**：modeChip span→button.layer-view（字面 2D/3D，参考要素按钮）；点击 setViewMode 切；renderLayerList 配对去重（skipIds，2D/3D 合并一条）；切换后 layers:changed 自动重绘。
  - **③图层栏紧凑**：GRIP 移至 del 左侧；.layer-row gap spacing-2→1px。
  - 左下角 2D/3D 按钮暂保留（要删再删）。验证：3 JS node --check；F5 验。
- **Task 2.17 眼睛关闭后 2D/3D 分裂+视角按钮失效（bug hotfix）**：根因 ①去重只跳过"有可见配对的隐藏层"→ 都隐藏时都不跳过→分裂；②分裂后都隐藏→setViewMode filter(visible) 空→视角按钮失效。修：①去重改按 sig 配对组（不论可见，每组选代表：可见优先‖最近切 mode‖兜底最后）→ 始终一条；②新增 toggleGridViewMode(layerId) 针对该 sig 切（不依赖 visible）→ 修失效；③_lastGridMode 记 sig→最近切 mode，选代表避切回时选错。验证：2 JS node --check；F5 验眼睛关闭后仍一条 + 视角按钮有效。
- **Task 2.18 视角切 3D 后 2D/3D 同显混乱（bug hotfix）**：用户报"点视角按钮后 2D 3D 同时显示"。根因 ≠ toggleGridViewMode（该函数正确，map 只一个 3D 层 visible）；真因 = `addPolygonPaint` 3D 层 `if(p.fillOn)` 仍加 fill 色块(地面) + fill-extrusion 柱体 → 同一 3D 层渲染"地面色块+柱体"视觉判为"2D 3D 同显"。修：3D 跳过 fill（`if(p.fillOn && !isTool3d)`，柱体自含面不需地面色块）；2D 仍 fill。验证：node --check；F5 验切 3D 后只柱体无色块重叠。
- **Task 2.19 极性 cell-popup 地点换行下排被遮挡（bug hotfix）**：`.popup-text` 通用 `-webkit-line-clamp:2 + overflow:hidden`，cp-loc 继承 → 地点 `_locBlock`（区·街道\n近邻列表）换行超 2 行被切。修：`.popup-cell .cp-loc` 重置 `display:block + line-clamp:unset + overflow:visible`，地点任意行数不截断。 | `frontend/css/popup.css` |
- **Task 2.20 popup 间距→2px + 展开态自适应无滚动条**：①全局 popup 属性信息间距压缩 2px（popup-text margin-bottom / popup-kv gap / kv-row gap / cp popup-kv gap）；popup-kv flex:0 0 auto。②.popup 去 min/max-height + overflow-y:auto → 纯自适应高度无滚动条；padding 收紧缩高。验证：CSS；F5 验紧凑无滚动。
- **Task 2.21 cell-popup 改"属性：值"横排缩高 + 拖拽后切视角跳序修复**：①cell-popup kv 改横排（_cellKvRows 返元组、渲染 kv-row grid auto 1fr），kv-v 字号 2xs+bold（同属性字号、粗体），每行单行缩高；删 cp-row 系列 dead CSS。②拖拽后切视角跳序根因 addLayer push pair 末尾→修：toggleGridViewMode/setViewMode 每次切 reorderLayers(pair, l) 接替原层槽位。验证：2 JS node --check；F5 验。

### ⬜ 下一步
- **【待 F5 验】** Task 2.8 七项：start.bat→F5→重生成网格/地形，验①胶囊=柱体色 ②tip「等N处」/cell 近邻列表 ③默认 400m ④tip 换行 ⑤进度环爬升→绿 ⑥调高度后悬停升起正确 ⑦3D 远近高差+明暗
- Overview 深化（项 4）本周偏后
- terrain 3D 重做已搁置；待用户定：range tooltip 迁移 / Task 3 热点图 / Task 2.2 时间轴

## 📅 2026-06-30（周二）

### ✅ 已完成
- **poi_4x5_map 重写为高德→4×5 单一权威源（修 `_L1_FALLBACK` 缺口）**：承重 note 10 候选——查证 `BAIDU_L2_TO_4X5`/`_L1_FALLBACK`/`map_baidu_to_4x5` 为百度类名**零调用死码**（真实高德→4×5 只内联在 pull_amap_poi `AMAP_TYPES`，4×5 专属模块反无高德表=真缺口）。改：`poi_4x5_map.py` 删死码 + 新增 `AMAP_L1_TO_4X5`(高德 13 大类，值搬自 AMAP_TYPES) + `map_amap_to_4x5`；`pull_amap_poi.AMAP_TYPES` 改经表派生 domain/element（单源，4-tuple 形状不变）。**不改 generate_l1_mock 数据流**（seed 值不变→Task 2.7 已测 L2 数据零变化）。验证：自检 sum=1.0/entries=13 + import 接线 n=13 + pytest 115 passed（1 预存在失败 `test_capabilities` 非本次引入，stash 证实）。
- **tip-popup 扩展到 point 悬停**（统一悬停设计语言落地）：point 层原只有 cursor+click 高亮、**零 hover 文本**。改：`tip-popup.js` `bindTipPopup(layer,lid,uiOverride)` 接显式 ui + point 分支（同步 zone_name/area 不逐点 geocode + 极性分数 + domain×element）；`map.js` `bindPointInteractions` 接入。
- **Task 2.7 交互桥修复+增强**（cell-popup / tip-popup / hover 高亮 / 颜色校准；Overview 深化本周偏后）——三批迭代：
  - **修点击错格 bug**：`popup.js:pickCellFeature`（fill-extrusion > fill > line-hit 优先级）替 `feats.find(isCellFeature)`——根因 3D queryRenderedFeatures 返回被遮挡邻格 base fill、2D 边缘 20px hit-line 串邻居；点击路由+tip 悬停共用。
  - **cell-popup**：地点「区·街道·最近POI·距离」（后端 reverse_geocode always regeo extensions=all 返 district/township/street），drop「通用市区」；移除「平均分数」；kv 缩字号细体（对齐 Range）；ⓘ 解释后按用户要求移除（留 title hover）。
  - **tip-popup**：150→120px；地点同 cell-popup；「极性判断」行（5 级 valenceOf）；高度自适应（地点换行不截）。
  - **state.js** `valenceOf`/`valenceColorOf`（5 级）全站共用。
  - **颜色校准（重点）**：**piToNorm 固定分段映射**（grid-tool+后端 `_pi_to_norm` 同公式，对齐 valenceOf 阈值）**替旧 p95 对称拉伸**（后者数据相关致色带边界无法对齐判断=颜色不准根因）；terrain-9 中性段对齐 pi±0.15；`valenceColorOf` 改用 TERRAIN_*[2]/[1]（与色带同源，修字/卡不一致）。
  - **3D 悬停高亮**：`showCellHover` 整柱 overlay cellH→1.5× native transition 350ms 升起动画；**用与格层同款 color 表达式**（保 properties，修 rampColor 均匀间距≠实际 stop 位致升起变色）；**点击保持升起**（clearCellHover 仅 mouseleave 触发）；2D 品牌蓝亮粗描边。
  - 验证：node --check / py compile / piToNorm 数学 / pytest 10 passed（spatial）零新回归。**未 F5 实测**（Playwright 环境阻断）：start.bat→F5→**重生成网格/地形**（_grid_norm/_norm 在生成时算）→验颜色/升起/点击/字色。

### ⬜ 下一步
- **【待 F5 验】** Task 2.7 三批：重生成网格/地形验颜色(偏消极=红)/升起不变色/点击保持升起/字色对齐
- Overview 深化（项 4）本周偏后
- terrain 3D 重做已**搁置**；待用户定：range tooltip 迁移 / Task 3 热点图 / Task 2.2 时间轴

## 📅 2026-06-29（周一）

### ✅ 已完成（续 feature/kde-l2-3d · 演示逻辑链纲领首落地）
- **演示逻辑链提为项目全局纲领** → 写入 `CLAUDE.md`「## 演示逻辑链」（最高优先级：数据为表现力、演示为有用性）
- **P3 数据语义化重模拟**：`_norm`/`_grid_norm` 对称拉伸（张力根因，grid+terrain 同步）+ l1_confidence 局部密度自相关 + POI-anchored 4×5/三层极性（保叙事弧）
- **聚合层 4×5 归因（DEMO，L3/L4 删）**：`domain_top`/`element_top` + `issue_label`/`attribution`/`suggestion`，供 Task 2.7 popup
- **验证**：T1 pi=-0.13 / T3=0.47（叙事弧✓）、\|pi\|>1.2 约半数格（张力✓）、归因连贯（renewal×service neg→"老旧小区/物业"✓）；旧数据→`old-data/`；pytest 8 passed（2 h3 缺包 pre-existing 无关）。详情见 `revision-log.md` 5.14

### ⬜ 下一步
- start.bat 重启后端（加载新聚合/归因代码）→ 用户 F5 肉眼验张力与 4×5 配色
- **Task 2.7**：网格/柱体 popup + Overview 接 `domain_top×element_top` + 归因字段（演示链"交互→识别"桥）

## 📅 2026-06-28（周日）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 空间分析 P0 后端地基 | `core/spatial_analysis.py` `core/buffer_analysis.py` `api/routes.py` `api/schemas.py` `tests/test_spatial_analysis.py` `requirements.txt` | create_square_grid(F_006, snap-to-grid 4546→4326)；/spatial/aggregate + /spatial/grid(hex\|square)；h3+httpx 补装；F_005 补登；10 测试全过；hotspot/moran+PySAL 延后 P4 |
| 2 | ✅ | Grid工具5项修复+vibe策略 | `frontend/js/{map,grid-tool,sidebar,state}.js` `frontend/index.html` `~/.claude/CLAUDE.md`(新) | ①3D图层自动pitch55+暗色底图(dark-matter),2D复原原底图(setView3D+_pre3dBasemap记忆) ②图例linear-gradient→分段span(复用.legend-heat-seg) ③green-3/red-3/blue-3拉大对比(浅淡深深) ④2D透明度统一控件(fill-opacity读_ui.extrusionOpacity,2D/3D同滑块) ⑤要素按钮原地更新(editLayerId分支;按钮生成→调整) ⑥录入全局CLAUDE.md:调动次数优先(不派subagent/批量并行/合并修改) |
| 3 | ✅ | Grid视角/图例/透明度/2D-3D视图按钮(4项) | `frontend/js/{map,map-controls,grid-tool,sidebar}.js` | ①3D生成不跳视角:fitBounds后设pitch=60+style.load防setStyle吞+与map-controls统一 ②L2综合图例labels=消极/中性/积极(单色/热度=低/高) ③2D首次透明根治:grid paint显式fillOpacity=extrusionOpacity绕开addLayer默认0.3 ④2D/3D视图按钮(btnView)一键切换:setViewMode按数据签名配对独立层(无配对则同fc生成,渲染独立)+pitch+Light/Dark底图+generateGrid不再独占关grid层 |
| 4 | ✅ | Grid视图切换两下+独占修复(2项) | `frontend/js/{map,grid-tool}.js` | ①2D/3D切换要点两下:setView3D的once(style.load)race→第一下pitch回调没挂上(底图已切),第二下底图已dark跳过setBasemap才easeTo;改:移除_easePitch/style.load等待(maplibre setStyle不重置camera)→直接easeTo pitch(650ms顺滑,一次到位) ②生成新网格没关其他图层:上轮误改generateGrid跳过grid层(为视图按钮多层)破坏独占→改回独占关所有其他可见层(记memory:generateGrid独占与setViewMode配对两场景独立勿耦合) |

### 📝 开发日志

**关键字**：空间聚合分析, Spatial Analysis, 标准网格(方格 fishnet), 指定单元(zonal), H3, polarity_index, EPSG:4546, create_square_grid, snap-to-grid

#### 做了什么
- **P0 后端地基**：用户把核密度（连续密度场：KDE 地形+H3 密度分箱）与空间聚合（离散面域统计：方格/指定单元+Gi\*/Moran's I）拆为两个 Toolbox 功能。本期只做后端，为 P1-P3 铺地基。
  - `create_square_grid`(F_006)：snap-to-grid 只建有点的格（避免稀疏点生成巨量空格），EPSG:4546 量米制保证 50/200/400/1000m 精确，聚合 point_count/score_mean/五级极性/polarity_index，回 4326。
  - `/spatial/aggregate`(指定单元) + `/spatial/grid`(hex|square 统一入口) 端点，schemas 照搬 BufferRequest。
  - 补装 h3(P1 用) + httpx(端点测试)；补登 F_005(buffer，原 @track 未注册，rule 10)。
- **复用**：聚合统计复制 aggregate_by_polygons（不动既有函数，零回归）；CRS 范式照搬 create_buffer；端点结构照搬 /spatial/buffer。

#### 踩坑 & 收获
- **PySAL 重栈延后**：libpysal+esda 在 requirements.txt 声明但本 env 未装，且仅 P4 的 Gi\*/Moran's I 需要 → P0 不装、不接 hotspot/moran 端点（免留调用即 500 的死端点）。h3 轻量，为 P1 装上。
- **TestClient 需 httpx**：fastapi.testclient 在本 env 缺 httpx → 端点测试初失败；装 httpx 后全过（starlette 弃用警告指向 httpx2，httpx 仍可用）。
- **snap-to-grid vs 全 fishnet**：稀疏点下全 fishnet 会生成巨量空格；改为按点 snap 到格原点、去重后只建有点的格（与 create_hex_grid 行为一致）。
- **track 注册是运行时的**：MOD_SPATIAL 的 ID 不在 tracker.py 静态 `_REGISTRY`，而是各模块 import 时 `register_track_id()` 动态填。F_005(buffer) 之前只 @track 未 register → rule 10 漏洞，本次补登。

#### 🔜 下一步（新会话）
- **P1 核密度重组**：拆 综合/极性地形(去 L1/L2 命名)、移走情绪网格、加 H3 六边形(2D/3D, 橙黄-暗红)。/spatial/grid(hex) 已就绪。
- **P2 空间聚合骨架 + 标准网格**：新 Toolbox 项 + 步骤导航 + 标准网格(2D/3D, 3 极性)。/spatial/grid(square) 已就绪。
- **衔接**：plan `~/.claude/plans/majestic-marinating-cerf.md`（P0 已完成）。

---

## 📅 2026-06-27（周五）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | A1 三页架构文档整合 | `architecture.md` `decisions.md`(ADR-015) `prd.md` `dev-notes.md` `memory/three-page-architecture.md` | 三页=数据库→控制台→实时地图；当前聚焦控制台 α v0.1；L0-L4 双视角 |
| 2 | ✅ | B0 全局色彩 | `design/tokens.json` `css/tokens.css` `css/panel.css` | 8 处 #007afc→#4285F4；新增 card-fill #384555；Overview/Table 卡片深灰+浅字 |
| 3 | ✅ | B1 上端栏单层化 | `index.html` `css/layout.css` `css/toolbar.css` | 双层→单条深蓝 48px；面包屑递进；Import/Export/i 靠右白字 |
| 4 | ✅ | B2 左下 3 按钮集 | `js/map-controls.js` `css/map-controls.css` | 指针/测量/图层纵列于 5 按钮簇上方；initToolbar 选择器自动绑；measure 占位 |
| 5 | ✅ | B3 左端栏三区 + B6 随动复核 | `index.html` `js/sidebar.js` `css/sidebar.css` `css/layout.css` `css/tokens.css` | 手风琴→tab 互斥（Range/Layers/Toolbox）；删 Analysis/+Upload Range；区2 工具栏（初版深灰，row 6 修订为白底）；默认宽 240px；B6 Playwright 验左簇跟随零改动 |
| 6 | ✅ | B3·区2 工具栏修订（按参考截图） | `index.html` `js/sidebar.js` `css/sidebar.css` | 配色翻转：深灰底→白底+#384555图标+hover；顺序 [+][文件夹][方片叠加][眼睛][垃圾桶]…[漏斗 计数]；新增 #lp-add/#lp-group 占位；补漏斗 SVG；计数 textContent→querySelector 避免冲掉 svg |
| 7 | ✅ | B4 左端参数弹出栏 | `index.html` `js/param-panel.js` `js/settings.js` `js/heatmap-tool.js` `js/buffer-tool.js` `js/main.js` `css/param-panel.css` | 三参数入口（样式/核密度/Buffer）独立浮窗→统一 `#param-panel`（紧贴左栏右缘 + 随动 + 不可拖宽 + 默认隐藏）；1:2 分栏（左=样式 / 右=分析 子页签）+ 中灰 2px 竖线 + 右上 X；`<dialog>`→`<div>`、id 全保留，仅 showModal→面板显隐，**apply 链零改**；决策①核密度拍平单滚动 ②底图保留 top-right；Playwright 全链路验证（含核密度真生成） |
| 8 | ✅ | B5 色板圆角 + 品牌蓝查漏 | `css/settings.css` `css/sidebar.css` `css/panel.css` `css/toolbar.css` `css/dialog.css` `css/toast.css` `css/param-panel.css` `css/search-bar.css` `js/map.js` | `.swatch` 50%→圆角矩形(--geojson-radius-md 6px)；残留旧蓝 #007afc/rgba(0,122,252) 清零——半透明→color-mix 派生、回退值→#4285F4、toast --geojson-brand 幽灵 token 修复、map.js 回退；保留 PRESET_COLORS/arch-diagram 内容色 |
| 9 | ✅ | A2 UI 层文档（Martin 收尾） | `docs/decisions.md` `docs/spec.md` `docs/ui-redesign-plan.md` `memory/martin-ui-redesign.md` | ADR-016（Martin 导航范式决策：三区左栏+悬浮参数栏+胶囊选项集+品牌蓝单源，落地 B0-B5）；spec §3.4 前端导航架构规格（§3 定位注改指 §3.4）；ui-redesign-plan Phase 4（B0-B5 落地，标注 Phase1-3 已被 ADR-012 超越）；memory martin-ui-redesign 承重约定 |

> 💡 Martin 导航重塑全部完成（B0-B5 + B6 + A2 文档，ADR-016）→ 控制台 α v0.1 UI 主线收口。下一步可推进 L3 语义/L4 归因接口、或空间分析引擎 MVP（缓冲区+行政聚合）。

### 📝 开发日志

**关键字**：三页架构 ADR-015, L0-L4 双视角, #4285F4/#384555, 单层顶栏, 面包屑, 3 按钮集, Martin 导航重塑, 色板圆角, color-mix 派生

#### 做了什么
- **A1 三页架构文档**：产品升级三页架构（数据库→控制台→实时地图），当前=控制台 α v0.1。ADR-015 + architecture(§2 三页图 / §4 L0-L4 双视角 / §8 演进) + prd(§1.5 / §3.1 三页树) + dev-notes(06-27) + memory(three-page-architecture)。
- **B0 色彩**：token 单源（tokens.json→generate_css.py→tokens.css），品牌蓝 #007afc→#4285F4（8 处 + pill.bg RGB）；新增 --geojson-color-card-fill #384555；Overview/Table 卡片(ov-t1/ov-stat/stat-cell/ov-placeholder)深灰填充 + inverse 文字。数据表格保持白底。
- **B1 单层顶栏**：双层 88px→单条深蓝 48px；面包屑「宜昌市情绪地图 › 控制台（Console） prototype alpha v0.1」（title-zh ×2/3）；Import/Export/i 靠右白字（.draw-tool/.tb-text 改深蓝底白字）；select/basemap 移出（迁 B2）。
- **B2 3 按钮集**：map-controls 在 5 按钮簇上方加 toolsGroup（指针/测量/图层），8px 间距、悬停灰选中蓝。select/basemap 带 data-tool/data-action → initToolbar 自动绑（不改调用链）；measure toast 占位；#map .emotion-tools-ctrl 覆盖 .draw-tool 深蓝底白字污染。
- **B3 左端栏三区**：`.lp-sections` 从 4 段加法手风琴改为三区——区1 选择栏 tab 互斥（Range/Layers/Toolbox，`setActiveTab` 同步 pane 显隐 + 文件夹 title）、区2 深灰 `#384555` 工具栏（文件夹按当前页触发 range/import-input + 漏斗「可见/总数」+ 眼睛/垃圾桶从 Layers 段头迁入 id 不变）、区3 操作栏仅此滚动。删 Analysis 段（整合数据库）+ 删 `+Upload Range` 卡（上载统一文件夹）。默认宽 ×0.8 = 240px（`--left-w` + `--geojson-layout-left-panel-width` 同步）。
- **B6 随动复核**：左簇 `.emotion-controls-root` 锚 `#map`（absolute left:10px），`#map` flex-shrinks 天然跟随左端栏。Playwright 实测：遍历 --left-w ∈ [240,320,400,500]，Δcluster === Δlp（gap 恒 18 = gutter8 + offset10），B3 未动 flex → **零代码改动**，仅验证。

#### 踩坑 & 收获
- **token 单源**：tokens.css "DO NOT EDIT" → 改 tokens.json + 跑 generate_css.py；pill.bg 是 rgba 非 #007afc 字面量，replace_all 漏，单独更 RGB→(66,133,244)。
- **.draw-tool 双语境**：header（深蓝底）与 #map（白底）共用 .draw-tool → 用 `#map .emotion-tools-ctrl .draw-tool` 覆盖回白底深字。
- **initToolbar 选择器复用**：按钮迁址带 data-tool/data-action 即自动绑，不必改 map.js/main.js（initMap 先于 initToolbar，按钮已 in DOM）。
- **B3 迁移不破坏绑定**：`#layers-toggle-all`/`#layers-clear` 从 `.section-head` 迁到 `.lp-zone-tools`，id 不变 → sidebar.js 的 getElementById 绑定与 renderLayerList 的 innerHTML 刷新全保留；旧 `.section-head .layers-*` CSS 选择器变 dead 但无害。
- **B6 同步读取陷阱**：`#left-panel` 有 `transition: width`，遍历 `--left-w` 后同步 `getBoundingClientRect()` 读到动画初值（lpRight 卡 240）。解法：测试时 `lp.style.transition='none'` + `void lp.offsetWidth` 强制回流，再验 Δcluster===Δlp。另：cluster 与左端栏间隔是 gutter(8)+offset(10)=18，非 10。
- **showLayerManager 适配**：原依赖 `.lp-section[data-section="layers"]` 加 `.open`，三区重构后改调 `setActiveTab('layers')`——重构结构性改动必须 grep 旧选择器的所有消费方。
- **B5 幽灵 token + 半透明 token 化**：`--geojson-brand`（toast.css 引用）全仓无定义 → 回退 `#007afc` 永驻旧蓝（**真 bug**，非纯回退值不一致），改用真 token `--geojson-color-brand-primary`。半透明蓝（选中态填充等）无法直接引 token → `color-mix(in srgb, var(--geojson-color-brand-primary) N%, transparent)` 派生（单源真值，brand 变更自动跟随）；`rgba(66,133,244,N)` 虽匹配 `--geojson-color-pill-bg` 风格但仍是硬编码 RGB，不满足"替换为 token"。**判别**：`PRESET_COLORS` 调色板色 / arch-diagram 七色 `--lc` 是**内容色**（用户选色/装饰分层），非 chrome token 消费方，保留不动；`.ov-swatch`/`.stat-cell .swatch` 为图例小圆点，保留圆形。

#### 🔜 下一步（新会话）
- **B4 左端弹出栏**（✅ 已完成）：紧贴 `#left-panel` 右缘的 `#param-panel`（absolute `left:var(--left-w)` 随动 B6 机制、不可拖宽、默认隐藏），1:2 分栏（左=点/线/面样式 `#settings-popover` / 右=核密度·Buffer 子页签）+ 中灰 2px 竖线 + 右上 X。三模块 `<dialog>`→`<div>`、id 全保留，open/close 由 `showModal()`→`openParamPanel()/closeParamPanel()`（新 `param-panel.js` 编排显隐+页签+outside-click/Escape），**apply 链零改**（`applyPaint`/`generateHeatmap`/`generateBuffer` + 读值选择器一字未动）。**决策已锁**：①核密度 3 段拍平单滚动（不引入步骤导航）②`#basemap-popover` 保留 top-right。Playwright 全链路验证通过：paint 实时生效、核密度真生成（图层 4→5 + 热力图例）、buffer 填充、tab 切换、X/Escape 关闭；零 JS 错误。
- **B5 色板圆角 + 品牌蓝查漏**（✅ 已完成）：`.swatch` 圆形(50%)→圆角矩形(`--geojson-radius-md` 6px，与同弹窗 `.linestyle-cap` 一致)；全局 `#4285F4` 品牌蓝查漏——残留旧蓝 `#007afc`/`rgba(0,122,252)` 清零：(a)半透明填充改 `color-mix(in srgb, var(--geojson-color-brand-primary) N%, transparent)` 派生（`.layer-row.is-selected` 12/18%、`.is-bar-sel`/`.hm-style-btn.is-bar-sel` 12/18%、`.sc-hit`/`.arch-desc code` 6%、linestyle-cap 选中阴影 30%）；(b)`var(--token,#007afc)` 回退值统一→`#4285F4`（panel/sidebar/toolbar/settings/param-panel/search-bar）；(c)**toast `--geojson-brand` 幽灵 token**（全仓无定义、回退永驻旧蓝）→真 token `--geojson-color-brand-primary`；(d)`map.js` hover-ring 回退 `#007afc`→`#4285F4`。**保留不动**（内容色非 chrome）：`PRESET_COLORS` 调色板蓝、arch-diagram 七色彩虹 `--lc`。
- **A2 UI 层文档**（✅ 已完成）：①`decisions.md` **ADR-016**「Martin 编辑器范式（三区左栏+悬浮参数栏）」——背景/三选项表/决策(B0-B5)/后果 + 索引行 ②`spec.md` **§3.4** 前端主界面导航架构规格（布局区域表 + 左栏三区表 + 色彩控件单源），§3 定位注改指 §3.4 ③`ui-redesign-plan.md` **Phase 4**（B0-B5 落地表，Phase 1-3 标注已被 ADR-012 超越）④memory **`martin-ui-redesign`**（承重约定：三区 tab 互斥/参数栏随动 B6/apply 链零改/品牌蓝单源 `#4285F4`/胶囊设计语言）+ MEMORY.md 索引。revision-log §5.12 已同步。
- **衔接**：plan 文件 `C:\Users\Hi\.claude\plans\feature-kde-l2-3d-martin-delegated-milner.md`（B3-B6+A2 执行计划，**Phase 1 = B3+B6 已完成**）。

---

## 📅 2026-06-25（周三）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | Phase 2 地点搜索 — 后端 | `core/geocode.py` `api/routes.py` `api/schemas.py` `requirements.txt` | MOD_GEOCODE：本地 rapidfuzz + 高德兜底，`_amap_request` 双向 GCJ-02↔WGS84；3 GET 路由 |
| 2 | ✅ | Phase 2 地点搜索 — 前端搜索栏 | `frontend/js/search-bar.js` `css/search-bar.css` `js/api.js` `index.html` `main.js` `popup.js` `design/tokens.json` | 6 态状态机（不用 maplibre-gl-geocoder），胶囊折叠 32px→200px；空白点击反查 chip |
| 3 | ✅ | Search v2 — 拼音匹配 + 高亮 | `core/place_layer.py` `frontend/js/search-bar.js` | pypinyin 模糊匹配（wd/wanda→万达）；结果高亮子串 |
| 4 | ✅ | Search v2 — 红大头针 + Point 卡 + 交互 | `frontend/js/search-bar.js` `popup.js` | 自定义红色 pushpin，hover tooltip，click popup，激活放大，点外收起，x 关闭 |
| 5 | ✅ | Search v2.1 — 排名分层 | `core/place_layer.py` `tests/test_geocode.py` | exact(300) > prefix(250) > pinyin-exact(220) > substring(180+) > fuzzy；修"金缔华城→苏宁易购"bug |
| 6 | ✅ | Search v2.1 — 落水 POI 过滤 + 导出标记 | `core/place_layer.py` `export_poi_geojson.py` `DATA/place/pois_wgs84.geojson` | 28/1428 落现状水系，`__init__` 预标 `_in_water`，`forward()` 跳过，导出标 in_water |
| 7 | ✅ | Search v2.1 — Point 卡审计字段 | `frontend/js/popup.js` `core/place_layer.py` `api/schemas.py` | 数据源(高德POI库/种子手标) + baidu_level1/2 + area + 坐标 6 位精度 |
| 8 | ✅ | Search v2.1 — L0 数据点 popup 增强 | `frontend/js/popup.js` | showPopup 坐标 6 位不灰 + async 反查"区域 / 最近 POI" |
| 9 | ✅ | Zone v2.2 — POI/zone 审计 | `docs/poi-zone-audit.md` `audit_poi_zones.py` `audit_zones_local.py` | seed 121 条无 amap 对照（部分伪造）+ 坐标偏 1–9km；万达≠国贸 2731m；太古里伪造。根因报告 |
| 10 | ✅ | Zone v2.2 — 数据根基重建（Stage 1） | `DATA/place/zone_typology.json` `core/place_layer.py` | amap 重建 12 zone（7 商圈 + 4 非商业 + general）+ center+radius 商圈圆 + 删 wanda_cbd + all_pois=amap |
| 11 | ✅ | Zone v2.2 — 情绪叙事级联（Stage 2） | `emotion_corpus.json` `snapshot_config.py` `generate_l1_mock.py` `check_spatial.py` `place_keywords.json` | corpus 桶扩 12 zone × 3 极性；zone_caps 重算；mock 打标；check_spatial 适配 |
| 12 | ✅ | 合并 + 清理 + L0 popup 对齐 | git `main` / `frontend/js/popup.js` | merge feat→main(14 commits)；删 2 分支；main-only 工作流；L0 badge "原始"对齐 L1/L2 节奏 |
| 13 | ✅ | P2 geocode 离线退化 | `core/place_layer.py` `core/geocode.py` `tests/test_geocode.py` | `forward()` 加 `min_fuzzy_score` 参数；离线时 55→35 返回更多近似命中；pytest 35/37 全过 |
| 14 | ✅ | P3 下拉结果丰富化 | `core/place_layer.py` `api/schemas.py` `frontend/js/search-bar.js` `frontend/css/search-bar.css` `tests/test_geocode.py` | zone 色点 + 双副信息（zone+地址/类别同时显示）+ 匹配类型标签（精确/前缀/拼音/子串）|
| 15 | ✅ | P5 UX loading 态 + 无结果引导 | `frontend/js/search-bar.js` `frontend/css/search-bar.css` | 输入即显 spinner "搜索中..."；空态显示标题+引导文案 |

> 💡 开发工作流（solo）: 以后在 main 上直接工作 → `git commit` → `git push`。不做分支/PR。

### 📝 开发日志

**关键字**：地点搜索, 高德地理编码, CRS 红线, rapidfuzz 模糊匹配, 6 态搜索栏状态机, 拼音匹配, 分层排名, 落水过滤, zone 重建, amap 数据校准, 商圈本地知识

#### 做了什么
- **Phase 2 全栈地点搜索**（后端 `core/geocode.py` MOD_GEOCODE + 3 GET 路由 → 前端 6 态搜索栏 + 反查 chip）。两大红线：AMAP_KEY 仅服务端 .env（`_load_env()` 自加载——api/main.py 不加载 .env）；高德 GCJ-02 一律 `_gcj_loc_to_wgs`（正向）+ regeo 入参 `wgs84_to_gcj02`（反向），1m 往返单测守住。
- **Search v2**：pypinyin 拼音模糊（wd/wanda→万达）+ 结果高亮；红色大头针标记（hover tooltip + click Point 卡 + 激活态放大 + 点外收起 + x 关闭）。
- **Search v2.1 数据质量**：① 排名分层（exact>prefix>substring）修"金缔华城→苏宁易购"bug——原 partial_ratio 同分按数据顺序误排；② 28/1428 落现状水系→forward 跳过+导出标 in_water；③ Point 卡加审计字段（数据源/baidu_level/area/坐标 6 位）④ L0 数据点 popup async 反查区域+最近 POI。
- **Zone v2.2 根基重建**：审计发现 seed 158 条中 121 条 amap 无对照、坐标偏 1–9km（宜昌东站 9334m/国贸大厦 1019m/水悦城 671m）、太古里（西陵）伪造。用户本地知识校准——宜昌 9 商圈（夷陵CBD≠万达；CBD 专指夷陵广场；万达=万达广场唯一；水悦城/中南路/五一广场/吾悦/夷陵万达 各自独立）。重写 zone_typology 为 12 zone（7 商圈 center+radius 圆 + 4 非商圈子区 amap 锚点 buffer + general）；all_pois=amap only（seed 退命名不参与坐标/边界）。Stage 2 级联情绪叙事 12 zone（corpus/zone_caps/generate_l1_mock/check_spatial）。模拟数据暂不动。华翔CAZ/江南URD 数据 0 命中→归 general。
- **工作流切换**：合并全部到 main，删分支，以后 solo main-only 开发（commit→push 即完成）。

#### 踩坑 & 收获
- **数据信源不可信**：seed 158 条是手标/模板生成的，坐标大面积错+含伪造条目。amap 1270 条准。zone 边界原由 seed buffer 构建→种子错边界全错。教训：生成数据不能当初信源（边界/坐标），只能用真实 API 数据做锚。
- **排名同分陷阱**：`partial_ratio` 对"金缔华城"和"苏宁易购(金缔华城店)"都给 100 分——排序本质是 tiebreaker，不在数据层而在排层。分层打分才是正解。
- **zone 命名需本地人校准**：AI 从数据推断"万达簇""万达-国贸商圈"，但本地知识是万达=万达广场（唯一）、CBD=夷陵广场（≠万达）、万达和国贸 2731m 两个商圈。不加本地校验的 zone 分类不可靠。

#### 验证
- `py -m pytest tests/ -q`：geocode 25 全过（CRS 1m 往返 + 排名分层 + 落水过滤）。全量 80+/81（1 既有 L2 test_capabilities 与本批无关）。
- Playwright：搜索→flyTo CRS 自洽（center==hit 坐标）；Point 卡字段全显；L0 popup async 反查挂载；落水点不在结果中。
- curl `/place/search?q=金缔华城` → 金缔华城(300) 首条；`/reverse-geocode` → zone 正确。

#### 🔜 下一步
- 情绪真实数据 pipeline（L0→L1→L2 完整跑通，待 DeepSeek API Key 验证）。
- KDE 批2 时间轴。
- 华翔CAZ/江南URD 数据补齐后升 zone。

---

## 📅 2026-06-22（周一）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 批1·1b 小类配色按大类派生 | `frontend/js/state.js` | `EMOTION_TYPE_COLORS` 7 色派生自 `EMOTION_MACRO`；愁类 2 小类紫色系明度梯度 |
| 2 | ✅ | 类型细分色板方向翻转对齐胶囊顺序 | `frontend/js/state.js` | `positive/negative/neutral` 三 ramp 端点反转，对齐 `EMOTION_MACRO_ORDER`；放弃"高密度=最强情绪"旧语义 |
| 3 | ✅ | 补 todo.md 06-19~06-21 断档 | `docs/todo.md` | 核密度弹窗重构 7 项 + 开发日志（交接卡遗留） |
| 4 | ✅ | H 按钮重生成消失 bug | `heatmap-tool.js` `map.js` `serve.py` | opacity 反推百分比/比例混用（0.01 几乎透明）→ `*100`；附带 `to-number` + `serve.py` import ?v（破 Chrome module 缓存）+ 编辑分支原地更新（`editLayerId`） |
| 5 | ✅ | 色带随大类胶囊动态变化 | `state.js` `heatmap-tool.js` `map.js` `heatmap-legend.js` `panel.js` | `buildMacroRamp` inline rampStops（选中大类→只含选中类色）；消费方优先 inline；rampKey 保持 polarity（reverse 显示对齐胶囊序） |
| 6 | ✅ | 色带 HSL 色相插值 + 每类 3 段 | `state.js` | 取消 macroShades 明度变体；类色 HSL 插值（`gradientStopsHsl`），每类占 3 段色相；段数 积极 6/消极 9/中性 6/单类 3；HSL 替 RGB（中间黄绿明亮非土黄） |
| 7 | ✅ | #hm-macros click→change 事件 | `heatmap-tool.js` | label-click 时序 is-on 滞后 input.checked，单选色带不更新 → change 同步 |

> 💡 标准启动指令：`py frontend/serve.py 8080` → `http://127.0.0.1:8080/frontend/index.html`

### 📝 开发日志

**关键字**：小类配色派生, 色板方向翻转, EMOTION_MACRO_ORDER 对齐, density 语义放弃

#### 做了什么
- **批1·1b 小类配色按大类派生**：小类独立色板（`EMOTION_TYPE_COLORS`）与大类色板（`MACRO_COLORS`/`EMOTION_MACRO`）冲突——"不满抱怨"=橙却属大类"愁"=紫。改为派生：单小类=大类色，愁类 2 小类（焦虑担忧/不满抱怨）用紫色系明度梯度（中紫 `#A569BD` / 深紫 `#7D3C98`）。调用点不动（`heatmap-tool.js:274` `EMOTION_TYPE_COLORS[t]` 值变即生效）。
- **类型细分色板方向翻转**：`positive/negative/neutral` 三 ramp 端点顺序与胶囊 `EMOTION_MACRO_ORDER` 反向（积极胶囊 喜→乐，色板却 乐→喜）。反转三 ramp 端点对齐胶囊顺序（积极 喜→乐、消极 怒→哀→愁、中性 急→盼）。放弃"高密度=最强情绪"旧语义——色板是单维 density 渐变，颜色仅借大类色做视觉编码，无真实"密度段=情绪"含义。消费方（图例 / Overview / 设置 / 地图 paint）单源自动跟。
- **补 todo.md 06-19~06-21 断档**：核密度弹窗重构 7 项 + 开发日志（交接卡遗留项）。
- **H 按钮重生成消失 bug**（5bab6d4）：H 按钮重生成（原样再点生成）→ 热力图消失、眼睛救不回。Playwright + paint 查证：`openHeatmapDialog` 反推 opacity 百分比/比例混用（`sp.opacity` 0~1 直接赋百分比控件 0~100 → type=range clamp 1 → `generateHeatmap` 读 `1/100=0.01` 几乎透明）。修复：反推 `Math.round(sp.opacity*100)`。附带：`buildWeightExpression` `to-number`（MapLibre worker string 健壮）；`serve.py` 拦截 .js 注入 `import ?v=<mtime>`（破 Chrome module graph 缓存——旧 serve 只 main.js 带 ?v，子 module 缓存旧版致 F5 失效）；编辑分支原地更新（激活 `editLayerId`，4.6「继续编辑」语义）。
- **色带演进**（62724d1）：
  - **随胶囊动态**：`buildMacroRamp`（state.js）按选中大类生成 inline rampStops（选中大类 → 只含选中类色；全选 = 等同固定 ramp）；消费方优先 inline、fallback rampKey；rampKey 保持 polarity（rampDisplaySegs 据 polarity reverse，色带与胶囊同向）。
  - **每类 3 段 + HSL 色相插值**：取消 macroShades 明度变体（跨类明度跳变割裂），类色直接 HSL 插值（`gradientStopsHsl`，hue 最短路径），每类占 3 段色相，整体连续不割裂。段数 积极 6/消极 9/中性 6/单类 3。HSL 替 RGB（RGB 绿↔黄中间土黄 `rgb(152,148,65)`，HSL 中间黄绿明亮 `rgb(123,218,87)`）。
  - **#hm-macros click→change**：label-click 时序下 is-on class 滞后 input.checked（rAF 读旧值），单选时 renderStylePreview 取旧选中态、色带不更新 → 改 `change` 事件（input toggle 后同步触发）。

#### 踩坑 & 收获
- **色板方向 vs 胶囊顺序**：色板设计遵循 density 语义（左低右高），胶囊遵循情绪分类顺序（`EMOTION_MACRO_ORDER`），两者语义轴不同向导致全局反向。统一为胶囊顺序（视觉一致优先于牵强的 density-情绪绑定语义）。
- **小类派生 vs 直接读大类色**：愁类 2 小类若直接读大类色会撞色（焦虑担忧=不满抱怨=愁紫），保留小科级 + 值派生自大类色系，兼顾统一与区分。

#### 验证
- `node --check frontend/js/state.js` 语法通过。
- 起页肉眼验（`py frontend/serve.py 8080`）：核密度弹窗 ①选「类型细分」→ ②小类胶囊色对齐大类色系 → ③色板分段条方向对齐胶囊顺序。未上 Playwright（配色/方向小改）。

#### 🔜 次日计划
- 批1·1a 预览图换 terrain/factor Kepler 截图（等素材补齐，⏸ 搁置）。
- 任务树下一模块（Range 范围分析 / Analysis 接入 / Table 表格）。

---

## 📅 2026-06-19~06-21（周五~周日）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 核密度弹窗三阶引导重构 | `frontend/js/heatmap-tool.js` `frontend/css/dialog.css` | ①分析类型(总体/类型细分/多维归因) ②数据源 ③显示样式；①三组纵向排版 |
| 2 | ✅ | kepler 离散分段色板 + 栏/选项/胶囊三组件 token | `frontend/js/state.js` `design/tokens.json` `frontend/css/dialog.css` | 全站色带统一 `.segmented`，取代无极渐变 |
| 3 | ✅ | L1 热度值 | `frontend/js/heatmap-tool.js` | 强度×置信度，3 段动态分位 |
| 4 | ✅ | 7 大类配色 + 类型细分色板方向修复 | `frontend/js/state.js` | `MACRO_COLORS` 单一调色源(UberPool 6+1)；端点顺序低→高 |
| 5 | ✅ | 联动（Overview/popup/图例） | `frontend/js/sidebar.js` `frontend/js/popup.js` `legend` | `layers:changed` 事件三处同步 |
| 6 | ✅ | serve.py 自动 ?v 注入 + 启动清端口 | `frontend/serve.py` | `?v=<mtime>` 改文件即拉新，零手动 bump |
| 7 | ✅ | revision-log 任务树 + 工作机制 memory | `docs/revision-log.md` `~/.claude/` | 模块化任务树；session-handoff/token-saving/revision-log/kde-loadbearing |

> 💡 标准启动指令：`py frontend/serve.py 8080` → `http://127.0.0.1:8080/frontend/index.html`

### 📝 开发日志

**关键字**：核密度弹窗(KDE), 三阶引导, kepler 离散分段色板, L1 热度值, 7 大类配色, 类型细分色板方向修复, layers:changed 联动, serve ?v 注入, revision-log 任务树

#### 做了什么
- **核密度弹窗三阶引导重构**：①分析类型(总体情况/类型细分/多维归因) → ②数据源 → ③显示样式。①三组纵向排版（kepler 风），取代旧版杂糅表单。
- **kepler 离散分段色板**：全站色带统一 `.segmented`（色块拼接，非无极 linear-gradient）。色板采样自 kepler 源码——网格暖色谱≈Global Warming；7 色分类≈UberPool 6 色+补 1 色；L1 默认单色改橙红(ColorBrewer Reds)。栏/选项/胶囊三组件设计 token。
- **L1 热度值**：L1 综合舆情热度 = 强度×置信度，3 段动态分位（取代静态阈值）。
- **7 大类配色**：喜怒哀乐愁急盼 = 绿/橙/红/紫红/紫/深蓝/天蓝（`MACRO_COLORS` 单一调色源；胶囊/classify-7/积极·消极·中性格色板均派生自此，保证全局一致）。
- **类型细分色板方向修复**：端点顺序 = [低值色 … 高值色]（gradientStops 从低 density 到高 density）。积极=喜(绿)高/乐(橙)低；消极=怒(红)高/哀(紫红)中/愁(紫)低；中性=急(深蓝)高/盼(天蓝)低。
- **三处联动**：Overview / popup / 图例 通过 `layers:changed` 事件同步。
- **serve.py `?v=<mtime>` 自动注入**：返回 index.html 时给本地 css/js 引用自动注入 `?v=<mtime>`，文件一改浏览器即拉新，开发者零手动 bump；启动时清占用端口。
- **revision-log 任务树 + 工作机制 memory**：revision-log 顶部建模块化任务树（根→模块→批→叶，AI 全程维护）；建 4 条工作机制 memory（session-handoff / token-saving / revision-log / kde-loadbearing）。

#### 踩坑 & 收获
- **kde-loadbearing 两条底层逻辑（勿破坏）**：①**联动排除**——无字段层级自动排除（类型细分锁 L2、L1 无情绪字段时胶囊禁用）；②**独占显示**——生成新热力图隐藏其他层 + `dispatch layers:changed` 保侧栏眼睛同步。
- **类型细分色板端点顺序**：gradientStops 从低 density 到高 density，端点顺序 = [低值色 … 高值色]；方向搞反会让"高密度=低值色"，视觉语义倒置。

#### 验证
- 起页肉眼验（`py frontend/serve.py 8080`），未上 Playwright（配色/布局小改，遵循 no-routine-playwright-verify）。
- 核密度弹窗三阶引导、L1 热度值分位、7 大类胶囊色、类型细分色板方向、三处联动均肉眼确认。

#### 🔜 次日计划
- 批1·1b：小类配色按大类派生（小类色继承所属大类色相基调；愁类 2 小类用紫色系明度梯度）。
- 批1·1a：预览图换 terrain/factor Kepler 截图（等素材补齐，⏸ 搁置）。

---

## 📅 2026-06-18（周四）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | Import v1：1:1 geojson.io 导入管道 | `frontend/js/{import,dialog,toast,state,map,sidebar,main,popup}.js` `frontend/css/{toast,dialog,sidebar,popup,legend,layout}.css` `frontend/index.html` | groupFiles/detectType/parse(GeoJSON/CSV/KML/Shapefile)/proj4 CRS/几何分流/polarity探测/merge/fitBounds；导入确认弹窗（单/组合文件）；全局胶囊 toast；左栏图层管理器（眼睛/删除/清空） |
| 2 | ✅ | Import v2 批1：bug 修复 + 核心显示 | 同上 + `tokens.css` | 7 bug（polygon 线层泄漏/Import 误切模式/删 seed/左栏默认展开/Layers 自动展开/shapefile 5件包/眼睛放大）+ L1 橙色置信度着色 + 图例按层显隐 + polygon 海军轮廓 + 范围第二 popup |
| 3 | ✅ | Import 细化轮 | 同上 | 闭合线归为 polygon（GIS 常识）；范围 popup 重构（名称下沉第二层、收起显 Range）；点大小改密度自适应（稀疏14-18/高8-12/超高4-6，随zoom插值）；选中=灰白加粗描边不填充；收起胶囊定宽64px；L2 配色提浅（最深不变） |
| 4 | 🔄 | Import 批2：要素按钮 + Kepler 设置弹窗 + 预设色板 | `frontend/js/settings.js` `frontend/css/settings.css` `frontend/js/{sidebar,map}.js` `frontend/index.html` | 点/面 marker 变可点「要素按钮」（激活=深灰粗圆角框）；Kepler 设置弹窗（预设色板横条/色块 + 透明度/线宽滑块 + 面填充开关）；线暂不开放。实现完成待肉眼验 |

> 💡 标准启动指令：`@pm 开始处理 2026-06-18 的任务 N：任务名称`

### 📝 开发日志

**关键字**：Import, geojson.io 1:1, shapefile, proj4 CRS, L1 置信度, 密度自适应, 图层管理器, 范围 popup

#### 做了什么
- **Import v1**：geojson.io 1:1 导入。两处 Import（工具栏+左栏）+ 页面拖放 → 原生文件窗 → **每次导入都弹确认弹窗**（单文件=文件名+格式下拉可改写；组合包="Import {name} (n/N)"+文件名列表；Cancel/Import）。管道：`groupFiles`(shapefile 多文件成组) → `detectType`(扩展名/JSON内容sniff) → `parseGroup`(GeoJSON/CSV/KML/Shapefile) → `reprojectFC`(proj4 读 .prj → WGS84) → `splitByGeometry`(Point/Line/Polygon 分流) → `detectColorMode`(polarity/confidence/needsAnalysis) → **merge 追加** + fitBounds。全局胶囊 toast。左栏图层管理器（眼睛显隐/×删除/区段头清空）。
- **Import v2 批1**（用户实测后 7 bug + 显示）：①polygon 开关失效=fill(`lyr-{id}`)+line(`lyr-{id}-line`)两图层泄漏，改同步增删 ②顶端 Import 误切 sections，改仅加载成功后切 ③删 seed 模拟数据，首屏空 ④左栏默认展开凸显 Import ⑤加载后自动展开 Layers ⑥**shapefile 5件包失效**=shpjs `combine` 参数顺序写反(应[几何,属性])，改走 parseShp/parseDbf/combine 直读 ⑦眼睛放大。+ L1 橙色置信度着色（Kepler 风、小点无描边、置信度越高越深）+ 图例按层显隐（polarity/confidence/range 三块）+ polygon 默认 fillOff 海军轮廓 + 范围第二 popup（海军主题、面积/周长/类型/顶点/bbox）。
- **细化轮**：①闭合 LineString 归为 polygon（首尾点重合=面边界，GIS 常识）→ marker 显「面」②范围 popup 重构：名称下沉第二层(.popup-text，类评论)、「范围」badge 去强调、收起显粗体"Range"、与情绪胶囊同宽 ③点大小**密度自适应**(densityStops：≤1000→14-18/≤20000→8-12/>20000→4-6，随zoom插值，取代固定3x) ④选中=灰白(#E8E8E8)加粗(3.5)描边、不填充 ⑤收起胶囊定宽64px+大写+省略 ⑥L2 配色提浅（very-negative #B92D2D 不变，其余按明度比例提浅）⑦范围透明 hit 层(宽12)易悬停/点击。
- **Import 批2**：要素按钮 + Kepler 设置弹窗。图层行「点/面」marker 由 span 改可点 button（激活=gray-700 `#404040` 粗圆角框、放大到 ~22px 与眼睛齐；线为禁用 chip）；点开 `#settings-popover`（`position:fixed`，靠左栏右边+8px、240px、圆角 8px=radius-lg 同左簇/图例）：点·L1 confidence=**序列色板横条点选**(→`paint.ramp`)+透明度滑块；点·L2/needsAnalysis=仅透明度（颜色由极性/灰决定）；面=**填充开关**(→`paint.fillOn`)+**单色色块**(→`paint.color`)+线宽滑块+填充透明度滑块。控件 change → `setLayerPaint`+`renderLayer` 实时重渲（renderLayer 的 remove+readd 已支持 live）。预设 6 序列色板（橙默认/蓝/绿/紫/红/灰）+ 10 单色块。一次一弹窗；外部点/ESC/删图层关闭。`map.js addPointPaint` 改读 per-layer `paint.ramp`/`paint.opacity`。
- **点密度策略再修订**（用户定）：`densityStops` 阈值收紧——`<500→[14,18]` / `500-2000→[8,11]` / `≥2000→[3,5]`（原 ≤1000/≤20000/>20000）。用户 2000 点数据 ~10.7px→~4px。L0-L4 统一（radius 本就 colorMode 无关）。
- **配置**：index.html 加 CDN 解析库（csv2geojson/shpjs/proj4/fflate；@tmcw/togeojson 走 esm.sh 动态导入，CN 不可达则降级）。tokens.json/tokens.css 情绪五色单源同步。

#### 踩坑 & 收获
- **shpjs combine 参数顺序**：`combine([geometries, properties])` shp 在前 dbf 在后；写反 → geometry/properties 颠倒，splitByGeometry 无可识别几何→静默无操作（不抛异常）。用 getStyle() 取原始 paint 表达式才看出。
- **map.project 坐标系**：返回**地图容器内坐标**，Playwright `page.mouse.click` 用**视口坐标**，差左栏+头栏偏移 → 测试点击老偏。修正：+ getContainer().getBoundingClientRect() 偏移。
- **CGCS2000 .prj**：规划范围.shp 的 .prj = CGCS2000 3-degree GK CM_111E，**False_Easting=500000**(EPSG:4538)，非 4546 的 37500000。proj4 能直接解析 WKT，实测 [525439,3398933]→[111.266,30.711] 宜昌正确。
- **paint.get() 返回求值态**：MapLibre `layer.paint.get('circle-radius')` 返回当前 zoom 求值后的值，看不到原始表达式；改用 `map.getStyle().layers[].paint` 取原始表达式验证。
- **闭合线=面**：CAD 导出的 LWPolyline shapefile 几何类型是 LineString 但首尾闭合，本质是面边界。splitByGeometry 据此归为 polygon。

#### 验证
- Playwright file-upload 喂真实文件端到端：L2 GeoJSON（polarity 5色）/ L1 CSV（橙色置信度）/ shapefile 5件包（CRS重投影到宜昌）/ 测试 polygon（B1开关+范围popup）。控制台全程仅 favicon 404。
- 密度半径表达式 `interpolate(zoom,8→8px,14→12px)` 实测；选中 halo `stroke #E8E8E8 width 3.5 opacity 0` 实测；收起胶囊 `width 64px uppercase` 实测。

#### 🔜 次日计划
- Import 批2：要素按钮 + Kepler 设置弹窗 + 预设色板
- 用户视觉复验反馈微调（点密度档阈值 / L2 配色深浅 / 范围 popup 字段）
- MCP 收尾（github PAT / web_reader 重复）—— 06-17 遗留

---

## 📅 2026-06-17（周三）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 交接恢复：补 4 个天地图底图 JSON | `apps/static/tianditu_*.json` | gitignore 不同步，办公机手动补（img/vec × 有/无注记），否则默认底图 404 灰屏 |
| 2 | ✅ | 文档去陈：9 份权威文档对齐前端迁移 | 根`CLAUDE.md`/`apps/CLAUDE.md`/`AGENTS.md`/`docs/{architecture,architecture-pattern,spec,prd,brand-visual,ui-redesign-plan}.md` | Streamlit→MapLibre，全部标「迁移期遗留」，+130/−49 |
| 3 | ✅ | 新增 ADR-012 前端迁移决策 | `docs/decisions.md` | 历史审计连续，旧 ADR-001~011 不动 |
| 4 | ✅ | 补录 06-16 晚~06-17 凌晨工作 + 换机清单 | 本文件 + `session-handoff.md` | 昨晚工作原只记于交接卡，todo.md 漏更（见日志） |
| 5 | ✅ | MCP 能力层纳入 vibe coding + 智谱优先策略 | 根`CLAUDE.md`/`AGENTS.md`/`docs/mcp-strategy.md`(新)/`docs/decisions.md`(ADR-013)/本文件 | 9 服务实测 7 通；github PAT 失效、web_reader 重复待修 |
| 6 | ✅ | 闭环补强 9 波：开环→闭环 | `core/tracker.py`/`.claude/{settings,agents/*,hooks/*,commands/verify}`/`.githooks/`/`tests/test_pii_guard.py`/`docs/{trace-digest,decisions}.md`/memory/ | pytest 59 passed；trace 落盘+回灌、提交门禁、emoji 拦截、记忆索引全到位；ADR-014 |

> 💡 标准启动指令：`@pm 开始处理 2026-06-17 的任务 N：任务名称`

### 📝 开发日志

**关键字**：交接恢复, 文档去陈, ADR-012, 同步诊断, todo.md 漏更, 换机清单, MCP策略, 智谱优先, ADR-013

#### 做了什么
- **交接恢复**：办公机 `git pull` 到 cee9da9（与家用机同步健康，HEAD=origin），补 4 个被 gitignore 的天地图底图 JSON（img/vec × 有/无注记）
- **文档去陈**（+130/−49，10 文件）：根 CLAUDE.md / apps/CLAUDE.md / AGENTS.md / docs 6 份全部对齐「frontend/ MapLibre 为主、Streamlit 迁移期遗留」；ASCII 架构图内部不动（破坏对齐），改用 callout 兜底
- **新增 ADR-012**：记录前端迁移决策（背景/选项 A-C/决策/后果），保持 ADR 审计连续
- **同步诊断**：查明 todo.md 漏更真相——git 同步正常，但昨晚工作（前端 v2 / P0 债 / 启动说明）只写进 session-handoff + frontend/README，未同步进 todo.md
- **启动说明定位**：= `frontend/README.md`（cee9da9，86 行），未丢失
- **换机清单**：写入 session-handoff.md「换机前必做」，防止 todo.md 再漏更
- **MCP 能力层**：实测全部 9 个 MCP（7 通 / github 认证失败 / web-reader 重复）；新建 `docs/mcp-strategy.md` 路由手册；CLAUDE.md 规则 11 视觉改智谱为主、新增规则 12、补 MCP 状态行 + 文档登记；AGENTS.md 升 v2.1 加「MCP 能力外挂」子节；ADR-013 落档
- **闭环补强（9 波，ADR-014）**：诊断=协作半成品/闭环开环；补反馈链——①tracker 落盘 `.trace/trace.log`+`recent_errors()` ②`/verify`+`.githooks/pre-commit`(core.hooksPath) ③emoji PreToolUse hook(精确拦 U+1F000-1FAFF)+PII guard 测试 ④SessionEnd trace 摘要回灌 `docs/trace-digest.md`(游标防重) ⑤8 agent v2.1+MCP 能力段+铁律 1-12 ⑥建 MEMORY.md 索引(原缺失！)+修 3 陈旧记忆+3 种子 ⑦GitHub Actions CI(best-effort) ⑧skill 索引已精选(物理移除暂缓)。pytest 56→59 passed 零回归

#### 踩坑 & 收获
- **todo.md vs session-handoff 职责分裂**：两者都承载工作状态，昨晚只更交接卡、漏正式日志 → 新会话/Agent 读 todo.md 误判「06-16 后没干活」。根因：无「换机前必更两文件」强制清单
- **git 同步本身健康**：HEAD=origin/main=cee9da9，无未推送/未拉取，.claude/ 配置全在 git。问题在内容写入策略，不在 git
- **lint 区分**：MD028（我引入的 callout 紧跟 blockquote）修了；MD060/MD032/MD040（原文既有表格/标题接列表风格）不逐处改，保全文一致性
- **github MCP `disabled:true` 被忽略**：`.mcp.json` 标了禁用仍被加载，且 PAT 失效致 `Bad credentials`——禁用标记未必生效，需移除条目或重启确认
- **web-reader 重复服务**：`web-reader`（连字符）与 `web_reader`（下划线）指向同一智谱端点，保留连字符一份即可
- **Auto Memory 暗写不召回**：memory 目录有 6 条记忆但 MEMORY.md 索引从不存在——召回靠读索引，等于 6 条全废。已补建索引。根因：写记忆的流程没同步写索引
- **emoji hook UTF-8 陷阱**：初版用 `sys.stdin.read()` 在 Windows cp936 下把 emoji 读坏→JSON 解析失败→被 except 吞掉静默放行。改 `sys.stdin.buffer.read().decode('utf-8')` 才真拦住。教训：Windows 下读 stdin 必显式 UTF-8

#### 🔜 次日计划 (2026-06-18)
- 办公机补验证：pytest 56 回归 + FastAPI governance 冒烟（交接卡 P0 待办）
- Phase 2：前端接真实数据 `/api/v1/points` + A 分析接 `/analyze`
- MCP 收尾：github MCP 设 `GITHUB_PAT` 或移除条目；清理 `web_reader` 重复服务；核实 `4_5v_mcp` 来源

---

## 📅 2026-06-16（周二）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ⏸️ | L0→L1→L2 端到端管线验证 | `SCRIPT/data_governance.py`, `SCRIPT/emotion_analysis_v1.py`, `DATA/raw/simulated_20260613_100k_raw.csv` | **用户搁置至下周**：DeepSeek Key 已配好，届时跑完整三阶段 |
| 2 | ⬜ | 文档一致性修正 | `docs/spec.md`, `docs/architecture.md`, `AGENTS.md` | Python 3.14.5 / L1 列数 26 / pm.agent.md 角色说明 |
| 3 | ⬜ | Git 提交 + push | — | commit session-handoff 更新 + todo 更新 |

> 💡 标准启动指令：`@pm 开始处理 2026-06-16 的任务 N：任务名称`

### 📝 开发日志

**关键字**：文档修正, 交接更新

> ⚠️ L0→L2 端到端管线验证已由用户明确搁置至下周，本周不再排入计划。

#### 做了什么
- **P0 阻断债清理（5 项，家用机）**：①h3 v3→v4 API ②CorpusAnalyzer 双 `analyze_single` 合并 ③ADR 编号消解（ADR-008→011，避与 Scrapy 冲突）④PostToolUse hook 对齐（仅清 .pyc，不重启/不测试）⑤`run_governance_pipeline()` 抽取（API/CLI 共用、不含 sys.exit）——函数级已验证，pytest/FastAPI 冒烟待办公机补跑
- **前端 Phase 1 落地（家用机）**：`frontend/` MapLibre GL JS geojson.io 外壳，Token 单源（tokens.json `geojson` 段 → frontend/css/tokens.css），Playwright 验证通过
- **文档一致性修正**：d02dd36 提交（Python 版本/L1 列数/pm.agent 角色）

#### 踩坑 & 收获
- 家用机 Python 实为 3.13.2（非文档 3.14.5），pypi 直连被墙致 pytest/FastAPI 未跑成
- 前端 v2 配色纠正：误做全深色 chrome → 改「浅色为主 + 深蓝标题带」
- 切底图后情绪点消失：MapLibre 5.x re-apply 三套机制不稳 → 改 `setStyle(transformStyle)` 声明式 carry-over emotion-* 源/图层

#### 🔜 次日计划 (2026-06-17)
- （已完成，见上方 06-17 条目：交接恢复 + 文档去陈 + ADR-012）

---

## 📅 2026-06-15（周一）

### 🌙 凌晨完成（06-14 残余，commit `f044ca1`）

| # | 状态 | 任务 | 备注 |
|---|------|------|------|
| M1 | ✅ | Agent 架构 v2.0 升级 | 11→8 精简 + 自动编排 |
| M2 | ✅ | PRD + Spec 文档 | 27 功能 MoSCoW + 全规范 |
| M3 | ✅ | .claude 配置初始化 | 权限 + 记忆体系 + 中文偏好 |

### ☑ TODO List（今日，08:00+）

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ⏸️ | L0→L1→L2 端到端管线验证 | `SCRIPT/data_governance.py`, `SCRIPT/emotion_analysis_v1.py`, `DATA/` | **暂缓至下周**：准备测试数据 → 跑 L0→L1 治理 → 跑 L1→L2 情感分析 → 验证各层输出 |
| 2 | ⬜ | 用户验收周末改动 | 全项目 | Agent v2.0 架构 + PRD/Spec 文档 + 启动应用验证 + L1_COLUMNS 重排 + confidence 重命名 |
| 3 | ⬜ | Git 清理 + commit + push | — | 处理未提交 geojson + 提交今日变更 |
| 4 | ✅ | 安装 .claude Skill 包 | `.claude/skills/` | 4 源合入 455 技能：daymade(64) + python-skills(12) + laurigates(362) + **anthropics(17)** |

> 💡 标准启动指令：`@pm 开始处理 2026-06-15 的任务 N：任务名称`

### 📝 开发日志

**关键字**：端到端管线, 验收, Skill包, L1→L2验证, SnowNLP

#### 做了什么
- **Task 1**: L1→L2 管线验证通过（因缺 DeepSeek API Key，仅验证 L1→L2 段）
  - 用现有 L1 2000行数据跑 SnowNLP L2 分析：2000行全量通过
  - 极性分布：Very Positive 672 / Positive 275 / Neutral 232 / Negative 269 / Very Negative 552（U型分布，模拟数据预期正常）
  - CSV + GeoJSON 正确导出
  - 全部追踪点触发 (MOD_ANA.F_008/F_009/F_010, MOD_EXPORT.F_001/F_002)
  - check_data_quality.py 硬编码路径已修复，但 L1 段因列不匹配无法运行（旧脚本，技术债务）
- **Task 2**: 用户验收周末改动全部通过
  - 8 Agent 注册正确（pm.agent.md 未注册，作为行为指南保留）
  - PRD (294行) + Spec (436行) 完整
  - .claude 配置：权限/Memory/编排均正确
  - Streamlit 8501 正常启动，所有模块导入正常
- **Task 4**: 安装 .claude Skill 包
  - 4 源合入：anthropics(17) + daymade(64) + python-skills(12) + laurigates(362) = **455 技能**
  - 官方 anthropics/skills 从 Gitea 镜像拉取（GitHub 直连失败）
  - 以 anthropic- 前缀命名空间存放

#### 踩坑 & 收获
- GitHub 直连被重置（网络限制），通过 cncfstack Gitea 镜像成功拉取 anthropics/skills
- check_data_quality.py 是旧版脚本，L1 段期望 `in_scope`/`_kw_pass` 列，与当前 L1 CSV 26列格式不兼容——需后续全面重构
- L2 SnowNLP 2000行 ~6秒，比预期的 10 秒更快
- 455 个 Skill 文件总量 ~11MB，对 Git 仓库体积影响可接受

#### 发现的文档不一致（待修正）
- Python 版本：文档 3.10+/3.13.2，实际 3.14.5
- L1 列数：spec.md 写 20 列，实际 CSV 26 列
- pm.agent.md 未注册但仍在 agents/ 目录（行为指南角色）

#### 🔜 次日计划 (2026-06-16)
- 配置 DEEPSEEK_API_KEY，跑完整 L0→L1→L2 端到端管线
- 修复 check_data_quality.py 适配当前 L1 数据格式
- 修正文档中的 Python 版本和 L1 列数不一致

---

## 📋 每日模板

```markdown
## 📅 YYYY-MM-DD（周X）

### ☑ TODO List
<!-- 当日计划完成的任务，每天 ≤ 3 个大任务 -->

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ⬜ | 做什么 | `xxx.py` | |
| 2 | ⬜ | 做什么 | `xxx.py` | |
| 3 | ⬜ | 做什么 | `xxx.py` | |

> 💡 标准启动指令：`@pm 开始处理 YYYY-MM-DD 的任务 N：任务名称`
> ⚠️ 编号规则：每日任务从 1 开始连续编号，不跳号、不重复。跨日引用使用 `MMDD-NN` 格式（如 `0613-07`）。

### 📝 开发日志
<!-- 记录实际做了什么、踩了什么坑、收获了什么 -->

**关键字**：tag1, tag2

#### 做了什么
- 

#### 踩坑 & 收获
- 

#### 碎片想法
- 

#### 🔜 次日计划 (YYYY-MM-DD)
- 
```

---

## 📅 2026-06-13（周六）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 规划范围真实数据落图（L1治理+坐标转换+范围过滤管道） | `SCRIPT/data_governance.py`（新建）, `core/coord_transform.py`, `core/range_selector.py` | 边界=规划范围(LineString→buffer Polygon)；管道已就绪，24条占位坐标全部被过滤（预期行为），待真实坐标数据后完整验证 |
| 2 | ✅ | Data Agent 创建 + L0→L1 相关性筛选模块 | `SCRIPT/relevance_filter.py`（新建）, `data_governance.py`（重构 v1.1）, `.claude/agents/data.agent.md`, `AGENTS.md` | 两层漏斗：关键词粗筛 + DeepSeek LLM 精分类；Agent 整合入全局调度 |
| 3 | ➡ | L1 治理 + L2 分析 端到端验证 | `data_governance.py`, `emotion_analysis_v1.py`, `DATA/` | 数据爬取暂时放弃，MVP 专注 L0→L2 管线跑通，确保各层数据有价值 |
| 4 | ✅ | 情绪点显示样式优化（颜色/光晕/描边） | `core/config.py`, `core/map_engine.py`, `core/ui_components.py` | Designer 重设计：双层光晕 + Material色板 + Neutral改琥珀色 |
| 5 | ✅ | Design Token 体系搭建（设计令牌系统） | `design/tokens.json`, `design/generate_css.py`, `design/tokens.css`, `design/tokens.py` | Designer 创建完整设计体系：7大类150+token + 自动生成器 + ui_components.py 全部 Token 化 |
| 6 | ✅ | Token 双模式 (Light/Dark) + 设计系统展示页 | `design/tokens.json`(重构), `design/generate_css.py`(重写), `design/tokens.css`, `design/tokens.py`, `core/ui_components.py`, `apps/app_design_system.py`(新建) | Dark/Light 镜像双主题 + prefers-color-scheme 自动跟随 + [data-theme] 手动切换 + 独立 Kitchen Sink 展示页 |
| 7 | ✅ | 主应用集成新 Design Token（低饱和色卡+CSS变量） | `apps/app_main.py`, `design/tokens.css`, `design/tokens.py` | 添加 inject_theme_css() 调用 + 重新生成 Token CSS/Python |
| 8 | ✅ | 修复注记开关 [LB] 导致底图偏移/复位 | `apps/app_main.py` | st_folium() 返回值保存 last_center/last_zoom 到 session_state，rerun 后视图保持 |
| 9 | ✅ | 边界线粗细+颜色可调节（[R]窗口内） | `apps/app_main.py`, `core/map_engine.py` | show_range_dialog 新增 slider(1-20) + 7色 selectbox；add_boundary_layer 动态 hex→RGB + weight 参数 |
| 10 | ✅ | 决策追踪系统 (Decision Tracking System) | `core/tracker.py`(新建), `.claude/agents/debugger.agent.md`, `developer.agent.md`, `reviewer.agent.md`, `AGENTS.md`, `docs/architecture-pattern.md`, `docs/decisions.md` | 决策 ID + 行为 + Log + Tracking 体系；bug 定位 O(n)→O(1)；全局配套更新 |
| 11 | ✅ | 分析控制台柱状图颜色统一 + 按钮状态逻辑重构 | `design/tokens.json`, `design/tokens.py`, `design/tokens.css`, `core/ui_components.py`, `apps/app_main.py` | 图表颜色与地图 POLARITY_RGBA 对齐；按钮"开始分析"→"在地图上显示"双态切换 |
| 12 | ✅ | [LB] 按钮：注记死开关 → 地图底图 Dark/Light 切换 | `apps/app_main.py`, `core/map_engine.py` | 移除 _theme JS 注入；_map_style 控制 CartoDB dark-matter/positron 底图切换；[LM]/[LB] 图标自动切换 |
| 13 | ✅ | R 默认颜色→活力橙 + 新增 [Map] 底图切换 | `apps/app_main.py`, `core/map_engine.py` | 边界色默认 #d97d5c；5种底图(CartoDB深/浅/标准 + 天地图无/有注记)；Designer 优化为 radio+色条预览 |


> 💡 标准启动指令：`@pm 开始处理 YYYY-MM-DD 的任务 N：任务名称`

> ⚠️ 策略调整 (2026-06-13)：数据爬取暂时放弃（后期购买稳定数据），MVP 焦点转为 **L1 数据治理 + L2 数据分析 端到端跑通**，确保每一层产出的数据都有实际价值。

### 📝 开发日志

**关键字**：Data Agent, 相关性筛选, DeepSeek LLM, 两层漏斗, L0→L1 治理重构, 人民城市, 情绪点样式重设计, Design Token 体系, **决策追踪系统, Decision Tracking, Trace ID**

#### 做了什么
- 创建新 Agent：📡 数据管家（Data Agent），定义在 `.claude/agents/data.agent.md`
  - 职责：L0 多源数据采集 + L1 数据治理（坐标转换/范围过滤/相关性筛选/脱敏/字段规范化）
  - 可调用：developer, gis-developer
  - 已整合入 AGENTS.md 全局调度体系（Agent 从 10 → 11）
- 新建 `SCRIPT/relevance_filter.py` L0→L1 相关性筛选模块（~330 行）
  - 第一层：关键词粗筛（30 个广告/灌水关键词），旅游/美食/探店全部放行
  - 第二层：DeepSeek LLM 精分类，判断市民城市感受 → 映射五要素（设施/环境/服务/文化/事件）
  - 批量并发（ThreadPoolExecutor，每批 5 条），3 次指数退避重试
  - 新增 L1 字段：relevance, relevance_dimensions, relevance_emotion, relevance_urban_value, relevance_summary, filter_layer
- 重构 `SCRIPT/data_governance.py` v1.0 → v1.1
  - 管线从 4 步扩展为 5 步：坐标转换 → 范围过滤 → **相关性筛选（新）** → 脱敏+导出 → L2 分析
  - 脱敏时机后移（LLM 需要原始文本做分类）
  - 无 API Key 时优雅降级跳过
- 全部走完整 SOP：Developer → Reviewer（发现 1 个 bug + 1 个优化）→ Developer 修复 → Reviewer 复审 → Tester 测试（17/17 用例通过）
- Designer 重设计情绪点显示样式：双层光晕（外层 radius=13 opacity=0.12 + 内层 radius=7 opacity=0.92 stroke=#fff）+ Neutral 从灰色改为亮琥珀色 #ffd740 → 卫星底图上可见性大幅提升
- Designer 创建完整 Design Token 体系：7 大类 150+ token（color/typography/spacing/radius/shadow/effect/component），含 JSON 单源 + CSS/Python 自动生成器 + ui_components.py 全部 Token 化
- Designer 扩展 Token 体系为 Light/Dark 双模式：tokens.json 增加 theme 层级，Dark/Light 镜像对称（深色半透明底↔浅色半透明底），CSS 支持 prefers-color-scheme 自动跟随 + [data-theme] 手动切换
- Designer 创建设计系统展示页 `apps/app_design_system.py`：独立 Streamlit Kitchen Sink，含主题切换/色板/字体/间距/圆角/阴影/组件全展示
- **PM 搭建决策追踪系统 (Decision Tracking System)**：
  - 新建 `core/tracker.py`（~280 行）：装饰器 `@track()` / 上下文管理器 `TrackContext` / 快捷函数 `trace_*()` / 全局注册表
  - 更新 debugger.agent.md：新诊断流程基于 [TRACE] 日志 + 决策 ID 精准定位
  - 更新 developer.agent.md：新增决策追踪编码标准 + 模块 ID 分配表 + 埋点规则
  - 更新 reviewer.agent.md：新增追踪点完整性审查清单
  - 更新 AGENTS.md：铁律 9/10 + 决策追踪系统说明 + 共享知识库
  - 更新 docs/architecture-pattern.md：增加决策追踪系统章节
  - 更新 docs/decisions.md：ADR-008 决策追踪系统
  - **渐进式埋点完成（13文件55追踪ID）**：全部 core/ + SCRIPT/ + apps/ + SCRAPER/ 模块已添加 @track() 装饰器和 register_track_id() 注册

#### 关键设计决策
- **相关性筛选理念**：从"是否属于城市规划领域"转变为"感知市民对城市的感受与需求"，践行"人民城市"理念
- **宽容原则**：旅游打卡、美食探店、街区体验全部保留（城市活力信号），不确定时倾向于保留
- **LLM 选型**：DeepSeek-V3（已有 API Key + 推理能力强 + 中文理解好）
- **两层漏斗**：先关键词快筛（免费），再 LLM 精分类（API），减少 API 调用量
- **决策追踪系统**：自研 `core/tracker.py`（~280 行），用决策 ID（MOD_XXX.F_NNN / D_NNN）装饰器 + 上下文管理器实现 O(1) 精准 bug 定位；全员遵守铁律 9/10 埋点规范

#### 踩坑 & 收获
- Reviewer 发现 relevance_summary 在 error 分支被覆盖 → 详细字段填充移入 else 互斥分支
- 并发累加计数器是代码异味 → 改为批次完成后从 DataFrame 列值统计
- 情绪点 Neutral 用灰色在天地图卫星底图上完全不可见 → Designer 改用亮琥珀色 #ffd740（绿→黄→红灯语义），双层光晕（外层 radius=13 opacity=0.12 + 内层 radius=7 opacity=0.92 stroke=#fff）大幅提升可见性

#### 🔜 次日计划 (2026-06-14)
- L0→L1→L2 端到端管线验证（准备有意义的测试数据 + 跑通全流程）
- L2 SnowNLP 分析结果质量评估（极性分布合理性、关键词有效性）
- 优化 L2 输出：情绪关键词提取质量 + 可视化落图

---

## 📅 2026-06-14（周日）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | LY 图层 checkbox 修复 + [确定] 按钮 | `apps/app_main.py` | 修复 _all_layers_hidden 不联动 + 新增红色确定按钮（未走 SOP，用户确认跳过） |
| 2 | ✅ | 数据层架构优化：L1_COLUMNS 重排 + v1.0 代码清理 | `SCRIPT/data_governance.py`, `apps/app_main.py` | 走完整 SOP Developer→Reviewer(2轮)→Tester；9组分组重排 + 3个DEPRECATED函数删除 + 残留导入/常量清理 |
| 3 | ✅ | L2 字段规范：confidence→l2_confidence + 新增 L2_COLUMNS | `SCRIPT/emotion_analysis_v1.py` | L2 CSV 列名改为 l2_confidence 避免与 L1 ai_confidence 冲突；新增 L2_COLUMNS 常量(9字段) |
| 4 | ⬜ | 端到端管线验证 L0→L1→L2 | `data_governance.py`, `emotion_analysis_v1.py` | 06-13 延续 |
| 5 | ✅ | L1~L4 confidence 列全局重命名：l1_confidence / l2_confidence / l3_confidence / l4_confidence | `SCRIPT/emotion_analysis_v1.py`, `docs/architecture.md`, `check_data_quality.py`, `SCRIPT/test_scripts_2.py` | 走完整 SOP；L2_COLUMNS 新增 l2/l3/l4_confidence；run_pipeline 按 phase 写入；run_full_pipeline L3/L4 写入对应置信度；架构文档字段表拆分；4 个 TrackContext 埋点 + 4 个追踪 ID 注册；Reviewer 两轮审查 + Tester 9/9 通过 |

> 💡 标准启动指令：`@pm 开始处理 2026-06-14 的任务 N：任务名称`

### 📝 开发日志

**关键字**：LY图层, 数据层架构审查, L1_COLUMNS, v1.0清退, **confidence列重命名, l1/l2/l3/l4_confidence**

#### 做了什么
- 修复 LY 图层控制 checkbox 不生效（_all_layers_hidden 与 checkbox 不联动）
- 新增红色 [确定] 按钮 + 批量操作分区优化交互
- PM 审查 L0→L2 数据管线架构，发现 5 个问题（同前）
- 数据层架构优化走完整 SOP 管线（同前）
- **L1~L4 confidence 列全局重命名走完整 SOP**：
  - PM 全局搜索 → 定位 4 文件 13 处引用
  - Developer 执行：`L2_COLUMNS` 新增 `l2_confidence`/`l3_confidence`/`l4_confidence`；`run_pipeline` 按 phase 条件写入对应置信度列；`run_full_pipeline` L3/L4 步骤分别写入 `l3_confidence`/`l4_confidence`；`docs/architecture.md` 字段表拆分 `confidence` → `l2/l3/l4_confidence`（列数 24→25/28→30/30→32）；`check_data_quality.py` / `test_scripts_2.py` 更新列名
  - Reviewer 首轮发现 3 个问题：① `run_pipeline` 硬编码 `l2_confidence` 未按 phase 区分 ② 4 个 >5 行块缺少 `TrackContext` ③ `TrackContext` 导入未使用
  - Developer 修复：if/elif/else 按 phase 写入 + 4 个 `TrackContext` 包裹（D_003~D_006）+ 追踪 ID 注册
  - Reviewer 复审通过 ✅
  - Tester 9/9 测试用例全部通过 ✅

#### 踩坑 & 收获
- Streamlit `st.dialog` 关闭时不自动触发 rerun → 需要显式"确定"按钮
- 数据层字段顺序对 CSV 可读性影响极大（人工检查时需反复滚动）
- `from pyproj import Transformer, CRS` 中 `CRS` 在函数删除后变为未使用导入，reviewer 静态分析是必要的

#### 🔜 次日计划 (2026-06-15)
- L0→L1→L2 端到端管线验证
- 用户验收本次所有改动

---

## 📅 2026-06-12（周五）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | 情绪数据爬取方案调研+小范围测试（西陵区） | `SCRAPER/data_scraper.py`（新建） | Scrapy 框架搭建完成 + 小红书 Spider 测试通过（HTTP 200） |
| 2 | ✅ | ~~西陵区真实数据落图~~ → 移至 06-13 任务1，范围改为规划范围 | — | 边界从西陵区改为用户上传的规划范围 Shapefile |
| 3 | ✅ | Agent 协作体系搭建：程序开发/调试/进度管理/审查/测试/文档 Agent | `.claude/agents/*.agent.md`, `AGENTS.md` | 6 Agent + AGENTS.md + 架构记忆 + 使用场景，基础搭建完成 |
| 4 | ✅ | 系统架构优化：七层架构 + 空间分析引擎重定义 + 溯佰科定位修正 | `docs/architecture.md`, `docs/decisions.md`, `docs/dev-notes.md`, `memories/repo/architecture-pattern.md`, `SCRIPT/emotion_analysis_v1.py`, `core/map_engine.py` | PM 研判 → Developer 改代码 → PM 同步文档，SOP 首次实战 |
| 5 | ✅ | 环境同步：requirements.txt 补全 + 新增环境管家 Agent | `requirements.txt`, `.claude/agents/ops.agent.md`, `AGENTS.md` | Scrapy 未装、streamlit-folium/shapely/pyproj 漏登记 |
| 6 | ✅ | 跨机协作体系：会话交接卡 + ops 自检 + PM 交接流程 | `memories/repo/session-handoff.md`, `ops.agent.md`, `pm.agent.md`, `AGENTS.md` | 换机 `@pm 同步上下文`，下班 `@pm 下班交接` |
| 7 | ✅ | Agent 扩展：UI设计师/设计审查员/GIS开发员（10 Agent） | `.claude/agents/designer.agent.md`, `design-reviewer.agent.md`, `gis-developer.agent.md`, `AGENTS.md` | 设计→审查→迭代闭环，GIS 专项能力 |
| 8 | ✅ | 初始页面重构：左侧三功能按钮 R/D/A + 全屏地图 | `app_main.py`, `core/ui_components.py` | 极简风格，CSS 统一到 ui_components，emoji 全清 |
| 9 | ✅ | 范围选择引擎：矢量文件上传/CRS检测/缓存/边界叠加 | `core/range_selector.py`, `app_main.py`, `data/boundaries/` | 支持 .shp/.geojson/.gpkg，自动投影转换 |
| 10 | ✅ | 坐标转换工具（WGS84/GCJ02/BD09）+ 宜昌标准 CGCS2000 | `core/coord_transform.py` | 社交媒体→WGS84→CGCS2000 投影完整链路 |
| 11 | ✅ | 爬虫验证：Scrapy 2.16 兼容修复 + 24条小红书数据采集 | `SCRAPER/spiders/xiaohongshu_spider.py` | start_urls 兼容 + explore 页 SSR 提取 |
| 12 | ✅ | 全局代码审查 + UI审查 + 交互审查（三 Agent 并行） | `app_main.py`, `ui_components.py`, `export.py` | 16 项问题全部修复，通过 Tester 验证 |

### 📝 开发日志

**关键字**：Agent扩展, UI重构, 范围引擎, 坐标转换, 跨机协作, 审查闭环, Scrapy兼容

#### 做了什么
- Agent 阵容从 6 → 10 个（新增 Ops/Designer/Design Reviewer/GIS Developer）
- 初始页面重构：左侧 R/D/A 三按钮 + 全屏地图，极简 ASCII 统一风格
- 范围选择引擎：支持 .shp/.geojson/.gpkg 上传，CRS 自动检测转换，边界叠加
- 坐标转换工具：GCJ02/BD09→WGS84，宜昌标准 CGCS2000_3_Degree_GK_CM_111E
- Scrapy 2.16 兼容修复：start_urls 空列表 bug + explore 页 SSR 数据提取
- 全局代码/UI/交互三 Agent 并行审查，16 项问题全部修复
- 跨机环境同步 + 会话交接卡体系
- CSS 统一收归 ui_components.py，空状态引导，emoji 全清

#### 踩坑 & 收获
- Streamlit @st.dialog 内 st.rerun() 导致对话框消失 → 去掉 rerun，利用自动重跑
- file_uploader 残留问题 → 最终去掉对话框内上传，改为读取 data/boundaries/ 目录
- 旧建成区文件 11280 区域导致卡顿 → 清理残留，0.1s 秒开
- Shapefile 单文件无法读取 → 多文件上传 + 子文件夹组织
- Scrapy 2.16 要求 start_urls 非空 → 加占位 start_urls 兼容
- geom.crs 不存在 → 改为 gdf.crs
- 边界只在数据加载后显示 → 空状态也叠加（selected_ranges 判定）

#### 碎片想法
- Tester Agent 必须每次都用，不通过不提交
- GIS 开发员和 Tester 交叉核实 CRS 很有价值
- SHP→GeoJSON 当前方案已足够，暂不需要独立转换工具

#### 🔜 06-13(周六)
- 西陵区真实数据落图（L1 数据治理 + 坐标转换 + 范围过滤）
- 数据爬取方案最终确定（登录 API vs 购买数据）
- 空间分析引擎 MVP（缓冲区分析 + 行政单元聚合）开始编码


## 📅 2026-06-11（周四）

### ☑ TODO List

| # | 状态 | 任务 | 涉及文件 | 备注 |
|---|------|------|----------|------|
| 1 | ✅ | L2/L3/L4 三级分析架构重构 | `emotion_analysis_v1.py`, `config.py`, `map_engine.py`, `ui_components.py`, `export.py` | 五级极性、引擎模板、导出命名统一 |
| 2 | ✅ | 入口统一：CLI + Tkinter + Streamlit 共用 run_analysis_task() | `run_analysis.py`, `app_main.py`, `launch.py` | 控制台合并进 main 为子页面，删 analysis_console.py |
| 3 | ✅ | GBK 编码修复 + docs/ 文档体系 | 全项目 `.py`, `docs/*.md` | emoji→ASCII，\_safe_print，架构规范入记忆 |

### 📝 开发日志

**关键字**：重构, 架构, 编码, GUI, 路由

#### 做了什么
- 重构 EmotionResult 为 L2→L3→L4 三级叠加结构，五级极性全链路更新
- 新增 run_analysis_task() 统一分析入口，CLI/Tkinter/Streamlit 全部调用它
- analysis_console 合并进 app_main，用 `?page=console` 路由，只启一个端口 8501
- 建立 docs/ 五文件（dev-notes/architecture/decisions/todo/scenarios）
- Tkinter GUI 美化，状态栏清晰
- 全项目 emoji 换 ASCII([OK]/[WARN]/[LOAD])，\_safe_print 防崩溃

#### 踩坑 & 收获
- Windows GBK 编码是最大坑——emoji 在 print/Streamlit 中反复崩溃，最终全量替换 + \_safe_print 解决
- builtins.print 劫持导致递归无限循环，改用显式 \_safe_print() 调用
- `?page=console&file=xxx` 路由模式是未来子页面的标准做法

#### 碎片想法
- 三入口统一到 run_analysis_task() 是正确的架构决策
- 导出含 L2/L3/L4 阶段标识，溯源清晰

#### 🔜 明日
- 西陵区数据爬取启动 + Agent 协作体系搭建


## 📅 2026-06-10（周三）及之前

| 日期 | 关键进展 |
|------|----------|
| 06-09 | SnowNLP pipeline 初版、点状地图、CSV/GeoJSON 导出、模块化重构 |
| 05-28~31 | 课题启动：20 轮对话确定三段式框架、技术栈、七大应用场景 |


## 🗂 长期备忘

| # | 想法 | 状态 |
|---|------|------|
| L1 | LLM 大模型接入（溯佰科平台 Agent 嵌入） | 🟡 demo 已接 DeepSeek（chat-panel + llm_client provider-agnostic），待换溯佰科底座 |
| L2 | 时序分析（多时间切片对比） | ⬜ |
| L3 | 行政区划聚合视图 | ✅ 已落地（Range tab 预设范围库 + grid-tool「指定单元」zonal + 4×5 归因 + Overview 矩阵/Top5） |
| L4 | 自动报告生成（PDF） | ⬜ |
| L5 | 空间自相关分析（Moran's I） | ⬜ |
| L6 | 问题-对策映射引擎 | ⬜ |
| L7 | Docker 部署 | ⬜ |
| L8 | 配置外部化（.env） | ⬜ |
| L9 | 移动端适配 | ⬜ |
| L10 | 语料库本地化词典 | ⬜ |
| L11 | 空间分析引擎 MVP（缓冲区分析 + 行政单元聚合） | ⬜ |

---

## ★ 单元深读候选池（关键词 × 3-5 候选聚合域；2026-07-04）

> 9 代表词（每极性 3），每词列 3-5 个候选聚合域（锚点·narrative_zone·domain×element）。
> **下会话进 plan：每词从候选池筛 1-3 个典型单元网格做最高优先级深读**（用户主导筛选）。

| 关键词 | 极性 | 主 domain×element | 目标聚合域（3-5） |
|---|---|---|---|
| 网红 | pos | 运营×服务/文化 | 大南门(ermawu) · 二马路历史街区(ermawu) · 夷陵广场CBD(commercial) · CBD万达(commercial) |
| 夜经济 | pos | 运营×事件 | 滨江公园/沿江大道(riverside) · 西坝不夜岛(riverside) · 奥体(venue) · 二马路(ermawu) |
| 大南门 | pos | 更新×文化/服务 | 大南门(ermawu) · 二马路历史街区(ermawu) · 解放路步行街(ermawu) |
| 楚超火爆 | pos | 运营×事件 | 奥体中心(venue) · 奥体周边餐饮(commercial) · 五一广场(commercial) · 滨江公园(riverside) |
| 卷桥河露营 | pos | 规划×环境 | 卷桥河湿地公园(park_plaza) · 江南URD绿地(residential) · 点军滨江(riverside) · 鄢家河郊野(park_plaza) |
| 江南绿肺 | pos | 规划×环境 | 江南URD(residential) · 卷桥河湿地(park_plaza) · 江南丘陵(park_plaza) · 点军滨江(riverside) |
| 停车难 | neg | 治理×设施 | 夷陵广场CBD(commercial) · CBD万达(commercial) · 国贸/铁路坝(commercial) · 奥体(venue) · 吾悦广场(commercial) |
| 占道停车 | neg | 治理×设施/环境 | 夷陵广场CBD(governance×facility) · 万达/国贸(governance×facility) · 二马路/大南门(renewal×environment) · 桃花岭老旧小区(planning×facility) · 滨江人行道(governance×environment) |
| 堵车 | neg | 治理×事件 | 东山大道(traffic) · 胜利三路(traffic) · 云集路(traffic) · 中南路(transit_hub) |
| 口袋公园 | neu | 规划×环境 | 街角口袋公园(park_plaza) · 儿童公园(park_plaza) · 滨江公园(riverside) · 夷陵广场(park_plaza) |
| 业态 | neu | 运营×服务/文化 | 夷陵广场CBD(commercial) · 铁路坝商圈(commercial) · 二马路(ermawu) · 大南门(ermawu) |
| 社区服务配套 | neu | 更新×设施/服务 | 桃花岭社区(residential) · 翁家堰社区(residential) · 行署小区(residential) · 江南URD(residential) |

**下会话筛选提示**：二马路/大南门(ermawu) 跨 pos 三词 + 占道停车共现，是天然高频区；但「1-3 典型格/词」由下会话讨论定。

> **本会话（07月06日 00:46）**：典型格大头针方案试做→用户否（"表达差/关键词越改越少"）→全回退（净 0 代码）。单元深读**重新设计定向**——Q2「推荐深读」清单+cluster①分级（替大头针）/ Q1 四板块·结论先行 / Q3 闭合「看同类」。关键词数量修 floor 10+平坦扩 15（旧"覆盖80%"陡分布时<10）。详见 revision-log 5.24 + 交接卡。**下会话先做 Q2。**

---

## ★ 本会话（07月13日）·5.83 沙箱挂 /run + 三道底线加固

> 字段语义层 P1-P3 收完后挂 /run（AI 助手自写 Python 出图的兜底能力）。沙箱原 `SAFE_READY=False`，补三道底线后切 True 挂载。用户拍板「演示版+底线加固」，不做 Job Object 硬限，定位本地单机演示。

**完成**：
- [api/sandbox.py](api/sandbox.py) 加固①② + MPLCONFIGDIR + SAFE_READY=True：open-wrapper（写必查 workdir 白名单/用户帧读查/库帧读放行）+ AST 反射审查 4 类拦 + frame-based eval（用户帧禁/库帧放行）。**关键 bug**：wrapper 须补 globals/locals=真正调用帧还原 eval 默认语义（否则 numpy.f2py `eval('lambda v,f=f')` NameError + importlib `exec(code,module.__dict__)` future ImportError）。
- 新建 [api/run_routes.py](api/run_routes.py)：POST /run（RunIn + run_sandbox + _encode_images figId=fig{n} 纯 ASCII）。
- [api/main.py](api/main.py)：CORS 收紧本机（allow_origin_regex）+ if SAFE_READY 条件挂载 run_router。
- [frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js)：run_python 工具（第 15）+ _figCache/getFig/clearFigCache + fetchRun（不调 addResultLayer，observation 用「图片」避对账）。
- [frontend/js/ai_qa/panel.js](frontend/js/ai_qa/panel.js)：_renderFigs（{{fig:ID}}→`<img>`，照 _renderCharts）+ enhanceCodeBlocks 调用。
- [ai_qa/paradigm.py](ai_qa/paradigm.py) CODE_EXEC_CATALOG + [ai_qa/prompts.py](ai_qa/prompts.py) run_python schema 行（花括号双写）+ build_agent_prompt 拼 catalog。
- [tests/test_sandbox.py](tests/test_sandbox.py) +9 加固测试（反射 4 + open-wrapper 2 + frame-based eval 3）。

**验证**：pytest tests/test_sandbox.py **28 passed**（19旧+9新）；post_run 端点真调（matplotlib 出图→fig1+dataUri / 反射端点级拦 / data_refs 注入 rows 2）；openapi 确认 /api/v1/run 挂载（total 34 paths 现有路由全在）；node --check + py_compile 全过。

**承重**：不破 frame-based trust（库帧 lazy-import/lazy-open/eval 放行，pandas/matplotlib/numpy 不误伤）/ 5.74 对账（figId 纯 ASCII + 「图片」措辞不进 verbRe/showRe）/ SAFE_READY 单点 revert（改回 False gate 自动卸载 /run）/ run_sandbox 永不裸输 / 演示版非 OS 隔离（内存 CPU 仅超时软限、别名反射 AST 拦不住靠禁 eval 收敛——文档化，生产须叠容器）。详见 revision-log 5.83。