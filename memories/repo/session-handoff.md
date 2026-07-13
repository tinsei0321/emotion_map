# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月13日（5.84 hotfix 收工）| 分支 `main`（**本地领先 origin 11 commit 待用户手动 push**）| 本次会话 = 5.83（沙箱挂 /run + 三道底线加固）+ 5.84（buildContext 括号 hotfix）

---

## 当前节点：5.84 沙箱 /run 已挂 + buildContext 括号 hotfix，下会话验 run_python 端到端或换主线

### 背景
字段语义层 P1-P3（5.80-5.82）收完后挂 /run（让 EMC 的 AI 助手自写 Python 跑数据分析、matplotlib 出图，geo 工具覆盖不到时的兜底，第 15 工具 run_python）。沙箱原 `SAFE_READY=False`，三道文档化硬缺口（open 不拦 / 反射绕过 / CORS 全开）。用户拍板「演示版+底线加固」，补三道底线后切 `SAFE_READY=True` 挂 /run，**不做 Job Object 硬限**（内存/CPU 仅超时软限），定位本地单机演示。挂 /run 验证时发现 5.82 遗留的 buildContext 括号 bug（前端半崩），hotfix 修复。

### ✅ 本会话已做（5.83 沙箱 + 5.84 hotfix）
- **5.83 沙箱挂 /run + 三道底线加固**（commit `3050f3a`）：
  - 加固①open-wrapper（[api/sandbox.py](api/sandbox.py) PRELUDE §2.5）：写必查 workdir 白名单 / 用户帧读查 / 库帧读放行；realpath+abspath 防 `..` 和 symlink 逃逸。
  - 加固②AST 反射审查（`_check_reflection` / `_ReflectionVisitor`）：4 类 dunder 反射静态拦；残余别名/IfExp 靠禁 eval/exec 兜底。
  - 加固②frame-based eval（关键 bug）：全禁误伤 matplotlib/pandas/numpy.f2py；降级 frame-based（用户帧禁/库帧放行）。**核心坑**：wrapper 须补 globals/locals=真正调用帧还原默认语义（仅调用者完全用默认时），否则 numpy.f2py NameError + importlib future ImportError（记 memory `sandbox-eval-wrapper-context-restore`）。
  - 加固③CORS 收紧（[api/main.py](api/main.py)）：`allow_origin_regex` 本机 + `allow_credentials` 关（serve.py 反代同源不破现有）。
  - `MPLCONFIGDIR=workdir/.mpl` 避 matplotlib 字体缓存写被拦误伤。
  - `SAFE_READY=True` + 新建 [api/run_routes.py](api/run_routes.py)（POST /run + `_encode_images` figId=`fig{n}` 纯 ASCII）+ main.py `if SAFE_READY` 条件挂载。
  - 前端 [frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js) run_python 工具（第 15）+ `_figCache`/`getFig`/`clearFigCache` + `fetchRun`（**不调 addResultLayer**，observation 用「图片」避 5.74 对账）；[frontend/js/ai_qa/panel.js](frontend/js/ai_qa/panel.js) `_renderFigs`（`{{fig:ID}}`→`<img>`，照 `_renderCharts`）；[ai_qa/paradigm.py](ai_qa/paradigm.py) `CODE_EXEC_CATALOG` + [ai_qa/prompts.py](ai_qa/prompts.py) run_python schema 行（花括号双写避 .format 冲突）+ build_agent_prompt 拼 catalog。
  - [tests/test_sandbox.py](tests/test_sandbox.py) +9 加固测试。
- **5.84 hotfix buildContext 括号**（commit `cc54e17` 代码 + `8526f41` 日志）：5.82 P3 改 buildContext（async + Promise.all）少一个 `)`（[tools.js:431](frontend/js/ai_qa/tools.js)），`node --check` 默认 CommonJS 宽容未报，浏览器 ESM 严格报 `Unexpected token ';'`，致整个 ai_qa 模块链加载失败 → buildContext 崩 → main.js 初始化中断 → **地图加载不出 + Range/Layers 按钮不可点**。`}))` → `})))` 修复。教训：node --check 对 ESM 不可靠，须 .mjs 副本（记 memory `node-check-esm-unreliable`）。

### 🔍 验证（已过）
- **静态全过**：`.mjs` ESM 全量扫描 frontend/js 全过（5.84 后）+ py_compile 后端全过。
- **沙箱 28 passed**（19 旧 + 9 新：反射 4 + open-wrapper 2 + frame-based eval 3）。eval locals 修复后全绿。
- **/run 端点真调**：matplotlib 出图→fig1+dataUri / 反射端点级拦 / data_refs 注入 rows 2。
- **openapi 确认 /api/v1/run 挂载**（total 34 paths 现有路由全在）。
- **Playwright 重载 0 errors**（5.84 修复后，原 2 errors）+ buildContext OK（4206 chars）+ maplibre 容器初始化 + bodyChildren 15→18 页面完整渲染。
- **端到端待肉眼验**（非阻塞）：用户开 serve 问 AI 一个出图问题，看 run_python 是否被调 + `{{fig:ID}}` 图片是否渲染。

### 待 push（用户手动）
本地领先 origin **11 commit**：5.80-5.82 字段语义 5 个 + 5.83 沙箱 3 个（`3050f3a`/`cc54e17`/`8526f41`）+ 5.79 用地分类 + 交接。`git push` 即可。

### ⬜ 下会话：沙箱主线已收，可选下一步
**沙箱 /run 已挂 + 前端半崩修复**，无遗留主线。下会话可选项：
1. **验 run_python 端到端**（建议先做）：用户开 serve 问 AI 出图问题（如「画各区情绪极性对比柱图」），看 run_python 工具是否被 LLM 调、matplotlib 图是否捕获、`{{fig:fig1}}` 是否渲染成 img。若有问题修。
2. **L4 多维归因**（⬜ 长期预留）：4×5 domain×element 归因的 L4 层（框架已预留，L3/L4 待实现）。
3. **空间分析引擎 MVP**（⬜）：缓冲区 + 行政单元聚合（Toolbox 多维归因分析待启动）。
4. **UI 设计优化**（⬜）：布局/色彩/交互（导航架构重塑 B4/B5 待续）。
5. **其他**：用户定。

### 承重（必守，下会话续改时留意）
- **沙箱（已完成，守不退）**：`SAFE_READY=True` 单点 revert（改回 False main.py gate 自动卸载 /run）；frame-based trust 不破（库帧 lazy-import/lazy-open/eval 放行，pandas/matplotlib/numpy 不误伤）；演示版非 OS 隔离（内存 CPU 仅超时软限、别名反射 AST 拦不住靠禁 eval 收敛——文档化，生产须叠容器/低权用户）；run_sandbox 永不裸输；不破 5.74 对账（figId 纯 ASCII + observation 用「图片」不进 verbRe/showRe）。
- **前端 ESM 语法验证**：`node --check x.js` 对 ESM 假绿；改前端 JS 后须 `.mjs` 副本扫描（`cp x.js /tmp/x.mjs && node --check`）+ 最好 Playwright 真加载验。
- **字段语义层（已完成，守不退）**：物理列名不改 / registry 字段段方括号包裹不破 5.74 / LLM 复用 chat_with_fallback / 自产层只声明 / field_dictionary 在 core/ / 思考透明 5.70 不动。
- **四态出口契约**（5.77）：EXIT_RESULT/GAP/CONCEPT/PARTIAL 扩非替换；ask_user 速率上限（_consecutiveAsks≥2 禁止）。
- commit/push 分离（用户手动 push）；专业词+通俗解释（用户初学者）。

### 本轮改的关键文件（下会话续改看这些）
- 沙箱：[api/sandbox.py](api/sandbox.py)（SAFE_READY=True + AST 反射 + open-wrapper PRELUDE + frame-based eval 双工厂 + _build_env MPLCONFIGDIR）/ [api/run_routes.py](api/run_routes.py)（POST /run + _encode_images figId）/ [api/main.py](api/main.py)（CORS 收紧 + if SAFE_READY 挂载）
- 前端 run_python：[frontend/js/ai_qa/tools.js](frontend/js/ai_qa/tools.js)（run_python 工具 + _figCache/getFig/clearFigCache + fetchRun + **buildContext 括号修复 L431**）/ [frontend/js/ai_qa/panel.js](frontend/js/ai_qa/panel.js)（_renderFigs + enhanceCodeBlocks + import getFig）
- catalog/prompt：[ai_qa/paradigm.py](ai_qa/paradigm.py)（CODE_EXEC_CATALOG + code_exec_catalog_text）/ [ai_qa/prompts.py](ai_qa/prompts.py)（run_python schema 行 + build_agent_prompt 拼 catalog）
- 测试：[tests/test_sandbox.py](tests/test_sandbox.py)（+9 加固测试，28 passed）

### 承重 memory 索引
- 本轮相关：`sandbox-eval-wrapper-context-restore`（劫持 eval/exec 须补 globals/locals=真正调用帧）/ `node-check-esm-unreliable`（node --check 对 ESM 假绿，须 .mjs）/ `emc-tri-state-exit-contract`（出口契约四态）/ `commit-only-user-pushes`（commit 后告知待 push）/ `pro-term-plus-plain-meaning`（专业词+通俗解释，用户初学者）/ `maintain-revision-log`+`todo-revision-log-sync`（每事同步）/ `chinese-all-deliverables`（交付物中文）/ `no-handoff-on-routine-commit`（说"交接"才覆写本卡）/ `landuse-codes-2023`（用地分类权威源读 .py 勿读 PDF，PDF 原件已删）

---

## 新会话 prompt（复制即用）

```
继续 EMC。沙箱 /run 已挂 + 三道底线加固完成（5.83，commit 3050f3a），buildContext 括号 hotfix（5.84，cc54e17/8526f41）。
本地领先 origin 11 commit 待手动 push。
沙箱 28 测试过、/run 端点真调过、openapi 确认挂载、Playwright 0 errors + buildContext OK + 页面完整渲染。
端到端 run_python（LLM 调 + 图片渲染）待肉眼验：开 serve 问 AI 出图问题。
本次按交接卡选下会话主线（建议先验 run_python 端到端，或 L4 归因/空间分析 MVP/UI 优化，或用户另定）。
承重：SAFE_READY 单点 revert / frame-based trust 不破（库帧放行）/ 演示版非 OS 隔离文档化 /
node --check 对 ESM 假绿须 .mjs 验 / 不破 5.74 对账（figId 纯 ASCII + 「图片」措辞）/
commit 只不 push / 专业词+通俗解释。
先读交接卡 memories/repo/session-handoff.md，再动手。
```
