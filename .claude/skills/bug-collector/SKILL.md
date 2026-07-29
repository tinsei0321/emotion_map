---
name: bug-collector
description: 把用户描述的 bug / CB 诊断发现 / 飞轮失败，标准化成 tests/buglog/ 条目并刷新索引。触发：用户说"记录这个bug/加入飞轮/这个问题反复出现/写进buglog"，或在 CB/飞轮复盘时要把某个失败沉淀成长期追踪项。只做"捕获 + 标准化 + 落盘 + 刷索引"，不做自动监听（SKILL 无法监听外部事件）。
---

# Bug Collector — 飞轮 Bug 采集 Skill

## 角色定位（Smart Agent, Dumb Tool 内核）

- **Smart（本 skill）**= 出口端标准化：把自然语言 bug 描述，转成结构化用例条目（问句/数据前提/预期/失败模式）。这是 LLM 擅长的"理解 + 表达"。
- **Dumb（脚本）**= `tests/buglog/_gen_index.py`：算索引、`--check` CI 守护。确定性、不调 LLM。**索引永远由脚本算，skill 不手写 `_index.md/_trend.md`。**
- 编排 = 本 skill 工作流（机械接线：标准化 → 落盘 → 调脚本）。

## 触发条件（仅手动）

SKILL.md 只能按用户输入触发，**不能监听文件/外部流程**。故自动场景须人工喊一声：

- 用户说「记录这个 bug / 加入飞轮 / 这个问题反复出现 / 写进 buglog」
- CB 复盘时：用户指着某条 CB 发现说「这个进 buglog」
- 飞轮复盘时：用户指着某次失败说「这个记下来」

> 不要在 CB 报告产出/飞轮失败时"自动触发"——那是 hook 的职责，不是 skill 的。

## 输入

用户提供（可缺，缺则问）：
- 问题描述（自然语言）
- 复现步骤（可选）
- 预期行为（可选）
- 关联信息：CB 轮次 / 根因报告路径 / 飞轮用例 TC-NN（可选）

## 工作流

### Step 1 · 取 next_id

跑 `py tests/buglog/_gen_index.py`，读末行 `next_id = BNNN`（连续不跳号）。

### Step 2 · 标准化（Smart·LLM 推理）

把原始描述转成（参考 `tests/buglog/_template.md`）：

- **问句**：保留用户原始中文（加注英文关键词）
- **数据前提**：明确需要的图层/字段/范围
- **预期行为**：用「① ② ③」编号
- **已知失败模式**：若反复出现，列各次表现 + 根因（引用根因报告路径）

### Step 3 · 分类（ASCII 枚举·禁 emoji）

| 字段 | 枚举 |
|------|------|
| `type` | `BUG`（功能错）/ `DEGRAD`（降智·错答·编造）/ `PERF`（性能）/ `UI` |
| `severity` | `CRIT` / `HIGH` / `MED` / `LOW` |
| `status` | `open`（未解决）/ `resolved`（已修复） |
| `module` | `数据识别` / `工具调用` / `finalStep` / `FC诊断` / `UI` |
| `source` | `用户实测` / `CB诊断` / `飞轮发现` |

> 编码规范 1：全 ASCII 标签，禁 emoji。展示时由前端/脚本加 `[ ]`（如 `[BUG][HIGH]`）。

### Step 4 · 落盘

- 复制 `tests/buglog/_template.md` → `tests/buglog/{open|resolved}/B{NNN}-{slug}.md`
- 填 frontmatter（YAML）+ 三个章节
- **纪律：条目只放摘要 + 指针，≤25 行。详细根因留 `docs/catch-ball/rootcause/`，`rootcause:` 字段指向它。**
- 跨链防孤岛：填 `cb:` / `case_ref:` / `rootcause:`（CLAUDE.md「记忆共享通则」）

### Step 5 · 刷索引（Dumb·委托脚本）

跑 `py tests/buglog/_gen_index.py` → 重生 `_index.md` + `_trend.md`。
确认末行 `[OK]` 且 `--check` 通过。

## recurring（复发）处理

- `repro_count` ≥ 2 → 脚本自动收入 `_trend.md`（历史复发趋势）。
- 同一 bug 再现：**不新建条目**，找到原条目 → `repro_count + 1` + `last_repro` 更新 + 「已知失败模式」加一行 → 重跑脚本。
- 状态从 open→resolved：移动文件 `open/`→`resolved/` + `status: resolved` + 补「修复记录」 → 重跑脚本。

## 边界 / 不做

- **不自动监听** CB 报告/飞轮事件（须 hook，非 skill 职责）。
- **不写根因正文**（留 rootcause/）。
- **不手维护 `_index.md/_trend.md`**（脚本算）。
- **不造数据**：status/severity 据实填，不臆测「自动修复」。

## 范例（见 B001）

`tests/buglog/resolved/B001-multi-extract-field-rename.md` —— CB-09 多要素裁剪螺旋，
4 次复现、M1/M2/M3 修复、根因指针 rootcause/2026-07-28-multi-extract-reasoning-spiral.md。
新建条目可照此结构。
