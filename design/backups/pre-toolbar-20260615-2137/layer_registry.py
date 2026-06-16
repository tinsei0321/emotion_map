"""
图层注册工具 (Layer Registry)
═══════════════════════════
管理 Streamlit session_state 中的地图图层列表。
所有功能（D/R/A/GV）必须通过此入口注册图层，保证 LY 弹窗和数据面板
始终与地图实际内容同步。
"""
import streamlit as st
from core.tracker import track


@track("MOD_APP.F_004", track_args=True)
def register_layer(name, file_path, level='L1', kind='data', color='#48C9B0',
                   range_label=''):
    """注册或更新一个图层到 session_state['layers']。

    Args:
        name: 图层显示名称
        file_path: 数据文件路径（用于去重和加载；范围图层可传 ''）
        level: 数据层级标签 (L0/L1/L2/L3/L4)
        kind: 'data' 数据图层 | 'range' 范围图层
        color: 图层颜色标识
        range_label: (deprecated) 保留向后兼容
    """
    layers = st.session_state.get('layers', [])
    # 去重：同路径已存在则更新
    for lyr in layers:
        if file_path and lyr.get('file_path') == file_path:
            lyr['name'] = name
            lyr['level'] = level
            lyr['kind'] = kind
            lyr['color'] = color
            lyr['visible'] = True  # 重新加载时恢复显示
            return
    layers.append({
        'name': name,
        'file_path': file_path,
        'level': level,
        'kind': kind,
        'color': color,
        'visible': True,
    })
    st.session_state['layers'] = layers
