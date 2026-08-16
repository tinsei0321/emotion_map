# ═══ CB-39 P0-1 · 管道诚实度机器化验收（claude组 反评价建议三断言）═══
#
# 治「能力声称 > 实际能力」三层造假象（CB-38 审计 P0-1）：
#   1. 无 key + full_pipeline → 显式报错（拒绝静默降级·不再产 L2 错标 L4 的文件）
#   2. 有 key + full_pipeline → 导出层标签 = 实际执行层级（df.attrs·≠ 硬编码 'L4'）
#   3. L4 stub 显式 raise NotImplementedError 含「未接入」（占位可检测）
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

from SCRIPT.emotion_analysis_v1 import CorpusAnalyzer, run_analysis_task


def test_full_pipeline_no_key_explicit_error(monkeypatch):
    """断言①：key 全空 → success=False + 显式报错文案（不静默跑 L2 标 L4）。"""
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    r = run_analysis_task(
        file_path='whatever.csv', engine_type='snownlp', full_pipeline=True,
        api_key='', l3_api_key='', l4_api_key='',
    )
    assert r['success'] is False
    assert 'API key' in r['message']
    assert '拒绝静默降级' in r['message']
    assert r.get('csv_path', '') == ''   # 未产出错标文件


def test_full_pipeline_phase_label_honest(monkeypatch):
    """断言②：管道实际跑到 L3 → 导出/结果层标签 = 'L3'（≠ 硬编码 'L4'）。"""
    import SCRIPT.emotion_analysis_v1 as M
    df = pd.DataFrame({
        'comments': ['a', 'b'],
        'polarity': ['Neutral', 'Positive'],
        'score': [0.5, 0.8],
    })
    df.attrs['phase'] = 'L3'   # 管道内实际增强到 L3
    captured = {}
    monkeypatch.setattr(M, 'run_full_pipeline', lambda *a, **k: df)
    monkeypatch.setattr(
        M, 'export_results',
        lambda d, name, phase='L2': (captured.update(phase=phase),
                                     {'csv_path': f'{name}_{phase}_result_csv.csv', 'geojson_path': ''})[1],
    )
    r = M.run_analysis_task(
        file_path='x.csv', engine_type='snownlp', full_pipeline=True,
        api_key='sk-test', l3_api_key='sk-test',
    )
    assert r['success'] is True
    assert captured['phase'] == 'L3'
    assert r['phase'] == 'L3'
    assert 'L4' not in r['csv_path']


def test_l4_stub_explicit_not_implemented():
    """断言③：L4 空壳显式 raise + 文案含「未接入」（占位可检测·非静默假跑）。"""
    eng = CorpusAnalyzer(api_key='sk-x')
    with pytest.raises(NotImplementedError, match='未接入'):
        eng._call_api('ping')
