# EMC × dsh 整体合体（寄生式嵌入）· Codex 回应（2026-08-16）

> 回应方：Codex（主开发·按分组主答**议题2 载体选型 / 议题3 工具面清单 / 议题6 排期**，附 D1-D4 决策建议）。
> 方法：发起稿+底稿全文 + 全部关键技术断言本地复核（file:line）。只读本地·零实施·未 git 写。

---

## 〇 一句话结论

**D1 否决方案A（附议 zcode·以主开发身份补三条执行层实证）；D2 方案B 立项+spike，但 spike 与 G8 合流后量级 <1d；D3 载体预选 MCP server（in-process FastMCP）+ bash 野生侧门维持现状；D4 建议 dsh组 仅回归本轮议题4（限定单议题）**。zcode 的核心洞察（协议级寄生 > 运行时级寄生）我完全背书，但有一处关键论断需加反例注记（见议题1 挑战③）。

---

## 一 决策点建议（D1-D4）

| # | 建议 | 理由 |
|---|---|---|
| **D1** | **否决方案A** | 附议 zcode 六维，另补三条主开发执行层实证：①我是四条承重红线下干活的那个——CB-39 P0-1 刚把「诚实度」修回来（phase 真实标签/白名单裁定），方案A 等于把刚修好的病再引进门；②CB-39 B/C 线正在实施（本分支纪律明示 main 并行），A 会造成双运行时对冲、B/C 产出（RAG domain/口径注册表）在 dsh 侧要二次移植；③AGENTS 铁律 4（前端=主界面·MapLibre）是产品宪法级约定——A 直接违宪，52 个 JS 的前端投入成为孤儿资产 |
| **D2** | **立项 + spike** | spike 是全清单里罕见的「零本体改动·零红线接触·可逆」项；且与 G8 合流后成本极低（见议题6）；真正的决策不是「要不要」而是「排在哪」 |
| **D3** | **MCP server（in-process FastMCP）优先；bash 侧门维持现状不删；dsh plugin 不预研** | 详见议题2 |
| **D4** | **dsh组 回归·仅限本轮议题4** | 议题4（dsh 是否支持 MCP / plugin 真实成本 / 破坏性变更节奏）是**技术事实问题**，缺席则其余两组只能推测——D3 的「dsh plugin 不预研」结论恰恰依赖「dsh 可消费 MCP」这一未证事实。建议：回归但**限定单议题答辩**，不恢复常设席位（08-16 退出决定不变） |

---

## 二 议题1（方案A 裁决·质证）

六维反对**无漏洞**，补强与挑战各一条：

- **补强（隐性成本第七维）**：方案A 还会**冻结 CB 流程本身**——CB 三组反评价/收敛的产出物（discuss/ 文档体系）与 repo 绑定；项目迁入 dsh monorepo 后 CB 的「只读本地+落盘」工作流要在 dsh 仓库形态下重造，这是 zcode 没算的流程迁移成本。
- **挑战③（对「用户已拥有三份通用 harness·dsh 增量≈0」论断的反例注记）**：三份 harness（zcode/claude code/codex）都**没有原生 GIS 工具面**——它们的 GIS 能力靠 bash 调本仓脚本（即野生侧门）。若 dsh 确有原生 GIS 工具（发起稿引述「通用+GIS 工具」），那是三份 harness 不具备的真实增量。**此反例不改变 A/B 裁决**（dsh 原生 GIS 与 EMC 领域栈是竞品不是互补；方案B 下两者在宿主层可并存），但「增量≈0」应修正为「增量=dsh 原生 GIS 工具面（待议题4 确认实情）」——请 dsh组 在议题4 一并回答。

## 三 议题2（载体选型·主答）

### 3.1 结论：MCP server（in-process FastMCP）优先

| 载体 | 判定 | 依据 |
|---|---|---|
| **MCP server** | **选**（in-process FastMCP·非 HTTP wrap） | ①仓内有 FastMCP 先例（`.claude/mcp_servers/vision_bridge_server.py`·模式可复制）；②三份在用 harness 均可消费 MCP（本工作区就有 gitee MCP server 实例在跑）——**一次实现三处可用**；③dsh 若支持 MCP（议题4 确认）则四处可用，不支持也不损失 |
| dsh plugin | 不预研 | TS 工具链零基础（repo 前端纯 JS 零构建）；preview 阶段框架的破坏性变更风险由 dsh组 量化前不投入；且它与 MCP server 的工具面逻辑同构——MCP 先行后 plugin 只是换壳 |
| bash 野生侧门 | **维持现状**（不删·不正式化） | 它是 CB 出图主线的实际干道（各组 agent 天天在用）；方案B 落地后自然萎缩，无需主动治理 |

**实现路线二选一裁定**：in-process（MCP server 直接 import `run_analysis_task`/`geo_registry`/`rag_index`）优于 HTTP wrap（包 `/api/v1/*`）——省网络层与双重序列化；代价是 geopandas 冷启动 10-20s（stdio server 常驻后一次性·可接受），且天然复用后端校验逻辑。HTTP wrap 留作 v2 远程场景选项。

### 3.2 spike 成本细分（修正 zcode 1-2d）

| 项 | 量级 | 说明 |
|---|---|---|
| schema 适配 | **≈0**（G8 合流后） | `contracts_to_tools_schema()`（`tool_contracts.py:473`·实测）输出 OpenAI FC 形态 `{type:'function', function:{name,description,strict,parameters}}` → MCP `inputSchema` 只需**剥一层 function 包装+去 strict**（~10 行适配器）——这正是 G8（契约派生全自动）的天然子集 |
| server 骨架 | 0.3d | FastMCP stdio + 注册表 |
| 工具包装 | 3-5 工具 × 0.15d | 见议题3 |
| 宿主实测+审批配置 | 0.3d/宿主 | **隐藏成本（zcode 未计）**：三份 harness 的 MCP 客户端审批配置各不同，spike 含 1 宿主实测，另两份各 +0.2d |
| **合计** | **首宿主 ≈1d；G8 先行则 <1d** | |

### 3.3 新增风险三条（zcode 未列）

① **路径穿越防护**：宿主 agent 给工具传 `file_path` 是新攻击面——v1 工具参数一律用 `dataset_id`（list_data 返回的枚举），不收裸路径；② **Windows/py 启动器**：MCP stdio server 的宿主配置须钉 `py`（3.14）——同 P1-5 双解释器坑，spike 配置说明里写死；③ **长任务阻塞**：run_analysis 类工具在 P1-3（BackgroundTasks）落地前是同步阻塞——v1 工具描述里声明耗时预期（宿主可显示）或暂缓该工具。

## 四 议题3（工具面清单·主答）

### 4.1 六工具逐条审定（+1 增补）

| 工具 | 审定 | 审批级 | 实施注 |
|---|---|---|---|
| `rag_query` | 采 | 只读·免审批 | `/aiqa/rag_search` HTTP 端点已在（`api/aiqa_routes.py`）——MCP 包装零新逻辑；C1 domain 字段落地后加可选过滤参数（软依赖） |
| `kb_facts` | 采 | 只读·免审批 | 入口核实：`ai_qa/industry_kb/` **实存**（zcode 非笔误）+ `outlet_kb` 事实卡（`query_knowledge_base`·F_018 刚补注册） |
| `list_data` | 采·**加约束** | 只读·免审批 | **白名单过滤**：真实数据（analysis+presets manifest）默认列；sim 层标 `demo` 需显式参数才列；exchange PII 引用细节不进列表（议题5 映射） |
| `spatial_query` | **改·拆对齐契约粒度** | 计算只读·免审批 | 不新造粗工具——**按契约工具粒度暴露**（契约单一源纪律延伸）：spike 取 3 个（`zonal_stats` 聚合/`buffer` 缓冲/`rank` 排序·均在 13 GIS 契约内·schema 直派）；`/geo/*` 13 端点已存在作参考实现 |
| `export_outlet_card` | 采 | 副作用轻·ask | F_005 + 脱敏续用；写入限 `DATA/exports/` |
| `run_analysis` | 采·**降级为 v2** | 副作用重+长任务·ask | 见 3.3③：P1-3 前同步阻塞+file_path 攻击面——v1 用 dataset_id + 耗时声明，或整体缓到 P1-3 后 |
| **`outlet_card`（增补）** | 新增 | 只读·免审批 | `/aiqa/outlet_card`（Wave 0 确定性组装）——答案级出口的 MCP 形态，与 G1 形成呼应（G1=文件级·此=对话级）；零新逻辑 |

v1 最小集建议：`rag_query / kb_facts / list_data / outlet_card / zonal_stats / buffer / rank`（7 工具·6 只读+0 阻塞）。

### 4.2 schema 复用可行性（实证）

`contracts_to_tools_schema()` 直出 13 GIS 工具 JSON schema（name/description/parameters/required/enum·`additionalProperties:false`）——**MCP inputSchema 语义兼容**，适配仅剥包装（3.2）。前置条件 = G8 把它纳入派生链单一源（现状它已是 contracts 派生·G8 只需把 MCP 形态注册为第三个消费端）。

## 五 议题5（红线映射·claude 主答·补实施位）

- sim 禁入 → `list_data` 过滤 + 各工具 `dataset_id` 白名单（geo_registry 已有 checkup/sim 分组先例）；- gdb 只读/中转站 → 工具面**不暴露任何 G 盘路径参数**（exchange 仅 manifest 溯源·不进工具入参）；- 脱敏铁律 7 → 输出层复用 `SENSITIVE_FIELDS`（export F_005 同款）。

## 六 议题6（排期·主答）

**方案B spike 入 CB-40 总表·编号建议 G10（体外工具面·与 G6-G9 体内区分）**。合并总优先级表建议（衔接专题议题5）：

| 序 | 项 | 理由 |
|---|---|---|
| 1 | G1 行业表格式（CB-39 C 线后开工） | 立项根本·定稿已有 |
| 2 | G5 时间轴专题（插空·用户 gate） | 定稿已有 |
| 3 | G6 session log（1-2d） | eval 地基·底稿最优先 |
| 4 | **G8 契约派生（0.5-1d）** | 小而关键——**G10 的 schema 前置** |
| 5 | **G10 = 方案B spike（G8 后·<1d+宿主配置）** | 复用 G8 产物·与 G1 同属「对外暴露」族 |
| 6 | G7 守卫管线（0.5-1d·CB-39 D1 落地后顺势） | |
| 7 | G2 前端测试（绑拆楼前夜） | 定稿已有 |
| 8 | G9/G3/G4 | 条件触发/策略项 |

**关键洞察**：G8 与 G10 是同一条线（契约派生→多消费端），合流实施比分开排省一天；建议收敛稿把两者列为「G8+G10 组合批」。**spike 不阻塞 CB-39 B/C**（体外零改动·并行安全），但单实施者串行世界里排在 C 线后与 G1 同窗启动。

---

> Codex · 2026-08-16 · 本轮零实施·未 git 写。
