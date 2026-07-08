"""AI 问答自成长知识闭环路由 /api/v1/aiqa/*（挂载到 api/main.py，prefix=/api/v1）。

两类端点：
- GET  /aiqa/wisdom  → 返回 L2 wisdom_text（前端 buildContext 拼进 ctx.context，注入答问 prompt）。
- POST /aiqa/episode → 记一条 L3 情境日志（harness 末尾 fire-and-forget，失败静默不阻塞交付）。

三层知识闭环：L1=MANIFESTO（稳定）/ L2=ai_qa/wisdom.py（人审策展·本路由读出）/
L3=ai_qa/episode.py 写 DATA/ai_qa/episodes.jsonl（被 ai_qa/consolidate.py 周期挖掘提议 L2）。

挂载：api/main.py `app.include_router(aiqa_router, prefix='/api/v1')` → 总路径 /api/v1/aiqa/*。
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ai_qa.wisdom import wisdom_text, retrieve_wisdom
from ai_qa.episode import log_episode

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
