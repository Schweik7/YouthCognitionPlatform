<template>
  <div class="result-container">
    <h2>测试结果</h2>

    <el-card class="result-card">
      <div class="result-item total-score">
        <div class="result-label">总得分:</div>
        <div class="result-value">{{ testResults.totalScore }} / {{ testResults.maxPossibleScore }}</div>
      </div>
      <div class="result-item">
        <div class="result-label">得分率:</div>
        <div class="result-value">{{ formatPercentage(testResults.scorePercentage) }}%</div>
      </div>
      <div class="result-item">
        <div class="result-label">共完成题目:</div>
        <div class="result-value">{{ testResults.completedProblems }} / {{ totalProblems }}</div>
      </div>
      <div class="result-item">
        <div class="result-label">正确数量:</div>
        <div class="result-value">{{ testResults.correctProblems }}</div>
      </div>
      <div class="result-item">
        <div class="result-label">错误数量:</div>
        <div class="result-value">{{ testResults.completedProblems - testResults.correctProblems }}</div>
      </div>
      <div class="result-item">
        <div class="result-label">正确率:</div>
        <div class="result-value">{{ formatPercentage(testResults.accuracy) }}%</div>
      </div>
      <div class="result-item">
        <div class="result-label">平均反应时间:</div>
        <div class="result-value">{{ formatResponseTime(testResults.averageResponseTime) }}毫秒</div>
      </div>
      <div class="result-item">
        <div class="result-label">总用时:</div>
        <div class="result-value">{{ formatTime(testDuration - remainingTime) }}</div>
      </div>
    </el-card>

    <!-- 题型分析 -->
    <TypeStats 
      v-if="gradeLevel <= 6 && showTypeAnalysis"
      :grade-level="gradeLevel"
      :type-stats="typeStats"
      :format-percentage="formatPercentage"
    />

    <div class="action-buttons">
      <el-button type="primary" @click="$emit('go-to-selection')">返回测试选择</el-button>
      <el-button @click="$emit('restart-test')">重新测试</el-button>
    </div>
  </div>
</template>

<script setup>
import TypeStats from './TypeStats.vue'

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