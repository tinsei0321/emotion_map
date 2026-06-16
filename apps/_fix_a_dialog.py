"""修复 show_analysis_dialog — 用 st.radio 替代 st.button"""
import re

with open('apps/app_dialogs.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find function boundaries
start = None
end = None
for i, line in enumerate(lines):
    if '@track("MOD_APP.F_011", track_args=False)' in line and i > 840:
        start = i
    if start is not None and i > start + 5 and line.strip() == '':
        # Check if next non-empty line is a new function
        next_nonempty = None
        for j in range(i+1, len(lines)):
            if lines[j].strip() and not lines[j].strip().startswith('#'):
                next_nonempty = lines[j].strip()
                break
        if next_nonempty and next_nonempty.startswith('def _register_dialog_track_ids'):
            end = i
            break
        if next_nonempty and next_nonempty.startswith('#'):
            # check the next line after comments
            for j in range(i+1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    if lines[j].strip().startswith('def _register'):
                        end = i
                        break
                    else:
                        break
            if end:
                break

print(f"Function at lines {start+1} to {end+1}")

new_func = """@track("MOD_APP.F_011", track_args=False)
@st.dialog('ANA 运行情绪分析', width='large')
def show_analysis_dialog():
    if st.session_state.pop('_analysis_done_flag', False):
        return
    st.markdown('选择 L1 数据文件并运行情绪分析引擎，结果自动加载到地图。')

    l1_files = []
    if os.path.exists(PROCESSED_DIR):
        l1_files = sorted([f for f in os.listdir(PROCESSED_DIR)
                          if os.path.isfile(os.path.join(PROCESSED_DIR, f))
                          and f.lower().endswith(('.csv', '.tsv', '.json', '.geojson'))
                          and not f.lower().endswith('.geojson')
                          and '_L2_result' not in f
                          and '_L3_result' not in f
                          and '_L4_result' not in f])

    if not l1_files:
        st.warning(f'`{PROCESSED_DIR}/` 中没有可分析的 L1 文件。')
        return

    source_dir = PROCESSED_DIR
    file_choice = st.selectbox('FILE 待分析数据文件', l1_files)
    st.caption(f'路径: `{os.path.join(source_dir, file_choice)}`')

    input_path = os.path.join(source_dir, file_choice)
    try:
        sample = pd.read_csv(input_path, nrows=1)
        if not ('relevance' in sample.columns or 'in_scope' in sample.columns):
            st.warning('WARN 所选文件缺少 L1 治理标记列')
        n_rows = len(pd.read_csv(input_path))
        if n_rows > 10000:
            st.info(f'文件包含 {n_rows:,} 条记录。分析可能需要较长时间。')
    except Exception as e:
        st.warning(f'无法预览文件: {e}')

    with st.expander('L1 数据概览', expanded=False):
        gov_result = st.session_state.get('_governance_result')
        if gov_result:
            c1, c2 = st.columns(2)
            c1.metric('最近 L1 输出', gov_result['l1_n'])
            c2.metric('输入', gov_result['input_n'])

    st.divider()

    # -- L2 引擎选择 --
    st.caption('ENG L1 -> L2 情绪分析引擎')
    engine_type = st.radio(
        'L2 基础分析',
        ['snownlp', 'deepseek-l2'],
        format_func=lambda x: {
            'snownlp': 'SnowNLP -- 离线 . 免费 . 速度快',
            'deepseek-l2': 'DeepSeek -- 在线 . 高精度 . 约 0.001 元/条',
        }[x],
        index=0,
        horizontal=True,
    )

    api_key = ''
    if engine_type == 'deepseek-l2':
        api_key = os.environ.get('DEEPSEEK_API_KEY', '')
        if api_key:
            st.caption(f'Key: `{api_key[:8]}...{api_key[-4:]}` (来自环境变量)')
        else:
            st.warning('WARN 未检测到 DEEPSEEK_API_KEY。设置环境变量后重试。')

    # -- L3/L4 引擎选择 --
    st.divider()
    st.caption('ENG L3 / L4 高级引擎（可选）')
    advanced_engine = st.radio(
        'L3/L4 引擎',
        ['none', 'llm', 'corpus'],
        format_func=lambda x: {
            'none': '不使用（仅 L2）',
            'llm': 'L3 . LLM 细粒度语义解析 (需 API Key)',
            'corpus': 'L4 . 语料库多维归因 (需 API Key + 语料库)',
        }[x],
        index=0,
        horizontal=True,
    )

    if advanced_engine == 'llm':
        api_key = st.text_input('KEY LLM API Key', type='password', placeholder='sk-...')
        engine_type = 'llm'
    elif advanced_engine == 'corpus':
        api_key = st.text_input('KEY LLM API Key', type='password', placeholder='sk-...')
        engine_type = 'corpus'

    st.divider()

    # -- 文件变更检测 --
    if st.session_state.get('_last_analyzed_file', '') != file_choice:
        st.session_state['_analysis_done'] = False
        st.session_state['_last_analyzed_file'] = ''
        st.session_state['_last_analysis_result'] = None
        st.session_state['_analysis_show_results'] = False

    analysis_done = st.session_state.get('_analysis_done', False) and \\
                    st.session_state.get('_last_analyzed_file', '') == file_choice
    btn_label = '在地图上显示' if analysis_done else '开始分析'
    run_clicked = st.button(btn_label, type='primary', use_container_width=True)

    if run_clicked:
        if analysis_done:
            saved = st.session_state.get('_last_analysis_result')
            if saved:
                st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]
                st.session_state['file_choice'] = os.path.basename(saved['csv_path'])
                st.session_state['file_path'] = saved['csv_path']
                st.session_state['current_df'] = saved['df']
                st.session_state['current_file_choice'] = os.path.basename(saved['csv_path'])
                st.session_state['data_loaded'] = True
                register_layer(name=os.path.basename(saved['csv_path']),
                             file_path=saved['csv_path'], level='L2',
                             range_label='分析结果', color='#48C9B0')
                st.success(f'已加载 {saved["n_points"]} 条数据到地图。')
        else:
            _input_path = os.path.join(source_dir, file_choice)
            _base_name = os.path.splitext(file_choice)[0].replace('_raw', '').replace('_RAW', '')
            file_size_mb = os.path.getsize(_input_path) / (1024 * 1024)

            progress_bar = st.progress(0, text='准备分析...')
            def update_progress(step, total, message):
                progress_bar.progress(step / total, text=message)

            with st.status('分析中...', expanded=True) as status:
                status.update(label=f'文件: {_base_name} ({file_size_mb:.0f} MB)  |  引擎: {engine_type}')
                try:
                    result = run_analysis_task(
                        file_path=_input_path, engine_type=engine_type,
                        output_name=_base_name, api_key=api_key,
                        progress_callback=update_progress)
                    if result['success']:
                        progress_bar.progress(1.0, text=f'OK {result["n_points"]} 条完成')
                        status.update(label=f'OK 分析完成！{result["n_points"]} 条数据', state='complete')
                        st.session_state['_analysis_done'] = True
                        st.session_state['_last_analyzed_file'] = file_choice
                        st.session_state['_last_analysis_result'] = result
                        st.session_state['_analysis_show_results'] = True
                        st.session_state['folder_key'] = list(FOLDER_OPTIONS.keys())[1]
                        st.session_state['file_choice'] = os.path.basename(result['csv_path'])
                        st.session_state['file_path'] = result['csv_path']
                        st.session_state['current_df'] = result['df']
                        st.session_state['current_file_choice'] = os.path.basename(result['csv_path'])
                        st.session_state['data_loaded'] = True
                        register_layer(name=os.path.basename(result['csv_path']),
                                     file_path=result['csv_path'], level='L2',
                                     range_label='分析结果', color='#48C9B0')
                        st.session_state['_analysis_done_flag'] = True
                        st.rerun()
                    else:
                        progress_bar.progress(1.0, text='WARN 分析失败')
                        status.update(label='WARN 分析失败', state='error')
                        st.error(f'分析失败: {result["message"][:200]}')
                except Exception as e:
                    progress_bar.progress(1.0, text='ERR 分析失败')
                    status.update(label='ERR 分析出错', state='error')
                    st.error(f'分析失败: {str(e)[:200]}')
                    trace_error("MOD_APP.F_011", f'分析执行异常: {str(e)[:200]}')

    # -- 结果预览 --
    if analysis_done and st.session_state.get('_analysis_show_results'):
        saved = st.session_state.get('_last_analysis_result')
        if saved and saved.get('df') is not None:
            result_df = saved['df']
            result_csv = saved['csv_path']
            st.divider()
            st.subheader('分析结果预览')
            if 'polarity' in result_df.columns:
                render_polarity_stats(result_df, show_score=True)
                render_polarity_chart(result_df, height=200)
            else:
                st.caption(f'共 {len(result_df)} 条数据（无极性列）')

            _, btn_col, _ = st.columns([1, 2, 1])
            with btn_col:
                st.link_button('打开分析控制台查看详细报告',
                             url=f'/?page=console&file={result_csv.replace(chr(92), "/")}',
                             type='primary', use_container_width=True)

"""

new_lines = [l + '\n' for l in new_func.split('\n')]
result = lines[:start] + new_lines + lines[end+1:]

with open('apps/app_dialogs.py', 'w', encoding='utf-8') as f:
    f.writelines(result)

import ast
ast.parse(''.join(result))
print(f'[OK] Replaced. Total lines: {len(result)}')

# Verify
txt = ''.join(result)
assert 'st.radio(' in txt and 'horizontal=True' in txt
assert "'deepseek-l2'" in txt and "'snownlp'" in txt
print('[OK] st.radio + horizontal confirmed')
