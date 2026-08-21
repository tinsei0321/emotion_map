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

PT-CB10 C2-2：applied/ 归档 7 天 TTL 清理（保留 T16 归档机制·仅删过期副本）。

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

register_track_id('MOD_AIQA.F_029', 'render 收件箱 watcher：扫描新 spec→推 SSE 队列（坏文件跳过并 log）·高频扫描（1s 周期）免 @track（PT-CB10 C2-8 纪律·见 AGENTS 埋点规则豁免条）')
register_track_id('MOD_AIQA.F_030', 'render dataset 取数：preset/点层→FeatureCollection·>2000 降级')

router = APIRouter()

INBOX_DIR = os.path.join(REPO, 'DATA', 'exports', 'render_inbox')
_BACKLOG = []
_BACKLOG_LOCK = threading.Lock()
_SEEN = set()
# PT-CB7 T21：SSE 扇出——每个连接独立队列，watcher 向全体广播。
# 治单队列争用：多个地图页共用一个 queue 时，spec 只被其中一个连接消费，
# 用户当前页永收不到新图（只能 F5 重连后 backlog 重放才见）。
_SUBSCRIBERS = []
_SUB_LOCK = threading.Lock()

_UNKNOWN_HINT = '未知层 id·调用 list_data 查看清单'

# C2-2：applied/ 归档保留天数（超期即清·留痕窗口足够回溯又不无限堆积）。
_APPLIED_TTL_DAYS = 7
# C2-4：dataset 端点属性白名单（默认拒绝）——只放行名称/极性/领域/指标类字段，
#   禁办件编号等准标识字段随渲染通道外流（脱敏铁律 7 同源）。
_DATASET_PROP_KEYS = {
    # 名称类（边界/要素可读名）
    'name', 'Name', 'NAME', 'MC', '区名', '社区', '街道', '行政区', '单元',
    # 极性/情绪类
    'polarity', 'polarity_hint', 'polarity_index', 'score', 'score_mean',
    'l1_confidence', 'emotion_intensity',
    # 领域/归因类
    'domain', 'domain_top', 'element', 'element_top', 'topic', 'issue_label',
    # 指标/地点类
    'point_count', 'place_name', 'place_name_source', 'poi_names', 'poi_count',
    # 口径类（K-02 全覆盖口径必备 来源 字段）
    '来源',
}
_DATASET_PROP_PREFIXES = ('polarity', 'score', 'domain', 'element', 'poi', 'place')


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


def _cleanup_applied(inbox_dir, ttl_days=_APPLIED_TTL_DAYS):
    """C2-2：applied/ 归档 TTL 清理——删除超期已消费 spec（保留现归档机制）。返回删除数。"""
    applied_dir = os.path.join(inbox_dir, 'applied')
    if not os.path.isdir(applied_dir):
        return 0
    cutoff = time.time() - ttl_days * 86400
    removed = 0
    for fp in glob.glob(os.path.join(applied_dir, '*.json')):
        try:
            if os.path.getmtime(fp) < cutoff:
                os.remove(fp)
                removed += 1
        except OSError as exc:
            _safe_print(f'[WARN] render_inbox TTL 清理失败（不阻塞）: {os.path.basename(fp)}: {exc}', file=sys.stderr)
    return removed


def _filter_dataset_props(fc):
    """C2-4：dataset 属性白名单过滤（默认拒绝·几何不动）。返回被剔除的字段名集合（可观测）。"""
    dropped = set()
    for f in fc.get('features') or []:
        props = f.get('properties')
        if not isinstance(props, dict):
            continue
        kept = {}
        for k, v in props.items():
            if k in _DATASET_PROP_KEYS or k.startswith(_DATASET_PROP_PREFIXES):
                kept[k] = v
            else:
                dropped.add(k)
        f['properties'] = kept
    return dropped


def _publish(spec):
    """T21：向所有活跃 SSE 连接广播 spec（死队列即摘除）。"""
    with _SUB_LOCK:
        dead = []
        for q in _SUBSCRIBERS:
            try:
                q.put_nowait(spec)
            except Exception:
                dead.append(q)
        for q in dead:
            _SUBSCRIBERS.remove(q)


def _watch_loop():
    ticks = 0
    while True:
        try:
            collect = queue.Queue()
            scan_inbox(INBOX_DIR, _SEEN, collect, _BACKLOG)
            while not collect.empty():
                _publish(collect.get_nowait())
            # C2-2：首轮即清一次 + 之后每小时一次（扫描周期 1s·3600 轮）。
            if ticks == 0 or ticks % 3600 == 0:
                removed = _cleanup_applied(INBOX_DIR)
                if removed:
                    _safe_print(f'[OK] render_inbox applied/ TTL 清理 {_APPLIED_TTL_DAYS} 天超期 {removed} 件', file=sys.stderr)
            ticks += 1
        except Exception as exc:
            _safe_print(f'[WARN] render watcher 扫描异常: {exc}', file=sys.stderr)
        time.sleep(1)


def _sse_stream():
    my_q = queue.Queue()
    with _SUB_LOCK:
        _SUBSCRIBERS.append(my_q)
    try:
        # 根治图层残留（用户反复报告）：连接时只推最新 1 条 spec（非 20 条全量重放）
        # ——前端 _clearDshLayers 会清旧层再铺这条·页面刷新只恢复最新图不复活历史
        with _BACKLOG_LOCK:
            if _BACKLOG:
                yield _sse_event(_BACKLOG[-1])
        while True:
            try:
                spec = my_q.get(timeout=15)
            except queue.Empty:
                yield ': ping\n\n'
                continue
            yield _sse_event(spec)
    finally:
        with _SUB_LOCK:
            if my_q in _SUBSCRIBERS:
                _SUBSCRIBERS.remove(my_q)


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
        # C2-4：属性白名单过滤（办件编号等准标识字段不外流·被剔除字段名可观测）。
        dropped = _filter_dataset_props(fc)
        if dropped:
            _safe_print(f'[OK] render dataset {dataset_id}: 白名单外字段已剔除 {sorted(dropped)}', file=sys.stderr)
        return {'ok': True, 'dataset_id': dataset_id, 'geojson': fc, 'count': count}
    except (KeyError, FileNotFoundError, ValueError) as exc:
        return {'ok': False, 'hint': f'{_UNKNOWN_HINT}（{exc}）'}
    except Exception as exc:
        return {'ok': False, 'hint': f'render dataset 失败: {exc}'}


# 模块导入即起后台 watcher（daemon·目录不存在自动建）。
_thread = threading.Thread(target=_watch_loop, name='render-inbox-watcher', daemon=True)
_thread.start()
