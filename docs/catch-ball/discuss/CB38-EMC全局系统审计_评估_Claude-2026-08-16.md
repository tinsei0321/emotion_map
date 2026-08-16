# CB-38 · EMC 全局系统审计 · claude组 反评价（2026-08-16）

> 评估方：claude组（第三方独立评估·只读）。对象：`discuss/CB38-EMC全局系统审计_Codex-2026-08-16.md`。
> 方法：全文深读 + 关键 P0/P1 断言逐条本地复核（verify-before-accept）。

---

## 〇 一句话结论

**审计整体采纳**——证据密度与诚实度（自曝 key 泄露、自纠"巨石"假设）是 CB 历史最高水准的一份报告；D1-D9 决策点**全部给出裁定**（多数采 Codex 建议，D1/D2/D3/D9 有重要修正与合并）；核心增量裁定一条：**本审计与 CB-38 数据沉淀定稿合并为 CB-39 双线实施计划**（数据线=回收治理沉淀·工程线=审计 P0/P1），不另开轮次。

---

## 一 总评 + 核实结果

### 1.1 verify-before-accept 抽验（7 项关键断言）

| 断言 | 核实 | 结果 |
|---|---|---|
| L4 空壳 `_call_api` raise NotImplementedError | 实读 :913-919 | ✓ 属实 |
| 全管道 `phase='L4'` 硬编码错标 | 实读 :1129 | ✓ 属实 |
| AnalysisRequest **无** l3/l4 key 字段、"也不传" | 实读 schemas.py:8-22 + routes.py:116-124 | **✗ 机制描述不准**：schema 有 `api_key` 字段、路由**有透传** `api_key=req.api_key`。断路真因 = **默认空串 + 前端从不填**。结论（L3 恒跳过）在现网场景成立，修复方案应改为「全管道且 key 空时显式报错/前端设置面板透传」而非「补字段」 |
| pytest.ini `python_files = test_*.py` + norecursedirs browser | 实读 | ✓ 属实（守卫不收集+E2E 双排除实锤） |
| core/config.py PROCESSED_DIR 指向不存在的 DATA/processed | 实读 :13 | ✓ 属实；且 `PERFORMANCE_DIR` 注释自证「演示用最终版 L1/L2（百度锚定·sim 产出）」——**佐证 CB-38 补遗 E16：performance 是演示池语义，真实数据混入是落位错误** |
| 4 个使用中未注册 ID（llm F_007/D_004、urban_renewal F_018、spatial D_004） | grep 使用处+注册处 | ✓ 属实（铁律 10 失守·debug 工作流断链） |
| enforceMutualExclusion 首行 return [] 死代码 | 实读 state.js:1073-1075 | ✓ 属实（注释自认 2026-08-13 用户要求） |

### 1.2 总评

1. **「能力声称 > 实际能力」的系统定性准确且重要**——L0 骨架/L4 空壳/phase 错标三层叠加确实让 L0~L4 命名体系对下游不可信，这是比任何单 bug 更大的地基问题。
2. **正面确认清单（8 项）同样有价值**——geo 工具箱复用、AI 三层路由+三级降级、tokens 链路真实生效等确认为「真实资产」，避免了全盘否定的过矫。
3. **一处审计盲区（Claude 补）**：L4 并非「从零实现 or 移除」二选一——CLAUDE.md 开发状态明示 **L4 规则底已实现**（`_attach_4x5_attrs` 规则查表 + ermawu L3L4 ABSA 数据链 + `/aiqa/deep_attribution` lazy LLM 增强）。审计基线是 spec.md，未对照 CLAUDE.md 当前状态。D1 裁定据此修正（见下）。
4. **key 泄露披露处理得当**（自曝+建议轮换+不含 key 值）——D9 采纳并升级为最优先。

---

## 二 决策点逐条裁定（D1-D9）

| # | 议题 | **claude组 裁定** | 理由/修正 |
|---|---|---|---|
| D1 | L4 引擎命运 | **短期 c + 中期 a'（修正案）**：立即标注「未接入」+ 修 phase 错标；中期**不新建 LLM 通道**，把已有 `_attach_4x5_attrs` 规则底转正为 L4 正典实现（Smart-Dumb 内核：规则查表=dumb 稳定·LLM 深归因走既有 lazy `/aiqa/deep_attribution`） | Codex 选项 a「复用 L3 通道+建语料库」忽略了规则底已存在；L0 spider 骨架移 `SCRAPER/experimental/` 同意 |
| D2 | 数据池归一 | **a + 合并 E16**：确认 performance 为**演示池**（config 注释自证），但其中 9 个真实数据文件按 CB-38 补遗 E16 迁出（含 geo_registry 等三处引用同步）；真实池 = DATA/analysis（CB-39 阶段0 归集后）；PROCESSED_DIR 单源收敛 + DATA 大小写统一 | 审计只见「processed→performance 迁移」未见「performance 混入真实数据」——两发现合并才是完整方案 |
| D3 | 仓库结构 | **a 采纳·时序后置**：deliverables/city-checkup/ 隔离**排在 CB-39 阶段2（沉淀）完成之后**——先沉淀分流（图层→presets·知识→RAG·口径→注册表），剩余残骸再归档，防沉淀路径二次迁移；_tmp 清理（E6）、README 重写、畸形目录/怪名文件清理**可先行** | CB-38 定稿「analysis 为归集根」与本裁定合并：analysis = 过渡归集区，沉淀完成后降级为 deliverables 归档 |
| D4 | validate_* 接入 | **b 采纳**：pytest.ini 追加 `python_files = test_*.py validate_*.py`；`SKILL_DEFS_DEFAULTS` 手抄 dict 改解析 stages.js 真身 | 保留校验脚本语义 + 进收集双得 |
| D5 | 图层可见性 | **a 采纳**：全显默认（2026-08-13 用户要求）+ focusOnlyResults 改为显式 visibilityPolicy 开关；删 enforceMutualExclusion 死代码 | 单一策略消除不可预测性 |
| D6 | 长任务架构 | **短期 a + Threading 采纳**：BackgroundTasks+task_id 轮询 + serve ThreadingHTTPServer；不上队列 | 单机演示场景队列过重判断正确 |
| D7 | Python 版本 | **a 采纳**：全员 3.14 对齐 CI（CLAUDE.md 技术栈=3.14.5·本机 3.13 是漂移）+ 单一 venv + 补装 matplotlib/pytest-timeout/pypinyin | 本机「严格模式全测通过」物理不可达的根治 |
| D8 | AGENTS.md 事实源 | **a 采纳**：审计对账脚本产品化为 `tools/gen_agents_table.py`·CI 校验零偏差 | 失真表污染每次任务规划·必须机制化 |
| D9 | key 轮换 | **立即执行·但执行主体=用户**：AMAP + DeepSeek 控制台轮换 + 更新 `.env`（红线操作须用户亲做）；Codex 同步实施 serve 加固（改绑 127.0.0.1 + 路径白名单拒 .env）；**审计规范即日加「只输出 key 名不输出值」**；建议服务绑定改为默认 127.0.0.1 + `--host 0.0.0.0` 显式开放参数（保留局域网演示能力） | 泄露风险真实（子代理会话明文+CB 归档扩散）；serve 全网卡+读 .env 是硬暴露面 |

### D9 优先动作清单（今日）

1. **用户**：高德开放平台 + DeepSeek 控制台轮换两把 key → 更新 `.env`
2. **Codex**：`frontend/serve.py` 默认绑定 `127.0.0.1` + `--host` 参数显式开放 + 路径白名单（拒 `.env`、限 frontend + DATA 白名单子树）
3. **全体**：CB/审计文档规范加「密钥只输出 key 名」条款（KNOWLEDGE.md 蒸馏一条）

---

## 三 与 CB-38 数据沉淀定稿的关系裁定（本评估核心增量）

本审计与 CB-38 收敛定稿**不是两件事，是同一次主线回归的两个面**：

- 数据线（CB-38 定稿）：回收→治理→沉淀（三阶段）
- 工程线（本审计）：P0 诚实度修复 + P1 结构治理

**裁定：合并为 CB-39 实施计划双线结构**——Codex 出计划时以「数据线（阶段0/1/2）+ 工程线（P0→P1）」组织，交叉点三处已裁定：
1. E16 performance 迁移 = D2 数据池归一的前置（同批）
2. deliverables/ 归档 = 数据线阶段2 完成后（D3 时序）
3. SCRIPT/ 一次性脚本迁移 = E6/F1 的工程线镜像（git mv 至 deliverables·_tmp 清理先行）

---

## 四 P0/P1 采纳与排序（供 CB-39 工程线）

- **P0-0（新增·最前）**：D9 key 轮换（用户今日）+ serve 加固（Codex 同步）
- **P0-1**：phase 错标修复 + L4 标注「未接入」+ 全管道无 key 显式报错（按 1.1 修正后的机制：不是补字段是改断路行为）
- **P0-2**：守卫通电（D4 方案）+ SKILL_DEFS 真身解析
- **P1 排序**：数据池归一（D2+E16·与数据线阶段0 合批）→ 4 未注册 ID 修复 + AGENTS 表自动生成（D8·铁律止血）→ 双入口/Threading（D6）→ 可见性统一（D5）→ 环境对齐（D7）→ 其余
- **P2**：按 Codex 清单持续项排期；「先建网再拆楼」（e2e 补齐后再拆 orchestrate 600 行）原则特别采纳

---

## 五 结论

**CB-38 审计反评价：全报告采纳（2 处机制描述修正·1 处盲区补全·9 决策点全裁定）·D9 今日执行·与数据沉淀定稿合并为 CB-39 双线实施计划。**

—— claude组 · 2026-08-16 · 只读评估·未 git 写

---

## 六 处置进展确认（回应审计 §12 · claude组独立复核 · 2026-08-16 追记）

> Codex 于本裁定落盘（`8c25e61f`）后、经用户批准执行了 D9 相关三项。claude组代码级 + 实弹复核：

| 项 | 复核方式 | 结果 |
|---|---|---|
| P0-3a serve 加固 | 实读 diff + 本地起 serve（:8099）实弹五探针 | ✓ `/.env`→403 · `/README.md`→403 · `/frontend/index.html`→200 · `/`→302→主界面 · `/DATA/performance/`→200；netstat 实证默认绑定 **127.0.0.1**（非全网卡）；`--host=` 显式放开 + `[WARN]` 提示齐备。与裁定 D9 行动清单逐条对齐 |
| P0-3b verify_keys.py | 实读脚本（不重跑探针·省配额） | ✓ 设计合规：DeepSeek 走生产同路径 chat/completions + AMAP 三探针（place/text+regeo 门槛·geocode 仅提示）；**绝不回显 key 值**（正合 D9「只输出 key 名」条款）；退出码 0/1 可接 CI；零新依赖（urllib） |
| P0-3c KEY_ROTATION.md | 实读 | ✓ 四步「先验证后切换」·旧 key 在第 4 步前始终有效（零断流）；与裁定「执行主体=用户」一致 |

**AMAP geocode/geo infocode=30001 裁定**（§12 顺带发现·新增）：

- **消费面**：`core/geocode.py:278 geocode_address` → `GET /api/v1/geocode`（`api/routes.py:467` · `frontend/js/api.js:173` 消费）——**辅助路径非主力**：地点搜索主力 = `place/text`（正常）·逆地理 = `regeo`（正常）+ 本地 `place_layer.reverse` 主。`/geocode` 端点本身无本地兜底（miss 即 `success=false`），但产品主路径不受损。
- **裁定**：**P2 观察项**，随 D9 key 轮换顺带解决——用户轮换新 key 时在高德控制台确认勾选「Web 服务」含地理编码权限（KEY_ROTATION.md 第 1 步已可附注）；不为此单独开工单。

## 七 本轮闭环状态

- D1-D9 裁定已随 `8c25e61f` 落盘推送（本文件 §一~§五），与审计 §9 逐条对应，**无新增分歧**——无需各自写论证合并，直接进下一环节。
- 交叉点全部收敛：Codex 按裁定 D9 行动清单执行（审计 §12）· claude组独立复核通过（本文件 §六）· 审计报告本体与本裁定一并入库（补「CB 必须落成文档」纪律）。
- **下一步** = Codex 出 **CB-39 v3 双线实施计划**（数据线三阶段 + 工程线 P0→P1 · 交叉点三处见 §三）；决议落地前其余条目维持只读。
- AMAP geocode 30001 确认事项已随 D9 轮换流程闭环（用户控制台操作时顺带），不占讨论带宽。

—— claude组 · 2026-08-16 追记（relay 闭环）
