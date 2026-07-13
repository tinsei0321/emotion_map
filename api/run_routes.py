"""P3 code-exec /run 路由：把 sandbox.run_sandbox 暴露给 LLM agent 的 run_python 工具。

挂载条件：api/main.py 的 ``if SAFE_READY:`` gate（sandbox.py SAFE_READY=True 才挂）。
安全：sandbox 已叠三道底线（open-wrapper 路径白名单 / AST 反射审查 / frame-based eval），
CORS 收紧本机——但仍非 OS 级隔离（内存/CPU 仅超时软限），仅本地单机演示用，不暴露公网。

范式照 api/aiqa_routes.py post_profile_fields（Pydantic 入参 + 归一返回 + 永不裸输）。
run_sandbox 自身永不抛，路由层无需 try/except 包执行错误。
"""
import base64
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.sandbox import run_sandbox, SAFE_READY

run_router = APIRouter()


class RunIn(BaseModel):
    code: str
    # 注入子进程全局命名空间的对象（pickleable），如 {'fc': <GeoJSON dict>}。前端 run_python 工具
    # 把图层 fc 按 as 变量名注入，用户代码直接用该变量。
    data_refs: Dict[str, Any] = Field(default_factory=dict)
    timeout: float = 30.0


def _encode_images(artifacts: List[dict]) -> List[dict]:
    """image artifacts → {id, name, dataUri}（base64 内嵌，供前端 _figCache + {{fig:ID}} 渲染）。

    figId=fig{n}（n 从 1 起，只数 image）——纯 ASCII 字母+数字，避开 5.74 对账 verbRe/showRe 污染
    （observation 文案另用「图片」不用图层词，双重保险）。
    """
    out: List[dict] = []
    i = 0
    for a in artifacts or []:
        if a.get('type') != 'image':
            continue
        try:
            data = Path(a['path']).read_bytes()
            ext = a['name'].rsplit('.', 1)[-1].lower() if '.' in a['name'] else 'png'
            mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                    'svg': 'image/svg+xml', 'pdf': 'application/pdf'}.get(ext, 'image/png')
            data_uri = f'data:{mime};base64,{base64.b64encode(data).decode("ascii")}'
            i += 1
            out.append({'id': f'fig{i}', 'name': a['name'], 'dataUri': data_uri})
        except Exception:
            continue   # 单图编码失败不阻塞其他图
    return out


@run_router.post('/run')
def post_run(body: RunIn):
    """执行 agent 生成的 Python 代码（前端 run_python 工具的后端）。

    返回 {ok, stdout, error, figs}：figs = 图片 base64（前端 _figCache 缓存 → {{fig:ID}} 渲染）。
    SAFE_READY 双保险：main.py gate 外再守一道，防误挂。
    timeout clamp 到 [5, 60] 防滥用（演示场景）。
    """
    if not SAFE_READY:
        return {'ok': False, 'stdout': '', 'error': 'sandbox SAFE_READY=False，/run 未启用',
                'figs': []}
    timeout = max(5.0, min(float(body.timeout or 30.0), 60.0))
    r = run_sandbox(body.code, data_refs=body.data_refs or None, timeout=timeout)
    return {
        'ok': r['ok'],
        'stdout': r.get('stdout', ''),
        'error': r.get('error'),
        'figs': _encode_images(r.get('artifacts', [])),
    }
