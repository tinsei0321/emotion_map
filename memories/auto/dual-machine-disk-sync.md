---
name: dual-machine-disk-sync
description: 双机同步 = DEV-SYNC-HUB 硬盘专区（office 部署的四 bat），home 侧旧工具链已删；远端策略 origin→Gitee（office 可达），GitHub 降级 home 备份镜像
metadata: 
  node_type: memory
  type: project
  originSessionId: 2c3934a3-cd04-4f57-ad3f-4072fab441eb
  modified: 2026-08-15T13:13:55.378Z
---

双机同步体系（v2·2026-08-15）：同步机制 = office 部署的 **DEV-SYNC-HUB 移动硬盘专区**（`E:\DEV-SYNC-HUB`，盘符无关）；home 侧 08-14 自建工具链（sync_guard.py/双 bat/SessionStart hook/规则文档）已于 `89ce0f2b` **全部删除**，被 HUB + Gitee 方案取代。

**Why:** 公司无 GitHub 外网；曾靠整目录拷贝致 untracked 反复回流。首次通过 HUB 合流已完成（2026-08-15，报告 = `docs/sync-reports/2026-08-15_双环境合流同步报告.md`），本地=盘仓=GitHub 三方一致 `87c31bdd`，零内容丢失。

**How to apply:**
- **纪律**：离开任一环境双击 HUB 根目录 `Leave.bat`（WIP 兜底提交+push 全分支+backups 快照+增量 bundle+账本）；到岗双击 `Arrive.bat`（fetch+**只做快进**，分叉只红灯报警不动手）；home 离盘前**额外 push 远端**。`Status.bat` 体检、`Rescue.bat` 四层恢复
- **机器**：office = `BF-202608101011`（`D:\Github\emotion_map`，无外网）；home = `LAPTOP-HB0DA58R`（`d:\Github\emotion_map`，唯一外网枢纽）。registry.json 已双端登记
- **远端策略**：origin 改指 **Gitee**（office 可达，日常同步走远端），GitHub 改名 `github` 仅作 home 侧备份镜像；office 换绑后仍保 HUB 作备份层
- untracked 不 commit 永远不同步；`codex/dsh-onboarding` 是工作分支（Codex/ZCode 建），main = `4f6fac71` 双侧一致未动；`receive.denyNonFastForwards=true` 保护盘仓历史
- 相关：[[dual-env-schema-divergence]]（双环境并行编辑的其他风险）
