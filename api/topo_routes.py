"""项目架构拓扑图路由 /api/v1/topo（挂载到 api/main.py，prefix=/api/v1）。

GET /topo → 实时扫描项目结构（os.walk + ast + regex + AGENTS.md/revision-log 解析），
返回 force-graph（vasturiano）所需的 {nodes, links} JSON。mtime 签名缓存避免重复扫描。

前端 frontend/topology.html fetch 本端点 → force-graph 渲染交互拓扑图。
view 参数仅作 hint（后端默认返回全量，前端按 preset 过滤）：
  global / pipeline / emc / agent_skills / roadmap / module

挂载：api/main.py `app.include_router(topo_router, prefix='/api/v1')` → 总路径 /api/v1/topo。
核心扫描逻辑在 core/topo_scanner.py（参考 core/spatial_analysis.py + api/geo_routes.py 范式）。
"""
from pathlib import Path

from fastapi import APIRouter

from core.topo_scanner import build_topology, invalidate_cache, PROJECT_ROOT

topo_router = APIRouter()

_ALLOWED_VIEWS = {'global', 'pipeline', 'emc', 'agent_skills', 'roadmap', 'module'}


@topo_router.get('/topo')
def get_topology(view: str = 'global', refresh: bool = False):
    """返回项目架构拓扑 force-graph JSON（实时扫描 + mtime 缓存）。

    - view: 预设视图 hint（前端实际按 preset 过滤；后端默认返回全量）。
    - refresh: True 时清缓存强制全扫。
    """
    if view not in _ALLOWED_VIEWS:
        view = 'global'
    if refresh:
        invalidate_cache()
    return build_topology(PROJECT_ROOT, view=view)
