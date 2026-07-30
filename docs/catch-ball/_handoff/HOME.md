# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-07-30 | **操作人**：Claude Code + DeepSeek
> **同步**：git push 后办公室可见。到办公室后读 `OFFICE.md`。

## 当前状态

- **分支**：`fix/emc-buglog` @ `7126f6d`（昨晚稳定版本）
- **今天所有改动已回退**——反复修改均未达预期，详见 SESSION 记录
- **接手文档**：`DEEPSEEK_ONBOARDING_2026-07-30.md`

## 待做（优先级排序）

- [ ] **P0**：修复 FC 诊断 no_tool_calls→回退旧路径的阻断问题
- [ ] **P1**：Pro 模式最终结论生效（`answerModel = ctx.model || 'flash'`）
- [ ] **P1**：多步骤合并扩展（`_autoExpandOverlays` 支持 overlay union 模式）
- [ ] **P2**：方案 A Planner 的 where 格式对齐 + 前端缓存修复
- [ ] 测试回归：剪裁西陵区3类用地 / 合并3个图层 / Pro 结论质量

## 关键文件速查

| 看什么 | 路径 |
|------|------|
| Session 完整记录 | `docs/catch-ball/_handoff/SESSION_2026-07-30.md` |
| DeepSeek 接手文档 | `docs/catch-ball/_handoff/DEEPSEEK_ONBOARDING_2026-07-30.md` |
| CB 入口 | `docs/catch-ball/_cb-index.md` |
| todo 日志 | `docs/todo.md` |
| revision-log | `docs/revision-log.md` |
