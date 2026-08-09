# CB-16 Wave 1 macro 出口实施预检 SCAN（glm组）

> **评估方**：glm组（ZCode + GLM 5.2 · 第三方评估·非开发主）
> **日期**：2026-08-04 | **CB 轮次**：CB-16（Wave 1 macro 出口·renewal_object_identify + checkup_dimension）
> **基线**：git @ `dd4009e`（fix/emc-buglog）
> **方法**：代码级核实 7 处实施点现状（_extract_emc_value / _maybeBuildOutletCard / checkup field_mapping / DOMAIN_KW / zonal rows / 测试白名单）→ 7 问独立判断。结论先行。
> **立场**：glm组 为独立第三方评估·非开发主。对 claude组 草案施加独立审视·凡同意处给代码证据·凡风险处明确标出。未参考 Codex 报告。

---

## 结论先行（TL;DR）

| # | 实施点 | glm组 判断 | 一句话 |
|---|---|---|---|
| **①** | _extract_emc_value 加 rows 分支 | ✅ **同意·建议规整为统一入口** | 后端一个函数收 rows/features 两类→单一 features 视图·前端不打补丁·防前后端各判一次产物形态 |
| **②** | harness 优先取 data.rows + 门放宽 | ✅ **同意·门条件须精确** | 「rows 非空 ∨ newLayerCount>0」放行·禁删门（无产物也出卡=空卡风险）·**调用时机 data.rows 可达性须实测** |
| **③** | DOMAIN_KW 补「体检」 | ⚠️ **同意补·但必须用长词** | 单「体检」误触发（体检中心 POI/健康体检）·**补「城市体检」专有名词**·前后端 DOMAIN_KW + TRIGGER_WORDS 须同步 |
| **④** | checkup_dimension 字段映射 prose→真实字段 | ✅ **同意·白名单已核合规** | 四维度映射 polarity_index/domain_top/element_top/issue_label/place_name·全∈_EMC_FIELDS |
| **⑤** | point_count 语义（rows 型=N 单元数） | 🔵 **必须标注·否则误导** | rows 型顶层无 point_count·塞 rows.length 当 N = 单元数被误读为评论数·note 须区分单元数/评论数 |
| **⑥** | 测试方案（单测+E2E） | ✅ **够·补 2 边界断言** | 补"无 rows 无图层不出卡"+"rows 非空出卡且字段非暂无数据" |
| **⑦** | 边界（不碰承重/CB-15） | ✅ **无越界** | 仅出口层+词表+测试·不碰 diagnose/orchestrate/ChatRequest·不碰 CB-15 place_name |

**一句话总判定**：claude组 草案**方向正确、可行**·7 处改动落地后 macro 出口链路能打通。**无 P0 阻塞**。3 项 P1 建议（①统一入口 / ③长词防误触发 / ⑤语义标注）+ 2 项 P2 提醒（调用时机实测 / checkup_satisfaction 同改）。

---

## 第〇部分：现状核实（claude组 探索声明 vs glm组 实测）

### 0.1 核实结论：三层断裂声明全部属实

| claude组 声明 | glm组 实测 | 判定 |
|---|---|---|
| _extract_emc_value 不识别 {rows:[...]} | `build_outlet_schema.py:78-92`：只查 `result[emc_field]` 顶层 + `result.features[0].properties`·**无 rows 分支** | ✅ 属实 |
| _maybeBuildOutletCard newLayerCount<=0 直接 return | `harness.js:1566`：`if (newLayerCount <= 0) return null;` | ✅ 属实 |
| _maybeBuildOutletCard 只收图层 fc | `harness.js:1576-1578`：`result = { features: feats, point_count: feats.length }`·**只从 getArtifacts() 取图层** | ✅ 属实 |
| zonal rows 已含归因列 | `geo_routes.py:374-389`：rows = `[name/point_count/polarity_index/score_mean/domain_top/element_top/issue_label/attribution/suggestion]`·**富归因齐备** | ✅ 属实 |
| checkup_dimension field_mapping 全 prose | `urban_checkup_outlets.py:38-43`：`'micro 网格/POI 归因（建筑/居住情绪）'`等·全是描述文字·`_extract_emc_value` 取不到 | ✅ 属实 |
| DOMAIN_KW.urban_governance 无「体检」 | `emc-patterns.js:17`：`['治理','交通','停车','施工','城管','环境']`·**无体检** | ✅ 属实 |
| renewal_object_identify 已 macro 就绪 | `urban_renewal_outlets.py:20-21`：`scales=['macro']`·契约已注册 | ✅ 属实 |

**核实结论**：claude组 的结构性缺口诊断**准确无误**。三层断裂（门断裂 + 收集断裂 + 解析断裂）代码级证据齐·macro 问句要么不出卡要么出空卡的根因定位正确。

### 0.2 关键补充（glm组 独立发现）

**`_extract_emc_value` 的 qualifier 解析隐患**（build_outlet_schema.py:130-141）：
```python
main_field = _re.split(r'\s*(?:降序|占比|排序|负数|正数|TOP\d+)', str(emc_expr))[0].split('+')[0].split('（')[0].split('/')[0].strip()
```
这段把 field_mapping 的 emc_expr（如 `'polarity_index 降序'` 或 `'domain_top/element_top'`）拆出主字段。**rows 分支加入后·rows[0] 的字段名必须能被这段 qualifier 解析命中**——即 checkup_dimension 改后的 field_mapping 字段须是**裸字段名**（如 `'polarity_index'` 或 `'domain_top+element_top'`）·不能带额外修饰词（否则 qualifier 拆不出主字段→仍"暂无数据"）。**这是④实施时必须注意的约束**（claude组 草案未明确提醒）。

---

## 第一部分：7 问独立判断

### ① rows 并入出口链路：✅ 同意·建议规整为统一入口

**claude组 草案**：后端 `_extract_emc_value` 加 rows 分支 + 前端 `_maybeBuildOutletCard` 补 rows 收集。

**glm组 判断：方向对·建议升级为后端统一收产物**。

**理由**：
草案是"前端补 rows 收集 + 后端补 rows 解析"各改一处——**两端各自判产物形态，必然漂移**（前端判"有 rows 就传 rows"·后端判"有 rows 就查 rows"·两处逻辑必须永远同步）。更稳的是**后端单一入口规整**：

```python
def _extract_emc_value(result: dict, emc_field: str):
    if not result or not isinstance(result, dict):
        return None
    # 统一规整：rows / features 两类 → 单一 features 视图
    rows = result.get('rows')
    if isinstance(rows, list) and rows:
        feats = [{'properties': r} for r in rows]   # rows 型：每行当 properties
    else:
        feats = result.get('features') or []
    if isinstance(feats, list) and feats:
        p = feats[0].get('properties', feats[0]) if isinstance(feats[0], dict) else {}
        return p.get(emc_field)
    # 顶层 dict 兜底（统计型）
    return result.get(emc_field)
```

**优势**：
1. 后端一个函数处理 rows/features/统计 dict 三类·**前端只需把产物原样传**（rows 或 fc 都行·后端都能收）。
2. 产物形态判断只在一处（后端）·防前后端漂移。
3. 前端②简化为"优先传 data.rows·无则传图层 fc"·后端不强依赖前端传啥。

**Top-1 取值的固有限制**：rows[0] = 最消极/最优先单元。对 renewal_object_identify（识别更新对象）合理（Top-1 = 最需更新片区）。但 checkup_dimension 四维度并列时·卡片只展示 rows[0] 对应的一个维度——**本轮可接受（演示单维度）·多行支持是后续优化**。

### ② harness 产物收集 + 门放宽：✅ 同意·门条件须精确·调用时机须实测

**门放宽副作用核查**：
- macro 的 zonal/rank 权威产物是 rows（单元排行表）·**不一定产新图层**（rows 直接进 observation·地图可能只高亮已有面图层）。
- 若强求 newLayerCount>0 才出卡·macro 场景永远不出卡——**这正是当前 bug 根因**。
- **门条件须精确**：`if (!hasRows && newLayerCount <= 0) return null;`（rows 非空 ∨ 有新图层 才放行）。**禁删门**（无产物也出卡=空卡风险）。

**glm组 独立提醒（调用时机·claude组 草案未充分强调）**：
`_maybeBuildOutletCard` 在主循环的调用位置决定 data.rows 是否可达：
- 若在**工具执行后立即调**·data.rows 还在内存（可取）。
- 若在**final answer 后调**·data 可能已被回收·需从 toolHistory 重建——但 toolHistory 只有 observation 文本（`geo_routes.py:390` 的 message 字符串）·**不含 rows struct**。

**实施前必须实测**：harness.js 里 `_maybeBuildOutletCard(diagnose, ctx, newLayerCount)` 的调用点（grep 定位）·确认该位置能否访问到最近工具的 `data.rows`。若不能·需在工具返回时额外保留 data（轻量·只留 rows 字段进 ctx）·否则②的"优先取 data.rows"落空。

### ③ DOMAIN_KW 补「体检」：⚠️ 必须用长词

**误触发风险（glm组 独立推演）**：
- 「体检中心在哪」→ 这是 POI 查询（gis_operation）·但「体检」命中 DOMAIN_KW → domain_lens 兜底 urban_governance → 若问句还有接口词（如"识别"）可能误出 checkup_dimension 卡。
- 「健康体检」「入职体检」→ 医疗/HR 语境·非城市体检。
- DATA/POI 里可能有「xx体检中心」POI（geo_routes 搜索时命中）。

**glm组 建议：补「城市体检」长词·非单「体检」**。
- 「城市体检」是住建部政策专有名词（建办科函〔2025〕280号）·不会与"健康体检/体检中心 POI"混淆·**零误触发**。
- 单「体检」太泛·不补。

**前后端同步（关键）**：
- 前端 DOMAIN_KW（emc-patterns.js:17）+ 后端 TRIGGER_WORDS（build_outlet_schema.py:22）**都含产物触发词**。
- 若前端改长词「城市体检」而后端仍单「体检」·则**前后端触发不一致**（前端不触发"体检中心"但后端触发·或反之）。
- **必须同步**：前端 DOMAIN_KW.urban_governance 加「城市体检」+ 后端 TRIGGER_WORDS 的「体检」也改「城市体检」（或加 _UI_CONTEXT_WORDS 式排除）。
- **⑦同步守卫提醒**：若改 TRIGGER_WORDS·`validate_outlet_trigger_sync`（守 TRIGGER_WORDS↔OUTLET_TRIGGER_KW 同步）的预期词表须更新·否则 CI 红。

### ④ checkup_dimension 字段映射：✅ 同意·白名单合规·注意 qualifier 解析

**字段映射语义核查**：

| 维度 | claude组 草案字段 | 语义对齐 | 白名单 | 判定 |
|---|---|---|---|---|
| 住房(micro) | issue_label + place_name | 住房问题标签+落点 | ✅∈白名单 | ✅ 合理 |
| 小区(meso) | domain_top/element_top + polarity_index | 设施服务归因+情绪强度 | ✅∈白名单 | ✅ 合理 |
| 街区(meso) | issue_label + polarity_index | 街区问题+情绪 | ✅∈白名单 | ✅ 合理 |
| 城区(macro) | polarity_index + domain_top | 整体情绪+主导领域 | ✅∈白名单 | ✅ 合理 |

**glm组 提醒（qualifier 解析约束·0.2 已述）**：
改后的 field_mapping emc_expr 须是**裸字段名或 + 连接**·不能带额外修饰词：
- ✅ 正确：`'polarity_index'` / `'domain_top+element_top'` / `'issue_label+place_name'`
- ❌ 错误：`'polarity_index（整体情绪）'`（带括号说明·qualifier 拆 `（` 后取前半 → 取到 `'polarity_index'`·OK）/ `'polarity_index 降序'`（带修饰·OK·qualifier 拆 `降序`）/ **`'meso 社区单元 zonal'`**（prose·qualifier 拆不出字段 → 暂无数据·这是当前 bug）

即：**改 prose → 裸字段名即可**·qualifier 解析器（build_outlet_schema.py:133）能正确拆出主字段。

**遗漏提醒**：`checkup_satisfaction`（urban_checkup_outlets.py:24-28）的 field_mapping 也是 prose（`'评论情绪 → 自动满意率'`）·但交接卡只提改 checkup_dimension。**checkup_satisfaction 未改不影响 Wave 1**（非本波目标）·但建议后续也改（否则 S6 满意度卡同样出空卡）。P2。

### ⑤ point_count 语义：🔵 必须标注·否则误导

**现状**（build_outlet_schema.py:144-148）：
```python
n = result.get('point_count') or (result.get('stats', {}).get('point_count'))
if n is not None:
    card['data_base']['N'] = n
    card['data_base']['note'] = 'L2 聚合·时间窗待定'
```

**rows 型的歧义**：
- 图层型 result：`point_count = features.length`（评论点数）→ N=评论数 ✅
- rows 型 result：rows 里**每行**有 `point_count`（该单元评论数）·但 result**顶层无** point_count → 当前逻辑 n=None → data_base 降级空。

**误导风险**：若实施②时前端打包 `result={rows:[...], point_count: rows.length}`·则 N=单元数（非评论数）——**用户以为 N=评论数·实际是单元数**。

**glm组 建议（data_base 加 rows 分支）**：
```python
if 'rows' in result:
    rows = result['rows']
    card['data_base']['N'] = len(rows)                    # 单元数
    card['data_base']['total_points'] = sum(r.get('point_count', 0) for r in rows)  # 总评论数
    card['data_base']['note'] = f'{len(rows)} 个区域单元·共 {total} 条评论'
```
**禁混用**：不要把 rows.length 当评论数填 N——会误导用户。

### ⑥ 测试方案：✅ 够·补 2 边界断言

**claude组 草案**：test_outlet_schema.py 补 macro {rows:[...]} 用例 + 浏览器 E2E。

**glm组 判断**：够·补 2 边界断言：
1. **rows 非空出卡 + 字段非"暂无数据"**：验证 rows 分支取到值。
2. **无 rows 无图层不出卡**（防空卡）：验证门放宽后空产物仍不出卡（或出卡但全"暂无数据"·建议返回 None 不出卡）。

E2E（test_outlet_macro.py）建议加**截图断言**（卡片渲染可视化·防 CSS 回归）。

### ⑦ 边界（不碰承重/CB-15）：✅ 无越界

**核查**：
- diagnose prompt / harness orchestrate 主循环 / ChatRequest schema：**不碰**（出口层在主循环外·_maybeBuildOutletCard 是后处理）。✅
- CB-15 place_name 精确源：**不碰**（Wave 2）·Wave 1 的 place_name 仍是格内代表地名（粗略）·出口卡 limitations 已标注。✅
- D019 final 极瘦：**不碰**（出口卡是 final 后的结构化伴随·非 LLM 阶段）。✅
- validate_outlet_trigger_sync：若③同步 TRIGGER_WORDS·须更新测试预期词表·否则 CI 红。⚠️ 提醒（非越界·是同步义务）。

---

## 第二部分：方案评估（架构/触发/字段/测试）

### 2.1 架构合理性

草案的"rows 并入出口链路"是**正确的架构决策**——macro 分析的权威产物形态是 rows（排行表）·出口链路必须能收 rows。glm组 唯一建议是**后端统一收产物**（①）·避免前后端各判一次。

### 2.2 触发正确性

③「体检」补词需防误触发——**长词「城市体检」是正解**（专有名词零歧义）。前后端 DOMAIN_KW + TRIGGER_WORDS 须同步。

### 2.3 字段映射合规性

④四维度字段映射全部∈_EMC_FIELDS 白名单·语义对齐体检四层级。qualifier 解析约束已提醒（裸字段名）。

### 2.4 测试充分性

⑥单测 + E2E 够·补 2 边界断言（rows 出卡 / 空产物不出卡）。

---

## 第三部分：风险矩阵

| 风险 | 等级 | 状态 | 缓解 |
|---|---|---|---|
| **data.rows 调用时机不可达** | 🟡 中 | ⚠️ 须实测 | 实施②前 grep _maybeBuildOutletCard 调用点·确认 data 可达·必要时工具返回时保留 data |
| **「体检」误触发**（体检中心 POI） | 🟡 中 | 可控 | 补「城市体检」长词·前后端同步 |
| **point_count 语义错**（单元数当评论数） | 🟡 中 | 可控 | data_base 加 rows 分支·note 区分 |
| **qualifier 解析拆不出字段** | 🟢 低 | 可控 | field_mapping 用裸字段名·不带 prose |
| **Top-1 只填一维度**（四维度并列） | 🟢 低 | 可接受 | 本轮演示单维度·后续多行支持 |
| **validate_outlet_trigger_sync CI 红** | 🟢 低 | 可控 | 若③同步 TRIGGER_WORDS·须更新测试预期词表 |
| **承重红线触碰** | 🟢 低 | ✅ 不触碰 | 仅出口层+词表+测试 |

---

## 第四部分：承重红线再确认

本方案**不触碰**（KNOWLEDGE §1）：
- diagnose prompt / harness orchestrate / ChatRequest schema——出口层在主循环外·非路由/schema 变更
- D019 final 极瘦——出口卡是 final 后结构化伴随·非 LLM 阶段
- `@track()` / `_TRACKING_REGISTRY`——无新 track id

本方案**轻改/新增**（需守"改前扩 eval"）：
- `build_outlet_schema.py`：_extract_emc_value 加 rows 分支（函数内部增强·非签名变更）
- `harness.js`：_maybeBuildOutletCard 产物收集 + 门条件（内部逻辑·非主循环改）
- `urban_checkup_outlets.py`：field_mapping 数据改（非接口）
- `emc-patterns.js`：DOMAIN_KW 加词（数据·非逻辑）
- 测试：补单测 + E2E

---

## 第五部分：判定 + 建议

### 总判定：✅ 草案可行·3 项 P1 + 2 项 P2

**通过项**（7 处改动方向均正确·glm组 同意）：
- ✅ rows 并入出口链路（①+②）——打通 macro 断裂·架构正确
- ✅ 门放宽合理（macro 权威产物是 rows）
- ✅ checkup_dimension 字段映射合规（白名单核验）
- ✅ 测试方案够
- ✅ 无越界（不碰承重/CB-15）

### P1 建议（3 项·glm组 建议实施时纳入）

| # | 建议 | 理由 |
|---|---|---|
| **1** | **① 升级为后端统一收 rows/图层两类**（_extract_emc_value 单入口规整 rows→features 视图） | 避免前后端各判一次产物形态·单一真相源·防漂移 |
| **2** | **③ 补「城市体检」长词**（非单「体检」）·前后端 DOMAIN_KW + TRIGGER_WORDS 同步 | 防「体检中心/健康体检」误触发·专有名词零歧义 |
| **3** | **⑤ data_base 加 rows 分支**（N=单元数·note 区分·total_points 标总评论数） | 防语义误导（单元数当评论数） |

### P2 建议（2 项·可延后）

| # | 建议 | 理由 |
|---|---|---|
| 4 | checkup_satisfaction field_mapping 也改 prose→真实字段 | 否则 S6 满意度卡同样出空卡·后续必然踩同坑 |
| 5 | 实施②前实测 _maybeBuildOutletCard 调用时机的 data.rows 可达性 | 若不可达需工具返回时保留 data·否则②落空 |

### 实施顺序建议（glm组）

1. **①后端统一收产物**（_extract_emc_value）——基础·②依赖它
2. **⑤data_base rows 分支**——在①之后·同一文件
3. **②前端产物收集 + 门放宽**——基于①·实测调用时机
4. **④checkup_dimension 字段映射**——独立改·守裸字段名
5. **③DOMAIN_KW 补长词**——独立改·前后端同步
6. **⑥测试 + E2E**——①-⑤改完后补

---

## 附：现状核实证据（glm组 独立）

| 发现 | 证据 |
|---|---|
| _extract_emc_value 无 rows 分支 | `build_outlet_schema.py:78-92`·只查 dict 顶层 + features |
| _maybeBuildOutletCard newLayerCount<=0 门 | `harness.js:1566` |
| _maybeBuildOutletCard 只收图层 fc | `harness.js:1576-1578`·result={features,point_count} |
| zonal rows 含富归因字段 | `geo_routes.py:374-389`·rows=[name/point_count/polarity_index/domain_top/element_top/issue_label/attribution/suggestion] |
| checkup_dimension field_mapping 全 prose | `urban_checkup_outlets.py:38-43` |
| DOMAIN_KW.urban_governance 无「体检」 | `emc-patterns.js:17` |
| renewal_object_identify 已 macro 就绪 | `urban_renewal_outlets.py:20-21`·scales=['macro'] |
| _EMC_FIELDS 白名单含所需字段 | `tests/test_outlet_kb.py:14-16` |
| qualifier 解析器拆主字段 | `build_outlet_schema.py:133`·split(降序/占比/排序/+/（/） |
| TRIGGER_WORDS 含「体检」 | `build_outlet_schema.py:22`·须与③同步 |

### 声明

本报告由 glm组（ZCode + GLM 5.2）独立产出·2026-08-04·基于代码级核实 7 处实施点现状。仅读评估（禁改代码/禁 commit）。未参考 Codex 报告。

---

*登记：docs/context-map.md。*
