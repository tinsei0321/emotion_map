"""
情绪语义分析引擎 v1.0 — Emotion Analysis Engine (L2/L3/L4 三级架构)
══════════════════════════════════════════════════════════════
设计原则：
  1. 可插拔 — SnowNLP 今日，LLM 明日，Corpus 未来，同一接口
  2. 逐级叠加 — L2(基础) → L3(增强) → L4(归因)，每级不破坏前级
  3. 向量化管道 — 批量处理，避免逐行循环
  4. 独立模块 — 不依赖 Streamlit，可被任何应用调用

三级分析架构：
  ┌─────────────────────────────────────────────────────────┐
  │ L2 · 基础情绪分析（SnowNLP）                             │
  │ 综合情绪得分 + 五级极性 + 情绪关键词 + 置信度              │
  │ 现状：✅ 已实现，生产可用                                 │
  ├─────────────────────────────────────────────────────────┤
  │ L3 · LLM 语义增强（DeepSeek / Qwen / GLM …）             │
  │ 情绪类别 + 情绪强度 + 情绪对象(设施/环境/服务/文化/事件)    │
  │ 现状：⚠️ 接口已预留，待 API 接入                          │
  ├─────────────────────────────────────────────────────────┤
  │ L4 · 多维归因分析（自研语料库 + LLM）                    │
  │ 情绪因果归因 + 改善建议 + 证据溯源                        │
  │ 现状：🔮 框架已预留，语料库开发中                         │
  └─────────────────────────────────────────────────────────┘

L3 中文语义/情感分析模型推荐：
  · DeepSeek-V3 — 性价比高，中文理解优秀，API 稳定
  · 通义千问 Qwen-Max — 阿里云，情感分析 benchmark 领先
  · 智谱 GLM-4 — 国产开源标杆，支持细粒度情感分类
  · 百度 ERNIE 4.0 — 百度生态，NLU 能力强
  · 讯飞星火 — 语音+文本多模态，政务场景经验丰富

══════════════════════════════════════════════════════════════
"""
import os, re, json, sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Union

import pandas as pd
import numpy as np
from tqdm import tqdm

# 确保可导入 core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 安全 print — 防止 Windows GBK 控制台崩溃
import builtins as _bi
_real_print = _bi.print

def _safe_print(*args, **kwargs):
    try:
        _real_print(*args, **kwargs)
    except UnicodeEncodeError:
        _real_print(*(str(a).encode('ascii', errors='replace').decode('ascii') for a in args), **kwargs)

# 修复 Windows GBK 控制台 emoji 编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from core.config import (
    SCORE_POSITIVE, SCORE_NEGATIVE, PROCESSED_DIR,
)
from core.data_loader import load_emotion_data
from core.export import export_to_csv, export_to_geojson


# ═══════════════════════════════════════════════════════════
# 一、数据结构定义（L2 → L3 → L4 逐级叠加）
# ═══════════════════════════════════════════════════════════

@dataclass
class EmotionResult:
    """
    统一情绪分析结果 — 字段按 L2→L3→L4 逐级叠加。

    L2 (SnowNLP)          — score, polarity, keywords, confidence
    L3 (LLM) 在 L2 基础上 — category, intensity, target_type, target_detail
    L4 (Corpus+LLM) 在 L3 基础上 — attributions, suggestions
    """

    phase: str = 'L2'                     # 分析阶段标识: 'L2' | 'L3' | 'L4'

    # ── L2: 基础情绪分析（SnowNLP 引擎）──
    score: float = 0.5                    # 综合情绪得分 0~1（0=极端负面, 1=极端正面）
    polarity: str = 'Neutral'             # 五级极性: Very Negative / Negative / Neutral
                                          #            Positive / Very Positive
    keywords: list = field(default_factory=list)   # 情绪关键词（jieba 分词提取）
    confidence: float = 1.0               # 置信度（L2 默认 1.0，L3/L4 由模型提供）

    # ── L3: LLM 语义增强（在 L2 基础上叠加）──
    category: Optional[str] = None        # 情绪类别: 喜悦/愤怒/悲伤/惊讶/厌恶/恐惧/中性
    intensity: Optional[float] = None     # 情绪强度 0~1（与 score 互补：score 看正负，intensity 看浓淡）
    target_type: Optional[str] = None     # 情绪对象类型（五类）:
                                          #   设施 — 建筑/道路/公园/照明/停车…
                                          #   环境 — 噪音/卫生/绿化/空气/水质…
                                          #   服务 — 态度/效率/价格/售后/管理…
                                          #   文化 — 氛围/历史/艺术/活动/社区…
                                          #   事件 — 交通事故/施工/庆典/投诉/纠纷…
    target_detail: Optional[str] = None   # 情绪对象具体描述（如"小区门口的路灯"）

    # ── L4: 多维归因分析（自研语料库 + LLM，在 L3 基础上叠加）──
    attributions: Optional[list] = None   # 归因列表 [{"cause":str, "cause_category":str,
                                          #            "weight":float, "evidence":str}, …]
    suggestions: Optional[list] = None    # 改善建议 ["建议1", "建议2", …]

    # ── 调试用 ──
    raw_response: Optional[str] = None    # 原始模型返回（调试/审计用）

    # ── 向后兼容字段（已废弃，保留以兼容旧代码）──
    target: Optional[str] = None          # ⚠️ 已废弃，请用 target_type + target_detail

    def to_dict(self) -> dict:
        """转为字典（None 值不输出，空列表输出 []）"""
        result = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            if k == 'target':
                continue  # 废弃字段，不输出
            result[k] = v
        return result

    def get_polarity_level(self) -> int:
        """返回极性数值等级：-2(极负面) ~ +2(极正面)，方便统计聚合"""
        mapping = {
            'Very Negative': -2, 'Negative': -1, 'Neutral': 0,
            'Positive': 1, 'Very Positive': 2,
        }
        return mapping.get(self.polarity, 0)

    def is_actionable(self) -> bool:
        """是否需要行动干预（负面及以上）"""
        return self.polarity in ('Negative', 'Very Negative')

    def is_benchmark(self) -> bool:
        """是否可作为正面标杆（非常正面）"""
        return self.polarity == 'Very Positive'


@dataclass
class AnalysisReport:
    """批量分析报告"""
    phase: str                            # 分析阶段
    engine_name: str                      # 引擎名称
    engine_version: str                   # 引擎版本
    results: list                         # EmotionResult 列表
    summary: dict                         # 统计摘要
    meta: dict                            # 元信息（耗时、参数等）


# ═══════════════════════════════════════════════════════════
# 二、工具函数
# ═══════════════════════════════════════════════════════════

def _score_to_polarity(score: float) -> str:
    """
    将 0~1 分数映射为五级极性。

    区间划分理由（面向城市更新/治理/运营）：
      Very Negative  (0.00~0.20): 严重投诉/安全隐患 → 需紧急干预
      Negative       (0.20~0.40): 一般不满/吐槽 → 需关注改善
      Neutral        (0.40~0.60): 中性陈述/无明显情感
      Positive       (0.60~0.80): 一般满意/认可 → 维持即可
      Very Positive  (0.80~1.00): 非常满意/自发推荐 → 可作为标杆

    三级兼容（向后兼容旧代码）：
      旧 Positive = 新 Very Positive + Positive (≥0.7)
      旧 Negative = 新 Very Negative + Negative (≤0.3)
      旧 Neutral  = 新 Neutral (0.3~0.7)
    """
    if score <= 0.20:
        return 'Very Negative'
    elif score <= 0.40:
        return 'Negative'
    elif score <= 0.60:
        return 'Neutral'
    elif score <= 0.80:
        return 'Positive'
    else:
        return 'Very Positive'


def _extract_keywords(text: str, top_n: int = 5,
                      min_len: int = 2) -> list[str]:
    """
    使用 jieba 分词 + TF-IDF 提取情绪关键词。

    参数:
        text: 输入文本
        top_n: 返回前 N 个关键词
        min_len: 过滤短于该长度的词
    """
    try:
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(
            text, topK=top_n, withWeight=False, allowPOS=()
        )
        return [kw for kw in keywords if len(kw) >= min_len]
    except Exception:
        # jieba 不可用时的 fallback
        return []


def _polarity_to_ternary(polarity: str) -> str:
    """五级极性 → 三级极性（向后兼容）"""
    if polarity in ('Very Positive', 'Positive'):
        return 'Positive'
    elif polarity in ('Very Negative', 'Negative'):
        return 'Negative'
    return 'Neutral'


# ═══════════════════════════════════════════════════════════
# 三、分析引擎抽象接口
# ═══════════════════════════════════════════════════════════

class AnalyzerBase(ABC):
    """
    情绪分析引擎基类 — 所有引擎必须实现此接口。

    L2/L3/L4 引擎各自覆盖如下方法：
      L2: analyze_single() + analyze_batch()
      L3: analyze_single() 返回含 category/intensity/target 的 EmotionResult
      L4: analyze_single() 返回含 attributions/suggestions 的 EmotionResult
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """引擎版本"""
        ...

    @property
    @abstractmethod
    def phase(self) -> str:
        """分析阶段: 'L2' | 'L3' | 'L4'"""
        ...

    @abstractmethod
    def analyze_single(self, text: str) -> EmotionResult:
        """分析单条文本，返回带 phase 标识的 EmotionResult"""
        ...

    def analyze_batch(self, texts: list) -> list[EmotionResult]:
        """
        批量分析（默认逐条调用，子类可覆盖为向量化实现）。
        """
        return [self.analyze_single(t) for t in tqdm(texts, desc=self.name)]

    def get_capabilities(self) -> dict:
        """返回引擎能力清单"""
        return {
            'name': self.name,
            'version': self.version,
            'phase': self.phase,
            'supports_batch': True,
            'supports_keywords': False,
            'supports_category': False,
            'supports_intensity': False,
            'supports_target': False,
            'supports_attribution': False,
            'supports_confidence': False,
        }


# ═══════════════════════════════════════════════════════════
# 四、L2 引擎 — SnowNLP（当前生产引擎）
# ═══════════════════════════════════════════════════════════

class SnowNLPAnalyzer(AnalyzerBase):
    """
    【L2】基于 SnowNLP 的基础情绪分析引擎。

    产出字段：
      · score       — 综合情绪得分 0~1
      · polarity    — 五级极性（Very Negative ~ Very Positive）
      · keywords    — 情绪关键词（jieba TF-IDF 提取）
      · confidence  — 置信度（基于文本长度归一化）

    优点：轻量(~10MB)、离线、中文友好、无 API 费用
    局限：仅正面/负面分数，无情绪细分类、无对象识别
    """

    def __init__(self, enable_keywords: bool = True):
        self.enable_keywords = enable_keywords

    @property
    def name(self) -> str:
        return 'SnowNLP'

    @property
    def version(self) -> str:
        return '1.0.0-L2'

    @property
    def phase(self) -> str:
        return 'L2'

    def _calc_confidence(self, text: str) -> float:
        """
        基于文本长度计算置信度。

        思路：SnowNLP 本身不提供置信度，用文本长度作为代理——
        文本越长，包含的情感信号越多，结果越可信。
        """
        text_len = len(text.strip())
        if text_len <= 0:
            return 0.0
        if text_len >= 100:
            return 1.0
        return min(1.0, text_len / 100.0)  # 线性缩放，100 字以上满置信

    def analyze_single(self, text: str) -> EmotionResult:
        from snownlp import SnowNLP
        text = str(text).strip()
        if not text:
            return EmotionResult(
                phase='L2', score=0.5, polarity='Neutral',
                confidence=0.0, keywords=[],
            )

        s = SnowNLP(text).sentiments
        score = round(s, 2)
        polarity = _score_to_polarity(score)
        confidence = self._calc_confidence(text)
        keywords = _extract_keywords(text) if self.enable_keywords else []

        return EmotionResult(
            phase='L2',
            score=score,
            polarity=polarity,
            keywords=keywords,
            confidence=round(confidence, 2),
        )

    def analyze_batch(self, texts: list) -> list[EmotionResult]:
        """向量化批量分析 — 比逐条调用快 3~5 倍"""
        from snownlp import SnowNLP

        tqdm.pandas(desc=self.name)
        scores = pd.Series(texts).progress_apply(
            lambda x: round(SnowNLP(str(x).strip()).sentiments, 2)
        )

        results = []
        for i, s in enumerate(scores):
            text = str(texts[i]).strip()
            polarity = _score_to_polarity(s)
            confidence = self._calc_confidence(text)
            keywords = _extract_keywords(text) if self.enable_keywords else []
            results.append(EmotionResult(
                phase='L2',
                score=s,
                polarity=polarity,
                keywords=keywords,
                confidence=round(confidence, 2),
            ))
        return results

    def get_capabilities(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'phase': self.phase,
            'supports_batch': True,
            'supports_keywords': self.enable_keywords,
            'supports_category': False,
            'supports_intensity': False,
            'supports_target': False,
            'supports_attribution': False,
            'supports_confidence': True,
        }


# ═══════════════════════════════════════════════════════════
# 五、L3 引擎 — LLM 语义增强（接口已预留）
# ═══════════════════════════════════════════════════════════

# L3 推荐模型速查
# ┌──────────────┬────────────────┬──────────┬──────────────────────────┐
# │ 模型          │ 提供商          │ 推荐理由   │ API 获取                  │
# ├──────────────┼────────────────┼──────────┼──────────────────────────┤
# │ DeepSeek-V3  │ DeepSeek        │ 性价比高   │ platform.deepseek.com     │
# │ Qwen-Max     │ 阿里云(通义千问) │ 情感分析强 │ dashscope.aliyun.com       │
# │ GLM-4        │ 智谱 AI         │ 开源标杆   │ open.bigmodel.cn           │
# │ ERNIE 4.0    │ 百度            │ NLU 能力强 │ cloud.baidu.com            │
# │ 讯飞星火 4.0  │ 科大讯飞        │ 政务经验   │ xfyun.cn                   │
# └──────────────┴────────────────┴──────────┴──────────────────────────┘


class LLMAnalyzer(AnalyzerBase):
    """
    【L3】LLM 大模型情绪语义增强引擎。

    在 L2 基础上新增产出：
      · category      — 情绪类别（喜悦/愤怒/悲伤/惊讶/厌恶/恐惧/中性）
      · intensity     — 情绪强度 0~1
      · target_type   — 情绪对象类型（设施/环境/服务/文化/事件）
      · target_detail — 情绪对象具体描述
      · confidence    — 由 LLM 提供的置信度

    L3 的定位：
      - 不替代 L2 的 score/polarity，而是在其上叠加语义维度
      - 当 LLM 不可用时，L2 字段依然有效（降级策略）
      - target_type 五分类面向城市规划场景设计，可根据需要扩展

    接入步骤：
      1. 子类化 LLMAnalyzer 或直接配置 api_key/api_url
      2. 实现 _call_api() → 返回 LLM 原始响应 dict
      3. 实现 _parse_response() → dict → EmotionResult（L2+L3字段）
      4. 在 create_analyzer() 中注册
    """

    # ── 情绪类别枚举 ──
    EMOTION_CATEGORIES = [
        '喜悦', '愤怒', '悲伤', '惊讶', '厌恶', '恐惧', '中性',
    ]

    # ── 情绪对象类型枚举（面向城市规划五维框架）──
    TARGET_TYPES = ['设施', '环境', '服务', '文化', '事件']

    def __init__(self, api_key: str = '', api_url: str = '',
                 model: str = 'deepseek-chat'):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    @property
    def name(self) -> str:
        return f'LLM-{self.model}'

    @property
    def version(self) -> str:
        return '1.0.0-L3-dev'

    @property
    def phase(self) -> str:
        return 'L3'

    def _build_prompt(self, text: str) -> str:
        """
        构造 LLM 情绪分析提示词。

        要求 LLM 输出结构化 JSON，包含 L2 和 L3 所需的所有字段。
        """
        return f"""你是一个专业的文本情绪分析系统，面向城市规划与城市治理场景。
请分析以下文本的情绪，输出严格 JSON 格式（不要包含 markdown 代码块标记）：

{{
    "score": 0.0~1.0之间的浮点数（综合情绪得分，0=极端负面，1=极端正面）,
    "polarity": "Very Negative" / "Negative" / "Neutral" / "Positive" / "Very Positive",
    "category": "喜悦" / "愤怒" / "悲伤" / "惊讶" / "厌恶" / "恐惧" / "中性",
    "intensity": 0.0~1.0之间的浮点数（情绪强度，0=微弱，1=强烈）,
    "target_type": "设施" / "环境" / "服务" / "文化" / "事件" / null,
    "target_detail": "情绪对象的具体描述" 或 null,
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "confidence": 0.0~1.0之间的浮点数（你对本次分析的置信度）
}}

target_type 分类说明：
- 设施：建筑、道路、公园、照明、停车、厕所、电梯等物理设施
- 环境：噪音、卫生、绿化、空气、水质、温度、拥挤等环境感知
- 服务：功能、态度、效率、价格、售后、管理等服务体验
- 文化：氛围、历史、艺术、活动、社区关系等文化体验
- 事件：交通事故、施工、庆典、投诉、纠纷等具体事件

待分析文本：
"{text}"
"""

    def _call_api(self, text: str) -> dict:
        """
        调用 LLM API（待实现）。

        预期接入方式示例：
            import requests
            resp = requests.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": [
                    {"role": "user", "content": self._build_prompt(text)}
                ]}
            )
            return resp.json()["choices"][0]["message"]["content"]
        """
        raise NotImplementedError(
            f'LLM API 未接入。\n'
            f'当前模型: {self.model}\n'
            f'推荐接入: DeepSeek-V3 / Qwen-Max / GLM-4 / ERNIE 4.0\n'
            f'预期输入: text="{text[:50]}..."\n'
            f'预期输出: {{"score":0.8, "polarity":"Positive", '
            f'"category":"喜悦", "intensity":0.7, "target_type":"服务", ...}}'
        )

    def _parse_response(self, raw: dict) -> EmotionResult:
        """
        解析 LLM 返回的结构化 JSON → EmotionResult（含 L2 + L3 字段）。

        L3 基于 LLM 重新生成 score/polarity（更精确），
        同时覆盖 L2 的 SnowNLP 结果。
        """
        # ── L2 字段（LLM 版本，通常比 SnowNLP 更准）──
        score = float(raw.get('score', 0.5))
        polarity = raw.get('polarity', _score_to_polarity(score))
        # 确保 polarity 在五级值集合内
        valid_polarities = {'Very Negative', 'Negative', 'Neutral',
                            'Positive', 'Very Positive'}
        if polarity not in valid_polarities:
            polarity = _score_to_polarity(score)

        keywords = raw.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        confidence = float(raw.get('confidence', 0.8))

        # ── L3 字段 ──
        category = raw.get('category')
        intensity = raw.get('intensity')
        if intensity is not None:
            intensity = float(intensity)

        target_type = raw.get('target_type')
        target_detail = raw.get('target_detail')

        return EmotionResult(
            phase='L3',
            # L2 字段（LLM 生成）
            score=score,
            polarity=polarity,
            keywords=keywords,
            confidence=round(float(confidence), 2),
            # L3 新增字段
            category=category,
            intensity=round(intensity, 2) if intensity is not None else None,
            target_type=target_type,
            target_detail=target_detail,
            # 调试
            raw_response=json.dumps(raw, ensure_ascii=False),
        )

    def analyze_single(self, text: str) -> EmotionResult:
        raw = self._call_api(text)
        return self._parse_response(raw)

    def get_capabilities(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'phase': self.phase,
            'supports_batch': True,
            'supports_keywords': True,
            'supports_category': True,
            'supports_intensity': True,
            'supports_target': True,
            'supports_attribution': False,
            'supports_confidence': True,
        }


# ═══════════════════════════════════════════════════════════
# 六、L4 引擎 — 多维归因语料库 + LLM（框架已预留）
# ═══════════════════════════════════════════════════════════

class CorpusAnalyzer(AnalyzerBase):
    """
    【L4】多维归因语料库增强分析引擎。

    在 L3 基础上新增产出：
      · attributions  — 归因列表，每条包含:
          - cause:          情绪原因描述
          - cause_category: 原因类别（设施老化/管理缺位/设计缺陷/…）
          - weight:         该原因的影响权重 0~1
          - evidence:       原文中的支撑证据
      · suggestions   — 面向城市更新/治理的改善建议列表

    L4 的定位：
      - 依赖自研"多维归因语料库"（正在开发中）
      - 语料库提供"情绪→原因"的映射知识
      - LLM 负责自然语言理解和归因推理
      - 不替代 L2/L3，而是在其基础上做深度的因果分析

    与传统情绪分析的区别：
      L2/L3 回答 "情绪是什么"
      L4   回答 "为什么产生这种情绪" + "怎么改善"
    """

    def __init__(self, corpus_path: str = '',
                 api_key: str = '', api_url: str = '',
                 model: str = 'deepseek-chat'):
        self.corpus_path = corpus_path      # 多维归因语料库路径
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self._corpus = None                  # 语料库缓存（延迟加载）

    @property
    def name(self) -> str:
        return f'Corpus-{self.model}'

    @property
    def version(self) -> str:
        return '1.0.0-L4-dev'

    @property
    def phase(self) -> str:
        return 'L4'

    def _load_corpus(self):
        """加载多维归因语料库（待实现）"""
        if self._corpus is not None:
            return self._corpus
        if not self.corpus_path or not os.path.exists(self.corpus_path):
            return None
        # TODO: 加载语料库 → 归因映射表
        # self._corpus = json.load(open(self.corpus_path))
        return self._corpus

    def _build_attribution_prompt(self, text: str, l2_result: EmotionResult,
                                   l3_result: Optional[EmotionResult] = None) -> str:
        """
        构造 L4 归因分析提示词。

        结合 L2 的基础情绪（score/polarity）和 L3 的语义信息（category/target），
        通过语料库知识 + LLM 推理进行归因分析。
        """
        polarity_info = f"情绪极性: {l2_result.polarity}, 得分: {l2_result.score}"
        if l3_result:
            polarity_info += (f"\n情绪类别: {l3_result.category or '未知'}, "
                             f"强度: {l3_result.intensity or '未知'}, "
                             f"对象: {l3_result.target_type or '未知'} - "
                             f"{l3_result.target_detail or '无'}")

        return f"""你是一个面向城市规划的情绪归因分析专家。
基于以下文本和已有情绪分析结果，进行深度的因果归因分析。

已有分析：
{polarity_info}

请输出严格 JSON 格式（不要包含 markdown 代码块标记）：
{{
    "attributions": [
        {{
            "cause": "情绪原因描述",
            "cause_category": "设施老化" / "管理缺位" / "设计缺陷" / "服务失当" / "环境恶化" / "文化冲突" / "突发事件" / "其他",
            "weight": 0.0~1.0之间的浮点数（该原因的影响权重）,
            "evidence": "原文中支撑该归因的片段"
        }}
    ],
    "suggestions": ["改善建议1", "改善建议2", "改善建议3"],
    "urgency": "urgent" / "attention" / "normal" / "low"
}}

分析目标文本：
"{text}"
"""

    def _call_api(self, prompt: str) -> dict:
        """调用 LLM API（待实现，与 L3 共用同一 API 通道）"""
        raise NotImplementedError(
            f'L4 归因分析 API 未接入。\n'
            f'依赖: 自研多维归因语料库 + LLM ({self.model})\n'
            f'语料库路径: {self.corpus_path or "未配置"}'
        )

    def _parse_attribution_response(self, raw: dict) -> dict:
        """解析 L4 归因分析结果"""
        return {
            'attributions': raw.get('attributions', []),
            'suggestions': raw.get('suggestions', []),
            'urgency': raw.get('urgency', 'normal'),
        }

    def analyze_single(self, text: str,
                       l2_result: Optional[EmotionResult] = None,
                       l3_result: Optional[EmotionResult] = None) -> EmotionResult:
        """
        L4 分析 — 在 L2/L3 基础上进行归因。

        理想流程：
          1. L2 (SnowNLP)    → 基础 score + polarity + keywords
          2. L3 (LLM)        → category + intensity + target
          3. L4 (Corpus+LLM) → attributions + suggestions
        """
        prompt = self._build_attribution_prompt(text, l2_result, l3_result)
        raw = self._call_api(prompt)
        parsed = self._parse_attribution_response(raw)

        return EmotionResult(
            phase='L4',
            # 继承 L2
            score=l2_result.score if l2_result else 0.5,
            polarity=l2_result.polarity if l2_result else 'Neutral',
            keywords=l2_result.keywords if l2_result else [],
            confidence=l2_result.confidence if l2_result else 1.0,
            # 继承 L3
            category=l3_result.category if l3_result else None,
            intensity=l3_result.intensity if l3_result else None,
            target_type=l3_result.target_type if l3_result else None,
            target_detail=l3_result.target_detail if l3_result else None,
            # L4 新增
            attributions=parsed.get('attributions'),
            suggestions=parsed.get('suggestions'),
            raw_response=json.dumps(raw, ensure_ascii=False),
        )

    def analyze_single(self, text: str) -> EmotionResult:
        """
        降级模式：无 L2/L3 前置结果时，仅做基础归因。
        生产环境建议使用 pipeline 模式按 L2→L3→L4 顺序调用。
        """
        prompt = self._build_attribution_prompt(text, EmotionResult())
        raw = self._call_api(prompt)
        parsed = self._parse_attribution_response(raw)

        return EmotionResult(
            phase='L4',
            attributions=parsed.get('attributions'),
            suggestions=parsed.get('suggestions'),
            raw_response=json.dumps(raw, ensure_ascii=False),
        )

    def get_capabilities(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'phase': self.phase,
            'supports_batch': True,
            'supports_keywords': True,
            'supports_category': True,
            'supports_intensity': True,
            'supports_target': True,
            'supports_attribution': True,
            'supports_confidence': True,
        }


# ═══════════════════════════════════════════════════════════
# 七、引擎工厂
# ═══════════════════════════════════════════════════════════

def create_analyzer(engine: str = 'snownlp', **kwargs) -> AnalyzerBase:
    """
    引擎工厂 — 统一创建入口。

    用法:
        # L2: SnowNLP 基础分析
        engine = create_analyzer('snownlp')
        engine = create_analyzer('snownlp', enable_keywords=True)

        # L3: LLM 语义增强
        engine = create_analyzer('llm', api_key='sk-xxx', model='deepseek-chat')

        # L4: 语料库归因分析
        engine = create_analyzer('corpus', corpus_path='data/corpus/v1.json',
                                 api_key='sk-xxx')
    """
    engines = {
        'snownlp': SnowNLPAnalyzer,
        'llm': LLMAnalyzer,
        'corpus': CorpusAnalyzer,
    }
    cls = engines.get(engine)
    if cls is None:
        raise ValueError(
            f'未知引擎: {engine}。可用: {list(engines.keys())}\n'
            f'  snownlp → L2 基础情绪分析\n'
            f'  llm     → L3 语义增强分析\n'
            f'  corpus  → L4 多维归因分析'
        )

    # 只传目标引擎接受的参数，避免 TypeError
    valid_params = {
        'snownlp': {'enable_keywords'},
        'llm':     {'api_key', 'api_url', 'model'},
        'corpus':  {'corpus_path', 'api_key', 'api_url', 'model'},
    }
    filtered = {k: v for k, v in kwargs.items()
                if k in valid_params.get(engine, set())}
    return cls(**filtered)


# ═══════════════════════════════════════════════════════════
# 八、统一分析任务入口（供 CLI / GUI / Streamlit 共用）
# ═══════════════════════════════════════════════════════════

def run_analysis_task(
    file_path: str,
    engine_type: str = 'snownlp',
    output_name: str = 'analysis_output',
    api_key: str = '',
    corpus_path: str = '',
    enable_keywords: bool = True,
    full_pipeline: bool = False,
    l3_api_key: str = '',
    l4_api_key: str = '',
) -> dict:
    """
    统一分析任务入口 — 所有 UI（CLI / Tkinter / Streamlit）共用此函数。

    参数:
        file_path:        原始情绪DATA文件（L1）路径
        engine_type:      'snownlp' | 'llm' | 'corpus'
        output_name:      输出文件基础名（不含扩展名）
        api_key:          LLM API Key（L3/L4 需要）
        corpus_path:      L4 语料库路径
        enable_keywords:  是否提取关键词
        full_pipeline:    是否运行全管道 L2→L3→L4
        l3_api_key:       全管道 L3 Key
        l4_api_key:       全管道 L4 Key

    返回:
        {
            'success': bool,
            'df': pd.DataFrame | None,
            'n_points': int,
            'csv_path': str,
            'geojson_path': str,
            'message': str,
            'polarity_stats': dict,   # 五级极性统计
            'score_mean': float,
        }
    """
    result = {
        'success': False,
        'df': None,
        'n_points': 0,
        'csv_path': '',
        'geojson_path': '',
        'message': '',
        'polarity_stats': {},
        'score_mean': 0.0,
    }

    try:
        # 1. 运行管道
        if full_pipeline:
            df = run_full_pipeline(
                file_path,
                l3_api_key=l3_api_key,
                l4_api_key=l4_api_key,
                l4_corpus_path=corpus_path or '',
            )
        else:
            kwargs = {}
            if engine_type == 'snownlp':
                kwargs['enable_keywords'] = enable_keywords
            elif engine_type in ('llm', 'corpus'):
                if api_key:
                    kwargs['api_key'] = api_key
                if corpus_path and engine_type == 'corpus':
                    kwargs['corpus_path'] = corpus_path

            engine = create_analyzer(engine_type, **kwargs)
            df = run_pipeline(file_path, engine)

        if df is None or df.empty:
            result['message'] = '分析失败：无法加载数据或缺少 comments 列'
            return result

        # 2. 导出（文件名含阶段标识）
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        paths = export_results(df, output_name, phase=engine.phase if not full_pipeline else 'L4')
        csv_path = paths['csv_path']
        geojson_path = paths['geojson_path']

        # 3. 统计
        total = len(df)
        polarity_stats = {
            'Very Positive': int((df['polarity'] == 'Very Positive').sum()),
            'Positive':      int((df['polarity'] == 'Positive').sum()),
            'Neutral':       int((df['polarity'] == 'Neutral').sum()),
            'Negative':      int((df['polarity'] == 'Negative').sum()),
            'Very Negative': int((df['polarity'] == 'Very Negative').sum()),
        }

        result.update({
            'success': True,
            'df': df,
            'n_points': total,
            'csv_path': csv_path,
            'geojson_path': geojson_path if os.path.exists(geojson_path) else '',
            'message': f'分析完成！共 {total} 条数据',
            'polarity_stats': polarity_stats,
            'score_mean': round(float(df['score'].mean()), 2),
        })

    except Exception as e:
        result['message'] = f'分析出错: {e}'

    return result


# ═══════════════════════════════════════════════════════════
# 九、数据管道（支持 L2/L3/L4 逐级输出）
# ═══════════════════════════════════════════════════════════

def run_pipeline(file_path: str,
                 engine: AnalyzerBase = None,
                 phase: str = 'L2') -> pd.DataFrame | None:
    """
    一键执行完整分析管道（支持 L2/L3/L4）。

    参数:
        file_path: 原始 CSV/GeoJSON 路径
        engine:    分析引擎（默认 L2 SnowNLP）
        phase:     目标分析阶段 'L2' | 'L3' | 'L4'

    返回:
        包含分析结果的多列 DataFrame，失败返回 None

    L2 输出列: score, polarity, polarity_ternary, keywords, confidence, id_e
    L3 输出列: L2全部 + category, intensity, target_type, target_detail
    L4 输出列: L3全部 + attributions, suggestions
    """
    if engine is None:
        engine = create_analyzer('snownlp')

    # 1. 统一数据加载
    data = load_emotion_data(file_path)
    if not data:
        _safe_print(f'无法加载: {file_path}')
        return None

    df = data['df']
    _safe_print(f'[LOAD] 加载: {data["n_points"]} 条')

    # 2. 分析
    texts = df['comments'].tolist() if 'comments' in df.columns else []
    if not texts:
        _safe_print('[WARN] 无评论文本列')
        return None

    _safe_print(f'[{engine.phase}] {engine.name} v{engine.version} 分析中...')
    results = engine.analyze_batch(texts)

    # 3. 合并 L2 基础字段
    df['score'] = [r.score for r in results]
    df['polarity'] = [r.polarity for r in results]
    df['polarity_ternary'] = [_polarity_to_ternary(r.polarity) for r in results]
    df['keywords'] = [','.join(r.keywords) if r.keywords else '' for r in results]
    df['confidence'] = [r.confidence for r in results]

    # 4. 合并 L3 增强字段（如果引擎产出）
    if any(r.category is not None for r in results):
        df['category'] = [r.category or '' for r in results]
        df['intensity'] = [r.intensity if r.intensity is not None else np.nan
                          for r in results]
        df['target_type'] = [r.target_type or '' for r in results]
        df['target_detail'] = [r.target_detail or '' for r in results]

    # 5. 合并 L4 归因字段（如果引擎产出）
    if any(r.attributions is not None for r in results):
        df['attributions'] = [
            json.dumps(r.attributions, ensure_ascii=False)
            if r.attributions else ''
            for r in results
        ]
        df['suggestions'] = [
            json.dumps(r.suggestions, ensure_ascii=False)
            if r.suggestions else ''
            for r in results
        ]

    # 6. 生成 ID
    df['id_e'] = 'e' + (df.index + 1).astype(str).str.zfill(4)

    # 7. 坐标处理
    for col in ['lon', 'lat']:
        if col in df.columns:
            df[col] = df[col].astype(float).round(4)

    # 8. 统计概览
    _safe_print(f'\n[OK] 分析完成: {len(df)} 条')
    _safe_print(f'  --- 五级极性分布:')
    polarity_order = ['Very Negative', 'Negative', 'Neutral',
                      'Positive', 'Very Positive']
    for pol in polarity_order:
        count = (df['polarity'] == pol).sum()
        if count > 0:
            _safe_print(f'   {pol:16s} {count:5d} 条 ({count/len(df)*100:4.1f}%)')

    # 城市治理视角的统计
    actionable = sum(1 for r in results if r.is_actionable())
    benchmark = sum(1 for r in results if r.is_benchmark())
    _safe_print(f'\n  --- 城市治理视角:')
    _safe_print(f'   需干预项 (Negative + Very Negative): {actionable} 条')
    _safe_print(f'   标杆项   (Very Positive):              {benchmark} 条')

    return df


def export_results(df: pd.DataFrame, base_name: str,
                   output_dir: str = PROCESSED_DIR,
                   phase: str = 'L2') -> dict:
    """
    导出分析结果，文件名含阶段标识。

    参数:
        df:         分析结果 DataFrame
        base_name:  基础文件名（不含扩展名和阶段标识）
        output_dir: 输出目录
        phase:      分析阶段 'L2' | 'L3' | 'L4'

    返回:
        {'csv_path': str, 'geojson_path': str}
    """
    paths = {'csv_path': '', 'geojson_path': ''}

    # CSV
    csv_path = os.path.join(output_dir, f'{base_name}_{phase}_result_csv.csv')
    export_to_csv(df, csv_path)
    paths['csv_path'] = csv_path

    # GeoJSON（需要坐标列）
    if 'lon' in df.columns and 'lat' in df.columns:
        geojson_path = os.path.join(output_dir, f'{base_name}_{phase}_result_geojson.geojson')
        export_to_geojson(df, geojson_path)
        paths['geojson_path'] = geojson_path

    return paths


# ═══════════════════════════════════════════════════════════
# 九、多级管道（L2→L3→L4 顺序执行）
# ═══════════════════════════════════════════════════════════

def run_full_pipeline(file_path: str,
                      l3_api_key: str = '',
                      l4_api_key: str = '',
                      l4_corpus_path: str = '') -> pd.DataFrame | None:
    """
    L2→L3→L4 全管道顺序执行。

    流程:
      1. L2 SnowNLP: 所有文本 → 基础 score/polarity/keywords
      2. L3 LLM:     负面文本（Negative/Very Negative）→ 细粒度语义增强
                     正面/中性文本保留 L2 结果（节省 API 调用）
      3. L4 Corpus:  负面+需归因文本 → 因果归因 + 改善建议

    参数:
        file_path:      原始数据路径
        l3_api_key:     L3 LLM API Key（为空则跳过 L3）
        l4_api_key:     L4 LLM API Key（为空则跳过 L4）
        l4_corpus_path: 多维归因语料库路径
    """
    # L2
    engine_l2 = create_analyzer('snownlp')
    df = run_pipeline(file_path, engine_l2, phase='L2')
    if df is None:
        return None

    # L3（仅对负面文本调用 LLM，节省成本）
    if l3_api_key:
        _safe_print('\n── L3 LLM 语义增强 ──')
        engine_l3 = create_analyzer('llm', api_key=l3_api_key)
        neg_mask = df['polarity'].isin(['Negative', 'Very Negative'])
        neg_texts = df.loc[neg_mask, 'comments'].tolist()
        if neg_texts:
            l3_results = engine_l3.analyze_batch(neg_texts)
            for col in ['category', 'intensity', 'target_type', 'target_detail']:
                df.loc[neg_mask, col] = [
                    getattr(r, col, '') or '' for r in l3_results
                ]
            _safe_print(f'   L3 增强 {len(neg_texts)} 条负面文本')
        else:
            _safe_print('   无负面文本，跳过 L3')

    # L4（对需干预的文本进行归因）
    if l4_api_key:
        _safe_print('\n── L4 多维归因分析 ──')
        engine_l4 = create_analyzer('corpus', api_key=l4_api_key,
                                     corpus_path=l4_corpus_path)
        actionable_mask = df['polarity'].isin(['Negative', 'Very Negative'])
        actionable_texts = df.loc[actionable_mask, 'comments'].tolist()
        if actionable_texts:
            l4_results = engine_l4.analyze_batch(actionable_texts)
            df.loc[actionable_mask, 'attributions'] = [
                json.dumps(r.attributions, ensure_ascii=False)
                if r.attributions else ''
                for r in l4_results
            ]
            df.loc[actionable_mask, 'suggestions'] = [
                json.dumps(r.suggestions, ensure_ascii=False)
                if r.suggestions else ''
                for r in l4_results
            ]
            _safe_print(f'   L4 归因 {len(actionable_texts)} 条需干预文本')
        else:
            _safe_print('   无需归因文本，跳过 L4')

    return df


# ═══════════════════════════════════════════════════════════
# 十、命令行入口（保持向后兼容）
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 默认使用 L2 SnowNLP
    engine = create_analyzer('snownlp')
    _safe_print(f'引擎: {engine.name} v{engine.version} [{engine.phase}]')
    _safe_print(f'能力: {json.dumps(engine.get_capabilities(), ensure_ascii=False)}')

    df = run_pipeline('data/raw/test_0609_1.csv', engine)
    if df is not None and not df.empty:
        export_results(df, 'emotion_analysis_output')
        _safe_print('\n[OK] 全流程完成！')
