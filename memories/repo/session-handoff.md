# 会话交接卡

> 换机后读取此文件恢复上下文。**单份当前快照，每日翻新**——每次换机/新会话**覆写「当前节点」**，旧的（已交接的）直接删；历史在 `docs/revision-log.md` + git，不在此累积。

## 🔄 换机协议（常驻）

**离开前 5 步**（防 todo.md 再漏更——06-17 教训）：
1. `git status` 清空——所有改动 commit（**含 `docs/todo.md`**）
2. `git push`——`git log origin/main..HEAD` 确认输出为空（无未推送）
3. **两个状态文件都更**：`docs/todo.md`（正式日志）+ 本文件（交接）；不能只更一个
4. `.claude/` 配置改动（agent/hook/skill/memory）也要 commit
5. 记下「到机第一步」

**到机后**：
1. `git pull` + `git log origin/main..HEAD` 确认同步（应为空）
2. 读本文件「当前节点」接上下文
3. **天地图 img 底图 JSON 被 gitignore**（含内嵌 key）——新机若 `apps/static/tianditu_img*.json` 缺失，从已有机器拷 4 张（img / img_nolabel / label / nolabel）；key 亦在 `core/config.py`
4. `git status` 确认工作区

> 文件职责：`docs/todo.md` = 正式日志（每日任务+踩坑，倒序）；本文件 = 跨机交接（单节点快照）。职责不同，换机前都更。

## 当前节点 — 2026-06-24（家用机 · 任务一模拟器 v3.0→v3.1 pivot → 8 点换办公机）

### 机器 & 同步
- **机器 = 家用机**（`C:\Users\Hi\`；办公机 = `C:\Users\admin\`）。auto-memory 9 条本机生效。
- Git：**GitHub 此刻可达（200）**；c68f3de（export 修复）已 push（origin/main..HEAD 空）。本轮任务一工作（Phase A + v3.0 + 边界 + 本卡）**已 commit + push**，办公机 `git pull` 即同步。
- 天地图 4 底图 JSON 全在。

### 本轮产出（任务一 模拟器，家用机）
- **边界到位**：`DATA/boundaries/西陵伍家核心主城.geojson`（139.6km²，4229 顶点）+ `大南门二马路滨江片区.geojson`（0.599km²，42 顶点），均 WGS84 valid 嵌套。用户提供。
- **Phase A（保留，v3.1 复用）✅**：[emotion_text_pool.py](../../SCRIPT/emotion_text_pool.py)（78 条 SnowNLP 预筛文本，**L2 锚定 100%**）；[snapshot_config.py](../../SCRIPT/snapshot_config.py)（3 快照叙事，二马路 T1 消极 60%→T3 积极 65%）；[poi_data/](../../SCRIPT/poi_data/)（158 POI 种子 WGS84 + 4×5 映射 75 条）。
- **v3.0 [generate_l1_mock.py](../../SCRIPT/generate_l1_mock.py) ✅ 跑通但点位不可用**：3 快照 × 2500 点 + 二马路加密 + 埋点 + L1→L2（score 0.46→0.57→0.65 叙事弧 + 埋点迁移表）。**但空间生成是"158 POI 种子高斯聚类"→ 离散光斑 + 伍家空白**（数据证实：75% 网格空、伍家 0 点、最大光斑 388 点/格）→ **用户判"完全不可用"**。
- **环境补**：snownlp/jieba/tqdm 原缺（在 requirements 但没装），已 pip install。

### 下轮（8 点办公机）— v3.1 重做空间生成
**plan 文件在本机 `C:\Users\Hi\.claude\plans\...`（不跨机），方案要点写此卡**：
- **换空间生成**：**高德真实 POI**（全类目 ~13 类，`restapi.amap.com/v3/place/text`，GCJ-02→WGS84，boundary 过滤，缓存）→ **numpy 核密度曲面**（histogram2d + 高斯卷积平滑，**不引 scipy**，3.14 稳）→ **全域按密度拒绝采样**（密的区域多采、boundary.contains() 掩膜）。替 v3.0 的 POI 种子聚类。
- **复用**：Phase A（文本池/叙事/4×5）+ v3.0 非空间部分（inject_fields 的 domain/element/polarity、apply_anchors 埋点、transform_coords、fill_keywords、export_l1 GeoJSON、run_l2、main 3 快照循环）。**只改 generate_zone_points**（→ DensityField 拒绝采样）。
- **新文件**：`SCRIPT/poi_data/pull_amap_poi.py`（高德拉取，读 `AMAP_KEY`）、`SCRIPT/poi_data/poi_density.py`（核密度 + 拒绝采样）。
- **AMAP_KEY 待补 `.env`**（高德 Web 服务 Key，lbs.amap.com 个人免费；**用户暂无**）。无 Key 时 pull 脚本报错退出（不静默跳过）。
- **二马路**：密度曲面在 +150m buffer 内乘 boost 因子凑 ~700 点（平滑加密，非团）。
- **验证指标**（"不可用"的反面）：伍家 POI >15%（v3.0 是 0%）、网格填充 >60%（v3.0 是 25%）、无 >50 点/格光斑、叙事弧/L2 锚定/埋点不变。

**办公机第一步**：`git pull` → 读本卡 → 实现 v3.1（plan 已与用户对齐过：高德 POI + KDE + 拒绝采样；AMAP_KEY 后补；全类目；不引 scipy）→ 写 pull + density → 改 generate_zone_points → 跑 + 肉眼验。

### 怎么跑
```
py frontend/serve.py 8080   # F5 迭代；后端无 --reload，改路由要重启 serve
py SCRIPT/generate_l1_mock.py   # v3.1 改完再跑（需 AMAP_KEY + 已拉 POI 缓存）
```

### ⚠ 换机注意
- v3.0 输出（`DATA/processed/xiling_wujia_L*`）+ `docs/minimax-workspace/` 参考包 **未 commit**（家用机本地）；办公机没有。输出 v3.1 会重新生成；参考包用户可重投（Phase A 已吸收其精华，非必需）。
- `DATA/boundaries/规划范围/` 旧 shp 在家用机工作区标删除，**未 commit**（避红线"删文件先问"）；办公机仍有（无害，v2.2 遗留）。

## 工作机制速查（memory 在线时的快查；若 memory 丢失看此恢复）

- **session-handoff**：满载 / 任务自然边界 / 用户提 token / 主题大切换 → 主动给 **4 件套**（①提示+理由 ②新会话衔接说明 ③衔接操作 ④commit 小结+状态）。
- **token-saving**：①分会话（最有效）②subagent 分流（探索/规划/大读）③少全读（grep+offset/limit）。**不降 effort**。
- **maintain-revision-log**：每次 commit → revision-log §5 追加一行（日期|commit|意图|文件）；任务树（顶部 ★）全程维护（新分支即追加 + 状态 ✅🔄⬜⏸❌）。
- **kde-loadbearing**（底层逻辑勿破坏）：①联动排除（无字段层级自动排除）②独占显示（新热力图隐其他层 + dispatch `layers:changed`）。
- **tool-layer-convention**：工具生成层 = 独立组卡（`categoryOf` 加该工具 category）+ 要素按钮（H/B/…）开本工具弹窗（编辑态 `paint._ui` 回填 + 原地更新，layer id 稳定）。
- **中文交付**（plan/报告/docs 中文；代码/路径/标识符英文）+ **术语纠正**（非专业表述→专业术语）。
- **auto-compact**：`CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000`（晚压缩）。
- **交接卡新约定（2026-06-23）**：单节点翻新，不累积历史；旧节点删（已进 revision-log + git）。
