// 标记为正确的辅助函数
const markAsCorrect = (answerMark, trialId) => {
  answerMark.textContent = '√';
  answerMark.classList.remove('wrong-mark'); // 先移除可能存在的错误标记
  answerMark.classList.add('correct-mark');
  answerMark.classList.remove('answer-animation'); // 先移除以确保动画重新触发
  setTimeout(() => {
    answerMark.classList.add('answer-animation');
  }, 10);
  
  // 高亮正确按钮
  const correctBtn = document.getElementById(`correct-btn-${trialId}`);
  if (correctBtn) {
    correctBtn.classList.add('selected');
  }
  
  // 自动进入下一题
  setTimeout(() => {
    keyProcessing.value = false;
    if (jsPsych && typeof jsPsych.finishTrial === 'function') {
      jsPsych.finishTrial();
    }
  }, 500); // 延长动画时间
};

// 标记为错误的辅助函数
const markAsWrong = (answerMark, trialId) => {
  answerMark.textContent = '╳';
  answerMark.classList.remove('correct-mark'); // 先移除可能存在的正确标记
  answerMark.classList.add('wrong-mark');
  answerMark.classList.remove('answer-animation'); // 先移除以确保动画重新触发
  setTimeout(() => {
    answerMark.classList.add('answer-animation');
  }, 10);
  
  // 高亮错误按钮
  const wrongBtn = document.getElementById(`wrong-btn-${trialId}`);
  if (wrongBtn) {
    wrongBtn.classList.add('selected');
  }
  
  // 自动进入下一题
  setTimeout(() => {
    keyProcessing.value = false;
    if (jsPsych && typeof jsPsych.finishTrial === 'function') {
      jsPsych.finishTrial();
    }
  }, 500); // 延长动画时间
};

// 教学阶段使用的正确标记函数
const practiceMarkAsCorrect = (answerMark) => {
  answerMark.textContent = '√';
  answerMark.classList.remove('wrong-mark'); // 先移除错误标记
  answerMark.classList.add('correct-mark');
  answerMark.classList.remove('answer-animation'); // 先移除以确保动画重新触发
  setTimeout(() => {
    answerMark.classList.add('answer-animation');
  }, 10);
  
  setTimeout(() => {
    keyProcessing.value = false;
  }, 300);
};

// 教学阶段使用的错误标记函数
const practiceMarkAsWrong = (answerMark) => {
  answerMark.textContent = '╳';
  answerMark.classList.remove('correct-mark'); // 先移除正确标记
  answerMark.classList.add('wrong-mark');
  answerMark.classList.remove('answer-animation'); // 先移除以确保动画重新触发
  setTimeout(() => {
    answerMark.classList.add('answer-animation');
  }, 10);
  
  setTimeout(() => {
    keyProcessing.value = false;
  }, 300);
};<template>
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
// 添加防抖变量
const keyProcessing = ref(false);

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
    try {
      // 尝试使用可用的方法
      if (typeof jsPsych.endCurrentTimeline === 'function') {
        jsPsych.endCurrentTimeline();
      } else if (typeof jsPsych.finishTrial === 'function') {
        // 多次调用finishTrial来跳过当前试验
        for (let i = 0; i < 5; i++) {
          jsPsych.finishTrial();
        }
      }
      
      if (typeof jsPsych.resumeExperiment === 'function') {
        jsPsych.resumeExperiment();
      }
      
      currentTrialIndex = jumpToTrial.value - 1;
      console.log(`跳转到题号: ${jumpToTrial.value}`);
    } catch (error) {
      console.error('跳转题目时出错:', error);
      ElMessage.error('跳转失败，请尝试其他方法');
    }
  } else {
    ElMessage.warning('实验尚未开始，无法跳转');
  }
};

// 创建计时器组件
const createTimerComponent = () => {
  // 设置全局计时器值
  window.timerValue = 180; // 3分钟
  window.timerStarted = false; // 跟踪计时器是否已启动
  
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
      
      // 使用正确的方法结束实验
      try {
        // 尝试使用可用的方法结束实验
        if (jsPsych && typeof jsPsych.endExperiment === 'function') {
          jsPsych.endExperiment('<div class="experiment-end"><h2>实验结束</h2><p>感谢你的参与！</p></div>');
        } else {
          // 显示结束信息
          const jspsychTarget = document.getElementById('jspsych-target');
          if (jspsychTarget) {
            jspsychTarget.innerHTML = '<div class="experiment-end"><h2>实验结束</h2><p>感谢你的参与！</p></div>';
          }
          // 尝试使用finishTrial
          if (jsPsych && typeof jsPsych.finishTrial === 'function') {
            jsPsych.finishTrial();
          }
        }
      } catch (error) {
        console.error('结束实验时出错:', error);
        // 确保实验结束信息显示
        const jspsychTarget = document.getElementById('jspsych-target');
        if (jspsychTarget) {
          jspsychTarget.innerHTML = '<div class="experiment-end"><h2>实验结束</h2><p>感谢你的参与！</p></div>';
        }
      }
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
      // 防止重复启动计时器
      if (!window.timerStarted) {
        window.timerStarted = true;
        // 启动计时器
        intervalId = setInterval(updateTimerDisplay, 1000);
        // 立即更新一次显示
        updateTimerDisplay();
      }
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
      <p style="margin-top:15px">你也可以直接点击屏幕上的"正确"或"错误"按钮来回答。</p>
    </div>
  `;

  const practiceInstructionHtml = `
    <div class="instruction">
      <h2>练习阶段</h2>
      <p>我们先来练习几道题，看你有没有明白，好吗？</p>
    </div>
  `;

  const formalInstructionHtml = `
    <div class="instruction">
      <h2>正式测验</h2>
      <p>好的，现在我们来多做一些。都准备好了吗？</p>
      <p>准备好后，点击"开始"按钮，计时将立即开始！</p>
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
          <div class="answer-buttons">
            <button class="answer-btn correct-btn" id="practice-correct-btn">正确 (√)</button>
            <button class="answer-btn wrong-btn" id="practice-wrong-btn">错误 (╳)</button>
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
          const handleKeyDown = (e) => {
            // 防抖处理
            if (keyProcessing.value) return;
            keyProcessing.value = true;
            
            const answerMark = document.getElementById('answer-mark');
            if (!answerMark) return;

            if (e.key.toLowerCase() === 'q') {
              practiceMarkAsCorrect(answerMark);
            } else if (e.key.toLowerCase() === 'w') {
              practiceMarkAsWrong(answerMark);
            } else {
              keyProcessing.value = false;
            }
          };
          
          // 添加鼠标点击支持
          const correctBtn = document.getElementById('practice-correct-btn');
          const wrongBtn = document.getElementById('practice-wrong-btn');
          const answerMark = document.getElementById('answer-mark');
          
          // 正确按钮处理函数
          const handleCorrectClick = () => {
            console.log("正确按钮点击");
            if (keyProcessing.value) return;
            keyProcessing.value = true;
            if (answerMark) {
              practiceMarkAsCorrect(answerMark);
              if (correctBtn) correctBtn.classList.add('selected');
              if (wrongBtn) wrongBtn.classList.remove('selected');
            }
          };
          
          // 错误按钮处理函数
          const handleWrongClick = () => {
            console.log("错误按钮点击");
            if (keyProcessing.value) return;
            keyProcessing.value = true;
            if (answerMark) {
              practiceMarkAsWrong(answerMark);
              if (wrongBtn) wrongBtn.classList.add('selected');
              if (correctBtn) correctBtn.classList.remove('selected');
            }
          };
          
          if (correctBtn) {
            correctBtn.onclick = handleCorrectClick;
            correctBtn.classList.add('btn-hover-enabled');
          }
          
          if (wrongBtn) {
            wrongBtn.onclick = handleWrongClick;
            wrongBtn.classList.add('btn-hover-enabled');
          }
          
          document.addEventListener('keydown', handleKeyDown);
          
          // 返回清理函数
          return () => {
            document.removeEventListener('keydown', handleKeyDown);
            if (correctBtn) correctBtn.onclick = null;
            if (wrongBtn) wrongBtn.onclick = null;
          };
        },
        on_finish: (data) => {
          // 记录用户的响应
          if (data.response === 'q') {
            data.user_answer = true;
          } else if (data.response === 'w') {
            data.user_answer = false;
          } else {
            // 如果没有响应，设置默认值
            data.user_answer = false;
          }
          
          data.correct = data.user_answer === trial.correct;
          
          // 记录练习题结果但不保存到服务器
          console.log(`练习题 ${trial.id} 完成:`, {
            response: data.response,
            user_answer: data.user_answer,
            correct: data.correct,
            rt: data.rt || 0
          });
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
          <div class="trial-timer">
            <span id="timer-minutes">03</span>:<span id="timer-seconds">00</span>
          </div>
        </div>
        <div class="sentence">${trial.text.split('（')[0]}</div>
        <div class="answer">
          <span class="answer-label">（</span>
          <span class="answer-mark" id="answer-mark-${trial.id}"></span>
          <span class="answer-label">）</span>
        </div>
        <div class="answer-buttons">
          <button class="answer-btn correct-btn" id="correct-btn-${trial.id}">正确 (√)</button>
          <button class="answer-btn wrong-btn" id="wrong-btn-${trial.id}">错误 (╳)</button>
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
          // 按键防抖
          if (keyProcessing.value) return;
          keyProcessing.value = true;
          
          const answerMark = document.getElementById(`answer-mark-${trial.id}`);
          if (!answerMark) return;

          if (e.key.toLowerCase() === 'q') {
            answerMark.textContent = '√';
            answerMark.classList.add('correct-mark');
            // 自动进入下一题
            setTimeout(() => {
              keyProcessing.value = false;
              jsPsych.finishTrial();
            }, 300);
          } else if (e.key.toLowerCase() === 'w') {
            answerMark.textContent = '╳';
            answerMark.classList.add('wrong-mark');
            // 自动进入下一题
            setTimeout(() => {
              keyProcessing.value = false;
              jsPsych.finishTrial();
            }, 300);
          } else {
            keyProcessing.value = false;
          }
        };
        
        document.addEventListener('keydown', handleKeyDown);
        
        // 清理函数
        return () => {
          document.removeEventListener('keydown', handleKeyDown);
          this.keyProcessing = false;
        };
      },
      on_finish: (data) => {
        // 记录用户的响应
        if (data.response === 'q') {
          data.user_answer = true; // 正确
        } else if (data.response === 'w') {
          data.user_answer = false; // 错误
        } else {
          // 如果没有响应，设置默认值避免验证错误
          data.user_answer = false;
          data.rt = data.rt || 0; // 确保有响应时间，即使用户没有响应
        }
        
        // 保存试验数据到服务器
        saveTrialData({
          trial_id: trial.id,
          user_answer: data.user_answer,
          response_time: data.rt || 0
        });
      }
    });
  });
  
  return formalTrialsList;
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
  if (!userInfo.name || !userInfo.school || !userInfo.grade || !userInfo.classNumber) {
    console.error('saveTrialData: 用户信息不完整', userInfo);
    return; // 如果用户信息不完整，不继续保存
  }
  
  try {
    const response = await fetch('/api/save-trial', {
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
    },
    use_webaudio: false, // 禁用Web Audio以防止在某些浏览器中出现问题
    exclusions: {
      min_width: 300, // 最小屏幕宽度
      min_height: 300 // 最小屏幕高度
    },
    show_progress_bar: false,
    auto_update_progress_bar: false,
    default_iti: 0 // 默认试验间隔
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
  align-items: center;
}

:deep(.trial-number) {
  font-weight: bold;
  font-size: 18px;
}

:deep(.trial-timer) {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
  background-color: white;
  padding: 5px 10px;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
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

:deep(.answer-animation) {
  animation: pop-in 0.3s ease;
}

@keyframes pop-in {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.2); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}

:deep(.answer-buttons) {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
}

:deep(.answer-btn) {
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

:deep(.answer-btn::after) {
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

:deep(.answer-btn:active::after) {
  transform: scale(0, 0);
  opacity: 0.1;
  transition: 0s;
}

:deep(.btn-hover-enabled:hover) {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.correct-btn) {
  color: #67C23A;
  border-color: #c2e7b0;
}

:deep(.correct-btn:hover) {
  background-color: #f0f9eb;
  border-color: #85ce61;
}

:deep(.wrong-btn) {
  color: #F56C6C;
  border-color: #fbc4c4;
}

:deep(.wrong-btn:hover) {
  background-color: #fef0f0;
  border-color: #f78989;
}

:deep(.correct-btn.selected) {
  background-color: #f0f9eb;
  color: #67C23A;
  border-color: #67C23A;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.2);
}

:deep(.wrong-btn.selected) {
  background-color: #fef0f0;
  color: #F56C6C;
  border-color: #F56C6C;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.2);
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