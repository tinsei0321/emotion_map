# EMC 06-llm 报告评估

> 评估对象：`tests/reports/report-2026-07-24-06-llm.md`（工具选择 11 例，2026-07-24 16:55）
> 评估人：CodeBuddy（K3）｜ 2026-07-24 ｜ 归档：`.codebuddy/reports/`
> 关联：[emc-eval-report05-2026-07-24.md](emc-eval-report05-2026-07-24.md)（T1-T7）、[emc-experience-plan-2026-07-24.md](emc-experience-plan-2026-07-24.md) §五（D1-D5）

---

## 〇、结论摘要

pass 0%（0/11）——**但不能误读为系统退化**。11 例拆解：

| 失败簇 | 例数 | 性质 | 归属 |
|--------|------|------|------|
| TOL-003/006/009（夷陵区） | 3 | **错误期望的用例**——数据真缺夷陵区边界，EMC 判缺是正确的 | 测试资产/用例 bug |
| TOL-001/002/010（renderedNew=0） | 3 | 新渲染断言**首次立功**，暴露渲染断裂 | 产品/环境待二分 |
| TOL-007/008（错工具） | 2 | "空间密度分布"→clip/extract_feature，语义桥缺失 | 系统（诊断选型） |
| TOL-004/005/011（超时） | 3 | 链式即兴 + 例间层堆叠加剧上下文膨胀 | 系统（D3 适应证）+ 测试基建 |

叠加两项测试基建债：**seam 数据路径 stale**（文件已迁 `DATA/performance/`，seam 仍 fetch `DATA/processed/` → 404）+ **例间不清层**（e2e_points 堆叠）。**T1/T8 修复并重测前，本轮 pass 率不作系统能力基线。**

## 一、飞轮本体评估

- **renderedNew 断言首战立功**：s4 类失败（触发工具但地图未渲染）首次被结构化捕获——这正是"以图说话"落图自检（plan P1-4）要的信号，断言硬化方向验证正确。
- **新暴露基建债**（本轮才真正咬人）：seam 路径与 DATA 资产迁移脱节；例间无清层。飞轮 v5 清单需补 T8/T9（见 §四）。

## 二、六问题诊断（证据全文挂 file:line）

### Q1 彩虹热力图不显示 → 渲染断裂，根因待二分，结构弱点已坐实

- 现象：density 触发、state 层 +1/+2，但 `renderedNew=0`（TOL-001/002/010，s4）。
- **结构性弱点（坐实）**：`renderLayer` 失败被静默容忍（seam 注释自承"底图 style 未加载时 addSource 抛错…忽略"，`e2e-seam.js:37-39`），**state 层与地图渲染脱节，无重试、无上报**——产品侧同样无渲染成功校验。
- 二分假设：① 环境性——底图天地图瓦片 404（`map.js:31` DEFAULT_BASEMAP='tianditu-img-nolabel'，key/Referer 受限）致 style 加载流程受阻；② 产品性——heatmap 层渲染真 bug（`map.js:669-726` heatmap spec，weight 表达式引用字段缺失时 MapLibre 抛错）。
- 验证法：运行时二分——浏览器开 console 跑一例 density，看 `addSource/addLayer` 抛错内容（style not loaded = 环境；paint expression = 产品）。**T12**。
- 根治：renderLayer 失败重试+错误上报 + 落图自检（产物入 state 后核验 map source 真实存在）——plan P1-4 前置项。

### Q2 e2e_points 一堆且重复生成 → seam 命名 + 例间不清层 + 路径 stale

- **来源**：测试 seam 内部命名 `base='e2e_points'`（`e2e-seam.js:36`），L2 拆组后 = `L2·e2e` 组 + `积极/中性/消极·e2e_points` 子层——不是你的数据，是测试装载器。
- **重复生成**：`llmRun` 每例执行 loadCSV+loadRange 但**例间不清层**（`test-cases.js:17-24`），`addLayer` 零去重（E3）→ 11 例 × 4 行 ≈ 44 行层堆叠；范围层同样每例重复加。堆叠还反向膨胀 grounding 上下文（每层都进 buildContext 列表），加剧超时。
- **路径 stale**：数据池已迁 `DATA/performance/`（`test-assets.js:3` 注释），但 seam 仍 fetch `/DATA/processed/`（`e2e-seam.js:102`）→ 404 → loadCSV 静默失败（try/catch 吞掉，`test-cases.js:19`）→ **06 全部用例实际跑在 05 遗留的陈旧层上**（页未刷新）。
- **唯一 ID 诉求**（用户再次点名）= plan P0-2 srcId 指纹，**升级为最高优先**；seam 侧 T8 修路径 + T9 例间清层（或 srcId 幂等后自然解决）。

### Q3 缺工具 → 用户已认领（后续工具补齐+本地化），挂 D5 跟踪。

### Q4「看伍家岗区情绪点哪里最密集」→ 只产出 clip 层 —— 三重根因

1. **语义桥缺失**：density 在工具目录的触发词是"核密度/密度分析/聚集强度/热力分布"（`paradigm.py:250`），**"密集/最密集"不在其中**（全 prompts.py/paradigm.py 无"密集"匹配）——用户的自然表达与工具语义之间缺同义词桥。
2. **假完成放行**：clip 产一层 → `newLayerCount>0` → EXIT_RESULT 判"完成"（脱节 4：成功定义错位）——链只走了第一步就被裁定器放行。
3. **无 method/chain**：D3 链式模板适应证不变（"哪里最密集"= 范围→剪裁→density 固定链，应 0 中间轮）。

### Q5 夷陵区边界识别失败 → EMC 是对的，用例是错的

- **数据真相**：`DATA/boundaries/行政区.geojson` 仅 9 个要素，MC 值 = 龙泉/猇亭区/点军区/**小溪塔**/白洋/西陵区/龙泉绿心/伍家岗区/生物产业园——**无"夷陵区"**（小溪塔是夷陵区驻地，但名义不匹配）。
- EMC 判"缺夷陵区边界"= **正确的真 GAP**；`test-assets.js:8` 注释"含西陵/伍家岗/夷陵等区"是**错误描述**，TOL-003/006/009 是错误期望用例。
- 修复：① 资产描述改正；② 用例期望改为"识别真缺口并精确说明"（现有 9 单元清单 + 缺夷陵区）或补夷陵边界数据；③ D1 派生判定器落地后，此类答复会从"请补充数据"升级为"现有：西陵区/伍家岗区/猇亭区…；缺：夷陵区——是否用「小溪塔」近似？"的精确交互。

### Q6「工具链不支持热力/聚合」→ 工具认知四重断裂（用户质问成立：认知未形成，但比想象细）

工具目录其实**有** density/hotspot/zonal_stats（`paradigm.py:170-255`），模型却答"仅支持裁剪/融合/缓冲/属性筛选"——断裂在：

1. **同义词桥缺**：用户说"密集/六边形网格"，目录写的是"核密度/规则方格"——词不通则工具隐身（同 Q4-①）。
2. **缺正向映射**：catalog 只有"工具→何时用"的反向描述（when/params/yields/contributes——SOP 卡雏形已具！），没有"问题类型→分析方法→工具"的正向路由（method 层缺失，plan P1-3/D3）。
3. **文档漂移**：density 的 yields 仍写"规则方格面网格"（`paradigm.py:252`），但 `tools.js:192-193` 注明 density 已委托 Toolbox `generateHeatmapForAI`（2D 彩虹热力）/`generateGridForAI`（网格），`/geo/density` 后端已 deprecated——**目录描述的产物 ≠ 实际产物**，模型按旧描述无法理解"彩虹热力图"就是 density 的 2D 形态。
4. **Toolbox 能力不在目录**：heatmap/grid/terrain 三个前端委托能力没有独立目录条目（仅 density 代表），"六边形密度网格"找不到字面对应 → 模型如实（且错误地）宣判"不支持"。

> 注：GEO_TOOL_CATALOG 已是 SOP 卡雏形（when/params/yields/contributes 四段式），P1-2 不是从零建卡，而是**升级它**：补同义词桥、对齐实际产物、收编 Toolbox 能力、加正例负例。

## 三、增量项（T8-T12）与优先级

| # | 项 | 内容 | 优先级/挂靠 |
|---|-----|------|------------|
| **T8** | seam 数据路径同源 | fetch 路径改 `DATA/performance/`（或从 test-assets 注入 base） | **P0 插队**（与 T1 同级，评估基线前提） |
| **T9** | 例间层清理 | llmRun 例间清层（或 srcId 幂等后免清）；范围层同 | P0（随 T8） |
| **T10** | 同义词桥 | "密集/最密集/聚集在哪/六边形网格"→density/grid 进 SOP 卡与决策树 | 随 D3/P1-2 |
| **T11** | 目录对齐+收编 | catalog yields 对齐 Toolbox 实际产物；heatmap/grid/terrain 能力入目录 | 随 P1-2 |
| **T12** | 渲染断裂二分+自检 | 运行时二分 env/product；renderLayer 重试+上报+落图核验 | P1-4 前置 |
| — | 夷陵用例修正 | 资产描述改正 + 期望改"真缺口精确说明"（或补数据） | 随 T9 |
| — | srcId 唯一 ID | 用户第二次点名，**P0-2 确认为最高优先** | B1 头部 |

**重测纪律**：T1（05 报告）+T8/T9 完成后重跑 04/05/06 全量，重建干净基线；此前所有涉极性/涉装载的 pass 率不作数。

## 四、证据锚点（供其他模型复核）

- seam 命名/路径：`frontend/js/e2e-seam.js:36`（e2e_points）、`:102`（/DATA/processed/ stale）；资产迁移声明：`frontend/js/test-assets.js:3`；实际文件：`DATA/performance/yichang_L2_T1_L2_result_csv.csv`。
- 例间不清层：`frontend/js/test-cases.js:17-24`（llmRun 装载段，无 clear）。
- 夷陵区：`DATA/boundaries/行政区.geojson` 9 要素 MC 值清单（无夷陵区，含小溪塔）；错误描述 `test-assets.js:8`。
- 密集缺词：prompts.py/paradigm.py 全文无"密集"；density 触发词 `paradigm.py:250`。
- 目录漂移：`paradigm.py:248-254`（density yields=方格网格）vs `frontend/js/ai_qa/tools.js:192-193`（已委托 Toolbox，/geo/density deprecated）。
- 渲染：`frontend/js/map.js:31`（天地图默认底图）、`:669-726`（heatmap spec）；静默容忍 `e2e-seam.js:37-39`。
