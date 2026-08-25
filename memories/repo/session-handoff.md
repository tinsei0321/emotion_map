# Session Handoff · 2026-08-25 晚（office → home）

> ⛔ **已冻结（2026-08-26·PT-CB18 W1-1）**：本卡停止更新，只作历史参考；在途状态唯一落点 = 仓根 `STATE.md`（`py tools/gen_state.py` 生成）+ 阶段交接段模板 `docs/state-handoff-template.md`。观察一阶段后退役。

> 读我即可恢复全部上下文。分支：`EMC_Codex_Harness` · 门禁基线 **616 passed + 1 skipped** · 待推送 11 批。

## 今日成果（全部已 commit·待 push）

| 批次 | 内容 |
|---|---|
| PT-CB15(K1) | 出图双 Bug 治本：几何零转录（layer_output 服务端落盘→render_dataset_id）、manifest 24 断链修复、193 层（含村）入消费面成默认边界、「两个方面」叙事退役、RAG 索引重建 375 chunk、watcher 迟到 TTL、tmp_render 7 天 TTL、transformers 5.x 兼容兜底 |
| PT-CB16(C1C3) | E2E 测试骨架（tests/e2e·真实数据顶点保真）+ SSE 多页面订阅身份/定向投递（render_spec target） |
| PT-CB16(S1) | Codex 侧：环境配方 M1-M3（docs/dsh-environment/）+ 索引半自动重建 |
| PT-CB16(D1→C2) | 交互三机制定稿+实施：会接话（followup_actions 两级 resolved_params）/会请示（身份卡分支请示纪律）/会看大小（scale 确定性倒推·outlet_card scale_check）；契约 docs/interaction-contract.md |
| PT-CB17(B1B4) | cdh 产品层四问题治本：AGENTS.md 身份纪律+回答范式+只读沙箱纪律（仓内权威副本 docs/cdh/AGENTS.md·start.bat 同步）、aggregate_export 全量导出工具（F_044·③档脚本路径退役）、表格 CSS 规范化、RAG 语料扩 DATA 分层（385 chunk·96.7% 门禁零退化） |
| R7+ 防旧码体系 | start.bat 三进程全重置（8000/8080/8600 先杀旧再起新）、devcheck.bat 人话版自检（tools/devcheck.py）、serve.py 启动自检、emc_status 进程自证戳、bat 三铁律（GBK+CRLF+实跑） |

## home 机开工五步（照做即可）

1. `git pull --rebase origin EMC_Codex_Harness`（office 的 11 批要先 push 成功才有得拉）；
2. **重建 RAG 索引**（双机纪律·索引不入仓）：`HF_HUB_OFFLINE=1 py tools/rag_index.py --rebuild`（首次可能需联网下 BGE 模型 92M·加 HF_ENDPOINT=https://hf-mirror.com）；
3. 双击 `start.bat`（三进程全重置+启动自检）；
4. 双击 `devcheck.bat` 确认全绿（人话版·只答能不能测）；
5. 按下面「复测清单」逐项过。

## 复测清单（今日修复的验收口径）

1. 问「你是谁/能做什么」→ 应答 EMC 产品身份，**无「读代码/改文件/跑命令」**；
2. 问「数据分哪几类」→ 应答 权威 AUTHORITY/注册 REGISTRY/专题 THEME/产物 Export 四层；
3. 「投诉 TOP12 社区紫色渲染」→ 图层为**真边界**（万达≈66 顶点量级·非手绘 5-20 点）；全量 20+ 走 aggregate_export 不报沙箱错；
4. 数据类回答 → 三段式（加粗结论+表格+口径段）·表格有网格线/斑马纹；
5. 追问「那第 8 个呢」→ 直接答不重述背景（followup_actions 生效）；
6. 用 130 层口径提问 → AI 应先请示口径（130 历史 vs 193 现行）；
7. 连开两个地图页 → render_spec 带 target 仅目标页上屏，不带则两页同上。

## TODO（按优先级）

| # | 事项 | 负责 | 备注 |
|---|---|---|---|
| T1 | **push 11 批** | 用户（本地终端） | `git push origin EMC_Codex_Harness`；冲突先 pull --rebase |
| T2 | home 机 RAG 索引重建 | 用户/Kimi(home) | 见开工五步-2 |
| T3 | 复测清单 7 项 | 用户 | 异常直接发我 |
| T4 | 口径/身份卡文案过目 | 用户 | manifest 5 条+口径注册表 K-C1/K-01+身份卡两纪律段（措辞均为草案） |
| T5 | C2-4 裁决：cdh 侧胶囊/选项 UI（bridge 透传 1 天） | 主手/用户 | 评估件 docs/catch-ball/discuss/PT-CB16-C2-4评估_cdh侧交互UI载体_Kimi-2026-08-25.md·建议下一批首件 |
| T6 | 浏览器级 E2E 栈验 | Kimi | tests/browser/ptcb16_render_e2e.py（隔离栈 8090/8009·约 2 分钟） |
| T7 | 身份问答观察 | 用户 | 若仍串味→下一步 adapter 层身份直答短路（零 LLM） |
| T8 | 「迎客第一句+首问预热」 | 待立项 | 20:02 汇报建议·可并入 C2-4 |

## 关键环境事实（home 机注意）

- 三进程独立载码：8000 后端/8080 前端/8600 MCP 插座——「重启」=start.bat 全重置，怀疑旧码=devcheck.bat；
- office 网络：github.com 不可直连·push 用 origin（gitee 或用户终端）；
- transformers 5.x 已由 _load_st_model 兼容兜底（rag_index.py）·无需降级；
- RAG 重建命令须加 `HF_HUB_OFFLINE=1`（office 代理环境防 37 分钟联网重试）；
- 本机沙箱 os.remove 拦截：跑 pytest 用 `PYTHONPATH=` 前缀旁路；
- Codex 侧配置在 ~/.codex/config.toml（[mcp_servers.emc] → 8600）·**AGENTS.md 权威副本在 docs/cdh/AGENTS.md**（start.bat 自动同步到 ../_codex_cwd/）。

## 在途协作状态

- Codex：S1/S2 已提交（环境配方+索引半自动）·K1 批次审计已收敛（条件通过·条件项已闭环）；
- Qoder：D1 评审已收敛（四点调整全吸收）；
- 下一批候选：C2-4（bridge 透传）> T6 浏览器栈验 > 迎客第一句。

---

> Kimi · 2026-08-25 22:20 · office 收工。门禁 616+1 绿·三服务全绿·home 见。
