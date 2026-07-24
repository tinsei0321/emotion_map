# EMC 全面修复工程 · 问题 Backlog

> 2026-07-24 ｜ 承接：测试飞轮两批验证后定调治本（K3 `emc-sys-improvement-2026-07-24.md` P0/P1/P2）
> 权威 plan：`~/.claude/plans/emc-sys-rippling...`（注：实际文件 `backup-immutable-otter.md`）+ 本批 plan `emc-gis-rippling-dream.md`
> 红线：diagnose prompt（`ai_qa/prompts.py`）/ harness `orchestrate` 主循环（`harness.js`）/ ChatRequest schema（`ai_qa/schemas.py`）—— 改前先扩 eval，每次只改一处。

---

## 已修（保留 · 两批改动已 commit）

| # | 修复 | 落点 | 验证 |
|---|------|------|------|
| H1 | template 信号接通 | [panel.js:1090](../frontend/js/ai_qa/panel.js#L1090) onDiagnose dispatch `diagnose:done` + [e2e-seam.js:56](../frontend/js/e2e-seam.js#L56) chatPhases 听事件 | TOL-001 template=density 非 null（C1 断链已治） |
| H3 | 参数断言硬化 | test-cases.js PARAMS 断言接 sig.params（cell/radius/boundary 容差匹配） | 10 例从"恒 pass"变真断言 |
| H5 | JSON 报告 | `/_test/report` 同步落 `report-*.json`（含 run 元数据） | serve.py + test-board.js |
| EMC-SUM | 摘要 3 行格式 | EMC-SUM v1（链路/产物/状态 键值定序） | 报告 per-case 块 |
| A | 字段识别扩容 | tools.js DataEye 关键字段全值 | 非 6 字段×2 样本×24 字符 |
| B | 摘要 3 行中文 | EMC-SUM 中文渲染 | — |
| C | 渲染断言 | test-cases.js mapSources + renderedNew 断言 | 验图层真上地图 |

**回归基线**：`py -m pytest tests/ -q` → 203 passed, 7 skipped（2026-07-24）。

---

## 待修（治本 · 按 K3 P0→P1→P2）

### ① 超时 91s（模型路由 · P0 红线 · 单列 plan）

- **证据**：`tests/reports/report-2026-07-24-03-llm.json` s3=waitAnswer，durationSolo 91s；report-01 工具例 14/15 超时。
- **真因（本会话纠正 K3 §3.1 过时认知）**：
  - K3 文档说"diagnose Pro→Flash"已**过时**——diagnose 实跑 flash（[stages.js:236](../frontend/js/ai_qa/stages.js#L236) `model: 'flash'`）。
  - 真因 = `agent`（[stages.js:217](../frontend/js/ai_qa/stages.js#L217) `ctx.model` 默认 pro）多轮 reasoner + `final`（[:251](../frontend/js/ai_qa/stages.js#L251) pro）+ `revise`（[:296](../frontend/js/ai_qa/stages.js#L296) pro）**串行**；`_thinkMode` 默认 'pro'。
  - `runTemplatePath`（单技能 0 agent 轮，[harness.js:285](../frontend/js/ai_qa/harness.js#L285)）已存在但被 `_tplHitRateReady` 80% gate 卡。
- **治本方向**（K3 §3.1 A/B/C）：①预算制（分段 deadline + 超预算降级 skip revise / 异步 review，保必有回答）；②per-stage 路由（final→flash 简单任务，仿 `deliberateStep` 门控）；③`runTemplatePath` eval≥80% 后提为单技能默认（0 agent 轮）；④进度透明（阶段时间线 / 增量落图 / 可取消）。
- **红线**：触 harness `orchestrate` 主循环 → **必先扩 `tests/eval_template_flash.py` 再动手，每次只改一处**。

### ② density 抓取漏（P0 安全批 · 本批修）

- **证据**：[tools.js:1061](../frontend/js/ai_qa/tools.js#L1061) density 委托前端 Toolbox（`generateHeatmap/Grid/TerrainForAI`，不走 `/geo/density`），飞轮 sig.tools 正则 `/geo/|/spatial/`（[e2e-seam.js:56](../frontend/js/e2e-seam.js#L56)）抓不到 → TOL-001 永远 tool_hit=0。
- **治本方向**：density（及同类前端委托工具）执行后 dispatch `tool:executed {tool, name, newLayerIds, ts}`，`e2e-seam` 监听并入 sig.tools。注：模型路由后 density 可能改走真 KDE `/geo/density`（届时正则自通），本批先补事件信号保证观测不依赖路径。

### ③ 选错工具（P1 · GIS 推理链）

- **证据**：TOL-003（clip 应 density）：template=null + tools=[clip]。
- **根因**：Flash 从 SKILL_DEFS 一次性直选，prompt 无"方法→尺度→工具→路径"链式结构；词表漂移（C2）加剧。
- **治本方向**（K3 §3.3）：①建 10 工具 SOP 卡（用途/适用尺度/前置/参数契约/输出契约/失败模式/正例2+负例1）；②diagnose 增 method 字段（**触 diagnose prompt 红线 → 先冻结 eval**）；③method→tool 确定性映射（代码非 LLM）；④校验修复环。

### ④ 字段识别完整 manifest（P1）

- **证据**：DataEye 已扩容（A）但非导入时一次计算全复用；每层字段识别分散、无统一 manifest。
- **治本方向**（K3 §2.2/§3.2）：Layer Manifest 管线（导入时一次性计算全链路复用）= `{srcId, kind, featureCount, bbox, crs, fields{role,dtype,confidence,samples}, semantics, quality}`；三级识别（嗅探正则/dtype → 字典 `core/field_dictionary.py` 单一事实源 → LLM 兜底按 srcId 缓存）；消费点 buildContext / diagnose data_plan 三态 / SKILL_DEFS 参数校验。

### ⑤ 渲染 bug（P1 · 图层入 state 地图空）

- **证据**：[e2e-seam.js:33](../frontend/js/e2e-seam.js#L33) renderLayer 容错吞错；图层入 state 后地图空（2a 场景）。
- **治本方向**（K3 §3.4）：渲染自检（addLayer 后查 source exists / features 非空 / bbox 落请求范围 / 与输入层不重复 srcId）；失败标 partial 而非 result（治"假完成"）。

### ⑥ 摘要完整 ①②③（计划数/命中数/占比）

- **证据**：飞轮未采集 diagnose method/plan → EMC-SUM ②产物 `layers=计划n→实产n` 的"计划 n"无源。
- **治本方向**：method/plan 采集（diagnose 增字段回传，同 domain_lens threading 范式 5.108）。

---

## 路线（P0→P1→P2）

- **P0 止血**：①模型路由（红线·单列）②density 信号（本批）+ 滚动复位（E6）+ srcId 去重（E3，本批安全 3 项）。
- **P1 机制（核心主线·GIS 工具补全）**：⑥Layer Manifest（④）⑦10 工具 SOP 卡 + 成图范式 + plan-once-execute（③⑤，"以图说话"落地）⑧异步 review + 进度时间线。
- **P2 长期**：⑨Dataset Registry + 预检喂 diagnose（srcId 已铺垫）⑩LLM 网关 + 遥测 ⑪episodes golden set + 回归 gate。

10 工具（已登记 `paradigm.TEMPLATE_REGISTRY`）：density / zonal / rank / buffer / clip / overlay / merge / extract_feature / hotspot / nearest。
