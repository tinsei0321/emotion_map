# -*- coding: utf-8 -*-
"""治理 2024年12345投诉数据_raw.xlsx → 两份文件落 06_主观数据治理/。

文件 1 · 12345_治理清洗版.csv（8 条要求·57265 行）
文件 2 · 12345_情绪地图中转版.csv（EMC 消费·polarity/score 0~1/4×5/place/region_scope）

对齐：CB-23 12345 治理方案反评价收敛定稿（Codex 4 P1 + 8 P2 全采纳）。
用法：py SCRIPT/govern_12345_raw.py
"""
import json
import os
import re
import sys

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

RAW = r"D:/OneDrive/2026/15_城市更新专项规划研究/1 宜昌市城市体检/2024年12345投诉数据_raw.xlsx"
OUT = r"D:/OneDrive/2026/15_城市更新专项规划研究/1 宜昌市城市体检/EMC数据中转站/06_主观数据治理"
os.makedirs(OUT, exist_ok=True)

# ── 区域代码 → 区名（宜昌行政区划代码）──
REGION_CODE = {
    '420502': '西陵区', '420503': '伍家岗区', '420504': '点军区',
    '420505': '猇亭区', '420506': '夷陵区', '420507': '夷陵区',
    '420528': '长阳土家族自治县', '420582': '当阳市',
}
# 中心城区（P1-4 口径·两板块报告用）
CENTRAL = {'西陵区', '伍家岗区', '点军区', '猇亭区'}

# ── 诉求类型 → 系统化归类 ──
TYPE_RULE = {
    '投诉类': '投诉',
    '咨询类': '咨询',
    '建议类': '建议',
    '求助类': '求助',
    '表扬类': '表扬',
    '其它类': '其它',
    '营商环境类': '其它',
}

# ── 情绪 5 级映射（结合诉求类型 + 内容关键词·对齐 EMC L2 枚举）──
# score 按 _score_to_polarity 分档：Very Negative=0.1/Negative=0.3/Neutral=0.5/Positive=0.7/Very Positive=0.9
NEG_HARD = ['强烈', '严重', '紧急', '尽快', '马上', '危险', '扰民严重', '无法', '投诉强烈']
# Codex P2-5：去「建议」自指（建议类标题/内容必含「建议」→ 全升 Positive 偏离默认 Neutral 意图）·语气词=真正正面
POS_SOFT = ['期盼', '希望', '期待', '点赞', '感谢', '满意']


def map_polarity(type_, title='', content=''):
    """诉求类型 + 标题/内容关键词 → (polarity, score)。"""
    txt = f"{title} {content}"
    if type_ == '表扬':
        return 'Very Positive', 0.9
    if type_ == '投诉':
        if any(k in txt for k in NEG_HARD):
            return 'Very Negative', 0.1
        return 'Negative', 0.3
    if type_ == '求助':
        return 'Negative', 0.3
    if type_ == '建议':
        # 建议默认 Neutral·含正面语气升 Positive
        if any(k in txt for k in POS_SOFT) and not any(k in txt for k in NEG_HARD):
            return 'Positive', 0.7
        return 'Neutral', 0.5
    # 咨询 / 其它 / 营商环境
    return 'Neutral', 0.5


# ── 4×5 映射（读 12345_4x5映射.json）──
with open(os.path.join(OUT, '12345_4x5映射.json'), encoding='utf-8') as f:
    _MAP = json.load(f)
MEDIUM_MAP = _MAP['medium_mapping']
MAJOR_FALLBACK = _MAP['major_fallback']
UNMAPPED = _MAP['unmapped_default']


def map_4x5(major, medium):
    if medium in MEDIUM_MAP:
        return MEDIUM_MAP[medium]
    if major in MAJOR_FALLBACK:
        return MAJOR_FALLBACK[major]
    return UNMAPPED


# ── 地点提取（内容·完整地名·79% 覆盖）──
# 匹配完整地名（「滨江公园」「夷陵区新坪村」「西陵区二马路55号」「吾悦广场」·非泛词）
_PLACE_RE = re.compile(r'[^\s，。；、]{2,30}(?:小区|路|街|大道|巷|桥|广场|公园|市场|社区|苑|村|镇|路口|站|店|楼|医院|学校)')
_PREFIXED = re.compile(r'(?:湖北省宜昌市)?[一-龥]{2,4}(?:区|市)[一-龥]{2,20}(?:小区|路|街|大道|巷|桥|广场|公园|市场|社区|苑|村|镇|路口|站|店|楼)')


def extract_place(content):
    """从诉求内容提取完整地名（返回首个具体地名·非泛词）。"""
    if pd.isna(content):
        return ''
    c = str(content)
    # 优先带区/市前缀的完整地名（最细粒度·可对坐标）
    m = _PREFIXED.search(c)
    if m:
        return m.group(0)
    # 次优：普通完整地名（滨江公园/吾悦广场/凯旋名邸小区）
    m2 = _PLACE_RE.search(c)
    if m2:
        return m2.group(0)
    return ''




# ── 地点清洗（Codex 审计 P1：去口语前缀 + 门牌/楼栋降级）──
_PREFIX_STRIP = re.compile(r'^(?:我是|上到|反映|位于|来电|接到|本人|关于|咨询|进入|旁边|在|于|因|反映人|来电人|诉求人|居住在|住在|靠近|围绕|经过|途径|走到|到|去|在附近|住在)')
_MENPAI = re.compile(r'\d+号(?:院|楼|房)?')
_LOUDONG = re.compile(r'\d+[号楼栋]')


def clean_place(place, conf):
    """地点清洗：剥离口语前缀 + 门牌/楼栋降级到小区/道路/街办级·重算 confidence。"""
    if not place:
        return place, conf
    p = str(place)
    # ① 剥口语前缀（锚定地名起点）
    p = _PREFIX_STRIP.sub('', p).strip()
    # ② 门牌降级：西陵区二马路55号 → 西陵区二马路
    p = _MENPAI.sub('', p).strip('，。、 ')
    # ③ 楼栋降级：龙盘湖世纪山水九号楼 → 龙盘湖世纪山水
    p = _LOUDONG.sub('', p).strip('，。、 ')
    # ④ 空后重算 conf
    if not p:
        return '', ''
    return p, conf


def infer_place(row):
    """地点三级推断：内容地点词 → 主办部门街办 → 区域。返回 (place, source, conf)。"""
    content = str(row.get('诉求内容', '')) or ''
    office = str(row.get('主办部门', '')) or ''
    region = str(row.get('区域', '')) or ''
    # ① 内容完整地名（滨江公园/夷陵区新坪村/西陵区二马路55号·最细粒度·可对坐标）
    phit = extract_place(content)
    if phit:
        conf = 'high' if re.match(r'.*(?:区|市)', phit) else 'medium'
        phit_c, conf_c = clean_place(phit, conf)
        if phit_c:
            return phit_c, 'content', conf_c
        return '', 'empty', ''
    # ② 主办部门街办（西陵区云集街办）
    m2 = re.search(r'([\u4e00-\u9fa5]{2,4}(?:区|市)[\u4e00-\u9fa5]{2,6}(?:街办|街道|镇))', office)
    if m2:
        return m2.group(1), 'office', 'medium'
    # ④ 区域兜底
    if region:
        return region, 'region', 'low'
    return '', 'empty', ''


def simplify_title(row):
    """标题简化：参考大类/中类/小类。"""
    medium = str(row.get('中类', '')) or ''
    small = str(row.get('小类', '')) or ''
    title = str(row.get('诉求标题', '')) or ''
    # 用中类/小类做简洁描述（去「问题/噪声」冗余）
    if small:
        return small
    if medium:
        return medium
    return title[:20]


def main():
    df = pd.read_excel(RAW)
    print(f"[LOAD] {len(df)} 行")
    out = pd.DataFrame()
    # 1) 办件编号 + 投诉时间（事件上报时间·完整时间戳）
    out['办件编号'] = df['办件编号'].astype(str).str.zfill(14)
    out['投诉时间'] = df['事件上报时间'].astype(str).str[:10]
    out['事件时间'] = df['事件上报时间'].astype(str).str[:10]  # 事件时间未知默认=投诉时间
    # 2) 诉求类型归
    out['诉求类型_归'] = df['诉求类型'].map(TYPE_RULE).fillna('其它')
    # 3) 标题简化
    out['诉求标题_简'] = df.apply(simplify_title, axis=1)
    # 4) 内容结构化（时间+地点+事件+态度）
    out['诉求内容_构'] = df.apply(
        lambda r: f"{str(r['事件上报时间'])[:10]};{extract_place(str(r.get('诉求内容','')))};{str(r.get('诉求内容',''))[:120]}", axis=1)
    # 5) 事发地 + 地点推断
    out['事发地'] = df['事发地']
    place_info = df.apply(infer_place, axis=1, result_type='expand')
    out['地点推断'] = place_info[0]
    out['place_source'] = place_info[1]
    out['place_confidence'] = place_info[2]
    # 6) 区域清洗
    out['区域'] = df['区域'].astype(str).str.strip()
    out['区域_清洗'] = out['区域'].map(REGION_CODE).fillna(out['区域'])
    # CB-23 审计 P2-2（Codex）：高新区东山园区地理上属中心城区功能组团·但含白洋镇等外围——单列「高新区」防漏计也防误算
    out['region_scope'] = out['区域_清洗'].apply(
        lambda r: '中心城区' if r in CENTRAL else ('高新区' if r == '高新区' else '县市'))
    # 7) 大类/中类/小类整合
    out['大类_归'] = df['大类']
    out['中类_归'] = df['中类']
    out['小类_归'] = df['小类']
    # 8) 主办部门 + 评价结果
    out['主办部门'] = df['主办部门']
    out['评价结果'] = df['评价结果']
    out['source'] = '2024年12345投诉数据_raw'
    # 写治理清洗版
    out.to_csv(os.path.join(OUT, '12345_治理清洗版.csv'), index=False, encoding='utf-8-sig')
    print(f"[OK] 治理清洗版 {len(out)} 行·落 {OUT}")

    # ── 文件 2 · 情绪地图中转版 ──
    t2 = pd.DataFrame()
    t2['办件编号'] = out['办件编号']
    t2['投诉时间'] = out['投诉时间']
    # 情绪 5 级（type 用映射后系统类型·非原始「投诉类」）
    _type_mapped = out['诉求类型_归']
    pol = df.apply(lambda r: map_polarity(_type_mapped.iloc[r.name], r['诉求标题'], r['诉求内容']), axis=1, result_type='expand')
    t2['polarity'] = pol[0]
    t2['score'] = pol[1]
    t2['polarity_score_5'] = t2['polarity'].map({'Very Negative': 1, 'Negative': 2, 'Neutral': 3, 'Positive': 4, 'Very Positive': 5})
    t2['emotion_intensity'] = df['诉求内容'].apply(lambda c: 0.7 if '强烈' in str(c) or '严重' in str(c) else 0.5)
    # 4×5 归因
    m45 = df.apply(lambda r: map_4x5(str(r['大类']), str(r['中类'])), axis=1, result_type='expand')
    t2['domain'] = m45[0]
    t2['element'] = m45[1]
    # topic/issue_label
    t2['topic'] = df['中类']
    t2['issue_label'] = df['小类']
    # place + region_scope
    t2['place_name'] = out['地点推断']
    t2['place_source'] = out['place_source']
    t2['place_confidence'] = out['place_confidence']
    t2['region'] = out['区域_清洗']
    t2['region_scope'] = out['region_scope']
    t2['lon'] = ''
    t2['lat'] = ''
    # Codex P2-6：emotion_aspect 补「期盼」——建议类内容含 期盼/希望/期待 → 期盼（_followupCue/_keywordRank 层消费·不造 5 级）
    _aspect = df['诉求类型'].map(TYPE_RULE).fillna('其它')
    _qiwang = df.apply(lambda r: ('建议' == _aspect.iloc[r.name] and any(
        k in str(r['诉求内容']) for k in ('期盼', '希望', '期待'))), axis=1)
    t2['emotion_aspect'] = _aspect.mask(_qiwang, '期盼')
    t2['source'] = '2024年12345投诉数据_raw'
    t2.to_csv(os.path.join(OUT, '12345_情绪地图中转版.csv'), index=False, encoding='utf-8-sig')
    print(f"[OK] 情绪地图中转版 {len(t2)} 行·落 {OUT}")


if __name__ == '__main__':
    main()
