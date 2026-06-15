"""
图层注册工具 (Layer Registry)
═══════════════════════════
管理 Streamlit session_state 中的地图图层列表。
被 app_main.py 和 app_console.py 共享。
"""
import streamlit as st
from core.tracker import track


@track("MOD_APP.F_004", track_args=True)
def register_layer(name, file_path, level='L1', range_label='', color='#48C9B0'):
    """注册或更新一个图层到 session_state['layers']。

    Args:
        name: 图层显示名称
        file_path: 数据文件路径（用于去重和加载）
        level: 数据层级标签 (L0/L1/L2/L3/L4)
        range_label: 范围/来源标签
        color: 图层颜色标识
    """
    layers = st.session_state.get('layers', [])
    # 去重：同路径已存在则更新
    for lyr in layers:
        if lyr['file_path'] == file_path:
            lyr['name'] = name
            lyr['level'] = level
            lyr['range_label'] = range_label
            lyr['color'] = color
            return
    layers.append({
        'name': name,
        'file_path': file_path,
        'level': level,
        'range_label': range_label,
        'color': color,
        'visible': True,
    })
    st.session_state['layers'] = layers
