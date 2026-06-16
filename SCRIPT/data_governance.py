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
    python SCRIPT/data_governance.py                          # 使用默认路径
    python SCRIPT/data_governance.py --input DATA/raw/my_data.csv --output my_project
"""

import argparse
import os
import sys
from typing import Optional

import pandas as pd
from pyproj import Transformer

# 确保可导入 core 和 SCRIPT 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 修复 Windows GBK 控制台编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from core.coord_transform import gcj02_to_wgs84
from core.export import export_to_csv
from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id
from core.utils import safe_print
from SCRIPT.emotion_analysis_v1 import run_analysis_task

# ═══════════════════════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'raw')
PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'processed')
BOUNDARY_DIR = os.path.join(PROJECT_ROOT, 'DATA', 'boundaries', '规划范围')

# 默认路径（可通过 CLI 参数覆盖）
DEFAULT_RAW_CSV = os.path.join(RAW_DIR, 'simulated_20260613_100k_raw.csv')
DEFAULT_OUTPUT_NAME = 'simulated_20260613_规划范围'

# ═══════════════════════════════════════════════════════════
# L1 字段定义 (v2.0)
# ═══════════════════════════════════════════════════════════

L1_COLUMNS = [
    # ① 标识
    'id_e',
    # ② 时间
    'publish_time', 'crawl_time',
    # ③ 空间
    'scope', 'location_mentioned', 'poi', 'lon', 'lat',
    # ④ 原始内容
    'title', 'text', 'text_length', 'tags',
    # ⑤ 相关性判定（L1 治理结果）
    'relevance', 'relevance_category', 'filter_layer', 'has_location',
    # ⑥ 情绪分析（L1 LLM 产出）
    'primary_emotion', 'emotion_intensity', 'urban_value', 'ai_summary', 'l1_confidence',
    # ⑦ 社交指标
    'like_count', 'comment_count',
    # ⑧ 溯源
    'source', 'url',
    # ⑨ 技术坐标（按需使用）
    'x_cgcs2000', 'y_cgcs2000',
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
    safe_print(f'[LOAD] 读取原始数据: {csv_path}')

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f'原始数据文件不存在: {csv_path}')

    df = pd.read_csv(csv_path, encoding='utf-8')
    safe_print(f'[LOAD] 共加载 {len(df)} 条原始记录')

    # 兼容旧格式: 将 raw CSV 中的 lon/lat 重命名为 lon_gcj02/lat_gcj02
    df.rename(columns={'lon': 'lon_gcj02', 'lat': 'lat_gcj02'}, inplace=True)

    # 校验必需列
    required_cols = ['lon_gcj02', 'lat_gcj02']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f'原始 CSV 缺少必需列: {missing}')

    # ── 坐标转换: GCJ-02 → WGS84 ──
    safe_print('[TRANSFORM] GCJ-02 → WGS84 (数学转换) ...')
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
            safe_print(f'[WARN] 坐标转换失败 (行索引={_.name}): {e}, 标记为无效')
            wgs84_lons.append(None)
            wgs84_lats.append(None)

    df['lon'] = wgs84_lons
    df['lat'] = wgs84_lats
    safe_print(f'[OK] WGS84 转换完成, 示例: ({df["lon"].iloc[0]}, {df["lat"].iloc[0]})')

    # ── 坐标投影: WGS84 → CGCS2000 EPSG:4546 ──
    safe_print('[TRANSFORM] WGS84 → CGCS2000 EPSG:4546 (投影转换) ...')
    try:
        transformer = Transformer.from_crs('EPSG:4326', 'EPSG:4546', always_xy=True)
    except Exception as e:
        safe_print(f'[ERR] 无法创建 pyproj Transformer: {e}')
        safe_print('[WARN] 跳过 EPSG:4546 投影，x_cgcs2000/y_cgcs2000 将为空')
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
            safe_print(f'[WARN] EPSG:4546 投影失败 (索引={_.name}): {e}')
            x_cgcs.append(None)
            y_cgcs.append(None)

    df['x_cgcs2000'] = x_cgcs
    df['y_cgcs2000'] = y_cgcs
    safe_print(f'[OK] EPSG:4546 投影完成, 示例: ({df["x_cgcs2000"].iloc[0]}, {df["y_cgcs2000"].iloc[0]})')

    # 生成稳定行标识符
    df['id_e'] = 'e' + (df.index + 1).astype(str).str.zfill(4)
    safe_print(f'[OK] 生成行标识符 id_e: e0001 ~ e{len(df):04d}')

    # 添加范围标识
    df['scope'] = '规划范围'
    safe_print(f'[OK] 范围标识 scope = "规划范围"')

    return df


# ═══════════════════════════════════════════════════════════
# 步骤 2: 调用 L2 SnowNLP 分析
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
    safe_print(f'[L2] 启动 SnowNLP 情绪分析...')
    safe_print(f'[L2] 输入: {l1_csv_path}')
    safe_print(f'[L2] 输出基础名: {output_name}')

    result = run_analysis_task(
        file_path=l1_csv_path,
        engine_type='snownlp',
        output_name=output_name,
        enable_keywords=True,
    )

    if result['success']:
        safe_print(f'\n[OK] L2 分析完成!')
        safe_print(f'  数据条数: {result["n_points"]}')
        safe_print(f'  综合得分均值: {result["score_mean"]}')
        safe_print(f'  五级极性分布:')
        for pol, count in result.get('polarity_stats', {}).items():
            safe_print(f'    {pol}: {count}')
        safe_print(f'  CSV 输出: {result["csv_path"]}')
        safe_print(f'  GeoJSON 输出: {result["geojson_path"]}')
    else:
        safe_print(f'[ERR] L2 分析失败: {result["message"]}')

    return result


# ═══════════════════════════════════════════════════════════
# 主流程 (v2.0) — API/CLI 共用的治理管道 + CLI 薄包装
# ═══════════════════════════════════════════════════════════

@track("MOD_GOV.F_007", track_args=True)
def run_governance_pipeline(
    csv_path: str,
    output_name: str,
    boundary_path: Optional[str] = None,
    run_l2: bool = False,
    api_key: Optional[str] = None,
    progress_callback=None,
) -> dict:
    """L0→L1 治理主管道（API/CLI 共用，永不 sys.exit）。

    流程:
      1. 加载原始数据 + 坐标转换 (GCJ-02 → WGS84 → CGCS2000 EPSG:4546)
      2. (可选) 空间范围过滤 — 铁律8「空间范围优先」
      3. 批量 DeepSeek LLM 一次完成: relevance? + 五要素 + 情绪 + 地点 + 城市价值
      4. 筛选 relevant + has_location
      5. 字段整理 + 脱敏
      6. 导出 L1 CSV
      7. (可选, run_l2=True) L2 SnowNLP 分析

    参数:
        csv_path:    L0 原始 CSV 路径
        output_name: L1/L2 输出命名前缀
        boundary_path: 可选，规划范围矢量文件路径；提供则先做空间过滤
        run_l2:      是否继续跑 L2 SnowNLP 分析
        api_key:     DeepSeek API Key；为 None 时回退环境变量 DEEPSEEK_API_KEY，
                     仍无则**明确报错返回**（不静默降级为 keyword-only）
        progress_callback: 可选 (current, total, message) -> None

    返回:
        {success, input_n, spatial_n, relevant_n, output_n, l1_path, l2_result, message}
    """
    result = {
        'success': False, 'input_n': 0, 'spatial_n': 0,
        'relevant_n': 0, 'output_n': 0,
        'l1_path': '', 'l2_result': None, 'message': '',
    }
    l1_csv_output = os.path.join(PROCESSED_DIR, f'{output_name}_L1_result_csv.csv')

    safe_print('=' * 60)
    safe_print('  数据治理管道 — L0 -> L1' + (' -> L2' if run_l2 else ''))
    safe_print(f'  输入: {csv_path}')
    safe_print(f'  输出: {output_name}')
    safe_print('=' * 60)

    # ── 步骤 1: 加载 + 坐标转换 ──
    try:
        df = step1_load_and_transform(csv_path)
    except Exception as e:
        trace_error("MOD_GOV.F_007", "step1 failed", exc=e)
        result['message'] = f'步骤1失败: {e}'
        return result
    result['input_n'] = len(df)

    # ── 步骤 2: (可选) 空间范围过滤 — 铁律8 空间范围优先 ──
    spatial_n = len(df)
    if boundary_path and os.path.exists(boundary_path):
        safe_print(f'[FILTER] 空间范围过滤: {boundary_path}')
        try:
            from core.range_selector import load_boundaries, filter_by_range
            ranges = load_boundaries(boundary_path)
            df_filtered = filter_by_range(df, 'lon', 'lat', ranges, None)
            df = pd.DataFrame(df_filtered)
            spatial_n = len(df)
            safe_print(f'[OK] 空间过滤后保留: {spatial_n} / {result["input_n"]} 条')
        except Exception as e:
            trace_error("MOD_GOV.F_007", "spatial filter failed", exc=e)
            result['message'] = f'空间过滤失败: {e}'
            return result
    result['spatial_n'] = spatial_n

    if spatial_n == 0:
        result['success'] = True  # 非错误，仅空结果
        result['message'] = '空间过滤后无数据'
        return result

    # ── API Key 解析（不静默降级为 keyword-only）──
    resolved_key = api_key or os.environ.get('DEEPSEEK_API_KEY', '')
    if not resolved_key:
        msg = ('需要 DeepSeek API Key（LLM 相关性分类）。\n'
               '设置 DEEPSEEK_API_KEY 环境变量或传入 api_key 参数。\n'
               'PowerShell: $env:DEEPSEEK_API_KEY="sk-xxx"')
        safe_print(f'[ERR] {msg}')
        result['message'] = msg
        return result

    # ── 步骤 3: 批量 LLM 筛选+分类 ──
    safe_print('[STEP] 批量 LLM 筛选+分类 (DeepSeek)')
    texts = []
    for _, row in df.iterrows():
        title = str(row.get('title', '') or '').strip()
        text = str(row.get('text', '') or '').strip()
        content = f'{title} {text}'.strip()
        if len(content) < 3:
            continue
        texts.append({'id_e': row['id_e'], 'text': text, 'title': title,
                      'source': str(row.get('source', '') or '')})
    safe_print(f'[LOAD] 准备发送 {len(texts)} 条文本到 LLM (batch_size=50)')
    if not texts:
        result['success'] = True
        result['message'] = '无有效文本可分类'
        return result

    from SCRIPT.relevance_filter import llm_classify_batch
    try:
        with TrackContext("MOD_GOV.D_004", total_texts=len(texts)):
            results = llm_classify_batch(
                texts, api_key=resolved_key, batch_size=50,
                progress_callback=progress_callback,
            )
        trace_log("MOD_GOV.D_004", detail=f"LLM batch complete, {len(results)} results")
    except Exception as e:
        trace_error("MOD_GOV.F_007", "batch LLM classify failed", exc=e)
        result['message'] = f'批量 LLM 分类失败: {e}'
        return result

    # ── 合并 LLM 结果到 df ──
    with TrackContext("MOD_GOV.D_005", n_results=len(results)):
        for col in ['relevance', 'relevance_category', 'primary_emotion',
                    'emotion_intensity', 'has_location', 'location_mentioned',
                    'urban_value', 'ai_summary', 'l1_confidence']:
            if col not in df.columns:
                df[col] = None
        df['relevance'] = 'irrelevant'
        df['has_location'] = False
        df['emotion_intensity'] = 0
        df['l1_confidence'] = 0.0
        for r in results:
            idx_list = df.index[df['id_e'] == r['id_e']]
            if len(idx_list) == 0:
                continue
            idx = idx_list[0]
            df.at[idx, 'relevance'] = r.get('relevance', 'irrelevant')
            df.at[idx, 'relevance_category'] = r.get('relevance_category', '') or ''
            df.at[idx, 'primary_emotion'] = r.get('primary_emotion', '') or ''
            df.at[idx, 'emotion_intensity'] = int(r.get('emotion_intensity', 0) or 0)
            df.at[idx, 'has_location'] = bool(r.get('has_location', False))
            df.at[idx, 'location_mentioned'] = r.get('location_mentioned', '') or ''
            df.at[idx, 'urban_value'] = r.get('urban_value', 'low') or 'low'
            df.at[idx, 'ai_summary'] = r.get('ai_summary', '') or ''
            df.at[idx, 'l1_confidence'] = float(r.get('ai_confidence', 0.0) or 0.0)

    n_relevant = int((df['relevance'] == 'relevant').sum())
    result['relevant_n'] = n_relevant
    safe_print(f'[OK] relevant: {n_relevant} / {len(df)}')

    # ── 步骤 4: 筛选 relevant + has_location ──
    with TrackContext("MOD_GOV.D_006", input_n=len(df)):
        df_relevant = df[(df['relevance'] == 'relevant') & (df['has_location'] == True)].copy()
    safe_print(f'[OK] 筛选后保留: {len(df_relevant)} / {len(df)} 条')

    if df_relevant.empty:
        result['success'] = True
        result['message'] = '无 relevant + has_location 记录，未产出 L1'
        return result

    # ── 步骤 5: 字段整理 + 脱敏 ──
    df_relevant['text_length'] = df_relevant['text'].astype(str).str.len()
    existing_cols = [c for c in L1_COLUMNS if c in df_relevant.columns]
    missing_cols = [c for c in L1_COLUMNS if c not in df_relevant.columns]
    if missing_cols:
        safe_print(f'[WARN] L1_COLUMNS 缺失列已跳过: {missing_cols}')
    df_l1 = df_relevant[existing_cols].copy()
    if 'comments' in df_l1.columns:
        df_l1['comments'] = ''

    # ── 步骤 6: 导出 L1 ──
    try:
        export_to_csv(df_l1, l1_csv_output)
    except Exception as e:
        trace_error("MOD_GOV.F_007", "L1 export failed", exc=e)
        result['message'] = f'L1 导出失败: {e}'
        return result

    result['output_n'] = len(df_l1)
    result['l1_path'] = l1_csv_output
    result['success'] = True
    result['message'] = (f'L1 治理完成: {result["input_n"]} → '
                         f'{result["output_n"]} 条 (relevant {n_relevant})')

    # ── 步骤 7: (可选) L2 SnowNLP ──
    if run_l2:
        try:
            l2_result = step4_run_l2_analysis(l1_csv_output, output_name)
            result['l2_result'] = l2_result
        except Exception as e:
            trace_error("MOD_GOV.F_007", "L2 analysis failed", exc=e)
            # L1 已成功，L2 失败不回滚整体
            result['message'] += f'；L2 分析失败: {e}'

    safe_print(f'[OK] {result["message"]}')
    return result


@track("MOD_GOV.F_006", track_args=False)
def main(csv_path=None, output_name=None):
    """L1 数据治理管道 CLI 入口（薄包装，调用 run_governance_pipeline）。

    CLI 不做空间过滤（假设原始 CSV 已在规划范围内）；需要空间过滤请用
    API /api/v1/governance 或直接调 run_governance_pipeline(boundary_path=...)。
    """
    csv_path = csv_path or DEFAULT_RAW_CSV
    output_name = output_name or DEFAULT_OUTPUT_NAME

    result = run_governance_pipeline(
        csv_path=csv_path,
        output_name=output_name,
        boundary_path=None,
        run_l2=True,
    )

    if not result['success']:
        safe_print(f'[ERR] {result["message"]}')
        sys.exit(1)

    safe_print('\n' + '=' * 60)
    safe_print('  数据治理管道完成!')
    safe_print('=' * 60)
    safe_print(f'  L0 输入:      {result["input_n"]} 条')
    safe_print(f'  LLM relevant: {result["relevant_n"]} 条')
    safe_print(f'  L1 输出:      {result["l1_path"]} ({result["output_n"]} 条)')
    l2 = result.get('l2_result') or {}
    if l2.get('success'):
        safe_print(f'  L2 CSV:       {l2.get("csv_path", "")}')
        safe_print(f'  L2 GeoJSON:   {l2.get("geojson_path", "")}')
    safe_print('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='数据治理管道 v2.0 — L0 → L1 → L2')
    parser.add_argument('--input', type=str, default=None,
                        help=f'L0 原始 CSV 路径 (默认: {DEFAULT_RAW_CSV})')
    parser.add_argument('--output', type=str, default=None,
                        help=f'输出命名前缀 (默认: {DEFAULT_OUTPUT_NAME})')
    args = parser.parse_args()
    main(csv_path=args.input, output_name=args.output)

# ── 追踪 ID 注册表 ──
register_track_id("MOD_GOV.F_001", "步骤1: 加载原始数据 + GCJ-02->WGS84->CGCS2000坐标转换")
register_track_id("MOD_GOV.F_005", "调用L2 SnowNLP分析管道")
register_track_id("MOD_GOV.F_006", "数据治理CLI入口 (薄包装, 调用 run_governance_pipeline)")
register_track_id("MOD_GOV.F_007", "L0->L1治理主管道 (API/CLI共用, run_governance_pipeline, 含LLM漏斗)")
register_track_id("MOD_GOV.D_004", "批量LLM分类调用 (llm_classify_batch)")
register_track_id("MOD_GOV.D_005", "合并LLM分类结果到DataFrame")
register_track_id("MOD_GOV.D_006", "筛选relevant+has_location")
