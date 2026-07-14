# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月14日（5.94 EMC 工作机制重构收工）| 分支 `main`（**本地领先 origin ≥1 commit 待用户手动 push**）| 本次会话 = 5.89-5.94 六 commit（EMC 图面本地化 + 止血降温 + 技能化编排 + 工作机制矫正）

---

## 当前节点：EMC 工作机制重构三阶段全部完成（站在巨人肩膀上落地），下会话先运行时验证

### 背景（用户两条核心反馈 → 三阶段重构）
1. **"半成品/不知所云" + EMC 自造 GIS 不套主 Toolbox**：三 Explore agent 实测证实——EMC 20 工具仅 `ensure_zone` 调主 Toolbox，density/hotspot/buffer 等全走自造 `/api/v1/geo/*` + 自造 `addResultLayer`；EMC density（kde_raster+DENSITY_RAMP）≠ Toolbox heatmap（rainbow）/grid（terrain-9）；7 工具硬默认 `layer:'yichang_l2_t1'`（registry 缓存，只传 L1·T1 照跑 L2）；run_python 仅 prompt 软约束；无上传胶囊。
2. **"步骤>3-4步跑偏/抽奖"**：诊断=自由 ReAct agent loop 的 p^N 概率链（temp×22工具×N轮）。
用户定位铁律：**EMC 本质=参数化设计**——tool=成熟gis+本地化、param=LLM识别+标准化字段+本地化、design=标准分析图层+本地化token。本次彻底落地。

### ✅ 本会话已做（6 commit，每 commit 同步 revision-log + todo）
- **5.89 / `b028b95` Track 0 图面本地化**：density 图例（sidebar 加 density 分支）+ value_col 默认 'score'（带情绪语义）+ 五极色归一 tokens（L2_* #86E61C→#78DC32 套对齐 tokens.css/emotionColors，修"图例色≠点色"真 bug）+ DENSITY_RAMP→gradient.neg + brand-visual.md 同步 + density 3D mode + 去噪 + 粗化透明（kde_raster 回传 actual_cell_m）。
- **5.90 / `b8de781` Track 1 数据兜底+纪律**：L1 极性静默全0兜底（aggregate_by_polygons 探测小写3级→3级路径，空值剔分母）+ score 自适应 + query-first 代码门控（round0 注入 query_layers observation 到 toolHistory，零 LLM）。
- **5.91 / `5e39dfb` Track 2 P1 技能化编排**：TEMPLATE_REGISTRY 9 技能（concept/density/rank/buffer/clip/overlay/zonal/multi/unknown，拟人化+可生长）+ diagnose method→template/params + stages.js SKILL_DEFS镜像+validateParams+_PARAM_ALIAS 25项+normalizeCard + harness runTemplatePath（single 路径 0-agentStep，p^N→p²）+ buffer 聚合闭环（BufferRequest 继承_GeoBase+焊圈内4×5归因）+ Flash 80% gate（test_emc_template.py 结构测 + eval_template_flash.py 手动评测）。**两真 bug 修**：normalizeParams 加 export + parseDiagnoseCard 收 template 卡。
- **5.92 / `75f3551` 机制 Commit A 数据纪律+收口**：pickVisiblePointLayer（只扫 visible 层）+ 6 点层工具默认 layer 从 registry 'yichang_l2_t1' 改 visible fc + 无可见守卫 + buildContext 移除 formatGeoCatalog（registry 全量泄漏源）+ addResultLayer 注入 _ui.tool（EMC 产物获 Toolbox 编辑面板身份）+ run_python gate（ctx.allowCodeViz 才放行）+ composeGapCard 缺工具分支。
- **5.93 / `9952bce` 机制 Commit B density 委托 Toolbox**：generateHeatmapForAI（heatmap-tool.js 新增 2D 彩虹程序化入口，仿 generateGridForAI）+ TOOLS.density 重写委托（2D→heatmap/3D→grid，弃用自造 /api/v1/geo/density+DENSITY_RAMP）+ TEMPLATE_REGISTRY/SKILL_DEFS density 同步 Toolbox 入参。
- **5.94 / `8deab94` 机制 Phase 2**（用户指定跳过 upload 胶囊）：generateTerrainForAI（3D KDE 等值面，**Toolbox 可视化三件套程序化入口齐备**：heatmap2D/grid3D/terrain3D）+ density 三模式路由（mode='terrain'）+ _registerToolboxLayer（补 _registry/_stepRecords provenance，修委托 Toolbox 的对账缺口）+ DENSITY_RAMP 死码退场 + /api/v1/geo/density 后端标 DEPRECATED（F_005 承重保留）。

### 🔍 验证（已过）
- **静态全过**：`.mjs` ESM（heatmap-tool/grid-tool/ai_qa 全量）+ py_compile（paradigm/prompts/geo_routes/spatial_analysis）。
- **pytest 166 过 / 6 失败全预存无关**（h3 未装致 hex grid ImportError + emotion_analysis/geocode/range_selector 未碰模块）。test_emc_template 5/5。
- **node 内联测**：parse+validate 管线 6/6（buffer 补默认/缺槽检测/density 默认/bogus→unknown/别名归一/single 路由）。
- **buffer 聚合 TestClient**：no-layer 逐字节同原，with-layer 焊 point_count=396/polarity=-0.596/全4×5归因。
- **L1 兜底直测**：aggregate_by_polygons L1 风格 polarity_index=0.083（改前 0），L2 5级回归 0.24 不变。
- **运行时待用户开 serve 肉眼验**（非阻塞，最优先）：density 三模式 / 只传L1·T1不跑L2 / buffer编辑面板 / 缺工具卡 / 图例3D色板一致。

### 待 push（用户手动）
`git log origin/main..HEAD` 看未推数。git 报告 origin 落后到 `9952bce`（Commit B），**Phase 2 `8deab94` 确定 unpushed**；前 5 个（5.89-5.93）状态以你本地为准。push 前先确认。

### ⬜ 下一步任务（全面计划，按优先级）
1. **运行时验证（最优先）**：开 `serve`（`start.bat` 或 `py frontend/serve.py 8080`）验各 track。重点：① density 三模式——问"分布热度"，试 `mode:'2d'`(彩虹heatmap)/`'3d'`(grid)/`'terrain'`(等值面)；② 数据纪律——只加载 L1·T1，问热度，确认**绝不跑 L2**；③ buffer 产物能否用 Toolbox 编辑面板（_ui.tool='buffer'）；④ 问需写代码的分析→落"缺工具"卡而非临场写；⑤ 五极色图例/点/密度三处一致。发现问题即修（前端改动 F5 即可，.mjs 验）。
2. **Flash 80% gate 实测**：`py tests/eval_template_flash.py` 跑真 DeepSeek Flash 测 13 代表问模板命中率。≥80% → single 路径主导；<80% → 保 concept+multi/unknown 兜底（渐进激活，零回归）。
3. **`{{upload:preset}}` 胶囊**（Phase 2 跳过项，用户指定后续）：`panel.js renderAnswer` 正则加 upload 分支 + onMsgClick handler 调 `range-presets.js triggerUpload`；遇缺 Range/商业/居住用地引导点击上传。配套 catalog 转 upload 引导源（buildContext 已不注 catalog，胶囊需另取 catalog 列预设）。
4. **后端 density 全退场**（需 SOP）：删 `/api/v1/geo/density` + `kde_raster`(F_005)——承重函数，走完整 SOP（Developer→Reviewer→Tester）。确认无其他引用后删。
5. **P2 专业框架做厚**：B/C 赛道范式树（`B_TRACK_PARADIGM` 粗粒度9类 + `SCALE_PARADIGM.method_templates` C对齐住建部城市体检四层级 + `select_template(track,card)` 单一真相源）+ `field_dictionary` 接入承重函数（上传层 alias，行355 polarity门控/356五级值域/576-581 domain-element）+ `popularity` role（timestamp/boundary_id/category 已存）+ `_missStats` 遥测 + confidence 阈值 0.3。
6. **加技能 #8-11**：nearest/hotspot/area_stats/merge/extract_feature 进 TEMPLATE_REGISTRY（结构已可生长，paradigm.py 追加 dict + stages.js SKILL_DEFS 同步 + harness 路由自动生效）。

### 承重（必守，下会话续改时留意）
- **EMC 委托主 Toolbox 不自造**（本轮核心决策）：density→generateHeatmap/Grid/TerrainForAI；新增分析能力优先扩 Toolbox 工具+程序化入口，勿在 EMC 自造并行 geo 端点。
- **数据可见纪律铁律**：EMC 只用 `getLayers().filter(visible)` 的层，registry 未显示层一律禁用（pickVisiblePointLayer）；buildContext 不注 catalog 全量。
- **run_python 收口**：harness gate 拦截，`ctx.allowCodeViz=true` 才放行；缺工具→EXIT_GAP 缺工具卡引导后续开发。
- **主 Toolbox dialog 流不破**：`generateHeatmap`/`generateTerrain` 不动，仅新增 `*ForAI` 入口；`generateGridForAI` 签名不改。
- **三大件出图**（addResultLayer+paint固化）/ **5.74 对账**（_verifyClaims/_extractClaimedLayers，_registerToolboxLayer 强化之）/ **四态出口**（EXIT_RESULT/GAP/CONCEPT/PARTIAL）/ **frame-based trust** / **F_005**（kde_raster 端点保留 deprecated）—— 全不破。
- **前端 ESM 验证**：`node --check x.js` 对 ESM 假绿，改前端 JS 须 `.mjs` 副本（`cp x.js /tmp/x.mjs && node --check`）。
- **字段语义层**：物理列名不改 / L2_* 五极色对齐 tokens(geojson.emotion #78DC32 套) 勿回散用。
- commit 只不 push（用户手动）；专业词+通俗解释（用户初学者）；交付物中文；**每较大改动同步 todo.md + revision-log**（用户强调）。

### 本轮改的关键文件（下会话续改看这些）
- **Toolbox 程序化入口**：[frontend/js/grid-tool.js](frontend/js/grid-tool.js)（generateGridForAI，已存在 ensure_zone 用）/ [frontend/js/heatmap-tool.js](frontend/js/heatmap-tool.js)（**新增 generateHeatmapForAI + generateTerrainForAI**）
- **EMC 委托+纪律**：[frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js)（TOOLS.density 三模式委托 + pickVisiblePointLayer + resolvePointLayer + _registerToolboxLayer + addResultLayer _ui.tool 注入 + buildContext visible-only + 6 点层工具守卫）/ [frontend/js/ai_qa/harness.js](frontend/js/ai_qa/harness.js)（runTemplatePath + 路由 + query-first round0 + run_python gate + composeGapCard 缺工具分支）
- **编排+校验**：[frontend/js/ai_qa/stages.js](frontend/js/ai_qa/stages.js)（SKILL_DEFS 镜像 + validateParams + _PARAM_ALIAS 25 + normalizeCard template/params）/ [ai_qa/paradigm.py](ai_qa/paradigm.py)（TEMPLATE_REGISTRY 9 技能 + template_registry_text）/ [ai_qa/prompts.py](ai_qa/prompts.py)（diagnose method→template + 技能目录附录）
- **后端**：[api/geo_routes.py](api/geo_routes.py)（buffer 聚合闭环 + density 标 DEPRECATED）/ [core/spatial_analysis.py](core/spatial_analysis.py)（L1 极性3级兜底 + score 自适应 + kde_raster actual_cell_m attrs）
- **测试**：[tests/test_emc_template.py](tests/test_emc_template.py)（5 结构测）/ [tests/eval_template_flash.py](tests/eval_template_flash.py)（手动 Flash 80% gate 评测）

### 承重 memory 索引
- 本轮新增：`emc-delegates-to-toolbox`（EMC 不自造 GIS，委托主 Toolbox generateHeatmap/Grid/TerrainForAI + Layers 可见数据纪律 + run_python 收口——本轮核心架构决策）
- 复用：`stand-on-giants-shoulders`（优先业界成熟库别造轮子）/ `emc-tri-state-exit-contract`（四态出口+format漂移修复）/ `node-check-esm-unreliable`（.mjs 验）/ `commit-only-user-pushes` / `pro-term-plus-plain-meaning` / `maintain-revision-log`+`todo-revision-log-sync`（每事同步）/ `chinese-all-deliverables` / `no-handoff-on-routine-commit`（说"交接"才覆写本卡）/ `landuse-codes-2023`（用地分类读 .py）

---

## 新会话 prompt（复制即用）

```
继续 EMC。工作机制重构三阶段全部完成（站在巨人肩膀上落地，5.89-5.94 六 commit）：
EMC 现委托主 Toolbox（generateHeatmap/Grid/TerrainForAI），不自造 GIS；数据只用 Layers 可见层；
run_python 收口（ctx.allowCodeViz 才放行）；技能化编排（TEMPLATE_REGISTRY 9 技能 + runTemplatePath，p^N→p²）。
静态全过（.mjs ESM + py_compile + pytest 166 过/6 预存无关）；运行时待开 serve 验。
本地领先 origin ≥1 commit（Phase 2 8deab94 确定 unpushed）待手动 push。
本次按交接卡选主线：① 最优先开 serve 运行时验证各 track（density 三模式/只传L1不跑L2/buffer面板/缺工具卡）
② Flash 80% gate 实测（py tests/eval_template_flash.py）③ upload 胶囊（Phase 2 跳过项）
④ 后端 density 全退场（SOP）⑤ P2 专业框架 ⑥ 加技能 #8-11。
承重：EMC 委托 Toolbox 不自造 / 数据可见纪律铁律 / run_python 收口 / 主 Toolbox dialog 流不破 /
三大件出图+5.74+四态+frame-based trust+F_005 不破 / node --check 假绿须 .mjs / commit 只不 push /
专业词+通俗解释 / 每较大改动同步 todo+revision-log。
先读交接卡 memories/repo/session-handoff.md，再动手。
```
