# PT-CB16 · C2-4 评估：cdh 侧交互 UI 载体（Kimi·2026-08-25）

> **性质**：裁决点⑤ A 案配套评估件——「Codex Harness 侧追问胶囊/选项按钮」的落地范围与成本评估，供主手裁决是否立项实施。零实施。

## 白话摘要

三条规矩已经在「AI 的脑子和手册」里生效了（两个引擎都受益）。但你测试用的新引擎（cdh）的**屏幕上**还看不到两样东西：①回答下面「点一下就接着问」的小建议条；②AI 请示时的「点选按钮」（现在 AI 只能打字问你，你打字回答）。本评估算了笔账：把这两样接到新引擎屏幕上，大约要动三处、花 1.5~2 天。建议**立项但不必急**——因为今天刚修过那座「桥」（codex_bridge），隔一个批次再动它更稳；而且纯文字问答现在就能用，按钮是锦上添花。

## 一、现状断层（Qoder 实证链复核确认）

| 环节 | light 引擎（内置问答） | cdh（Codex Harness·主力） |
|---|---|---|
| 工具返回值进事件流 | 完整（tool.end 带 observation 全文） | **只有「工具名+完成/失败」**（`brain-adapter-codex.js` L93-98；`codex_bridge.py` L277-285 item/completed 仅透传 name/status/error） |
| 追问胶囊 | followup chips 链路完整（panel L1560-1566→followup.js） | 模型在 MCP 返回值里能看到 cue，**前端收不到** |
| ask 选项 UI | RENDER ask_user 事件（acp-channel L66/L146） | 无此事件通道·模型只能纯文本提问 |

## 二、落地范围与成本估算

| 件 | 内容 | 改动面 | 预估 |
|---|---|---|---|
| C2-4a | bridge 透传工具返回值摘要：codex_bridge 的 item/completed 事件增加 `observation_excerpt`（含 followup_actions/scale_check·截断 2KB 防大 payload） | `core/codex_bridge.py` + `frontend/js/ai_qa/brain-adapter-codex.js`（事件→panel trace.followupCues 接线） | 1 天 |
| C2-4b | ask 选项事件：模型文本提问的选项化（约定格式 `[ask] 问题 \| 选项A \| 选项B` → 前端渲染按钮·免 bridge 改协议） | panel 渲染层 + 身份卡句式约定 | 0.5 天 |
| C2-4c | 一键重放：胶囊点击直接按 params 调工具（跳过 LLM·机读结构的第一消费方） | panel.js 点击行为（回填→直发工具调用） | 0.5 天 |

**风险点**：codex_bridge 今日刚完成 interrupt 修复（f234bab3），建议隔批再动；observation_excerpt 必须截断+脱敏复核（工具返回值可能含大 geojson——layer_output 已改 dataset_id 后此风险大降，这正是先做 C2-1 的红利）。

## 三、建议

**立项 C2-4a（透传摘要）为下一批首件**（1 天·收益最大：胶囊+scale_check 同时上线）；C2-4b/4c 视 4a 落地体验再排。cdh 为唯一落地 harness 的战略定向（用户令 08-25）下，本件是「三机制收益触达主力引擎」的最后一公里——值得做，但不值得与 bridge 修复同批叠加。

---

> Kimi · 2026-08-25 · 评估件·零实施。
