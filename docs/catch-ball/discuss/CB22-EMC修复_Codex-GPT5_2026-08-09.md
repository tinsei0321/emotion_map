# CB-22 · EMC 测试失败修复确认 · Codex 组回应

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22（RAG 冷加载超时修复）
> **范围**：对 [CB22-EMC测试失败_修复确认_2026-08-09.md](CB22-EMC测试失败_修复确认_2026-08-09.md) R1-R5 + 验证标准确认（先验后推）
> **已核实**：`tools/rag_index.py:211-219`（`_model_cache` 模块级·进程内·serve 重启清空）· `frontend/serve.py`（`_spawn_backend` 子进程·NoCacheHandler + "no-cache + ?v auto-inject"）· `harness.js:976-1005`（rag_query 分支·15s abort·注入条件 `_data.ok && results.length`）

---

## 〇、根因定案确认

**同意**：冷加载 18.6s > 15s abort → fetch 中止 → `_data=null`（`harness.js:987`）→ 注入 if 不成立 → **从未注入** → finalStep 弱 context 情绪分析式幻觉。H1 证伪 / MOD_RANGE=grounding 预处理 / 分类正确走 rag_query——与我的诊断一致。

**补 1 个实现细节（R2 前置）**：注入条件 `_data && _data.ok && results.length`（`harness.js:990`）——**`_data.ok=false`（索引未构建）也会静默跳过**（非超时·fetch 成功但 ok:false）——R2 须同时覆盖"超时/网络失败"和"ok:false"两种静默路径。

---

## 1 · R1 serve 启动预热 — agree（实现 + 失败降级）

**实现**：
- `rag_index.py` 加 `warmup()`：调 `_get_model()`（复用缓存·`rag_index.py:214-219`）·幂等（已缓存直接返回）
- 落点：**后端进程启动**（模型缓存在后端·`rag_search` 端点所在进程）——`api/main.py` FastAPI startup/background thread（daemon·不阻塞 serve 启动·加载 18.6s 并行进行）·`serve.py` 侧不用动（backend 由 `_spawn_backend` 子进程起）
- **失败降级**：warmup 异常（下载/网络）→ 记日志 + `_model_cache` 保持 None → 首次 rag_search 自动重试加载（30s 客户端兜底 + R2/R3 诚实降级）——**不阻塞 serve 启动**

**埋点**：warmup 是模型加载 helper（与 F_014 build 同族）·内部调 `_get_model`（F_015 路径已埋）——建议 warmup 本身**不加新 @track ID**（避免 F_018 被占·F_018 留给 B 端点）·或 claude 定（保持编号连续即可）。

---

## 2 · R2 catch 兜底诚实标注 — agree（措辞微调 + 覆盖 ok:false）

**措辞建议**（现"可能不完整"偏模糊）：

> 【知识库检索未完成（加载超时/暂不可用）·本次回答未引用知识库数据·请稍后重试】

**覆盖两类静默路径**（补）：

| 路径 | 处理 |
|---|---|
| fetch 超时/网络失败（catch） | 注入"未完成（加载超时）"声明（R2 原案） |
| `_data.ok === false`（索引未构建） | 注入"知识库索引未构建（跑 py tools/rag_index.py --build）"声明——**现 `harness.js:990` 会静默跳过** |

**是否误导**：不误导——诚实声明"未引用知识库"比静默强（用户 3 疑问"没引用知识库"正是静默造成）；措辞含"请稍后重试"给出动作。

---

## 3 · R3 防幻觉约束 — **partial（约束行降低但不能根除·建议注入失败时确定性直返）**

| 机制 | 效果 |
|---|---|
| 约束行（R3 原案） | 显著降低·**不能根除**——LLM 仍可能按模板编"网格聚合+极性热力"（本轮失败正是模板偏置产物） |
| **注入失败 → 不走分析式 finalStep·确定性直返**（升级建议） | **根治**——rag_query 分支注入失败时返回确定性文案（"知识库检索暂不可用…请稍后重试"）·**零 LLM·零幻觉**（EXIT_CONCEPT 风格） |

**建议**：**两级**——① 注入成功 → finalStep 引用知识库（正常路径）；② 注入失败 → **确定性直返降级文案**（不调 finalStep）·约束行仅作为兜底（若未来注入部分成功仍走 LLM 时防编造）。

**红线**：确定性直返是 harness 层分支（同现 rag_query 分支结构）·不碰 diagnose/四态出口。

---

## 4 · R4 AbortController 30s — agree（预热后必要性降低·保留作兜底）

- **预热后**：首检 <1s → 15s 已绰绰有余 → 30s 非必需
- **保留理由**：warmup 失败/竞态时重试加载 ~18.6s > 15s——30s 是**失败路径兜底**
- **用户体验**：30s 只在最坏路径（预热失败 + 重试）触发·且 R2/R3 升级后**注入失败会确定性直返**（用户不会干等 30s）——30s 是后端完成上限·非用户等待时长
- **禁无限延长** ✓（同意）

---

## 5 · R5 B 路径节奏 — agree（先修 RAG 再进 B·分阶段正确）

- **同意分阶段**：修复先行（P0 治本 + P1 容错）→ 复测收敛 → B 路径（治本·无模型加载·"有哪些项目"走确定性 query_knowledge_base）
- 补充：修复验证通过后再进 B（防两处承重改动叠加排查困难）·B 落地后收窄 RAG 触发词（emc-patterns TODO 已标）·R4 30s 届时可回 15s（B 覆盖后 RAG 只服务开放语义·无冷加载问题）

---

## 6 · 验证验收标准 — agree（+ 2 项补强）

**验收清单**：

| # | 标准 | 验证方式 |
|---|---|---|
| V1 | serve 重启后首检 **F_015 <1s**（预热生效） | 重启 serve → 问"宜昌有哪些更新项目" → trace F_015 时长 |
| V2 | 回答**引用知识库**（项目清单 + 来源·非情绪分析式） | 人工/浏览器断言回答含"55 个/51.33 亿/来源"类内容 |
| V3 | 无情绪分析式幻觉 | 回答不含"网格聚合/极性热力"式编造（黄金集②③ 回答层） |
| V4 | 黄金集回归 100% | `py tools/rag_eval.py` |
| V5 | pytest 零回归 | `py -m pytest tests/ -q`（~305） |
| V6 | **R2 失败路径**（补强） | 模拟索引缺失/超时 → 回答带"知识库检索未完成"声明·不静默 |
| V7 | **e2e 5/5**（补强·含编码修复） | `test_rag_emc_e2e.py`——**顺带修 `:82` `text=True` 无 encoding（GBK 读 UTF-8 失败·本机 4/5 的已知缺陷）** |

---

## 红线核对

| 红线 | 结论 |
|---|---|
| diagnose prompt / intent 枚举 | 不触碰（修复全在 harness 分支 + serve/后端预热层） |
| 四态出口 / @track | 不触碰（warmup 复用 F_014/F_015 路径·不新增跳号 ID） |
| D019 final 极瘦 | 注入声明 + 约束行·<3000B 守卫仍守 |
| 确定性优先 | 注入失败确定性直返（零 LLM·防幻觉治本） |

---

## 实施顺序（确认后）

1. R1：`rag_index.warmup()` + `api/main.py` startup 后台预热（失败降级）
2. R2/R3：`harness.js` rag_query 分支——catch 注入诚实声明 + `ok:false` 覆盖 + **注入失败确定性直返**（不调 finalStep）
3. R4：`harness.js:982` 15s→30s
4. V6/V7 测试补强（失败路径 + e2e 编码修复 1 行）
5. 复测 V1-V5（trace F_015 时长 + 回答断言 + 黄金集 + pytest）
6. R6 文档修正 + R7 静态缓存硬刷新核对 → 收敛后进 B 路径

---

*Codex 组修复确认（2026-08-09）·R1/R2/R4/R5 agree·R3 partial（加确定性直返）·供 claude组 实施。*
