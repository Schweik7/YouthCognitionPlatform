<template>
  <div class="all-problems-container">
    <!-- 五年级特殊提醒 -->
    <div v-if="gradeLevel === 5" class="grade5-notice">
      <el-alert
        title="注意"
        type="info"
        :closable="false"
        show-icon
      >
        <div class="notice-content">
          涉及小数运算，能除尽的请除尽。无法除尽的，如果答案是循环数，请标出循环节，如果答案不是循环数，请保留两位小数。
        </div>
      </el-alert>
    </div>

    <!-- 测试头部 -->
    <div class="test-header">
      <div class="test-info">
        <span>{{ gradeLevel }}年级计算流畅性测试</span>
        <span class="progress-text">已完成：{{ completedCount }}/{{ totalProblems }}</span>
      </div>
      <div class="test-timer">
        <span>{{ formatTime(remainingTime) }}</span>
      </div>
    </div>

    <!-- 题目网格 -->
    <div class="problems-grid">
      <div 
        v-for="(problem, index) in problems" 
        :key="problem.index"
        class="problem-item"
        :class="{ 'completed': answers[index] !== null && answers[index] !== undefined }"
      >
        <!-- 题目文本 -->
        <div class="problem-text">
          {{ problem.text }}
        </div>

        <!-- 答案区域 -->
        <div class="answer-area">
          <!-- 五年级小数题目的特殊答案框 -->
          <div v-if="gradeLevel === 5" class="answer-box-decimal">
            <div class="decimal-input-container">
              <!-- 整数部分 -->
              <input 
                v-model="decimalAnswers[index].integer"
                type="text"
                class="answer-input decimal-integer"
                :class="{ 'filled': decimalAnswers[index].integer !== '' }"
                placeholder="0"
                @input="handleDecimalChange(index)"
              />
              
              <!-- 小数点 -->
              <span class="decimal-point">.</span>
              
              <!-- 小数部分容器 -->
              <div class="decimal-part">
                <!-- 小数位数字 -->
                <div class="decimal-digits">
                  <span 
                    v-for="(digit, digitIndex) in decimalAnswers[index].decimals" 
                    :key="digitIndex"
                    class="decimal-digit"
                    :class="{ 'has-dot': digit.hasDot }"
                    @click="toggleDot(index, digitIndex)"
                  >
                    <input 
                      v-model="digit.value"
                      type="text"
                      class="digit-input"
                      maxlength="1"
                      @input="handleDigitInput(index, digitIndex, $event)"
                      @keydown="handleDigitKeydown(index, digitIndex, $event)"
                    />
                    <div v-if="digit.hasDot" class="repeating-dot"></div>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 普通题目的答案框 (非五年级) -->
          <div v-else-if="!problem.hasFraction" class="answer-box-simple">
            <input 
              v-model.number="answers[index]"
              type="number"
              class="answer-input"
              :class="{ 'filled': answers[index] !== null && answers[index] !== undefined }"
              placeholder=""
              @input="handleAnswerChange(index, $event)"
            />
          </div>

          <!-- 分数题目的答案框 (整数 + 分数) -->
          <div v-else class="answer-box-fraction">
            <!-- 整数部分 -->
            <div class="whole-number-box">
              <input 
                v-model.number="fractionAnswers[index].whole"
                type="number"
                class="answer-input fraction-input"
                :class="{ 'filled': fractionAnswers[index].whole !== null && fractionAnswers[index].whole !== undefined }"
                placeholder=""
                @input="handleFractionChange(index)"
              />
            </div>
            
            <!-- 分数部分 -->
            <div class="fraction-box">
              <div class="numerator-box">
                <input 
                  v-model.number="fractionAnswers[index].numerator"
                  type="number"
                  class="answer-input fraction-input"
                  :class="{ 'filled': fractionAnswers[index].numerator !== null && fractionAnswers[index].numerator !== undefined }"
                  placeholder=""
                  @input="handleFractionChange(index)"
                />
              </div>
              <div class="fraction-line"></div>
              <div class="denominator-box">
                <input 
                  v-model.number="fractionAnswers[index].denominator"
                  type="number"
                  class="answer-input fraction-input"
                  :class="{ 'filled': fractionAnswers[index].denominator !== null && fractionAnswers[index].denominator !== undefined }"
                  placeholder=""
                  @input="handleFractionChange(index)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 提交按钮 -->
    <div class="submit-section">
      <el-button 
        type="primary" 
        size="large"
        @click="submitAllAnswers"
        :disabled="isProcessing"
      >
        {{ isProcessing ? '提交中...' : '提交答案' }}
      </el-button>
    </div>

    <!-- 计时器沙漏 -->
    <div class="timer-container">
      <div class="hourglass-container">
        <div class="hourglass">
          <div class="hourglass-top" :style="hourglassStyles.top"></div>
          <div class="hourglass-bottom" :style="hourglassStyles.bottom"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'

const props = defineProps({
  problems: {
    type: Array,
    required: true
  },
  gradeLevel: {
    type: Number,
    required: true
  },
  totalProblems: {
    type: Number,
    required: true
  },
  remainingTime: {
    type: Number,
    required: true
  },
  formatTime: {
    type: Function,
    required: true
  },
  hourglassStyles: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['submit-all-answers'])

// 答案数组
const answers = ref(new Array(props.problems.length).fill(null))

// 分数答案对象（用于4-6年级的分数题）
const fractionAnswers = reactive({})

// 五年级小数答案对象
const decimalAnswers = reactive({})

// 处理状态
const isProcessing = ref(false)

// 初始化分数答案
const initializeFractionAnswers = () => {
  props.problems.forEach((problem, index) => {
    if (problem.hasFraction) {
      fractionAnswers[index] = {
        whole: null,
        numerator: null,
        denominator: null
      }
    }
  })
}

// 初始化五年级小数答案
const initializeDecimalAnswers = () => {
  if (props.gradeLevel === 5) {
    props.problems.forEach((problem, index) => {
      decimalAnswers[index] = {
        integer: '',
        decimals: [
          { value: '', hasDot: false },
          { value: '', hasDot: false },
          { value: '', hasDot: false },
          { value: '', hasDot: false }
        ]
      }
    })
  }
}

// 完成数量
const completedCount = computed(() => {
  if (props.gradeLevel === 5) {
    // 五年级计算已填写的小数答案
    return Object.values(decimalAnswers).filter(decimal => {
      return decimal.integer !== '' || decimal.decimals.some(d => d.value !== '')
    }).length
  } else {
    // 其他年级使用原有逻辑
    return answers.value.filter(answer => answer !== null && answer !== undefined).length
  }
})

// 处理普通答案变化
const handleAnswerChange = (index, event) => {
  const value = event.target.value
  answers.value[index] = value === '' ? null : parseFloat(value)
}

// 处理分数答案变化
const handleFractionChange = (index) => {
  const fraction = fractionAnswers[index]
  if (fraction) {
    // 将分数转换为小数作为最终答案
    let decimalAnswer = 0
    
    // 整数部分
    if (fraction.whole !== null && fraction.whole !== undefined) {
      decimalAnswer += fraction.whole
    }
    
    // 分数部分
    if (fraction.numerator !== null && fraction.numerator !== undefined && 
        fraction.denominator !== null && fraction.denominator !== undefined && 
        fraction.denominator !== 0) {
      decimalAnswer += fraction.numerator / fraction.denominator
    }
    
    // 更新答案数组
    answers.value[index] = decimalAnswer
  }
}

// 处理五年级小数答案变化
const handleDecimalChange = (index) => {
  const decimal = decimalAnswers[index]
  if (decimal) {
    // 构建小数答案字符串
    let answerString = decimal.integer || '0'
    
    // 添加小数部分
    const decimalPart = decimal.decimals.map(d => d.value).join('').replace(/0+$/, '')
    if (decimalPart) {
      answerString += '.' + decimalPart
    }
    
    // 转换为数字
    const numericAnswer = parseFloat(answerString) || 0
    answers.value[index] = numericAnswer
  }
}

// 处理小数位数字输入
const handleDigitInput = (index, digitIndex, event) => {
  const value = event.target.value
  if (/^\d$/.test(value) || value === '') {
    decimalAnswers[index].decimals[digitIndex].value = value
    
    // 如果输入了数字且不是最后一位，自动聚焦下一位
    if (value && digitIndex < 3) {
      const nextInput = event.target.parentElement.parentElement.children[digitIndex + 1]?.querySelector('.digit-input')
      if (nextInput) {
        nextInput.focus()
      }
    }
    
    handleDecimalChange(index)
  } else {
    // 不允许非数字输入
    event.target.value = decimalAnswers[index].decimals[digitIndex].value
  }
}

// 处理小数位键盘事件
const handleDigitKeydown = (index, digitIndex, event) => {
  // 退格键处理
  if (event.key === 'Backspace' && !decimalAnswers[index].decimals[digitIndex].value && digitIndex > 0) {
    const prevInput = event.target.parentElement.parentElement.children[digitIndex - 1]?.querySelector('.digit-input')
    if (prevInput) {
      prevInput.focus()
      prevInput.select()
    }
  }
  
  // 左右箭头键处理
  if (event.key === 'ArrowLeft' && digitIndex > 0) {
    const prevInput = event.target.parentElement.parentElement.children[digitIndex - 1]?.querySelector('.digit-input')
    if (prevInput) {
      prevInput.focus()
    }
  }
  
  if (event.key === 'ArrowRight' && digitIndex < 3) {
    const nextInput = event.target.parentElement.parentElement.children[digitIndex + 1]?.querySelector('.digit-input')
    if (nextInput) {
      nextInput.focus()
    }
  }
}

// 切换循环节点
const toggleDot = (index, digitIndex) => {
  decimalAnswers[index].decimals[digitIndex].hasDot = !decimalAnswers[index].decimals[digitIndex].hasDot
}

// 提交所有答案
const submitAllAnswers = async () => {
  if (isProcessing.value) return
  
  isProcessing.value = true
  
  // 构建答案数据
  const answerData = props.problems.map((problem, index) => ({
    problemIndex: problem.index,
    problemText: problem.text,
    correctAnswer: problem.answer,
    userAnswer: answers.value[index],
    type: problem.type,
    hasFraction: problem.hasFraction || false,
    fractionAnswer: problem.hasFraction ? fractionAnswers[index] : null
  }))
  
  emit('submit-all-answers', answerData)
  
  isProcessing.value = false
}

// 初始化
initializeFractionAnswers()
initializeDecimalAnswers()

// 监听题目变化，重新初始化
watch(() => props.problems, () => {
  answers.value = new Array(props.problems.length).fill(null)
  initializeFractionAnswers()
  initializeDecimalAnswers()
}, { deep: true })
</script>

<style scoped>
.all-problems-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 0 10px;
}

.test-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.test-info span:first-child {
  font-size: 20px;
  font-weight: bold;
}

.progress-text {
  font-size: 16px;
  color: #666;
}

.test-timer {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  background-color: white;
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.problems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.problem-item {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.problem-item.completed {
  border-color: #67C23A;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.problem-text {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 15px;
  text-align: center;
}

.answer-area {
  display: flex;
  justify-content: center;
  align-items: center;
}

.answer-box-simple {
  width: 100%;
  max-width: 120px;
}

.answer-input {
  width: 100%;
  height: 45px;
  font-size: 18px;
  text-align: center;
  border: 2px dashed #ddd;
  border-radius: 6px;
  background-color: #fafafa;
  outline: none;
  transition: all 0.3s ease;
}

.answer-input:focus {
  border-color: #409EFF;
  background-color: white;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.answer-input.filled {
  border-color: #67C23A;
  background-color: #f0f9ff;
}

.answer-box-fraction {
  display: flex;
  align-items: center;
  gap: 10px;
}

.whole-number-box {
  width: 60px;
}

.fraction-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.numerator-box,
.denominator-box {
  width: 50px;
  height: 35px;
}

.fraction-input {
  width: 100%;
  height: 100%;
  font-size: 16px;
}

.fraction-line {
  width: 60px;
  height: 2px;
  background-color: #333;
  margin: 2px 0;
}

/* 五年级小数输入样式 */
.grade5-notice {
  margin-bottom: 20px;
}

.notice-content {
  font-size: 16px;
  line-height: 1.6;
  color: #666;
}

.answer-box-decimal {
  width: 100%;
  max-width: 250px;
}

.decimal-input-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px;
  border: 2px dashed #ddd;
  border-radius: 6px;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

.decimal-input-container:focus-within {
  border-color: #409EFF;
  background-color: white;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.decimal-integer {
  width: 60px;
  height: 35px;
  font-size: 18px;
  text-align: center;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  outline: none;
}

.decimal-integer.filled {
  border-color: #67C23A;
  background-color: #f0f9ff;
}

.decimal-point {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin: 0 2px;
}

.decimal-part {
  display: flex;
  align-items: center;
}

.decimal-digits {
  display: flex;
  gap: 2px;
}

.decimal-digit {
  position: relative;
  display: inline-block;
  cursor: pointer;
}

.digit-input {
  width: 25px;
  height: 35px;
  font-size: 16px;
  text-align: center;
  border: 1px solid #ddd;
  border-radius: 3px;
  background-color: white;
  outline: none;
  transition: all 0.2s ease;
}

.digit-input:focus {
  border-color: #409EFF;
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.3);
}

.repeating-dot {
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  background-color: #409EFF;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.decimal-digit.has-dot .digit-input {
  border-color: #409EFF;
  background-color: #f0f9ff;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: translateX(-50%) scale(1);
  }
  50% {
    opacity: 0.7;
    transform: translateX(-50%) scale(1.2);
  }
}

.submit-section {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

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

@media (max-width: 768px) {
  .problems-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .test-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .test-timer {
    font-size: 20px;
    padding: 8px 16px;
  }
  
  .problem-item {
    padding: 15px;
  }
}
</style>