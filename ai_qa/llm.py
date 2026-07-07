"""LLM 客户端（provider-agnostic）— 默认 DeepSeek，未来换溯佰科规划大模型只改 base_url/model/key。

迁自 core/llm_client.py（AI 问答独立成子系统时归入 ai_qa/）。core.tracker 仍是基础设施依赖。

设计：
- 复用 SCRIPT/relevance_filter.py 的 OpenAI 兼容 chat/completions 端点（DeepSeek 原生兼容）。
- 用 httpx（已在 deps）做 SSE 流式，逐 token yield（前端增量渲染）。
- 不引 openai SDK（非必要依赖；与 repo 现有 requests/httpx 风格一致）。
- provider-agnostic：LLMClient(base_url=, model=, api_key=) 一处切换。

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

# 默认 DeepSeek（与 relevance_filter.py 同源常量）。
# 模型策略：Flash=审查员/日常(快/省；deepseek-chat)；Pro=思考+出稿(deepseek-reasoner，带 reasoning_content 思考链)。
# 注：deepseek-chat / deepseek-reasoner 别名映射可能随时间变；用 env DEEPSEEK_MODEL 覆盖最稳。
DEFAULT_BASE_URL = 'https://api.deepseek.com/v1'
MODEL_FLASH = 'deepseek-chat'          # 审查员 / 日常：非思考、流式快、便宜
MODEL_PRO = 'deepseek-reasoner'        # 思考 + 出稿：带 reasoning_content（思考链）
DEFAULT_MODEL = MODEL_PRO              # Harness 默认 Pro（用户要求：默认 DeepSeek v4 pro，带思考链）
MODEL_ENV = 'DEEPSEEK_MODEL'           # env 覆盖（优先级最高）
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
        # 优先级：显式传参 > env DEEPSEEK_MODEL > 默认 Pro
        self.model = model or os.environ.get(MODEL_ENV) or DEFAULT_MODEL
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
             temperature: float = 0.6, max_tokens: int = 2500,
             with_reason: bool = False, json_mode: bool = False) -> Iterator:
        """OpenAI 兼容 chat/completions。

        stream=True → 生成器增量 yield：
            with_reason=False（默认，向后兼容）→ yield content 字符串；
            with_reason=True → yield (kind, tok) 元组，kind='reason'(思考链)|'content'(正文)。
            DeepSeek reasoner(Pro) 的 delta.reasoning_content → kind='reason'。
        stream=False → 生成器只 yield 一次完整结果（同上两态，便于复用同一调用点）。
        json_mode=True → body 增 response_format:{type:'json_object'}（DeepSeek 原生 JSON mode，
            think/review 阶段输出稳定 JSON；勿与 reasoning 同用，JSON 模式下 reasoning 通常为空）。
        出错抛 LLMError（route 层捕获转 4xx/5xx）。
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
                            delta = (obj.get('choices') or [{}])[0].get('delta', {})
                            reason = delta.get('reasoning_content')   # Pro 思考链
                            content = delta.get('content')            # 正文
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


register_track_id("MOD_LLM.F_001", "LLM chat/completions（流式 SSE，provider-agnostic）")
