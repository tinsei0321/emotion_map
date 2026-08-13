# -*- coding: utf-8 -*-
"""page7 密度+分层 排名：生成 TOP20 统计表（Excel）。"""
import csv, pathlib, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

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
        社区=c, 楼栋=bldg,
        体检安全=tj_safe, 体检民生=tj_min,
        热线安全=r_safe, 热线民生=r_min,
        客观=obj, 主观=sub,
        客观密度=obj / bldg * 100,
        主观密度=sub / bldg * 100,
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

top = shuang[:99] + ke[:8] + zh[:7]
if len(top) > 20:
    top = top[:20]

print("分层计数:", dict(Counter(r["分层"] for r in rows)))
print("TOP 列表:")
for i, r in enumerate(top, 1):
    print(f"{i:2d} {r['社区']:<8} 楼栋{int(r['楼栋']):>3} 客观{int(r['客观']):>4}({r['客观密度']:6.1f}) 主观{int(r['主观']):>4}({r['主观密度']:6.1f}) {r['分层']} {r['低置信']}")

# ---- 写 Excel ----
wb = Workbook()
ws = wb.active
ws.title = "分层TOP20"

header = ["序", "社区", "楼栋数", "体检隐患(点)", "客观密度(每百栋)", "热线诉求(件)", "主观密度(每百栋)", "分层", "备注"]
ws.append(header)
for i, r in enumerate(top, 1):
    ws.append([
        i, r["社区"], int(r["楼栋"]), int(r["客观"]), round(r["客观密度"], 1),
        int(r["主观"]), round(r["主观密度"], 1), r["分层"], r["低置信"],
    ])

# 双高四维副表
ws2 = wb.create_sheet("双高四维")
ws2.append(["社区", "体检安全", "体检民生", "热线安全", "热线民生", "楼栋数"])
for r in shuang:
    ws2.append([r["社区"], int(r["体检安全"]), int(r["体检民生"]), int(r["热线安全"]), int(r["热线民生"]), int(r["楼栋"])])

thin = Side(style="thin", color="999999")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
bold = Font(bold=True)
for sheet in (ws, ws2):
    for row in sheet.iter_rows():
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(horizontal="center", vertical="center")
    for cell in sheet[1]:
        cell.font = bold
    # 列宽自适应
    for col in sheet.columns:
        letter = col[0].column_letter
        w = max(len(str(c.value)) for c in col if c.value is not None) + 4
        sheet.column_dimensions[letter].width = min(max(w, 8), 22)

out = BASE / "page7小结" / "page7_分层TOP20_2026-08-14.xlsx"
wb.save(out)
print("\n已写出:", out)
