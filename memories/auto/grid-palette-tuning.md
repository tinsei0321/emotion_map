---
name: grid-palette-tuning
description: "L1 grid-warm 色板 renorm 位置(红段收窄) + L2 极性 green/red/blue-3 6段 + 3D FOV/东北光/#map背景随底图"
metadata: 
  node_type: memory
  type: reference
  originSessionId: afd04aa7-761a-4109-ad75-de3d7cb224f1
---

网格色板 + 3D 透视/光照参数（2026-07-01 用户多轮调定，feature/kde-l2-3d）。

**L1 grid-warm 色板**（[state.js HEATMAP_RAMPS['grid-warm']](frontend/js/state.js)，单源 legend/预览/格层全跟）：红段收窄、过渡段对齐数据主体（γ=0.5 下 q25-q90 _grid_h 落 0.12-0.40），避"大面积红"。normStops renorm 后 `[0/0.15/0.30/0.50/0.78/1.0] = [#8B0000(暗红低不变)/#C92A20(鲜红)/#F06428(红橙)/#FF9900(橙黄·用户指定中)/#FFC63C(橙金)/#FFDF00(亮金·用户指定顶)]`。改色改 stops 即可（renorm 自动）。

**L2 极性 ramp**：green-3/red-3/blue-3 = `gradientStops(TERRAIN_*, 6)`（6 段，中间过渡多、张力；2026-07-01 由 3 段改 6 段）。颜色 field = `_grid_h_pos/neg/neu`（见 [[extrusion-height-maxheight]]）。

**3D 透视**（[map.js initMap](frontend/js/map.js)）：`map.setVerticalFieldOfView(55)`（MapLibre v5，单位**度**，默认 36.87° 长焦压缩→疑似轴测；加宽到 55 近高远矮）。方向光 `map.setLight({anchor:'viewport', position:[1.5,45,60], intensity:0.5})`——position=[r,方位°(0=上/北·顺时针),极角°(0=正上/90=水平)]，**45=东北来光**(亮面朝 NE/暗面朝 SW，默认北朝上视角四梯度清晰)，极角 60 偏低侧光强化明暗。FOV 设一次（camera 抗 setStyle），light `map.on('style.load', …)` 重敷（属 style，切底图会重置）。

**3D 上沿白条**：FOV55+pitch60 视口上沿露 `#map` 容器白底 → `setBasemap` 按 basemap 设容器背景（dark-matter→#0e0e0e/positron→白/voyager→米/天地图→浅蓝），露空区融入。

关联：[[extrusion-height-maxheight]]、[[ramp-discrete-segments]]、[[symmetric-norm-stretch]](piToNorm 替代)。
