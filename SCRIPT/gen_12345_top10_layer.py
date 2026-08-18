# -*- coding: utf-8 -*-
"""page7 数据图层：12345 两方面（民生基础+安全韧性）诉求总量 TOP10/TOP20 社区面。

口径（与 page7 两表口径 2026-08-17 完全一致·勿另起炉灶）：
- 源数据 = DATA/analysis/12345主观/12345_社区x9类_全覆盖.csv
  （174 社区范围内落点·ok 精确点·154 社区有落点·区级点不进社区表）
- 总量 = 类9 九列求和（= 两方面合计）；
  方面拆分（点级「方面」字段核验 2026-08-18）：
    民生基础 = {住宅, 停车, 出行, 噪声, 物业}
    安全韧性 = {出行安全, 消防安全, 环境安全, 管网安全}
- 社区面 = DATA/analysis/体检对象_社区_面.geojson 原样单社区面（每社区一个 feature·不合并）
产出（TOP_NS 驱动·幂等可复跑）：
  1) DATA/boundaries/presets/12345_top10_社区.geojson / 12345_top20_社区.geojson
  2) presets manifest 注册（体检控件对象组末尾·幂等）
对账断言：TOP20 全量锁定（前 10 = 按页数据更新 md「主观表头部」·11-20 = 2026-08-18 基线），
口径漂移即报错。第 20 名边界无并列（88 vs 83·2026-08-18 实测）。
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX_CSV = os.path.join(ROOT, "DATA", "analysis", "12345主观", "12345_社区x9类_全覆盖.csv")
COMMUNITY_FACE = os.path.join(ROOT, "DATA", "analysis", "体检对象_社区_面.geojson")
MANIFEST = os.path.join(ROOT, "DATA", "boundaries", "presets", "manifest.json")

MINSHENG = {"住宅", "停车", "出行", "噪声", "物业"}  # 其余类9列 = 安全韧性

TOP_NS = [10, 20]

# 主观表头部（体检2026补充_按页数据更新_2026-08-17.md·page7 节）——对账基准 1-10 名
EXPECTED_1_10 = [
    ("朝阳路社区", 594), ("万达社区", 501), ("港务社区", 417), ("建设社区", 372),
    ("岳湾路社区", 225), ("大学路社区", 222), ("伍临路社区", 221), ("东城社区", 191),
    ("张家湾社区", 187), ("宝联社区", 156),
]
# 2026-08-18 基线 11-20 名（源头未变则恒定）
EXPECTED_11_20 = [
    ("体育场路社区", 136), ("枫香树社区", 126), ("营盘路社区", 117), ("胜利四路社区", 115),
    ("胜利二路社区", 111), ("冯家湾社区", 108), ("汕头路社区", 107), ("花艳社区", 97),
    ("小林园社区", 93), ("柏临河路社区", 88),
]
EXPECTED_TOP20 = EXPECTED_1_10 + EXPECTED_11_20


def _manifest_item(n):
    return {
        "id": f"page7_12345_top{n}",
        "label": f"12345-诉求总量TOP{n}社区（{n}·两方面合计）",
        "file": f"12345_top{n}_社区.geojson",
        "nameField": "社区",
        "note": (f"page7·12345 两方面（民生基础+安全韧性）诉求总量 TOP{n} 社区·"
                 "ok 精确点口径与两表一致（08-17 扩域版）·单社区面不合并"),
    }


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("gbk", "replace").decode("gbk"))


def load_top(n):
    with open(MATRIX_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    stats = []
    for r in rows:
        ms = sum(int(r[c]) for c in MINSHENG)
        aq = sum(int(r[c]) for c in r if c != "社区" and c not in MINSHENG)
        stats.append((r["社区"], ms + aq, ms, aq))
    stats.sort(key=lambda x: (-x[1], x[0]))
    top = stats[:n]

    # 对账断言：TOP20 全量锁定（含 TOP10 = md 主观表头部）
    if n >= 10:
        anchor = EXPECTED_TOP20[:n] if n <= 20 else EXPECTED_TOP20
        got = [(c, t) for c, t, _, _ in top[:len(anchor)]]
        if got != anchor:
            diff = [(i + 1, e, g) for i, (e, g) in enumerate(zip(anchor, got)) if e != g]
            raise SystemExit(f"[ERR] TOP{n} 与锁定基线不一致（名次·期望·实际）: {diff}")
        _safe_print(f"[OK] TOP{n} 对账通过（1-10 = md 主观表头部·11+ = 08-18 基线）")
    return top


def build_geojson(top, n):
    out_path = os.path.join(ROOT, "DATA", "boundaries", "presets", f"12345_top{n}_社区.geojson")
    with open(COMMUNITY_FACE, encoding="utf-8") as f:
        faces = json.load(f)
    by_name = {}
    for ft in faces["features"]:
        nm = ft["properties"].get("SQMC")
        if nm and nm not in by_name:
            by_name[nm] = ft

    feats = []
    for rank, (name, total, ms, aq) in enumerate(top, 1):
        src = by_name.get(name)
        if src is None:
            raise SystemExit(f"[ERR] 社区面缺失: {name}")
        props = dict(src["properties"])  # 保留 SQMC/SSJD/类型/来源 原属性
        props.update({
            "社区": name,
            "排名": rank,
            "诉求总量": total,
            "民生基础件": ms,
            "安全韧性件": aq,
            "每周约件数": round(total / 52),  # 2024 全年 52 周·叙事口径同主观档
        })
        feats.append({"type": "Feature", "properties": props, "geometry": src["geometry"]})

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False)
    _safe_print(f"[OK] 写出 {out_path}（{len(feats)} 社区·单面不合并）")


def register_manifest(n):
    item = _manifest_item(n)
    with open(MANIFEST, encoding="utf-8") as f:
        data = json.load(f)
    target = None
    for g in data:
        if any(it.get("id") == "checkup_cfg_community_xlwj" for it in g.get("items", [])):
            target = g
            break
    if target is None:
        raise SystemExit("[ERR] 未找到体检控件对象组")
    if any(it.get("id") == item["id"] for it in target["items"]):
        _safe_print(f"[skip] manifest 已存在 {item['id']}")
        return
    target["items"].append(item)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    _safe_print(f"[OK] manifest 注册 {item['id']} → 体检控件对象组末尾")


def main():
    for n in TOP_NS:
        top = load_top(n)
        for c, t, ms, aq in top:
            _safe_print(f"  {c}: 总{t}（民生{ms}+安全{aq}）")
        build_geojson(top, n)
        register_manifest(n)


if __name__ == "__main__":
    main()
