<template>
  <div class="literacy-test-container">
    <TopNavBar />
    
    <div class="test-content">
      <div class="test-header">
        <h2>识字量测验</h2>
        <p class="test-description">点击汉字后按住空格键进行朗读，松开空格键结束录音</p>
      </div>

      <!-- 测试状态显示 -->
      <div class="test-status" v-if="testStarted">
        <el-tag :type="statusTagType">{{ statusText }}</el-tag>
        <span class="progress-text">已录制: {{ completedCount }}/{{ totalCharacters }}</span>
      </div>

      <!-- 字符组选择 -->
      <div class="group-selection" v-if="!testStarted">
        <h3>选择测试组</h3>
        <div class="group-buttons">
          <el-button
            v-for="group in characterGroups"
            :key="group.group_id"
            @click="selectGroup(group)"
            type="primary"
            :disabled="group.characters.length === 0"
          >
            {{ group.group_name }} ({{ group.characters.length }}字)
          </el-button>
        </div>
      </div>

      <!-- 测试界面 -->
      <div class="test-interface" v-if="testStarted && currentGroup">
        <div class="group-info">
          <h3>{{ currentGroup.group_name }}</h3>
          <p>系数: {{ currentGroup.coefficient }}</p>
        </div>

        <!-- 字符展示区域 -->
        <div class="characters-grid">
          <div
            v-for="(character, index) in currentGroup.characters"
            :key="index"
            class="character-card"
            :class="{
              'recording': currentCharacterIndex === index && isRecording,
              'completed': recordedCharacters.has(character),
              'current': currentCharacterIndex === index && !recordedCharacters.has(character),
              'disabled': recordedCharacters.has(character)
            }"
            @click="selectCharacter(index)"
          >
            <div class="character-text">{{ character }}</div>
            <div class="character-status">
              <el-icon v-if="recordedCharacters.has(character)" class="completed-icon">
                <Check />
              </el-icon>
              <el-icon v-else-if="currentCharacterIndex === index && isRecording" class="recording-icon">
                <Microphone />
              </el-icon>
              <el-icon v-else-if="currentCharacterIndex === index" class="current-icon">
                <ArrowRight />
              </el-icon>
            </div>
          </div>
        </div>

        <!-- 录音控制提示 -->
        <div class="recording-hint">
          <p v-if="currentCharacterIndex === -1">请选择要朗读的汉字</p>
          <p v-else-if="!isRecording">按住空格键开始录音朗读"{{ currentGroup.characters[currentCharacterIndex] }}"</p>
          <p v-else class="recording-text">正在录音中...松开空格键结束</p>
          <p class="skip-hint">不认识的字可以点击跳过，选择其他认识的字</p>
        </div>

        <!-- 完成测试按钮 -->
        <div class="test-actions" v-if="completedCount > 0">
          <el-button @click="finishTest" type="success" size="large">
            完成测试 ({{ completedCount }}/{{ totalCharacters }})
          </el-button>
        </div>
      </div>

      <!-- 测试结果 -->
      <div class="test-results" v-if="showResults">
        <h3>测试结果</h3>
        <div class="results-summary">
          <el-card>
            <div class="result-item">
              <span>总分:</span>
              <span class="score">{{ testResults?.total_score?.toFixed(2) || 0 }}</span>
            </div>
            <div class="result-item">
              <span>正确率:</span>
              <span>{{ testResults?.accuracy_rate?.toFixed(1) || 0 }}%</span>
            </div>
            <div class="result-item">
              <span>正确字数:</span>
              <span>{{ testResults?.correct_characters || 0 }}/{{ testResults?.total_characters || 0 }}</span>
            </div>
          </el-card>
        </div>

        <div class="results-actions">
          <el-button @click="restartTest" type="primary">重新测试</el-button>
          <el-button @click="backToSelection" type="default">返回选择</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Microphone, ArrowRight } from '@element-plus/icons-vue'
import TopNavBar from '../TopNavBar.vue'
import vmsg from 'vmsg'

// 响应式数据
const characterGroups = ref([])
const currentGroup = ref(null)
const testStarted = ref(false)
const currentCharacterIndex = ref(-1)
const isRecording = ref(false)
const recordedCharacters = ref(new Set())
const testId = ref(null)
const showResults = ref(false)
const testResults = ref(null)
const recorder = ref(null)

// 用户信息
const userInfo = ref({
  id: null,
  name: '',
  school: '',
  grade: 1,
  class_number: 1
})

// 计算属性
const completedCount = computed(() => recordedCharacters.value.size)
const totalCharacters = computed(() => currentGroup.value?.characters?.length || 0)

const statusText = computed(() => {
  if (showResults.value) return '测试完成'
  if (isRecording.value) return '录音中'
  if (testStarted.value) return '测试中'
  return '准备开始'
})

const statusTagType = computed(() => {
  if (showResults.value) return 'success'
  if (isRecording.value) return 'danger'
  if (testStarted.value) return 'warning'
  return 'info'
})

// 录音相关函数
const createRecorder = async () => {
  try {
    return new vmsg.Recorder({
      wasmURL: '/vmsg.wasm',
      shimURL: '/vmsg.js'
    })
  } catch (error) {
    console.error('创建录音器失败:', error)
    ElMessage.error('录音器初始化失败')
    return null
  }
}

const startRecording = async () => {
  if (currentCharacterIndex.value === -1 || !currentGroup.value) {
    ElMessage.warning('请先选择要朗读的汉字')
    return
  }

  const currentCharacter = currentGroup.value.characters[currentCharacterIndex.value]
  if (recordedCharacters.value.has(currentCharacter)) {
    ElMessage.info('该字符已录制完成')
    return
  }

  try {
    recorder.value = await createRecorder()
    if (!recorder.value) return

    await recorder.value.init()
    await recorder.value.startRecording()
    isRecording.value = true
    console.log('开始录音:', currentGroup.value.characters[currentCharacterIndex.value])
  } catch (error) {
    console.error('启动录音失败:', error)
    ElMessage.error('启动录音失败')
    isRecording.value = false
  }
}

const stopRecording = async () => {
  if (!isRecording.value || !recorder.value) return

  try {
    const blob = await recorder.value.stopRecording()
    isRecording.value = false
    
    console.log('录音完成，大小:', blob.size)
    
    if (blob.size > 0) {
      await uploadAudio(blob)
    } else {
      ElMessage.error('录音文件为空')
    }
  } catch (error) {
    console.error('停止录音失败:', error)
    ElMessage.error('停止录音失败')
    isRecording.value = false
  }
}

// API调用函数
const fetchCharacterGroups = async () => {
  try {
    const response = await fetch('/api/literacy/character-groups')
    const result = await response.json()
    if (result.success) {
      characterGroups.value = result.data
    } else {
      throw new Error('获取字符组失败')
    }
  } catch (error) {
    console.error('获取字符组失败:', error)
    ElMessage.error('获取字符组失败')
  }
}

const startTest = async (groupId) => {
  try {
    const response = await fetch('/api/literacy/start-test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `user_id=${userInfo.value.id}`
    })
    const result = await response.json()
    if (result.success) {
      testId.value = result.data.test_id
      return true
    } else {
      throw new Error('创建测试失败')
    }
  } catch (error) {
    console.error('创建测试失败:', error)
    ElMessage.error('创建测试失败')
    return false
  }
}

const uploadAudio = async (audioBlob) => {
  try {
    const currentCharacter = currentGroup.value.characters[currentCharacterIndex.value]
    const formData = new FormData()
    formData.append('test_id', testId.value)
    formData.append('character', currentCharacter)
    formData.append('group_id', currentGroup.value.group_id)
    formData.append('coefficient', currentGroup.value.coefficient)
    formData.append('audio_file', audioBlob, `${currentCharacter}.mp3`)

    const response = await fetch('/api/literacy/upload-audio', {
      method: 'POST',
      body: formData
    })

    const result = await response.json()
    if (result.success) {
      recordedCharacters.value.add(currentCharacter)
      ElMessage.success(`"${currentCharacter}"录音上传成功`)
      
      // 自动跳到下一个字符
      moveToNextCharacter()
    } else {
      throw new Error(result.message || '上传失败')
    }
  } catch (error) {
    console.error('上传音频失败:', error)
    ElMessage.error('上传音频失败')
  }
}

const fetchTestResults = async () => {
  try {
    const response = await fetch(`/api/literacy/test/${testId.value}/results`)
    const result = await response.json()
    if (result.success) {
      testResults.value = result.data
      showResults.value = true
    } else {
      throw new Error('获取测试结果失败')
    }
  } catch (error) {
    console.error('获取测试结果失败:', error)
    ElMessage.error('获取测试结果失败')
  }
}

// 交互函数
const selectGroup = async (group) => {
  currentGroup.value = group
  const success = await startTest(group.group_id)
  if (success) {
    testStarted.value = true
    recordedCharacters.value.clear()
    initializeFirstCharacter()
  }
}

const selectCharacter = (index) => {
  if (isRecording.value) return
  if (!currentGroup.value) return
  
  const character = currentGroup.value.characters[index]
  if (recordedCharacters.value.has(character)) {
    ElMessage.info('该字符已录制完成，无法重复录制')
    return
  }
  
  currentCharacterIndex.value = index
}

const moveToNextCharacter = () => {
  if (!currentGroup.value) return
  
  const characters = currentGroup.value.characters
  
  // 从当前位置的下一个开始找
  for (let i = currentCharacterIndex.value + 1; i < characters.length; i++) {
    if (!recordedCharacters.value.has(characters[i])) {
      currentCharacterIndex.value = i
      return
    }
  }
  
  // 如果后面没有未录制的，从头开始找
  for (let i = 0; i < currentCharacterIndex.value; i++) {
    if (!recordedCharacters.value.has(characters[i])) {
      currentCharacterIndex.value = i
      return
    }
  }
  
  // 都录制完了
  currentCharacterIndex.value = -1
  ElMessage.success('所有字符都已录制完成！')
}

const initializeFirstCharacter = () => {
  if (!currentGroup.value) return
  
  // 找到第一个未录制的字符
  for (let i = 0; i < currentGroup.value.characters.length; i++) {
    if (!recordedCharacters.value.has(currentGroup.value.characters[i])) {
      currentCharacterIndex.value = i
      return
    }
  }
  currentCharacterIndex.value = -1
}

const finishTest = async () => {
  try {
    await ElMessageBox.confirm(
      `确定完成测试吗？已录制 ${completedCount.value}/${totalCharacters.value} 个字符`,
      '确认完成',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 等待一段时间让后端处理完评测
    ElMessage.info('正在处理测试结果，请稍候...')
    setTimeout(async () => {
      await fetchTestResults()
    }, 2000)
    
  } catch {
    // 用户取消
  }
}

const restartTest = () => {
  testStarted.value = false
  currentGroup.value = null
  currentCharacterIndex.value = -1
  recordedCharacters.value.clear()
  testId.value = null
  showResults.value = false
  testResults.value = null
}

const backToSelection = () => {
  window.history.back()
}

// 键盘事件处理
const handleKeyDown = (event) => {
  if (event.code === 'Space' && !isRecording.value && testStarted.value && currentCharacterIndex.value !== -1) {
    event.preventDefault()
    startRecording()
  }
}

const handleKeyUp = (event) => {
  if (event.code === 'Space' && isRecording.value) {
    event.preventDefault()
    stopRecording()
  }
}

// 生命周期
onMounted(async () => {
  // 获取用户信息
  const userInfoStr = localStorage.getItem('userInfo')
  if (userInfoStr) {
    userInfo.value = JSON.parse(userInfoStr)
  }

  // 获取字符组数据
  await fetchCharacterGroups()

  // 添加键盘事件监听
  document.addEventListener('keydown', handleKeyDown)
  document.addEventListener('keyup', handleKeyUp)
})

onUnmounted(() => {
  // 清理事件监听
  document.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('keyup', handleKeyUp)
  
  // 清理录音器
  if (recorder.value) {
    try {
      recorder.value.close()
    } catch (error) {
      console.error('清理录音器失败:', error)
    }
  }
})
</script>

<style scoped>
.literacy-test-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.test-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.test-header {
  text-align: center;
  margin-bottom: 30px;
}

.test-header h2 {
  color: #303133;
  margin-bottom: 10px;
}

.test-description {
  color: #606266;
  font-size: 16px;
}

.test-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.progress-text {
  font-weight: 500;
  color: #409eff;
}

.group-selection {
  text-align: center;
  margin-bottom: 30px;
}

.group-selection h3 {
  margin-bottom: 20px;
  color: #303133;
}

.group-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: center;
}

.test-interface {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.group-info {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.group-info h3 {
  color: #303133;
  margin-bottom: 10px;
}

.group-info p {
  color: #606266;
  font-size: 14px;
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.character-card {
  position: relative;
  background: #f8f9fa;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
}

.character-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.character-card.current {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.character-card.disabled {
  opacity: 0.4;
  background: #f5f7fa;
  border-color: #dcdfe6;
  cursor: not-allowed;
}

.character-card.disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: #dcdfe6;
}

.character-card.recording {
  border-color: #f56c6c;
  background: #fef0f0;
  animation: pulse 1s infinite;
}

.character-card.completed {
  border-color: #67c23a;
  background: #f0f9ff;
}

.character-text {
  font-size: 48px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.character-status {
  height: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.completed-icon {
  color: #67c23a;
  font-size: 20px;
}

.recording-icon {
  color: #f56c6c;
  font-size: 20px;
  animation: pulse 1s infinite;
}

.current-icon {
  color: #409eff;
  font-size: 20px;
  animation: bounce 2s infinite;
}

.recording-hint {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.recording-hint p {
  margin: 0;
  font-size: 16px;
  color: #606266;
}

.recording-text {
  color: #f56c6c !important;
  font-weight: 500;
}

.skip-hint {
  color: #909399 !important;
  font-size: 14px !important;
  margin-top: 10px !important;
}

.test-actions {
  text-align: center;
}

.test-results {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.test-results h3 {
  text-align: center;
  margin-bottom: 20px;
  color: #303133;
}

.results-summary {
  margin-bottom: 30px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #ebeef5;
  font-size: 16px;
}

.result-item:last-child {
  border-bottom: none;
}

.score {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.results-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-3px);
  }
  60% {
    transform: translateY(-2px);
  }
}

@media (max-width: 768px) {
  .characters-grid {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 15px;
  }
  
  .character-text {
    font-size: 36px;
  }
  
  .test-interface {
    padding: 20px;
  }
}
</style>