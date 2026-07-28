# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。上周（07-20~07-26）见 [todo-archive/2026-07-20_2026-07-26.md](todo-archive/2026-07-20_2026-07-26.md)。
> 📝 详版历史 = [revision-log §5](revision-log.md#L226)（永久审计底·5.x 逐条）·本文件只记当前 + 计划。

---

## 📅 2026-07-29（明日计划·**开 plan**）

### 🔄 测试飞轮更新 + 9 模块测试围绕新飞轮

- **用户主导**：根据 5.242 修复后的 EMC 架构（三阶段 diagnose + **数据感知选型** + 追问胶囊 + 质量防线 + Pro 动态 chain）**更新测试飞轮机制 + 模拟测试内容**。
- **飞轮核心**：覆盖「**数据×问句**」组合测（不只关键词）——DeepSeek 评估报告 §十一（缺失测试 7 项）+ §九 P2 建议（S10-S15）可参考。
- **开 plan**（用户明示）。
- 参考：[DeepSeek EVAL_REPORT_unified_2026-07-28](docs/catch-ball/emc-arch-deepdive/EVAL_REPORT_unified_2026-07-28.md)（8 bug·P0 已修·P1 部分修·P2 待续）+ [emc-fix-progress §一](emc-fix-progress.md)（9 模块矩阵）。

---

## 📅 2026-07-28（今日·**9 模块验证暴露链路缺陷 → 系统性修复**·commit+push）

### ✅ 5.242 EMC 链路系统性修复（选型数据感知 + 9 bug·融合 DeepSeek 评估·revision-log 5.242）

- 用户验证 9 模块后报「剪裁西陵区」失败 + 「无变化」+ 「基本功能丧失」。
- **根因**（DeepSeek EVAL 确认）：`select_candidates(question, None)` context 硬 None → 0LLM 选型**数据盲**（不知点/面）→ 误路由 + `TOOL_GEOMETRY_REQUIRE['clip']` 误设 None（Phase A 漏设）。
- **修复 11 项**：S1 数据感知（layer_meta 端到端）+ clip 几何表修正 + stale multi 移除 + 剪裁歧义词 + 空候选→request_upload + S3-S9（clip 恢复/ensure_zone/F_008/capsule intent/正则统一/chain hasRows/FILL_CARD 兜底）。
- **验证**：pytest **219 passed** 零回归 + 实测（剪裁+polygon→extract / 无点→request_upload）+ serve 干净。
- **教训**：选型不能脱离数据上下文（question-only = 架构债）+ clip 几何表 Phase A 漏设 + 改 Python 后须重启 serve。

### ✅ 5.241 selector trigger 补 + 诊断「无变化」根因（uvicorn 需重启）

- 用户报「无变化」→ 诊断主因 = serve.py 未重启（uvicorn 无 --reload·旧 Python 未载入）。
- selector 补「剪裁/裁剪」trigger（5.241 初版·5.242 修正为歧义词）。

---

## 📅 2026-07-27（CB-09 9 模块全落地 + 收尾）

### 🎯 CB-09 EMC 架构重构 · 9 模块实施 9/9 全 ✅（5.231-5.240）

**新架构全景**（三阶段 diagnose + 胶囊 + 防线 + 动态 chain）：

| 路径 | 改造前 | 改造后 | 模块/版本 |
|------|:---:|:---:|------|
| 单/少候选（~80%） | diagnose 25-45s | **<5s** | 一 D006 Phase B（5.236）·极瘦填卡 45.8KB→1.85KB |
| 复合（~20%） | 大 prompt 25-45s | **5-10s** | 一 D009 + 二 D012 Phase C（5.237）·Pro 产 chain→runChainPath |
| finalStep | 25-50s | **<1s** | 四 D019（5.233）·17KB→1.86KB |
| 追问胶囊 | 静态 NL 15-20s | **动态 L1 <2s / L2 5-8s** | 四 D020-D021（5.234）·runCapsule 跳 Flash |
| 选型 | Flash 13 选 1 | **0LLM 规则 97%** | 九 D035-D038 Phase A（5.235）·select_candidates |
| 质量 | LLM 审查 5-15s | **代码防线 <20ms** | 五 D023（5.232）·applyQualityDefense |
| 契约 | 四处分裂 | **tool_contracts 单一源** | 六 D025-D026（5.226/5.240）·全派生 |
| Toolbox 接口 | ForAI 自带默认 | **dialog 镜像 + CI** | 七 D027-D029（5.226/5.238）·L3 全Resolved |
| CPD | 独立对话框（设计） | **胶囊实现 D031 + 偏好埋点** | 八 D030-D034（5.239）·不另造重复 |
| 执行层 | 矛盾（谎报/锚定） | **observation 自述 + 镜像** | 三 D016-D018（5.231） |

**9 模块实施 9/9 ✅**（D001-D040 全落地）·详 [revision-log §5](revision-log.md#L226)（5.231-5.240 逐条）+ [emc-fix-progress §一 矩阵](emc-fix-progress.md)。
**验证**：pytest **214 passed**+5 skipped（零回归）+ serve/boot 干净。**待用户飞轮齐验**（明日）。

### ✅ 收尾（今日）

- [emc-fix-progress.md](emc-fix-progress.md) §一 矩阵 9/9 + §三 backlog 清零（仅剩 T4-T6/⑥·非 9 模块决策）+ §四 时序到 5.240。
- todo/revision-log 按新架构清理：旧 CB-09 轮次详条留 revision-log §5（审计底）·todo 精简为新架构视图；上周日段归档 [todo-archive/2026-07-20_2026-07-26.md](todo-archive/2026-07-20_2026-07-26.md)。

### 🔄 遗留（待用户）

- **明早办公室大讨论**（用户主持·议题未告知）。
- **KDE 去 3D 连带设计**（备查·非大讨论主题）：「情绪地形」命名 / 「总体情况」栏仅剩 1 卡 / EMC `generateTerrainForAI` 仍 3D / Grid 3D 收口。
- **9 模块浏览器齐验**（明日飞轮就绪后·用户约定）。
- **按钮文案**：「生成 2D 热力图」（带空格）vs 用户原话「生成2D热力图」·待定。
