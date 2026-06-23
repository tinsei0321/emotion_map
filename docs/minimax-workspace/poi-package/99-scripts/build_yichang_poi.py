# -*- coding: utf-8 -*-
"""
宜昌 POI 多格式输出生成器（修正版）
==================================

从 WGS84 经纬度"真理之源"出发，用 pyproj 精确转换到：
- EPSG:4546 (CGCS2000 / 3°GK zone 37 / CM 111°E) 米级
- WGS84 (EPSG:4326) 地理坐标

输出：
- yichang-poi-wgs84.csv        (WGS84 CSV, 主流地图库可读)
- yichang-poi-wgs84.geojson    (WGS84 GeoJSON, Leaflet/Mapbox 可直接读)
- yichang-poi-epsg4546.geojson (EPSG:4546 GeoJSON, 自定义 CRS demo 用)
- yichang-poi-seed-rich.json   (通用 seed, 含两种坐标)

注：之前的 EPSG:4547 是错的（CM 114°E），正确的是 EPSG:4546 (CM 111°E)
"""

import json
import csv
import os
import sys
import warnings
warnings.filterwarnings("ignore")

# 导入 WGS84 经纬度真值表
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yichang_poi_lnglat import YICHANG_POIS_LNGLAT

from pyproj import Transformer

# ============================================================================
# 1. 转换器
# ============================================================================

# WGS84 -> EPSG:4546 (CM 111E)
# CGCS2000 与 WGS84 椭球几乎一样（差异 < 1cm），可直接转换
# 注意：EPSG:4546 是 CM 111°E（不是 EPSG:4547，4547 是 CM 114°E）
T_WGS84_TO_4546 = Transformer.from_crs("EPSG:4326", "EPSG:4546", always_xy=True)


def to_epsg4546(lng, lat):
    """WGS84 -> EPSG:4546 米级，返回 (y_东向, x_北向)"""
    x, y = T_WGS84_TO_4546.transform(lng, lat)
    # x = 东向, y = 北向
    return x, y


# ============================================================================
# 2. 转换 + 输出
# ============================================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(base_dir), "data")
    os.makedirs(data_dir, exist_ok=True)

    print("=" * 60)
    print("宜昌 POI 多格式输出生成器（修正版）")
    print("=" * 60)
    print(f"源数据: WGS84 经纬度 ({len(YICHANG_POIS_LNGLAT)} 条 POI)")
    print(f"目标坐标系: EPSG:4546 (CGCS2000 / 3°GK zone 37 / CM 111°E)")
    print()

    # 转换所有 POI
    converted = []
    for i, p in enumerate(YICHANG_POIS_LNGLAT):
        y_east, x_north = to_epsg4546(p["lng"], p["lat"])
        converted.append({
            "id": f"yc_poi_{i:03d}",
            "name": p["name"],
            "baidu_level1": p["level1"],
            "baidu_level2": p["level2"],
            # WGS84
            "lng": p["lng"],
            "lat": p["lat"],
            # EPSG:4546 米级
            "y_east_m": y_east,
            "x_north_m": x_north,
            # 其他字段
            "weight": p["weight"],
            "domain": p["domain"],
            "element": p["element"],
            "area": p["area"],
            "address_hint": p["address_hint"],
            "radius_m": p.get("radius_m", 300),
        })

    # ---------- 1. WGS84 CSV ----------
    csv_path = os.path.join(data_dir, "yichang-poi-wgs84.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "id", "name", "lng", "lat",
            "baidu_level1", "baidu_level2", "area",
            "domain", "element", "weight", "radius_m",
            "address_hint",
            "x_epsg4546_north_m", "y_epsg4546_east_m"
        ])
        for c in converted:
            w.writerow([
                c["id"], c["name"],
                round(c["lng"], 6), round(c["lat"], 6),
                c["baidu_level1"], c["baidu_level2"], c["area"],
                c["domain"], c["element"], c["weight"], c["radius_m"],
                c["address_hint"],
                round(c["x_north_m"], 2), round(c["y_east_m"], 2),
            ])
    print(f"✓ WGS84 CSV: {csv_path}")

    # ---------- 2. WGS84 GeoJSON ----------
    wgs84_geo_path = os.path.join(data_dir, "yichang-poi-wgs84.geojson")
    features = []
    for c in converted:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(c["lng"], 6), round(c["lat"], 6)]
            },
            "properties": {
                "id": c["id"],
                "name": c["name"],
                "baidu_level1": c["baidu_level1"],
                "baidu_level2": c["baidu_level2"],
                "area": c["area"],
                "domain": c["domain"],
                "element": c["element"],
                "weight": c["weight"],
                "radius_m": c["radius_m"],
                "address_hint": c["address_hint"],
                "xy_epsg4546_m": {
                    "x_north_m": round(c["x_north_m"], 2),
                    "y_east_m": round(c["y_east_m"], 2),
                }
            }
        })
    fc = {
        "type": "FeatureCollection",
        "name": "yichang-poi-wgs84",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "metadata": {
            "description": "宜昌核心主城精选 POI（WGS84 地理坐标，主流地图库可读）",
            "source_crs": "EPSG:4326 (WGS84)",
            "target_crs": "EPSG:4326 (WGS84)",
            "poi_count": len(features),
            "schema_version": "2.0",
            "fix_note": "EPSG 编号从 4547 修正为 4546 (CM 111E)",
        },
        "features": features,
    }
    with open(wgs84_geo_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)
    print(f"✓ WGS84 GeoJSON: {wgs84_geo_path}")

    # ---------- 3. EPSG:4546 GeoJSON ----------
    epsg_geo_path = os.path.join(data_dir, "yichang-poi-epsg4546.geojson")
    features_epsg = []
    for c in converted:
        features_epsg.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                # GeoJSON: [东向, 北向] = [Y, X]
                "coordinates": [round(c["y_east_m"], 2), round(c["x_north_m"], 2)]
            },
            "properties": {
                "id": c["id"],
                "name": c["name"],
                "baidu_level1": c["baidu_level1"],
                "baidu_level2": c["baidu_level2"],
                "area": c["area"],
                "domain": c["domain"],
                "element": c["element"],
                "weight": c["weight"],
                "radius_m": c["radius_m"],
                "address_hint": c["address_hint"],
            }
        })
    fc_epsg = {
        "type": "FeatureCollection",
        "name": "yichang-poi-epsg4546",
        "crs": {"type": "name", "properties": {"name": "EPSG:4546"}},
        "metadata": {
            "description": "宜昌核心主城精选 POI（EPSG:4546 米级，自定义 CRS demo 用）",
            "coordinate_system": "EPSG:4546 (CGCS2000 / 3°GK zone 37 / CM 111°E)",
            "unit": "meter",
            "poi_count": len(features_epsg),
            "schema_version": "2.0",
            "fix_note": "EPSG 编号从 4547 修正为 4546 (CM 111E)",
        },
        "features": features_epsg,
    }
    with open(epsg_geo_path, "w", encoding="utf-8") as f:
        json.dump(fc_epsg, f, ensure_ascii=False, indent=2)
    print(f"✓ EPSG:4546 GeoJSON: {epsg_geo_path}")

    # ---------- 4. Rich Seed JSON（既有 WGS84 又有 EPSG:4546） ----------
    seed_path = os.path.join(data_dir, "yichang-poi-seed-rich.json")
    seed = {
        "metadata": {
            "description": "宜昌核心主城精选 POI（双坐标系）",
            "coordinate_system_wgs84": "EPSG:4326 (lng/lat 度)",
            "coordinate_system_epsg4546": "EPSG:4546 (X=北向_米, Y=东向_米)",
            "poi_count": len(converted),
            "schema_version": "2.0",
            "fix_note": "EPSG 编号从 4547 修正为 4546 (CM 111E)",
        },
        "pois": [
            {
                "id": c["id"],
                "name": c["name"],
                "baidu_level1": c["baidu_level1"],
                "baidu_level2": c["baidu_level2"],
                # WGS84
                "lng": round(c["lng"], 6),
                "lat": round(c["lat"], 6),
                # EPSG:4546
                "xy_x_m": round(c["x_north_m"], 2),  # 北向
                "xy_y_m": round(c["y_east_m"], 2),   # 东向
                "weight": c["weight"],
                "domain": c["domain"],
                "element": c["element"],
                "area": c["area"],
                "address_hint": c["address_hint"],
                "radius_m": c["radius_m"],
            }
            for c in converted
        ]
    }
    with open(seed_path, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
    print(f"✓ Rich Seed JSON: {seed_path}")

    # ============================================================================
    # 3. 抽样验证
    # ============================================================================
    print()
    print("=" * 60)
    print("抽样验证（关键 POI）")
    print("=" * 60)
    test_names = ["解放路步行街", "CBD 万达广场", "大南门", "二马路（主街）", "宜昌东站", "三峡机场"]
    for n in test_names:
        for c in converted:
            if c["name"] == n:
                print(f"\n{c['name']} ({c['id']}):")
                print(f"  WGS84:    lng={c['lng']:.6f}°, lat={c['lat']:.6f}°")
                print(f"  EPSG:4546: Y(东向)={c['y_east_m']:.0f}m, X(北向)={c['x_north_m']:.0f}m")
                break

    # ============================================================================
    # 4. 坐标范围检查
    # ============================================================================
    print()
    print("=" * 60)
    print("坐标范围检查")
    print("=" * 60)
    lngs = [c["lng"] for c in converted]
    lats = [c["lat"] for c in converted]
    ys = [c["y_east_m"] for c in converted]
    xs = [c["x_north_m"] for c in converted]
    print(f"WGS84 经度:  {min(lngs):.4f} ~ {max(lngs):.4f}°E")
    print(f"WGS84 纬度:  {min(lats):.4f} ~ {max(lats):.4f}°N")
    print(f"EPSG:4546 Y(东向): {min(ys):.0f} ~ {max(ys):.0f}m")
    print(f"EPSG:4546 X(北向): {min(xs):.0f} ~ {max(xs):.0f}m")
    print()
    print("✅ 完成！")


if __name__ == "__main__":
    main()
