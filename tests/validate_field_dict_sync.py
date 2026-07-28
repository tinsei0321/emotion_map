"""WS2 F2.6 CI：前后端字段字典同步校验。

权威源 core/field_dictionary.py::FIELD_ROLE_DICT ↔ 镜像 frontend/js/field_dictionary.js::FIELD_ROLES。
CB 发现：原人工同步无 CI 守护，易漂移（前端认 role 后端不认 / 反之）。本测试防漂移。

跑：py -m pytest tests/validate_field_dict_sync.py -q
"""
import re
from pathlib import Path

from core.field_dictionary import FIELD_ROLE_DICT

_JS_PATH = Path(__file__).resolve().parent.parent / "frontend" / "js" / "field_dictionary.js"


def _parse_js_roles(text):
    """从容错解析 field_dictionary.js 提取 {role: set(variants)}。

    匹配 `roleName: { variants: [...], ... }`（.js 单行 variant list）。
    """
    roles = {}
    for m in re.finditer(r"(\w+):\s*\{\s*variants:\s*\[([^\]]*)\]", text):
        role = m.group(1)
        variants = set(re.findall(r"""['"]([^'"]+)['"]""", m.group(2)))
        roles[role] = variants
    return roles


def test_field_dict_role_set_sync():
    """前后端 role 集一致（.py 有↔.js 有）。"""
    js_roles = _parse_js_roles(_JS_PATH.read_text(encoding="utf-8"))
    py_keys, js_keys = set(FIELD_ROLE_DICT), set(js_roles)
    missing_in_js = py_keys - js_keys
    extra_in_js = js_keys - py_keys
    assert not missing_in_js, f"roles in .py but missing in .js (frontend won't recognize): {sorted(missing_in_js)}"
    assert not extra_in_js, f"roles in .js but missing in .py (backend won't recognize): {sorted(extra_in_js)}"


def test_field_dict_variants_sync():
    """每 role 的 variant 集前后端一致（顺序无关）。"""
    js_roles = _parse_js_roles(_JS_PATH.read_text(encoding="utf-8"))
    mismatches = []
    for role, info in FIELD_ROLE_DICT.items():
        py_v = set(info["variants"])
        js_v = js_roles.get(role, set())
        if py_v != js_v:
            mismatches.append(
                f"{role}: only.py={sorted(py_v - js_v)} only.js={sorted(js_v - py_v)}"
            )
    assert not mismatches, "field dict variants out of sync (sync .js when .py changes):\n  " + "\n  ".join(mismatches)
