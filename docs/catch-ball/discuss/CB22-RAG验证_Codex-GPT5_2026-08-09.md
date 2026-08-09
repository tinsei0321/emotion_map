# CB-22 · RAG 接入 EMC 验证 · Codex 组

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22（RAG 接入验证·证据驱动）
> **范围**：对 [CB22-RAG验证_发起_2026-08-09.md](CB22-RAG验证_发起_2026-08-09.md) 9 项成果核验 + 6 焦点（代码核验 + 可跑测试实测）
> **实测**：`py tools/rag_eval.py`（黄金集）· `py -m pytest tests/browser/test_rag_emc_e2e.py` · `pytest tests/test_outlet_kb.py + test_outlet_schema.py` · `rag_index.py --stats` · 代码逐项核验

---

## 〇、实测结果总览

| 测试 | 结果 |
|---|---|
| 黄金集 `rag_eval.py` | ✅ **100%**（召回 10/10·越维 2/2·案例 2/2·整体通过） |
| e2e `test_rag_emc_e2e.py` | ⚠️ **本机实测 4/5**（claude 报 5/5）——1 失败为**跨环境编码缺陷**（见 #9） |
| `test_outlet_kb.py` + `test_outlet_schema.py` | ✅ 47 passed（含 point 方法论断言） |
| 索引 | ✅ 225 条·512 维·`search()` 11-13ms（**模型缓存已生效**） |

---

## 1 · 9 项成果证据核验 — 8 项属实 + 1 项有缺陷

| # | 成果 | 核验 |
|---|---|---|
| 1 | case point 方法论 | ✅ `test_outlet_kb.py:62-65` 断言（point 非空·≤80 字·**不含数字**·47 passed） |
| 2 | 事实卡 35 条（7 类·dimension） | ✅ `ai_qa/outlet_kb/urban_renewal_knowledge.py`（PROJECTS 8/INDICATORS 8/…·dimension 落位正确） |
| 3 | rag_index 225 条（模型缓存·原子写·维度标注） | ✅ `--stats` 实测 fact 35+note 185+case 5·search 11-13ms（缓存生效）·meta 含 data_dim |
| 4 | 黄金集 3 类 | ✅ `rag_eval.py` 实测 100%（召回 10/10·越维/案例刚性） |
| 5 | cannot 维度化（F_016） | ✅ `build_outlet_schema.py:23,287`（`_render_dimension_cannot`·@track 注册） |
| 6 | 端点 /aiqa/rag_search（F_017） | ✅ `api/aiqa_routes.py:110-128`（dim_counts 聚合·`ok/results/count/dim_counts`·未构建索引降级文案） |
| 7 | harness 'rag_query' 短路 | ✅ `harness.js:71`（RAG_QUERY_KW + RAG_KNOWLEDGE_RE 双条件保守）·`:978` 短路分支·e2e-seam 直测口 |
| 8 | finalStep 注入 | ✅ `harness.js:976-1000`（Top-5·每条 ≤200 字·维度标注·检索纪律·15s 超时·失败静默降级） |
| 9 | e2e 5/5 | ⚠️ **本机 4/5**——`test_rag_gold_set_regression`（`test_rag_emc_e2e.py:81-89`）`subprocess.run(text=True)` **未指定 encoding**：GBK 区域设置读 UTF-8 输出 → `UnicodeDecodeError` → `r.stdout=None` → 断言失败。claude 环境 5/5 成立（UTF-8 locale）·**缺陷真实（跨环境不可移植）** |

**修正建议（1 行·交付前）**：`subprocess.run(..., text=True, encoding='utf-8', errors='replace')`。

---

## 2 · 颗粒度原则落地 — agree（充分·补 1 标注）

- ✅ **data_dim 全链**：事实卡（dimension）→ 索引（data_dim）→ 端点（dim_counts）→ finalStep 注入（维度标注·`harness.js:981`）
- ✅ **cannot 维度化**（F_016·按数据源维度渲染"无法到更细维度"）
- ✅ **黄金集②越维 2 例** + harness 检索纪律（"结论不超过 data_dim·不得引用他城具体数值"·`harness.js:995`）
- ⚠️ **标注**：越维/案例的"回答层"约束靠**注入纪律文本 + finalStep 约束**（e2e-seam 不发真实 LLM·无端到端回答断言）——**建议 B 路径落地后补 1-2 例真实 LLM 抽验**（"数据到片区·问栋"→ 回答确实降级声明·非仅检索层命中）

---

## 3 · 案例方法论 — agree（落实）

- ✅ point 5 案例方法论浓缩·**无数字**（机器断言 `test_outlet_kb.py:64-65` 守卫）
- ✅ `_load_cases` 只取 point + "方法论参考·不引用他城具体数值"标注（`rag_index.py:94-101`）
- ✅ 黄金集③ 2 例（南京/问卷量禁词·实测通过）

---

## 4 · 承重红线 — agree（守住）

| 红线 | 核验 |
|---|---|
| diagnose / intent 枚举 | ✅ 零触碰（`_quickIntent` 前置短路·`prompts.py` 3 值未改） |
| @track 连续 | ✅ F_016（cannot）·F_017（端点）注册·编号连续（F_015→F_016→F_017 无跳号） |
| D019 <3000B | ✅ 注入 Top-5 × ≤200 字 ≈ 1KB·远低于守卫（+ 检索纪律一行） |
| 数据红线 | ✅ `data/rag_index/` gitignore（.gitignore:19） |

---

## 5 · 黄金集质量 — partial（**100% 非 cherry-pick·但覆盖有缺口**）

**非 cherry-pick 证据**：14 条 3 类·含历史难例（"葛洲坝片区停车泊位缺口"曾 Top-1 南京·现在必须命中本地·防回归）·预期 source 用关键词匹配（防路径硬编码脆弱）·10 条召回全部命中事实卡/宜昌笔记（事实卡向量化收益真实）。

**覆盖缺口（RAG 核心价值 = 开放语义·未充分验证）**：

| 缺口 | 建议难例 | 期望 |
|---|---|---|
| 跨文档综合正向 | "哪些城市用片区统筹解决资金平衡" | 命中案例方法论（上海/广州/杭州·非事实卡直命中） |
| 案例方法论召回正向 | "上海城市更新怎么组织" | 命中 case 方法论·**无数值** |
| 模糊长尾 | "社区设施怎么补" | 命中完整社区/事实卡 |

**判定**：现有 100% 证明「结构化事实卡检索」达标；**「开放语义跨文档综合」未充分验证**——补 3-5 条难例后黄金集完整（不阻塞当前交付·B 路径落地后补更合适——结构化查询归 B·开放语义归 RAG）。

---

## 6 · 可交付判定 — **有条件交付**

| 项 | 判定 |
|---|---|
| 核心功能（检索/注入/维度/红线） | ✅ 真实可用（黄金集 100%·47 passed·225 索引·11-13ms） |
| **交付前修正 1 项** | e2e 编码缺陷（`test_rag_emc_e2e.py:82` 加 `encoding='utf-8'`）——1 行·改后本机应 5/5 |
| **后续补 2 项**（不阻塞交付） | ① 黄金集补难例（跨文档/案例方法论正向 3-5 条）② 真实 LLM 抽验越维回答 1-2 例 |
| B 路径衔接 | 验证收敛 → 进 CB-22b（query_knowledge_base）·落地后收窄 RAG 触发词（emc-patterns TODO 已标）·gold 难例同步补 |

---

*Codex 组验证报告（2026-08-09）·供 claude组 修正后交付。*
