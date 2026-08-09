"""CB-22 CI：分类→回答范式映射（PARADIGM_MAP）完整性校验。

背景（CB-22 三支柱对齐·Codex 补2）：分类→范式映射曾隐式存在导致两轮失败
（RAG 问答被图层模板带偏出"分析图已生成"）。PARADIGM_MAP（emc-patterns.js）
是架构支柱（EMC 架构）的显式契约——本测试守护：
1. 覆盖完整性：所有 _quickIntent 分类 + B 路径预留 + diagnose 出口都有范式
2. 范式合法值：text_qa（纯文字）/ knowledge_qa（检索→LLM 综合）/ layer（图层）
3. 三支柱契约（用户人工验证定·不可回归）：rag_query → knowledge_qa 且 harness
   rag_query 分支必须走 finalStep LLM 综合（零 LLM = 砍第三支柱·用户否定）
4. knowledge_qa 语义契约（注释含"LLM 综合"·防注释/实现漂回"确定性组装"）

跑：py -m pytest tests/validate_paradigm_map.py -q
"""
import re
from pathlib import Path

_JS_PATTERNS = Path(__file__).resolve().parent.parent / "frontend" / "js" / "ai_qa" / "emc-patterns.js"
_JS_HARNESS = Path(__file__).resolve().parent.parent / "frontend" / "js" / "ai_qa" / "harness.js"

# 范式合法值（与 emc-patterns.js PARADIGM_MAP 注释契约同步）
_VALID_PARADIGMS = {"text_qa", "knowledge_qa", "layer"}
# 必须被覆盖的分类（_quickIntent 出口 + B 路径预留 + diagnose 出口）
_REQUIRED_KEYS = {"general", "rag_query", "knowledge_query", "gis_operation", "emotion_analysis"}


def _parse_js_map(path):
    """正则解析 emc-patterns.js 的 PARADIGM_MAP（dict key→value）。"""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"export const PARADIGM_MAP = \{(.*?)\};", text, re.S)
    assert m, "PARADIGM_MAP 定义缺失"
    out = {}
    for k, v in re.findall(r"""['"]([a-z_]+)['"]\s*:\s*['"]([a-z_]+)['"]""", m.group(1)):
        out[k] = v
    return out


def test_paradigm_map_covers_all_intents():
    """覆盖完整性：_quickIntent 分类 + B 路径 + diagnose 出口全在映射内。"""
    mapping = _parse_js_map(_JS_PATTERNS)
    missing = _REQUIRED_KEYS - set(mapping)
    assert not missing, f"PARADIGM_MAP 缺分类（新意图未映射范式）：{missing}"


def test_paradigm_values_legal():
    """范式值合法性：text_qa / knowledge_qa / layer。"""
    mapping = _parse_js_map(_JS_PATTERNS)
    illegal = {k: v for k, v in mapping.items() if v not in _VALID_PARADIGMS}
    assert not illegal, f"PARADIGM_MAP 非法范式值：{illegal}"


def test_rag_query_maps_to_knowledge_qa():
    """三支柱契约：rag_query → knowledge_qa（知识问答·禁回退确定性组装/零 LLM）。"""
    mapping = _parse_js_map(_JS_PATTERNS)
    assert mapping.get("rag_query") == "knowledge_qa", (
        f"rag_query 范式被改：{mapping.get('rag_query')}（CB-22 用户定·知识问答必须 LLM 综合素材）"
    )


def test_rag_query_branch_uses_finalstep():
    """零 LLM 防回归：harness rag_query 分支必须调用 finalStep LLM 综合（用户验证否定零 LLM）。

    Codex 复验挑战（CB-22 对齐轮）：字符串包含断言弱化——删调用留注释/变量名仍可误过·
    改精确调用点 `await stages.finalStep(`（低成本·更强防回归）。
    """
    text = _JS_HARNESS.read_text(encoding="utf-8")
    seg = text.split("_quickIntent(ctx.question) === 'rag_query'")[1].split("_quickIntent(ctx.question)")[0]
    assert "await stages.finalStep(ctx, hooks, '')" in seg, (
        "rag_query 分支无 finalStep LLM 综合调用（零 LLM 回归·砍第三支柱）"
    )


def test_rag_injection_volume_budget():
    """注入体积预算守卫（Codex 复验挑战·防注入膨胀撑爆 context）。

    动态注入预算 ≤8KB（素材 Top-5 × 1000B + 指令 ~500B ≈ 5.5KB）：
    ① snippet 上限锁 slice(0, 1000)/条 ② 指令常量行数有界 ③ Top-K 请求 k≤5。
    """
    text = _JS_HARNESS.read_text(encoding="utf-8")
    seg = text.split("_quickIntent(ctx.question) === 'rag_query'")[1].split("_quickIntent(ctx.question)")[0]
    assert "slice(0, 1000)" in seg, "rag 注入 snippet 上限被改（须 ≤1000B/条·体积预算守卫）"
    assert "k: 5" in seg, "rag Top-K 请求被改（须 ≤5 条·体积预算守卫）"
    instr_lines = [l for l in seg.splitlines()
                   if "【知识问答排版】" in l or l.strip().startswith(("1. **", "2. **", "3. **"))]
    assert 1 <= len(instr_lines) <= 6, f"知识问答指令行数异常（防注入无限膨胀）: {len(instr_lines)}"


def test_knowledge_qa_contract_comment():
    """契约注释语义：knowledge_qa 注释须含 LLM 综合（防注释/实现漂回"确定性组装"）。"""
    text = _JS_PATTERNS.read_text(encoding="utf-8")
    header = text.split("export const PARADIGM_MAP")[0].split("\n")[-3:]
    assert any("LLM 综合" in line for line in header), "PARADIGM_MAP 头部注释缺'LLM 综合'语义"
