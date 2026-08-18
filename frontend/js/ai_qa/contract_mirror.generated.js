// ═══ contract_mirror.generated.js — 前端契约镜像（自动生成·禁手改）═══
// 单一源 = ai_qa/tool_contracts.py（铁律 11）。再生成：py tools/gen_stages_mirror.py
// CI 守护 = tests/validate_skill_params.py::test_mirror_freshness（派生 diff=0）。
// G8a（PT-CB1 T2·2026-08-18）：stages.js 手写 SKILL_DEFS/别名表永久退役。
// 承重纪律（承袭旧手写镜像注释）：rank/buffer/clip/zonal 不硬默认 layer——
//   硬默认会经 validateParams 合并绕过 resolvePointLayer 可见过滤（"只传 L1 却跑 L2"）；
//   contracts 中这些工具的 layer 参数无 default，生成结果自然保持无默认。


export const SKILL_DEFS = {
  concept: {"tool": null, "category": "concept", "required_slots": [], "optional_defaults": {}},
  density: {"tool": "density", "category": "single", "required_slots": [], "optional_defaults": {"polarity": "overall", "mode": "2d", "radius": 300, "cell_size": 600, "weightField": "emotion_intensity"}},
  rank: {"tool": "rank", "category": "single", "required_slots": [], "optional_defaults": {"by": "worst", "top_n": 5}},
  buffer: {"tool": "buffer", "category": "single", "required_slots": ["center"], "optional_defaults": {"radius_m": 500, "agg_cols": ["score"]}},
  clip: {"tool": "clip", "category": "single", "required_slots": ["range"], "optional_defaults": {}},
  overlay: {"tool": "overlay", "category": "single", "required_slots": ["layer_a", "layer_b"], "optional_defaults": {"how": "intersection"}},
  zonal: {"tool": "zonal_stats", "category": "single", "required_slots": ["boundary"], "optional_defaults": {"agg_cols": ["score"]}},
  compare: {"tool": "compare_regions", "category": "single", "required_slots": ["boundaries"], "optional_defaults": {"agg_cols": ["score", "polarity_index"]}},
  extract_feature: {"tool": "extract_feature", "category": "single", "required_slots": ["layer"], "optional_defaults": {}},
  area_stats: {"tool": "area_stats", "category": "single", "required_slots": ["boundary"], "optional_defaults": {}},
  merge: {"tool": "merge", "category": "single", "required_slots": [], "optional_defaults": {}},
  nearest: {"tool": "nearest", "category": "single", "required_slots": ["target"], "optional_defaults": {"k": 1}},
  lookup_place: {"tool": "lookup_place", "category": "single", "required_slots": [], "optional_defaults": {}},
  hotspot: {"tool": "hotspot", "category": "single", "required_slots": [], "optional_defaults": {"value_col": "score", "threshold": 1.96, "soft_threshold": 1.0}},
  generate_point_layer: {"tool": "generate_point_layer", "category": "single", "required_slots": ["names"], "optional_defaults": {}},
  filter_attr: {"tool": "filter_attr", "category": "single", "required_slots": ["pre_filter"], "optional_defaults": {}},
  multi: {"tool": null, "category": "multi", "required_slots": [], "optional_defaults": {}},
  unknown: {"tool": null, "category": "unknown", "required_slots": [], "optional_defaults": {}},
};

// 每工具全量别名（由 contracts 各工具 params[].alias 派生·G8a 起替代旧「通用+专属」双层手写）。
export const TOOL_ALIAS = {
  density: {"bandwidth_m": "radius", "cell_size_m": "cell_size", "value_col": "weightField", "output": "as", "output_layer": "as", "layer_name": "as", "named": "as", "name": "as"},
  rank: {"sort": "by", "sort_by": "by", "criteria": "by", "top": "top_n", "limit": "top_n", "n": "top_n", "zone": "boundary", "region": "boundary"},
  buffer: {"point": "center", "center_point": "center", "radius": "radius_m", "radius_meters": "radius_m", "buffer_radius": "radius_m", "distance": "radius_m"},
  clip: {"output": "as", "output_layer": "as", "layer_name": "as", "named": "as", "name": "as"},
  overlay: {"mode": "how", "output": "as", "output_layer": "as", "layer_name": "as", "named": "as", "name": "as"},
  zonal_stats: {"zone": "boundary", "region": "boundary", "top": "top_n", "limit": "top_n", "n": "top_n"},
  compare_regions: {"regions": "boundaries", "areas": "boundaries"},
  extract_feature: {"output": "as", "output_layer": "as", "layer_name": "as", "named": "as", "name": "as"},
  area_stats: {"zone": "boundary", "region": "boundary", "by": "group_by"},
  merge: {"zone": "boundary", "region": "boundary", "layer_list": "layers", "layers_list": "layers", "sort": "by", "sort_by": "by", "criteria": "by", "output": "as", "output_layer": "as", "layer_name": "as", "named": "as", "name": "as"},
  nearest: {"target_layer": "target", "target_poi": "target"},
  lookup_place: {"query": "q", "name": "q", "place": "q", "lon": "lng", "x": "lng", "y": "lat"},
  hotspot: {"value": "value_col", "column": "value_col", "field_name": "value_col", "inverse": "invert", "output": "as", "output_layer": "as", "layer_name": "as", "named": "as", "name": "as"},
  generate_point_layer: {"items": "names", "places": "names", "projects": "names", "name_list": "names", "output": "as", "output_layer": "as", "layer_name": "as", "named": "as", "name": "as"},
  filter_attr: {"output": "as", "output_layer": "as", "layer_name": "as", "named": "as", "name": "as"},
};
