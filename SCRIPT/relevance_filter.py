"""
相关性筛选模块 v2.0 — Relevance Filter (L1.5)
===============================================
基于两层漏斗架构判断社交媒体文本是否与城市感受/需求相关。

两层漏斗:
  1. keyword_prefilter(text) — 信号评分粗筛，目标过滤率 15-20%
  2. llm_classify(text, api_key) — DeepSeek LLM 精分类

关键词层 v2.0 设计 — 正负信号加权评分:
  - 负向信号 (每命中 -15): 美妆/穿搭/游戏/纯私人情感/娱乐八卦/纯健身
  - 正向信号 (每命中 +20): 地点指示词/城市问题词/城市体验词
  - 评分: score = 50 + 正向命中*20 - 负向命中*15
  - score < 20  → reject (高置信度无关)
  - score >= 70 → pass (高置信度相关，可跳过 LLM)
  - 20 <= score < 70 → pass to LLM (不确定)
  - 特殊规则: 宜昌地名/地址格式 → 直接 pass; 纯广告/纯灌水 → 直接 reject

主函数:
  filter_relevance(df, api_key) — 对 DataFrame 执行两层过滤

用法:
    from SCRIPT.relevance_filter import filter_relevance
    df_filtered = filter_relevance(df, api_key="sk-xxx")

调试模式:
    设置环境变量 DEBUG_KEYWORD=1 可打印每条文本的评分详情

依赖:
    pip install requests
    DeepSeek API Key (环境变量 DEEPSEEK_API_KEY 或函数参数传入)

编码铁律:
    - 所有 print() 使用 _safe_print()
    - 无 emoji，仅 ASCII 标记 [OK]/[WARN]/[ERR]/[LOAD]
    - API Key 不硬编码，从环境变量读取
"""

import os
import sys
import json
import time
import builtins as _bi
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import pandas as pd
import requests

from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id

# ── 安全 print — 防止 Windows GBK 控制台崩溃 ──
_real_print = _bi.print


def _safe_print(*args, **kwargs):
    try:
        _real_print(*args, **kwargs)
    except UnicodeEncodeError:
        _real_print(
            *(str(a).encode('ascii', errors='replace').decode('ascii') for a in args),
            **kwargs,
        )


# 修复 Windows GBK 控制台编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ═══════════════════════════════════════════════════════════
# 常量配置
# ═══════════════════════════════════════════════════════════

DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = 'deepseek-chat'
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # 指数退避基数（秒）
BATCH_SIZE = 20         # 每批并发 LLM 调用数（可调高至 50，注意 API 限流）
REQUEST_TIMEOUT = 30    # 单次 API 请求超时（秒）

# ═══════════════════════════════════════════════════════════
# 关键词信号评分词汇池 (v2.0)
# ═══════════════════════════════════════════════════════════

# ── 负向信号词 (每命中一个 -15 分) ──
# 当文本不含城市信号时，这些领域的专有词汇大概率无关

NEG_BEAUTY = [
    '口红', '粉底', '眼影', '腮红', '护肤', '面膜', '精华液', '隔离霜',
    '定妆', '美甲', '发型', '空瓶记', '色号', '试色', '底妆', '卸妆',
    '水乳', '安瓶', '气垫', '遮瑕', '高光', '修容', '睫毛', '眉笔',
    '妆前乳', '素颜霜', 'BB霜', 'CC霜',
    # v2.1 扩充: 品牌名
    '雅诗兰黛', '兰蔻', '迪奥', '香奈儿', 'YSL', 'MAC',
    '花西子', '完美日记', '珂拉琪', 'INTO YOU', '橘朵', '稚优泉', 'colorkey',
    # v2.1 扩充: 强信号词
    '眼影盘', '口红试色', '彩妆', '护肤步骤', '早C晚A', '刷酸', '以油养肤', '沉浸式护肤',
]

NEG_FASHION = [
    '穿搭', 'OOTD', '显瘦', '百搭', '阔腿裤', '连衣裙', '卫衣', 'T恤',
    '衬衫', '牛仔裤', '半身裙', '风衣', '羽绒服', '毛衣', '西装',
    '高跟鞋', '帆布鞋', '配饰', '包包', '撞色',
    # v2.1 扩充: OOTD 变体 + 强信号
    '今日穿搭', '一周穿搭', '早春穿搭', '秋冬穿搭',
    'ootd', '显高显瘦', '梨形身材', '小个子穿搭', '通勤穿搭', '约会穿搭',
]

NEG_GAMING = [
    '王者荣耀', '吃鸡', '原神', '崩坏', '星穹铁道', 'LOL', 'DOTA',
    '上分', '排位', '开黑', '氪金', '抽卡', '抽到SSR', 'SSR卡', '副本', '公会',
    # v2.1 扩充: 热门游戏
    '王者', '原神启动', '崩铁', '阴阳师', '第五人格', '明日方舟', '碧蓝航线',
]

NEG_PERSONAL = [
    'crush', '暗恋', '前任', '脱单', '相亲', '分手', '复合', '暧昧',
    '心动', '意中人', '表白',
    # v2.1 扩充: 强情感信号
    '分手快乐', '复合了吗', '前任', '相亲经历', '母单', '单身狗', '注孤生', '情感树洞',
]

NEG_ENTERTAINMENT = [
    '明星', '爱豆', '饭圈', '追星', '演唱会', '综艺', '选秀', '塌房',
    '官宣', '嗑cp', '组CP',
]

NEG_FITNESS = [
    '减脂', '增肌', '撸铁', '深蹲', '卧推', '有氧', '帕梅拉', 'HIIT',
    '跳绳打卡',
]

# v2.1 新增: 宠物相关
NEG_PET = [
    '猫咪', '狗狗', '主子', '喵星人', '汪星人', '撸猫', '撸狗', '猫奴', '狗奴',
    '猫粮', '狗粮', '猫砂', '遛狗绳', '宠物店',
]

# v2.1 新增: 纯日常灌水
NEG_DAILY = [
    '早安', '晚安', '今天也是', '无聊的一天', '又是摸鱼', '不想上班',
    '今天吃什么', '午饭打卡', '下班了吗',
]

# 合并所有负向信号词 (附带类别名，便于调试)
NEG_SIGNAL_POOLS = [
    ('beauty', NEG_BEAUTY),
    ('fashion', NEG_FASHION),
    ('gaming', NEG_GAMING),
    ('personal', NEG_PERSONAL),
    ('entertainment', NEG_ENTERTAINMENT),
    ('fitness', NEG_FITNESS),
    ('pet', NEG_PET),
    ('daily', NEG_DAILY),
]


# ── 正向信号词 (每命中一个 +20 分) ──
# 这些信号暗示文本可能与城市空间/服务相关

POS_LOCATION = [
    '巷', '公园', '广场', '小区', '社区', '桥', '河',
    '站', '商圈', 'CBD', '校区',
]

# 单字地点词 — 权重降低为 +10，避免误匹配"思路""路透社""街道办"等无关内容
POS_LOCATION_LOW_WEIGHT = [
    '路', '街', '道',
]

POS_URBAN_ISSUE = [
    '修', '建', '拆', '投诉', '扰民', '噪音', '垃圾', '停车', '物业',
    '路灯', '绿化', '违建', '占道', '摆摊', '拆迁', '施工',
]

POS_URBAN_EXPERIENCE = [
    '打卡', '推荐', '好吃', '好玩', '拍照', '周末', '逛', '散步', '遛弯',
    '遛狗', '骑行', '跑步',
]

# 合并所有正向信号词（location_low 权重为 +10，其余 +20）
POS_SIGNAL_POOLS = [
    ('location', POS_LOCATION),
    ('location_low', POS_LOCATION_LOW_WEIGHT),
    ('urban_issue', POS_URBAN_ISSUE),
    ('urban_experience', POS_URBAN_EXPERIENCE),
]


# ── 纯广告词 (命中且无正向信号 → 直接 reject) ──
PURE_AD_KEYWORDS = [
    '加微信', '扫码', '扫码添加', '扫码咨询',
    '兼职', '刷单', '代理', '免费领取',
]


# ── 宜昌安全网地名 (命中任一 → 直接 pass，不受评分影响) ──
# NOTE: '万达'/'CBD'/'国贸' 为通用商业地名，当前仅限宜昌数据范围使用。
# 若跨城市使用，需替换为对应城市的地标名称，否则会造成误匹配。
YICHANG_SAFEGUARD_PLACES = [
    '滨江', '东山', '运河', '儿童公园', '磨基山', '夷陵', '西陵', '伍家岗',
    '点军', '猇亭', 'CBD', '万达', '国贸', '均瑶', '水悦城', '三峡大学',
    '葛洲坝', '长江', '黄柏河',
]


# ── 灌水检测：中文字符少于该数 → 直接 reject ──
MIN_CHINESE_CHARS = 8

# ── 非中文内容比例阈值：超过此比例且文本长度>10 → 直接 reject ──
NON_CHINESE_RATIO_THRESHOLD = 0.8
MIN_TEXT_LEN_FOR_RATIO_CHECK = 10


# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════

def _count_chinese(text: str) -> int:
    """统计文本中中文字符数量。"""
    return sum(1 for c in text if '\u4e00' <= c <= '\u9fff')


def _has_address_pattern(text: str) -> bool:
    """检测是否包含具体地址格式 (如 'xx路xx号'、'xx小区xx栋')。"""
    import re
    patterns = [
        r'\S{1,6}路\d{1,6}号',       # xx路xx号
        r'\S{1,6}街\d{1,6}号',       # xx街xx号
        r'\S{1,8}小区\d{1,4}栋',     # xx小区xx栋
        r'\S{1,8}小区\S{1,4}号楼',    # xx小区xx号楼
        r'\S{1,8}村\d{1,4}号',       # xx村xx号
    ]
    for pat in patterns:
        if re.search(pat, text):
            return True
    return False


# ═══════════════════════════════════════════════════════════
# 第一层: 信号评分粗筛 (v2.0)
# ═══════════════════════════════════════════════════════════

def _score_keyword_relevance(text: str) -> tuple:
    """
    对文本进行正负信号加权评分（调试用）。

    Args:
        text: 待评分文本

    Returns:
        (score: int, reasons: list[str])
        score = 50 + 正向命中*20 - 负向命中*15
        reasons 列出每条命中/不命中的原因
    """
    reasons = []
    score = 50
    pos_hits = 0
    neg_hits = 0

    # ── 正向信号扫描 ──
    for pool_name, pool_words in POS_SIGNAL_POOLS:
        for word in pool_words:
            if word in text:
                pos_hits += 1
                if pool_name == 'location_low':
                    score += 10
                    reasons.append(f'+10 [{pool_name}] "{word}"')
                else:
                    score += 20
                    reasons.append(f'+20 [{pool_name}] "{word}"')

    # ── 负向信号扫描 ──
    for pool_name, pool_words in NEG_SIGNAL_POOLS:
        for word in pool_words:
            if word in text:
                neg_hits += 1
                score -= 15
                reasons.append(f'-15 [{pool_name}] "{word}"')

    reasons.insert(0, f'score={score} (base=50, +{pos_hits}*20, -{neg_hits}*15)')
    return score, reasons


@track("MOD_REL.F_001", track_args=False)
def keyword_prefilter(text: str) -> str:
    """
    信号评分粗筛 — 快速排除高置信度无关内容。

    评分机制:
      - 正负信号加权评分，起始 50 分
      - score < 20  → reject (高置信度无关，命中 2+ 负向且无正向)
      - score >= 70 → pass (高置信度相关)
      - 20 <= score < 70 → pass to LLM (不确定)

    特殊规则 (不受评分影响):
      - 直接 pass: 宜昌地名 / 具体地址格式
      - 直接 reject: 中文<8字符 / 纯广告且无正向信号 / 非中文占比>80%
                     / 连续重复字符灌水 / 低质短文本无正向信号

    Args:
        text: 待筛选文本 (title + text 拼接)

    Returns:
        'pass'   — 需要 LLM 进一步判断, 或高置信度相关
        'reject' — 直接剔除
    """
    debug_mode = os.environ.get('DEBUG_KEYWORD', '0') == '1'

    if not text or not isinstance(text, str):
        if debug_mode:
            _safe_print(f'[KEYWORD-DEBUG] reject: empty or non-string')
        return 'reject'

    text_stripped = text.strip()
    if not text_stripped:
        if debug_mode:
            _safe_print(f'[KEYWORD-DEBUG] reject: whitespace only')
        return 'reject'

    chinese_count = _count_chinese(text_stripped)

    # ── 直接 reject: 中文字符过少 (纯灌水/纯emoji) ──
    if chinese_count < MIN_CHINESE_CHARS:
        if debug_mode:
            _safe_print(
                f'[KEYWORD-DEBUG] reject: chinese_chars={chinese_count} '
                f'< {MIN_CHINESE_CHARS} | text={text_stripped[:80]}'
            )
        return 'reject'

    # ── 直接 reject: 连续重复字符灌水 (如"哈哈哈哈哈哈") ──
    import re as _re
    if _re.search(r'(.)\1{4,}', text_stripped):
        if debug_mode:
            _safe_print(
                f'[KEYWORD-DEBUG] reject: repeated_char_pattern '
                f'| text={text_stripped[:80]}'
            )
        return 'reject'

    # ── 直接 reject: 连续重复短词灌水 (如"笑死笑死笑死") ──
    if _re.search(r'(.{2,3})\1{2,}', text_stripped):
        if debug_mode:
            _safe_print(
                f'[KEYWORD-DEBUG] reject: repeated_phrase_pattern '
                f'| text={text_stripped[:80]}'
            )
        return 'reject'

    # ── 直接 reject: 非中文内容占比过高 ──
    text_len = len(text_stripped)
    if text_len > MIN_TEXT_LEN_FOR_RATIO_CHECK:
        non_chinese_ratio = 1.0 - (chinese_count / text_len)
        if non_chinese_ratio > NON_CHINESE_RATIO_THRESHOLD:
            if debug_mode:
                _safe_print(
                    f'[KEYWORD-DEBUG] reject: non_chinese_ratio={non_chinese_ratio:.1%} '
                    f'> {NON_CHINESE_RATIO_THRESHOLD:.0%} | text={text_stripped[:80]}'
                )
            return 'reject'

    # ── 直接 pass: 宜昌安全网地名 ──
    for place in YICHANG_SAFEGUARD_PLACES:
        if place in text_stripped:
            if debug_mode:
                _safe_print(
                    f'[KEYWORD-DEBUG] direct-pass: yichang_place="{place}" '
                    f'| text={text_stripped[:80]}'
                )
            return 'pass'

    # ── 直接 pass: 具体地址格式 ──
    if _has_address_pattern(text_stripped):
        if debug_mode:
            _safe_print(
                f'[KEYWORD-DEBUG] direct-pass: address_pattern '
                f'| text={text_stripped[:80]}'
            )
        return 'pass'

    # ── 纯广告检测 (命中且无正向信号 → 直接 reject) ──
    has_ad_keyword = any(kw in text_stripped for kw in PURE_AD_KEYWORDS)
    if has_ad_keyword:
        # 检查是否有正向信号
        has_pos_signal = any(
            word in text_stripped
            for _, pool_words in POS_SIGNAL_POOLS
            for word in pool_words
        )
        if not has_pos_signal:
            if debug_mode:
                _safe_print(
                    f'[KEYWORD-DEBUG] reject: pure_ad_no_pos_signal '
                    f'| text={text_stripped[:80]}'
                )
            return 'reject'

    # ── 低质短文本检测: 中文>=8 但 <15 且无正向信号 → reject ──
    if 8 <= chinese_count < 15:
        has_pos = any(
            word in text_stripped
            for _, pool_words in POS_SIGNAL_POOLS
            for word in pool_words
        )
        if not has_pos:
            if debug_mode:
                _safe_print(
                    f'[KEYWORD-DEBUG] reject: low_quality_short '
                    f'(chinese_chars={chinese_count}, no_pos_signal) '
                    f'| text={text_stripped[:80]}'
                )
            return 'reject'

    # ── 正负信号加权评分 ──
    score, reasons = _score_keyword_relevance(text_stripped)

    if debug_mode:
        _safe_print(
            f'[KEYWORD-DEBUG] {"reject" if score < 20 else "pass"} '
            f'| {" | ".join(reasons)} | text={text_stripped[:120]}'
        )

    if score < 20:
        return 'reject'

    # NOTE: score >= 70 "skip LLM" optimization is NOT yet enabled.
    # Currently all pass results are sent to LLM for final classification.
    # When enabled, score >= 70 can bypass LLM to save API costs.
    # 20 <= score < 70: 不确定，交给 LLM
    return 'pass'


# ═══════════════════════════════════════════════════════════
# 第二层: DeepSeek LLM 精分类 (单条)
# ═══════════════════════════════════════════════════════════

LLM_SYSTEM_PROMPT = """你是一个城市研究助手，正在帮助分析市民对城市的真实感受。
请阅读以下社交媒体文本，判断它是否表达了市民对城市空间、
设施、环境、服务、文化或事件的感受、需求或评价。

【五要素】
- 设施：城市公共设施、基础设施（道路、交通、停车、公园、
       学校、医院、体育设施、商业配套等）
- 环境：城市自然环境或建成环境（绿化、空气质量、噪音、
       卫生、景观风貌、水系、街道界面等）
- 服务：城市公共服务或商业服务（物业管理、环卫保洁、
       公共交通、政务服务、商户服务、社区服务等）
- 文化：城市文化空间或活动（历史街区、文创园区、
       节庆活动、展览演出、网红打卡地、街区氛围等）
- 事件：城市相关事件或变化（拆迁施工、投诉举报、
       政策影响、社区活动、突发事件、街区变化等）
- 情绪：文本中体现了怎样的情绪倾向（满足/期待/失望/愤怒/喜爱/
       怀念/好奇/无所谓）

【输出格式】严格按 JSON 返回，不要有任何其他文字：
{
  "relevant": true,
  "dimensions": ["设施","文化"],
  "primary_emotion": "喜爱",
  "urban_value": "high",
  "summary": "一句话概括市民在表达什么城市相关感受",
  "has_location_clue": true
}

【判断原则】
- relevant=false 仅限以下情况：纯广告/垃圾信息、纯私人情感倾诉
  且无地点信息、纯灌水内容
- 旅游打卡、美食探店、街区体验——这些都是 relevant=true，
  它们反映了城市活力和空间品质
- 任何提及具体地点、场所、设施的文本，即使主要是消费分享，
  也视为 relevant=true
- urban_value 分级：
  · high：直接讨论城市问题、政策或建议
  · medium：表达对城市空间/服务/环境的感受或评价
  · low：附带地点信息但城市属性较弱
- 宽容原则：不确定时，倾向于 relevant=true"""


# ═══════════════════════════════════════════════════════════
# 批量 LLM 分类 System Prompt (新)
# ═══════════════════════════════════════════════════════════

LLM_BATCH_SYSTEM_PROMPT = """你是一个城市研究助手。请分析以下社交媒体文本，判断它们是否表达了市民对城市的感受。

【目标】从市民日常表达中，识别与城市空间、设施、环境、服务、文化、事件相关的真实感受。

【判断标准】
relevant=true（保留）：
- 提及具体地点（路、街、小区、公园、商场、学校等）并表达感受
- 讨论城市问题（修路、噪音、停车、物业、卫生、绿化等）
- 分享城市体验（逛公园、打卡街区、骑行绿道、参加活动等）
- 涉及城市政策或变化（拆迁、施工、限行、新建设施等）
- 表达对社区/邻里的评价

relevant=false（剔除）：
- 纯美妆护肤、时尚穿搭（无地点信息）
- 纯个人情感倾诉（无地点信息）
- 纯宠物分享（无城市设施关联）
- 纯广告/引流
- 纯游戏/动漫/娱乐八卦
- 文本过短无法判断（<5字）

【分类维度】对 relevant=true 的文本，标注：
- relevance_category: 设施/环境/服务/文化/事件（单选）
- primary_emotion: 满足/期待/失望/愤怒/喜爱/怀念/好奇/中性
- emotion_intensity: 1-5（1=微弱, 5=强烈）
- has_location: true/false
- location_mentioned: 提取文本中提到的具体地点名称
- urban_value: high(直接讨论城市问题或建议)/medium(表达对城市空间的感受)/low(附带地点但城市属性弱)
- ai_summary: 一句话概括市民表达了什么（<=20字）

【输出格式】严格返回 JSON 数组，不要有任何其他文字：
[
  {"id":0, "relevant":true, "relevance_category":"设施", "primary_emotion":"失望", 
   "emotion_intensity":4, "has_location":true, "location_mentioned":"胜利四路",
   "urban_value":"high", "ai_summary":"市民反映修路导致出行不便", "ai_confidence":0.92},
  ...
]

【宽容原则】不确定时倾向于 relevant=true。旅游打卡、美食探店、街区体验都应保留——它们反映城市活力和空间品质。"""



def _get_api_key(api_key: Optional[str] = None) -> str:
    """获取 API Key：优先使用传入值，否则从环境变量读取。"""
    if api_key:
        return api_key
    key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not key:
        raise ValueError(
            'DeepSeek API Key 未设置。请设置环境变量 DEEPSEEK_API_KEY '
            '或传入 api_key 参数。'
        )
    return key


def _parse_llm_response(response_text: str) -> dict:
    """
    解析 LLM 返回的 JSON 响应。

    处理常见格式问题：
      - Markdown 代码块包裹 (```json ... ```)
      - 前后多余空白/换行
      - JSON 解析失败时的降级策略
    """
    text = response_text.strip()

    # 去除 Markdown 代码块标记
    if text.startswith('```'):
        # 找到第一个换行后的内容
        lines = text.split('\n')
        # 去除首行 ```json 或 ```
        if lines[0].startswith('```'):
            lines = lines[1:]
        # 去除末行 ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        text = '\n'.join(lines).strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取 JSON 对象
        import re
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
            except json.JSONDecodeError:
                raise ValueError(f'无法解析 LLM 响应为 JSON: {text[:200]}')
        else:
            raise ValueError(f'LLM 响应中未找到 JSON 对象: {text[:200]}')

    # 标准化字段
    result.setdefault('relevant', False)
    result.setdefault('dimensions', [])
    result.setdefault('primary_emotion', '')
    result.setdefault('urban_value', 'low')
    result.setdefault('summary', '')
    result.setdefault('has_location_clue', False)

    return result


@track("MOD_REL.F_002", track_args=False)
def llm_classify(text: str, api_key: Optional[str] = None) -> dict:
    """
    调用 DeepSeek LLM 进行文本分类。

    Args:
        text: 待分类文本（title + text 拼接）
        api_key: DeepSeek API Key，不传则从环境变量 DEEPSEEK_API_KEY 读取

    Returns:
        {
            'relevant': bool,
            'dimensions': list[str],
            'primary_emotion': str,
            'urban_value': str,
            'summary': str,
            'has_location_clue': bool,
            'error': str | None,  # 仅在出错时有值
        }

    Raises:
        不抛出异常 — 所有错误通过返回 dict 中的 'error' 字段传递
    """
    key = _get_api_key(api_key)

    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }

    payload = {
        'model': DEEPSEEK_MODEL,
        'messages': [
            {'role': 'system', 'content': LLM_SYSTEM_PROMPT},
            {'role': 'user', 'content': text},
        ],
        'temperature': 0.1,  # 低温度，追求一致性
        'max_tokens': 500,
        'stream': False,
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if resp.status_code == 200:
                data = resp.json()
                content = data['choices'][0]['message']['content']
                result = _parse_llm_response(content)
                result['error'] = None
                return result

            elif resp.status_code == 429:
                # 限流 — 指数退避
                wait_time = RETRY_DELAY_BASE ** attempt
                _safe_print(
                    f'[WARN] API 限流 (429)，第 {attempt}/{MAX_RETRIES} 次重试，'
                    f'等待 {wait_time}s ...'
                )
                time.sleep(wait_time)
                last_error = f'API 限流 (429)'

            elif resp.status_code in (500, 502, 503, 504):
                # 服务端错误 — 重试
                wait_time = RETRY_DELAY_BASE ** attempt
                _safe_print(
                    f'[WARN] API 服务端错误 ({resp.status_code})，'
                    f'第 {attempt}/{MAX_RETRIES} 次重试，等待 {wait_time}s ...'
                )
                time.sleep(wait_time)
                last_error = f'服务端错误 ({resp.status_code})'

            else:
                # 不可恢复的错误
                error_msg = f'API 返回非预期状态码: {resp.status_code}'
                _safe_print(f'[ERR] {error_msg}')
                return {
                    'relevant': False,
                    'dimensions': [],
                    'primary_emotion': '',
                    'urban_value': 'low',
                    'summary': '',
                    'has_location_clue': False,
                    'error': error_msg,
                }

        except requests.exceptions.Timeout:
            _safe_print(
                f'[WARN] API 请求超时，第 {attempt}/{MAX_RETRIES} 次重试 ...'
            )
            time.sleep(RETRY_DELAY_BASE ** attempt)
            last_error = '请求超时'

        except requests.exceptions.ConnectionError as e:
            _safe_print(
                f'[WARN] 网络连接错误: {e}，'
                f'第 {attempt}/{MAX_RETRIES} 次重试 ...'
            )
            time.sleep(RETRY_DELAY_BASE ** attempt)
            last_error = f'网络连接错误: {e}'

        except Exception as e:
            _safe_print(f'[ERR] LLM 分类异常: {e}')
            return {
                'relevant': False,
                'dimensions': [],
                'primary_emotion': '',
                'urban_value': 'low',
                'summary': '',
                'has_location_clue': False,
                'error': str(e),
            }

    # 所有重试耗尽
    return {
        'relevant': False,
        'dimensions': [],
        'primary_emotion': '',
        'urban_value': 'low',
        'summary': '',
        'has_location_clue': False,
        'error': last_error or '重试耗尽',
    }


# ═══════════════════════════════════════════════════════════
# 批量 LLM 分类 (新)
# ═══════════════════════════════════════════════════════════

def _parse_llm_batch_response(response_text: str, batch_size: int) -> list[dict]:
    """
    解析批量 LLM 返回的 JSON 数组响应。

    处理常见格式问题：
      - Markdown 代码块包裹 (```json ... ```)
      - 前后多余空白/换行
      - JSON 解析失败时的降级策略（逐条 fallback）

    Args:
        response_text: LLM 原始响应文本
        batch_size: 本批次期望的结果数量

    Returns:
        list[dict] — 长度与 batch_size 一致，解析失败的位置填充默认值
    """
    text = response_text.strip()

    # 去除 Markdown 代码块标记
    if text.startswith('```'):
        lines = text.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        text = '\n'.join(lines).strip()

    try:
        results = json.loads(text)
        if isinstance(results, list):
            return results
        elif isinstance(results, dict):
            # 某些模型可能返回 {"results": [...]} 或单个对象
            if 'results' in results:
                return results['results']
            return [results]
    except json.JSONDecodeError:
        pass

    # 降级: 尝试提取 JSON 数组
    import re
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            results = json.loads(match.group(0))
            if isinstance(results, list):
                return results
        except json.JSONDecodeError:
            pass

    # 最终降级: 返回默认值填充
    trace_error("MOD_REL.D_005", "failed to parse batch LLM response", 
                exc=ValueError(f"response[:200]: {text[:200]}"))
    return [
        {
            'id': i,
            'relevant': False,
            'relevance_category': '',
            'primary_emotion': '',
            'emotion_intensity': 0,
            'has_location': False,
            'location_mentioned': '',
            'urban_value': 'low',
            'ai_summary': '',
            'ai_confidence': 0.0,
        }
        for i in range(batch_size)
    ]


def _build_batch_user_content(batch: list[dict]) -> str:
    """
    构建批量 LLM 请求的 user message 内容。

    Args:
        batch: [{'id_e': 'e0001', 'text': '...', 'title': '...'}, ...]

    Returns:
        格式化的 user content 字符串
    """
    lines = ["请分析以下文本："]
    for i, item in enumerate(batch):
        title = item.get('title', '') or ''
        text = item.get('text', '') or ''
        content = f"{title} {text}".strip()
        if not content:
            content = '(empty)'
        lines.append(f"[{i}] {content}")
    return "\n".join(lines)


@track("MOD_REL.F_005", track_args=True)
def llm_classify_batch(texts: list[dict], api_key: str = None, batch_size: int = 50,
                       progress_callback=None) -> list[dict]:
    """
    批量 LLM 分类：一次 API 调用处理多条文本。

    Args:
        texts: [{'id_e': 'e0001', 'text': '...', 'title': '...', 'source': '...'}, ...]
        api_key: DeepSeek API Key
        batch_size: 每批处理条数（默认 50）
        progress_callback: 进度回调 callable(current, total, message)

    Returns:
        [{'id_e': 'e0001', 'relevance': 'relevant', 'relevance_category': '设施',
          'primary_emotion': '失望', 'emotion_intensity': 4, 'has_location': True,
          'location_mentioned': '胜利四路', 'urban_value': 'high',
          'ai_summary': '市民反映胜利四路修路导致出行不便', 'ai_confidence': 0.92}, ...]
    """
    key = _get_api_key(api_key)
    total = len(texts)
    all_results = []

    total_batches = (total + batch_size - 1) // batch_size

    _safe_print(f'[LOAD] 批量 LLM 分类开始: {total} 条文本, '
                f'batch_size={batch_size}, 共 {total_batches} 批')

    for batch_num in range(0, total, batch_size):
        batch = texts[batch_num:batch_num + batch_size]
        current_batch_no = (batch_num // batch_size) + 1

        with TrackContext("MOD_REL.D_004", 
                          batch=f"{current_batch_no}/{total_batches}",
                          n_texts=len(batch)):
            # 构建 user content
            user_content = _build_batch_user_content(batch)

            headers = {
                'Authorization': f'Bearer {key}',
                'Content-Type': 'application/json',
            }

            payload = {
                'model': DEEPSEEK_MODEL,
                'messages': [
                    {'role': 'system', 'content': LLM_BATCH_SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_content},
                ],
                'temperature': 0.1,
                'max_tokens': 4096,
            }

            last_error = None
            batch_results = None

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    resp = requests.post(
                        DEEPSEEK_API_URL,
                        headers=headers,
                        json=payload,
                        timeout=120,
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        content = data['choices'][0]['message']['content']
                        batch_results = _parse_llm_batch_response(content, len(batch))
                        break

                    elif resp.status_code == 429:
                        wait_time = RETRY_DELAY_BASE ** attempt
                        _safe_print(
                            f'[WARN] 批量 API 限流 (429)，'
                            f'批次 {current_batch_no}/{total_batches}, '
                            f'第 {attempt}/{MAX_RETRIES} 次重试，等待 {wait_time}s ...'
                        )
                        time.sleep(wait_time)
                        last_error = 'API 限流 (429)'

                    elif resp.status_code in (500, 502, 503, 504):
                        wait_time = RETRY_DELAY_BASE ** attempt
                        _safe_print(
                            f'[WARN] 批量 API 服务端错误 ({resp.status_code})，'
                            f'批次 {current_batch_no}/{total_batches}, '
                            f'第 {attempt}/{MAX_RETRIES} 次重试，等待 {wait_time}s ...'
                        )
                        time.sleep(wait_time)
                        last_error = f'服务端错误 ({resp.status_code})'

                    else:
                        error_msg = f'API 返回非预期状态码: {resp.status_code}'
                        _safe_print(f'[ERR] 批量 {error_msg}')
                        trace_error("MOD_REL.D_004", error_msg)
                        last_error = error_msg
                        break

                except requests.exceptions.Timeout:
                    _safe_print(
                        f'[WARN] 批量 API 请求超时，'
                        f'批次 {current_batch_no}/{total_batches}, '
                        f'第 {attempt}/{MAX_RETRIES} 次重试 ...'
                    )
                    time.sleep(RETRY_DELAY_BASE ** attempt)
                    last_error = '请求超时'

                except requests.exceptions.ConnectionError as e:
                    _safe_print(
                        f'[WARN] 批量 网络连接错误: {e}，'
                        f'批次 {current_batch_no}/{total_batches}, '
                        f'第 {attempt}/{MAX_RETRIES} 次重试 ...'
                    )
                    time.sleep(RETRY_DELAY_BASE ** attempt)
                    last_error = f'网络连接错误: {e}'

                except Exception as e:
                    _safe_print(f'[ERR] 批量 LLM 分类异常: {e}')
                    trace_error("MOD_REL.D_004", f"batch LLM exception", exc=e)
                    last_error = str(e)
                    break

            # ── 处理本批结果 ──
            if batch_results is None:
                # 所有重试耗尽，生成默认结果
                _safe_print(f'[WARN] 批次 {current_batch_no}/{total_batches} '
                            f'失败: {last_error}, 生成默认 irrelevant 结果')
                batch_results = [
                    {
                        'id': i,
                        'relevant': False,
                        'relevance_category': '',
                        'primary_emotion': '',
                        'emotion_intensity': 0,
                        'has_location': False,
                        'location_mentioned': '',
                        'urban_value': 'low',
                        'ai_summary': '',
                        'ai_confidence': 0.0,
                    }
                    for i in range(len(batch))
                ]

            # 将 LLM 返回的 id（数组索引）映射回 id_e
            for i, item in enumerate(batch):
                result = {}
                # 在 batch_results 中按 id 匹配
                matched = None
                for r in batch_results:
                    if r.get('id') == i:
                        matched = r
                        break
                if matched is None and i < len(batch_results):
                    matched = batch_results[i]

                if matched:
                    result = {
                        'id_e': item['id_e'],
                        'relevance': 'relevant' if matched.get('relevant') else 'irrelevant',
                        'relevance_category': matched.get('relevance_category', ''),
                        'primary_emotion': matched.get('primary_emotion', ''),
                        'emotion_intensity': int(matched.get('emotion_intensity', 0) or 0),
                        'has_location': bool(matched.get('has_location', False)),
                        'location_mentioned': matched.get('location_mentioned', '') or '',
                        'urban_value': matched.get('urban_value', 'low') or 'low',
                        'ai_summary': matched.get('ai_summary', '') or '',
                        'ai_confidence': float(matched.get('ai_confidence', 0.0) or 0.0),
                    }
                else:
                    result = {
                        'id_e': item['id_e'],
                        'relevance': 'irrelevant',
                        'relevance_category': '',
                        'primary_emotion': '',
                        'emotion_intensity': 0,
                        'has_location': False,
                        'location_mentioned': '',
                        'urban_value': 'low',
                        'ai_summary': '',
                        'ai_confidence': 0.0,
                    }
                all_results.append(result)

            trace_log("MOD_REL.D_004",
                      detail=f"batch {current_batch_no}/{total_batches} done, "
                             f"got {len(batch_results)} results")

        # ── 进度回调 ──
        if progress_callback:
            progress_callback(
                min(batch_num + batch_size, total),
                total,
                f'LLM batch {current_batch_no}/{total_batches}'
            )

    # ── 汇总统计 ──
    n_relevant = sum(1 for r in all_results if r['relevance'] == 'relevant')
    n_location = sum(1 for r in all_results if r.get('has_location'))
    _safe_print(f'[OK] 批量 LLM 分类完成: {total} 条输入 → '
                f'{n_relevant} relevant, {n_location} has_location')

    return all_results


def _build_text_for_classification(row: pd.Series) -> str:
    """
    从 DataFrame 行构建用于分类的文本。

    优先级: title + text > text > title > comments
    """
    title = str(row.get('title', '')).strip() if pd.notna(row.get('title')) else ''
    text = str(row.get('text', '')).strip() if pd.notna(row.get('text')) else ''
    comments = str(row.get('comments', '')).strip() if pd.notna(row.get('comments')) else ''

    # title 和 text 相同时不重复拼接
    if title and text:
        if title == text:
            return text
        return f'{title}\n{text}'
    elif text:
        return text
    elif title:
        return title
    elif comments:
        return comments
    return ''


# ═══════════════════════════════════════════════════════════
# 主函数: 两层漏斗过滤
# ═══════════════════════════════════════════════════════════

@track("MOD_REL.F_003", track_args=True)
def filter_relevance(
    df: pd.DataFrame,
    api_key: Optional[str] = None,
    batch_size: int = BATCH_SIZE,
) -> pd.DataFrame:
    """
    [DEPRECATED v2.0] 对 DataFrame 执行两层漏斗相关性筛选。

    流程:
      1. 关键词粗筛 (keyword_prefilter) → reject 的直接标记
      2. 通过粗筛的文本 → DeepSeek LLM 精分类 (每批 batch_size 条并发)

    新增列:
      - relevance:              'relevant' | 'irrelevant'
      - relevance_dimensions:   相关维度列表 (JSON 字符串)
      - relevance_emotion:      主要情绪
      - relevance_urban_value:  城市价值等级 (high/medium/low)
      - relevance_summary:      LLM 摘要
      - filter_layer:           筛选层级 ('keyword' | 'llm')

    Args:
        df: 输入 DataFrame（需含 title/text/comments 中的至少一列）
        api_key: DeepSeek API Key，不传则从环境变量 DEEPSEEK_API_KEY 读取
        batch_size: LLM 并发批量大小（默认 5）

    Returns:
        添加了 relevance 系列列的 DataFrame（不删除行，由调用方决定过滤策略）
    """
    _safe_print(f'[LOAD] 相关性筛选开始，共 {len(df)} 条数据')

    total = len(df)

    # ── 初始化新列 ──
    df = df.copy()
    df['relevance'] = 'irrelevant'
    df['relevance_dimensions'] = ''
    df['relevance_emotion'] = ''
    df['relevance_urban_value'] = ''
    df['relevance_summary'] = ''
    df['filter_layer'] = ''

    # ── 第一层: 关键词粗筛 ──
    _safe_print('[LAYER 1] 关键词粗筛 ...')
    keyword_pass_indices = []
    keyword_reject_count = 0

    for idx in df.index:
        text = _build_text_for_classification(df.loc[idx])
        result = keyword_prefilter(text)
        if result == 'pass':
            keyword_pass_indices.append(idx)
        else:
            df.at[idx, 'relevance'] = 'irrelevant'
            df.at[idx, 'filter_layer'] = 'keyword'
            keyword_reject_count += 1

    _safe_print(
        f'[OK] 关键词粗筛完成: {len(keyword_pass_indices)} 条 pass, '
        f'{keyword_reject_count} 条 reject'
    )

    if not keyword_pass_indices:
        _safe_print('[WARN] 关键词粗筛后无数据通过，跳过 LLM 分类')
        return df

    # ── 第二层: LLM 精分类 (批量并发) ──
    _safe_print(f'[LAYER 2] LLM 精分类 (DeepSeek {DEEPSEEK_MODEL}) ...')

    key = _get_api_key(api_key)  # 提前校验 API Key
    llm_processed = 0

    # 分批处理
    pass_list = list(keyword_pass_indices)
    total_batches = (len(pass_list) + batch_size - 1) // batch_size

    for batch_num in range(0, len(pass_list), batch_size):
        batch_indices = pass_list[batch_num:batch_num + batch_size]
        current_batch = (batch_num // batch_size) + 1

        # 准备批次数据
        batch_data = {}
        for idx in batch_indices:
            text = _build_text_for_classification(df.loc[idx])
            batch_data[idx] = text

        # 并发调用 LLM
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {
                executor.submit(llm_classify, text, key): idx
                for idx, text in batch_data.items()
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = {
                        'relevant': False,
                        'dimensions': [],
                        'primary_emotion': '',
                        'urban_value': 'low',
                        'summary': '',
                        'has_location_clue': False,
                        'error': str(e),
                    }

                llm_processed += 1

                if result.get('error'):
                    df.at[idx, 'relevance'] = 'error'
                    df.at[idx, 'filter_layer'] = 'llm_error'
                    df.at[idx, 'relevance_summary'] = result['error']
                else:
                    if result.get('relevant'):
                        df.at[idx, 'relevance'] = 'relevant'
                    else:
                        df.at[idx, 'relevance'] = 'irrelevant'
                    df.at[idx, 'filter_layer'] = 'llm'
                    # 填充详细字段（仅在 LLM 成功返回时执行）
                    dims = result.get('dimensions', [])
                    df.at[idx, 'relevance_dimensions'] = (
                        json.dumps(dims, ensure_ascii=False) if dims else ''
                    )
                    df.at[idx, 'relevance_emotion'] = result.get('primary_emotion', '')
                    df.at[idx, 'relevance_urban_value'] = result.get('urban_value', '')
                    df.at[idx, 'relevance_summary'] = result.get('summary', '')

        # 进度显示（从 DataFrame 列值统计，避免并发累加反模式）
        batch_relevant = (df['relevance'] == 'relevant').sum()
        batch_irrelevant = ((df['relevance'] == 'irrelevant') & (df['filter_layer'] == 'llm')).sum()
        batch_errors = (df['relevance'] == 'error').sum()
        pct = min(100, round(llm_processed / len(pass_list) * 100, 1))
        _safe_print(
            f'  [LOAD] 批次 {current_batch}/{total_batches} '
            f'({llm_processed}/{len(pass_list)}, {pct}%) '
            f'| relevant: {batch_relevant} | irrelevant: {batch_irrelevant} '
            f'| errors: {batch_errors}'
        )

    # ── 汇总统计（从 DataFrame 列值统计，避免并发累加反模式） ──
    llm_relevant = (df['relevance'] == 'relevant').sum()
    llm_irrelevant = ((df['relevance'] == 'irrelevant') & (df['filter_layer'] == 'llm')).sum()
    llm_errors = (df['relevance'] == 'error').sum()

    _safe_print('\n' + '=' * 50)
    _safe_print('  相关性筛选完成')
    _safe_print('=' * 50)
    _safe_print(f'  总数据:        {total}')
    _safe_print(f'  关键词剔除:    {keyword_reject_count}')
    _safe_print(f'  LLM 判定相关:  {llm_relevant}')
    _safe_print(f'  LLM 判定无关:  {llm_irrelevant}')
    _safe_print(f'  LLM 错误:      {llm_errors}')
    _safe_print(f'  最终相关:      {llm_relevant}')
    _safe_print('')

    return df


# ═══════════════════════════════════════════════════════════
# 辅助: 打印相关性分布统计
# ═══════════════════════════════════════════════════════════

@track("MOD_REL.F_004", track_args=False)
def print_relevance_stats(df: pd.DataFrame):
    """
    打印相关性筛选的分布统计。

    包括: 各维度计数、urban_value 分布。
    """
    if 'relevance' not in df.columns:
        _safe_print('[WARN] DataFrame 无 relevance 列，跳过统计')
        return

    relevant_df = df[df['relevance'] == 'relevant']

    _safe_print('\n--- 相关性分布统计 ---')
    _safe_print(f'  相关数据: {len(relevant_df)} / {len(df)} 条')

    if relevant_df.empty:
        _safe_print('  (无相关数据，跳过维度统计)')
        return

    # ── 各维度计数 ──
    import collections
    dim_counter = collections.Counter()
    for dims_str in relevant_df['relevance_dimensions']:
        if dims_str:
            try:
                dims = json.loads(dims_str)
                for d in dims:
                    dim_counter[d] += 1
            except (json.JSONDecodeError, TypeError):
                pass

    if dim_counter:
        _safe_print('\n  维度分布:')
        for dim, count in dim_counter.most_common():
            _safe_print(f'    {dim}: {count}')

    # ── urban_value 分布 ──
    uv_counts = relevant_df['relevance_urban_value'].value_counts()
    if not uv_counts.empty:
        _safe_print('\n  urban_value 分布:')
        for val, count in uv_counts.items():
            if val:
                _safe_print(f'    {val}: {count}')

    # ── 情绪分布 ──
    emo_counts = relevant_df['relevance_emotion'].value_counts()
    if not emo_counts.empty:
        _safe_print('\n  情绪分布:')
        for emo, count in emo_counts.head(10).items():
            if emo:
                _safe_print(f'    {emo}: {count}')

    _safe_print('')

# ── 追踪 ID 注册表 ──
register_track_id("MOD_REL.F_001", "关键词预筛选（正负信号加权评分）")
register_track_id("MOD_REL.F_002", "DeepSeek LLM 精分类（五要素城市感受）")
register_track_id("MOD_REL.F_003", "两层漏斗完整过滤（关键词+LLM）")
register_track_id("MOD_REL.F_004", "输出相关性统计报告")
register_track_id("MOD_REL.F_005", "批量 LLM 分类（一次API调用处理50条）")
register_track_id("MOD_REL.D_004", "批量 LLM 单批API请求+重试循环")
register_track_id("MOD_REL.D_005", "批量 LLM 响应JSON解析降级")
