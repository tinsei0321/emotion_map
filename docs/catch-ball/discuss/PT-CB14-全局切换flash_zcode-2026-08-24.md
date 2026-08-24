# PT-CB14 · LLM 全局切换 Flash（zcode 主手·2026-08-24）

> 用户令：「EMC 接入的 LLM 默认模型如果是 pro 请全局切换成 flash，不需要 pro——保证 EMC 使用时一直在用 flash」。

## 排查结果（三处 pro·一处已 flash）

| 位置 | 原模型 | 处置 |
|---|---|---|
| 前端思考深度开关（panel.js _thinkMode） | 已强制 flash（CB-12 用户拍板·localStorage 残留也强制回 flash） | ✅ 无需改 |
| 后端默认（ai_qa/llm.py DEFAULT_MODEL） | **pro** | ✅ 改 flash（与前端强制 flash 对齐·消除"前端发 flash 但无参调用走 pro"的隐患） |
| dsh 全局（~/.dsh/settings.yaml·3080 web） | **pro** | ✅ 改 flash |
| dsh emc-test profile（8080 dsh 引擎） | **pro**（effort=max 为 pro 上定档） | ✅ 改 flash（effort 保留 max·**flash+max 重验标注**） |

## 验证

- 后端：`_resolve_model(None)` → deepseek-v4-flash；pro 仍可显式用（保留别名·不删除）；
- 门禁 581+2 零退化；
- **flash+max 稳定性初验**：真实分析题「12345 top5 显示在地图上」一次通过——完整答案+口径说明+出图（图层「12345热线诉求最强烈TOP5社区」）——flash 在多工具链+max 档可用，与 pro 同效果；
- dsh 双 profile dump 已确认 flash。

## 注记

- flash+max 仅初验 1 次——后续 T1-T7 重跑窗口按 R25 纪律补 ×3 稳定性数据；
- rag synthesize 等路径无显式 model 时均走 DEFAULT=flash（统一）；
- 本改动含 ~/.dsh（仓外）——复刻清单：两处 settings 的 model 行改 flash（各机照改）。
