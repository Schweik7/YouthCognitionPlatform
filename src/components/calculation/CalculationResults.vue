<template>
  <div class="result-container">
    <el-card class="result-card thanks-card">
      <div class="thanks-icon">🎉</div>
      <h2>测试已完成</h2>
      <p class="thanks-text">感谢你的作答！</p>
    </el-card>

    <div class="action-buttons">
      <el-button type="primary" @click="$emit('go-to-selection')">返回测试选择</el-button>
      <el-button @click="$emit('restart-test')">重新测试</el-button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  testResults: {
    type: Object,
    required: true
  },
  totalProblems: {
    type: Number,
    required: true
  },
  gradeLevel: {
    type: Number,
    required: true
  },
  typeStats: {
    type: Object,
    required: true
  },
  testDuration: {
    type: Number,
    required: true
  },
  remainingTime: {
    type: Number,
    required: true
  },
  formatPercentage: {
    type: Function,
    required: true
  },
  formatResponseTime: {
    type: Function,
    required: true
  },
  formatTime: {
    type: Function,
    required: true
  },
  showTypeAnalysis: {
    type: Boolean,
    default: true
  }
})

defineEmits(['go-to-selection', 'restart-test'])
</script>

<style scoped>
.result-container {
  text-align: center;
  width: 100%;
  max-width: 620px;
  margin: clamp(20px, 6vh, 64px) auto;
}

.result-container h2 {
  color: var(--ink-900);
  margin-bottom: 12px;
  font-size: clamp(23px, 2.8vw, 29px);
}

.result-card { margin-bottom: 28px; }

.thanks-card {
  padding: clamp(34px, 5vw, 54px) 24px;
  background:
    radial-gradient(600px 300px at 50% -30%, rgba(139, 92, 246, .12), transparent 70%),
    var(--surface);
}

.thanks-icon {
  font-size: 60px;
  margin-bottom: 14px;
  animation: pop 0.6s cubic-bezier(.22, 1.2, .3, 1) both;
}

@keyframes pop {
  0% { transform: scale(.4); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.thanks-text {
  font-size: 17px;
  color: var(--ink-500);
  margin-top: 10px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 4px;
  border-bottom: 1px solid var(--line-soft);
}

.result-item:last-child { border-bottom: none; }

.result-label {
  font-weight: 600;
  color: var(--ink-500);
  font-size: 14px;
}

.result-value {
  color: var(--ink-900);
  font-weight: 700;
  font-family: var(--font-num);
  font-variant-numeric: tabular-nums;
  font-size: 18px;
}

.total-score {
  background: linear-gradient(135deg, rgba(139, 92, 246, .10), rgba(76, 111, 255, .07));
  padding: 16px;
  border-radius: var(--r-md);
  margin: 12px 0;
  border-bottom: none;
}

.total-score .result-label {
  color: var(--ink-700);
  font-size: 15px;
}

.total-score .result-value {
  color: var(--hue-calc);
  font-size: 26px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 26px;
}

.action-buttons :deep(.el-button) { min-width: 170px; }
</style>
