import csv
from collections import Counter

path = r"d:\Github\emotion_map\DATA\raw\simulated_20260613_100k_raw.csv"
with open(path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# === City-related tags ===
city_tags = {
    "宜昌", "城建", "规划", "环境", "基础设施", "公共设施", "城市设施", "社区",
    "城市", "城市记忆", "城市生活", "便民", "民生", "民生关注", "民生实事",
    "宜昌环境", "宜昌身边事", "宜昌文化", "宜昌新闻", "宜昌服务", "打卡宜昌",
    "生活服务", "生活便利", "物业服务", "身边事", "新鲜事", "城建动态",
    "文化场馆", "公共空间", "市容环境", "市政设施", "噪音扰民", "河道管理",
    "环境污染", "供水供电", "道路设施", "照明", "公共交通", "道路施工",
    "拆迁安置", "规划公示", "城市建设", "图书馆", "文化", "文化设施",
    "书店", "展览", "活动", "社区服务", "本地新闻", "周边环境", "服务",
    "休闲娱乐", "休闲", "娱乐", "教育", "培训",
}

def is_city_related(row):
    tags = set(row["tags"].split("|"))
    return bool(tags & city_tags)

city_rows = [r for r in rows if is_city_related(r)]
irrel_rows = [r for r in rows if not is_city_related(r)]

print("=== Correlation Ratio ===")
print(f"City-related: {len(city_rows)} ({len(city_rows)/len(rows)*100:.1f}%)")
print(f"Irrelevant:   {len(irrel_rows)} ({len(irrel_rows)/len(rows)*100:.1f}%)")
print(f"Target: ~10% city-related = ~10,000")

print()
print("=== City-related by source ===")
city_src = Counter(r["source"] for r in city_rows)
for src, cnt in city_src.most_common():
    print(f"  {src}: {cnt} ({cnt/len(city_rows)*100:.1f}%)")

print()
print("=== Irrelevant by source ===")
irrel_src = Counter(r["source"] for r in irrel_rows)
for src, cnt in irrel_src.most_common():
    print(f"  {src}: {cnt} ({cnt/len(irrel_rows)*100:.1f}%)")

print()
print("=== City-related tag distribution ===")
city_tag_cnt = Counter()
for r in city_rows:
    for t in r["tags"].split("|"):
        if t.strip() in city_tags:
            city_tag_cnt[t.strip()] += 1
for tag, cnt in city_tag_cnt.most_common(20):
    print(f"  {tag}: {cnt}")

print()
print("=== Irrelevant tag distribution (top 20) ===")
irrel_tag_cnt = Counter()
for r in irrel_rows:
    for t in r["tags"].split("|"):
        irrel_tag_cnt[t.strip()] += 1
for tag, cnt in irrel_tag_cnt.most_common(20):
    print(f"  {tag}: {cnt}")

# === Content Sampling ===
import random
random.seed(123)

print()
print("=" * 60)
print("=== CONTENT SAMPLING: 10 CITY-RELATED ===")
print("=" * 60)
city_sample = random.sample(city_rows, min(10, len(city_rows)))
for i, r in enumerate(city_sample):
    print(f"[C{i+1}] src={r['source']} | tags={r['tags']}")
    print(f"     title: {r['title'][:100] if r['title'] else '(no title)'}")
    print(f"     text:  {r['text'][:150]}")
    print()

print()
print("=" * 60)
print("=== CONTENT SAMPLING: 10 IRRELEVANT ===")
print("=" * 60)
irrel_sample = random.sample(irrel_rows, min(10, len(irrel_rows)))
for i, r in enumerate(irrel_sample):
    print(f"[I{i+1}] src={r['source']} | tags={r['tags']}")
    print(f"     title: {r['title'][:100] if r['title'] else '(no title)'}")
    print(f"     text:  {r['text'][:150]}")
    print()

print()
print("=" * 60)
print("=== SPECIAL CHECK: su12345 with 'other' tag ===")
print("=" * 60)
su_other = [r for r in rows if r["source"] == "su12345" and "其他" in r["tags"]]
print(f"su12345 entries tagged 'other': {len(su_other)} / {len([r for r in rows if r['source']=='su12345'])} total su12345")
print("Samples:")
for r in su_other[:5]:
    print(f"  title: {r['title'][:80]}")
    print(f"  text:  {r['text'][:100]}")
    print(f"  tags:  {r['tags']}")
    print()
