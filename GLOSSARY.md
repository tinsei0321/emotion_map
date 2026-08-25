# EMC 术语表（内部编号 → 业务名）

> 数据源=仓内权威注册点·确定性生成（`py tools/gen_glossary.py`）·generated from a87ae50。禁裸用编号（用户沟通纪律 2）——查不到编号含义先跑本生成器。

## R 规则号（全局调试记忆·细则见 docs/debug-memory.md）

**R1** 多入口工具必须逐入口验证；**R2** 列值匹配必须显式处理空值——静默丢数据是重罪；**R3** 地图显示错误按「数据 → 映射 → 渲染」三层排查；症状迁移 ≠ 修错方向；**R4** 着色驱动字段必须匹配数据语义——禁静默降级；**R5** bbox 中心 ≠ 空间归属点；**R6** 纸面推演穷尽后，trace + 端口是第一实证源；**R7** 旧进程载旧码——「修了还错」先问进程重启了吗；**R7.3** 磁盘 JS 新 ≠ 已开页面内存里的 JS 新（前端静态改动第三形态·PT-CB…；**R8** 验证测试忌与被验实现同构；**R8.1** R8 补充——验证矩阵三路：mock 正常链 × 真实数据链 × 边界实证（PT…；**R9** 复算落到单元粒度——全量清单 > 抽样样本；**R10** 同族 bug 反复发作者的根因是「修症状层没修语义层」；**R11** 块注释内禁止出现 `*/` 字样——前缀通配写法会提前闭合注释；**R12** 渲染投递通道三坑——SSE 长连接 × 单线程服务器 × 重放不去重（PT-CB…；**R13** dsh web profile 是 pnpm 管——插件必须登记进 packag…；**R14** dsh rc.8 三约束——仓外插件构建需登记 stub · client 模块…；**R15** dsh-better-sidebar 会拦截 `ctx.workspaces.o…；**R16** dsh web 必须从真实控制台窗口启动——无控制台环境会触发 node-pty…；**R17** 就绪探测必须验「真依赖」——no-cors opaque 探测对 502 也 r…；**R18** 重量级只读资产在服务启动时预热——请求期/进程级重复加载不是常态路径（PT-CB…；**R19** 跨机环境复刻先取「装成机器」的安装步骤实录（PT-CB8 E1·2026-08-…；**R20** batch 前台阻塞命令之后的段=死代码；新增段放阻塞命令之前并防 goto 跳…；**R21** 跨 shell 生成/调用 Windows 命令——CRLF 换行与引号转义双坑…；**R22** 全局配置文件会被工具静默改写——空值键覆盖系统级配置（PT-CB11·2026-…；**R23** 空间工具对输入层的隐式假设（几何类型/规模）必须显式守卫（PT-CB11·202…；**R24** 治理标注须引原文句子级语义；契约函数必须是唯一消费点（PT-CB9 泳道①②合流…；**R25** 通道测试≠行为测试——模型编排链路验收必含真实复杂问题×3（PT-CB14·20…；**R25** 多 Agent 并发仓的 git gc 是高危操作——死锁中断会连锁炸掉 ref…；**R26** 超时看门狗「有流量即续命」——预算检查必须在主循环内·禁只在静默超时分支（PT-…；**R27** 跨进程桥（JSONL/SSE）边界六坑——硬编码/行上限/取证工具/帧分隔/诊断…

## F_/D_ 工具号（register_track_id 注册表·按模块聚簇）

- **MOD_AIQA**（44F/0D）：F_001=select_template（承重路由：track+card→canonical template id，track_result 捕获决策）；F_002=build_agent_prompt（ReAct agent loop 每轮 prompt）；F_003=build_final_prompt（最终结论 prompt）；F_005=build_diagnose_prompt（承重 eval-anchor：6 字段问题理解卡，永不动内容）；F_006=build_field_infer_prompt（P2 字段语义推断）；F_007=build_deep_attribution_prompt（L4 深度归因·政策→情绪→项目闭环，lazy enrichment）；F_008=build_optimize_prompt（5.215 Prompt 优化·Flash 流式·不增维度·梳理已有要素）；F_009=build_fill_card_prompt（Phase B 极瘦填卡·select_candidates 预选→Flash 填卡）；F_010=build_diagnose_prompt_dispatch（Phase B+C 三路分派·5.242 数据感知 layer_meta）；F_011=build_plan_prompt（Phase C Pro 复合计划·产 chain）；F_012=select_candidates（0LLM 候选工具选择·模块九 D035-D038·Phase A 纯规则·5.242 context 接回）；F_013=lookup_place 工具契约（CB-15 P1·查地点：q 或坐标 → search + reverse 近邻）；F_014=build_rag_index（RAG 向量索引构建·本地 BGE·原子写·embed_hash）；F_015=rag_search（RAG 向量检索·余弦 Top-K·返回片段+来源）；F_016=_render_dimension_cannot（颗粒度原则·按数据源维度渲染不能越维声明）；F_017=post_rag_search（RAG 知识检索端点·开放语义·返回 Top-K + dim_counts）；F_018=query_knowledge_base（B 路径确定性事实卡查询·CB-22f D5）；F_019=fc_diagnose（FC 路由 SSE 生成器·tool_calls/tool_name/_fcError 可观测·CB-22g 手动埋点）；F_020=口径复核：读注册表作废值→扫素材→命中即fail清单；F_021=MCP list_data（数据说明书：点层+边界层目录·开卷定参）；F_022=MCP rag_query（带来源知识检索·v1 综合降级 deferred_v2）；F_023=MCP kb_facts（行业事实卡·真身签名直映 query/keyword/topic/limit）；F_024=MCP outlet_card（行业出口卡·确定性组装·对话级）；F_025=MCP zonal_stats（单元聚合·宏观/中观结论）；F_026=MCP buffer（缓冲影响圈·中观）；F_027=MCP rank（排序评价·最差/最好 Top-N）；F_028=MCP render_spec（图层图纸：dataset/inline→spec 落收件箱）；F_029=render 收件箱 watcher：扫描新 spec→推 SSE 队列（坏文件跳过并 log）·高频扫描（1s 周期）免 @track（PT-CB10 C2-8 纪律·见 AGENTS 埋点规则豁免条）；F_030=render dataset 取数：preset/点层→FeatureCollection·>2000 降级；F_031=MCP render_file（把文件现在显示到地图：服务端读取·≤60 内联/>60 自动登记临时 dataset·一步到位）；F_032=MCP emc_status（8080 地图服务就绪探测·入口向导流程轮询用·临时测试件·无 @track 明文豁免——轻探测件非业务逻辑·先例 F_029 豁免条·终审 N2 成文）；F_033=MCP grid_aggregate（方格网空间聚合·参数化替代 T8 脚本）；F_034=MCP compare_regions（≥2 区域同口径并排+差异·契约 boundaries 参数）；F_035=MCP hotspot_analysis（Gi* 逐点显著聚集·五档分类）；F_036=MCP nearest_analysis（最近邻锚定·k 近邻配对+投影米距）；F_037=MCP area_stats（面积占比统计·group_by 分组·km2）；F_038=MCP overlay_analysis（叠置交叉·面∩/∪/差/对称差+面积）；F_039=MCP trend_analysis（T1/T2/T3 三期时序对比·方向+幅度）；F_040=MCP report_assemble（综合报告组装·确定性零 LLM·四段结构）；F_041=post_dsh_engine（壳二期 BA：dsh headless 引擎端点·spawn dsh --profile emc-test 一次性问答·stdout 全量返回·无流式降级形态）；F_042=codex_bridge ask（PT-CB15 SPIKE→转正：Codex app-server 桥·stdio JSONL 常驻单例·；F_043=post_codex_engine（PT-CB15 SPIKE：Codex app-server SSE 引擎端点·bridge 事件流→text/event-stream·真流式 msg.delta 源）；F_044=MCP aggregate_export（全量聚合导出·③档工具化：服务端聚合+落盘+注册→dataset_id·治 cdh 只读沙箱脚本路径不可用）；F_045=codex_bridge _ensure_harness_home（2026-08-26 配置隔离：harness 自备 CODEX_HOME 自愈生成——
- **MOD_ANA**（5F/7D）：D_001=进度回调：SnowNLP批量分析循环；D_002=进度回调：run_pipeline透传callback到analyze_batch；D_003=run_full_pipeline L3 LLM语义增强块；D_004=run_full_pipeline L4 多维归因块；D_005=run_pipeline L3 字段合并块；D_006=run_pipeline L4 字段合并块；D_007=run_full_pipeline L3 多模态视觉分析块；F_007=分析器工厂函数（create_analyzer）；F_008=统一分析任务入口（run_analysis_task）；F_009=单阶段分析管道（run_pipeline）；F_010=导出分析结果CSV+GeoJSON；F_011=L2→L3→L4全阶段管道（run_full_pipeline）
- **MOD_APP**（17F/7D）：D_010=图层控制：单个图层圆点点击切换 visible；D_011=图层控制：[全部打开] 批量显示所有图层；D_012=图层控制：[全部关闭] 批量隐藏所有图层；D_013=主数据点层：_all_layers_hidden 隐藏主数据；D_020=A功能：解析矢量文件决策点；D_021=A功能：安全阈值校验 + 自动简化决策点；D_022=pydeck selection 事件检测与选中状态保存决策点；F_001=分析控制台子页面（?page=console）；F_002=主应用入口（地图浏览器 + 路由分发）；F_003=数据治理弹窗（L0→L1 治理管道）；F_004=注册/更新图层到 session_state；F_005=数据源选择弹窗；F_006=数据概览弹窗；F_007=数据表格弹窗；F_008=设置与调试弹窗；F_009=分析范围选择弹窗；F_010=底图切换弹窗；F_011=情绪分析弹窗；F_012=选中点详情卡片渲染（pydeck selection 事件 → 详情面板）；F_013=图层控制弹窗（[LY]）；F_017=A功能：获取图层默认样式（自动差异化配色）；F_018=A功能：解析上传矢量文件（GeoJSON/Shapefile/KML）；F_019=A功能：渲染单图层横条控件（名称+Switch+样式按钮）；F_020=A功能：渲染样式编辑面板（线宽/颜色/填充/不透明度）
- **MOD_EXPORT**（5F/0D）：F_001=DataFrame → CSV 导出；F_002=DataFrame → GeoJSON 导出（含 geometry 构建）；F_003=边界图层合并导出为 GeoJSON FeatureCollection；F_004=导出对话框预览（数据+边界统计）；F_005=图层导出（geojson/csv/shp.zip，含 CRS + 脱敏）
- **MOD_FIELD**（4F/2D）：D_001=LLM role 因低置信(<0.3)/无效被丢弃（不承重，防误导）；D_002=usage-guard 拒绝（结论层作空间操作输入·PT-CB2 T2 铁律7 机械化）；F_001=resolve_field_alias（⑤② 承重：field→实际列名 alias 解析，全域调用）；F_002=find_boundary_name_column（面层 nameField 优先级推断）；F_003=validate_llm_roles（FIELD_INFER choke point：LLM role 校验）；F_004=validate_input_usage（PT-CB2 T2 承重：铁律7 守卫——结论层拒绝作空间操作输入）
- **MOD_GEN**（1F/0D）：F_013=POI 核密度曲面 + 密度引导采样（v3.1）
- **MOD_GEOCODE**（4F/2D）：D_001=搜索源选择：本地命中阈值 vs 高德兜底；D_002=CRS 转换：regeo 入参 WGS84→GCJ-02；F_001=search_place 本地+高德 POI 搜索；F_002=geocode_address 高德正向地理编码；F_003=reverse_geocode 本地+高德逆地理编码；F_004=_amap_request 高德统一请求（注入 key+重试+缓存）
- **MOD_GOV**（4F/3D）：D_004=批量LLM分类调用 (llm_classify_batch)；D_005=合并LLM分类结果到DataFrame；D_006=筛选relevant+has_location；F_001=步骤1: 加载原始数据 + GCJ-02->WGS84->CGCS2000坐标转换；F_005=调用L2 SnowNLP分析管道；F_006=数据治理CLI入口 (薄包装, 调用 run_governance_pipeline)；F_007=L0->L1治理主管道 (API/CLI共用, run_governance_pipeline, 含LLM漏斗)
- **MOD_LLM**（7F/4D）：D_001=LLM retry 触发（pre-stream 失败，退避后重拨）；D_002=LLM fallback 切换 provider（重试耗尽或 4xx）；D_003=LLM 流中途失败（不重试不换家，交上层降级）；D_004=chat 总预算超时强制降级 + FC 流式 pre-stream 失败换家；F_001=LLM chat/completions（流式 SSE，provider-agnostic，V4）；F_002=chat_with_fallback（retry+fallback 编排，主链路+审查共用）；F_003=LLM chat_with_tools（function calling，非流式，v2 改良混合·CB-05 CR1 修：从 F_002 改避碰撞）；F_004=chat_with_tools_fallback（FC provider fallback·v3 C1·CB-05 CR1 新 ID 避碰撞）；F_005=LLMClient.chat_with_tools_stream（FC 流式·诊断思考可见·Hotfix R2 S7）；F_006=chat_with_tools_stream_fallback（FC 流式 provider 韧性·Hotfix R2 S7）；F_007=search_chat（增强 web_search 单发不重试·失败快速 fallback·CB-12 问题3）
- **MOD_LOADER**（1F/2D）：D_001=不支持的文件扩展名分支；D_002=NaN 坐标过滤兜底；F_001=统一数据加载入口（CSV/TSV/JSON/GeoJSON）
- **MOD_MAP**（6F/0D）：F_001=创建 pydeck 基础地图（支持暗色/亮色/卫星三档底图切换）；F_002=添加情绪点标记层（pydeck ScatterplotLayer + 五级极性）；F_003=添加行政区划边界叠加层（pydeck GeoJsonLayer），支持独立填充/线宽/颜色；F_004=添加热力图图层（pydeck HeatmapLayer）；F_005=添加多个矢量范围图层（每图层独立样式）；F_006=添加选中点高亮轮廓圆环（金色半透明圆环 + 中心微点）
- **MOD_MM**（6F/7D）：D_001=VisionAnalyzer API调用异常捕获；D_002=VisionAnalyzer JSON响应解析降级；D_003=OCRAnalyzer OCR API调用块；D_004=AudioAnalyzer ASR API调用块；D_005=merge_multimodal_to_df Vision字段合并块；D_006=merge_multimodal_to_df OCR字段合并块；D_007=merge_multimodal_to_df Audio字段合并块；F_001=VisionAnalyzer.analyze_single（单张图像视觉情绪分析）；F_002=OCRAnalyzer.analyze_single（单张图片OCR文字提取）；F_003=AudioAnalyzer.analyze_single（单个音频语音转文字）；F_004=多模态引擎工厂（create_multimodal_analyzer）；F_005=批量图像分析（analyze_images）；F_006=多模态结果合并到DataFrame（merge_multimodal_to_df）
- **MOD_PERF**（12F/0D）：F_001=加载百度热力点 + 文本池 + POI；F_002=坐标转换 WGS84->4546；F_003=注入字段（4×5 双层 + 极性 + 文本）；F_004=导出 L1 CSV + GeoJSON；F_005=主流程 3 快照循环；F_006=加载边界 cc/core/unit；F_008=jieba keywords + 季节话题；F_009=4×5 + 区域倾斜自检；F_010=百度去聚合散点（Poisson + jitter）；F_011=重点叙事区锚点迁移；F_012=L1∩中心城区 -> L2；F_013=大南门·二马路 L3+L4 sim 生成器（ABSA aspect + 政策→项目种子 + buffer 科学化）
- **MOD_PLACE**（5F/0D）：F_001=place 层数据加载（zone/POI/边界）；F_002=resolve_zone：POI/点 -> zone_id（subtag->keyword->边界->general）；F_003=classify_point：坐标 -> zone_id（边界 contains）；F_004=forward：本地 POI 模糊搜索；F_005=reverse：坐标 -> 最近 POI + 所在区
- **MOD_RANGE**（15F/1D）：D_010=顶点数超限 → 自动简化；F_001=列出可用矢量数据集；F_002=获取当前激活的边界路径；F_003=加载矢量文件 → {name: RangeConfig}；F_004=保存上传的矢量文件到 data/boundaries/；F_005=判断点属于哪些范围；F_006=按范围筛选 DataFrame；F_007=获取可用范围列表（供 UI）；F_008=获取边界文件 CRS 信息；F_009=获取边界 GeoJSON（地图叠加用）；F_010=统计 GeoJSON 顶点总数；F_011=道格拉斯-普克几何简化；F_012=矢量文件安全阈值校验 + 自动简化；F_013=读取预设范围 manifest（标注 available）；F_014=按 id 加载预设范围 → GeoJSON；F_015=保存上传 GeoJSON 为预设文件（激活按钮）
- **MOD_REL**（5F/2D）：D_004=批量 LLM 单批API请求+重试循环；D_005=批量 LLM 响应JSON解析降级；F_001=关键词预筛选（正负信号加权评分）；F_002=DeepSeek LLM 精分类（五要素城市感受）；F_003=两层漏斗完整过滤（关键词+LLM）；F_004=输出相关性统计报告；F_005=批量 LLM 分类（一次API调用处理50条）
- **MOD_RUN**（2F/0D）：F_001=Tkinter GUI 启动入口；F_002=CLI 命令行入口
- **MOD_SCRAPER**（2F/1D）：D_001=SSR数据提取成功/失败分支；F_001=小红书Spider初始化/搜索页抓取；F_002=小红书笔记详情页解析
- **MOD_SPATIAL**（9F/5D）：D_001=热点分析：自适应空间权重矩阵构建；D_002=热点分析：分类结果统计（hot/cold/ns）；D_003=地形：KDE 曲面 + 等值面提取参数；D_004=情绪地形：KDE 直方图网格化 + 可分离卷积平滑参数；D_005=CB-23 A1：方格网格显式 agg_cols 聚合（体检中文截断列→{col}_sum/_mean）；F_001=Getis-Ord Gi* 热点分析；F_002=Moran；F_003=行政单元聚合统计；F_004=H3 六边形网格聚合；F_005=缓冲区分析(覆盖范围)；F_006=固定方格网格聚合(标准网格)；F_007=情绪地形 KDE 等值面 mesh；F_008=⑤③ membership 分组聚合（点带 zone role 直接 groupby，非 sjoin）；F_009=情绪地形 DEM（KDE→terrarium RGB·setTerrain 连续曲面）
- **MOD_TRANSFORM**（6F/0D）：F_001=GCJ-02 → WGS84 坐标转换（精确迭代）；F_002=BD-09 → WGS84 坐标转换；F_003=WGS84 → BD-09 坐标转换；F_004=单点坐标转换入口（支持多源坐标系）；F_005=DataFrame 批量坐标标准化；F_006=获取平台坐标系信息
- **MOD_UI**（11F/0D）：F_001=注入 Design Token CSS 变量；F_002=注入全覆盖地图 CSS + JS；F_003=HUD 按钮统一样式 CSS；F_004=渲染 HUD 按钮；F_005=渲染图例叠加层；F_006=渲染标题栏；F_007=渲染极性统计面板；F_008=渲染极性分布图表；F_009=渲染空状态引导页；F_010=渲染数据摘要叠加层；F_011=渲染居中 Toast 通知

## 批次号（CB 讨论档案）

- **CB23** 中转站全局数据质量审计_修改Plan
- **CB24** 图数表叙事逻辑_评估
- **CB25** page2内容完善_评估
- **CB26** page2合并版_评估
- **CB27** page3安全韧性体检结果_评估
- **CB28** page4安全韧性市民反映_评估
- **CB29** 线二口径矛盾_审计
- **CB30** 12345有坐标点治理_plan审计
- **CB31** 地图底图策略_plan审计
- **CB32** page7问题需求小结_审计回应
- **CB33** page4page6命中体检对象_审计回应
- **CB34** page7表格结构视觉_评估
- **CB35** page7排序数据审计_评估
- **CB36** 体检点数据管线审计_plan
- **CB37** page7社区问题一览图_讨论发起
- **CB38** EMC全局系统审计_评估
- **CB39** 实施计划_反评价
- **CB40** EMC现状与目标差距_回应与交叉挑战
- **CB41** 体检点聚合双bug_问题描述与排查发起
- **CB42** 思维链成本诊断_契约与业界方案_评估讨论发起
- **PT-CB1** T3b干净环境设计
- **PT-CB2** T1执行记录
- **PT-CB3** EMC意图外置与需求契约_讨论发起
- **PT-CB4** dsh轻量批二派发单
- **PT-CB5** T3执行记录
- **PT-CB6** EMC入口插件_问题复盘与审计交接
- **PT-CB7** 增补批T10-T13_Toolbox契约与出图范式
- **PT-CB8** 双模结局plan_v0.9待讨论
- **PT-CB9** RAG重建实施计划_分工版_v1.1定稿
- **PT-CB10** 战略转向裁定_dsh归官方与MCP优先
- **PT-CB11** MCP工具丰富化与注入链路补全_任务书
- **PT-CB12** guard接线与ACP契约_任务书
- **PT-CB13** 进度契约派发单_Codex
- **PT-CB14** EMCxdsh工作状态审查报告
- **PT-CB15** 2026-08-25出图与口径Bug根因复核与修复计划书
- **PT-CB16** C2-4评估_cdh侧交互UI载体
- **PT-CB17** cdh产品层四问题治本执行记录
- **PT-CB18** W12-手册瘦身自证证据与去重清单
