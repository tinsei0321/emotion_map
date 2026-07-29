# GLM 验收 Prompt — EMC 飞轮测试模块扩建

> **提交方**：用户（ZCode + DeepSeek 规划） → **验收方**：GLM（VS Code + Claude Code 实施）
> **日期**：2026-07-29

---

## 一、背景

EMC 当前 `?test=1` 飞轮测试模块已初步搭建（`test-board.js` + `test-cases.js` + `test-board.css`），但存在以下问题：

1. **用例与 bug 脱节**：CB 诊断发现的 bug 未注入飞轮
2. **报告堆积无索引**：`tests/reports/` 有 12+ 份历史报告，无法快速对比趋势
3. **无 bug 追踪**：发现的 bug 散落在根因报告、CB journal、对话中，无统一追踪
4. **重复问题无标记**：同一用例反复失败看不出历史

## 二、需要你验收的方案

完整方案见：`docs/catch-ball/arch/FLYWHEEL_PLAN_2026-07-29.md`

### 核心要求

1. **所有改动基于现有 `?test=1` 模块扩建**，不另起炉灶。代码改动集中在：
   - `test-board.js` — 内部新增仪表盘渲染函数
   - `test-cases.js` — 内部新增数据读取逻辑
   - `test-board.css` — 追加仪表盘样式
   
2. **新建数据目录**（被上述文件读取）：
   - `tests/buglog/` — Bug 追踪日志（open / resolved / recurring）
   - `tests/reports/INDEX.md` — 报告索引
   - `tests/_index.md` — 飞轮总入口文档

3. **Bug 采集 Skill**：新建 `.agents/skills/bug-collector/SKILL.md`，用于标准化用户提交的 bug 描述并写入 buglog。

4. **飞轮仪表盘 UI**（在现有 `?test=1` 抽屉中追加）：
   - 4 个 KPI 卡片（通过率 / 平均耗时 / Bug 待修 / 回归检测）
   - 通过率趋势图（最近 7 次飞轮）
   - 重复问题标记
   - 未解决清单
   - 报告详情入口

### 扩建映射表

| 现有文件 | 扩建方式 |
|------|:---:|
| `test-board.js` | 内部加仪表盘组件（不删现有测试运行功能） |
| `test-cases.js` | 内部加读取 buglog/reports 逻辑（不删现有用例） |
| `test-board.css` | 追加仪表盘样式（不删现有样式） |
| — | 🆕 `tests/buglog/` 三级目录 |
| — | 🆕 `tests/reports/INDEX.md` |
| — | 🆕 `tests/_index.md` |
| — | 🆕 `.agents/skills/bug-collector/SKILL.md` |

## 三、请你验证/评估的事项

1. **方案可行性**：在当前 `?test=1` 架构上扩建，技术路径是否合理？AGREE / DISAGREE / PARTIAL + 理由。
2. **遗漏或冲突**：方案中有无遗漏的环节？与现有代码有无冲突点？
3. **工作量估算**：按 P0→P1→P2→P3 顺序，每个阶段的预计代码行数和工时。
4. **改进建议**：方案中可以优化或简化的地方。
5. **一句话总评**。

## 四、验收输出格式

按 CB 标准（agree / disagree / partial + 证据），逐条回应：

```
1. 基于现有 ?test=1 扩建 — [agree/disagree/partial]
   理由：
   
2. 扩建映射表完整性 — [agree/disagree/partial]
   理由：

3. buglog 目录设计 — [agree/disagree/partial]
   理由：

4. 仪表盘 UI 设计 — [agree/disagree/partial]
   理由：

5. Skill 设计 — [agree/disagree/partial]
   理由：

6. 工作量估算
   P0: 
   P1: 
   P2: 
   P3: 
   
7. 一句话总评：
```

---

> **参考文件**：`docs/catch-ball/arch/FLYWHEEL_PLAN_2026-07-29.md`
> **CB 入口**：`docs/catch-ball/_cb-index.md`
