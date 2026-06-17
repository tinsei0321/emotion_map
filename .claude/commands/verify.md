---
description: 提交前验证门禁 — pytest + tracker 合规扫描 + trace 最近错误 + PII guard
argument-hint: "(可选) 只跑某一项: tests | compliance | trace | pii"
---

执行提交前验证（闭环补强 Wave2 的柔和门禁）。逐项跑，汇总 PASS/FAIL，**不自动 commit**。

参数 `$ARGUMENTS` 若指定单项则只跑那一项（tests/compliance/trace/pii），否则全跑。

## 步骤

1. **测试套件**（`tests`）：`py -m pytest tests/ -q` — 全绿才算过。
2. **追踪合规扫描**（`compliance`）：对核心管道文件跑合规报告，重点关注 `verdict=FAIL`：
   ```python
   from core.tracker import print_compliance_report
   for f in ["SCRIPT/data_governance.py","SCRIPT/emotion_analysis_v1.py",
             "SCRIPT/relevance_filter.py","core/coord_transform.py",
             "core/data_loader.py","core/export.py"]:
       print_compliance_report(f)
   ```
3. **trace 最近错误**（`trace`）：
   `py -c "from core.tracker import recent_errors; [print(e) for e in recent_errors(limit=20)]"`
   若有近期 `[ERR]`，列出供确认是否已知/已修。
4. **PII guard**（`pii`）：`py -m pytest tests/test_pii_guard.py -q`（文件存在才跑）。

## 输出格式

- 每项一行：`[OK] tests: 56 passed` 或 `[ERR] compliance: data_governance.py FAIL (3 untracked fn)`
- 末尾总结：`VERDICT: PASS`（可提交）或 `VERDICT: FAIL`（列出阻塞项）

遵守 CLAUDE.md：结论先行、ASCII 标记、不夸、安全打印。这是提交前的最后一道闸，本地门禁（比 CI 更可靠，因 GitHub 直连受限）。
