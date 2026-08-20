# PT-CB7 · Qoder 主执行验收报告（zcode 主手·2026-08-21）

> 验收方：zcode（主手·verify-before-accept）。对象：Qoder 主执行 PT-CB7 全批（提交链 5b91f19e→c6013cf8+记录 5772047b）。方法：逐任务独立复验（白名单 diff/代码真身/全量测试/T8 实跑复现/身份卡查询/dsh 侧文件与引用抽查）——不采信执行记录自述。

---

## 〇 验收结论：**通过**——四件 EMC 仓任务全绿（独立复验全对），dsh 环境件半就绪且证据链完整，执行质量与纪律均为高水准。**Qoder 主执行效果评估：优**（详见 §四）。

## 一 逐任务独立复验表

| T | 复验方法 | 结果 |
|---|---|---|
| T1 图层自清理 | 代码真身：`_clearDshLayers()`（getLayers 遍历 `[dsh]` 前缀→removeLayerFromMap+removeLayer 成对·单项 try/catch+计数=A9 口径）·`_apply` 内先于首个 addToolboxLayer 调用（L113） | ✅ 与任务书语义一致 |
| T6 描述紧凑化 | build_server 实测八工具描述 137-247 字符（render_spec 247=11 参数例外）；CALIBERS/G-2 守卫/签名零变化 | ✅ |
| T8 脚本参数化 | **默认参数实跑复现**：ok 11,207 / 网格 434 / 最大格 845 / in_xw 9,004 / in_174 7,656——与原始交付全对；summary.caliber_compare 九字段齐（source_total_with_coords 18,130·landing_rate 61.8%·full_k01/full_k02·subset_declaration·registry_ref·dropped_core_fields）；render_inbox 自清旧 spec 实测生效 | ✅（落点率 61.8% 口径=对源含坐标点 18,130 计算·与全量 49,192 的 22.8% 双口径并存且各声明——正确） |
| T5+T9 身份卡 | `query_knowledge_base(keyword='EMC')` 命中 EMC-IDENTITY-01·四段全含（能做什么/不能做什么/口径纪律/口径对照） | ✅ |
| 白名单 | 四 commit `git show --stat`：各只含任务书白名单文件（T1 两件/T6 一件/T8 两件/T5 一件）·零越界·零 add -A 误扫 | ✅ |
| 全量测试 | `py -m pytest tests/ -q` = **435 passed / 2 skipped**（与自述一致） | ✅ |
| T3（dsh 环境） | bundle 13,631B 在位·四特征（registerTab/emcFullyReady/FIRST_LOAD_GRACE/host.openPath）grep 命中 12 处；**运行时验证未做**（待浏览器实测清单） | ✅ 代码半就绪·验证留 Q2 |
| F1 实证 | config-catalog.md **L926** `reasoningEffort?: 'off'\|'low'\|'high'\|'max'` 精确命中（Qoder 引 L916-926 无误）；结论「分析档=low·无 medium」成立 | ✅ |

## 二 待裁决项处置（主手裁定）

| # | 裁定 | 理由 |
|---|---|---|
| **Q1** 前序 3 文档入库 | **同意保留** | 归档正确·无需 revert |
| **Q2** T3 运行时验证窗口 | **转用户浏览器实测清单**（§三）——8080 停启冷启动场景必须真人点击验证 | 代码已就绪·只剩运行时 |
| **Q3** render_spec 247 字符 | **接受为合理例外** | 11 参数工具·已至最小集·不再压 |
| N1 插件同步提醒 | 记录·非阻塞（归 dsh-profile 仓） | — |
| N2 评估 R1 误判 | 采纳 Qoder 自我纠正（poi 字段=core 有意设计） | 主手确认：`_attach_poi_attrs` 属实 |

## 三 浏览器实测清单（用户参与·dsh 批 2 完成后）

1. dsh web 硬刷新 → 左下角「EMC 情绪地图」按钮在位；
2. 8080 停时点击 → start.bat 弹窗+新会话+欢迎卡 → 就绪后**内嵌 Tab 无乱码**（冷启动场景）；
3. Tab「新窗口打开」按钮 → 外部浏览器开图；
4. 同会话两次 render_spec → 仅剩最新 [dsh] 层（T1 运行时确认）；
5. 新会话问「你是谁」→ 自述 EMC 身份与边界（T5 人设+欢迎卡）。

## 四 Qoder 主执行效果评估（用户「看看效果怎么样」的答案）

**总评：优**——与 dsh 前几批执行对照：

| 维度 | Qoder 本批表现 | 对照 dsh 前批 |
|---|---|---|
| 计划前置 | **强项**：主执行前审计出 M1-M4 四处修正（shared.js 未导出三函数→改 import 真身/测试改静态契约断言/跨源 iframe 不可读 contentDocument→改宽限期 remount/身份卡已存在→原地扩写不重复）——先审计后编码省下至少 3 次返工 | dsh 强在快速执行·偶有"旧版任务书开工"类失配 |
| 委派策略 | 复杂自执/简单派 dsh 三批——正确使用团队（T2/T4/T7 落地交最懂 dsh 的一方） | dsh 全收全做 |
| 自我纠错 | 两处诚实披露（JSX-in-.ts PARSE_ERROR/评估 R1 误判撤回）——学术诚实度最高一档 | 两真发现（PII/双头）也是高水准 |
| 证据纪律 | file:line 引用全部精确命中（L926 实测·bundle 特征 grep） | 同样达标 |
| 文档量 | 3 份（审计/拆解/记录）·我 2 份=本批 5 份 | 略高于 R4 刹车线·但属执行档可接受 |

**结论**：Qoder 具备主执行资质——本次"审计先行+执行"模式值得固化（后续大轮可沿用：执行方先出审计/修正再动工）。dsh 与 Qoder 皆可用，按任务属性分派（dsh 环境件归 dsh·EMC 仓复杂件归 Qoder 或主手）均可。

## 五 下一步

1. **dsh 三批回收**（Qoder 派出的批 1/2/3：T2 决策树+T4 计时取证 / T5 人设落地+T3 运行时验证 / T7 双模预设落地+≤2 分钟验收跑）——dsh 完成后统一送检；
2. **浏览器实测清单**（§三·用户参与）；
3. **终审**：Codex+claude 对本批（Qoder 四 commit+主手验收报告）复核——送审 prompt 随下轮交付。

---

> zcode 主手 · 2026-08-21 · 独立复验·零采信自述
