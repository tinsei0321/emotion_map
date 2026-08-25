"""RAG 向量索引构建/查询工具（CB-22c Phase 1·本地 BGE embedding + numpy 暴力检索）。

用途：把 L0 知识库（docs/urban-renewal-plan/ 提炼笔记 + L1.5 事实卡 + case_library）向量化，
供 EMC 问答 rag_search 检索引用。业界主流 RAG 路线·本地 BGE 离线免费·不依赖外部 API 配额。

用法：
  py tools/rag_index.py --build          # 构建索引（向量化 L0 + 事实卡 + case·原子写）
  py tools/rag_index.py --query "葛洲坝有哪些更新项目"   # 检索 Top-K（试运行）
  py tools/rag_index.py --rebuild        # 全量重建（换模型/损坏）
  py tools/rag_index.py --stats          # 索引统计（向量数/维度/来源分布）
  py tools/rag_index.py --rebuild-if-stale  # 知识源新于索引才重建，否则报 OK（PT-CB16 S2）

纯函数·ASCII 标记（[OK]/[ERR]·禁 emoji）·不调 LLM。
track：MOD_AIQA.F_014（build_rag_index）/ F_015（rag_search）
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.tracker import track, register_track_id

register_track_id('MOD_AIQA.F_014', 'build_rag_index（RAG 向量索引构建·本地 BGE·原子写·embed_hash）')
register_track_id('MOD_AIQA.F_015', 'rag_search（RAG 向量检索·余弦 Top-K·返回片段+来源）')

# HF 镜像（国内网络·不覆盖用户显式配置）
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
# 模型已缓存（~/.cache/huggingface/hub）——默认离线，避免构建时联网重试卡死（PT-CB16 S2）
os.environ.setdefault('HF_HUB_OFFLINE', '1')

REPO = Path(__file__).resolve().parents[1]
RAG_DIR = REPO / 'DATA' / 'RAG' / 'rag_index'
VECTORS = RAG_DIR / 'vectors.npy'
META = RAG_DIR / 'meta.jsonl'
MODEL_NAME = 'BAAI/bge-small-zh-v1.5'

# 知识库来源
NOTES_DIR = REPO / 'docs' / 'urban-renewal-plan'
INDEX_FILE = NOTES_DIR / '_INDEX.md'


def _tag(ok, msg):
    print(f'[{"OK" if ok else "ERR"}] {msg}')


# 数据维度关键词推断（对齐四维度：住房/小区/社区/街区/城区 + 城中村专项·原则：结论颗粒度=数据来源维度）
_DIM_KEYWORDS = {
    '住房': ['住宅', '危旧房', '房屋', '楼栋', '栋', '住房', '建筑'],
    '小区': ['小区', '物业', '停车', '充电', '学位', '托育', '养老', '运动场'],
    '社区': ['社区', '党群', '街道'],
    '街区': ['街区', '街道', '道路', '步行道', '乱停'],
    '城区': ['城区', '城市', '总体规划', '综合', '整体', '宏观'],
    '城中村': ['城中村', '汉宜村', '改造'],
}


def _infer_dim(text):
    """从文本推断数据维度（关键词加权·返回最可能维度）。"""
    score = {}
    for dim, kws in _DIM_KEYWORDS.items():
        score[dim] = sum(1 for kw in kws if kw in text)
    if not any(score.values()):
        return '社区'  # 默认社区（调研最小单元）
    return max(score, key=score.get)


# ── PT-CB9 L3 · X-01 作废 chunk 显式登记（chunk source 级·替代 L1 文件级前缀机制）──
# R24 红线：每条登记必附原文引句（禁主题/时间推断——L1 误读 03-10§一 把 38 chunk 误标的教训）。
# 判定口径（派发单）：「以作废数字为现行结论」→ superseded；
#   「历史叙述/清单登记提及」（治理卡自身/变更链/资产清册/计划状态记述）→ 登记但 active
#   ——active 登记项与引句见执行记录 PT-CB9-L3执行记录 §三逐条表；待裁同表。
_SUPERSEDED_SOURCES = {
    # [1] X-01「公服设施 1,068 点」（菜市场 422+中学 535 误计）——引句：「民生基础需求 · 公服设施
    #     （8 项指标·总 1068 点·覆盖 136 社区）」——以误计值为现行总量结论（全表占比以其为分母）。
    #     替代：全覆盖版 165 点（K-04）。
    'docs/urban-renewal-plan/3prime/占比表_民生_公服设施_社区_2026-08-12.md#0',
    # [2] X-01「双高 16/32/3/26（各代·双高概念整体取消）」——引句：「① 双高区（G10·重头·16 格·
    #     管线已验证）」「观点：双高区 = 最急难愁盼（市民声音×客观指标双证聚焦）」——作废概念
    #     各代值 16 格作现行分析结论。替代：K-03 两表。
    'docs/urban-renewal-plan/3prime/B3B4_归纳与落图_交付_2026-08-12.md#2',
}

# lineage 同源谱系（'src:<上游文件>#<节>'·节=loader 位置序号·只标注不删档）。
# 逐卡经 token 验证（distinctive 数字/专名在目标小节 verbatim 命中）·67/68 事实卡；
# EMC-IDENTITY-01 上游为 PT-CB 文档（非语料）·不标。不确定项入执行记录 §待裁清单。
_LINEAGE_MAP = {
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P01': 'src:docs/urban-renewal-plan/_笔记/codex_0819_260713_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P02': 'src:docs/urban-renewal-plan/_笔记/codex_0819_260713_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P03': 'src:docs/urban-renewal-plan/_笔记/codex_伍家岗十五五_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P04': 'src:docs/urban-renewal-plan/_笔记/codex_伍家岗十五五_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P05': 'src:docs/urban-renewal-plan/00-宜昌专项/00-02_宜昌城市更新专项规划阶段性成果0610.md#5',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P06': 'src:docs/urban-renewal-plan/_笔记/codex_0819_260713_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P07': 'src:docs/urban-renewal-plan/_笔记/codex_伍家岗十五五_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P08': 'src:docs/urban-renewal-plan/_笔记/codex_伍家岗十五五_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P09': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#5',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P10': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P11': 'src:docs/urban-renewal-plan/城市更新专项规划资料集_总览报告.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-P12': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I01': 'src:docs/urban-renewal-plan/_笔记/codex_体检附件_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I02': 'src:docs/urban-renewal-plan/_笔记/codex_体检附件_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I03': 'src:docs/urban-renewal-plan/_笔记/claude_GIS图层对照_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I04': 'src:docs/urban-renewal-plan/_笔记/codex_体检附件_2026-08-09.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I05': 'src:docs/urban-renewal-plan/_笔记/codex_体检附件_2026-08-09.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I06': 'src:docs/urban-renewal-plan/00-宜昌专项/03-05_宜昌葛洲坝片区体检报告.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I07': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#5',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I08': 'src:docs/urban-renewal-plan/00-宜昌专项/03-05_宜昌葛洲坝片区体检报告.md#6',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I09': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I10': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I11': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I12': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I13': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I14': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I15': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-I16': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-C01': 'src:docs/urban-renewal-plan/00-宜昌专项/03-05_宜昌葛洲坝片区体检报告.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-C02': 'src:docs/urban-renewal-plan/00-宜昌专项/03-05_宜昌葛洲坝片区体检报告.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-C03': 'src:docs/urban-renewal-plan/_笔记/claude_GIS图层对照_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-C04': 'src:docs/urban-renewal-plan/00-宜昌专项/03-06_宜昌2024年度国土空间规划城市体检报告.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-C05': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-C06': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-C07': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#5',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-A01': 'src:docs/urban-renewal-plan/_笔记/codex_0819_260713_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-A02': 'src:docs/urban-renewal-plan/00-宜昌专项/00-01_宜昌市中心城区城市更新专项规划修编0809.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-A03': 'src:docs/urban-renewal-plan/_笔记/codex_伍家岗十五五_2026-08-09.md#1',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-K01': 'src:ai_qa/outlet_kb/case_library.py#yichang_wangzhou',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-K02': 'src:ai_qa/outlet_kb/case_library.py#shanghai_satisfaction',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-K03': 'src:ai_qa/outlet_kb/case_library.py#nanjing_bigdata',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-K04': 'src:ai_qa/outlet_kb/case_library.py#guangzhou_satisfaction',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-K05': 'src:ai_qa/outlet_kb/case_library.py#ningxia_guideline',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-L01': 'src:docs/urban-renewal-plan/城市更新专项规划资料集_总览报告.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-L02': 'src:docs/urban-renewal-plan/_笔记/codex_部委文件_2026-08-09.md#1',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-L03': 'src:docs/urban-renewal-plan/_笔记/glm_05编制导则_2026-08-09.md#0',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-L04': 'src:docs/urban-renewal-plan/城市更新专项规划资料集_总览报告.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-M01': 'src:docs/urban-renewal-plan/00-宜昌专项/03-05_宜昌葛洲坝片区体检报告.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-M02': 'src:docs/urban-renewal-plan/_笔记/codex_伍家岗十五五_2026-08-09.md#2',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-M03': 'src:docs/urban-renewal-plan/00-宜昌专项/00-04_宜昌城市更新专项规划说明书0714.md#0',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-M04': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#URP-M05': 'src:docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#1',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I01': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I02': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I03': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I04': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I05': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I06': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I07': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I08': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I09': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I10': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-I11': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-P01': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#3',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-P02': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#4',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-P03': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#5',
    'ai_qa/outlet_kb/urban_renewal_knowledge.py#CHK-P04': 'src:docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md#10',
}

# ── PT-CB9R-B3：X-01 关联集替代指针（返回结构不对称标注·判定数据=本表+_SUPERSEDED_SOURCES+_LINEAGE_MAP）──
# 历史叙述类 = L3 执行记录登记表（PT-CB9-L3执行记录 §三）判定三分法 A 行/待裁→主手裁定 active 行·登记但 active。
# 逐条对应（R24：chunk 级·原文引句核验在案·执行记录 PT-CB9R-D 附逐条映射）：
#   口径注册表#3 = L3 行 1/2/3/13/14（L3 表写 #4·实测作废数字卡在 loader 第 3 节·已报主手纠错）；
#   B3B4#0 = 行 5（数据源/管线记述）·B3B4#3 = 行 6（交付清单事实登记）；
#   总纲#3/#4 = 行 8 + 主手 08-23 裁定（#5 由 Qoder F-03 补入·均判 active 登记·计划状态记述）。
#   03-10（行 10）为现行口径文档（自带取消声明）→ 零标签不入本表；素材表#0（行 7/12）chunk 截断处
#   无作废值行（loader 2000 字截断）→ 零标签不入本表·详见执行记录待裁清单。
_X01_HISTORICAL_NARRATIVE = {
    'docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md#3': 'X-01 卡替代列（K-01/K-02/K-03/K-04 等）',
    'docs/urban-renewal-plan/3prime/B3B4_归纳与落图_交付_2026-08-12.md#0': 'K-03 两表',
    'docs/urban-renewal-plan/3prime/B3B4_归纳与落图_交付_2026-08-12.md#3': 'K-03 两表',
    'docs/urban-renewal-plan/3prime/分析计划与内容_总纲_2026-08-12.md#3': 'K-03 两表',
    'docs/urban-renewal-plan/3prime/分析计划与内容_总纲_2026-08-12.md#4': 'K-03 两表',
    'docs/urban-renewal-plan/3prime/分析计划与内容_总纲_2026-08-12.md#5': 'K-03 两表',
}

# superseded 行的替代指针（chunk 本身已被检索层滤除·供 lineage 谱系链式命中反查——
# 未来事实卡 lineage 指向作废源时按此注记·当前语料无此类命中·机制就位）。
_X01_SUPERSEDED_POINTERS = {
    'docs/urban-renewal-plan/3prime/占比表_民生_公服设施_社区_2026-08-12.md#0': 'K-04 全覆盖版 165 点',
    'docs/urban-renewal-plan/3prime/B3B4_归纳与落图_交付_2026-08-12.md#2': 'K-03 两表',
}


def _history_note(source, lineage=None):
    """PT-CB9R-B3：X-01 关联历史叙述类不对称标注（确定性零 LLM·现行条目返回 None=零标签）。

    判定：①直接命中 _X01_HISTORICAL_NARRATIVE（登记但 active 的历史叙述类 chunk）→ 注记；
    ②谱系链式——lineage 非空且目标 ∈ X-01 关联集（含 superseded 源）→ 注记（当前语料无命中·机制就位）。
    返回格式：'历史口径·现行见<替代指针>'（替代指针逐条来自 L3 执行记录登记表）。
    """
    if source in _X01_HISTORICAL_NARRATIVE:
        return f'历史口径·现行见{_X01_HISTORICAL_NARRATIVE[source]}'
    if lineage:
        _tgt = lineage[4:] if lineage.startswith('src:') else lineage
        _ptr = _X01_SUPERSEDED_POINTERS.get(_tgt) or _X01_HISTORICAL_NARRATIVE.get(_tgt)
        if _ptr:
            return f'历史口径·现行见{_ptr}'
    return None


def _governance(source):
    """治理字段填充（PT-CB9 L1/L3）：返回 (status, lineage)。

    status：_SUPERSEDED_SOURCES 显式登记（X-01 逐条·R24 引句）→ 'superseded'，其余 'active'；
    lineage：_LINEAGE_MAP 直查·无同源 → None。字段缺失=active 兼容（契约 §四红线）。
    """
    status = 'superseded' if source in _SUPERSEDED_SOURCES else 'active'
    return status, _LINEAGE_MAP.get(source)


def _load_notes():
    """读 L0 提炼笔记（按小节切分·段落级向量·标注数据维度）。"""
    chunks = []
    if not NOTES_DIR.exists():
        return chunks
    # 下划线知识本体白名单（主手裁决 08-22·L2 收口）：注册表/素材表是业务口径知识本体
    # （RAG 最该答的「数字怎么算」），非治理台账——下划线排除本意挡 _INDEX/_PATHS/_提炼模板。
    _KNOWLEDGE_UNDERSCORE_WHITELIST = {'_口径注册表.md', '_图层素材表.md'}
    for md in sorted(NOTES_DIR.rglob('*.md')):
        # 跳过索引/README/模板（下划线默认排除·知识本体白名单放行）
        if (md.name.startswith('_') and md.name not in _KNOWLEDGE_UNDERSCORE_WHITELIST) \
                or 'README' in md.name or '模板' in md.name:
            continue
        text = md.read_text(encoding='utf-8', errors='ignore')
        # 按 ## 小节切分（~200-500 字/段）
        parts = []
        for block in text.split('\n## '):
            if block.strip():
                parts.append(block.strip())
        for i, p in enumerate(parts):
            if len(p) < 20:
                continue
            src = f'docs/urban-renewal-plan/{md.relative_to(NOTES_DIR).as_posix()}#{i}'
            st, lin = _governance(src)   # PT-CB9 L1：3prime 旧口径标 superseded·谱系查表
            chunks.append({
                'text': p[:2000],
                'source': src,
                'type': 'note',
                'dim': _infer_dim(p),  # 数据维度标注
                'status': st,
                'lineage': lin,
            })
    return chunks


def _load_data_readmes():
    """读 DATA 分层文档（PT-CB17 B4）：DATA/README.md（分层单一权威）+ DATA/THEME/**/README.md。

    根因：DATA 重组（权威 AUTHORITY/注册 REGISTRY/专题 THEME/产物 Export 四层 taxonomy）
    的权威文档不在 RAG 语料内——模型检索「数据分层/权威/专题」只能命中无关旧文档。
    治本源进语料（单一权威保持在 DATA/README.md·索引为只读镜像·不另写副本防双头）。
    切分/治理字段与 _load_notes 同纪律（## 小节·<20 丢弃·2000 截断·lineage=src）。"""
    chunks = []
    candidates = [REPO / 'DATA' / 'README.md']
    theme_dir = REPO / 'DATA' / 'THEME'
    if theme_dir.exists():
        candidates.extend(sorted(theme_dir.rglob('README.md')))
    for md in candidates:
        if not md.exists() or '_Retired' in str(md):
            continue
        text = md.read_text(encoding='utf-8', errors='ignore')
        parts = [b.strip() for b in text.split('\n## ') if b.strip()]
        for i, p in enumerate(parts):
            if len(p) < 20:
                continue
            src = f'{md.relative_to(REPO).as_posix()}#{i}'
            st, lin = _governance(src)
            chunks.append({
                'text': p[:2000],
                'source': src,
                'type': 'note',
                'dim': '数据分层',
                'status': st,
                'lineage': lin,
            })
    return chunks


def _load_cases():
    """读 case_library（案例块·只取方法论 point·不引他城数据·标注为方法论参考）。"""
    try:
        sys.path.insert(0, str(REPO))
        from ai_qa.outlet_kb.case_library import CASES
        chunks = []
        for key, c in CASES.items():
            # 案例 = 方法论参考（做法/路径/机制）·不引用他城具体数据（原则 2·防张冠李戴）
            text = f"{c.get('city','')}·{c.get('project','')}：{c.get('point','')}（方法论参考·做法/路径/机制·不引用他城具体数值）"
            st, lin = _governance(f'ai_qa/outlet_kb/case_library.py#{key}')   # PT-CB9 L1
            chunks.append({
                'text': text[:2000],
                'source': f'ai_qa/outlet_kb/case_library.py#{key}',
                'type': 'case',
                'dim': '方法论',  # 案例 = 方法论参考·非数据维度
                'status': st,
                'lineage': lin,
            })
        return chunks
    except Exception as e:
        _tag(False, f'case_library 读取失败: {str(e)[:60]}')
        return []


def _load_facts():
    """读 L1.5 事实卡（urban_renewal_knowledge.py·7 类·逐条一向量·含 dimension）。"""
    try:
        sys.path.insert(0, str(REPO))
        from ai_qa.outlet_kb.urban_renewal_knowledge import all_facts
        chunks = []
        for f in all_facts():
            src = f"ai_qa/outlet_kb/urban_renewal_knowledge.py#{f['id']}"
            st, lin = _governance(src)   # PT-CB9 L1：事实卡全 active·67/68 带同源谱系
            chunks.append({
                'text': f"{f['city']}·{f['region']}·{f['name']}：{f['detail']}（{f['keywords']}）",
                'source': src,
                'type': 'fact',
                'dim': f.get('dimension', '社区'),  # 数据维度（事实卡已标注）
                # CB-22f D3（Codex 富矿）：透传 fact 结构化字段——识别层零 LLM 组装 ctx.extracted 用
                #   （region=地理实体·topic/year/keywords=归因字段·检索辅助 + 动作链衔接）。
                #   注：向量化时拍平进 text 的字段在此保留结构化副本（search 透传 meta）。
                'region': f.get('region', ''),
                'topic': f.get('topic', ''),
                'year': f.get('year', ''),
                'keywords': f.get('keywords', ''),
                'status': st,
                'lineage': lin,
            })
        return chunks
    except Exception as e:
        _tag(False, f'事实卡读取失败: {str(e)[:60]}')
        return []


def _load_concepts():
    """读概念卡（CB-22 三层架构 P1·type='concept'·产品定位/方法论/边界认知·高度凝练+引用摘抄）。"""
    try:
        sys.path.insert(0, str(REPO))
        from ai_qa.outlet_kb.concept_knowledge import all_concepts
        chunks = []
        for c in all_concepts():
            src = f"ai_qa/outlet_kb/concept_knowledge.py#{c['id']}"
            st, lin = _governance(src)   # PT-CB9 L1
            chunks.append({
                'text': f"{c['name']}：{c['detail']}（{c['keywords']}）",
                'source': src,
                'type': 'concept',
                'dim': '方法论',  # 概念卡 = 定义/背景/边界（静态）·非数据维度
                'status': st,
                'lineage': lin,
            })
        return chunks
    except Exception as e:
        _tag(False, f'概念卡读取失败: {str(e)[:60]}')
        return []


def load_chunks():
    """全量 chunk（含治理字段 status/lineage·PT-CB9 L1·rag-loader-contract §二签名）。

    superseded 默认过滤由检索层做（search 预置·字段缺失=active 兼容）——loader 只填字段不过滤。
    顺序与 build_index 既有内联序一致（facts+notes+cases+concepts）——泳道②换挂零漂移。
    """
    chunks = (_load_facts() + _load_notes() + _load_data_readmes()
              + _load_cases() + _load_concepts())
    # PT-CB9 A1：前注注入（map=git 权威源·_ctx_prefix_map.json；护栏：正文 hash 不符不注入）
    import hashlib as _hl
    _map_path = Path(REPO) / 'docs' / 'urban-renewal-plan' / '_ctx_prefix_map.json'
    if _map_path.exists():
        try:
            _pm = json.loads(_map_path.read_text(encoding='utf-8'))
        except Exception:
            _pm = {}
        for _c in chunks:
            _e = _pm.get(_c['source'])
            if not _e:
                continue
            _th = _hl.sha256(_c['text'].encode('utf-8')).hexdigest()[:16]
            if _e.get('text_hash') != _th:
                continue   # 正文已变·前注待重生成（护栏：不注入失配前注）
            _c['ctx_prefix'] = _e['ctx_prefix']
            _c['ctx_prefix_model'] = _e.get('model')
            _c['ctx_prefix_hash'] = _hl.sha256(_e['ctx_prefix'].encode('utf-8')).hexdigest()[:16]
    return chunks


def _embed_texts(model, texts):
    """统一编码（query/passage 一致处理·bge-v1.5 支持 instruction）。"""
    return model.encode(texts, normalize_embeddings=True)


def _load_st_model(**kwargs):
    """加载 BGE 模型（transformers 5.x 兼容兜底·PT-CB15 K7）。

    bge-small-zh-v1.5 旧模型卡无 processor 配置：transformers 5.x 的
    AutoProcessor.from_pretrained 直接抛 ValueError（Unrecognized processing class），
    而 st 的 tokenizer 属性原生支持「processor 即 tokenizer 实例」——回退 AutoTokenizer 即可。
    只在命中该特定错误时安装兜底（一次性·加载后恢复原方法·A9 不静默吞其他错误）。"""
    from sentence_transformers import SentenceTransformer
    try:
        return SentenceTransformer(MODEL_NAME, **kwargs)
    except ValueError as exc:
        if 'processing class' not in str(exc):
            raise
        from transformers import AutoProcessor, AutoTokenizer
        _orig = AutoProcessor.from_pretrained

        def _fallback(name_or_path, *a, **kw):
            try:
                return _orig(name_or_path, *a, **kw)
            except ValueError:
                return AutoTokenizer.from_pretrained(name_or_path, *a, **kw)

        AutoProcessor.from_pretrained = _fallback
        try:
            return SentenceTransformer(MODEL_NAME, **kwargs)
        finally:
            AutoProcessor.from_pretrained = _orig


@track('MOD_AIQA.F_014', track_args=False)
def build_index():
    """构建向量索引（原子写 + embed_hash）。"""
    import numpy as np

    RAG_DIR.mkdir(parents=True, exist_ok=True)
    _tag(True, f'加载模型 {MODEL_NAME}（首次下载 ~40s·需 HF 镜像）...')
    model = _load_st_model()

    # 护栏 4（PT-CB9 L3）：重建命令一体化——前注增量生成内串（禁手工两步·双机重建一条命令）。
    #   限定域 chunk 缺失/正文 hash 不符才调 LLM·未变更零调用；失败不阻塞构建（已有前注不受影响）。
    _pfx = {'made': 0, 'skipped': 0, 'map_total': 0}
    try:
        from tools.rag_ctx_prefix import generate as _gen_ctx_prefix
        _pfx = _gen_ctx_prefix() or _pfx
    except (ImportError, OSError) as exc:
        _tag(False, f'前注增量生成不可用（继续构建·已有前注不受影响）: {str(exc)[:60]}')
    except Exception as exc:
        _tag(False, f'前注增量生成失败（继续构建·已有前注不受影响）: {type(exc).__name__}: {str(exc)[:60]}')

    # 收集向量化对象——走 load_chunks() 单源（loader 契约·治理字段+前注唯一注入点·主手合流 08-22）
    all_chunks = load_chunks()
    _tag(True, f'向量化对象: {len(all_chunks)} chunk（经 load_chunks·含治理/前注字段）')

    if not all_chunks:
        _tag(False, '无向量化对象')
        return

    # PT-CB9 A1 消融层（主手合流）：编码输入 = ctx_prefix + 正文（限定域 chunk 有前注）
    texts = [((c.get('ctx_prefix') or '') + '\n' + c['text']) if c.get('ctx_prefix') else c['text']
             for c in all_chunks]
    _tag(True, f'编码 {len(texts)} 条·前注覆盖 {sum(1 for c in all_chunks if c.get("ctx_prefix"))} 条...')
    vectors = _embed_texts(model, texts)
    _tag(True, f'编码完成·维度 {vectors.shape[1]}')

    # 元数据（含 embed_hash + 数据维度 + build_time）
    import hashlib
    import time
    metas = []
    for c, vec in zip(all_chunks, vectors):
        # 护栏 3（PT-CB9 L3）：content_hash 覆盖「正文+前注」整体——前注变而正文未变→hash 变→快照可检测；
        #   ctx_prefix_hash 分离保留（loader 契约三字段不变·用于正文变→前注必重算的校验方向）。
        h = hashlib.sha256((c['text'] + (c.get('ctx_prefix') or '')).encode('utf-8')).hexdigest()
        metas.append({
            'source': c['source'],
            'type': c['type'],
            'data_dim': c.get('dim', '社区'),  # 数据维度（住房/小区/社区/街区/城区/城中村/方法论）
            'content_hash': h,
            # CB-22 三支柱修正（两组对齐后承重发现）：素材内容必须随索引持久化——
            #   此前只存 hash·search 返回无 text·注入 finalStep 的"素材"仅文件名列表·
            #   LLM 无内容可综合（三支柱①空转·验收 V2 结构性不可过）→ 存片段全文供 LLM 综合
            'text': c['text'][:2000],
            'embedding_model': MODEL_NAME,
            'dim': int(vectors.shape[1]),
            'build_time': time.strftime('%Y-%m-%d %H:%M'),
            # CB-22f D3（Codex 富矿）：fact 结构化字段透传（region/topic/year/keywords）——
            #   识别层零 LLM 组装 ctx.extracted 用·仅 type=fact 有值·note/case/concept 空串
            'region': c.get('region', ''),
            'topic': c.get('topic', ''),
            'year': c.get('year', ''),
            'keywords': c.get('keywords', ''),
            # PT-CB9 L1+A1 合流（主手）：治理与前注字段随 meta 持久化（search 过滤/BM25 拼接消费面）
            'status': c.get('status', 'active'),
            'lineage': c.get('lineage'),
            'ctx_prefix': c.get('ctx_prefix'),
            'ctx_prefix_model': c.get('ctx_prefix_model'),
            'ctx_prefix_hash': c.get('ctx_prefix_hash'),
        })

    # 原子写（防崩溃不一致·np.save 自动加 .npy·临时名用 .npy 结尾）
    tmp_v = RAG_DIR / 'vectors.tmp.npy'
    tmp_m = RAG_DIR / 'meta.jsonl.tmp'
    np.save(str(tmp_v), vectors.astype('float32'))
    with open(tmp_m, 'w', encoding='utf-8') as f:
        for m in metas:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')
    os.replace(str(tmp_v), str(VECTORS))
    os.replace(str(tmp_m), str(META))
    _tag(True, f'索引已写: {VECTORS} ({len(metas)} 条·原子写)')
    # 护栏 4（PT-CB9 L3）：构建摘要——chunk 总数/前注覆盖/前注新生成/跳过（未变更）/superseded 数
    _cov = sum(1 for c in all_chunks if c.get('ctx_prefix'))
    _sup = sum(1 for c in all_chunks if c.get('status') == 'superseded')
    _tag(True, f'构建摘要: chunk {len(all_chunks)}·前注覆盖 {_cov}·前注新生成 {_pfx["made"]}'
               f'·跳过(未变更) {_pfx["skipped"]}·superseded {_sup}')


def load_index():
    """加载索引（向量 + 元数据·校验一致性）。"""
    import numpy as np
    if not VECTORS.exists() or not META.exists():
        return None, []
    vectors = np.load(str(VECTORS))
    metas = []
    with open(META, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                metas.append(json.loads(line))
    # 一致性校验（防写半崩溃·vectors/meta 行数不匹配 → 提示 --rebuild）
    if len(vectors) != len(metas):
        _tag(False, f'索引不一致（向量 {len(vectors)} vs 元数据 {len(metas)}）·请跑 --rebuild')
        return None, []
    return vectors, metas


# 模块级模型单例（lru_cache·防每次 search 冷加载 16-23s）
_model_cache = None
_bm25_cache = None       # (bm25 实例, 活跃 chunk 下标数组)——运行时构建（364 段 <1s·零索引格式变更）
_BM25_MODE = os.environ.get('RAG_SEARCH_MODE', 'rrf')     # dense|bm25|rrf——消融开关·默认 rrf（融合终态）
_RRF_K = 60             # RRF 常数（业界标准起步·观测参数·系数不拍死）
_RRF_W_DENSE = 1.0      # 稠密路权重（消融观测参数）
_RRF_W_BM25 = 0.5       # BM25 路权重（等权=1.0 时 noun -7.2pp·降半权防稀释）


def _hub_penalty(m):
    """语义枢纽 chunk 降权系数（基线 §2.2 实证：身份卡 10/10 miss 的 top1 占位者）。

    EMC-IDENTITY-* 身份卡含「情绪地图/得分/指标」高频词——稠密与 BM25 双路都吸。
    它是库的「关于页」不是专项答案源；降权不排除（叙述类仍可用）。"""
    src = m.get('source', '')
    if 'EMC-IDENTITY' in src:
        return 0.2
    return 1.0


def _get_model():
    global _model_cache
    if _model_cache is None:
        # local_files_only=True：模型已缓存（~/.cache/huggingface/hub·92M）·禁联网检查——
        # 否则启动时 HEAD hf-mirror.com 超时重试 5 次（~30-60s+·2026-08-12 实测）·网络不通则启动卡死
        _model_cache = _load_st_model(local_files_only=True)
    return _model_cache


def _get_bm25(metas):
    """运行时构建 BM25（jieba 分词·superseded 预置过滤·缓存复用）。

    PT-CB9 泳道②件①：字面精确匹配路——治「精确术语被语义枢纽身份卡顶位」
    （基线 10 miss 中 5 条该模式）。小语料 364 段构建 <1s，故选运行时构建零索引格式变更。
    superseded 过滤（loader 契约：检索层职责·字段缺失=active 兼容）。"""
    global _bm25_cache
    if _bm25_cache is not None and _bm25_cache[2] == id(metas):
        return _bm25_cache[0], _bm25_cache[1]
    import jieba
    from rank_bm25 import BM25Okapi

    active = [i for i, m in enumerate(metas) if m.get('status', 'active') == 'active']
    corpus = [list(jieba.cut_for_search(
        metas[i].get('text', '') + ' ' + (metas[i].get('ctx_prefix') or '')))
        for i in active]
    bm25 = BM25Okapi(corpus) if corpus else None
    _bm25_cache = (bm25, active, id(metas))
    return bm25, active


def warmup():
    """serve 启动预热 RAG 模型（CB-22 EMC 修复 R1·消除首检冷加载 18.6s）。

    复用 _get_model 单例（首次调用触发加载 + 缓存）·幂等（已缓存直接返回）。
    失败不抛（调用方异步线程·降级为首次检索冷加载兜底）。
    不加新 @track ID（与 F_014/F_015 同族·Codex 建议避免占号）。
    """
    try:
        _get_model()
        _tag(True, 'RAG 模型预热完成')
    except Exception as e:
        _tag(False, f'RAG 预热失败（非阻塞·首检冷加载兜底）: {str(e)[:60]}')


@track('MOD_AIQA.F_015', track_args=False)
def search(query, k=5):
    """检索 Top-K（余弦相似度 + BM25 字面路·返回片段 + 来源·含数据维度）。

    消融开关 RAG_SEARCH_MODE：dense（默认·纯稠密）/ bm25（纯字面）/ rrf（两路融合·件②）。
    superseded chunk 预置过滤（loader 契约·字段缺失=active 兼容）。
    PT-CB9R-B3：返回顶层带 suppressed_count（本次被 superseded 过滤条数·active_idx 过滤处观测·纯计数不改过滤）；
    条目不对称治理标注——X-01 关联历史叙述类带 caliber_note·现行条目零标签（确定性零 LLM·不改排序）。
    """
    import numpy as np

    vectors, metas = load_index()
    if vectors is None or len(metas) == 0:
        return {'ok': False, 'error': '检索暂不可用（索引未构建·跑 py tools/rag_index.py --build）'}

    # superseded 预置过滤（两路共用·检索层职责）
    active_idx = [i for i, m in enumerate(metas) if m.get('status', 'active') == 'active']
    if not active_idx:
        return {'ok': False, 'error': '检索语料为空（全部 chunk 为 superseded）'}

    # PT-CB9R-B3：suppressed_count 观测（仅计数·过滤行为零改动）
    _suppressed = len(metas) - len(active_idx)

    if _BM25_MODE == 'bm25':
        bm25, bm25_active = _get_bm25(metas)
        if bm25 is None:
            return {'ok': False, 'error': 'BM25 语料为空'}
        import jieba
        q_tokens = list(jieba.cut_for_search(query))
        scores = bm25.get_scores(q_tokens)
        order = sorted(range(len(bm25_active)), key=lambda j: scores[j], reverse=True)[:k]
        top_idx = [bm25_active[j] for j in order]
        top_scores = [float(scores[j]) for j in order]
        results = []
        for rank, i in enumerate(top_idx):
            _entry = {
                'score': top_scores[rank],
                'source': metas[i].get('source', ''),
                'type': metas[i].get('type', ''),
                'data_dim': metas[i].get('data_dim', '社区'),
                'text': metas[i].get('text', ''),
                'region': metas[i].get('region', ''),
                'topic': metas[i].get('topic', ''),
                'year': metas[i].get('year', ''),
                'keywords': metas[i].get('keywords', ''),
            }
            _note = _history_note(_entry['source'], metas[i].get('lineage'))   # PT-CB9R-B3
            if _note:
                _entry['caliber_note'] = _note
            results.append(_entry)
        return {'ok': True, 'results': results, 'count': len(results),
                'suppressed_count': _suppressed}

    model = _get_model()
    qvec = _embed_texts(model, [query])[0]
    scores = vectors @ qvec
    raw_cos = scores.copy()   # PT-CB9R A-2：加权/枢纽降权前的原始余弦（dense_score 透传·消费方置信信号用·纯增量不改排序）
    # CB-22f D5（glm/Codex 共识·P1）：混合检索 fact 加权 ×1.2——fact 短文本向量信号弱·加权提升命中率·
    #   可观测参数（黄金集 Recall@5 跟踪·不拍死·Codex「系数作观测起步」）。
    for i, m in enumerate(metas):
        if m.get('type') == 'fact':
            scores[i] = float(scores[i]) * 1.2
        scores[i] = float(scores[i]) * _hub_penalty(m)

    if _BM25_MODE == 'rrf':
        # RRF 融合（Reciprocal Rank Fusion·k=60·两路等权起步）
        # 稠密路=余弦+fact×1.2（既有加权保留）；BM25 路=字面精确；overfetch k*4。
        bm25, bm25_active = _get_bm25(metas)
        if bm25 is None:
            return {'ok': False, 'error': 'BM25 语料为空（无法 RRF 融合）'}
        import jieba
        q_tokens = list(jieba.cut_for_search(query))
        bm25_scores = bm25.get_scores(q_tokens)
        dense_ranked = sorted(active_idx, key=lambda i: scores[i], reverse=True)[:k * 4]
        bm25_ranked_pos = sorted(range(len(bm25_active)),
                                 key=lambda j: bm25_scores[j], reverse=True)[:k * 4]
        fused = {}
        for rank, i in enumerate(dense_ranked):
            fused[i] = fused.get(i, 0.0) + _RRF_W_DENSE / (_RRF_K + rank + 1)
        for rank, j in enumerate(bm25_ranked_pos):
            i = bm25_active[j]
            fused[i] = fused.get(i, 0.0) + _RRF_W_BM25 / (_RRF_K + rank + 1)
        # 枢纽降权在融合分上做（RRF rank-based·稠密路乘常数不改序·此处才有效）
        for i in list(fused):
            fused[i] *= _hub_penalty(metas[i])
        top_idx = sorted(fused, key=fused.get, reverse=True)[:k]
        results = []
        for i in top_idx:
            _entry = {
                'score': round(float(fused[i]), 6),
                'dense_score': round(float(raw_cos[i]), 6),   # PT-CB9R A-2：原始余弦（置信信号·RRF 分为秩融合分不承载语义）
                'source': metas[i].get('source', ''),
                'type': metas[i].get('type', ''),
                'data_dim': metas[i].get('data_dim', '社区'),
                'text': metas[i].get('text', ''),
                'region': metas[i].get('region', ''),
                'topic': metas[i].get('topic', ''),
                'year': metas[i].get('year', ''),
                'keywords': metas[i].get('keywords', ''),
            }
            _note = _history_note(_entry['source'], metas[i].get('lineage'))   # PT-CB9R-B3
            if _note:
                _entry['caliber_note'] = _note
            results.append(_entry)
        return {'ok': True, 'results': results, 'count': len(results),
                'suppressed_count': _suppressed}

    # superseded 过滤后的稠密排序（active_idx 白名单内取 top-k）
    order = sorted(active_idx, key=lambda i: scores[i], reverse=True)[:k]
    top_idx = order
    results = []
    for i in top_idx:
        _entry = {
            'score': float(scores[i]),
            'dense_score': round(float(raw_cos[i]), 6),   # PT-CB9R A-2：原始余弦（置信信号·score 含 fact×1.2/枢纽降权）
            'source': metas[i].get('source', ''),
            'type': metas[i].get('type', ''),
            'data_dim': metas[i].get('data_dim', '社区'),  # 数据维度（住房/小区/社区/街区/城区/城中村/方法论）
            # CB-22 三支柱修正：透传片段全文（老索引无 text → 空串·前端标注"片段缺失·请重建索引"）
            'text': metas[i].get('text', ''),
            # CB-22f D3：fact 结构化字段透传（识别层零 LLM 组装 ctx.extracted 用·仅 type=fact 有值）
            'region': metas[i].get('region', ''),
            'topic': metas[i].get('topic', ''),
            'year': metas[i].get('year', ''),
            'keywords': metas[i].get('keywords', ''),
        }
        _note = _history_note(_entry['source'], metas[i].get('lineage'))   # PT-CB9R-B3
        if _note:
            _entry['caliber_note'] = _note
        results.append(_entry)
    return {'ok': True, 'results': results, 'count': len(results),
            'suppressed_count': _suppressed}


def stats():
    """索引统计。"""
    vectors, metas = load_index()
    if vectors is None:
        _tag(False, '索引未构建（跑 --build）')
        return
    types = {}
    for m in metas:
        types[m['type']] = types.get(m['type'], 0) + 1
    _tag(True, f'向量数 {len(metas)}·维度 {vectors.shape[1]}·类型 {types}')


def _knowledge_sources(repo=REPO):
    """扫描 RAG 知识源文件（与 check_server_freshness 共用·PT-CB16 S2 抽公共函数）。"""
    out = []
    for rel, pat in (("docs/urban-renewal-plan", ".md"), ("DATA/THEME", ".md"),
                     ("ai_qa/outlet_kb", ".py")):
        root = os.path.join(str(repo), rel)
        for dirpath, _dirs, files in os.walk(root):
            if "_Retired" in dirpath or "_retired" in dirpath:
                continue
            for fn in files:
                if not fn.endswith(pat):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    out.append((fp, os.path.getmtime(fp)))
                except OSError:
                    continue
    return out


def _index_freshness(repo=REPO):
    """返回 (索引 mtime, 知识源列表, 最新知识源) ；索引缺失时首项 None。"""
    idx = os.path.join(str(repo), 'DATA', 'RAG', 'rag_index', 'vectors.npy')
    if not os.path.isfile(idx):
        return None, [], None
    idx_m = os.path.getmtime(idx)
    srcs = _knowledge_sources(repo)
    newest = max(srcs, key=lambda s: s[1], default=None)
    return idx_m, srcs, newest


def main():
    ap = argparse.ArgumentParser(description='RAG 向量索引工具')
    ap.add_argument('--build', action='store_true', help='构建索引')
    ap.add_argument('--rebuild', action='store_true', help='全量重建')
    ap.add_argument('--rebuild-if-stale', action='store_true', help='知识源新于索引才重建（PT-CB16 S2）')
    ap.add_argument('--query', type=str, help='检索 Top-K')
    ap.add_argument('--stats', action='store_true', help='索引统计')
    ap.add_argument('--k', type=int, default=5, help='Top-K')
    args = ap.parse_args()

    if args.rebuild_if_stale:
        idx_m, _srcs, newest = _index_freshness()
        if idx_m is None:
            _tag(False, '索引不存在——开始重建')
            build_index()
        elif newest and newest[1] > idx_m:
            _tag(True, f'知识源较新（{os.path.basename(newest[0])}）——开始重建')
            build_index()
        else:
            _tag(True, '索引新鲜（知识源无更新）·跳过重建')
    elif args.build or args.rebuild:
        build_index()
    elif args.query:
        r = search(args.query, args.k)
        if not r['ok']:
            _tag(False, r['error'])
        else:
            _tag(True, f'Top-{r["count"]} 检索结果:')
            for i, res in enumerate(r['results'], 1):
                print(f'  {i}. [{res["score"]:.3f}] {res["source"]} ({res["type"]}·维度={res.get("data_dim", "?")})')
    elif args.stats:
        stats()
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
