# 会话交接卡

> **用途**：每天收工前更新，换机后通过此文件恢复上下文。

## 🔄 进行中（未完成）

| 任务 | 进度% | 下一步 | 阻塞 |
|------|-------|--------|------|
| L0→L1→L2 端到端管线验证 | 0% | DeepSeek Key 已配，可随时跑 | 用户搁置 |
| Kepler UI 改造 | 80% | Tooltip 微调 / Token 体系补全 / 弹窗主题 | 须保持当前基准 |
| Skill 包整合 | 95% | bytedance agentkit-samples 待网络恢复后拉取 | GitHub 网络 |

## 📌 上下文快照

- **当前分支**：`main`
- **最新 commit**：`36fdf68 fix: Tooltip border-radius 100px`
- **领先 origin/main**：约 15 commits（GitHub 网络不可达，未 push）
- **Python**：3.14.5 | **Streamlit**：1.58.0
- **默认端口**：8501

## 换机启动指令

```
git pull origin main          # 拉取最新（如果已 push）
pip install -r requirements.txt
python -m streamlit run apps/app_main.py
```

---

## 2026-06-15 (周一) 白日 — 完整进展

### 1. Harness 体系搭建 ✅

按照 Claude Code 7 层 Harness 架构，**下三层已扎实**：

| 层 | 状态 | 关键产出 |
|----|:--:|----------|
| ① CLAUDE.md | ✅ | 三层：全局 `~/.claude/CLAUDE.md` + 项目 `CLAUDE.md` + 模块 `SCRIPT/` `core/` `apps/` |
| ② Hooks | ✅ | SessionStart (环境检查+API+Todo+Git) + SessionEnd (交接提醒) |
| ③ Skills | ✅ | 465 个 Skill 包 (Anthropic 17 + daymade 64 + python 12 + laurigates 362 + 讯飞 3 + 字节 6 + 火山 1) |

### 2. 项目框架优化 ✅

| 做了什么 | 文件 |
|----------|------|
| `_safe_print` → `core/utils.py` 统一 | 14 文件迁移 |
| `app_main.py` 拆分：控制台独立为 `apps/app_console.py` | -306 行 |
| `_register_layer` → `core/layer_registry.py` 共享 | 新文件 |
| `data_governance.py` CLI 参数化 | `--input` / `--output` |
| `check_data_quality.py` L1 段适配 26 列格式 | 路径修复 |
| `pm.agent.md` 归档 | PM=主线程 |
| 清理 16 个冗余文件 | 根目录散乱脚本 + 爬虫产物 |

### 3. 记忆体系 ✅

- 三层记忆：CLAUDE.md (明规则) → Auto Memory (隐规则) → 专项参考文档
- 新建 3 份参考：`docs/brand-visual.md` `docs/copywriting-style.md` `docs/api-conventions.md`
- `.claudeignore` 文件
- 批量修改 SOP 记忆：`memory/sop-mistake.md`

### 4. Kepler.gl 风格 UI 改造 ✅ (80%)

| 完成 | 内容 |
|:--:|------|
| ✅ | 全屏地图 CSS (移除 Streamlit chrome + pydeck canvas 100vh) |
| ✅ | 右侧竖排浮动 HUD [R] [D] [A] [H] |
| ✅ | 左上角 [*] 设置 |
| ✅ | 底部左下角 [M] [OV] [TB] [LY] |
| ✅ | 默认 Light 主题 (carto_standard 底图) |
| ✅ | 按钮毛玻璃效果 (30% 透明 → hover 加深) |
| ✅ | 自定义 CSS tooltip (右侧←左/底部↑上/左上↓下, 胶囊形) |
| ✅ | 图例中文 (非常积极/积极/中性/消极/非常消极) |
| ✅ | Toast 通知自定义 (居中, 2秒 fadeOut, 胶囊形) |
| ✅ | LY 图层 toggle 开关 + [L1]/[L2] 加粗前缀 |
| ✅ | 分级渲染 (5k-100k+ 五级自适应) |
| ✅ | 备份 + 一键恢复脚本 `design/backups/restore.sh` |
| ⏸️ | Token 体系补全 (Kepler 色板/间距/动画) |
| ⏸️ | 弹窗暗色主题统一 |

### 5. 关键决策

- **UI 基准**：当前 Kepler 风格全屏地图+HUD 已确认满意，以后所有 UI 修改基于此版，不回退。记录在 `memory/kepler-ui-baseline.md`
- **坐标转换**：宜昌双源策略（社交GCJ-02 + 规划CGCS2000），灵活支持自定义 EPSG
- **批量修改验证 SOP**：AST 检查 + 导入检查 + 函数列表 (防止误删/漏导入再犯)
- **视觉中转站**：`docs/vision-inbox/latest.md` 跨 Chat 图片识别（另一个 Chat 写，本项目读）
- **API Key**：DeepSeek + 讯飞 + 火山引擎全配，`.env` 被 `.gitignore` 排除

### 6. ⚠️ 注意事项

- **不要**删除 `_add_boundary_if_exists` 或忘记 `RENDER_TIERS` 导入 — 已犯错两次，记录在 SOP
- **不要**用 CSS 重写 `stDialog` 样式 — 曾导致弹窗错乱，已回退
- **Tooltip**：纯 CSS `::after` + `border-radius:100px`，不要再用 JS 注入方案
- **Git push**：约 15 commits 未推，GitHub 网络不可达（须换网络或手动）
- **代码中仍有大量未使用的 import**（linter hints），可择机清理但不影响功能

## 🔜 明日 (06-16)

1. git push（换网络后）
2. Token 体系补全 + 弹窗主题统一（续 Kepler 改造）
3. 根据用户反馈微调 UI
4. L0→L1→L2 管线验证（DeepSeek Key 已就绪）
