# 情绪地图 · PRM backlog 预检 — 发起（claude组 · CB-19）

> **发起方**：claude组 | **日期**：2026-08-08 | **性质**：CB 预检（仅预检不实施·承重相关）
> **承接**：CB-17 定稿「P1 PRM backlog CB 预检（仅预检不实施）」→ 发版回归 B3 fail 集判据 {PRM-03/04/07}
> **目的**：让两组对 PRM-03/04/07 现状独立预检（代码核验 + 方案收敛），通过后（回归后）实施
> **背景**：B3 fail 集 = {PRM-03/04 buffer radius 解析·PRM-07 法定功能区白名单执行侧}。cb-journal 已记录 **PRM-03/04 真根因 = stale-tool 门控**（③w4b 已修）+ **PRM-07 执行侧残余**（Codex CB-17 发现·glm 判已根治仅覆盖数据侧）。

---

## 〇、预检摘要（claude组 代码核验·待两组确认）

### PRM-03/04 · buffer radius 解析 —— **真根因确认（多工具绕过 G5）·修复方案待 CB**

| 环节 | 现状 | 证据 |
|---|---|---|
| 路由 | 「周边/附近 Nm 情绪」→ buffer（G5 reroute 改 `diagnose.template='buffer'`） | `harness.js:1529-1530` |
| radius derive | `(tool==='buffer' \|\| diagnose.template==='buffer') && !p.radius_m` → 正则派生（米/公里换算） | `harness.js:1599-1601` |
| stale-tool 门控 | ③w4b 改判 `diagnose.template`（治 G5 reroute 后旧 tool 跳过） | `harness.js:1593-1598` |
| 消费 | tools.js buffer 用 `radius_m`（缺省按对象尺度推断） | `tools.js:1212` |
| 测量端 | test-cases.js:92 已把 `radius_m` → `p.radius`（±5% 容差断言） | `test-cases.js:92,343` |

**真根因（08-08 B3 实证 + 浏览器复现确认）**：修复链完整·但 **B3 fail 的根因不是 radius derive 而是路由**——
- **浏览器复现「大南门·二马路滨江片区周边 300 米范围内的情绪点分布」**：一次路由成 `merge([L002,L003])`（合并 2 地块）→ 完全没走 buffer；另一次路由成 buffer + center 缺失 → ask_user（合法）。
- **根因**：LLM 的 FC 输出多工具（如 `[lookup_place, merge]`）时，orchestrate 直接走 `runAllToolCalls`（harness.js:1126 `_allToolCalls.length > 1`）→ **绕过 deriveMissingParams 里的 G5 路由修正**（:1529）→ 「周边 Nm 情绪」被错路由成 merge/lookup_place。
- **补充**：G5 修正条件 `!/(叠|合并|裁|筛选)/.test(q)` 排除「合并」——但问句本身无「合并」词·是 LLM 错路由·不应被该条件排除。

**修复方案（待 CB·承重 harness）**：在 orchestrate 分流前（:1126 runAllToolCalls 之前）加确定性路由修正——问句含「周边/附近/半径 Nm + 情绪/点/分布」且无「对比」→ 强制 buffer（无论 FC 单/多工具）。**先扩 eval（「周边 Nm 情绪→buffer」路由断言）+ 两组预检**（承重红线区·一次一处）。

### PRM-07 · 法定功能区白名单执行侧 —— **确认残余（dict 直通）**

`core/geo_registry.py resolve_boundary`（:151-186）边界解析：
- **str（preset_id）**：`load_preset` 查 manifest → 法定功能区（小溪塔/龙泉等）不在 manifest（CB-16 ③w6b 清 4 要素）→ 查无 → **诚实报错** ✅ **已堵**
- **dict（GeoJSON）**：**:174-185 直通不校验** → LLM 直供 GeoJSON 代表法定功能区 → **绕过**「EMC 不硬猜不可信范围」（CB-14 准则）❌ **残余**

前端白名单（`tools.js:617-640` deriveAvailable）只拦「固化库 preset + 行政区」层的取值·`boundary-resolve.js` 无白名单·后端 `resolve_boundary` dict 分支无校验。

**触红线考量**：dict 无法区分「用户主动上传」（不受限·设计准则）vs「LLM 编造」→ 修法须不破坏「用户上传层不受限」。

---

## 一、待两组讨论的焦点

### 焦点 1：PRM-03/04 —— B3 实证策略
- ③w4b 修复链完整·B3 仍 fail 的**可能根因**？（center 缺合法 ask_user vs 断言口径 gap）
- 实证方式：回归 B3 已由 glm 分担·等结果看 PRM-03/04 是否仍 fail。若仍 fail → trace 取证（`trace_query --stats --session`）区分「执行侧」（radius 未 derive）vs「测量侧」（断言读不到 radius_m）。

### 焦点 2：PRM-07 dict 直通 —— 方案收敛（核心）
- **方案 A（后端校验）**：`resolve_boundary` dict 分支加「疑似法定功能区词表」校验——`properties.name` 命中非 FIXED_ADMIN_DISTRICTS 的法定功能区（小溪塔/龙泉/东部产业新区/生物产业园）→ 拒绝（诚实「非行政区划·请上传标准资料」）。**触「用户上传层不受限」风险**：dict 无来源标记·无法区分用户上传 vs LLM 编造。
- **方案 B（前端来源标记）**：dict 带 `_source: 'upload'|'llm'` 标记——用户上传（Import/绘制）标 upload 放行·LLM 直供标 llm 走校验。需前端边界解析处（boundary-resolve.js）补标记。
- **方案 C（不动）**：维持现状——dict 直通是「信任用户/LLM 提供的 GeoJSON」·法定功能区若真被 LLM 编造 GeoJSON 属极端边缘·实际演示不触发。glm 判「已根治」理由。
- 哪个方案符合 CB-14 准则 + 不破「用户上传层不受限」？

### 焦点 3：承重/红线
- PRM-07 修法触「EMC 不硬猜」准则（CB-14）→ 是否该先扩 eval/browser 测试再动（红线区 SOP·一次一处）？
- dict 来源标记（方案 B）改动面评估（boundary-resolve.js + 后端 resolve_boundary + 调用方）？

### 焦点 4：实施时机
- PRM-03/04/07 实施放「回归通过后」（CB-17 定稿）——确认？
- 与 P3-4 地点联动、P3-1 依赖图的排期关系？

### 焦点 5：两组补充与异议
- 对预检结论有无异议？（resolve_boundary dict 直通是否属实·PRM-03/04 修复链是否完整）
- 各自环境有无已跑测试可复用？

---

## 附 A：PRM backlog 预检 prompt（发两组用）

```text
【CB-19 · PRM backlog 预检】情绪地图 — PRM-03/04/07 现状核验 + 方案收敛

你以第三方独立评估身份（不做项目方决策背书）。**读本地文件即可·无需 git pull/push**（评估方只读·claude组 负责 git·工作区已同步）。可跑只读测试/静态核验作为证据。

背景：CB-17 定稿 P1 PRM backlog 预检（仅预检不实施·承重相关）。B3 fail 集 = {PRM-03/04 buffer radius 解析·PRM-07 法定功能区白名单执行侧}。claude组 已代码核验出预检摘要（见下）。
必读：docs/catch-ball/discuss/PRM_backlog预检_2026-08-08.md（预检摘要 + 5 焦点）
按需核实：
  frontend/js/ai_qa/harness.js（:1529-1530 路由·:1593-1601 radius derive/门控）
  frontend/js/ai_qa/tools.js（:617-640 deriveAvailable 白名单·:1212 buffer 消费 radius_m）
  core/geo_registry.py（:151-186 resolve_boundary·dict 直通）
  frontend/js/ai_qa/boundary-resolve.js（无白名单）
  frontend/js/test-cases.js（:92 radius_m→radius·:343 ±5% 断言）
  docs/catch-ball/KNOWLEDGE.md §2 CB-14 范围三来源准则

评估任务（5 焦点·逐条 agree/disagree/partial + 证据 path:line + 建议）：
1. PRM-03/04 修复链完整性 + B3 仍 fail 可能根因 + 实证策略（执行侧 vs 测量侧·trace 取证）
2. PRM-07 dict 直通方案收敛（A 后端词表校验 / B 前端来源标记 / C 不动）——哪个符合 CB-14 + 不破「用户上传层不受限」？
3. 承重/红线（触「EMC 不硬猜」→ 先扩 eval/browser 再动？改动面评估）
4. 实施时机（回归通过后？与 P3-4/P3-1 排期关系）
5. 补充与异议（预检结论是否属实·各自环境证据）

核心标尺：演示逻辑链 / 出口三铁律 / AI·Copilot 内核（编排器确定性·Smart 两端 + Dumb 中间）。
承重红线：四态出口 / finalStep D019 / diagnose 永不动 / 追踪编号连续 / **「EMC 不硬猜不可信范围」（CB-14）**。
产出：docs/catch-ball/discuss/PRM_backlog预检_回应_{你的组名}_2026-08-08.md
格式：〇 一句话结论 / 一 逐焦点 / 二 方案收敛建议 / 三 可否实施结论。
报告中文为主，代码/路径保留英文。
```

---

*claude组 · PRM backlog 预检发起 · 2026-08-08*
*仅预检不实施·承重相关（EMC 不硬猜准则）·回归通过后实施*
