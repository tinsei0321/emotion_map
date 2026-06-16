"""
多模态分析引擎 v1.0 — Multimodal Analysis Engine (L3 Vision + OCR + Audio)
==========================================================================
在 L2 SnowNLP 文本分析基础上，增加图像/音频/OCR 多模态分析能力。

设计原则：
  1. 可插拔 — 继承 AnalyzerBase，与 SnowNLP/LLM/Corpus 引擎同接口
  2. 逐级叠加 — Vision/OCR 结果作为 L3 增强字段，不破坏 L2 字段
  3. 容错设计 — API 不可用时优雅降级，不阻塞主 Pipeline
  4. 独立模块 — 不依赖 Streamlit，可被任何应用调用

分析器:
  VisionAnalyzer  — 火山引擎 Ark Vision: 图像情绪+场景+物体识别
  OCRAnalyzer     — 讯飞 iFlytek OCR: 图片/PDF 文字提取
  AudioAnalyzer   — 字节/讯飞 ASR: 语音转文字（框架预留）

用法:
  from SCRIPT.multimodal_analysis import create_multimodal_analyzer
  engine = create_multimodal_analyzer('vision')
  result = engine.analyze_single(image_path='path/to/img.jpg', text='市民评论...')

API 依赖:
  VisionAnalyzer → ARK_API_KEY + ARK_VISION_MODEL (火山引擎 Ark)
  OCRAnalyzer    → IFLYTEK_API_KEY (讯飞 OCR)
  AudioAnalyzer  → IFLYTEK_API_KEY 或 VOLCENGINE_API_KEY

编码铁律:
  - 所有 print() 使用 safe_print()
  - 无 emoji，仅 ASCII 标记 [OK]/[WARN]/[ERR]/[LOAD]
  - API Key 不硬编码，从环境变量读取
  - 公开函数 @track() 装饰，关键分支 TrackContext
==========================================================================
"""
import os, sys, json, time, re, base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

import requests

from core.tracker import track, TrackContext, trace_log, trace_error, register_track_id
from core.utils import safe_print

# 修复 Windows GBK 控制台编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


# ═══════════════════════════════════════════════════════════
# 一、多模态结果数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class MultimodalResult:
    """
    多模态分析统一结果 — 各分析器共用。

    字段按分析器类型逐级叠加：
      VisionAnalyzer → vision_score, vision_scene, vision_objects, vision_summary
      OCRAnalyzer    → ocr_text, ocr_confidence
      AudioAnalyzer  → audio_text, audio_confidence, audio_duration_s
    """

    analyzer_type: str = ''                 # 'vision' | 'ocr' | 'audio'
    success: bool = False                   # 分析是否成功
    error: Optional[str] = None             # 错误信息（成功时为 None）

    # ── Vision 字段 ──
    vision_score: Optional[float] = None    # 视觉情绪得分 0~1
    vision_scene: Optional[str] = None      # 场景分类（公园/街道/商店/餐厅/交通/…）
    vision_objects: Optional[list] = None   # 检测到的城市相关物体列表
    vision_summary: Optional[str] = None    # 图像内容摘要
    vision_confidence: Optional[float] = None  # 视觉分析置信度

    # ── OCR 字段 ──
    ocr_text: Optional[str] = None          # OCR 提取的文字
    ocr_confidence: Optional[float] = None  # OCR 置信度

    # ── Audio 字段 ──
    audio_text: Optional[str] = None        # 语音转文字结果
    audio_confidence: Optional[float] = None  # ASR 置信度
    audio_duration_s: Optional[float] = None  # 音频时长（秒）

    # ── 原始返回（调试用）──
    raw_response: Optional[str] = None

    def to_dict(self) -> dict:
        """转为字典（None 值不输出）"""
        result = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            if k == 'raw_response':
                continue  # 调试字段不输出
            result[k] = v
        return result

    def is_valid(self) -> bool:
        """是否有有效分析结果"""
        return self.success and self.error is None


# ═══════════════════════════════════════════════════════════
# 二、多模态分析引擎抽象接口
# ═══════════════════════════════════════════════════════════

class MultimodalBase(ABC):
    """
    多模态分析引擎基类 — 所有多模态引擎必须实现此接口。

    与 SCRIPT/emotion_analysis_v1.py 的 AnalyzerBase 互补：
      - AnalyzerBase 面向文本情绪分析（L2→L3→L4）
      - MultimodalBase 面向多模态输入（图像/音频/OCR）

    两者通过管道编排器统一调度。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """引擎版本"""
        ...

    @property
    @abstractmethod
    def analyzer_type(self) -> str:
        """分析器类型: 'vision' | 'ocr' | 'audio'"""
        ...

    @abstractmethod
    def analyze_single(self, **kwargs) -> MultimodalResult:
        """分析单条多模态输入，返回 MultimodalResult"""
        ...

    def analyze_batch(self, items: list, progress_callback=None) -> list[MultimodalResult]:
        """
        批量分析（默认逐条调用，子类可覆盖为向量化/并发实现）。

        progress_callback: Optional[Callable[[int, int, str], None]]
        """
        total = len(items)
        results = []
        for i, item in enumerate(items):
            if isinstance(item, dict):
                results.append(self.analyze_single(**item))
            else:
                results.append(self.analyze_single(image_path=str(item)))
            if progress_callback and (i % max(1, total // 10) == 0 or i == total - 1):
                progress_callback(i + 1, total, f'{self.name} {i+1}/{total}')
        return results

    def get_capabilities(self) -> dict:
        """返回引擎能力清单"""
        return {
            'name': self.name,
            'version': self.version,
            'analyzer_type': self.analyzer_type,
            'supports_batch': True,
        }


# ═══════════════════════════════════════════════════════════
# 三、工具函数
# ═══════════════════════════════════════════════════════════

def _encode_image_base64(image_path: str) -> str:
    """将本地图片编码为 base64 data URL。"""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    ext = Path(image_path).suffix.lower().lstrip(".")
    mime_map = {
        "jpg": "jpeg", "jpeg": "jpeg", "png": "png",
        "gif": "gif", "webp": "webp", "bmp": "bmp",
    }
    mime = mime_map.get(ext, "jpeg")
    return f"data:image/{mime};base64,{data}"


def _download_image_to_base64(image_url: str, timeout: int = 30) -> str:
    """下载网络图片并编码为 base64 data URL。"""
    resp = requests.get(image_url, timeout=timeout, stream=True)
    resp.raise_for_status()
    data = base64.b64encode(resp.content).decode("utf-8")

    # 尝试从 Content-Type 推断 MIME
    content_type = resp.headers.get('Content-Type', 'image/jpeg')
    mime = content_type.split('/')[-1] if '/' in content_type else 'jpeg'
    if mime == 'svg+xml':
        mime = 'svg'
    return f"data:image/{mime};base64,{data}"


def _get_image_data(image_path: str = '', image_url: str = '') -> str:
    """
    获取图片的 base64 data URL。

    优先级: image_path > image_url
    返回: data:image/...;base64,... 或 '' (失败时)
    """
    if image_path and os.path.exists(image_path):
        try:
            return _encode_image_base64(image_path)
        except Exception as e:
            safe_print(f'[WARN] 本地图片编码失败: {image_path} | {e}')
            return ''

    if image_url:
        try:
            return _download_image_to_base64(image_url)
        except Exception as e:
            safe_print(f'[WARN] 网络图片下载失败: {image_url[:80]} | {e}')
            return ''

    return ''


# ═══════════════════════════════════════════════════════════
# 四、VisionAnalyzer — 火山引擎 Ark Vision
# ═══════════════════════════════════════════════════════════

# 视觉情绪分析 System Prompt
VISION_EMOTION_PROMPT = """你是一个城市规划与城市治理视觉分析专家。
请分析这张图片，从以下维度输出结构化 JSON（不要包含 markdown 代码块标记）：

{
    "scene": "场景分类（公园/街道/商店/餐厅/交通/市场/广场/住宅/施工/水域/绿地/其他）",
    "visual_sentiment": "视觉情绪倾向（positive/neutral/negative）",
    "sentiment_score": 0.0~1.0之间的浮点数（0=极度负面视觉环境, 1=极度正面视觉环境）,
    "urban_objects": ["检测到的城市相关物体（如路灯、垃圾桶、绿化、停车位、人行道、自行车道、公交站等）"],
    "issues": ["发现的潜在城市问题（如垃圾堆积、路面破损、占道经营、照明不足、绿化缺失等）"],
    "positive_elements": ["值得肯定的积极元素（如整洁环境、良好绿化、完善设施、活力氛围等）"],
    "summary": "一句话总结图片表达的城市感受（<=30字）",
    "confidence": 0.0~1.0之间的浮点数（分析置信度）
}

分析要求：
- visual_sentiment 从城市环境品质角度判断，非纯美学判断
- urban_objects 聚焦城市基础设施和公共空间相关物体
- 如果没有明显城市元素，scene 填 "其他"，confidence 降低到 0.3 以下
"""


class VisionAnalyzer(MultimodalBase):
    """
    火山引擎 Ark Vision 视觉分析引擎。

    对城市相关图片进行视觉情绪分析，提取：
      - 视觉情绪得分（环境品质角度）
      - 场景分类（公园/街道/商店/…）
      - 城市相关物体检测
      - 潜在城市问题识别

    API: 火山引擎 Ark Chat Completions (vision-capable endpoint)
    Key: ARK_API_KEY + ARK_VISION_MODEL 环境变量
    """

    def __init__(self, api_key: str = '', model: str = '',
                 max_tokens: int = 1024, request_timeout: int = 120):
        self.api_key = api_key or os.environ.get('ARK_API_KEY', '')
        self.model = model or os.environ.get('ARK_VISION_MODEL', '')
        self.max_tokens = max_tokens
        self.request_timeout = request_timeout
        self._endpoint = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'

    @property
    def name(self) -> str:
        return 'Volcengine-Vision'

    @property
    def version(self) -> str:
        return '1.0.0-L3-vision'

    @property
    def analyzer_type(self) -> str:
        return 'vision'

    def _check_ready(self) -> Optional[str]:
        """检查 API 就绪状态，返回错误信息或 None"""
        if not self.api_key:
            return 'ARK_API_KEY 未设置'
        if not self.model:
            return 'ARK_VISION_MODEL 未设置'
        return None

    @track("MOD_MM.F_001", track_args=False)
    def analyze_single(self, image_path: str = '', image_url: str = '',
                       text: str = '', custom_prompt: str = '') -> MultimodalResult:
        """
        分析单张图片的视觉情绪。

        Args:
            image_path: 本地图片路径
            image_url:  图片 URL（与 image_path 二选一）
            text:       关联文本（如市民评论原文，用于辅助分析）
            custom_prompt: 自定义提示词（覆盖默认 Prompt）

        Returns:
            MultimodalResult 含视觉情绪分析结果
        """
        ready_err = self._check_ready()
        if ready_err:
            return MultimodalResult(
                analyzer_type='vision', success=False, error=ready_err,
            )

        # 获取图片数据
        image_data = _get_image_data(image_path=image_path, image_url=image_url)
        if not image_data:
            return MultimodalResult(
                analyzer_type='vision', success=False,
                error=f'无法获取图片: path={image_path}, url={image_url[:60] if image_url else "N/A"}',
            )

        # 构建 Prompt
        prompt = custom_prompt or VISION_EMOTION_PROMPT
        if text:
            prompt += f'\n\n[关联文本上下文] 市民原文: "{text[:500]}"'

        # 构建多模态消息
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_data}},
        ]

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # 带重试的 API 调用
        max_retries = 3
        retry_delay_base = 2
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(
                    self._endpoint, headers=headers, json=payload,
                    timeout=self.request_timeout,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    content_text = ''
                    if 'choices' in data and len(data['choices']) > 0:
                        content_text = data['choices'][0]['message']['content']

                    parsed = self._parse_vision_response(content_text)
                    parsed['raw_response'] = json.dumps(data, ensure_ascii=False)
                    parsed['analyzer_type'] = 'vision'
                    parsed['success'] = True
                    return MultimodalResult(**parsed)

                elif resp.status_code == 429:
                    wait_time = retry_delay_base ** attempt
                    safe_print(
                        f'[WARN] Vision API 限流 (429)，'
                        f'第 {attempt}/{max_retries} 次重试，等待 {wait_time}s ...'
                    )
                    time.sleep(wait_time)
                    last_error = 'API 限流 (429)'

                elif resp.status_code in (500, 502, 503, 504):
                    wait_time = retry_delay_base ** attempt
                    safe_print(
                        f'[WARN] Vision API 服务端错误 ({resp.status_code})，'
                        f'第 {attempt}/{max_retries} 次重试，等待 {wait_time}s ...'
                    )
                    time.sleep(wait_time)
                    last_error = f'服务端错误 ({resp.status_code})'

                else:
                    error_msg = f'API 返回非预期状态码: {resp.status_code}'
                    safe_print(f'[ERR] Vision {error_msg}')
                    return MultimodalResult(
                        analyzer_type='vision', success=False, error=error_msg,
                    )

            except requests.exceptions.Timeout:
                safe_print(
                    f'[WARN] Vision API 请求超时，'
                    f'第 {attempt}/{max_retries} 次重试 ...'
                )
                time.sleep(retry_delay_base ** attempt)
                last_error = '请求超时'

            except requests.exceptions.ConnectionError as e:
                safe_print(
                    f'[WARN] Vision 网络连接错误: {e}，'
                    f'第 {attempt}/{max_retries} 次重试 ...'
                )
                time.sleep(retry_delay_base ** attempt)
                last_error = f'网络连接错误'

            except Exception as e:
                safe_print(f'[ERR] Vision 分析异常: {e}')
                trace_error("MOD_MM.D_001", f"Vision analyze exception", exc=e)
                return MultimodalResult(
                    analyzer_type='vision', success=False, error=str(e),
                )

        # 所有重试耗尽
        return MultimodalResult(
            analyzer_type='vision', success=False,
            error=last_error or '重试耗尽',
        )

    def _parse_vision_response(self, response_text: str) -> dict:
        """
        解析 Vision API 返回的 JSON 响应。

        处理常见格式问题：Markdown 代码块、多余空白。
        """
        text = response_text.strip()

        # 去除 Markdown 代码块标记
        if text.startswith('```'):
            lines = text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines).strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取 JSON 对象
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(0))
                except json.JSONDecodeError:
                    return self._default_vision_result(text[:200])
            else:
                return self._default_vision_result(text[:200])

        # 映射到 MultimodalResult 字段
        score = result.get('sentiment_score')
        if score is not None:
            score = float(score)

        sentiment = result.get('visual_sentiment', 'neutral')
        # 将 positive/neutral/negative 映射为 0~1 分数（如果 sentiment_score 缺失）
        if score is None:
            sentiment_map = {'positive': 0.75, 'neutral': 0.5, 'negative': 0.25}
            score = sentiment_map.get(sentiment, 0.5)

        confidence = result.get('confidence')
        if confidence is not None:
            confidence = float(confidence)
        else:
            confidence = 0.7

        return {
            'vision_score': round(score, 2),
            'vision_scene': result.get('scene', ''),
            'vision_objects': result.get('urban_objects', []),
            'vision_summary': result.get('summary', ''),
            'vision_confidence': round(confidence, 2),
        }

    def _default_vision_result(self, raw_preview: str) -> dict:
        """Vision 解析失败时的默认结果。"""
        trace_error("MOD_MM.D_002", f"Vision response parse failed",
                   exc=ValueError(f"raw[:200]: {raw_preview}"))
        return {
            'vision_score': 0.5,
            'vision_scene': '',
            'vision_objects': [],
            'vision_summary': '',
            'vision_confidence': 0.0,
        }

    def get_capabilities(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'analyzer_type': 'vision',
            'supports_batch': True,
            'supports_image_path': True,
            'supports_image_url': True,
            'supports_text_context': True,
            'supports_custom_prompt': True,
            'model': self.model,
            'ready': self._check_ready() is None,
        }


# ═══════════════════════════════════════════════════════════
# 五、OCRAnalyzer — 讯飞 iFlytek OCR
# ═══════════════════════════════════════════════════════════

class OCRAnalyzer(MultimodalBase):
    """
    讯飞 iFlytek OCR 文字提取引擎。

    从图片/PDF 中提取文字内容，用于：
      - 社交媒体截图的文字覆盖提取
      - 12345 工单扫描件文字识别
      - 公告/通知类图片的文字提取

    API: 讯飞 iFlytek OCR API
    Key: IFLYTEK_API_KEY 环境变量

    注意: 讯飞 OCR API 需要 WebSocket 连接或特定的 HTTP 鉴权方式。
    当前实现使用简化的 HTTP 接口框架，具体鉴权逻辑需根据
    讯飞最新 API 文档调整。
    """

    def __init__(self, api_key: str = '', request_timeout: int = 60):
        self.api_key = api_key or os.environ.get('IFLYTEK_API_KEY', '')
        self.request_timeout = request_timeout
        # 讯飞 OCR API 端点（需根据官方文档确认）
        self._endpoint = 'https://api.xf-yun.com/v1/ocr'

    @property
    def name(self) -> str:
        return 'iFlytek-OCR'

    @property
    def version(self) -> str:
        return '1.0.0-L3-ocr'

    @property
    def analyzer_type(self) -> str:
        return 'ocr'

    def _check_ready(self) -> Optional[str]:
        """检查 API 就绪状态"""
        if not self.api_key:
            return 'IFLYTEK_API_KEY 未设置'
        return None

    @track("MOD_MM.F_002", track_args=False)
    def analyze_single(self, image_path: str = '', image_url: str = '') -> MultimodalResult:
        """
        对单张图片/PDF 执行 OCR 文字提取。

        Args:
            image_path: 本地图片/PDF 路径
            image_url:  图片 URL

        Returns:
            MultimodalResult 含 ocr_text, ocr_confidence
        """
        ready_err = self._check_ready()
        if ready_err:
            return MultimodalResult(
                analyzer_type='ocr', success=False, error=ready_err,
            )

        image_data = _get_image_data(image_path=image_path, image_url=image_url)
        if not image_data:
            return MultimodalResult(
                analyzer_type='ocr', success=False,
                error=f'无法获取图片: path={image_path}, url={image_url[:60] if image_url else "N/A"}',
            )

        # 讯飞 OCR 具体 API 鉴权和调用逻辑
        # 参考 .claude/skills/ifly-pdf-image-ocr/ 中的实现
        # 当前提供框架接口，实际接入需根据讯飞 SDK 调整
        with TrackContext("MOD_MM.D_003"):
            try:
                # TODO: 接入讯飞 OCR API 实际调用
                # 讯飞 OCR 通常需要 APPID + APIKey 组合鉴权，
                # 以及特定的请求体格式。参考已有 skill 实现接入。
                trace_log("MOD_MM.D_003",
                         detail="OCR API call placeholder - needs iFlytek SDK integration")
                return MultimodalResult(
                    analyzer_type='ocr', success=False,
                    error='讯飞 OCR API 接入待实现 — 参考 .claude/skills/ifly-pdf-image-ocr/ 完成 SDK 集成',
                )
            except Exception as e:
                safe_print(f'[ERR] OCR 分析异常: {e}')
                trace_error("MOD_MM.D_003", f"OCR analyze exception", exc=e)
                return MultimodalResult(
                    analyzer_type='ocr', success=False, error=str(e),
                )

    def get_capabilities(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'analyzer_type': 'ocr',
            'supports_batch': True,
            'supports_image_path': True,
            'supports_image_url': True,
            'supports_pdf': True,
            'ready': self._check_ready() is None,
        }


# ═══════════════════════════════════════════════════════════
# 六、AudioAnalyzer — 语音转文字（框架预留）
# ═══════════════════════════════════════════════════════════

class AudioAnalyzer(MultimodalBase):
    """
    语音转文字引擎（框架预留）。

    将 12345 热线录音等音频文件转为文本，供后续情绪分析。

    API 选项:
      - 字节跳动 ASR (VOLCENGINE_API_KEY) → 火山引擎语音识别
      - 讯飞 ASR (IFLYTEK_API_KEY) → 讯飞语音转写

    当前状态: 框架已预留，API 接入待实现。
    参考: .claude/skills/byted-voice-to-text/ (字节 ASR)
          .claude/skills/daymade-audio-stepfun-asr/ (阶跃星辰 ASR)
    """

    def __init__(self, api_key: str = '', provider: str = 'volcengine',
                 request_timeout: int = 300):
        self.api_key = api_key or os.environ.get(
            'VOLCENGINE_API_KEY' if provider == 'volcengine' else 'IFLYTEK_API_KEY', ''
        )
        self.provider = provider
        self.request_timeout = request_timeout

    @property
    def name(self) -> str:
        return f'ASR-{self.provider}'

    @property
    def version(self) -> str:
        return '1.0.0-L3-audio-dev'

    @property
    def analyzer_type(self) -> str:
        return 'audio'

    def _check_ready(self) -> Optional[str]:
        if not self.api_key:
            return f'{self.provider.upper()}_API_KEY 未设置'
        return None

    @track("MOD_MM.F_003", track_args=False)
    def analyze_single(self, audio_path: str = '') -> MultimodalResult:
        """
        对单个音频文件执行语音转文字。

        Args:
            audio_path: 本地音频文件路径

        Returns:
            MultimodalResult 含 audio_text, audio_confidence
        """
        ready_err = self._check_ready()
        if ready_err:
            return MultimodalResult(
                analyzer_type='audio', success=False, error=ready_err,
            )

        if not audio_path or not os.path.exists(audio_path):
            return MultimodalResult(
                analyzer_type='audio', success=False,
                error=f'音频文件不存在: {audio_path}',
            )

        with TrackContext("MOD_MM.D_004", audio_path=audio_path):
            try:
                # TODO: 接入 ASR API 实际调用
                # 参考 .claude/skills/byted-voice-to-text/ (字节)
                # 或 .claude/skills/daymade-audio-stepfun-asr/ (阶跃)
                trace_log("MOD_MM.D_004",
                         detail="ASR API call placeholder - needs SDK integration")
                return MultimodalResult(
                    analyzer_type='audio', success=False,
                    error='ASR API 接入待实现 — 参考已有 skill 完成 SDK 集成',
                )
            except Exception as e:
                safe_print(f'[ERR] ASR 分析异常: {e}')
                trace_error("MOD_MM.D_004", f"ASR analyze exception", exc=e)
                return MultimodalResult(
                    analyzer_type='audio', success=False, error=str(e),
                )

    def get_capabilities(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'analyzer_type': 'audio',
            'supports_batch': True,
            'provider': self.provider,
            'ready': self._check_ready() is None,
        }


# ═══════════════════════════════════════════════════════════
# 七、引擎工厂
# ═══════════════════════════════════════════════════════════

@track("MOD_MM.F_004", track_args=False)
def create_multimodal_analyzer(engine: str = 'vision', **kwargs) -> MultimodalBase:
    """
    多模态引擎工厂 — 统一创建入口。

    用法:
        # Vision: 图像情绪分析
        engine = create_multimodal_analyzer('vision')
        engine = create_multimodal_analyzer('vision', api_key='...', model='ep-xxx')

        # OCR: 文字提取
        engine = create_multimodal_analyzer('ocr')
        engine = create_multimodal_analyzer('ocr', api_key='...')

        # Audio: 语音转文字
        engine = create_multimodal_analyzer('audio')
        engine = create_multimodal_analyzer('audio', provider='volcengine')

    Args:
        engine: 'vision' | 'ocr' | 'audio'
        **kwargs: 传递给具体引擎构造函数的参数

    Returns:
        MultimodalBase 子类实例
    """
    engines = {
        'vision': VisionAnalyzer,
        'ocr': OCRAnalyzer,
        'audio': AudioAnalyzer,
    }
    cls = engines.get(engine)
    if cls is None:
        raise ValueError(
            f'未知多模态引擎: {engine}。可用: {list(engines.keys())}\n'
            f'  vision → 火山引擎 Ark Vision 图像情绪分析\n'
            f'  ocr    → 讯飞 iFlytek OCR 文字提取\n'
            f'  audio  → 字节/讯飞 ASR 语音转文字'
        )

    # 只传目标引擎接受的参数
    valid_params = {
        'vision': {'api_key', 'model', 'max_tokens', 'request_timeout'},
        'ocr':    {'api_key', 'request_timeout'},
        'audio':  {'api_key', 'provider', 'request_timeout'},
    }
    filtered = {k: v for k, v in kwargs.items()
                if k in valid_params.get(engine, set())}
    return cls(**filtered)


# ═══════════════════════════════════════════════════════════
# 八、便捷函数 — 批量多模态分析
# ═══════════════════════════════════════════════════════════

@track("MOD_MM.F_005", track_args=True)
def analyze_images(df, text_col: str = 'text',
                   image_url_col: str = 'image_url',
                   image_path_col: str = '',
                   engine: Optional[VisionAnalyzer] = None,
                   progress_callback=None) -> list[MultimodalResult]:
    """
    对 DataFrame 中的图片进行批量视觉分析。

    Args:
        df:              包含文本和图片列的 DataFrame
        text_col:        文本列名（用于辅助视觉分析）
        image_url_col:   图片 URL 列名
        image_path_col:  本地图片路径列名（与 image_url_col 二选一）
        engine:          已初始化的 VisionAnalyzer（None 则自动创建）
        progress_callback: 进度回调

    Returns:
        list[MultimodalResult] 与 df 行对应的结果列表
    """
    if engine is None:
        engine = create_multimodal_analyzer('vision')

    # 检查就绪状态
    if not isinstance(engine, VisionAnalyzer):
        safe_print('[WARN] analyze_images 需要 VisionAnalyzer 引擎')
        return []

    ready_err = engine._check_ready()
    if ready_err:
        safe_print(f'[WARN] Vision 引擎未就绪: {ready_err}')
        return []

    total = len(df)
    results = []

    for i, (_, row) in enumerate(df.iterrows()):
        image_url = str(row.get(image_url_col, '')) if image_url_col in df.columns else ''
        image_path = str(row.get(image_path_col, '')) if image_path_col and image_path_col in df.columns else ''
        text = str(row.get(text_col, '')) if text_col in df.columns else ''

        if not image_url and not image_path:
            results.append(MultimodalResult(
                analyzer_type='vision', success=False,
                error='no image available',
            ))
        else:
            result = engine.analyze_single(
                image_path=image_path, image_url=image_url, text=text,
            )
            results.append(result)

        if progress_callback and (i % max(1, total // 10) == 0 or i == total - 1):
            progress_callback(i + 1, total, f'Vision {i+1}/{total}')

    return results


@track("MOD_MM.F_006", track_args=True)
def merge_multimodal_to_df(df, vision_results: list[MultimodalResult] = None,
                            ocr_results: list[MultimodalResult] = None,
                            audio_results: list[MultimodalResult] = None):
    """
    将多模态分析结果合并到 DataFrame。

    在 df 上直接添加多模态字段列（原地修改）。

    Args:
        df:              目标 DataFrame
        vision_results:  VisionAnalyzer 结果列表
        ocr_results:     OCRAnalyzer 结果列表
        audio_results:   AudioAnalyzer 结果列表
    """
    n_rows = len(df)

    # ── Vision 字段 ──
    if vision_results and len(vision_results) == n_rows:
        with TrackContext("MOD_MM.D_005", n_results=len(vision_results)):
            df['vision_score'] = [
                r.vision_score if r.vision_score is not None else None
                for r in vision_results
            ]
            df['vision_scene'] = [r.vision_scene or '' for r in vision_results]
            df['vision_objects'] = [
                json.dumps(r.vision_objects, ensure_ascii=False)
                if r.vision_objects else ''
                for r in vision_results
            ]
            df['vision_summary'] = [r.vision_summary or '' for r in vision_results]
            df['vision_confidence'] = [
                r.vision_confidence if r.vision_confidence is not None else None
                for r in vision_results
            ]
            n_valid = sum(1 for r in vision_results if r.is_valid())
            safe_print(f'[OK] Vision 结果合并: {n_valid}/{n_rows} 成功')

    # ── OCR 字段 ──
    if ocr_results and len(ocr_results) == n_rows:
        with TrackContext("MOD_MM.D_006", n_results=len(ocr_results)):
            df['ocr_text'] = [r.ocr_text or '' for r in ocr_results]
            df['ocr_confidence'] = [
                r.ocr_confidence if r.ocr_confidence is not None else None
                for r in ocr_results
            ]
            n_valid = sum(1 for r in ocr_results if r.is_valid())
            safe_print(f'[OK] OCR 结果合并: {n_valid}/{n_rows} 成功')

    # ── Audio 字段 ──
    if audio_results and len(audio_results) == n_rows:
        with TrackContext("MOD_MM.D_007", n_results=len(audio_results)):
            df['audio_text'] = [r.audio_text or '' for r in audio_results]
            df['audio_confidence'] = [
                r.audio_confidence if r.audio_confidence is not None else None
                for r in audio_results
            ]
            n_valid = sum(1 for r in audio_results if r.is_valid())
            safe_print(f'[OK] Audio 结果合并: {n_valid}/{n_rows} 成功')


# ── 追踪 ID 注册表 ──
register_track_id("MOD_MM.F_001", "VisionAnalyzer.analyze_single（单张图像视觉情绪分析）")
register_track_id("MOD_MM.F_002", "OCRAnalyzer.analyze_single（单张图片OCR文字提取）")
register_track_id("MOD_MM.F_003", "AudioAnalyzer.analyze_single（单个音频语音转文字）")
register_track_id("MOD_MM.F_004", "多模态引擎工厂（create_multimodal_analyzer）")
register_track_id("MOD_MM.F_005", "批量图像分析（analyze_images）")
register_track_id("MOD_MM.F_006", "多模态结果合并到DataFrame（merge_multimodal_to_df）")
register_track_id("MOD_MM.D_001", "VisionAnalyzer API调用异常捕获")
register_track_id("MOD_MM.D_002", "VisionAnalyzer JSON响应解析降级")
register_track_id("MOD_MM.D_003", "OCRAnalyzer OCR API调用块")
register_track_id("MOD_MM.D_004", "AudioAnalyzer ASR API调用块")
register_track_id("MOD_MM.D_005", "merge_multimodal_to_df Vision字段合并块")
register_track_id("MOD_MM.D_006", "merge_multimodal_to_df OCR字段合并块")
register_track_id("MOD_MM.D_007", "merge_multimodal_to_df Audio字段合并块")
