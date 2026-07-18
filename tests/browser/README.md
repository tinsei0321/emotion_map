# EMC Browser 端到端测试

补 EMC eval（`tests/eval_template_flash.py`，空 context 模板路由）测不出的**运行时行为**（C6 盲区）。
复用 `anthropic-webapp-testing` skill（Playwright sync 黑盒脚本范式）+ 本项目 `frontend/serve.py`（自起后端 uvicorn :8000 + /api 反代）。

## 结构

```text
tests/browser/
  lib/emc_helpers.py          # 通用：open_emc / send_prompt / GeoCapture（抓 /geo 调用）/ wait_answer_done
  test_compare_regions.py     # 用例 1：compare 西陵 vs 伍家岗
  fixtures/compare_points.geojson  # 点层 fixture（落西陵/伍家岗区内，供 zonal_stats 聚合）
  README.md                   # 本文件
docs/emc-test-cases.md        # C6 运行时用例清单（catalog，4 例）
```

## 前置

1. **DeepSeek key**：`.env` 配 `DEEPSEEK_API_KEY`（chat 链路需 LLM 跑 diagnose+answer）。
2. **Playwright**：`py -m playwright --version`（项目已装 1.61.0）；首次需 `py -m playwright install chromium`。
3. **Preset 文件**：`data/boundaries/presets/行政区.geojson` 存在（含 西陵区/伍家岗区 feature，nameField=MC）。

## 运行（单命令：测试自管 serve.py）

```bash
py tests/browser/test_compare_regions.py
```

测试自起 `frontend/serve.py :8080`（serve.py 自起后端 uvicorn :8000 + /api 反代 + 等 health），跑完同停。
脚本 exit 0 = 用例绿。

> 不用 `with_server.py`：实测该包装下 main.js 模体加载时序异常（test seam `window.__emcTest` 长时间不可用），
> 而测试自管 serve.py（subprocess + health wait）稳定复现已验证的手动流程。anthropic-webapp-testing skill
> 的 Playwright 黑盒范式仍在 `lib/emc_helpers.py` 内沿用（sync_playwright、侦察后行动、networkidle 陷阱规避）。

## 断言分层（守 verify-real-endpoint：测真业务端点）

- **硬断言（网络层，不依赖 LLM 散文）**：恰好 2× `POST /api/v1/geo/zonal_stats`、均 200、每响应 `rows[0].name` 含对应区名。
- **软断言（回答层）**：`.aiq-answer` 文本含"西陵""伍家岗"（LLM 散文波动，仅 `[WARN]` 不 fail）。

## 加新用例

1. `docs/emc-test-cases.md` 里把用例状态 ⬜→🔄，补描述/前置/步骤/断言。
2. 复制 `test_compare_regions.py` → 改 PROMPT + 断言（复用 `emc_helpers`）。
3. 跑通后 catalog 标 ✅。
