# 会话交接卡

> 换机后读取此文件恢复上下文。

## 🔄 进行中

| 任务 | 状态 |
|------|------|
| L0→L1→L2 端到端管线验证 | ⏸️ 暂缓至下周 |
| UI 重构 Phase 1 (双层顶栏+左面板) | ✅ 基本完成 |

## 📌 上下文快照
- **分支**: `main`
- **Streamlit**: 运行中 (端口 8501)
- **Python**: 3.13.2

## 2026-06-15/16 完成

| # | 任务 |
|---|------|
| 1 | UI 重构：geojson.io 风格双层顶栏 (标题栏 48px 深蓝 + 工具栏 44px 白底) |
| 2 | 工具栏按钮：36px 方形/72px 长条, 4px 圆角, 粗体, hover 灰底 |
| 3 | 左侧信息面板：260px 白底, <details> 折叠 (数据一览/图层一览) |
| 4 | Toast 通知：全屏居中, 2s 自动淡出, 地图任何变化触发 |
| 5 | Primary 按钮 #007afc 蓝, Secondary 白底灰框 |
| 6 | Streamlit 主题 primaryColor=#007afc |
| 7 | 按钮间距设计规则文档化 |
| 8 | 记忆体系完善 (6 个 memory 文件) |
| 9 | Playwright 截图工具安装 |

## 关键设计决策

- **双层顶栏**: 标题栏 48px #1a2940 + 工具栏 44px #fff
- **按钮设计语言**: S=36px, G=8px, R=4px, 定位公式 left/right=12+Σ(prev_w+G)
- **Toast 规则**: 地图任何变化→中央提示条, st.empty() 强制新 DOM
- **Streamlit 限制**: st.radio 不可自定义 CSS; @st.dialog 不可强制居中/改倒角
- **LY 弹窗保留**: 面板仅展示, 开关通过 LY 弹窗控制

## 文件变更 (未提交)
```
 M apps/app_main.py
 M core/ui_components.py
 M core/map_engine.py
 M core/layer_registry.py
 M docs/todo.md
 M docs/ui-redesign-plan.md
 M docs/prd.md
 M docs/decisions.md
 M docs/vision-inbox/latest.md
 M docs/spec.md
 M docs/architecture-pattern.md
 M AGENTS.md
 M MEMORY.md
 M .claude/settings.json
 M memories/repo/session-handoff.md
?? .streamlit/
?? .claude/agents/
?? .claude/memory/
?? design/backups/
?? docs/vision-inbox/*.png
```

## 每日启动
```powershell
py -m streamlit run apps/app_main.py --server.port 8501
# http://localhost:8501
```
