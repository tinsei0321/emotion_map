---
name: rag-chain-bringup
description: 换环境补 RAG 链三步（依赖 torch+cpualiyun 镜像 / BGE HF 镜像 / rag_index --build）·数据源纯 git 内不依赖 OneDrive·AMAP_KEY 可从历史会话找回
metadata: 
  node_type: memory
  type: project
  originSessionId: d116c2ed-cb0d-40e1-83eb-ab4a6ee80359
  modified: 2026-08-09T15:50:09.394Z
---

换环境（家/公司）补 RAG 链的三步流程 + 关键坑：

1. **依赖**：`pip install -r requirements-rag.txt`。**坑**：`torch==2.13.0+cpu` 的 `+cpu` 本地标签在 PyPI 默认源没有（报 "No matching distribution"）——必须从国内 PyTorch 镜像拉，实测可用阿里云：`pip install "https://mirrors.aliyun.com/pytorch-wheels/cpu/torch-2.13.0+cpu-cp314-cp314-win_amd64.whl"`。官方 `download.pytorch.org` 国内超慢（15min 无响应）。
2. **模型**：BGE `BAAI/bge-small-zh-v1.5`。`tools/rag_index.py` 脚本内置 `HF_ENDPOINT=https://hf-mirror.com`，首次 build 自动下载。
3. **索引**：`py tools/rag_index.py --build` 重建（约 60s·原子写）。**索引不入 git·每环境必建**。家环境建成 235 条（fact 36 + note 185 + case 5 + concept 9·维度 512）。

**数据源纯 git 内**：`rag_index.py` 4 来源全在 repo（`docs/urban-renewal-plan/` 提炼笔记 + `ai_qa/outlet_kb/` 三 py）·OneDrive/G 盘原始资料（875 文件 docx/pptx/GIS）**从不进索引**——换环境索引重建与 OneDrive 路径无关。`{URENEWAL_ROOT}` 只影响 L0 原文溯源（`_PATHS.md`：办公室 `G:\` / 家庭 `C:\Users\Hi\`·已填）。

**AMAP_KEY 找回**：家 .env 重建丢高德 key → 从 `~/.claude/projects/d--Github-emotion-map/*.jsonl` 历史会话 grep `AMAP_KEY=` 找回（值 7294b86...16·实测 API status=1 有效）。换环境补 .env 先查历史会话，别重复申请。

相关：[[emc-tri-state-exit-contract]]（RAG 检索素材注入 harness）· KNOWLEDGE.md §2「RAG 链纯 git 内数据源」条目。
