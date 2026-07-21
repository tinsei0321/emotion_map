"""
测试地理编码模块（core/geocode.py）— Phase 2

重点（红线 #2）：高德返回 GCJ-02 必须转 WGS84，漏转 = 50-500m 静默偏移。
用 _gcj_loc_to_wgs 的往返误差 <1m 守住这条红线（模拟正向地理编码链路）。

本地路径（search_place / reverse_geocode）走 place_layer，不依赖网络；
结构测试 monkeypatch AMAP_KEY='' 强制 local-only，保证确定性。
"""
import math
import pytest

import core.geocode as geocode
from core.geocode import (
    search_place,
    geocode_address,
    reverse_geocode,
    _gcj_loc_to_wgs,
)
from core.coord_transform import wgs84_to_gcj02


def _haversine_m(lng1, lat1, lng2, lat2):
    """两点（度）球面距离（米）—— 断言偏移量用。"""
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ── 红线 #2：CRS 转换正确性（核心单测）──

class TestCrsRoundtrip:
    """高德 location(GCJ-02) → _gcj_loc_to_wgs → WGS84 往返误差须 <1m。

    模拟正向链路：真实 WGS84 点 → wgs84_to_gcj02（= 高德会返回的坐标）
    → 格式化为 'lng,lat' → _gcj_loc_to_wgs 还原。漏转/错转会造成 50-500m 偏移。
    """

    @pytest.mark.parametrize("lng,lat", [
        (111.2877, 30.6919),   # 万达广场（wanda_cbd）
        (111.2905, 30.7050),   # 西陵 core
        (111.3300, 30.7420),   # 伍家岗
        (111.3500, 30.7000),   # 东郊
    ])
    def test_roundtrip_within_1m(self, lng, lat):
        gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
        loc_str = '{:.6f},{:.6f}'.format(gcj_lng, gcj_lat)
        wgs = _gcj_loc_to_wgs(loc_str)
        assert wgs is not None
        d = _haversine_m(lng, lat, wgs[0], wgs[1])
        assert d < 1.0, 'GCJ-02->WGS84 往返偏移 {:.2f}m（应 <1m，漏转红线）'.format(d)

    def test_bad_location_returns_none(self):
        assert _gcj_loc_to_wgs('') is None
        assert _gcj_loc_to_wgs(None) is None
        assert _gcj_loc_to_wgs('not-a-coord') is None

    def test_out_of_china_passthrough(self):
        """境外点（无偏移算法）应原样返回，不报错。"""
        wgs = _gcj_loc_to_wgs('0.000000,0.000000')
        assert wgs == (0.0, 0.0)


# ── 本地搜索（place_layer 主；强制 local-only 不触网）──

class TestSearchPlaceLocal:
    """本地 1270 POI 即时搜索（rapidfuzz/difflib）。"""

    def test_known_poi_returns_hits(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')   # 强制 local-only
        hits = search_place('万达', limit=10)
        assert isinstance(hits, list)
        assert len(hits) > 0
        h = hits[0]
        assert 'name' in h and 'lng' in h and 'lat' in h
        assert h['source'] == 'local'
        # P3: zone_color 字段（前端色点用）
        assert 'zone_color' in h and h['zone_color'].startswith('#')
        # 万达应在 wanda_plaza 叙事区（zone_name 非空）
        assert h.get('zone_name', '') != ''

    def test_empty_query_returns_empty(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')
        assert search_place('', limit=10) == []
        assert search_place('   ', limit=10) == []
        assert search_place(None, limit=10) == []

    def test_hits_are_wgs84_in_yichang(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')
        hits = search_place('广场', limit=5)
        for h in hits:
            # 宜昌经度 111-112、纬度 30-31；落此区间即 WGS84 合理（GCJ-02 偏移也在度级内）
            assert 110.0 < h['lng'] < 112.0
            assert 30.0 < h['lat'] < 31.0

    def test_limit_respected(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')
        hits = search_place('路', limit=3)
        assert len(hits) <= 3


# ── 逆地理编码（本地 reverse 主；强制 local-only）──

class TestReverseGeocodeLocal:
    """坐标 → 所在区 + 最近 POI（place_layer.reverse）。"""

    def test_structure(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')   # local-only，不触网
        res = reverse_geocode(111.29, 30.69)
        assert isinstance(res, dict)
        for key in ('zone_id', 'zone_name', 'nearest_poi', 'formatted_address', 'source'):
            assert key in res
        # local-only 时无街道地址、source=local
        assert res['formatted_address'] == ''
        assert res['source'] == 'local'

    def test_nearest_poi_shape(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')
        res = reverse_geocode(111.29, 30.69)
        near = res['nearest_poi']
        assert near is None or ('name' in near and 'dist_m' in near)


# ── amap 兜底降级（红线 #1：Key 缺失只 local）──

class TestAmapDisabledFallback:
    """AMAP_KEY 缺失/requests 不可用时，高德分支优雅降级。"""

    def test_search_local_only_when_key_missing(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')
        assert geocode._amap_enabled() is False
        # 本地仍可用
        hits = search_place('万达', limit=5)
        assert len(hits) > 0
        assert all(h['source'] == 'local' for h in hits)

    def test_geocode_returns_none_when_key_missing(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')
        assert geocode_address('宜昌万达广场') is None

    def test_reverse_still_local_when_key_missing(self, monkeypatch):
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')
        res = reverse_geocode(111.29, 30.69)
        assert res['source'] == 'local'


# ── 追踪 ID 已注册（铁律 10：编号入 _TRACKING_REGISTRY）──

class TestTrackingRegistered:
    def test_mod_geocode_ids_registered(self):
        from core.tracker import list_track_ids
        ids = list_track_ids()
        for tid in (
            'MOD_GEOCODE.F_001', 'MOD_GEOCODE.F_002',
            'MOD_GEOCODE.F_003', 'MOD_GEOCODE.F_004',
            'MOD_GEOCODE.D_001', 'MOD_GEOCODE.D_002',
        ):
            assert tid in ids, '未注册: {}'.format(tid)


# ── 拼音模糊匹配（Search v2 · Phase D；依赖 pypinyin，缺失则跳过）──

class TestPinyinForward:
    def test_initial_pinyin_matches_wanda(self):
        pytest.importorskip('pypinyin')
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('wd', 5)
        assert any('万达' in h['name'] for h in hits), 'wd 应命中万达（首字母拼音）'

    def test_full_pinyin_matches_wanda(self):
        pytest.importorskip('pypinyin')
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('wanda', 5)
        assert any('万达' in h['name'] for h in hits), 'wanda 应命中万达（全拼）'

    def test_chinese_still_matches(self):
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('万达', 5)
        assert any('万达' in h['name'] for h in hits)


# ── 分层排名（Search v2.1：exact > prefix > substring，修「金缔华城→苏宁易购」类 bug）──

class TestTieredRanking:
    def test_exact_beats_substring_jindihuacheng(self):
        """金缔华城（本体，exact 300）必须排在 苏宁易购(金缔华城店)（substring 200）之前。"""
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('金缔华城', 10)
        assert hits, '金缔华城 应有命中'
        assert hits[0]['name'] == '金缔华城', '首条应为精确匹配，实为 ' + repr(hits[0]['name'])

    def test_exact_beats_substring_shuiyuecheng(self):
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('水悦城', 10)
        assert hits[0]['name'] == '水悦城'

    def test_prefix_ranking_suning(self):
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('苏宁', 5)
        assert hits and '苏宁' in hits[0]['name']


# ── 落水过滤（Search v2.1：现状水系内的 POI 不进搜索结果，导出标 in_water）──
# v2.2：all_pois 改 amap-only，落水点 ~5（seed 退命名不再入库）。

class TestWaterFilter:
    def test_in_water_flag_set(self):
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        flagged = [p for p in pl.all_pois if p.get('_in_water')]
        assert 0 < len(flagged) < 20   # amap-only 贴/落水点 ~5

    def test_forward_excludes_water(self):
        """落水 POI（如「求索溪」）不应出现在搜索结果。"""
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        water_names = {p['name'] for p in pl.all_pois if p.get('_in_water')}
        assert any('求索溪' in n or '垂钓' in n for n in water_names), '应有已知落水点'
        hits = pl.forward('求索', 30)
        result_names = {h['name'] for h in hits}
        leak = result_names & water_names
        assert not leak, '搜索结果含落水点: ' + str(leak)

    def test_search_still_returns_dry_pois(self):
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('二马路', 10)
        assert hits and any('二马路' in h['name'] for h in hits)


# ── Zone v2.2 归类（12 zone：7 商圈 + 4 非商业 + general）──
# 基于本地知识校准：水悦城/中南路/万达/夷陵CBD 等独立商圈分离。

class TestZoneV2:
    def _zone_of(self, q):
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        for p in pl.all_pois:
            if q in (p.get('name') or ''):
                return pl.resolve_zone(p['name'], p.get('area', ''), p['lng'], p['lat'])
        return None

    def test_shuiyuecheng_zone(self):
        assert self._zone_of('水悦城') == 'shuiyuecheng'

    def test_xingfa_zhongnan(self):
        # 兴发广场在中南路（非夷陵CBD）—— seed 坐标曾错标
        assert self._zone_of('兴发广场') == 'zhongnan_road'

    def test_wanda_plaza(self):
        assert self._zone_of('伍家岗万达') == 'wanda_plaza'

    def test_yiling_cbd_guomao(self):
        # 国贸大厦在夷陵广场CBD
        assert self._zone_of('国贸大厦') == 'yiling_cbd'

    def test_wuyue_square(self):
        assert self._zone_of('吾悦广场') == 'wuyue_square'

    def test_yiling_wanda_separate(self):
        # 夷陵万达（夷陵区）≠ 万达广场（wanda_plaza）
        assert self._zone_of('夷陵万达') == 'yiling_wanda'

    def test_fujiuyuan_wuyi(self):
        # 福久源在五一广场
        assert self._zone_of('福久源') == 'wuyi_square'

    def test_no_wanda_cbd(self):
        """wanda_cbd zone 应已删除（拆成 7 商圈）。"""
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        assert 'wanda_cbd' not in pl.zone_by_id
        assert 'yiling_cbd' in pl.zone_by_id
        assert 'shuiyuecheng' in pl.zone_by_id


# ── P2 离线退化：AMAP 不可用时模糊阈值从 55 降至 35 ──

class TestOfflineDegradation:
    """P2 geocode 离线退化：离线时 forward() 使用更低的模糊阈值获取更多近似结果。"""

    def test_relaxed_threshold_returns_more(self):
        """min_fuzzy_score=35 应 >= default(=55) 的结果数。"""
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        # limit 留足余量（200）：语料扩容后 '东站' default≈46 / relaxed≈56，
        # 原 limit=30 会把两者都截到 30 → 断言误败。此处取全量不截断比较。
        hits_default = pl.forward('东站', 200)
        hits_relaxed = pl.forward('东站', 200, min_fuzzy_score=35)
        assert len(hits_relaxed) > len(hits_default), \
            'relaxed(35)={} 应 > default(55)={}'.format(
                len(hits_relaxed), len(hits_default))

    def test_relaxed_has_low_scores(self):
        """松弛后应有 score < 55 的命中（证明阈值真被降低了）。"""
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('东站', 200, min_fuzzy_score=35)
        low_scores = [h for h in hits if h['score'] < 55]
        assert len(low_scores) > 0, \
            '松弛阈值应产生 score<55 的命中，实际 {} 条'.format(len(hits))

    def test_search_offline_all_local(self, monkeypatch):
        """离线 search_place 所有结果 source='local'。"""
        monkeypatch.setattr(geocode, 'AMAP_KEY', '')
        assert geocode._amap_enabled() is False
        hits = search_place('万达', limit=5)
        assert len(hits) > 0, '离线应至少返回一些结果'
        assert all(h['source'] == 'local' for h in hits)

    def test_default_threshold_unchanged(self):
        """min_fuzzy_score=None 时阈值仍为 55（在线行为不变）。"""
        from core.place_layer import get_place_layer
        pl = get_place_layer()
        hits = pl.forward('万达', 10)
        # 默认阈值 55：所有结果 score >= 55
        assert len(hits) > 0
        assert all(h['score'] >= 55 for h in hits), \
            '默认阈值应为 55，不应有低分命中'
