#!/usr/bin/env python3
"""
模拟数据生成脚本 v1.0
=====================
生成 10 万条逼近真实的社交媒体 L0 原始数据，用于 MVP 测试 L0->L1->L2 全管线。

数据设计:
  - 无关内容 ~90% (9万条): 美妆/穿搭/情感/日常/宠物/搞笑/广告/学习/其他
  - 城市相关 ~10% (1万条): 设施/环境/服务/文化/事件
  - 平台分布: 小红书40% 微博30% 大众点评20% 美团5% 12345热线5%
  - 坐标范围: 宜昌市西陵区及周边 (lon:111.25~111.38, lat:30.68~30.75)
  - 空间聚类: 10个高斯混合簇模拟市民活动热点

输出: DATA/raw/simulated_20260613_100k_raw.csv

用法: python SCRIPT/generate_test_data.py
"""

import os
import sys
import random
import builtins as _bi
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# ── 安全 print — 防止 Windows GBK 控制台崩溃 ──
_real_print = _bi.print

def _safe_print(*args, **kwargs):
    try:
        _real_print(*args, **kwargs)
    except UnicodeEncodeError:
        _real_print(
            *(str(a).encode('ascii', errors='replace').decode('ascii') for a in args),
            **kwargs,
        )

# 修复 Windows GBK 控制台编码
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ═══════════════════════════════════════════════════════════
# 全局配置
# ═══════════════════════════════════════════════════════════

random.seed(42)
np.random.seed(42)

TOTAL_COUNT = 100_000
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'simulated_20260613_100k_raw.csv')

CRAWL_TIME = datetime(2026, 6, 13, 12, 0, 0)
PUBLISH_START = datetime(2026, 3, 13)
PUBLISH_END = datetime(2026, 6, 13)
PUBLISH_RANGE_SEC = int((PUBLISH_END - PUBLISH_START).total_seconds())

# ═══════════════════════════════════════════════════════════
# 宜昌地名词汇池 (40+ 真实地名)
# ═══════════════════════════════════════════════════════════

YICHANG_DISTRICTS = [
    '西陵区', '伍家岗区', '点军区', '猇亭区', '夷陵区',
]

YICHANG_PARKS = [
    '滨江公园', '东山公园', '运河公园', '儿童公园', '磨基山公园', '夷陵广场',
]

YICHANG_ROADS = [
    '沿江大道', '胜利四路', '云集路', '东山大道', '夷陵大道',
    '发展大道', '城东大道', '港窑路', '西陵一路', '珍珠路',
]

YICHANG_COMMERCIAL = [
    'CBD', '万达广场', '国贸大厦', '均瑶广场', '水悦城',
]

YICHANG_AREAS = [
    '锦绣社区', '白龙岗小区', '绿萝路', '体育场路', '葛洲坝', '三峡大学',
]

YICHANG_NATURAL = [
    '长江', '黄柏河', '东山',
]

# 合并全量地名池
ALL_PLACES = (
    YICHANG_DISTRICTS + YICHANG_PARKS + YICHANG_ROADS +
    YICHANG_COMMERCIAL + YICHANG_AREAS + YICHANG_NATURAL
)

# 详细地点名（用于组合，如"XX小区附近"、"XX路和XX路交叉口"）
PLACE_DETAIL = [
    'CBD中央大街', '万达金街', '国贸负一楼', '均瑶广场门口',
    '水悦城星巴克', '滨江公园大门口', '东山公园山顶', '运河公园步道',
    '儿童公园北门', '夷陵广场喷泉', '三峡大学图书馆', '三峡大学沁苑',
    '锦绣社区门口', '白龙岗小区南门', '葛洲坝公园', '绿萝路菜市场',
    '体育场路加油站', '沿江大道中段', '发展大道高速口', '城东大道BRT站',
    '港窑路口', '西陵一路天桥', '珍珠路小学', '东山大道长途站',
    '夷陵大道中医院', '云集路商场', '胜利四路滨江', '磨基山森林公园',
]

# 社区/小区名
COMMUNITY_NAMES = [
    '锦绣社区', '白龙岗小区', '绿萝路小区', '华祥商业中心',
    '香山福久源', '宏峰上上城', '碧桂园公园壹号', '恒大绿洲',
    '万科理想城', '中建之星', '世纪山水', '江山多娇',
    '虹桥国际', '金色海岸', '长江瑞景', '御景天地',
    '东辰壹号', '香格里拉', '锦绣天下', '紫晶城',
]

# ═══════════════════════════════════════════════════════════
# 无关内容 — 词汇池
# ═══════════════════════════════════════════════════════════

BEAUTY_BRANDS = [
    '兰蔻', '雅诗兰黛', 'SK-II', '完美日记', '花西子', 'MAC', '迪奥',
    '香奈儿', 'YSL', '阿玛尼', '资生堂', '欧莱雅', '珂润', '理肤泉',
    '薇诺娜', 'OLAY', '赫莲娜', '海蓝之谜', 'CPB', 'NARS',
    '3CE', 'colorkey', 'INTO YOU', '花知晓', '毛戈平', '珀莱雅',
    '丸美', '自然堂', '百雀羚', '相宜本草',
]

BEAUTY_PRODUCTS = [
    '粉底液', '口红', '眼影盘', '精华', '面霜', '防晒霜', '卸妆油',
    '眉笔', '腮红', '睫毛膏', '面膜', '气垫', '妆前乳', '定妆喷雾',
    '遮瑕膏', '高光', '修容', '眼线笔', '唇釉', '隔离霜',
    '洗面奶', '爽肤水', '乳液', '眼霜', '颈霜', '身体乳',
]

SKIN_TYPES = ['干皮', '油皮', '混合皮', '敏感肌', '痘痘肌', '中性皮']

BEAUTY_EMOJI = [
    '\U0001f484', '\U0001f48b', '\U0001f48d', '\u2728', '\U0001f31f',
    '\U0001f338', '\U0001f495', '\U0001f60d', '\U0001f3b5', '\u2600\ufe0f',
]

FASHION_ITEMS = [
    '卫衣', '牛仔裤', '连衣裙', '西装外套', '风衣', '针织衫', '阔腿裤',
    '半身裙', 'T恤', '衬衫', '棒球帽', '运动鞋', '马丁靴', '帆布鞋',
    '毛衣', '羽绒服', '短裤', '吊带裙', '开衫', '百褶裙', '皮衣',
    '牛仔外套', '雪纺衫', '打底衫', '烟管裤', 'A字裙', '老爹鞋',
]

FASHION_COLORS = [
    '奶白', '雾霾蓝', '焦糖', '豆沙粉', '牛油果绿', '香芋紫', '克莱因蓝',
    '卡其', '黑色', '燕麦色', '奶茶色', '复古红', '莫兰迪', '米色',
]

SEASONS = ['春天', '夏天', '秋天', '冬天', '初春', '深秋', '初夏', '入冬']

FASHION_EMOJI = [
    '\U0001f45c', '\U0001f460', '\U0001f457', '\U0001f456', '\u2728',
    '\U0001f338', '\u2601\ufe0f', '\U0001f31e', '\U0001f343', '\u2764\ufe0f',
]

EMOTION_WORDS = ['前任', '初恋', '暗恋对象', '闺蜜', '男朋友', '女朋友', '家里人', '室友', '同事', '领导']

EMOTION_EVENTS = [
    '下雨了', '失眠了', '加班到深夜', '一个人吃饭', '看到朋友圈',
    '翻到老照片', '听了首歌', '走在路上', '做梦梦到', '喝多了',
]

EMOTION_EMOJI = [
    '\U0001f622', '\U0001f494', '\U0001f497', '\U0001f525', '\U0001f33b',
    '\u2614', '\U0001f319', '\U0001f33f', '\u2764\ufe0f\u200d\U0001f525',
]

DAILY_TOPICS = [
    '今天天气', '周末去哪玩', '午饭吃什么', '减肥第N天', '熬夜冠军',
    '今天上班', '宅家一天', '追剧中', '健身打卡', '学做饭',
    '收拾房间', '逛超市', '洗衣服', '午睡', '外卖到了',
]

DAILY_EMOJI = [
    '\U0001f4aa', '\U0001f34c', '\u2615', '\U0001f3a7', '\U0001f4f1',
    '\U0001f3a5', '\U0001f60a', '\U0001f44d', '\u270c\ufe0f',
]

PET_TYPES = ['猫', '狗', '仓鼠', '兔子', '鹦鹉', '金毛', '布偶猫', '英短', '柴犬', '柯基', '橘猫', '泰迪', '美短', '哈士奇', '比熊']

PET_ACTIONS = ['撒娇', '卖萌', '拆家', '睡觉', '吃饭', '洗澡', '打滚', '黏人', '发呆', '跑酷']

PET_EMOJI = ['\U0001f431', '\U0001f436', '\U0001f430', '\U0001f439', '\U0001f426', '\U0001f981', '\U0001f43e']

JOKE_TEMPLATES_SIMPLE = [
    '哈哈哈笑不活了', '今日份快乐源泉', '这也太搞笑了吧', '笑死我对你有什么好处',
    '救命笑疯了', '我不允许还有人没看过这个', '哈哈哈哈哈哈哈哈', '笑点低慎入',
    '今日最佳', '这也太真实了', '是谁在偷窥我的生活', '转发了让更多人看到',
]

AD_PRODUCTS = ['减肥茶', '美白丸', '祛痘膏', '增高药', '理财课程', '副业培训', 'POS机', '信用卡代办', '微商爆款', '酵素果冻']
AD_JOBS = ['客服', '打字员', '刷单员', '手工活', '主播', '模特', '配音员']
AD_AMOUNTS = ['100', '200', '300', '500', '800', '1000', '1500']

STUDY_TOPICS = ['考研', '考公', '雅思', '托福', 'CPA', '法考', '教资', '四六级', '专升本', '计算机二级']
STUDY_ACTIONS = ['打卡', '刷题', '背单词', '上课', '模考', '出分', '查成绩', '面试', '复试', '调剂']
STUDY_EMOJI = ['\U0001f4da', '\u270d\ufe0f', '\U0001f4aa', '\U0001f3af', '\U0001f4af', '\U0001f31f']

OTHER_TOPICS = [
    '游戏日常', '分享一首好听的歌', '今日幸运色', '星座运势',
    '手机壁纸分享', '头像合集', '晚安打卡', '早安世界',
    '朋友圈文案', '深夜emo', '无聊中', '求互关',
]

# ═══════════════════════════════════════════════════════════
# 无关内容 — 模板池 (每类 >= 10 种句式变体)
# ═══════════════════════════════════════════════════════════

BEAUTY_TEMPLATES = [
    '{brand}新出的{product}也太好用了吧 {emoji}',
    '求推荐适合{skin}的{product}',
    '{brand}{product}测评来啦，用完皮肤真的变好了',
    '姐妹们{brand}这波新品值得冲吗',
    '终于找到适合{skin}的{product}了，绝绝子 {emoji}',
    '{brand1}vs{brand2} {product}对比测评，结果出乎意料',
    '囤的{product}终于到了，开箱分享 {emoji}',
    '踩雷了{brand}{product}，用完过敏了 {emoji}',
    '{product}平替找到了，只要{brand}十分之一的价格',
    '今日妆容 | {product1}+{product2} yyds {emoji}',
    '{skin}必入{product}清单，亲测好用',
    '{brand}柜姐推荐的这个{product}真的值得买吗',
    '换季护肤routine | {product}一定要用起来',
    '空瓶记 | {brand}{product}我回购了三次',
]

FASHION_TEMPLATES = [
    '今日OOTD {emoji} {season}穿搭分享',
    '{item1}搭配{item2}真的绝了 {emoji}',
    '{season}衣橱必备{item}推荐，百搭又好看',
    '小个子女生{item}穿搭指南，显高显瘦',
    '{color}系穿搭也太温柔了吧 {emoji}',
    '{season}流行{item}，你get了吗',
    '上班通勤穿搭 | {item}一周不重样',
    '微胖女生{item}这样穿显瘦10斤 {emoji}',
    '{item}的N种穿法，一件穿出不同风格',
    '学生党平价{item}推荐，百元内搞定 {emoji}',
    '约会穿搭 | {item}+{item2}回头率爆表',
    '{season}胶囊衣橱 | 10件{item}搭出30套',
    '今天穿{item}出门被夸了 {emoji}',
    '最近超爱{color}色系的{item}',
]

EMOTION_TEMPLATES = [
    '{time_word}了还是忘不掉{person}',
    '今天{event}，突然好想{person}',
    '{person}离开的第N天，还是会难过 {emoji}',
    '如果当初没有{action}，现在会不会不一样',
    '{event}的时候，第一个人想到的还是{person}',
    '成年人的崩溃就在一瞬间 {emoji}',
    '{person}结婚了，祝福但心里空落落的',
    '{time_word}没联系{person}了，大家都还好吗',
    '有些话想说但不知道发给谁 {emoji}',
    '一个人{action}的时候最想家',
    '翻到和{person}的聊天记录，感慨万千',
    '长大就是学会和孤独相处吧 {emoji}',
    '今天{event}，突然觉得好累',
    '深夜了，{person}你睡了吗',
]

EMOTION_TIME_WORDS = ['这么久了', '大半年', '好几个月', '快一年', '整整两年', '三年多']
EMOTION_ACTIONS = ['坚持', '放手', '勇敢一点', '主动联系', '不那么倔', '早点明白', '好好说再见']

DAILY_TEMPLATES = [
    '{topic} {emoji}',
    '今天{topic}，感觉还不错',
    '{topic}第一天，加油 {emoji}',
    '又是{topic}的一天 {emoji}',
    '{topic}记录 | Day{day}',
    '日常{topic}分享 {emoji}',
    '周末就是用来{topic}的 {emoji}',
    '最近的日常：{topic1}、{topic2}、{topic3}',
    '{topic}打卡完成 {emoji}',
    '今天没干啥，就是{topic}',
    '{topic}日常碎碎念',
    '平淡的一天从{topic}开始 {emoji}',
    '今日份{topic}已送达',
    '在家{topic}的一天，舒服 {emoji}',
]

PET_TEMPLATES = [
    '我家{pet}太可爱了 {emoji}',
    '{pet}今天{action}的样子笑死我了 {emoji}',
    '养{pet}的快乐谁懂啊 {emoji}',
    '我家{pet}又在{action}了，管不住了',
    '{pet}的{action}日常 {emoji}',
    '回家看到{pet}在{action}，一天的疲惫都没了',
    '求问{pet}{action}怎么办，在线等',
    '{pet}绝育后的变化，太搞笑了 {emoji}',
    '晒一下我家{pet}的{action}瞬间',
    '云吸{pet}的来 {emoji}',
    '{pet}和{pet2}的相处模式 be like',
    '{pet}今天{action}被我抓到了 {emoji}',
]

JOKE_TEMPLATES = [
    '{joke} {emoji}',
    '刷到一个好笑的 {joke}',
    '{joke}，建议全文背诵',
    '今日幽默：{joke}',
    '{joke}，笑点低的别进',
    '在微博看到这个笑出声 {joke}',
    '{joke}，我不信有人能不笑',
    '同事发我的 {joke}，分享给大家',
    '{joke}，懂的都懂 {emoji}',
    '{joke}，已笑疯',
    '这个段子我能笑一年 {joke}',
    '{joke}，过于真实引起不适',
]
JOKE_EMOJI = ['\U0001f602', '\U0001f923', '\U0001f92d', '\U0001f61c', '\U0001f929']

AD_TEMPLATES = [
    '{product}限时优惠，加微信{wechat}了解',
    '招聘{job}，日结{amount}，简单好做',
    '在家就能做的{job}，月入过万不是梦',
    '正品{product}一手货源，代理价拿货加{wechat}',
    '急招{job}，无经验可培训，薪资{amount}/天',
    '{product}效果好到爆，无效退款 VX:{wechat}',
    '新项目招募合伙人，{job}方向，零成本创业',
    '处理{product}尾货，白菜价甩卖，加{wechat}',
    '【招募】{job}若干名，工资{amount}日结',
    '厂家直销{product}，价格低到你不敢信',
    '免费招代理，{product}一件代发，+V:{wechat}',
    '在家兼职{job}，手机即可操作，{amount}/天',
]

STUDY_TEMPLATES = [
    '{study}人集合 {emoji}',
    '{study}{action}打卡 Day{day} {emoji}',
    '{study}倒计时{count}天，冲鸭 {emoji}',
    '今天{study}{action}效率好低 {emoji}',
    '{study}资料分享，需要的私我',
    '{study}上岸经验贴 | {action}篇',
    '{study}出分了，{score}分什么水平',
    '{study}人的一天：{action1}->{action2}->{action3}',
    '求{study}搭子，一起{action}互相监督',
    '{study}复试{action}经验总结 {emoji}',
    '二战{study}的第{count}天 {emoji}',
    '{study}{action}必备APP推荐',
    '{study}人深夜{action}实录 {emoji}',
    '报！{study}国家线出来了',
]

OTHER_TEMPLATES = [
    '{topic} {emoji}',
    '分享一个{topic}',
    '今日{topic}已更新',
    '{topic}，有人一起吗',
    '无聊发个{topic}',
    '{topic} | 纯分享',
    '晚上好，{topic}时间到',
    '有人在吗，聊{topic}',
    '{topic}打卡 {emoji}',
    '最近沉迷{topic}',
]

# ═══════════════════════════════════════════════════════════
# 城市相关内容 — 词汇池
# ═══════════════════════════════════════════════════════════

FACILITY_ITEMS = [
    '路灯', '停车位', '电梯', '消防设施', '监控', '门禁', '绿化',
    '健身器材', '垃圾桶', '下水道', '楼道灯', '充电桩', '消防通道',
    '护栏', '减速带', '斑马线', '红绿灯', '公交站台', '公共厕所',
    '快递柜', '信报箱', '防盗门', '楼梯扶手', '无障碍通道',
]

FACILITY_ISSUES = [
    '坏了', '不够用', '好几天没人修', '被占了', '太旧了',
    '设计不合理', '存在安全隐患', '需要增加', '没人管', '早该换了',
]

ENV_ISSUES = [
    '工地天天施工，噪音太大了', '灰尘特别大，窗户都不敢开',
    '水质越来越差了', '空气有异味', '垃圾清运不及时',
    '晚上光污染严重', '河水发臭了', '绿化带被破坏了',
    '路边烧烤油烟扰民', '广场舞音响太吵了',
    '附近工厂排废气', '下水道反味', '河道漂浮垃圾',
    '渣土车半夜经过噪音大', '小区门口乱倒建筑垃圾',
]

SERVICE_AREAS = [
    '物业费', '公交车', '快递', '外卖', '社区医院', '幼儿园',
    '菜市场', '超市', '药店', '银行', '理发店', '维修',
    '保洁', '保安', '供暖', '供水', '供电', '燃气',
]

SERVICE_ISSUES = [
    '涨了服务反而更差', '早晚高峰根本挤不上去', '态度特别差',
    '办事效率太低', '经常找不到人', '收费不合理',
    '配套设施跟不上', '人手不够', '管理混乱', '一直没人处理',
    '投诉了好几次没用', '比以前差远了', '需要排队排很久',
]

CULTURE_ASPECTS = [
    '老建筑翻新后挺有味道', '文创园搞得很不错', '街区的历史感保留得很好',
    '博物馆免费开放了', '图书馆环境很好', '文化节办得有声有色',
    '老字号店铺值得打卡', '街头艺术越来越多了', '传统手艺人在做展示',
    '非遗活动很有意思', '滨江的文化墙更新了', '社区文化中心活动丰富',
    '城市书房24小时开放', '工业遗址改造得很成功',
]

CULTURE_EVENTS = [
    '灯光秀', '音乐节', '美食节', '庙会', '花展', '龙舟赛',
    '书画展', '摄影展', '读书会', '非遗展演', '民俗文化周',
    '诗歌朗诵', '街头艺人汇演', '文创市集',
]

EVENT_TYPES = [
    '要拆迁了', '业主在投诉物业', '在修路',
    '规划方案公示了', '要建新的地铁站', '旁边要盖商业综合体',
    '小区要改造了', '道路要拓宽', '要建新的学校',
    '公交线路要调整', '菜市场要搬迁', '公园要升级改造',
    '老旧小区加装电梯', '附近建了新的医院', '开发商跑路了',
    '准备建垃圾中转站', '要通天然气了', '要进行老旧管网改造',
]

EVENT_REACTIONS = [
    '大家怎么看', '有人了解情况吗', '希望早点落实', '这对我们有影响吗',
    '支持', '反对', '观望中', '已经签了同意书', '有没有业主群',
    '听说补偿方案出来了', '施工队已经进场了', '公示期到月底',
]

# ═══════════════════════════════════════════════════════════
# 城市相关内容 — 模板池 (每类 >= 10 种变体)
# ═══════════════════════════════════════════════════════════

FACILITY_TEMPLATES = [
    '{place}的{fc_item}{fc_issue}',
    '{place}{fc_item}{fc_issue}，反映了好几次了',
    '吐槽{place}的{fc_item}，{fc_issue}',
    '{place}附近{fc_item}{fc_issue}，出行很不方便',
    '{place}的{fc_item}终于{fc_issue}了',
    '住在{place}，{fc_item}{fc_issue}真是受够了',
    '{place}{fc_item}{fc_issue}，打12345有用吗',
    '对比隔壁{place2}，我们{place}的{fc_item}{fc_issue}',
    '{place}的{fc_item}如果能{fix}就好了',
    '{place}新装的{fc_item}挺好的，给社区点赞',
    '{community}的{fc_item}{fc_issue}，物业一直不解决',
    '每天路过{place}，{fc_item}{fc_issue}太危险了',
    '{place}{fc_item}终于要{fix}了，期待',
]

ENV_TEMPLATES = [
    '{place}那边{env_issue}',
    '住在{place}附近，{env_issue}，快受不了了',
    '{place}的环境问题：{env_issue}',
    '{place}{env_issue}，希望有关部门管管',
    '{place}最近{env_issue}，居民意见很大',
    '对比前几年，{place}{env_issue}越来越严重了',
    '{place}环境整治后好多了，但{env_issue}还是存在',
    '每次路过{place}都闻到{env_issue}',
    '{place}的{env_issue}问题，已经持续大半年了',
    '{community}的{env_issue}，谁能来管管',
    '{place}的{env_issue}影响了周边居民生活',
    '早起{place}散步，但{env_issue}体验很差',
    '{place}{env_issue}，大家有没有同感',
]

SERVICE_TEMPLATES = [
    '{place}的{sv_item}{sv_issue}',
    '{place}{sv_item}{sv_issue}，体验很不好',
    '吐槽一下{place}的{sv_item}服务',
    '{place}附近{sv_item}{sv_issue}，生活很不方便',
    '{place}的{sv_item}比以前好多了',
    '{community}的{sv_item}{sv_issue}，大家有没有同感',
    '在{place}{sv_item}{sv_issue}，效率真的低',
    '{place}的{sv_item}如果能改善一下就好了',
    '{place}新开了{sv_item}，方便多了',
    '{place}{sv_item}的{sv_issue}问题，已经反映多次',
    '住在{place}最不方便的就是{sv_item}{sv_issue}',
    '{place}和{place2}的{sv_item}对比，差距太大了',
    '{place}{sv_item}终于{fix}了，等了很久',
]

CULTURE_TEMPLATES = [
    '{place}的{culture}',
    '周末去{place}逛了逛，{culture}',
    '{place}的{culture}，推荐大家去看看',
    '原来{place}{culture}，今天才发现',
    '{place}{event}今年在{park}办得不错',
    '{place}的{culture}值得一逛',
    '宜昌{culture}，{place}是个好去处',
    '{district}{culture}，很有特色',
    '{place}的{culture}，周末带娃去了',
    '{park}的{event}今年规模很大',
    '{place}的{culture}，拍照超出片',
    '{season}的{place}，{culture}氛围很好',
    '{place}的{culture}，老宜昌人的记忆',
]

EVENT_TEMPLATES = [
    '{place}那边{event_type}',
    '听说{place}{event_type}，真的假的',
    '{place}{event_type}，{reaction}',
    '关于{place}{event_type}，有知情人士吗',
    '{place}{event_type}，大家{reaction}',
    '{community}{event_type}，不知道什么时候动工',
    '{place}{event_type}，对周边房价有影响吗',
    '{place}最近{event_type}，邻居们都在讨论',
    '关注{place}{event_type}的最新进展',
    '今天看到{place}{event_type}的通告',
    '{place}{event_type}，有业主群吗求拉',
    '{place}{event_type}，这次是真的要动了',
    '分享一下{place}{event_type}的最新消息',
]

# ═══════════════════════════════════════════════════════════
# 评论词汇池
# ═══════════════════════════════════════════════════════════

COMMENT_POSITIVE = [
    '确实不错', '学到了', '收藏了', '好美', '在哪里买的',
    '求链接', '已关注', '太好看了吧', '干货满满', '说得太对了',
    '同款get', '赞一个', '支持', '有道理', '感谢分享',
    '种草了', '马住', '好棒', '学到了学到了', '太实用了',
]

COMMENT_NEGATIVE = [
    '广告吧', 'fake', '不好用', '太贵了', '说实话一般',
    '又是广告', '没用的', '浪费钱', '别信', '软文吧',
    '亲测无效', '智商税', '别买', '踩过雷', '太假了',
]

COMMENT_NEUTRAL = [
    '路过', '打卡', '看看', '沙发', '前排',
    '已阅', '留名', '来了', '滴滴', '围观',
]

COMMENT_QUESTION = [
    '这个在哪里', '多少钱', '好用吗', '怎么联系', '还有吗',
    '楼主在哪', '求具体位置', '能私聊吗', '什么时候的事', '怎么参与',
]

COMMENT_USERS = [
    '宜昌小丸子', '三峡土著', '西陵区老张', '爱吃热干面', '路人甲',
    '夷陵小仙女', '江边的风', 'CBD遛弯群众', '磨基山爬山人', '小陈今天开心吗',
    '伍家岗一霸', '点军小透明', '宜昌热心市民', '东山脚下', '奶茶鉴定师',
    '不吃香菜', '熬夜协会会长', '葛洲坝退休工人', '三峡大学学生', '宜昌生活通',
]

# ═══════════════════════════════════════════════════════════
# 坐标生成: 10 簇高斯混合模型
# ═══════════════════════════════════════════════════════════

# 簇中心 (lon, lat) + 权重 + 标准差
COORD_CLUSTERS = [
    # (lon_center, lat_center, weight, lon_std, lat_std, label)
    (111.288, 30.710, 0.15, 0.006, 0.005, 'CBD商圈'),
    (111.305, 30.705, 0.12, 0.005, 0.004, '万达广场'),
    (111.315, 30.728, 0.15, 0.008, 0.007, '三峡大学'),
    (111.282, 30.698, 0.10, 0.007, 0.005, '滨江公园沿岸'),
    (111.290, 30.710, 0.10, 0.004, 0.003, '夷陵广场'),
    (111.312, 30.740, 0.08, 0.006, 0.005, '葛洲坝片区'),
    (111.296, 30.718, 0.08, 0.005, 0.004, '东山公园周边'),
    (111.300, 30.715, 0.07, 0.004, 0.004, '绿萝路/体育场路'),
    (111.330, 30.720, 0.08, 0.007, 0.005, '发展大道沿线'),
    (111.265, 30.690, 0.07, 0.010, 0.008, '点军/江南'),
]

# 叠加一层全局均匀噪声 (5% 的点是随机散布的，模拟零散用户)
UNIFORM_NOISE_RATIO = 0.05

# 坐标边界 (用于裁剪)
LON_MIN, LON_MAX = 111.25, 111.38
LAT_MIN, LAT_MAX = 30.68, 30.75


def generate_coordinates(n: int):
    """生成 n 个坐标点，使用高斯混合模型 + 边界裁剪"""
    cluster_centers = np.array([(c[0], c[1]) for c in COORD_CLUSTERS])
    cluster_weights = np.array([c[2] for c in COORD_CLUSTERS])
    cluster_stds = np.array([(c[3], c[4]) for c in COORD_CLUSTERS])
    cluster_weights = cluster_weights / cluster_weights.sum()

    # 分配每个点到某个簇
    n_uniform = int(n * UNIFORM_NOISE_RATIO)
    n_cluster = n - n_uniform
    assignments = np.random.choice(len(COORD_CLUSTERS), size=n_cluster, p=cluster_weights)

    lons = np.zeros(n)
    lats = np.zeros(n)

    # 生成聚类坐标
    for i, cluster_idx in enumerate(assignments):
        lons[i] = np.random.normal(cluster_centers[cluster_idx, 0], cluster_stds[cluster_idx, 0])
        lats[i] = np.random.normal(cluster_centers[cluster_idx, 1], cluster_stds[cluster_idx, 1])

    # 生成均匀随机坐标
    if n_uniform > 0:
        lons[n_cluster:] = np.random.uniform(LON_MIN, LON_MAX, n_uniform)
        lats[n_cluster:] = np.random.uniform(LAT_MIN, LAT_MAX, n_uniform)

    # 裁剪到边界内
    lons = np.clip(lons, LON_MIN, LON_MAX)
    lats = np.clip(lats, LAT_MIN, LAT_MAX)

    return lons, lats


# ═══════════════════════════════════════════════════════════
# 辅助生成函数
# ═══════════════════════════════════════════════════════════

def _pick(lst):
    """从列表中随机选一个元素"""
    return lst[random.randint(0, len(lst) - 1)]


def _pick_n(lst, n):
    """从列表中随机选 n 个不重复元素"""
    return random.sample(lst, min(n, len(lst)))


def _maybe_emoji(emoji_list, prob=0.6):
    """以一定概率返回 emoji，否则返回空字符串"""
    return _pick(emoji_list) if random.random() < prob else ''


def _fmt_wechat():
    """生成随机微信号"""
    prefixes = ['wx', 'vx', 'V', 'WX', '']
    return f"{_pick(prefixes)}{random.randint(10000, 99999999)}"


def generate_publish_time() -> str:
    """生成过去3个月内随机时间"""
    sec_offset = random.randint(0, PUBLISH_RANGE_SEC)
    dt = PUBLISH_START + timedelta(seconds=sec_offset)
    return dt.strftime('%Y-%m-%dT%H:%M:%S')


def generate_like_comment_counts():
    """
    生成 like_count 和 comment_count (幂律分布)
    大部分帖子 0-50 赞，少数爆款 500-50000
    """
    # 使用指数分布生成赞数
    # 70% 0-20 赞，20% 20-200 赞，8% 200-2000 赞，2% 2000-50000 赞
    r = random.random()
    if r < 0.70:
        likes = int(np.random.exponential(8) + random.randint(0, 5))
    elif r < 0.90:
        likes = int(np.random.exponential(60) + 20)
    elif r < 0.98:
        likes = int(np.random.exponential(500) + 200)
    else:
        likes = int(np.random.exponential(8000) + 2000)

    likes = max(0, min(likes, 100000))

    # 评论数与赞数正相关 + 噪声
    comment_ratio = random.uniform(0.005, 0.08)
    comments = int(likes * comment_ratio + random.randint(0, 5))
    comments = max(0, min(comments, 5000))

    return likes, comments


def generate_tags(source: str, category: str) -> str:
    """根据平台生成合适的 tags"""
    if source == 'xiaohongshu':
        tag_pools = {
            'beauty': ['护肤', '美妆', '好物分享', '彩妆', '变美', '护肤心得', '空瓶记'],
            'fashion': ['穿搭', 'OOTD', '日常穿搭', '时尚', '显瘦穿搭', '今日穿搭'],
            'emotion': ['情感', '心情', '深夜话题', '情绪', '治愈'],
            'daily': ['日常', '生活', '记录生活', 'plog', '碎碎念'],
            'pet': ['宠物', '萌宠', '吸猫', '撸狗', '宠物日常'],
            'joke': ['搞笑', '沙雕', '每日一笑', '快乐源泉'],
            'ad': ['好物推荐', '种草', '福利'],
            'study': ['学习', '考研', '考公', '备考', '上岸'],
            'other': ['分享', '日常', '随手拍'],
            'facility': ['城市生活', '宜昌', '社区', '民生'],
            'environment': ['宜昌', '环境', '生活', '城市'],
            'service': ['宜昌', '生活服务', '便民', '社区'],
            'culture': ['宜昌', '文化', '打卡', '城市记忆'],
            'event': ['宜昌', '城建', '规划', '新鲜事'],
        }
        tags = tag_pools.get(category, ['分享', '日常'])
        n_tags = random.randint(1, 4)
        return '|'.join(_pick_n(tags, n_tags))

    elif source == 'weibo':
        tag_pools = {
            'beauty': ['美妆推荐', '护肤心得', '好物安利', '化妆教程'],
            'fashion': ['穿搭分享', '今日穿搭', 'ootd', '时尚潮流'],
            'emotion': ['情感语录', '心情日记', '深夜感慨', '情绪树洞'],
            'daily': ['日常生活', '碎碎念', '记录生活', '日常分享'],
            'pet': ['萌宠日常', '宠物', '猫猫狗狗', '云吸猫'],
            'joke': ['搞笑日常', '段子', '今日笑点', '哈哈哈'],
            'ad': ['好物推荐', '优惠活动'],
            'study': ['学习打卡', '考研', '备考日常', '上岸'],
            'other': ['分享', '日常'],
            'facility': ['宜昌身边事', '城市设施', '民生关注'],
            'environment': ['宜昌环境', '城市生活', '身边事'],
            'service': ['宜昌服务', '生活便利', '民生'],
            'culture': ['宜昌文化', '城市记忆', '打卡宜昌'],
            'event': ['宜昌新闻', '城建动态', '民生实事'],
        }
        tags = tag_pools.get(category, ['日常'])
        n_tags = random.randint(1, 3)
        return '|'.join(_pick_n(tags, n_tags))

    elif source == 'dianping':
        tag_pools = {
            'beauty': ['美容SPA', '皮肤管理', '化妆品'],
            'fashion': ['服装', '配饰', '买手店'],
            'emotion': ['心情'],
            'daily': ['生活', '日常'],
            'pet': ['宠物店', '宠物医院'],
            'joke': ['休闲娱乐'],
            'ad': ['优惠', '促销'],
            'study': ['书店', '图书馆', '自习室'],
            'other': ['生活'],
            'facility': ['公共设施', '基础设施'],
            'environment': ['环境', '周边'],
            'service': ['服务', '生活服务', '物业服务'],
            'culture': ['文化场馆', '展览', '活动'],
            'event': ['城建', '规划'],
        }
        tags = tag_pools.get(category, ['生活'])
        n_tags = random.randint(1, 2)
        return '|'.join(_pick_n(tags, n_tags))

    elif source == 'meituan':
        tag_pools = {
            'beauty': ['美容美体', '美发', '美甲'],
            'fashion': ['服装', '购物'],
            'daily': ['生活', '日常消费'],
            'pet': ['宠物', '宠物服务'],
            'joke': ['娱乐', '休闲'],
            'ad': ['优惠', '团购'],
            'study': ['教育', '培训'],
            'other': ['生活服务'],
            'facility': ['基础设施'],
            'environment': ['周边环境'],
            'service': ['生活服务', '社区服务', '物业服务'],
            'culture': ['休闲娱乐', '文化'],
            'event': ['本地新闻'],
        }
        tags = tag_pools.get(category, ['生活服务'])
        n_tags = random.randint(1, 2)
        return '|'.join(_pick_n(tags, n_tags))

    else:  # su12345
        tag_pools = {
            'facility': ['市政设施', '公共设施', '道路设施', '照明'],
            'environment': ['环境污染', '噪音扰民', '市容环境', '河道管理'],
            'service': ['物业服务', '公共交通', '供水供电', '社区服务'],
            'culture': ['文化设施', '公共空间'],
            'event': ['城市建设', '规划公示', '拆迁安置', '道路施工'],
        }
        tags = tag_pools.get(category, ['其他'])
        n_tags = random.randint(1, 2)
        return '|'.join(_pick_n(tags, n_tags))


def generate_url(source: str) -> str:
    """生成平台逼真URL"""
    if source == 'xiaohongshu':
        hex_id = ''.join(random.choices('0123456789abcdef', k=24))
        return f'https://www.xiaohongshu.com/explore/{hex_id}'
    elif source == 'weibo':
        user_id = random.randint(1000000000, 9999999999)
        post_id = ''.join(random.choices('0123456789abcdef', k=8))
        return f'https://weibo.com/{user_id}/{post_id}'
    elif source == 'dianping':
        post_id = random.randint(10000000, 99999999)
        return f'https://www.dianping.com/review/{post_id}'
    elif source == 'meituan':
        post_id = random.randint(100000000, 999999999)
        return f'https://www.meituan.com/meishi/{post_id}/'
    else:  # su12345
        complaint_id = f'S{datetime.now().year}{random.randint(100000, 999999)}'
        return f'https://su12345.yichang.gov.cn/complaint/{complaint_id}'


def generate_comments() -> str:
    """50% 为空，50% 有 1-2 条简短评论"""
    if random.random() < 0.5:
        return ''

    n_comments = 1 if random.random() < 0.7 else 2
    comments = []
    for _ in range(n_comments):
        user = _pick(COMMENT_USERS)
        pool = random.choice([COMMENT_POSITIVE, COMMENT_NEUTRAL, COMMENT_QUESTION, COMMENT_NEGATIVE])
        content = _pick(pool)
        comments.append(f'{user}: {content}')

    return ' | '.join(comments)


# ═══════════════════════════════════════════════════════════
# 内容生成引擎
# ═══════════════════════════════════════════════════════════

def generate_beauty_content():
    """生成美妆类内容"""
    tmpl = _pick(BEAUTY_TEMPLATES)
    return tmpl.format(
        brand=_pick(BEAUTY_BRANDS),
        brand1=_pick(BEAUTY_BRANDS),
        brand2=_pick(BEAUTY_BRANDS),
        product=_pick(BEAUTY_PRODUCTS),
        product1=_pick(BEAUTY_PRODUCTS),
        product2=_pick(BEAUTY_PRODUCTS),
        skin=_pick(SKIN_TYPES),
        emoji=_maybe_emoji(BEAUTY_EMOJI, 0.7),
    )


def generate_fashion_content():
    """生成穿搭类内容"""
    tmpl = _pick(FASHION_TEMPLATES)
    return tmpl.format(
        item=_pick(FASHION_ITEMS),
        item1=_pick(FASHION_ITEMS),
        item2=_pick(FASHION_ITEMS),
        season=_pick(SEASONS),
        color=_pick(FASHION_COLORS),
        emoji=_maybe_emoji(FASHION_EMOJI, 0.7),
    )


def generate_emotion_content():
    """生成情感类内容"""
    tmpl = _pick(EMOTION_TEMPLATES)
    return tmpl.format(
        time_word=_pick(EMOTION_TIME_WORDS),
        person=_pick(EMOTION_WORDS),
        event=_pick(EMOTION_EVENTS),
        action=_pick(EMOTION_ACTIONS),
        emoji=_maybe_emoji(EMOTION_EMOJI, 0.5),
    )


def generate_daily_content():
    """生成日常生活类内容"""
    tmpl = _pick(DAILY_TEMPLATES)
    topics = _pick_n(DAILY_TOPICS, 3)
    return tmpl.format(
        topic=topics[0],
        topic1=topics[0],
        topic2=topics[1] if len(topics) > 1 else topics[0],
        topic3=topics[2] if len(topics) > 2 else topics[0],
        day=random.randint(1, 365),
        emoji=_maybe_emoji(DAILY_EMOJI, 0.5),
    )


def generate_pet_content():
    """生成宠物类内容"""
    tmpl = _pick(PET_TEMPLATES)
    return tmpl.format(
        pet=_pick(PET_TYPES),
        pet2=_pick(PET_TYPES),
        action=_pick(PET_ACTIONS),
        emoji=_maybe_emoji(PET_EMOJI, 0.8),
    )


def generate_joke_content():
    """生成搞笑类内容"""
    tmpl = _pick(JOKE_TEMPLATES)
    return tmpl.format(
        joke=_pick(JOKE_TEMPLATES_SIMPLE),
        emoji=_maybe_emoji(JOKE_EMOJI, 0.5),
    )


def generate_ad_content():
    """生成广告类内容"""
    tmpl = _pick(AD_TEMPLATES)
    return tmpl.format(
        product=_pick(AD_PRODUCTS),
        job=_pick(AD_JOBS),
        amount=_pick(AD_AMOUNTS),
        wechat=_fmt_wechat(),
    )


def generate_study_content():
    """生成学习考试类内容"""
    tmpl = _pick(STUDY_TEMPLATES)
    return tmpl.format(
        study=_pick(STUDY_TOPICS),
        action=_pick(STUDY_ACTIONS),
        action1=_pick(STUDY_ACTIONS),
        action2=_pick(STUDY_ACTIONS),
        action3=_pick(STUDY_ACTIONS),
        day=random.randint(1, 200),
        count=random.randint(10, 180),
        score=random.randint(280, 450) if random.random() < 0.5 else random.randint(60, 100),
        emoji=_maybe_emoji(STUDY_EMOJI, 0.6),
    )


def generate_other_content():
    """生成其他类内容"""
    tmpl = _pick(OTHER_TEMPLATES)
    return tmpl.format(
        topic=_pick(OTHER_TOPICS),
        emoji=_maybe_emoji(DAILY_EMOJI, 0.4),
    )


# ── 城市相关内容生成 ──

def generate_facility_content():
    """生成设施类内容"""
    tmpl = _pick(FACILITY_TEMPLATES)
    return tmpl.format(
        place=_pick(ALL_PLACES + PLACE_DETAIL),
        place2=_pick(ALL_PLACES),
        community=_pick(COMMUNITY_NAMES),
        fc_item=_pick(FACILITY_ITEMS),
        fc_issue=_pick(FACILITY_ISSUES),
        fix=_pick(['修好', '改善', '更新', '改造', '升级', '增加', '换新']),
    )


def generate_environment_content():
    """生成环境类内容"""
    tmpl = _pick(ENV_TEMPLATES)
    return tmpl.format(
        place=_pick(ALL_PLACES + PLACE_DETAIL),
        community=_pick(COMMUNITY_NAMES),
        env_issue=_pick(ENV_ISSUES),
    )


def generate_service_content():
    """生成服务类内容"""
    tmpl = _pick(SERVICE_TEMPLATES)
    return tmpl.format(
        place=_pick(ALL_PLACES + PLACE_DETAIL),
        place2=_pick(ALL_PLACES),
        community=_pick(COMMUNITY_NAMES),
        sv_item=_pick(SERVICE_AREAS),
        sv_issue=_pick(SERVICE_ISSUES),
        fix=_pick(['改善', '提升', '解决', '优化', '调整', '加强']),
    )


def generate_culture_content():
    """生成文化类内容"""
    tmpl = _pick(CULTURE_TEMPLATES)
    return tmpl.format(
        place=_pick(ALL_PLACES),
        district=_pick(YICHANG_DISTRICTS),
        park=_pick(YICHANG_PARKS),
        culture=_pick(CULTURE_ASPECTS),
        event=_pick(CULTURE_EVENTS),
        season=_pick(['春天', '夏天', '秋天', '冬天']),
    )


def generate_event_content():
    """生成事件类内容"""
    tmpl = _pick(EVENT_TEMPLATES)
    return tmpl.format(
        place=_pick(ALL_PLACES + PLACE_DETAIL),
        community=_pick(COMMUNITY_NAMES),
        event_type=_pick(EVENT_TYPES),
        reaction=_pick(EVENT_REACTIONS),
    )


# 生成函数映射
IRRELEVANT_GENERATORS = {
    'beauty': generate_beauty_content,
    'fashion': generate_fashion_content,
    'emotion': generate_emotion_content,
    'daily': generate_daily_content,
    'pet': generate_pet_content,
    'joke': generate_joke_content,
    'ad': generate_ad_content,
    'study': generate_study_content,
    'other': generate_other_content,
}

CITY_GENERATORS = {
    'facility': generate_facility_content,
    'environment': generate_environment_content,
    'service': generate_service_content,
    'culture': generate_culture_content,
    'event': generate_event_content,
}


def generate_title(source: str, text: str, category: str) -> str:
    """根据平台生成标题"""
    if source in ('dianping', 'meituan'):
        # 大众点评/美团约 80% 无标题
        if random.random() < 0.8:
            return ''
        else:
            return text[:30] if len(text) > 30 else text

    if source == 'su12345':
        # 12345 用简短摘要
        return text[:40] if len(text) > 40 else text

    # 小红书/微博
    if random.random() < 0.85:
        # 标题 = 正文 (或前50字)
        return text[:50] if len(text) > 50 else text
    else:
        # 独立简短标题
        return text[:25] if len(text) > 25 else text


# ═══════════════════════════════════════════════════════════
# 主生成流程
# ═══════════════════════════════════════════════════════════

def main():
    _safe_print('=' * 60)
    _safe_print('[LOAD] 模拟数据生成脚本 v1.0')
    _safe_print(f'[LOAD] 目标: 生成 {TOTAL_COUNT:,} 条 L0 模拟数据')
    _safe_print(f'[LOAD] 随机种子: 42')
    _safe_print('=' * 60)

    # ── 1. 计算各类别数量 ──
    # 无关内容 90% = 90000, 城市相关 10% = 10000
    n_irrelevant = int(TOTAL_COUNT * 0.90)
    n_city = TOTAL_COUNT - n_irrelevant

    # 无关内容子类分布
    irrelevant_dist = {
        'beauty': 0.20, 'fashion': 0.15, 'emotion': 0.15,
        'daily': 0.15, 'pet': 0.08, 'joke': 0.07,
        'ad': 0.05, 'study': 0.05, 'other': 0.10,
    }
    # 城市相关内容子类分布
    city_dist = {
        'facility': 0.20, 'environment': 0.25, 'service': 0.20,
        'culture': 0.20, 'event': 0.15,
    }

    # 平台分布
    platform_dist = {
        'xiaohongshu': 0.40, 'weibo': 0.30, 'dianping': 0.20,
        'meituan': 0.05, 'su12345': 0.05,
    }

    _safe_print('[CALC] 内容配比计算...')
    irr_counts = {k: int(v * n_irrelevant) for k, v in irrelevant_dist.items()}
    # 修正舍入误差
    irr_diff = n_irrelevant - sum(irr_counts.values())
    irr_counts['other'] += irr_diff

    city_counts = {k: int(v * n_city) for k, v in city_dist.items()}
    city_diff = n_city - sum(city_counts.values())
    city_counts['environment'] += city_diff

    _safe_print(f'  无关内容: {sum(irr_counts.values()):,} 条')
    for k, v in irr_counts.items():
        _safe_print(f'    {k}: {v:,}')

    _safe_print(f'  城市相关: {sum(city_counts.values()):,} 条')
    for k, v in city_counts.items():
        _safe_print(f'    {k}: {v:,}')

    # ── 2. 构建类别+平台序列 ──
    _safe_print('[GEN] 构建类别-平台分配序列...')

    # 为每条数据预分配 (category, is_city, platform)
    # 无关内容
    irr_categories = []
    for cat, count in irr_counts.items():
        irr_categories.extend([cat] * count)
    random.shuffle(irr_categories)

    # 城市相关
    city_categories = []
    for cat, count in city_counts.items():
        city_categories.extend([cat] * count)
    random.shuffle(city_categories)

    # 合并
    all_categories = irr_categories + city_categories
    # 最终全局打乱
    random.shuffle(all_categories)

    # 平台分配 (平台与内容类型独立随机)
    platforms = random.choices(
        list(platform_dist.keys()),
        weights=list(platform_dist.values()),
        k=TOTAL_COUNT,
    )

    # ── 3. 生成坐标 ──
    _safe_print('[GEN] 生成坐标 (高斯混合模型 + 均匀噪声)...')
    lons, lats = generate_coordinates(TOTAL_COUNT)

    # ── 4. 逐条生成内容 ──
    _safe_print('[GEN] 开始生成内容数据...')

    crawl_time_str = CRAWL_TIME.strftime('%Y-%m-%dT%H:%M:%S.%f')

    # 预分配列表
    sources = [None] * TOTAL_COUNT
    urls = [None] * TOTAL_COUNT
    titles = [None] * TOTAL_COUNT
    texts = [None] * TOTAL_COUNT
    tags_list = [None] * TOTAL_COUNT
    like_counts = [0] * TOTAL_COUNT
    comment_counts = [0] * TOTAL_COUNT
    publish_times = [None] * TOTAL_COUNT
    comments_list = [None] * TOTAL_COUNT

    # 进度汇报间隔
    report_interval = 10000

    for i in range(TOTAL_COUNT):
        cat = all_categories[i]
        platform = platforms[i]

        # 判断是否城市相关
        is_city = cat in CITY_GENERATORS

        # 生成正文
        if is_city:
            text = CITY_GENERATORS[cat]()
        else:
            text = IRRELEVANT_GENERATORS[cat]()

        # 生成其他字段
        title = generate_title(platform, text, cat)
        url = generate_url(platform)
        likes, comments_n = generate_like_comment_counts()
        publish_time = generate_publish_time()
        tags = generate_tags(platform, cat)
        comments_text = generate_comments()

        # 存储
        sources[i] = platform
        urls[i] = url
        titles[i] = title
        texts[i] = text
        tags_list[i] = tags
        like_counts[i] = likes
        comment_counts[i] = comments_n
        publish_times[i] = publish_time
        comments_list[i] = comments_text

        if (i + 1) % report_interval == 0:
            _safe_print(f'  [PROGRESS] 已生成 {i + 1:,} / {TOTAL_COUNT:,} 条...')

    _safe_print(f'  [OK] 内容生成完成: {TOTAL_COUNT:,} 条')

    # ── 5. 构建 DataFrame 并写出 CSV ──
    _safe_print('[EXPORT] 构建 DataFrame 并写出 CSV...')

    df = pd.DataFrame({
        'source': sources,
        'url': urls,
        'crawl_time': crawl_time_str,
        'title': titles,
        'text': texts,
        'lon_gcj02': np.round(lons, 6),
        'lat_gcj02': np.round(lats, 6),
        'area': '规划范围',
        'tags': tags_list,
        'like_count': like_counts,
        'comment_count': comment_counts,
        'publish_time': publish_times,
        'comments': comments_list,
    })

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8', quoting=1)  # QUOTE_ALL
    file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    _safe_print(f'[OK] 已写出: {OUTPUT_FILE}')
    _safe_print(f'[OK] 文件大小: {file_size_mb:.1f} MB')

    # ── 6. 打印统计信息 ──
    _safe_print('')
    _safe_print('=' * 60)
    _safe_print('  生成统计')
    _safe_print('=' * 60)
    _safe_print(f'  总条数:            {TOTAL_COUNT:>8,}')
    _safe_print(f'  无关内容:          {n_irrelevant:>8,}  ({n_irrelevant/TOTAL_COUNT*100:.1f}%)')
    _safe_print(f'  城市相关:          {n_city:>8,}  ({n_city/TOTAL_COUNT*100:.1f}%)')
    _safe_print('')

    _safe_print('  平台分布:')
    for platform in ['xiaohongshu', 'weibo', 'dianping', 'meituan', 'su12345']:
        cnt = sources.count(platform)
        _safe_print(f'    {platform:>14s}: {cnt:>8,}  ({cnt/TOTAL_COUNT*100:.1f}%)')

    _safe_print('')
    _safe_print('  无关内容子类:')
    for cat in ['beauty', 'fashion', 'emotion', 'daily', 'pet', 'joke', 'ad', 'study', 'other']:
        cnt = all_categories.count(cat)
        _safe_print(f'    {cat:>10s}: {cnt:>8,}  ({cnt/TOTAL_COUNT*100:.1f}%)')

    _safe_print('')
    _safe_print('  城市相关内容子类:')
    for cat in ['facility', 'environment', 'service', 'culture', 'event']:
        cnt = all_categories.count(cat)
        _safe_print(f'    {cat:>10s}: {cnt:>8,}  ({cnt/TOTAL_COUNT*100:.1f}%)')

    _safe_print('')
    _safe_print('  坐标范围:')
    _safe_print(f'    lon_gcj02: [{lons.min():.4f}, {lons.max():.4f}]')
    _safe_print(f'    lat_gcj02: [{lats.min():.4f}, {lats.max():.4f}]')

    _safe_print('')
    _safe_print('  like_count 分布:')
    _safe_print(f'    min={np.min(like_counts):,}, max={np.max(like_counts):,}')
    _safe_print(f'    median={np.median(like_counts):.0f}, mean={np.mean(like_counts):.0f}')
    pct_0_20 = sum(1 for lc in like_counts if lc <= 20) / TOTAL_COUNT * 100
    pct_20_200 = sum(1 for lc in like_counts if 20 < lc <= 200) / TOTAL_COUNT * 100
    pct_200_2000 = sum(1 for lc in like_counts if 200 < lc <= 2000) / TOTAL_COUNT * 100
    pct_2000_plus = sum(1 for lc in like_counts if lc > 2000) / TOTAL_COUNT * 100
    _safe_print(f'    0-20: {pct_0_20:.1f}%, 20-200: {pct_20_200:.1f}%, 200-2000: {pct_200_2000:.1f}%, >2000: {pct_2000_plus:.1f}%')

    _safe_print('')
    _safe_print(f'  comments 非空比例: {sum(1 for c in comments_list if c) / TOTAL_COUNT * 100:.1f}%')

    _safe_print('')
    _safe_print('=' * 60)
    _safe_print('[OK] 生成完毕!')
    _safe_print(f'[OK] 输出文件: {OUTPUT_FILE}')
    _safe_print('=' * 60)


if __name__ == '__main__':
    main()
