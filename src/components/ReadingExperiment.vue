<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
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

// 全局变量，跟踪当前活动试验ID
let currentTrialId = null;
let trialTransitioning = false;

/**
 * 统一的答案标记函数 - 标记为正确
 * @param {HTMLElement} answerMark - 答案标记元素
 * @param {string} trialId - 试验ID
 * @param {boolean} autoFinish - 是否自动完成试验
 */
const markAsCorrect = (answerMark, trialId, autoFinish = true) => {
  try {
    // 防止重复处理
    if (!answerMark || answerMark.textContent === '√' || trialTransitioning) {
      keyProcessing.value = false;
      return;
    }
    
    // 标记正在处理试验转换
    if (autoFinish) {
      trialTransitioning = true;
    }
    
    // 设置当前试验ID
    currentTrialId = trialId;
    
    // 更新标记和样式
    answerMark.textContent = '√';
    answerMark.classList.remove('wrong-mark');
    answerMark.classList.add('correct-mark');
    
    // 重置并触发动画
    answerMark.classList.remove('answer-animation');
    setTimeout(() => {
      answerMark.classList.add('answer-animation');
    }, 10);

    // 高亮正确按钮
    const correctBtn = document.getElementById(`correct-btn-${trialId}`);
    const wrongBtn = document.getElementById(`wrong-btn-${trialId}`);
    if (correctBtn) {
      correctBtn.classList.add('selected');
      if (wrongBtn) wrongBtn.classList.remove('selected');
    }

    // 自动进入下一题
    if (autoFinish) {
      setTimeout(() => {
        keyProcessing.value = false;
        
        // 确保仍然是当前正在处理的试验
        if (currentTrialId === trialId && jsPsych && typeof jsPsych.finishTrial === 'function') {
          // 使用一次性定时器延迟执行finishTrial，防止事件冲突
          setTimeout(() => {
            trialTransitioning = false;
            jsPsych.finishTrial();
          }, 50);
        } else {
          trialTransitioning = false;
        }
      }, 500);
    } else {
      setTimeout(() => {
        keyProcessing.value = false;
      }, 300);
    }
  } catch (error) {
    console.error('标记为正确时出错:', error);
    keyProcessing.value = false;
    trialTransitioning = false;
  }
};

/**
 * 统一的答案标记函数 - 标记为错误
 * @param {HTMLElement} answerMark - 答案标记元素
 * @param {string} trialId - 试验ID
 * @param {boolean} autoFinish - 是否自动完成试验
 */
const markAsWrong = (answerMark, trialId, autoFinish = true) => {
  try {
    // 防止重复处理
    if (!answerMark || answerMark.textContent === '╳' || trialTransitioning) {
      keyProcessing.value = false;
      return;
    }
    
    // 标记正在处理试验转换
    if (autoFinish) {
      trialTransitioning = true;
    }
    
    // 设置当前试验ID
    currentTrialId = trialId;
    
    // 更新标记和样式
    answerMark.textContent = '╳';
    answerMark.classList.remove('correct-mark');
    answerMark.classList.add('wrong-mark');
    
    // 重置并触发动画
    answerMark.classList.remove('answer-animation');
    setTimeout(() => {
      answerMark.classList.add('answer-animation');
    }, 10);

    // 高亮错误按钮
    const correctBtn = document.getElementById(`correct-btn-${trialId}`);
    const wrongBtn = document.getElementById(`wrong-btn-${trialId}`);
    if (wrongBtn) {
      wrongBtn.classList.add('selected');
      if (correctBtn) correctBtn.classList.remove('selected');
    }

    // 自动进入下一题
    if (autoFinish) {
      setTimeout(() => {
        keyProcessing.value = false;
        
        // 确保仍然是当前正在处理的试验
        if (currentTrialId === trialId && jsPsych && typeof jsPsych.finishTrial === 'function') {
          // 使用一次性定时器延迟执行finishTrial，防止事件冲突
          setTimeout(() => {
            trialTransitioning = false;
            jsPsych.finishTrial();
          }, 50);
        } else {
          trialTransitioning = false;
        }
      }, 500);
    } else {
      setTimeout(() => {
        keyProcessing.value = false;
      }, 300);
    }
  } catch (error) {
    console.error('标记为错误时出错:', error);
    keyProcessing.value = false;
    trialTransitioning = false;
  }
};

/**
 * 处理用户响应 - 统一键盘和鼠标事件
 * @param {string} response - 用户响应 ('correct' 或 'wrong')
 * @param {string} trialId - 试验ID
 * @param {boolean} autoFinish - 是否自动完成试验
 */
const handleUserResponse = (response, trialId, autoFinish = true) => {
  // 防抖处理 - 如果正在处理中或试验切换中则拒绝新操作
  if (keyProcessing.value || trialTransitioning) {
    console.log('跳过操作 - 按键处理中或试验切换中');
    return;
  }
  
  // 标记正在处理按键
  keyProcessing.value = true;
  
  // 如果当前试验ID不为空且不等于请求的trialId，忽略此操作
  if (currentTrialId !== null && currentTrialId !== trialId) {
    console.log(`跳过操作 - 试验ID不匹配: 当前=${currentTrialId}, 请求=${trialId}`);
    keyProcessing.value = false;
    return;
  }
  
  // 检查当前活动试验元素
  const activeTrialElement = document.querySelector('.jspsych-display-element .jspsych-content-wrapper');
  if (!activeTrialElement) {
    console.log('跳过操作 - 找不到活动试验元素');
    keyProcessing.value = false;
    return;
  }

  // 用tryCatch包装DOM操作，防止意外错误
  try {
    const answerMark = document.getElementById(`answer-mark-${trialId}`);
    if (!answerMark) {
      console.log(`跳过操作 - 找不到标记元素: answer-mark-${trialId}`);
      keyProcessing.value = false;
      return;
    }
    
    // 验证标记元素在当前活动试验中
    if (!activeTrialElement.contains(answerMark)) {
      console.log(`跳过操作 - 标记元素不在当前活动试验中`);
      keyProcessing.value = false;
      return;
    }

    // 更新当前处理的试验ID
    currentTrialId = trialId;
    
    // 处理用户响应
    if (response === 'correct') {
      markAsCorrect(answerMark, trialId, autoFinish);
    } else if (response === 'wrong') {
      markAsWrong(answerMark, trialId, autoFinish);
    } else {
      keyProcessing.value = false;
    }
  } catch (error) {
    console.error('处理用户响应时出错:', error);
    keyProcessing.value = false;
    trialTransitioning = false;
  }
};

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
  
  // 使用performance API跟踪实际时间
  let startTime = null;
  let lastUpdateTime = null;

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
    // 初始化开始时间（如果尚未设置）
    if (startTime === null) {
      startTime = performance.now();
      lastUpdateTime = startTime;
    }
    
    // 获取当前时间
    const currentTime = performance.now();
    
    // 根据实际经过的时间更新计时器值
    const elapsedSeconds = Math.floor((currentTime - startTime) / 1000);
    window.timerValue = Math.max(0, 180 - elapsedSeconds);
    
    // 至少过去了1秒才更新显示
    if (currentTime - lastUpdateTime >= 1000) {
      lastUpdateTime = currentTime;
      
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
    }
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
        // 高频率更新计时器，以确保平滑运行
        intervalId = setInterval(updateTimerDisplay, 100);
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
      button_html: ['<button class="jspsych-btn btn-hover-enabled">%choice%</button>'],
      data: {
        phase: 'instruction'
      },
      version: '1.0.0',
      on_load: () => {
        // 确保滚动位置在顶部
        window.scrollTo(0, 0);
      }
    },
    {
      type: htmlButtonResponse,
      stimulus: practiceInstructionHtml,
      choices: ['开始练习'],
      button_html: ['<button class="jspsych-btn btn-hover-enabled">%choice%</button>'],
      data: {
        phase: 'practice-instruction'
      },
      version: '1.0.0',
      on_load: () => {
        // 确保滚动位置在顶部
        window.scrollTo(0, 0);
      }
    },
    // 练习题在此之后添加
    {
      type: htmlButtonResponse,
      stimulus: formalInstructionHtml,
      choices: ['开始'],
      button_html: ['<button class="jspsych-btn primary-btn btn-hover-enabled">%choice%</button>'],
      data: {
        phase: 'formal-instruction'
      },
      version: '1.0.0',
      on_load: () => {
        // 确保滚动位置在顶部
        window.scrollTo(0, 0);
      },
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
            <span class="answer-mark wrong-mark answer-animation">╳</span>
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
        button_html: ['<button class="jspsych-btn btn-hover-enabled">%choice%</button>'],
        data: {
          phase: 'practice',
          trial_id: trial.id,
          demonstrated: true
        },
        version: '1.0.0',
        on_load: () => {
          // 确保滚动位置在顶部
          window.scrollTo(0, 0);
        }
      });
    } else {
      // 由用户自己完成的练习题
      stimulus = `
        <div class="trial-container">
          <div class="sentence">${trial.text.replace('（       ）', '')}</div>
          <div class="answer">
            <span class="answer-label">（</span>
            <span class="answer-mark" id="answer-mark-${trial.id}"></span>
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
            <button class="answer-btn correct-btn btn-hover-enabled" id="correct-btn-${trial.id}">正确 (√)</button>
            <button class="answer-btn wrong-btn btn-hover-enabled" id="wrong-btn-${trial.id}">错误 (╳)</button>
          </div>
        </div>
      `;

      // 增加安全检查的事件处理函数
      const safeHandleResponse = (response, trialId) => {
        const answerMark = document.getElementById(`answer-mark-${trialId}`);
        if (!answerMark) {
          console.warn(`找不到标记元素: answer-mark-${trialId}`);
          return;
        }
        handleUserResponse(response, trialId, true);
      };

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
          // 确保滚动位置在顶部
          window.scrollTo(0, 0);
          
          // 添加按键响应处理
          const handleKeyDown = (e) => {
            if (e.key.toLowerCase() === 'q') {
              safeHandleResponse('correct', trial.id);
            } else if (e.key.toLowerCase() === 'w') {
              safeHandleResponse('wrong', trial.id);
            }
          };

          document.addEventListener('keydown', handleKeyDown);

          // 添加鼠标点击支持
          const correctBtn = document.getElementById(`correct-btn-${trial.id}`);
          const wrongBtn = document.getElementById(`wrong-btn-${trial.id}`);

          if (correctBtn) {
            correctBtn.addEventListener('click', () => {
              safeHandleResponse('correct', trial.id);
            });
          }

          if (wrongBtn) {
            wrongBtn.addEventListener('click', () => {
              safeHandleResponse('wrong', trial.id);
            });
          }

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
          <button class="answer-btn correct-btn btn-hover-enabled" id="correct-btn-${trial.id}">正确 (√)</button>
          <button class="answer-btn wrong-btn btn-hover-enabled" id="wrong-btn-${trial.id}">错误 (╳)</button>
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
        // 确保滚动位置在顶部
        window.scrollTo(0, 0);
        
        // 更新当前试验状态
        currentTrialId = trial.id;
        trialTransitioning = false;
        keyProcessing.value = false;
        
        // 同步显示计时器的当前时间
        const updateCurrentTimerDisplay = () => {
          if (window.timerValue !== undefined) {
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
          }
        };

        // 立即更新一次计时器显示
        updateCurrentTimerDisplay();

        // 添加按键响应处理
        const handleKeyDown = (e) => {
          // 忽略重复触发的键盘事件（长按）
          if (e.repeat) return;
          
          // 忽略试验间切换
          if (trialTransitioning) return;
          
          // 防止事件冒泡导致多次触发
          e.stopPropagation();
          
          if (e.key.toLowerCase() === 'q') {
            handleUserResponse('correct', trial.id);
          } else if (e.key.toLowerCase() === 'w') {
            handleUserResponse('wrong', trial.id);
          }
        };

        document.addEventListener('keydown', handleKeyDown, {capture: true, once: false});

        // 添加鼠标点击事件
        const correctBtn = document.getElementById(`correct-btn-${trial.id}`);
        const wrongBtn = document.getElementById(`wrong-btn-${trial.id}`);

        if (correctBtn) {
          correctBtn.addEventListener('click', (e) => {
            // 防止事件冒泡
            e.stopPropagation();
            // 忽略试验间切换
            if (trialTransitioning) return;
            handleUserResponse('correct', trial.id);
          }, {capture: true, once: true});
        }

        if (wrongBtn) {
          wrongBtn.addEventListener('click', (e) => {
            // 防止事件冒泡
            e.stopPropagation();
            // 忽略试验间切换
            if (trialTransitioning) return;
            handleUserResponse('wrong', trial.id);
          }, {capture: true, once: true});
        }

        // 清理函数
        return () => {
          document.removeEventListener('keydown', handleKeyDown, {capture: true});
          if (correctBtn) correctBtn.onclick = null;
          if (wrongBtn) wrongBtn.onclick = null;
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
        
        // 重置试验状态
        currentTrialId = null;
      }
    });
  });

  return formalTrialsList;
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
      // 如果API请求失败，使用本地数据
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
  // 这只是在API请求失败时的备用方案
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
  // 先确保目标元素存在
  let targetElement = document.getElementById('jspsych-target');
  
  if (!targetElement) {
    console.warn('JSPsych目标元素不存在，创建一个新的元素');
    // 直接添加到body上，不依赖experiment-container
    const newTarget = document.createElement('div');
    newTarget.id = 'jspsych-target';
    newTarget.className = 'jspsych-display-element';
    document.body.appendChild(newTarget);
    targetElement = newTarget;
  }

  // 添加顶部空间占位元素，使内容显示在屏幕中央偏上
  const spacer = document.createElement('div');
  spacer.className = 'top-spacer';
  document.body.insertBefore(spacer, targetElement);

  // 确保初始滚动位置在页面顶部
  window.scrollTo(0, 0);

  try {
    // 初始化jsPsych
    jsPsych = initJsPsych({
      display_element: targetElement, // 直接传递DOM元素而非ID字符串
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
  } catch (error) {
    console.error('初始化jsPsych时出错:', error);
    ElMessage.error('实验初始化失败，请刷新页面重试');
  }
};

// 生命周期钩子
onMounted(async () => {
  console.log('组件已挂载，开始初始化实验');
  // 添加键盘事件监听器（用于调试模式）
  window.addEventListener('keydown', keyHandler);

  try {
    // 获取试验数据
    await fetchTrials();

    // 确保初始滚动位置在页面顶部
    window.scrollTo(0, 0);

    // 使用更长的延迟确保DOM完全渲染
    setTimeout(() => {
      console.log('DOM状态检查:');
      console.log('- jspsych-target元素:', !!document.getElementById('jspsych-target'));
      
      // 初始化实验
      initializeExperiment();
      
      // 再次确保滚动位置在顶部
      window.scrollTo(0, 0);
    }, 500); // 降到500ms延迟，加快加载速度
  } catch (error) {
    console.error('初始化实验时出错:', error);
    ElMessage.error('初始化实验失败，请刷新页面重试');
  }
});

onUnmounted(() => {
  // 清理资源
  window.removeEventListener('keydown', keyHandler);
  clearInterval(intervalId);
});

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
}
</script>

<style>
/* 全局样式 - 不使用scoped，确保应用到jsPsych生成的元素 */
.experiment-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}

/* 顶部空间，用于将内容向下推 */
.top-spacer {
  height: 10vh; /* 调整这个值可以控制内容向下的距离 */
  width: 100%;
}

/* JSPsych显示元素样式，确保居中 */
.jspsych-display-element {
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  box-sizing: border-box;
}

/* 内容容器样式，控制显示范围 */
#jspsych-content {
  max-width: 800px !important;
  margin: 0 auto !important;
}

/* 添加jsPsych自定义样式 */
.jspsych-content {
  max-width: 800px;
}

.jspsych-btn {
  padding: 10px 20px;
  font-size: 16px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  margin: 10px;
}

.primary-btn {
  background-color: #409EFF;
  color: white;
  font-weight: bold;
}

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
  text-align: center;
  padding: 10px 0;
  font-weight: bold;
  color: #409EFF;
}

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

.btn-hover-enabled:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

.instruction {
  margin: 10px 0;
  line-height: 1.6;
}

.key-guide {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}

.timer-container {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.timer {
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
  animation: drainSand 180s linear forwards;
}

.hourglass-bottom {
  position: absolute;
  bottom: 0;
  width: 30px;
  height: 25px;
  background-color: #E6E6E6;
  clip-path: polygon(0 100%, 100% 100%, 50% 0, 0 100%);
  animation: fillSand 180s linear forwards;
}

@keyframes drainSand {
  from {
    height: 25px;
  }

  to {
    height: 0;
  }
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

.experiment-end {
  text-align: center;
  padding: 40px;
}

.experiment-end h2 {
  color: #409EFF;
  margin-bottom: 20px;
}
</style>