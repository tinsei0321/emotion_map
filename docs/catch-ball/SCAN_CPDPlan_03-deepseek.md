模型：deepseek

# CB-CPD-03 · CPD 核心引导逻辑 — DeepSeek 第三轮验证评审

> **评审模型**：DeepSeek V4 Pro
> **评审时间**：2026-07-22
> **CB 专轨**：CPD 核心引导 Plan · 第三轮 · 稳定化验证
> **评审对象**：`docs/cpd-core-plan.md` **v0.4**（CB-CPD-02 反评价后修订）
> **基线对比**：v0.3 → v0.4
> **评审基调**：本轮是三轮 catch-ball 的收尾轮。v0.4 变动量小但精准——修复 v0.3 引入的 2 个高优 + 3 个中优 + 2 个低优。评审聚焦：修复质量 + plan 是否已达"可进入 P0 实施"的稳定态。

---

## 第〇部分：CB-CPD-02 建议修复核实

| # | CB-CPD-02 | 优先级 | v0.4 状态 | 证据 |
|---|----------|--------|----------|------|
| R1 | S4 动态变量降级为 `{区域名}` | 高 | ✅ | §4.2 文案 "**{区域名}**的归因已就绪"，来源 `_followUps:455`；§4.2 规则注释："若未来要 domain/element/rank，由 turn-ended 载荷从 diagnose.card 结构字段带（留 G3）" |
| R2 | init 恢复模块边界措辞 | 高 | ✅ **超越修复** | v0.3 "导出只读 getter" 会致 panel.js↔cpd-guide.js 循环 import。v0.4 改**依赖注入**：`initCpdGuide({ getLastExit, isStreaming })`，panel.js→cpd-guide.js 单向，cpd-guide.js 零 import panel.js。这比 R2 建议的"措辞修正"更彻底——直接消除了架构缺陷 |
| R3 | hasImport 判据注释 | 中 | ✅ | §4.1 谓词注释："G1 实现注释列出排除来源：inspect_zone focus marker / zonal grid point / AI 组 point" |
| R4 | S3 空间引导实现路径 | 中 | ✅ | §6.4："G1=被动文案 / G3=地图高亮（三端同步橙色 #ff9000）" |
| R5 | U8 用户忙状态集中 | 中 | ✅ **超越修复** | §十一·U8：弃"3 秒时间窗"魔数→改 dock/param-panel `is-open` 确定性状态（复用 cpd-state.js:60-63 observer），比时间窗方案更稳 |
| R6 | range 加载文案优化 | 低 | ⬜ | v0.4 未纳入。低优先边界 case，G3 实施时自然处理 |
| R7 | U10 地图浮层远期 | 低 | ✅ | §十一·U10 维持远期 |

**核实结论**：7 条中 5 条修复（含 R2/R5 超越修复），1 条远期保留，1 条低优先延后。无残留阻塞项。

---

## 第一部分：v0.4 新增变更评审

### 1.1 H1 依赖注入 → 循环 import 消除

**这是本轮最重要的架构修正。**

v0.3 方案：panel.js "导出只读 getter"（`export function getLastExit()`）→ cpd-guide.js `import { getLastExit } from './panel.js'`。这会产生 `panel.js ↔ cpd-guide.js` 循环依赖——panel.js 需要 import cpd-guide.js（初始化时调 initCpdGuide），cpd-guide.js 需要 import panel.js（读 getLastExit）。

v0.4 方案：依赖注入。panel.js 在 init 时传入 getter 函数，cpd-guide.js **零 import panel.js**。

```js
// panel.js（调用方）
import { initCpdGuide } from './cpd-guide.js';
initCpdGuide({
  getLastExit: () => _history.at(-1)?.trace?.exit ?? null,
  isStreaming: () => _streaming,
});
// cpd-guide.js（被调用方）
let _getLastExit, _isStreaming;
export function initCpdGuide(deps) {
  _getLastExit = deps.getLastExit;
  _isStreaming = deps.isStreaming;
  // restore guidance from last trace...
}
```

**评价：A**。方向正确，消除了循环 import。`initCpdGuide` 的 deps 对象可扩展（未来加新依赖不破接口）。与决策 2 "引擎不 import panel.js"自洽。

**微瑕**：`initCpdGuide` 的调用时机需在 panel.js `initChatPanel` 流程中插入——plan §九 panel.js 行应明确调用位置（建议在 `_setupCpdBar` 之前）。当前 plan §九 panel.js 行写"init 时注入 getter（非导出，消除循环 import）"，措辞足够。

### 1.2 M3 流式优先级修正

**这是一个正确的 bug fix。**

v0.3 优先级文字写"hasImport 优先一切（先导数据）→ streaming=true（不打扰）→ ..."。但 streaming=true 应该是**绝对最高优先级**——用户正在看流式回答时，无论 hasImport 是什么，都不应该推任何引导。

v0.4 修正：优先级规则改为"`streaming=true`（不打扰，第一优先）→ `hasImport=false`（先导数据）→ ..."。

**核实**：表格中 streaming=true 行放在最后（`* | * | * | * | true | null`）——因为优先级规则是"自上而下首匹"，streaming 行放最后会先被 hasImport=false 匹配。但规则文字说 streaming 第一优先→实现时需 streaming 行放**第一行**或代码入口处提前 return null。

**这只是一个 plan 描述歧义**——表格物理顺序与文字优先级不匹配。G1 实现时按文字优先级（streaming 第一）即可。

### 1.3 M1 色名同步色带

v0.3 文案"深红"→ v0.4 "深橙"。代码核验：`tokens.css` very-negative = `#D85A30`（深珊瑚橙），确实无"深红"。色名现在从 theme var 派生——正确。

**延伸**：very-positive = `#0F6E56`（深青绿）→ 文案"深绿"正确。这是小改动但体现了对设计 token 的尊重。

### 1.4 M2 hasRange=false + result 兼带次 CTA

一个巧妙的边界处理：用户有数据、无范围、但上一轮已经是 result 出口（如 F5 刷新后）。v0.3 在此状态推 range 引导（正确），但丢失了上一个 result 的深读/导出入口。

v0.4 在 range 行加："兼带深读/导出次 CTA，避免演示高潮断档"。这是一个 **UX 平滑处理**——用户在"演示高潮"（刚得到一个好结论）后刷新页面，不应只看到"框选范围"，还应看到"继续深读上次结论"的入口。

**评价**：好设计。但"兼带次 CTA"的实现细节留给了 G1/G2——在 range 引导的 banner 中额外渲染深读/导出按钮。G2 实施时需确认 banner 组件支持多 CTA 布局。

### 1.5 新增 §6.5 引导态不持久化

**正确决策。** 引导态（guidance kind / `.has-guidance` 类）不写 localStorage。每次加载由引擎 init 恢复重算。

这与 `_emcCollapsed` 折叠态的策略一致（2026-07-22 用户定：F5 默认折叠不记忆）。引导态同哲学——信号全客户端可重推，不引入持久化的脏态风险。

---

## 第二部分：三轮迭代后的 plan 成熟度评估

### 2.1 架构稳定性

| 组件 | v0.2 | v0.3 | v0.4 | 稳定？ |
|------|------|------|------|--------|
| 映射 key | curState（结构性错误） | 特征向量真值表 | 同 v0.3 | ✅ 稳定 |
| 信号源 | .aiq-conclusion（死信号） | .aiq-exit-badge | 同 v0.3 | ✅ 稳定 |
| exit 词表 | 大写 RESULT/CONCEPT（错） | 小写五值+undefined | 同 v0.3 | ✅ 稳定 |
| turn-ended 载荷 | 未定义 | {exit,turnId,intent} | 同 v0.3 | ✅ 稳定 |
| init 恢复 | 无 | 导出 getter（循环 import） | 依赖注入（单向） | ✅ 稳定 |
| 优先级 | 无明确定义 | hasImport→streaming（矛盾） | streaming 第一 | ✅ 稳定 |

**结论**：v0.4 是第一个所有架构决策自洽的版本。v0.2→v0.3 解决了"是否正确"的问题（事实错误），v0.3→v0.4 解决了"是否自洽"的问题（循环 import / 优先级矛盾）。**plan 已达到可进入实施的稳定态**。

### 2.2 演示表现力收敛

| 维度 | v0.2 | v0.3 | v0.4 | 收敛？ |
|------|------|------|------|--------|
| 文案叙事化 | 功能名 | 叙事步骤 | 色名同步色带 + 动态变量降级 | ✅ |
| S3 空间交互 | 打字 | 点击地图（被动） | G1 被动 / G3 高亮三端同步 | ✅ 路径明确 |
| S4 闭环回视野 | 无 | 地图定位 CTA | 区域名动态填充 + M2 兼带次 CTA | ✅ |
| 三端同步橙色高亮 | 零提及 | 零提及 | G3 地图高亮 #ff9000 | ✅ 列入 G3 |
| 色名一致性 | 脱节 | "深红"（错） | "深橙"（从 theme var 派生） | ✅ |

**结论**：演示表现力从 v0.2 的 C+ 到 v0.4 已达到 **B+** 水平。剩余工作（三端同步橙色高亮、地图浮层）已明确列入 G3-G4 实施路径，不再有设计层未决项。

### 2.3 六维评级三轮演变

| 维度 | v0.2 | v0.3 | v0.4 | 总变化 |
|------|------|------|------|--------|
| 架构合理性 | B+ | A- | **A-** | ↑1 级（v0.4 消除循环 import，自洽） |
| 功能图谱完备 | B | A- | **A-** | ↑1 级（U1-U10 全部收敛） |
| 承重边界 | B+ | A- | **A-** | ↑1 级（光环 theme-var 列入 G2；依赖注入不破零 import 铁律） |
| 演示表现力 | C+ | B- | **B+** | ↑2 级（色名同步 + 动态变量降级 + 三端同步列入 G3） |
| 分阶段合理 | B | B+ | **B+** | ↑0.5 级（M2 兼带次 CTA 平滑演示断档） |
| 风险漏项 | C+ | B+ | **A-** | ↑2.5 级（流式优先级修正 + 循环 import 消除 + 引导态不持久化） |
| **综合** | **B-** | **B+** | **A-** | **↑2 级** |

---

## 第三部分：v0.4 可以进入 P0 实施

### 不阻塞实施的残留项

| # | 项 | 原因 | 处理 |
|---|----|------|------|
| 1 | 真值表 streaming 行物理位置与优先级文字歧义 | 表格放最后行，文字说 streaming 第一。G1 实现时按文字优先级（代码入口提前 return）即可 | G1 编码注意 |
| 2 | R6 range 加载文案 | 低优先边界 case | G3 自然处理 |
| 3 | S4 "若未来要 domain/element/rank" 的远期扩展 | G3 预留，非当前需求 | 不阻塞 |

### 不建议再开 CB-CPD-04

plan 已进入稳定态。v0.2→v0.3→v0.4 三轮迭代已将核心架构决策全部收敛（映射 key / 信号源 / exit 词表 / 载荷 / init / 优先级）。剩余的开放项（U8-U10）均为 G3 实施细节，不需要在 plan 层继续迭代。

**建议**：CB-CPD 专轨在此轮收尾。项目方进入 P0 测试铺底 → P1 尺度诚实 → P2 G1-G4。若实施过程中发现 plan 层的新问题，再开 CB-CPD-04。

---

> **给项目方的后续指令**：
> CB-CPD-03（第三轮验证评审）。CB-CPD-02 的 7 条建议中 5 条修复（含 2 条超越修复）、1 条远期、1 条延后。
> v0.4 综合 **A-**（v0.2 B- → ↑2 级）。plan 已达到可进入 P0 实施的稳定态。
> **建议 CB-CPD 专轨在此轮收尾**。三轮迭代已将核心架构决策全部收敛，剩余开放项（U8-U10）为 G3 实施细节。
