# 认知能力评估平台 (Youth Cognitive Assessment Platform)

这是一个基于 Vue 3 + FastAPI 的全栈认知能力评估平台，提供阅读流畅性、注意力筛查、计算流畅性、识字量测试等多种认知能力测评功能。

## 🌟 功能特点

- 🧠 **多种认知测试**: 阅读流畅性、口语阅读流畅性、注意力筛查、计算流畅性、识字量测试
- 🏗️ **模块化架构**: 每个测试系统独立封装，易于扩展
- 🔄 **实时数据**: WebSocket 支持，实时语音评测
- 📱 **响应式设计**: 支持多设备访问
- 🔒 **安全部署**: HTTPS + SSL 证书，生产环境就绪
- 📊 **数据分析**: 完整的测试结果记录和分析

## 🏛️ 系统架构

**前端**: Vue 3 + Element Plus + Vite  
**后端**: FastAPI + SQLModel + MySQL  
**数据库**: MySQL 8.0 with Docker support  
**包管理**: Frontend (npm/pnpm), Backend (uv/pip)  
**部署**: Nginx + Let's Encrypt SSL

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- MySQL 8.0+
- uv (Python包管理器)

### 📦 安装依赖

#### 前端依赖
```bash
npm install
# 或者
pnpm install
```

#### 后端依赖
```bash
cd backend

# 安装 uv (如果未安装)
pip install uv

# 创建虚拟环境并安装依赖
uv sync
```

### 🗄️ 数据库设置

使用 Docker 快速启动 MySQL：

```bash
docker run -d --name mysql-8-app -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=meng123456 \
  -e MYSQL_DATABASE=appdb \
  -e MYSQL_USER=meng \
  -e MYSQL_PASSWORD=meng123456 \
  -v mysql_data:/var/lib/mysql \
  mysql:8.0.39 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci \
  --default-authentication-plugin=mysql_native_password
```

或手动创建数据库：
```sql
CREATE DATABASE appdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'meng'@'%' IDENTIFIED BY 'meng123456';
GRANT ALL PRIVILEGES ON appdb.* TO 'meng'@'%';
FLUSH PRIVILEGES;
```

### 🔧 开发环境启动

#### 方式一：一键启动（推荐）
```bash
# 启动开发环境
npm start

# 或分别启动前后端
npm run dev        # 前端开发服务器
npm run start:server  # 后端服务器
```

#### 方式二：分别启动
```bash
# 启动前端 (端口 5173)
npm run dev

# 启动后端 (端口 3000)
cd backend
uv run python main.py
```

#### 初始化数据库
```bash
cd backend
python init_db.py
```

### 访问地址
- **前端**: http://localhost:5173
- **后端API**: http://localhost:3000
- **API文档**: http://localhost:3000/api/docs

## 🌐 生产环境部署

平台支持三种环境模式：`development` | `staging` | `production`

### 快速部署

#### 使用部署脚本（推荐）
```bash
# 部署到临时环境 (staging)
./deploy.sh staging

# 部署到生产环境
./deploy.sh production

# 停止所有服务
./stop.sh
```

#### 手动部署
```bash
# 1. 设置环境变量
export ENVIRONMENT=staging  # 或 production
export VITE_APP_ENV=staging

# 2. 启动后端 (端口 8001)
cd backend
nohup uv run python main.py > ../logs/backend.log 2>&1 &

# 3. 启动前端 (端口 8080)
nohup npm run dev:staging -- --port 8080 --host 0.0.0.0 > logs/frontend.log 2>&1 &
```

### 🔒 生产环境配置

#### 域名配置
- **前端域名**: https://eduscreen.psyventures.cn
- **后端API域名**: https://eduscreenapi.psyventures.cn

#### SSL 证书 (Let's Encrypt)
```bash
# 获取 SSL 证书
certbot certonly --webroot -w /var/www/html -d eduscreen.psyventures.cn
certbot certonly --webroot -w /var/www/html -d eduscreenapi.psyventures.cn
```

#### Nginx 配置
配置文件位于 `/etc/nginx/sites-available/psyventures`，包含：
- HTTP/2 支持
- Gzip 压缩优化
- 静态文件缓存
- WebSocket 代理
- 安全头设置

### 📊 服务监控

#### 查看服务状态
```bash
# 检查进程
ps aux | grep -E "(vite|python.*main.py)"

# 查看端口占用
netstat -tlnp | grep -E "(8080|8001)"
```

#### 查看日志
```bash
# 前端日志
tail -f logs/frontend.log

# 后端日志  
tail -f logs/backend.log

# Nginx 访问日志
tail -f /var/log/nginx/access.log
```

## 🎯 测试系统说明

### 1. 阅读流畅性测试 (`reading_fluency/`)
- 教学阶段和正式阶段词汇测试
- 反应时间和准确率记录

### 2. 口语阅读流畅性测试 (`oral_reading_fluency/`)  
- 基于科大讯飞语音评测API
- 实时语音识别和评分

### 3. 注意力测试 (`attention_test/`)
- 视觉注意力筛查任务
- 多种注意力维度评估

### 4. 计算流畅性测试 (`calculation_test/`)
- 数学运算能力评估
- 分层级难度设计

### 5. 识字量测试 (`literacy_test/`)
- 汉字识别能力测评
- 年级分层测试设计

## 🔧 开发指南

### 项目结构
```
YouthCognitionPlatform/
├── src/                    # 前端源码
│   ├── components/         # Vue 组件
│   ├── views/             # 页面视图
│   ├── router/            # 路由配置
│   └── config/            # 环境配置
├── backend/               # 后端源码
│   ├── apps/              # 业务模块
│   │   ├── reading_fluency/
│   │   ├── oral_reading_fluency/
│   │   ├── attention_test/
│   │   ├── calculation_test/
│   │   └── literacy_test/
│   ├── data/              # 测试数据
│   ├── config.py          # 配置文件
│   ├── database.py        # 数据库配置
│   └── main.py           # 应用入口
├── deploy.sh             # 部署脚本
├── stop.sh              # 停止脚本
└── logs/                # 日志目录
```

### 添加新测试模块
1. 在 `backend/apps/` 创建新模块目录
2. 实现 `models.py`、`router.py`、`service.py`
3. 在 `main.py` 中注册路由
4. 创建对应的前端组件和路由

### API 接口规范
- 统一前缀：`/api/`
- RESTful 设计
- 统一响应格式
- 完整的 OpenAPI 文档

## 📋 常用命令

### 开发命令
```bash
# 前端开发
npm run dev              # 开发模式
npm run build           # 生产构建
npm run preview         # 预览构建结果

# 后端开发  
cd backend
uv run python main.py   # 启动服务
python init_db.py       # 初始化数据库
pytest                  # 运行测试
```

### 生产命令
```bash
# 环境切换
npm run dev:staging     # 临时部署模式
npm run build:staging   # 临时部署构建
npm run start:staging   # 启动临时部署环境

# 服务管理
./deploy.sh [environment]  # 部署指定环境
./stop.sh                  # 停止所有服务
```

## 🐛 常见问题

### 1. 数据库连接失败
- 检查 MySQL 服务状态
- 验证连接配置 (`backend/config.py`)
- 确认防火墙设置

### 2. 前端无法访问API
- 检查 CORS 配置
- 验证代理设置 (`vite.config.js`)  
- 确认后端服务运行状态

### 3. SSL 证书问题
- 检查域名解析
- 验证 certbot 配置
- 查看 nginx 配置语法

### 4. 端口占用冲突
```bash
# 查看端口占用
lsof -i :8080
lsof -i :8001

# 释放端口
kill -9 <PID>
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

**访问地址**:
- 🌍 **生产环境**: https://eduscreen.psyventures.cn
- 🔗 **API文档**: https://eduscreenapi.psyventures.cn/api/docs