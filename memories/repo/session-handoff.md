# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月13日（5.82 字段语义层 P3 收工，P1-P3 全闭环）| 分支 `main`（**本地领先 origin 7 commit 待用户手动 push**）| 本次会话 = 5.81（字段语义层 P2 profile+LLM 推断）+ 5.82（字段语义层 P3 catalog/registry 带字段）

---

## 当前节点：5.82 字段语义层 P1-P3 全闭环，下会话可选 P3 沙箱挂 /run（支线升主线）

### 背景
字段语义层（让 EMC 上传任何数据都能自动识别字段语义角色、where 用别名自动解析、catalog/registry 带字段卡片给 LLM）三阶段全做完。业界 data dictionary + semantic layer + schema matching 标准做法，且是"收敛上抬"非"重起炉灶"（EMC 已有 9 处零散映射）。本次（5.81/5.82）续 P2+P3，P1 在 5.80 已落。

### ✅ 本会话已做（5.81 P2 + 5.82 P3）
- **5.81 字段语义层 P2**（commit `6d05d9f`+`dc0fb2d`）：profile + LLM 字段角色推断（规则优先 LLM 兜底）。
  - [frontend/js/import.js](frontend/js/import.js) `profileFields(fc)`：纯读画像 `{field:{dtype,samples,stats}}`，dtype 含 **datetime**（正则+Date.parse 判，值不转换只标 dtype）；stats number→min/max/mean、datetime→min/max(ISO)、string→distinct 近似。
  - [ai_qa/prompts.py](ai_qa/prompts.py) `build_field_infer_prompt` + `FIELD_INFER_TEMPLATE`：范式照 build_diagnose_prompt，从 core.field_dictionary 拉 17 个用户上传 role 候选 + description，要求严格 JSON `{field:{role,confidence,reason}}`。
  - [api/aiqa_routes.py](api/aiqa_routes.py) `POST /aiqa/profile_fields`：复用 `chat_with_fallback`（tier='flash' stream=False json_mode with_reason=False，5.71 DeepSeek→Ark→讯飞韧性链）；全 provider 不可用 → try/except LLMError → 降级 `{fields:{},degraded:True}` 不阻塞；`_parse_field_json` 容错解析（照 review._parse_review_json）；`validate_llm_roles`（P1 已实现，零改动）校验非法 role 置 null。
  - [frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js) `_fieldCardCache`(Map by layerId) + `getFieldCard`（profile→resolveRole 规则标注→miss 调 fetchProfileFields→source:'rule'|'llm'|'rule-miss' 合并→缓存）+ `fetchProfileFields`（POST，j.detail||j.error）。**懒加载**：首次问询才算，不改 main.js 上传流程。
- **5.82 字段语义层 P3**（commit `5747430`+`b1b896c`）：catalog/registry 带字段卡片 + _fieldSamples 语义升级。
  - [tools.js _fieldSamples](frontend/js/ai_qa/tools.js)：async，格式 `field=dtype:role:sample`（num/dt/bool/cat）；过滤从硬 `k[0]!=='_'` 改 `isInternalField(k)||isRenderContract(role)`——**保留自产 polarity_index/point_count**、**过滤渲染契约** _level/_ui；buildContext 改 `await _fieldSamples(l.fc,6,l.id)`（Promise.all）。
  - [tools.js formatRegistry](frontend/js/ai_qa/tools.js)：每条 artifact 后追加 `[字段: f1:role1, …]`（前5+…）。字段来源优先 registry 项 `fields`（addResultLayer 新增可选参）；缺则反查 `getLayer(id).fc` 调 `_fieldBrief` 同步 resolveRole 标（不调 LLM）。**5.74 对账安全**：verbRe 字符类排除 `[` `]`，字段段方括号包裹不误抽（实测字段 token 零泄漏）；字段段禁入图层名与 `{{show:}}`（showRe 不排除方括号会吞）。
  - [core/geo_registry.py](core/geo_registry.py) `_point_layer_overview` 返加 `field_cards`（规则标注 `{field:{role,source:'rule'}}`）；`_FIELD_CACHE` value 扩 field_cards；`list_point_layers` 透传。前端 formatGeoCatalog 渲染点层 `k[role]:v`。
  - P3.1 自产层声明 P1 已闭环（11 self_produced + 6 render_contract 标记全在），仅核对无工作。原 P2.6 _FIELD_CACHE 扩展合并到 P3.6（与消费同处，避免死存储）；`_geojson_fingerprint` 按 YAGNI 推迟到有需求。

### 🔍 验证（已过）
- **静态全过**：py_compile 后端（prompts/aiqa_routes/field_dictionary/geo_registry）+ node --check 前端（import.js/tools.js）。
- **功能自检全过**：build_field_infer_prompt 无未填槽+花括号配对 / validate_llm_roles 合法通过非法置 null / profileFields dtype+stats 正确（含 datetime）/ resolve_role 规则-miss 分流 / _fieldSamples 格式+过滤（polarity_index 保留/_level 过滤）/ **对账正则安全**（构造含 `[字段:...]` draft→verbRe/showRe 抽出 names 零字段 token 泄漏）。
- **pytest 152 passed**，6 failed 全预存环境问题（SnowNLP/geocode×2/renewal/h3×2），与本改动无关，**0 新回归**（P2 后 + P3 后各跑一次，均 152/6）。

### ✅ P2 端点真调已通过（key 在 .env，直接调，不推用户）
- **已实测**（本次会话末尾跑通）：复用 `app_main._load_dotenv` 手写加载 .env（**DEEPSEEK_API_KEY=SET**，Ark/讯飞未配）→ `build_field_infer_prompt` → `chat_with_fallback(deepseek-v4-flash, stream=False, json_mode=True)` → `_parse_field_json` → `validate_llm_roles`。
- **结果 3/3 全对**：心情（规则 miss→LLM）→ polarity 0.9；评分（规则命中 score）→ score 0.9（LLM 一致）；行政区名（规则 miss→LLM）→ boundary_name 0.9。role 全合法过 validate。整条 P2 链路真调闭环。
- **教训**：key 在 .env 就该当场调实验证，别写"待用户带 key 复现"推出去（用户已指出）。
- **端到端待肉眼验**（非阻塞）：上传含非 variant 列→首次问询看前端 LLM 推断 role 标注是否准；registry `[字段:...]` 段在真 agent loop 里是否被 LLM 正确引用。

### 待 push（用户手动）
本地领先 origin 7 commit：`6d7c014`(5.80 P1) / `a1a306f`(5.80 交接) / `cd29a8d`(5.79 用地分类) + 本次 4：`6d05d9f`(5.81 P2 代码) / `dc0fb2d`(5.81 日志) / `5747430`(5.82 P3 代码) / `b1b896c`(5.82 日志)。`git push` 即可。

### ⬜ 下会话：字段语义层主线已收，可选支线升主线
**字段语义层 P1-P3 全闭环**，无遗留主线。下会话可选项：
1. **P3 沙箱挂 /run**（原月级支线，可升主线）：先重跑 `py -m pytest tests/test_sandbox.py -q` + 人审 [api/sandbox.py](api/sandbox.py) → `SAFE_READY=True` → 新建 [api/run_routes.py](api/run_routes.py)（POST /run 调 sandbox.run_sandbox）+ [api/main.py](api/main.py) 条件挂载 + [tools.js](frontend/js/ai_qa/tools.js) 加第 15 工具 run_python + [paradigm.py](ai_qa/paradigm.py) `CODE_EXEC_CATALOG` + [panel.js](frontend/js/ai_qa/panel.js) `{{fig:ID}}` 渲染。**挂 /run 须叠 OS 级隔离**（open builtin 不拦/纯 Py 反射绕过是已知局限，sandbox.py docstring 文档化）。范式：run_python 复用 addResultLayer，registry 自动记 provenance（5.74 对账 tool-agnostic）。
2. **其他**：用户定。

### 承重（必守，下会话续改时留意）
- **字段语义层（已完成，守不退）**：物理列名不改（alias/profile/getFieldCard/_fieldSamples 全只读 fc.properties）；registry 扩展保持 `层名（tool·round）` 前缀+字段段方括号包裹不破 5.74 对账（字段段禁入图层名/{{show:}}）；LLM 推断复用 chat_with_fallback 不新写调用；自产层契约只声明不改产出（_attach_4x5_attrs 未碰）；field_dictionary 在 core/（ai_qa→core 合法，反向依赖禁止）；land_use_class 值域引用 landuse_codes_2023.py 不硬编码；懒加载不改 main.js 上传流程；思考透明 5.70 不动。
- **四态出口契约**（5.77）：EXIT_RESULT/GAP/CONCEPT/PARTIAL 扩非替换；fallback_annotated 走 result 不走 partial；卡片模板化+动态值 _esc 转义；诚实门 _verifyClaims 不被跳；ask_user 速率上限（_consecutiveAsks≥2 禁止）。
- **5.74 registry/对账 tool-agnostic**：code-exec run_python 复用（若做沙箱支线）。
- **沙箱红线**（若挂 /run）：SAFE_READY=False（当前）；挂 /run 前必复验沙箱单测+人审+OS 隔离；frame-based trust 不破。
- "永不裸输原始 token"；commit/push 分离（用户手动 push）；专业词+通俗解释（用户初学者）。

### 本轮改的关键文件（下会话续改看这些）
- 字段语义层 P2：[frontend/js/import.js](frontend/js/import.js)（profileFields + _DT_PATTERNS/_looksDatetime/_profileStats）/ [ai_qa/prompts.py](ai_qa/prompts.py)（FIELD_INFER_TEMPLATE + build_field_infer_prompt）/ [api/aiqa_routes.py](api/aiqa_routes.py)（ProfileFieldsIn + _parse_field_json + post_profile_fields）/ [frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js)（_fieldCardCache + getFieldCard + fetchProfileFields，L43-100 区）
- 字段语义层 P3：[tools.js](frontend/js/ai_qa/tools.js)（_fieldSamples async + _dtypeTag + _fieldBrief + formatRegistry 带字段 + addResultLayer fields 参 + buildContext Promise.all + formatGeoCatalog field_cards）/ [core/geo_registry.py](core/geo_registry.py)（_point_layer_overview field_cards + _FIELD_CACHE 扩 + list_point_layers 透传）
- P1 字典（权威源，未本次改）：[core/field_dictionary.py](core/field_dictionary.py)（35 roles + resolve_role/alias/validate_llm_roles L253/find_boundary_name_column/is_self_produced/is_render_contract）/ [frontend/js/field_dictionary.js](frontend/js/field_dictionary.js)（镜像 + resolveRole/isRenderContract/isInternalField）
- LLM 韧性（P2 复用）：[ai_qa/llm.py](ai_qa/llm.py)（chat_with_fallback L214，全失败抛 LLMError）/ [ai_qa/review.py](ai_qa/review.py)（_parse_review_json L122 + review_answer L183 降级范本）
- 沙箱（下会话支线）：[api/sandbox.py](api/sandbox.py)（SAFE_READY=False）+ [tests/test_sandbox.py](tests/test_sandbox.py)（19 测试）/ api/run_routes.py + main.py（待建/挂）

### 承重 memory 索引
- 本轮相关：`emc-tri-state-exit-contract`（出口契约四态）/ `landuse-codes-2023`（用地分类权威源读 .py 勿读 PDF）/ `commit-only-user-pushes`（commit 后告知待 push）/ `pro-term-plus-plain-meaning`（专业词+通俗解释，用户初学者）/ `maintain-revision-log`+`todo-revision-log-sync`（每事同步）/ `chinese-all-deliverables`（交付物中文）/ `no-handoff-on-routine-commit`（说"交接"才覆写本卡）/ `design-language-consistency-iron-rule`（_fieldSamples 过滤走语义层 isRenderContract 不走硬下划线）
- 计划文件：`C:\Users\admin\.claude\plans\calm-discovering-snowflake.md`（月级全计划 P0-P3）/ `C:\Users\admin\.claude\plans\emc-field-semantic-layer.md`（字段语义层 P1-P3 父 plan，全闭环）/ `C:\Users\admin\.claude\plans\emc-plan-emc-field-semantic-layer-md-p1-zazzy-duckling.md`（P2-P3 执行 plan，全闭环）

---

## 新会话 prompt（复制即用）

```
继续 EMC。字段语义层 P1-P3 已全闭环（5.80-5.82，commit 6d7c014/6d05d9f/5747430，待用户手动 push）。
P2 端点真调已通过（.env 里 DEEPSEEK_API_KEY 已配，3/3 字段推断正确：心情→polarity/评分→score/行政区名→boundary_name）。
本次按交接卡选下会话主线（建议 P3 沙箱挂 /run 支线升主线，或用户另定）。
承重：物理列名不改 / registry 字段段方括号包裹不破 5.74 对账 / LLM 复用 chat_with_fallback /
自产层只声明 / field_dictionary 在 core/ / 思考透明 5.70 不动 / commit 只不 push / 专业词+通俗解释。
先读交接卡 memories/repo/session-handoff.md，再动手。
```
