# Retired 台账（退役文件清单）

> /weed 与手动退役的文件留痕。删除前 grep 零活引用；退役即追加一行。
> 凡入此台账的文件均经 `git rm`，**可从 git 历史恢复**。

---

## 2026-07-18（CB-1 · apps 退役遗留僵尸清理）

| 文件 | 原职责 | 退役原因 | 可恢复 |
|------|--------|----------|--------|
| `core/ui_components.py` | Streamlit 可复用 UI 组件（835 行，29 处 streamlit 引用） | apps/ Streamlit 层 2026-07-18 整层退役，frontend/ MapLibre 接管；零活引用 | git 历史 |
| `core/layer_registry.py` | Streamlit session_state 图层注册（3 处 st.） | 同上，Streamlit 会话绑定，FastAPI/脚本环境不可复用 | git 历史 |
| `core/map_engine.py` | pydeck 底图+标记+热力+边界 | 前端迁 MapLibre GL JS 后 pydeck 渲染路径废弃；零活引用（仅退役 apps 备份） | git 历史 |
| `.streamlit/config.toml` | Streamlit 主题配置 | apps/ 退役，无消费方 | git 历史 |

**删除前核验**：`grep -rn "from core.ui_components\|from core.layer_registry\|from core.map_engine" --include=*.py` = **零活 import**（仅 `design/backups/` 退役 app 残留 + `core/__init__.py` docstring 文字提及，均已清）。pytest 207 passed 零回归。

**来源**：CB-1（[SCAN_DeepSeek.md](SCAN_DeepSeek.md) §2.5.3/讨论5 指出 ui_components+layer_registry；我方核验扩到 map_engine 同类 pydeck 僵尸）。详见 [cb-journal.md](cb-journal.md) CB-1。
