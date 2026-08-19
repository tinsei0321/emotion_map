"""PT-CB6 P · render 通道测试（render_spec / layer_output / watcher / dataset 端点）。"""
import json
import os
import queue
import sys

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, ROOT)

import mcp_server_emc as mse
from api import render_routes


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _fake_manifest(tmp_path, items):
    reg = tmp_path / 'manifest.json'
    _write(reg, json.dumps([{'group': 'g', 'items': items}], ensure_ascii=False))
    return str(reg)


def _patch_render_globals(monkeypatch, tmp_path, manifest_items):
    monkeypatch.setattr(mse, 'MANIFEST', _fake_manifest(tmp_path, manifest_items))
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))


class _FakePoints:
    def __init__(self):
        self.columns = ['score']


class _FakeBoundary:
    pass


def _fake_merged(n=5):
    return gpd.GeoDataFrame({
        'name': [f'单元{i}' for i in range(n)],
        'point_count': list(range(1, n + 1)),
        'polarity_index': [-1.0 + i * 0.4 for i in range(n)],
        'score_mean': [0.1] * n,
        'domain_top': ['治理'] * n,
        'element_top': ['设施'] * n,
        'issue_label': ['停车'] * n,
    }, geometry=[Polygon([(111.2 + i, 30.6), (111.3 + i, 30.6),
                          (111.3 + i, 30.7), (111.2 + i, 30.6)]) for i in range(n)],
       crs='EPSG:4326')


def _patch_geo(monkeypatch, merged):
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda layer: _FakePoints())
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda boundary: _FakeBoundary())
    monkeypatch.setattr('core.spatial_analysis.aggregate_by_polygons',
                        lambda points, polys, agg_cols=None, polygon_name_col=None: merged)


# ════════════ render_spec ════════════

def test_render_spec_writes_inbox_file_with_contract(monkeypatch, tmp_path):
    _patch_render_globals(monkeypatch, tmp_path, [
        {'id': 'base_18village_area', 'label': '18村', 'file': 'a.geojson',
         'nameField': 'SQMC', 'usage': 'analysis_output'},
    ])
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: [])
    out = mse.render_spec(kind='choropleth', name='情绪最差三区',
                          dataset_id='base_18village_area', value_field='polarity_index',
                          source_tool='rank')
    assert out['ok'] is True and out['spec_id']
    fp = out['inbox_path']
    assert os.path.isfile(fp)
    spec = json.loads(open(fp, encoding='utf-8').read())
    assert spec['spec_version'] == 1
    assert spec['kind'] == 'choropleth'
    assert spec['origin']['source_tool'] == 'rank'
    assert spec['caliber_lite']['usage'] == 'analysis_output'
    assert _caliber_ok(out['caliber'])


def _caliber_ok(c):
    return all(k in c for k in ('scale', 'semantics', 'limits', 'refs'))


def test_render_spec_inline_limit_and_missing_data(monkeypatch, tmp_path):
    _patch_render_globals(monkeypatch, tmp_path, [])
    fc = {'type': 'FeatureCollection',
          'features': [{'type': 'Feature', 'geometry': Point(111, 30).__geo_interface__,
                        'properties': {}} for _ in range(61)]}
    out = mse.render_spec(kind='point', name='超限', geojson=fc)
    assert out['ok'] is False and '60' in out['hint']

    out = mse.render_spec(kind='point', name='缺数据')
    assert out['ok'] is False and '二选一' in out['hint']


def test_render_spec_dataset_validation(monkeypatch, tmp_path):
    _patch_render_globals(monkeypatch, tmp_path, [
        {'id': 'base_18village_area', 'label': '18村', 'file': 'a.geojson',
         'nameField': 'SQMC', 'usage': 'analysis_output'},
    ])
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: [])
    out = mse.render_spec(kind='choropleth', name='未知', dataset_id='nope')
    assert out['ok'] is False and '未知 dataset_id' in out['hint']

    out = mse.render_spec(kind='choropleth', name='结论层显示',
                          dataset_id='base_18village_area', value_field='polarity_index')
    assert out['ok'] is True
    assert out['caliber']['refs'][0] == 'G-2(显示徽标)'


# ════════════ zonal / rank layer_output ════════════

def test_zonal_layer_output_geojson_topn_and_default_no_key(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(5))
    out = mse.zonal_stats('admin_district', top_n=3, layer_output=True)
    assert out['geojson']['type'] == 'FeatureCollection'
    assert len(out['geojson']['features']) == 3
    assert 'value' in out['geojson']['features'][0]['properties']

    out_off = mse.zonal_stats('admin_district', top_n=3)
    assert 'geojson' not in out_off


def test_rank_layer_output_geojson_topn(monkeypatch):
    _patch_geo(monkeypatch, _fake_merged(5))
    out = mse.rank(boundary='admin_district', top_n=2, layer_output=True)
    assert len(out['geojson']['features']) == 2
    assert len(out['rows']) == 2


# ════════════ watcher ════════════

def test_watcher_scan_order_and_bad_json_skip(tmp_path):
    inbox = tmp_path / 'inbox'
    _write(inbox / '01.json', json.dumps(
        {'spec_version': 1, 'kind': 'point', 'origin': {'producer': 'dsh', 'source_tool': 'manual'}}))
    _write(inbox / '02.json', '{bad json')
    _write(inbox / '03.json', json.dumps(
        {'spec_version': 1, 'kind': 'choropleth', 'origin': {'producer': 'dsh', 'source_tool': 'rank'}}))

    seen = set()
    q = queue.Queue()
    backlog = []
    pushed = render_routes.scan_inbox(str(inbox), seen, q, backlog)
    assert pushed == 2
    assert q.get()['kind'] == 'point'
    assert q.get()['kind'] == 'choropleth'
    assert len(backlog) == 2


# ════════════ dataset 端点 ════════════

def test_render_dataset_preset_returns_fc(monkeypatch):
    gdf = gpd.GeoDataFrame({'name': ['a']}, geometry=[Point(111, 30)], crs='EPSG:4326')
    monkeypatch.setattr('core.geo_registry.list_boundaries', lambda: [{'id': 'admin_district'}])
    monkeypatch.setattr('core.geo_registry.resolve_boundary', lambda bid: gdf)
    out = render_routes.render_dataset('admin_district')
    assert out['ok'] is True
    assert out['geojson']['type'] == 'FeatureCollection'
    assert out['geojson']['features'][0]['properties']['name'] == 'a'


def test_render_dataset_unknown_returns_hint(monkeypatch):
    monkeypatch.setattr('core.geo_registry.list_boundaries', lambda: [])
    monkeypatch.setattr('core.geo_registry.resolve_points', lambda lid: (_ for _ in ()).throw(KeyError('x')))
    out = render_routes.render_dataset('nope')
    assert out['ok'] is False
    assert 'list_data' in out['hint']
