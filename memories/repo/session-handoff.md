# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月15日（5.98 任务计划拟定；5.95–5.97 承重双修+静态清理+Flash+lingbot 收工）| 分支 `main`（**本地领先 origin 待用户手动 push**）| 本次会话 = 5.95–5.98

---

## 当前节点：EMC 工作机制重构 + 承重收尾全部完成，任务计划已定（下会话从 A1 起一步步推进）

### 背景
5.89–5.94 三阶段重构（站在巨人肩膀上落地）+ 5.95 承重双修 + 5.97 静态清理 = **EMC 工作机制静态已知 bug 全收**。Flash 80% gate = 9/13 = 69% NO-GO（single 路径保渐进激活，不主导）。lingbot-map 借鉴评估不采纳（5.96，3D 重建项目非 AI+地图）。todo/revision-log 结构已整改（最新内容置顶）。

### ✅ 本会话已做（5.95–5.98，每 commit 同步 todo/revision-log）
- **5.95（`32a86ac`）承重双修**：① visible 纪律被默认 layer 绕过——rank/buffer/clip/zonal 的 SKILL_DEFS+TEMPLATE_REGISTRY optional_defaults 去硬默认 `layer='yichang_l2_t1'`（该默认经 validateParams 合并绕过 pickVisiblePointLayer，致"只传 L1·T1 却跑 L2"）；buffer 缺省 layer 改用可见点层名。② buffer 编辑面板 _ui 元数据丢失——TOOLS.buffer 产物注入 _ui（distance 关键+dissolve/样式+sourceLayer），修 openBufferDialog 回填 DEFAULTS(1000m) 重做全然不同 buffer。
- **Flash 80% gate 实测 = 9/13 = 69% → NO-GO**（真 DeepSeek-v4-flash）：2 MISS 概念问 Flash 散文直答不吐 diagnose JSON 卡（走 general 短路，非真回归）+ 2 真歧义（clip↔zonal / overlay↔multi，所选皆有效）。**single 路径保渐进激活兜底**（Flash 不命中 template→unknown→while-loop，零回归，符合 5.91 设计）。
- **5.96（`53d4a9a`）lingbot-map 借鉴评估**：双 Explore agent 全仓深读证伪——实为 3D 重建/SLAM（GCT=几何上下文变换器，图像帧→3D 点云），非 AI+地理地图。技术栈零重叠、可复用代码≈0。决策不采纳：3 条架构思想启发（流式增量/keyframe 降级/YAML 配置，均未来需求或冗余）落 `docs/reference-lingbot-map-eval.md`，原项目 324M（未跟踪）已删。
- **5.97（`ff5bec2`）承重静态清理**（5.95 双修时静态另揪的中/低兄弟 bug，前置收掉）：① density 2D/terrain 产物侧栏不刷新——generateHeatmapForAI+generateTerrainForAI 补 renderLayerList/refreshLegend/reorderAllZ/showLayerManager（+import，与 grid-tool 同模式）；② query_layers 列不可见层——加 l.visible 过滤（与 pickVisiblePointLayer/buildContext 同源）；③ isRange 把分析产物当 range 显假图例——改为排除任何 _ui.tool 标记层（buffer/overlay/area_stats/merge 不再显 NAVY 假图例），收掉 density 死码。
- **结构整改（`d337b3b`）**：用户批评"todo/revision-log 还停留在 7月13日"——根因=5.89–5.97 被 append 到底部。整改：todo.md 机械搬移到顶部按 07-15/07-14 建段；revision-log §5 顶加「📍 最新动态」指针；记 upload 胶囊搁置。memory `todo-revision-log-sync` 强化"最新必须置顶、禁底部追加"。
- **5.98（`9794461`+）任务计划拟定**：详细计划记入 todo.md 07-15 🗺️ 段 + revision-log 5.98。

### ⬜ 下一步任务计划（详细见 [docs/todo.md](docs/todo.md) 07-15 🗺️ 段）
**推进序：A1 → A2（并行）→ A3 → B1**

1. **A1（最优先）Flash 命中率提升 69%→≥80%** → 解锁 single-path 主导。**关键=概念问 Flash 散文直答不吐 diagnose JSON 卡（2 MISS）** → 改 `ai_qa/prompts.py` DIAGNOSE_TEMPLATE 强约束「任何问必先吐 JSON 卡、概念问 template=concept」+ few-shot；**单此一项即 85% PASS**。歧义 2 MISS 细化 `ai_qa/paradigm.py` triggers/voice。重跑 `tests/eval_template_flash.py`（`PYTHONPATH=. PYTHONIOENCODING=utf-8` + .env 加载）验 ≥80%。承重不破 normalizeCard/runTemplatePath/四态/渐进激活兜底。
2. **A2 后端 density 全退场（SOP 删 F_005）**：删 `/api/v1/geo/density` + `kde_raster`（前端已全委托 Toolbox，无引用）。完整 SOP（Developer→Reviewer→Tester）+ tracker F_005 注册表维护。承重：buffer 聚合闭环 + aggregate_by_polygons L1 兜底/score 自适应（spatial_analysis 331-372）不能连带破。
3. **A3 P2 专业框架**：B/C 赛道范式树（B_TRACK_PARADIGM 9 类 + SCALE_PARADIGM.method_templates 对齐住建部城市体检四层级 + select_template 单一真相源）+ field_dictionary 接承重函数（spatial_analysis 355 polarity 门控/356 五级值域/576-581 domain-element）+ popularity role（timestamp/boundary_id/category→热度）+ _missStats 遥测 + confidence 0.3。与 A1 协同（范式树进 diagnose prompt）。承重：field_dictionary 接承重须 SOP。
4. **B1 加技能 #8-11（gated A1）**：TEMPLATE_REGISTRY 9→14（nearest/hotspot/area_stats/merge/extract_feature）。paradigm.py dict + stages.js SKILL_DEFS 镜像 + prompts.py 枚举串；TOOLS.* + _GEO_TOOLS 已实装。
- **持续 C1**：用户开 serve 运行时验证各 track（density 三模式 / 只传 L1·T1 不跑 L2 / buffer 点 B 回填真半径 / 缺工具卡 + 5.97 三修复：侧栏刷新/可见层/图例）。
- **搁置 C2**：upload 胶囊（用户 07-15 指定）。

### 待 push（用户手动）
本地领先 origin（5.89–5.98）。本地 origin/main ref 已前进到 `5d4bb54`（用户已 push 前批 32a86ac/05d539a/53d4a9a/ff5bec2/5d4bb54）。push 前 `git fetch` 确认真实远端，再手动推。

### 承重（必守，下会话续改时留意）
- **EMC 委托主 Toolbox 不自造**（本轮核心决策）：density→generateHeatmap/Grid/TerrainForAI；新增分析能力优先扩 Toolbox 工具+程序化入口，勿在 EMC 自造并行 geo 端点。
- **数据可见纪律铁律**：EMC 只用 `getLayers().filter(visible)` 的层（pickVisiblePointLayer / query_layers / buildContext 三处同源）；single 技能不硬默认 layer（5.95 已修）；registry 未显示层一律禁用。
- **run_python 收口**：harness gate 拦截，`ctx.allowCodeViz=true` 才放行；缺工具→EXIT_GAP 缺工具卡。
- **主 Toolbox dialog 流不破**：`generateHeatmap/Terrain/Grid` 不动，仅 `*ForAI` 入口；`generateGridForAI` 签名不改；buffer 产物 _ui 元数据透传（5.95 已修）。
- **三大件出图**（addResultLayer+paint固化+侧栏刷新，5.97 补齐）/ **5.74 对账**（_verifyClaims/_extractClaimedLayers/_registerToolboxLayer）/ **四态出口**（RESULT/GAP/CONCEPT/PARTIAL）/ **frame-based trust** / **F_005**（kde_raster 保留 deprecated，A2 SOP 才删）—— 全不破。
- **前端 ESM 验证**：`node --check x.js` 对 ESM 假绿，改前端 JS 须 `.mjs` 副本（`cp x.js /tmp/x.mjs && node --check`）。
- **字段语义层**：物理列名不改 / L2_* 五极色对齐 tokens(#78DC32 套)。
- **todo/revision-log 最新置顶铁律**（07-15 用户批评后强化）：todo 按日段倒序（最新一天 `## 📅` 在顶）、revision-log §5 顶「📍 最新动态」指针；**禁止底部追加**；每事同步、不攒会话末。
- commit 只不 push（用户手动）；专业词+通俗解释（用户初学者）；交付物中文。

### 本轮改的关键文件（下会话续改看这些）
- **A1 改**：[ai_qa/prompts.py](ai_qa/prompts.py) DIAGNOSE_TEMPLATE（diagnose method→template，约 182-183 枚举串）+ few-shot ／ [ai_qa/paradigm.py](ai_qa/paradigm.py) TEMPLATE_REGISTRY 9 技能（210-253）triggers/voice。
- **A1 测**：[tests/eval_template_flash.py](tests/eval_template_flash.py)（13 代表问手动评测，PYTHONPATH=. + .env 加载跑）／ [tests/test_emc_template.py](tests/test_emc_template.py) 5 结构测。
- **A2 改**：[api/geo_routes.py](api/geo_routes.py) density 端点（523+ DEPRECATED）／ [core/spatial_analysis.py](core/spatial_analysis.py) kde_raster(F_005, 120-228) ／ [core/tracker.py](core/tracker.py) F_005 注册。
- **A3 改**：[ai_qa/paradigm.py](ai_qa/paradigm.py) + ai_qa/field_dictionary.py + [core/spatial_analysis.py](core/spatial_analysis.py) 355/356/576-581。
- **编排+校验**（A1/B1 触）：[frontend/js/ai_qa/stages.js](frontend/js/ai_qa/stages.js) SKILL_DEFS/validateParams/_PARAM_ALIAS/normalizeCard（template 归一 166-169）／ [frontend/js/ai_qa/harness.js](frontend/js/ai_qa/harness.js) runTemplatePath(189-236)/路由(351-354)/run_python gate(423-425)/composeGapCard(96-119)。
- **详细计划**：[docs/todo.md](docs/todo.md) 07-15 🗺️ 段。

### 承重 memory 索引
- 本轮强化：`todo-revision-log-sync`（最新置顶铁律，07-15 用户批评后强化——todo 按日段倒序、revision-log §5 顶「最新动态」指针，禁底部追加）。
- 复用：`emc-delegates-to-toolbox`（EMC 不自造 GIS，委托 Toolbox + Layers 可见纪律 + run_python 收口）／`emc-tri-state-exit-contract`（四态出口+format漂移修复）／`stand-on-giants-shoulders`／`node-check-esm-unreliable`（.mjs 验）／`commit-only-user-pushes`／`pro-term-plus-plain-meaning`／`maintain-revision-log`／`chinese-all-deliverables`／`no-handoff-on-routine-commit`（说"交接/开新会话"才覆写本卡）／`landuse-codes-2023`（用地分类读 .py）／`verify-real-endpoint`（验证打真 POST 端点）。

---

## 新会话 prompt（复制即用）

```
继续 EMC，按任务计划推进（详细见 docs/todo.md 07-15 🗺️ 段 + revision-log 5.98）。
基线：5.89–5.97 工作机制重构 + 承重双修 + 静态清理全收；Flash gate 69% NO-GO（single 路径保渐进激活）。
本次从 A1 起：Flash 命中率提升 69%→≥80%，解锁 single-path 主导。
关键=概念问 Flash 散文直答不吐 diagnose JSON 卡（2 MISS）→ 改 ai_qa/prompts.py DIAGNOSE_TEMPLATE
强约束「任何问必先吐 JSON 卡、概念问 template=concept」+ few-shot（单此一项即 85% PASS）；
歧义 2 MISS（clip↔zonal/overlay↔multi）细化 paradigm.py triggers/voice。
重跑 tests/eval_template_flash.py（PYTHONPATH=. PYTHONIOENCODING=utf-8 + .env 加载）验 ≥80%。
A2（后端 density 全退场 SOP 删 F_005）可并行。
承重：EMC 委托 Toolbox 不自造 / 数据可见纪律铁律 / run_python 收口 / 主 Toolbox dialog 流不破 /
三大件出图+5.74+四态+frame-based trust+F_005 不破 / node --check 假绿须 .mjs / commit 只不 push /
专业词+通俗解释 / todo+revision-log 最新置顶同步（禁底部追加，每事同步）。
先读交接卡 memories/repo/session-handoff.md + docs/todo.md 07-15 🗺️ 段，再动手。
```
