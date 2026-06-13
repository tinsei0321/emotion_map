#!/usr/bin/env python3
"""
L1 模拟数据生成脚本 v1.0
========================
从 L0 原始数据 `DATA/raw/simulated_20260613_100k_raw.csv` 中
筛选"城市相关"标签，生成 2000 条 L1 模拟治理数据。

数据流程:
  1. 筛选城市相关标签 → 取 2000 条
  2. 坐标转换：GCJ02 → WGS84 → CGCS2000 EPSG:4546
  3. 注入 L1 模拟字段（id_e, scope, relevance 等）
  4. 导出到 DATA/processed/

输出: DATA/processed/simulated_l1_2000_规划范围_L1_result_csv.csv

用法: python SCRIPT/generate_l1_mock.py
"""

import os
import sys
import random
import builtins as _bi
from collections import Counter

import pandas as pd
import numpy as np
from pyproj import Transformer

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

# 确保可导入 core 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.coord_transform import gcj02_to_wgs84
from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id

# ═══════════════════════════════════════════════════════════
# 全局配置
# ═══════════════════════════════════════════════════════════

random.seed(2026)
np.random.seed(2026)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'raw')
PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'processed')
RAW_CSV = os.path.join(RAW_DIR, 'simulated_20260613_100k_raw.csv')
OUTPUT_CSV = os.path.join(PROCESSED_DIR, 'simulated_l1_2000_规划范围_L1_result_csv.csv')

TARGET_COUNT = 2000

# ── 城市相关标签（用于筛选）──
CITY_TAGS = [
    '城市', '城建', '规划', '环境', '社区', '民生', '投诉',
    '设施', '交通', '河道', '噪音', '公共设施', '基础设施',
    '本地新闻', '城市生活',
]

# ── 标签 → relevance_category 映射 ──
TAG_TO_CATEGORY = {
    '城市': '城市',
    '城建': '城建',
    '规划': '规划',
    '环境': '环境',
    '社区': '社区',
    '民生': '民生',
    '投诉': '投诉',
    '设施': '设施',
    '交通': '交通',
    '河道': '环境',
    '噪音': '环境',
    '公共设施': '设施',
    '基础设施': '设施',
    '本地新闻': '本地新闻',
    '城市生活': '城市生活',
}

# ── 情绪类别池 ──
EMOTIONS = ['满足', '期待', '失望', '愤怒', '喜爱', '怀念', '好奇', '中性']

# ── 城市价值池 ──
URBAN_VALUES = ['high', 'medium', 'low']

# ── 宜昌地名池（用于 location_mentioned 随机抽取）──
YICHANG_PLACES = [
    '西陵区', '伍家岗区', '点军区', '猇亭区', '夷陵区',
    '滨江公园', '东山公园', '运河公园', '儿童公园', '磨基山公园', '夷陵广场',
    '沿江大道', '胜利四路', '云集路', '东山大道', '夷陵大道',
    '发展大道', '城东大道', '港窑路', '西陵一路', '珍珠路',
    'CBD', '万达广场', '国贸大厦', '均瑶广场', '水悦城',
    '锦绣社区', '白龙岗小区', '绿萝路', '体育场路', '葛洲坝', '三峡大学',
    '长江', '黄柏河', '东山',
]


# ═══════════════════════════════════════════════════════════
# 步骤 1: 加载并筛选城市相关数据
# ═══════════════════════════════════════════════════════════

@track("MOD_GEN.F_001", track_args=False)
def load_and_filter() -> pd.DataFrame:
    """加载 L0 原始 CSV，筛选城市相关标签，取前 TARGET_COUNT 条。"""
    _safe_print(f'[LOAD] 读取原始数据: {RAW_CSV}')

    if not os.path.exists(RAW_CSV):
        raise FileNotFoundError(f'原始数据文件不存在: {RAW_CSV}')

    df = pd.read_csv(RAW_CSV, encoding='utf-8')
    _safe_print(f'[LOAD] 共加载 {len(df)} 条原始记录')

    # 筛选：tags 列包含任一城市标签
    with TrackContext("MOD_GEN.D_001", input_n=len(df)):
        pattern = '|'.join(CITY_TAGS)
        mask = df['tags'].astype(str).str.contains(pattern, case=False, na=False)
        df_city = df[mask].copy()
        _safe_print(f'[FILTER] 城市相关标签匹配: {len(df_city)} 条')

    if len(df_city) < TARGET_COUNT:
        _safe_print(f'[WARN] 城市相关数据不足 {TARGET_COUNT} 条，仅有 {len(df_city)} 条')
    else:
        df_city = df_city.head(TARGET_COUNT)
        _safe_print(f'[FILTER] 取前 {TARGET_COUNT} 条')

    return df_city


# ═══════════════════════════════════════════════════════════
# 步骤 2: 坐标转换 GCJ-02 → WGS84 → CGCS2000 EPSG:4546
# ═══════════════════════════════════════════════════════════

@track("MOD_GEN.F_002", track_args=False)
def transform_coords(df: pd.DataFrame) -> pd.DataFrame:
    """坐标转换：GCJ-02 → WGS84 → CGCS2000 EPSG:4546。"""
    _safe_print('[TRANSFORM] GCJ-02 → WGS84 (数学转换)...')

    wgs84_lons = []
    wgs84_lats = []
    for _, row in df.iterrows():
        try:
            lon_val = float(row['lon_gcj02'])
            lat_val = float(row['lat_gcj02'])
            wlon, wlat = gcj02_to_wgs84(lon_val, lat_val)
            wgs84_lons.append(round(wlon, 6))
            wgs84_lats.append(round(wlat, 6))
        except (ValueError, TypeError) as e:
            _safe_print(f'[WARN] 坐标转换失败 (行索引={_.name}): {e}')
            wgs84_lons.append(None)
            wgs84_lats.append(None)

    df['lon'] = wgs84_lons
    df['lat'] = wgs84_lats
    _safe_print(f'[OK] WGS84 转换完成, 有效: {sum(1 for v in wgs84_lons if v is not None)} 条')

    # ── 投影: WGS84 → CGCS2000 EPSG:4546 ──
    _safe_print('[TRANSFORM] WGS84 → CGCS2000 EPSG:4546 (投影)...')
    try:
        transformer = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
    except Exception as e:
        _safe_print(f'[ERR] 无法创建 pyproj Transformer: {e}')
        df['x_cgcs2000'] = None
        df['y_cgcs2000'] = None
        return df

    x_cgcs = []
    y_cgcs = []
    for _, row in df.iterrows():
        try:
            if row['lon'] is None or row['lat'] is None:
                x_cgcs.append(None)
                y_cgcs.append(None)
                continue
            x, y = transformer.transform(row['lon'], row['lat'])
            x_cgcs.append(round(x, 2))
            y_cgcs.append(round(y, 2))
        except Exception as e:
            _safe_print(f'[WARN] EPSG:4546 投影失败 (索引={_.name}): {e}')
            x_cgcs.append(None)
            y_cgcs.append(None)

    df['x_cgcs2000'] = x_cgcs
    df['y_cgcs2000'] = y_cgcs
    _safe_print(f'[OK] EPSG:4546 投影完成, 有效: {sum(1 for v in x_cgcs if v is not None)} 条')

    return df


# ═══════════════════════════════════════════════════════════
# 步骤 3: 注入 L1 模拟字段
# ═══════════════════════════════════════════════════════════

def _map_tag_to_category(tags_str: str) -> str:
    """将 tags 字符串映射到 relevance_category。"""
    if not isinstance(tags_str, str):
        return '其他'
    for tag in CITY_TAGS:
        if tag in tags_str and tag in TAG_TO_CATEGORY:
            return TAG_TO_CATEGORY[tag]
    # 兜底：按匹配到的第一个城市标签
    for tag in CITY_TAGS:
        if tag in tags_str:
            return '其他'
    return '其他'


@track("MOD_GEN.F_003", track_args=False)
def inject_l1_fields(df: pd.DataFrame) -> pd.DataFrame:
    """注入 L1 模拟字段：id_e, scope, text_length 等。"""
    n = len(df)
    _safe_print(f'[INJECT] 为 {n} 条数据注入 L1 模拟字段...')

    # id_e: e0001 ~ e{nnnn}
    df['id_e'] = ['e' + str(i + 1).zfill(4) for i in range(n)]

    # scope
    df['scope'] = '规划范围'

    # text_length
    df['text_length'] = df['text'].astype(str).apply(len)

    # location_mentioned: 随机抽取宜昌地名
    df['location_mentioned'] = [random.choice(YICHANG_PLACES) for _ in range(n)]

    # has_location
    df['has_location'] = True

    # relevance
    df['relevance'] = 'relevant'

    # relevance_category: 根据 tags 映射
    df['relevance_category'] = df['tags'].apply(_map_tag_to_category)

    # primary_emotion: 随机分配
    df['primary_emotion'] = [random.choice(EMOTIONS) for _ in range(n)]

    # emotion_intensity: 随机 1-5
    df['emotion_intensity'] = [random.randint(1, 5) for _ in range(n)]

    # urban_value: 随机 high/medium/low
    df['urban_value'] = [random.choice(URBAN_VALUES) for _ in range(n)]

    # ai_summary: 基于 text 截取前 20 字
    df['ai_summary'] = df['text'].astype(str).apply(lambda t: t[:20])

    # ai_confidence: 随机 0.70-0.99
    df['ai_confidence'] = [round(random.uniform(0.70, 0.99), 2) for _ in range(n)]

    # 脱敏：清空 comments 列
    if 'comments' in df.columns:
        df['comments'] = ''

    _safe_print(f'[OK] L1 字段注入完成, 共 {len(df.columns)} 列')

    return df


# ═══════════════════════════════════════════════════════════
# 步骤 4: 导出 + 统计
# ═══════════════════════════════════════════════════════════

@track("MOD_GEN.F_004", track_args=False)
def export_and_stats(df: pd.DataFrame) -> str:
    """导出 L1 CSV 并打印统计信息。"""
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # L1 列顺序（与 data_governance.py L1_COLUMNS 一致）
    col_order = [
        'id_e', 'scope', 'location_mentioned',
        'text', 'title', 'text_length',
        'relevance', 'relevance_category', 'primary_emotion',
        'emotion_intensity', 'urban_value', 'ai_summary', 'ai_confidence',
        'filter_layer', 'has_location',
        'like_count', 'comment_count', 'tags',
        'source', 'url', 'crawl_time', 'publish_time',
        'lon', 'lat', 'x_cgcs2000', 'y_cgcs2000',
    ]
    cols = [c for c in col_order if c in df.columns] + \
           [c for c in df.columns if c not in col_order]
    df = df[cols]

    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    _safe_print(f'[OK] L1 CSV 已保存: {OUTPUT_CSV}')
    _safe_print(f'[OK] 共 {len(df)} 条, {len(df.columns)} 个字段')

    # ── 统计输出 ──
    _safe_print('\n' + '=' * 60)
    _safe_print('  统计报告')
    _safe_print('=' * 60)

    # relevance_category 分布
    if 'relevance_category' in df.columns:
        cat_counts = df['relevance_category'].value_counts()
        _safe_print(f'\n[STAT] relevance_category 分布 (共 {len(cat_counts)} 类):')
        for cat, cnt in cat_counts.items():
            bar = '#' * max(1, int(cnt / max(cat_counts) * 40))
            _safe_print(f'  {cat:<12s} {cnt:>5d}  {bar}')

    # primary_emotion 分布
    if 'primary_emotion' in df.columns:
        emo_counts = df['primary_emotion'].value_counts()
        _safe_print(f'\n[STAT] primary_emotion 分布:')
        for emo, cnt in emo_counts.items():
            _safe_print(f'  {emo:<8s} {cnt:>5d}')

    # urban_value 分布
    if 'urban_value' in df.columns:
        uv_counts = df['urban_value'].value_counts()
        _safe_print(f'\n[STAT] urban_value 分布:')
        for val, cnt in uv_counts.items():
            _safe_print(f'  {val:<8s} {cnt:>5d}')

    # emotion_intensity 分布
    if 'emotion_intensity' in df.columns:
        ei_counts = df['emotion_intensity'].value_counts().sort_index()
        _safe_print(f'\n[STAT] emotion_intensity 分布:')
        for val, cnt in ei_counts.items():
            _safe_print(f'  等级 {val}: {cnt:>5d}')

    _safe_print('\n' + '=' * 60)
    _safe_print(f'  输出文件: {OUTPUT_CSV}')
    _safe_print('=' * 60)

    return OUTPUT_CSV


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

@track("MOD_GEN.F_005", track_args=False)
def main():
    _safe_print('=' * 60)
    _safe_print('  L1 模拟数据生成脚本 v1.0')
    _safe_print('=' * 60)
    _safe_print(f'  数据源: {RAW_CSV}')
    _safe_print(f'  目标条数: {TARGET_COUNT}')
    _safe_print(f'  城市标签: {CITY_TAGS}')
    _safe_print('=' * 60)

    try:
        # 1. 加载并筛选
        df = load_and_filter()
        _safe_print(f'[STEP 1/4] 筛选完成: {len(df)} 条')

        # 2. 坐标转换
        df = transform_coords(df)
        _safe_print(f'[STEP 2/4] 坐标转换完成')

        # 3. 注入 L1 字段
        df = inject_l1_fields(df)
        _safe_print(f'[STEP 3/4] L1 字段注入完成')

        # 4. 导出 + 统计
        export_and_stats(df)
        _safe_print(f'[STEP 4/4] 导出完成')

        _safe_print('\n[OK] 全部完成！')
    except Exception as e:
        _safe_print(f'\n[ERR] 执行失败: {e}')
        trace_error("MOD_GEN.F_005", f'主流程异常: {str(e)[:200]}')
        raise


# ── 追踪 ID 注册表 ──
register_track_id("MOD_GEN.F_001", "加载 L0 原始数据并筛选城市相关标签")
register_track_id("MOD_GEN.F_002", "坐标转换 GCJ-02 → WGS84 → CGCS2000 EPSG:4546")
register_track_id("MOD_GEN.F_003", "注入 L1 模拟字段（id_e/scope/relevance/emotion 等）")
register_track_id("MOD_GEN.F_004", "导出 L1 CSV 并打印统计报告")
register_track_id("MOD_GEN.F_005", "L1 模拟数据生成主流程")
register_track_id("MOD_GEN.D_001", "城市相关标签筛选（正则匹配 tags 列）")

if __name__ == '__main__':
    main()
