---
name: streamlit-dialog-patterns
description: Streamlit @st.dialog 交互铁律 — rerun 行为、toggle 处理、toast 模式
metadata:
  type: reference
---

# Streamlit Dialog 交互模式

## 铁律：`st.rerun()` inside `@st.dialog` = 关闭弹窗

Streamlit 的 `@st.dialog` 装饰器会在 `st.rerun()` 调用时关闭弹窗。这不是 bug，是设计如此。

**规则**：

| 场景 | 做法 | 原因 |
|------|------|------|
| 用户 toggle/checkbox 切换 | **不调** `st.rerun()` | Streamlit 自动重绘 dialog，toggle 状态已写入 session_state |
| 用户点"确定"/"确认" | 调 `st.rerun()` | 这是用户明确表示"我改完了，关闭并应用" |
| 用户点外面 | 自动关闭 | Streamlit 原生行为 |
| 批量操作（全部打开/关闭） | 调 `st.rerun()` | 批量操作后应关闭弹窗并应用 |

## 判断标准

在 `@st.dialog` 函数内加 `st.rerun()` 之前，问自己：
- 这个操作后，用户是否还需要继续在弹窗内做其他操作？
  - **是** → 不调 rerun
  - **否**（如"确认"按钮、批量操作）→ 调 rerun

## Toast 通知模式

在 dialog 中设置 toast 消息时，使用 `session_state['_toast']` 而非直接 `st.markdown`：
- dialog 内 `st.markdown` 渲染的 toast 会随 dialog 关闭而消失
- `session_state['_toast']` 在 `main()` 的 rerun 中消费，保证 toast 可见
- dialog 内的 `st.rerun()` 触发 `main()` 重新执行 → toast 正常显示

## 历史犯过的错误

1. **LY 图层 toggle 后 `st.rerun()`** — 每次切换开关弹窗就关，用户无法连续操作多个开关。修复：去掉 rerun。
2. **dialog 内直接 `st.markdown` toast** — rerun 后消失。修复：改用 `session_state['_toast']`。

**Why:** 多次在同一个 Streamlit dialog 交互模式上犯错，用户反复纠正。记录下来确保不再重复。
**How to apply:** 任何涉及 `@st.dialog` 的改动，先读本文件。写 toggle/checkbox 时不加 rerun，写"确定"按钮时加 rerun。
