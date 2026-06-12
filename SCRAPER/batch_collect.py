"""
批量数据采集脚本 — 无需登录，基于探索页 SSR
==========================================
1. 多轮刷新探索页累积笔记 ID
2. 逐个抓取笔记详情页获取完整正文
3. 输出 CSV 到 data/raw/
"""
import requests, re, json, csv, os, time, random
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def safe_print(*args):
    try:
        print(*args)
    except UnicodeEncodeError:
        print(*(str(a).encode('ascii', errors='replace').decode('ascii') for a in args))

def extract_initial_state(html):
    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
    if match:
        raw = match.group(1)
        raw = re.sub(r':\s*undefined', ': null', raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return None

def parse_count(value):
    if not value:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    value = str(value).strip()
    if not value:
        return 0
    if '万' in value:
        try:
            return int(float(value.replace('万', '')) * 10000)
        except ValueError:
            return 0
    try:
        return int(value.replace(',', ''))
    except ValueError:
        return 0

# ── Phase 1: 多轮采集笔记 ──
safe_print("[Phase 1] Collecting note IDs from explore page...")
seen_ids = set()
notes = []

for round_num in range(8):
    try:
        resp = requests.get("https://www.xiaohongshu.com/explore", headers=HEADERS, timeout=15)
        data = extract_initial_state(resp.text)
        if not data:
            continue
        
        feeds = data.get('feed', {}).get('feeds', [])
        new_count = 0
        for feed in feeds:
            note_id = feed.get('id', '')
            if note_id in seen_ids:
                continue
            seen_ids.add(note_id)
            
            nc = feed.get('noteCard', {})
            interact = nc.get('interactInfo', {})
            notes.append({
                'id': note_id,
                'title': nc.get('displayTitle', ''),
                'desc': nc.get('desc', ''),
                'likes': parse_count(interact.get('likedCount', '')),
                'comments': parse_count(interact.get('commentCount', '')),
                'type': nc.get('type', ''),
                'tags': [t.get('name', '') for t in nc.get('tagList', []) if isinstance(t, dict)],
            })
            new_count += 1
        
        safe_print(f"  Round {round_num+1}: +{new_count} new (total: {len(notes)})")
        time.sleep(random.uniform(1.5, 3))
    except Exception as e:
        safe_print(f"  Round {round_num+1} error: {e}")

safe_print(f"\n[OK] Phase 1 done: {len(notes)} unique notes collected")

# ── Phase 2: 笔记详情页采集 ──
safe_print("\n[Phase 2] Fetching note detail pages...")
detail_count = 0
for i, note in enumerate(notes):
    if note['desc'] and len(note['desc']) >= 20:
        detail_count += 1
        continue  # 已有足够正文，跳过
    
    detail_url = f"https://www.xiaohongshu.com/explore/{note['id']}"
    try:
        resp = requests.get(detail_url, headers=HEADERS, timeout=10)
        data = extract_initial_state(resp.text)
        if data:
            note_data = data.get('note', {})
            note_detail_map = note_data.get('noteDetailMap', {})
            note_detail = note_detail_map.get(note['id'], {})
            if note_detail:
                note_info = note_detail.get('note', {})
                desc = note_info.get('desc', '')
                if desc:
                    note['desc'] = desc
                    detail_count += 1
        
        if (i+1) % 20 == 0:
            safe_print(f"  Progress: {i+1}/{len(notes)}, details: {detail_count}")
        time.sleep(random.uniform(0.3, 1))
    except Exception as e:
        pass

safe_print(f"[OK] Phase 2 done: {detail_count}/{len(notes)} notes have descriptions")

# ── Phase 3: 写出 CSV ──
today = datetime.now().strftime('%Y%m%d')
output_file = os.path.join(OUTPUT_DIR, f'xiaohongshu_{today}_bulk_raw.csv')

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['source', 'url', 'title', 'text', 'tags', 'like_count', 'comment_count', 'area', 'crawl_time'])
    writer.writeheader()
    for note in notes:
        text = note['desc'] if note['desc'] and len(note['desc']) >= 5 else note['title']
        writer.writerow({
            'source': 'xiaohongshu',
            'url': f"https://www.xiaohongshu.com/explore/{note['id']}",
            'title': note['title'],
            'text': text,
            'tags': '|'.join(note['tags']) if note['tags'] else '',
            'like_count': note['likes'],
            'comment_count': note['comments'],
            'area': '通用',
            'crawl_time': datetime.now().isoformat(),
        })

safe_print(f"\n[DONE] Output: {output_file}")
safe_print(f"       {len(notes)} rows written")
