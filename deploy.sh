#!/bin/bash

# 认知能力评估平台部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 认知能力评估平台部署脚本 ===${NC}"

# 检查环境参数
ENVIRONMENT=${1:-staging}
echo -e "${YELLOW}部署环境: $ENVIRONMENT${NC}"

# 设置端口
if [ "$ENVIRONMENT" = "development" ]; then
    FRONTEND_PORT=5173
    BACKEND_PORT=3000
elif [ "$ENVIRONMENT" = "staging" ]; then
    FRONTEND_PORT=8080
    BACKEND_PORT=8001
elif [ "$ENVIRONMENT" = "production" ]; then
    FRONTEND_PORT=8080
    BACKEND_PORT=8001
else
    echo -e "${RED}错误: 无效的环境参数. 请使用 development, staging, 或 production${NC}"
    exit 1
fi

echo -e "${YELLOW}前端端口: $FRONTEND_PORT${NC}"
echo -e "${YELLOW}后端端口: $BACKEND_PORT${NC}"

# 停止现有进程（如果存在）
echo -e "${YELLOW}停止现有进程...${NC}"
pkill -f "vite.*--port $FRONTEND_PORT" || echo "前端进程未运行"
pkill -f "python.*main.py.*$BACKEND_PORT" || echo "后端进程未运行"

# 安装依赖
echo -e "${YELLOW}安装前端依赖...${NC}"
npm install

echo -e "${YELLOW}安装后端依赖...${NC}"
cd backend
uv sync || echo "后端依赖已安装"
cd ..

# 设置环境变量
export VITE_APP_ENV=$ENVIRONMENT
export ENVIRONMENT=$ENVIRONMENT

# 启动后端
echo -e "${YELLOW}启动后端服务 (端口 $BACKEND_PORT)...${NC}"
cd backend
nohup uv run python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../pids/backend.pid
cd ..

# 等待后端启动
echo -e "${YELLOW}等待后端服务启动...${NC}"
sleep 3

# 启动前端
echo -e "${YELLOW}启动前端服务 (端口 $FRONTEND_PORT)...${NC}"
nohup npm run dev:$ENVIRONMENT -- --port $FRONTEND_PORT --host 0.0.0.0 > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > pids/frontend.pid

# 创建必要目录
mkdir -p logs pids

echo -e "${GREEN}=== 部署完成 ===${NC}"
echo -e "${GREEN}前端服务: http://localhost:$FRONTEND_PORT${NC}"
echo -e "${GREEN}后端服务: http://localhost:$BACKEND_PORT${NC}"
echo -e "${GREEN}前端PID: $FRONTEND_PID${NC}"
echo -e "${GREEN}后端PID: $BACKEND_PID${NC}"

if [ "$ENVIRONMENT" = "staging" ]; then
    echo -e "${GREEN}生产环境访问地址:${NC}"
    echo -e "${GREEN}前端: https://eduscreen.psyventures.cn${NC}"
    echo -e "${GREEN}后端API: https://eduscreenapi.psyventures.cn${NC}"
fi

echo -e "${YELLOW}查看日志:${NC}"
echo -e "tail -f logs/frontend.log"
echo -e "tail -f logs/backend.log"

echo -e "${YELLOW}停止服务:${NC}"
echo -e "./stop.sh"