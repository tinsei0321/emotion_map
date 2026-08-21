# PT-CB11 · Kimi A-4 版本徽章派发 prompt（zcode 主手·2026-08-22 上午）

> 首批双件回收**通过**（考核=优·见 `PT-CB11-Kimi件回收与claude审计终裁_zcode-2026-08-22.md`）。本件=A-4 版本徽章三件套（PT-CB10 原任务·规格原文引用）。
> 转发方式：下方代码框整段复制给 Kimi。

---

```
【PT-CB11 · Kimi 第二批：A-4 版本徽章三件套】

你是 Kimi。首批双件回收已通过（考核优）。本件=A-4 版本徽章——治「修没修好」自查难：
用户从 netstat+build stamp 三态核对降为看页面角标。纯增益件·规模小。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【开工准备】
git pull origin EMC_harness_dsh（基线最新·含你的 K1/K2 已回收入库）
必读：docs/catch-ball/discuss/PT-CB10-收口批总派发_zcode-2026-08-21.md §A-4 段（规格原文·以下为全文引用）

【三件规格（照 PT-CB10 原文）】

A-4a 服务端 /version 端点
  - 文件：api/render_routes.py（现有 render 路由文件·追加端点）
  - 规格：GET /api/v1/version 返回
    {"commit": "<git rev-parse --short HEAD>", "startup": "<ISO 时间>", "branch": "<分支名>"}
  - git commit 获取：subprocess.run(['git','rev-parse','--short','HEAD'], cwd=REPO)
    ——启动时缓存一次（不每请求跑 git）；分支同理缓存。

A-4b 前端角标
  - 文件：frontend/js/render_client.js（追加）
  - 页面加载时 fetch /api/v1/version → 地图容器左下角（attribution 上方）显示
    v<commit 前 7 位> 小字角标（CSS 内联·不新增文件）；服务不可达不显示（静默降级）。

A-4c 不匹配告警横幅（时间富余才做）
  - 页面加载比较 /api/v1/version 的 commit 与 localStorage 上次记录——不同则黄底横幅一行
    「服务已更新·建议硬刷新（Ctrl+Shift+R）」+点击关闭+自动更新 localStorage。

【注意（与你 K1 的并行衔接）】
- render_client.js 你刚改过（B3-6 段）——基于最新代码追加·勿动你已交付的段落。
- ⚠ api/render_routes.py 模块尾有 watcher 线程自启——测试 import 该模块会起线程，
  参照 tests/test_render_channel.py 既有处理方式（它已 import·无碍·但你的新用例注意清理）。

【测试与交付】
- +1 用例：version 端点返回含 commit 字段（tests/test_render_channel.py）
- python -m pytest tests/ -q 全绿（457 绿+7 存量环境失败为基线·不新增）
- 验收实测：起 8080 → 左下角见 v 角标；改一字符重启 serve → 刷新 → 角标变化
- commit 前缀 PT-CB11(K3): ·显式路径·执行记录落盘
  docs/catch-ball/discuss/PT-CB11-Kimi执行记录A4_Kimi-2026-08-22.md（含验收截图）
- 纪律同首批：禁 emoji·_safe_print·禁宽 except 静默
```

---

> zcode 主手 · 2026-08-22 上午
