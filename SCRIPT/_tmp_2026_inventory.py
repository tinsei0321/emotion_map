# -*- coding: utf-8 -*-
# 2026 体检补充数据盘点：16 层要素数/几何/CRS/属性/范围 + 与 2025 同名层重叠比对（增量vs替换判定）
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import geopandas as gpd
import pandas as pd

GIS = r"D:/OneDrive/2026/15_城市更新专项规划研究/1 宜昌市城市体检/3_gis数据"
D26 = os.path.join(GIS, "2026")
# 2025 各维度子类文件夹
D25 = {
    "住房维度问题": ["1城市体检——住房维度/安全耐久", "1城市体检——住房维度/功能完备", "1城市体检——住房维度/绿色智能"],
    "小区（社区）维度问题": ["2城市体检——小区维度/设施完善", "2城市体检——小区维度/环境宜居", "2城市体检——小区维度/管理健全"],
}


def find_2025(name):
    for sub in [s for v in D25.values() for s in v]:
        p = os.path.join(GIS, sub, name + ".shp")
        if os.path.exists(p):
            return p
    return None


rows = []
overlap_report = []
for dim in ["住房维度问题", "小区（社区）维度问题"]:
    d = os.path.join(D26, dim)
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".shp"):
            continue
        name = fn[:-4]
        p26 = os.path.join(d, fn)
        g26 = gpd.read_file(p26)
        crs26 = str(g26.crs)
        gt = g26.geom_type.value_counts().to_dict()
        b = g26.to_crs(4326).total_bounds
        flds = list(g26.columns)
        row = {"维度": dim, "图层": name, "n2026": len(g26), "几何": gt, "CRS": crs26,
               "lon范围": f"{b[0]:.3f}~{b[2]:.3f}", "lat范围": f"{b[1]:.3f}~{b[3]:.3f}", "字段": flds}
        # 属性样例（首个非几何字段取值分布·≤8 类时）
        attr_cols = [c for c in g26.columns if c != "geometry"]
        samples = {}
        for c in attr_cols[:4]:
            vc = g26[c].value_counts()
            if len(vc) <= 8:
                samples[c] = dict(vc)
        row["属性样例"] = samples
        rows.append(row)

        # 2025 同名层比对
        p25 = find_2025(name)
        if p25:
            g25 = gpd.read_file(p25)
            # 投影到 4546 做 overlap
            a = g26.to_crs(4546)
            bb = g25.to_crs(4546)
            matched = 0
            new_feats = 0
            for i, geom in enumerate(a.geometry):
                if geom is None or geom.is_empty:
                    continue
                # 与 2025 层做相交面积比
                inter = gpd.GeoSeries([geom], crs=4546).intersection(bb.geometry.union_all())
                ratio = inter.area.iloc[0] / geom.area if geom.area > 0 else 0
                if ratio > 0.5:
                    matched += 1
                else:
                    new_feats += 1
            overlap_report.append({
                "图层": name, "n2026": len(g26), "n2025": len(g25),
                "重叠(交面>50%)": matched, "2026新增(<50%重叠)": new_feats,
                "2025未被覆盖": len(g25) - matched,
            })
        else:
            overlap_report.append({"图层": name, "n2026": len(g26), "n2025": "无同名层", "重叠(交面>50%)": "-", "2026新增(<50%重叠)": "-", "2025未被覆盖": "-"})

df = pd.DataFrame(rows)
print("=== 2026 图层盘点（16 层）===")
for _, r in df.iterrows():
    print(f"\n[{r['维度']}] {r['图层']}")
    print(f"  n={r['n2026']} 几何={r['几何']} CRS={r['CRS']}")
    print(f"  范围 lon {r['lon范围']} lat {r['lat范围']}")
    print(f"  字段: {r['字段']}")
    if r["属性样例"]:
        print(f"  属性: {r['属性样例']}")

print("\n\n=== 2026 vs 2025 同名层重叠比对（判定增量/替换）===")
ov = pd.DataFrame(overlap_report)
print(ov.to_string(index=False))
