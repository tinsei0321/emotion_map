import csv
from collections import Counter

path = r"d:\Github\emotion_map\DATA\raw\simulated_20260613_100k_raw.csv"
with open(path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Strict city tags (remove ambiguous ones)
strict_city = {
    "宜昌", "城建", "规划", "环境", "基础设施", "公共设施", "城市设施", "社区",
    "城市", "城市记忆", "城市生活", "便民", "民生", "民生关注", "民生实事",
    "宜昌环境", "宜昌身边事", "宜昌文化", "宜昌新闻", "宜昌服务", "打卡宜昌",
    "生活服务", "生活便利", "物业服务", "身边事", "新鲜事", "城建动态",
    "文化场馆", "公共空间", "市容环境", "市政设施", "噪音扰民", "河道管理",
    "环境污染", "供水供电", "道路设施", "照明", "公共交通", "道路施工",
    "拆迁安置", "规划公示", "城市建设", "文化设施", "社区服务", "本地新闻",
    "周边环境", "服务", "教育", "文化",
}

# Tags that we previously included but are too ambiguous
ambiguous_tags = {
    "休闲娱乐", "休闲", "娱乐", "书店", "图书馆", "自习室", "培训", "展览", "活动",
}

def strict_city_related(row):
    tags = set(row["tags"].split("|"))
    return bool(tags & strict_city)

def broad_city_related(row):
    tags = set(row["tags"].split("|"))
    return bool(tags & (strict_city | ambiguous_tags))

strict_city_rows = [r for r in rows if strict_city_related(r)]
broad_city_rows = [r for r in rows if broad_city_related(r)]

print("=== Refined Correlation Ratio ===")
print(f"Strict city-related: {len(strict_city_rows)} ({len(strict_city_rows)/len(rows)*100:.1f}%)")
print(f"Broad city-related:  {len(broad_city_rows)} ({len(broad_city_rows)/len(rows)*100:.1f}%)")
print(f"Target: ~10% = ~10,000")
print()

# Check distribution of ambiguous-only (no strict city tag)
ambig_only = [r for r in broad_city_rows if not strict_city_related(r)]
print(f"Ambiguous-only entries: {len(ambig_only)}")
ambig_tags_cnt = Counter()
for r in ambig_only:
    for t in r["tags"].split("|"):
        if t.strip() in ambiguous_tags:
            ambig_tags_cnt[t.strip()] += 1
print("Ambiguous-only tag breakdown:")
for tag, cnt in ambig_tags_cnt.most_common():
    print(f"  {tag}: {cnt}")
print()

# Sample ambiguous-only for review
import random
random.seed(7)
ambig_sample = random.sample(ambig_only, min(10, len(ambig_only)))
print("=== Ambiguous-only samples ===")
for i, r in enumerate(ambig_sample):
    print(f"[A{i+1}] src={r['source']} | tags={r['tags']}")
    print(f"     title: {r['title'][:100] if r['title'] else '(none)'}")
    print(f"     text:  {r['text'][:120]}")
    print()

# Check su12345 issue
su_total = len([r for r in rows if r["source"] == "su12345"])
su_other = len([r for r in rows if r["source"] == "su12345" and "其他" in r["tags"]])
su_city_strict = len([r for r in rows if r["source"] == "su12345" and strict_city_related(r)])
print(f"su12345 total: {su_total}")
print(f"su12345 with '其他' tag: {su_other} ({su_other/su_total*100:.1f}%)")
print(f"su12345 strict city-related: {su_city_strict} ({su_city_strict/su_total*100:.1f}%)")

# Check comments field
print()
print("=== Comments field ===")
empty_comments = sum(1 for r in rows if not r.get("comments", "").strip())
nonempty = sum(1 for r in rows if r.get("comments", "").strip())
print(f"Empty comments: {empty_comments}")
print(f"Non-empty comments: {nonempty}")
# Sample non-empty comments
nonempty_rows = [r for r in rows if r.get("comments", "").strip()]
random.seed(1)
for r in random.sample(nonempty_rows, min(8, len(nonempty_rows))):
    print(f"  comments: {r['comments'][:120]}")
    print(f"  text: {r['text'][:80]}")
    print()
