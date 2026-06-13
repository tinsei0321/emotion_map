"""
统一数据加载 — CSV / GeoJSON → 结构化数据
══════════════════════════════════════════════════════════════
消除 streamlit_app_v2 / test_base_map / test_scripts_2 中的重复加载逻辑。
"""
import json
import os
import re
import pandas as pd


def load_emotion_data(file_path: str) -> dict | None:
    """
    统一入口：根据文件扩展名自动选择加载方式。

    参数:
        file_path: 文件路径（支持 .csv / .tsv / .json / .geojson）

    返回:
        {
            'lats': [纬度列表],
            'lons': [经度列表],
            'scores': [情绪得分列表],
            'df': pd.DataFrame,       # 表格数据（不含 geometry 列）
            'n_points': int,          # 数据点数量
        }
        失败返回 None
    """
    if not os.path.exists(file_path):
        return None

    ext = os.path.splitext(file_path)[1].lower().lstrip('.')

    if ext in ('csv', 'tsv'):
        return _load_csv(file_path, ext)
    elif ext in ('json', 'geojson'):
        return _load_geojson(file_path)
    return None


def _load_csv(file_path: str, ext: str) -> dict:
    """加载 CSV/TSV，自动检测 lon/lat 列或 coordinate 元组列"""
    sep = '\t' if ext == 'tsv' else ','
    df = pd.read_csv(file_path, sep=sep)

    lats, lons = [], []

    # 方式 A：独立的 lon/lat 列
    lon_col = next((c for c in ['lon', 'longitude', 'lng', 'lon_gcj02'] if c in df.columns), None)
    lat_col = next((c for c in ['lat', 'latitude', 'lat_gcj02'] if c in df.columns), None)
    if lon_col and lat_col:
        lats = df[lat_col].astype(float).tolist()
        lons = df[lon_col].astype(float).tolist()
    # 方式 B：coordinate 元组列 "(111.29, 30.71)"
    elif 'coordinate' in df.columns:
        for _, row in df.iterrows():
            m = re.findall(r'[\d.]+', str(row['coordinate']))
            if len(m) >= 2:
                lons.append(float(m[0]))
                lats.append(float(m[1]))
    else:
        return None

    scores = (df['score'].astype(float).tolist()
              if 'score' in df.columns
              else [0.5] * len(lats))

    # 过滤 NaN 坐标（兜底）
    valid_indices = [
        i for i in range(len(lats))
        if (isinstance(lats[i], (int, float)) and isinstance(lons[i], (int, float))
            and not (pd.isna(lats[i]) or pd.isna(lons[i])))
    ]
    if len(valid_indices) < len(lats):
        lats = [lats[i] for i in valid_indices]
        lons = [lons[i] for i in valid_indices]
        scores = [scores[i] for i in valid_indices]
        df = df.iloc[valid_indices].reset_index(drop=True)

    return {
        'lats': lats,
        'lons': lons,
        'scores': scores,
        'df': df,
        'n_points': len(lats),
    }


def _load_geojson(file_path: str) -> dict:
    """加载 GeoJSON FeatureCollection"""
    with open(file_path, encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, dict) or data.get('type') != 'FeatureCollection':
        return None

    lats, lons, scores = [], [], []
    for feat in data['features']:
        c = feat['geometry']['coordinates']
        lons.append(c[0])
        lats.append(c[1])
        scores.append(float(feat['properties'].get('score', 0.5)))

    # 构建 DataFrame（不含 geometry，方便表格展示）
    props = [feat['properties'] for feat in data['features']]
    df = pd.DataFrame(props)

    return {
        'lats': lats,
        'lons': lons,
        'scores': scores,
        'df': df,
        'geo_data': data,       # 保留原始 GeoJSON 用于地图渲染
        'n_points': len(lats),
    }
