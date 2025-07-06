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