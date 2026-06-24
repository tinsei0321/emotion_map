"""
校验文本池 — L2 极性锚定核心
============================
问题：SnowNLP 对同一意图文本分数会飘，无法稳定讲"二马路前消极后积极"的叙事。
方案：离线为每个 (polarity, element) 写候选文本 -> SnowNLP 打分 -> 只留分数落在
      目标极性带的 -> 存池。SnowNLP 确定性 -> 池稳定，不确定性在建池阶段消化。
      生成时 sample_text(target_polarity, element) 从校验池采样，跑真实 L1->L2 管线
      -> L2 极性 = 目标（确定性）+ 真实分数（可信）。命中率目标 >= 90%。

极性带（对齐 emotion_analysis_v1._score_to_polarity / _polarity_to_ternary）：
  积极 = score > 0.60  (Positive / Very Positive)
  消极 = score <= 0.40 (Negative / Very Negative)
  中性 = 0.40 < score <= 0.60 (Neutral)
  综合 = UI 选择（= 不过滤），无独立池
池内带（SnowNLP 确定性，无随机飘移，可直接对齐管线阈值，留 epsilon 避边界）：
  positive >= 0.65（强积极，叙事清晰）/ negative <= 0.35（强消极）/ neutral 0.41~0.59

中性策略：SnowNLP 对中性表达极挑剔（"就那样/凑合/马马虎虎"竟判负，"中国银行"0.996），
  故 neutral 用**跨要素共享池**（中性情绪本就泛化），不按 element 分格。

用法：
  from emotion_text_pool import sample_text, build_pool
  build_pool()                                  # 建池（首次），缓存到 poi_data/emotion_text_pool.json
  txt = sample_text('negative', 'facility')     # 采样一条已校验文本
"""
import os
import json
import random

_HERE = os.path.dirname(os.path.abspath(__file__))
POOL_FILE = os.path.join(_HERE, 'poi_data', 'emotion_text_pool.json')
CORPUS_FILE = os.path.join(_HERE, 'poi_data', 'emotion_corpus.json')   # v3.3 地域化语料（zone|polarity）


def load_corpus_candidates():
    """加载地域化语料原始候选（zone|polarity -> [text]）。emotion_corpus.json 不存在返回 {}。
    DeepSeek 扩充脚本（generate_corpus.py）往此文件追加，本函数零改动即生效。"""
    if not os.path.exists(CORPUS_FILE):
        return {}
    try:
        data = json.load(open(CORPUS_FILE, encoding='utf-8'))
        return data.get('candidates', data)
    except Exception:
        return {}

# ── 极性带（与 L1->L2 管线阈值对齐）──
POLARITY_BANDS = {
    'positive': (0.65, 1.01),   # 强积极（叙事清晰）
    'negative': (-0.01, 0.35),  # 强消极
    'neutral': (0.41, 0.59),    # SnowNLP 确定性,无 margin,0.41~0.59 留 epsilon 避开 0.40/0.60 边界
}
ELEMENTS = ('facility', 'environment', 'service', 'culture', 'event')
POLARITIES = ('positive', 'negative', 'neutral')


# ── 积极/消极候选：按 (polarity, element) 分格（宜昌/二马路风味，清晰极性线索）──
CANDIDATES = {
    # ── facility 设施（交通/市政/应急）──
    ('positive', 'facility'): [
        '新修的滨江绿道走起来很舒服，规划得不错',
        'BRT 快速公交准点又方便，出行省心',
        '公交站牌更新了，线路清楚多了',
        '停车场改造后车位多了不少，停车方便',
        '这条路修好后通畅多了，赞',
        '新装的路灯晚上亮堂，走着安全',
        '充电桩布局合理，充电方便快捷',
        '公厕翻新后干净整洁，维护得很好',
        '解放路天桥修好了，过街安全',
        '夜间道路标识反光清晰，开车省心',
    ],
    ('negative', 'facility'): [
        '二马路施工封路，绕行太折腾了',
        '这条路坑坑洼洼半年没人修',
        '公交等了四十分钟不来，太差了',
        '停车场收费贵还找不到位，真坑',
        '路灯坏了几天没人修，晚上黑得可怕',
        '下水道堵了，路上全是积水没人管',
        '充电桩坏了好几个一直没人修',
        '施工噪音半夜还在响，扰民',
        '井盖松动没人处理，差点绊倒',
        '道路开挖反复，尘土飞扬',
    ],
    # ── environment 环境（公园/绿化/滨江/空气）──
    ('positive', 'environment'): [
        '滨江公园散步看江景很惬意，环境真好',
        '磨基山公园绿化做得漂亮',
        '运河公园整治后水清了，舒服',
        '街道两旁的银杏秋天特别美',
        '长江沿线景观带做得漂亮，喜欢',
        '小区绿化维护得好，住着舒心',
        '空气清新，适合晨练',
        '江滩改造后面貌一新，很赞',
    ],
    ('negative', 'environment'): [
        '江边垃圾没人清理，味道难闻',
        '公园座椅坏了没人修',
        '施工扬尘太大，不敢开窗',
        '绿化带被踩秃了一片，可惜',
        '江水有异味，怀疑有排污',
        '广场舞噪音扰民，没法休息',
        '河道漂浮物很多，没人打捞',
        '路边的树被乱砍，心疼',
    ],
    # ── service 服务（商业/政务/医疗/教育/便民）──
    ('positive', 'service'): [
        '这家老字号味道正宗，强烈推荐',
        '政务中心办事效率高，一次办好',
        '社区医院服务态度很好，点赞',
        '便利店 24 小时营业，方便',
        '万达广场品牌全，逛着舒服',
        '店员热情周到，购物体验好',
        '学校新换了课桌椅，孩子们开心',
        '物业服务到位，响应及时',
    ],
    ('negative', 'service'): [
        '窗口排队两小时，办事效率太低',
        '这家店服务态度差，不会再来了',
        '医院挂号太难，等得太久',
        '物业不作为，投诉没人理',
        '快递丢件了客服推诿扯皮',
        '餐厅上菜慢，菜都凉了',
        '办事大厅工作人员态度冷漠',
        '维修预约了一周都没人上门',
    ],
    # ── culture 文化（历史/文创/博物馆/老字号/节庆）──
    ('positive', 'culture'): [
        '二马路老街区改造后很有味道，喜欢',
        '博物馆展览内容丰富，值得一看',
        '文创市集热闹又有创意，点赞',
        '老字号保护得好，有传承',
        '历史建筑修缮得很用心',
        '非遗活动办得精彩',
        '街区夜景漂亮，适合打卡',
        '剧院演出水准很高，推荐',
    ],
    ('negative', 'culture'): [
        '文物修缮太敷衍，丢了原味，可惜',
        '老建筑被拆了，心疼',
        '文化活动组织混乱，体验差',
        '文创产品同质化严重，没意思',
        '历史街区过度商业化，变味了',
        '博物馆展品更新太慢',
        '节庆活动人挤人，体验糟糕',
        '剧院音响效果差，失望',
        '老街区改造后失去原有韵味，遗憾',
        '文物被破坏无人过问，痛心',
        '传统手艺后继无人，可悲',
        '文化设施破旧失修，令人失望',
    ],
    # ── event 事件（活动/夜经济/市集/应急/舆情）──
    ('positive', 'event'): [
        '夜市开市了，烟火气十足，热闹',
        '国庆活动办得热闹喜庆',
        '文创市集周末很火，氛围好',
        '灯光秀很震撼，点赞',
        '美食节种类丰富，逛得开心',
        '街区活动吸引很多人，有活力',
        '夜经济让城市更有活力了',
        '文化节组织有序，体验棒',
    ],
    ('negative', 'event'): [
        '活动结束垃圾满地没人扫，太乱',
        '夜市噪音扰民，投诉不断',
        '节日人多拥挤差点出事',
        '灯光秀人流管控混乱',
        '活动组织无序，体验很差',
        '突发暴雨活动没应急预案',
        '节庆交通拥堵严重，寸步难行',
        '演出取消也没提前通知，坑',
    ],
}

# ── 中性候选：跨要素共享（SnowNLP 实测落 0.41~0.59 的表达）──
# SnowNLP 对中性极挑剔，这些是离线 debug 出的稳定中性句；不按 element 分格。
NEUTRAL_CANDIDATES = [
    '一般般',
    '普普通通',
    '普通',
    '没什么特别',
    '没什么亮点',
    '感觉一般',
    '就这样吧',
    '也就那样吧',
    '价格普通',
    '普通水平',
    '一般水平',
    '设双向四车道',
    '营业十二小时',
    '活动为期三天',
]


def _snownlp_score(text):
    """SnowNLP 情感分（0~1）。失败返回 None。"""
    try:
        from snownlp import SnowNLP
        return float(SnowNLP(str(text).strip()).sentiments)
    except Exception:
        return None


def _in_band(score, polarity):
    if score is None:
        return False
    lo, hi = POLARITY_BANDS[polarity]
    return lo <= score <= hi


def build_pool(verbose=True):
    """对所有候选过 SnowNLP，只留落在目标极性带的，持久化到 POOL_FILE。
    积极/消极按 element 分格；中性共享一份填入每个 element 格。"""
    pool = {}
    stats = {}

    # 积极/消极：按 (polarity, element) 分格
    for (pol, elem), texts in CANDIDATES.items():
        kept = [t for t in texts if _in_band(_snownlp_score(t), pol)]
        pool['{}|{}'.format(pol, elem)] = kept
        stats['{}|{}'.format(pol, elem)] = (len(kept), len(texts))

    # 中性：共享池填入每个 element 格
    neu_kept = [t for t in NEUTRAL_CANDIDATES if _in_band(_snownlp_score(t), 'neutral')]
    for elem in ELEMENTS:
        pool['neutral|{}'.format(elem)] = list(neu_kept)
    stats['neutral|*'] = (len(neu_kept), len(NEUTRAL_CANDIDATES))

    # v3.3 地域化语料：zone|polarity -> 落带的文本（locality 文本，sample_text 地域优先抽）
    corpus = load_corpus_candidates()
    for key, texts in corpus.items():
        parts = key.split('|')
        if len(parts) != 2:
            continue
        _zone, pol = parts[0], parts[1]
        if pol not in POLARITY_BANDS:
            continue
        kept = [t for t in texts if _in_band(_snownlp_score(t), pol)]
        pool[key] = kept
        stats[key] = (len(kept), len(texts))

    os.makedirs(os.path.dirname(POOL_FILE), exist_ok=True)
    json.dump(pool, open(POOL_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    if verbose:
        total_kept = sum(v[0] for v in stats.values())
        total_cand = sum(v[1] for v in stats.values())
        for k in sorted(stats):
            kept, cand = stats[k]
            mark = '[WARN]' if kept < 4 else '[OK]  '
            print('  {}{}: {}/{}'.format(mark, k, kept, cand))
        rate = (100.0 * total_kept / total_cand) if total_cand else 0
        print('[OK] pool kept {}/{} ({:.0f}%) -> {}'.format(
            total_kept, total_cand, rate, POOL_FILE.replace('\\', '/')))
    return pool


def load_pool(rebuild=False):
    """加载池；rebuild=True 或缓存不存在时重建。"""
    if rebuild or not os.path.exists(POOL_FILE):
        return build_pool(verbose=False)
    return json.load(open(POOL_FILE, encoding='utf-8'))


def sample_text(polarity, element, pool=None, rng=random, zone=None, flavor=None, locality_bias=0.65):
    """从校验池采样一条文本。
    v3.3 地域化：若给 zone 且 rng<locality_bias 且该 zone|polarity 地域桶非空 -> 抽地域文本
    （含 place_keywords = 本地相关）；否则退通用 (polarity,element) 池。
    polarity ∈ {positive,negative,neutral}；element ∈ 5 类；zone ∈ place_layer zone_id。
    flavor 预留（corpus 含 flavor 变体时优先；起步语料未分 flavor，暂不影响）。"""
    if pool is None:
        pool = load_pool()
    # 地域优先（v3.3）—— zone|polarity 桶
    if zone:
        ztexts = pool.get('{}|{}'.format(zone, polarity)) or []
        if ztexts and rng.random() < locality_bias:
            return rng.choice(ztexts)
    # 通用 (polarity, element)；空则回退同 polarity 任意 element 格
    key = '{}|{}'.format(polarity, element)
    texts = pool.get(key) or []
    if not texts:
        for k, v in pool.items():
            if k.startswith('{}|'.format(polarity)) and v:
                texts = v
                break
    return rng.choice(texts) if texts else ''


def pool_stats(pool=None):
    """返回每格样本数 dict，供健康检查。"""
    pool = pool or load_pool()
    return {k: len(v) for k, v in pool.items()}


if __name__ == '__main__':
    build_pool()
