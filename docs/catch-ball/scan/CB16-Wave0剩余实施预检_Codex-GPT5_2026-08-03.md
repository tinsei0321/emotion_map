# CB-16 Wave 0 剩余实施预检（Codex 第三方独立评估）

> **评估方**：Codex（GPT-5，第三方独立评估小组）  
> **评估时间**：2026-08-03 | **分支**：`fix/emc-buglog` @ `4369df2`  
> **对象**：Wave 0 三 bug 修复（f84b3ae）+ 本轮实施预告（① 触发词表镜像 ② 前端卡片渲染）  
> **方法**：读 f84b3ae diff + 运行级验证（修复三例）+ 前端复用点核验（renderAnswer/{{show:}}/token）+ 接线状态检查  
> **结论先行**：**三 bug 修复确认（qualifier/更新词/体检 domain 正确落地）**；**① 触发词镜像 agree + 2 补充**（须镜像 UI 语境排除表·同步守卫校验双份）；**② 卡片渲染 agree + 1 个关键缺口**（`build_outlet_schema` 目前**无前端接线调用点**——本轮若只做 UI 提示 + 渲染器，MVP 无卡可渲染；需明确后端调用 + schema 运输机制）

---

## 一、三 bug 修复确认（f84b3ae）

| Bug | 修复 | 判定 |
|---|:---|:---:|
| qualifier 后缀解析 | `build_outlet_schema.py` `_re.split(r'\s*(?:降序\|占比\|排序\|负数\|正数\|TOP\d+)', emc_expr)[0]`——去限定词后取主字段 | **OK**（与我上一轮建议一致） |
| "更新"词过宽 | `_UI_CONTEXT_WORDS = ('更新图层','更新时间','更新样式','刷新','重新加载')`——触发匹配前从问句剥离 UI 语境 | **OK**（"帮我更新图层"→ 剥离后无接口词 → 不出卡） |
| 体检 domain 不触发 | `urban_checkup_outlets.py` DOMAIN `urban_checkup`→`urban_governance`（诊断卡 domain_lens 枚举无 checkup·glm 最小改动） | **OK**（语义近似·S6 可触发） |
| 回归测试 | +3 例（qualifier/更新图层负测/体检命中）·10 passed·全量 242 | **OK** |

## 二、实施预告①：条件触发词表镜像（emc-patterns.js）

| 预检点 | 判定 | 要点 |
|---|:---:|---|
| 放 emc-patterns.js 末尾 | **agree** | 与 SEARCH_KW/REGION_KW 同构（文件尾部已有同类词表）·符合既有模式 |
| 同步守卫（validate_outlet_trigger_sync.py） | **agree** | 防漂移——项目已有 field_dict_sync 先例（前后端词表漂移教训） |
| "仅 UI 提示不改控制流" | **partial** | UI 提示合理（告知用户将出行业卡）；**但需镜像完整判定**——见下 |

**2 个补充**：

1. **镜像必须含 UI 语境排除表**：后端 `_UI_CONTEXT_WORDS`（f84b3ae 新增）决定"更新图层"不出卡——前端若只镜像 8 词不镜像排除表 → "更新图层"会显示"即将生成行业出口卡片"提示但后端不出卡（**提示与行为不一致**）；建议镜像为 `OUTLET_TRIGGER_KW`（8 词）+ `OUTLET_UI_EXCLUDE_KW`（5 词·与后端同表）；
2. **同步守卫校验双份**：`validate_outlet_trigger_sync.py` 应同时比对 8 词 + 5 排除词（不是只比对 8 词）——防排除表单向漂移。

## 三、实施预告②：前端 outlet-card 渲染

| 预检点 | 判定 | 要点 |
|---|:---:|---|
| 纯模板函数 | **agree** | 分层正确（数字后端算·前端只摆）·数据全来自后端 JSON ✓ |
| 缺失灰色 + 引用块 | **agree** | tokens.css 有 gray 系列 + EMC dark scope 已覆写 `--geojson-color-*`（`ai_qa.css:7`）→ 卡片用 `var()` 随主题 ✓；引用块走 markdown 既有样式 ✓ |
| {{show:}} 复用 | **agree** | `renderAnswer`（`panel.js:1437`）的 `panel.js:454` 正则处理 `{{show:/focus:/inspect:}}` → 卡片若经 renderAnswer 渲染自动得按钮 ✓ |

**1 个关键缺口（本轮实施必须明确）**：

- **`build_outlet_schema` 无前端接线调用点**——`rg` 确认 harness.js/panel.js/api.js/router.py 均无调用；当前只有单元测试直调；
- 本轮若只做"UI 提示 + 渲染器"，MVP 演示**无卡可渲染**（后端没在流程里出卡·schema 没有 transport 到前端）；
- **建议明确**（至少一项本轮落地）：
  a) **后端接线**：finalStep 完成后调 `build_outlet_schema`（条件触发·纯增量不碰承重路径）；
  b) **schema 运输**：卡 JSON 随 answer SSE 附加（或 trace 字段 `outlet_card`）→ 前端 `renderOutletCard(card)` 消费；
  c) **UI 提示与后端触发同源**：提示判定也用后端结果（卡存在才提示·或提示仅基于 OUTLET_TRIGGER_KW 且与后端一致）。

## 四、结论

- **三 bug 修复：通过**（qualifier/更新词/体检 domain 正确·回归测试补齐）；
- **① 触发词镜像：agree + 2 补充**（镜像排除表·守卫校验双份）；
- **② 卡片渲染：agree + 1 缺口**（后端接线 + schema transport 需明确——否则本轮渲染器无数据源）；
- **建议**：本轮实施 = 触发词镜像（含排除表）+ 渲染器 + **最小后端接线（finalStep 后条件调用 + SSE/trace 附加卡 JSON）**——三件一起才构成"提示 → 出卡 → 渲染"闭环。

---

*本报告为 Codex 组独立预检；修复经 f84b3ae diff + 运行级三例验证，前端复用点经 `panel.js:454/1437`、`ai_qa.css:7-26` 核验，接线状态经全前端 rg 确认。*
