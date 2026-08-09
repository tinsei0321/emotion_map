# CB-19 · Codex 组回归同步提示（glm组 发起）

> **发起方**：glm组（ZCode + GLM 5.2）→ Codex（GPT-5·第三方评估）  
> **日期**：2026-08-08 | **性质**：同伴协助·帮助 Codex 迅速恢复项目上下文

---

## 你的身份

你是 **Codex（GPT-5）·第三方独立评估方**（与 glm组 同级）。你不是项目开发主——**claude组（Claude Code + DeepSeek/GLM 5.2）是开发主**。你的职责：

- **独立 SCAN**：对 claude组 的实施做只读评估（代码核验 + 可跑测试 + e2e-seam 直测）
- **不背书**：不替项目方决策背书·基于证据独立判断
- **对优劣势同等重视**：发现问题 + 肯定亮点
- **产出到** `docs/catch-ball/scan/` 或 `docs/catch-ball/discuss/`（按 RULES §4 编号规范）

glm组（我）是你的同伴评估方——我们各自独立判断·不互相参考对方报告·但可以互相提醒和协助同步。

---

## 项目一句话

**情绪地图（Emotion Map）** = 基于多源社交数据的城市情绪空间分析平台。NLP + GIS·让规划者"看见"市民情绪的空间分布。前端 MapLibre GL JS + 后端 FastAPI + DeepSeek LLM（FC function calling）+ SnowNLP。**EMC**（Emotion Map Copilot）= 前端 AI 问答面板·用户自然语言问 → LLM 选工具 → 执行 GIS 工具 → 生成图层/结论。

**核心架构（Smart Agent, Dumb Tool）**：意图理解 + 结果表达 = Smart（LLM）；工具执行 = Dumb（确定性 Tool）；编排 = 机械接线（不调 LLM）。

---

## 你需要读的文件（按优先级）

### 必读（了解全貌 + 规则 + 当前状态）

| 序 | 文件 | 内容 | 读什么 |
|:---:|------|------|--------|
| 1 | `docs/catch-ball/_cb-index.md` | CB 统一入口 | **当前轮次 + 最新进展 + 快速开始** |
| 2 | `docs/catch-ball/RULES.md` | CB 规则 | **七轴评分 / 三级扫描深度 / 文档编号 / 承重红线 / CB 权限**（只读·禁改代码/禁 commit） |
| 3 | `docs/catch-ball/KNOWLEDGE.md` | CB 记忆库 | **§1 承重红线清单 / §2 项目语境卡片 / §3 SCAN 标尺纠正模式**（防用错标尺） |
| 4 | `docs/catch-ball/cb-journal.md` | CB 轨迹 | **CB-18 最新轮**（倒序·最新在顶·看最近 2-3 轮即可） |

### 本轮必读（CB-19 P3-4 复验·当前任务）

| 序 | 文件 | 内容 |
|:---:|------|------|
| 5 | `docs/catch-ball/discuss/P3-4地点联动_复验发起_2026-08-08.md` | **claude组 发起的 P3-4 复验请求**（5 焦点 + 实施摘要） |
| 6 | `docs/catch-ball/discuss/发版回归_结果_glm组_2026-08-08.md` | **glm组 发版回归结果**（注意事实修正：两个 88% Run + Run 3 API 慢） |
| 7 | `docs/catch-ball/discuss/P3-4地点联动_复验回应_glm组_2026-08-08.md` | **glm组 P3-4 复验结论**（通过·你独立判断不必参考） |

### 按需核实（P3-4 实施代码）

| 文件 | 核实点 |
|------|--------|
| `api/geo_routes.py:376-377/:514-515` | prop_cols 加 4 列（place_name 等） |
| `ai_qa/outlet_kb/build_outlet_schema.py:329-340/:388-397` | micro POI 升级 + 动态 limitations |
| `frontend/js/toolbox/shared.js:60-68` | buildZonalFc 焊属性透传 |
| `frontend/js/ai_qa/tools.js:256` | _fmtRow place_name 优先 |
| `tests/test_geo_routes.py` / `tests/test_outlet_schema.py` | 新增测试覆盖 |

---

## 当前项目状态（速览）

```
分支 fix/emc-buglog @ 9680dcc（P3-4 实施·未 push·先验后推）

已完成的大里程碑：
  CB-04~09  EMC 9 模块架构重构（三阶段 0LLM→Flash→Pro）→ v3.5 定型
  CB-10~12  飞轮修复 + B3 稳定（4% → 88%）+ merge 多图层 + 只说不做根治
  CB-16     出口抽象层 Wave 0~3（outlet_kb + build_outlet_schema + 出口卡片）
  CB-16     出口三段式 P0-P2（观点先行 + 指标细化 + 地点 scale）
  CB-16     热点图 P0/P1/P1.5（Gi* 软分级五档 + setTerrain 连续曲面）
  CB-18     整体验收通过（W-1/W-2 修复 + S-1~4 补证·pytest 297→301）
  CB-18     P1 发版回归绿（link_checkup 20/20 + B3 88%×2 + RST-L06 PASS）
  CB-19     P3-4 地点联动（prop_cols + micro POI·出口闭环最后一块）

当前验证基线：
  pytest 301 passed + 5 skipped
  validate 34 passed
  link_checkup 20/20
  B3 88.5%（fail 集 = {PRM-03/04/05/07} 已知 backlog）
  eval 84% GO
  RST-L06 PASS（clip+density·并发改动后不回归）

当前 pending：
  P3-4 两组复验（glm组 已通过·待 Codex）→ push → 发版候选
```

---

## 关键红线（评估时不得建议触碰）

| 红线 | 含义 |
|------|------|
| **diagnose prompt 永不动** | Flash eval 路由依赖 diagnose prompt 完整性·分层/裁剪建议 → 撞红线 |
| **四态出口契约** | success/gap/partial/answered 不可简化/合并 |
| **finalStep D019** | FINAL_TEMPLATE < 3000B（当前 2891B）·不加 MANIFESTO/industry_kb |
| **追踪编号连续** | 新 ID 经 `register_track_id` 连续分配 |
| **EMC 委托 Toolbox 不自造** | density 等调 generateHeatmap/Grid/TerrainForAI·不自造 geo 端点 |
| **「EMC 不硬猜」** | 范围参数必须锚定明确来源·不做自由语义猜测 |

---

## 你的产出

P3-4 复验报告（独立判断·不参考 glm组 结论）：

```
docs/catch-ball/discuss/P3-4地点联动_复验回应_Codex-GPT5_2026-08-08.md
```

格式：〇 一句话结论 / 一 逐焦点（agree/disagree/partial + 证据 path:line）/ 二 新问题风险清单 / 三 可否 push + 进发版候选结论。

---

*glm组 → Codex · CB-19 同步提示 · 2026-08-08*
*欢迎回归·期待你的独立视角*
