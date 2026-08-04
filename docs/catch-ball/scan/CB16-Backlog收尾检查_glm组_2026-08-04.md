# CB-16 发版 backlog 收尾实施后检查（glm组 · ZCode + GLM 5.2）

> **验证方**：glm组（ZCode + GLM 5.2）  
> **日期**：2026-08-04 | **对象**：23efe74（footer 条件化 + preset 清理 + RST-L06 MC + eval 注释）  
> **方法**：harness.js composeGapCard footer + chain pre-check MC 代码审查 + preset geojson 4 features 实查 + district-stats _TUAN_MAP 4 组团核查 + eval 注释 diff + pytest 277 passed + 全仓 admin_district 引用扫描

---

## 核验结论：通过

**4 项实施全部正确落地。footer 条件化（"图层"残留消除）+ preset 清理（9→4 真实区划）+ district-stats 同步（8→4 组团）+ RST-L06 MC 字段补全（死代码消除）+ eval 注释精确化 + tuple 双接受。pytest 277 passed 零回归。无破坏性依赖。**

---

## 逐项核验

### 项 1 footer 条件化 — **OK**

`harness.js:237-242`：

```javascript
const _footerLayer = (failedObs && failedObs.length > 0) ? '或未生成图层' : '';
// ...
'> 在没有可靠数据' + _footerLayer + '前，我不会凭空编造结论。'
```

| 核验点 | 结果 |
|--------|:---:|
| failedObs=0 → footer 无"图层" | ✅ `_footerLayer=''` → "在没有可靠数据前" |
| failedObs>0 → footer 有"图层" | ✅ `_footerLayer='或未生成图层'` → "在没有可靠数据或未生成图层前" |
| 与 request_upload 分支冲突？ | ✅ 不冲突——request_upload 走 `:222` 分支（先于 `:226`）·footer 是所有分支共用·条件化不影响分支优先级 |

**"图层"字眼彻底检查**：composeGapCard 在 failedObs=0 场景下·head（`:229-231`）和 footer（`:242`）都不含"图层" ✅

### 项 3 preset fixture 清理 + district-stats 同步 — **OK**

| 核验点 | 结果 | 证据 |
|--------|:---:|------|
| preset 9→4 features | ✅ | `行政区.geojson`：4 features（西陵区/伍家岗区/猇亭区/点军区）= FIXED_ADMIN_DISTRICTS |
| 备份 .bak9 | ✅ | `行政区.geojson.bak9` 存在（1.9MB·保 BOM） |
| _TUAN_MAP 8→4 组团 | ✅ | `district-stats.js:9-15`：西陵/伍家岗/猇亭/点军 4 组团 |
| 法定功能区清除 | ✅ | 龙泉/小溪塔/白洋/龙泉绿心/生物产业园 不在 preset |
| manifest nameField=MC 不变 | ✅ | `geo_registry.py:107-108` nameField 不改 |

**破坏性依赖检查**：

| 引用方 | 影响 | 判定 |
|--------|------|:---:|
| `deriveAvailable` 白名单 `:617-631` | 法定功能区不在 preset → 白名单自动不命中（双重保险）| ✅ 无破坏 |
| `CHAIN_REGISTRY extract_overlay` `stages.js:76` | `layer: 'admin_district'` → preset 仍存在·4 features | ✅ 无破坏 |
| `_boundaryEnum` `tools.js:551` | "行政区·含:西陵区/伍家岗区/…" → 4 features 仍含这些 | ✅ 无破坏 |
| district-stats `_TUAN_MAP` | 8→4 组团·L1 数据总览显示 4 组团 | ✅ 行为正确（法定功能区非真实区划） |
| geo_registry preset manifest | nameField=MC 不变·load_presolve 仍正确 | ✅ 无破坏 |

**结论**：无破坏性依赖——5 个被删要素（法定功能区）在所有代码路径中都被 FIXED_ADMIN_DISTRICTS 白名单过滤·删除只是消除数据源（不再出现在 preset）。

### 项 4 RST-L06 fallback MC 修复 — **OK**

`harness.js:1138-1141`：

```javascript
const _pf = _presetLayer.fc.features.find((f) => {
    // ③w6b（Codex P1）：行政区 preset 要素仅 MC 字段 → 补 MC
    const v = f.properties && (f.properties.name || f.properties.NAME || f.properties.name_field || f.properties.MC);
    return v != null && String(v).includes(_pname);
});
```

| 核验点 | 结果 |
|--------|:---:|
| 补 MC 字段查询 | ✅ `f.properties.MC` 加入 OR 链 |
| 死代码消除 | ✅ 原 `name/NAME/name_field` 三字段在 preset 中恒缺（只有 MC）→ 加 MC 后可命中 |
| geo_registry nameField=MC 一致 | ✅ `load_presolve:170-172` 做 `polys['name'] = polys[nf]`（nf=MC）副本 → 实际 features 有 name 副本。但 harness fallback 不经 load_presolve（直接读 layer.fc.features）→ 只看原始 properties → MC 是唯一可用字段 |

**复跑验证**：待前台 serve 环境（claude组 标注 backlog）——不阻塞·代码逻辑正确。

### 项 5 eval 注释精确化 — **OK**

`eval_template_flash.py:88-89`：

```python
# ③w4b（glm 标尺纠错）：select_template 对多数单工具问返单工具·复合问（「…并排序」）可能返 multi...
# ③w5b（glm 补充）："西陵区的商业用地" clip/overlay 双合理（面∩面解读）·tuple 双接受治 Flash 概率性歧义 MISS
('西陵区的商业用地', ('clip', 'overlay')),   # clip 或 overlay 皆合理
('西陵区范围内密度分析', 'density'),
```

| 核验点 | 结果 |
|--------|:---:|
| 注释精确化（"不返回 multi"→"对多数返单工具·复合问可能返 multi"）| ✅ |
| tuple 双接受（clip/overlay 皆合理）| ✅ 采纳 glm组 补充建议 |
| 标尺对齐架构（select_template 是单工具选择器）| ✅ |

---

## 承重 + 回归

| 核验点 | 结果 |
|--------|:---:|
| diagnose prompt 不动 | ✅ |
| 三态出口结构不动（exit:'gap' 不变） | ✅ |
| ChatRequest 不动 | ✅ |
| pytest 277 passed | ✅ 零回归 |

---

## 验证清单

| # | 验证项 | 方法 | 结果 |
|:---:|------|------|:---:|
| 1 | footer 条件化（"图层"消除） | 代码审查 | ✅ |
| 2 | footer 与 request_upload 不冲突 | 分支优先级分析 | ✅ |
| 3 | preset 9→4 features | geojson 实查 | ✅ |
| 4 | 备份 .bak9 存在 | 文件检查 | ✅ |
| 5 | _TUAN_MAP 8→4 | district-stats.js 审查 | ✅ |
| 6 | 破坏性依赖（全仓 admin_district 引用扫描） | grep + 逻辑分析 | ✅ 无破坏 |
| 7 | RST-L06 MC 字段补全 | 代码审查 | ✅ 死代码消除 |
| 8 | eval 注释精确化 + tuple 双接受 | diff 审查 | ✅ |
| 9 | pytest 277 passed | 全量运行 | ✅ |
| 10 | 承重零触碰 | diff 范围 | ✅ |

---

## P2 建议（非阻塞）

**fixture 清理断言**：建议加一个 pytest 断言验证 preset 行政区 features ⊆ FIXED_ADMIN_DISTRICTS——防未来数据更新时法定功能区重新混入。但非阻塞（当前白名单 `:617-631` 已是双重保险）。

---

## 一句话结论

**4 项 backlog 收尾全部正确落地——footer 条件化（"图层"彻底消除·零工具场景无残留）+ preset 清理（9→4 真实区划·备份 .bak9·无破坏性依赖）+ district-stats 同步（8→4 组团）+ RST-L06 MC 补全（死代码消除·Codex P1 采纳）+ eval 注释精确化 + tuple 双接受（glm 补充采纳）。pytest 277 passed 零回归。承重零触碰。PRM-07 根治（法定功能区不在 preset → FC 无法直供）。RST-L06 复跑待前台 serve·不阻塞。**

---

*glm组（ZCode + GLM 5.2）· CB-16 backlog 收尾检查 · 2026-08-04*  
*验证基于：harness.js :237-242 footer + :1138-1141 MC 补全代码审查 + DATA/boundaries/presets/行政区.geojson 4 features 实查 + district-stats.js :9-15 _TUAN_MAP 4 组团 + eval :88-89 注释 diff + 全仓 admin_district/FIXED_ADMIN_DISTRICTS 引用扫描 + pytest 277 passed。*
