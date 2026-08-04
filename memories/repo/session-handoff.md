# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月04日深夜（**CB-16 ③w2~③w7 全闭环：全局优化 + 发版 backlog 收尾完成·措辞修复 + eval 标尺 + fixture 清理**）| 分支 `fix/emc-buglog` | **已与 `origin/fix/emc-buglog` 0/0 同步（0bb55df）**
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md` + `OFFICE.md`

## 当前节点：CB-16 出口抽象层 Wave 0-3 + ③z 余留 + ③w2~③w7 全部闭环（已推）

08-04 大跨轮（CB-16 出口深化全链路 + 发版准备）：
- **Wave 0-3 出口抽象层**（已闭环）：出口卡片链路 + R7 截断 + 大南门接入 + macro 出口 + place_name 双源 + 多卡 + validate CI + 可感知计算器 2a/2b + checkup P2
- **③z 余留 2b/P2**（已闭环）：可感知计算器 2b（B 类条件等式）+ checkup_satisfaction P2 + panel 渲染
- **③w2/③w3 全局优化 + backlog 收尾**（已闭环）：validate_skill_params drift 修复 + renewal 门控 + CLAUDE.md 5 行 + todo 周归档 + ADR-017~019 + 记忆 GC + B3 快照（84.6%）+ eval 标尺 + RST-L06 硬化
- **③w4/③w5 措辞修复 + 发版遗留**（已闭环）：gap 措辞 failedObs 判据（零工具尝试「无法直接回答」非「未生成图层」）+ eval 标尺（76%→84% GO）+ RST-L06 preset fallback + buffer stale-tool 门控
- **③w6/③w7 发版 backlog 收尾**（已闭环）：footer 条件化 + preset 行政区清 4 要素（备份 .bak9）+ district-stats 8→4 组团 + RST-L06 fallback MC 修复 + eval 注释 + fixture 静态守卫

## 今日 commit（fix/emc-buglog·**已与远端 0/0 同步**）

| commit | 内容 |
|---|---|
| `0bb55df` | ③w7b 反评价（两组通过·fixture 静态守卫 +1·pytest 278） |
| `23efe74` | **③w6b 实施（footer 条件化 + fixture 清 4 + district-stats 8→4 + RST-L06 MC + eval 注释）** |
| `1730e82` | ③w7 检查发起 |
| `d671df9` | ③w6 发版 backlog 收尾预检发起 |
| `2130a49` | ③w5b 反评价（glm 补充 eval 84% 纠正·已推） |
| `78db0e3` | ③w5 闭环（措辞断言 e2e-seam + eval tuple 双接受 + 检查请求） |
| `c53aa99` | **③w4b 实施（措辞 failedObs + eval 标尺 + RST-L06 fallback + buffer 门控）** |
| `ef49cc1` | ③w4 综合 plan（措辞 + eval + RST-L06 + PRM 打包） |
| `dc50e11` | ③w4 措辞修复预检发起 |
| `0a0d103` | ③z3b 反评价 |
| `401371b` | **③z 余留 2b + P2 实现** |
| `dc88f35` | ③w2 全局优化 + 发版快照 + 时间轴预检发起 |
| `7d8a258` | ③z 全闭环文档同步 |
| ... | ③z 前历史（Wave 0-3 + ③z 预检·已 push） |

## 关键架构（下会话须知道）

- **出口抽象层三铁律**（CLAUDE.md 顶层纲领）：EMC 找市场接口 / 三段式线性（意图→结果→成果范式 agent·**第三段已实现**）/ 定性+定量+地理按尺度
- **软指标可信性缺口**（立项切入点）：官方三类（可量化/可感知/可评价）·情绪地图 = 填补可靠软指标层
- **outlet_kb**（`ai_qa/outlet_kb/`）：7 契约 + 21 指标映射 + build_outlet_schema（确定性组装·不调 LLM）+ 可感知计算器 2a/2b
- **CB-15 数据认知**（已完成）：3220 POI 接入 + place_name 双源 + /grid/pois + lookup_place + buffer 中文 fallback
- **③w7 发版收尾**（已完成）：preset 行政区清 4 真实区划（FIXED_ADMIN_DISTRICTS·备份 .bak9）·district-stats 8→4 组团·PRM-07 根治·fixture 静态守卫
- **三态出口措辞**（③w4/w5/w6 完成）：failedObs 判据——零工具尝试「无法直接回答/无法理解」·试过工具「未生成图层」·footer 条件化
- **eval 标尺**（③w4/w5）：select_template 单工具不返 multi（前端 CHAIN_REGISTRY 覆盖）·tuple 双接受治概率性歧义·84% GO
- **B3 修复**（已闭环）：范围三来源 + FIXED_ADMIN_DISTRICTS + derive 鲁棒性 + CPD + PRM-08
- **trace 取证纪律**：根因分析先 `trace_query --stats`·跑测试带 session

## 【下一步】（用户定·换环境后续作）

1. **发版就绪度回归**：B3 快照重跑（验证 ③w4~③w7 修复后·目标 25/26·96.2%）+ link_checkup 体检 + eval 复采（≥2 次·记录日期/模型）+ RST-L06 复跑（前台 serve 环境）
2. **时间轴专题**（用户之前说「不成熟·放后面开专题」·manifest 404 同源派生方案已探索·候选 1 geo_registry 同源 + fallback API）
3. **backlog 残留**：陈旧注释同步（district-stats 头部「8 组团」/panel.js×4）·FC 编造 boundary 残余 · 措辞断言测试前台 serve 验证 · MOD_PLACE 渲染风暴 · MOD_LLM.F_002

## 待续项（下会话从这继续）

- **【核心】发版就绪度回归**（B3 重跑 + link_checkup + eval 复采 + RST-L06 复跑·前台 serve）
- **时间轴专题**（manifest 404·候选 1 同源派生方案）
- **backlog**：陈旧注释·FC boundary·措辞断言前台验证·MOD_PLACE 风暴·MOD_LLM.F_002
- **待用户浏览器复验**：多卡渲染 + perceptible_metrics 小节 + 措辞修复（零工具「无法直接回答」）+ fixture 4 组团 L1 总览

## 测试基建

- pytest：**278 passed**（+fixture 静态守卫）
- 新增守卫：`tests/validate_outlet_fields.py`（死字段 fail/缺消费 warn）+ `validate_outlet_trigger_sync.py` + `test_range_selector_presets.py::test_admin_district_fixture_mc_in_whitelist`（preset MC ⊆ 白名单·防回潮）
- 措辞断言：`py tests/browser/test_gap_wording.py`（3 场景·待前台 serve 环境验证）
- 飞轮：`py tests/browser/flywheel_audit.py --batch B3`（带 `EMOTION_TRACE_SESSION=B3-<批>`）
- 体检：`py tests/browser/test_link_checkup.py`（20 例·回归门）
- 根因分析：`py tools/trace_query.py --stats/--id/--time/--session`（第一动作）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前 CB 轮次：**CB-16（Wave 0-3 + ③z~③w7 全闭环·发版准备）**·之前 CB-12/13/14/15 已闭环
- **双阵营**：claude组（开发主）+ Codex + glm组（评估·trace 取证功臣）
- 反评价轨迹：`docs/catch-ball/cb-journal.md`（③a-③w7b）
- 恢复卡：`docs/catch-ball/_handoff/CB恢复记忆卡_2026-08-03.md`（两组换环境用）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / **`@track()` 签名 / `_TRACKING_REGISTRY` 格式**（改前先扩 eval·每次一处）
- **出口抽象层**：不新增 LLM 阶段（撞 D019）·outlet 契约走 tool_contracts 单一源·能/不能双栏诚实·确定性组装（compute_perceptible 不调 LLM）
- **CB 机制**：每轮工作进 CB（实施前预检 + 实施后检查·两组 SCAN 反评价·先讨论再实施·先验后推）·评估方（Codex/glm）同一本地工作区只读·不 git pull/push（claude组 负责 git）·prompt 用代码块包裹（可点击复制）·**plan/草案也进 CB**（不只修复）
- **数据红线**：改 DATA 需备份 + 用户确认（③w6 fixture 清理已备份 .bak9 先例）
- **trace 取证**：根因分析先 `trace_query --stats`·推断只作假设
- **EMC 产物不临时创造样式**；不动 FC prompt；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**；commit 后 push（commit+push 组合·push 非红线）

## 恢复指引（新会话·换环境后）

1. `git pull`（fix/emc-buglog·最新 `0bb55df`·与远端同步）。
2. 读本卡「关键架构」+「待续项」。
3. 读 `docs/todo.md` 08-04 段 + `docs/revision-log.md` §5 最新。
4. 读 CLAUDE.md「出口抽象层」顶层纲领节（最底层逻辑·指导开发）。
5. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
6. 从「待续项」继续（核心 = **发版就绪度回归**：B3 重跑 + link_checkup + eval 复采 + RST-L06 复跑）。
