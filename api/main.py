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

# CORS — 允许溯佰科平台和本地前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路由 — 重定向到 API 文档。"""
    return {
        "message": "情绪地图 API v1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
