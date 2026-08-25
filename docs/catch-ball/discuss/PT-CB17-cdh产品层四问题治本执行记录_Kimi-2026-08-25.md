# PT-CB17 · cdh 产品层四问题治本执行记录（Kimi·2026-08-25）

> **触发**：用户手动测试 cdh 报四问题（身份认知串味/RAG 未吸收 DATA 分层/出图沙箱拦截/排版丑），用户令「治本·系统性解决一类问题」。
> **统一根因**：**引擎更替（dsh→cdh）时产品层未随迁**——dsh 时代装在 profile/persona/脚本生态里的「身份、范式、数据产物通道」在 cdh 侧分别缺位，四个问题是同一断层的四个剖面。
> **门禁**：**616 passed / 1 skipped**（613+1 → 净 +3：aggregate_export×2 + data_readmes×1；零失败）。**RAG 门禁 Recall@5=96.7% 守住零退化**（语料 375→385 chunk）。
> **git**：未 commit（建议前缀 `PT-CB17(B1B4)`·主手/用户代提交）。

## 白话摘要

四个病其实是一个病：换了「大堂经理」（新引擎 Codex）后，原来贴在旧经理身上的「员工守则」没抄给新经理——所以它用程序员口吻自我介绍、不知道资料怎么分类、想用旧方法（写脚本）做菜却被厨房新规（只读沙箱）拦住、上菜摆盘也没人教。修法是补一套完整的「新员工守则」：①身份卡写死「你是情绪地图产品，不是编程助手」；②资料分类手册接进它的知识库；③「全量出图」做成一个正规工具，再也不需要写脚本；④回答排版立了三段式规矩，表格也加了网格线样式。

## 一、四问题根因与治本对照

| # | 用户现象 | 根因（实证） | 治本方案 | 状态 |
|---|---|---|---|---|
| B1 | 身份问答自称「读代码改文件跑命令」（Codex 桌面身份） | `_codex_cwd/AGENTS.md` 产品层只有一句身份·**无身份问答口径与禁自述条款**；身份类提问模型不查 RAG 直接以系统人设作答 | AGENTS.md 补【身份纪律】（EMC 产品身份问答口径+严禁 Codex/编码助手自述）+【回答范式】三段式/表格/排版规范+【只读沙箱纪律】；**权威副本入仓 `docs/cdh/AGENTS.md`**（原文件在仓外·无双机配方）+ start.bat 启动强制同步 | ✅ |
| B2 | 出图报「进程创建被沙箱拦截」 | codex_bridge `thread/start` 定参 **`sandbox: 'read-only'` + `approvalPolicy: 'never'`**（codex_bridge.py L198）——cdh 下脚本造文件**设计上必失败**，而 render-contract ③档仍教模型「脚本+注册」 | ③档**工具化**：新工具 `aggregate_export`（F_044·服务端全量聚合+落盘+永久注册→dataset_id·zonal 同源无截断）；render-contract ③档改写+list_data paradigm 同步+AGENTS.md 明令「禁脚本造文件」 | ✅ |
| B3 | 排版丑·无主次·表格无网格 | cdh 无回答范式契约（dsh 时代的范式在 profile 提示词里未随迁）+ 前端 markdown 表格零样式 | 范式入 AGENTS.md（与 B1 同件·三段式：结论句/证据段（表格化）/口径段）；`ai_qa.css` 增表格规范样式（网格线/表头底色/斑马纹/紧凑标题） | ✅ |
| B4 | RAG 不知「权威/专题」分层 | rag_index 语料=docs/urban-renewal-plan+事实卡+案例+概念卡——**DATA 目录文档从未入语料**（DATA/README.md 分层单一权威在语料外）；实测检索分层关键词命中无关旧文档 | loader 增 `_load_data_readmes()`（DATA/README.md+THEME READMEs·治理字段同纪律·单一权威保持·索引为只读镜像防双头）；重建 385 chunk；检索实测 Top-1=DATA/README#1 | ✅ |

## 二、改动文件

- 新增：`docs/cdh/AGENTS.md`（产品层权威副本）、本记录
- 修改：`_codex_cwd/AGENTS.md`（同步·仓外派生）、`start.bat`（同步步骤）、`tools/mcp_server_emc.py`（aggregate_export+_register_dataset+F_044 注册+守卫表+paradigm）、`tools/rag_index.py`（_load_data_readmes 接入 load_chunks）、`docs/render-contract.md`（③档工具化）、`frontend/css/ai_qa.css`（表格样式）、`tests/test_mcp_server_emc.py`（+2）、`tests/test_rag_loader.py`（公式更新+1 新测）、`docs/progress.md`（刷新）
- 派生：`DATA/RAG/rag_index/`（385 chunk）

## 三、验收口径（R7 三态：重启 8000+强刷 8080）

1. 问「你是谁/你能做什么」→ 回答为 EMC 产品身份（情绪地图分析/出图/知识库/口径纪律），**无「读代码/改文件/跑命令」表述**；
2. 问「数据分哪几类/什么是权威数据」→ 命中 DATA 分层（AUTHORITY 权威/REGISTRY 注册/THEME 专题/Export 产物）；
3. 全量出图（如「20 个社区渲染」）→ 模型调 aggregate_export（不再出现沙箱报错）→ render_spec dataset_id 上屏；
4. 数据类回答 → 三段式（结论加粗+表格+口径段）；表格有网格线/表头底色/斑马纹。

## 四、遗留与建议

1. **身份问答的兜底观察**：AGENTS.md 指令对身份类提问的约束依赖模型遵守（无代码短路）——若复测仍串味，下一招是 adapter 层身份问题直答短路（检测身份意图→直接以 EMC-IDENTITY-01 组装回答·零 LLM）；
2. 表格数字列右对齐需 markdown 对齐语法（`:---:`）——已写入 AGENTS.md 表格规范由模型生成控制；
3. C2-4（cdh 侧胶囊/选项 UI）仍在评估待裁决；「迎客第一句+首问预热」建议（20:02 汇报）未立项；
4. 复测通过前本批与今日前四批一并待 push（共五批）。

---

> Kimi · 2026-08-25 · B1-B4 全做·门禁 616+1·RAG 96.7% 零退化。
