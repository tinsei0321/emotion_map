---
name: audit-script-utf8-output
description: 跑含中文输出的核验/审计脚本必须 py -X utf8，否则 GBK 乱码致数字误读
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 63ae6e3f-ed3b-4eb0-a9cb-aacd777c0ecb
  modified: 2026-08-13T14:36:28.654Z
---

Windows 下 `py script.py` 默认 stdout 编码 GBK，跑含中文标签（社区名/村名等）的核验脚本会乱码。虽然 ASCII 数字本身清晰，但中文标签乱码时，大脑极易把**刚才读过文档（md/Excel）里的数字"脑补"进乱码输出**，把错数当成自己复算的结果——CB-33 实测踩坑：v1 脚本 GBK 输出下，我把 page4 md 的错误数字（精确社区1300/港务168）误读成了"我的复算结果"，差点据此判 agree；UTF-8（`py -X utf8`）重跑才见真相（1035/港务83），推翻 md。

**Why**：数字审计/对账场景，乱码误读会直接产出错误审计结论（agree/disagree 判反），后果严重；且这种误读是静默的——数字看着"合理"（因为脑补的就是文档值），不交叉验证发现不了。

**How to apply**：
1. 任何含中文 stdout 的核验脚本，一律 `py -X utf8 script.py`（或 `PYTHONIOENCODING=utf-8`），别偷懒。
2. 数字核验**必须交叉验证**：独立脚本复算 + 已生成交付物文件读回计数，两路一致才采信；单一来源（尤其乱码来源）不可信。
3. 当"我的复算结果"与某文档**完全相同**时要警惕——可能不是算对了，而是乱码误读/脑补，应换干净编码重跑确认。
4. 与 [[no-routine-playwright-verify]] 的"实现→交付→用户验证"不同，数字审计是"必须自己验准才下判"，不能交给肉眼。
