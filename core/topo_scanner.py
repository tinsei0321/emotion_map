"""项目架构拓扑图扫描器（Project Topology Scanner）。

实时扫描项目自身结构，产出 force-graph（vasturiano）所需的 {nodes, links} JSON：
  - os.walk   → 目录/文件节点 + contains（包含）边
  - ast       → .py import 边（含相对 import level 上溯解析）
  - regex     → .js ES module import 边（+ 动态 import() 兜底）
  - AGENTS.md → 21 个 MOD_* 模块节点 + 文件→module 反查 + owns 边
  - revision-log §0 → 任务节点（任务树扁平）
  - revision-log §5 → latest 最新动态指针
  - CLAUDE.md L0→L4 → 5 个合成 pipeline-stage 节点 + pipeline 边

挂载：api/topo_routes.py `GET /api/v1/topo` → 本模块 build_topology()。
属 dev 工具、非业务管道：不动 tracker 红线（不 register_track_id、不加 MOD_TOPO），
仅入口 _safe_print 日志。

设计参考：core/spatial_analysis.py + api/geo_routes.py 的「核心逻辑在 core / HTTP 适配在 api」范式。
"""
import ast
import hashlib
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.utils import safe_print

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ── 扫描排除（第三方源码快照 + 缓存目录）──
_EXCLUDE_DIRS = {
    '__pycache__', '.git', 'node_modules', '.pytest_cache', '.trace', '.idea', '.vscode',
    # docs 下第三方源码快照（非本项目）
    'maplibre-gl-js-main', 'martin-main', 'geojson.io', 'minimax-workspace', 'minimax-workbox', 'refs',
    # vision-inbox 是 MCP 识图中转站（非代码）
    'vision-inbox',
}
_EXCLUDE_DIR_SUFFIXES = ('-main',)  # docs 下 *-main 源码快照兜底
# 节点收录的扩展名
_INCLUDE_EXT = {'.py', '.js', '.mjs', '.md', '.html', '.css'}

# ── L0→L4 数据管道（CLAUDE.md 权威定义）──
_PIPELINE_STAGES: List[Tuple[str, str, str, str]] = [
    ('L0', 'L0 原始采集', 'Scrapy 爬虫',   'done'),
    ('L1', 'L1 数据治理', '坐标+脱敏',     'progress'),
    ('L2', 'L2 情绪极性', 'SnowNLP+jieba', 'done'),
    ('L3', 'L3 语义增强', 'DeepSeek LLM',  'todo'),
    ('L4', 'L4 多维归因', '空间统计+lazy', 'progress'),
]

# ── mtime 签名缓存（同签名命中直返）──
_CACHE_LOCK = threading.Lock()
_CACHE: Dict[str, Any] = {"sig": None, "data": None, "builtAt": 0.0}

# 任务树状态 emoji → state
_TASK_STATE_MAP = {'✅': 'done', '🔄': 'progress', '⬜': 'todo', '⏸': 'paused',
                   '❌': 'rejected', '◆': 'milestone'}
# AGENTS.md 模块表状态 emoji → state
_MOD_STATE_MAP = {'✅': 'done', '⬜': 'todo', '🔧': 'milestone', '🔄': 'progress'}

# revision-log §0 ```text 任务树行：缩进（树形字符+空格）+ 标签 + 可选状态 emoji
_TASK_LINE_RE = re.compile(r"^([├└─│\s]+)(.+?)(✅|🔄|⬜|⏸|❌|◆)?\s*$")
# AGENTS.md 模块表行：| emoji | `MOD_XXX` | `path` |
_MOD_ROW_RE = re.compile(r"\|\s*(✅|⬜|🔧|🔄)\s*\|\s*`(MOD_\w+)`\s*\|\s*`([^`]+)`")
# JS ES module import/export ... from 'spec'
_JS_IMPORT_RE = re.compile(
    r"""^\s*(?:import\s+(?:[\s\S]*?\s+from\s+)?|export\s+(?:\*|\{[^}]*\})\s+from\s+)['"]([^'"]+)['"]""",
    re.MULTILINE,
)
# JS 动态 import('spec')
_JS_DYNAMIC_RE = re.compile(r"""import\(\s*['"]([^'"]+)['"]\s*\)""")


def build_topology(root: Path, view: str = "global") -> dict:
    """扫描项目，返回 force-graph JSON。view 仅作 hint（后端默认返回全量，前端按 preset 过滤）。"""
    sig = _compute_signature(root)
    with _CACHE_LOCK:
        if _CACHE["sig"] == sig and _CACHE["data"] is not None:
            data = _CACHE["data"]
            data["cache"] = {"hit": True, "ageMs": int((time.time() - _CACHE["builtAt"]) * 1000)}
            return data

    nodes: List[dict] = []
    links: List[dict] = []
    file_index: Dict[str, dict] = {}   # id → node（反查回填 module/state 用）

    _scan_dir_tree(root, nodes, links, file_index)
    _scan_imports(root, links, file_index)
    _scan_fastapi_routes(root / "api" / "main.py", root, links)
    modules = _parse_agents_modules(root / "AGENTS.md", nodes, links, file_index)
    tasks = _parse_revision_tasks(root / "docs" / "revision-log.md", nodes)
    latest = _parse_latest_pointer(root / "docs" / "revision-log.md")
    _inject_pipeline_stages(nodes, links)
    _cleanup_links(nodes, links)

    data = {
        "nodes": nodes,
        "links": links,
        "modules": modules,
        "tasks": tasks,
        "latest": latest,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "stats": _summarize(nodes, links),
        "cache": {"hit": False, "ageMs": 0},
    }
    with _CACHE_LOCK:
        _CACHE["sig"] = sig
        _CACHE["data"] = data
        _CACHE["builtAt"] = time.time()
    safe_print(f"[OK] topo built: {len(nodes)} nodes, {len(links)} links (view={view})")
    return data


def invalidate_cache() -> None:
    """端点 ?refresh=1 调用：清签名，下次请求强制全扫。"""
    with _CACHE_LOCK:
        _CACHE["sig"] = None


# ════════════════════════════════════════════════════════════════════
# 目录树 + 文件节点
# ════════════════════════════════════════════════════════════════════
def _is_excluded_dir(name: str) -> bool:
    if name in _EXCLUDE_DIRS:
        return True
    if name.startswith('.') and name not in ('.claude',):
        # .claude 是项目 harness 要扫；其他隐藏目录（.git 等）已在 _EXCLUDE_DIRS 或此分支排除
        return name not in ('.claude',)
    return any(name.endswith(s) and len(name) > len(s) for s in _EXCLUDE_DIR_SUFFIXES)


# .claude 下要排除的完整路径前缀（marketplace skill 缓存 ~1500+543 文件、worktree 副本等）
_EXCLUDE_PATHS = ('.claude/skills', '.claude/skills_archive', '.claude/worktrees', '.claude/projects',
                  '.claude/shell-snapshots', '.claude/todos', '.claude/plans')


def _is_excluded_path(rel: str) -> bool:
    """完整 rel 路径前缀排除（配合 basename 黑名单，剪掉 marketplace 缓存等大目录）。"""
    return any(rel == p or rel.startswith(p + '/') for p in _EXCLUDE_PATHS)


def _rel(p: Path, root: Path) -> str:
    return os.path.relpath(p, root).replace('\\', '/')


def _scan_dir_tree(root: Path, nodes: List[dict], links: List[dict],
                   file_index: Dict[str, dict]) -> None:
    """os.walk → dir + file 节点 + contains 边。原地改 dirnames 剪枝。"""
    dir_node_ids: set = set()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace('\\', '/')
        if rel_dir == '.':
            rel_dir = ''   # 根
        # 剪枝：basename 黑名单 + .claude 下 marketplace 缓存等路径前缀
        dirnames[:] = [
            d for d in dirnames
            if not _is_excluded_dir(d)
            and not _is_excluded_path(f"{rel_dir}/{d}" if rel_dir else d)
        ]
        if rel_dir == '':
            group = 'root'
        else:
            group = rel_dir.split('/')[0]
            if rel_dir not in dir_node_ids:
                dir_node_ids.add(rel_dir)
                nodes.append({
                    "id": rel_dir, "name": os.path.basename(dirpath), "group": group,
                    "type": "dir", "path": rel_dir + '/', "fileType": None, "lines": None,
                    "state": None, "module": None, "docs": [], "collapsed": True,
                })
                parent = '/'.join(rel_dir.split('/')[:-1])
                if parent:
                    links.append({"source": parent, "target": rel_dir, "type": "contains"})
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in _INCLUDE_EXT:
                continue
            fid = f"{rel_dir}/{fn}" if rel_dir else fn
            if fid in file_index:
                continue
            fp = root / fid
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                    lines = sum(1 for _ in fh)
            except Exception:
                lines = None
            node = {
                "id": fid, "name": fn, "group": group, "type": "file", "path": fid,
                "fileType": ext.lstrip('.') or None, "lines": lines, "state": None,
                "module": None, "docs": [], "collapsed": False,
            }
            nodes.append(node)
            file_index[fid] = node
            if rel_dir:
                links.append({"source": rel_dir, "target": fid, "type": "contains"})


# ════════════════════════════════════════════════════════════════════
# import 边（.py ast + .js regex）
# ════════════════════════════════════════════════════════════════════
def _scan_imports(root: Path, links: List[dict], file_index: Dict[str, dict]) -> None:
    for fid, node in file_index.items():
        ft = node.get('fileType')
        if ft == 'py':
            _scan_py_imports(root / fid, root, links, file_index)
        elif ft in ('js', 'mjs'):
            _scan_js_imports(root / fid, root, links, file_index)


def _emit_import_link(src_id: str, dotted: str, root: Path, links: List[dict],
                      lang: str, weak: bool = False) -> None:
    """dotted module path → 文件路径候选；命中项目内文件才加 import 边（自然过滤标准库）。"""
    base = dotted.replace('.', '/')
    cands = [base + '.py', base + '/__init__.py']
    for c in cands:
        if (root / c).is_file():
            links.append({"source": src_id, "target": c, "type": "import",
                          "lang": lang, **({"weak": True} if weak else {})})
            return


def _scan_py_imports(fp: Path, root: Path, links: List[dict],
                     file_index: Dict[str, dict]) -> None:
    try:
        tree = ast.parse(fp.read_text(encoding='utf-8', errors='ignore'), filename=str(fp))
    except (SyntaxError, ValueError):
        return
    src_id = _rel(fp, root)
    pkg = src_id.rsplit('/', 1)[0].replace('/', '.') if '/' in src_id else ''
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _emit_import_link(src_id, alias.name, root, links, lang='py')
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # 相对 import：从当前包 pkg 上溯 level-1 级（level=1→当前包，level=2→上一级）
                parts = pkg.split('.') if pkg else []
                cut = len(parts) - (node.level - 1)
                base = '.'.join(parts[:cut]) if cut >= 0 and parts else ''
                full = f"{base}.{node.module}" if (base and node.module) else (node.module or base)
            else:
                # 绝对 import：module 本身即完整 dotted 路径（勿拼 pkg，否则成 core.core.xxx）
                full = node.module
            if full:
                _emit_import_link(src_id, full, root, links, lang='py')


def _resolve_js_spec(spec: str, src_id: str, root: Path) -> Optional[str]:
    """相对 specifier → 项目内文件 id；bare npm 包返回 None。"""
    if not spec.startswith('.'):
        return None
    d = src_id.rsplit('/', 1)[0] if '/' in src_id else ''
    for part in spec.split('/'):
        if part == '..':
            d = d.rsplit('/', 1)[0] if '/' in d else ''
        elif part in ('.', ''):
            continue
        else:
            d = f"{d}/{part}" if d else part
    for ext in ('.js', '.mjs', '/index.js', '/index.mjs'):
        cand = d + ext
        if (root / cand).is_file():
            return cand
    # 兜底：源文件可能省略扩展名
    for ext in ('.js', '.mjs'):
        if (root / (d + ext)).is_file():
            return d + ext
    return None


def _scan_js_imports(fp: Path, root: Path, links: List[dict],
                     file_index: Dict[str, dict]) -> None:
    text = fp.read_text(encoding='utf-8', errors='ignore')
    src_id = _rel(fp, root)
    for m in _JS_IMPORT_RE.finditer(text):
        tgt = _resolve_js_spec(m.group(1), src_id, root)
        if tgt:
            links.append({"source": src_id, "target": tgt, "type": "import", "lang": "js"})
    for m in _JS_DYNAMIC_RE.finditer(text):
        tgt = _resolve_js_spec(m.group(1), src_id, root)
        if tgt:
            links.append({"source": src_id, "target": tgt, "type": "import", "lang": "js", "weak": True})


# ════════════════════════════════════════════════════════════════════
# FastAPI 路由挂载边
# ════════════════════════════════════════════════════════════════════
def _scan_fastapi_routes(main_py: Path, root: Path, links: List[dict]) -> None:
    if not main_py.is_file():
        return
    text = main_py.read_text(encoding='utf-8', errors='ignore')
    # 抓 `from <api|ai_qa>.x import name [as alias]` → key=别名优先（include_router 用别名）
    import_re = re.compile(r"from\s+((?:api|ai_qa)[\w.]*)\s+import\s+(\w+)(?:\s+as\s+(\w+))?")
    include_re = re.compile(r"app\.include_router\(\s*(\w+)")
    imports: Dict[str, str] = {}
    for m in import_re.finditer(text):
        mod, name, alias = m.group(1), m.group(2), m.group(3)
        imports[alias or name] = mod
    for m in include_re.finditer(text):
        var = m.group(1)
        mod_path = imports.get(var)
        if not mod_path:
            continue
        router_file = mod_path.replace('.', '/') + '.py'
        if (root / router_file).is_file():
            links.append({"source": "api/main.py", "target": router_file, "type": "route"})


# ════════════════════════════════════════════════════════════════════
# AGENTS.md 模块表
# ════════════════════════════════════════════════════════════════════
def _parse_agents_modules(path: Path, nodes: List[dict], links: List[dict],
                          file_index: Dict[str, dict]) -> List[dict]:
    if not path.is_file():
        return []
    text = path.read_text(encoding='utf-8', errors='ignore')
    modules: List[dict] = []
    for m in _MOD_ROW_RE.finditer(text):
        emoji, mod_id, raw_path = m.group(1), m.group(2), m.group(3)
        state = _MOD_STATE_MAP.get(emoji, 'todo')
        mod_path = raw_path.replace('\\', '/').rstrip('/')
        modules.append({"id": mod_id, "name": mod_id, "file": mod_path, "state": state})
        nodes.append({
            "id": mod_id, "name": mod_id, "group": "module", "type": "module",
            "path": mod_path, "fileType": None, "lines": None, "state": state,
            "module": mod_id, "docs": ["AGENTS.md"], "collapsed": False,
        })
        # 反查文件节点回填 module + state + owns 边（mod_path 可能含 + 多文件，逐一匹配）
        matched = False
        for cand in _split_module_paths(mod_path):
            fn = file_index.get(cand)
            if fn:
                fn['module'] = mod_id
                if fn.get('state') is None:
                    fn['state'] = state
                links.append({"source": mod_id, "target": cand, "type": "owns"})
                matched = True
        if not matched:
            # 文件未被收录（如目录型 mod_path）→ owns 边指向路径本身（若存在为目录节点）
            links.append({"source": mod_id, "target": mod_path, "type": "owns"})
    return modules


def _split_module_paths(mod_path: str) -> List[str]:
    """AGENTS.md mod_path 可能是 'apps/app_main.py + app_dialogs.py + app_console.py' → 拆分。"""
    out = []
    for part in re.split(r'\s*\+\s*', mod_path):
        part = part.strip().replace('\\', '/').rstrip('/')
        if part:
            out.append(part)
    return out


# ════════════════════════════════════════════════════════════════════
# revision-log §0 任务树 + §5 最新动态
# ════════════════════════════════════════════════════════════════════
def _parse_revision_tasks(path: Path, nodes: List[dict]) -> List[dict]:
    if not path.is_file():
        return []
    text = path.read_text(encoding='utf-8', errors='ignore')
    # §0 任务树在 ```text fenced 块里（紧跟「★ 任务路线图」标题）
    m = re.search(r"★.*?```text\s*\n(.*?)```", text, re.DOTALL)
    if not m:
        return []
    tasks: List[dict] = []
    seen_ids: set = set()
    for line in m.group(1).splitlines():
        rm = _TASK_LINE_RE.match(line)
        if not rm:
            continue
        indent, label, emoji = rm.groups()
        label = label.strip().rstrip('｜|').strip()
        # 跳过纯分隔符行（如 '│'、空树形）
        if not label or len(label) < 2:
            continue
        state = _TASK_STATE_MAP.get(emoji) if emoji else None
        tid = f"task:{label[:40]}"
        if tid in seen_ids:
            continue
        seen_ids.add(tid)
        tasks.append({"id": tid, "label": label, "state": state or 'unknown',
                      "depth": max(1, len(indent) // 2)})
        nodes.append({
            "id": tid, "name": label, "group": "task", "type": "task",
            "path": "docs/revision-log.md#任务路线图", "fileType": None, "lines": None,
            "state": state or 'unknown', "module": None,
            "docs": ["docs/revision-log.md"], "collapsed": False,
        })
    return tasks


def _parse_latest_pointer(path: Path) -> Optional[dict]:
    if not path.is_file():
        return None
    text = path.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r"最新动态（([^）]+)）\*\*.*?最新工作\s*=\s*\*\*(5\.\d+)\s+(.+?)\*\*", text)
    if m:
        return {"id": m.group(2), "title": m.group(3).strip(), "ts": m.group(1).strip()}
    return None


# ════════════════════════════════════════════════════════════════════
# 合成 L0→L4 pipeline-stage 节点
# ════════════════════════════════════════════════════════════════════
def _inject_pipeline_stages(nodes: List[dict], links: List[dict]) -> None:
    for sid, name, note, state in _PIPELINE_STAGES:
        nodes.append({
            "id": sid, "name": f"{name}", "group": "pipeline", "type": "pipeline-stage",
            "path": f"CLAUDE.md#数据管道-{sid}", "fileType": None, "lines": None,
            "state": state, "module": None,
            "docs": ["CLAUDE.md"], "collapsed": False, "note": note,
        })
    for a, b in zip(_PIPELINE_STAGES, _PIPELINE_STAGES[1:]):
        links.append({"source": a[0], "target": b[0], "type": "pipeline"})


# ════════════════════════════════════════════════════════════════════
# 收尾
# ════════════════════════════════════════════════════════════════════
def _cleanup_links(nodes: List[dict], links: List[dict]) -> None:
    ids = {n['id'] for n in nodes}
    links[:] = [l for l in links
                if l.get('source') in ids and l.get('target') in ids
                and l.get('source') != l.get('target')]


def _summarize(nodes: List[dict], links: List[dict]) -> dict:
    from collections import Counter
    nc = Counter(n['type'] for n in nodes)
    lc = Counter(l['type'] for l in links)
    return {"nodes": len(nodes), "links": len(links),
            "byNodeType": dict(nc), "byEdgeType": dict(lc)}


def _compute_signature(root: Path) -> str:
    """组合各顶层目录最大 mtime + 关键 markdown mtime → md5。任一文件变动即失效缓存。"""
    parts: List[str] = []
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return "empty"
    for top in entries:
        p = root / top
        if p.is_dir():
            try:
                latest = 0.0
                for f in p.rglob('*'):
                    if f.is_file():
                        try:
                            mt = f.stat().st_mtime
                            if mt > latest:
                                latest = mt
                        except OSError:
                            pass
                parts.append(f"{top}:{int(latest)}")
            except OSError:
                pass
        elif p.is_file():
            try:
                parts.append(f"{top}:{int(p.stat().st_mtime)}")
            except OSError:
                pass
    for doc in ('AGENTS.md', 'CLAUDE.md', 'docs/revision-log.md', 'docs/todo.md'):
        p = root / doc
        if p.exists():
            try:
                parts.append(f"{doc}:{int(p.stat().st_mtime)}")
            except OSError:
                pass
    return hashlib.md5('|'.join(parts).encode('utf-8')).hexdigest()
