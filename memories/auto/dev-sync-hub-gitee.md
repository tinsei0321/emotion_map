---
name: dev-sync-hub-gitee
description: 双机同步架构：H:\DEV-SYNC-HUB 移动硬盘中枢 + Gitee 主远程(origin) + GitHub 镜像(github)·两端对称
metadata: 
  node_type: memory
  type: project
  originSessionId: fa3079ae-5450-47ef-8131-fa29a5e67eab
  modified: 2026-08-17T05:16:07.589Z
---

双机（office=BF-202608101011 无 GitHub / home=LAPTOP-HB0DA58R）同步架构，2026-08-17 定型：

- **仓库远程**（两端对称）：`origin` = Gitee `gitee.com/tinsei0321/emotion_map`（主同步·全分支+标签）；`github` = GitHub 同名仓（镜像备份·office 不可达时容错跳过）。
- **H:\DEV-SYNC-HUB**（移动硬盘·盘符无关）：office↔home 唯一离线载体。日常只用两个入口：`一键到达.bat`（hub ff 合并 + gitee pull + 记忆恢复）、`一键离开.bat`（hub WIP提交+全分支推盘仓+bundle 兜底 + 记忆快照 + `push origin --all`/`--tags` 推 Gitee + github 镜像）。英文版 Leave/Arrive.bat 为旧简化包装。
- 盘仓保护：`receive.denyNonFastForwards=true`；arrive 只 ff，分叉只报警；refs/origin-mirror/ 现在是 **Gitee 镜像**（status.ps1 界面文案仍写"GitHub"·已知陈旧）。四层兜底：盘仓 backups refs(30 时间点) / bundles(留10) / 两端本地 .git / logs\timeline.csv 账本。
- 记忆快照按机器分侧存 `memory\<office|home>\`，密钥默认排除；仓库内 `tools/memory_sync.py` 做蒸馏层镜像（push/restore）。
- 历史提交里的 `[SYNC-WIP] ... 离盘自动快照` = leave.bat 自动兜底提交，非人工 commit；回到岗可 `git reset --soft HEAD^` 展开。

相关：[[session-handoff]]
