"""预设范围测试 — 更新单元编号注入（range_selector）+ 三调用地拆分（ingest_landuse_preset）。

覆盖：
  - load_preset('renewal_unit')：nameField='编号' 时按 feature 序注入「更新单元-NN」。
  - ingest_landuse_preset.inspect：列 DLMC + 计数。
  - ingest_landuse_preset.split：按映射 dissolve + 简化 + 落盘 + 更新 manifest。
"""
import json
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPT_DIR = os.path.join(_ROOT, 'SCRIPT')


# ── 更新单元编号注入 ──

def test_renewal_unit_numbering_injected():
    """nameField='编号' → load_preset 给每 feature 注入「更新单元-NN」（按文件序，不改原文件）。"""
    from core.range_selector import load_preset
    r = load_preset('renewal_unit')
    if not r.get('available'):
        pytest.skip('更新单元 preset 文件未随仓分发（本地数据）；编号注入逻辑见 load_preset nameField=编号 分支')
    assert r['nameField'] == '编号'
    feats = r['geojson']['features']
    assert feats, '应至少 1 个面'
    width = max(2, len(str(len(feats))))
    expect_first = '更新单元-{0:0{w}d}'.format(1, w=width)
    # 每 feature 都被注入 编号，且首条为「更新单元-01/001」
    assert all(f['properties'].get('编号', '').startswith('更新单元-') for f in feats)
    assert feats[0]['properties']['编号'] == expect_first


# ── ingest_landuse_preset ──

@pytest.fixture
def ingest():
    sys.path.insert(0, _SCRIPT_DIR)
    import ingest_landuse_preset as ing
    yield ing
    sys.path.pop(0)


_SYNTH_FC = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "properties": {"DLMC": "零售商业用地"},
         "geometry": {"type": "Polygon", "coordinates": [[[111.28, 30.69], [111.29, 30.69], [111.29, 30.70], [111.28, 30.70], [111.28, 30.69]]]}},
        {"type": "Feature", "properties": {"DLMC": "零售商业用地"},
         "geometry": {"type": "Polygon", "coordinates": [[[111.30, 30.69], [111.31, 30.69], [111.31, 30.70], [111.30, 30.70], [111.30, 30.69]]]}},
        {"type": "Feature", "properties": {"DLMC": "公园绿地"},
         "geometry": {"type": "Polygon", "coordinates": [[[111.32, 30.69], [111.33, 30.69], [111.33, 30.70], [111.32, 30.70], [111.32, 30.69]]]}},
    ],
}


def test_ingest_inspect_lists_dlmc(ingest, tmp_path, capsys):
    src = tmp_path / 'lu.geojson'
    src.write_text(json.dumps(_SYNTH_FC), encoding='utf-8')
    ingest.cmd_inspect(str(src))
    out = capsys.readouterr().out
    assert '零售商业用地' in out and '公园绿地' in out
    assert 'feature 数' in out


def test_ingest_split_dissolves_and_updates_manifest(ingest, tmp_path, monkeypatch):
    src = tmp_path / 'lu.geojson'
    src.write_text(json.dumps(_SYNTH_FC), encoding='utf-8')
    map_path = tmp_path / 'map.json'
    map_path.write_text(json.dumps({"商业": ["零售商业用地"], "公园广场": ["公园绿地"]}), encoding='utf-8')

    # 重定向产出目录与 manifest 到 tmp，避免污染真实 preset
    presets_dir = tmp_path / 'presets'
    presets_dir.mkdir()
    manifest_path = presets_dir / 'manifest.json'
    manifest_path.write_text(json.dumps([
        {"group": "用地筛选（三调）", "items": [
            {"id": "land_commercial", "label": "商业区", "file": "用地_商业.geojson", "nameField": "DLMC"},
        ]}
    ]), encoding='utf-8')
    monkeypatch.setattr(ingest, '_PRESETS_DIR', str(presets_dir))
    monkeypatch.setattr(ingest, '_MANIFEST', str(manifest_path))

    ingest.cmd_split(str(src), str(map_path), tol=5.0)

    # 两个 preset 文件，各 1 个 dissolve 后的 feature
    com = json.loads((presets_dir / '用地_商业.geojson').read_text(encoding='utf-8'))
    park = json.loads((presets_dir / '用地_公园广场.geojson').read_text(encoding='utf-8'))
    assert len(com['features']) == 1 and com['features'][0]['properties']['DLMC'] == '商业'
    assert len(park['features']) == 1 and park['features'][0]['properties']['DLMC'] == '公园广场'
    # manifest 被补全（公园广场 项加入）
    m = json.loads(manifest_path.read_text(encoding='utf-8'))
    ids = {it['id'] for it in m[0]['items']}
    assert {'land_commercial', 'land_park'} <= ids
