"""
情绪类型关键词词典 — Emotion Type Lexicon
==========================================
基于 jieba 关键词 + 情感词典的规则分类，用于 L2 粗粒度情绪类型识别。

七类情绪类型 — 采纳论文《基于网络社交数据的城市情绪地图及空间优化探索：以成都市为例》
（《规划师》2023.9）的双层分类体系（宏观极性 + 微观具体情绪），每类对齐一个城市规划
治理动作 + 论文情绪因子词锚点：

  愤怒     — 事故/灾害/严重侵权 → 紧急响应
  不满抱怨 — 设施服务差/脏乱老旧同质化 → 设施整改
  焦虑担忧 — 拥堵/停车/租房/安全隐患 → 安全出行治理
  失望厌恶 — 扰民/噪音/水臭/环境差 → 环境整治
  期待建议 — 市民献策/诉求 → 献策纳规
  喜悦满意 — 太阳/花朵/美食/通畅 → 标杆保护
  怀旧认同 — 武侯祠/历史文化/乡愁 → 文化传承

当 L3 (LLM) 接入后，可替换为更精确的分类器。词典独立文件，方便替换。

v2 (2026-06-18): 词典条目带置信权重 (word, weight)。分类用累加权重 argmax +
优先级兜底；强度公式加重词加成与短文本惩罚。
v3 (2026-06-18): 词表对齐论文 7 类 + 因子词锚点（论文积极/消极十大因子）。
"""

# 重词阈值：weight >= HEAVY_WEIGHT 视为"重词"，触发强度加成
HEAVY_WEIGHT = 0.9

# ── 情绪类型关键词词典（带权重，论文双层体系微观 7 类）──
# 每条 (word, weight)：1.0 = 核心/紧急词，0.6 = 一般词，0.4 = 弱/易误判词
# 分类时按类型累加权重，argmax 决定类型（同分按 PRIORITY_ORDER 兜底）
# 论文因子词（脏乱/拥堵/噪音/太阳…）作高权重锚点，对齐城市规划治理场景
EMOTION_LEXICON = {
    '愤怒': {
        # 极端负面，紧急响应（事故/灾害/严重侵权）
        'words': [
            ('事故', 1.0), ('灾难', 1.0), ('塌陷', 1.0), ('倒塌', 1.0),
            ('爆炸', 1.0), ('火灾', 1.0), ('中毒', 1.0), ('亡人', 1.0),
            ('惨', 0.9), ('坑人', 0.9), ('无耻', 0.9), ('愤怒', 1.0),
            ('气死', 0.9), ('恶心', 0.7), ('离谱', 0.7), ('荒唐', 0.8),
            ('豆腐渣', 1.0), ('草菅人命', 1.0),
        ],
    },
    '不满抱怨': {
        # 设施/服务整改（论文消极因子：脏乱/老旧/同质化/停车）
        'words': [
            ('脏乱', 1.0), ('脏', 0.7), ('乱', 0.5), ('老旧', 0.9),
            ('同质化', 0.9), ('千篇一律', 0.7), ('停车', 0.8), ('难停', 0.8),
            ('坏了', 0.7), ('破损', 0.8), ('烂', 0.6), ('停工', 0.7),
            ('闲置', 0.6), ('废弃', 0.6), ('没人管', 0.8), ('不作为', 0.8),
            ('投诉', 0.8), ('举报', 0.8), ('踢皮球', 0.8), ('敷衍', 0.7),
            ('太慢', 0.5), ('太贵', 0.5), ('不方便', 0.6), ('不合理', 0.6),
            ('不满意', 0.7), ('物业', 0.5), ('差', 0.4),
        ],
    },
    '焦虑担忧': {
        # 安全/出行治理（论文消极因子：拥堵/租房/出行）
        'words': [
            ('拥堵', 1.0), ('堵车', 0.9), ('堵', 0.6), ('租房', 0.9),
            ('房租', 0.8), ('买房', 0.7), ('危险', 1.0), ('隐患', 0.9),
            ('治安', 0.8), ('安全', 0.7), ('害怕', 0.8), ('担心', 0.7),
            ('担忧', 0.7), ('不安', 0.6), ('紧张', 0.6), ('污染', 0.8),
            ('偷盗', 0.7), ('骚扰', 0.7), ('报警', 0.6), ('求助', 0.6),
            ('黑灯', 0.5), ('无灯', 0.5), ('没灯', 0.5), ('昏暗', 0.5),
        ],
    },
    '失望厌恶': {
        # 环境整治（论文消极因子：扰民/噪音/水臭）
        'words': [
            ('扰民', 1.0), ('噪音', 1.0), ('吵', 0.7), ('水臭', 1.0),
            ('臭', 0.7), ('雨季', 0.8), ('积水', 0.7), ('污水', 0.8),
            ('失望', 1.0), ('心寒', 0.9), ('无语', 0.7), ('遗憾', 0.6),
            ('厌烦', 0.8), ('烦', 0.5), ('不如', 0.6), ('还不如', 0.7),
            ('越来越差', 0.8), ('可惜', 0.6), ('竟然', 0.5), ('居然', 0.5),
        ],
    },
    '期待建议': {
        # 献策纳规（诉求类，建设性）
        'words': [
            ('建议', 0.9), ('应该', 0.7), ('最好', 0.7), ('希望', 0.7),
            ('能不能', 0.6), ('要是', 0.5), ('增加', 0.7), ('减少', 0.6),
            ('改进', 0.7), ('改善', 0.7), ('优化', 0.7), ('提升', 0.7),
            ('完善', 0.7), ('改造', 0.7), ('增设', 0.8), ('修建', 0.7),
            ('规划', 0.6), ('便民', 0.7), ('利民', 0.7), ('惠民', 0.7),
            ('提议', 0.7), ('呼吁', 0.7), ('期待', 0.8), ('盼望', 0.7),
        ],
    },
    '喜悦满意': {
        # 标杆保护（论文积极因子：太阳/花朵/美食/火锅/麻将/喝茶）
        'words': [
            ('太阳', 1.0), ('晒太阳', 1.0), ('见雪山', 1.0), ('雪山', 0.9),
            ('花朵', 0.9), ('花', 0.5), ('美食', 0.9), ('火锅', 0.9),
            ('麻将', 0.8), ('喝茶', 0.8), ('通畅', 0.9), ('逛街', 0.7),
            ('满意', 0.9), ('点赞', 1.0), ('好评', 0.9), ('棒', 0.8),
            ('非常好', 0.9), ('不错', 0.6), ('漂亮', 0.6), ('干净', 0.6),
            ('整洁', 0.6), ('舒服', 0.6), ('幸福', 0.8), ('开心', 0.7),
            ('高兴', 0.7), ('喜悦', 0.8), ('感谢', 0.7), ('焕然一新', 0.9),
        ],
    },
    '怀旧认同': {
        # 文化传承（论文积极因子：武侯祠/文殊院/金沙/历史文化）
        'words': [
            ('武侯祠', 1.0), ('文殊院', 1.0), ('金沙', 0.9), ('历史', 0.7),
            ('历史文化', 0.9), ('底蕴', 0.8), ('传承', 0.8), ('怀旧', 0.9),
            ('怀念', 1.0), ('想念', 0.9), ('乡愁', 0.9), ('故乡', 0.8),
            ('记忆', 0.7), ('回忆', 0.7), ('童年', 0.8), ('老城', 0.8),
            ('老街', 0.8), ('老字号', 0.8), ('认同', 0.8), ('自豪', 0.9),
            ('守护', 0.7), ('保护', 0.6), ('留住', 0.7),
        ],
    },
}

# 优先级：分类同分时按此顺序兜底；紧急/负面优先
# （'其他' 不在词典内，由 score 兜底分支返回）
PRIORITY_ORDER = ['愤怒', '不满抱怨', '焦虑担忧', '失望厌恶', '期待建议', '喜悦满意', '怀旧认同']


def _lexicon_match(text: str) -> tuple[dict, bool]:
    """
    扫描文本，返回 (type_weights, heavy_hit)。

    - type_weights: {emotion_type: accumulated_weight}
    - heavy_hit: 是否命中任何 weight >= HEAVY_WEIGHT 的重词（用于强度加成）
    """
    text = str(text)
    type_weights = {}
    heavy_hit = False
    for etype, entry in EMOTION_LEXICON.items():
        total = 0.0
        for word, weight in entry['words']:
            if word in text:
                total += weight
                if weight >= HEAVY_WEIGHT:
                    heavy_hit = True
        if total > 0:
            type_weights[etype] = total
    return type_weights, heavy_hit


def _argmax_type(type_weights: dict, score: float) -> str:
    """从累加权重 dict 取 argmax 类型；同分按 PRIORITY_ORDER 兜底；空则按 score 兜底。"""
    if not type_weights:
        if score < 0.3:
            return '不满抱怨'
        elif score > 0.7:
            return '喜悦满意'
        else:
            return '其他'
    best_type = None
    best_weight = -1.0
    for etype in PRIORITY_ORDER:
        w = type_weights.get(etype, 0.0)
        if w > best_weight:
            best_weight = w
            best_type = etype
    if best_type is None:
        best_type = max(type_weights, key=type_weights.get)
    return best_type


# ── 分类逻辑 ──

def classify_emotion_type(text: str, score: float = 0.5) -> str:
    """
    基于关键词权重累加 + argmax 的情绪类型分类。

    参数:
        text: 评论文本
        score: SnowNLP 综合情绪得分 (0-1)

    返回:
        情绪类型标签: 愤怒/不满抱怨/焦虑担忧/失望厌恶/期待建议/喜悦满意/怀旧认同/其他
        （'其他' 为中性兜底，无关键词命中且 score 中性时返回）
    """
    text = str(text).strip()
    if not text:
        return '其他'
    type_weights, _ = _lexicon_match(text)
    return _argmax_type(type_weights, score)


def calc_emotion_intensity(score: float, text: str = '', keywords_count: int = 0,
                            heavy_hit: bool = False) -> float:
    """
    综合计算情绪强度 (0-1)。

    计算逻辑:
        - base: score 偏离中性 (0.5) 的程度 = abs(score - 0.5) * 2
        - short_text_penalty: text_len < 8 时 base *= 0.7（短文本易过激）
        - density_bonus: 关键词密度加成，最多 +0.2
        - heavy_bonus: 命中重词（事故/塌陷/拥堵/扰民等）+0.15
        - 最终: min(base + density_bonus + heavy_bonus, 1.0)
    """
    base = abs(score - 0.5) * 2  # 0-1

    text_str = str(text).strip()
    text_len = max(len(text_str), 1)
    if text_len < 8:
        base *= 0.7

    density = min(keywords_count / max(text_len / 50, 1), 1) * 0.2

    if not heavy_hit and text_str:
        _, heavy_hit = _lexicon_match(text_str)
    heavy_bonus = 0.15 if heavy_hit else 0.0

    return round(min(base + density + heavy_bonus, 1.0), 3)


def analyze_emotion(text: str, score: float, keywords_count: int = 0
                     ) -> tuple[str, float]:
    """
    一次扫描同时产出情绪类型 + 强度（复用同一次词典匹配，避免重复扫描）。

    返回: (emotion_type, emotion_intensity)
    供 emotion_analysis_v1.py 批量路径调用，比分别调两个函数快。
    """
    text_str = str(text).strip()
    if not text_str:
        return '其他', round(min(abs(score - 0.5) * 2, 1.0), 3)

    type_weights, heavy_hit = _lexicon_match(text_str)
    emo_type = _argmax_type(type_weights, score)
    intensity = calc_emotion_intensity(
        score, text_str, keywords_count, heavy_hit=heavy_hit
    )
    return emo_type, intensity
