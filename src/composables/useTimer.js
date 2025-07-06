import { ref, computed } from 'vue'

export function useTimer(initialTime = 180) {
  const remainingTime = ref(initialTime)
  const timerInterval = ref(null)
  const isRunning = ref(false)

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  const updateTimer = (onTimeEnd) => {
    if (!isRunning.value) return

    remainingTime.value--

    if (remainingTime.value <= 0) {
      stopTimer()
      if (onTimeEnd) onTimeEnd()
    }
  }

  const startTimer = (onTimeEnd) => {
    if (timerInterval.value) clearInterval(timerInterval.value)
    isRunning.value = true
    timerInterval.value = setInterval(() => updateTimer(onTimeEnd), 1000)
  }

  const stopTimer = () => {
    if (timerInterval.value) {
      clearInterval(timerInterval.value)
      timerInterval.value = null
    }
    isRunning.value = false
  }

  const resetTimer = (newTime = initialTime) => {
    stopTimer()
    remainingTime.value = newTime
  }

  // 沙漏样式计算
  const hourglassStyles = computed(() => {
    const percentage = (remainingTime.value / initialTime) * 100
    return {
      top: {
        height: `${percentage / 2}%`,
        transition: 'height 1s linear'
      },
      bottom: {
        height: `${(100 - percentage) / 2}%`,
        backgroundColor: percentage > 80 ? '#409EFF' : '#E6E6E6',
        transition: 'height 1s linear, background-color 1s linear'
      }
    }
  })

  return {
    remainingTime,
    isRunning,
    formatTime,
    startTimer,
    stopTimer,
    resetTimer,
    hourglassStyles
  }
}