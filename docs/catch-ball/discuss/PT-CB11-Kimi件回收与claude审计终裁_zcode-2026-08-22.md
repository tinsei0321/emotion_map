# PT-CB11 · Kimi 件回收 + claude 审计终裁（zcode 主手·2026-08-22 上午）

> 对象：Kimi K1（d9685861·前端四件）/ K2（99521515·area_stats F_037）+ claude 独立审计报告全部发现。
> 方法：代码逐行审查 + 门禁复跑（38 绿）+ area_stats 真实链复测（R8 独立路径）。

## 一 Kimi 件回收裁决：**通过**（双件·试实力考核=优）

### K1 前端四件（B3-3~B3-6）

| 件 | 审查结论 |
|---|---|
| B3-3 图例 | ✅ 判据改 gridField 语义 + isRange 排除注入层 + `_ui \|\| {}` 空对象兜底（防注入层 TypeError·超出派发规格的防御性加分）+ 注入层标题取层名 |
| B3-4 tip | ✅ map.js 绑定 + tip-popup `ui.choropleth` 最小适配（直取首要素·绕开按 _ui.tool 白名单的 pickCellFeature 过滤·**根因理解到位**）；指标行=value_field 原值（勿走 L2 极性兜底显 0/0/0 误导） |
| B3-5 面板 | ✅ gridField 层隐藏拾色器+换色走重投递提示（§七-7 契约对齐） |
| B3-6 告警 | ✅ 全零 console.warn（字段断裂嫌疑·含 value_field 与要素数）+ paint 透传 valueField |
| 契约条目 | ✅ render-contract §七第 8 条（gridField 判定语义·R22 达标） |
| 自测 | ✅ headless playwright 四口径截图 4 张+脚本已入库（discuss/PT-CB11-Kimi自测-*.png + 脚本） |

### K2 area_stats（F_037）

- ✅ 门禁 38 绿（29+9）；**真实链复测**：admin_district 逐要素 791.11 km²（点军区 533 km²/67.38%·数值合理）；admin_county 分组 14 行 share 合计 97.67%（top10 截断后正确）；G-2 结论层拒绝 ✅；group_by 缺列语义化拒绝（附可用列）✅；零面积语义化拒绝 ✅。
- ✅ 投影 EPSG:4546（照抄 create_square_grid target_crs·宜昌本地 CM 111E·面积差 <1%）；layer_output 前重投影回 4326（渲染正确性细节·加分）。

### 待裁决项裁定：**认可**

「rows 沿 hotspot 先例逐格 _jsonable（_gdf_rows 固定列白名单不含 area_km2/share_pct）」——**认可**。理由：与 Codex hotspot_analysis 同先例（工具自有输出列不硬塞通用白名单）；_gdf_rows 白名单语义=「跨工具通用统计列」，面积列非通用。形成惯例：**新工具自有列逐格 _jsonable·通用列走 _gdf_rows**。

## 二 claude 审计终裁（处置表·编号从 claude 报告）

> claude 报告摘要段与发现段的 P2-1/P2-2 编号互为颠倒（文书小疵）——本终裁按发现段编号为准：**P2-1=grid_aggregate 空集边界（B 件过审条件）·P2-2=render_policy 前缀通配张力**。

| 发现 | 终裁 | 落点 |
|---|---|---|
| P2-1 空集边界（空点层/裁剪零点→int(nan) ValueError→模糊错误或误导「未知层」） | **接受·必修** | Codex P2 批 Phase 1（判空语义化返回+1 用例·5-8 行）→ 合入后 B 件转「通过」 |
| P2-2 前缀通配张力（poi_*/place_* 等任意后缀自动放行·当前零实际外流） | **接受·收紧** | zcode 自修（render_policy 作者·随 P2 批期）：前缀改实际全集枚举 |
| P3-1 renderable_fields 逐字段 manifest IO | 挂账（低频错误路径·可接受） | P3 挂账清单 |
| P3-2 首 3 要素采样可能漏列（提示不完整·非安全向） | 挂账（文案注「部分字段可能未列出」随 P2-2 顺手） | P2 批 Codex 顺手 |
| P3-3 compare_regions KeyError 坍缩 _UNKNOWN_HINT（低概率误导） | 接受·随 P2-1 同款判空 | P2 批 Codex Phase 1 |
| P3-4 hotspot 无 layer_output 用例+空集零用例 | 接受 | P2 批 Codex 补例 |
| P3-5 F_036 号位预留须确保落地 | 接受 | P2 批 Phase 1 首件=nearest（F_036） |
| render_file docstring 未提示面文件显式传 value_field | 接受 | P2 批 Codex 一句注 |
| claude 建议「空集边界列入新工具标准用例模式」 | **采纳为派发单模板条目** | P2 起生效 |

**B 件状态**：有条件通过 → 条件（P2-1）随 P2 批 Phase 1 合入后转**通过**。A 件维持通过。

## 三 claude 审计方法评价（记入 CB 档案）

三条验证路径互证（Codex mock / zcode 真链 / claude pandas 边界实证）——空集边界仅 claude 覆盖=**独立审计价值实证**。双态跑（工作区态 63 绿 vs 纯净 stash 态 54 绿）排除在途污染的方法值得固化为审计标准动作。

---

> zcode 主手 · 2026-08-22 06:5x · Kimi 件通过+claude 终裁落档·P2 批即刻派发
