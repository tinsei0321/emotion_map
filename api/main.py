"""
FastAPI 应用入口

启动:
    uvicorn api.main:app --reload --port 8000

访问:
    API 文档: http://localhost:8000/docs
    健康检查: http://localhost:8000/api/v1/health
"""
import os
import sys

# 确保项目根在 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_env_file():
    """轻量 .env 加载（不依赖 python-dotenv）：解析项目根 .env → 注入 os.environ（不覆盖已有）。
    让 DEEPSEEK_API_KEY 等 key 持久化（serve 重启不丢、终端无关）。
    前端后端入口（uvicorn api.main:app）默认不读 .env——本函数补齐与遗留 Streamlit
    入口（app_main._load_dotenv）一致的体验，避免 key 只在某终端会话有效、serve 起的后端读不到。"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass   # .env 解析失败不阻塞启动（key 缺失由 LLMClient._ensure_key 明确报错）


_load_env_file()   # FastAPI app 构建前注入 .env

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router

app = FastAPI(
    title="情绪地图 API",
    description="城市情绪空间分析引擎 — 溯佰科平台 Agent 接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — 仅允许本机 origin（localhost/127.0.0.1 任意端口）。
# 收紧自 allow_origins=["*"]（加固③，配合 /run 代码执行端点）：serve.py 反代是同源
# （:8080→:8000 服务端完成，浏览器不跨域），正常开发链路 CORS 不触发；此设置只在
# 「浏览器直连后端」的开发场景放行本机，挡住外部网页远程调用 /run 等敏感路由。
# 生产部署须进一步收紧到真实域名。
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r'https?://(localhost|127\.0\.0\.1)(:\d+)?',
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# AI 问答子系统（独立 router，挂同 prefix；/chat 总路径 /api/v1/chat）。
# 子系统代码在 ai_qa/（manifesto/prompts/review/schemas/router/llm），未来做厚都在该目录内演进。
from ai_qa.router import router as ai_qa_router
app.include_router(ai_qa_router, prefix="/api/v1")

# GIS 工具箱子系统（/geo/* 总路径 /api/v1/geo/*）——AI 问答内由模型自动调用的 GIS 原子操作。
# 复用 core/spatial_analysis + core/range_selector + core/geo_registry（GeoPandas，不造轮子）。
from api.geo_routes import geo_router
app.include_router(geo_router, prefix="/api/v1")

# AI 问答自成长知识闭环（/aiqa/* 总路径 /api/v1/aiqa/*）——L2 wisdom 读出 + L3 episode 记录。
# 三层闭环：L1=MANIFESTO / L2=ai_qa/wisdom.py（人审策展） / L3=DATA/ai_qa/episodes.jsonl（consolidate 挖掘）。
from api.aiqa_routes import aiqa_router
app.include_router(aiqa_router, prefix="/api/v1")

# /run 代码执行端点（P3 sandbox，须 SAFE_READY=True 才挂）。
# SAFE_READY 是红线开关：sandbox 单测全过 + 人审后置 True；置 False 时此 if 自动卸载 /run（单点 revert）。
# 安全现状（演示版底线）：open-wrapper + AST 反射 + frame-based eval + CORS 本机，非 OS 级隔离。
from api.run_routes import run_router
from api.sandbox import SAFE_READY
if SAFE_READY:
    app.include_router(run_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路由 — 重定向到 API 文档。"""
    return {
        "message": "情绪地图 API v1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
