# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月03日（**出口抽象层攻坚：软指标可信性缺口定案 + 案例三段式深挖 + outlet_kb 出向知识库 + 出口抽象层入 CLAUDE.md 顶层纲领**）| 分支 `fix/emc-buglog` | **待 push（本地领先 2）**
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md` + `OFFICE.md`

## 当前节点：出口抽象层攻坚（立项根本目标）— 软指标可信性缺口定案 + 案例深挖 + outlet_kb

今日大跨轮（CB-12/13/14 已闭环）：
- **B3-verify-07 = 25/26（96.2%）历史最佳**（CPD 全过 + PRM-08 修复 + 范围三来源准则 + derive 鲁棒性）
- **RAG 定稿**：现在不建·RAG-lite（A4 选择性注入 finalStep）先行
- **用户新定性**：范围=矢量表达不关键·**地点认知（拓扑）是关键**·归因↔地点联动=中微观标准出口
- **出口抽象层（立项关键）**：EMC 找市场接口·三段式（意图→结果→**成果范式 agent**）·软指标可信性缺口 = 立项切入点
- **案例深挖 v3**：三段式（真实民意调研→情绪地图对应→对标对表）+ 四方面逻辑闭环小结 + 体检工作方式背景 + 61 项指标三类分列（客观 ~79% / 主观感知 ~21% / 地方特色）
- **outlet_kb 出向知识库**（`ai_qa/outlet_kb/`）：7 契约 + 8 指标 + 5 案例 + summary 四方面闭环 + 测试守卫（pytest 234 passed）
- **出口抽象层已入 CLAUDE.md 顶层纲领**（最底层逻辑·指导后续开发）

## 今日已 commit（fix/emc-buglog · **本地领先远端 2·待 push**）

| commit | 内容 |
|---|---|
| `1c634ee` | 官方原文引用 + A→D 承上启下 + 来源链接改版（**待 push**）|
| `e3701a7` | 措辞修正（客观/主观指标·官方表述）+ 强化 A→D 逻辑链（**待 push**）|
| `bb2019d` | 软指标官方表述 + 全部主观指标罗列 + 地方特色关系（已 push）|
| `a821274` | A 部分 61 项指标三类分列 + 占比统计（已 push）|
| `530a50e` | 深化传统体检做法论证 + 官方链接 + 全局逻辑（已 push）|
| `d80a289` | 案例加体检工作方式背景（已 push）|
| `22dd2b9` | 案例小结四方面闭环（已 push）|
| `b4df098` | 案例深挖 v3 三段式（已 push）|
| `2c3ca52` | 案例深挖 v2 指向指标体系（已 push）|
| `c434d6e` | 宜昌望洲岗改示范成效（已 push）|
| `63493b2` `51fa836` | outlet_kb + 出口修正工程讨论（已 push）|

> 注：`e3701a7` 是用户/subagent 提交的措辞修正·与 `bb2019d` 内容互补·不冲突。

## 关键架构（下会话须知道）

- **出口抽象层三铁律**（CLAUDE.md 新增顶层纲领）：EMC 找市场接口 / 三段式线性（意图→结果→成果范式 agent·第三段缺失）/ 定性+定量+地理按尺度
- **软指标可信性缺口**（立项切入点）：住建部 61 项基础指标**官方三类**（建科〔2023〕75号）：可量化 ~55-65%（遥感/CIM/普查·不含民意）+ 可感知 ~15-20% + 可评价 ~15-25%（问卷·样本≥0.2%·时滞/难定位/难追踪）——**合计 30-45% 涉及市民感受**·缺"既承载民意又统计可靠可定位"的软指标层 = 情绪地图要填的（全量评论流）
- **三大指标体系**：国家十五五（10 项·统领）/ **住建部（4 维度 61 项·重点·规建营：住房=建/小区=营/街区=规+营/城区=规）**/ 自然资源部（110 项·了解）
- **地方特色指标**：官方"基础+特色"两类框架·特色=基础之上增加（非第三类并列）·以可量化为主（呼和浩特 60+8+32/天津 61+41/鄂尔多斯 55+6+17/邵阳/漠河）
- **outlet_kb**（`ai_qa/outlet_kb/`）：7 契约（更新对象识别/需求摸排/时序/内容/项目 + 体检满意度/四维度）+ **21 指标映射（官方三类：可感知 10 + 可评价 3 + 可量化 8）** + 5 案例（宜昌望洲岗/上海/广州/南京/宁夏）·确定性组装（build_outlet_schema 查契约·不靠 LLM 编造）·能/不能双栏·**已登记 context-map 叶·专项参考**
- **案例三段式**：真实民意调研（做法/数据/难点短板）→ 情绪地图对应（图/数/表/观点→指标）→ 对标对表（更专业/全面/科学）+ 四方面闭环小结（需求调研/片区评估/示范选择/事项紧迫性）
- **B3 修复**（已闭环）：范围三来源准则 + FIXED_ADMIN_DISTRICTS + derive 鲁棒性 + CPD 测试基建 + PRM-08 compare 兜底 + A4 注入（pytest 234 passed）
- **trace 取证纪律**：根因分析先 `trace_query --stats`（F_002/F_003 非 F_001）·跑测试带 session

## 【下一步】换环境继续攻坚（用户定）

1. **开展 CB 讨论**：发出口抽象层报告（专业版+通俗版·已含案例深挖 v3）给 Codex/glm 两组 → 讨论结果范式 agent 修正工程 + outlet_kb 接入（请求已落 `_handoff/CB15-出口修正工程讨论`）
2. **完善**：根据两组 SCAN 反评价 → 完善出口抽象层方案（结果范式 agent 架构/outlet_id 映射/outlet_kb 消费/尺度校验/MVP=S2）
3. **定稿执行**：方案定稿 → 实现结果范式 agent（build_outlet_schema）+ 出口卡片渲染 → 立项目标落地

## 待续项（下会话从这继续）

- **【核心】出口抽象层定稿执行**：CB 讨论 → 反评价 → 结果范式 agent 实现（build_outlet_schema 查 outlet_kb 契约组装出口卡片）·MVP = S2 更新需求分析
- **outlet_kb 消费**：build_outlet_schema（后端确定性组装）+ 前端卡片渲染（不新增 LLM 阶段·撞 D019 红线风险）
- **CB-15 数据认知**（先行）：格↔POI sjoin + place_name 双源 + /grid/pois 端点（出口地理定位要素依赖）
- **backlog**：MOD_PLACE 渲染风暴 + MOD_LLM.F_002 fallback 重核 + CPD-L01/L02 测试基建 + 时间轴 manifest 404
- 发版候选评估（B3 96.2% 达标上沿·整体评估）

## 测试基建

- pytest：**234 passed**（+outlet_kb 6 测试）
- 飞轮：`py tests/browser/flywheel_audit.py --batch B3`（带 `EMOTION_TRACE_SESSION=B3-<批>`）
- 体检：`py tests/browser/test_link_checkup.py`（20 例·回归门）
- 根因分析：`py tools/trace_query.py --stats/--id/--time/--session`（第一动作）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前 CB 轮次：**CB-15 出口抽象层 + 数据认知**（立项关键·讨论中）· 之前 CB-12/13/14 已闭环
- **双阵营**：claude组（开发主）+ Codex + glm组（评估·trace 取证功臣）
- 反评价轨迹：`docs/catch-ball/cb-journal.md`
- 恢复卡：`docs/catch-ball/_handoff/CB恢复记忆卡_2026-08-03.md`（两组换环境用）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / **`@track()` 签名 / `_TRACKING_REGISTRY` 格式**（改前先扩 eval·每次一处）
- **出口抽象层**：不新增 LLM 阶段（撞 D019 红线）·outlet 契约走 tool_contracts 单一源·能/不能双栏诚实
- **trace 取证**：根因分析先 `trace_query --stats`（F_002/F_003 非 F_001）·推断只作假设
- **EMC 产物不临时创造样式**；不动 FC prompt；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**；commit 后 push 待网络（当前本地领先 2）

## 恢复指引（新会话）

1. `git log --oneline -8` 对账（最新 `1c634ee` + 待 push）。
2. 读本卡「关键架构」+「待续项」。
3. 读 `docs/todo.md` 08-03 段 + `docs/revision-log.md` §5 最新。
4. 读 CLAUDE.md「出口抽象层」顶层纲领节（最底层逻辑·指导开发）。
5. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
6. 从「待续项」继续（核心 = 出口抽象层定稿执行·先 CB 讨论）。
