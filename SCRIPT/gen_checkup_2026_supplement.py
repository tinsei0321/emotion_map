# -*- coding: utf-8 -*-
"""2026 体检补充数据处理管线：
1. 范围验证（全覆盖检验：2026 点落区分布 + 与 2025 西陵伍家范围互斥性）
2. 问题点提取（安全3类/民生5类·沿用 2025 指标字符串与排除规则）
3. 社区聚合（STRtree contains/covers·同 rebuild_minsheng_matrix）
4. 输出：checkup_qty_2026_* 点数据 + 3类/5类矩阵（2026增量 + 全覆盖）+ 全域客观密度

用法：py -X utf8 SCRIPT/gen_checkup_2026_supplement.py
"""
import json
import os
import sys
import io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIS26 = r"D:/OneDrive/2026/15_城市更新专项规划研究/1 宜昌市城市体检/3_gis数据/2026"
PRESETS = os.path.join(ROOT, "DATA", "boundaries", "presets")
Q77 = os.path.join(ROOT, "DATA", "analysis", "77项量化")
OUT_SAFE = os.path.join(ROOT, "DATA", "analysis", "安全韧性")
OUT_LIVE = os.path.join(ROOT, "DATA", "analysis", "民生基础")
OUT_P7 = os.path.join(ROOT, "DATA", "analysis", "page7小结")
DEN = os.path.join(OUT_P7, "社区规模分母_174.csv")

# ── 2026 图层 → 分类映射（沿用 2025 指标字符串）──
BOARD_SAFE = "安全韧性底线"
BOARD_LIVE = "民生基础需求"
# (文件夹, 图层名, 类文件, 指标, board) —— 排除层不进此表
MAPPING = [
    ("住房维度问题", "存在结构安全隐患的住宅", "安全_住房", "存在结构安全隐患的住宅数量（栋）", BOARD_SAFE),
    ("住房维度问题", "存在围护安全隐患的住宅", "安全_住房", "存在围护安全隐患的住宅数量（栋）", BOARD_SAFE),
    ("住房维度问题", "存在楼道安全隐患的住宅", "安全_安全消防", "存在楼道安全隐患的住宅数量（栋）", BOARD_SAFE),
    ("住房维度问题", "存在管线管道破损的住宅", "安全_市政管网", "存在管线管道破损的住宅数量（栋）", BOARD_SAFE),
    ("住房维度问题", "需要进行适老化改造住宅", "民生_住房", "需要进行适老化改造的住宅数量（栋）", BOARD_LIVE),
    ("小区（社区）维度问题", "未达标配建养老服务设施的社区数量", "民生_公服设施", "未达标配建养老服务设施的小区数量（个）", BOARD_LIVE),
    ("小区（社区）维度问题", "未达标配建婴幼儿照护服务设施的社区数量", "民生_公服设施", "未达标配建婴幼儿照护服务设施的小区数量（个）", BOARD_LIVE),
    ("小区（社区）维度问题", "未达标配建公共活动场地的社区数量", "民生_公服设施", "未达标配建公共活动场地的小区数量（个）", BOARD_LIVE),
    ("小区（社区）维度问题", "停车泊位存在较大缺口的小区数", "民生_停车设施", "停车泊位缺口数（个）", BOARD_LIVE),
    ("小区（社区）维度问题", "新能源汽车充电桩缺口数", "民生_停车设施", "新能源汽车充电桩缺口数（个）", BOARD_LIVE),
    ("小区（社区）维度问题", "未配建电动自行车充电设施的小区数", "民生_停车设施", "未配建电动自行车充电设施的小区数量（个）", BOARD_LIVE),
    ("小区（社区）维度问题", "不达标的步行道长度", "民生_交通设施", "不达标的步行道长度（千米）", BOARD_LIVE),
    ("小区（社区）维度问题", "未实施物业管理的小区数量", "民生_物业街面", "未实施物业管理的小区数量（个）", BOARD_LIVE),
]
EXCLUDED = [
    ("住房维度问题", "需要进行数字化改造住宅", "附加发展类（绿色智能）"),
    ("小区（社区）维度问题", "需要进行智慧化改造的小区数量", "附加发展类（智慧化）"),
    ("小区（社区）维度问题", "绿色社区达标率", "率值类·记录为正向达标样本"),
]


def load_gj(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_tree(geojson_path):
    d = load_gj(geojson_path)
    # 优先取"值像名称"的字段（含中文），防误取数字编码列
    key = None
    for f0 in d["features"]:
        for k, v in f0["properties"].items():
            if v and any("一" <= ch <= "鿿" for ch in str(v)):
                key = k
                break
        if key:
            break
    geoms = [shape(f["geometry"]) for f in d["features"]]
    names = [f["properties"].get(key) for f in d["features"]]
    return geoms, names


def main():
    # ── 基础配置 ──
    comm_geoms, comm_names = build_tree(os.path.join(PRESETS, "checkup_配置_社区174.geojson"))
    comm_tree = STRtree(comm_geoms)
    county_geoms, county_names = build_tree(os.path.join(PRESETS, "admin_county_official.geojson"))
    county_tree = STRtree(county_geoms)
    xw_geom = None  # 体检对象（西陵+伍家岗）union
    xw = load_gj(os.path.join(PRESETS, "体检对象_西陵+伍家岗.geojson"))
    from shapely.ops import unary_union
    xw_geom = unary_union([shape(f["geometry"]) for f in xw["features"]])

    def comm_of(pt):
        for gi in comm_tree.query(pt):
            g = comm_geoms[gi]
            if g.contains(pt) or g.covers(pt):
                return comm_names[gi]
        return None

    def county_of(pt):
        for gi in county_tree.query(pt):
            if county_geoms[gi].contains(pt) or county_geoms[gi].covers(pt):
                return county_names[gi]
        return None

    # ── 1. 遍历 2026 图层 → 提取问题点 ──
    print("=" * 70)
    print("一、2026 图层遍历与问题点提取")
    print("=" * 70)
    all_feats = defaultdict(list)   # 类文件 -> [feature]
    layer_stats = []
    county_cnt = defaultdict(int)
    ssjq_mismatch = []
    n_in_xw = 0
    n_unattr = 0
    for dim, layer, clsfile, zb, board in MAPPING:
        p = os.path.join(GIS26, dim, layer + ".shp")
        g = gpd.read_file(p)
        n_hit = 0
        for _, row in g.iterrows():
            pt = Point(row.geometry.x, row.geometry.y)
            c = comm_of(pt)
            if c is None:
                n_unattr += 1
            county = county_of(pt)
            county_cnt[county or "未命中行政区"] += 1
            if xw_geom.contains(pt) or xw_geom.covers(pt) or xw_geom.intersects(pt):
                n_in_xw += 1
            props = {
                "指标": zb, "中类": clsfile.split("_", 1)[1], "board": board,
                "来源": "2026补充", "原图层": layer,
            }
            for src, dst in [("ssjd", "街办_源"), ("sssq", "社区_源"), ("xcmc", "小区_源"), ("xqmc", "小区_源"), ("ldmc", "楼栋_源")]:
                v = row.get(src)
                if isinstance(v, str):
                    v = v.replace("\r", "").replace("\n", "").strip()
                if v:
                    props[dst] = v
            if c:
                props["社区"] = c
                n_hit += 1
                # 交叉核对 sssq vs sjoin
                if "社区_源" in props:
                    a = props["社区_源"].replace("社区", "").strip()
                    b = c.replace("社区", "").strip()
                    if a != b:
                        ssjq_mismatch.append((layer, props["社区_源"], c))
            all_feats[clsfile].append({
                "type": "Feature",
                "properties": props,
                "geometry": {"type": "Point", "coordinates": [row.geometry.x, row.geometry.y]},
            })
        layer_stats.append({"维度": dim, "图层": layer, "点数": len(g), "命中社区": n_hit, "归类": clsfile, "指标": zb})
        print(f"  [OK] {layer}: {len(g)} 点, 命中社区 {n_hit}")

    # 排除层盘点
    print("\n排除层（沿用 2025 排除规则）：")
    for dim, layer, why in EXCLUDED:
        g = gpd.read_file(os.path.join(GIS26, dim, layer + ".shp"))
        print(f"  [SKIP] {layer}: {len(g)} 点 —— {why}")

    df_ls = pd.DataFrame(layer_stats)
    print("\n各层统计：")
    print(df_ls[["图层", "点数", "命中社区", "归类"]].to_string(index=False))

    # ── 2. 范围验证 ──
    print("\n" + "=" * 70)
    print("二、范围验证（全覆盖检验）")
    print("=" * 70)
    print(f"落点行政区分布: {dict(county_cnt)}")
    print(f"2026 点落入 2025 体检对象（西陵+伍家岗）范围: {n_in_xw}")
    print(f"未命中社区面（范围外/落缝）: {n_unattr}")
    if ssjq_mismatch:
        print(f"源属性社区名 vs 空间归属不一致: {len(ssjq_mismatch)} 处")
        for m in ssjq_mismatch[:10]:
            print(f"    {m}")

    # ── 3. 写 checkup_qty_2026 点数据 ──
    print("\n" + "=" * 70)
    print("三、写 checkup_qty_2026 点数据")
    print("=" * 70)
    total_pts = 0
    merged = []
    for clsfile, feats in all_feats.items():
        out = os.path.join(Q77, f"checkup_qty_2026_{clsfile}.geojson")
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False)
        total_pts += len(feats)
        merged.extend(feats)
        zb_cnt = defaultdict(int)
        for x in feats:
            zb_cnt[x["properties"]["指标"]] += 1
        print(f"  {clsfile}: {len(feats)} 点 {dict(zb_cnt)}")
    with open(os.path.join(Q77, "checkup_qty_2026_合并.geojson"), "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": merged}, f, ensure_ascii=False)
    print(f"  合计问题点: {total_pts}")

    # ── 4. 社区聚合 → 矩阵（2026增量 + 全覆盖）──
    print("\n" + "=" * 70)
    print("四、社区聚合矩阵（2026 增量 / 2025+2026 全覆盖）")
    print("=" * 70)
    SAFE_COLS = ["市政管网", "安全消防", "住房"]
    LIVE_COLS = ["公服设施", "住房", "停车设施", "交通设施", "物业街面"]
    # 2026 增量矩阵（按完整类文件键计数·防"住房"跨类同名污染）
    inc26 = defaultdict(lambda: defaultdict(int))
    for clsfile, feats in all_feats.items():
        for x in feats:
            c = x["properties"].get("社区")
            if c:
                inc26[c][clsfile] += 1
    SAFE_COLMAP = {"安全_市政管网": "市政管网", "安全_安全消防": "安全消防", "安全_住房": "住房"}
    LIVE_COLMAP = {"民生_公服设施": "公服设施", "民生_住房": "住房", "民生_停车设施": "停车设施",
                   "民生_交通设施": "交通设施", "民生_物业街面": "物业街面"}

    def matrix_from(counter, cols, tag):
        rows = []
        for c, cls in counter.items():
            tot = sum(cls.values())
            rows.append({"社区": c, **{k: cls.get(k, 0) for k in cols}, "总点数": tot})
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        grand = df["总点数"].sum()
        df["总占比%"] = (df["总点数"] / grand * 100).round(2)
        df["覆盖类数"] = (df[[k for k in cols]] > 0).sum(axis=1)
        df = df.sort_values("总点数", ascending=False).reset_index(drop=True)
        df["排序"] = df.index + 1
        df["严重度"] = df["总占比%"].apply(lambda p: "严重" if p >= 5 else ("较严重" if p >= 3 else "一般"))
        return df

    def matrix_union(old_csv, colmap, out_inc, out_all):
        cols = list(colmap.values())
        old = pd.read_csv(old_csv)
        # 2026 增量计数翻译到列名
        trans = {c: {colmap[k]: v for k, v in cls.items() if k in colmap}
                 for c, cls in inc26.items()}
        trans = {c: cls for c, cls in trans.items() if cls}
        df_inc = matrix_from(trans, cols, "2026")
        df_inc.to_csv(out_inc, index=False, encoding="utf-8-sig")
        # 全覆盖 = 2025 + 2026 增量（按社区名对齐）
        uni = defaultdict(lambda: defaultdict(int))
        for _, r in old.iterrows():
            for k in cols:
                uni[r["社区"]][k] += int(r[k])
        for c, cls in trans.items():
            for k, v in cls.items():
                uni[c][k] += v
        df_all = matrix_from(uni, cols, "全覆盖")
        df_all.to_csv(out_all, index=False, encoding="utf-8-sig")
        return old, df_inc, df_all

    old_s, inc_s, all_s = matrix_union(
        os.path.join(OUT_SAFE, "安全韧性_社区3类矩阵.csv"), SAFE_COLMAP,
        os.path.join(OUT_SAFE, "安全韧性_社区3类矩阵_2026增量.csv"),
        os.path.join(OUT_SAFE, "安全韧性_社区3类矩阵_全覆盖.csv"))
    old_l, inc_l, all_l = matrix_union(
        os.path.join(OUT_LIVE, "民生_社区5类矩阵.csv"), LIVE_COLMAP,
        os.path.join(OUT_LIVE, "民生_社区5类矩阵_2026增量.csv"),
        os.path.join(OUT_LIVE, "民生_社区5类矩阵_全覆盖.csv"))

    for tag, old, inc, allx, cols in [("安全韧性3类", old_s, inc_s, all_s, SAFE_COLS),
                                       ("民生基础5类", old_l, inc_l, all_l, LIVE_COLS)]:
        print(f"\n[{tag}] 2025基线: {len(old)} 社区 {int(old['总点数'].sum())} 点")
        print(f"  2026增量: {len(inc)} 社区 {int(inc['总点数'].sum())} 点, 分类合计 {inc[cols].sum().to_dict() if not inc.empty else {}}")
        print(f"  全覆盖: {len(allx)} 社区 {int(allx['总点数'].sum())} 点, 分类合计 {allx[cols].sum().to_dict()}")

    # ── 5. 覆盖检验（174 社区谁有数据）──
    print("\n" + "=" * 70)
    print("五、174 社区覆盖检验")
    print("=" * 70)
    has25 = set(old_s["社区"]) | set(old_l["社区"])
    has26 = set(inc26.keys())
    allc = set(comm_names)
    both = has25 & has26
    only25 = has25 - has26
    only26 = has26 - has25
    neither = allc - has25 - has26
    print(f"174 社区中: 2025有数据 {len(has25)} · 2026有数据 {len(has26)} · 两者都有 {len(both)}")
    print(f"  仅2025: {len(only25)} · 仅2026: {len(only26)} · 两边都无问题点: {len(neither)}")
    print(f"  全覆盖后有数据社区: {len(has25 | has26)} / {len(allc)}")
    if only26:
        print(f"  仅2026（新区新覆盖）: {sorted(only26)}")
    if neither:
        print(f"  零问题社区（无任何问题点·覆盖缺口或确无问题）: {sorted(neither)}")

    # ── 6. 全域客观密度（参考·page7 扩展口径）──
    print("\n" + "=" * 70)
    print("六、全域客观密度（174 社区·参考口径）")
    print("=" * 70)
    den = pd.read_csv(DEN)
    den["k"] = den["社区"]
    ck25 = defaultdict(int)
    for _, r in old_s.iterrows():
        ck25[r["社区"]] += int(r["总点数"])
    for _, r in old_l.iterrows():
        ck25[r["社区"]] += int(r["总点数"])
    ck26 = defaultdict(int)
    for c, cls in inc26.items():
        ck26[c] += sum(cls.values())
    rows = []
    for _, r in den.iterrows():
        c = r["k"]
        b = r["bldg_n"]
        if pd.isna(b) or b <= 0:
            b = None
        p25, p26 = ck25.get(c, 0), ck26.get(c, 0)
        tot = p25 + p26
        dens = round(tot / b * 100, 1) if b else None
        rows.append({"社区": c, "楼栋数": int(b) if b else None, "体检点_2025": p25, "体检点_2026新增": p26,
                     "体检点_全覆盖": tot, "密度_每百栋_全覆盖": dens, "area_km2": round(r["area_km2"], 3)})
    ddf = pd.DataFrame(rows)
    ddf.to_csv(os.path.join(OUT_P7, "客观密度_全域174_2026补充.csv"), index=False, encoding="utf-8-sig")
    n_pos = ddf[ddf["体检点_全覆盖"] > 0]
    print(f"全域密度表已写: {len(ddf)} 社区, 有问题点 {len(n_pos)}, 密度 top10:")
    print(n_pos.sort_values("密度_每百栋_全覆盖", ascending=False).head(10).to_string(index=False))

    # ── 7. 指标级汇总（2025 / 2026新增 / 全覆盖合计）──
    print("\n" + "=" * 70)
    print("七、指标级汇总（页数据包用）")
    print("=" * 70)
    zb25 = defaultdict(int)
    for fn in ["checkup_qty_安全_住房", "checkup_qty_安全_安全消防", "checkup_qty_安全_市政管网",
               "checkup_qty_民生_住房", "checkup_qty_民生_公服设施_问题类", "checkup_qty_民生_停车设施",
               "checkup_qty_民生_交通设施", "checkup_qty_民生_物业街面"]:
        d = load_gj(os.path.join(Q77, fn + ".geojson"))
        for x in d["features"]:
            zb25[x["properties"]["指标"]] += 1
    zb26 = defaultdict(int)
    for x in merged:
        zb26[x["properties"]["指标"]] += 1
    zb_order = [
        "存在结构安全隐患的住宅数量（栋）", "存在围护安全隐患的住宅数量（栋）",
        "存在楼道安全隐患的住宅数量（栋）", "存在燃气安全隐患的住宅数量（栋）",
        "存在管线管道破损的住宅数量（栋）",
        "需要进行适老化改造的住宅数量（栋）", "非成套住宅数量（套）",
        "未达标配建养老服务设施的小区数量（个）", "未达标配建婴幼儿照护服务设施的小区数量（个）",
        "未达标配建幼儿园的小区数量（个）", "未达标配建公共活动场地的小区数量（个）",
        "未达标配建的多功能运动场地数量（个）", "小学学位缺口数（个）",
        "停车泊位缺口数（个）", "新能源汽车充电桩缺口数（个）", "未配建电动自行车充电设施的小区数量（个）",
        "不达标的步行道长度（千米）", "未实施物业管理的小区数量（个）", "存在乱停乱放车辆问题的道路数量（条）",
    ]
    print(f"{'指标':<40} {'2025':>6} {'2026新增':>8} {'全覆盖':>7}")
    for zb in zb_order:
        a, b = zb25.get(zb, 0), zb26.get(zb, 0)
        print(f"{zb:<40} {a:>6} {b:>8} {a + b:>7}")
    print(f"{'合计':<40} {sum(zb25.values()):>6} {sum(zb26.values()):>8} {sum(zb25.values()) + sum(zb26.values()):>7}")


if __name__ == "__main__":
    main()
