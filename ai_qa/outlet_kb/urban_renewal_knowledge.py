"""城市更新知识事实卡（L1.5 数据层 · CB-22b/22c）。

从 L0 资料库（docs/urban-renewal-plan/ 提炼笔记）确定性提取的结构化事实卡——
供 B 路径 query_knowledge_base（确定性查询）+ RAG 向量化（rag_index _load_facts）共用。

**schema**：{id, city, region, topic, name, detail(≤80字), dimension, year, keywords, source}
- dimension：数据维度（住房/小区/社区/街区/城区/城中村专项/方法论）——颗粒度原则：结论细粒度=数据来源维度
- source：_INDEX 编号 / G 盘相对路径（可溯源·防张冠李戴）

**来源**：三组提炼笔记（claude/codex/glm·2026-08-09）·真实数据·非 LLM 编造。
"""
from __future__ import annotations

# CB-22f D5（B 路径收尾）：追踪埋点——query_knowledge_base 是公开函数（MOD_AIQA.F_018·CB-22g 修正：F_016 撞 build_outlet_schema._render_dimension_cannot·改 F_018 连续）
try:
    from core.tracker import track, register_track_id
except Exception:  # 独立调试兜底
    def track(*a, **k):
        def deco(f):
            return f
        return deco
    def register_track_id(*a, **k):
        pass

# CB-39 P0-2（原号补注册·@track 使用见 :270·CB-22g 定号 F_018 但漏 register）
register_track_id("MOD_AIQA.F_018", "query_knowledge_base（B 路径确定性事实卡查询·CB-22f D5）")

# ── 更新项目（PROJECTS）──────────────────────────────────────────
PROJECTS = [
    {'id': 'URP-P01', 'city': '宜昌', 'region': '中心城区', 'topic': 'project',
     'name': '2025-2027 城市更新项目（55 个）', 'detail': '55个·51.33亿：污水厂网一体16个20.14亿/葛洲坝12个11.07亿/夷陵12个6.15亿/红星路3个7.57亿/其他12个(43个·44.93亿)',
     'dimension': '片区', 'year': '2025-2027', 'keywords': '更新项目 城市更新项目 污水厂网一体 葛洲坝 夷陵三峡移民 红星路二马路',
     'source': '宜昌市中心城区城市更新专项规划260713（阶段性成果 PDF 版）·项目库章节（2026.7 最新版）', 'source_path': 'docs/urban-renewal-plan/_笔记/codex_0819_260713_2026-08-09.md#43',
     'version_note': 'CB-23 审计 P1：本 55 项目（260713·51.33 亿·项目级·污水厂网一体16）与 0819 P35 55 项目（三年行动·50.3 亿·14 片区聚合）数量巧合非同一批·引用前标注版本'},
    {'id': 'URP-P11', 'city': '宜昌', 'region': '中心城区', 'topic': 'project',
     'name': '2030 核心目标（老版口径）', 'detail': '2030核心目标(00-02老版·勿混55项目)：5重点片区+21片区+32城中村+1园4厂+43完整社区+10-15km²低效用地·2005前老旧小区全更新',
     'dimension': '片区', 'year': '2030', 'keywords': '2030 核心目标 完整社区 重点片区 城中村 低效用地 二马路 织布街 1园4厂 老旧小区',
     'source': '宜昌市中心城区城市更新专项规划0610（阶段性成果 PDF 版）·核心目标章节（2026.6 老版）', 'source_path': 'docs/urban-renewal-plan/_笔记/codex_0819_260713_2026-08-09.md#00-02(0610)'},
    {'id': 'URP-P02', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'project',
     'name': '葛洲坝片区更新项目', 'detail': '12 个·11.07 亿',
     'dimension': '片区', 'year': '2025-2027', 'keywords': '葛洲坝 项目 投资',
     'source': '宜昌市中心城区城市更新专项规划260713（阶段性成果 PDF 版）·项目库章节', 'source_path': 'docs/urban-renewal-plan/_INDEX#00-03(260713)'},
    {'id': 'URP-P03', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'project',
     'name': '危旧房改造', 'detail': '入库 4 栋 C/D + 45 栋危旧 + 36 栋非成套·16.4 亿',
     'dimension': '住房', 'year': '十五五', 'keywords': '危旧房 改造 投资',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    {'id': 'URP-P04', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'project',
     'name': '汉宜村安置房', 'detail': '1960 套·18.06 亿',
     'dimension': '城中村专项', 'year': '十五五', 'keywords': '汉宜村 安置 城中村',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    {'id': 'URP-P05', 'city': '宜昌', 'region': '老城中心', 'topic': 'project',
     'name': '老城中心片区更新', 'detail': '16 个·16.6 亿',
     'dimension': '片区', 'year': '2025-2027', 'keywords': '老城中心 项目 投资',
     'source': 'docs/urban-renewal-plan/_INDEX#00-03(260713)'},
    {'id': 'URP-P06', 'city': '宜昌', 'region': '红星路-二马路', 'topic': 'project',
     'name': '红星路-二马路历史文化街区', 'detail': '3 个·7.57 亿',
     'dimension': '街区', 'year': '2025-2027', 'keywords': '历史街区 二马路 投资',
     'source': 'docs/urban-renewal-plan/_INDEX#00-03(260713)'},
    {'id': 'URP-P07', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'project',
     'name': '静态交通停车场', 'detail': '40 个停车场·6200 泊位',
     'dimension': '城区', 'year': '十五五', 'keywords': '停车 停车场 泊位',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    {'id': 'URP-P08', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'project',
     'name': '完整社区建设', 'detail': '优先 16 个社区·约 2940 万',
     'dimension': '社区', 'year': '十五五', 'keywords': '完整社区 建设',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    # ── CB-22g 体检整合：治理项目库（对接体检→更新出口·空间落位增量）──
    {'id': 'URP-P09', 'city': '宜昌', 'region': '中心城区', 'topic': 'project',
     'name': '综合体检治理对策与项目库', 'detail': '好房子/好社区/好街区/好城区四大对策·32个重点项目库(建设内容/规模/责任单位)·对接体检→更新出口',
     'dimension': '片区', 'year': '2025', 'keywords': '治理对策 项目库 四好 体检出口 32个',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·对策与项目库', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#五'},
    {'id': 'URP-P10', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'project',
     'name': '葛洲坝片区治理项目19项', 'detail': '安全3(铁路大院原拆原建/前湾危改)/公服4/交通5(西坝慢行过江0.6km)/文化5(西坝环岛绿道6.5km)/空间增效2',
     'dimension': '片区', 'year': '2025', 'keywords': '葛洲坝 治理项目 19项 铁路大院 西坝绿道 西坝慢行',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·葛洲坝片区体检', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.5'},
    {'id': 'URP-P12', 'city': '宜昌', 'region': '中心城区', 'topic': 'project',
     'name': '停车专项治理项目83个', 'detail': '新增12539泊位/投资7.9亿·夷陵广场地下850/国贸南楼停车楼11层/三峡大学附中480·促共享21单位/优管理3处挪用',
     'dimension': '城区', 'year': '2025', 'keywords': '停车 专项 83个 泊位 夷陵广场 国贸南楼 共享',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·停车设施专项体检', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.6'},
]

# ── 体检指标数值（INDICATORS）────────────────────────────────────
INDICATORS = [
    {'id': 'URP-I01', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '结构安全隐患住宅', 'detail': '42 栋',
     'dimension': '住房', 'year': '2025', 'keywords': '结构隐患 危房 住宅',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I02', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '围护安全隐患住宅', 'detail': '454 栋',
     'dimension': '住房', 'year': '2025', 'keywords': '围护隐患 漏水 住宅',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I03', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '停车泊位缺口', 'detail': '140 个小区',
     'dimension': '小区', 'year': '2025', 'keywords': '停车 泊位 缺口 小区',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I04', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '小学学位缺口', 'detail': '31 所·李家湖 400 个',
     'dimension': '小区', 'year': '2025', 'keywords': '学位 小学 缺口',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I05', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '中学覆盖率', 'detail': '56.10%·生物产业园 0%',
     'dimension': '街区', 'year': '2025', 'keywords': '中学 覆盖率',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-I06', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'indicator',
     'name': '完整社区达标率', 'detail': '19%·仅 6 社区达标',
     'dimension': '社区', 'year': '2025', 'keywords': '完整社区 达标率',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    {'id': 'URP-I07', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'indicator',
     'name': '停车设施专项体检·泊位结构', 'detail': '92:6:2（不达标·标准≥85:10-15:≤5）',
     'dimension': '城区', 'year': '2025', 'keywords': '停车 泊位结构 体检',
     'source': 'docs/urban-renewal-plan/_INDEX#03-04(停车专项)'},
    {'id': 'URP-I08', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'indicator',
     'name': '低效用地面积', 'detail': '葛洲坝片区 285.9 公顷·工业占 54%',
     'dimension': '片区', 'year': '2025', 'keywords': '低效用地 面积 工业',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    # ── CB-22g 体检整合：指标空间落位（I01-I08 给总量·I09-I16 给空间分布·互补不删）──
    {'id': 'URP-I09', 'city': '宜昌', 'region': '西陵区', 'topic': 'indicator',
     'name': '结构隐患住宅·空间分布', 'detail': '42栋·西陵29栋(69%)云集街办24栋(57%)·二马路/新隆康路·伍家岗13栋·沿江老城集聚带',
     'dimension': '住房', 'year': '2025', 'keywords': '结构隐患 空间分布 西陵 云集街办 二马路 新隆康路 沿江老城',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·住房维度问题空间落位', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.1'},
    {'id': 'URP-I10', 'city': '宜昌', 'region': '西陵区', 'topic': 'indicator',
     'name': '围护隐患住宅·空间分布', 'detail': '454栋·西陵385栋(85%)夜明珠街办111栋(24%)西峡社区42栋·沿江老城带·伍家岗69栋',
     'dimension': '住房', 'year': '2025', 'keywords': '围护隐患 空间分布 西陵 夜明珠街办 西峡社区 沿江老城带',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·住房维度问题空间落位', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.1'},
    {'id': 'URP-I11', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'indicator',
     'name': '小学学位缺口·空间错配', 'detail': '6603个·31社区·伍家岗北部大缺口(岳湾路1184/八一路1059/胡家冲1016)·老城富余新城紧张',
     'dimension': '小区', 'year': '2025', 'keywords': '学位缺口 空间错配 伍家岗 岳湾路 八一路 胡家冲 老城富余新城紧张',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·小区维度学位空间分布', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#4.4'},
    {'id': 'URP-I12', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'indicator',
     'name': '中学服务半径盲区', 'detail': '覆盖率56.10%·生物产业园0%·伍家岗街办/宝塔河/伍家乡配置不足·北部居住斑块盲区',
     'dimension': '街区', 'year': '2025', 'keywords': '中学 服务半径 盲区 生物产业园 宝塔河 伍家乡 北部居住斑块',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·街区维度中学覆盖', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#4.5'},
    {'id': 'URP-I13', 'city': '宜昌', 'region': '西陵区', 'topic': 'indicator',
     'name': '停车泊位缺口·空间集聚', 'detail': '约29912个·西陵占63%(2.12万)·夜明珠/大公桥/西坝/学院老城·江山3791/白马山2600/山庄路2135',
     'dimension': '小区', 'year': '2025', 'keywords': '停车缺口 空间集聚 西陵 夜明珠 大公桥 西坝 学院 江山 白马山 山庄路',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·停车专项空间集聚', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.6'},
    {'id': 'URP-I14', 'city': '宜昌', 'region': '中心城区', 'topic': 'indicator',
     'name': '人口密度·空间失衡', 'detail': '0.67万/km²偏低·环城北路5.27万/km²过载·点军/猇亭/龙泉<0.2万稀疏·葛洲坝多社区>4万',
     'dimension': '城区', 'year': '2025', 'keywords': '人口密度 空间失衡 环城北路 点军 猇亭 龙泉 葛洲坝',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·城区维度人口密度', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.4'},
    {'id': 'URP-I15', 'city': '宜昌', 'region': '点军/猇亭', 'topic': 'indicator',
     'name': '消防站服务半径覆盖率', 'detail': '20.59%(不足)·点军覆盖率低·猇亭/伍家岗需小型消防站·建成区加密',
     'dimension': '城区', 'year': '2025', 'keywords': '消防站 服务半径 覆盖率 点军 猇亭 伍家岗 小型消防站 建成区',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·城区维度消防覆盖', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.4'},
    {'id': 'URP-I16', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'indicator',
     'name': '历史建筑空置·对象分布', 'detail': '29%(15处)·西坝甲街民居/履元里7号/汪家老屋/海声科技办公楼·葛洲坝2处空置100%',
     'dimension': '街区', 'year': '2025', 'keywords': '历史建筑 空置 对象分布 西坝甲街民居 履元里7号 汪家老屋 海声科技',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·街区维度历史建筑', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.3'},
]

# ── 体检问题清单（CHECKUP_ISSUES）──────────────────────────────
CHECKUP_ISSUES = [
    {'id': 'URP-C01', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'issue',
     'name': '葛洲坝体检问题·五大方面', 'detail': '既有建筑/完整社区/老旧街区/公服短板/基础设施',
     'dimension': '片区', 'year': '2025', 'keywords': '葛洲坝 体检 问题',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    {'id': 'URP-C02', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'issue',
     'name': '历史建筑空置率', 'detail': '100%·西坝甲街/皂角树民居未活化',
     'dimension': '街区', 'year': '2025', 'keywords': '历史建筑 空置 活化',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    {'id': 'URP-C03', 'city': '宜昌', 'region': '中心城区', 'topic': 'issue',
     'name': '未实施物业管理小区', 'detail': '273 个',
     'dimension': '小区', 'year': '2025', 'keywords': '物业 管理 小区',
     'source': 'docs/urban-renewal-plan/_INDEX#03-01(附件1)'},
    {'id': 'URP-C04', 'city': '宜昌', 'region': '中心城区', 'topic': 'issue',
     'name': '消防 5 分钟可达覆盖率', 'detail': '59.69%（标准 100%）',
     'dimension': '城区', 'year': '2024', 'keywords': '消防 覆盖 安全',
     'source': 'docs/urban-renewal-plan/_INDEX#03-06(2024体检)'},
    # ── CB-22g 体检整合：问题空间规律 + 成效对比（C01-C04 给现象·C05-C07 给空间规律/成效）──
    {'id': 'URP-C05', 'city': '宜昌', 'region': '西陵沿江带', 'topic': 'issue',
     'name': '安全隐患集聚带', 'detail': '安全耐久问题住宅高度集长江北岸沿江老城带·西密东疏/沿江密内陆疏·西陵核心-葛洲坝=整治重点',
     'dimension': '住房', 'year': '2025', 'keywords': '安全隐患 集聚带 沿江老城 西密东疏 沿江密内陆疏 西陵 葛洲坝 整治重点',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·安全耐久分布专题', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#4.2'},
    {'id': 'URP-C06', 'city': '宜昌', 'region': '中心城区', 'topic': 'issue',
     'name': '风险区域叠加识别', 'detail': '1781处点位(住房1057/小区707/街区14)+12345热线(市政257/停车104/公服76)·西陵老城=存量高地',
     'dimension': '城区', 'year': '2025', 'keywords': '风险区域 叠加识别 点位 12345热线 市政 停车 公服 西陵老城 存量高地',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·风险区域叠加识别', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#4.6'},
    {'id': 'URP-C07', 'city': '宜昌', 'region': '中心城区', 'topic': 'issue',
     'name': '上年度整治成效', 'detail': '2024年46项整治率61%(住房60/小区67/街区71/城区53)·适老化3678户/学位11027/托位1993/停车场6529泊位',
     'dimension': '方法论', 'year': '2024', 'keywords': '整治成效 整治率 适老化 学位 托位 停车场 2024',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·上年度整治成效', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#一'},
]

# ── 更新片区（PANELS）────────────────────────────────────────────
PANELS = [
    {'id': 'URP-A01', 'city': '宜昌', 'region': '中心城区', 'topic': 'panel',
     'name': '重点更新片区（5 个）', 'detail': '葛洲坝/老城中心/环三峡大学/滨江商务/小溪塔中心',
     'dimension': '片区', 'year': '2025-2030', 'keywords': '重点片区 更新',
     'source': 'docs/urban-renewal-plan/_INDEX#00-02/00-03'},
    {'id': 'URP-A02', 'city': '宜昌', 'region': '中心城区', 'topic': 'panel',
     'name': '更新片区（23 个）', 'detail': '0.5-3 平方公里·四大分类（功能活力/宜居品质/产业迭代/历史街区）',
     'dimension': '片区', 'year': '2026', 'keywords': '更新片区 分类 23',
     'source': 'docs/urban-renewal-plan/_INDEX#00-01(0809)'},
    {'id': 'URP-A03', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'panel',
     'name': '伍家岗重点更新片区（10 个）', 'detail': '滨江商务/五一广场/临江溪/双创产业园等·住区/园区/景区三类',
     'dimension': '片区', 'year': '十五五', 'keywords': '伍家岗 片区 10',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
]

# ── 案例方法论（CASES·由 case_library point 派生）────────────
CASES = [
    {'id': 'URP-K01', 'city': '湖北宜昌', 'region': '葛洲坝片区', 'topic': 'case',
     'name': '望洲岗原拆原建', 'detail': '坝坝会+入户+算账说服·全量评论流替代小样本问卷',
     'dimension': '方法论', 'year': '2025', 'keywords': '望洲岗 原拆原建 示范',
     'source': 'ai_qa/outlet_kb/case_library.py#yichang_wangzhou'},
    {'id': 'URP-K02', 'city': '上海', 'region': '上海市', 'topic': 'case',
     'name': '上海体检满意度调查', 'detail': '线上问卷+社区座谈·一表三清单·问卷低分项情绪定位',
     'dimension': '方法论', 'year': '2025', 'keywords': '上海 满意度 调查 方法论',
     'source': 'ai_qa/outlet_kb/case_library.py#shanghai_satisfaction'},
    {'id': 'URP-K03', 'city': '南京', 'region': '南京市', 'topic': 'case',
     'name': '南京大数据定位交通断点', 'detail': '大数据+问卷+踏勘·客观位置与主观感受双重证据',
     'dimension': '方法论', 'year': '2024', 'keywords': '南京 大数据 交通 方法论',
     'source': 'ai_qa/outlet_kb/case_library.py#nanjing_bigdata'},
    {'id': 'URP-K04', 'city': '广州', 'region': '广州市', 'topic': 'case',
     'name': '广州体检满意度调查', 'detail': '线上问卷+进社区意见征询+观察员·四好框架·青年专项对焦',
     'dimension': '方法论', 'year': '2025', 'keywords': '广州 满意度 四好 方法论',
     'source': 'ai_qa/outlet_kb/case_library.py#guangzhou_satisfaction'},
    {'id': 'URP-K05', 'city': '宁夏', 'region': '宁夏', 'topic': 'case',
     'name': '宁夏编制导则标准', 'detail': '专项规划/片区策划成果标准表格图件·图文字数一致',
     'dimension': '方法论', 'year': '2024', 'keywords': '宁夏 编制导则 标准 方法论',
     'source': 'ai_qa/outlet_kb/case_library.py#ningxia_guideline'},
]

# ── 政策要点（POLICIES·gist 级）────────────────────────────────
POLICIES = [
    {'id': 'URP-L01', 'city': '国家', 'region': '全国', 'topic': 'policy',
     'name': '城市更新行动意见', 'detail': '专项规划-片区策划-项目实施方案三级体系·8 大任务',
     'dimension': '方法论', 'year': '2025', 'keywords': '城市更新 意见 三级体系',
     'source': 'docs/urban-renewal-plan/_INDEX#01-01(中办国办)'},
    {'id': 'URP-L02', 'city': '国家', 'region': '全国', 'topic': 'policy',
     'name': '防止大拆大建', 'detail': '拆≤20%·拆建比≤2·就地就近安置≥50%',
     'dimension': '方法论', 'year': '2021', 'keywords': '大拆大建 底线 拆建比',
     'source': 'docs/urban-renewal-plan/_INDEX#01-02(建科63号)'},
    {'id': 'URP-L03', 'city': '国家', 'region': '全国', 'topic': 'policy',
     'name': '城市更新专项规划编制导则', 'detail': '规划期 5 年·适用 4 类城市·内容 7 项',
     'dimension': '方法论', 'year': '2025', 'keywords': '编制导则 46号 专项规划',
     'source': 'docs/urban-renewal-plan/_笔记/glm_05编制导则'},
    {'id': 'URP-L04', 'city': '宜昌', 'region': '宜昌', 'topic': 'policy',
     'name': '宜昌城市更新行动方案', 'detail': '"1+4+N"机制·三个聚焦·危旧房市场化路径',
     'dimension': '方法论', 'year': '2025-2027', 'keywords': '宜昌 行动方案 1+4+N',
     'source': 'docs/urban-renewal-plan/_INDEX#01-11(宜昌行动方案)'},
]

# ── 指标体系（METRICS_SYSTEM·框架与数值分离）────────────────────
METRICS_SYSTEM = [
    {'id': 'URP-M01', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'metric',
     'name': '片区体检指标（20 项）', 'detail': '既有建筑/老旧小区/完整社区/老旧街区/公服/基础设施/生态/历史 8 方面',
     'dimension': '方法论', 'year': '2025', 'keywords': '体检指标 20项 片区',
     'source': 'docs/urban-renewal-plan/_INDEX#03-05(葛洲坝)'},
    {'id': 'URP-M02', 'city': '宜昌', 'region': '伍家岗区', 'topic': 'metric',
     'name': '区十五五指标（40 项）', 'detail': '住房保障/城市宜居/市政设施/城市韧性 6 大类',
     'dimension': '方法论', 'year': '十五五', 'keywords': '伍家岗 40项 指标',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(伍家岗十五五)'},
    {'id': 'URP-M03', 'city': '宜昌', 'region': '中心城区', 'topic': 'metric',
     'name': '更新指标（21 项细化）', 'detail': '安全韧性 10/服务群众 6/赋能潜力 5·危旧房 294→386 等',
     'dimension': '方法论', 'year': '2027-2030', 'keywords': '更新指标 21项 细化',
     'source': 'docs/urban-renewal-plan/_INDEX#00-04(说明书0714)'},
    # ── CB-22g 体检整合：片区概况 + 指标体系框架（出口卡片 context layer）──
    {'id': 'URP-M04', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': 'metric',
     'name': '葛洲坝片区概况', 'detail': '13.93km²·17.2万人·密度1.4万/km²(逼近1.5上限)·老龄化32.9%(重度)·2000前住宅62.9%·低效用地2.95km²',
     'dimension': '方法论', 'year': '2025', 'keywords': '葛洲坝 概况 面积 人口 密度 老龄化 2000前住宅 低效用地',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·葛洲坝片区体检', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#3.5'},
    {'id': 'URP-M05', 'city': '宜昌', 'region': '中心城区', 'topic': 'metric',
     'name': '城市体检指标体系（77项）', 'detail': '77项=住建部基础60+湖北省自选9+宜昌特色8·四维度(住房9/小区12/街区10/城区45)·数据时点2024-12-31·8302栋/1075小区',
     'dimension': '方法论', 'year': '2025', 'keywords': '体检指标体系 77项 住建部基础 湖北省自选 宜昌特色 四维度 8302栋 1075小区',
     'source': '宜昌2025年度城市体检全维度整合梳理（03-07）·77项指标总表', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-07_宜昌2025年度城市体检全维度整合梳理.md#二'},
]


# ── EMC 身份卡（PT-CB6 EMC 入口重定义 · 2026-08-20；PT-CB7 T5+T9 扩写·能力/边界/口径纪律）──
IDENTITY = [
    {'id': 'EMC-IDENTITY-01', 'city': '宜昌', 'region': '全局', 'topic': 'identity',
     'name': 'EmotionMap Copilot（EMC 情绪地图助手）',
     'detail': ('你好，我是 EmotionMap Copilot。用情绪地图看懂市民心声——问区域情绪、做空间分析、追原因与建议。'
                '【能做什么】基于多源市民诉求数据的城市情绪空间分析：七件标准工具——知识检索(rag_query)/行业事实卡(kb_facts)/数据清单(list_data)/行业出口卡(outlet_card)/单元聚合(zonal_stats)/缓冲影响圈(buffer)/排序评价(rank)，另可经 render_spec 出图到情绪地图前端；结论附口径引用义务。'
                '【不能做什么】不编造数字（无数据则明说）；usage=analysis_output 的结论层仅作展示、禁作分析输入；宏观情绪倾向不等于微观诊断，不做单点归因；不碰 EMC 前端 QA 管线。'
                '【口径纪律】引用数据必带 caliber 与口径注册表卡 ID（如 K-01/K-02）；社区口径枚举按 K-C1（174/154/118/130 等不得混用）。'
                '【交付纪律（T9）】所有数据类交付必带口径对照段：口径卡 ID + 子集声明（本结果≠全量）+ 覆盖说明。'),
     'dimension': '平台身份', 'year': '2026',
     'keywords': '你是谁 EmotionMap Copilot EMC 情绪地图 身份 自我介绍 能力 边界 口径纪律 口径对照 七件工具',
     'source': 'PT-CB6 EMC 入口重定义任务书（Codex 设计·2026-08-20）；PT-CB7 T5+T9 扩写（2026-08-21）',
     'version_note': 'PT-CB7 T5：原卡仅欢迎卡文案，本次原地扩写能力/边界/口径纪律（M4 审计裁定·不新增重复卡）；T9 交付口径对照纪律并入本卡'},
]



def all_facts():
    """全部事实卡（供 query_knowledge_base / rag_index 检索）。"""
    return (IDENTITY + PROJECTS + INDICATORS + CHECKUP_ISSUES + CHECKUP_FACTS + PANELS + CASES + POLICIES + METRICS_SYSTEM)


@track("MOD_AIQA.F_018", track_args=False)
def query_knowledge_base(query='', city='宜昌', topic=None, keyword=None, limit=5):
    """B 路径：确定性查询事实卡（关键词精确 WHERE·非向量·CB-22f D5 收尾）。

    场景：精确数字类问（"55 个分别是什么"/"葛洲坝几个项目"）——向量模糊时·确定性兜底。
    匹配链：① 关键词命中 fact 的 keywords/region/name/topic ② 再按 topic 过滤 ③ Top-N 兜底。
    返回与 RAG 结果同构（可混合注入 finalStep 素材）：[{id,name,detail,dimension,year,source,region,topic}]。
    """
    if not query and not keyword and not topic:
        return []
    facts = all_facts()
    if city:
        facts = [f for f in facts if f.get('city') == city or city in str(f.get('city', ''))]
    scored = []
    for f in facts:
        s = 0
        hay = ' '.join([str(f.get(k, '')) for k in ('keywords', 'region', 'name', 'topic', 'detail')])
        for kw in (keyword or '').split():
            if kw and kw in hay:
                s += 1
        if query:
            # query 清洗：去疑问词/量词 → fact 的 keywords/region 是否作为子串出现在 query 中（中文无空格·整串反查）
            #   「葛洲坝片区几个项目」→ 反查 fact keywords 含「葛洲坝」→ 命中（比正查稳·防滑窗噪音）
            _qclean = query.replace('有哪些', '').replace('是什么', '').replace('多少', '').replace('几个', '').replace('多少', '').strip()
            for _kw in (str(f.get('keywords', '')).split() + [str(f.get('region', ''))]):
                if len(_kw) >= 2 and _kw in _qclean:
                    s += 1
        if topic and topic == f.get('topic'):
            s += 2
        if s > 0:
            scored.append((s, f))
    scored.sort(key=lambda x: -x[0])
    return [{
        'id': f['id'], 'name': f['name'], 'detail': f['detail'], 'dimension': f.get('dimension', ''),
        'year': f.get('year', ''), 'source': f.get('source', ''), 'region': f.get('region', ''),
        'topic': f.get('topic', ''), 'keywords': f.get('keywords', ''),
    } for _s, f in scored[:limit]]


if __name__ == '__main__':
    facts = all_facts()
    print(f'[OK] 事实卡总数: {len(facts)}')
    from collections import Counter
    print('  分类:', dict(Counter(f['topic'] for f in facts)))
    print('  维度:', dict(Counter(f['dimension'] for f in facts)))
    # schema 校验
    for f in facts:
        for k in ('id', 'city', 'region', 'topic', 'name', 'detail', 'dimension', 'year', 'keywords', 'source'):
            assert k in f, f'{f["id"]} 缺 {k}'
        assert len(f['detail']) <= 80, f'{f["id"]} detail 超 80 字'
    print('[OK] 事实卡 schema 校验通过')

# ── CB-23 阶段2' 体检专题 fact（zcode 04_互通优化 机械转换·15条 CHK·detail≤80字·keywords数组→字符串）──
CHECKUP_FACTS = [
    {'id': 'CHK-I01', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '结构安全隐患住宅42栋', 'detail': '2025年体检识别结构安全隐患住宅42栋（西陵29/伍家13，云集街办24栋，86%超30年），违规拆承重24栋+混凝土裂缝19栋（1栋重叠去重）。',
     'dimension': '住房', 'year': 2025, 'keywords': '结构隐患 危房 承重墙 42栋',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I02', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '围护安全隐患住宅454栋', 'detail': '2025年体检识别围护安全隐患454栋（西陵385/夜明珠111/西峡42），屋面漏水245栋、渗漏152栋、外墙脱落严重62栋。',
     'dimension': '住房', 'year': 2025, 'keywords': '围护 漏水 外墙脱落 454栋',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I03', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '楼道安全隐患住宅242栋', 'detail': '2025年体检识别楼道隐患242栋（西陵191/东苑36/深圳路30），高层消火栓缺失或无水94栋、消防门损坏37栋、占道堆物42栋。',
     'dimension': '住房', 'year': 2025, 'keywords': '楼道 消火栓 消防通道 242栋',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I04', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '小学学位净缺口6603个', 'detail': '2025年体检小学学位净缺口6603个（31校超额7482减9校盈余879），大缺口集中伍家岗新城（岳湾路1184/八一路1059/胡家冲1016/花艳991）',
     'dimension': '小区', 'year': 2025, 'keywords': '学位 小学 入学 6603 7482',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I05', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '停车泊位缺口约2.99万个', 'detail': '2025年体检识别停车泊位缺口约2.99万个（61社区，西陵占约70%），江山3791/白马山2600/山庄路2135；西陵组团泊车比0.95、小溪塔0.81。',
     'dimension': '小区', 'year': 2025, 'keywords': '停车 泊位 2.99万 停车难',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I06', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '消防站覆盖率20.59%、高层预警11.6%', 'detail': '城区维度安全韧性短板：消防站服务半径覆盖率20.59%（点军低/猇亭伍家需小型站）、高层建筑智能火灾预警覆盖率11.6%（已建成高层配置低）。',
     'dimension': '城区', 'year': 2025, 'keywords': '消防 火灾预警 20.59% 11.6%',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I07', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '中学服务半径覆盖率56.10%', 'detail': '街区维度：中学服务半径覆盖率56.10%（覆盖15.80/28.16㎞²），生物产业园0%（无中学）、伍家岗/宝塔河/伍家乡配置不足，北部组团服务盲区。',
     'dimension': '街区', 'year': 2025, 'keywords': '中学 学区 56.10% 生物产业园',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I08', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '托育设施未达标34个社区', 'detail': '2025年体检识别婴幼儿照护设施未达标34个社区（西陵24占71%，西坝/葛洲坝街办各6个）；养老设施未达标2社区（云集二马路/赵家湾，附件3口径夷陵路）。',
     'dimension': '小区', 'year': 2025, 'keywords': '托育 婴幼儿 养老 34社区',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I09', 'city': '宜昌', 'region': '中心城区', 'topic': '城市体检',
     'name': '未实施物业管理小区273个', 'detail': '2025年体检识别未实施物业管理小区273个（西陵163占60%，云集街办52个、宝联社区25个），以老旧小区为主。',
     'dimension': '小区', 'year': 2025, 'keywords': '物业 无物业 273个',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I10', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': '城市体检',
     'name': '葛洲坝片区完整社区达标率19%', 'detail': '葛洲坝完整社区达标率19%（31社区仅6达标：刘家大堰/锦绣/石板溪/船柴/夜明珠/营盘路），三短板便民商业74%/公共活动空间65%/物业覆盖52%',
     'dimension': '小区', 'year': 2025, 'keywords': '完整社区 19% 葛洲坝',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-I11', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': '城市体检',
     'name': '葛洲坝片区概况13.93㎞²/老龄化32.9%', 'detail': '葛洲坝片区13.93㎞²、5街道33社区、人口17.2万、老龄化率32.9%（重度老龄化）、低效用地约2.95㎞²、2000年前居住建筑占62.9%。',
     'dimension': '片区', 'year': 2025, 'keywords': '葛洲坝 13.93 32.9% 老龄化',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-P01', 'city': '宜昌', 'region': '中心城区', 'topic': '城市更新项目库',
     'name': '体检32个项目库', 'detail': '体检附件5列32个项目库（住房8/小区11/街区8/城区5），结构隐患细化42栋名单，停车增补西陵20910+伍家9012泊位，无投资额字段',
     'dimension': '项目库', 'year': 2025, 'keywords': '项目库 32个 附件5',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-P02', 'city': '宜昌', 'region': '葛洲坝片区', 'topic': '城市更新项目库',
     'name': '葛洲坝片区19个治理项目', 'detail': '葛洲坝体检19个治理项目：安全防控3/公服提质4/交通优化5/文化活化5/空间增效2（前湾危旧房·黄河路西延·沙河公园·西坝环岛绿道6.5km）',
     'dimension': '项目库', 'year': 2025, 'keywords': '葛洲坝 19项目 治理项目',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-P03', 'city': '宜昌', 'region': '中心城区', 'topic': '城市更新项目库',
     'name': '停车专项83个项目/12539泊位/7.9亿元', 'detail': '停车专项83个增供给项目，新增泊位12539个、投资7.9亿元；亮点夷陵广场地下850泊位、国贸南楼停车楼11层、三峡大学附中地下480泊位',
     'dimension': '项目库', 'year': 2025, 'keywords': '停车 83项目 12539 7.9亿',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
    {'id': 'CHK-P04', 'city': '宜昌', 'region': '中心城区', 'topic': '城市更新项目库',
     'name': '2024年整治成效', 'detail': '2024年整治：危旧房581套、老旧小区311个、电梯402部、适老化3678户、学位11027个、托位1993个、公共停车场6529泊位、二马路一期10月完成',
     'dimension': '成效', 'year': 2024, 'keywords': '整治 成效 2024 二马路',
     'source': '宜昌2025年城市体检报告_材料通读摘要', 'source_path': 'docs/urban-renewal-plan/00-宜昌专项/03-08_宜昌2025年城市体检报告_材料通读摘要.md'},
]
