// ═══ test-cases.js — 测试飞轮用例集（v1.7）═══
// 每例 = { id, name, category, type: 'no-llm'|'llm', run: async (t) => {pass, stage, obs, review?} }
// t = window.__emcTest（test helpers）。run 返回 {pass:bool, stage:string, obs:string, review?:string}。
// fail fast：run 内顺序断言，第一阶段 fail 立即 return（不等后续）。

// 内联 fixture（5 点·西陵+伍家岗·避免 serve.py /tests/ 路由）
const FX = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { polarity: 'Positive', score: 0.3 }, geometry: { type: 'Point', coordinates: [111.31, 30.72] } },
    { type: 'Feature', properties: { polarity: 'Negative', score: -0.2 }, geometry: { type: 'Point', coordinates: [111.32, 30.73] } },
    { type: 'Feature', properties: { polarity: 'Positive', score: 0.4 }, geometry: { type: 'Point', coordinates: [111.33, 30.71] } },
    { type: 'Feature', properties: { polarity: 'Negative', score: -0.3 }, geometry: { type: 'Point', coordinates: [111.36, 30.65] } },
    { type: 'Feature', properties: { polarity: 'Positive', score: 0.5 }, geometry: { type: 'Point', coordinates: [111.37, 30.64] } },
  ],
};

export const CASES = [
  // ── A. 真实 bug 回归（no-llm）──
  { id: 'T01', name: '空态欢迎卡（不引导 import）', category: 'CPD', type: 'no-llm',
    run: async (t) => {
      if (!t.collapsed()) return { pass: false, stage: 's0', obs: 'EMC 未折叠' };
      if (!t.welcome()) return { pass: false, stage: 's0', obs: '欢迎卡未显' };
      return { pass: true, obs: 'is-collapsed + welcome OK' };
    },
  },
  { id: 'T02', name: 'hint 消失 bug（suppress 后展开显示）', category: 'CPD', type: 'no-llm',
    run: async (t) => {
      t.clickHalo(); await new Promise(r => setTimeout(r, 200));
      document.dispatchEvent(new CustomEvent('layers:changed'));
      await new Promise(r => setTimeout(r, 200));
      const input = document.getElementById('chat-input'); if (input) input.focus();
      await new Promise(r => setTimeout(r, 400));
      if (!t.collapsed() && !t.hintVisible()) return { pass: false, stage: 's4', obs: '展开后 hint 不可见（suppress 误杀）' };
      return { pass: true, obs: '展开后 hint 显示正常' };
    },
  },
  { id: 'T03', name: '引导卡 vs 欢迎卡互斥', category: 'CPD', type: 'no-llm',
    run: async (t) => {
      document.dispatchEvent(new CustomEvent('cpd:guidance', { detail: { guidance: { kind: 'intent', text: 'test', ctaKind: 'analyze', directions: [{ tag: 'test', dir: 'test', hint: 'x' }], refinements: {} } } }));
      await new Promise(r => setTimeout(r, 200));
      const card = t.guidanceCard();
      const welcome = t.welcome();
      if (card && welcome) return { pass: false, stage: 's4', obs: '引导卡与欢迎卡同时显示（冲突）' };
      return { pass: true, obs: '引导卡显时欢迎卡隐（互斥 OK）' };
    },
  },
  { id: 'T04', name: 'Pro/Flash 图标渲染', category: 'UI', type: 'no-llm',
    run: async (t) => {
      const pro = document.querySelector('#aiq-mode button[data-mode="pro"] svg');
      const flash = document.querySelector('#aiq-mode button[data-mode="flash"] svg');
      if (!pro) return { pass: false, stage: 's4', obs: 'Pro 按钮无 SVG 图标' };
      if (!flash) return { pass: false, stage: 's4', obs: 'Flash 按钮无 SVG 图标' };
      return { pass: true, obs: 'Pro/Flash SVG 图标 OK' };
    },
  },
  { id: 'T05', name: 'CPD 方向级联（A→B→填 input）', category: 'CPD', type: 'no-llm',
    run: async (t) => {
      if (!t.collapsed()) { const i = document.getElementById('chat-input'); if (i) i.blur(); document.getElementById('chat-collapse')?.click(); await new Promise(r => setTimeout(r, 200)); }
      t.clickHalo(); await new Promise(r => setTimeout(r, 200));
      t.clickDirection('emotion'); await new Promise(r => setTimeout(r, 200));
      const opts = document.querySelectorAll('.cpd-guide-opt[data-prompt]');
      if (!opts.length) return { pass: false, stage: 's2', obs: '方向级联后无细化选项' };
      opts[0].click(); await new Promise(r => setTimeout(r, 100));
      if (!t.inputValue()) return { pass: false, stage: 's3', obs: '点击细化后 input 未填入' };
      return { pass: true, obs: `方向→细化→填 input OK（"${t.inputValue().slice(0, 30)}"）` };
    },
  },
  // ── B. 常规场景（LLM·需 DeepSeek）──
  { id: 'T06', name: 'zonal 不误判 GAP', category: 'EMC核心', type: 'llm',
    run: async (t) => {
      t.clearLog(); t.loadPoints(FX); await new Promise(r => setTimeout(r, 800));
      t.setMode('flash'); t.send('西陵区情绪归因'); const ok = await t.waitAnswer(90000);
      if (!ok) return { pass: false, stage: 's3', obs: '回答超时' };
      const b = t.badge();
      if (b && /缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's3', obs: `误判 GAP: badge="${b}"` };
      return { pass: true, obs: `badge="${b}"·不误判 GAP`, review: '结论是否合理？' };
    },
  },
  { id: 'T07', name: 'compare 产合并聚合图层', category: 'EMC核心', type: 'llm',
    run: async (t) => {
      t.clearLog(); t.loadPoints(FX); await new Promise(r => setTimeout(r, 800));
      t.setMode('flash'); t.send('对比西陵区和伍家岗区的情绪与归因'); const ok = await t.waitAnswer(90000);
      if (!ok) return { pass: false, stage: 's3', obs: '回答超时' };
      const b = t.badge();
      if (b && /缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's3', obs: `误判 GAP: badge="${b}"` };
      const names = t.layerNames();
      if (!names.some(n => n.includes('对比'))) return { pass: false, stage: 's3', obs: `无对比图层（layers: ${names.join(',')}）` };
      return { pass: true, obs: `badge="${b}" + 对比图层 OK`, review: '对比结论是否合理？' };
    },
  },
  { id: 'T08', name: '网格→3d（非热力图）', category: '工具选择', type: 'llm',
    run: async (t) => {
      t.clearLog(); t.loadPoints(FX); await new Promise(r => setTimeout(r, 800));
      t.setMode('flash'); t.send('做1000m标准网格分析'); const ok = await t.waitAnswer(90000);
      if (!ok) return { pass: false, stage: 's3', obs: '回答超时' };
      const b = t.badge();
      if (b && /缺数据|未产出|需上传/.test(b)) return { pass: false, stage: 's3', obs: `GAP: badge="${b}"` };
      return { pass: true, obs: `badge="${b}"`, review: '是否生成了方格网格（非彩虹热力图）？' };
    },
  },
  { id: 'T09', name: '通用问答（general 短路）', category: '意图识别', type: 'llm',
    run: async (t) => {
      t.clearLog(); t.send('什么是4×5矩阵'); const ok = await t.waitAnswer(60000);
      if (!ok) return { pass: false, stage: 's3', obs: '回答超时' };
      const b = t.badge();
      if (b && /缺数据|未产出/.test(b)) return { pass: false, stage: 's3', obs: `通用问答误判 GAP: badge="${b}"` };
      return { pass: true, obs: `badge="${b}"`, review: '回答是否简洁合理（无硬塞领域框架）？' };
    },
  },
  { id: 'T10', name: '缺参 ask_user', category: 'Smart', type: 'llm',
    run: async (t) => {
      t.clearLog(); t.loadPoints(FX); await new Promise(r => setTimeout(r, 800));
      t.setMode('flash'); t.send('周边分析'); const ok = await t.waitAnswer(60000);
      if (!ok) return { pass: false, stage: 's3', obs: '回答超时' };
      const b = t.badge();
      const askOpts = document.querySelectorAll('.aiq-ask-chip');
      if (askOpts.length > 0) return { pass: true, obs: `ask_user 选项 ${askOpts.length} 个`, review: '问题是否精准？' };
      if (b && /缺数据/.test(b)) return { pass: true, obs: `GAP（缺参→GAP 兜底）badge="${b}"` };
      return { pass: true, obs: `badge="${b}"`, review: '缺参时是否提问了（非直接放弃）？' };
    },
  },
  { id: 'T11', name: 'GIS 裁剪（clip 点层）', category: '工具选择', type: 'llm',
    run: async (t) => {
      t.clearLog(); t.loadPoints(FX); await new Promise(r => setTimeout(r, 800));
      t.setMode('flash'); t.send('裁剪西陵区范围内的情绪点'); const ok = await t.waitAnswer(90000);
      if (!ok) return { pass: false, stage: 's3', obs: '回答超时' };
      const b = t.badge();
      if (b && /缺数据|未产出/.test(b)) return { pass: false, stage: 's3', obs: `GAP: badge="${b}"` };
      return { pass: true, obs: `badge="${b}"`, review: '是否裁剪出了点层（结果为点图层）？' };
    },
  },
  { id: 'T12', name: 'Pro/Flash 切换', category: 'UI', type: 'no-llm',
    run: async (t) => {
      t.setMode('flash');
      if (t.getMode() !== 'flash') return { pass: false, stage: 's4', obs: `Flash 切换失败: mode=${t.getMode()}` };
      t.setMode('pro');
      if (t.getMode() !== 'pro') return { pass: false, stage: 's4', obs: `Pro 切换失败: mode=${t.getMode()}` };
      return { pass: true, obs: 'Pro/Flash 切换 OK' };
    },
  },
];
