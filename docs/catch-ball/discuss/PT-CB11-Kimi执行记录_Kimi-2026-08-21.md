# PT-CB11 · Kimi 首批执行记录（任务A 前端四件 + 任务B area_stats）

> 执行：Kimi（WorkBuddy）· 2026-08-21 深夜 · 分支 EMC_harness_dsh  
> 派发：`PT-CB11-Kimi派发prompt_zcode-2026-08-21.md` · 任务书：`PT-CB11-MCP工具丰富化与注入链路补全_任务书_zcode-2026-08-21.md`  
> commit：`PT-CB11(K1):`（任务A 前端 5 文件 + 契约条目）/ `PT-CB11(K2):`（任务B 工具+测试+本记录）

---

## 一 结果速览（四口径全过 + 工具九测全绿）

| 件                | 状态 | 证据                                                                                                                      |
| ---------------- | -- | ----------------------------------------------------------------------------------------------------------------------- |
| B3-3 图例判定改语义     | ✅  | sidebar.js 判据改 `paint.gridField`；自测截图①右下角标准色带图例（标题=层名·低/高标签）                                                            |
| B3-4 悬停 tip 绑定   | ✅  | map.js 绑定条件加注入分支；tip-popup 最小适配；截图②浮卡显 `point_count 30 / 名称 ge3 / 地点反查`                                                 |
| B3-5 面板防误导       | ✅  | settings.js polygon 分支 gridField 层隐藏拾色器；截图③显提示「数据驱动着色·换色请重投递 spec」，面开关/线宽/透明度保留                                         |
| B3-6 全零可观测       | ✅  | render_client.js 归一全零 console.warn；自测控制台实捕 `[dsh] choropleth 归一全零（字段断裂嫌疑）: value_field = point_count \| 要素数 = 5 \| ...` |
| F_037 area_stats | ✅  | 9 用例全绿；全量门禁 467 passed, 2 skipped（基线 444·+23 含本批 9 件与 Codex/zcode 在途新增）                                                 |

## 二 任务A 改动面（5 文件·各 1-10 行·与派发规格对齐）

1. **sidebar.js**：`isRange` 增 `&& !paint.gridField`（防注入层误显线框图例）；legend-grid 判据改 `paint.gridField || _ui.tool ∈ {grid,terrain,density}`（与 map.js:810/:841 F4 同判据）；块内 `ui = paint._ui || {}` 兜底（原代码 `grid.paint._ui.polarity` 对注入层必抛 TypeError）；注入层图例标题取层名（无工具归属可显）。
2. **map.js**：polygon 分支绑定条件改 `_tool ∈ {grid,terrain} || (!_tool && paint.gridField)`；注入层以 `uiOverride={choropleth:true, valueField}` 调 bindTipPopup；`_ui.mode` 访问加 `_ui &&` 守卫（注入层 \_ui 缺省）。
3. **tip-popup.js**（最小适配·勿大改）：onEnter/onMove 要素拾取对 `ui.choropleth` 直取 `e.features[0]`（pickCellFeature 按 \_ui.tool 白名单过滤·注入层必漏）；metricText/sizeText 增 choropleth 分支——指标行=value_field 原始值，次行=name/社区 可读字段（不走 L2 极性 0/0/0 与「网格边长 —」兜底）。
4. **render_client.js**：两款 choropleth paint 增 `valueField` 透传（tip 指标行取原始字段名）；`_normCommunityCount` 归一恒零 console.warn（含 valueField/要素数/断裂嫌疑提示）。
5. **settings.js**：polygon 分支 `p.gridField` → 拾色器替换为 `.set-note` 提示文案（render-contract §七-7 的 UI 落地·换色走重投递是既定契约非缺陷）。

**契约同步**：render-contract.md §七 增第 8 条「注入层图例/悬停/面板判定 = gridField 语义·非 \_ui.tool 白名单」（批级 DoD·R22 条目产出，随 K1 提交）。

## 三 自测方式与截图说明（不依赖 zcode 后端修复·内联路径）

1. 8080 服务已在跑（用户侧常驻）→ `render_spec` 内联投递 5 格 `point_count=10..50` 方格（宜昌 111.2-111.5E/30.6N）→ 页面刷新即染。
2. headless playwright 脚本 `_tmp/pt_cb11_kimi_selftest.py`（未提交·临时件）自动开页→截图→悬停→开面板→再投全零 spec→捕控制台。
3. 截图（未提交·本机 `_tmp/`）：
   - `kimi_b3_1_map_legend.png`：5 格浅橙→深红连续梯度填色（非灰框）+ 右下角 legend-grid 色带图例（标题 `[dsh] [真实] Kimi selftest grid heat`·低/高）。
   - `kimi_b3_2_tip.png`：悬停中间格浮卡=地点反查（伍家岗区·伍家乡·畔山明月）+ `point_count 30` + `名称 ge3`。
   - `kimi_b3_3_panel.png`：要素按钮面板=填充面域开关 + **提示文案（无拾色器）** + 线宽/线型/填充透明度 72%。
   - `kimi_b3_4_zero.png` + 控制台捕获：全零 spec 触发 B3-6 warn 原文命中「字段断裂嫌疑」。
4. 页面 JS 报错审计：仅存量 `time-source manifest 404`（与本批无关·time-source.js 拉取既有问题）+ headless 环境外网瓦片超时；**零本批改动引入的报错**。

### 复测指引（用户四口径·照做即可）

1. 刷新 8080 页面（确保最新 JS）；在 3080/dsh 问「12345 诉求最密集的 5 个社区，显示在地图上」（zcode B3-1/B3-2 合入后走 dataset 路径）或直接投任意内联 choropleth spec。
2. **口径①标准色带图例**：看左栏图例区出现横向色带（legend-grid），标题=层名，低/高标签——不再是空白或线框图例。
3. **口径②悬停显数值**：鼠标悬停任一填色面→白色浮卡显 value_field 数值+名称+地点（不再是仅层名简 tooltip）。
4. **口径③面板不误导**：点该层「面」要素按钮→颜色位是提示文案「数据驱动着色·换色请重投递 spec」而非拾色器；面开关/线宽/透明度仍可调。
5. **口径④控制台全零告警**：F12 Console——若再有字段断裂（值全零），30 秒内可见 `[dsh] choropleth 归一全零（字段断裂嫌疑）: value_field = ...` 黄条。

## 四 任务B · area_stats（F_037）实现与五判据答辩

**落位**：register_track_id 接 F_035 后（F_036=nearest 留后批·未占号）；函数置 hotspot_analysis 与 `_dataset_meta` 之间；`build_server()` 注册一行；**零既有函数体改动**（与 Codex F_033-F_035 同文件无冲突）。

**backing 链**：`_reject_analysis_output`（G-2）→ `resolve_boundary` → 投影 EPSG:4546（照抄 `create_square_grid` target_crs·宜昌 CM 111E 米制）→ `g.geometry.area / 1e6` → group_by 给出则 `dissolve(by=...)` 分组汇总 → share_pct=类面积/总面积 → 降序 head(top_n≤20) → `layer_output` 复用 `_layer_output_geojson`（200KB 硬顶·回投影 4326）。纯只读零写盘·重依赖惰性导入·caliber 按派发原文四键。

**五判据一行答辩**：

1. **结构化输出**：rows（name/group 值+area_km2+share_pct）+ total_km2 + row_count/truncated——宿主零解析直用 ✓
2. **口径内建**：caliber 明写「非情绪归因——情绪结论用 zonal_stats/rank」+ 投影差异 <1%·裸调 geopandas 无此护栏 ✓
3. **脱敏自动**：boundary 经 manifest usage 检查（G-2 结论层拒绝）·只输出面积结构数值零 PII ✓
4. **错误语义化**：group_by 缺列报「可用列清单」·未知 preset 报「list_data 引导」·零面积报原因 ✓
5. **组合性**：boundary preset id 与 list_data/zonal_stats/rank 同命名空间·layer_output geojson 可直接喂 render_spec 出图 ✓

**测试 9 用例**（tests/test_mcp_server_emc.py 尾部·范式沿 zonal/grid/hotspot）：注册断言 / 正常链+降序+占比和 / 面积数值断言（0.01° 方格 @111E·30N ≈1.067km²·容差 6%）/ group_by dissolve 汇总 / 缺列语义化拒绝 / top_n cap+layer_output / G-2 结论层拒绝 / 未知边界 hint / 零面积拒绝。

## 五 与派发规格的不符处（停手记·待主手裁决）

1. **rows 构造未走 `_gdf_rows`**（派发 §任务B 步骤4 原文「rows = \_gdf_rows(...)」）：`_gdf_rows` 列白名单固定（name/point_count/polarity_index/...），area_km2/share_pct 会被滤光；纪律又禁改既有函数体 → 沿 hotspot_analysis 先例（:706）逐格 `_jsonable` 构造。**影响**：行为符合预期（测试锁定）；若主手希望统一走 `_gdf_rows`，需其扩列白名单参数（建议 P2 批顺手收）。
2. **git pull 未能刷新远端**：本环境 bash 无 gitee 凭据（credential helper=helper-selector 需交互弹窗）→ 以本地 origin/EMC_harness_dsh（0fb5d604）为基线开工。若远端有更新（如 zcode B3-1/B3-2 后续提交），push 前需用户在本机跑一次 `git pull --rebase`。
3. **契约三处镜像**：核对 `ai_qa/tool_contracts.py:191` area_stats skill——参数名 boundary/group_by 与实现一致·无需改动（与派发判定一致）；top_n/layer_output 为 MCP 侧通用附加参数（与 zonal_stats/rank 同款·契约「可少不可多」不违）。

## 六 纪律自查

- [x] 代码零 emoji（ASCII 标记 [OK]/[WARN] 仅既有件）；后端 print 走 \_safe_print（本件无 print）
- [x] 禁宽 except 静默：area_stats 两档捕获（KeyError/FileNotFoundError→引导 hint；Exception→带因 hint）与既有工具同款
- [x] 纯只读零写盘（area_stats）；前端四件零副作用外溢
- [x] 显式路径 commit·禁 add -A；分支 EMC_harness_dsh；前缀 PT-CB11(K1)/(K2)
- [x] pytest 全绿：467 passed, 2 skipped（基线 444·上浮 +23 已注明）
- [x] F 号连续：F_037 注册·F_036 留给后批未占
- [ ] push：凭据环境受限·待用户本机 push（见 §五-2）

> Kimi · 2026-08-21 深夜 · PT-CB11 首批双件交付·待用户复测四口径
