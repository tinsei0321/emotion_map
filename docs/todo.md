# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。
> 📝 详版历史 = [revision-log §5](revision-log.md#L226)（永久审计底）·本文件只记当前 + 计划。
> 📌 **架构版本**：v1（三阶段 5.231-5.242）→ **v2（单次 LLM + FC·5.243-5.245b·第三方实施）** → **v3（v2 做对·5.246-657c2e3·GLM 修复）** → **v3.1**（reg.filter 崩溃修复 + SCAN P1）→ **v3.2**（CB-09 bug 修复·D057 修订·代码自动扩展·全自动多步执行·fix/emc-buglog 分支 7 commit）→ **v3.5**（CB-10/CB-11 系列·merge 多图层 + 只说不做根治）

---

## 📅 2026-08-21（PT-CB7「稳定与灵魂」批主执行 · Qoder · 分支 `EMC_harness_dsh` · home 收工待 office 续点）

> 全天 home 班：审计先行 + T1-T21 大半销号 + 用户实测五连修 + dsh 两批回收；基线 442 passed/2 skipped；收工卡 `_handoff/HOME.md`。

### ✅ 已销号（commit 链 97fb95bd→28f78c63）

- ✅ T1 图层叠层自清理（`97fb95bd`）· T6 MCP 描述紧凑化（`0d752150`）· T8 800m 脚本参数化+口径对照段（`9e7ca1dc`）· T5+T9 身份卡扩写+RAG 364 条（`c6013cf8`）· T14 结果呈现契约§七（`1dc80123`）· T10 出图范式契约 render-contract.md（`a8a697e5`）。
- ✅ 用户实测五连修：T18 render_file 第 9 插座（“显示到地图”一步到位·治长思维+误入 Range·`3d80d2cd`）· T16 历史图层残留根治（applied/ 归档·`8608ff14`）· T19 /emc-ready 真就绪 gate+快通道+杀窗守卫（治“加载一半失效”·`23888cb3`）· T21 SSE 扇出广播+50s 豁免（治“F5 才见”·`691676ab`）· T15 start_silent.vbs 隐藏启动+对话气泡首屏卡（`fa661192`）。
- ✅ dsh 两批回收：批 1（T2 terminal chunk/T4 计时取证/F1-F4）；批 2（人设 prompt 落地生效·「你是谁」实测通过；T17 timeout 120s 无效→根因=MCP 冷启动 >120s）。

### 🔄 进行中 / ⬜ 待办（office 续点按序）

- ⬜ T17 服务端预热真修（MCP server 启动即预载 geo/RAG·设计后派 dsh）——第一优先。
- ⬜ T7 双模预设落地（emc-analysis 默认 low+工具子集 / emc-research max）+ ≤2min 验收跑（批 3）。
- ⬜ 五项用户实测验证（快通道/冷启动气泡卡/免 F5 铺层/render_file/身份自述）。
- ⬜ zcode 回收验收 + 《Qoder 执行效果评估》（对照 dsh 前几批）。
- ⏸️ 待裁决：T11 被 render_file 吸收待销项确认；D2 欢迎卡绑定目标会话；debug-memory 双 R11 撞号合并。
- ⏸️ 观察：render_file 临时 dataset（tmp_render_*）manifest 累积节奏。

---

## 📅 2026-08-20（PT-CB6 用户交互复测 + render 通道排障 · dsh · 分支 `EMC_harness_dsh`）

> 凌晨 home 班：用户亲测 Q2「12345 热线诉求最密集的 10 个社区是哪些？把结果铺到地图上」；端到端打通并修复渲染通道三个坑。

### ✅ Q2 端到端成图（用户复测通过）

- 结果：TOP10 社区（朝阳路 594 / 万达 501 / 港务 417 / 建设 372 / 岳湾路 225 / 大学路 222 / 伍临路 221 / 东城 191 / 张家湾 187 / 宝联 156）
- 铺图：`render_spec` 投递 `[dsh] [真实] 12345热线诉求最密集TOP10社区(真实)`（community_choropleth_v1·value_field=诉求总量·community=174）
- 最终采用**内联 GeoJSON**（`DATA/boundaries/presets/12345_top10_社区.geojson`）而不是 dataset_id 引用，避免浏览器二次取数排队

### ✅ 修复：前端 serve 单线程被 SSE 占死（严重）

- 现象：8080 页面能显示默认地图但一直转圈；`/api/v1/render/dataset/*` 全部 502/超时
- 根因：`frontend/serve.py` 用 `socketserver.TCPServer` 单线程；`render_client.js` 的 EventSource 长连接占死唯一请求线程
- 修复：`ReuseTCPServer` 改为 `socketserver.ThreadingTCPServer` + `daemon_threads=True`
- 验证：改后 8080 静态页、API、SSE 可并发响应

### ✅ 修复：SSE 重连重放 backlog 导致图层循环跳动（严重）

- 现象：8~9 个图层反复“删除→重建→缩放”，一直不停
- 根因：`render_client.js` 未按 `spec_id` 去重；EventSource 断线重连会把收件箱 backlog 重放，同批 spec 被反复应用
- 修复：`frontend/js/render_client.js` 增加页面会话级 `_seenSpecIds`，同一 spec_id 只应用一次
- 验证：无头浏览器连续 12s 采样，dsh 图层恒为 1 个，不再跳动

### ✅ 清理：render_inbox 历史测试 spec 移入 _backup

- 收件箱根目录原有 16 个 spec（含历史测试图层），全部重放造成图层爆炸
- 处理：除当前 TOP10 内联 spec `1787161960132-3411.json` 外，15 个旧 spec 移到 `DATA/exports/render_inbox/_backup/`（未删除）
- 验证：SSE backlog 只含 1 条 spec；页面只出现 1 个 `[dsh] [真实] 12345热线诉求最密集TOP10社区(真实)`

### ⚠️ 踩坑备忘（office 必读）

1. **单线程 HTTP 服务器不能挂 SSE 长连接**：serve.py 必须 ThreadingTCPServer；若再遇“页面转圈但静态可开”，先查 8080 是否被 SSE 占死。
2. **SSE backlog 重放必须客户端按 spec_id 去重**：否则重连即循环增删图层/缩放跳动。
3. **render_inbox 是运行时垃圾场**：测试 spec 会积压并在下次连 SSE 时全部重放；演示前应清空/移走旧 spec。
4. **zonal_stats 默认按 polarity_index 排序**，不是 point_count；“最密集/件数”类问题不要直接拿 zonal_stats top_n 当结论（PT-CB6 D1 已记）。
5. **dataset_id 引用在大图层/多 spec 并发时会排队超时**；关键演示图层优先用内联 GeoJSON（≤60 要素）。

---

### ✅ D 批打磨回收（office 班·zcode）

- 8 件全销号；主手抽验全过（D10 同源/D11 混配断言/D1 默认零退化）；门禁 434+2（上浮 7 注明）。
- **缺陷清单 D1-D13 收官**（D9 豁免裁决）。剩余收口=用户 Q3/Q4 复测+挂账顺修 6 项。

### ✅ Codex 全量审计回收 + D 批签发（office 班·zcode）

- 四线通过：CB6 主体（D9-D13 新缺陷·全 P2/P3）/ CB5 补审 / CB4 抽验 / **B1 正式销号**。
- 主手抽验五缺陷成立；D9 豁免裁决；D10 着色分派规格主手定稿（polarity→piToNorm 同源）。
- D 批 8 件签发（派发单 PT-CB6-D批派发单_zcode-2026-08-20.md·待转发 dsh）。
- 挂账顺修 6 项。

### ✅ S7 增量判读（office 班·zcode）

- D6-D8 三显示面缺陷验收通过并入清单（已修销号）；踩坑沉淀 debug-memory R11。
- 缺陷清单现状：D1-D3 待派、D4 待做、D5/D6-D8 已销。
- 下一步三选（用户定）：D 批打磨派发 / 用户复测 Q3-Q4 / B1 复审并入 CB6 期审计。

## 📅 2026-08-18（CB-41 体检点聚合双 bug 排查发起 · zcode · 分支 `EMC_harness_dsh`）

> 接 claude 交接（4 commit 待用户 push·对账无漂移·自检全过：生成器幂等 + presets 3 passed）。用户指派双 bug 修复线：① 体检点聚合着色反语义 ② tip 社区归属错乱。

### ✅ EMC×dsh 可行性深挖收工（revision-log 5.265·零实施·回家续读）

- dsh组 深挖完成：确认“情绪地图资产 + 标准插座”主路；建议补结果口径标签、数据说明书、知识综合；反对 dsh 专用插件/深嵌
- Codex 抽验完成：三项修正强吸收；纠正 dsh 仓库/破坏性变更/权限事实口径
- 外接大脑定位：零维护观察，不进产品排期；若未来转正必须专用最小权限环境
- 用户沟通纪律全局生效：面向用户禁裸用内部代号，先通俗系统讲解再给推荐
- 回家第一读：`docs/catch-ball/discuss/EMC-dsh可行性深挖_收工报告_通俗版_Codex-2026-08-18.md`
- 待确认：三张说明标签、外接大脑零维护观察、专用干净环境；新插座考试标准已初步接受；朋友每天使用 Codex+dsh 已确认
### ✅ 底图淡化 veil（revision-log 5.264·commit `2b2b3fe7`·数字框/双击路径待用户验收）

- 白罩层 `basemap-veil`（底图之上/分析层之下·世界 bbox 白填充）·0=默认全透·100=纯白底出图
- 控件：底图 popover 底部（滑条+数字框+百分比+双击归零）·localStorage 记忆；切底图携带+style.load 重敷双保险
- 踩坑 R11 入 debug-memory：块注释内 `*/` 提前闭合注释 → ESM SyntaxError 白屏（.mjs 强制解析才可检出）
- 机检：启动 ✓/滑条端到端 ✓（60%→opacity 0.6）/刷新恢复 ✓

### ✅ Layers 图层卡组策略 v2（revision-log 5.263·commit `5770ba5b`·拖拽视觉验收待用户）

- **模型**：渲染卡归属三级判定（真组成员 > `_cardCat` 覆写 > categoryOf 默认归集）——新层默认归集不变，拖拽=写可逆覆写；排序/z 序恒随 `_layers` 序
- **交互**：拖出行→上/下缘插入线；卡组头→「入组」高亮；空白处 drop→拖出独立（顶层游离行·锚定拖放位置）；跨卡组迁移/入真组（组头或成员行）；移除旧「同类别才能拖」限制
- **自动化**：空真组自动清除（Copilot 常驻）；迁移 toast 具体反馈；类目眼睛按渲染卡成员
- 验证：Node 逻辑测试 15/15 + 启动冒烟 + 语法双检；**拖拽交互需用户浏览器验收**

### ✅ 体检点全覆盖三图层入 Range 库（revision-log 5.262）

- `qty_合并`（2296 点）/`qty_安全_合并`（1350）/`qty_民生_合并`（946）→ 体检控件对象组·按类 8 量化预设块首；nameField=指标；灰点参考层流（grid/zonal 聚合源）
- 生成脚本 `SCRIPT/gen_checkup_point_presets.py` 幂等 + 口径锁定断言（点数/board 纯度）；`load_preset` 后端核验 ✓；presets 测试 3 passed

### 🔄 CB-41 双 bug 根因定位 + 台账 + dsh 排查发起（revision-log 5.257-5.260·**三轮修复已实施·待用户验收**）

- **B014 新立+修复**（08-18 增补·用户复测暴露）：`/spatial/aggregate` membership 值匹配静默丢点（异构属性点文件 74% NaN 被整行丢弃·2296→600·136/174 社区清零=中央无填充）。**修复**：混合策略（有值→值匹配/空值非 region→回退 sjoin/空值 region→丢弃）·CB-23 语义不变·12345 口径回归一致·pytest 372 passed
- **B013 新立+修复**（聚合着色）：后端计数无罪（复算=客观表头部逐字吻合）；L0 无极性点层 → grid-warm 色带高值浅金+零点最深红，与「点数越多越深」用户语义相反。**修复 `126537eb`**：grid 对话框「着色语义」显式分叉（点数(临时)/极性·默认随数据轨·手选锁定）+ `_count_norm` 计数着色（低浅高深）+ 零点透明 + zonal UI 自动分叉 + 图例/层名/tip 适配
- **B012 第 3 次复现+修复**（tip 社区错名）：归属点=要素 bbox 中心而非鼠标位置 → **34/174 精确清单**。**修复 `126537eb`**：社区面聚合层 tip 直读 properties.name（零查找）+ 网格/terrain 鼠标 lngLat 归属+节流 + point 分支清残留
- **边界**：ForAI 契约（generateGridForAI/generateZonalForAI）零变化·L2 极性色带/`_grid_h` 高度不动（dsh 排查报告三数字可信+三增量全采纳·收敛定稿 10 条裁定）
- 测试：新 `tests/test_zonal_count_semantic.py` 3 passed；全量 368 passed+3 skipped（1 failed 为 test_sandbox 既有脆弱性·与本次无关·单跑通过）
- **全局调试记忆库已建**（5.261·应用户要求）：`docs/debug-memory.md` R1-R10 踩坑规则·四挂载（AGENTS.md 知识源表+排查纪律 / KNOWLEDGE §1 红线×2+§2 卡 / context-map / dev-notes）·多组共享
- **待用户验收**（**先重启前端/后端进程**——8000 端口旧后端仍载旧码）：体检两方面合并点 174 社区聚合 → ① 中央密集社区（五龙/润城/深圳路）**深红且有点数** ② 零点社区（30 个）无填充仅描边 ③ 悬停 34 清单社区 tip=Table 行名·显「点数·N」 ④ 情绪 L2 极性图与 AI 入口如旧。验收通过后 B012/B013/B014 关账
- 编号账：CB-38 叙述的「B013=range tooltip」从未登记，本号归聚合着色；range tooltip 问题并入 CB-41 §2.4
- **用户拍板已入文档 §六**（5.258）：着色语义 UI 显式分叉（无极性→点数·有极性→极性·至少提示或可选·不静默切换）；无极性模式=临时分析出图（不做标准图例·不接 EMC 出口·ForAI 契约不动）

---

## 📅 2026-08-18（page7 TOP10 图层 + EMC×dsh 拍板待启 · claude · 分支 `EMC_harness_dsh`）

> 交接卡对账无漂移（`15468f62` 已推送·工作树净）；专题卡在「等用户三组拍板」（E4 形态3 / 并轨排期 / 外挂大脑）→ 拍板后出 CB-41。

### ✅ page7 数据图层：TOP20 社区（revision-log 5.256，commit `7ce68fbe` · **用户手动 push**）

- 脚本参数化 `TOP_NS=[10,20]` 幂等复跑；TOP20 续位 11-20（体育场路 136→柏临河路 88·第 20 名边界无并列 88 vs 83）
- 对账断言全量锁定（1-10 = 主观表头部·11-20 = 08-18 基线）；presets 注册 `page7_12345_top20`；测试 3 passed
- 叙事红利：11-17 名含 5 个两表重叠社区（宝联/体育场路/营盘路/胜利四路/汕头路）·与客观表叠加呼应

### ✅ page7 数据图层：12345 两方面诉求总量 TOP10 社区（revision-log 5.255，commit `f672f0a8` · **用户手动 push**）

- 两方面（民生基础+安全韧性）合计总量 TOP10 = 主观表头部 10 社区（朝阳路 594→宝联 156·含新区东城）；拆分点级核验（民生 5 类/安全 4 类）
- `DATA/boundaries/presets/12345_top10_社区.geojson`：**10 社区单面不合并**·属性含 排名/诉求总量/两方拆分/每周约件数；presets 注册 `page7_12345_top10`
- 生成脚本 `SCRIPT/gen_12345_top10_layer.py` 带对账断言（锁主观表头部·防口径漂移）；`test_range_selector_presets` 3 passed
- 踩坑复用：RAG 索引重建须 `HF_HUB_OFFLINE=1`（裸跑联网卡死 25min+·5.253 已记）；索引为本地产物（gitignore）

---

## 📅 2026-08-18~19（PT 平台化转型开工：CB1 开工轮→回口 / CB2 B1 批 T1 · zcode 主手+dsh 副手+Codex/claude 审计 · 分支 `EMC_harness_dsh`·main 冻结）

> 用户新协作体系（08-18 晚令）：zcode 主手（设计/拆解/派发/攻坚）·dsh 通用副手（非长思考任务·代码强）·Codex+claude 审计协助；每轮回收→收敛→拆解→派发→执行；新命名=任务代号+CB 轮次（PT-CB{n}·旧 CB 编号封存·CB-41 撞号化解）。

- [x] **PT-CB1 开工轮**：拍板生效落账/三日志（goal-status 增产品入口维度·G6-G9 改道）/CB41 草案转正 PT 总计划 v1.0/勘误归档批（dsh·12 项中 11 项销号）/审计章程+B6 反转主手认账（25% 实出自 CB-40 zcode 发起文档）/基线重录 372+3
- [x] **T2 G8a 契约派生**：stages.js 手写镜像退役→gen_stages_mirror.py+contract_mirror.generated.js；freshness diff=0 断言+别名派生等价+guard 差异冻结 8 项断言；根治 field_name→'field' 漂移 bug；375+3 零退化零新增 ID；Codex 审计零打回
- [x] **分支策略纠正**（用户）：实施一律走分支·main 冻结不动（08-18 晚误并已纠正认账）；全组切分支通知
- [x] **PT-CB2 开工（B1 批）+T1 回收**：dsh manifest 注册四件套（5→8 组/38→57 层/19 新注册/usage 45+12 全覆盖）+主手四裁决+qty 存量路径修复；审计顺延下轮（用户裁定）
- [ ] **office 续点**：①到岗 `git checkout EMC_harness_dsh && git pull`+`git push hub --all` 补推 ②PT-CB2 T2=usage 白名单消费点（geo_routes 输入校验+toolbox 链·zcode 攻坚·白名单开工前细化）③T1+裁决+T2 一并送审 ④之后 PT-CB3=B2 版本对账+B3 口径注册表/check_caliber（F_020 起取号）

## 📅 2026-08-17（EMC×dsh 合体讨论 R0-R3 · zcode·家 · 分支 `EMC_harness_dsh` · 纯讨论零实施）

> 用户设想「情绪地图整体寄生进 dsh」→ 四轮讨论后纠偏：真痛点 = EMC 入口聪明度不足。全部落盘 `discuss/EMC-dsh整体合体_讨论过程台账.md`（R0-R3）。

### ✅ page7 三调：两表口径取消双高（revision-log 5.254，commit `cd5f9a64` · **用户手动 push**）

- 客观线 ≥15 个问题点（48 社区）·主观线 ≥50 件诉求≈每周 1 件（47 社区）·**两表重叠恰好 10**（落图叠加目标）
- 网格搜索校准整数阈值；深浅档全整数+每周件数叙事（主观深档=每 2 天至少 1 件）
- 全链同步：csv + Excel 4 sheet + 两数据包 md + RAG 笔记 §四 + 索引重建

### ✅ RAG 知识库同步体检 2026 补充（revision-log 5.253，commit `74e5a2e2` · **用户手动 push**）

- 新建 03-10 蒸馏笔记（8 节·geojson/csv 禁入 RAG·只入知识）+ 口径优先级声明（压制 3prime 旧口径笔记）
- 索引重建 363 条（21.6s）；踩坑：build 未带 local_files_only 联网卡死 → HF_HUB_OFFLINE=1 解决
- 验证：特征查询命中 #1（0.737）；宽泛查询 fact ×1.2 加权属既有设计

### ✅ PPT 表格 Excel 同步（revision-log 5.252，commit `e7b169c5` · **用户手动 push**）

- `图数表出图_PPT表格汇总.xlsx` page1-6 全 sheet 重写（全覆盖+12345 扩域口径·表型保持）
- page3 润城/五龙登顶·表B 分母 100 社区；page4/6 表B ok精确 vs 区级拆分；page5 五类+四分类 TOP10
- 新建 `page7_分组汇总_2026-08-17_绝对值.xlsx`（61 高社区·3 sheet）——旧 08-14 密度版被取代（保留历史）

### ✅ 12345 主观轨扩域重算（revision-log 5.251，commit `9700daa1` · **用户手动 push**）

- 18,130 有坐标点 sjoin 174 社区 → 范围内 12,711（新区增量 1,569）；安全 1,951 图斑·129 社区 / 民生 10,758·148 社区；矩阵 154 社区（+36 新区）
- 区级点计图斑不进矩阵/TOP（修正区质心社畸高）；TOP 与旧版衔接 + 东城 26/165 双榜入 TOP10
- page7 重算：主观线 71.79@154 → **双高 3（+果园路）/ 客观高 31 / 主观高 27**
- 两数据包 md 同步（page4/6/7 全重写）

### ✅ 全覆盖范围面生成（revision-log 5.250，commit `893ffa80` · **用户手动 push**）

- 174 社区 dissolve 合并单要素面（无社区间分界线）→ `体检全覆盖范围_174社区合并面.geojson`
- 22 部分（跨江正常）·9 真实未覆盖洞·212.25 km²·<5000m² 尘埃/微缝已清·README 已登记

### ✅ 点数据清理：只留全覆盖（revision-log 5.249，commit `8e9f4c5f` · **用户手动 push**）

- 删 77项量化 分年点文件 19 个（2025 版 10 + 2026 版 9）→ 只留 11 个 `_全覆盖` 文件（2,296 点）
- 每点保留 `来源` 字段（2025体检/2026补充）·想看增量按它筛·不强制分开
- README 文件清单重写；删前 grep 验证无运行时依赖（presets 副本不受影响）

### ✅ 按 raw PDF（0817 版）逐页数据更新（revision-log 5.248，commit `e55061e1` · **用户手动 push**）

- 读 0817 raw PDF（8 页）：page8 = 三级统计逻辑表（26 图层/3,268 → 提取 1,685 → 落图 1,683）——按其数据类型逐页更新
- **page1**：体检成果叙事改"2025 西陵伍家 120 社区 + 2026 补充 38 社区 = 174 全覆盖达成"（实测 26,426 栋/22 街办/1,559 小区·与 PDF 微差如实注）
- **page3**：928→**1,344 图斑·100 社区**·TOP10 = 润城 102/五龙 88 登顶（新区 4 社区入榜）
- **page5**：757→**939·138 社区**·TOP10 峡江 35/五龙 24 入榜·营盘路占比降档系分母效应（如实注）
- **page7**：指向绝对值口径（5.247）；**page4/6 不变**（12345 未动）
- **page8**：逻辑表全更新（**42 图层/3,973 要素 = 提取 2,296 + 排除 1,677** + 2026 16 图层明细同表型）
- 数据包：`DATA/analysis/汇总/体检2026补充_按页数据更新_2026-08-17.md`

### ✅ page7 口径变更：绝对值 + 5 待拍板全裁定（revision-log 5.247，commit `ca653746` · **用户手动 push**）

- **用户裁定**：page7 弃"每百栋"取**社区内绝对值**·全 page 统一全域口径（效果不好再议）·无数据如实·步行道千米+处双给·缺口数值按真实
- 绝对值三类：客观线 ≥21 点（p81@174全域）·主观线 ≥74 件（p81@118有数据域）→ **双高 2（营盘路/宝联）/ 客观高 32 / 主观高 21**
- 与密度版差异：双高 5→2（汕头/胜利四/胜利二落主观高中档）·新区大户入客观高深档（五龙 112/润城 110/峡江 66）
- 步行道双数据：千米 = 仅 2025 报告值 2.09（2026 无长度·如实）；处 = 35 精准到社区
- 产出：`gen_page7_absolute_2026.py` + `page7_绝对值口径_全域_2026-08-17.csv` + 数据包 md §九

### ✅ 体检 2026 补充数据入库（revision-log 5.246，commit `d368a660` · **用户手动 push**）

- 2026 新数据（`3_gis数据/2026/`·16 图层全 Point）= **夷陵 342/点军 158/猇亭 111**——与 2025 西陵伍家**空间互斥纯增量**（0 点落入体检对象·合并直接相加）
- 提取 **611 问题点**（安全 422/民生 189·排除数字化+智慧化+绿色达标率 3 层）→ `checkup_qty_2026_*.geojson` 9 文件（schema 兼容 2025）
- 3 类/5 类矩阵 × {2026 增量·全覆盖} 4 csv（安全 928+416=1344·民生 755+184=939·原 2025 矩阵不动）
- 全覆盖检验：174 社区有问题点 144·零问题 30（24 西陵伍家+6 新区）·**6 项指标无新区图层**→「数据全覆盖 ≠ 问题全查清」
- **page7 西陵伍家口径完全不变**（实证 0 点落入）·page4/6 不动；page2/3/5 数值更新表已给
- 数据包：`DATA/analysis/汇总/体检2026补充_全域数据包_2026-08-17.md`（**结论留空·用户落图**·含 5 待拍板项：全域叙事口径/6 无图层指标/30 零问题确认/步行道单位/缺口数值类）


- [x] **R0** zcode 评估发起：方案A（整体寄生·六维反对）/方案B（工具级寄生·MCP server）+ 三组联合讨论 prompt 交用户投递
- [x] **R1** 三组回应回收（claude/Codex/dsh组·dsh组 经重邀回归）：**四决策点全一致**——D1 否决A / D2 立项B+spike / D3 MCP 唯一解（dsh 原生 MCP 客户端实锤·breaking 16/600 周级）/ D4 dsh组回归
- [x] **R2** 澄清轮：方案B 三层提升+核心改变=能力可达性与安全性（非能力新增）+四条诚实边界（EMC 产品本身零提升居首）
- [x] **R3** **纠偏轮（本轮转折）**：真痛点 = EMC 入口聪明度不足（意图→方法+工具路径不聪明·拆东墙补西墙）。机理四层（封闭分类法/单发诊断不可恢复/参数闭卷/eval 失真）+ reframe（灵活性归还入口端非中间开放）。**讨论稿落盘 `discuss/EMC-聪明路径_入口端灵活性_讨论稿_zcode-2026-08-17.md`**（四机制 M4→M2→M1→M3·E1-E3）
- [ ] **待用户拍板（office 继续）**：D1-D4（A/B/G10 线）+ E1-E3（聪明路径线：是否并入底稿专题会话/优先级 vs G1-G5/M1 交互形态）→ 两线收敛统一总优先级表

## 📅 2026-08-16（紧急任务收官 · 主线回归 CB-38 发起 · claude·家）

### 🔄 CB-38 主线回归与数据沉淀·讨论发起（纯讨论·零实施·`e1de81ac` 已推）

> 紧急任务（城市体检 PPT page1-7）全部完成收官。主线回归 RAG+EMC。用户纪律：「以后都不要急着动手，讨论清楚再开工」+ 今天任务全进 CB。

- [x] **任务① 数据沉淀梳理发起**：实测盘点 `DATA/analysis/` 93 文件 → 六数据族初步意见（空间底座→图层体系 / 体检专题+主观轨→「体检」域 / 更新→「更新」域 / page7 中间产物候选清理 / 成文分析 md=RAG 黄金素材）+ 焦点 F1-F5（留删 / RAG 层级·体检更新分域 / geojson 不进 RAG / 口径漂移防线 / PII+sim+铁律7 红线）。**用户新口径：体检（找问题需求）与更新（规建营项目）分开**
- [x] **任务② EMC bug 清单发起**：E1 社区 tip 错误（**buglog 零书面记录·需建条目+复现信息**）/ E2 office 底图仅天地图（Esri BLOCKED·国内源+自托管方向待议）+ 补充 E3-E7（manifest 404 / open bug×3+deferred×2 / CB 登记债 / tmp 脚本 / office 周一换绑）
- [x] **任务③ 下周排期**：城市体检时间轴工程（自由时间点·弃 T1~T3·重构整个时间轴·先列计划不展开）
- [x] **CB38 发起文档落盘推送**：`discuss/CB38-主线回归与数据沉淀_讨论发起_2026-08-16.md`（含 dsh组 onboarding 上下文·第四节）
- [x] **三组评估回收 + 收敛定稿**（12:24-12:30 三组齐）：全采纳（Codex 2 处推翻有据）·4 分歧裁定（归档不删/脚本退役/B002-B004 升 P0/分轴并存）·统一编号 E8-E15/N1-N7·`收敛定稿_2026-08-16.md` 落盘
- [x] **E1 根因实锤**（用户提供五组样本·系统化排障）：B012=格心归属（tip-popup.js:433·五组全相邻·400m 跨界格模拟复现·buglog 建条+审计脚本 `e0a01186`）；B013 新立=range tooltip 显图层名（map.js:1004·zcode 候选核实）
- [x] **E5 登记债清偿 + DoD 化**：cb-journal 补 CB-29~37 简记 + _cb-index 更新到 CB-38 + 每轮收敛必更固定条目
- [ ] **下一步：Codex 出 CB-39 实施计划**（下周排期 D1-D5·B002/B004 P0 前移·manifest 再生成须用户授权）
- [x] **CB-39 三方反评价已收敛**（Claude/zcode/Codex 审计线·`77520641`）：14 项 v3.1 变更单 + api.js 冲突实测裁定；**dsh 反评价缺位待用户处置**；Codex 出 v3.1 增量修订后待用户拍板开工
- [x] **P0-0 key 轮换：用户拍板暂缓**（2026-08-16·"暂不轮换没事"）——serve 暴露面已封堵（403 实测）·SOP 备用随时可做（`tools/KEY_ROTATION.md`·顺带确认 AMAP geocode 服务）·后续会话勿再催

### ⬜ 地图底图增强（另开会话实施·2026-08-16 用户定·本会话只收口）

> 用户需求：①新增 Esri 高清影像底图 ②地图右下角坐标/缩放/高程状态栏。home 先做看效果·office 探活自动灰显回退天地图（CB-31 框架现成）。

- [x] **esri-imagery 底图档已注册**（2026-08-16 收口）：`map.js` `_ESRI_IMAGERY`（World_Imagery·`{z}/{y}/{x}` 顺序·maxzoom 18）+ BASEMAPS + `_BASEMAP_BG['#23303c']` + index.html swatch 按钮 + dialog.css `.bm-esriimg`——**home 可直接选档验效果**（cb31 探活/灰显/回退 tianditu-img-nolabel 全自动）
- [ ] **coord-bar 状态栏（待另开会话）**：右下角 bottom:28px（legend-stack 60px 与 attribution 之间的空档）·mousemove→WGS84 经纬度 + zoom + 高程。**技术要点**：高程源 AWS Terrarium `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`（无 key 无配额·中国境内 SRTM~30m）；客户端采样（fetch PNG→离屏 canvas 读像素→瓦片 LRU 缓存 ~40·采样级 clamp z8-13）·**不挂 setTerrain**（不碰 08-05 DEM draping 承重）；**解码公式 `(R*256 + G + B/256) - 32768`（用户原案 B×256 是笔误·B 为 ÷256 细粒度项）**；office fetch 失败静默显 '—' 不 toast；3D pitch 下 e.lngLat 仍有效
- [ ] 验收：home 肉眼看影像清晰度/拼接色差 + 状态栏跟随；office 确认灰显回退 + 高程 '—' 降级

### ⬜ 初始载入界面「地球」动态展示（另开会话实施·2026-08-16 zcode 评估·**plan 已落盘待拍板·零实施**）

> 用户需求：初始页改为缓慢自转的地球 + 深邃太空背景（Google Earth 载入观感）；纹理跟随默认底图（①影像→真实地球 ②地图→maplibre.org 式地板版地球）；点「复位」按钮 flyTo 宜昌进主界面。**可行性结论：能实现**——vendored MapLibre **v5.2.0** 原生支持 globe 投影（零新依赖），天地图影像瓦片直接作纹理（office 网络也可用），`YICHANG` 常量现成（map.js:45）。
> **完整方案：`docs/globe-intro-plan.md`**（新会话先读它——架构/风险/工作量/验收/决策点全在内）。

- [x] 可行性评估 + 实施预案落盘（zcode·2026-08-16）：单 map 实例 + 载入态状态机（globe 自转 → 复位 flyTo 宜昌 → 落地切回 mercator 保零回归）；估算 1-1.5 天开发 + 0.5 天审查测试；关键承重项=测试基建须加 `?intro=0` 跳过参数（防飞轮用例红一片）
- [ ] **待用户拍板 D1-D5**（见 plan 第七节）：载入态侧栏隐藏 vs 虚化 / 复位按钮是否常驻主界面 / 星空基础版 vs 增强 / 飞入 ~3s vs ~1.5s / 是否加项目标题开场
- [ ] 拍板后：立独立 CB 轮次 → Codex 出实施计划 → 严格 SOP（控制流+多文件）实施；涉及 `frontend/js/globe-intro.js`（新·~200 行）+ map.js/main.js/index.html/css 小改

### ⬜ EMC harness 架构借鉴 dsh 专题（另开会话深入讨论·2026-08-16 zcode 底稿已落盘·**零实施**）

> 用户想法：「让 EMC 依托 harness+LLM+plugin 运作、模仿 dsh（https://github.com/deepseek-ai/deepseek-harness）重构，是否更智能灵活」。zcode 在线研读 dsh 四份核心文档后梳理的**核心结论**：EMC 已是该形式（Smart/Dumb/编排器内核=harness.js+19 契约工具+双 LLM 端），「重构为该形式」前提不成立；真正有价值=**三点定向借鉴**（G6 session log 可重放 / G7 守卫管线化 / G8 契约全自动派生）+ 条件性 G9（CPD 复活借 delegated turn）；明确反对换 Cordis 框架/开放 agent loop 替换确定性编排/推翻重写（B001/B003 病史背书）。
> **专题底稿：`docs/catch-ball/discuss/EMC-harness架构借鉴dsh_专题底稿_zcode-2026-08-16.md`**（新会话先读它——dsh 四支柱研读摘要/EMC 对照表/借鉴清单/反对项/五议题议程/D1-D3 决策点全在内）。

- [x] dsh 研读 + 对照梳理 + 专题底稿落盘（zcode·2026-08-16）
- [ ] **专题会话深入讨论**（用户另开会话）：按底稿第七节五议题推进（session log 设计 / 守卫管线 / 契约派生 / CPD delegated turn / G6-G9 与 CB-40 G1-G5 合并排序）；红线=diagnose prompt 永不动·编排器确定性·零实施
- [ ] 讨论收敛后：G6-G9 入 CB-40 缺口清单或独立 CB 轮 → 用户拍板 → Codex 出实施计划

---

## 📅 2026-08-15（双环境首次合流 · DEV-SYNC-HUB 接入 · Gitee 迁移 · claude·家）

### ✅ 双环境合流（office 25 提交 ↔ home 1 提交 · 零丢失）

- [x] **机制弄清 + 接入**：office 端部署的 `E:\DEV-SYNC-HUB`（Leave/Arrive/Status/Rescue 四入口 + 盘仓唯一真相源 + 四层兜底）；home 端 registry 登记完成（`LAPTOP-HB0DA58R` + 项目路径）
- [x] **昨日 home 自建同步工程退役**（`89ce0f2b`）：sync_guard.py / 双 bat / 规则文档 / SessionStart hook / _tmp 补丁全删，被 HUB + Gitee 方案取代；保留 .gitignore 防回流
- [x] **合流 office 领先 25 提交**（`3be6398c`）：CB36/37 + page7 三表/三类社区数据 + zonal 修复；零冲突（todo/revision-log 不同区域自动合并；CB 文档/脚本双侧同内容 add/add 自动消解）
- [x] **ec9c70e 悬空救援**：账本 13:28:15 记录的 office 真实末梢未落盘头（HUB 增量打包验证测试所致）→ 临时 ref 取回合流 → 事后清理；保证明日 office Arrive 纯快进
- [x] **三方一致** `87c31bdd`：本地 = 盘仓（Leave.bat 全分支+bundle+账本）= GitHub；main 维持 `4f6fac71` 未动
- [x] **同步报告**：`docs/sync-reports/2026-08-15_双环境合流同步报告.md`（机制解读/两侧清单/异常处置/勘误 08-14 记录）

### ✅ Gitee 迁移（origin 换绑完成 · `https://gitee.com/tinsei0321/emotion_map.git`）

- [x] **体积体检**：648MB（>500MB 提醒线 / <1GB 禁推线，可迁）；最大单文件 83MB `社区.geojson` < 100MB 拒收线；顺手清 268MB 中断 push 残留 tmp_pack（garbage 归零）
- [x] **全量推送**：2 分支 + 1 标签 → Gitee 校验一致（`codex/dsh-onboarding = ff1f7e26`、`main = 4f6fac71`）；upstream 已指向 origin(Gitee)
- [x] **双远端策略落地**：`origin` = Gitee（日常同步·office 可达）；`github` = GitHub（home 侧备份镜像，改名保留）；`hub` = 盘仓（HUB 备份层不变）
- [x] **MCP 换绑**：项目 `.mcp.json` 新增 `gitee`（官方 `mcp-gitee` v1.0.1·继承系统 env `GITEE_ACCESS_TOKEN`·`${VAR}` 中转映射实测不展开已弃用）+ `github` 停用（disabled=true 留配置备查）
- [ ] **office 明日换绑**：Arrive.bat 快进到最新 → `git remote set-url origin https://gitee.com/tinsei0321/emotion_map.git`（office 首推需私人令牌当密码）→ `memory-sync.bat pull` 恢复记忆 → Leave.bat
- [x] **用户侧账号操作**（2026-08-15 完成）：vscode GitHub 登出 ✓、私人令牌 setx `GITEE_TOKEN`+`GITEE_ACCESS_TOKEN`（后者 = mcp-gitee 实际变量名·server 纯继承启动实测通过，`/mcp` 内对 gitee 批准/重连即连）✓、Codex/ZCode 查明无独立 GitHub 绑定零动作 ✓

### ✅ C 盘对话 context / AI 记忆双机同步（三层记忆保护伞）

- [x] **机制启用**：DEV-SYNC-HUB 内置 `Memory.bat`（office 已部署·home 从未跑过=缺口）→ home 首推完成：6 工具 ~1.3GB 入 `memory\home\`（claude 267M / claude-global 4.5M / codex 385M / zcode 623M / vscode 5.5M / dsh 34M），账本 `MEMORY-push` 行落
- [x] **盲区一修补**：registry 补 `claude-global` 条目（全局 `~/.claude\CLAUDE.md`/skills/plans/settings 原不在同步范围）
- [x] **安全问题修正**：office 原配置漏排密钥——`codex/auth.json`（OAuth 令牌）/`zcode\v2\credentials.json`/`certs\zcode-network-ca.key+.pem` 已落盘两侧快照 → registry 排除表补齐 + 盘上 8 个凭据副本删除（源机器文件未动）
- [x] **Gitee 蒸馏层**（末日保险）：`tools/memory_sync.py` + `memory-sync.bat`（双击镜像 AutoMemory → repo `memories/auto/` + commit + 双远端 push）；首推 `3ad8b08d` 89 文件 1767 行；全量 context 明确不上云（密钥明文+GB 体积+jsonl 无合并意义）
- [x] **登记**：context-map 记忆共享通则（「AutoMemory 机本地已知局限」关闭）+ CLAUDE.md 第二层跨机同步注 + `memories/README.md`
- [x] **一键聚合**（用户反馈 3 bat 太繁琐）：盘专区新增 `一键离开.bat`（Leave+Memory+蒸馏层+origin 兜底）与 `一键到达.bat`（Arrive+Gitee pull+`memory_sync.py restore` 合并式恢复·只补新不删本地）；`memory_sync.py` 补 restore 模式（/E+/XO·与 pull 的 /MIR 区分：restore=日常、pull=迁移专用）；原 Leave/Arrive/Memory 三入口保留不动（office 部署物·可单用）
- [ ] **明日 office**：`一键到达.bat` → `git remote set-url origin https://gitee.com/tinsei0321/emotion_map.git`（首推令牌当密码）→ 之后日常 = 一键离开/一键到达 两个入口

---



### ✅ CB-35 page7 排序（claude组·第三方独立评估·只读·经用户授权 git 写）

- [x] **排序优先级评估**（`discuss/CB35-page7排序优先级_评估_Claude-2026-08-14.md`）：采候选 A（双高→客观高→主观高）·层内用「本源绝对量」极简两键（体检层族=体检点降序 / 诉求层=诉求件降序）·密度只作并列列不做排序键·核心裁定「**客观优先=层序 ≠ 层内某社区必须第一**」反驳 zcode「金安岭必须密度第一否则打脸」过度推论（金安岭按量排体检层#3·仍 TOP10·原则无损）·独立发现镇境山跨页不一致（主图红五角星 vs 旧表落榜）随换键已修复
- [x] **排序数据审计**（`discuss/CB35-page7排序数据审计_评估_Claude-2026-08-14.md` + 可复现脚本 `SCRIPT/_tmp_audit_cb35_page7.py`）：20 社区楼栋/体检点/诉求件/四列密度 vs 三源矩阵**零偏差（20/20 OK）**·分层标签 20/20 一致·三段排序严格降序·红五角星 4 社区全在客观高层·港务诉求第 3/体检 17·沉默比属实·无低置信社区·澄清分层机制（**阈值定资格[双高恰 5·强证据] + 层内 TOP-N 截断[客观高取 8/主观高取 7 凑满 20]**）·两处存疑 P1 非阻塞（阈值 28.57/146.67 精确来源[≈12345 覆盖 116 社区密度 p75·实测 27.73/153.76 非精确] + 体检点=安全+民生两视角合计含多归属需表注）
- [x] commit push（`codex/dsh-onboarding` 分支·`f315217c` 评估+审计+脚本 + `62abba45` revision-log）

### 🔄 下一步（待 Codex 主开发）

- [ ] Codex 公布分层坑位口径：阈值 28.57/146.67 精确统计算法 + 坑位 5/8/7 分配逻辑（防答辩追问）
- [ ] 多归属口径表注 + 分层机制补「TOP-N 截断」描述（md/Excel 同步）
- [ ] page7 Excel 主表 + page7 md 按三组收敛方案定稿（候选 A + 绝对量层内键 + 不设独立正榜·三组已齐）
- [ ] 4' 分析报告（图/数/表/观点 + 口径对照 + 缺口清单 + 出口卡对接）

> 🏢 **收工（08-14 深夜·家 → 早上去公司）**：CB-35 三组评估已齐、收敛。公司到岗 `git fetch origin && git checkout codex/dsh-onboarding && git pull` 看 CB-35 产出；page7 表数据已审计零偏差、可直接用于汇报。

### ✅ 双机同步体系 + 工作区清理（08-14 晚·家·claude）

- [x] **双机同步工具链**（公司连不上 GitHub → 硬盘 bare 中转 + 家机 GitHub 枢纽）：`tools/sync_guard.py`（status/leave/arrive 三模式·盘符漂移自修·幂等自补 SessionStart hook）+ 根目录 `sync-leave.bat`/`sync-arrive.bat`（双击即推/拉）+ `docs/dual-machine-sync.md`（规则 + 公司首次初始化步骤）+ SessionStart hook（每次 Claude 会话开场注入同步状态）
- [x] **工作区清理**（用户要求·图片/PDF 反复出现根因 = untracked + 整目录拷贝回流）：删除 docs 根 12 个散落图片/PDF + `.gitignore` 加 `docs/*.png|jpg|pdf` 与 `tests/browser/out/` 防回流
- [x] 未跟踪文件入库 + push（当晚模型服务故障，实际为 bat 兜底单 checkpoint `d324b501`·**未**分组、**未**归位 main——勘误见 08-15 同步报告§五）

> 🏠 **明天公司到岗（08-15）**：① 插硬盘按 `docs/dual-machine-sync.md` 第三节首次初始化（`git init --bare <盘>:/git-sync/emotion_map.git` + `git remote add syncdisk` + `git push syncdisk --all`）② 之后离开前双击 `sync-leave.bat`、到岗双击 `sync-arrive.bat` 即可。

---

## 📅 2026-08-13（图数表出图 · 线二口径 83.3% 定稿 · 角色变更 Codex 主开发）

### ✅ 图数表出图（page1-6 汇总 md + 正式 Excel page1-5）

- [x] **page1 概况**（体检对象全量 22 街办/174 城市社区/1562 小区/26426 住宅 + 77 项指标体系 16 大类）·Excel page1 sheet
- [x] **page2 两个方面**（官方文件引用版·去掉「可量化/可感知/可评价」概念框架·线一 31→25 80.6% + 线二 83.3%）·Excel page2 sheet（表A-G）
- [x] **page3 安全韧性·体检结果**（3 类 5 项·928 点·70 社区·西峡/深圳路/金安岭/镇境山）·Excel page3 sheet
- [x] **page4 安全韧性·市民反映**（4 类 1,376 条·126 城市社区+18 村·含村排行表C-2）·Excel page4 sheet
- [x] **page5 民生基础·体检结果**（5 类 16 项·757 点·106 社区）·Excel page5 sheet
- [x] **page6 民生基础·市民反映**（md 就绪·Excel page6 sheet 待追加）
- [x] 正式 Excel `DATA/analysis/图数表出图_PPT表格汇总.xlsx` page1-5 sheet 完成（排版：表头加粗+细边框+同值合并·无颜色填充·表间空 2 行）

### ✅ 线二口径定稿（83.3%·全局回改）

- [x] 87.9%（投诉+求助+建议·"建议=盼"）中间口径**作废**（用户确认错误）
- [x] 现行 **83.3% = 47,693 / 57,265**（三层定稿·投诉+求助·9 个分类·安全 4,800 8.4% + 民生 42,871 74.9%）
- [x] 全局回改：page2 v12 / page3 衔接句 / page4 开头+口径链（4,800→4,601→1,376）/ Excel page2 表D改9分类+表E口径演变记录

### ✅ 角色变更（2026-08-13 起）

- [x] **Codex = 主开发（唯一 git 写者）**·Claude = 第三方评估（接替原 Codex 评估岗）·zcode = 数据侧+复核
- [x] session-handoff.md 落盘「主开发工作基准」（四根顶层纲领：演示逻辑链/设计哲学/Copilot 内核/出口三铁律 + Excel 分工 + git 状态）

### ⬜ 下一步

- [ ] **zcode 复核双高 + 出地图渲染**（prompt 已发·回 `CB32-*审计回应_zcode-2026-08-13.md`）
- [ ] **page7 汇总 md + Excel page7 sheet**（双高社区总表·去村）
- [ ] **4' 分析报告**（图/数/表/观点 + 口径对照 + 缺口 + 出口卡）

### ✅ PPT 出图收口（下午·Codex 主开发）

- [x] **PPT 7 页审计**（只读不改·6 P0 + 2 P1 + 3 P2·落盘 `CB-PPT审计_城市体检问题PPT1_Codex-2026-08-13.md`）
- [x] **CB32 page7 设计发起**（双高定义 + 图/数/表方案 + 双高初算 27 个·前 8 集中度民生 38.8%/安全 21.1%）
- [x] **CB31 底图策略提交**（Esri raster + 天地图回退 + plan/审计文档）

---

## 📅 2026-08-12（12345+体检统一分类对标重构 · 三组讨论回收 → 收敛定稿）

### ✅ 三组讨论回收 + 收敛定稿（本轮主线）

- [x] **Codex 回应回收**（10 焦点·6 agree + 4 partial）：映射最小单位=中类·12 项目类型定稿·213 小类继承+跨界<20·体检/12345 共用项目类型层·4 列落结构·子维度更正 17→16·4×5 兜底表·问题整治独立 agree
- [x] **zcode 回应回收**（5 焦点·1 partial + 4 agree）：先出分类映射表再加列（战略 1）·10 中类偏粗建议·矛盾/社会治理独立类 0.9%·板块→中类→小类·附件2 归整治成效（低优先）
- [x] **收敛定稿**（`docs/catch-ball/discuss/CB23-12345分类对标重构_收敛定稿_2026-08-12.md`）：12 类取 Codex（噪声治理独立贴合用户例子）·矛盾拆+残留归其他（两案合并）·智慧高效按项拆分（zcode 案）·列结构合一（层次 3 层 + 落结构 4 列）·执行顺序=映射表→加列→重跑→diff 校验→三组复核
- [x] cb-journal 追加本轮（讨论回收+收敛定稿闭环）

### ✅ 用户纠正重分类（不强行归拢）→ 两组优化意见回收 → 收敛定稿 v2 → 全局执行

- [x] **用户纠正**：77 项不能全归两板块（绿色智能=附加类≠民生基础需求·基础需求=急难愁盼）·12345 同理 → 重分类（安全17/民生29/其他30/整治1 + 12345 侧重排）
- [x] **两组优化意见回收**（`CB23-分类对标重构_重分类_两组优化讨论发起` + 意见 2 份）：F1 三标准 agree·F2 22 项移出 agree·Codex 小类级切分 4 处实测（道路通行 2634→民生/消防通道 442→安全/停车场设施 518→民生/毁坏桥梁 11→安全）+ 堡坎 215→安全（两组独立发现）·zcode 整体归边不取（442 实测 38.6%）
- [x] **收敛定稿 v2**（`CB23-12345分类对标重构_收敛定稿_v2_2026-08-12.md`）：三标准判据（安全=生命财产/民生=急难愁盼/其他=附加）+ 判据注释表 + 双口径呈现 + 执行计划
- [x] **全局执行**：① `12345_分类映射.json` v2（42 中类主表 + 小类覆盖含供水供气服务类→民生）② 治理脚本加 4 列重跑（**民生 49,192 85.9% / 安全 8,046 14.0% / 其他 27**·无 None·全核对过）③ 77 项 board 重落（17/29/30/1·主题分类零矛盾）④ 问题清单 board 同步（59 行零缺失）⑤ 05 链条板块核对（已对·不动 project_type）⑥ checkup_12345_2024 重导出（25 列含 4 新列·emotion_intensity 保留前端兼容）⑦ manifest 1.5.1
- [x] pytest **320 passed 零回归**

### ✅ 三组复核闭环（分类对标重构 v2 全链完成）

- [x] **codex 审计**：5 项重点核验全通过·无 P0/P1·3 项 P2 观察（emotion_intensity 值域标注/[47] 车速条件判据/供水服务-设施分轨规则）
- [x] **zcode 判据注释表**（`03_元数据/77项_板块判据注释.md`·六章 162 行：安全 17/民生 29/其他 30 逐条理由/整治 1/14 处差异记录/P2 规则文档化）+ manifest 1.5.2
- [x] **两板块=结论逻辑沉淀**（用户明确·与铁律 7 同构：分析过程不消费 board·分类=治理标注+结论组织框架）→ memory + 交接卡

### ⬜ 下一步（出图数表讨论 → 3' 分析）

- [ ] 出图数表讨论（当前唯一门槛·图1-4 呈现链·2×3 矩阵·双口径呈现·分析内容×方法×结果形式）→ 3' 开动

### 📌 分析完善待办（CB 建议记录·整体框架完成后慢慢完善·2026-08-12）

- [ ] **密度视角**（Codex）：严重度分级补「点数/社区楼栋总数」密度（配置库楼栋可用·防大社区点数多小社区被忽略）
- [ ] 消防站覆盖率 20.59%/高层预警 11.6% 等宏观指标·与有点指标的空间呼应（总量卡已备·呼应待做）
- [ ] 结构隐患 42 栋二马路 40.5% 聚集·与 03-07 材料（云集 24 栋 57%）一致性标注
- [ ] 危房 61 社区 vs 市政/消防 36 社区覆盖差异·报告解读标注防误导
- [ ] 出图数表讨论（重构后）→ 3' 开动

---

## 📅 2026-08-11（紧急任务·城市体检两板块分析·数据/工具/管线全就绪·收工回家换环境）

### ✅ 数据质量闭环 + 官方行政数据 + 出图数表讨论待定（今日主线·详细）

**数据治理与审计（全链路）**：
- [x] 12345 原始数据治理（57265 行·用户提供 `2024年12345投诉数据_raw.xlsx`）→ 治理清洗版 + 情绪地图中转版（polarity 5级/score 0~1/4×5/topic/place/region_scope/cross_region）·`06_主观数据治理/` 两份 + 4x5 映射 + 方法论（模拟数据黄金样本）
- [x] 12345 geocode 回填（clean 地名 80% 命中·region 质心兜底·离群过滤 93→0·PII 车牌0/人名0）·注册 `checkup_12345_2024` 层（18171 有坐标·中心城区 77%）
- [x] 项目端数据（用户提供·十五五储备表 excel 183 项目 + 重点项目 gdb point185+line102=183·gdb 只读导出 GeoJSON·excel 匹配 99%）·注册 `checkup_project_point/line` 层
- [x] **官方行政数据**（用户插入·市域县级 14 县区 + 村社区 1682 shp·SSX 聚合 113 街办含 16 街办口径）·admin_street/community/county 注册·社区 94MB reference_only·**街办 zonal 打通**（宝塔河 3066）
- [x] **数据质量修复**（两组全局审计 Codex 2P0/8P1/12P2 + zcode 3P0/12P1）：P0-1 双轨 buffer 4546（双高格 1768→16）·P0-2 12345 治理（噪声 53%→0.05%）·P1-1 admin_county·P1-2 cross_region 664·P2-3 extract_event·P2-4 16 街办对齐·P2-6 趋势聚拢标注·PII 过滤（车牌容忍空格/人名·脱敏红线达标）
- [x] 管线测试 6/6（体检/12345→密度·双轨→双高·项目聚拢 64%·zonal sum·hotspot 守卫）·双轨密度完整版（双高格 16）
- [x] 趋势聚拢验证：12345→项目 57%/81% 落高密度格（统计显著·方法可复现）

**术语/统计**：
- [x] **街办术语统一**（街道→街办·全局·CLAUDE.md 铁律·分派三组·claude 代码层完成）
- [x] **三组犯错统计**（claude≈87%/Codex≈29%/glm-zcode≈77%·glm→zcode 更名合并·角色不对称声明）

**跨项目协作（CB）**：
- [x] 每轮进 CB 两组审计（数据质量/管线双轨/行政数据/闭环验证全回收）
- [x] zcode 数据侧分工（CSV 重构/列错位/专家评审/manifest v1.4.6）+ 街办术语分派
- [x] 定位修正：**分析不依赖片区边界**（片区=结论·问题聚集推导·CLAUDE.md 铁律7·分析过程不预设片区·边界供团队叠加）

### ⬜ 下一步（出图数表讨论 + 3' 分析）

- [ ] **出图数表讨论**（图1-4 呈现链·2×3 矩阵汇报框架·分析内容×方法×结果形式·Codex 方案 A）→ 定稿后 3' 开动
- [ ] 3' 两板块分析（安全韧性 + 民生·问题→项目趋势聚拢·不卡边界）
- [ ] 4' 分析报告（图/数/表/观点 + 口径对照 + 缺口清单 + 出口卡对接·不等边界）

### ✅ 阶段 1'+2' 完成 + 空间落位铁律全局修改（后续补充）

- [x] **阶段 1' 后端小扩展 A1/A3/A4/A5/A7**（b8828c54）：grid agg_cols / hotspot 常数+NaN 守卫 / 聚合 _sum / zonal sort_by / presets manifest 修·320 passed
- [x] **阶段 2' RAG**（595a6369）：15 CHK fact→CHECKUP_FACTS（all_facts 52→67）+ outlet_kb 客观轨契约 + RAG摘要落 00-09 + 索引重建 258→295·冒烟命中
- [x] **Codex 审计回收**（3 P1 修正）：zonal 响应补 _sum / A3 NaN dropna / checkup_two_panels→PANEL_MAPPING·零 disagree
- [x] **zcode 思路对齐·全局修改**：空间落位口径铁律入 CLAUDE.md（4维度控件对象=输入·片区=结论推导）+ plan 覆盖矩阵两段化 + 主观轨落图（12345 514处·双轨对照）+ D1 图面=网格聚合倾向
- [x] 回应 zcode 2 疑问：聚集趋势四维 / 情绪地图价值=12345 真实声音落图

### ✅ 阶段 0' 对接层（读定稿+交接卡+Codex 评估 → 全交付）

- [x] 读 `emc-rag-emc-wise-lark.md`（定稿五阶段·Codex 7 修正+6 决策全采纳）+ 交接卡 + Codex 评估 + zcode 中转站 manifest v1.1.0 实读
- [x] **`DATA/exchange/` 对接层四件套**：README（三分法）+ manifest.json（引用清单 19 层 + copy + derived）+ schema_inventory.md + PII_EXCEPTIONS.md + 口径对齐.md
- [x] **PII 实读**：`building_50year_1.geojson` 380 要素 `yslxr/yslxrdh` 字段全存在（值空格）→ 只引用不复制·派生层剥离；`存在问1` 照片 URL 不入库；验收扫描零残留 ✓
- [x] **口径漂移确认**：manifest「20 项」vs 实表 18 行 → 以实表 18 项为权威
- [x] **追踪模块 ID 决策**（D5）：新增 `MOD_CHECKUP`（`SCRIPT/checkup_ingest.py`·F_001 起）·AGENTS.md 登记
- [x] 副本落位：03-08 摘要 → `00-宜昌专项/03-08...md` + `_INDEX.md` 00-08；`_PATHS.md` 扩展第三环境 `D:\OneDrive`；context-map + AutoMemory 登记
- [x] revision-log §5 + todo 08-11 段同步

### ⬜ 下一步（阶段 1'）

- [ ] checkup 直通适配器 `SCRIPT/checkup_ingest.py`（WGS84 透传·无 LLM 漏斗·L2 旁路·L1 导出 + geo_registry 注册 + 面层 preset + 质心点层·坐标透传单测·MOD_CHECKUP F_001 起）
- [ ] 风险前置验证：zonal 对「指标数值字段」聚合 + 面层质心化后 hotspot 可用性（防阶段 3 返工）

---

## 📅 2026-08-10（CB-22d 地图标记路径跑通闭环 · 收工 · 分支合并 main）

### ✅ CB-22g 追问无法完成·反评价收敛定稿 + P0 实施 + 2025体检整合入RAG（收尾·待 push）

- **背景**：CB-22f 5 阶段实施后用户实测追问仍失败 → 上轮两组评估已出 → 用户「连带本次体检整合一起修复·先进 CB」
- **两组反评价收敛**（采纳 Codex 主线）：诚实记录 claude 上轮 trace 取证错误（sess-22008 实为 pytest 非 user session·F_005=build_diagnose_prompt≠FC）→ **坐实 4 根因**：① F_016 编号冲突 ② FC 端点缺埋点（trace 盲区）③ knowledge_qa 零参 schema 可疑 ④ 旧 SSE diagnose 死路径
- **P0 四批全落地**：
  - [x] 批1 编号冲突 + stages bug：query_knowledge_base `@track F_016→F_018`（解 build_outlet_schema 冲突）+ stages.js:322 `question→ctx.question`（fcDiagnoseStep ReferenceError·glm 发现）
  - [x] 批2 track_ids 全仓守卫：新增 `tests/validate_track_ids.py`（ast 解析·只认语法树装饰器节点·正则版误判自身 docstring 已废·15 装饰器零 DUP·防复发）
  - [x] 批3 体检整合：md 移入 `00-宜昌专项/03-07_` + **16 fact 补空间落位**（I09-I16/C05-C07/P09/P10/P12/M04/M05·36→52）+ P01/P11 顺手修 detail>80 字违例 + 索引重建 + 6 组检索全命中
  - [x] 批4 FC 埋点 F_019：router.py `_fc_gen` 手动 enter/exit/error（`@track` 不适用生成器·tool_calls/tool_name/_fcError 落 trace·FC 从此可观测）
- **验证**：**315 passed + 3 skipped 零回归**（基线 315）·validate_track_ids 2 + validate_knowledge_route 5 + validate_rag_material 9 全过·schema 自校验 detail≤80 字
- [ ] **待 push**（用户手动）+ **P1 待用户**（knowledge_qa 零参 schema 浏览器冒烟 + 重采真 session 取证）+ **P2 独立**（F_009 DEM error / F_005 KeyError lon_gcj02）

### ✅ 分支合并：fix/emc-buglog → main（收敛·删分支·保持干净）

- **合并**：`fix/emc-buglog`（368 提交·含 CB-22d 全链）→ `main` · merge commit `b77daef`（保留全部历史 + 本地 main 的 `81784f0` mcp 配置）
- **推送**：`git push origin main`（`76124d6..b77daef`）
- **删分支**：本地 `git branch -d fix/emc-buglog` + 远程 `git push origin --delete fix/emc-buglog`
- **当前**：唯一分支 `main`（本地 = 远程 origin/main = `b77daef`）·工作区干净
- **⚠️ 双环境提醒**：**公司/家里 git pull 后需更新分支引用**——`git fetch --prune origin`（删本地过时 `origin/fix/emc-buglog`）·**另两组（Codex/glm）只读本地不 git**·claude 已 push main·它们读本地 main 即最新（勿再引用 fix 分支路径）

### ✅ CB-22d 知识问答→地图标记·路径跑通闭环（用户实测成功·两组复验通过）

- **背景**：追问「能在地图上标记出这些项目的位置吗」→ 首版全未匹配 + 停半途 7 分钟 → **三证合一根因**（trace + 用户思考内容 while-loop + 两组复验预判）
- **用户两想法**（北极星）：① 地点模糊搜索须 LLM 参与·非纯算法硬匹配（业界=意图分层+分词+加权·高德专利）② 无法识别地点就放弃·像人思维·不能 while-loop 无限思考
- **两组根因修正**：Codex（挂起=finalStep 单调用·names 拼接串·冷加载·依赖缺失）·glm（数据缺口=匹配入口未分词·补单轮超时）
- **实施**（commit `ace4f8f`·路径跑通）：names split + 冷加载20s + rapidfuzz/pypinyin装 + 高德优先(amap_first) + A0 jieba分词双路 + 聚合名放弃(_isAggregate) + **B1 零命中零LLM出口（根治挂起）**
- **验证**：307 passed 零回归·validate 9 断言·路径跑通 8/9·两组复验均通过·用户实测「基本成功生成正确图层」
- **后续（非阻断）**：见下方「公司待办」

### 🔴 公司待办（08-10 上午·OFFICE 卡·**当前在 main 分支**）

> ⚠️ **到公司先 `git pull`（拉 main 最新）+ `git fetch --prune origin`**（删本地过时 fix 分支引用）·当前开发在 **main**·不再用 fix/emc-buglog。

- [x] **分支同步**（office 08-10 上午）：本地 fix/emc-buglog 已删·仅剩 main·交接卡漂移修正 commit `52040f10`（未 push·网络暂断）
- [x] **环境恢复 + 分支同步**（office 08-10）：目录残缺→fetch origin（`0fdd64c`）→checkout main→删 fix 分支→唯一 main 与远端对齐·工作区干净
- [x] **CB-22e 地图标记准确度与防护·反评价收敛定稿**（两组回收·P2 前提修正实锤 N/M 断链 + P1 四件套定稿 + P3 落点修正·**并入 CB-22f 实施**）
- [x] **CB-22f 纯问答→空间动作链路由打通·反评价收敛 + 详细讨论最终定稿**（8 焦点 4 agree+4 partial·两组详细回应回收·**Codex 2 修正** + **glm 3 修正** 已核实·**最终定稿 5 阶段**）
- [x] **CB-22f 实施完成**（今天任务·已过 CB→实施完毕）：
  - [x] 阶段0 CB-22e P2+P1：降级结论选行 + 准确度四件套（_core_entities 候选表/中心挡词/_WHOLE_AGGREGATES/独立 Tokenizer+yichang_places.txt/amap 标注）
  - [x] 阶段1 CB-22e P3：test-cases B3 用例（RST-L07）+ 桩测四场景（N/M 断链修复验证）
  - [x] 阶段2 A 路由打通：knowledge 伪工具 + 三分支 + 方案 A 兜底 + FC 纪律 + validate_knowledge_route 5 断言
  - [x] 阶段3 B 识别+衔接：fact meta 透传重建（region/topic/year/keywords 验证）+ ctx.extracted 实体清单级 + priorTurn 回灌 + _followupCue 分类器（8 场景 PASS）+ recover 扩 analyze/compare
  - [x] 阶段4 D RAG 收尾：query_knowledge_base（**F_016**）+ fact 加权×1.2（3 测试）
  - [x] 验证：**315 passed + 3 skipped 零回归**·serve 重启新代码加载验证
- [x] **CB-22h 追问读秒卡住·三组根因收敛 + 修复**（glm 承重根因 `_assembleKnowledgeQA` 无降级兜底 → P0-1 catch 降级 / P0-2 总 deadline / P0-3 httpx 分段 / P1 预热同步）
- [x] **CB-22i 追问标记崩溃根因定位修复**（Playwright 抓 console 定位 `PAGEERROR: JSON.parse(...).slice is not a function`（panel.js _distillTurn extracted 回灌对象 .slice）→ 修对象属性限制·**完整链路实测通过**：首问 11s + 追问标记 7s 出「宜昌城市更新项目点位」图层·0 挂起·PAGEERROR 消失·commit a27c0e2e）
- [x] **CB-22i Timer 主动中断修正**（Timer 移 `client.stream()` __enter__ 前·覆盖等响应头阻塞·本地挂死 server 1.0s 中断验证 + serve 反代 50s 超时 + 前端 Promise.race）
- [ ] **CB-22i 用户浏览器实测**（强刷 Ctrl+Shift+R 后完整链路：首问→追问标记出图层·若仍异常抓 console PAGEERROR 发我）
- [ ] **CB-22f B3 飞轮实跑**（留后验证）· **CB-22f 动作链 2 步 demo**（标记→分析·Phase2 多步·预载 L2）
- [ ] **A1 GIS 甄别 / tier-2 面化 / A3 项目库坐标**（G 盘 GIS 重活·**单独轮**）
- [ ] RAG 遗留（OFFICE 卡）：B 路径 query_knowledge_base · 混合检索 · 全仓 [中文]+类 扫描 · Recall@5 · P0-6 复审

## 📅 2026-08-09（城市更新专项规划知识库构建 CB-21b · L2 任务 + RAG 计划）

### ✅ CB-21b · 城市更新专项规划知识库构建（主体完成·三组协同）

- **背景**：用户接到《城市更新专项规划》（宜昌城区）研究任务·需权威资料（政策/指标/案例/体检/GIS）+ 沉淀 EMC 知识库。G 盘 `15_城市更新专项规划研究`（875 文件·真实权威）。
- **L0 资料库**（`docs/urban-renewal-plan/`·主体完成）：00-宜昌专项 8 份 + 政策 12 + 指标各城对照 + GIS 31 图层 + 上海/杭州/广州/成都案例 + 总览报告 + 完成度清单
- **L1 知识库**（`ai_qa/industry_kb/urban_renewal.py`·完成）：TOP_DESIGN 6 + CORE_FRAMEWORK 10 + KEY_TERMS 9 + METRICS 7 + CASES 8 + PROJECT_TYPES 9——**305 passed 零回归·final_brief 1625B<6000**
- **三组协同**：claude（GIS/体检/专项规划/上海考察）+ codex（政策/指标/PPTX/伍家岗十五五）+ glm（编制导则识图/湖北 OCR/南湖）
- **收尾项**（低优先·已登记）：湖北导则 OCR P0 章节·北京 OCR·伍家岗图册·PPTX 图表

### ✅ CB-22 三层架构优化实施完成（今日收工·全链闭环·用户实测通过）

- **背景**：用户复测「宜昌市城市更新的项目有哪些？」出图层失败 → trace 取证（词序变体击穿短路 + diagnose 无知识问答通道）→ **用户拍板「NL 意图判断必须通过 LLM」** + **三层架构**（数据层三库/实施层 Smart·Dumb/表达层三段式）→ 两组三轮讨论（6 焦点 + 0b/0c 性能根因 + 执行前验证 8 焦点全 agree）→ 实施
- **P0 意图判断归位**（commit `24e6ab0f`）：diagnose 加 `knowledge_qa` 枚举（对比句判据 + 续作例外·**红线豁免记录** KNOWLEDGE §1）+ _quickIntent 降级加速器（6 词最小化·漏网落 diagnose LLM 判）+ `_assembleKnowledgeQA` 合流（短路+diagnose 双入口·data_plan 三态 score≥0.5）+ 分通道增强（ctx.context 条件注入·D019 不动）
- **P1 概念库**（9 条 3 类·type='concept'·产品定位/方法论/边界认知·摘抄+引用禁重述）·索引 235 条
- **P2 防回归**（触发正负例语义更新/枚举断言/知识问答路由 e2e·injectOnly 确定性消 flaky）+ **P3 出处**（URP-P01 双来源）
- **素材术语去硬造 + 来源标注弱化**（commit `39f51265`）：URP-P01/笔记:43/总览报告去「典型片区类/机制建设类」硬造分类·罗列式·来源标注 `〔来源：可读名称〕` + CSS 0.85em 浅灰弱化
- **杜绝概念创造 3 层治本防线**（commit `3b07d52a`·用户「记住」）：① 素材清洁（全仓零残留·黑名单断言）② 提炼纪律（**CLAUDE.md 铁律 13** + KNOWLEDGE + AutoMemory）③ LLM 自创防线（指令 3 禁推断分类/解释 + 黄金集概念清洁断言）
- **验证**：全仓零残留 · validate 9 + pytest 307 + e2e 7 全绿 · 用户实测通过
- **待续（RAG 遗留·明天继续推进）**：见下方「🔴 遗留 RAG 工作」

### ✅ 家环境同步（08-09 晚·pull 公司全链后）

- **pull 同步**：`434a604..56cd67b` fast-forward（公司 08-09 全链·无冲突）·push @ `3abe31e`
- **进度同步 + 环境检查发两组**：`discuss/进度同步与环境检查_讨论发起_2026-08-09.md`（3 焦点 + 附 A prompt）·HOME 卡更新
- **RAG 补链完成**（用户要求补齐环境）：torch `2.13.0+cpu`（阿里云镜像·PyPI 无 +cpu 标签）+ BGE 模型 + 索引 235 条 + 检索冒烟通过
- **三组进入状态通知**：`_handoff/三组进入状态通知_RAG补链完成_2026-08-09.md`（push @ `a3fadcf`）
- **双环境路径补齐**：`_PATHS.md` + `README.md` 家庭 `C:\Users\Hi\OneDrive\...`（878 文件实测·push @ `aa05543`）
- **AMAP_KEY 恢复**：历史会话找回 `7294b86...` → .env 补回 + 高德 API `status=1` 有效
- **三组记忆完善**：KNOWLEDGE §2 沉淀 2 条 + AutoMemory `rag-chain-bringup` + `_handoff/三组记忆完善prompt_2026-08-09.md`（push @ `a967253`）
- [ ] 等两组回应 + 记忆同步确认 → /cb 反评价收敛 → 发 RAG 遗留任务分配

### 🔴 遗留 RAG 工作（明天继续推进·重要）

- [ ] **用户复测本轮全链**（无硬造分类 + 来源弱化·公司电脑·通过后已 push）
- [ ] **B 路径（CB-22b·query_knowledge_base 确定性查询）**——RAG_QUERY_KW 临时结构化词（有哪些项目/体检问题等）待迁移·`knowledge_query` 范式已预留
- [ ] **混合检索**（glm/Codex 共识·P1）：fact 加权或 Top-5 保底 ≥1 fact·降 note 占比（当前「有哪些更新项目」Top-5 全 note·fact 短文本向量信号弱）·提升素材精度
- [ ] **全仓 `[中文]+类` 扫描 + 逐条核实源文档**（黑名单机制 + 人工审新词·防误拦官方词）
- [ ] **Recall@5 素材质量机制**（Codex V5·黄金集 Recall≥80% 持续跟踪）
- [ ] **P0-6 分通道 tier 复审**（暂缓·flash 保持·路径跑顺后**勿忘**·glm 提醒：知识问答开 pro 综合深度）
- [ ] L2 出向任务（outlet_kb 接入运行时·进 CB 讨论）

### 🔄 L2 出向任务（进 CB 讨论·定稿执行）

- **内容**：让新增知识库贯通 EMC"出口"——L2 出口契约对接知识库（outlet_kb 接入运行时·体检-更新衔接契约·具体项目问答支撑）
- **状态**：进 CB（L2 任务讨论发起）→ 两组评估 → 定稿执行
- **CB 支撑**：后续开发参考本知识库·尤其是 EMC"出口"

### 🔄 CB-22 三支柱对齐实施（两组回收全 agree → 实施修正 → 待两组复验）

- **两组对齐回应已回收**（`CB22-三支柱对齐_{Codex-GPT5|glm组}_2026-08-09.md`）：6 焦点全 agree·glm 诚实承认零 LLM 错误（过度防幻觉·忽视 LLM 综合是三支柱之三·原则升级 = trace + 产品意图对齐）·Codex 挑战 3 条（认领无挑战·零 LLM 边界显式限定·指令治本是幻觉）
- **⚠️ 承重发现（两组未检出）**：rag 索引 meta **不存 text**·注入 finalStep 的"素材"仅文件名·LLM 无内容可综合（三支柱①空转·验收 V2 结构性不可过）
- **实施修正 5 项**（黄金集 5/5 + pytest 305 零回归）：
  - A 素材内容注入：`rag_index.py` meta 存 text + search 透传 + `harness.js` 注入片段全文 + 四指令（强标记/只基于素材/综合 Top-N/禁图层·finalStep LLM 综合保留）
  - B PARADIGM_MAP 注释修正（"确定性组装·零 LLM"→"知识问答·LLM 综合"·注释曾与实现矛盾）
  - C **新单测** `tests/validate_paradigm_map.py`（5 断言·含零 LLM 防回归机器化）
  - D KNOWLEDGE 蒸馏 3 条（零 LLM 边界/LLM 综合边界/§7 规则 5 交叉挑战）
  - E 端点测试补 text 断言（防素材回退文件名）
- **两组复验已回收 + 反评价收敛定稿**（[复验回应 ×2](docs/catch-ball/discuss/) + [反评价收敛定稿](docs/catch-ball/discuss/CB22-三支柱对齐_反评价收敛_定稿_2026-08-09.md)）：
  - **P0 定性**：glm e2e 失败 = 环境非回归（claude 复跑 PASSED·整组 5/5 全绿）
  - **P1 已修**：finalStep 断言精确化（`await stages.finalStep(ctx, hooks, '')` 精确调用点·Codex 挑战 2）
  - **P2 已修**：注入体积守卫新测试（snippet ≤1000B + k≤5 + 指令行数有界·预算 ≤8KB 文档化·Codex 挑战 1）
  - **B5 留用户实测**：指令优先级（ctx.context 强标记 vs FINAL_TEMPLATE 图层导向·两组标核心看点）
- **状态**：定稿可推 → **用户手动检查**（清单见定稿文档附：①知识问答主路径 ②准确性 ③全面性 ④稳定性 ⑤边界负例）
- **待续**：push 后 B 路径（CB-22b·query_knowledge_base 确定性查询·RAG_QUERY_KW 临时结构化词待迁移）·Recall@5 素材质量机制待建

### ✅ RAG 建设（本周重点·已完成主体）

- **背景**：用户问"宜昌有哪些更新项目"→ 暴露 EMC 只注入不检索·需 RAG（向量化 L0/outlet_kb）
- **已完成**：本地 BGE embedding（Py3.14 装好·HF 镜像）·事实卡 35 条（L1.5·`urban_renewal_knowledge.py`）·索引 225 条·`/aiqa/rag_search` 端点（F_017）+ harness `rag_query` 短路·黄金集 3 类 100%·e2e 5/5
- **修复**：serve 启动预热（消冷加载 18.6s）·EXIT_CONCEPT 兜底·超时 30s（CB-22 根因：冷加载>超时→RAG 丢失）
- **机制完善（分类→范式映射）**：CLAUDE.md 铁律6·rag_query 注入素材→finalStep LLM 综合（非零 LLM）
- **待续**：B 路径（CB-22b·query_knowledge_base 确定性查询）·收窄 RAG 触发词

### ⭐ 关键经验教训（跨轮蒸馏·指引后续开发）

- **三支柱**：纯回答稳定性 = 本地知识库完备度 + EMC 架构（分类→范式映射）+ LLM 归纳总结能力·**缺一不可**（CLAUDE.md 铁律6）
- **零 LLM 教训**：RAG 检索出文件必须 LLM 综合总结（非零 LLM 拼列表）·曾砍 LLM 支柱被用户验证否定
- **产品定位**：EMC+RAG = 本地化聚焦专业知识蒸馏（区别于网络搜索/其他 AI·本地化+聚焦+专业+可追溯）
- **结论颗粒度 = 数据来源维度**（城区⊃街区⊃社区⊃小区+零散住房+城中村·社区≠小区）



### ✅ CB-17 闭环（三组进度同步 + 下一步安排收敛）

- **背景**：用户 08-06~08-07 暂停回归 → 要求回顾 + 三组同步下一步。claude组 核实基线（git `cf5ef04` 同步·08-05 两专题 CB 全闭环·验证基线）→ 落 [讨论发起](docs/catch-ball/discuss/进度同步与下一步安排_讨论发起_2026-08-08.md)（7 债 + 5 焦点 + 附 A prompt·commit `ce850a3` 已 push）
- **两组回应已回收**（`docs/catch-ball/discuss/进度同步与下一步安排_回应_{Codex-GPT5|glm组}_2026-08-08.md`）：
  - **Codex**：快照事实核验全通过（代码 grep 逐项佐证）·补 B3 fail 集合快照判据（fail 集 == {PRM-03/04/07}·新增即阻断）+ 三路径观点卡浏览器抽验（B1 补丁只被 pytest 未被 B3 覆盖）·PRM-07 **partial（P2→P1·仅预检不实施·执行侧残余实测）**·补债 HOME/OFFICE 交接卡过期/flywheel 注释 25→26/回归判据缺 fail 快照/前端 JS 单测补课
  - **glm组**：pytest 独立跑 **291 passed + 5 skipped**（vs claude 声称 293·差异 2 待核实）·补回归范围 validate_outlet_fields/validate_skill_params/test_hotspot·**P3-4 地点联动优先于 P3-1**（出口闭环最后一块·微观落点粗略→精确）·PRM **agree 不排入**（03/04 center ask_user 正确·07 已根治）·补债 .outlet-metrics CSS 缺失
- **claude组 反评价（verify-before-accept · 关键争议核实）**：
  - pytest 实测 **291 passed + 5 skipped**（35.47s 全绿）→ **glm 的 291 正确**·「293」为旧口径（差异 2·非回归·发版回归对齐口径）
  - `.outlet-metrics` **已存在于 ai_qa.css**（Grep 证实·401371b ③z3b P2-1 已修）→ **glm 补债为过时信息·disagree**
  - **PRM-07 执行侧残余属实**（tools.js:617-622 白名单只对 `source==='preset' && /行政区/` 生效·FC 直供非 preset 边界绕过）→ **Codex 对·glm「已根治」仅覆盖数据侧**
  - flywheel_audit.py:7 注释 25 vs 26 属实
- **下一步安排定稿**（cb-journal CB-17 章节）：

```
P0（用户·当前）整体验收：todo「整体验收清单」浏览器肉眼验证 + 记 3 观感（观点卡干货感/热点五档可读性/setTerrain 地势感）
P1（发版门）发版就绪度回归：pytest 全量（291 passed + 5 skipped 基线）+ validate（含 outlet_fields/skill_params）+ link_checkup 20/20 + eval 复采（带 session）+ B3 三连（判据 = fail 集 == {PRM-03/04/07}）+ RST-L06 三连 + 三路径观点卡浏览器抽验 + flywheel 注释对齐（25→26）
P1（预检）PRM backlog CB 预检（仅预检不实施）：B3 取证确认 fail 集合 → PRM-03/04 stale-tool 修复覆盖核实（center ask_user 正确·非改代码）→ PRM-07 执行侧两候选收敛（白名单补齐 vs request_upload 强化）→ 回归通过后实施
P2（回归后）P3-4 地点联动（出口闭环·微观落点粗略→精确）：复用 geo_label·先盘点消费方·分开 commit 先验后推
P2（回归后）P3-1 依赖图（零红线）：DAG 纯函数·不交 LLM·与 P3-4 分开 commit
P3（文档）HOME/OFFICE 交接卡同步 + _cb-index 状态更新 + revision-log 归档
P3（后置）P3-2 并行（降挂起）· KDE/DBSCAN 替代（发版后专题·先定产品定义）· 时间轴 manifest · 前端 JS 单测补课
```

### ✅ 整体验收通过（CB-18 全闭环 · 用户新工作方式：验收交两组走 CB）

- **两组 CB 验收**（`整体验收_实施检查发起_2026-08-08.md`）：**有条件通过**（Codex 更严 + glm 通过）→ 修 W-1/W-2 + 补 S-1~4（commit `d5a5625`）→ **glm 复验通过**（`整体验收_修复验证回应_glm组_2026-08-08.md`·W-1 零残留/W-2 链闭合/S-1~4 充分·pytest 297 零回归）→ **push + 整体验收通过**
  - ✅ **W-1**：tools.js hotspot docstring/observation 红/绿文案 → 纯橙系五档（零逻辑·纯文案）
  - ✅ **W-2**：threshold/soft_threshold 转发补齐（hotspot-tool.js `_execute` body + tools.js hotspot 透传·默认 1.96/1.0 不破坏）
  - **W-3**：legend 五档口径 → 定「EMC 工具卡文本图例」（地图图例补 UI 后置）
  - ✅ **S-1**：`tests/test_export.py` 新建 4 例（BOM/列/脱敏/空卡）
  - ✅ **S-2**：`tests/test_spatial_analysis.py` +2（terrarium 解码 0~500/bounds/尺寸 + 极性过滤 ValueError）
  - ✅ **S-3**：`tests/browser/test_result_struct.py` 新建 + e2e-seam 暴露 buildResultStruct（观点/无观点/4 要点/结论带地点/scale 三档/无地名降级·P0-3 DOM 断言留回归期浏览器抽验）
  - ✅ **S-4**：`tests/test_outlet_schema.py` 补 geo_label micro + unknown→None
  - **验证**：pytest **297 passed + 5 skipped**（+6 新增·零回归）· S-3 e2e-seam PASS · ESM 语法 OK
  - **Codex 缺席标注**：glm 单组复验通过（用户指示「先只看 glm组」）·Codex 恢复后补验（W-2 全链 + S-3 边界 + DOM 断言前置评估）
  - 观感类（P0-1/P0-5/H-1/H-4·干货/地势感/无露底/console）标「可选用户复核」

### ✅ P1 发版回归绿 + P3-4 地点联动实施完成

- **发版就绪度回归（绿）**：pytest 301（done·claude）+ validate 34 + eval 81% PASS + 三路径观点卡 PASS + **glm 分担全回**——link_checkup **20/20** + B3 **Run1/2 均 23/26（88%）**（fail ⊆ {PRM-03/04/05/07} 已知 backlog·RST-L06 PASS·成果范式 6/6）+ Run3 API 慢时段（21 timeout·trace 排除）·**回归绿·可进发版候选**
  - **事实修正**：glm 报告「Run2=5/26」计数有误·实际 Run2=23/26（88%）·仅 Run3 API 慢
  - **PRM-05 补入 fail 集判据**：{PRM-03/04/05/07}（boundary derive 方差·CB-12 起持续·非并发引入）
- **P3-4 地点联动实施完成**（commit `9680dcc`·未 push·先验后推）：
  - P3-4-1 zonal/rank prop_cols 放行 place_name/place_name_source/poi_names/poi_count（Gap B 核心杠杆）
  - P3-4-2 buildZonalFc 焊地点字段透传
  - P3-4-3 出口卡动态 limitations（按 source 诚实标注）+ micro 需求位置 POI 升级
  - P3-4-4 _fmtRow place_name 优先
  - 验证：pytest 301 + test_outlet_micro/test_outlet_macro e2e-seam PASS
  - **待两组复验**（`P3-4地点联动_复验发起_2026-08-08.md`）→ push → 发版候选

### ✅ CB-19 发版回归全面测试完成 · 发版候选通过

- **三组协同**（`发版回归全面测试_方案_2026-08-08.md`）·**fail 集判据 {PRM-03/04} 达成**：
  - **claude 组**：pytest **303 passed + 5 skipped** + validate 34 + ESM 6/6 + **B3 24/26（92%·历史最佳）**·fail={PRM-07 空对象 LLM 方差·单要素拒识已生效, RST-L06 Flash 方差}·PRM-03/04/05 全转 PASS
  - **glm 组**：条件绿（pytest 303 + CB-18 数据 + 修复代码审查·环境端口冲突未新跑）
  - **Codex**：T6 PRM 专项 PASS + T8 出口卡 e2e PASS + **T7 多步链 FAIL【阻断】**（469bf32 黑名单误伤「龙泉」·层首要素）→ **claude 修复**（5115d7c·只拦单要素·T7 复测 PASS·pytest 303）→ **阻断解除**
- **基建修复 4 commit**（三组并发必需）：端口隔离 3dc0a1c + 后台 PATH fdc1c1d + serve 断连 76b16eb + PRM-07 文案 2f9965f
- **发版候选判定：通过**（T7 阻断已修·fail 集判据达成·剩余 fail 均已知/方差）

### ✅ CB-19c 5115d7c 黑名单修复复验通过（两组确认）

- **Codex + glm 均通过**：T7 多步链阻断解除（执行成功）+ 小溪塔单要素仍拒识 + 前后端一致 + pytest 303 零回归·漏拦风险低（三重保险）
- **采纳 Codex P2 建议入 backlog**：P2-1 多要素全黑名单增强 · **P2-2 boundaryLabel 取 features[0].properties.name（治 `[object Object]`·治 PRM-07 偶发 fail 方差源·高价值）** · P2-3 verify_prm57 断言加严
- **CB-19 全部闭环**：整体验收 → 修复 → 深读 → 发版回归全面测试 → 黑名单复验 → **发版候选通过（两组确认）**

### ✅ 收尾完成（P2-2 + P2-3 + 文档债）

- **P2-2 boundaryLabel 取 features[0].properties.name**（`12aa1f9`·治 `[object Object]`·LLM 转述不可读·zonal/rank/area_stats/compare 4 处）
- **P3 文档债**（`76cfd2d`）：HOME/OFFICE 交接卡同步到 08-08 + cb-index 到 CB-19c
- **P3-1 依赖图评估**：无独立消费者（并行未实施）→ 随 P3-2 一起·不单独推进
- **P2-3 verify_prm57 断言加严**（`a331568`·去宽泛「上传」·加「法定功能区/标准边界」·诚实暴露 PRM-07 空对象真实残余）

### ✅ CB-20 PRM-07 空对象根治完成（两组预检通过·实施 bdde1f0）

- **方案 A 主 + B 兜底**（`bdde1f0`·已推）：A harness derive 失败+boundary 可疑 → `strategy='request_upload'`（复用既有短路·LLM 无法弱化·不依赖 `_regions`·法定功能区无后缀）+ B zonal handler 空对象 → 「需上传标准边界资料」
- **验证**：pytest 303 零回归 · verify_prm07_ab（e2e-seam 可控）：`zonal_stats({})` → 需上传 ✅ 生效（替代「无数据」）
- **工程边界诚实收敛**：浏览器实测 PRM-07 仍受 **LLM 传参方差**影响（空对象/单要素字段名不标准/层未加载）·方案 A/B 覆盖可控场景·完全消除 LLM 行为方差不可能·合理边界
- **新 learning**：`_regions` 正则只匹配区/市/县后缀·法定功能区名提取不到；LLM 字段名不标准时黑名单取不到名

### 🔄 下一步（后置项 · 明日公司电脑续）

- [ ] `git pull`（拉取今日全部 push @ `903632e`）+ 读 OFFICE/HOME 交接卡
- [ ] **PRM-07 残余**：LLM 单要素字段名不标准（无 name/MC/NAME）→ 黑名单扩字段名覆盖（P2 级）
- [ ] **P2-1 多要素全黑名单增强** · RST-L06 Flash 方差 · KDE/DBSCAN 替代 Gi* · 时间轴 manifest
- [ ] **P3-2 并行 + P3-1 依赖图**（`$n` 索引重构前置·规模后启动）

> 📦 08-08 收工：CB-17~CB-20 全闭环 · 发版候选通过 · 交接卡 OFFICE.md 已更新 · 全部已 push @ `903632e`

---

## 📅 2026-08-05（情绪热点图重做专题 + 发版就绪度回归待续）

### 🔄 情绪热点图重做 ·「热力 vs 热点」专题（今日任务）

- **现状（代码实查）**：三轨语义错位——情绪地形（KDE 热力面 `/spatial/terrain`·create_terrain_mesh）+ 情绪热点（逐点 Gi\* `/geo/hotspot`·KNN k=8）+ 热力图（heatmap-tool 委托 terrain 同款）。用户诉求"舆情热度·高程/地势感" = KDE 热力面（业界正名）；现「情绪热点(Gi\*)」是显著性检验，且逐点输入噪声大 + hot/cold→极性色是自造语义。
- **第一轮已完成**：概念基座 + 业界做法核实 → 专题文档 `情绪热点图_热力vs热点_专题讨论_2026-08-05.md`（4 焦点 + 附 A 发组 prompt）
- **第一轮两组回应已回收**：glm组（partial 定位/KNN 尺度漂移修正/invert 链成立/命名表）+ Codex（grid_pois 修正/5 个"热点"语义/dormant deck.gl/spatial_hotspot 字段/无测试护栏/多维归因占位）——两组合点 = KDE 主图 + Gi\* 网格化 + 视觉去极性色 + 命名定标先行
- **用户新增焦点**：热点图（Gi\*）= 2D 即可；热力图 2D+3D vs 2D 需讨论（含 3D 形式）；当前 3D 地形效果差（非连续曲面·无地势感）
- **已完成**：3D 效果差根因（contourpy 等值线环 7 层 → fill-extrusion 逐环固定高度 = 梯田/千层饼非曲面）+ 业界正解调研（MapLibre setTerrain+raster-dem 三角网地形 / deck.gl TerrainLayer / fill-extrusion 改造）→ **第二轮文档** `情绪热点图_第二轮_claude组反评价与3D焦点_2026-08-05.md`（反评价 + 焦点 5 + 附 B 第二轮 prompt）
- **第二轮两组回应已回收**（`情绪热点图_第二轮回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**3D 形式两组全选 a（MapLibre setTerrain+RGB DEM）**——弃 b（deck.gl 本仓踩坑前科）与 c（fill-extrusion=伪曲面）；glm 深化 = setTerrain **全局 draping 风险需 PoC 隔离**（不常驻+互斥+exaggeration+sky）+ A/B 验证升格 P1 前置 + P0 3D 入口与 P1 合并；Codex = 500m 默认+降档护栏+统一三处粒度 + sky/compare/DEM 测试补 6 项
- **已完成**：**定稿执行计划** `情绪热点图_定稿执行计划_2026-08-05.md`（D1-D7 决策 + P0/P1/P1.5/P2 范围 + 闸门 + 待拍板 4 点）——**待用户拍板**
- **待续**：用户拍板（P-1 3D=a 确认 · P-2 2D/3D 共源 · P-3 今天执行范围 · P-4 3D 入口时机）→ 执行（P0 命名定标 + Gi\* A/B 前置 → P1 网格化 → P1.5 setTerrain）

### 🔄 后续任务规划 · 出口三段式 + 工具管线（热点图完成后排期 · 本次纯讨论零代码）

- **用户意图**：① 分析结论「出口」重整理成**新三段式**（替换旧三段式）——第一段=明确观点（基于用户提问·LLM 核心价值）；第二段=4 要点（分析方法/使用数据/分析结果/**分析结论**——观点≠结论：观点=转化解答提问·结论=图数表描述性论述）；第三段=行业接口对标对表→一键入库参数（城市体检/更新·更新需求调研场景·参考国内指标案例）② 工具管线优化（调用/协作线性并行/地点联动）③ 所有工具出口联动地点信息（宏观面域/中微观用地地点·三段式插入环节由成果范式 agent 思考）——目标=出口**既稳定又灵活**
- **已完成**：现状基线实查（四态出口契约·finalStep 极瘦 D019·outlet_kb 7 契约 21 指标映射确定性组装·CB-15 地点联动）→ **讨论发起文档** `情绪地图_出口三段式与工具管线_讨论发起_2026-08-05.md`（5 焦点 F1 映射/F2 观点vs结论/F3 接口参数/F4 地点尺度/F5 管线优先级 + 附 A 发组 prompt）
- **第一轮两组回应已回收**（`情绪地图_出口三段式与工具管线回应_{glm组|Codex-GPT5}_2026-08-05.md`）：两组共识 = A+C 先行 B 后置·落地=前端呈现层+后端确定性聚合·观点段素材现成（提问在 finalStep messages）·地点插入三处力度不同·第三段缺口=业务细化；分歧 = 观点段落点（glm 软扩 vs Codex 零改动+ctx 注入）
- **用户拍板**：Q1 第三段=条件段（意图 agent 判断·未涉归因不入库）· Q2 结论段=确定性为主+LLM 润色可选 · Q3 A+C 先行 B 后置 · **Q4 反馈"观点先行=核心价值（干货）"** → claude组 修正 = **采纳 glm 软扩**（观点段 FINAL_TEMPLATE 正式指令·LLM 必读·先扩 eval 门禁再动）·否 Codex 零改动（ctx 附加提示遵守度弱=价值打折）
- **已完成**：定稿计划（D1-D5 + P0/P1/P2/P3 范围 + 验证）→ **定稿评估发起文档** `情绪地图_出口三段式_定稿评估发起_2026-08-05.md`（定稿计划全文 + 6 焦点 + 附 A 评估 prompt）
- **两组定稿评估已回收**（`情绪地图_出口三段式_定稿评估回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**"有条件执行"**——Codex 阻断 R1（行为 eval 扩）/R2（观点提取兜底契约）+ 警告 W1（基线 2641B 过时）+ W4（条件段不交 LLM）；glm 阻断 B1（风格定调）/B2（结论段独立聚合·不解析 markdown）+ W1（双保险）/W2（结果结构化改动量被低估）
- **用户拍板"定稿执行"→ P0 已实施**：行为 eval 扩（test_final_prompt_has_insight_first 三锚点）+ 体积门禁 <3000B/≤2980B（**实测基线 2833B·非 2641B·观点指令 124B→2957B**）+ FINAL_TEMPLATE 观点先行软扩 + harness ctx 双保险 + onResultStruct hook + 新 result-struct.js（结论段独立聚合·观点三档兜底）+ panel 观点卡/4 要点卡 + CSS · **pytest 283 passed 零回归**（+1 新断言）
- **已完成**：**P0 实施审计发起** `情绪地图_出口三段式P0_实施审计发起_2026-08-05.md`（改动清单 + 6 审计焦点 + 附 A 审计 prompt）
- **两组 P0 审计已回收**（`情绪地图_出口三段式P0_实施审计回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**P0 通过 + 阻断项 B1 + 警告 W1-W3 + 建议项** → **claude组 已全部修复**——B1（runChainPath/runAllToolCalls 补 onResultStruct·抽 _dispatchResultStruct 共享 helper）+ W1（结论段改从 rows 聚合·学术句式·Top 数值+地名+归因）+ W2（体积预算放宽·仅 <3000B·模板冻结加字）+ W3（首段首句兜底删·无标记不显卡）+ 建议项（整块捕获/_pendingStruct send 重置/三锚点位置断言）·**pytest 283 passed + test_emc_template 24 passed + 括号全平衡**
- **用户定**：P0 暂不验（记录·完成后一起验证）→ **推进 P1/P2**
- **已完成**：P1/P2 执行计划 → **P1/P2 计划评估发起** `情绪地图_出口三段式P1P2_计划评估发起_2026-08-05.md`（6 焦点）
- **两组 P1/P2 计划评估已回收**（`情绪地图_出口三段式P1P2_计划评估回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**可执行 + 修正**——glm 阻断 B1（**polarity_index 值域双轨** L1 -1~1/L2 -2~2·分级须归一化）+ W1（"低"档含积极语义）+ W2（覆盖度归一定义）+ W3（CSV 前端入口）；Codex 修正（四档高/中/低/无显著需求·p95 归一+缺省不参与+主题 0/0.5/1·CSV 显式脱敏+outlet_id/name/scale 列·宁夏 5 张映射+8 张边界·limitations 卡级声明·前端导出按钮）
- **✅ P1/P2 已执行完成**（按评估修正）：
  - **P1-1** `grade_demand_intensity(pi, level)`——L2 值域归一（-2~2→-1~1·glm B1）+ 四档（< -0.5 高 / ≤-0.15 中 / ≤0.15 低 / >0.15 无显著需求·Codex W1）·边界 < 修正
  - **P1-2** `priority_score(row)`——p95 归一（Codex W2·防离群格）+ 缺省不参与加权（防缺失反超实值）+ 主题契合 0/0.5/1 + `PRIORITY_WEIGHTS` 常量（启发式初值标注）
  - **P1-3** case_library 四案例 `measure_note`（感知维度非官方评分）+ 出口卡 limitations 卡级声明（"行业案例为对标参照·非评分基准"·双层）
  - **P1-4** `export_outlet_card_csv`（显式脱敏+outlet_id/name/scale 列+BOM）+ **前端导出按钮**（panel.js·glm W3 防空转）+ CSS
  - **P2** 出口卡 `geo_label`（宏观·面域/中观·单元/微观·落点·glm S4）
  - **验证**：pytest **290 passed**（+7 零回归）· validate_outlet_fields 2 passed · CSV 真跑（BOM/列✓）
- **待验收（用户定·完成后一起验证）**：见「整体验收清单」节
- **已完成**：todo 验收清单 + revision-log §5 归档（P0/P1/P2）
- **已完成**：**P3 工具管线计划** `情绪地图_工具管线P3_计划评估发起_2026-08-05.md`（P3-1 依赖图 DAG 判定纯函数·不交 LLM / P3-2 并行执行 Promise.all 同层·PARALLEL_ENABLED 开关 / P3-3 编排器稳定性红线 SOP·先扩 eval 一次一处 / P3-4 地点联动工具出口统一 place_name·5 焦点 + 附 A prompt）
- **两组 P3 计划评估已回收**（`情绪地图_工具管线P3_计划评估回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**两组高度共识 = P3-2 并行执行后置/砍掉**——🔴 `$n` 引用机制依赖严格顺序（tools.js _stepResults 按产出序 push·并行破坏索引确定性·Codex B1 + glm B1 一致）+ 并行收益不足（multi 触发场景多有 $n 依赖·真正可并行极少·Codex B2/glm B2）+ 成本严重低估（3 天→Codex 4-5/glm 5-9 天）；**P3-1 依赖图 + P3-4 地点联动保留**（零红线·可做）；**排期后置到热点图专题之后**（两组一致·避免 harness 撞车）
- **claude组 反评价收敛**：采纳两组共识——**P3 整体后置**到热点图专题完成后（P3-1 依赖图 + P3-4 地点联动保留·P3-2 并行暂不做·待 EMC 规模化）；P3-2 若未来做须先解 `$n` 索引重构（index-based）+ 共享状态隔离（_lastToolRows 确定性选取）·PARALLEL_ENABLED 默认关
- **待续**：回到主线 = **热点图重做专题**
- **用户拍板（P-1~P-4 全按建议）**：P-1 3D=a setTerrain / P-2 2D/3D 不统一 / P-3 B（P0 命名+A/B 前置）/ P-4 随 P1.5 合并开·**强调工具间解耦不互相干扰**
- **✅ P0 命名定标完成**（8 处）：hotspot-tool 图层名「显著聚集点(Gi*)」· grid-tool 占位卡/组卡「显著聚集(Gi*)」· panel.js spatial_hotspot→「代表地点」+ Overview 文案 · test-cases.js 语料 · index.html 注释 · spec.md 字段/调试描述
- **✅ P0-前置 Gi\* A/B 验证完成（重大发现）**：真实 L2 数据（xiling_wujia·2500 点）**逐点/500m 网格/200m 网格 Gi\* 全部无显著热点（全 ns）**——Gi_Z 全在 ±1.07~1.26。**实测根因**：score std 仅 0.377（方差小）+ KNN 邻居 50m~2.5km（尺度漂移·glm 第一轮 B2 证实）+ 阈值 1.96 严。**网格化平滑 Z 但未变全 ns → 输入粒度修正（原 P1 核心）不足以让 Gi\* 出热点**（"效果不对"实锤）
- **两组 P1 修正评估已回收**（`情绪热点图_P1修正回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**根因加深 = score 是 U 形多峰离散分布（5 级极性分类副产物·glm 主因）·与 Gi\* 连续正态假设不匹配**（Codex：局部邻域偏差小=弱信号·降阈值必失败 max\|Z\|1.26<1.65）；**方案收敛 = A 软分级主推（五档·诚实标倾向聚集）·弃 B（逐点无 polarity_index 原生列）·距离带 P2·长期评估 KDE/DBSCAN 替代 Gi\***
- **✅ 热点图 P0/P1/P1.5 已全部实施完成**（工具间解耦）：
  - **P0 命名定标**（8 处）：Gi\*→「显著聚集点(Gi\*)」· spatial_hotspot→「代表地点」·「热力图」统一
  - **P0 前置 A/B**：全 ns 实锤（U 形离散分布·glm 主因）→ 驱动 P1 修正
  - **P1 软分级**：`_classify_hotspot` 五档（hot/tend_hot/ns/tend_cold/cold·threshold 参数化）+ `hotspot_tier` 字段 + 前端 `colorMode='hotspot'` 显著性符号层（弃 `_CLS_POL` 极性色·单色系+大小分档·与 KDE 解耦）
  - **P1.5 setTerrain 3D**：`create_terrain_dem`（F_009·KDE→terrarium RGB·bounds 转 WGS84）+ `/spatial/dem` 端点（header 返 bounds/size）+ `runDem` + map.js `setTerrainDEM`（**draping 隔离**：不常驻+与 3D 网格柱互斥+sky 层）+ `generateTerrain3DForAI`/`closeTerrain3D` + retired.md 渲染路径退役登记（fill-extrusion 3D → setTerrain 连续曲面·2D 等值线保留）
  - **验证**：pytest **293 passed**（+3 零回归）· DEM 解码验证（高度 0~500·峰 500m·bounds WGS84 正确）· 括号全平衡
- **待整体验收**（todo「整体验收清单」·用户定完成后一起验证）· **热点图执行进 CB 审计**（两组·下一步）
- **两组热点图实施审计已回收**（`情绪热点图_实施审计回应_{glm组|Codex-GPT5}_2026-08-05.md`）：**P0+P1 可验收**（命名定标 8 处 + 软分级五档参数化·默认 soft=1.0 解全 ns 显示）· **P1.5 有 B1 阻断**（setTerrain 无用户入口 + EMC 委托未切·与 retired.md 矛盾）
- **✅ 审计修复全部完成**：**B1**（tools.js EMC 委托切 generateTerrain3DForAI·setTerrain 连续曲面）· **W1**（map.js 符号层改纯橙系·弃红蓝双色·与 KDE 解耦）· **W2+W3**（/geo/hotspot 透传 threshold/soft_threshold + legend 五档显著 95%/倾向 84%）· **W6**（tool_contracts/paradigm/stages SKILL_DEFS/validate SKILL_DEFS_DEFAULTS/_KNOWN_SLOTS 契约层五档同步）· **建议级**（index.html:14/1172·state.js:107 注释清理·map.js 注释澄清）
- **验证**：pytest **293 passed** + validate_skill_params/test_emc_template **28 passed** + 括号全平衡
- **待整体验收**（todo「整体验收清单」·出口三段式 P0-P2 + 热点图 P0/P1/P1.5 一起·用户浏览器验收）

---

## 📋 整体验收清单（出口三段式 · 用户定"完成后一起验证"）

> 启动方式：`py frontend/serve.py 8080` 打开 → 浏览器肉眼验收（默认链路·无需 Playwright 除非异步/控制流）。

### P0 验收（观点先行 + 三段式骨架）
- [ ] **观点卡置顶**：问 EMC 一个情绪分析问（如"西陵区哪些区域情绪最差？"）→ 回答顶部出现"观点"强调卡（干货·答"所以呢"）·正文无重复观点行
- [ ] **4 要点卡底部**：回答底部出现"分析支撑（4 要点）"卡——方法/数据/结果/结论四栏（结论含"数据显示 X 区极性指数…"学术句式）
- [ ] **三路径都出卡**：单技能问（默认）+ 多步链问（"裁剪出西陵区情绪点再叠置"·runChainPath）+ 多工具问（multi·runAllToolCalls）——观点卡/4 要点卡都应出现（B1 补丁验证）
- [ ] **无观点不显卡**：若 LLM 未写 `> **观点：**` 标记 → 无观点卡（保守·不取动作描述当观点·W3）
- [ ] **无 console 错**：浏览器 F12 无 JS 报错（Codex W4 浏览器最小验收）

### P1 验收（第三段指标细化 + CSV 入库）
- [ ] **需求强度等级**：出口卡出现"需求强度等级"（高/中/低/无显著需求·四档）——问"西陵区更新需求分析"·若极性偏负应显示"高/中"
- [ ] **复合优先级**：问"更新时序排序"→ 出口卡"优先级排序"为 Top1 区域 + 复合规则（非单一极性降序）
- [ ] **CSV 导出按钮**：出口卡上"导出 CSV"按钮 → 点击下载 CSV（Excel 可开·UTF-8 BOM·含 outlet_id/name/scale 列·脱敏无敏感字段）
- [ ] **案例口径标注**：出口卡 limitations 含"行业案例为对标参照·非评分基准"
- [ ] **地点 scale 标注**：出口卡出现"宏观·面域/中观·单元/微观·落点"（geo_label·随问句尺度）

### P2 验收（地点联动）
- [ ] **结论段带地点**：4 要点卡结论含地点（宏观=面域名/中观=单元名/微观=POI·按尺度）

### 热点图重做验收（另一专题·P-1~P-4 待拍板）
- [ ] 3D 地形 = MapLibre setTerrain 连续曲面（非 fill-extrusion 千层饼）· Gi\* 网格化 · 命名定标（D1-D7·待拍板后）

---

## 📅 2026-08-05（续作 · 发版就绪度回归 + backlog 清理·e2e-seam 解封）

> 公司环境续作（交接卡 7aaa1e4）。用户拍板顺序：**先修 backlog → 修完进 CB 审计回归**。

### ✅ 先修（backlog 已知项全闭环）

- **陈旧注释同步**（Codex ③w7 P2·直接改）：district-stats.js 头部「8 组团」→「4 组团」（含 ③w6b 说明）+ panel.js×7（注释 + **UI 文案「中心城区内 · 4 组团」**）+ panel.css×2
- **MOD_PLACE 渲染风暴·根因修正 + 修**：trace 取证 1595/1602 次 F_002 外层=forward（search_place 链路）·**非地图渲染风暴**（Codex 假设修正）——是 EMC/测试高频地理查询重复全量扫 4310 POI。**修**：forward/reverse 加结果缓存（存副本返副本防污染·超上限清空·纯性能·行为不变）+ test_geocode.py 新增 2 守卫（防污染/一致性）
- **MOD_LLM.F_002 重核**：2476 次调用 attempt≥1 仅 349（14%）·86% 首次成功——**确认调用数非 fallback 数**（Codex 修正成立）·无 while-loop 风暴
- **FC boundary 残余评估**：白名单已落地（tools.js:617-630 deriveAvailable preset 过滤）·未命中走后端诚实报错（PRM-07 弃 fallback）·用户上传层设计不受限——**保持现状·不进修改**
- **e2e-seam 解封（重要发现·阻断所有 browser 测试）**：harness.js `composeGapCard` 漏 `export`（③w4b c53aa99 起）→ e2e-seam import 链崩 → `__emcTest` 永不注入 → link_checkup/gap_wording/flywheel 全超时。**加 export 修复**（纯暴露）·08-04「20/20」是修复前记录·本次真实验证

### ✅ CB 审计回归（发版就绪度）

- pytest **282 passed**（+2 缓存守卫·零回归）
- link_checkup **20/20 PASS**（R9 单测 + fixture 注入 4 行政区 + C2 采样信号 OK·耗时软门槛超时不判失败）
- 措辞断言 **test_gap_wording.py 3 场景 PASS**（③w5 措辞修复前台验证）
- **eval 复采 ×4**：76/73/78/84%——MISS 主因 = **Flash 间歇空流**（API 层 len=0·实测同问重测正常）·加**空流重试 1 次**治测量污染（73-78%→**84% PASS**·与 08-04 持平）·剩余 MISS=2 空流 + 4 已知歧义（rank→zonal/overlay→clip/hotspot→density）·FC 参数 3/3=100%
- **B3 快照重跑 ×3**（`EMOTION_TRACE_SESSION=B3-snapshot-0805` + B3-RSTL06-2/3）·**84.6% / 88.5% / 88.5%**（22/23/23 pass·~10-12min）·fail 全在「参数正确性」PRM（已知 backlog：PRM-03/04 buffer radius 解析·PRM-07 法定功能区白名单执行侧缺口=Codex ③w7「FC boundary 残余」P2）·PRM-01 cell 已修复（500m OK）·**成果范式/Smart/CPD/UI 全 OK**（并发改动影响·需重验）
- **RST-L06 三连 PASS**（tools=clip,density·1→2 层·③w4/③w6b 修复实证）·**用户提示并发任务改成果范式/agent 出口 → RST-L06 结果标注并发改动后需重验**

### 待续（本次未收）

- 时间轴专题（manifest 404·用户定后置）
- **并发任务**（成果范式/agent 出口改动·用户提示）·完成后相关测试（RST-L06/B3 成果范式类）需重验
- PRM backlog（buffer radius·法定功能区白名单执行侧·Codex ③w7「FC boundary 残余」）待 CB 讨论（承重走预检）

---

## 📅 2026-08-04（CB-16 全链路闭环 + 发版准备：Wave 0-3 + ③z 余留 + ③w2~③w7 全局优化/措辞修复/发版收尾）

### ✅ ③w4~③w7 措辞修复 + 发版 backlog 收尾 · 全闭环（两组通过·已推 0bb55df）

- **③w4/③w5 措辞修复 + 发版遗留**（已闭环·78db0e3 + 2130a49）：用户实测「EMC 无法回答时结论'无法生成图层'·但问题可能跟图层无关」→ gap 措辞 failedObs 判据（零工具尝试「无法直接回答/无法理解」·试过工具「未生成图层」）+ eval 标尺纠错（select_template 单工具·76%→84% GO·tuple 双接受）+ RST-L06 preset fallback + buffer stale-tool 门控 + e2e-seam 措辞断言
- **③w6/③w7 发版 backlog 收尾**（已闭环·23efe74 + 0bb55df）：footer 条件化（failedObs>0 才「未生成图层」）+ **preset 行政区清 4 要素**（FIXED_ADMIN_DISTRICTS·备份 .bak9·用户拍板·PRM-07 根治）+ **district-stats 8→4 组团** + RST-L06 fallback 补 MC（Codex P1 死代码）+ eval 注释 + **fixture 静态守卫**（防回潮）
- **验证**：pytest 278 passed 零回归·ESM-OK·eval 84% GO·link_checkup 20/20 PASS·B3 快照 84.6%（方差区间）
- **已推**（0bb55df·先验后推解锁·远端 0/0 同步）
- **待续**：发版就绪度回归（B3 重跑 + eval 复采 + RST-L06 复跑·前台 serve）·时间轴专题（manifest 404 同源派生方案）·backlog（陈旧注释·FC boundary·MOD_PLACE·MOD_LLM.F_002）

### ✅ ③w2/③w3 全局优化 + 发版快照 · 全闭环（两组通过·已推 ff7b125）

- **全局优化**：CLAUDE.md 当前开发状态 5 行（L3✅·L4🔄·空间✅·UI✅·L0→L1 sim）+ todo 周归档（07-27~08-02）+ decisions ADR-017~019 + 记忆 GC
- **backlog 收尾**：validate_skill_params drift 修复（paradigm `_sync_geo_catalog_guard_fields`·1 FAIL→4 passed）+ renewal 卡 perceptible_metrics domain 门控
- **发版快照**：B3 26 例 pass=22（84.6%·Codex 方差区间）·link_checkup 20/20 PASS·tracklog F_002=25 调用·eval 76% NO-GO（③w5 修·标尺错）·RST-L06 回归（③w4 修·clip range derive）
- **已推**（ff7b125·远端同步）

### ✅ Wave 3 + ③z 余留 2b/P2 · 全闭环（两组检查通过·已推）

- **范围**：出口深化最后一块（多卡 + validate_outlet_fields CI + 可感知计算器 2a + **③z 余留 2b + P2**）
- **多卡落地**：resolve_outlet_ids（跨 domain 多卡·同 domain 最高分）+ build_outlet_schema 返 cards + build_outlet_schema_single 兼容 + /outlet_card 返 {cards, card} + 前端多卡渲染
- **validate_outlet_fields CI 落地**：tests/validate_outlet_fields.py（正则提取消费字段→死字段 fail/缺消费 warn）
- **③z 2b 落地**（两组预检 P1×3 全采纳）：`_parse_emc_expr`（拆 `+`·**多值 `/` 拆列表**·含 polarity→2a）+ compute_perceptible_metrics 2a/2b（**生态宜居明示留 2a**·2b 仅可感知·条件不匹配→跳过·**关键词未命中→跳过**·source 对齐）+ `_kw_hit` 共用
- **③z P2 落地**：checkup_satisfaction prose→真实字段（满意度 polarity_index·8 领域 element_top/domain_top **element_top 优先**·不满意项不动）
- **panel.js 渲染 perceptible_metrics**（可感知指标小节·Codex P2 并入）+ .outlet-metrics CSS（③z3b P2-1）
- **③z3b 检查两组通过**（无 P0/P1）·采纳 P2-1/3（CSS + 边界测试·+2）·P2-2（`==`）不采纳
- **验证**：pytest 276 passed（+9）零回归·真端点（cards 2 张 + B 类条件命中出值·source 标条件+命中）
- **已推**（0a0d103·先验后推解锁·远端 0/0 同步）
- **后续**：backlog（7 工具 drift·MOD_PLACE 渲染风暴·MOD_LLM.F_002·CPD-L01/L02·时间轴 manifest·renewal 卡 domain 门控）

### ✅ CB-15 P1 · 实施后检查通过 + P2 补修（**可 push**·先验后推）

- **范围**：让地点进 EMC 问答管线（A buffer 中文 POI + C lookup_place + D 归因落点模板·B 评论↔POI 后置 Wave 3）
- **两组预检反评价**：四子项方向全对路·无 P0
- **A 落地**：`/geo/buffer` fallback search_place（preset 优先·top-1·无命中诚实 400·WGS84·只对 str center）
- **C 落地**：lookup_place 契约后端 + 前端执行混合（TOOL_CONTRACTS + paradigm + tools.js + SKILL_DEFS + GEO_VERB_KW + track ID F_013）
- **D 落地**：_extract_emc_value 扩 `+` 多字段合成 + 暴露 poi_names/place_name_source + 修 :179 陈旧文案
- **两组检查反评价**：通过·可推（buffer 中文名 200/400 实测·drift 既有性回测确认）+ **P2×4 补修**（触发词去"附近"·source 只列非空·docstring 修·required_slots 对齐）
- **验证**：pytest 266 passed 零回归·括号平衡×3
- **backlog**：validate_skill_params 7 工具 drift（density/buffer/clip/overlay/zonal/extract/merge·paradigm when 同步）
- **✅ 可 push**（两组已验）· **待用户 push** · Wave 3

### ✅ Wave 2 / CB-15 数据认知 P0 · 实施后检查通过 + P1/P2 补修（**可 push**·先验后推）

- **范围**：下钻链最小闭环（place_name 双源融合 + poi_names + /grid/pois + 3220 接入 + 去重）
- **两组预检反评价**：P0 实锤 place_layer 未读 3220（1270≠3220·FC 字段错配）→ _read_pois_geojson 适配层 + _load 合并 + _dedup_pois·P1 语义分层（polygon 保留边界名·grid POI 优先·最近质心）+ place_name_source
- **两组检查反评价**：主体通过 + **glm组 P1**（_dedup_pois 连锁店误删·_seen 先锁 name → name+坐标容差联合判定）+ **Codex P2**（create_square_grid 输出 cell_id 列）+ **测试边界 3 新增**
- **验证**：all_pois=4342（恢复 32 误删连锁店）·grid/pois 200（count=32 CBD）·**pytest 261 passed 零回归**（+3 新增）
- **✅ 可 push**（两组已验）· **待用户 push** · P1（lookup_place/归因落点模板）

### ✅ Wave 1（macro 出口）· 实施后检查通过 + P1/P2 补修（**可 push**·先验后推）

- **范围**：renewal_object_identify（更新对象识别·macro）+ checkup_dimension（体检四维度·含 macro）
- **两组预检**：Codex P1（checkup_dimension 四维度×单尺度语义错位→`[scale=xxx]` 槽位限定）+ claude组 P1×3（① `_extract_emc_value` 统一收 rows/features 单入口 ③ DOMAIN_KW 补「城市体检」长词 ⑤ data_base rows 分支·N=单元数）+ rows 可达性缓存（`_lastToolRows`×3）
- **两组检查反评价**：主体通过（5 环节正确·单测 23 passed）+ **glm组 P1**（runAllToolCalls rows 处理·else 误判 + 守护漏 hasRows→三独立 if + hasRows 放行）+ **Codex P1**（跨轮重置 `_lastToolRows = null`）+ P2×2（while-loop rows 捕获 / 测试改名）
- **测试**：pytest 253 passed · 括号平衡 · test_outlet_macro.py E2E 两场景全过
- **✅ 可 push**（两组已验·先验后推）· **待用户 push + 浏览器复验** · **Wave 2（CB-15 前置·后置）**

### ⏸️ CB-15 数据认知（Wave 2 前置·用户定后置·Wave 1 先行）

- 格↔POI sjoin + place_name 双源 + /grid/pois 端点（讨论稿共识已立·落地未做）
- **排进待办**：Wave 1 完成后推进（用户定优先级）

### ✅ R7 补修（commit a42fb1a·**待用户 push**·两组检查反评价）

R7 修复发实施后检查 → 两组 SCAN：**claude组 P0 发现** `lastIndexOf('.')` 误切 markdown 列表标题「**4.**」句点 → 结论第 N 点落 1500 边界时复现原 bug（场景 4 实测）→ **方案 A 去 `.` 切句符**。
- 采纳：Codex 断句符补 `！？` + 悬空编号行剥除（`/\n\d+\.\s*$/`）+ claude组 文案微调（"已精简"→"已截断保留要点"）+ 补边界测试
- **新增** `tests/browser/test_r7_truncation.py`（e2e-seam 直测真实 JS 逻辑·3 场景：多要素完整 / 失控截断无空标题 / {{show:}} 完整）
- **验证**：新测试全过 + 括号配对 +2/+2 + **pytest 249 passed 零回归**
- **待用户 F5 复验**

### ✅ R7 结论截断修复（commit 0aff59e·**待用户 push**·用户实测发现）

用户浏览器实测「大南门·二马路片区更新需求分析」发现结尾「**4.**\n…（结论已截断）」→ 问"未完成"。
- **根因**：R7 防线（harness.js applyQualityDefense）`>800 字 → slice(0,800)` 字符级硬切·阈值过低（用户定：多要素结论超 800 正常）+ 切点不感知 markdown（切「**4.**」标题后）+ R2 按钮被切连带 + 文案误导
- **修复**（纯 harness.js）：阈值 **800→1500**（用户定）+ 切点**结构回切**（句号/换行·治空标题）+ **R2 移 R7 后**（按钮保留）+ 文案场景化
- **验证**：括号配对完整（+7/+7）·Playwright 页面零 console 错误·**pytest 249 passed 零回归**
- **待用户 F5 复验**：重问「大南门·二马路片区更新需求分析」→ 应不再出现「**4.**」空标题

### ✅ 大南门·二马路数据接入 EMC 出口链路（commit c792c5d·**待用户 push**）

交接卡【下一步】核心待续项打穿——Wave 0 端到端演示数据场景。两组预检通过（Codex 必补项 + claude组 建议全纳入）→ 实施 → 验证 249 passed。

- **backfill**：`SCRIPT/backfill_ermawu_coords.py`（一次性·id_e 断言·保 BOM·备份·生成器修复 TODO）→ T1/T2/T3 共 2400 行补 lon/lat
- **注册点层**：`core/geo_registry.py` 追加 `ermawu_l3l4_t{1,2,3}`（level='L3L4'·富归因列原样保留）
- **边界登记**：`DATA/boundaries/presets/manifest.json` 加 `damanmen_area` + **复制 geojson 进 presets/**（Codex 必补项·name 属性改为片区名）
- **测试**：`tests/test_geo_registry.py` 新建 4 例 + `test_outlet_schema.py` +1 真实聚合出卡
- **端到端验证**：/geo/catalog 暴露 3 ermawu 层 + damanmen 边界 → /geo/zonal_stats 578 点（polarity_index 0.73·文化）→ /outlet_card 命中 **renewal_demand 需求分析卡**（需求强度 0.73·停车难·N=578）
- **pytest 249 passed（+7·零回归）**

### 待续
- **浏览器 EMC 真实问答肉眼验证**（问"大南门·二马路片区更新需求分析"→ 应出诊断卡 + 分析执行 + 出口需求分析卡·LLM 选层/路由走真实链路 + **perceptible_metrics 可感知指标小节**）
- **时间轴 manifest（_time_manifest.json）**（用户定·与需求分析是两件事·后置）
- **backlog**：validate_skill_params 7 工具 drift（paradigm when 同步）· MOD_PLACE 渲染风暴 + MOD_LLM.F_002 fallback 重核 + CPD-L01/L02 + 时间轴 manifest 404 · renewal 卡 perceptible_metrics domain 门控（③z3 已知）

---

## 📅 2026-08-03（CB-13 反评价闭环 · 多步问最终收敛 + PRM-08/CPD 根因定案）

### ✅ CB-13 反评价闭环（revision-log 5.254，commit e052fe7 · **用户手动 push**）

- **多步问最终收敛（CB-12→13 闭环）**：RST-L06 两轮连续 PASS·while-loop 根治（F_002=4）·pro 0 守住
- **PRM-08 根因定案**（两组一致）：FC 选型偏离 compare→extract_feature·非路由退化/非测量层·compare 缺确定性路由兜底 → CB-14 修（先取证）
- **CPD-L01/L02 = 测试基建文件名过期**（Codex 实锤）：`test-cases.js:8` 引用已改名的 `xiling_wujia_*`·1 行修复·产品引导逻辑正常
- **上轮 3 注意点已落地**（_hasSeq 收紧·Pro chain 前置·recover 链前置）
- **反评价**：8 agree / 2 partial / 0 disagree·learning 入库 KNOWLEDGE §3
- **backlog 修正**：MOD_LLM.F_002 79 次=调用数非 fallback 数

### ✅ CB-12 B3-verify-05 全量重测闭环（revision-log 5.253，session B3-verify-05 · **用户手动 push**）

- **B3 全量 26 例（含 RST-L06 新增）pass=23（88.5%）历史最佳**·RST-L06 多步问 PASS（tools=clip,density）→ **多步问修复收敛·CB-12 闭环**
- **PRM 9/10**（PRM-08 compare 链路 fail·tools=extract_feature 单工具·boundary[ERR]）·**F_002=4**（≤5 阈值·while-loop 早停生效）·**pro 0**·计划命中 16/20 步
- 0 timeout·误杀/漏判 0·p95 50s·11.2min
- **残余（非阻塞）**：PRM-08（compare 路由退化）+ CPD-L01/02（引导态 hint 未推）·转 backlog
- **下一步**：进入 CB-13（让 Codex/glm 组检查 PRM-08/CPD 残余 + 多步问修复确认）

### 待续

- PRM-08 compare 确定性路由兜底（CB-14·先带 session 取证 FC 选型）
- CPD-L01/L02 测试基建 1 行修复（CSV 改 resolvePoints('L1-T1')）+ CPD-L03 硬断言
- 发版候选评估（B3 88.5% 达标上沿·整体评估）
- MOD_PLACE 渲染风暴 + fallback 重试（backlog）

