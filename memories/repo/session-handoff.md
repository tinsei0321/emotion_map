# 会话交接卡

> 换机后读取此文件恢复上下文。

## 当前节点 — 2026-06-16 傍晚

### 代码状态

| 模块 | 状态 |
|------|------|
| tests/ | 56 tests 全过 |
| apps/app_main.py | ~350 行，工具栏直接调用弹窗，Import 后 A/OV/TB 立即可用 |
| apps/app_dialogs.py | ~1030 行，Import 用 early-return 关闭模式 |
| apps/app_console.py | 不变 |
| api/ | FastAPI 4 端点，就绪未启动 |
| core/db.py | EmotionDB 就绪 |
| core/spatial_analysis.py | Gi* / Moran's I / 行政聚合 / H3 就绪 |
| SCRIPT/emotion_analysis_v1.py | DeepSeekL2Analyzer 代码就绪，未接入 A 对话框 |
| SCRAPER/spiders/ | 4 个 spider (xiaohongshu/weibo/meituan/su12345) |

### A 对话框当前 UI

```
ENG 分析引擎
  ● L2 . SnowNLP粗粒度分析 (离线)
  ○ L3 . LLM 细粒度语义解析 (DeepSeek)     ← Key 自动从 .env 读取
  ○ L4 . 语料库多维归因 (需 LLM + 语料库)

[开始分析]
```

### 搁置项

- 点击详情面板: `core/ui_components.py` 标记 `[SHELVED]`
- 弹窗按钮样式: 尝试 CSS 调整后还原
- Toast CSS: 尝试调整后还原
- v3 UI 改造: 延后

### CLAUDE.md 新增规则

- 开发工作流: 每次修改后清缓存 + 杀旧进程 + 重启
- 沟通方式: 中文回复, 结论先行
- Git: 提交前展示变更, commit 用英文
- 红线: 删文件/改密钥/push 必须先问

## 下一阶段

**MapLibre GL JS 迁移计划** → 见 `C:\Users\admin\.claude\plans\vibe-coding-skill-agent-sop-ui-mvp-agen-prancy-zebra.md`

回到家用以下命令恢复：
```
cd C:\Users\admin\Documents\GitHub\emotion_map
```
然后说"打开迁移计划"，我会加载计划文件并继续讨论。
