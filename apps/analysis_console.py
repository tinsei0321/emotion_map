"""
情绪分析控制台 v1.0 — Analysis Console
══════════════════════════════════════════════════════════════

启动: python launch.py                   # 一键启动全部（推荐）
      python launch.py --console         # 仅启动控制台
      python -m streamlit run apps/analysis_console.py --server.port 8502

功能:
  ① 上传/选择原始数据（CSV/GeoJSON）
  ② 选择分析引擎（L2/L3/L4）
  ③ 配置引擎参数
  ④ 实时进度查看
  ⑤ 结果预览（统计 + 图表）
  ⑥ 一键下载（CSV + GeoJSON）
  ⑦ 跳转到地图浏览器

══════════════════════════════════════════════════════════════
"""
import os, sys, json, time
from io import StringIO
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import RAW_DIR, PROCESSED_DIR
from SCRIPT.emotion_analysis_v1 import run_analysis_task

st.set_page_config(
    page_title='情绪分析控制台',
    page_icon='🔬',
    layout='wide',
)

# ═══════════════════════════════════════════════════════════
# 侧边栏 — 引擎配置
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    st.title('🔬 情绪分析控制台')

    st.divider()
    st.subheader('🧠 分析引擎')

    engine_choice = st.selectbox(
        '选择引擎',
        ['L2 · SnowNLP（离线/免费/快速）',
         'L3 · LLM 语义增强（需 API Key）',
         'L4 · 多维归因（需语料库 + API Key）',
         '🚀 全管道 L2→L3→L4'],
        help='L2 = 基础情绪分析\nL3 = L2 + 语义增强\nL4 = L3 + 因果归因\n全管道 = 顺序执行全部'
    )

    # ── 引擎参数 ──
    api_key = ''
    l3_api_key = ''
    l4_api_key = ''
    corpus_path = ''

    if 'LLM' in engine_choice or 'L3' in engine_choice:
        api_key = st.text_input(
            '🔑 API Key',
            type='password',
            placeholder='sk-...',
            help='支持 DeepSeek / Qwen / GLM / ERNIE / 讯飞'
        )

    if '全管道' in engine_choice:
        l3_api_key = st.text_input(
            '🔑 L3 API Key',
            type='password',
            placeholder='sk-...',
        )
        l4_api_key = st.text_input(
            '🔑 L4 API Key',
            type='password',
            placeholder='sk-...',
        )

    if 'L4' in engine_choice or '全管道' in engine_choice:
        corpus_path = st.text_input(
            '📚 语料库路径',
            placeholder='data/corpus/v1.json',
            help='多维归因语料库 JSON 文件路径'
        )

    st.divider()
    st.subheader('⚙ 分析选项')

    enable_keywords = st.checkbox('提取情绪关键词 (jieba)', value=True,
                                  help='每条文本提取 Top 5 关键词')

    st.divider()
    st.caption('v1.0 · L2/L3/L4 架构')
    st.caption(f'数据目录: `{RAW_DIR}/` → `{PROCESSED_DIR}/`')


# ═══════════════════════════════════════════════════════════
# 主区域 — 三步走
# ═══════════════════════════════════════════════════════════

st.title('🔬 情绪分析控制台')
st.caption('三步完成情绪分析：选数据 → 配引擎 → 跑分析 → 下载/查看')

# ── Step 1: 数据源 ──
st.subheader('📂 Step 1: 选择数据', divider='gray')

tab1, tab2 = st.tabs(['📁 从 raw 目录选择', '📤 上传新文件'])

with tab1:
    raw_files = []
    if os.path.exists(RAW_DIR):
        raw_files = sorted([
            f for f in os.listdir(RAW_DIR)
            if os.path.isfile(os.path.join(RAW_DIR, f))
            and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))
        ])
    if raw_files:
        file_choice = st.selectbox('原始数据文件', raw_files)
        input_path = os.path.join(RAW_DIR, file_choice)
        st.caption(f'完整路径: `{input_path}`')
    else:
        st.warning(f'`{RAW_DIR}/` 中没有可分析的文件，请上传或手动放入。')

with tab2:
    uploaded = st.file_uploader(
        '拖拽或点击上传',
        type=['csv', 'tsv', 'json', 'geojson'],
        help='需包含 comments（文本）和 lon/lat（坐标）列'
    )
    if uploaded:
        os.makedirs(RAW_DIR, exist_ok=True)
        save_path = os.path.join(RAW_DIR, uploaded.name)
        with open(save_path, 'wb') as f:
            f.write(uploaded.getbuffer())
        st.success(f'已保存: `{save_path}`')
        file_choice = uploaded.name
        input_path = save_path

# ── Step 2: 预览 ──
st.subheader('👀 Step 2: 数据预览', divider='gray')

if 'input_path' in dir() and input_path and os.path.exists(input_path):
    try:
        df_preview = pd.read_csv(input_path, nrows=5)
        st.dataframe(df_preview, width='stretch')
        st.caption(f'预览前 5 行 · 共 {len(pd.read_csv(input_path))} 条记录')

        # 检查必要列
        has_comments = 'comments' in pd.read_csv(input_path, nrows=1).columns
        has_lon = any(c in pd.read_csv(input_path, nrows=1).columns
                     for c in ['lon', 'longitude', 'lng'])
        has_lat = any(c in pd.read_csv(input_path, nrows=1).columns
                     for c in ['lat', 'latitude'])

        if not has_comments:
            st.warning('⚠️ 缺少 `comments` 列——情绪分析需要文本数据')
        if not (has_lon and has_lat):
            st.warning('⚠️ 缺少坐标列 `lon`/`lat`——无法在地图上展示')
    except Exception as e:
        st.error(f'无法预览: {e}')
else:
    st.info('👈 请先在 Step 1 选择或上传数据文件')

# ── Step 3: 运行 ──
st.subheader('🚀 Step 3: 运行分析', divider='gray')

output_name = st.text_input(
    '输出文件名（基础名，不含扩展名）',
    value=os.path.splitext(file_choice)[0] if 'file_choice' in dir() else 'analysis_output',
    help='将在 data/processed/ 下生成 {name}_L2_result_csv.csv 等文件（L2/L3/L4 自动识别）'
)

c1, c2, c3 = st.columns([1, 1, 3])
run_clicked = c1.button('🚀 开始分析', type='primary', use_container_width=True)

if run_clicked:
    if 'input_path' not in dir() or not input_path or not os.path.exists(input_path):
        st.error('请先选择或上传数据文件！')
    else:
        # ── 执行分析 ──
        progress_bar = st.progress(0, text='初始化…')

        try:
            # 确定引擎类型
            eng_type = 'snownlp'
            is_full = False
            if '全管道' in engine_choice:
                is_full = True
            elif 'L3' in engine_choice:
                eng_type = 'llm'
            elif 'L4' in engine_choice:
                eng_type = 'corpus'

            progress_bar.progress(20, text='分析中…')
            result = run_analysis_task(
                file_path=input_path,
                engine_type=eng_type,
                output_name=output_name,
                api_key=api_key,
                corpus_path=corpus_path,
                enable_keywords=enable_keywords,
                full_pipeline=is_full,
                l3_api_key=l3_api_key,
                l4_api_key=l4_api_key,
            )

            if result['success']:
                df = result['df']
                stats = result['polarity_stats']
                progress_bar.progress(100, text='✅ 完成！')
                st.success(f"🎉 {result['message']}")

                # ── 结果预览 ──
                st.subheader('📊 分析结果', divider='gray')

                neg = stats['Negative']; vneg = stats['Very Negative']
                pos = stats['Positive']; vpos = stats['Very Positive']
                total = result['n_points']

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric('🟢 非常正面', vpos)
                m2.metric('✅ 正面', pos)
                m3.metric('➖ 中性', stats['Neutral'])
                m4.metric('⚠️ 负面', neg)
                m5.metric('🔴 非常负面', vneg)

                st.caption(
                    f"得分均值: **{result['score_mean']}** · "
                    f"需干预: **{neg + vneg}** 条 ({(neg+vneg)/total*100:.1f}%) · "
                    f"标杆: **{vpos}** 条 ({vpos/total*100:.1f}%)"
                )

                # 极性柱状图
                import altair as alt
                pol_order = ['Very Negative','Negative','Neutral',
                             'Positive','Very Positive']
                pol_colors = ['#dc3545','#e8590c','#6c757d','#28a745','#1a7a1a']
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X('polarity:N', title=None, sort=pol_order),
                    y=alt.Y('count()', title=None),
                    color=alt.Color('polarity:N',
                        scale=alt.Scale(domain=pol_order, range=pol_colors),
                        legend=None)
                ).properties(height=250)
                st.altair_chart(chart, width='stretch')

                # ── 下载 & 跳转 ──
                st.subheader('📥 导出 & 下一步', divider='gray')

                d1, d2, d3 = st.columns(3)
                if os.path.exists(result['csv_path']):
                    with open(result['csv_path'], 'rb') as f:
                        d1.download_button(
                            '⬇ 下载 CSV', f.read(),
                            file_name=os.path.basename(result['csv_path']),
                            mime='text/csv', use_container_width=True,
                        )
                if result['geojson_path'] and os.path.exists(result['geojson_path']):
                    with open(result['geojson_path'], 'rb') as f:
                        d2.download_button(
                            '⬇ 下载 GeoJSON', f.read(),
                            file_name=os.path.basename(result['geojson_path']),
                            mime='application/geo+json', use_container_width=True,
                        )

                d3.markdown(
                    '✅ 数据已保存到 `data/processed/`',
                    help='分析结果已自动导出为 CSV + GeoJSON'
                )

                # 数据表预览
                with st.expander('📋 查看数据表（前 100 行）'):
                    cols_to_show = [c for c in df.columns
                                    if c not in ['geometry']]
                    st.dataframe(df[cols_to_show].head(100), width='stretch')

            else:
                progress_bar.progress(100, text='❌ 失败')
                st.error(result['message'])

        except Exception as e:
            st.error(f'❌ 分析出错: {e}')
            st.exception(e)
