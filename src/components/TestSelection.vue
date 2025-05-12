<template>
  <div class="test-selection-container">
    <el-card class="selection-card">
      <template #header>
        <div class="card-header">
          <h1>认知能力评估平台</h1>
          <p>请选择一个测试项目进行评估</p>
        </div>
      </template>

      <div class="test-grid">
        <el-card
          v-for="test in availableTests"
          :key="test.id"
          class="test-card"
          shadow="hover"
          @click="selectTest(test)"
        >
          <div class="test-icon">
            <el-icon :size="36">
              <component :is="test.icon" />
            </el-icon>
          </div>
          <h3>{{ test.name }}</h3>
          <p>{{ test.description }}</p>
        </el-card>
      </div>

      <div class="user-info">
        <p><strong>用户信息:</strong> {{ userInfo.name }} | {{ userInfo.school }} | {{ userInfo.grade }}年级{{ userInfo.class_number }}班</p>
        <el-button type="text" @click="logout">退出登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Document, View, EditPen } from '@element-plus/icons-vue';

const router = useRouter();
const userInfo = ref({
  name: '',
  school: '',
  grade: 1,
  class_number: 1
});

// 可用测试列表
const availableTests = ref([
  {
    id: 'reading-fluency',
    name: '阅读流畅性测试',
    description: '测量阅读句子并判断正误的能力',
    icon: 'Document',
    route: '/experiment'
  },
  {
    id: 'attention-test',
    name: '注意力筛查测试',
    description: '测量快速定位特定符号的能力',
    icon: 'View',
    route: '/attention-experiment'
  },
  {
    id: 'calculation-test',
    name: '计算流畅性测试',
    description: '测量快速运算的能力',
    icon: 'EditPen',
    route: '/calculation-experiment'
  }
]);

onMounted(() => {
  // 获取用户信息
  const userInfoStr = localStorage.getItem('userInfo');
  if (!userInfoStr) {
    ElMessage.warning('未登录，请先登录');
    router.push('/');
    return;
  }

  try {
    const info = JSON.parse(userInfoStr);
    userInfo.value = info;
  } catch (error) {
    console.error('解析用户信息失败:', error);
    ElMessage.error('用户信息无效，请重新登录');
    router.push('/');
  }
});

// 选择测试
const selectTest = (test) => {
  router.push(test.route);
};

// 退出登录
const logout = () => {
  localStorage.removeItem('userInfo');
  ElMessage.success('已退出登录');
  router.push('/');
};
</script>

<style scoped>
.test-selection-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}

.selection-card {
  width: 100%;
  max-width: 800px;
}

.card-header {
  text-align: center;
  margin-bottom: 20px;
}

.card-header h1 {
  font-size: 24px;
  color: #409EFF;
  margin-bottom: 10px;
}

.test-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.test-card {
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.test-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.test-icon {
  margin-bottom: 15px;
  color: #409EFF;
}

.test-card h3 {
  margin: 10px 0;
  color: #303133;
}

.test-card p {
  color: #606266;
  text-align: center;
}

.user-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>