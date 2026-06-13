import csv
from collections import Counter

path = r"d:\Github\emotion_map\DATA\raw\simulated_20260613_100k_raw.csv"
with open(path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Check "xiuxian yule" content
print("=== Entries tagged '休闲娱乐' samples ===")
xr = [r for r in rows if "休闲娱乐" in r["tags"]]
print(f"Total: {len(xr)}")
import random
random.seed(99)
for r in random.sample(xr, min(15, len(xr))):
    print(f"  src={r['source']} | tags={r['tags']}")
    print(f"  title: {r['title'][:100] if r['title'] else '(none)'}")
    print(f"  text:  {r['text'][:120]}")
    print()

# Check "书店" and "图书馆" tagged entries
print("=== Entries tagged '书店' or '图书馆' samples ===")
book_rows = [r for r in rows if "书店" in r["tags"] or "图书馆" in r["tags"]]
print(f"Total: {len(book_rows)}")
random.seed(42)
for r in random.sample(book_rows, min(15, len(book_rows))):
    print(f"  src={r['source']} | tags={r['tags']}")
    print(f"  title: {r['title'][:100] if r['title'] else '(none)'}")
    print(f"  text:  {r['text'][:120]}")
    print()

# Check su12345 "其他" more carefully
print("=== su12345 with '其他' tag: all unique texts ===")
su_other = [r for r in rows if r["source"] == "su12345" and "其他" in r["tags"]]
# Get text patterns
texts = Counter(r["text"] for r in su_other)
print(f"Unique texts: {len(texts)}")
for text, cnt in texts.most_common(20):
    print(f"  [{cnt}x] {text[:100]}")
