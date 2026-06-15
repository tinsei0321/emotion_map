"""
通用工具函数 (Shared Utilities)
════════════════════════════════
所有模块共用的基础工具，避免代码重复。
"""
import builtins as _bi

_real_print = _bi.print


def safe_print(*args, **kwargs):
    """
    安全打印 — Windows GBK 编码兼容。

    替代所有 print() 调用，防止 emoji 和特殊 Unicode 字符
    在 Windows 控制台中引发 UnicodeEncodeError。

    用法:
        from core.utils import safe_print
        safe_print("[OK] 分析完成")
    """
    try:
        _real_print(*args, **kwargs)
    except UnicodeEncodeError:
        _real_print(*(
            str(a).encode('ascii', errors='replace').decode('ascii')
            for a in args
        ), **kwargs)
