# 这是一个测试脚本，用于练习数据处理和分析

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import geopandas as gpd
import numpy as np
import csv
import json
from snownlp import SnowNLP
from tqdm import tqdm

# 现在可以导入 emotion_map 包了
from core.config import PROCESSED_DIR, SCORE_POSITIVE, SCORE_NEGATIVE

# 修复 Windows GBK 控制台 emoji 编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


# 增加数据预处理环节，去除无效数据、空数据、重复数据等，确保数据质量
# 思路（二）：大规模生产。向量化直接处理DataFrame，新增列
# 与思路（一）的区别：全程使用 pandas 向量化操作（.apply / np.select / 直接列赋值），
# 避免 for 循环 iterrows，大幅提升大批量数据处理性能。


# 环境准备
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 确保工作目录为项目根目录
os.makedirs(PROCESSED_DIR, exist_ok=True)    # 创建阶段性（复用）成果目录


# ─── 安全读取csv文件 ───
def safe_read_csv(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        return data
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

# ─── 读取原始数据 ───
file_path = 'data/raw/test_0609_1.csv'
data_raw = safe_read_csv(file_path)
df_raw = pd.DataFrame(data_raw)

# ─── 数据预处理（向量化） ───
print(f"原始数据条数: {len(df_raw)}")

# 向量化清洗：链式操作，一步到位
df_clean = (
    df_raw
    .dropna(subset=['comments'])                              # 去 NaN
    .loc[lambda d: d['comments'].str.strip() != '']           # 去空字符串
    .drop_duplicates(subset=['comments'])                     # 去重复评论
    .reset_index(drop=True)                                   # 重置索引
)
print(f"清洗后数据条数: {len(df_clean)}")
print(f"去除无效数据: {len(df_raw) - len(df_clean)} 条")


# ═══════════════════════════════════════════════════════════
# 思路（二）核心：向量化情绪分析（五级极性 + 关键词 + 置信度）
# ═══════════════════════════════════════════════════════════
print("\n 开始SnowNLP情绪分析 L2（五级极性）...")

# ─── Step 1: 向量化 SnowNLP 打分 ───
tqdm.pandas(desc="SnowNLP 打分")
df_clean['score'] = df_clean['comments'].progress_apply(
    lambda x: round(SnowNLP(str(x).strip()).sentiments, 2)
)

# ─── Step 2: 向量化五级极性分类 ───
# 五级制，面向城市更新/治理优化：
#   Very Negative (0.00~0.20): 严重不满 → 需紧急干预
#   Negative      (0.20~0.40): 一般负面 → 需关注改善
#   Neutral       (0.40~0.60): 中性/无明显情绪
#   Positive      (0.60~0.80): 一般正面 → 维持即可
#   Very Positive (0.80~1.00): 非常满意 → 可作为标杆
conditions = [
    df_clean['score'] <= 0.20,
    df_clean['score'] <= 0.40,
    df_clean['score'] <= 0.60,
    df_clean['score'] <= 0.80,
]
choices = ['Very Negative', 'Negative', 'Neutral', 'Positive']
df_clean['polarity'] = np.select(conditions, choices, default='Very Positive')

# 三级极性（向后兼容）
df_clean['polarity_ternary'] = np.select(
    [df_clean['polarity'].isin(['Very Positive', 'Positive']),
     df_clean['polarity'].isin(['Very Negative', 'Negative'])],
    ['Positive', 'Negative'],
    default='Neutral',
)

# ─── Step 3: 情绪关键词提取（jieba TF-IDF）──
try:
    import jieba.analyse
    tqdm.pandas(desc="关键词提取")
    df_clean['keywords'] = df_clean['comments'].progress_apply(
        lambda x: ','.join(jieba.analyse.extract_tags(str(x).strip(), topK=5))
    )
except ImportError:
    df_clean['keywords'] = ''
    print("[WARN] jieba 未安装，跳过关键词提取。安装: pip install jieba")

# ─── Step 4: 置信度（文本长度归一化）──
df_clean['confidence'] = df_clean['comments'].str.strip().str.len().clip(upper=100) / 100.0
df_clean['confidence'] = df_clean['confidence'].round(2)

# ─── Step 5: 向量化生成 id_e ───
df_clean['id_e'] = 'e' + (df_clean.index + 1).astype(str).str.zfill(4)

# ─── Step 6: 向量化坐标处理 ───
df_clean['lon'] = df_clean['lon'].astype(float).round(4)
df_clean['lat'] = df_clean['lat'].astype(float).round(4)

# ─── Step 7: 整理输出列 ───
df_result = df_clean[[
    'id_e', 'lon', 'lat', 'district', 'poi', 'comments',
    'score', 'polarity', 'polarity_ternary', 'keywords', 'confidence',
]].copy()

# ─── 统计概览 ───
print(f"\n情绪分析完成，成功处理 {len(df_result)} 条数据")
print(f"五级极性分布:")
for pol in ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']:
    cnt = (df_result['polarity'] == pol).sum()
    if cnt > 0:
        print(f"   {pol:16s} {cnt:5d} 条 ({cnt/len(df_result)*100:4.1f}%)")
print(f"评分均值: {df_result['score'].mean():.2f}，中位数: {df_result['score'].median():.2f}")

# 城市治理视角
actionable = df_result['polarity'].isin(['Very Negative', 'Negative']).sum()
benchmark = (df_result['polarity'] == 'Very Positive').sum()
print(f"\n  --- 城市治理视角:")
print(f"   需干预项 (Negative + Very Negative): {actionable} 条")
print(f"   标杆项   (Very Positive):              {benchmark} 条")


# ═══════════════════════════════════════════════════════════
# 保存阶段性成果
# ═══════════════════════════════════════════════════════════

# ─── 保存为 CSV ───
csv_path = f'{PROCESSED_DIR}/test_0609_2_L2_result_csv.csv'
df_result.to_csv(csv_path, index=False, encoding='utf-8')
print(f"\n[OK] CSV 结果已保存至: {csv_path}")

# ─── 保存为 GeoJSON（向量化方式） ───
# 直接用 lon/lat 列创建 GeoDataFrame，无需中间元组转换
gdf = gpd.GeoDataFrame(
    df_result,
    geometry=gpd.points_from_xy(df_result['lon'], df_result['lat']),
    crs="EPSG:4326"
)

# 删除冗余的 lon/lat 列（geometry 已包含坐标信息）
gdf_result = gdf.drop(columns=['lon', 'lat'])

geojson_path = f'{PROCESSED_DIR}/test_0609_2_L2_result_geojson.geojson'
gdf_result.to_file(geojson_path, driver='GeoJSON', encoding='utf-8')
print(f"[OK] GeoJSON 结果已保存至: {geojson_path}")

print("\n[OK] 向量化处理流程全部完成！")
print(f"   输出文件: {csv_path}")
print(f"   输出文件: {geojson_path}")

# ─── 运行说明 ───
# cd C:\Users\admin\Documents\GitHub\emotion_map
# python SCRIPT/test_scripts_2.py
# streamlit run streamlit_app.py

