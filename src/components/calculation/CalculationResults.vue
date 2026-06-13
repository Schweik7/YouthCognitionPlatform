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
}

.result-container h2 {
  color: #409EFF;
  margin-bottom: 20px;
}

.result-card {
  margin-bottom: 30px;
}

.thanks-card {
  padding: 40px 20px;
}

.thanks-icon {
  font-size: 56px;
  margin-bottom: 10px;
}

.thanks-text {
  font-size: 18px;
  color: #606266;
  margin-top: 10px;
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

.total-score {
  background-color: #f0f9eb;
  padding: 15px;
  border-radius: 4px;
  margin: 10px 0;
}

.total-score .result-label {
  color: #67C23A;
  font-size: 1.1em;
}

.total-score .result-value {
  color: #67C23A;
  font-size: 1.2em;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}
</style>