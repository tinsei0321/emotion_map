# 这是一个测试脚本，用于练习数据处理和分析

import pandas as pd
import geopandas as gpd
import numpy as np
import csv
import json
import os
from snownlp import SnowNLP
from tqdm import tqdm

# 思路（一）：小规模数据测试，for循环逐条生成emotion_dict，字典新增列，再生成DataFrame
# 思路（二）：大规模生产，向量化直接处理DataFrame，新增列


# 小规模测试（for循环字典路径）
# 生成emotion_dict（L2）: ['id', 'coordinate', 'district', 'poi', 'comments', 'score', 'polarity']
for i, text in enumerate(texts):    # enumerate原始评论文本，生成emotion_dict（L2）


    emotion_dict = [
        {
            "id": f"e{i+1:04d}",    # 情绪id, e0001
            "coordinate": (x, y),    # x = lon, y = lat
            "district": district,    # 行政区划
            "poi": poi,    # POI
            "comments": text,   # 原始评论文本
            # Emotion_analysis_results_L2:
            "score": s,    # s > 0.5: positive, s < 0.5: negative, s = 0.5: neutral
            "polarity": polarity,   # porality: ["positive", "negative", "neutral"]          
        }
    ]



