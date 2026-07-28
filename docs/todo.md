# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。
> 📝 详版历史 = [revision-log §5](revision-log.md#L226)（永久审计底）·本文件只记当前 + 计划。
> 📌 **架构版本**：v1（三阶段 5.231-5.242）→ **v2（单次 LLM + FC·5.243-5.245b·第三方实施）** → **v3（v2 做对·5.246-657c2e3·GLM 修复）** → 当前 **v3.1**（reg.filter 崩溃修复 + SCAN P1）。

---

## 📅 2026-07-28（今日·**v2→v3 架构转型 + 修复**·commit+push）

### 🎯 架构转型：v1 三阶段 → v2 单次 LLM + Function Calling → v3 做对

用户 + DeepSeek 产出 v2 改良混合架构（[SUMMARY](docs/catch-ball/emc-arch-deepdive/SUMMARY.md)·61 决策 D041-D068）·废弃 v1 三阶段 + 信息卡·改用 DeepSeek V4 原生 function calling + 契约 Schema。第三方实施（5.243-5.245b）→ GLM 审查发现 3 CRITICAL + 6 HIGH → v3 修复（7858d5a）→ 用户实测发现 `reg.filter` 崩溃 → v3.1 修复（657c2e3）。

### ✅ v3.1 reg.filter 崩溃修复 + SCAN P1 边界（revision-log 5.246·commit 657c2e3）

- **根因（治用户全部 4 问题）**：`formatRegistry()` 返**字符串**·`applyQualityDefense` + `_composeDegradedConclusion` 对其调 `.filter()` → 类型错误崩溃 → `[请求失败]` + 胶囊消失 + dock 永转（感知 70s+）。
- **修复**：`getArtifacts()` 替代（返数组）。+ SCAN P1：zonal_stats 补 _NEEDS_POINT / _parsePlans strip domain_lens 前缀 / _fc_fixes 传回 / domain_lens 默认返 []。
- **验证**：pytest **221 passed**+3 skipped 零回归 + serve/boot 干净。**待浏览器验证**：重启 serve + 硬刷 → 「分析情绪热度」→ FC → 出图 → applyQualityDefense **不崩** → 胶囊显示 → ~10s。

### ✅ v3 修复第三方 v2 的 3 CRITICAL + 4 HIGH（commit 7858d5a）

- **C1**：`chat_with_tools_fallback`（DeepSeek→Ark→讯飞 provider 链·治 FC 单点故障）。
- **C2**：执行前 data gate（`_normalizeFcDiagnose` 检查 layer_meta.has_point + _NEEDS_POINT→request_upload·治 5.242 数据感知回归）。
- **C3**：domain_lens A+B 混合（`_deriveDomainLens`：先 parse FC content `[domain_lens:xxx]`→空则关键词推导）。
- **H2**：`_PARAM_RANGES`（radius/cell_size/top_n 等 minimum/maximum）。**H5**：timeout 45s→20s。**H6**：删前端 `_validateFcParams`·后端 router 调 `validate_tool_call`。

### ✅ 第三方 v2 实施（5.243-5.245b·commit 810139c→143f3da）

- **5.243** v2 FC 后端+前端（contracts_to_tools_schema + chat_with_tools + fcDiagnoseStep + D062 校验 + D065 数据变化检测）。
- **5.244** v2 CPD plans→胶囊（D068 _plansToCapsules）。
- **5.245** FC diagnose 兼容性修复（7 项：tool→skill 映射 / normalizeCard 补全 / intent 推导 / signal+timeout / usage 统计）。

### ✅ v1 三阶段实施（5.231-5.242·已被 v2 取代·代码保留过渡期）

- 5.231-5.240：9 模块 v1 三阶段（select_candidates + FILL_CARD + PLAN + dispatch）。
- 5.241-5.242：selector trigger + 数据感知修复。
- **v2 取代**：v1 diagnose 管线（select_candidates / FILL_CARD / PLAN / dispatch）被 FC 取代·但代码保留（Phase 4 清理待 v3 稳定后）。

### 🔄 遗留（待处理）

- **浏览器验证**：重启 serve + 硬刷 → 测「分析情绪热度」+「剪裁西陵区」→ 确认 reg.filter 不崩 + 胶囊显示 + ~10s 速度。
- **Phase 4 清理**：v3 稳定后删 v1 diagnose 管线（select_candidates / FILL_CARD / PLAN / dispatch / triggers·~500 行）。
- **测试飞轮**：围绕 v2/v3 FC 架构更新飞轮机制 + 模拟测试内容（开 plan）。
- **FC 稳定性**：DeepSeek V4 FC 复杂场景（R1 社区报告空响应/循环）·fallback 降级。
- **plans[] 常空**（R2）：LLM FC 模式倾向不产 content → CPD plans 设计名存实亡·finalStep 胶囊兜底。
