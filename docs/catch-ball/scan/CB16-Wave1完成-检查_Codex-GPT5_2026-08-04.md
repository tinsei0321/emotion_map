# CB-16 Wave 1（macro 出口）实施后检查（Codex 第三方）

> **评估方**：Codex（GPT-5 · 第三方独立评估组）  
> **时间**：2026-08-04 | **分支**：`fix/emc-buglog` @ `0c7a783`（Wave 1 commit `97cf232`）  
> **方法**：commit diff 逐行核验 + 当前代码追查（工具执行路径全枚举）+ 单元测试实跑 + E2E 可执行性评估  
> **范围**：只读评估 · 不改代码 · 不 commit

---

## 结论摘要（先行）

**Wave 1 通过。** 5 环节全部按两组预检反评价落地且逻辑正确；单测实测 **23 passed（15+6+2）**。  
**2 项需修（不阻塞主线功能，建议 push 前处理）：**
- **【P1】`_lastToolRows` 跨轮不重置**：模块级缓存无回合生命周期——turn1 跑过 macro zonal 后，turn2 出口问句若无工具执行，会附**陈旧 rows** 出卡（数据错误）。建议 orchestrate 入口（`harness.js:875`）重置 `_lastToolRows = null`。
- **【P2】第 4 条工具执行路径未捕获 rows**：ReAct while-loop 兜底（`harness.js:1238-1252` 直调 `TOOLS`）只捕 `layerId` 不捕 `rows`——macro 问句若走 while-loop（degraded/unknown 兜底），rows 不可达、出口卡回落图层 fc。建议 `:1252` 补同款 rows 捕获。
- **【P2 测试质量】`test_wave1_empty_rows_no_card` 名实不符**：名字"不出卡"、断言"出卡"（后端容错组装 + 前端门拦截的分工）——改名或改 docstring。

---

## 一、5 环节核验（对照预检 P1/P2 落地）

| 环节 | 落地核验 | 判定 |
|---|---|---|
| ① `_extract_emc_value` 统一收 rows/features | ✅ 顶层 dict 直取 → rows（每行当 feature.properties·Top-1）→ features（含裸 dict 归一化）——单入口防前后端漂移 | 正确 |
| ② `_lastToolRows` ×3 + 门放宽 | ✅ runTemplatePath（:559）/ runChainPath（:757）/ runAllToolCalls（:1868）三处捕获；`_maybeBuildOutletCard` rows 优先 + 门放宽「`_hasRows`（非空）或 newLayerCount>0」+ 空 rows 守卫 | 正确（**漏 while-loop 第 4 路径**·见 P2） |
| ③ DOMAIN_KW「城市体检」 | ✅ `emc-patterns.js` governance 补「城市体检」；TRIGGER_WORDS/OUTLET_TRIGGER_KW 保留「体检」——触发/domain 分离 | 正确 |
| ④ checkup_dimension scale 限定 | ✅ 四维度 prose→真实字段 + `[scale=micro/meso/meso/macro]`；字段全部 ∈ `_EMC_FIELDS` 白名单 | 正确 |
| ⑤ e2e-seam 钩子 + 测试 | ✅ `setOutletRows`/`buildOutletCardForTest` seam 直测（不赌博 LLM）+ 单测 4 新增 + test_outlet_macro.py 两场景 | 正确 |

---

## 二、七问逐答

### 1. `_extract_emc_value` 顺序正确，无破坏既有用例

- 顺序：顶层 dict → rows → features——macro 权威 rows 优先，features-only 结果走原路径，归一化兼容裸 dict。既有 features 用例无回归（单测 15 passed 实测佐证）。✓

### 2. `_lastToolRows` ×3 覆盖主路径，**遗漏 while-loop 第 4 路径（P2）**

- 覆盖：runTemplatePath（单技能）/ runChainPath（链）/ runAllToolCalls（多 call）——macro 问句常规全走这三条。
- **遗漏**：ReAct while-loop（`harness.js:1238-1252` 直调 `TOOLS[step.action.name]`）只捕 `r.data.layerId`，未捕 rows——degraded-FC/unknown 兜底路径下 macro rows 不可达（出口卡回落图层 fc 或不出卡）。当前 while-loop 低频（F_002 已压到 2 次/轮），P2。

### 3. 门放宽无"空卡"副作用；**发现跨轮陈旧风险（P1）**

- 空 rows 守卫 ✓（`_hasRows` 要求 `Array.isArray && length`）。
- **P1**：`_lastToolRows` 为模块级缓存、**无回合重置**——turn1 zonal（rows 入缓存）→ turn2 出口问句（无工具执行）→ 陈旧 rows 附新卡（错误数据）。修法一行：orchestrate 入口（:875）`_lastToolRows = null`。

### 4. `[scale=xxx]` 限定正确

- macro→城区填值·住房/小区/街区"需对应尺度分析"；meso→小区/街区填值·城区/住房限定——单测两个用例（macro+meso）断言全覆盖 ✓。scale 空时全槽"需对应尺度分析（当前未知）"（诚实）。

### 5. `data_base` rows 语义不误导 ✓

- N=区域单元数、note「N 个区域单元（单元评论数见 point_count 列）」、total_points=sum(point_count)——单测断言 N=2/total=500 ✓。

### 6. 「城市体检」长词触发正确

- 「健康体检/体检中心」不含「城市体检」→ 不误触 ✓；「城市体检评估」含 → 触发 ✓。
- 知晓项：无「城市」前缀的「体检维度/体检指标」问句 B 部兜底 miss，依赖 FC A 部 domain_lens——防误触优先的既定取舍，可接受。

### 7. 测试覆盖够，1 处名实不符（P2）

- 单测 4 新增（rows 取值 / scale macro / scale meso / 空 rows）+ E2E 两场景（门放宽出卡 + scale 限定）覆盖主线与边界。
- P2：`test_wave1_empty_rows_no_card` 名字"不出卡"、断言 `card is not None`（后端容错组装 + 前端门拦截分工）——改名/改 docstring。

---

## 三、端到端验证

| 项 | 结果 |
|---|---|
| `pytest test_outlet_schema + test_outlet_kb + validate_outlet_trigger_sync` | ✅ **实测 23 passed**（15+6+2·0.07s） |
| `py tests/browser/test_outlet_macro.py` | ⚠️ **本环境无法执行**：`emc_helpers` 用 `py` 启动 serve，本机 `py` 是 WindowsApps 坏占位符（已知环境异常）——非测试本身问题；claude组 commit 记录两场景全过，测试断言与实现逐行核对一致 |
| 浏览器「各行政区更新优先级排序」出卡 | 待 claude组/用户环境复验（依赖 serve + LLM 路由·同环境限制） |

---

## 四、判定

- **Wave 1 通过**：5 环节正确、单测全绿、预检 P1（scale 限定）与 claude组 P1×3 全部落地。
- **P1（1 项）**：`_lastToolRows` 跨轮重置（orchestrate 入口一行）——防陈旧 rows 附卡。
- **P2（2 项）**：while-loop 第 4 路径 rows 捕获；`test_wave1_empty_rows_no_card` 改名。
- **边界合规**：未触碰 diagnose/orchestrate 主循环/ChatRequest；DOMAIN_KW 非 TRIGGER_WORDS（validate 同步不受影响）；place_name 精确源留 Wave 2。

---

*本报告为 Codex 组独立评估；单测实测 + commit diff 逐行核验 + 工具执行路径全枚举，E2E 受本机 py 占位符环境限制未能重跑（非测试缺陷），未参考其他组报告。*
