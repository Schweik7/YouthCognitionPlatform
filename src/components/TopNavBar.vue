<template>
  <el-header class="top-nav-bar">
    <div class="nav-container">
      <div class="nav-left">
        <el-button link @click="goHome" class="nav-button">
          <el-icon><House /></el-icon>
          首页
        </el-button>
        <el-button link @click="goTestResults" class="nav-button">
          <el-icon><Document /></el-icon>
          测试结果
        </el-button>
      </div>
      
      <div class="nav-right">
        <el-dropdown @command="handleCommand">
          <div class="user-avatar-container">
            <el-avatar :size="36" :style="{ backgroundColor: userAvatarColor }">
              <el-icon :size="20"><component :is="userAvatarIcon" /></el-icon>
            </el-avatar>
            <span class="username">{{ userInfo.name }}</span>
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                个人信息
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </el-header>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { House, Document, User, SwitchButton, ArrowDown, Avatar, Female, Male, UserFilled, Promotion, Star } from '@element-plus/icons-vue';

const router = useRouter();
const userInfo = ref({
  name: '',
  school: '',
  grade: 1,
  class_number: 1
});
const userAvatarIcon = ref('User');
const userAvatarColor = ref('#409eff');

// 头像图标和颜色列表
const avatarOptions = [
  { icon: 'User', color: '#409eff' },
  { icon: 'Avatar', color: '#67c23a' },
  { icon: 'Female', color: '#e6a23c' },
  { icon: 'Male', color: '#f56c6c' },
  { icon: 'UserFilled', color: '#909399' },
  { icon: 'Star', color: '#b88bf7' }
];

onMounted(() => {
  // 获取用户信息
  const userInfoStr = localStorage.getItem('userInfo');
  if (userInfoStr) {
    try {
      const info = JSON.parse(userInfoStr);
      userInfo.value = info;
      
      // 获取或生成用户头像
      let savedAvatarData = localStorage.getItem('userAvatarData');
      if (!savedAvatarData) {
        // 基于用户名生成固定的头像索引
        const hash = userInfo.value.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        const avatarIndex = hash % avatarOptions.length;
        const selectedAvatar = avatarOptions[avatarIndex];
        savedAvatarData = JSON.stringify(selectedAvatar);
        localStorage.setItem('userAvatarData', savedAvatarData);
      }
      
      const avatarData = JSON.parse(savedAvatarData);
      userAvatarIcon.value = avatarData.icon;
      userAvatarColor.value = avatarData.color;
    } catch (error) {
      console.error('解析用户信息失败:', error);
    }
  }
});

// 导航到首页
const goHome = () => {
  router.push('/selection');
};

// 导航到测试结果
const goTestResults = () => {
  ElMessage.info('测试结果功能即将上线');
};

// 处理下拉菜单命令
const handleCommand = (command) => {
  if (command === 'profile') {
    showProfile();
  } else if (command === 'logout') {
    logout();
  }
};

// 显示个人信息
const showProfile = () => {
  ElMessage.info('个人信息功能即将上线');
};

// 退出登录
const logout = () => {
  localStorage.removeItem('userInfo');
  localStorage.removeItem('userAvatarData');
  ElMessage.success('已退出登录');
  router.push('/');
};
</script>

<style scoped>
.top-nav-bar {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid #e4e7ed;
  height: 60px;
  padding: 0;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #606266;
  font-size: 14px;
  padding: 8px 16px;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-button:hover {
  background-color: #f5f7fa;
  color: #409eff;
}

.nav-right {
  display: flex;
  align-items: center;
}

.user-avatar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-avatar-container:hover {
  background-color: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #606266;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-icon {
  font-size: 12px;
  color: #909399;
}

.el-dropdown-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>