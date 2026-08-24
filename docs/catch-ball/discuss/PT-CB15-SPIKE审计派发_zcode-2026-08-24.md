# PT-CB15 SPIKE · 双组审计派发（claude+Qoder 视角分工·zcode 收敛）

> 审计对象：Qoder spike 交付 `5925118`（四问全通·条件 PASS）。审计方：**claude（正确性/测试/集成）** + **kimi（产品/用户视角）**。收敛=zcode。
> 零实施零 git 写（审计报告除外）·分支 **`EMC_Codex_Harness`**·本地仓即最新。产出含白话摘要段。

## 审计范围（spike 交付文件）

| # | 文件 | 内容 |
|---|---|---|
| S1 | `core/codex_bridge.py` | app-server 常驻桥（F_042·惰性单例·15s 心跳·300s 看门狗·16MB 行上限·thread 续用=多轮） |
| S2 | `api/aiqa_routes.py` codex_engine 段 | SSE 端点（F_043·delta/tool/ping/done/error 五类事件） |
| S3 | `frontend/js/ai_qa/brain-adapter-codex.js` | 前端适配器（SSE→ACP msg.delta·恒 provenance='real'） |
| S4 | `frontend/js/ai_qa/panel.js` + `brain-adapter-dsh.js` | 第四引擎分发+徽标（白名单加 codex·一处改动） |
| S5 | `frontend/serve.py` | codex_engine 代理 600s+SSE 50s 豁免 |
| S6 | `tests/fixtures/codex_appserver_schema/` | Schema 版本锁（锚定 0.149.1） |

## claude 审计重点（正确性/测试/集成）

1. **S1 桥的正确性**：JSONL 解析健壮性（半行/坏行/超大行）；看门狗与心跳的交互（误杀活连接？）；线程生命周期（异常退出/重启/多轮续用状态）；F_042 免 @track 的豁免理由核实。
2. **S2 端点**：SSE 事件格式与 ACP v1.1 一致性；错误路径（codex 崩溃/断连/超时）用户看到什么；与 post_dsh_engine 的代码复用度（复制粘贴面=双维护风险？）。
3. **S3 适配器**：provenance='real' 与诚实性红线的符合性；消息丢弃/乱序防护；与 dsh 版的结构对称性。
4. **S4 第四引擎**：白名单改动对 light/dsh/mock 三态的回归风险；徽标正确性。
5. **S6 schema 锁**：README 的重建命令可复现性。
6. **测试覆盖**：spike 交付有没有测试？（579+4 绿里有多少是本件新增？）Q4 暴露的两个问题（双后端 inbox 竞争+map.js 样式竞态）有没有测试防回归？

## kimi 审计重点（产品/用户视角）

1. **用户流式体验**：实测 34-155ms/批的体感评估——是否真「逐字」；首字延迟 3-6.6s 对用户感知的影响。
2. **四引擎心智模型**：light/dsh/codex/mock 四态并存对用户操作的复杂度；徽标方案是否足够。
3. **Q4 两个残留问题对用户的影响**：双后端 inbox 竞争（测试时旧服务没关）——用户日常会踩吗？map.js 样式竞态（图层开关才显示）——用户体验损害程度。
4. **诚实性**：provenance='real' 的 codex 流 vs light 引擎——用户能看到什么区别。
5. **验收建议**：给用户的「自己怎么测」指引是否友好（8081 端口/关旧服务等前置条件）。

## 产出

落盘 `PT-CB15-SPIKE审计_{组名}-2026-08-24.md`：白话摘要段+逐文件发现清单（P1-P3+file:line）+横切发现+四档总裁决（通过/有条件通过/退回/搁置）。

## 收敛

两报告齐后 zcode 收敛：交叉对账+处置表+双能力评估（对 claude/kimi 本次审计能力）→ 报用户终裁。

> zcode 主手 · 2026-08-24 · 双组审计派发
