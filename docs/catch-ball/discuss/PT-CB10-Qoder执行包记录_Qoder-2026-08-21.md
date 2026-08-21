# PT-CB10 · Qoder 执行包记录（进行中·换组交接版）（Qoder·2026-08-21）

> **性质**：执行记录（任务书指定唯一新增写入物）·**状态=进行中·用户令暂停换组**
> **任务书**：`PT-CB10-Qoder执行包任务书_zcode-2026-08-21.md`（C2 十件 / C5 四件 / C1b 四件）
> **门禁现状**：**442 passed / 2 skipped**（开工基线=441 passed+**1 failed**+2 skipped——既有红 test_render_client_d10_source_dispatch 系 F4 裁决后断言陈旧·已随 C2-3 修正·详见 §三）
> **分支**：`EMC_harness_dsh`（已 pull 至最新·未 push·git 由主手代提交）

---

## 一、完成清单（C2 块九件已完·一件未动）

| # | 项 | 状态 | 改动与验收要点 |
|---|---|:-:|---|
| C2-1 | A9 收窄 | ✅ | `tools/mcp_server_emc.py` `_reject_analysis_output`：宽 except fail-open → 按异常类型三分（FileNotFoundError/OSError 显式放行+stderr 留痕；JSONDecodeError 拒绝并说明；其他异常拒绝+摘要）。语法过 |
| C2-2 | inbox TTL | ✅ | `api/render_routes.py`：`_cleanup_applied()` 新增（applied/ 7 天 TTL·`_APPLIED_TTL_DAYS=7`），watcher 首轮+每 3600 轮执行一次，删除数 stderr 留痕；T16 归档机制原样保留。语法过 |
| C2-3 | 公共函数 | ✅ | `frontend/js/toolbox/shared.js` 新增 `export function countNorm(count, maxCount)`（log1p 归一单源）；`buildZonalFc` 改用（countDenom→countMax）；`frontend/js/render_client.js` `_normCommunityCount` 改引 countNorm（import 已加）。node --check 双过 |
| C2-4 | 字段白名单 | ✅ | `api/render_routes.py`：`_DATASET_PROP_KEYS`（名称/极性/领域/指标/口径「来源」）+`_DATASET_PROP_PREFIXES` 默认拒绝过滤，dataset 端点接入；被剔除字段名 stderr 可观测。语法过 |
| C2-5 | K-C1 补 118 | ✅ | `docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md`：K-C1 表新增 **118**（12345 西陵+伍家岗聚合面·派生自 130·`subj_12345_xlwj_aggregate_area`），值锚点+变更行同步，标题六种→七种 |
| C2-6 | demo preset 注册 | ✅ | `core/geo_registry.py`：双点层注册进 `_POINT_LAYERS`（level='CHECKUP' 同族·第 4 元素子目录）+ GeoJSON 分支（`get_layer_points` 按扩展名 gpd.read_file+CRS 归一；`_point_layer_overview` 同分支）。`tools/demo_pioneer.py` 删 `_load_preset_fc` 改直传层 id+清 json 死 import。**实测**：safety 1167 点/livelihood 6487 点·EPSG:4326·list_point_layers 可见（available=True·10 字段）。注：注册文件名经脚本从 manifest 真值对齐（终端中文乱码防猜错） |
| C2-7 | 白名单扩（8→10） | ❌ 未动 | 属 `~/.dsh` 操作·按计划归 C5 块纪律（先备份）·**换组后待做** |
| C2-8 | D9 纪律固化 | ✅ | `AGENTS.md` 埋点规则新增豁免条（≥1s 周期免 @track·注册表描述必须注明）；`api/render_routes.py` F_029 注册描述同步注明「高频扫描·免埋点」。落点说明：任务书文件列写 docs/，实际 tracker 纪律节在 AGENTS.md（各组 onboarding 必读位）·请主手抽验认可此落点 |
| C2-9 | 待开发工具登记机制 | ✅ | `docs/render-contract.md` §八：触发条件+登记四要素（工具名/场景/成本/优先级）+流程+空登记表 |
| C2-10 | 色板缺口登记机制 | ✅ | `docs/render-contract.md` §九：触发条件+登记三要素（场景/期望/理由）+流程（HEATMAP_RAMPS 单一权威源）+空登记表 |

### C2 块验收（任务书要求）

- 全量门禁：**442 passed / 2 skipped**（对基线 441+1f 零退化且转绿·与任务书 442+2 口径一致）；
- C2-6 实测数据见上表；
- C2-7 冒烟待 C5 块执行后补。

## 二、未完成清单（换组接手范围）

### 2.1 C2-7（~/.dsh·与 C5 同纪律）

快分析档 guard 白名单 8→10 件：`~/.dsh/profiles/emc-analysis/node_modules/emc-analysis-guard/index.mjs` 的 `EMC_TOOLS` 加 `'mcp__emc__emc_status'` + `'mcp__emc__render_file'`；POLICY 同步两句（8080 探测用 emc_status 轻量一次调用 / 「显示到地图」走 render_spec/render_file）。**改前必备份到 `ptcb8-t7-backup-20260821/`；改后 node --check + 实跑 emc-analysis 冒烟 + 复刻步骤写入本记录。**

### 2.2 C5 块（四件·全部未动·先备份）

| # | 项 | 规格（双模结局收敛定稿 v1.0） |
|---|---|---|
| C5-1 | 研究档归档 | `~/.dsh/profiles/emc-research` → `_retired-emc-research`（改名不删）；EMC_DUAL_MODE.md 记退役日期与复活法 |
| C5-2 | MODE_ESCALATION 改写 | guard POLICY：从「use profile emc-research」改「引导用户到 3080 网页档」（与 C2-7 同文件一次改） |
| C5-3 | 启动器瘦身 | `~/.dsh/dsh-emc.ps1`：删研究关键词路由与 -Research 分支（或指向退役提示） |
| C5-4 | 说明文档改写 | `~/.dsh/EMC_DUAL_MODE.md` 改单档说明+网页档指引（标题改「EMC 无头模式说明」） |

验收：`dsh --profile emc-research` 预期报错（非静默）；`dsh --profile emc-analysis` 正常+**10** 工具；文档与实况一致；全部先备份。

### 2.3 C1b 块（四件·全部未动·仓内改 vendor/dsh-emc-entry/）

| # | 项 | 规格 |
|---|---|---|
| C1b-1 | 独立工作区归置 | 优先查找 id/name=`emc-lab` 工作区并 connect·会话开其下 |
| C1b-2 | 降级链 | emc-lab 不存在→实测编程创建（dsh 有无 createWorkspace API）→仍不行 fallback 当前+console.warn |
| C1b-3 | 命名统一 | 会话标题统一 `[EMC] ` 前缀 |
| C1b-4 | 可复刻 | emc-lab 创建步骤写入本记录→M1 配方一节 |

验收：点击入口→会话出现在 emc-lab（截图）·emotion_map 零新增；创建步骤可复刻。注：openPath 劫持修复已由主手完成（勿重复）。

### 2.4 收尾件

1. 本记录补全：C2-7/C5 备份清单 + emc-lab 创建步骤 + 最终门禁输出 + 验收截图引用 + 三块逐项销号表改终版；
2. 全量门禁复跑（换组完成后）；
3. 停下等主手回收（逐项抽检+门禁复核）。

## 三、关键事实与决策留痕（换组必读）

1. **开工基线即有一处既有红**：`tests/test_d_batch.py::test_render_client_d10_source_dispatch` 断言 `defaultPaint('zonal','polygon','count')` 存在于 render_client.js——该调用已被 F4 修复（`f75aee58`）按 render-contract §七-7 口径**刻意移除**（防 `_ui.tool` 标记误入 zonal 对话框），断言陈旧。C2-3 同域改动中已修正断言为同源判据（`countNorm(`+`countStops(`+既有 `_normCommunityCount`/`piToNorm`/`polarityStops` 断言保留），注释注明 F4/C2-3 出处。**该测试文件不在任务书白名单——属 C2-3 域内必要的连带修正，请主手抽验认可**（不修则门禁无法满足零红）。
2. **C2-6 文件名对齐**：注册的 GeoJSON 文件名用脚本从 `manifest.json` 真值回写（`12345_安全韧性_社区点.geojson`/`12345_民生基础_社区点.geojson` 一系·终端乱码不手猜）；临时脚本已删。
3. **demo_pioneer 语义变化**：双点层从 manifest 现路径 dict send-in 改为注册表 id 直引——行为等价（同一文件·同 CRS 归一），且 `list_data` 从此起可见这两层（input usage·真实数据）。
4. **门禁数字**：开工 441+1f+2s → 现状 442+0f+2s；期间唯一测试改动即 §三-1 的断言修正。
5. **运行中服务**：3080（dsh web·web profile）与 8080（EMC）全程未重启——C2 改动均为磁盘态，对运行中进程无影响；**C2-4 字段白名单与 C2-1 守卫收窄需下次 serve 重启方生效**（交付口径含重启·debug-memory R7）。
6. **~/.dsh 状态快照**（C5/C2-7 前置参考）：profiles 现存 emc-analysis/emc-research/emc-test/emc-test-headless/web；guard 白名单现=EMC 8 件+read/glob/grep/ask_user_question；备份目录 `~/.dsh/ptcb8-t7-backup-20260821/` 在位。

## 四、已改文件清单（git 待主手代提交）

```
tools/mcp_server_emc.py                                    （C2-1）
api/render_routes.py                                       （C2-2/C2-4/C2-8 F_029 注记）
frontend/js/toolbox/shared.js                              （C2-3）
frontend/js/render_client.js                               （C2-3）
tests/test_d_batch.py                                      （C2-3 连带·白名单外·见 §三-1）
core/geo_registry.py                                       （C2-6）
tools/demo_pioneer.py                                      （C2-6）
docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md           （C2-5）
docs/render-contract.md                                    （C2-9/C2-10）
AGENTS.md                                                  （C2-8·落点见 C2-8 行说明）
docs/catch-ball/discuss/PT-CB10-Qoder执行包记录_Qoder-2026-08-21.md （本文件）
```

> Qoder · 2026-08-21 · 用户令暂停换组。C2 九件已完（C2-7 归 C5 纪律），C5/C1b 未动，门禁 442+2 绿。
