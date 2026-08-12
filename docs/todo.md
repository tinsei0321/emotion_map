# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。
> 📝 详版历史 = [revision-log §5](revision-log.md#L226)（永久审计底）·本文件只记当前 + 计划。
> 📌 **架构版本**：v1（三阶段 5.231-5.242）→ **v2（单次 LLM + FC·5.243-5.245b·第三方实施）** → **v3（v2 做对·5.246-657c2e3·GLM 修复）** → **v3.1**（reg.filter 崩溃修复 + SCAN P1）→ **v3.2**（CB-09 bug 修复·D057 修订·代码自动扩展·全自动多步执行·fix/emc-buglog 分支 7 commit）→ **v3.5**（CB-10/CB-11 系列·merge 多图层 + 只说不做根治）

---

## 📅 2026-08-12（12345+体检统一分类对标重构 · 三组讨论回收 → 收敛定稿）

### ✅ 三组讨论回收 + 收敛定稿（本轮主线）

- [x] **Codex 回应回收**（10 焦点·6 agree + 4 partial）：映射最小单位=中类·12 项目类型定稿·213 小类继承+跨界<20·体检/12345 共用项目类型层·4 列落结构·子维度更正 17→16·4×5 兜底表·问题整治独立 agree
- [x] **zcode 回应回收**（5 焦点·1 partial + 4 agree）：先出分类映射表再加列（战略 1）·10 中类偏粗建议·矛盾/社会治理独立类 0.9%·板块→中类→小类·附件2 归整治成效（低优先）
- [x] **收敛定稿**（`docs/catch-ball/discuss/CB23-12345分类对标重构_收敛定稿_2026-08-12.md`）：12 类取 Codex（噪声治理独立贴合用户例子）·矛盾拆+残留归其他（两案合并）·智慧高效按项拆分（zcode 案）·列结构合一（层次 3 层 + 落结构 4 列）·执行顺序=映射表→加列→重跑→diff 校验→三组复核
- [x] cb-journal 追加本轮（讨论回收+收敛定稿闭环）

### ✅ 用户纠正重分类（不强行归拢）→ 两组优化意见回收 → 收敛定稿 v2 → 全局执行

- [x] **用户纠正**：77 项不能全归两板块（绿色智能=附加类≠民生基础需求·基础需求=急难愁盼）·12345 同理 → 重分类（安全17/民生29/其他30/整治1 + 12345 侧重排）
- [x] **两组优化意见回收**（`CB23-分类对标重构_重分类_两组优化讨论发起` + 意见 2 份）：F1 三标准 agree·F2 22 项移出 agree·Codex 小类级切分 4 处实测（道路通行 2634→民生/消防通道 442→安全/停车场设施 518→民生/毁坏桥梁 11→安全）+ 堡坎 215→安全（两组独立发现）·zcode 整体归边不取（442 实测 38.6%）
- [x] **收敛定稿 v2**（`CB23-12345分类对标重构_收敛定稿_v2_2026-08-12.md`）：三标准判据（安全=生命财产/民生=急难愁盼/其他=附加）+ 判据注释表 + 双口径呈现 + 执行计划
- [x] **全局执行**：① `12345_分类映射.json` v2（42 中类主表 + 小类覆盖含供水供气服务类→民生）② 治理脚本加 4 列重跑（**民生 49,192 85.9% / 安全 8,046 14.0% / 其他 27**·无 None·全核对过）③ 77 项 board 重落（17/29/30/1·主题分类零矛盾）④ 问题清单 board 同步（59 行零缺失）⑤ 05 链条板块核对（已对·不动 project_type）⑥ checkup_12345_2024 重导出（25 列含 4 新列·emotion_intensity 保留前端兼容）⑦ manifest 1.5.1
- [x] pytest **320 passed 零回归**

### ⬜ 下一步（分类对标重构收尾 + 出图数表讨论）

- [ ] 三组复核（v2 执行结果：占比 85.9/14.0/0.05·判据注释表待 zcode 落）
- [ ] 出图数表讨论（重构后·当前唯一门槛）→ 3' 开动
- [ ] 出图数表讨论（重构后）→ 3' 开动

---

## 📅 2026-08-11（紧急任务·城市体检两板块分析·数据/工具/管线全就绪·收工回家换环境）

### ✅ 数据质量闭环 + 官方行政数据 + 出图数表讨论待定（今日主线·详细）

**数据治理与审计（全链路）**：
- [x] 12345 原始数据治理（57265 行·用户提供 `2024年12345投诉数据_raw.xlsx`）→ 治理清洗版 + 情绪地图中转版（polarity 5级/score 0~1/4×5/topic/place/region_scope/cross_region）·`06_主观数据治理/` 两份 + 4x5 映射 + 方法论（模拟数据黄金样本）
- [x] 12345 geocode 回填（clean 地名 80% 命中·region 质心兜底·离群过滤 93→0·PII 车牌0/人名0）·注册 `checkup_12345_2024` 层（18171 有坐标·中心城区 77%）
- [x] 项目端数据（用户提供·十五五储备表 excel 183 项目 + 重点项目 gdb point185+line102=183·gdb 只读导出 GeoJSON·excel 匹配 99%）·注册 `checkup_project_point/line` 层
- [x] **官方行政数据**（用户插入·市域县级 14 县区 + 村社区 1682 shp·SSX 聚合 113 街办含 16 街办口径）·admin_street/community/county 注册·社区 94MB reference_only·**街办 zonal 打通**（宝塔河 3066）
- [x] **数据质量修复**（两组全局审计 Codex 2P0/8P1/12P2 + zcode 3P0/12P1）：P0-1 双轨 buffer 4546（双高格 1768→16）·P0-2 12345 治理（噪声 53%→0.05%）·P1-1 admin_county·P1-2 cross_region 664·P2-3 extract_event·P2-4 16 街办对齐·P2-6 趋势聚拢标注·PII 过滤（车牌容忍空格/人名·脱敏红线达标）
- [x] 管线测试 6/6（体检/12345→密度·双轨→双高·项目聚拢 64%·zonal sum·hotspot 守卫）·双轨密度完整版（双高格 16）
- [x] 趋势聚拢验证：12345→项目 57%/81% 落高密度格（统计显著·方法可复现）

**术语/统计**：
- [x] **街办术语统一**（街道→街办·全局·CLAUDE.md 铁律·分派三组·claude 代码层完成）
- [x] **三组犯错统计**（claude≈87%/Codex≈29%/glm-zcode≈77%·glm→zcode 更名合并·角色不对称声明）

**跨项目协作（CB）**：
- [x] 每轮进 CB 两组审计（数据质量/管线双轨/行政数据/闭环验证全回收）
- [x] zcode 数据侧分工（CSV 重构/列错位/专家评审/manifest v1.4.6）+ 街办术语分派
- [x] 定位修正：**分析不依赖片区边界**（片区=结论·问题聚集推导·CLAUDE.md 铁律7·分析过程不预设片区·边界供团队叠加）

### ⬜ 下一步（出图数表讨论 + 3' 分析）

- [ ] **出图数表讨论**（图1-4 呈现链·2×3 矩阵汇报框架·分析内容×方法×结果形式·Codex 方案 A）→ 定稿后 3' 开动
- [ ] 3' 两板块分析（安全韧性 + 民生·问题→项目趋势聚拢·不卡边界）
- [ ] 4' 分析报告（图/数/表/观点 + 口径对照 + 缺口清单 + 出口卡对接·不等边界）

### ✅ 阶段 1'+2' 完成 + 空间落位铁律全局修改（后续补充）

- [x] **阶段 1' 后端小扩展 A1/A3/A4/A5/A7**（b8828c54）：grid agg_cols / hotspot 常数+NaN 守卫 / 聚合 _sum / zonal sort_by / presets manifest 修·320 passed
- [x] **阶段 2' RAG**（595a6369）：15 CHK fact→CHECKUP_FACTS（all_facts 52→67）+ outlet_kb 客观轨契约 + RAG摘要落 00-09 + 索引重建 258→295·冒烟命中
- [x] **Codex 审计回收**（3 P1 修正）：zonal 响应补 _sum / A3 NaN dropna / checkup_two_panels→PANEL_MAPPING·零 disagree
- [x] **zcode 思路对齐·全局修改**：空间落位口径铁律入 CLAUDE.md（4维度控件对象=输入·片区=结论推导）+ plan 覆盖矩阵两段化 + 主观轨落图（12345 514处·双轨对照）+ D1 图面=网格聚合倾向
- [x] 回应 zcode 2 疑问：聚集趋势四维 / 情绪地图价值=12345 真实声音落图

### ✅ 阶段 0' 对接层（读定稿+交接卡+Codex 评估 → 全交付）

- [x] 读 `emc-rag-emc-wise-lark.md`（定稿五阶段·Codex 7 修正+6 决策全采纳）+ 交接卡 + Codex 评估 + zcode 中转站 manifest v1.1.0 实读
- [x] **`DATA/exchange/` 对接层四件套**：README（三分法）+ manifest.json（引用清单 19 层 + copy + derived）+ schema_inventory.md + PII_EXCEPTIONS.md + 口径对齐.md
- [x] **PII 实读**：`building_50year_1.geojson` 380 要素 `yslxr/yslxrdh` 字段全存在（值空格）→ 只引用不复制·派生层剥离；`存在问1` 照片 URL 不入库；验收扫描零残留 ✓
- [x] **口径漂移确认**：manifest「20 项」vs 实表 18 行 → 以实表 18 项为权威
- [x] **追踪模块 ID 决策**（D5）：新增 `MOD_CHECKUP`（`SCRIPT/checkup_ingest.py`·F_001 起）·AGENTS.md 登记
- [x] 副本落位：03-08 摘要 → `00-宜昌专项/03-08...md` + `_INDEX.md` 00-08；`_PATHS.md` 扩展第三环境 `D:\OneDrive`；context-map + AutoMemory 登记
- [x] revision-log §5 + todo 08-11 段同步

### ⬜ 下一步（阶段 1'）

- [ ] checkup 直通适配器 `SCRIPT/checkup_ingest.py`（WGS84 透传·无 LLM 漏斗·L2 旁路·L1 导出 + geo_registry 注册 + 面层 preset + 质心点层·坐标透传单测·MOD_CHECKUP F_001 起）
- [ ] 风险前置验证：zonal 对「指标数值字段」聚合 + 面层质心化后 hotspot 可用性（防阶段 3 返工）

---

## 📅 2026-08-10（CB-22d 地图标记路径跑通闭环 · 收工 · 分支合并 main）

### ✅ CB-22g 追问无法完成·反评价收敛定稿 + P0 实施 + 2025体检整合入RAG（收尾·待 push）

- **背景**：CB-22f 5 阶段实施后用户实测追问仍失败 → 上轮两组评估已出 → 用户「连带本次体检整合一起修复·先进 CB」
- **两组反评价收敛**（采纳 Codex 主线）：诚实记录 claude 上轮 trace 取证错误（sess-22008 实为 pytest 非 user session·F_005=build_diagnose_prompt≠FC）→ **坐实 4 根因**：① F_016 编号冲突 ② FC 端点缺埋点（trace 盲区）③ knowledge_qa 零参 schema 可疑 ④ 旧 SSE diagnose 死路径
- **P0 四批全落地**：
  - [x] 批1 编号冲突 + stages bug：query_knowledge_base `@track F_016→F_018`（解 build_outlet_schema 冲突）+ stages.js:322 `question→ctx.question`（fcDiagnoseStep ReferenceError·glm 发现）
  - [x] 批2 track_ids 全仓守卫：新增 `tests/validate_track_ids.py`（ast 解析·只认语法树装饰器节点·正则版误判自身 docstring 已废·15 装饰器零 DUP·防复发）
  - [x] 批3 体检整合：md 移入 `00-宜昌专项/03-07_` + **16 fact 补空间落位**（I09-I16/C05-C07/P09/P10/P12/M04/M05·36→52）+ P01/P11 顺手修 detail>80 字违例 + 索引重建 + 6 组检索全命中
  - [x] 批4 FC 埋点 F_019：router.py `_fc_gen` 手动 enter/exit/error（`@track` 不适用生成器·tool_calls/tool_name/_fcError 落 trace·FC 从此可观测）
- **验证**：**315 passed + 3 skipped 零回归**（基线 315）·validate_track_ids 2 + validate_knowledge_route 5 + validate_rag_material 9 全过·schema 自校验 detail≤80 字
- [ ] **待 push**（用户手动）+ **P1 待用户**（knowledge_qa 零参 schema 浏览器冒烟 + 重采真 session 取证）+ **P2 独立**（F_009 DEM error / F_005 KeyError lon_gcj02）

### ✅ 分支合并：fix/emc-buglog → main（收敛·删分支·保持干净）

- **合并**：`fix/emc-buglog`（368 提交·含 CB-22d 全链）→ `main` · merge commit `b77daef`（保留全部历史 + 本地 main 的 `81784f0` mcp 配置）
- **推送**：`git push origin main`（`76124d6..b77daef`）
- **删分支**：本地 `git branch -d fix/emc-buglog` + 远程 `git push origin --delete fix/emc-buglog`
- **当前**：唯一分支 `main`（本地 = 远程 origin/main = `b77daef`）·工作区干净
- **⚠️ 双环境提醒**：**公司/家里 git pull 后需更新分支引用**——`git fetch --prune origin`（删本地过时 `origin/fix/emc-buglog`）·**另两组（Codex/glm）只读本地不 git**·claude 已 push main·它们读本地 main 即最新（勿再引用 fix 分支路径）

### ✅ CB-22d 知识问答→地图标记·路径跑通闭环（用户实测成功·两组复验通过）

- **背景**：追问「能在地图上标记出这些项目的位置吗」→ 首版全未匹配 + 停半途 7 分钟 → **三证合一根因**（trace + 用户思考内容 while-loop + 两组复验预判）
- **用户两想法**（北极星）：① 地点模糊搜索须 LLM 参与·非纯算法硬匹配（业界=意图分层+分词+加权·高德专利）② 无法识别地点就放弃·像人思维·不能 while-loop 无限思考
- **两组根因修正**：Codex（挂起=finalStep 单调用·names 拼接串·冷加载·依赖缺失）·glm（数据缺口=匹配入口未分词·补单轮超时）
- **实施**（commit `ace4f8f`·路径跑通）：names split + 冷加载20s + rapidfuzz/pypinyin装 + 高德优先(amap_first) + A0 jieba分词双路 + 聚合名放弃(_isAggregate) + **B1 零命中零LLM出口（根治挂起）**
- **验证**：307 passed 零回归·validate 9 断言·路径跑通 8/9·两组复验均通过·用户实测「基本成功生成正确图层」
- **后续（非阻断）**：见下方「公司待办」

### 🔴 公司待办（08-10 上午·OFFICE 卡·**当前在 main 分支**）

> ⚠️ **到公司先 `git pull`（拉 main 最新）+ `git fetch --prune origin`**（删本地过时 fix 分支引用）·当前开发在 **main**·不再用 fix/emc-buglog。

- [x] **分支同步**（office 08-10 上午）：本地 fix/emc-buglog 已删·仅剩 main·交接卡漂移修正 commit `52040f10`（未 push·网络暂断）
- [x] **环境恢复 + 分支同步**（office 08-10）：目录残缺→fetch origin（`0fdd64c`）→checkout main→删 fix 分支→唯一 main 与远端对齐·工作区干净
- [x] **CB-22e 地图标记准确度与防护·反评价收敛定稿**（两组回收·P2 前提修正实锤 N/M 断链 + P1 四件套定稿 + P3 落点修正·**并入 CB-22f 实施**）
- [x] **CB-22f 纯问答→空间动作链路由打通·反评价收敛 + 详细讨论最终定稿**（8 焦点 4 agree+4 partial·两组详细回应回收·**Codex 2 修正** + **glm 3 修正** 已核实·**最终定稿 5 阶段**）
- [x] **CB-22f 实施完成**（今天任务·已过 CB→实施完毕）：
  - [x] 阶段0 CB-22e P2+P1：降级结论选行 + 准确度四件套（_core_entities 候选表/中心挡词/_WHOLE_AGGREGATES/独立 Tokenizer+yichang_places.txt/amap 标注）
  - [x] 阶段1 CB-22e P3：test-cases B3 用例（RST-L07）+ 桩测四场景（N/M 断链修复验证）
  - [x] 阶段2 A 路由打通：knowledge 伪工具 + 三分支 + 方案 A 兜底 + FC 纪律 + validate_knowledge_route 5 断言
  - [x] 阶段3 B 识别+衔接：fact meta 透传重建（region/topic/year/keywords 验证）+ ctx.extracted 实体清单级 + priorTurn 回灌 + _followupCue 分类器（8 场景 PASS）+ recover 扩 analyze/compare
  - [x] 阶段4 D RAG 收尾：query_knowledge_base（**F_016**）+ fact 加权×1.2（3 测试）
  - [x] 验证：**315 passed + 3 skipped 零回归**·serve 重启新代码加载验证
- [x] **CB-22h 追问读秒卡住·三组根因收敛 + 修复**（glm 承重根因 `_assembleKnowledgeQA` 无降级兜底 → P0-1 catch 降级 / P0-2 总 deadline / P0-3 httpx 分段 / P1 预热同步）
- [x] **CB-22i 追问标记崩溃根因定位修复**（Playwright 抓 console 定位 `PAGEERROR: JSON.parse(...).slice is not a function`（panel.js _distillTurn extracted 回灌对象 .slice）→ 修对象属性限制·**完整链路实测通过**：首问 11s + 追问标记 7s 出「宜昌城市更新项目点位」图层·0 挂起·PAGEERROR 消失·commit a27c0e2e）
- [x] **CB-22i Timer 主动中断修正**（Timer 移 `client.stream()` __enter__ 前·覆盖等响应头阻塞·本地挂死 server 1.0s 中断验证 + serve 反代 50s 超时 + 前端 Promise.race）
- [ ] **CB-22i 用户浏览器实测**（强刷 Ctrl+Shift+R 后完整链路：首问→追问标记出图层·若仍异常抓 console PAGEERROR 发我）
- [ ] **CB-22f B3 飞轮实跑**（留后验证）· **CB-22f 动作链 2 步 demo**（标记→分析·Phase2 多步·预载 L2）
- [ ] **A1 GIS 甄别 / tier-2 面化 / A3 项目库坐标**（G 盘 GIS 重活·**单独轮**）
- [ ] RAG 遗留（OFFICE 卡）：B 路径 query_knowledge_base · 混合检索 · 全仓 [中文]+类 扫描 · Recall@5 · P0-6 复审

## 📅 2026-08-09（城市更新专项规划知识库构建 CB-21b · L2 任务 + RAG 计划）

### ✅ CB-21b · 城市更新专项规划知识库构建（主体完成·三组协同）

- **背景**：用户接到《城市更新专项规划》（宜昌城区）研究任务·需权威资料（政策/指标/案例/体检/GIS）+ 沉淀 EMC 知识库。G 盘 `15_城市更新专项规划研究`（875 文件·真实权威）。
- **L0 资料库**（`docs/urban-renewal-plan/`·主体完成）：00-宜昌专项 8 份 + 政策 12 + 指标各城对照 + GIS 31 图层 + 上海/杭州/广州/成都案例 + 总览报告 + 完成度清单
- **L1 知识库**（`ai_qa/industry_kb/urban_renewal.py`·完成）：TOP_DESIGN 6 + CORE_FRAMEWORK 10 + KEY_TERMS 9 + METRICS 7 + CASES 8 + PROJECT_TYPES 9——**305 passed 零回归·final_brief 1625B<6000**
- **三组协同**：claude（GIS/体检/专项规划/上海考察）+ codex（政策/指标/PPTX/伍家岗十五五）+ glm（编制导则识图/湖北 OCR/南湖）
- **收尾项**（低优先·已登记）：湖北导则 OCR P0 章节·北京 OCR·伍家岗图册·PPTX 图表

### ✅ CB-22 三层架构优化实施完成（今日收工·全链闭环·用户实测通过）

- **背景**：用户复测「宜昌市城市更新的项目有哪些？」出图层失败 → trace 取证（词序变体击穿短路 + diagnose 无知识问答通道）→ **用户拍板「NL 意图判断必须通过 LLM」** + **三层架构**（数据层三库/实施层 Smart·Dumb/表达层三段式）→ 两组三轮讨论（6 焦点 + 0b/0c 性能根因 + 执行前验证 8 焦点全 agree）→ 实施
- **P0 意图判断归位**（commit `24e6ab0f`）：diagnose 加 `knowledge_qa` 枚举（对比句判据 + 续作例外·**红线豁免记录** KNOWLEDGE §1）+ _quickIntent 降级加速器（6 词最小化·漏网落 diagnose LLM 判）+ `_assembleKnowledgeQA` 合流（短路+diagnose 双入口·data_plan 三态 score≥0.5）+ 分通道增强（ctx.context 条件注入·D019 不动）
- **P1 概念库**（9 条 3 类·type='concept'·产品定位/方法论/边界认知·摘抄+引用禁重述）·索引 235 条
- **P2 防回归**（触发正负例语义更新/枚举断言/知识问答路由 e2e·injectOnly 确定性消 flaky）+ **P3 出处**（URP-P01 双来源）
- **素材术语去硬造 + 来源标注弱化**（commit `39f51265`）：URP-P01/笔记:43/总览报告去「典型片区类/机制建设类」硬造分类·罗列式·来源标注 `〔来源：可读名称〕` + CSS 0.85em 浅灰弱化
- **杜绝概念创造 3 层治本防线**（commit `3b07d52a`·用户「记住」）：① 素材清洁（全仓零残留·黑名单断言）② 提炼纪律（**CLAUDE.md 铁律 13** + KNOWLEDGE + AutoMemory）③ LLM 自创防线（指令 3 禁推断分类/解释 + 黄金集概念清洁断言）
- **验证**：全仓零残留 · validate 9 + pytest 307 + e2e 7 全绿 · 用户实测通过
- **待续（RAG 遗留·明天继续推进）**：见下方「🔴 遗留 RAG 工作」

### ✅ 家环境同步（08-09 晚·pull 公司全链后）

- **pull 同步**：`434a604..56cd67b` fast-forward（公司 08-09 全链·无冲突）·push @ `3abe31e`
- **进度同步 + 环境检查发两组**：`discuss/进度同步与环境检查_讨论发起_2026-08-09.md`（3 焦点 + 附 A prompt）·HOME 卡更新
- **RAG 补链完成**（用户要求补齐环境）：torch `2.13.0+cpu`（阿里云镜像·PyPI 无 +cpu 标签）+ BGE 模型 + 索引 235 条 + 检索冒烟通过
- **三组进入状态通知**：`_handoff/三组进入状态通知_RAG补链完成_2026-08-09.md`（push @ `a3fadcf`）
- **双环境路径补齐**：`_PATHS.md` + `README.md` 家庭 `C:\Users\Hi\OneDrive\...`（878 文件实测·push @ `aa05543`）
- **AMAP_KEY 恢复**：历史会话找回 `7294b86...` → .env 补回 + 高德 API `status=1` 有效
- **三组记忆完善**：KNOWLEDGE §2 沉淀 2 条 + AutoMemory `rag-chain-bringup` + `_handoff/三组记忆完善prompt_2026-08-09.md`（push @ `a967253`）
- [ ] 等两组回应 + 记忆同步确认 → /cb 反评价收敛 → 发 RAG 遗留任务分配

### 🔴 遗留 RAG 工作（明天继续推进·重要）

- [ ] **用户复测本轮全链**（无硬造分类 + 来源弱化·公司电脑·通过后已 push）
- [ ] **B 路径（CB-22b·query_knowledge_base 确定性查询）**——RAG_QUERY_KW 临时结构化词（有哪些项目/体检问题等）待迁移·`knowledge_query` 范式已预留
- [ ] **混合检索**（glm/Codex 共识·P1）：fact 加权或 Top-5 保底 ≥1 fact·降 note 占比（当前「有哪些更新项目」Top-5 全 note·fact 短文本向量信号弱）·提升素材精度
- [ ] **全仓 `[中文]+类` 扫描 + 逐条核实源文档**（黑名单机制 + 人工审新词·防误拦官方词）
- [ ] **Recall@5 素材质量机制**（Codex V5·黄金集 Recall≥80% 持续跟踪）
- [ ] **P0-6 分通道 tier 复审**（暂缓·flash 保持·路径跑顺后**勿忘**·glm 提醒：知识问答开 pro 综合深度）
- [ ] L2 出向任务（outlet_kb 接入运行时·进 CB 讨论）

### 🔄 L2 出向任务（进 CB 讨论·定稿执行）

- **内容**：让新增知识库贯通 EMC"出口"——L2 出口契约对接知识库（outlet_kb 接入运行时·体检-更新衔接契约·具体项目问答支撑）
- **状态**：进 CB（L2 任务讨论发起）→ 两组评估 → 定稿执行
- **CB 支撑**：后续开发参考本知识库·尤其是 EMC"出口"

### 🔄 CB-22 三支柱对齐实施（两组回收全 agree → 实施修正 → 待两组复验）

- **两组对齐回应已回收**（`CB22-三支柱对齐_{Codex-GPT5|glm组}_2026-08-09.md`）：6 焦点全 agree·glm 诚实承认零 LLM 错误（过度防幻觉·忽视 LLM 综合是三支柱之三·原则升级 = trace + 产品意图对齐）·Codex 挑战 3 条（认领无挑战·零 LLM 边界显式限定·指令治本是幻觉）
- **⚠️ 承重发现（两组未检出）**：rag 索引 meta **不存 text**·注入 finalStep 的"素材"仅文件名·LLM 无内容可综合（三支柱①空转·验收 V2 结构性不可过）
- **实施修正 5 项**（黄金集 5/5 + pytest 305 零回归）：
  - A 素材内容注入：`rag_index.py` meta 存 text + search 透传 + `harness.js` 注入片段全文 + 四指令（强标记/只基于素材/综合 Top-N/禁图层·finalStep LLM 综合保留）
  - B PARADIGM_MAP 注释修正（"确定性组装·零 LLM"→"知识问答·LLM 综合"·注释曾与实现矛盾）
  - C **新单测** `tests/validate_paradigm_map.py`（5 断言·含零 LLM 防回归机器化）
  - D KNOWLEDGE 蒸馏 3 条（零 LLM 边界/LLM 综合边界/§7 规则 5 交叉挑战）
  - E 端点测试补 text 断言（防素材回退文件名）
- **两组复验已回收 + 反评价收敛定稿**（[复验回应 ×2](docs/catch-ball/discuss/) + [反评价收敛定稿](docs/catch-ball/discuss/CB22-三支柱对齐_反评价收敛_定稿_2026-08-09.md)）：
  - **P0 定性**：glm e2e 失败 = 环境非回归（claude 复跑 PASSED·整组 5/5 全绿）
  - **P1 已修**：finalStep 断言精确化（`await stages.finalStep(ctx, hooks, '')` 精确调用点·Codex 挑战 2）
  - **P2 已修**：注入体积守卫新测试（snippet ≤1000B + k≤5 + 指令行数有界·预算 ≤8KB 文档化·Codex 挑战 1）
  - **B5 留用户实测**：指令优先级（ctx.context 强标记 vs FINAL_TEMPLATE 图层导向·两组标核心看点）
- **状态**：定稿可推 → **用户手动检查**（清单见定稿文档附：①知识问答主路径 ②准确性 ③全面性 ④稳定性 ⑤边界负例）
- **待续**：push 后 B 路径（CB-22b·query_knowledge_base 确定性查询·RAG_QUERY_KW 临时结构化词待迁移）·Recall@5 素材质量机制待建

### ✅ RAG 建设（本周重点·已完成主体）

- **背景**：用户问"宜昌有哪些更新项目"→ 暴露 EMC 只注入不检索·需 RAG（向量化 L0/outlet_kb）
- **已完成**：本地 BGE embedding（Py3.14 装好·HF 镜像）·事实卡 35 条（L1.5·`urban_renewal_knowledge.py`）·索引 225 条·`/aiqa/rag_search` 端点（F_017）+ harness `rag_query` 短路·黄金集 3 类 100%·e2e 5/5
- **修复**：serve 启动预热（消冷加载 18.6s）·EXIT_CONCEPT 兜底·超时 30s（CB-22 根因：冷加载>超时→RAG 丢失）
- **机制完善（分类→范式映射）**：CLAUDE.md 铁律6·rag_query 注入素材→finalStep LLM 综合（非零 LLM）
- **待续**：B 路径（CB-22b·query_knowledge_base 确定性查询）·收窄 RAG 触发词

### ⭐ 关键经验教训（跨轮蒸馏·指引后续开发）

- **三支柱**：纯回答稳定性 = 本地知识库完备度 + EMC 架构（分类→范式映射）+ LLM 归纳总结能力·**缺一不可**（CLAUDE.md 铁律6）
- **零 LLM 教训**：RAG 检索出文件必须 LLM 综合总结（非零 LLM 拼列表）·曾砍 LLM 支柱被用户验证否定
- **产品定位**：EMC+RAG = 本地化聚焦专业知识蒸馏（区别于网络搜索/其他 AI·本地化+聚焦+专业+可追溯）
- **结论颗粒度 = 数据来源维度**（城区⊃街区⊃社区⊃小区+零散住房+城中村·社区≠小区）



### ✅ CB-17 闭环（三组进度同步 + 下一步安排收敛）

- **背景**：用户 08-06~08-07 暂停回归 → 要求回顾 + 三组同步下一步。claude组 核实基线（git `cf5ef04` 同步·08-05 两专题 CB 全闭环·验证基线）→ 落 [讨论发起](docs/catch-ball/discuss/进度同步与下一步安排_讨论发起_2026-08-08.md)（7 债 + 5 焦点 + 附 A prompt·commit `ce850a3` 已 push）
- **两组回应已回收**（`docs/catch-ball/discuss/进度同步与下一步安排_回应_{Codex-GPT5|glm组}_2026-08-08.md`）：
  - **Codex**：快照事实核验全通过（代码 grep 逐项佐证）·补 B3 fail 集合快照判据（fail 集 == {PRM-03/04/07}·新增即阻断）+ 三路径观点卡浏览器抽验（B1 补丁只被 pytest 未被 B3 覆盖）·PRM-07 **partial（P2→P1·仅预检不实施·执行侧残余实测）**·补债 HOME/OFFICE 交接卡过期/flywheel 注释 25→26/回归判据缺 fail 快照/前端 JS 单测补课
  - **glm组**：pytest 独立跑 **291 passed + 5 skipped**（vs claude 声称 293·差异 2 待核实）·补回归范围 validate_outlet_fields/validate_skill_params/test_hotspot·**P3-4 地点联动优先于 P3-1**（出口闭环最后一块·微观落点粗略→精确）·PRM **agree 不排入**（03/04 center ask_user 正确·07 已根治）·补债 .outlet-metrics CSS 缺失
- **claude组 反评价（verify-before-accept · 关键争议核实）**：
  - pytest 实测 **291 passed + 5 skipped**（35.47s 全绿）→ **glm 的 291 正确**·「293」为旧口径（差异 2·非回归·发版回归对齐口径）
  - `.outlet-metrics` **已存在于 ai_qa.css**（Grep 证实·401371b ③z3b P2-1 已修）→ **glm 补债为过时信息·disagree**
  - **PRM-07 执行侧残余属实**（tools.js:617-622 白名单只对 `source==='preset' && /行政区/` 生效·FC 直供非 preset 边界绕过）→ **Codex 对·glm「已根治」仅覆盖数据侧**
  - flywheel_audit.py:7 注释 25 vs 26 属实
- **下一步安排定稿**（cb-journal CB-17 章节）：

```
P0（用户·当前）整体验收：todo「整体验收清单」浏览器肉眼验证 + 记 3 观感（观点卡干货感/热点五档可读性/setTerrain 地势感）
P1（发版门）发版就绪度回归：pytest 全量（291 passed + 5 skipped 基线）+ validate（含 outlet_fields/skill_params）+ link_checkup 20/20 + eval 复采（带 session）+ B3 三连（判据 = fail 集 == {PRM-03/04/07}）+ RST-L06 三连 + 三路径观点卡浏览器抽验 + flywheel 注释对齐（25→26）
P1（预检）PRM backlog CB 预检（仅预检不实施）：B3 取证确认 fail 集合 → PRM-03/04 stale-tool 修复覆盖核实（center ask_user 正确·非改代码）→ PRM-07 执行侧两候选收敛（白名单补齐 vs request_upload 强化）→ 回归通过后实施
P2（回归后）P3-4 地点联动（出口闭环·微观落点粗略→精确）：复用 geo_label·先盘点消费方·分开 commit 先验后推
P2（回归后）P3-1 依赖图（零红线）：DAG 纯函数·不交 LLM·与 P3-4 分开 commit
P3（文档）HOME/OFFICE 交接卡同步 + _cb-index 状态更新 + revision-log 归档
P3（后置）P3-2 并行（降挂起）· KDE/DBSCAN 替代（发版后专题·先定产品定义）· 时间轴 manifest · 前端 JS 单测补课
```

### ✅ 整体验收通过（CB-18 全闭环 · 用户新工作方式：验收交两组走 CB）

- **两组 CB 验收**（`整体验收_实施检查发起_2026-08-08.md`）：**有条件通过**（Codex 更严 + glm 通过）→ 修 W-1/W-2 + 补 S-1~4（commit `d5a5625`）→ **glm 复验通过**（`整体验收_修复验证回应_glm组_2026-08-08.md`·W-1 零残留/W-2 链闭合/S-1~4 充分·pytest 297 零回归）→ **push + 整体验收通过**
  - ✅ **W-1**：tools.js hotspot docstring/observation 红/绿文案 → 纯橙系五档（零逻辑·纯文案）
  - ✅ **W-2**：threshold/soft_threshold 转发补齐（hotspot-tool.js `_execute` body + tools.js hotspot 透传·默认 1.96/1.0 不破坏）
  - **W-3**：legend 五档口径 → 定「EMC 工具卡文本图例」（地图图例补 UI 后置）
  - ✅ **S-1**：`tests/test_export.py` 新建 4 例（BOM/列/脱敏/空卡）
  - ✅ **S-2**：`tests/test_spatial_analysis.py` +2（terrarium 解码 0~500/bounds/尺寸 + 极性过滤 ValueError）
  - ✅ **S-3**：`tests/browser/test_result_struct.py` 新建 + e2e-seam 暴露 buildResultStruct（观点/无观点/4 要点/结论带地点/scale 三档/无地名降级·P0-3 DOM 断言留回归期浏览器抽验）
  - ✅ **S-4**：`tests/test_outlet_schema.py` 补 geo_label micro + unknown→None
  - **验证**：pytest **297 passed + 5 skipped**（+6 新增·零回归）· S-3 e2e-seam PASS · ESM 语法 OK
  - **Codex 缺席标注**：glm 单组复验通过（用户指示「先只看 glm组」）·Codex 恢复后补验（W-2 全链 + S-3 边界 + DOM 断言前置评估）
  - 观感类（P0-1/P0-5/H-1/H-4·干货/地势感/无露底/console）标「可选用户复核」

### ✅ P1 发版回归绿 + P3-4 地点联动实施完成

- **发版就绪度回归（绿）**：pytest 301（done·claude）+ validate 34 + eval 81% PASS + 三路径观点卡 PASS + **glm 分担全回**——link_checkup **20/20** + B3 **Run1/2 均 23/26（88%）**（fail ⊆ {PRM-03/04/05/07} 已知 backlog·RST-L06 PASS·成果范式 6/6）+ Run3 API 慢时段（21 timeout·trace 排除）·**回归绿·可进发版候选**
  - **事实修正**：glm 报告「Run2=5/26」计数有误·实际 Run2=23/26（88%）·仅 Run3 API 慢
  - **PRM-05 补入 fail 集判据**：{PRM-03/04/05/07}（boundary derive 方差·CB-12 起持续·非并发引入）
- **P3-4 地点联动实施完成**（commit `9680dcc`·未 push·先验后推）：
  - P3-4-1 zonal/rank prop_cols 放行 place_name/place_name_source/poi_names/poi_count（Gap B 核心杠杆）
  - P3-4-2 buildZonalFc 焊地点字段透传
  - P3-4-3 出口卡动态 limitations（按 source 诚实标注）+ micro 需求位置 POI 升级
  - P3-4-4 _fmtRow place_name 优先
  - 验证：pytest 301 + test_outlet_micro/test_outlet_macro e2e-seam PASS
  - **待两组复验**（`P3-4地点联动_复验发起_2026-08-08.md`）→ push → 发版候选

### ✅ CB-19 发版回归全面测试完成 · 发版候选通过

- **三组协同**（`发版回归全面测试_方案_2026-08-08.md`）·**fail 集判据 {PRM-03/04} 达成**：
  - **claude 组**：pytest **303 passed + 5 skipped** + validate 34 + ESM 6/6 + **B3 24/26（92%·历史最佳）**·fail={PRM-07 空对象 LLM 方差·单要素拒识已生效, RST-L06 Flash 方差}·PRM-03/04/05 全转 PASS
  - **glm 组**：条件绿（pytest 303 + CB-18 数据 + 修复代码审查·环境端口冲突未新跑）
  - **Codex**：T6 PRM 专项 PASS + T8 出口卡 e2e PASS + **T7 多步链 FAIL【阻断】**（469bf32 黑名单误伤「龙泉」·层首要素）→ **claude 修复**（5115d7c·只拦单要素·T7 复测 PASS·pytest 303）→ **阻断解除**
- **基建修复 4 commit**（三组并发必需）：端口隔离 3dc0a1c + 后台 PATH fdc1c1d + serve 断连 76b16eb + PRM-07 文案 2f9965f
- **发版候选判定：通过**（T7 阻断已修·fail 集判据达成·剩余 fail 均已知/方差）

### ✅ CB-19c 5115d7c 黑名单修复复验通过（两组确认）

- **Codex + glm 均通过**：T7 多步链阻断解除（执行成功）+ 小溪塔单要素仍拒识 + 前后端一致 + pytest 303 零回归·漏拦风险低（三重保险）
- **采纳 Codex P2 建议入 backlog**：P2-1 多要素全黑名单增强 · **P2-2 boundaryLabel 取 features[0].properties.name（治 `[object Object]`·治 PRM-07 偶发 fail 方差源·高价值）** · P2-3 verify_prm57 断言加严
- **CB-19 全部闭环**：整体验收 → 修复 → 深读 → 发版回归全面测试 → 黑名单复验 → **发版候选通过（两组确认）**

### ✅ 收尾完成（P2-2 + P2-3 + 文档债）

- **P2-2 boundaryLabel 取 features[0].properties.name**（`12aa1f9`·治 `[object Object]`·LLM 转述不可读·zonal/rank/area_stats/compare 4 处）
- **P3 文档债**（`76cfd2d`）：HOME/OFFICE 交接卡同步到 08-08 + cb-index 到 CB-19c
- **P3-1 依赖图评估**：无独立消费者（并行未实施）→ 随 P3-2 一起·不单独推进
- **P2-3 verify_prm57 断言加严**（`a331568`·去宽泛「上传」·加「法定功能区/标准边界」·诚实暴露 PRM-07 空对象真实残余）

### ✅ CB-20 PRM-07 空对象根治完成（两组预检通过·实施 bdde1f0）

- **方案 A 主 + B 兜底**（`bdde1f0`·已推）：A harness derive 失败+boundary 可疑 → `strategy='request_upload'`（复用既有短路·LLM 无法弱化·不依赖 `_regions`·法定功能区无后缀）+ B zonal handler 空对象 → 「需上传标准边界资料」
- **验证**：pytest 303 零回归 · verify_prm07_ab（e2e-seam 可控）：`zonal_stats({})` → 需上传 ✅ 生效（替代「无数据」）
- **工程边界诚实收敛**：浏览器实测 PRM-07 仍受 **LLM 传参方差**影响（空对象/单要素字段名不标准/层未加载）·方案 A/B 覆盖可控场景·完全消除 LLM 行为方差不可能·合理边界
- **新 learning**：`_regions` 正则只匹配区/市/县后缀·法定功能区名提取不到；LLM 字段名不标准时黑名单取不到名

### 🔄 下一步（后置项 · 明日公司电脑续）

- [ ] `git pull`（拉取今日全部 push @ `903632e`）+ 读 OFFICE/HOME 交接卡
- [ ] **PRM-07 残余**：LLM 单要素字段名不标准（无 name/MC/NAME）→ 黑名单扩字段名覆盖（P2 级）
- [ ] **P2-1 多要素全黑名单增强** · RST-L06 Flash 方差 · KDE/DBSCAN 替代 Gi* · 时间轴 manifest
- [ ] **P3-2 并行 + P3-1 依赖图**（`$n` 索引重构前置·规模后启动）

> 📦 08-08 收工：CB-17~CB-20 全闭环 · 发版候选通过 · 交接卡 OFFICE.md 已更新 · 全部已 push @ `903632e`

---

## 📅 2026-08-05（情绪热点图重做专题 + 发版就绪度回归待续）

### 🔄 情绪热点图重做 ·「热力 vs 热点」专题（今日任务）

- **现状（代码实查）**：三轨语义错位——情绪地形（KDE 热力面 `/spatial/terrain`·create_terrain_mesh）+ 情绪热点（逐点 Gi\* `/geo/hotspot`·KNN k=8）+ 热力图（heatmap-tool 委托 terrain 同款）。用户诉求"舆情热度·高程/地势感" = KDE 热力面（业界正名）；现「情绪热点(Gi\*)」是显著性检验，且逐点输入噪声大 + hot/cold→极性色是自造语义。
- **第一轮已完成**：概念基座 + 业界做法核实 → 专题文档 `情绪热点图_热力vs热点_专题讨论_2026-08-05.md`（4 焦点 + 附 A 发组 prompt）
- **第一轮两组回应已回收**：glm组（partial 定位/KNN 尺度漂移修正/invert 链成立/命名表）+ Codex（grid_pois 修正/5 个"热点"语义/dormant deck.gl/spatial_hotspot 字段/无测试护栏/多维归因占位）——两组合点 = KDE 主图 + Gi\* 网格化 + 视觉去极性色 + 命名定标先行
- **用户新增焦点**：热点图（Gi\*）= 2D 即可；热力图 2D+3D vs 2D 需讨论（含 3D 形式）；当前 3D 地形效果差（非连续曲面·无地势感）
- **已完成**：3D 效果差根因（contourpy 等值线环 7 层 → fill-extrusion 逐环固定高度 = 梯田/千层饼非曲面）+ 业界正解调研（MapLibre setTerrain+raster-dem 三角网地形 / deck.gl TerrainLayer / fill-extrusion 改造）→ **第二轮文档** `情绪热点图_第二轮_claude组反评价与3D焦点_2026-08-05.md`（反评价 + 焦点 5 + 附 B 第二轮 prompt）
- **第二轮两组回应已回收**（`情绪热点图_第二轮回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**3D 形式两组全选 a（MapLibre setTerrain+RGB DEM）**——弃 b（deck.gl 本仓踩坑前科）与 c（fill-extrusion=伪曲面）；glm 深化 = setTerrain **全局 draping 风险需 PoC 隔离**（不常驻+互斥+exaggeration+sky）+ A/B 验证升格 P1 前置 + P0 3D 入口与 P1 合并；Codex = 500m 默认+降档护栏+统一三处粒度 + sky/compare/DEM 测试补 6 项
- **已完成**：**定稿执行计划** `情绪热点图_定稿执行计划_2026-08-05.md`（D1-D7 决策 + P0/P1/P1.5/P2 范围 + 闸门 + 待拍板 4 点）——**待用户拍板**
- **待续**：用户拍板（P-1 3D=a 确认 · P-2 2D/3D 共源 · P-3 今天执行范围 · P-4 3D 入口时机）→ 执行（P0 命名定标 + Gi\* A/B 前置 → P1 网格化 → P1.5 setTerrain）

### 🔄 后续任务规划 · 出口三段式 + 工具管线（热点图完成后排期 · 本次纯讨论零代码）

- **用户意图**：① 分析结论「出口」重整理成**新三段式**（替换旧三段式）——第一段=明确观点（基于用户提问·LLM 核心价值）；第二段=4 要点（分析方法/使用数据/分析结果/**分析结论**——观点≠结论：观点=转化解答提问·结论=图数表描述性论述）；第三段=行业接口对标对表→一键入库参数（城市体检/更新·更新需求调研场景·参考国内指标案例）② 工具管线优化（调用/协作线性并行/地点联动）③ 所有工具出口联动地点信息（宏观面域/中微观用地地点·三段式插入环节由成果范式 agent 思考）——目标=出口**既稳定又灵活**
- **已完成**：现状基线实查（四态出口契约·finalStep 极瘦 D019·outlet_kb 7 契约 21 指标映射确定性组装·CB-15 地点联动）→ **讨论发起文档** `情绪地图_出口三段式与工具管线_讨论发起_2026-08-05.md`（5 焦点 F1 映射/F2 观点vs结论/F3 接口参数/F4 地点尺度/F5 管线优先级 + 附 A 发组 prompt）
- **第一轮两组回应已回收**（`情绪地图_出口三段式与工具管线回应_{glm组|Codex-GPT5}_2026-08-05.md`）：两组共识 = A+C 先行 B 后置·落地=前端呈现层+后端确定性聚合·观点段素材现成（提问在 finalStep messages）·地点插入三处力度不同·第三段缺口=业务细化；分歧 = 观点段落点（glm 软扩 vs Codex 零改动+ctx 注入）
- **用户拍板**：Q1 第三段=条件段（意图 agent 判断·未涉归因不入库）· Q2 结论段=确定性为主+LLM 润色可选 · Q3 A+C 先行 B 后置 · **Q4 反馈"观点先行=核心价值（干货）"** → claude组 修正 = **采纳 glm 软扩**（观点段 FINAL_TEMPLATE 正式指令·LLM 必读·先扩 eval 门禁再动）·否 Codex 零改动（ctx 附加提示遵守度弱=价值打折）
- **已完成**：定稿计划（D1-D5 + P0/P1/P2/P3 范围 + 验证）→ **定稿评估发起文档** `情绪地图_出口三段式_定稿评估发起_2026-08-05.md`（定稿计划全文 + 6 焦点 + 附 A 评估 prompt）
- **两组定稿评估已回收**（`情绪地图_出口三段式_定稿评估回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**"有条件执行"**——Codex 阻断 R1（行为 eval 扩）/R2（观点提取兜底契约）+ 警告 W1（基线 2641B 过时）+ W4（条件段不交 LLM）；glm 阻断 B1（风格定调）/B2（结论段独立聚合·不解析 markdown）+ W1（双保险）/W2（结果结构化改动量被低估）
- **用户拍板"定稿执行"→ P0 已实施**：行为 eval 扩（test_final_prompt_has_insight_first 三锚点）+ 体积门禁 <3000B/≤2980B（**实测基线 2833B·非 2641B·观点指令 124B→2957B**）+ FINAL_TEMPLATE 观点先行软扩 + harness ctx 双保险 + onResultStruct hook + 新 result-struct.js（结论段独立聚合·观点三档兜底）+ panel 观点卡/4 要点卡 + CSS · **pytest 283 passed 零回归**（+1 新断言）
- **已完成**：**P0 实施审计发起** `情绪地图_出口三段式P0_实施审计发起_2026-08-05.md`（改动清单 + 6 审计焦点 + 附 A 审计 prompt）
- **两组 P0 审计已回收**（`情绪地图_出口三段式P0_实施审计回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**P0 通过 + 阻断项 B1 + 警告 W1-W3 + 建议项** → **claude组 已全部修复**——B1（runChainPath/runAllToolCalls 补 onResultStruct·抽 _dispatchResultStruct 共享 helper）+ W1（结论段改从 rows 聚合·学术句式·Top 数值+地名+归因）+ W2（体积预算放宽·仅 <3000B·模板冻结加字）+ W3（首段首句兜底删·无标记不显卡）+ 建议项（整块捕获/_pendingStruct send 重置/三锚点位置断言）·**pytest 283 passed + test_emc_template 24 passed + 括号全平衡**
- **用户定**：P0 暂不验（记录·完成后一起验证）→ **推进 P1/P2**
- **已完成**：P1/P2 执行计划 → **P1/P2 计划评估发起** `情绪地图_出口三段式P1P2_计划评估发起_2026-08-05.md`（6 焦点）
- **两组 P1/P2 计划评估已回收**（`情绪地图_出口三段式P1P2_计划评估回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**可执行 + 修正**——glm 阻断 B1（**polarity_index 值域双轨** L1 -1~1/L2 -2~2·分级须归一化）+ W1（"低"档含积极语义）+ W2（覆盖度归一定义）+ W3（CSV 前端入口）；Codex 修正（四档高/中/低/无显著需求·p95 归一+缺省不参与+主题 0/0.5/1·CSV 显式脱敏+outlet_id/name/scale 列·宁夏 5 张映射+8 张边界·limitations 卡级声明·前端导出按钮）
- **✅ P1/P2 已执行完成**（按评估修正）：
  - **P1-1** `grade_demand_intensity(pi, level)`——L2 值域归一（-2~2→-1~1·glm B1）+ 四档（< -0.5 高 / ≤-0.15 中 / ≤0.15 低 / >0.15 无显著需求·Codex W1）·边界 < 修正
  - **P1-2** `priority_score(row)`——p95 归一（Codex W2·防离群格）+ 缺省不参与加权（防缺失反超实值）+ 主题契合 0/0.5/1 + `PRIORITY_WEIGHTS` 常量（启发式初值标注）
  - **P1-3** case_library 四案例 `measure_note`（感知维度非官方评分）+ 出口卡 limitations 卡级声明（"行业案例为对标参照·非评分基准"·双层）
  - **P1-4** `export_outlet_card_csv`（显式脱敏+outlet_id/name/scale 列+BOM）+ **前端导出按钮**（panel.js·glm W3 防空转）+ CSS
  - **P2** 出口卡 `geo_label`（宏观·面域/中观·单元/微观·落点·glm S4）
  - **验证**：pytest **290 passed**（+7 零回归）· validate_outlet_fields 2 passed · CSV 真跑（BOM/列✓）
- **待验收（用户定·完成后一起验证）**：见「整体验收清单」节
- **已完成**：todo 验收清单 + revision-log §5 归档（P0/P1/P2）
- **已完成**：**P3 工具管线计划** `情绪地图_工具管线P3_计划评估发起_2026-08-05.md`（P3-1 依赖图 DAG 判定纯函数·不交 LLM / P3-2 并行执行 Promise.all 同层·PARALLEL_ENABLED 开关 / P3-3 编排器稳定性红线 SOP·先扩 eval 一次一处 / P3-4 地点联动工具出口统一 place_name·5 焦点 + 附 A prompt）
- **两组 P3 计划评估已回收**（`情绪地图_工具管线P3_计划评估回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**两组高度共识 = P3-2 并行执行后置/砍掉**——🔴 `$n` 引用机制依赖严格顺序（tools.js _stepResults 按产出序 push·并行破坏索引确定性·Codex B1 + glm B1 一致）+ 并行收益不足（multi 触发场景多有 $n 依赖·真正可并行极少·Codex B2/glm B2）+ 成本严重低估（3 天→Codex 4-5/glm 5-9 天）；**P3-1 依赖图 + P3-4 地点联动保留**（零红线·可做）；**排期后置到热点图专题之后**（两组一致·避免 harness 撞车）
- **claude组 反评价收敛**：采纳两组共识——**P3 整体后置**到热点图专题完成后（P3-1 依赖图 + P3-4 地点联动保留·P3-2 并行暂不做·待 EMC 规模化）；P3-2 若未来做须先解 `$n` 索引重构（index-based）+ 共享状态隔离（_lastToolRows 确定性选取）·PARALLEL_ENABLED 默认关
- **待续**：回到主线 = **热点图重做专题**
- **用户拍板（P-1~P-4 全按建议）**：P-1 3D=a setTerrain / P-2 2D/3D 不统一 / P-3 B（P0 命名+A/B 前置）/ P-4 随 P1.5 合并开·**强调工具间解耦不互相干扰**
- **✅ P0 命名定标完成**（8 处）：hotspot-tool 图层名「显著聚集点(Gi*)」· grid-tool 占位卡/组卡「显著聚集(Gi*)」· panel.js spatial_hotspot→「代表地点」+ Overview 文案 · test-cases.js 语料 · index.html 注释 · spec.md 字段/调试描述
- **✅ P0-前置 Gi\* A/B 验证完成（重大发现）**：真实 L2 数据（xiling_wujia·2500 点）**逐点/500m 网格/200m 网格 Gi\* 全部无显著热点（全 ns）**——Gi_Z 全在 ±1.07~1.26。**实测根因**：score std 仅 0.377（方差小）+ KNN 邻居 50m~2.5km（尺度漂移·glm 第一轮 B2 证实）+ 阈值 1.96 严。**网格化平滑 Z 但未变全 ns → 输入粒度修正（原 P1 核心）不足以让 Gi\* 出热点**（"效果不对"实锤）
- **两组 P1 修正评估已回收**（`情绪热点图_P1修正回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**根因加深 = score 是 U 形多峰离散分布（5 级极性分类副产物·glm 主因）·与 Gi\* 连续正态假设不匹配**（Codex：局部邻域偏差小=弱信号·降阈值必失败 max\|Z\|1.26<1.65）；**方案收敛 = A 软分级主推（五档·诚实标倾向聚集）·弃 B（逐点无 polarity_index 原生列）·距离带 P2·长期评估 KDE/DBSCAN 替代 Gi\***
- **✅ 热点图 P0/P1/P1.5 已全部实施完成**（工具间解耦）：
  - **P0 命名定标**（8 处）：Gi\*→「显著聚集点(Gi\*)」· spatial_hotspot→「代表地点」·「热力图」统一
  - **P0 前置 A/B**：全 ns 实锤（U 形离散分布·glm 主因）→ 驱动 P1 修正
  - **P1 软分级**：`_classify_hotspot` 五档（hot/tend_hot/ns/tend_cold/cold·threshold 参数化）+ `hotspot_tier` 字段 + 前端 `colorMode='hotspot'` 显著性符号层（弃 `_CLS_POL` 极性色·单色系+大小分档·与 KDE 解耦）
  - **P1.5 setTerrain 3D**：`create_terrain_dem`（F_009·KDE→terrarium RGB·bounds 转 WGS84）+ `/spatial/dem` 端点（header 返 bounds/size）+ `runDem` + map.js `setTerrainDEM`（**draping 隔离**：不常驻+与 3D 网格柱互斥+sky 层）+ `generateTerrain3DForAI`/`closeTerrain3D` + retired.md 渲染路径退役登记（fill-extrusion 3D → setTerrain 连续曲面·2D 等值线保留）
  - **验证**：pytest **293 passed**（+3 零回归）· DEM 解码验证（高度 0~500·峰 500m·bounds WGS84 正确）· 括号全平衡
- **待整体验收**（todo「整体验收清单」·用户定完成后一起验证）· **热点图执行进 CB 审计**（两组·下一步）
- **两组热点图实施审计已回收**（`情绪热点图_实施审计回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**P0+P1 可验收**（命名定标 8 处 + 软分级五档参数化·默认 soft=1.0 解全 ns 显示）· **P1.5 有 B1 阻断**（setTerrain 无用户入口 + EMC 委托未切·与 retired.md 矛盾）
- **✅ 审计修复全部完成**：**B1**（tools.js EMC 委托切 generateTerrain3DForAI·setTerrain 连续曲面）· **W1**（map.js 符号层改纯橙系·弃红蓝双色·与 KDE 解耦）· **W2+W3**（/geo/hotspot 透传 threshold/soft_threshold + legend 五档显著 95%/倾向 84%）· **W6**（tool_contracts/paradigm/stages SKILL_DEFS/validate SKILL_DEFS_DEFAULTS/_KNOWN_SLOTS 契约层五档同步）· **建议级**（index.html:14/1172·state.js:107 注释清理·map.js 注释澄清）
- **验证**：pytest **293 passed** + validate_skill_params/test_emc_template **28 passed** + 括号全平衡
- **待整体验收**（todo「整体验收清单」·出口三段式 P0-P2 + 热点图 P0/P1/P1.5 一起·用户浏览器验收）

---

## 📋 整体验收清单（出口三段式 · 用户定"完成后一起验证"）

> 启动方式：`py frontend/serve.py 8080` 打开 → 浏览器肉眼验收（默认链路·无需 Playwright 除非异步/控制流）。

### P0 验收（观点先行 + 三段式骨架）
- [ ] **观点卡置顶**：问 EMC 一个情绪分析问（如"西陵区哪些区域情绪最差？"）→ 回答顶部出现"观点"强调卡（干货·答"所以呢"）·正文无重复观点行
- [ ] **4 要点卡底部**：回答底部出现"分析支撑（4 要点）"卡——方法/数据/结果/结论四栏（结论含"数据显示 X 区极性指数…"学术句式）
- [ ] **三路径都出卡**：单技能问（默认）+ 多步链问（"裁剪出西陵区情绪点再叠置"·runChainPath）+ 多工具问（multi·runAllToolCalls）——观点卡/4 要点卡都应出现（B1 补丁验证）
- [ ] **无观点不显卡**：若 LLM 未写 `> **观点：**` 标记 → 无观点卡（保守·不取动作描述当观点·W3）
- [ ] **无 console 错**：浏览器 F12 无 JS 报错（Codex W4 浏览器最小验收）

### P1 验收（第三段指标细化 + CSV 入库）
- [ ] **需求强度等级**：出口卡出现"需求强度等级"（高/中/低/无显著需求·四档）——问"西陵区更新需求分析"·若极性偏负应显示"高/中"
- [ ] **复合优先级**：问"更新时序排序"→ 出口卡"优先级排序"为 Top1 区域 + 复合规则（非单一极性降序）
- [ ] **CSV 导出按钮**：出口卡上"导出 CSV"按钮 → 点击下载 CSV（Excel 可开·UTF-8 BOM·含 outlet_id/name/scale 列·脱敏无敏感字段）
- [ ] **案例口径标注**：出口卡 limitations 含"行业案例为对标参照·非评分基准"
- [ ] **地点 scale 标注**：出口卡出现"宏观·面域/中观·单元/微观·落点"（geo_label·随问句尺度）

### P2 验收（地点联动）
- [ ] **结论段带地点**：4 要点卡结论含地点（宏观=面域名/中观=单元名/微观=POI·按尺度）

### 热点图重做验收（另一专题·P-1~P-4 待拍板）
- [ ] 3D 地形 = MapLibre setTerrain 连续曲面（非 fill-extrusion 千层饼）· Gi\* 网格化 · 命名定标（D1-D7·待拍板后）

---

## 📅 2026-08-05（续作 · 发版就绪度回归 + backlog 清理·e2e-seam 解封）

> 公司环境续作（交接卡 7aaa1e4）。用户拍板顺序：**先修 backlog → 修完进 CB 审计回归**。

### ✅ 先修（backlog 已知项全闭环）

- **陈旧注释同步**（Codex ③w7 P2·直接改）：district-stats.js 头部「8 组团」→「4 组团」（含 ③w6b 说明）+ panel.js×7（注释 + **UI 文案「中心城区内 · 4 组团」**）+ panel.css×2
- **MOD_PLACE 渲染风暴·根因修正 + 修**：trace 取证 1595/1602 次 F_002 外层=forward（search_place 链路）·**非地图渲染风暴**（Codex 假设修正）——是 EMC/测试高频地理查询重复全量扫 4310 POI。**修**：forward/reverse 加结果缓存（存副本返副本防污染·超上限清空·纯性能·行为不变）+ test_geocode.py 新增 2 守卫（防污染/一致性）
- **MOD_LLM.F_002 重核**：2476 次调用 attempt≥1 仅 349（14%）·86% 首次成功——**确认调用数非 fallback 数**（Codex 修正成立）·无 while-loop 风暴
- **FC boundary 残余评估**：白名单已落地（tools.js:617-630 deriveAvailable preset 过滤）·未命中走后端诚实报错（PRM-07 弃 fallback）·用户上传层设计不受限——**保持现状·不进修改**
- **e2e-seam 解封（重要发现·阻断所有 browser 测试）**：harness.js `composeGapCard` 漏 `export`（③w4b c53aa99 起）→ e2e-seam import 链崩 → `__emcTest` 永不注入 → link_checkup/gap_wording/flywheel 全超时。**加 export 修复**（纯暴露）·08-04「20/20」是修复前记录·本次真实验证

### ✅ CB 审计回归（发版就绪度）

- pytest **282 passed**（+2 缓存守卫·零回归）
- link_checkup **20/20 PASS**（R9 单测 + fixture 注入 4 行政区 + C2 采样信号 OK·耗时软门槛超时不判失败）
- 措辞断言 **test_gap_wording.py 3 场景 PASS**（③w5 措辞修复前台验证）
- **eval 复采 ×4**：76/73/78/84%——MISS 主因 = **Flash 间歇空流**（API 层 len=0·实测同问重测正常）·加**空流重试 1 次**治测量污染（73-78%→**84% PASS**·与 08-04 持平）·剩余 MISS=2 空流 + 4 已知歧义（rank→zonal/overlay→clip/hotspot→density）·FC 参数 3/3=100%
- **B3 快照重跑 ×3**（`EMOTION_TRACE_SESSION=B3-snapshot-0805` + B3-RSTL06-2/3）·**84.6% / 88.5% / 88.5%**（22/23/23 pass·~10-12min）·fail 全在「参数正确性」PRM（已知 backlog：PRM-03/04 buffer radius 解析·PRM-07 法定功能区白名单执行侧缺口=Codex ③w7「FC boundary 残余」P2）·PRM-01 cell 已修复（500m OK）·**成果范式/Smart/CPD/UI 全 OK**（并发改动影响·需重验）
- **RST-L06 三连 PASS**（tools=clip,density·1→2 层·③w4/③w6b 修复实证）·**用户提示并发任务改成果范式/agent 出口 → RST-L06 结果标注并发改动后需重验**

### 待续（本次未收）

- 时间轴专题（manifest 404·用户定后置）
- **并发任务**（成果范式/agent 出口改动·用户提示）·完成后相关测试（RST-L06/B3 成果范式类）需重验
- PRM backlog（buffer radius·法定功能区白名单执行侧·Codex ③w7「FC boundary 残余」）待 CB 讨论（承重走预检）

---

## 📅 2026-08-04（CB-16 全链路闭环 + 发版准备：Wave 0-3 + ③z 余留 + ③w2~③w7 全局优化/措辞修复/发版收尾）

### ✅ ③w4~③w7 措辞修复 + 发版 backlog 收尾 · 全闭环（两组通过·已推 0bb55df）

- **③w4/③w5 措辞修复 + 发版遗留**（已闭环·78db0e3 + 2130a49）：用户实测「EMC 无法回答时结论'无法生成图层'·但问题可能跟图层无关」→ gap 措辞 failedObs 判据（零工具尝试「无法直接回答/无法理解」·试过工具「未生成图层」）+ eval 标尺纠错（select_template 单工具·76%→84% GO·tuple 双接受）+ RST-L06 preset fallback + buffer stale-tool 门控 + e2e-seam 措辞断言
- **③w6/③w7 发版 backlog 收尾**（已闭环·23efe74 + 0bb55df）：footer 条件化（failedObs>0 才「未生成图层」）+ **preset 行政区清 4 要素**（FIXED_ADMIN_DISTRICTS·备份 .bak9·用户拍板·PRM-07 根治）+ **district-stats 8→4 组团** + RST-L06 fallback 补 MC（Codex P1 死代码）+ eval 注释 + **fixture 静态守卫**（防回潮）
- **验证**：pytest 278 passed 零回归·ESM-OK·eval 84% GO·link_checkup 20/20 PASS·B3 快照 84.6%（方差区间）
- **已推**（0bb55df·先验后推解锁·远端 0/0 同步）
- **待续**：发版就绪度回归（B3 重跑 + eval 复采 + RST-L06 复跑·前台 serve）·时间轴专题（manifest 404 同源派生方案）·backlog（陈旧注释·FC boundary·MOD_PLACE·MOD_LLM.F_002）

### ✅ ③w2/③w3 全局优化 + 发版快照 · 全闭环（两组通过·已推 ff7b125）

- **全局优化**：CLAUDE.md 当前开发状态 5 行（L3✅·L4🔄·空间✅·UI✅·L0→L1 sim）+ todo 周归档（07-27~08-02）+ decisions ADR-017~019 + 记忆 GC
- **backlog 收尾**：validate_skill_params drift 修复（paradigm `_sync_geo_catalog_guard_fields`·1 FAIL→4 passed）+ renewal 卡 perceptible_metrics domain 门控
- **发版快照**：B3 26 例 pass=22（84.6%·Codex 方差区间）·link_checkup 20/20 PASS·tracklog F_002=25 调用·eval 76% NO-GO（③w5 修·标尺错）·RST-L06 回归（③w4 修·clip range derive）
- **已推**（ff7b125·远端同步）

### ✅ Wave 3 + ③z 余留 2b/P2 · 全闭环（两组检查通过·已推）

- **范围**：出口深化最后一块（多卡 + validate_outlet_fields CI + 可感知计算器 2a + **③z 余留 2b + P2**）
- **多卡落地**：resolve_outlet_ids（跨 domain 多卡·同 domain 最高分）+ build_outlet_schema 返 cards + build_outlet_schema_single 兼容 + /outlet_card 返 {cards, card} + 前端多卡渲染
- **validate_outlet_fields CI 落地**：tests/validate_outlet_fields.py（正则提取消费字段→死字段 fail/缺消费 warn）
- **③z 2b 落地**（两组预检 P1×3 全采纳）：`_parse_emc_expr`（拆 `+`·**多值 `/` 拆列表**·含 polarity→2a）+ compute_perceptible_metrics 2a/2b（**生态宜居明示留 2a**·2b 仅可感知·条件不匹配→跳过·**关键词未命中→跳过**·source 对齐）+ `_kw_hit` 共用
- **③z P2 落地**：checkup_satisfaction prose→真实字段（满意度 polarity_index·8 领域 element_top/domain_top **element_top 优先**·不满意项不动）
- **panel.js 渲染 perceptible_metrics**（可感知指标小节·Codex P2 并入）+ .outlet-metrics CSS（③z3b P2-1）
- **③z3b 检查两组通过**（无 P0/P1）·采纳 P2-1/3（CSS + 边界测试·+2）·P2-2（`==`）不采纳
- **验证**：pytest 276 passed（+9）零回归·真端点（cards 2 张 + B 类条件命中出值·source 标条件+命中）
- **已推**（0a0d103·先验后推解锁·远端 0/0 同步）
- **后续**：backlog（7 工具 drift·MOD_PLACE 渲染风暴·MOD_LLM.F_002·CPD-L01/L02·时间轴 manifest·renewal 卡 domain 门控）

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
- **浏览器 EMC 真实问答肉眼验证**（问"大南门·二马路片区更新需求分析"→ 应出诊断卡 + 分析执行 + 出口需求分析卡·LLM 选层/路由走真实链路 + **perceptible_metrics 可感知指标小节**）
- **时间轴 manifest（_time_manifest.json）**（用户定·与需求分析是两件事·后置）
- **backlog**：validate_skill_params 7 工具 drift（paradigm when 同步）· MOD_PLACE 渲染风暴 + MOD_LLM.F_002 fallback 重核 + CPD-L01/L02 + 时间轴 manifest 404 · renewal 卡 perceptible_metrics domain 门控（③z3 已知）

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

