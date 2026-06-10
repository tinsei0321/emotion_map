# 这是一个测试脚本，用于练习数据处理和分析

import pandas as pd
import geopandas as gpd
import numpy as np
import csv
import json
import os
from snownlp import SnowNLP
from tqdm import tqdm


# 增加数据预处理环节，去除无效数据、空数据、重复数据等，确保数据质量
# 思路（二）：大规模生产。向量化直接处理DataFrame，新增列
# 与思路（一）的区别：全程使用 pandas 向量化操作（.apply / np.select / 直接列赋值），
# 避免 for 循环 iterrows，大幅提升大批量数据处理性能。


# 环境准备
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 确保工作目录为项目根目录
os.makedirs('data/processed', exist_ok=True)    # 创建阶段性（复用）成果目录


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
# 思路（二）核心：向量化情绪分析
# ═══════════════════════════════════════════════════════════
print("\n 开始SnowNLP情绪分析 L2...")

# ─── Step 1: 向量化 SnowNLP 打分 ───
# 使用 .apply() 对整列操作，比 iterrows 快 3-5 倍
tqdm.pandas(desc="SnowNLP 打分")  # 为 pandas apply 添加进度条
df_clean['score'] = df_clean['comments'].progress_apply(
    lambda x: round(SnowNLP(str(x).strip()).sentiments, 2)
)

# ─── Step 2: 向量化极性分类 ───
# 使用 np.select 一次性完成全列条件判断，避免逐行 if-else
conditions = [
    df_clean['score'] < 0.3,
    df_clean['score'] < 0.7,
]
choices = ['Negative', 'Neutral']
df_clean['polarity'] = np.select(conditions, choices, default='Positive')

# ─── Step 3: 向量化生成 id_e ───
# 利用 pandas 索引直接生成格式化 ID
df_clean['id_e'] = 'e' + (df_clean.index + 1).astype(str).str.zfill(4)

# ─── Step 4: 向量化坐标处理 ───
# 直接保留 lon/lat 为浮点数列，保留4位小数避免坐标重叠（~11m精度）
df_clean['lon'] = df_clean['lon'].astype(float).round(4)
df_clean['lat'] = df_clean['lat'].astype(float).round(4)

# ─── Step 5: 整理输出列 ───
# 构建最终结果 DataFrame（纯向量化列选择）
df_result = df_clean[[
    'id_e', 'lon', 'lat', 'district', 'poi', 'comments', 'score', 'polarity'
]].copy()

# ─── 统计概览 ───
print(f"\n情绪分析完成，成功处理 {len(df_result)} 条数据")
print(f"情绪分布:\n{df_result['polarity'].value_counts().to_string()}")
print(f"评分均值: {df_result['score'].mean():.2f}，中位数: {df_result['score'].median():.2f}")


# ═══════════════════════════════════════════════════════════
# 保存阶段性成果
# ═══════════════════════════════════════════════════════════

# ─── 保存为 CSV ───
csv_path = 'data/processed/test_0609_2_result_csv.csv'
df_result.to_csv(csv_path, index=False, encoding='utf-8')
print(f"\n✅ CSV 结果已保存至: {csv_path}")

# ─── 保存为 GeoJSON（向量化方式） ───
# 直接用 lon/lat 列创建 GeoDataFrame，无需中间元组转换
gdf = gpd.GeoDataFrame(
    df_result,
    geometry=gpd.points_from_xy(df_result['lon'], df_result['lat']),
    crs="EPSG:4326"
)

# 删除冗余的 lon/lat 列（geometry 已包含坐标信息）
gdf_result = gdf.drop(columns=['lon', 'lat'])

geojson_path = 'data/processed/test_0609_2_result_geojson.geojson'
gdf_result.to_file(geojson_path, driver='GeoJSON', encoding='utf-8')
print(f"✅ GeoJSON 结果已保存至: {geojson_path}")

print("\n🎉 向量化处理流程全部完成！")
print(f"   输出文件: {csv_path}")
print(f"   输出文件: {geojson_path}")

# ─── 运行说明 ───
# cd C:\Users\admin\Documents\GitHub\emotion_map
# python SCRIPT/test_scripts_2.py
# streamlit run streamlit_app.py

