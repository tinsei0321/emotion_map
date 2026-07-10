# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月10日 | 分支 `main` | 本次 = EMC 三态出口契约(闸门) + 阶段3(追问/折叠/用地色) + 用地色全路径 + build stamp + 单实例 start.bat（revision-log 5.61–5.66）

---

## 当前节点：EMC 回答策略重构 + 阶段3 三项 + 用地色 · 已实现+Playwright 验过（待用户肉眼验 + 待 push）

### 背景
用户反复报 EMC「只说不做」+把工具调用以 ```json 代码块糊进答案。本轮系统性重构回答策略，并把阶段3 三项（推荐追问/长对话折叠/用地色）做完。**承重逻辑全程未碰**（视野-数据-结论同步 / KDE cascade-exclude / 4×5 归因 / 对称拉伸 / tip-popup / EMC 深色 / 网格视图配对 setViewMode/_gridMapSetVis）。

### ⚠️ 待办（收工时未完成）
1. **push 未成功**：本地有 **2 个未推提交**（GitHub 网络当时 reset）：`410ae0c`(用地色全路径+build stamp)、`a8517ac`(start.bat)。**下会话第一步：`git push`**（或确认已推）。
2. **用户肉眼验未做**（用户机器当时浏览器缓存旧 JS，已重启 serve.py+加 build 角标解决，但用户尚未确认看到新效果）。

### ✅ 本会话已做（6 提交，详见 revision-log 5.61–5.66）

**闸门·三态出口契约**（`9bb5298`，根治只说不做+代码块泄漏）：
- 根因：出口逻辑只在 prompt 不在代码；DeepSeek 格式漂移 → parseAgentStep 返畸形 → 8 轮空转 → `onDegraded` 把原始 token 糊进答案泡（=代码块）。
- 修：[harness.js](frontend/js/ai_qa/harness.js) 三态终态机（做成/缺数据/纯问答，代码裁定）+ 零成功→EXIT_GAP；[stages.js parseAgentStep](frontend/js/ai_qa/stages.js) 抗漂移（归一 drift schema+别名+`narrated` 哨兵，**漂移注入测试 8/8**）；[panel.js onDegraded](frontend/js/ai_qa/panel.js) 永不裸输 + 终态徽章；密度出口做真（[core/spatial_analysis.py kde_raster](core/spatial_analysis.py) F_005 + [api/geo_routes.py /geo/density](api/geo_routes.py) + tools.js density）；hotspot 修落图层；装齐 scipy/libpysal/esda（hotspot Gi* 之前也因此失败）。

**阶段3 三项**（`00f754e`）：推荐追问胶囊（stampDone 后 `#chat-suggest`，上下文相关 intent/exit+ref）/ 长对话折叠（>2 条自动折叠旧的留近 2，摘要 stub+展开）/ 用地色（PDF 附录B 抽 39 类 → [landuse_colors.js](frontend/js/landuse_colors.js) matcher）。

**用地色三连修**：DLMC 权威落色（`a512e27`，优先读要素 DLMC 非 label）→ fillOpacity 0.6（`2c75ff6`，原默认 0.15 几乎看不见）→ **全路径覆盖**（`410ae0c`：手动上传 main.js + EMC tools.js addResultLayer 也接 `landuseLayerPaint`，三处收口）。

**防缓存**（`410ae0c`）：[serve.py](frontend/serve.py) 注入右下角 build 角标 `build <git短哈希>·<js/css 最新 mtime>`，改代码后硬刷新看角标时间变=新代码。

**单实例启动器**（`a8517ac`）：[start.bat](start.bat) 启动前 netstat+taskkill 清 8080/8000 旧进程，再起单实例；ASCII-only（cmd 按 GBK 解析 .bat，UTF-8 中文会破坏 `^|` 转义）。

### 🔍 验证（Playwright，已过）
parseAgentStep 漂移注入 8/8 ｜ landuse matcher 10/10 + landuseLayerPaint 9/9 ｜ KDE 真数据冒烟(500点→110格) ｜ app 启动+/geo/density 注册 ｜ pytest 123过/0新坏(6预存无关) ｜ **预设/导入/EMC 三路用地色 served JS 接线确认**（main.js×3/tools.js×2）｜ start.bat 实测 kill 旧 PID+起单实例 ｜ build 角标注入确认。

### ⬜ 下会话：先 push，再陪用户肉眼验

**第一步**：`git push`（推 410ae0c + a8517ac + 本交接卡提交）。

**用户肉眼验清单**（硬刷新后，看右下角 build 角标时间是否更新）：
1. **核密度问答**：问"对 L2 做核密度分析"→ 应出**密度图层+结论+零代码块**（闸门核心复验，`docs/landuse-colors.md` 不相关，是 EMC）。
2. **用地色三路**：手动上传 `用地_商业.geojson` / 点商业预设按钮 / 让 EMC"筛选西陵区商业用地"→ 都应**红 #FF0000 0.6 不透明**；居住=黄 #FFFF2D；公园广场=绿 #00FF00。
3. **推荐追问**：答案后底部出追问胶囊，点击即发。
4. **长对话折叠**：连问 3+ 轮，旧的自动折叠为摘要，点展开。
5. **缺数据出口**：构造硬缺口问 → 出"需补充数据"卡（不硬答不编造）。

### 承重（必守，下会话续改时留意）
- 用地色只改三个 addLayer 收口点的 paint（range-presets/main.js/tools.js addResultLayer）；**勿动 map.js 渲染管线/极色色带**。density 复用 isTool 色带 fill 管线 2D。
- panel.js **不 import** map/state/panel 主窗口写函数（AI 子系统边界）。
- 改色带一律离散分段（遵 ramp-discrete-segments）。
- start.bat 保持 ASCII-only（中文会破坏 cmd 解析）。

### 本轮改的文件（下会话续改看这些）
- EMC 三态/防裸输：[frontend/js/ai_qa/harness.js](frontend/js/ai_qa/harness.js) / [stages.js](frontend/js/ai_qa/stages.js) / [panel.js](frontend/js/ai_qa/panel.js) / [tools.js](frontend/js/ai_qa/tools.js) / [ai_qa.css](frontend/css/ai_qa.css)
- 密度后端：[core/spatial_analysis.py](core/spatial_analysis.py)(kde_raster F_005) / [api/geo_routes.py](api/geo_routes.py)(/geo/density) / [ai_qa/paradigm.py](ai_qa/paradigm.py) / [ai_qa/prompts.py](ai_qa/prompts.py) / [ai_qa/manifesto.py](ai_qa/manifesto.py)
- 用地色：[frontend/js/landuse_colors.js](frontend/js/landuse_colors.js)(新) / [range-presets.js](frontend/js/range-presets.js) / [main.js](frontend/js/main.js) / [map.js](frontend/js/map.js)(isTool 增 density) / [docs/landuse-colors.md](docs/landuse-colors.md)(新)
- 防缓存/启动器：[frontend/serve.py](frontend/serve.py)(build 角标) / [start.bat](start.bat) / [requirements.txt](requirements.txt)(scipy)

### 承重 memory 索引
- 本轮新增：`emc-tri-state-exit-contract`（出口契约=代码强制终态；格式漂移→修复非裸输；密度出口=真KDE+hotspot落图；onDegraded 永不裸输）
- 相关：`emotion-map-logic-chain` / `view-data-conclusion-sync` / `design-language-consistency-iron-rule` / `stand-on-giants-shoulders`(CARTO/QGIS-Copilot/LLM-Geo) / `verify-real-endpoint`(真POST+真数据) / `maintain-revision-log`+`todo-revision-log-sync` / `no-routine-playwright-verify`(本轮控制流风险大，例外跑了 Playwright) / `chinese-all-deliverables` / `no-handoff-on-routine-commit`(说"交接"才覆写本卡)

## 新会话 prompt（复制即用）
见下方代码块。
