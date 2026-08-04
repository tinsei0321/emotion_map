# CB-16 发版 backlog 收尾预检（glm组 · ZCode + GLM 5.2）

> **预检方**：glm组（ZCode + GLM 5.2）  
> **日期**：2026-08-04 | **对象**：③w5b 发版 backlog 5 项收尾草案  
> **方法**：harness.js composeGapCard footer/boundary derive 代码审查 + tools.js FIXED_ADMIN_DISTRICTS 白名单 + deriveAvailable 白名单逻辑 + preset geojson 9 features 实查 + eval 注释审查

---

## 预检结论：通过（3 项可行 + 1 项需用户确认 + 1 项验证项）

**5 项草案逻辑全部可行。footer 条件化 + eval 注释精确化无风险可直接做。FC boundary 白名单校验有误伤风险需细化。preset fixture 清理是数据改动需用户拍板。RST-L06 复跑是验证项非实施项。**

---

## 逐项预检

### 1. footer「未生成图层」措辞条件化 — **OK（与 request_upload 不冲突）**

| 核验点 | 判定 | 理由 |
|--------|:---:|------|
| failedObs=0 → 改"未完成分析" | ✅ | footer `:240` 恒含"图层"·零工具分支的 head 已改（③w4）但 footer 仍漏 |
| 与 request_upload 分支冲突？ | ✅ 不冲突 | request_upload 走 `:222` 分支（先于 `:226` failedObs=0 分支）→ footer 条件化只影响 failedObs=0 的两子情况·不影响 request_upload |
| 承重？ | ✅ | 只改 composeGapCard 内文·不动出口结构 |

**glm组 建议**：footer 条件化方式：
```javascript
// 当前（:240 恒含"图层"）
'> 在没有可靠数据或未生成图层前，我不会凭空编造结论。'

// 建议（条件化）
const _footerLayer = (failedObs && failedObs.length > 0) ? '或未生成图层' : '';
'> 在没有可靠数据' + _footerLayer + '前，我不会凭空编造结论。'
```

### 2. FC boundary 白名单校验 — **⚠️ 有误伤风险·需细化**

| 核验点 | 判定 | 理由 |
|--------|:---:|------|
| FC 直供 boundary 绕过 deriveAvailable 白名单 | ✅ 确认 | FC 返回 `params.boundary` 时·`deriveMissingParams:1546` 的 `_needDerive` 检查 `_boundarySuspect`——FC 给的 GeoJSON FeatureCollection(1 feature) 不触发 `_boundarySuspect`（`f.length === 1` 返 false）→ 不 derive → 白名单不检查 |
| 拒绝 FC 直供法定功能区（小溪塔）→ 清 boundary → request_upload | ⚠️ **误伤风险** | FC 可能返回用户上传层的要素 boundary（source=upload·非 preset）——上传层不受白名单限制（`:619` 注释明示）。如果校验不区分 source·会误清用户上传的合法 boundary |

**glm组 判定**：方向正确但需细化——**只校验 source=preset + 层名含"行政区"的 boundary**（与 deriveAvailable 白名单逻辑一致·`:621`）。FC 给的 boundary 如果来自用户上传层·不应校验。

**建议实现**：
```javascript
// deriveMissingParams boundary 校验（仅 preset 行政区层）
if (p.boundary && typeof p.boundary === 'object' && p.boundary.features) {
  const _f0 = p.boundary.features[0];
  if (_f0) {
    const _pname = _f0.properties?.name || _f0.properties?.MC || '';
    // 仅当 FC boundary 来源疑似 preset 行政区时校验（非上传层）
    // 判据：FC 无 source 信息 → 保守不校验（防误伤上传层）
    // 如需校验：需 FC 返回 boundary_source 字段（当前无）→ 暂不校验 FC 直供
  }
}
```

**结论**：FC boundary 白名单校验**暂缓**（P2）——当前 FC 不带 boundary source 信息·无法区分 preset vs upload·校验会误伤。PRM-07 根因是 preset fixture 含法定功能区（项 3）·修 fixture 比加 FC 校验更直接。

### 3. preset fixture 清理 — **⚠️ 数据改动·需用户确认**

| 核验点 | 判定 |
|--------|:---:|
| 改数据文件算红线？ | **需用户确认**——`行政区.geojson` 是固化库 preset·改其内容 = 改数据。但这是**清理**（删非法行政区划的法定功能区要素）非**新增/修改**情绪数据 |
| 9→4 要素影响面 | 中——preset 只保留西陵/伍家岗/猇亭/点军（FIXED_ADMIN_DISTRICTS）。5 个法定功能区要素（龙泉/小溪塔/白洋/龙泉绿心/生物产业园）删除 |
| deriveAvailable 白名单已覆盖 | ✅ `:622-625` 已过滤 FIXED_ADMIN_DISTRICTS·即使 fixture 含法定功能区·deriveAvailable 也不返回它们 |
| PRM-07 根因 | FC 直供绕过 deriveAvailable 白名单（项 2 分析）——fixture 清理是治本（法定功能区不在 preset → FC 无法直供）|

**glm组 判定**：fixture 清理**是治本方案**（比 FC 校验更直接）·但需用户确认。建议：**用户确认前·PRM-07 保持已知 backlog**（不阻塞发版——B3 断言已知 fail·非回归）。

### 4. RST-L06 复跑验证 — **OK（验证项·非实施项）**

| 核验点 | 判定 |
|--------|:---:|
| 浏览器 e2e 单例 vs B3 子集？ | **B3 子集更充分**——单例只跑 1 次（Flash 概率性）·B3 子集跑 3-5 次可验证稳定性 |
| 充分方法 | 起 serve → `?test=1` → 单跑 RST-L06 × 3 次 → 如果 ≥2 次 PASS → 硬化生效 |

**glm组 判定**：这是**验证项**（确认硬化是否生效）·非实施项（硬化代码已做 `:1129-1142`）。可与其他项并行·结果不影响其他项的推进。

### 5. eval 注释精确化 + 发版前复采 — **OK**

| 核验点 | 判定 |
|--------|:---:|
| 注释"select_template 不返回 multi"不严谨 | ✅ 确认——复合问"…并排序"可能返回 multi（B_TRACK_PARADIGM 有 multi 触发）|
| 精确化 | ✅ 改为"select_template 对多数单工具问返单工具·复合问可能返 multi·eval 标尺对齐多数情况" |
| 发版前复采 | ✅ 合理——eval 单次采样有 Flash 方差·发版前复采记录日期/模型 |

---

## 综合优先级

| 优先级 | 项 | glm组 判定 | 理由 |
|:---:|------|:---:|------|
| **P1** | footer 条件化（项 1） | ✅ 做 | 低风险·直接改·消"图层"残留 |
| **P1** | eval 注释 + 复采（项 5） | ✅ 做 | 低风险·精确化注释 |
| **P2** | RST-L06 复跑（项 4） | ✅ 做 | 验证项·起 serve 后跑 |
| **P2** | preset fixture 清理（项 3） | ⚠️ **需用户确认** | 数据改动·需拍板 |
| **P3** | FC boundary 白名单（项 2） | ⚠️ **暂缓** | FC 无 source 信息·误伤风险·fixture 清理更直接 |

---

## 范围边界

5 项中：
- **必做**：footer 条件化（项 1）+ eval 注释（项 5）—— 低风险·纯文本/注释改
- **应做**：RST-L06 复跑（项 4）—— 验证硬化效果
- **需确认**：preset fixture 清理（项 3）—— 数据改动·用户拍板
- **暂缓**：FC boundary 白名单（项 2）—— 误伤风险·fixture 清理后不需要

**承重零触碰**：所有项只改 composeGapCard footer / eval 注释 / preset geojson（数据）/ 无 diagnose prompt / 三态出口 / ChatRequest 变更 ✅

---

## 一句话结论

**5 项 backlog 收尾草案可行——footer 条件化（项 1·消"图层"残留）+ eval 注释精确化（项 5·对齐架构现实）低风险直接做。FC boundary 白名单（项 2）暂缓——FC 无 boundary source 信息·无法区分 preset vs upload·误伤风险·fixture 清理更直接。preset fixture 清理（项 3）是治本但需用户确认数据改动。RST-L06 复跑（项 4）是验证项非实施项。优先级：P1 footer + eval → P2 RST-L06 复跑 → P2 fixture（需确认）→ P3 FC 白名单（暂缓）。**

---

*glm组（ZCode + GLM 5.2）· CB-16 backlog 收尾预检 · 2026-08-04*  
*验证基于：harness.js :226-240 composeGapCard + :1540-1556 boundary derive + tools.js :617-631 FIXED_ADMIN_DISTRICTS 白名单 + DATA/boundaries/presets/行政区.geojson 9 features 实查（MC=龙泉/小溪塔/白洋/龙泉绿心/生物产业园/西陵区/伍家岗区/猇亭区/点军区）+ eval :88-89 注释审查。*
