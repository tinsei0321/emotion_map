"""LLM 客户端（provider-agnostic）— 默认 DeepSeek，未来换溯佰科规划大模型只改 base_url/model/key。

设计：
- 复用 SCRIPT/relevance_filter.py 的 OpenAI 兼容 chat/completions 端点（DeepSeek 原生兼容）。
- 用 httpx（已在 deps）做 SSE 流式，逐 token yield（前端增量渲染）。
- 不引 openai SDK（非必要依赖；与 repo 现有 requests/httpx 风格一致）。
- provider-agnostic：LLMClient(base_url=, model=, api_key=) 一处切换，未来溯佰科改这三参 + key env。

使用：
    cli = LLMClient()                       # 默认 DeepSeek，读 DEEPSEEK_API_KEY
    for tok in cli.chat(messages, stream=True):
        ...  # 增量 token
"""
import os
import json
from typing import Iterator, List, Optional

import httpx

from core.tracker import trace_log, register_track_id

# 默认 DeepSeek（与 relevance_filter.py 同源常量）
DEFAULT_BASE_URL = 'https://api.deepseek.com/v1'
DEFAULT_MODEL = 'deepseek-chat'
DEFAULT_KEY_ENV = 'DEEPSEEK_API_KEY'


class LLMError(RuntimeError):
    """LLM 调用错误（缺 key / 401 / 网络 / 解析）。"""


class LLMClient:
    """OpenAI 兼容 chat/completions 客户端（DeepSeek / 溯佰科 / 任意兼容服务）。

    provider 切换：构造时传 base_url + model + api_key，或子类化覆写默认常量。
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None,
                 api_key: Optional[str] = None, timeout: float = 60.0):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip('/')
        self.model = model or DEFAULT_MODEL
        self.api_key = api_key or os.environ.get(DEFAULT_KEY_ENV, '')
        self.timeout = timeout

    def _ensure_key(self):
        if not self.api_key:
            raise LLMError(
                f'未配置 LLM API Key。设置环境变量 {DEFAULT_KEY_ENV}（DeepSeek），'
                f'或在 LLMClient(api_key=...) 传入。未来接入溯佰科规划大模型时'
                f'改 base_url/model/key 即可。'
            )

    def chat(self, messages: List[dict], stream: bool = True,
             temperature: float = 0.6, max_tokens: int = 1500) -> Iterator[str]:
        """OpenAI 兼容 chat/completions。

        stream=True → 生成器，yield 内容增量（SSE 逐 data: 行解析 choices[0].delta.content）。
        stream=False → 生成器只 yield 一次完整 content（便于复用同一调用点）。
        出错抛 LLMError（route 层捕获转 4xx/5xx）。
        """
        self._ensure_key()
        url = f'{self.base_url}/chat/completions'
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        body = {'model': self.model, 'messages': messages, 'temperature': temperature,
                'max_tokens': max_tokens, 'stream': stream}
        trace_log('MOD_LLM.F_001', f'chat stream={stream} model={self.model} msgs={len(messages)}')
        try:
            if stream:
                with httpx.Client(timeout=self.timeout) as client:
                    with client.stream('POST', url, headers=headers, json=body) as resp:
                        if resp.status_code != 200:
                            body_txt = resp.read().decode('utf-8', 'ignore')[:400]
                            if resp.status_code == 401:
                                raise LLMError(f'API Key 无效 (401)。检查 {DEFAULT_KEY_ENV} 是否正确。')
                            raise LLMError(f'LLM HTTP {resp.status_code}: {body_txt}')
                        for line in resp.iter_lines():
                            if not line or not line.startswith('data:'):
                                continue
                            data = line[5:].strip()
                            if data == '[DONE]':
                                break
                            try:
                                obj = json.loads(data)
                            except json.JSONDecodeError:
                                continue
                            delta = (obj.get('choices') or [{}])[0].get('delta', {}).get('content')
                            if delta:
                                yield delta
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, headers=headers, json={**body, 'stream': False})
                    if resp.status_code != 200:
                        raise LLMError(f'LLM HTTP {resp.status_code}: {resp.text[:400]}')
                    obj = resp.json()
                    yield (obj.get('choices') or [{}])[0].get('message', {}).get('content', '')
        except httpx.HTTPError as e:
            raise LLMError(f'LLM 网络错误: {e}') from e
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f'LLM 调用异常: {e}') from e


register_track_id("MOD_LLM.F_001", "LLM chat/completions（流式 SSE，provider-agnostic）")
