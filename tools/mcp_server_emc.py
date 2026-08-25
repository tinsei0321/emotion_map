#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PT-CB5 T3 · G10 标准插座（MCP server）——七件分析工具 + PT-CB6 render_spec 第 8 插座。

把 EMC 既有后端能力包装为 MCP 工具，供 zcode/claude/codex/dsh 等
通用助手经协议即插即用。分析七工具纯只读、零 LLM；render_spec 仅写
收件箱 spec JSON（DATA/exports/render_inbox·前端显示屏消费）。

用法：
  py tools/mcp_server_emc.py        # stdio 启动（Ctrl+C 退出）

纪律：
  - 重依赖（geopandas/rag 等）全部函数体内惰性导入，启动轻快；
  - 每个工具一个追踪号 MOD_AIQA.F_021-F_028（F_023 kb_facts 按主手
    裁决直映真身签名 query/keyword/topic/limit；F_028=render_spec）；
  - print 走 _safe_print；代码禁 emoji；
  - 返回值必带 caliber 对象（口径/语义/禁用边界/注册表卡引用）。
"""
import json
import os
import random
import re
import sys
import time
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from core.tracker import register_track_id, track

register_track_id('MOD_AIQA.F_021', 'MCP list_data（数据说明书：点层+边界层目录·开卷定参）')
register_track_id('MOD_AIQA.F_022', 'MCP rag_query（带来源知识检索·v1 综合降级 deferred_v2）')
register_track_id('MOD_AIQA.F_023', 'MCP kb_facts（行业事实卡·真身签名直映 query/keyword/topic/limit）')
register_track_id('MOD_AIQA.F_024', 'MCP outlet_card（行业出口卡·确定性组装·对话级）')
register_track_id('MOD_AIQA.F_025', 'MCP zonal_stats（单元聚合·宏观/中观结论）')
register_track_id('MOD_AIQA.F_026', 'MCP buffer（缓冲影响圈·中观）')
register_track_id('MOD_AIQA.F_027', 'MCP rank（排序评价·最差/最好 Top-N）')
register_track_id('MOD_AIQA.F_028', 'MCP render_spec（图层图纸：dataset/inline→spec 落收件箱）')
register_track_id('MOD_AIQA.F_031', 'MCP render_file（把文件现在显示到地图：服务端读取·≤60 内联/>60 自动登记临时 dataset·一步到位）')
register_track_id('MOD_AIQA.F_032', 'MCP emc_status（8080 地图服务就绪探测·入口向导流程轮询用·临时测试件·无 @track 明文豁免——轻探测件非业务逻辑·先例 F_029 豁免条·终审 N2 成文）')
register_track_id('MOD_AIQA.F_033', 'MCP grid_aggregate（方格网空间聚合·参数化替代 T8 脚本）')
register_track_id('MOD_AIQA.F_034', 'MCP compare_regions（≥2 区域同口径并排+差异·契约 boundaries 参数）')
register_track_id('MOD_AIQA.F_035', 'MCP hotspot_analysis（Gi* 逐点显著聚集·五档分类）')
register_track_id('MOD_AIQA.F_036', 'MCP nearest_analysis（最近邻锚定·k 近邻配对+投影米距）')
register_track_id('MOD_AIQA.F_037', 'MCP area_stats（面积占比统计·group_by 分组·km2）')
register_track_id('MOD_AIQA.F_038', 'MCP overlay_analysis（叠置交叉·面∩/∪/差/对称差+面积）')
register_track_id('MOD_AIQA.F_039', 'MCP trend_analysis（T1/T2/T3 三期时序对比·方向+幅度）')
register_track_id('MOD_AIQA.F_040', 'MCP report_assemble（综合报告组装·确定性零 LLM·四段结构）')

MANIFEST = os.path.join(REPO, 'DATA', 'REGISTRY', 'presets', 'manifest.json')

# P+ scheme 受管样式词表（前端按名解析·未知即拒）
SCHEMES = ('community_choropleth_v1', 'point_default_v1', 'boundary_fill_v1')

CALIBERS = {
    'list_data': {
        'scale': '数据资产清单',
        'semantics': '可供分析的点层与边界层目录（开卷定参的查询面）',
        'limits': '结论层（usage=analysis_output）禁作空间操作输入',
        'refs': ['G-2', 'K-C1'],
    },
    'rag_query': {
        'scale': '知识检索',
        'semantics': '本地知识库向量检索（非穷尽）·结果为素材非结论',
        'limits': 'Top-K 召回非全量；结论须综合并注来源；勿将倾向表述为精确值',
        'refs': ['K-01'],
    },
    'kb_facts': {
        'scale': '事实卡',
        'semantics': '本地蒸馏的权威事实（带来源年份）',
        'limits': '事实卡非实时数据；引用须带来源',
        'refs': ['K-01'],
    },
    'outlet_card': {
        'scale': '答案级出口',
        'semantics': '确定性组装的行业出口卡片（结果范式 agent 第三段·对话级）',
        'limits': '字段缺失降级不编造；文件级导出属 v2',
        'refs': ['K-01', 'K-03'],
    },
    'zonal_stats': {
        'scale': '宏观/中观（单元聚合）',
        'semantics': '情绪点按边界单元的统计聚合——宏观倾向判断',
        'limits': '非逐户调查结论；社区数口径见 K-C1；勿当精确诊断',
        'refs': ['K-01', 'K-C1'],
    },
    'buffer': {
        'scale': '中观（设施影响圈）',
        'semantics': '设施周边半径内的情绪聚合（半径语义=尺度表·社区250/区500/主城1000）',
        'limits': '半径为可达性近似非服务边界；结论属影响面判断',
        'refs': ['K-C1'],
    },
    'rank': {
        'scale': '中观（排序落点）',
        'semantics': '按极性指数的单元排序（最差/最好 Top-N）',
        'limits': '排序基于聚合指标非原始诉求逐条复核；"最差"为统计表述',
        'refs': ['K-01'],
    },
    'render_spec': {
        'scale': '呈现层',
        'semantics': '图层图纸（数据引用+样式令牌）——由前端解析渲染',
        'limits': 'v1 语义令牌（无解析副本·场景S 双载留 v2）；非分析操作',
        'refs': ['G-2(显示徽标)', '渲染契约v1'],
    },
}


def _derive_followup_cues(results, top_dim):
    """H1 followup_cue 确定性派生（D2 四红线·零 LLM·三张小表 ai_qa/rag_cues.json）。

    价值序：维度相邻 > 口径关联 > 小节邻接；疑问句方向零事实断言；
    目标库内真实存在才发；无 cue = 省略字段（不返回空数组）。"""
    import json as _json
    import os as _os

    cues_path = _os.path.join(REPO, 'ai_qa', 'rag_cues.json')
    try:
        with open(cues_path, encoding='utf-8') as _fh:
            tables = _json.load(_fh)
    except Exception:
        return []

    dims_in_results = {res.get('data_dim', '') for res in results if res.get('data_dim')}
    neighbors = tables.get('dim_neighbors', {})
    translations = tables.get('caliber_translations', {})
    blacklist = set(tables.get('section_blacklist', []))

    out = []
    # ①维度相邻（top_dim 的邻居·非当前结果已含维度）
    for nb in neighbors.get(top_dim, [])[:2]:
        if nb not in dims_in_results:
            out.append(f'要对比{nb}维度的情况吗？（可换用相邻维度数据交叉验证）')

    # ②口径关联（命中含 K-C/K-G 的 source·文案翻译·禁裸编号）
    for res in results:
        src = res.get('source', '')
        for k_id, cn_text in translations.items():
            if k_id in src and k_id not in [c for c in out if k_id in c]:
                out.append(f'{cn_text}的适用范围是什么？（可用 kb_facts 精确查）')
                break

    # ③小节邻接（同文档相邻小节·黑名单过滤）——当前结果源去重后取首文档
    if results:
        src0 = results[0].get('source', '')
        base = src0.split('#')[0] if '#' in src0 else ''
        if base and not any(b in base for b in blacklist):
            out.append(f'{base.split("/")[-1]}的上下文背景是什么？（可查同文档相邻小节）')

    return out[:3]   # 2-3 条·价值序


# ── PT-CB9R A-2 · 检索信号字段族阈值（可观测参数·沿 fact ×1.2「系数作观测起步·不拍死」先例）──
# 校准依据（2026-08-23 实测·默认 rrf 模式）：相关查询 dense top1 余弦 0.64-0.84·离题 0.44-0.45。
# dense_score=加权前原始余弦（RRF 融合分为秩分不承载语义近度·故置信读 dense_score 不读 score）。
_RAG_SIG = {
    'dense_high': 0.62,   # top1 dense_score ≥ 此 → 高置信
    'dense_low': 0.50,    # top1 dense_score < 此 → 低置信
    'bm25_high': 8.0,     # 消融模式（bm25）粗校·观测起步（未实测校准）
    'bm25_low': 3.0,
    'narrow_share': 0.6,  # top_dim 占比 > 此（且结果≥3 条）→ 查询面窄
}


def _derive_retrieval_signals(results, k, top_dim, dim_counts):
    """PT-CB9R A-2 信号字段族确定性派生（零 LLM·零二次检索·「告知不足·不替外脑补救」）。

    confidence 三档：top1 dense_score 绝对值定档（margin 只调文案不调档——
      实测离题查询亦可有大 margin·margin 降档会冤杀「一强多弱」正常命中）；
    coverage_hint：top_dim 占比 >60%（结果≥3 条才判·防 1/1=100% 噪声）→ 查询面窄提示；
    thin_result：命中数 < k 或低置信；
    retry_cue：低置信/thin 时发——相邻维度词复用 rag_cues.json dim_neighbors 表。
    返回 dict：confidence/thin_result 恒在；coverage_hint/retry_cue 按需省略（H1 同律）。"""
    count = len(results)
    top1 = 0.0
    margin = 0.0
    if count:
        def _ds(res):
            v = res.get('dense_score')
            return v if v is not None else res.get('score', 0.0)
        top1 = _ds(results[0])
        margin = (top1 - _ds(results[1])) if count > 1 else top1

    from tools import rag_index as _ri
    if _ri._BM25_MODE == 'bm25':
        hi, lo = _RAG_SIG['bm25_high'], _RAG_SIG['bm25_low']
    else:
        hi, lo = _RAG_SIG['dense_high'], _RAG_SIG['dense_low']

    if not count or top1 < lo:
        confidence = '低'
    elif top1 >= hi:
        confidence = '高'
    else:
        confidence = '中'

    thin = (count < k) or (confidence == '低')
    sig = {'confidence': confidence, 'thin_result': thin}

    # 查询面窄：单维占比 >60%（结果≥3 条才判）
    if count >= 3 and top_dim and dim_counts.get(top_dim, 0) / count > _RAG_SIG['narrow_share']:
        sig['coverage_hint'] = (f'结果集中于「{top_dim}」单一维度（{dim_counts[top_dim]}/{count}）'
                                '——查询面偏窄：精确口径建议 kb_facts·或换相邻维度查询')

    # retry_cue（低置信或 thin 才发·文案分流用 margin）
    if thin:
        cues = []
        if confidence == '低':
            if count and margin > 0.02:
                cues.append('命中相关度整体偏低——建议细化关键词（加维度词/地名）或改精确查询 kb_facts')
            else:
                cues.append('语料未覆盖该主题或关键词过泛——建议换精确名词/口径数字查 kb_facts')
        else:
            cues.append(f'命中 {count} 条不足 k={k}——建议放宽关键词或改精确查询 kb_facts')
        # 相邻维度提示（复用 rag_cues.json dim_neighbors 骨架）
        if top_dim:
            import json as _json2
            import os as _os2
            try:
                with open(_os2.path.join(REPO, 'ai_qa', 'rag_cues.json'), encoding='utf-8') as _fh2:
                    _nb = _json2.load(_fh2).get('dim_neighbors', {})
            except (FileNotFoundError, OSError, ValueError):
                _nb = {}
            for nb in _nb.get(top_dim, [])[:1]:
                if nb not in dim_counts:
                    cues.append(f'可换相邻维度「{nb}」重查验证')
        sig['retry_cue'] = cues
    return sig


def _reject_analysis_output(preset_id, param, caliber):
    """G-2/铁律7 服务端强制：analysis_output 结论层禁作空间操作输入（PT-CB5 审计发现即修）。

    PT-CB10 C2-1（A9 收窄）：manifest 读取按异常类型区分处置，禁宽 except fail-open——
    - FileNotFoundError/OSError（文件缺失）：G8b 枚举层仍有引导 → 显式放行（返 None）并 stderr 留痕；
    - json.JSONDecodeError（内容损坏）：usage 无法判定=防穿洞风险 → 拒绝该输入并说明原因；
    - 其他异常：拒绝 + 异常摘要（宁可诚实拒绝，不可静默放行结论层）。
    """
    try:
        with open(MANIFEST, encoding='utf-8') as _fp:
            _manifest_groups = json.load(_fp)
    except (FileNotFoundError, OSError) as exc:
        _safe_print(f'[WARN] G-2 守卫: manifest 不可读·放行本次并依赖 G8b 枚举引导: {exc}', file=sys.stderr)
        return None
    except json.JSONDecodeError as exc:
        return {'ok': False, 'hint': (
            f'{param} 的 usage 判定失败：manifest 内容损坏（{exc}）·G-2 守卫拒绝该输入'
            '（请修复 DATA/REGISTRY/presets/manifest.json 后重试）'), 'caliber': caliber}
    except Exception as exc:
        return {'ok': False, 'hint': (
            f'{param} 的 usage 判定失败：manifest 读取异常（{type(exc).__name__}: {str(exc)[:80]}）'
            '·G-2 守卫拒绝该输入'), 'caliber': caliber}
    for _g in _manifest_groups:
        for _it in _g.get('items', []):
            if _it.get('id') == preset_id and _it.get('usage') == 'analysis_output':
                return {'ok': False, 'hint': (
                    f'{param}={preset_id} 是结论层（usage=analysis_output·铁律7 禁作分析输入）；'
                    '请改用 input 层（调用 list_data 查看清单与 usage 标记）'), 'caliber': caliber}
    return None

_UNKNOWN_HINT = '未知层 id·调用 list_data 查看清单'

# K-C1 社区口径枚举（inline 校验）与已知 dataset 自动 scope（PT-CB6 D11）
K_C1_COMMUNITY_SCOPES = (174, 154, 118, 193, 130)
_KNOWN_COMMUNITY_SCOPE = {
    'page7_12345_top10': 154,
    'page7_12345_top20': 154,
    'base_174_aggregate_area': 174,
}


def _safe_print(msg, file=None):
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'), file=file)


def _jsonable(value):
    """把 numpy/pandas 标量归一为 JSON 原生类型（MCP 序列化安全）。"""
    if value is None:
        return ''
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value
    item = getattr(value, 'item', None)
    if callable(item):
        try:
            value = item()
        except Exception:
            pass
    if isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


def _gdf_rows(gdf, agg_cols=None):
    """聚合结果转 AI 友好行（NaN 转空串·numpy 标量转原生）。"""
    import pandas as pd

    cols = ['name', 'point_count', 'polarity_index', 'score_mean',
            'domain_top', 'element_top', 'issue_label', 'attribution', 'suggestion',
            'place_name', 'place_name_source', 'poi_names', 'poi_count']
    for c in (agg_cols or []):
        if f'{c}_sum' in gdf.columns and f'{c}_sum' not in cols:
            cols.append(f'{c}_sum')
    cols = [c for c in cols if c in gdf.columns]
    rows = []
    for _, row in gdf.iterrows():
        item = {}
        for c in cols:
            v = row.get(c, '')
            try:
                if pd.isna(v):
                    v = ''
                else:
                    v = _jsonable(v)
            except Exception:
                v = _jsonable(v)
            item[c] = v
        rows.append(item)
    return rows


def _layer_output_fc(gdf, top_n, value_col, max_features=20):
    """layer_output 取 top_n 子集 + value 统一统计值列 → FeatureCollection dict。

    PT-CB15 K2（R1-1）：simplify 阶梯（>200KB 才启动的 0.001-0.05 度简化）**退役**——
    产物改服务端落盘直传（_persist_layer_output），不再穿 MCP payload，无体积约束，
    几何保真优先。根治「转录抽稀」：实测模型手抄内联 geojson 时 2297 顶点只剩 80 个
    （100% 源顶点子集·非幻觉），边界粗糙如随手画。"""
    subset = gdf.head(min(int(top_n), max_features)).copy()
    if value_col in subset.columns:
        subset['value'] = subset[value_col]
    return json.loads(subset.to_json())


# ── PT-CB15 K2/K3（R1-1/R1-4）：layer_output 服务端落盘 + tmp_render 生命周期 ──
# 设计：大宗几何不过模型上下文——工具落盘 tmp_render/*.geojson 并登记临时 dataset，
# 模型只传 dataset_id（render_spec 引用）。「快递贴单号，不让 AI 手搬」。
TMP_RENDER_DIR = os.path.join(REPO, 'DATA', 'Export', 'exports', 'tmp_render')
_TMP_RENDER_TTL_DAYS = 7


def _cleanup_tmp_render():
    """tmp_render 生命周期（R1-4）：删超期文件 + 摘除 manifest 中 file 已失的
    tmp_render_ 登记条目。幂等；单点失败仅 stderr 留痕不阻塞（A9 具体捕获）。"""
    removed_files = 0
    try:
        os.makedirs(TMP_RENDER_DIR, exist_ok=True)
        cutoff = time.time() - _TMP_RENDER_TTL_DAYS * 86400
        for fp in glob.glob(os.path.join(TMP_RENDER_DIR, '*.geojson')):
            try:
                if os.path.getmtime(fp) < cutoff:
                    os.remove(fp)
                    removed_files += 1
            except OSError as exc:
                _safe_print(f'[WARN] tmp_render 文件清理失败（不阻塞）: {fp}: {exc}', file=sys.stderr)
    except OSError as exc:
        _safe_print(f'[WARN] tmp_render 目录异常（不阻塞）: {exc}', file=sys.stderr)
    pruned = 0
    try:
        with open(MANIFEST, 'r', encoding='utf-8') as fh:
            groups = json.load(fh)
        base = os.path.dirname(MANIFEST)
        dirty = False
        for g in groups:
            keep = []
            for it in g.get('items', []):
                if str(it.get('id', '')).startswith('tmp_render_'):
                    rel = str(it.get('file', ''))
                    if not rel or not os.path.isfile(os.path.normpath(os.path.join(base, rel))):
                        pruned += 1
                        dirty = True
                        continue
                keep.append(it)
            g['items'] = keep
        if dirty:
            with open(MANIFEST, 'w', encoding='utf-8', newline='') as fh:
                json.dump(groups, fh, ensure_ascii=False, indent=2)
    except (OSError, ValueError) as exc:
        _safe_print(f'[WARN] tmp_render 登记摘链失败（不阻塞）: {exc}', file=sys.stderr)
    if removed_files or pruned:
        _safe_print(f'[OK] tmp_render 清理：超期文件 {removed_files} 件·失链登记摘除 {pruned} 条',
                    file=sys.stderr)


def _persist_layer_output(tool, fc, value_col):
    """分析结果出图直传：fc 落盘 tmp_render + 登记临时 dataset（renderFields 声明
    value/value_col 防渲染通道字段政策误剔）→ dataset_id。几何全程不过模型上下文。"""
    _cleanup_tmp_render()
    fp = os.path.join(TMP_RENDER_DIR, f'{tool}-{int(time.time() * 1000)}.geojson')
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        json.dump(fc, fh, ensure_ascii=False)
    return _register_tmp_dataset(fp, f'{tool} 分析结果', render_fields=['value', value_col])


def _attach_render_ref(out, tool, fc, value_col):
    """layer_output 统一出口：落盘+登记+挂 render_dataset_id/render_hint。
    落盘失败降级为 render_hint 说明（不拖垮已成功的分析结果·A9）。"""
    try:
        ds_id = _persist_layer_output(tool, fc, value_col)
    except (OSError, ValueError) as exc:
        _safe_print(f'[WARN] {tool} layer_output 落盘失败（分析结果不受影响）: {exc}',
                    file=sys.stderr)
        out['render_hint'] = f'出图落盘失败（{exc}）——可重试或改用 render_file'
        return out
    out['render_dataset_id'] = ds_id
    out['render_hint'] = (f'出图：render_spec(dataset_id={ds_id!r}, value_field={value_col!r})'
                          '——几何服务端直传·勿手抄坐标（手抄必抽稀）')
    return out


@track('MOD_AIQA.F_021', track_args=False)
def list_data(include_demo: bool = False) -> dict:
    """数据说明书：列出可分析点层与边界 preset（字段/类型/usage/数据性质·不含样例值），并附 render 出图能力段（scheme 词表/三档范式/tip 字段/上限）。
    参数：include_demo 兼容保留（清单恒为 resolve 可解析集·F1）。
    限制：分析前必查（layer/boundary 取 id 的唯一入口）；返回带 caliber 口径标；出图前读 render 段或 docs/render-contract.md。"""
    from core.config import PERFORMANCE_DIR
    from core.geo_registry import _POINT_LAYERS, _layer_path, list_point_layers

    point_layers = []
    for p in list_point_layers():
        if not p.get('available'):
            continue
        data_nature = 'real'
        entry = _POINT_LAYERS.get(p.get('id'))
        if entry is not None:
            try:
                path = os.path.normpath(_layer_path(entry))
                data_nature = 'demo' if path.startswith(os.path.normpath(PERFORMANCE_DIR) + os.sep) else 'real'
            except Exception:
                data_nature = 'demo' if str(p.get('level', '')).upper() != 'CHECKUP' else 'real'
        else:
            data_nature = 'demo' if str(p.get('level', '')).upper() != 'CHECKUP' else 'real'
        point_layers.append({
            'id': p.get('id'),
            'label': p.get('label'),
            'level': p.get('level'),
            'fields': p.get('fields', []),
            'dtypes': p.get('dtypes', {}),
            'crs': p.get('crs', 'EPSG:4326'),
            'usage': 'input',
            'data_nature': data_nature,
        })

    try:
        with open(MANIFEST, 'r', encoding='utf-8') as fh:
            groups = json.load(fh)
    except Exception as exc:
        return {'ok': False, 'hint': f'manifest 读取失败: {exc}', 'caliber': CALIBERS['list_data']}

    presets = []
    presets_dir = os.path.dirname(MANIFEST)
    for group in groups:
        for it in group.get('items', []):
            # P1-B：临时 render 产物不进清单（防模型把历史 tmp_render 当本轮分析结果随手引用）
            if str(it.get('id', '')).startswith('tmp_render_'):
                continue
            fname = str(it.get('file', ''))
            # PT-CB14 C2（D-1 销号）：presets 段加 available 过滤（与点层段同纪律）——
            #   manifest 已登记 ≠ 文件已落盘（如 admin_community）·清单恒为 resolve 可解析集（F1 同口径）
            available = bool(fname) and os.path.isfile(os.path.join(presets_dir, fname))
            if not available:
                continue
            geometry = 'unknown'
            if fname.lower().endswith('.geojson'):
                geometry = 'polygon' if it.get('nameField') else 'point'
            presets.append({
                'id': it.get('id'),
                'label': it.get('label'),
                'geometry': geometry,
                'usage': it.get('usage', 'input'),
                'name_field': it.get('nameField'),
                'data_nature': it.get('data_nature', 'real'),
                'available': True,
            })

    return {
        'point_layers': point_layers,
        'presets': presets,
        'count': len(point_layers) + len(presets),
        # PT-CB7 T10：出图能力段（契约权威 = docs/render-contract.md）
        # PT-CB15 K5/K6：paradigm 改写（内联档收窄）+ 边界默认指引（12345 社区级=193 层）
        'render': {
            'schemes': list(SCHEMES),
            'paradigm': ('分析结果出图正道：分析工具 layer_output=True 返回 render_dataset_id'
                         ' → render_spec(dataset_id=...) 引用（几何服务端直传·勿手抄坐标·手抄必抽稀）；'
                         '①inline 仅限模型自造小几何示意（≤60 要素）②dataset_id 引用已注册数据源'
                         '③脚本全量+manifest 注册后走②；把已有文件显示到地图用 render_file；'
                         '详见 docs/render-contract.md'),
            'boundary_guidance': ('12345 社区级分析默认边界=base_community_area（193 含村·SQMC·现行权威）；'
                                  'checkup_cfg_community_xlwj=130 为西陵+伍家岗历史调研范围·显式点名才用；'
                                  'checkup_cfg_community174=去村统计口径（174）'),
            'tip_required_fields': ['name'],
            'tip_recommended_fields': ['point_count', 'polarity_index'],
            'limits': {'inline_features_max': 60, 'zonal_top_n_max': 20},
            'caliber_lite_required': ['usage', 'data_nature'],
        },
        'caliber': CALIBERS['list_data'],
    }


@track('MOD_AIQA.F_022', track_args=False)
def rag_query(query: str, k: int = 5, synthesize: bool = False) -> dict:
    """带来源知识检索：本地治理知识库 Top-K 素材+维度分布（非联网·非空间分析）。
    参数：query 必填；k 1-10；synthesize=True 时 v1 诚实降级 deferred_v2（附宿主综合指引）。
    限制：索引未建时报提示（py tools/rag_index.py --build）；适用叙述/方法/对比问答。
    路由分工（A2）：精确名词/口径数字优先 kb_facts（注册表直查）；叙述/方法/对比用 rag_query。
    B3：顶层 suppressed_count（被 superseded 过滤条数）；条目不对称治理标注（历史叙述类带 caliber_note·现行零标签）。"""
    if not query or not str(query).strip():
        return {'ok': False, 'hint': 'query 不能为空', 'caliber': CALIBERS['rag_query']}

    k = max(1, min(int(k), 10))
    import time as _time
    _t0 = _time.perf_counter()
    try:
        from tools.rag_index import search
        r = search(str(query), k)
    except Exception as exc:
        return {'ok': False, 'hint': f'检索失败: {exc}', 'caliber': CALIBERS['rag_query']}

    if not r.get('ok'):
        return {
            'ok': False,
            'hint': '索引未构建：py tools/rag_index.py --build',
            'error': r.get('error', ''),
            'caliber': CALIBERS['rag_query'],
        }

    dim_counts = {}
    for res in r.get('results', []):
        d = res.get('data_dim', '社区')
        dim_counts[d] = dim_counts.get(d, 0) + 1
    elapsed_ms = round((_time.perf_counter() - _t0) * 1000, 1)
    top_dim = max(dim_counts, key=dim_counts.get) if dim_counts else ''

    # A2 路由改道（窄面）：命中口径类 chunk（type=fact 且 source 指向口径注册表）时附 caliber_ref
    caliber_hit = next((res for res in r.get('results', [])
                        if res.get('type') == 'fact'
                        and any(k in res.get('source', '') for k in ('K-C', 'K-G', 'caliber'))), None)
    if caliber_hit:
        _safe_print(f'[A2] rag_query caliber_ref emitted: {caliber_hit.get("topic", "")[:40]}',
                    file=sys.stderr)

    # H1 followup_cue（确定性派生·零 LLM·三张小表 ai_qa/rag_cues.json）
    followup_cues = _derive_followup_cues(r.get('results', []), top_dim)

    # PT-CB9R A-2 信号字段族（确定性·零 LLM·零二次检索——告知不足·不替外脑补救）
    signals = _derive_retrieval_signals(r.get('results', []), k, top_dim, dim_counts)

    out = {
        'ok': True,
        'results': r.get('results', []),
        'count': r.get('count', 0),
        'dim_counts': dim_counts,
        'top_dim': top_dim,
        'elapsed_ms': elapsed_ms,
        'synthesize': False,
        'caliber': CALIBERS['rag_query'],
        'suppressed_count': r.get('suppressed_count', 0),   # PT-CB9R-B3：search 过滤处观测透传
    }
    out.update(signals)
    if caliber_hit:
        out['caliber_ref'] = {
            'kind': 'caliber_class',
            'suggest': 'kb_facts',
            'topic': caliber_hit.get('topic', ''),
        }
    elif signals['confidence'] == '低':
        # A2 改道承载：低置信 → 结构化建议换 kb_facts（精确名词/口径数字走注册表直查）
        out['caliber_ref'] = {
            'kind': 'low_confidence',
            'suggest': 'kb_facts',
            'topic': str(query)[:40],
        }
    if followup_cues:
        out['followup_cues'] = followup_cues
    if synthesize:
        out['synthesize'] = 'deferred_v2'
        out['guidance'] = ('v1 未接后端综合：请宿主基于以上带来源素材综合，'
                           '注明来源与维度；避免把宏观倾向说成微观结论')
    return out


@track('MOD_AIQA.F_023', track_args=False)
def kb_facts(query: str = '', keyword: str = '', topic: str = '',
             limit: int = 5) -> dict:
    """行业事实卡：确定性查询（关键词精确命中·非向量·CB-22f D5 兜底）。
    参数：query/keyword 至少给一；topic 可选（metric/issue/project/identity 等）；limit 1-20。
    限制：固定 city=宜昌；命中按 keywords/region 反查加权。
    路由分工（A2）：精确名词/口径数字优先本工具（注册表直查·零向量碰运气）；叙述/方法/对比用 rag_query。
    B3：条目不对称治理标注（X-01 关联历史叙述类带 caliber_note·现行零标签·确定性零 LLM）。"""
    limit = max(1, min(int(limit), 20))
    try:
        from ai_qa.outlet_kb.urban_renewal_knowledge import query_knowledge_base
        facts = query_knowledge_base(query=query or '', city='宜昌',
                                     topic=topic or None, keyword=keyword or None,
                                     limit=limit)
    except Exception as exc:
        return {'ok': False, 'hint': f'kb_facts 失败: {exc}',
                'facts': [], 'count': 0, 'caliber': CALIBERS['kb_facts']}
    # PT-CB9R-B3：不对称治理标注（现行零标签·X-01 关联历史叙述类带 caliber_note·确定性零 LLM）
    #   kb_facts 条目=事实卡·判定走 _LINEAGE_MAP 谱系（直接命中/链式命中·当前语料均零标签·机制就位）。
    try:
        from tools.rag_index import _history_note, _LINEAGE_MAP
        for _f in facts:
            _src = f"ai_qa/outlet_kb/urban_renewal_knowledge.py#{_f.get('id')}"
            _note = _history_note(_src, _LINEAGE_MAP.get(_src))
            if _note:
                _f['caliber_note'] = _note
    except Exception as _exc:
        _safe_print(f'[WARN] kb_facts 治理标注降级（非阻塞）: {type(_exc).__name__}',
                    file=sys.stderr)
    # PT-CB9R A-2 信号字段族（kb_facts 侧=确定性关键词命中语义·无向量分数）：
    #   有命中=高置信（精确匹配即答案）；零命中=低置信+thin+retry_cue（改 rag_query 叙述路）。
    out = {'facts': facts, 'count': len(facts), 'caliber': CALIBERS['kb_facts']}
    if facts:
        out['confidence'] = '高'
        out['thin_result'] = False
    else:
        out['confidence'] = '低'
        out['thin_result'] = True
        out['retry_cue'] = ['事实卡未命中该精确词——叙述/方法/对比类问题建议改 rag_query']
        out['caliber_ref'] = {'kind': 'no_hit', 'suggest': 'rag_query',
                              'topic': (keyword or query or topic)[:40]}
    return out


@track('MOD_AIQA.F_024', track_args=False)
def outlet_card(question: str = '', result: dict = None, diagnose: dict = None) -> dict:
    """行业出口卡：确定性组装的对话级行业接口卡（零 LLM）。
    参数：question 原始问题；result 分析结果对象；diagnose 诊断对象（scale/domain_lens/outlet）；字段均可缺。
    限制：组装失败返回 ok=False+hint；不产新数据。"""
    try:
        from ai_qa.outlet_kb.build_outlet_schema import build_outlet_schema
        cards = build_outlet_schema(diagnose or {}, result or {}, question or '')
    except Exception as exc:
        return {'ok': False, 'hint': f'outlet_card 组装失败: {exc}', 'cards': [],
                'card': None, 'caliber': CALIBERS['outlet_card']}
    return {'cards': cards, 'card': cards[0] if cards else None,
            'caliber': CALIBERS['outlet_card']}


@track('MOD_AIQA.F_025', track_args=False)
def zonal_stats(boundary: str, layer: str = 'yichang_l2_t1',
                agg_cols: list = None, top_n: int = 10,
                layer_output: bool = False,
                sort_by: str = 'polarity_index') -> dict:
    """单元聚合：情绪点按边界单元统计（宏观/中观结论）。
    参数：boundary 必填（先 list_data）；layer 默认 yichang_l2_t1；sort_by=point_count|polarity_index|score_mean；top_n 1-20；layer_output=True 落盘登记临时 dataset 返回 render_dataset_id（几何服务端直传·render_spec 以 dataset_id 引用·PT-CB15 K2）。
    限制：首次调用 geopandas 冷启动约 10-20s；rows 硬顶 20。"""
    try:
        from core.geo_registry import resolve_boundary, resolve_points
        from core.spatial_analysis import aggregate_by_polygons

        _g = _guard_check('zonal_stats', {'boundary': boundary}, CALIBERS['zonal_stats'])
        if _g:
            return _g
        points = resolve_points(layer)
        polys = resolve_boundary(boundary)
        cols = agg_cols or (['score'] if 'score' in points.columns else [])
        merged = aggregate_by_polygons(points, polys, agg_cols=cols,
                                       polygon_name_col='name')
        _SORT_ALLOWED = ('point_count', 'polarity_index', 'score_mean')
        if sort_by not in _SORT_ALLOWED:
            return {'ok': False, 'hint': f'sort_by 非法: {sort_by!r}（可选 {_SORT_ALLOWED}）',
                    'caliber': CALIBERS['zonal_stats']}
        if sort_by == 'point_count':
            sort_col = 'point_count'
        elif sort_by == 'score_mean':
            sort_col = 'score_mean' if 'score_mean' in merged.columns else (
                'polarity_index' if 'polarity_index' in merged.columns else 'point_count')
        else:
            sort_col = 'polarity_index' if 'polarity_index' in merged.columns else next(
                (f'{c}_sum' for c in cols if f'{c}_sum' in merged.columns), 'point_count')
        merged = merged.sort_values(
            by=sort_col,
            key=(lambda s: s.abs() if sort_col == 'polarity_index' else s),
            ascending=False, kind='stable')
        row_count = int(len(merged))
        top_n = max(1, min(int(top_n), 20))
        top_rows = merged.head(top_n)
        rows = _gdf_rows(top_rows, cols)
        out_fc = _layer_output_fc(merged, top_n, sort_col) if layer_output else None
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': CALIBERS['zonal_stats']}
    except Exception as exc:
        return {'ok': False, 'hint': f'zonal_stats 失败: {exc}', 'caliber': CALIBERS['zonal_stats']}

    out = {'rows': rows, 'row_count': row_count, 'truncated': row_count > len(rows),
           'caliber': CALIBERS['zonal_stats']}
    if layer_output:
        _attach_render_ref(out, 'zonal_stats', out_fc, sort_col)
    return out


@track('MOD_AIQA.F_026', track_args=False)
def buffer(center: str, radius_m: int = 500, layer: str = 'yichang_l2_t1',
           dissolve: bool = True) -> dict:
    """缓冲影响圈：设施周边半径范围 + 圈内情绪点计数。
    参数：center 必填（先 list_data）；radius_m 50-3000；layer 计数点层；dissolve=True 合并覆盖区。
    限制：几何过大（>5 要素或 >100KB）省略 buffer_fc 改用前端渲染。"""
    try:
        from core.buffer_analysis import create_buffer
        from core.geo_registry import resolve_boundary, resolve_points
        from shapely.geometry import shape

        radius_m = max(50, min(int(radius_m), 3000))
        _g = _guard_check('buffer', {'center': center}, CALIBERS['buffer'])
        if _g:
            return _g
        center_gdf = resolve_boundary(center)
        fc, area_km2 = create_buffer(center_gdf.__geo_interface__, radius_m, dissolve)

        point_count = 0
        if layer:
            pts = resolve_points(layer)
            polys = [shape(f['geometry']) for f in fc.get('features', [])]
            for geom in pts.geometry:
                if any(poly.contains(geom) for poly in polys):
                    point_count += 1
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': CALIBERS['buffer']}
    except Exception as exc:
        return {'ok': False, 'hint': f'buffer 失败: {exc}', 'caliber': CALIBERS['buffer']}

    fc_json = json.dumps(fc, ensure_ascii=False)
    include_fc = len(fc.get('features', [])) <= 5 and len(fc_json) <= 100000
    out = {'area_km2': float(area_km2), 'point_count': int(point_count),
           'caliber': CALIBERS['buffer']}
    if include_fc:
        out['buffer_fc'] = fc
    else:
        out['fc_omitted'] = True
        out['hint'] = '缓冲几何较大·请用 EMC 前端渲染 v2'
    return out


@track('MOD_AIQA.F_027', track_args=False)
def rank(by: str = 'worst', layer: str = 'yichang_l2_t1',
         boundary: str = '', top_n: int = 5,
         layer_output: bool = False,
         sort_by: str = 'polarity_index') -> dict:
    """排序评价：按极性指数找最差/最好 Top-N 单元（先聚合再排）。
    参数：boundary 必填；by=worst|best；sort_by=point_count|polarity_index|score_mean；top_n 1-20；layer_output=True 落盘登记临时 dataset 返回 render_dataset_id（几何服务端直传·PT-CB15 K2）。
    限制：首次调用冷启动同 zonal_stats；层无 polarity_index 时报提示。"""
    if not boundary:
        return {'ok': False, 'hint': 'rank 需 boundary（先 zonal 聚合再排）',
                'caliber': CALIBERS['rank']}
    try:
        from core.geo_registry import resolve_boundary, resolve_points
        from core.spatial_analysis import aggregate_by_polygons

        _g = _guard_check('rank', {'boundary': boundary}, CALIBERS['rank'])
        if _g:
            return _g
        points = resolve_points(layer)
        polys = resolve_boundary(boundary)
        cols = ['score'] if 'score' in points.columns else []
        merged = aggregate_by_polygons(points, polys, agg_cols=cols,
                                       polygon_name_col='name')
        _SORT_ALLOWED = ('point_count', 'polarity_index', 'score_mean')
        if sort_by not in _SORT_ALLOWED:
            return {'ok': False, 'hint': f'sort_by 非法: {sort_by!r}（可选 {_SORT_ALLOWED}）',
                    'caliber': CALIBERS['rank']}
        if sort_by == 'polarity_index' and 'polarity_index' not in merged.columns:
            return {'ok': False, 'hint': 'rank 需层含 polarity_index（先 zonal_stats 聚合）',
                    'caliber': CALIBERS['rank']}
        if sort_by == 'point_count':
            merged = merged.sort_values('point_count', ascending=False, kind='stable')
        elif sort_by == 'score_mean':
            merged = merged.sort_values('score_mean', ascending=False, kind='stable')
        else:
            by = (by or 'worst').lower()
            ascending = (by == 'worst')
            merged = merged.sort_values('polarity_index', ascending=ascending, kind='stable')
        sort_col = 'point_count' if sort_by == 'point_count' else ('score_mean' if sort_by == 'score_mean' else 'polarity_index')
        row_count = int(len(merged))
        top_n = max(1, min(int(top_n), 20))
        top_rows = merged.head(top_n)
        rows = _gdf_rows(top_rows, cols)
        out_fc = _layer_output_fc(merged, top_n, sort_col) if layer_output else None
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': CALIBERS['rank']}
    except Exception as exc:
        return {'ok': False, 'hint': f'rank 失败: {exc}', 'caliber': CALIBERS['rank']}

    out = {'rows': rows, 'row_count': row_count, 'caliber': CALIBERS['rank']}
    if layer_output:
        _attach_render_ref(out, 'rank', out_fc, sort_col)
    return out


@track('MOD_AIQA.F_033', track_args=False)
def grid_aggregate(layer: str = 'yichang_l2_t1', cell_size: int = 800,
                   value_col: str = '', boundary: str = '',
                   top_n: int = 10, layer_output: bool = False) -> dict:
    """方格网空间聚合：点层按固定边长方格统计（中观·规则格）。
    参数：cell_size 格边长米（默认 800·语义同 Grid dialog cellSize=格边长非带宽）；value_col 空=只计数·给值则同时算 _sum/_mean；boundary 可选 preset 裁剪；top_n 1-20；layer_output=True 落盘登记临时 dataset 返回 render_dataset_id（几何服务端直传·PT-CB15 K2）。
    限制：方格≠行政单元——社区级结论用 zonal_stats；geopandas 冷启动 10-20s。"""
    caliber = {'scale': '中观（规则方格·边长 cell_size m）',
               'semantics': '方格网聚合强度（规则格·非行政单元）',
               'limits': '方格≠社区/行政区——勿把格结论说成社区结论；行政单元归因用 zonal_stats',
               'refs': ['K-C1']}
    try:
        from core.geo_registry import resolve_boundary, resolve_points
        from core.spatial_analysis import create_square_grid

        points = resolve_points(layer)
        if value_col and value_col not in points.columns:
            return {'ok': False, 'hint': f'value_col 不存在: {value_col!r}（该层可用列: {list(points.columns)}）',
                    'caliber': caliber}
        if boundary:
            _g = _guard_check('grid_aggregate', {'boundary': boundary}, caliber)
            if _g:
                return _g
            import geopandas as gpd
            polys = resolve_boundary(boundary)
            points = gpd.clip(points, polys.unary_union)
        merged = create_square_grid(points, cell_size,
                                    agg_cols=([value_col] if value_col else []))
        row_count = int(len(merged))
        if row_count == 0 or 'point_count' not in merged.columns:
            return {'ok': False,
                    'hint': '聚合结果为空（点层为空或 boundary 裁剪后零点）——请换 boundary 或检查点层',
                    'caliber': caliber}
        sort_col = (f'{value_col}_mean' if value_col and f'{value_col}_mean' in merged.columns
                    else 'point_count')
        merged = merged.sort_values(sort_col, ascending=False, kind='stable')
        top_n = max(1, min(int(top_n), 20))
        rows = _gdf_rows(merged.head(top_n), [value_col] if value_col else None)
        out_fc = _layer_output_fc(merged, top_n, sort_col) if layer_output else None
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': caliber}
    except Exception as exc:
        return {'ok': False, 'hint': f'grid_aggregate 失败: {exc}', 'caliber': caliber}

    stats = {'total_cells': row_count,
             'nonzero_cells': int((merged['point_count'] > 0).sum()),
             'max_count': int(merged['point_count'].max())}
    out = {'rows': rows, 'stats': stats, 'row_count': row_count,
           'truncated': row_count > len(rows), 'caliber': caliber}
    if layer_output:
        _attach_render_ref(out, 'grid_aggregate', out_fc, sort_col)
    return out


@track('MOD_AIQA.F_034', track_args=False)
def compare_regions(boundaries: list, layer: str = 'yichang_l2_t1',
                    agg_cols: list = None) -> dict:
    """区域对比：≥2 个 boundary preset 同口径并排聚合+差异方向（谁更高/差多少/几倍）。
    参数：boundaries 必填 list（≥2·≤5·超5截断标注）；agg_cols 默认 ['score']（沿 zonal_stats）；layer 默认 yichang_l2_t1。
    限制：跨 layer/agg_cols 的对比无意义；单区归因用 zonal_stats。"""
    caliber = {'scale': '宏观/中观（区域对比）',
               'semantics': '≥2 区域同口径并排+差异方向',
               'limits': '区数 2-5；同 layer 同 agg_cols 才可比；单区归因用 zonal_stats',
               'refs': ['K-C1']}
    if isinstance(boundaries, str):
        items = [s.strip() for s in boundaries.replace('|', ',').split(',') if s.strip()]
    elif isinstance(boundaries, (list, tuple)):
        items = [str(b).strip() for b in boundaries if str(b).strip()]
    else:
        return {'ok': False,
                'hint': 'boundaries 需为 preset id 列表（≥2 区·对齐契约 failure_modes）',
                'caliber': caliber}
    truncated = len(items) > 5
    items = items[:5]
    if len(items) < 2:
        return {'ok': False,
                'hint': 'compare_regions 需 ≥2 区（对齐契约 failure_modes·boundaries 为 list 或 "a|b" 分隔串）',
                'caliber': caliber}
    try:
        import pandas as pd
        from core.geo_registry import list_boundaries, resolve_boundary, resolve_points
        from core.spatial_analysis import aggregate_by_polygons

        label_map = {}
        try:
            label_map = {b.get('id'): (b.get('label') or b.get('id')) for b in list_boundaries()}
        except Exception:
            pass
        frames = []
        for b in items:
            _g = _guard_check('compare_regions', {'boundaries': b}, caliber)
            if _g:
                return _g
            polys = resolve_boundary(b)
            g = polys[['geometry']].dissolve()
            g['name'] = label_map.get(b, b)
            frames.append(g)
        combined = pd.concat(frames, ignore_index=True)
        points = resolve_points(layer)
        cols = agg_cols if agg_cols else (['score'] if 'score' in points.columns else [])
        merged = aggregate_by_polygons(points, combined, agg_cols=cols,
                                       polygon_name_col='name')
        if len(merged) == 0:
            return {'ok': False,
                    'hint': '聚合结果为空（点层为空或所选区内零点）——请换 layer 或检查区内点分布',
                    'caliber': caliber}
        rows = _gdf_rows(merged, cols)
        diff = {}
        metric_cols = ['point_count']
        for c in ('polarity_index', 'score_mean', *(f'{c}_mean' for c in cols)):
            if c in merged.columns:
                metric_cols.append(c)
        for m in metric_cols:
            key = merged[m].abs() if m == 'polarity_index' else merged[m]
            max_i, min_i = key.idxmax(), key.idxmin()
            max_v, min_v = float(merged.at[max_i, m]), float(merged.at[min_i, m])
            diff[m] = {
                'max_region': merged.at[max_i, 'name'],
                'min_region': merged.at[min_i, 'name'],
                'gap': round(max_v - min_v, 4),
                'ratio': round(max_v / min_v, 3) if min_v > 0 else None,
            }
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': caliber}
    except Exception as exc:
        return {'ok': False, 'hint': f'compare_regions 失败: {exc}', 'caliber': caliber}

    return {'regions': rows, 'count': len(rows), 'truncated': truncated,
            'diff': diff, 'caliber': caliber}


@track('MOD_AIQA.F_035', track_args=False)
def hotspot_analysis(layer: str = 'yichang_l2_t1', value_col: str = 'score',
                     invert: bool = True, threshold: float = 1.96,
                     soft_threshold: float = 1.0, top_n: int = 10,
                     layer_output: bool = False) -> dict:
    """显著聚集识别：逐点 Gi* Z-score 五档分类（hot/tend_hot/ns/tend_cold/cold）。
    参数：value_col 默认 score；invert=True 负面为热（契约默认）；threshold 1.96=95%（1.65=90/2.58=99）；soft_threshold 1.0=倾向档；top_n 1-20。
    限制：显著=统计显著性非业务重要性；连续密度面用 density；score 为 U 形离散分布·ns 占多属正常（P1 修正口径）。"""
    caliber = {'scale': '微观（逐点 Gi*）',
               'semantics': '逐点 Gi* Z-score 五档显著聚集分类',
               'limits': '显著=统计显著性非业务重要性；连续热度分布用 density；threshold 对应置信度（1.65→90%/1.96→95%/2.58→99%）',
               'refs': ['K-C1']}
    try:
        from core.geo_registry import resolve_points
        from core.spatial_analysis import hot_spot_analysis

        points = resolve_points(layer)
        if value_col not in points.columns:
            import pandas as pd
            try:
                numeric = [c for c in points.columns
                           if c != 'geometry' and pd.api.types.is_numeric_dtype(points[c])]
            except Exception:
                numeric = [c for c in points.columns if c != 'geometry']
            return {'ok': False,
                    'hint': f'value_col 不存在: {value_col!r}（可用数值列: {numeric}；连续热度分布请用 density·勿混用）',
                    'caliber': caliber}
        result = hot_spot_analysis(points, value_col=value_col, invert=invert,
                                   threshold=threshold, soft_threshold=soft_threshold)
        tiers = ('hot', 'tend_hot', 'ns', 'tend_cold', 'cold')
        counts = {t: int((result['hotspot_tier'] == t).sum()) for t in tiers}
        tier_rank = {'hot': 0, 'cold': 1, 'tend_hot': 2, 'tend_cold': 3, 'ns': 4}
        result = result.assign(_tier_rank=result['hotspot_tier'].map(tier_rank),
                               _abs_z=result['Gi_Z'].abs())
        ordered = result.sort_values(['_tier_rank', '_abs_z'],
                                     ascending=[True, False], kind='stable')
        row_count = int(len(ordered))
        top_n = max(1, min(int(top_n), 20))
        row_cols = [c for c in ('place_name', 'Gi_Z', 'Gi_P', 'hotspot_tier')
                    if c in ordered.columns]
        rows = [{c: _jsonable(row[c]) for c in row_cols}
                for _, row in ordered.head(top_n).iterrows()]
        out_fc = _layer_output_fc(result, top_n, 'Gi_Z') if layer_output else None
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': caliber}
    except Exception as exc:
        return {'ok': False, 'hint': f'hotspot_analysis 失败: {exc}', 'caliber': caliber}

    out = {'counts': counts, 'rows': rows, 'row_count': row_count,
           'truncated': row_count > len(rows), 'caliber': caliber}
    if layer_output:
        _attach_render_ref(out, 'hotspot_analysis', out_fc, 'Gi_Z')
    return out


@track('MOD_AIQA.F_037', track_args=False)
def area_stats(boundary: str, group_by: str = '', top_n: int = 10,
               layer_output: bool = False) -> dict:
    """面积占比统计：面层按要素/分组字段算面积与占比（结构量化·非情绪归因）。
    参数：boundary 必填 preset id（先 list_data）；group_by 给出则按该字段 dissolve 分组汇总；top_n 1-20；layer_output=True 落盘登记临时 dataset 返回 render_dataset_id（几何服务端直传·PT-CB15 K2）。
    限制：只算面积结构——情绪结论用 zonal_stats/rank；投影面积与椭球面积差异 <1% 级。"""
    caliber = {'scale': '宏观/中观（面积结构）',
               'semantics': '面积与占比统计（结构量化）',
               'limits': '非情绪归因——情绪结论用 zonal_stats/rank；投影差异 <1%',
               'refs': ['K-C1']}
    try:
        from core.geo_registry import resolve_boundary

        _g = _guard_check('area_stats', {'boundary': boundary}, caliber)
        if _g:
            return _g
        g = resolve_boundary(boundary)
        if group_by and group_by not in g.columns:
            usable = [c for c in g.columns if c != 'geometry']
            return {'ok': False,
                    'hint': f'group_by 字段不存在: {group_by!r}（该层可用列: {usable}）',
                    'caliber': caliber}
        if g.crs is None:
            g = g.set_crs('EPSG:4326')
        # 面积：投影到米制 CRS 再算（照抄 create_square_grid 的 target_crs=EPSG:4546·宜昌 CM 111E）
        gm = g.to_crs('EPSG:4546')
        if group_by:
            gm = gm.dissolve(by=group_by, as_index=False)
        gm['area_km2'] = gm.geometry.area / 1e6
        total_km2 = float(gm['area_km2'].sum())
        if total_km2 <= 0:
            return {'ok': False, 'hint': '面积合计为 0——几何为空或异常，无法算占比',
                    'caliber': caliber}
        gm['share_pct'] = (gm['area_km2'] / total_km2 * 100).round(2)
        gm['area_km2'] = gm['area_km2'].round(4)
        gm = gm.sort_values('area_km2', ascending=False, kind='stable')
        row_count = int(len(gm))
        top_n = max(1, min(int(top_n), 20))
        # rows：area_km2/share_pct 不在 _gdf_rows 固定列白名单——沿 hotspot 先例逐格 _jsonable
        label_col = group_by if group_by else ('name' if 'name' in gm.columns else None)
        rows = []
        for _, row in gm.head(top_n).iterrows():
            item = {}
            if label_col:
                item[label_col] = _jsonable(row.get(label_col, ''))
            item['area_km2'] = _jsonable(row['area_km2'])
            item['share_pct'] = _jsonable(row['share_pct'])
            rows.append(item)
        out_fc = (_layer_output_fc(gm.to_crs('EPSG:4326'), top_n, 'area_km2')
                  if layer_output else None)
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': caliber}
    except Exception as exc:
        return {'ok': False, 'hint': f'area_stats 失败: {exc}', 'caliber': caliber}

    out = {'rows': rows, 'total_km2': round(total_km2, 4), 'row_count': row_count,
           'truncated': row_count > len(rows), 'caliber': caliber}
    if layer_output:
        _attach_render_ref(out, 'area_stats', out_fc, 'area_km2')
    return out


@track('MOD_AIQA.F_036', track_args=False)
def nearest_analysis(layer: str = 'yichang_l2_t1', target: str = '',
                     k: int = 1, top_n: int = 10, layer_output: bool = False) -> dict:
    """最近邻锚定：每个锚点找目标层最近的 k 个（微观·POI 锚定）。
    参数：target 必填（preset_id：先试点层、解析失败再作面层；契约 required_slots）；k 默认 1·cap 5；top_n 1-20；layer_output=True 增连线 geojson（微几何 ≤40 顶点·内联例外·PT-CB15 K2 注记）。
    限制：邻近≠因果；距离为 EPSG:4546 投影平面距离（<1% 级误差·照 area_stats 先例）。"""
    caliber = {'scale': '微观（POI 锚定）',
               'semantics': '最近邻配对（锚点×目标）+投影米距',
               'limits': '邻近≠因果；距离为投影平面距离（<1% 级误差）；k≤5 cap',
               'refs': ['K-C1']}
    if not target:
        return {'ok': False, 'hint': 'nearest_analysis 需 target（preset_id·契约 required_slots）',
                'caliber': caliber}
    k = max(1, min(int(k), 5))
    try:
        import numpy as np
        from core.geo_registry import resolve_boundary, resolve_points

        anchor = resolve_points(layer)
        if anchor is None or len(anchor) == 0:
            return {'ok': False,
                    'hint': '锚点层为空——nearest 无配对可算（请检查 layer 或换点层）',
                    'caliber': caliber}
        try:
            targets = resolve_points(target)
        except Exception:
            targets = None
        if targets is None:
            _g = _guard_check('nearest_analysis', {'target': target}, caliber)
            if _g:
                return _g
            targets = resolve_boundary(target)
        if len(targets) == 0:
            return {'ok': False,
                    'hint': '目标层为空——nearest 无配对可算（请换 target）',
                    'caliber': caliber}

        def _to_metric(gdf):
            g = gdf if gdf.crs is not None else gdf.set_crs('EPSG:4326')
            g = g.to_crs('EPSG:4546')
            # PT-CB11 P1 修复（zcode 协同顺手修）：面/线目标 .geometry.x 只支持点——
            # 非 Point 几何先取 representative_point()（落在面内·比 centroid 稳·防凹多边形外心）
            if not g.geometry.geom_type.isin(('Point',)).all():
                g = g.copy()
                g.geometry = g.geometry.apply(
                    lambda gm: gm if gm.geom_type == 'Point' else gm.representative_point())
            return g

        # PT-CB11 P2 守卫：距离矩阵 O(n_a×n_t)——超预算语义化拒绝（防 GB 级中间矩阵拖垮宿主）
        _PAIR_BUDGET = 5 * 10 ** 7
        if len(anchor) * len(targets) > _PAIR_BUDGET:
            return {'ok': False,
                    'hint': (f'配对规模超预算: {len(anchor)}×{len(targets)}'
                             f'>{_PAIR_BUDGET}——请先用 grid_aggregate/zonal_stats 降密度，'
                             '或换更小的 target 层'),
                    'caliber': caliber}

        a = _to_metric(anchor)
        t = _to_metric(targets)
        ax = np.column_stack([a.geometry.x.values, a.geometry.y.values])
        tx = np.column_stack([t.geometry.x.values, t.geometry.y.values])
        # 投影平面距离矩阵 n_a×n_t（配对预算 _PAIR_BUDGET 内·中间 (n,m,2) float64）。
        # 派发单 backing 的 sjoin_nearest 为 k=1 特例；此处统一矩阵法覆盖 k≤5，语义一致。
        dist = np.sqrt(((ax[:, None, :] - tx[None, :, :]) ** 2).sum(axis=-1))
        k_eff = min(k, len(t))
        take = np.argsort(dist, axis=1, kind='stable')[:, :k_eff]

        anchor_name = 'place_name' if 'place_name' in a.columns else None
        target_name = ('name' if 'name' in t.columns
                       else 'place_name' if 'place_name' in t.columns else None)
        anchor_orig = anchor.reset_index(drop=True)
        target_orig = t.to_crs('EPSG:4326').reset_index(drop=True)
        pairs = []
        lines = []
        for i in range(len(a)):
            for j in take[i]:
                item = {'anchor': (_jsonable(anchor_orig.at[i, anchor_name])
                                   if anchor_name else f'anchor_{i}'),
                        'target': (_jsonable(target_orig.at[j, target_name])
                                   if target_name else f'target_{j}'),
                        'dist_m': round(float(dist[i, j]), 2)}
                pairs.append(item)
                from shapely.geometry import LineString
                lines.append({'type': 'Feature',
                              'geometry': LineString([anchor_orig.geometry.iat[i],
                                                      target_orig.geometry.iat[j]]).__geo_interface__,
                              'properties': item})
        pairs.sort(key=lambda p: p['dist_m'])
        all_dists = [p['dist_m'] for p in pairs]
        top_n = max(1, min(int(top_n), 20))
        shown = pairs[:top_n]
        out_geojson = ({'type': 'FeatureCollection', 'features': lines[:top_n]}
                       if layer_output else None)
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': caliber}
    except Exception as exc:
        return {'ok': False, 'hint': f'nearest_analysis 失败: {exc}', 'caliber': caliber}

    out = {'pairs': shown,
           'stats': {'mean_dist': round(sum(all_dists) / len(all_dists), 2) if all_dists else None,
                     'max_dist': round(max(all_dists), 2) if all_dists else None,
                     'pair_count': len(pairs)},
           'row_count': len(pairs), 'truncated': len(pairs) > len(shown),
           'caliber': caliber}
    if layer_output:
        out['geojson'] = out_geojson
    return out


@track('MOD_AIQA.F_038', track_args=False)
def overlay_analysis(layer_a: str, layer_b: str, how: str = 'intersection',
                     top_n: int = 10, layer_output: bool = False) -> dict:
    """叠置交叉：两个面层做交集/并集/差集/对称差（面∩面正解）。
    参数：layer_a/layer_b 必填 preset id（先 list_data）；how=intersection|union|difference|symmetric（默认 intersection·契约同）；top_n 1-20；layer_output=True 落盘登记临时 dataset 返回 render_dataset_id（几何服务端直传·PT-CB15 K2）。
    限制：面∩面运算——点层裁剪勿用（无意义·取点用 zonal/clip）；结果要素可能 explode 多块（按面积降序 top）。"""
    caliber = {'scale': '中观（跨图层面）',
               'semantics': '两图层面叠置交叉+面积统计',
               'limits': '面∩面运算——点层裁剪勿用（无意义）；结果要素可能 explode 多块（按面积降序 top）',
               'refs': ['K-C1']}
    _HOW_ALLOWED = ('intersection', 'union', 'difference', 'symmetric')
    if how not in _HOW_ALLOWED:
        return {'ok': False, 'hint': f'how 非法: {how!r}（可选 {_HOW_ALLOWED}）',
                'caliber': caliber}
    if not layer_a or not layer_b:
        return {'ok': False, 'hint': 'overlay_analysis 需 layer_a 与 layer_b（两个面层 preset id）',
                'caliber': caliber}
    try:
        import geopandas as gpd
        from core.geo_registry import resolve_boundary

        _ga = _guard_check('overlay_analysis', {'layer_a': layer_a, 'layer_b': layer_b}, caliber)
        if _ga:
            return _ga
        a_raw = resolve_boundary(layer_a)
        b_raw = resolve_boundary(layer_b)
        if len(a_raw) == 0 or len(b_raw) == 0:
            return {'ok': False,
                    'hint': '叠置输入为空——layer_a/layer_b 无要素（请换面层）',
                    'caliber': caliber}
        # 只带 geometry+规范名进 overlay（防同名列后缀冲突·输出稳定 name_a/name_b）
        a = a_raw[['geometry']].copy()
        a['name_a'] = (a_raw['name'] if 'name' in a_raw.columns
                       else ('a_1' if len(a_raw) == 1 else 'a'))
        b = b_raw[['geometry']].copy()
        b['name_b'] = (b_raw['name'] if 'name' in b_raw.columns
                       else ('b_1' if len(b_raw) == 1 else 'b'))
        result = gpd.overlay(a, b, how=how)
        if len(result) == 0:
            return {'ok': False,
                    'hint': '叠置结果为空——两图层无交集/差集为空（请换 how 或检查图层范围）',
                    'caliber': caliber}
        if result.crs is None:
            result = result.set_crs('EPSG:4326')
        rm = result.to_crs('EPSG:4546')
        result['area_km2'] = (rm.geometry.area / 1e6).round(4)
        result = result.sort_values('area_km2', ascending=False, kind='stable')
        row_count = int(len(result))
        top_n = max(1, min(int(top_n), 20))
        rows = [{'name_a': _jsonable(r['name_a']) if 'name_a' in result.columns else '',
                 'name_b': _jsonable(r['name_b']) if 'name_b' in result.columns else '',
                 'area_km2': _jsonable(r['area_km2'])}
                for _, r in result.head(top_n).iterrows()]
        out_fc = _layer_output_fc(result, top_n, 'area_km2') if layer_output else None
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': caliber}
    except Exception as exc:
        return {'ok': False, 'hint': f'overlay_analysis 失败: {exc}', 'caliber': caliber}

    out = {'rows': rows, 'result_count': row_count,
           'stats': {'total_area_km2': round(float(result['area_km2'].sum()), 4)},
           'truncated': row_count > len(rows), 'caliber': caliber}
    if layer_output:
        _attach_render_ref(out, 'overlay_analysis', out_fc, 'area_km2')
    return out


# ── PT-CB11 P2③ · guard 迁 server 侧（_reject_analysis_output 泛化） ──────────

# PT-CB12 T1 · 全量接线完成：9 件带面输入工具入口统一调 _guard_check（本表=单一守卫通路）。
#   _audit_input_surfaces 启动时核对声明参数 vs 函数签名（B4 差集兜底·漂移即 WARN）。
#   未声明工具调 _guard_check → 放行（None）——新工具必须同步登记本表（test 有文档化断言防漏）。
_GUARD_SPECS = {
    'zonal_stats': {'usage_params': ('boundary',)},
    'rank': {'usage_params': ('boundary',)},
    'buffer': {'usage_params': ('center',)},
    'grid_aggregate': {'usage_params': ('boundary',)},
    'compare_regions': {'usage_params': ('boundaries',)},
    'area_stats': {'usage_params': ('boundary',)},
    'nearest_analysis': {'usage_params': ('target',), 'pair_budget': 5 * 10 ** 7},
    'overlay_analysis': {'usage_params': ('layer_a', 'layer_b')},
    'trend_analysis': {'usage_params': ('boundary',)},
}


def _guard_check(tool: str, args: dict, caliber: dict = None) -> dict | None:
    """工具前置校验（G-2 usage 泛化 + 步数预算占位 + 审批策略占位）。

    - usage：对 spec.usage_params 逐参过 _reject_analysis_output（结论层禁作分析输入）；
    - 步数预算占位：pair_budget 声明位（nearest 已在函数体内置 _PAIR_BUDGET 守卫，
      此处为未来新工具的统一接线挂点·避免各自散落）；
    - 审批策略占位：写操作类工具未来接入（当前 server 工具全只读·无审批需求）。
    返回 None=放行；dict=语义化拒绝（带工具 caliber）。"""
    spec = _GUARD_SPECS.get(tool)
    if not spec:
        return None
    _cal = caliber or {'scale': 'guard', 'semantics': '工具前置校验',
                       'limits': 'usage 拒绝', 'refs': ['G-2']}
    for param in spec.get('usage_params', ()):
        value = args.get(param)
        if isinstance(value, str) and value:
            _g = _reject_analysis_output(value, param, _cal)
            if _g:
                return _g
    # 步数预算占位（统一挂点·当前由各工具内置守卫承担，新工具接线在此扩展）
    return None


def _audit_input_surfaces():
    """B4 白名单差集自动核对（服务启动一次·log 警告不阻塞）：
    ① _GUARD_SPECS 声明的 usage 参数与工具真实签名差集 → 提示 spec 漂移；
    ② manifest 可见面与可接受输入面（usage=input）差集 = analysis_output 集
    （按设计拒绝·仅记数留痕，供 B4 差集审计对账）。"""
    import inspect

    for tool, spec in _GUARD_SPECS.items():
        fn = globals().get(tool)
        if not callable(fn):
            _safe_print(f'[WARN] B4 差集核对: {tool} 不存在（_GUARD_SPECS 漂移）', file=sys.stderr)
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        for p in spec.get('usage_params', ()):
            if p not in sig.parameters:
                _safe_print(f'[WARN] B4 差集核对: {tool} 守卫参数 {p} 不在函数签名——请核对 _GUARD_SPECS',
                            file=sys.stderr)
    try:
        with open(MANIFEST, encoding='utf-8') as _fp:
            _groups = json.load(_fp)
        _ids = [it.get('id') for g in _groups for it in g.get('items', [])]
        _rejected = sum(1 for g in _groups for it in g.get('items', [])
                        if it.get('usage') == 'analysis_output')
        _safe_print(f'[OK] B4 输入面核对: manifest {len(_ids)} preset·拒绝面 {_rejected}'
                    '（analysis_output·按设计）', file=sys.stderr)
    except Exception as _exc:
        # A9：守卫/审计类禁静默吞——核对失败必须留痕（不阻塞启动）
        _safe_print(f'[WARN] B4 输入面核对跳过: {_exc}', file=sys.stderr)


# ── PT-CB11 P2① · trend_analysis（F_039·时序对比） ────────────────────────────

_TREND_LAYERS = {'T1': 'yichang_l2_t1', 'T2': 'yichang_l2_t2', 'T3': 'yichang_l2_t3'}
_TREND_METRICS = ('polarity_index', 'point_count', 'score_mean')


@track('MOD_AIQA.F_039', track_args=False)
def trend_analysis(boundary: str = '', metric: str = 'polarity_index',
                   periods: list = None) -> dict:
    """三期时序对比：L2 情绪点 T1/T2/T3 按可选 boundary 聚合→对比表+方向+幅度。
    参数：boundary 可选 preset（缺省=全城整体聚合）；metric=polarity_index|point_count|score_mean；periods 默认全三期（可取子集·≥2）。
    限制：三期=采集批次非等间隔日历期——勿算速率/环比；趋势为聚合口径非个体追踪；单期深挖用 zonal/hotspot。
    R23 两问：非 Point 几何仅出现在 boundary（面层·走 aggregate_by_polygons 的 sjoin 通道·无 .geometry.x 假设）；
    最坏规模=三期各约 2.2 万点的 O(n) 统计 + boundary sjoin O(n log n)——无配对矩阵·空点层/区内零点语义化拒绝。"""
    caliber = {'scale': '宏观/中观（三期聚合对比）',
               'semantics': 'T1/T2/T3 三期同口径聚合对比+方向（升/降/平）+幅度',
               'limits': '三期=采集批次非等间隔日历期——勿算速率/环比；趋势为聚合口径非个体追踪；单期深挖用 zonal/hotspot',
               'refs': ['K-C1']}
    if metric not in _TREND_METRICS:
        return {'ok': False, 'hint': f'metric 非法: {metric!r}（可选 {_TREND_METRICS}）',
                'caliber': caliber}
    if periods is None:
        keys = ['T1', 'T2', 'T3']
    elif isinstance(periods, str):
        keys = [s.strip().upper() for s in periods.replace('|', ',').split(',') if s.strip()]
    elif isinstance(periods, (list, tuple)):
        keys = [str(p).strip().upper() for p in periods if str(p).strip()]
    else:
        keys = []
    bad = [k for k in keys if k not in _TREND_LAYERS]
    if bad or len(keys) < 2:
        return {'ok': False,
                'hint': f'periods 需 ≥2 期且取自 {list(_TREND_LAYERS)}（收到 {periods!r}'
                        f'{"·未知期 " + str(bad) if bad else ""}）',
                'caliber': caliber}
    try:
        from core.geo_registry import resolve_boundary, resolve_points
        from core.spatial_analysis import aggregate_by_polygons

        polys = None
        if boundary:
            _g = _guard_check('trend_analysis', {'boundary': boundary}, caliber)
            if _g:
                return _g
            polys = resolve_boundary(boundary)
            polys = polys[['geometry']].dissolve()
            polys['name'] = '整体'
        rows = []
        for key in keys:
            layer_id = _TREND_LAYERS[key]
            pts = resolve_points(layer_id)
            if pts is None or len(pts) == 0:
                return {'ok': False,
                        'hint': f'{key} 点层为空（{layer_id}）——三期对比需各期有点',
                        'caliber': caliber}
            if polys is not None:
                cols = ['score'] if metric == 'score_mean' else []
                merged = aggregate_by_polygons(pts, polys, agg_cols=cols,
                                                polygon_name_col='name')
                if len(merged) == 0:
                    return {'ok': False,
                            'hint': f'{key} 在 boundary 内零点——聚合结果为空（请换 boundary 或检查点分布）',
                            'caliber': caliber}
                row = {'period': key, 'layer': layer_id,
                       'point_count': int(merged['point_count'].iloc[0])}
                row[metric] = (_jsonable(merged[metric].iloc[0])
                               if metric in merged.columns else None)
            else:
                import pandas as pd
                row = {'period': key, 'layer': layer_id, 'point_count': int(len(pts))}
                if metric == 'score_mean':
                    s = (pd.to_numeric(pts['score'], errors='coerce')
                         if 'score' in pts.columns else None)
                    row[metric] = (round(float(s.mean()), 4)
                                   if s is not None and s.notna().any() else None)
                elif metric == 'polarity_index':
                    if 'polarity' in pts.columns:
                        vc = pts['polarity'].astype(str).str.strip()
                        row[metric] = round(float(
                            (vc.eq('Very Positive') * 2 + vc.eq('Positive') * 1
                             + vc.eq('Negative') * -1 + vc.eq('Very Negative') * -2).sum()
                            / max(len(pts), 1)), 4)
                    else:
                        row[metric] = None
            rows.append(row)
        values = [r.get(metric) for r in rows]
        first, last = values[0], values[-1]
        if first is None or last is None:
            direction, delta = None, None
        else:
            delta = round(float(last) - float(first), 4)
            direction = 'flat' if abs(delta) < 0.01 else ('up' if delta > 0 else 'down')
        steps = []
        for i in range(len(rows) - 1):
            a, b = values[i], values[i + 1]
            steps.append({'from': rows[i]['period'], 'to': rows[i + 1]['period'],
                          'delta': (round(float(b) - float(a), 4)
                                    if a is not None and b is not None else None)})
    except (KeyError, FileNotFoundError):
        return {'ok': False, 'hint': _UNKNOWN_HINT, 'caliber': caliber}
    except Exception as exc:
        return {'ok': False, 'hint': f'trend_analysis 失败: {exc}', 'caliber': caliber}

    return {'rows': rows, 'metric': metric, 'direction': direction, 'delta': delta,
            'steps': steps, 'period_count': len(rows), 'caliber': caliber}


# ── PT-CB11 P2② · report_assemble（F_040·综合报告组装·零 LLM） ────────────────

@track('MOD_AIQA.F_040', track_args=False)
def report_assemble(question: str = '', results: list = None,
                    sections: list = None) -> dict:
    """综合报告组装：把各工具返回 dict 确定性组装为四段（零 LLM·不产生新结论）。
    参数：question 原问题；results=各工具返回 dict 列表（宿主链式传入·≥1 项）；sections 可选过滤（conclusion/evidence/caliber/suggestion）。
    段：conclusion=问题+有效结果计数确定性拼接；evidence=各结果 caliber 摘要+规模；caliber=refs 去重；suggestion=各结果行级 suggestion 汇总（无则诚实占位）。
    限制：组装不产生新结论——只汇总输入结果；输入无 caliber 的段落标注「口径缺失」不编造。"""
    caliber = {'scale': '答案级（综合报告）',
               'semantics': '确定性组装输入结果（零 LLM·不产生新结论）',
               'limits': '组装不产生新结论——只汇总输入结果；输入无 caliber 的段落标注「口径缺失」不编造',
               'refs': ['K-03']}
    if not isinstance(results, list) or len(results) == 0:
        return {'ok': False,
                'hint': 'report_assemble 需 results（各工具返回 dict 列表·≥1 项）——空输入无法组装',
                'caliber': caliber}
    _SECTION_ALLOWED = ('conclusion', 'evidence', 'caliber', 'suggestion')
    want = [s for s in (sections or _SECTION_ALLOWED) if s in _SECTION_ALLOWED]
    if not want:
        want = list(_SECTION_ALLOWED)

    evidence = []
    refs = []
    missing = 0
    for idx, r in enumerate(results):
        if not isinstance(r, dict):
            evidence.append({'index': idx + 1, 'scale': '口径缺失',
                             'semantics': '非 dict 输入', 'size': None})
            missing += 1
            continue
        cal = r.get('caliber') if isinstance(r.get('caliber'), dict) else None
        if cal is None:
            missing += 1
        size = next((r.get(k) for k in ('row_count', 'count', 'pair_count', 'result_count')
                     if r.get(k) is not None), None)
        evidence.append({
            'index': idx + 1,
            'scale': (cal.get('scale') if cal else None) or '口径缺失',
            'semantics': (cal.get('semantics') if cal else None) or '口径缺失',
            'size': size,
        })
        rrefs = cal.get('refs') if cal else None
        if isinstance(rrefs, list):
            refs.extend(str(x) for x in rrefs)
        elif rrefs:
            refs.append(str(rrefs))
    refs = list(dict.fromkeys(refs))
    valid = [r for r in results if isinstance(r, dict) and r.get('ok') is not False]
    conclusion = (f"问题：{question or '（未提供）'}；汇总 {len(valid)}/{len(results)} 项有效结果"
                  + (f"；其中 {missing} 项口径缺失（已标注·不编造）" if missing else "；全部结果带口径"))
    tips = []
    for r in valid:
        for row in (r.get('rows') or [])[:3]:
            if isinstance(row, dict) and row.get('suggestion'):
                tips.append(str(row['suggestion']))
    suggestion = tips if tips else '（输入结果未携带建议字段——本工具不产生新结论，建议需结合现场复核）'

    out_sections = {}
    if 'conclusion' in want:
        out_sections['conclusion'] = conclusion
    if 'evidence' in want:
        out_sections['evidence'] = evidence
    if 'caliber' in want:
        out_sections['caliber'] = {'refs': refs, 'missing_caliber_count': missing}
    if 'suggestion' in want:
        out_sections['suggestion'] = suggestion
    return {'question': question, 'sections': out_sections,
            'result_count': len(results), 'caliber': caliber}


def _dataset_meta(dataset_id, groups=None):
    """dataset_id → {usage, data_nature, note}（preset 读 manifest·点层按池路径·未知 None）。"""
    try:
        if groups is None:
            with open(MANIFEST, 'r', encoding='utf-8') as fh:
                groups = json.load(fh)
        for group in groups:
                for it in group.get('items', []):
                    if it.get('id') == dataset_id:
                        return {'usage': it.get('usage', 'input'),
                                'data_nature': it.get('data_nature', 'real'),
                                'note': it.get('note', '')}
    except Exception:
        pass
    try:
        from core.config import PERFORMANCE_DIR
        from core.geo_registry import _POINT_LAYERS, _layer_path, list_point_layers
        for p in list_point_layers():
            if p.get('id') == dataset_id and p.get('available'):
                entry = _POINT_LAYERS.get(dataset_id)
                nature = 'real'
                if entry is not None:
                    path = os.path.normpath(_layer_path(entry))
                    nature = 'demo' if path.startswith(os.path.normpath(PERFORMANCE_DIR) + os.sep) else 'real'
                return {'usage': 'input', 'data_nature': nature}
    except Exception:
        pass
    return None


@track('MOD_AIQA.F_028', track_args=False)
def render_spec(kind: str, name: str, dataset_id: str = '', geojson: dict = None,
                scheme: str = '', value_field: str = 'polarity_index',
                ramp_hint: str = '', zoom_to: bool = True, producer: str = 'dsh',
                source_tool: str = 'manual', data_nature: str = 'real',
                community_caliber: int = 0) -> dict:
    """图层图纸：dataset 引用或内联 GeoJSON → render_inbox spec，经 8080 前端显示屏呈现。
    参数：kind=point|choropleth；name 必填；dataset_id 与 geojson（要素≤60）二选一；value_field 默认 polarity_index（错配/被字段政策剔除→语义化拒绝·B3-2）；scheme 缺省自动；community_caliber 可选 K-C1 枚举。
    限制：写盘毫秒级不渲染；需浏览器已开情绪地图页；新 spec 覆盖旧 [dsh] 图层（T1）；三档出图范式（inline/dataset_id/脚本+注册）见 docs/render-contract.md。"""
    if kind not in ('point', 'choropleth'):
        return {'ok': False, 'hint': f'kind 非法: {kind!r}（仅 point|choropleth）',
                'caliber': CALIBERS['render_spec']}
    if not name or not str(name).strip():
        return {'ok': False, 'hint': 'name 必填（现实内容命名）',
                'caliber': CALIBERS['render_spec']}

    # P+ scheme 受管词表（旧 token 机制不再产出）
    resolved_scheme = scheme or ('point_default_v1' if kind == 'point' else 'community_choropleth_v1')
    if resolved_scheme not in SCHEMES:
        return {'ok': False, 'hint': f'scheme 未注册: {resolved_scheme}（词表: {", ".join(SCHEMES)}）',
                'caliber': CALIBERS['render_spec']}

    fixes = []
    usage = 'input'
    # PT-CB14 C3（D-6 销号）：data_nature 增 'test' 值（测试 spec 显式标记·前端徽标 [测试]·用毕清理纪律见 render-contract §五）
    nature = data_nature if data_nature in ('real', 'demo', 'test') else 'real'
    data = {}
    if dataset_id:
        meta = _dataset_meta(dataset_id)
        if meta is None:
            return {'ok': False, 'hint': f'未知 dataset_id: {dataset_id}（调用 list_data 查看清单）',
                    'caliber': CALIBERS['render_spec']}
        usage = meta['usage']
        # P1-B：引用预注册结论层/临时层时软警示，提示模型核对是否与本轮答案口径一致（不硬拒）
        # PT-CB15 K2 豁免：tmp_render_ 且 note 含「layer_output 自动登记」= 本轮分析直传产物，
        # 正是推荐路径——警示会误报，改为中性确认句。
        _is_layer_output_ref = (dataset_id.startswith('tmp_render_')
                                and 'layer_output' in str(meta.get('note', '')))
        if _is_layer_output_ref:
            fixes.append(f'引用 layer_output 直传产物 dataset_id={dataset_id}——确认 value_field 与统计口径一致即可')
        elif usage == 'analysis_output' or dataset_id.startswith('tmp_render_') or re.match(r'page7_.*_top\d+', dataset_id):
            fixes.append(f'引用预注册层 dataset_id={dataset_id}（usage={usage}）非本轮计算结果——若答案指定 Top-N/口径，请核对图层要素是否一致')
        # PT-CB14 C3：data_nature='test' 为测试投递显式标记·不被 dataset meta 覆盖（real/demo 仍以 dataset 为准）
        if nature != 'test':
            nature = meta['data_nature']
        data = {'dataset_id': dataset_id}
        if geojson is not None:
            fixes.append('dataset_id 与 geojson 同时给·以 dataset_id 为准')
    elif geojson is not None:
        if not isinstance(geojson, dict) or geojson.get('type') != 'FeatureCollection':
            return {'ok': False, 'hint': 'geojson 必须是 FeatureCollection',
                    'caliber': CALIBERS['render_spec']}
        feats = geojson.get('features') or []
        if len(feats) > 60:
            return {'ok': False, 'hint': '内联要素 >60·请改用 dataset_id 引用',
                    'caliber': CALIBERS['render_spec']}
        data = {'geojson': geojson}
        # PT-CB15 K4（R1-2）：内联几何抽稀软校验（提示级·不阻断·守软校验红线）——
        # 面要素带统计字段但面均外环顶点 <30：疑似模型转录抽稀（TOP7 实测源 2297 顶点被手抄成 80），
        # 提示改用分析工具 layer_output 返回的 render_dataset_id 直传（几何不过上下文）。
        if kind == 'choropleth' and feats:
            _STATS_KEYS = ('point_count', 'polarity_index', 'value', 'score_mean')
            has_stats = any(any(k in (f.get('properties') or {}) for k in _STATS_KEYS)
                            for f in feats)
            ring_counts = []
            for f in feats:
                geom = f.get('geometry') or {}
                coords = geom.get('coordinates') or []
                try:
                    if geom.get('type') == 'Polygon' and coords:
                        ring_counts.append(len(coords[0]))
                    elif geom.get('type') == 'MultiPolygon' and coords and coords[0]:
                        ring_counts.append(len(coords[0][0]))
                except (TypeError, IndexError):
                    continue
            if has_stats and ring_counts and sum(ring_counts) / len(ring_counts) < 30:
                fixes.append(
                    f'内联几何疑似被压缩（面均外环顶点 {sum(ring_counts) // len(ring_counts)}·源数据通常数百）'
                    '——分析结果出图请改用 layer_output 返回的 render_dataset_id 直传（几何不过上下文）')
    else:
        return {'ok': False, 'hint': 'data 二选一必填：dataset_id 或 geojson',
                'caliber': CALIBERS['render_spec']}

    if kind == 'choropleth' and not value_field:
        return {'ok': False, 'hint': 'choropleth 须 value_field 非空',
                'caliber': CALIBERS['render_spec']}

    # PT-CB11 B3-2：value_field 服务端校验（治注入层灰框根因①——字段错配→归一全零→透明无填充）。
    # dataset 路径双层：实际字段（读文件首要素）+ 渲染通道政策（core/render_policy 单一权威源）；
    # inline 路径：要素属性并集。读不到实际字段时降级为仅政策校验（不硬拒）。
    if kind == 'choropleth':
        from core.render_policy import dataset_field_names, field_allowed, renderable_fields
        if dataset_id:
            actual = dataset_field_names(dataset_id)
            if actual is not None and value_field not in actual:
                usable = sorted(renderable_fields(dataset_id))
                return {'ok': False,
                        'hint': (f'value_field {value_field!r} 不在 dataset {dataset_id} 要素属性中'
                                 f'（可渲染字段: {usable[:12]}·部分字段可能未列出）——错配会全零透明'),
                        'caliber': CALIBERS['render_spec']}
            if not field_allowed(value_field, dataset_id):
                usable = sorted(renderable_fields(dataset_id))
                return {'ok': False,
                        'hint': (f'value_field {value_field!r} 会被渲染通道字段政策剔除'
                                 f'（preset 可在 manifest 声明 renderFields·当前可渲染: {usable[:12]}·部分字段可能未列出）'),
                        'caliber': CALIBERS['render_spec']}
        elif geojson is not None:
            keys = set()
            for f in (geojson.get('features') or []):
                props = f.get('properties')
                if isinstance(props, dict):
                    keys.update(props.keys())
            if keys and value_field not in keys:
                return {'ok': False,
                        'hint': (f'value_field {value_field!r} 不在 geojson 要素属性中'
                                 f'（可用: {sorted(keys)[:12]}）'),
                        'caliber': CALIBERS['render_spec']}

    style = {'scheme': resolved_scheme, 'value_field': value_field}
    if ramp_hint:
        style['ramp_hint'] = ramp_hint
        # 词表校验在前端 HEATMAP_RAMPS（单一权威·后端不复制）·未注册将回落默认 grid-warm
        fixes.append(f'ramp_hint={ramp_hint} 已透传·未注册则前端回落默认色带（受管词表见 render-contract §四）')

    caliber_lite = {'usage': usage, 'data_nature': nature, 'note': '; '.join(fixes)}
    # K-C1 社区口径校验（PT-CB6 D11）
    if dataset_id:
        known_scope = _KNOWN_COMMUNITY_SCOPE.get(dataset_id)
        if known_scope is not None:
            auto_community = known_scope
            if community_caliber and int(community_caliber) != auto_community:
                caliber_lite['community_warning'] = (
                    f'调用方声明 community={int(community_caliber)}，'
                    f'但 dataset {dataset_id} 已知 scope={auto_community}（K-C1）')
            caliber_lite['community'] = auto_community
        elif community_caliber:
            cc = int(community_caliber)
            if cc not in K_C1_COMMUNITY_SCOPES:
                return {'ok': False,
                        'hint': f'community_caliber 非法: {cc}（K-C1 可选 {K_C1_COMMUNITY_SCOPES}）',
                        'caliber': CALIBERS['render_spec']}
            caliber_lite['community'] = cc
    elif community_caliber:
        cc = int(community_caliber)
        if cc not in K_C1_COMMUNITY_SCOPES:
            return {'ok': False,
                    'hint': f'community_caliber 非法: {cc}（K-C1 可选 {K_C1_COMMUNITY_SCOPES}）',
                    'caliber': CALIBERS['render_spec']}
        caliber_lite['community'] = cc


    spec_id = f'{int(time.time() * 1000)}-{random.randint(1000, 9999)}'
    spec = {
        'spec_version': 1,
        'spec_id': spec_id,
        'kind': kind,
        'data': data,
        'style': style,
        'ui': {'name': str(name).strip(), 'zoom_to': bool(zoom_to)},
        'origin': {'producer': producer, 'source_tool': source_tool},
        'caliber_lite': caliber_lite,
    }

    inbox_dir = os.path.join(REPO, 'DATA', 'Export', 'exports', 'render_inbox')
    os.makedirs(inbox_dir, exist_ok=True)
    inbox_path = os.path.join(inbox_dir, f'{spec_id}.json')
    with open(inbox_path, 'w', encoding='utf-8', newline='') as fh:
        json.dump(spec, fh, ensure_ascii=False)

    return {'ok': True, 'spec_id': spec_id, 'inbox_path': inbox_path,
            'caliber_lite': caliber_lite,
            'caliber': CALIBERS['render_spec']}


# PT-CB7 T18：render_file 自动登记临时 dataset 的 manifest 分组
TMP_RENDER_GROUP = 'dsh 临时渲染（render_file 自动登记）'


def _find_tmp_dataset(groups, rel_file):
    """同源文件已有临时登记则复用 id（防重复登记膨胀 manifest）。"""
    for group in groups:
        for it in group.get('items', []):
            if str(it.get('id', '')).startswith('tmp_render_') and it.get('file') == rel_file:
                return it.get('id')
    return None


def _register_tmp_dataset(abs_path, label, render_fields=None):
    """落盘文件登记进 manifest TMP_RENDER_GROUP（同源文件复用既有 id）→ dataset_id。

    PT-CB15 K2 抽公共：render_file 与 layer_output 落盘共用本登记通道。
    render_fields：声明可经渲染通道透传的字段（render_policy 政策层·防 value/指标字段被白名单误剔）。
    manifest 读写异常抛给调用方处置（render_file 语义化拒绝 / _attach_render_ref 降级）。"""
    with open(MANIFEST, 'r', encoding='utf-8') as fh:
        groups = json.load(fh)
    rel = os.path.relpath(abs_path, os.path.dirname(MANIFEST)).replace(os.sep, '/')
    ds_id = _find_tmp_dataset(groups, rel)
    if ds_id is None:
        ds_id = f'tmp_render_{int(time.time() * 1000)}'
        entry = {'id': ds_id, 'label': label, 'file': rel,
                 'nameField': 'name', 'usage': 'analysis_output',
                 'note': 'render_file/layer_output 自动登记（临时渲染·7 天 TTL·PT-CB15 K3）'}
        if render_fields:
            entry['renderFields'] = [f for f in render_fields if f]
        target = next((g for g in groups if g.get('group') == TMP_RENDER_GROUP), None)
        if target is None:
            target = {'group': TMP_RENDER_GROUP, 'items': []}
            groups.append(target)
        target['items'].append(entry)
        with open(MANIFEST, 'w', encoding='utf-8', newline='') as fh:
            json.dump(groups, fh, ensure_ascii=False, indent=2)
    return ds_id


@track('MOD_AIQA.F_031', track_args=False)
def render_file(file: str, name: str = '', kind: str = '',
                value_field: str = 'point_count') -> dict:
    """把 geojson 文件现在显示到地图：服务端读取，≤60 要素内联，>60 自动登记临时 dataset 并引用（无需手工注册）。
    参数：file 仓内路径（白名单根目录·相对或绝对）；name 缺省取文件名；kind 缺省自动判 point/choropleth；value_field 默认 point_count。
    限制：仅收 FeatureCollection；面文件默认 value_field=point_count 多半不适用——显式传该文件真实指标字段；
    「把 X 显示到地图上」的唯一正路——直接渲染，不做进 Range 等用户点击。"""
    cal = CALIBERS['render_spec']
    # 路径安全：白名单 = 仓根（防路径穿越读外部文件）
    p = os.path.abspath(file if os.path.isabs(file) else os.path.join(REPO, file))
    if not p.startswith(REPO + os.sep):
        return {'ok': False, 'hint': 'file 必须在仓内（路径白名单）', 'caliber': cal}
    if not os.path.isfile(p):
        return {'ok': False, 'hint': f'文件不存在: {os.path.relpath(p, REPO)}', 'caliber': cal}
    try:
        with open(p, 'r', encoding='utf-8') as fh:
            fc = json.load(fh)
    except Exception as exc:
        return {'ok': False, 'hint': f'geojson 解析失败: {exc}', 'caliber': cal}
    if not isinstance(fc, dict) or fc.get('type') != 'FeatureCollection':
        return {'ok': False, 'hint': '文件必须是 FeatureCollection', 'caliber': cal}
    feats = fc.get('features') or []
    if not feats:
        return {'ok': False, 'hint': 'geojson 无要素', 'caliber': cal}

    if not kind:
        gtype = str((feats[0].get('geometry') or {}).get('type', ''))
        kind = 'point' if gtype == 'Point' else 'choropleth'
    layer_name = name.strip() or os.path.splitext(os.path.basename(p))[0]

    # ≤ 60 要素：直接内联（范式①）
    if len(feats) <= 60:
        out = render_spec(kind=kind, name=layer_name, geojson=fc,
                          value_field=value_field)
        out['mode'] = 'inline'
        return out

    # > 60 要素：自动登记临时 dataset（同源复用）→ dataset_id 引用（范式②③自动合体）
    try:
        ds_id = _register_tmp_dataset(p, layer_name)
    except (OSError, ValueError) as exc:
        return {'ok': False, 'hint': f'manifest 登记失败: {exc}', 'caliber': cal}
    out = render_spec(kind=kind, name=layer_name, dataset_id=ds_id,
                      value_field=value_field)
    out['mode'] = 'dataset'
    out['dataset_id'] = ds_id
    return out


def build_server():
    """惰性装配 FastMCP（mcp 包仅在真正启动 server 时 import）。"""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP('EMC 标准插座（分析七件套 + render_spec）')
    server.tool()(list_data)
    server.tool()(rag_query)
    server.tool()(kb_facts)
    server.tool()(outlet_card)
    server.tool()(zonal_stats)
    server.tool()(buffer)
    server.tool()(rank)
    server.tool()(grid_aggregate)
    server.tool()(compare_regions)
    server.tool()(hotspot_analysis)
    server.tool()(area_stats)
    server.tool()(nearest_analysis)
    server.tool()(overlay_analysis)
    server.tool()(trend_analysis)
    server.tool()(report_assemble)
    server.tool()(render_spec)
    server.tool()(render_file)
    server.tool()(emc_status)
    _audit_input_surfaces()
    return server


def emc_status() -> dict:
    """探测 8080 地图服务（前端+渲染显示屏）就绪状态。入口向导流程专用（临时测试件）。
    用法：轮询本工具直至 ready=True（建议间隔 3-5s；服务预热含 RAG 模型加载约 30-60s）。
    ready=False 且 phase='starting' 时正在预热——继续轮询勿重复启动；phase='down' 时服务未运行。"""
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080/emc-ready', timeout=3) as r:
            ready = (r.status == 200)
        return {'ok': True, 'ready': ready,
                'phase': 'ready' if ready else 'starting',
                'hint': '' if ready else '服务预热中（RAG 模型加载约 30-60s），继续轮询',
                'caliber': {'scale': 'meta', 'semantics': '服务状态', 'limits': '仅探测不分析',
                            'refs': ['PT-CB8 入口向导']}}
    except Exception:
        return {'ok': True, 'ready': False, 'phase': 'down',
                'hint': '8080 服务未运行（需经 start_silent.vbs 启动后轮询）',
                'caliber': {'scale': 'meta', 'semantics': '服务状态', 'limits': '仅探测不分析',
                            'refs': ['PT-CB8 入口向导']}}


def _warmup():
    """PT-CB8 T17 · 冷启动预热线程：把惰性重资产在后台提前加载——
    ① RAG embedding 模型+索引（实测首调 13.8s → 热 0.02s·timeout 根因）
    ② 常用数据层（174 聚合边界 + 12345 点层）进 geo_registry 缓存
    ③ manifest usage 索引首建。失败无害（log 不静默·不倒 server）。主线程同步执行（见下修正注记）。"""

    def _task():
        try:
            from tools.rag_index import search
            search('预热', k=1)
            _safe_print('[OK] 预热: RAG 模型+索引就绪', file=sys.stderr)
        except Exception as exc:  # 预热失败不阻断服务（A9：log 不静默）
            _safe_print(f'[WARN] 预热 RAG 失败(不阻断): {exc}', file=sys.stderr)
        try:
            from core.geo_registry import resolve_boundary, get_layer_points
            resolve_boundary('checkup_cfg_community174')
            get_layer_points('checkup_12345_2024')
            _safe_print('[OK] 预热: 常用数据层就绪', file=sys.stderr)
        except Exception as exc:
            _safe_print(f'[WARN] 预热数据层失败(不阻断): {exc}', file=sys.stderr)
        try:
            from core.field_dictionary import get_layer_usage
            get_layer_usage('admin_district')
        except Exception:
            pass  # usage 索引毫秒级·失败无感

    # 主线程同步预热（T17 实测修正）：子线程 import 在 server 事件循环进程内会卡死
    # （独立进程正常·根因疑为主线程已部分加载的重库+子线程续载 DLL 交互），改主线程
    # 顺序预热：启动期约 +15s，换取 initialize 后全工具热调（client 超时 120s 保险）。
    _safe_print('[OK] 预热开始（约 15s·主线程同步）', file=sys.stderr)
    _task()
    _safe_print('[OK] 预热完成', file=sys.stderr)


def main(mode='stdio', port=8600):
    """MCP server 启动入口。

    stdio 模式：dsh 经 stdin/stdout 管道通信（终端须保持打开）。
    http 模式：常驻 HTTP 服务（终端可随意开关·多会话共享）。
    """
    import argparse
    parser = argparse.ArgumentParser(description='EMC MCP Server')
    parser.add_argument('--http', action='store_true', help='HTTP 模式（常驻服务·默认 stdio）')
    parser.add_argument('--port', type=int, default=port, help='HTTP 端口（默认 8600）')
    args = parser.parse_args()

    if args.http:
        _safe_print(f'[OK] EMC MCP server HTTP 模式启动 (port={args.port})', file=sys.stderr)
        _warmup()
        _safe_print('[OK] 预热完成·开始监听', file=sys.stderr)
        _srv = build_server()
        _srv.settings.host = '127.0.0.1'
        _srv.settings.port = args.port
        _srv.run(transport='streamable-http')
        return

    # stdio 模式（原有逻辑）
    _safe_print('[OK] EMC MCP server stdio 启动（Ctrl+C 退出）', file=sys.stderr)
    import os as _os
    if _os.environ.get('EMC_MCP_STDIO', '1') != '0':
        _orig_stdout = sys.stdout
        sys.stdout = sys.stderr
        try:
            _warmup()
        finally:
            sys.stdout = _orig_stdout
            _safe_print('[OK] stdout 已恢复给 FastMCP JSON-RPC', file=sys.stderr)
    else:
        _warmup()
    build_server().run()


if __name__ == '__main__':
    main()
