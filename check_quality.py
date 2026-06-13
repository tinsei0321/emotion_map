import csv
from collections import Counter

path = r"d:\Github\emotion_map\DATA\raw\simulated_20260613_100k_raw.csv"
with open(path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

tag_counter = Counter()
for r in rows:
    if r["tags"]:
        for t in r["tags"].split("|"):
            tag_counter[t.strip()] += 1

print("=== ALL tags (51 onward) ===")
for i, (tag, cnt) in enumerate(tag_counter.most_common()):
    if i >= 50:
        print(f"  {i+1:3d}. {tag}: {cnt}")

print()
print("=== Yichang tagged entries ===")
yichang_rows = [r for r in rows if "宜昌" in r["tags"]]
print(f"Count: {len(yichang_rows)}")
for r in yichang_rows[:5]:
    print(f"  src={r['source']} | tags={r['tags']}")
    print(f"  title: {r['title'][:80]}")
    print(f"  text: {r['text'][:100]}")
    print()

print("=== su12345 entries sample ===")
su_rows = [r for r in rows if r["source"] == "su12345"]
for r in su_rows[:8]:
    print(f"  tags={r['tags']}")
    print(f"  title: {r['title'][:80]}")
    print(f"  text: {r['text'][:100]}")
    print()

print("=== meituan entries sample ===")
mt_rows = [r for r in rows if r["source"] == "meituan"]
for r in mt_rows[:8]:
    print(f"  tags={r['tags']}")
    print(f"  title: {r['title'][:80]}")
    print(f"  text: {r['text'][:100]}")
    print()
