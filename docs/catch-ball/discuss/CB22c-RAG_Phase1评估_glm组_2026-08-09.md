# CB-22c RAG Phase 1 实现评估 — 回应（glm组）

> **评估方**：glm组（ZCode + GLM 5.2 · 第三方独立评估·不做项目方决策背书）
> **日期**：2026-08-09 | **CB 轮次**：CB-22c（RAG Phase 1·三组共同评估）
> **回应对象**：`tools/rag_index.py`（实现）+ `CB22c-RAG_Phase1_执行定稿_2026-08-09.md`
> **上轮承接**：glm Phase 0 评估提 3 项补强（召回率黄金集 / bge 抽样 / 体积守卫）——本轮核对落实
> **核心标尺**：演示逻辑链 / 出口三铁律 / AI·Copilot 内核 / 承重红线

---

## 〇、一句话结论

**Phase 1 实现主体正确（BGE 编码/原子写/embed_hash/@track 注册都落实）·但 glm Phase 0 提的 3 项补强仅落实 1 项（embed_hash）·召回率黄金集 + 体积守卫缺失——"停车"检索 0.595 偏低且 Top-3 未命中"南湖停车缺口 1072"（南湖笔记有此数据但排名靠后）正是 glm 担心的召回盲区。@track 注册实测确认正确（glm 上轮查询返空是未 import 模块所致·非实现问题）。同意 Phase 1 核心可用·但 RAG 质量底线（召回率黄金集）必须在接入 EMC 前补·否则"0.819/0.745 高"是 cherry-pick·0.595 低才是隐患。6 焦点 3 agree + 3 partial。**

---

## 一、逐焦点回应

### 焦点 1：编码规范（query/passage 统一封装 + bge instruction）— **partial（统一编码对·但 bge-v1.5 instruction 未用）**

**实现**（:90-92）：`_embed_texts` 统一 `model.encode(texts, normalize_embeddings=True)`·query/passage 一致。

**glm组 判断：partial——统一编码正确（query/passage 同模型同方法）·但 bge-v1.5 官方推荐 query 加 instruction（"为这个句子生成表示以用于检索相关文章："）·实现未用·相似度可能略失真。**

**bge-v1.5 instruction 机制**：
- BGE 官方文档：query 编码前加 instruction prefix（中文："为这个句子生成表示以用于检索相关文章："）·passage 不加。
- 效果：检索质量提升 ~2-5%（MTEB 中文榜·bge-small-zh-v1.5 用 instruction 比不用高）。
- 实现 :92 `model.encode(texts, normalize_embeddings=True)` —— **未区分 query/passage·未加 instruction**。

**影响评估**：
- "0.819/0.745 高 / 0.595 低"——部分原因可能是**未加 instruction 致 query-passage 不对称**。
- glm 实测"停车"Top-3：南京大数据 0.595 / 南湖公园 0.576 / 体检附件 0.553——**南湖笔记含"停车缺口 1072"但排名靠后**·instruction 可能改善。

**glm组 建议（Phase 1 补·非阻断）**：
```python
# bge-v1.5 query 加 instruction（passage 不加）
QUERY_INSTRUCTION = '为这个句子生成表示以用于检索相关文章：'
def _embed_query(model, q):
    return model.encode([QUERY_INSTRUCTION + q], normalize_embeddings=True)[0]
def _embed_passages(model, texts):  # build_index 用
    return model.encode(texts, normalize_embeddings=True)
```
- build_index 用 `_embed_passages`（无 instruction）·search 用 `_embed_query`（加 instruction）。
- **改后重 build + 重测**——若 0.595 提升到 0.7+ 则 instruction 有效。

**相似度失真风险**：现状未加 instruction 不是"错"（仍可用）·是"次优"——bge-v1.5 不加 instruction 也能跑·只是 query-passage 对齐差一点。**Phase 1 可用·Phase 1.5 优化**。

### 焦点 2：原子写 + embed_hash — **agree（原子写充分）+ partial（增量缺口）**

**实现**（:133-141）：临时文件 `vectors.tmp.npy`/`meta.jsonl.tmp` + `os.replace` 原子 rename。

**glm组 判断：agree 原子写充分（glm Phase 0 警告 W3 落实）·partial 增量重向量化缺口。**

**原子写核实**：
- :134-135 临时文件名 `*.tmp.npy`/`*.jsonl.tmp` ✅
- :140-141 `os.replace` 原子 rename ✅（glm Phase 0 建议采纳）
- vectors.npy + meta.jsonl 两文件分别 rename——**理论上两 rename 间崩溃会不一致**（vectors 新 + meta 旧）·但实际 `os.replace` 极快（微秒）·崩溃概率极低。**可接受**。

**增量重向量化缺口（glm Phase 0 焦点 5 / CB-22c 焦点 5）**：
- 实现 :96 `build_index()` 是**全量构建**（每次重跑全量编码 190 条）。
- embed_hash（content_hash :124）**已存入 meta**——但 **load_index 后无"比对 hash 决定是否重嵌"逻辑**。
- 即：content_hash 字段有值·但**增量重向量化未实现**——更新 L0 后须手动 `--rebuild`（全量重跑 40s+）。

**glm组 建议（Phase 1.5 增量·非阻断 Phase 1）**：
```python
def build_index(incremental=True):
    # 增量：读旧 meta content_hash + 新 chunks hash 比对
    old_hashes = {m['source']: m['content_hash'] for m in load_metas()}
    new_chunks = collect_chunks()
    to_embed = [c for c in new_chunks if old_hashes.get(c['source']) != hash(c['text'])]
    # 只重新编码变更的·合并旧向量
    ...
```
- 当前 190 条全量 40s·增量后更新几条 <5s——**后期可维护**（用户要求）·Phase 1.5 必做。

### 焦点 3：元数据 schema — **agree（够 + 防漂移）**

**实现**（:122-131）：`source/type/content_hash/embedding_model/dim` 五字段。

**glm组 判断：agree——schema 完整·glm CB-22c 焦点 5 建议全采纳。**

**字段核实**（glm 实测 meta.jsonl 样本）：
- `source`：`docs/urban-renewal-plan/.../00-01_...md#0`（路径 + 段落号）✅ 可溯源
- `type`：'note'/'case' ✅ 分类
- `content_hash`：sha256 ✅ 防漂移（增量对比依据）
- `embedding_model`：'BAAI/bge-small-zh-v1.5' ✅ 模型标识（换模型时识别）
- `dim`：512 ✅ 维度

**防漂移能力**：
- content_hash 字段存在 → 增量重向量化有依据（焦点 2 缺口是逻辑未实现·非 schema 缺）。
- embedding_model 字段 → 换 bge-large 时识别旧索引须重建。

**glm组 补建议（非阻断）**：加 `build_time` 字段（索引构建时间戳·审计可溯）——当前缺·Phase 1.5 加。

### 焦点 4：索引质量（190 条覆盖 + 缺 L1.5 事实卡）— **partial（笔记+案例够起步·L1.5 事实卡缺 + 段落切分粗）**

**实现**：190 条（note 185 + case 5）。

**glm组 判断：partial——起步够·但 2 缺口。**

**缺口 ① L1.5 事实卡缺（CB-22b 尚未建）**：
- 190 条全是 L0 笔记段落 + case_library·**无 L1.5 事实卡**（CB-22b PROJECTS/INDICATORS 未建）。
- 影响：用户"宜昌有哪些更新项目"→ RAG 检索笔记段落（粗）·**非事实卡精确数据**。
- 但这是 CB-22b/CB-22c 顺序问题（CB-22b 先于 CB-22c）——**glm CB-22c 上轮已定 B 路径先行**·CB-22b 未建则 RAG 无事实卡可嵌·属**依赖未就绪**·非 CB-22c 实现缺陷。

**glm组 建议**：CB-22b（L1.5 事实卡）建后·`build_index` 加 `_load_facts()`（PROJECTS/INDICATORS → 向量）·补事实卡检索。

**缺口 ② 段落切分粗（:56-67）**：
- 切分逻辑：`text.split('\n## ')`（按 `## ` 小节）·每段 ≤2000 字。
- **问题**：`## ` 是 markdown 二级标题——有些笔记用 `### `（三级）或无标题·切分不均。
- glm 实测：南湖笔记含"停车缺口 1072"·但"停车"检索 Top-3 南湖排第 2（0.576）·**说明该数据被切进了一个大段·相似度被稀释**。
- **glm组 建议**（Phase 1.5）：补段落切分策略——长段（>500 字）再按句号/换行细分·或按字段（"停车缺口 1072"单独成段）。

**覆盖评估**：
- 190 条 / L0 数十篇笔记 ≈ 每篇 4-5 段——**段落级覆盖合理**。
- case 5 条（上海/广州/南京/宁夏/宜昌望洲岗）——少·但 case_library 就这 5 个。

### 焦点 5：检索质量（0.819/0.745 高 vs 0.595 停车低）— **disagree 前提（需黄金集·勿 cherry-pick）**

**验证结果**：0.819（更新项目）/ 0.745（葛洲坝体检）/ 0.595（停车偏低）。

**glm组 判断：disagree 前提——"0.819/0.745 高"可能是 cherry-pick·0.595 低才是隐患·必须用黄金集 Recall 量化。**

**glm Phase 0 补强①（召回率黄金集）未落实**：
- Phase 0 glm 明确提"预设 10-20 黄金查询 + 断言召回率 ≥80%"——**Phase 1 实现里无黄金集断言**。
- 现状 3 个点测（0.819/0.745/0.595）是**主观选样**·不是客观黄金集——"更新项目"/"葛洲坝"是容易的（笔记标题直含关键词）·"停车"是难的（数据在段落内）。
- **0.595 低 + Top-3 未命中"停车缺口 1072"**——正是 glm 担心的"该命中的没命中"（召回盲区）。

**glm组 实测验证（停车检索）**：
```
py tools/rag_index.py --query "停车" --k 3
Top-3:
1. [0.595] case_library#nanjing_bigdata（南京大数据·泛案例）
2. [0.576] glm_南湖公园#2（南湖笔记·含停车 1072 但段太大稀释）
3. [0.553] codex_体检附件#8（体检附件）
```
- **Top-1 是南京案例（0.595）·非南湖停车数据**——南湖"1072 个缺口"在 #2 段（0.576）·**相似度被段落稀释**（焦点 4 切分粗）。
- 即"停车"检索**用户看到的 Top-1 是南京·不是宜昌南湖**——**本地数据召回失败**。

**glm组 强烈建议（接入 EMC 前必做）**：
1. **黄金集**（10-20 查询·含"停车"/"指标"/"案例"等难词·断言召回率 ≥80%）。
2. **bge instruction**（焦点 1·改善 query-passage 对齐）。
3. **段落细切**（焦点 4·防长段稀释）。
- 三者都做后重测"停车"——若 Top-1 升到南湖 0.7+ 则质量达标。

**bge-small vs large**：glm Phase 0 建议先 small 跑召回率·不达标升 large——现状 small 未跑召回率就判"高"·**判断依据不足**。

### 焦点 6：承重红线（@track 注册 + diagnose/四态未碰）— **agree（@track 正确·glm 上轮查询瑕疵已澄清）**

**claude 自查**：@track MOD_AIQA.F_014/015 已注册（e42b974b）。

**glm组 判断：agree——@track 注册正确·glm 上轮查询返空是实测方法瑕疵（未 import 模块）·非实现问题。**

**glm组 实测复核（本次修正方法）**：
```python
# glm 上轮（返空·方法错）：
from core.tracker import _TRACKING_REGISTRY
# 未 import tools.rag_index → 模块级 register_track_id 未执行 → 空

# glm 本次（修正·import 触发）：
import tools.rag_index  # 触发模块级 register_track_id
# → _TRACKING_REGISTRY +2
# F_014: 'build_rag_index（...）'  F_015: 'rag_search（...）' ✅
```

**@track 注册机制澄清**：
- `tools/rag_index.py:24-25` 模块级 `register_track_id(...)`——import 时执行。
- glm 上轮 `from core.tracker import _TRACKING_REGISTRY` **只查不 import tools.rag_index** → 注册未触发 → 空。
- **这是 glm 上轮实测方法瑕疵**·非 claude 实现问题。**glm 诚实承认上轮查询方法错·本次修正确认 @track 正确。**

**承重红线核实**：
- @track F_014/F_015 ✅ 注册（连续编号·无跳号）
- diagnose prompt：rag_index 是 tools/ 脚本·不碰 diagnose ✅
- 四态出口：search 返 `{ok, results, count}`·非出口裁定 ✅
- D019 final：未注入 prompt（接入 EMC 时才涉及·Phase 1 未接）✅

---

## 二、风险清单

### 阻断级（接入 EMC 前必修）

| # | 风险 | glm组 建议 |
|---|---|---|
| **B1** | **召回率黄金集缺失**（0.595 停车低 + Top-1 南京非南湖 = 本地召回失败） | 接入 EMC 前必建黄金集（10-20 查询·召回率 ≥80% 断言） |

### 警告级

| # | 风险 | glm组 建议 |
|---|---|---|
| **W1** | bge-v1.5 instruction 未用（query-passage 不对称·相似度失真） | search 加 QUERY_INSTRUCTION 前缀·重 build + 重测 |
| **W2** | 段落切分粗（## 小节·长段稀释·"停车 1072"被埋） | 长段 >500 字再细分·或关键字段单独成段 |
| **W3** | 增量重向量化未实现（content_hash 有字段无逻辑·全量 40s） | Phase 1.5 加 hash 比对增量（用户要求"后期可维护"） |
| **W4** | L1.5 事实卡缺（CB-22b 未建·RAG 无精确数据可嵌） | CB-22b 先行·建后补 `_load_facts()` |

### 建议级

| # | 建议 | 优先级 |
|---|---|---|
| **S1** | 黄金集（10-20 查询·含难词"停车/指标/案例"·召回率 ≥80%） | P0（接入前） |
| **S2** | bge instruction（query 加前缀·passage 不加）+ 重 build 重测 | P0 |
| **S3** | 段落细切（长段再分·关键字段单独成段） | P1 |
| **S4** | 增量重向量化（hash 比对·Phase 1.5·用户要求） | P1 |
| **S5** | build_time 字段（审计可溯） | P2 |
| **S6** | L1.5 事实卡接入（CB-22b 建后） | P1（依赖 CB-22b） |

---

## 三、可否执行结论

### ⚠️ Phase 1 核心可用·但接入 EMC 前须补召回率黄金集（B1）

**glm组 核心立场**：

Phase 1 实现主体正确——BGE 编码/原子写/embed_hash/@track 注册都落实（glm Phase 0 评估 3 补强落实 embed_hash 1/3）。**但 RAG 质量底线未验证**：
- 0.819/0.745 高 + 0.595 低 → **可能 cherry-pick**（易词高·难词低）。
- glm 实测"停车"Top-1 是南京案例（0.595）·非南湖本地数据（0.576 排第 2）——**本地召回失败**。
- glm Phase 0 明确提"召回率黄金集 ≥80%"——**Phase 1 未落实**。

**6 焦点判定**：
- 焦点 1 编码规范：**partial**（统一编码对·bge instruction 未用·次优）
- 焦点 2 原子写 + embed_hash：**agree**（原子写充分）+ **partial**（增量缺口）
- 焦点 3 元数据 schema：**agree**（5 字段完整 + 防漂移）
- 焦点 4 索引质量：**partial**（笔记+案例够起步·L1.5 缺 + 切分粗）
- 焦点 5 检索质量：**disagree 前提**（需黄金集·勿 cherry-pick·0.595 是隐患）
- 焦点 6 承重红线：**agree**（@track 正确·glm 上轮查询瑕疵已澄清）

**承重红线**：@track F_014/F_015 ✅ / diagnose ✅ / 四态 ✅ / D019 ✅——**零触碰**。

**glm组 关键提醒**：

1. **glm 上轮 @track 查询瑕疵诚实澄清**——glm Phase 0 评估实测返空是"未 import 模块"方法错·非 claude 实现问题。本次修正确认 @track 注册正确。**glm 基于事实承认上轮方法错·这是 glm 一贯原则（立场基于事实·不固执）**。

2. **召回率黄金集是 RAG 接入 EMC 的生命线**——0.595 停车低 + Top-1 南京（非本地）= 用户问"宜昌停车"看到南京案例 = **演示失败**。接入前必须黄金集验证（含难词 + 本地召回断言）。

3. **三优先行（接入前）**：黄金集 + bge instruction + 段落细切——三者做后重测·"停车"Top-1 应升到南湖 0.7+。若仍低·再升 bge-large。

**glm组 建议 Phase 1.5（接入前补强）**：
1. 黄金集（10-20 查询·召回率 ≥80%）
2. bge instruction（query 加前缀）
3. 段落细切（长段再分）
4. 重 build + 重测·"停车"Top-1 本地化
5. L1.5 事实卡（CB-22b 先行）

---

## 附：现状核实证据（glm组 独立实测）

| 发现 | 证据 |
|---|---|
| **@track 注册正确**（glm 上轮瑕疵澄清） | glm 实测：`import tools.rag_index` 后 _TRACKING_REGISTRY +2（F_014/F_015） |
| glm 上轮查询返空原因 | 未 import tools.rag_index → 模块级 register_track_id 未触发（glm 方法错·非实现错） |
| 索引 190 条 512 维 | glm 实测 `--stats`：note 185 + case 5 |
| 元数据 5 字段完整 | glm 实测 meta.jsonl：source/type/content_hash/embedding_model/dim |
| **停车检索 0.595 偏低 + Top-1 南京** | glm 实测 `--query "停车"`：Top-1 case_library#nanjing_bigdata 0.595（非本地） |
| 南湖"停车 1072"被稀释 | 南湖笔记 #2 段 0.576 排第 2（段太大·含停车数据但相似度稀释） |
| 原子写实现 | :134-141 临时文件 + os.replace（glm Phase 0 W3 落实） |
| embed_hash 实现 | :124 content_hash 字段（glm Phase 0 焦点 5 落实） |
| **增量重向量化未实现** | :96 build_index 全量·content_hash 有字段无 hash 比对逻辑 |
| **bge instruction 未用** | :92 `model.encode(texts)` 无 QUERY_INSTRUCTION 前缀 |
| **召回率黄金集缺失** | 实现无黄金集断言·3 点测（0.819/0.745/0.595）主观选样 |

### 声明

本回应由 glm组（ZCode + GLM 5.2）独立产出·2026-08-09·基于实测 tools/rag_index.py（@track 注册 + 索引 stats + 停车检索 + 元数据样本）。第三方独立评估·不做项目方决策背书。**glm 诚实澄清上轮 @track 查询方法瑕疵**（未 import 模块致返空·非 claude 实现错）——基于事实的立场修正是 glm 一贯原则。

---

*登记：docs/context-map.md · CB-22c Phase 1 评估 glm组 回应。*
