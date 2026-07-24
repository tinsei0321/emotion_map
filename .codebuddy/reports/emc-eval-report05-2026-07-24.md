# EMC 05-llm 报告评估

> 评估对象：`tests/reports/report-2026-07-24-05-llm.{md,json}`（commit 15f948c，意图识别 11 例）
> 评估人：CodeBuddy（K3）｜ 2026-07-24 ｜ 归档：`.codebuddy/reports/`（AI 评估报告固定目录，供多模型交叉复核）
> 关联：[emc-experience-plan-2026-07-24.md](emc-experience-plan-2026-07-24.md) §五（04 报告深化，D1-D5 沿用）

---

## 〇、结论摘要

| 面 | 判定 |
|----|------|
| 飞轮（测量系统） | **显著好转**：EMC-SUM v1 头部 + JSON sidecar（含 commit）+ template 部分捕获 + 工具双通道信号——测量正在成型 |
| 被测系统（EMC） | pass 18%（2/11，04 报告为 6%/17 例），**但本轮最大发现是测试基建在喂坏数据**——涉及极性的历史 llm 例结论全部需要重估 |
| 用户四问题定性 | Q1=测试 seam bug（洗坏 polarity）｜Q2=产品 UX 一致性 bug（胶囊默认 ready + 两阶段无对账）｜Q3=半成品 feature（卷帘 POC 退化呈现）｜Q4=断言软（验信号不验完成） |

---

## 一、飞轮本体评估（进步 / 残留）

**进步**（对照审计 H/M 清单）：
- EMC-SUM v1 批级头部落地：n/pass/timeout/t_p50=77s/t_p95=105s 齐备（审计 M-B）。
- JSON sidecar 落地且含 commit 元数据（审计 H5）——可机读、可跨 run diff。
- template 信号部分捕获：filter_attr/zonal/unknown 出现在 7/11 例（H1 修复部分生效，`diagnose:done` 事件通道）。
- 工具信号双通道：`zonal_stats+zonal`（后端 geo + 前端委托 tool:executed 补盲）。

**残留**：
- `tpl=?` 仍有 4/11（全为超时例——diagnose:done 事件在长管道中未发出或未捕获，信号覆盖与超时根因纠缠）。
- **参数列序列化 bug**：`区=[object Object]`（INT-005/006）——报告层未序列化对象参数，且需排查是否为真实工具入参错误。
- judge 只有 ok/err 二态，误杀/漏判细分未启用（用户投票 0/11 未评——闭环仍缺人工环）。
- 单例耗时元数据在 JSON（durationSolo）但未进 md 表格（对比不便）。

## 二、四问题诊断（证据锚点全文挂 file:line）

### Q1「只有中性评论」→ 测试 seam 洗坏数据（屎进屎出，EMC 如实回答）

- **真实数据**（`DATA/processed/xiling_wujia_L2_T1_L2_result_csv.csv`，2500 行，csv 模块正确解析）：Very Negative **1030** / Very Positive **829** / Neutral 442 / Negative 151 / Positive 48——极性数据充足。
- **洗坏路径**（测试装载 seam，`e2e-seam.js`）：
  - `e2e-seam.js:115` `lines[i].split(',')` **naive 分割不解引号** → 含逗号文本列（POI 名/地址）致列错位；
  - `e2e-seam.js:119` polarity 映射只认英文精确值 `Positive`/`Negative`——**`Very Positive`/`Very Negative`（1859 条）+ 全部错位行 → 一律归 Neutral**；
  - 结果：载入图层 ≈92% Neutral，仅 48+151 条正负幸存。EMC 答"仅含中性评论，缺负面极性数据"**对这份被洗坏的数据而言是正确的**。
- **数据池没错**：`/DATA/processed/` 文件完好；**产品正式导入管线也没错**（`import.js:103-159` 用 `dsvRows`/`csv2geojson` 库正确处理引号，且 `main.js:117-119` 识别五档极性）。
- **衍生真问题**：polarity 标准化缺单一事实源——seam 两档映射 vs 产品五档枚举，同一数据两条装载路径两种语义。
- **修复**：seam `loadCSV` 复用产品解析（或至少引号感知 dsv + 五档映射表）；manifest（plan P1-1）字段统计项须含 **polarity 值分布**——值分布可见后，diagnose 与人都不会再被"2 个样本"骗。

### Q2「数据齐全」胶囊 vs 结论缺数据 → 两阶段无对账 + 默认值放大

- 胶囊来源：`panel.js:463` `_STRATEGY_LABEL = { ready: '数据齐全', … }`；`panel.js:816` **`strategy 缺省默认 'ready'`**——diagnose 卡没给 data_plan 也显示"数据齐全"。
- 机制：胶囊 = diagnose（s1）一次性判断（看字段**存在性**："有 polarity 列"→齐全）；结论 = 执行/作答阶段发现字段**值层面**无有效 Negative（本轮因 Q1 被洗坏）→ 答缺数据。**两个阶段的判断对象不同（存在性 vs 值分布），且无回写对账**。
- **修复**：① strategy 缺失时不渲染胶囊或显"未评估"（消灭默认 ready）；② 作答阶段发现值层面缺口时回写修正诊断卡标记（或答案旁注"与诊断不一致"）；③ 根治靠 plan D1/D4（manifest 值分布进 diagnose 视野，判错从源头消失）。

### Q3 对比（C 键）左情绪点右网格 → 半成品 feature 的退化呈现

- 定性：**feature（POC）**，非 bug——`map.js:110` 注释「compare 是 toggle…不碰 renderLayer/applyTime」，`main.js` 注释「批4 Swipe 卷帘 POC：'c' 键 toggle compare 模式（Step 4 改 time-bar 正式入口）」。
- **设计语义**：同一**焦点 grid** 的两个**时间片** A/B 卷帘对比——mapB 镜像焦点 grid（`map.js:216-244`），time-bar 渲染片 B。
- **用户所见"左点右格"= 退化呈现**：mapA 保持当前可见层（情绪点），mapB 镜像了焦点 grid；在无明确时间片选择、无对比语境时，呈现意义不明。
- **问题在交互管理**：隐藏键盘入口无说明、无焦点 grid 时行为未定义、双屏无标题标注各自内容。
- **修复**：C 键入口收敛（默认禁用或首次触发给引导说明）；无焦点 grid 时 toast「请先生成/选择聚合图层再对比」；双屏顶部加内容标题（左：当前图层 / 右：对比对象+时间片）。

### Q4 [OK] 但没跑通 → 断言只验信号不验完成

- INT-005/006 判 OK 的依据是 `tpl=zonal + tools=zonal_stats,zonal` 信号命中（`tmplOk||toolOk` 软断言），**不验证任务是否完成**（回答是否产出、落图是否切题、参数是否正确——`区=[object Object]` 已提示参数可疑）。
- 叠加 Q1 数据被洗坏：即便 zonal 真跑通，"情绪整体偏向"结论也建立在 92% 假 Neutral 上——**信号对了，答案错了**。
- **修复**：审计 M-A-3 断言硬化 + 新增"任务完成校验"三件套（exit badge 非 gap + 落图自检过 + 答案非"缺数据"话术）；修参数序列化 bug。

## 三、05 vs 04 指标对比

| 指标 | 04（17 例） | 05（11 例） | 读法 |
|------|-------------|-------------|------|
| pass 率 | 6% | 18% | 略升，但两例 OK 均受 Q1/Q4 污染，**真实进度待 seam 修复后重测** |
| 超时 | 10 | 3 | 链式超时仍在（INT-001/002/008），D3 链式模板适应证不变 |
| t_p50 / t_p95 | 91s / 240s | 77s / 105s | 改善主因是快失败（s1 GAP 20s 级）替代长超时，非真提速 |
| s1 假 GAP | 6 | 3 | 部分"GAP"实为 seam 洗数据后的**如实回答**——假 GAP 与真数据污染需重分类 |
| unknown template | 0 | 2（INT-007/011） | diagnose 选型仍退 unknown，词表/决策树问题残留 |

## 四、对修复 plan 的增量（T 系列 · 测试基建）

| # | 项 | 内容 | 挂靠 |
|---|-----|------|------|
| **T1** | seam loadCSV 修复 | 引号感知解析（复用产品 dsvRows/csv2geojson 路径）+ polarity 五档映射表 | **P0 插队**（污染评估基线，先于一切重测） |
| **T2** | polarity 标准化单一事实源 | 五档枚举+别名映射抽为共享常量（产品/seam/工具 where 条件同源） | 随 T1 |
| **T3** | 参数序列化 bug | 报告参数列对象正确序列化；排查 `区=[object Object]` 是否真实入参错误 | B2 |
| **T4** | 胶囊默认 ready 消灭 + 两阶段对账 | 缺 strategy 不显"数据齐全"；值层面缺口回写修正 | B1 |
| **T5** | compare POC 收敛 | 入口管理 + 无焦点提示 + 双屏标题 | B1 |
| **T6** | 任务完成校验三件套进断言 | exit 非 gap + 落图自检 + 答案非缺数据话术 | B2（M-A-3 内） |
| **T7** | seam 修复后**重跑 04+05 全量** | 重建干净基线（此前涉极性例结论作废重估） | T1 后立即 |

## 五、证据锚点与复现（供其他模型复核）

- 真实分布复现：`csv.DictReader` 读 `DATA/processed/xiling_wujia_L2_T1_L2_result_csv.csv` 统计 polarity → VN 1030 / VP 829 / Neu 442 / N 151 / P 48（2500 行）。
- seam 缺陷：`frontend/js/e2e-seam.js:115`（naive split）、`:119`（两档映射）；对照产品 `frontend/js/import.js:103-159`（dsvRows/csv2geojson）与 `main.js:117-119`（五档分组）。
- 胶囊：`frontend/js/ai_qa/panel.js:463`（_STRATEGY_LABEL）、`:816`（默认 ready）。
- compare POC：`frontend/js/map.js:110-249`、`frontend/js/main.js`（'c' 键注释行）。
- 报告原文：`tests/reports/report-2026-07-24-05-llm.{md,json}`。
