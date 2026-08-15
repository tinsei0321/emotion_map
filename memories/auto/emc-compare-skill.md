---
name: emc-compare-skill
description: EMC compare 区域对比技能（复用 zonal_stats 不造端点）+ _driftRe 拓宽（任意围栏→revise）；compare 路由 eval 测不出靠 browser
metadata: 
  node_type: memory
  type: project
  originSessionId: 64210e14-45f0-4874-b8e9-ced5d44d7f05
---

EMC `compare` 单技能（5.114，commit 8f82ebb）治欢迎胶囊"对比西陵伍家岗"三老毛病（代码块/回答一半/方法不做）。

**compare 技能契约**：
- 复用 `geoFetch('zonal_stats')` 逐区聚合（**不造 geo 端点**，守 [[emc-delegates-to-toolbox]]）；后端 zonal_stats 已 `resolve_field_alias` → compare 继承规范名，自身不重复 alias 逻辑（守 [[emc-aggregate-column-alias-silent-zero]]）。
- `select_template` C 分支：`decision_type=='对比'`（或问句含 对比/比较/VS）→ `compare`，**优先于 scale 的 rank/zonal**。B-track 不受影响。
- 入参 `boundaries`（数组或 `|,，、` 分隔，上限 4 区）；`normalizeParams` 加 `regions/areas→boundaries`（**不动 `boundary`**——zonal/clip/merge/area_stats 用单数）。
- 三件套同步：`paradigm.py` TEMPLATE_REGISTRY + select_template + 决策树文本；`tools.js` compare_regions；`stages.js` SKILL_DEFS 镜像（守 [[js-chinese-identifier-trap]] 不涉，纯英文标识）。

**_driftRe 拓宽**（harness.js:516）：原只拦 action-JSON 代码块→老毛病"非 action 代码块泄漏"。改：草稿含**任意 ``` 围栏**→走 `_reviseOnce` 重写 prose（EMC 结论设计上无代码块，图表用内联 `{chart}/{fig}`，勿围栏）；复用既有 revise-失败→固定卡 通道，不静默 strip。

**Why:** "对比"原只是 decision_type/B-track voice，TEMPLATE_REGISTRY 无一等技能→胶囊承诺的能力 harness 做不了→落 multi/unknown 临场拼→三老毛病随机犯。

**How to apply:** 改 compare 路由/工具须保三件套同步（Py 注册表 ↔ JS SKILL_DEFS）；加 compare 类技能走 `select_template` 单一真相源；**compare 路由 eval 测不出**（19 例无 compare 问句）——验 compare 须 browser 实跑（C6，[[emc-eval-empty-context-vs-runtime]]）。diagnose prompt 因技能目录变→改完必重跑 `py tests/eval_template_flash.py`（PYTHONPATH=.，5.114 实测 16/19=84% PASS）。关联 [[emc-domain-lens-threading]]。

**5.129 中文地名解析 + E2E 测试范式（boundary-resolve.js）**：compare/zonal 的 boundary 入参现接受**中文地名**（不只 preset_id）—— `frontend/js/ai_qa/boundary-resolve.js` 惰性建面域 preset（admin_*/renewal_*，跳 land_*）的 name→feature 索引（全名 + 去尾缀 区/街道/社区），中文地名→单 feature GeoJSON dict（后端 resolve_boundary 已支持 dict 路径；feature 显式设 properties.name 供 zonal_stats polygon_name_col）。治 5.115：LLM 不知 preset_id 英文，只能填问句中文名；地名是 admin_district feature 的 MC 属性非 preset_id。**E2E 测试 compare**：地图**空启动**（main.js:244 "No seed sample"，点层只来自 Import）→ `main.js` 加 `?e2e=1` test seam 暴露 `window.__emcTest.loadPoints(fc)` 注入 fixture 点层（复用 Import 装载逻辑，零生产影响，tolerate 底图未加载——zonal_stats 只需 state 可见点层不依赖地图渲染）；`tests/browser/test_compare_regions.py` **自管 serve.py**（subprocess+health wait，单命令可跑，**不用 with_server.py**——后者下 main.js seam 长时间不可用，环境怪癖）。硬断言挂网络层（2× POST zonal_stats 200 + rows）非 LLM 散文。
