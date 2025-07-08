import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from sqlmodel import Session
import uvicorn
from pathlib import Path
import time
from datetime import datetime

from config import settings
from database import get_session, create_db_and_tables
from logger_config import logger

# 导入各个应用的路由
from apps.users.router import router as users_router
from apps.reading_fluency.router import router as reading_fluency_router
from apps.attention_test.router import router as attention_test_router
from apps.calculation_test.router import router as calculation_router  # 新增计算流畅性测试路由

# 未来可以导入其他测试系统的路由


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="认知能力评估平台API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
# 用户管理路由
app.include_router(users_router, prefix=f"{settings.API_PREFIX}/users")

# 测试系统路由
app.include_router(reading_fluency_router, prefix=f"{settings.API_PREFIX}/reading-fluency")
app.include_router(attention_test_router, prefix=f"{settings.API_PREFIX}/attention-test")
app.include_router(
    calculation_router, prefix=f"{settings.API_PREFIX}/calculation"
)  # 新增计算流畅性测试路由

# 未来可以注册其他测试系统的路由


# 挂载静态文件服务（前端资源）
static_dir = Path("dist")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_spa(request: Request):
    """提供前端SPA页面"""
    index_html = static_dir / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return HTMLResponse("<html><body><h1>认知能力评估平台</h1><p>前端资源未构建</p></body></html>")


@app.on_event("startup")
def on_startup():
    """应用启动时执行"""
    # 创建数据库表
    create_db_and_tables()
    logger.info("数据库表创建完成")
    logger.info(f"应用启动成功，访问地址: http://localhost:{settings.PORT}")


@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """API健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    # 直接运行此文件时启动服务器
    try:
        logger.info(f"启动服务器 - 端口: {settings.PORT}")
        uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True,log_level="debug")
    except KeyboardInterrupt:
        logger.info("用户中断，应用正在关闭...")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
