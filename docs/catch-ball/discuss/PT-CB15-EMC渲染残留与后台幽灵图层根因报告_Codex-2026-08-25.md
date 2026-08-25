# PT-CB15 · EMC 渲染残留与后台幽灵图层根因报告（Codex·2026-08-25）

## 白话摘要

页面一打开就“自己长出”上次测试的图层，原因是后端在浏览器一连接时就把“最近一张图”主动重放了一遍。于是你硬刷新后，旧图又被推回来；如果后台还有延迟完成的上一个问题，也会突然再冒出来。这个重放逻辑我已经关掉，并重启了后端。另一个问题是模型在回答“7 个社区”时，可能错误地选了“TOP10”预设图层去出图，所以内容也对不上。

## 根因

1. **SSE backlog 重放**：`api/render_routes.py` 的 `_sse_stream()` 在每次新连接时 `yield _sse_event(_BACKLOG[-1])`，把上次消费过的 spec 重新推给前端。硬刷新 = 新连接 = 旧图复活。
2. **旧进程未重启**：前端/后端在旧代码上运行，导致修复未生效。
3. **模型选错出图数据源**：问题要“TOP7”，模型却调用 `render_spec(dataset_id='page7_12345_top10')` 或 `tmp_render_...`，产出“TOP10/全量174”图层；文本回答对了，但图不对。
4. **次要噪音**：`time-source.js` 请求 `/DATA/performance/_time_manifest.json` 返回 404；该 manifest 当前缺失，属于数据资产缺口，不阻塞渲染但污染控制台。

## 已修复

- 移除 `_sse_stream` 连接时的 backlog 重放；页面刷新不再自动恢复旧图。
- 重启 8000/8080 后端，确保最新代码生效。
- `?test=1` 自动清空 chat 历史/归档（此前已改）。
- EMC 默认仅 Codex Harness（此前已改）。

## 待 kimi / qoder 联合修复

1. 出图数据源收敛：模型必须用本轮计算出的 TOP7 内联 GeoJSON 调 `render_spec`，禁止随手挑 `page7_*_top10` / `tmp_render_*` 预设。是否需要在 AGENTS.md / tool_contracts 中把 `render_spec` 参数约束得更死？
2. 后台任务幽灵图层：是否存在 render_spec 在 turn 结束后仍被 watcher 延迟推送的竞态？是否应给 spec 加 turn_id，前端只接受当前 turn 的 spec？
3. `_time_manifest.json` 缺失：由谁生成、是否应随 data 资产补一份最小 manifest，或让 time-source 优雅降级不报 404。
4. 启动到结束的链路自检：是否应增加一条“连接时不重放 + 版本自检 + 三服务路径一致性”的统一 health/自检。
