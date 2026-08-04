# CB-16 全局优化 + backlog 收尾 实施后检查（Codex / glm组 · 2026-08-04）

> **用途**：claude组 已按 ③w2 预检反评价实施（validate drift 修复 + renewal 门控 + 全局优化 4 子项·时间轴剥离）。请两组**核验实施** + **分析 B3 快照回归（RST-L06）**。
> **登记**：docs/context-map.md · cb-journal CB-16 ③w3。

---

【CB-16 全局优化 + backlog 收尾 实施后检查（Codex / glm组）】

背景：③w2 预检两组通过（Codex P1×3 + glm 注意项·全纳入）。claude组 实施（时间轴剥离·用户定后置专题）。请核验实施 + 分析 B3 快照发现。

第一步 · 读本地文件（同一工作区·**无需 git pull/push**·直接读）
- 实施依据：`ai_qa/paradigm.py`（`_sync_geo_catalog_guard_fields` 新增）· `ai_qa/outlet_kb/build_outlet_schema.py`（renewal domain 门控）· `tests/test_outlet_schema.py`（+renewal 门控测试）· `docs/decisions.md`（ADR-017~019）· `docs/todo.md` + `docs/todo-archive/2026-07-27_2026-08-02.md`（周归档）· CLAUDE.md（当前开发状态 5 行）
- B3 快照：`tests/reports/report-2026-08-04-01-llm.md` + `tests/browser/out/audit-B3-210952.json`

第二步 · 核验已实施内容

① **validate_skill_params drift 修复**（Codex P1 建议·glm P0）
- `paradigm.py` 加 `_sync_geo_catalog_guard_fields()`：导入时用 `derive_geo_catalog()` 派生值对齐 GEO_TOOL_CATALOG 的 when/params/yields/contributes 4 字段（scale/preconditions/failure_modes/examples 保留手写·不在 guard 范围）
- 结果：`py -m pytest tests/validate_skill_params.py -q` → **4 passed**（原 1 failed）

② **renewal 卡 perceptible_metrics domain 门控**（③z3 已知 backlog）
- `build_outlet_schema.py _build_card`：仅 `domain == 'urban_governance'`（体检域）计算 perceptible_metrics·renewal 卡不混挂
- +测试 `test_wave3_renewal_no_perceptible_gate`

③ **全局优化**（④w2 子项 1）
- CLAUDE.md「当前开发状态」5 行（L3✅·L4🔄·空间✅·UI✅·L0→L1 补 sim·Codex P1 修正 L4 🔄）
- todo 周归档：新建 `todo-archive/2026-07-27_2026-08-02.md`（302 行）+ 删重复节
- decisions.md 补 ADR-017~019（Streamlit 退役 / EMC v2/v3 FC 转型 / 出口抽象层）+ 索引 + CLAUDE.md「19 个 ADR」
- 记忆 GC（extrusion 索引合并·删 commit-only-user-pushes·global-time-axis/batch4 标「已实现·manifest 404 待修复」）

**B3 快照回归（需两组分析）**：
- B3 26 例 pass=22 fail=4（84.6%·**低于基线 88.5%**）·elapsed 9.6min
- **RST-L06 明确回归**（多步「先裁剪再热力图」）：旧 PASS（clip+density·1→2层）→ 本次 FAIL（tools= 空·clip 1→0层）
- **claude组 根因假设**：paradigm density.when 同步成 contracts 值（加了 `CB-12 P2：方格/网格聚合...→ mode=3d`）——改动前后**唯一 LLM 可见差异**·LLM 读到新 density 描述可能影响「热力图」第二步路由。**需实证 + 两组独立判断**。
- 其他 fail：PRM-03/04（buffer radius[ERR]）·PRM-07（zonal 边界·应 request_upload）——已知 backlog 非本次引入

请核验：
1. **validate drift 修复**：`_sync_geo_catalog_guard_fields` 导入时 patch 思路对路？会不会影响 diagnose prompt（eval 红线）？有无副作用（如多次 import 重复 patch）？
2. **RST-L06 回归根因**：claude组 假设（density.when 文本变化）对吗？还是其他原因？paradigm 同步是否该保留（若证实引发回归）？还是该改回手写 + 只修 validate？
3. **renewal 门控**：domain==urban_governance 判断正确？会不会漏掉应挂体检指标的卡？
4. **全局优化**：ADR-017~019 内容准确？todo 归档无遗漏？记忆 GC（删 push 记忆·标 global-time-axis/batch4）合理？
5. **B3 其他 fail**：PRM-03/04/07 是否确认为既有 backlog 非本次引入？
6. **tracklog**：B3-snapshot-0804 会话 trace 取证（F_002/pro/timeout）应补齐——claude组 待分类器恢复后跑
7. **承重零触碰**：diagnose/harness/ChatRequest 不动？paradigm 同步是否影响 eval？

第四步 · 产出简短 SCAN 落 docs/catch-ball/scan/CB16-GlobalOptimize检查-*_2026-08-04.md
- 判定：实施是否通过·RST-L06 回归根因 + 修法（P0/P1/P2）
- 独立判断·不要互相参考对方报告

规则：只读评估·禁改代码/禁 commit·结论先行。

---

*本请求由 claude组 发起（2026-08-04）·CB-16 全局优化实施后检查 + B3 快照回归分析。*
