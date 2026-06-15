---
name: volcengine-vision
description: 火山引擎多模态 Embedding API — 提取图片和文本的联合向量表示。用于图片相似度搜索、图文匹配、多模态语义理解。触发场景：用户提到识图、图片理解、多模态、图片搜索、以图搜图、图片特征提取。
---

# 火山引擎多模态识图 (Volcengine Multimodal Vision)

基于火山引擎 Ark 平台的多模态 Embedding API，支持图片+文本的联合向量提取。

## 功能

- **图片特征提取**：将图片编码为向量表示
- **图文联合编码**：同时输入文本+图片，获取多模态联合向量
- **相似度搜索**：通过向量距离实现以图搜图、以文搜图

## Quick Start

```bash
# 提取图片特征向量
python scripts/multimodal_embed.py /path/to/image.png

# 图片+文本联合编码
python scripts/multimodal_embed.py /path/to/image.png --text "图片描述文字"

# 从 URL 提取
python scripts/multimodal_embed.py --url "https://example.com/image.jpg"

# 保存结果到文件
python scripts/multimodal_embed.py /path/to/image.png -o result.json
```

## 环境变量

- `ARK_API_KEY`: 火山引擎 Ark API Key
- `ARK_VISION_MODEL`: 模型端点 ID (默认: ep-20260615134152-wzt8b)

## API 端点

`https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal`

## 限制

- 这是多模态 **Embedding** API（向量提取），不是图片描述生成 API
- 图片支持 URL 或 base64 编码
- 返回高维向量，适合用于相似度计算和搜索
