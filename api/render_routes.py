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
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

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

# ── PT-CB15 PROMOTE P2-9（C-4）：watcher 竞争锁——同机只允许一个实例消费 inbox ──
# 根因：双后端实例（8000/8001）的 watcher 同扫一个 render_inbox，spec 被先到者消费
# 推给它自己的 SSE 订阅者 → 另一实例的页面永远收不到（spike Q4 实证「图亮在隔壁屏幕」）。
# 修法（最轻量）：pidfile 锁——锁文件记持有者 pid·pid 死则抢占；未持有者不扫描不消费，
# 消费源全局唯一 → 错向根治。评审注记：跨进程扇出需 IPC·重方案不采；
# pid 复用风险可接受（锁持有者死→1s 内重抢·误判窗口极小）。
_PIDLOCK = os.path.join(INBOX_DIR, '.watcher.pid')


def _pid_alive(pid):
    if pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _try_claim_watch():
    """竞争锁持有判定：锁空/自持/持锁者已死 → 抢占并返 True；他活实例持锁 → False（本实例让出）。"""
    try:
        os.makedirs(INBOX_DIR, exist_ok=True)
        if os.path.isfile(_PIDLOCK):
            try:
                with open(_PIDLOCK, 'r') as fh:
                    held = int((fh.read() or '0').strip() or 0)
            except Exception:
                held = 0
            if held and held != os.getpid() and _pid_alive(held):
                return False
        tmp = f'{_PIDLOCK}.tmp.{os.getpid()}'
        with open(tmp, 'w') as fh:
            fh.write(str(os.getpid()))
        os.replace(tmp, _PIDLOCK)
        return True
    except OSError as exc:
        _safe_print(f'[WARN] render watcher 竞争锁异常（按持有处理）: {exc}', file=sys.stderr)
        return True

# C2-2：applied/ 归档保留天数（超期即清·留痕窗口足够回溯又不无限堆积）。
_APPLIED_TTL_DAYS = 7
# C2-4：dataset 端点属性白名单（默认拒绝）——只放行名称/极性/领域/指标类字段，
#   禁办件编号等准标识字段随渲染通道外流（脱敏铁律 7 同源）。
#   PT-CB11 B3-1：键表与前缀迁入 core/render_policy.py（单一权威源·与 MCP 侧校验共用）；
#   preset 的 nameField/renderFields 声明字段按 dataset 增量放行（含中文指标字段·治注入层灰框根因①）。
from core.render_policy import DATASET_PROP_KEYS as _DATASET_PROP_KEYS
from core.render_policy import preset_render_fields


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


def _filter_dataset_props(fc, extra_keys=None):
    """C2-4+B3-1：dataset 属性白名单过滤（默认拒绝·几何不动）。

    extra_keys=preset 声明字段（nameField+renderFields·含中文指标）增量放行。
    返回被剔除的字段名集合（可观测）。"""
    extra = set(extra_keys or ())
    dropped = set()
    for f in fc.get('features') or []:
        props = f.get('properties')
        if not isinstance(props, dict):
            continue
        kept = {}
        for k, v in props.items():
            if (k in _DATASET_PROP_KEYS or k in extra):
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
            # P2-9：竞争锁——同机已有活实例持有消费权则本实例让出（每轮重查·持锁者死 1s 内接管）
            if not _try_claim_watch():
                ticks += 1
                if ticks % 60 == 1:   # 1s 周期·每分钟提醒一次（运维纪律：同机只跑一个后端）
                    _safe_print('[WARN] render watcher 让出消费权（另一后端实例持锁）——同机只跑一个后端（PT-CB15 P2-9）',
                                file=sys.stderr)
                time.sleep(1)
                continue
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
        # B3-1：preset 声明字段（nameField+renderFields）增量放行——治中文指标字段被误剔。
        dropped = _filter_dataset_props(fc, extra_keys=preset_render_fields(dataset_id))
        if dropped:
            _safe_print(f'[OK] render dataset {dataset_id}: 白名单外字段已剔除 {sorted(dropped)}', file=sys.stderr)
        return {'ok': True, 'dataset_id': dataset_id, 'geojson': fc, 'count': count}
    except (KeyError, FileNotFoundError, ValueError) as exc:
        return {'ok': False, 'hint': f'{_UNKNOWN_HINT}（{exc}）'}
    except Exception as exc:
        return {'ok': False, 'hint': f'render dataset 失败: {exc}'}


# ── PT-CB11 A-4a：/version 版本徽章端点（治「修没修好」自查·页面角标数据源）──
def _build_version_info():
    """git commit/branch 于启动时解析一次（subprocess·不每请求跑 git）。

    不可用降级为空串 + stderr WARN（A9：具体捕获 OSError/SubprocessError·不静默吞）。
    """
    info = {'commit': '', 'branch': '',
            'startup': datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}
    for key, args in (('commit', ['git', 'rev-parse', '--short', 'HEAD']),
                      ('branch', ['git', 'rev-parse', '--abbrev-ref', 'HEAD'])):
        try:
            r = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                info[key] = r.stdout.strip()
            else:
                _safe_print(f'[WARN] /version {key} 获取失败（rc={r.returncode}·降级空串）: {r.stderr.strip()[:80]}',
                            file=sys.stderr)
        except (OSError, subprocess.SubprocessError) as exc:
            _safe_print(f'[WARN] /version {key} 获取异常（降级空串）: {exc}', file=sys.stderr)
    return info


_VERSION_INFO = _build_version_info()   # 启动时缓存一次（模块导入即服务装配期）


@router.get('/version')
def version():
    """版本徽章：{"commit","branch","startup"}——commit/branch 启动时缓存，startup 为本次进程启动时间。"""
    return _VERSION_INFO


# 模块导入即起后台 watcher（daemon·目录不存在自动建）。
_thread = threading.Thread(target=_watch_loop, name='render-inbox-watcher', daemon=True)
_thread.start()
