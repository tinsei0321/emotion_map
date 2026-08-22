"""RAG 向量索引构建/查询工具（CB-22c Phase 1·本地 BGE embedding + numpy 暴力检索）。

用途：把 L0 知识库（docs/urban-renewal-plan/ 提炼笔记 + L1.5 事实卡 + case_library）向量化，
供 EMC 问答 rag_search 检索引用。业界主流 RAG 路线·本地 BGE 离线免费·不依赖外部 API 配额。

用法：
  py tools/rag_index.py --build          # 构建索引（向量化 L0 + 事实卡 + case·原子写）
  py tools/rag_index.py --query "葛洲坝有哪些更新项目"   # 检索 Top-K（试运行）
  py tools/rag_index.py --rebuild        # 全量重建（换模型/损坏）
  py tools/rag_index.py --stats          # 索引统计（向量数/维度/来源分布）

纯函数·ASCII 标记（[OK]/[ERR]·禁 emoji）·不调 LLM。
track：MOD_AIQA.F_014（build_rag_index）/ F_015（rag_search）
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.tracker import track, register_track_id

register_track_id('MOD_AIQA.F_014', 'build_rag_index（RAG 向量索引构建·本地 BGE·原子写·embed_hash）')
register_track_id('MOD_AIQA.F_015', 'rag_search（RAG 向量检索·余弦 Top-K·返回片段+来源）')

# HF 镜像（国内网络·不覆盖用户显式配置）
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

REPO = Path(__file__).resolve().parents[1]
RAG_DIR = REPO / 'data' / 'rag_index'
VECTORS = RAG_DIR / 'vectors.npy'
META = RAG_DIR / 'meta.jsonl'
MODEL_NAME = 'BAAI/bge-small-zh-v1.5'

# 知识库来源
NOTES_DIR = REPO / 'docs' / 'urban-renewal-plan'
INDEX_FILE = NOTES_DIR / '_INDEX.md'


def _tag(ok, msg):
    print(f'[{"OK" if ok else "ERR"}] {msg}')


# 数据维度关键词推断（对齐四维度：住房/小区/社区/街区/城区 + 城中村专项·原则：结论颗粒度=数据来源维度）
_DIM_KEYWORDS = {
    '住房': ['住宅', '危旧房', '房屋', '楼栋', '栋', '住房', '建筑'],
    '小区': ['小区', '物业', '停车', '充电', '学位', '托育', '养老', '运动场'],
    '社区': ['社区', '党群', '街道'],
    '街区': ['街区', '街道', '道路', '步行道', '乱停'],
    '城区': ['城区', '城市', '总体规划', '综合', '整体', '宏观'],
    '城中村': ['城中村', '汉宜村', '改造'],
}


def _infer_dim(text):
    """从文本推断数据维度（关键词加权·返回最可能维度）。"""
    score = {}
    for dim, kws in _DIM_KEYWORDS.items():
        score[dim] = sum(1 for kw in kws if kw in text)
    if not any(score.values()):
        return '社区'  # 默认社区（调研最小单元）
    return max(score, key=score.get)


def _load_notes():
    """读 L0 提炼笔记（按小节切分·段落级向量·标注数据维度）。"""
    chunks = []
    if not NOTES_DIR.exists():
        return chunks
    for md in sorted(NOTES_DIR.rglob('*.md')):
        # 跳过索引/README/模板
        if md.name.startswith('_') or 'README' in md.name or '模板' in md.name:
            continue
        text = md.read_text(encoding='utf-8', errors='ignore')
        # 按 ## 小节切分（~200-500 字/段）
        parts = []
        for block in text.split('\n## '):
            if block.strip():
                parts.append(block.strip())
        for i, p in enumerate(parts):
            if len(p) < 20:
                continue
            chunks.append({
                'text': p[:2000],
                'source': f'docs/urban-renewal-plan/{md.relative_to(NOTES_DIR).as_posix()}#{i}',
                'type': 'note',
                'dim': _infer_dim(p),  # 数据维度标注
            })
    return chunks


def _load_cases():
    """读 case_library（案例块·只取方法论 point·不引他城数据·标注为方法论参考）。"""
    try:
        sys.path.insert(0, str(REPO))
        from ai_qa.outlet_kb.case_library import CASES
        chunks = []
        for key, c in CASES.items():
            # 案例 = 方法论参考（做法/路径/机制）·不引用他城具体数据（原则 2·防张冠李戴）
            text = f"{c.get('city','')}·{c.get('project','')}：{c.get('point','')}（方法论参考·做法/路径/机制·不引用他城具体数值）"
            chunks.append({
                'text': text[:2000],
                'source': f'ai_qa/outlet_kb/case_library.py#{key}',
                'type': 'case',
                'dim': '方法论',  # 案例 = 方法论参考·非数据维度
            })
        return chunks
    except Exception as e:
        _tag(False, f'case_library 读取失败: {str(e)[:60]}')
        return []


def _load_facts():
    """读 L1.5 事实卡（urban_renewal_knowledge.py·7 类·逐条一向量·含 dimension）。"""
    try:
        sys.path.insert(0, str(REPO))
        from ai_qa.outlet_kb.urban_renewal_knowledge import all_facts
        chunks = []
        for f in all_facts():
            chunks.append({
                'text': f"{f['city']}·{f['region']}·{f['name']}：{f['detail']}（{f['keywords']}）",
                'source': f"ai_qa/outlet_kb/urban_renewal_knowledge.py#{f['id']}",
                'type': 'fact',
                'dim': f.get('dimension', '社区'),  # 数据维度（事实卡已标注）
                # CB-22f D3（Codex 富矿）：透传 fact 结构化字段——识别层零 LLM 组装 ctx.extracted 用
                #   （region=地理实体·topic/year/keywords=归因字段·检索辅助 + 动作链衔接）。
                #   注：向量化时拍平进 text 的字段在此保留结构化副本（search 透传 meta）。
                'region': f.get('region', ''),
                'topic': f.get('topic', ''),
                'year': f.get('year', ''),
                'keywords': f.get('keywords', ''),
            })
        return chunks
    except Exception as e:
        _tag(False, f'事实卡读取失败: {str(e)[:60]}')
        return []


def _load_concepts():
    """读概念卡（CB-22 三层架构 P1·type='concept'·产品定位/方法论/边界认知·高度凝练+引用摘抄）。"""
    try:
        sys.path.insert(0, str(REPO))
        from ai_qa.outlet_kb.concept_knowledge import all_concepts
        chunks = []
        for c in all_concepts():
            chunks.append({
                'text': f"{c['name']}：{c['detail']}（{c['keywords']}）",
                'source': f"ai_qa/outlet_kb/concept_knowledge.py#{c['id']}",
                'type': 'concept',
                'dim': '方法论',  # 概念卡 = 定义/背景/边界（静态）·非数据维度
            })
        return chunks
    except Exception as e:
        _tag(False, f'概念卡读取失败: {str(e)[:60]}')
        return []


def _embed_texts(model, texts):
    """统一编码（query/passage 一致处理·bge-v1.5 支持 instruction）。"""
    return model.encode(texts, normalize_embeddings=True)


@track('MOD_AIQA.F_014', track_args=False)
def build_index():
    """构建向量索引（原子写 + embed_hash）。"""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    RAG_DIR.mkdir(parents=True, exist_ok=True)
    _tag(True, f'加载模型 {MODEL_NAME}（首次下载 ~40s·需 HF 镜像）...')
    model = SentenceTransformer(MODEL_NAME)

    # 收集向量化对象（事实卡 + 笔记段落 + 方法论案例 + 概念卡·CB-22 P1）
    facts = _load_facts()
    notes = _load_notes()
    cases = _load_cases()
    concepts = _load_concepts()
    all_chunks = facts + notes + cases + concepts
    _tag(True, f'向量化对象: 事实卡 {len(facts)} + 笔记段落 {len(notes)} + 案例 {len(cases)} + 概念卡 {len(concepts)} = {len(all_chunks)}')

    if not all_chunks:
        _tag(False, '无向量化对象')
        return

    texts = [c['text'] for c in all_chunks]
    _tag(True, f'编码 {len(texts)} 条...')
    vectors = _embed_texts(model, texts)
    _tag(True, f'编码完成·维度 {vectors.shape[1]}')

    # 元数据（含 embed_hash + 数据维度 + build_time）
    import hashlib
    import time
    metas = []
    for c, vec in zip(all_chunks, vectors):
        h = hashlib.sha256(c['text'].encode('utf-8')).hexdigest()
        metas.append({
            'source': c['source'],
            'type': c['type'],
            'data_dim': c.get('dim', '社区'),  # 数据维度（住房/小区/社区/街区/城区/城中村/方法论）
            'content_hash': h,
            # CB-22 三支柱修正（两组对齐后承重发现）：素材内容必须随索引持久化——
            #   此前只存 hash·search 返回无 text·注入 finalStep 的"素材"仅文件名列表·
            #   LLM 无内容可综合（三支柱①空转·验收 V2 结构性不可过）→ 存片段全文供 LLM 综合
            'text': c['text'][:2000],
            'embedding_model': MODEL_NAME,
            'dim': int(vectors.shape[1]),
            'build_time': time.strftime('%Y-%m-%d %H:%M'),
            # CB-22f D3（Codex 富矿）：fact 结构化字段透传（region/topic/year/keywords）——
            #   识别层零 LLM 组装 ctx.extracted 用·仅 type=fact 有值·note/case/concept 空串
            'region': c.get('region', ''),
            'topic': c.get('topic', ''),
            'year': c.get('year', ''),
            'keywords': c.get('keywords', ''),
        })

    # 原子写（防崩溃不一致·np.save 自动加 .npy·临时名用 .npy 结尾）
    tmp_v = RAG_DIR / 'vectors.tmp.npy'
    tmp_m = RAG_DIR / 'meta.jsonl.tmp'
    np.save(str(tmp_v), vectors.astype('float32'))
    with open(tmp_m, 'w', encoding='utf-8') as f:
        for m in metas:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')
    os.replace(str(tmp_v), str(VECTORS))
    os.replace(str(tmp_m), str(META))
    _tag(True, f'索引已写: {VECTORS} ({len(metas)} 条·原子写)')


def load_index():
    """加载索引（向量 + 元数据·校验一致性）。"""
    import numpy as np
    if not VECTORS.exists() or not META.exists():
        return None, []
    vectors = np.load(str(VECTORS))
    metas = []
    with open(META, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                metas.append(json.loads(line))
    # 一致性校验（防写半崩溃·vectors/meta 行数不匹配 → 提示 --rebuild）
    if len(vectors) != len(metas):
        _tag(False, f'索引不一致（向量 {len(vectors)} vs 元数据 {len(metas)}）·请跑 --rebuild')
        return None, []
    return vectors, metas


# 模块级模型单例（lru_cache·防每次 search 冷加载 16-23s）
_model_cache = None
_bm25_cache = None       # (bm25 实例, 活跃 chunk 下标数组)——运行时构建（364 段 <1s·零索引格式变更）
_BM25_MODE = os.environ.get('RAG_SEARCH_MODE', 'rrf')     # dense|bm25|rrf——消融开关·默认 rrf（融合终态）
_RRF_K = 60             # RRF 常数（业界标准起步·观测参数·系数不拍死）
_RRF_W_DENSE = 1.0      # 稠密路权重（消融观测参数）
_RRF_W_BM25 = 0.5       # BM25 路权重（等权=1.0 时 noun -7.2pp·降半权防稀释）


def _hub_penalty(m):
    """语义枢纽 chunk 降权系数（基线 §2.2 实证：身份卡 10/10 miss 的 top1 占位者）。

    EMC-IDENTITY-* 身份卡含「情绪地图/得分/指标」高频词——稠密与 BM25 双路都吸。
    它是库的「关于页」不是专项答案源；降权不排除（叙述类仍可用）。"""
    src = m.get('source', '')
    if 'EMC-IDENTITY' in src:
        return 0.2
    return 1.0


def _get_model():
    global _model_cache
    if _model_cache is None:
        from sentence_transformers import SentenceTransformer
        # local_files_only=True：模型已缓存（~/.cache/huggingface/hub·92M）·禁联网检查——
        # 否则启动时 HEAD hf-mirror.com 超时重试 5 次（~30-60s+·2026-08-12 实测）·网络不通则启动卡死
        _model_cache = SentenceTransformer(MODEL_NAME, local_files_only=True)
    return _model_cache


def _get_bm25(metas):
    """运行时构建 BM25（jieba 分词·superseded 预置过滤·缓存复用）。

    PT-CB9 泳道②件①：字面精确匹配路——治「精确术语被语义枢纽身份卡顶位」
    （基线 10 miss 中 5 条该模式）。小语料 364 段构建 <1s，故选运行时构建零索引格式变更。
    superseded 过滤（loader 契约：检索层职责·字段缺失=active 兼容）。"""
    global _bm25_cache
    if _bm25_cache is not None and _bm25_cache[2] == id(metas):
        return _bm25_cache[0], _bm25_cache[1]
    import jieba
    from rank_bm25 import BM25Okapi

    active = [i for i, m in enumerate(metas) if m.get('status', 'active') == 'active']
    corpus = [list(jieba.cut_for_search(
        metas[i].get('text', '') + ' ' + (metas[i].get('ctx_prefix') or '')))
        for i in active]
    bm25 = BM25Okapi(corpus) if corpus else None
    _bm25_cache = (bm25, active, id(metas))
    return bm25, active


def warmup():
    """serve 启动预热 RAG 模型（CB-22 EMC 修复 R1·消除首检冷加载 18.6s）。

    复用 _get_model 单例（首次调用触发加载 + 缓存）·幂等（已缓存直接返回）。
    失败不抛（调用方异步线程·降级为首次检索冷加载兜底）。
    不加新 @track ID（与 F_014/F_015 同族·Codex 建议避免占号）。
    """
    try:
        _get_model()
        _tag(True, 'RAG 模型预热完成')
    except Exception as e:
        _tag(False, f'RAG 预热失败（非阻塞·首检冷加载兜底）: {str(e)[:60]}')


@track('MOD_AIQA.F_015', track_args=False)
def search(query, k=5):
    """检索 Top-K（余弦相似度 + BM25 字面路·返回片段 + 来源·含数据维度）。

    消融开关 RAG_SEARCH_MODE：dense（默认·纯稠密）/ bm25（纯字面）/ rrf（两路融合·件②）。
    superseded chunk 预置过滤（loader 契约·字段缺失=active 兼容）。"""
    import numpy as np

    vectors, metas = load_index()
    if vectors is None or len(metas) == 0:
        return {'ok': False, 'error': '检索暂不可用（索引未构建·跑 py tools/rag_index.py --build）'}

    # superseded 预置过滤（两路共用·检索层职责）
    active_idx = [i for i, m in enumerate(metas) if m.get('status', 'active') == 'active']
    if not active_idx:
        return {'ok': False, 'error': '检索语料为空（全部 chunk 为 superseded）'}

    if _BM25_MODE == 'bm25':
        bm25, bm25_active = _get_bm25(metas)
        if bm25 is None:
            return {'ok': False, 'error': 'BM25 语料为空'}
        import jieba
        q_tokens = list(jieba.cut_for_search(query))
        scores = bm25.get_scores(q_tokens)
        order = sorted(range(len(bm25_active)), key=lambda j: scores[j], reverse=True)[:k]
        top_idx = [bm25_active[j] for j in order]
        top_scores = [float(scores[j]) for j in order]
        results = []
        for rank, i in enumerate(top_idx):
            results.append({
                'score': top_scores[rank],
                'source': metas[i].get('source', ''),
                'type': metas[i].get('type', ''),
                'data_dim': metas[i].get('data_dim', '社区'),
                'text': metas[i].get('text', ''),
                'region': metas[i].get('region', ''),
                'topic': metas[i].get('topic', ''),
                'year': metas[i].get('year', ''),
                'keywords': metas[i].get('keywords', ''),
            })
        return {'ok': True, 'results': results, 'count': len(results)}

    model = _get_model()
    qvec = _embed_texts(model, [query])[0]
    scores = vectors @ qvec
    # CB-22f D5（glm/Codex 共识·P1）：混合检索 fact 加权 ×1.2——fact 短文本向量信号弱·加权提升命中率·
    #   可观测参数（黄金集 Recall@5 跟踪·不拍死·Codex「系数作观测起步」）。
    for i, m in enumerate(metas):
        if m.get('type') == 'fact':
            scores[i] = float(scores[i]) * 1.2
        scores[i] = float(scores[i]) * _hub_penalty(m)

    if _BM25_MODE == 'rrf':
        # RRF 融合（Reciprocal Rank Fusion·k=60·两路等权起步）
        # 稠密路=余弦+fact×1.2（既有加权保留）；BM25 路=字面精确；overfetch k*4。
        bm25, bm25_active = _get_bm25(metas)
        if bm25 is None:
            return {'ok': False, 'error': 'BM25 语料为空（无法 RRF 融合）'}
        import jieba
        q_tokens = list(jieba.cut_for_search(query))
        bm25_scores = bm25.get_scores(q_tokens)
        dense_ranked = sorted(active_idx, key=lambda i: scores[i], reverse=True)[:k * 4]
        bm25_ranked_pos = sorted(range(len(bm25_active)),
                                 key=lambda j: bm25_scores[j], reverse=True)[:k * 4]
        fused = {}
        for rank, i in enumerate(dense_ranked):
            fused[i] = fused.get(i, 0.0) + _RRF_W_DENSE / (_RRF_K + rank + 1)
        for rank, j in enumerate(bm25_ranked_pos):
            i = bm25_active[j]
            fused[i] = fused.get(i, 0.0) + _RRF_W_BM25 / (_RRF_K + rank + 1)
        # 枢纽降权在融合分上做（RRF rank-based·稠密路乘常数不改序·此处才有效）
        for i in list(fused):
            fused[i] *= _hub_penalty(metas[i])
        top_idx = sorted(fused, key=fused.get, reverse=True)[:k]
        results = []
        for i in top_idx:
            results.append({
                'score': round(float(fused[i]), 6),
                'source': metas[i].get('source', ''),
                'type': metas[i].get('type', ''),
                'data_dim': metas[i].get('data_dim', '社区'),
                'text': metas[i].get('text', ''),
                'region': metas[i].get('region', ''),
                'topic': metas[i].get('topic', ''),
                'year': metas[i].get('year', ''),
                'keywords': metas[i].get('keywords', ''),
            })
        return {'ok': True, 'results': results, 'count': len(results)}

    # superseded 过滤后的稠密排序（active_idx 白名单内取 top-k）
    order = sorted(active_idx, key=lambda i: scores[i], reverse=True)[:k]
    top_idx = order
    results = []
    for i in top_idx:
        results.append({
            'score': float(scores[i]),
            'source': metas[i].get('source', ''),
            'type': metas[i].get('type', ''),
            'data_dim': metas[i].get('data_dim', '社区'),  # 数据维度（住房/小区/社区/街区/城区/城中村/方法论）
            # CB-22 三支柱修正：透传片段全文（老索引无 text → 空串·前端标注"片段缺失·请重建索引"）
            'text': metas[i].get('text', ''),
            # CB-22f D3：fact 结构化字段透传（识别层零 LLM 组装 ctx.extracted 用·仅 type=fact 有值）
            'region': metas[i].get('region', ''),
            'topic': metas[i].get('topic', ''),
            'year': metas[i].get('year', ''),
            'keywords': metas[i].get('keywords', ''),
        })
    return {'ok': True, 'results': results, 'count': len(results)}


def stats():
    """索引统计。"""
    vectors, metas = load_index()
    if vectors is None:
        _tag(False, '索引未构建（跑 --build）')
        return
    types = {}
    for m in metas:
        types[m['type']] = types.get(m['type'], 0) + 1
    _tag(True, f'向量数 {len(metas)}·维度 {vectors.shape[1]}·类型 {types}')


def main():
    ap = argparse.ArgumentParser(description='RAG 向量索引工具')
    ap.add_argument('--build', action='store_true', help='构建索引')
    ap.add_argument('--rebuild', action='store_true', help='全量重建')
    ap.add_argument('--query', type=str, help='检索 Top-K')
    ap.add_argument('--stats', action='store_true', help='索引统计')
    ap.add_argument('--k', type=int, default=5, help='Top-K')
    args = ap.parse_args()

    if args.build or args.rebuild:
        build_index()
    elif args.query:
        r = search(args.query, args.k)
        if not r['ok']:
            _tag(False, r['error'])
        else:
            _tag(True, f'Top-{r["count"]} 检索结果:')
            for i, res in enumerate(r['results'], 1):
                print(f'  {i}. [{res["score"]:.3f}] {res["source"]} ({res["type"]}·维度={res.get("data_dim", "?")})')
    elif args.stats:
        stats()
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
