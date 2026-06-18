# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

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
| L1 | LLM 大模型接入（溯佰科平台 Agent 嵌入） | ⬜ |
| L2 | 时序分析（多时间切片对比） | ⬜ |
| L3 | 行政区划聚合视图 | ⬜ |
| L4 | 自动报告生成（PDF） | ⬜ |
| L5 | 空间自相关分析（Moran's I） | ⬜ |
| L6 | 问题-对策映射引擎 | ⬜ |
| L7 | Docker 部署 | ⬜ |
| L8 | 配置外部化（.env） | ⬜ |
| L9 | 移动端适配 | ⬜ |
| L10 | 语料库本地化词典 | ⬜ |
| L11 | 空间分析引擎 MVP（缓冲区分析 + 行政单元聚合） | ⬜ |
