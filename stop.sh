#!/bin/bash

# 停止认知能力评估平台服务脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== 停止认知能力评估平台服务 ===${NC}"

# 停止前端服务
if [ -f pids/frontend.pid ]; then
    FRONTEND_PID=$(cat pids/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${YELLOW}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        rm pids/frontend.pid
        echo -e "${GREEN}前端服务已停止${NC}"
    else
        echo -e "${YELLOW}前端服务未运行${NC}"
        rm -f pids/frontend.pid
    fi
else
    echo -e "${YELLOW}前端PID文件不存在，尝试通过进程名停止...${NC}"
    pkill -f "vite" || echo -e "${YELLOW}未找到前端进程${NC}"
fi

# 停止后端服务
if [ -f pids/backend.pid ]; then
    BACKEND_PID=$(cat pids/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        rm pids/backend.pid
        echo -e "${GREEN}后端服务已停止${NC}"
    else
        echo -e "${YELLOW}后端服务未运行${NC}"
        rm -f pids/backend.pid
    fi
else
    echo -e "${YELLOW}后端PID文件不存在，尝试通过进程名停止...${NC}"
    pkill -f "python.*main.py" || echo -e "${YELLOW}未找到后端进程${NC}"
fi

# 清理其他可能的进程
echo -e "${YELLOW}清理其他相关进程...${NC}"
pkill -f "node.*vite" || true
pkill -f "python.*uvicorn" || true

echo -e "${GREEN}=== 所有服务已停止 ===${NC}"