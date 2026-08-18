# EMC × dsh 可行性深挖 · dsh组回应回收抽验（Codex·2026-08-18）

> **对象**：`EMC-dsh可行性深挖_回应_dsh组-2026-08-18.md`  
> **性质**：主线程回收抽验与增量裁定。零实施、零 git 写、不出实施计划。  
> **方法**：对 dsh checkout 与 EMC 侧代码逐项复核；不因结论方向相同而跳过事实核验。

---

## 〇 一句话结论

**dsh组本轮增量质量高，三项架构修正建议应吸收：① `caliber` 必须进工具 output；② `list_data` 必须开卷定参；③ `rag_query` 不能裸返 chunks。** 但其“当前克隆 0 个 `!:`/BREAKING 标记”的口径**与主线程实测相矛盾**（当前克隆全史可检出 16 个 `!:` 与 13 个 BREAKING 相关提交）；该错误不推翻“preview 节奏快、不宜深嵌”的结论，反而说明归档时必须同时保留“旧 600-commit 口径不可复现”和“当前全史仍有 16 个 `!:`”两层事实。

---

## 一 抽验结果

| # | dsh组断言 | 主线程抽验 | 处置 |
|---|---|---|---|
| 1 | 当前 checkout 为 `D:\Github\dsh` @ `f1e10a678e`，rc.7 | ✅ 属实 | 采纳为当前事实底座 |
| 2 | 旧 `D:\Github\dsh_test` checkout 已不存在 | ⚠️ **表述需修正**：目录仍存在，但已无 `.git`，只剩 plugins/cleanup 脚本等残留；旧 git checkout 确实不可用 | 归档措辞改为“旧 git checkout 已移除，目录残留清理文件” |
| 3 | 当前克隆 0 个 `!:`/BREAKING 标记 | ❌ **不属实**：`git log --grep='!:'` 全史 16 条；`-i --grep='BREAKING'` 13 条。16 条 `!:` 均在 2026-08-10 及以前；最早 `!:` 到 HEAD 约 6058 commits，非“近 600” | 采纳“旧 600-commit 计数不可复现”，拒绝“当前 0 标记”；preview 风险另用 release cadence 证明 |
| 4 | 6 天 10 个 rc | ✅ 基本属实：08-11 至 08-17 共 10 个 rc 版本；08-13 有 9 条 release 相关 log（8 条直接 release commit + 1 merge） | 采纳为供应链风险主证据 |
| 5 | ACP `session/new` 拒绝非空 `mcpServers` | ✅ 属实：`packages/acp/acp/src/index.ts:544` | 采纳：G10 须 profile 全局 MCP 配置 |
| 6 | headless 无 Host/HTTP/Web/browser/监听端口 | ✅ 属实：`packages/bundle/headless/README.md:5,7` | 采纳 |
| 7 | MCP 默认 `toolCallTimeoutMs=60000`；重连预算；tools-only；outputSchema 超词汇退化 | ✅ 属实：`packages/mcp/mcp-client/README.md:46,48-51,69-71,113,117` | 采纳为 G10 输出/超时设计约束 |
| 8 | 审批策略为 `ask|never`，`allowed-once` 是唯一 grant | ✅ 属实：`docs/subsystems/approval.md:28,46`；实现见 `packages/interaction/user-approval/src/types.ts:29` | 采纳；dsh组引 `index.d.ts` 的文件名需修正为 `src/types.ts` |
| 9 | dsh pre-execute 不能改写参数 | ✅ 属实：`docs/subsystems/tools.md:402` | 采纳：MCP server 必须补全默认值并前置校验 |
| 10 | EMC 七工具 backing 存在 | ✅ 属实：`api/aiqa_routes.py:31,92,112`；`core/spatial_analysis.py:237,403`；`core/buffer_analysis.py:18`；`ai_qa/tool_contracts.py:373,473,548` | 采纳 |
| 11 | `rag_query` 现有端点裸返 chunks，缺综合 | ✅ 方向属实：`post_rag_search` 返回 Top-K + `dim_counts`，LLM 综合在前端 finalStep 路径完成 | 采纳问题；但实现不能简单新造推理，应抽出/复用知识问答 finalStep 组装与提示词资产 |

---

## 二 应吸收的架构修正

### R1. `caliber` 进入每个工具 output（强吸收）

dsh组对 C11 的挑战成立：description 只能防参数误用，防不住宿主把宏观聚合说成微观诊断。EMC 的差异化不是“能算”，而是**口径可辩护**。

**修正建议**：

- 每个工具返回统一 `caliber` 对象：`{scale, semantics, limits, refs}`；
- `refs` 指向 paradigm / KB / 口径注册 ID；
- `rag_query`、`zonal_stats`、`rank`、`render_spec` 尤其必带；
- 该字段进入 C10 平台 eval，而不是仅靠 description lint。

### R2. `list_data` 开卷定参（强吸收，附安全修正）

只返回 `dataset_id` 会把 R4 的“闭卷填参”病灶搬到 MCP 面。应返回：

- dataset_id；
- 行数；
- 字段名与类型；
- CRS；
- 几何类型；
- 口径/用途；
- 可选枚举值或受控样例。

**Codex 安全追加**：样例不能直接输出原始 PII/敏感行。样例必须过 C1 脱敏，或仅返回字段类型、枚举、值域、空值率与受控 synthetic sample。`schema/CRS/几何类型` 可以默认给，`样例行` 必须分级。

### R3. `rag_query` 增加 synthesize 选项（强吸收，附实现约束）

dsh组判断成立：MCP 消费端拿到裸 chunks 后，宿主 LLM 的归纳是无引导的，CB-22 “三支柱”会在协议面退化。

**实现约束**：

- 不是让 MCP server 自由发明“聪明工具”；
- 应复用 EMC 既有知识问答 finalStep 的素材组装、来源约束、维度声明与降级逻辑；
- `synthesize=false` 可保留给调试/检索场景；
- 默认值是否为 true 需在 G10 设计中单独裁定（涉及延迟、key 依赖、宿主意图）；
- 输出必须带来源、维度、caliber 与 degraded 状态。

### R4. 渲染 v1 文本化 render_spec（吸收）

dsh Web 没有 EMC 的 JS 解析器；只给“语义令牌 + 解析副本”仍无法保证外部可渲染。render_spec 应尽早文本化为：

- GeoJSON / layer facts；
- style token JSON；
- 图例与拉伸说明；
- `resolved_by` 与口径标注。

同时保留 JS 渲染器权威，避免第二份语义解析逻辑。

### R5. 输出体积与 60s 超时（吸收）

G10 v1 必须内建：

- `top_n` / `cells` / `limit` 等体积控制；
- 摘要 + 可复查引用 ID；
- description 的 `limits` 中声明耗时量级；
- 超大任务不进 v1，留给 v2 `run_analysis`。

---

## 三 对 B 变体的裁定修正

dsh组认为“实验保留仍偏乐观”，主线程部分接受：

1. **接受**：B 变体不应占产品排期，不应专门维护；
2. **接受**：用户工作流用法本身就是观察窗口；
3. **接受**：若转正，必须使用专用瘦 profile，不能复用用户日常 profile；
4. **修正**：五条件不必全部等价对待。有效判据可压缩为：
   - A 变体已稳定；
   - 自由任务需求真实出现；
   - dsh 供应链可接受（脱 preview 或锁定版本可维护）；
   - 一次同任务对比验收通过。

**仍待用户一句话**：朋友成品是否存在。若存在，先评审；若不存在，仅做 ACP 50 行级 demo 设计，不进产品链路。

---

## 四 归档前必须修正的文档事实

1. “`dsh_test` 已不存在” → 改为“旧 git checkout 已不可用，目录残留非 git 清理文件”。
2. “当前克隆 0 个 `!:`/BREAKING” → 改为“当前全史 16 个 `!:`、13 个 BREAKING 相关提交；旧 `600 commit 内 16` 口径在当前历史不可复现，16 个 `!:` 跨约 6058 commits且最后出现在 08-10”。
3. `user-approval/index.d.ts:167` → 修正为 `packages/interaction/user-approval/src/types.ts:29`（`allowed-once` 唯一 grant；docs 佐证 `approval.md:21,28,46`）。
4. “08-13 单日 8 个 rc”建议写成“08-13 有 9 条 release 相关提交（8 direct + 1 merge）；08-11→08-17 六天 10 个 rc 版本”，避免口径歧义。

---

## 五 给用户的下一组决策键

1. **是否接受 dsh组三项 G10 修正**：caliber output / list_data 开卷 / rag synthesize。Codex 建议全收，但样例必须脱敏。
2. **是否接受 G10 转正判据**：同任务 MCP 相比 bash 轮次节省 ≥30%，且叙事纠偏率 ≤50%。Codex 建议作为 spike 验收线。
3. **B 变体是否降为零维护观察项**：Codex 建议是；不进产品排期，靠真实自由任务需求触发。
4. **朋友成品是否存在**：一句话分流评审 / ACP demo。
5. **是否接受专用瘦 profile 作为 B 变体转正硬条件**：Codex 建议是。

---

> Codex · 2026-08-18 · 只读抽验；未修改生产代码，未出实施计划。
