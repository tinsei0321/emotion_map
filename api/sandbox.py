"""P3 code-exec 沙箱：隔离执行 agent 生成的 Python 数据分析代码。

设计要点（承重安全代码，改动需人审 + 全单测通过）：
1. subprocess 隔离 —— 用户代码在独立 Python 进程跑（``-I`` 隔离 PYTHON* env / user site），
   父进程只读 stdout/stderr/退出码，不共享内存；崩溃不影响主服务。
2. import 白名单 —— PRELUDE 重写 ``builtins.__import__``，仅放行数据分析所需库；
   非白名单模块用 frame-based trust 区分「用户脚本直接 import」（拦）与
   「库内部 lazy-import 传递依赖」（放行，如 matplotlib savefig 拉 io/socket），
   避免 whitelisting 危险库或误伤库自身的依赖链。
3. 超时 kill —— Popen + communicate(timeout) + 失败时 taskkill /T（Windows）/ killpg（POSIX）
   杀整棵进程树，死循环不会卡死调用方。
4. 写区隔离 —— tempfile.mkdtemp() 作 cwd，matplotlib savefig / to_csv 默认落在此；
   artifacts 扫描此目录按扩展名归类。
5. artifacts —— 执行后按扩展名归类（geojson/image/data）回传。

红线（红线自查）：
- ``SAFE_READY`` 默认 False。单测全过 + 人审后才置 True，
  届时才在 run_routes.py 挂 /run。本会话不写 run_routes.py、不动 api/main.py、不挂任何 HTTP 端点。
- 代码里没有任何地方把 SAFE_READY 设 True。

已知局限（future work，需 OS 级沙箱 chroot/seccomp 或 open-wrapper allowlist 才能根治）：
- ``open`` builtin 不拦（pandas/csv 出图需读写文件）；绝对路径写不在 cwd 内未被硬拦，
  仅靠 subprocess 同权限隔离 + cwd 相对路径约束。文件级逃逸硬化留待后续迭代。
- 同用户权限运行，非 OS 级隔离；生产部署应叠加容器/用户隔离。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

SAFE_READY: bool = False  # 红线开关：False=不挂 /run。绝不在此文件设 True。

# ---------------------------------------------------------------------------
# 白名单（top-level 模块名）。
# 子模块（matplotlib.pyplot / scipy.stats / numpy.linalg / shapely.geometry）
# 由 guard 的 top-name 规则自动放行（top = name.split('.')[0]）。
# 显式不放：os / sys / subprocess / socket / ctypes / pickle / importlib /
#           threading / multiprocessing / builtins —— 防命令注入、网络外联、绕过 guard。
# 路径操作用 pathlib（标准库，安全）替代 os。
# ---------------------------------------------------------------------------
WHITELIST: frozenset[str] = frozenset({
    # 数据分析主力（requirements.txt 已声明；h3 当前环境未装则 import 时自然 ImportError）
    'pandas', 'numpy', 'geopandas', 'shapely', 'scipy',
    'matplotlib', 'esda', 'libpysal', 'h3',
    # 标准库白名单
    'math', 'statistics', 'itertools', 'collections',
    'json', 'datetime', 're', 'pathlib',
})

# ---------------------------------------------------------------------------
# PRELUDE：注入到生成 script 顶部。安装 import guard + 加载 data_refs。
# 两个 format 字段：{whitelist}（白名单 set 字面量）、{data_refs_path}（pickle 路径字面量）。
# PRELUDE 自身需 builtins/sys/pickle —— 在 guard 安装前导入（走原始 __import__）。
# 守卫策略 = frame-based trust：
#   - 白名单 top-level（pandas/matplotlib/...）→ 直接放行。
#   - 非白名单模块：检查「直接发起 import 的帧」的源文件。
#       * 源文件 = 用户脚本（_sb_user.py）→ 拦（用户直接 import 危险模块）。
#       * 源文件 = 库文件 / <frozen importlib> → 放行（库的传递依赖，如 matplotlib
#         在 savefig 时 lazy-import io/socket —— 库源已审计，非用户输入）。
#   这区分了「用户主动 import socket」（拦）与「matplotlib 内部 lazy-import socket」（放），
#   是 inside-flag 做不到的（lazy import 发生在用户代码执行期、库函数帧里）。
# ---------------------------------------------------------------------------
_PRELUDE_TEMPLATE = r'''# ===== SANDBOX PRELUDE (auto-generated, do not edit) =====
import builtins as _sb_builtins
import sys as _sb_sys
import pickle as _sb_pickle

# ---- 1) 加载 data_refs（父进程 pickle 的可信对象）。
# 必须在 guard 安装前做：unpickle 会触发各种 import（如 builtins/pandas/_libs），
# 这些是可信数据的重建需求，不应被 guard 拦。guard 只管用户代码（在下方之后运行）。----
_SB_DATA_REFS = r"{data_refs_path}"
if _SB_DATA_REFS:
    try:
        with open(_SB_DATA_REFS, 'rb') as _sb_f:
            _sb_loaded = _sb_pickle.load(_sb_f)
        if isinstance(_sb_loaded, dict):
            for _sb_k, _sb_v in _sb_loaded.items():
                globals()[_sb_k] = _sb_v
    except FileNotFoundError:
        pass
    except Exception:
        pass   # 加载失败 → 对应 name 不绑定；用户代码会 NameError（可观察，不静默吞安全事件）

# ---- 2) 安装 import 守卫（之后所有 USER CODE 的 import 都过 guard）----
_sb_orig_import = _sb_builtins.__import__
_SB_USER_SCRIPT = __file__


def _sb_guard(name, globals=None, locals=None, fromlist=(), level=0,
              _getframe=_sb_sys._getframe, _orig=_sb_orig_import,
              _wl=frozenset({whitelist!r}), _user_script=_SB_USER_SCRIPT):
    """import 守卫：白名单放行；非白名单看直接 importer 是不是用户脚本。"""
    top = name.split('.')[0] if name else ''
    if top in _wl:
        return _orig(name, globals, locals, fromlist, level)
    # 非白名单：定位直接发起 import 的帧（IMPORT_NAME 的当前帧）
    try:
        _f = _getframe(1)
        _importer = _f.f_code.co_filename if _f is not None else ''
    except (ValueError, AttributeError):
        _importer = ''
    if _importer == _user_script:
        raise ImportError('[sandbox] 禁止导入: ' + name + '（不在白名单内）')
    # 库帧 / frozen importlib → 传递依赖，放行
    return _orig(name, globals, locals, fromlist, level)


_sb_builtins.__import__ = _sb_guard

# ---- 3) 清理 PRELUDE 私有符号。guard 依赖（_getframe/_orig/_wl/_user_script）已绑进闭包
# 默认参数，故可删全局 _sb_sys/_sb_orig_import，避免用户态 _sb_sys.modules['os'] 这类 trivial 绕过。
# 残余风险（文档化）：__import__.__defaults__/__closure__ 反射仍可取回 _orig —— 纯 Python 沙箱
# 的固有限制，根治需 OS 级隔离（容器/独立低权用户/seccomp），由部署层叠加。----
for _sb_n in ('_sb_pickle', '_sb_builtins', '_sb_sys', '_sb_orig_import',
              '_sb_loaded', '_sb_f', '_sb_k', '_sb_v', '_sb_n', '_SB_DATA_REFS',
              '_SB_USER_SCRIPT'):
    try:
        del globals()[_sb_n]
    except KeyError:
        pass
# ===== END PRELUDE =====

'''

# artifacts 扩展名 → 类型归类
_ARTIFACT_EXT: dict[str, str] = {
    '.geojson': 'geojson',
    '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
    '.svg': 'image', '.pdf': 'image',
    '.csv': 'data',
}


def _kill_tree(pid: int) -> None:
    """杀掉 pid 及其全部子进程（Windows=taskkill /T /F；POSIX=killpg SIGKILL）。

    幂等、吞异常——仅用于超时兜底，失败不应影响调用流。
    """
    try:
        if os.name == 'nt':
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(pid)],
                capture_output=True, timeout=10,
            )
        else:
            try:
                os.killpg(os.getpgid(pid), 9)
            except (ProcessLookupError, PermissionError):
                pass
    except Exception:
        pass


def _build_env() -> dict:
    """subprocess 环境：拷贝 os.environ，强制 Agg 后端（无显示环境出图），剥离 PYTHON* env。

    ``-I`` 已忽略 PYTHON* env，此处剥离为双保险（防 PYTHONPATH 投毒等）。
    保留 PYTHONIOENCODING（编码稳定）。
    """
    env = dict(os.environ)
    env['MPLBACKEND'] = 'Agg'
    # 强制子进程 stdio 用 utf-8（匹配 Popen 的 encoding='utf-8' 解码，避免 Windows
    # cp936 mojibake 让 error 摘要乱码）。PYTHONIOENCODING 不会被 -I 忽略（非 PYTHON* site 项）。
    env['PYTHONIOENCODING'] = 'utf-8'
    for k in list(env):
        if k.startswith('PYTHON') and k != 'PYTHONIOENCODING':
            env.pop(k, None)
    return env


def _scan_artifacts(workdir: str, exclude: set[str]) -> list[dict]:
    """扫描写区产物，按扩展名归类。exclude=本执行不应回收的文件名（script/data_refs pkl）。"""
    out: list[dict] = []
    try:
        for p in sorted(Path(workdir).iterdir()):
            if p.name in exclude or not p.is_file():
                continue
            t = _ARTIFACT_EXT.get(p.suffix.lower())
            if t:
                out.append({'type': t, 'path': str(p), 'name': p.name})
    except Exception:
        pass
    return out


def _fail(error: str) -> dict:
    """构造统一的失败返回（启动前错误用）。"""
    return {'ok': False, 'stdout': '', 'stderr': '',
            'timed_out': False, 'artifacts': [], 'error': error}


def run_sandbox(
    code: str,
    data_refs: dict | None = None,
    timeout: float = 30.0,
) -> dict:
    """隔离执行用户/agent 生成的 Python 代码。

    参数:
        code: 待执行 Python 源码（不可信）。
        data_refs: 注入子进程全局命名空间的对象（须 pickleable），
            如 ``{'df': <DataFrame>}``。仅由可信父进程传入。
        timeout: 硬超时秒；超时杀整棵进程树，timed_out=True。

    返回:
        ``{ok: bool, stdout: str, stderr: str, timed_out: bool,
           artifacts: list[dict], error: str | None}``。
        run_sandbox 自身永不抛异常（子进程崩溃/超时/启动失败均归一为 dict）。
    """
    workdir = tempfile.mkdtemp(prefix='emc_sb_')
    script_path = os.path.join(workdir, '_sb_user.py')
    data_refs_path = ''

    # pickle data_refs（仅当提供；由父进程（可信层）写，子进程在 guard 下加载）
    if data_refs is not None:
        if not isinstance(data_refs, dict):
            return _fail('data_refs 必须是 dict')
        data_refs_path = os.path.join(workdir, '_sb_data.pkl')
        try:
            import pickle
            with open(data_refs_path, 'wb') as f:
                pickle.dump(data_refs, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            return _fail(f'data_refs pickle 失败: {e}')

    prelude = _PRELUDE_TEMPLATE.format(
        whitelist=tuple(sorted(WHITELIST)),
        data_refs_path=data_refs_path,
    )
    full = prelude + '\n' + (code or '')

    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(full)
    except Exception as e:
        return _fail(f'写脚本失败: {e}')

    env = _build_env()
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0

    try:
        proc = subprocess.Popen(
            # -I = 隔离（忽略 PYTHON* env + user site，防投毒）。
            # -X utf8 = 强制子进程 stdio 用 utf-8（-I 会忽略 PYTHONIOENCODING，
            #   只能靠 -X 命令行 flag 让 traceback / print 走 utf-8，匹配父进程 decode）。
            [sys.executable, '-I', '-X', 'utf8', script_path],
            cwd=workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=creationflags,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
    except Exception as e:
        return _fail(f'启动子进程失败: {e}')

    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_tree(proc.pid)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except Exception:
            stdout, stderr = '', ''
        rc = proc.returncode if proc.returncode is not None else -1

    artifacts = _scan_artifacts(
        workdir,
        exclude={os.path.basename(script_path), os.path.basename(data_refs_path)},
    )

    # 短错误摘要：超时 → 'timeout after Ns'；非 0 → stderr 最后一个非空行
    error: str | None = None
    if timed_out:
        error = f'timeout after {timeout}s'
    elif rc != 0:
        lines = [ln for ln in (stderr or '').splitlines() if ln.strip()]
        error = lines[-1] if lines else f'exit code {rc}'

    return {
        'ok': (rc == 0 and not timed_out),
        'stdout': stdout or '',
        'stderr': stderr or '',
        'timed_out': timed_out,
        'artifacts': artifacts,
        'error': error,
    }
