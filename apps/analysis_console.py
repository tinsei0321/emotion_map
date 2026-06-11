"""
情绪分析控制台 v1.0 — Analysis Console
══════════════════════════════════════════════════════════════

启动: python launch.py                   # 一键启动全部（推荐）
      python launch.py --console         # 仅启动控制台
      python -m streamlit run apps/analysis_console.py --server.port 8502

支持从地图浏览器跳转（自动加载结果）：
  http://localhost:8502?file=data/processed/xxx_L2_result_csv.csv

══════════════════════════════════════════════════════════════
"""
import os, sys, json, time
from io import StringIO
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import RAW_DIR, PROCESSED_DIR
from core.data_loader import load_emotion_data
from SCRIPT.emotion_analysis_v1 import run_analysis_task

st.set_page_config(
    page_title='情绪分析控制台',
    page_icon='🔬',
    layout='wide',
)

# ═══════════════════════════════════════════════════════════
# 读取 URL 参数 — 是否从地图浏览器跳转过来
# ═══════════════════════════════════════════════════════════
auto_file = st.query_params.get('file', None)
auto_loaded_df = None
auto_loaded_stats = None
auto_loaded_score = 0.0
auto_loaded_n = 0
is_auto_mode = False

if auto_file and os.path.exists(auto_file):
    try:
        data = load_emotion_data(auto_file)
        if data:
            auto_loaded_df = data['df']
            auto_loaded_n = data['n_points']
            if 'polarity' in auto_loaded_df.columns:
                auto_loaded_stats = {
                    'Very Positive': int((auto_loaded_df['polarity'] == 'Very Positive').sum()),
                    'Positive':      int((auto_loaded_df['polarity'] == 'Positive').sum()),
                    'Neutral':       int((auto_loaded_df['polarity'] == 'Neutral').sum()),
                    'Negative':      int((auto_loaded_df['polarity'] == 'Negative').sum()),
                    'Very Negative': int((auto_loaded_df['polarity'] == 'Very Negative').sum()),
                }
            if 'score' in auto_loaded_df.columns:
                auto_loaded_score = round(float(auto_loaded_df['score'].mean()), 2)
            is_auto_mode = True
    except Exception:
        pass  # 加载失败则回退到普通模式


# ═══════════════════════════════════════════════════════════
# 侧边栏 — 新文件分析 + 导出
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    st.title('情绪分析控制台')

    if is_auto_mode:
        st.success(f'已加载: {os.path.basename(auto_file)}')
        st.caption(f'{auto_loaded_n} 条数据')

    st.divider()
    st.subheader('新文件分析')

    engine_choice = st.selectbox(
        '选择引擎',
        ['L2 · SnowNLP', 'L3 · LLM 语义增强', 'L4 · 多维归因', '全管道 L2-L3-L4'],
    )

    api_key = ''
    corpus_path = ''
    if 'L3' in engine_choice or 'L4' in engine_choice:
        api_key = st.text_input('API Key', type='password', placeholder='sk-...')
    if 'L4' in engine_choice or '全管道' in engine_choice:
        corpus_path = st.text_input('语料库路径', placeholder='data/corpus/v1.json')

    enable_keywords = st.checkbox('提取关键词 (jieba)', value=True)

    st.divider()
    st.caption('v1.0 · L2/L3/L4')


# ═══════════════════════════════════════════════════════════
# 主区域
# ═══════════════════════════════════════════════════════════

st.title('情绪分析控制台')

# ── 模式 A: 自动加载模式（从地图跳转过来）──
if is_auto_mode and auto_loaded_df is not None:
    st.caption(f'文件: `{auto_file}` | {auto_loaded_n} 条记录')

    # 结果统计 — 折叠面板
    if auto_loaded_stats:
        with st.expander(f'📊 分析结果 · {auto_loaded_n} 条数据', expanded=True):
            stats = auto_loaded_stats
            neg = stats['Negative']; vneg = stats['Very Negative']
            pos = stats['Positive']; vpos = stats['Very Positive']
            total = auto_loaded_n

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric('非常正面', vpos)
            m2.metric('正面', pos)
            m3.metric('中性', stats['Neutral'])
            m4.metric('负面', neg)
            m5.metric('非常负面', vneg)

            st.caption(
                f"均分 {auto_loaded_score} | "
                f"需干预 {neg + vneg} 条 ({(neg+vneg)/total*100:.1f}%) | "
                f"标杆 {vpos} 条 ({vpos/total*100:.1f}%)"
            )

            import altair as alt
            pol_order = ['Very Negative','Negative','Neutral','Positive','Very Positive']
            pol_colors = ['#dc3545','#e8590c','#6c757d','#28a745','#1a7a1a']
            chart = alt.Chart(auto_loaded_df).mark_bar().encode(
                x=alt.X('polarity:N', title=None, sort=pol_order),
                y=alt.Y('count()', title=None),
                color=alt.Color('polarity:N',
                    scale=alt.Scale(domain=pol_order, range=pol_colors), legend=None)
            ).properties(height=250)
            st.altair_chart(chart, width='stretch')

            # 数据表
            with st.expander('查看数据表（前 100 行）'):
                cols = [c for c in auto_loaded_df.columns if c not in ['geometry']]
                st.dataframe(auto_loaded_df[cols].head(100), width='stretch')

    # 导出
    st.subheader('导出', divider='gray')
    d1, d2, _ = st.columns(3)
    if os.path.exists(auto_file):
        with open(auto_file, 'rb') as f:
            d1.download_button('下载 CSV', f.read(),
                file_name=os.path.basename(auto_file), mime='text/csv',
                use_container_width=True)
    geojson_path = auto_file.replace('_csv.csv', '_geojson.geojson')
    if os.path.exists(geojson_path):
        with open(geojson_path, 'rb') as f:
            d2.download_button('下载 GeoJSON', f.read(),
                file_name=os.path.basename(geojson_path),
                mime='application/geo+json', use_container_width=True)

    st.divider()

# ── 模式 B: 分析新文件 ──
st.subheader('选择新数据文件', divider='gray')

tab1, tab2 = st.tabs(['从 raw 目录选择', '上传新文件'])

new_file_selected = False
input_path = ''

with tab1:
    raw_files = []
    if os.path.exists(RAW_DIR):
        raw_files = sorted([
            f for f in os.listdir(RAW_DIR)
            if os.path.isfile(os.path.join(RAW_DIR, f))
            and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))
            and '_result_' not in f  # 排除已分析结果文件
        ])
    if raw_files:
        file_choice = st.selectbox('原始数据文件', raw_files, key='raw_select')
        input_path = os.path.join(RAW_DIR, file_choice)
        st.caption(f'`{input_path}`')
        new_file_selected = True
    else:
        st.info('无可用原始文件')

with tab2:
    uploaded = st.file_uploader('上传文件', type=['csv', 'tsv', 'json', 'geojson'])
    if uploaded:
        os.makedirs(RAW_DIR, exist_ok=True)
        save_path = os.path.join(RAW_DIR, uploaded.name)
        with open(save_path, 'wb') as f:
            f.write(uploaded.getbuffer())
        st.success(f'已保存')
        input_path = save_path
        new_file_selected = True

# ── 预览 ──
if new_file_selected and input_path and os.path.exists(input_path):
    try:
        df_p = pd.read_csv(input_path, nrows=5)
        st.caption(f'预览 {len(df_p)} 行')

        has_com = 'comments' in df_p.columns
        has_lon = any(c in df_p.columns for c in ['lon','longitude','lng'])
        has_lat = any(c in df_p.columns for c in ['lat','latitude'])

        if not has_com:
            st.warning('缺少 comments 列')
        if not (has_lon and has_lat):
            st.warning('缺少坐标列')
    except Exception:
        pass

# ── 开始分析按钮（仅当选择了新文件时显示）──
if new_file_selected and input_path:
    st.divider()
    output_name = st.text_input(
        '输出文件名', value=os.path.splitext(os.path.basename(input_path))[0],
    )
    if st.button('开始分析', type='primary'):
        eng_type = 'snownlp'
        is_full = False
        if 'L3' in engine_choice:
            eng_type = 'llm'
        elif 'L4' in engine_choice:
            eng_type = 'corpus'
        elif '全管道' in engine_choice:
            is_full = True

        l3_key = api_key if is_full else ''
        l4_key = api_key if is_full else ''

        with st.status('分析中...', expanded=True) as status:
            result = run_analysis_task(
                file_path=input_path,
                engine_type=eng_type,
                output_name=output_name,
                api_key=api_key,
                corpus_path=corpus_path,
                enable_keywords=enable_keywords,
                full_pipeline=is_full,
                l3_api_key=l3_key,
                l4_api_key=l4_key,
            )
            if result['success']:
                status.update(label=f'完成！{result["n_points"]} 条', state='complete')
                st.rerun()
            else:
                status.update(label='失败', state='error')
                st.error(result['message'])
