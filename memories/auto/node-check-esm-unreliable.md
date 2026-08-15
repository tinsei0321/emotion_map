---
name: node-check-esm-unreliable
description: node --check 对 .js 默认 CommonJS 不报 ESM 语法错；前端 JS 须 .mjs 副本或 --input-type=module 检查
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37d07713-df9f-4427-92af-e27b871d6574
  modified: 2026-07-27T12:10:11.038Z
---

`node --check file.js` 对含 `import`/`export` 的 ES module 文件**默认按 CommonJS 检查，宽容不报语法错**（括号不匹配、某些 ESM 严格语法都不报）。浏览器 `<script type="module">` 按 ESM 严格 parse 才暴露。

**Why**（5.84 hotfix）：5.82 P3 改 buildContext（async + Promise.all）少一个 `)`，`node --check tools.js` 默许通过，但浏览器报 `Unexpected token ';'`，致整个 ai_qa 模块链加载失败、前端半崩（地图不出 + 按钮不可点），潜伏一个版本到 5.83 用户验证时才暴露。

**How to apply**：前端 ES module JS 验证语法用**任一**：① `cp x.js /tmp/x.mjs && node --check /tmp/x.mjs`（.mjs 强制 ESM）；② `node --input-type=module --check < x.js`。提交前全量 `find frontend/js -name '*.js'` 转 .mjs 扫一遍。**不要只信 `node --check x.js`**（它对 ESM 假绿）。同类「工具宽容致 bug 潜伏」见 [[sandbox-eval-wrapper-context-restore]]。

**⚠️ 本环境 node 不在 PATH**（CB-09 5.232 验：`which node`/`command -v node` 全空·项目是 Python 3.14 + 静态前端 JS 经 `frontend/serve.py` serve·node 非依赖）。上述 node --check 方案在此机跑不了 → JS 语法验证退化为：① 精确手工 Edit 对账（old/new 串严匹配）+ 承重大块改完 Read 一遍最终态；② `py frontend/serve.py 8080` 起服务冒烟（验 serve.py + 后端 boot 无 Py 错·文件可服务）；③ JS 执行级错误交用户肉眼浏览器验（同 [[no-routine-playwright-verify]]·不日常上 Playwright）。勿再试 `node --check`（command not found 浪费调用）。
