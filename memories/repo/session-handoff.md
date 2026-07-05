# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月06日 00:46 | 分支 `main` | HEAD=`46250a6`（**已 push**）

---

## 当前节点：单元深读重新设计定向（典型格大头针方案已试做→回退，待实现 Q2）

### 本会话 Recap（07月06日 00:46，承 46250a6）
- **试做**「典型格大头针 + 关键词▲徽章 + `_typicalCell` 预设机制 + 关键词数量自适应（累计覆盖 80%）+ 深读诊断句」：新 `frontend/js/typical-cells.js` + panel.js/main.js/index.html/search-bar.css/panel.css 7 文件 + revision-log/todo。
- **用户否**："大头针表达差 / 关键词越改越少（top10 变少）"。
- **全回退**：`git checkout HEAD --` 7 文件 + `rm typical-cells.js`。HEAD 已含全部前会话已提交成果（TOPIC_MATRIX_MAP/双 sub-Tab/easeToCell/候选池 都验过在），**净代码改动 = 0**，工作树净。

### 单元深读重新设计定向（brainstorming 商定，待实现）

**Q1 内容+排版** → 4 板块·结论先行（数据全已有 `n_dom_*/n_elem_*/五级极性/place_name/topic_top/issue_label/attribution/suggestion`，前端纯渲染，零后端改）：
- ①**结论**（大字）：`issue_label` + 诊断句「【domain×element】极性聚集 pi=X（图层最差 Y%）· 市民关切 topic_top」。
- ②**证据**：本格 4×5 微分布（4 域条+5 要素条，高亮 top）+ 五级极性堆叠条 + topic_top 证词。
- ③**严重度**：分位条（`pct`）+ 同桶均值对比（`bucket`）。
- ④**行动·闭合**：`suggestion` + 4×5 行动落点标签；积极绿"保持"/消极红"整改"色码。

**Q2 引导点中典型格**（**替大头针**，大头针已否）：
- 图层总览加「推荐深读」清单：12 典型格 = 精选行（`issue_label`+`domain×element`+`pi`+`place`），点行 → flyTo + `cell:selected` 深读。带故事标题，比地图图钉强。
- cluster 内典型格(#1) 加粗描边+标号①，其余浅橙——cluster 从"一堆橙"变"①代表+其余相关"。

**Q3 闭合点** → 诊断→开方→下一步入口（先做 1 个）：
- 「看同类」跳同 `domain×element` 其他强消极格（点到面）；后续可加「对比演进」T1↔T3、「导出单元报告」、积极格「作样板」。

**数量修复**（并入 Q2）：`_keywordRank`（panel.js L789 `.slice(0,10)`）截断改 **floor 10 + 平坦扩 15**（旧"累计覆盖 80%"陡分布时 <10，回归）。

### 承重（全保，回退未触碰）
- `TOPIC_MATRIX_MAP`（panel.js 32 词语义表）+ `TOPIC_TABLE` 删 3 词（楚超火爆/卷桥河露营/江南绿肺 靠地标 proximity）+ 改 TOPIC_TABLE 必同步前端 `TOPIC_POLARITY`/`TOPIC_ORDER`/`TOPIC_MATRIX_MAP` 白名单（`_keywordRank` 丢弃未登记词）。
- 双层 sub-Tab（setOverview L159/setCellOverview L219/activateOvTab L184{silent}）；easeToCell `_cellModeZoom` 进入固定一次；highlightCellSet/toggleStickyHighlight（橙 #ff9000 opacity1.0 mh*2 拔高）；_attach_4x5_attrs 格属性单源；enforceMutualExclusion；**关键词点击仍走 `_topKeywordCells`+`fitBoundsTo`（bbox top10，5.20 原状，未改）**；hover top-10 cluster；KDE cascade-exclude；4×5 单源 poi_4x5_map.AMAP_L1_TO_4X5；关键词橙框 .ov-kw-track。
- **勿再做"地图大头针/marker 叠加"引导**——用户已否；引导走面板「推荐深读」清单 + cluster①分级。

## 当前状态
- 分支 `main`，**已 push**（origin/main 同步 = HEAD=46250a6；本会话 docs-only commit 后再推一次）。
- 工作树：本 handoff 卡 + revision-log 5.24 + todo 注记（待 commit）。
- 未 F5（本会话净 0 代码改动，无需验）。
- 5.23 的 12 词 cell ID 清单仍在 revision-log 5.23（坐标 = 地标锚点，Q2「推荐深读」清单复用）。

## 新会话 prompt（复制即用）
```
续 main（HEAD=46250a6，已 push）。读 memories/repo/session-handoff.md（单元深读重新设计定向快照）。

任务：实现「单元深读」重新设计——先做 Q2「推荐深读」清单 + cluster①分级（替已否的大头针方案）。
- Q2 清单：图层总览（square-grid L2 分析层）加「推荐深读」板块——12 典型格（revision-log 5.23 坐标）渲染为精选行（issue_label+domain×element+pi+place），点行 → 命中典型格 feature（按 _center 最近+先筛 topic_top===topic）→ flyTo + dispatch cell:selected 进深读。
- cluster①分级：hover/点关键词/矩阵块出橙 cluster 时，典型格(#1) 粗描边+标号①、其余浅橙（替"一堆橙分不清"）。
- 顺手修关键词数量：_keywordRank L789 .slice(0,10) 改 floor 10 + 平坦时扩到 15（旧"覆盖80%"陡分布时<10 回归）。
- 承 Q1（4 板块·结论先行）/ Q3（闭合「看同类」）后做。

承重：TOPIC_MATRIX_MAP/TOPIC_TABLE 删 3 词/双 sub-Tab/easeToCell _cellModeFixed/highlightCellSet mh*2/_attach_4x5_attrs/enforceMutualExclusion 全保；改 TOPIC_TABLE 必同步前端白名单+TOPIC_MATRIX_MAP。**勿再做地图大头针引导（已否）。**

先 F5 看单元深读 + 关键词现状，再落 Q2。
计费按调动次数，工作方式见 ~/.claude/CLAUDE.md（不派 subagent、批量并行、给推荐不穷举、常规前端改交付肉眼验）。时间戳写"MM月DD日 HH:MM"。
```

## 承重 memory 索引
- 本轮新增：`time-format-date-hm`（**新规：todo/handoff/revision-log 时间戳写"MM月DD日 HH:MM"**）
- 本轮相关：`topic-table-frontend-sync`、`grid-4x5-attribution`、`generate-grid-exclusive-vs-viewmode`、`kde-loadbearing-logic`、`no-handoff-on-routine-commit`、`todo-revision-log-sync`、`chinese-all-deliverables`、`push-not-redline`、`no-routine-playwright-verify`
- 前会话承重：`extrusion-height-maxheight`、`maplibre-query-array-stringify`、`terrain-mesh-rendering`、`capsule-button-design-language`、`tool-layer-convention`、`view-data-conclusion-sync`、`frontend-default-light-theme`、`martin-ui-redesign`、`three-page-architecture`
