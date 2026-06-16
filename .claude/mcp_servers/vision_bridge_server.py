"""
Vision Bridge MCP Server — 让不支持图片的模型也能"看图"
══════════════════════════════════════════════════════
通过 MCP 工具将图片发送给火山引擎 Ark Vision API，
返回文字描述给当前模型。

用法:
  1. 注册到 .mcp.json
  2. 在对话框粘贴图片，VS Code 会保存到文件
  3. 让 Claude 调用 analyze_image 工具

依赖:
  pip install mcp requests
  ARK_API_KEY + ARK_VISION_MODEL 环境变量（.env 中已配置）
"""
import os, sys, base64, json
from pathlib import Path

# 加载 .env
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_path = os.path.join(_PROJECT_ROOT, ".env")
if os.path.exists(_env_path):
    with open(_env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                if key.strip() and key.strip() not in os.environ:
                    os.environ[key.strip()] = value.strip()

from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP("Vision Bridge")


def _encode_image_base64(image_path: str) -> str:
    """将本地图片编码为 base64 data URL。"""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp", "bmp": "bmp"}
    mime = mime_map.get(ext, "jpeg")
    return f"data:image/{mime};base64,{data}"


@mcp.tool()
def analyze_image(
    image_path: str,
    prompt: str = "请详细描述这张图片的内容。如果是UI界面，描述布局、组件、颜色、交互元素。如果是照片，描述场景、人物、情绪、关键物体。"
) -> str:
    """
    分析图片内容，返回文字描述。

    当用户粘贴图片后需要识别图片内容时调用此工具。
    支持本地图片路径（如 docs/vision-inbox/xxx.png 或临时文件路径）。

    Args:
        image_path: 图片文件的绝对路径
        prompt:     可选的识别提示词（默认会全面描述图片内容）

    Returns:
        图片的文字描述
    """
    if not os.path.exists(image_path):
        return f"[ERR] 图片文件不存在: {image_path}"

    api_key = os.environ.get("ARK_API_KEY", "")
    model = os.environ.get("ARK_VISION_MODEL", "")

    if not api_key:
        return "[ERR] ARK_API_KEY 未设置，无法调用视觉 API"
    if not model:
        return "[ERR] ARK_VISION_MODEL 未设置，无法调用视觉 API"

    # 编码图片
    try:
        data_url = _encode_image_base64(image_path)
    except Exception as e:
        return f"[ERR] 图片编码失败: {e}"

    # 构建请求
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": data_url}},
    ]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 2048,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    endpoint = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        if "choices" in data and len(data["choices"]) > 0:
            content_text = data["choices"][0]["message"]["content"]
            return content_text
        else:
            return f"[ERR] API 返回格式异常: {json.dumps(data, ensure_ascii=False)[:500]}"

    except requests.exceptions.RequestException as e:
        return f"[ERR] Vision API 请求失败: {e}"
    except Exception as e:
        return f"[ERR] 未知错误: {e}"


if __name__ == "__main__":
    mcp.run()
