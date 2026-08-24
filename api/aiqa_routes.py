"""AI 问答自成长知识闭环路由 /api/v1/aiqa/*（挂载到 api/main.py，prefix=/api/v1）。

两类端点：
- GET  /aiqa/wisdom  → 返回 L2 wisdom_text（前端 buildContext 拼进 ctx.context，注入答问 prompt）。
- POST /aiqa/episode → 记一条 L3 情境日志（harness 末尾 fire-and-forget，失败静默不阻塞交付）。

三层知识闭环：L1=MANIFESTO（稳定）/ L2=ai_qa/wisdom.py（人审策展·本路由读出）/
L3=ai_qa/episode.py 写 DATA/ai_qa/episodes.jsonl（被 ai_qa/consolidate.py 周期挖掘提议 L2）。

挂载：api/main.py `app.include_router(aiqa_router, prefix='/api/v1')` → 总路径 /api/v1/aiqa/*。
"""
import json
import sys
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.tracker import track, track_async, register_track_id
from core.codex_bridge import get_bridge
from ai_qa.wisdom import wisdom_text, retrieve_wisdom
from ai_qa.episode import log_episode
from ai_qa.llm import LLMError, chat_with_fallback, search_chat

register_track_id('MOD_AIQA.F_017', 'post_rag_search（RAG 知识检索端点·开放语义·返回 Top-K + dim_counts）')
register_track_id('MOD_AIQA.F_041', 'post_dsh_engine（壳二期 BA：dsh headless 引擎端点·spawn dsh --profile emc-test 一次性问答·stdout 全量返回·无流式降级形态）')
register_track_id('MOD_AIQA.F_043', 'post_codex_engine（PT-CB15 SPIKE：Codex app-server SSE 引擎端点·bridge 事件流→text/event-stream·真流式 msg.delta 源）')
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


class DshEngineIn(BaseModel):
    """壳二期 BA：dsh headless 引擎入参（降级形态·无真流式——契约 docs/brain-adapter.md §二）。"""
    # FIX-02：max_length=4000——Windows 命令行 32767 上限远大于此·语义化 422 拒绝（防 OSError(WinError 206)→500）
    question: str = Field(default='', max_length=4000)
    timeout_s: int = 240


# FIX-01：有界并发闸（上限 2）——多用户同时调 dsh 时排队等待（低频场景可接受·防 profile 竞争+资源风暴）。
# 模块级 Semaphore：asyncio 原语惰性绑当前 loop·uvicorn 单 loop 安全。
import asyncio
_dsh_semaphore = asyncio.Semaphore(2)

_DSH_MAX_OUTPUT = 200 * 1024   # FIX-05：stdout 上限 200KB（dsh 异常喷长日志时保护内存/响应体积）
# PT-CB14 D-3 Q4 迭代史（实测固化）：
#   v1：单次预算压 140s 为重试留余量 → 多工具链（实测 50-366s）全超时回归（top10 0/3）——预算不可压；
#   v2：仅快速失败重试 → 丢失任务书「超时重试」语义（发散为概率性·同题第二遍可能收敛，zcode 对照实验 2成1败）；
#   v3（现行）：除 OSError（问句过长·重试无益）外全部失败重试一次（间隔 2s）·预算保调用方原值。
#   注：最坏总时长 240+2+240=482s > 代理 300s——第一遍超时后代理可能先断，但第二遍仍在后台跑完：
#   出图副作用（render_spec 写盘→SSE 推图）与 HTTP 响应解耦，重试对用户体验仍有正收益。


def _safe_print(msg, file=None):
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'), file=file)


def _run_dsh_sync(q: str, timeout_s: int) -> Dict[str, Any]:
    """dsh headless 同步执行体（在 asyncio.to_thread 里跑·不占事件循环）。

    命令解析 fail-closed（FIX-03）：npm shim→node 直调 bin.js（argv 传参零注入）；
    dsh 非 .cmd（POSIX 软链）→直调；其余布局（含 bin.js 缺失）→语义化拒绝·不留死路径。
    PT-CB14 D-3 Q4（v3）：除 OSError（问句过长·重试无益）外，失败（超时/非零返回/空 stdout）自动重试一次（间隔 2s）；
    响应恒带 retried 字段；单次尝试预算保调用方原值（v1 压缩致回归·教训见模块头注释）。
    """
    import os
    import shutil
    import subprocess
    import time as _time

    exe = shutil.which('dsh')
    if not exe:
        return {'ok': False, 'error': 'dsh not found in PATH（本机未装 dsh——装 dsh 后可用·双机差异注记）'}
    if exe.lower().endswith(('.cmd', '.bat')):
        # npm shim 结构固定：node "<dp0>\\node_modules\\@deepseek-ai\\dsh\\lib\\bin.js" %*
        dp0 = os.path.dirname(exe)
        bin_js = os.path.join(dp0, 'node_modules', '@deepseek-ai', 'dsh', 'lib', 'bin.js')
        if not os.path.isfile(bin_js):
            return {'ok': False, 'error': 'dsh 安装布局未识别（npm shim 下未见 bin.js·请检查 dsh 安装）'}
        node_exe = os.path.join(dp0, 'node.exe')
        node = node_exe if os.path.isfile(node_exe) else (shutil.which('node') or 'node')
        cmd = [node, bin_js, '--profile', 'emc-test', q]
    else:
        cmd = [exe, '--profile', 'emc-test', q]

    attempt_budget = timeout_s   # Q4v2：预算不压——多工具链需 50-185s，压缩致回归（实测）
    retried = False
    for _attempt in range(2):
        t0 = _time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                                  errors='replace', timeout=attempt_budget, shell=False)
        except subprocess.TimeoutExpired:
            if _attempt == 0:   # Q4v3：超时重试（发散概率性·同题第二遍可能收敛·任务书语义）
                retried = True
                _safe_print(f'[WARN] dsh_engine 超时({attempt_budget}s)·2s 后自动重试一次（PT-CB14 D-3 Q4v3）', file=sys.stderr)
                _time.sleep(2)
                continue
            return {'ok': False, 'error': f'dsh timeout ({attempt_budget}s x2 attempts)',
                    'elapsed': round(_time.time() - t0, 1), 'retried': True}
        except OSError as e:   # FIX-02：超长问句/系统限制（如 WinError 206）——语义化降级·不 500·重试无益不重跑
            return {'ok': False, 'error': f'问句过长或系统限制：{e}', 'elapsed': round(_time.time() - t0, 1),
                    'retried': retried}

        out = (proc.stdout or '').strip()
        err = (proc.stderr or '').strip()
        ok = proc.returncode == 0 and bool(out)
        if not ok and _attempt == 0:   # Q4v3：非零返回/空 stdout → 重试一次（含慢败·出图副作用与响应解耦）
            retried = True
            _safe_print(f'[WARN] dsh_engine rc={proc.returncode}/空输出·2s 后自动重试一次（PT-CB14 D-3 Q4v3）', file=sys.stderr)
            _time.sleep(2)
            continue
        truncated = len(out) > _DSH_MAX_OUTPUT   # FIX-05：输出截断标记（前端按需提示）
        if truncated:
            out = out[:_DSH_MAX_OUTPUT]
        resp = {'ok': ok, 'output': out, 'elapsed': round(_time.time() - t0, 1),
                'returncode': proc.returncode, 'stderr_tail': err[-400:], 'truncated': truncated,
                'retried': retried}
        if not ok:
            resp['error'] = err[-400:] or f'dsh returncode={proc.returncode} / empty stdout'
        return resp
    return {'ok': False, 'error': 'dsh 重试流程异常', 'retried': retried}


@track_async('MOD_AIQA.F_041', track_args=False)
@aiqa_router.post('/aiqa/dsh_engine')
async def post_dsh_engine(body: DshEngineIn):
    """壳二期 BrainAdapter：spawn dsh headless（`dsh --profile emc-test "<q>"`）一次性问答。

    返回 {ok, output, elapsed, returncode, stderr_tail, truncated}——output=stdout（截 200KB·无流式）。
    FIX-01：async def + asyncio.to_thread（不占 uvicorn 共享线程池）+ Semaphore(2) 有界并发排队。
    降级形态事件（tool.begin 桩+周期 ping）由前端 BA 发·本端点只出结果。
    """
    q = (body.question or '').strip()
    if not q:
        return {'ok': False, 'error': 'empty question'}
    timeout_s = max(30, min(int(body.timeout_s or 240), 600))
    async with _dsh_semaphore:
        return await asyncio.to_thread(_run_dsh_sync, q, timeout_s)


class CodexEngineIn(BaseModel):
    """PT-CB15 SPIKE：Codex 引擎入参（全量形态·真流式——契约 docs/brain-adapter.md §二）。"""
    question: str = Field(default='', max_length=4000)
    timeout_s: int = 300


@track_async('MOD_AIQA.F_043', track_args=False)
@aiqa_router.post('/aiqa/codex_engine')
async def post_codex_engine(body: CodexEngineIn):
    """PT-CB15 SPIKE：Codex app-server 引擎端点（SSE 流式）。

    事件流（text/event-stream·bridge 逐事件转发）：
      delta {kind:content|reason, delta, n} / tool {phase:begin|end, name, ok} /
      ping {elapsed}（15s 心跳·防反代读超时）/ done {status, n_delta, elapsed} /
      error {code, message}（fail-closed 语义化·不伪造答案）。
    出图：Codex 经 MCP 8600 调 render_spec 写盘→SSE 推图（与 HTTP 响应解耦·与 dsh 同源先例）。
    """
    q = (body.question or '').strip()
    if not q:
        return {'ok': False, 'error': 'empty question'}

    async def _gen():
        bridge = get_bridge()
        try:
            async for evt in bridge.ask(q, timeout_s=max(30, min(int(body.timeout_s or 300), 600))):
                # SSE 帧分隔约定（PT-CB15 P2-11）：event 行 + data 行 + 空行（\n\n 分帧·LF）；
                # 前端解析端须兼容 CRLF（见 brain-adapter-codex.js 归一化）。
                yield f"event: {evt.get('event', 'msg')}\ndata: {json.dumps(evt, ensure_ascii=False)}\n\n"
        except Exception as e:   # 桥层未捕获异常兑底：error 事件收口（SSE 已开流·不 500）
            yield f"event: error\ndata: {json.dumps({'event': 'error', 'code': 'CODEX_ENDPOINT', 'message': str(e)[:200]}, ensure_ascii=False)}\n\n"

    return StreamingResponse(_gen(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


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
    返回 {ok, results:[{score, source, type, data_dim, text}], count, dim_counts}。
    text=片段全文（CB-22 三支柱修正·供 finalStep LLM 综合·老索引无 text 为空串）。
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
