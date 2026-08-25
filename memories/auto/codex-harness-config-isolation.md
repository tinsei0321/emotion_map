---
name: codex-harness-config-isolation
description: "EMC Codex Harness 与桌面 Codex 工具配置彻底隔离——harness 自备 CODEX_HOME(_codex_cwd/.codex·桥自愈生成)，桌面 ~/.codex/config.toml 禁放 [mcp_servers.emc]"
metadata: 
  node_type: memory
  type: project
  originSessionId: 960e706a-817c-40ff-9ba3-f70a150cde4a
  modified: 2026-08-25T22:27:32.133Z
---

2026-08-26 第二次复发后根治（配置隔离）：

- **根因**：EMC harness 与桌面 Codex 工具曾共用 `~/.codex/config.toml`——PT-CB15 把 `[mcp_servers.emc] required=true` 写进共享配置；桌面应用升级/model 切换持续改写该文件，手工修复被冲掉 → 冲突反复。
- **隔离架构**（core/codex_bridge.py `_ensure_harness_home`·F_045）：桥 spawn 时注入 `CODEX_HOME={REPO}/../_codex_cwd/.codex`，每次自愈生成 harness 专属 config.toml（**锁定 deepseek-v4-flash 全局不可切换**·用户令 2026-08-26 + emc required 迁入）+ models.json（复制桌面版并强制 deepseek 系 supports_search_tool=false 防 Deferred 工具陷阱）+ auth.json（缺则复制）；密钥运行时从桌面配置复制不进仓。P2-4 的 CODEX_MODEL_* 环境变量切换已退役。
- **桌面侧**：`~/.codex/config.toml` 摘除 [mcp_servers.emc]（备份 bak-20260826）——桌面工具回归纯编程工具，8600 起不起都不影响；模型 flash/pro 可切换由桌面配置自控。
- **实测**：`codex app-server --stdio` 的 initialize 响应 `codexHome` 返回注入值、sqlite 全建在 CODEX_HOME 下 → 环境变量 100% 生效。
- **git 附带**：本机 fetch 报 geometric repack 失败（HEAD reflog 有 10+ 无效条目·疑似同步残留）——已 `git config maintenance.auto false`（仓库级）绕开；根治需 `git reflog expire --expire=now --all` + `git gc`（用户暂未批准）。

**How to apply:** 改 codex 相关配置时先分清归属——harness 侧一切归 `_codex_cwd/.codex`（桥自愈·勿手改），桌面侧只碰 `~/.codex`（禁放 emc）；双机复刻 = 装 codex CLI + 桌面配置有 [model_providers.deepseek] 或 DEEPSEEK_API_KEY。关联 [[codex-cb-member-vs-cdh-brain]] [[dual-machine-disk-sync]]。
