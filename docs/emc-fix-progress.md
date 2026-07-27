# EMC 修复工程 · 总进度汇总卡

> **一页看清** EMC 修复整体状态（分层·✅已修/🔄进行中/⬜待修）。详时序见 [revision-log §5](revision-log.md#L226)；评估决策见 [cb-journal](catch-ball/cb-journal.md)（倒序·CB-05 在顶）。
> **更新**：2026-07-27（CB-05 后 + 5.228 数据识别 visible 修）
> **承继**：本卡由 `emc-fix-backlog.md`（2026-07-24 快照）更名重写，聚焦"分层总进度 + 重点突出"，区别于 revision-log 的时序大段。

---

## 总进度（分层）

### 契约层（参数契约 · Smart↔Dumb 接口）
- ✅ density 参数契约四处分裂 → [`tool_contracts.py`](../ai_qa/tool_contracts.py) 单一真相源 + [`validate_skill_params.py`](../tests/validate_skill_params.py) 守护（CB-04·5.226）
- ✅ ForAI=dialog 镜像（`generateHeatmapForAI` 复用 `computeStyle`·CB-04）
- ✅ `normalizeParams` 按工具区分别名（治 `_PARAM_ALIAS` 误伤 density·CB-04）
- ✅ rank `by` 默认 worst + compare_regions 入 prompt（CB-04）
- ✅ density triggers 补「热力图」+ 参数名对齐 + few-shot 极性例（CB-04）
- ⬜ 13 工具 `panel_source` 全核查（L3·density 完整·其余 28 项待·非色板核心）

### 体验层（UX · EMC 核心价值）
- ✅ **ReAct 超时根治**（while-loop 7 策略·L0 路由补"网格/方格"+L1 缩轮+L2 完成信号+L3 prompt 条件化+P0-A 异常降级不丢图+P0-B 单轮 45s 超时+P1-C 早终止·CB-06·5.229）
- ✅ **去 LLM 审查**（REVIEW_ENABLED 默认 false + FINAL_TEMPLATE 内嵌自查 5 条·省 7-14s·CB-05·5.227）
- ✅ **删除符号四层根治**（strip~~ + `getValidRefNames` 扩展治 CSS invalid 主因 + css 弱化 + REVISE 补·CB-05）
- ✅ `runTemplatePath` 加 `onObservation`（地图出图后 dock 反馈·治"出图但 dots 不停"·CB-05）
- ✅ panel 清审查 UI（占位/`_PHASE_ORDER`/审查区/文案·CB-05）
- ✅ prompt 优化工程（OPTIMIZE_TEMPLATE + chip 两行 + 中文化·5.215-5.219）
- ✅ 指代标注 `resolveCoref`（5.212）+ Bug5 折叠胶囊展开（5.224）

### 数据层（数据识别 · grounding）
- ✅ **数据识别 visible bug 修**（眼睛关的点层仍可用·`pickVisiblePointLayer`/`buildContext` 去 visible 过滤·**5.228·本次**）
- ✅ Layer Manifest 字段识别（`getFieldCard` Promise 缓存 + 全字段值域·5.211/5.223）
- ✅ Flash 全字段值域识别（`buildContext` 数据摘要·categorical/数值/时间·5.223）
- ✅ EMC 组统一（`ensure_zone` `_adoptToolboxResult`·5.223）
- ✅ Layers 组卡数=0 根治（`_adoptToolboxResult` parentId·5.221）
- ✅ density 红色大面积修 + 全局中文化（5.220）

### 路由层（编排 · 计划→执行）
- ✅ `runTemplatePath` 单技能快路径（0 agent 轮·5.210）
- ✅ `runChainPath` 多步链（0 LLM 中间轮·治 C3 超时·5.210）
- ✅ 模型路由（flash 默认 + 简单任务跳 diagnose·5.222）
- ✅ density 视角默认（2D/3D 读 pitch·5.222）
- ✅ E1 多步链 + E3 partial 出口（渲染失败层不计产出·5.210/5.209）

### 质量层（诚实 · 防假完成）
- ✅ 代码诚实门保留（`_verifyClaims`/`_driftRe`/对账/F3·确定性·CB-05 去审查后仍守）
- ✅ 空答案检测（工具产出但结论过短→补引导·CB-05）
- ✅ KDE「情绪地形」去 3D 统一 2D 彩虹（5.225）

---

## 待修（欠什么）

| 项 | 说明 | 来源 |
|----|------|------|
| ⬜ L3 panel_source 全核查 | 13 工具·density 完整·其余 28 项（layer/boundary/as/keep 等通用参数·非色板核心） | CB-04 |
| ⬜ T4 胶囊矛盾 | 无 strategy 不显"齐全" + 值层面缺口回写 diagnose | backlog |
| ⬜ T5 对比 C 键 | 批4 Swipe 入口收敛 + 无焦点提示 + 双屏标题 | backlog |
| ⬜ T6 飞轮断言三件套 | 答案产出/落图/切题校验（非只信号） | backlog |
| ⬜ ⑥ 摘要完整 ①②③ | method/plan 采集（diagnose 增字段回传） | backlog |

---

## 时序（5.203→5.228 · 详 [revision-log §5](revision-log.md#L226)）

| 版本 | 修复 | CB |
|------|------|:--:|
| **5.229** | **CB-06 ReAct 超时根治**（while-loop 7 策略·防+兜·不丢图） | CB-06 |
| 5.228 | 数据识别 visible bug（眼睛关的点层仍可用） | — |
| 5.227 | 去 LLM 审查 + 删除符号四层根治 | CB-05 |
| 5.226 | density 契约整改 L1+L2+L3（tool_contracts 单一源） | CB-04 |
| 5.225 | KDE 去 3D 统一 2D 彩虹 | — |
| 5.224 | Bug5 折叠胶囊展开 | — |
| 5.223 | Flash 全字段值域 + EMC 组统一 | — |
| 5.222 | Bug3 删除符号初修 + density 视角默认 | — |
| 5.221 | Layers 组卡数=0 + 能力 hint | — |
| 5.220 | density 红色修 + 中文化 | — |
| 5.215-219 | prompt 优化 + chip 两行 + 优化键 | — |
| 5.210 | E1 多步链 runChainPath + E3 partial | — |
| 5.203 | T1 seam 修 + UI/排版（backlog 已修项） | — |

---

## 指针
- **详时序**：[revision-log §5 最新动态](revision-log.md#L226)（5.x 倒序·最新在顶）
- **评估决策**：[cb-journal](catch-ball/cb-journal.md)（CB 倒序·CB-05/CB-04 在顶）+ [KNOWLEDGE](catch-ball/KNOWLEDGE.md)（跨轮蒸馏）
- **单一契约源**：[`ai_qa/tool_contracts.py`](../ai_qa/tool_contracts.py) + [`tests/validate_skill_params.py`](../tests/validate_skill_params.py)
- **最高纪律**：CLAUDE.md 第 5 条 + AGENTS.md 铁律 11（EMC 复用 Toolbox 参数面板·ForAI=dialog 镜像）
- **红线**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema（改前先扩 eval·每次一处）
