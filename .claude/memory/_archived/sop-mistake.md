---
name: sop-mistake
description: 代码批量修改后必须跑的验证步骤
metadata:
  type: feedback
---

# 批量修改后的验证 SOP

**教训来源**：2026-06-15 app_main.py 拆分时连续两次出错：
1. 删除代码块时把非目标函数 `_add_boundary_if_exists` 一并切掉
2. 新增 `RENDER_TIERS` 引用但漏加 `from .config import RENDER_TIERS`

**Why:** 批量操作（sed、行范围删除、Python 脚本改写）不可靠——边界条件极易出错。人工核对容易遗漏。

**How to apply:**
每次批量修改代码后，立即执行以下三条验证，不通过不提交：

```
# 1. AST 语法检查（所有改过的 .py 文件）
python -c "import ast; ast.parse(open('file.py').read())"

# 2. 导入完整性检查
python -c "from module import *"

# 3. 函数完整性检查（对比前后函数列表）
grep -n "^def \|^class " file.py
```

如果改的是 `app_main.py` 或 Streamlit 相关，必须再跑：
```
timeout 8 python -m streamlit run apps/app_main.py --server.headless true
```

**阈值**：涉及 2+ 文件或 50+ 行变化 → 强制执行全部三项。
