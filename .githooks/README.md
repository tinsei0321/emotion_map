# .githooks — 共享 Git 钩子

闭环补强 Wave2：把"提交前跑测试"从自觉变成强制。

## 启用（每台机器一次性）

```bash
git config core.hooksPath .githooks
```

启用后，每次 `git commit` 会先跑 `.githooks/pre-commit`（pytest 快速子集，失败阻断）。

## 临时跳过

```bash
git commit --no-verify   # 紧急修复时
```

## 关闭

```bash
git config --unset core.hooksPath
```

## 为什么不用 python `pre-commit` 框架

- 免新依赖（不装 `pre-commit` 包）
- 离线可用（GitHub 直连受限环境下重要）
- 随 Git 仓库共享（`.githooks/` 入库，团队/换机一致）
- 与 `/verify` slash command 互补：`/verify` 是柔和的提交前自查（含合规扫描/trace/PII），本钩子是硬闸（pytest 必过）
