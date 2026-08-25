# PT-CB15 · EMC 渲染链路治本收敛（Codex·2026-08-25）

> 输入：Codex 根因报告 + Kimi 复核意见 + Qoder 独立复核。
> 状态：收敛定稿。以下为最终采用方案，按优先级实施。

## 最终结论

幽灵图层有两条源头：①连接时 backlog 重放（已关）；②旧 turn 在收口后仍后台跑完并延迟写盘（未修）。必须两层都修。

## 采用方案

| 级 | 项 | 采纳方 |
|---|---|---|
| P0-A | `core/codex_bridge.py` 在超时/EOF/取消等非正常收口路径调用 `turn/interrupt`，从源头停掉旧 turn | Qoder |
| P0-B | SSE 连接首帧发 `event: hello`；前端拒收 hello 之前的 spec；删除 `_BACKLOG` 死代码与过时注释 | Qoder + Kimi |
| P1-B | 出图数据源软引导：render_spec 引用 `analysis_output`/`tmp_render_*`/`page7_*_topN` 时回显要素数与警示；`tmp_render_*` 不进 list_data；契约文档同步 | Qoder + Kimi |
| P2-A | `time-source.js` 对 404 静默降级（info 一次性），不补空 manifest；缺口登记 DATA/README | Qoder + Kimi |
| P2-B | /version 或自检端点补 repo_root / inbox / 8600 可达，前端徽标 title 显 mismatch（低优先） | Qoder + Kimi |

## 不采用

- spec 强绑 turn_id：Kimi 与 Qoder 均认为成本和脆弱性偏高；以 P0-A（interrupt）+ P0-B（hello 首帧）替代，turn_ref 作为后续可选软防线。
- 硬禁 `page7_*_top10` / `tmp_render_*`：误伤合法直陈展示流，改用软警示。
- 生成空 `_time_manifest.json`：会掩盖“清单从未生成”，改为前端降级 + 数据侧登记。
