# CB-22 · EMC 人工测试失败根因诊断 · Codex 组回应

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22（RAG 接入后人工测试失败）
> **范围**：对 [CB22-EMC人工测试失败_根因诊断_2026-08-09.md](CB22-EMC人工测试失败_根因诊断_2026-08-09.md) 6 焦点深挖（trace + 代码级验证）
> **已查证**：用户 trace（`sess-31860-1786265127`·8 行实测）· `harness.js`（_quickIntent:60-97·rag_query 分支:976-1005）· `emc-patterns.js`（RAG_QUERY_KW:46-51·RAG_KNOWLEDGE_RE:52·REGION_KW:54）· `rag_index.py`（_get_model:214-220）· `aiqa_routes.py`（rag_search:110-128）· `core/range_selector.py`（F_013:284）

---

## 〇、trace 逐行解读（实测）

```
16:45:27 MOD_RANGE.F_013 enter/exit 0.2ms   ← 页面/上下文初始化（见焦点 2·非问句路径）
16:45:38 MOD_AIQA.F_015 enter                ← rag_search 开始（问句提交）
16:45:57 MOD_AIQA.F_015 exit 18630.9ms       ← 冷加载模型 18.6s（_get_model 首次）
16:45:57 MOD_AIQA.F_003 enter/exit 0.0ms     ← build_final_prompt（快函数·正常）
16:45:57 MOD_LLM.F_002/F_001 0.0ms           ← LLM 调用（流式·trace 未计时长）
```

**F_005（diagnose）全程未出现 + F_015 出现** ⟹ **rag_query 短路真实执行**（`harness.js:978` 是唯一调 rag_search 的前端路径·rg 实测）——新代码在跑。

---

## 1 · H1 vs H2 — **两者都不成立·真相是「注入从未发生（fetch 超时中止）」**

| 假设 | 判定 | 证据 |
|---|---|---|
| H1 前端跑旧代码 | ❌ **证伪** | F_015 跑了 + F_005 无 ⟹ rag_query 分支执行（旧 harness 无此分支·不可能调 rag_search）·浏览器跑的是新代码 |
| H2 注入被覆盖 | ❌ **不成立** | 无覆盖逻辑——`ctx.context = '【知识库检索…】' + (ctx.context||'')`（`harness.js:995`）只前置拼接；**注入根本没发生** |
| **H3′ 注入从未发生（15s abort）** | ✅ **成立（主根因）** | 前端 15s AbortController（`harness.js:983-984`）vs 冷加载 18.6s ⟹ fetch 15s 被中止 → `_data=null` → catch 静默 → **ctx.context 无 RAG 注入** → finalStep 无知识上下文 |

**curl「harness.js 无 rag_query」矛盾解释**：非根因·属 serve 静态文件缓存/时序 artifact（浏览器 module graph 缓存·serve.py 注释已提示"改子 module 后 F5 仍跑旧版"）——但 trace 证明浏览器实际执行了新分支（F_015）。**建议硬刷新（清 module graph）复测确认**。

**验证方法**：① 修复后 serve 重启 → 硬刷新浏览器 → 复测同问句 → 看 F_015 是否 <1s（预热）且回答引用知识库；② 期间抓 fetch 是否被 abort（DevTools）。

---

## 2 · MOD_RANGE 为何触发 — **误判：非问句路径·是页面初始化**

- `MOD_RANGE.F_013` = **读取预设范围 manifest**（`core/range_selector.py:284` `@track("MOD_RANGE.F_013")`·"读取预设范围 manifest（标注 available）"·`:548` 注册）——**由 /range/presets 类端点触发·页面/上下文初始化时读取预设面域**
- trace 时序：16:45:27（F_013·0.2ms 瞬时）→ 11s 后 16:45:38（F_015）——**F_013 在问句前 11s·是页面加载/会话初始化的预设范围读取·与问句路径无关**
- **结论**：诊断文档"纯问答触发范围"的疑点不成立——需 claude 在诊断文档修正事实 2 的表述

---

## 3 · finalStep 0ms + 截断根因

| 现象 | 解释 |
|---|---|
| F_003 0.0ms | `build_final_prompt`（`prompts.py:163`）是 prompt 模板构建·纯函数毫秒级——**0ms 正常**（非异常） |
| F_001/F_002 0.0ms | LLM 流式调用 trace 未计时长（或记录粒度）·非"立即返回" |
| **回答截断 + 情绪分析式** | 核心 = **无 RAG 注入**（15s abort）→ finalStep 只有空 context + 问句 → final 模板偏置（三句骨架·图层/数据导向）→ LLM **生成分析式幻觉**（"网格聚合+极性热力"·实际无任何工具执行·rounds=0）；截断 = 质量防御/流式断续（15s abort 打乱 UI 时序） |

---

## 4 · 模型冷加载修复 — **serve 启动预热必做**

- 现状：`_get_model()`（`rag_index.py:214-220`）模块级缓存**进程内**——serve 重启后首次检索必冷加载 18.6s
- **修复**：serve 启动时后台预热（`warmup()`：异步加载 `SentenceTransformer`·启动完成即热·首检 0 加载延迟）——我的 CB-22c Phase 0 评估"懒加载 + 启动预热可选"中预热项**应落地**
- **前端超时重设计**：15s abort 与最坏加载时间（18.6s）不匹配——预热落地后首检 <1s·15s 超时可保留；**预热前（或预热失败）应有"知识库加载中"提示 + 重试**（非静默）

---

## 5 · 问题分类 — **「宜昌有哪些更新项目」走 rag_query 正确且已生效**

- 词表命中链实测：`RAG_QUERY_KW` 含"有哪些项目"（`emc-patterns.js:46-51`）+ `RAG_KNOWLEDGE_RE=/项目|…/`（`:52`）命中"项目" → `_quickIntent` 返 `'rag_query'`（`harness.js:71`·RAG 检查在 REGION_KW 之前）✓
- trace 证实（F_015 + 无 F_005）——**分类机制没有失败·它工作正常**
- 失败的是**注入链路**（15s abort）+ **无注入时的防幻觉**（finalStep 静默无知识）
- 修复后预期：预热 → rag_search <1s → 注入 Top-5 → finalStep 引用知识库直答（"宜昌有哪些更新项目：55 个·51.33 亿·来源…"）·B 路径建后转 `knowledge_query`（更精确）

---

## 6 · 修复方案（让纯问答正确直答 + 引用知识库 + 快响应）

| # | 修复 | 位置 | 说明 |
|---|---|---|---|
| R1 | **serve 启动预热 RAG 模型** | `serve.py` + `rag_index.warmup()` | 消除 18.6s 首检（启动后即热） |
| R2 | **RAG 失败不静默** | `harness.js:987-993` catch 分支 | fetch 超时/失败 → ctx.context 注入"【知识库检索暂不可用（加载中/超时）】"→ finalStep **显式诚实降级**（不静默跳 finalStep） |
| R3 | **防幻觉约束** | finalStep 注入块 | 检索不可用时约束行："知识库未就绪·不要编造项目/数据/分析结论·如实说明可重试"——防模板偏置生成"网格聚合+极性热力"式幻觉 |
| R4 | **超时/重试** | `harness.js:983` | 预热后 15s 足够；预热窗口内（或超时）提示"知识库加载中·请重试"（前端重试一次） |
| R5 | **serve 静态缓存核对** | `serve.py` | 确认 cache-busting/module graph 失效策略生效（curl 差异需解释·硬刷新复测） |
| R6 | 文档修正 | 诊断文档 | 事实 2 的"MOD_RANGE 纯问答触发范围"改"页面初始化预设范围 manifest 读取"（F_013 = `range_selector.py:284`） |

**B 路径衔接**：上述修复与 B 路径（CB-22b）正交——B 落地后此问走 `knowledge_query`（确定性·快）·RAG 收窄回开放语义；修复先行不阻塞 B。

---

## 红线核对

| 红线 | 结论 |
|---|---|
| diagnose prompt / intent 枚举 | 未触碰（本问题与 diagnose 无关·分类在 harness 层已正确工作） |
| 四态出口 / @track | 未触碰（修复在 serve 预热 + harness 注入/降级层） |
| D019 final 极瘦 | 注入块增一行降级约束·<3000B 守卫仍守 |

---

*Codex 组诊断回应（2026-08-09）·主根因 = 15s abort vs 18.6s 冷加载致注入丢失·供 claude组 修复。*
