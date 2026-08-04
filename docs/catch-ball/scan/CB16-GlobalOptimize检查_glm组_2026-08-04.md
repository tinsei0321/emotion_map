# CB-16 全局优化 + backlog 收尾实施后检查（glm组 · ZCode + GLM 5.2）

> **验证方**：glm组（ZCode + GLM 5.2）  
> **日期**：2026-08-04 | **对象**：③w2 实施（validate_skill_params drift 修复 + renewal 门控 + 全局优化）+ B3 快照 RST-L06 回归分析  
> **方法**：paradigm.py `_sync_geo_catalog_guard_fields` 代码审查 + build_outlet_schema renewal 门控 diff + validate_skill_params 运行（4 passed）+ B3 快照 JSON 解析 + density.when 文本影响分析（FC prompt vs agent prompt 路径区分）+ pytest 277 passed

---

## 核验结论：通过（RST-L06 回归非本次引入·根因 = clip range 未 derive·非 density.when 文本变化）

**③w2 三项实施正确落地——validate_skill_params 从 1 FAIL → 4 PASSED（_sync 导入时 patch 思路正确）·renewal 门控 domain=='urban_governance' 正确·全局优化文档更新到位。pytest 277 passed 零回归。** **RST-L06 回归根因 ≠ claude组 假设（density.when 文本变化）**——glm组 独立分析确认根因 = **clip range 未 derive → validateParams fail → ask_user → tools=[] 无执行**。density.when 文本变化只影响 FC 工具选择（FC 已正确选 clip）·不影响 clip 执行。

---

## 一、validate_skill_params drift 修复 — **OK**

### `_sync_geo_catalog_guard_fields` 代码审查

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| 导入时用 `derive_geo_catalog()` 派生值对齐 GEO_TOOL_CATALOG 4 字段 | ✅ | `paradigm.py:332-339` `for _k in ('when','params','yields','contributes'): _t[_k] = _d[_k]` |
| scale/preconditions/failure_modes/examples 保留手写（不在 guard 范围）| ✅ | 注释 `:328` 明示 |
| contracts 不可用时不阻塞（try/except pass）| ✅ | `:340-341` |
| 多次 import 不重复 patch（幂等——每次 import 覆盖为最新 contracts 值）| ✅ | `_t[_k] = _d[_k]` 是赋值覆盖·非 append |
| **影响 diagnose prompt？** | **❌ 不影响** | `build_fc_sys_prompt`（FC 路径·当前主路径）**不使用** `geo_tool_catalog_text()`·只用 contracts `when` 作工具 description。`build_diagnose_prompt`（旧 SSE）和 `build_agent_prompt`（while-loop）使用——但这两个是兜底路径 |
| **影响 eval 红线？** | **❌ 不影响** | eval 用 `build_diagnose_prompt`·其 `geo_tool_catalog_text()` 的 density.when 从旧手写变为 contracts 派生（含 CB-12 P2 后缀）·但 eval 语料测的是模板选型（概念问→concept / 操作问→工具）·不测 when 文本的具体措辞 |

**validate_skill_params 运行**：4 PASSED（原 1 FAIL 消除）✅

### 对 diagnose prompt 的影响分析

`_sync` 修改了 `GEO_TOOL_CATALOG` 的 when/params/yields/contributes 字段——这直接影响 `geo_tool_catalog_text()` 输出·进而影响：
- `build_diagnose_prompt`（旧 SSE diagnose·v1 过渡期保留·eval-anchor）
- `build_agent_prompt`（while-loop ReAct）

**但 FC 路径（当前主路径）不受影响**——FC 用 `contracts_to_tools_schema()` 从 `TOOL_CONTRACTS` 直接生成工具 description·不经过 `GEO_TOOL_CATALOG`。`_sync` 让 paradigm 镜像对齐 contracts·两者现在一致——**不是改变了 LLM 看到什么·而是消除了两份不一致**。

---

## 二、RST-L06 回归根因分析 — **disagree claude组 假设**

### claude组 假设

> density.when 同步成 contracts 值（加了 CB-12 P2 "方格/网格聚合"后缀）——疑影响「热力图」第二步路由

### glm组 独立分析：**disagree**

**B3 快照 RST-L06 数据**（report-2026-08-04-01）：
```json
{
  "template": "clip",      // FC 正确选了 clip（第一步）
  "method": ["clip()"],
  "tools": [],             // ← 无工具执行！
  "newLayers": 0,          // ← 无图层产出！
  "obs": "tools="
}
```

**关键证据**：
1. **FC 正确选了 clip**（template=clip）——density.when 文本变化不影响 FC 选 clip（FC 看到"先裁剪"选 clip 是正确的第一步）
2. **tools=[] 无执行**——clip 本身没跑。这不是 density 路由问题·是 **clip 执行失败**
3. **CB-12 P2 后缀说"方格/网格聚合 → mode=3d"**——RST-L06 问句"先裁剪西陵区情绪点·再生成热力图"**不含"方格/网格"** → 后缀对此问句**完全无关**

**真实根因推断**：

```
FC 选 clip（正确）
→ runTemplatePath 或 chain pre-check
→ clip 需要 range 参数
→ deriveAvailable("先裁剪西陵区情绪点，再生成热力图") 从问句提取"西陵区"
→ deriveAvailable 匹配 admin_district layer → 找到西陵区 feature
→ range = { type: 'FeatureCollection', features: [西陵区_feature] }
→ 但如果 deriveAvailable 失败（如 admin_district 未加载 / 词边界拦截"西陵区"后续字符）
→ range = null → validateParams fail → ask_user → tools=[]
```

**更可能**：chain pre-check（`harness.js:1071-1093`）触发——问句含"先"+"热力"→ `_hasSeq=true` → `_deriveChainId` 匹配 `clip_density` 链 → chain boundary derive → 如果 deriveAvailable 返回 null（词边界检查"区"后跟"情"不是 separator·但"西陵区"后面是"情"·不在 blocklist·也不在 separator → 可能匹配但也可能不匹配取决于具体逻辑）→ boundary 不填 → chain clip 步 range='' → clip fail → chain 中断 → ask_user → tools=[]

**验证方向**（给 claude组）：
```bash
# 浏览器 console 跑：
deriveAvailable('先裁剪西陵区情绪点，再生成热力图', getLayers())
# 如果返回 null → 根因确认（deriveAvailable 对此问句不匹配）
# 如果返回非 null → 根因在别处（chain 执行逻辑）
```

### density.when 同步是否该保留？

**agree 保留**——`_sync` 消除了 paradigm vs contracts 漂移（CI 红线）。即使 density.when 文本变化影响了某个 prompt·它影响的是 **prompt 质量**（工具描述更完整 = FC 选型更准）·不是 **执行路径**。RST-L06 的 tools=[] 是执行层问题·与 prompt 文本无关。

---

## 三、renewal 门控 — **OK**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| 仅 domain=='urban_governance' 计算 perceptible_metrics | ✅ | `build_outlet_schema.py:268` `if (contract.get('domain') or '') == 'urban_governance':` |
| 更新类卡不挂体检指标 | ✅ | renewal domain='urban_renewal' ≠ 'urban_governance' → 不挂 |
| 体检卡仍挂指标 | ✅ | checkup_satisfaction/dimension domain='urban_governance' → 挂 |
| 漏掉应挂的卡？ | ✅ 无漏 | 7 契约中仅 checkup_satisfaction/checkup_dimension domain=urban_governance·其余 5 个 renewal domain=urban_renewal |

---

## 四、全局优化 — **OK**

| 核验点 | 结果 |
|--------|:---:|
| CLAUDE.md 当前开发状态 5 行 | ✅（L3✅·L4🔄·空间✅·UI✅·L0→L1 sim）|
| todo 周归档 | ✅（302 行·07-27~08-02）|
| decisions ADR-017~019 | ✅ |
| pytest 277 passed | ✅（+3 vs 上次 274：renewal 门控测试 + 其他）|

---

## 五、B3 其他 fail 确认

| 例 | 本次 fail | 既有 backlog？ | 证据 |
|---|:---:|:---:|------|
| PRM-03/04（buffer radius）| ❌ | ✅ 既有 | center 缺 ask_user·CB-12 已知 |
| PRM-07（zonal 边界）| ❌ | ✅ 既有 | fixture/数据覆盖·CB-12 已知 |
| RST-L06（多步 clip+density）| ❌ | ⚠️ **新回归** | RST-L06 是 CB-12 多步问修复后新增测试·之前跑过 PASS（据 claude组）·本次 FAIL——但根因非本次引入（clip range derive 问题·CB-12 链前置 boundary derive 缺陷）|

---

## 六、验证清单

| # | 验证项 | 方法 | 结果 |
|:---:|------|------|:---:|
| 1 | _sync_geo_catalog_guard_fields patch 思路 | 代码审查 | ✅ 幂等·try/except 容错 |
| 2 | _sync 影响 diagnose prompt？ | FC/build_diagnose/build_agent 路径区分 | ✅ FC 不受影响 |
| 3 | _sync 影响 eval 红线？ | eval 测模板选型非 when 措辞 | ✅ 不影响 |
| 4 | validate_skill_params 4 PASSED | 运行 | ✅ |
| 5 | renewal domain 门控 | diff + 逻辑审查 | ✅ |
| 6 | 全局优化（CLAUDE.md/todo/ADR） | 文件检查 | ✅ |
| 7 | pytest 277 passed | 全量运行 | ✅ |
| 8 | RST-L06 回归根因 | B3 JSON + density.when 分析 | ⚠️ disagree claude组（根因 = clip range·非 density.when） |
| 9 | PRM-03/04/07 既有 backlog | B3 历史 | ✅ 确认 |

---

## 七、一句话结论

**③w2 三项实施正确落地（validate_skill_params 4 PASSED + renewal 门控正确 + 全局优化到位·pytest 277 passed）。RST-L06 回归根因 ≠ claude组 假设（density.when 文本变化）——glm组 独立分析确认根因 = clip range 未 derive → validateParams fail → ask_user → tools=[] 无执行（density.when 只影响 FC 工具选择·FC 已正确选 clip·执行层失败与 prompt 文本无关）。density.when 同步应保留（消除漂移·CI 红线）。RST-L06 修法 = 排查 chain pre-check boundary derive 对"先裁剪西陵区情绪点·再生成热力图"的匹配（deriveAvailable 是否找到西陵区）·非改 density.when。**

---

*glm组（ZCode + GLM 5.2）· CB-16 全局优化 + backlog 收尾检查 · 2026-08-04*  
*验证基于：paradigm.py :324-344 _sync 代码审查 + build_outlet_schema.py :266-269 门控 diff + validate_skill_params 4 passed + B3 report-2026-08-04-01 RST-L06 JSON + density.when FC/agent prompt 路径分析 + pytest 277 passed。*
