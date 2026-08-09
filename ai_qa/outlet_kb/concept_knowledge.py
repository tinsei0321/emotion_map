"""CB-22 三层架构 P1：概念库（type='concept'·RAG 检索素材·高度凝练+引用摘抄）。

定位（用户澄清）：概念库 = RAG 知识库一部分（非独立物理库）——产品定义/宏观背景/边界认知·高度凝练 + 引用摘抄。
3 类（Codex V5 来源清单·防随意生成）：
  ① 产品定位（EMC = 城市连续主观体检·宏观诊断）
  ② 方法论（尺度-方法-范式·4×5 归因·三段式出口）
  ③ 边界认知（能/不能·四态·颗粒度·不替代客观）
每条 ≤200 字·**摘抄+引用（标来源）·禁 LLM 重述生成**（Codex V5·防口径漂移·与案例"只取方法论"同纪律）。
来源：MANIFESTO（ai_qa/manifesto.py）/ CLAUDE.md / paradigm.py（scale_paradigm）。
"""
from typing import List, Dict

CONCEPTS: List[Dict] = [
    # ── ① 产品定位（来源：CLAUDE.md「产品本质」+ KNOWLEDGE 蒸馏）──
    {
        'id': 'CONCEPT-P01',
        'topic': '产品定位',
        'name': '情绪地图 = 城市的连续主观体检',
        'detail': '情绪地图 = 城市的"连续主观体检"/情绪气象图：基于海量评论（社交/点评/热线）的统计聚合·'
                  '产物性格注定偏宏观——看见分布与演变·非精确测量。价值 = 让规划者定位关注区 + 生成假设 + 排序优先级·'
                  '而非微观精确诊断。宏观是定位护城河·不是局限（来源：CLAUDE.md 产品本质）。',
        'keywords': '产品定位 连续主观体检 宏观诊断 情绪地图',
        'source': 'CLAUDE.md 产品本质',
    },
    {
        'id': 'CONCEPT-P02',
        'topic': '产品定位',
        'name': 'EMC+RAG = 本地化聚焦专业知识蒸馏',
        'detail': 'EMC 通过 RAG 实现纯问答 → 稳定准确全面的相关信息（宜昌城市更新/体检专题）。'
                  '核心价值 = 区别于网络搜索/其他 AI——本地化（宜昌专属）+ 聚焦（更新/体检）+ 专业（权威源）+ '
                  '可追溯（来源引用）的专业知识蒸馏（来源：KNOWLEDGE.md §2 产品定位蒸馏·CB-22）。',
        'keywords': '产品定位 RAG 专业知识蒸馏 本地化 聚焦 可追溯',
        'source': 'KNOWLEDGE.md §2（CB-22）',
    },
    {
        'id': 'CONCEPT-P03',
        'topic': '产品定位',
        'name': '演示逻辑链 = 项目北极星',
        'detail': '张力图面（深红/深绿）→ 引导点击突出要素 → 交互分析张力原因 → 定位关注区 + 主题倾向 + 排序优先级'
                  '（宏观诊断信号·供规划者假设/排序）。一切数据服务表现力·一切演示服务有用性'
                  '（来源：CLAUDE.md 演示逻辑链）。',
        'keywords': '演示逻辑链 表现力 有用性 宏观诊断',
        'source': 'CLAUDE.md 演示逻辑链',
    },

    # ── ② 方法论（来源：paradigm.py scale_paradigm + CLAUDE.md 项目设计哲学）──
    {
        'id': 'CONCEPT-M01',
        'topic': '方法论',
        'name': '尺度-方法-范式（结论颗粒度 = 数据来源维度）',
        'detail': '城市体检/更新四维度：城区 ⊃ 街区 ⊃ 社区 ⊃ 小区+零散住房/城中村（层级包含）。'
                  '概念关键：社区≠小区（社区=行政区划·小区=居住形态单元·社区⊃n 个小区）。'
                  '数据来自哪个维度 → 只能得到哪个维度的答案（不臆造越维）。'
                  '宏观禁落单点·微观禁泛泛（来源：paradigm.py SCALE_PARADIGM + KNOWLEDGE §2 颗粒度·CB-22）。',
        'keywords': '方法论 颗粒度 尺度 范式 社区 小区 数据维度',
        'source': 'paradigm.py + KNOWLEDGE.md §2（CB-22）',
    },
    {
        'id': 'CONCEPT-M02',
        'topic': '方法论',
        'name': '4×5 = 归因落点矩阵（跨领域×要素多归属）',
        'detail': '4 领域（规划/更新/运营/治理）× 5 要素（设施/环境/服务/文化/事件）——表达"这片区域的情绪主题倾向"·'
                  '是宏观诊断信号·非指标分类清单、非精确归因。一个现象可落多个格（多归属是表达力·不是缺位）。'
                  '归因底层逻辑 = 政策→情绪→项目 方向性锚（来源：CLAUDE.md 项目设计哲学）。',
        'keywords': '方法论 4x5 归因矩阵 多归属 政策情绪项目',
        'source': 'CLAUDE.md 项目设计哲学',
    },
    {
        'id': 'CONCEPT-M03',
        'topic': '方法论',
        'name': '三支柱（纯回答稳定性缺一不可）',
        'detail': '纯回答稳定性 = ① 本地知识库完备度（素材）+ ② EMC 架构（分类→范式映射·正确路由）+ '
                  '③ LLM 归纳总结能力（综合素材+引用来源）——三者缺一不可。'
                  'RAG 检索出相关文件必须走 LLM 综合总结（零 LLM 拼列表 = 砍第三支柱·用户验证否定）'
                  '（来源：KNOWLEDGE.md §2 三支柱·CB-22）。',
        'keywords': '方法论 三支柱 知识库 架构 LLM 综合',
        'source': 'KNOWLEDGE.md §2（CB-22）',
    },

    # ── ③ 边界认知（来源：CLAUDE.md 产品本质 + 四态出口契约）──
    {
        'id': 'CONCEPT-B01',
        'topic': '边界认知',
        'name': 'EMC 不替代客观检测（能/不能边界）',
        'detail': '情绪地图 = 市民感知层（主观·宏观诊断信号）·不替代客观检测（官方体检硬指标/工程检测）。'
                  '出口卡「能/不能」双栏：情绪=市民感知·不替代客观——定位关注区 + 生成假设 + 排序优先级'
                  '（来源：CLAUDE.md 出口抽象层 + 出口卡片体系）。',
        'keywords': '边界认知 能 不能 主观感知 客观检测 不替代',
        'source': 'CLAUDE.md 出口抽象层',
    },
    {
        'id': 'CONCEPT-B02',
        'topic': '边界认知',
        'name': '四态出口契约（success/gap/partial/answered）',
        'detail': 'EMC 回答策略 = harness 代码强制终态（做成/缺数据/部分/纯问答）——非模型自觉。'
                  '知识问答走 answered（LLM 综合素材）·检索失败走 gap 兜底（禁 LLM 凭空编·防情绪分析式幻觉）'
                  '（来源：KNOWLEDGE §1 四态出口契约 + EMC 三态出口契约记忆）。',
        'keywords': '边界认知 四态出口 契约 兜底 防幻觉',
        'source': 'KNOWLEDGE.md §1（CB 红线）',
    },
    {
        'id': 'CONCEPT-B03',
        'topic': '边界认知',
        'name': 'NL 意图判断必须通过 LLM（规则仅加速器）',
        'detail': '用户输入自然语言的意图判断（NL→intent）必须通过 LLM（EMC 接入 LLM 的核心价值）——'
                  '规则词表不得承担判断主体（仅可做明显命中直通省调用·漏网全落 diagnose 由 LLM 判）。'
                  '意图判断 agent 位置在计划执行之前（诊断阶段）（来源：CLAUDE.md AI·Copilot 内核 + CB-22 用户拍板）。',
        'keywords': '边界认知 NL 意图判断 LLM 加速器 意图归位',
        'source': 'CLAUDE.md AI·Copilot 内核（CB-22 用户拍板）',
    },
]


def all_concepts() -> List[Dict]:
    """概念卡列表（供 RAG 索引 _load_concepts）。"""
    return CONCEPTS
