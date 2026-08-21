# PT-CB11 · P1 批独立审计派发 prompt（claude 组·zcode 主手）

> 依据：审计前置（CB 六改·改2）+ A-5 改 scope（审 CB11 首件）。范围=PT-CB11 P1 已合入的两 commit（zcode B3 治本 + Codex 三件工具）。Kimi 件回收后并入或续审。
> 转发方式：下方代码框整段复制给 claude 组。

---

```
【PT-CB11 · P1 批独立审计（claude 组·A-5 改 scope）】

你是 claude 组，EMC 项目第三方独立审计角色。任务：审计 PT-CB11 P1 批已合入的两个 commit。
你是审计方——**零实施零 git 写**，唯一产出=一份审计报告（新建文件·不改任何代码/文档）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【审计对象（两个 commit·分支 EMC_harness_dsh）】

commit A = 0fb5d604（zcode·B3-1/B3-2 注入层灰框治本后端两件）
  - 新建 core/render_policy.py（渲染通道字段政策单一权威源）
  - 改 api/render_routes.py（白名单迁入共享政策+extra_keys 透传）
  - 改 tools/mcp_server_emc.py render_spec（value_field 双层校验）
  - 改 DATA/boundaries/presets/manifest.json（三 preset 增 renderFields）
commit B = 3f9e55a4（Codex·C1 三件 MCP 工具）
  - grid_aggregate(F_033)/compare_regions(F_034)/hotspot_analysis(F_035)
  - +11 测试用例

【必读材料（按序）】

1. docs/catch-ball/discuss/PT-CB11-MCP工具丰富化与注入链路补全_任务书_zcode-2026-08-21.md
   —— 总任务书（§一 B-3 根因链+修复方案·§二 工具通用规格·§七 拍板与并行裁定）
2. docs/catch-ball/discuss/PT-CB11-P1三件工具派发单_Codex_zcode-2026-08-21.md
   —— Codex 的执行规格（审计基准·八条铁则+同文件并行协调区）
3. docs/catch-ball/discuss/PT-CB11-P1三件执行记录_Codex-2026-08-21.md
   —— 执行方自报（真身核对表/五判据答辩/测试）
4. docs/catch-ball/discuss/PT-CB11-P1回收审计_zcode-2026-08-21.md
   —— 主手回收结论（已通过·你的任务是独立复核+挑主手没看到的刺）
5. docs/catch-ball/discuss/PT-CB11-Kimi派发prompt_zcode-2026-08-21.md（背景参考·B3-3~B3-6 前端件尚在途）

【审计维度（七轴·按 docs/catch-ball/RULES.md）】

代码质量/安全/契约合规/守卫有效性/体积纪律/追踪埋点/测试充分性。
重点对抗性检查角度（不限于此）：
- render_policy：政策三层（静态键/前缀/manifest 声明）有没有旁路？
  大文件块解码路径（>25MB 走 4MB chunk raw_decode）会不会误判/漏判？
  api/render_routes 与 mcp_server_emc 两消费方是否真正同源（无双头漂移残留）？
- render_spec 校验：有没有绕过校验的调用路径（如 render_file 内部委托）？
  错误提示会不会泄漏不该外流的字段名（脱敏纪律）？
- 三件工具：边界条件（空点层/boundary 裁剪后零点/全 ns 的 hotspot/top_n=0 或负数）
  会不会抛未捕获异常或返回误导结构？守卫（G-2）是否所有入口都过？
- 并行协调：两 commit 是否真的零冲突互踩（禁改区/取号连续 F_021-F_035）？
- 与前端 render_client.js 消费端的语义对齐（value_field 语义/字段透传）

【环境注意（勿浪费时间）】

- 已知存量失败 7 件=test_sandbox×3（缺 matplotlib）+validate_rag_material×4
  （缺 sentence_transformers）——环境缺依赖·与本批无关·主手已 stash 验证。跳过。
- admin_community preset「文件未上传」=存量数据问题（主手已留档）·跳过。
- 运行测试：python -m pytest tests/test_mcp_server_emc.py tests/test_render_channel.py
  tests/test_d_batch.py -q（应全绿）

【产出】

审计报告落盘：docs/catch-ball/discuss/PT-CB11-P1审计_claude-2026-08-21.md
结构：①逐 commit 裁决（四档：通过/有条件通过/退回/搁置）②发现清单
（编号·严重度 P1-P3·证据 file:line）③对主手回收结论的复核意见
（同意/异议）④测试独立性说明（你自跑了什么·与执行方/主手的验证路径差异）。
纪律：报告用中文·结论先行·每条发现带证据·零 git 写（报告文件除外）。
```

---

> zcode 主手 · 2026-08-21 深夜 · claude 独立审计派发
