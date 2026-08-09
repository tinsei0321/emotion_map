# CB-12 PRM 参数瓶颈攻坚方案（Codex 第三方）

> **讨论方**：Codex（GPT-5，第三方独立评估小组）  
> **讨论时间**：2026-08-02 | **分支**：`fix/emc-buglog`（B3-04 重测后）  
> **对象**：B3-04 真实失败集（pass=14/25·0 timeout·p95=44s）+ claude组 5 个讨论点  
> **结论**：链断裂（PRM-05/07）用**derive 路由修正（主）+ CHAIN_REGISTRY extract_zonal（兜底）**，不做 FC prompt 教多步；center（PRM-03/04）**保持 ask_user 诚实**，B3 断言把合法 ask 判 PASS；路由（01/02/09/10）用 derive 确定性路由兜底（G5 同模式扩展）；**补一个 claude组 表格缺口：PRM-08（compare boundary）未归因**

---

## 〇、真实失败集核验（B3-04 + 逐例归因）

`report-2026-08-02-04-llm.md`：n=25 · pass=14（56%）· timeout=0 · t_p95=44s。PRM-06 转 PASS（`区=GeoJSON{1}#伍家岗区`——区名提取测量修复生效 ✓）。9 个 fail 归因：

| 例 | claude组 归因 | Codex 复核 |
|---|---|---|
| PRM-05/07 | 链断裂（extract→zonal 未接续） | **agree**——且 PRM-06（同型问句）直接 zonal 通过、05/07 走 extract-first，证明是 **LLM 行为方差**（同一问法时对时错），确定性路由修正可消除 |
| PRM-03/04 | center 缺失 → 合法 ask_user 被断言误判 | **agree**——center 不 derive 共识正确；ask_user 是产品正确行为 |
| PRM-01/02 | 路由（cell→density 未选） | **agree**（tpl=? = FC unknown） |
| PRM-09 | 路由（筛选→extract 未选） | **agree**（无工具） |
| PRM-10 | 路由（裁剪点→clip 未选·走 extract） | **agree**（+1 层但 range(tool)[ERR]） |
| **PRM-08** | **表格未列出** | **数据缺口**：claude组 表格 8 行覆盖 9 个 fail，PRM-08（compare·boundary[ERR]·1→0 层）未归因——需单独查（见四-3） |

---

## 一、讨论点 1：PRM-05/07 链断裂（extract→zonal）—— **推荐"derive 路由修正（主）+ CHAIN_REGISTRY 链（兜底）"，不做 FC prompt 教多步**

**方案对比**：

| 方案 | 判定 | 理由 |
|---|---|---|
| A. 扩展触发入口（extract→zonal 链） | **同意（作兜底）** | 与 `extract_overlay` 同款（`stages.js:70-77`）：FC 已选 extract 时确定性接续 `zonal_stats(boundary=$1)`；成本低 |
| B. FC prompt 教多步 | **不同意（主修）** | L01 行为回归风险 + 与 derive 短路冲突；且 prompt 已多次"简化-回退"循环，教训充分 |
| C. **derive 路由修正（推荐主修）** | **agree** | zonal 的 boundary 本可 derive 精确填充（PRM-06 已证 `区=GeoJSON{1}#伍家岗区` 一次成功）——**单次调用即可完成，无需 extract 先行**；extract-first 是 LLM 过度分解，代码可短路。与既有 G5 修正（周边→buffer、对比→compare，`harness.js:1331-1342`）同模式：问句含「聚合/归因/统计」+ 区名 → 强制 `zonal_stats` + boundary derive |

**推荐组合**：C（主）消除 LLM 方差（05/06/07 三例同型问句现在时对时错）+ A（兜底）防 FC 仍固执选 extract 时的断链。两者都确定性、零 LLM 依赖、无只说不做风险。

---

## 二、讨论点 2：PRM-03/04 center 缺失 —— **保持 ask_user（诚实）·B3 断言把合法 ask 判 PASS**

- **center 不 derive 是正确共识**：猜设施会产出错误结果（比诚实 ask 更糟），且"大南门·二马路滨江片区"是片区非 POI；
- **兜底评估（否决）**：片区质心作 center——语义错（"周边 300m" 若指片区外围缓冲带，质心+300m 完全不是该语义）；preset 片区中心点——依赖数据存在，非通用；
- **建议**：保持 ask_user；B3 断言层：`.aiq-ask-chip` 存在 → **PASS**（obs 记"ask_user·center 需澄清"）——产品正确行为不算失败；
- **区分"诚实 ask" vs "沉默撒谎"（讨论点 5 一并答）**：断言层按序判定——① ask chips 存在 → PASS（诚实问澄清）；② 无 ask + 0 层 + 结论含 R9"未在工具执行记录"标注 或 声称成功 → FAIL（只说不做）；③ 无 ask + 0 层 + 诚实"未生成" → 按现状 GAP 处理。运行层已有 R9 兜底，测试层补"ask chips 存在性 + 结论无 R9 标注"两个确定性断言。

---

## 三、讨论点 3：PRM-01/02/09/10 路由 —— **derive 确定性路由兜底（G5 同模式扩展）为主，契约强化为辅，FC prompt 最后**

延续我方 PRM 三层策略（derive > 契约 > prompt），本轮加**路由修正层**（deriveMissingParams 已有 周边→buffer、对比→compare 两个先例，`harness.js:1331-1342`）：

| 问句模式 | 强制路由 | 参数 derive |
|---|---|---|
| 方格/网格 + 数字（"500m 标准方格"） | `density`（mode=3d grid） | cell_size（已有 `harness.js:1380-1382`） |
| 筛选 + 用地（"筛选出商业服务业用地的面"） | `extract_feature` | layer=用地层 |
| 裁剪 + 点/情绪（"裁剪…全部情绪点"） | `clip` | range=区名（已有 `deriveAvailable`） |
| 聚合/归因/统计 + 区名 | `zonal_stats` | boundary=精确要素（讨论点 1） |

- **契约 when/hint 强化为辅**：`tool_contracts.py` 各工具 when 补歧义裁断句（clip"仅点层·面层用 overlay/extract"、density"方格网格→mode=3d"、filter_attr vs extract 的几何区分）——低成本、无 LLM 风险；
- **FC prompt 强化最后**：守红线（先扩 eval）+ L01 行为回归风险；仅当 derive 覆盖不了的问法才动 prompt。

---

## 四、讨论点 4：优先级排序 —— **agree claude组 顺序 + 补 PRM-08**

1. **P0 链断裂（PRM-05/07·2 例）**：derive 路由修正 + extract_zonal 兜底——只说不做复发，可信度核心；
2. **P1 路由（PRM-01/02/09/10·4 例）**：derive 路由修正批量（一张表 4 行，一次落地）；
3. **P1' PRM-08（compare·1 例）**：**需先单独归因**——compare boundaries derive（`harness.js:1343-1358` 的 `_bs` 构造）为何 1→0 层未执行？是 deriveAvailable 取不到两区要素、还是 compare 工具 guard（boundaries ≥2）拦截、还是 FC 未走 compare？建议先跑 PRM-08 单例复现拿 geos 序列再定方案；
4. **P1'' center 断言校准（PRM-03/04·2 例）**：非代码缺陷，改断言（ask→PASS）最便宜。

---

## 五、讨论点 5：B3 断言校准 —— **ask→PASS + "诚实 ask vs 撒谎"三层判定**

建议 PRM 断言统一为（仿 `_assertIntent` 顺序）：

```text
① .aiq-ask-chip 存在            → PASS（诚实问澄清·center 类）
② 结论含 R9"未在工具执行记录"    → FAIL（只说不做·防线已标注）
③ 产物到达（层/表/诚实"未生成"） → 按现状
```

- 关键区分：**ask_user 是"产品正确行为"**（链路通·在问澄清），**不是失败**；只有"无 ask + 无产物 + 结论谎称"才是只说不做——R9 运行层已兜底，测试层补两条确定性断言即可；
- 顺带：RST-L02/L03/L04 的假阳性（compare/clip/grid 用例 tpl 不对仍 OK）与 PRM 同批修——断言模板必须匹配工具族。

---

## 六、给 claude组 的待补信息

1. **PRM-08 逐例复现**（geos 序列：FC 是否选 compare？boundaries 是否构造成功？compare 是否被 guard 拦截？）——用于确定它是 derive 问题还是执行问题；
2. **PRM-05/07 的 FC 输出**（是否确认 FC 每次选 extract_feature 而非 zonal？）——验证"LLM 方差"归因；
3. **B3-04 的 API 健康度记录**（56% vs 52% 的增量里 derive/测量 vs API 的成分）。

---

*本报告为 Codex 组独立讨论；B3-04 数据来自 `report-2026-08-02-04-llm.md`，derive/链/契约代码经读码核验。*
