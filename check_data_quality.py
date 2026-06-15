"""
数据质量分析脚本 — DATA/processed/ 管道产出文件
================================================
分析 L1 CSV / L2 CSV / L2 GeoJSON 的数据质量，
核心关注：无 API Key 运行时，关键词层过滤后的 L2 数据中误判率。
"""
import os
import sys
import json
import csv
import builtins as _bi

import pandas as pd
import numpy as np

_real_print = _bi.print

def _safe_print(*args, **kwargs):
    try:
        _real_print(*args, **kwargs)
    except UnicodeEncodeError:
        _real_print(*(str(a).encode('ascii', errors='replace').decode('ascii') for a in args), **kwargs)

# Fix Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DATA', 'processed')

L1_FILE = os.path.join(DATA_DIR, 'simulated_l1_2000_规划范围_L1_result_csv.csv')
L2_FILE = os.path.join(DATA_DIR, 'simulated_l1_2000_规划范围_V2_L2_result_csv.csv')
GEOJSON_FILE = os.path.join(DATA_DIR, 'simulated_l1_2000_规划范围_V2_L2_result_geojson.geojson')

# ═══════════════════════════════════════════════════════════
# 辅助：人工抽检判断
# ═══════════════════════════════════════════════════════════

def manual_judge_relevance(text):
    """
    模拟人工判断一条文本是否真的与城市感受/需求相关。
    基于相关性筛选设计中的五要素判断原则。
    返回: (is_relevant: bool, reason: str)
    """
    if not isinstance(text, str) or not text.strip():
        return False, "空文本"

    t = text.strip()

    # ── 明显无关：纯个人情感、美妆、游戏、广告 ──
    pure_irrelevant_patterns = [
        # 纯情感/个人
        ('晚安', '纯个人问候'),
        ('早安', '纯个人问候'),
        ('追剧', '纯个人娱乐'),
        ('追剧中', '纯个人娱乐'),
        ('不知道发给谁', '纯个人情感倾诉 - 无地点信息'),
        ('想说的话但不知道', '纯个人情感倾诉 - 无地点信息'),
        ('有些话想说', '纯个人情感倾诉 - 无地点信息'),
        ('初恋离开', '纯个人情感'),
        ('难过', '纯个人情感'),
        ('心情不好', '纯个人情感'),
        # 美妆/护肤
        ('粉底液', '美妆护肤 - 无关城市'),
        ('精华液', '美妆护肤 - 无关城市'),
        ('精华', '美妆护肤 - 无关城市'),
        ('隔离霜', '美妆护肤 - 无关城市'),
        ('眉笔', '美妆护肤 - 无关城市'),
        ('眼线笔', '美妆护肤 - 无关城市'),
        ('油皮', '美妆护肤 - 无关城市'),
        ('痘痘肌', '美妆护肤 - 无关城市'),
        ('洗面奶', '美妆护肤 - 无关城市'),
        # 广告
        ('厂家直销', '纯广告'),
        ('理财课程', '纯广告'),
        ('价格低到你不敢信', '纯广告'),
        # 游戏
        ('游戏日常打卡', '游戏 - 无关城市'),
        ('上分', '游戏 - 无关城市'),
        ('排位', '游戏 - 无关城市'),
        # 纯健身
        ('撸铁', '纯健身 - 无城市信息'),
        ('减脂', '纯健身 - 无城市信息'),
        ('增肌', '纯健身 - 无城市信息'),
    ]

    for pattern, reason in pure_irrelevant_patterns:
        if pattern in t:
            return False, reason

    # ── 明显相关：涉及城市设施/环境/服务/文化/事件 ──
    relevant_indicators = [
        # 设施
        ('快递柜', '设施 - 基础设施建议'),
        ('停车', '设施 - 停车问题'),
        ('公园', '设施 - 公园绿地'),
        ('幼儿园', '设施 - 教育设施'),
        ('学校', '设施 - 教育设施'),
        ('医院', '设施 - 医疗设施'),
        ('商场', '设施 - 商业配套'),
        ('超市', '设施 - 商业配套'),
        ('公交', '设施 - 交通'),
        ('地铁', '设施 - 交通'),
        ('公共设施', '设施 - 公共设施'),
        # 环境
        ('垃圾', '环境 - 卫生问题'),
        ('河道', '环境 - 水系'),
        ('河水', '环境 - 水系'),
        ('发臭', '环境 - 环境质量'),
        ('噪音', '环境 - 噪音'),
        ('绿化', '环境 - 绿化'),
        ('空气', '环境 - 空气质量'),
        # 服务
        ('物业', '服务 - 物业管理'),
        ('环卫', '服务 - 环卫'),
        ('投诉', '服务 - 投诉'),
        ('12345', '服务 - 政务投诉'),
        # 文化
        ('非遗', '文化 - 非遗活动'),
        ('历史', '文化 - 历史街区'),
        ('文创', '文化 - 文创'),
        ('打卡', '文化/体验 - 城市打卡'),
        ('葛洲坝', '文化/地点 - 宜昌地标'),
        ('滨江', '地点 - 城市地标'),
        ('东山', '地点 - 城市地标'),
        # 事件
        ('拆迁', '事件 - 拆迁'),
        ('施工', '事件 - 施工'),
        ('活动', '事件 - 城市活动'),
        # 地点明确
        ('路', '地点 - 具体道路'),
        ('街', '地点 - 具体街道'),
        ('巷', '地点 - 具体位置'),
        ('社区', '地点 - 社区'),
        ('小区', '地点 - 小区'),
        ('万达', '地点 - 商业地标'),
        ('CBD', '地点 - 商业地标'),
        ('水悦城', '地点 - 商业地标'),
        ('三峡大学', '地点 - 教育地标'),
        # 市民体验
        ('散步', '体验 - 城市散步'),
        ('遛弯', '体验 - 城市步行'),
        ('周末去哪玩', '体验 - 城市休闲'),
        ('周末去', '体验 - 城市出行'),
        ('逛街', '体验 - 城市消费'),
        ('逛', '体验 - 城市体验'),
        ('推荐', '体验 - 城市推荐'),
    ]

    for indicator, reason in relevant_indicators:
        if indicator in t:
            return True, reason

    # ── 不确定 → 倾向于保留（宽容原则） ──
    # 任何提及具体地点/场所的文本 → 保留
    place_words = ['店', '馆', '院', '所', '中心', '广场', '大厦', '城', '区', '门口']
    for w in place_words:
        if w in t:
            return True, f"包含地点词'{w}' → 保留"

    return False, "无明确城市信号 → 倾向判定为无关"


# ═══════════════════════════════════════════════════════════
# 1. L1 CSV 分析
# ═══════════════════════════════════════════════════════════

_safe_print("=" * 70)
_safe_print(f"═══ L1 CSV 分析: {os.path.basename(L1_FILE)} ═══")
_safe_print("=" * 70)

df_l1 = pd.read_csv(L1_FILE, encoding='utf-8-sig')
_safe_print(f"\n[1] 总行数: {len(df_l1)}")
_safe_print(f"[2] 总列数: {len(df_l1.columns)}")
_safe_print(f"[3] 列名: {list(df_l1.columns)}")

# relevance 分布
_safe_print(f"\n─── relevance 分布 ───")
rel_counts = df_l1['relevance'].value_counts()
_safe_print(rel_counts.to_string())
_safe_print(f"  relevance='relevant' 比例: {rel_counts.get('relevant', 0) / len(df_l1) * 100:.1f}%")

# relevance_category 分布
_safe_print(f"\n─── relevance_category 分布 ───")
if 'relevance_category' in df_l1.columns:
    rc_counts = df_l1['relevance_category'].value_counts()
    _safe_print(rc_counts.to_string())
else:
    _safe_print("  (列不存在)")

# primary_emotion 分布
_safe_print(f"\n─── primary_emotion 分布 ───")
if 'primary_emotion' in df_l1.columns:
    pe_counts = df_l1['primary_emotion'].value_counts()
    _safe_print(pe_counts.to_string())

# emotion_intensity 分布
_safe_print(f"\n─── emotion_intensity 分布 ───")
if 'emotion_intensity' in df_l1.columns:
    ei_counts = df_l1['emotion_intensity'].value_counts().sort_index()
    _safe_print(ei_counts.to_string())
    _safe_print(f"  平均强度: {df_l1['emotion_intensity'].mean():.2f}")

# urban_value 分布
_safe_print(f"\n─── urban_value 分布 ───")
if 'urban_value' in df_l1.columns:
    uv_counts = df_l1['urban_value'].value_counts()
    _safe_print(uv_counts.to_string())

# l1_confidence 统计
_safe_print(f"\n─── l1_confidence 统计 ───")
if 'l1_confidence' in df_l1.columns:
    c = df_l1['l1_confidence']
    _safe_print(f"  mean={c.mean():.3f} median={c.median():.3f} min={c.min():.3f} max={c.max():.3f}")

# has_location 分布
_safe_print(f"\n─── has_location 分布 ───")
if 'has_location' in df_l1.columns:
    hl_counts = df_l1['has_location'].value_counts()
    _safe_print(hl_counts.to_string())

# source 分布
_safe_print(f"\n─── source 分布 ───")
src_counts = df_l1['source'].value_counts()
_safe_print(src_counts.to_string())

# 管道数据流
_safe_print(f"\n─── 管道数据流 ───")
_safe_print(f"  L1 总入池:           {len(df_l1)}")
if 'relevance' in df_l1.columns:
    relevant = df_l1[df_l1['relevance'] == 'relevant']
    _safe_print(f"  relevant:             {len(relevant)} ({len(relevant)/len(df_l1)*100:.1f}%)")
if 'has_location' in df_l1.columns:
    with_location = df_l1[df_l1['has_location'] == True]
    _safe_print(f"  has_location=True:    {len(with_location)} ({len(with_location)/len(df_l1)*100:.1f}%)")
if 'urban_value' in df_l1.columns:
    high_value = df_l1[df_l1['urban_value'] == 'high']
    _safe_print(f"  urban_value=high:     {len(high_value)} ({len(high_value)/len(df_l1)*100:.1f}%)")

# ═══════════════════════════════════════════════════════════
# 2. L2 CSV 分析
# ═══════════════════════════════════════════════════════════

_safe_print("\n\n")
_safe_print("=" * 70)
_safe_print("═══ L2 CSV 分析: simulated_20260613_规划范围_L2_result_csv.csv ═══")
_safe_print("=" * 70)

df_l2 = pd.read_csv(L2_FILE, encoding='utf-8-sig')
_safe_print(f"\n[1] 总行数: {len(df_l2)}")

# polarity 分布
_safe_print(f"\n─── polarity 五级分布 ───")
pol_counts = df_l2['polarity'].value_counts()
_safe_print(pol_counts.to_string())
for pol in ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']:
    cnt = pol_counts.get(pol, 0)
    pct = cnt / len(df_l2) * 100
    bar = '█' * int(pct / 2)
    _safe_print(f"  {pol:>15}: {cnt:>6} ({pct:5.1f}%) {bar}")

# score 统计
_safe_print(f"\n─── score 统计 ───")
scores = df_l2['score'].dropna()
_safe_print(f"  mean:   {scores.mean():.4f}")
_safe_print(f"  median: {scores.median():.4f}")
_safe_print(f"  std:    {scores.std():.4f}")
_safe_print(f"  min:    {scores.min():.4f}")
_safe_print(f"  max:    {scores.max():.4f}")
_safe_print(f"  Q1:     {scores.quantile(0.25):.4f}")
_safe_print(f"  Q3:     {scores.quantile(0.75):.4f}")

# score 分布区间
bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
labels = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
df_l2['score_bin'] = pd.cut(df_l2['score'], bins=bins, labels=labels, include_lowest=True)
_safe_print(f"\n─── score 分布区间 ───")
score_dist = df_l2['score_bin'].value_counts().sort_index()
_safe_print(score_dist.to_string())

# l2_confidence 统计
_safe_print(f"\n─── l2_confidence 统计 ───")
if 'l2_confidence' in df_l2.columns:
    conf = df_l2['l2_confidence'].dropna()
    _safe_print(f"  mean:   {conf.mean():.4f}")
    _safe_print(f"  median: {conf.median():.4f}")
    _safe_print(f"  min:    {conf.min():.4f}")
    _safe_print(f"  max:    {conf.max():.4f}")

# source 分布
_safe_print(f"\n─── source 分布 ───")
src_counts = df_l2['source'].value_counts()
_safe_print(src_counts.to_string())

# ═══════════════════════════════════════════════════════════
# 3. 核心分析：L2 中误判为 relevant 的无关内容
# ═══════════════════════════════════════════════════════════

_safe_print("\n\n")
_safe_print("=" * 70)
_safe_print("═══ 核心分析：L2 关键词层误判率 ═══")
_safe_print("=" * 70)

# 对 L2 所有条目进行人工抽检逻辑判断
_safe_print(f"\n[1] 对 L2 全部 {len(df_l2)} 条数据进行逐条判断...")

judgments = []
for idx, row in df_l2.iterrows():
    text = str(row.get('text', ''))
    title = str(row.get('title', ''))
    combined = f"{title} {text}"
    is_rel, reason = manual_judge_relevance(combined)
    judgments.append({
        'id_e': row.get('id_e', ''),
        'text': text[:80],
        'title': title[:40],
        'polarity': row.get('polarity', ''),
        'score': row.get('score', 0),
        'manual_relevant': is_rel,
        'manual_reason': reason,
        'tags': str(row.get('tags', '')),
        'source': str(row.get('source', '')),
    })

df_judge = pd.DataFrame(judgments)

# 统计
total_l2 = len(df_judge)
manual_rel = df_judge['manual_relevant'].sum()
manual_irr = total_l2 - manual_rel
misclass_rate = manual_irr / total_l2 * 100

_safe_print(f"\n─── 人工抽检结果 ───")
_safe_print(f"  L2 总数:                {total_l2}")
_safe_print(f"  人工判定 '真正相关':     {manual_rel} ({manual_rel/total_l2*100:.1f}%)")
_safe_print(f"  人工判定 '误判为相关':   {manual_irr} ({misclass_rate:.1f}%)")
_safe_print(f"  *** 误判率:             {misclass_rate:.1f}% ***")

# 按误判原因分组
_safe_print(f"\n─── 误判原因分布 ───")
false_positives = df_judge[~df_judge['manual_relevant']]
reason_counts = false_positives['manual_reason'].value_counts()
_safe_print(reason_counts.to_string())

# 展示误判样本（前 20 条）
_safe_print(f"\n─── 误判样本展示 (前 20 条) ───")
_safe_print(f"{'ID':<8} {'原因':<45} {'文本':<80}")
_safe_print("-" * 140)
for i, (_, row) in enumerate(false_positives.head(20).iterrows()):
    _safe_print(f"{row['id_e']:<8} {row['manual_reason']:<45} {row['text'][:78]}")

# ═══════════════════════════════════════════════════════════
# 4. 抽样 10 条详细展示
# ═══════════════════════════════════════════════════════════

_safe_print("\n\n")
_safe_print("=" * 70)
_safe_print("═══ 抽样 10 条详细展示（均匀抽样） ═══")
_safe_print("=" * 70)

# 均匀抽样
sample_indices = np.linspace(0, len(df_l2) - 1, 10, dtype=int)
sample = df_l2.iloc[sample_indices]

_safe_print(f"\n{'#':<3} {'ID':<8} {'文本':<70} {'polarity':<15} {'score':<7} {'人工判定':<10} {'原因'}")
_safe_print("-" * 160)
for i, (orig_idx, row) in enumerate(sample.iterrows()):
    text = str(row.get('text', ''))[:68]
    title = str(row.get('title', ''))
    combined = f"{title} {text}"
    is_rel, reason = manual_judge_relevance(combined)
    status = "[OK] 相关" if is_rel else "[!!] 误判"
    _safe_print(f"{i+1:<3} {row.get('id_e', ''):<8} {text:<70} {str(row.get('polarity', '')):<15} {row.get('score', 0):<7.2f} {status:<10} {reason}")

# ═══════════════════════════════════════════════════════════
# 5. 误判严重程度分析
# ═══════════════════════════════════════════════════════════

_safe_print("\n\n")
_safe_print("=" * 70)
_safe_print("═══ 误判严重程度分析 ═══")
_safe_print("=" * 70)

# 按 score 分布看误判
_safe_print(f"\n─── 按 score 区间的误判分布 ───")
df_judge['score'] = df_l2['score'].values
score_bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
score_labels = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
df_judge['score_bin'] = pd.cut(df_judge['score'], bins=score_bins, labels=score_labels, include_lowest=True)

for bin_label in score_labels:
    bin_data = df_judge[df_judge['score_bin'] == bin_label]
    if len(bin_data) == 0:
        continue
    misclass = (~bin_data['manual_relevant']).sum()
    rate = misclass / len(bin_data) * 100
    _safe_print(f"  {bin_label}: 总数={len(bin_data):>5}, 误判={misclass:>5} ({rate:5.1f}%)")

# 高 score 但误判的案例（最危险的误判）
_safe_print(f"\n─── 高 score (>=0.8) 但误判的案例 ───")
high_score_fp = df_judge[(df_judge['score'] >= 0.8) & (~df_judge['manual_relevant'])]
_safe_print(f"  数量: {len(high_score_fp)}")
for _, row in high_score_fp.head(10).iterrows():
    _safe_print(f"  [{row['id_e']}] score={row['score']:.2f} | {row['text'][:70]}")

# 按 polarity 的误判分布
_safe_print(f"\n─── 按 polarity 的误判分布 ───")
for pol in ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']:
    pol_data = df_judge[df_judge['polarity'] == pol]
    if len(pol_data) == 0:
        continue
    misclass = (~pol_data['manual_relevant']).sum()
    rate = misclass / len(pol_data) * 100
    _safe_print(f"  {pol:>15}: 总数={len(pol_data):>5}, 误判={misclass:>5} ({rate:5.1f}%)")

# source 层面的误判分布
_safe_print(f"\n─── 按 source 的误判分布 ───")
for src in df_judge['source'].unique():
    src_data = df_judge[df_judge['source'] == src]
    misclass = (~src_data['manual_relevant']).sum()
    rate = misclass / len(src_data) * 100
    _safe_print(f"  {src:<15}: 总数={len(src_data):>5}, 误判={misclass:>5} ({rate:5.1f}%)")

# ═══════════════════════════════════════════════════════════
# 6. L2 GeoJSON 分析
# ═══════════════════════════════════════════════════════════

_safe_print("\n\n")
_safe_print("=" * 70)
_safe_print("═══ L2 GeoJSON 分析 ═══")
_safe_print("=" * 70)

if os.path.exists(GEOJSON_FILE):
    _safe_print(f"\n[OK] GeoJSON 文件存在: {GEOJSON_FILE}")
    file_size = os.path.getsize(GEOJSON_FILE)
    _safe_print(f"     文件大小: {file_size / 1024:.1f} KB")

    with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    features = geojson_data.get('features', [])
    _safe_print(f"     Feature 数量: {len(features)}")
    _safe_print(f"     CRS: {geojson_data.get('crs', {}).get('properties', {}).get('name', 'N/A')}")

    if len(features) > 0:
        # 检查第一个 feature 结构
        first = features[0]
        _safe_print(f"     首个 Feature properties keys: {list(first.get('properties', {}).keys())}")
        _safe_print(f"     首个 Feature geometry type: {first.get('geometry', {}).get('type', 'N/A')}")
else:
    _safe_print(f"\n[ERR] GeoJSON 文件不存在: {GEOJSON_FILE}")

# ═══════════════════════════════════════════════════════════
# 7. 总结
# ═══════════════════════════════════════════════════════════

_safe_print("\n\n")
_safe_print("=" * 70)
_safe_print("═══ 数据质量总结 ═══")
_safe_print("=" * 70)

_safe_print(f"""
┌─────────────────────────────────────────────────────────┐
│  L1 数据质量                                            │
│    总入池:           {len(df_l1):>6}                            │
│    relevant:         {len(relevant):>6} ({len(relevant)/len(df_l1)*100:.1f}%)                      │
│    has_location:     {len(with_location):>6} ({len(with_location)/len(df_l1)*100:.1f}%)                      │
│    urban_value=high: {len(high_value):>6} ({len(high_value)/len(df_l1)*100:.1f}%)                      │
├─────────────────────────────────────────────────────────┤
│  L2 数据质量                                            │
│    总行数:           {total_l2:>6}                            │
│    人工判定真正相关:  {manual_rel:>6} ({manual_rel/total_l2*100:.1f}%)                      │
│    人工判定误判:     {manual_irr:>6} ({misclass_rate:.1f}%)                      │
├─────────────────────────────────────────────────────────┤
│  是否需要 LLM 层？                                      │
│    误判率 = {misclass_rate:.1f}%                                     │
│    {'[!!] 强烈建议启用 LLM 层' if misclass_rate > 15 else '[OK] 关键词层基本可用' if misclass_rate < 5 else '[WARN] 建议启用 LLM 层提升精度'}                     │
└─────────────────────────────────────────────────────────┘
""")

# 是否需要 LLM 层的判断
_safe_print("\n─── 结论与建议 ───")
if misclass_rate > 20:
    _safe_print(f"[!!] 误判率 {misclass_rate:.1f}% 过高 (>20%)，关键词层无法有效区分城市相关内容。")
    _safe_print("      强烈建议启用 LLM 精分类层 (DeepSeek) 进行二次过滤。")
    _safe_print("      当前关键词层主要问题:")
    # 列出 top 误判原因
    top_reasons = reason_counts.head(3)
    for reason, count in top_reasons.items():
        _safe_print(f"        - {reason}: {count} 条")
elif misclass_rate > 10:
    _safe_print(f"[WARN] 误判率 {misclass_rate:.1f}% 偏高 (10-20%)，建议启用 LLM 层提升精度。")
else:
    _safe_print(f"[OK] 误判率 {misclass_rate:.1f}% 可接受 (<10%)，关键词层基本可用。")
