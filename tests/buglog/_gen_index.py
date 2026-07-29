"""buglog 索引生成器（确定性·非 LLM）。

扫描 tests/buglog/{open,resolved}/B*.md，解析 YAML frontmatter，重生：
  - _index.md  概览（按状态/类型/模块计数）+ 全部条目表
  - _trend.md  复现 >=2 的历史复发项（recurring 为派生属性，非独立目录）

用法：
  py tests/buglog/_gen_index.py          # 重生 _index.md + _trend.md
  py tests/buglog/_gen_index.py --check   # CI 守护：索引与条目不一致则非零退出

设计依据（Smart Agent, Dumb Tool 内核·铁律 1/3）：
  - Smart = 调用本 skill 的 agent 填写 B*.md 条目（LLM 擅长的出口端标准化）
  - Dumb  = 本脚本算索引（确定性·纯函数式·不调 LLM·CI 可跑）
  对标 tests/validate_field_dict_sync.py 的确定性守护思路。

前端 test-board.js 仪表盘（P2）将直接读本脚本产出的 _index.md / _trend.md。
"""
import re
import sys
from pathlib import Path

BUGLOG = Path(__file__).resolve().parent
STATE_DIRS = ("open", "resolved")
INDEX = BUGLOG / "_index.md"
TREND = BUGLOG / "_trend.md"
REGRESSION = BUGLOG / "_regression.md"

TYPE_TAG = {"BUG": "[BUG]", "DEGRAD": "[DEGRAD]", "PERF": "[PERF]", "UI": "[UI]"}
SEV_TAG = {"CRIT": "[CRIT]", "HIGH": "[HIGH]", "MED": "[MED]", "LOW": "[LOW]"}
STATUS_TAG = {"open": "[OPEN]", "resolved": "[RESOLVED]"}


# ── 解析 ────────────────────────────────────────────────────────────
def _parse_fm(text):
    """最小 YAML frontmatter 解析（仅 key: value 标量；不引依赖）。"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            v = v.strip().strip("'\"")  # 去引号
            fm[k.strip()] = v
    return fm


def load_entries():
    """返回排序后的条目 dict 列表（含 _status / _path 派生字段）。"""
    entries = []
    for st in STATE_DIRS:
        d = BUGLOG / st
        if not d.is_dir():
            continue
        for p in sorted(d.glob("B*.md")):
            fm = _parse_fm(p.read_text(encoding="utf-8"))
            if fm:
                fm["_status"] = st
                fm["_path"] = f"{st}/{p.name}"
                entries.append(fm)
    entries.sort(key=lambda e: e.get("id", ""))
    return entries


def next_id(entries=None):
    """下一个可用 B{NNN}（skill 新建条目前调用）。"""
    entries = entries if entries is not None else load_entries()
    nums = [int(re.sub(r"\D", "", e.get("id", "0"))) for e in entries if re.sub(r"\D", "", e.get("id", ""))]
    return f"B{(max(nums) + 1) if nums else 1:03d}"


# ── 渲染 ────────────────────────────────────────────────────────────
def _counts(entries, key, tag_map=None):
    """按 key 计数；tag_map 提供展示名。"""
    c = {}
    for e in entries:
        v = e.get(key, "?")
        label = (tag_map or {}).get(v, v) if tag_map else v
        c[label] = c.get(label, 0) + 1
    return c


def _table(title, counter):
    rows = "".join(f"| {k} | {v} |\n" for k, v in sorted(counter.items(), key=lambda kv: -kv[1]))
    return f"### {title}\n\n| 值 | 数量 |\n|---|:-:|\n{rows}\n" if rows else ""


def render_index(entries):
    status_c = _counts(entries, "_status", STATUS_TAG)
    type_c = _counts(entries, "type", TYPE_TAG)
    sev_c = _counts(entries, "severity", SEV_TAG)
    module_c = _counts(entries, "module")
    total = len(entries)
    open_n = sum(1 for e in entries if e.get("_status") == "open")

    lines = [
        "# Bug Log 索引",
        "",
        f"> 自动生成（`py tests/buglog/_gen_index.py`）·勿手改。条目总数 **{total}**·未解决 **{open_n}**。",
        "> recurring（历史复发 >=2）见 [_trend.md](_trend.md)。",
        "",
        "## 概览",
        "",
        _table("按状态", status_c),
        _table("按类型", type_c),
        _table("按严重度", sev_c),
        _table("按模块", module_c),
        "## 全部条目",
        "",
        "| ID | 标题 | 类型 | 严重度 | 状态 | 模块 | 复现 | 关联 |",
        "|:-:|------|:-:|:-:|:-:|:-:|:-:|------|",
    ]
    for e in entries:
        links = []
        if e.get("cb"):
            links.append(e["cb"])
        if e.get("case_ref"):
            links.append(e["case_ref"])
        lines.append(
            f"| {e.get('id','?')} | {e.get('title','')} "
            f"| {TYPE_TAG.get(e.get('type',''), e.get('type','?'))} "
            f"| {SEV_TAG.get(e.get('severity',''), e.get('severity','?'))} "
            f"| {STATUS_TAG.get(e.get('_status',''), e.get('_status','?'))} "
            f"| {e.get('module','?')} | {e.get('repro_count','?')}"
            f" | {' '.join(links) or '—'} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_trend(entries):
    rec = [e for e in entries if int(e.get("repro_count", "0") or 0) >= 2]
    rec.sort(key=lambda e: -int(e.get("repro_count", "0") or 0))
    lines = [
        "# 历史复发趋势（repro_count >= 2）",
        "",
        "> 自动生成·recurring 为派生属性（非独立目录）。本表反映「曾反复出现的 bug」分布，",
        "> 用于飞轮回归聚焦 + 仪表盘重复问题热力图（P2）。",
        "",
        "| ID | 标题 | 复现 | 模块 | 状态 | 最近复现 | 根因 |",
        "|:-:|------|:-:|:-:|:-:|:-:|------|",
    ]
    for e in rec:
        rc_link = f"[{e.get('repro_count', '0')}]({e.get('_path', '')})"  # 链到条目（同目录）
        # rootcause 是 repo 相对路径；_trend.md 在 tests/buglog/，须 ../../ 回到根
        rc = e.get("rootcause", "")
        rc_link_root = f"[{rc.split('/')[-1]}](../../{rc})" if rc else "—"
        lines.append(
            f"| {e.get('id','?')} | {e.get('title','')} | {rc_link} "
            f"| {e.get('module','?')} "
            f"| {STATUS_TAG.get(e.get('_status',''), e.get('_status','?'))} "
            f"| {e.get('last_repro','—')} | {rc_link_root} |"
        )
    if not rec:
        lines.append("| — | 暂无复发项 | — | — | — | — | — |")
    lines.append("")
    return "\n".join(lines)


def _parse_body_case(text):
    """从条目 body「标准化用例」节提取问句 + 预期（① ② ③）。"""
    m = re.search(r"\*\*问句\*\*[：:]\s*[「「\"]?(.*?)[」」\"]?\s*\n", text)
    q = m.group(1).strip() if m else ""
    exp = re.findall(r"[①②③④⑤⑥]\s*(.*)", text)
    exp = " / ".join(x.strip() for x in exp[:4]) if exp else ""
    return q, exp


def render_regression(entries):
    """已修复 bug → 回归清单（问句+预期+根因指针）。
    诚实定位：这是「发版前手动复验清单」·非飞轮自动执行——
    数据前提（加载哪个面层/字段）逐案不同，无法从语义描述自动装配执行；
    关联飞轮用例（case_ref）在常规飞轮跑中已覆盖执行。"""
    resolved = [e for e in entries if e.get("_status") == "resolved"]
    head = [
        "# 回归关注清单（resolved · 自动生成）",
        "",
        "> 自动生成（`py tests/buglog/_gen_index.py`）·勿手改。已修复 bug 的标准化用例 + 根因指针。",
        "> 供发版前**手动复验**。非飞轮自动执行——数据前提逐案不同（如 B001 需带字段 MC 的面层），",
        "> 无法从语义描述自动装配；关联飞轮用例（case_ref）在常规跑中已覆盖执行。",
        "",
    ]
    if not resolved:
        head += ["| ID | 标题 | 关联用例 | 模块 |", "|:-:|------|:-:|:-:|", "| — | 暂无已修复 bug | — | — |"]
        return "\n".join(head)
    # 读 body 取问句
    rows = []
    details = []
    for e in resolved:
        p = BUGLOG / e.get("_path", "")
        q, exp = ("", "")
        try:
            q, exp = _parse_body_case(p.read_text(encoding="utf-8"))
        except Exception:
            pass
        rc = e.get("rootcause", "")
        rc_link = f"[{rc.split('/')[-1]}](../../{rc})" if rc else "—"
        rows.append(f"| {e.get('id','?')} | {e.get('title','')} | {e.get('case_ref') or '—'} | {e.get('module','?')} |")
        details.append((e.get("id", "?"), q, exp, rc_link))
    head += ["## 用例速查", "", "| ID | 标题 | 关联用例 | 模块 |", "|:-:|------|:-:|:-:|"] + rows
    head += ["", "## 标准化用例（问句 + 预期，供手动复验）", ""]
    for bid, q, exp, rc_link in details:
        head.append(f"### {bid}")
        if q:
            head.append(f"- **问句**：「{q}」")
        if exp:
            head.append(f"- **预期**：{exp}")
        head.append(f"- **根因**：{rc_link}")
        head.append("")
    return "\n".join(head)


# ── 主入口 ──────────────────────────────────────────────────────────
def _write(path, content):
    path.write_text(content, encoding="utf-8")


def main():
    check = "--check" in sys.argv
    entries = load_entries()
    if not check:
        _write(INDEX, render_index(entries))
        _write(TREND, render_trend(entries))
        _write(REGRESSION, render_regression(entries))
        print(f"[OK] buglog index regenerated: {len(entries)} entries -> {INDEX.name} + {TREND.name} + {REGRESSION.name}")
        print(f"[OK] next_id = {next_id(entries)}")
        return 0

    # --check：比对现存索引与应生成内容
    stale = []
    for path, renderer in ((INDEX, render_index), (TREND, render_trend), (REGRESSION, render_regression)):
        if not path.exists():
            stale.append(f"{path.name} missing")
            continue
        if path.read_text(encoding="utf-8") != renderer(entries):
            stale.append(f"{path.name} out of sync (run: py tests/buglog/_gen_index.py)")
    if stale:
        print("[ERR] buglog index stale:\n  " + "\n  ".join(stale))
        return 1
    print(f"[OK] buglog index in sync ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
