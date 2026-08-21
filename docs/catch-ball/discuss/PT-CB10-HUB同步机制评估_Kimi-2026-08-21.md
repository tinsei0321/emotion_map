# PT-CB10 · DEV-SYNC-HUB 同步机制评估（Kimi·2026-08-21）

> **性质**：应用户要求对 H:\DEV-SYNC-HUB 做只读扫描，对照计划书（核心思想 v1.1 双环境同步目标 + 规则七 + M0-M3）评估机制能否达标。零实施：未修改盘上/仓内任何文件。
> **扫描对象**：`H:\DEV-SYNC-HUB\`（README/registry.json/bin/*.ps1/state/logs/repos/backups/memory）+ 本地仓库与盘仓的版本比对 + office 网络可达性实测。

---

## 〇 一页结论

| 层 | 机制能否实现计划书目标 | 判定 |
|---|---|---|
| ① 仓库代码层 | **能，且设计精良——但当前处于严重空转状态**（office 领先盘仓 204 commit，4 天未 Leave） | 机制不用重构，要补执行纪律 |
| ② dsh 环境层（~/.dsh） | **不能**——文件级镜像与计划书的「配方化」路线方向冲突，且快照停在 08-17，T7 双模预设等关键环境根本不在盘上 | 按 M1-M3 配方化（原计划），HUB 镜像降级为参考快照 |
| ③ 可重建资产层（索引/缓存） | 能——排除规则正确（node_modules/沙箱缓存均不同步） | ✅ |
| ④ 密钥安全 | 能——.credentials.yaml/auth.json/credentials.json/certs 均已排除 | ✅ |
| ⑤ 10-15 分钟到岗恢复 | 不能——缺配方与体检脚本（这正是 M1-M3 存在的意义，HUB 不背这个锅） | 等 M1-M3 |

**问题 2 的答案（不需要移动仓盘也能同步吗）：能，仅就代码层**——实测 office 到 gitee.com 网络可达（curl HTTP 200；此前 git fetch 失败只是无存储凭据的非交互报错，不是网络不通）。配上 gitee 凭据后 office 可直连 gitee 与 home 双向同步，HUB 降级为「大文件/记忆快照/演示包 + 离线兜底」通道。注意事项见 §三。

---

## 一、扫描证据

### 1.1 HUB 机制设计（README + bin/*.ps1 核实）

- 盘仓裸仓 `repos/emotion_map.git`：`receive.denyNonFastForwards=true`（拒改写历史）；leave.ps1 推全分支+tags，并镜像 `refs/remotes/origin/*`；WIP 兜底提交；bundle 全量+增量链；refs/backups 留 30 时间点；fsck 校验；timeline.csv 账本。**四层兜底设计完整，08-15 恢复实测 PASS 在档。**
- 记忆同步（memory.ps1）：robocopy /MIR 按机器分侧镜像（office/home 互不覆盖），公共排除 `__pycache__/node_modules/.git`，密钥文件逐项排除。设计合理。

### 1.2 空转证据（关键发现）

| 证据 | 数值 |
|---|---|
| 最后一次 Leave | 2026-08-17 01:48（home 端） |
| 最后一次 office Arrive | 2026-08-17 15:23 |
| 盘仓 EMC_harness_dsh 版本 | `0ebbe9f`（08-17） |
| office 本地 HEAD | `7a848dfd`（08-21·PT-CB10） |
| **本地领先盘仓** | **204 个 commit（PT-CB1~CB10 四天全部产出）** |
| 最新 bundle | 20260817（同 4 天前） |
| 盘上 dsh 快照的 profiles | **只有 `web`**——本机现有 emc-analysis/emc-research/emc-test/emc-test-headless + .agent-presets 五个预设 + ptcb8-t7-backup 全部不在盘上 |

**含义**：①规则七「未 push 不算交付」——四天的批次交付物在双环境视角下全部未交付；②L3 兜底（对端 .git）实际失效——office 磁盘若此刻损坏，四天工作零副本；③核心思想 v1.1 认定的「最大断点」（T7 双模预设只在 office ~/.dsh）在 HUB 里依然断着。**这是「机制空转」的实锤案例（呼应 Kimi 任务设计书 P-4）：机制建好了，没有人按按钮。**

### 1.3 dsh 环境层的方向冲突

即便 Memory.bat 今天跑起来，文件级镜像也不等于计划书的「环境即代码」：
- profiles/settings 中的绝对路径（`C:\Users\Administrator`）、junction、file: 依赖原样搬到 home（`C:\Users\Hi`）即失效——核心思想断点 3/4 明令禁止手工搬运；
- HUB 的设计是「分侧存放 + 人工阅读合并」，合并成本留给人——与「10-15 分钟到岗恢复」目标不兼容；
- 正确路线仍是 M1-M3（配方入仓→manifest→体检脚本），配方走 git（HUB 或 gitee 都能传），~/.dsh 镜像只作参考快照。

---

## 二、重构 plan（仅针对不达标的两层）

**不需要重构 HUB 引擎本身**（代码层机制设计精良）。需要四件事：

| # | 动作 | 归属 | 成本 |
|---|---|---|---|
| R1 | **立即止血**：office 双击 Leave.bat（204 commit 上盘 + bundle + 记忆快照含 T7 预设） | 用户·今天 | 5 分钟 |
| R2 | **纪律入册**：Leave/Arrive 嵌入开工/收工 SOP——主手 C4 清账时检查 `state/emotion_map.json` 的 lastLeave 日期，超 24h 未 Leave 即亮红灯；此项写入 M3 到岗体检脚本 | 主手·随收口批 | 0.5 天 |
| R3 | **dsh 环境层按计划书 M1-M3 配方化**（原案不动），HUB 记忆同步定位改为「会话记录/蒸馏记忆迁移」通道，profiles/presets 以仓内配方为权威源 | 阶段 C | 按 M1-M3 原估 |
| R4 | **直sync 双轨过渡**：office 配 gitee PAT → 代码层双写（push gitee + Leave 上盘）并行 2 周 → Status.bat 扩展比对 gitee 与盘仓一致性 → 连续一致后 HUB 降级为周备份+大文件通道 | 见 §三 | 1 天 |

---

## 三、不需要移动仓盘也能同步：注意事项（gitee 直连方案）

**前提已验证**：office→gitee.com 网络可达（HTTP 200）。缺的只是凭据。office 配好 gitee PAT 后，代码层同步可以完全不依赖盘。注意事项：

1. **凭据管理**：gitee PAT 只授 repo 最小权限；存 Windows Credential Manager（`git config --global credential.helper manager`）；**禁写进 remote URL**（会落 .git/config 明文，且可能随配置分享外泄）。PAT 本身=秘密资产——只同步「变量名与配置方法」，值禁入库禁搬运（核心思想 C 类纪律）。
2. **规则七表述更新**：office 的「push 才算交付」口径从「Leave 上盘」改为「push origin(gitee)」——涉及 AGENTS.md/核心思想 v1.1 的措辞修订，**须走 CB 流程裁决**，不悄悄改。
3. **双写冲突窗口**：两端都能推 gitee 后，纪律平移 HUB 的 ff-only——开工先 `git pull --ff-only`，分叉只报警不自动改写；gitee 服务端默认拒非快进（与盘仓 denyNonFastForwards 等价）。
4. **main 冻结不变**：只推 EMC_harness_dsh 等工作分支；home 的 GitHub 备份职责不变（gitee→github 定期镜像）。
5. **不要试图让大文件走 gitee**：记忆快照 3.3GB、演示包（自带 Python 运行时+BGE 模型）走 git 会炸仓库——**这部分 HUB 不可替代**，直sync 后 HUB 仍是大文件/演示包/离线兜底通道。
6. **网络依赖的新风险**：原 HUB 路线是离线闭环，直sync 后同步纪律被 gitee 可用性绑定——gitee 抽风时回退 HUB（双轨过渡期正好覆盖此风险）。
7. **过渡期双写校验**：每天 Leave 时既 push gitee 又上盘，Status.bat 看两边分支矩阵；连续 2 周一致再降级 HUB——防止「新通道没验熟就拆旧通道」（渲染三坑 R11 同款教训：通道切换要双轨验证）。
8. **记忆同步维持走盘**：全量会话快照（3.3GB）不适合任何 git 远端；蒸馏记忆（repo 内 memories/）已走 git，两者定位不冲突。

---

## 四、给控制线的登记建议

- 本评估发现的「HUB 空转」应作为机制空转检测（Kimi 任务设计书 §四-改5）的首个实例入档；
- R1（立即 Leave）为今天可执行的止血动作；R2/R4 建议并入收口批 C4 清账件或 M 系列立项时一并裁决。

---

> Kimi · 2026-08-21 · 只读扫描，零写入（HUB 与本仓均未改动）。
