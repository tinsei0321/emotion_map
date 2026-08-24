# PT-CB15 · Codex 真实用例验证 spike（Qoder·2026-08-24·并入三组回应修正）

> 依据：三组 CB 回应收敛后的关键修正。目的：**用最少步骤验证「Codex 在 EMC 壳里能不能做到流式+多轮+工具调用+出图」——用户想要的核心体验**。
> 执行=Qoder·commit 前缀 `PT-CB15(SPIKE):`。新分支 **`EMC_Codex_Harness`**（注意：不再是旧分支）。零 pull 零 push（显式路径 commit）。
> 产出含白话摘要段。

## 三组回应关键修正（吸收进本 spike）

| 来源 | 修正 | 本 spike 采纳 |
|---|---|---|
| claude | `codex exec --json` 无 token 增量·**必须走 app-server 协议**才有流式 | ✅ 本 spike 走 app-server |
| Qoder | 计划漏 C0（认证/安装前置·不先做第一天就卡） | ✅ 本 spike 第一步=C0 |
| Qoder | app-server 传输=stdio（`stdio://`默认）；MCP=HTTP 8600 常驻（D1 双轨） | ✅ |
| Qoder | 项目 AGENTS.md（写给 Claude Code 的 9-Agent 规范）会泄漏给 Codex——**cwd 不指向本仓**或用 profile 隔离 | ✅ spike 时 cwd=独立目录 |
| Kimi | render_spec 非写面·免审批 | ✅ |
| Qoder | Schema 锁：`codex app-server generate-json-schema --out` 产物存仓 | ✅ 随 spike 产出 |

## Spike 步骤（验证用户核心体验的四问）

### 第一问：Codex 能调 EMC 工具吗？（~1h·含 C0 安装认证）

1. **C0 安装+认证**：本机安装 Codex Harness（按三组回应推荐方式）→ 配 key/登录
2. **C1 MCP 注册**：config.toml 加 `[mcp_servers.emc]`——HTTP `http://127.0.0.1:8600/mcp`·`startup_timeout_sec≥60`·`tool_timeout_sec≥120`
3. **验证**：Codex 对话问「列出你可用的 mcp__emc__ 开头的工具」→ 应返回 18 件
4. **工具调用**：问「12345 诉求最密集的 5 个社区是哪些？」→ Codex 应调 rank/zonal_stats→返回结论

### 第二问：Codex 能流式输出吗？（~1h）

1. **app-server 连接**：Python subprocess 连 Codex app-server（stdio JSONL）——参考 codex-main 源码 `app-server-protocol` 段
2. **流式事件接收**：监听 `AgentMessageDeltaNotification`——确认逐 token 到达
3. **验证**：写一个最小 Python 脚本打印收到的 delta 时间戳——证明**流式不是一次性的**

### 第三问：流式能进 EMC 壳吗？（~2h）

1. **后端桥接端点**：仿 post_dsh_engine 建 `/aiqa/codex_engine`——subprocess 连 Codex app-server → JSONL 解析 → SSE 转发到前端
2. **前端适配**：brain-adapter-codex.js 仿 dsh 版——fetch→SSE 消费→ACP msg.delta 逐 token 发射
3. **引擎第五态**：`?engine=codex` 分发
4. **验证**：8080 打开 `?engine=codex` 问「什么是留改拆」→ **EMC 对话框应出现逐字打字**

### 第四问：完整链路通吗？（~1h）

1. **多轮对话**：第一问「西陵区情绪怎么样」→第二问「那伍家岗呢」（上下文延续）
2. **工具+出图**：问「西陵区情绪最差社区显示在地图上」→ 8080 地图亮层
3. **多轮+出图+流式三合一**：最终验证

## Spike 产出（DoD）

- [ ] 四问各有**实测截图/日志**（成功或失败都如实记录）
- [ ] 如果通了：白话摘要「EMC 壳里逐字打字+多轮+出图全部实现」+操作指引（用户怎么测）
- [ ] 如果不通：**卡在哪一步+根因+是否可修**——诚实告知
- [ ] Schema 锁产物入仓（`codex app-server generate-json-schema --out` → tests/fixtures/）
- [ ] 预判坑验证：Qoder 六坑清单中 P1-P5 哪些实际遇到
- [ ] 执行记录落盘（白话摘要段+每问验证数据）

## 红线

- EMC MCP 18 件工具零改动
- dsh/light 引擎零退化
- RAG 96.7% 零退化
- Codex 配置全部仓外（~/.codex/）·复刻清单入记录
- cwd 隔离（不指向本仓·防 AGENTS.md 冲突）

> zcode 主手 · 2026-08-24 · Codex 真实用例验证 spike 派发·Qoder 执行
