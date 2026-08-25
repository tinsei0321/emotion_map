# SOP 风险分级详表（自根 AGENTS.md 移出 · PT-CB18 W1-2）

> 根手册只留一句口径：任务按风险三档走流程（轻量/标准/严格），细则查本文。

## 风险分级（v2.1 | 2026-06-16）

| 等级 | 触发条件 | 流程 | 示例 |
|------|----------|------|------|
| **轻量** | 仅 UI/CSS/文案修改、单文件格式调整、注释修改 | Developer 直出 + Reviewer 快速扫（不 spawn Tester） | 改按钮颜色、调间距、修拼写 |
| **标准** | 涉及 2+ 文件、I/O 操作、函数签名修改 | Developer → Reviewer → Tester | 新增 API 端点、修改数据加载逻辑 |
| **严格** | 控制流修改（if/else/loop/try-except）、核心管道、追踪基础设施 | Developer → Reviewer → Tester → Reviewer 复审 | 修改 data_governance.py、tracker.py、分析算法 |

**严格模式附加要求：**
- 必须通过 `py -m pytest tests/ -q` 全部测试；
- 必须验证端到端管道（L0→L1→L2）不退化；
- 追踪 ID 变更必须在提交描述中列出。

## 触发条件详情

以下情况自动走**标准 SOP** 或以上：
- 新增或删除函数 / 类；
- 修改函数签名（参数 / 返回值）；
- **任何控制流逻辑修改（if/else/for/while/try-except）** → 严格；
- 涉及 I/O 操作（文件读写 / API 调用）；
- 涉及 2 个及以上文件；
- 修改 `core/tracker.py` 或追踪基础设施 → 严格。

## 何时跳过（直接执行）

- 仅修改注释 / 文档字符串；
- 变量 / 函数重命名（不改变签名）；
- 单文件内的格式化 / 代码风格调整；
- 修复明显的拼写错误。

## 按角色推荐阅读（知识源分工）

| 角色 | 必读 | 选读 |
|------|------|------|
| Developer | `docs/spec.md`, `docs/architecture-pattern.md`, `core/tracker.py` | `docs/decisions.md`, `docs/dev-notes.md` |
| Reviewer | `docs/spec.md`, `docs/architecture-pattern.md`, `core/tracker.py` | `docs/decisions.md`, `docs/catch-ball/RULES.md` |
| Tester | `docs/spec.md`, `docs/architecture-pattern.md` | `core/tracker.py`, `docs/dev-notes.md` |
| Data | `docs/spec.md`（数据管道章节）, `docs/architecture-pattern.md` | `docs/decisions.md` |
| GIS Dev | `docs/spec.md`（坐标规范章节）, `docs/architecture-pattern.md` | `core/tracker.py` |
| Designer | `docs/spec.md`（UI 组件章节）, `design/tokens.css` | — |
| Docs | `docs/architecture-pattern.md`, `docs/decisions.md` | `docs/dev-notes.md`, `core/tracker.py`, `docs/catch-ball/RULES.md` |
| Ops | `requirements.txt`, `docs/spec.md`（依赖章节） | — |
