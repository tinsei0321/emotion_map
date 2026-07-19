# Retired 台账（退役文件清单）

> /weed 与手动退役的文件留痕。删除前 grep 零活引用；退役即追加一行。
> 凡入此台账的文件均经 `git rm`，**可从 git 历史恢复**。
>
> ---
> **归档信息**：原始路径 `docs/retired.md`，于 2026-07-19 移入 `docs/catch-ball/` 归档。

---

## 2026-07-18（CB-01 · apps 退役遗留僵尸清理）

| 文件 | 原职责 | 退役原因 | 可恢复 |
|------|--------|----------|--------|
| `core/ui_components.py` | Streamlit 可复用 UI 组件（835 行，29 处 streamlit 引用） | apps/ Streamlit 层 2026-07-18 整层退役，frontend/ MapLibre 接管；零活引用 | git 历史 |
| `core/layer_registry.py` | Streamlit session_state 图层注册（3 处 st.） | 同上，Streamlit 会话绑定，FastAPI/脚本环境不可复用 | git 历史 |
| `core/map_engine.py` | pydeck 底图+标记+热力+边界 | 前端迁 MapLibre GL JS 后 pydeck 渲染路径废弃；零活引用（仅退役 apps 备份） | git 历史 |
| `.streamlit/config.toml` | Streamlit 主题配置 | apps/ 退役，无消费方 | git 历史 |
| `core/db.py` | SQLite+SpatiaLite 存储层（EmotionDB，296 行，含 insert_points/query_by_bbox/export_csv 等） | 全仓零活引用、无 test_db；demo 走 GeoJSON 文件非 SQLite；SCAN 建议7（iterrows→executemany）= 死代码优化 declined（且 insert_points 早已用 executemany）。未来购买数据需 DB 时按当时 schema 重建 | git 历史 |

**删除前核验**：`grep -rn "from core.ui_components\|from core.layer_registry\|from core.map_engine" --include=*.py` = **零活 import**（仅 `design/backups/` 退役 app 残留 + `core/__init__.py` docstring 文字提及，均已清）。pytest 207 passed 零回归。

**来源**：CB-01（[SCAN_DeepSeek_01.md](SCAN_DeepSeek_01.md) §2.5.3/讨论5 指出 ui_components+layer_registry；我方核验扩到 map_engine 同类 pydeck 僵尸）。详见 [cb-journal.md](cb-journal.md) CB-01。

---

## 2026-07-19（CB-02 · sim 脚本退役）

| 文件 | 原职责 | 退役原因 | 可恢复 |
|------|--------|----------|--------|
| `SCRIPT/generate_l1_mock.py` | L1 模拟数据生成器（522 行，POI-anchored，西陵伍家） | 自标 superseded，被 `sim_performance_data.py` 替代（百度热力点真实密度底座更优）；零活引用（仅注释提及） | git 历史 |

**删除前核验**：`grep -rn "generate_l1_mock" --include="*.py"` = 零活 import（仅 `sim_performance_data.py`/`snapshot_config.py`/`poi_4x5_map.py` 注释提及「替/superseded」，非调用）。

**保留 `SCRIPT/generate_test_data.py`**（SCAN 建议4 建议同退役，**declined·事实错误**）：它生成 **L0 原始数据**（10 万条社交媒体 raw，测 L0→L1→L2 全管线），与 sim_performance_data（L1/L2 POI-anchored demo）**用途不同、非冗余**。SCAN"功能重叠"判断不准（verify-before-accept 查 docstring 确认）。

**来源**：CB-02（[SCAN_DeepSeek_02.md](SCAN_DeepSeek_02.md) 建议4）。详见 [cb-journal.md](cb-journal.md) CB-02。
