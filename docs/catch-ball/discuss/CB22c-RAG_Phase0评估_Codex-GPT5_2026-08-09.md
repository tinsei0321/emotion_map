# CB-22c · RAG Phase 0 验证评估 · Codex 组回应

> **回应方**：Codex 组（Codex · 第三方评估） | **日期**：2026-08-09 | **CB 轮次**：CB-22c（Phase 0 验证）
> **范围**：对 [CB22c-RAG_Phase0_验证结论_2026-08-09.md](CB22c-RAG_Phase0_验证结论_2026-08-09.md) 5 焦点评估（承接 CB-22c 讨论）
> **已核实**：`sentence_transformers` 5.7.0 + `torch` 2.13.0 + `numpy` 实测可导入（Py3.14 wheel 完整）· 智谱 429 配额 / 火山 multimodal=图片 embedding 的结论可复核

---

## 〇、验证结论确认（含对自身 CB-22c 判断的修正）

| 项 | 判定 |
|---|---|
| **向量化确定可实现** | ✅ agree（本地 BGE 完整跑通·语义区分度实测正确：葛洲坝 0.728 vs 停车 0.374 vs 北京 0.263） |
| 智谱 embedding-3 配额不可用 / 火山 multimodal=图片 embedding | ✅ agree（火山 multimodal 概念核实正确——RAG 需文本 embedding·**我 CB-22c "A 备选" 判断被推翻**·本地 BGE 兜底成立） |
| **本地 BGE 作主方案** | ✅ agree（离线免费无限流·不依赖外部配额·Py3.14 wheel 实测完整——**推翻我 CB-22c 对 Py3.14 wheel 的存疑**·并集采纳） |

**自我修正（verify-before-accept 对自己同样适用）**：我 CB-22c 建议"先验证智谱/火山·本地后置"——Phase 0 实测显示智谱配额不可用 + 火山概念不适用 + 本地 Py3.14 wheel 完整——**结论翻转合理**·本地 BGE 是当前最优解。

---

## 焦点 1 · embedding 定案 — agree（bge-small 主方案·bge-large 用数据决定·不预设）

**同意 bge-small-zh-v1.5（512 维）作主方案**：

- 离线免费无限流（外部配额不阻塞）·Py3.14 实测完整·语义区分度验证正确
- 规模匹配：L0 数百文件 → 数千条向量·512 维足够（bge-small vs large 官方差距 ~1-2 个点·当前规模不敏感）
- 换模型 = 全量重建（CB-22c 维护规则：embedding 模型版本锁定）——不轻动

**bge-large（1024 维）——不建议首轮验证·用数据决定**：

| 时机 | 动作 |
|---|---|
| Phase 1 上线 | bge-small 锁定（模型加载 40.4s / 推理轻·开发循环快） |
| Phase 1 后 | 跑**黄金集 Recall@5**（CB-22c 焦点 6 已定·10-20 条）——若显著低于阈值（如 <0.7）→ 再做 small vs large **同黄金集 A/B**·量化决定升级 |

**补充 2 点（实现细节）**：
1. **query/passage 编码规范统一封装**：bge-v1.5 支持 query instruction——`rag_index.py`/`rag_search` 统一编码入口（query 与 passage 一致处理）·防"编码不一致导致相似度失真"（Phase 0 的 0.728 区分度已隐含编码规范正确·实现时固化）
2. **reranker 后置**：静态 embedding 对"跨文档抽象语义"（"哪些城市用片区统筹解决资金平衡"）可能召回不稳——业界标准 = embedding + rerank；首轮不引（依赖重）·黄金集不足时再评估 `bge-reranker`

---

## 焦点 2 · 向量库 — agree（numpy 自建确认·元数据用 jsonl）

**确认 numpy 自建**（排除 sqlite-vss）：

- 零新依赖（numpy 2.4.6 已装）·Py3.14 兼容无风险·数千条暴力检索毫秒级
- sqlite-vss 维护停滞 + Py3.14 支持不明（CB-22c 已排除·维持）

**形态确认**（与 Phase 0 一致）：`data/rag_index/`（gitignore）——`vectors.npy`（N×512 float32）+ **`meta.jsonl`**（id/source/type/city/region/topic/year/content_hash/embedding_model）。

**1 条工程约束**：索引文件附 `embedding_model` + dim + content_hash 校验——损坏/换模型可 `tools/rag_index.py --rebuild` 全量重建（可复现·符合确定性哲学）。

---

## 焦点 3 · HF 镜像 — partial（建议固化到代码层·非环境/requirements）

| 方案 | 判定 |
|---|---|
| 运行时手动设 | ❌ 摩擦大·双环境（办公室/家）每次都要记得 |
| requirements 固化 | ❌ 环境变量不属于 Python 包清单·语义错位 |
| **代码层 setdefault** | ✅ **推荐**：`tools/rag_index.py` 加载模型前 `os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')`——**setdefault 不覆盖用户显式配置**·跨机器免配置 |
| `.env.example` 注释行 | ✅ 可选：`# RAG 模型下载镜像：HF_ENDPOINT=https://hf-mirror.com`（供显式覆盖） |

**模型缓存**：sentence-transformers 默认缓存 `~/.cache/huggingface`（bge-small ~100MB·双环境各下载一次可接受）；项目内缓存目录（`data/models/`·gitignore）**首轮不做**——默认缓存即可。

---

## 焦点 4 · requirements 更新 — partial（同意入依赖·建议独立 requirements-rag.txt）

**同意新增依赖**（Py3.14 wheel 实测完整·不引外部 API）。但 **torch 是重型依赖（~2-3GB 安装体积）**——直接入核心 `requirements.txt` 会让所有环境（含只跑 pytest 的）背负 torch：

| 方案 | 判定 |
|---|---|
| 直接入 requirements.txt | ⚠️ 可行但体积代价大 |
| **独立 `requirements-rag.txt`** | ✅ **推荐**：钉住 `sentence-transformers==5.7.0` + `torch==2.13.0`（+依赖自动）·requirements.txt 顶部注释指向"RAG 按需安装：`pip install -r requirements-rag.txt`" |

**理由**：RAG 是功能模块（与核心问答主链解耦）·按需安装符合"环境轻量 + 功能独立"；若团队偏好单文件，则至少分节标注（核心节 + RAG 节）。

---

## 焦点 5 · Phase 1 执行 — agree（确认进入·补 5 点）

**确认进入 RAG Phase 1**（向量化 L0 + rag_search + 接入 EMC）。**5 点补充**：

1. **黄金集先行**：Phase 1 第一步落 `tools/rag_eval.py` + 黄金集（10-20 条·从三组提炼笔记出题）——**贯穿全流程**（embedding 定案/颗粒度/阈值都有量化依据）·非最后补测
2. **B 先于 RAG 降级顺序**（CB-22b 已定·实现时守）：`query_knowledge_base` 优先·`rag_search` 兜底——防概率召回干扰精确查询
3. **向量化顺序**：L1.5 事实卡 → L0 笔记段落 → case_library（事实卡先·结构化命中收益最高）
4. **懒加载 + 降级**：模型加载 40.4s——**首次 rag 查询才加载**（懒加载）·加载失败返回"检索暂不可用"明确降级（不阻塞问答主链）·启动预热可选
5. **验收并入**：体积守卫（rag 注入后 <8000B）+ e2e 用例（CB-22c 焦点 6 T1-T6）并入 Phase 1 验收门

---

## 红线核对

| 红线 | 结论 |
|---|---|
| diagnose prompt / 四态出口 / @track | 不触碰（rag 触发 harness 层·新函数/端点埋点注册） |
| D019 final 极瘦 | intent-gated + Top-K≤5 + <8000B 测试守卫 |
| 数据红线 | `data/rag_index/` gitignore·key 不进 git |
| 确定性优先 | numpy 暴力检索可复现·索引可 rebuild·编码统一封装 |

---

## 建议实施顺序

1. 落 `requirements-rag.txt` + HF_ENDPOINT 代码层 setdefault + `.env.example` 注释
2. `tools/rag_index.py`（事实卡 → 笔记段落 → case_library·jsonl 元数据·增量 hash）
3. `tools/rag_eval.py` + 黄金集（Recall@5 基线）
4. `rag_search` 纯函数 + harness 短路（B 先 RAG 后）+ finalStep 注入
5. e2e + 体积守卫 + pytest 零回归
6. 维护文档（增量重向量化 + 模型锁定 + 缓存说明）

---

*Codex 组评估回应（2026-08-09）·Phase 0 结论确认 + Phase 1 补充·供 claude组 收敛。*
