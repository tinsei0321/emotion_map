// ═══ sse-parse.mjs — SSE 帧分隔解析纯函数（PT-CB15 PROMOTE P2-7/P2-11）═══
// 约定（两端注释互指·P2-11）：后端帧 = `event: <名>\ndata: <JSON>\n\n`（LF·双换行分帧）；
// 本解析归一化 CRLF 后按 \n\n 切帧。node 单测：tests/acp_schema/test_codex_sse_parse.py。

/**
 * 从缓冲提取完整 SSE 帧。
 * @param {string} buf 累积缓冲（含历史残留）
 * @returns {{frames: Array<{ev: string, data: string}>, rest: string}}
 *   frames = 完整帧（event 行 + data 行）·rest = 尾部未完成残留（等待后续 chunk）
 */
export function parseSseFrames(buf) {
  const b = String(buf == null ? '' : buf).replace(/\r\n/g, '\n');   // P2-11：CRLF 归一化
  const frames = [];
  let cur = b;
  let sep;
  while ((sep = cur.indexOf('\n\n')) >= 0) {
    const frame = cur.slice(0, sep);
    cur = cur.slice(sep + 2);
    const ev = (frame.match(/^event:\s*(.+)$/m) || [])[1] || '';
    const data = (frame.match(/^data:\s*(.+)$/m) || [])[1] || '';
    if (ev || data) frames.push({ ev, data });
  }
  return { frames, rest: cur };
}
