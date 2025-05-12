<style scoped>
/* 全局样式 */
.experiment-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 10px;
}

.content-area {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  box-sizing: border-box;
}

/* 调试面板 */
.debug-panel {
  position: fixed;
  top: 0;
  left: 0;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 10px;
  z-index: 1000;
  border-radius: 0 0 5px 0;
}

.debug-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

/* 指导语样式 */
.instruction {
  max-width: 700px;
  margin: 0 auto;
  text-align: left;
  line-height: 1.6;
}

.instruction h2 {
  text-align: center;
  color: #409EFF;
  margin-bottom: 20px;
}

.continue-btn {
  margin: 20px auto;
  display: block;
  min-width: 120px;
  font-weight: bold;
}

/* 测试容器样式 */
.test-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.test-header {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 20px;
  align-items: center;
}

.test-info {
  font-weight: bold;
  font-size: 18px;
}

.test-timer {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  background-color: white;
  padding: 5px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* 题目卡片样式 */
.problem-card {
  width: 100%;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 30px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.problem-text {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 30px;
  text-align: center;
}

.answer-input {
  display: flex;
  gap: 10px;
  width: 100%;
  max-width: 300px;
}

/* 计时器沙漏 */
.timer-container {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hourglass-container {
  margin-top: 10px;
  display: flex;
  justify-content: center;
}

.hourglass {
  position: relative;
  width: 30px;
  height: 50px;
}

.hourglass-top {
  position: absolute;
  top: 0;
  width: 30px;
  height: 25px;
  background-color: #409EFF;
  clip-path: polygon(0 0, 100% 0, 50% 100%, 0 0);
}

.hourglass-bottom {
  position: absolute;
  bottom: 0;
  width: 30px;
  height: 0;
  background-color: #E6E6E6;
  clip-path: polygon(0 100%, 100% 100%, 50% 0, 0 100%);
}

/* 结果页面样式 */
.result-container {
  text-align: center;
  width: 100%;
}

.result-container h2 {
  color: #409EFF;
  margin-bottom: 20px;
}

.result-card {
  margin-bottom: 30px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 15px 0;
  border-bottom: 1px solid #ebeef5;
}

.result-item:last-child {
  border-bottom: none;
}

.result-label {
  font-weight: bold;
  color: #606266;
}

.result-value {
  color: #303133;
  font-weight: bold;
}

/* 题型统计 */
.type-stats {
  margin-top: 30px;
  width: 100%;
}

.type-stats h3 {
  margin-bottom: 20px;
  color: #409EFF;
}

.type-card {
  height: 100%;
}

.type-header {
  font-weight: bold;
  color: #303133;
}

.type-stats-content {
  padding: 10px 0;
}

.type-stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.type-stat-item:last-child {
  border-bottom: none;
}

/* 按钮区域 */
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .problem-text {
    font-size: 28px;
  }
  
  .test-timer {
    font-size: 20px;
  }
  
  .problem-card {
    padding: 20px;
  }
}
</style>
<template>
  <div class="experiment-container">
    <!-- 调试面板 -->
    <div v-if="debugMode" class="debug-panel">
      <h3>调试模式</h3>
      <div class="debug-controls">
        <el-input-number v-model="jumpToIndex" :min="1" :max="totalProblems" label="跳转题号"></el-input-number>
        <el-button type="primary" @click="jumpToProblem">跳转</el-button>
        <el-input-number v-model="remainingTime" :min="0" :max="testDuration" label="剩余时间(秒)"></el-input-number>
        <el-button type="primary" @click="updateTimer">更新时间</el-button>
        <el-button type="warning" @click="endTest">结束测试</el-button>
      </div>
    </div>

    <!-- 实验内容区域 -->
    <div class="content-area">
      <!-- 指导语阶段 -->
      <div v-if="phase === 'welcome'" class="instruction">
        <h2>计算流畅性测试</h2>
        <p>欢迎参加计算流畅性测试，这个测试将评估你的计算能力和速度。</p>
        <p>在测试中，你将看到一系列计算题目，需要输入正确的答案。</p>
        <p>请认真完成测试，尽可能快速准确地计算出答案。</p>
        <p v-if="gradeLevel === 1">一年级的题目为0到10，两个数的加减法，加法减法各20题。</p>
        <p v-if="gradeLevel === 2">二年级的题目为两位数的加减法；包括30道两个数的加减法和10道三个数的加减法。</p>
        <p v-if="gradeLevel === 3">三年级的题目包括三位数和两位数的加减法，三位数与三位数的加减法，以及三位数三个数的加减法。</p>
        <el-button type="primary" class="continue-btn" @click="nextPhase">开始测试</el-button>
      </div>

      <!-- 正式测试阶段 -->
      <div v-else-if="phase === 'test' && !testEnded" class="test-container">
        <div class="test-header">
          <div class="test-info">
            <span>第 {{ currentIndex + 1 }}/{{ totalProblems }} 题</span>
          </div>
          <div class="test-timer">
            <span>{{ formatTime(remainingTime) }}</span>
          </div>
        </div>

        <div class="problem-card">
          <div class="problem-text">
            {{ currentProblem.text }}
          </div>
          <div class="answer-input">
            <el-input
              v-model.number="userAnswer"
              type="number"
              placeholder="输入答案"
              @keyup.enter="submitAnswer"
              ref="answerInput"
              :disabled="isProcessing"
            ></el-input>
            <el-button 
              type="primary" 
              @click="submitAnswer" 
              :disabled="isProcessing || userAnswer === ''"
            >
              确认
            </el-button>
          </div>
        </div>

        <!-- 计时器沙漏 -->
        <div class="timer-container">
          <div class="hourglass-container">
            <div class="hourglass">
              <div class="hourglass-top" :style="hourglassTopStyle"></div>
              <div class="hourglass-bottom" :style="hourglassBottomStyle"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 测试结果 -->
      <div v-else-if="phase === 'result'" class="result-container">
        <h2>测试结果</h2>

        <el-card class="result-card">
          <div class="result-item">
            <div class="result-label">共完成题目:</div>
            <div class="result-value">{{ testResults.completedProblems }} / {{ totalProblems }}</div>
          </div>
          <div class="result-item">
            <div class="result-label">正确数量:</div>
            <div class="result-value">{{ testResults.correctProblems }}</div>
          </div>
          <div class="result-item">
            <div class="result-label">错误数量:</div>
            <div class="result-value">{{ testResults.completedProblems - testResults.correctProblems }}</div>
          </div>
          <div class="result-item">
            <div class="result-label">正确率:</div>
            <div class="result-value">{{ formatPercentage(testResults.accuracy) }}%</div>
          </div>
          <div class="result-item">
            <div class="result-label">平均反应时间:</div>
            <div class="result-value">{{ formatResponseTime(testResults.averageResponseTime) }}毫秒</div>
          </div>
          <div class="result-item">
            <div class="result-label">总用时:</div>
            <div class="result-value">{{ formatTime(testDuration - remainingTime) }}</div>
          </div>
        </el-card>

        <div v-if="gradeLevel === 1" class="type-stats">
          <h3>题型分析</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card class="type-card">
                <template #header>
                  <div class="type-header">加法题</div>
                </template>
                <div class="type-stats-content">
                  <div class="type-stat-item">
                    <span>完成数量:</span>
                    <span>{{ typeStats.addition.completed }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确数量:</span>
                    <span>{{ typeStats.addition.correct }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确率:</span>
                    <span>{{ formatPercentage(typeStats.addition.accuracy) }}%</span>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="type-card">
                <template #header>
                  <div class="type-header">减法题</div>
                </template>
                <div class="type-stats-content">
                  <div class="type-stat-item">
                    <span>完成数量:</span>
                    <span>{{ typeStats.subtraction.completed }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确数量:</span>
                    <span>{{ typeStats.subtraction.correct }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确率:</span>
                    <span>{{ formatPercentage(typeStats.subtraction.accuracy) }}%</span>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <div v-else-if="gradeLevel === 2" class="type-stats">
          <h3>题型分析</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card class="type-card">
                <template #header>
                  <div class="type-header">两数加减法</div>
                </template>
                <div class="type-stats-content">
                  <div class="type-stat-item">
                    <span>完成数量:</span>
                    <span>{{ typeStats.twoNumbers.completed }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确数量:</span>
                    <span>{{ typeStats.twoNumbers.correct }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确率:</span>
                    <span>{{ formatPercentage(typeStats.twoNumbers.accuracy) }}%</span>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="type-card">
                <template #header>
                  <div class="type-header">三数加减法</div>
                </template>
                <div class="type-stats-content">
                  <div class="type-stat-item">
                    <span>完成数量:</span>
                    <span>{{ typeStats.threeNumbers.completed }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确数量:</span>
                    <span>{{ typeStats.threeNumbers.correct }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确率:</span>
                    <span>{{ formatPercentage(typeStats.threeNumbers.accuracy) }}%</span>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <div v-else-if="gradeLevel === 3" class="type-stats">
          <h3>题型分析</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-card class="type-card">
                <template #header>
                  <div class="type-header">三位数和两位数加减法</div>
                </template>
                <div class="type-stats-content">
                  <div class="type-stat-item">
                    <span>完成数量:</span>
                    <span>{{ typeStats.type1.completed }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确数量:</span>
                    <span>{{ typeStats.type1.correct }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确率:</span>
                    <span>{{ formatPercentage(typeStats.type1.accuracy) }}%</span>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="type-card">
                <template #header>
                  <div class="type-header">三位数与三位数加减法</div>
                </template>
                <div class="type-stats-content">
                  <div class="type-stat-item">
                    <span>完成数量:</span>
                    <span>{{ typeStats.type2.completed }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确数量:</span>
                    <span>{{ typeStats.type2.correct }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确率:</span>
                    <span>{{ formatPercentage(typeStats.type2.accuracy) }}%</span>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="type-card">
                <template #header>
                  <div class="type-header">三位数三数加减法</div>
                </template>
                <div class="type-stats-content">
                  <div class="type-stat-item">
                    <span>完成数量:</span>
                    <span>{{ typeStats.type3.completed }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确数量:</span>
                    <span>{{ typeStats.type3.correct }}</span>
                  </div>
                  <div class="type-stat-item">
                    <span>正确率:</span>
                    <span>{{ formatPercentage(typeStats.type3.accuracy) }}%</span>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <div class="action-buttons">
          <el-button type="primary" @click="goToSelection">返回测试选择</el-button>
          <el-button @click="restartTest">重新测试</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus';

const router = useRouter();

// 状态变量
const phase = ref('welcome'); // 实验阶段: welcome, test, result
const debugMode = ref(false);
const userId = ref(null);
const testSessionId = ref(null);
const gradeLevel = ref(1); // 年级（1-3）
const problems = ref([]); // 所有题目
const currentIndex = ref(0); // 当前题目索引
const userAnswer = ref(''); // 用户输入的答案
const totalProblems = ref(40); // 总题目数
const isProcessing = ref(false); // 是否正在处理答案
const testEnded = ref(false); // 测试是否结束
const answerInput = ref(null); // 答案输入框的引用
const jumpToIndex = ref(1); // 调试模式：跳转题号
const responseTime = ref(0); // 答题时间（毫秒）
const problemStartTime = ref(0); // 当前题目开始时间
const remainingTime = ref(180); // 默认3分钟倒计时
const testDuration = ref(180); // 测试总时间
const timerInterval = ref(null); // 计时器

// 测试结果
const testResults = reactive({
  completedProblems: 0,
  correctProblems: 0,
  accuracy: 0,
  averageResponseTime: 0
});

// 题型统计
const typeStats = reactive({
  // 一年级
  addition: { completed: 0, correct: 0, accuracy: 0 },
  subtraction: { completed: 0, correct: 0, accuracy: 0 },
  // 二年级
  twoNumbers: { completed: 0, correct: 0, accuracy: 0 },
  threeNumbers: { completed: 0, correct: 0, accuracy: 0 },
  // 三年级
  type1: { completed: 0, correct: 0, accuracy: 0 }, // 三位数和两位数加减法
  type2: { completed: 0, correct: 0, accuracy: 0 }, // 三位数与三位数加减法
  type3: { completed: 0, correct: 0, accuracy: 0 }  // 三位数三数加减法
});

// 当前题目
const currentProblem = computed(() => {
  if (problems.value.length === 0 || currentIndex.value >= problems.value.length) {
    return { text: "", answer: 0 };
  }
  return problems.value[currentIndex.value];
});

// 沙漏样式计算
const hourglassTopStyle = computed(() => {
  const percentage = (remainingTime.value / testDuration.value) * 100;
  return {
    height: `${percentage / 2}%`,
    transition: 'height 1s linear'
  };
});

const hourglassBottomStyle = computed(() => {
  const percentage = 100 - (remainingTime.value / testDuration.value) * 100;
  return {
    height: `${percentage / 2}%`,
    backgroundColor: percentage > 80 ? '#409EFF' : '#E6E6E6',
    transition: 'height 1s linear, background-color 1s linear'
  };
});

// 工具函数
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

const formatPercentage = (value) => {
  return Math.round(value * 10) / 10;
};

const formatResponseTime = (time) => {
  return Math.round(time);
};

// 更新计时器
const updateTimer = () => {
  if (phase.value !== 'test' || testEnded.value) return;

  remainingTime.value--;

  if (remainingTime.value <= 0) {
    clearInterval(timerInterval.value);
    endTest();
  }
};

// 启动倒计时
const startTimer = () => {
  if (timerInterval.value) clearInterval(timerInterval.value);
  timerInterval.value = setInterval(updateTimer, 1000);
};

// 获取用户信息
const getUserInfo = async () => {
  const userInfoStr = localStorage.getItem('userInfo');
  if (!userInfoStr) {
    ElMessage.warning('未登录，请先登录');
    router.push('/');
    return;
  }

  try {
    const userInfo = JSON.parse(userInfoStr);
    
    // 设置年级
    gradeLevel.value = userInfo.grade > 0 && userInfo.grade <= 3 ? userInfo.grade : 1;
    
    // 设置测试时间（根据年级不同）
    if (gradeLevel.value === 1) {
      testDuration.value = 180; // 一年级3分钟
    } else if (gradeLevel.value === 2) {
      testDuration.value = 240; // 二年级4分钟
    } else {
      testDuration.value = 300; // 三年级5分钟
    }
    remainingTime.value = testDuration.value;

    // 如果已经有userId字段，直接使用
    if (userInfo.userId) {
      userId.value = userInfo.userId;
      return;
    }

    // 否则，尝试查找或创建用户
    const response = await fetch('/api/users/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: userInfo.name,
        school: userInfo.school,
        grade: userInfo.grade,
        class_number: userInfo.classNumber || userInfo.class_number
      })
    });

    if (response.ok) {
      const data = await response.json();
      userId.value = data.id;

      // 更新localStorage中的用户信息
      const updatedUserInfo = { ...userInfo, userId: data.id };
      localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo));
    } else {
      console.error('创建用户失败:', await response.text());
    }
  } catch (error) {
    console.error('解析用户信息失败:', error);
  }
};

// 生成题目
const generateProblems = () => {
  const problems = [];
  
  if (gradeLevel.value === 1) {
    // 一年级：0-10的加减法，加法减法各20题
    // 加法题：20道
    for (let i = 0; i < 20; i++) {
      let a, b;
      // 确保至少有一个数是10，或者两数之和不超过10
      if (Math.random() < 0.3) {
        // 30%的概率一个数是10
        a = 10;
        b = Math.floor(Math.random() * 10); // 0-9的随机数
      } else {
        // 70%的概率两数之和不超过10
        a = Math.floor(Math.random() * 10) + 1; // 1-10的随机数
        b = Math.floor(Math.random() * (11 - a)); // 确保a+b不超过10
      }
      
      // 创建题目
      problems.push({
        index: i + 1,
        text: `${a} + ${b} = `,
        answer: a + b,
        type: "addition"
      });
    }
    
    // 减法题：20道
    for (let i = 0; i < 20; i++) {
      let a, b;
      // 确保结果不为负
      if (Math.random() < 0.3) {
        // 30%的概率第一个数是10
        a = 10;
        b = Math.floor(Math.random() * 11); // 0-10的随机数
      } else {
        // 70%的概率普通减法，确保a >= b
        a = Math.floor(Math.random() * 10) + 1; // 1-10的随机数
        b = Math.floor(Math.random() * (a + 1)); // 确保b不大于a
      }
      
      // 创建题目
      problems.push({
        index: i + 21,
        text: `${a} - ${b} = `,
        answer: a - b,
        type: "subtraction"
      });
    }
  } else if (gradeLevel.value === 2) {
    // 二年级：两位数（可以包含一位数）的加减法
    // 第一部分：30道两数加减法
    for (let i = 0; i < 30; i++) {
      let a, b, isAddition;
      
      isAddition = Math.random() < 0.5; // 50%概率加法
      
      if (isAddition) {
        // 加法，确保结果不超过100
        a = Math.floor(Math.random() * 90) + 10; // 10-99的随机数
        b = Math.floor(Math.random() * (101 - a)); // 确保a+b不超过100
        
        // 创建题目
        problems.push({
          index: i + 1,
          text: `${a} + ${b} = `,
          answer: a + b,
          type: "twoNumbers"
        });
      } else {
        // 减法，确保结果不为负
        a = Math.floor(Math.random() * 90) + 10; // 10-99的随机数
        b = Math.floor(Math.random() * (a + 1)); // 确保b不大于a
        
        // 创建题目
        problems.push({
          index: i + 1,
          text: `${a} - ${b} = `,
          answer: a - b,
          type: "twoNumbers"
        });
      }
    }
    
    // 第二部分：10道三数加减法
    for (let i = 0; i < 10; i++) {
      let a, b, c, op1, op2, text, answer;
      
      // 第一个运算符
      op1 = Math.random() < 0.5 ? "+" : "-";
      
      // 第二个运算符
      op2 = Math.random() < 0.5 ? "+" : "-";
      
      if (op1 === "+") {
        // 第一个运算是加法
        a = Math.floor(Math.random() * 50) + 10; // 10-59的随机数
        b = Math.floor(Math.random() * 40) + 1; // 1-40的随机数
        
        // 中间结果
        let midResult = a + b;
        
        if (op2 === "+") {
          // 加法 + 加法
          c = Math.floor(Math.random() * (101 - midResult)); // 确保最终结果不超过100
          text = `${a} + ${b} + ${c} = `;
          answer = midResult + c;
        } else {
          // 加法 + 减法
          c = Math.floor(Math.random() * (midResult + 1)); // 确保最终结果不为负
          text = `${a} + ${b} - ${c} = `;
          answer = midResult - c;
        }
      } else {
        // 第一个运算是减法，确保a > b
        a = Math.floor(Math.random() * 50) + 50; // 50-99的随机数
        b = Math.floor(Math.random() * a); // 确保b < a
        
        // 中间结果
        let midResult = a - b;
        
        if (op2 === "+") {
          // 减法 + 加法
          c = Math.floor(Math.random() * (101 - midResult)); // 确保最终结果不超过100
          text = `${a} - ${b} + ${c} = `;
          answer = midResult + c;
        } else {
          // 减法 + 减法
          c = Math.floor(Math.random() * (midResult + 1)); // 确保最终结果不为负
          text = `${a} - ${b} - ${c} = `;
          answer = midResult - c;
        }
      }
      
      // 创建题目
      problems.push({
        index: i + 31,
        text: text,
        answer: answer,
        type: "threeNumbers"
      });
    }
  } else if (gradeLevel.value === 3) {
    // 三年级
    // 第一部分：10道三位数和两位数的加减法
    for (let i = 0; i < 10; i++) {
      let a, b, isAddition;
      
      isAddition = Math.random() < 0.5; // 50%概率加法
      
      if (isAddition) {
        // 加法，确保结果不超过1000
        a = Math.floor(Math.random() * 900) + 100; // 100-999的随机数
        b = Math.floor(Math.random() * 90) + 10; // 10-99的随机数
        
        // 创建题目
        problems.push({
          index: i + 1,
          text: `${a} + ${b} = `,
          answer: a + b,
          type: "type1" // 三位数和两位数加减法
        });
      } else {
        // 减法，确保结果不为负
        a = Math.floor(Math.random() * 900) + 100; // 100-999的随机数
        b = Math.floor(Math.random() * 90) + 10; // 10-99的随机数
        
        // 创建题目
        problems.push({
          index: i + 1,
          text: `${a} - ${b} = `,
          answer: a - b,
          type: "type1" // 三位数和两位数加减法
        });
      }
    }
    
    // 第二部分：20道三位数与三位数的加减法
    for (let i = 0; i < 20; i++) {
      let a, b, isAddition;
      
      isAddition = Math.random() < 0.5; // 50%概率加法
      
      if (isAddition) {
        // 加法，确保结果不超过1000
        a = Math.floor(Math.random() * 500) + 100; // 100-599的随机数
        b = Math.floor(Math.random() * (1000 - a - 100)) + 100; // 确保a+b不超过1000，且b是三位数
        
        // 创建题目
        problems.push({
          index: i + 11,
          text: `${a} + ${b} = `,
          answer: a + b,
          type: "type2" // 三位数与三位数加减法
        });
      } else {
        // 减法，确保结果不为负
        a = Math.floor(Math.random() * 900) + 100; // 100-999的随机数
        b = Math.floor(Math.random() * (a - 100)) + 100; // 确保b不大于a，且b是三位数
        
        // 创建题目
        problems.push({
          index: i + 11,
          text: `${a} - ${b} = `,
          answer: a - b,
          type: "type2" // 三位数与三位数加减法
        });
      }
    }
    
    // 第三部分：10道三位数3个数字的加减法
    for (let i = 0; i < 10; i++) {
      let a, b, c, op1, op2, text, answer;
      
      // 第一个运算符
      op1 = Math.random() < 0.5 ? "+" : "-";
      
      // 第二个运算符
      op2 = Math.random() < 0.5 ? "+" : "-";
      
      if (op1 === "+") {
        // 第一个运算是加法
        a = Math.floor(Math.random() * 400) + 100; // 100-499的随机数
        b = Math.floor(Math.random() * 400) + 100; // 100-499的随机数
        
        // 中间结果
        let midResult = a + b;
        
        if (op2 === "+") {
          // 加法 + 加法
          c = Math.floor(Math.random() * (1001 - midResult)) + 1; // 确保最终结果不超过1000
          if (c < 100) c = 100; // 确保c是三位数
          text = `${a} + ${b} + ${c} = `;
          answer = midResult + c;
        } else {
          // 加法 + 减法
          c = Math.floor(Math.random() * (midResult - 100)) + 100; // 确保最终结果不为负且c是三位数
          text = `${a} + ${b} - ${c} = `;
          answer = midResult - c;
        }
      } else {
        // 第一个运算是减法，确保a > b
        a = Math.floor(Math.random() * 400) + 500; // 500-899的随机数
        b = Math.floor(Math.random() * (a - 400)) + 100; // 确保b < a且b是三位数
        
        // 中间结果
        let midResult = a - b;
        
        if (op2 === "+") {
          // 减法 + 加法
          c = Math.floor(Math.random() * (1001 - midResult)) + 100; // 确保最终结果不超过1000且c是三位数
          text = `${a} - ${b} + ${c} = `;
          answer = midResult + c;
        } else {
          // 减法 + 减法
          c = Math.floor(Math.random() * (midResult - 100)) + 100; // 确保最终结果不为负且c是三位数
          text = `${a} - ${b} - ${c} = `;
          answer = midResult - c;
        }
      }
      
      // 创建题目
      problems.push({
        index: i + 31,
        text: text,
        answer: answer,
        type: "type3" // 三位数三数加减法
      });
    }
  }
  
  // 随机打乱题目顺序
  for (let i = problems.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [problems[i], problems[j]] = [problems[j], problems[i]];
  }
  
  // 重新设置题目序号
  problems.forEach((problem, index) => {
    problem.index = index + 1;
  });
  
  return problems;
};

// 创建测试会话
const createTestSession = async () => {
  if (!userId.value) {
    console.error('无法创建测试会话：缺少用户ID');
    return;
  }

  try {
    const response = await fetch('/api/calculation/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId.value,
        grade_level: gradeLevel.value,
        total_questions: totalProblems.value
      })
    });

    if (response.ok) {
      const data = await response.json();
      testSessionId.value = data.id;
      console.log('测试会话创建成功，ID:', testSessionId.value);
    } else {
      console.error('创建测试会话失败:', await response.text());
    }
  } catch (error) {
    console.error('创建测试会话请求失败:', error);
  }
};

// 更新测试会话进度
const updateTestSession = async (progress) => {
  if (!testSessionId.value) return;

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        progress: progress
      })
    });

    if (!response.ok) {
      console.error('更新测试会话失败:', await response.text());
    }
  } catch (error) {
    console.error('更新测试会话请求失败:', error);
  }
};

// 完成测试会话
const completeTestSession = async () => {
  if (!testSessionId.value) return;

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      console.log('测试会话已完成');
    } else {
      console.error('完成测试会话失败:', await response.text());
    }
  } catch (error) {
    console.error('完成测试会话请求失败:', error);
  }
};

// 保存题目答案
const saveProblem = async (problem, userAnswer, responseTime) => {
  if (!testSessionId.value || !userId.value) {
    console.error('无法保存题目：缺少会话ID或用户ID');
    return;
  }

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}/problems`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId.value,
        test_session_id: testSessionId.value,
        problem_index: problem.index,
        problem_text: problem.text,
        correct_answer: problem.answer,
        user_answer: userAnswer,
        response_time: responseTime
      })
    });

    if (!response.ok) {
      console.error('保存题目失败:', await response.text());
    }
  } catch (error) {
    console.error('保存题目请求失败:', error);
  }
};

// 获取测试结果
const getTestResults = async () => {
  if (!testSessionId.value) return;

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}/results`);
    
    if (response.ok) {
      const data = await response.json();
      
      // 更新测试结果
      testResults.completedProblems = data.stats.totalProblems;
      testResults.correctProblems = data.stats.correctProblems;
      testResults.accuracy = data.stats.accuracy;
      testResults.averageResponseTime = data.stats.averageResponseTime;
      
      // 根据年级更新题型统计
      if (gradeLevel.value === 1) {
        if (data.stats.problemTypeStats.addition) {
          typeStats.addition.completed = data.stats.problemTypeStats.addition.total;
          typeStats.addition.correct = data.stats.problemTypeStats.addition.correct;
          typeStats.addition.accuracy = data.stats.problemTypeStats.addition.accuracy;
        }
        
        if (data.stats.problemTypeStats.subtraction) {
          typeStats.subtraction.completed = data.stats.problemTypeStats.subtraction.total;
          typeStats.subtraction.correct = data.stats.problemTypeStats.subtraction.correct;
          typeStats.subtraction.accuracy = data.stats.problemTypeStats.subtraction.accuracy;
        }
      } else if (gradeLevel.value === 2) {
        if (data.stats.problemTypeStats.twoNumbers) {
          typeStats.twoNumbers.completed = data.stats.problemTypeStats.twoNumbers.total;
          typeStats.twoNumbers.correct = data.stats.problemTypeStats.twoNumbers.correct;
          typeStats.twoNumbers.accuracy = data.stats.problemTypeStats.twoNumbers.accuracy;
        }
        
        if (data.stats.problemTypeStats.threeNumbers) {
          typeStats.threeNumbers.completed = data.stats.problemTypeStats.threeNumbers.total;
          typeStats.threeNumbers.correct = data.stats.problemTypeStats.threeNumbers.correct;
          typeStats.threeNumbers.accuracy = data.stats.problemTypeStats.threeNumbers.accuracy;
        }
      } else if (gradeLevel.value === 3) {
        if (data.stats.problemTypeStats.twoDigitOperations) {
          typeStats.type1.completed = data.stats.problemTypeStats.twoDigitOperations.total;
          typeStats.type1.correct = data.stats.problemTypeStats.twoDigitOperations.correct;
          typeStats.type1.accuracy = data.stats.problemTypeStats.twoDigitOperations.accuracy;
        }
        
        if (data.stats.problemTypeStats.threeDigitOperations) {
          typeStats.type2.completed = data.stats.problemTypeStats.threeDigitOperations.total;
          typeStats.type2.correct = data.stats.problemTypeStats.threeDigitOperations.correct;
          typeStats.type2.accuracy = data.stats.problemTypeStats.threeDigitOperations.accuracy;
        }
        
        if (data.stats.problemTypeStats.threeDigitThreeNumbers) {
          typeStats.type3.completed = data.stats.problemTypeStats.threeDigitThreeNumbers.total;
          typeStats.type3.correct = data.stats.problemTypeStats.threeDigitThreeNumbers.correct;
          typeStats.type3.accuracy = data.stats.problemTypeStats.threeDigitThreeNumbers.accuracy;
        }
      }
      
      console.log('测试结果获取成功');
    } else {
      console.error('获取测试结果失败:', await response.text());
    }
  } catch (error) {
    console.error('获取测试结果请求失败:', error);
  }
};

// 进入下一阶段
const nextPhase = () => {
  if (phase.value === 'welcome') {
    startTest();
  }
};

// 开始测试
const startTest = async () => {
  // 获取用户信息
  await getUserInfo();
  
  // 生成题目
  problems.value = generateProblems();
  
  // 创建测试会话
  await createTestSession();
  
  // 准备测试
  phase.value = 'test';
  currentIndex.value = 0;
  userAnswer.value = '';
  problemStartTime.value = Date.now();
  
  // 启动计时器
  startTimer();
  
  // 聚焦答案输入框
  nextTick(() => {
    if (answerInput.value) {
      answerInput.value.focus();
    }
  });
};

// 提交答案
const submitAnswer = async () => {
  if (isProcessing.value || userAnswer.value === '') return;
  
  isProcessing.value = true;
  
  // 计算反应时间
  const endTime = Date.now();
  responseTime.value = endTime - problemStartTime.value;
  
  // 获取当前题目
  const problem = problems.value[currentIndex.value];
  
  // 保存答题结果
  await saveProblem(problem, parseInt(userAnswer.value), responseTime.value);
  
  // 更新进度
  await updateTestSession(currentIndex.value + 1);
  
  // 准备下一题
  isProcessing.value = false;
  userAnswer.value = '';
  
  if (currentIndex.value < problems.value.length - 1 && remainingTime.value > 0) {
    currentIndex.value++;
    problemStartTime.value = Date.now();
    
    // 聚焦答案输入框
    nextTick(() => {
      if (answerInput.value) {
        answerInput.value.focus();
      }
    });
  } else {
    // 测试结束
    endTest();
  }
};

// 结束测试
const endTest = async () => {
  if (testEnded.value) return;
  
  testEnded.value = true;
  clearInterval(timerInterval.value);
  
  // 显示加载中提示
  const loading = ElLoading.service({
    lock: true,
    text: '正在处理结果...',
    background: 'rgba(0, 0, 0, 0.7)'
  });
  
  try {
    // 完成测试会话
    await completeTestSession();
    
    // 获取测试结果
    await getTestResults();
    
    // 显示结果页面
    phase.value = 'result';
  } catch (error) {
    console.error('结束测试失败:', error);
    ElMessage.error('处理测试结果失败，请重试');
  } finally {
    // 关闭加载提示
    loading.close();
  }
};

// 返回测试选择
const goToSelection = () => {
  router.push('/selection');
};

// 重新测试
const restartTest = () => {
  // 重置状态
  phase.value = 'welcome';
  currentIndex.value = 0;
  userAnswer.value = '';
  problems.value = [];
  testEnded.value = false;
  remainingTime.value = testDuration.value;
  testSessionId.value = null;
  
  // 重置结果
  Object.assign(testResults, {
    completedProblems: 0,
    correctProblems: 0,
    accuracy: 0,
    averageResponseTime: 0
  });
  
  // 重置题型统计
  if (gradeLevel.value === 1) {
    Object.assign(typeStats.addition, { completed: 0, correct: 0, accuracy: 0 });
    Object.assign(typeStats.subtraction, { completed: 0, correct: 0, accuracy: 0 });
  } else if (gradeLevel.value === 2) {
    Object.assign(typeStats.twoNumbers, { completed: 0, correct: 0, accuracy: 0 });
    Object.assign(typeStats.threeNumbers, { completed: 0, correct: 0, accuracy: 0 });
  } else if (gradeLevel.value === 3) {
    Object.assign(typeStats.type1, { completed: 0, correct: 0, accuracy: 0 });
    Object.assign(typeStats.type2, { completed: 0, correct: 0, accuracy: 0 });
    Object.assign(typeStats.type3, { completed: 0, correct: 0, accuracy: 0 });
  }
};

// 调试模式：跳转到指定题目
const jumpToProblem = () => {
  if (phase.value !== 'test' || jumpToIndex.value < 1 || jumpToIndex.value > problems.value.length) {
    return;
  }
  
  currentIndex.value = jumpToIndex.value - 1;
  userAnswer.value = '';
  problemStartTime.value = Date.now();
  
  // 聚焦答案输入框
  nextTick(() => {
    if (answerInput.value) {
      answerInput.value.focus();
    }
  });
};

// 键盘监听函数
const keyHandler = (e) => {
  // 检测是否同时按下【】键 (Alt+[ 和 Alt+])
  if ((e.key === '[' && e.altKey) || (e.key === ']' && e.altKey)) {
    debugMode.value = !debugMode.value;
    return;
  }
};

// 生命周期钩子
onMounted(() => {
  // 添加键盘事件监听
  window.addEventListener('keydown', keyHandler);
  
  // 获取用户信息和初始化年级
  getUserInfo();
});

onUnmounted(() => {
  // 清理资源
  window.removeEventListener('keydown', keyHandler);
  clearInterval(timerInterval.value);
});

// 观察remainingTime变化，以便在调试模式下更新
watch(remainingTime, (newVal) => {
  if (debugMode.value && phase.value === 'test') {
    // 调试模式下手动更新倒计时，触发计算属性重新计算沙漏样式
  }
});
</script>