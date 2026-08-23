// SHELL2(FIX) FIX-09：追问纯逻辑单测（node 直跑·无浏览器）——由 test_followup_chips.py 驱动。
// 覆盖：空/非数组归一化·非串过滤·截 3·ask 互斥·优先级（cues > 胶囊 > 静态）。
import { normalizeFollowupCues, pickFollowupSource } from 'file:///D:/Github/emotion_map/frontend/js/ai_qa/followup.js';

let fail = 0;
const results = [];
const ok = (cond, msg) => { if (!cond) fail++; results.push({ ok: !!cond, msg }); };

// 归一化：空/非数组/混合脏数据/截 3
ok(JSON.stringify(normalizeFollowupCues(undefined)) === '[]', 'undefined→[]');
ok(JSON.stringify(normalizeFollowupCues(null)) === '[]', 'null→[]');
ok(JSON.stringify(normalizeFollowupCues('str')) === '[]', '非数组→[]');
ok(JSON.stringify(normalizeFollowupCues([])) === '[]', '空数组→[]');
ok(JSON.stringify(normalizeFollowupCues([null, '', '  甲  ', 123, '乙', '丙', '丁'])) === '["甲","123","乙"]',
  '混合脏数据：trim+非串 String 化+滤空+截 3');
ok(JSON.stringify(normalizeFollowupCues(['a', 'b'])) === '["a","b"]', '≤3 条原样');

// 源选择：ask 互斥 / cues 优先 / 胶囊次之 / 静态兜底
ok(pickFollowupSource(null).kind === 'none', 'null trace→none');
ok(pickFollowupSource({ exit: 'ask', followupCues: ['x'] }).kind === 'none', 'ask 轮互斥（即使带 cues）');
const srcCues = pickFollowupSource({ exit: 'final', followupCues: ['a', 'b'] });
ok(srcCues.kind === 'cues' && srcCues.items.length === 2, 'cues 源命中');
const srcMix = pickFollowupSource({ exit: 'final', followupCues: ['a'], defense: { capsules: [{ label: 'L1', skill: 'x' }] } });
ok(srcMix.kind === 'cues', '优先级：cues > 胶囊');
const srcCap = pickFollowupSource({ exit: 'final', defense: { capsules: [{ label: 'L1', skill: 'x' }] } });
ok(srcCap.kind === 'capsules' && srcCap.items.length === 1, '胶囊源命中（无 cues 时）');
ok(pickFollowupSource({ exit: 'final' }).kind === 'static', '无 cues 无胶囊→static 兜底');
const srcDirty = pickFollowupSource({ exit: 'final', followupCues: [null, '   '] });
ok(srcDirty.kind === 'static', '全脏 cues 归一后为空→落 static（不悬空渲染）');

process.stdout.write(JSON.stringify({ fail, results }));
process.exit(fail ? 1 : 0);
