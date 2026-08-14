# -*- coding: utf-8 -*-
# page7 最终三张表（一张 Excel·三个 sheet）。
# Sheet1 原表（直接保留 page7_分组汇总_2026-08-14.xlsx 原样·含条件格式填充条）
# Sheet2 分类表（双高/客观高/主观高）
# Sheet3 体检诉求对比（合并安全+民生·保留原表填充条样式：条件格式 DataBar·蓝色体检/橙色诉求·实心无渐变）
import os

import openpyxl
from openpyxl.comments import Comment
from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P7 = os.path.join(ROOT, "DATA", "analysis", "page7小结")
SRC = os.path.join(P7, "page7_分组汇总_2026-08-14.xlsx")
OUT = os.path.join(P7, "page7_分组汇总_2026-08-14_最终.xlsx")

HDR_FILL = PatternFill("solid", fgColor="404040")
HDR_FONT = Font(bold=True, color="FFFFFF")
LAYER_FILL = {
    "双高": PatternFill("solid", fgColor="FCE4EC"),
    "客观高": PatternFill("solid", fgColor="E3EDF7"),
    "主观高": PatternFill("solid", fgColor="FDEBD9"),
}
LAYER_HEAD = {
    "双高": PatternFill("solid", fgColor="C00000"),
    "客观高": PatternFill("solid", fgColor="1F4E79"),
    "主观高": PatternFill("solid", fgColor="C55A11"),
}
LABEL_FONT = {
    "双高": Font(bold=True, color="C00000"),
    "客观高": Font(bold=True, color="1F4E79"),
    "主观高": Font(bold=True, color="C55A11"),
}
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)

# 唯一数据源：社区, 楼栋, 体检安全, 体检民生, 诉求安全, 诉求民生, 层
ROWS = [
    ("营盘路社区", 66, 0, 37, 10, 107, "双高"),
    ("宝联社区", 94, 3, 26, 29, 127, "双高"),
    ("汕头路社区", 39, 14, 3, 10, 97, "双高"),
    ("胜利四路社区", 44, 6, 10, 20, 95, "双高"),
    ("胜利二路社区", 30, 6, 3, 9, 102, "双高"),
    ("深圳路社区", 127, 78, 29, 3, 4, "客观高"),
    ("西峡社区", 78, 82, 9, 3, 32, "客观高"),
    ("金安岭社区", 56, 73, 11, 9, 11, "客观高"),
    ("镇境山社区", 78, 67, 15, 4, 1, "客观高"),
    ("幸福路社区", 58, 48, 17, 1, 0, "客观高"),
    ("新隆康路社区", 130, 47, 15, 6, 58, "客观高"),
    ("果园路社区", 93, 25, 26, 11, 62, "客观高"),
    ("桥北社区", 48, 17, 20, 0, 0, "客观高"),
    ("朝阳路社区", 84, 7, 4, 58, 536, "主观高"),
    ("万达社区", 69, 0, 7, 50, 451, "主观高"),
    ("港务社区", 106, 2, 15, 83, 334, "主观高"),
    ("建设社区", 66, 0, 9, 52, 320, "主观高"),
    ("岳湾路社区", 83, 0, 2, 19, 206, "主观高"),
    ("大学路社区", 97, 1, 6, 44, 178, "主观高"),
    ("伍临路社区", 55, 0, 8, 20, 201, "主观高"),
]

LAYER_ORDER = ["双高", "客观高", "主观高"]
LAYER_TITLES = {
    "双高": "① 双高 · 体检+诉求都高（5 个）",
    "客观高": "② 客观隐患高 · 体检独证（诉求未暴露 · 8 个）",
    "主观高": "③ 主观诉求高 · 热线独证（体检未印证 · 7 个）",
}
LAYER_LABELS = {
    "双高": "双高 ★",
    "客观高": "客观隐患高\n诉求未暴露",
    "主观高": "主观诉求高\n体检未印证",
}


def d(n, b):
    return round(n / b * 100, 1) if b else 0


def _layer_head(ws, r, layer, ncol):
    ws.cell(r, 1, LAYER_TITLES[layer])
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncol)
    for c in range(1, ncol + 1):
        cell = ws.cell(r, c)
        cell.fill = LAYER_HEAD[layer]
        cell.font = Font(bold=True, color="FFFFFF")
        cell.border = BORDER
    ws.cell(r, 1).alignment = LEFT


def _hdr(ws, r, vals):
    for c, h in enumerate(vals, 1):
        cell = ws.cell(r, c, h)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.border = BORDER
        cell.alignment = CENTER


def build_classify(ws):
    _hdr(ws, 1, ["序", "社区", "楼栋", "体检问题（点）", "市民诉求（件）", "每百栋（体检/诉求）", "综合评估"])
    r = 2
    seq = 0
    for layer in LAYER_ORDER:
        _layer_head(ws, r, layer, 7)
        r += 1
        for name, b, tsa, tms, ssa, ssm, _l in ROWS:
            if _l != layer:
                continue
            seq += 1
            tj = tsa + tms
            sub = ssa + ssm
            dens = f"{d(tj, b)} / {d(sub, b) if sub else '—'}"
            vals = [seq, name, b, tj, sub if sub else "—", dens, LAYER_LABELS[layer]]
            for c, v in enumerate(vals, 1):
                cell = ws.cell(r, c, v)
                cell.border = BORDER
                cell.fill = LAYER_FILL[layer]
                cell.alignment = CENTER if c in (1, 3, 4, 5, 6) else LEFT
                if c == 7:
                    cell.font = LABEL_FONT[layer]
                    cell.alignment = CENTER
            r += 1
    for i, w in enumerate([5, 14, 7, 12, 12, 18, 20], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w


def build_compare(ws):
    """Sheet3 体检诉求对比：合并安全+民生，保留原表条件格式 DataBar 填充条（实心无渐变）。"""
    _hdr(ws, 1, ["序号", "名称", "楼栋", "体检（每百栋）", "诉求（每百栋）", "评估"])
    r = 2
    seq = 0
    first_data_row = None
    for layer in LAYER_ORDER:
        _layer_head(ws, r, layer, 6)
        r += 1
        for name, b, tsa, tms, ssa, ssm, _l in ROWS:
            if _l != layer:
                continue
            seq += 1
            tj = tsa + tms
            sub = ssa + ssm
            vals = [seq, name, b, d(tj, b), d(sub, b), LAYER_LABELS[layer]]
            for c, v in enumerate(vals, 1):
                cell = ws.cell(r, c, v)
                cell.border = BORDER
                cell.fill = LAYER_FILL[layer]
                cell.alignment = CENTER if c in (1, 3, 4, 5) else LEFT
                if c == 6:
                    cell.font = LABEL_FONT[layer]
                    cell.alignment = CENTER
            if first_data_row is None:
                first_data_row = r
            r += 1
    last_data_row = r - 1
    # 填充条：条件格式 DataBar（体检蓝 / 诉求橙），分轨刻度（体检 0~150 点/百栋、诉求 0~726 件/百栋）——避免体检条被诉求大值压扁
    ws.conditional_formatting.add(
        f"D{first_data_row}:D{last_data_row}",
        DataBarRule(start_type="num", start_value=0, end_type="num", end_value=150,
                    color="1F4E79", showValue=True),
    )
    ws.conditional_formatting.add(
        f"E{first_data_row}:E{last_data_row}",
        DataBarRule(start_type="num", start_value=0, end_type="num", end_value=726,
                    color="C55A11", showValue=True),
    )
    for i, w in enumerate([5, 14, 7, 13, 13, 18], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w


def main():
    # 原表直接保留（含条件格式填充条），在此基础上加两张表
    wb = openpyxl.load_workbook(SRC)
    ws0 = wb.worksheets[0]
    ws0.title = "1原表"
    ws2 = wb.create_sheet("2分类表")
    build_classify(ws2)
    ws3 = wb.create_sheet("3体检诉求对比")
    build_compare(ws3)
    # 内部注（不对外·你我看即可）：作图实际社区面数 = 体检对象西陵+伍家岗全集（约130），统计底数 120（体检报告），明面统一按 120、图表对应。
    ws3["A1"].comment = Comment("内部注（不对外）：作图实际社区面数=体检对象西陵+伍家岗全集(约130面)，统计底数=120(体检报告)；明面统一按120、图表对应。", "Codex")
    wb.save(OUT)
    _solid_databars(OUT)
    print("[OK]", os.path.basename(OUT))


def _solid_databars(path):
    """把 Sheet3 的 dataBar 改为实心（gradient=0）——openpyxl 未暴露该属性，这里直接改 XML。"""
    import re
    import shutil
    import zipfile

    tmp = path + ".tmp"
    with zipfile.ZipFile(path, "r") as zin:
        # 找非 sheet1 且含 dataBar 的 sheet xml（即 Sheet3；原表在 sheet1 保留原样）
        target = None
        for n in zin.namelist():
            if re.match(r"xl/worksheets/sheet\d+\.xml$", n):
                xml = zin.read(n).decode("utf-8")
                if n != "xl/worksheets/sheet1.xml" and "<dataBar" in xml:
                    target = n
                    break
        if not target:
            return
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == target:
                    xml = data.decode("utf-8")
                    xml = re.sub(r'<dataBar([^>]*)>', r'<dataBar gradient="0"\1>', xml)
                    data = xml.encode("utf-8")
                zout.writestr(item, data)
    shutil.move(tmp, path)


if __name__ == "__main__":
    main()
