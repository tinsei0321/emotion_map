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
import time
from dataclasses import dataclass
from typing import Iterator, List, Optional

import httpx

from core.tracker import trace_log, trace_warn, trace_error, register_track_id

DEFAULT_BASE_URL = 'https://api.deepseek.com/v1'
MODEL_FLASH = 'deepseek-v4-flash'     # 快速经济（继 chat）
MODEL_PRO = 'deepseek-v4-pro'         # 旗舰推理（继 reasoner，1M 上下文）
DEFAULT_MODEL = MODEL_PRO             # 默认 Pro（用户要求 v4-pro，深度思考）
MODEL_ENV = 'DEEPSEEK_MODEL'          # env 覆盖（优先级最高）
DEFAULT_KEY_ENV = 'DEEPSEEK_API_KEY'

MAX_RETRIES = 3   # 单 provider 内重试次数（指数退避 2**attempt 秒：attempt 0/1/2 → 1/2/4s）

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
    """LLM 调用错误（缺 key / 401 / 网络 / 解析）。
    status_code：HTTP 状态码（None=网络/解析错误，_is_retryable 视为可重试）。"""
    def __init__(self, *args, status_code=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_code = status_code


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
        if stream:
            body['stream_options'] = {'include_usage': True}   # 流式末 chunk 返 usage（容量圆圈用）
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
                                raise LLMError(f'API Key 无效 (401)。检查 {DEFAULT_KEY_ENV}。', status_code=401)
                            raise LLMError(f'LLM HTTP {resp.status_code}: {body_txt}', status_code=resp.status_code)
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
                            usage = obj.get('usage')   # 流式末尾 chunk 含 usage（prompt/completion/total_tokens）
                            if usage and with_reason:
                                yield ('usage', usage)
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, headers=headers, json={**body, 'stream': False})
                    if resp.status_code != 200:
                        raise LLMError(f'LLM HTTP {resp.status_code}: {resp.text[:400]}', status_code=resp.status_code)
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


# ── 韧性层：retry（单 provider 内重拨）+ fallback（provider 链换家）──

@dataclass(frozen=True)
class Provider:
    """单个 LLM 供应商配置（OpenAI 兼容端点）。"""
    name: str
    base_url: str
    api_key: str
    model_pro: str
    model_flash: str


def _resolve_providers(tier: str = 'pro') -> List[Provider]:
    """按 env 解析有序 provider 列表（空 key 跳过）。tier ∈ {'pro','flash'}。
    顺序：DeepSeek（主）→ 火山 Ark（备 1）→ 讯飞 Spark（备 2）。
    向后兼容：仅配 DEEPSEEK_API_KEY 时长度=1，行为同今天。"""
    provs = []
    # 主：DeepSeek（OpenAI 兼容 /v1/chat/completions）
    ds_key = os.environ.get(DEFAULT_KEY_ENV, '')
    if ds_key:
        provs.append(Provider(
            name='deepseek',
            base_url=os.environ.get('DEEPSEEK_BASE_URL', DEFAULT_BASE_URL).rstrip('/'),
            api_key=ds_key,
            model_pro=os.environ.get('DEEPSEEK_MODEL_PRO', MODEL_PRO),
            model_flash=os.environ.get('DEEPSEEK_MODEL_FLASH', MODEL_FLASH),
        ))
    # 备 1：火山引擎 Ark（OpenAI 兼容 /api/v3/chat/completions；model 填 endpoint id 或 doubao 名）
    ark_key = os.environ.get('ARK_API_KEY', '')
    if ark_key:
        provs.append(Provider(
            name='ark',
            base_url=os.environ.get('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3').rstrip('/'),
            api_key=ark_key,
            model_pro=os.environ.get('ARK_MODEL_PRO', 'doubao-pro-32k'),
            model_flash=os.environ.get('ARK_MODEL_FLASH', 'doubao-lite-32k'),
        ))
    # 备 2：讯飞 Spark（OpenAI 兼容 /v1/chat/completions）
    iflytek_key = os.environ.get('IFLYTEK_API_KEY', '')
    if iflytek_key:
        provs.append(Provider(
            name='iflytek',
            base_url=os.environ.get('IFLYTEK_BASE_URL', 'https://spark-api-open.xfyun.cn/v1').rstrip('/'),
            api_key=iflytek_key,
            model_pro=os.environ.get('IFLYTEK_MODEL_PRO', '4.0Ultra'),
            model_flash=os.environ.get('IFLYTEK_MODEL_FLASH', 'generalv3'),
        ))
    return provs


def _tier_of(model: Optional[str]) -> str:
    """模型名/别名 → tier（'pro'/'flash'）。供 chat_with_fallback 选 model_pro/model_flash。"""
    return 'flash' if _resolve_model(model) == MODEL_FLASH else 'pro'


def _is_retryable(err: 'LLMError') -> bool:
    """可重试：网络/解析错误（status_code=None）/ 5xx / 429。4xx 非 429 不可重试（直接换家）。"""
    sc = getattr(err, 'status_code', None)
    return sc is None or sc >= 500 or sc == 429


def chat_with_fallback(messages, tier: str = 'pro', **chat_kwargs) -> Iterator:
    """带 retry + fallback 的 chat 编排（主链路 agent_step/answer/diagnose/revise + 审查员共用）。

    - provider 链顺序试，每家内 retry MAX_RETRIES 次（退避 2**attempt 秒）。
    - 流式边界（关键）：首个 chunk 之前失败 → 可重试 / 可换家；首个 chunk 之后失败 → 直接抛
      （防前端"半截答案突然重来"，让上层 onDegraded 接管）。
    - yield 形状与 LLMClient.chat() 完全一致（(kind, tok)），调用方零改动。
    """
    providers = _resolve_providers(tier)
    if not providers:
        raise LLMError(
            f'无可用 LLM provider（{DEFAULT_KEY_ENV} 等均未配置）。'
            f'在项目根 .env 加 "{DEFAULT_KEY_ENV}=sk-..."（api/main.py 启动自动加载）。'
        )
    last_err = None
    for prov in providers:
        model = prov.model_pro if tier == 'pro' else prov.model_flash
        cli = LLMClient(base_url=prov.base_url, model=model, api_key=prov.api_key)
        for attempt in range(MAX_RETRIES):
            started = False
            try:
                trace_log('MOD_LLM.F_002', f'chat provider={prov.name} model={model} tier={tier} attempt={attempt}')
                for chunk in cli.chat(messages, **chat_kwargs):
                    started = True   # 首 chunk 已出 → 此后失败不重试不换家
                    yield chunk
                return   # 成功走完，结束整个 wrapper
            except LLMError as e:
                last_err = e
                if started:
                    trace_error('MOD_LLM.D_003', f'mid-stream failure provider={prov.name}（不重试不换家）: {e}')
                    raise   # 流中途断：直接抛，让上层降级
                if not _is_retryable(e):
                    trace_warn('MOD_LLM.D_002', f'fallback away provider={prov.name} status={e.status_code}（4xx 不可重试）: {e}')
                    break   # 4xx 等：换下一家 provider
                if attempt < MAX_RETRIES - 1:
                    trace_warn('MOD_LLM.D_001', f'retry provider={prov.name} attempt={attempt + 1}/{MAX_RETRIES} status={e.status_code}: {e}')
                    time.sleep(2 ** attempt)
                else:
                    trace_warn('MOD_LLM.D_002', f'retry exhausted provider={prov.name}，换下一家')
    trace_error('MOD_LLM.F_002', f'all providers exhausted: {last_err}')
    raise last_err or LLMError('所有 LLM provider 均失败')


register_track_id("MOD_LLM.F_002", "chat_with_fallback（retry+fallback 编排，主链路+审查共用）")
register_track_id("MOD_LLM.D_001", "LLM retry 触发（pre-stream 失败，退避后重拨）")
register_track_id("MOD_LLM.D_002", "LLM fallback 切换 provider（重试耗尽或 4xx）")
register_track_id("MOD_LLM.D_003", "LLM 流中途失败（不重试不换家，交上层降级）")
