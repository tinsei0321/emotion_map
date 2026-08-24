import json
import os

src = r"C:\Users\ADMINI~1\AppData\Local\Temp\dsh-spill-jAFUm3\session-ac034401789d\863605d9c489-mcp__emc__rank.txt"
dst = r"D:\Github\emotion_map\DATA\analysis\12345_top5_communities.geojson"

with open(src, encoding="utf-8") as f:
    data = json.load(f)

geojson = data["geojson"]

os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False)

print("[OK] wrote", dst)
print("[OK] features:", len(geojson.get("features", [])))
for feat in geojson.get("features", []):
    p = feat.get("properties", {})
    print("[OK]  ", p.get("name"), "| point_count=", p.get("point_count"), "| polarity_index=", p.get("polarity_index"))
