#!/usr/bin/env python3
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
import uvicorn
import datetime
import argparse
import time
import inspect
import tools
import sys
import importlib

# 导入工具函数
from tools import *

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fin_mcp_server.log'
)
logger = logging.getLogger("fin-mcp-server")

# 初始化 FastMCP 服务器
mcp = FastMCP("fin-data")

# 导入所有工具函数
from tools import *
# 如果有其他工具模块，也导入它们
# from tools_code.generated_functions import *

# 批量注册工具函数
import inspect
import tools
# 如果有其他工具模块，也导入它们
import sys
import importlib

# 手动注册一些特定工具（如果需要）
mcp.tool()(restart_server)
mcp.tool()(get_exchange_list)

# 自动注册tools模块中的所有函数
for name, func in inspect.getmembers(tools, inspect.isfunction):
    # 跳过已经手动注册的函数
    if name not in ['restart_server', 'get_exchange_list']:
        mcp.tool()(func)

# 如果您有tools_code目录下的多个模块需要注册
# 可以遍历目录下的所有Python文件
tools_dir = 'tools_code'
if os.path.exists(tools_dir):
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f'tools_code.{filename[:-3]}'
            try:
                module = importlib.import_module(module_name)
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    mcp.tool()(func)
            except ImportError as e:
                logger.error(f"无法导入模块 {module_name}: {e}")

# 创建 FastAPI 应用
app = FastAPI(title="金融数据 MCP 服务器")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Accel-Buffering"],
)

# SSE 端点 - 支持 GET 和 POST
@app.get("/mcp-sse")
@app.post("/mcp-sse")
async def mcp_sse(request: Request):
    """SSE 端点，用于 MCP 通信"""
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"收到 MCP 请求: 方法={request.method}, 客户端={client_host}")
    
    async def event_generator():
        try:
            if request.method == "POST":
                # 从请求中获取 MCP 消息
                body = await request.json()
                logger.info(f"收到 MCP 消息: {json.dumps(body)}")
                
                # 处理 MCP 消息
                response = await mcp.handle_message(body)
                logger.info(f"MCP 响应: {json.dumps(response)}")
                
                # 发送响应
                yield {
                    "event": "message",
                    "data": json.dumps(response)
                }
            else:  # GET 请求
                # 对于 GET 请求，建立 SSE 连接
                yield {
                    "event": "connected",
                    "data": json.dumps({
                        "status": "connected",
                        "message": "MCP 服务器连接已建立，请使用 POST 请求发送 MCP 消息"
                    })
                }
                while True:
                    await asyncio.sleep(30)
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": str(datetime.datetime.now())})
                    }
                    
            logger.info(f"SSE 连接已建立: 客户端={client_host}")
        except Exception as e:
            logger.error(f"处理 MCP 请求错误: {str(e)}, 客户端={client_host}")
            logger.exception("详细错误信息:")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            logger.info(f"SSE 连接已关闭: 客户端={client_host}")
    
    # 设置正确的响应头
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "X-Accel-Buffering": "no"  # 对于 Nginx 代理很重要
    }
    
    return EventSourceResponse(event_generator(), headers=headers)

# 添加一个直接的工具列表端点，用于调试
@app.get("/tools/list")
async def list_tools():
    """列出所有可用的 MCP 工具"""
    tools_info = []
    for tool in mcp.tools:
        tool_info = {
            "name": tool.__name__,
            "description": tool.__doc__,
            "parameters": {}  # 这里可以添加参数信息
        }
        tools_info.append(tool_info)
    
    return {"tools": tools_info}

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "fin-mcp-server"}

def create_starlette_app(mcp_server, *, debug: bool = False) -> Starlette:
    """创建一个 Starlette 应用，用于 SSE 传输"""
    # 创建 SSE 传输
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        """处理 SSE 连接"""
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            # 运行 MCP 服务器
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    # 创建并返回 Starlette 应用
    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),  # SSE 连接端点
            Mount("/messages/", app=sse.handle_post_message),  # 消息发送端点
        ],
    )

# 主函数
if __name__ == "__main__":
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='运行金融数据 MCP 服务器')
    parser.add_argument('--transport', choices=['stdio', 'sse', 'fastapi'], default='sse', 
                        help='传输模式 (stdio, sse 或 fastapi)')
    parser.add_argument('--host', default='0.0.0.0', 
                        help='服务器绑定的主机 (用于 sse 和 fastapi 模式)')
    parser.add_argument('--port', type=int, default=8000, 
                        help='服务器监听的端口 (用于 sse 和 fastapi 模式)')
    args = parser.parse_args()

    # 确保MCP服务器完全初始化
    logger.info("正在初始化MCP服务器...")
    time.sleep(1)  # 给服务器一些初始化时间
    
    # 根据传输模式启动服务器
    if args.transport == 'stdio':
        # 使用 stdio 传输模式运行
        logger.info("使用 stdio 传输模式启动 MCP 服务器")
        mcp.run(transport='stdio')
    elif args.transport == 'sse':
        # 使用 SSE 传输模式运行
        logger.info(f"使用 SSE 传输模式启动 MCP 服务器，监听 {args.host}:{args.port}")
        mcp_server = mcp._mcp_server  # 获取底层 MCP 服务器
        starlette_app = create_starlette_app(mcp_server, debug=True)
        uvicorn.run(starlette_app, host=args.host, port=args.port)
    else:  # fastapi 模式
        # 使用 FastAPI 运行
        logger.info(f"使用 FastAPI 模式启动 MCP 服务器，监听 {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)