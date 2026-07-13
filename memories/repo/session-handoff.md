# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月13日（5.80 字段语义层 P1 收工）| 分支 `main`（**本地领先 origin 11 commit 待用户手动 push**）| 本次会话 = 5.77（P0d 第四态+P1 ask_user+P3 沙箱骨架）+ 5.78（顶栏 build 号）+ 5.79（用地分类固化）+ 5.80（字段语义层 P1）

---

## 当前节点：5.80 字段语义层 P1 完成，下会话 P2（profile+LLM 推断）→ P3（catalog/registry 带字段）

### 背景
本次会话从用户"EMC 如何更好理解问题-数据-字段-答案闭环"的想法出发 → 评估合理（业界 data dictionary/semantic layer/schema matching）→ 三方向定（完整/别名层不改源/规则优先 LLM 兜底）→ 固化用地分类权威源 → Plan agent 出字段语义层完整设计 → 实施 P1（字典收敛+alias 解析）。前置的 5.77（体验闭环+沙箱骨架）也已落地。

### ✅ 本会话已做（5.77→5.80）
- **5.77 P0d+P1+P3 沙箱骨架**：EXIT_PARTIAL 第四态（做成一部分+标注局限+引导下一步）+ ask_user 主动澄清（速率上限/历史恢复/续作链/注入转义）+ api/sandbox.py 沙箱骨架（SAFE_READY=False 未挂 /run，frame-based trust，19 测试过）。两组 Workflow 对抗验证揪 CRITICAL fallback_annotated 误判+10 项，全修，0 回归。
- **5.78 顶栏 build 号**：serve.py _inject_header_version 注入（build：短哈希）到顶栏 .title-version span（与 _inject_title 同源，换环境识别）。
- **5.79 国标用地分类固化**：[ai_qa/landuse_codes_2023.py](ai_qa/landuse_codes_2023.py) 单一权威源（24 一级/111 二级/40 三级 + 代码 + landuse_name/level/parent/children/search + EMC_PRESET_TO_GB）+ docs 概览 + CLAUDE.md/memory 索引。**读 .py 勿再读 PDF**。诚实差异：指南述 113/140 但 PDF 实际 111/40（三级类仅 06-12 城镇建设类），以 PDF 为准。
- **5.80 字段语义层 P1**：[core/field_dictionary.py](core/field_dictionary.py)（35 roles 权威源 + resolve_role/alias/find_boundary_name_column/validate_llm_roles）+ [frontend/js/field_dictionary.js](frontend/js/field_dictionary.js)（镜像 + findKeyByRole）。收敛 9 处零散映射（state.js/geo_routes/geo_registry/range_selector/landuse_colors/import.js）。修 pandas Index 真值歧义 bug。物理列名不改。

### 🔍 验证（已过 + 待复现）
- **静态全过**：py_compile 后端 + node --check 前端 + field_dictionary 自检（35 roles）+ prompts format。
- **pytest 152 passed**，6 failed 全预存环境问题（SnowNLP/geocode×2/renewal/h3×2），与本改动无关，**0 新回归**。
- **待用户带 key 复现**：P0d（对账 missing→partial 卡）/ P1 ask_user（模糊问题→胶囊点选续作）/ 字段语义层 alias（上传"名称"列→where 自动解析）。

### 待 push（用户手动）
本地领先 origin 11 commit：`02df5af`(5.77 代码) / `e388104`(5.77 交接) / `2df8fe7`(5.78 build) / `0e9bf00`(5.78 交接) / `cd29a8d`(5.79 用地分类) / `6d7c014`(5.80 字段语义层 P1) + 之前 5 (5.72-5.76)。`git push` 即可。

### ⬜ 下会话：字段语义层 P2 → P3（主线）+ P3 沙箱挂 /run（支线）
**主线 = 字段语义层**（plan: `C:\Users\admin\.claude\plans\emc-field-semantic-layer.md`）：
1. **P2 · profile + LLM 推断端点（周级，3-5 天）**：
   - 扩 [import.js coercePropertyTypes](frontend/js/import.js)(L170) 为 `profileFields`（dtype+samples+stats+datetime）。
   - [ai_qa/prompts.py](ai_qa/prompts.py) 加 `build_field_infer_prompt(fields, layer_kind, context)`。
   - [api/aiqa_routes.py](api/aiqa_routes.py) 新增 `POST /aiqa/profile_fields`：仅对规则 miss 字段调 LLM，复用 [chat_with_fallback](ai_qa/llm.py)（tier='flash', stream=False, json_mode=True，5.71 韧性 DeepSeek→Ark→讯飞）。`validate_llm_roles` 校验 role 在字典内。
   - 前端 upload 流程：profile → labelCanonicalRoles（规则）→ miss 调 /aiqa/profile_fields → 存 `_fieldCardCache`（tools.js 模块级 Map）。
   - [core/geo_registry.py _FIELD_CACHE](core/geo_registry.py)(L38) 扩支持 GeoJSON 指纹 key + `field_cards` 值。
   - 降级：LLM 全不可用 → 返 {fields:[],error}，不阻塞上传（只标规则命中的字段）。
2. **P3 · catalog/registry 带字段 + 自产层声明（2-3 天）**：
   - [core/field_dictionary.py](core/field_dictionary.py) 补全自产层契约字段声明（polarity_index/_level/density/Gi_Z 等 self_produced:True）。
   - [tools.js _fieldSamples](frontend/js/ai_qa/tools.js)(L282) 升级 `field=type:role:sample`，过滤改 `isRenderContract`（保留 polarity_index 等自产契约，过滤 _level/_ui 渲染契约）。
   - [tools.js formatRegistry](frontend/js/ai_qa/tools.js)(L221) 追加 `[字段: field:role,...]` 段（保持 `层名（tool·round）` 前缀不破坏 _extractClaimedLayers 正则）。
   - [tools.js addResultLayer](frontend/js/ai_qa/tools.js)(L183) 加可选 `fields` 参数存入 `_registry`。
   - [core/geo_registry.py _point_layer_overview](core/geo_registry.py)(L44) 返回加 `field_cards`；[tools.js formatGeoCatalog](frontend/js/ai_qa/tools.js)(L263) 渲染。

**支线 = P3 沙箱挂 /run**（月级计划另一支，可并行）：
- 先重跑 `py -m pytest tests/test_sandbox.py -q` + 人审 [api/sandbox.py](api/sandbox.py) 确认安全，再 `SAFE_READY=True`。
- 新建 [api/run_routes.py](api/run_routes.py)（run_router，POST /run 调 sandbox.run_sandbox，范式照 geo_routes）+ [api/main.py L80](api/main.py) 条件挂载（`if SAFE_READY: app.include_router`）。
- [tools.js](frontend/js/ai_qa/tools.js) 加第 15 工具 run_python（POST /api/v1/run，复用 addResultLayer，registry 自动记 provenance）。
- [paradigm.py L192](ai_qa/paradigm.py) 后加 `CODE_EXEC_CATALOG` + `code_exec_catalog_text()`。[prompts.py](ai_qa/prompts.py) 加规则 8（何时 run_python）。[panel.js _renderCharts](frontend/js/ai_qa/panel.js) 扩 `{{fig:ID}}` 渲染 matplotlib PNG。
- **挂 /run 须叠 OS 级隔离**（open builtin 不拦/纯 Py 反射绕过是已知局限，sandbox.py docstring 文档化）。

### 承重（必守，下会话续改时留意）
- **字段语义层**：物理列名不改（alias 解析只读 columns 不 rename，除 resolve_boundary 临时层 nameField→name 已有行为）；registry 扩展（P3）保持 `层名（tool·round）` 前缀不破坏 5.74 _extractClaimedLayers 对账；LLM 推断（P2）复用 chat_with_fallback 不新写调用；自产层契约只声明不改产出；field_dictionary 在 core/（不放 ai_qa/，避免 core 反向依赖）；land_use_class 值域引用 landuse_codes_2023.py 不重复硬编码。
- **四态出口契约**（5.77）：EXIT_RESULT/GAP/CONCEPT/PARTIAL 扩非替换；fallback_annotated 走 result 不走 partial；卡片模板化+动态值 _esc 转义；诚实门 _verifyClaims 不被跳；ask_user 速率上限（_consecutiveAsks≥2 禁止）。
- **5.74 registry/对账 tool-agnostic**：code-exec run_python 复用。
- **沙箱红线**（P3 挂 /run）：SAFE_READY=False；挂 /run 前必复验沙箱单测+人审+OS 隔离；frame-based trust 不破。
- "永不裸输原始 token"；思考透明 5.70 不动；commit/push 分离（用户手动 push）；专业词+通俗解释（用户初学者）。

### 本轮改的关键文件（下会话续改看这些）
- 字段语义层：[core/field_dictionary.py](core/field_dictionary.py)（35 roles + resolve_role L100 + resolve_field_alias L120 + find_boundary_name_column L155 + validate_llm_roles L175）/ [frontend/js/field_dictionary.js](frontend/js/field_dictionary.js)（镜像 + findKeyByRole）
- alias 注入：[api/geo_routes.py](api/geo_routes.py)（_apply_attr_filter L72 + extract_feature L204）/ [core/geo_registry.py](core/geo_registry.py)（resolve_boundary L162 GeoJSON 推断 + _point_layer_overview L44 + _FIELD_CACHE L38）/ [core/range_selector.py](core/range_selector.py)（name_col L128）
- 前端收敛：[frontend/js/state.js](frontend/js/state.js)（FIELD_SYNONYMS re-export L995）/ [frontend/js/import.js](frontend/js/import.js)（detectColorMode L562 findKeyByRole）/ [frontend/js/landuse_colors.js](frontend/js/landuse_colors.js)（dominantDLMC L79）
- 用地分类：[ai_qa/landuse_codes_2023.py](ai_qa/landuse_codes_2023.py)（24/111/40 + 查询函数 + EMC_PRESET_TO_GB）
- 出口/对账/ask（5.77）：[harness.js](frontend/js/ai_qa/harness.js)（_esc/composePartialCard/对账/partial 裁定/ask 分支）/ [panel.js](frontend/js/ai_qa/panel.js)（onAskUser/_consecutiveAsks/_exitBadge/_followUps）/ [stages.js](frontend/js/ai_qa/stages.js)（parseAgentStep isAsk）/ [prompts.py](ai_qa/prompts.py)（schema/rule8/FINAL）/ [manifesto.py](ai_qa/manifesto.py)（四态出口）
- 沙箱（5.77）：[api/sandbox.py](api/sandbox.py)（SAFE_READY=False）+ [tests/test_sandbox.py](tests/test_sandbox.py)（19 测试）/ api/run_routes.py + main.py L80（下会话挂）
- LLM 韧性（P2 复用）：[ai_qa/llm.py](ai_qa/llm.py)（chat_with_fallback）

### 承重 memory 索引
- 本轮相关：`emc-tri-state-exit-contract`（出口契约已扩四态）/ `landuse-codes-2023`（用地分类权威源读 .py 勿读 PDF）/ `commit-only-user-pushes` / `pro-term-plus-plain-meaning` / `maintain-revision-log`+`todo-revision-log-sync` / `chinese-all-deliverables` / `no-handoff-on-routine-commit`（说"交接"才覆写本卡）
- 计划文件：`C:\Users\admin\.claude\plans\calm-discovering-snowflake.md`（月级全计划 P0-P3）/ `C:\Users\admin\.claude\plans\emc-field-semantic-layer.md`（字段语义层 P1-P3 完整，P1 已实施）

---

## 新会话 prompt（复制即用）

```
继续 EMC 字段语义层实施（plan: emc-field-semantic-layer.md，P1 已完成），本次做 P2 → P3。
上次 5.80 完成 P1（core/field_dictionary.py 35 roles + alias 解析 + 收敛 9 处，物理列名不改，pytest 152 passed 0 回归），commit 6d7c014（待用户 push）。
本次从 P2 开始：扩 import.js coercePropertyTypes 为 profileFields（dtype+samples+stats+datetime）+ ai_qa/prompts.py 加 build_field_infer_prompt + api/aiqa_routes.py 新增 POST /aiqa/profile_fields（仅规则 miss 字段调 LLM，复用 chat_with_fallback tier='flash' stream=False json_mode=True）+ validate_llm_roles 校验 + 前端 upload 流程 profile→规则标注→miss 调端点→存 _fieldCardCache + _FIELD_CACHE 扩 GeoJSON 指纹 key。降级：LLM 全不可用不阻塞上传。然后 P3：_fieldSamples 升级 field=type:role:sample + formatRegistry 追加 [字段:...] + addResultLayer 加 fields 参数 + 自产层契约声明。
承重：物理列名不改（alias 只读）/ registry 扩展保持层名前缀不破坏 5.74 对账 / LLM 复用 chat_with_fallback / 自产层只声明 / field_dictionary 在 core/ / land_use_class 值域引用 landuse_codes_2023.py / 思考透明 5.70 不动 / commit 只不 push / 专业词+通俗解释。
先读交接卡 memories/repo/session-handoff.md + plan 文件 emc-field-semantic-layer.md，然后从 P2 动手。
```
