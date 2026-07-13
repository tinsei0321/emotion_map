"""AI 问答自成长知识闭环路由 /api/v1/aiqa/*（挂载到 api/main.py，prefix=/api/v1）。

两类端点：
- GET  /aiqa/wisdom  → 返回 L2 wisdom_text（前端 buildContext 拼进 ctx.context，注入答问 prompt）。
- POST /aiqa/episode → 记一条 L3 情境日志（harness 末尾 fire-and-forget，失败静默不阻塞交付）。

三层知识闭环：L1=MANIFESTO（稳定）/ L2=ai_qa/wisdom.py（人审策展·本路由读出）/
L3=ai_qa/episode.py 写 DATA/ai_qa/episodes.jsonl（被 ai_qa/consolidate.py 周期挖掘提议 L2）。

挂载：api/main.py `app.include_router(aiqa_router, prefix='/api/v1')` → 总路径 /api/v1/aiqa/*。
"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ai_qa.wisdom import wisdom_text, retrieve_wisdom
from ai_qa.episode import log_episode
from ai_qa.llm import LLMError, chat_with_fallback
from ai_qa.prompts import build_field_infer_prompt
from core.field_dictionary import validate_llm_roles

aiqa_router = APIRouter()


@aiqa_router.get('/aiqa/wisdom')
def get_wisdom(scale: Optional[str] = None, domain: Optional[str] = None):
    """返回 L2 答问智慧文本。

    无参 → 全量（v1 wholesale，L2 人审策展恒小）。
    带 scale/domain → 检索命中条目（v2，L2 > ~12 条时前端 harness 按 diagnose 卡调）。
    """
    entries = None
    if scale or domain:
        doms = [d.strip() for d in domain.split(',')] if domain else None
        entries = retrieve_wisdom(scale, doms)
    return {'wisdom_text': wisdom_text(entries), 'count': len(entries) if entries is not None else None}


class EpisodeIn(BaseModel):
    question: str = ''
    diagnose: Optional[Dict[str, Any]] = None
    final: Optional[str] = None
    review: Optional[Dict[str, Any]] = None
    ok: bool = True
    extra: Optional[Dict[str, Any]] = None


@aiqa_router.post('/aiqa/episode')
def post_episode(ep: EpisodeIn):
    """记一条 L3 episode（append DATA/ai_qa/episodes.jsonl）。失败不抛（返回 ok=False）。"""
    saved = log_episode(
        question=ep.question, diagnose=ep.diagnose, final=ep.final,
        review=ep.review, ok=ep.ok, extra=ep.extra,
    )
    return {'ok': saved}


class ProfileFieldsIn(BaseModel):
    # P2 字段语义推断：fields = 规则字典 miss 的 {field: {dtype, samples, stats}}
    fields: Dict[str, Dict[str, Any]] = {}
    layer_kind: str = ''    # 'point' | 'polygon' | ''（推断辅助）
    context: str = ''       # 可选附加上下文


def _parse_field_json(raw: str) -> dict:
    """容错解析字段推断 JSON；失败返 {}（照 review._parse_review_json 范式）。"""
    if not raw or not raw.strip():
        return {}
    s = raw.find('{')
    e = raw.rfind('}')
    if s < 0 or e < 0 or e <= s:
        return {}
    candidate = raw[s:e + 1]
    try:
        obj = json.loads(candidate)
    except Exception:
        try:
            cleaned = candidate.replace(',}', '}').replace(',]', ']')
            obj = json.loads(cleaned)
        except Exception:
            return {}
    return obj if isinstance(obj, dict) else {}


@aiqa_router.post('/aiqa/profile_fields')
def post_profile_fields(body: ProfileFieldsIn):
    """P2 字段语义推断：为规则字典 miss 的字段调 LLM 选 role（schema matching 兜底）。

    复用 chat_with_fallback（tier='flash' + json_mode，DeepSeek→Ark→讯飞 5.71 韧性链）；
    全 provider 不可用 → 降级 {fields:{}, degraded:True}，不阻塞前端上传/AI（前端只标规则命中字段）。
    返回 {fields: {field:{role,confidence,reason}}}（非法 role 经 validate_llm_roles 置 null）。
    """
    if not body.fields:
        return {'fields': {}}
    sys_prompt = build_field_infer_prompt(body.fields, body.layer_kind, body.context)
    messages = [
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': '请为上述待推断字段输出 JSON。'},
    ]
    try:
        gen = chat_with_fallback(messages, tier='flash', stream=False,
                                 json_mode=True, with_reason=False,
                                 temperature=0.1, max_tokens=1200)
        raw = next(gen)
    except LLMError as e:
        return {'fields': {}, 'degraded': True, 'degraded_reason': str(e)}
    except Exception as e:
        return {'fields': {}, 'degraded': True, 'degraded_reason': f'字段推断异常: {e}'}
    parsed = _parse_field_json(raw)
    validated = validate_llm_roles(parsed)
    return {'fields': validated}
