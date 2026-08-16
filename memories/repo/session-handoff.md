# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月16日 深夜（CB-39 双线实施·P0 线+A 线完成·收工）| 分支 `codex/dsh-onboarding`（已 push·最新 `2317785d`·origin 已切 Gitee）
>
> CB 入口：`docs/catch-ball/_cb-index.md`
> 角色（08-16 起）：**Codex = 主开发（唯一 git 写者）**·claude组 = 第三方评估+收敛方·zcode组 = 评估。**dsh组 已退出（08-16·用户通知）**。
> 换机卡片：`docs/catch-ball/_handoff/HOME.md`（家）+ `OFFICE.md`（公司）

---

## 当前节点：CB-39 双线实施 · P0 线（已验证）+ A 线（A1-A5）完成 · 待 B 线治理

### 08-16 全天脉络（CB-38 收官 → CB-39 开工）

1. **CB-38 收敛**（两条输入线）：数据沉淀收敛定稿（三组评估·4 裁定·第八节补遗 E16）+ EMC 全局系统审计（另一 Codex 会话产出·claude组 反评价 D1-D9 全裁定）→ **合并为 CB-39 双线实施计划 v3.1**（`discuss/CB39-实施计划_Codex-2026-08-16.md`·24 批·两组反评价 18 处修订全落）。
2. **P0 线实施完成 + claude组 验证「有条件通过·零打回」**（`CB39-P0线验证_Claude-2026-08-16.md`·3 吸收项已落 `a112dccb`）：
   - P0-2 守卫通电：9 个 `validate_*` 进 pytest 收集 + **15 个 ID 原号补注册**（审计 4 + MOD_PERF 11·动态循环改字面量）+ SKILL_DEFS 真身解析（**当场抓出 compare 漂移**·contracts=权威）+ 新闸门「使用 ID ⊆ 注册表」+ 3 存量红全修零 xfail
   - P0-1 诚实度：phase 真实标签（`df.attrs`·不再硬编码 L4）+ key 空显式报错拒静默降级 + L4 stub 显式跳过标注 + L0 四 spider 隔离 `SCRAPER/experimental/` + routes key 打通 L3/L4 + `test_pipeline_honesty.py` 三断言
   - P0-0：KNOWLEDGE 密钥条款（只输出 key 名）已落；**key 轮换用户暂缓**
3. **A 线（阶段0 回收归集）A1-A5 完成**：
   - A2/E16：performance 六件真实数据迁出演示池（checkup_12345_2024 → `DATA/analysis/12345主观/`·57,265 行完整）+ geo_registry 子目录字段向后兼容 + D2 数据池归一（PROCESSED_DIR→`DATA/exports` 单源·data_governance 双源根治·空 DATA/processed 删）+ `DATA/README.md` 池规则
   - A3：根 5 散件族内归位（根目录仅剩 7 空间底座）+ cb33 临时脚本×4 按 E6 退役
   - A4：page7 九件归档 `_retired/`（改名保史）+ E10 双变量主图退役 + README 版本口径链
   - A5：**《紧急任务数据总账》`DATA/analysis/_总账.md` 100 行**（族/来源 commit/去留/口径/去向）+ 可复跑生成器 `SCRIPT/_ops_gen_ledger_cb39.py`
4. **里程碑**：`DATA/performance/` 只剩 sim——时间轴专题轮分轴物理前提备好（D3 已冻结·用户定调另开专题轮）。
5. **基线演变**：321+3 → **366+3**（P0-2 守卫 +42 / P0-1 断言 +3 / pii 目录副作用治愈后为干净基线）。门禁钉死 `py -m pytest`（禁裸 python=3.13 缺 matplotlib）。

### 本日 commit（均已 push）

`713e1ad9` P0-2+P0-0 → `7b2c3ead` P0-1 → `9ceff715` CB 归档 → `a112dccb` 吸收修正 → `a5449175` A2 → `209de0a4` A3 → `b9e9e3de` A4 → `2317785d` A5

---

## 【下一步】（CB-39 续·按 v3.1 计划）

1. **B 线治理**：B1 presets 补注册+usage 铁律7 机械化（12345 点层/page7 点版/18村面/底座 group）→ B2 同名三对四证据对账（挂起区见总账）→ B3 口径注册表+`tools/check_caliber.py` 复核门（MOD_AIQA.F_020 起取号）→ B4 PII/sim/铁律7 全量复检
2. **C 线沉淀**：C1 domain 三域+存量 214 回溯（3prime 四件标 superseded）→ C2 体检 fact 增量（CHK 续编）→ C3 图层卡 26+ → C4 E14 白名单硬实现 → C5 rebuild+E12 指纹+**E15 黄金问题（用户 gate·候选见计划附B）**
3. **并行 bug 线**：D1 B002/B004 白名单裁定（v1 收窄版：图层名+observation 格式）·D2 B012+B013 同场修（B013 条目未建）·D4 E2 纯色底图+GeoQ spike
4. **工程线插空**：P1-2b gen_agents_table（机械/人工分区）·P1-3 双入口/Threading+api.js 适配·P1-4 可见性·P1-6 README 重写；**P1-5（3.14）位置固定 R1 前**
5. **挂起项**：key 轮换（用户暂缓）·E7 office 机 Gitee 换绑（origin 已切 gitee·到岗 set-url 即可）·时间轴专题轮（D3 冻结）

---

## 关键架构（下会话须知道·承重）

- **CB-39 双线**：数据线（回收 A✅→治理 B→沉淀 C→归档 R1）+ 工程线（P0✅→P1）+ bug 线 D 并行；唯一现行计划 `discuss/CB39-实施计划_Codex-2026-08-16.md`（v3.1）
- **数据池三分**（`DATA/README.md` 单源）：`analysis/`=真实归集根（100 件·总账为准）·`performance/`=演示池（仅 sim·真实禁入）·`exports/`=运行导出（不入 git）；boundaries/presets=图层注册；exchange=G 盘溯源
- **双轨架构**：客观轨（体检）+ 主观轨（12345·checkup_12345_2024 层·已迁 analysis/12345主观/）→ 双高区 → 项目聚拢
- **空间落位口径铁律7**：4 维度控件对象=第一性落位；片区=结论禁作输入；结论层（合并范围/聚合174/18村/page7 三组）标 `usage: analysis_output`
- **城市体检 vs 城市更新分域**（08-16 用户铁律）：体检=找问题/需求数据·更新=规建营项目数据；RAG domain 三域封顶（checkup/renewal/base）
- **出口抽象层三铁律** + **演示逻辑链**（CLAUDE.md·不变）
- **守卫已通电**：pytest 收集 9 个 validate_*；新闸门=使用 ID ⊆ 注册表；SKILL_DEFS 真身解析（改 stages.js 会被守卫抓）

## 隐规则清单（主开发必守·完整在 AutoMemory）

- 实事求是纪律（最高）：不附和·不为字面要求硬做错事
- 风险主题命名「XX安全」后缀·数据层字段不改；每页重构=重构+数据审计；排行 top10·0 值不列；「以及」仅分隔社区与村；专业词+通俗解释；交付物全中文；沟通=框架+条目+总结

## 测试基建

- pytest：**366 passed + 3 skipped 零回归**（阶段基线·P1-5 后重录）；门禁 `py -m pytest tests/ -q`
- 总账复跑：`py SCRIPT/_ops_gen_ledger_cb39.py`（R1 终对账用）
- 12345 治理重跑：`py SCRIPT/govern_12345_raw.py`；双轨密度：`py SCRIPT/dual_track_density.py`（路径已同步新落位）
- 自测前必须重启 serve（`py frontend/serve.py 8080`·默认 127.0.0.1·局域网需 `--host=0.0.0.0`）

## CB 状态

- 当前：**CB-39 双线实施中**（P0 线验证通过 + A 线完成·待 B 线；A 线未送验证·可直进 B 或先送 claude组）
- CB-38 已收官（数据沉淀定稿 + EMC 审计 D1-D9 裁定·均并入 CB-39）
- 双阵营：claude组（评估+收敛）+ Codex（主开发）+ zcode组（评估）；dsh 退出
- CB 工作流：评估方只读+禁 git+落盘 discuss/；每轮收敛必更新 _cb-index+cb-journal（DoD 化）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / `@track()` 签名 / 铁律7 / 两板块=结论 / **时间轴 manifest 生成须用户授权**（D3 专题轮）
- **数据源**：中转站真实数据·sim 禁入·gdb 只读；**蒸馏源纪律**：只认 analysis 最终产物与已成文 md·禁 discuss 取数
- **追踪编号连续**：新增 `register_track_id`·MOD_AIQA.F 从 F_020 起（现最大 19）；空洞不造空号（F_004/F_007 均已登记说明）
- 不造轮子：复用 create_square_grid/aggregate_by_polygons/geo_registry/rag_index
- 街道≠道路（街道=行政单元）·术语统一「街办」（识别字典=超集两者并存）
- 代码禁 emoji·print 走 `_safe_print`·**密钥只输出 key 名**

---

## 恢复指引（新会话）

1. `git pull origin codex/dsh-onboarding`（origin=Gitee）·`git log -8` 对账（末位应见 `2317785d` A5）
2. 读 `docs/catch-ball/_cb-index.md` + 本卡 + `discuss/CB39-实施计划_Codex-2026-08-16.md`（v3.1·唯一现行计划）
3. 数据链路：`DATA/analysis/_总账.md`（100 行总账）+ `DATA/README.md`（池规则）+ `docs/catch-ball/retired.md`（page7 归档）
4. 从「下一步」继续（B1 起步）；若用户要先验证 A 线，出 prompt 给 claude组（P0 线同款）

## 换机提醒（08-16）

- **origin 已切 Gitee**（`gitee.com/tinsei0321/emotion_map`·08-16）+ github 备轨 + `E:/DEV-SYNC-HUB` 本地枢纽；office 机到岗 `git remote set-url origin` 同步切（E7·首推令牌当密码）
- 中转站路径：公司 `D:\OneDrive\2026\15_城市更新专项规划研究`·家 `C:\Users\Hi\OneDrive\...` 同结构
- AMAP 新 key 创建时记得勾选 geocode/geo 服务（存量 key 该接口 infocode=30001）
