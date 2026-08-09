# DeepSeek Onboarding — Emotion Map EMC 修复工程

> **给你**：你是 Claude Code + DeepSeek V4，接手这个项目的 EMC 修复工程。
> **当前分支**：`fix/emc-buglog`，commit `7126f6d`。代码纯净，今天改动已全量回退。
> **完整 Session 记录**：`docs/catch-ball/_handoff/SESSION_2026-07-30.md`
> **CB 入口**：`docs/catch-ball/_cb-index.md`

---

## 一、项目是什么

**Emotion Map（情绪地图）** — 把居民在社交媒体/12345 等平台表达的情感（开心、愤怒、抱怨）精准定位到地图上，构建城市"心情"可视化分析工具。

技术栈：Python 后端（FastAPI）+ MapLibre GL JS 前端 + DeepSeek V4 LLM。

### 架构
```
L0 数据采集 → L1 数据治理 → L2 情绪分析 → L3 归因 → L4 深度归因
                                  ↓
                          frontend/（MapLibre GL JS）
                          ai_qa/   （LLM Agent 问答系统 = EMC）
                          api/     （Geo 工具后端）
```

### EMC（你要修的部分）
EMC 是嵌入前端的 LLM Agent 对话系统。用户用自然语言提 GIS/情绪分析需求，Agent 自动选工具→执行→出结论。

**内核**：Smart Agent / Dumb Tool
```
用户提问 → FC 诊断（Flash LLM 选工具）→ 编排器（代码执行）→ 工具集（纯参数化）→ 结论
              ↓ 失败时回退
         旧 SSE 诊断（rule-based 预选工具·不可靠）
```

---

## 二、当前聚焦：修复工程

### ✅ 已修复（当前版本 7126f6d 包含，不要动）
1. **"只说不做"** — Agent 口头说"已生成图层"但实际没生成 → 工具观测诚实化 + 零图层守护（harness.js `runAllToolCalls`）
2. **overlay union 后端崩溃** — geopandas 重复列名 → `api/geo_routes.py` 列重命名 `_a/_b` 后缀
3. **clip vs overlay 工具选错** — `tool_contracts.py` clip.when="❌仅点层" + FC prompt 明确"面层→overlay"
4. **e2e 图层命名混淆** — `e2e-seam.js` group 改名
5. **回到底部按钮 UI** — CSS 毛玻璃 + '↓'

### 🔴 仍存在的问题（需要你修）

**P0：FC 诊断偶尔 no_tool_calls → 回退旧 SSE → 彻底失败**
- 现象：FC 诊断（Flash function calling）偶发不产出 tool_call → 回退到旧 SSE 诊断 → 旧路径用 `select_candidates` 预选工具常选错 → 查询完全失败（用户看到"这次没跑通——我没能生成可用的图层"）
- 测试用例：提问"剪裁出西陵区范围内的商业+居住+公园广场用地"
- 关键位置：
  - `ai_qa/router.py:38-44`（FC prompt，4 行版）
  - `frontend/js/ai_qa/stages.js:293-348`（`fcDiagnoseStep`）
  - `frontend/js/ai_qa/harness.js:794-806`（FC→旧 SSE 回退逻辑）
- 当前 FC prompt（别乱动——这是多轮回归验证的最稳定版本）：
  ```
  你是情绪地图分析助手。根据用户请求选择最合适的工具。
  - 用户说"裁剪/剪裁"面层→用 overlay(intersection)。clip 仅用于点数据
  - 多步骤请求→先做第一步，系统自动补全后续
  - 参数用数据上下文中的实际字段名和图层 ID
  ```

**P1：Pro 模式不生效**
- 现象：用户选 Pro 但 finalStep 结论仍用 Flash 生成
- 根因：`harness.js:741` `ctx.answerModel = 'flash'` 硬编码
- 修复：改为 `ctx.answerModel = ctx.model || 'flash'`（在 `orchestrate` 函数入口）
- ⚠️ FC 诊断必须永 Flash！不要改——Pro 做工具选择已证明会过度思考（76+ 行 reasoning 后丢失 tool_call）

**P1：多步骤合并只能 2/3**
- 现象：提问"合并3个图层"只完成 2 个
- 根因：FC 诊断只产 1 个 tool_call → 1 次 overlay 只处理 2 层。`_autoExpandOverlays`（harness.js:1130）只检测"X区内Y1+Y2+…用地"裁剪模式，不处理合并模式
- 修复方向：扩展 `_autoExpandOverlays` 支持 `how='union'` 多目标模式

**P2：方案 A Planner 值得继续**
- 后端已验证：Pro 正确输出 4 步 JSON 执行计划
- 遗留 bug：① Planner 输出 `where="MC='西陵区'"`，`normPreFilter`（tools.js:227）只认 `/` 分隔格式 ② 前端缓存
- 代码在 reflog 中（`299b0e2` 之后的几个 commit），可 cherry-pick

---

## 三、关键文件地图

| 文件 | 作用 | ⚠️ 注意 |
|------|------|---------|
| `ai_qa/router.py` | 后端路由：FC 诊断 + SSE 各阶段分流 | FC prompt 在第 38-44 行 |
| `ai_qa/prompts.py` | Agent/Answer/Diagnose prompt 模板 | diagnose prompt 永不动（eval anchor） |
| `ai_qa/llm.py` | LLM 客户端 + provider fallback 链 | `_tier_of()` 模型名→tier 映射 |
| `ai_qa/tool_contracts.py` | 13 个工具契约（单一权威源） | clip.when 已改为"❌仅点层" |
| `ai_qa/schemas.py` | ChatRequest Pydantic schema | phase 字段定义 |
| `frontend/js/ai_qa/harness.js` | **编排器（最复杂·约 1200 行）** | `orchestrate()` 入口、`_autoExpandOverlays`、`runAllToolCalls` |
| `frontend/js/ai_qa/stages.js` | 各阶段函数 | `fcDiagnoseStep`、`diagnoseStep`（旧 SSE）、`agentStep`、`finalStep` |
| `frontend/js/ai_qa/tools.js` | 13 工具实现 + `ref()` + `normPreFilter()` | `ref()` 按名称/ID/$n 查找图层 |
| `frontend/js/ai_qa/panel.js` | 对话面板 UI + `_thinkMode` | Pro/Flash 按钮切换 |
| `frontend/js/ai_qa/api.js` | SSE 流式通信 | 不动 |
| `frontend/js/state.js` | 图层状态管理 | `setLayerVisible`、`getLayer` |
| `api/geo_routes.py` | Geo 工具后端 | overlay 列重命名修复在此 |

---

## 四、铁律（违反会导致回归）

1. **改 JS 后硬刷新浏览器**（Ctrl+Shift+R）— 浏览器缓存是今天最大时间陷阱
2. **FC 诊断永 Flash** — Pro 做工具选择 = 过度思考 → no_tool_calls → 回退失败
3. **改 FC prompt 要回归测试** "剪裁西陵区3类用地" — 最敏感用例
4. **所有 print() 必须用 `_safe_print()`**
5. **代码禁用 emoji** — 只用 `[OK] [WARN] [ERR]`
6. **追踪 ID 必注册** — 新函数加 `@track()` + `register_track_id()`
7. **讨论结果必须同步落盘到记录文档**（AGENTS.md 铁律）

---

## 五、环境

```bash
# 启动
python frontend/serve.py 8080    # 前端 8080 + 后端 8000，Ctrl+C 同停

# API
POST http://localhost:8000/api/v1/chat

# 测试数据
浏览器加载 e2e-seam.js 测试数据组（?e2e=1 参数）
```

---

## 六、回归测试用例

```
# P0 验证
剪裁出西陵区范围内的商业+居住+公园广场用地

# P1 验证
合并商业、居住和公园广场用地

# 基准（不应退化）
西陵区在哪里？
对比西陵区和伍家岗区的情绪
分析西陵区的消极情绪热力图
```
