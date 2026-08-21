# PT-CB11 · Kimi 派发 prompt（首批执行：注入图层补链四件 + area_stats 工具件）

> 主手：zcode。用户拍板（2026-08-21 深夜）：Kimi 两件都派（B-3 前端 + area_stats）——试实力双考（前端视觉件 + 后端工具件）。
> 派发依据：任务书 `PT-CB11-MCP工具丰富化与注入链路补全_任务书_zcode-2026-08-21.md`（先读 §一根因链）。
> 转发方式：把下方代码框整段复制给 Kimi。

---

```
【PT-CB11 · Kimi 首批执行：注入图层补链四件（前端）+ area_stats 工具件（后端）】

你是 Kimi，「情绪地图（EMC）」项目组成员。本次是你首批执行任务（双件试实力）：
任务 A = 前端四小件（视觉验收·用户直接感知）；任务 B = 后端一件 MCP 工具（契约工程）。
先做任务 A（见效快），再做任务 B。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【开工准备】

环境：git pull 最新分支 EMC_harness_dsh（仓库 D:/Github/emotion_map·如无则 clone
https://gitee.com/tinsei0321/emotion_map · 分支 EMC_harness_dsh）

必读（按序·约 15 分钟）：
1. docs/catch-ball/discuss/PT-CB11-MCP工具丰富化与注入链路补全_任务书_zcode-2026-08-21.md
   —— 本批任务书·重点读 §一（B-3 根因链·你要修的就是它）和 §二（工具通用规格）
2. docs/render-contract.md —— 渲染契约（§七 结果呈现契约·换色走重投递的既定约定）
3. AGENTS.md 编码铁律段 —— 禁 emoji·_safe_print·追踪埋点纪律

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【任务 A · 注入图层补链四件（前端·B3-3 ~ B3-6）】

背景（一句话）：dsh 经 MCP 渲染的 choropleth 注入图层显示为「灰色框+无填充」、
无标准图例、参数面板调色无效。根因=注入层不带 _ui.tool 标记（这是故意的·
PT-CB8 F4 修复），而图例/悬停/面板全按 _ui.tool 白名单判定 → 注入层全部漏判。
数据侧断裂（白名单字段/字段错配）由 zcode 并行修复中，与你无关——你只改前端判定。

四件规格（每件都小·合计约 4 文件·各 1-10 行）：

B3-3 图例判定改语义（frontend/js/sidebar.js）
  - 现状 :222-223：色带图例（legend-grid）只认 l.paint._ui.tool ∈ {grid,terrain,density}
  - 改为：paint.gridField 存在即数据驱动 choropleth → 显示色带图例
    （与 map.js:810/:841 的 F4 修复同判据——语义统一）
  - 顺修 :203-204：isRange 判定排除带 gridField 的层（现在会误显线框图例）

B3-4 悬停 tip 绑定（frontend/js/map.js）
  - 现状 :650-652：富 tip（bindTipPopup）只绑 _ui.tool ∈ {grid,terrain}
  - 改为：绑定条件加 || p.gridField
  - 注意：先验证 tip-popup.js 对无 _ui 层取字段的兼容性（不兼容则做最小适配·
    取 name/社区 等可读字段·勿大改）

B3-5 参数面板防误导（frontend/js/settings.js）
  - 现状 :100-101 polygon 分支：拾色器对数据驱动 fill 无效（fill 恒为表达式）
  - 改为：gridField 层禁用/隐藏拾色器，附提示文案
    「数据驱动着色·换色请重投递 spec」（换色走重投递是既定契约·不是缺陷）

B3-6 全零可观测（frontend/js/render_client.js）
  - _normCommunityCount（:58-73）：归一后全零时 console.warn
    （含 valueField 名与「字段断裂嫌疑」提示）——下次断裂 30 秒定位

自测方式（不依赖 zcode 的后端修复）：
  py frontend/serve.py 8080 起服务 → 用 MCP 内联 geojson 投递一张带 point_count
  的 choropleth spec（内联路径不过后端白名单·立即见效）：
    python -c "import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'.'); \
import mcp_server_emc as m; print(m.render_spec(kind='choropleth', \
name='Kimi自测·方格热度', value_field='point_count', geojson={'type':\
'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Polygon',\
'coordinates':[[[111.2,30.6],[111.25,30.6],[111.25,30.65],[111.2,30.6]]]},\
'properties':{'name':f'格{i}','point_count':i*10}} for i in range(1,6)]}))"
  刷新 8080 页面 → 应看到：色带图例（B3-3）+ 悬停显数值（B3-4）+ 面板不误导（B3-5）。
  （灰框问题本身是数据侧的·zcode 修·你只管图例/tip/面板/告警四件）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【任务 B · area_stats 工具件（后端·tools/mcp_server_emc.py·F_037）】

规格（函数级·零判断执行·与真身签名不符处停手记「待主手裁决」）：

register_track_id('MOD_AIQA.F_037', 'MCP area_stats（面积占比统计·group_by 分组·km2）')

@track('MOD_AIQA.F_037', track_args=False)
def area_stats(boundary: str, group_by: str = '', top_n: int = 10,
               layer_output: bool = False) -> dict:
    """面积占比统计：面层按要素/分组字段算面积与占比（结构量化·非情绪归因）。
    参数：boundary 必填 preset id（先 list_data）；group_by 给出则按该字段 dissolve 分组汇总；top_n 1-20；layer_output=True 增 geojson。
    限制：只算面积结构——情绪结论用 zonal_stats/rank；投影面积与椭球面积差异 <1% 级。"""

backing 链（参照 zonal_stats :390-440 范式）：
1. _reject_analysis_output(boundary, 'boundary', CALIBERS['area_stats'])
   + resolve_boundary(boundary)（core.geo_registry）
2. 面积：投影到米制 CRS 再算——先查仓内 create_square_grid（core/spatial_analysis.py:806）
   的 target_crs 用法照抄同一投影 → g['area_km2'] = g.geometry.area / 1e6
3. group_by 给出：dissolve(by=group_by) 按类汇总（面积和+share_pct=类面积/总面积）
   缺省：逐要素面积 + total_km2
4. rows = _gdf_rows(...) 按面积降序 head(top_n)；
   layer_output → _layer_output_geojson(g, top_n, 'area_km2')
5. caliber = {'scale': '宏观/中观（面积结构）', 'semantics': '面积与占比统计（结构量化）',
   'limits': '非情绪归因——情绪结论用 zonal_stats/rank；投影差异 <1%', 'refs': ['K-C1']}

契约同步（铁律 11·三处）：本件是新 MCP 工具（非 generate*ForAI），契约源 =
ai_qa/tool_contracts.py 的 area_stats skill（:191）——参数名 boundary/group_by
与契约一致（panel_source 已标 Area-stats dialog）·无需改三处镜像。
通用规格必守：纯只读/惰性导入/_safe_print/caliber 四键/rows≤20/200KB 硬顶/
五判据一行答辩（结构化/口径内建/脱敏自动/错误语义化/组合性）。

测试：tests/test_mcp_server_emc.py 新增 ~8 用例（范式沿
test_zonal_stats_rows_cap_row_count_and_caliber）：正常链（monkeypatch
resolve_boundary）+ G-2 拒绝 + group_by 缺列语义化拒绝 + top_n cap + 面积数值断言。

⚠ 同文件并行：Codex 并行在 mcp_server_emc.py 取了 F_033-F_035（三件工具）·
你只加 F_037（F_036=nearest 留给后批·勿占）。改动面=模块顶部 register_track_id
段加一行 + 新增 area_stats 函数（建议放 rank 与 _dataset_meta 之间）+
build_server() 注册一行。禁改任何既有函数体。若 pull 后见 Codex 的 F_033-F_035
已提交，你的 F_037 行接在其后；register 段冲突=几行事·rebase 解决。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【纪律与交付】

- 代码禁 emoji（只许 ASCII 标记 [OK]/[WARN]/[ERR]）；print 走 _safe_print；
  禁宽 except 静默（A9）；纯只读零写盘（area_stats）
- 分支 EMC_harness_dsh（main 冻结）；commit 前缀 PT-CB11(K1):（任务A）/ PT-CB11(K2):（任务B）
- 显式路径 commit·禁 add -A
- python -m pytest tests/ -q 全绿（基线 444·上浮注明）
- 执行记录落盘 docs/catch-ball/discuss/PT-CB11-Kimi执行记录_Kimi-2026-08-21.md
  （含：五判据答辩·自测截图说明·遇到的不符签名处）
- 用户复测四口径（任务 A 验收）：标准色带图例 / 悬停显数值 / 面板不误导 /
  控制台全零告警——修完在执行记录里给「复测指引」一段（用户照做）
```

---

> zcode 主手 · 2026-08-21 深夜 · Kimi 首批双件派发
