#!/usr/bin/env python3
"""
火山引擎多模态 Embedding 客户端
═══════════════════════════════════════
调用 Ark 平台多模态 API，提取图片+文本的联合向量表示。

用法:
    python multimodal_embed.py image.png
    python multimodal_embed.py image.png --text "描述"
    python multimodal_embed.py --url "https://..." --text "描述"
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests


def encode_image_base64(image_path: str) -> str:
    """将本地图片编码为 base64 data URL。"""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    ext = Path(image_path).suffix.lower().lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp", "bmp": "bmp"}
    mime = mime_map.get(ext, "jpeg")
    return f"data:image/{mime};base64,{data}"


def multimodal_embed(image_url=None, image_path=None, text=None, api_key=None, model=None):
    """
    调用多模态 Embedding API。

    Args:
        image_url:  图片 URL（与 image_path 二选一）
        image_path: 本地图片路径（与 image_url 二选一）
        text:       可选的文本输入（用于图文联合编码）
        api_key:    Ark API Key（默认读环境变量 ARK_API_KEY）
        model:      模型端点 ID（默认读环境变量 ARK_VISION_MODEL）

    Returns:
        API 响应的 JSON dict，包含 embedding 向量等字段。
    """
    api_key = api_key or os.environ.get("ARK_API_KEY", "")
    model = model or os.environ.get("ARK_VISION_MODEL", "ep-20260615134152-wzt8b")

    if not api_key:
        raise ValueError("ARK_API_KEY 未设置。请设置环境变量或传入 api_key 参数。")

    # 构建 input 列表
    inputs = []
    if text:
        inputs.append({"type": "text", "text": text})
    if image_url:
        inputs.append({"type": "image_url", "image_url": {"url": image_url}})
    elif image_path:
        data_url = encode_image_base64(image_path)
        inputs.append({"type": "image_url", "image_url": {"url": data_url}})

    if not inputs:
        raise ValueError("至少需要 image_url / image_path / text 之一。")

    payload = {"model": model, "input": inputs}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    endpoint = "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal"

    resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="火山引擎多模态 Embedding 客户端")
    parser.add_argument("image", nargs="?", help="本地图片路径")
    parser.add_argument("--url", help="图片 URL（与本地路径二选一）")
    parser.add_argument("--text", help="可选的文本描述")
    parser.add_argument("--api-key", help="Ark API Key")
    parser.add_argument("--model", help="模型端点 ID")
    parser.add_argument("-o", "--output", help="保存结果到文件")
    args = parser.parse_args()

    if not args.image and not args.url and not args.text:
        parser.error("至少需要 image / --url / --text 之一")

    try:
        result = multimodal_embed(
            image_url=args.url,
            image_path=args.image,
            text=args.text,
            api_key=args.api_key,
            model=args.model,
        )

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"[OK] 结果已保存到: {args.output}")

        # 输出摘要
        data = result.get("data", {})
        if isinstance(data, dict):
            emb = data.get("embedding", [])
            print(f"[OK] embedding dims: {len(emb)}, preview: {emb[:5]}...")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                emb = item.get("embedding", [])
                print(f"[{i}] embedding dims: {len(emb)}, preview: {emb[:5]}...")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"[ERR] API 请求失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
