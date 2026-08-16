# -*- coding: utf-8 -*-
# CB-30 12345 有坐标点数据治理（可复现）
# 流程：有坐标点筛选 -> 事件三大类 -> 9类问题(落图版) -> 社区/村 sjoin(ok点·城市优先)
# 输出：12345_有坐标点.geojson + 社区x9类 + 村x9类 矩阵 CSV
import json
import os
import pandas as pd
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = r"D:\OneDrive\2026\15_城市更新专项规划研究\1 宜昌市城市体检\EMC数据中转站\06_主观数据治理\12345_治理清洗版.csv"
CHECKUP = os.path.join(ROOT, "DATA", "analysis", "12345主观", "checkup_12345_2024.csv")   # CB-39 A2/E16：迁出演示池
COMM = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")
VILL = os.path.join(ROOT, "DATA", "analysis", "18村_面范围.geojson")
OUT = os.path.join(ROOT, "DATA", "analysis", "12345主观")


def _event3(t):
    if t == "投诉":
        return "投诉"
    if t in ("求助", "咨询"):
        return "求助"
    if t == "建议":
        return "建议"
    return "其他"


def _nine9(board, pt):
    if board == "安全韧性底线":
        m = {"市政管网": "管网安全", "交通设施": "出行安全",
             "安全消防": "消防安全", "环境治理": "环境安全"}
        return m.get(pt, "安全-其他")
    if board == "民生基础需求":
        if pt in ("噪声治理", "施工管理", "街面秩序"):
            return "噪声"
        if pt == "停车设施":
            return "停车"
        if pt in ("住房", "城市更新"):
            return "住宅"
        if pt in ("交通设施", "市政管网"):
            return "出行"
        if pt in ("物业管理", "环境治理", "公服设施"):
            return "物业"
        return "民生-其他"
    return "其他"


def _aspect(board):
    return {"安全韧性底线": "安全韧性", "民生基础需求": "民生基础"}.get(board, "其他")


def _load_geoms(path, name_key):
    with open(path, encoding="utf-8") as f:
        g = json.load(f)
    geoms, names = [], []
    for feat in g["features"]:
        geoms.append(shape(feat["geometry"]))
        names.append(feat["properties"][name_key])
    return geoms, names, STRtree(geoms)


def main():
    df = pd.read_csv(CLEAN, encoding="utf-8-sig", low_memory=False, dtype={"办件编号": str})
    ck = pd.read_csv(CHECKUP, encoding="utf-8-sig", low_memory=False, dtype={"办件编号": str})

    has = ck[ck["lon"].notna()].copy()
    ev = df.set_index("办件编号")["诉求类型_归"]
    has["事件"] = has["办件编号"].map(ev).map(_event3)
    has["类9"] = [_nine9(b, p) for b, p in zip(has["board"], has["project_type"])]
    has["方面"] = has["board"].map(_aspect)
    has["区域"] = has["办件编号"].map(df.set_index("办件编号")["区域_清洗"])
    has["社区"] = None
    has["村"] = None

    comm_g, comm_n, comm_tree = _load_geoms(COMM, "社区")
    vill_g, vill_n, vill_tree = _load_geoms(VILL, "SQMC")

    ok = has[has["geocode_status"] == "ok"]
    idx = ok.index.tolist()
    ok_lon = ok["lon"].astype(float).values
    ok_lat = ok["lat"].astype(float).values

    n_city = n_vill = n_out = 0
    for i, lon, lat in zip(idx, ok_lon, ok_lat):
        pt = Point(lon, lat)
        # CB-33 修复：STRtree.query 只做 bbox 命中，须精确 contains/covers 判定（否则相邻社区 bbox 重叠致错标）。
        matched = False
        for gi in comm_tree.query(pt):
            if comm_g[gi].contains(pt) or comm_g[gi].covers(pt):
                has.at[i, "社区"] = comm_n[gi]
                n_city += 1
                matched = True
                break
        if matched:
            continue
        for gi in vill_tree.query(pt):
            if vill_g[gi].contains(pt) or vill_g[gi].covers(pt):
                has.at[i, "村"] = vill_n[gi]
                n_vill += 1
                matched = True
                break
        if matched:
            continue
        n_out += 1

    print(f"[OK] ok 点 {len(ok)}：命中社区 {n_city} / 命中村 {n_vill} / 范围外 {n_out}")

    def _dump(sub, name):
        feats = []
        for _, r in sub.iterrows():
            props = {
                "办件编号": r["办件编号"], "事件": r["事件"], "类9": r["类9"],
                "方面": r["方面"], "geocode_status": r["geocode_status"],
                "board": r["board"], "project_type": r["project_type"],
                "社区": r["社区"], "村": r["村"],
            }
            feats.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]},
                "properties": props,
            })
        gj = {"type": "FeatureCollection", "features": feats}
        out_gj = os.path.join(OUT, name)
        with open(out_gj, "w", encoding="utf-8") as f:
            json.dump(gj, f, ensure_ascii=False)
        print(f"[OK] {name} ({len(feats)} 点)")

    _dump(has, "12345_有坐标点.geojson")
    for asp in ("安全韧性", "民生基础"):
        sub = has[has["方面"] == asp]
        _dump(sub, f"12345_{asp}_有坐标点.geojson")
        # ok 点按社区/村拆分
        _dump(sub[(sub["geocode_status"] == "ok") & sub["社区"].notna()],
              f"12345_{asp}_社区点.geojson")
        _dump(sub[(sub["geocode_status"] == "ok") & sub["村"].notna()],
              f"12345_{asp}_村点.geojson")
        # region 区级点
        _dump(sub[sub["geocode_status"] == "region"],
              f"12345_{asp}_区级点.geojson")

    city_ok = has[(has["geocode_status"] == "ok") & has["社区"].notna()]
    city_mat = pd.crosstab(city_ok["社区"], city_ok["类9"])
    city_mat.to_csv(os.path.join(OUT, "12345_社区x9类.csv"), encoding="utf-8-sig")
    print(f"[OK] 社区 x 9类 -> {len(city_mat)} 社区")

    vill_ok = has[(has["geocode_status"] == "ok") & has["村"].notna()]
    vill_mat = pd.crosstab(vill_ok["村"], vill_ok["类9"])
    vill_mat.to_csv(os.path.join(OUT, "12345_村x9类.csv"), encoding="utf-8-sig")
    print(f"[OK] 村 x 9类 -> {len(vill_mat)} 村")

    region = has[has["geocode_status"] == "region"]
    reg = pd.crosstab(region["区域"], region["类9"])
    reg.to_csv(os.path.join(OUT, "12345_区级x9类.csv"), encoding="utf-8-sig")
    print(f"[OK] region 区级 x 9类 -> {len(reg)} 区")


if __name__ == "__main__":
    main()
