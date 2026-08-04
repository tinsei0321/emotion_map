# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月04日（**Wave 3 余留 2b + P2 预检已发·家庭环境续作·与远端 0/0 同步**）| 分支 `fix/emc-buglog` | **已与 `origin/fix/emc-buglog` 0/0 同步（0862f09 + 1500e5b 均已在远端·无需推）**
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md` + `OFFICE.md`

## 当前节点：CB-16 出口抽象层 Wave 0-3 全闭环·Wave 3 检查已发 + 余留 2b/P2 预检再发

08-04 大跨轮（CB-16 出口深化·Wave 0→1→2→3 全闭环）：
- **Wave 0 出口卡片完整链路**（已闭环·CB 两轮检查通过）：build_outlet_schema 确定性组装器 + /outlet_card 端点 + harness 接线 + panel 渲染 + 触发词表同步守卫
- **R7 截断修复**（已闭环·用户实测 bug）：阈值 800→1500 + 结构回切 + R2 按钮保留 + 去 '.' 切句符 + 悬空编号剥除（两组检查 P0 补修）
- **大南门·二马路数据接入**（已闭环）：ermawu L3L4 三层注册 + CSV 补坐标 + 边界登记 + R7 截断修复
- **Wave 1 macro 出口**（已闭环·两组检查 P1/P2 补修）：rows 产物链路打通（_lastToolRows 缓存 + 门放宽 + _extract_emc_value 统一收 rows/features + checkup_dimension scale 限定 + DOMAIN_KW 城市体检）
- **Wave 2 / CB-15 P0 数据认知**（已闭环·两组检查 P1/P2 补修）：3220 POI 接入（_read_pois_geojson + _dedup_pois·all_pois=4342）+ place_name 双源融合（_attach_poi_attrs grid/polygon 双模式 + place_name_source）+ poi_names + /grid/pois 端点 + cell_id
- **CB-15 P1 地点进问答管线**（已闭环·两组检查 P2×4 补修）：buffer 中文 POI fallback（search_place）+ lookup_place 工具（契约三处同步 + track F_013）+ 归因落点模板（+ 合成 + 修文案）
- **Wave 3 出口深化**（实施完成·**检查已发 0862f09 待两组 SCAN**）：多卡支持（resolve_outlet_ids + cards + build_outlet_schema_single 兼容）+ validate_outlet_fields CI + 可感知计算器 2a（B 类条件等式 2b 后置）
- **③z 余留 2b + P2 预检已发**（`_handoff/CB16-Wave3预检2b-P2_2026-08-04.md`）：可感知计算器 2b（B 类条件等式 6 项·_parse_emc_expr）+ checkup_satisfaction P2（prose→真实字段）

## 今日 commit（fix/emc-buglog·**已与远端 0/0 同步·无需推**）

| commit | 内容 |
|---|---|
| `1500e5b` | 进度更新 + 交接卡覆写（Wave 3 检查发起·待换环境续作） |
| `0862f09` | **Wave 3 实施后检查发起（已推）** |
| `1daffc6` | **Wave 3 多卡 + validate CI + 可感知计算器 2a** |
| `0c9ba95` | Wave 3 预检发起 |
| `04a6487` | CB-15 P1 补修（P2×4） |
| `c3e1c9d` | CB-15 P1 检查发起 |
| `61567d6` | **CB-15 P1 地点进问答管线** |
| `5d3ccc9` | CB-15 P1 预检发起 |
| `ad18f59` | Wave 2 补修（去重连锁店 + cell_id） |
| `49e0e71` | Wave 2 检查发起 |
| `623e293` | **Wave 2 / CB-15 P0 下钻链最小闭环** |
| `386a23d` | Wave 2 预检发起 |
| `9f40e55` | Wave 1 补修（runAllToolCalls rows + 跨轮重置） |
| `0c7a783` | Wave 1 检查发起 |
| `9ea1290` | 交接卡更新 |
| `97cf232` | **Wave 1 macro 出口** |
| ... | Wave 0/R7/大南门接入（已 push） |

## 关键架构（下会话须知道）

- **出口抽象层三铁律**（CLAUDE.md 顶层纲领）：EMC 找市场接口 / 三段式线性（意图→结果→成果范式 agent·**第三段已实现**）/ 定性+定量+地理按尺度
- **软指标可信性缺口**（立项切入点）：官方三类（可量化/可感知/可评价）·合计 30-45% 涉及市民感受·情绪地图 = 填补可靠软指标层
- **outlet_kb**（`ai_qa/outlet_kb/`）：7 契约 + 21 指标映射（官方三类）+ 5 案例 + build_outlet_schema.py（确定性组装·不调 LLM）
- **Wave 0-3 全链路**（已完成）：build_outlet_schema（多卡 cards + 单卡兼容 + 可感知计算器）→ /outlet_card（{cards, card}）→ harness 接线 → panel 多卡渲染 → 触发词同步守卫 + validate_outlet_fields CI
- **CB-15 数据认知**（已完成）：3220 POI 接入（all_pois=4342）+ place_name 双源（poi_sjoin/top_places + place_name_source）+ /grid/pois + lookup_place + buffer 中文 fallback
- **B3 修复**（已闭环）：范围三来源 + FIXED_ADMIN_DISTRICTS + derive 鲁棒性 + CPD + PRM-08
- **trace 取证纪律**：根因分析先 `trace_query --stats`·跑测试带 session

## 【下一步】（用户定·换环境后续作）

1. **等两组 Wave 3 实施后检查 SCAN**（已发 0862f09）→ 反评价 → push（已与远端同步·届时只需本地 push）
2. **Wave 3 余留 2b + P2 补充预检已发**（③z·`_handoff/CB16-Wave3预检2b-P2_2026-08-04.md`）→ 等两组补充 SCAN → 反评价 → 实施（计算器 2b + checkup_satisfaction P2）
3. **backlog**：validate_skill_params 7 工具 drift（paradigm when 同步）·MOD_PLACE 渲染风暴 + MOD_LLM.F_002 fallback 重核 + CPD-L01/L02 + 时间轴 manifest 404

## 待续项（下会话从这继续）

- **【核心】Wave 3 检查 SCAN 处理**（两组已发·待反评价）+ **③z 补充预检 SCAN**（2b/P2 草案·待反评价）
- **可感知计算器 2b**（B 类条件等式·草案已发两组预检）
- **checkup_satisfaction** prose→字段（P2·草案已发）
- **backlog**：7 工具 drift · MOD_PLACE 渲染风暴 · MOD_LLM.F_002 · CPD-L01/L02 · 时间轴 manifest
- 发版候选评估（B3 96.2% 达标上沿）
- **待用户浏览器复验**：macro 问句出卡 + buffer 中文名 + lookup_place 地点清单 + 多卡渲染

## 测试基建

- pytest：**269 passed**（+Wave 3 多卡/计算器/validate + CB-15 P1 + Wave 2 + Wave 1 全部）
- 新增守卫：`py -m pytest tests/validate_outlet_fields.py`（死字段 fail/缺消费 warn）+ `validate_outlet_trigger_sync.py`（触发词同步）
- 飞轮：`py tests/browser/flywheel_audit.py --batch B3`（带 `EMOTION_TRACE_SESSION=B3-<批>`）
- 体检：`py tests/browser/test_link_checkup.py`（20 例·回归门）
- 根因分析：`py tools/trace_query.py --stats/--id/--time/--session`（第一动作）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前 CB 轮次：**CB-16 出口深化（Wave 0-3 全闭环·Wave 3 检查进行中 + ③z 余留 2b/P2 预检待反评价）**·之前 CB-12/13/14/15 已闭环
- **双阵营**：claude组（开发主）+ Codex + glm组（评估·trace 取证功臣）
- 反评价轨迹：`docs/catch-ball/cb-journal.md`（③a-③z）
- 恢复卡：`docs/catch-ball/_handoff/CB恢复记忆卡_2026-08-03.md`（两组换环境用）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / **`@track()` 签名 / `_TRACKING_REGISTRY` 格式**（改前先扩 eval·每次一处）
- **出口抽象层**：不新增 LLM 阶段（撞 D019）·outlet 契约走 tool_contracts 单一源·能/不能双栏诚实·确定性组装（compute_perceptible 不调 LLM）
- **CB 机制**：每轮工作进 CB（实施前预告 + 实施后检查·两组 SCAN 反评价）·prompt 用代码块包裹（可点击复制）
- **trace 取证**：根因分析先 `trace_query --stats`·推断只作假设
- **EMC 产物不临时创造样式**；不动 FC prompt；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**；commit 后 push（网络不稳时待恢复）

## 恢复指引（新会话·换环境后）

1. `git log --oneline -8` 对账（最新 `1500e5b`·已与 `origin/fix/emc-buglog` 0/0 同步·无需推）。
2. 读本卡「关键架构」+「待续项」。
3. 读 `docs/todo.md` 08-04 段 + `docs/revision-log.md` §5 最新。
4. 读 CLAUDE.md「出口抽象层」顶层纲领节（最底层逻辑·指导开发）。
5. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
6. 从「待续项」继续（核心 = Wave 3 检查 SCAN 处理 + ③z 余留 2b/P2 预检反评价）。
