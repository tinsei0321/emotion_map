# EMC 运行时测试用例清单（C6 盲区 catalog）

> eval（`tests/eval_template_flash.py`）只测 Flash 模板路由（空 context），**运行时行为测不出**。
> 本文件登记这些 C6 盲区用例，每例：描述 / 前置 / 步骤 / 断言 / 状态。
> 可自动化的落 `tests/browser/`（Playwright），其余为手工用例。主 plan：Phase 5 筑基。

状态：✅ 已实现并跑通 ｜ 🔄 进行中 ｜ ⬜ 待实现 ｜ 🤚 手工（难自动化）

---

## 用例 1 · compare 中文地名↔preset_id 错配 ✅

- **描述**：欢迎胶囊"对比西陵区和伍家岗区的情绪与归因" → compare_regions 调 2× zonal_stats。
  修复前 LLM 把中文名"西陵区"当 preset_id 传 → 后端 `load_preset` 按 id 查无 → 400 → "仅 0/2 区"。
  修复 = `frontend/js/ai_qa/boundary-resolve.js` 把中文名解析成 `admin_district` 内 feature 的 GeoJSON dict。
- **前置**：`.env` DEEPSEEK key；`data/boundaries/presets/行政区.geojson` 在位。
- **步骤**：开 EMC → 填 `#chat-input` + 点 `#chat-send`（问句含"对比"→ select_template 路由 compare）。
- **断言**：硬=2× `POST /geo/zonal_stats` 均 200 + `rows[0].name` 含两区；软=回答文本含两区。
- **脚本**：`tests/browser/test_compare_regions.py`。
- **关联**：memory `emc-compare-skill` / `verify-real-endpoint`；plan `5-127-...shiny-tome.md` Phase 5。

---

## 用例 2 · domain_lens 等结构字段被前端压扁 ⬜

- **描述**：diagnose 卡的结构字段（`domain_lens` 等）被前端压扁进 `ctx.context` 字符串丢结构，
  下游结构化用（compare/threading）须显式回传 ChatRequest（④5.108 范式），别正则抠。
- **前置**：问一句会触发 domain_lens 的多领域问句（如"对比规划与治理两板块"）。
- **步骤**：开 EMC → 发多领域问句 → 抓 `/chat` SSE agent_step → 看 domain_lens 是否数组传到下游。
- **断言**：硬=下游（如 compare/归因）按 domain_lens 分组正确；软=回答体现两板块对比。
- **关联**：memory `emc-domain-lens-threading`。

---

## 用例 3 · `_driftRe` 无围栏裸 JSON 边缘 ⬜

- **描述**：harness.js `_driftRe` 拦「任意 ``` 围栏」→ revise；边缘 case = 草稿含裸 JSON 内联（无围栏）
  或围栏内非 action-JSON，确认不静默 strip、走 revise-失败→固定卡 通道。
- **前置**：构造会触发 LLM 产围栏/裸 JSON 的问句（如强求"给 JSON"）。
- **步骤**：开 EMC → 发问 → 看回答是否泄漏代码块 / 是否走 revise 兜底。
- **断言**：硬=回答无裸 ``` 围栏泄漏；软=有合理兜底叙述。
- **关联**：memory `emc-compare-skill`（_driftRe 拓宽段）。

---

## 用例 4 · 路由与空 context eval 分歧 🤚

- **描述**：`eval_template_flash` 用 `build_diagnose_prompt('')` 空 context 选模板；
  有 grounding 层时运行时路由可能与空 context eval 分歧（C6：居住用地里→zonal 非 overlay）。
- **前置**：先加载某 grounding 层（如居住用地 preset）→ 再问会落在分歧路由的问句。
- **步骤**：browser 先上载/选层 → 发问 → 对比 eval（空 context）与运行时（有层）的路由。
- **断言**：人工判运行时路由是否更贴合 grounding（eval 测不出，靠 browser）。
- **关联**：memory `emc-eval-empty-context-vs-runtime`。

---

> 加例守则：先在此 catalog 登记（状态⬜）→ 实现 `tests/browser/` 脚本 → 跑通标 ✅。
> 断言一律硬挂网络层/数据层（测真业务端点），软挂回答散文。
