---
name: verify-real-endpoint
description: 验证要测实际业务端点（POST+数据），不能只 health/页面加载就判通
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 22e972fb-64fe-47c3-bbb5-efd0c7d69068
---

验证后端/接口/反代时，必须测**实际业务端点**（POST + 真实 payload，看响应 JSON），不能只 curl `/health`（通）或看页面加载（无报错）就判定"通了"。

**Why:** 用户两次遇到"我说修好了但实际没好"——第一次只验证前端加载没测后端 API；第二次只 curl health（旧后端 health 也通）没测 `/spatial/grid`，漏掉旧后端缺路由的 404。**health 通 ≠ 业务端点通；进程活着 ≠ 路由/逻辑正确。**

**How to apply:** 改后端/serve.py/反代后，curl POST 实际端点带样例 payload + 看响应；前端改动用 Playwright 实际点按钮触发 fetch + 看 network/console，不只看 DOM 属性。复用旧进程要警惕（health 通但代码旧/路由缺）——serve.py `_spawn_backend` 强制重起就是这个教训。关联 [[select-cascade-progressive]]。
