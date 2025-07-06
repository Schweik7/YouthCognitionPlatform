# 认知能力评估平台

这个项目是一个基于 FastAPI 和 Vue 的认知能力评估平台，整合了多种测试系统，包括阅读流畅性测试、读字测试、注意筛查和识字量测试等。

## 功能特点

- 模块化的后端设计，各个测试系统独立封装
- MySQL 数据库存储，使用 SQLModel ORM
- 支持多种认知能力测试的集成
- RESTful API 接口
- 前端使用 Vue 3 + Element Plus

## 系统架构

- **后端**: FastAPI (Python)
- **数据库**: MySQL
- **ORM框架**: SQLModel
- **前端**: Vue 3 + Element Plus
- **包管理**: uv

## 项目结构

```
认知能力评估平台/
├── apps/                   # 应用模块目录
│   ├── reading_fluency/    # 阅读流畅性测试模块
│   │   ├── __init__.py     
│   │   ├── models.py       # 数据模型
│   │   ├── router.py       # API路由
│   │   └── service.py      # 业务逻辑
│   ├── word_recognition/   # 识字量测试模块（待实现）
│   ├── attention_test/     # 注意筛查模块（待实现）
│   └── calculation/        # 计算筛查模块（待实现）
├── data/                   # 数据文件目录
│   ├── 教学阶段.csv          # 阅读流畅性教学阶段题目
│   └── 正式阶段.csv          # 阅读流畅性正式阶段题目
├── tests/                  # 测试目录
├── config.py               # 配置文件
├── database.py             # 数据库连接和模型基类
├── main.py                 # 应用入口
├── init_db.py              # 数据库初始化脚本
├── run.py                  # 应用启动脚本
└── pyproject.toml          # 项目依赖配置
```

## 系统要求

- Python 3.10+
- MySQL 5.7+
- Node.js 16.0+ (前端开发)

## 安装和部署

### 1. 克隆仓库

```bash
git clone <仓库地址>
cd backend
```

### 2. 创建和激活虚拟环境

使用 `uv` 管理依赖：

```bash
# 安装 uv (如果尚未安装)
pip install uv

# 创建虚拟环境并安装依赖
# uv venv
uv pip install -r pyproject.toml

# 激活虚拟环境
# 在 Windows 上
# .venv\Scripts\activate
# 在 macOS/Linux 上
# source .venv/bin/activate
```

### 3. 配置数据库

docker run -d --name mysql-8-app -p 3306:3306 -e MYSQL_ROOT_PASSWORD=meng123456 -e MYSQL_DATABASE=appdb -e MYSQL_USER=meng -e MYSQL_PASSWORD=meng123456 -v mysql_data:/var/lib/mysql mysql:8.0.39 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci --default-authentication-plugin=mysql_native_password
确保 MySQL 服务已启动，并创建名为 `appdb` 的数据库：

```sql
CREATE DATABASE appdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'meng'@'localhost' IDENTIFIED BY 'meng123456';
GRANT ALL PRIVILEGES ON appdb.* TO 'meng'@'localhost';
FLUSH PRIVILEGES;
```


或者安装好mysql8.0以后，执行以下命令
```sql
CREATE DATABASE appdb;
CREATE USER 'meng'@'%' IDENTIFIED BY 'meng123456';
GRANT ALL PRIVILEGES ON appdb.* TO 'meng'@'%';
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'meng123456';
FLUSH PRIVILEGES;
```



### 4. 初始化数据库和数据

```bash
python init_db.py
```

### 5. 启动应用

```bash
python run.py
```

应用将在 http://localhost:3000 上启动，API 文档可在 http://localhost:3000/api/docs 访问。

## API 接口说明

### 阅读流畅性测试 API

- `GET /api/reading-fluency/schools/recent`: 获取最近一天参与测试的学校列表
- `GET /api/reading-fluency/trials`: 获取试题数据
- `POST /api/reading-fluency/save-trial`: 保存试验数据
- `GET /api/reading-fluency/results/{user_id}`: 获取指定用户的实验结果

## 开发指南

### 添加新的测试系统

1. 在 `apps` 目录下创建新的模块目录，例如 `word_recognition`
2. 实现必要的文件：`__init__.py`, `models.py`, `router.py`, `service.py`
3. 在 `main.py` 中导入并注册路由

### 前端开发

前端代码位于 `dist` 目录中。如需开发前端，可以：

1. 编辑 Vue 源代码
2. 构建生产版本
3. 将构建结果复制到 `dist` 目录

### 数据库迁移

当模型发生变化时，可以重新运行初始化脚本：

```bash
python init_db.py
```

注意：这将重新创建所有表，可能导致数据丢失。在生产环境中，应使用适当的迁移工具。

## 常见问题

1. **数据库连接错误**

   确保 MySQL 服务已启动，并且配置文件中的连接信息正确。

2. **CSV数据加载失败**

   检查 `data` 目录下是否存在 `教学阶段.csv` 和 `正式阶段.csv` 文件，并确保格式正确。

3. **前端资源不可用**

   确保 `dist` 目录中包含构建好的前端资源。

## 许可证

[MIT](LICENSE)