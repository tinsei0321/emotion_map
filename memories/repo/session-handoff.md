# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月10日（收工） | 分支 `main`（已与 origin/main 同步，无积压）| 本次 = EMC 回答策略重构(三态出口) + 阶段3(追问/折叠/用地色) + 防缓存(start.bat/build角标) + EMC 端到端 Phase 1 图表生成（revision-log 5.61–5.67）

---

## 当前节点：EMC 端到端升级 · Phase 1 图表已完+已推（待用户肉眼验 + Phase 2/3）

### 背景
两段工作：(1) 根治 EMC「只说不做」+代码块泄漏（三态出口契约）；(2) 对标开源 AI+GIS agent（GIS Copilot/LLM-Geo/GeoGPT/ChartGPT/mapgpt），补 EMC 端到端最大差距——**答案内图表**。**承重逻辑全程未碰**（三态出口/视野-数据-结论同步/KDE cascade-exclude/4×5/对称拉伸/tip-popup/EMC 深色/网格视图配对）。

### ✅ 本会话已做（7 提交 5.61–5.67，全部已推 origin/main，无积压）
- **5.61 三态出口契约**（闸门）：harness 代码强制终态(做成 EXIT_RESULT/缺数据 EXIT_GAP/纯问答 EXIT_CONCEPT)，零成功→确定性缺数据卡不裸输；parseAgentStep 抗漂移(漂移注入 8/8)+`narrated` 哨兵；onDegraded 永不裸输+终态徽章；密度出口=真 KDE（core/spatial_analysis.kde_raster F_005 + /geo/density + tools.js density）+ hotspot 修落图层；装齐 scipy/libpysal/esda。站在巨人肩膀上：CARTO/QGIS-Copilot/LLM-Geo。
- **5.62 阶段3 三项**：推荐追问胶囊（`#chat-suggest`，上下文相关 exit/intent+ref）+ 长对话折叠（>2 自动折叠旧的留近 2）+ 用地色（PDF 附录B 抽 39 类 → landuse_colors.js，matcher 10/10）。
- **5.63–5.65 用地色三连修**：DLMC 权威落色（读要素 DLMC 非 label）→ fillOpacity 0.6（原默认 0.15 看不见）→ **全路径覆盖**（预设 range-presets / 手动上传 main.js / EMC tools.js addResultLayer 三处收口 `landuseLayerPaint`）+ serve.py **build 角标**（`build <git短哈希>·<js/css 最新 mtime>`，硬刷新看角标时间=新代码）。
- **5.66 start.bat 单实例**：netstat+taskkill 清 8080/8000 旧进程再起单实例；ASCII-only（cmd 按 GBK 解析 .bat，UTF-8 中文破坏 `^|` 转义）。
- **5.67 EMC 图表 Phase 1**（端到端超越点）：答案 `{{chart:TYPE|title|..|x=labels|y=values}}` → Chart.js 柱/折/饼（bar=排序/line=时序/pie=占比）。panel.js `_renderCharts`（挂 enhanceCodeBlocks，覆盖所有 renderAnswer 站点）+ Chart.js@4 CDN + FINAL_TEMPLATE 教出图 + .aiq-chart-wrap CSS。**两陷阱**：`.format()` 吞括号→正则兼容 1~2 花括号；畸形规格用 HTML 实体防二次嵌套。

### 🔍 验证（Playwright，控制流风险大故上，均已过）
parse 漂移注入 8/8 ｜ landuse matcher 10/10 + landuseLayerPaint 9/9 ｜ KDE 真数据冒烟(500点→110格) ｜ app 启动+/geo/density 注册 ｜ pytest 123过/0新坏 ｜ 用地三路(预设/手动/EMC) served JS 接线确认 ｜ start.bat 实测 kill+起单实例 ｜ **图表真实管线**（注入伪答案→restoreHistory→renderAnswer→_renderCharts）：3图渲染+3实例绑定+畸形留1不嵌套+零崩 ｜ build 角标注入确认。

### ⚠️ 收尾未决（下会话先处理）
1. **mapgpt-main 待删**（红线，需用户确认）：`docs/mapgpt-main/`（**未入仓**、读完即删的参考包）——用户说"读完就删"，待一句"go"即 `rm -rf`。
2. **{{focus}} 单括号隐患**（latent bug，未修）：`.format()` 把 `{{focus}}`→`{focus}`(单括号)喂模型，模型可能输单括号，而前端 focus/show/inspect 正则只匹双括号 → 按钮可能不渲染。chart 已兼容 1~2 花括号；**下次顺手把 focus/show/inspect 正则也改兼容**（panel.js renderAnswer 内）。

### ⬜ 下会话：先验 Phase 1，再 Phase 2/3
1. **验 Phase 1**（用户硬刷新，看 build 角标时间更新）：问"各区情绪排序"→ 出柱图；"T1→T3 演进"→ 折线；"4 域归因占比"→ 饼。同时复验用地三路上色 + 追问胶囊 + 长对话折叠。
2. **Phase 2 DataEye 深化**（低工作量高收益）：tools.js buildContext 加字段 dtype+2-3 样本值（borrow GIS Copilot see_vector/_get_df_types_str），复杂 where 命中率升。只富化 context 字符串。
3. **Phase 3 复合工具+报告导出**：compare/timeseries 一次性取数喂图（core/spatial_analysis + api/geo_routes + tools.js + paradigm catalog）+ 答案脚"导出报告"钮（Chart.js `toBase64Image()`→markdown/HTML→PDF，事企业"城市体检报告"出口）。
4. **Phase 4（远期）**：tool-doc RAG（FAISS，工具数翻倍再做）+ code-gen kernel（GIS Copilot/GISclaw 路）。

### 承重（必守）
- 图表/用地色都是**纯增量**（新模板+后处理器 / 三处 addLayer 收口点 paint），不动 map.js 渲染管线/极色色带。
- panel.js **不 import** map/state/panel 主窗口写函数（AI 子系统边界）。
- 改色带一律离散分段（ramp-discrete-segments）；改前端视觉先读 brand-visual.md。
- start.bat 保持 ASCII-only；serve.py 的 no-store/?v/build-角标 勿退。

### 本轮改的关键文件（下会话续改看这些）
- EMC 回答/防裸输/图表：[harness.js](frontend/js/ai_qa/harness.js) / [stages.js](frontend/js/ai_qa/stages.js) / [panel.js](frontend/js/ai_qa/panel.js)（`_renderCharts`+`enhanceCodeBlocks`）/ [tools.js](frontend/js/ai_qa/tools.js)（density+landuseLayerPaint）/ [ai_qa.css](frontend/css/ai_qa.css)
- 密度后端：[core/spatial_analysis.py](core/spatial_analysis.py)(kde_raster F_005) / [api/geo_routes.py](api/geo_routes.py)(/geo/density) / [paradigm.py](ai_qa/paradigm.py) / [prompts.py](ai_qa/prompts.py)(chart 指引+出口契约) / [manifesto.py](ai_qa/manifesto.py)
- 用地色：[landuse_colors.js](frontend/js/landuse_colors.js) / [range-presets.js](frontend/js/range-presets.js) / [main.js](frontend/js/main.js) / [map.js](frontend/js/map.js)(isTool 增 density) / [docs/landuse-colors.md](docs/landuse-colors.md)
- 防缓存/启动器：[serve.py](frontend/serve.py)(build 角标) / [start.bat](start.bat) / [requirements.txt](requirements.txt)(scipy)

### 承重 memory 索引
- 本轮新增：`emc-tri-state-exit-contract`（出口契约=代码强制终态）/ `emc-charts-and-end-to-end`（{{chart}}→Chart.js + 两花括号陷阱 + Phase1完/Phase2-3待做）
- 相关：`emotion-map-logic-chain` / `view-data-conclusion-sync` / `design-language-consistency-iron-rule` / `stand-on-giants-shoulders` / `verify-real-endpoint` / `maintain-revision-log`+`todo-revision-log-sync` / `no-routine-playwright-verify`（本轮控制流风险大，例外跑了 Playwright）/ `no-handoff-on-routine-commit`（说"交接/收工"才覆写本卡）/ `chinese-all-deliverables`

## 新会话 prompt（复制即用）
见下方代码块。
