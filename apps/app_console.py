"""
分析控制台页面 (Analysis Console Page)
═══════════════════════════════════════
Streamlit 子页面，路由: ?page=console

功能:
  - 模式 A: URL 参数自动加载 (?file=xxx) → 展示结果
  - 模式 B: 选择/上传数据文件 → 运行 SnowNLP/L3/L4 分析
"""
import os
import streamlit as st
import streamlit.components.v1 as components

from core.config import FOLDER_OPTIONS, PROCESSED_DIR
from core.data_loader import load_emotion_data
from core.ui_components import render_polarity_stats, render_polarity_chart
from SCRIPT.emotion_analysis_v1 import run_analysis_task
from core.layer_registry import register_layer
from core.tracker import track
from core.utils import safe_print


def _parse_console_params():
    """解析 URL 参数，返回自动加载模式的数据上下文。

    返回 dict:
        auto_file, auto_loaded_df, auto_loaded_n, auto_loaded_score,
        auto_loaded_stats, is_auto_mode
    """
    result = {
        'auto_file': None,
        'auto_loaded_df': None,
        'auto_loaded_n': 0,
        'auto_loaded_score': 0.0,
        'auto_loaded_stats': None,
        'is_auto_mode': False,
    }

    auto_file = st.query_params.get('file', None)
    if not auto_file or not os.path.exists(auto_file):
        return result

    try:
        data = load_emotion_data(auto_file)
        if data:
            auto_loaded_df = data['df']
            auto_loaded_stats = None
            auto_loaded_score = 0.0
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

            result.update({
                'auto_file': auto_file,
                'auto_loaded_df': auto_loaded_df,
                'auto_loaded_n': data['n_points'],
                'auto_loaded_score': auto_loaded_score,
                'auto_loaded_stats': auto_loaded_stats,
                'is_auto_mode': True,
            })
    except Exception:
        safe_print(f'[WARN] 无法加载自动文件: {auto_file}')

    return result


def _render_console_sidebar(params: dict):
    """渲染分析控制台侧边栏，返回引擎配置。

    返回 dict:
        engine_choice, api_key, corpus_path, enable_keywords
    """
    with st.sidebar:
        if params['is_auto_mode']:
            st.success(f'已加载: {os.path.basename(params["auto_file"])}')
            st.caption(f'{params["auto_loaded_n"]} 条数据')
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
        st.caption('v1.0')
        st.markdown('[返回地图浏览器](/)')

    return {
        'engine_choice': engine_choice,
        'api_key': api_key,
        'corpus_path': corpus_path,
        'enable_keywords': enable_keywords,
    }


def _render_auto_loaded_view(params: dict):
    """模式 A: 展示自动加载的分析结果（含极性统计/图表/导出/数据表）。"""
    auto_file = params['auto_file']
    auto_loaded_df = params['auto_loaded_df']
    auto_loaded_n = params['auto_loaded_n']
    auto_loaded_score = params['auto_loaded_score']
    auto_loaded_stats = params['auto_loaded_stats']

    if auto_loaded_df is None:
        return

    st.caption(f'文件: `{auto_file}` | {auto_loaded_n} 条记录')
    if auto_loaded_stats and 'polarity' in auto_loaded_df.columns:
        with st.expander(f'分析结果 · {auto_loaded_n} 条数据', expanded=True):
            render_polarity_stats(auto_loaded_df, show_score=True)
            render_polarity_chart(auto_loaded_df, height=250)
            with st.expander('查看数据表（前 100 行）'):
                cols = [c for c in auto_loaded_df.columns if c not in ['geometry']]
                st.dataframe(auto_loaded_df[cols].head(100), width='stretch')

    st.subheader('导出', divider='gray')
    d1, d2, _ = st.columns(3)
    if os.path.exists(auto_file):
        with open(auto_file, 'rb') as f:
            d1.download_button('下载 CSV', f.read(), file_name=os.path.basename(auto_file),
                               mime='text/csv', use_container_width=True)
    geojson_path = auto_file.replace('_csv.csv', '_geojson.geojson')
    if os.path.exists(geojson_path):
        with open(geojson_path, 'rb') as f:
            d2.download_button('下载 GeoJSON', f.read(), file_name=os.path.basename(geojson_path),
                               mime='application/geo+json', use_container_width=True)
    st.divider()


def _render_new_analysis_view(engine_cfg: dict):
    """模式 B: 选择新文件并运行分析（文件选择 + 分析触发）。"""
    st.subheader('选择新数据文件', divider='gray')
    tab1, tab2 = st.tabs(['从 processed 目录选择 (L1)', '上传新文件'])
    new_file_selected = False
    input_path = ''
    source_dir = PROCESSED_DIR

    with tab1:
        l1_files = []
        if os.path.exists(PROCESSED_DIR):
            l1_files = sorted([
                f for f in os.listdir(PROCESSED_DIR)
                if os.path.isfile(os.path.join(PROCESSED_DIR, f))
                and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))
                and not f.lower().endswith('.geojson')
                and '_L2_result' not in f
                and '_L3_result' not in f
                and '_L4_result' not in f  # 仅 L1 文件，排除 L2/L3/L4 结果
            ])
        if l1_files:
            file_choice = st.selectbox('L1 治理后数据', l1_files, key='console_l1',
                                       help='仅 L1 文件，不含 _L2/L3/L4_result')
            input_path = os.path.join(PROCESSED_DIR, file_choice)
            st.caption(f'`{input_path}`')
            new_file_selected = True
            source_dir = PROCESSED_DIR
        else:
            st.info('无可用 L1 文件。请先生成 L1 模拟数据：`python SCRIPT/generate_l1_mock.py`')

    with tab2:
        uploaded = st.file_uploader('上传文件', type=['csv', 'tsv', 'json', 'geojson'])
        if uploaded:
            os.makedirs(PROCESSED_DIR, exist_ok=True)
            save_path = os.path.join(PROCESSED_DIR, uploaded.name)
            with open(save_path, 'wb') as f:
                f.write(uploaded.getbuffer())
            st.success('已保存')
            input_path = save_path
            new_file_selected = True

    if new_file_selected and input_path:
        st.divider()
        # 规范化输出名称：移除 _raw 后缀
        _default_name = os.path.splitext(os.path.basename(input_path))[0]
        _default_name = _default_name.replace('_raw', '').replace('_RAW', '')
        output_name = st.text_input('输出文件名', value=_default_name)
        # ── 文件变更检测：新文件重置分析状态 ──
        current_file_key = f'{input_path}|{output_name}'
        if st.session_state.get('_console_last_analyzed', '') != current_file_key:
            st.session_state['_console_analysis_done'] = False
            st.session_state['_console_last_result'] = None
        # ── 判断分析是否已完成 ──
        analysis_done = st.session_state.get('_console_analysis_done', False)
        btn_label = '[在地图上显示]' if analysis_done else '[开始分析]'
        if st.button(btn_label, type='primary', use_container_width=True):
            if analysis_done:
                # ── 模式 B: 加载到地图 ──
                result = st.session_state.get('_console_last_result')
                if result:
                    st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]  # processed
                    st.session_state['file_choice'] = os.path.basename(result['csv_path'])
                    st.session_state['file_path'] = result['csv_path']
                    st.session_state['current_df'] = result['df']
                    st.session_state['current_file_choice'] = os.path.basename(result['csv_path'])
                    st.session_state['data_loaded'] = True
                    register_layer(
                        name=os.path.basename(result['csv_path']),
                        file_path=result['csv_path'],
                        level='L2',
                        range_label='分析结果',
                        color='#48C9B0',
                    )
                    st.success(f'已加载 {result["n_points"]} 条数据到地图。切换至地图浏览器查看。')
            else:
                # ── 模式 A: 运行分析 ──
                eng_type = 'snownlp'; is_full = False
                engine_choice = engine_cfg['engine_choice']
                if 'L3' in engine_choice: eng_type = 'llm'
                elif 'L4' in engine_choice: eng_type = 'corpus'
                elif '全管道' in engine_choice: is_full = True
                with st.status('分析中...', expanded=True) as status:
                    result = run_analysis_task(
                        file_path=input_path, engine_type=eng_type,
                        output_name=output_name, api_key=engine_cfg['api_key'],
                        corpus_path=engine_cfg['corpus_path'],
                        enable_keywords=engine_cfg['enable_keywords'],
                        full_pipeline=is_full,
                    )
                    if result['success']:
                        status.update(label=f'完成！{result["n_points"]} 条', state='complete')
                        register_layer(
                            name=os.path.basename(result['csv_path']),
                            file_path=result['csv_path'],
                            level='L2',
                            range_label='分析结果',
                            color='#48C9B0',
                        )
                        # ── 保存分析状态 ──
                        st.session_state['_console_analysis_done'] = True
                        st.session_state['_console_last_analyzed'] = current_file_key
                        st.session_state['_console_last_result'] = result
                        st.rerun()
                    else:
                        status.update(label='失败', state='error')
                        st.error(result['message'])


@track("MOD_APP.F_001", track_args=False)
def show_console_page():
    """分析控制台主入口 — 委托给 4 个子函数处理。"""
    components.html(
        '<script>window.parent.document.title = "情绪地图v1.0：情绪控制台";</script>',
        height=0, width=0)
    st.title('情绪地图v1.0：情绪控制台')

    # 1. 解析 URL 参数
    params = _parse_console_params()

    # 2. 渲染侧边栏
    engine_cfg = _render_console_sidebar(params)

    # 3. 模式 A: 自动加载结果
    if params['is_auto_mode']:
        _render_auto_loaded_view(params)

    # 4. 模式 B: 手动分析新文件
    _render_new_analysis_view(engine_cfg)
