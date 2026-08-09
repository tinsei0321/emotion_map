# CB 记忆同步 — RAG 补链 + 双环境路径（2026-08-09）

> 同步来源：`docs/catch-ball/_handoff/三组记忆完善prompt_2026-08-09.md` + `三组进入状态通知_RAG补链完成_2026-08-09.md` + KNOWLEDGE.md §2（claude组 已沉淀）。
> 纪律：评估方只读本地·不 git；本笔记为 Codex 侧本地记忆，不 commit。

## 一、RAG 链 = 纯 git 内数据源（换环境可独立重建）

`tools/rag_index.py` 的 4 个来源**全在 repo**（`docs/urban-renewal-plan/` 提炼笔记 + `ai_qa/outlet_kb/` 三 py），OneDrive/G 盘原始资料（875+ 文件）**从不进索引**。换环境只需重建索引，与 OneDrive 路径无关；`{URENEWAL_ROOT}` 仅影响 L0 原文溯源。

## 二、RAG 补链三步（踩坑记录）

1. 依赖：`pip install -r requirements-rag.txt` — torch `2.13.0+cpu` PyPI 默认源无 `+cpu` 标签 → 阿里云镜像 `mirrors.aliyun.com/pytorch-wheels/cpu/torch-2.13.0+cpu-cp314-cp314-win_amd64.whl`（官方 download.pytorch.org 国内慢）。
2. 模型：首次 build 自动下载 BGE `BAAI/bge-small-zh-v1.5`（脚本内置 `HF_ENDPOINT=https://hf-mirror.com`）。
3. 索引：`py tools/rag_index.py --build` — 索引不入 git·**每环境必建**。

## 三、AMAP_KEY 历史会话可找回

高德 key 丢失时从 `~/.claude/projects/<proj>/*.jsonl` grep `AMAP_KEY=` 找回（已恢复·实测 status=1 有效），别重复申请。

## 四、双环境路径

办公室 `G:\` / 家庭 `C:\Users\Hi\OneDrive\2026\15_城市更新专项规划研究`（`docs/urban-renewal-plan/_PATHS.md` + README 已填）。本机（家庭）实测存在·878 文件 ≈ 875。

## 五、本机环境核对记录（Codex 侧·2026-08-09 晚）

| 项 | 状态 | 证据 |
|---|---|---|
| git | ✅ | `fix/emc-buglog` @ `c18b106`（claude组 已 commit·本地即最新） |
| Python | ✅ | `py` = 3.14.6（RAG 链标准解释器；`python` 3.13.2 未装 RAG 依赖，勿混用） |
| RAG 依赖 | ✅ | torch `2.13.0+cpu` + sentence-transformers `5.7.0`（py 3.14 下 pip show 确认） |
| BGE 模型 | ✅ | `~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5` 已缓存 |
| 向量索引 | ✅ | `data/rag_index/` 235 条（fact 36 / note 185 / case 5 / concept 9·512 维·2026-08-09 23:37 建） |
| 检索冒烟 | ✅ | `--query "葛洲坝有哪些更新项目"` → Top-5 含 fact URP-P02 0.752 / URP-P01 0.704（fact 已可命中） |
| .env | ✅ | DEEPSEEK_API_KEY + AMAP_KEY 均在（仅列出 key 名·值不外泄） |
| 家庭路径 | ✅ | `C:\Users\Hi\OneDrive\2026\15_城市更新专项规划研究` 存在·878 文件 |
| Codex hooks | ✅ | SessionStart 已注册 `.codex/hooks.json`（2026-08-09 22:55）·上次 WARN 已消 |

## 六、待命任务预告（RAG 遗留·等 claude组 分配）

B 路径（query_knowledge_base 确定性查询）/ 混合检索（fact 加权或 Top-5 保底 ≥1 fact）/ 全仓 `[中文]+类` 扫描 / Recall@5 素材质量机制 / P0-6 分通道 tier 复审 / L2 出向任务（outlet_kb 接入运行时）。
