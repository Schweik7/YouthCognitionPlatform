<template>
  <div class="experiment-container">
    <div id="jspsych-target"></div>
    
    <!-- 调试面板 - 默认隐藏 -->
    <el-dialog v-model="debugMode" title="调试模式" width="50%">
      <el-form>
        <el-form-item label="跳转到题号">
          <el-input-number v-model="jumpToTrial" :min="1" :max="maxTrials"></el-input-number>
          <el-button type="primary" @click="jumpToTrialNumber">跳转</el-button>
        </el-form-item>
        <el-form-item label="剩余时间">
          <el-input-number v-model="remainingTime" :min="0" :max="180"></el-input-number>
          <el-button type="primary" @click="updateTimer">更新</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { initJsPsych } from 'jspsych';
import htmlKeyboardResponse from '@jspsych/plugin-html-keyboard-response';
import htmlButtonResponse from '@jspsych/plugin-html-button-response';
import { ElMessage } from 'element-plus';

// 调试模式状态
const debugMode = ref(false);
const jumpToTrial = ref(1);
const maxTrials = ref(100);
const remainingTime = ref(180);
let jsPsych = null;
let experimentStarted = false;
let intervalId = null;
let currentTrialIndex = 0;

// 教学阶段试题数据
const practiceTrials = [
  { id: 1, text: "太阳从西边升起。（      ）", correct: false, demonstrated: true },
  { id: 2, text: "燕子会飞。（       ）", correct: true, demonstrated: false },
  { id: 3, text: "写字要用手。（       ）", correct: true, demonstrated: false }
];

// 正式阶段试题数据（初始为空，将从后端获取）
const formalTrials = ref([]);

// 键盘监听函数，用于调试模式
const keyHandler = (e) => {
  // 检测是否同时按下【】键
  if ((e.key === '[' && e.altKey) || (e.key === ']' && e.altKey)) {
    debugMode.value = !debugMode.value;
  }
};

// 更新计时器
const updateTimer = () => {
  if (window.timerValue !== undefined) {
    window.timerValue = remainingTime.value;
  }
};

// 跳转到指定题号
const jumpToTrialNumber = () => {
  if (jsPsych && experimentStarted) {
    const targetIndex = jumpToTrial.value - 1 + practiceTrials.length + 3; // 加上指导语和练习题的数量
    jsPsych.endCurrentTimeline();
    jsPsych.resumeExperiment();
    currentTrialIndex = jumpToTrial.value - 1;
  }
};

// 创建计时器组件
const createTimerComponent = () => {
  // 设置全局计时器值
  window.timerValue = 180; // 3分钟
  
  const timerHtml = `
    <div class="timer-container">
      <div class="timer">
        <span id="timer-minutes">03</span>:<span id="timer-seconds">00</span>
      </div>
      <div class="hourglass-container">
        <div class="hourglass">
          <div class="hourglass-top"></div>
          <div class="hourglass-bottom"></div>
        </div>
      </div>
    </div>
  `;

  const updateTimerDisplay = () => {
    if (window.timerValue <= 0) {
      clearInterval(intervalId);
      jsPsych.endExperiment('<div class="experiment-end"><h2>实验结束</h2><p>感谢你的参与！</p></div>');
      return;
    }

    const minutes = Math.floor(window.timerValue / 60);
    const seconds = window.timerValue % 60;
    const minutesDisplay = String(minutes).padStart(2, '0');
    const secondsDisplay = String(seconds).padStart(2, '0');

    const minutesEl = document.getElementById('timer-minutes');
    const secondsEl = document.getElementById('timer-seconds');
    
    if (minutesEl && secondsEl) {
      minutesEl.textContent = minutesDisplay;
      secondsEl.textContent = secondsDisplay;
    }
    
    window.timerValue--;
  };

  return {
    type: htmlKeyboardResponse,
    stimulus: timerHtml,
    choices: "NO_KEYS",
    trial_duration: 0,
    data: {
      phase: 'timer'
    },
    version: '1.0.0',
    on_start: () => {
      // 启动计时器
      intervalId = setInterval(updateTimerDisplay, 1000);
    }
  };
};

// 创建实验指导语试验
const createInstructionTrials = () => {
  const welcomeHtml = `
    <div class="instruction">
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
      <div class="continue-btn">点击下一步继续</div>
    </div>
  `;

  const practiceInstructionHtml = `
    <div class="instruction">
      <h2>练习阶段</h2>
      <p>我们先来练习几道题，看你有没有明白，好吗？</p>
      <div class="continue-btn">点击下一步开始练习</div>
    </div>
  `;

  const formalInstructionHtml = `
    <div class="instruction">
      <h2>正式测验</h2>
      <p>好的，现在我们来多做一些。都准备好了吗？</p>
      <p>准备好后，点击"开始"按钮，计时将立即开始！</p>
      <div class="continue-btn">开始</div>
    </div>
  `;

  return [
    {
      type: htmlButtonResponse,
      stimulus: welcomeHtml,
      choices: ['下一步'],
      button_html: ['<button class="jspsych-btn">%choice%</button>'],
      data: {
        phase: 'instruction'
      },
      version: '1.0.0'
    },
    {
      type: htmlButtonResponse,
      stimulus: practiceInstructionHtml,
      choices: ['开始练习'],
      button_html: ['<button class="jspsych-btn">%choice%</button>'],
      data: {
        phase: 'practice-instruction'
      },
      version: '1.0.0'
    },
    // 练习题在此之后添加
    {
      type: htmlButtonResponse,
      stimulus: formalInstructionHtml,
      choices: ['开始'],
      button_html: ['<button class="jspsych-btn primary-btn">%choice%</button>'],
      data: {
        phase: 'formal-instruction'
      },
      version: '1.0.0',
      on_finish: () => {
        experimentStarted = true;
      }
    }
  ];
};

// 创建练习阶段试验
const createPracticeTrials = () => {
  const practiceTrialsList = [];

  practiceTrials.forEach((trial, index) => {
    let stimulus;
    
    if (trial.demonstrated) {
      // 第一个演示题，自动显示结果
      stimulus = `
        <div class="trial-container">
          <div class="sentence">${trial.text.replace('（      ）', '')}</div>
          <div class="answer">
            <span class="answer-label">（</span>
            <span class="answer-mark">╳</span>
            <span class="answer-label">）</span>
          </div>
          <div class="explanation">
            <p>第${trial.id}题："${trial.text.replace('（      ）', '')}"对还是错？这是错的。</p>
            <p>（自动打个"╳"）</p>
          </div>
        </div>
      `;
      
      practiceTrialsList.push({
        type: htmlButtonResponse,
        stimulus: stimulus,
        choices: ['下一题'],
        button_html: ['<button class="jspsych-btn">%choice%</button>'],
        data: {
          phase: 'practice',
          trial_id: trial.id,
          demonstrated: true
        },
        version: '1.0.0'
      });
    } else {
      // 由用户自己完成的练习题
      stimulus = `
        <div class="trial-container">
          <div class="sentence">${trial.text.replace('（       ）', '')}</div>
          <div class="answer">
            <span class="answer-label">（</span>
            <span class="answer-mark" id="answer-mark"></span>
            <span class="answer-label">）</span>
          </div>
          <div class="instruction">
            <p>请判断这个句子是正确的还是错误的：</p>
            <div class="key-guide">
              <div>按 Q 键 = 正确（√）</div>
              <div>按 W 键 = 错误（╳）</div>
            </div>
          </div>
        </div>
      `;
      
      practiceTrialsList.push({
        type: htmlKeyboardResponse,
        stimulus: stimulus,
        choices: ['q', 'w'],
        data: {
          phase: 'practice',
          trial_id: trial.id,
          demonstrated: false
        },
        version: '1.0.0',
        on_load: () => {
          // 添加按键响应处理
          document.addEventListener('keydown', (e) => {
            const answerMark = document.getElementById('answer-mark');
            if (!answerMark) return;

            if (e.key.toLowerCase() === 'q') {
              answerMark.textContent = '√';
              answerMark.classList.add('correct-mark');
            } else if (e.key.toLowerCase() === 'w') {
              answerMark.textContent = '╳';
              answerMark.classList.add('wrong-mark');
            }
          }, { once: true });
        },
        on_finish: (data) => {
          // 记录用户的响应
          if (data.response === 'q') {
            data.user_answer = true;
          } else if (data.response === 'w') {
            data.user_answer = false;
          }
          
          data.correct = data.user_answer === trial.correct;
        }
      });
    }
  });

  return practiceTrialsList;
};

// 创建正式阶段试验
const createFormalTrials = () => {
  if (!formalTrials.value.length) return [];
  
  const formalTrialsList = [];
  
  // 添加计时器试验（在正式阶段开始时）
  formalTrialsList.push(createTimerComponent());
  
  // 添加每个正式题目
  formalTrials.value.forEach((trial, index) => {
    const stimulus = `
      <div class="trial-container formal-trial">
        <div class="trial-header">
          <div class="trial-number">第 ${trial.id} 题</div>
          <div class="timer">
            <span id="timer-minutes">03</span>:<span id="timer-seconds">00</span>
          </div>
        </div>
        <div class="sentence">${trial.text.split('（')[0]}</div>
        <div class="answer">
          <span class="answer-label">（</span>
          <span class="answer-mark" id="answer-mark-${trial.id}"></span>
          <span class="answer-label">）</span>
        </div>
      </div>
    `;
    
    formalTrialsList.push({
      type: htmlKeyboardResponse,
      stimulus: stimulus,
      choices: ['q', 'w'],
      data: {
        trial_id: trial.id,
        trial_type: 'formal',
        sentence: trial.text,
        phase: 'formal'
      },
      version: '1.0.0',
      on_load: () => {
        // 更新当前试验索引
        currentTrialIndex = index;
        
        // 添加按键响应处理
        const handleKeyDown = (e) => {
          const answerMark = document.getElementById(`answer-mark-${trial.id}`);
          if (!answerMark) return;

          if (e.key.toLowerCase() === 'q') {
            answerMark.textContent = '√';
            answerMark.classList.add('correct-mark');
            // 自动进入下一题
            setTimeout(() => {
              jsPsych.finishTrial();
            }, 300);
          } else if (e.key.toLowerCase() === 'w') {
            answerMark.textContent = '╳';
            answerMark.classList.add('wrong-mark');
            // 自动进入下一题
            setTimeout(() => {
              jsPsych.finishTrial();
            }, 300);
          }
        };
        
        document.addEventListener('keydown', handleKeyDown);
        
        // 清理函数
        return () => {
          document.removeEventListener('keydown', handleKeyDown);
        };
      },
      on_finish: (data) => {
        if (data.response === 'q') {
          data.user_answer = true; // 正确
        } else if (data.response === 'w') {
          data.user_answer = false; // 错误
        }
        
        // 保存试验数据到服务器
        saveTrialData({
          trial_id: trial.id,
          user_answer: data.user_answer,
          response_time: data.rt
        });
      }
    });
  });
  
  return formalTrialsList;
};

// 保存试验数据到服务器
const saveTrialData = async (trialData) => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
  
  try {
    await fetch('/api/save-trial', {
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
  } catch (error) {
    console.error('保存数据失败:', error);
  }
};

// 获取试验数据
const fetchTrials = async () => {
  try {
    const response = await fetch('/api/trials');
    if (response.ok) {
      const data = await response.json();
      formalTrials.value = data.formalTrials.map((trial, index) => ({
        id: index + 1,
        text: trial
      }));
      maxTrials.value = formalTrials.value.length;
    } else {
      // 如果API请求失败，使用本地数据（从上传的CSV文件解析）
      parseLocalTrials();
    }
  } catch (error) {
    console.error('获取试验数据失败:', error);
    // 解析本地试验数据
    parseLocalTrials();
  }
};

// 解析本地试验数据（从上传的文件）
const parseLocalTrials = () => {
  // 使用服务器中上传的CSV文件的硬编码样例
  // 注意：这只是在API请求失败时的备用方案
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
    text: trial
  }));
  
  maxTrials.value = formalTrials.value.length;
  
  console.warn('使用备用试题数据，请检查API连接');
};

// 初始化jsPsych并运行实验
const initializeExperiment = () => {
  // 初始化jsPsych
  jsPsych = initJsPsych({
    display_element: 'jspsych-target',
    on_finish: () => {
      // 实验结束时的处理
      clearInterval(intervalId);
      ElMessage.success('实验已完成，感谢您的参与！');
    }
  });
  
  // 合并所有试验
  const timeline = [
    ...createInstructionTrials(),
    ...createPracticeTrials(),
    ...createFormalTrials()
  ];
  
  // 运行jsPsych
  jsPsych.run(timeline);
};

// 生命周期钩子
onMounted(async () => {
  // 添加键盘事件监听器（用于调试模式）
  window.addEventListener('keydown', keyHandler);
  
  // 获取试验数据
  await fetchTrials();
  
  // 初始化实验
  initializeExperiment();
});

onUnmounted(() => {
  // 清理资源
  window.removeEventListener('keydown', keyHandler);
  clearInterval(intervalId);
});
</script>

<style scoped>
.experiment-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}

/* 添加jsPsych自定义样式 */
:deep(.jspsych-content) {
  max-width: 800px;
}

:deep(.jspsych-btn) {
  padding: 10px 20px;
  font-size: 16px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  margin: 10px;
}

:deep(.primary-btn) {
  background-color: #409EFF;
  color: white;
  font-weight: bold;
}

:deep(.instruction) {
  max-width: 700px;
  margin: 0 auto;
  text-align: left;
  line-height: 1.6;
}

:deep(.instruction h2) {
  text-align: center;
  color: #409EFF;
  margin-bottom: 20px;
}

:deep(.key-instruction) {
  margin: 20px 0;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-weight: bold;
}

:deep(.continue-btn) {
  margin: 20px auto;
  text-align: center;
  padding: 10px 0;
  font-weight: bold;
  color: #409EFF;
}

:deep(.trial-container) {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 700px;
  margin: 0 auto;
  padding: 20px;
}

:deep(.trial-header) {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 20px;
}

:deep(.trial-number) {
  font-weight: bold;
  font-size: 18px;
}

:deep(.sentence) {
  font-size: 20px;
  line-height: 1.5;
  margin: 20px 0;
  text-align: center;
}

:deep(.answer) {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 15px 0;
}

:deep(.answer-label) {
  font-size: 24px;
  padding: 0 5px;
}

:deep(.answer-mark) {
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  font-weight: bold;
}

:deep(.correct-mark) {
  color: #67C23A;
}

:deep(.wrong-mark) {
  color: #F56C6C;
}

:deep(.explanation) {
  background-color: #f0f7ff;
  padding: 15px;
  border-radius: 4px;
  margin: 20px 0;
  width: 100%;
}

:deep(.instruction) {
  margin: 20px 0;
  line-height: 1.6;
}

:deep(.key-guide) {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}

:deep(.timer-container) {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

:deep(.timer) {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  background-color: white;
  padding: 10px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  align-items: center;
}

:deep(.hourglass-container) {
  margin-top: 10px;
  display: flex;
  justify-content: center;
}

:deep(.hourglass) {
  position: relative;
  width: 30px;
  height: 50px;
}

:deep(.hourglass-top) {
  position: absolute;
  top: 0;
  width: 30px;
  height: 25px;
  background-color: #409EFF;
  clip-path: polygon(0 0, 100% 0, 50% 100%, 0 0);
  animation: drainSand 180s linear forwards;
}

:deep(.hourglass-bottom) {
  position: absolute;
  bottom: 0;
  width: 30px;
  height: 25px;
  background-color: #E6E6E6;
  clip-path: polygon(0 100%, 100% 100%, 50% 0, 0 100%);
  animation: fillSand 180s linear forwards;
}

@keyframes drainSand {
  from { height: 25px; }
  to { height: 0; }
}

@keyframes fillSand {
  from { 
    height: 0; 
    background-color: #E6E6E6;
  }
  to { 
    height: 25px; 
    background-color: #409EFF;
  }
}

:deep(.experiment-end) {
  text-align: center;
  padding: 40px;
}

:deep(.experiment-end h2) {
  color: #409EFF;
  margin-bottom: 20px;
}
</style>