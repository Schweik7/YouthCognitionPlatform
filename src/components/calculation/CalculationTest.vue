<template>
  <div class="test-container">
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
          size="large"
        />
        <el-button 
          type="primary" 
          @click="submitAnswer" 
          :disabled="isProcessing || userAnswer === ''" 
          size="large"
        >
          确认
        </el-button>
      </div>
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
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  currentProblem: {
    type: Object,
    required: true
  },
  currentIndex: {
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

const emit = defineEmits(['submit-answer'])

const userAnswer = ref('')
const isProcessing = ref(false)
const answerInput = ref(null)

const submitAnswer = async () => {
  if (isProcessing.value || userAnswer.value === '') return
  
  isProcessing.value = true
  
  // 将用户答案转换为数字
  const numericAnswer = parseInt(userAnswer.value)
  
  emit('submit-answer', numericAnswer)
  
  // 重置状态
  isProcessing.value = false
  userAnswer.value = ''
  
  // 聚焦答案输入框
  nextTick(() => {
    if (answerInput.value) {
      answerInput.value.focus()
    }
  })
}

// 暴露方法给父组件
defineExpose({
  focusInput: () => {
    nextTick(() => {
      if (answerInput.value) {
        answerInput.value.focus()
      }
    })
  }
})
</script>

<style scoped>
.test-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 14px;
  margin-bottom: 20px;
  padding: 12px 20px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  box-shadow: var(--sh-xs);
}

.test-info {
  font-weight: 700;
  font-size: 15px;
  color: var(--ink-900);
  font-variant-numeric: tabular-nums;
}

.test-timer {
  font-family: var(--font-num);
  font-variant-numeric: tabular-nums;
  font-size: 22px;
  font-weight: 700;
  color: #0f8f56;
  background: var(--success-soft);
  padding: 6px 18px;
  border-radius: var(--r-full);
  box-shadow: none;
}

.problem-card {
  width: 100%;
  background-color: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  box-shadow: var(--sh-md);
  padding: clamp(30px, 5vw, 52px);
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.problem-text {
  font-family: var(--font-num);
  font-size: clamp(34px, 5vw, 44px);
  font-weight: 700;
  color: var(--ink-900);
  letter-spacing: .04em;
  margin-bottom: 34px;
  text-align: center;
}

.answer-input {
  display: flex;
  gap: 12px;
  width: 100%;
  max-width: 340px;
}

.answer-input :deep(.el-input__inner) {
  text-align: center;
  font-family: var(--font-num);
  font-size: 20px;
  font-weight: 600;
}

/* 沙漏计时 */
.timer-container {
  position: fixed;
  top: 84px;
  right: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, .9);
  backdrop-filter: blur(10px);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  box-shadow: var(--sh-sm);
  z-index: 40;
}

.hourglass-container { display: flex; justify-content: center; }

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
  background-color: var(--hue-calc);
  clip-path: polygon(0 0, 100% 0, 50% 100%, 0 0);
}

.hourglass-bottom {
  position: absolute;
  bottom: 0;
  width: 30px;
  height: 0;
  background-color: var(--line);
  clip-path: polygon(0 100%, 100% 100%, 50% 0, 0 100%);
}

@media (max-width: 768px) {
  .problem-card { padding: 26px 20px; }
  .test-timer { font-size: 20px; }
  .timer-container { top: 72px; right: 12px; padding: 8px; }
}
</style>
