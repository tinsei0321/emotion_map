---
description: 项目除草器 — 扫描/输入文件清单→判安全等级(绿/黄/红)→列清单等批准→删+入retired.md+调/sync-log。触发：除草/清理冗余/删无用文件/清缓存/weed/退役
argument-hint: "(可选) 文件/目录清单；省略则扫描孤儿文件/_前缀/过期plan/散落test 建议候选"
---

把"除草"从手动反复操作沉淀成统一流程：判等级 + 列清单 + 批准 + 留痕。复用 `/sync-log`（不重复同步逻辑）。退役台账 [docs/retired.md](docs/retired.md)。

## 安全等级（铁律）

| 等级 | 判定 | 处置 |
|---|---|---|
| 🟢 绿 | dev 截图 / 临时 py / `_` 前缀文件 / 孤儿 test / 过期 plan / 散落 test（不在 tests/）/ `__pycache__` | 直接删 |
| 🟡 黄 | 整层退役（如 apps/）/ 文档 / 疑似被引用 / 大目录 | 列清单等用户确认，grep 核查依赖后再删 |
| 🔴 红 | `core/tracker.py` / `.env` / API Key / `core/` 承重逻辑 / 配置 / 未批准项 / 任何不确定 | **不碰**，红色提示用户 |

## 步骤

1. **收集候选**：`$ARGUMENTS` 给了用清单；否则扫描建议——
   - 孤儿文件（根目录散落 .py/.png/.jpg 不在标准位置）
   - `_` 前缀文件（临时修复/废弃信号）
   - 过期 plan（根目录 `*_PLAN.md` / `REFACTOR_*.md`，对照 revision-log 看是否已被吸收）
   - 散落 test（`test_*.py` 在 SCRIPT/ 或根目录而非 tests/）
   - `__pycache__` 残留
2. **判等级**：逐项按上表标 🟢/🟡/🔴，🟡 项 grep `from <path>|import <name>` 核查引用方。
3. **列清单表**（等批准，**不在 auto-accept 下静默删**）：
   - 格式 `[等级] path — 理由（引用方 grep 结果）`
4. **批准后执行**：🟢 直接删；🟡 按用户确认删；🔴 跳过。
   - git rm（追踪）/ rm -rf（未追踪兜底）
5. **留痕**：追加 [docs/retired.md](docs/retired.md)（退役台账：日期 + 清单 + 理由）。不存在则创建（标题 + 表头）。
6. **同步日志**：调 `/sync-log`（revision-log §5 + todo + 告知"待你 push"）。

## 输出

```
[WEED] 候选 N 项（🟢 a / 🟡 b / 🔴 c）
  🟢 test_xxx.py — 根目录散落 test（应进 tests/）
  🟡 apps/ — 整层；grep 命中：仅文档引用（非代码依赖）
  🔴 core/tracker.py — 承重红线，不碰
批准后删除 M 项，retired.md 已更新。调 /sync-log 同步。
```

## 注意

- 删除红线：先列清单→用户批准→执行，**绝不静默删**（CLAUDE.md 红线操作）。
- 历史文档（dev-notes/todo 历史条目）保留事实，不删——只删"活规则"里失效引用，历史条目留痕。
- 批量删用 `git rm --ignore-unmatch`（容未追踪）+ `rm -rf` 兜底。
- 复用 `/sync-log`，不重复实现同步。
- 遵守 CLAUDE.md：结论先行、ASCII、中文、给推荐。手动触发，零被动开销。
