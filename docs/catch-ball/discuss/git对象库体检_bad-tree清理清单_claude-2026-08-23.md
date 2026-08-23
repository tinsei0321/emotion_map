# git 对象库体检 · bad-tree 清理清单（claude·2026-08-23·报主手）

> 执行：`git fsck --no-progress` 全量 + `git fsck HEAD`（家机·08-23 晚·**只读取证·零 prune/repack 实操**）。
> 背景：08-23 15:55 git gc 中断事件（Kimi 记录：gc.pid 死进程 → refs 清空 + 274MB tmp_pack 截断 + 对象整链缺失）恢复后（fetch + update-ref + unpack-objects 救回 11,744 松散对象）的**首次全量体检**。事件全貌见 `事件记录-git对象库损坏与恢复指引_2026-08-23.md` + debug-memory R25。

## 一 体检账目

| 项 | 数量 | 说明 |
|---|---|---|
| broken link（树→树/树→blob） | **1,636** | `git fsck HEAD` 同数——**全部落在 HEAD 可达历史**（17136d3a 经 `merge-base --is-ancestor` 实证·在 main + EMC_harness_dsh 双分支） |
| missing objects | **1,636** | 对应 broken link 的灭失目标（随截断 pack 丢失·本地已无副本） |
| dangling（不可达松散对象） | 1,543 | 恢复期 unpack-objects 所得但无 ref 指向 |
| invalid reflog 条目 | 23 | HEAD/EMC_harness_dsh/stash 各若干 |
| idx-only 残件（.idx 在·.pack 已灭失） | 18 | 中断 gc 已删 .pack·idx 残留（pack-042b568f 等） |
| tmp_pack 残件（.git/objects/pack/ 内） | 2 | `tmp_pack_PxzNld` + `tmp_pack_recover.pack`（各 274MB·截断原物+恢复副本） |
| pack 加载失败 | 3 | multi-pack-index position 0/2/3（midx 仍引用已删/坏 pack） |
| 松散对象 | 11,825 | 恢复所得 11,744 + 事件后新提交 |
| HEAD fsck exit code | **34** | 非零 = 历史完整性受损（非干净仓） |

## 二 现状判定

- **日常链路可用**：status/log/commit/push 全部正常·工作树零损失·分支已对齐 origin（本日双 commit 已推）。
- **历史链路受损**：`git show`/`git diff` 旧 commit、`git log --stat` 涉旧树操作会失败；受影响 commit 横跨 main 与 EMC_harness_dsh 两支（样本见 §四）。
- **gc/repack 高危**：multi-pack-index 引用 3 个不可加载 pack + 18 个已删 pack + 2 个 274MB 截断残件——**此刻任何 gc/repack 可能再产出残缺 pack 或失败**（与 R25 预防四条「多组并发仓禁窗口期 gc」一致）。

## 三 清理清单（报主手·建议序·**本组只报不实操**）

| # | 动作 | 命令/说明 | 风险 |
|---|---|---|---|
| 1 | 清 tmp_pack 残件 | 删 `.git/objects/pack/tmp_pack_PxzNld`、`tmp_pack_recover.pack`（各 274MB·截断物） | 无（无 idx 引用） |
| 2 | 清 idx-only 残件 + 重建 midx | 删 18 个 `.idx`（对应 `.pack` 已灭失者）→ `git multi-pack-index expire` + `git multi-pack-index write` | 低·纯索引层 |
| 3 | reflog 清洗 | `git reflog expire --expire=now --all`（清 23 条 invalid 行） | 低·仅日志 |
| 4 | **历史对象补全** | 关键点：**`git fetch origin` 不会自动补**——18 个 idx 残件让 git 误判「对象已持有」→ 必须先做完 #2 清 idx，再 `git fetch origin`（重谈缺失对象）→ `git fsck` 复检 | 中·务必先 #2 |
| 5 | 兜底方案 | 若 #4 后仍有 missing → 全新 `git clone` + 工作树迁移（R25 恢复六步法·`_tmp/pack_quarantine/` 内 pack-064a3518.pack 为参照物·勿删） | 中·耗时可观 |
| 6 | 终验 | `git fsck` 零 error + `git log --stat --oneline | head` 抽查旧 commit 可读 + 一次 push 往返正常 | — |

**时机建议**：月度独占 gc 窗口内执行（R25 预防四条）·执行前确认无其他组在仓（并发仓禁窗口期 gc 已两轮教训）。

## 四 broken-link 受影响 commit 样本（前 20·共 1,636 条）

```
17136d3a cbe49fad b7f1f97c 985942c2 5966d822 adb8710b 246dec27 1b4c097f
21e368ad a2970126 e03e3636 0378e79c 07ed76d5 be3f6b30 b0287da9 8f382b91
58de4603 5377027e b13eb62f f056c1e0
```

全量 broken/missing 明细在 `git fsck --no-progress` 输出（主手可复跑取全文）。

—— claude · 2026-08-23 · 家机 · 零实操
