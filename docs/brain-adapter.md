# BrainAdapter 接口契约 v0.1（壳阶段 S1 · 只定义不实现 · 2026-08-23）

> 依据：壳阶段联合任务书 v1.0 §一.1（双轨制·BrainAdapter 接口位预留）+ ACP 契约 v1.1。
> 角色：**壳与引擎之间的翻译层接口**——壳只认 ACP 事件流与四动词，不认引擎具体形态（可插拔大脑的接缝）。
> 红线：只定义签名不定义实现（YAGNI·接口超一页即砍）；**编排权在引擎层——Adapter 是翻译层非编排层**（壳不经 Adapter 调度 MCP 工具）。

## 一 接口签名

**事件出**（Adapter → 壳·ACP 五族事件流·语义见 `docs/acp-contract-v1.md` §二/§五）：

```text
emit: msg.delta(kind: 'reason'|'content', provenance: 'real'|'synthesized')
      tool.begin(name, params_summary)
      tool.end(payload: {工具特定摘要 + caliber 摘要}, followup_cues?)
      error(code, hint)
      approval.req(...)
```

**动词入**（壳 → Adapter·ACP 四动词）：

```text
open(context) -> session_id        # 开会话（携垂域 grounding/意图）
step()                            # 推进一轮（思考/工具/出图·事件流随之发射）
seal()                            # 定稿出口（答案/图层/报告）
close()                           # 关闭（留痕归档）
```

## 二 三形态

| 形态 | 机制 | provenance | 状态 |
|---|---|---|---|
| **轻循环引擎**（内置·首引擎） | ai_qa 四阶段直发 ACP 事件（`ai_qa/prompts.py` 既有管线·只动事件发射层） | 恒 `real` | 壳阶段主路（S4） |
| **dsh 降级形态** | headless 调用 + 壳侧进度桩事件模拟（无真流式） | **桩事件必带 `synthesized`**（前端渲染为「步进进度」非「思考流」·ACP v1.1 §五-1 诚实性标记） | 接口位预留·按需实现 |
| **Codex 全量形态**（注记） | app-server 官方「自建 UI」路径（`codex app-server --stdio` JSON-RPC·桥 `core/codex_bridge.py`·SSE 端点 `/aiqa/codex_engine`）——事件映射沿 ACP v1.1 §四宿主映射表 | 恒 `real` | **PT-CB15 已验证转正**（2026-08-24·四问实测·引擎第四态 `?engine=codex`）——运维见 `docs/codex-harness-ops.md` |

## 三 验收（未来怎么审）

1. 契约符合性：任一形态实现的事件流过 S6 schema 校验器（五族+provenance·pytest 桩）；
2. 双轨对照口径：轻循环引擎上线时同题 10 题 × 两引擎对照（纯问答/GIS 操作/情绪分析/知识问四类）——架构证据进 CB 归档；
3. 降级形态诚实性：dsh 适配器发出的全部 msg.delta 均带 `provenance='synthesized'`（缺省即违规）。

---

> SHELL(S129) S1 · Qoder · 2026-08-23 · BrainAdapter 接口契约（半页）·zcode 审读收敛
