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
          <li>每完成一行朗读后，按<strong>空格键</strong>进入下一行</li>
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
            :class="{
              'current-char': rowIndex === currentRowIndex && charIndex === currentCharIndex
            }"
          >
            {{ char }}
          </span>
        </div>
        <div class="row-status">
          <el-icon v-if="rowIndex < currentRowIndex" class="completed-icon">
            <Check />
          </el-icon>
          <span v-if="rowIndex === currentRowIndex" class="reading-text">
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
          :disabled="!isRecording"
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
import lamejs from 'lamejs'

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
const currentCharIndex = ref(0)
const timeLeft = ref(60) // 倒计时秒数
const isRecording = ref(false)
const isLoading = ref(false)
const isSubmitting = ref(false)

// 录音相关
const mediaRecorder = ref(null)
const audioChunks = ref([])
const currentAudioBlob = ref(null)
const audioContext = ref(null)
const sourceNode = ref(null)

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
  return currentRowIndex.value * 10 + Math.min(currentCharIndex.value + 1, characterRows.value[currentRowIndex.value]?.length || 0)
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
    currentCharIndex.value = 0
    timeLeft.value = 60
    
    // 开始计时
    startTimer()
    
    // 开始录音
    startRecording()
    
  } catch (error) {
    ElMessage.error('无法启动录音功能，请检查麦克风权限')
    console.error('Recording initialization failed:', error)
  } finally {
    isLoading.value = false
  }
}

const initializeRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        sampleRate: 44100, // MP3通常使用44100Hz
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
      }
    })
    
    // 初始化AudioContext用于MP3编码
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)()
    sourceNode.value = audioContext.value.createMediaStreamSource(stream)
    
    // 使用最佳支持的格式录制原始音频
    let mimeType = 'audio/webm;codecs=opus'
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = 'audio/webm'
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/ogg;codecs=opus'
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = '' // 使用默认
        }
      }
    }
    
    console.log('录制格式:', mimeType || '默认格式', '将转换为MP3')
    
    const options = mimeType ? { mimeType } : {}
    mediaRecorder.value = new MediaRecorder(stream, options)
    
    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
        console.log('录音数据块大小:', event.data.size, 'bytes')
      }
    }
    
    mediaRecorder.value.onstop = async () => {
      const audioBlob = new Blob(audioChunks.value, { type: mimeType || 'audio/webm' })
      console.log('原始录音完成，文件大小:', audioBlob.size, 'bytes')
      
      // 转换为MP3格式
      try {
        const mp3Blob = await convertToMp3(audioBlob)
        currentAudioBlob.value = mp3Blob
        console.log('MP3转换完成，文件大小:', mp3Blob.size, 'bytes')
      } catch (error) {
        console.error('MP3转换失败，使用原始格式:', error)
        currentAudioBlob.value = audioBlob
      }
      
      audioChunks.value = []
    }
    
    mediaRecorder.value.onerror = (error) => {
      console.error('录音错误:', error)
    }
    
  } catch (error) {
    throw new Error('Failed to initialize recording: ' + error.message)
  }
}

// MP3转换函数
const convertToMp3 = async (audioBlob) => {
  return new Promise((resolve, reject) => {
    try {
      const reader = new FileReader()
      reader.onload = async (e) => {
        try {
          const arrayBuffer = e.target.result
          const audioContext = new (window.AudioContext || window.webkitAudioContext)()
          
          // 解码音频数据
          const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
          
          // 获取PCM数据
          const samples = audioBuffer.getChannelData(0) // 单声道
          const sampleRate = audioBuffer.sampleRate
          
          // 转换为16位PCM
          const pcm16 = new Int16Array(samples.length)
          for (let i = 0; i < samples.length; i++) {
            pcm16[i] = Math.max(-32768, Math.min(32767, samples[i] * 32767))
          }
          
          // 使用lamejs编码为MP3
          const mp3Encoder = new lamejs.Mp3Encoder(1, sampleRate, 128) // 单声道，采样率，比特率128kbps
          const mp3Data = []
          
          const blockSize = 1152 // MP3帧大小
          for (let i = 0; i < pcm16.length; i += blockSize) {
            const chunk = pcm16.subarray(i, i + blockSize)
            const mp3buf = mp3Encoder.encodeBuffer(chunk)
            if (mp3buf.length > 0) {
              mp3Data.push(mp3buf)
            }
          }
          
          // 结束编码
          const finalMp3buf = mp3Encoder.flush()
          if (finalMp3buf.length > 0) {
            mp3Data.push(finalMp3buf)
          }
          
          // 创建MP3 Blob
          const mp3Blob = new Blob(mp3Data, { type: 'audio/mp3' })
          resolve(mp3Blob)
          
        } catch (error) {
          reject(error)
        }
      }
      
      reader.onerror = () => reject(new Error('Failed to read audio blob'))
      reader.readAsArrayBuffer(audioBlob)
      
    } catch (error) {
      reject(error)
    }
  })
}

const startRecording = () => {
  if (mediaRecorder.value && mediaRecorder.value.state !== 'recording') {
    audioChunks.value = []
    mediaRecorder.value.start()
    isRecording.value = true
  }
}

const stopRecording = () => {
  if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    mediaRecorder.value.stop()
    isRecording.value = false
  }
}

const startTimer = () => {
  timer = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      finishTest()
    }
  }, 1000)
}

const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

const nextRow = async () => {
  if (currentRowIndex.value < characterRows.value.length - 1) {
    // 停止当前行录音并保存
    await saveCurrentRowAudio()
    
    // 移动到下一行
    currentRowIndex.value++
    currentCharIndex.value = 0
    
    // 开始新行录音
    startRecording()
  } else {
    finishTest()
  }
}

const saveCurrentRowAudio = async () => {
  stopRecording()
  
  // 等待录音停止并获取音频数据
  return new Promise(async (resolve) => {
    const checkAudio = async () => {
      if (currentAudioBlob.value) {
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
          
          currentAudioBlob.value = null
          resolve()
        } catch (error) {
          console.error('上传音频失败:', error)
          ElMessage.error(`第${currentRowIndex.value + 1}行音频上传失败`)
          resolve() // 继续执行，不阻塞流程
        }
      } else {
        setTimeout(checkAudio, 100)
      }
    }
    checkAudio()
  })
}

// 上传单个音频文件
const uploadAudioFile = async (audioBlob, roundNumber, rowIndex) => {
  if (!testId.value) {
    throw new Error('测试ID不存在')
  }
  
  // 固定使用mp3后缀，文件更小更适合传输
  const fileExtension = 'mp3'
  
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
  console.log(`第${roundNumber}轮第${rowIndex + 1}行音频上传成功:`, result)
  return result
}

const finishTest = async () => {
  stopTimer()
  await saveCurrentRowAudio()
  
  // 保存当前轮次结果
  const roundKey = `round${currentRound.value}`
  testResults.value[roundKey].duration = 60 - timeLeft.value
  testResults.value[roundKey].characterCount = readCharacterCount.value
  
  testPhase.value = 'completed'
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

// 键盘事件监听
const handleKeyPress = (event) => {
  if (event.code === 'Space' && testPhase.value === 'testing') {
    event.preventDefault()
    nextRow()
  }
}

// 生命周期
onMounted(() => {
  document.addEventListener('keydown', handleKeyPress)
  
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
  document.removeEventListener('keydown', handleKeyPress)
  stopTimer()
  if (mediaRecorder.value && mediaRecorder.value.stream) {
    mediaRecorder.value.stream.getTracks().forEach(track => track.stop())
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

.current-char {
  background: #409eff;
  color: white;
  transform: scale(1.1);
}

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