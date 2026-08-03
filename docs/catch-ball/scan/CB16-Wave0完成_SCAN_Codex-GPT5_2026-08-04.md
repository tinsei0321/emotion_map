# CB-16 Wave 0 完整链路实施后检查 · SCAN（Codex 第三方独立评估）

> **评估方**：Codex（GPT-5，第三方独立评估小组）  
> **评估时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `bd3ccce`  
> **对象**：5 环节（后端端点/前端接线/渲染/词表镜像/同步守卫）+ 端到端验证  
> **方法**：读 5 环节实现 + TestClient 运行级验证（主用例 + 5 边界）+ 接线/分层/守卫核验  
> **结论先行**：**Wave 0 完整链路落地成立（通过）**——端点 7 要素 + 诚实标注 ✓、接线纯增量异步静默 ✓、渲染纯模板分层 ✓、词表镜像 + 排除表 + 双份守卫 ✓；主用例（S2 需求分析卡）与体检卡（checkup_satisfaction）运行级验证通过；**3 个低severity 注意点**：① hint-only 触发残余（"给我建议清单"无接口词也出卡·低）② harness 内联词表重复 emc-patterns（DRY + 守卫不覆盖）③ result 为前端传入（信任边界·演示可接受）

---

## 一、5 环节核验

| 环节 | 判定 | 证据 |
|---|:---:|---|
| ① 后端端点 | **OK** | `api/aiqa_routes.py:88-104`——`OutletCardIn{question,diagnose,result}` → `build_outlet_schema` → `{card}`；确定性·零 LLM·未命中返 `{card:None}` |
| ② 前端接线 | **OK** | `harness.js:1351-1356 + 1539-1585`——finalStep 后异步调·触发词 + UI 语境排除·`newLayerCount>0` 门·失败静默·不碰承重/四态 |
| ③ 前端渲染 | **OK** | `panel.js:283-330` `renderOutletCard` 纯模板（字段/对接任务/引用块局限/来源）·缺失灰色 `.outlet-muted`·`{{show:}}` 复用 `renderAnswer` refs；`onOutletCard`（`panel.js:1495-1498`）挂 trace |
| ④ 词表镜像 | **OK** | `emc-patterns.js:48-50`——`OUTLET_TRIGGER_KW`(8) + `OUTLET_UI_EXCLUDE_KW`(5) |
| ⑤ 同步守卫 | **OK** | `tests/validate_outlet_trigger_sync.py:43-56`——双份校验（触发词 + 排除表）·2 passed |

## 二、端到端验证（TestClient 运行级）

| 用例 | 结果 |
|---|---|
| S2 主例（"西陵区老旧小区更新需求分析"·meso·renewal） | **200 · renewal_demand**：接口标识 ✓ / 问题类型→停车难 ✓ / 需求强度→-0.32 ✓ / 需求位置→夷陵广场 ✓ / 需求类型→urban_renewal ✓ / 数据基础→1247 ✓ / limits=3（边界+place_name 粗略+规则归因）✓ / can+cannot ✓ / source=确定性组装 ✓ |
| 体检（"社会满意度调查"·macro·governance） | **200 · checkup_satisfaction**（domain 修复生效）✓ |
| 无接口词（"生成热力图"·outlet=生成图层） | **None**（真实 outlet 下不出卡）✓ |
| UI 语境（"帮我更新图层"/"刷新图层"·outlet=生成图层） | **None**（排除表生效·真实 outlet 下）✓ |
| 字段缺失（point_count=0） | 各字段"暂无数据"·不编造 ✓ |
| 提示仅触发（"给我建议清单"·outlet=建议清单·无接口词） | **renewal_demand**（hint-only 触发·见注意 1） |

## 三、5 检查项 + 3 个注意点

| 检查 | 判定 | 要点 |
|---|:---:|---|
| ① 端点契约合理（安全/边界） | **OK** | 内部 API（同 aiqa 其他端点·无鉴权·演示域）；入参结构清晰 |
| ② 接线纯增量不碰承重 | **OK** | finalStep 后·异步·失败静默·不触碰 diagnose/harness 主循环/ChatRequest |
| ③ 渲染分层正确 | **OK** | 前端纯模板（后端 JSON → 摆位·不计算·`{{show:}}` 走既有 renderAnswer） |
| ④ 词表镜像 + 排除表完整 | **OK** | 8+5 词与后端一致（守卫实测过） |
| ⑤ 守卫覆盖够 | **OK** | 触发词 + 排除表双份（2 用例）；补充建议见注意 2 |

**注意点**：

1. **hint-only 触发残余（低）**：`outlet='建议清单'` + domain/scale 匹配 + 无接口词 → 仍出卡（OUTLET_HINT +2）。真实流中 outlet 由 FC 从问句推导——"给我建议清单"类泛问可能误出更新需求卡。**建议**：hint-only 触发需叠加问句上下文（至少含领域词或 ≥1 接口词），或接受为"建议清单本身即行业输出意图"（低风险·演示可接受）。
2. **harness 内联词表重复（DRY·低）**：`harness.js:1548-1551` 内联 `_trigger`/`_uiExclude` 数组与 `emc-patterns.js` 重复——**同步守卫只查后端↔emc-patterns，不覆盖 harness 内联**（harness 漂移不会被守卫发现）。**建议**：harness 改 `import { OUTLET_TRIGGER_KW, OUTLET_UI_EXCLUDE_KW } from './emc-patterns.js'`（前端单一源）。
3. **result 为前端传入（信任边界·低）**：`result`（含 polarity_index/features）由客户端组装后 POST——本地演示可信；若未来接外部，建议后端从自身产物记录取数（防注入假数据）。当前 `source='确定性组装'` 标注已诚实（数值来自 result·来源可见）。

## 四、结论

- **Wave 0 完整链路：通过**——5 环节齐全·主用例与边界运行级验证通过·诚实标注/确定性组装/分层正确；
- **3 个低 severity 注意点**（不阻塞）：hint-only 触发残余（可接受或收紧）、harness 内联词表改 import、result 信任边界（演示可接受）；
- **浏览器端到端**：沙箱无法起 serve（网络/进程受限）——代码级接线确认（`onOutletCard` → `renderOutletCard` 链完整）；建议项目方在有网环境复验"西陵区老旧小区更新需求分析"出卡。

---

*本报告为 Codex 组独立 SCAN；端到端/边界经 TestClient 运行级验证（主例 + 5 边界·真实 outlet 口径），5 环节经代码逐行核验。*
