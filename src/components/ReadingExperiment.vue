<template>
  <div class="experiment-page">
    <TopNavBar />
    <div class="experiment-container">
    <!-- 调试面板 -->
    <div v-if="debugMode" class="debug-panel">
      <h3>调试模式</h3>
      <div class="debug-controls">
        <el-input-number v-model="jumpToTrial" :min="1" :max="maxTrials" label="跳转题号"></el-input-number>
        <el-button type="primary" @click="jumpToTrialNumber">跳转</el-button>
        <el-input-number v-model="remainingTime" :min="0" :max="180" label="剩余时间(秒)"></el-input-number>
        <el-button type="primary" @click="updateTimer">更新时间</el-button>
      </div>
    </div>

    <!-- 实验内容区域 -->
    <div class="content-area">
      <!-- 指导语阶段 -->
      <div v-if="phase === 'welcome'" class="instruction">
        <h2>阅读流畅性实验</h2>
        <p>同学们，我们现在来玩的这个游戏是让你阅读句子，并判断句子是否正确。</p>
        <p>请你快速认真地读完句子（默读），如果你觉得句子是正确的，你就在句子后面的括号内打个"√"；如果你觉得句子是错误的，那就在句子后面的括号内打个"╳"。</p>
        <p>如果读句子时遇到不认识的字，也不要停下来，抓紧时间，继续往后做。</p>
        <p>记住要一题一题从上往下做，做完一页后快速翻到后面再继续做。</p>
        <p>一共有3分钟时间来阅读，题目很多，肯定做不完的。所以没有做完也没有关系，只要尽快做就好了。</p>
        <div class="key-instruction">
          <div>按键说明：</div>
          <div>Q 键 = 正确（√）</div>
          <div>W 键 = 错误（╳）</div>
        </div>
        <p style="margin-top:15px">你也可以直接点击屏幕上的"正确"或"错误"按钮来回答。</p>
        <el-button type="primary" class="continue-btn" @click="nextPhase">下一步</el-button>
      </div>

      <!-- 练习阶段说明 -->
      <div v-else-if="phase === 'practice-intro'" class="instruction">
        <h2>练习阶段</h2>
        <p>我们先来练习几道题，看你有没有明白，好吗？</p>
        <el-button type="primary" class="continue-btn" @click="nextPhase">开始练习</el-button>
      </div>

      <!-- 练习题阶段 -->
      <div v-else-if="phase === 'practice'" class="trial-container">
        <!-- 演示题 -->
        <div v-if="currentPracticeTrial.demonstrated" class="practice-demo">
          <div class="sentence">{{ currentPracticeTrial.text.split('（')[0] }}</div>
          <div class="answer">
            <span class="answer-label">（</span>
            <span class="answer-mark wrong-mark answer-animation">╳</span>
            <span class="answer-label">）</span>
          </div>
          <div class="explanation">
            <p>第{{ currentPracticeTrial.id }}题："{{ currentPracticeTrial.text.split('（')[0] }}"对还是错呢？这是错的。</p>
          </div>
          <el-button type="primary" class="continue-btn" @click="nextTrial">下一题</el-button>
        </div>

        <!-- 练习题 -->
        <div v-else>
          <div class="sentence">{{ currentPracticeTrial.text.split('（')[0] }}</div>
          <div class="answer">
            <span class="answer-label">（</span>
            <span class="answer-mark" ref="answerMark"></span>
            <span class="answer-label">）</span>
          </div>
          <div class="instruction">
            <p>请判断这个句子是正确的还是错误的：</p>
            <div class="key-guide">
              <div>按 Q 键 = 正确（√）</div>
              <div>按 W 键 = 错误（╳）</div>
            </div>
          </div>
          <div class="answer-buttons">
            <button class="answer-btn correct-btn" :class="{ 'selected': userAnswer === true }"
              @click="handleAnswer(true)">
              正确 (√)
            </button>
            <button class="answer-btn wrong-btn" :class="{ 'selected': userAnswer === false }"
              @click="handleAnswer(false)">
              错误 (╳)
            </button>
          </div>
        </div>
      </div>

      <!-- 正式阶段说明 -->
      <div v-else-if="phase === 'formal-intro'" class="instruction">
        <h2>正式测验</h2>
        <p>好的，现在我们来多做一些。都准备好了吗？</p>
        <p>准备好后，点击"开始"按钮，计时将立即开始！</p>
        <el-button type="primary" class="continue-btn" @click="startFormalTest">开始</el-button>
      </div>

      <!-- 正式阶段题目 -->
      <div v-else-if="phase === 'formal' && !testEnded" class="trial-container formal-trial">
        <div class="trial-header">
          <div class="trial-number">第 {{ currentFormalTrial.id }} 题</div>
          <div class="trial-timer">
            <span>{{ formatTime(remainingTime) }}</span>
          </div>
        </div>
        <div class="sentence">{{ currentFormalTrial.text.split('（')[0] }}</div>
        <div class="answer">
          <span class="answer-label">（</span>
          <span class="answer-mark" ref="answerMark"></span>
          <span class="answer-label">）</span>
        </div>
        <div class="answer-buttons">
          <button class="answer-btn correct-btn" :class="{ 'selected': userAnswer === true }" @click="handleAnswer(true)">
            正确 (√)
          </button>
          <button class="answer-btn wrong-btn" :class="{ 'selected': userAnswer === false }" @click="handleAnswer(false)">
            错误 (╳)
          </button>
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

      <!-- 实验结束 -->
      <div v-else-if="phase === 'end'" class="experiment-end">
        <h2>实验结束</h2>
        <p>感谢你的参与！</p>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { ElMessage } from 'element-plus';
import TopNavBar from './TopNavBar.vue';

// 状态变量
const phase = ref('welcome'); // 实验阶段: welcome, practice-intro, practice, formal-intro, formal, end
const currentPracticeIndex = ref(0);
const currentFormalIndex = ref(0);
const userAnswer = ref(null);
const answerMark = ref(null);
const isProcessing = ref(false);
const testEnded = ref(false);
const debugMode = ref(false);
const jumpToTrial = ref(1);
const maxTrials = ref(100);
const remainingTime = ref(180); // 3分钟倒计时
const startTime = ref(null);
const timerInterval = ref(null);
const testSessionId = ref(null);
const userId = ref(null);
// 计算属性
const currentPracticeTrial = computed(() => {
  return practiceTrials[currentPracticeIndex.value] || {};
});

const currentFormalTrial = computed(() => {
  return formalTrials.value[currentFormalIndex.value] || {};
});

// 沙漏样式计算
const hourglassTopStyle = computed(() => {
  const percentage = (remainingTime.value / 180) * 100;
  return {
    height: `${percentage / 2}%`,
    transition: 'height 1s linear'
  };
});

const hourglassBottomStyle = computed(() => {
  const percentage = 100 - (remainingTime.value / 180) * 100;
  return {
    height: `${percentage / 2}%`,
    backgroundColor: percentage > 80 ? '#409EFF' : '#E6E6E6',
    transition: 'height 1s linear, background-color 1s linear'
  };
});

// 教学阶段试题数据
const practiceTrials = [
  { id: 1, text: "太阳从西边升起。（      ）", correct: false, demonstrated: true },
  { id: 2, text: "燕子会飞。（       ）", correct: true, demonstrated: false },
  { id: 3, text: "写字要用手。（       ）", correct: true, demonstrated: false }
];

// 正式阶段试题数据
const formalTrials = ref([]);

// 记录开始时间的方法（用于计算反应时间）
let trialStartTime = 0;
// 获取用户信息
const getUserInfo = async () => {
  const userInfoStr = localStorage.getItem('userInfo');
  if (!userInfoStr) {
    console.error('无法获取用户信息：localStorage中没有userInfo');
    return;
  }
  
  try {
    const userInfo = JSON.parse(userInfoStr);
    
    // 如果已经有userId字段，直接使用
    if (userInfo.userId) {
      userId.value = userInfo.userId;
      console.log('使用已存在的用户ID:', userId.value);
      return userInfo.userId;
    }
    
    // 否则，创建新用户
    console.log('准备创建新用户...');
    
    const userResponse = await fetch('/api/users/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: userInfo.name,
        school: userInfo.school,
        grade: userInfo.grade,
        class_number: userInfo.class_number || userInfo.classNumber
      })
    });
    
    if (!userResponse.ok) {
      const errorText = await userResponse.text();
      console.error('创建用户失败:', errorText);
      throw new Error(`创建用户失败: ${errorText}`);
    }
    
    const userData = await userResponse.json();
    userId.value = userData.id;
    console.log('新用户创建成功，ID:', userId.value);
    
    // 更新localStorage中的用户信息
    const updatedUserInfo = { ...userInfo, userId: userData.id };
    localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo));
    
    return userData.id;
  } catch (error) {
    console.error('处理用户信息失败:', error);
    throw error;
  }
};

// 创建用户
const createUser = async (userInfo) => {
  try {
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
      console.log('新用户创建成功，ID:', userId.value);
      
      // 更新localStorage中的用户信息
      const updatedUserInfo = { ...userInfo, userId: data.id };
      localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo));
    } else {
      console.error('创建用户失败:', await response.text());
    }
  } catch (error) {
    console.error('创建用户请求失败:', error);
  }
};

// 创建测试会话
const createTestSession = async () => {
  if (!userId.value) {
    console.error('无法创建测试会话：缺少用户ID');
    throw new Error('缺少用户ID');
  }
  
  try {
    console.log(`准备为用户ID=${userId.value}创建测试会话`);
    
    const response = await fetch('/api/reading-fluency/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId.value,
        total_questions: formalTrials.value.length
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('创建测试会话失败:', errorText);
      throw new Error(`创建测试会话失败: ${errorText}`);
    }
    
    const data = await response.json();
    testSessionId.value = data.id;
    console.log('测试会话创建成功，ID:', testSessionId.value);
    return data;
  } catch (error) {
    console.error('创建测试会话请求失败:', error);
    throw error;
  }
};
// 添加计算正确题目数量的计算属性
const correctTrialsCount = computed(() => {
  return formalTrials.value.filter(trial => trial.userAnswer === true).length;
});
// 更新测试会话进度 - 修复后的版本
const updateTestSession = async (progress) => {
  if (!testSessionId.value) return;
  
  try {
    const response = await fetch(`/api/reading-fluency/sessions/${testSessionId.value}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        progress: progress
        // 移除 correct_count，让后端根据每道题的正确性计算
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
    const response = await fetch(`/api/reading-fluency/sessions/${testSessionId.value}/complete`, {
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

// 在测试会话中保存答题记录
const saveTrialWithSession = async (trialData) => {
  if (!testSessionId.value || !userId.value) {
    // 如果测试会话不存在，使用旧的保存方法
    return saveTrialLegacy(trialData);
  }
  
  try {
    const response = await fetch(`/api/reading-fluency/sessions/${testSessionId.value}/trials`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId.value,
        trial_id: trialData.trial_id,
        user_answer: trialData.user_answer,
        response_time: trialData.response_time
      })
    });
    
    if (!response.ok) {
      console.error('保存答题记录失败:', await response.text());
    }
  } catch (error) {
    console.error('保存答题记录请求失败:', error);
  }
};
// 键盘监听函数
const keyHandler = (e) => {
  // 检测是否同时按下【】键 (Alt+[ 和 Alt+])
  if ((e.key === '[' && e.altKey) || (e.key === ']' && e.altKey)) {
    debugMode.value = !debugMode.value;
    return;
  }

  // 如果正在处理答案或不在练习/正式阶段，则不处理键盘输入
  if (isProcessing.value || (phase.value !== 'practice' && phase.value !== 'formal') ||
    (phase.value === 'practice' && currentPracticeTrial.value.demonstrated)) {
    return;
  }

  // 按键响应
  if (e.key.toLowerCase() === 'q') {
    handleAnswer(true);
  } else if (e.key.toLowerCase() === 'w') {
    handleAnswer(false);
  }
};

// 格式化时间显示
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

// 更新计时器
const updateTimer = () => {
  if (phase.value !== 'formal' || testEnded.value) return;

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

// 获取试验数据
const fetchTrials = async () => {
  try {
    const response = await fetch('/api/reading-fluency/trials');
    if (response.ok) {
      const data = await response.json();
      formalTrials.value = data.formalTrials.map((trial, index) => ({
        id: index + 1,
        text: trial,
        startTime: 0,
        responseTime: 0,
        userAnswer: null
      }));
      maxTrials.value = formalTrials.value.length;
    } else {
      // 如果API请求失败，使用本地数据
      parseLocalTrials();
    }
  } catch (error) {
    console.error('获取试验数据失败:', error);
    // 解析本地试验数据
    parseLocalTrials();
  }
};

// 解析本地试验数据（备用方案）
const parseLocalTrials = () => {
  const formalTrialsRaw = [
    "天安门在北京。（       ）",
    "老虎喜欢吃青草。（        ）",
    "蚂蚁比大象小很多。（        ）",
    "汽车比火车长很多。（       ）",
    "猫是捉老鼠的能手。（        ）",
    "骑自行车比坐飞机快。（        ）",
    "太阳给了我们光和热。（        ）",
    "海水是可以直接喝的。（        ）",
    "月亮上也住着许多人。（        ）",
    "多做运动对身体有好处。（        ）"
  ];

  formalTrials.value = formalTrialsRaw.map((trial, index) => ({
    id: index + 1,
    text: trial,
    startTime: 0,
    responseTime: 0,
    userAnswer: null
  }));

  maxTrials.value = formalTrials.value.length;
  console.warn('使用备用试题数据，请检查API连接');
};
// 修改 handleAnswer 方法
const handleAnswer = (isCorrect) => {
  if (isProcessing.value) return;

  isProcessing.value = true;
  userAnswer.value = isCorrect;

  // 计算反应时间（毫秒）
  const responseTime = Date.now() - trialStartTime;

  // 更新答案标记
  const markEl = answerMark.value;
  if (markEl) {
    markEl.textContent = isCorrect ? '√' : '╳';
    markEl.classList.remove('correct-mark', 'wrong-mark', 'answer-animation');

    if (isCorrect) {
      markEl.classList.add('correct-mark');
    } else {
      markEl.classList.add('wrong-mark');
    }

    // 触发动画
    setTimeout(() => {
      markEl.classList.add('answer-animation');
    }, 10);
  }

  // 保存数据（如果在正式阶段）
  if (phase.value === 'formal') {
    const currentTrial = formalTrials.value[currentFormalIndex.value];
    if (currentTrial) {
      currentTrial.userAnswer = isCorrect;
      currentTrial.responseTime = responseTime;

      // 保存到服务器
      saveTrialWithSession({
        trial_id: currentTrial.id,
        user_answer: isCorrect,
        response_time: responseTime
      });
      
      // 只更新会话进度，让后端计算正确数量
      updateTestSession(currentFormalIndex.value + 1);
    }
  }

  // 短暂延迟后进入下一题
  setTimeout(() => {
    nextTrial();
    isProcessing.value = false;
  }, 500);
};
// 进入下一阶段
const nextPhase = () => {
  switch (phase.value) {
    case 'welcome':
      phase.value = 'practice-intro';
      break;
    case 'practice-intro':
      phase.value = 'practice';
      currentPracticeIndex.value = 0;
      prepareCurrentTrial();
      break;
    case 'practice':
      if (currentPracticeIndex.value >= practiceTrials.length - 1) {
        phase.value = 'formal-intro';
      } else {
        currentPracticeIndex.value++;
        prepareCurrentTrial();
      }
      break;
    case 'formal-intro':
      startFormalTest();
      break;
    default:
      break;
  }
};

// 修改 startFormalTest 方法确保正确的执行顺序
const startFormalTest = async () => {
  phase.value = 'formal';
  currentFormalIndex.value = 0;
  remainingTime.value = 180; // 重置计时器
  
  try {
    // 获取用户信息并等待完成
    await getUserInfo();
    
    // 确保已获取到用户ID
    if (!userId.value) {
      console.error('无法开始测试：未获取到用户ID');
      ElMessage.error('用户信息不完整，请返回重新填写');
      return;
    }
    
    // 创建测试会话并等待完成
    await createTestSession();
    
    // 只有在成功创建会话后才启动计时器
    if (testSessionId.value) {
      startTimer(); // 启动计时器
      prepareCurrentTrial();
    } else {
      console.error('无法启动测试：会话创建失败');
      ElMessage.error('会话创建失败，请刷新页面重试');
    }
  } catch (error) {
    console.error('启动正式测试失败:', error);
    ElMessage.error('启动测试失败，请刷新页面重试');
  }
};

// 准备当前试题
const prepareCurrentTrial = () => {
  userAnswer.value = null;

  // 记录试题开始时间（用于计算反应时间）
  trialStartTime = Date.now();

  nextTick(() => {
    // 确保DOM更新后再重置答案标记
    if (answerMark.value) {
      answerMark.value.textContent = '';
      answerMark.value.classList.remove('correct-mark', 'wrong-mark', 'answer-animation');
    }
  });
};

// 进入下一题
const nextTrial = () => {
  if (phase.value === 'practice') {
    if (currentPracticeIndex.value >= practiceTrials.length - 1) {
      phase.value = 'formal-intro';
    } else {
      currentPracticeIndex.value++;
      prepareCurrentTrial();
    }
  } else if (phase.value === 'formal') {
    if (currentFormalIndex.value >= formalTrials.value.length - 1 || remainingTime.value <= 0) {
      endTest();
    } else {
      currentFormalIndex.value++;
      prepareCurrentTrial();
    }
  }
};

// 修改 endTest 方法
const endTest = async () => {
  clearInterval(timerInterval.value);
  testEnded.value = true;
  
  // 完成测试会话
  await completeTestSession();
  
  phase.value = 'end';
  ElMessage.success('实验已完成，感谢您的参与！');
};
// 跳转到指定题号（仅调试模式）
const jumpToTrialNumber = () => {
  if (phase.value !== 'formal') {
    ElMessage.warning('只能在正式阶段跳转题目');
    return;
  }

  const targetIndex = Math.min(jumpToTrial.value - 1, formalTrials.value.length - 1);
  currentFormalIndex.value = Math.max(0, targetIndex);
  prepareCurrentTrial();
  ElMessage.success(`已跳转到第 ${jumpToTrial.value} 题`);
};

// 保存试验数据到服务器
const saveTrialData = async (trialData) => {
  // 验证数据
  if (trialData.user_answer === undefined) {
    console.error('saveTrialData: user_answer 未定义，设置为默认值false');
    trialData.user_answer = false;
  }

  if (trialData.response_time === undefined || trialData.response_time === null) {
    console.error('saveTrialData: response_time 未定义，设置为默认值0');
    trialData.response_time = 0;
  }

  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');

  // 确保必要的用户信息存在
  if (!userInfo.name || !userInfo.school || !userInfo.grade || !userInfo.class_number) {
    console.error('saveTrialData: 用户信息不完整', userInfo);
    return; // 如果用户信息不完整，不继续保存
  }

  try {
    const response = await fetch('/api/reading-fluency/save-trial', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ...userInfo,
        ...trialData,
        timestamp: new Date().toISOString()
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('保存数据失败:', errorData);
    } else {
      console.log('试验数据保存成功:', trialData.trial_id);
    }
  } catch (error) {
    console.error('保存数据出错:', error);
  }
};

// 生命周期钩子
onMounted(async () => {
  // 添加键盘事件监听
  window.addEventListener('keydown', keyHandler);

  // 获取试验数据
  await fetchTrials();

  // 确保初始滚动位置在页面顶部
  window.scrollTo(0, 0);
});

onUnmounted(() => {
  // 清理资源
  window.removeEventListener('keydown', keyHandler);
  clearInterval(timerInterval.value);
});

// 观察remainingTime变化，以便在调试模式下更新
watch(remainingTime, (newVal) => {
  if (debugMode.value && phase.value === 'formal') {
    // 调试模式下手动更新倒计时，触发计算属性重新计算沙漏样式
  }
});
</script>

<style>
/* 全局样式 */
.experiment-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.experiment-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: calc(100vh - 60px);
  padding: 20px;
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

.key-instruction {
  margin: 20px 0;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-weight: bold;
}

.continue-btn {
  margin: 20px auto;
  display: block;
  min-width: 120px;
  font-weight: bold;
}

/* 试题样式 */
.trial-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 700px;
  margin: 0 auto;
  padding: 20px;
}

.trial-header {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 20px;
  align-items: center;
}

.trial-number {
  font-weight: bold;
  font-size: 18px;
}

.trial-timer {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
  background-color: white;
  padding: 5px 10px;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.sentence {
  font-size: 20px;
  line-height: 1.5;
  margin: 20px 0;
  text-align: center;
}

.answer {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 15px 0;
}

.answer-label {
  font-size: 24px;
  padding: 0 5px;
}

.answer-mark {
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  font-weight: bold;
}

.correct-mark {
  color: #67C23A;
}

.wrong-mark {
  color: #F56C6C;
}

.answer-animation {
  animation: pop-in 0.3s ease;
}

@keyframes pop-in {
  0% {
    transform: scale(0);
    opacity: 0;
  }

  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }

  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.answer-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
}

.answer-btn {
  padding: 10px 20px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fff;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.answer-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.answer-btn::after {
  content: '';
  display: block;
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  pointer-events: none;
  background-image: radial-gradient(circle, #000 10%, transparent 10.01%);
  background-repeat: no-repeat;
  background-position: 50%;
  transform: scale(10, 10);
  opacity: 0;
  transition: transform 0.5s, opacity 0.5s;
}

.answer-btn:active::after {
  transform: scale(0, 0);
  opacity: 0.1;
  transition: 0s;
}

.correct-btn {
  color: #67C23A;
  border-color: #c2e7b0;
}

.correct-btn:hover {
  background-color: #f0f9eb;
  border-color: #85ce61;
}

.wrong-btn {
  color: #F56C6C;
  border-color: #fbc4c4;
}

.wrong-btn:hover {
  background-color: #fef0f0;
  border-color: #f78989;
}

.correct-btn.selected {
  background-color: #f0f9eb;
  color: #67C23A;
  border-color: #67C23A;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.2);
}

.wrong-btn.selected {
  background-color: #fef0f0;
  color: #F56C6C;
  border-color: #F56C6C;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.2);
}

.explanation {
  background-color: #f0f7ff;
  padding: 15px;
  border-radius: 4px;
  margin: 20px 0;
  width: 100%;
}

.key-guide {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}

/* 计时器和沙漏 */
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

/* 实验结束 */
.experiment-end {
  text-align: center;
  padding: 40px;
}

.experiment-end h2 {
  color: #409EFF;
  margin-bottom: 20px;
}
</style>