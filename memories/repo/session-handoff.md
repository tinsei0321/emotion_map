# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月08日 13:00 | 分支 `main` | HEAD=739f198（已 push）

---

## 当前节点：AI 问答 · 专业认知层 + GIS 骨干·**后端半完成**（前端接线 + 流式未做）

### 核心判断（问题重定义，2026-07-08 确立）
5.35 审查层接通后"回答几乎不能用"——根因**不在审查/revise**，而在整个 ai_qa 缺一层「专业认知」：agent loop 在前端 [harness.js](frontend/js/ai_qa/harness.js)，工具 [tools.js](frontend/js/ai_qa/tools.js) 只读单一 `activeAnalysis()` 聚合层——不能下钻/上卷/按几何过滤，故无论宏观/微观问都只能"在这一层按 |polarity_index| 排序报几个格"= **答成坐标（范式错位）**。审查再严也只是打磨一个范式就错了的答案。

**用户定调**（4 决策）：① 质量优先、流式收尾顺手做；② 尺度-范式 运行时内置 + skill 双落；③ 数据缺口 = 硬缺口请求上传 / 软缺口降级标注；④ **GIS 常规操作（几何剪裁/合并、用地字段筛选、面积统计等）为必备，且 AI 问答内自动调用**（用户不手动点）。

**验收线（质量达标硬测）**：问"中心城区哪里最需优先更新？"→ 必须给**结构化结论**（哪类更新单元/哪些街道/哪类用地系统性落后 + 4×5 归因），**而非坐标**；再问微观（这个公园哪里最差）→ 落点结论。**两问范式不同 = 过线**。过线才开 AI 问答 UI 重做。

### ✅ 本会话已做（后端半，commit 332230c + 739f198，已 push）
- **Phase A2/B3 知识基座**：[ai_qa/paradigm.py](ai_qa/paradigm.py)（尺度-方法-范式矩阵 macro/meso/micro + 4 域出口启发 + GIS 操作目录 10 工具 + DIAGNOSE 卡 6 字段 + strategy 语义）；[manifesto.py](ai_qa/manifesto.py) 第十一节硬约束。
- **Phase B1/B2 GIS 骨干**：[core/geo_registry.py](core/geo_registry.py)（lazy 缓存 L1/L2×T1-T3 + 边界 preset，按 id 引用免大数据中转）；[api/geo_routes.py](api/geo_routes.py) **10 个 `/api/v1/geo/*` 操作**（filter_attr/clip/merge/area_stats/zonal_stats/rank/buffer/overlay/nearest/hotspot + catalog）+ 复合入参 `layer+range+pre_filter`；挂载 [api/main.py](api/main.py)。
- **Phase A1 后端 DIAGNOSE**：[prompts.py](ai_qa/prompts.py) `build_diagnose_prompt`（6 字段问题理解卡；范式表 format 后拼接避花括号）；[schemas.py](ai_qa/schemas.py) phase 放行 diagnose；[router.py](ai_qa/router.py) diagnose 流式分支。
- **Phase A3 后端审查**：[review.py](ai_qa/review.py) 第 7 条 `scale_paradigm_fit`（key 稳定，旧 6 条不动）+ review prompt 拼回 MANIFESTO（治 professional/actionable 偏松）+ REVIEW_TEMPLATE 六→七。
- **验证**：12 路由注册 ✓；E2E `zonal_stats`(L2×行政区) →「白洋/伍家岗区/猇亭区 pi+归因」**宏观结构化结论（非坐标）= 验收核心路径打通**；clip/area_stats/filter_attr ✓；`tests/test_geo_routes.py` 8 passed，全量 124 passed（5 既有失败与本轮无关）。

### ⬜ 下会话：前端接线 + 流式（同 plan `main-memories-repo-session-handoff-md-a-smooth-hamster.md`）

**最紧迫 = B4 + A1 前端**（用户可见的质量解锁：让 AI 真正调 geo 工具产出结构化答案）：
1. **B4** [tools.js](frontend/js/ai_qa/tools.js)：把 10 个 geo 工具暴露成 agent tool（每个 = 调对应 `/api/v1/geo/*`，POST JSON 取 rows/geojson）；`buildContext()` 增列「可用边界 preset + 用地类型 + 时点 + geo 工具清单」（调 `/geo/catalog`）；视觉工具（focus/inspect/open_attribution）不动。
2. **A1 前端** [stages.js](frontend/js/ai_qa/stages.js) +`diagnoseStep`（phase=diagnose，onReason + token 累积→parseDiagnoseCard 取 JSON 卡，容错同 parseAgentStep）；[harness.js](frontend/js/ai_qa/harness.js) orchestrate 开头先跑 diagnose（失败降级空卡不阻塞），卡注入后续 agent/final prompt（context 或 system 前置「已诊断：scale=X/method=[...]」）；[panel.js](frontend/js/ai_qa/panel.js) 渲染问题理解卡（domain/scale/decision/outlet + data_plan.strategy + method）。
3. **C** [panel.js](frontend/js/ai_qa/panel.js)：strategy=request_upload → 渲染"请求上传"卡（说清要什么/为何/格式）；fallback_annotated → 结论显著标注口径。
4. **D 流式三件套**（治当前 O(n²) 卡顿）[panel.js](frontend/js/ai_qa/panel.js)：onFinal/onRevise/onReason 改 token buffer + `requestAnimationFrame` 逐字 drain，流式期间 textContent（裸文本 + 既有 chat-cursor ▍），**仅 onFinalDone/onReviseDone 跑一次 marked.parse**；scrollBottom 改"用户上滑停跟 + 回到底部按钮"。思考提示从气泡 inline（panel.js:117）移到 `#chat-panel` sticky dock（贴底不被顶走）+ 阶段进度 chip。完毕戳 `onFinalDone/ReviseDone/Degraded` 末尾追加「回答完毕 · 情绪地图测试版 v1.0 · MM月DD日 HH:MM」+ 存 trace.doneAt + 历史恢复同步。
5. **A4**：沉淀 `.claude/skills/emotion-scale-paradigm/`（方法论镜像，表1/表2/卡 schema/校验清单）；同步 [docs/ai-qa-design.md](docs/ai-qa-design.md) 第 3/4/5 章（加认知层 + GIS 骨干）。

### 承重（必守）
- panel.js **不 import** map/state/panel 主窗口函数（AI 子系统边界铁律）。
- REVIEW_CHECKLIST key 稳定（新增不删旧，前端按 key 渲染）。
- revise 1 轮不递归 / 审查与 diagnose 失败均降级不阻塞。
- V4 模型 ID：`deepseek-v4-pro`/`deepseek-v4-flash`（别名 pro/flash，勿回旧 ID）。
- MANIFESTO 花括号：MANIFESTO 本身从不 `.format()`（仅拼接）；参与 `.format()` 的 *_TEMPLATE 内 `{` `}` 必须转义 `{{ }}`（DIAGNOSE_TEMPLATE/AGENT_TEMPLATE/REVIEW_TEMPLATE 已处理，改时留意）。
- geo_routes 复合入参范式：分析类（zonal_stats/rank/hotspot）接受 layer+range+pre_filter 一次完成，避免 AI 中转大数据；返回 rows（属性表，非整 GeoJSON）给 LLM。

### 前端文件清单（下会话改这些）
- `frontend/js/ai_qa/tools.js`（B4：geo RPC + buildContext）
- `frontend/js/ai_qa/stages.js`（A1：diagnoseStep + parseDiagnoseCard）
- `frontend/js/ai_qa/harness.js`（A1：orchestrate 前插 diagnose）
- `frontend/js/ai_qa/panel.js`（A1 卡渲染 + C 请求上传卡 + D 流式三件套）
- `frontend/css/ai_qa.css`（D sticky dock + 完毕戳 + 卡片样式）
- `frontend/js/ai_qa/api.js`（可能：geo 工具的 fetch 封装，或直接在 tools.js fetch）

### 验证（下会话）
- **acceptance 硬测**：`py frontend/serve.py 8080` → 问"中心城区哪里最需优先更新？"→ 期望 diagnose 判 macro+更新 → AI 自动调 `/geo/zonal_stats`(更新单元) → 结构化结论（无坐标）；再问"这个公园里哪里最差？"→ micro → `/geo/clip`+`/geo/rank` → 落点。**两问范式不同 = 过线**。
- 前端验证用 **webapp-testing skill**（非 Playwright）；默认交付肉眼验，控制流/数据流/bug 才上。
- pytest `tests/test_geo_routes.py` 保持 8 passed（回归）。

### 承重 memory 索引
- 本轮相关：`emotion-map-logic-chain`（演示逻辑链=全局纲领）/ `view-data-conclusion-sync` / `stand-on-giants-shoulders`（GIS 复用 GeoPandas 不造轮子）/ `spatial-aggregation-numeric-coerce`（聚合前 to_numeric）/ `verify-real-endpoint`（geo 端点已打真 POST）/ `verify-with-webapp-testing-skill`（前端验证）/ `maintain-revision-log` + `todo-revision-log-sync` / `chinese-all-deliverables` / `push-not-redline` / `timestamp-no-weekday` / `no-routine-playwright-verify`
- AI 问答既有：审查层接通（5.35）/ Agent Loop ReAct（5.34）/ Harness 四层（5.33）—— 见 revision-log

## 新会话 prompt（复制即用）
见下方代码块。
