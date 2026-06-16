# API 约定 (API Conventions)

> 写 API 调用、定义返回格式、对接外部服务时必读本文档。

## API Key 管理

**绝对禁止**在 `.py` 文件中硬编码 API Key。

| 服务 | 环境变量 | 使用模块 |
|------|----------|----------|
| DeepSeek | `DEEPSEEK_API_KEY` | `SCRIPT/relevance_filter.py` |
| 火山引擎 Ark Vision | `ARK_API_KEY`, `ARK_VISION_MODEL` | `SCRIPT/multimodal_analysis.py` |
| 火山引擎 Ark Embed | `ARK_API_KEY`, `ARK_EMBED_MODEL` | `SCRIPT/multimodal_analysis.py` |
| 讯飞 OCR | `IFLYTEK_API_KEY` | `SCRIPT/multimodal_analysis.py` |
| 讯飞 ASR | `IFLYTEK_API_KEY` | `SCRIPT/multimodal_analysis.py` |
| 字节 ASR/TTS | `VOLCENGINE_API_KEY` | `SCRIPT/multimodal_analysis.py` |
| 讯飞 OCR/翻译 | `IFLYTEK_API_KEY` | `.claude/skills/ifly-*` |
| 火山引擎 | `VOLCENGINE_API_KEY` | `.claude/skills/byted-*` |

**管理方式**：
- 开发环境：`.env` 文件（已 gitignore）
- 部署环境：系统环境变量
- 不要在代码中写 fallback 默认值（安全风险）

## HTTP 请求规范

### 重试策略

所有外部 API 调用使用指数退避重试：

```python
MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        return response
    except requests.RequestException:
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)
        else:
            raise
```

### 超时设置

- 常规请求：30 秒
- LLM 批量请求：120 秒
- Vision 视觉分析：120 秒
- OCR 文字提取：60 秒
- ASR 语音转写：300 秒
- 文件上传：300 秒

## 返回格式约定

### 分析结果

```python
{
    'success': bool,
    'n_points': int,
    'score_mean': float,
    'polarity_stats': dict,
    'csv_path': str,
    'geojson_path': str,
    'message': str,
}
```

### 数据加载

```python
{
    'success': bool,
    'df': pd.DataFrame | None,
    'n_rows': int,
    'message': str,
}
```

## 错误处理

- 所有 `except` 块必须记录 `trace_error()`
- 不要在 except 块中静默吞异常
- 对外暴露简化的错误信息，内部记录完整 traceback
- API Key 缺失时明确报错：`raise ValueError("DEEPSEEK_API_KEY 未设置")`

## 安全红线

- API Key **绝不**出现在日志输出中
- API Key **绝不**出现在 commit 中
- 请求 URL 和 payload 在日志中脱敏处理（截断 Key 参数）
