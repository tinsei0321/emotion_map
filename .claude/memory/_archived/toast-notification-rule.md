---
name: toast-notification-rule
description: 地图上任何变化都必须触发居中 Toast 提示
metadata:
  type: feedback
---

# Toast 通知铁律

**地图上产生任何变化 → 中央提示条必须出现。**

## 触发条件

任何改变地图显示状态的操作，在 `st.rerun()` 之前必须设置 `st.session_state['_toast']`：

| 操作 | Toast |
|------|-------|
| 加载数据 | `[OK] 数据加载成功` |
| 切换底图 | `[OK] xxx底图` |
| 切换热力图/散点 | `[OK] 已切换至热力图/散点图` |
| 确认范围 | `[OK] N 个范围已确认` |
| 清空范围 | `[OK] 范围已清空` |
| 图层状态更新 | `[OK] 图层状态已更新` |
| 全部打开/关闭 | `[OK] 全部图层已显示/隐藏` |
| 数据治理加载 | `[OK] xxx 加载完成` |

## 消费逻辑

`main()` 中在 CSS 注入后、按钮渲染前：
```python
pending = st.session_state.pop('_toast', None)
if pending:
    show_toast(pending)
```

## 注意

- 必须用 `session_state['_toast']` 而非直接 `st.markdown`（rerun 后持久化）
- `show_toast()` 渲染为全屏正中央，2s 自动淡出

**Why:** 用户要求地图上只要产生了变化，中央的提示信息条就要出现。
**How to apply:** 所有改变 `_map_style`/`_heatmap_mode`/`layers`/`selected_ranges`/`file_path` 的操作，rerun 前必设 `_toast`。
