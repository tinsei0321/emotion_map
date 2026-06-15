# 识图结果 — 2026-06-15 (第二次)

## 概述

一张 Streamlit 应用错误截图。红色告警框中显示 `NameError: name 'safe_print' is not defined`，调用链从 `app_main.py` 的 `main()` 函数一直深入到 `core/tracker.py` 的 `_emit()` 方法。

## 详细描述

### 错误信息

```text
NameError: name 'safe_print' is not defined
```

### Traceback 调用链

| 文件 | 行号 | 调用 |
| ---- | ---- | ---- |
| `apps/app_main.py` | 1472 | `main()` |
| `core/tracker.py` | 207 | `wrapper` → `t.enter(track_id, input_info=input_info)` |
| `core/tracker.py` | 121 | `enter` → `self.log(track_id, status="enter", input_info=input_info)` |
| `core/tracker.py` | 114 | `log` → `self._emit(line)` |
| `core/tracker.py` | 154 | `_emit` → `safe_print(line, flush=True)` ❌ |

### UI 元素

- 红色告警框显示完整错误堆栈
- 右下角有 "Deploy" 按钮和 "Copy"、"Ask Google"、"Ask ChatGPT" 操作项

## 根因分析

`core/tracker.py` 第 48-50 行 `# ── 安全打印 ──` 注释下方是**空行**，缺少了：

```python
from core.utils import safe_print
```

`safe_print` 函数定义在 `core/utils.py`，是正确的实现。但 `tracker.py` 没有导入就直接调用，导致 `NameError`。
