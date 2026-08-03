"""思考层 · Agent Loop prompt builder（ReAct）。

阶段（phase）：
- diagnose   ：问题理解卡（6 字段 JSON，Flash·eval-anchor，永不动内容）。
- agent_step ：ReAct 每轮，输出 {thought, action} JSON（流式 reasoning + content JSON）。
- answer     ：agent 决定 answer 后，基于全部探索历史出最终结论（流式 markdown）。
- optimize   ：Flash 把用户 NL 优化成具体/实操 prompt（5.215·不增维度·梳理已有要素）。
（CB-09 D022：删旧 review/revise 阶段 → 前端 harness.applyQualityDefense 代码防线取代 LLM 审查+重写）

改 prompt 只改本文件。
"""
import datetime as _dt

from ai_qa.manifesto import MANIFESTO
from ai_qa.paradigm import (
    scale_paradigm_text, domain_outlets_text, geo_tool_catalog_text, code_exec_catalog_text,
    template_registry_text, b_track_paradigm_text, select_template_text, template_id_list_text,
    DIAGNOSE_CARD_FIELDS, DATA_STRATEGY, TEMPLATE_REGISTRY,
)
from ai_qa.industry_kb import industry_kb_brief_text, industry_kb_lens_appendix, industry_kb_final_brief
from core.tracker import track, register_track_id


def _today_line() -> str:
    """当前现实日期前缀（喂 LLM 让其知「今天」=通用问答的日期语境，与 T1/T2/T3 数据时点无关）。"""
    d = _dt.date.today()
    wk = '周一 周二 周三 周四 周五 周六 周日'.split()[d.weekday()]
    return f'当前现实日期：{d.year}年{d.month}月{d.day}日（{wk}）。\n'


# CB-10 P0-4：人民城市理念改运行时条件注入（省静态 ~130B·防 D019 回弹 test_final_prompt_stays_lean）
_PEOPLE_CITY_LINE = ('**"人民城市"理念**：问题涉及项目背景/定位/情绪地图定义/意义价值时，自然融入——'
                     '"人民城市人民建，人民城市为人民"，情绪地图价值=听见市民心声、把人民情绪与诉求纳入'
                     '城市体检与规划决策（补传统问卷采样局限）；融入贴题自然，勿生硬口号。\n')


def _is_concept_question(context):
    """概念/背景问（人民城市理念注入条件）：项目背景/定位/定义/意义价值。"""
    return any(w in (context or '') for w in ('什么是', '意义', '价值', '理念', '城市体检', '项目背景', '定义', '情绪地图'))


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
- inspect_zone：深读某聚合域明细（极性/4×5/问题）。params: {{ "name": "区域名" }}
- deep_read_attribution：L4 深度归因——某簇 rule 底（issue_label/attribution/suggestion）+ 簇评论 → 政策→情绪→项目闭环（deep_attribution + 政策锚 policy_link + 落点项目 project_link + 官方盲区 blind_spot）。**当用户要"这里什么问题/归因/怎么治/政策依据/落什么项目"时用此**（在 inspect_zone 极性/4×5 基础上深化到可落地项目）。params: {{ "name": "区域名" }}
【GIS 工具】（按 intent/问题尺度自动组合，见下方「GIS 操作目录」附录；**结果自动落地图为新图层**；B 纯操作类必走此类产出图层，允许坐标与裸结果）：
**工具选择决策**：①"某范围内"=clip（点）/extract_feature（面）；②"A 内的 B"（如西陵区内的商业用地）=先 extract_feature(A) 再 overlay(A, B, intersection)；③面∩面/面∪面=overlay（**勿用 clip——clip 只切点，面层会报错**）；④合并多面=merge；⑤周边半径=buffer。
**用地数据模型（重要）**：用地预设（如 land_commercial/land_residential/land_park）是**按地类 dissolve 的全市单面/多面**，**没有"类×区"联合资产**——即无法直接抽取"西陵区的商业用地"。要"某区内的某类用地"，必须**几何叠置**：先 extract_feature(admin_district, 区名) 得该区面 → overlay(layer_a=该区面, layer_b=land_xxx, how="intersection") 得交集。同理"某区内居住+商业两类"= 该区面分别与 land_residential、land_commercial 叠置（或 union 后再叠），不可只传一个 preset 期望自动分区。
**工具链（chain，推荐显式变量）**：多步操作用 `$1`/`$2` 引用前序工具产物（第 1/2 个产图层的工具结果，最稳，不依赖图层名匹配）。例：extract_feature(admin_district, MC/eq/西陵区) 得 `$1` → overlay(layer_a="$1", layer_b="land_commercial", how="intersection") 得西陵区内商业用地。也支持传"已生成的图层名"或 preset_id。
**结果图层命名（重要）**：凡产图层的工具（extract_feature/clip/filter_attr/merge/buffer/overlay）可传 `as` 自定义图层名。**`as` 必须用结果的现实内容命名（如「西陵区内商业用地」「滨江公园·500m」「西陵区·伍家岗区」），严禁用实现术语（叠置/intersection/clip/抽取）**——用户看图，名要说清"这层是什么"。不传 `as` 时系统按内容自动命名兜底。
**图层生命周期（重要·勿死板）**：EMC 组**默认只留最终结果**——链式中间产物（被后续工具引用的，如 extract→overlay 的 extract）自动清理；并列最终结果（居住+商业）保留。**但用户的显式意图优先于该默认**：凡产图层工具可传 `keep: true` 标记"此层要保留"——被标记的层**即使被后续引用也不会被清理**。何时用 keep：① 用户明确说"保留/留下/也显示 某图层"；② 该层本身就是要展示给用户的结论图层（非纯中间步骤），你不确定它会不会被后续引用。**判据：问自己"这层用户最终要在地图上看到吗？"——是，就 keep:true；只是通往结果的跳板，就不传（默认清）。**
**GIS 工具**（13 个 single 技能·params/入参/产出/失败模式/正负例详见下方「GIS 操作目录」附录·**由 [`tool_contracts.py`](ai_qa/tool_contracts.py) 单一源派生·D026 全派生**）：filter_attr / extract_feature / clip / merge / area_stats / buffer / overlay / nearest / hotspot / density / rank / zonal_stats / compare_regions。选型见上方「工具选择决策」+附录各工具 `failure_modes`（消歧）。
- run_python：自由执行 Python（geo 工具覆盖不到的灵活分析/出图兜底；geo 工具够用时**优先 geo**）。params: {{ "code": "Python 源码", "inputs": ["可选 {{layer:$1/图层名, as:变量名}}（取已加载图层为 GeoJSON dict 注入子进程）"], "timeout": 30 }}
  **使用约束**：① 优先用 geo 工具（zonal_stats/rank/overlay/density/...），run_python 是兜底——常规柱/折/饼图（排序/对比/时序/占比）用 zonal_stats/rank 取数 + 结论阶段 `{{chart:bar|...}}` 即可（见下规则 9「出图决策」），勿用 run_python；② 出图用 matplotlib（Agg 已设），`plt.savefig('fig.png')` 即可（图片自动捕获）；③ 取图层用 inputs 指定变量名，代码里直接用该变量（GeoJSON FeatureCollection dict）——**inputs 的 as 必须与代码内变量名字面一致**：`inputs:[{{layer:'$1', as:'fc'}}]` 配代码 `import pandas as pd; df = pd.DataFrame([f['properties'] for f in fc['features']])`（as='fc' ↔ 代码用 fc，不一致会 NameError）；④ **字段名必须以 query_layers/buildContext 观察到的为准**——buildContext 里 `field=dtype:role:sample` 列出的就是真实字段名，**勿臆造**（臆造会 KeyError）；**先 query_layers 看字段，再写 run_python 代码**；⑤ 空间连接用 geopandas：`import geopandas as gpd; gdf = gpd.GeoDataFrame.from_features(fc, crs='EPSG:4326')`。可 import：pandas/numpy/geopandas/shapely/scipy/matplotlib/esda/libpysal/h3 + 标准库（math/statistics/json/datetime/re/pathlib）；os/sys/subprocess/socket 等被禁；⑥ 结论里引用图片用 `{{fig:fig1}}`（figId 从观察里读，禁编造；观察输出"已生成图片：fig.png（用 {{fig:figN}} 引用）"）；⑦ 描述图片用「**图片**」「**柱图**」「**折线图**」，**禁用**「图层/分布/网格/面/点」字样（防对账误抽）；⑧ run_python 失败时观察会指明"[sandbox] 数据没注入"还是"代码错"——按提示修；**连续同类失败勿盲重试超 2 次**，换 geo 工具（zonal_stats/rank + {{chart}}）。
- answer：已掌握足够信息，退出 loop 出结论。params: {{}}

【Agent 规则】（严守）
1. **首轮 query 即可·勿过度验证**（CB-06 L3-a）：拿到问题在首轮执行前 query_layers 了解数据概况（系统已自动注入）。**工具执行产出的 observation 已含关键统计——直接据此结论，勿追加 query 验证**。已有聚合层就复用，勿盲目重复 ensure_zone。
2. **数据驱动**（CB-06 L3-b）：结论中引用工具 observation 中的真实数值（图层名/单元数/极性值等）或 query 结果。**工具 observation = 已验证的数据源，无需二次 query 确认**；勿臆造。
3. **每轮只做一个动作**（一个 tool、answer 或 ask_user）。
4. **最少轮次原则·信息足够即 answer**（CB-06 L3-c）：生成类请求（生成图/热力图/网格/方格/分析图）工具产出图层 → **立即 answer**（1-2 轮）；简单 GIS 操作 1-2 轮即答；复合操作 2-4 轮；最多 6 轮（绝对上限·超此可能超时）。**不要为"完整性"追加 query 查询**——工具 observation 已提供足够数据驱动结论。纯定义类问题（如"什么是情绪地图"）1-2 轮即可 answer。
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


@track("MOD_AIQA.F_002", track_args=False)
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

═══ 最终结论 ═══
基于【探索历史】+【当前数据】给最终结论。

**三句骨架**（必守）：① 动作（做了什么）② 产出（发现什么·**引用真实数值/地名**）③ 交互（`{{show:图层名}}` 按钮引导）。**图层是主出口**——分析类必产图层·零图层系统降级·严禁只给文字。

**诚实**：失败/未生成就说失败（"尝试 X 未成功"/"数据不足"）·**禁编造图层名/数字**（地图状态用户可见·谎报失信）。

**格式**：可读 markdown·禁工具 JSON·禁删除线。
**排版**（G2·突出关键·禁纯段落堆砌）：结论/关键数值/地名用 `**加粗**`·多个发现用 `-` 列表·局限/口径用 `> 引用块`·要点可用 `###` 小标题。

**内联模板**（独占一行·渲染成按钮/图）：`{{show:图层}}` 显示 · `{{focus:区域}}` 飞到 · `{{inspect:区域}}` 深读 · 数据≥3 项比较/排序/趋势出图 `{{chart:TYPE|title=|x=标签|y=数值}}`。

**追问胶囊**（末尾产 1-3 个·各占一行）：`{{capsule:标签|级别|技能|参数=值|...}}`。级别 `L1`=同工具换参（直达·换极性/排序）/`L2`=跨工具单步（轻判·叠置/缓冲）·禁 L3。技能 ∈ density/rank/buffer/clip/overlay/zonal/compare/extract_feature/area_stats/hotspot/nearest/filter_attr。参数=值 从本问结果派生。例：`{{capsule:切换消极热力图|L1|density|analysis=negative|polarity=N}}`。

**语言风格**（严格遵守）：
- **面向用户**：城市分析报告非技术日志。禁工具名（extract_feature/density）、参数名（boundary/polarity_index）、代码片段、英文术语、→ 符号（用逗号/句号断句）。
- **中文化**：字段名 emotion_intensity→情绪强度、polarity→极性、polarity_index→极性指数、domain_top→归因领域；工具名用中文（抽取/裁剪/聚合/排序/缓冲/叠置/筛选/合并/热力图/区域对比）。
- **专业且生动**：专业客观理性 + 生动自然形象（"这片区域情绪偏消极"而非"polarity_index=-0.45"）；简短 3-5 句·通俗+专业词紧跟解释（极性=情绪正负）·勿追加"建议进一步分析"。

**thinking 推理**：生动口语拟人，像跟同事边想边讲，避免"因为/所以/另外/但是"八股；正文仍守语言风格。

**纯问答排版**（无工具操作、纯文字作答时·如"什么是情绪地图/项目意义/某概念"）：用**条目式**组织（`###` 小标题 + `-` 要点列表），关键术语/结论用 `**加粗**` 强调，信息分层（是什么→为什么→怎么用）；此时不受"3-5 句简短"约束。

【探索历史】（历轮工具观察）：
{tool_history}

【当前数据】：
{context}
"""


@track("MOD_AIQA.F_003", track_args=False)
def build_final_prompt(context: str = '', tool_history: str = '', context_tokens: list = None,
                       domain_lens: list = None) -> str:
    """answer 阶段：基于全部探索出最终结论（流式 markdown + [ref:]）。"""
    ctx = context or '（未提供数据上下文）'
    hist = tool_history or '（无探索历史）'
    # CB-09 D019 极瘦：去 MANIFESTO 前置（省 11.2KB）+ industry_kb_lens_appendix（省 0-20KB）·17KB→~0.9KB
    # 诚实/结构由前端 harness.applyQualityDefense 代码守（5.232·空答/谎报/矛盾/截断）·prompt 不再内嵌自查清单
    prompt = _today_line() + FINAL_TEMPLATE.format(tool_history=hist, context=ctx)
    # CB-14（A4）：finalStep 按 domain_lens 条件注入命中领域【精简归因速查】——治"finalStep 无领域知识"痛点
    #   （D019 后 final 极瘦·FC 出 domain_lens 但 final 不消费→回答缺行业权威话语/归因落点）。
    #   与 agent_step 的 industry_kb_lens_appendix（全量）区分：此处只注精简框架（每域 ~1.6KB·非全量·防 D019 回弹）。
    #   条件性注入——空 context/无 domain_lens 不触发·test_final_prompt_stays_lean 静态门禁不受影响。
    #   体积守卫见 test_final_prompt_with_lens_stays_bounded（四域全注 <5KB·防 final_brief 加厚回弹）。
    if domain_lens:
        _brief = industry_kb_final_brief(domain_lens)
        if _brief:
            prompt = prompt + '\n\n' + _brief
    # CB-10 P0-4：人民城市理念仅概念问注入（省静态体积·防 D019 回弹）
    if _is_concept_question(ctx):
        prompt = _PEOPLE_CITY_LINE + prompt
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
  "template": "技能id（{template_ids} 之一，见下方【技能目录】）",
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
**可派生（易误判 GAP·重点）**：所需范围/数据若可从已加载层"派生"——如问句提到的区/街道是某已加载 boundary（行政区/片区/社区）的命名子要素（见 grounding 已加载层的「含:」清单，如「行政区·含:西陵区/伍家岗区/…」），则 clip/extract_feature 可裁出该子区 → **strategy=ready**（非 request_upload）。即"超集可派生子集"算齐全，勿因未单独加载该子区层就保守判 GAP。例：问"西陵区情绪归因"+已加载行政区（含西陵区）→ ready（zonal boundary=西陵区）；问"伍家岗区的点"+行政区已加载 → ready（clip range=伍家岗区）。

当前数据（grounding，主窗口推送的图层摘要；据此判断 available/gap）：
{context}
"""


@track("MOD_AIQA.F_005", track_args=False)
def build_diagnose_prompt(context: str = '', context_tokens: list = None) -> str:
    """diagnose 阶段：输出 6 字段问题理解卡（流式 reasoning + content JSON）。

    范式知识（矩阵/出口/工具目录/卡字段）在 DIAGNOSE_TEMPLATE.format() 之后拼接——
    避免这些含花括号的文本被 str.format 误解析（见 manifesto/py 花括号警示）。
    """
    ctx = context or '（未提供数据上下文）'
    prompt = _today_line() + MANIFESTO +DIAGNOSE_TEMPLATE.format(context=ctx, template_ids=template_id_list_text())
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


# ════════════ Phase B（D006·5.236）极瘦填卡 prompt：select_candidates 预选 → Flash 只填卡 ════════════
# 与 build_diagnose_prompt（复合兜底·45.8KB）配对：单/少候选（无 multi）走本极瘦版（<3.5KB·<5s）。
# 卡 schema 8 字段不变（DIAGNOSE_CARD_FIELDS）→ parseDiagnoseCard/harness 路由不动。
# 去 MANIFESTO/全量 catalog/B_TRACK/few-shot（候选 schema 过滤注入·只注 1-4 个）。
FILL_CARD_TEMPLATE = """

═══ Diagnose · 填卡（预选工具已定·你不选型·只填卡）═══

为下列**预选工具**填 diagnose 信息卡（8 字段 JSON）。**不做工具选型**（已由 0LLM 规则预选）·只填参数 + 维度 + 数据状态。

【预选工具】（template 只能取其一·method=[template]）：
{candidates_schema}

【输出】**严格 JSON 对象**（仅 JSON·禁 markdown 代码块/前后解释）：
{{
  "intent": "general|gis_operation|emotion_analysis",
  "domain_lens": ["urban_planning|urban_renewal|urban_operation|urban_governance|general"],
  "scale": "macro|meso|micro",
  "decision_type": "评价|选址|排查|对比|监测|定义|操作|通用问答",
  "outlet": "生成图层|地图定位|指标排序|报告结论|建议清单|预警|执行操作",
  "data_plan": {{ "strategy": "ready|fallback_annotated|request_upload", "needed": [], "available": [], "gap": [] }},
  "template": "<预选工具 id>",
  "method": ["<预选工具 id>"],
  "params": {{}}
}}

【规则】
1. template/method = 预选工具（1 个→直接填；多个→选最匹配问句的·**禁选预选外的**）。
2. params 按预选工具入参 schema 填（值从问句/grounding 派生·缺必填槽→strategy=request_upload·**禁编造字段名/数值**）。
3. data_plan.strategy：ready=数据齐·fallback_annotated=软缺口有替代·request_upload=硬缺口（关键数据无替代·该问不硬答）。
4. concept（概念问）→ intent=general·template=concept·params={{}}·method=[]。
5. domain_lens/scale/decision_type/outlet 据问句语义判·outlet 默认「生成图层」。
6. **数据纠错兜底（5.242·S8）**：若 grounding 显示预选工具数据明显不支撑（如 clip 但无点层 / density 但无情绪点）·即使预选了也须 data_plan.strategy=request_upload + rationale 说明需什么数据·勿硬填 ready 跑工具致失败。无候选时同理→request_upload。

【问句】
{question}

【grounding】（据此判 available/gap）
{context}
"""


def _candidate_schema_text(candidates):
    """渲染候选工具紧凑 schema（FILL_CARD 注入·从 TEMPLATE_REGISTRY 过滤·<400B/候选）。

    候选 skill id（select_candidates 产）→ TEMPLATE_REGISTRY 查·渲 required_slots + optional_defaults（=入参 schema）。"""
    by_skill = {s['skill']: s for s in TEMPLATE_REGISTRY}
    lines = []
    for sk in candidates:
        s = by_skill.get(sk)
        if not s:
            continue
        req = s.get('required_slots') or []
        opt = s.get('optional_defaults') or {}
        opt_hint = ', '.join(f'{k}={v!r}' for k, v in opt.items()) or '（无）'
        req_hint = ('必填:' + ','.join(req)) if req else '无必填'
        lines.append(f'- {sk}（{s.get("name", "")}）：{req_hint}；可选：{opt_hint}')
    return '\n'.join(lines) if lines else '- （无候选工具·当前数据不支撑任何预选工具·输出 data_plan.strategy=request_upload + rationale 说明需什么数据）'


@track("MOD_AIQA.F_009", track_args=False)
def build_fill_card_prompt(question, candidates, context: str = '', context_tokens: list = None) -> str:
    """Phase B 极瘦填卡 prompt（<3.5KB·D006）：select_candidates 预选工具 → Flash 只填卡（不选型）。

    卡 schema 8 字段不变 → 前端 parseDiagnoseCard/harness 路由不动。复合/0 候选走 build_diagnose_prompt 兜底（router 分派）。
    5.242：空候选（数据过滤后无工具可执）→ FILL_CARD 出 request_upload 卡（Flash 说明需什么数据）。"""
    schema = _candidate_schema_text(candidates or [])
    prompt = _today_line() + FILL_CARD_TEMPLATE.format(
        candidates_schema=schema, question=question or '（空）', context=context or '（无 grounding）')
    return _inject_tokens(prompt, context_tokens)


@track("MOD_AIQA.F_010", track_args=False)
def build_diagnose_prompt_dispatch(question, context: str = '', context_tokens: list = None, layer_meta=None):
    """Phase B+C（D006·5.236/5.237）diagnose prompt 分派（router 调·可单测·不打 LLM）：
    select_candidates(question, layer_meta) 预选 → 单/少候选（无 multi）走极瘦填卡（Flash·<3.5KB·<5s）·复合（multi）走 Pro 计划（D009·<5KB·5-10s·产 chain）。
    **5.242 数据感知**：layer_meta（{has_point,has_polygon}）喂 select_candidates → _filter_by_context 激活（解 context=None 数据盲）。
    空候选分二态：layer_meta 提供 + 空 = 数据不支撑 → fill_card 空（Flash 出 request_upload）；无 layer_meta + 空 = 大 prompt 兜底。
    返 (prompt, path, model_override)·path ∈ {'fill_card','fill_card_empty','plan','fallback'}。"""
    from ai_qa.candidate_selector import select_candidates
    cands = select_candidates(question or '', layer_meta)['candidates']
    if cands and 'multi' not in cands:
        return build_fill_card_prompt(question, cands, context, context_tokens), 'fill_card', None
    if 'multi' in cands:   # Phase C（D009+D012）：复合 → Pro 产工具链 plan → runChainPath 动态消费
        return build_plan_prompt(question, cands, context, context_tokens), 'plan', 'pro'
    # 空候选：layer_meta 提供（数据感知模式）→ 数据不支撑任何工具 → fill_card 空（Flash 出 request_upload）
    if layer_meta:
        return build_fill_card_prompt(question, [], context, context_tokens), 'fill_card_empty', None
    return build_diagnose_prompt(context, context_tokens), 'fallback', None


# ════════════ Phase C（D009+D012·5.237）Pro 复合计划 prompt：复合 → Pro 产工具链 chain ════════════
# 与 fill_card（单候选·Flash）/ diagnose（0 候选兜底）配对：复合（select_candidates 返 multi）走本 Pro plan。
# 产 diagnose 卡 + chain({name,steps:[{tool,params}]}) → 前端 normalizeCard 透传 chain → runChainPath 动态消费（取代固定 CHAIN_REGISTRY）。
PLAN_TEMPLATE = """

═══ Plan · 复合计划（Pro 推理·多步组合）═══

用户问句需**多步工具组合**（0LLM 规则预判为复合·select_candidates）。你的任务：拆解为工具链 plan（不做单步填卡·不做选型——复合组件已预选）。

【问句】
{question}

【候选工具（chain 的 tool 只能取这些）】
{candidates_schema}

【grounding】（据此判 available/gap）
{context}

【拆链规则】
- 拆 **2-3 步**·每步 {{ "tool": "...", "params": {{...}} }}。
- **$1/$2** 引用前序产图层步骤的结果（第 1/2 个产图层工具的输出·作下步的 layer/layer_a 等）。
- **{{question}}** 占位由问句填·其他上下文占位按语义填。
- tool+params 须**合法**（按候选 schema·禁编工具名/字段/数值）。
- name 用**现实内容**（如「西陵区内商业用地」·非"叠置/intersection"实现术语）。

【输出】**严格 JSON 对象**（仅 JSON·禁 markdown 代码块/解释）：
{{
  "intent": "gis_operation|emotion_analysis",
  "domain_lens": ["urban_planning|urban_renewal|urban_operation|urban_governance|general"],
  "scale": "macro|meso|micro",
  "template": "multi",
  "method": ["<step1 tool>", "<step2 tool>"],
  "data_plan": {{ "strategy": "ready|fallback_annotated|request_upload", "needed": [], "available": [], "gap": [] }},
  "chain": {{
    "name": "<现实内容名>",
    "steps": [
      {{ "tool": "<候选1>", "params": {{...}} }},
      {{ "tool": "<候选2>", "params": {{ "layer_a": "$1", ... }} }}
    ]
  }}
}}

【规则】① chain.steps ≥2·tool ∈ 候选·params 按 schema；② 缺数据→strategy=request_upload·chain 仍给但标局限；③ 诚实（禁编字段/数值·地图状态用户可见）。
"""


@track("MOD_AIQA.F_011", track_args=False)
def build_plan_prompt(question, candidates, context: str = '', context_tokens: list = None) -> str:
    """Phase C（D009+D012·5.237）Pro 复合计划 prompt（<5KB）：select_candidates 复合 → Pro 产工具链 plan。
    产 diagnose 卡 + chain({name,steps:[{tool,params}]}) → runChainPath 动态消费（取代固定 CHAIN_REGISTRY）。"""
    schema = _candidate_schema_text(candidates or [])
    prompt = _today_line() + PLAN_TEMPLATE.format(
        candidates_schema=schema, question=question or '（空）', context=context or '（无 grounding）')
    return _inject_tokens(prompt, context_tokens)


# 输出示例（注入 diagnose prompt 末尾·最强 recency）：3 条 Q→完整 JSON 卡，覆盖概念问(→concept)、
# 单工具操作(→density)、对已有结果的概念追问(→concept，防被 geo 词误导短路进操作)。
_DIAGNOSE_FEW_SHOT = """

═══════════ 附录 · 输出示例（仿此格式，**只输出 JSON 卡，不要任何前后解释/正文**）═══════════
【例1·概念问】用户问：什么是核密度分析
你的输出（仅此 JSON，不写概念解释正文）：
{"intent":"general","domain_lens":["general"],"scale":"macro","decision_type":"定义","outlet":"报告结论","data_plan":{"needed":[],"available":[],"gap":[],"strategy":"ready"},"template":"concept","params":{}}

【例2·单工具操作】用户问：做核密度分析 / 生成 L2 消极点的热力图
你的输出（综合→polarity=overall；极性词"消极/积极/中性"→对应 polarity，图面用对应色板非彩虹）：
{"intent":"gis_operation","domain_lens":["general"],"scale":"macro","decision_type":"操作","outlet":"生成图层","data_plan":{"needed":["L2 极性点"],"available":["L2 T1 极性点"],"gap":[],"strategy":"ready"},"template":"density","params":{"mode":"2d","polarity":"negative"}}

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


# CB-09 D022: revise stage deleted (REVISE_TEMPLATE + build_revise_prompt) -> frontend harness.applyQualityDefense (code defense, no LLM)

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

DEEP_ATTRIBUTION_TEMPLATE = """

═══════════ 本次任务 · 深度归因（L4 DEEP ATTRIBUTION）═══════════
你是城市情绪归因专家。下面给你一个**空间簇（zone/网格/单元内的评论集合）**的【领域×要素×极性】+ 簇内代表性评论
+ 规则底归因建议。请输出**政策→情绪→项目闭环**的深度归因：国家/主管政策（该领域应怎样）→ 情绪数据定位
（市民实际反馈什么、差在哪）→ 具体可落地项目（工程/治理/规划）。区别于规则底（按 domain×element 查表），
你要结合评论实质 + 下方权威语境，给**有具体所指、可操作**的归因，不泛泛。

【簇上下文】
{cluster_context}

输出**严格 JSON 对象**（仅 JSON，禁 markdown 代码块 / 前后解释）：
{{
  "deep_attribution": "一句深度归因（评论实质 + 落点矩阵格 + 差/好在哪。如：'修旧如旧获好评但业态同质化+烟火气商业化流失担忧，落 更新×文化/运营×服务，差在业态多元与原住民保留'）",
  "policy_link": "关联的顶层政策/标准（如：'住建部防止大拆大建通知（不大规模拆除/搬迁）+ 城市更新意见'）。无则空串",
  "project_link": "指向的具体项目类型（如：'历史街区保护更新 / 业态多元化引导 / 完整社区试点'）。无则空串",
  "confidence": 0.0,
  "blind_spot": "若涉及官方标准忽视的盲区（事件的瞬时空间影响 / 情绪微观颗粒）指明；无则空串"
}}
要求：
- 政策→情绪→项目必须闭合：policy_link（方向）+ deep_attribution（情绪实质+落点）+ project_link（可操作项目）。
- 多归属：一现象可落多矩阵格（domain×element），deep_attribution 点明主+次落点。
- 事件(element=事件)要素：给**瞬时空间影响**归因（官方体检按日均评估忽视的盲区=EMC 差异化价值）→ 填 blind_spot。
- confidence：评论充足+归因清晰→0.8+；评论少或泛→0.5；勉强→0.3。低置信会被上层回退规则底。
- 禁编造政策/项目名（须在下方权威语境内）；禁学术八股；权威术语+通俗解释。
"""


@track("MOD_AIQA.F_006", track_args=False)
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


@track("MOD_AIQA.F_007", track_args=False)
def build_deep_attribution_prompt(domain, element, polarity, zone_name, sample_texts, rule_suggestion,
                                  policy_seed_hint='', project_seed_hint='', aspect_hint=''):
    """L4 深度归因 prompt：簇评论 + 规则底 + 权威语境 → 政策→情绪→项目闭环 JSON（deep_attribution/policy_link/project_link/confidence/blind_spot）。
    lazy enrichment（EMC 深读某簇时按需触发，非 eager 每 aggregate 跑）；低置信/LLM 不可用由上层（/aiqa/deep_attribution）回退规则底。
    policy_seed_hint/project_seed_hint/aspect_hint：Sim 富归因数据（ermawu_l3l4）预提取的簇种子，作权威锚（LLM 优先采用，比凭空联想更准）。
    范式照 build_field_infer_prompt：MANIFESTO + TEMPLATE.format() + industry_kb 附录拼接（花括号安全）。"""
    from ai_qa.industry_kb import industry_kb_text
    samp = '\n'.join(f'  - {t}' for t in (sample_texts or [])[:8]) or '  - （无代表性评论）'
    cluster = (
        f'- 领域(domain)={domain or "?"} | 要素(element)={element or "?"} | 极性={polarity or "?"} | 区域={zone_name or "?"}\n'
        f'- 簇内代表性评论：\n{samp}\n'
        f'- 规则底归因建议（base，按 domain×element 查表，在此基础上深化，勿照抄）：{rule_suggestion or "（无）"}'
    )
    # Sim 富归因数据预提取的种子（A1+Sim 闭环：数据带 policy_seed/project_seed/aspect → 权威锚）
    hints = []
    if aspect_hint:
        hints.append(f'aspect 维度（簇内主导 ABSA 方面）：{aspect_hint}')
    if policy_seed_hint:
        hints.append(f'预提取政策锚（数据 policy_seed，**优先采用**）：{policy_seed_hint}')
    if project_seed_hint:
        hints.append(f'预提取落点项目（数据 project_seed，**优先采用**）：{project_seed_hint}')
    if hints:
        cluster += '\n- ' + '\n- '.join(hints)
    prompt = _today_line() + MANIFESTO + DEEP_ATTRIBUTION_TEMPLATE.format(cluster_context=cluster)
    kb = industry_kb_text(domain) if domain else ''
    if kb:
        prompt += '\n\n═══════════ 附录 · 聚焦领域权威语境（政策/项目/案例/归因焦点，政策→情绪→项目闭环依据）═══════════\n' + kb
    return prompt


# ════════════ Prompt 优化（5.215 · Flash 流式·不增维度·梳理已有要素）════════════
OPTIMIZE_TEMPLATE = """
你是情绪地图（Emotion Map）的 prompt 优化器。把用户输入**精准化扩充 + 逻辑梳理**（非改写）·从**用户向 EMC 提问**的语气·让 prompt 更明确。

精准化：模糊词→具体（"上传的范围/点数据"→参考下方数据的图层名；"分布情况"→"整体极性（积极/中性/消极）的空间分布"；"这边"→具体区域）。
逻辑：原文不清才梳理·清晰不改。
语气：用户提问（"分析 X 范围内 Y 的 Z 分布"）·非指导（"你应该/建议"）。
不启发：不加用户没提的维度（没提归因不加 4×5·没提时间不加 T1/T3）。

示例：输入「我想通过上传的范围和情绪点数据来分析情绪的分布情况」+ 数据有「中心城区范围」「L2情绪点」
→「分析「中心城区范围」范围内的「L2情绪点」的整体极性（积极/中性/消极）的空间分布。」

绝不：JSON / thought / action / 代码块 / 指导语气 / 加维度。只输出一段优化 prompt。

输入：{user_input}
数据：{context}
"""


@track("MOD_AIQA.F_008", track_args=False)
def build_optimize_prompt(context: str = '', user_input: str = '') -> str:
    """优化阶段（5.215）：把用户 NL 优化成具体/实操/逻辑清晰的 prompt（Flash 流式·<3s）。
    不增维度（只梳理已有要素）·让用户对需求更清晰（启发）。无 MANIFESTO（精简提速）。"""
    prompt = _today_line() + OPTIMIZE_TEMPLATE.format(user_input=user_input or '', context=context or '（未提供数据上下文）')
    return prompt


# ════════════ MOD_AIQA 追踪 ID 注册（build_*_prompt 承重入口）════════════
# diagnose prompt 永不动（保 Flash eval）——@track 是 pass-through 装饰器，不改 prompt 内容。
register_track_id("MOD_AIQA.F_002", "build_agent_prompt（ReAct agent loop 每轮 prompt）")
register_track_id("MOD_AIQA.F_003", "build_final_prompt（最终结论 prompt）")
# CB-09 D022：F_004（build_revise_prompt）已随 revise 阶段退役——ID 不重分配（保历史·新函数续 F_009+）。
register_track_id("MOD_AIQA.F_005", "build_diagnose_prompt（承重 eval-anchor：6 字段问题理解卡，永不动内容）")
register_track_id("MOD_AIQA.F_006", "build_field_infer_prompt（P2 字段语义推断）")
register_track_id("MOD_AIQA.F_007", "build_deep_attribution_prompt（L4 深度归因·政策→情绪→项目闭环，lazy enrichment）")
register_track_id("MOD_AIQA.F_008", "build_optimize_prompt（5.215 Prompt 优化·Flash 流式·不增维度·梳理已有要素）")
register_track_id("MOD_AIQA.F_009", "build_fill_card_prompt（Phase B 极瘦填卡·select_candidates 预选→Flash 填卡）")
register_track_id("MOD_AIQA.F_010", "build_diagnose_prompt_dispatch（Phase B+C 三路分派·5.242 数据感知 layer_meta）")
register_track_id("MOD_AIQA.F_011", "build_plan_prompt（Phase C Pro 复合计划·产 chain）")
