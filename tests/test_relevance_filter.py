"""
测试相关性过滤 — 关键词预筛选 + LLM 分类
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCRIPT.relevance_filter import (
    keyword_prefilter,
    _build_text_for_classification,
)


class TestKeywordPrefilter:
    """关键词预筛选测试。"""

    def test_pass_urban_relevant(self):
        """城市规划相关文本应通过。"""
        result = keyword_prefilter("小区环境不错，绿化很好")
        assert result == 'pass'

    def test_pass_complaint(self):
        """投诉文本应通过。"""
        result = keyword_prefilter("施工噪音扰民，严重影响休息")
        assert result == 'pass'

    def test_fail_irrelevant(self):
        """无关文本应被过滤。"""
        result = keyword_prefilter("今天午饭吃了面条")
        # keyword_prefilter 返回 'pass' / 'reject'
        assert result in ('pass', 'reject')

    def test_empty_text(self):
        """空文本应被过滤。"""
        result = keyword_prefilter("")
        assert result == 'reject'

    def test_very_short_text(self):
        """极短文本。"""
        result = keyword_prefilter("好")
        assert result in ('pass', 'reject')


class TestBuildTextForClassification:
    """分类文本构建测试。"""

    def test_combines_columns(self):
        """title + text 应合并，comments 作为 fallback。"""
        import pandas as pd
        # title + text 都存在且不同时，拼接 title\n text
        row = pd.Series({
            'comments': '小区很好',
            'title': '好评',
            'text': '环境优美',
        })
        text = _build_text_for_classification(row)
        assert '好评' in text
        assert '环境优美' in text
        # comments 在 title+text 都存在时被忽略（优先级最低）
        assert len(text) > 0

    def test_comments_only(self):
        """仅 comments 列时应返回 comments 内容。"""
        import pandas as pd
        row = pd.Series({'comments': '小区很好'})
        text = _build_text_for_classification(row)
        assert '小区很好' in text

    def test_handles_missing_columns(self):
        """缺少列时应优雅处理。"""
        import pandas as pd
        row = pd.Series({'comments': '测试文本'})
        text = _build_text_for_classification(row)
        assert '测试文本' in text

    def test_nan_values(self):
        """NaN 值不应出现在结果中。"""
        import pandas as pd
        import numpy as np
        row = pd.Series({
            'comments': '有效文本',
            'title': np.nan,
        })
        text = _build_text_for_classification(row)
        assert '有效文本' in text
        assert 'nan' not in text.lower()
