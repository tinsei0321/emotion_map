# 双机同步规则（公司机 ↔ 移动硬盘 ↔ 家机 ↔ GitHub）

> 建立于 2026-08-14。背景：公司电脑连不上 GitHub，靠移动硬盘中转；家机是唯一 GitHub 枢纽。
> 配套工具：`tools/sync_guard.py`（状态/推/拉三模式）+ 根目录 `sync-leave.bat` / `sync-arrive.bat`（双击即用）+ `.claude/settings.json` SessionStart hook（每次 Claude Code 会话开场自动显示同步状态）。

## 一、数据流与角色

```
公司机（领先但连不上 GitHub）
   ↕ syncdisk = 移动硬盘上的 bare 中转仓（<盘符>:/git-sync/emotion_map.git）
家机（能连 GitHub = 唯一枢纽）
   ↕ origin = GitHub
```

- **bare 仓库** = 只有 git 数据、没有工作区文件的中转仓，不会被直接编辑。
- **remote 配置存各机本地 `.git/config`、不随仓库走** → 两边盘符不同（如公司 E:、家 F:）互不影响，各配各的。
- 硬盘**不需要空盘**：中转仓只是盘上一个普通文件夹，与其他内容互不干扰。建议 NTFS 格式、集中放 `/git-sync/` 目录、勿手动编辑其中内容、勿让 OneDrive 类同步盘二次托管。

## 二、日常铁律（防乱核心）

| 时机 | 动作 |
|------|------|
| **离开任一环境前** | 插硬盘 → 双击 `sync-leave.bat`（自动：add -A + commit `chore: sync checkpoint <时间>` + push syncdisk + GitHub 可达则 push origin） |
| **到达任一环境后** | 插硬盘 → 双击 `sync-arrive.bat`（自动：fetch syncdisk + pull --rebase 当前分支） |
| **家机每晚** | 额外 push origin（bat 内已含，连不上自动跳过） |

三条铁律：

1. **untracked 必须 commit 才会同步**——没 `git add` 过的文件不进任何 push/pull（2026-08-14 "大量内容不在远端"的根因）。
2. **冲突显式解决，禁止整目录拷贝覆盖**——出现 rebase 冲突时：改文件 → `git add -A` → `git rebase --continue`；想放弃：`git rebase --abort`。绝不手动用文件夹覆盖另一边。
3. **公司机 origin 连不上属正常现象**——脚本会自动跳过并标注，不要在公司机折腾 GitHub。

## 三、公司机首次初始化（一次性，2026-08-15 执行）

```bash
# 1. 插硬盘后（假设盘符 E:），在中转位置建 bare 仓
git init --bare E:/git-sync/emotion_map.git

# 2. 在项目仓库目录配置 remote 并推送（工作分支 + main 都推）
git remote add syncdisk E:/git-sync/emotion_map.git
git push syncdisk --all
```

回家后首次：

```bash
git remote add syncdisk F:/git-sync/emotion_map.git   # 按家机实际盘符
git fetch syncdisk
git pull --rebase syncdisk <分支>
git push origin --all
```

> 首次初始化后，全部日常操作交给两个 bat 双击即可，无需手敲命令。

## 四、工具说明

### sync-leave.bat / sync-arrive.bat（双击兜底层，不依赖任何 AI 工具）

- `sync-leave.bat` → `python tools/sync_guard.py --mode leave`：提交全部变更 → 推硬盘 → 推 GitHub（可达时）
- `sync-arrive.bat` → `python tools/sync_guard.py --mode arrive`：从硬盘拉取 + rebase 当前分支
- 硬盘盘符漂移（公司 E: / 家 F: 轮换插）时自动扫描 `git-sync/emotion_map.git` 并自动 `remote set-url` 修复

### SessionStart hook（AI 伴侣提醒层）

`.claude/settings.json` 的 SessionStart 含 `sync_guard.py --mode status`：每次 Claude Code 会话启动自动注入同步状态（未提交数 / 硬盘在否 / 待推数），Claude 开场即提醒。配置随仓库走，公司机拉取后同样生效。

### sync_guard.py 手动用法

```bash
python tools/sync_guard.py                # 状态检查（纯本地、即时）
python tools/sync_guard.py --mode leave   # 离开前推
python tools/sync_guard.py --mode arrive  # 到岗后拉
```

## 五、故障排查

| 症状 | 处理 |
|------|------|
| `[ERR] 硬盘未插入或中转仓不存在` | 插硬盘；公司首次需先做第三节初始化 |
| `pull --rebase 失败（可能冲突）` | 按铁律 2 解决冲突后 `git rebase --continue` |
| `[WARN] origin 不可达` | 公司机正常现象；家机则检查网络/代理后重跑 |
| 想确认硬盘里有什么 | `git ls-remote syncdisk` |
