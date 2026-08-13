# -*- coding: utf-8 -*-
# 排查：tip 社区提示错误（石板/建设/港务 社区错标）+ grid 聚合颜色异常。
import json
import os
from collections import Counter

from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C1 = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区.geojson")
C2 = os.path.join(ROOT, "DATA", "boundaries", "presets", "checkup_配置_社区174.geojson")
PT = os.path.join(ROOT, "DATA", "analysis", "12345主观", "12345_有坐标点.geojson")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    c1 = load(C1)
    c2 = load(C2)
    f1 = c1["features"]
    f2 = c2["features"]
    # 名字段
    key = None
    for f in f1:
        for k, v in f["properties"].items():
            if v:
                key = k
                break
        if key:
            break
    n1 = {f["properties"].get(key): shape(f["geometry"]) for f in f1}
    n2 = {f["properties"].get(key): shape(f["geometry"]) for f in f2}
    print(f"名字段={key} | C1 {len(n1)} · C2 {len(n2)}")
    print(f"C1/C2 名字差异: 仅C1={sorted(set(n1)-set(n2))} 仅C2={sorted(set(n2)-set(n1))}")

    # 含石板/建设/港务 的名字
    for kw in ("石板", "建设", "港务", "石板溪", "石板冲"):
        hits1 = sorted(n for n in n1 if kw in n)
        hits2 = sorted(n for n in n2 if kw in n)
        print(f"含[{kw}]: C1={hits1} C2={hits2}")

    # 几何一致性：同名社区 C1 vs C2 的面积/质心差
    print("\n同名社区 C1 vs C2 几何差异（面积差 > 1% 或质心差 > 100m）:")
    diff = 0
    for name in sorted(set(n1) & set(n2)):
        g1, g2 = n1[name], n2[name]
        a1, a2 = g1.area, g2.area
        if a1 == 0:
            continue
        area_d = abs(a1 - a2) / a1
        c1c, c2c = g1.centroid, g2.centroid
        # 度 -> 米 粗略（lat 30°）
        dx = (c1c.x - c2c.x) * 111320 * 0.866
        dy = (c1c.y - c2c.y) * 110540
        dist = (dx * dx + dy * dy) ** 0.5
        if area_d > 0.01 or dist > 100:
            diff += 1
            if name in ("石板社区", "石板溪社区", "建设社区", "港务社区") or diff <= 20:
                print(f"  {name}: 面积差={area_d*100:.1f}% 质心差={dist:.0f}m")
    print(f"  差异总数={diff}")

    # 检查多边形重叠（可能致 point-in-polygon 错标）
    print("\n检查多边形重叠（交集面积 > 100 ㎡）:")
    geoms = [shape(f["geometry"]) for f in f1]
    names = [f["properties"].get(key) for f in f1]
    overlaps = 0
    for i in range(len(geoms)):
        for j in range(i + 1, len(geoms)):
            inter = geoms[i].intersection(geoms[j])
            if inter.is_empty:
                continue
            if inter.area > 100 / (111320**2):  # 100 ㎡ -> 度²
                overlaps += 1
                if overlaps <= 30:
                    print(f"  {names[i]} ↔ {names[j]}: 交集面积≈{inter.area*111320**2:.0f}㎡")
    print(f"  重叠总数={overlaps}")

    # 对比：sjoin 社区字段 vs 精确 point-in-polygon（找错标根因）
    print("\n对比 sjoin 社区 vs 精确 point-in-polygon:")
    pts = load(PT)
    pfeats = pts["features"]
    from shapely.geometry import Point
    g1 = [shape(f["geometry"]) for f in f1]
    n1l = [f["properties"].get(key) for f in f1]
    # 预建 point-in-polygon 精确判定
    def exact_comm(pt):
        for gi, name in zip(g1, n1l):
            if gi.contains(pt) or gi.covers(pt):
                return name
        return None
    mism = {}
    for pf in pfeats:
        prop = pf["properties"]
        if prop.get("geocode_status") != "ok" or not prop.get("社区"):
            continue
        lon, lat = pf["geometry"]["coordinates"]
        exact = exact_comm(Point(lon, lat))
        sjoin = prop.get("社区")
        if exact and exact != sjoin:
            mism[(sjoin, exact)] = mism.get((sjoin, exact), 0) + 1
    print(f"  错标点数（sjoin≠精确）: {sum(mism.values())}")
    for k, v in sorted(mism.items(), key=lambda x: -x[1])[:25]:
        print(f"    sjoin[{k[0]}] → 精确[{k[1]}] : {v}")


if __name__ == "__main__":
    main()
