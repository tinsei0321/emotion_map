"""
测试情绪分析引擎 — L2 SnowNLP 核心管道
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCRIPT.emotion_analysis_v1 import (
    SnowNLPAnalyzer,
    create_analyzer,
    _score_to_polarity,
    _extract_keywords,
    _polarity_to_ternary,
    EmotionResult,
    run_analysis_task,
    run_pipeline,
    export_results,
    run_full_pipeline,
)


class TestScoreToPolarity:
    """五级极性映射测试。"""

    def test_very_negative(self):
        assert _score_to_polarity(0.0) == 'Very Negative'
        assert _score_to_polarity(0.1) == 'Very Negative'
        assert _score_to_polarity(0.2) == 'Very Negative'

    def test_negative(self):
        assert _score_to_polarity(0.21) == 'Negative'
        assert _score_to_polarity(0.35) == 'Negative'
        assert _score_to_polarity(0.4) == 'Negative'

    def test_neutral(self):
        assert _score_to_polarity(0.41) == 'Neutral'
        assert _score_to_polarity(0.5) == 'Neutral'
        assert _score_to_polarity(0.6) == 'Neutral'

    def test_positive(self):
        assert _score_to_polarity(0.61) == 'Positive'
        assert _score_to_polarity(0.75) == 'Positive'
        assert _score_to_polarity(0.8) == 'Positive'

    def test_very_positive(self):
        assert _score_to_polarity(0.81) == 'Very Positive'
        assert _score_to_polarity(0.95) == 'Very Positive'
        assert _score_to_polarity(1.0) == 'Very Positive'


class TestPolarityTernary:
    """五级→三级极性兼容转换。"""

    def test_positive_group(self):
        assert _polarity_to_ternary('Very Positive') == 'Positive'
        assert _polarity_to_ternary('Positive') == 'Positive'

    def test_negative_group(self):
        assert _polarity_to_ternary('Very Negative') == 'Negative'
        assert _polarity_to_ternary('Negative') == 'Negative'

    def test_neutral(self):
        assert _polarity_to_ternary('Neutral') == 'Neutral'


class TestEmotionResult:
    """EmotionResult 数据结构测试。"""

    def test_default_values(self):
        r = EmotionResult()
        assert r.phase == 'L2'
        assert r.score == 0.5
        assert r.polarity == 'Neutral'
        assert r.keywords == []

    def test_to_dict(self):
        r = EmotionResult(score=0.8, polarity='Positive', keywords=['好', '美'])
        d = r.to_dict()
        assert d['score'] == 0.8
        assert d['polarity'] == 'Positive'
        assert 'target' not in d  # 废弃字段不输出
        assert 'category' not in d  # None 字段不输出

    def test_get_polarity_level(self):
        assert EmotionResult(polarity='Very Negative').get_polarity_level() == -2
        assert EmotionResult(polarity='Negative').get_polarity_level() == -1
        assert EmotionResult(polarity='Neutral').get_polarity_level() == 0
        assert EmotionResult(polarity='Positive').get_polarity_level() == 1
        assert EmotionResult(polarity='Very Positive').get_polarity_level() == 2

    def test_is_actionable(self):
        assert EmotionResult(polarity='Very Negative').is_actionable()
        assert EmotionResult(polarity='Negative').is_actionable()
        assert not EmotionResult(polarity='Neutral').is_actionable()
        assert not EmotionResult(polarity='Positive').is_actionable()

    def test_is_benchmark(self):
        assert EmotionResult(polarity='Very Positive').is_benchmark()
        assert not EmotionResult(polarity='Positive').is_benchmark()
        assert not EmotionResult(polarity='Neutral').is_benchmark()


class TestSnowNLPAnalyzer:
    """SnowNLP L2 引擎测试。"""

    def setup_method(self):
        self.engine = SnowNLPAnalyzer(enable_keywords=True)

    def test_engine_properties(self):
        assert self.engine.name == 'SnowNLP'
        assert self.engine.phase == 'L2'
        assert 'L2' in self.engine.version

    def test_empty_text(self):
        result = self.engine.analyze_single('')
        assert result.score == 0.5
        assert result.polarity == 'Neutral'
        assert result.confidence == 0.0

    def test_positive_text(self):
        result = self.engine.analyze_single('这个公园太美了，环境很好，散步很舒服')
        # SnowNLP 对正面文本应给出高分
        assert result.score > 0.5
        assert result.polarity in ('Positive', 'Very Positive')

    def test_negative_text(self):
        result = self.engine.analyze_single('垃圾成堆，臭气熏天，投诉也没人管')
        # SnowNLP 对负面文本应给出低分
        assert result.score < 0.5
        assert result.polarity in ('Negative', 'Very Negative')

    def test_keywords_enabled(self):
        result = self.engine.analyze_single('公园环境优美绿化好')
        assert len(result.keywords) > 0
        assert isinstance(result.keywords[0], str)

    def test_keywords_disabled(self):
        engine = SnowNLPAnalyzer(enable_keywords=False)
        result = engine.analyze_single('公园环境优美绿化好')
        assert result.keywords == []

    def test_batch_analysis(self, sample_texts):
        texts = [t for t, _ in sample_texts if t]  # 排除空文本
        results = self.engine.analyze_batch(texts)
        assert len(results) == len(texts)
        for r in results:
            assert isinstance(r, EmotionResult)
            assert r.phase == 'L2'

    def test_capabilities(self):
        caps = self.engine.get_capabilities()
        assert caps['supports_batch'] is True
        assert caps['supports_keywords'] is True
        assert caps['supports_category'] is True  # L2 规则分类 (emotion_type)，已支持


class TestCreateAnalyzer:
    """引擎工厂测试。"""

    def test_create_snownlp(self):
        engine = create_analyzer('snownlp')
        assert engine.name == 'SnowNLP'
        assert engine.phase == 'L2'

    def test_create_llm(self):
        engine = create_analyzer('llm', api_key='test-key')
        assert 'LLM' in engine.name
        assert engine.phase == 'L3'

    def test_create_corpus(self):
        engine = create_analyzer('corpus', api_key='test-key')
        assert 'Corpus' in engine.name
        assert engine.phase == 'L4'

    def test_unknown_engine(self):
        with pytest.raises(ValueError, match='未知引擎'):
            create_analyzer('unknown_engine')


class TestKeywords:
    """关键词提取测试。"""

    def test_basic_extraction(self):
        keywords = _extract_keywords('公园环境优美，绿化很好，适合散步跑步')
        assert len(keywords) > 0
        # 短词应被过滤
        for kw in keywords:
            assert len(kw) >= 2

    def test_empty_text(self):
        keywords = _extract_keywords('')
        assert keywords == []

    def test_short_text(self):
        keywords = _extract_keywords('好')
        # 单字应被过滤
        assert keywords == []
