# PT-CB10 · 战略转向裁定：dsh 归官方 + MCP/RAG 优先（zcode 主手·2026-08-21）

> 用户裁定：①入口按钮等 dsh 侧定制件=临时测试件·不再投入；②重装 dsh 官方 origin 版·即刻执行；③工作重心转向 MCP 工具丰富度+RAG 架构+ACP/API 适配。主手评估：**全部正确·即刻执行**。

---

## 一 收口批重新裁切

| 原任务 | 新状态 | 理由 |
|---|---|---|
| A-1 C2-7+C5（guard 白名单+profile 维护） | **降级→仅保留 M1 配方快照** | 重装后 guard 插件不恢复（逻辑迁 server 侧）·profile 重建走配方 |
| A-2 C1b（会话归置+入口文本） | **取消** | 入口插件退役·文本修正无意义 |
| A-3 stdio 纯度 | **保留·升为最高优先** | 官方 dsh 可能更严格·必须先修再重装 |
| A-4 版本徽章 | **保留** | EMC 侧价值·与 dsh 版本无关 |
| A-5 审计 | **改 scope**：审 stdio 修复+版本徽章+重装后 MCP 全量验证 | |

## 二 重装 dsh 官方版·操作序列

```
第 1 步（30 分钟·重装前必须）
  A-3 stdio 纯度修复（Codex）——修完 pytest 全绿 + 严格 client 10 工具验证通过

第 2 步（15 分钟·快照当前配置供 M1 参考）
  导出当前 profile 配置（emc-analysis/cordis.patch.yml/settings.yaml/package.json）
  存入 docs/catch-ball/arch/m1-recipe-snapshot/（只读参考·不恢复）

第 3 步（30 分钟·清理重装）
  ①备份 ~/.dsh/ → ~/.dsh-backup-pre-official/
  ②卸载当前 dsh（npm uninstall -g @deepseek-ai/dsh 或等效）
  ③清理 D:/Github/dsh 中的本地修改（git checkout . 或 clone fresh）
  ④安装官方最新：npm install -g @deepseek-ai/dsh（或 git clone origin + pnpm build）
  ⑤验证 dsh --version = 官方版本号

第 4 步（15 分钟·最小配置重建）
  只做一件事：新建 profile（如 emc-test）→ cordis.patch.yml 注册 mcp-emc insert
  （照 M1 配方快照中的 mcp-emc 段照抄·其余全不恢复——无 guard/无 entry/无双模）

第 5 步（15 分钟·验证）
  dsh --profile emc-test "列出你可用的 mcp__emc__ 开头的工具"
  → 应返回 10 件（list_data/rag_query/kb_facts/outlet_card/zonal_stats/buffer/rank/render_spec/render_file/emc_status）
  → 问一个真实问题验证工具可调用：「12345 诉求最密集的 5 个社区是哪些？」
```

**重装后不恢复的件**（正式退役·沉没成本止损）：
- dsh-emc-entry 入口插件——退役（EMC 壳阶段有自己的入口）
- emc-analysis-guard 白名单插件——退役（逻辑迁 server 侧·后续作为 MCP server 内置守卫）
- emc-research profile——退役（研究走 web 档+/plan·已裁定）
- better-sidebar 第三方插件——不再依赖（monkey-patch 风险源消除）

**重装后保留的件**：
- EMC MCP server（tools/mcp_server_emc.py·十件插座——**这是唯一的正式接触面**）
- EMC 全部资产（数据/契约/渲染/RAG/口径体系）
- 8080 前端（渲染契约·EMC 自有）

## 三 新的工作优先级（替代原路线图 A+/B/C 编排）

### 第一优先：MCP 工具丰富化（新批 PT-CB11·替代原 A+ 批）

| 新工具 | 价值 | 来源 |
|---|---|---|
| **grid_aggregate** | 800m 方格聚合参数化（T8 脚本→工具·同类任务 1 调用） | dsh 建议④+R46 总纲 |
| **compare_regions** | 多区域对比（≥2 区并排+差异叙述） | contracts 已有 |
| **hotspot_analysis** | Gi* 显著聚集识别 | contracts 已有 |
| **nearest_analysis** | 最近邻锚定（POI 邻近） | contracts 已有 |
| **area_stats** | 面积占比统计 | contracts 已有 |
| **overlay_analysis** | 叠置交叉（面∩面） | contracts 已有 |
| **trend_analysis** | 时序对比（L2 T1/T2/T3） | 数据已有 |
| **report_assemble** | 综合报告组装（多工具结果→结构化报告） | outlet_card 扩展 |

**设计原则**：每件工具=①契约 schema 从 tool_contracts 派生 ②caliber 四键 ③体积纪律 ④服务端守卫（G-2 等）⑤五判据答辩。**guard 逻辑从 dsh 插件迁入 server 侧**（工具调用前服务端校验·不依赖宿主自觉）。

### 第二优先：RAG 重建（PT-CB9 原案·提前到与 MCP 并行）

- 原案 v1.1 不动（泳道①内容/②检索/③工程）
- **消费接口=rag_query 工具**（已有）——RAG 重建提升的是这个工具的返回质量
- B4 白名单差集检查器改为 server 侧自动校验（新工具注册时自动核对）

### 第三优先：ACP/API 适配（替代原 dsh B 变体完整版）

- **大脑端口契约 v1**（20 行级文档·只定义不实现）——Qoder R2 建议
- ACP 是机制 MCP 是门面——写进 copilot-architecture
- 实际 ACP 实施=EMC 壳阶段（当前只做契约定义）

### 保留不变

- 版本徽章（A-4·EMC 侧）
- 进度契约（_board.yaml 合并版）
- M1-M3 环境配方（重装后按新环境重做·配方模板不变）
- CB 六改（改1-改6）

## 四 与原路线图的差异表

| 原路线图 | 新路线图 | 理由 |
|---|---|---|
| A+ 体验契约批（选择机制/追问/受管默认值等·dsh 侧） | **MCP 工具丰富化批** | 体验件依赖 dsh 插件→已退役；工具件才是永久资产 |
| D1 讨论批中的 dsh 侧议题 | **缩小 scope**：只讨论工具契约与 server 侧守卫 | dsh 侧交互契约随插件退役失去载体 |
| 阶段 C M1-M3 环境配方 | **保留但简化**：只配方 mcp-emc 连接·不再配方 guard/entry | 接触面从 7 件缩到 1 件 |

---

> zcode 主手 · 2026-08-21 · 用户战略转向裁定·即刻执行
