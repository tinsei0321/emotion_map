"""PT-CB14 claude 包四件（C1-C4）回归测试。

C1 D-4 qty 点层注册 / C2 D-1 清单一致性 / C3 D-6 测试件标记 / C4 D-7 引擎徽标。
设计：C1-C3 行为断言 + C4 源码契约断言（前端行为移交浏览器实测清单·执行记录见
PT-CB14-修复批claude执行记录_claude-2026-08-24.md）。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, ROOT)

import mcp_server_emc as mse
from core.geo_registry import _POINT_LAYERS, _layer_path, get_layer_points, list_point_layers, resolve_boundary

QTY_IDS = ['qty_合并', 'qty_安全_住房', 'qty_安全_合并', 'qty_安全_安全消防', 'qty_安全_市政管网',
           'qty_民生_交通设施', 'qty_民生_住房', 'qty_民生_停车设施', 'qty_民生_公服设施',
           'qty_民生_合并', 'qty_民生_物业街面']


# ════════════ C1：D-4 qty 点层注册 ════════════

def test_c1_qty_layers_registered_and_readable():
    """11 个 qty 层全注册·子目录 presets·GeoJSON 分支可读（文件真实在盘）。"""
    for lid in QTY_IDS:
        assert lid in _POINT_LAYERS, f'{lid} 未注册'
        entry = _POINT_LAYERS[lid]
        assert entry[2] == 'CHECKUP'
        assert entry[3] == 'DATA/boundaries/presets'
        assert os.path.isfile(_layer_path(entry)), f'{lid} 文件未落盘: {_layer_path(entry)}'
    gdf = get_layer_points('qty_民生_停车设施')
    assert len(gdf) > 0
    assert gdf.crs is not None


def test_c1_list_data_point_layers_reaches_23():
    """验收口径：list_data 点层 = 原 12 + 11 qty = 23（可用层）。"""
    out = mse.list_data()
    ids = [p['id'] for p in out['point_layers']]
    assert len(ids) == 23
    assert 'qty_民生_停车设施' in ids


# ════════════ C2：D-1 清单一致性 ════════════

def test_c2_list_data_presets_filters_missing_files(monkeypatch, tmp_path):
    """presets 段 available 过滤：manifest 已登记但文件未落盘 → 不出现在清单。"""
    reg = tmp_path / 'manifest.json'
    reg.write_text(json.dumps([{'group': 'g', 'items': [
        {'id': 'ok_preset', 'label': '在盘', 'file': 'ok.geojson', 'nameField': 'name', 'usage': 'input'},
        {'id': 'admin_community', 'label': '缺文件', 'file': 'admin_community_official.geojson', 'usage': 'input'},
    ]}], ensure_ascii=False), encoding='utf-8')
    (tmp_path / 'ok.geojson').write_text('{}', encoding='utf-8')
    monkeypatch.setattr(mse, 'MANIFEST', str(reg))
    monkeypatch.setattr('core.geo_registry.list_point_layers', lambda: [])
    out = mse.list_data()
    ids = [p['id'] for p in out['presets']]
    assert 'ok_preset' in ids
    assert 'admin_community' not in ids
    ok = next(p for p in out['presets'] if p['id'] == 'ok_preset')
    assert ok.get('available') is True


def test_c2_resolve_boundary_missing_file_message(monkeypatch):
    """resolve_boundary 报错语义：「文件未落盘·需上传：<file>（manifest 已登记）」含"未落盘"。"""
    monkeypatch.setattr('core.geo_registry.load_preset', lambda b: {'available': False})
    with pytest.raises(FileNotFoundError) as ei:
        resolve_boundary('admin_community')
    assert '未落盘' in str(ei.value)


# ════════════ C3：D-6 测试件标记 ════════════

def test_c3_render_spec_test_nature(monkeypatch, tmp_path):
    """data_nature='test' 透传 caliber_lite（dataset 与 inline 两路径）·默认仍以 dataset meta 为准。"""
    monkeypatch.setattr(mse, 'REPO', str(tmp_path))
    out = mse.render_spec(kind='point', name='测试投递', dataset_id='qty_民生_停车设施', data_nature='test')
    assert out['ok'] is True
    assert out['caliber_lite']['data_nature'] == 'test'
    spec = json.loads(open(out['inbox_path'], encoding='utf-8').read())
    assert spec['caliber_lite']['data_nature'] == 'test'
    os.remove(out['inbox_path'])

    fc = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [111.3, 30.7]},
         'properties': {'name': 'x'}}]}
    out2 = mse.render_spec(kind='point', name='内联测试', geojson=fc, data_nature='test')
    assert out2['ok'] is True
    assert out2['caliber_lite']['data_nature'] == 'test'
    os.remove(out2['inbox_path'])

    # 回归：dataset 路径无显式 test → 以 dataset meta 为准（qty 层=real）
    out3 = mse.render_spec(kind='point', name='默认回归', dataset_id='qty_民生_停车设施')
    assert out3['caliber_lite']['data_nature'] == 'real'
    os.remove(out3['inbox_path'])


def test_c3_render_contract_documents_test_cleanup():
    """render-contract §五 补 test 值 + 清理纪律一行（文档契约）。"""
    with open(os.path.join(ROOT, 'docs', 'render-contract.md'), encoding='utf-8') as f:
        doc = f.read()
    assert 'real / demo / test' in doc
    assert '用毕即删' in doc


# ════════════ C4：D-7 引擎徽标（源码契约断言·行为实测浏览器清单） ════════════

def test_c4_engine_badge_and_dsh_prefix_source():
    """panel.js 徽标函数在位 + brain-adapter 报错前缀 [dsh引擎] + render_client [测试] 徽标分支。"""
    with open(os.path.join(ROOT, 'frontend', 'js', 'ai_qa', 'panel.js'), encoding='utf-8') as f:
        panel = f.read()
    assert '_initEngineBadge' in panel
    assert 'emc-engine-badge' in panel
    assert '引擎·dsh' in panel
    with open(os.path.join(ROOT, 'frontend', 'js', 'ai_qa', 'brain-adapter-dsh.js'), encoding='utf-8') as f:
        dsh = f.read()
    assert '[dsh引擎]' in dsh
    with open(os.path.join(ROOT, 'frontend', 'js', 'render_client.js'), encoding='utf-8') as f:
        rc = f.read()
    assert '[测试]' in rc
