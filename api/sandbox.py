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
- ``SAFE_READY`` 默认 False。单测全过 + 人审后才置 True；api/main.py 以 ``if SAFE_READY``
  条件挂 run_router，关掉只需改回 False（单点 revert）。
- 代码里没有任何地方把 SAFE_READY 设 True（仅此文件一处手动切）。

加固（演示版底线，非 OS 级隔离）：
- 加固① open-wrapper（PRELUDE §2.5）：写模式无论帧都查 workdir 白名单（拦 plt.savefig 逃逸）；
  读模式仅用户帧查（拦 open('.env') 偷密钥/PII），库帧读放行（字体/证书/c ext 不可枚举）。
- 加固② AST 反射审查（run_sandbox 进子进程前静态）：拦 dunder 直接访问 + getattr 同族 4 类；
  残余别名/IfExp 靠禁 eval/exec/compile + del _sb_* 兜底。
- 加固③ CORS（api/main.py）：allow_origins 本机白名单（serve.py 反代同源，不破现有调用）。

已知局限（纯 Python 沙箱固有，根治需 OS 级隔离——容器/低权用户/seccomp，部署层叠加）：
- 内存/CPU 硬限缺失：Windows 无 setrlimit 等价物，仅靠 communicate(timeout) 软限；演示场景单机可接受。
- 别名反射（g=getattr; g(x,'__class__')）/ IfExp 间接调用：AST 不做数据流分析拦不住，靠清理+禁 eval 收敛。
- 同用户权限运行，非 OS 级隔离；生产部署应叠加容器/用户隔离。
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SAFE_READY: bool = True   # 红线开关：True=允许 api/main.py 挂 /run（须全单测过 + 人审后切；
                          # revert 只需改回 False，main.py 的 if SAFE_READY gate 自动卸载 /run）。

# ---------------------------------------------------------------------------
# AST 反射审查（加固②）：代码进子进程前静态拦截 dunder 反射逃逸。
# 纯 Python 沙箱的固有限制 = ``__import__.__closure__[0].cell_contents`` 一行取回原始
# __import__ 整个 guard 失效。AST 层拦得住「直接属性访问」「getattr 常量/拼接/f-string」
# 4 类；残余（别名 g=getattr、跨行拼接、IfExp 间接调用）靠 PRELUDE 禁 eval/exec/compile
# + del _sb_* 符号兜底——根治仍需 OS 级隔离（容器/低权用户/seccomp），文档化。
# ---------------------------------------------------------------------------
# 危险 dunder：取回原函数/闭包（绕 guard）、元类逃逸链（().__class__.__bases__[0].__subclasses__()）、
# 取 import/builtins、取任意命名空间。__init__/__new__ 移出（用户合法继承 cls.__new__(cls)
# /super().__init__() 会误伤）；残余 f.__init__.__globals__ 链由 __globals__ 在集合内拦截。
_DANGEROUS_ATTRS: frozenset[str] = frozenset({
    '__closure__', '__defaults__', '__code__', '__globals__',
    '__class__', '__bases__', '__mro__', '__subclasses__',
    '__import__', '__builtins__', '__dict__',
    '__func__', '__self__', '__qualname__',
    '__subclasshook__', '__instancecheck__',
    '__subclasscheck__', '__class_getitem__', '__init_subclass__',
})

# getattr 同族：第二参是属性名字符串——dunder 经此反射同样绕 guard。
_GETATTR_LIKE: frozenset[str] = frozenset({'getattr', 'hasattr', 'setattr', 'delattr'})


class _ReflectionVisitor(ast.NodeVisitor):
    """遍历用户代码 AST，收集 dunder 反射违规（不抛，审查层汇总后归一 _fail）。"""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # 类①：直接属性访问 x.__class__ / obj.__subclasses__
        if node.attr in _DANGEROUS_ATTRS:
            self.violations.append(f'L{node.lineno}: 禁止访问反射属性 .{node.attr}')
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        # 类②③④：getattr 同族 + 第二参形态
        if isinstance(func, ast.Name) and func.id in _GETATTR_LIKE and len(node.args) >= 2:
            second = node.args[1]
            if isinstance(second, ast.Constant) and isinstance(second.value, str):
                # 类②：常量字符串含危险 dunder
                if any(d in second.value for d in _DANGEROUS_ATTRS):
                    self.violations.append(
                        f'L{node.lineno}: 禁止用 {func.id}() 反射访问 dunder 属性')
            elif isinstance(second, (ast.BinOp, ast.JoinedStr, ast.Name)):
                # 类③④+别名：拼接 / f-string / 变量名作属性——保守全拦（防 '__cl'+'osure__' 等绕过）
                self.violations.append(
                    f'L{node.lineno}: 禁止用 {func.id}() 传非字面量作属性名（防 dunder 拼接/别名绕过）')
        self.generic_visit(node)


def _check_reflection(code: str) -> str | None:
    """AST 反射审查（仅用户代码，不含 PRELUDE）。

    返 None=通过；返 str=失败原因（含行号摘要，前 3 条截断防爆）。语法错误也在此归一。
    """
    if not code or not code.strip():
        return None
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f'代码语法错误: {e.msg}（行 {e.lineno or "?"}）'
    v = _ReflectionVisitor()
    v.visit(tree)
    if v.violations:
        return '反射审查命中: ' + '; '.join(v.violations[:3])
    return None

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
import os.path as _sb_sp   # 路径判定（open-wrapper 用）；guard 安装前导入，否则 os 被拦

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

# ---- 2.5) 安装 open 守卫（加固①：路径白名单 + frame-based trust 决定检查强度）----
# 写模式（w/a/+/x）无论用户帧还是库帧都查白名单（拦 plt.savefig('C:/anywhere') 逃逸）；
# 读模式仅用户脚本帧查白名单（拦 open('.env') 偷密钥/PII），库帧读放行（字体/证书/c ext 不可枚举）。
# realpath+abspath 解 symlink + 规范化 ..，os.sep 后缀匹配防 workdir_x 假阳成 workdir 子路径。
# data_refs 的 pickle 已在 §1 加载完（本守卫之前），故自身加载不受影响。
_sb_orig_open = _sb_builtins.open
_SB_WORKDIR = _sb_sp.dirname(_SB_USER_SCRIPT)


def _sb_open_guard(file, mode='r', *args,
                   _getframe=_sb_sys._getframe, _orig=_sb_orig_open,
                   _sp=_sb_sp, _workdir=_SB_WORKDIR,
                   _user_script=_SB_USER_SCRIPT, **kwargs):
    _mode = str(mode)
    _is_write = any(_c in _mode for _c in ('w', 'a', '+', 'x'))
    try:
        _rp = _sp.realpath(_sp.abspath(str(file)))
        _wd = _sp.realpath(_sp.abspath(_workdir))
        _in_wd = (_rp == _wd) or _rp.startswith(_wd + _sp.sep)
    except (OSError, ValueError):
        if _is_write:
            raise PermissionError('[sandbox] 路径解析失败禁止写: ' + str(file))
        return _orig(file, mode, *args, **kwargs)
    if _is_write:
        if not _in_wd:
            raise PermissionError('[sandbox] 禁止写沙箱外路径: ' + str(file))
    else:
        try:
            _f = _getframe(1)
            _importer = _f.f_code.co_filename if _f is not None else ''
        except (ValueError, AttributeError):
            _importer = ''
        if _importer == _user_script and not _in_wd:
            raise PermissionError('[sandbox] 用户代码禁止读沙箱外路径: ' + str(file))
    return _orig(file, mode, *args, **kwargs)


_sb_builtins.open = _sb_open_guard

# ---- 2.6) 禁 eval/exec/compile（加固②残余兜底，frame-based：用户帧禁、库帧放行）----
# AST 静态层拦不住 eval('__import__("os")') 这类动态字符串构造反射；用户帧调三件套才拦，
# 库帧放行（matplotlib/pandas/numpy.f2py/importlib 内部依赖 eval/exec/compile，全禁会误伤）。
# 关键：eval/exec 默认用「调用帧」的 globals/locals，包一层 guard 后原始函数的 _getframe(1) 会
# 取到本 guard 帧而非真正调用者，致上下文错位（numpy.f2py 的 eval('lambda v,f=f:...') NameError）；
# 故 guard 放行时须显式补 globals/locals=_getframe(1)（真正调用者）。compile 不依赖调用帧上下文，原样转发。
def _sb_make_exec_guard(_orig, _getframe=_sb_sys._getframe, _user_script=_SB_USER_SCRIPT):
    def _guard(expr, globals=None, locals=None, *args, **kwargs):
        try:
            _f = _getframe(1)
            _imp = _f.f_code.co_filename if _f is not None else ''
        except (ValueError, AttributeError):
            _f = None
            _imp = ''
        if _imp == _user_script:
            raise PermissionError('[sandbox] 用户代码禁止 eval/exec/compile')
        # 仅当调用者完全用默认（globals 未传）才补 globals+locals=真正调用帧——还原 eval 默认语义
        # （包一层后原始函数 _getframe(1) 会取到本 guard 帧致上下文错位，numpy.f2py 的
        # eval('lambda v,f=f:...') 会 NameError）。调用者显式传 globals 时尊重之（locals 默认=globals，
        # 不覆盖——否则污染 importlib 的 exec(code, module.__dict__) 致 __future__ import 失败）。
        if globals is None and _f is not None:
            globals = _f.f_globals
            locals = _f.f_locals
        return _orig(expr, globals, locals, *args, **kwargs)
    return _guard


def _sb_make_compile_guard(_orig, _getframe=_sb_sys._getframe, _user_script=_SB_USER_SCRIPT):
    def _guard(*args, **kwargs):
        try:
            _f = _getframe(1)
            _imp = _f.f_code.co_filename if _f is not None else ''
        except (ValueError, AttributeError):
            _imp = ''
        if _imp == _user_script:
            raise PermissionError('[sandbox] 用户代码禁止 eval/exec/compile')
        return _orig(*args, **kwargs)
    return _guard


_sb_builtins.eval = _sb_make_exec_guard(_sb_builtins.eval)
_sb_builtins.exec = _sb_make_exec_guard(_sb_builtins.exec)
_sb_builtins.compile = _sb_make_compile_guard(_sb_builtins.compile)

# ---- 3) 清理 PRELUDE 私有符号。guard/open-wrapper 依赖（_getframe/_orig/_wl/_workdir）已绑进
# 闭包默认参数，故可删全局 _sb_sys/_sb_sp/_sb_orig_import/_sb_orig_open，避免用户态
# _sb_sys.modules['os'] 这类 trivial 绕过。
# 残余风险（文档化）：AST 审查 + 禁 eval/exec/compile 已拦绝大多数 dunder 反射逃逸；
# 别名（g=getattr; g(x,'__class__')）/ IfExp 间接调用 AST 不做数据流分析拦不住，靠本清理
# + 部署层 OS 级隔离（容器/低权用户/seccomp）最终兜底——纯 Python 沙箱的固有限制。----
for _sb_n in ('_sb_pickle', '_sb_builtins', '_sb_sys', '_sb_sp',
              '_sb_orig_import', '_sb_orig_open',
              '_sb_loaded', '_sb_f', '_sb_k', '_sb_v', '_sb_n', '_SB_DATA_REFS',
              '_SB_USER_SCRIPT', '_SB_WORKDIR', '_sb_open_guard',
              '_sb_make_exec_guard', '_sb_make_compile_guard'):
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


def _build_env(workdir: str = '') -> dict:
    """subprocess 环境：拷贝 os.environ，强制 Agg 后端（无显示环境出图），剥离 PYTHON* env。

    ``-I`` 已忽略 PYTHON* env，此处剥离为双保险（防 PYTHONPATH 投毒等）。
    保留 PYTHONIOENCODING（编码稳定）。
    MPLCONFIGDIR 指向沙箱内 workdir/.mpl：让 matplotlib 字体/配置缓存写到沙箱内，避免
    open-wrapper（加固①）拦截首次 savefig 写 ~/.matplotlib 的库帧写逃逸（误伤）。
    """
    env = dict(os.environ)
    env['MPLBACKEND'] = 'Agg'
    # 强制子进程 stdio 用 utf-8（匹配 Popen 的 encoding='utf-8' 解码，避免 Windows
    # cp936 mojibake 让 error 摘要乱码）。PYTHONIOENCODING 不会被 -I 忽略（非 PYTHON* site 项）。
    env['PYTHONIOENCODING'] = 'utf-8'
    if workdir:
        mpl_dir = os.path.join(workdir, '.mpl')
        try:
            os.makedirs(mpl_dir, exist_ok=True)
            env['MPLCONFIGDIR'] = mpl_dir
        except OSError:
            pass   # 创建失败不阻塞（matplotlib 落默认 ~/.matplotlib 会被守卫拦，但非致命）
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
    # AST 反射审查（加固②）：代码进子进程前静态拦 dunder 反射逃逸，命中即归一 _fail（不建 workdir）。
    reflection_err = _check_reflection(code or '')
    if reflection_err:
        return _fail(reflection_err)

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

    env = _build_env(workdir)
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
