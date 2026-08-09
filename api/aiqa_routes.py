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

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.tracker import track, register_track_id
from ai_qa.wisdom import wisdom_text, retrieve_wisdom
from ai_qa.episode import log_episode
from ai_qa.llm import LLMError, chat_with_fallback, search_chat

register_track_id('MOD_AIQA.F_017', 'post_rag_search（RAG 知识检索端点·开放语义·返回 Top-K + dim_counts）')
from ai_qa.prompts import build_field_infer_prompt, build_deep_attribution_prompt
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
    defense: Optional[Dict[str, Any]] = None   # CB-09 D024：质量防线结果（取代旧 review）
    ok: bool = True
    extra: Optional[Dict[str, Any]] = None
    capsule_clicked: Optional[str] = None   # CB-09 D034：用户点击的胶囊 skill（Pro 排序自我成长偏好信号·5.239）


class SearchIn(BaseModel):
    question: str = ''


@aiqa_router.post('/aiqa/search')
def post_search(body: SearchIn):
    """G6b 联网搜索（纯问答大问题/聚焦问题·DeepSeek Responses API web_search）。

    前端 general 短路命中 SEARCH_KW → 调本端点 → 返 {answer, sources}（answer=模型综合回答·sources=引用）。
    失败抛 502（前端 try/catch fallback 原 finalStep·不阻塞回答）。
    """
    if not body.question.strip():
        return {'answer': '', 'sources': []}
    try:
        return search_chat(body.question.strip())
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))


@aiqa_router.post('/aiqa/episode')
def post_episode(ep: EpisodeIn):
    """记一条 L3 episode（append DATA/ai_qa/episodes.jsonl）。失败不抛（返回 ok=False）。"""
    saved = log_episode(
        question=ep.question, diagnose=ep.diagnose, final=ep.final,
        defense=ep.defense, ok=ep.ok, extra=ep.extra, capsule_clicked=ep.capsule_clicked,
    )
    return {'ok': saved}


class OutletCardIn(BaseModel):
    """CB-16 Wave 0：出口卡片组装入参（前端 result 态后 POST）。"""
    question: str = ''
    diagnose: Optional[Dict[str, Any]] = None   # scale/domain_lens/outlet
    result: Optional[Dict[str, Any]] = None     # 分析产物（polarity_index/features 等）
    tool_history: Optional[str] = ''


@aiqa_router.post('/aiqa/outlet_card')
def post_outlet_card(body: OutletCardIn):
    """CB-16 Wave 0：确定性组装出口卡片（结果范式 agent·第三段·Wave 3 多卡）。

    前端 harness result 态后条件调用（问句含接口词·不碰承重路径）。
    返回 {cards: [...], card: cards[0]}（cards 多卡·card 兼容旧前端·未命中 []/None）。
    确定性·不调 LLM·字段缺失降级·不编造。
    """
    from ai_qa.outlet_kb.build_outlet_schema import build_outlet_schema
    cards = build_outlet_schema(body.diagnose or {}, body.result or {}, body.question)
    return {'cards': cards, 'card': cards[0] if cards else None}


class RagSearchIn(BaseModel):
    """CB-22 RAG 接入：知识检索入参（开放语义·B 路径未命中降级）。"""
    query: str
    k: int = 5


@track('MOD_AIQA.F_017', track_args=False)
@aiqa_router.post('/aiqa/rag_search')
def post_rag_search(body: RagSearchIn):
    """CB-22 RAG：知识检索（开放语义/跨文档综合·返回 Top-K + 维度分布）。

    触发：harness _quickIntent 'rag_query' 短路（开放语义词）·B 路径（CB-22b）未命中时降级。
    返回 {ok, results:[{score, source, type, data_dim}], count, dim_counts}。
    确定性（向量检索非 LLM）·索引未构建返 ok:False 非 500（前端静默）。
    """
    from tools.rag_index import search
    r = search(body.query, body.k)
    if not r.get('ok'):
        return {'ok': False, 'error': r.get('error', '索引未构建·跑 py tools/rag_index.py --build')}
    # dim_counts：Top-K 维度分布（finalStep 维度声明直接引用·颗粒度原则）
    dim_counts = {}
    for res in r['results']:
        d = res.get('data_dim', '社区')
        dim_counts[d] = dim_counts.get(d, 0) + 1
    return {'ok': True, 'results': r['results'], 'count': r['count'], 'dim_counts': dim_counts}


class ProfileFieldsIn(BaseModel):
    # P2 字段语义推断：fields = 规则字典 miss 的 {field: {dtype, samples, stats}}
    fields: Dict[str, Dict[str, Any]] = {}
    layer_kind: str = ''    # 'point' | 'polygon' | ''（推断辅助）
    context: str = ''       # 可选附加上下文


def _parse_field_json(raw: str) -> dict:
    """容错解析字段推断 JSON；失败返 {}（首末花括号截取 + 尾逗号清理·通用范式）。"""
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


class DeepAttributionIn(BaseModel):
    # L4 深度归因（lazy enrichment）：簇评论 + 规则底 → LLM 政策→情绪→项目闭环
    domain: str = ''           # urban_renewal/...（簇 domain_top）
    element: str = ''          # 设施/环境/服务/文化/事件（element_top）
    polarity: str = ''         # positive/negative/neutral 或中文
    zone_name: str = ''        # 簇/区域名（如"二马路历史街区"）
    sample_texts: List[str] = []   # 簇内代表性评论（≤8 条）
    rule_suggestion: str = ''  # 规则底归因 suggestion（_attach_4x5_attrs 产出）
    # L4 种子 hints（Sim ermawu_l3l4 富归因数据预提取；普通 L2 无则空）
    policy_seed_hint: str = ''   # 簇点 policy_seed top（权威锚，LLM 优先用）
    project_seed_hint: str = ''  # 簇点 project_seed top
    aspect_hint: str = ''        # 簇点 aspect_primary top（ABSA 维度）


def _deep_attribution_fallback(body: DeepAttributionIn, reason: str, parsed: dict = None) -> dict:
    """低置信(<0.5)/LLM 不可用/未产出 → 回退规则底（degraded）。规则底常在保零回归。"""
    p = parsed or {}
    return {
        'deep_attribution': p.get('deep_attribution') or body.rule_suggestion or '（规则底归因，LLM 未深化）',
        'policy_link': p.get('policy_link', ''),
        'project_link': p.get('project_link', ''),
        'confidence': float(p.get('confidence') or 0),
        'blind_spot': p.get('blind_spot', ''),
        'degraded': True,
        'degraded_reason': reason,
    }


@aiqa_router.post('/aiqa/deep_attribution')
def post_deep_attribution(body: DeepAttributionIn):
    """L4 深度归因（lazy enrichment）：EMC 深读某簇时按需触发（非 eager 每 aggregate 跑）。
    簇评论 + 规则底 + 权威语境 → LLM 政策→情绪→项目闭环 JSON。
    低置信(<0.5)/LLM 不可用 → 回退规则底（degraded）。复用 chat_with_fallback（DeepSeek→Ark→讯飞韧性链）。"""
    if not body.sample_texts and not body.rule_suggestion:
        return _deep_attribution_fallback(body, '缺 sample_texts 与 rule_suggestion，无可深化素材')
    sys_prompt = build_deep_attribution_prompt(
        body.domain, body.element, body.polarity, body.zone_name, body.sample_texts, body.rule_suggestion,
        body.policy_seed_hint, body.project_seed_hint, body.aspect_hint)
    messages = [
        {'role': 'system', 'content': sys_prompt},
        {'role': 'user', 'content': '请为上述簇输出深度归因 JSON。'},
    ]
    try:
        gen = chat_with_fallback(messages, tier='flash', stream=False,
                                 json_mode=True, with_reason=False,
                                 temperature=0.2, max_tokens=900)
        raw = next(gen)
    except LLMError as e:
        return _deep_attribution_fallback(body, str(e))
    except Exception as e:
        return _deep_attribution_fallback(body, f'deep_attribution 异常: {e}')
    parsed = _parse_field_json(raw)
    if not parsed or not parsed.get('deep_attribution'):
        return _deep_attribution_fallback(body, 'LLM 未产出有效 deep_attribution')
    try:
        conf = float(parsed.get('confidence') or 0)
    except (TypeError, ValueError):
        conf = 0.0
    if conf < 0.5:
        return _deep_attribution_fallback(body, f'low confidence ({conf} < 0.5)', parsed=parsed)
    return {
        'deep_attribution': parsed.get('deep_attribution', ''),
        'policy_link': parsed.get('policy_link', ''),
        'project_link': parsed.get('project_link', ''),
        'confidence': conf,
        'blind_spot': parsed.get('blind_spot', ''),
        'degraded': False,
    }
