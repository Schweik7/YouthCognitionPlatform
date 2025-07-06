import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useUserInfo() {
  const userId = ref(null)

  const getUserInfo = async () => {
    const userInfoStr = localStorage.getItem('userInfo')
    if (!userInfoStr) {
      ElMessage.warning('未登录，请先登录')
      throw new Error('用户信息不存在')
    }

    try {
      const userInfo = JSON.parse(userInfoStr)
      
      // 如果已经有userId字段，直接使用
      if (userInfo.userId) {
        userId.value = userInfo.userId
        return userInfo
      }

      // 否则，尝试查找或创建用户
      const response = await fetch('/api/users/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: userInfo.name,
          school: userInfo.school,
          grade: userInfo.grade,
          class_number: userInfo.classNumber || userInfo.class_number
        })
      })

      if (response.ok) {
        const data = await response.json()
        userId.value = data.id

        // 更新localStorage中的用户信息
        const updatedUserInfo = { ...userInfo, userId: data.id }
        localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo))
        
        return updatedUserInfo
      } else {
        console.error('创建用户失败:', await response.text())
        throw new Error('创建用户失败')
      }
    } catch (error) {
      console.error('解析用户信息失败:', error)
      throw error
    }
  }

  return {
    userId,
    getUserInfo
  }
}