# CB-22c · RAG Phase 1 实现评估 · Codex 组

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22c（Phase 1 实现）
> **范围**：对 [CB22c-RAG_Phase1_执行定稿_2026-08-09.md](CB22c-RAG_Phase1_执行定稿_2026-08-09.md) 的落地核验 + `tools/rag_index.py` 实现质量评估（6 焦点）
> **实测**：`py tools/rag_index.py --stats/--query` ×3 · import + `_TRACKING_REGISTRY` 核验 · meta.jsonl 字段核验 · .gitignore 核验

---

## 〇、实测结论（代码级·全部实测）

| 项 | 结果 | 证据 |
|---|---|---|
| 索引状态 | ✅ 190 条·512 维（note 185 + case 5）·meta.jsonl 0.05MB + vectors.npy 0.37MB | `--stats` 实测 |
| @track 注册 | ✅ F_014/F_015 已注册（import 时 register_track_id + `@track` 装饰）·**编号连续**（F_013→F_014/015） | `_TRACKING_REGISTRY` 实测 |
| 检索质量 | ✅ "宜昌有哪些更新项目" Top-5 全相关（0.763-0.788·0819/260713/00-02/00-03）·"葛洲坝体检问题" Top-5 全相关（0.650-0.697）·**"停车" Top-5 内容全相关（0.456-0.595·南京案例/南湖/停车专项/GIS 对照）** | `--query` ×3 实测 |
| 数据红线 | ✅ `data/rag_index/` 已入 .gitignore（line 19）·git status 干净 | .gitignore + git 核验 |
| HF_ENDPOINT | ✅ 代码层 setdefault（`tools/rag_index.py` 模块级·不覆盖用户显式） | 代码核验 |

**总体判定**：Phase 1 核心实现**可用**（检索召回正确·@track 合规·红线未碰）·但有 **2 项明确缺口 + 2 项建议补强**（见焦点 3/4/1/2）——**有条件通过**。

---

## 焦点 1 · 编码规范 — partial（统一封装 ✓·instruction 可选·**模型缓存缺口**）

- ✅ `_embed_texts` 统一封装（`tools/rag_index.py:_embed_texts`）+ `normalize_embeddings=True`——query/passage 一致处理·相似度不失真（与 Phase 0 结论一致）
- ⚠️ **bge query instruction 未用**：bge-v1.5 官方支持 query 前缀（"为这个句子生成表示以用于检索相关文章："）——**当前不加是自洽的**（两侧一致）；是否加由黄金集 Recall@5 决定（当前目测召回够·倾向不加·保持简单）
- 🔴 **模型实例未缓存（性能缺口·建议接入前必修）**：`search()` 每次调用 `SentenceTransformer(MODEL_NAME)` 新建模型——实测单次查询 **16-23s（含模型加载）**·同一进程多次查询会**重复冷加载**（第一次 40.4s 下载 + 每次 16-23s 加载）。接入 harness 会话内多次检索必卡顿——**建议模块级模型单例/lru_cache**（首次加载后复用）

---

## 焦点 2 · 原子写 + embed_hash — partial（原子写 ✓·**增量未落地 + 双文件一致性校验缺**）

- ✅ 临时文件 + `os.replace`（`build_index` 内 tmp_v/tmp_m → replace·防崩溃不一致）
- ✅ content_hash（sha256）已写入 meta
- ⚠️ **增量重向量化未实现**：`--build` 是全量重建（无 diff/按 source 重嵌）——执行定稿承诺"增量 hash"未落地。当前 190 条全量可接受（~1 分钟级）·但维护文档需明确"**Phase 1 全量重建（可接受）→ Phase 2 补增量**"或实现 diff
- ⚠️ **双文件原子一致性缺口**：先 replace vectors 后 replace meta——崩溃中间态可能出现两文件错位（新 vectors + 旧 meta）。`load_index()` 应校验 `len(vectors)==len(metas)`（**未实现·建议补**·不匹配则报"索引不一致·--rebuild"）

---

## 焦点 3 · 元数据 schema — partial（**明确缺口：缺 5 字段**）

| 定稿要求（执行定稿 §2） | 实现（meta.jsonl 实测） | 判定 |
|---|---|---|
| id / source / type / content_hash / embedding_model | source / type / content_hash / embedding_model / dim | ✅ 有 |
| **city / region / topic / year** | ❌ **缺** | ⚠️ 未落实 |

**影响**：
1. **city/region/topic 过滤无法做**——B 路径（query_knowledge_base）衔接 + 检索预过滤弱化（"葛洲坝体检问题"只能靠向量·无法先按 region 过滤）
2. **source 指针弱**：`docs/...md#0` 只有"文件+小节序号"·无 `_INDEX` 编号/版本状态——防张冠李戴追溯弱化（有文件路径可追·但不规范）

**建议**：补 `city/region/topic/year`（笔记可从文件名/内容派生·事实卡天然有）；source 增加 `_INDEX` 编号引用或至少保留文件名（当前文件名即主题·可接受·但编号更稳）。

---

## 焦点 4 · 索引覆盖 — partial（**事实卡缺口属实·建议 Phase 1 内先建**）

- ✅ 笔记段落 185 + case 5（case_library 当前 5 案例·覆盖正确）
- 🔴 **L1.5 事实卡未建**（执行定稿向量化顺序第 1 项未落地·CB-22b 尚未实施）——影响：
  - 数字类精确查询（"葛洲坝 12 个项目 11.07 亿"）只能靠笔记段落**概率召回**（粒度粗·需整段恰好含该数字）
  - B 路径（query_knowledge_base）与事实卡是同一层——**B 未建 + RAG 先上 = 精确查询全落概率召回·顺序反了**
- **建议**：Phase 1 内**先建 L1.5 事实卡**（小规模·从已提炼笔记确定性提取·与 CB-22b 共享同一层）→ 事实卡逐条向量化（补元数据）→ 再接 rag_search——事实卡是"结构化命中主源"·RAG 是"开放语义兜底"

---

## 焦点 5 · 检索质量 — agree（**先纠正评估口径**·黄金集必须补）

- ⚠️ **"0.595 停车偏低"是分数·不是召回**——实测"停车" Top-5 内容**全部相关**（南京停车大数据案例/南湖公园/停车专项体检/GIS 图层对照·0.456-0.595）——**评估必须用 Recall@5（Top-5 是否含期望 source）而非相似度分数**（分数低 = 内容分散·非答非所问）
- 🔴 `tools/rag_eval.py` + 黄金集**未实现**（执行定稿第 3 步未落地）——**Phase 1 验收前必须补**（Recall@5 ≥80% 门槛）
- bge-small vs large：维持"**Recall <80% 才升 large**"（执行定稿已采纳·agree）——用黄金集量化决定·不预设

---

## 焦点 6 · 承重红线 — agree（全部核验通过）

| 红线 | 核验 |
|---|---|
| @track 编号连续 | ✅ F_014/F_015 紧跟 F_013（`_TRACKING_REGISTRY` 实测）·**注：MOD_AIQA.F_004 缺失系历史既有跳号（非本次引入）·修正属全局梳理·低优先** |
| diagnose / 四态出口 | ✅ 未碰（rag_index.py 仅 tools/ 层·无 prompts/harness 改动） |
| D019 final 极瘦 | ✅ 未接入（rag_search 尚未接线 harness·注入守卫在接入时补） |
| 数据红线 | ✅ `.gitignore:19` data/rag_index/ · key 不进 git |
| HF 镜像 | ✅ 代码层 setdefault（不覆盖用户显式） |

---

## 结论与建议实施顺序

**判定：有条件通过**——检索核心可用（召回正确·红线合规）·补齐 4 项后进 Phase 1 验收：

1. **补元数据**：city/region/topic/year（meta 字段·笔记可派生）
2. **模型缓存**：search() 模块级模型单例（防会话内重复 16-23s 冷加载）
3. **补一致性校验**：load_index 校验 vectors/meta 行数一致（不匹配报 --rebuild）
4. **先建 L1.5 事实卡**（Phase 1 内·与 CB-22b 共享）→ 事实卡逐条向量化
5. **黄金集 + tools/rag_eval.py**（Recall@5 ≥80%·bge-small vs large 按数据决定）
6. 接入 harness（B 先 RAG 后·懒加载·Top-K≤5·<3000B 注入守卫）+ 增量维护文档（Phase 2 补）

---

*Codex 组评估回应（2026-08-09）·供 claude组 收敛。*
