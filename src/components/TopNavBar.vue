<template>
  <el-header class="top-nav-bar">
    <div class="nav-container">
      <div class="nav-left">
        <div class="nav-brand" @click="goHome">
          <svg viewBox="0 0 32 32" aria-hidden="true">
            <rect x="2" y="2" width="28" height="28" rx="9" fill="url(#navbm)" />
            <path d="M10 21V13.5c0-1.7 1.4-3 3.1-3 1.3 0 2.4.8 2.9 2 .5-1.2 1.6-2 2.9-2 1.7 0 3.1 1.3 3.1 3V21"
                  fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" />
            <circle cx="16" cy="24.5" r="1.7" fill="#fff" />
            <defs>
              <linearGradient id="navbm" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#7d95ff" />
                <stop offset="100%" stop-color="#3a56d4" />
              </linearGradient>
            </defs>
          </svg>
          <span>中小学生学习困难筛查线上平台</span>
        </div>
        <span class="nav-divider"></span>
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
import { House, Document, User, SwitchButton, ArrowDown, Avatar, Female, Male, UserFilled, Star } from '@element-plus/icons-vue';

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
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, .82);
  backdrop-filter: saturate(1.4) blur(14px);
  border-bottom: 1px solid var(--line);
  box-shadow: 0 1px 0 rgba(19, 26, 43, .02), var(--sh-xs);
  height: 64px;
  padding: 0;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 clamp(16px, 3vw, 28px);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 10px;
  transition: background-color .2s ease;
}

.nav-brand:hover { background: var(--brand-50); }

.nav-brand svg {
  width: 30px;
  height: 30px;
  flex: none;
  display: block;
}

.nav-brand span {
  font-size: 15px;
  font-weight: 700;
  color: var(--ink-900);
  white-space: nowrap;
}

.nav-divider {
  width: 1px;
  height: 22px;
  background: var(--line);
  margin: 0 6px;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ink-500);
  font-size: 14px;
  font-weight: 600;
  padding: 8px 14px;
  border-radius: var(--r-full);
  transition: all .2s ease;
}

.nav-button:hover {
  background-color: var(--brand-50);
  color: var(--brand-600);
}

.nav-right {
  display: flex;
  align-items: center;
}

.user-avatar-container {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 12px 6px 6px;
  border: 1px solid var(--line);
  border-radius: var(--r-full);
  background: var(--surface);
  transition: all .2s ease;
}

.user-avatar-container:hover {
  border-color: var(--brand-300);
  box-shadow: var(--sh-sm);
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-700);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-icon {
  font-size: 12px;
  color: var(--ink-300);
}

.el-dropdown-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 720px) {
  .nav-brand span { display: none; }
  .nav-divider { display: none; }
}
</style>