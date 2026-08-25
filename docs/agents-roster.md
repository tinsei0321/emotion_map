# Agent 花名册与编排参考库（自根 AGENTS.md 移出 · PT-CB18 W1-2）

> 移出说明：本文件承接根手册瘦身后移出的「角色卡 + 编排流程」参考内容。
> 概念框架声明仍留根：9 个 Agent 定义 = 角色卡片，非独立执行单元；实际任务由主线程直接执行
> （用户全局「不派 subagent」铁律），SOP 分级指导执行深度而非触发独立 Agent。

## 核心理念

**主线程 = PM**。无需手动 `@agent` 切换：给一个任务，主线程内部按 SOP 编排
开发→审查→测试→文档全流程，用户只看最终结果。

## Agent 清单（9 个）

| Agent | 文件 | 职责 | 可调用 |
|-------|------|------|--------|
| Developer | `.claude/agents/developer.agent.md` | 编写代码 + 诊断修复 bug + 决策追踪埋点 | gis-developer |
| Reviewer | `.claude/agents/reviewer.agent.md` | 审查代码质量、架构合规、追踪点完整性 | — |
| Tester | `.claude/agents/tester.agent.md` | 运行测试、验证功能、CRS 交叉核实 | gis-developer |
| Data | `.claude/agents/data.agent.md` | L0 多源数据采集 + L1 数据治理 | developer, gis-developer |
| Designer | `.claude/agents/designer.agent.md` | UI 视觉设计 + 交互优化 + 设计自审 | — |
| GIS Dev | `.claude/agents/gis-developer.agent.md` | 地理空间数据处理、坐标系转换、空间分析 | — |
| Docs | `.claude/agents/docs.agent.md` | 维护文档体系、更新开发日志、记录 ADR | — |
| Ops | `.claude/agents/ops.agent.md` | 环境诊断、依赖同步、requirements.txt 维护 | — |
| Sim | `.claude/agents/sim-emotion-data.agent.md` | 演示数据模拟（百度热力点为底座，从演示目的逆推生成 L0~L4） | — |

### 历史沿革（v1.0 → v2.0）

- Debugger 并入 Developer（开发 + 诊断双能力）；
- Design Reviewer 并入 Designer（交付前自审清单把关）；
- PM 不再独立：主线程承担编排，`pm.agent.md` 保留作行为指南；
- 手动 `@agent` 切换 → 自动编排。

## 自动编排流程

```
你说: "实现 XX 功能"
        ↓
自动:  ① 拆解任务（PM 视角）
       ② 按需启用 Developer/Designer/Data/GIS 角色
       ③ 审查（Reviewer 职责）
       ④ 验证（Tester 职责）
       ⑤ 汇总结果汇报
```

### 三管线自动路由

| 任务类型 | 自动执行流程 |
|----------|-------------|
| **纯逻辑** | 拆解 → 编码 → 审查 → 测试 → 文档同步 |
| **纯 UI** | 拆解 → 设计+自审 → 汇报 |
| **逻辑+UI** | 拆解 → 设计稿 → 按稿编码 → 审查 → 测试 → 复审还原度 |

### MCP 能力外挂（完整路由见 `docs/mcp-strategy.md`）

| Agent / 场景 | 首选 MCP | 备注 |
|--------------|----------|------|
| Developer / GIS — 理解开源依赖、读第三方仓库 | `zread` | 未收录的仓退 github MCP / 直接 clone |
| Developer — 查最新 API 用法、库变更 | `web-search-prime` | |
| Developer — 读某个文档/网页 URL | `web-reader` | 勿用下划线重复项 `web_reader` |
| Designer / Reviewer — 看设计稿、报错截图、UI 比对 | `zai-mcp-server` | 智谱主；不通退 `vision-bridge`（火山引擎） |
| Tester — 前端 E2E、异步/数据流隐患验证 | `playwright` | 按验证节奏，非常规改动不滥用 |
| Docs / Ops — GitHub Issue/PR 操作 | `github` MCP | 当前 PAT 失效，修复前用 `gh` CLI |

> 选型铁律：同类功能优先智谱（`zai`/`web-search-prime`/`web-reader`/`zread`），连不上再退备选。
