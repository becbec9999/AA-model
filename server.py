#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大类资产配置指标监控面板 - FastAPI 服务
=====================================
启动命令: python server.py
访问地址: http://localhost:8000
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from api import router

# 创建 FastAPI 应用
app = FastAPI(
    title="大类资产配置指标监控",
    description="专业金融终端风格指标展示",
    version="5.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(router)

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回主页面"""
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'index.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("AA-Model Dashboard Server V5.0")
    print("=" * 60)
    print("\n启动服务...")
    print("访问地址: http://localhost:8000")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
