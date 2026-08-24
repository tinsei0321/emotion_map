// ═══ codex_sse_parse_dump.mjs — SSE 帧解析离线测试驱动（PT-CB15 PROMOTE P2-7）═══
// 跑法：node tests/acp_schema/codex_sse_parse_dump.mjs → stdout 一行 JSON（各用例解析结果）
// 桥式测法同源 ba_wire_dump.mjs：node 驱前端纯函数 → pytest 断言（无浏览器无网络）。
import { parseSseFrames } from '../../frontend/js/ai_qa/sse-parse.mjs';

const cases = {
  // 标准 LF 两帧
  lf_two: 'event: delta\ndata: {"event":"delta","n":1}\n\nevent: done\ndata: {"event":"done"}\n\n',
  // CRLF 帧分隔（P2-11 兼容）
  crlf: 'event: delta\r\ndata: {"n":2}\r\n\r\nevent: ping\r\ndata: {"elapsed":1}\r\n\r\n',
  // 尾部不完整帧（残留待下一 chunk）
  trailing: 'event: delta\ndata: {"n":3}\n\nevent: tool\nda',
  // 混合：完整帧 + 噪音帧（只有 data）+ CRLF 混合
  mixed: 'event: delta\ndata: {"n":4}\n\nnoise-line\ndata: {"n":5}\n\nevent: tool\r\ndata: {"n":6}\r\n\r\n',
  // 空输入
  empty: '',
};

const out = {};
for (const [k, v] of Object.entries(cases)) out[k] = parseSseFrames(v);
console.log(JSON.stringify(out));
