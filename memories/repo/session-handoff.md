# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：2026-06-28 | 分支 `feature/kde-l2-3d` @ `3006c4f`

## 本会话完成
**P2 空间聚合 Grid 工具**（square/zonal 2D/3D）+ L1 舆论热度（密度×置信度）+ 配套。已 commit `3006c4f`（18 文件 +782/-66）。

要点：
- Grid 工具（`frontend/js/grid-tool.js`）：分析类型导航（聚合域=标准网格 square + 指定单元 zonal；热点 Gi*/Moran's I 占位 dev）、L1/L2 数据联动递进、极性在②网格参数、图层独占（生成时关其他）、深拷贝防数据污染
- **L1 舆论热度 = `point_count × l1_confidence_mean`**（密度×置信度），颜色（grid-warm 暗红→金黄）+ 高度（fill-extrusion）都用 `_grid_h` → **正相关**（金黄高热高柱 / 暗红低热低柱）
- 3D fill-extrusion：透明度可调（默认不透明）、3D 去线框；grid-warm 纯红→金黄 sequential（去紫红/玫红）；2D 不透明
- square 调后端 `/spatial/grid`；zonal 调 `/spatial/aggregate`
- KDE「总体情况」去掉「情绪网格」preset；pp-tab 顺序对齐 Toolbox（网格移 buffer 左）
- **start.bat 一键启动**（serve.py 自起后端 uvicorn + /api 反代 + Ctrl+C 同停；强制重起死 :8000，解决"Failed to fetch"真根因）；前端启动 health 自检

## 当前状态
- 分支 `feature/kde-l2-3d`，HEAD `3006c4f`，**未 push**
- Grid 工具完整可用（square + zonal，2D/3D，L1 热度 / L2 极性 4 极）
- **deck.gl grid 方案已弃**（回 MapLibre fill-extrusion）：GridLayer/HexagonLayer extruded 在 MapLibre+MapboxOverlay 不渲染；ColumnLayer 效果不及 kepler 理想 → 用户决定回自创 fill-extrusion。addDeckGridLayer + 4 辅助已移除（弃用注释）。addHotpointLayer（热点图 deck.gl）保留搁置
- 后端 `create_square_grid` 加了 `l1_confidence_mean` + `emotion_intensity_mean` 聚合（L1 热度用）
- start.bat / serve.py 一键启动正常（curl health 通）

## 下一步：P1 核密度重组
- 拆 KDE 综合/极性地形（去 L1/L2 命名撞车）、移走情绪网格（已去 preset）、加 H3 六边形（2D/3D，橙黄-暗红）
- `/spatial/grid(hex)` 后端已就绪；**H3 归 KDE 工具**（与 P2 方格分家）
- **需 `pip install h3`**（当前 env 缺，pytest 2 hex 测试 fail）

## 新会话 prompt（复制即用）
```
续 feature/kde-l2-3d。P2 空间聚合 Grid 工具已完成（commit 3006c4f：square/zonal 2D/3D + L1 热度=密度×置信度 + 颜色高度正相关 + grid-warm 纯红 + 3D 透明度可调 + start.bat 一键）。

下一步 P1 核密度重组：拆 KDE 综合/极性地形（去 L1/L2 命名撞车）、移走情绪网格、加 H3 六边形（2D/3D 橙黄-暗红，归 KDE 工具）。先读 memories/repo/session-handoff.md + docs/revision-log.md 5.14 + memory（deck-gl-gridlayer-extruded-broken / stand-on-giants-shoulders / select-cascade-progressive / ramp-discrete-segments / verify-real-endpoint）+ plan ~/.claude/plans/feature-kde-l2-3d-p0-create-square-grid-fuzzy-rossum.md。需 pip install h3。
```

## 承重注意事项（踩坑，勿重复）
1. **deck.gl GridLayer/HexagonLayer extruded 在 MapLibre+deck.gl@9.1.0+MapboxOverlay 不渲染**（canvas 在/层构造/数据进层但完全空）；ColumnLayer 渲染但不及 kepler → 3D 网格用 **MapLibre fill-extrusion**（addPolygonPaint grid 分支）。详见 memory deck-gl-gridlayer-extruded-broken
2. **serve.py 必须 start.bat / `py frontend/serve.py 8080` 一键**（自起后端）；手动 `uvicorn` PATH 失败；旧后端进程占 :8000 被 `_spawn_backend` 误判复用（缺新路由→404→Failed to fetch）→ 已改强制 `_free_port(8000)` 重起
3. **验证测实际端点**（POST /spatial/grid + 数据），不只 health（旧后端 health 也通但路由缺）；详见 memory verify-real-endpoint
4. **数据选择联动递进**（选 level 后点层只显该层）；**色带离散分段**（.hm-style-seg，禁 linear-gradient）；**.hm-section[hidden] 需 CSS**（display:flex 覆盖 [hidden]，已加 .hm-section[hidden]{display:none}）
5. **L1 CSV 无 score**（score 在 L2）；L1 热度用 `l1_confidence`（后端已加 l1_confidence_mean 聚合）；L1 颜色/高度用 `_grid_h`（point_count×l1_confidence_mean 分位），L2 颜色用 `_grid_norm`(polarity)/高度 `_grid_h`
6. `polarity_index` 真实值域 -2~+2（后端 docstring 写 -1~1 有误），归一化 (x+2)/4
7. 生成新分析图 = **独占显示**（关其他可见层）+ 新建图层（同数据调参也新建，便于对比）

## 回顾（P2 演进）
初版（cellSize+polarity 简化）→ 完整版（分析类型导航+L1/L2 联动+极性移②）→ 修正1（联动递进）→ 修正2（离散分段+后端死进程）→ 修正3（Failed to fetch 真根因=旧后端复用）→ 弃 deck.gl 回 fill-extrusion（kepler 效果不达）→ L1 热度密度×置信度（颜色高度正相关）+ grid-warm 纯红 + 透明度可调 + 2D 不透明。
