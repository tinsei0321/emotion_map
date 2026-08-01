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
SUMMARY = BUGLOG / "_summary.md"

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
                # CB-10 P1-1：frontmatter status 优先于目录（治 B010/B011 写 resolved 却在 open/ 被计 OPEN 的状态双源）
                fm["_status"] = fm.get("status", "") if fm.get("status", "") in STATE_DIRS else st
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


# ── _summary.md 人类可读工程日志 ──────────────────────────────────────
def _find_fix_section(body_text):
    """定位 body 中「修复记录」节（## 修复记录 之后到下一个 ## 或文末）。返该段文本。"""
    lines = body_text.splitlines()
    start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("## 修复记录"):
            start = i + 1
            break
    if start < 0:
        return ""
    # 找到下一个 ## 标题为终止
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].strip().startswith("## ") and "修复记录" not in lines[i]:
            end = i
            break
    return "\n".join(lines[start:end])


def _parse_fix_progress(body_text):
    """从条目 body「修复记录」表提取最新修复进度（仅读修复记录表，不读已知失败模式）。
    返 (label, commit_short) 或 ('待修复', '')。"""
    section = _find_fix_section(body_text)
    if not section:
        return ('待修复', '')
    in_table = False
    last_date = last_action = last_commit = ''
    for line in section.splitlines():
        s = line.strip()
        if s.startswith('|') and ('日期' in s or '操作' in s):
            in_table = True
            continue
        if in_table and s.startswith('|') and not s.startswith('|--'):
            parts = [p.strip() for p in s.split('|')]
            if len(parts) >= 4:
                d = parts[1] if len(parts) > 1 else ''
                a = parts[2] if len(parts) > 2 else ''
                c = parts[3] if len(parts) > 3 else ''
                if d and d != '—' and d != '':
                    last_date, last_action, last_commit = d, a, c
        elif in_table and not s.startswith('|'):
            in_table = False
    if last_action and last_action != '待修复':
        c_short = last_commit[:7] if len(last_commit) >= 7 else last_commit
        return (last_action, c_short) if c_short else (last_action, '')
    return ('待修复', '')


def _parse_fix_timeline(entries):
    """从所有条目「修复记录」表提取时间线（仅读修复记录表）·去重·按日期倒序·近 15 条。
    返 [(date, action, commit_short, bug_ids)] 列表。"""
    rows = []
    for e in entries:
        p = BUGLOG / e.get("_path", "")
        try:
            body = p.read_text(encoding="utf-8")
        except Exception:
            continue
        section = _find_fix_section(body)
        if not section:
            continue
        in_table = False
        for line in section.splitlines():
            s = line.strip()
            if s.startswith('|') and ('日期' in s or '操作' in s):
                in_table = True
                continue
            if in_table and s.startswith('|') and not s.startswith('|--'):
                parts = [p.strip() for p in s.split('|')]
                if len(parts) >= 4:
                    d, a, c = parts[1], parts[2], parts[3] if len(parts) > 3 else ''
                    if d and d != '—' and d != '':
                        c_short = c[:7] if len(c) >= 7 else c
                        rows.append((d, a, c_short, e.get('id', '?')))
            elif in_table and not s.startswith('|'):
                in_table = False
    # 去重：(date, commit) 相同 → 合并 bug_ids
    dedup = {}
    for d, a, c, bid in rows:
        key = (d, c)
        if key not in dedup:
            dedup[key] = (d, a, c, [])
        dedup[key][3].append(bid)
    # 按日期倒序
    out = sorted(dedup.values(), key=lambda x: x[0], reverse=True)[:15]
    return out


def _latest_report_summary():
    """读 tests/reports/ 最新 JSON（EMC-SUM v1 schema），返一行摘要（pass%/total/报告名）。"""
    reports_dir = BUGLOG.parent / "reports"
    if not reports_dir.is_dir():
        return ''
    jsons = sorted(reports_dir.glob("report-*.json"), reverse=True)
    if not jsons:
        return ''
    try:
        import json
        data = json.loads(jsons[0].read_text(encoding="utf-8"))
        meta = data.get("meta", {})
        cases = data.get("cases", [])
        total = meta.get("total", len(cases))
        passed = sum(1 for c in cases if c.get("pass"))
        pct = f"{int(passed / total * 100)}%" if total else "—"
        name = jsons[0].stem
        return f"{name} ({pct}·{passed}/{total})"
    except Exception:
        return jsons[0].stem


def render_summary(entries):
    """人类可读工程日志：概览 KPI + 按优先级详述 + 修复时间线 + 复发趋势 + 飞轮对接。"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    open_entries = [e for e in entries if e.get("_status") == "open"]
    resolved_entries = [e for e in entries if e.get("_status") == "resolved"]
    total = len(entries)
    open_n = len(open_entries)

    # 优先级分组
    p0 = [e for e in open_entries if e.get("priority") == "P0"]
    p1 = [e for e in open_entries if e.get("priority") == "P1"]
    p2 = [e for e in open_entries if e.get("priority") == "P2"]
    unp = [e for e in open_entries if e.get("priority", "") not in ("P0", "P1", "P2")]

    # 修复进度统计
    fixed_submitted = 0
    for e in open_entries:
        p = BUGLOG / e.get("_path", "")
        try:
            prog, _ = _parse_fix_progress(p.read_text(encoding="utf-8"))
            if prog != '待修复':
                fixed_submitted += 1
        except Exception:
            pass

    # 复发趋势
    rec = [(e, int(e.get("repro_count", "0") or 0)) for e in entries if int(e.get("repro_count", "0") or 0) >= 2]
    rec.sort(key=lambda x: -x[1])

    # 飞轮
    flywheel_info = _latest_report_summary()
    tc_count = "27"  # 硬编码（用例数手工维护·不自动扫描·避依赖 emc_test_cases.md 解析）

    lines = [
        "# EMC Bug 修复工程日志",
        "",
        f"> 自动生成（`py tests/buglog/_gen_index.py`）·勿手改 · 最后更新：{now}",
        f"> 条目 **{total}** · OPEN **{open_n}** · RESOLVED **{total - open_n}** · P0 阻塞 **{len(p0)}** · 修复已提交 **{fixed_submitted}**",
        f"> 飞轮：{tc_count} 用例" + (f" · 最近报告：{flywheel_info}" if flywheel_info else ""),
        "",
        "---",
        "",
        "## 工程概览",
        "",
        "| 指标 | 值 |",
        "|------|-----|",
        f"| 总条目 | {total} |",
        f"| OPEN（未解决） | {open_n} |",
        f"| RESOLVED（已解决） | {total - open_n} |",
        f"| P0 阻塞 | {len(p0)}（{'/'.join(e.get('id','?') for e in p0) if p0 else '无'}）|",
        f"| P1 高优先 | {len(p1)}（{'/'.join(e.get('id','?') for e in p1) if p1 else '无'}）|",
        f"| P2 中优先 | {len(p2)}（{'/'.join(e.get('id','?') for e in p2) if p2 else '无'}）|",
        f"| 修复已提交 | {fixed_submitted} |",
        f"| 飞轮用例 | {tc_count} |",
        f"| 最近飞轮报告 | {flywheel_info or '—'} |",
        "",
        "---",
    ]

    # ── 各优先级详述 ──
    PRIORITY_SECTIONS = [
        ("P0 · 阻塞项（必须立即修复）", p0),
        ("P1 · 高优先", p1),
        ("P2 · 中优先", p2),
    ]
    # 未标优先级
    if unp:
        PRIORITY_SECTIONS.append(("未标优先级", unp))

    for section_title, group in PRIORITY_SECTIONS:
        lines.append(f"## {section_title}")
        lines.append("")
        if not group:
            lines.append("*暂无*")
            lines.append("")
            continue
        for e in group:
            bid = e.get("id", "?")
            title = e.get("title", "").strip("'\"")
            sev = e.get("severity", "?")
            module = e.get("module", "?")
            repro = e.get("repro_count", "?")
            rootcause = e.get("rootcause", "")
            case_ref = e.get("case_ref", "")
            cb = e.get("cb", "")

            # 修复进度
            p = BUGLOG / e.get("_path", "")
            fix_progress = "待修复"
            fix_commit = ""
            try:
                fix_progress, fix_commit = _parse_fix_progress(p.read_text(encoding="utf-8"))
            except Exception:
                pass
            progress_str = f"{fix_progress}" + (f" ({fix_commit})" if fix_commit else "")

            # 问句
            q = ""
            try:
                q, _ = _parse_body_case(p.read_text(encoding="utf-8"))
            except Exception:
                pass

            # 关联链接
            links = []
            entry_path = e.get("_path", "")
            if entry_path:
                links.append(f"[entry]({entry_path})")
            if rootcause:
                # rootcause 是 repo 相对路径，_summary.md 在 tests/buglog/ 需 ../../ 返回根
                rc_name = rootcause.split("/")[-1]
                links.append(f"[rootcause](../../{rootcause})")
            if case_ref:
                links.append(case_ref)
            if cb:
                links.append(cb)

            lines.append(f"### {bid} · {title}")
            lines.append("")
            lines.append(f"- **严重度**：{sev} | **模块**：{module} | **复现**：{repro}×")
            lines.append(f"- **修复进度**：{progress_str}")
            if q:
                lines.append(f"- **问句**：「{q}」")
            # 找同根因的其他 bug
            same_root = [e2.get("id") for e2 in open_entries
                         if e2.get("id") != bid and e2.get("rootcause") == rootcause and rootcause]
            if same_root:
                lines.append(f"- **同根因**：{'/'.join(same_root)}")
            lines.append(f"- **关联**：{' · '.join(links)}")
            lines.append("")

    # ── 已解决 ──
    lines.append("## 已解决")
    lines.append("")
    if not resolved_entries:
        lines.append("*暂无*")
        lines.append("")
    else:
        lines.append("| ID | 标题 | 模块 | 修复 commit |")
        lines.append("|:-:|------|:-:|------|")
        for e in resolved_entries:
            bid = e.get("id", "?")
            title = e.get("title", "").strip("'\"")
            module = e.get("module", "?")
            p = BUGLOG / e.get("_path", "")
            prog, commit = "", ""
            try:
                prog, commit = _parse_fix_progress(p.read_text(encoding="utf-8"))
            except Exception:
                pass
            c_str = commit if commit else "—"
            lines.append(f"| {bid} | {title} | {module} | {c_str} |")
        lines.append("")

    # ── 修复时间线 ──
    lines.append("---")
    lines.append("")
    lines.append("## 修复时间线（倒序）")
    lines.append("")
    timeline = _parse_fix_timeline(entries)
    if not timeline:
        lines.append("*暂无修复记录*")
        lines.append("")
    else:
        lines.append("| 日期 | commit | 修复内容 | 关联 Bug |")
        lines.append("|------|--------|----------|:---:|")
        for d, a, c, bids in timeline:
            bids_str = "/".join(bids)
            c_str = c if c else "—"
            a_short = a[:60] + ("..." if len(a) > 60 else "")
            lines.append(f"| {d} | {c_str} | {a_short} | {bids_str} |")
        lines.append("")

    # ── 复发趋势 ──
    lines.append("## 复发趋势（repro ≥ 2）")
    lines.append("")
    if not rec:
        lines.append("*暂无复发项*")
        lines.append("")
    else:
        for e, cnt in rec:
            bid = e.get("id", "?")
            title = e.get("title", "").strip("'\"")
            status = e.get("_status", "?")
            lines.append(f"- **{bid}** · {title} — {cnt}× 复现（{status}）")
        lines.append("")

    # ── 飞轮对接 ──
    lines.append("---")
    lines.append("")
    lines.append("## 飞轮对接")
    lines.append("")
    lines.append(f"- **飞轮用例**：{tc_count} 个（`tests/emc_test_cases.md`）")
    lines.append(f"- **最近报告**：{flywheel_info or '—'}（`tests/reports/`）")
    lines.append("- **仪表盘**：`?test=1` → 仪表盘 tab（KPI + 未解决清单 + 复发趋势 + 回归关注）")
    lines.append("- **索引文件**：[`_index.md`](_index.md) · [`_trend.md`](_trend.md) · [`_regression.md`](_regression.md)")
    lines.append("- **条目目录**：[`open/`](open/) · [`resolved/`](resolved/)")
    lines.append("")

    return "\n".join(lines)


# ── 主入口 ──────────────────────────────────────────────────────────
def _write(path, content):
    path.write_text(content, encoding="utf-8")


def _strip_timestamp(text):
    """去「最后更新」时间戳行（--check 比对用——render_summary 每次重渲染分钟变化·逐字节比对必红）。"""
    return "\n".join(l for l in text.splitlines() if "最后更新" not in l)


def main():
    check = "--check" in sys.argv
    entries = load_entries()
    if not check:
        _write(INDEX, render_index(entries))
        _write(TREND, render_trend(entries))
        _write(REGRESSION, render_regression(entries))
        _write(SUMMARY, render_summary(entries))
        print(f"[OK] buglog index regenerated: {len(entries)} entries -> {INDEX.name} + {TREND.name} + {REGRESSION.name} + {SUMMARY.name}")
        print(f"[OK] next_id = {next_id(entries)}")
        return 0

    # --check：比对现存索引与应生成内容（忽略「最后更新」时间戳行·CB-10 ③）
    stale = []
    for path, renderer in ((INDEX, render_index), (TREND, render_trend), (REGRESSION, render_regression), (SUMMARY, render_summary)):
        if not path.exists():
            stale.append(f"{path.name} missing")
            continue
        if _strip_timestamp(path.read_text(encoding="utf-8")) != _strip_timestamp(renderer(entries)):
            stale.append(f"{path.name} out of sync (run: py tests/buglog/_gen_index.py)")
    if stale:
        print("[ERR] buglog index stale:\n  " + "\n  ".join(stale))
        return 1
    print(f"[OK] buglog index in sync ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
