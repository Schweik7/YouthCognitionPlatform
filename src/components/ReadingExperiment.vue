<template>
  <div class="experiment-container">
    <!-- 级别选择面板 -->
    <div v-if="phase === 'level-selection'" class="level-selection">
      <h2>阅读流畅性测试</h2>
      <p>请选择适合的测试级别：</p>
      <div class="level-buttons">
        <el-button type="primary" size="large" @click="selectLevel('elementary')">
          小学级别
        </el-button>
        <el-button type="primary" size="large" @click="selectLevel('junior_high')">
          初中及以上级别
        </el-button>
      </div>
    </div>

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
        <h2>阅读流畅性测试</h2>
        
        <!-- 小学级别指导语 -->
        <div v-if="!isJuniorHighLevel">
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
        </div>
        
        <!-- 初中及以上级别指导语 -->
        <div v-else>
          <p>欢迎参加阅读理解测试！本测试包含判断题和选择题两种类型。</p>
          <p>对于判断题，请阅读句子并判断其是否正确；对于选择题，请根据题目要求选择最合适的答案。</p>
          <p>有些题目配有图片，请仔细观察图片内容来帮助你做出判断。</p>
          <p>测试时间为3分钟，请尽可能多地完成题目，但不要因为时间紧张而草率作答。</p>
          <div class="key-instruction">
            <div>按键说明：</div>
            <div>判断题：Q 键 = 正确，W 键 = 错误</div>
            <div>选择题：A/B/C/D 键对应相应选项</div>
          </div>
          <p style="margin-top:15px">你也可以直接点击屏幕上的按钮来回答。</p>
        </div>
        
        <el-button type="primary" class="continue-btn" @click="nextPhase">下一步</el-button>
      </div>

      <!-- 练习阶段说明 -->
      <div v-else-if="phase === 'practice-intro'" class="instruction">
        <h2>练习阶段</h2>
        <p v-if="!isJuniorHighLevel">我们先来练习几道题，看你有没有明白，好吗？</p>
        <p v-else>我们先通过几道练习题来熟悉一下答题方式。</p>
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
            <button class="answer-btn correct-btn" :class="{ 'selected': userAnswer === 'true' }"
              @click="handleAnswer('true')">
              正确 (√)
            </button>
            <button class="answer-btn wrong-btn" :class="{ 'selected': userAnswer === 'false' }"
              @click="handleAnswer('false')">
              错误 (╳)
            </button>
          </div>
        </div>
      </div>

      <!-- 正式阶段说明 -->
      <div v-else-if="phase === 'formal-intro'" class="instruction">
        <h2>正式测试</h2>
        <p v-if="!isJuniorHighLevel">好的，现在我们来多做一些。都准备好了吗？</p>
        <p v-else>练习完成！现在开始正式测试。请认真阅读每道题目，准确作答。</p>
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
        
        <!-- 显示图片（如果有） -->
        <div v-if="currentFormalTrial.image_path" class="question-image">
          <img :src="getImageUrl(currentFormalTrial.image_path)" :alt="'题目图片'" @error="onImageError" />
        </div>
        
        <div class="sentence">{{ getQuestionText(currentFormalTrial) }}</div>
        
        <!-- 判断题界面 -->
        <div v-if="currentFormalTrial.question_type === '判断'">
          <div class="answer">
            <span class="answer-label">（</span>
            <span class="answer-mark" ref="answerMark"></span>
            <span class="answer-label">）</span>
          </div>
          <div class="answer-buttons">
            <button class="answer-btn correct-btn" :class="{ 'selected': userAnswer === 'true' }" @click="handleAnswer('true')">
              正确 (√)
            </button>
            <button class="answer-btn wrong-btn" :class="{ 'selected': userAnswer === 'false' }" @click="handleAnswer('false')">
              错误 (╳)
            </button>
          </div>
        </div>
        
        <!-- 选择题界面 -->
        <div v-else-if="currentFormalTrial.question_type === '选择'" class="choice-question">
          <div class="choice-options">
            <button 
              v-for="(option, index) in currentFormalTrial.options" 
              :key="index"
              class="choice-btn"
              :class="{ 'selected': userAnswer === getOptionLabel(index) }"
              @click="handleAnswer(getOptionLabel(index))"
            >
              <span class="option-label">{{ getOptionLabel(index) }}.</span>
              <span class="option-text">{{ option }}</span>
            </button>
          </div>
        </div>
        
        <!-- 兜底：旧版本判断题界面 -->
        <div v-else>
          <div class="answer">
            <span class="answer-label">（</span>
            <span class="answer-mark" ref="answerMark"></span>
            <span class="answer-label">）</span>
          </div>
          <div class="answer-buttons">
            <button class="answer-btn correct-btn" :class="{ 'selected': userAnswer === 'true' }" @click="handleAnswer('true')">
              正确 (√)
            </button>
            <button class="answer-btn wrong-btn" :class="{ 'selected': userAnswer === 'false' }" @click="handleAnswer('false')">
              错误 (╳)
            </button>
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

      <!-- 实验结束 -->
      <div v-else-if="phase === 'end'" class="experiment-end">
        <h2>实验结束</h2>
        <p>感谢你的参与！</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { ElMessage } from 'element-plus';

// 状态变量
const phase = ref('level-selection'); // 实验阶段: level-selection, welcome, practice-intro, practice, formal-intro, formal, end
const selectedLevel = ref('elementary'); // 选择的级别
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
const isJuniorHighLevel = computed(() => selectedLevel.value === 'junior_high');

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
        total_questions: formalTrials.value.length,
        level: selectedLevel.value
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
        user_answer: String(trialData.user_answer),  // 确保是字符串
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

  const currentTrial = phase.value === 'practice' ? currentPracticeTrial.value : currentFormalTrial.value;
  
  // 根据题目类型处理按键
  if (currentTrial.question_type === '选择') {
    // 选择题：A/B/C/D 键
    const key = e.key.toLowerCase();
    if (['a', 'b', 'c', 'd'].includes(key)) {
      handleAnswer(key.toUpperCase());
    }
  } else {
    // 判断题：Q/W 键
    if (e.key.toLowerCase() === 'q') {
      handleAnswer('true');
    } else if (e.key.toLowerCase() === 'w') {
      handleAnswer('false');
    }
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
    // 获取用户信息并根据年级自动确定级别
    const userInfoStr = localStorage.getItem('userInfo');
    let apiUrl = `/api/reading-fluency/trials?level=${selectedLevel.value}`;
    
    if (userInfoStr) {
      try {
        const userInfo = JSON.parse(userInfoStr);
        if (userInfo.grade) {
          // 使用年级参数让后端自动确定级别
          apiUrl = `/api/reading-fluency/trials?grade=${userInfo.grade}`;
        }
      } catch (error) {
        console.warn('解析用户信息失败，使用默认级别');
      }
    }
    
    const response = await fetch(apiUrl);
    if (response.ok) {
      const data = await response.json();
      
      // 从响应中获取实际的级别
      const actualLevel = data.level || selectedLevel.value;
      selectedLevel.value = actualLevel;
      
      if (actualLevel === 'junior_high') {
        // 初中及以上级别，使用新格式
        formalTrials.value = data.questions.map((question) => ({
          id: question.id,
          question_type: question.question_type,
          text: question.text,
          image_path: question.image_path,
          options: question.options,
          correct_answer: question.correct_answer,
          startTime: 0,
          responseTime: 0,
          userAnswer: null
        }));
      } else {
        // 小学级别，使用旧格式
        formalTrials.value = data.formalTrials.map((trial, index) => ({
          id: index + 1,
          question_type: '判断',
          text: trial,
          startTime: 0,
          responseTime: 0,
          userAnswer: null
        }));
      }
      
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
const handleAnswer = (answer) => {
  if (isProcessing.value) return;

  isProcessing.value = true;
  userAnswer.value = answer;

  // 计算反应时间（毫秒）
  const responseTime = Date.now() - trialStartTime;

  const currentTrial = phase.value === 'practice' ? currentPracticeTrial.value : currentFormalTrial.value;
  
  // 更新答案标记（仅对判断题）
  if (currentTrial.question_type === '判断' || !currentTrial.question_type) {
    const markEl = answerMark.value;
    if (markEl) {
      const isCorrect = answer === 'true';
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
  }

  // 保存数据（如果在正式阶段）
  if (phase.value === 'formal') {
    const currentTrial = formalTrials.value[currentFormalIndex.value];
    if (currentTrial) {
      currentTrial.userAnswer = answer;
      currentTrial.responseTime = responseTime;

      // 保存到服务器
      saveTrialWithSession({
        trial_id: currentTrial.id,
        user_answer: answer,
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
      // 初中及以上级别直接跳到正式测试
      if (isJuniorHighLevel.value) {
        phase.value = 'formal-intro';
      } else {
        phase.value = 'practice-intro';
      }
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

// 选择测试级别
const selectLevel = async (level) => {
  selectedLevel.value = level;
  phase.value = 'welcome';
  
  // 根据选择的级别获取相应的题目
  await fetchTrials();
};

// 获取图片URL
const getImageUrl = (imagePath) => {
  if (!imagePath) return '';
  // 如果是相对路径，添加前缀
  if (imagePath.startsWith('images/')) {
    return `/${imagePath}`;
  }
  return imagePath;
};

// 图片加载错误处理
const onImageError = (event) => {
  console.warn('图片加载失败:', event.target.src);
  event.target.style.display = 'none';
};

// 获取题目文本
const getQuestionText = (trial) => {
  if (isJuniorHighLevel.value) {
    return trial.text;
  } else {
    return trial.text.split('（')[0];
  }
};

// 获取选项标签
const getOptionLabel = (index) => {
  return String.fromCharCode(65 + index); // A, B, C, D
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

  // 确保初始滚动位置在页面顶部
  window.scrollTo(0, 0);
  
  // 检查用户信息，如果有用户信息则自动开始实验
  const userInfoStr = localStorage.getItem('userInfo');
  if (userInfoStr) {
    try {
      const userInfo = JSON.parse(userInfoStr);
      if (userInfo.grade) {
        // 跳过级别选择，直接开始实验
        await autoStartExperiment();
      }
    } catch (error) {
      console.warn('解析用户信息失败，显示级别选择');
    }
  }
});

// 自动开始实验（基于用户年级）
const autoStartExperiment = async () => {
  try {
    // 获取题目数据
    await fetchTrials();
    
    // 直接进入欢迎页面
    phase.value = 'welcome';
  } catch (error) {
    console.error('自动开始实验失败:', error);
    // 如果失败，回退到级别选择
    phase.value = 'level-selection';
  }
};

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
.experiment-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
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

/* 级别选择 */
.level-selection {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
  padding: 40px 20px;
}

.level-selection h2 {
  color: #409EFF;
  margin-bottom: 20px;
  font-size: 28px;
}

.level-selection p {
  margin: 20px 0;
  font-size: 16px;
  color: #606266;
}

.level-buttons {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-top: 30px;
}

.level-buttons .el-button {
  padding: 15px 30px;
  font-size: 16px;
  min-width: 150px;
}

/* 题目图片 */
.question-image {
  margin: 20px 0;
  text-align: center;
}

.question-image img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 选择题样式 */
.choice-question {
  width: 100%;
  margin: 20px 0;
}

.choice-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 20px;
}

.choice-btn {
  display: flex;
  align-items: flex-start;
  padding: 15px 20px;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  background-color: #fff;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
  width: 100%;
  min-height: 60px;
}

.choice-btn:hover {
  border-color: #409EFF;
  background-color: #f5f7fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.choice-btn.selected {
  border-color: #409EFF;
  background-color: #ecf5ff;
  color: #409EFF;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.25);
}

.option-label {
  font-weight: bold;
  font-size: 16px;
  margin-right: 10px;
  flex-shrink: 0;
  color: #409EFF;
}

.option-text {
  flex: 1;
  line-height: 1.5;
  font-size: 15px;
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