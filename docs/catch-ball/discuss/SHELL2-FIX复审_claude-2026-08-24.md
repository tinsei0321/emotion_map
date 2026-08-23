# SHELL2(FIX) 复审 · claude（正确性/测试/集成视角·2026-08-24）

> 复审对象：Qoder 修复批 `a170a0e`（12 件·574+2 绿·rag_eval 96.7% 零退化）。对照 = 我的原审计（`壳工程深度审计_claude-2026-08-23.md`）+ Qoder 原审计 + FIX 派发单。
> **总裁决（先行）**：**通过**——12 件全修到位；我提的七件独有发现 6 件 ✓ 根修·1 件（X-1 provenance 渲染分支）按我原裁决本就挂账「随 BA 二轮」·非漏修；新测试测行为不测存在性；4 条 P3 新发现挂账不阻塞。零实施零 git 写（本报告除外）。

## 一 白话摘要段

Qoder 把我上次体检发现的问题全修了一遍，我逐条"复诊"：**大洞（P1）修到了根上**——超长问句现在会在门口被拦下（4000 字上限）而不是把后端打崩，后端也加了兜底网（拦漏了也不 500）；**七件我独有的发现六件修到位**——报错原因现在能走到用户眼前（白名单文案·不裸输）、追问按钮的逻辑抽出来单独测了 13 个断言、主路引擎的事件格式也进了质检；**一件属于"挂账"不是"漏修"**（诚实性标记的界面样式·当时就定了随下一轮做）。顺手发现 4 个**小瑕疵**（如报错卡片里两句话自相矛盾），都不拦路、下一轮顺手修。**结论：这批修复过关。**

## 二 逐件核验表

### 七件独有发现（本组提）

| 原发现 | 修复件 | 核验 | 证据（file:line） | 残余风险 |
|---|---|---|---|---|
| C3-1 P1 超长 500 | FIX-02 | ✓ **根修** | `question: Field(max_length=4000)` [aiqa_routes.py:88](api/aiqa_routes.py#L88)（pydantic 422 门口拦）+ `except OSError` [aiqa_routes.py:140](api/aiqa_routes.py#L140)（拦漏兜底）；边界测试 4000 收/4001 拒 [test_dsh_engine.py:88](tests/test_dsh_engine.py#L88)、OSError 206 语义化 [test_dsh_engine.py:93](tests/test_dsh_engine.py#L93) | 无 |
| C1-1 P2 caliber 契约 | FIX-12 | ✓ **认可处置** | 契约降「必带」→「有则带」+ 理由（发射侧无口径源不硬造）[acp-contract-v1.md:56](docs/acp-contract-v1.md#L56)·设计理由段同步改。**这正是我原审计开的选项 B**（「契约降级为有则带·S2 增补时定稿」） | 无（「带则统一结构」约束仍在·未开自由口） |
| X-2 P2 hint 三层断链 | FIX-10 | ✓ **通两层半** | ①panel 白名单原因行（按 wire.code 映射·未知码归通用·原始 hint 只存 trace）[panel.js:1636-1642](frontend/js/ai_qa/panel.js#L1636-L1642) ②S4 wire 补 hint [acp-channel.js:140-141](frontend/js/ai_qa/acp-channel.js#L140-L141) ③bus hint 原有 | **BA 侧 error wire 仍无 hint**（DSH_ENGINE_FAIL 的 wire 只 code/message）——远端消费 BA 错误仍拿不到原因。P3 挂账（见 N2） |
| X-1 P2 provenance 孤儿 | —（未列本批） | ✗ **未修·挂账合规** | panel 渲染仍无 provenance 分支（msg.delta 直接进思考流） | 我原总裁决即「并入排期·随 BA 二轮」——非漏修·复审确认挂账在案 |
| C4-1 P2 dsh 兜底追问 | FIX-11 | ✓ | `_followUps` 补 `intent==='dsh'` 分支：深问（概念展开）/求据（依据出处）/本地分析（逃生口）[panel.js:724-730](frontend/js/ai_qa/panel.js#L724-L730)；Part C 真 dsh 轮实证无情绪问法混入 [test_followup_chips.py:116-118](tests/browser/test_followup_chips.py#L116-L118) | 无（内容搭调·知识类文案） |
| C5-1 P2 S4 wire 校验 | FIX-08 | ✓ | s4_wire_dump 16 次调用覆盖**全 14 方法**（diagnose/round×3/thought/action×2/observation×2/reason/final/resultStruct/finalDone/askUser/outletCard/defense/degraded）[s4_wire_dump.mjs:14-28](tests/acp_schema/s4_wire_dump.mjs#L14-L28)；三断言=真实 jsonschema+thought 豁免（我 C1-4 的测试侧坑已显式处理）+real provenance+分层/六族/配对/seq 单调 [test_s4_wire.py:55-91](tests/acp_schema/test_s4_wire.py#L55-L91) | 无 |
| C5-2 P2 chips 三态测试 | FIX-09 | ✓ **三态全测** | 13 断言：空/非数组/脏数据（null+空串+非串 String 化+trim）**截 3**/ask 互斥（带 cues 也互斥）/优先级三档（cues>胶囊·胶囊·static）**全脏 cues→落 static 不悬空** [followup_chips_dump.mjs](tests/browser/followup_chips_dump.mjs)；Part B 浏览器层优先级实证（标签=追问建议 证明 cues 压过静态）[test_followup_chips.py:70-75](tests/browser/test_followup_chips.py#L70-L75) | 无 |

### 其余五件（Qoder 侧发现·本组顺验）

| 修复件 | 核验 | 证据 | 残余 |
|---|---|---|---|
| FIX-01 并发/线程池 | ✓ | async def + `asyncio.to_thread`（不占共享线程池）+ `Semaphore(2)` [aiqa_routes.py:96-98,169-172](api/aiqa_routes.py#L96-L98)；**真并发实证**（0.25s 重叠窗口·4 并发→峰值 ≤2·非假并发）[test_dsh_engine.py:141-160](tests/test_dsh_engine.py#L141-L160)；track_async 加法基建·既有 track() 零改动 [core/tracker.py:266](core/tracker.py#L266) | 无 |
| FIX-03 死路径 | ✓ | fallback-cmd 字符串拼装路径整段删除·bin.js 缺失→语义化拒绝·测试断言「fail-closed 分支不得触发 subprocess」[test_dsh_engine.py:67-75](tests/test_dsh_engine.py#L67-L75) | 无 |
| FIX-04 看门狗 | ✓ | 330s Promise.race（>代理 300s>后端 240s·分层合理）·finally 双清理无定时器泄漏 [brain-adapter-dsh.js:63-77](frontend/js/ai_qa/brain-adapter-dsh.js#L63-L77) | 超时胜出时底层 fetch 未 abort（后端继续跑完·响应被弃）——P3 可接受 |
| FIX-05 输出截断 | ✓ | 200KB 截断+truncated 标记 [aiqa_routes.py:147-150](api/aiqa_routes.py#L147-L150)·边界测试（200KB+999→恰 200KB） | **truncated 字段前端未消费**（用户不知道答案被截）——见 N4 |
| FIX-06 廉价判长 | ✓ | 类型分支先截（string slice/数组行长/对象键名列表）·免万行观察值全量 stringify [acp-channel.js:94-106](frontend/js/ai_qa/acp-channel.js#L94-L106) | 对象摘要语义由 JSON→键名列表·summary 性质可接受 |
| FIX-07 start.bat | ✓ | 8600 依赖注记 + 启动序（先 MCP 后 Web）·docs 级 | 无 |

## 三 新发现（修复过程引入/漏网·均 P3）

| # | 发现 | 证据 |
|---|---|---|
| N1 | **降级卡体文案自相矛盾**——原因行按 code 出「外部大脑（dsh 引擎）暂不可用」·卡体正文仍硬编码「模型输出未能解析为可执行动作，且最终结论生成失败」叙事·dsh 失败时两句互斥 | [panel.js:1639-1643](frontend/js/ai_qa/panel.js#L1639-L1643) `_degradedText` 固定文案未按 code 分型 |
| N2 | **BA error wire 无 hint**——X-2 三层只补了 S4 侧·BA（DSH_ENGINE_FAIL）wire 仍 code/message 两键·hint 仅 bus | [brain-adapter-dsh.js:84-86](frontend/js/ai_qa/brain-adapter-dsh.js#L84-L86) |
| N3 | **Part C 无 dsh 缺席守卫**——无 dsh 机器上必红（与 Part A node 缺席 skip 纪律不一致）·office 未装 dsh 时此测试直接 ERR | [test_followup_chips.py:99-118](tests/browser/test_followup_chips.py#L99-L118) |
| N4 | **truncated 标记前端未消费**——BA 透传 `String(resp.output)` 时丢 truncated·200KB 截断后用户无感 | [brain-adapter-dsh.js:91](frontend/js/ai_qa/brain-adapter-dsh.js#L91) |
| N5 | （记录备查·非问题）模块级 Semaphore 惰性绑当前 loop·py3.10+ 语义安全·uvicorn 单 loop 下无跨 loop 风险 | [aiqa_routes.py:96](api/aiqa_routes.py#L96) |

## 四 测试质量评估

**总体：测行为·非测存在性——优秀**。

- **断言=行为**：argv 逐元素比对（`cmd[-1] == '问句含 & | > " 特殊字符'` 证单一 argv 无元字符面）·边界值 4000/4001·「fail-closed 不得触发 subprocess」·真并发峰值 ≤2·seq 单调且唯一·toolcall 配对 set 相等·thought 子型显式豁免（我 C1-4 原坑被正确处理）。
- **分层合理**：后端 monkeypatch（零真 spawn·快且稳）→ node dump（零浏览器）→ playwright 真浏览器（mock/dsh 真轮）三层各司其职。
- **可移植性**：node 缺席 skip·栈未起 skip——唯独 N3（dsh 缺席）漏守卫。
- **实测复核**：本组重跑 `tests/test_dsh_engine.py + test_acp_schema/test_s4_wire.py + test_brain_adapter_wire.py` = **20 passed**（1.72s·与全量 574+2 申报一致）。

## 五 四档总裁决

**通过**。

- **通过理由**：P1 三件根修（max_length 门口拦 + OSError 兜底 + 死路径删除·皆带行为级测试）；七件独有发现 6 修 1 挂账（X-1 按原裁决随 BA 二轮·非漏修）；rag_eval 96.7% 零退化 + MCP 零改动 + 轻量引擎默认路径逐字同路（守 eval-anchor）。
- **挂账清单（不阻塞·随 BA 二轮顺手）**：N1 降级卡文案分型 / N2 BA wire 补 hint / N3 Part C dsh 缺席守卫 / N4 truncated 前端提示 / X-1 provenance 渲染分支（原挂账）。
- **回看**：本批修复证实了双组交叉审计的价值——我提的 C5-1/C5-2 缺口与 Qoder 提的架构问题被同一批、同一标准补测到位。

—— claude · 2026-08-24 · 家机 · 零实施
