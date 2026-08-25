# dsh 环境配方（PT-CB16 S1）

> 只入库模板/清单/脚本，不生成本机运行时。占位符：`{REPO}`（EMC 仓库根）、`{DSH_HOME}`（当前用户 `~/.dsh`）。禁止硬编码绝对路径与用户名。

## 内容

| 文件 | 用途 |
|---|---|
| `manifest.yml` | 双机环境版本清单（M2） |
| `profiles/emc-analysis/settings.yaml.template` | emc-analysis profile 设置模板 |
| `profiles/emc-analysis/cordis.patch.yml.template` | emc-analysis 插件/设置补丁模板 |
| `agent-presets/emc-analyst/preset.yml.template` | EMC Analyst 人设 preset 模板 |
| `scripts/start-emc.ps1.template` | 启动脚本模板（8600/8000/8080） |
| `check.ps1` | 到岗体检脚本（M3） |

## 到岗顺序

1. `git pull origin EMC_Codex_Harness`；
2. 按 `manifest.yml` 安装/核对版本；
3. 把 `profiles/`、`agent-presets/` 模板复制到 `{DSH_HOME}` 并替换占位符；
4. 跑 `docs/dsh-environment/check.ps1`，全部 `[OK]`；
5. 按需 `rebuild_rag.bat` 重建 RAG 索引。
