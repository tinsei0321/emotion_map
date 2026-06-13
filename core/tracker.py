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
import time
import threading
from typing import Any, Callable, Optional, Dict

# ── 全局开关 ──
TRACKING_ENABLED = True           # 主开关
TRACKING_VERBOSE = False          # 是否输出 DEBUG 级别追踪
TRACKING_LOG_FILE = None          # 若设置路径，同时写入文件（None=仅 stderr）

# ── 安全打印（避免 GBK 崩溃，保持与项目一致）──

def _safe_print(*args, **kwargs):
    """安全打印——兼容 Windows GBK 终端"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for a in args:
            if isinstance(a, str):
                safe_args.append(a.encode('ascii', errors='replace').decode('ascii'))
            else:
                safe_args.append(a)
        print(*safe_args, **kwargs)


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
        _safe_print(line, flush=True)
        if TRACKING_LOG_FILE:
            try:
                with open(TRACKING_LOG_FILE, 'a', encoding='utf-8') as f:
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
        _safe_print(f"[WARN] Log file not found: {log_file}")
    return records


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
