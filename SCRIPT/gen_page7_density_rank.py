# -*- coding: utf-8 -*-
"""page7 密度+分层 排名：生成 TOP20 统计表（Excel·四维数据条）。"""
import csv, pathlib, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.formatting.rule import DataBarRule

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
    rows.append(dict(
        社区=c, 楼栋=bldg,
        体检安全=tj_safe, 体检民生=tj_min,
        热线安全=r_safe, 热线民生=r_min,
        体检安全密度=tj_safe / bldg * 100,
        体检民生密度=tj_min / bldg * 100,
        热线安全密度=r_safe / bldg * 100,
        热线民生密度=r_min / bldg * 100,
        客观=tj_safe + tj_min,
        主观=r_safe + r_min,
        客观密度=(tj_safe + tj_min) / bldg * 100,
        主观密度=(r_safe + r_min) / bldg * 100,
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

shuang = sorted([r for r in rows if r["分层"] == "双高"], key=lambda r: -r["主观密度"])
ke = sorted([r for r in rows if r["分层"] == "客观高"], key=lambda r: -r["客观密度"])
zh = sorted([r for r in rows if r["分层"] == "主观高"], key=lambda r: -r["主观密度"])
top = shuang + ke[:8] + zh[:7]
if len(top) > 20:
    top = top[:20]

global_max = max(max(r["体检安全密度"], r["体检民生密度"], r["热线安全密度"], r["热线民生密度"]) for r in top)

# ---- 写 Excel ----
wb = Workbook()
ws = wb.active
ws.title = "分层TOP20"

header = ["序", "社区", "楼栋",
          "体检安全\n(每百栋)", "体检民生\n(每百栋)",
          "热线安全\n(每百栋)", "热线民生\n(每百栋)",
          "体检隐患\n(点)", "热线诉求\n(件)", "分层", "备注"]
ws.append(header)

for i, r in enumerate(top, 1):
    ws.append([
        i, r["社区"], int(r["楼栋"]),
        round(r["体检安全密度"], 1), round(r["体检民生密度"], 1),
        round(r["热线安全密度"], 1), round(r["热线民生密度"], 1),
        int(r["客观"]), int(r["主观"]), r["分层"], r["低置信"],
    ])

n = len(top)
last = n + 1  # 数据从第2行到第 n+1 行
# 体检(客观)蓝条 · 热线(主观)橙条 · 统一刻度 0..global_max
ws.conditional_formatting.add(
    f"D2:E{last}",
    DataBarRule(start_type="num", start_value=0, end_type="num", end_value=round(global_max, 1),
                color="4472C4", showValue=True),
)
ws.conditional_formatting.add(
    f"F2:G{last}",
    DataBarRule(start_type="num", start_value=0, end_type="num", end_value=round(global_max, 1),
                color="ED7D31", showValue=True),
)

# 双高四维副表（原始件数·供 4 根柱子图）
ws2 = wb.create_sheet("双高四维")
ws2.append(["社区", "体检安全(点)", "体检民生(点)", "热线安全(件)", "热线民生(件)", "楼栋"])
for r in shuang:
    ws2.append([r["社区"], int(r["体检安全"]), int(r["体检民生"]), int(r["热线安全"]), int(r["热线民生"]), int(r["楼栋"])])

thin = Side(style="thin", color="D9D9D9")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
bold = Font(bold=True)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
for sheet in (ws, ws2):
    for row in sheet.iter_rows():
        for cell in row:
            cell.border = border
            cell.alignment = center
    for cell in sheet[1]:
        cell.font = bold
    for col in sheet.columns:
        letter = col[0].column_letter
        w = max(len(str(c.value).replace("\n", "")) for c in col if c.value is not None) + 3
        sheet.column_dimensions[letter].width = min(max(w, 8), 18)

# 图例说明行（放在表格下方）
note_row = last + 2
ws.cell(row=note_row, column=1, value="图例：蓝色数据条 = 体检（客观·每百栋）；橙色数据条 = 热线（主观·每百栋）；两色同刻度，可横向并排比较。")
ws.cell(row=note_row, column=1).font = Font(italic=True, color="808080")

out = BASE / "page7小结" / "page7_分层TOP20_2026-08-14.xlsx"
wb.save(out)
print("已写出:", out)
print("双高数:", len(shuang), " 客观高数:", len(ke), " 主观高数:", len(zh))
