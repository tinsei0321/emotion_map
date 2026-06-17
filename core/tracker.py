"""
决策追踪系统 (Decision Tracking System)
═══════════════════════════════════════════════════════════
为每个功能/行为/代码块分配唯一决策 ID，运行时自动记录
行为轨迹和日志，实现 bug 的指数级快速定位。

设计原则：
  1. 非侵入式 —— 装饰器/上下文管理器，不破坏原有逻辑
  2. 零成本关闭 —— 通过 TRACKING_ENABLED 全局开关
  3. 层级 ID —— MODULE.FUNCTION.DECISION 三级编号
  4. 结构化日志 —— 统一 [TRACE] 前缀，便于 grep 解析
  5. 兼容 _safe_print —— 复用项目已有的安全打印机制

ID 命名规范：
  MOD_XXX        → 模块级（如 MOD_GOV = data_governance）
  MOD_XXX.F_NNN  → 函数级（F_001, F_002...）
  MOD_XXX.D_NNN  → 决策点（D_001, D_002... if/else 分支）

使用示例：
  from core.tracker import track, TrackContext, get_tracker

  # 方式1：装饰器
  @track("MOD_GOV.F_001", track_args=True)
  def transform_coordinates(df):
      ...

  # 方式2：上下文管理器
  with TrackContext("MOD_GOV.D_003", input_n=len(df)):
      df = do_filter(df)
      ...

  # 方式3：手动埋点
  t = get_tracker()
  t.log("MOD_GOV.D_005", status="ok", detail="filtered 3 rows")

═══════════════════════════════════════════════════════════
"""

import functools
import inspect
import os
import time
import threading
from pathlib import Path
from typing import Any, Callable, Optional, Dict

# ── 全局开关 ──
TRACKING_ENABLED = True           # 主开关
TRACKING_VERBOSE = False          # 是否输出 DEBUG 级别追踪
TRACKING_LOG_FILE = None          # 兼容占位；下方 _resolve_log_file() 覆盖默认值

# ── 安全打印（避免 GBK 崩溃，保持与项目一致）──
from core.utils import safe_print


# ── 追踪日志落盘路径解析（闭环补强 Wave1）──
# env EMOTION_TRACE_LOG 可覆盖；未设则默认 <项目根>/.trace/trace.log；设为空串则关闭落盘。
# 落盘后 debug 史可检索、可回灌 dev-notes（见 tracker.recent_errors）。
def _resolve_log_file():
    _env = os.environ.get("EMOTION_TRACE_LOG")
    if _env is not None:
        return _env  # 显式设值（含空串=关闭）
    return str(Path(__file__).resolve().parents[1] / ".trace" / "trace.log")


TRACKING_LOG_FILE = _resolve_log_file()


# ── 追踪器核心 ──

class DecisionTracker:
    """决策追踪器 —— 线程安全的单例"""

    _instance: Optional["DecisionTracker"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.enabled = TRACKING_ENABLED
        self.verbose = TRACKING_VERBOSE
        self._indent = 0             # 调用栈缩进
        self._call_stack: list = []  # 当前调用链
        self._stats: Dict[str, int] = {}  # 每 ID 调用次数统计

    # ── 公共 API ──

    def log(
        self,
        track_id: str,
        status: str = "ok",
        detail: str = "",
        input_info: str = "",
        output_info: str = "",
        elapsed_ms: float = 0.0,
        level: str = "INFO",
    ):
        """发射一条追踪日志"""
        if not self.enabled:
            return
        if level == "DEBUG" and not self.verbose:
            return

        # 统计
        self._stats[track_id] = self._stats.get(track_id, 0) + 1

        # 构建日志行
        indent = "  " * self._indent
        ts = time.strftime("%H:%M:%S", time.localtime())
        parts = [f"[TRACE] {ts} | {track_id}"]

        if status and status != "ok":
            parts.append(f"| [{status}]")
        if input_info:
            parts.append(f"| in: {input_info}")
        if output_info:
            parts.append(f"| out: {output_info}")
        if elapsed_ms > 0:
            parts.append(f"| {elapsed_ms:.1f}ms")
        if detail:
            parts.append(f"| {detail}")

        line = f"{indent}{' '.join(parts)}"
        self._emit(line)

    def enter(self, track_id: str, input_info: str = ""):
        """进入追踪块（增加缩进）"""
        if not self.enabled:
            return
        self._call_stack.append(track_id)
        self.log(track_id, status="enter", input_info=input_info)
        self._indent += 1

    def exit(self, track_id: str, output_info: str = "", elapsed_ms: float = 0.0):
        """退出追踪块（减少缩进）"""
        if not self.enabled:
            return
        self._indent = max(0, self._indent - 1)
        self.log(track_id, status="exit", output_info=output_info, elapsed_ms=elapsed_ms)
        if self._call_stack and self._call_stack[-1] == track_id:
            self._call_stack.pop()

    def error(self, track_id: str, detail: str, exception: Exception = None):
        """发射错误追踪日志"""
        exc_info = f" | {type(exception).__name__}: {exception}" if exception else ""
        self.log(track_id, status="ERR", detail=f"{detail}{exc_info}", level="ERROR")

    def warn(self, track_id: str, detail: str):
        """发射警告追踪日志"""
        self.log(track_id, status="WARN", detail=detail, level="WARN")

    def stats(self) -> Dict[str, int]:
        """返回各 ID 调用次数统计"""
        return dict(self._stats)

    def reset_stats(self):
        """重置统计"""
        self._stats.clear()

    # ── 内部 ──

    def _emit(self, line: str):
        """输出日志行"""
        safe_print(line, flush=True)
        if TRACKING_LOG_FILE:
            try:
                _lf = Path(TRACKING_LOG_FILE)
                _lf.parent.mkdir(parents=True, exist_ok=True)
                with open(_lf, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
            except Exception:
                pass  # 静默失败，不影响主流程


# ── 便捷获取 ──

def get_tracker() -> DecisionTracker:
    """获取全局追踪器实例"""
    return DecisionTracker()


# ── 装饰器 ──

def track(
    track_id: str,
    track_args: bool = False,
    track_result: bool = False,
    level: str = "INFO",
):
    """
    函数追踪装饰器。

    参数:
        track_id: 决策 ID，如 "MOD_GOV.F_001"
        track_args: 是否记录入参摘要
        track_result: 是否记录返回值摘要
        level: 日志级别
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            t = get_tracker()
            if not t.enabled:
                return func(*args, **kwargs)

            # 构建入参信息
            input_info = ""
            if track_args:
                arg_parts = []
                # 跳过 self/cls
                for i, a in enumerate(args):
                    if i == 0 and inspect.ismethod(func):
                        continue
                    arg_parts.append(_summarize(a))
                for k, v in kwargs.items():
                    arg_parts.append(f"{k}={_summarize(v)}")
                input_info = ", ".join(arg_parts) if arg_parts else ""

            t.enter(track_id, input_info=input_info)
            t_start = time.time()

            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - t_start) * 1000

                output_info = ""
                if track_result:
                    output_info = _summarize(result)

                t.exit(track_id, output_info=output_info, elapsed_ms=elapsed)
                return result

            except Exception as e:
                elapsed = (time.time() - t_start) * 1000
                t.error(track_id, f"exception after {elapsed:.1f}ms", exception=e)
                raise

        return wrapper
    return decorator


# ── 上下文管理器 ──

class TrackContext:
    """
    代码块追踪上下文管理器。

    用法:
        with TrackContext("MOD_GOV.D_003", input_n=24):
            df = do_something(df)

        with TrackContext("MOD_ANA.D_012") as ctx:
            ...
            if error:
                ctx.warn("unexpected value")
    """

    def __init__(self, track_id: str, **kwargs):
        self.track_id = track_id
        self.tracker = get_tracker()
        self._start = 0.0
        # 将 kwargs 作为输入信息
        input_parts = [f"{k}={_summarize(v)}" for k, v in kwargs.items()]
        self._input_info = ", ".join(input_parts) if input_parts else ""

    def __enter__(self):
        self.tracker.enter(self.track_id, input_info=self._input_info)
        self._start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.time() - self._start) * 1000
        if exc_type is not None:
            self.tracker.error(
                self.track_id,
                f"exception after {elapsed:.1f}ms",
                exception=exc_val,
            )
        else:
            self.tracker.exit(self.track_id, elapsed_ms=elapsed)
        return False  # 不吞异常

    def log(self, detail: str, status: str = "ok"):
        """块内手动埋点"""
        self.tracker.log(self.track_id, status=status, detail=detail)

    def warn(self, detail: str):
        """块内警告"""
        self.tracker.warn(self.track_id, detail=detail)


# ── 辅助函数 ──

def _summarize(obj: Any) -> str:
    """生成对象的简短摘要（避免日志膨胀）"""
    if obj is None:
        return "None"
    if isinstance(obj, bool):
        return str(obj)
    if isinstance(obj, (int, float)):
        if isinstance(obj, float):
            return f"{obj:.3g}"
        return str(obj)
    if isinstance(obj, str):
        if len(obj) <= 40:
            return repr(obj)
        return repr(obj[:37] + "...")
    if hasattr(obj, '__len__'):
        return f"len={len(obj)}"
    if hasattr(obj, '__class__'):
        return f"<{obj.__class__.__name__}>"
    return str(type(obj))


# ── 模块级快捷函数 ──

def trace_enter(track_id: str, **kwargs):
    """快捷：进入追踪点（无需 with 语句）"""
    t = get_tracker()
    input_info = ", ".join(f"{k}={_summarize(v)}" for k, v in kwargs.items())
    t.enter(track_id, input_info=input_info)


def trace_exit(track_id: str, **kwargs):
    """快捷：退出追踪点"""
    t = get_tracker()
    output_info = ", ".join(f"{k}={_summarize(v)}" for k, v in kwargs.items())
    t.exit(track_id, output_info=output_info)


def trace_log(track_id: str, detail: str = "", status: str = "ok"):
    """快捷：埋点日志"""
    get_tracker().log(track_id, status=status, detail=detail)


def trace_error(track_id: str, detail: str, exc: Exception = None):
    """快捷：错误日志"""
    get_tracker().error(track_id, detail=detail, exception=exc)


def trace_warn(track_id: str, detail: str):
    """快捷：警告日志"""
    get_tracker().warn(track_id, detail=detail)


# ── 调试辅助：从日志回溯调用链 ──

def replay_from_log(log_file: str, target_track_id: str = None):
    """
    从日志文件重建调用链（用于事后分析）。

    返回: List[Dict] 按时间排序的追踪记录
    """
    records = []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '[TRACE]' not in line:
                    continue
                if target_track_id and target_track_id not in line:
                    continue
                # 简单解析
                parts = line.strip().split('|')
                record = {
                    'raw': line.strip(),
                    'ts': parts[0].replace('[TRACE]', '').strip() if parts else '',
                    'track_id': parts[1].strip() if len(parts) > 1 else '',
                }
                records.append(record)
    except FileNotFoundError:
        safe_print(f"[WARN] Log file not found: {log_file}")
    return records


def recent_errors(log_file: str = None, limit: int = 50) -> list:
    """
    读取追踪日志中最近的 ERR/WARN 行（闭环补强 Wave4：供 SessionEnd
    摘要回灌 / dev-notes 沉淀，让 debug 史不再蒸发）。

    参数:
        log_file: 日志路径；None 则用当前 TRACKING_LOG_FILE
        limit: 最多返回最近 N 行（0=全部）

    返回: List[str] 原始日志行（按时间正序，取末尾 limit 条）
    """
    path = log_file or TRACKING_LOG_FILE
    if not path:
        return []
    hits = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if '[ERR]' in line or '[WARN]' in line:
                    hits.append(line.rstrip('\n'))
    except FileNotFoundError:
        return []
    except Exception:
        return []
    return hits[-limit:] if limit else hits


# ── 模块注册表：记录项目中所有已注册的追踪 ID ──

_TRACKING_REGISTRY: Dict[str, str] = {}  # track_id → description


def register_track_id(track_id: str, description: str):
    """注册一个追踪 ID 到全局注册表"""
    _TRACKING_REGISTRY[track_id] = description


def list_track_ids() -> Dict[str, str]:
    """列出所有已注册的追踪 ID"""
    return dict(_TRACKING_REGISTRY)


def lookup_track_id(track_id: str) -> str:
    """查找追踪 ID 的描述"""
    return _TRACKING_REGISTRY.get(track_id, "unknown")


# ── 合规性验证（Reviewer 审查时使用）──

def validate_tracking_compliance(file_path: str) -> dict:
    """
    检查 Python 文件中追踪埋点的合规性。

    检查项：
      1. 所有公开函数（非 _ 前缀）是否有 @track() 装饰
      2. >5 行的 if/for/while/try 块是否有 TrackContext
      3. I/O 操作（open/read_csv/to_csv/requests）是否有追踪埋点
      4. except 块是否有 trace_error()

    返回:
        {
            "file": str,
            "public_functions": {"total": int, "tracked": int, "missing": [...]},
            "large_blocks": {"total": int, "tracked": int, "missing": [...]},
            "io_operations": {"total": int, "tracked": int, "missing": [...]},
            "except_blocks": {"total": int, "with_trace_error": int, "missing": [...]},
            "issues": [...],
            "verdict": "PASS" | "FAIL"
        }
    """
    import ast
    import os

    result = {
        "file": file_path,
        "public_functions": {"total": 0, "tracked": 0, "missing": []},
        "large_blocks": {"total": 0, "tracked": 0, "missing": []},
        "io_operations": {"total": 0, "tracked": 0, "missing": []},
        "except_blocks": {"total": 0, "with_trace_error": 0, "missing": []},
        "issues": [],
        "verdict": "PASS",
    }

    if not os.path.exists(file_path):
        result["issues"].append(f"File not found: {file_path}")
        result["verdict"] = "FAIL"
        return result

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        result["issues"].append(f"Syntax error: {e}")
        result["verdict"] = "FAIL"
        return result

    # ── 辅助：检查节点所在行是否在 TrackContext 或 @track 装饰器内部 ──
    def _has_track_decorator(node):
        """检查函数是否有 @track 装饰器"""
        for dec in getattr(node, 'decorator_list', []):
            if isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name) and dec.func.id == 'track':
                    return True
                if isinstance(dec.func, ast.Attribute) and dec.func.attr == 'track':
                    return True
        return False

    def _source_lines(start_lineno, end_lineno):
        """获取节点对应的源码行"""
        lines = source.split('\n')
        return '\n'.join(lines[start_lineno-1:end_lineno])

    # ── 检查 1: 公开函数是否有 @track ──
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('_'):
                continue  # 跳过私有函数
            # 跳过类内部的 __init__ 等 dunder 方法（它们通常不需要追踪）
            if node.name.startswith('__') and node.name.endswith('__'):
                continue
            result["public_functions"]["total"] += 1
            if _has_track_decorator(node):
                result["public_functions"]["tracked"] += 1
            else:
                result["public_functions"]["missing"].append(
                    f"Line {node.lineno}: {node.name}()"
                )

    # ── 检查 2: >5 行的 if/for/while/try 块 ──
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
            if hasattr(node, 'end_lineno') and node.end_lineno:
                n_lines = node.end_lineno - node.lineno + 1
                if n_lines > 5:
                    result["large_blocks"]["total"] += 1
                    # 简单启发式：检查源码中附近是否有 TrackContext
                    context_start = max(0, node.lineno - 3)
                    context_end = node.end_lineno + 1
                    nearby = _source_lines(context_start, context_end)
                    has_tc = 'TrackContext' in nearby
                    if has_tc:
                        result["large_blocks"]["tracked"] += 1
                    else:
                        node_type = type(node).__name__.lower()
                        result["large_blocks"]["missing"].append(
                            f"Line {node.lineno}: {node_type} block ({n_lines} lines)"
                        )

    # ── 检查 3: I/O 操作 ──
    io_patterns = ['open(', 'pd.read_csv', 'pd.read_excel', 'df.to_csv',
                   'df.to_excel', 'json.load', 'json.dump', 'requests.get',
                   'requests.post', 'aiohttp.', 'sqlite3.']
    lines = source.split('\n')
    for i, line in enumerate(lines, 1):
        for pat in io_patterns:
            if pat in line:
                result["io_operations"]["total"] += 1
                # 检查前后 5 行是否有追踪相关调用
                check_start = max(0, i - 5)
                check_end = min(len(lines), i + 5)
                nearby = '\n'.join(lines[check_start:check_end])
                has_tracking = any(t in nearby for t in
                    ['TrackContext', 'trace_log', 'trace_enter', '@track', 't.log', 't.enter'])
                if has_tracking:
                    result["io_operations"]["tracked"] += 1
                else:
                    result["io_operations"]["missing"].append(
                        f"Line {i}: {line.strip()[:60]}"
                    )
                break  # 每行只计一次

    # ── 检查 4: except 块是否有 trace_error ──
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            result["except_blocks"]["total"] += 1
            except_code = _source_lines(node.lineno,
                                        node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else node.lineno + 3)
            if 'trace_error' in except_code:
                result["except_blocks"]["with_trace_error"] += 1
            else:
                result["except_blocks"]["missing"].append(
                    f"Line {node.lineno}: except block"
                )

    # ── 汇总 issues ──
    if result["public_functions"]["missing"]:
        result["issues"].append(
            f"PUBLIC_FUNC: {len(result['public_functions']['missing'])} untracked: "
            + ", ".join(result["public_functions"]["missing"])
        )
    if result["large_blocks"]["missing"]:
        result["issues"].append(
            f"LARGE_BLOCK: {len(result['large_blocks']['missing'])} untracked: "
            + ", ".join(result["large_blocks"]["missing"])
        )
    if result["io_operations"]["missing"]:
        result["issues"].append(
            f"IO_OP: {len(result['io_operations']['missing'])} untracked: "
            + ", ".join(result["io_operations"]["missing"])
        )
    if result["except_blocks"]["missing"]:
        result["issues"].append(
            f"EXCEPT: {len(result['except_blocks']['missing'])} missing trace_error: "
            + ", ".join(result["except_blocks"]["missing"])
        )

    if result["issues"]:
        result["verdict"] = "FAIL"

    return result


def print_compliance_report(file_path: str) -> None:
    """
    打印合规性报告（供 Reviewer 直接使用）。

    用法:
        from core.tracker import print_compliance_report
        print_compliance_report("SCRIPT/data_governance.py")
    """
    r = validate_tracking_compliance(file_path)
    safe_print(f"\n{'='*60}")
    safe_print(f"  Tracking Compliance Report: {r['file']}")
    safe_print(f"{'='*60}")
    safe_print(f"  Verdict: {r['verdict']}")
    safe_print(f"  Public Functions: {r['public_functions']['tracked']}/{r['public_functions']['total']} tracked")
    safe_print(f"  Large Blocks:     {r['large_blocks']['tracked']}/{r['large_blocks']['total']} tracked")
    safe_print(f"  I/O Operations:   {r['io_operations']['tracked']}/{r['io_operations']['total']} tracked")
    safe_print(f"  Except Blocks:    {r['except_blocks']['with_trace_error']}/{r['except_blocks']['total']} with trace_error")
    if r['issues']:
        safe_print(f"\n  [ISSUES]")
        for issue in r['issues']:
            safe_print(f"    - {issue}")
    safe_print(f"{'='*60}\n")
