#!/usr/bin/env python3
"""
火山引擎视觉理解客户端 (Vision Chat)
═══════════════════════════════════════
调用 Ark 平台 Chat Completions API，支持图片+文字输入，
返回模型对图片的文字描述。

用法:
    python vision_chat.py image.png
    python vision_chat.py image.png --prompt "图片里有什么？"
    python vision_chat.py --url "https://..." --prompt "描述这张图片"
    python vision_chat.py image.png -o result.txt
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
    mime_map = {
        "jpg": "jpeg", "jpeg": "jpeg", "png": "png",
        "gif": "gif", "webp": "webp", "bmp": "bmp"
    }
    mime = mime_map.get(ext, "jpeg")
    return f"data:image/{mime};base64,{data}"


def vision_chat(image_url=None, image_path=None, prompt=None,
                api_key=None, model=None, max_tokens=1024):
    """
    调用视觉理解 Chat Completions API。

    Args:
        image_url:  图片 URL（与 image_path 二选一）
        image_path: 本地图片路径（与 image_url 二选一）
        prompt:     文字提示（默认 "请描述这张图片的内容"）
        api_key:    Ark API Key
        model:      模型端点 ID
        max_tokens: 最大输出 token 数

    Returns:
        API 响应的 JSON dict
    """
    api_key = api_key or os.environ.get("ARK_API_KEY", "")
    model = model or os.environ.get("ARK_VISION_MODEL", "ep-20260615141017-zrwzz")

    if not api_key:
        raise ValueError("ARK_API_KEY 未设置。")

    prompt = prompt or "请详细描述这张图片的内容"

    # 构建多模态消息
    content = [{"type": "text", "text": prompt}]

    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    elif image_path:
        data_url = encode_image_base64(image_path)
        content.append({"type": "image_url", "image_url": {"url": data_url}})

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    endpoint = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    resp = requests.post(endpoint, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="火山引擎视觉理解客户端")
    parser.add_argument("image", nargs="?", help="本地图片路径")
    parser.add_argument("--url", help="图片 URL（与本地路径二选一）")
    parser.add_argument("--prompt", default="请详细描述这张图片的内容",
                        help="文字提示 (默认: 描述图片内容)")
    parser.add_argument("--api-key", help="Ark API Key")
    parser.add_argument("--model", help="模型端点 ID")
    parser.add_argument("--max-tokens", type=int, default=1024,
                        help="最大输出 token 数 (默认: 1024)")
    parser.add_argument("-o", "--output", help="保存结果到文件")
    args = parser.parse_args()

    if not args.image and not args.url:
        parser.error("至少需要 image 或 --url")

    try:
        result = vision_chat(
            image_url=args.url,
            image_path=args.image,
            prompt=args.prompt,
            api_key=args.api_key,
            model=args.model,
            max_tokens=args.max_tokens,
        )

        # 提取文本
        content = ""
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]

        print(content)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"\n[OK] 结果已保存到: {args.output}", file=sys.stderr)

    except requests.exceptions.RequestException as e:
        print(f"[ERR] API 请求失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
