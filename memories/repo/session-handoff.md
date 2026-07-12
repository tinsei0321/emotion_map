# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月12日（P0d+P1+P3 收工）| 分支 `main`（**本地领先 origin 6 commit 待用户手动 push**）| 本次 = EMC 月级改造（一）：P0d 第四态 EXIT_PARTIAL + P1 ask_user 拟人 + P3 沙箱骨架（未挂 /run）

---

## 当前节点：5.77 P0d+P1+P3 沙箱骨架完成，下会话 P3 挂 /run → P2

### 背景
月级全计划（`C:\Users\admin\.claude\plans\calm-discovering-snowflake.md` 已批）开跑。本次第一段：体验闭环（第四态出口 + 主动问澄清）+ code-exec 沙箱地基。全程两组 Workflow 多 agent 对抗验证（ultracode 模式）——初验揪 CRITICAL+10 项承重 bug，全修；复验确认 + 再修 5 minor；0 新回归。

### ✅ 本会话已做（5.77）
- **P0d EXIT_PARTIAL 第四态**：[manifesto 第八节](ai_qa/manifesto.py) 三态→四态；[harness composePartialCard](frontend/js/ai_qa/harness.js) 引导式三段卡（已为你完成 A + 局限标注 B + 引导补 X，断言句→对话引导）；对账 missing 1-2 升级走 partial 出口（保 draft+inline 标注+引导卡）；composeGapCard 头部断言软化。
- **P1 ask_user 主动澄清 + 对话引导**：[prompts](ai_qa/prompts.py) action schema 加第三态 ask_user + 出口铁律放宽 + rule8（何时问，硬上限 1-2 次）；[stages parseAgentStep](frontend/js/ai_qa/stages.js) 加 isAsk 归一（含顶层裸 ask_user 收编 + options 对象 coerce）；[harness](frontend/js/ai_qa/harness.js) 主循环 ask 分支（exit='ask' 挂起，用户点选项→新 orchestrate 续作，无死锁）；[panel onAskUser](frontend/js/ai_qa/panel.js) 渲染问+选项胶囊（复用 aiq-suggest-chip）+ 历史恢复重建胶囊；_consecutiveAsks 跨会话速率上限（≥2 禁止 ask）+ 上轮 ask 强制 resume 续作链；FINAL_TEMPLATE「做成一部分也体面」+ 多目标收紧。
- **P3 沙箱骨架**：[api/sandbox.py](api/sandbox.py)（`SAFE_READY=False` 红线，**未写 run_routes.py、未挂 /run**）+ [tests/test_sandbox.py](tests/test_sandbox.py) 19 测试真跑 subprocess 全过。**核心设计 frame-based trust**（查 importer 帧：用户脚本→拦，库/冻结→放）解 matplotlib lazy-import socket vs 拦用户 socket 矛盾。subprocess `[-I, -X utf8]` + import 白名单 + 30s timeout + 写区隔离。**已知局限**（docstring 文档化）：open builtin 不拦（出图需写文件）、纯 Py 反射绕过——挂 /run 前须叠 OS 级隔离。
- **两组 Workflow 对抗验证**：① 初验 3 路 serious-issues 揪承重 bug 全修；② 复验 3 路 mostly-fixed + 再修 5 minor。详见 revision-log 5.77。

### 🔍 验证（已过 + 待复现）
- **静态全过**：node --check（harness/stages/panel）+ prompts format + py_compile sandbox。
- **pytest 152 passed**（含新 test_sandbox 19 + test_llm_resilience 10）；6 failed 全预存环境问题（h3 未装 ×2 / SnowNLP / geocode 阈值 / range 数据），与本改动无关。
- **对抗验证 0 新回归**。
- **待用户带 key 复现**：P0d（对账 missing→partial 卡，非丢答案）/ P1（模糊问题→ask_user 胶囊点选续作）/ P3（暂不挂，下会话翻 SAFE_READY 后跑 run_python）。

### 待 push（用户手动）
本地领先 origin 6 commit：`2023d15`(5.72) / `153251f`(5.73) / `7596eee`(5.74) / `aced31c`(5.75) / `29f13f1`(5.76) / `02df5af`(5.77)。网络恢复后 `git push`。

### ⬜ 下会话：P3 挂 /run → P2（月级全计划续）
1. **P3 挂 /run（先复验沙箱再翻开关）**：
   - **红线**：先重跑 `py -m pytest tests/test_sandbox.py -q` + 人审 sandbox.py，全过才 `SAFE_READY = True`。
   - [api/run_routes.py](api/run_routes.py) 新：`run_router = APIRouter()`，class RunRequest(BaseModel){code, data_refs?} → @run_router.post('/run') 调 sandbox.run_sandbox，try/except→HTTPException（范式照 [geo_routes.py](api/geo_routes.py)）。
   - [api/main.py L80](api/main.py) 后：`from api.run_routes import run_router` + `if SAFE_READY: app.include_router(run_router, prefix="/api/v1")`。
   - [tools.js](frontend/js/ai_qa/tools.js) 加第 15 工具 run_python：POST /api/v1/run → 复用 addResultLayer（registry 自动记 provenance，⑤ 对账同样适用）。
   - [paradigm.py L192](ai_qa/paradigm.py) 后：新增 `CODE_EXEC_CATALOG` + `code_exec_catalog_text()`（平行 GEO_TOOL_CATALOG，键同 name/when/params/yields/contributes）。
   - [prompts.py](ai_qa/prompts.py) 加规则 8（何时 run_python [模糊字段/join/相关性/聚合] vs 窄工具）+ schema 加 run_python。
   - [panel.js _renderCharts](frontend/js/ai_qa/panel.js) 扩 `{{fig:ID}}` 渲染 matplotlib PNG artifact。
2. **P2 减 GAP**：[harness.js L227 request_upload 短路](frontend/js/ai_qa/harness.js) 拆→进 loop 跑 fallback_annotated 参考答+末尾引导上传（不一上来 GAP）；[panel.js _buildPriorTurn](frontend/js/ai_qa/panel.js) 加 task_plan/progress + harness formatPriorTurn 回灌跨多轮规划（类 TodoWrite）。

### 承重（必守，下会话续改时留意）
- **四态出口契约**（manifesto 第八节）：EXIT_RESULT/GAP/CONCEPT/PARTIAL。**扩非替换**——gap/drift/result 调用方语义不变。PARTIAL 仅 `_isPartialMissing`（对账 missing 1-2）触发。
- **fallback_annotated 走 EXIT_RESULT + renderCaliber 口径卡，不走 PARTIAL**（软缺口用替代数据仍完整，5.77 验证纠的 CRITICAL 误判）。
- **composeGapCard/composePartialCard 模板化**（确定性组装，不让 LLM 自创出口文案）；动态值（needed/gap/_missing/_actualNames/failedObs/existingLine）必经 `_esc` 转义防注入（marked v12 不净化）。
- **诚实门 _verifyClaims 不被任何出口跳过**（partial 分支内也跑 gis 验证）。
- **5.74 registry/对账 tool-agnostic**（_registry/formatRegistry/⑤ _extractClaimedLayers），code-exec run_python 复用（产物进 registry 自动，⑤ 对账同样适用）。
- **ask_user 速率上限**（_consecutiveAsks ≥2 注入禁止；clearChat/switchSession 重置；上轮 ask 强制 resume）；顶层裸 {ask_user:{}} 已收编防叙述吞。
- **沙箱红线**（SAFE_READY=False；挂 /run 前必复验沙箱单测 + 人审；frame-based trust 不破；挂 /run 须叠 OS 级隔离）。
- "永不裸输原始 token"（drift 拦截 + 5.76 宽容 revise）。
- **思考透明（5.70 主题折叠）不动**（业界对标以上，真拟人）。
- **commit/push 分离**（memory commit-only-user-pushes）：Claude 只 commit，用户手动 push。
- **专业词 + 通俗解释**（memory pro-term-plus-plain-meaning）：用户初学者，全程配对解释。

### 本轮改的关键文件（下会话续改看这些）
- 出口/对账/注入：[harness.js](frontend/js/ai_qa/harness.js)（_esc L71 / composeGapCard L78 + composePartialCard L101 / drift 拦截 L375 / 对账 missing L391 / partial 裁定 L412 / _hardFail L329 / finalStep L343 / _extractClaimedLayers L129 / _verifyClaims L115 / 主循环 ask 分支 L291）
- ask 渲染/速率/续作：[panel.js](frontend/js/ai_qa/panel.js)（_consecutiveAsks L22 / onAskUser L929 / _exitBadge L318 / _followUps L411 / appendAssistantShell 恢复胶囊 L763 / _buildPriorTurn ask 特化 L1033 / send 续作+计数 L1078/L1090 / clearChat+switchSession 重置 L1197/L207）
- action 解析：[stages.js](frontend/js/ai_qa/stages.js)（parseAgentStep L33 / 顶层 ask_user 收编 L76-78 / isAsk L86 / options coerce L97 / finalStep L188 / reviseStep L216）
- prompt：[prompts.py](ai_qa/prompts.py)（AGENT_TEMPLATE L29 / action schema L36 / 出口铁律 L43 / rule8 L83 / FINAL_TEMPLATE 出口要素 L114）/ [manifesto.py](ai_qa/manifesto.py)（四态出口 L54）/ [paradigm.py](ai_qa/paradigm.py)（DATA_STRATEGY L218 / CODE_EXEC_CATALOG 待加 L192 后）
- 沙箱：[api/sandbox.py](api/sandbox.py)（SAFE_READY L34 / WHITELIST L44 / run_sandbox / frame-based trust PRELUDE）/ [tests/test_sandbox.py](tests/test_sandbox.py)（19 测试）/ api/run_routes.py + main.py L80（下会话挂）
- CSS：[ai_qa.css](frontend/css/ai_qa.css)（.aiq-ask-options L309）
- 韧性（上轮·不动）：[llm.py](ai_qa/llm.py)（chat_with_fallback）/ [router.py](ai_qa/router.py) / [review.py](ai_qa/review.py)

### 承重 memory 索引
- 本轮相关：`emc-tri-state-exit-contract`（出口契约，已扩四态）/ `commit-only-user-pushes`（只 commit 不 push）/ `pro-term-plus-plain-meaning`（专业词+通俗解释）/ `maintain-revision-log`+`todo-revision-log-sync` / `chinese-all-deliverables` / `no-handoff-on-routine-commit`（说"交接"才覆写本卡）
- 计划文件：`C:\Users\admin\.claude\plans\calm-discovering-snowflake.md`（月级全计划 P0-P3 完整）/ 本会话计划 `C:\Users\admin\.claude\plans\emc-p0-p1-starry-fern.md`

### 待清理
- `out.png`（仓库根）：沙箱测试 breakthrough matplotlib 产物，未提交（下会话查 test_sandbox 是否漏清 cwd，或加 .gitignore）。

---

## 新会话 prompt（复制即用）

```
继续 EMC 月级改造（计划文件 calm-discovering-snowflake.md 已批），本次 P3 挂 /run → P2。
上次 5.77 做完 P0d（EXIT_PARTIAL 第四态）+ P1（ask_user 主动澄清+速率上限+历史恢复）+ P3 沙箱骨架（api/sandbox.py + 19 测试，SAFE_READY=False 未挂 /run），两组 Workflow 对抗验证 0 回归，commit 02df5af（待用户 push）。
本次从 P3 挂 /run 开始：先重跑 pytest tests/test_sandbox.py + 人审 sandbox.py 确认安全，再翻 SAFE_READY=True；然后写 api/run_routes.py（/run 端点，范式照 geo_routes）+ api/main.py 条件挂载 + tools.js run_python 第 15 工具（复用 addResultLayer，registry 自动记 provenance）+ paradigm.py CODE_EXEC_CATALOG + prompts 规则 8（何时 run_python vs 窄工具）+ panel.js _renderCharts 扩 {{fig:ID}} 渲染 matplotlib PNG。挂 /run 须叠 OS 级隔离（open/reflex 局限）。然后 P2：request_upload 短路拆→进 loop 跑 fallback_annotated 参考答 + 多轮规划（_buildPriorTurn 加 task_plan/progress）。
承重：四态出口扩非替换（PARTIAL 仅 _isPartialMissing）/ fallback_annotated 走 result 不走 partial / 卡片模板化+动态值 _esc 转义 / 诚实门 _verifyClaims 不被跳 / ask_user 速率上限 / 沙箱红线（挂 /run 前复验+人审+OS 隔离）/ 思考透明 5.70 不动 / commit 只不 push / 专业词+通俗解释。
先读交接卡 memories/repo/session-handoff.md + 计划文件，然后从 P3 挂 /run 动手（先复验沙箱）。
```
