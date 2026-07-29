# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-07-28 | **操作人**：DeepSeek（ZCode）
> **同步**：git push 后办公室可见。到办公室后读 `OFFICE.md`。

## 本次做了什么

- ✅ EMC v1.0 全局复盘 + 代码审计（`audit/2026-07-28-comprehensive.md`）
- ✅ 全链路耗时分析：p50=27s, p95=93s，根因是 while-loop + LLM 延迟
- ✅ 数据识别深度审查：找到 `pickVisiblePointLayer` + `layerMeta.has_point` 两个盲区
- ✅ 工具调用分析：工具选型 100%，参数填充是瓶颈
- ✅ 5 个根因分析报告（`rootcause/`）
- ✅ CB 体系优化：文件夹重组 + 统一入口 + 环境适配

## 待办公室做

- [ ] 审查 `rootcause/` 中的根因分析，确认修复方案
- [ ] 飞轮测试：`tests/reports/report-2026-07-28-01-llm.md` 中 5 个失败案例排查
- [ ] 渐进式 token 流式实现（方案 A：绕过代理直连后端）
- [ ] 参数填充强化（system prompt 指引 + 前端预检）
- [ ] Phase 4 清理：删除 v1 诊断管线

## 关键文件速查

| 看什么 | 路径 |
|------|------|
| CB 全貌 | `docs/catch-ball/_cb-index.md` |
| CB 规则 | `docs/catch-ball/RULES.md` |
| CB 记忆库 | `docs/catch-ball/KNOWLEDGE.md` |
| 全局审计报告 | `docs/catch-ball/audit/2026-07-28-comprehensive.md` |
| 深度审查报告 | `docs/catch-ball/audit/2026-07-28-deep-dive.md` |
| 飞轮测试 | `tests/reports/report-2026-07-28-01-llm.md` |
