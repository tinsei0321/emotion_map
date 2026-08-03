"""CB-16 Wave 0 CI：出口卡片触发词表前后端同步校验。

权威源 ai_qa/outlet_kb/build_outlet_schema.py（TRIGGER_WORDS + _UI_CONTEXT_WORDS）
↔ 镜像 frontend/js/ai_qa/emc-patterns.js（OUTLET_TRIGGER_KW + OUTLET_UI_EXCLUDE_KW）。
CB-16 Codex/glm：需校验双份（8 词 + 5 排除词）——防前端提示与后端触发不一致
（如"更新图层"前端提示出卡·后端排除不出卡·用户困惑）。

跑：py -m pytest tests/validate_outlet_trigger_sync.py -q
"""
import ast
import re
from pathlib import Path

_PY_PATH = Path(__file__).resolve().parent.parent / "ai_qa" / "outlet_kb" / "build_outlet_schema.py"
_JS_PATH = Path(__file__).resolve().parent.parent / "frontend" / "js" / "ai_qa" / "emc-patterns.js"


def _parse_py_words(path):
    """AST 解析 build_outlet_schema.py 提取 TRIGGER_WORDS / _UI_CONTEXT_WORDS（tuple of str）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in ("TRIGGER_WORDS", "_UI_CONTEXT_WORDS"):
                    if isinstance(node.value, ast.Tuple) or isinstance(node.value, ast.List):
                        out[tgt.id] = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
    return out


def _parse_js_words(path):
    """正则解析 emc-patterns.js 提取 OUTLET_TRIGGER_KW / OUTLET_UI_EXCLUDE_KW（list of str）。"""
    text = path.read_text(encoding="utf-8")
    out = {}
    for name in ("OUTLET_TRIGGER_KW", "OUTLET_UI_EXCLUDE_KW"):
        m = re.search(rf"export const {name} = \[([^\]]*)\]", text)
        if m:
            out[name] = re.findall(r"""['"]([^'"]+)['"]""", m.group(1))
    return out


def test_outlet_trigger_kw_sync():
    """TRIGGER_WORDS（后端）↔ OUTLET_TRIGGER_KW（前端）集合一致。"""
    py = _parse_py_words(_PY_PATH)
    js = _parse_js_words(_JS_PATH)
    assert set(py.get("TRIGGER_WORDS", [])) == set(js.get("OUTLET_TRIGGER_KW", [])), (
        f'触发词表漂移：后端 {py.get("TRIGGER_WORDS")} vs 前端 {js.get("OUTLET_TRIGGER_KW")}'
    )


def test_outlet_ui_exclude_kw_sync():
    """_UI_CONTEXT_WORDS（后端）↔ OUTLET_UI_EXCLUDE_KW（前端）集合一致。"""
    py = _parse_py_words(_PY_PATH)
    js = _parse_js_words(_JS_PATH)
    assert set(py.get("_UI_CONTEXT_WORDS", [])) == set(js.get("OUTLET_UI_EXCLUDE_KW", [])), (
        f'UI 排除表漂移：后端 {py.get("_UI_CONTEXT_WORDS")} vs 前端 {js.get("OUTLET_UI_EXCLUDE_KW")}'
    )
