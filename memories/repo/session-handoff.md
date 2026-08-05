# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月05日深夜（**出口三段式 P0-P2 + 热点图 P0/P1/P1.5 全流程·CB 计划→执行→审计→修正闭环**）| 分支 `fix/emc-buglog` | **本地 commit `0916e8c`(已 push) + `83a1ac9`(进度文档·待 push·网络故障)**
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md` + `OFFICE.md`

## 当前节点：出口三段式 P0-P2 + 热点图 P0/P1/P1.5 全流程（已实施·待整体验收）

08-05 大跨轮（两专题·CB 全流程）：

### 出口三段式（用户意图：出口=观点先行干货→4 要点→行业接口参数·既稳定又灵活）
- **P0 观点先行**（已闭环）：FINAL_TEMPLATE 软扩（`> **观点：**` 引用块·观点≠结论·**2957B<3000B 门禁**）+ `result-struct.js`（结论段独立聚合·不解析 draft markdown·观点三档兜底）+ panel 观点卡/4 要点卡 + ctx 双保险 + `_dispatchResultStruct` 三路径补接（B1）
- **P1 指标细化**（已闭环）：`grade_demand_intensity` 四档（高/中/低/无显著需求·L2 值域归一）+ `priority_score` 复合优先级（p95/缺省不参与/主题 0.5/1）+ case_library measure_note×4 + `export_outlet_card_csv`（脱敏）+ 前端导出按钮 + geo_label
- **P2 地点 scale**（已闭环）：geo_label（宏观·面域/中观·单元/微观·落点）
- 两组评估/审计修正全采纳（值域双轨·结论段独立聚合·体积预算·观点卡兜底等）

### 热点图重做（用户意图：情绪热点图重做·热力/热点定标·3D 连续曲面·工具间解耦）
- **P0 命名定标**（已闭环·8 处）：Gi\*→「显著聚集点(Gi\*)」· `spatial_hotspot`→「代表地点」·「热力图」统一
- **P0 前置 A/B 验证**（重大发现）：真实 L2 数据 2500 点·**逐点/500m/200m 网格 Gi\* 全部全 ns 无热点**（Gi_Z 全在 ±1.07~1.26）·**根因 = score 是 5 级极性映射的 U 形多峰离散分布·与 Gi\* 连续正态假设不匹配**（glm 主因·网格化平滑 Z 但非解药）
- **P1 软分级五档**（已闭环）：`_classify_hotspot`（hot/tend_hot/ns/tend_cold/cold·threshold 参数化默认 1.96/soft 1.0）+ `hotspot_tier` + 前端 `colorMode='hotspot'` 显著性符号层（弃 `_CLS_POL` 极性色·**纯橙系**·与 KDE 解耦）
- **P1.5 setTerrain 连续曲面**（已闭环）：`create_terrain_dem`（**F_009**·KDE→terrarium RGB·bounds WGS84）+ `/spatial/dem` 端点 + map.js `setTerrainDEM`（**draping 隔离**：不常驻+与 3D 网格柱互斥+sky 层）+ `generateTerrain3DForAI`（EMC 委托已切）+ retired.md 退役登记（fill-extrusion 3D→setTerrain·2D 等值线保留）
- 实施审计（两组）：P0+P1 可验收·P1.5 有 B1 阻断（setTerrain 无入口+EMC 未切）→ **修复全完成**（B1 委托切换/W1 橙系/W2 threshold 透传/W3 legend 五档/W6 契约层同步/建议级注释清理）

## 今日 commit（fix/emc-buglog）

| commit | 内容 | push |
|---|---|---|
| `83a1ac9` | 进度文档（todo/emc-fix-progress/revision-log·v3.6） | ⚠️ **待 push**（网络故障·重试超时/Connection reset）|
| `0916e8c` | **出口三段式 P0-P2 + 热点图 P0/P1/P1.5 全流程**（69 文件·8007 增·pytest 293 passed + validate 28 passed） | ✅ 已 push |

> ⚠️ `83a1ac9` 未 push——网络访问 github 持续失败（`Connection reset`/443 端口超时）。恢复后手动 `git push`。

## 关键架构（下会话须知道）

- **出口三段式**（新定稿）：第一段=明确观点（`> **观点：**`·LLM 核心价值·答"所以呢"）→ 第二段=4 要点（方法/数据/结果/结论·确定性组装）→ 第三段=行业接口参数（**条件段**·意图 agent 判断·未涉归因不入库）·观点≠结论（观点=转化答提问·结论=图数表描述性论述）
- **热点图定稿**（新定稿）：KDE 热力面=主图（用户"舆情热度地势"）· Gi\* =「显著聚集点」显著性检验（**软分级五档·诚实标 84% 倾向**）· 3D = setTerrain 连续曲面（非 fill-extrusion 千层饼·draping 隔离）
- **Gi\* A/B 结论**：EMC score 是 U 形离散分布·**Gi\* 连续假设不匹配**→ 长期评估 KDE/DBSCAN 替代（热点图 P2/P3 议题·本轮不换）
- **出口抽象层**（旧纲领仍生效）：EMC 找市场接口 / 三段式线性 / 定性+定量+地理按尺度
- **outlet_kb**（`ai_qa/outlet_kb/`）：7 契约 + 21 指标映射 + build_outlet_schema（确定性组装）+ 可感知计算器 2a/2b + **P1 新增需求强度分级/复合优先级**
- **CB-15 数据认知**（已完成）：3220 POI + place_name 双源 + /grid/pois + lookup_place
- **trace 取证纪律**：根因分析先 `trace_query --stats`·跑测试带 session

## 【下一步】（用户定·换环境后续作）

1. **整体验收**（todo「整体验收清单」）：出口三段式（观点卡置顶/4 要点卡/三路径都出卡/需求强度等级/CSV 导出/geo_label）+ 热点图（显著聚集五档橙系/legend 五档/setTerrain 连续曲面/网格柱互斥/无露底）——用户浏览器验收
2. **`83a1ac9` push**（网络恢复后·进度文档）
3. **P3 工具管线**（后置·红线区）：依赖图 + 并行执行——两组共识「P3-2 并行后置」（`$n` 索引重构前置·tools.js `_stepResults` 按产出序 push 破坏并行索引）+ 地点联动（P3-4 低风险可做）

## 待续项（下会话从这继续）

- **【核心】整体验收**（todo「整体验收清单」·用户浏览器验收·出口三段式 + 热点图）
- **`83a1ac9` push**（网络恢复）
- **P3 工具管线**（后置·`$n` 索引重构前置）
- **长期 KDE/DBSCAN 替代 Gi\***（热点图 P2/P3 评估）
- **发版就绪度回归**（此前遗留：B3 重跑 + link_checkup + eval 复采 + RST-L06·并发改动后需重验）

## 测试基建

- pytest：**293 passed**（+出口三段式分级/优先级/geo_label + 热点图软分级五档·零回归）
- validate：**28 passed**（test_emc_template + validate_skill_params·含 hotspot 五档契约同步）
- DEM 解码验证：create_terrain_dem terrarium 高度 0~500·峰 500m·bounds WGS84 正确
- 前端语法：node 不可用 → python 括号平衡（全部改动 OK）
- 措辞断言：`py tests/browser/test_gap_wording.py`（3 场景）
- 飞轮：`py tests/browser/flywheel_audit.py --batch B3`（带 `EMOTION_TRACE_SESSION=B3-<批>`）
- 体检：`py tests/browser/test_link_checkup.py`（20 例·回归门）
- 根因分析：`py tools/trace_query.py --stats/--id/--time/--session`（第一动作）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前：**两专题 CB 全闭环**（出口三段式 P0-P2 + 热点图 P0/P1/P1.5·计划+实施各过两组评估/审计·反评价收敛）·CB-16 及之前已闭环
- **双阵营**：claude组（开发主）+ Codex + glm组（评估）
- 反评价轨迹：`docs/catch-ball/cb-journal.md` + `docs/catch-ball/discuss/`（今日 30+ 讨论文档）
- **CB 工作流提醒**：每阶段主动标注「已过 CB→继续推进」vs「需发两组 prompt」（用户会忘本轮是否过 CB）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / **`@track()` 签名 / `_TRACKING_REGISTRY` 格式**（改前先扩 eval·每次一处）·finalStep D019 极瘦（`<3000B`·余量 ~43B·**P1 起冻结模板加字**·学术化走前端）
- **出口抽象层**：不新增 LLM 阶段（撞 D019）·outlet 契约走 tool_contracts 单一源·能/不能双栏诚实·确定性组装
- **CB 机制**：每轮工作进 CB（计划+实施都进·两组评估/审计·先讨论再实施·先验后推）·评估方只读不 git（claude组 负责 git）·prompt 用代码块包裹·**plan/草案也进 CB**
- **数据红线**：改 DATA 需备份 + 用户确认
- **trace 取证**：根因分析先 `trace_query --stats`·推断只作假设
- **EMC 产物不临时创造样式**；不动 FC prompt；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**；commit 后 push（commit+push 组合·push 非红线）

## 恢复指引（新会话·换环境后）

1. `git pull`（fix/emc-buglog·若 `83a1ac9` 已 push 则同步最新）。
2. 读本卡「关键架构」+「待续项」。
3. 读 `docs/todo.md` 08-05 段 + `docs/revision-log.md` §5 最新（含出口三段式 + 热点图条目）。
4. 读 CLAUDE.md「出口抽象层」顶层纲领节 + 「演示逻辑链」北极星。
5. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
6. 从「待续项」继续（核心 = **整体验收**：todo「整体验收清单」）。
