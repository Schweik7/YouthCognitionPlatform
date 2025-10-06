<template>
  <div class="test-selection-page">
    <TopNavBar />
    <div class="test-selection-container">
    <el-card class="selection-card">
      <template #header>
        <div class="card-header">
          <h1>中小学生学习困难筛查线上平台</h1>
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
            <el-icon :size="40">
              <component :is="test.icon" />
            </el-icon>
          </div>
          <h3>{{ test.name }}</h3>
          <p>{{ test.description }}</p>
        </el-card>
      </div>

    </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Document, View, EditPen, Microphone, ChatLineRound, Grid } from '@element-plus/icons-vue';
import TopNavBar from './TopNavBar.vue';

const router = useRouter();

// 可用测试列表
const availableTests = ref([
  {
    id: 'reading-comprehension',
    name: '阅读流畅性测试',
    description: '测量阅读句子并判断真假的能力，考察您的阅读速度和理解能力',
    icon: 'Document',
    route: '/experiment'
  },
  {
    id: 'reading-fluency',
    name: '朗读流畅性测试',
    description: '测量朗读汉字的流畅度，评估您的口语表达能力和字音准确性',
    icon: 'Microphone',
    route: '/oral-reading-fluency-test'
  },
  {
    id: 'attention-test',
    name: '注意力筛查测试',
    description: '测量快速定位特定符号的能力，评估您的专注力和视觉搜索能力',
    icon: 'View',
    route: '/attention-experiment'
  },
  {
    id: 'calculation-test',
    name: '计算流畅性测试',
    description: '测量快速计算数学题的能力，评估您的心算能力和数学流畅度',
    icon: 'EditPen',
    route: '/calculation-experiment'
  },
  {
    id: 'literacy-test',
    name: '识字量测验',
    description: '测量汉字识别和朗读能力，评估您的识字水平和发音准确性',
    icon: 'ChatLineRound',
    route: '/literacy-test'
  },
  {
    id: 'raven-test',
    name: '图形推理测试',
    description: '瑞文智力测验，通过图形推理评估您的逻辑思维和抽象推理能力',
    icon: 'Grid',
    route: '/raven-test'
  }
]);

onMounted(() => {
  // 检查登录状态
  const userInfoStr = localStorage.getItem('userInfo');
  if (!userInfoStr) {
    ElMessage.warning('未登录，请先登录');
    router.push('/');
    return;
  }
});

// 选择测试
const selectTest = (test) => {
  router.push(test.route);
};

</script>

<style scoped>
.test-selection-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.test-selection-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 60px);
  padding: 20px;
}

.selection-card {
  width: 100%;
  max-width: 900px;
}

.card-header {
  text-align: center;
  margin-bottom: 20px;
}

.card-header h1 {
  font-size: 28px;
  color: #409EFF;
  margin-bottom: 10px;
}

.test-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

@media (max-width: 768px) {
  .test-grid {
    grid-template-columns: 1fr;
  }
}

.test-card {
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 25px 20px;
  height: 100%;
}

.test-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.test-icon {
  margin-bottom: 15px;
  color: #409EFF;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.test-card h3 {
  margin: 10px 0;
  color: #303133;
  font-size: 18px;
  text-align: center;
}

.test-card p {
  color: #606266;
  text-align: center;
  flex-grow: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}

</style>