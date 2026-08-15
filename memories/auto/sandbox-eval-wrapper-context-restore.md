---
name: sandbox-eval-wrapper-context-restore
description: sandbox 劫持 eval/exec 须补 globals/locals=真正调用帧还原默认上下文，否则误伤 numpy/importlib
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37d07713-df9f-4427-92af-e27b871d6574
---

sandbox.py（PRELUDE §2.6）frame-based 禁 eval/exec/compile 时，包一层 wrapper 会让原始函数的 `_getframe(1)` 取到 wrapper 帧而非真正调用者，破坏 eval/exec 默认上下文语义。

**Why**（两类误伤均实测，5.83）：
- numpy.f2py `eval('lambda v,f=f:not f(v)')`：f 是调用帧局部变量，wrapper 后 eval 在错误帧执行 → NameError: f。
- importlib `exec(code, module.__dict__)`：显式传 globals 但 locals 默认=None（=globals）；wrapper 若无条件补 locals 会污染 → `from __future__ import annotations` ImportError。
- 全禁（不 frame-based）更直接误伤 matplotlib/pandas/numpy.f2py（库内部依赖 eval/exec）。

**How to apply**：guard 仅当**调用者完全用默认（globals 未传）**才补 `globals=_f.f_globals, locals=_f.f_locals`（`_f=_getframe(1)` 真正调用帧）；调用者显式传 globals 时尊重之（locals 默认=globals，不覆盖）。compile 不依赖调用帧上下文，单独 guard 原样 `*args, **kwargs` 转发。同款 frame 判定见沙箱 import guard（PRELUDE _sb_guard）与 open-wrapper（_sb_open_guard）。详见 revision-log 5.83、[[sandbox-frame-based-trust]]。
