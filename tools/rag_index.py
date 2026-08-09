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

    # 收集向量化对象
    notes = _load_notes()
    cases = _load_cases()
    all_chunks = notes + cases
    _tag(True, f'向量化对象: 笔记段落 {len(notes)} + 案例 {len(cases)} = {len(all_chunks)}')

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
            'embedding_model': MODEL_NAME,
            'dim': int(vectors.shape[1]),
            'build_time': time.strftime('%Y-%m-%d %H:%M'),
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


def _get_model():
    global _model_cache
    if _model_cache is None:
        from sentence_transformers import SentenceTransformer
        _model_cache = SentenceTransformer(MODEL_NAME)
    return _model_cache


@track('MOD_AIQA.F_015', track_args=False)
def search(query, k=5):
    """检索 Top-K（余弦相似度·返回片段 + 来源·含数据维度）。"""
    import numpy as np

    vectors, metas = load_index()
    if vectors is None or len(metas) == 0:
        return {'ok': False, 'error': '检索暂不可用（索引未构建·跑 py tools/rag_index.py --build）'}

    model = _get_model()
    qvec = _embed_texts(model, [query])[0]
    scores = vectors @ qvec
    top_idx = np.argsort(scores)[::-1][:k]
    results = []
    for i in top_idx:
        results.append({
            'score': float(scores[i]),
            'source': metas[i].get('source', ''),
            'type': metas[i].get('type', ''),
            'data_dim': metas[i].get('data_dim', '社区'),  # 数据维度（住房/小区/社区/街区/城区/城中村/方法论）
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
