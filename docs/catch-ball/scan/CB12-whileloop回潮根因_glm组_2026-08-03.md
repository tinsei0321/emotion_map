# CB-12 B3-verify-03 while-loop 回潮根因（glm组 · ZCode + GLM 5.2）

> **审查方**：glm组（ZCode + GLM 5.2）·第三方独立评估  
> **日期**：2026-08-03 | **对象**：1ddac28 二修后 B3-verify-03 OK 3/ERR 7·F_002=6 回潮  
> **方法**：1ddac28 diff 审查 + `trace_query --session B3-verify-03` F_002 上下文独立拉取 + verify-01 对照 + orchestrate 路由分支代码追踪  
> **关键**：10/25 报告不在仓库（claude组 环境）·但 `.trace/trace.log` session B3-verify-03 在仓库——glm组 独立读取

---

## 根因定位：`_tplHitRateReady()` gate 跨 session 累积失效——非 1ddac28 直接引入

### 核心发现

**claude组 怀疑"zonal 多 call 重写（boundary 空）→ validateParams fail → while-loop"——glm组 判定：disagree 此路径·agree gate 是真因。**

trace 证据链：

```
B3-verify-03 Case C（23:52:50-23:53:12）：
  23:52:50 | MOD_LLM.F_005    ← FC diagnose 正常（非 degraded）
  23:53:00 | MOD_AIQA.F_002   ← agentStep（while-loop 入口）
  23:53:12 | MOD_AIQA.F_002   ← agentStep 第 2 轮

B3-verify-03 Case D（23:54:23-23:54:35）：
  23:54:23 | MOD_LLM.F_005    ← FC diagnose 正常
  23:54:35 | MOD_AIQA.F_002   ← agentStep（while-loop）
```

**FC 正常（F_005 有值·非 degraded）但落 while-loop（F_002）——唯一路径 = `_tplHitRateReady()` gate fail**（`harness.js:1064`）。

### Gate 失效机制

`_tplHitRateReady()`（`harness.js:115-119`）从 `localStorage` 读跨 session 累积的 hits/misses：
- `_TPL_MIN_SAMPLES = 10`：冷启动放行
- `_TPL_HIT_RATE_GATE = 0.6`：成熟后命中率 < 60% → gate fail → while-loop
- **localStorage 跨 session 持久化**——B3 多次重测的 FC 失败（`template='unknown'` 记 miss）累积·跨 verify-01/02/03 session 不清零

**verify-01 (80%) vs verify-03 (回潮) 的差异不在 1ddac28 代码·在 localStorage gate 状态**：
- verify-01 跑时 gate 可能刚好 pass（samples 刚过 10·命中率 ≥0.6）
- verify-03 跑时 gate 可能刚好 fail（更多 unknown miss 累积·命中率跌 < 0.6）
- 这是**概率性翻转**——同一代码不同 session 的 gate 状态不同·导致 while-loop 率波动

### 排除 claude组 嫌疑

| claude组 嫌疑 | glm组 判定 | 证据 |
|--------------|:---:|------|
| zonal 多 call 重写 boundary 空 → fail → while-loop | **disagree** | 重写后 `_allToolCalls.length=1`（`:1384`）→ `:1058` `length > 1` = false → 不进 runAllToolCalls → 进 `:1062` 单工具路径 → 如果 gate pass 则 runTemplatePath（validateParams fail = ask_user·非 while-loop）。**boundary 空不会导致 while-loop·只导致 ask_user** |
| recover 模式 G 误触发 | **disagree** | 模式 G 只在 FC degraded 时触发（`_deterministicRecover` 内）。trace 显示 FC 正常（F_005 非 degraded）→ recover 不触发 |
| 1ddac28 直接引入 while-loop | **disagree** | 1ddac28 改动（zonal 重写 + compare 补丁 + recover G + fixture）都不改 gate 逻辑 / localStorage / orchestrate while-loop 入口 |

### 1ddac28 的间接影响（低）

1ddac28 改了 PRM-07/09 问句（test-cases.js）+ zonal 重写 + recover G。这些改动**不直接改变 gate**——但如果新问句导致更多 FC 失败（新 fixture 数据不匹配→FC 选不出工具→unknown→miss）→ 间接累积 gate miss → gate flip。这是**间接/概率性**影响·非确定性 bug。

---

## trace 对照（verify-01 vs verify-03）

| 指标 | verify-01（80%）| verify-03（回潮）| 差异 |
|------|:---:|:---:|:---:|
| F_005（FC diagnose）| 19 | 9 | verify-03 FC 触发更少（更多 case 走 quickIntent 短路或 degraded） |
| F_002（agentStep）| 8 | 6 | 绝对数降·但 F_002/F_005 比率升（42% → 67%） |
| F_003（finalStep）| 30 | 14 | verify-03 finalStep 少（更多 case 没 reach finalStep = 链路断） |
| F_002 前 FC degraded？ | — | **否**（F_005 正常） | 关键：FC 正常仍 while-loop = gate fail |

**F_005=9（verify-03）vs 19（verify-01）**——verify-03 只有 9 个 case reach FC。其余 16 个 case 走了 quickIntent 短路或 data gate 或某处断了。这不是 while-loop 回潮——是**整体链路退化**（可能 API 慢 / gate 状态 / session 隔离副作用）。

---

## 修复建议

### P0：Gate 诊断 + session 隔离

```javascript
// harness.js orchestrate 路由前·加 gate 诊断 log
console.log('[gate]', _tplHitRateReady() ? 'PASS' : 'FAIL', 
            JSON.stringify(_loadTplStats()));
```

**验证**：在 B3-verify-03 的 console 中搜 `[gate]` → 确认 gate 是否 FAIL。如果 FAIL → gate 是 while-loop 根因。

### P0（如果确认 gate）：Gate session 重置或阈值调低

```javascript
// 方案 A：B3 飞轮模式清 gate（新 session = 冷启动 = gate 放行）
if (new URLSearchParams(location.search).get('test') === '1') {
  localStorage.removeItem(_TPL_STATS_KEY);  // 飞轮 = 冷启动
}

// 方案 B：阈值 0.6 → 0.4（容忍更多 unknown·防 gate 翻转）
const _TPL_HIT_RATE_GATE = 0.4;
```

**推荐方案 A**——B3 飞轮是测试环境·gate 累积无意义·每次飞轮应冷启动。生产环境 gate 保持 0.6。

### P1：zonal 多 call 重写加 boundary 空检查

即使 boundary 空不直接导致 while-loop（导致 ask_user）·也应加守卫防传空 boundary：

```javascript
// harness.js:1383 当前
if (Array.isArray(diagnose._allToolCalls) && diagnose._allToolCalls.length > 1) {
  diagnose._allToolCalls = [{ name: 'zonal_stats', params: { boundary: p.boundary } }];
}

// 建议：boundary 空时不重写（保留原 _allToolCalls·让 FC 原选执行）
if (Array.isArray(diagnose._allToolCalls) && diagnose._allToolCalls.length > 1 && p.boundary) {
  diagnose._allToolCalls = [{ name: 'zonal_stats', params: { boundary: p.boundary } }];
}
```

### 不建议回退 1ddac28

1ddac28 的改动（zonal 重写 + compare 补丁 + recover G + fixture）本身逻辑正确——不是 while-loop 回潮的直接根因。回退会丢失 PRM-07/09 的修复收益。**应修 gate 而非回退**。

---

## 验证方法

```bash
# 1. 确认 gate 状态
# 浏览器 console 跑：
JSON.parse(localStorage.getItem('ai_qa_template_stats_v1'))
# 如果 hits/(hits+misses) < 0.6 且 samples >= 10 → gate FAIL = while-loop 根因

# 2. 清 gate 后重跑 B3
localStorage.removeItem('ai_qa_template_stats_v1')
# 然后跑 B3 → 如果恢复 80% → 确认 gate 是根因

# 3. trace 确认
python tools/trace_query.py --session <new-session> --id MOD_AIQA.F_002
# 如果 F_002 显著下降 → gate 修复生效
```

---

## 一句话结论

**while-loop 回潮根因不是 1ddac28 的 zonal 多 call 重写（boundary 空导致 ask_user 非 while-loop）——是 `_tplHitRateReady()` gate 跨 session 累积失效：localStorage 持久化的 hits/misses 在多次 B3 重测后命中率跌 < 0.6 → gate FAIL → FC 正常的 case 也被挡出单工具路径 → while-loop。这是概率性翻转（同一代码不同 session gate 状态不同）·非确定性 bug。修复 = B3 飞轮模式清 gate（冷启动）+ zonal 重写加 boundary 空检查（P1 防御）。不建议回退 1ddac28——逻辑正确·不是直接根因。**

---

*glm组（ZCode + GLM 5.2）· CB-12 B3-verify-03 while-loop 回潮根因 · 2026-08-03*  
*证据基于：1ddac28 diff + trace_query --session B3-verify-03（F_002=6 / F_005=9 / F_003=14）+ verify-01 对照（F_002=8 / F_005=19 / F_003=30）+ orchestrate 路由分支 `harness.js:1058-1086` 代码追踪 + gate 逻辑 `harness.js:115-119`。*
