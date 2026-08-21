# PT-CB11 · Kimi 第二批执行记录（A-4 版本徽章三件套）

> 执行：Kimi（WorkBuddy）· 2026-08-22 晨 · 分支 EMC_harness_dsh
> 派发：PT-CB11 K3 派发 prompt（A-4 规格原文=PT-CB10-收口批总派发 §A-4 段）
> commit：`PT-CB11(K3):` ×2（①代码+测试 `6cdf443a` ②本记录+验收截图）

---

## 一 结果速览（三件套全过）

| 件 | 状态 | 证据 |
|---|---|---|
| A-4a /version 端点 | ✅ | `curl :8090/api/v1/version`（经反代）→ `{"commit":"6cdf443a","branch":"EMC_harness_dsh","startup":"2026-08-22T07:00:30+08:00"}` |
| A-4b 前端角标 | ✅ | 截图 `PT-CB11-KimiA4-角标验收截图_Kimi-2026-08-22.png`：#map 左下角 `vbf8c2ab` 小字角标（悬停 title=commit+分支+启动时间） |
| A-4c 不匹配横幅 | ✅ | 截图 `PT-CB11-KimiA4-横幅验收截图_Kimi-2026-08-22.png`：localStorage 置旧 commit 刷新→黄底横幅「服务已更新·建议硬刷新（Ctrl+Shift+R）」；点击关闭；再刷新不重现 |
| 角标跟踪变更 | ✅ | K3 提交后重启栈：角标 `vbf8c2ab` → `v6cdf443`（=K3 提交哈希·截图 `_tmp/kimi_a4_3_after_commit.png` 未提交） |
| 门禁 | ✅ | `py -m pytest tests/ -q`：**483 passed, 2 skipped, 0 failed**（派发基线「457 绿+7 存量环境失败」——本机 7 件存量环境失败未复现·零新增失败·+1 本批用例） |

## 二 改动面（3 文件·白名单内）

1. **api/render_routes.py**（追加·零既有函数体改动）：
   - `_build_version_info()`：`git rev-parse --short HEAD` / `--abbrev-ref HEAD` 各 subprocess 一次 + startup=进程启动 ISO 时间；捕获 `OSError/SubprocessError` 与 `rc!=0` 两档 → 降级空串 + stderr WARN（A9 不静默）。
   - `_VERSION_INFO` 模块级构建（导入=服务装配期·**启动时缓存一次**，不每请求跑 git）。
   - `@router.get('/version')` → 总路径 `/api/v1/version`（随 render_router 挂载）。
2. **frontend/js/render_client.js**（追加尾部·不动 B3-6 等已交付段落）：
   - `_initVersionBadge()`：fetch `/api/v1/version` → `#emc-version-badge` 锚 `#map` 左下（left:10px bottom:96px·在左下缩放/比例尺控件上方）；fetch 失败/无 commit → return 静默降级。
   - A-4c：`localStorage.emc_version_commit` 比对——不同且非首访 → `#emc-version-banner` 黄底横幅（点击关闭）；随后更新记录（首访只记录不打扰·防首次开页误报）。
3. **tests/test_render_channel.py**（+1 用例）：`test_version_endpoint_returns_commit_branch_startup`——三字段齐/commit≥7 位/startup ISO 可解析/**缓存契约（两次调用同一对象·不重复 subprocess）**。

## 三 验收实测（隔离栈·零干扰用户环境）

- **栈**：`py frontend/serve.py 8090 --backend-port 8009 --open=none`（serve.py CB-19 已支持 --backend-port·**不动用户常驻 8080/8000**）。
- **脚本**：`_tmp/pt_cb11_kimi_a4_accept.py`（headless playwright·未提交临时件）。
- **结果 JSON**（原文）：
  ```json
  {"badge_visible": true, "badge_text": "vbf8c2ab",
   "badge_title": "commit bf8c2ab3 · 分支 EMC_harness_dsh · 启动 2026-08-22T06:56:30+08:00",
   "banner_on_mismatch": true, "banner_text": "服务已更新·建议硬刷新（Ctrl+Shift+R）",
   "banner_click_closes": true, "banner_no_reappear": true}
  ```
- **变更跟踪**（派发验收「改一字符重启 serve→角标变化」的如实版）：K3 提交（6cdf443a）→ 重启栈 → /version 与角标同步变为 `v6cdf443`（启动时缓存语义正确）；角标 title 的启动时间同步刷新。

## 四 与设计/既有件的关系说明

- 与 serve.py 既有 build stamp（右下 `build <hash>·<mtime>`）/顶栏 `（build：hash）` **互补不重复**：build stamp 是前端文件 mtime 维度（每请求现算·反映磁盘），A-4 角标是**后端进程维度**（启动时缓存·反映正在跑的服务进程）——「修没修好」自查看的正是后者（后端是否已重启吃到新代码）。
- 角标位置：派发原文「左下角（attribution 上方）」——实测 attribution 在右下（MapLibre 默认），左下为缩放/比例尺控件；角标锚左下控件上方（bottom:96px），不与任何控件重叠（截图可证）。若主手希望严格贴 attribution（右下），一行 cssText 可移。

## 五 纪律自查

- [x] 白名单三文件（render_routes.py / render_client.js / test_render_channel.py）·零越界
- [x] 禁 emoji；服务端 _safe_print；except 具体类型（OSError/SubprocessError）+ WARN 不静默
- [x] 启动时缓存（不每请求 git）·测试锁定缓存契约
- [x] 全量门禁 483 绿零失败（基线 457+7 环境失败·本机未复现失败项·零新增）
- [x] 显式路径 commit ×2（代码+测试 / 记录+截图）·前缀 PT-CB11(K3):
- [ ] push：沙箱无 gitee 凭据（同首批）——用户本机 `git pull --rebase && git push origin EMC_harness_dsh`

> Kimi · 2026-08-22 晨 · A-4 三件套交付·待回收
