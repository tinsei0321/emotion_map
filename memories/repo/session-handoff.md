# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月27日收工（**KDE 情绪地形去 3D 5.225 + Bug5 补记 5.224**）| 分支 `main` | 本次 push

## 当前节点：KDE 去 3D 落地·明早办公室展开大讨论（用户主持·议题未告知 AI）

今日（07-27）收工批次：KDE「情绪地形」去 3D 统一 2D 彩虹热力图（5.225）+ 补记上轮未 sync 的 Bug5（5.224）。**明早办公室环境用户将展开一个"大讨论 + plan"**——议题用户已定但本会话未告知 AI（AI 曾据改动撬动的设计问题猜了 4 条·用户明确澄清"不是这个问题"）·下会话等用户开题再进入 brainstorming。

## 今日已 commit（5.225 / 5.224 · revision-log §5 · branch main）
- **d6b7d2c** 5.225 KDE 情绪地形去 3D·统一 2D 综合彩虹热力图（[heatmap-tool.js](frontend/js/heatmap-tool.js) 单文件：computeStyle terrain 恒出 rainbow 2D + 按钮改名「生成 2D 热力图」+ 删 3D 分支 + 删死码 generateTerrain() + 极性锁综合；未动 Grid 3D + EMC generateTerrainForAI）
- **（补记）** 5.224 Bug5 EMC 折叠胶囊无法展开——0f8761b `_runGuidanceCta` 先展开 / 38b64ed 真根因移除 `cpd:focus-tab` 切走（上轮代码 commit·本次 sync 补入 revision-log §5 + todo）
- **docs(sync)** revision-log §5（5.225 + 5.224 补记）+ todo 当日段 + 本交接卡

## 下会话：明早办公室大讨论（用户主持）

- **等用户开题**：用户将主导一个大讨论 + plan。AI 不要预设议题（本会话猜的 4 条 KDE 连带问题已被用户否决"不是这个问题"）·用户开口后再用 brainstorming 把意图聊透 → 出 plan。
- **KDE 去 3D 连带设计问题**（备查·非大讨论主题·用户已澄清）：「情绪地形」命名（去 3D 后语义失真）/「总体情况」栏仅剩 1 卡 / EMC `generateTerrainForAI` 仍 3D（口径分裂）/ 3D 收口到 Grid / 按钮文案空格。详见 todo 🔄 遗留段。

## 留用户验证 / 未决
- **浏览器验 5.225**：KDE → 总体情况 → 情绪地形 → 单按钮「生成 2D 热力图」→ 2D 综合彩虹热力图（L1/L2 一致·无 3D 入口）。
- **浏览器验 5.224**：EMC 折叠胶囊点击正常展开（cpd:focus-tab 已不切走）。
- **明早大讨论议题**：用户带到办公室。

## 红线 / 纪律（下会话守）
- **承重三不动**：diagnose prompt（prompts.py build_diagnose_prompt）/ harness orchestrate（harness.js orchestrate 主循环）/ ChatRequest schema（schemas.py）—— 改前先扩 eval，每次只改一处，不派 subagent。
- KDE/Toolbox 改动守「视野-数据-结论同步」+「设计语言一致性」；禁 emoji（[OK]/[ERR]）。

## 恢复指引（新会话·办公机）
1. `git log --oneline -8` 对账（d6b7d2c 5.225 / 0f8761b+38b64ed 5.224 / b5b3981 5.223）。
2. 读 [docs/todo.md](docs/todo.md) 当日段（2026-07-27）🔄 遗留 + revision-log §5 最新动态。
3. 等用户开大讨论议题 → brainstorming → plan（不预设）。
