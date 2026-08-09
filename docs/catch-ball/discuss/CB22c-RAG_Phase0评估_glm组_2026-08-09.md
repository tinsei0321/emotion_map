# RAG Phase 0 验证评估 — 回应（glm组）

> **评估方**：glm组（ZCode + GLM 5.2 · 第三方独立评估·不做项目方决策背书）
> **日期**：2026-08-09 | **CB 轮次**：CB-22c（RAG·Phase 0 评估）
> **回应对象**：`CB22c-RAG_Phase0_验证结论_2026-08-09.md`（本地 BGE 跑通结论）
> **上轮承接**：glm CB-22c 提"CB-14 硬阻塞 + 方案 A 概念混淆 + Py3.14 wheel 存疑"——本轮核对 Phase 0 是否真破除
> **核心标尺**：演示逻辑链 / 出口三铁律 / AI·Copilot 内核 / 承重红线

---

## 〇、一句话结论

**Phase 0 验证结论可信——glm 上轮 3 个担心（CB-14 硬阻塞/方案 A 概念混淆/Py3.14 wheel）实测全破除：sentence-transformers 5.7.0 + torch 2.13.0+cpu 真装可用（Py3.14 wheel 存疑推翻）+ 方案 A 图片 embedding 概念混淆被验证结论采纳排除 + 本地 BGE 离线不依赖配额。5 焦点 4 agree + 1 partial（向量库 numpy 同意但补"规模上限 + 持久化原子性"警告）。同意进入 Phase 1·但附 3 项必须补强（召回率黄金集/bge-small vs large 抽样验证/requirements 固化 HF 镜像）·防"单点相似度 0.728 = 质量定论"的过早乐观。**

---

## 现状核实：glm 上轮 3 个担心的破除情况

**glm CB-22c 上轮提 3 个担心**·Phase 0 实测全破除：

| 担心（glm CB-22c） | Phase 0 破除证据 | glm 实测确认 |
|---|---|---|
| **CB-14 硬阻塞**（.env 无 embedding key） | 本地 BGE 离线·不依赖 key | ✅ glm 实测 sentence-transformers import OK |
| **方案 A 概念混淆**（multimodal=图片≠文本） | 验证结论:22 采纳 glm 判断·排除方案 A | ✅ 验证结论明确标"❌ 概念混淆·不可用" |
| **Py3.14 wheel 存疑**（CB-14 :62） | torch 2.13.0+cpu + sentence-transformers 5.7.0 实装 | ✅ glm 实测 `torch.__version__ = 2.13.0+cpu` |

**glm 实测确认**：
```
[OK] sentence-transformers 5.7.0
[OK] torch 2.13.0+cpu
[OK] numpy 2.4.6
```

**Phase 0 结论可信**——glm 上轮的 3 个技术担心**全部被实测推翻或采纳**。这是 CB-14 硬阻塞解除的客观证据。

---

## 一、逐焦点回应

### 焦点 1：embedding 定案本地 BGE — **agree（bge-small 作主 + Phase 1 补抽样验证）**

**验证结论**：bge-small-zh-v1.5（512 维）语义检索有效（葛洲坝 0.728 vs 停车 0.374 vs 北京 0.263）。

**glm组 判断：agree——bge-small 作主方案合理（离线免费 + 中文专调 + 512 维够）·但单点 0.728 不能定质量·Phase 1 须补抽样验证 + bge-large 对比。**

**bge-small 够不够的判断依据**：
- L0 知识库是**专业领域**（城市更新/城市体检）·术语集中（葛洲坝/体检/更新单元/片区策划）。
- bge-small-zh-v1.5 是中文专调·在 MTEB 中文榜 ranking 靠前——**领域小 + 中文专调 = small 够用**（业界经验：<10 万文档 small 够·L0 数百文件远低于此）。
- 512 维 vs 1024 维：512 维检索速度更快·内存更省·数百文件规模下精度差 <2%（业界经验）。

**glm组 建议补充（Phase 1 质量验证·非阻断 Phase 0）**：

**① 召回率黄金集（glm CB-22c 已提·重申）**：
- 预设 10-20 个查询 + 黄金答案（如"葛洲坝"应命中葛洲坝笔记 + "停车缺口"应命中 1072 那条）。
- 断言 Top-K 召回率 ≥80%（bge-small 的底线）。
- **单点 0.728 不能定质量**——可能存在"该命中的没命中"（召回率盲区）。

**② bge-small vs bge-large 抽样对比（可选·非必须）**：
- 若召回率 <80%·再验证 bge-large-zh-v1.5（1024 维·精度更高但慢 3-5 倍）。
- glm 倾向：**先用 small 跑召回率**——若 ≥80% 则定 small·若 <80% 才升 large。
- 禁上来就 large（过杀·延迟 + 内存翻倍·数百文件不值得）。

**结论**：**bge-small 作主方案 agree**·Phase 1 补召回率黄金集验证·不达标再升 large。

### 焦点 2：向量库 numpy 自建 — **agree + 警告（规模上限 + 持久化原子性）**

**验证结论**：numpy 已装（2.4.6）·L0 数百文件 → 几千条向量·numpy 暴力检索毫秒级。

**glm组 判断：agree——numpy 零依赖 + 数百文件规模够·但补 2 警告。**

**numpy 自建的合理性**：
- L0 数百文件 × 段落级切分 ≈ 几千条向量 × 512 维 × 4 字节 ≈ **几 MB ~ 十几 MB**（numpy 内存毫无压力）。
- 暴力检索：`cosine_sim(query, matrix)` 一次矩阵乘·**毫秒级**（GPU 都不需要）。
- vs sqlite-vss/chroma：**零依赖 + 无 Py3.14 兼容风险**（glm 上轮担心 chroma wheel·numpy 已在 requirements 零风险）。
- glm 上轮倾向 sqlite-vss 是"以防 chroma 不兼容"——现 numpy 方案更优（零依赖）·**glm 修正立场支持 numpy**。

**glm组 2 警告（Phase 1 实现·非阻断 Phase 0）**：

**① 规模上限**：
- numpy 暴力检索是 O(N)——数千条向量毫秒级·但若未来 L0 涨到**十万级**（如全量政策原文段落）·可能退化到 100ms+。
- **glm 建议**：Phase 1 加规模监控（向量数 >50000 时 warning·建议转 FAISS/索引）——当前数百文件不触发·但留扩展点。

**② 持久化原子性**：
- 验证结论提 `vectors.npy` + `meta.jsonl`——两文件须**原子写**（防写一半崩溃致不一致）。
- **glm 建议**：写临时文件 + rename（原子）·或加 `index.lock` 防并发写。
  ```python
  # 原子写（防崩溃不一致）
  np.save('vectors.npy.tmp', vectors)
  os.replace('vectors.npy.tmp', 'vectors.npy')  # 原子 rename
  ```

### 焦点 3：HF 镜像固化 — **agree（env 固化 + 文档标注·非 requirements）**

**验证结论问**：HF_ENDPOINT=hf-mirror 固化还是运行时设？

**glm组 判断：agree 固化——env 固化 + 文档标注·非 requirements（requirements 不放 env 变量）。**

**固化方式建议（glm）**：

| 方式 | 合适？ | 理由 |
|---|---|---|
| **.env 文件** | ✅ 推荐 | `HF_ENDPOINT=https://hf-mirror.com`·与现有 AMAP_KEY/DEEPSEEK 同档·运行时 load |
| requirements.txt | ❌ 不合适 | requirements 是 pip 依赖·非 env 变量 |
| 代码硬编码 | ❌ 不合适 | 硬编码不利切换（若未来 hf-mirror 不可用·改代码麻烦） |
| 运行时手动设 | ❌ 不合适 | 易忘·新环境/换机会漏 |

**glm组 建议**：
- `.env` 加 `HF_ENDPOINT=https://hf-mirror.com`（固化）。
- `ai_qa/rag_embed.py`（Phase 1 新建）启动时 `os.environ.setdefault('HF_ENDPOINT', ...)` 兜底（防 .env 未加载）。
- `docs/` RAG 文档标注"首次下载需 hf-mirror·后续离线"。

**模型缓存固化（glm 补）**：
- bge-small 模型 ~100MB·首次 40.4s 下载·后续从缓存加载。
- **glm 建议**：模型缓存目录（`~/.cache/huggingface/`）**不入 git**（太大）·但**入 .gitignore + 文档标注首次下载**。
- 可选：模型文件随项目打包（若要离线分发·~100MB 可接受）。

### 焦点 4：requirements 更新（sentence-transformers 入库）— **agree（入 requirements + 版本锁）**

**glm组 判断：agree——sentence-transformers 入 requirements·须版本锁 + 子依赖标注。**

**glm组 建议（requirements 更新）**：

```
# requirements.txt 新增（RAG embedding·CB-22c Phase 0）
sentence-transformers==5.7.0    # bge-small-zh embedding（Py3.14 wheel 已验证）
torch==2.13.0+cpu               # CPU 版（无 GPU 环境·+cpu 后缀避 GPU 大包）
# numpy==2.4.6（已在·不重复）
```

**版本锁理由**：
- sentence-transformers/torch 大版本变可能破 Py3.14 wheel 兼容（刚验证的 5.7.0+2.13.0 须锁）。
- `+cpu` 后缀：避 pip 拉 CUDA 版（~2GB·无 GPU 环境浪费）。

**glm 提醒**：
- torch 是**重依赖**（~200MB CPU 版）——入 requirements 后 `pip install` 时间显著增加。
- 可选：requirements 拆 `requirements-rag.txt`（RAG 专项）·主 requirements 不强装——但 glm 倾向**主 requirements 入**（RAG 是核心能力·非可选）。

### 焦点 5：Phase 1 执行 — **agree（可进入 + 3 项补强）**

**glm组 判断：agree——Phase 0 通过·可进入 Phase 1·但附 3 项补强（防过早乐观）。**

**Phase 1 执行计划（glm 确认 + 补强）**：

| Phase 1 步骤 | glm 评估 | 补强 |
|---|---|---|
| 向量化 L0（笔记 + 事实卡 + 案例） | ✅ 可做 | 段落级切分 + embed_hash 指纹（CB-22c 焦点 5） |
| rag_search 工具 | ✅ 可做 | Top-K + 来源 + **召回率黄金集断言** |
| 接入 EMC（diagnose 复杂语义意图） | ✅ 可做 | 与 B 路径 query_knowledge_base 分工（glm CB-22b） |
| numpy 向量库 | ✅ 可做 | 原子写 + 规模监控 |
| 体积守卫 | ✅ 可做 | **收紧 <3000B**（glm CB-22c·验证结论未提具体值） |

**3 项必须补强（glm 立场）**：

**① 召回率黄金集（最关键）**：
- 单点相似度 0.728 **不能定质量**——可能"该命中的没命中"。
- Phase 1 必须预设 10-20 黄金查询 + 断言召回率 ≥80%。
- 这是 RAG 质量的**客观底线**——无此断言 = RAG 可能返回垃圾也通过。

**② bge-small vs large 抽样（若召回率不达标）**：
- 先用 small 跑召回率·≥80% 定 small·<80% 升 large。
- 禁上来 large（过杀）。

**③ 体积守卫收紧**：
- 验证结论未提 RAG 注入体积守卫具体值（CB-22c 讨论发起称 <8000B·glm 建议收紧 <3000B）。
- Phase 1 实现 rag_search 结果注入时·断言 <3000B（与 final_brief 同档）。

---

## 二、风险清单

### 阻断级
无（Phase 0 已通过·glm 上轮 3 担心全破除）。

### 警告级

| # | 风险 | glm组 建议 |
|---|---|---|
| **W1** | 单点相似度 0.728 被当质量定论 | Phase 1 补召回率黄金集（≥80%）·不达标升 bge-large |
| **W2** | numpy 规模上限（未来十万级退化） | 加规模监控（>50000 warning）·当前不触发·留扩展点 |
| **W3** | 持久化非原子（vectors.npy/meta.jsonl 写半崩溃） | 临时文件 + os.replace 原子 rename |

### 建议级

| # | 建议 | 优先级 |
|---|---|---|
| **S1** | bge-small 作主 + 召回率不达标升 large（抽样验证·非上来 large） | P0（Phase 1） |
| **S2** | HF_ENDPOINT 固化 .env + 代码 setdefault 兜底 + 文档标注 | P0 |
| **S3** | requirements 版本锁（sentence-transformers==5.7.0 + torch==2.13.0+cpu） | P0 |
| **S4** | 模型缓存不入 git（.gitignore）+ 文档标注首次下载 | P1 |
| **S5** | rag_search 注入 <3000B 体积守卫 | P1 |

---

## 三、可否执行结论

### ✅ 可进入 Phase 1——Phase 0 验证可信·附 3 项补强

**glm组 核心立场**：

Phase 0 验证结论**可信**——glm CB-22c 上轮 3 个技术担心（CB-14 硬阻塞/方案 A 概念混淆/Py3.14 wheel）**实测全破除**：
- 本地 BGE 离线跑通（不依赖配额）
- 方案 A 图片 embedding 被采纳排除
- Py3.14 wheel 兼容性实测通过（torch 2.13.0+cpu）

**5 焦点判定**：
- 焦点 1 embedding 定案 BGE：**agree**（small 作主 + Phase 1 召回率验证）
- 焦点 2 向量库 numpy：**agree + 2 警告**（规模上限 + 原子性·glm 修正上轮 sqlite-vss 立场支持 numpy）
- 焦点 3 HF 镜像固化：**agree**（.env 固化 + 代码兜底·非 requirements）
- 焦点 4 requirements：**agree**（版本锁 + torch +cpu）
- 焦点 5 Phase 1：**agree**（可进入 + 3 补强：召回率/抽样/体积守卫）

**承重红线**：Phase 0/1 不触碰（新工具/新模块·非 diagnose/四态/track/prompt）✅

**glm组 关键提醒（防过早乐观）**：

Phase 0 的"语义检索质量正确（0.728）"是**单点验证**——不能定 RAG 质量。Phase 1 必须补：
1. **召回率黄金集**（10-20 查询·召回率 ≥80%）——这是 RAG 质量的客观底线。
2. bge-small 不达标才升 large（抽样·非上来 large）。
3. rag_search 注入 <3000B（与 final_brief 同档·防膨胀）。

**glm 修正上轮立场**：
- CB-22c 上轮 glm 倾向 sqlite-vss（因担心 chroma wheel）——现 numpy 方案更优（零依赖·glm 改支持 numpy）。
- 这是基于实测的立场修正（非固执己见）——numpy 已在 requirements + Py3.14 可用 = 最低风险。

---

## 附：现状核实证据（glm组 独立实测）

| 发现 | 证据 |
|---|---|
| **sentence-transformers 真装可用** | glm 实测 `sentence_transformers.__version__ = 5.7.0` |
| **torch Py3.14 wheel 可用** | glm 实测 `torch.__version__ = 2.13.0+cpu`（CB-14 :62 担心推翻） |
| numpy 已装 | `numpy.__version__ = 2.4.6`（已在 requirements） |
| **sentence-transformers 未入 requirements** | glm 实测 requirements 仅 numpy·无 sentence-transformers/torch |
| HF 镜像未固化 | grep HF_ENDPOINT 仅在讨论文档·.env/代码未配 |
| 模型缓存位置 | `~/.cache/torch/sentence_transformers/` 仅有 .locks（模型在 HF hub cache·未入 git·正确） |
| 方案 A 概念混淆被采纳排除 | 验证结论 :22 采纳 glm CB-22c 判断 |

### 声明

本回应由 glm组（ZCode + GLM 5.2）独立产出·2026-08-09·基于代码级实测 sentence-transformers/torch/numpy 可用性 + requirements 现状 + HF 镜像配置 + 模型缓存位置。第三方独立评估·不做项目方决策背书。glm 修正 CB-22c 上轮 sqlite-vss 立场（因 numpy 实测更优）——基于事实的立场修正是 glm 一贯原则。

---

*登记：docs/context-map.md · CB-22c Phase 0 评估 glm组 回应。*
