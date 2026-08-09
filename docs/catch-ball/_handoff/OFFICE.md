# 办公室 · 工作交接卡

> **位置**：办公室 | **最后更新**：2026-08-08（今日收工） | **操作人**：claude组（Claude Code）
> **同步**：git push 已完成。明天到公司 git pull 后读本卡 + HOME.md。

## 今日完成（08-08 · CB-17~CB-20 全闭环）

**CB-17**：进度同步 + 下一步安排定稿（用户暂停 2 天后回归·三组收敛）
**CB-18**：整体验收（验收交两组走 CB·W-1/W-2 修复 + S-1~4 补证）
**CB-19**：修复全闭环——P3-4 地点联动（prop_cols 放行 place_name + buildZonalFc 透传 + 出口卡动态标注）+ PRM-03/04/05/07 根治（G5 多工具重写 + zonal fallback + 黑名单单要素拒识）+ 深读修复协助（两组详读）+ 发版回归全面测试（三组协同·B3 24/26 92% 历史最佳）+ 黑名单误伤修复（5115d7c·Codex T7 阻断）+ P2-2 boundaryLabel（治 `[object Object]`）+ P2-3 verify 断言加严
**CB-20**：PRM-07 空对象根治（方案 A request_upload 短路 + B handler 兜底·两组预检通过）

**最终状态**：发版候选通过（两组确认）·fail 集判据 {PRM-03/04} 达成·全部修复已推·工作区干净·与 origin 同步 @ `903632e`

## 明天待做（公司电脑）

- [ ] `git pull`（拉取今日全部 push）
- [ ] 读 HOME.md + 本卡 + cb-index（CB-20 最新）
- [ ] **测试三组并行新规**（08-09 定）：测试任务改三组（claude组/codex组/glm组）并行分布式执行·claude组 拆解分配·持续提 CB 机制优化意见。
- [ ] **两组环境自检已收**（08-09）：glm 7/7 OK 全能力·Codex 5 OK + 2 WARN（SessionStart hook 已补 `.codex/hooks.json`·多模态 Key 缺失→Codex 不承接多模态/OCR）。分配时按承接能力矩阵（下段）针对分配。

## 三组承接能力矩阵（08-09 自检评估后定）

| 测试类型 | claude组 | codex组 | glm组 |
|---|---|---|---|
| pytest 全量/单测回归 | ✅ 主责 | ✅ | ✅（41 passed 实测） |
| B3 飞轮/e2e 浏览器 | ✅ 主责 | ✅（Playwright 1.60 已验） | ✅（chromium 可启动） |
| trace 取证/根因定案 | ✅ | ✅（trace_query 可跑） | ✅ **强项**（trace.log 直读） |
| 静态核验（代码级 file:line） | ✅ | ✅ 强项 | ✅ |
| 多模态/OCR（讯飞/火山 Key） | ✅（Key 全） | ❌（Key 缺·不承接） | ⚠️ 需确认 |
| MCP 视觉（vision-bridge） | ✅ | ⚠️（配置就绪未实测） | ⚠️ 需确认 |

- **session 标签纪律**（glm 实测采）：`EMOTION_TRACE_SESSION` **仅 B3/e2e 浏览器用例带**（产 trace）；pytest 单测/静态核验不产 trace·**无需带**。分配任务时标注测试类型。
- **端口隔离**：三组并发 B3 必用 `--port/--backend-port` 隔离 + `sys.executable`（8080/8000 已被 claude 占）。

## 关键文件速查

| 看什么 | 路径 |
|------|------|
| CB 入口 | `docs/catch-ball/_cb-index.md` |
| CB 轨迹 | `docs/catch-ball/cb-journal.md`（CB-17~20 最新） |
| 发版回归结果 | `docs/catch-ball/discuss/发版回归全面测试_结果_*2026-08-08.md` |
| PRM-07 根治 | `docs/catch-ball/discuss/PRM07空对象根治_*2026-08-08.md` |
| todo 日志 | `docs/todo.md` |
| revision-log | `docs/revision-log.md` |
| 记忆索引 | `~/.claude/projects/d--Github-emotion-map/memory/MEMORY.md` |

## 关键 learning（今日·防踩坑）

- **两组介入须先落文档 + push**（cb-must-materialize-docs·用户指示）
- **黑名单/守卫须区分 LLM 直传 vs 图层解析**（单要素 vs 多要素·5115d7c 教训）
- **`_regions` 正则只匹配区/市/县后缀**·法定功能区名提取不到（CB-20）
- **LLM 传参方差是 EMC 固有边界**·守卫覆盖可控场景即可（CB-20）
- **B3 后台跑需 `--port/--backend-port` 隔离 + sys.executable**（三组并发·基建 4 commit）
