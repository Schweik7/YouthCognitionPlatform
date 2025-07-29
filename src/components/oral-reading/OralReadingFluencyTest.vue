<template>
  <div class="reading-fluency-page">
    <TopNavBar />
    <div class="reading-fluency-container">
    <!-- 测试标题和状态 -->
    <div class="test-header">
      <h2 class="test-title">朗读流畅性测试</h2>
      <div class="test-status">
        <div class="round-info">
          <span class="round-label">测试轮次:</span>
          <span class="round-number">第{{ currentRound }}/2轮</span>
        </div>
        <div class="timer" :class="{ 'timer-warning': timeLeft <= 10 }">
          <el-icon><Timer /></el-icon>
          <span class="time-text">{{ formatTime(timeLeft) }}</span>
        </div>
      </div>
    </div>

    <!-- 测试指导 -->
    <div class="instructions" v-if="testPhase === 'instruction'">
      <div class="instruction-content">
        <h3>测试说明</h3>
        <ul>
          <li>请按顺序朗读下面的汉字，从左到右，从上到下</li>
          <li><strong>按住空格键</strong>开始朗读，<strong>松开空格键</strong>结束录音并自动换行</li>
          <li>共需完成<strong>2轮</strong>朗读，每轮限时<strong>1分钟</strong></li>
          <li>只记录正确朗读的字数作为分数</li>
        </ul>
        <div class="start-button-container">
          <el-button 
            type="primary" 
            size="large" 
            @click="startTest"
            :loading="isLoading"
          >
            开始第{{ currentRound }}轮测试
          </el-button>
        </div>
      </div>
    </div>

    <!-- 字符表格显示 -->
    <div class="character-grid" v-if="testPhase === 'testing'">
      <div 
        v-for="(row, rowIndex) in characterRows" 
        :key="rowIndex"
        class="character-row"
        :class="{ 
          'current-row': rowIndex === currentRowIndex,
          'completed-row': rowIndex < currentRowIndex
        }"
      >
        <div class="row-number">{{ rowIndex + 1 }}</div>
        <div class="characters">
          <span 
            v-for="(char, charIndex) in row" 
            :key="charIndex"
            class="character"
          >
            {{ char }}
          </span>
        </div>
        <div class="row-status">
          <el-icon v-if="rowIndex < currentRowIndex" class="completed-icon">
            <Check />
          </el-icon>
          <span v-if="rowIndex === currentRowIndex && isRecording" class="reading-text">
            朗读中...
          </span>
        </div>
      </div>
    </div>

    <!-- 控制面板 -->
    <div class="control-panel" v-if="testPhase === 'testing'">
      <div class="progress-info">
        <span>当前进度: {{ currentRowIndex + 1 }}/{{ characterRows.length }}行</span>
        <span class="char-count">已读: {{ readCharacterCount }}字</span>
      </div>
      <div class="control-buttons">
        <el-button 
          @click="nextRow" 
          type="success"
          :disabled="isRecording || isProcessingAction"
          size="large"
        >
          下一行 (空格)
        </el-button>
        <el-button 
          @click="finishTest" 
          type="warning"
          size="large"
        >
          完成测试
        </el-button>
      </div>
    </div>

    <!-- 测试完成 -->
    <div class="test-complete" v-if="testPhase === 'completed'">
      <div class="completion-content">
        <h3>{{ currentRound < 2 ? '第一轮完成' : '测试完成' }}</h3>
        <div class="round-results">
          <div class="result-item">
            <span class="label">本轮用时:</span>
            <span class="value">{{ formatTime(60 - timeLeft) }}</span>
          </div>
          <div class="result-item">
            <span class="label">本轮朗读字数:</span>
            <span class="value">{{ readCharacterCount }}字</span>
          </div>
          <div class="result-item" v-if="currentRound === 2">
            <span class="label">平均成绩:</span>
            <span class="value">{{ averageScore.toFixed(1) }}字/分钟</span>
          </div>
        </div>
        
        <div class="completion-buttons">
          <el-button 
            v-if="currentRound < 2"
            type="primary" 
            size="large"
            @click="startNextRound"
            :loading="isLoading"
          >
            开始第二轮测试
          </el-button>
          <el-button 
            v-else
            type="success" 
            size="large"
            @click="submitResults"
            :loading="isSubmitting"
          >
            提交结果
          </el-button>
        </div>
      </div>
    </div>

    <!-- 录音状态指示器 -->
    <div class="recording-indicator" v-if="isRecording">
      <div class="recording-dot"></div>
      <span>录音中...</span>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElButton, ElIcon, ElMessage } from 'element-plus'
import { Timer, Check } from '@element-plus/icons-vue'
import TopNavBar from '../TopNavBar.vue'
import vmsg from 'vmsg'

// 字符数据
const characterData = ref([
  '的 一 了 我 是 不 在 上 来 有',
  '着 他 地 子 人 们 到 个 小 这',
  '里 大 天 就 说 那 去 看 下 得',
  '时 么 你 也 过 出 起 好 要 把',
  '它 儿 头 只 多 可 中 和 家 会',
  '还 又 没 花 水 长 道 面 样 见',
  '很 走 老 开 树 生 边 想 为 能',
  '声 后 然 从 自 妈 山 回 什 用',
  '成 发 叫 前 以 手 对 点 身 候',
  '飞 白 两 方 心 动 太 听 风 三',
  '十 吃 眼 几 亲 色 雨 光 学 月',
  '高 些 进 孩 住 气 给 她 知 向',
  '船 如 种 国 呢 事 红 快 外 无',
  '再 明 西 同 日 海 真 于 己 门',
  '亮 怎 草 跑 行 最 阳 问 正 啊',
  '常 马 牛 当 笑 打 放 别 经 河',
  '做 鸟 星 东 石 物 空 才 之 吧',
  '火 许 每 间 力 已 二 四 美 次'
])

// 组件状态
const testPhase = ref('instruction') // instruction, testing, completed
const currentRound = ref(1)
const currentRowIndex = ref(0)
// 移除字符索引，因为不需要跟踪朗读进度
const timeLeft = ref(60) // 倒计时秒数
const isRecording = ref(false)
const isLoading = ref(false)
const isSubmitting = ref(false)

// 录音相关 - 使用vmsg
const recorder = ref(null)
const currentAudioBlob = ref(null)

// 防抖和状态控制
const isProcessingAction = ref(false)  // 防止重复操作
const spaceKeyPressed = ref(false)     // 空格键状态跟踪

// 测试结果
const testResults = ref({
  round1: { duration: 0, characterCount: 0, audioFiles: [] },
  round2: { duration: 0, characterCount: 0, audioFiles: [] }
})

// 计时器
let timer = null

// 计算属性
const characterRows = computed(() => {
  return characterData.value.map(row => row.split(' '))
})

const readCharacterCount = computed(() => {
  return currentRowIndex.value * 10
})

const averageScore = computed(() => {
  if (currentRound.value < 2) return 0
  const total = testResults.value.round1.characterCount + testResults.value.round2.characterCount
  return total / 2
})

// 方法
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const startTest = async () => {
  isLoading.value = true
  
  try {
    // 如果是第一轮，先创建测试ID
    if (currentRound.value === 1 && !testId.value) {
      const success = await createTest()
      if (!success) {
        return
      }
    }
    
    // 初始化录音
    await initializeRecording()
    
    // 开始测试
    testPhase.value = 'testing'
    currentRowIndex.value = 0
    timeLeft.value = 60
    
    // 开始计时
    startTimer()
    
    // 不自动开始录音，等待用户按住空格键
    ElMessage.info('请按住空格键开始朗读当前行，松开空格键结束录音并换行')
    
  } catch (error) {
    ElMessage.error('无法启动录音功能，请检查麦克风权限')
    console.error('Recording initialization failed:', error)
  } finally {
    isLoading.value = false
  }
}

// 创建新的录音器实例
const createRecorder = async () => {
  console.log('🔧 创建新的vmsg录音器实例...')
  
  const newRecorder = new vmsg.Recorder({
    wasmURL: '/vmsg.wasm', // WASM文件路径
    bitRate: 128000, // 比特率 128kbps
    sampleRate: 16000, // 采样率，与后端API一致
  })
  
  await newRecorder.init()
  console.log('✅ vmsg录音器实例创建成功')
  return newRecorder
}

const initializeRecording = async () => {
  try {
    console.log('🎙️ 初始化vmsg录音系统...')
    // 只初始化一次，不创建实例（实例在每次录音时创建）
    console.log('✅ vmsg录音系统初始化成功')
    
  } catch (error) {
    console.error('❌ 录音系统初始化失败:', error)
    throw new Error('Failed to initialize recording: ' + error.message)
  }
}

// 使用vmsg的录音函数 - 每次创建新实例
const startRecording = async () => {
  try {
    console.log('🎙️ 开始录音...')
    
    // 每次录音创建新的录音器实例
    recorder.value = await createRecorder()
    
    await recorder.value.startRecording()
    isRecording.value = true
    console.log('✅ 录音已开始')
    
  } catch (error) {
    console.error('❌ 开始录音失败:', error)
    throw error
  }
}

const stopRecording = async () => {
  try {
    if (!recorder.value || !isRecording.value) {
      return
    }
    
    console.log('⏹️ 停止录音...')
    const mp3Blob = await recorder.value.stopRecording()
    console.log('✅ 录音停止，MP3文件大小:', mp3Blob.size, 'bytes')
    
    currentAudioBlob.value = mp3Blob
    isRecording.value = false
    
    // 关闭当前录音器实例，为下次录音做准备
    try {
      recorder.value.close()
      console.log('🔒 录音器实例已关闭')
    } catch (closeError) {
      console.warn('⚠️ 录音器关闭时出现警告:', closeError.message)
    }
    
    recorder.value = null // 清空引用
    
  } catch (error) {
    console.error('❌ 停止录音失败:', error)
    isRecording.value = false
    
    // 即使出错也要清理录音器
    if (recorder.value) {
      try {
        recorder.value.close()
      } catch (closeError) {
        console.warn('清理时录音器关闭失败:', closeError.message)
      }
      recorder.value = null
    }
    
    throw error
  }
}

const startTimer = () => {
  timer = setInterval(async () => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      stopTimer()
      await handleTimeUp()
    }
  }, 1000)
}

const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

// 倒计时结束处理
const handleTimeUp = async () => {
  if (isRecording.value && !isProcessingAction.value) {
    // 如果正在录音，自动停止并上传
    spaceKeyPressed.value = false  // 重置空格键状态
    try {
      await stopRecording()
      await stopAndUploadCurrentRow()
    } catch (error) {
      console.error('超时停止录音失败:', error)
    }
  }
  
  // 完成当前轮次
  await finishRound()
}

const nextRow = async () => {
  // 防止重复操作
  if (isProcessingAction.value) {
    return
  }
  
  if (currentRowIndex.value < characterRows.value.length - 1) {
    // 停止当前行录音并保存
    await saveCurrentRowAudio()
    
    // 移动到下一行
    currentRowIndex.value++
    
    // 不自动开始新行录音，等待用户按空格
  } else {
    await finishTest()
  }
}

// 停止录音并上传当前行
const stopAndUploadCurrentRow = async () => {
  // 防止重复调用
  if (isProcessingAction.value) {
    return
  }
  
  isProcessingAction.value = true
  
  try {
    // 检查是否有音频数据
    if (!currentAudioBlob.value) {
      console.warn('没有音频数据可上传')
      return
    }
    
    try {
      // 立即上传音频文件到后端
      await uploadAudioFile(currentAudioBlob.value, currentRound.value, currentRowIndex.value)
      
      // 保存到本地记录（用于统计）
      const roundKey = `round${currentRound.value}`
      testResults.value[roundKey].audioFiles.push({
        rowIndex: currentRowIndex.value,
        audioBlob: currentAudioBlob.value,
        timestamp: Date.now(),
        uploaded: true
      })
      
      console.log(`✅ 第${currentRound.value}轮第${currentRowIndex.value + 1}行录音上传成功`)
      
      // 自动进入下一行（如果不是最后一行）
      if (currentRowIndex.value < characterRows.value.length - 1) {
        currentRowIndex.value++
      } else {
        // 如果是最后一行，完成测试
        await finishRound()
      }
      
      currentAudioBlob.value = null
      
    } catch (error) {
      console.error('❌ 上传音频失败:', error)
      ElMessage.error(`第${currentRowIndex.value + 1}行音频上传失败`)
    }
    
  } finally {
    // 延迟重置状态，防止快速重复操作
    setTimeout(() => {
      isProcessingAction.value = false
    }, 300)
  }
}

// 保持原有函数用于其他地方调用
const saveCurrentRowAudio = stopAndUploadCurrentRow

// 上传单个音频文件 - 强制使用MP3格式
const uploadAudioFile = async (audioBlob, roundNumber, rowIndex) => {
  if (!testId.value) {
    throw new Error('测试ID不存在')
  }
  
  // 强制使用MP3格式（后端仅支持mp3/wav/pcm，我们选择mp3以获得最佳压缩比）
  const fileExtension = 'mp3'
  const mimeType = audioBlob.type || 'audio/mp3'
  
  console.log(`📤 上传音频文件: 第${roundNumber}轮第${rowIndex + 1}行`)
  console.log(`   文件大小: ${audioBlob.size} bytes`)
  console.log(`   MIME类型: ${mimeType}`)
  console.log(`   扩展名: ${fileExtension}`)
  
  const formData = new FormData()
  formData.append('round_number', roundNumber.toString())
  formData.append('row_index', rowIndex.toString())
  formData.append('audio_file', audioBlob, `round${roundNumber}_row${rowIndex}.${fileExtension}`)
  
  const response = await fetch(`/api/oral-reading-fluency/tests/${testId.value}/upload-audio`, {
    method: 'POST',
    body: formData
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`上传失败: ${response.status} - ${errorText}`)
  }
  
  const result = await response.json()
  console.log(`✅ 第${roundNumber}轮第${rowIndex + 1}行音频上传成功:`, result)
  return result
}

// 完成轮次
const finishRound = async () => {
  stopTimer()
  
  // 保存当前轮次结果
  const roundKey = `round${currentRound.value}`
  testResults.value[roundKey].duration = 60 - timeLeft.value
  testResults.value[roundKey].characterCount = readCharacterCount.value
  
  testPhase.value = 'completed'
}

const finishTest = async () => {
  // 如果还在录音，先停止并上传
  if (isRecording.value && !isProcessingAction.value) {
    try {
      await stopRecording()
      await stopAndUploadCurrentRow()
    } catch (error) {
      console.error('完成测试时停止录音失败:', error)
    }
  }
  
  await finishRound()
}

const startNextRound = () => {
  currentRound.value = 2
  testPhase.value = 'instruction'
}

// 组件状态增加测试ID
const testId = ref(null)

// 创建测试ID
const createTest = async () => {
  try {
    // 获取用户信息
    const userInfoStr = localStorage.getItem('userInfo')
    let userId = 1 // 默认使用测试用户ID
    
    if (userInfoStr) {
      try {
        const userInfo = JSON.parse(userInfoStr)
        if (userInfo && userInfo.id) {
          userId = userInfo.id
        }
      } catch (parseError) {
        console.warn('解析用户信息失败，使用默认用户ID:', parseError)
      }
    }
    
    console.log('创建测试，用户ID:', userId)
    
    const response = await fetch('/api/oral-reading-fluency/tests', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      testId.value = result.test_id
      console.log('测试创建成功，测试ID:', testId.value)
      return true
    } else {
      const errorData = await response.text()
      console.error('创建测试失败，响应:', errorData)
      throw new Error('创建测试失败: ' + response.status)
    }
  } catch (error) {
    console.error('创建测试异常:', error)
    ElMessage.error('创建测试失败: ' + error.message)
    return false
  }
}

const submitResults = async () => {
  isSubmitting.value = true
  
  try {
    if (!testId.value) {
      throw new Error('测试ID不存在')
    }
    
    // 准备提交数据（不再包含音频文件，因为已经逐行上传了）
    const formData = new FormData()
    
    // 添加基本信息
    formData.append('testType', 'reading_fluency')
    formData.append('results', JSON.stringify({
      round1: {
        duration: testResults.value.round1.duration,
        characterCount: testResults.value.round1.characterCount,
        audioFileCount: testResults.value.round1.audioFiles.length
      },
      round2: {
        duration: testResults.value.round2.duration, 
        characterCount: testResults.value.round2.characterCount,
        audioFileCount: testResults.value.round2.audioFiles.length
      },
      averageScore: averageScore.value
    }))
    
    // 提交到后端（音频文件已经单独上传，这里只提交测试结果）
    const response = await fetch(`/api/oral-reading-fluency/tests/${testId.value}/submit`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const result = await response.json()
      ElMessage.success('测试结果提交成功!')
      
      // 跳转到结果页面
      await showTestResults()
      
    } else {
      const errorText = await response.text()
      throw new Error(`提交失败: ${response.status} - ${errorText}`)
    }
    
  } catch (error) {
    ElMessage.error('提交结果失败: ' + error.message)
    console.error('Submit error:', error)
  } finally {
    isSubmitting.value = false
  }
}

// 显示测试结果
const showTestResults = async () => {
  try {
    const response = await fetch(`/api/oral-reading-fluency/tests/${testId.value}/results`)
    if (response.ok) {
      const results = await response.json()
      // 这里可以显示详细结果或跳转到结果页面
      console.log('测试结果:', results)
      ElMessage.info('测试完成，结果已生成！')
    }
  } catch (error) {
    console.error('获取结果失败:', error)
  }
}

// 键盘事件监听 - 按住空格录音，松手上传
const handleKeyDown = async (event) => {
  if (testPhase.value === 'testing' && event.code === 'Space' && !event.repeat) {
    // 防止重复按键和正在处理中的操作
    if (spaceKeyPressed.value || isProcessingAction.value) {
      return
    }
    
    spaceKeyPressed.value = true
    
    if (!isRecording.value && currentRowIndex.value < characterRows.value.length) {
      // 开始录音
      try {
        await startRecording()
        console.log(`🎙️ 开始录音第${currentRound.value}轮第${currentRowIndex.value + 1}行`)
      } catch (error) {
        console.error('开始录音失败:', error)
        ElMessage.error('开始录音失败')
        spaceKeyPressed.value = false
      }
    }
  }
}

const handleKeyUp = async (event) => {
  if (testPhase.value === 'testing' && event.code === 'Space') {
    // 只有当空格键确实被按下时才处理松开事件
    if (!spaceKeyPressed.value) {
      return
    }
    
    spaceKeyPressed.value = false
    
    if (isRecording.value && !isProcessingAction.value) {
      // 停止录音并上传
      try {
        await stopRecording()
        await stopAndUploadCurrentRow()
      } catch (error) {
        console.error('停止录音失败:', error)
        ElMessage.error('停止录音失败')
      }
    }
  }
}

// 全局空格键拦截函数 - 只阻止默认行为，不阻止事件传播
const globalSpaceHandler = (event) => {
  if (testPhase.value === 'testing' && event.code === 'Space') {
    // 只阻止空格键的默认行为（防止页面滚动），但允许事件继续传播到我们的处理函数
    event.preventDefault()
    // 不调用 stopPropagation()，让事件能正常传递给 handleKeyDown 和 handleKeyUp
  }
}

// 生命周期
onMounted(() => {
  // 添加全局空格键拦截，仅阻止默认行为（防止页面滚动）
  document.addEventListener('keydown', globalSpaceHandler, true)  // 使用捕获阶段
  
  // 添加我们的键盘事件处理器
  document.addEventListener('keydown', handleKeyDown)
  document.addEventListener('keyup', handleKeyUp)
  
  // 检查用户信息，如果没有则创建默认用户信息
  checkAndInitUserInfo()
})

// 检查并初始化用户信息
const checkAndInitUserInfo = () => {
  const userInfoStr = localStorage.getItem('userInfo')
  if (!userInfoStr) {
    // 创建默认用户信息
    const defaultUserInfo = {
      id: 1,
      name: '测试用户',
      school: '测试小学',
      grade: 2,
      class_number: 1
    }
    localStorage.setItem('userInfo', JSON.stringify(defaultUserInfo))
    console.log('已创建默认用户信息:', defaultUserInfo)
  }
}

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('keyup', handleKeyUp)
  document.removeEventListener('keydown', globalSpaceHandler, true)  // 移除全局拦截
  stopTimer()
  
  // 重置状态
  spaceKeyPressed.value = false
  isProcessingAction.value = false
  
  // 清理录音器
  if (recorder.value) {
    try {
      recorder.value.close()
      recorder.value = null
    } catch (error) {
      console.log('录音器清理完成')
    }
  }
})
</script>

<style scoped>
.reading-fluency-page {
  min-height: 100vh;
  background: #f8f9fa;
}

.reading-fluency-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.test-title {
  color: #2c3e50;
  margin: 0;
  font-size: 24px;
}

.test-status {
  display: flex;
  align-items: center;
  gap: 20px;
}

.round-info {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 16px;
}

.round-label {
  color: #666;
}

.round-number {
  color: #409eff;
  font-weight: bold;
}

.timer {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 15px;
  background: #e8f5e8;
  border-radius: 20px;
  font-size: 18px;
  font-weight: bold;
  color: #67c23a;
}

.timer-warning {
  background: #fdf6ec;
  color: #e6a23c;
}

.instructions {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.instruction-content h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  text-align: center;
}

.instruction-content ul {
  font-size: 16px;
  line-height: 1.8;
  color: #555;
  margin-bottom: 30px;
}

.instruction-content li {
  margin-bottom: 10px;
}

.start-button-container {
  text-align: center;
}

.character-grid {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.character-row {
  display: flex;
  align-items: center;
  padding: 15px 10px;
  border-radius: 8px;
  margin-bottom: 10px;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.current-row {
  background: #e8f4fd;
  border: 2px solid #409eff;
  transform: scale(1.02);
}

.completed-row {
  background: #e8f5e8;
  opacity: 0.7;
}

.row-number {
  width: 40px;
  text-align: center;
  font-weight: bold;
  color: #666;
}

.characters {
  flex: 1;
  display: flex;
  gap: 15px;
  padding: 0 20px;
}

.character {
  font-size: 24px;
  font-weight: 500;
  color: #2c3e50;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

/* 移除字符高亮样式，因为不再跟踪朗读进度 */

.row-status {
  width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.completed-icon {
  color: #67c23a;
  font-size: 20px;
}

.reading-text {
  color: #409eff;
  font-size: 14px;
  font-weight: bold;
}

.control-panel {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.char-count {
  color: #409eff;
  font-weight: bold;
}

.control-buttons {
  display: flex;
  gap: 15px;
}

.test-complete {
  background: white;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.completion-content h3 {
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 24px;
}

.round-results {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.result-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.result-item .label {
  color: #666;
  font-size: 14px;
}

.result-item .value {
  color: #2c3e50;
  font-size: 20px;
  font-weight: bold;
}

.completion-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.recording-indicator {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  background: #ff4d4f;
  color: white;
  border-radius: 25px;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.3);
  z-index: 1000;
}

.recording-dot {
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}

@media (max-width: 768px) {
  .character-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .characters {
    padding: 0;
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .character {
    font-size: 20px;
    padding: 6px 10px;
  }
  
  .control-panel {
    flex-direction: column;
    gap: 20px;
  }
  
  .round-results {
    flex-direction: column;
    gap: 20px;
  }
}
</style>