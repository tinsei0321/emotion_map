# 运维手册（回滚 / 换机 / 数据目录指针）（自根 AGENTS.md 移出 · PT-CB18 W1-2）

## 紧急回滚流程

```
发现问题 → 判断严重程度
              ↙           ↘
          紧急回滚        标准修复
           ↓                ↓
     git revert          走 SOP 流程
     + Tester 验证       (开发 → 审查 → 测试)
     + Reviewer 快速审
```

> 紧急回滚标准：系统无法启动、核心功能崩溃、数据损坏。

## 跨机协作（办公室 ↔ 家里）

**新流程（PT-CB18 W1-1 起）**：
- 换机启动 = 读仓根 `STATE.md`（机器骨架 `py tools/gen_state.py` 可重建）+ 对应换机交接卡
  （`docs/catch-ball/_handoff/HOME.md` / `OFFICE.md`，环境事实仍归卡）+ 本次任务书；
- 阶段交接 = `STATE.md` 手写区按 `docs/state-handoff-template.md` 八字段；
- 下班交接 = 更新换机卡 + `STATE.md` + git commit（push 由用户执行）。

**旧流程（冻结留痕）**：原「同步上下文」读 `memories/repo/session-handoff.md`、
「下班交接」更新该卡——该卡已于 2026-08-26 冻结（只读历史参考，观察一阶段后退役）。

**同步原理**：
| 同步方式 | 内容 |
|----------|------|
| **Git** | 代码 + docs/ + requirements.txt + 生成器（STATE/GLOSSARY 为生成物，两机各自重建） |
| **pip** | `pip install -r requirements.txt`（ops 自检） |

## 数据目录与 RAG 规则（2026-08-25 重构）

> 权威入口：`DATA/README.md`；全组通知：`docs/catch-ball/discuss/PT-CB15-数据目录与代码映射重构_全组通知_Codex-2026-08-25.md`。

- 预设/上传一律走 `DATA/REGISTRY/presets/`；权威数据读 `DATA/AUTHORITY/`；专题读 `DATA/THEME/`；导出读/写 `DATA/Export/`。
- `DATA/boundaries` 与顶层 `DATA/exports` 已退休/删除，禁止再引用。
- RAG 索引位于 `DATA/RAG/rag_index/`，重建命令 `py tools/rag_index.py --build`；episode 记录位于 `DATA/RAG/ai_qa/`。
- 用地数据、建成区数据：禁止入库/RAG；仅用户一次性上传，不落盘。
- 同名多格式文件：`.csv` 副格式统一放 `DATA/others/`，代码优先读 GeoJSON。
