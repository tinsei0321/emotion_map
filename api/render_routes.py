# -*- coding: utf-8 -*-
"""PT-CB6 P2 · 投递通道：render_inbox watcher + SSE 流 + dataset 取数端点。

通道语义：
  dsh 会话（MCP render_spec）→ 写 DATA/exports/render_inbox/<spec_id>.json
  → 本模块后台 watcher 线程扫描新文件（按 spec_id 文件名排序·推送后归档）
  → queue.Queue 推给 SSE 连接（先补最近 20 条 backlog·再持续流式）
  → 8080 前端 render_client.js 消费 spec 取数渲染。

PT-CB7 T16：spec 推送成功后移入 applied/ 归档（glob 只扫一级 *.json）——
  治历史图层残留：_SEEN 是内存态，serve 重启（start.bat 杀旧起新）后首轮扫描
  会把存量 spec 全量重推进 backlog → 新页面复活历史层；归档后重启不再重放。

纪律：
  - 纯只读（dataset 端点只解析/降级·不写盘）；
  - watcher 单条坏文件 log 一行并跳过（A9：禁宽 except 静默吞线程）；
  - 追踪：MOD_AIQA.F_029（watcher 扫描）、MOD_AIQA.F_030（dataset 取数）。
"""
import glob
import json
import os
import queue
import sys
import threading
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from core.tracker import register_track_id, track

register_track_id('MOD_AIQA.F_029', 'render 收件箱 watcher：扫描新 spec→推 SSE 队列（坏文件跳过并 log）')
register_track_id('MOD_AIQA.F_030', 'render dataset 取数：preset/点层→FeatureCollection·>2000 降级')

router = APIRouter()

INBOX_DIR = os.path.join(REPO, 'DATA', 'exports', 'render_inbox')
_SPEC_QUEUE = queue.Queue()
_BACKLOG = []
_BACKLOG_LOCK = threading.Lock()
_SEEN = set()

_UNKNOWN_HINT = '未知层 id·调用 list_data 查看清单'


def _safe_print(msg, file=None):
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'), file=file)


def _sse_event(spec):
    return f'event: spec\ndata: {json.dumps(spec, ensure_ascii=False)}\n\n'


def scan_inbox(inbox_dir, seen, out_queue, backlog):
    """扫描收件箱新文件→入队+backlog，推送成功即归档 applied/（T16：重启不重放）。坏文件 log 后跳过。返回本次入队数。"""
    os.makedirs(inbox_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(inbox_dir, '*.json')))
    pushed = 0
    for fp in files:
        base = os.path.basename(fp)
        if base in seen:
            continue
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                spec = json.load(fh)
            if spec.get('spec_version') != 1:
                raise ValueError(f'spec_version={spec.get("spec_version")!r}')
            if not isinstance(spec.get('kind'), str):
                raise ValueError('kind 缺失')
            if not isinstance(spec.get('origin'), dict):
                raise ValueError('origin 缺失')
        except Exception as exc:
            _safe_print(f'[WARN] render_inbox 坏文件跳过: {base}: {exc}', file=sys.stderr)
            continue
        seen.add(base)
        out_queue.put(spec)
        backlog.append(spec)
        del backlog[:-20]
        pushed += 1
        # T16：推送成功后归档（一级 glob 不再扫到·serve 重启不重放·留痕可查）
        try:
            applied_dir = os.path.join(inbox_dir, 'applied')
            os.makedirs(applied_dir, exist_ok=True)
            os.replace(fp, os.path.join(applied_dir, base))
        except OSError as exc:
            _safe_print(f'[WARN] render_inbox 归档失败（不阻塞）: {base}: {exc}', file=sys.stderr)
    return pushed


def _watch_loop():
    while True:
        try:
            scan_inbox(INBOX_DIR, _SEEN, _SPEC_QUEUE, _BACKLOG)
        except Exception as exc:
            _safe_print(f'[WARN] render watcher 扫描异常: {exc}', file=sys.stderr)
        time.sleep(1)


def _sse_stream():
    with _BACKLOG_LOCK:
        for spec in list(_BACKLOG):
            yield _sse_event(spec)
    while True:
        try:
            spec = _SPEC_QUEUE.get(timeout=15)
        except queue.Empty:
            yield ': ping\n\n'
            continue
        yield _sse_event(spec)


@router.get('/render/stream')
def render_stream():
    """SSE 规格流：先推 backlog（最近 20 条）再持续推新 spec；每 15s 心跳注释。"""
    return StreamingResponse(
        _sse_stream(),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@router.get('/render/dataset/{dataset_id}')
@track('MOD_AIQA.F_030', track_args=False)
def render_dataset(dataset_id: str):
    """preset 边界或点层 → GeoJSON FeatureCollection（>2000 要素降级提示）。"""
    try:
        from core.geo_registry import list_boundaries, resolve_boundary, resolve_points

        boundary_ids = {b.get('id') for b in list_boundaries()}
        if dataset_id in boundary_ids:
            gdf = resolve_boundary(dataset_id)
        else:
            gdf = resolve_points(dataset_id)
        count = int(len(gdf))
        if count > 2000:
            return {'ok': False, 'hint': '要素过多·请用分析工具聚合后再渲'}
        fc = gdf.__geo_interface__
        return {'ok': True, 'dataset_id': dataset_id, 'geojson': fc, 'count': count}
    except (KeyError, FileNotFoundError, ValueError) as exc:
        return {'ok': False, 'hint': f'{_UNKNOWN_HINT}（{exc}）'}
    except Exception as exc:
        return {'ok': False, 'hint': f'render dataset 失败: {exc}'}


# 模块导入即起后台 watcher（daemon·目录不存在自动建）。
_thread = threading.Thread(target=_watch_loop, name='render-inbox-watcher', daemon=True)
_thread.start()
