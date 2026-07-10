// ═══ landuse_colors.js — 市级国土空间总体规划制图规范·附录 B「用地用海分类配色指引表」═══
// 数据源：docs/市级国土空间总体规划制图规范.pdf 附录 B（一次性抽取，2026-07-10）。
// 39 类（PDF 表全量；用户口中的"38 类"为约数）。RGB 已规整 PDF 的全角标点
//   （公用设施用地原 RGB(0，99,128) 全角逗号；盐田用地原 RGB（0,0,255）全角括号）。
// 这是【数据色 token】（地图填充色），与 design/ 的 UI chrome token 分离——
//   用地图层按 DLMC 落规范色，UI 图例 swatch 引用本表，勿混入 design/tokens.json。
// 改色 = 改本表（数据，非逻辑）。matcher 做 DLMC/名称→规范色模糊匹配。

/** 附录 B 用地用海分类 × 规范 RGB（name=规范全称；aliases=常见短标签/同义，供模糊匹配）。 */
export const LANDUSE_COLORS = [
  { name: '耕地', rgb: [245, 248, 220] },
  { name: '园地', rgb: [191, 233, 170] },
  { name: '林地', rgb: [104, 177, 103] },
  { name: '草地', rgb: [205, 245, 122] },
  { name: '湿地', rgb: [101, 205, 170] },
  { name: '农业设施建设用地', rgb: [216, 215, 159] },
  { name: '城镇住宅用地', rgb: [255, 255, 45], aliases: ['居住用地', '城镇居住用地', '居住', '住宅', '二类居住', '一类居住'] },
  { name: '农村宅基地', rgb: [255, 211, 128], aliases: ['农村居住用地'] },
  { name: '机关团体用地', rgb: [255, 0, 255] },
  { name: '文化用地', rgb: [255, 127, 0] },
  { name: '教育用地', rgb: [255, 133, 201] },
  { name: '科研用地', rgb: [230, 0, 92] },
  { name: '体育用地', rgb: [0, 165, 124] },
  { name: '医疗卫生用地', rgb: [255, 127, 126], aliases: ['医疗', '卫生'] },
  { name: '社会福利用地', rgb: [255, 159, 127] },
  { name: '商业服务业用地', rgb: [255, 0, 0], aliases: ['商业', '商务', '服务业', '商住'] },
  { name: '工业用地', rgb: [187, 150, 116], aliases: ['工业', '一类工业', '二类工业'] },
  { name: '采矿用地', rgb: [158, 108, 84] },
  { name: '盐田用地', rgb: [0, 0, 255] },
  { name: '仓储用地', rgb: [135, 97, 211], aliases: ['仓储', '物流'] },
  { name: '储备库用地', rgb: [153, 153, 255] },
  { name: '交通运输用地', rgb: [183, 183, 183], aliases: ['交通'] },
  { name: '公路用地', rgb: [173, 173, 173] },
  { name: '城镇道路用地', rgb: [163, 163, 163], aliases: ['道路'] },
  { name: '管道运输用地', rgb: [153, 153, 153] },
  { name: '公用设施用地', rgb: [0, 99, 128], aliases: ['公用设施', '基础设施'] },
  { name: '公园绿地', rgb: [0, 255, 0], aliases: ['公园', '绿地'] },
  { name: '防护绿地', rgb: [20, 141, 74] },
  { name: '广场用地', rgb: [172, 255, 207], aliases: ['广场'] },
  { name: '特殊用地', rgb: [133, 145, 86] },
  { name: '留白用地', rgb: [255, 255, 255] },
  { name: '陆地水域', rgb: [51, 142, 192], aliases: ['水域', '水系', '河流', '湖泊'] },
  { name: '渔业用海', rgb: [148, 213, 235] },
  { name: '工矿通信用海', rgb: [86, 166, 211] },
  { name: '交通运输用海', rgb: [108, 139, 209] },
  { name: '游憩用海', rgb: [26, 170, 230] },
  { name: '特殊用海', rgb: [131, 188, 214] },
  { name: '其他土地', rgb: [238, 238, 238] },
  { name: '其他海域', rgb: [214, 234, 243] },
];

const _toHex = (rgb) => '#' + rgb.map((n) => Math.max(0, Math.min(255, Number(n) | 0)).toString(16).padStart(2, '0')).join('').toUpperCase();
LANDUSE_COLORS.forEach((c) => { c.hex = _toHex(c.rgb); });

const _DEFAULT = '#9AA0A6';   // 未匹配兜底灰（中性，区别于任何规范色）

/** DLMC/用地名称 → 规范色 hex。模糊匹配三级：精确规范名 → 别名精确 → 子串（"商业"⊂"商业服务业用地"）。
 *  子串级取命中最长规范名（更具体优先），解决"公园广场"→公园绿地 vs 广场用地的歧义。 */
export function matchLanduseColor(name) {
  const s = String(name || '').trim();
  if (!s) return _DEFAULT;
  const exact = LANDUSE_COLORS.find((c) => c.name === s);
  if (exact) return exact.hex;
  const alias = LANDUSE_COLORS.find((c) => (c.aliases || []).includes(s));
  if (alias) return alias.hex;
  let best = null;
  for (const c of LANDUSE_COLORS) {
    const hit = c.name.includes(s) || s.includes(c.name) || (c.aliases || []).some((a) => s.includes(a) || a.includes(s));
    if (hit && (!best || c.name.length > best.name.length)) best = c;
  }
  return best ? best.hex : _DEFAULT;
}

/** land_* 预设 → 规范色（preset 的 label 多为短标签如"商业/居住/公园广场"，走 matchLanduseColor）。 */
export function presetLanduseColor(label) { return matchLanduseColor(label); }

/** MapLibre 数据驱动 fill-color 表达式：按 feature[field] 的 DLMC 名称落规范色（离散分段）。
 *  field 默认 'DLMC'。供任意含 DLMC 的多类用地层按类上色（一个图层含多用地类型时）。 */
export function landuseFillColorExpr(field = 'DLMC') {
  const expr = ['match', ['get', field]];
  for (const c of LANDUSE_COLORS) {
    expr.push(c.name, c.hex);
    for (const a of c.aliases || []) expr.push(a, c.hex);
  }
  expr.push(_DEFAULT);
  return expr;
}

/** CSS 变量块（供图例 swatch / UI 引用）：--land-<index>: #hex;
 *  变量名用索引（CSS 自定义属性含中文虽合法但不通用），名→色以本表 LANDUSE_COLORS 为权威。 */
export const LANDUSE_CSS_VARS = LANDUSE_COLORS
  .map((c, i) => `--land-${i}: ${c.hex};   /* ${c.name} */`).join('\n');
