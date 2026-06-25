# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。

## 🔄 换机协议（常驻）

**离开前**：① `git status` 清空（全 commit）② `git push`（`git log origin/main..HEAD` 应空）③ 更 `docs/revision-log.md` + 本卡 ④ `.claude/` 改动也 commit。
**到机后**：① `git pull` + 确认同步 ② 读本卡「当前节点」③ 天地图 4 底图 JSON 被 gitignore（新机从已有机器拷，key 亦在 `core/config.py`）④ `git status` 确认。

## 当前节点 — 2026-06-25（办公机 · Search P2-P5 全部完成）

### 机器 & 同步
- **机器 = 办公机**（`C:\Users\admin\`）。
- **分支 = main only**（solo 开发，不做 feature branch）。
- `py frontend/serve.py 8080` → `http://localhost:8080/frontend/index.html`

### 已完成（本日 4 commits）

| Commit | 内容 |
|--------|------|
| `edf668f` | **P2 geocode 离线退化** — `forward()` 加 `min_fuzzy_score` 参数；离线时阈值 55→35 |
| `0798dcd` | **P3 下拉结果丰富化** — zone 色点 + 双副信息 + 匹配类型标签（精确/前缀/拼音/子串） |
| `ed00b07` | **修复** — `.search-bar` `overflow:hidden` 裁剪下拉，改用 `opacity:0` |
| `33df6e3` | **P5 UX loading + 空态引导** — 输入即显 spinner；空态显示引导文案 |

P4（华翔CAZ/江南URD 数据缺口）跳过——暂无数据。

### 下一步（可选方向，按优先级）

**功能模块**（来自任务树）：
1. **KDE 批2 全局时间轴** ◆ 架构转折点 — 解锁批3（3D）和批4（A/B对比）
2. **Analysis 情绪分析接入** — L2 管道接前端 / 空间分析 MVP
3. **Table 数据表格** — 列表/筛选/导出（联动管线已预留）
4. **Range 范围分析** — 缓冲/叠加/聚合
5. **多维归因分析** — 自 KDE ① 剥离
6. **KDE 批5B 图层自由编组**

**数据管道**：
- L3 LLM 语义增强（接口已预留）、L4 多维归因（框架已预留）
- 情绪真实数据 pipeline L0→L1→L2（待 DeepSeek API Key 验证）
- L1→L2 analysis 搁置

### 怎么跑
```
py frontend/serve.py 8080          # 前端 + 反代 + 自动起 uvicorn
py -m pytest tests/ -q             # 提交前（geocode 35 全过；relevance_filter 需 requests）
```

### ⚠ 注意
- AMAP_KEY 仅服务端 `.env`，高德 GCJ-02→WGS84 红线守住。
- 每完成一件事必更 `todo.md` + `docs/revision-log.md`。只说"交接"时才更本卡。
- 不做 feature branch，main 上直接 commit→push。
- `.sb-results` 依赖 `.search-bar` 的 `overflow:visible`（已修），勿加回 `overflow:hidden`。
- `serve.py` 的 `?v=<mtime>` 只覆盖 HTML 中 `<script>` 标签；ES module import 链不受保护，改 JS 后需 Ctrl+Shift+R。
