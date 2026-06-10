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

