# PT-CB11 · Codex P2-Phase1 + Kimi A-4 回收记录（zcode 主手·2026-08-22 上午）

> 对象：`bf8c2ab3`（Codex Phase 1·空集补丁×2+nearest F_036+overlay F_038+顺手三件+12 测试）+ `6cdf443a`/`4b2e001d`（Kimi A-4 版本徽章三件套）。
> 模式：**zcode+Codex 协同**（用户令 08-22 上午起）——主手审计发现 P1/P2 即顺手修，不再派返。

## 一 Codex Phase 1 裁决：**通过（含主手协同修 2 处）**

### 逐项对账

| 件 | 结论 |
|---|---|
| 空集补丁×2（grid_aggregate+compare_regions） | ✅ 与 claude 审计条件逐字对齐——**B 件（3f9e55a4）过审条件就此满足，转「通过」** |
| nearest_analysis F_036 | ⚠️ 审出 P1+P2（下表）·主手已修+回归测试 2 例 |
| overlay_analysis F_038 | ✅ how 枚举/G-2 双侧/空集语义拒绝/name_a-name_b 列隔离（防同名列后缀冲突·加分设计）/4546 面积/top_n cap |
| 顺手三件 | ✅ hotspot layer_output 用例/render_file docstring 注/提示「部分字段可能未列出」（P3-2） |
| 12 测试 | ✅ 74 绿（53 mcp+19 render+2 主手新增） |

### 主手协同修（P1/P2·已入库随本批 commit）

| 级 | 发现 | 修复 |
|---|---|---|
| P1 | 面 target 崩溃：矩阵法 `.geometry.x` 只支持 Point——resolve_boundary 面层 fallback 形同虚设（`x attribute access only provided for Point geometries`→通用 except） | `_to_metric` 增非 Point 几何 `representative_point()` 适配（落面内·比 centroid 稳）；实测 admin_district target→伍家岗区 117.8m ✓ |
| P2 | 距离矩阵 O(n_a×n_t) 无预算守卫：此前 17418×27717≈4.8 亿配对「成功」实为**静默分配 ~7.7GB 中间矩阵**（本机跑过≠可依赖·双环境更险） | `_PAIR_BUDGET=5e7` 前置守卫（约 1.2GB 上限）·超限语义化拒绝并引导「先 grid_aggregate/zonal 降密度」 |

### 观察项（不阻塞）

- 大点层锚点无 place_name → pairs 显 `anchor_13689` 类索引（诚实降级·可用性低）——hint 已引导换命名层；chunked argpartition 算法优化列 P2 Phase 2 可选项。
- F_036/F_038 注册连续（F_037 Kimi 已落·F_036 空洞补上·铁律 10 闭环）。

## 二 Kimi A-4 裁决：**通过**

- `/version` 端点实测（8080 现网）：`{"commit":"bf8c2ab3","branch":"EMC_harness_dsh","startup":"..."}` ✓；commit/branch 启动时缓存一次 ✓；subprocess 失败具体捕获降级空串+WARN（A9 合规）✓。
- 前端角标+横幅：render_client.js 追加段与 B3-6 段无冲突；隔离栈 8090/8009 实测三证据截图入库（discuss/PT-CB11-Kimi自测A4-*.png）；+1 测试 ✓（19 绿）。
- A-4c 横幅「首访只记录不打扰」=细节加分。
- **验收即用户可见**：8080 左下角 v 角标现已生效（serve 06:54 起的进程已载入端点代码）。

## 三 蒸馏

已蒸馏 **R23**（空间工具对输入层的隐式假设——几何类型/规模预算——必须显式守卫）·见 debug-memory。

## 四 后续

- Codex Phase 2 即刻派发（trend F_039+report_assemble F_040+guard 迁 server·协同模式继续）。
- zcode 在途：render_policy 前缀通配收紧（claude P2-2·本批内完成）。
- Kimi 暂停派发（用户令·额度 13:00 恢复）——A-4 已收完无挂账。

> zcode 主手 · 2026-08-22 07:1x · 协同模式首轮回收
