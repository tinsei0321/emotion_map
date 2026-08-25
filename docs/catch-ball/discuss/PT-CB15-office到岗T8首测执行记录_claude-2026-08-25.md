# PT-CB15 · office 到岗 + T8 首测执行记录（claude·2026-08-25）

> 依据：`docs/catch-ball/_handoff/OFFICE.md`（到岗清单）。分支 `EMC_Codex_Harness`。git 由主手代提交。

## 一 到岗四步

| 步骤 | 结果 |
|---|---|
| 1. git fetch + switch + fsck | ✅ 已在 `EMC_Codex_Harness`（旧分支已删）·fsck 仅 dangling 正常态·工作区干净（HEAD=2742f733） |
| 2. 环境补装 | ✅ codex-cli **0.149.1**（npm i -g @openai/codex@0.149.1）·桥实测解析到 APPDATA npm vendor（非商店版）·模型配置环境变量默认即用 |
| 3. 基线 | ✅ **597 passed + 2 skipped**（与 PT-CB15 DoD 597/2 一致·零退化） |
| 4. T1-T8 实测 | T8=?engine=codex 首测完成（见 §三）·T1-T7 用户浏览器侧 |

## 二 服务栈重建（office 机缺三件）

1. **后端 8000 跑旧分支旧代码**（750a41b8·EMC_harness_dsh·无 codex_bridge）→ 重启到当前分支（serve.py 自起 uvicorn·`py frontend/serve.py 8080` 标准栈）。
2. **8600 EMC MCP 未起** → `py tools/mcp_server_emc.py --http`（streamable-http·18 工具·握手 200）——**cdh 的 app-server 启动强依赖它**（config.toml `[mcp_servers.emc]` required=true·thread/start 时握手·失败则整个 thread 创建失败）。
3. 3080 dsh web 未起（cdh 时代不再需要·未起）。

## 三 T8 首测（?engine=codex）

**壳体验全通**：绿色「引擎·codex」徽标 ✓ · 推理占位符 ✓ · 逐字流式 ✓ · 回答渲染 + 追问卡片 ✓。

**内容链两次失败→一次全通**：

| 尝试 | 模型 | 结果 |
|---|---|---|
| ① | deepseek-v4-flash（我 08-25 上午误改） | 不调 emc 工具（仅 list_mcp_resources）·commandExecution 被 sandbox read-only 拒·回答「环境故障」·**链断** |
| ② | deepseek-chat（回滚·+AGENTS.md 引导） | **list_data→zonal_stats→rag_query→kb_facts→render_spec×2→hotspot_analysis·955 delta·68s·全链通** ✓ |

**根因链**（三环）：
1. **缺 8600 MCP** → app-server thread/start 失败（required emc 握手失败）——已修（§二-2）。
2. **缺 EMC 人设引导**（PT-CB15 C2 转正批未落地·`D:\Github\_codex_cwd` 空）→ 模型不知道 emc 工具是干什么的——**补写 `_codex_cwd/AGENTS.md`**（身份+先 list_data+唯一工具面=emc MCP+禁 webSearch+必出图·仓外不入库·换机复制清单登记）。
3. **模型档位**：deepseek-chat = **v4-flash 兼容别名**（官方文档：映射 v4-flash 非思考模式·flash 档价格）——用户令「cdh 恒 flash」与桥现状（deepseek-chat）**天然一致·无需改动**；全名 deepseek-v4-flash 实测断链（别名通·保持别名）。

## 四 模型档位定稿（用户问「chat 是 flash 还是 pro 价格」）

- **deepseek-chat = Flash 档**（官方 alias→v4-flash·flash 价格：高峰输入 3 元/输出 9 元每百万·闲时减半；pro 高峰 9/27 元）。
- 桥保持 `CODEX_MODEL=deepseek-chat`（=Flash·符合用户令）·环境变量逃生门保留。
- 桌面版 `[model_providers.deepseek] models = ["deepseek-v4-pro","deepseek-v4-flash"]`（08-25 加·已备份 config.toml.bak-20260825）——Pro/Flash 可切换。

## 五 冲突问题结论（桌面客户端 vs cdh 共存）

1. **命令解析隔离**：桥 `_resolve_codex_exe` 命中 npm CLI（APPDATA vendor）·不碰商店版。
2. **配置隔离**：桥 `-c model_provider/model` 进程级覆盖·不读写桌面顶层 config.toml。
3. **运行隔离**：cwd 仓外 `_codex_cwd`·sandbox read-only·approvalPolicy never。
4. **共享面**：~/.codex/auth.json 登录态（特性·EMC 复用登录）。
5. **唯一注意**：npm CLI 不能卸载/重装到别处（桥依赖其 vendor 路径探测）。

## 六 遗留与移交

- T1-T7 用户浏览器实测（可给指引：8080 页面 light/dsh/codex 三引擎各问 1-2 题）。
- `_codex_cwd/AGENTS.md`（仓外）登记换机复制清单（docs/codex-harness-ops.md 建议同步）。
- webSearch 工具在 app-server 下 ok=false（冒烟观察·不阻塞·引导已禁用它）。
- 主手回收：git 提交（含 codex_bridge 默认值注释更新）。
