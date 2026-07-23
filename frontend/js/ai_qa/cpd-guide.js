// ═══ cpd-guide.js — CPD 引导引擎（客户端确定性编排器 · deriveGuidance）═══
// plan v1.0（cpd-core-plan.md §4.2）· CLAUDE.md「AI·Copilot 开发内核」铁律3：纯函数推导，不调 LLM、不推理。
//
// 从客户端**特征信号向量** (hasImport, hasRange, hasVisibleEmotionLayer, hasAnalysis, lastExit, streaming)
// 确定性算出「此刻唯一动作」{kind, text, ctaKind}，派发 cpd:guidance → panel.js 落地 DOM（光环/placeholder/CTA）。
//
// **承重边界**：
// - 零 import panel.js / harness.js（_history/_streaming 经依赖注入单向读取·CB-CPD-02 H1 消除循环 import）。
// - 只读（cpd-state 谓词 + DI getter），不写 harness/diagnose/四态出口/curState 推导逻辑。
// - 事件松耦合：cpd:turn-ended（panel.js finally dispatch）携带 {exit,turnId,intent} → 引擎去重算下一步。

import { hasImport, hasRange, hasAnalysis, hasVisibleEmotionLayer, subscribe } from './cpd-state.js';

// 色名铁律（CB-CPD-02 M1）：文案色名取 theme var 端点（very-positive 深青绿 / very-negative 深珊瑚橙，无"深红"）。
// 单一源常量——色带调整时文案只改此处（CSS-var→显示名绑定留 G2）。
const COLOR_POS = '深绿';
const COLOR_NEG = '深橙';

let _deps = null;          // { getLastExit, isStreaming, getLastRegion }（panel.js 依赖注入）
let _lastTurnId = -1;      // 单调去重：仅处理 turnId > _lastTurnId（H1 修复·免疫 general 跳号）
let _suppressedKind = null;   // engage 解除：用户已 engage 某 kind → 同 kind 不重亮，直至 kind 变化（plan §6.2.3）
let _inited = false;

/** 引导文案表（叙事化·服务演示链「张力→点击→分析→识别」）。
 *  @param {object} f  特征向量 { hasImport, hasRange, visEmotion, hasAnalysis, lastExit, region }
 *  @returns {{kind, text, ctaKind}|null} */
export function deriveGuidance(f) {
  if (!f) return null;
  // 优先级自上而下首匹（plan §4.2 规则 v1.0：streaming 第一 → hasImport 先导 → gap/partial/ask 让 _followUps → drift → 其余按表）
  if (f.streaming) return null;                                                    // 1 流式硬门（不打扰，第一优先）
  if (!f.hasImport) {                                                              // 2 先导数据
    return f.visEmotion
      ? { kind: 'import', text: '导入数据继续分析', ctaKind: 'import' }             //   纯 AI 层降级（CB-CPD-02 L3）
      : { kind: 'import', text: '生成第一张情绪地图——导入数据，我帮你定位最值得关注的区域', ctaKind: 'import' };
  }
  if (f.lastExit === 'gap' || f.lastExit === 'partial' || f.lastExit === 'ask') return null;   // 3 _followUps 已覆盖追问胶囊，不双 CTA
  if (f.lastExit === 'drift') return { kind: 'retry', text: '生成异常·已拦截——换个问法或缩小范围', ctaKind: 'input' };  // 4
  if (!f.hasRange) return { kind: 'range', text: '聚焦一片城区——上传范围文件，或在地图框选', ctaKind: 'range' };        // 5
  if (!f.visEmotion) {                                                             // 6
    return { kind: 'layers', text: `看张力——选情绪图层，${COLOR_POS}（情绪好）/ ${COLOR_NEG}（情绪差）告诉你哪里最值得关注`, ctaKind: 'layers' };
  }
  if (f.lastExit === null || f.lastExit === undefined || f.lastExit === 'general') {   // 7 默认 analyze / hasAnalysis 升级 interpret（M1·dock 产图桥回 EMC）
    return f.hasAnalysis
      ? { kind: 'interpret', text: '这张图已就绪——问我：这张图说明了什么？', ctaKind: 'analyze' }
      : { kind: 'analyze', text: `点击地图上${COLOR_POS}/${COLOR_NEG}的区域——我告诉你那里为什么`, ctaKind: 'analyze' };
  }
  if (f.lastExit === 'result') {                                                   // 8
    const r = f.region ? `${f.region}的` : '';
    return { kind: 'export', text: `${r}归因已就绪——深读 / 在地图定位 / 导出`, ctaKind: 'export' };
  }
  return null;                                                                     // 9 fallback
}

/** 组装特征向量 + 派发 cpd:guidance（engage 解除：同 kind 不重亮）。 */
function _compute() {
  if (!_deps) return;
  const raw = deriveGuidance({
    hasImport: hasImport(),
    hasRange: hasRange(),
    visEmotion: hasVisibleEmotionLayer(),
    hasAnalysis: hasAnalysis(),
    lastExit: _deps.getLastExit(),
    streaming: _deps.isStreaming(),
    region: _deps.getLastRegion ? _deps.getLastRegion() : '',
  });
  // engage 解除：用户已 engage 此 kind → 不重亮（null）；kind 变化 → 清除抑制、恢复正常引导。
  let guidance = raw;
  if (raw && _suppressedKind && raw.kind === _suppressedKind) guidance = null;
  else if (raw && raw.kind !== _suppressedKind) _suppressedKind = null;
  document.dispatchEvent(new CustomEvent('cpd:guidance', { detail: { guidance } }));
}

/** 依赖注入 init（panel.js 调，单向；cpd-guide.js 零 import panel.js·CB-CPD-02 H1）。
 *  @param {{getLastExit:()=>*, isStreaming:()=>boolean, getLastRegion?:()=>string}} deps
 *  - getLastExit()   读末条 trace.exit（panel.js `_history.at(-1)?.trace?.exit ?? null`）
 *  - isStreaming()   读流式态（panel.js `_streaming`）
 *  - getLastRegion() （可选）读末条答案 [ref:区域]/{{focus:}} 抽取的区域名（确定性变量·plan §4.3） */
export function initCpdGuide(deps) {
  _deps = deps || _deps;
  _lastTurnId = -1;            // 重置（切会话/clearChat 致 _history.length 回退断链·CB-CPD-02 L1）
  _suppressedKind = null;
  if (_inited) { _compute(); return; }   // 已接线（F5/切会话再调）：仅重算恢复，不重复绑监听
  _inited = true;
  // 自接线监听（只读，不写 harness）
  document.addEventListener('layers:changed', _compute);                       // 谓词变但 curState 可能不变（如聚合层生成）
  document.addEventListener('cpd:turn-ended', (e) => {                          // 单调去重（H1·免疫 general 跳号 + 快速连续 send）
    const id = e && e.detail && e.detail.turnId;
    if (typeof id === 'number' && id > _lastTurnId) { _lastTurnId = id; _compute(); }
  });
  subscribe(_compute);                                                          // curState 变 → 重算
  _compute();                                                                   // F5/init 主动恢复（读末条 trace.exit·plan §4.3）
}

/** 显式重算（reset 去重 + 重算）：供 panel.js clearChat/切会话/finally 触发恢复。 */
export function recomputeGuidance() {
  _lastTurnId = -1;
  _suppressedKind = null;
  _compute();
}

/** engage 解除（plan §6.2.3）：用户已点击 CTA / 聚焦输入 → 抑制当前 kind 重亮，直至状态变化。 */
export function suppressGuidance() {
  if (!_deps) return;
  const g = deriveGuidance({
    hasImport: hasImport(), hasRange: hasRange(), visEmotion: hasVisibleEmotionLayer(),
    hasAnalysis: hasAnalysis(), lastExit: _deps.getLastExit(), streaming: _deps.isStreaming(),
    region: _deps.getLastRegion ? _deps.getLastRegion() : '',
  });
  if (g) _suppressedKind = g.kind;
}
