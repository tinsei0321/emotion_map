# DATA/exchange · EMC 对接层（轻量）

> **定位**：EMC repo 与 zcode 中转站之间的**轻量对接层**——只登记「引用 / 副本 / 派生」三类归属 + schema 契约指针 + 校验命令，**不建 raw/staging/preprocessed 五层**（zcode 中转站已预治理，见 `00_中转站规则.md`）。
> **中转站位置**：`{URENEWAL_ROOT}/1 宜昌市城市体检/EMC数据中转站/`（`{URENEWAL_ROOT}` 占位见 `docs/urban-renewal-plan/_PATHS.md`；本机 = `D:\OneDrive\2026\15_城市更新专项规划研究`）
> **上游契约**：`manifest.json`（v1.1.0·EPSG:4326）→ `交付说明.md` → `03_元数据/`（口径/字段/转换脚本）
> **创建**：2026-08-11 ｜ **维护**：claude组 ｜ **登记**：docs/context-map.md

---

## 一、三分法（引用 / 副本 / 派生）

| 类 | 定义 | 落点 | 现状 |
|---|---|---|---|
| **引用**（reference） | 空间大文件原始层：不进 git，经 `{URENEWAL_ROOT}` 占位 + 相对路径引用 | 无（只在 `manifest.json` 登记） | 10 层登记 |
| **副本**（copy） | 文本/小文件（合计 <200KB）：同步进 repo，RAG/消费可直接重建 | `docs/urban-renewal-plan/00-宜昌专项/` + `DATA/exchange/` | 03-08 摘要落位 + 5 CSV + 元数据 |
| **派生**（derived） | 分析所需空间派生层：脱敏后入库，可独立重建 | `DATA/performance/` + `DATA/boundaries/presets/` | 阶段 1 适配器导入生成 |

**判定依据**：空间大文件 ~60MB（建筑汇总 32MB / 2001-2005 15MB / 覆盖率面 ~5.4MB）全量进 git 膨胀 → 只引用；文本/小文件（5 CSV ~84KB + 03-08 摘要 32.9KB + 04 素材 ~65KB）< 200KB → 副本无压力。

## 二、引用清单 manifest

`manifest.json` = 机器可读引用清单（dataset 对齐中转站 v1.1.0·三类归属明细·校验状态）。文件/路径/要素数见该文件；改动须更新 version + changelog（守中转站规则五·版本管理）。

## 三、schema 契约指针

| 契约 | 位置 | 用途 |
|---|---|---|
| **schema 盘点表（本层）** | `DATA/exchange/schema_inventory.md` | 全部图层/CSV 字段映射（dbf 截断中文 ↔ 完整含义）+ 有效字段指引 |
| PII 例外清单（本层） | `DATA/exchange/PII_EXCEPTIONS.md` | 只引用不复制层 + 派生剥离字段 + 验收扫描 |
| 口径清单 | `{URENEWAL_ROOT}/…/03_元数据/口径不一致清单_18项.csv` | **引用数值前必读**（18 项·建议口径） |
| 字段说明 | `{URENEWAL_ROOT}/…/03_元数据/字段说明与坐标系说明.md` | 字段名含义映射 + 覆盖率面层有效字段指引 |
| 转换记录 | `{URENEWAL_ROOT}/…/02_空间数据集/_转换记录.csv` | 26 shp 转换明细（要素数/字段/CRS） |
| 04 互通优化 | `{URENEWAL_ROOT}/…/04_互通优化/` | RAG 素材（fact 卡/摘要/图表 JSON/图层元数据）·阶段 2 消费 |
| EMC 图层注册 | `core/geo_registry.py` + `DATA/boundaries/presets/manifest.json` | 点层/面层注册（阶段 1 执行） |

## 四、校验命令

```bash
# 1) 中转站 manifest 契约校验（版本/CRS/文件存在）
py -c "import json,os;m=json.load(open(r'{URENEWAL_ROOT}/1 宜昌市城市体检/EMC数据中转站/manifest.json',encoding='utf-8'));print('version',m['version'],'crs',m['crs'])"

# 2) PII 扫描：repo 内零残留（派生层不得出现 验收联系人/电话/照片URL 字段）
grep -rE "yslxr|yslxrdh|存在问1" DATA/performance/ DATA/boundaries/ docs/urban-renewal-plan/00-宜昌专项/ || echo "[OK] PII zero residue"

# 3) 口径对照：引用数值前核对 18 项建议口径
#    （学位 6603 非 7482 / 结构 42 非 43 / 楼道 240 源 242 / 菜市场 57.84% / 250栋≠54栋结构隐患）
```

## 五、口径纪律（Data Governance）

- 两板块名「安全韧性底线/民生基础需求」= **专项规划修编工作分类**（00-01:51），非住建部官方术语；报告标注板块来源（专项规划分类 × 建科〔2023〕75号指标域）。
- manifest 声称「口径清单 20 项」vs 实表 `18项.csv` 18 行 → **以实表 18 项为权威**，已报 zcode 对齐（见 `口径对齐` 记录）。
- 待核实未决项（34%/150万/89.45km）不进报告；C 级参考 md 仅线索。

## 六、修订记录

| 版本 | 日期 | 说明 |
|---|---|---|
| 0.1.0 | 2026-08-11 | 对接层建立：三分法 + 引用清单 manifest + schema 盘点 + PII 例外（阶段 0' 交付） |
