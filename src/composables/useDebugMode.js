import { ref, onMounted, onUnmounted } from 'vue'

export function useDebugMode() {
  const debugMode = ref(false)

  const keyHandler = (e) => {
    // 检测是否同时按下【】键 (Alt+[ 和 Alt+])
    if ((e.key === '[' && e.altKey) || (e.key === ']' && e.altKey)) {
      debugMode.value = !debugMode.value
      return
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', keyHandler)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', keyHandler)
  })

  return {
    debugMode
  }
}