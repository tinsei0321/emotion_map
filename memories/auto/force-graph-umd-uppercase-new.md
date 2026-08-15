---
name: force-graph-umd-uppercase-new
description: force-graph(vasturiano) UMD 全局名是 ForceGraph(大写F)+需 new ForceGraph(el)；CDN // 协议相对在 http 页降级被 jsdelivr 拒→vendor 本地
metadata: 
  node_type: memory
  type: reference
  originSessionId: 55f1a39e-28ad-4e5e-b338-c25238e13432
---

用 force-graph（vasturiano，Obsidian graph view 同款 d3-force + Canvas）做交互拓扑图时的三大非显然坑（Playwright 实测踩过，每个都静默失败无报错，诊断成本高）：

1. **UMD 全局名是 `ForceGraph`（大写 F）**，不是小写 `forceGraph`。验证：`typeof ForceGraph === 'function'`，`typeof forceGraph === 'undefined'`。很多博客/Agent 报告误写小写。

2. **必须 `new ForceGraph(el)`（带 new）**。无 new 的 `ForceGraph(el)` 返回的是 connector function 而非图实例——**静默不创建 canvas、console 0 error**，container 一直空（`el.children.length === 0`）。诊断信号：`typeof ForceGraph` 是 function、`.graphData()` 方法存在、但容器无 canvas 子节点。替代写法：`ForceGraph()(el)` 两次调用也行。

3. **CDN `<script src="//cdn.jsdelivr.net/...">` 的协议相对 `//` 在 `http://localhost` 页面会降级成 `http://cdn.jsdelivr.net`**，被 jsdelivr 强制 https 拒（脚本 403/加载失败、ForceGraph undefined、仍无 console error）。**改用明确 `https://` 或 vendor 本地**。本项目 vendor 到 `frontend/vendor/force-graph.min.js`（curl 从 jsdelivr 下，1.51.0, 173KB）。

**Why**：force-graph 是 Obsidian graph view 的 1:1 OSS 复刻（d3-force + Canvas），vanilla JS + CDN 友好，做"项目架构/依赖拓扑可视化"的首选。但这三个坑都不报错，靠 Playwright `evaluate` 查 `typeof ForceGraph` / `el.children.length` / canvas 存在性才能定位。

**How to apply**：本项目落地见 `core/topo_scanner.py`（build_topology 实时扫）+ `frontend/topology.html`/`topo.css`/`topology.js` + `frontend/vendor/force-graph.min.js` + `api/topo_routes.py`（GET /api/v1/topo），revision-log 5.122。下次用 force-graph（或同 vasturiano 系 3d-force-graph）直接 `new ForceGraph(el)` + vendor 本地，跳过这三个坑。
