# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月18日（**项目全局复盘 + CB-1（SCAN_DeepSeek 反评价）实质完成**）| 分支 `main` | 本次会话 = 5.132–5.135

---

## 当前节点：CB-1 实质完成；明天换环境续（前端 JS 单测 / browser 复验 / 待 CB-2）

### 背景
07-18 上半场（5.129–5.131 复盘修复日）已在 origin。**本会话**用户要做项目全局复盘 + 引入第三方评价（`docs/SCAN_DeepSeek.md`，DeepSeek V4 Pro）做 **catch-ball（CB）**：我方复盘 → 读 SCAN → 反评价（agree/disagree/partial）→ 行动 → 定期总结。CB 轨迹在 [docs/cb-journal.md](docs/cb-journal.md)。

**我方复盘 ~7.6/10**（架构 8.5/模块 7.0/数据管道 7.5/测试 7.5/债 7.0/文档 8.0）。用户澄清关键策略：**L0 未来走购买途径，sim 当下充分非风险**（memory `l0-acquisition-purchase-strategy`）。唯一真短板 = 前端测试薄。

### ✅ 本会话已做（5.132–5.135，每 commit 同步 todo + revision-log §5 + cb-journal）

| commit | 5.NNN | 内容 |
|---|---|---|
| `3edbb90` | 5.132 | CB-1 反评价 + geo_routes 三处清理 + sim agent 注册 + cb-journal 建 |
| `5e7b8c6` | 5.133 | 删 4 僵尸（ui_components/layer_registry/map_engine/.streamlit，-1439 行）+ 入库 .zcode/SCAN + retired.md |
| `3fd4129` | 5.133 | Tier 1 文档卫生：tracking-progress 漂移修（指 AGENTS.md 权威源）+ §0 主干 refresh |
| `e91aaf5` | 5.134 | ?e2e=1 seam 去生产化（main.js 零 test 代码→独立 e2e-seam.js + index.html 条件 dynamic-import）+ §0 补 topology/AI 7 月 |
| `8cea41a` | 5.135 | db.py 退役（SCAN 建议7 declined，死代码）+ zonal_stats latent bug wontfix（无消费方） |

**全部已 push 至 origin**（用户手动推 3edbb90/5e7b8c6/3fd4129/e91aaf5；8cea41a 本次按用户「commit push」由 Claude 推）。

**CB-1 declined（证据挡低价值活）**：SCAN 建议1-4 调用次数（前提不成立·项目不派 subagent）/ 建议4 MANIFESTO 分层（撞 diagnose 永不动承重红线）/ MCP 与 DeepSeek 匹配论（错标尺）/ 建议7 db.py iterrows（死代码 + insert_points 早已 executemany）/ zonal_stats latent bug（无活消费方）。

### 🎯 下一步（明天换环境后续，择序）
1. **前端 JS 单测基建**（Tier 2，头号短板，**不依赖 browser**）——最大剩余价值。先切一刀：`field_dictionary.js` / `boundary-resolve.js` / `import.js` 纯函数补 jest/vitest 单测；JSDoc 类型注释（不引 TS，保零构建）。
2. **browser 环境挂排查 + 复验**（5.134 seam 改动是 async-loading，需 browser 真验；本会话两次跑 `test_compare_regions.py` 都挂死在 pre-seam 的 open_emc 阶段，疑似 serve/Playwright 环境 问题，**非 seam 问题**——seam 坏会 45s 退出非挂死）。换环境后先跑一次确认。
3. **C6 补 3 例**（domain_lens / _driftRe / 路由分歧，browser e2e，需环境恢复）。
4. **CB-2**：等用户用 DeepSeek 二次扫描（对比验证 CB-1 改进）→ 开 CB-2 轮。
5. 9⬜ tracker 埋点细化（低优先）。

### Push 状态
**全部已 push**（origin/main 含至 `8cea41a`）。明天换环境 `git pull` 即可同步。

### 承重（必守，下会话续改时留意）
- **调动次数优先**（用户全局规则，覆盖 plan mode 派 Explore/Plan 默认）：不派 subagent，自己读/grep/改；批量并行只读；合并多文件修改；给推荐不穷举。
- **CB 反评价标尺**：agree/disagree/partial 有论据；承重红线（tracker 编号连续 / diagnose 永不动 / 四态出口）不接受简化；L0 购买策略勿把 sim 当风险。CB 轨迹按轮追加 `docs/cb-journal.md`（不覆写）；不编辑 `docs/SCAN_DeepSeek.md`（第三方专属）。
- **?e2e=1 seam 已去生产化**（5.134）：seam 在 `frontend/js/e2e-seam.js`（独立），`index.html` 条件 dynamic-import（仅 ?e2e=1 加载，生产永不加载）；main.js 零 test 代码。**待 browser 真验**（环境挂未解）。
- **browser 环境挂**（未解）：本会话 serve/Playwright 启动卡在 open_emc，疑似环境问题。明天换环境先跑 `py tests/browser/test_compare_regions.py` 验 seam + 排查。
- **退役台账** `docs/retired.md`：apps/ + ui_components + layer_registry + map_engine + .streamlit + db.py（皆 git 可恢复）。
- **EMC 承重（沿用）**：L4 lazy enrichment / Sim 资讯+buffer 方法论 / compare 技能契约 / 委托主 Toolbox 不自造 / aggregate 别名静默零（resolve_field_alias）/ diagnose prompt 永不动保 Flash eval / 四态出口+frame-based trust / C6（eval 空 context≠运行时）/ node --check ESM 假绿须 .mjs。
- **项目顶层设计哲学**：4×5=归因矩阵（非指标清单）+多归属+政策→情绪→项目闭环+补盲区+知识库可成长；勿用官方指标完备性质疑 4×5（错标尺）。
- 专业词+通俗解释（用户是初学者）/ todo+revision-log 最新置顶同步 / 交付物中文（代码/路径英文）/ 只 commit 不 push（用户手动；本次「换环境」例外已 push）。

### 本轮改的关键文件
- **CB-1 清理**：[api/geo_routes.py](api/geo_routes.py)（三处冗余清 + zonal_stats wontfix 注释）/ [.claude/settings.json](.claude/settings.json)（sim agent 注册，8→9）。
- **退役**：[core/__init__.py](core/__init__.py)（docstring 去 map_engine/ui_components）/ [docs/retired.md](docs/retired.md)（台账）。
- **入库**：[.zcode/](.zcode/)（ZCode 工具状态·双环境同步）/ [docs/SCAN_DeepSeek.md](docs/SCAN_DeepSeek.md)（CB 输入历史，**第三方写勿编辑**）。
- **Tier 1 文档**：[memories/repo/tracking-progress.md](memories/repo/tracking-progress.md)（指 AGENTS.md 权威源）/ [docs/revision-log.md](docs/revision-log.md) §0 任务树刷新（主干+topology+AI 7 月）+ §5（5.132–5.135）/ [docs/cb-journal.md](docs/cb-journal.md)（CB-1 轨迹）/ [docs/todo.md](docs/todo.md)。
- **seam 去生产化**：[frontend/js/e2e-seam.js](frontend/js/e2e-seam.js)（新）/ [frontend/js/main.js](frontend/js/main.js)（seam 移出）/ [frontend/index.html](frontend/index.html)（条件 dynamic-import bootstrap）/ [tests/browser/lib/emc_helpers.py](tests/browser/lib/emc_helpers.py)（注释）。

### 承重 memory 索引
- 本会话新增：`l0-acquisition-purchase-strategy`（L0 走购买·sim 充分非风险）。
- 复用（明天续参照）：`project-design-philosophy` / `emotion-map-logic-chain` / `context-coherence-discipline` / `token-saving-workstyle` / `maintain-revision-log` / `todo-revision-log-sync` / `no-handoff-on-routine-commit` / `commit-only-user-pushes`（本次换环境例外）/ `chinese-all-deliverables` / `pro-term-plus-plain-meaning` / `node-check-esm-unreliable` / EMC 系 / `sim-research-buffer-methodology` / `verify-real-endpoint` / `stand-on-giants-shoulders`。

---

## 新会话 prompt（明天换环境，复制即用）

```
接续 07-18 会话（项目全局复盘 + CB-1 实质完成，5.132–5.135 全部已 push，详见 memories/repo/session-handoff.md）。
本会话目标（择序，明天定）：
1. 前端 JS 单测基建（头号短板，不依赖 browser）——先切 field_dictionary/boundary-resolve/import 纯函数。
2. browser 环境挂排查 + 5.134 seam 去生产化复验（跑 py tests/browser/test_compare_regions.py）。
3. C6 补 3 例（domain_lens/_driftRe/路由分歧）。
4. CB-2（等用户 DeepSeek 二次扫描）。

先读（不动代码）：
- memories/repo/session-handoff.md（当前节点 + 承重）
- docs/cb-journal.md（CB-1 轨迹 + declined 清单）
- docs/revision-log.md §0（任务树已刷新）+ §5（5.132–5.135）

承重：调动次数优先（不派 subagent）/ CB 反评价标尺（承重红线不接受简化）/ L0 购买策略勿把 sim 当风险 / browser 环境挂未解（换环境先验）/ 只 commit 不 push（用户手动）。
```
