"""LLM 韧性（retry + fallback）单测 —— chat_with_fallback 编排逻辑。

monkeypatch LLMClient → _FakeLLMClient（按调用序号消费 _fake_behaviors 行为），
不依赖真实网络/httpx，专注测 retry / 流中途断 / provider 链编排。
行为 _gen(...) 是 generator：依次 yield chunks；遇 BaseException 则 raise
（模拟 LLMClient.chat 已把 httpx 错误转成 LLMError 后的效果）。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from ai_qa import llm
from ai_qa.llm import LLMError, chat_with_fallback, _resolve_providers, MAX_RETRIES


_fake_behaviors = []   # 每次 LLMClient.chat 调用消费一个行为（generator）


def _gen(*items):
    """生成器：依次 yield chunks；遇 BaseException 则 raise。"""
    for it in items:
        if isinstance(it, BaseException):
            raise it
        yield it


class _FakeLLMClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    def chat(self, messages, **kwargs):
        yield from _fake_behaviors.pop(0)


@pytest.fixture(autouse=True)
def _setup(monkeypatch):
    _fake_behaviors.clear()
    monkeypatch.setattr(llm, 'LLMClient', _FakeLLMClient)
    monkeypatch.setattr(llm.time, 'sleep', lambda s: None)   # 跳过退避（否则测试慢 ~3s）
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'sk-test')


def test_retry_then_success():
    """pre-stream 网络错 → 重试 → 成功。"""
    _fake_behaviors[:] = [_gen(LLMError('net', status_code=None)), _gen(('content', 'hi'))]
    chunks = list(chat_with_fallback([{'role': 'user', 'content': 'q'}], tier='pro', stream=True, with_reason=True))
    assert chunks == [('content', 'hi')]


def test_500_then_success():
    """pre-stream HTTP 500 → 重试 → 成功。"""
    _fake_behaviors[:] = [_gen(LLMError('500', status_code=500)), _gen(('content', 'ok'))]
    chunks = list(chat_with_fallback([{'role': 'user', 'content': 'q'}], tier='pro'))
    assert chunks == [('content', 'ok')]


def test_401_no_retry():
    """401 不可重试 → 不重拨、无下一家（Commit1 单 provider）→ 直接抛。"""
    _fake_behaviors[:] = [_gen(LLMError('401', status_code=401)), _gen(('content', 'should-not-reach'))]
    with pytest.raises(LLMError) as ei:
        list(chat_with_fallback([{'role': 'user', 'content': 'q'}], tier='pro'))
    assert ei.value.status_code == 401
    assert len(_fake_behaviors) == 1   # 只消费 1 个（没重试、没换家）


def test_all_retries_exhausted():
    """单 provider 重试 MAX_RETRIES 次全 pre-stream 失败 → 抛 last_err。"""
    _fake_behaviors[:] = [_gen(LLMError('net')) for _ in range(MAX_RETRIES)]
    with pytest.raises(LLMError):
        list(chat_with_fallback([{'role': 'user', 'content': 'q'}], tier='pro'))
    assert len(_fake_behaviors) == 0


def test_midstream_no_retry():
    """首 chunk 后断（started=True）→ 不重试、不换家 → 断前 chunk 保留、抛错。"""
    _fake_behaviors[:] = [_gen(('content', 'partial'), LLMError('mid', status_code=None)),
                          _gen(('content', 'should-not-reach'))]
    out = []
    with pytest.raises(LLMError):
        for c in chat_with_fallback([{'role': 'user', 'content': 'q'}], tier='pro'):
            out.append(c)
    assert out == [('content', 'partial')]
    assert len(_fake_behaviors) == 1   # 没重试（剩 1 个未消费）


def test_single_provider_backward_compat(monkeypatch):
    """仅配 DEEPSEEK_API_KEY → provider 链长度=1（向后兼容，行为同今天）；没 key → 空。"""
    provs = _resolve_providers('pro')
    assert len(provs) == 1 and provs[0].name == 'deepseek'
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    assert _resolve_providers('pro') == []


def test_no_provider_raises(monkeypatch):
    """无任何 provider key → 明确报错（提示配 .env）。"""
    monkeypatch.setattr(llm, '_resolve_providers', lambda tier='pro': [])
    with pytest.raises(LLMError) as ei:
        list(chat_with_fallback([{'role': 'user', 'content': 'q'}], tier='pro'))
    assert '无可用' in str(ei.value)


def _prov(name):
    return llm.Provider(name=name, base_url='http://' + name, api_key='k-' + name,
                        model_pro='mp', model_flash='mf')


def test_401_fallback_to_next_provider(monkeypatch):
    """provider A 401（不可重试）→ 换 provider B 成功（fallback 换家）。"""
    monkeypatch.setattr(llm, '_resolve_providers', lambda tier='pro': [_prov('A'), _prov('B')])
    _fake_behaviors[:] = [_gen(LLMError('401', status_code=401)), _gen(('content', 'from-B'))]
    chunks = list(chat_with_fallback([{'role': 'user', 'content': 'q'}], tier='pro'))
    assert chunks == [('content', 'from-B')]
    assert len(_fake_behaviors) == 0


def test_multi_provider_all_fail(monkeypatch):
    """两家 provider 各重试 MAX_RETRIES 次全失败 → 抛 last_err。"""
    monkeypatch.setattr(llm, '_resolve_providers', lambda tier='pro': [_prov('A'), _prov('B')])
    _fake_behaviors[:] = [_gen(LLMError('net')) for _ in range(MAX_RETRIES * 2)]
    with pytest.raises(LLMError):
        list(chat_with_fallback([{'role': 'user', 'content': 'q'}], tier='pro'))
    assert len(_fake_behaviors) == 0


def test_resolve_providers_multi(monkeypatch):
    """配齐三家 key → 链长度=3，顺序 deepseek → ark → iflytek。"""
    monkeypatch.setenv('ARK_API_KEY', 'ark-x')
    monkeypatch.setenv('IFLYTEK_API_KEY', 'iflytek-x')
    names = [p.name for p in _resolve_providers('pro')]
    assert names == ['deepseek', 'ark', 'iflytek']
