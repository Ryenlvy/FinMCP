# 使用 nohup 启动服务器
nohup uv run server.py --transport sse --host 0.0.0.0 --port 8000 > fin_mcp_server.out 2>&1 &

# 输出进程 ID
echo "服务器已在后台启动，进程 ID: $!"
echo "日志输出到 fin_mcp_server.out 和 fin_mcp_server.log" 
