"""GIS 数据注册表 · AI 问答 geo 工具箱的数据后端。

lazy-load + 内存缓存（GeoDataFrame），按稳定 id 引用——避免大数据（L1 30MB / 社区 87MB）
每次问答往返。被 api/geo_routes.py 的 /api/v1/geo/* 端点调用，供 AI 经 ReAct 自动选用。

数据资产：
- 点层：L1（治理点）/ L2（情绪点，含 score+polarity）× T1/T2/T3，读 DATA/performance/
- 边界 preset：行政区/街办/社区/更新单元/用地，复用 core/range_selector 的 manifest 机制
- CRS 统一 EPSG:4326（地图渲染基准；面积/缓冲在 spatial_analysis 内投影 EPSG:4546）

用户临时上传层不走注册表（保留 send-in 模式，由调用方直接传 GeoJSON）。
"""
import json
import os
from typing import Optional

import geopandas as gpd
import pandas as pd

from core.config import PERFORMANCE_DIR, PROJECT_ROOT
from core.range_selector import list_presets, load_preset, _PRESETS_DIR
from core.field_dictionary import resolve_role, find_boundary_name_column   # P1 字段语义层

# 模块级缓存：layer_id/boundary_id → GeoDataFrame。lazy load，不启动全量加载。
_CACHE: dict = {}

# ── 点层 id → (文件名, 标签, 层级) ──
# L2 含 score/polarity（情绪主用）；L1 含 domain/element/topic（治理要素，无 score）。
_POINT_LAYERS = {
    'yichang_l2_t1': ('yichang_L2_T1_L2_result_geojson.geojson', '宜昌 L2 · T1（中心城区情绪·初）', 'L2'),
    'yichang_l2_t2': ('yichang_L2_T2_L2_result_geojson.geojson', '宜昌 L2 · T2（中心城区情绪·中）', 'L2'),
    'yichang_l2_t3': ('yichang_L2_T3_L2_result_geojson.geojson', '宜昌 L2 · T3（中心城区情绪·末）', 'L2'),
    'yichang_l1_t1': ('yichang_L1_T1_result_csv.csv.geojson', '宜昌 L1 · T1（全域治理点·初）', 'L1'),
    'yichang_l1_t2': ('yichang_L1_T2_result_geojson.geojson', '宜昌 L1 · T2（全域治理点·中）', 'L1'),
    'yichang_l1_t3': ('yichang_L1_T3_result_geojson.geojson', '宜昌 L1 · T3（全域治理点·末）', 'L1'),
    # 大南门·二马路历史街区 L3+L4（ABSA 富归因·CB-16 数据专题接入·坐标经 backfill_ermawu_coords 补齐）
    # 注：level='L3L4' 数据层零 level 检查（resolve_points/get_layer_points 只读 CSV+lon/lat）·仅 R5 胶囊防线（UI 追问）不含
    'ermawu_l3l4_t1': ('ermawu_l3l4_T1_result_geojson.geojson', '大南门·二马路 L3L4 · T1（历史街区·开街扰扰）', 'L3L4'),
    'ermawu_l3l4_t2': ('ermawu_l3l4_T2_result_geojson.geojson', '大南门·二马路 L3L4 · T2（历史街区·暑假打卡）', 'L3L4'),
    'ermawu_l3l4_t3': ('ermawu_l3l4_T3_result_geojson.geojson', '大南门·二马路 L3L4 · T3（历史街区·文旅爆满）', 'L3L4'),
    # CB-23 checkup 主观轨：12345 治理版（2024·57265 行·geocode 回填 32% 坐标·中心城区+县市）
    # 注：checkup_* 层隔离（Codex G6 whitelist·sim 层零引用）·level='CHECKUP' 零 level 检查·极性负偏平台特性（观点以强度为主）
    # CB-39 A2/E16：真实数据迁出演示池 → DATA/analysis/12345主观/（第 4 元素=repo 相对子目录·缺省走 PERFORMANCE_DIR）
    'checkup_12345_2024': ('checkup_12345_2024.csv', '12345 投诉 2024（主观轨·体检医生·中心城区+县市）', 'CHECKUP', 'DATA/THEME/theme_城市体检/12345_政务热线_城市体检分析'),
    # PT-CB10 C2-6（D 批挂账销号）：demo_pioneer 演示双点层注册进点层表——原走 manifest 现路径 dict send-in，
    #   现注册后与全部点层同通道（list_data 可见/resolve_points 可引）；GeoJSON 格式·get_layer_points 按扩展名分支读。
    #   数据=12345 主观轨真实点（安全韧性/民生基础两类·社区层）·level='CHECKUP' 同族。
    'subj_12345_safety_community_point': ('12345_安全韧性_社区点.geojson', '12345 安全韧性点·社区层（主观轨·演示双用）', 'CHECKUP', 'DATA/THEME/theme_城市体检/12345_政务热线_城市体检分析'),
    'subj_12345_livelihood_community_point': ('12345_民生基础_社区点.geojson', '12345 民生基础点·社区层（主观轨·演示双用）', 'CHECKUP', 'DATA/THEME/theme_城市体检/12345_政务热线_城市体检分析'),
    # PT-CB14 C1（D-4 销号）：checkup qty 体检量化点层 11 层注册进点层表——文件在 DATA/boundaries/presets（非 analysis）·
    #   照 subj_12345 先例（第 4 元素=子目录·level='CHECKUP'·GeoJSON 分支 get_layer_points 直读几何）。
    #   数据=客观轨 77 项量化（指标/中类/board 属性·无极性）·id 与验收口径一致（qty_民生_停车设施 等）。
    'qty_合并': ('themes_point_checkup_全量问题点_2296.geojson', '体检 qty 量化 · 全量问题点（客观轨·77 项）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_安全_住房': ('themes_point_checkup_住房安全_670.geojson', '体检 qty 量化 · 住房安全（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_安全_合并': ('themes_point_checkup_安全合并_1350.geojson', '体检 qty 量化 · 安全合并（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_安全_安全消防': ('themes_point_checkup_消防安全_421.geojson', '体检 qty 量化 · 消防安全（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_安全_市政管网': ('themes_point_checkup_市政管网_259.geojson', '体检 qty 量化 · 市政管网（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_民生_交通设施': ('themes_point_checkup_不达标步行道_35.geojson', '体检 qty 量化 · 不达标步行道（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_民生_住房': ('themes_point_checkup_住房保障_97.geojson', '体检 qty 量化 · 住房保障（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_民生_停车设施': ('themes_point_checkup_停车设施_369.geojson', '体检 qty 量化 · 停车设施（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_民生_公服设施': ('themes_point_checkup_公服设施_165.geojson', '体检 qty 量化 · 公服设施（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_民生_合并': ('themes_point_checkup_民生合并_946.geojson', '体检 qty 量化 · 民生合并（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
    'qty_民生_物业街面': ('themes_point_checkup_物业街面_280.geojson', '体检 qty 量化 · 物业街面（客观轨）', 'CHECKUP', 'DATA/THEME/theme_城市体检'),
}


def _layer_path(entry) -> str:
    """注册条目 → 文件绝对路径（CB-39 A2：可选第 4 元素=repo 相对子目录·缺省 PERFORMANCE_DIR 向后兼容）。"""
    fname = entry[0]
    sub = entry[3] if len(entry) > 3 else ''
    return os.path.join(PROJECT_ROOT, sub, fname) if sub else os.path.join(PERFORMANCE_DIR, fname)


_FIELD_CACHE: dict = {}   # fname → {fields, samples, dtypes, field_cards}（catalog 暴露给 AI，避免瞎猜列名/取值/role）
# P1: 删 _KEY_FIELDS 硬编码，改用 field_dictionary.resolve_role 判定哪些字段优先给样例值（帮 LLM 构造 pre_filter）
# P3: value 增 field_cards（规则标注 role，供 catalog/formatGeoCatalog 标注字段语义）


def _point_layer_overview(fname: str) -> dict:
    """读 CSV 表头 + 首行（缓存），返 {fields, samples, dtypes, field_cards}。

    field_cards = {field: {role, source:'rule'}}——resolve_role 规则标注（role 为 None 表 miss）。
    供 catalog 暴露字段名 + 取值样例 + 类型 + 语义角色。"""
    if fname in _FIELD_CACHE:
        return _FIELD_CACHE[fname]
    # CB-39 A2：fname 可能是完整路径（含子目录层）——目录存在则直接用，否则按 PERFORMANCE_DIR 兼容旧调
    path = fname if os.path.isfile(fname) else os.path.join(PERFORMANCE_DIR, fname)
    ov = {'fields': [], 'samples': {}, 'dtypes': {}, 'field_cards': {}}
    if os.path.isfile(path):
        try:
            # PT-CB10 C2-6：GeoJSON 点层同样走 overview（gpd 读·与 CSV 同口径暴露字段/样例/role）。
            if str(fname).lower().endswith(('.geojson', '.json')):
                df = gpd.read_file(path, rows=2)
            else:
                df = pd.read_csv(path, nrows=2)
            fields = list(df.columns)
            # 优先给有 canonical role 的字段样例值（resolve_role 命中=polarity/score/text/name/...）
            key = [c for c in fields if resolve_role(c)] or fields[:8]
            row0 = df.iloc[0] if len(df) else None
            ov = {
                'fields': fields,
                'samples': {c: (str(row0[c])[:24] if row0 is not None and c in row0 else '') for c in key},
                'dtypes': {c: str(df[c].dtype) for c in key},
                'field_cards': {c: {'role': resolve_role(c), 'source': 'rule'} for c in key},
            }
        except Exception:
            pass
    _FIELD_CACHE[fname] = ov
    return ov


def list_point_layers() -> list:
    """列出可用的点层（标注 available + 字段/样例/类型/CRS）。L2 优先（含 score/polarity）。"""
    out = []
    for lid, entry in _POINT_LAYERS.items():   # CB-39 A2：条目可带第 4 元素（子目录）·不再定长解包
        fname, label, level = entry[0], entry[1], entry[2]
        path = _layer_path(_POINT_LAYERS[lid])
        available = os.path.isfile(path)
        ov = _point_layer_overview(path) if available else {'fields': [], 'samples': {}, 'dtypes': {}, 'field_cards': {}}
        out.append({
            'id': lid,
            'label': label,
            'level': level,
            'available': available,
            'fields': ov['fields'],
            'samples': ov['samples'],
            'dtypes': ov['dtypes'],
            'field_cards': ov['field_cards'],   # P3：规则标注 role，前端 formatGeoCatalog 渲染 k[role]:v
            'crs': 'EPSG:4326',
        })
    return out


def list_boundaries() -> list:
    """列出可用的边界 preset（展平 list_presets 的 group→items，标注 available + name_field）。"""
    flat = []
    for g in list_presets() or []:
        for it in g.get('items', []):
            flat.append({
                'id': it.get('id'),
                'label': it.get('label'),
                'group': g.get('group'),
                'available': bool(it.get('available')),
                # 暴露名称字段：AI 据此构造 where（如 admin_district 的 MC、renewal_unit 的编号）
                'name_field': it.get('nameField'),
                # PT-CB2 T2：透出 manifest usage（input=分析原料 | analysis_output=结论层·禁作空间操作输入）
                'usage': it.get('usage'),
            })
    return flat


def get_layer_points(layer_id: str) -> gpd.GeoDataFrame:
    """按 id 取点层 GeoDataFrame（EPSG:4326，lon/lat → Point）。lazy 缓存。

    需要 lon/lat 列；score/polarity/domain/element/topic 等按文件原样保留（缺失则下游聚合跳过）。
    """
    if layer_id in _CACHE:
        return _CACHE[layer_id]
    if layer_id not in _POINT_LAYERS:
        raise KeyError(f'未知点层 id: {layer_id}（可用：{list(_POINT_LAYERS)}）')
    path = _layer_path(_POINT_LAYERS[layer_id])
    if not os.path.isfile(path):
        raise FileNotFoundError(f'点层文件缺失: {path}')

    # PT-CB10 C2-6：GeoJSON 点层分支（演示双点层·无 lon/lat 列·几何直读；属性按文件原样保留）。
    if path.lower().endswith(('.geojson', '.json')):
        gdf = gpd.read_file(path)
        # GeoJSON 中的日期字符串会被 pyogrio 解析成 datetime/Timestamp，序列化时需还原为字符串
        for col in gdf.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].astype(str)
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326')
        else:
            gdf = gdf.to_crs('EPSG:4326')
        _CACHE[layer_id] = gdf
        return gdf

    df = pd.read_csv(path)
    # 坐标列兼容（L1/L2 均含 lon/lat；缺失则报错）
    lon_col = 'lon' if 'lon' in df.columns else ('longitude' if 'longitude' in df.columns else None)
    lat_col = 'lat' if 'lat' in df.columns else ('latitude' if 'latitude' in df.columns else None)
    if not lon_col or not lat_col:
        raise KeyError(f'{layer_id} 缺 lon/lat 列')

    df = df.dropna(subset=[lon_col, lat_col]).copy()
    # 数值列容错（聚合前 to_numeric；防 csv str 化崩 mean）
    for c in ('score', 'l1_confidence', 'emotion_intensity'):
        if c in df.columns:
            df[c] = pd.to_numeric(df.get(c), errors='coerce')
    # 极性规范化列名（聚合函数读 'polarity'）
    if 'polarity' not in df.columns and 'polarity_hint' in df.columns:
        # L1 用 polarity_hint（弱极性），映射到 polarity 列名供下游统一处理
        df = df.rename(columns={'polarity_hint': 'polarity'})

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs='EPSG:4326'
    )
    _CACHE[layer_id] = gdf
    return gdf


def resolve_boundary(boundary) -> gpd.GeoDataFrame:
    """把边界规格解析为面域 GeoDataFrame（EPSG:4326）。

    boundary可为：
    - str：preset_id（如 'renewal_unit'）→ load_preset 读 manifest 对应文件
    - dict：GeoJSON FeatureCollection（用户临时上传，send-in 模式）
    """
    if isinstance(boundary, str):
        loaded = load_preset(boundary)
        if not loaded.get('available'):
            # PT-CB14 C2（D-1 销号）：报错语义改「文件未落盘」（manifest 已登记≠文件已上传）·带需上传文件名
            fname = ''
            try:
                with open(os.path.join(_PRESETS_DIR, 'manifest.json'), encoding='utf-8') as _fh:
                    for _g in json.load(_fh):
                        for _it in _g.get('items', []):
                            if _it.get('id') == boundary:
                                fname = str(_it.get('file', ''))
                                break
            except Exception:
                pass
            avail = [b['id'] for b in list_boundaries() if b.get('available')]
            raise FileNotFoundError(
                f'边界 preset 不可用: {boundary}（文件未落盘·需上传：{fname}（manifest 已登记））。可用 preset: {avail}')
        gj = loaded.get('geojson') or {}
        feats = gj.get('features') if isinstance(gj, dict) else None
        if not feats:
            raise ValueError(f'边界 preset {boundary} 无 features')
        polys = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
        # 规范名称列（manifest nameField → name），供 zonal_stats 输出可读单元名
        # CB-05 ROOTCAUSE 方案 B：改 rename→copy（原始列保留 + name 副本·治字段名断裂）
        nf = loaded.get('nameField')
        if nf and nf in polys.columns and 'name' not in polys.columns:
            polys['name'] = polys[nf]   # 副本（不删原始列·下游 MC/name 都能用）
        return polys
    if isinstance(boundary, dict):
        feats = boundary.get('features') if isinstance(boundary, dict) else None
        if not feats:
            raise ValueError('boundary GeoJSON 无 features')
        polys = gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
        # P1 send-in GeoJSON nameField 推断：find_boundary_name_column 找名称列→加 name 副本
        # CB-05 ROOTCAUSE 方案 B：改 rename→copy（原始列如 MC 保留·_apply_attr_filter 仍能引用）
        if 'name' not in polys.columns:
            nf = find_boundary_name_column(polys.columns)
            if nf:
                polys['name'] = polys[nf]   # 副本（不删原始列·治字段名断裂）
        # PRM-07（08-08 深读·glm A）：法定功能区黑名单兜底——dict 直供 boundary 若要素名命中
        #   法定功能区（非真实行政区划）→ 拒绝（诚实 request_upload·CB-14「EMC 不硬猜」）。
        #   用黑名单而非白名单：用户上传层可含任意合法地名·白名单会误拦（用户上传层不受限设计）。
        _ADMIN_BLOCKLIST = {'小溪塔', '龙泉', '白洋', '生物产业园', '东部产业新区', '绿心'}
        _name_col = 'name' if 'name' in polys.columns else None
        if _name_col is None:
            _nf = find_boundary_name_column(polys.columns)
            _name_col = _nf if _nf else None
        # Codex T7 阻断修复：仅拦「单要素」dict（LLM 直传特征·如 {features:[小溪塔]}）——
        #   多要素（从已加载面层/索引解析的整层·如行政区层 9 要素含龙泉）是合法图层操作·放行。
        if _name_col is not None and len(polys) == 1:
            for _nm in polys[_name_col].astype(str):
                _hit = next((d for d in _ADMIN_BLOCKLIST if d in _nm or _nm in d), None)
                if _hit:
                    raise ValueError(f'边界要素「{_nm}」为法定功能区·非真实行政区划·EMC 不硬猜不可信范围（CB-14）·请上传标准边界资料')
        return polys
    raise TypeError(f'boundary 需为 preset_id(str) 或 GeoJSON(dict)，收到 {type(boundary)}')


def resolve_points(layer) -> Optional[gpd.GeoDataFrame]:
    """把点层规格解析为点 GeoDataFrame。

    layer可为：
    - str：注册表 layer_id（如 'yichang_l2_t1'）
    - dict：GeoJSON FeatureCollection（send-in，前端已加载的聚合层/上传点）
    - None：取默认情绪层（首个可用的 L2）
    """
    if layer is None:
        for lid in _POINT_LAYERS:   # L2 优先（_POINT_LAYERS 已按 L2 在前排序）
            try:
                return get_layer_points(lid)
            except Exception:
                continue
        raise FileNotFoundError('无可用点层')
    if isinstance(layer, str):
        return get_layer_points(layer)
    if isinstance(layer, dict):
        feats = layer.get('features') if isinstance(layer, dict) else None
        if not feats:
            raise ValueError('layer GeoJSON 无 features')
        return gpd.GeoDataFrame.from_features(feats, crs='EPSG:4326')
    raise TypeError(f'layer 需为 layer_id(str) / GeoJSON(dict) / None，收到 {type(layer)}')


def clear_cache():
    """清空注册表缓存（数据文件更新后调用）。"""
    _CACHE.clear()
