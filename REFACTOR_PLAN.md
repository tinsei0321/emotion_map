# Refactor Plan: 地点搜索 + 情绪点重平衡 + 评论文本地域化

Created: 2026-06-24
Last updated: 2026-06-24
Base commit: 6ae4d1b54887515b7f03c3beebbda8a436487a0a
Branch: feat/location-search-emotion-rebalance

## Overview
三件事共用一个 place 层脊柱：(A) 修二马路失控的空间重平衡，(B) 全图 ~60% 本地性的评论文本绑定，(C) 地点搜索 + 逆地理编码。详见批准计划。

## 锁定决策
- 数据源：本地 1270 POI 即时 + 高德 API 补全（混合）
- 搜索栏：展开 200px（=popup 宽）/ 折叠 32px 圆
- corpus：DeepSeek 生成 ~1.5-2.5k 地域化文本 + 人工审，全图 60% 本地性（已论证合理）

## Phase 0: 共享 place 层（脊柱）
- Status: done
- Files: core/place_layer.py, DATA/place/zone_typology.json, DATA/place/place_keywords.json, AGENTS.md
- Acceptance: 158 种子 100% 命中（无失败）；classify_point 一致；不改调用方 ✓
- Result: place_layer 单例跑通。158 种子分布 wanda64/ermalu34/riverside26/transit21/residential9/general4。1270 高德 POI：general65%(825)/wanda15.7%(199)/transit8%(102)/riverside5%(65)/ermalu4.1%(52)/residential2.1%(27)。修一 bug：amap POI area="宜昌" 经 _area_suffix 误匹配 transit "宜昌站" subtag（83% 误归交通）→ _area_suffix 无 '-' 返回 '' 修复。general 65% 符合预期（城市主体），真实平衡由 Phase 1 check_spatial 断言。forward/reverse 烟雾测试通过。

## Phase 1: 情绪点重平衡 + 文本地域化（A+B）
- Status: pending (depends Phase 0)
- Files: SCRIPT/snapshot_config.py, SCRIPT/generate_l1_mock.py, SCRIPT/emotion_text_pool.py, SCRIPT/poi_data/emotion_corpus.json, SCRIPT/poi_data/check_spatial.py
- Acceptance: score arc 0.46→0.57→0.63 ±0.01；二马路 share ≤0.20 全快照；密度比 ≤25×；落水系<0.5%；重点区本地性 75-85%、全图≈60%
- GATING: 重生成全部 3 套 GeoJSON + 过 check_spatial 后才动 Phase 2
- Result: (pending)

## Phase 2: 地点搜索功能（C）
- Status: pending (depends Phase 1 gating)
- Files: core/geocode.py, api/schemas.py, api/routes.py, requirements.txt, design/tokens.json, frontend/js/search-bar.js, frontend/css/search-bar.css, frontend/js/api.js, frontend/index.html, frontend/js/main.js, frontend/js/popup.js
- Acceptance: 搜已知 POI→flyTo 无 GCJ-02 偏移；状态机 6 态；空白点击→地名 chip 不干扰点/range/popup
- Result: (pending)

## 执行约定
- 逐阶段 commit（feature 分支，禁推 main）；每阶段过验收才进下一阶段；`--continue` 跨会话续
- 完成后追加 docs/revision-log.md
