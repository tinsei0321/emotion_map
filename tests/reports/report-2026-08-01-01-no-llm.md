# EMC 测试报告 · 2026-08-01 11:51

## RUN 2026-08-01 | schema=EMC-SUM v1 | mode=no-llm | n=45 | pass=36 80% | timeout=0 | gap=0 | 误杀=0 漏判=0 | 计划命中=0/0步 | t_p50=0s t_p95=1s | cats=全选
- 用户 OK 0 / BAD 0 / 未评 45

| ID | 名称 | 类型 | 判定 | judge | 用户 | template | 计划→实产 | 工具 | 参数/产物 | obs |
|---|---|---|---|---|---|---|---|---|---|---|
| CPD-01 | 空态欢迎卡 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | is-collapsed + welcome |
| CPD-02 | 折叠态 placeholder 非空 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | 向 EmotionMap Copilot 提问：了解"情绪地 |
| CPD-03 | 展开后 hint 不跳顶 | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | suppress bug |
| CPD-04 | 方向级联 emotion | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | 无细化 |
| CPD-05 | 方向级联 gis | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | 无细化 |
| CPD-06 | 方向级联 buffer | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | 无细化 |
| CPD-07 | 方向级联 inspect | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | 无细化 |
| CPD-08 | 点细化→填 input | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | 无细化 |
| CPD-09 | 引导卡 vs 欢迎卡互斥 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | 互斥 OK |
| CPD-10 | 返回方向按钮 | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | 无返回 |
| CPD-11 | 进度点 5 个 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| CPD-12 | chip 行 3 个 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-01 | Pro SVG 图标 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-02 | Flash SVG 图标 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-03 | Pro/Flash 切换 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-04 | 主题切换按钮 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-05 | 历史按钮 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-06 | 新对话按钮 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-07 | 发送按钮 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-08 | resize grip | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-09 | 折叠展开切换 | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | ? |
| UI-10 | 图层 chip 计数 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | =0 |
| UI-11 | CPD bar 折叠态隐藏 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| UI-12 | 提示条展开态显 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | hidden=true |
| PRED-01 | 空态 hasImport=false | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| PRED-02 | 空态 hasRange=false | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| PRED-03 | 空态 visEmotion=false | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| PRED-04 | 空态 hasAnalysis=false | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| PRED-05 | 导入点层 hasImport=true | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| PRED-06 | 情绪层 visEmotion=true | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| PRED-07 | 无情绪层 visEmotion=false（M2） | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | M2 回归 OK |
| PRED-08 | 导入范围 hasRange=true | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| PRED-09 | 删层回空态 hasImport=false | no-llm | ERR | err | — | ? | ?→0层 | ? | ? | ? |
| PRED-10 | H1 不冻结（general 后响应） | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | H1 不冻结 |
| RST-01 | layer-list DOM | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| RST-02 | #aiq-suggest | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| RST-03 | #chat-suggest | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| RST-04 | ctx-cap SVG | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| RST-05 | legend | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| SMT-01 | 流式中断 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | 中断路径走通 |
| SMT-02 | 新对话恢复 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | 恢复空态 |
| SMT-03 | 历史视图切换 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |
| SMT-04 | F5 恢复 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | F5 需手动验 |
| SMT-05 | 滚动不跳顶 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | scrollTop=0 |
| SMT-06 | 欢迎卡胶囊 | no-llm | OK | ok | — | ? | ?→0层 | ? | ? | ? |

## 待复查（9）
- **CPD-03** [s4] tpl=? suppress bug
- **CPD-04** [s2] tpl=? 无细化
- **CPD-05** [s2] tpl=? 无细化
- **CPD-06** [s2] tpl=? 无细化
- **CPD-07** [s2] tpl=? 无细化
- **CPD-08** [s2] tpl=? 无细化
- **CPD-10** [s4] tpl=? 无返回
- **UI-09** [s4] tpl=? 
- **PRED-09** [s0] tpl=? 
