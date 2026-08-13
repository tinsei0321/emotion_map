# -*- coding: utf-8 -*-
"""page7 汇总表：六列 + 两横条上下并列 + 任务量分层排序。"""
import csv, pathlib, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles.colors import Color

BASE = pathlib.Path("DATA/analysis")

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def num(s):
    try:
        return float(s)
    except Exception:
        return 0.0

safe = read_csv(BASE / "安全韧性" / "安全韧性_社区3类矩阵.csv")
mins = read_csv(BASE / "民生基础" / "民生_社区5类矩阵.csv")
r123 = read_csv(BASE / "12345主观" / "12345_社区x9类_西陵伍家.csv")
denom = read_csv(BASE / "page7小结" / "社区规模分母_174.csv")

safe_map = {r["社区"]: r for r in safe}
mins_map = {r["社区"]: r for r in mins}
r123_map = {r["社区"]: r for r in r123}
denom_map = {r["社区"]: r for r in denom}

SAFE_COLS = ["管网安全", "出行安全", "消防安全", "环境安全"]
MIN_COLS = ["噪声", "停车", "住宅", "出行", "物业"]

rows = []
for c, d in denom_map.items():
    bldg = num(d["bldg_n"])
    if bldg <= 0:
        continue
    tj_safe = num(safe_map[c]["总点数"]) if c in safe_map else 0.0
    tj_min = num(mins_map[c]["总点数"]) if c in mins_map else 0.0
    r_safe = sum(num(r123_map[c][k]) for k in SAFE_COLS) if c in r123_map else 0.0
    r_min = sum(num(r123_map[c][k]) for k in MIN_COLS) if c in r123_map else 0.0
    obj = tj_safe + tj_min
    sub = r_safe + r_min
    rows.append(dict(
        社区=c, 楼栋=bldg, resi=num(d["resi_km2"]),
        体检安全=tj_safe, 体检民生=tj_min,
        热线安全=r_safe, 热线民生=r_min,
        客观=obj, 主观=sub, 任务量=obj + sub,
        体检安全密度=tj_safe / bldg * 100, 体检民生密度=tj_min / bldg * 100,
        热线安全密度=r_safe / bldg * 100, 热线民生密度=r_min / bldg * 100,
        客观密度=obj / bldg * 100, 主观密度=sub / bldg * 100,
    ))

active = [r for r in rows if r["客观"] > 0 or r["主观"] > 0]

def pct(xs, p):
    s = sorted(xs)
    if not s:
        return 0.0
    k = (len(s) - 1) * p
    i = int(k)
    f = k - i
    return s[i] * (1 - f) + s[min(i + 1, len(s) - 1)] * f

obj_p75 = pct([r["客观密度"] for r in active], 0.75)
sub_p75 = pct([r["主观密度"] for r in active], 0.75)

for r in rows:
    oh = r["客观密度"] >= obj_p75 and r["客观"] > 0
    sh = r["主观密度"] >= sub_p75 and r["主观"] > 0
    if oh and sh:
        r["分层"] = "双高"
    elif oh:
        r["分层"] = "客观高"
    elif sh:
        r["分层"] = "主观高"
    else:
        r["分层"] = "其余"
    r["低置信"] = "低置信" if r["楼栋"] < 20 else ""

shuang = sorted([r for r in rows if r["分层"] == "双高"], key=lambda r: -r["任务量"])
dangao = sorted([r for r in rows if r["分层"] in ("客观高", "主观高")], key=lambda r: -r["任务量"])
top = shuang + dangao[:15]

tj_max = max(max(r["体检安全密度"], r["体检民生密度"]) for r in active)
rx_max = max(max(r["热线安全密度"], r["热线民生密度"]) for r in active)

def bar_len(d, mx):
    if d <= 0:
        return 0
    return max(1, round(d / mx * 12))

DEEP_BLUE = "FF1F4E79"
LIGHT_BLUE = "FF4472C4"
DEEP_ORANGE = "FFC55A11"
LIGHT_ORANGE = "FFED7D31"
RED = "FFC00000"
GRAY = "FF808080"

def bar_line(label, density, count, color, mx):
    n = bar_len(density, mx)
    bar = "█" * n if n else "—"
    return TextBlock(InlineFont(color=Color(rgb=color)), f"{label} {bar} {int(count)}")

def two_bar_cell(sl, sd, sc, scolor, ml, md, mc, mcolor, mx):
    return CellRichText(
        bar_line(sl, sd, sc, scolor, mx),
        TextBlock(InlineFont(), "\n"),
        bar_line(ml, md, mc, mcolor, mx),
    )

def assess_cell(r):
    if r["分层"] == "双高":
        label, color = "双高", RED
        star = " ★"
    elif r["分层"] == "客观高":
        label, color = "客观高", DEEP_BLUE
        star = ""
    else:
        label, color = "主观高", DEEP_ORANGE
        star = ""
    note = " 低置信" if r["低置信"] else ""
    return CellRichText(
        TextBlock(InlineFont(color=Color(rgb=color), b=True, sz=12), label + star),
        TextBlock(InlineFont(color=Color(rgb=GRAY), sz=9), f"客观{int(r['客观密度'])}/百栋 主观{int(r['主观密度'])}/百栋{note}"),
    )

# ---- 写 Excel ----
wb = Workbook()
ws = wb.active
ws.title = "page7汇总"

header = ["社区", "楼栋数", "面积\n(km²·仅参考)", "可量化指标\n(体检·点)", "可感知指标\n(12345·件)", "综合评估"]
ws.append(header)

for r in top:
    ws.append([
        r["社区"],
        int(r["楼栋"]),
        round(r["resi"], 2),
        two_bar_cell("安全", r["体检安全密度"], r["体检安全"], DEEP_BLUE,
                     "民生", r["体检民生密度"], r["体检民生"], LIGHT_BLUE, tj_max),
        two_bar_cell("安全", r["热线安全密度"], r["热线安全"], DEEP_ORANGE,
                     "民生", r["热线民生密度"], r["热线民生"], LIGHT_ORANGE, rx_max),
        assess_cell(r),
    ])

thin = Side(style="thin", color="D9D9D9")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
bold = Font(bold=True, color="FFFFFF")
header_fill = PatternFill("solid", fgColor="404040")
center = Alignment(horizontal="center", vertical="center", wrap_text=True)

for row in ws.iter_rows(min_row=1, max_row=1 + len(top)):
    for cell in row:
        cell.border = border
        cell.alignment = center
for cell in ws[1]:
    cell.font = bold
    cell.fill = header_fill

widths = {"A": 14, "B": 8, "C": 9, "D": 22, "E": 22, "F": 22}
for col, w in widths.items():
    ws.column_dimensions[col].width = w
for i in range(2, 2 + len(top)):
    ws.row_dimensions[i].height = 42
ws.row_dimensions[1].height = 34

note_row = len(top) + 3
ws.cell(row=note_row, column=1, value="图例：条长 = 每百栋密度（体检列满格≈130点/百栋、热线列满格≈654件/百栋）；条旁数字 = 原始件数/点数。")
ws.cell(row=note_row, column=1).font = Font(italic=True, color="808080")
ws.cell(row=note_row + 1, column=1, value="颜色：体检=蓝系（安全深蓝·民生浅蓝）、热线=橙系（安全深橙·民生浅橙）；综合评估标签 双高=红、客观高=蓝、主观高=橙。")
ws.cell(row=note_row + 1, column=1).font = Font(italic=True, color="808080")

out = BASE / "page7小结" / "page7_汇总表_2026-08-14.xlsx"
wb.save(out)
print("已写出:", out)
print("双高数:", len(shuang), " 单轨高数:", len(dangao))
print("排序结果:")
for i, r in enumerate(top, 1):
    print(f"{i:2d} [{r['分层']}] {r['社区']:<8} 楼栋{int(r['楼栋']):>3} 任务量{int(r['任务量']):>4} 客观{int(r['客观']):>4}({int(r['客观密度']):>3}/百栋) 主观{int(r['主观']):>4}({int(r['主观密度']):>3}/百栋)")
