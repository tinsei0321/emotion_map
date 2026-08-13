# dsh 组 onboarding 任务 · 全局深读（2026-08-14）

> 发起方：Codex 主开发 · 对象：dsh组（deepseek harness）· 分支：`codex/dsh-onboarding`
> 定位：dsh组 = 第三方评估/理解方，职责与规则同 zcode组、claude组

## 欢迎

欢迎 dsh组 加入。你的定位、职责、规则与 zcode组、claude组 **完全相同**——第三方评估/理解方：只读数据与代码、禁 git、意见落盘 `docs/catch-ball/discuss/`。

## 一、双项目 + 双工作环境（路径不同，先认路）

1. **情绪地图项目（代码仓库）**：`D:\Github\emotion_map`（办公室与家同一路径，git 同步）
   - 定位「体检医生·模块」：处理分析城市体检数据（客观指标 + 主观诉求）。
2. **宜昌市中心城区城市更新专项规划（资料库·数据）**：
   - 办公室：`D:\OneDrive\2026\15_城市更新专项规划研究`
   - 家：`C:\Users\Hi\OneDrive\2026\15_城市更新专项规划研究`
   - 数据中转站（只读）：`…\1 宜昌市城市体检\EMC数据中转站\`

## 二、本次紧急任务 = 两项目交叉「两边支撑 + 两边消费」

- **情绪地图（支撑方）**：提供数据处理、空间分析、RAG、客观/主观双轨能力。
- **城市更新专项（消费方）**：消费情绪地图分析结果 → 安全韧性底线 + 民生基础需求两板块 → 图/数/表/观点 → 分析报告。
- **当前进度**：page1-6 已定稿（page4/6 去村），page7「问题与需求小结」进行中（密度 + 分层方案）。

## 三、必读清单（全局深读·按顺序）

1. `AGENTS.md`（协作规范·编码铁律·追踪体系·9 Agent 角色）
2. `CLAUDE.md`（顶层纲领·出口抽象层三铁律·空间落位铁律 7·演示逻辑链）
3. `docs/catch-ball/_cb-index.md`（CB 入口·当前 CB-33）
4. `docs/catch-ball/RULES.md`（评估规则·权限口径·落盘规范）
5. `docs/catch-ball/KNOWLEDGE.md`（红线·语境卡片）
6. `memories/repo/session-handoff.md`（主交接卡·隐规则清单·测试基建）
7. `docs/catch-ball/_handoff/OFFICE.md` + `HOME.md`（双环境卡片）
8. `docs/catch-ball/cb-journal.md`（CB 轨迹）
9. `docs/prd.md` + `docs/spec.md` + `docs/architecture-pattern.md`
10. `DATA/analysis/`（当前分析产物结构）+ `06_主观数据治理/` + `02_空间数据集/`

## 四、你的规则（与其他第三方完全相同）

- 只读项目数据与代码；禁 git；禁写生产代码/数据/正式 Excel。
- 意见必须落盘 `docs/catch-ball/discuss/`（或 scan/），禁只回聊天文字。
- 代码禁 emoji；print 走 `_safe_print`；术语「街办」非「街道」。
- 实事求是、不附和：发现问题当场说，不硬凑错误结果。
- prompt 用代码块包裹。

## 五、本次输出（落盘）

全局深读后，落盘一份「项目全景理解报告」：
`docs/catch-ball/discuss/dsh-项目全景理解_2026-08-14.md`

内容至少含：

1. 项目全景（七层架构 / 双轨 / 两板块 / 片区=结论）
2. 两项目关系（两边支撑 + 两边消费）
3. 双工作环境路径差异
4. 你理解的规则 / 要求 / 习惯清单
5. 对 page7 当前「密度 + 分层」方案的独立看法（可选）
