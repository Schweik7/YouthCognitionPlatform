<template>
  <div class="literacy-test-container">
    <TopNavBar />
    
    <div class="test-content">
      <div class="test-header">
        <h2>识字量测验</h2>
        <p class="test-description">先点击不认识的汉字进行标记，然后连续朗读剩余的汉字</p>
      </div>

      <!-- 测试状态显示 -->
      <div class="test-status" v-if="testStarted">
        <el-tag :type="statusTagType">{{ statusText }}</el-tag>
      </div>

      <!-- 测试界面 - 显示所有组 -->
      <div class="test-interface" v-if="testStarted">
        <!-- 所有组的字符展示 -->
        <div v-for="group in characterGroups" :key="group.group_id" class="character-group">
          <div class="group-header">
            <h3>{{ group.group_name }}</h3>
            <!-- <p>系数: {{ group.coefficient }} | 字数: {{ group.characters.length }}</p> -->
          </div>

          <!-- 字符展示区域 -->
          <div class="characters-grid">
            <div
              v-for="(character, index) in group.characters"
              :key="`${group.group_id}-${index}`"
              class="character-card"
              :class="{
                'unknown': unknownCharacters.has(character),
                'recording': currentRecordingGroup === group.group_id && isRecording,
                'completed': recordedCharacters.has(character),
                'selectable': true
              }"
              @click="handleCharacterClick(character, group.group_id)"
            >
              <div class="character-text">{{ character }}</div>
              <div class="character-status">
                <el-icon v-if="unknownCharacters.has(character)" class="unknown-icon">
                  <Close />
                </el-icon>
                <el-icon v-else-if="recordedCharacters.has(character)" class="completed-icon">
                  <Check />
                </el-icon>
                <el-icon v-else-if="currentRecordingGroup === group.group_id && isRecording" class="recording-icon">
                  <Microphone />
                </el-icon>
              </div>
            </div>
          </div>

          <!-- 每组的操作按钮 -->
          <div class="group-actions">
            <el-button 
              v-if="!hasGroupRecorded(group.group_id)"
              @click="startGroupRecording(group)" 
              type="primary" 
              :disabled="isRecording || getGroupKnownCharacters(group).length === 0 || (currentRecordingGroup && currentRecordingGroup !== group.group_id)"
              size="large"
            >
              <el-icon><Microphone /></el-icon>
              朗读该组认识的汉字 ({{ getGroupKnownCharacters(group).length }}个)
            </el-button>
          </div>
        </div>

        <!-- 操作提示 -->
        <div class="recording-hint">
          <div class="instruction-phase">
            <h4>使用说明</h4>
            <p v-if="!isRecording">点击不认识的汉字进行标记，然后点击"朗读该组认识的汉字"按钮，按住空格键连续朗读该组所有认识的汉字。每次只能朗读一组，完成后可以选择其他组继续录音或直接结束测试。</p>
            <p v-else class="recording-text">正在录音中...松开空格键结束（正在录制：{{ currentRecordingGroupName }}）</p>
          </div>
        </div>

        <!-- 测试控制按钮 -->
        <div class="test-actions">
          <el-button v-if="recordedGroups.size > 0" @click="finishTest" type="success" size="large">
            完成测试 (已录制{{ recordedGroups.size }}组)
          </el-button>
          <el-button @click="restartTest" type="default" size="large">
            重新开始测试
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
              <span>认识字数:</span>
              <span>{{ getTotalKnownCharacters() }}/{{ getTotalCharacters() }}</span>
            </div>
            <div class="result-item">
              <span>录音数量:</span>
              <span>{{ completedCount }}个</span>
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
import { Check, Microphone, ArrowRight, Close } from '@element-plus/icons-vue'
import TopNavBar from '../TopNavBar.vue'
import vmsg from 'vmsg'

// 响应式数据
const characterGroups = ref([])
const testStarted = ref(false)
const isRecording = ref(false)
const recordedCharacters = ref(new Set())
const unknownCharacters = ref(new Set())
const testId = ref(null)
const showResults = ref(false)
const testResults = ref(null)
const recorder = ref(null)
const currentRecordingGroup = ref(null)
const currentRecordingGroupName = ref('')
const recordedGroups = ref(new Set()) // 追踪已录音的组

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


const getTotalCharacters = () => {
  return characterGroups.value.reduce((total, group) => total + group.characters.length, 0)
}

const getTotalKnownCharacters = () => {
  return getTotalCharacters() - unknownCharacters.value.size
}

const getGroupUnknownCount = (group) => {
  return group.characters.filter(char => unknownCharacters.value.has(char)).length
}

const getGroupRecordedCount = (group) => {
  return group.characters.filter(char => recordedCharacters.value.has(char)).length
}

const getGroupKnownCharacters = (group) => {
  return group.characters.filter(char => !unknownCharacters.value.has(char))
}

const hasGroupRecorded = (groupId) => {
  return recordedGroups.value.has(groupId)
}

const statusText = computed(() => {
  if (showResults.value) return '测试完成'
  if (isRecording.value) return '录音中'
  return '识字量测试'
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
  if (!currentRecordingGroup.value) {
    ElMessage.warning('请先选择要朗读的组')
    return
  }

  try {
    recorder.value = await createRecorder()
    if (!recorder.value) return

    await recorder.value.init()
    await recorder.value.startRecording()
    isRecording.value = true
    console.log('开始录音该组:', currentRecordingGroupName.value)
  } catch (error) {
    console.error('启动录音失败:', error)
    ElMessage.error('启动录音失败')
    isRecording.value = false
  }
}

const stopRecording = async () => {
  if (!isRecording.value || !recorder.value || !currentRecordingGroup.value) return

  try {
    const blob = await recorder.value.stopRecording()
    isRecording.value = false
    
    console.log('录音完成，大小:', blob.size)
    
    if (blob.size > 0) {
      await uploadGroupAudio(blob)
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


const uploadGroupAudio = async (audioBlob) => {
  try {
    const group = characterGroups.value.find(g => g.group_id === currentRecordingGroup.value)
    if (!group) {
      ElMessage.error('找不到录音组信息')
      return
    }

    // 获取该组认识的所有字符
    const knownCharacters = getGroupKnownCharacters(group)
    const charactersText = knownCharacters.join('')

    // 转换音频数据为base64
    const arrayBuffer = await audioBlob.arrayBuffer()
    const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)))
    
    const requestData = {
      test_id: testId.value,
      character: charactersText, // 将该组所有认识的字符作为一个整体
      group_id: group.group_id,
      coefficient: group.coefficient,
      audio_data: base64Audio,
      audio_filename: `group_${group.group_id}_${charactersText.substring(0, 5)}.mp3`
    }

    const response = await fetch('/api/literacy/upload-audio', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    })

    const result = await response.json()
    if (result.success) {
      // 标记该组所有认识的字符为已录音
      knownCharacters.forEach(char => {
        recordedCharacters.value.add(char)
      })
      
      // 标记该组为已录音
      recordedGroups.value.add(group.group_id)
      
      ElMessage.success(`${group.group_name}录音上传成功（${knownCharacters.length}个字符）`)
      
      // 重置当前录音组
      currentRecordingGroup.value = null
      currentRecordingGroupName.value = ''
    } else {
      throw new Error(result.message || '上传失败')
    }
  } catch (error) {
    console.error('上传音频失败:', error)
    ElMessage.error('上传音频失败')
    currentRecordingGroup.value = null
    currentRecordingGroupName.value = ''
  }
}

const uploadUnrecordedGroups = async () => {
  try {
    // 找出未录音的组
    const unrecordedGroups = characterGroups.value.filter(group => 
      !recordedGroups.value.has(group.group_id)
    )
    
    for (const group of unrecordedGroups) {
      // 获取该组所有字符（都标记为不认识）
      const groupCharacters = group.characters.join('')
      
      const requestData = {
        test_id: testId.value,
        characters: groupCharacters,
        group_id: group.group_id,
        coefficient: group.coefficient,
        is_empty: true  // 标记为空记录
      }

      const response = await fetch('/api/literacy/upload-empty-group', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      })

      const result = await response.json()
      if (result.success) {
        // 标记该组为已处理
        recordedGroups.value.add(group.group_id)
        console.log(`已标记未录音组：组 ${group.group_id}`)
      } else {
        console.error(`标记组 ${group.group_id} 失败:`, result.message)
      }
    }
  } catch (error) {
    console.error('处理未录音组失败:', error)
    ElMessage.warning('处理未录音的组时出现错误，但测试将继续完成')
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
const handleCharacterClick = (character, groupId) => {
  if (isRecording.value) {
    ElMessage.warning('录音中无法标记字符')
    return
  }
  
  // 切换不认识状态
  if (unknownCharacters.value.has(character)) {
    unknownCharacters.value.delete(character)
    ElMessage.info(`取消标记"${character}"为不认识`)
  } else {
    unknownCharacters.value.add(character)
    ElMessage.info(`标记"${character}"为不认识`)
  }
}

const startGroupRecording = (group) => {
  if (isRecording.value) return
  if (hasGroupRecorded(group.group_id)) {
    ElMessage.warning('该组已经录音完成')
    return
  }
  if (currentRecordingGroup.value && currentRecordingGroup.value !== group.group_id) {
    ElMessage.warning('请先完成当前组的录音')
    return
  }
  if (getGroupKnownCharacters(group).length === 0) {
    ElMessage.warning('该组没有认识的汉字')
    return
  }
  
  currentRecordingGroup.value = group.group_id
  currentRecordingGroupName.value = group.group_name
  ElMessage.info(`准备录制 ${group.group_name}，按住空格键开始录音`)
}


const startTest = async () => {
  try {
    // 确保用户ID存在
    if (!userInfo.value.id) {
      ElMessage.error('用户信息不完整，请重新登录')
      return false
    }

    const response = await fetch('/api/literacy/start-test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userInfo.value.id })
    })
    const result = await response.json()
    if (result.success) {
      testId.value = result.data.test_id
      testStarted.value = true
      recordedCharacters.value.clear()
      unknownCharacters.value.clear()
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

const finishTest = async () => {
  try {
    await ElMessageBox.confirm(
      `确定完成测试吗？已录制 ${recordedGroups.value.size} 个组的音频`,
      '确认完成',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 先为未录音的组上传空记录
    ElMessage.info('正在处理未录音的组...')
    await uploadUnrecordedGroups()
    
    // 调用后端完成测试的API，传递不认识的字符列表
    ElMessage.info('正在完成测试...')
    
    const unknownCharsArray = Array.from(unknownCharacters.value)
    
    const response = await fetch(`/api/literacy/test/${testId.value}/finish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        unknown_characters: unknownCharsArray
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('测试完成')
      // 等待一下再获取结果
      setTimeout(async () => {
        await fetchTestResults()
      }, 1000)
    } else {
      throw new Error(result.message || '完成测试失败')
    }
    
  } catch (error) {
    console.error('完成测试失败:', error)
    ElMessage.error('完成测试失败')
  }
}

const restartTest = () => {
  testStarted.value = false
  recordedCharacters.value.clear()
  unknownCharacters.value.clear()
  recordedGroups.value.clear()
  testId.value = null
  showResults.value = false
  testResults.value = null
  currentRecordingGroup.value = null
  currentRecordingGroupName.value = ''
}

const backToSelection = () => {
  window.history.back()
}

// 全局空格键处理器 - 防止页面滚动
const globalSpaceHandler = (event) => {
  if (testStarted.value && event.code === 'Space') {
    // 只阻止空格键的默认行为（防止页面滚动），但允许事件继续传播到我们的处理函数
    event.preventDefault()
    // 不调用 stopPropagation()，让事件能正常传递给 handleKeyDown 和 handleKeyUp
  }
}

// 键盘事件处理
const handleKeyDown = (event) => {
  if (event.code === 'Space' && !isRecording.value && currentRecordingGroup.value) {
    startRecording()
  }
}

const handleKeyUp = (event) => {
  if (event.code === 'Space' && isRecording.value) {
    stopRecording()
  }
}

// 生命周期
onMounted(async () => {
  // 获取用户信息
  const userInfoStr = localStorage.getItem('userInfo')
  if (userInfoStr) {
    try {
      const parsedUserInfo = JSON.parse(userInfoStr)
      userInfo.value = parsedUserInfo
      
      // 确保用户信息包含必要字段
      if (!userInfo.value.id) {
        ElMessage.error('用户信息缺少ID，请重新登录')
        return
      }
    } catch (error) {
      console.error('解析用户信息失败:', error)
      ElMessage.error('用户信息格式错误，请重新登录')
      return
    }
  } else {
    ElMessage.error('未找到用户信息，请先登录')
    return
  }

  // 获取字符组数据
  await fetchCharacterGroups()
  
  // 自动开始测试
  await startTest()

  // 添加全局空格键拦截，仅阻止默认行为（防止页面滚动）
  document.addEventListener('keydown', globalSpaceHandler, true)  // 使用捕获阶段
  
  // 添加我们的键盘事件处理器
  document.addEventListener('keydown', handleKeyDown)
  document.addEventListener('keyup', handleKeyUp)
})

onUnmounted(() => {
  // 清理事件监听
  document.removeEventListener('keydown', globalSpaceHandler, true)
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

.character-group {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.group-header {
  text-align: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.group-header h3 {
  color: #303133;
  margin-bottom: 8px;
  font-size: 18px;
}

.group-header p {
  color: #606266;
  margin: 5px 0;
}

.group-stats {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}

.stat {
  font-size: 14px;
  color: #909399;
  background: #f5f7fa;
  padding: 4px 12px;
  border-radius: 12px;
}

.group-actions {
  text-align: center;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.group-actions .el-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
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
  margin-bottom: 10px;
  color: #303133;
}

.selection-hint {
  color: #606266;
  font-size: 14px;
  margin-bottom: 20px;
  text-align: center;
}

.group-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.group-buttons .el-button {
  height: 80px;
  white-space: normal;
  line-height: 1.4;
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
  padding: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 90px;
  height: 90px;
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

.character-card.unknown {
  background: #f5f5f5;
  border-color: #d3d3d3;
  color: #909399;
}

.character-card.unknown .character-text {
  color: #909399;
}

.character-card.unknown:hover {
  border-color: #b0b0b0;
  background: #efefef;
}

.character-card.selectable {
  cursor: pointer;
}

.character-card.selectable:hover {
  border-color: #67c23a;
  background: #f0f9ff;
}

.character-card.recording:not(.unknown) {
  border-color: #f56c6c;
  background: #fef0f0;
  animation: pulse 1s infinite;
}

.character-card.recording.unknown {
  border-color: #d3d3d3;
  background: #f5f5f5;
  animation: none;
}

.character-card.completed {
  border-color: #67c23a;
  background: #f0f9ff;
}

.character-text {
  font-family: "KaiTi", "楷体", "STKaiti", "KaiTi_GB2312",serif;
  font-size: 36px;
  font-weight: normal;
  color: #303133;
  text-align: center;
  line-height: 1;
}

.character-status {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 16px;
  height: 16px;
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

.unknown-icon {
  color: #f56c6c;
  font-size: 20px;
}

.selection-phase,
.reading-phase {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.selection-phase h4,
.reading-phase h4 {
  color: #303133;
  margin-bottom: 10px;
  font-size: 18px;
}

.selection-phase p,
.reading-phase p {
  color: #606266;
  margin: 10px 0;
}

.phase-actions {
  margin-top: 20px;
}

.recording-text {
  color: #f56c6c !important;
  font-weight: 500;
}

.test-actions {
  text-align: center;
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 20px;
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
  
  .group-buttons {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .test-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>