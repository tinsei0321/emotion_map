"""
数据治理管道 v2.0 — Data Governance Pipeline (L1)
==================================================
L0(原始爬取) -> 批量LLM筛选+分类 -> L1(治理后城市情绪DATA) -> L2(SnowNLP分析)

新流程 (v2.0):
  1. 加载原始数据 + 坐标转换 (GCJ-02 -> WGS84 -> CGCS2000 EPSG:4546)
  2. 批量 DeepSeek LLM 一次完成: relevance? + 五要素 + 情绪 + 地点 + 城市价值
  3. 筛选 relevant + has_location
  4. 字段整理 + 脱敏
  5. 导出 L1 CSV
  6. 调用 L2 SnowNLP 分析

不再需要关键词层 (keyword_prefilter) 作为独立过滤步骤。
LLM 批量处理足够快且更准。

命名规范:
  L1 输出: {name}_L1_result_csv.csv (仅 relevant + has_location 的有效城市情绪数据)
  L2 输出: {name}_L2_result_csv.csv (SnowNLP 分析结果)

用法:
    python SCRIPT/data_governance.py
"""

import os
import sys
import builtins as _bi

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer, CRS

# 确保可导入 core 和 SCRIPT 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


# 修复 Windows GBK 控制台编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from core.coord_transform import gcj02_to_wgs84
from core.export import export_to_csv
from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id
from SCRIPT.emotion_analysis_v1 import run_analysis_task

# ═══════════════════════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'raw')
PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'processed')
BOUNDARY_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '规划范围')

# 输入文件
RAW_CSV = os.path.join(RAW_DIR, 'simulated_20260613_100k_raw.csv')

# 输出命名
L1_OUTPUT_NAME = 'simulated_20260613_规划范围'
L1_CSV_OUTPUT = os.path.join(PROCESSED_DIR, f'{L1_OUTPUT_NAME}_L1_result_csv.csv')

BUFFER_DISTANCE_M = 3000  # [DEPRECATED v2.0] LineString buffer距离，v2.0不再调用此函数

# ═══════════════════════════════════════════════════════════
# L1 字段定义 (v2.0)
# ═══════════════════════════════════════════════════════════

L1_COLUMNS = [
    # 标识
    'id_e',
    # 空间定位
    'scope', 'location_mentioned',
    # 核心内容
    'text', 'title', 'text_length',
    # 情绪分析
    'relevance', 'relevance_category', 'primary_emotion',
    'emotion_intensity', 'urban_value', 'ai_summary', 'ai_confidence',
    'filter_layer', 'has_location',
    # 社交指标
    'like_count', 'comment_count', 'tags',
    # 来源追溯
    'source', 'url', 'crawl_time', 'publish_time',
    # 坐标（最后，技术字段）
    'lon', 'lat', 'x_cgcs2000', 'y_cgcs2000',
]


# ═══════════════════════════════════════════════════════════
# 步骤 1: 加载原始数据 + 坐标转换
# ═══════════════════════════════════════════════════════════

@track("MOD_GOV.F_001", track_args=True)
def step1_load_and_transform(csv_path: str) -> pd.DataFrame:
    """
    加载原始 CSV，完成 GCJ-02 → WGS84 → CGCS2000 EPSG:4546 坐标转换。

    新增列: lon(原lon_wgs84), lat(原lat_wgs84), x_cgcs2000, y_cgcs2000
    保留原始 lon_gcj02, lat_gcj02 列不动。

    Returns:
        含转换后坐标的 DataFrame
    """
    _safe_print(f'[LOAD] 读取原始数据: {csv_path}')

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f'原始数据文件不存在: {csv_path}')

    df = pd.read_csv(csv_path, encoding='utf-8')
    _safe_print(f'[LOAD] 共加载 {len(df)} 条原始记录')

    # 兼容旧格式: 将 raw CSV 中的 lon/lat 重命名为 lon_gcj02/lat_gcj02
    df.rename(columns={'lon': 'lon_gcj02', 'lat': 'lat_gcj02'}, inplace=True)

    # 校验必需列
    required_cols = ['lon_gcj02', 'lat_gcj02']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f'原始 CSV 缺少必需列: {missing}')

    # ── 坐标转换: GCJ-02 → WGS84 ──
    _safe_print('[TRANSFORM] GCJ-02 → WGS84 (数学转换) ...')
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
            _safe_print(f'[WARN] 坐标转换失败 (行索引={_.name}): {e}, 标记为无效')
            wgs84_lons.append(None)
            wgs84_lats.append(None)

    df['lon'] = wgs84_lons
    df['lat'] = wgs84_lats
    _safe_print(f'[OK] WGS84 转换完成, 示例: ({df["lon"].iloc[0]}, {df["lat"].iloc[0]})')

    # ── 坐标投影: WGS84 → CGCS2000 EPSG:4546 ──
    _safe_print('[TRANSFORM] WGS84 → CGCS2000 EPSG:4546 (投影转换) ...')
    try:
        transformer = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
    except Exception as e:
        _safe_print(f'[ERR] 无法创建 pyproj Transformer: {e}')
        _safe_print('[WARN] 跳过 EPSG:4546 投影，x_cgcs2000/y_cgcs2000 将为空')
        df['x_cgcs2000'] = None
        df['y_cgcs2000'] = None
        return df

    x_cgcs = []
    y_cgcs = []
    for _, row in df.iterrows():
        try:
            x, y = transformer.transform(row['lon'], row['lat'])
            x_cgcs.append(round(x, 2))
            y_cgcs.append(round(y, 2))
        except Exception as e:
            _safe_print(f'[WARN] EPSG:4546 投影失败 (索引={_.name}): {e}')
            x_cgcs.append(None)
            y_cgcs.append(None)

    df['x_cgcs2000'] = x_cgcs
    df['y_cgcs2000'] = y_cgcs
    _safe_print(f'[OK] EPSG:4546 投影完成, 示例: ({df["x_cgcs2000"].iloc[0]}, {df["y_cgcs2000"].iloc[0]})')

    # 生成稳定行标识符
    df['id_e'] = 'e' + (df.index + 1).astype(str).str.zfill(4)
    _safe_print(f'[OK] 生成行标识符 id_e: e0001 ~ e{len(df):04d}')

    # 添加范围标识
    df['scope'] = '规划范围'
    _safe_print(f'[OK] 范围标识 scope = "规划范围"')

    return df


# ═══════════════════════════════════════════════════════════
# 步骤 2: 范围过滤
# ═══════════════════════════════════════════════════════════

@track("MOD_GOV.F_002", track_args=True)
def step2_filter_by_boundary(df: pd.DataFrame, shp_path: str) -> pd.DataFrame:
    """
    [DEPRECATED v2.0] 加载规划范围边界，buffer 生成 Polygon，用 WGS84 坐标过滤。

    边界为 LineString（EPSG:4546），需 buffer 3000m 转为 Polygon，
    再转为 EPSG:4326 与数据点的 WGS84 坐标做 point-in-polygon 判断。

    Returns:
        过滤后的 DataFrame（仅保留边界内的数据点）
    """
    _safe_print(f'[LOAD] 加载边界文件: {shp_path}')

    if not os.path.exists(shp_path):
        raise FileNotFoundError(f'边界文件不存在: {shp_path}')

    # 检查 .shx 伴生文件
    shx_path = shp_path[:-4] + '.shx'
    if not os.path.exists(shx_path):
        raise FileNotFoundError(
            f'Shapefile 缺少 .shx 索引文件: {shx_path}\n'
            f'请确保 .shp / .shx / .dbf 三个文件都在同一目录。'
        )

    try:
        gdf_boundary = gpd.read_file(shp_path)
    except Exception as e:
        _safe_print(f'[ERR] 边界文件读取失败: {e}')
        raise

    orig_crs = gdf_boundary.crs
    _safe_print(f'[LOAD] 边界 CRS: {orig_crs}')
    _safe_print(f'[LOAD] 边界几何类型: {[g.geom_type for g in gdf_boundary.geometry]}')
    _safe_print(f'[LOAD] 边界要素数: {len(gdf_boundary)}')

    # ── 校验边界 CRS 是否为投影坐标系（buffer 需要米制单位）──
    crs_obj = CRS.from_user_input(gdf_boundary.crs)
    if not crs_obj.is_projected:
        _safe_print(
            f'[ERR] 边界 CRS 为地理坐标系 ({gdf_boundary.crs})，'
            f'buffer 需要投影坐标系（单位为米）。'
        )
        _safe_print('[ERR] 请将边界转换为投影坐标系（如 EPSG:4546）后再使用。')
        raise ValueError(
            f'边界坐标系不是投影坐标系: {gdf_boundary.crs}。buffer 需要米制投影坐标系。'
        )

    # ── Buffer 3000m 生成 Polygon（在原投影坐标系下操作，单位=米）──
    _safe_print(f'[TRANSFORM] LineString → Polygon (buffer={BUFFER_DISTANCE_M}m) ...')
    try:
        gdf_boundary['geometry'] = gdf_boundary.geometry.buffer(BUFFER_DISTANCE_M)
        _safe_print(f'[OK] Buffer 后几何类型: {[g.geom_type for g in gdf_boundary.geometry]}')
    except Exception as e:
        _safe_print(f'[ERR] Buffer 操作失败: {e}')
        raise

    # ── 转为 EPSG:4326 用于 point-in-polygon ──
    _safe_print('[TRANSFORM] 边界 Polygon → EPSG:4326 ...')
    try:
        gdf_wgs84 = gdf_boundary.to_crs('EPSG:4326')
    except Exception as e:
        _safe_print(f'[ERR] 边界坐标系转换失败: {e}')
        raise

    # ── point-in-polygon 过滤 ──
    boundary_polygon = gdf_wgs84.union_all()  # 合并所有 Polygon 为一个几何体
    _safe_print(f'[LOAD] 合并后边界几何类型: {boundary_polygon.geom_type}')

    input_count = len(df)
    keep_mask = []
    for _, row in df.iterrows():
        try:
            lon = float(row['lon'])
            lat = float(row['lat'])
            pt = Point(lon, lat)
            keep_mask.append(boundary_polygon.contains(pt))
        except (ValueError, TypeError):
            keep_mask.append(False)

    df['in_scope'] = keep_mask
    df_filtered = df[df['in_scope']].copy()
    dropped_count = input_count - len(df_filtered)

    _safe_print(f'[OK] 范围过滤完成: {input_count} → {len(df_filtered)} 条 (过滤掉 {dropped_count} 条)')

    if df_filtered.empty:
        _safe_print('[WARN] 过滤后数据为空！请检查边界范围是否与数据点坐标匹配。')

    return df_filtered


# ═══════════════════════════════════════════════════════════
# 步骤 3: 数据脱敏 + 导出 L1
# ═══════════════════════════════════════════════════════════

@track("MOD_GOV.F_003", track_args=False)
def anonymize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    [DEPRECATED v2.0] 数据脱敏处理：清空敏感列（comments）。

    脱敏规则:
      - 清空 'comments' 列（可能包含其他用户评论中的个人身份信息）
      - 保留 'title' 和 'text'（公开发布内容）
      - 保留所有其他列

    Returns:
        脱敏后的 DataFrame（原地修改）
    """
    _safe_print('[ANONYMIZE] 数据脱敏处理...')

    sensitive_cols = ['comments']
    removed = []
    for col in sensitive_cols:
        if col in df.columns:
            df[col] = ''
            removed.append(col)

    if removed:
        _safe_print(f'[OK] 已清空敏感列: {removed}')
    else:
        _safe_print('[OK] 无需脱敏的列（comments 列不存在）')

    return df


@track("MOD_GOV.F_004", track_args=True)
def step3_export_filtered(df: pd.DataFrame, output_path: str) -> str:
    """
    [DEPRECATED v2.0] 导出过滤后数据 CSV（脱敏已在步骤 1 后完成，此处仅导出）。

    Returns:
        导出的 CSV 文件路径
    """
    _safe_print(f'[EXPORT] 导出过滤后数据: {output_path}')
    export_to_csv(df, output_path)

    return output_path


# ═══════════════════════════════════════════════════════════
# 步骤 4: 调用 L2 SnowNLP 分析
# ═══════════════════════════════════════════════════════════

@track("MOD_GOV.F_005", track_args=True)
def step4_run_l2_analysis(l1_csv_path: str, output_name: str) -> dict:
    """
    调用 emotion_analysis_v1.run_analysis_task() 执行 L2 SnowNLP 分析。

    Args:
        l1_csv_path: L1 治理后数据 CSV 路径
        output_name: 输出文件基础名

    Returns:
        run_analysis_task 返回的结果 dict
    """
    _safe_print(f'[L2] 启动 SnowNLP 情绪分析...')
    _safe_print(f'[L2] 输入: {l1_csv_path}')
    _safe_print(f'[L2] 输出基础名: {output_name}')

    result = run_analysis_task(
        file_path=l1_csv_path,
        engine_type='snownlp',
        output_name=output_name,
        enable_keywords=True,
    )

    if result['success']:
        _safe_print(f'\n[OK] L2 分析完成!')
        _safe_print(f'  数据条数: {result["n_points"]}')
        _safe_print(f'  综合得分均值: {result["score_mean"]}')
        _safe_print(f'  五级极性分布:')
        for pol, count in result.get('polarity_stats', {}).items():
            _safe_print(f'    {pol}: {count}')
        _safe_print(f'  CSV 输出: {result["csv_path"]}')
        _safe_print(f'  GeoJSON 输出: {result["geojson_path"]}')
    else:
        _safe_print(f'[ERR] L2 分析失败: {result["message"]}')

    return result


# ═══════════════════════════════════════════════════════════
# 主流程 (v2.0)
# ═══════════════════════════════════════════════════════════

@track("MOD_GOV.F_006", track_args=False)
def main():
    """L1 数据治理管道主入口 (v2.0)。

    流程:
      1. 加载原始数据 + 坐标转换
      2. 批量 DeepSeek LLM: relevance? + 五要素 + 情绪 + 地点 + 城市价值
      3. 筛选 relevant + has_location
      4. 字段整理
      5. 数据脱敏
      6. 导出 L1 CSV
      7. L2 SnowNLP 分析
    """
    _safe_print('=' * 60)
    _safe_print('  数据治理管道 v2.0 — L0 -> L1 -> L2')
    _safe_print('  (批量 LLM 一次完成筛选+分类)')
    _safe_print('=' * 60)

    # ── 步骤 1: 加载原始数据 + 坐标转换 ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 1/7] 加载原始数据 + 坐标转换')
    _safe_print('-' * 40)
    try:
        df = step1_load_and_transform(RAW_CSV)
    except Exception as e:
        trace_error("MOD_GOV.F_006", "step1 failed", exc=e)
        _safe_print(f'[ERR] 步骤 1 失败: {e}')
        sys.exit(1)

    # ── 步骤 2: 批量 LLM 筛选+分类 ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 2/7] 批量 LLM 筛选+分类 (DeepSeek)')
    _safe_print('-' * 40)

    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        _safe_print('[ERR] 需要设置 DEEPSEEK_API_KEY 环境变量')
        _safe_print('[ERR] PowerShell: $env:DEEPSEEK_API_KEY="sk-xxx"')
        sys.exit(1)

    # 准备发送给 LLM 的数据
    texts = []
    skipped_empty = 0
    for _, row in df.iterrows():
        title = str(row.get('title', '') or '').strip()
        text = str(row.get('text', '') or '').strip()
        content = f"{title} {text}".strip()
        if len(content) < 3:
            skipped_empty += 1
            continue
        texts.append({
            'id_e': row['id_e'],
            'text': text,
            'title': title,
            'source': str(row.get('source', '') or ''),
        })

    if skipped_empty > 0:
        _safe_print(f'[WARN] 跳过 {skipped_empty} 条空内容文本')

    _safe_print(f'[LOAD] 准备发送 {len(texts)} 条文本到 LLM (batch_size=50)')

    # 调用批量 LLM
    from SCRIPT.relevance_filter import llm_classify_batch

    def _progress_callback(current, total, message):
        pct = min(100, round(current / total * 100, 1))
        _safe_print(f'  [LOAD] {message} | {current}/{total} ({pct}%)')

    try:
        with TrackContext("MOD_GOV.D_004", total_texts=len(texts)):
            results = llm_classify_batch(
                texts,
                api_key=api_key,
                batch_size=50,
                progress_callback=_progress_callback,
            )
        trace_log("MOD_GOV.D_004", detail=f"LLM batch complete, got {len(results)} results")
    except Exception as e:
        trace_error("MOD_GOV.F_006", "batch LLM classify failed", exc=e)
        _safe_print(f'[ERR] 批量 LLM 分类失败: {e}')
        sys.exit(1)

    # ── 合并 LLM 结果到 df ──
    _safe_print('\n[MERGE] 合并 LLM 分类结果到 DataFrame ...')

    with TrackContext("MOD_GOV.D_005", n_results=len(results)):
        # 初始化新列
        for col in ['relevance', 'relevance_category', 'primary_emotion',
                     'emotion_intensity', 'has_location', 'location_mentioned',
                     'urban_value', 'ai_summary', 'ai_confidence']:
            if col not in df.columns:
                df[col] = None

        df['relevance'] = 'irrelevant'
        df['has_location'] = False
        df['emotion_intensity'] = 0
        df['ai_confidence'] = 0.0

        n_merged = 0
        for r in results:
            idx_list = df.index[df['id_e'] == r['id_e']]
            if len(idx_list) == 0:
                continue
            idx = idx_list[0]
            n_merged += 1

            df.at[idx, 'relevance'] = r.get('relevance', 'irrelevant')
            df.at[idx, 'relevance_category'] = r.get('relevance_category', '') or ''
            df.at[idx, 'primary_emotion'] = r.get('primary_emotion', '') or ''
            df.at[idx, 'emotion_intensity'] = int(r.get('emotion_intensity', 0) or 0)
            df.at[idx, 'has_location'] = bool(r.get('has_location', False))
            df.at[idx, 'location_mentioned'] = r.get('location_mentioned', '') or ''
            df.at[idx, 'urban_value'] = r.get('urban_value', 'low') or 'low'
            df.at[idx, 'ai_summary'] = r.get('ai_summary', '') or ''
            df.at[idx, 'ai_confidence'] = float(r.get('ai_confidence', 0.0) or 0.0)

        trace_log("MOD_GOV.D_005", detail=f"merged {n_merged} LLM results into df")

    # ── 统计 LLM 分类结果 ──
    n_relevant = int((df['relevance'] == 'relevant').sum())
    n_location = int(df['has_location'].sum())
    _safe_print(f'[OK] LLM 分类统计:')
    _safe_print(f'     relevant: {n_relevant} / {len(df)}')
    _safe_print(f'     has_location: {n_location} / {len(df)}')

    # ── 步骤 3: 筛选 relevant + has_location ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 3/7] 筛选 relevant + has_location')
    _safe_print('-' * 40)

    with TrackContext("MOD_GOV.D_006", input_n=len(df)):
        df_relevant = df[(df['relevance'] == 'relevant') & (df['has_location'] == True)].copy()
        trace_log("MOD_GOV.D_006",
                  detail=f"filtered: {len(df)} -> {len(df_relevant)} "
                         f"(relevant+has_location)")

    _safe_print(f'[OK] 筛选后保留: {len(df_relevant)} / {len(df)} 条')

    if df_relevant.empty:
        _safe_print('[WARN] 筛选后无数据（无 relevant + has_location 的记录）。')
        _safe_print('[WARN] 可能原因: LLM 判定所有文本为 irrelevant 或 has_location=false。')
        _safe_print('[WARN] 全量数据仍保留在 DataFrame 中（可手动检查）。')
        _safe_print('\n' + '=' * 60)
        _safe_print('  数据治理管道完成 (仅 L1, 无有效数据)!')
        _safe_print('=' * 60)
        _safe_print('')
        sys.exit(0)

    # ── 步骤 4: 字段整理 ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 4/7] 字段整理')
    _safe_print('-' * 40)

    df_relevant['text_length'] = df_relevant['text'].astype(str).str.len()

    # 选择 L1 列（仅保留存在的列）
    existing_cols = [c for c in L1_COLUMNS if c in df_relevant.columns]
    missing_cols = [c for c in L1_COLUMNS if c not in df_relevant.columns]
    if missing_cols:
        _safe_print(f'[WARN] L1_COLUMNS 中以下列不存在，已跳过: {missing_cols}')

    df_l1 = df_relevant[existing_cols].copy()
    _safe_print(f'[OK] L1 DataFrame 字段: {list(df_l1.columns)}')

    # ── 步骤 5: 脱敏 ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 5/7] 数据脱敏')
    _safe_print('-' * 40)

    if 'comments' in df_l1.columns:
        df_l1['comments'] = ''
        _safe_print('[OK] 已清空 comments 列')
    else:
        _safe_print('[OK] 无需脱敏（无 comments 列）')

    # ── 步骤 6: 导出 L1 ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 6/7] 导出 L1 CSV')
    _safe_print('-' * 40)

    try:
        export_to_csv(df_l1, L1_CSV_OUTPUT)
        _safe_print(f'[OK] L1 已保存: {L1_CSV_OUTPUT} ({len(df_l1)} 条)')
    except Exception as e:
        trace_error("MOD_GOV.F_006", "L1 export failed", exc=e)
        _safe_print(f'[ERR] L1 导出失败: {e}')
        sys.exit(1)

    # ── 步骤 7 (额外): L2 SnowNLP 分析 ──
    _safe_print('\n' + '-' * 40)
    _safe_print('[STEP 7/7] L2 SnowNLP 情绪分析')
    _safe_print('-' * 40)

    try:
        l2_result = step4_run_l2_analysis(L1_CSV_OUTPUT, L1_OUTPUT_NAME)
    except Exception as e:
        trace_error("MOD_GOV.F_006", "L2 analysis failed", exc=e)
        _safe_print(f'[ERR] L2 分析失败: {e}')
        sys.exit(1)

    # ── 汇总 ──
    _safe_print('\n' + '=' * 60)
    _safe_print('  数据治理管道完成!')
    _safe_print('=' * 60)
    _safe_print(f'  L0 输入:     {len(df)} 条')
    _safe_print(f'  LLM relevant: {n_relevant} 条')
    _safe_print(f'  L1 输出:     {L1_CSV_OUTPUT} ({len(df_l1)} 条)')
    if l2_result.get('success'):
        _safe_print(f'  L2 CSV:      {l2_result["csv_path"]}')
        _safe_print(f'  L2 GeoJSON:  {l2_result["geojson_path"]}')
    _safe_print('')


if __name__ == '__main__':
    main()

# ── 追踪 ID 注册表 ──
register_track_id("MOD_GOV.F_001", "步骤1: 加载原始数据 + GCJ-02->WGS84->CGCS2000坐标转换")
register_track_id("MOD_GOV.F_002", "[DEPRECATED v2.0] 范围过滤（v2.0已不再调用）")
register_track_id("MOD_GOV.F_003", "[DEPRECATED v2.0] 数据脱敏（v2.0已不再调用）")
register_track_id("MOD_GOV.F_004", "[DEPRECATED v2.0] 导出过滤后数据（v2.0已不再调用）")
register_track_id("MOD_GOV.F_005", "调用L2 SnowNLP分析管道")
register_track_id("MOD_GOV.F_006", "数据治理主入口 (v2.0: 批量LLM筛选+分类)")
register_track_id("MOD_GOV.D_004", "批量LLM分类调用 (llm_classify_batch)")
register_track_id("MOD_GOV.D_005", "合并LLM分类结果到DataFrame")
register_track_id("MOD_GOV.D_006", "筛选relevant+has_location")
