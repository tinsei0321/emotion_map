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
        # CB-22 三支柱修正（承重发现机器化）：素材须含片段全文（LLM 综合依赖内容·
        #   此前仅文件名致三支柱①空转）·老索引无 text → 重建后必非空
        assert 'text' in res, f'素材缺 text 字段（需 py tools/rag_index.py --rebuild 重建索引）: {res["source"]}'
        assert res.get('text', '').strip(), f'素材 text 为空（重建索引后不应为空）: {res["source"]}'


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
    """加速器直通（CB-22 P0-4 降级加速器）：高置信精确命中 → 'rag_query'（省 diagnose FC·非判断主体）。"""
    with emc_session() as page:
        assert _quick(page, '宜昌有哪些更新项目') == 'rag_query'          # 含「更新项目」精确子串
        assert _quick(page, '城市更新体检问题有哪些') == 'rag_query'      # 含「体检问题」
        assert _quick(page, '城市更新项目有哪些') == 'rag_query'          # 含「更新项目」精确子串（词序变体也被覆盖）


def test_quickintent_no_false_trigger():
    """负例（CB-22 P0-4 语义更新）：词序变体/分析问/概念问 → 不加速器直通（落 diagnose·由 LLM 判）。

    三层架构：_quickIntent 降级为加速器（非判断主体）——词序变体（本次失败句）**正确落 diagnose**·
    由 diagnose LLM 判 knowledge_qa（非短路失败·测试语义随架构变·Codex V6 正例两类）。
    """
    with emc_session() as page:
        # ★ 本次失败句：无「更新项目」精确子串（「项目有哪些」词序反）→ 落 diagnose（LLM 判·非短路失败）
        assert _quick(page, '宜昌市城市更新的项目有哪些') in (None, 'general')
        # 概念问 → general（走概念·非 RAG）
        assert _quick(page, '什么是更新单元') in ('general', None)
        # 纯空间问 → null（落 diagnose·可能 B/C）
        assert _quick(page, '宜昌西陵区情绪分布') in (None, 'general')
        # 分析问（含「哪些」+知识词「片区」）→ 不直通（非知识问答意图·LLM 判 emotion_analysis）
        assert _quick(page, '哪些片区情绪最差') in (None, 'general')


def test_knowledge_qa_routing_assembles():
    """P2-3 知识问答合流组装（e2e-seam 直测·injectOnly 确定性·去 LLM 依赖·Codex 复验挑战消 flaky）。

    injectOnly=true → _assembleKnowledgeQA 只组装注入 ctx.context·不调 finalStep LLM——
    断言**真实组装逻辑**（素材+强标记+四指令）·确定性·无模型加载竞态（冷加载走 R3 兜底不再是 flaky 源）。
    """
    with emc_session() as page:
        r = page.evaluate(
            "(q) => window.__emcTest.assembleKnowledgeQA(q, { _quick: false, injectOnly: true }).then(res => ({ final: res.final, skipped: res.skipped }))",
            '宜昌有哪些更新项目')
        # 合流组装路径（injectOnly 返回 skipped·不走 finalStep）
        assert r and r.get('skipped') == 'diagnose-knowledge-qa', f'知识问答未走合流组装: {r}'
        inj = r.get('final') or ''
        # 强标记（防 FINAL_TEMPLATE 图层导向·glm W1）
        assert '本次为知识问答·严禁图层' in inj, '注入缺强标记（严禁图层·glm W1）'
        # 只基于素材（Codex 补1）
        assert '只基于上述素材作答' in inj, '注入缺「只基于素材」（Codex 补1）'
        # 综合全部 Top-N（glm W2）
        assert '综合全部 Top-' in inj, '注入缺「综合全部 Top-N」（glm W2）'
        # 逐数字锚定 [来源] + 可读名称（P3-2 + A 来源可读性）
        assert '紧跟 [来源] 锚点' in inj, '注入缺「逐数字锚定 [来源]」（P3-2）'
        assert '可读名称' in inj and '内部代号' in inj, '注入缺「可读名称·禁内部代号」（A 来源可读性）'
        # 禁图层（第二根因防）
        assert '不要生成分析图层' in inj, '注入缺「禁生成图层」'


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
