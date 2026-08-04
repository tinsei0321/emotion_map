# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月04日（**Wave 1（macro 出口）实施完成：两组预检反评价 + 7 处落地·rows 产物链路打通**）| 分支 `fix/emc-buglog` | **待 push（今晨起 ~12 commit 未推）**
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md` + `OFFICE.md`

## 当前节点：Wave 1（macro 出口）实施完成（Wave 0 完整链路 + R7 修复 + 大南门数据接入已闭环）

08-03→04 大跨轮（CB-12/13/14/15 已闭环·CB-16 出口深化收敛）：
- **出口抽象层定稿**：EMC 找市场·三段式（意图→结果→**成果范式 agent**）·软指标可信性缺口 = 立项切入点·官方三类指标（可量化 ~55-65% / 可感知 ~15-20% / 可评价 ~15-25%·合计 30-45% 涉及市民感受）
- **outlet_kb 出向知识库**：7 契约 + 21 指标映射（官方三类）+ 5 案例 + summary 四方面闭环 + 测试守卫
- **Wave 0 出口卡片完整链路（从 0 到 1·核心成果）**：
  - `build_outlet_schema.py`（确定性组装器：resolve_outlet_id + 7 要素组装·不调 LLM·字段缺失降级·尺度分派·诚实标注）
  - `/api/v1/aiqa/outlet_card` 端点（接收 diagnose+result+question → 卡 JSON）
  - harness result 态后条件调（_maybeBuildOutletCard·触发词+UI 语境排除·产物收集·5s 超时·失败静默）
  - panel `renderOutletCard` 纯模板渲染（仿 .cpd-guide-card·既有 token·缺失灰·引用块·{{show:}} 复用）+ `.outlet-card` CSS
  - emc-patterns.js OUTLET_TRIGGER_KW + OUTLET_UI_EXCLUDE_KW（镜像·DRY import）·validate_outlet_trigger_sync.py 同步守卫（双份）
  - **端到端验证**：问"西陵区老旧小区更新需求分析"→ 需求分析卡（停车难/-0.32/夷陵广场·诚实标注）
  - **CB 两轮检查通过**（实施后检查：Codex+glm 全通过·3 P3 已修：词表 import/point_count/超时）
- **出口驱动开发方法论**（用户定）：基于出口反推定制分析方法/计划/执行工具/图例样式/出图文本范式·新功能评审清单非全量门禁

## 今日已 commit（fix/emc-buglog · **已 push·与远端同步**）

| commit | 内容 |
|---|---|
| `5dfac4b` | Wave 0 三 P3 修复（词表 import/point_count/超时）+ 检查 SCAN 入库 |
| `e0503b9` | Wave 0 实施后检查发起（5 环节核验）|
| `bd3ccce` | Wave 0 完整链路完成登记 |
| `38d3a0c` | **Wave 0 出口卡片完整链路**（端点/接线/渲染/词表/守卫）|
| `25bf898` | Wave 0 剩余实施预告（CB 机制）|
| `4369df2` | Wave 0 三 bug 修复反评价登记 |
| `f84b3ae` | Wave 0 三 bug 修复（qualifier/更新词/体检 domain）+ 回归测试 |
| `21e5f8f` | Wave 0 剩余实施检查发起 |
| `9a98785` | **Wave 0 出口卡片确定性组装器**（build_outlet_schema）+ CB-16 反评价 |
| `c7c7f4b` | CB-16 出口深化讨论发起（含出口驱动开发逻辑链）|
| `0822b49` | 官方三类指标进指标库 + 上下文树登记 |
| `e1c1446` | 指标体系官方三类表达（可量化/可感知/可评价）+ 全量罗列 + 规建营 + 三大体系 |
| `27f176f` | **出口抽象层入 CLAUDE.md 顶层纲领** + 交接卡 |
| `1c634ee` `e3701a7` | 官方原文引用 + A→D 承上启下 + 措辞修正 |
| `bb2019d` | 软指标官方表述 + 全部主观指标罗列 + 地方特色关系 |
| `a821274` | A 部分 61 项指标三类分列 + 占比统计 |
| `530a50e` | 深化传统体检做法论证 + 官方链接 |
| `d80a289` | 案例加体检工作方式背景 |
| `22dd2b9` | 案例小结四方面闭环 |
| `b4df098` | 案例深挖 v3 三段式 |
| `2c3ca52` | 案例深挖 v2 指向指标体系 |
| `c434d6e` | 宜昌望洲岗改示范成效 |
| `51fa836` | 出口报告 EMC→情绪地图·EMC + 案例深挖 |
| `63493b2` | **outlet_kb 出向知识库**（7 契约+21 指标+5 案例）|
| `c981371` | CB-13/14/15 讨论入库 |
| `aa077c8` | **B3-verify-07 25/26 历史最佳**（范围三来源 + 归因联动基础）|

## 关键架构（下会话须知道）

- **出口抽象层三铁律**（CLAUDE.md 顶层纲领）：EMC 找市场接口 / 三段式线性（意图→结果→成果范式 agent·**第三段已实现**）/ 定性+定量+地理按尺度
- **软指标可信性缺口**（立项切入点）：官方三类（可量化/可感知/可评价）·合计 30-45% 涉及市民感受·情绪地图 = 填补可靠软指标层（全量评论流）
- **三大指标体系**：国家十五五（10 项·统领）/ 住建部（4 维度 61 项·规建营·重点）/ 自然资源部（110 项·了解）
- **Wave 0 出口卡片链路**（已完成）：build_outlet_schema → /outlet_card 端点 → harness 接线 → outlet-card 渲染 → 同步守卫
- **outlet_kb**（`ai_qa/outlet_kb/`）：7 契约 + 21 指标映射（官方三类）+ 5 案例 + build_outlet_schema.py·确定性组装·测试守卫（pytest 242 passed）
- **出口驱动开发方法论**：基于出口反推定制分析/计划/工具/图例/范式·新功能评审清单（Codex CI 守卫 validate_outlet_fields 待 Wave 3）
- **B3 修复**（已闭环）：范围三来源 + FIXED_ADMIN_DISTRICTS + derive 鲁棒性 + CPD + PRM-08（pytest 242）
- **trace 取证纪律**：根因分析先 `trace_query --stats`（F_002/F_003 非 F_001）·跑测试带 session

## 【下一步】（用户定：Wave 1 先行已完成）

1. **Wave 2 / CB-15**（数据认知·前置落地）：格↔POI sjoin + place_name 双源 + /grid/pois 端点——出口卡「需求位置」从粗略版（格内代表地名）升级到精确 POI（用户之前问的「出口×地点联动」精确版）
2. **Wave 3**：可感知 10 项计算器（compute_perceptible_metrics）+ validate_outlet_fields CI + 多卡支持
3. **补 1 处**：checkup_satisfaction field_mapping 也 prose→真实字段（P2·否则 S6 满意度卡同出空卡）

## 待续项（下会话从这继续）

- **【核心】Wave 2 / CB-15**：格↔POI sjoin + place_name 双源 + /grid/pois（CB-15 讨论稿共识已立·落地未做）
- **Wave 3**：可感知计算器 + validate_outlet_fields CI + 多卡
- **checkup_satisfaction** prose→字段（P2）
- **backlog**：MOD_PLACE 渲染风暴 + MOD_LLM.F_002 fallback 重核 + CPD-L01/L02 测试基建 + 时间轴 manifest 404
- 发版候选评估（B3 96.2% 达标上沿）
- **待用户浏览器复验**：Wave 1 macro 问句真出卡（更新对象识别/体检四维度）+ R7 截断修复 + push 全部 commit

## 测试基建

- pytest：**242 passed**（+outlet_schema 10 + trigger_sync 2）
- 飞轮：`py tests/browser/flywheel_audit.py --batch B3`（带 `EMOTION_TRACE_SESSION=B3-<批>`）
- 体检：`py tests/browser/test_link_checkup.py`（20 例·回归门）
- 根因分析：`py tools/trace_query.py --stats/--id/--time/--session`（第一动作）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前 CB 轮次：**CB-16 出口深化（Wave 0 闭环）**·之前 CB-12/13/14/15 已闭环
- **双阵营**：claude组（开发主）+ Codex + glm组（评估·trace 取证功臣）
- 反评价轨迹：`docs/catch-ball/cb-journal.md`
- 恢复卡：`docs/catch-ball/_handoff/CB恢复记忆卡_2026-08-03.md`（两组换环境用）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / **`@track()` 签名 / `_TRACKING_REGISTRY` 格式**（改前先扩 eval·每次一处）
- **出口抽象层**：不新增 LLM 阶段（撞 D019）·outlet 契约走 tool_contracts 单一源·能/不能双栏诚实
- **CB 机制**：每轮工作进 CB（实施前预告 + 实施后检查·两组 SCAN 反评价）
- **trace 取证**：根因分析先 `trace_query --stats`·推断只作假设
- **EMC 产物不临时创造样式**；不动 FC prompt；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**；commit 后 push（网络不稳时待恢复）

## 恢复指引（新会话·公司）

1. `git log --oneline -8` 对账（最新 `5dfac4b`·与远端同步）。
2. 读本卡「关键架构」+「待续项」。
3. 读 `docs/todo.md` 08-03/04 段 + `docs/revision-log.md` §5 最新。
4. 读 CLAUDE.md「出口抽象层」顶层纲领节（最底层逻辑·指导开发）。
5. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
6. 从「待续项」继续（核心 = 大南门·二马路数据模拟专题 + Wave 1 macro 出口）。
