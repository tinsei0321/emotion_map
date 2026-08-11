# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月11日 晚（office 环境·紧急任务城市体检两板块·数据/工具/管线全就绪·收工回家换环境）| 分支 `main` @ 7dad0324
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/zcode组 评估**·glm组 2026-08-11 正式更名 zcode组）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md`（家）+ `OFFICE.md`（公司）

## 当前节点：紧急任务·城市体检两板块分析（阶段 0-2 完成·数据/工具/管线全就绪·就差出图数表讨论）

08-11 大轮（跨项目工程·城市体检两板块·双项目交叉）·定稿五阶段推进：

### 阶段状态（对照 `C:\Users\Administrator\.claude\plans\emc-rag-emc-wise-lark.md`）

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0' 对接层 | DATA/exchange 三分法 + PII 例外 + 口径对齐 + MOD_CHECKUP | ✅ 完成 |
| 1' checkup 适配器 | WGS84 透传·无 LLM·L2 旁路·图层注册（后端扩展 A1-A8 + 12345 层 + 项目层） | ✅ 完成 |
| 2' RAG 优化 | fact 卡 + 索引重建 + outlet_kb 客观轨 | ✅ 完成 |
| 3' 两板块分析 | 图/数/表/观点 | 🔄 **未开动·就差出图数表讨论** |
| 4' 分析报告 | 图/数/表 + 口径对照 + 缺口 + 出口卡 | ⬜ 3' 后·不等边界 |

### 数据/工具/管线全就绪（今日核心成果）

- **12345 治理**（57265 行·用户提供 `2024年12345投诉数据_raw.xlsx`）→ `06_主观数据治理/` 治理清洗版 + 情绪地图中转版（polarity 5级/score 0~1/4×5/topic/place/region_scope/cross_region）·**PII 干净**（车牌 0/人名 0·容忍空格）·**噪声 0.05%**
- **geocode 回填**（clean 地名 80% 命中·region 质心兜底·离群过滤）·注册 `checkup_12345_2024` 层（18171 有坐标·中心城区 77%）
- **项目端**（十五五储备表 excel 183 项目 + 重点项目 gdb point185+line102=183·**gdb 只读**导出 GeoJSON·excel 匹配 99%）·注册 `checkup_project_point/line`
- **官方行政数据**（市域县级 14 县区 + 村社区 1682 shp·SSX 聚合 113 街办含 16 街办口径）·admin_street/community/county 注册·社区 94MB reference_only·**街办 zonal 打通**（宝塔河 3066）
- **数据质量修复**（两组全局审计·Codex 2P0/8P1/12P2 + zcode 3P0/12P1）：双高格 16·cross_region 664·extract_event 0.05%·16 街办对齐·趋势聚拢标注
- **管线测试 6/6**·**双轨密度完整版**（双高格 16）·**趋势聚拢验证**（12345→项目 57%/81% 落高密度格）
- **街办术语统一**（街道→街办·全局·CLAUDE.md 铁律）·**三组犯错统计**（claude≈87%/Codex≈29%/glm-zcode≈77%·更名合并）
- pytest **320 passed 零回归**

## 关键架构（下会话须知道）

- **城市体检两板块**：安全韧性底线（结构42/围护454/楼道240/燃气6/管线186 + 250危旧房 + 50年建筑 + 消防20.59%）·民生基础需求（停车2.99万/学位6603/托育34/幼儿园11/养老2 + 中学/公园/菜市场覆盖）
- **双轨架构**：客观轨（体检·02 空间层）+ 主观轨（12345·checkup_12345_2024 层）→ 双轨密度叠加 → 双高区 → 项目聚拢 → 三片区统筹
- **分析不依赖片区边界**（CLAUDE.md 铁律 7·片区=结论·问题聚集推导·倒推不外显）·边界供团队整合（其他人分析叠加）
- **出图数表讨论基础**（已备）：图1-4 呈现链（问题分布→双高区→项目聚拢→片区统筹）·2×3 矩阵汇报框架（客观/主观 × 安全韧性/民生·数量可调）·Codex 方案 A（双板块×双轨×三片区趋势聚拢）
- **数据源红线**：全部中转站真实数据·sim 模拟禁入（checkup_* 层 whitelist）

## 【下一步】（回家后·出图数表讨论 + 3' 分析）

1. **出图数表讨论**（当前唯一门槛·定稿后 3' 开动）：图1-4 呈现链·2×3 矩阵·分析内容×方法×结果形式·Codex 方案 A
2. **3' 两板块分析**（不卡边界·问题→项目趋势聚拢→三片区统筹）
3. **4' 分析报告**（图/数/表/观点 + 口径对照 + 缺口清单 + 出口卡对接）
4. 阶段 2' RAG 索引重建（若新数据·`py tools/rag_index.py --rebuild`）

## 测试基建

- pytest：**320 passed + 3 skipped 零回归**
- 12345 治理重跑：`py SCRIPT/govern_12345_raw.py`（含自动回填 geocode）
- geocode 回填：`py SCRIPT/backfill_12345_geocode.py`（cross_region 标记）
- 双轨密度：`py SCRIPT/dual_track_density.py`（双高格 16）
- **自测前必须重启 serve**（`py frontend/serve.py 8080`）·否则跑旧代码

## CB 状态

- 当前：**CB-23 数据质量闭环 + 官方行政数据 + 街办术语统一 + 三组犯错统计**（两组审计全回收·P1/P2 全处理·push 完成）
- 双阵营：claude组（开发主）+ Codex + **zcode组**（评估·glm组 更名）
- 反评价轨迹：`docs/catch-ball/cb-journal.md` + `docs/catch-ball/discuss/CB23-*`（全系列）
- **CB 工作流提醒**：每阶段主动标注「已过 CB→继续推进」vs「需发两组 prompt」·prompt 发给谁由用户提示（codex/zcode 分工）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / `@track()` 签名 / `_TRACKING_REGISTRY` 格式 / finalStep D019 极瘦 / **CLAUDE.md 铁律 7（片区=结论·分析不预设片区）**
- **数据源**：中转站真实数据·sim 禁入·gdb 只读（用户明确·勿动）
- **不造轮子**：复用 create_square_grid/aggregate_by_polygons/hot_spot_analysis/geo_registry/rag_index
- **追踪编号连续**：新增公开函数 `register_track_id`·先 grep 全仓取最大 +1
- **CB 机制**：每轮进 CB·评估方只读不 git·prompt 用代码块包裹·**prompt 发给谁由用户提示（非两组一起发）**
- **街道≠道路**（街道=行政单元·admin_street 非路网线）·**术语统一「街办」**
- 代码禁 emoji·print 走 `_safe_print`

## 恢复指引（新会话·换环境后）

1. `git pull`（对齐远端 main）+ 读本卡（读交接卡前先 git log -5 对账·防漂移）
2. 读 `docs/catch-ball/_cb-index.md`（当前 CB-23）+ `docs/todo.md` 08-11 段 + `C:\Users\Administrator\.claude\plans\emc-rag-emc-wise-lark.md`（定稿）
3. 读 CLAUDE.md「出口抽象层」+「演示逻辑链」+「空间落位口径铁律 7」
4. 数据链路：`06_主观数据治理/`（12345 治理）·`02_空间数据集/行政区划_官方/`（官方街办）·`DATA/performance/checkup_12345_2024.csv`（12345 层）
5. 从「下一步」继续（**出图数表讨论 → 3' 分析**·数据/工具/管线已就绪）
