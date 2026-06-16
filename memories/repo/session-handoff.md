# 会话交接卡

> 换机后读取此文件恢复上下文。

## 当前节点 — 2026-06-16 傍晚

### 代码状态

| 模块 | 状态 |
|------|------|
| tests/ | 56 tests 全过 |
| apps/app_main.py | ~350 行，工具栏直接调用弹窗，Import 后 A/OV/TB 立即可用 |
| apps/app_dialogs.py | ~1030 行，Import 用 early-return 关闭模式 |
| apps/app_console.py | 不变 |
| api/ | FastAPI 4 端点，就绪未启动 |
| core/db.py | EmotionDB 就绪 |
| core/spatial_analysis.py | Gi* / Moran's I / 行政聚合 / H3 就绪 |
| SCRIPT/emotion_analysis_v1.py | DeepSeekL2Analyzer 代码就绪，未接入 A 对话框 |
| SCRAPER/spiders/ | 4 个 spider (xiaohongshu/weibo/meituan/su12345) |

### A 对话框当前 UI

```
ENG 分析引擎
  ● L2 . SnowNLP粗粒度分析 (离线)
  ○ L3 . LLM 细粒度语义解析 (DeepSeek)     ← Key 自动从 .env 读取
  ○ L4 . 语料库多维归因 (需 LLM + 语料库)

[开始分析]
```

### 搁置项

- 点击详情面板: `core/ui_components.py` 标记 `[SHELVED]`
- 弹窗按钮样式: 尝试 CSS 调整后还原
- Toast CSS: 尝试调整后还原
- v3 UI 改造: 延后

### CLAUDE.md 新增规则

- 开发工作流: 每次修改后清缓存 + 杀旧进程 + 重启
- 沟通方式: 中文回复, 结论先行
- Git: 提交前展示变更, commit 用英文
- 红线: 删文件/改密钥/push 必须先问

## P0 阻断债清理（2026-06-16 家用机完成，待办公机补验证）

> 起因：迁移前全体系审查（见 `C:\Users\Hi\.claude\plans\1-vibe-coding-skill-mcp-agent-ui-2-lively-flute.md`）发现 9 个 🔴 阻断项。已在**家用机**完成其中 5 个代码级修复，但 pytest + FastAPI HTTP 验证因依赖未装（家用机 pypi 直连 SSL 被墙）未能跑，**需在办公机补跑**。

### 已完成（5 项，函数级已验证）

| # | 文件 | 改动 | 验证状态 |
|---|------|------|----------|
| 1 | `core/spatial_analysis.py` | h3 v3→v4 API（`latlng_to_cell`/`cell_to_boundary`，Polygon 坐标序反转） | ✅ 运行时验证（create_hex_grid 返回有效六边形）|
| 2 | `SCRIPT/emotion_analysis_v1.py` | CorpusAnalyzer 双 `analyze_single` 合并为单一带默认参签名 | ✅ compile + ABC 兼容验证 |
| 3 | `docs/decisions.md` | 决策追踪系统 ADR-008 → ADR-011（消解与 Scrapy 的编号冲突）| ✅ grep 验证唯一 |
| 4 | `CLAUDE.md` + `.claude/settings.json` + `.claude/hooks/on_post_edit.py` | "自动执行"承诺对齐 + 新增 PostToolUse hook（仅清 .pyc，不重启/不测试）| ✅ settings.json JSON 合法 + hook stdin 模拟验证 |
| 5 | `SCRIPT/data_governance.py` + `api/routes.py` | 抽出 `run_governance_pipeline()`（API/CLI 共用、不含 sys.exit、保留 LLM 漏斗、可选空间过滤）；`main()` 改薄包装；API `/governance` 删内联+硬编码 relevance，改调主管道 | ✅ 直接调用 run_governance_pipeline 验证：无 DEEPSEEK_API_KEY 时返回明确错误（不再静默产出 keyword-only 假 L1），MOD_GOV.F_007 追踪正常 |

### 待办公机补验证（家用机缺依赖，pypi 被墙）

1. `py -m pytest tests/ -q` —— 56 tests 全过回归（家用机无 pytest）
2. FastAPI `/api/v1/governance` HTTP 冒烟 —— `TestClient` POST，确认 404/无key-500/有key-200 三路径（家用机无 fastapi）
3. governance 等价性：同一 raw 数据，CLI `python SCRIPT/data_governance.py` 与 API `POST /governance` 产出 L1 CSV 行数+列集一致

### 重要提醒

- 这些文件**在会话开始前就已是 modified 状态**（办公机既有未提交改动），`git diff` 含办公机旧改动 + 本次 P0 改动，提交前需人工 review。
- 家用机 Python 实为 **3.13.2**（非 CLAUDE.md 所写 3.14.5）—— 又一处文档/实际不符，归 P1。
- `python` 命令在家用机 bash 下 exit 49 不可用，需用 `py`（hook 已用 `py`）。

## 前端 Phase 1 已落地（2026-06-16 家用机，geojson.io 1:1 外壳）

> 计划见 `C:\Users\Hi\.claude\plans\1-vibe-coding-skill-mcp-agent-ui-2-lively-flute.md` Part E。已用 Playwright 实测渲染通过。

### 已建（`frontend/`，纯 HTML/CSS/JS + MapLibre GL JS）
- **Token 单源**：`tokens.json` 新增 `geojson` 段（brand `#007afc`、gray-50..900、半径/阴影/字体对齐 geojson.io；emotion 五色保留）；`generate_css.py` 扩展生成 `frontend/css/tokens.css`（74 个 `--geojson-*` 变量，Light-first）。改色一处 → 三端同步。
- **外壳**：64px 固定头栏 + 工具栏按钮组（flexbox，非绝对定位）+ flex(map | 320px 右面板) + 折叠 + 右下角图例。
- **地图**：MapLibre GL JS（jsdelivr CDN 可用），默认**天地图底图**（CN 可达，复用 `apps/static/tianditu_label.json`，key 已内嵌）；底图切换 popover。
- **情绪点**：circle 层，五色 match + 白描边；**点击 → 蓝色选中光环 + 右面板「详情」卡片**（复活了 SHELVED 的 F_014）。
- **右面板 4 tab**：概览(五级统计卡+迷你柱状图) / 分析(L2/L3/L4 引擎 radio) / 详情(点击点) / GeoJSON(占位)。
- **Export modal**（geojson.io 风格原生 `<dialog>`，8px 圆角 + shadow-lg + 复选框模块）。

### 预览命令
```
cd d:/Github/emotion_map && py -m http.server 8080
# 浏览器开 http://127.0.0.1:8080/frontend/index.html
```

### 已知限制 / 待办
- **CartoDB 三底图（浅/深/标准）在 CN 被墙**（`tiles.basemaps.cartocdn.com` 连接重置）→ 默认天地图可用；CartoDB 选项留给网络允许时。
- **数据是 Phase 1 样本**（`js/state.js` 生成 80 个宜昌假点）；Phase 2 接 `/api/v1/points`。
- A 分析 tab、Import/Export modal、TB 表格 modal 目前是占位（Phase 2 接真实端点）。
- 边界范围层、热力图切换、空间分析 tab 待 Phase 2-3。

## 下一阶段

**Phase 2**：接真实数据（新增 `/api/v1/points` 端点 + `api.js` fetch）、A 分析接 `/analyze`、Import/Export/TB modal 功能化。
**P1 清债**：配色单源（删 config.py COLOR_MAP/FOLIUM_COLOR_MAP）、删 folium、Python/pandas 降档、CORS、天地图 Key 移 .env、skill 清理。

完整计划 + 评审见 `C:\Users\Hi\.claude\plans\1-vibe-coding-skill-mcp-agent-ui-2-lively-flute.md`（Part A-E）。
