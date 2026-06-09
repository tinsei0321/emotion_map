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
# 思路（一）：小规模数据测试。for循环逐条生成emotion_dict，字典新增列，再生成DataFrame
# 思路（二）：大规模生产。向量化直接处理DataFrame，新增列


# 环境准备
os.makedirs('data/processed', exist_ok=True)    # 创建阶段性（复用）成果目录


# 安全读取csv文件
def safe_read_csv(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        return data
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []
# 读取测试csv文件
file_path = 'data/raw/test_0609_1.csv'
data_raw = safe_read_csv(file_path)
df_raw = pd.DataFrame(data_raw)
# 数据预处理，质量控制
print(f"原始数据条数: {len(df_raw)}")
df_clean = df_raw.dropna(subset=['comments'])                  # 去 NaN
df_clean = df_clean[df_clean['comments'].str.strip() != '']    # 去空字符串
print(f"清洗后数据条数: {len(df_clean)}")       


# for循环字典路径（小规模测试，需要增加异常处理）
# 生成emotion_dict（L2）: ['id', 'coordinate', 'district', 'poi', 'comments', 'score', 'polarity']
print("开始SnowNLP情绪分析 L2...")

# 创建emotion_dict，定义字段，初始化字典
emotion_dict = {field: [] for field in [
    'id_e',
    'coordinate',
    'district',
    'poi',
    'comments',
    'score',
    'polarity',
]}


# 遍历数据，填充字典，异常处理
for i, row in tqdm(df_clean.iterrows(), total=len(df_clean), desc="情绪分析进度"):
    try:
        # 提取并清洗评论文本数据
        text = str(row['comments']).strip()    # 移除空格、制表符、换行符，语法：字符转.strip(字符)
        if len(text) == 0:
            continue    # 跳过评论值为空
        # Eomtion_analysis_results_L2
        s = round(SnowNLP(text).sentiments, 2)    # SnowNLP打分，取小数点后两位
        if s < 0.3:
            polarity = "Negative"
        elif s <0.7:
            polarity = "Neutral"
        else:
            polarity = "Positive"
        
        # 填充字典
        emotion_dict['id_e'].append(f"e{i+1:04d}")    # 将id_e的格式调整为：e0001
        lon = round(float(row['lon']), 2)    # 定义lon
        lat = round(float(row['lat']), 2)    # 定义lat
        emotion_dict['coordinate'].append((lon, lat))    # 填充经纬度，存为元组（lon, lat）
        emotion_dict['district'].append(row['district']) # 填充行政区划 
        emotion_dict['poi'].append(row['poi'])           # 填充poi
        emotion_dict['comments'].append(row['comments']) # 填充原始评论文本
        emotion_dict['score'].append(s)                  # 填充评分
        emotion_dict['polarity'].append(polarity)        # 填充情绪极性
    
    except Exception as e:
        print(f"\n id={row['id']}行数据处理出错: {e}")
        continue

print(f"\n 情绪分析完成，成功处理{len(emotion_dict['id_e'])}行数据，数据总量{len(df_clean)}行")


# 转换为DataFrame
df_result = pd.DataFrame(emotion_dict)


# 保存阶段性成果（.to_csv），方便数据复用
csv_path = 'data/processed/test_0609_1_result_csv.csv'
df_result.to_csv(csv_path, index=False, encoding='utf-8')
print(f"\n CSV结果已保存至：{csv_path}")
        

# CSV转换GeoJSON格式（使用geopandas）
# 读取csv或直接使用df_result
gdf = gpd.GeoDataFrame(                   # 创建GeoDataFrame
    df_result,                            # 传入普通DataFrame
    geometry=gpd.points_from_xy(          # 根据经纬度生成几何列
        df_result['coordinate'].str[0],   # 取坐标列每个元组中的第1个元素（lon）
        df_result['coordinate'].str[1]    # 取坐标列每个元组中的第2个元素（lat）
    ),
    crs="EPSG:4326"                       # WGS84坐标系
)

gdf_result = gdf.drop(columns=['coordinate'])    # 删除坐标列（已转换为geometry）

# 保存为GeoJSON
geojson_path = 'data/processed/test_0609_1_result_geojson.geojson'
gdf_result.to_file(geojson_path, driver='GeoJSON', encoding='utf-8')
print(f"\n GEOJSON结果已保存至：{geojson_path}")


# 调整工作目录：cd C:\Users\admin\Documents\GitHub\emotion_map
# 运行命令：python SCRIPT/test_scripts.py

# Streamlit展示：python -m streamlit run streamlit_app.py --server.port 8502 2>&1