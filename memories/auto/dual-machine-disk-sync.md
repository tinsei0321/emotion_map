---
name: dual-machine-disk-sync
description: 双机同步 = DEV-SYNC-HUB 硬盘专区（office 部署的四 bat），home 侧旧工具链已删；远端策略 origin→Gitee（office 可达），GitHub 降级 home 备份镜像
metadata: 
  node_type: memory
  type: project
  originSessionId: 2c3934a3-cd04-4f57-ad3f-4072fab441eb
  modified: 2026-08-15T14:22:53.760Z
---

双机同步体系（v2·2026-08-15）：同步机制 = office 部署的 **DEV-SYNC-HUB 移动硬盘专区**（`E:\DEV-SYNC-HUB`，盘符无关）；home 侧 08-14 自建工具链（sync_guard.py/双 bat/SessionStart hook/规则文档）已于 `89ce0f2b` **全部删除**，被 HUB + Gitee 方案取代。

**Why:** 公司无 GitHub 外网；曾靠整目录拷贝致 untracked 反复回流。首次通过 HUB 合流已完成（2026-08-15，报告 = `docs/sync-reports/2026-08-15_双环境合流同步报告.md`），本地=盘仓=GitHub 三方一致 `87c31bdd`，零内容丢失。

**How to apply:**
- **纪律**：离开任一环境双击 HUB 根目录 `Leave.bat`（WIP 兜底提交+push 全分支+backups 快照+增量 bundle+账本）→ `Memory.bat`（C 盘对话 context 六工具分侧快照入 `memory\<role>\<工具>\`）→ repo 根 `memory-sync.bat`（AutoMemory 蒸馏镜像 → `memories/auto/` + push Gitee）；到岗双击 `Arrive.bat`（fetch+**只做快进**）；跨机衔接 = 会话开场读 `E:\DEV-SYNC-HUB\memory\<对端>\claude\` 最近会话尾部 + 对端 MEMORY.md。`Status.bat` 体检、`Rescue.bat` 四层恢复；`Memory.bat pull`/`memory_sync.py pull` 仅迁移/灾难用（/MIR 覆盖）
- **记忆三层**：盘快照（全量·主力）+ AI 分侧阅读（同步语义）+ Gitee `memories/auto/`（蒸馏·末日保险）；全量 context **不上云**（密钥明文+GB 体积）；registry 密钥排除 = codex auth.json / zcode credentials.json+certs / dsh .credentials.yaml
- **机器**：office = `BF-202608101011`（`D:\Github\emotion_map`，无外网）；home = `LAPTOP-HB0DA58R`（`d:\Github\emotion_map`，唯一外网枢纽）。registry.json 已双端登记
- **远端策略**：origin 改指 **Gitee**（office 可达，日常同步走远端），GitHub 改名 `github` 仅作 home 侧备份镜像；office 换绑后仍保 HUB 作备份层
- untracked 不 commit 永远不同步；`codex/dsh-onboarding` 是工作分支（Codex/ZCode 建），main = `4f6fac71` 双侧一致未动；`receive.denyNonFastForwards=true` 保护盘仓历史
- 相关：[[dual-env-schema-divergence]]（双环境并行编辑的其他风险）
