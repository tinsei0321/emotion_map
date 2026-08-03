# CB-16 Wave 0 剩余实施检查 · SCAN（Codex 第三方独立评估）

> **评估方**：Codex（GPT-5，第三方独立评估小组）  
> **评估时间**：2026-08-03 | **分支**：`fix/emc-buglog` @ `9a98785`  
> **对象**：Wave 0 核心（`ai_qa/outlet_kb/build_outlet_schema.py` + `tests/test_outlet_schema.py`）+ 本轮实施预告（触发词表镜像 + 前端卡片渲染）  
> **方法**：读码 + pytest 实测 + 组装器运行级验证（S2/S3/误触发三例）  
> **结论先行**：**Wave 0 核心方向正确、符合 CB-16 共识（确定性/不调 LLM/诚实标注）**；**但发现 1 个组装 bug + 1 个触发词过宽风险 + 测试覆盖缺口**——① `renewal_sequence` 的"优先级排序"字段（`polarity_index 降序`）解析失败→显示"暂无数据"（实测确认·真实值 -0.45 丢失）② "帮我更新图层"误触发 renewal_demand（`更新`词过宽·实测确认）③ 测试实为 **7 passed 非 13**。实施预告：触发词表镜像 agree（但需先修"更新"过宽 + 加前后端同步守卫）·卡片渲染用既有 token agree

---

## 一、Wave 0 核心核验（3 检查项）

| 检查项 | 判定 | 证据 |
|---|:---:|---|
| 1. 确定性组装符合 CB-16 共识 | **OK** | `build_outlet_schema.py` 纯 Python·零 LLM 调用；`source:'确定性组装（非 LLM）'`；缺失字段降级"暂无数据·不编造"；诚实标注（place_name 粗略 + 规则归因 DEMO + can/cannot 双栏 + 局限）✓ |
| 2. resolve_outlet_id 路由 | **OK（2 个注意点）** | domain+scale 必要条件 ✓ + 接口词/outlet hint 触发 ✓；**注意 ①**：`更新` 词过宽（见二-2）；**注意 ②**：同分取首个（dict 注册序·确定性但依赖注册顺序） |
| 3. 测试覆盖 | **部分** | 7 个测试（**实测 7 passed·非 13**）覆盖：路由命中/未中/尺度分派 + S2 7 要素 + polarity 取值 + 缺失降级 + 不出卡；**缺口**：qualifier 后缀字段（S3 时序）、体检契约、多匹配 tie、"更新图层"误触发、图层 fc 路径 |

## 二、发现的问题（运行级实测确认）

### 问题 1（组装 bug·MED）：qualifier 后缀字段解析失败

- `build_outlet_schema.py` `main_field` 解析：`emc_expr.split('+')[0].split('（')[0].split('/')[0].strip()`——**不去除尾部限定词**（降序/占比/负数）；
- 实测 `renewal_sequence`（"西陵区更新时序排序"）卡片：
  - `优先级排序`（field_mapping='polarity_index 降序'）→ **"暂无数据 | 缺失·不编造"**——实际 result 有 `polarity_index=-0.45`·**核心定量指标丢失**；
  - `单元特征`（domain_top）→ urban_renewal ✓；
- **影响**：S3 时序排序卡的"优先级"列全空；其他含限定词映射（如 `n_negative 占比`）同病；
- **修复**：解析时去尾部限定词（`re.split(r'\s*(?:降序|占比|排序|负数|正数|TOP\d+)', emc_expr)[0]` 或契约字段改用纯键名）。

### 问题 2（触发词过宽·MED）：「更新图层」误触发行业卡

- 实测 `resolve_outlet_id({'scale':'meso','outlet':'生成图层'}, '帮我更新图层')` → **renewal_demand**；
- **根因**：`TRIGGER_WORDS` 含 `更新`（行业词·也是 EMC UI 术语"更新图层"）——问句含"更新" + 契约名含"更新"即命中；
- **影响**：用户 UI 操作类问句（"更新图层/更新时间"）会错误出"更新需求分析"卡——若镜像到前端 emc-patterns.js，误触发面更大；
- **修复**：① 触发词加行业上下文限定（"更新需求/更新改造/老旧小区更新"）或排除 UI 语境（"更新图层/更新时间/刷新"）；② 或提高触发门槛（需 outlet hint 或 ≥2 接口词）。

### 问题 3（事实修正）：测试 13 passed → 实测 7

- `tests/test_outlet_schema.py` 仅 7 个 `def test_*`，pytest 实测 **7 passed**；与 claude组 声称的"13 passed"不符（除非含其他套件）——需确认口径。

## 三、本轮实施预告检查

### ① 条件触发词表镜像到 emc-patterns.js —— **agree（需 2 个前置）**

- **agree EMC 侧词表**（与 outlet_kb TRIGGER_WORDS 一致·方案 A）——符合出口驱动开发（触发词是"EMC 理解什么问句出卡"·放 EMC 侧合理）；
- **前置 1**：先修"更新"过宽（问题 2）再镜像——否则前端误触发与后端同源；
- **前置 2**：**双源漂移守卫**——outlet_kb TRIGGER_WORDS（后端）与 emc-patterns.js（前端）为双份，项目已有"字段字典前后端同步漂移"教训（validate_field_dict_sync.py）——建议：单一权威源（outlet_kb）+ emc-patterns 镜像 + 新增同步 CI（或 emc-patterns 从后端派生）；
- **触发位置**：前端触发应与后端 `resolve_outlet_id` 一致（避免"前端判定出卡·后端路由未命中"或反之）——建议触发判定收敛在后端（finalStep 后一次调用），前端只渲染。

### ② 前端 markdown 卡片渲染（仿 .cpd-guide-card·既有 token）—— **agree**

- 符合设计语言铁律（复用既有 token/组件模式·不新造样式）；
- **建议**：卡片渲染为纯模板函数（7 要素 → markdown/HTML）·数据全部来自 `build_outlet_schema` 返回的 JSON（前端不自行计算/不补字段）——保持"数字后端算、前端只摆"的分层；
- **注意**：卡片中的 `{{show:图层}}` 等联动需复用既有 `renderAnswer` 的 ref 解析（getValidRefNames）——不另造联动机制。

## 四、结论

- **Wave 0 核心：有条件通过**——方向正确（确定性组装/诚实标注/尺度分派）；修 2 项后转通过：① 字段解析去限定词（renewal_sequence 丢值）② 触发词"更新"过宽；
- **测试**：补 3 个缺口用例（qualifier 解析、`更新图层` 误触发负测试、体检契约命中）——与实施同包；
- **预告实施**：触发词表镜像 + 卡片渲染均 agree 方向，按前置条件执行（先修触发词·加同步守卫·渲染纯模板）。

---

*本报告为 Codex 组独立 SCAN；Wave 0 经 pytest 实测（7 passed）+ 组装器运行级三例验证（S2 正常/S3 字段丢值/更新图层误触发），未引用对方报告。*
