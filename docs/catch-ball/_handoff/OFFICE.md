# 公司 · 工作交接卡

> **位置**：公司 | **最后更新**：2026-08-25 凌晨（**home 预置·office 到岗续点**·zcode） | **同步**：分支 `EMC_Codex_Harness`（⚠ 已更替·旧分支删除）。

## office 到岗清单（08-25·zcode 预置）

1. `git fetch + git switch EMC_Codex_Harness`（⚠ 分支已更替·旧 EMC_harness_dsh 已删）→ `git fsck --no-progress | head` 体检（R25）
2. 环境差异注记：codex 桥依赖 codex-cli（npm i -g @openai/codex·0.149.1）·model 配置经环境变量（CODEX_MODEL_PROVIDER/CODEX_MODEL·默认 deepseek）·复刻清单在 PT-CB15-PROMOTE执行记录
3. 基线确认：python -m pytest tests/ -q（应 595+4）
4. **T1-T8 用户实测**——T8 新增=?engine=codex（EMC 壳里完整 Harness 首测·逐字流式+多轮+工具+出图）
5. 转正批复验（Qoder 14 件修复的 office 侧复测）

---

## 收工快照（08-24 office 班·PT-CB14 全轮）

- **测试+修复+验收一轮闭环**：完整测试（Qoder 四层）→ 用户实测四问题 → 双方独立审查（zcode 审查报告+Qoder 复核·三分歧定谳含一次主检查代码字段错误诚实更正）→ 修复批双包（claude 简单四件+Qoder 复杂五子件）→ 回收裁决+跨包验证出图实证 → **全局切 flash**（用户令）。
- **当前基线 581+2**；EMC 全链路恒 flash（后端+dsh 双 profile·三处切换验证过·初验含出图）。
- **测试纪律 R25 新入册**：通道测试≠行为测试（真实复杂问题×3 次稳定性）+检查代码自验字段。
- 修复批关键产出：qty 体检点层 11 层注册（停车出图路径通）/persona 出图直出（9 轮 0 反问）/超时重试 v3/代理 600s/引擎徽标可见。

## home 到岗入口

1. `memories/repo/session-handoff.md`（当前节点=home 续点）
2. `PT-CB14-修复批回收裁决_zcode-2026-08-24.md` + `PT-CB14-全局切换flash_zcode-2026-08-24.md`（当日两定稿）
3. 体检医生专题方向框架：`PT-CB10-Kimi预期目标清单` 相关节 or 向主手要（框架已备）

## 待办移交

- **home zcode**：flash+max ×3 补验 → T1-T7 重跑或体检医生专题（用户定）
- **用户**：D-5 取证时间点 / 堆积会话清理确认

## 禁止事项

main 冻结；EMC 恒 flash（勿回 pro）；R25 纪律；未 push 不算交付。
