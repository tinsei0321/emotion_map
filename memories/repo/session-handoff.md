# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。

## 🔄 换机协议（常驻）

**离开前**：① `git status` 清空（全 commit）② `git push`（`git log origin/main..HEAD` 应空）③ 更 `docs/revision-log.md` + 本卡 ④ `.claude/` 改动也 commit。
**到机后**：① `git pull` + 确认同步 ② 读本卡「当前节点」③ 天地图 4 底图 JSON 被 gitignore（新机从已有机器拷，key 亦在 `core/config.py`）④ `git status` 确认。

## 当前节点 — 2026-06-25（办公机 · Search v2.2 完成，转入 P2+ 优化）

### 机器 & 同步
- **机器 = 办公机**（`C:\Users\admin\`）。
- **分支 = main only**（已合并全部分支并清理，solo 开发不再用 feature branch）。
- origin/main 缺 `91fa355`（docs）——网络恢复后 `git push` 即可。
- `py frontend/serve.py 8080` → `http://localhost:8080/frontend/index.html`

### 已完成（全汇总）

**Phase 2 地点搜索（全栈）**
- 后端 `core/geocode.py` MOD_GEOCODE：本地 1270 amap POI rapidfuzz + 高德兜底，`_amap_request` 双向 GCJ-02↔WGS84。3 GET 路由。
- 前端 6 态搜索栏 + 反查 chip + Point 卡 + L0 popup 增强。

**Search v2（交互增强）**拼音模糊+高亮，红大头针+tooltip+Point 卡交互。L0 badge "L0"。

**Search v2.1（数据质量）**排名分层（修金缔华城 bug），落水过滤 28 POI，P0 拼音前缀 boost +15，P1 去前导 ASCII 拼音。

**Zone v2.2**：amap 重建 12 zone（7 商圈 center+radius 200m + 4 非商业 + general）。商圈半径 500→200m。删泛词。geojson 改用 classify_point。情绪叙事级联 12 zone。seed 退命名。

### 下一步（P2+ 搜索优化）
| 优先级 | 优化项 |
|-------|--------|
| P2 | geocode 离线退化 |
| P3 | 下拉结果丰富化 |
| P4 | 数据缺口（华翔CAZ/江南URD） |
| P5 | UX loading 态+无结果引导 |

### 怎么跑
```
py frontend/serve.py 8080          # 前端 + 反代 + 自动起 uvicorn
py -m pytest tests/ -q             # 提交前（geocode 25 全过）
```

### ⚠ 注意
- 网络恢复后 `git push` 推 `91fa355`。
- AMAP_KEY 仅服务端 `.env`，高德 GCJ-02→WGS84 红线守住。
- L1→L2 analysis 搁置。
- 每完成一件事必更 `todo.md` + `docs/revision-log.md`。只说"交接"时才更本卡。
