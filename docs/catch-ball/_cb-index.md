 CB Index — Catch-Ball 统一入口

> **读我**：claude组（Claude Code 开发主）+ Codex + zcode组（ZCode + GLM 5.2·2026-08-11 由 glm组 正式更名）启动时读此文件，了解 CB 全貌。
> **维护**：每轮 CB 完成后更新。最后更新：2026-08-21 上午（**PT-CB8 避坑沉淀报告落盘·全组当轮回应待收**：Codex 受用户令收集 EMC×dsh 期（08-18~21）全部踩坑，归纳六条元模式+业界对照+维护机制，固化 debug-memory R1-R19（撞号修正+新增 R17-R19+维护协议）；报告 `discuss/PT-CB8-EMC-dsh避坑沉淀报告_Codex-2026-08-21.md`——zcode/claude组/dsh/Qoder 按 AGENTS v2.4 四档裁决当轮回应·**已派 zcode 全局部署**·派发单 `discuss/PT-CB8-E3回收与全局部署派发_Codex-2026-08-21.md`）‖ 上一记：2026-08-18 下午（**EMC×dsh 可行性深挖收工**：dsh组深挖回应 + Codex 抽验 + 通俗收工报告 + HOME 交接完成；五项决策待用户回家确认；CB-41 / CB-39 照各自线推进）。

---

## 当前状态

| 项目 | 状态 |
|------|:---:|
| **全局核心路线** | **EMC×dsh 工程预期与双环境同步核心思想（08-21 用户定稿）**——测试期 dsh=外置实验驾驶舱，消费 EMC 数据/RAG/注册 Toolbox/render 契约并控制 8080 出图；稳定期 EMC 产品壳吸收测试链路。权威报告 `discuss/EMC-dsh工程预期与双环境同步核心思想_Codex-2026-08-21.md`；AGENTS v2.5 + KNOWLEDGE + context-map 已挂全局指针。各组涉及该线必须先读并遵守 |
| **当前 CB 轮次** | **CB-41 · 体检点聚合双 bug 修复轮·已收敛转实施**（B013 聚合着色反语义 + B012 tip 社区归属错乱；发起/排查/定稿三件套在 `discuss/CB41-*`；用户拍板 §六：着色语义 UI 显式分叉·点数模式=临时出图不接 EMC 出口）‖ **CB-39 · 双线实施**（数据线：P0 工程线✅验证通过 + A 线 A1-A5✅ → **待 B 线治理**；基线 366+3；唯一现行计划 `discuss/CB39-实施计划_Codex-2026-08-16.md` v3.1）‖ **CB-40 · EMC 现状与目标差距·已收敛**（`discuss/CB40-EMC现状与目标差距_收敛定稿_2026-08-16.md`·CB-39 后排期依据：G1>G5>G2·`docs/goal-status.md` 每轮必更） |
| **上一轮** | CB-38 主线回归与数据沉淀（收敛定稿 + EMC 全局审计 D1-D9 裁定·双输入线并入 CB-39）；CB-24~37 简记见 cb-journal 顶部补账 |
| **当前环境** | **Codex（主开发·唯一 git 写者·08-13 起）** + **claude组（第三方独立评估+收敛）** + **zcode组（本线接续：page7 图层线 + CB-41 双 bug 修复·用户指派）**（dsh组 本轮经用户指派回归参与 CB-41 排查） |
| **当前分支** | `EMC_harness_dsh`（**PT 实施分支**·2026-08-19 用户纠正：实施一律走分支，main 只经用户授权合并；08-18 晚主手曾误判「实施回归主干」并快进推送 main（纯增量·已纠正·详见台账 R17）；**main 用户裁定冻结不动（08-19）——各组一律切分支工作**（dsh 08-18 T3 两提交原落 main·已快进收编进分支·无损）|
| **最新讨论** | **PT-CB8 学习线：EMC×dsh 避坑沉淀报告（08-21·Codex 受用户令·全组当轮回应待收）**——收集 08-18~21 EMC×dsh 全部踩坑 → debug-memory R1-R19（撞号修正/新增 R17-R19/维护协议）+ 六条元模式 + 业界对照 + T1-T6 调优建议；落盘 `discuss/PT-CB8-EMC-dsh避坑沉淀报告_Codex-2026-08-21.md`，回应义务见其 §七 ‖ **PT-CB3 EMC 意图外置与需求契约（08-19 下午·claude 发起·待 zcode 研判）**——用户学习 Cordis 时提出：**抛弃 EMC 内部意图理解 Agent、意图理解完全外置**给外置大脑（LLM+Harness 的 MCP 服务），以"意图→结论"**需求契约**防跑偏（业界答案=From Prompts to Contracts 论文/JSON Schema 输出验证层/契约单一权威源），演示近期**静态化**。落盘 `discuss/PT-CB3-EMC意图外置与需求契约_讨论发起_claude-2026-08-19.md`；请 zcode 研判（范式体系如何在外置场景保住/契约粒度/与 MCP v1 关系）‖ **PT-CB3 学习线：dsh 精髓学习报告与插件化方向（08-19·发起·zcode 两轮回应·待 Codex→收敛）**——用户学习 dsh Harness 后要求输出详细分析报告并发放 zcode/Codex 调优方向；发起文档 `discuss/PT-CB3-dsh精髓学习报告与插件化方向_讨论发起_2026-08-19.md`（**编号已定：学习线=PT-CB3（用户 PT 命名令）·下轮实施批=PT-CB4**）。**08-19 深化（claude 组·用户"行动轨迹线性"令）**：发起文档已追加第八节「Cordis 框架系统学习」（七核心概念 Context/Plugin/Service/inject/Event/Effect/Fiber + 论文溯源 Parnas/微内核/Fowler DI/Saga 可逆计算/责任链 + dsh 应用映射 + 对平台启示·只借思想不引运行时），讨论问题扩至 16 问（原 10 问 + 补充 6 问，其中 13/15/16 已被 zcode 裁决覆盖，11/12/14 待 Codex 补答）；独立纪要文件已合并删除（学习线单文档线性延续）。**zcode 已回应**（`discuss/PT-CB3-dsh精髓学习_zcode回应与调优_2026-08-19.md`·四档裁决：A1-A4 立即吸收进 T2/派发规范·B1-B4 并入排期（MCP v1 排 B/C 线后·自家先吃狗粮）·C1-C2 暂缓（render_spec/rag 默认综合）·D1 反对现在开 MCP 专项（时序）·D2 修正报告基线（manifest 57 层已注册））**zcode 二轮回应已落盘**（`discuss/PT-CB3-Cordis深化_zcode二轮回应_2026-08-19.md`·AGENTS v2.4 新规首次执行：A5 观察者必须放行/A6 副作用必带补偿吸收为纪律·C3 不做 Python 守卫原型·D3 修正 tool_contracts 同构表述·补答 11/12/14）**意图外置线终收敛 v2 定稿**（`PT-CB3-意图外置终收敛v2_zcode-2026-08-19.md`·三方链闭合：用户质疑"零思考壳子论"→zcode 接受修正废除内部路由→dsh 实现者评价五问全答→v2：EMC=契约集合体四类+两补充/零思考操作性定义(闭包校验+纯规则红线)/结构化打回+em:mode 分流器+方法论契约双写/过渡四步+对拍+回滚开关+切换判据四条·首个实施触点=PT-CB4 T2）——取代 v1（`PT-CB3-意图外置收敛_zcode-2026-08-19.md`·用户拍板三项：意图理解完全外置/需求契约=防跑偏核心/演示静态化；zcode 收敛 N1-N9：范式映射下沉为契约不随 Agent 外移·LLM 只做转译·两级契约（工具级已有+意图卡新增）·并入 MCP v1 设计输入·内部 Agent 冻结不拆四步过渡；Codex 审计视角可非高峰补）‖ **待 Codex 回应收敛** ‖ **EMC×dsh 可行性深挖（08-18 下午·收工）**——① dsh组 回应：主路=标准插座，不建议 dsh 专用插件/深嵌；三项修正=结果口径标签、数据说明书、知识综合；② Codex 抽验：三项强吸收，纠正 dsh 破坏性变更与旧目录口径；③ 外接大脑=零维护观察，不进产品排期；④ 用户沟通纪律全局生效（禁裸用内部代号）；⑤ 收工报告 `discuss/EMC-dsh可行性深挖_收工报告_通俗版_Codex-2026-08-18.md` + HOME 卡待回家续读 ‖ **EMC×dsh R0-R9 拍板包仍待用户确认** ‖ **CB-41 体检点聚合双 bug 修复轮已收敛转实施**（详见 CB41 文档） |
| **最新进展** | **PT-CB2 B1 批全完工（08-19·待送审）**：T1 图层注册四件套（8 组 57 层·usage 45+12）+ T2 usage 消费点（守卫 F_004/D_002 三段式拒绝·后端十端点+前端 ref() 双侧·门禁 387+3）+ T3 验收包（check_manifest 0err/2warn 存量·冒烟三链路·R7 变体入档）——送审包四件就绪 ‖ CB-39 已开工：P0-2 守卫通电（9 validate_*·15 ID 补注册·SKILL_DEFS 真身解析）+ P0-1 诚实度（phase 真实标签·key 空显式报错·L0 隔离）+ A 线回收归集（E16 六件迁出演示池·数据池三分·page7 归档·**总账 100 行**）；performance 只剩 sim=时间轴专题轮分轴前提；下一批 B 线治理 |
| **接手文档** | `memories/repo/session-handoff.md` + `docs/catch-ball/cb-journal.md`（CB-38 + CB-29~37 补账）+ `_handoff/HOME.md` + `OFFICE.md` |
| **上次操作人** | tinsei0321 + Codex（专题 R8 回收/R9 发起与收敛/拍板包/通俗报告/收工归档·commit push 经授权）+ 三组（形态3 评审×2 + 外挂大脑×3） |

## 快速开始

### claude组（Claude Code·开发主）

1. Hook 自动检测：`.claude/hooks/on_session_start.py` 启动时打印 CB 状态
2. 手动：读本文件 → 按需进入对应目录
3. 新接手：读 `_handoff/DEEPSEEK_ONBOARDING_2026-07-30.md`

### Codex / glm组（CB 辅助评估）

1. 读本文件了解当前轮次 + 最新 SCAN
2. 读 `KNOWLEDGE.md` 了解红线和语境
3. 产出 SCAN → `scan/CB{NN}-{topic}_{env}-{model}_{YYYY-MM-DD}.md`（glm组 用 `CB{NN}-{topic}_glm组_{YYYY-MM-DD}.md`）
4. 按需进入对应目录
5. **glm组（ZCode + GLM 5.2）**：以第三方评估者身份加入·独立 SCAN/讨论·与 Codex 互补视角·非开发主

## 文件夹地图

```
docs/catch-ball/
├── _cb-index.md          ← 你在这里
├── RULES.md              CB 规则（评估方法、七轴评分、文档规范）
├── KNOWLEDGE.md          CB 记忆库（红线、语境卡片、SCAN 标尺纠正）
├── cb-journal.md         CB 轨迹（按轮倒序·SCAN摘要+反评价+行动+状态）
├── retired.md            退役台账
│
├── scan/                 SCAN 评估报告
│   ├── CB01~CB03         历史评估（DeepSeek）
│   ├── CB09-*.md         CB-09 实测诊断 + GLMv3 修复审计
│   └── cpd/              CPD 专轨评估
│
├── rootcause/            根因分析报告
│   ├── 2026-07-28-MC-field-rename.md
│   ├── 2026-07-28-layer-hallucination.md
│   ├── 2026-07-28-nl-vs-capsule.md
│   ├── 2026-07-28-streaming-failure.md
│   └── 2026-07-28-finalstep-timeout.md
│
├── audit/                综合审计报告
│   ├── 2026-07-28-comprehensive.md  全局复盘+代码审计
│   └── 2026-07-28-deep-dive.md      全链路+识别+路由深度审查
│
├── arch/                 架构设计 + 历史评估文档
│   ├── SUMMARY.md        v2 架构全景（68 决策）
│   ├── 01~09-*.md        9 模块设计
│   ├── EVAL_*.md         历史评估报告
│   └── ...
│
└── _handoff/             换机交接卡 + 接手文档
    ├── HOME.md            家里做了什么、待做什么
    ├── OFFICE.md          办公室做了什么、待做什么
    ├── SESSION_2026-07-30.md     今日 Session 完整记录
    └── DEEPSEEK_ONBOARDING_2026-07-30.md  Claude Code + DeepSeek 接手文档
```

## CB 流程

```
SCAN 阶段（评估方：Codex 或 glm组·CB 辅助·独立于开发主 claude组）
  ① 读本文件了解当前轮次
  ② 读 KNOWLEDGE.md 了解红线和语境
  ③ 产出 SCAN → docs/catch-ball/scan/{NN}-{model}.md（glm组 用 {NN}-glm组.md）
  ④ 更新本文件「待反评价」
  ⑤ 更新 _handoff/{HOME|OFFICE}.md

Journal 阶段（项目方：claude组）
  ① 读本文件发现新 SCAN
  ② 逐条反评价（agree/disagree/partial）
  ③ 追加 cb-journal.md 对应轮次
  ④ 更新本文件「已反评价」
```

## 换机指南

1. **到新环境后**：`git pull` → 读本文件 → 读 `_handoff/{HOME|OFFICE}.md`
2. **离开前**：更新 `_handoff/{HOME|OFFICE}.md` → `git commit + push`
3. **跨环境一致性**：所有 CB 文件在 git 中同步，两边都能看到完整历史
