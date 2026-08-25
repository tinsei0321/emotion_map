你是 Qoder，担任 EMC（情绪地图）项目的评审组。请与 Kimi 组就「交互三机制」讨论稿做联合讨论，给出你的独立立场。

【背景】
用户实测新 Harness 时提出三类体验问题：①追问要重述背景（AI 不会接话）；②关键分支 AI 不请示就自行决定（或反过来问太多）；③大问题小问题一个跑法（不会看事情大小）。Kimi 已写出规格草案，进入 D1 讨论定稿环节，未定稿不实施。

【讨论对象】
docs/catch-ball/discuss/PT-CB16-D1-交互三机制讨论稿_Kimi-2026-08-25.md（先读）
背景材料：
- docs/catch-ball/discuss/PT-CB10-测试问题入档与排档_zcode-2026-08-21.md（问题 2/4/5 主手初稿意见）
- docs/catch-ball/discuss/PT-CB16-短板修复计划书_Kimi-2026-08-25.md §三 C2 节

【请逐条给出立场（吸收/调整/反对+理由）】
1. 追问机制：followup_cues 从纯文本升级为机读结构 {cue_text, tool, param_delta}——成本 vs 收益是否成立？续接路由放宿主侧是否有更优解？
2. 选择机制：三触发清单（不可逆分支/两解成本差大/口径分叉）是否有遗漏或冗余？频率上限「快档≤1/研究档≤2」是否合理？
3. 规模机制：意图卡 scale 三枚举（brief/analysis/research）粒度是否合适？出口核对用软提示还是硬阻断？
4. 实施切分（C2-1/C2-2/C2-3 共约 4 天）是否合理，有无更优排期？

【纪律】
- 不采信 Kimi 结论，有异议直接点名（带证据/先例）；业界同类机制（OpenAI reasoning_effort、Claude thinking budget、CPD 渐进式披露）可引用对照。
- 输出落盘 docs/catch-ball/discuss/，命名 PT-CB16-D1-交互三机制回应_Qoder-2026-08-25.md，逐条四档立场+理由。
- 纯讨论零实施：不改任何代码与配置。
