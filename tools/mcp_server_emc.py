#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PT-CB5 T3 · G10 标准插座（MCP server）——七件分析工具 + PT-CB6 render_spec 第 8 插座。

把 EMC 既有后端能力包装为 MCP 工具，供 zcode/claude/codex/dsh 等
通用助手经协议即插即用。分析七工具纯只读、零 LLM；render_spec 仅写
收件箱 spec JSON（DATA/exports/render_inbox·前端显示屏消费）。

用法：
  py tools/mcp_server_emc.py        # stdio 启动（Ctrl+C 退出）

纪律：
  - 重依赖（geopandas/rag 等）全部函数体内惰性导入，启动轻快；
  - 每个工具一个追踪号 MOD_AIQA.F_021-F_028（F_023 kb_facts 按主手
    裁决直映真身签名 query/keyword/topic/limit；F_028=render_spec）；
  - print 走 _safe_print；代码禁 emoji；
  - 返回值必带 caliber 对象（口径/语义/禁用边界/注册表卡引用）。
"""
import json
import os
import random
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from core.tracker import register_track_id, track

register_track_id('MOD_AIQA.F_021', 'MCP list_data（数据说明书：点层+边界层目录·开卷定参）')
register_track_id('MOD_AIQA.F_022', 'MCP rag_query（带来源知识检索·v1 综合降级 deferred_v2）')
register_track_id('MOD_AIQA.F_023', 'MCP kb_facts（行业事实卡·真身签名直映 query/keyword/topic/limit）')
register_track_id('MOD_AIQA.F_024', 'MCP outlet_card（行业出口卡·确定性组装·对话级）')
register_track_id('MOD_AIQA.F_025', 'MCP zonal_stats（单元聚合·宏观/中观结论）')
register_track_id('MOD_AIQA.F_026', 'MCP buffer（缓冲影响圈·中观）')
register_track_id('MOD_AIQA.F_027', 'MCP rank（排序评价·最差/最好 Top-N）')
register_track_id('MOD_AIQA.F_028', 'MCP render_spec（图层图纸：dataset/inline→spec 落收件箱）')

MANIFEST = os.path.join(REPO, 'DATA', 'boundaries', 'presets', 'manifest.json')

# P+ scheme 受管样式词表（前端按名解析·未知即拒）
SCHEMES = ('community_choropleth_v1', 'point_default_v1')

CALIBERS = {
    'list_data': {
        'scale': '数据资产清单',
        'semantics': '可供分析的点层与边界层目录（开卷定参的查询面）',
        'limits': '结论层（usage=analysis_output）禁作空间操作输入',
        'refs': ['G-2', 'K-C1'],
    },
    'rag_query': {
        'scale': '知识检索',
        'semantics': '本地知识库向量检索（非穷尽）·结果为素材非结论',
        'limits': 'Top-K 召回非全量；结论须综合并注来源；勿将倾向表述为精确值',
        'refs': ['K-01'],
    },
    'kb_facts': {
        'scale': '事实卡',
        'semantics': '本地蒸馏的权威事实（带来源年份）',
        'limits': '事实卡非实时数据；引用须带来源',
        'refs': ['K-01'],
    },
    'outlet_card': {
        'scale': '答案级出口',
        'semantics': '确定性组装的行业出口卡片（结果范式 agent 第三段·对话级）',
        'limits': '字段缺失降级不编造；文件级导出属 v2',
        'refs': ['K-01', 'K-03'],
    },
    'zonal_stats': {
        'scale': '宏观/中观（单元聚合）',
        'semantics': '情绪点按边界单元的统计聚合——宏观倾向判断',
        'limits': '非逐户调查结论；社区数口径见 K-C1；勿当精确诊断',
        'refs': ['K-01', 'K-C1'],
    },
    'buffer': {
        'scale': '中观（设施影响圈）',
        'semantics': '设施周边半径内的情绪聚合（半径语义=尺度表·社区250/区500/主城1000）',
        'limits': '半径为可达性近似非服务边界；结论属影响面判断',
        'refs': ['K-C1'],
    },
    'rank': {
        'scale': '中观（排序落点）',
        'semantics': '按极性指数的单元排序（最差/最好 Top-N）',
        'limits': '排序基于聚合指标非原始诉求逐条复核；"最差"为统计表述',
        'refs': ['K-01'],
    },
    'render_spec': {
        'scale': '呈现层',
        'semantics': '图层图纸（数据引用+样式令牌）——由前端解析渲染',
        'limits': 'v1 语义令牌（无解析副本·场景S 双载留 v2）；非分析操作',
        'refs': ['G-2(显示徽标)', '渲染契约v1'],
    },
}


def _reject_analysis_output(preset_id, param, caliber):
    """G-2/铁律7 服务端强制：analysis_output 结论层禁作空间操作输入（PT-CB5 审计发现即修）。"""
    try:
        with open(MANIFEST, encoding='utf-8') as _fp:
            for _g in json.load(_fp):
                for _it in _g.get('items', []):
                    if _it.get('id') == preset_id and _it.get('usage') == 'analysis_output':
                        return {'ok': False, 'hint': (
                            f'{param}={preset_id} 是结论层（usage=analysis_output·铁律7 禁作分析输入）；'
                            '请改用 input 层（调用 list_data 查看清单与 usage 标记）'), 'caliber': caliber}
    except Exception:
        pass   # manifest 不可用时不阻塞（G8b 枚举层仍有引导）
    return None

_UNKNOWN_HINT = '未知层 id·调用 list_data 查看清单'


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'))


def _jsonable(value):
    """把 numpy/pandas 标量归一为 JSON 原生类型（MCP 序列化安全）。"""
    if value is None:
        return ''
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value
    item = getattr(value, 'item', None)
    if callable(item):
        try:
            value = item()
        except Exception:
            pass
    if isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


def _gdf_rows(gdf, agg_cols=None):
    """聚合结果转 AI 友好行（NaN 转空串·numpy 标量转原生）。"""
    import pandas as pd

    cols = ['name', 'point_count', 'polarity_index', 'score_mean',
            'domain_top', 'element_top', 'issue_label', 'attribution', 'suggestion',
            'place_name', 'place_name_source', 'poi_names', 'poi_count']
    for c in (agg_cols or []):
        if f'{c}_sum' in gdf.columns and f'{c}_sum' not in cols:
            cols.append(f'{c}_sum')
    cols = [c for c in cols if c in gdf.columns]
    rows = []
    for _, row in gdf.iterrows():
        item = {}
        for c in cols:
            v = row.get(c, '')
            try:
                if pd.isna(v):
                    v = ''
                else:
                    v = _jsonable(v)
            except Exception:
                v = _jsonable(v)
            item[c] = v
        rows.append(item)
    return rows


def _layer_output_geojson(gdf, top_n, value_col):
    """layer_output=True 时：仅 top_n 行对应多边形 → FeatureCollection（properties 含统计值+value）。"""
    subset = gdf.head(int(top_n)).copy()
    if value_col in subset.columns:
        subset['value'] = subset[value_col]
    return json.loads(subset.to_json())


@track('MOD_AIQA.F_021', track_args=False)
def list_data(include_demo: bool = False) -> dict:
    """数据说明书：列出可分析点层与边界 preset（字段/类型/usage·不含样例值）。

    清单口径（F1）：点层 = resolve 可解析集（list_point_layers 的 available 项），
    不再按 level 过滤——保证与 zonal_stats 等工具的实际解析能力一致。
    include_demo 参数保留兼容，当前不改变清单口径。

    Args:
        include_demo: 兼容保留（F1 起清单恒为可解析集）。
    """
    from core.config import PERFORMANCE_DIR
    from core.geo_registry import _POINT_LAYERS, _layer_path, list_point_layers

    point_layers = []
    for p in list_point_layers():
        if not p.get('available'):
            continue
        data_nature = 'real'
        entry = _POINT_LAYERS.get(p.get('id'))
        if entry is not None:
            try:
                path = os.path.normpath(_layer_path(entry))
                data_nature = 'demo' if path.startswith(os.path.normpath(PERFORMANCE_DIR) + os.sep) else 'real'
            except Exception:
                data_nature = 'demo' if str(p.get('level', '')).upper() != 'CHECKUP' else 'real'
        else:
            data_nature = 'demo' if str(p.get('level', '')).upper() != 'CHECKUP' else 'real'
        point_layers.append({
            'id': p.get('id'),
            'label': p.get('label'),
            'level': p.get('level'),
            'fields': p.get('fields', []),
            'dtypes': p.get('dtypes', {}),
            'crs': p.get('crs', 'EPSG:4326'),
            'usage': 'input',
            'data_nature': data_nature,
        })

    try:
        with open(MANIFEST, 'r', encoding='utf-8') as fh:
            groups = json.load(fh)
    except Exception as exc:
        return {'ok': False, 'hint': f'manifest 读取失败: {exc}', 'caliber': CALIBERS['list_data']}

    presets = []
    for group in groups:
        for it in group.get('items', []):
            fname = str(it.get('file', ''))
            geometry = 'unknown'
            if fname.lower().endswith('.geojson'):
                geometry = 'polygon' if it.get('nameField') else 'point'
            presets.append({
                'id': it.get('id'),
                'label': it.get('label'),
                'geometry': geometry,
                'usage': it.get('usage', 'input'),
                'name_field': it.get('nameField'),
                'data_nature': it.get('data_nature', 'real'),
            })

    return {
        'point_layers': point_layers,
        'presets': presets,
        'count': len(point_layers) + len(presets),
        'caliber': CALIBERS['list_data'],
    }


@track('MOD_AIQA.F_022', track_args=False)
def rag_query(query: str, k: int = 5, synthesize: bool = False) -> dict:
    """带来源知识检索：返回 Top-K 素材与维度分布（v1 不调 LLM 综合）。

    Args:
        query: 检索问题（开放语义）。
        k: Top-K（1-10，自动夹取）。
        synthesize: True 时 v1 诚实降级 deferred_v2（附宿主综合指引）。
    """
    if not query or not str(query).strip():
        return {'ok': False, 'hint': 'query 不能为空', 'caliber': CALIBERS['rag_query']}

    k = max(1, min(int(k), 10))
    try:
        from tools.rag_index import search
        r = search(str(query), k)
    except Exception as exc:
        return {'ok': False, 'hint': f'检索失败: {exc}', 'caliber': CALIBERS['rag_query']}

    if not r.get('ok'):
        return {
            'ok': False,
            'hint': '索引未构建：py tools/rag_index.py --build',
            'error': r.get('error', ''),
            'caliber': CALIBERS['rag_query'],
        }

    dim_counts = {}
    for res in r.get('results', []):
        d = res.get('data_dim', '社区')
        dim_counts[d] = dim_counts.get(d, 0) + 1

    out = {
        'ok': True,
        'results': r.get('results', []),
        'count': r.get('count', 0),
        'dim_counts': dim_counts,
        'synthesize': False,
        'caliber': CALIBERS['rag_query'],
    }
    if synthesize:
        out['synthesize'] = 'deferred_v2'
        out['guidance'] = ('v1 未接后端综合：请宿主基于以上带来源素材综合，'
                           '注明来源与维度；避免把宏观倾向说成微观结论')
    return out


@track('MOD_AIQA.F_023', track_args=False)
def kb_facts(query: str = '', keyword: str = '', topic: str = '',
             limit: int = 5) -> dict:
    """行业事实卡：确定性查询（关键词精确 WHERE·非向量·CB-22f D5 兜底）。

    Args:
        query: 问题短句（真身按 keywords/region 反查命中）。
        keyword: 关键词（空格分词·精确命中加权）。
        topic: 事实卡主题过滤（metric/issue/project 等）。
        limit: 返回条数（1-20）。
    """
    limit = max(1, min(int(limit), 20))
    try:
        from ai_qa.outlet_kb.urban_renewal_knowledge import query_knowledge_base
        facts = query_knowledge_base(query=query or '', city='宜昌',
                                     topic=topic or None, keyword=keyword or None,
                                     limit=limit)
    except Exception as exc:
        return {'ok': False, 'hint': f'kb_facts 失败: {exc}',
                'facts': [], 'count': 0, 'caliber': CALIBERS['kb_facts']}
    return {'facts': facts, 'count': len(facts), 'caliber': CALIBERS['kb_facts']}


@track('MOD_AIQA.F_024', track_args=False)
def outlet_card(question: str = '', result: dict = None, diagnose: dict = None) -> dict:
    """行业出口卡（对话级·确定性组装·零 LLM）。

    Args:
        question: 原始问题。
        result: 分析结果对象（可缺字段）。
        diagnose: 诊断对象（scale/domain_lens/outlet）。
    """
    try:
        from ai_qa.outlet_kb.build_outlet_schema import build_outlet_schema
        cards = build_outlet_schema(diagnose or {}, result or {}, question or '')
    except Exception as exc:
        return {'ok': False, 'hint': f'outlet_card 组装失败: {exc}', 'cards': [],
                'card': None, 'caliber': CALIBERS['outlet_card']}
    return {'cards': cards, 'card': cards[0] if cards else None,
            'caliber': CALIBERS['outlet_card']}


@track('MOD_AIQA.F_025', track_args=False)
def zonal_stats(boundary: str, layer: str = 'yichang_l2_t1',
                agg_cols: list = None, top_n: int = 10,
                layer_output: bool = False) -> dict:
    """单元聚合：情绪点按边界单元统计（首次调用含 geopandas 冷启动约 10-20s）。

    Args:
        boundary: 边界 preset id（先经 list_data 查询）。
        layer: 点层 id（默认 yichang_l2_t1）。
        agg_cols: 聚合数值列（默认 ['score']）。
        top_n: 返回 Top-N 行（1-20，rows 硬顶 20）。
        layer_output: True 时返回值增 geojson（仅 top_n 行多边形）。
    """
    try:
        from core.geo_registry import resolve_boundary, resolve_points
        from core.spatial_analysis import aggregate_by_polygons

        _g = _reject_analysis_output(boundary, 'boundary', CALIBERS['zonal_stats'])
        if _g:
            return _g
        points = resolve_points(layer)
        polys = resolve_boundary(boundary)
        cols = agg_cols or (['score'] if 'score' in points.columns else [])
        merged = aggregate_by_polygons(points, polys, agg_cols=cols,
                                       polygon_name_col='name')
        sort_col = 'polarity_index' if 'polarity_index' in merged.columns else next(
            (f'{c}_sum' for c in cols if f'{c}_sum' in merged.columns), 'point_count')
        merged = merged.sort_values(
            by=sort_col,
            key=(lambda s: s.abs() if sort_col == 'polarity_index' else s),
            ascending=False, kind='stable')
        row_count = int(len(merged))
        top_n = max(1, min(int(top_n), 20))
        top_rows = merged.head(top_n)
        rows = _gdf_rows(top_rows, cols)
        out_geojson = _layer_output_geojson(merged, top_n, sort_col) if layer_output else None
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': CALIBERS['zonal_stats']}
    except Exception as exc:
        return {'ok': False, 'hint': f'zonal_stats 失败: {exc}', 'caliber': CALIBERS['zonal_stats']}

    out = {'rows': rows, 'row_count': row_count, 'truncated': row_count > len(rows),
           'caliber': CALIBERS['zonal_stats']}
    if layer_output:
        out['geojson'] = out_geojson
    return out


@track('MOD_AIQA.F_026', track_args=False)
def buffer(center: str, radius_m: int = 500, layer: str = 'yichang_l2_t1',
           dissolve: bool = True) -> dict:
    """缓冲影响圈：设施周边半径范围 + 圈内情绪点计数。

    Args:
        center: 中心 preset id（先经 list_data 查询）。
        radius_m: 半径米（50-3000）。
        layer: 圈内点计数用点层 id。
        dissolve: True 合并为单一覆盖区。
    """
    try:
        from core.buffer_analysis import create_buffer
        from core.geo_registry import resolve_boundary, resolve_points
        from shapely.geometry import shape

        radius_m = max(50, min(int(radius_m), 3000))
        _g = _reject_analysis_output(center, 'center', CALIBERS['buffer'])
        if _g:
            return _g
        center_gdf = resolve_boundary(center)
        fc, area_km2 = create_buffer(center_gdf.__geo_interface__, radius_m, dissolve)

        point_count = 0
        if layer:
            pts = resolve_points(layer)
            polys = [shape(f['geometry']) for f in fc.get('features', [])]
            for geom in pts.geometry:
                if any(poly.contains(geom) for poly in polys):
                    point_count += 1
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': CALIBERS['buffer']}
    except Exception as exc:
        return {'ok': False, 'hint': f'buffer 失败: {exc}', 'caliber': CALIBERS['buffer']}

    fc_json = json.dumps(fc, ensure_ascii=False)
    include_fc = len(fc.get('features', [])) <= 5 and len(fc_json) <= 100000
    out = {'area_km2': float(area_km2), 'point_count': int(point_count),
           'caliber': CALIBERS['buffer']}
    if include_fc:
        out['buffer_fc'] = fc
    else:
        out['fc_omitted'] = True
        out['hint'] = '缓冲几何较大·请用 EMC 前端渲染 v2'
    return out


@track('MOD_AIQA.F_027', track_args=False)
def rank(by: str = 'worst', layer: str = 'yichang_l2_t1',
         boundary: str = '', top_n: int = 5,
         layer_output: bool = False) -> dict:
    """排序评价：按极性指数找最差/最好 Top-N 单元（先聚合再排）。

    Args:
        by: worst（最负在前）| best（最正在前）。
        layer: 点层 id。
        boundary: 边界 preset id。
        top_n: 返回行数（1-20）。
        layer_output: True 时返回值增 geojson（仅 top_n 行多边形）。
    """
    if not boundary:
        return {'ok': False, 'hint': 'rank 需 boundary（先 zonal 聚合再排）',
                'caliber': CALIBERS['rank']}
    try:
        from core.geo_registry import resolve_boundary, resolve_points
        from core.spatial_analysis import aggregate_by_polygons

        _g = _reject_analysis_output(boundary, 'boundary', CALIBERS['rank'])
        if _g:
            return _g
        points = resolve_points(layer)
        polys = resolve_boundary(boundary)
        cols = ['score'] if 'score' in points.columns else []
        merged = aggregate_by_polygons(points, polys, agg_cols=cols,
                                       polygon_name_col='name')
        if 'polarity_index' not in merged.columns:
            return {'ok': False, 'hint': 'rank 需层含 polarity_index（先 zonal_stats 聚合）',
                    'caliber': CALIBERS['rank']}
        by = (by or 'worst').lower()
        ascending = (by == 'worst')
        merged = merged.sort_values('polarity_index', ascending=ascending, kind='stable')
        row_count = int(len(merged))
        top_n = max(1, min(int(top_n), 20))
        top_rows = merged.head(top_n)
        rows = _gdf_rows(top_rows, cols)
        out_geojson = _layer_output_geojson(merged, top_n, 'polarity_index') if layer_output else None
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': CALIBERS['rank']}
    except Exception as exc:
        return {'ok': False, 'hint': f'rank 失败: {exc}', 'caliber': CALIBERS['rank']}

    out = {'rows': rows, 'row_count': row_count, 'caliber': CALIBERS['rank']}
    if layer_output:
        out['geojson'] = out_geojson
    return out


def _dataset_meta(dataset_id):
    """dataset_id → {usage, data_nature}（preset 读 manifest·点层按池路径·未知 None）。"""
    try:
        with open(MANIFEST, 'r', encoding='utf-8') as fh:
            for group in json.load(fh):
                for it in group.get('items', []):
                    if it.get('id') == dataset_id:
                        return {'usage': it.get('usage', 'input'),
                                'data_nature': it.get('data_nature', 'real')}
    except Exception:
        pass
    try:
        from core.config import PERFORMANCE_DIR
        from core.geo_registry import _POINT_LAYERS, _layer_path, list_point_layers
        for p in list_point_layers():
            if p.get('id') == dataset_id and p.get('available'):
                entry = _POINT_LAYERS.get(dataset_id)
                nature = 'real'
                if entry is not None:
                    path = os.path.normpath(_layer_path(entry))
                    nature = 'demo' if path.startswith(os.path.normpath(PERFORMANCE_DIR) + os.sep) else 'real'
                return {'usage': 'input', 'data_nature': nature}
    except Exception:
        pass
    return None


@track('MOD_AIQA.F_028', track_args=False)
def render_spec(kind: str, name: str, dataset_id: str = '', geojson: dict = None,
                scheme: str = '', value_field: str = 'polarity_index',
                ramp_hint: str = '', zoom_to: bool = True, producer: str = 'dsh',
                source_tool: str = 'manual', data_nature: str = 'real',
                community_caliber: int = 0) -> dict:
    """图层图纸（render spec v1）：dataset 引用或内联 GeoJSON → 收件箱 JSON。

    产物经 8080 前端显示屏呈现（需浏览器已打开情绪地图页面）；
    写盘 = DATA/exports/render_inbox/<spec_id>.json（毫秒级·不渲染）。

    Args:
        kind: point | choropleth。
        name: 图层名（现实内容·前端加 [dsh] 前缀）。
        dataset_id: preset 或点层 id（与 geojson 二选一·同时给以 dataset_id 为准）。
        geojson: 内联 FeatureCollection（要素 ≤60）。
        scheme: community_choropleth_v1 | point_default_v1（缺省按 kind 推导）。
        value_field: choropleth 取值字段（默认 polarity_index）。
        ramp_hint: worst_first 可选（其余省略）。
        zoom_to: True 前端铺层后缩放至图层。
        producer: 生产者标识（默认 dsh）。
        source_tool: 来源工具（rank | zonal_stats | manual）。
        data_nature: real | demo（inline 由调用方声明·dataset 由池路径判定）。
        community_caliber: 社区口径（174|154|118|130…·填则入 caliber_lite.community）。
    """
    if kind not in ('point', 'choropleth'):
        return {'ok': False, 'hint': f'kind 非法: {kind!r}（仅 point|choropleth）',
                'caliber': CALIBERS['render_spec']}
    if not name or not str(name).strip():
        return {'ok': False, 'hint': 'name 必填（现实内容命名）',
                'caliber': CALIBERS['render_spec']}

    # P+ scheme 受管词表（旧 token 机制不再产出）
    resolved_scheme = scheme or ('point_default_v1' if kind == 'point' else 'community_choropleth_v1')
    if resolved_scheme not in SCHEMES:
        return {'ok': False, 'hint': f'scheme 未注册: {resolved_scheme}（词表: {", ".join(SCHEMES)}）',
                'caliber': CALIBERS['render_spec']}

    fixes = []
    usage = 'input'
    nature = data_nature if data_nature in ('real', 'demo') else 'real'
    data = {}
    if dataset_id:
        meta = _dataset_meta(dataset_id)
        if meta is None:
            return {'ok': False, 'hint': f'未知 dataset_id: {dataset_id}（调用 list_data 查看清单）',
                    'caliber': CALIBERS['render_spec']}
        usage = meta['usage']
        nature = meta['data_nature']
        data = {'dataset_id': dataset_id}
        if geojson is not None:
            fixes.append('dataset_id 与 geojson 同时给·以 dataset_id 为准')
    elif geojson is not None:
        if not isinstance(geojson, dict) or geojson.get('type') != 'FeatureCollection':
            return {'ok': False, 'hint': 'geojson 必须是 FeatureCollection',
                    'caliber': CALIBERS['render_spec']}
        feats = geojson.get('features') or []
        if len(feats) > 60:
            return {'ok': False, 'hint': '内联要素 >60·请改用 dataset_id 引用',
                    'caliber': CALIBERS['render_spec']}
        data = {'geojson': geojson}
    else:
        return {'ok': False, 'hint': 'data 二选一必填：dataset_id 或 geojson',
                'caliber': CALIBERS['render_spec']}

    if kind == 'choropleth' and not value_field:
        return {'ok': False, 'hint': 'choropleth 须 value_field 非空',
                'caliber': CALIBERS['render_spec']}

    style = {'scheme': resolved_scheme, 'value_field': value_field}
    if ramp_hint:
        style['ramp_hint'] = ramp_hint

    caliber_lite = {'usage': usage, 'data_nature': nature, 'note': '; '.join(fixes)}
    if community_caliber:
        caliber_lite['community'] = int(community_caliber)

    spec_id = f'{int(time.time() * 1000)}-{random.randint(1000, 9999)}'
    spec = {
        'spec_version': 1,
        'spec_id': spec_id,
        'kind': kind,
        'data': data,
        'style': style,
        'ui': {'name': str(name).strip(), 'zoom_to': bool(zoom_to)},
        'origin': {'producer': producer, 'source_tool': source_tool},
        'caliber_lite': caliber_lite,
    }

    inbox_dir = os.path.join(REPO, 'DATA', 'exports', 'render_inbox')
    os.makedirs(inbox_dir, exist_ok=True)
    inbox_path = os.path.join(inbox_dir, f'{spec_id}.json')
    with open(inbox_path, 'w', encoding='utf-8', newline='') as fh:
        json.dump(spec, fh, ensure_ascii=False)

    return {'ok': True, 'spec_id': spec_id, 'inbox_path': inbox_path,
            'caliber': CALIBERS['render_spec']}


def build_server():
    """惰性装配 FastMCP（mcp 包仅在真正启动 server 时 import）。"""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP('EMC 标准插座（分析七件套 + render_spec）')
    server.tool()(list_data)
    server.tool()(rag_query)
    server.tool()(kb_facts)
    server.tool()(outlet_card)
    server.tool()(zonal_stats)
    server.tool()(buffer)
    server.tool()(rank)
    server.tool()(render_spec)
    return server


def main():
    _safe_print('[OK] EMC MCP server stdio 启动（Ctrl+C 退出）')
    build_server().run()


if __name__ == '__main__':
    main()
