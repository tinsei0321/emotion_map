"""思考层 · Agent Loop prompt builder（ReAct）。

替代上一轮的 think/answer/review 三阶段。现两阶段：
- agent_step ：ReAct 每轮，输出 {thought, action} JSON（流式 reasoning + content JSON）。
- answer     ：agent 决定 answer 后，基于全部探索历史出最终结论（流式 markdown）。

改 prompt 只改本文件。
"""
import datetime as _dt

from ai_qa.manifesto import MANIFESTO
from ai_qa.paradigm import (
    scale_paradigm_text, domain_outlets_text, geo_tool_catalog_text, code_exec_catalog_text,
    template_registry_text, b_track_paradigm_text, select_template_text,
    DIAGNOSE_CARD_FIELDS, DATA_STRATEGY,
)
from ai_qa.industry_kb import industry_kb_brief_text, industry_kb_lens_appendix


def _today_line() -> str:
    """当前现实日期前缀（喂 LLM 让其知「今天」=通用问答的日期语境，与 T1/T2/T3 数据时点无关）。"""
    d = _dt.date.today()
    wk = '周一 周二 周三 周四 周五 周六 周日'.split()[d.weekday()]
    return f'当前现实日期：{d.year}年{d.month}月{d.day}日（{wk}）。\n'


def _inject_tokens(prompt, context_tokens):
    """@关联对象 → 追加约束。"""
    if not context_tokens:
        return prompt
    refs = []
    for t in context_tokens:
        typ = t.get('type', '对象')
        label = t.get('label') or t.get('ref', {}).get('name') or '?'
        refs.append(f'{typ}:{label}')
    return prompt + '\n用户本次@关联的对象（回答/操作须围绕它们展开）：' + '、'.join(refs)


# ── agent_step 阶段：ReAct 每轮，输出 {thought, action} ──────────────────────
AGENT_TEMPLATE = """

═══════════ 本次任务 · Agent Loop 第 {round} 轮（ReAct）═══════════
你在用 Thought-Action-Observation 模式解题：每轮思考一步、做一个动作、看结果、再思考。
本轮你必须输出**严格的 JSON 对象**（仅 JSON，禁 markdown 代码块 / 前后解释 / "我打算…我将调用…"之类的只说不做），结构如下：
{{
  "thought": "这一步你在想什么（口语化、面向用户、可见，如：我先看看当前有哪些数据）",
  "action": {{
    "type": "tool", "name": "工具名", "params": {{...}}
  }}
  // 或（信息已足够时）：
  // "action": {{ "type": "answer" }}
  // 或（关键信息模糊、硬猜风险高时，主动问用户一句）：
  // "action": {{ "type": "ask_user", "question": "你想看哪个区/哪个时点？", "options": ["西陵区", "伍家岗区"] }}
}}
**出口契约铁律**：你的目标是**做成**（调工具产出图层/结论）、**做成一部分并诚实标注局限**（缺一些时保留已做的、标注缺什么、引导补充）、**诚实说做不成**（缺什么→引导上传），或**主动问澄清**（范围/时点/domain 模糊、硬猜风险高时用 ask_user 问一句，别硬猜也别直接 GAP）。零成功且无澄清必要时 harness 会强制出"缺数据卡"——故勿用计划文/代码块敷衍：给动作、answer，或 ask_user。

【可用工具】（action.name 只能取以下值之一，params 仅列出的键）：
- query_layers：查当前已加载的图层/数据（有什么可用）。params: {{}}
- query_zone_stats：查区域极性统计（按维度排序找区域）。params: {{ "criteria": "worst" | "best" | "domain:规划" | "domain:更新" | "domain:运营" | "domain:治理" | "element:设施" | "element:环境" | "element:服务" | "element:文化" | "element:事件", "top": 个数(默认3) }}
- query_attribution：查 4×5 归因（全局或某区域）。params: {{ "zone": "区域名" 或 空字符串(全局) }}
- query_keywords：查关键词/热门话题。params: {{ "polarity": "overall" | "positive" | "negative" }}
- ensure_zone：生成/确保聚合域（仅当无聚合层时用）。params: {{ "analysis": "square" | "zonal"(默认square), "cell_size": 米(square默认500), "polarity": "overall", "mode": "2d" | "3d"(默认2d) }}
- focus_zones：定位区域到地图（飞到+高亮）。params: {{ "names": ["区域A", "区域B"] }}
- open_attribution：展开 Overview 归因面板。params: {{}}
- inspect_zone：深读某聚合域明细。params: {{ "name": "区域名" }}
【GIS 工具】（按 intent/问题尺度自动组合，见下方「GIS 操作目录」附录；**结果自动落地图为新图层**；B 纯操作类必走此类产出图层，允许坐标与裸结果）：
**工具选择决策**：①"某范围内"=clip（点）/extract_feature（面）；②"A 内的 B"（如西陵区内的商业用地）=先 extract_feature(A) 再 overlay(A, B, intersection)；③面∩面/面∪面=overlay（**勿用 clip——clip 只切点，面层会报错**）；④合并多面=merge；⑤周边半径=buffer。
**用地数据模型（重要）**：用地预设（如 land_commercial/land_residential/land_park）是**按地类 dissolve 的全市单面/多面**，**没有"类×区"联合资产**——即无法直接抽取"西陵区的商业用地"。要"某区内的某类用地"，必须**几何叠置**：先 extract_feature(admin_district, 区名) 得该区面 → overlay(layer_a=该区面, layer_b=land_xxx, how="intersection") 得交集。同理"某区内居住+商业两类"= 该区面分别与 land_residential、land_commercial 叠置（或 union 后再叠），不可只传一个 preset 期望自动分区。
**工具链（chain，推荐显式变量）**：多步操作用 `$1`/`$2` 引用前序工具产物（第 1/2 个产图层的工具结果，最稳，不依赖图层名匹配）。例：extract_feature(admin_district, MC/eq/西陵区) 得 `$1` → overlay(layer_a="$1", layer_b="land_commercial", how="intersection") 得西陵区内商业用地。也支持传"已生成的图层名"或 preset_id。
**结果图层命名（重要）**：凡产图层的工具（extract_feature/clip/filter_attr/merge/buffer/overlay）可传 `as` 自定义图层名。**`as` 必须用结果的现实内容命名（如「西陵区内商业用地」「滨江公园·500m」「西陵区·伍家岗区」），严禁用实现术语（叠置/intersection/clip/抽取）**——用户看图，名要说清"这层是什么"。不传 `as` 时系统按内容自动命名兜底。
**图层生命周期（重要·勿死板）**：EMC 组**默认只留最终结果**——链式中间产物（被后续工具引用的，如 extract→overlay 的 extract）自动清理；并列最终结果（居住+商业）保留。**但用户的显式意图优先于该默认**：凡产图层工具可传 `keep: true` 标记"此层要保留"——被标记的层**即使被后续引用也不会被清理**。何时用 keep：① 用户明确说"保留/留下/也显示 某图层"；② 该层本身就是要展示给用户的结论图层（非纯中间步骤），你不确定它会不会被后续引用。**判据：问自己"这层用户最终要在地图上看到吗？"——是，就 keep:true；只是通往结果的跳板，就不传（默认清）。**
- zonal_stats：**宏/中观结论主干**——按行政区/街道/更新单元等边界聚合点层，得每单元极性/点数/4×5 归因+排序。params: {{ "boundary": "admin_district|admin_street|renewal_unit|...(preset_id)", "layer": "(默认 yichang_l2_t1)", "range": "(可选 preset_id 先裁剪)", "pre_filter": "可选，形如 field/op/value 见附录", "top_n": 5 }}
- rank：Top N 排序（最差/最好/按 domain·element 占比）。params: {{ "by": "worst|best|domain:更新|element:设施", "boundary": "preset_id", "top_n": 5, "layer": "(默认L2)", "range": "(可选)", "pre_filter": "(可选)" }}
- filter_attr：按属性筛选用地/极性/domain/element/时点。params: {{ "pre_filter": "field/op/value，如 domain/eq/urban_renewal", "layer": "默认L2", "range": "可选", "as": "图层名(现实内容)", "keep": "可选 true=保留此层免清理" }}
- extract_feature：从面边界按属性抽单要素为独立面图层（**裁出某区/某单元**，自动落地图）。params: {{ "layer": "preset_id(如 admin_district)", "where": "field/op/value(如 MC/eq/西陵区，field 见 catalog name_field)", "as": "图层名(现实内容)", "keep": "可选 true=保留此层免清理" }}
- clip：按几何裁剪（某区/某公园范围内的点，自动落地图）。params: {{ "range": "preset_id(如 land_park/admin_district)", "layer": "(默认L2)", "pre_filter": "可选 field/op/value", "as": "图层名(现实内容)", "keep": "可选 true=保留此层免清理" }}
- area_stats：各类用地/各单元面积占比。params: {{ "boundary": "preset_id", "group_by": "字段(如 name)" }}
- merge：合并/dissolve（几街道合成片区/同类用地合并）。params: {{ "boundary": "preset_id", "by": "字段|空=全部合并", "as": "图层名(现实内容)", "keep": "可选 true=保留此层免清理" }}
- buffer：设施缓冲区（地铁500m/奥体1km）。params: {{ "center": "preset_id|geojson", "radius_m": 500, "as": "图层名(现实内容)", "keep": "可选 true=保留此层免清理" }}
- overlay：叠置（商业用地∩更新单元 等）。params: {{ "layer_a": "preset_id", "layer_b": "preset_id", "how": "intersection|union|difference|symmetric_difference", "as": "图层名(现实内容)", "keep": "可选 true=保留此层免清理" }}
- nearest：最近邻（离地铁最近的负面点）。params: {{ "layer": "点层", "target": "preset_id|geojson", "k": 1 }}
- hotspot：Gi* 热点识别（负面聚集/情绪热点，逐点 hot/cold/ns，自动落图层）。params: {{ "value_col": "score", "invert": true(负面为热), "layer": "(默认L2)", "range": "(可选)", "as": "(图层名)", "keep": "(可选true)" }}
- density：核密度(KDE)栅格——用户说"核密度/密度分析/聚集强度/热力分布"时**首选**（产连续密度面，2D 离散分段色带，自动落图层；区别于 hotspot 逐点 Gi*）。params: {{ "bandwidth_m": 800(平滑带宽·越大越平滑), "cell_size_m": 300(格长), "value_col": "(可选加权如score，不传=纯点密度)", "layer": "(默认L2)", "range": "(可选)", "as": "(图层名·现实内容)", "keep": "(可选true)" }}
- run_python：自由执行 Python（geo 工具覆盖不到的灵活分析/出图兜底；geo 工具够用时**优先 geo**）。params: {{ "code": "Python 源码", "inputs": ["可选 {{layer:$1/图层名, as:变量名}}（取已加载图层为 GeoJSON dict 注入子进程）"], "timeout": 30 }}
  **使用约束**：① 优先用 geo 工具（zonal_stats/rank/overlay/density/...），run_python 是兜底——常规柱/折/饼图（排序/对比/时序/占比）用 zonal_stats/rank 取数 + 结论阶段 `{{chart:bar|...}}` 即可（见下规则 9「出图决策」），勿用 run_python；② 出图用 matplotlib（Agg 已设），`plt.savefig('fig.png')` 即可（图片自动捕获）；③ 取图层用 inputs 指定变量名，代码里直接用该变量（GeoJSON FeatureCollection dict）——**inputs 的 as 必须与代码内变量名字面一致**：`inputs:[{{layer:'$1', as:'fc'}}]` 配代码 `import pandas as pd; df = pd.DataFrame([f['properties'] for f in fc['features']])`（as='fc' ↔ 代码用 fc，不一致会 NameError）；④ **字段名必须以 query_layers/buildContext 观察到的为准**——buildContext 里 `field=dtype:role:sample` 列出的就是真实字段名，**勿臆造**（臆造会 KeyError）；**先 query_layers 看字段，再写 run_python 代码**；⑤ 空间连接用 geopandas：`import geopandas as gpd; gdf = gpd.GeoDataFrame.from_features(fc, crs='EPSG:4326')`。可 import：pandas/numpy/geopandas/shapely/scipy/matplotlib/esda/libpysal/h3 + 标准库（math/statistics/json/datetime/re/pathlib）；os/sys/subprocess/socket 等被禁；⑥ 结论里引用图片用 `{{fig:fig1}}`（figId 从观察里读，禁编造；观察输出"已生成图片：fig.png（用 {{fig:figN}} 引用）"）；⑦ 描述图片用「**图片**」「**柱图**」「**折线图**」，**禁用**「图层/分布/网格/面/点」字样（防对账误抽）；⑧ run_python 失败时观察会指明"[sandbox] 数据没注入"还是"代码错"——按提示修；**连续同类失败勿盲重试超 2 次**，换 geo 工具（zonal_stats/rank + {{chart}}）。
- answer：已掌握足够信息，退出 loop 出结论。params: {{}}

【Agent 规则】（严守）
1. **先 query 后操作**：拿到问题先用 query_layers / query_zone_stats / query_attribution 摸清当前有什么数据、数据说什么，再决定动作。**勿盲目 ensure_zone**（已有聚合层就复用）。
2. **数据驱动**：thought 里引用 query 拿到的真实数值/区域，勿臆造。
3. **每轮只做一个动作**（一个 tool、answer 或 ask_user）。
4. **信息足够即 answer，简单问题提速**：通常 3-6 轮；**简单问题（单图层能答的 B 类 / 轻 C 类）≤3 轮**，跳过 DIAGNOSE 深挖，直接 query → 产图层 → answer；纯定义类问题（如"什么是情绪地图"）1-2 轮即可 answer，不必 query。
5. **thought 面向用户、口语化**（"我先看看有哪些数据"），不提 JSON/tool 字眼。
6. **多目标完整性（铁律）**：问句里的**全部**目标须落地，**不可只做一部分就 answer**。如「西陵+伍家岗的居住和商业用地」= 要覆盖西陵/伍家岗两区 × 居住/商业两类（或其完整组合），产 1/4 就 answer 是失败。多目标优先**多值筛选**（`MC/in/西陵区,伍家岗区` 一调用拿全两区）省步骤；method 含多步须**全做完**再 answer；answer 前自查"问句每个目标是否都已产出对应图层/结论"，未完成则继续做、勿 answer。
7. **图层生命周期·显式意图优先**：链式中间产物默认自动清理（EMC 组只留最终结果）。但**用户显式要保留的层不得清**——用户说"保留/留下/也显示 某图层"，或某层是你要给用户看的结论（非纯跳板），就在产出它的工具传 `keep: true`；被标记的层即使被后续引用也保留。判据："这层用户最终要在地图上看到吗？"是→keep:true；只是跳板→不传。
8. **主动问澄清（ask_user · 非一问一答）**：遇到**关键模糊点**（范围不明 / 时点不明 / domain 不明 / 用户意图多解）且硬猜风险高时，优先 `ask_user` 问一句（带 2-4 个 options），而非硬猜或直接 GAP。判据："这个模糊不澄清，后面整条分析会跑偏吗？"——会，就问；不会（通用概念问、或能合理推断），就别问，直接做。问时 question 要具体、口语化（"你想看哪个区的？" 优于 "请明确范围"）。**整个会话最多主动问 1-2 次澄清，连续问到第 3 次时 harness 会强制禁止 ask_user**——届时必须基于合理推断直接做，不得借连环追问拖延执行。每问一轮即等用户答，用户答后承接续作。
9. **出图决策（柱/折/饼 → 轻路径；散点/空间 → run_python）**：排序/对比/时序/占比类柱图、折线图、饼图——**先用 zonal_stats/rank 取数，再在结论阶段写 `{{chart:bar|...}}` 占位符**（前端渲染），勿用 run_python。范例：`zonal_stats(boundary=admin_district)` 拿到各区极性 → 结论里 `{{chart:bar|title=各区情绪极性|x=西陵区,伍家岗区,点军区|y=-0.45,0.32,-0.12}}`。只有 `{{chart}}` 做不到的（散点/空间叠加/双轴/热力矩阵/自定义可视化）才用 run_python。

【已完成的探索】（历轮 thought + action + 工具观察；首轮为空）：
{tool_history}

当前数据（grounding，主窗口推送的图层摘要）：
{context}
"""


def build_agent_prompt(context: str = '', tool_history: str = '', round_n: int = 1,
                       context_tokens: list = None, domain_lens: list = None) -> str:
    """agent_step 阶段：ReAct 每轮，输出 {thought, action} JSON。"""
    ctx = context or '（未提供数据上下文）'
    hist = tool_history or '（首轮，尚无探索）'
    prompt = _today_line() + MANIFESTO +AGENT_TEMPLATE.format(round=round_n, tool_history=hist, context=ctx)
    # GIS 操作目录附录（format 后拼接，花括号安全）—— 教模型选对 geo 工具 + 入参/产出/出口贡献
    prompt += '\n\n═══════════ 附录 · GIS 操作目录（何时用/入参/产出/出口贡献）═══════════\n' + geo_tool_catalog_text()
    prompt += '\n\n═══════════ 附录 · 代码执行目录（run_python · geo 兜底）═══════════\n' + code_exec_catalog_text()
    prompt += industry_kb_lens_appendix(domain_lens)   # 命中领域完整权威语境（diagnose domain_lens 注入）
    return _inject_tokens(prompt, context_tokens)


# ── answer 阶段：基于全部探索出最终结论 ─────────────────────────────────────
FINAL_TEMPLATE = """

═══════════ 本次任务 · 最终结论 ═══════════
你已完成探索（下方"探索历史"含你历轮的 thought/action/工具观察）。现在基于掌握的全部信息，给用户最终结论。

**诚实铁律（最高优先级 · 禁止"只说不做"）**：结论中任何"已加载/已生成/已裁出图层X"的陈述，必须对应【已完成的探索】中**真实成功**的工具调用（每轮观察末尾的"地图:N层[...] "可验证）。若工具失败、未执行、或结果为空，必须如实说明（"尝试 X 未成功，原因是 Y"或"当前数据不足以完成 Z"），**严禁谎报成功**。用户能看到地图实际状态，谎报一次即丧失信任。

**格式铁律（防漂移 · 严禁输出工具 JSON）**：本阶段输出**可读 markdown 结论**，严禁输出工具调用 JSON（即含 thought/action 字段的那种，那是 agent 探索阶段的格式，不是结论）。若误输，会被系统拦截、不计为可读结论，用户将看到"未能生成可读结论"提示。

**出口要素（软引导·图层优先）**：① **已产出的地图图层**（`{{show:图层名}}` 让用户点开看，**图层是主出口**）② **解题逻辑一句话**（我怎么解的：先 query → 发现 X → 产图层 Y，让用户秒懂操作链）③ 简短结论（**图层的注脚**，1-3 句话说清这层表现什么 + 含 1 条可落地建议；别写长报告/学术八股）。**B/C 类都必产图层**（纯概念问答 intent=A 除外）；零图层会被系统降级，严禁只给文字。**做成一部分也体面（仅限数据真缺时适用）**：若部分数据缺，先给已做成的结论段，再诚实标注局限（缺什么 / 未生成什么），末尾引导用户补数据后继续——这比"没答案"有用得多；但问句里**明确列出的多个目标（如"A 区和 B 区的规划与更新"）必须全做完**——目标未全做完时不适用此条，须继续做完再 answer；严禁只给思路不执行、严禁"点击 X 即可聚焦"却没真生成 X。
**可操作结论**：结论里给用户的操作建议用模板渲染成按钮——`{{focus:区域名}}`（飞到）、`{{inspect:区域名}}`（深读归因）、`{{show:图层名}}`（显示已生成的图层）。用户一点即执行，取代"请点击/请查看"等空话。

**结论配图（数据≥3 项的比较/排序/趋势/占比时出图，取代干巴巴数字罗列；无关勿强出）**：在结论里**独占一行**写 `{{chart:TYPE|title=标题|x=标签逗号分隔|y=数值逗号分隔}}`——前端渲染成柱/折/饼图。
- 排序/对比（各区情绪、各类用地强度、Top N）→ `bar`
- 时序（T1→T2→T3 演进、前后对比）→ `line`
- 占比/构成（4 域归因、用地结构）→ `pie` 或 `doughnut`
规则：TYPE 只能 bar/line/pie/doughnut；x 与 y 项数相等（≥3）；y 必须是【探索】里真实观察到的数，勿臆造；一条结论最多 1 张图（聚焦）。
例：`{{chart:bar|title=各区情绪极性指数|x=西陵区,伍家岗区,点军区|y=-0.45,0.32,-0.12}}` ；时序：`{{chart:line|title=中心城区T1→T3均极性|x=T1,T2,T3|y=-0.31,-0.08,0.22}}` 。

严格遵守 MANIFESTO 第十节回答公约：**图层优先**（必产图层，`{{show:图层名}}` 主出口）、**解题逻辑一句话**（我怎么解的）、**简单清晰直接**（通俗 + 专业词紧跟解释，不学术八股）、**互动可操作**（`{{focus}}`/`{{inspect}}` 按钮 + [ref:区域名]）、**简短**、数据驱动（引用数值/区域）、4×5 归因仅复杂情绪分析、结论有指向。
结论要对齐演示逻辑链：**产出图层让地图有张力可点 → 按钮引导互动 → 简短结论**（而非写长篇文字报告）。

【探索历史】（你历轮的 thought + action + 工具观察）：
{tool_history}

当前数据：
{context}
"""


def build_final_prompt(context: str = '', tool_history: str = '', context_tokens: list = None,
                       domain_lens: list = None) -> str:
    """answer 阶段：基于全部探索出最终结论（流式 markdown + [ref:]）。"""
    ctx = context or '（未提供数据上下文）'
    hist = tool_history or '（无探索历史）'
    prompt = _today_line() + MANIFESTO +FINAL_TEMPLATE.format(tool_history=hist, context=ctx)
    prompt += industry_kb_lens_appendix(domain_lens)   # 命中领域完整权威语境（用权威话语 + 归因落具体项目）
    return _inject_tokens(prompt, context_tokens)


# ── diagnose 阶段：问题理解卡（agent_step 之前的专业认知前置步）─────────────────
DIAGNOSE_TEMPLATE = """

═══════════ 本次任务 · 问题诊断（DIAGNOSE · 专业认知前置步）═══════════
阅读用户问题，**像城市规划师那样先沿专业轴拆解**——不是语义解析后直接走管线，而是判定：
这是个什么行业视角、什么空间尺度、什么决策类型的问题，该出什么形态的结论，需要什么数据、
当前是否齐全、该用什么 GIS 方法。诊断卡会指导后续 agent loop 的工具选型与最终结论的颗粒度。

严格遵守 MANIFESTO 第十一节「尺度-方法-范式」：结论颗粒度必须匹配问题尺度（宏观禁落单点 /
微观禁泛泛）。数据盘点要诚实——缺关键数据须在 strategy 标 request_upload 或 fallback_annotated，
勿假装全知。

输出**严格 JSON 对象**（仅 JSON，禁 markdown 代码块 / 前后解释），结构如下（8 字段必填，intent 置顶）：
{{
  "intent": "general" | "gis_operation" | "emotion_analysis",
  "domain_lens": ["urban_planning" | "urban_renewal" | "urban_operation" | "urban_governance" | "general", ...],
  "scale": "macro" | "meso" | "micro",
  "decision_type": "评价" | "选址" | "排查" | "对比" | "监测" | "定义" | "操作" | "通用问答",
  "outlet": "报告结论" | "指标排序" | "地图定位" | "建议清单" | "预警" | "执行操作" | "生成图层",
  "data_plan": {{
    "needed": ["回答此问所需的数据，如『更新单元矢量』『L2 极性』"],
    "available": ["当前已有的，如『L2 T1 极性』『行政区边界』"],
    "gap": ["缺失的，如『更新紧迫度评估』"],
    "strategy": "ready" | "fallback_annotated" | "request_upload"
  }},
  "template": "技能id（density/rank/buffer/clip/overlay/zonal/nearest/hotspot/area_stats/merge/extract_feature/concept/multi/unknown 之一，见下方【技能目录】）",
  "params": {{"必填槽名": "值（按所选技能 required_slots 填，可空槽系统补默认）"}}
}}
**输出铁律（最高优先级·违者计 MISS）**：本阶段是**问题诊断**，不是答题——无论问题是什么类型（概念/定义/通用问答/纯 GIS 操作/情绪分析），你**必须且仅输出一个 JSON 诊断卡，绝不能用自然语言/散文直接回答用户的问题**。即使问"什么是核密度""情绪地图是什么"这类概念问，也**只输出一张 `template="concept"` 的卡**（概念解释交给后续阶段作答），**绝不可直接写出概念解释的正文**。卡里 `template` 字段必填（概念/定义/通用问答→填 concept；操作问→填对应技能 id），不可省略、不可留空字符串。无 `{{...}}` 形式 JSON 的纯文字输出 = 失败。
**intent 判定要点（最高优先级）**：
- general=通用问答/常识/寒暄/纯概念（今天星期几、什么是等时圈）→ domain_lens=["general"]，**template 必填 "concept"**，不进情绪分析。**包含"就已有图层/上一轮结果的概念追问"**——用户问"差别/区别/为什么/解释/含义/是什么/对比"且针对**已生成的图层/结果**（不要求新操作），即使含"核密度/用地/极性"等关键词，也判 general（**template=concept**，概念解释交后续阶段作答，本阶段只出卡）。例：「生成的 4 个核密度图层有什么差别」「为什么 X 区比 Y 区差」「这些图层是什么意思」→ general（concept）。
- gis_operation=纯 GIS/数据操作（裁剪/抽取某区/缓冲/叠置/合并/字段筛选/上传数据处理/核密度density）→ outlet="生成图层"，**template 选 clip/overlay/buffer/density/rank/zonal 等对应技能 id**（见【技能目录】），出口是新图层而非归因报告。**注意：「核密度/密度分析/聚集强度/热力分布」属此类（template="density"）仅当用户「新请求做」分析；若用户是「问已有」密度图层的问题（见上一条），判 general（template=concept）勿短路进操作。**
- emotion_analysis=情绪评价/排序/归因/预警（7 场景）→ 走原 domain_lens/scale/decision_type 体系。

**多轮续作（最高优先级，覆盖上文 intent 判定）**：若上文含【上一轮上下文】块，且用户本轮在追问/续做（问句含"继续/接着/补充/我上传了X/那个/把刚才"等，或承接上一轮未完成任务），则：
- intent **取上一轮 intent**（多为 gis_operation / emotion_analysis，**勿判 general**）；
- method **承接上一轮 method 从断点续做**——上轮【缺口】数据若本轮已就位（如用户上传了），继续执行原 method 剩余步骤，产出最终结果；
- data_plan 按当前数据**重判**（已补齐的缺口不再算缺失；strategy 多从 request_upload 升为 ready）；
- 即便问句极短（如"继续"），只要上文有【上一轮上下文】，按续作处理，不要当通用问答短路。


【尺度判定要点】（查下方矩阵）：
- 提到"中心城区/片区/整体/哪个区/哪类"→ 多为宏观；提到"街道/社区/更新单元/几个片区对比"→ 中观；
  提到"这条街/这个小区/这个公园/哪个点位"→ 微观。
- "定义"类问题（如"什么是情绪地图"）scale 可填 macro 但 decision_type=定义，method 可空。
【strategy 判定要点】（查下方 strategy 语义）：硬缺口（无替代）→ request_upload；
有合理替代（社区代街道、用极性近似紧迫度）→ fallback_annotated；齐全 → ready。

当前数据（grounding，主窗口推送的图层摘要；据此判断 available/gap）：
{context}
"""


def build_diagnose_prompt(context: str = '', context_tokens: list = None) -> str:
    """diagnose 阶段：输出 6 字段问题理解卡（流式 reasoning + content JSON）。

    范式知识（矩阵/出口/工具目录/卡字段）在 DIAGNOSE_TEMPLATE.format() 之后拼接——
    避免这些含花括号的文本被 str.format 误解析（见 manifesto/py 花括号警示）。
    """
    ctx = context or '（未提供数据上下文）'
    prompt = _today_line() + MANIFESTO +DIAGNOSE_TEMPLATE.format(context=ctx)
    # 范式知识附录（format 后拼接，花括号安全）
    prompt += '\n═══════════ 附录 · 尺度-方法-范式矩阵 ═══════════\n' + scale_paradigm_text()
    prompt += '\n\n═══════════ 附录 · 4 领域出口范式启发库 ═══════════\n' + domain_outlets_text()
    prompt += '\n\n═══════════ 附录 · 四领域官方术语与项目类型速查（行业知识库 brief）═══════════\n' \
              + industry_kb_brief_text()
    prompt += '\n\n═══════════ 附录 · B 赛道操作范式树（gis_operation · Load→Transform→Analyze）═══════════\n' \
              + '【list 顺序 = 关键词匹配优先级，B 操作歧义裁断的单一真相源】\n' \
              + b_track_paradigm_text()
    prompt += '\n\n═══════════ 附录 · GIS 操作目录（template 字段选型参照）═══════════\n' \
              + geo_tool_catalog_text()
    prompt += '\n\n═══════════ 附录 · 技能目录（template 字段据此选型 · 拟人化 · P1 编排层）═══════════\n' \
              + '【选择要点·铁律】intent=general→template=concept；intent=gis_operation→density/rank/buffer/clip/overlay/nearest/hotspot/area_stats/merge/extract_feature 之一；intent=emotion_analysis→zonal/rank。**单一空间关系就是 single，严禁选 multi/unknown**——周边/附近/半径→buffer；某区/某范围/XX区内的目标→clip；两图层关系（A∩B、A里的B）→overlay；排序/最差最好→rank；密度/聚集→density。**只有一句话含≥2个不同动作（如"裁出来并排序"）才选 multi**；真无任何现成技能才选 unknown。勿把单一关系当复合、勿因不确定就退 unknown。\n' \
              + template_registry_text()
    prompt += '\n\n═══════════ 附录 · 选型决策树（单一真相源 · track+scale+关键词→template）═══════════\n' \
              + select_template_text()
    prompt += '\n\n═══════════ 附录 · 诊断卡字段说明 ═══════════'
    for k, v in DIAGNOSE_CARD_FIELDS.items():
        prompt += f'\n- {k}：{v}'
    prompt += '\n\n═══════════ 附录 · data_plan.strategy 语义 ═══════════'
    for k, v in DATA_STRATEGY.items():
        prompt += f'\n- {k}：{v}'
    # 输出示例（few-shot·纯字符串拼接于 .format 之后，花括号安全）：教 Flash「任何问必先吐 JSON 卡、概念问 template=concept」，
    # 治概念问散文直答不吐卡的 2 MISS（eval 69% 主因）。概念解释交后续阶段，本阶段只出卡。
    prompt += _DIAGNOSE_FEW_SHOT
    return _inject_tokens(prompt, context_tokens)


# 输出示例（注入 diagnose prompt 末尾·最强 recency）：3 条 Q→完整 JSON 卡，覆盖概念问(→concept)、
# 单工具操作(→density)、对已有结果的概念追问(→concept，防被 geo 词误导短路进操作)。
_DIAGNOSE_FEW_SHOT = """

═══════════ 附录 · 输出示例（仿此格式，**只输出 JSON 卡，不要任何前后解释/正文**）═══════════
【例1·概念问】用户问：什么是核密度分析
你的输出（仅此 JSON，不写概念解释正文）：
{"intent":"general","domain_lens":["general"],"scale":"macro","decision_type":"定义","outlet":"报告结论","data_plan":{"needed":[],"available":[],"gap":[],"strategy":"ready"},"template":"concept","params":{}}

【例2·单工具操作】用户问：做核密度分析
你的输出：
{"intent":"gis_operation","domain_lens":["general"],"scale":"macro","decision_type":"操作","outlet":"生成图层","data_plan":{"needed":["L2 极性点"],"available":["L2 T1 极性点"],"gap":[],"strategy":"ready"},"template":"density","params":{"mode":"2d"}}

【例3·对已有结果的概念追问】用户问：刚生成的核密度图层是什么意思 / 这几个密度图有什么差别
你的输出（含"核密度/密度图"也判 concept，勿短路进操作）：
{"intent":"general","domain_lens":["general"],"scale":"macro","decision_type":"定义","outlet":"报告结论","data_plan":{"needed":[],"available":["已生成的密度图层"],"gap":[],"strategy":"ready"},"template":"concept","params":{}}

【例4·缓冲（single，勿选 multi）】用户问：奥体中心周边 1 公里情绪怎么样 / 地铁站周边情绪
你的输出（"周边/附近/半径"→buffer，单一空间关系不是复合）：
{"intent":"gis_operation","domain_lens":["urban_operation"],"scale":"meso","decision_type":"排查","outlet":"生成图层","data_plan":{"needed":["L2 极性点","设施位置"],"available":["L2 T1 极性点"],"gap":[],"strategy":"ready"},"template":"buffer","params":{"center":"奥体中心","radius_m":1000}}

【例5·范围裁取（single，勿选 multi/unknown）】用户问：伍家岗区内的居住用地 / 某区的商业用地
你的输出（"某区内的/范围内的"目标→clip，能答就别选 unknown）：
{"intent":"gis_operation","domain_lens":["urban_renewal"],"scale":"meso","decision_type":"操作","outlet":"生成图层","data_plan":{"needed":["行政区边界","用地层"],"available":["admin_district","land_residential"],"gap":[],"strategy":"ready"},"template":"clip","params":{"range":"admin_district","pre_filter":"MC/eq/伍家岗区"}}

【例6·叠置（single，勿选 multi）】用户问：公园用地与商业用地的交集 / 居住用地里情绪差的地方
你的输出（"两图层关系/A里的B"→overlay，单一关系不是复合）：
{"intent":"gis_operation","domain_lens":["urban_planning"],"scale":"meso","decision_type":"操作","outlet":"生成图层","data_plan":{"needed":["用地图层"],"available":["land_park","land_commercial"],"gap":[],"strategy":"ready"},"template":"overlay","params":{"layer_a":"land_park","layer_b":"land_commercial","how":"intersection"}}

记住：**任何问题都先吐一张 JSON 诊断卡**（template 必填），再由后续阶段作答——绝不直接用文字回答用户。**单一空间关系（周边/范围内/两图关系/排序/密度）一律选对应 single 技能，只有一句话含≥2个不同动作（如"裁出来并排序"）才选 multi。**
"""


# ── revise 阶段：审查未过，基于 draft + hints 重写 ───────────────────────────
REVISE_TEMPLATE = """

═══════════ 本次任务 · 修订重写 ═══════════
你之前的草稿未通过审查员审查（审查意见见下）。请基于审查意见修订重写，逐条修正不达标项，输出修订后的完整结论。

严格遵守 MANIFESTO 第十节回答公约：**图层为主出口**（`{{show:图层名}}`）+ 解题逻辑一句话 + 简短结论（1-3 句，含 1 条可落地建议）；数据驱动（引用数值/区域 + [ref:区域名]）、专业用语、**禁学术八股**（问题定性→数据证据→结论建议 那套，与 manifesto 公约3 一致）、**禁长报告**。

【审查意见】（六条中不达标/警告项 + 修正方向，须逐条对照修正）：
{review_hints}

【原草稿】（在此基础上改，不要推翻重写、保留正确部分）：
{draft}

【探索历史】（你历轮的 thought/action/工具观察）：
{tool_history}

当前数据：
{context}

输出修订后的完整结论（markdown + [ref:区域名]），不要解释"我改了什么"、不要前后缀解释。
"""


def build_revise_prompt(draft: str = '', review_hints: str = '', context: str = '',
                        tool_history: str = '', context_tokens: list = None,
                        domain_lens: list = None) -> str:
    """revise 阶段：基于 draft + review_hints 重写（流式 markdown）。"""
    ctx = context or '（未提供数据上下文）'
    hist = tool_history or '（无探索历史）'
    prompt = _today_line() + MANIFESTO +REVISE_TEMPLATE.format(
        review_hints=review_hints or '（无具体意见，请按六条公约全面检查并改写）',
        draft=draft or '（空）',
        tool_history=hist,
        context=ctx,
    )
    prompt += industry_kb_lens_appendix(domain_lens)   # 命中领域完整权威语境（重写时用权威话语）
    return _inject_tokens(prompt, context_tokens)


# ── 字段语义推断（P2 /aiqa/profile_fields 用）────────────────────────────────
# 为规则字典未命中的字段调 LLM 选 role（schema matching 兜底）。返 str（system prompt）。
FIELD_INFER_TEMPLATE = """

═══════════ 本次任务 · 字段语义推断（FIELD ROLE INFERENCE）═══════════
你是数据字典（data dictionary，=字段含义清单）专家。下面给你若干**待识别字段**——每个字段有 dtype（数据类型）
+ 样本值 + 统计。请为每个字段选**最贴近的语义角色（role）**。role 是字段的语义类型（如"极性/名称/用地类型"，
不是物理列名），从下方【role 候选表】选一个；若实在无法判断或都不贴切，role 填 null。

【role 候选表】（name + 一句说明；选最贴近的一个）：
{role_catalog}

【待推断字段】（仅这些字段需要你判，规则字典已命中的不在此列）：
{field_profiles}

输出**严格 JSON 对象**（仅 JSON，禁 markdown 代码块 / 前后解释），结构如下：
{{
  "字段名1": {{"role": "role_a", "confidence": 0.9, "reason": "一句依据（如：样本含 Positive/Negative→极性）"}},
  "字段名2": {{"role": null, "confidence": 0, "reason": "无法判断的原因"}}
}}
要求：
- role 必须是上方候选表里的 name 之一（或 null）；非法 role 会被后端置 null。
- confidence 反映把握：样本清晰→0.9，较有把握→0.7，模糊→0.5，纯猜→0.3。
- land_use_class 候选的值域见国标用地分类（landuse_codes_2023.py：24 一级/111 二级/40 三级）；
  样本若像用地类型代码或名称（如"商业用地""居住用地"）→选 land_use_class。
- 判据举例：样本像情绪标签（Positive/好评/差评）→polarity；像 0~1 或 -2~2 的数值+有正负→score；
  像地址/地点→location；像行政区/街道/单元名→boundary_name 或 name。
"""


def build_field_infer_prompt(fields: dict, layer_kind: str = '', context: str = '') -> str:
    """P2 字段语义推断 prompt：为规则字典 miss 的字段选 role。返 str（system prompt）。

    fields = {field: {dtype, samples, stats}}（规则字典未命中、交由 LLM 兜底的字段）。
    范式照 build_diagnose_prompt：MANIFESTO + TEMPLATE.format() + 附录拼接（花括号安全）。
    """
    from core.field_dictionary import FIELD_ROLE_DICT
    # 候选表只列用户上传可命中的 role（自产/渲染契约规则已命中，不交 LLM 推断）
    user_roles = [
        'polarity', 'score', 'confidence', 'text', 'location', 'emotion_type', 'emotion_intensity',
        'name', 'category', 'domain', 'element', 'topic', 'timestamp',
        'geometry_lon', 'geometry_lat', 'boundary_name', 'boundary_id', 'land_use_class',
    ]
    catalog_lines = [f"- {r}：{(FIELD_ROLE_DICT.get(r) or {}).get('description', '')}" for r in user_roles]
    role_catalog = '\n'.join(catalog_lines)
    # 字段画像
    profile_lines = []
    for fld, p in (fields or {}).items():
        p = p or {}
        dtype = p.get('dtype', '?')
        samples = p.get('samples', []) or []
        stats = p.get('stats', {}) or {}
        samp_str = '|'.join(str(s) for s in samples[:3]) or '（无样本）'
        stats_str = ', '.join(f'{k}={v}' for k, v in stats.items()) if stats else ''
        line = f"- {fld}（dtype={dtype}）样本: {samp_str}"
        if stats_str:
            line += f" 统计: {stats_str}"
        profile_lines.append(line)
    field_profiles = '\n'.join(profile_lines) or '（无）'
    prompt = _today_line() + MANIFESTO +FIELD_INFER_TEMPLATE.format(
        role_catalog=role_catalog, field_profiles=field_profiles,
    )
    if layer_kind:
        prompt += f"\n（图层类型：{layer_kind}，可作为推断辅助）"
    if context:
        prompt += f"\n（附加上下文：{context}）"
    return prompt
