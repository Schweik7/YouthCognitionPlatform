<template>
  <div class="experiment-page">
    <TopNavBar />
    <div class="experiment-container">
    <!-- 调试面板 -->
    <div v-if="debugMode" class="debug-panel">
      <h3>调试模式</h3>
      <div class="debug-controls">
        <el-input-number v-model="jumpToIndex" :min="1" :max="totalProblems" label="跳转题号"></el-input-number>
        <el-button type="primary" @click="jumpToProblem">跳转</el-button>
        <el-input-number v-model="remainingTime" :min="0" :max="testDuration" label="剩余时间(秒)"></el-input-number>
        <el-button type="primary" @click="() => resetTimer(remainingTime)">更新时间</el-button>
        <el-button type="warning" @click="endTest">结束测试</el-button>
      </div>
    </div>

    <!-- 实验内容区域 -->
    <div class="content-area">
      <!-- 指导语阶段 -->
      <CalculationWelcome 
        v-if="phase === 'welcome'" 
        :grade-level="gradeLevel"
        @start="startTest"
      />

      <!-- 正式测试阶段 -->
      <CalculationAllProblems
        v-if="phase === 'test' && !testEnded"
        :problems="problems"
        :grade-level="gradeLevel"
        :total-problems="totalProblems"
        :remaining-time="remainingTime"
        :format-time="formatTime"
        :hourglass-styles="hourglassStyles"
        @submit-all-answers="handleSubmitAllAnswers"
        ref="testComponent"
      />

      <!-- 测试结果 -->
      <CalculationResults
        v-else-if="phase === 'result'"
        :test-results="testResults"
        :total-problems="totalProblems"
        :grade-level="gradeLevel"
        :type-stats="typeStats"
        :test-duration="testDuration"
        :remaining-time="remainingTime"
        :format-percentage="formatPercentage"
        :format-response-time="formatResponseTime"
        :format-time="formatTime"
        :show-type-analysis="showTypeAnalysis"
        @go-to-selection="goToSelection"
        @restart-test="restartTest"
      />
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import TopNavBar from './TopNavBar.vue'
import { useUserInfo } from '@/composables/useUserInfo'
import { useTimer } from '@/composables/useTimer'
import { useDebugMode } from '@/composables/useDebugMode'
import { useCalculationProblems } from '@/composables/useCalculationProblems'
import CalculationWelcome from './calculation/CalculationWelcome.vue'
import CalculationTest from './calculation/CalculationTest.vue'
import CalculationAllProblems from './calculation/CalculationAllProblems.vue'
import CalculationResults from './calculation/CalculationResults.vue'

const router = useRouter()

// 使用组合式函数
const { userId, getUserInfo } = useUserInfo()
const { debugMode } = useDebugMode()
const { generateProblems } = useCalculationProblems()

// 状态变量
const phase = ref('welcome') // 实验阶段: welcome, test, result
const testSessionId = ref(null)
const gradeLevel = ref(1) // 年级（1-6）
const problems = ref([]) // 所有题目
const currentIndex = ref(0) // 当前题目索引
const totalProblems = ref(40) // 总题目数
const testEnded = ref(false) // 测试是否结束
const jumpToIndex = ref(1) // 调试模式：跳转题号
const showTypeAnalysis = ref(true) // 控制是否显示题型成绩分析
const problemStartTime = ref(0) // 当前题目开始时间
const testComponent = ref(null) // 测试组件引用

// 根据年级设置测试时间
const getTestDuration = (grade) => {
  const durations = {
    1: 180, // 一年级3分钟
    2: 240, // 二年级4分钟
    3: 300, // 三年级5分钟
    4: 360, // 四年级6分钟
    5: 420, // 五年级7分钟
    6: 480  // 六年级8分钟
  }
  return durations[grade] || 300
}

const testDuration = computed(() => getTestDuration(gradeLevel.value))
const { remainingTime, formatTime, startTimer, stopTimer, resetTimer, hourglassStyles } = useTimer(testDuration.value)

// 测试结果
const testResults = reactive({
  completedProblems: 0,
  correctProblems: 0,
  totalScore: 0,
  maxPossibleScore: totalProblems.value,
  scorePercentage: 0,
  accuracy: 0,
  averageResponseTime: 0
})

// 题型统计 - 扩展支持更多年级
const typeStats = reactive({
  // 一年级
  addition: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  subtraction: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  // 二年级
  twoNumbers: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  threeNumbers: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  // 三年级
  type1: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  type2: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  type3: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  // 四年级
  twoDigitAddSub: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  twoDigitMult: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  fractionAddSub: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  threeDigitMult: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  // 五年级及以上
  multiplication: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  division: { total: 0, completed: 0, correct: 0, accuracy: 0 },
  mixed: { total: 0, completed: 0, correct: 0, accuracy: 0 }
})

// 当前题目
const currentProblem = computed(() => {
  if (problems.value.length === 0 || currentIndex.value >= problems.value.length) {
    return { text: "", answer: 0 }
  }
  return problems.value[currentIndex.value]
})

// 工具函数
const formatPercentage = (value) => {
  return Math.round(value * 10) / 10
}

const formatResponseTime = (time) => {
  return Math.round(time)
}

// 获取用户信息并设置年级
const initializeUserInfo = async () => {
  const userInfoStr = localStorage.getItem('userInfo')
  if (!userInfoStr) {
    ElMessage.warning('未登录，请先登录')
    router.push('/')
    return
  }

  try {
    const userInfo = JSON.parse(userInfoStr)
    
    // 设置年级（支持1-6年级）
    gradeLevel.value = userInfo.grade > 0 && userInfo.grade <= 6 ? userInfo.grade : 1
    
    // 根据年级设置题目数量
    const problemCounts = {
      1: 40, // 一年级
      2: 40, // 二年级
      3: 40, // 三年级
      4: 40, // 四年级
      5: 40, // 五年级
      6: 40  // 六年级
    }
    totalProblems.value = problemCounts[gradeLevel.value] || 40
    
    // 重置计时器为对应年级的时间
    resetTimer(testDuration.value)

    // 获取或创建用户
    await getUserInfo()
  } catch (error) {
    console.error('解析用户信息失败:', error)
  }
}

// 创建测试会话
const createTestSession = async () => {
  if (!userId.value) {
    console.error('无法创建测试会话：缺少用户ID')
    return
  }

  try {
    const response = await fetch('/api/calculation/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId.value,
        grade_level: gradeLevel.value,
        total_questions: totalProblems.value
      })
    })

    if (response.ok) {
      const data = await response.json()
      testSessionId.value = data.id
      console.log('测试会话创建成功，ID:', testSessionId.value)
    } else {
      console.error('创建测试会话失败:', await response.text())
    }
  } catch (error) {
    console.error('创建测试会话请求失败:', error)
  }
}

// 更新测试会话进度
const updateTestSession = async (progress) => {
  if (!testSessionId.value) return

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        progress: progress
      })
    })

    if (!response.ok) {
      console.error('更新测试会话失败:', await response.text())
    }
  } catch (error) {
    console.error('更新测试会话请求失败:', error)
  }
}

// 保存题目答案
const saveProblem = async (problem, userAnswer, responseTime) => {
  if (!testSessionId.value || !userId.value) {
    console.error('无法保存题目：缺少会话ID或用户ID')
    return
  }

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}/problems`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId.value,
        test_session_id: testSessionId.value,
        problem_index: problem.index,
        problem_text: problem.text,
        correct_answer: problem.answer,
        user_answer: userAnswer,
        response_time: responseTime
      })
    })

    if (!response.ok) {
      console.error('保存题目失败:', await response.text())
    }
  } catch (error) {
    console.error('保存题目请求失败:', error)
  }
}

// 批量保存题目答案
const saveBatchProblems = async (answerData) => {
  if (!testSessionId.value || !userId.value) {
    console.error('无法保存题目：缺少会话ID或用户ID')
    return
  }

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}/problems-batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId.value,
        test_session_id: testSessionId.value,
        problems: answerData
      })
    })

    if (!response.ok) {
      console.error('批量保存题目失败:', await response.text())
    }
  } catch (error) {
    console.error('批量保存题目请求失败:', error)
  }
}

// 完成测试会话
const completeTestSession = async () => {
  if (!testSessionId.value) return

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      console.log('测试会话已完成')
    } else {
      console.error('完成测试会话失败:', await response.text())
    }
  } catch (error) {
    console.error('完成测试会话请求失败:', error)
  }
}

// 获取测试结果
const getTestResults = async () => {
  if (!testSessionId.value) return

  try {
    const response = await fetch(`/api/calculation/sessions/${testSessionId.value}/results`)
    
    if (response.ok) {
      const data = await response.json()
      
      // 更新测试结果
      Object.assign(testResults, {
        completedProblems: data.stats.completedProblems,
        correctProblems: data.stats.correctProblems,
        totalScore: data.stats.totalScore,
        maxPossibleScore: data.stats.maxPossibleScore,
        scorePercentage: data.stats.scorePercentage,
        accuracy: data.stats.accuracy,
        averageResponseTime: data.stats.averageResponseTime
      })
      
      // 更新题型统计
      updateTypeStats(data.stats.problemTypeStats)
      
      console.log('测试结果获取成功')
    } else {
      console.error('获取测试结果失败:', await response.text())
    }
  } catch (error) {
    console.error('获取测试结果请求失败:', error)
  }
}

// 更新题型统计
const updateTypeStats = (problemTypeStats) => {
  // 重置所有统计
  Object.keys(typeStats).forEach(key => {
    Object.assign(typeStats[key], { total: 0, completed: 0, correct: 0, accuracy: 0 })
  })

  // 根据年级更新对应的统计
  if (gradeLevel.value === 1) {
    if (problemTypeStats.addition) {
      Object.assign(typeStats.addition, problemTypeStats.addition)
    }
    if (problemTypeStats.subtraction) {
      Object.assign(typeStats.subtraction, problemTypeStats.subtraction)
    }
  } else if (gradeLevel.value === 2) {
    if (problemTypeStats.twoNumbers) {
      Object.assign(typeStats.twoNumbers, problemTypeStats.twoNumbers)
    }
    if (problemTypeStats.threeNumbers) {
      Object.assign(typeStats.threeNumbers, problemTypeStats.threeNumbers)
    }
  } else if (gradeLevel.value === 3) {
    if (problemTypeStats.twoDigitOperations) {
      Object.assign(typeStats.type1, problemTypeStats.twoDigitOperations)
    }
    if (problemTypeStats.threeDigitOperations) {
      Object.assign(typeStats.type2, problemTypeStats.threeDigitOperations)
    }
    if (problemTypeStats.threeDigitThreeNumbers) {
      Object.assign(typeStats.type3, problemTypeStats.threeDigitThreeNumbers)
    }
  } else if (gradeLevel.value === 4) {
    if (problemTypeStats.twoDigitAddSub) {
      Object.assign(typeStats.twoDigitAddSub, problemTypeStats.twoDigitAddSub)
    }
    if (problemTypeStats.twoDigitMult) {
      Object.assign(typeStats.twoDigitMult, problemTypeStats.twoDigitMult)
    }
    if (problemTypeStats.fractionAddSub) {
      Object.assign(typeStats.fractionAddSub, problemTypeStats.fractionAddSub)
    }
    if (problemTypeStats.threeDigitMult) {
      Object.assign(typeStats.threeDigitMult, problemTypeStats.threeDigitMult)
    }
  } else if (gradeLevel.value >= 5) {
    if (problemTypeStats.multiplication) {
      Object.assign(typeStats.multiplication, problemTypeStats.multiplication)
    }
    if (problemTypeStats.division) {
      Object.assign(typeStats.division, problemTypeStats.division)
    }
    if (problemTypeStats.mixed) {
      Object.assign(typeStats.mixed, problemTypeStats.mixed)
    }
  }
}

// 开始测试
const startTest = async () => {
  try {
    // 获取用户信息
    await initializeUserInfo()

    // 生成题目
    const generatedProblems = await generateProblems(gradeLevel.value)
    if (!generatedProblems || generatedProblems.length === 0) {
      ElMessage.error('获取题目失败，请重试')
      return
    }
    problems.value = generatedProblems

    // 创建测试会话
    await createTestSession()

    // 准备测试
    phase.value = 'test'
    currentIndex.value = 0
    problemStartTime.value = Date.now()

    // 启动计时器
    startTimer(() => endTest())

    // 聚焦答案输入框
    nextTick(() => {
      if (testComponent.value?.focusInput) {
        testComponent.value.focusInput()
      }
    })
  } catch (error) {
    console.error('开始测试失败:', error)
    ElMessage.error('开始测试失败，请重试')
  }
}

// 处理提交答案
const handleSubmitAnswer = async (userAnswer) => {
  // 计算反应时间
  const endTime = Date.now()
  const responseTime = endTime - problemStartTime.value
  
  // 获取当前题目
  const problem = problems.value[currentIndex.value]
  
  // 保存答题结果
  await saveProblem(problem, userAnswer, responseTime)
  
  // 更新进度
  await updateTestSession(currentIndex.value + 1)
  
  // 准备下一题
  if (currentIndex.value < problems.value.length - 1 && remainingTime.value > 0) {
    currentIndex.value++
    problemStartTime.value = Date.now()
    
    // 聚焦答案输入框
    nextTick(() => {
      if (testComponent.value?.focusInput) {
        testComponent.value.focusInput()
      }
    })
  } else {
    // 测试结束
    endTest()
  }
}

// 处理批量提交答案
const handleSubmitAllAnswers = async (answerData) => {
  // 批量保存答题结果
  await saveBatchProblems(answerData)
  
  // 更新进度为总题目数
  await updateTestSession(totalProblems.value)
  
  // 测试结束
  endTest()
}

// 结束测试
const endTest = async () => {
  if (testEnded.value) return

  testEnded.value = true
  stopTimer()

  // 显示加载中提示
  const loading = ElLoading.service({
    lock: true,
    text: '正在处理结果...',
    background: 'rgba(0, 0, 0, 0.7)'
  })

  try {
    // 完成测试会话
    await completeTestSession()

    // 获取测试结果
    await getTestResults()

    // 显示结果页面
    phase.value = 'result'
  } catch (error) {
    console.error('结束测试失败:', error)
    ElMessage.error('处理测试结果失败，请重试')
  } finally {
    // 关闭加载提示
    loading.close()
  }
}

// 返回测试选择
const goToSelection = () => {
  router.push('/selection')
}

// 重置测试
const restartTest = () => {
  // 重置状态
  phase.value = 'welcome'
  currentIndex.value = 0
  problems.value = []
  testEnded.value = false
  testSessionId.value = null
  
  // 重置计时器
  resetTimer(testDuration.value)
  
  // 重置结果
  Object.assign(testResults, {
    completedProblems: 0,
    correctProblems: 0,
    totalScore: 0,
    maxPossibleScore: totalProblems.value,
    scorePercentage: 0,
    accuracy: 0,
    averageResponseTime: 0
  })
  
  // 重置题型统计
  Object.keys(typeStats).forEach(key => {
    Object.assign(typeStats[key], { total: 0, completed: 0, correct: 0, accuracy: 0 })
  })
}

// 调试模式：跳转到指定题目
const jumpToProblem = () => {
  if (phase.value !== 'test' || jumpToIndex.value < 1 || jumpToIndex.value > problems.value.length) {
    return
  }

  currentIndex.value = jumpToIndex.value - 1
  problemStartTime.value = Date.now()

  // 聚焦答案输入框
  nextTick(() => {
    if (testComponent.value?.focusInput) {
      testComponent.value.focusInput()
    }
  })
}

// 生命周期钩子
onMounted(() => {
  // 初始化用户信息
  initializeUserInfo()
})

onUnmounted(() => {
  // 清理资源
  stopTimer()
})
</script>

<style scoped>
.experiment-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.experiment-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: calc(100vh - 60px);
  padding: 10px;
}

.content-area {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  box-sizing: border-box;
}

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
</style>