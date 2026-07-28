# v2 实施问题与风险记录

> **日期**：2026-07-28  
> **范围**：v2 FC 改良混合架构实施过程中的问题、修复、残留风险

---

## 一、已发现并修复的问题（12 项）

### 数据流兼容性（7 项）

| # | 严重度 | 问题 | 修复 | commit |
|:---:|:---:|------|------|:---:|
| 1 | HIGH | FC 返回 tool name（zonal_stats）而非 skill name（zonal）→ SKILL_DEFS 查不到 → fast path 失效 | `_TOOL_TO_SKILL` 反映射 | 5.245 |
| 2 | HIGH | FC diagnose 未走 normalizeCard → template 未归一化 → 命中率遥测污染 | `_normalizeFcDiagnose` 补全 | 5.245 |
| 3 | HIGH | FC diagnose 缺 data_plan/domain_lens/scale/outlet → 下游消费者读到 undefined | `_normalizeFcDiagnose` 补默认值 | 5.245 |
| 4 | MED | deriveDiagnoseMethod 用 tool name → method=[] for zonal/compare | `_normalizeFcDiagnose` 产 `method:[toolName()]` | 5.245 |
| 5 | MED | FC 硬编码 intent='gis_operation' → 情绪分析问题被误标为纯操作 | `_EMOTION_TOOLS` 按工具推导 intent | 5.245 |
| 6 | LOW | plans content 经常空 → CPD 胶囊不出现 | 追问胶囊由 finalStep 产出（已有机制·非阻塞） | — |
| 7 | LOW | ctx.plans 空时不覆盖 → 可能复用上轮 stale plans | 后续优化（数据变化检测已覆盖大部分场景） | — |

### UI 状态兼容性（5 项）

| # | 严重度 | 问题 | 修复 | commit |
|:---:|:---:|------|------|:---:|
| 5a | **BLOCKING** | fcDiagnoseStep 无 ctx.signal → 用户无法取消 FC 诊断 | AbortController + ctx.signal 联动 | 5.245 |
| 5b | **BLOCKING** | fcDiagnoseStep 无 timeout → 后端挂起时 dock 永转 | 45s setTimeout + clearTimeout | 5.245 |
| 5c | COSMETIC | FC 不更新 _callCount/_lastUsage → 用量统计少算 | 手动更新 _emcLastUsage | 5.245 |
| UI-1 | COSMETIC | onReason('Function Calling 诊断中…') 写入思考面板和历史 | 后续优化（改用 onStatus hook 或移除） | — |
| UI-2 | COSMETIC | FC diagnose 卡片缺 domain/scale chips → 显示不完整 | _normalizeFcDiagnose 已补全字段（渲染应改善） | 5.245 |

---

## 二、残留风险（待后续处理）

| # | 风险 | 等级 | 缓解 | 时机 |
|:---:|------|:---:|------|:---:|
| R1 | DeepSeek V4 FC 复杂场景稳定性（社区报告 V3 时空响应/循环） | 🟡 | fallback 降级旧 SSE + 45s timeout | 浏览器测试 |
| R2 | plans content 暂空（LLM FC 模式倾向不产 content） | 🟢 | 追问胶囊由 finalStep 产出·不阻塞 | 后续 prompt 优化 |
| R3 | "按行政区聚合归因"类问题 LLM 未选工具 | 🟡 | 降级旧 SSE diagnose | prompt 优化 |
| R4 | Phase 4 清理未做（旧 v1 代码保留） | 🟢 | D053 过渡期保留 | v2 稳定后 |
| R5 | strict 实测不强制（enum 外值不被 API 拒绝） | 🟡 | D062 代码层 validate_tool_call 兜底 | 已缓解 |
| R6 | UI-1 onReason 占位符污染思考面板 | 🟢 | 后续改用专用 hook | 优化期 |

---

## 三、实施进度

| Phase | 内容 | 状态 | commit |
|:---:|------|:---:|:---:|
| 0 | 分支同步（git pull 5.235-5.242） | ✅ | — |
| 1 | 后端 FC 基础设施 | ✅ | 5.243 |
| 2 | 前端 fcDiagnoseStep + 编排器适配 | ✅ | 5.243 |
| 3 | CPD plans→胶囊 | ✅ | 5.244 |
| — | prompt 优化（plans 格式） | ✅ | 5.244b |
| — | 兼容性修复（7 数据流 + 5 UI） | ✅ | 5.245 |
| 4 | 清理废弃 v1 代码 | ⬜ | v2 稳定后 |

---

## 四、验证状态

| 验证项 | 结果 |
|------|:---:|
| contracts_to_tools_schema 13 工具 | ✅ |
| chat_with_tools DeepSeek V4 FC | ✅ |
| validate_tool_call 合法/非法参数 | ✅ |
| router fc_diagnose HTTP 200 | ✅ |
| density/clip/rank FC 选型正确 | ✅ |
| compare_regions→compare 映射 | ✅ |
| zonal_stats→zonal 映射 | ✅ |
| 前端 fcDiagnoseStep 加载 | ✅ |
| signal + timeout（用户取消/挂起） | ✅ |
| normalizeCard 等价结构补全 | ✅ |
| **浏览器端到端出图** | ⬜ 待用户测试 |

---

*最后更新：2026-07-28 · v2 实施问题与风险记录*
