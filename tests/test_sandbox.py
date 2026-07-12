"""P3 code-exec 沙箱单测 —— 隔离执行 agent 生成的 Python 数据分析代码。

真跑 subprocess（不 mock run_sandbox 的子进程）：验证隔离、import 守卫、超时 kill、
artifacts 回收、data_refs 注入都是真实生效的，而非 monkeypatch 自欺。

分组:
- SAFE_READY gate：红线开关默认 False；白名单覆盖与禁列校验。
- test_rejects_*：危险代码（命令注入 / 网络外联 / 死循环 / 文件逃逸）必须被拦/超时/无副作用。
- test_breakthrough_*：真实数据分析（pandas / numpy+scipy / shapely / matplotlib / csv / data_refs）必须能跑通。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from api.sandbox import run_sandbox, SAFE_READY, WHITELIST


# ---------------------------------------------------------------------------
# SAFE_READY gate + 白名单结构校验
# ---------------------------------------------------------------------------
def test_safe_ready_default_off():
    """红线：SAFE_READY 默认 False。单测全过 + 人审前绝不挂 /run。"""
    assert SAFE_READY is False


def test_whitelist_covers_required_libs():
    """白名单含数据分析主力库（pandas/geopandas/shapely/scipy/matplotlib/esda/libpysal）。"""
    required = {'pandas', 'geopandas', 'shapely', 'scipy', 'matplotlib', 'esda', 'libpysal'}
    assert required <= set(WHITELIST)


def test_whitelist_excludes_dangerous_modules():
    """os/sys/subprocess/socket/ctypes/pickle/importlib/threading 等绝不在白名单。"""
    for dangerous in ('os', 'sys', 'subprocess', 'socket', 'ctypes',
                      'pickle', 'importlib', 'threading', 'multiprocessing',
                      'signal', 'pty', 'builtins'):
        assert dangerous not in WHITELIST, f'{dangerous} 不得在白名单'


# ---------------------------------------------------------------------------
# test_rejects_* —— 危险代码被拦 / 超时 / 无副作用
# ---------------------------------------------------------------------------
def test_rejects_os_system():
    """import os → 拦（os 不在白名单，防 os.system 命令注入）。"""
    r = run_sandbox("import os; os.system('echo hacked')", timeout=15)
    assert r['ok'] is False
    assert r['timed_out'] is False
    assert '禁止导入' in (r['error'] or '') or 'os' in (r['stderr'] or '')


def test_rejects_dunder_import_subprocess():
    """__import__('subprocess') → 拦（绕过 import 语句的动态导入也无效）。"""
    r = run_sandbox("__import__('subprocess').run(['cmd', '/c', 'echo hacked'])", timeout=15)
    assert r['ok'] is False
    assert r['timed_out'] is False
    assert 'subprocess' in (r['stderr'] or '') or '禁止导入' in (r['error'] or '')


def test_rejects_socket():
    """import socket → 拦（防网络外联）。"""
    r = run_sandbox("import socket; socket.socket()", timeout=15)
    assert r['ok'] is False
    assert r['timed_out'] is False
    assert 'socket' in (r['stderr'] or '') or '禁止导入' in (r['error'] or '')


def test_rejects_pickle():
    """import pickle → 拦（防反序列化 RCE 链）。"""
    r = run_sandbox("import pickle", timeout=15)
    assert r['ok'] is False
    assert '禁止导入' in (r['error'] or '')


def test_rejects_infinite_loop_times_out():
    """死循环 → 超时杀进程，timed_out=True，测试不卡死。"""
    r = run_sandbox("while True:\n    pass", timeout=4)
    assert r['timed_out'] is True
    assert r['ok'] is False
    assert 'timeout' in (r['error'] or '')


def test_rejects_external_file_read_graceful():
    """读沙箱外相对路径（../../etc/passwd）→ 子进程内失败，run_sandbox 不抛、归一为 ok=False。"""
    r = run_sandbox("open('../../etc/passwd').read()", timeout=10)
    assert r['ok'] is False
    assert r['timed_out'] is False
    assert r['error']   # 有错误摘要（FileNotFoundError/Path 等）


def test_run_sandbox_never_raises_on_crash():
    """子进程内抛异常 → run_sandbox 归一为 dict，绝不向调用方抛出。"""
    r = run_sandbox("raise RuntimeError('boom')", timeout=10)
    assert r['ok'] is False
    assert r['timed_out'] is False
    assert 'RuntimeError' in (r['stderr'] or '') or 'boom' in (r['stderr'] or '')
    assert isinstance(r['artifacts'], list)


# ---------------------------------------------------------------------------
# test_breakthrough_* —— 真实数据分析能力
# ---------------------------------------------------------------------------
def test_breakthrough_whitelist_imports():
    """白名单库在子进程内真实可 import（pandas/numpy/scipy/matplotlib/shapely/geopandas）。"""
    code = (
        "import pandas as pd\n"
        "import numpy as np\n"
        "import scipy\n"
        "import matplotlib\n"
        "import shapely\n"
        "import geopandas as gpd\n"
        "import esda\n"
        "import libpysal\n"
        "print('ALL_OK')\n"
    )
    r = run_sandbox(code, timeout=60)
    assert r['ok'] is True, r['stderr']
    assert 'ALL_OK' in r['stdout']


def test_breakthrough_pandas_groupby():
    """pandas DataFrame 分箱 groupby mean（核心数据分析能力）。"""
    code = (
        "import pandas as pd\n"
        "df = pd.DataFrame({'g': ['a', 'a', 'b', 'b'], 'v': [1.0, 3.0, 10.0, 20.0]})\n"
        "m = df.groupby('g').mean()\n"
        "print('mean_b', float(m.loc['b', 'v']))\n"
    )
    r = run_sandbox(code, timeout=30)
    assert r['ok'] is True, r['stderr']
    assert 'mean_b 15.0' in r['stdout']


def test_breakthrough_numpy_scipy_describe():
    """numpy + scipy.stats.describe → 统计计算可用。"""
    code = (
        "import numpy as np\n"
        "from scipy import stats\n"
        "x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])\n"
        "d = stats.describe(x)\n"
        "print('mean', float(d.mean))\n"
    )
    r = run_sandbox(code, timeout=30)
    assert r['ok'] is True, r['stderr']
    assert 'mean 3.0' in r['stdout']


def test_breakthrough_shapely_buffer():
    """shapely Point.buffer → 几何面积计算可用。"""
    code = (
        "from shapely.geometry import Point\n"
        "p = Point(0.0, 0.0).buffer(1.0)\n"
        "print('area_gt_3', float(p.area) > 3.0)\n"
    )
    r = run_sandbox(code, timeout=30)
    assert r['ok'] is True, r['stderr']
    assert 'area_gt_3 True' in r['stdout']


def test_breakthrough_matplotlib_image_artifact():
    """matplotlib Agg savefig → 写区产生 image artifact。"""
    code = (
        "import matplotlib\n"
        "matplotlib.use('Agg')\n"
        "import matplotlib.pyplot as plt\n"
        "plt.plot([1, 2, 3], [1, 4, 9])\n"
        "plt.savefig('out.png')\n"
    )
    r = run_sandbox(code, timeout=60)
    assert r['ok'] is True, r['stderr']
    imgs = [a for a in r['artifacts'] if a['type'] == 'image']
    assert imgs and imgs[0]['name'] == 'out.png'


def test_breakthrough_csv_artifact():
    """DataFrame.to_csv → 写区产生 data artifact（验证产物回收 + 类型归类）。"""
    code = (
        "import pandas as pd\n"
        "pd.DataFrame({'x': [1, 2]}).to_csv('out.csv', index=False)\n"
    )
    r = run_sandbox(code, timeout=30)
    assert r['ok'] is True, r['stderr']
    data = [a for a in r['artifacts'] if a['type'] == 'data']
    assert data and data[0]['name'] == 'out.csv'


def test_breakthrough_data_refs_injection():
    """data_refs 注入：父进程传 DataFrame → 子进程按名访问。"""
    pd = pytest.importorskip('pandas')
    code = "print('rows', len(df))\n"
    r = run_sandbox(code, data_refs={'df': pd.DataFrame({'x': [1, 2, 3]})}, timeout=30)
    assert r['ok'] is True, r['stderr']
    assert 'rows 3' in r['stdout']


def test_breakthrough_library_lazy_import_not_blocked():
    """matplotlib savefig 内部 lazy-import io/socket 等传递依赖 → 不被守卫误伤。

    这是 frame-based trust 的关键验证：库帧的 import 放行，用户帧的 import 才拦。
    若此用例失败说明守卫退化成「无脑拦白名单外」，会误伤所有出图/统计库。
    """
    code = (
        "import matplotlib\n"
        "matplotlib.use('Agg')\n"
        "import matplotlib.pyplot as plt\n"
        "plt.plot([1, 2], [3, 4])\n"
        "plt.savefig('p.png')\n"   # savefig 触发 Agg 渲染链，lazy 拉 io/socket/struct 等
    )
    r = run_sandbox(code, timeout=60)
    assert r['ok'] is True, r['stderr']
    assert any(a['name'] == 'p.png' for a in r['artifacts'])


def test_data_refs_must_be_dict():
    """data_refs 非 dict → 立即 _fail，不进子进程。"""
    r = run_sandbox("print('x')", data_refs=[1, 2, 3], timeout=10)  # type: ignore[arg-type]
    assert r['ok'] is False
    assert 'dict' in (r['error'] or '')
