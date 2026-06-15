"""
core — 可复用基础设施（被 import）

模块:
    config          — 全局配置
    utils           — 通用工具（safe_print）
    data_loader     — 数据加载
    coord_transform — 坐标转换
    map_engine      — 地图渲染
    range_selector  — 范围选择
    ui_components   — UI 组件
    export          — 导出工具
    tracker         — 决策追踪系统
"""

from core.utils import safe_print
from core.tracker import track, TrackContext, trace_log, trace_error, trace_warn, register_track_id
