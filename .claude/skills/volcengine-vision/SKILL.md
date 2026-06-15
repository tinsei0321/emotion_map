---
name: volcengine-vision
description: 火山引擎视觉理解 + 多模态 Embedding。支持识图、图片内容描述、图片相似度搜索、图文匹配。触发场景：用户提到识图、看图、图片里有什么、描述图片、多模态、以图搜图。
---

# 火山引擎视觉 (Volcengine Vision)

基于火山引擎 Ark 平台，提供两大能力：

## 1. 视觉理解 (Vision Chat) — 识图

**输入图片 → 输出文字描述。** 真正的"看图说话"。

```bash
# 本地图片识图
python scripts/vision_chat.py image.png

# 自定义提问
python scripts/vision_chat.py image.png --prompt "图里有几个人？什么颜色？"

# 从 URL 识图
python scripts/vision_chat.py --url "https://..." --prompt "描述建筑风格"

# 保存结果
python scripts/vision_chat.py image.png -o result.txt
```

## 2. 多模态 Embedding — 向量提取

**输入图片(+文字) → 输出 2048 维向量。** 用于相似度搜索、以图搜图。

```bash
python scripts/multimodal_embed.py image.png
python scripts/multimodal_embed.py image.png --text "描述"
python scripts/multimodal_embed.py --url "https://..."
```

## 环境变量

- `ARK_API_KEY`: 火山引擎 Ark API Key
- `ARK_VISION_MODEL`: 视觉理解模型端点 (默认: ep-20260615141017-zrwzz)
- `ARK_EMBED_MODEL`: Embedding 模型端点 (默认: ep-20260615134152-wzt8b)
