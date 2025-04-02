import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';
import path from 'path';
import fs from 'fs';
import { parse } from 'csv-parse/sync';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// ES模块中获取__dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());

// 添加请求日志中间件
app.use((req, res, next) => {
  const start = Date.now();
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  
  // 请求结束后记录响应状态和时间
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url} ${res.statusCode} - ${duration}ms`);
  });
  
  next();
});

app.use(express.static(path.join(__dirname, 'dist')));

// 连接数据库
mongoose.connect('mongodb://localhost:27017/reading-fluency', {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => console.log('MongoDB 连接成功'))
.catch(err => console.error('MongoDB 连接失败:', err));

// 定义模型
const UserSchema = new mongoose.Schema({
  name: { type: String, required: true },
  school: { type: String, required: true },
  grade: { type: Number, required: true },
  classNumber: { type: Number, required: true },
  date: { type: Date, default: Date.now }
});

const TrialSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  trial_id: { type: Number, required: true },
  user_answer: { type: Boolean, required: true, default: false },  // 添加默认值
  response_time: { type: Number, required: true, default: 0 },     // 添加默认值
  timestamp: { type: Date, default: Date.now }
});

const User = mongoose.model('User', UserSchema);
const Trial = mongoose.model('Trial', TrialSchema);

// 从CSV文件读取试题
function readTrialsFromCSV(filePath) {
  try {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const records = parse(fileContent);
    return records.map(record => record[1] || record[0]);
  } catch (error) {
    console.error(`读取CSV文件失败: ${filePath}`, error);
    return [];
  }
}

const practiceTrialPath = path.join(__dirname, 'server', '教学阶段.csv');
const formalTrialPath = path.join(__dirname, 'server', '正式阶段.csv');

// 可以从parse-csv.js导入解析好的数据
import { practiceTrials as parsedPracticeTrials, formalTrials as parsedFormalTrials } from './parse-csv.js';

// 读取试题数据
let practiceTrials = [];
let formalTrials = [];

try {
  // 优先使用已解析的数据
  if (parsedPracticeTrials && parsedPracticeTrials.length > 0) {
    practiceTrials = parsedPracticeTrials;
  } else {
    practiceTrials = readTrialsFromCSV(practiceTrialPath);
  }
  
  if (parsedFormalTrials && parsedFormalTrials.length > 0) {
    formalTrials = parsedFormalTrials;
  } else {
    formalTrials = readTrialsFromCSV(formalTrialPath);
  }
  
  console.log(`成功加载 ${practiceTrials.length} 个练习题和 ${formalTrials.length} 个正式题`);
} catch (error) {
  console.error('加载试题数据失败:', error);
}

// API路由
// 获取最近的学校
app.get('/api/schools/recent', async (req, res) => {
  try {
    // 查询最近一天的学校数据
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    
    const recentUsers = await User.find({ date: { $gte: oneDayAgo } })
                                 .distinct('school');
    
    res.json({ schools: recentUsers });
  } catch (error) {
    console.error('获取最近学校失败:', error);
    res.status(500).json({ error: '服务器错误' });
  }
});

// 获取试题
app.get('/api/trials', (req, res) => {
  res.json({
    practiceTrials,
    formalTrials
  });
});

// 保存试验数据
app.post('/api/save-trial', async (req, res) => {
  try {
    const { name, school, grade, classNumber, trial_id, user_answer, response_time } = req.body;
    
    // 验证所需字段
    if (name === undefined || school === undefined || grade === undefined || classNumber === undefined) {
      return res.status(400).json({ error: '用户信息不完整', details: req.body });
    }
    
    if (trial_id === undefined) {
      return res.status(400).json({ error: 'trial_id 不能为空', details: req.body });
    }
    
    // 确保user_answer和response_time有值
    const validatedUserAnswer = user_answer !== undefined ? user_answer : false;
    const validatedResponseTime = response_time !== undefined ? response_time : 0;
    
    // 查找或创建用户
    let user = await User.findOne({ name, school, grade, classNumber });
    
    if (!user) {
      user = new User({ name, school, grade, classNumber });
      await user.save();
    }
    
    // 保存试验数据
    const trial = new Trial({
      userId: user._id,
      trial_id,
      user_answer: validatedUserAnswer,
      response_time: validatedResponseTime
    });
    
    await trial.save();
    
    res.status(201).json({ message: '数据保存成功' });
  } catch (error) {
    console.error('保存试验数据失败:', error);
    res.status(500).json({ error: '服务器错误', details: error.message });
  }
});

// 获取实验结果
app.get('/api/results/:userId', async (req, res) => {
  try {
    const userId = req.params.userId;
    
    const user = await User.findById(userId);
    if (!user) {
      return res.status(404).json({ error: '用户不存在' });
    }
    
    const trials = await Trial.find({ userId });
    
    // 计算结果
    const totalTrials = trials.length;
    const correctTrials = trials.filter(trial => trial.user_answer).length;
    const averageResponseTime = trials.reduce((sum, trial) => sum + trial.response_time, 0) / totalTrials;
    
    res.json({
      user,
      results: {
        totalTrials,
        correctTrials,
        accuracy: (correctTrials / totalTrials) * 100,
        averageResponseTime
      },
      trials
    });
  } catch (error) {
    console.error('获取结果失败:', error);
    res.status(500).json({ error: '服务器错误' });
  }
});

// 捕获所有其他请求，转发到前端应用
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
});

// 由于使用ES模块，这里不再需要module.exports