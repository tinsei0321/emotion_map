# -*- coding: utf-8 -*-
"""CB-35 page7 排序数据审计（claude组·只读不 git）
对账 page7_分组汇总_2026-08-14.xlsx vs 三源矩阵 + 分母表。
"""
import warnings; warnings.filterwarnings('ignore')
import pandas as pd, os
BASE = r'DATA/analysis'
PJ = os.path.join(BASE, 'page7小结')

def sp(msg):
    try: print(msg)
    except Exception: print(msg.encode('utf-8', 'replace').decode('utf-8', 'replace'))

# ===== 源矩阵 =====
safe = pd.read_csv(os.path.join(BASE, '安全韧性', '安全韧性_社区3类矩阵.csv'),
                   encoding='utf-8-sig').set_index('社区')['总点数'].rename('安全体检')
live = pd.read_csv(os.path.join(BASE, '民生基础', '民生_社区5类矩阵.csv'),
                   encoding='utf-8-sig').set_index('社区')['总点数'].rename('民生体检')
h = pd.read_csv(os.path.join(BASE, '12345主观', '12345_社区x9类_西陵伍家.csv'),
                encoding='utf-8-sig').set_index('社区')
h_safe = (h['出行安全'] + h['消防安全'] + h['环境安全'] + h['管网安全']).rename('安全诉求')
h_live = (h['住宅'] + h['停车'] + h['出行'] + h['噪声'] + h['物业']).rename('民生诉求')
h_other = h['其他'].rename('其他诉求') if '其他' in h.columns else None
den = pd.read_csv(os.path.join(PJ, '社区规模分母_174.csv'),
                  encoding='utf-8-sig').set_index('社区')['bldg_n'].rename('楼栋')

src = pd.concat([safe, live, h_safe, h_live, den], axis=1).fillna(0)
src['体检点_源'] = src['安全体检'] + src['民生体检']
src['诉求件_源'] = src['安全诉求'] + src['民生诉求']
src['客观密度'] = src.apply(lambda r: r['体检点_源'] / r['楼栋'] * 100 if r['楼栋'] > 0 else None, axis=1)
src['主观密度'] = src.apply(lambda r: r['诉求件_源'] / r['楼栋'] * 100 if r['楼栋'] > 0 else None, axis=1)

# ===== xlsx =====
xl = pd.read_excel(os.path.join(PJ, 'page7_分组汇总_2026-08-14.xlsx'), header=0, skiprows=[1])
xl.columns = ['序号', '社区', '楼栋', '安体密', '安诉密', '民体密', '民诉密',
              '体检点', '诉求件', '评估', '备注']
xl = xl.dropna(subset=['社区']).reset_index(drop=True)
for c in ['楼栋', '体检点', '诉求件', '安体密', '安诉密', '民体密', '民诉密']:
    xl[c] = pd.to_numeric(xl[c], errors='coerce')

sp('=' * 78)
sp('一·数值对账（xlsx vs 源矩阵：楼栋/体检点/诉求件）')
sp('=' * 78)
hdr = '{:<10}{:>10}{:>12}{:>12}  {}'.format('社区', '楼栋xl/源', '体检xl/源', '诉求xl/源', '判定')
sp(hdr)
mismatch = []
for _, r in xl.iterrows():
    nm = r['社区']
    if nm not in src.index:
        sp('{:<10}  [源缺失]'.format(nm)); continue
    s = src.loc[nm]
    bld_ok = (r['楼栋'] == s['楼栋'])
    ti_ok = (r['体检点'] == s['体检点_源'])
    rq_ok = (r['诉求件'] == s['诉求件_源'])
    tag = []
    if not bld_ok: tag.append('楼栋!')
    if not ti_ok: tag.append('体检!')
    if not rq_ok: tag.append('诉求!')
    flag = 'OK' if not tag else 'XX ' + ' '.join(tag)
    if tag: mismatch.append((nm, tag, r['体检点'], s['体检点_源'], r['诉求件'], s['诉求件_源']))
    row = '{:<10}{:>4}/{:<4}{:>5}/{:<5}{:>5}/{:<5}  {}'.format(
        nm.replace('社区', ''), int(r['楼栋']), int(s['楼栋']),
        int(r['体检点']), int(s['体检点_源']), int(r['诉求件']), int(s['诉求件_源']), flag)
    sp(row)
sp('\n[数值对账结论] {} 个社区全对；{} 个不符：{}'.format(
    len(xl) - len(mismatch), len(mismatch), mismatch if mismatch else '无'))

# ===== 密度自洽（H=安+民体检点，密度=点/楼栋×100）=====
sp('\n' + '=' * 78)
sp('二·密度自洽（H=安体点+民体点；D=安体点/楼栋×100；F=民体点/楼栋×100）')
sp('=' * 78)
derr = []
for _, r in xl.iterrows():
    nm = r['社区']; s = src.loc[nm]
    # 由密度反推点数
    d_pts = round(r['安体密'] * r['楼栋'] / 100)
    f_pts = round(r['民体密'] * r['楼栋'] / 100)
    e_pts = round(r['安诉密'] * r['楼栋'] / 100)
    g_pts = round(r['民诉密'] * r['楼栋'] / 100)
    h_calc = d_pts + f_pts
    i_calc = e_pts + g_pts
    h_ok = (h_calc == r['体检点'])
    i_ok = (i_calc == r['诉求件'])
    # 源一致性
    d_src_ok = (d_pts == s['安全体检']); f_src_ok = (f_pts == s['民生体检'])
    e_src_ok = (e_pts == s['安全诉求']); g_src_ok = (g_pts == s['民生诉求'])
    if not (h_ok and i_ok and d_src_ok and f_src_ok and e_src_ok and g_src_ok):
        derr.append((nm, 'D{}F{}->H{}(xl{})'.format(d_pts, f_pts, h_calc, r['体检点']),
                     'E{}G{}->I{}(xl{})'.format(e_pts, g_pts, i_calc, r['诉求件']),
                     'src安体{}民体{}安诉{}民诉{}'.format(int(s['安全体检']), int(s['民生体检']), int(s['安全诉求']), int(s['民生诉求']))))
sp('密度→点数 反推不符：{} 项'.format(len(derr)))
for e in derr: sp('  ' + str(e))
if not derr: sp('  全部密度↔点数↔源 自洽 ✓')

# ===== 分层判定（阈值 28.57 / 146.67）=====
sp('\n' + '=' * 78)
sp('三·分层判定（客观=体检点/楼栋×100；主观=诉求件/楼栋×100；阈值客观28.57/主观146.67）')
sp('=' * 78)
TO, TS = 28.57, 146.67
def classify(o, su):
    if o is None or su is None: return '无楼栋'
    if o >= TO and su >= TS: return '双高'
    if o >= TO and su < TS: return '客观隐患高·诉求未暴露'
    if o < TO and su >= TS: return '主观诉求高·体检未印证'
    return '其余(双低)'
lerr = []
for _, r in xl.iterrows():
    nm = r['社区']; s = src.loc[nm]
    calc = classify(s['客观密度'], s['主观密度'])
    xl_tag = r['评估']
    ok = (calc.split('·')[0].replace('客观隐患高','客观隐患高·诉求未暴露').replace('主观诉求高','主观诉求高·体检未印证') == xl_tag) or (calc == xl_tag)
    # 宽松匹配
    def norm(t): return t.replace('·诉求未暴露','').replace('·体检未印证','')
    ok = norm(calc) == norm(xl_tag)
    if not ok: lerr.append((nm, round(s['客观密度'],1), round(s['主观密度'],1), calc, xl_tag))
    sp('{:<10} 客观{:>6} 主观{:>7}  阈值判[{}] xlsx[{}] {}'.format(
        nm.replace('社区',''), round(s['客观密度'],1), round(s['主观密度'],1), calc, xl_tag, 'OK' if ok else 'XX'))
sp('\n[分层判定] 不符：{} 项 {}'.format(len(lerr), lerr if lerr else '→ 全部标签与阈值判定一致 ✓'))

# ===== 阈值来源（p75 验证）=====
sp('\n' + '=' * 78)
sp('四·阈值来源验证（在全样本上算客观/主观密度的分位数）')
sp('=' * 78)
sub = src[(src['楼栋'] > 0) & (src['楼栋'] >= 20)].copy()  # 去楼栋<20 & 有楼栋
sp('参与社区数(楼栋>0 且>=20): {}'.format(len(sub)))
for q in [0.5, 0.75, 0.8]:
    sp('  客观密度 p{:.0f}={:.2f}  主观密度 p{:.0f}={:.2f}'.format(
        q*100, sub['客观密度'].quantile(q), q*100, sub['主观密度'].quantile(q)))
sp('  → 给定阈值 客观28.57 / 主观146.67 是否=p75？')
sp('  客观p75={:.2f} vs 28.57；主观p75={:.2f} vs 146.67'.format(
    sub['客观密度'].quantile(0.75), sub['主观密度'].quantile(0.75)))

# ===== 排序严格性 =====
sp('\n' + '=' * 78)
sp('五·排序严格性（双高/客观高=体检点降序；主观高=诉求件降序）')
sp('=' * 78)
def chk_block(df, key, name):
    vals = df[key].tolist()
    desc = all(vals[i] >= vals[i+1] for i in range(len(vals)-1))
    sp('[{}] {}项 降序{}  值={}'.format(name, len(vals), 'OK✓' if desc else 'XX乱序', vals))
    return desc
bl = xl[xl['评估'].str.startswith('双高')]
bo = xl[xl['评估'].str.startswith('客观隐患高')]
bs = xl[xl['评估'].str.startswith('主观诉求高')]
chk_block(bl, '体检点', '双高·体检点')
chk_block(bo, '体检点', '客观高·体检点')
chk_block(bs, '诉求件', '主观高·诉求件')
sp('坑位数：双高{} 客观高{} 主观高{} 合计{}'.format(len(bl), len(bo), len(bs), len(xl)))

# ===== 跨页：红五角星对齐 =====
sp('\n' + '=' * 78)
sp('六·跨页一致性')
sp('=' * 78)
STAR = ['西峡社区', '深圳路社区', '金安岭社区', '镇境山社区']
obj_set = set(bo['社区'])
sp('红五角星4社区(主图体检独证) vs 客观高层对齐：')
for s in STAR:
    sp('  {} → 在客观高层: {}'.format(s, s in obj_set))
sp('客观高层8社区: {}'.format(list(bo['社区'])))
# 港务诉求绝对量排名
rq_rank = src['诉求件_源'].sort_values(ascending=False)
sp('诉求绝对量 TOP5: {}'.format([(i, int(v)) for i, v in rq_rank.head(5).items()]))
gw_pos = list(rq_rank.index).index('港务社区') + 1
sp('港务诉求绝对量排名: 第{} (417件)'.format(gw_pos))
sp('港务体检点: {} (xlsx)'.format(int(xl[xl['社区']=='港务社区']['体检点'].iloc[0])))
# 沉默比
sp('沉默比：深圳{}/{:.0f}x 金安{}/{:.1f}x 西峡{}/{:.1f}x'.format(
    int(src.loc['深圳路社区','体检点_源']), src.loc['深圳路社区','体检点_源']/max(src.loc['深圳路社区','诉求件_源'],1),
    int(src.loc['金安岭社区','体检点_源']), src.loc['金安岭社区','体检点_源']/max(src.loc['金安岭社区','诉求件_源'],1),
    int(src.loc['西峡社区','体检点_源']), src.loc['西峡社区','体检点_源']/max(src.loc['西峡社区','诉求件_源'],1)))

# ===== 楼栋<20 低置信 =====
sp('\n' + '=' * 78)
sp('七·低置信（楼栋<20）排查')
sp('=' * 78)
lowb = xl[xl['楼栋'] < 20]
sp('20行内楼栋<20社区: {} {}'.format(len(lowb), list(lowb['社区']) if len(lowb) else '→ 无，天然规避 ✓'))
sp('楼栋最小3社区: {}'.format(xl.nsmallest(3,'楼栋')[['社区','楼栋']].values.tolist()))
