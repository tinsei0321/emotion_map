"""守卫测试：MOD_AIQA.F_* @track 装饰器编号去重（CB-22g · 防 F_016 冲突复发）。

背景：CB-22f D5 给 query_knowledge_base 加 @track("MOD_AIQA.F_016")，但 F_016
已被 build_outlet_schema._render_dimension_cannot 占用（register :23 + @track :287）。
glm/claude 两轮扫描都漏了 ai_qa/outlet_kb/ 子目录，致编号冲突上线。

本测试全仓（含 ai_qa/outlet_kb/）用 ast 解析扫描真实的 @track 装饰器节点，
同一编号被多个 @track 占用即 fail。

为何用 ast 而非正则：
  正则分不清 docstring/字符串/注释里的 @track("...F_NNN") 字样与本尊——本守卫文件
  自身 docstring 写了 F_016 背景说明会被正则误判为占用。ast 只认语法树里的装饰器
  节点，彻底规避。

为何只看 @track、不把 register_track_id 纳入冲突判定：
  register_track_id 是「描述性注册」，常与 @track 配对出现在同文件同函数（如
  build_outlet_schema：register :23 + @track :287 同号是合法配对）。把 register 也
  纳入去重会把这种合法配对误报为冲突。@track 是「运行时真占用」——同编号多 @track =
  两个函数抢一个 ID = 真冲突。本类 bug 根因正是 @track 同号，故守卫只盯 @track。

执行：pytest tests/validate_track_ids.py -q
"""
import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# 跳过非源码目录（虚拟环境/依赖/构建产物/前端）
_SKIP_PARTS = {"venv", ".venv", "__pycache__", "site-packages",
               "node_modules", ".git", "dist", "build"}
# 装饰器字面量参数须严格匹配 MOD_AIQA.F_NNN（整串）
_ID_RE = re.compile(r'^MOD_AIQA\.F_(\d+)$')


def _decorator_name(node):
    """取装饰器 callable 名：track 或 core.tracker.track → 'track'。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _collect_track_decorators():
    """全仓 ast 扫描 @track("MOD_AIQA.F_NNN") 装饰器节点。

    返回 [(编号, 相对路径, 行号), ...]——只认语法树 Decorator 节点里的 Call，
    docstring/字符串/注释里的字样不会误判。
    """
    hits = []
    for py in REPO_ROOT.rglob("*.py"):
        if any(part in _SKIP_PARTS for part in py.parts):
            continue
        try:
            text = py.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue  # 读不了/解析不了（非本仓规范源码）跳过
        rel = str(py.relative_to(REPO_ROOT)).replace("\\", "/")
        for node in ast.walk(tree):
            deco_list = getattr(node, "decorator_list", None) or []
            for deco in deco_list:
                # @track("MOD_AIQA.F_NNN", ...) 形如 Call(func=Name('track'), args=[Constant])
                if not isinstance(deco, ast.Call):
                    continue
                if _decorator_name(deco.func) != "track":
                    continue
                for arg in deco.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        m = _ID_RE.match(arg.value)
                        if m:
                            hits.append((m.group(1), rel, deco.lineno))
    return hits


def test_no_duplicate_mod_aiqa_track_id():
    """同一 MOD_AIQA.F_NNN 不得被多个 @track 装饰器占用（CB-22g F_016 冲突防复发）。"""
    hits = _collect_track_decorators()
    by_id = {}
    for num, rel, lineno in hits:
        by_id.setdefault(num, []).append(f"{rel}:{lineno}")
    dups = {num: locs for num, locs in by_id.items() if len(locs) > 1}
    assert not dups, (
        "MOD_AIQA.F_* 编号被多个 @track 装饰器占用（冲突，须改其中一处编号）：\n"
        + "\n".join(f"  F_{num}: {', '.join(locs)}"
                    for num, locs in sorted(dups.items(), key=lambda x: int(x[0])))
    )


def test_track_scan_not_empty():
    """sanity：扫描应命中足够多 MOD_AIQA 埋点（防 rglob/ast 逻辑失效误报绿）。"""
    hits = _collect_track_decorators()
    assert len(hits) >= 10, (
        f"MOD_AIQA @track 埋点扫描命中过少（{len(hits)}），扫描逻辑可能失效"
    )


if __name__ == "__main__":
    # 手动跑：py tests/validate_track_ids.py —— 打印当前 @track 分布画像
    hits = _collect_track_decorators()
    print(f"[OK] 扫描到 {len(hits)} 个 @track MOD_AIQA.F_* 装饰器")
    by_id = {}
    for num, rel, lineno in hits:
        by_id.setdefault(num, []).append(f"{rel}:{lineno}")
    for num in sorted(by_id, key=int):
        locs = by_id[num]
        flag = "  [DUP]" if len(locs) > 1 else ""
        print(f"  F_{num:>3}: {', '.join(locs)}{flag}")
