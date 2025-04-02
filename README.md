# 阅读流畅性实验平台

这个项目是一个基于jsPsych、Vue3和ElementPlus的阅读流畅性测试实验平台，用于测量被试者阅读和判断句子真假的能力。

## 功能特点

- 用户信息收集（姓名、学校、年级、班级）
- 实验指导语展示
- 教学阶段（示范和练习）
- 正式测验（100个句子判断题）
- 3分钟倒计时（带沙漏动画）
- 数据自动保存至数据库
- 键盘快捷操作（Q=√, W=╳）
- 调试模式（同时按下"【】"进入）

## 技术栈

- 前端：Vue 3 + ElementPlus + jsPsych 8.2.1
- 后端：Express + MongoDB
- 构建工具：Vite

## 系统要求

- Node.js 16.0+
- MongoDB 4.4+

## 安装和运行

1. 克隆仓库：

```bash
git clone <仓库地址>
cd reading-fluency-experiment
```

2. 安装依赖：

```bash
npm install
```

3. 启动MongoDB：

确保MongoDB服务已经启动。在大多数系统上，可以使用以下命令：

```bash
mongod --dbpath=<数据存储路径>
```

4. 启动应用（开发模式）：

```bash
npm run start
```

这将同时启动前端开发服务器和后端API服务器。

5. 构建生产版本：

```bash
npm run build
```

6. 运行生产版本：

```bash
npm run start:server
```

## 项目结构

```
reading-fluency-experiment/
├── src/                    # 前端源代码
│   ├── components/         # Vue组件
│   ├── App.vue             # 主应用组件
│   └── main.js             # 应用入口
├── server/                 # 数据文件
│   ├── 教学阶段.csv         # 教学阶段题目
│   └── 正式阶段.csv         # 正式阶段题目
├── public/                 # 静态资源
├── server.js               # Express后端服务
├── parse-csv.js            # CSV解析工具
├── vite.config.js          # Vite配置
└── package.json            # 项目依赖配置
```

## API接口

- `GET /api/schools/recent`: 获取最近一天参与测试的学校列表
- `GET /api/trials`: 获取试题数据
- `POST /api/save-trial`: 保存试验数据
- `GET /api/results/:userId`: 获取指定用户的实验结果

## 常见问题

1. **MongoDB连接错误**

   确保MongoDB服务已启动，并且服务器配置中的连接字符串正确。

2. **CSV数据加载失败**

   检查server目录下是否存在教学阶段.csv和正式阶段.csv文件，并确保格式正确。

3. **调试模式**

   同时按下"【"和"】"键可以进入调试模式，可以跳转题目和调整时间。

## 定制化

1. **修改试题**：
   更新server目录下的CSV文件即可修改试题内容。

2. **调整时间限制**：
   在ReadingExperiment.vue文件中修改timerValue的初始值（默认为180秒）。

3. **修改UI样式**：
   样式定义在各个Vue组件的<style>部分，可以按需调整。

## 许可证

[MIT](LICENSE)