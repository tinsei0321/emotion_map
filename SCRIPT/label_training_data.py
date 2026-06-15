"""
标注训练数据脚本 v1.0 — Label Training Data
=============================================
从 100k 模拟数据中分层采样 500 条，用 DeepSeek LLM 精确标注，
作为 Embedding 分类器训练的"金标准"。

采样策略:
  - 城市相关 (五要素各 ~80 条) = 400 条
  - 无关内容 (6 类各 ~15-20 条) = 100 条
  - 使用 tags 列辅助分层，固定 seed=42

标注引擎:
  - 复用 SCRIPT.relevance_filter 中的 llm_classify() 和 LLM_SYSTEM_PROMPT
  - 逐条调用 DeepSeek API，支持断点续传和错误重试

输出: DATA/processed/labeled_training_500.csv

用法:
    $env:DEEPSEEK_API_KEY = "sk-xxx"
    py SCRIPT/label_training_data.py

编码铁律:
    - 所有 print() 使用 safe_print()
    - 无 emoji，仅 ASCII 标记 [OK]/[WARN]/[ERR]/[LOAD]
    - API Key 从环境变量读取
"""

import os
import sys
import json
import random
import time
from typing import Optional

import numpy as np
import pandas as pd
from core.utils import safe_print

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 从 relevance_filter 复用核心函数 ──
try:
    from SCRIPT.relevance_filter import (
        llm_classify,
        safe_print,
        _build_text_for_classification,
        DEEPSEEK_MODEL,
    )
except ImportError:
    def safe_print(*args, **kwargs):
        print(*args, **kwargs)

# ═══════════════════════════════════════════════════════════
# 常量配置
# ═══════════════════════════════════════════════════════════

# 输入文件
INPUT_CSV = os.path.join('DATA', 'raw', 'simulated_20260613_100k_raw.csv')

# 输出文件
OUTPUT_CSV = os.path.join('DATA', 'processed', 'labeled_training_500.csv')

# 采样配置
TOTAL_SAMPLES = 500
SEED = 42

# 城市五要素 — 目标采样数
URBAN_ELEMENTS = ['设施', '环境', '服务', '文化', '事件']
URBAN_PER_ELEMENT = 80

# 无关内容 — 目标采样数
IRRELEVANT_CATEGORIES = ['美妆', '穿搭', '情感', '宠物', '游戏', '广告']
IRRELEVANT_PER_CATEGORY = [17, 17, 17, 17, 16, 16]  # 总和 = 100

# ═══════════════════════════════════════════════════════════
# 标签→类别映射 (基于 generate_test_data.py 中的 tag_pools)
# ═══════════════════════════════════════════════════════════

# ── 无关内容标签关键词 (按优先级排列，优先匹配) ──
IRRELEVANT_TAG_MAP = {
    '美妆': [
        '护肤', '美妆', '彩妆', '变美', '护肤心得', '空瓶记',
        '化妆品', '皮肤管理', '美容SPA', '美容美体', '美发', '美甲',
        '美妆推荐', '好物安利', '化妆教程', '好物分享',
    ],
    '穿搭': [
        '穿搭', 'OOTD', 'ootd', '时尚', '今日穿搭', '日常穿搭',
        '显瘦穿搭', '穿搭分享', '时尚潮流', '服装', '配饰', '买手店', '购物',
    ],
    '情感': [
        '情感', '心情', '深夜话题', '情绪', '治愈',
        '情感语录', '心情日记', '深夜感慨', '情绪树洞',
    ],
    '宠物': [
        '宠物', '萌宠', '吸猫', '撸狗', '宠物日常',
        '萌宠日常', '猫猫狗狗', '云吸猫', '宠物店', '宠物医院', '宠物服务',
    ],
    '游戏': [
        '游戏', '王者荣耀', '吃鸡', '原神', '崩坏', '星穹铁道',
        'LOL', '上分', '排位', '开黑', '氪金', '抽卡',
        '王者', '原神启动', '崩铁', '阴阳师', '第五人格', '明日方舟', '碧蓝航线',
        '游戏日常',
    ],
    '广告': [
        '好物推荐', '种草', '福利', '优惠活动', '优惠', '促销', '团购',
        '招募', '合伙人', '创业', '代理', '兼职',
    ],
}

# ── 城市五要素标签关键词 ──
URBAN_TAG_MAP = {
    '设施': [
        '城市设施', '公共设施', '基础设施', '市政设施', '道路设施',
        '照明', '设施', '民生关注', '城市生活',
    ],
    '环境': [
        '环境', '周边环境', '环境污染', '噪音扰民', '市容环境',
        '河道管理', '宜昌环境', '城市生活', '身边事',
    ],
    '服务': [
        '生活服务', '便民', '社区服务', '物业服务', '公共交通',
        '供水供电', '宜昌服务', '生活便利', '民生',
    ],
    '文化': [
        '文化', '城市记忆', '打卡', '展览', '活动',
        '文化场馆', '公共空间', '宜昌文化', '打卡宜昌', '文化设施',
        '休闲娱乐',
    ],
    '事件': [
        '城建', '规划', '新鲜事', '城建动态', '民生实事',
        '本地新闻', '城市建设', '规划公示', '拆迁安置', '道路施工',
        '宜昌新闻',
    ],
}

# ── 标题/正文辅助关键词 — 当 tags 无法确定时使用 ──
TEXT_KEYWORDS_URBAN = {
    '设施': ['路灯', '停车位', '电梯', '消防', '监控', '门禁', '绿化带',
             '健身器材', '垃圾桶', '下水道', '充电桩', '公交站', '公共厕所',
             '快递柜', '斑马线', '红绿灯', '护栏', '减速带'],
    '环境': ['噪音', '灰尘', '空气', '水质', '垃圾清运', '光污染', '河水',
             '烧烤油烟', '广场舞', '废气', '下水道反味', '建筑垃圾', '渣土车'],
    '服务': ['物业费', '公交车', '快递', '外卖', '社区医院', '幼儿园',
             '菜市场', '超市', '药店', '银行', '维修', '保洁', '保安',
             '供暖', '供水', '供电', '燃气'],
    '文化': ['老建筑', '文创', '街区', '博物馆', '图书馆', '文化节',
             '老字号', '街头艺术', '传统手艺', '非遗', '文化墙', '书房',
             '工业遗址', '灯光秀', '音乐节', '美食节', '庙会', '花展',
             '龙舟赛', '书画展', '摄影展', '读书会', '民俗', '市集'],
    '事件': ['拆迁', '投诉', '修路', '规划方案', '地铁站', '商业综合体',
             '小区改造', '道路拓宽', '加装电梯', '线路调整', '搬迁',
             '升级改造', '垃圾中转站', '通天然气', '管网改造'],
}

TEXT_KEYWORDS_IRRELEVANT = {
    '美妆': ['粉底', '口红', '眼影', '面膜', '精华', '防晒', '卸妆',
             '眉笔', '腮红', '睫毛', '气垫', '隔离霜', '洗面奶', '爽肤水',
             '乳液', '眼霜', '护肤', '品牌', '色号'],
    '穿搭': ['卫衣', '牛仔裤', '连衣裙', '西装', '风衣', '衬衫', '阔腿裤',
             '裙子', '毛衣', '羽绒服', '帽子', '运动鞋', '靴子', '帆布鞋'],
    '情感': ['初恋', '暗恋', '前任', '分手', '相亲', '喜欢', '想念',
             '难过', '孤独', '失眠', '崩溃'],
    '宠物': ['猫', '狗', '猫咪', '狗狗', '柴犬', '柯基', '金毛', '布偶',
             '英短', '泰迪', '主子', '遛狗'],
    '游戏': ['王者', '吃鸡', '原神', '排位', '开黑', '上分', '副本', '公会',
             'SSR', '抽到'],
    '广告': ['加微信', '扫码', '招募', '限时优惠', '日结', '代理价',
             '免费领取', '厂家直销', '一件代发'],
}


# ═══════════════════════════════════════════════════════════
# 类别分类函数
# ═══════════════════════════════════════════════════════════

def _classify_row_by_tags(tags_str: str) -> Optional[str]:
    """
    根据 tags 字符串将行分类到具体类别。

    优先匹配无关内容标签（更独特），再匹配城市标签。
    返回类别名称，或 None 表示无法确定。
    """
    if not isinstance(tags_str, str) or not tags_str.strip():
        return None

    tags_lower = tags_str.lower()
    tags_parts = [t.strip() for t in tags_str.split('|')]

    # ── 1. 优先检查无关内容标签 ──
    for category, keywords in IRRELEVANT_TAG_MAP.items():
        for kw in keywords:
            kw_lower = kw.lower()
            # 精确匹配标签片段 或 子串匹配整个 tags 字符串
            if any(kw_lower == part.lower() for part in tags_parts):
                return category
            if kw_lower in tags_lower:
                return category

    # ── 2. 检查城市五要素标签 ──
    for category, keywords in URBAN_TAG_MAP.items():
        for kw in keywords:
            kw_lower = kw.lower()
            if any(kw_lower == part.lower() for part in tags_parts):
                return category
            if kw_lower in tags_lower:
                return category

    return None


def _classify_row_by_text(row: pd.Series) -> Optional[str]:
    """
    当 tags 无法确定类别时，通过正文关键词辅助分类。
    """
    text = _build_text_for_classification(row)
    if not text:
        return None

    text_lower = text.lower()

    # ── 先检查无关内容关键词 ──
    for category, keywords in TEXT_KEYWORDS_IRRELEVANT.items():
        for kw in keywords:
            if kw in text_lower:
                return category

    # ── 再检查城市关键词 ──
    for category, keywords in TEXT_KEYWORDS_URBAN.items():
        for kw in keywords:
            if kw in text_lower:
                return category

    return None


# ═══════════════════════════════════════════════════════════
# 1. 智能采样
# ═══════════════════════════════════════════════════════════

def sample_for_labeling(df: pd.DataFrame, n: int = TOTAL_SAMPLES) -> pd.DataFrame:
    """
    分层采样：确保各内容类型都有代表。

    策略:
      1. 用 tags 列将每条数据分类到具体类别
      2. 无法从 tags 确定的，用正文关键词辅助判断
      3. 仍无法确定的归入 '其他' 池
      4. 从每个目标类别中按配额采样
      5. 若某类别不足，从其他池中补充

    Args:
        df: 原始 DataFrame
        n: 总采样数 (默认 500)

    Returns:
        采样后的 DataFrame (保留原始索引作为 id_e)
    """
    safe_print(f'[LOAD] 开始分层采样，目标 {n} 条 ...')
    safe_print(f'  输入数据: {len(df)} 条')

    random.seed(SEED)
    np.random.seed(SEED)

    df = df.copy()

    # ── Step 1: 分类每条数据 ──
    category_col = []
    for idx in df.index:
        tags = df.loc[idx, 'tags']
        cat = _classify_row_by_tags(tags)
        if cat is None:
            cat = _classify_row_by_text(df.loc[idx])
        if cat is None:
            cat = '其他'
        category_col.append(cat)

    df['_sample_category'] = category_col

    # 打印分类分布
    cat_counts = df['_sample_category'].value_counts()
    safe_print(f'\n  标签分类分布:')
    for cat, count in cat_counts.items():
        safe_print(f'    {cat}: {count}')

    # ── Step 2: 分层采样 ──
    sampled_dfs = []
    sample_summary = {}

    # 城市五要素
    for element in URBAN_ELEMENTS:
        pool = df[df['_sample_category'] == element]
        available = len(pool)
        target = URBAN_PER_ELEMENT
        actual = min(available, target)
        if actual > 0:
            sampled = pool.sample(n=actual, random_state=SEED)
            sampled_dfs.append(sampled)
        sample_summary[element] = {'target': target, 'available': available, 'sampled': actual}

    # 无关内容
    for i, category in enumerate(IRRELEVANT_CATEGORIES):
        pool = df[df['_sample_category'] == category]
        available = len(pool)
        target = IRRELEVANT_PER_CATEGORY[i]
        actual = min(available, target)
        if actual > 0:
            sampled = pool.sample(n=actual, random_state=SEED)
            sampled_dfs.append(sampled)
        sample_summary[category] = {'target': target, 'available': available, 'sampled': actual}

    # ── Step 3: 缺口补充 ──
    current_total = sum(len(d) for d in sampled_dfs)
    shortage = n - current_total

    if shortage > 0:
        safe_print(f'\n  [WARN] 部分类别样本不足，需补充 {shortage} 条')
        # 从 "其他" 池和已采样不足的类别中补充
        already_sampled_idx = set()
        for sdf in sampled_dfs:
            already_sampled_idx.update(sdf.index)

        other_pool = df[~df.index.isin(already_sampled_idx)]
        if len(other_pool) > 0:
            extra_n = min(shortage, len(other_pool))
            extra = other_pool.sample(n=extra_n, random_state=SEED)
            sampled_dfs.append(extra)
            safe_print(f'  从剩余池补充 {extra_n} 条')

    # ── Step 4: 合并 & 去重 ──
    result = pd.concat(sampled_dfs, ignore_index=False)
    # 万一有重复索引，去重
    result = result[~result.index.duplicated(keep='first')]

    # 若还有不足，从原始数据随机补
    if len(result) < n:
        remaining_idx = df.index.difference(result.index)
        if len(remaining_idx) > 0:
            extra_n = min(n - len(result), len(remaining_idx))
            extra = df.loc[remaining_idx].sample(n=extra_n, random_state=SEED)
            result = pd.concat([result, extra], ignore_index=False)

    # 确保恰好 n 条
    if len(result) > n:
        result = result.sample(n=n, random_state=SEED)

    # 移除临时列
    result = result.drop(columns=['_sample_category'], errors='ignore')

    # ── 打印采样汇总 ──
    safe_print(f'\n  === 采样汇总 ===')
    safe_print(f'  {"类别":<6} {"目标":<6} {"可用":<6} {"实采":<6} {"达成率":<8}')
    safe_print(f'  {"-" * 38}')
    for cat, info in sample_summary.items():
        rate = f"{info['sampled'] / info['target'] * 100:.0f}%" if info['target'] > 0 else 'N/A'
        safe_print(f'  {cat:<6} {info["target"]:<6} {info["available"]:<6} {info["sampled"]:<6} {rate:<8}')

    safe_print(f'\n  [OK] 采样完成: {len(result)} 条')

    return result


# ═══════════════════════════════════════════════════════════
# 2. LLM 标注 (逐条)
# ═══════════════════════════════════════════════════════════

def label_batch(
    df: pd.DataFrame,
    api_key: Optional[str] = None,
    skip_labeled: bool = True,
) -> pd.DataFrame:
    """
    用 DeepSeek LLM 逐条标注数据。

    对 df 中每条数据调用 llm_classify()，将结果写入 relevance 系列列。
    支持断点续传: 如果某行已有有效标注结果则跳过。

    Args:
        df: 待标注的 DataFrame (需含 title/text/comments 列)
        api_key: DeepSeek API Key
        skip_labeled: 是否跳过已有标注的行

    Returns:
        标注后的 DataFrame
    """
    total = len(df)

    # 初始化标注列
    if 'relevance' not in df.columns:
        df['relevance'] = ''
    if 'relevance_dimensions' not in df.columns:
        df['relevance_dimensions'] = ''
    if 'relevance_emotion' not in df.columns:
        df['relevance_emotion'] = ''
    if 'relevance_urban_value' not in df.columns:
        df['relevance_urban_value'] = ''
    if 'relevance_summary' not in df.columns:
        df['relevance_summary'] = ''

    # 统计已标注
    already_labeled = 0
    if skip_labeled:
        for idx in df.index:
            rel = df.at[idx, 'relevance']
            if rel in ('relevant', 'irrelevant', 'error'):
                already_labeled += 1

    to_label = total - already_labeled
    safe_print(f'\n[LOAD] LLM 标注开始: 共 {total} 条, 已标注 {already_labeled} 条, 待标注 {to_label} 条')

    if to_label == 0:
        safe_print('[OK] 所有数据已标注完成，无需重复标注')
        return df

    processed = 0
    error_count = 0
    relevant_count = 0
    irrelevant_count = 0
    start_time = time.time()

    for _, idx in enumerate(df.index):
        # 跳过已标注
        if skip_labeled and df.at[idx, 'relevance'] in ('relevant', 'irrelevant', 'error'):
            continue

        text = _get_text_for_labeling(df.loc[idx])
        if not text:
            df.at[idx, 'relevance'] = 'irrelevant'
            df.at[idx, 'relevance_summary'] = 'empty text'
            processed += 1
            irrelevant_count += 1
            continue

        # 调用 LLM 标注
        result = llm_classify(text, api_key=api_key)

        processed += 1

        if result.get('error'):
            df.at[idx, 'relevance'] = 'error'
            df.at[idx, 'relevance_summary'] = result['error']
            error_count += 1
        else:
            if result.get('relevant'):
                df.at[idx, 'relevance'] = 'relevant'
                relevant_count += 1
            else:
                df.at[idx, 'relevance'] = 'irrelevant'
                irrelevant_count += 1

            dims = result.get('dimensions', [])
            df.at[idx, 'relevance_dimensions'] = (
                json.dumps(dims, ensure_ascii=False) if dims else ''
            )
            df.at[idx, 'relevance_emotion'] = result.get('primary_emotion', '')
            df.at[idx, 'relevance_urban_value'] = result.get('urban_value', '')
            df.at[idx, 'relevance_summary'] = result.get('summary', '')

        # 进度显示
        pct = processed / to_label * 100
        elapsed = time.time() - start_time
        if processed > 0:
            eta = (elapsed / processed) * (to_label - processed)
            eta_str = f'ETA {eta:.0f}s'
        else:
            eta_str = ''

        safe_print(
            f'  [LOAD] 第 {already_labeled + processed}/{total} 条 '
            f'({pct:.0f}%) '
            f'| 相关: {relevant_count} | 无关: {irrelevant_count} '
            f'| 错误: {error_count} '
            f'| {eta_str}'
        )

        # 每 10 条保存一次中间结果（断点续传保护）
        if processed % 10 == 0:
            _save_checkpoint(df)

    safe_print(f'\n[OK] LLM 标注完成!')
    safe_print(f'  相关: {relevant_count} | 无关: {irrelevant_count} | 错误: {error_count}')
    safe_print(f'  耗时: {time.time() - start_time:.0f}s')

    return df


def _get_text_for_labeling(row: pd.Series) -> str:
    """
    获取用于标注/训练的文本。

    优先使用 _build_text_for_classification (title+text 拼接)，
    如果行只有单个 'text' 列（断点续传场景），则直接使用该列。
    """
    # 断点续传场景：CSV 中只有合并后的 'text' 列
    if 'title' not in row.index and 'text' in row.index:
        val = row.get('text', '')
        return str(val).strip() if pd.notna(val) else ''

    # 正常场景：使用 relevance_filter 的拼接逻辑
    return _build_text_for_classification(row)


def _build_output_df(df: pd.DataFrame) -> pd.DataFrame:
    """构建输出 DataFrame，包含用户要求的列。"""
    out = df.copy()
    # 构建 text 列 (用于训练的文本)
    texts = []
    for idx in out.index:
        texts.append(_get_text_for_labeling(out.loc[idx]))
    out['text'] = texts

    # 输出列
    output_cols = ['text', 'source', 'tags',
                   'relevance', 'relevance_dimensions', 'relevance_emotion',
                   'relevance_urban_value', 'relevance_summary']
    available = [c for c in output_cols if c in out.columns]
    return out[available]


def _save_checkpoint(df: pd.DataFrame):
    """保存中间结果到输出文件。"""
    try:
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        out_df = _build_output_df(df)
        out_df.to_csv(OUTPUT_CSV, index=True, index_label='id_e',
                      encoding='utf-8-sig')
    except Exception as e:
        safe_print(f'  [WARN] 保存中间结果失败: {e}')


# ═══════════════════════════════════════════════════════════
# 3. 打印统计
# ═══════════════════════════════════════════════════════════

def print_statistics(df: pd.DataFrame):
    """打印标注结果统计。"""
    safe_print('\n' + '=' * 60)
    safe_print('  标注结果统计')
    safe_print('=' * 60)

    total = len(df)

    # ── 相关/无关比例 ──
    relevant_mask = df['relevance'] == 'relevant'
    irrelevant_mask = df['relevance'] == 'irrelevant'
    error_mask = df['relevance'] == 'error'

    n_relevant = relevant_mask.sum()
    n_irrelevant = irrelevant_mask.sum()
    n_error = error_mask.sum()

    safe_print(f'\n  [相关/无关比例]')
    safe_print(f'    总样本:    {total}')
    safe_print(f'    相关:      {n_relevant} ({n_relevant / total * 100:.1f}%)')
    safe_print(f'    无关:      {n_irrelevant} ({n_irrelevant / total * 100:.1f}%)')
    safe_print(f'    错误:      {n_error} ({n_error / total * 100:.1f}%)')

    # ── 五要素分布 ──
    safe_print(f'\n  [五要素分布] (相关样本中)')
    if n_relevant > 0:
        dim_counter = {}
        for idx in df[relevant_mask].index:
            dims_str = df.at[idx, 'relevance_dimensions']
            if dims_str and isinstance(dims_str, str):
                try:
                    dims = json.loads(dims_str)
                    for d in dims:
                        dim_counter[d] = dim_counter.get(d, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass

        if dim_counter:
            for dim, count in sorted(dim_counter.items(), key=lambda x: -x[1]):
                safe_print(f'    {dim}: {count}')
        else:
            safe_print(f'    (无维度数据)')
    else:
        safe_print(f'    (无相关样本)')

    # ── 情绪分布 ──
    safe_print(f'\n  [情绪分布] (相关样本中)')
    if n_relevant > 0:
        emotion_counts = df.loc[relevant_mask, 'relevance_emotion'].value_counts()
        for emotion, count in emotion_counts.items():
            if emotion:
                safe_print(f'    {emotion}: {count}')
        if emotion_counts.empty:
            safe_print(f'    (无情绪数据)')
    else:
        safe_print(f'    (无相关样本)')

    # ── urban_value 分布 ──
    safe_print(f'\n  [urban_value 分布] (相关样本中)')
    if n_relevant > 0:
        uv_counts = df.loc[relevant_mask, 'relevance_urban_value'].value_counts()
        for uv, count in uv_counts.items():
            if uv:
                safe_print(f'    {uv}: {count}')
        if uv_counts.empty:
            safe_print(f'    (无 urban_value 数据)')

    safe_print(f'\n' + '=' * 60)


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

def main():
    """主入口: 采样 + 标注 + 保存 + 统计。"""
    safe_print('=' * 60)
    safe_print('  标注训练数据 v1.0')
    safe_print(f'  输出: {OUTPUT_CSV}')
    safe_print('=' * 60)

    # ── 0. 获取 API Key ──
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        safe_print('\n[ERR] 环境变量 DEEPSEEK_API_KEY 未设置!')
        safe_print('  请先设置: $env:DEEPSEEK_API_KEY = "sk-xxx"')
        sys.exit(1)
    safe_print(f'\n[OK] API Key 已就绪 (model: {DEEPSEEK_MODEL})')

    # ── 1. 加载原始数据 ──
    safe_print(f'\n[LOAD] 加载原始数据: {INPUT_CSV}')
    if not os.path.exists(INPUT_CSV):
        safe_print(f'[ERR] 输入文件不存在: {INPUT_CSV}')
        sys.exit(1)

    df_raw = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    safe_print(f'[OK] 已加载 {len(df_raw)} 条数据')

    # ── 2. 分层采样 (固定 seed，确定性复现) ──
    df_to_label = sample_for_labeling(df_raw, TOTAL_SAMPLES)

    # ── 3. 检查是否已有标注进度 (断点续传) ──
    if os.path.exists(OUTPUT_CSV):
        safe_print(f'\n[LOAD] 检测到已有标注文件: {OUTPUT_CSV}')
        df_existing = pd.read_csv(OUTPUT_CSV, encoding='utf-8-sig', index_col='id_e')
        safe_print(f'  已有 {len(df_existing)} 条记录')

        # 检查是否已完成
        if 'relevance' in df_existing.columns:
            already_done = (df_existing['relevance'].isin(['relevant', 'irrelevant', 'error'])).sum()
        else:
            already_done = 0

        if already_done >= TOTAL_SAMPLES:
            safe_print(f'[OK] 标注已完成 ({already_done} 条)，直接打印统计')
            print_statistics(df_existing)
            return
        elif already_done > 0:
            safe_print(f'  其中已标注 {already_done} 条，将 merge 标注列到重采样数据上继续')
            # 确定性复现: 重采样后再 merge checkpoint 的标注列
            # 不依赖原始 CSV 的行序，只依赖 seed 固定的重采样结果
            label_cols = ['relevance', 'relevance_dimensions', 'relevance_emotion',
                          'relevance_urban_value', 'relevance_summary']
            for col in label_cols:
                if col in df_existing.columns:
                    if col not in df_to_label.columns:
                        df_to_label[col] = ''
                    # 仅覆盖重采样和 checkpoint 共有的行
                    common_idx = df_to_label.index.intersection(df_existing.index)
                    df_to_label.loc[common_idx, col] = df_existing.loc[common_idx, col]
        else:
            safe_print(f'  [WARN] 文件中无有效标注数据，将使用新采样结果')

    # ── 4. LLM 标注 ──
    df_labeled = label_batch(df_to_label, api_key=api_key, skip_labeled=True)

    # ── 5. 保存最终结果 ──
    safe_print(f'\n[SAVE] 保存标注结果到: {OUTPUT_CSV}')
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    out_df = _build_output_df(df_labeled)
    out_df.to_csv(OUTPUT_CSV, index=True, index_label='id_e',
                  encoding='utf-8-sig')
    safe_print(f'[OK] 已保存 {len(out_df)} 条记录')

    # ── 6. 打印统计 ──
    print_statistics(df_labeled)

    safe_print(f'\n[OK] 全部完成!')


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
