# Bug 条目模板（复制本文件到 open/ 或 resolved/ 后填写）

> **纪律**：本文件只放「摘要 + 指针」。详细根因分析放 `docs/catch-ball/rootcause/`，
> 本文件用 `rootcause:` 字段指向它。单条目控制在 ~25 行以内（DeepSeek 意见 1）。
>
> **标签全 ASCII**（编码规范 1·禁 emoji）：type/severity/status/module 均用下方枚举。
>
> **命名**：`B{NNN}-{slug}.md`（NNN 连续不跳号；slug 英文短横）。
> 新建前先跑 `py tests/buglog/_gen_index.py`，脚本会打印 next_id。

---

复制下方 frontmatter + 章节，删除本说明段：

```markdown
---
id: B000
title: 一句话标题（现象 + 触发点）
type: BUG            # BUG | DEGRAD（降智/错答）| PERF | UI
severity: HIGH        # CRIT | HIGH | MED | LOW
priority: ''          # P0 | P1 | P2（CB 评估优先级·无则留空）
status: open         # open | resolved
module: 数据识别       # 数据识别 | 工具调用 | finalStep | FC诊断 | UI
source: 用户实测      # 用户实测 | CB诊断 | 飞轮发现
cb: ''               # 关联 CB 轮次（如 CB-09），无则留空字符串
rootcause: ''        # 指向 docs/catch-ball/rootcause/<file>.md，无则留空
case_ref: ''         # 关联飞轮用例（TC-NN 目录 ID 或模式描述）；runtime 用例 ID 见 rootcause
repro_count: 1       # 累计复现次数（每次再现 +1）
last_repro: ''       # 最近一次复现日期 YYYY-MM-DD
---

## 标准化用例

**问句**：「用户原始中文问句」

**数据前提**：需要的图层/字段/范围

**预期行为**：
① ...
② ...

## 已知失败模式

| # | 日期 | 表现 | 根因 |
|:-:|------|------|------|
| 1 | MM-DD | ... | ... |

## 修复记录

| 日期 | 操作 | commit |
|------|------|--------|
| - | 待修复 | - |
```

填写完跑 `py tests/buglog/_gen_index.py` 刷新 `tests/buglog/_index.md` 与 `_trend.md`。
