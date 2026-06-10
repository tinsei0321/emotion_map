"""
情绪语义分析引擎 v1.0 — Emotion Analysis Engine
══════════════════════════════════════════════════════════════
设计原则：
  1. 分析引擎可插拔 — SnowNLP 今日，大模型明日，同一接口
  2. 向量化管道 — 批量处理，避免逐行循环
  3. 细粒度扩展 — 预留多维度分析接口（情绪类别/强度/对象）
  4. 独立模块 — 不依赖 Streamlit，可被任何应用调用

未来接入溯佰科大模型时，只需实现 AnalyzerBase 接口即可。
══════════════════════════════════════════════════════════════
"""
import os, re, json, sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import numpy as np
from tqdm import tqdm

# 确保可导入 core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import SCORE_POSITIVE, SCORE_NEGATIVE, PROCESSED_DIR
from core.data_loader import load_emotion_data
from core.export import export_to_csv, export_to_geojson

# ═══════════════════════════════════════════════════════════
# 一、数据结构定义
# ═══════════════════════════════════════════════════════════

@dataclass
class EmotionResult:
    """单条情绪分析结果"""
    score: float                          # 综合情绪得分 0~1
    polarity: str                         # 极性：Positive / Neutral / Negative
    confidence: float = 1.0               # 置信度（大模型可提供）
    # -- 未来扩展字段（LLM 可填充） --
    category: Optional[str] = None        # 情绪类别：喜悦/愤怒/悲伤/惊讶...
    intensity: Optional[float] = None     # 情绪强度 0~1
    target: Optional[str] = None          # 情绪对象：POI/服务/环境...
    keywords: list = field(default_factory=list)  # 情绪关键词
    raw_response: Optional[str] = None    # 原始模型返回（调试用）

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class AnalysisReport:
    """批量分析报告"""
    results: list                        # EmotionResult 列表
    summary: dict                        # 统计摘要
    meta: dict                           # 元信息（引擎名、耗时等）


# ═══════════════════════════════════════════════════════════
# 二、分析引擎抽象接口
# ═══════════════════════════════════════════════════════════

class AnalyzerBase(ABC):
    """情绪分析引擎基类 — 所有引擎必须实现此接口"""

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

    @abstractmethod
    def analyze_single(self, text: str) -> EmotionResult:
        """分析单条文本"""
        ...

    def analyze_batch(self, texts: list) -> list[EmotionResult]:
        """
        批量分析（默认逐条调用，子类可覆盖为向量化实现）。

        参数:
            texts: 文本列表

        返回:
            EmotionResult 列表
        """
        return [self.analyze_single(t) for t in tqdm(texts, desc=self.name)]

    def get_capabilities(self) -> dict:
        """返回引擎能力清单"""
        return {
            'name': self.name,
            'version': self.version,
            'supports_batch': True,
            'supports_category': False,
            'supports_intensity': False,
            'supports_target': False,
            'supports_confidence': False,
        }


# ═══════════════════════════════════════════════════════════
# 三、SnowNLP 引擎实现（当前生产引擎）
# ═══════════════════════════════════════════════════════════

class SnowNLPAnalyzer(AnalyzerBase):
    """
    基于 SnowNLP 的情绪分析引擎。
    优点：轻量、离线、中文友好
    局限：粒度粗（仅正面/负面分数），无情绪分类
    """

    def __init__(self):
        self.pos_thresh = SCORE_POSITIVE
        self.neg_thresh = SCORE_NEGATIVE

    @property
    def name(self) -> str:
        return 'SnowNLP'

    @property
    def version(self) -> str:
        from snownlp import SnowNLP
        return 'snownlp-0.12'

    def analyze_single(self, text: str) -> EmotionResult:
        from snownlp import SnowNLP
        text = str(text).strip()
        if not text:
            return EmotionResult(score=0.5, polarity='Neutral', confidence=0.0)

        s = SnowNLP(text).sentiments
        score = round(s, 4)

        if score >= self.pos_thresh:
            polarity = 'Positive'
        elif score <= self.neg_thresh:
            polarity = 'Negative'
        else:
            polarity = 'Neutral'

        return EmotionResult(score=score, polarity=polarity)

    def analyze_batch(self, texts: list) -> list[EmotionResult]:
        """向量化批量分析 — 比逐条调用快 3-5 倍"""
        from snownlp import SnowNLP
        tqdm.pandas(desc=self.name)
        scores = pd.Series(texts).progress_apply(
            lambda x: round(SnowNLP(str(x).strip()).sentiments, 4)
        )
        results = []
        for s in scores:
            if s >= self.pos_thresh:
                pol = 'Positive'
            elif s <= self.neg_thresh:
                pol = 'Negative'
            else:
                pol = 'Neutral'
            results.append(EmotionResult(score=s, polarity=pol))
        return results

    def get_capabilities(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'supports_batch': True,
            'supports_category': False,
            'supports_intensity': False,
            'supports_target': False,
            'supports_confidence': False,
        }


# ═══════════════════════════════════════════════════════════
# 四、未来 LLM 引擎接口（溯佰科大模型接入模板）
# ═══════════════════════════════════════════════════════════

class LLMAnalyzer(AnalyzerBase):
    """
    LLM 大模型情绪分析引擎（占位 / 模板）。

    接入溯佰科时，只需：
    1. 实现 _call_api() 方法
    2. 实现 _parse_response() 方法
    3. 在工厂函数中注册
    """

    def __init__(self, api_key: str = '', api_url: str = '',
                 model: str = 'shuboke-v1'):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    @property
    def name(self) -> str:
        return f'LLM-{self.model}'

    @property
    def version(self) -> str:
        return '0.1.0-dev'

    def _call_api(self, text: str) -> dict:
        """调用 LLM API（待实现）"""
        raise NotImplementedError(
            'LLM API 未接入。'
            '未来在此实现 HTTP 请求 → 溯佰科 / 其他大模型。'
            f'预期输入: text="{text[:30]}..."'
            '预期输出: {"score":0.8, "polarity":"Positive", '
            '"category":"喜悦", "intensity":0.7, "target":"服务"}'
        )

    def _parse_response(self, raw: dict) -> EmotionResult:
        """解析 LLM 返回的结构化 JSON"""
        return EmotionResult(
            score=float(raw.get('score', 0.5)),
            polarity=raw.get('polarity', 'Neutral'),
            confidence=float(raw.get('confidence', 0.8)),
            category=raw.get('category'),
            intensity=raw.get('intensity'),
            target=raw.get('target'),
            keywords=raw.get('keywords', []),
            raw_response=json.dumps(raw, ensure_ascii=False),
        )

    def analyze_single(self, text: str) -> EmotionResult:
        raw = self._call_api(text)
        return self._parse_response(raw)

    def get_capabilities(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'supports_batch': True,
            'supports_category': True,
            'supports_intensity': True,
            'supports_target': True,
            'supports_confidence': True,
        }


# ═══════════════════════════════════════════════════════════
# 五、引擎工厂
# ═══════════════════════════════════════════════════════════

def create_analyzer(engine: str = 'snownlp', **kwargs) -> AnalyzerBase:
    """
    引擎工厂 — 统一创建入口。

    用法:
        engine = create_analyzer('snownlp')
        engine = create_analyzer('llm', api_key='...', model='shuboke-v1')

    未来扩展:
        engine = create_analyzer('custom', ...)   # 自定义引擎
    """
    engines = {
        'snownlp': SnowNLPAnalyzer,
        'llm': LLMAnalyzer,
    }
    cls = engines.get(engine)
    if cls is None:
        raise ValueError(f'未知引擎: {engine}。可用: {list(engines.keys())}')
    return cls(**kwargs)


# ═══════════════════════════════════════════════════════════
# 六、数据管道（基于 core 模块）
# ═══════════════════════════════════════════════════════════

def run_pipeline(file_path: str, engine: AnalyzerBase = None) -> pd.DataFrame | None:
    """
    一键执行完整分析管道。

    参数:
        file_path: 原始 CSV/GeoJSON 路径
        engine: 分析引擎（默认 SnowNLP）

    返回:
        包含 score / polarity 列的 DataFrame，失败返回 None
    """
    if engine is None:
        engine = create_analyzer('snownlp')

    # 1. 统一数据加载（core/data_loader）
    data = load_emotion_data(file_path)
    if not data:
        print(f'无法加载: {file_path}')
        return None

    df = data['df']
    print(f'加载: {data["n_points"]} 条')

    # 2. 分析
    texts = df['comments'].tolist() if 'comments' in df.columns else []
    if not texts:
        print('无评论文本列')
        return None

    results = engine.analyze_batch(texts)

    # 3. 合并结果
    df['score'] = [r.score for r in results]
    df['polarity'] = [r.polarity for r in results]

    # 4. 生成 ID
    df['id_e'] = 'e' + (df.index + 1).astype(str).str.zfill(4)

    # 5. 坐标处理
    for col in ['lon', 'lat']:
        if col in df.columns:
            df[col] = df[col].astype(float).round(4)

    print(f'分析完成: {len(df)} 条')
    print(df['polarity'].value_counts().to_string())

    return df


def export_results(df: pd.DataFrame, base_name: str,
                   output_dir: str = PROCESSED_DIR):
    """导出（使用 core/export）"""
    # CSV
    csv_path = os.path.join(output_dir, f'{base_name}_result_csv.csv')
    export_to_csv(df, csv_path)

    # GeoJSON（需要坐标列）
    if 'lon' in df.columns and 'lat' in df.columns:
        geojson_path = os.path.join(output_dir, f'{base_name}_result_geojson.geojson')
        export_to_geojson(df, geojson_path)


# ═══════════════════════════════════════════════════════════
# 八、命令行入口（保持向后兼容）
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 默认使用 SnowNLP
    engine = create_analyzer('snownlp')

    # 未来切换 LLM 只需改一行:
    # engine = create_analyzer('llm', api_key='xxx', model='shuboke-v1')

    print(f'引擎: {engine.name} v{engine.version}')
    print(f'能力: {engine.get_capabilities()}')

    df = run_pipeline('data/raw/test_0609_1.csv', engine)
    if not df.empty:
        export_results(df, 'test_0609_v1')
