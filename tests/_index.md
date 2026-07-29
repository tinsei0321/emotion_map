# 测试与飞轮总入口

> EMC 测试飞轮 + 单元测试 + bug 追踪的总目录。2026-07-29 整理（含 buglog 扩建 P0/P1）。

## 一、EMC 飞轮（行为测试·`?test=1`）

浏览器开 `http://localhost:8080/frontend/index.html?test=1` 启动。加载链见
[frontend/index.html](../frontend/index.html)（`?test=1` → `test-board.css` + `e2e-seam.js` + `test-board.js`）。

| 文件 | 职责 |
|------|------|
| [frontend/js/test-board.js](../frontend/js/test-board.js) | 飞轮 UI（FAB + 配置弹窗 + 抽屉 + run loop + 报告生成 `_buildMarkdown/_buildJSON` + `POST /_test/report` 落盘） |
| [frontend/js/test-cases.js](../frontend/js/test-cases.js) | 用例定义（`CASES/CATEGORIES`·数据数组展开·no-llm ~45 例 / 全量 250+） |
| [frontend/css/test-board.css](../frontend/css/test-board.css) | 飞轮样式（pass `#0F6E56` / fail `#D85A30` / running `#4285F4` / accent `#D97757`） |
| [emc_test_cases.md](emc_test_cases.md) | 人工用例目录（TC-01~TC-20·Markdown 表格） |

报告 schema = `EMC-SUM v1`（RUN 头含 `pass% / t_p50 / t_p95 / 计划命中`），落盘走
[frontend/serve.py](../frontend/serve.py) `/_test/report` → `tests/reports/report-<date>-<NN>-<type>.{md,json}`。

## 二、Bug 追踪（buglog·新建）

| 路径 | 职责 |
|------|------|
| [buglog/_template.md](buglog/_template.md) | 条目模板（ASCII 标签·≤25 行·只放摘要+指针） |
| [buglog/open/](buglog/open/) `resolved/` | 按 status 分目录（recurring 为 `_trend.md` 派生属性，非独立目录） |
| [buglog/_index.md](buglog/_index.md) | 总索引（自动生成·`py buglog/_gen_index.py`） |
| [buglog/_trend.md](buglog/_trend.md) | 历史复发趋势（repro_count ≥ 2） |
| [buglog/_gen_index.py](buglog/_gen_index.py) | 确定性索引生成器（generate + `--check` CI 守护） |

采集 skill = [.claude/skills/bug-collector/SKILL.md](../.claude/skills/bug-collector/SKILL.md)。
纪律：条目只放摘要 + 指针，详细根因留 [docs/catch-ball/rootcause/](../docs/catch-ball/rootcause/)。

## 三、单元 / E2E 测试

| 路径 | 职责 |
|------|------|
| `test_*.py`（~16 个） | Python 单元测试（坐标/治理/情绪/沙箱/字段字典同步等） |
| [browser/](browser/) | Playwright E2E（EMC 高度适应 / CPD / exit-badge / toolbox 管线等） |
| [browser/flywheel_audit.py](browser/flywheel_audit.py) | 离线批量审计驱动（B0-B3·45+100+100+25 例·三路采集·输出 `browser/out/audit-*.json`） |
| [eval_template_flash.py](eval_template_flash.py) | Flash 路由 eval |
| `validate_*.py` | CI 守护（字段字典同步 / skill 参数） |

> 飞轮（在线·行为）与 flywheel_audit（离线·批量）互补不重叠：前者交互跑、后者大批量采。
> 仪表盘（P2·未实施）将统一读 `reports/*.json` + `buglog/_index.md` 做跨次趋势。

## 四、运行

```bash
py -m pytest tests/ -q                    # 全量单测
py tests/buglog/_gen_index.py             # 刷 buglog 索引
py tests/buglog/_gen_index.py --check     # CI：索引一致性
py tests/browser/flywheel_audit.py --batch B0   # 离线批量审计（no-llm 全量）
```
