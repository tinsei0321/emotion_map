"""LLM 客户端（provider-agnostic）— DeepSeek V4 时代（2026-07）。

V4 模型（旧 deepseek-chat/deepseek-reasoner 2026-07-24 退役，过渡期映射到 V4 后端——
故旧 ID 不可靠，必须用 V4 新 ID）：
- deepseek-v4-pro   旗舰推理（1M 上下文，继 reasoner）—— 默认，深度思考
- deepseek-v4-flash 快速经济（继 chat）—— 审查员/快速调度

前端思考深度开关发逻辑名 'pro'/'flash'，本模块 _resolve_model 映射到真实 ID（集中管理，
前端不耦合真实 ID）。provider 切换（未来溯佰科）：base_url/model/key 三参 + env。
"""
import os
import json
from typing import Iterator, List, Optional

import httpx

from core.tracker import trace_log, register_track_id

DEFAULT_BASE_URL = 'https://api.deepseek.com/v1'
MODEL_FLASH = 'deepseek-v4-flash'     # 快速经济（继 chat）
MODEL_PRO = 'deepseek-v4-pro'         # 旗舰推理（继 reasoner，1M 上下文）
DEFAULT_MODEL = MODEL_PRO             # 默认 Pro（用户要求 v4-pro，深度思考）
MODEL_ENV = 'DEEPSEEK_MODEL'          # env 覆盖（优先级最高）
DEFAULT_KEY_ENV = 'DEEPSEEK_API_KEY'

# 别名 → 真实 V4 ID。前端思考深度开关发 'pro'/'flash'；旧 ID 兼容（防残留）。
_MODEL_ALIASES = {
    'pro': MODEL_PRO, 'flash': MODEL_FLASH,
    'reasoner': MODEL_PRO, 'chat': MODEL_FLASH,               # 旧逻辑名
    'deepseek-reasoner': MODEL_PRO, 'deepseek-chat': MODEL_FLASH,  # 旧 API ID（2026-07-24 退役）
    'v4-pro': MODEL_PRO, 'v4-flash': MODEL_FLASH,
}


def _resolve_model(model: Optional[str]) -> str:
    """别名 → 真实 V4 ID；None/空 → 默认 Pro。"""
    if not model:
        return DEFAULT_MODEL
    return _MODEL_ALIASES.get(str(model).strip().lower(), str(model).strip())


class LLMError(RuntimeError):
    """LLM 调用错误（缺 key / 401 / 网络 / 解析）。"""


class LLMClient:
    """OpenAI 兼容 chat/completions 客户端（DeepSeek V4 / 任意兼容服务）。"""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None,
                 api_key: Optional[str] = None, timeout: float = 60.0):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip('/')
        self.model = _resolve_model(model or os.environ.get(MODEL_ENV))
        self.api_key = api_key or os.environ.get(DEFAULT_KEY_ENV, '')
        self.timeout = timeout

    def _ensure_key(self):
        if not self.api_key:
            raise LLMError(
                f'未配置 LLM API Key（{DEFAULT_KEY_ENV}）。'
                f'在项目根 .env 加一行 "{DEFAULT_KEY_ENV}=sk-..."（每台机器各一次，.env 在 .gitignore 不进 git；'
                f'api/main.py 启动自动加载），或设系统环境变量，或 LLMClient(api_key=...) 传入。'
            )

    def chat(self, messages: List[dict], stream: bool = True,
             temperature: float = 0.6, max_tokens: int = 4000,
             with_reason: bool = False, json_mode: bool = False) -> Iterator:
        """OpenAI 兼容 chat/completions。

        stream=True → 生成器增量 yield：
            with_reason=False → yield content 字符串；
            with_reason=True  → yield (kind, tok)，kind='reason'(思考链)|'content'(正文)。
                V4 Pro 的 delta.reasoning_content → kind='reason'。
        stream=False → 生成器只 yield 一次完整结果（同上两态）。
        json_mode=True → response_format json_object（agent loop 不用，抑制 reasoning）。
        """
        self._ensure_key()
        url = f'{self.base_url}/chat/completions'
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        body = {'model': self.model, 'messages': messages, 'temperature': temperature,
                'max_tokens': max_tokens, 'stream': stream}
        if json_mode:
            body['response_format'] = {'type': 'json_object'}
        trace_log('MOD_LLM.F_001', f'chat stream={stream} model={self.model} msgs={len(messages)} reason={with_reason} json={json_mode}')
        try:
            if stream:
                with httpx.Client(timeout=self.timeout) as client:
                    with client.stream('POST', url, headers=headers, json=body) as resp:
                        if resp.status_code != 200:
                            body_txt = resp.read().decode('utf-8', 'ignore')[:400]
                            if resp.status_code == 401:
                                raise LLMError(f'API Key 无效 (401)。检查 {DEFAULT_KEY_ENV}。')
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
                            delta = (obj.get('choices') or [{}])[0].get('delta', {})
                            reason = delta.get('reasoning_content')   # V4 Pro 思考链
                            content = delta.get('content')
                            if with_reason:
                                if reason:
                                    yield ('reason', reason)
                                if content:
                                    yield ('content', content)
                            else:
                                if content:
                                    yield content
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, headers=headers, json={**body, 'stream': False})
                    if resp.status_code != 200:
                        raise LLMError(f'LLM HTTP {resp.status_code}: {resp.text[:400]}')
                    obj = resp.json()
                    msg = (obj.get('choices') or [{}])[0].get('message', {})
                    content = msg.get('content', '')
                    if with_reason:
                        reason = msg.get('reasoning_content') or ''
                        if reason:
                            yield ('reason', reason)
                        yield ('content', content)
                    else:
                        yield content
        except httpx.HTTPError as e:
            raise LLMError(f'LLM 网络错误: {e}') from e
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f'LLM 调用异常: {e}') from e


register_track_id("MOD_LLM.F_001", "LLM chat/completions（流式 SSE，provider-agnostic，V4）")
