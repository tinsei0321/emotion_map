# memories/ — 跨机记忆目录

| 子目录 | 内容 | 维护方式 |
|---|---|---|
| `repo/` | 跨机会话交接卡（session-handoff 等） | 手写·随 git 同步 |
| `auto/` | AutoMemory 蒸馏层镜像（~/.claude/projects/d--Github-emotion-map/memory/） | `memory-sync.bat` 双击镜像·勿手改 |

`auto/` 的意义：AutoMemory 本体在 C 盘（机本地），经此镜像入 repo 后随 Gitee 双机同步——
机器+硬盘同时损毁时的最后一层记忆保险。恢复用 `py tools/memory_sync.py pull`（覆盖本地·带确认）。

全量对话 context 不同步到云端（密钥明文风险 + GB 级体积），走 DEV-SYNC-HUB 硬盘 `Memory.bat` 分侧快照。
