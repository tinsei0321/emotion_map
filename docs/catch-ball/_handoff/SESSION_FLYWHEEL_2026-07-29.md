# 新会话衔接 Prompt — EMC 飞轮测试 + Bug 采集

> **用途**：在新会话（ZCode 或 VS Code）中粘贴此 Prompt，快速恢复上下文并进入飞轮测试工作流。
> **日期**：2026-07-29 | **上一会话**：ZCode + DeepSeek

---

请先阅读以下上下文文件恢复状态：

## 必读文件（按顺序）

1. `docs/catch-ball/_cb-index.md` — CB 全貌（当前 CB-09）
2. `docs/catch-ball/arch/FLYWHEEL_PLAN_2026-07-29.md` — **飞轮优化方案**（本次核心）
3. `docs/catch-ball/scan/CB09-v1.0实测诊断_ZCode-DeepSeek_2026-07-28.md` — 最新 CB 报告（5 案例 + 7 根因）
4. `tests/emc_test_cases.md` — 当前飞轮用例目录（20 个）

## 当前状态

飞轮测试模块基于 `http://localhost:8080/frontend/index.html?test=1`：
- `test-board.js` — 飞轮 UI 抽屉（已有）
- `test-cases.js` — 用例定义 564 行 20 用例（已有）
- `test-board.css` — 飞轮样式（已有）
- `tests/reports/` — 12+ 份历史报告，最新 `report-2026-07-28-01-llm`

## 本次任务

CF-09 Bug 采集与飞轮扩建。按以下顺序执行：

### Step 1：接收 bug 报告
用户会逐一描述在实际使用中遇到的问题。对每个问题：

1. **诊断**：追踪根因（参考 CB-09 已有的 7 个根因分析报告）
2. **标准化**：将用户描述转为标准化用例格式（问句 + 数据前提 + 预期行为 + 断言）
3. **判断**：是新 bug 还是已知问题的复现
4. **写入 buglog**：按 `FLYWHEEL_PLAN_2026-07-29.md` §4.2 模板创建条目

### Step 2：同步飞轮用例
每个新 bug 确认后，追加到 `tests/emc_test_cases.md`

### Step 3：产出 CB 报告
所有 bug 处理完毕后，产出 CB-09 补充评估报告（SCAN 格式），放入 `docs/catch-ball/scan/`

## Bug 采集格式

每个 bug 使用以下模板写入 `tests/buglog/open/`：

```markdown
# B{NNN} · {标题}

| 字段 | 值 |
|------|------|
| **ID** | B{NNN} |
| **类型** |  |
| **严重度** |  |
| **来源** | 用户实测 · 2026-07-29 |
| **关联模块** |  |
| **状态** | 🔴 未解决 |
| **复现次数** |  |
| **最后复现** |  |

## 标准化用例
**问句**：
**数据前提**：
**预期行为**：
## 已知失败模式
| # | 日期 | 表现 | 根因 |
## 修复记录
| 日期 | 操作 | commit |
```

## 当前已知 Bug 清单（来自 CB-09·待入库）

| ID | 标题 | 类型 | 严重度 | 状态 |
|:---:|------|:---:|:---:|:---:|
| — | MC 字段重命名断裂 | 🐛 | 🔴 | 未解决 |
| — | 层引用幻觉（filter_attr） | 🐛 | 🔴 | 未解决 |
| — | finalStep 假结论 | 🐛 | 🔴 | 未解决 |
| — | 多要素提取推理螺旋 | ⚠️ | 🟠 | 未解决 |
| — | finalStep 超时 25s 过紧 | 🚀 | 🟠 | 未解决 |
| — | NL 追问 vs 胶囊路径差异 | ⚠️ | 🟡 | 未解决 |
| — | 流式代理断裂 | 🚀 | 🟡 | 部分修复 |

## 换机提示

如果在 VS Code（办公室）打开：读 `docs/catch-ball/_handoff/OFFICE.md`
如果在家（ZCode）：读 `docs/catch-ball/_handoff/HOME.md`
