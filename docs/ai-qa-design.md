# 情绪地图 AI 问答子系统 · 设计圣经

> 版本：Harness v1（2026-07-07，四层 SOP + Review + 独立子架构 + 独立窗口化）
> 范围：AI 问答作为独立子系统的权威设计文档。未来做厚（多轮记忆 / Agent / 多模型协作 / 知识库 RAG）就扩本文。
> 关联：后端 `ai_qa/` + 前端 `frontend/js/ai_qa/` + `frontend/chat.html` + `frontend/js/ai_qa_host.js`。

---

## 第 1 章 · 子系统定位与边界

**为什么独立成子系统**：AI 问答未来会做厚，从散落于 `core/chat_context.py` + `frontend/js/chat-panel.js` 收拢为独立子系统，边界干净、未来好扩，不污染主体（map/state/panel 等基础设施）。

**目录结构**：

```
后端 ai_qa/（顶层，与 core/api 平级）
├── manifesto.py   知识层 · MANIFESTO 领域宪法（喂给模型，让它真懂情绪地图）
├── prompts.py     思考层 · build_think/answer/review_prompt（SOP 解题协议）
├── review.py      审查层 · REVIEW_CHECKLIST 六条 + 审查员模型配置
├── schemas.py     ChatRequest（phase: think|answer|review + draft/observation/review_feedback）
├── router.py      /chat 路由（think/answer SSE 流式；review 非流式 JSON）
├── llm.py         LLMClient（provider-agnostic，默认 DeepSeek）
└── __init__.py

前端 frontend/
├── chat.html                       独立小窗口页面（载 ai_qa.css + panel.js）
├── js/ai_qa_host.js                主窗口侧 · BroadcastChannel 监听执行器 + buildContext 推送
├── css/ai_qa.css                   样式（独立窗 + 浮窗降级 + 解题面板 + 审查区）
└── js/ai_qa/
    ├── protocol.js   协议层 · CHANNEL + 消息 type + request/notify/onPush/hello RPC
    ├── harness.js    管线 · STAGES 阶段注册表 + orchestrate + Review 闭环
    ├── stages.js     think/execute/answer/review 四阶段函数
    ├── tools.js      执行层 · TOOLS（ensure_zone/rank_zones/open_attribution/inspect_zone）
    ├── panel.js      UI · 解题面板5格 + 思考链 + 审查区（chat.html 与浮窗降级共用）
    └── api.js        streamChat(SSE) + reviewChat(非流式)
```

**挂载**：后端 `api/main.py` `include_router(ai_qa.router.router, prefix='/api/v1')`；前端 `main.js` `initAiQaHost()`。

**边界铁律**：`panel.js` **不 import** map/state/panel（主窗口函数）——全经 `protocol.js` 与主窗口通信。这是"形态可插拔"的关键（chat 是独立窗还是浮窗，核心逻辑零改动）。

---

## 第 2 章 · 情绪地图原理（MANIFESTO 的人类可读版）

AI 必须懂的核心 = 一条**数据流闭环**：

```
范围(Range)框定 ─► 范围内情绪散点(评论+坐标+时间)
   │         ┌──────────┴──────────┐
   │         ▼                     ▼
   │    聚合域①标准单元          聚合域②指定单元        ← 决策单元
   │   (方格/H3，均质)        (行政区/更新单元/用地)
   │         └─────────┬───────────┘
   │                   ▼
   │         【极性评价】(积极/消极/中性量化)
   │                   ▼
   │         【4×5 归因矩阵】(规划/更新/运营/治理 × 设施/环境/服务/文化/事件)
   │                   ▼
   │         【关键词/热门话题】(综合+极性)
   │                   ▼
   └──────────►  锚定聚合域 ─► 识别城建问题 ─► 可落地建议
                        └──── 视野↔数据↔结论 三者同步 ────┘
```

**逻辑闭环**：`极性评价 →（4×5归因 + 关键词 + 聚合域）→ 空间精准匹配需求 → 城建问题识别`。
无论用户问什么，解题路径都落在这条链某一环。数据语义当前 L2–L3（产"极性 + 归因/关键词"）。

4×5 治理要素（归因权威，禁臆造维度）：
- **4 领域**：城市规划 / 城市更新 / 城市运营 / 城市治理。
- **5 要素**：设施（配套，15 分钟生活圈）/ 环境（绿地正面、噪音脏乱负面）/ 服务（政务物业业态）/ 文化（历史人文活化）/ 事件（大型公共事件）。
- 归因落点 = domain × element。

---

## 第 3 章 · Harness 四层架构

一次问答完整流程（用户全程可见、流式；chat 在独立窗口，地图在主窗口，协议联动）：

```
[chat 窗口] 用户提问
   │  ◄── CONTEXT 消息：主窗口推送 buildContext() grounding 摘要
   ▼  ── 后端所有阶段 system prompt 前置 MANIFESTO（知识层）──
[Stage 1 · THINK]  Pro(deepseek-reasoner)
   reasoning_content ─►「思考链」区(灰显可折叠)         ← 里层（用户要的"看思考"）
   content(JSON){framing,mapping,steps[]} ─► 解题面板 STEP①②③
   │
[Stage 2 · EXECUTE+OBSERVE]  chat tools.js 发协议指令 ─► 主窗口执行地图操作 ─► 回包 observation
   ─► 解题面板 STEP④ + 执行轨道实时状态
   │  (MVP 开环；预留 reflect 钩子，未来深闭环)
   │
[Stage 3 · ANSWER(draft)]  Pro  ─► 结论初稿(流式 markdown+[ref:]) ─► 结论区(标"待审")
   │
[Stage 4 · REVIEW]  Flash  ─► 6 条 checklist → {pass,checks[],revise_hints}
   ├─ pass ─► 转正呈现
   └─ fail ─► 带 hints 回 Stage 3'(Pro 重写，最多1轮) ─► 呈现
   │  [ref:] 点击 / 附件卡 ─► ACTION 消息 ─► 主窗口聚焦/开 Overview
   ▼
最终呈现(排版易读 + [ref:] 可点 + 数据驱动 + 有结论有指向)
```

四层 ↔ 文件映射：

| 层 | 后端 | 前端 |
|---|---|---|
| 知识层 | `manifesto.py` | — |
| 思考层 | `prompts.py:build_think_prompt` | `stages.js:think` + `panel.js` 解题面板 |
| 执行层 | — | `tools.js` + `stages.js:execute` |
| 审查层 | `review.py` + `prompts.py:build_review_prompt` | `stages.js:review` + `panel.js` 审查区 |
| 协议层 | — | `protocol.js` + `ai_qa_host.js` |
| 形态层 | — | `chat.html`(独立窗) / `#chat-panel`(浮窗降级) |
| LLM | `llm.py` | — |
| 管线 | `router.py` | `harness.js`(STAGES) |

---

## 第 4 章 · SOP 解题协议（5 步 + Pro reasoning 分层）

**里层**：Pro `reasoning_content` 流式 → 思考链区（灰显可折叠）。零加工，"像其他大模型看思考"的本体。

**外壳**：固定 5 格解题面板，横跨多阶段填充（对齐情绪地图框架）：

| 格 | 内容 | 来源 |
|---|---|---|
| ① 问题定性 | 落在数据流闭环哪一环（极性/归因/定位/关键词/建议/定义） | think.framing |
| ② 框架映射 | 要走数据流哪几段（范围?点?聚合域?极性?归因?关键词?） | think.mapping |
| ③ 路径规划 | 基于数据状态规划步骤（已有聚合域?标准/指定?按什么排序?） | think.steps + 执行轨道 |
| ④ 执行·观察 | 每步真实数据（区域/极性/归因/关键词），核对是否够回答 | execute 逐步填 |
| ⑤ 结论·归因 | 按"极性→归因→关键词→聚合域→建议"闭环出结论 | answer |

think 阶段 JSON 从 B1 的 `{thinking, steps[]}` 升级为 `{framing, mapping, steps[]}`（强制 3 字段）。
**关键**：think **不用 json_mode**（DeepSeek reasoner 在 json_mode 下抑制 reasoning_content）；靠 prompt 强约束 + 前端 `parseThink` 容错解析（取首{...}）。

---

## 第 5 章 · Review 审查标准（六条 checklist + Revise）

**审查员**：默认 Flash（`deepseek-chat`，省 token、快），env `REVIEWER_MODEL` 可切 Pro。同步阻塞，最多 1 轮 Revise（防无限循环）。

**六条 checklist**（`review.py REVIEW_CHECKLIST`）：
1. **排版易读** `layout`：关键信息（数值/区域名/结论）凸显，分点清晰。
2. **结构清晰** `structure`：有"问题定性→证据→结论"体系化结构（非流水账）。
3. **内容精炼** `concise`：无废话/恭维/无意义话，信息密度高。
4. **语句专业** `professional`：贴合城市规划行业用语（专业名词 + 常规说法）。
5. **数据驱动** `data_driven`：引用具体数值与区域 + `[ref:]` 标注，不臆造。
6. **结论有指向性** `actionable`：有明确结论 + 可落地建议（有"出口"）。

**流程**：Draft(Pro) → Review(Flash json_mode) → `{pass, checks[], revise_hints}`。pass=false → 带 revise_hints 触发 Pro 重写（answer 阶段 `review_feedback` 分支）→ 呈现修订版 + 标"已按审查修订"。pass=true → 标"审查通过"。

---

## 第 6 章 · 窗口化与联动协议

**解决痛点**：B1 的底部全宽滑出面板折叠地图视野，用户反复开关切换。

**联动协议**（`protocol.js`，BroadcastChannel `CHANNEL='emotion-map-ai'`）：

| kind | 方向 | 说明 |
|---|---|---|
| `request` | chat→host | `{id,type,params}` 需回包（ensure_zone/rank_zones/inspect_zone/open_attribution） |
| `response` | host→chat | `{id,ok,data,note}` 回包 |
| `notify` | chat→host | 单向动作（focus，[ref:]/附件卡） |
| `push` | host→chat | 主动推送（context/selection/tokens） |
| `hello`/`bye` | chat→host | 生命周期（chat 启动→host 推 context） |

- `tools.js` 每个 tool = `request(type, params)` → Promise；`harness/stages` 形态无关。
- 主窗口 `ai_qa_host.js` 监听指令 → 现有函数（`generateGridForAI`/`setOverview`/`fitBoundsTo`/`cell:selected`），回包；图层变化主动推 `buildContext()` grounding。
- **buildContext() 在主窗口侧**（grounding 数据 `getLayers`/`getSelectedLayer` 在主窗口，chat 只接收字符串）——更干净的边界。

**窗口形态**（目标真独立窗口 + 浮窗降级）：
- **真独立窗口**：`#chat-trigger` → `window.open('chat.html', 'emotion_map_ai', 'width=440,height=620')`。用户可自由拉大、不挡地图、空间充裕。
- **浮窗降级**：`window.open` 返回 null（弹窗被拦）→ 主页面 `#chat-panel` 加 `is-float-fallback`（右下浮窗，不挡地图），动态 import `panel.js initChat`。
- chat.html 与浮窗降级**共用同一 `panel.js`**（一 UI 两挂载），逻辑零分叉。

---

## 第 7 章 · 可扩展性（未来接入点）

- **加 Stage**：`harness.js STAGES` 插项（`reflect` 深闭环 / 知识库 RAG 检索 / 专业规则库校验）。
- **换形态**：协议化后形态是可插拔外壳——浮窗↔独立窗↔侧栏↔移动端，核心 `harness/tools/panel` 不变，工程量小。
- **换知识层/审查标准/tool/provider**：各单文件（`manifesto.py`/`review.py`/`tools.js`/`llm.py`）。
- 子架构独立 → 未来做厚都在 `ai_qa/` + `frontend/js/ai_qa/` 内演进。

---

## 第 8 章 · 演进路线

- **v1（当前 MVP）**：四层 SOP + Review + 独立子架构 + 独立窗口。执行开环（plan 一次定 steps）。
- **v1.1**：`reflect` 深闭环（execute 每步后调 LLM 判断够不够，不够补步骤）。
- **v2**：多轮对话记忆（_messages 上下文累积）；@关联对象拖拽（contextTokens 接通）。
- **v3**：知识库 RAG（情绪地图专题知识检索注入 grounding）；多模型协作（不同 Stage 用不同模型）。
- **v4**：Agent 化（自主多步探索、跨数据源）。

---

## 附录 · 回答公约（MANIFESTO 第六节，审查层判定基准）

1. 数据驱动：仅基于"当前数据"与"执行观察"作答；引用区域名+数值，勿臆造。
2. `[ref:区域名]`：引用区域标注（可点 chip，点击定位地图）。
3. 结构清晰：问题定性 → 数据证据 → 结论建议。
4. 4×5 表达：归因用 domain×element，禁自创维度。
5. 语句专业：贴合规划行业术语，不口语化。
6. 结论有指向性：明确结论 + 可落地建议（有"出口"）。
7. 内容精炼：不废话、不恭维。
