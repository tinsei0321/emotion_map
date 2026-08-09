"""RAG 接入 EMC e2e 测试（CB-22·端点 + harness 短路 + finalStep 注入）。

经 e2e-seam 直测真实逻辑：
- 后端：POST /aiqa/rag_search（TestClient·入参/返回字段/降级文案）
- 前端：_quickIntent 'rag_query' 短路（RAG_QUERY_KW 双条件·保守不误断）
- 黄金集回归：召回/越维/案例 3 类仍 100%（接入后不退化）

无需真实 LLM（向量检索确定性·harness 纯函数）。
运行：py tests/browser/test_rag_emc_e2e.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session


def _quick(page, q):
    """调 _quickIntent（真实 JS·RAG 短路判定）。"""
    return page.evaluate("(q) => window.__emcTest.quickIntent(q)", q)


def test_rag_search_endpoint():
    """后端端点：POST /aiqa/rag_search 返回 {ok, results, count, dim_counts}。"""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from api.aiqa_routes import aiqa_router
    app = FastAPI()
    app.include_router(aiqa_router)
    c = TestClient(app)
    r = c.post('/aiqa/rag_search', json={'query': '宜昌城市更新有哪些项目', 'k': 3})
    assert r.status_code == 200
    data = r.json()
    assert data.get('ok') is True
    assert data.get('count', 0) >= 1
    assert data.get('dim_counts')  # 维度聚合（颗粒度原则）
    for res in data['results']:
        assert 'data_dim' in res  # 每条约含维度标注
        assert 'source' in res


def test_rag_search_fallback_when_no_index():
    """降级：索引未构建 → ok:False（非 500·前端静默）。"""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from api.aiqa_routes import aiqa_router
    import tools.rag_index as ri
    # 临时改 VECTORS 路径指向不存在（测降级）
    _orig = ri.VECTORS
    try:
        ri.VECTORS = ri.RAG_DIR / 'nonexistent.npy'
        app = FastAPI()
        app.include_router(aiqa_router)
        c = TestClient(app)
        r = c.post('/aiqa/rag_search', json={'query': '测试', 'k': 3})
        assert r.status_code == 200
        assert r.json().get('ok') is False
        assert '索引' in r.json().get('error', '')
    finally:
        ri.VECTORS = _orig


def test_quickintent_rag_trigger():
    """前端短路：开放语义/知识问 → 'rag_query'（RAG_QUERY_KW + 知识词）。"""
    with emc_session() as page:
        assert _quick(page, '宜昌有哪些更新项目') == 'rag_query'
        assert _quick(page, '城市更新体检问题有哪些') == 'rag_query'
        assert _quick(page, '如何参考上海城市更新做法') == 'rag_query'


def test_quickintent_no_false_trigger():
    """负例：分析问/纯空间问 → 不触发 rag_query（保守·宁落不误断）。"""
    with emc_session() as page:
        # 概念问 → general（走概念·非 RAG）
        assert _quick(page, '什么是更新单元') in ('general', None)
        # 纯空间问 → null（落 diagnose·可能 B/C）
        assert _quick(page, '宜昌西陵区情绪分布') in (None, 'general')


def test_assemble_rag_results():
    """分类→范式映射：rag_query 确定性组装（条目式+来源+维度·零 LLM·无图层导向）。"""
    with emc_session() as page:
        out = page.evaluate("() => window.__emcTest.assembleRagResults([{source: 'x/y.md#1', data_dim: '片区', score: 0.8}], 1)")
        # 条目式 + 来源 + 维度声明·无"分析图已生成"/无图层
        assert '知识库检索结果' in out
        assert '片区维度' in out
        assert '来源' in out
        assert '数据维度声明' in out
        assert '分析图' not in out      # 无图层导向（负例·根治模板错位）
        assert '{{show' not in out      # 无图层按钮


def test_rag_gold_set_regression():
    """黄金集回归：接入后召回/越维/案例 3 类仍 100%（防接入退化）。"""
    import subprocess
    # Codex 验证：跨环境编码缺陷——text=True 未指定 encoding·GBK locale 读 UTF-8 输出 → UnicodeDecodeError
    r = subprocess.run([sys.executable, '-X', 'utf8', 'tools/rag_eval.py', '--k', '5'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace',
                       cwd=os.path.join(os.path.dirname(__file__), '..', '..'))
    out = r.stdout or ''
    assert '正确召回: 10/10' in out, f'召回退化: {out}'
    assert '越维降级: 通过' in out, f'越维退化: {out}'
    assert '案例不引数据: 通过' in out, f'案例退化: {out}'
    assert '[OK] 黄金集整体通过' in out, f'黄金集未通过: {out}'


if __name__ == '__main__':
    import pytest
    raise SystemExit(pytest.main([__file__, '-v']))
