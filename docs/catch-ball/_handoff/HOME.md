# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-08-08 | **操作人**：claude组（Claude Code）
> **同步**：git push 后办公室可见。到办公室后读 `OFFICE.md`。

## 当前状态（08-08）

- **分支**：`fix/emc-buglog` @ `12aa1f9`（与 origin 同步·工作区干净）
- **CB-19 全闭环**：整体验收（CB-18·交两组走 CB）→ 修复（P3-4 + PRM-03/04/05/07）→ 深读协助 → 发版回归全面测试（三组协同·B3 24/26 92% 历史最佳）→ 黑名单修复复验（两组通过）→ **发版候选通过**
- **发版候选**：fail 集判据 {PRM-03/04} 达成·剩余 fail = {PRM-07 空对象 LLM 方差·RST-L06 Flash 方差}·均已知/方差
- **接手文档**：`DEEPSEEK_ONBOARDING_2026-07-30.md`（历史）

## 待做（优先级排序）

- [ ] **P2-2 已做**（boundaryLabel 治 `[object Object]`·12aa1f9）
- [ ] **P3 文档债**：OFFICE.md 同步（本次·OFFICE 待填）
- [ ] **P3-1 依赖图**：随 P3-2 一起（并行后置·无独立消费者）
- [ ] **后置项**：P2-1 多要素全黑名单增强 · P2-3 verify_prm57 断言加严 · PRM-07 空对象场景 · RST-L06 Flash 方差 · KDE/DBSCAN 替代 Gi* · 时间轴 manifest

## 关键文件速查

| 看什么 | 路径 |
|------|------|
| CB 入口 | `docs/catch-ball/_cb-index.md` |
| CB 轨迹 | `docs/catch-ball/cb-journal.md`（CB-19 最新） |
| 发版回归结果 | `docs/catch-ball/discuss/发版回归全面测试_结果_*2026-08-08.md` |
| todo 日志 | `docs/todo.md` |
| revision-log | `docs/revision-log.md` |
| 记忆索引 | `~/.claude/projects/d--Github-emotion-map/memory/MEMORY.md` |
